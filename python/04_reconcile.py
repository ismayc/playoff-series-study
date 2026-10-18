"""Gate: the R and Python implementations of questions 1, 3, and 4 must agree.

Compares output/<table>.csv (Python) with output/r/<table>.csv (R) for every
table 03, 06, and 08 write. In each table the key rows must match exactly, every
shared column must exist on both sides, numbers must agree within TOL
(blank on one side means blank on the other), and text and flags must be
equal. An empty table or a missing file fails; nothing is skipped quietly.

    python python/03_game1.py && Rscript R/03_game1.R
    python python/06_profiles.py && Rscript R/06_profiles.R
    python python/08_stakes_rest.py && Rscript R/08_stakes_rest.R
    python python/04_reconcile.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
TOL = 1e-9

TABLES = {
    "game1_series.csv": ["LEAGUE", "SEASON", "SERIES_KEY"],
    "game1_team.csv": ["LEAGUE", "SEASON", "SERIES_KEY", "TEAM_ID"],
    "game1_summary.csv": ["LEAGUE", "PANEL", "METRIC"],
    "game1_pooled.csv": ["LEAGUE"],
    "game1_season.csv": ["LEAGUE", "SEASON"],
    "profile_games.csv": ["LEAGUE", "SEASON", "SERIES_KEY", "GAME_NO"],
    "profile_summary.csv": ["LEAGUE", "PANEL", "GAME_NO", "METRIC"],
    "profile_state.csv": ["LEAGUE"],
    "series_stage.csv": ["LEAGUE", "SEASON", "SERIES_KEY"],
    "stakes_summary.csv": ["LEAGUE", "STAGE", "METRIC"],
    "rest_series.csv": ["LEAGUE", "SEASON", "SERIES_KEY"],
    "rest_summary.csv": ["LEAGUE", "BIN", "METRIC"],
}


def read(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, schema_overrides={"SERIES_KEY": pl.Utf8, "PANEL": pl.Utf8, "BIN": pl.Utf8},
                       infer_schema_length=None)


def compare(name: str, keys: list[str], py: pl.DataFrame, r: pl.DataFrame) -> list[str]:
    errs = []
    if py.height == 0 or r.height == 0:
        return [f"{name}: empty (python {py.height} rows, R {r.height})"]
    only_py, only_r = set(py.columns) - set(r.columns), set(r.columns) - set(py.columns)
    if only_py or only_r:
        errs.append(f"{name}: columns only in python {sorted(only_py)}, only in R {sorted(only_r)}")
    if py.height != r.height:
        errs.append(f"{name}: {py.height} python rows vs {r.height} R rows")
    py_only = py.join(r, on=keys, how="anti").height
    r_only = r.join(py, on=keys, how="anti").height
    if py_only or r_only:
        errs.append(f"{name}: {py_only} key rows only in python, {r_only} only in R")
    if py.select(keys).is_duplicated().any() or r.select(keys).is_duplicated().any():
        errs.append(f"{name}: duplicate keys")
    j = py.join(r, on=keys, how="inner", suffix="_R")
    checked = 0
    for c in sorted(set(py.columns) & set(r.columns) - set(keys)):
        a, b = j[c], j[f"{c}_R"]
        if a.dtype.is_numeric() and b.dtype.is_numeric():
            a, b = a.cast(pl.Float64), b.cast(pl.Float64)
            null_mismatch = (a.is_null() != b.is_null()).sum()
            diff = (a - b).abs().max()
            if null_mismatch:
                errs.append(f"{name}.{c}: {null_mismatch} rows blank on one side only")
            if diff is not None and diff > TOL:
                errs.append(f"{name}.{c}: max |python - R| = {diff:.3g}")
        else:
            bad = (a.cast(pl.Utf8).str.to_lowercase().fill_null("") != b.cast(pl.Utf8).str.to_lowercase().fill_null("")).sum()
            if bad:
                errs.append(f"{name}.{c}: {bad} rows differ")
        checked += 1
    if checked == 0:
        errs.append(f"{name}: no columns compared")
    print(f"  {name}: {j.height} rows matched, {checked} columns compared")
    return errs


def main() -> int:
    failures = []
    for name, keys in TABLES.items():
        p, q = OUT / name, OUT / "r" / name
        if not p.exists() or not q.exists():
            failures.append(f"{name}: missing ({p.exists()=}, {q.exists()=})")
            continue
        failures += compare(name, keys, read(p), read(q))
    if failures:
        print("reconcile: FAILED")
        for f in failures:
            print("  " + f)
        return 1
    print("reconcile: PASSED (python and R agree on every cell)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
