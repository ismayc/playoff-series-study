"""Question 3, stakes and rest: the definitions in docs/design.md ("Question
3, fixed October 18, 2026") as pure functions. R/functions.R mirrors them;
both are pinned to tests/fixtures/stage_games.csv.
"""

from __future__ import annotations

import polars as pl

from game1lib import describe, ratio

SERIES_KEYS = ["LEAGUE", "SEASON", "SERIES_KEY"]
REST_BINS = [("1-2", 1, 2), ("3-5", 3, 5), ("6+", 6, None)]
REST_METRICS = ["CONTRAST_PCT", "CONTRAST_RATE"]
STAKE_METRICS = ["D_PCT", "D2_PCT", "D_RATE"]


def stages(tg: pl.DataFrame) -> pl.DataFrame:
    """STAGE per series: 0 for the Finals, else one more than the stage of
    the next series its winner played. Null when the path never reaches a
    Finals in the data. Uses every valid series, single games included."""
    team_series = (tg.group_by([*SERIES_KEYS, "TEAM_ID"])
                     .agg(pl.col("GAME_DATE").min().alias("START"))
                     .sort("LEAGUE", "SEASON", "TEAM_ID", "START")
                     .with_columns(pl.col("SERIES_KEY").shift(-1).over("LEAGUE", "SEASON", "TEAM_ID").alias("NEXT")))
    info = tg.group_by(SERIES_KEYS).agg(pl.col("WINNER_ID").first(), pl.col("FINALS").first())
    nxt = info.join(team_series.rename({"TEAM_ID": "WINNER_ID"}).select(*SERIES_KEYS, "WINNER_ID", "NEXT"),
                    on=[*SERIES_KEYS, "WINNER_ID"], how="left")
    stage: dict[tuple, int] = {}
    nexts = {}
    for r in nxt.iter_rows(named=True):
        key = (r["LEAGUE"], r["SEASON"], r["SERIES_KEY"])
        nexts[key] = None if r["NEXT"] is None else (r["LEAGUE"], r["SEASON"], r["NEXT"])
        if r["FINALS"]:
            stage[key] = 0
    # Each pass resolves one more round back from the Finals.
    for _ in range(len(nexts)):
        added = False
        for key, n in nexts.items():
            if key not in stage and n is not None and n in stage:
                stage[key] = stage[n] + 1
                added = True
        if not added:
            break
    return (pl.DataFrame([{"LEAGUE": k[0], "SEASON": k[1], "SERIES_KEY": k[2], "STAGE": stage.get(k)} for k in nexts],
                         schema={"LEAGUE": pl.Int64, "SEASON": pl.Int64, "SERIES_KEY": pl.Utf8, "STAGE": pl.Int64})
              .sort(SERIES_KEYS))


def stage_mismatches(tg: pl.DataFrame, st: pl.DataFrame) -> pl.DataFrame:
    """Series whose STAGE disagrees with the encoded round (season max round
    minus the series' round), where the ID encodes one."""
    rounds = (tg.filter(pl.col("ROUND").is_not_null()).group_by(SERIES_KEYS).agg(pl.col("ROUND").first())
                .with_columns(pl.col("ROUND").max().over("LEAGUE", "SEASON").alias("MAX_ROUND")))
    return (rounds.join(st, on=SERIES_KEYS, how="left")
                  .filter(pl.col("STAGE").is_not_null() & (pl.col("STAGE") != pl.col("MAX_ROUND") - pl.col("ROUND"))))


def unexplained_missing_stages(tg: pl.DataFrame, st: pl.DataFrame) -> pl.DataFrame:
    """Series without a stage in a league-season that does have a Finals in
    the data. A missing stage is expected only where the Finals is absent
    (the 2026 WNBA Finals, excluded while in progress)."""
    with_finals = tg.filter(pl.col("FINALS")).select("LEAGUE", "SEASON").unique()
    return st.filter(pl.col("STAGE").is_null()).join(with_finals, on=["LEAGUE", "SEASON"])


