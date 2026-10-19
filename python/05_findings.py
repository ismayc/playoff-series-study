"""Write the generator-owned regions of README.md from the committed outputs.

Every number in those regions comes from a committed summary table under
output/ (questions 1 to 4 and follow-ups 5 to 8); prose outside the regions carries no numbers
(family rule). Regions are delimited by <!-- gen:NAME --> and
<!-- /gen:NAME -->.

    python python/05_findings.py           # rewrite the regions
    python python/05_findings.py --check   # fail if README is out of date

Run glossary.py --sync (basketball-analysis-tools) after a rewrite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
# glossary.py --sync wraps terms in hover tags after this runs; strip them
# before rendering and comparing, as the other studies' generators do.
ABBR = re.compile(r'<abbr title="[^"]*">([^<]*)</abbr>')
LEAGUES = {0: "NBA", 10: "WNBA"}
# Below this many series a reading names the count instead of a direction.
FEW = 10


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


PROFILE_LABELS = {
    "PF100": ("Fouls per 100 possessions", 1), "FTR": ("Free-throw rate (FTA / FGA, x100)", 100),
    "TOV100": ("Turnovers per 100 possessions", 1), "PACE": ("Pace (possessions per regulation game)", 1),
    "ORTG": ("Points per 100 possessions", 1), "OREB_PCT": ("Offensive rebound % (x100)", 100),
    "AST_RATE": ("Assists per made field goal (x100)", 100),
    "FG3A_RATE": ("Three-point attempt rate (x100)", 100), "FG3_PCT": ("Three-point % (x100)", 100),
}


def profile_table(prof: pl.DataFrame, league: int, panel: str) -> list[str]:
    sub = prof.filter((pl.col("LEAGUE") == league) & (pl.col("PANEL") == panel))
    games = sorted(sub["GAME_NO"].unique().to_list())
    n = {g: sub.filter((pl.col("GAME_NO") == g) & (pl.col("METRIC") == "PF100"))["N"].item() for g in games}
    lines = ["| Rate, deviation from the series mean | " + " | ".join(f"G{g}" for g in games) + " |",
             "|---|" + "---|" * len(games),
             "| Games | " + " | ".join(str(n[g]) for g in games) + " |"]
    for m, (label, k) in PROFILE_LABELS.items():
        cells = []
        for g in games:
            r = get_profile(sub, g, m)
            text = f"{r['MEAN'] * k:+.2f}"
            cells.append(f"**{text}**" if r["LO"] is not None and excludes_zero(r) else text)
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def get_profile(sub: pl.DataFrame, game: int, metric: str) -> dict:
    r = sub.filter((pl.col("GAME_NO") == game) & (pl.col("METRIC") == metric))
    if r.height != 1:
        raise KeyError(f"expected one profile row for game {game} {metric}, found {r.height}")
    return r.row(0, named=True)


def profiles_region(prof: pl.DataFrame) -> str:
    out = []
    for lg, name in LEAGUES.items():
        out += [f"**{name}, every series.**", ""] + profile_table(prof, lg, "all") + [""]
        out += [f"**{name}, full-length series only** (same series in every column).", ""]
        out += profile_table(prof, lg, "full_length") + [""]
    out.append("Bold: the 95% interval excludes zero. Each cell is the mean over games of the "
               "two teams' deviations from their own series means.")
    return "\n".join(out)


def state_region(state: pl.DataFrame) -> str:
    lines = ["| League | Games with a series leader | Trailing minus leading team | Tied games left out |",
             "|---|---|---|---|"]
    for r in state.sort("LEAGUE").iter_rows(named=True):
        lines.append(f"| {LEAGUES[r['LEAGUE']]} | {r['N']} | {cell(r)} | {r['TIED_GAMES']} |")
    lines += ["", "Three-point attempt rate, each team relative to its own series mean, percentage points."]
    verdicts = []
    for r in state.sort("LEAGUE").iter_rows(named=True):
        name = LEAGUES[r["LEAGUE"]]
        if excludes_zero(r):
            verdicts.append(f"{name}: the team behind in the series takes relatively "
                            f"{'fewer' if r['MEAN'] < 0 else 'more'} threes than the leader.")
        else:
            verdicts.append(f"{name}: no difference between trailing and leading teams.")
    return "\n".join(lines + ["", "**Reading.** " + " ".join(verdicts)])


def stage_label(stage: int) -> str:
    return "Finals" if stage == 0 else f"{stage} round{'s' if stage > 1 else ''} before the Finals"


def stakes_region(st: pl.DataFrame) -> str:
    lines = ["| League | Stage | Series | 3P%: Game 1 minus Games 2+ | 3P%: Game 1 minus Game 2 "
             "| Attempt rate: Game 1 minus Games 2+ |", "|---|---|---|---|---|---|"]
    both, rate_hits = [], []
    for lg, name in LEAGUES.items():
        for stage in sorted(st.filter(pl.col("LEAGUE") == lg)["STAGE"].unique().to_list()):
            rows = {m: st.filter((pl.col("LEAGUE") == lg) & (pl.col("STAGE") == stage) & (pl.col("METRIC") == m)).row(0, named=True)
                    for m in ("D_PCT", "D2_PCT", "D_RATE")}
            d, d2, r = rows["D_PCT"], rows["D2_PCT"], rows["D_RATE"]
            lines.append(f"| {name} | {stage_label(stage)} | {d['N']} | {cell(d)} | {cell(d2)} | {cell(r)} |")
            if excludes_zero(d) and excludes_zero(d2) and (d["MEAN"] < 0) == (d2["MEAN"] < 0):
                both.append(f"{name} {stage_label(stage)}")
            if excludes_zero(r):
                rate_hits.append((name, stage))
    reading = ("No stage in either league shows a Game 1 accuracy gap that holds on both comparisons."
               if not both else "Accuracy gaps holding on both comparisons: " + ", ".join(both) + ".")
    for lg, name in LEAGUES.items():
        n_stages = st.filter(pl.col("LEAGUE") == lg)["STAGE"].n_unique()
        hits = [s for n, s in rate_hits if n == name]
        reading += (f" {name}: the attempt-rate gap excludes zero at {len(hits)} of {n_stages} stages"
                    + (f" ({', '.join(stage_label(s) for s in hits)})." if hits else "."))
    return "\n".join(lines + ["", "**Reading.** " + reading])


def rest_region(rs: pl.DataFrame) -> str:
    lines = ["| League | Rest gap | Series | 3P% contrast | Attempt-rate contrast |", "|---|---|---|---|---|"]
    readings = []
    for lg, name in LEAGUES.items():
        sub = rs.filter(pl.col("LEAGUE") == lg)
        for b in ("1-2", "3-5", "6+", "any"):
            p = sub.filter((pl.col("BIN") == b) & (pl.col("METRIC") == "CONTRAST_PCT")).row(0, named=True)
            r = sub.filter((pl.col("BIN") == b) & (pl.col("METRIC") == "CONTRAST_RATE")).row(0, named=True)
            label = "any gap" if b == "any" else f"{b} days"
            lines.append(f"| {name} | {label} | {p['N']} | {cell(p)} | {cell(r)} |")
        p = sub.filter((pl.col("BIN") == "any") & (pl.col("METRIC") == "CONTRAST_PCT")).row(0, named=True)
        zero = p["ZERO_GAP_SERIES"]
        bins_excl = [b for b in ("1-2", "3-5", "6+")
                     if excludes_zero(sub.filter((pl.col("BIN") == b) & (pl.col("METRIC") == "CONTRAST_PCT")).row(0, named=True))]
        if excludes_zero(p):
            readings.append(f"{name}: across every nonzero gap the more-rested team's Game 1 three-point shooting "
                            f"is relatively {'worse' if p['MEAN'] < 0 else 'better'}, but "
                            + ("no single gap bin excludes zero" if not bins_excl else f"only the {', '.join(bins_excl)} bin excludes zero")
                            + f", so it is a hint, not a finding ({zero} series with no gap left out).")
        else:
            readings.append(f"{name}: no rest-gap difference in Game 1 three-point shooting ({zero} series with no gap left out).")
    lines += ["", "Each contrast is the more-rested team's own Game 1 minus own Games 2+, minus the same for "
              "the less-rested team, in percentage points."]
    return "\n".join(lines + ["", "**Reading.** " + " ".join(readings)])


def lower_run(rows: pl.DataFrame) -> tuple[int, int] | None:
    """First and last season of the longest unbroken run of seasons whose
    Game 1 attempt rate is below Games 2+, or None if there is no such season."""
    best, start, prev = None, None, None
    for season, d in rows.sort("SEASON").select("SEASON", "D_RATE").iter_rows():
        if d is not None and d < 0:
            start = season if start is None or prev != season - 1 else start
            if best is None or season - start > best[1] - best[0]:
                best = (start, season)
        else:
            start = None
        prev = season
    return best


def eras_region(summary: pl.DataFrame, season: pl.DataFrame) -> str:
    lines = ["| League | Decade | Series | Accuracy | Attempt rate |", "|---|---|---|---|---|"]
    for lg, name in LEAGUES.items():
        decades = sorted({p for p in summary.filter(pl.col("LEAGUE") == lg)["PANEL"].to_list()
                          if re.fullmatch(r"\d{4}s", p)})
        for p in decades:
            a, r = get(summary, lg, p, "D_PCT"), get(summary, lg, p, "D_RATE")
            lines.append(f"| {name} | {p} | {a['N']} | {cell(a)} | {cell(r)} |")
    lines += ["", "Game 1 minus Games 2+, mean over series in percentage points with a 95% interval."]
    lines += ["", "| League | Decade | Seasons | Game 1 3P% | Games 2+ 3P% | Game 1 3PA rate "
              "| Games 2+ 3PA rate | Seasons with a lower Game 1 rate |", "|---|---|---|---|---|---|---|---|"]
    runs = []
    for lg, name in LEAGUES.items():
        rows = season.filter(pl.col("LEAGUE") == lg).with_columns(((pl.col("SEASON") // 10) * 10).alias("DECADE"))
        if rows.height == 0:
            raise KeyError(f"no season rows for {name}")
        dec = (rows.group_by("DECADE")
                   .agg(pl.len().alias("SEASONS"), (pl.col("D_RATE") < 0).sum().alias("LOWER"),
                        *[pl.col(c).sum() for s in ("G1", "REST") for c in (f"{s}_M", f"{s}_A", f"{s}_FGA")])
                   .sort("DECADE"))
        for d in dec.iter_rows(named=True):
            lines.append(f"| {name} | {d['DECADE']}s | {d['SEASONS']} "
                         f"| {d['G1_M'] / d['G1_A'] * 100:.1f} | {d['REST_M'] / d['REST_A'] * 100:.1f} "
                         f"| {d['G1_A'] / d['G1_FGA'] * 100:.1f} | {d['REST_A'] / d['REST_FGA'] * 100:.1f} "
                         f"| {d['LOWER']} of {d['SEASONS']} |")
        run = lower_run(rows)
        if run:
            runs.append(f"{name}: the longest unbroken run of seasons with a lower Game 1 attempt rate "
                        f"is {run[0]} to {run[1]}.")
    lines += ["", "Every three in the decade's series pooled, so a season with more threes counts for more."]
    return "\n".join(lines + ["", "**Reading.** " + " ".join(runs)])


def share(row: dict) -> str:
    """A proportion as a percentage with its interval, one decimal."""
    return f"{row['P'] * 100:.1f}% ({row['LO'] * 100:.1f} to {row['HI'] * 100:.1f})"


def outshoot_region(os_: pl.DataFrame) -> str:
    lines = ["| League | Series | Better Game 1 three-point shooter wins the series "
             "| Game 1 winner wins the series: it also outshot | it was outshot | Difference |",
             "|---|---|---|---|---|---|"]
    readings = []
    for lg, name in LEAGUES.items():
        r = {e: os_.filter((pl.col("LEAGUE") == lg) & (pl.col("ESTIMATE") == e)).row(0, named=True)
             for e in ("shooter_wins_series", "g1_winner_outshot", "g1_winner_not_outshot", "difference")}
        d = r["difference"]
        diff = f"{d['P'] * 100:+.1f} ({d['LO'] * 100:+.1f} to {d['HI'] * 100:+.1f})"
        lines.append(f"| {name} | {r['shooter_wins_series']['N']} | {share(r['shooter_wins_series'])} "
                     f"| {share(r['g1_winner_outshot'])}, {r['g1_winner_outshot']['N']} series "
                     f"| {share(r['g1_winner_not_outshot'])}, {r['g1_winner_not_outshot']['N']} series | {diff} |")
        readings.append(f"{name}: " + (
            "with the Game 1 result held fixed, outshooting the opponent from three adds nothing "
            "that the interval can tell from zero." if not excludes_zero_p(d) else
            f"with the Game 1 result held fixed, the Game 1 winner that also outshot its opponent wins the series "
            f"{'more' if d['P'] > 0 else 'less'} often."))
    dropped = {LEAGUES[k]: v for k, v in os_.filter(pl.col("ESTIMATE") == "difference")
               .select("LEAGUE", "N_DROPPED").iter_rows()}
    lines += ["", "Shares of series in percent with a 95% interval; the difference is in percentage points. "
              "Series with equal Game 1 three-point percentages, or a team with no Game 1 attempts, are left out ("
              + ", ".join(f"{k} {v}" for k, v in dropped.items()) + ")."]
    return "\n".join(lines + ["", "**Reading.** " + " ".join(readings)])


def excludes_zero_p(row: dict) -> bool:
    return row["LO"] is not None and (row["LO"] > 0 or row["HI"] < 0)


BREAK_LABELS = {"season_2020": "2020 (single site)", "other_seasons": "every other season",
                "best_of_3": "best-of-3", "best_of_5": "best-of-5", "best_of_7": "best-of-7"}


def num_cell(row: dict, k: float = 1.0) -> str:
    if row["LO"] is None:
        return f"{row['MEAN'] * k:+.2f} (one series)"
    return f"{row['MEAN'] * k:+.2f} ({row['LO'] * k:+.2f} to {row['HI'] * k:+.2f})"


def breaks_region(br: pl.DataFrame) -> str:
    lines = ["| League | Split | Series | 3P%: Game 1 minus Games 2+ | Attempt rate: Game 1 minus Games 2+ "
             "| Game 1 fouls per 100 possessions | Game 1 free-throw rate (x100) |", "|---|---|---|---|---|---|---|"]
    readings = []
    for lg, name in LEAGUES.items():
        sub = br.filter(pl.col("LEAGUE") == lg)
        for panel, label in BREAK_LABELS.items():
            if sub.filter(pl.col("PANEL") == panel).height == 0:
                continue
            m = {k: get(sub, lg, panel, k) for k in ("D_PCT", "D_RATE", "G1_PF100", "G1_FTR")}
            lines.append(f"| {name} | {label} | {m['D_PCT']['N']} | {num_cell(m['D_PCT'], 100)} "
                         f"| {num_cell(m['D_RATE'], 100)} | {num_cell(m['G1_PF100'])} | {num_cell(m['G1_FTR'], 100)} |")
        b, o = get(sub, lg, "season_2020", "G1_PF100"), get(sub, lg, "other_seasons", "G1_PF100")
        in_2020 = (f"there are too few 2020 series ({b['N']}) to say whether it held there"
                   if b["N"] < FEW else
                   f"in 2020 it {'holds' if excludes_zero(b) else 'is absent (the interval includes zero)'}, "
                   f"from {b['N']} series")
        readings.append(f"{name}: the Game 1 foul dip {'holds' if excludes_zero(o) else 'is absent'} in other "
                        f"seasons; {in_2020}.")
    lines += ["", "Percentage points except fouls (per 100 possessions); the foul and free-throw columns are "
              "Game 1's deviation from the series mean, as in question 4. Mean over series with a 95% interval."]
    return "\n".join(lines + ["", "**Reading.** " + " ".join(readings)])


def decades_region(pdec: pl.DataFrame) -> str:
    out, readings = [], []
    for lg, name in LEAGUES.items():
        sub = pdec.filter((pl.col("LEAGUE") == lg) & (pl.col("GAME_NO") == 1))
        decades = sorted(sub["DECADE"].unique().to_list())
        out += [f"**{name}, Game 1 deviation from the series mean, by decade.**", "",
                "| Rate | " + " | ".join(f"{d}s" for d in decades) + " |", "|---|" + "---|" * len(decades),
                "| Series | " + " | ".join(str(sub.filter((pl.col("DECADE") == d) & (pl.col("METRIC") == "PF100"))["N"].item())
                                         for d in decades) + " |"]
        every = []
        for m, (label, k) in PROFILE_LABELS.items():
            cells, hits = [], 0
            for d in decades:
                r = sub.filter((pl.col("DECADE") == d) & (pl.col("METRIC") == m)).row(0, named=True)
                text = f"{r['MEAN'] * k:+.2f}"
                hit = r["LO"] is not None and excludes_zero(r)
                hits += hit
                cells.append(f"**{text}**" if hit else text)
            out.append(f"| {label} | " + " | ".join(cells) + " |")
            if hits == len(decades):
                every.append(label.split(" (")[0].lower())
        out.append("")
        thin = [f"{d}s" for d in decades
                if sub.filter((pl.col("DECADE") == d) & (pl.col("METRIC") == "PF100"))["N"].item() < FEW]
        readings.append(f"{name}: " + (f"Game 1 differs from the series mean in every decade for {', '.join(every)}"
                                       if every else "no rate differs from the series mean in every decade")
                        + (f" (the {', '.join(thin)} hold{'s' if len(thin) == 1 else ''} fewer than {FEW} series)"
                           if thin else "") + ".")
    rate = pdec.filter((pl.col("LEAGUE") == 0) & (pl.col("METRIC") == "FG3A_RATE"))
    games = sorted(rate["GAME_NO"].unique().to_list())
    out += ["**NBA three-point attempt rate (x100) by game number and decade.**", "",
            "| Decade | " + " | ".join(f"G{g}" for g in games) + " |", "|---|" + "---|" * len(games)]
    for d in sorted(rate["DECADE"].unique().to_list()):
        cells = []
        for g in games:
            r = rate.filter((pl.col("DECADE") == d) & (pl.col("GAME_NO") == g)).row(0, named=True)
            text = f"{r['MEAN'] * 100:+.2f}"
            cells.append(f"**{text}**" if r["LO"] is not None and excludes_zero(r) else text)
        out.append(f"| {d}s | " + " | ".join(cells) + " |")
    out += ["", "Bold: the 95% interval excludes zero."]
    return "\n".join(out + ["", "**Reading.** " + " ".join(readings)])


def regions() -> dict[str, str]:
    summary = pl.read_csv(ROOT / "output" / "game1_summary.csv")
    pooled = pl.read_csv(ROOT / "output" / "game1_pooled.csv")
    season = pl.read_csv(ROOT / "output" / "game1_season.csv")
    prof = pl.read_csv(ROOT / "output" / "profile_summary.csv")
    state = pl.read_csv(ROOT / "output" / "profile_state.csv")
    return {"headline": headline(summary), "rate": rate(summary),
            "baseline": baseline(summary), "pooled": pooled_region(pooled),
            "eras": eras_region(summary, season),
            "profiles": profiles_region(prof), "state": state_region(state),
            "stakes": stakes_region(pl.read_csv(ROOT / "output" / "stakes_summary.csv")),
            "rest": rest_region(pl.read_csv(ROOT / "output" / "rest_summary.csv")),
            "outshoot": outshoot_region(pl.read_csv(ROOT / "output" / "outshoot_summary.csv")),
            "breaks": breaks_region(pl.read_csv(ROOT / "output" / "break_summary.csv")),
            "decades": decades_region(pl.read_csv(ROOT / "output" / "profile_decade.csv"))}


def render(text: str, new: dict[str, str]) -> str:
    for name, body in new.items():
        pat = re.compile(rf"(<!-- gen:{name} -->\n)(.*?)(<!-- /gen:{name} -->)", re.S)
        if not pat.search(text):
            raise KeyError(f"README has no gen:{name} region")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text)
    return text


def main() -> int:
    text = ABBR.sub(r"\1", README.read_text())
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
