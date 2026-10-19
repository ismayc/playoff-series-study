"""followlib against tests/fixtures/follow_games.csv (same expected numbers
in tests/R/test_functions.R).

Worked by hand. Game 1 three-point lines, winner first:
  1-2 (2010): team 1 wins 4/10 over 3/10, and wins the series.
    OUTSHOT true, SERIES_WIN true, SHOOTER_WON true.
  3-4 (2020): team 3 wins 2/10 over 5/10; team 4 wins the series.
    OUTSHOT false, SERIES_WIN false, SHOOTER_WON true (team 4 outshot).
  5-6 (2020): team 6 has no Game 1 attempts, so it drops (SERIES_WIN true).
Summary: shooter_wins_series 2 of 2; outshot 1 of 1; not outshot 0 of 1;
difference 1 with SE 0; one series dropped.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import followlib as fl  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


@pytest.fixture
def games():
    return pl.read_csv(FIX / "follow_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})


def test_outshoot_values(games):
    ov = fl.outshoot_values(games)
    assert ov["SERIES_KEY"].to_list() == ["1-2", "3-4", "5-6"]
    assert ov["OUTSHOT"].to_list() == [True, False, None]
    assert ov["SERIES_WIN"].to_list() == [True, False, True]
    assert ov["SHOOTER_WON"].to_list() == [True, True, None]
    assert ov["W_PCT"].to_list() == pytest.approx([0.4, 0.2, 0.3])


def test_outshoot_summary(games):
    s = {r["ESTIMATE"]: r for r in fl.outshoot_summary(fl.outshoot_values(games)).iter_rows(named=True)}
    assert (s["shooter_wins_series"]["N"], s["shooter_wins_series"]["P"]) == (2, 1.0)
    assert s["shooter_wins_series"]["N_DROPPED"] == 1
    assert (s["g1_winner_outshot"]["N"], s["g1_winner_outshot"]["P"]) == (1, 1.0)
    assert (s["g1_winner_not_outshot"]["N"], s["g1_winner_not_outshot"]["P"]) == (1, 0.0)
    assert s["difference"]["P"] == 1.0 and s["difference"]["SE"] == 0.0
    assert s["difference"]["N_DROPPED"] == 1


def test_proportion_interval():
    p = fl.proportion([True, False, True, True, None])
    assert (p["N"], p["N_DROPPED"], p["P"]) == (4, 1, 0.75)
    se = (0.75 * 0.25 / 4) ** 0.5
    assert p["LO"] == pytest.approx(0.75 - 1.96 * se) and p["HI"] == pytest.approx(0.75 + 1.96 * se)
    assert fl.proportion([None])["P"] is None


def test_difference_blank_without_both_groups():
    ov = pl.DataFrame({"LEAGUE": [0], "SEASON": [2010], "SERIES_KEY": ["1-2"], "W_PCT": [0.4], "L_PCT": [0.3],
                       "OUTSHOT": [True], "SERIES_WIN": [True], "SHOOTER_WON": [True]})
    d = fl.outshoot_summary(ov).filter(pl.col("ESTIMATE") == "difference")
    assert d["P"].to_list() == [None] and d["N"].to_list() == [1]


def test_break_values_and_panels(games):
    series = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [2010, 2020], "SERIES_KEY": ["1-2", "3-4"],
                           "D_PCT": [0.1, 0.3], "D2_PCT": [0.0, 0.0], "D_RATE": [0.0, 0.0], "D2_RATE": [0.0, 0.0]})
    dev = pl.DataFrame({"LEAGUE": [0, 0, 0], "SEASON": [2010, 2010, 2020], "SERIES_KEY": ["1-2", "1-2", "3-4"],
                        "GAME_NO": [1, 2, 2], "PF100": [-2.0, 2.0, 5.0], "FTR": [-0.1, 0.1, 0.2]})
    bv = fl.break_values(series, games, dev)
    assert bv["WINS_NEEDED"].to_list() == [2, 2]
    assert bv["G1_PF100"].to_list() == [-2.0, None]  # 3-4 has no Game 1 row in dev
    s = fl.break_summary(bv)
    row = s.filter((pl.col("PANEL") == "season_2020") & (pl.col("METRIC") == "D_PCT")).row(0, named=True)
    assert (row["N"], row["MEAN"]) == (1, 0.3)
    b3 = s.filter((pl.col("PANEL") == "best_of_3") & (pl.col("METRIC") == "D_PCT")).row(0, named=True)
    assert b3["N"] == 2 and b3["MEAN"] == pytest.approx(0.2)
    assert s.filter(pl.col("PANEL") == "best_of_7").height == 0  # empty panels are left out


def test_profile_decade():
    dev = pl.DataFrame({"LEAGUE": [0, 0, 0], "SEASON": [1999, 1990, 2001], "GAME_NO": [1, 1, 1],
                        **{m: [1.0, 3.0, 5.0] for m in fl.METRICS}})
    pd = fl.profile_decade(dev).filter(pl.col("METRIC") == "PF100")
    assert pd["DECADE"].to_list() == [1990, 2000]
    assert pd["N"].to_list() == [2, 1] and pd["MEAN"].to_list() == [2.0, 5.0]
