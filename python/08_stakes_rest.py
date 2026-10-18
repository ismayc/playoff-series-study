"""Question 3: does the Game 1 gap change with the stakes (stage) or with the
rest gap between the two teams?

Implements "Question 3, fixed October 18, 2026" in docs/design.md
(R/08_stakes_rest.R is the twin; 04_reconcile.py compares them). Fails when
any series' stage disagrees with its encoded round. Writes:

- series_stage.csv: STAGE for every valid series.
- stakes_summary.csv: question 1 metrics by league and stage.
- rest_series.csv: rest gap and rested-minus-tired contrasts per series.
- rest_summary.csv: contrasts by league and gap bin.

    python python/08_stakes_rest.py [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game1lib as g1  # noqa: E402
import stagelib as sl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    ts = pl.read_csv(ROOT / "data" / "team_seasons.csv", infer_schema_length=None)
    cov = pl.read_csv(ROOT / "output" / "coverage.csv")

    st = sl.stages(tg)
    bad = sl.stage_mismatches(tg, st)
    if bad.height:
        print(f"FAILED: {bad.height} series whose stage disagrees with the encoded round")
        print(bad.head(10))
        return 1
    lost = sl.unexplained_missing_stages(tg, st)
    if lost.height:
        print(f"FAILED: {lost.height} series without a stage in a season that has a Finals")
        print(lost.head(10))
        return 1
    encoded = (tg.filter(pl.col("ROUND").is_not_null()).select(sl.SERIES_KEYS).unique()
                 .join(st.filter(pl.col("STAGE").is_not_null()), on=sl.SERIES_KEYS).height)
    if encoded == 0:
        print("FAILED: no encoded rounds to check stage against")
        return 1

    games = g1.add_expected(g1.sample(tg, cov), ts)
    sv = g1.series_values(games).join(st, on=sl.SERIES_KEYS, how="left")
    rv = sl.rest_values(games)

    st.write_csv(args.out / "series_stage.csv")
    sl.stake_summary(sv).write_csv(args.out / "stakes_summary.csv")
    rv.write_csv(args.out / "rest_series.csv")
    sl.rest_summary(rv).write_csv(args.out / "rest_summary.csv")
    print(f"stakes and rest: stage matches the encoded round in all {encoded} encoded series; "
          f"{st['STAGE'].null_count()} series without a stage; {sv['STAGE'].null_count()} of "
          f"{sv.height} sample series without one; {rv.filter(pl.col('GAP') == 0).height} zero-gap series")
    return 0


if __name__ == "__main__":
    sys.exit(main())
