"""Follow-ups 5 to 7: the Game 1 three-point winner and the series, format
breaks, and question 4 profiles by decade.

Implements "Follow-ups 5 to 8, fixed October 19, 2026" in docs/design.md
(R/11_followups.R is the twin; 04_reconcile.py compares them). Reads 02's
tables and 06's profile_games.csv. Writes:

- outshoot_series.csv: one row per series (local; gitignored).
- outshoot_summary.csv: series-win shares per league.
- break_series.csv: one row per series (local; gitignored).
- break_summary.csv: question 1 metrics and Game 1 fouls by 2020 and by length.
- profile_decade.csv: question 4 profile by league, decade, and game number.

    python python/11_followups.py [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import followlib as fl  # noqa: E402
import game1lib as g1  # noqa: E402

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
    dev = pl.read_csv(ROOT / "output" / "profile_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})

    games = g1.add_expected(g1.sample(tg, cov), ts)
    ov = fl.outshoot_values(games)
    bv = fl.break_values(g1.series_values(games), games, dev)
    pd = fl.profile_decade(dev)
    if ov.height == 0 or bv.height == 0 or pd.height == 0:
        print(f"FAILED: empty table (outshoot {ov.height}, breaks {bv.height}, decades {pd.height})")
        return 1
    no_profile = bv["G1_PF100"].null_count()

    ov.write_csv(args.out / "outshoot_series.csv")
    fl.outshoot_summary(ov).write_csv(args.out / "outshoot_summary.csv")
    bv.write_csv(args.out / "break_series.csv")
    fl.break_summary(bv).write_csv(args.out / "break_summary.csv")
    pd.write_csv(args.out / "profile_decade.csv")
    print(f"follow-ups: {ov.height} series ({ov['OUTSHOT'].null_count()} without a Game 1 three-point "
          f"winner), {no_profile} series without a question 4 Game 1, {pd.height} decade profile rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
