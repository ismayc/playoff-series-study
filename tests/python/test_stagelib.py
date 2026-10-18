"""stagelib against tests/fixtures/stage_games.csv (same expected numbers in
tests/R/test_functions.R).

Worked by hand. 2010: semifinals 1-2 (team 1 wins) and 3-4 (team 3 wins),
Finals 1-3. 2011: one series, 5-6, whose winner plays no further series.
  Stages: Finals 0; both semifinals 1; 5-6 none.
  Rest gaps at Game 1: 1-2 is 5 vs 2 (gap 3), 3-4 is 4 vs 4 (gap 0),
  Finals 6 vs 3 (gap 3), 2011's 5-6 is 3 vs 3 (gap 0).
  1-2: team 1 own G1 minus G2+ = 10/30 - 12/30; team 2 = 6/20 - 9/20.
       Rates: team 1 30/80 - 30/80 = 0; team 2 20/80 - 20/90.
  Finals: team 1 5/25 - 20/50 = -.2; team 3 8/20 - 12/40 = .1; rates 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import stagelib as sl  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


@pytest.fixture
def tg():
    return pl.read_csv(FIX / "stage_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})


def test_stages(tg):
    st = {(r["SEASON"], r["SERIES_KEY"]): r["STAGE"] for r in sl.stages(tg).iter_rows(named=True)}
    assert st == {(2010, "1-3"): 0, (2010, "1-2"): 1, (2010, "3-4"): 1, (2011, "5-6"): None}


def test_stage_check_passes_and_fails(tg):
    st = sl.stages(tg)
    assert sl.stage_mismatches(tg, st).height == 0
    bad = tg.with_columns(pl.when(pl.col("SERIES_KEY") == "3-4").then(2).otherwise(pl.col("ROUND")).alias("ROUND"))
    m = sl.stage_mismatches(bad, st)
    assert m["SERIES_KEY"].to_list() == ["3-4"]


def test_missing_stage_allowed_only_without_a_finals(tg):
    st = sl.stages(tg)
    # 2011 has no Finals in the data, so its missing stage is explained.
    assert sl.unexplained_missing_stages(tg, st).height == 0
    # Blank a 2010 semifinal's stage: 2010 has a Finals, so it is not.
    broken = st.with_columns(pl.when(pl.col("SERIES_KEY") == "1-2").then(None).otherwise(pl.col("STAGE")).alias("STAGE"))
    assert sl.unexplained_missing_stages(tg, broken)["SERIES_KEY"].to_list() == ["1-2"]
    # A missing stage is not reported as a round mismatch.
    assert sl.stage_mismatches(tg, broken).height == 0


def test_stage_follows_byes():
    # Team 1 has a bye; its first series is the Finals-path semifinal.
    rows = []
    def s(key, n, t1, t2, w, fin, day):
        for i in range(n):
            for a, b in ((t1, t2), (t2, t1)):
                rows.append({"LEAGUE": 10, "SEASON": 1999, "SERIES_KEY": key, "TEAM_ID": a, "OPP_ID": b,
                             "GAME_DATE": f"1999-08-{day + i:02d}", "WINNER_ID": w, "FINALS": fin})
    s("2-3", 1, 2, 3, 2, False, 1)    # single-game first round
    s("1-2", 2, 1, 2, 1, False, 5)    # bye team 1 beats team 2
    s("1-4", 2, 1, 4, 1, True, 20)
    st = {r["SERIES_KEY"]: r["STAGE"] for r in sl.stages(pl.DataFrame(rows)).iter_rows(named=True)}
    assert st == {"1-4": 0, "1-2": 1, "2-3": 2}


def test_rest_values(tg):
    rv = {r["SERIES_KEY"]: r for r in sl.rest_values(tg).iter_rows(named=True)}
    assert rv["1-2"]["GAP"] == 3 and rv["1-3"]["GAP"] == 3 and rv["3-4"]["GAP"] == 0
    assert rv["1-2"]["CONTRAST_PCT"] == pytest.approx((10 / 30 - 12 / 30) - (6 / 20 - 9 / 20))
    assert rv["1-2"]["CONTRAST_RATE"] == pytest.approx(0 - (20 / 80 - 20 / 90))
    assert rv["1-3"]["CONTRAST_PCT"] == pytest.approx(-0.2 - 0.1)
    assert rv["1-3"]["CONTRAST_RATE"] == pytest.approx(0.0)
    assert rv["3-4"]["CONTRAST_PCT"] is None


def test_rest_summary(tg):
    s = sl.rest_summary(sl.rest_values(tg))
    r = s.filter((pl.col("BIN") == "3-5") & (pl.col("METRIC") == "CONTRAST_PCT")).row(0, named=True)
    a, b = (10 / 30 - 12 / 30) - (6 / 20 - 9 / 20), -0.3
    assert r["N"] == 2 and r["MEAN"] == pytest.approx((a + b) / 2)
    assert r["ZERO_GAP_SERIES"] == 2  # 3-4 (4 vs 4) and 2011's 5-6 (3 vs 3)
    assert s.filter((pl.col("BIN") == "6+"))["N"].to_list() == [0, 0]
    assert s.filter((pl.col("BIN") == "any") & (pl.col("METRIC") == "CONTRAST_PCT"))["N"].item() == 2


def test_stake_summary():
    sv = pl.DataFrame({"LEAGUE": [0, 0, 0, 0], "STAGE": [0, 1, 1, None],
                       "D_PCT": [0.1, 0.2, 0.4, 9.0], "D2_PCT": [0.0] * 4, "D_RATE": [0.0] * 4})
    s = sl.stake_summary(sv)
    assert sorted(s["STAGE"].unique().to_list()) == [0, 1]
    r = s.filter((pl.col("STAGE") == 1) & (pl.col("METRIC") == "D_PCT")).row(0, named=True)
    assert r["N"] == 2 and r["MEAN"] == pytest.approx(0.3)
