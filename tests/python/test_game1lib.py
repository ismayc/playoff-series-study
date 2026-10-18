"""game1lib against the hand-worked fixture in tests/fixtures/ (the same
expected numbers are pinned in tests/R/test_functions.R).

Worked by hand. One series, A (team 1) at home in Game 1, B (team 2):
  G1: A 3/10, B 2/10 -> 5/20 = .25; FGA 80, rate 20/80 = .25
  G2: A 4/10, B 4/10 -> 8/20 = .40; rate .25
  G3: A 6/10, B 0/0  -> REST = G2 + G3 = 14/30; FGA 160, rate 30/160 = .1875
  Regular season: A 3P% .30, allowed .35; B .40, allowed .30; league 700/2000 = .35
  Expected: A = .30 + .30 - .35 = .25; B = .40 + .35 - .35 = .40
  G1 EA = 2.5 + 4.0 = 6.5;  REST EA = .25 * 20 + .40 * 10 = 9
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import game1lib as g1  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


@pytest.fixture
def games():
    tg = pl.read_csv(FIX / "game1_games.csv")
    ts = pl.read_csv(FIX / "game1_team_seasons.csv")
    return g1.add_expected(tg, ts)


def test_expected_pct(games):
    e = dict(games.filter(pl.col("GAME_NO") == 1).select("TEAM_ID", "EXP_PCT").iter_rows())
    assert e[1] == pytest.approx(0.25)
    assert e[2] == pytest.approx(0.40)


def test_series_values(games):
    s = g1.series_values(games).row(0, named=True)
    assert s["G1_PCT"] == pytest.approx(0.25)
    assert s["REST_PCT"] == pytest.approx(14 / 30)
    assert s["G2_PCT"] == pytest.approx(0.40)
    assert s["D_PCT"] == pytest.approx(0.25 - 14 / 30)
    assert s["D2_PCT"] == pytest.approx(-0.15)
    assert s["D_RATE"] == pytest.approx(0.25 - 0.1875)
    assert s["D2_RATE"] == pytest.approx(0.0)
    assert s["RESID_G1"] == pytest.approx((5 - 6.5) / 20)
    assert s["RESID_REST"] == pytest.approx((14 - 9) / 30)
    assert s["DECADE"] == 2010


def test_team_values(games):
    t = {r["TEAM_ID"]: r for r in g1.team_values(games).iter_rows(named=True)}
    assert t[1]["G1_HOME"] is True and t[2]["G1_HOME"] is False
    assert t[1]["TEAM_D_PCT"] == pytest.approx(0.30 - 0.50)
    assert t[2]["TEAM_D_PCT"] == pytest.approx(0.20 - 0.40)
    assert t[1]["TEAM_RESID_G1"] == pytest.approx(0.05)
    assert t[2]["TEAM_RESID_G1"] == pytest.approx(-0.20)
    assert t[1]["TEAM_RESID_REST"] == pytest.approx(0.25)
    assert t[2]["TEAM_RESID_REST"] == pytest.approx(0.0)


def test_team_values_drop_neutral_seasons(games):
    assert g1.team_values(games.with_columns(pl.lit(2020).alias("SEASON"))).height == 0
    # ...but the series-level values keep them.
    assert g1.series_values(games.with_columns(pl.lit(2020).alias("SEASON"))).height == 1


def test_zero_attempt_segment_is_null(games):
    # Team B shot no threes in Game 3; give it none in Game 1 either.
    z = games.with_columns(pl.when((pl.col("TEAM_ID") == 2) & (pl.col("GAME_NO") == 1))
                             .then(0).otherwise(pl.col("FG3A")).alias("FG3A"),
                           pl.when((pl.col("TEAM_ID") == 2) & (pl.col("GAME_NO") == 1))
                             .then(0).otherwise(pl.col("FG3M")).alias("FG3M"))
    t = {r["TEAM_ID"]: r for r in g1.team_values(z).iter_rows(named=True)}
    assert t[2]["G1_PCT"] is None
    assert t[2]["TEAM_D_PCT"] is None
    assert t[1]["TEAM_D_PCT"] == pytest.approx(-0.2)


def test_missing_baseline_nulls_the_residual_not_the_pct(games):
    tg = pl.read_csv(FIX / "game1_games.csv")
    ts = pl.read_csv(FIX / "game1_team_seasons.csv").filter(pl.col("TEAM_ID") == 1)
    s = g1.series_values(g1.add_expected(tg, ts)).row(0, named=True)
    assert s["RESID_G1"] is None and s["RESID_REST"] is None
    assert s["D_PCT"] == pytest.approx(0.25 - 14 / 30)


def test_describe():
    d = g1.describe([1.0, 2.0, 3.0, None, float("nan")])
    assert (d["N"], d["N_DROPPED"]) == (3, 2)
    assert d["MEAN"] == pytest.approx(2.0)
    assert d["SD"] == pytest.approx(1.0)
    assert d["SE"] == pytest.approx(1 / math.sqrt(3))
    assert d["LO"] == pytest.approx(2 - 1.96 / math.sqrt(3))
    assert d["HI"] == pytest.approx(2 + 1.96 / math.sqrt(3))


def test_describe_small_samples():
    assert g1.describe([])["MEAN"] is None
    one = g1.describe([5.0])
    assert one["MEAN"] == 5.0 and one["SD"] is None and one["LO"] is None


def test_sample_keeps_complete_multi_game_series():
    tg = pl.DataFrame({"LEAGUE": [0, 0, 0], "SEASON": [1984, 1990, 1990], "N_GAMES": [5, 1, 4]})
    cov = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [1984, 1990],
                        "FG3M": [1.0, 1.0], "FG3A": [0.16, 1.0], "FGA": [1.0, 1.0]})
    got = g1.sample(tg, cov)
    assert got.rows() == [(0, 1990, 4)]


def test_summarize_panels_and_pooled(games):
    s = g1.series_values(games)
    out = g1.summarize(s, g1.series_panels(s), g1.SERIES_METRICS)
    assert set(out["PANEL"]) == {"all", "2010s"}
    row = out.filter((pl.col("PANEL") == "all") & (pl.col("METRIC") == "D_PCT")).row(0, named=True)
    assert row["N"] == 1 and row["MEAN"] == pytest.approx(0.25 - 14 / 30) and row["SD"] is None
    p = g1.pooled(s).row(0, named=True)
    assert (p["G1_M"], p["G1_A"], p["REST_M"], p["REST_A"]) == (5, 20, 14, 30)
    assert p["D_PCT"] == pytest.approx(0.25 - 14 / 30)


def test_season_values_pool_attempts(games):
    # The fixture series twice in 2010 and once, with no Game 1 threes, in 2016.
    s = g1.series_values(games)
    s16 = s.with_columns(pl.lit(2016).cast(s["SEASON"].dtype).alias("SEASON"),
                         (pl.col("G1_M") * 0).alias("G1_M"), (pl.col("G1_A") * 0).alias("G1_A"))
    out = g1.season_values(pl.concat([s, s, s16]))
    a = out.filter(pl.col("SEASON") == 2010).row(0, named=True)
    assert (a["SERIES"], a["G1_M"], a["G1_A"], a["G1_FGA"]) == (2, 10, 40, 160)
    assert a["G1_PCT"] == pytest.approx(0.25) and a["REST_PCT"] == pytest.approx(14 / 30)
    assert a["G1_RATE"] == pytest.approx(0.25) and a["D_RATE"] == pytest.approx(0.25 - 0.1875)
    b = out.filter(pl.col("SEASON") == 2016).row(0, named=True)
    assert b["G1_PCT"] is None and b["D_PCT"] is None and b["G1_RATE"] == 0.0
