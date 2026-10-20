"""Build the interactive figures for the family page (docs/story.md).

Every value comes from the committed summary outputs (game1_summary.csv,
game1_season.csv, profile_summary.csv, stakes_summary.csv, rest_summary.csv,
outshoot_summary.csv, break_summary.csv, profile_decade.csv,
officials_profile.csv, and experience_summary.csv), which 04_reconcile.py gates equal to the R run.
Figures are plotly originals written to figures/; report_builder.py swaps in
the family's famplot engine at publish time.

Figures:
  fig1_game1_gap_py        Game 1 minus later games, three-point percentage
                           and attempt rate, both comparisons, both leagues
  fig2_attempts_by_game_py three-point attempt rate by game number
  fig3_fouls_by_game_py    fouls per 100 possessions by game number
  fig4_decade_accuracy_py  Game 1 minus Games 2+ three-point percentage, by decade
  fig5_decade_volume_py    Game 1 minus Games 2+ attempt rate, by decade
  fig6_season_pct_py       Game 1 and Games 2+ three-point percentage per season
  fig7_season_rate_py      Game 1 and Games 2+ attempt rate per season
  fig8_stakes_py           Game 1 gaps by stage (distance from the Finals)
  fig9_rest_py             rested-minus-tired Game 1 contrast by rest gap (NBA)
  fig10_outshoot_py        Game 1 winner's series-win share, outshot or not
  fig11_fouls_eras_py      NBA Game 1 foul gap by decade, and 2020 against other seasons
  fig12_officials_py       fouls and crew tendency by game number
  fig13_experience_py      more minus less experienced team, Game 1 contrasts

Run:  python python/09_story_figures.py
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIG = ROOT / "figures"
LEAGUES = {0: "NBA", 10: "WNBA"}
# famplot's first two family colors, so each league keeps its color across figures.
COLORS = {0: "#2a78d6", 10: "#eb6834"}
# Lighter shades of the same, for a league's second series in one figure
# (famplot draws every marker as a filled circle; it has no marker.symbol).
LIGHT = {0: "#8db8ea", 10: "#f3a77f"}


def one(df: pl.DataFrame, **keys) -> dict:
    for k, v in keys.items():
        df = df.filter(pl.col(k) == v)
    if df.height != 1:
        raise SystemExit(f"expected one row for {keys}, found {df.height}")
    return df.row(0, named=True)


def base_layout(title: str, xtitle: str, ytitle: str) -> dict:
    return dict(title=title, xaxis_title=xtitle, yaxis_title=ytitle, template="plotly_white",
                height=420, margin=dict(l=70, r=30, t=60, b=60), legend=dict(orientation="h", y=-0.2))


def fig_gap(summary: pl.DataFrame) -> go.Figure:
    f = go.Figure()
    cats = ["Accuracy vs Games 2+", "Accuracy vs Game 2", "Attempt rate vs Games 2+", "Attempt rate vs Game 2"]
    metrics = ["D_PCT", "D2_PCT", "D_RATE", "D2_RATE"]
    for lg, name in LEAGUES.items():
        rows = [one(summary, LEAGUE=lg, PANEL="all", METRIC=m) for m in metrics]
        f.add_trace(go.Scatter(
            x=cats, y=[r["MEAN"] * 100 for r in rows], mode="markers", name=f"{name} ({rows[0]['N']} series)",
            error_y=dict(type="data", symmetric=False,
                         array=[(r["HI"] - r["MEAN"]) * 100 for r in rows],
                         arrayminus=[(r["MEAN"] - r["LO"]) * 100 for r in rows]),
            marker=dict(size=10),
            hovertemplate=f"{name}, %{{x}}: %{{y:+.2f}} points<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("Game 1 accuracy sits on zero; NBA Game 1 volume is lower",
                                  "", "Percentage points (95% interval)"))
    return f


def fig_by_game(prof: pl.DataFrame, metric: str, scale: float, title: str, ytitle: str, unit: str) -> go.Figure:
    f = go.Figure()
    for lg, name in LEAGUES.items():
        rows = (prof.filter((pl.col("LEAGUE") == lg) & (pl.col("PANEL") == "all") & (pl.col("METRIC") == metric))
                    .sort("GAME_NO"))
        if rows.height == 0:
            raise SystemExit(f"no profile rows for {name} {metric}")
        f.add_trace(go.Scatter(
            x=[f"G{g}" for g in rows["GAME_NO"].to_list()], y=(rows["MEAN"] * scale).to_list(),
            mode="lines+markers", name=name,
            error_y=dict(type="data", symmetric=False,
                         array=((rows["HI"] - rows["MEAN"]) * scale).to_list(),
                         arrayminus=((rows["MEAN"] - rows["LO"]) * scale).to_list()),
            customdata=[[n] for n in rows["N"].to_list()],
            hovertemplate=f"{name}, %{{x}}: %{{y:+.2f}} {unit} (%{{customdata[0]}} games)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout(title, "Game number", ytitle))
    # Category labels: famplot draws numeric axes with half-game ticks.
    return f


def fig_decade(summary: pl.DataFrame, metric: str, title: str, unit: str) -> go.Figure:
    f = go.Figure()
    for lg, name in LEAGUES.items():
        rows = (summary.filter((pl.col("LEAGUE") == lg) & (pl.col("METRIC") == metric)
                               & pl.col("PANEL").str.contains(r"^\d{4}s$"))
                       .sort("PANEL"))
        if rows.height == 0:
            raise SystemExit(f"no decade rows for {name} {metric}")
        f.add_trace(go.Scatter(
            x=rows["PANEL"].to_list(), y=(rows["MEAN"] * 100).to_list(), mode="lines+markers", name=name,
            error_y=dict(type="data", symmetric=False,
                         array=((rows["HI"] - rows["MEAN"]) * 100).to_list(),
                         arrayminus=((rows["MEAN"] - rows["LO"]) * 100).to_list()),
            marker=dict(size=9, color=COLORS[lg]), line=dict(color=COLORS[lg]),
            customdata=[[n] for n in rows["N"].to_list()],
            hovertemplate=f"{name}, %{{x}}: %{{y:+.2f}} {unit} (%{{customdata[0]}} series)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout(title, "Decade (season end year)", "Game 1 minus Games 2+ (95% interval)"))
    f.update_xaxes(type="category")
    return f


def fig_season_levels(season: pl.DataFrame, seg: str, title: str, ytitle: str) -> go.Figure:
    """Game 1 (solid) and Games 2+ (dashed) per season, both leagues."""
    f = go.Figure()
    for lg, name in LEAGUES.items():
        rows = season.filter(pl.col("LEAGUE") == lg).sort("SEASON")
        if rows.height == 0:
            raise SystemExit(f"no season rows for {name}")
        labels = [f"{y - 1}-{y % 100:02d}" if lg == 0 else str(y) for y in rows["SEASON"].to_list()]
        for part, dash, attempts in (("G1", None, "G1_A"), ("REST", "dash", "REST_A")):
            label = "Game 1" if part == "G1" else "Games 2+"
            y = [None if v is None else round(v * 100, 2) for v in rows[f"{part}_{seg}"].to_list()]
            f.add_trace(go.Scatter(
                x=rows["SEASON"].to_list(), y=y, mode="lines", name=f"{name} {label}",
                line=dict(color=COLORS[lg], dash=dash, width=2 if part == "G1" else 1.5),
                customdata=[[s, int(a)] for s, a in zip(labels, rows[attempts].to_list())],
                hovertemplate=f"{name} %{{customdata[0]}}, {label}: %{{y:.1f}}% "
                              f"(%{{customdata[1]}} 3PA)<extra></extra>"))
    f.update_layout(**base_layout(title, "Season (end year)", ytitle))
    return f


def interval(rows: list[dict], scale: float, mean: str = "MEAN") -> dict:
    return dict(type="data", symmetric=False,
                array=[(r["HI"] - r[mean]) * scale for r in rows],
                arrayminus=[(r[mean] - r["LO"]) * scale for r in rows])


def stage_label(stage: int) -> str:
    return "Finals" if stage == 0 else f"{stage} round{'s' if stage > 1 else ''} before"


def fig_stakes(st: pl.DataFrame) -> go.Figure:
    """NBA and WNBA Game 1 attempt-rate and accuracy gaps by stage."""
    f = go.Figure()
    for lg, name in LEAGUES.items():
        stages = sorted(st.filter(pl.col("LEAGUE") == lg)["STAGE"].unique().to_list(), reverse=True)
        if not stages:
            raise SystemExit(f"no stage rows for {name}")
        for metric, label, color in (("D_RATE", "share of shots from three", COLORS[lg]),
                                     ("D_PCT", "three-point percentage", LIGHT[lg])):
            rows = [one(st, LEAGUE=lg, STAGE=s, METRIC=metric) for s in stages]
            f.add_trace(go.Scatter(
                x=[stage_label(s) for s in stages], y=[r["MEAN"] * 100 for r in rows], mode="markers",
                name=f"{name}, {label}", error_y=interval(rows, 100),
                marker=dict(size=10, color=color),
                customdata=[[r["N"]] for r in rows],
                hovertemplate=f"{name} %{{x}}, {label}: %{{y:+.2f}} points (%{{customdata[0]}} series)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("Game 1 minus Games 2+, by round", "Round (distance from the Finals)",
                                  "Percentage points (95% interval)"))
    # Category order is first appearance; the NBA (four stages) comes first.
    f.update_xaxes(type="category")
    return f


def fig_rest(rs: pl.DataFrame) -> go.Figure:
    """NBA only: the WNBA's intervals (8 to 97 series a bin) would swamp it; its
    numbers are in the README."""
    bins = ["1-2", "3-5", "6+", "any"]
    labels = ["1-2 days", "3-5 days", "6+ days", "any gap"]
    rows = [one(rs, LEAGUE=0, BIN=b, METRIC="CONTRAST_PCT") for b in bins]
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=labels, y=[r["MEAN"] * 100 for r in rows], mode="markers", name="NBA", error_y=interval(rows, 100),
        marker=dict(size=10, color=COLORS[0]), customdata=[[r["N"]] for r in rows],
        hovertemplate="NBA, %{x}: %{y:+.2f} points (%{customdata[0]} series)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("NBA: more-rested team's Game 1 three-point shooting, relative to the less-rested",
                                  "Rest gap before Game 1", "Percentage points (95% interval)"))
    f.update_xaxes(type="category")
    return f


def fig_outshoot(os_: pl.DataFrame) -> go.Figure:
    """One column per league and Game 1 shooting result, each league's pair
    side by side; one trace with per-point colors keeps that order (famplot
    orders categories by first appearance)."""
    kinds = (("g1_winner_outshot", "also outshot", "#2a78d6"), ("g1_winner_not_outshot", "was outshot", "#898781"))
    rows, x, colors = [], [], []
    for lg, name in LEAGUES.items():
        for est, short, color in kinds:
            rows.append(one(os_, LEAGUE=lg, ESTIMATE=est))
            x.append(f"{name}, Game 1 winner {short}")
            colors.append(color)
    f = go.Figure(go.Scatter(
        x=x, y=[r["P"] * 100 for r in rows], mode="markers", name="Series won",
        error_y=interval(rows, 100, "P"), marker=dict(size=11, color=colors), showlegend=False,
        customdata=[[r["N"]] for r in rows],
        hovertemplate="%{x} from three: %{y:.1f}% win the series (%{customdata[0]} series)<extra></extra>"))
    f.update_layout(**base_layout("How often the Game 1 winner wins the series, by Game 1 three-point shooting",
                                  "", "Series won, % (95% interval)"))
    f.update_xaxes(type="category")
    return f


def fig_fouls_eras(pdec: pl.DataFrame, br: pl.DataFrame) -> go.Figure:
    """NBA Game 1 PF100 deviation by decade, then 2020 against every other season."""
    dec = (pdec.filter((pl.col("LEAGUE") == 0) & (pl.col("GAME_NO") == 1) & (pl.col("METRIC") == "PF100"))
               .sort("DECADE"))
    if dec.height == 0:
        raise SystemExit("no NBA decade foul rows")
    d_rows = dec.to_dicts()
    split = [one(br, LEAGUE=0, PANEL=p, METRIC="G1_PF100") for p in ("other_seasons", "season_2020")]
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=[f"{r['DECADE']}s" for r in d_rows], y=[r["MEAN"] for r in d_rows], mode="markers", name="By decade",
        error_y=interval(d_rows, 1), marker=dict(size=10, color=COLORS[0]),
        customdata=[[r["N"]] for r in d_rows],
        hovertemplate="NBA %{x}: %{y:+.2f} fouls per 100 (%{customdata[0]} series)<extra></extra>"))
    f.add_trace(go.Scatter(
        x=["Every season but 2020", "2020 (single site)"], y=[r["MEAN"] for r in split], mode="markers",
        name="2020 against the rest", error_y=interval(split, 1), marker=dict(size=10, color="#898781"),
        customdata=[[r["N"]] for r in split],
        hovertemplate="NBA %{x}: %{y:+.2f} fouls per 100 (%{customdata[0]} series)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("NBA Game 1 fouls against the series average", "",
                                  "Fouls per 100 possessions (95% interval)"))
    f.update_xaxes(type="category")
    return f


def fig_officials(op: pl.DataFrame) -> go.Figure:
    """Per league: the PF100 deviation by game number and the crew tendency."""
    f = go.Figure()
    for lg, name in LEAGUES.items():
        for part, label, dash in (("pf100", "fouls", None), ("crew", "crew tendency", "dash")):
            rows = op.filter((pl.col("LEAGUE") == lg) & (pl.col("PART") == part)
                             & (pl.col("N") >= MIN_GAMES)).sort("GAME_NO").to_dicts()
            if not rows:
                raise SystemExit(f"no officials rows for {name} {part}")
            f.add_trace(go.Scatter(
                x=[f"G{r['GAME_NO']}" for r in rows], y=[r["MEAN"] for r in rows], mode="lines+markers",
                name=f"{name} {label}", error_y=interval(rows, 1),
                line=dict(color=COLORS[lg] if part == "pf100" else LIGHT[lg], dash=dash),
                marker=dict(size=8, color=COLORS[lg] if part == "pf100" else LIGHT[lg]),
                customdata=[[r["N"]] for r in rows],
                hovertemplate=f"{name} {label}, %{{x}}: %{{y:+.2f}} per 100 (%{{customdata[0]}})<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("Fouls and the officials' usual tendency, by game number", "Game number",
                                  "Fouls per 100 possessions from the series mean"))
    f.update_xaxes(type="category")
    return f


def fig_experience(es: pl.DataFrame) -> go.Figure:
    """Every-gap contrasts per league and measure; one trace per contrast."""
    cats = [(lg, m) for lg in LEAGUES for m in ("roster", "franchise")]
    f = go.Figure()
    for metric, label, scale, color in (("CONTRAST_PCT", "three-point percentage (points)", 100, "#2a78d6"),
                                        ("CONTRAST_RATE", "share of shots from three (points)", 100, "#8db8ea"),
                                        ("CONTRAST_PF", "fouls per 100 possessions", 1, "#eb6834")):
        rows = [one(es, LEAGUE=lg, MEASURE=m, BIN="any", METRIC=metric) for lg, m in cats]
        f.add_trace(go.Scatter(
            x=[f"{LEAGUES[lg]}, {m}" for lg, m in cats], y=[r["MEAN"] * scale for r in rows], mode="markers",
            name=label, error_y=interval(rows, scale), marker=dict(size=10, color=color),
            customdata=[[r["N"]] for r in rows],
            hovertemplate=f"%{{x}} experience, {label}: %{{y:+.2f}} (%{{customdata[0]}} series)<extra></extra>"))
    f.add_hline(y=0, line_width=1, line_color="#898781")
    f.update_layout(**base_layout("More experienced minus less experienced team, Game 1 against later games",
                                  "League and experience measure", "Contrast (95% interval)"))
    f.update_xaxes(type="category")
    return f


# Game numbers with fewer games than this are left off fig12 (WNBA Game 5
# rests on a handful of series; Game 4 too before the October 19, 2026
# officials amendment).
MIN_GAMES = 20


def main() -> None:
    FIG.mkdir(exist_ok=True)
    summary = pl.read_csv(OUT / "game1_summary.csv")
    prof = pl.read_csv(OUT / "profile_summary.csv")
    season = pl.read_csv(OUT / "game1_season.csv")
    figs = {
        "fig1_game1_gap_py": fig_gap(summary),
        "fig2_attempts_by_game_py": fig_by_game(
            prof, "FG3A_RATE", 100, "Share of shots from three, by game number",
            "Points of FGA from the series mean (95% interval)", "points"),
        "fig3_fouls_by_game_py": fig_by_game(
            prof, "PF100", 1, "Fouls per 100 possessions, by game number",
            "Difference from the series mean (95% interval)", "fouls per 100"),
        "fig4_decade_accuracy_py": fig_decade(
            summary, "D_PCT", "Game 1 three-point percentage gap, by decade", "points"),
        "fig5_decade_volume_py": fig_decade(
            summary, "D_RATE", "Game 1 share of shots from three, gap by decade", "points of FGA"),
        "fig6_season_pct_py": fig_season_levels(
            season, "PCT", "Three-point percentage by season, Game 1 and Games 2+", "3P% (all series pooled)"),
        "fig7_season_rate_py": fig_season_levels(
            season, "RATE", "Share of shots from three by season, Game 1 and Games 2+",
            "3PA / FGA, % (all series pooled)"),
        "fig8_stakes_py": fig_stakes(pl.read_csv(OUT / "stakes_summary.csv")),
        "fig9_rest_py": fig_rest(pl.read_csv(OUT / "rest_summary.csv", schema_overrides={"BIN": pl.Utf8})),
        "fig10_outshoot_py": fig_outshoot(pl.read_csv(OUT / "outshoot_summary.csv")),
        "fig11_fouls_eras_py": fig_fouls_eras(pl.read_csv(OUT / "profile_decade.csv"),
                                              pl.read_csv(OUT / "break_summary.csv")),
        "fig12_officials_py": fig_officials(pl.read_csv(OUT / "officials_profile.csv")),
        "fig13_experience_py": fig_experience(pl.read_csv(OUT / "experience_summary.csv")),
    }
    for name, fig in figs.items():
        fig.write_html(FIG / f"{name}.html", include_plotlyjs="cdn")
        print(f"wrote figures/{name}.html")


if __name__ == "__main__":
    main()
