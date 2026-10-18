"""Assemble every harvested postseason into series and check them.

Reads data/raw/gamelogs/ (from 01) and writes:

- data/team_games.csv: one row per team per playoff game, with its series,
  game number, home flag, rest days, and both teams' box-score counts.
  Only games in valid series.
- data/team_seasons.csv: regular-season baselines per team (3P% made and
  allowed, attempt rate, foul and turnover rates per 100 possessions).
- output/series.csv: one row per series, valid or not, with the reason.
- output/coverage.csv: per league-season, the share of playoff rows with
  each count present, so era cutoffs come from the data.

Fails (non-zero exit) when an encoded game number disagrees with the
date-order game number, or when a series fails validation outside the known
cases listed in KNOWN_INVALID. Every invalid series is printed, so a new one
cannot pass silently.

    python python/02_build_series.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pslib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "gamelogs"
DATA = ROOT / "data"
OUT = ROOT / "output"

# Invalid series that are expected, keyed by league, season, and the
# validator's reason, with why. Filled from the first full build (October 18,
# 2026); any other invalid series, including a different reason in a listed
# season, is a failure.
KNOWN_INVALID: dict[tuple[str, int, str], str] = {
    ("00", 1954, "pair met twice"):
        "division round robins: each pair met in the round robin and again later",
    ("10", 2026, "Finals shorter than an earlier round"):
        "Finals in progress at harvest (Game 1 played October 17, 2026); delete "
        "data/raw/gamelogs/wnba_2026_po.csv and rerun 01 once it ends, then drop this entry",
}


def possessions(prefix: str = "") -> pl.Expr:
    """Basic possession estimate: FGA + 0.44 FTA - OREB + TOV."""
    c = lambda s: pl.col(prefix + s)  # noqa: E731
    return c("FGA") + 0.44 * c("FTA") - c("OREB") + c("TOV")


def load(league: str, end_year: int, key: str) -> pl.DataFrame:
    name = RAW / pslib_file(league, end_year, key)
    if not name.exists():
        return pl.DataFrame(schema={k: v for k, v in pslib.LOG_SCHEMA.items()})
    return pslib.read_log(name)


def pslib_file(league: str, end_year: int, key: str) -> str:
    return f"{'nba' if league == '00' else 'wnba'}_{end_year}_{key}.csv"


def seasons() -> list[tuple[str, int]]:
    out = []
    for p in sorted(RAW.glob("*_po.csv")):
        lg, year, _ = p.stem.split("_")
        out.append(("00" if lg == "nba" else "10", int(year)))
    return out


def build_season(league: str, year: int):
    po = load(league, year, "po")
    rs = load(league, year, "rs")
    pi = load(league, year, "pi")
    if po.height == 0:
        return None
    s = pslib.assign_series(pslib.pair_games(po))

    # Encoded game numbers must match date order.
    s = s.with_columns(
        pl.col("GAME_ID").map_elements(lambda g: pslib.id_game_no(g, league, year),
                                       return_dtype=pl.Int64).alias("ID_GAME_NO"),
        pl.col("GAME_ID").map_elements(lambda g: pslib.id_round(g, year),
                                       return_dtype=pl.Int64).alias("ROUND"))
    clash = s.filter(pl.col("ID_GAME_NO").is_not_null() & (pl.col("ID_GAME_NO") != pl.col("GAME_NO")))
    rounds = s.group_by("SERIES_KEY").agg(pl.col("ROUND").n_unique().alias("NR"))
    if rounds.filter(pl.col("NR") > 1).height:
        clash = pl.concat([clash, s.filter(pl.col("SERIES_KEY").is_in(
            rounds.filter(pl.col("NR") > 1)["SERIES_KEY"].implode()))], how="diagonal_relaxed")

    sched = pl.concat([d.select("TEAM_ID", "GAME_ID", "GAME_DATE") for d in (rs, pi, po) if d.height])
    s = s.join(pslib.rest_days(sched), on=["TEAM_ID", "GAME_ID"], how="left")
    opp_rest = s.select("GAME_ID", pl.col("TEAM_ID").alias("OPP_ID"), pl.col("REST").alias("OPP_REST"))
    s = s.join(opp_rest, on=["GAME_ID", "OPP_ID"], how="left")

    # Last series of the postseason is the Finals; each team's series ordinal.
    last_date = s["GAME_DATE"].max()
    finals = s.filter(pl.col("GAME_DATE") == last_date)["SERIES_KEY"].unique().to_list()
    starts = (s.group_by("SERIES_KEY", "TEAM_ID").agg(pl.col("GAME_DATE").min().alias("START"))
               .sort("TEAM_ID", "START")
               .with_columns(pl.int_range(1, pl.len() + 1).over("TEAM_ID").alias("TEAM_SERIES_NO")))
    s = (s.join(starts.select("SERIES_KEY", "TEAM_ID", "TEAM_SERIES_NO"), on=["SERIES_KEY", "TEAM_ID"])
          .with_columns(pl.col("SERIES_KEY").is_in(finals).alias("FINALS"),
                        pl.lit(league).alias("LEAGUE"), pl.lit(year).alias("SEASON")))

    v = pslib.validate_series(s)
    per_series = s.select("SERIES_KEY", "ROUND", "FINALS", "WINS_NEEDED").unique()
    fmt = pslib.format_flags(per_series)
    v = (v.join(per_series.select("SERIES_KEY", "ROUND", "FINALS"), on="SERIES_KEY")
          .join(fmt, on="SERIES_KEY", how="left")
          .with_columns(pl.coalesce("INVALID_REASON", "FORMAT_REASON").alias("INVALID_REASON"))
          .with_columns(pl.col("INVALID_REASON").is_null().alias("VALID"),
                        pl.lit(league).alias("LEAGUE"), pl.lit(year).alias("SEASON"))
          .drop("FORMAT_REASON"))

    cov = po.select([pl.col(c).is_not_null().mean().alias(c) for c in pslib.STATS]).with_columns(
        pl.lit(league).alias("LEAGUE"), pl.lit(year).alias("SEASON"), pl.lit(po.height).alias("ROWS"))

    base = None
    if rs.height:
        r = pslib.pair_games(rs).with_columns(possessions().alias("POSS"))
        # A total is blank unless every game behind it has the count
        # (pslib.full_sum; found October 18, 2026).
        full = pslib.full_sum
        base = (r.group_by("TEAM_ID").agg(
                    pl.len().alias("RS_GAMES"),
                    *[full(c, f"RS_{c}") for c in ("FG3M", "FG3A", "FGA", "PF", "TOV")],
                    *[full(f"OPP_{c}", f"RS_OPP_{c}") for c in ("FG3M", "FG3A", "FGA")],
                    full("POSS", "RS_POSS"))
                 .with_columns(pl.lit(league).alias("LEAGUE"), pl.lit(year).alias("SEASON")))
    return s, v, clash, cov, base


def main() -> int:
    DATA.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    games, series, covs, bases, failures = [], [], [], [], []
    for league, year in seasons():
        built = build_season(league, year)
        if built is None:
            continue
        s, v, clash, cov, base = built
        if clash.height:
            failures.append(f"{league} {year}: {clash.height} rows where the ID game number differs from date order")
        bad = v.filter(~pl.col("VALID"))
        for row in bad.iter_rows(named=True):
            known = KNOWN_INVALID.get((league, year, row["INVALID_REASON"]))
            tag = "known" if known else "UNEXPECTED"
            print(f"invalid series ({tag}): {league} {year} {row['SERIES_KEY']} {row['INVALID_REASON']}")
            if not known:
                failures.append(f"{league} {year} {row['SERIES_KEY']}: {row['INVALID_REASON']}")
        valid_keys = v.filter(pl.col("VALID"))["SERIES_KEY"]
        games.append(s.filter(pl.col("SERIES_KEY").is_in(valid_keys.implode())))
        series.append(v)
        covs.append(cov)
        if base is not None:
            bases.append(base)

    tg = pl.concat(games, how="diagonal_relaxed").drop("ID_GAME_NO")
    tg = tg.with_columns(pl.col("GAME_DATE").cast(pl.Utf8))
    tg.sort("LEAGUE", "SEASON", "SERIES_KEY", "GAME_NO", "TEAM_ID").write_csv(DATA / "team_games.csv")
    pl.concat(series).sort("LEAGUE", "SEASON", "SERIES_KEY").write_csv(OUT / "series.csv")
    pl.concat(covs).sort("LEAGUE", "SEASON").write_csv(OUT / "coverage.csv")
    pl.concat(bases).sort("LEAGUE", "SEASON", "TEAM_ID").write_csv(DATA / "team_seasons.csv")

    sr = pl.concat(series)
    print(f"series: {sr.height} total, {sr['VALID'].sum()} valid; team-game rows written: {tg.height}")
    if failures:
        print("FAILED:")
        for f in failures:
            print("  " + f)
        return 1
    print("series build: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
