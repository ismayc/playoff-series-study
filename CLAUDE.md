# playoff-series-study

Is Game 1 three-point shooting worse than the rest of a playoff series, in
the NBA and the WNBA? Then: how the Game 1 gap moves with round and with
the rest gap between the two teams, and how every box-score count drifts
by game number through a series. Personal research in the
basketball-data-science family. The design, the pre-specified analysis,
and what loading the data showed are in `docs/design.md`; read it first.

## Data context

- **Grain:** `data/team_games.csv` is one row per team per playoff game
  (two rows per game), valid series only. `data/team_seasons.csv` is one
  row per team-season of regular-season totals. `output/series.csv` is one
  row per series, valid or not, with the reason.
- **Keys and joins:** a series is `LEAGUE` + `SEASON` + `SERIES_KEY`
  (lower team id, higher team id). Game rows join to their opponent on
  `GAME_ID` (exactly two rows each; `pair_games` raises otherwise).
  Baselines join on `LEAGUE` + `SEASON` + `TEAM_ID`, many to one.
- **Metric definitions:** 3P% = FG3M / FG3A over pooled makes and
  attempts, never an average of per-game percentages. Possessions =
  FGA + 0.44 FTA - OREB + TOV. Rest = calendar days since the team's
  previous game, play-in included; rest gap = team rest minus opponent rest
  in the same Game 1. `SEASON` is the year the season ends.
- **Known issues:** game IDs for seasons ending before 2002 do not encode
  series or game, so `GAME_NO` always comes from date order, and 02 checks
  it against the encoded digit from 2002 on. NBA 3PA, TOV, and OREB are
  incomplete before 1984-85 (`output/coverage.csv`). The 1954 NBA round
  robins and the 2026 WNBA Finals (in progress at harvest) are excluded as
  known invalid in `02_build_series.py::KNOWN_INVALID`. The 2020 NBA bubble
  lists home and road teams on a neutral floor.
- **Sources of truth:** stats.nba.com box scores. Basketball-Reference is
  the independent check for series lengths when one is needed.
- **Suspicious results:** a perfect score, a total of zero, or an impossibly
  large sum means stop and check before reporting.

Data sources, licenses, and retrieval dates: see `DATA_SOURCES.md`. NBA.com
terms allow private, non-commercial use; keep this repo private until
Chester decides how a public page fits those terms.

## Commands

```
../.venv/bin/python python/01_harvest.py         # ~10 min, resumable, skips files on disk
../.venv/bin/python python/02_build_series.py    # data/team_games.csv and the checks
./run_checks.sh                                  # every check; non-zero on failure
```

The interpreter is the family venv (`~/repos/basketball-data-science/.venv`);
`requirements.txt` pins the packages this repo imports from it.

## How work is done here

- **Pre-specification holds.** The question 1 analysis in
  `docs/design.md` is fixed before any outcome is computed. Changing the
  metric, sample, or baseline after that needs a dated amendment there.
- **Plan mode first** for any step that drops or filters rows, deletes or
  overwrites files, joins tables, or changes a metric definition.
- `data/raw/` holds files exactly as downloaded and is never edited.
- Family conventions: polars and plotly; deterministic methods only (the R
  twin must reconcile with Python); no number typed into prose by hand
  (generator-owned README regions, `verify_numbers.py` once registered).
- Every gate gets shown to fail on a real or injected case before it is
  trusted, and its skip paths are loud.
- Label anything not checked against the data as unverified.
