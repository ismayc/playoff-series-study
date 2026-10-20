"""Explainer diagrams for the family page (docs/story.md), drawn with the
family's famdiagram (../basketball-analysis-tools/famdiagram.py) and saved to
figures/<ref>.svg plus a <ref>_narrow.svg phone layout. report_builder.py
inlines them so they follow the page theme.

Every number drawn is read from a committed summary output; none is typed
here, and no diagram shows a single game or series (per-game and per-series
tables stay local, see DATA_SOURCES.md and CLAUDE.md).

Diagrams:
  dg1_within_series  why every comparison stays inside one series: how many
                     series reach each game number, and how one series'
                     Game 1 is set against its own later games, with the
                     NBA results (output/profile_summary.csv,
                     game1_summary.csv, game1_pooled.csv)
  dg2_officials      the two explanations for the Game 1 foul dip and what
                     each measurement says (output/officials_profile.csv,
                     officials_within.csv, officials_reliability.csv)
  dg3_outshoot       why outshooting in Game 1 looks like it matters: the
                     NBA series split by whether the better three-point
                     team also won Game 1 (output/outshoot_summary.csv)

Run:     python python/16_diagrams.py
--check: rebuild every SVG in memory and fail if a committed one differs.
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIG = ROOT / "figures"
sys.path.insert(0, str(ROOT.parent / "basketball-analysis-tools"))
import famdiagram as fd  # noqa: E402

NBA, WNBA = 0, 10


def one(df: pl.DataFrame, **keys) -> dict:
    for k, v in keys.items():
        df = df.filter(pl.col(k) == v)
    if df.height != 1:
        raise SystemExit(f"expected one row for {keys}, found {df.height}")
    return df.row(0, named=True)


def sgn(v: float, d: int = 2) -> str:
    return f"{v:+.{d}f}".replace("-", "−")


def pct(v: float, d: int = 1) -> str:
    return f"{v * 100:.{d}f}%"


def wrap(s: str, width: float, size: float) -> list[str]:
    """Greedy word wrap on an estimated glyph width."""
    per = size * 0.55
    out, cur = [], ""
    for w in s.split():
        t = f"{cur} {w}".strip()
        if len(t) * per > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def para(d: fd.Diagram, x, y, s, width, size, lh=None, **kw) -> float:
    """Wrapped text from baseline y; returns the baseline of the last line."""
    lh = lh or size * 1.35
    lines = wrap(s, width, size)
    for i, line in enumerate(lines):
        d.text(x, y + i * lh, line, size=size, **kw)
    return y + (len(lines) - 1) * lh


def arrow(d: fd.Diagram, x1, y1, x2, y2, stroke="ink3", sw=1.5) -> None:
    """A line with a drawn arrowhead. famdiagram's marker arrows share one
    id, and on phones the first SVG holding it is display:none, so the
    marker does not render; a drawn triangle always does."""
    ang = math.atan2(y2 - y1, x2 - x1)
    hl, hw = 9, 5
    bx, by = x2 - hl * math.cos(ang), y2 - hl * math.sin(ang)
    d.line(x1, y1, bx, by, stroke=stroke, sw=sw)
    px, py = -math.sin(ang) * hw, math.cos(ang) * hw
    d.path(f"M{x2:.1f},{y2:.1f} L{bx + px:.1f},{by + py:.1f} L{bx - px:.1f},{by - py:.1f} Z",
           fill=stroke, stroke=None)


def card(d: fd.Diagram, x, y, w, h, accent=None) -> None:
    d.rect(x, y, w, h, fill="surface2", stroke="rule", rx=8)
    if accent:
        d.rect(x, y, 6, h, fill=accent, rx=3)


# ---------------------------------------------------------------- dg1
def within_series(narrow: bool) -> fd.Diagram:
    prof = pl.read_csv(OUT / "profile_summary.csv")
    reach = (prof.filter((pl.col("LEAGUE") == NBA) & (pl.col("PANEL") == "all")
                         & (pl.col("METRIC") == "PF100"))
                 .sort("GAME_NO").select("GAME_NO", "N").rows())
    summ = pl.read_csv(OUT / "game1_summary.csv")
    d1 = one(summ, LEAGUE=NBA, PANEL="all", METRIC="D_PCT")
    d2 = one(summ, LEAGUE=NBA, PANEL="all", METRIC="D2_PCT")
    pooled = one(pl.read_csv(OUT / "game1_pooled.csv"), LEAGUE=NBA)
    n_series = reach[0][1]
    max_games = reach[-1][0]
    first = (pl.read_csv(OUT / "game1_season.csv").filter(pl.col("LEAGUE") == NBA)["SEASON"].min())
    since = f"{first - 1}-{str(first)[-2:]}"

    W = 360 if narrow else 760
    fs, small, head = (13, 12, 17) if narrow else (15, 14, 20)
    pad = 12
    d = fd.Diagram(W, 10, "Why every comparison stays inside one series")

    # ---- panel A: how many series reach each game
    aw = W - 2 * pad if narrow else 300
    y = 28
    d.text(pad, y, "1. Later games come from fewer series", size=head, display=True,
           weight="600")
    y = para(d, pad, y + 24, f"NBA series since {since}. The blue band is the series "
             "still going at each game; the gray piece peels off the series that ended "
             "in that game.", aw, small, fill="ink2")
    # Flow of counts, top to bottom: band width is the number of series
    # alive at each game, and each game's ended series leave to the right.
    top = y + 22
    rowh = 30
    lw = 30                      # game labels
    bwmax = aw * 0.52
    x0 = pad + lw
    ws = [bwmax * n / n_series for _, n in reach]
    lx = x0 + bwmax + 18
    for k, (g, n) in enumerate(reach):
        ry = top + k * rowh
        nxt = reach[k + 1][1] if k + 1 < len(reach) else 0
        wn = ws[k + 1] if k + 1 < len(reach) else 0
        d.text(pad, ry + rowh * 0.62, f"G{g}", size=small, fill="ink",
               weight="700" if g == 1 else None)
        d.rect(x0, ry + 4, wn, rowh - 8, fill="nba", opacity=1.0 if g == 1 else 0.75)
        if k + 1 < len(reach):
            d.rect(x0, ry + rowh - 4, wn, 8, fill="nba", opacity=0.35)
        ended = n - nxt
        if ended > 0:
            d.rect(x0 + wn, ry + 4, ws[k] - wn, rowh - 8, fill="ink3", opacity=0.8)
            d.path(f"M{x0 + ws[k]:.1f},{ry + rowh / 2:.1f} L{lx - 4:.1f},{ry + rowh / 2:.1f}",
                   stroke="ink3", sw=1.5, dash="2 3")
            last = k + 1 == len(reach)
            d.text(lx, ry + rowh * 0.62, f"{ended:,} " + ("played a G7" if last
                   else f"ended in G{g}"), size=small, fill="ink2")
        if g == 1:
            d.text(x0 + 6, ry + rowh * 0.62, f"{n:,}", size=small, fill="surface", weight="700")
    yb = top + len(reach) * rowh - 2 * small - 20
    ya = para(d, pad, yb + 2 * small + 40, f"Every series has a Game 1, but only "
              f"{reach[-1][1]:,} of {n_series:,} reach a Game {max_games}, and those are the close "
              "ones. A league-wide Game 1 against Game 7 would compare different series.",
              aw, small, fill="ink2")

    # ---- panel B: one series, compared with itself
    if narrow:
        bx, by_, bw = pad, ya + 44, W - 2 * pad
    else:
        bx, by_, bw = pad + aw + 40, 28, W - (pad + aw + 40) - pad
    d.text(bx, by_, "2. Compare each series with itself", size=head, display=True,
           weight="600")
    y = para(d, bx, by_ + 24, "Both teams' made and attempted threes, pooled:", bw, small,
             fill="ink2") + 22
    gw = (bw - 10) / max_games
    gh = 34

    def strip(y, rest_upto, label, note, value):
        for g in range(1, max_games + 1):
            x = bx + (g - 1) * gw + (10 if g > 1 else 0)
            if g == 1:
                fill, op, dash, stroke = "nba", 1.0, None, None
            elif g <= rest_upto:
                fill, op, dash, stroke = "c4", 0.9, None, None
            else:
                fill, op, dash, stroke = "surface2", 1.0, "3 3", "rule"
            d.rect(x + 2, y, gw - 4, gh, fill=fill, rx=4, opacity=op, stroke=stroke, dash=dash)
            d.text(x + gw / 2, y + gh / 2 + 5, f"G{g}", size=small, anchor="middle",
                   fill="surface" if g <= rest_upto else "ink3", weight="700")
        yy = y + gh + 22
        d.text(bx, yy, label, size=fs, fill="ink", weight="700")
        yy = para(d, bx, yy + fs * 1.35, note, bw, small, fill="ink2")
        d.text(bx, yy + fs * 1.6, value, size=fs + 1, fill="nba", weight="700")
        return yy + fs * 1.6

    y = strip(y, max_games, "Game 1 against Games 2 on",
              "Game 1's three-point percentage minus the rest of the series', then averaged "
              f"over {n_series:,} series.",
              f"{sgn(d1['MEAN'] * 100)} points ({sgn(d1['LO'] * 100)} to {sgn(d1['HI'] * 100)})")
    y = strip(y + 32, 2, "Game 1 against Game 2 alone",
              "Every series has a Game 2, so this check has no close-series tilt.",
              f"{sgn(d2['MEAN'] * 100)} points ({sgn(d2['LO'] * 100)} to {sgn(d2['HI'] * 100)})")
    y = para(d, bx, y + 32, f"Counting every NBA three together instead: Game 1s hit "
             f"{pct(pooled['G1_PCT'], 2)}, later games {pct(pooled['REST_PCT'], 2)}.",
             bw, small, fill="ink3", italic=True)
    d.h = max(y, ya) + 16
    return d


# ---------------------------------------------------------------- dg2
def officials(narrow: bool) -> fd.Diagram:
    prof = pl.read_csv(OUT / "officials_profile.csv")
    dip = one(prof, LEAGUE=NBA, PART="pf100", GAME_NO=1)
    crew = one(prof, LEAGUE=NBA, PART="crew", GAME_NO=1)
    wcrew = one(prof, LEAGUE=WNBA, PART="crew", GAME_NO=1)
    within = pl.read_csv(OUT / "officials_within.csv")
    win, wwin = one(within, LEAGUE=NBA), one(within, LEAGUE=WNBA)
    rel = one(pl.read_csv(OUT / "officials_reliability.csv"), LEAGUE=NBA)

    W = 360 if narrow else 760
    fs, small, head = (13, 12, 17) if narrow else (15, 14, 19)
    pad = 12
    d = fd.Diagram(W, 10, "Two explanations for the Game 1 foul dip, and what each measurement says")

    # top: the fact
    tw = W - 2 * pad
    y = 14
    th = 92 if narrow else 74
    card(d, pad, y, tw, th, accent="nba")
    d.text(pad + 20, y + 28, "The fact: Game 1 has the fewest fouls", size=head, display=True,
           weight="600")
    para(d, pad + 20, y + 28 + fs * 1.5,
         f"NBA games with listed officials: Game 1 runs {sgn(dip['MEAN'])} fouls per 100 "
         f"possessions against the series average ({dip['N']:,} series).", tw - 34, small,
         fill="ink2")
    y += th
    # two branches
    gap = 24
    bw = tw if narrow else (tw - gap) / 2
    branches = [
        ("A", "Lighter-whistling crews get Game 1s?",
         "Each crew's usual foul level, from its other games: the Game 1 crew against the "
         "series' other crews.",
         f"{sgn(crew['MEAN'])}", f"({sgn(crew['LO'])} to {sgn(crew['HI'])}, {crew['N']:,} series; "
         f"WNBA {sgn(wcrew['MEAN'])})",
         "No: Game 1s get ordinary crews.", "ink3"),
        ("B", "The same officials call Game 1s lighter?",
         "Each official's fouls per 100 possessions in their Game 1s against their own later "
         "games.",
         f"{sgn(win['MEAN'])}", f"({sgn(win['LO'])} to {sgn(win['HI'])}, {win['N']:,} officials; "
         f"WNBA {sgn(wwin['MEAN'])})",
         "Yes: the dip is in how Game 1s are called.", "c3"),
    ]
    def body(dd, bx, by_, b) -> float:
        """Draw a branch's text from the card top; returns the last baseline."""
        k, q, how, val, ci, verdict, col = b
        tx, inner = bx + 20, bw - 34
        yy = para(dd, tx, by_ + 30, f"{k}. {q}", inner, fs + 1, fill="ink", weight="700")
        yy = para(dd, tx, yy + 8 + small * 1.35, how, inner, small, fill="ink2")
        yy += 22 + fs + 8
        dd.text(tx, yy, val, size=fs + 12, fill=col if col != "ink3" else "ink", weight="700")
        yy = para(dd, tx, yy + small * 1.6, ci, inner, small, fill="ink3")
        return para(dd, tx, yy + 14 + fs, verdict, inner, fs, fill="ink", weight="600")

    # measure on a scratch canvas, then draw cards behind the text
    hs = [body(fd.Diagram(W, 10, ""), 0, 0, b) + 18 for b in branches]
    if not narrow:
        hs = [max(hs)] * 2
    tops = []
    for i, h in enumerate(hs):
        bx = pad if narrow else pad + i * (bw + gap)
        by_ = y + 44 if (not narrow or i == 0) else tops[0][1] + tops[0][2] + 44
        tops.append((bx, by_, h))
    for (bx, by_, h), b in zip(tops, branches):
        ax = W / 2 if narrow else bx + bw / 2
        arrow(d, ax, by_ - 40, ax, by_ - 6)
        card(d, bx, by_, bw, h, accent=b[6])
        body(d, bx, by_, b)
    y = max(by_ + h for _, by_, h in tops) + 30
    last = para(d, pad, y, f"Officials do differ from one another: an NBA official's foul level in "
                f"even-numbered seasons tracks their level in odd ones (r = {sgn(rel['R'])}). So "
                "crew assignment could have mattered; the data say it did not.", tw, small,
                fill="ink2")
    d.h = last + 14
    return d


