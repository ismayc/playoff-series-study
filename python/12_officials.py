"""Follow-up 8: fouls and the officials.

Implements "8. Fouls and the officials" in docs/design.md (R/12_officials.R
is the twin; 04_reconcile.py compares them). First flattens the raw harvest
(data/raw/officials/, from 10_harvest_officials.py) into
data/game_officials.csv, and the cached liveData box scores
(data/raw/live/, copied from the October 19, 2026 audit) into
data/live_officials.csv; both twins read the two. Reads 06's
profile_games.csv. Writes:

- officials_coverage.csv: games, games harvested, games with a crew of
  three, and how many of those had the alternate identified by liveData.
- officials_profile.csv: 8a (PART pf100) and 8b (PART crew) by game number.
- officials_within.csv: 8c, Game 1 minus later games with the official fixed.
- officials_reliability.csv: 8d, split-half correlation of officials.
- officials_crew_games.csv, officials_people.csv, officials_halves.csv:
  per game and per official (local; gitignored).

    python python/12_officials.py [--out DIR]
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livelib  # noqa: E402
import officiallib as ol  # noqa: E402

FIRST_SEASON = importlib.import_module("10_harvest_officials").FIRST_SEASON

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    raw = ROOT / "data" / "raw" / "officials"
    crews = ol.flatten_officials(raw)
    if crews.height == 0:
        print(f"FAILED: no harvested officials in {raw}; run python/10_harvest_officials.py")
        return 1
    crews.write_csv(ROOT / "data" / "game_officials.csv")
    live_dir = ROOT / "data" / "raw" / "live"
    live = livelib.officials(live_dir)
    if live.height == 0:
        print(f"FAILED: no liveData officials in {live_dir}; copy the cached boxes there (see DATA_SOURCES.md)")
        return 1
    live.write_csv(ROOT / "data" / "live_officials.csv")
    crews, resolved = ol.working_crews(crews, live)

    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    dev = pl.read_csv(ROOT / "output" / "profile_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})
    ids = ol.game_ids(tg)

    cov = ol.coverage(dev, ids, crews, FIRST_SEASON, resolved)
    games, link = ol.sample(dev, ids, crews)
    if games.height == 0:
        print("FAILED: no question 4 game lists three officials")
        return 1
    cv = ol.crew_values(games, link)
    wo = ol.within_official(link)
    h = ol.halves(link)

    cov.write_csv(args.out / "officials_coverage.csv")
    pl.concat([ol.game1_profile(games), ol.crew_profile(cv, dev)]).write_csv(args.out / "officials_profile.csv")
    ol.within_summary(wo).write_csv(args.out / "officials_within.csv")
    ol.reliability(h).write_csv(args.out / "officials_reliability.csv")
    cv.write_csv(args.out / "officials_crew_games.csv")
    wo.write_csv(args.out / "officials_people.csv")
    h.write_csv(args.out / "officials_halves.csv")
    missing = cov["GAMES"].sum() - cov["HARVESTED"].sum()
    print(f"officials: {games.height} games with a crew of three ({cov['RESOLVED'].sum()} with the alternate "
          f"identified by liveData), {missing} games not yet harvested, "
          f"{link['OFFICIAL_ID'].n_unique()} officials, {wo.height} with both Game 1s and later games, "
          f"{h.height} with both season halves")
    return 0


if __name__ == "__main__":
    sys.exit(main())
