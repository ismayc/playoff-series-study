"""experiencelib against tests/fixtures/profile_games.csv (the series, with
GAME_ID g1 to g3 added) and exp_players.csv / exp_team_logs.csv (same
expected numbers in tests/R/test_functions.R).

Worked by hand. Series 1-2 (2010), teams 1 and 2.
  Roster: team 1 has player 1 (100 minutes, 5 earlier playoff games: 2 in
  2008, 3 in 2009) and player 2 (50 minutes, none), so (500 + 0) / 150 = 10/3.
  Team 2 has player 3 (120 minutes, 1 earlier game) and player 4 (30
  minutes, 4 in 2007), so (120 + 120) / 150 = 1.6. Player 1's 2011 game does
  not count.
  Franchise (three previous postseasons, 2007 to 2009): team 1 2 + 4 = 6
  (its 2006 games are too old); team 2 3.
  Own Game 1 minus own Games 2 on: team 1 3P% 1/4 - 30/70, rate 1/4 - 70/190,
  PF100 20 - 20; team 2 3P% 1/4 - 9/57, rate 1/2 - 57/190, PF100 30 - 20.
  Team 1 is more experienced on both measures, so each contrast is team 1
  minus team 2.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import experiencelib as ex  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
CONTRAST = {"CONTRAST_PCT": (1 / 4 - 3 / 7) - (1 / 4 - 9 / 57),
            "CONTRAST_RATE": (1 / 4 - 7 / 19) - (1 / 2 - 3 / 10),
            "CONTRAST_PF": -10.0}


@pytest.fixture
def parts():
    games = (pl.read_csv(FIX / "profile_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})
               .with_columns(("g" + pl.col("GAME_NO").cast(pl.Utf8)).alias("GAME_ID")))
    players = pl.read_csv(FIX / "exp_players.csv", schema_overrides={"MIN": pl.Float64})
    logs = pl.read_csv(FIX / "exp_team_logs.csv")
    return games, players, logs


def test_roster_experience(parts):
    games, players, _ = parts
    r = ex.roster_experience(players, games)
    assert r["TEAM_ID"].to_list() == [1, 2]
    assert r["ROSTER_EXP"].to_list() == pytest.approx([10 / 3, 1.6])


def test_franchise_experience(parts):
    games, _, logs = parts
    f = ex.franchise_experience(logs, games)
    assert f["FRAN_EXP"].to_list() == [6.0, 3.0]


def test_team_gaps(parts):
    g = ex.team_gaps(parts[0])
    assert g["DP"].to_list() == pytest.approx([1 / 4 - 3 / 7, 1 / 4 - 9 / 57])
    assert g["DR"].to_list() == pytest.approx([1 / 4 - 7 / 19, 1 / 5])
    assert g["DPF"].to_list() == pytest.approx([0, 10])


@pytest.mark.parametrize("measure", ["roster", "franchise"])
def test_contrasts(parts, measure):
    games, players, logs = parts
    exp = ex.roster_experience(players, games) if measure == "roster" else ex.franchise_experience(logs, games)
    col = ex.MEASURES[measure]
    cv = ex.contrasts(ex.team_gaps(games), exp, col)
    row = cv.row(0, named=True)
    assert row["GAP"] == pytest.approx({"roster": 10 / 3 - 1.6, "franchise": 3.0}[measure])
    for k, v in CONTRAST.items():
        assert row[k] == pytest.approx(v)


def test_equal_experience_gives_no_contrast(parts):
    games = parts[0]
    exp = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [2010, 2010], "SERIES_KEY": ["1-2", "1-2"],
                        "TEAM_ID": [1, 2], "X": [2.0, 2.0]})
    row = ex.contrasts(ex.team_gaps(games), exp, "X").row(0, named=True)
    assert row["GAP"] == 0 and row["CONTRAST_PCT"] is None


def test_quantile7_matches_r_type_7():
    assert ex.quantile7([1, 2, 3, 4], 1 / 3) == pytest.approx(2)
    assert ex.quantile7([1, 2, 3, 4, 5], 0.25) == 2
    assert ex.quantile7([1, 2, 4, 8], 0.5) == 3


def test_summary_bins():
    cv = pl.DataFrame({"LEAGUE": [0] * 5, "SEASON": [2010] * 5, "SERIES_KEY": list("abcde"),
                       "GAP": [0.0, 1.0, 2.0, 3.0, 4.0], "CONTRAST_PCT": [None, 0.1, 0.2, 0.3, 0.4],
                       "CONTRAST_RATE": [None, 0.0, 0.0, 0.0, 0.0], "CONTRAST_PF": [None, 1.0, 1.0, 1.0, 1.0]})
    s = ex.summary(cv, "roster").filter(pl.col("METRIC") == "CONTRAST_PCT")
    by = {r["BIN"]: r for r in s.iter_rows(named=True)}
    assert by["low"]["Q1"] == pytest.approx(2) and by["low"]["Q2"] == pytest.approx(3)
    assert (by["low"]["N"], by["middle"]["N"], by["high"]["N"], by["any"]["N"]) == (2, 1, 1, 4)
    assert by["any"]["EQUAL_SERIES"] == 1 and by["any"]["MEAN"] == pytest.approx(0.25)


def test_coverage():
    players = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [2009, 2009], "GAME_ID": ["a", "b"]})
    seasons = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [2009, 2010]})
    assert ex.coverage(players, seasons)["PLAYER_ROWS"].to_list() == [2, 0]
