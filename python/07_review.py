"""Build the series and team review page (question 2).

Writes docs/review/data.json (gitignored: it lists NBA.com box scores game by
game) and docs/review/index.html, which is review/template.html with the
family display face inlined. Descriptive only: the page shows each series'
games and each team's Game 1 against the rest of its series. Estimates come
from 03 and 06 outputs; nothing here is a new analysis.

    python python/07_review.py
    cd docs/review && python3 -m http.server 8766   # view at http://localhost:8766/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT.parent / "basketball-analysis-tools"
sys.path.insert(0, str(FAMILY))
from family_fonts import FONT_FACE_CSS  # noqa: E402

OUT = ROOT / "docs" / "review"
REGULATION = {0: 48.0, 10: 40.0}
GAME_COLS = ["PTS", "FG3M", "FG3A", "FGA", "PF", "FTA", "TOV"]


def season_label(league: int, season: int) -> str:
    return str(season) if league == 10 else f"{season - 1}-{str(season)[-2:]}"


def num(x):
    """JSON-friendly number: ints stay ints, NaN and None become None."""
    if x is None or (isinstance(x, float) and x != x):
        return None
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return round(x, 5) if isinstance(x, float) else x


def build() -> dict:
    tg = pl.read_csv(ROOT / "data" / "team_games.csv", infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    # Single-game rounds have no "rest of series".
    tg = tg.filter(pl.col("N_GAMES") >= 2)
    gs = pl.read_csv(ROOT / "output" / "game1_series.csv", infer_schema_length=None,
                     schema_overrides={"SERIES_KEY": pl.Utf8}).select("LEAGUE", "SEASON", "SERIES_KEY", "D_PCT")
    prof = pl.read_csv(ROOT / "output" / "profile_summary.csv")

    # Side A is the Game 1 home team (the higher seed), B its opponent.
    g1 = tg.filter(pl.col("GAME_NO") == 1)
    side = (g1.filter(pl.col("HOME")).select("LEAGUE", "SEASON", "SERIES_KEY", pl.col("TEAM_ID").alias("A_ID"),
                                             pl.col("OPP_ID").alias("B_ID")))
    # Neutral-site rows still flag one team as home; a Game 1 with no home flag would drop here.
    if side.height != g1.height // 2:
        raise ValueError(f"{g1.height // 2 - side.height} Game 1s without a home team")

    teams = {}
    for r in (tg.sort("SEASON").group_by("TEAM_ID", maintain_order=True)
                .agg(pl.col("LEAGUE").last(), pl.col("TEAM_NAME").last(), pl.col("TEAM_ABBREVIATION").last())
                .iter_rows(named=True)):
        teams[str(r["TEAM_ID"])] = {"lg": r["LEAGUE"], "name": r["TEAM_NAME"], "abbr": r["TEAM_ABBREVIATION"]}

    t = tg.join(side, on=["LEAGUE", "SEASON", "SERIES_KEY"])
    poss = (pl.col("FGA") + 0.44 * pl.col("FTA") - pl.col("OREB") + pl.col("TOV")
            + pl.col("OPP_FGA") + 0.44 * pl.col("OPP_FTA") - pl.col("OPP_OREB") + pl.col("OPP_TOV")) / 2
    reg = pl.col("LEAGUE").replace_strict(REGULATION, return_dtype=pl.Float64)
    t = t.with_columns((poss * reg / (pl.col("MIN") / 5)).alias("PACE"))
    a_rows = t.filter(pl.col("TEAM_ID") == pl.col("A_ID"))
    b_rows = t.filter(pl.col("TEAM_ID") == pl.col("B_ID")).select(
        "GAME_ID", "TEAM_ABBREVIATION", *[pl.col(c).alias(f"B_{c}") for c in GAME_COLS])

    games = (a_rows.join(b_rows.rename({"TEAM_ABBREVIATION": "B_ABBR"}), on="GAME_ID")
                   .sort("LEAGUE", "SEASON", "SERIES_KEY", "GAME_NO"))
    series = []
    gap = {(r[0], r[1], r[2]): r[3] for r in gs.iter_rows()}
    for (lg, season, key), g in games.group_by(["LEAGUE", "SEASON", "SERIES_KEY"], maintain_order=True):
        first = g.row(0, named=True)
        a, b = first["A_ID"], first["B_ID"]
        wa = int((g["WL"] == "W").sum())
        rows = []
        for r in g.iter_rows(named=True):
            rows.append([r["GAME_NO"], r["GAME_DATE"], 1 if r["HOME"] else 0,
                         *[num(r[c]) for c in GAME_COLS], *[num(r[f"B_{c}"]) for c in GAME_COLS],
                         num(r["PACE"])])
        series.append({
            "lg": lg, "s": season, "label": season_label(lg, season), "k": key,
            "round": num(first["ROUND"]), "finals": bool(first["FINALS"]),
            "start": first["GAME_DATE"], "a": str(a), "b": str(b),
            "aAbbr": first["TEAM_ABBREVIATION"], "bAbbr": first["B_ABBR"],
            "wa": wa, "wb": len(rows) - wa, "need": first["WINS_NEEDED"],
            "winner": "a" if first["WINNER_ID"] == a else "b",
            # Every game records 3PA for both teams (partial early-1980s rows would mislead).
            "has3": bool(g["FG3A"].null_count() == 0 and g["B_FG3A"].null_count() == 0),
            "gap": num(gap.get((lg, season, key))), "games": rows})

    profiles = [{"lg": r["LEAGUE"], "panel": r["PANEL"], "g": r["GAME_NO"], "m": r["METRIC"],
                 "mean": num(r["MEAN"]), "lo": num(r["LO"]), "hi": num(r["HI"]), "n": r["N"]}
                for r in prof.iter_rows(named=True)]
    return {"gameCols": ["no", "date", "aHome", *[f"a{c}" for c in GAME_COLS], *[f"b{c}" for c in GAME_COLS], "pace"],
            "teams": teams, "series": series, "profiles": profiles}


def main() -> int:
    data = build()
    if not data["series"] or not data["profiles"]:
        print("FAILED: empty review data")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    html = (ROOT / "review" / "template.html").read_text()
    if "/*FONT_FACE_CSS*/" not in html:
        print("FAILED: template has no /*FONT_FACE_CSS*/ marker")
        return 1
    (OUT / "index.html").write_text(html.replace("/*FONT_FACE_CSS*/", FONT_FACE_CSS))
    size = (OUT / "data.json").stat().st_size / 1e6
    print(f"review: {len(data['series'])} series, {len(data['teams'])} teams, "
          f"{len(data['profiles'])} profile rows, data.json {size:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
