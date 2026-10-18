"""Shared functions for the playoff series study.

Everything here is a pure function of polars frames so the tests can pin it
to hand-built fixtures. The scripts (02 onward) do the file I/O.

Series identity comes from the data, not the game ID. Game IDs for seasons
ending before 2002 are numbered sequentially through the postseason
(0049600001), so
they say nothing about the series or the game number; later IDs encode both
(004 YY 00 R S G). A series here is one unordered pair of teams within one
league-season, and the game number is the order of that pair's games by date.
Where the ID does encode a game number, `id_game_no` carries it so the build
can cross-check the two.
"""

from __future__ import annotations

import polars as pl

# Box-score counts carried into the team-game table. FG3A and TOV are blank
# in most early NBA rows; coverage is measured in 02, never assumed.
STATS = ["MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "OREB", "DREB",
         "AST", "STL", "BLK", "TOV", "PF", "PTS"]

LOG_SCHEMA = {"GAME_ID": pl.Utf8, "TEAM_ID": pl.Int64, "SEASON_ID": pl.Utf8,
              "TEAM_ABBREVIATION": pl.Utf8, "GAME_DATE": pl.Utf8, "MATCHUP": pl.Utf8,
              "WL": pl.Utf8, **{s: pl.Float64 for s in STATS}}


def read_log(path) -> pl.DataFrame:
    """Read one harvested LeagueGameLog CSV with fixed types.

    GAME_ID must stay text (leading zeros), and the counts are floats because
    early seasons leave them blank. Rows with no TEAM_ID are dropped; the 2005
    WNBA regular season has three of them (family note).
    """
    df = pl.read_csv(path, schema_overrides=LOG_SCHEMA, infer_schema_length=0, raise_if_empty=False)
    if df.height == 0:
        return pl.DataFrame(schema=LOG_SCHEMA)
    keep = ["GAME_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GAME_DATE", "MATCHUP", "WL", *STATS]
    return (df.select(keep)
              .filter(pl.col("TEAM_ID").is_not_null())
              .with_columns(pl.col("GAME_DATE").str.to_date("%Y-%m-%d")))


def id_game_no(game_id: str, league: str, end_year: int) -> int | None:
    """Game number encoded in a playoff GAME_ID, or None where it is not.

    Encoded IDs end in round, series, and game digits (0042400171 is first
    round, series 7, game 1). Both leagues switched in 2002: the NBA's
    2001-02 and the WNBA's 2002 (the 2000-01 NBA IDs still run 0040000001
    upward; the 2001 WNBA ones run 1040100001 to 1040100020). Earlier IDs are
    a running count, so None. 02 checks every encoded season against date
    order.
    """
    if end_year < 2002:
        return None
    return int(game_id[-1])


def id_round(game_id: str, end_year: int) -> int | None:
    """Round encoded in a playoff GAME_ID (2002 on), or None before."""
    if end_year < 2002:
        return None
    return int(game_id[7])


def format_flags(series: pl.DataFrame) -> pl.DataFrame:
    """Flag series whose length format is out of line with their round.

    `series` has one row per series with SERIES_KEY, ROUND (null where the
    ID does not encode it), FINALS, and WINS_NEEDED. A series still in
    progress passes `validate_series` whenever its leader won the last game
    played (one game into a best of 7 looks like a finished best of 1), so
    this compares formats instead: a series needing fewer wins than another
    series in its round, or a Finals needing fewer wins than any series that
    season, is flagged. Returns SERIES_KEY and FORMAT_REASON for flagged
    series only.
    """
    in_round = (series.filter(pl.col("ROUND").is_not_null())
                      .with_columns(pl.col("WINS_NEEDED").max().over("ROUND").alias("ROUND_MAX"))
                      .filter(pl.col("WINS_NEEDED") < pl.col("ROUND_MAX"))
                      .select("SERIES_KEY", pl.lit("fewer wins than its round").alias("FORMAT_REASON")))
    season_max = series["WINS_NEEDED"].max()
    finals = (series.filter(pl.col("FINALS") & (pl.col("WINS_NEEDED") < season_max))
                    .select("SERIES_KEY", pl.lit("Finals shorter than an earlier round").alias("FORMAT_REASON")))
    return pl.concat([finals, in_round]).unique("SERIES_KEY", keep="first").sort("SERIES_KEY")


def pair_games(log: pl.DataFrame) -> pl.DataFrame:
    """Attach the opponent to each team-game row.

    Every GAME_ID must have exactly two rows with different teams; anything
    else raises, because a silently dropped game shifts every later game
    number in its series.
    """
    counts = log.group_by("GAME_ID").agg(pl.len().alias("n"), pl.col("TEAM_ID").n_unique().alias("t"))
    bad = counts.filter((pl.col("n") != 2) | (pl.col("t") != 2))
    if bad.height:
        raise ValueError(f"games without exactly two teams: {bad['GAME_ID'].to_list()[:10]}")
    opp = log.select(pl.col("GAME_ID"), pl.col("TEAM_ID").alias("OPP_ID"),
                     pl.col("TEAM_ABBREVIATION").alias("OPP"),
                     *[pl.col(s).alias(f"OPP_{s}") for s in STATS])
    return (log.join(opp, on="GAME_ID")
               .filter(pl.col("TEAM_ID") != pl.col("OPP_ID"))
               .with_columns(pl.col("MATCHUP").str.contains(" vs. ").alias("HOME")))


