"""Follow-ups 5 to 7: the definitions in docs/design.md ("Follow-ups 5 to 8,
fixed October 19, 2026") as pure functions. R/functions.R mirrors them; both
are pinned to tests/fixtures/follow_games.csv.

5. outshoot_values / outshoot_summary: does the Game 1 three-point winner
   win the series, within the Game 1 result?
6. break_values / break_summary: the 2020 bubble and series length.
7. profile_decade: the question 4 profile per league and decade.
"""

from __future__ import annotations

import math

import polars as pl

from game1lib import SERIES_KEYS, Z, describe, ratio, summarize
from profilelib import METRICS

BREAK_METRICS = ["D_PCT", "D2_PCT", "D_RATE", "D2_RATE", "G1_PF100", "G1_FTR"]
BREAK_PANELS = {
    "season_2020": pl.col("SEASON") == 2020,
    "other_seasons": pl.col("SEASON") != 2020,
    "best_of_3": pl.col("WINS_NEEDED") == 2,
    "best_of_5": pl.col("WINS_NEEDED") == 3,
    "best_of_7": pl.col("WINS_NEEDED") == 4,
}


def proportion(flags: list[bool | None]) -> dict:
    """N, N_DROPPED, P, SE, and the Wald 95% interval of a share."""
    kept = [f for f in flags if f is not None]
    n = len(kept)
    out = {"N": n, "N_DROPPED": len(flags) - n, "P": None, "SE": None, "LO": None, "HI": None}
    if n == 0:
        return out
    p = sum(1 for f in kept if f) / n
    se = math.sqrt(p * (1 - p) / n)
    out.update(P=p, SE=se, LO=p - Z * se, HI=p + Z * se)
    return out


def outshoot_values(games: pl.DataFrame) -> pl.DataFrame:
    """One row per series in the question 1 sample, from the Game 1 winner's
    side. OUTSHOT and SHOOTER_WON are null when either team has no Game 1
    three-point attempts or the two Game 1 percentages are equal."""
    g1 = games.filter(pl.col("GAME_NO") == 1).with_columns(
        ratio(pl.col("FG3M"), pl.col("FG3A")).alias("G1_PCT"))
    win = g1.filter(pl.col("WL") == "W").select(
        *SERIES_KEYS, pl.col("TEAM_ID").alias("G1_WINNER"), "WINNER_ID", pl.col("G1_PCT").alias("W_PCT"))
    lose = g1.filter(pl.col("WL") == "L").select(*SERIES_KEYS, pl.col("G1_PCT").alias("L_PCT"))
    comparable = (pl.col("W_PCT").is_not_null() & pl.col("L_PCT").is_not_null()
                  & (pl.col("W_PCT") != pl.col("L_PCT")))
    return (win.join(lose, on=SERIES_KEYS)
               .with_columns((pl.col("G1_WINNER") == pl.col("WINNER_ID")).alias("SERIES_WIN"))
               .with_columns(
                   pl.when(comparable).then(pl.col("W_PCT") > pl.col("L_PCT")).otherwise(None).alias("OUTSHOT"))
               .with_columns(
                   pl.when(comparable).then(pl.col("OUTSHOT") == pl.col("SERIES_WIN")).otherwise(None)
                     .alias("SHOOTER_WON"))
               .select(*SERIES_KEYS, "W_PCT", "L_PCT", "OUTSHOT", "SERIES_WIN", "SHOOTER_WON")
               .sort(SERIES_KEYS))


def outshoot_summary(ov: pl.DataFrame) -> pl.DataFrame:
    """Per league: the share of series won by the better Game 1 three-point
    shooter, the Game 1 winner's series-win share when it outshot and when
    it did not, and the difference of those two."""
    rows = []
    for league in sorted(ov["LEAGUE"].unique().to_list()):
        lv = ov.filter(pl.col("LEAGUE") == league)
        dropped = lv["OUTSHOT"].null_count()
        shooter = proportion(lv["SHOOTER_WON"].to_list())
        yes = proportion(lv.filter(pl.col("OUTSHOT") == True)["SERIES_WIN"].to_list())  # noqa: E712
        no = proportion(lv.filter(pl.col("OUTSHOT") == False)["SERIES_WIN"].to_list())  # noqa: E712
        rows += [{"LEAGUE": league, "ESTIMATE": "shooter_wins_series", **shooter},
                 {"LEAGUE": league, "ESTIMATE": "g1_winner_outshot", **yes, "N_DROPPED": dropped},
                 {"LEAGUE": league, "ESTIMATE": "g1_winner_not_outshot", **no, "N_DROPPED": dropped}]
        diff = {"N": yes["N"] + no["N"], "N_DROPPED": dropped, "P": None, "SE": None, "LO": None, "HI": None}
        if yes["N"] and no["N"]:
            d = yes["P"] - no["P"]
            se = math.sqrt(yes["SE"] ** 2 + no["SE"] ** 2)
            diff.update(P=d, SE=se, LO=d - Z * se, HI=d + Z * se)
        rows.append({"LEAGUE": league, "ESTIMATE": "difference", **diff})
    return pl.DataFrame(rows, schema={"LEAGUE": pl.Int64, "ESTIMATE": pl.Utf8, "N": pl.Int64,
                                      "N_DROPPED": pl.Int64, "P": pl.Float64, "SE": pl.Float64,
                                      "LO": pl.Float64, "HI": pl.Float64})


def break_values(series: pl.DataFrame, games: pl.DataFrame, dev: pl.DataFrame) -> pl.DataFrame:
    """Question 1 series values with WINS_NEEDED and the series' Game 1
    PF100 and FTR deviations from the question 4 game table."""
    wins = games.select(*SERIES_KEYS, "WINS_NEEDED").unique()
    g1 = dev.filter(pl.col("GAME_NO") == 1).select(
        *SERIES_KEYS, pl.col("PF100").alias("G1_PF100"), pl.col("FTR").alias("G1_FTR"))
    return (series.select(*SERIES_KEYS, "D_PCT", "D2_PCT", "D_RATE", "D2_RATE")
                  .join(wins, on=SERIES_KEYS, how="left")
                  .join(g1, on=SERIES_KEYS, how="left")
                  .sort(SERIES_KEYS))


def break_summary(bv: pl.DataFrame) -> pl.DataFrame:
    return summarize(bv, BREAK_PANELS, BREAK_METRICS)


def profile_decade(dev: pl.DataFrame) -> pl.DataFrame:
    """Long table: league, decade, game number, metric (every series)."""
    d = dev.with_columns(((pl.col("SEASON") // 10) * 10).alias("DECADE"))
    rows = []
    for league in sorted(d["LEAGUE"].unique().to_list()):
        lv = d.filter(pl.col("LEAGUE") == league)
        for dec in sorted(lv["DECADE"].unique().to_list()):
            dv = lv.filter(pl.col("DECADE") == dec)
            for g in sorted(dv["GAME_NO"].unique().to_list()):
                gv = dv.filter(pl.col("GAME_NO") == g)
                for m in METRICS:
                    rows.append({"LEAGUE": league, "DECADE": dec, "GAME_NO": g, "METRIC": m,
                                 **describe(gv[m].to_list())})
    return pl.DataFrame(rows, schema={"LEAGUE": pl.Int64, "DECADE": pl.Int64, "GAME_NO": pl.Int64,
                                      "METRIC": pl.Utf8, "N": pl.Int64, "N_DROPPED": pl.Int64,
                                      "MEAN": pl.Float64, "SD": pl.Float64, "SE": pl.Float64,
                                      "LO": pl.Float64, "HI": pl.Float64})
