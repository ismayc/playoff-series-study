"""Question 4, per-game profiles through a series: the definitions in
docs/design.md ("Question 4, fixed October 18, 2026") as pure functions.
R/functions.R mirrors them; both are pinned to the fixture in tests/fixtures/.
"""

from __future__ import annotations

import polars as pl

from game1lib import describe, ratio

NEEDED = ["FGA", "FTA", "OREB", "DREB", "TOV", "PF", "AST", "FGM", "FG3A", "MIN"]
METRICS = ["PF100", "TOV100", "ORTG", "FTR", "AST_RATE", "OREB_PCT", "PACE", "FG3A_RATE", "FG3_PCT"]
REGULATION = {0: 48.0, 10: 40.0}
SERIES_KEYS = ["LEAGUE", "SEASON", "SERIES_KEY"]
GAME_KEYS = [*SERIES_KEYS, "GAME_NO"]


def sample(team_games: pl.DataFrame, coverage: pl.DataFrame) -> pl.DataFrame:
    complete = coverage.filter(pl.all_horizontal([pl.col(c) == 1 for c in NEEDED])).select("LEAGUE", "SEASON")
    return team_games.join(complete, on=["LEAGUE", "SEASON"]).filter(pl.col("N_GAMES") >= 2)


def team_game_metrics(games: pl.DataFrame) -> pl.DataFrame:
    """One row per team-game with every metric. P is the game's possessions,
    the mean of both teams' estimates."""
    own = pl.col("FGA") + 0.44 * pl.col("FTA") - pl.col("OREB") + pl.col("TOV")
    opp = pl.col("OPP_FGA") + 0.44 * pl.col("OPP_FTA") - pl.col("OPP_OREB") + pl.col("OPP_TOV")
    reg = pl.col("LEAGUE").replace_strict(REGULATION, return_dtype=pl.Float64)
    return (games.with_columns(((own + opp) / 2).alias("P"))
                 .with_columns(
                     ratio(100 * pl.col("PF"), pl.col("P")).alias("PF100"),
                     ratio(100 * pl.col("TOV"), pl.col("P")).alias("TOV100"),
                     ratio(100 * pl.col("PTS"), pl.col("P")).alias("ORTG"),
                     ratio(pl.col("FTA"), pl.col("FGA")).alias("FTR"),
                     ratio(pl.col("AST"), pl.col("FGM")).alias("AST_RATE"),
                     ratio(pl.col("OREB"), pl.col("OREB") + pl.col("OPP_DREB")).alias("OREB_PCT"),
                     ratio(pl.col("P") * reg, pl.col("MIN") / 5).alias("PACE"),
                     ratio(pl.col("FG3A"), pl.col("FGA")).alias("FG3A_RATE"),
                     ratio(pl.col("FG3M"), pl.col("FG3A")).alias("FG3_PCT")))


def game_deviations(tm: pl.DataFrame) -> pl.DataFrame:
    """One row per game: for each metric, the mean over its two teams of
    (team-game value minus that team's mean over the series). polars' mean
    skips nulls, which is the rule in the design (a blank team drops; both
    blank leaves the game blank)."""
    team_keys = [*SERIES_KEYS, "TEAM_ID"]
    dev = tm.with_columns([(pl.col(m) - pl.col(m).mean().over(team_keys)).alias(m) for m in METRICS])
    return (dev.group_by(GAME_KEYS)
               .agg(pl.col("N_GAMES").first(), pl.col("WINS_NEEDED").first(),
                    *[pl.col(m).mean().alias(m) for m in METRICS])
               .sort(GAME_KEYS))


def profiles(dev: pl.DataFrame) -> pl.DataFrame:
    """Long table: league, panel (all, full_length), game number, metric."""
    panels = {"all": pl.lit(True), "full_length": pl.col("N_GAMES") == 2 * pl.col("WINS_NEEDED") - 1}
    rows = []
    for league in sorted(dev["LEAGUE"].unique().to_list()):
        for panel, cond in panels.items():
            pv = dev.filter((pl.col("LEAGUE") == league) & cond)
            for g in sorted(pv["GAME_NO"].unique().to_list()):
                gv = pv.filter(pl.col("GAME_NO") == g)
                for m in METRICS:
                    rows.append({"LEAGUE": league, "PANEL": panel, "GAME_NO": g, "METRIC": m,
                                 **describe(gv[m].to_list())})
    return pl.DataFrame(rows, schema={"LEAGUE": pl.Int64, "PANEL": pl.Utf8, "GAME_NO": pl.Int64,
                                      "METRIC": pl.Utf8, "N": pl.Int64, "N_DROPPED": pl.Int64,
                                      "MEAN": pl.Float64, "SD": pl.Float64, "SE": pl.Float64,
                                      "LO": pl.Float64, "HI": pl.Float64})


def series_state(tm: pl.DataFrame) -> tuple[pl.DataFrame, dict[int, int]]:
    """Per game from Game 2 on where one team leads the series: the trailing
    team's FG3A_RATE deviation minus the leading team's. Also returns, per
    league, the number of games played with the series tied (left out)."""
    team_keys = [*SERIES_KEYS, "TEAM_ID"]
    t = (tm.sort([*team_keys, "GAME_NO"])
           .with_columns((pl.col("FG3A_RATE") - pl.col("FG3A_RATE").mean().over(team_keys)).alias("DEV"),
                         ((pl.col("WL") == "W").cast(pl.Int64).cum_sum().over(team_keys)
                          - (pl.col("WL") == "W").cast(pl.Int64)).alias("WINS_BEFORE")))
    opp = t.select(*GAME_KEYS, pl.col("TEAM_ID").alias("OPP_ID"),
                   pl.col("WINS_BEFORE").alias("OPP_WINS_BEFORE"), pl.col("DEV").alias("OPP_DEV"))
    lead = (t.filter(pl.col("GAME_NO") >= 2).join(opp, on=[*GAME_KEYS, "OPP_ID"])
              .filter(pl.col("WINS_BEFORE") < pl.col("OPP_WINS_BEFORE")))  # this row is the trailing team
    tied = (t.filter(pl.col("GAME_NO") >= 2).join(opp, on=[*GAME_KEYS, "OPP_ID"])
              .filter((pl.col("WINS_BEFORE") == pl.col("OPP_WINS_BEFORE")) & (pl.col("TEAM_ID") < pl.col("OPP_ID"))))
    games = lead.select(*GAME_KEYS, (pl.col("DEV") - pl.col("OPP_DEV")).alias("TRAIL_MINUS_LEAD"))
    return games.sort(GAME_KEYS), dict(tied.group_by("LEAGUE").len().iter_rows())


def state_summary(games: pl.DataFrame, tied: dict[int, int]) -> pl.DataFrame:
    rows = []
    for league in sorted(games["LEAGUE"].unique().to_list()):
        v = games.filter(pl.col("LEAGUE") == league)["TRAIL_MINUS_LEAD"].to_list()
        rows.append({"LEAGUE": league, "TIED_GAMES": tied.get(league, 0), **describe(v)})
    return pl.DataFrame(rows)
