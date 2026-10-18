"""Build the interactive figures for the family page (docs/story.md).

Every value comes from the committed summary outputs (game1_summary.csv and
profile_summary.csv), which 04_reconcile.py gates equal to the R run.
Figures are plotly originals written to figures/; report_builder.py swaps in
the family's famplot engine at publish time.

Figures:
  fig1_game1_gap_py        Game 1 minus later games, three-point percentage
                           and attempt rate, both comparisons, both leagues
  fig2_attempts_by_game_py three-point attempt rate by game number
  fig3_fouls_by_game_py    fouls per 100 possessions by game number

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
    f.update_layout(**base_layout("Game 1 minus later games in the same series",
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


def main() -> None:
    FIG.mkdir(exist_ok=True)
    summary = pl.read_csv(OUT / "game1_summary.csv")
    prof = pl.read_csv(OUT / "profile_summary.csv")
    figs = {
        "fig1_game1_gap_py": fig_gap(summary),
        "fig2_attempts_by_game_py": fig_by_game(
            prof, "FG3A_RATE", 100, "Share of shots from three, by game number",
            "Points of FGA from the series mean (95% interval)", "points"),
        "fig3_fouls_by_game_py": fig_by_game(
            prof, "PF100", 1, "Fouls per 100 possessions, by game number",
            "Difference from the series mean (95% interval)", "fouls per 100"),
    }
    for name, fig in figs.items():
        fig.write_html(FIG / f"{name}.html", include_plotlyjs="cdn")
        print(f"wrote figures/{name}.html")


if __name__ == "__main__":
    main()
