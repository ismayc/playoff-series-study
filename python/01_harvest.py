"""Harvest team-game box scores for every NBA and WNBA season.

One LeagueGameLog call (team mode) per league, season, and season type:

- Playoffs: the games the study is about.
- Regular Season: each team's baseline rates, and the date of its last
  game, which sets first-round rest.
- PlayIn (NBA, 2019-20 onward): a play-in team's last game before the
  first round is its play-in game, so first-round rest is wrong without it.

nba_api returns pandas; frames are converted to polars at the boundary and
written as CSV under data/raw/gamelogs/ (gitignored, resumable: files that
already exist are skipped). An empty season type is written as a header-only
file so a rerun does not ask again.

    python python/01_harvest.py [--league 00|10] [--first YEAR] [--last YEAR]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import polars as pl
from nba_api.stats.library import http

# nba_api's shipped browser UA gets hung by Akamai; a generic UA does not
# (family note, lineup-valuation-study/python/05_build_stints.py).
http.STATS_HEADERS["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

from nba_api.stats.endpoints import leaguegamelog  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "gamelogs"
DELAY = 1.0

# First and last season per league, by the calendar year the season ends.
LEAGUES = {"00": (1947, 2026), "10": (1997, 2026)}
TYPES = {"Regular Season": "rs", "Playoffs": "po", "PlayIn": "pi"}


def season_str(league: str, end_year: int) -> str:
    """NBA seasons are '2024-25'; WNBA seasons are a single year."""
    if league == "10":
        return str(end_year)
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def file_name(league: str, end_year: int, type_key: str) -> str:
    return f"{'nba' if league == '00' else 'wnba'}_{end_year}_{type_key}.csv"


def wanted(league: str, end_year: int, season_type: str) -> bool:
    return season_type != "PlayIn" or (league == "00" and end_year >= 2020)


def fetch(league: str, season: str, season_type: str) -> pl.DataFrame:  # pragma: no cover - network
    frame = leaguegamelog.LeagueGameLog(
        league_id=league, season=season, season_type_all_star=season_type,
        player_or_team_abbreviation="T", timeout=90,
    ).get_data_frames()[0]
    return pl.from_pandas(frame)


def save(league: str, end_year: int, season_type: str) -> None:  # pragma: no cover - network
    dest = OUT / file_name(league, end_year, TYPES[season_type])
    if dest.exists():
        return
    season = season_str(league, end_year)
    for attempt in range(4):
        try:
            df = fetch(league, season, season_type)
            break
        except Exception as e:  # network errors surface under several types
            print(f"ERR {dest.name} attempt {attempt + 1}: {type(e).__name__}", flush=True)
            time.sleep(20 * (attempt + 1))
    else:
        print(f"FAILED {dest.name}", flush=True)
        return
    df.write_csv(dest)
    print(f"OK  {dest.name} rows={df.height}", flush=True)
    time.sleep(DELAY)


def main() -> None:  # pragma: no cover - network
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", choices=sorted(LEAGUES))
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for league, (first, last) in LEAGUES.items():
        if args.league and league != args.league:
            continue
        for y in range(max(first, args.first or first), min(last, args.last or last) + 1):
            for season_type in TYPES:
                if wanted(league, y, season_type):
                    save(league, y, season_type)


if __name__ == "__main__":
    main()
