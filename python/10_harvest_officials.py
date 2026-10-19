"""Harvest the officials for every playoff game in data/team_games.csv.

One BoxScoreSummaryV3 call per game (V2 returns nothing for 2024-25 on).
The stats API lists officials from about the 2001-02 NBA season and the
2004 WNBA season (probed October 19, 2026); earlier games come back with
an empty list, so only games from FIRST_SEASON on are requested.

Each game is written as data/raw/officials/<GAME_ID>.json holding the
API's officials list exactly as returned (gitignored, resumable: files
that already exist are skipped). A game whose call fails four times is
logged as FAILED and left for the next run.

    python python/10_harvest_officials.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import polars as pl
from nba_api.stats.library import http

# Same UA workaround as 01_harvest.py.
http.STATS_HEADERS["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

from nba_api.stats.endpoints import boxscoresummaryv3  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "officials"
DELAY = 0.8
# Season (year it ends) of the first probed game with officials listed.
FIRST_SEASON = {0: 2001, 10: 2003}


def wanted_games(games: pl.DataFrame) -> list[str]:
    """Distinct game ids from each league's first officials season on."""
    keep = pl.lit(False)
    for league, first in FIRST_SEASON.items():
        keep = keep | ((pl.col("LEAGUE") == league) & (pl.col("SEASON") >= first))
    return sorted(games.filter(keep)["GAME_ID"].unique().to_list())


def fetch(game_id: str) -> list[dict]:  # pragma: no cover - network
    d = boxscoresummaryv3.BoxScoreSummaryV3(game_id=game_id, timeout=60).get_dict()
    return d["boxScoreSummary"].get("officials", [])


def save(game_id: str) -> bool:  # pragma: no cover - network
    dest = OUT / f"{game_id}.json"
    if dest.exists():
        return False
    for attempt in range(4):
        try:
            officials = fetch(game_id)
            break
        except Exception as e:  # network errors surface under several types
            print(f"ERR {game_id} attempt {attempt + 1}: {type(e).__name__}", flush=True)
            time.sleep(15 * (attempt + 1))
    else:
        print(f"FAILED {game_id}", flush=True)
        return True
    dest.write_text(json.dumps(officials))
    print(f"OK  {game_id} officials={len(officials)}", flush=True)
    time.sleep(DELAY)
    return True


def main() -> None:  # pragma: no cover - network
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    games = pl.read_csv(ROOT / "data" / "team_games.csv",
                        schema_overrides={"GAME_ID": pl.Utf8})
    ids = wanted_games(games)
    print(f"{len(ids)} games wanted", flush=True)
    asked = 0
    for gid in ids:
        if args.limit and asked >= args.limit:
            break
        asked += save(gid)


if __name__ == "__main__":
    main()
