"""Write the generator-owned regions of README.md from the question 1 outputs.

Every number in those regions comes from output/game1_summary.csv or
output/game1_pooled.csv; prose outside the regions carries no numbers
(family rule). Regions are delimited by <!-- gen:NAME --> and
<!-- /gen:NAME -->.

    python python/05_findings.py           # rewrite the regions
    python python/05_findings.py --check   # fail if README is out of date
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LEAGUES = {0: "NBA", 10: "WNBA"}


def pp(x: float) -> str:
    """A proportion as signed percentage points, two decimals."""
    return f"{x * 100:+.2f}"


def cell(row: dict) -> str:
    return f"{pp(row['MEAN'])} ({pp(row['LO'])} to {pp(row['HI'])})"


def excludes_zero(row: dict) -> bool:
    return row["LO"] > 0 or row["HI"] < 0


def get(summary: pl.DataFrame, league: int, panel: str, metric: str) -> dict:
    r = summary.filter((pl.col("LEAGUE") == league) & (pl.col("PANEL") == panel) & (pl.col("METRIC") == metric))
    if r.height != 1:
        raise KeyError(f"expected one summary row for {league} {panel} {metric}, found {r.height}")
    return r.row(0, named=True)


def headline(summary: pl.DataFrame) -> str:
    lines = ["| League | Series | Game 1 minus Games 2+ | Game 1 minus Game 2 |", "|---|---|---|---|"]
    for lg, name in LEAGUES.items():
        d, d2 = get(summary, lg, "all", "D_PCT"), get(summary, lg, "all", "D2_PCT")
        lines.append(f"| {name} | {d['N']} | {cell(d)} | {cell(d2)} |")
    lines.append("")
    lines.append("Three-point percentage, both teams pooled within each series; mean "
                 "over series in percentage points with a 95% interval.")
    verdicts = []
    for lg, name in LEAGUES.items():
        d, d2 = get(summary, lg, "all", "D_PCT"), get(summary, lg, "all", "D2_PCT")
        if excludes_zero(d) and excludes_zero(d2) and (d["MEAN"] < 0) == (d2["MEAN"] < 0):
            verdicts.append(f"{name}: Game 1 differs ({'lower' if d['MEAN'] < 0 else 'higher'}).")
        else:
            verdicts.append(f"{name}: no Game 1 dip; both intervals include zero."
                            if not excludes_zero(d) and not excludes_zero(d2)
                            else f"{name}: not claimed (the two comparisons do not agree).")
    return "\n".join(lines + ["", "**Verdict.** " + " ".join(verdicts)])


def rate(summary: pl.DataFrame) -> str:
    lines = ["| League | Game 1 minus Games 2+ | Game 1 minus Game 2 |", "|---|---|---|"]
    for lg, name in LEAGUES.items():
        lines.append(f"| {name} | {cell(get(summary, lg, 'all', 'D_RATE'))} "
                     f"| {cell(get(summary, lg, 'all', 'D2_RATE'))} |")
    lines.append("")
    lines.append("Three-point attempt rate (3PA / FGA), percentage points of field-goal attempts.")
    verdicts = []
    for lg, name in LEAGUES.items():
        d, d2 = get(summary, lg, "all", "D_RATE"), get(summary, lg, "all", "D2_RATE")
        if excludes_zero(d) and excludes_zero(d2) and (d["MEAN"] < 0) == (d2["MEAN"] < 0):
            verdicts.append(f"{name}: a {'smaller' if d['MEAN'] < 0 else 'larger'} share of shots "
                            "from three in Game 1, on both comparisons.")
        else:
            verdicts.append(f"{name}: no Game 1 difference in volume that holds on both comparisons.")
    lines += ["", "**Reading.** " + " ".join(verdicts)]
    decades = sorted({p for p in summary.filter(pl.col("LEAGUE") == 0)["PANEL"].to_list() if p.endswith("0s")})
    lines += ["", "NBA by decade, Game 1 minus Games 2+:", "",
              "| Decade | Series | Attempt rate | Accuracy |", "|---|---|---|---|"]
    for p in decades:
        r, a = get(summary, 0, p, "D_RATE"), get(summary, 0, p, "D_PCT")
        lines.append(f"| {p} | {r['N']} | {cell(r)} | {cell(a)} |")
    return "\n".join(lines)


def baseline(summary: pl.DataFrame) -> str:
    lines = ["| League | Game 1 minus expected | Games 2+ minus expected | Series with a baseline |",
             "|---|---|---|---|"]
    for lg, name in LEAGUES.items():
        g, r = get(summary, lg, "all", "RESID_G1"), get(summary, lg, "all", "RESID_REST")
        lines.append(f"| {name} | {cell(g)} | {cell(r)} | {g['N']} of {g['N'] + g['N_DROPPED']} |")
    lines += ["", "Expected 3P% is the team's regular-season 3P% plus its opponent's 3P% "
              "allowed minus the league's."]
    lines += ["", "| League | Game 1 at | Team-series | Own Game 1 minus own Games 2+ | Game 1 minus expected |",
              "|---|---|---|---|---|"]
    for lg, name in LEAGUES.items():
        for side in ("home", "road"):
            d, g = get(summary, lg, side, "TEAM_D_PCT"), get(summary, lg, side, "TEAM_RESID_G1")
            lines.append(f"| {name} | {side} | {d['N']} | {cell(d)} | {cell(g)} |")
    return "\n".join(lines)


def pooled_region(pooled: pl.DataFrame) -> str:
    lines = ["| League | Game 1 3P% | Games 2+ 3P% | Difference |", "|---|---|---|---|"]
    for r in pooled.sort("LEAGUE").iter_rows(named=True):
        lines.append(f"| {LEAGUES[r['LEAGUE']]} | {r['G1_PCT'] * 100:.2f} | {r['REST_PCT'] * 100:.2f} "
                     f"| {pp(r['D_PCT'])} |")
    lines += ["", "Every three-pointer in every Game 1 against every one after it, no intervals."]
    return "\n".join(lines)


def regions() -> dict[str, str]:
    summary = pl.read_csv(ROOT / "output" / "game1_summary.csv")
    pooled = pl.read_csv(ROOT / "output" / "game1_pooled.csv")
    return {"headline": headline(summary), "rate": rate(summary),
            "baseline": baseline(summary), "pooled": pooled_region(pooled)}


def render(text: str, new: dict[str, str]) -> str:
    for name, body in new.items():
        pat = re.compile(rf"(<!-- gen:{name} -->\n)(.*?)(<!-- /gen:{name} -->)", re.S)
        if not pat.search(text):
            raise KeyError(f"README has no gen:{name} region")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text)
    return text


def main() -> int:
    text = README.read_text()
    out = render(text, regions())
    if "--check" in sys.argv:
        if out != text:
            print("findings: FAILED (README regions differ from outputs; run python/05_findings.py)")
            return 1
        print(f"findings: PASSED ({len(regions())} regions match the outputs)")
        return 0
    README.write_text(out)
    print("findings: README regions rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