# ---------------------------------------------------------------- dg3
def outshoot(narrow: bool) -> fd.Diagram:
    o = pl.read_csv(OUT / "outshoot_summary.csv")
    total = one(o, LEAGUE=NBA, ESTIMATE="shooter_wins_series")
    a = one(o, LEAGUE=NBA, ESTIMATE="g1_winner_outshot")
    b = one(o, LEAGUE=NBA, ESTIMATE="g1_winner_not_outshot")
    # The outshooter's overall share is the two branches' weighted average;
    # check it so the diagram's arithmetic is the table's.
    recombined = (a["N"] * a["P"] + b["N"] * (1 - b["P"])) / (a["N"] + b["N"])
    if a["N"] + b["N"] != total["N"] or abs(recombined - total["P"]) > 1e-9:
        raise SystemExit("outshoot branches do not recombine to the overall share")

    W = 360 if narrow else 760
    fs, small, head = (13, 12, 17) if narrow else (15, 14, 19)
    pad = 12
    d = fd.Diagram(W, 10, "Outshooting in Game 1 and winning the series")
    tw = W - 2 * pad
    y = 14
    rh = 104 if narrow else 92
    card(d, pad, y, tw, rh, accent="nba")
    d.text(pad + 20, y + 28, f"{total['N']:,} NBA series", size=head, display=True, weight="600")
    para(d, pad + 20, y + 28 + fs * 1.5, "Which team shot the better three-point percentage "
         f"in Game 1? ({total['N_DROPPED']} more series had no better shooter and are left "
         "out.)", tw - 34, fs, fill="ink2")
    y += rh
    gap = 24
    bw = tw if narrow else (tw - gap) / 2
    leaves = [
        (a, "It also won Game 1", a["P"], "c3",
         "Here the better shooter is the Game 1 winner."),
        (b, "It lost Game 1", 1 - b["P"], "ink3",
         f"The Game 1 winner, the worse shooter, took the other {pct(b['P'])}."),
    ]
    inner = bw - 34
    lh = 118 + max(len(wrap(n, inner, small)) for *_, n in leaves) * small * 1.35 + 14
    ends = []
    for i, (r, lab, shooter_p, col, note) in enumerate(leaves):
        bx = pad if narrow else pad + i * (bw + gap)
        by_ = y + 44 if not narrow else y + 44 + i * (lh + 44)
        arrow(d, bx + bw / 2, by_ - 40, bx + bw / 2, by_ - 6)
        card(d, bx, by_, bw, lh, accent=col)
        tx = bx + 20
        d.text(tx, by_ + 28, lab, size=fs + 1, fill="ink", weight="700")
        d.text(bx + bw - 14, by_ + 28, f"{r['N']:,} series", size=small, fill="ink3",
               anchor="end")
        # bar: share of these series the better shooter went on to win
        d.rect(tx, by_ + 44, inner, 16, fill="rule", rx=3)
        d.rect(tx, by_ + 44, inner * shooter_p, 16, fill=col, rx=3)
        d.text(tx, by_ + 94, pct(shooter_p), size=fs + 10, fill="ink", weight="700")
        d.text(tx + (fs + 10) * 3.2, by_ + 94, "won by the better shooter", size=small,
               fill="ink2")
        para(d, tx, by_ + 122, note, inner, small, fill="ink2")
        ends.append(by_ + lh)
    y = max(ends) + 30
    y = para(d, pad, y, f"Together the better Game 1 shooter wins {pct(total['P'])} of series. "
             f"That share is mostly the Game 1 result: the Game 1 winner takes about "
             f"{pct(a['P'], 0)} of series whether or not it also outshot the other team.",
             tw, fs, fill="ink2")
    d.h = y + 14
    return d


DIAGRAMS = {"dg1_within_series": within_series, "dg2_officials": officials,
            "dg3_outshoot": outshoot}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        fails = []
        with tempfile.TemporaryDirectory() as tmp:
            for ref, fn in DIAGRAMS.items():
                for p in fd.save(Path(tmp), ref, fn(False), fn(True)):
                    old = FIG / p.name
                    if not old.exists() or old.read_text() != p.read_text():
                        fails.append(p.name)
        for f in fails:
            print("FAIL", f, "differs from a fresh build")
        print("DIAGRAMS", "FAILED" if fails else
              f"PASSED: {len(DIAGRAMS)} diagrams rebuild identically")
        return 1 if fails else 0
    for ref, fn in DIAGRAMS.items():
        for p in fd.save(FIG, ref, fn(False), fn(True)):
            print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
