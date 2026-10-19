"""Harvest player-mode playoff game logs for every NBA and WNBA postseason.

One LeagueGameLog call (player mode, Playoffs) per league-season, for the
roster experience measure of follow-up 9 in docs/design.md. Written as CSV
under data/raw/playerlogs/ (gitignored, resumable: files that already exist
are skipped). An empty season is written as a header-only file so a rerun
does not ask again. Like 10_harvest_officials.py, the harvest exits with
status 3 (STALLED) after FAIL_STREAK failed seasons in a row, so a fresh
process can pick up where it left off:

    until python python/13_harvest_players.py; [ $? -ne 3 ]; do :; done
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

import polars as pl
from nba_api.stats.library import http

# Same UA workaround as 01_harvest.py.
http.STATS_HEADERS["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

from nba_api.stats.endpoints import leaguegamelog  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
H = importlib.import_module("01_harvest")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "playerlogs"
DELAY = 1.5
FAIL_STREAK = 2
STALLED = 3


def save(league: str, end_year: int) -> bool | None:  # pragma: no cover - network
    """False when already on disk, True when saved, None when it failed."""
    dest = OUT / H.file_name(league, end_year, "po")
    if dest.exists():
        return False
    for attempt in range(3):
        try:
            frame = leaguegamelog.LeagueGameLog(
                league_id=league, season=H.season_str(league, end_year), season_type_all_star="Playoffs",
                player_or_team_abbreviation="P", timeout=90).get_data_frames()[0]
            break
        except Exception as e:  # network errors surface under several types
            print(f"ERR {dest.name} attempt {attempt + 1}: {type(e).__name__}", flush=True)
            time.sleep(15 * (attempt + 1))
    else:
        print(f"FAILED {dest.name}", flush=True)
        return None
    df = pl.from_pandas(frame)
    df.write_csv(dest)
    print(f"OK  {dest.name} rows={df.height}", flush=True)
    time.sleep(DELAY)
    return True


def main() -> int:  # pragma: no cover - network
    OUT.mkdir(parents=True, exist_ok=True)
    streak = 0
    for league, (first, last) in H.LEAGUES.items():
        for y in range(first, last + 1):
            result = save(league, y)
            streak = streak + 1 if result is None else 0
            if streak >= FAIL_STREAK:
                print(f"STALLED after {streak} failed seasons; restart for a fresh process", flush=True)
                return STALLED
    return 0


if __name__ == "__main__":
    sys.exit(main())