def assign_series(paired: pl.DataFrame) -> pl.DataFrame:
    """Number each pair's games by date and attach series-level facts.

    Adds SERIES_KEY (lower team id, higher team id), GAME_NO (1-based, by
    date then GAME_ID), N_GAMES, the series winner, and WINS_NEEDED (the
    winner's win total). A pair that meets twice in one postseason would be
    merged into one series here; `validate_series` catches that shape.
    """
    lo = pl.min_horizontal("TEAM_ID", "OPP_ID")
    hi = pl.max_horizontal("TEAM_ID", "OPP_ID")
    df = paired.with_columns(
        (lo.cast(pl.Utf8) + "-" + hi.cast(pl.Utf8)).alias("SERIES_KEY"))
    order = (df.select("SERIES_KEY", "GAME_ID", "GAME_DATE").unique()
               .sort("SERIES_KEY", "GAME_DATE", "GAME_ID")
               .with_columns(pl.int_range(1, pl.len() + 1).over("SERIES_KEY").alias("GAME_NO"),
                             pl.len().over("SERIES_KEY").alias("N_GAMES")))
    df = df.join(order.drop("GAME_DATE"), on=["SERIES_KEY", "GAME_ID"])
    wins = (df.filter(pl.col("WL") == "W").group_by("SERIES_KEY", "TEAM_ID")
              .agg(pl.len().alias("W")))
    top = (wins.sort("W", "TEAM_ID", descending=[True, False])
               .group_by("SERIES_KEY", maintain_order=True).first()
               .rename({"TEAM_ID": "WINNER_ID", "W": "WINS_NEEDED"}))
    return df.join(top, on="SERIES_KEY", how="left")


def validate_series(df: pl.DataFrame) -> pl.DataFrame:
    """One row per series with a VALID flag and the reason when it fails.

    A valid series has its games in one unbroken run for each team, one
    team reaching WINS_NEEDED wins, the other fewer, the clinching win in
    the last game, and N_GAMES no more than 2 * WINS_NEEDED - 1. Round-robin
    pairings (the 1954 NBA playoffs), a pair that met twice, or a series
    still in progress fail at least one.
    """
    per_team = (df.group_by("SERIES_KEY", "TEAM_ID")
                  .agg((pl.col("WL") == "W").sum().alias("W")))
    w = (per_team.group_by("SERIES_KEY")
                 .agg(pl.col("W").max().alias("W_MAX"), pl.col("W").min().alias("W_MIN"),
                      pl.len().alias("TEAMS")))
    last = (df.filter(pl.col("GAME_NO") == pl.col("N_GAMES"))
              .filter(pl.col("WL") == "W")
              .select("SERIES_KEY", pl.col("TEAM_ID").alias("LAST_WINNER")))
    # Within each team's postseason, a series' games must be one unbroken
    # run; a pair that meets, plays someone else, and meets again does not.
    runs = (df.select("TEAM_ID", "GAME_DATE", "GAME_ID", "SERIES_KEY").unique()
              .sort("TEAM_ID", "GAME_DATE", "GAME_ID")
              .with_columns((pl.col("SERIES_KEY") != pl.col("SERIES_KEY").shift(1).over("TEAM_ID"))
                            .fill_null(True).cum_sum().over("TEAM_ID").alias("RUN"))
              .group_by("SERIES_KEY", "TEAM_ID").agg(pl.col("RUN").n_unique().alias("RUNS"))
              .group_by("SERIES_KEY").agg((pl.col("RUNS").max() > 1).alias("SPLIT")))
    s = (df.select("SERIES_KEY", "N_GAMES", "WINNER_ID").unique()
           .join(w, on="SERIES_KEY").join(last, on="SERIES_KEY", how="left")
           .join(runs, on="SERIES_KEY"))
    reason = (pl.when(pl.col("TEAMS") != 2).then(pl.lit("not two teams"))
                .when(pl.col("SPLIT")).then(pl.lit("pair met twice"))
                .when(pl.col("W_MAX") == pl.col("W_MIN")).then(pl.lit("tied"))
                .when(pl.col("LAST_WINNER") != pl.col("WINNER_ID")).then(pl.lit("last game not the clincher"))
                .when(pl.col("N_GAMES") > 2 * pl.col("W_MAX") - 1).then(pl.lit("too many games"))
                .otherwise(pl.lit(None)))
    return (s.with_columns(reason.alias("INVALID_REASON"))
             .with_columns(pl.col("INVALID_REASON").is_null().alias("VALID"))
             .sort("SERIES_KEY"))


def rest_days(games: pl.DataFrame) -> pl.DataFrame:
    """Days since each team's previous game, from a team's full schedule.

    `games` is every TEAM_ID, GAME_ID, GAME_DATE row a team played in the
    season (regular season, play-in, and playoffs together). REST is the
    difference in calendar days from the previous game, so a back-to-back is
    1. A team's first game of the season has no REST.
    """
    return (games.select("TEAM_ID", "GAME_ID", "GAME_DATE").unique()
                 .sort("TEAM_ID", "GAME_DATE", "GAME_ID")
                 .with_columns((pl.col("GAME_DATE") - pl.col("GAME_DATE").shift(1).over("TEAM_ID"))
                               .dt.total_days().alias("REST"))
                 .select("TEAM_ID", "GAME_ID", "REST"))
