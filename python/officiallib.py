"""Follow-up 8, fouls and the officials: the definitions in docs/design.md
("8. Fouls and the officials") as pure functions. R/functions.R mirrors
them; both are pinned to tests/fixtures/official_games.csv and
tests/fixtures/official_crews.csv.

Inputs: the question 4 game table (profile_games.csv, one row per game with
its PF100 deviation), the game ids from team_games.csv, and
data/game_officials.csv (one row per game and listed official, flattened
from the raw harvest by flatten_officials).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import polars as pl

from game1lib import SERIES_KEYS, Z, describe

GAME_KEYS = [*SERIES_KEYS, "GAME_NO"]
CREW_SIZE = 3
MIN_OTHER_GAMES = 5    # 8b: games in other series behind an official's tendency
MIN_SPLIT_GAMES = 3    # 8c: Game 1s and later games per official
MIN_HALF_GAMES = 10    # 8d: games per official in each season half


def flatten_officials(raw_dir: Path) -> pl.DataFrame:
    """One row per harvested game and listed official; a game with an empty
    list gets one row with a null OFFICIAL_ID, so it is still counted."""
    rows = []
    for f in sorted(raw_dir.glob("*.json")):
        officials = json.loads(f.read_text())
        if not officials:
            rows.append({"GAME_ID": f.stem, "OFFICIAL_ID": None})
        rows += [{"GAME_ID": f.stem, "OFFICIAL_ID": int(o["personId"])} for o in officials]
    return pl.DataFrame(rows, schema={"GAME_ID": pl.Utf8, "OFFICIAL_ID": pl.Int64})


def game_ids(team_games: pl.DataFrame) -> pl.DataFrame:
    return team_games.select(*GAME_KEYS, "GAME_ID").unique().sort(GAME_KEYS)


def coverage(dev: pl.DataFrame, ids: pl.DataFrame, crews: pl.DataFrame, first: dict[int, int]) -> pl.DataFrame:
    """Per league-season from the first officials season: question 4 games,
    games harvested, and games listing exactly three officials."""
    keep = pl.lit(False)
    for league, season in first.items():
        keep = keep | ((pl.col("LEAGUE") == league) & (pl.col("SEASON") >= season))
    n = crews.group_by("GAME_ID").agg(pl.col("OFFICIAL_ID").drop_nulls().n_unique().alias("N_OFF"))
    g = dev.filter(keep).select(GAME_KEYS).join(ids, on=GAME_KEYS, how="left").join(n, on="GAME_ID", how="left")
    return (g.group_by("LEAGUE", "SEASON")
             .agg(pl.len().alias("GAMES"), pl.col("N_OFF").is_not_null().sum().alias("HARVESTED"),
                  (pl.col("N_OFF") == CREW_SIZE).sum().alias("WITH_CREW"))
             .sort("LEAGUE", "SEASON"))


def sample(dev: pl.DataFrame, ids: pl.DataFrame, crews: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Games listing exactly three officials (with PF100 and RESID, the PF100
    deviation minus the league's mean at that game number in this sample),
    and the matching game-official rows."""
    c = crews.drop_nulls("OFFICIAL_ID").unique()
    full = c.group_by("GAME_ID").agg(pl.len().alias("N_OFF")).filter(pl.col("N_OFF") == CREW_SIZE)
    games = (dev.select(*GAME_KEYS, "PF100").join(ids, on=GAME_KEYS).join(full.select("GAME_ID"), on="GAME_ID")
                .filter(pl.col("PF100").is_not_null())
                .with_columns((pl.col("PF100") - pl.col("PF100").mean().over("LEAGUE", "GAME_NO")).alias("RESID"))
                .sort(GAME_KEYS))
    link = c.join(games.select("GAME_ID", *GAME_KEYS, "PF100", "RESID"), on="GAME_ID").sort([*GAME_KEYS, "OFFICIAL_ID"])
    return games, link


def game1_profile(games: pl.DataFrame) -> pl.DataFrame:
    """8a: mean PF100 deviation by league and game number in this sample."""
    rows = []
    for league in sorted(games["LEAGUE"].unique().to_list()):
        lv = games.filter(pl.col("LEAGUE") == league)
        for g in sorted(lv["GAME_NO"].unique().to_list()):
            rows.append({"LEAGUE": league, "PART": "pf100", "GAME_NO": g,
                         **describe(lv.filter(pl.col("GAME_NO") == g)["PF100"].to_list())})
    return pl.DataFrame(rows)


