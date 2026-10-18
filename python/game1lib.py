"""Question 1, the Game 1 three-point dip: the definitions in docs/design.md
as pure functions. R/functions.R mirrors every one of them, and the tests in
tests/python and tests/R pin both to the same hand-worked fixtures.

Segments of a series: G1 is Game 1, REST is Games 2 through the last, G2 is
Game 2 alone (the selection-free comparison).
"""

from __future__ import annotations

import math

import polars as pl

SERIES_KEYS = ["LEAGUE", "SEASON", "SERIES_KEY"]
SEGMENTS = {"G1": pl.col("GAME_NO") == 1, "REST": pl.col("GAME_NO") >= 2, "G2": pl.col("GAME_NO") == 2}
SERIES_METRICS = ["D_PCT", "D2_PCT", "D_RATE", "D2_RATE", "RESID_G1", "RESID_REST"]
TEAM_METRICS = ["TEAM_D_PCT", "TEAM_RESID_G1", "TEAM_RESID_REST"]
Z = 1.96
# Neutral-site postseasons (Amendment 1): out of the home and road split only.
NEUTRAL_SEASONS = [2020]


def complete_seasons(coverage: pl.DataFrame) -> pl.DataFrame:
    """League-seasons whose playoff rows all carry FG3M, FG3A, and FGA."""
    return (coverage.filter((pl.col("FG3M") == 1) & (pl.col("FG3A") == 1) & (pl.col("FGA") == 1))
                    .select("LEAGUE", "SEASON"))


def sample(team_games: pl.DataFrame, coverage: pl.DataFrame) -> pl.DataFrame:
    """Valid series (team_games holds only those) of two or more games in complete seasons."""
    return (team_games.join(complete_seasons(coverage), on=["LEAGUE", "SEASON"])
                      .filter(pl.col("N_GAMES") >= 2))