def rest_values(games: pl.DataFrame) -> pl.DataFrame:
    """One row per series: GAP (absolute days), and the rested-minus-tired
    contrasts in own Game 1 minus own Games 2 on. Contrasts are null when the
    gap is zero or a team lacks attempts on either side."""
    keys = [*SERIES_KEYS, "TEAM_ID"]
    g1 = games.filter(pl.col("GAME_NO") == 1)
    rest = games.filter(pl.col("GAME_NO") >= 2)
    t = (g1.group_by(keys).agg(pl.col("REST").first(), pl.col("FG3M").sum().alias("M1"),
                               pl.col("FG3A").sum().alias("A1"), pl.col("FGA").sum().alias("F1"))
           .join(rest.group_by(keys).agg(pl.col("FG3M").sum().alias("MR"), pl.col("FG3A").sum().alias("AR"),
                                         pl.col("FGA").sum().alias("FR")), on=keys)
           .with_columns((ratio(pl.col("M1"), pl.col("A1")) - ratio(pl.col("MR"), pl.col("AR"))).alias("DP"),
                         (ratio(pl.col("A1"), pl.col("F1")) - ratio(pl.col("AR"), pl.col("FR"))).alias("DR")))
    hi = t.sort([*SERIES_KEYS, "REST", "TEAM_ID"], descending=[False, False, False, True, False])
    rested = hi.group_by(SERIES_KEYS, maintain_order=True).first()
    tired = hi.group_by(SERIES_KEYS, maintain_order=True).last()
    out = rested.select(*SERIES_KEYS, pl.col("REST").alias("R_HI"), pl.col("DP").alias("DP_HI"), pl.col("DR").alias("DR_HI")).join(
        tired.select(*SERIES_KEYS, pl.col("REST").alias("R_LO"), pl.col("DP").alias("DP_LO"), pl.col("DR").alias("DR_LO")),
        on=SERIES_KEYS)
    gap = pl.col("R_HI") - pl.col("R_LO")
    return (out.with_columns(gap.alias("GAP"))
               .with_columns(pl.when(pl.col("GAP") > 0).then(pl.col("DP_HI") - pl.col("DP_LO")).otherwise(None).alias("CONTRAST_PCT"),
                             pl.when(pl.col("GAP") > 0).then(pl.col("DR_HI") - pl.col("DR_LO")).otherwise(None).alias("CONTRAST_RATE"))
               .select(*SERIES_KEYS, "GAP", "CONTRAST_PCT", "CONTRAST_RATE")
               .sort(SERIES_KEYS))


def rest_summary(rv: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for league in sorted(rv["LEAGUE"].unique().to_list()):
        lv = rv.filter(pl.col("LEAGUE") == league)
        zero = lv.filter(pl.col("GAP") == 0).height
        bins = [(name, pl.col("GAP").is_between(lo, hi) if hi is not None else (pl.col("GAP") >= lo))
                for name, lo, hi in REST_BINS] + [("any", pl.col("GAP") >= 1)]
        for name, cond in bins:
            bv = lv.filter(cond)
            for m in REST_METRICS:
                rows.append({"LEAGUE": league, "BIN": name, "METRIC": m, "ZERO_GAP_SERIES": zero,
                             **describe(bv[m].to_list())})
    return pl.DataFrame(rows)


def stake_summary(sv: pl.DataFrame) -> pl.DataFrame:
    """sv: question 1 series values joined to STAGE."""
    rows = []
    for league in sorted(sv["LEAGUE"].unique().to_list()):
        lv = sv.filter(pl.col("LEAGUE") == league)
        for stage in sorted(lv["STAGE"].drop_nulls().unique().to_list()):
            st = lv.filter(pl.col("STAGE") == stage)
            for m in STAKE_METRICS:
                rows.append({"LEAGUE": league, "STAGE": stage, "METRIC": m, **describe(st[m].to_list())})
    return pl.DataFrame(rows)
