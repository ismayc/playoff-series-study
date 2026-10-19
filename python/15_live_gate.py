"""Gate: team box scores in data/team_games.csv against the NBA liveData
box scores, for the games the October 19, 2026 audit cached (NBA 2019-20
on and WNBA 2022 on).

The reference is data/live_team_box.csv (one row per game and team), which
this script rebuilds from data/raw/live/ whenever those files are present
(livelib.team_box). Both stay local: they list box scores game by game,
which this public repo never commits (CLAUDE.md, DATA_SOURCES.md). The
committed outputs are summaries: output/live_gate.csv (per stat) and
output/live_gate_coverage.csv (per league-season).

Rules, each loud:

- Every team-game that differs on any stat is printed, inside or outside
  its tolerance.
- A stat fails if any team-game differs by more than TOL, or if more than
  MAX_DIFF_SHARE of the compared team-games differ at all (a shifted
  column or a wrong season would differ everywhere, one step at a time).
- A snapshot that is not Final (liveData gameStatus 3) is listed as STALE
  and not compared. The stale games and the games in the cached seasons
  with no box are pinned (KNOWN_STALE, KNOWN_NO_BOX); a new one, or a
  pinned one that changed, fails the gate, so nothing drops silently.
- The reference must agree with itself (PTS = 2 FGM + FG3M + FTM), and
  every team in a box must be in team_games and the other way round.

Tolerances come from the data (1,372 Final team-games, October 19, 2026):
PTS, FGM, FG3M, FTM, FTA, and AST never differ, so they must match
exactly. FGA, FG3A, OREB, DREB, STL, and PF differ by at most one (FG3A in
4 team-games, all -1). BLK and TOV differ by at most two (one team-game
each). These are scorer-credit counts that get corrected after a game, and
the two feeds need not carry the same correction. At most 11 team-games
differ on any one stat (TOV), 0.8%; MAX_DIFF_SHARE is 2%.

    python python/15_live_gate.py [--team-games CSV] [--live-dir DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livelib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOL = {"PTS": 0, "FGM": 0, "FG3M": 0, "FTM": 0, "FTA": 0, "AST": 0,
       "FGA": 1, "FG3A": 1, "OREB": 1, "DREB": 1, "STL": 1, "PF": 1, "BLK": 2, "TOV": 2}
MAX_DIFF_SHARE = 0.02
# Snapshots cached mid-game (2020 bubble), and 2019-20 games the audit did
# not cache. Pinned October 19, 2026.
KNOWN_STALE = {"0041900123", "0041900133", "0041900174", "0041900223"}
KNOWN_NO_BOX = {"0041900131", "0041900141", "0041900166", "0041900171", "0041900211"}


def reference(live_dir: Path, table: Path) -> tuple[pl.DataFrame, str]:
    if any(live_dir.glob("*.json")):
        ref = livelib.team_box(live_dir)
        return ref, f"rebuilt from {live_dir}"
    if table.exists():
        return pl.read_csv(table, schema_overrides={"GAME_ID": pl.Utf8}), f"read from {table} ({live_dir} is empty)"
    return pl.DataFrame(), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-games", type=Path, default=ROOT / "data" / "team_games.csv")
    ap.add_argument("--live-dir", type=Path, default=ROOT / "data" / "raw" / "live")
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    table = ROOT / "data" / "live_team_box.csv"

    ref, how = reference(args.live_dir, table)
    if ref.height == 0:
        print(f"FAILED: no liveData reference ({args.live_dir} is empty and {table} is missing)")
        return 1
    if args.live_dir == ROOT / "data" / "raw" / "live":
        ref.write_csv(table)
    print(f"reference: {ref['GAME_ID'].n_unique()} games, {how}")
    failures: list[str] = []

    bad_pts = ref.filter(pl.col("PTS") != 2 * pl.col("FGM") + pl.col("FG3M") + pl.col("FTM"))
    if bad_pts.height:
        failures.append(f"reference disagrees with itself (PTS != 2 FGM + FG3M + FTM) in {bad_pts.height} team-games")
        print(bad_pts.select("GAME_ID", "TEAM_ID", "PTS", "FGM", "FG3M", "FTM"))

    tg = pl.read_csv(args.team_games, infer_schema_length=None,
                     schema_overrides={"GAME_ID": pl.Utf8, "SERIES_KEY": pl.Utf8})
    tg = tg.select("GAME_ID", "TEAM_ID", "TEAM_ABBREVIATION", "LEAGUE", "SEASON",
                   *[pl.col(s).cast(pl.Int64, strict=True) for s in TOL])
    seasons = (tg.join(ref.select("GAME_ID").unique(), on="GAME_ID", how="semi")
                 .select("LEAGUE", "SEASON").unique())
    scope = tg.join(seasons, on=["LEAGUE", "SEASON"], how="semi")

    stale = ref.filter(pl.col("GAME_STATUS") != livelib.FINAL_STATUS)
    stale_ids = set(stale["GAME_ID"].to_list())
    no_box = set(scope["GAME_ID"].to_list()) - set(ref["GAME_ID"].to_list())
    print(f"\nSTALE (not Final, not compared): {len(stale_ids)} games")
    for gid, status in stale.select("GAME_ID", "GAME_STATUS_TEXT").unique().sort("GAME_ID").iter_rows():
        print(f"  {gid}  liveData status '{status}'")
    print(f"NO BOX (in a cached season, not compared): {len(no_box)} games: {', '.join(sorted(no_box))}")
    if stale_ids != KNOWN_STALE:
        failures.append(f"stale snapshots changed: new {sorted(stale_ids - KNOWN_STALE)}, "
                        f"no longer stale {sorted(KNOWN_STALE - stale_ids)} (update KNOWN_STALE once checked)")
    if no_box != KNOWN_NO_BOX:
        failures.append(f"games without a box changed: new {sorted(no_box - KNOWN_NO_BOX)}, "
                        f"now boxed {sorted(KNOWN_NO_BOX - no_box)} (update KNOWN_NO_BOX once checked)")

    final = ref.filter(pl.col("GAME_STATUS") == livelib.FINAL_STATUS)
    j = final.join(scope, on=["GAME_ID", "TEAM_ID"], how="full", suffix="_TG", coalesce=True)
    orphans = j.filter(pl.col("GAME_STATUS").is_null() & pl.col("GAME_ID").is_in(final["GAME_ID"].implode())
                       | pl.col("LEAGUE").is_null())
    if orphans.height:
        failures.append(f"{orphans.height} team-games in only one source")
        print(orphans.select("GAME_ID", "TEAM_ID", "GAME_STATUS", "LEAGUE"))
    j = j.filter(pl.col("GAME_STATUS").is_not_null() & pl.col("LEAGUE").is_not_null())
    n = j.height

    rows, diffs = [], []
    for stat, tol in TOL.items():
        d = j.select("GAME_ID", "TEAM_ABBREVIATION", "LEAGUE", "SEASON", pl.lit(stat).alias("STAT"),
                     pl.col(f"{stat}_TG").alias("TEAM_GAMES"), pl.col(stat).alias("LIVE"),
                     (pl.col(f"{stat}_TG") - pl.col(stat)).alias("D"))
        nulls = d.filter(pl.col("D").is_null()).height
        dd = d.filter(pl.col("D").is_null() | (pl.col("D") != 0))
        diffs.append(dd)
        max_abs = dd["D"].abs().max() if dd.height else 0
        cap = int(MAX_DIFF_SHARE * n)
        rows.append({"STAT": stat, "TOL": tol, "TEAM_GAMES": n, "N_DIFF": dd.height,
                     "MAX_ABS": max_abs or 0, "MAX_N_DIFF": cap})
        if nulls:
            failures.append(f"{stat}: {nulls} team-games with a missing value")
        if dd.filter(pl.col("D").abs() > tol).height:
            failures.append(f"{stat}: {dd.filter(pl.col('D').abs() > tol).height} team-games beyond tolerance {tol}")
        if dd.height > cap:
            failures.append(f"{stat}: {dd.height} team-games differ, more than {cap} ({MAX_DIFF_SHARE:.0%} of {n})")

    allD = pl.concat(diffs).with_columns(
        pl.when(pl.col("D").is_null() | (pl.col("D").abs() > pl.col("STAT").replace_strict(TOL)))
          .then(pl.lit("OUT OF TOLERANCE")).otherwise(pl.lit("within tolerance")).alias("VERDICT"))
    print(f"\nMISMATCHES: {allD.height} cells in {n} Final team-games ({n // 2} games)")
    for r in allD.sort("GAME_ID", "TEAM_ABBREVIATION", "STAT").iter_rows(named=True):
        print(f"  {r['GAME_ID']} {r['TEAM_ABBREVIATION']:>4} {r['STAT']:<5} team_games {r['TEAM_GAMES']} "
              f"liveData {r['LIVE']} ({r['D']:+d}) {r['VERDICT']}" if r["D"] is not None else
              f"  {r['GAME_ID']} {r['TEAM_ABBREVIATION']} {r['STAT']} missing  OUT OF TOLERANCE")

    summary = pl.DataFrame(rows)
    print("\n" + "\n".join(f"  {r['STAT']:<5} tol {r['TOL']}  {r['N_DIFF']:>3} of {r['TEAM_GAMES']} differ, "
                           f"max |d| {r['MAX_ABS']}" for r in summary.iter_rows(named=True)))
    cov = (scope.select("GAME_ID", "LEAGUE", "SEASON").unique()
                .join(ref.select("GAME_ID", "GAME_STATUS").unique(), on="GAME_ID", how="left")
                .group_by("LEAGUE", "SEASON")
                .agg(pl.len().alias("GAMES"), pl.col("GAME_STATUS").is_not_null().sum().alias("BOXES"),
                     (pl.col("GAME_STATUS") == livelib.FINAL_STATUS).sum().alias("FINAL"),
                     (pl.col("GAME_STATUS").is_not_null() & (pl.col("GAME_STATUS") != livelib.FINAL_STATUS))
                     .sum().alias("STALE"))
                .sort("LEAGUE", "SEASON"))
    if args.out == ROOT / "output":
        summary.write_csv(args.out / "live_gate.csv")
        cov.write_csv(args.out / "live_gate_coverage.csv")

    if failures:
        print("\nLIVE GATE FAILED:\n" + "\n".join(f"  {f}" for f in failures))
        return 1
    print(f"\nLIVE GATE PASSED: {n // 2} Final games compared on {len(TOL)} stats; "
          f"{len(stale_ids)} stale and {len(no_box)} unboxed games listed above, not compared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
