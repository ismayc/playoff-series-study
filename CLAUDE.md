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
terms allow "legitimate news reporting or private, non-commercial purposes"
and bar a public database of comprehensive statistics without consent. So
the repo is public with summaries only (decided by Chester, October 18,
2026): per-series and per-game outputs, `data/`, and the review page build
are gitignored and must stay that way. Never commit a file that lists box
scores game by game or series by series. The review page is local only.

## Commands

```
../.venv/bin/python python/01_harvest.py         # ~10 min, resumable, skips files on disk
../.venv/bin/python python/02_build_series.py    # data/team_games.csv and the checks
../.venv/bin/python python/03_game1.py           # question 1 (Python) -> output/game1_*.csv
Rscript R/03_game1.R                             # question 1 (R twin) -> output/r/
../.venv/bin/python python/06_profiles.py        # question 4 (Python) -> output/profile_*.csv
Rscript R/06_profiles.R                          # question 4 (R twin) -> output/r/
../.venv/bin/python python/08_stakes_rest.py     # question 3 (Python); fails if stage != encoded round
Rscript R/08_stakes_rest.R                       # question 3 (R twin) -> output/r/
../.venv/bin/python python/11_followups.py       # follow-ups 5-7 (Python); reads 06's profile_games.csv
Rscript R/11_followups.R                         # follow-ups 5-7 (R twin) -> output/r/
../.venv/bin/python python/10_harvest_officials.py  # follow-up 8 officials, ~2 h, resumable
../.venv/bin/python python/12_officials.py       # follow-up 8 (Python); flattens data/game_officials.csv first
Rscript R/12_officials.R                         # follow-up 8 (R twin) -> output/r/
../.venv/bin/python python/13_harvest_players.py  # follow-up 9 player playoff logs, resumable
../.venv/bin/python python/14_experience.py      # follow-up 9 (Python); flattens data/player_games.csv first
Rscript R/14_experience.R                        # follow-up 9 (R twin) -> output/r/
../.venv/bin/python python/04_reconcile.py       # every cell must agree within 1e-9
../.venv/bin/python python/05_findings.py        # README regions; --check is the drift gate
../.venv/bin/python python/07_review.py          # review page -> review/build/ (gitignored)
(cd review/build && python3 -m http.server 8766) # view at http://localhost:8766/
./run_checks.sh                                  # all of the above except 01; non-zero on failure
```

Family page (public, summaries only): `docs/story.md` plus
`python/09_story_figures.py` (figures from the committed summary tables),
built by `report_builder.build_study('playoff-series-study')` in
basketball-analysis-tools into `docs/index.html`. Registered in that repo's
`glossary.py`, `verify_numbers.py`, and the hub's `NEW_CARDS`. Regen order
after any output change: 05, then `glossary.py --sync`, then 09, then
`report_builder.py --all`, then the family gates (`verify_numbers.py
--check`, `glossary.py --check`, `check_family_brand.py`, tools pytest).

Every number in `docs/story.md` is bound to one committed cell in
basketball-analysis-tools `number_bindings/playoff-series-study__docs_story.md.json`
(since October 18, 2026). `verify_numbers.py --check` fails on a number whose
cell no longer displays the same, and on any new number with no binding.
After adding or moving a story number, run `verify_numbers.py --propose
playoff-series-study docs/story.md`, settle the open items in the
`.proposals.json` it writes, and commit the bindings with the story.

After any change to outputs: 03, 06, 08, 11, 12, and 14 with their R twins, 04, then 05 (without `--check`).
`LEAGUE` is written as the integers 0 and 10; R reads it with `col_integer()`
(as text "00", `"00" == 0` is FALSE in R, which once gave NBA games the
WNBA's 40-minute pace).

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