def crew_values(games: pl.DataFrame, link: pl.DataFrame) -> pl.DataFrame:
    """8b per game: CREW (mean leave-one-series-out tendency of its
    officials) and CREW_DEV (CREW minus its series mean), for series whose
    every question 4 game is in the sample with a CREW value."""
    tot = link.group_by("LEAGUE", "OFFICIAL_ID").agg(pl.col("RESID").sum().alias("T_SUM"), pl.len().alias("T_N"))
    own = link.group_by(*SERIES_KEYS, "OFFICIAL_ID").agg(pl.col("RESID").sum().alias("S_SUM"), pl.len().alias("S_N"))
    tend = (own.join(tot, on=["LEAGUE", "OFFICIAL_ID"])
               .with_columns((pl.col("T_N") - pl.col("S_N")).alias("OTHER_N"))
               .with_columns(pl.when(pl.col("OTHER_N") >= MIN_OTHER_GAMES)
                               .then((pl.col("T_SUM") - pl.col("S_SUM")) / pl.col("OTHER_N"))
                               .otherwise(None).alias("TEND"))
               .select(*SERIES_KEYS, "OFFICIAL_ID", "TEND"))
    crew = (link.select(*GAME_KEYS, "OFFICIAL_ID").join(tend, on=[*SERIES_KEYS, "OFFICIAL_ID"])
                .group_by(GAME_KEYS).agg(pl.col("TEND").mean().alias("CREW")))
    return games.select(*GAME_KEYS).join(crew, on=GAME_KEYS, how="left").sort(GAME_KEYS)


def crew_profile(cv: pl.DataFrame, dev: pl.DataFrame) -> pl.DataFrame:
    """8b: mean CREW_DEV by league and game number over complete series."""
    want = dev.group_by(SERIES_KEYS).agg(pl.len().alias("WANT"))
    have = cv.filter(pl.col("CREW").is_not_null()).group_by(SERIES_KEYS).agg(pl.len().alias("HAVE"))
    ok = want.join(have, on=SERIES_KEYS).filter(pl.col("WANT") == pl.col("HAVE")).select(SERIES_KEYS)
    d = (cv.join(ok, on=SERIES_KEYS)
           .with_columns((pl.col("CREW") - pl.col("CREW").mean().over(SERIES_KEYS)).alias("CREW_DEV")))
    rows = []
    for league in sorted(d["LEAGUE"].unique().to_list()):
        lv = d.filter(pl.col("LEAGUE") == league)
        for g in sorted(lv["GAME_NO"].unique().to_list()):
            rows.append({"LEAGUE": league, "PART": "crew", "GAME_NO": g,
                         **describe(lv.filter(pl.col("GAME_NO") == g)["CREW_DEV"].to_list())})
    return pl.DataFrame(rows)


def within_official(link: pl.DataFrame) -> pl.DataFrame:
    """8c per official: mean PF100 deviation in Game 1s minus in Games 2 on."""
    return (link.group_by("LEAGUE", "OFFICIAL_ID")
                .agg((pl.col("GAME_NO") == 1).sum().alias("N_G1"), (pl.col("GAME_NO") >= 2).sum().alias("N_LATER"),
                     pl.col("PF100").filter(pl.col("GAME_NO") == 1).mean().alias("G1"),
                     pl.col("PF100").filter(pl.col("GAME_NO") >= 2).mean().alias("LATER"))
                .filter((pl.col("N_G1") >= MIN_SPLIT_GAMES) & (pl.col("N_LATER") >= MIN_SPLIT_GAMES))
                .with_columns((pl.col("G1") - pl.col("LATER")).alias("D"))
                .sort("LEAGUE", "OFFICIAL_ID"))


def within_summary(wo: pl.DataFrame) -> pl.DataFrame:
    return pl.DataFrame([{"LEAGUE": lg, **describe(wo.filter(pl.col("LEAGUE") == lg)["D"].to_list())}
                         for lg in sorted(wo["LEAGUE"].unique().to_list())])


def halves(link: pl.DataFrame) -> pl.DataFrame:
    """8d per official: mean RESID in even and in odd seasons."""
    return (link.group_by("LEAGUE", "OFFICIAL_ID")
                .agg((pl.col("SEASON") % 2 == 0).sum().alias("N_EVEN"), (pl.col("SEASON") % 2 == 1).sum().alias("N_ODD"),
                     pl.col("RESID").filter(pl.col("SEASON") % 2 == 0).mean().alias("EVEN"),
                     pl.col("RESID").filter(pl.col("SEASON") % 2 == 1).mean().alias("ODD"))
                .filter((pl.col("N_EVEN") >= MIN_HALF_GAMES) & (pl.col("N_ODD") >= MIN_HALF_GAMES))
                .sort("LEAGUE", "OFFICIAL_ID"))


def pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 2:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None


def reliability(h: pl.DataFrame) -> pl.DataFrame:
    """8d per league: split-half correlation with the Fisher interval."""
    rows = []
    for league in sorted(h["LEAGUE"].unique().to_list()):
        lv = h.filter(pl.col("LEAGUE") == league)
        n = lv.height
        r = pearson(lv["EVEN"].to_list(), lv["ODD"].to_list())
        lo = hi = None
        if r is not None and n > 3 and abs(r) < 1:
            z, se = math.atanh(r), 1 / math.sqrt(n - 3)
            lo, hi = math.tanh(z - Z * se), math.tanh(z + Z * se)
        rows.append({"LEAGUE": league, "N": n, "R": r, "LO": lo, "HI": hi})
    return pl.DataFrame(rows, schema={"LEAGUE": pl.Int64, "N": pl.Int64, "R": pl.Float64,
                                      "LO": pl.Float64, "HI": pl.Float64})
