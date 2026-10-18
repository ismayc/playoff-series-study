# Playoff series study

Is Game 1 three-point shooting worse than the rest of a playoff series?
Every NBA and WNBA postseason with complete three-point records, rebuilt
series by series from stats.nba.com box scores. The analysis was fixed in
[`docs/design.md`](docs/design.md) before any Game 1 number was computed;
its two amendments were made before any outcome was looked at, and both
are recorded there with dates and reasons.

Private, personal research in the basketball-data-science family. Data:
NBA.com.

## Question 1: the Game 1 three-point dip

<!-- gen:headline -->
| League | Series | Game 1 minus Games 2+ | Game 1 minus Game 2 |
|---|---|---|---|
| NBA | 630 | -0.03 (-0.87 to +0.82) | -0.32 (-1.36 to +0.73) |
| WNBA | 170 | +0.26 (-1.14 to +1.67) | +0.64 (-0.87 to +2.14) |

Three-point percentage, both teams pooled within each series; mean over series in percentage points with a 95% interval.

**Verdict.** NBA: no Game 1 dip; both intervals include zero. WNBA: no Game 1 dip; both intervals include zero.
<!-- /gen:headline -->

The selection-free column matters because Games 6 and 7 exist only in
close series. A dip claimed on one comparison but not the other would not
count.

### Attempts, not just accuracy

The secondary outcome: the share of a team's shots taken from three. A
lower Game 1 volume at unchanged accuracy is a different finding from a
cold Game 1.

<!-- gen:rate -->
| League | Game 1 minus Games 2+ | Game 1 minus Game 2 |
|---|---|---|
| NBA | -1.32 (-1.61 to -1.03) | -1.02 (-1.37 to -0.67) |
| WNBA | -0.33 (-0.99 to +0.34) | -0.33 (-1.09 to +0.42) |

Three-point attempt rate (3PA / FGA), percentage points of field-goal attempts.

**Reading.** NBA: a smaller share of shots from three in Game 1, on both comparisons. WNBA: no Game 1 difference in volume that holds on both comparisons.

NBA by decade, Game 1 minus Games 2+:

| Decade | Series | Attempt rate | Accuracy |
|---|---|---|---|
| 1980s | 75 | -0.64 (-1.15 to -0.13) | -1.16 (-5.09 to +2.76) |
| 1990s | 150 | -1.43 (-2.00 to -0.87) | +0.00 (-1.96 to +1.97) |
| 2000s | 150 | -1.79 (-2.35 to -1.23) | -0.46 (-2.00 to +1.07) |
| 2010s | 150 | -1.79 (-2.44 to -1.15) | +0.82 (-0.53 to +2.16) |
| 2020s | 105 | -0.30 (-1.14 to +0.54) | +0.15 (-1.08 to +1.37) |
<!-- /gen:rate -->

Exploratory, not the pre-specified test. Why volume moves is not settled
here: adjustment between games, more trailing (and so more threes) in
later games, or both. Question 4's per-game profiles are where that gets
looked at.

### Against the regular-season baseline

<!-- gen:baseline -->
| League | Game 1 minus expected | Games 2+ minus expected | Series with a baseline |
|---|---|---|---|
| NBA | -0.45 (-1.16 to +0.27) | -0.60 (-0.99 to -0.21) | 615 of 630 |
| WNBA | +0.73 (-0.51 to +1.97) | +0.52 (-0.46 to +1.50) | 170 of 170 |

Expected 3P% is the team's regular-season 3P% plus its opponent's 3P% allowed minus the league's.

| League | Game 1 at | Team-series | Own Game 1 minus own Games 2+ | Game 1 minus expected |
|---|---|---|---|---|
| NBA | home | 614 | -0.79 (-2.15 to +0.57) | -1.09 (-2.19 to +0.02) |
| NBA | road | 615 | -0.12 (-1.34 to +1.09) | -0.71 (-1.80 to +0.38) |
| WNBA | home | 167 | +0.68 (-1.54 to +2.90) | +0.55 (-1.25 to +2.35) |
| WNBA | road | 167 | -0.67 (-2.90 to +1.57) | +0.58 (-1.31 to +2.48) |
<!-- /gen:baseline -->

Game 1 is at the higher seed's floor. The 2020 seasons were played at
neutral sites and are left out of the home and road rows only.

### Every three, pooled

<!-- gen:pooled -->
| League | Game 1 3P% | Games 2+ 3P% | Difference |
|---|---|---|---|
| NBA | 35.11 | 34.83 | +0.28 |
| WNBA | 34.79 | 34.40 | +0.39 |

Every three-pointer in every Game 1 against every one after it, no intervals.
<!-- /gen:pooled -->

## What this design cannot claim

- **Causes.** A difference between Game 1 and later games mixes rest, scouting
  adjustment, officiating, and game script; this compares, it does not
  separate them.
- **Before 1984-85 in the NBA.** Three-point attempts are missing from most
  box scores before then (`output/coverage.csv`).
- **The 2026 WNBA Finals,** in progress at harvest and excluded until it
  ends.

## How to run

```
../.venv/bin/python python/01_harvest.py      # network, resumable
./run_checks.sh                               # everything else, with every gate
```

`run_checks.sh` runs the Python and R unit tests, the series build and its
checks, both implementations of the analysis, the reconcile gate (every
output cell must agree between Python and R), and the README drift check.
Each gate was shown to fail on a real or injected error before it was
trusted (`docs/design.md`).
