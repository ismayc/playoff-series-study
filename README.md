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
| Free-throw rate (FTA / FGA, x100) | **-2.23** | **+0.65** | **+0.73** | **+1.10** | +0.29 | -0.63 | -0.62 |
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
| Free-throw rate (FTA / FGA, x100) | **-2.20** | **+1.78** | -0.05 | +0.55 | +0.56 | -0.30 | -0.62 |
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
| Free-throw rate (FTA / FGA, x100) | **-1.80** | **+1.64** | -0.35 | +1.63 | +1.24 |
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
| Free-throw rate (FTA / FGA, x100) | -1.26 | +1.00 | -0.18 | +1.18 | +1.24 |
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
- **Officiating, from fouls.** Fewer fouls in a game can mean fewer called
  or fewer committed; box scores cannot tell the two apart.
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
