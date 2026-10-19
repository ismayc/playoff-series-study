"""The NBA liveData box scores cached in data/raw/live/ (one
<GAME_ID>.json per game, exactly as downloaded), flattened into the two
compact tables the study reads:

- live_officials: GAME_ID, OFFICIAL_ID, ASSIGNMENT (OFFICIAL1, OFFICIAL2,
  OFFICIAL3, or ALTERNATE), read by follow-up 8 to tell the three working
  officials from the alternate (officiallib.working_crews).
- live_team_box: one row per game and team with the snapshot's status and
  the team box-score counts, read by the box-score gate (15_live_gate.py).

The boxes were fetched by an audit on October 19, 2026 from the NBA's
liveData feed and cannot be re-fetched from this machine (403), so the raw
files are the only copy; both tables are rebuilt from them, never edited.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

# team_games.csv column -> liveData team statistics key.
STATS = {"PTS": "points", "FGM": "fieldGoalsMade", "FGA": "fieldGoalsAttempted",
         "FG3M": "threePointersMade", "FG3A": "threePointersAttempted",
         "FTM": "freeThrowsMade", "FTA": "freeThrowsAttempted",
         "OREB": "reboundsOffensive", "DREB": "reboundsDefensive", "AST": "assists",
         "STL": "steals", "BLK": "blocks", "TOV": "turnoversTotal", "PF": "foulsPersonal"}
FINAL_STATUS = 3  # liveData gameStatus: 1 scheduled, 2 in progress, 3 final


def _boxes(raw_dir: Path):
    for f in sorted(raw_dir.glob("*.json")):
        game = json.loads(f.read_text())["game"]
        if game["gameId"] != f.stem:
            raise ValueError(f"{f.name} holds game {game['gameId']}")
        yield f.stem, game


def officials(raw_dir: Path) -> pl.DataFrame:
    rows = [{"GAME_ID": gid, "OFFICIAL_ID": int(o["personId"]), "ASSIGNMENT": o["assignment"]}
            for gid, g in _boxes(raw_dir) for o in g.get("officials", [])]
    return pl.DataFrame(rows, schema={"GAME_ID": pl.Utf8, "OFFICIAL_ID": pl.Int64, "ASSIGNMENT": pl.Utf8})


def team_box(raw_dir: Path) -> pl.DataFrame:
    rows = []
    for gid, g in _boxes(raw_dir):
        for side in ("homeTeam", "awayTeam"):
            t = g[side]
            rows.append({"GAME_ID": gid, "TEAM_ID": int(t["teamId"]), "GAME_STATUS": int(g["gameStatus"]),
                         "GAME_STATUS_TEXT": g["gameStatusText"].strip(),
                         **{k: int(t["statistics"][v]) for k, v in STATS.items()}})
    return pl.DataFrame(rows, schema={"GAME_ID": pl.Utf8, "TEAM_ID": pl.Int64, "GAME_STATUS": pl.Int64,
                                      "GAME_STATUS_TEXT": pl.Utf8, **{k: pl.Int64 for k in STATS}})
