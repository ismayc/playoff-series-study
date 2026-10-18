"""profilelib against tests/fixtures/profile_games.csv (same expected numbers
in tests/R/test_functions.R).

Worked by hand. One best-of-3 series, team 1 (A) wins Games 1 and 3.
  Possessions: each team FGA + 11 - 10 + 9 = FGA + 10, so P = 90, 100, 110.
  PF100: A 20, 20, 20 (dev 0); B 30, 20, 20, mean 70/3, devs 20/3, -10/3, -10/3.
    Game devs: 10/3, -5/3, -5/3.
  PACE: 90, 100, 110 * 48 / 53 (Game 3 is overtime: MIN 265 / 5 = 53).
  FG3A_RATE: A .25, 1/3, .4; B .5, .3, .3.
  Series state: before Game 2 A leads 1-0 (B trails); before Game 3 tied.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import profilelib as pf  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


@pytest.fixture
def tm():
    return pf.team_game_metrics(pl.read_csv(FIX / "profile_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8}))


def by_game(df, col):
    return df.sort("GAME_NO")[col].to_list()


def test_possessions_and_rates(tm):
    a = tm.filter(pl.col("TEAM_ID") == 1).sort("GAME_NO")
    assert a["P"].to_list() == pytest.approx([90, 100, 110])
    assert a["PF100"].to_list() == pytest.approx([20, 20, 20])
    assert a["PACE"].to_list() == pytest.approx([90, 100, 110 * 48 / 53])
    assert a["OREB_PCT"].to_list() == pytest.approx([0.25] * 3)
    assert a["FTR"].to_list() == pytest.approx([25 / 80, 25 / 90, 25 / 100])
    assert a["AST_RATE"].to_list() == pytest.approx([0.5] * 3)
    assert a["ORTG"].to_list() == pytest.approx([100 * 100 / 90, 100, 100 * 100 / 110])
    assert a["TOV100"].to_list() == pytest.approx([10, 9, 900 / 110])


def test_game_deviations(tm):
    d = pf.game_deviations(tm)
    assert by_game(d, "PF100") == pytest.approx([10 / 3, -5 / 3, -5 / 3])
    pace = [90, 100, 110 * 48 / 53]
    m = sum(pace) / 3
    assert by_game(d, "PACE") == pytest.approx([p - m for p in pace])
    a = [0.25, 1 / 3, 0.4]
    b = [0.5, 0.3, 0.3]
    ma, mb = sum(a) / 3, sum(b) / 3
    assert by_game(d, "FG3A_RATE") == pytest.approx([((x - ma) + (y - mb)) / 2 for x, y in zip(a, b)])
    assert by_game(d, "OREB_PCT") == pytest.approx([0, 0, 0])


def test_blank_team_drops_from_game_mean(tm):
    # B shot no threes in Game 3: its FG3_PCT is blank there, so the game's
    # FG3_PCT deviation is A's alone, and B's series mean uses Games 1-2.
    z = tm.with_columns(pl.when((pl.col("TEAM_ID") == 2) & (pl.col("GAME_NO") == 3))
                          .then(None).otherwise(pl.col("FG3_PCT")).alias("FG3_PCT"))
    d = pf.game_deviations(z)
    a = [5 / 20, 10 / 30, 20 / 40]
    ma = sum(a) / 3
    assert by_game(d, "FG3_PCT")[2] == pytest.approx(a[2] - ma)
    b = [10 / 40, 9 / 27]
    mb = sum(b) / 2
    assert by_game(d, "FG3_PCT")[0] == pytest.approx(((a[0] - ma) + (b[0] - mb)) / 2)


def test_profiles_panels(tm):
    p = pf.profiles(pf.game_deviations(tm))
    assert set(p["PANEL"]) == {"all", "full_length"}  # 3 games of a best of 3 is full length
    row = p.filter((pl.col("PANEL") == "all") & (pl.col("GAME_NO") == 1) & (pl.col("METRIC") == "PF100")).row(0, named=True)
    assert row["N"] == 1 and row["MEAN"] == pytest.approx(10 / 3)


def test_profiles_full_length_excludes_short_series(tm):
    short = pf.game_deviations(tm).with_columns(pl.lit(4).alias("WINS_NEEDED"))
    p = pf.profiles(short)
    assert set(p["PANEL"]) == {"all"}


def test_series_state(tm):
    games, tied = pf.series_state(tm)
    assert games.height == 1 and games["GAME_NO"].item() == 2
    a = [0.25, 1 / 3, 0.4]
    b = [0.5, 0.3, 0.3]
    dev_a, dev_b = a[1] - sum(a) / 3, b[1] - sum(b) / 3
    assert games["TRAIL_MINUS_LEAD"].item() == pytest.approx(dev_b - dev_a)
    assert tied == {0: 1}
    s = pf.state_summary(games, tied).row(0, named=True)
    assert s["TIED_GAMES"] == 1 and s["N"] == 1


def test_sample_requires_every_count():
    tg = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [1984, 1985], "N_GAMES": [4, 4]})
    cov = pl.DataFrame({"LEAGUE": [0, 0], "SEASON": [1984, 1985],
                        **{c: [1.0, 1.0] for c in pf.NEEDED}}).with_columns(
        pl.when(pl.col("SEASON") == 1984).then(0.16).otherwise(1.0).alias("TOV"))
    assert pf.sample(tg, cov)["SEASON"].to_list() == [1985]
