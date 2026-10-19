"""Follow-up 9: experienced against inexperienced teams.

Implements "Follow-up 9, fixed October 19, 2026" in docs/design.md
(R/14_experience.R is the twin; 04_reconcile.py compares them). Reads 02's
tables, the raw team playoff logs, and the player logs from
13_harvest_players.py; first writes data/player_games.csv and
data/team_playoff_games.csv, the flattened inputs both twins read. Writes:

- experience_coverage.csv: player rows per league-season harvested.
- experience_team.csv, experience_series.csv: per team-series and per
  series (local; gitignored).
- experience_summary.csv: contrasts by league, measure, and gap tercile.

    python python/14_experience.py [--out DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiencelib as ex  # noqa: E402
import game1lib as g1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"(nba|wnba)_(\d{4})_po\.csv")


def read_logs(folder: Path, cols: list[str]) -> pl.DataFrame:
    frames = []
    for f in sorted(folder.glob("*_po.csv")):
        m = NAME.fullmatch(f.name)
        if not m:
            continue
        d = pl.read_csv(f, infer_schema_length=0)
        d = d.select(cols) if d.height else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
        frames.append(d.with_columns(pl.lit(0 if m[1] == "nba" else 10).alias("LEAGUE"),
                                     pl.lit(int(m[2])).alias("SEASON")))
    return pl.concat(frames)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    praw = ROOT / "data" / "raw" / "playerlogs"
    if not list(praw.glob("*_po.csv")):
        print(f"FAILED: no player logs in {praw}; run python/13_harvest_players.py")
        return 1
    players = (read_logs(praw, ["GAME_ID", "TEAM_ID", "PLAYER_ID", "MIN"])
               .with_columns(pl.col("TEAM_ID").cast(pl.Int64), pl.col("PLAYER_ID").cast(pl.Int64),
                             pl.col("MIN").cast(pl.Float64)))
    teams = (read_logs(ROOT / "data" / "raw" / "gamelogs", ["GAME_ID", "TEAM_ID"])
             .with_columns(pl.col("TEAM_ID").cast(pl.Int64)))
    players.write_csv(ROOT / "data" / "player_games.csv")
    teams.write_csv(ROOT / "data" / "team_playoff_games.csv")

    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    cov = pl.read_csv(ROOT / "output" / "coverage.csv")
    games = g1.sample(tg, cov)

    seasons = teams.select("LEAGUE", "SEASON").unique()
    pc = ex.coverage(players, seasons)
    exp = ex.roster_experience(players, games).join(ex.franchise_experience(teams, games), on=ex.TEAM_KEYS, how="full",
                                                    coalesce=True)
    gaps = ex.team_gaps(games)
    team = gaps.join(exp, on=ex.TEAM_KEYS, how="left").sort(ex.TEAM_KEYS)
    series, summaries = [], []
    for measure, col in ex.MEASURES.items():
        cv = ex.contrasts(gaps, exp.select(*ex.TEAM_KEYS, col).drop_nulls(col), col)
        series.append(cv.with_columns(pl.lit(measure).alias("MEASURE")))
        summaries.append(ex.summary(cv, measure))
    if team.height == 0 or any(s.height == 0 for s in series):
        print("FAILED: empty experience table")
        return 1
    missing = team["ROSTER_EXP"].null_count()

    pc.write_csv(args.out / "experience_coverage.csv")
    team.write_csv(args.out / "experience_team.csv")
    pl.concat(series).select("MEASURE", *ex.SERIES_KEYS, "GAP", *ex.CONTRASTS).write_csv(args.out / "experience_series.csv")
    pl.concat(summaries).write_csv(args.out / "experience_summary.csv")
    empty = pc.filter(pl.col("PLAYER_ROWS") == 0)
    print(f"experience: {team.height} team-series ({missing} without a roster value), "
          f"{empty.height} harvested seasons with no player rows "
          f"({', '.join(f'{lg}:{s}' for lg, s in empty.select('LEAGUE', 'SEASON').iter_rows()) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
