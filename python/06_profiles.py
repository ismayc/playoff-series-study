"""Question 4: how each box-score rate moves by game number through a series.

Implements "Question 4, fixed October 18, 2026" in docs/design.md
(R/06_profiles.R is the twin; 04_reconcile.py compares them). Writes:

- profile_games.csv: one row per game, each metric's deviation.
- profile_summary.csv: mean deviation by league, panel, game number, metric.
- profile_state.csv: trailing minus leading team three-point volume, per league.

    python python/06_profiles.py [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profilelib as pf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    cov = pl.read_csv(ROOT / "output" / "coverage.csv")
    tm = pf.team_game_metrics(pf.sample(tg, cov))
    if tm.height == 0:
        print("FAILED: empty sample")
        return 1
    dev = pf.game_deviations(tm)
    state, tied = pf.series_state(tm)

    dev.write_csv(args.out / "profile_games.csv")
    pf.profiles(dev).write_csv(args.out / "profile_summary.csv")
    pf.state_summary(state, tied).write_csv(args.out / "profile_state.csv")
    print(f"profiles: {dev.height} games, {state.height} games with a series leader, "
          f"{sum(tied.values())} tied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
