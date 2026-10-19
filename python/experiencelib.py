"""Follow-up 9, experienced against inexperienced teams: the definitions in
docs/design.md ("Follow-up 9, fixed October 19, 2026") as pure functions.
R/functions.R mirrors them; both are pinned to tests/fixtures/exp_*.csv.

Inputs: the question 1 sample of team-games, player-mode playoff logs for
every postseason (LEAGUE, SEASON, GAME_ID, TEAM_ID, PLAYER_ID, MIN), and the
raw team playoff logs (LEAGUE, SEASON, GAME_ID, TEAM_ID).
"""

from __future__ import annotations

import math

import polars as pl

from game1lib import SERIES_KEYS, describe, ratio
from profilelib import team_game_metrics

TEAM_KEYS = [*SERIES_KEYS, "TEAM_ID"]
MEASURES = {"roster": "ROSTER_EXP", "franchise": "FRAN_EXP"}
CONTRASTS = ["CONTRAST_PCT", "CONTRAST_RATE", "CONTRAST_PF"]
FRANCHISE_SEASONS = 3


def roster_experience(players: pl.DataFrame, games: pl.DataFrame) -> pl.DataFrame:
    """Per team-series: minutes-weighted career playoff games before that
    postseason. A team whose players logged no minutes gets a null."""
    per_season = (players.group_by("LEAGUE", "PLAYER_ID", "SEASON").agg(pl.col("GAME_ID").n_unique().alias("N"))
                         .sort("LEAGUE", "PLAYER_ID", "SEASON")
                         .with_columns((pl.col("N").cum_sum().over("LEAGUE", "PLAYER_ID") - pl.col("N")).alias("PRIOR")))
    ids = games.select(*SERIES_KEYS, "GAME_ID").unique()
    mins = (players.join(ids, on=["LEAGUE", "SEASON", "GAME_ID"])
                   .group_by(*TEAM_KEYS, "PLAYER_ID").agg(pl.col("MIN").fill_null(0).sum().alias("MIN"))
                   .join(per_season.select("LEAGUE", "PLAYER_ID", "SEASON", "PRIOR"),
                         on=["LEAGUE", "PLAYER_ID", "SEASON"]))
    return (mins.group_by(TEAM_KEYS)
                .agg(ratio((pl.col("MIN") * pl.col("PRIOR")).sum(), pl.col("MIN").sum()).alias("ROSTER_EXP"))
                .sort(TEAM_KEYS))


def franchise_experience(team_logs: pl.DataFrame, games: pl.DataFrame) -> pl.DataFrame:
    """Per team-series: playoff games the franchise played in the three
    previous postseasons (every playoff game, valid series or not)."""
    per = team_logs.group_by("LEAGUE", "TEAM_ID", "SEASON").agg(pl.col("GAME_ID").n_unique().alias("N"))
    teams = games.select(TEAM_KEYS).unique()
    lagged = [teams.join(per.with_columns((pl.col("SEASON") + k).alias("SEASON")),
                         on=["LEAGUE", "TEAM_ID", "SEASON"], how="left").select(*TEAM_KEYS, pl.col("N").fill_null(0))
              for k in range(1, FRANCHISE_SEASONS + 1)]
    return (pl.concat(lagged).group_by(TEAM_KEYS).agg(pl.col("N").sum().cast(pl.Float64).alias("FRAN_EXP"))
              .sort(TEAM_KEYS))


