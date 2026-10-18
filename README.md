# Playoff series study

Is Game 1 three-point shooting worse than the rest of a playoff series?
Every NBA and WNBA postseason with complete three-point records, rebuilt
series by series from stats.nba.com box scores. The analysis was fixed in
[`docs/design.md`](docs/design.md) before any Game 1 number was computed;
its two amendments were made before any outcome was looked at, and both
are recorded there with dates and reasons.

Personal research in the basketball-data-science family. Data: NBA.com.

<!-- terms -->
> **Terms used in this analysis.** Dotted-underlined terms anywhere below repeat these definitions on hover ([full glossary](https://github.com/ismayc/basketball-data-science/blob/main/docs/glossary.md)).
>
> - **FGA**: Field-goal attempts.
<!-- /terms -->

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

Three-point attempt rate (3PA / <abbr title="Field-goal attempts.">FGA</abbr>), percentage points of field-goal attempts.

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

Exploratory, not the pre-specified test. Question 4 below follows the
attempt rate through every game of the series and tests one explanation
for it.

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

## Question 3: stakes and layoffs

Exploratory. Stage is distance from the Finals, read from each winner's
path, so formats with byes and single-game rounds line up; it matches the
round encoded in every game ID that has one. Every outcome is a
within-series difference, so team strength cancels without a rating
adjustment.

### By stage

<!-- gen:stakes -->
| League | Stage | Series | 3P%: Game 1 minus Games 2+ | 3P%: Game 1 minus Game 2 | Attempt rate: Game 1 minus Games 2+ |
|---|---|---|---|---|---|
| NBA | Finals | 42 | +0.23 (-2.79 to +3.24) | -1.80 (-5.54 to +1.94) | -1.65 (-2.94 to -0.37) |
| NBA | 1 round before the Finals | 84 | +0.26 (-1.92 to +2.44) | +0.60 (-1.89 to +3.09) | -1.56 (-2.28 to -0.84) |
| NBA | 2 rounds before the Finals | 168 | -0.80 (-2.35 to +0.75) | -2.15 (-4.09 to -0.20) | -0.55 (-1.16 to +0.06) |
| NBA | 3 rounds before the Finals | 336 | +0.25 (-0.96 to +1.46) | +0.56 (-0.95 to +2.06) | -1.60 (-1.98 to -1.23) |
| WNBA | Finals | 28 | -1.52 (-5.67 to +2.64) | +0.20 (-4.28 to +4.68) | +0.77 (-0.83 to +2.38) |
| WNBA | 1 round before the Finals | 56 | +0.35 (-1.84 to +2.54) | +0.71 (-1.53 to +2.94) | -0.67 (-1.78 to +0.45) |
| WNBA | 2 rounds before the Finals | 80 | +0.76 (-1.33 to +2.85) | +0.91 (-1.39 to +3.22) | -0.44 (-1.39 to +0.50) |

**Reading.** No stage in either league shows a Game 1 accuracy gap that holds on both comparisons. NBA: the attempt-rate gap excludes zero at 3 of 4 stages (Finals, 1 round before the Finals, 3 rounds before the Finals). WNBA: the attempt-rate gap excludes zero at 0 of 3 stages.
<!-- /gen:stakes -->

### By rest gap

The two teams in a Game 1 often arrive with different rest: one swept its
last series, the other went seven. Each team is measured against its own
later games in the same series, then the more-rested team is compared with
the less-rested one.

<!-- gen:rest -->
| League | Rest gap | Series | 3P% contrast | Attempt-rate contrast |
|---|---|---|---|---|
| NBA | 1-2 days | 184 | -2.69 (-6.31 to +0.92) | -0.68 (-1.86 to +0.49) |
| NBA | 3-5 days | 131 | -2.86 (-6.39 to +0.68) | -0.32 (-1.68 to +1.03) |
| NBA | 6+ days | 22 | +1.40 (-4.35 to +7.15) | -2.98 (-6.30 to +0.34) |
| NBA | any gap | 337 | -2.49 (-4.92 to -0.06) | -0.69 (-1.55 to +0.16) |
| WNBA | 1-2 days | 72 | -2.64 (-7.32 to +2.04) | -0.60 (-3.00 to +1.80) |
| WNBA | 3-5 days | 17 | -0.11 (-11.71 to +11.49) | -0.44 (-5.56 to +4.68) |
| WNBA | 6+ days | 8 | +1.59 (-11.85 to +15.03) | -5.08 (-11.11 to +0.96) |
| WNBA | any gap | 97 | -1.85 (-5.98 to +2.29) | -0.94 (-2.99 to +1.11) |

Each contrast is the more-rested team's own Game 1 minus own Games 2+, minus the same for the less-rested team, in percentage points.

**Reading.** NBA: across every nonzero gap the more-rested team's Game 1 three-point shooting is relatively worse, but no single gap bin excludes zero, so it is a hint, not a finding (293 series with no gap left out). WNBA: no rest-gap difference in Game 1 three-point shooting (73 series with no gap left out).
<!-- /gen:rest -->

## Question 4: how the box score moves through a series

Exploratory: estimates and intervals, no significance claims. Every rate
is measured against the same team's average over the same series, so
team strength cancels, and the game is the unit. Overtime is removed from
pace, and every count is a rate per possession or per attempt. The
full-length tables hold only series that went the distance, so a trend
there is not a change in which series are present.

<!-- gen:profiles -->
**NBA, every series.**

| Rate, deviation from the series mean | G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|---|
| Games | 630 | 630 | 630 | 583 | 448 | 266 | 109 |
| Fouls per 100 possessions | **-1.05** | +0.20 | **+0.38** | **+0.64** | +0.06 | **-0.43** | +0.06 |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | **-2.23** | **+0.65** | **+0.73** | **+1.10** | +0.29 | -0.63 | -0.62 |
| Turnovers per 100 possessions | -0.04 | +0.10 | +0.12 | +0.09 | -0.10 | -0.08 | **-0.91** |
| Pace (possessions per regulation game) | **+0.60** | +0.18 | -0.17 | -0.09 | -0.09 | -0.42 | **-1.68** |
| Points per 100 possessions | -0.53 | +0.48 | +0.06 | -0.25 | +0.43 | -0.24 | +0.09 |
| Offensive rebound % (x100) | -0.14 | -0.00 | +0.19 | -0.11 | +0.05 | +0.10 | -0.15 |
| Assists per made field goal (x100) | +0.03 | +0.20 | -0.22 | -0.13 | +0.29 | -0.21 | -0.04 |
| Three-point attempt rate (x100) | **-1.07** | -0.06 | +0.22 | **+0.27** | **+0.36** | **+0.53** | **+1.01** |
| Three-point % (x100) | -0.26 | +0.57 | +0.04 | -0.10 | -0.16 | +0.05 | -0.38 |

**NBA, full-length series only** (same series in every column).

| Rate, deviation from the series mean | G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|---|
| Games | 155 | 155 | 155 | 155 | 155 | 109 | 109 |
| Fouls per 100 possessions | **-1.15** | **+0.48** | +0.27 | **+0.63** | +0.11 | **-0.55** | +0.06 |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | **-2.20** | **+1.78** | -0.05 | +0.55 | +0.56 | -0.30 | -0.62 |
| Turnovers per 100 possessions | +0.16 | +0.32 | +0.16 | +0.15 | -0.22 | +0.11 | **-0.91** |
| Pace (possessions per regulation game) | **+1.30** | +0.45 | -0.33 | -0.15 | -0.26 | +0.25 | **-1.68** |
| Points per 100 possessions | -0.79 | **+1.24** | +0.11 | -0.50 | +0.91 | **-1.45** | +0.09 |
| Offensive rebound % (x100) | -0.61 | +0.10 | +0.58 | +0.10 | +0.28 | -0.51 | -0.15 |
| Assists per made field goal (x100) | -0.43 | +0.01 | +0.54 | +0.24 | +0.29 | -0.87 | -0.04 |
| Three-point attempt rate (x100) | **-1.35** | -0.05 | -0.07 | +0.15 | +0.41 | +0.29 | **+1.01** |
| Three-point % (x100) | -0.27 | +1.05 | -0.31 | -0.28 | +0.21 | -0.06 | -0.38 |

**WNBA, every series.**

| Rate, deviation from the series mean | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|
| Games | 170 | 170 | 109 | 28 | 15 |
| Fouls per 100 possessions | **-1.00** | **+0.63** | +0.33 | +0.66 | +0.69 |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | **-1.80** | **+1.64** | -0.35 | +1.63 | +1.24 |
| Turnovers per 100 possessions | -0.10 | +0.31 | -0.42 | +0.01 | +0.61 |
| Pace (possessions per regulation game) | +0.08 | +0.31 | **-0.64** | +0.65 | -0.97 |
| Points per 100 possessions | -0.30 | +0.24 | +0.27 | -0.40 | -0.52 |
| Offensive rebound % (x100) | -0.42 | +0.49 | +0.16 | -1.94 | +1.59 |
| Assists per made field goal (x100) | -0.48 | +0.29 | +0.18 | -1.02 | +2.68 |
| Three-point attempt rate (x100) | -0.16 | +0.17 | -0.05 | -0.13 | +0.52 |
| Three-point % (x100) | +0.01 | -0.61 | +0.34 | **+3.14** | -1.52 |

**WNBA, full-length series only** (same series in every column).

| Rate, deviation from the series mean | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|
| Games | 81 | 81 | 81 | 15 | 15 |
| Fouls per 100 possessions | **-0.78** | +0.15 | +0.44 | +0.35 | +0.69 |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | -1.26 | +1.00 | -0.18 | +1.18 | +1.24 |
| Turnovers per 100 possessions | +0.04 | +0.45 | **-0.61** | +0.01 | +0.61 |
| Pace (possessions per regulation game) | +0.24 | +0.48 | **-0.58** | +0.26 | -0.97 |
| Points per 100 possessions | -0.37 | -0.48 | +0.84 | +0.55 | -0.52 |
| Offensive rebound % (x100) | -0.02 | +0.06 | +0.13 | -2.50 | +1.59 |
| Assists per made field goal (x100) | +0.19 | +0.16 | -0.44 | -2.21 | +2.68 |
| Three-point attempt rate (x100) | +0.07 | -0.21 | +0.03 | +0.11 | +0.52 |
| Three-point % (x100) | -0.35 | -0.14 | +0.15 | +3.39 | -1.52 |

Bold: the 95% interval excludes zero. Each cell is the mean over games of the two teams' deviations from their own series means.
<!-- /gen:profiles -->

### Does falling behind in a series bring more threes?

One explanation for rising three-point volume is that the team behind in
the series shoots its way back. This compares the two teams in the same
game, from Game 2 on, whenever one leads the series.

<!-- gen:state -->
| League | Games with a series leader | Trailing minus leading team | Tied games left out |
|---|---|---|---|
| NBA | 2077 | -1.07 (-1.35 to -0.80) | 589 |
| WNBA | 220 | -2.34 (-3.24 to -1.44) | 102 |

Three-point attempt rate, each team relative to its own series mean, percentage points.

**Reading.** NBA: the team behind in the series takes relatively fewer threes than the leader. WNBA: the team behind in the series takes relatively fewer threes than the leader.
<!-- /gen:state -->

## What this design cannot claim

- **Causes.** A difference between Game 1 and later games mixes rest, scouting
  adjustment, officiating, and game script; this compares, it does not
  separate them.
- **Intent, from series state.** A team trails a series because it lost
  games, so trailing and leading teams differ in recent results as well as
  in what is at stake. The comparison sorts teams by series position; it
  does not show that trailing teams choose to shoot fewer threes.
- **Rust, from the rest gap.** The more-rested team usually won its last
  series faster, so rest arrives together with recent form and with
  whatever let it finish early.
- **Officiating, from fouls.** Fewer fouls in a game can mean fewer called
  or fewer committed; box scores cannot tell the two apart.
- **Before 1984-85 in the NBA.** Three-point attempts are missing from most
  box scores before then (`output/coverage.csv`).
- **The 2026 WNBA Finals,** in progress at harvest and excluded until it
  ends.

## Question 2: the review page

`review/` holds a local page with three views: every series game by game
(three-point percentage and share of shots from three for both teams, plus
fouls, free throws, turnovers, and pace), each franchise's Game 1 against
the rest of its series over time, and the question 4 profiles by game
number. It is descriptive; the estimates above are the analysis. Build it
with `python/07_review.py` and serve `review/build/` over HTTP. Its data
lists NBA.com box scores game by game, so the build stays local and is not
published; this repository commits only summary tables (see
`DATA_SOURCES.md`). For the same reason a fresh clone runs the tests and
the README drift check but cannot rebuild the analysis until `01_harvest.py`
has fetched the game logs.

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
