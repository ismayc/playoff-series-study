"""Question 1: is Game 1 three-point shooting worse than the rest of the series?

Implements the pre-specified analysis in docs/design.md (R/03_game1.R is the
independent twin; 04_reconcile.py compares them). Reads data/team_games.csv,
data/team_seasons.csv, and output/coverage.csv from 02. Writes, under
output/ (or the directory given with --out):

- game1_series.csv: one row per series, both teams pooled.
- game1_team.csv: one row per team per series, home or road in Game 1.
- game1_summary.csv: mean, sd, and 95% interval per league, panel, metric.
- game1_pooled.csv: attempt-weighted league totals.
- game1_season.csv: attempt-weighted totals per league and season.

    python python/03_game1.py [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game1lib as g1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # Infer from the whole file: the first rows are 1947 games whose
    # three-point counts are blank, which a short inference reads as text.
    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    ts = pl.read_csv(ROOT / "data" / "team_seasons.csv", infer_schema_length=None)
    cov = pl.read_csv(ROOT / "output" / "coverage.csv")

    games = g1.add_expected(g1.sample(tg, cov), ts)
    missing = games.filter(pl.col("EXP_PCT").is_null()).height
    series = g1.series_values(games)
    team = g1.team_values(games)
    if series.height == 0 or team.height == 0:
        print("FAILED: empty sample; check data/ and output/coverage.csv")
        return 1

    summary = pl.concat([
        g1.summarize(series, g1.series_panels(series), g1.SERIES_METRICS),
        g1.summarize(team, g1.TEAM_PANELS, g1.TEAM_METRICS),
    ])
    series.write_csv(args.out / "game1_series.csv")
    team.write_csv(args.out / "game1_team.csv")
    summary.write_csv(args.out / "game1_summary.csv")
    g1.pooled(series).write_csv(args.out / "game1_pooled.csv")
    g1.season_values(series).write_csv(args.out / "game1_season.csv")

    print(f"game1: {series.height} series, {team.height} team-series, "
          f"{missing} team-game rows without an expected 3P%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