def ratio(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    """num / den, null when den is zero or null."""
    return pl.when(den > 0).then(num / den).otherwise(None)


def add_expected(games: pl.DataFrame, team_seasons: pl.DataFrame) -> pl.DataFrame:
    """Attach EXP_PCT: team 3P% plus opponent 3P% allowed minus league 3P%,
    all regular season. Null when any piece is missing or has no attempts."""
    league = (team_seasons.group_by("LEAGUE", "SEASON")
                          .agg(ratio(pl.col("RS_FG3M").sum(), pl.col("RS_FG3A").sum()).alias("LG_PCT")))
    own = team_seasons.select("LEAGUE", "SEASON", "TEAM_ID",
                              ratio(pl.col("RS_FG3M"), pl.col("RS_FG3A")).alias("OWN_PCT"))
    allowed = team_seasons.select("LEAGUE", "SEASON", pl.col("TEAM_ID").alias("OPP_ID"),
                                  ratio(pl.col("RS_OPP_FG3M"), pl.col("RS_OPP_FG3A")).alias("ALLOWED_PCT"))
    return (games.join(own, on=["LEAGUE", "SEASON", "TEAM_ID"], how="left")
                 .join(allowed, on=["LEAGUE", "SEASON", "OPP_ID"], how="left")
                 .join(league, on=["LEAGUE", "SEASON"], how="left")
                 .with_columns((pl.col("OWN_PCT") + pl.col("ALLOWED_PCT") - pl.col("LG_PCT")).alias("EXP_PCT"))
                 .drop("OWN_PCT", "ALLOWED_PCT", "LG_PCT"))


def segment_sums(games: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Per key group and segment: M, A, FGA, and EA (sum of EXP_PCT * FG3A,
    null if any row in the segment lacks EXP_PCT)."""
    parts = []
    for name, cond in SEGMENTS.items():
        g = games.filter(cond).group_by(keys).agg(
            pl.col("FG3M").sum().alias(f"{name}_M"),
            pl.col("FG3A").sum().alias(f"{name}_A"),
            pl.col("FGA").sum().alias(f"{name}_FGA"),
            pl.when(pl.col("EXP_PCT").null_count() == 0)
              .then((pl.col("EXP_PCT") * pl.col("FG3A")).sum()).otherwise(None).alias(f"{name}_EA"))
        parts.append(g)
    out = parts[0]
    for p in parts[1:]:
        out = out.join(p, on=keys, how="left")
    return out


def with_metrics(sums: pl.DataFrame, team: bool = False) -> pl.DataFrame:
    """Percentages, rates, residuals, and the differences, from segment sums."""
    pct = {s: ratio(pl.col(f"{s}_M"), pl.col(f"{s}_A")) for s in SEGMENTS}
    rate = {s: ratio(pl.col(f"{s}_A"), pl.col(f"{s}_FGA")) for s in SEGMENTS}
    resid = {s: ratio(pl.col(f"{s}_M") - pl.col(f"{s}_EA"), pl.col(f"{s}_A")) for s in ("G1", "REST")}
    cols = [pct[s].alias(f"{s}_PCT") for s in SEGMENTS] + [rate[s].alias(f"{s}_RATE") for s in SEGMENTS]
    if team:
        return sums.with_columns(*cols).with_columns(
            (pl.col("G1_PCT") - pl.col("REST_PCT")).alias("TEAM_D_PCT"),
            resid["G1"].alias("TEAM_RESID_G1"), resid["REST"].alias("TEAM_RESID_REST"))
    return sums.with_columns(*cols).with_columns(
        (pl.col("G1_PCT") - pl.col("REST_PCT")).alias("D_PCT"),
        (pl.col("G1_PCT") - pl.col("G2_PCT")).alias("D2_PCT"),
        (pl.col("G1_RATE") - pl.col("REST_RATE")).alias("D_RATE"),
        (pl.col("G1_RATE") - pl.col("G2_RATE")).alias("D2_RATE"),
        resid["G1"].alias("RESID_G1"), resid["REST"].alias("RESID_REST"))


def series_values(games: pl.DataFrame) -> pl.DataFrame:
    """One row per series, both teams pooled, with DECADE."""
    return (with_metrics(segment_sums(games, SERIES_KEYS))
            .with_columns(((pl.col("SEASON") // 10) * 10).alias("DECADE"))
            .sort(SERIES_KEYS))


def team_values(games: pl.DataFrame) -> pl.DataFrame:
    """One row per team per series, with HOME as of that team's Game 1.
    Neutral-site seasons are dropped here (Amendment 1)."""
    g = games.filter(~pl.col("SEASON").is_in(NEUTRAL_SEASONS))
    home = g.filter(pl.col("GAME_NO") == 1).select(*SERIES_KEYS, "TEAM_ID", pl.col("HOME").alias("G1_HOME"))
    keys = [*SERIES_KEYS, "TEAM_ID"]
    return (with_metrics(segment_sums(g, keys), team=True).join(home, on=keys).sort(keys))


def describe(values: list[float | None]) -> dict:
    """N, N_DROPPED, MEAN, SD (n - 1), SE, and the normal 95% interval.

    Written as plain arithmetic so R/functions.R can match it term for term.
    SD and everything after it are None when fewer than two values remain.
    """
    kept = [v for v in values if v is not None and not math.isnan(v)]
    n = len(kept)
    out = {"N": n, "N_DROPPED": len(values) - n, "MEAN": None, "SD": None, "SE": None, "LO": None, "HI": None}
    if n == 0:
        return out
    mean = sum(kept) / n
    out["MEAN"] = mean
    if n < 2:
        return out
    sd = math.sqrt(sum((v - mean) ** 2 for v in kept) / (n - 1))
    se = sd / math.sqrt(n)
    out.update(SD=sd, SE=se, LO=mean - Z * se, HI=mean + Z * se)
    return out


def summarize(values: pl.DataFrame, panels: dict[str, pl.Expr], metrics: list[str]) -> pl.DataFrame:
    """Long table: one row per league, panel, and metric."""
    rows = []
    for league in sorted(values["LEAGUE"].unique().to_list()):
        lv = values.filter(pl.col("LEAGUE") == league)
        for panel, cond in panels.items():
            pv = lv.filter(cond)
            if pv.height == 0:
                continue
            for m in metrics:
                rows.append({"LEAGUE": league, "PANEL": panel, "METRIC": m, **describe(pv[m].to_list())})
    return pl.DataFrame(rows, schema={"LEAGUE": pl.Int64, "PANEL": pl.Utf8, "METRIC": pl.Utf8,
                                      "N": pl.Int64, "N_DROPPED": pl.Int64, "MEAN": pl.Float64,
                                      "SD": pl.Float64, "SE": pl.Float64, "LO": pl.Float64, "HI": pl.Float64})


def series_panels(values: pl.DataFrame) -> dict[str, pl.Expr]:
    panels = {"all": pl.lit(True)}
    for d in sorted(values["DECADE"].unique().to_list()):
        panels[f"{d}s"] = pl.col("DECADE") == d
    return panels


TEAM_PANELS = {"home": pl.col("G1_HOME"), "road": ~pl.col("G1_HOME")}


def pooled(values: pl.DataFrame) -> pl.DataFrame:
    """Attempt-weighted league totals: every Game 1 three against every later one."""
    return (values.group_by("LEAGUE").agg(
                pl.len().alias("SERIES"),
                *[pl.col(f"{s}_{k}").sum().alias(f"{s}_{k}") for s in ("G1", "REST") for k in ("M", "A")])
            .with_columns((pl.col("G1_M") / pl.col("G1_A")).alias("G1_PCT"),
                          (pl.col("REST_M") / pl.col("REST_A")).alias("REST_PCT"))
            .with_columns((pl.col("G1_PCT") - pl.col("REST_PCT")).alias("D_PCT"))
            .sort("LEAGUE"))


def season_values(values: pl.DataFrame) -> pl.DataFrame:
    """Attempt-weighted totals per league and season: the level of Game 1 and
    later-game shooting over time (exploratory, not in the pre-specification)."""
    sums = [pl.col(f"{s}_{k}").sum().alias(f"{s}_{k}") for s in ("G1", "REST") for k in ("M", "A", "FGA")]
    return (values.group_by("LEAGUE", "SEASON").agg(pl.len().alias("SERIES"), *sums)
            .with_columns(ratio(pl.col("G1_M"), pl.col("G1_A")).alias("G1_PCT"),
                          ratio(pl.col("REST_M"), pl.col("REST_A")).alias("REST_PCT"),
                          ratio(pl.col("G1_A"), pl.col("G1_FGA")).alias("G1_RATE"),
                          ratio(pl.col("REST_A"), pl.col("REST_FGA")).alias("REST_RATE"))
            .with_columns((pl.col("G1_PCT") - pl.col("REST_PCT")).alias("D_PCT"),
                          (pl.col("G1_RATE") - pl.col("REST_RATE")).alias("D_RATE"))
            .sort("LEAGUE", "SEASON"))
