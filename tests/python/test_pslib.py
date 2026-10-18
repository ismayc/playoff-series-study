"""Hand-built fixtures for pslib: every expected value here is worked out by
hand, not produced by running the code."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
import pslib  # noqa: E402

A, B, C = 1, 2, 3


def game(gid, d, home, away, home_won, **stats):
    """Two team-game rows for one game, home team first."""
    rows = []
    for team, opp, is_home in ((home, away, True), (away, home, False)):
        won = home_won if is_home else not home_won
        abbr, oabbr = f"T{team}", f"T{opp}"
        rows.append({"GAME_ID": gid, "TEAM_ID": team, "TEAM_ABBREVIATION": abbr,
                     "GAME_DATE": date.fromisoformat(d),
                     "MATCHUP": f"{abbr} vs. {oabbr}" if is_home else f"{abbr} @ {oabbr}",
                     "WL": "W" if won else "L",
                     **{s: float(stats.get(s, 0)) for s in pslib.STATS}})
    return rows


def frame(*games):
    return pl.DataFrame([r for g in games for r in g])


def sweep_and_six():
    """A beats B 3-0 (best of 5); C beats A 4-2 later (best of 7)."""
    return frame(
        game("g1", "2020-04-01", A, B, True), game("g2", "2020-04-03", A, B, True),
        game("g3", "2020-04-05", B, A, False),
        game("h1", "2020-04-20", C, A, True), game("h2", "2020-04-22", C, A, False),
        game("h3", "2020-04-24", A, C, False), game("h4", "2020-04-26", A, C, True),
        game("h5", "2020-04-28", C, A, True), game("h6", "2020-04-30", A, C, False),
    )


def build(log):
    return pslib.assign_series(pslib.pair_games(log))


def test_pair_games_attaches_opponent_and_home():
    p = pslib.pair_games(frame(game("g1", "2020-04-01", A, B, True, FG3M=5)))
    assert p.height == 2
    a = p.filter(pl.col("TEAM_ID") == A).row(0, named=True)
    assert (a["OPP_ID"], a["HOME"], a["FG3M"], a["OPP_FG3M"]) == (B, True, 5.0, 5.0)
    assert p.filter(pl.col("TEAM_ID") == B)["HOME"].item() is False


def test_pair_games_rejects_a_one_sided_game():
    log = frame(game("g1", "2020-04-01", A, B, True)).head(1)
    with pytest.raises(ValueError, match="g1"):
        pslib.pair_games(log)


def test_pair_games_rejects_a_duplicated_team_row():
    rows = game("g1", "2020-04-01", A, B, True)
    with pytest.raises(ValueError):
        pslib.pair_games(pl.DataFrame([rows[0], rows[0]]))


def test_game_numbers_follow_date_not_id():
    # IDs deliberately out of date order: "z" is game 1.
    log = frame(game("z", "2020-04-01", A, B, True), game("a", "2020-04-03", A, B, True),
                game("m", "2020-04-05", B, A, False))
    s = build(log)
    got = dict(s.filter(pl.col("TEAM_ID") == A).select("GAME_ID", "GAME_NO").iter_rows())
    assert got == {"z": 1, "a": 2, "m": 3}


def test_assign_series_counts_and_winner():
    s = build(sweep_and_six())
    ab = s.filter(pl.col("SERIES_KEY") == "1-2")
    ac = s.filter(pl.col("SERIES_KEY") == "1-3")
    assert ab["N_GAMES"].unique().to_list() == [3]
    assert ab["WINNER_ID"].unique().to_list() == [A]
    assert ab["WINS_NEEDED"].unique().to_list() == [3]
    assert ac["N_GAMES"].unique().to_list() == [6]
    assert ac["WINNER_ID"].unique().to_list() == [C]
    assert ac["WINS_NEEDED"].unique().to_list() == [4]


def test_validate_passes_complete_series():
    v = pslib.validate_series(build(sweep_and_six()))
    assert v["VALID"].to_list() == [True, True]


def test_validate_flags_a_tied_round_robin_pair():
    # 1954-style round robin: two games, one win each.
    log = frame(game("r1", "1954-03-16", A, B, True), game("r2", "1954-03-18", B, A, True))
    v = pslib.validate_series(build(log))
    assert v["VALID"].item() is False
    assert v["INVALID_REASON"].item() == "tied"


def test_validate_flags_series_in_progress():
    # A leads 2-1; looks like a finished best of 3 except the last game was a loss.
    log = frame(game("p1", "2026-10-01", A, B, True), game("p2", "2026-10-03", A, B, True),
                game("p3", "2026-10-05", B, A, True))
    v = pslib.validate_series(build(log))
    assert v["INVALID_REASON"].item() == "last game not the clincher"


def test_validate_flags_pair_meeting_twice():
    # A beats B 2-0, plays C, then meets B again and wins 2-1. Merged, that
    # is 5 games with 4 A wins, which the win-count rules alone would pass.
    log = frame(game("x1", "2000-04-01", A, B, True), game("x2", "2000-04-03", A, B, True),
                game("c1", "2000-04-10", A, C, True), game("c2", "2000-04-12", A, C, True),
                game("y1", "2000-05-01", A, B, True), game("y2", "2000-05-03", A, B, False),
                game("y3", "2000-05-05", A, B, True))
    s = build(log)
    v = pslib.validate_series(s).filter(pl.col("SERIES_KEY") == "1-2")
    assert s.filter(pl.col("SERIES_KEY") == "1-2")["WINS_NEEDED"].unique().item() == 4
    assert v["INVALID_REASON"].item() == "pair met twice"
    assert pslib.validate_series(s).filter(pl.col("SERIES_KEY") == "1-3")["VALID"].item() is True


def test_rest_days_counts_calendar_days():
    sched = pl.DataFrame({"TEAM_ID": [A, A, A, B],
                          "GAME_ID": ["r1", "r2", "p1", "p1"],
                          "GAME_DATE": [date(2020, 4, 1), date(2020, 4, 2), date(2020, 4, 10), date(2020, 4, 10)]})
    r = dict(pslib.rest_days(sched).filter(pl.col("TEAM_ID") == A).select("GAME_ID", "REST").iter_rows())
    assert r == {"r1": None, "r2": 1, "p1": 8}
    assert pslib.rest_days(sched).filter(pl.col("TEAM_ID") == B)["REST"].item() is None


@pytest.mark.parametrize("gid,league,year,expected", [
    ("0042400171", "00", 2025, 1),
    ("0042400407", "00", 2025, 7),
    ("0049600001", "00", 1997, None),
    ("0040000002", "00", 2001, None),
    ("0040100102", "00", 2002, 2),
    ("1042500304", "10", 2025, 4),
    ("1040100020", "10", 2001, None),
    ("1040200102", "10", 2002, 2),
])
def test_id_game_no(gid, league, year, expected):
    assert pslib.id_game_no(gid, league, year) == expected


def series_rows(*rows):
    return pl.DataFrame(rows, schema=["SERIES_KEY", "ROUND", "FINALS", "WINS_NEEDED"], orient="row")


def test_format_flags_finals_in_progress():
    # 2026 WNBA shape: best of 3, best of 5, then one game into a best of 7.
    s = series_rows(("r1a", 1, False, 2), ("r1b", 1, False, 2), ("sf", 2, False, 3), ("f", 3, True, 1))
    got = pslib.format_flags(s)
    assert got.rows() == [("f", "Finals shorter than an earlier round")]


def test_format_flags_series_behind_its_round():
    # One first-round series led 2-0 in a best of 7 while the others finished.
    s = series_rows(("a", 1, False, 4), ("b", 1, False, 4), ("c", 1, False, 2), ("f", 4, True, 4))
    assert pslib.format_flags(s).rows() == [("c", "fewer wins than its round")]


def test_format_flags_quiet_on_a_complete_season_and_unencoded_rounds():
    s = series_rows(("a", 1, False, 2), ("b", 2, False, 3), ("f", 3, True, 3))
    assert pslib.format_flags(s).height == 0
    old = series_rows(("a", None, False, 2), ("b", None, False, 3), ("f", None, True, 4))
    assert pslib.format_flags(old).height == 0


def test_format_flags_reports_one_reason_per_series():
    # The Finals is both shorter than the season max and than its own round? Only one row.
    s = series_rows(("x", 4, True, 2), ("y", 4, False, 4))
    got = pslib.format_flags(s)
    assert got.height == 1 and got["SERIES_KEY"].item() == "x"


@pytest.mark.parametrize("gid,year,expected", [
    ("0042400171", 2025, 1), ("0042400407", 2025, 4), ("1042600301", 2026, 3), ("0040000002", 2001, None)])
def test_id_round(gid, year, expected):
    assert pslib.id_round(gid, year) == expected


def test_read_log_keeps_leading_zeros_and_drops_teamless(tmp_path):
    p = tmp_path / "x.csv"
    header = "SEASON_ID,TEAM_ID,TEAM_ABBREVIATION,TEAM_NAME,GAME_ID,GAME_DATE,MATCHUP,WL," + ",".join(pslib.STATS)
    blank = "," * (len(pslib.STATS) - 1)
    p.write_text(header + "\n"
                 + "22024,1610612747,LAL,Lakers,0042400161,2025-04-19,LAL vs. MIN,L," + "1" + blank + "\n"
                 + "22024,,,,0042400161,2025-04-19,,," + blank + "\n")
    df = pslib.read_log(p)
    assert df.height == 1
    assert df["GAME_ID"].item() == "0042400161"
    assert df["GAME_DATE"].item() == date(2025, 4, 19)
    assert df["FGA"].item() is None


def test_read_log_empty_file(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("")
    assert pslib.read_log(p).height == 0