def team_gaps(games: pl.DataFrame) -> pl.DataFrame:
    """Per team-series: own Game 1 minus own Games 2 on, for 3P% and attempt
    rate (pooled sums) and PF100 (Game 1 value minus mean of later games)."""
    tm = team_game_metrics(games)
    g1 = tm.filter(pl.col("GAME_NO") == 1).group_by(TEAM_KEYS).agg(
        pl.col("FG3M").sum().alias("M1"), pl.col("FG3A").sum().alias("A1"), pl.col("FGA").sum().alias("F1"),
        pl.col("PF100").mean().alias("PF1"))
    rest = tm.filter(pl.col("GAME_NO") >= 2).group_by(TEAM_KEYS).agg(
        pl.col("FG3M").sum().alias("MR"), pl.col("FG3A").sum().alias("AR"), pl.col("FGA").sum().alias("FR"),
        pl.col("PF100").mean().alias("PFR"))
    return (g1.join(rest, on=TEAM_KEYS)
              .select(*TEAM_KEYS,
                      (ratio(pl.col("M1"), pl.col("A1")) - ratio(pl.col("MR"), pl.col("AR"))).alias("DP"),
                      (ratio(pl.col("A1"), pl.col("F1")) - ratio(pl.col("AR"), pl.col("FR"))).alias("DR"),
                      (pl.col("PF1") - pl.col("PFR")).alias("DPF"))
              .sort(TEAM_KEYS))


def contrasts(gaps: pl.DataFrame, exp: pl.DataFrame, col: str) -> pl.DataFrame:
    """Per series: GAP (more minus less experienced) and the more experienced
    team's gaps minus the less experienced team's. Contrasts are null when
    the two teams' experience is equal or either is missing."""
    t = gaps.join(exp, on=TEAM_KEYS).sort([*SERIES_KEYS, col, "TEAM_ID"], descending=[False, False, False, True, False])
    hi = t.group_by(SERIES_KEYS, maintain_order=True).first()
    lo = t.group_by(SERIES_KEYS, maintain_order=True).last()
    j = hi.join(lo, on=SERIES_KEYS, suffix="_LO")
    gap = pl.col(col) - pl.col(f"{col}_LO")
    ok = gap > 0
    return (j.select(*SERIES_KEYS, gap.alias("GAP"),
                     pl.when(ok).then(pl.col("DP") - pl.col("DP_LO")).alias("CONTRAST_PCT"),
                     pl.when(ok).then(pl.col("DR") - pl.col("DR_LO")).alias("CONTRAST_RATE"),
                     pl.when(ok).then(pl.col("DPF") - pl.col("DPF_LO")).alias("CONTRAST_PF"))
             .sort(SERIES_KEYS))


def quantile7(values: list[float], p: float) -> float:
    """R's default quantile (type 7): linear interpolation between order statistics."""
    v = sorted(values)
    h = (len(v) - 1) * p
    lo = math.floor(h)
    return v[lo] + (h - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo])


def summary(cv: pl.DataFrame, measure: str) -> pl.DataFrame:
    """Per league: contrasts by tercile of the nonzero gap, and for every
    nonzero gap, with the cut points and the count of equal-experience series."""
    rows = []
    for league in sorted(cv["LEAGUE"].unique().to_list()):
        lv = cv.filter(pl.col("LEAGUE") == league)
        pos = lv.filter(pl.col("GAP") > 0)
        equal = lv.filter(pl.col("GAP") == 0).height
        gaps = pos["GAP"].to_list()
        q1, q2 = quantile7(gaps, 1 / 3), quantile7(gaps, 2 / 3)
        bins = {"low": pl.col("GAP") <= q1, "middle": (pl.col("GAP") > q1) & (pl.col("GAP") <= q2),
                "high": pl.col("GAP") > q2, "any": pl.lit(True)}
        for b, cond in bins.items():
            bv = pos.filter(cond)
            for m in CONTRASTS:
                rows.append({"LEAGUE": league, "MEASURE": measure, "BIN": b, "METRIC": m, "Q1": q1, "Q2": q2,
                             "EQUAL_SERIES": equal, **describe(bv[m].to_list())})
    return pl.DataFrame(rows)


def coverage(players: pl.DataFrame, seasons: pl.DataFrame) -> pl.DataFrame:
    """Player rows per league-season harvested (zero for an empty file)."""
    n = players.group_by("LEAGUE", "SEASON").agg(pl.len().alias("PLAYER_ROWS"))
    return (seasons.join(n, on=["LEAGUE", "SEASON"], how="left")
                   .with_columns(pl.col("PLAYER_ROWS").fill_null(0)).sort("LEAGUE", "SEASON"))
