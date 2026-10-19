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

### Across eras

Exploratory, not part of the pre-specified test. The first table splits
the Game 1 gap by decade for both leagues. The second follows the level of
three-point shooting itself, Game 1 against later games, so the gap can be
read against how much the game changed around it.

<!-- gen:eras -->
| League | Decade | Series | Accuracy | Attempt rate |
|---|---|---|---|---|
| NBA | 1980s | 75 | -1.16 (-5.09 to +2.76) | -0.64 (-1.15 to -0.13) |
| NBA | 1990s | 150 | +0.00 (-1.96 to +1.97) | -1.43 (-2.00 to -0.87) |
| NBA | 2000s | 150 | -0.46 (-2.00 to +1.07) | -1.79 (-2.35 to -1.23) |
| NBA | 2010s | 150 | +0.82 (-0.53 to +2.16) | -1.79 (-2.44 to -1.15) |
| NBA | 2020s | 105 | +0.15 (-1.08 to +1.37) | -0.30 (-1.14 to +0.54) |
| WNBA | 1990s | 6 | -6.55 (-10.99 to -2.10) | +2.14 (+0.20 to +4.08) |
| WNBA | 2000s | 70 | +0.55 (-1.63 to +2.73) | -0.27 (-1.28 to +0.75) |
| WNBA | 2010s | 54 | +1.13 (-1.70 to +3.95) | -0.94 (-1.97 to +0.09) |
| WNBA | 2020s | 40 | -0.38 (-2.80 to +2.04) | +0.02 (-1.65 to +1.70) |

Game 1 minus Games 2+, mean over series in percentage points with a 95% interval.

| League | Decade | Seasons | Game 1 3P% | Games 2+ 3P% | Game 1 3PA rate | Games 2+ 3PA rate | Seasons with a lower Game 1 rate |
|---|---|---|---|---|---|---|---|
| NBA | 1980s | 5 | 31.0 | 30.7 | 6.2 | 6.8 | 5 of 5 |
| NBA | 1990s | 10 | 34.7 | 34.4 | 15.3 | 16.7 | 10 of 10 |
| NBA | 2000s | 10 | 34.6 | 35.0 | 20.0 | 22.0 | 10 of 10 |
| NBA | 2010s | 10 | 35.7 | 34.7 | 28.1 | 29.8 | 10 of 10 |
| NBA | 2020s | 7 | 35.6 | 35.4 | 40.3 | 40.6 | 5 of 7 |
| WNBA | 1990s | 2 | 27.1 | 34.1 | 25.0 | 22.6 | 0 of 2 |
| WNBA | 2000s | 10 | 35.3 | 34.7 | 23.6 | 24.0 | 7 of 10 |
| WNBA | 2010s | 10 | 34.8 | 33.5 | 22.6 | 23.9 | 6 of 10 |
| WNBA | 2020s | 7 | 35.0 | 34.9 | 33.3 | 32.4 | 4 of 7 |

Every three in the decade's series pooled, so a season with more threes counts for more.

**Reading.** NBA: the longest unbroken run of seasons with a lower Game 1 attempt rate is 1985 to 2020. WNBA: the longest unbroken run of seasons with a lower Game 1 attempt rate is 2007 to 2011.
<!-- /gen:eras -->

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

## Follow-ups

Four parts of the original idea that questions 1 to 4 left out, each
defined in [`docs/design.md`](docs/design.md) before it was computed.
Exploratory: estimates and intervals, no significance claims.

### 5. Does the Game 1 three-point winner win the series?

The team that shoots better from three in Game 1 usually wins Game 1, and
Game 1 winners usually win the series. So the question is asked with the
Game 1 result held fixed: among Game 1 winners, do the ones that also
outshot their opponent from three win the series more often?

<!-- gen:outshoot -->
| League | Series | Better Game 1 three-point shooter wins the series | Game 1 winner wins the series: it also outshot | it was outshot | Difference |
|---|---|---|---|---|---|
| NBA | 614 | 59.8% (55.9 to 63.7) | 76.7% (72.6 to 80.7), 420 series | 76.8% (70.9 to 82.7), 194 series | -0.1 (-7.3 to +7.0) |
| WNBA | 167 | 61.1% (53.7 to 68.5) | 75.0% (67.0 to 83.0), 112 series | 67.3% (54.9 to 79.7), 55 series | +7.7 (-7.0 to +22.5) |

Shares of series in percent with a 95% interval; the difference is in percentage points. Series with equal Game 1 three-point percentages, or a team with no Game 1 attempts, are left out (NBA 16, WNBA 3).

**Reading.** NBA: with the Game 1 result held fixed, outshooting the opponent from three adds nothing that the interval can tell from zero. WNBA: with the Game 1 result held fixed, outshooting the opponent from three adds nothing that the interval can tell from zero.
<!-- /gen:outshoot -->

### 6. Format breaks: the 2020 single-site playoffs and series length

Both 2020 postseasons were played at one site with no crowd. Series
length is confounded with round and era (short series are early rounds,
and the NBA's best-of-5 first rounds ended in 2002), so the length rows
are description.

<!-- gen:breaks -->
| League | Split | Series | 3P%: Game 1 minus Games 2+ | Attempt rate: Game 1 minus Games 2+ | Game 1 fouls per 100 possessions | Game 1 free-throw rate (x100) |
|---|---|---|---|---|---|---|
| NBA | 2020 (single site) | 15 | +0.54 (-2.13 to +3.21) | -0.14 (-1.84 to +1.56) | +0.63 (-0.35 to +1.61) | -0.11 (-1.95 to +1.72) |
| NBA | every other season | 615 | -0.04 (-0.91 to +0.82) | -1.35 (-1.64 to -1.05) | -1.09 (-1.31 to -0.86) | -2.28 (-2.80 to -1.76) |
| NBA | best-of-5 | 144 | +0.36 (-1.98 to +2.71) | -1.61 (-2.10 to -1.12) | -0.88 (-1.32 to -0.44) | -2.59 (-3.68 to -1.50) |
| NBA | best-of-7 | 486 | -0.15 (-0.99 to +0.70) | -1.23 (-1.58 to -0.89) | -1.10 (-1.36 to -0.84) | -2.12 (-2.70 to -1.54) |
| WNBA | 2020 (single site) | 3 | +5.92 (-0.86 to +12.69) | +3.21 (+0.84 to +5.58) | -1.32 (-2.11 to -0.54) | -0.40 (-4.28 to +3.48) |
| WNBA | every other season | 167 | +0.16 (-1.26 to +1.59) | -0.39 (-1.07 to +0.28) | -1.00 (-1.41 to -0.59) | -1.82 (-2.79 to -0.86) |
| WNBA | best-of-3 | 127 | +0.45 (-1.15 to +2.05) | -0.61 (-1.36 to +0.14) | -0.90 (-1.34 to -0.47) | -1.43 (-2.50 to -0.36) |
| WNBA | best-of-5 | 42 | -0.40 (-3.40 to +2.59) | +0.25 (-1.10 to +1.60) | -1.24 (-2.21 to -0.27) | -2.76 (-4.81 to -0.72) |
| WNBA | best-of-7 | 1 | +4.78 (one series) | +10.88 (one series) | -3.92 (one series) | -7.73 (one series) |

Percentage points except fouls (per 100 possessions); the foul and free-throw columns are Game 1's deviation from the series mean, as in question 4. Mean over series with a 95% interval.

**Reading.** NBA: the Game 1 foul dip holds in other seasons; in 2020 it is absent (the interval includes zero), from 15 series. WNBA: the Game 1 foul dip holds in other seasons; there are too few 2020 series (3) to say whether it held there.
<!-- /gen:breaks -->

### 7. Question 4 by decade

<!-- gen:decades -->
**NBA, Game 1 deviation from the series mean, by decade.**

| Rate | 1980s | 1990s | 2000s | 2010s | 2020s |
|---|---|---|---|---|---|
| Series | 75 | 150 | 150 | 150 | 105 |
| Fouls per 100 possessions | **-1.53** | **-1.30** | **-1.13** | **-0.64** | **-0.81** |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | **-3.81** | **-2.89** | **-2.34** | -0.99 | **-1.77** |
| Turnovers per 100 possessions | +0.13 | -0.05 | -0.05 | +0.00 | -0.20 |
| Pace (possessions per regulation game) | **+0.86** | **+0.71** | +0.49 | **+0.64** | +0.35 |
| Points per 100 possessions | -0.27 | -0.79 | -1.10 | -0.16 | -0.04 |
| Offensive rebound % (x100) | -0.59 | -0.18 | +0.17 | -0.31 | +0.06 |
| Assists per made field goal (x100) | **+1.76** | +0.35 | -0.82 | +0.21 | -0.72 |
| Three-point attempt rate (x100) | **-0.49** | **-1.12** | **-1.40** | **-1.54** | -0.26 |
| Three-point % (x100) | -1.42 | -0.93 | -0.42 | +0.86 | +0.13 |

**WNBA, Game 1 deviation from the series mean, by decade.**

| Rate | 1990s | 2000s | 2010s | 2020s |
|---|---|---|---|---|
| Series | 6 | 70 | 54 | 40 |
| Fouls per 100 possessions | -0.97 | **-0.89** | **-0.91** | **-1.34** |
| Free-throw rate (FTA / <abbr title="Field-goal attempts.">FGA</abbr>, x100) | -1.18 | **-1.71** | **-1.94** | **-1.85** |
| Turnovers per 100 possessions | +0.13 | -0.12 | +0.00 | -0.21 |
| Pace (possessions per regulation game) | +0.60 | -0.26 | +0.25 | +0.37 |
| Points per 100 possessions | +0.41 | +0.47 | -0.59 | -1.36 |
| Offensive rebound % (x100) | -0.63 | -0.31 | -0.17 | -0.89 |
| Assists per made field goal (x100) | +3.08 | -0.86 | +0.31 | -1.42 |
| Three-point attempt rate (x100) | **+1.30** | -0.20 | -0.52 | +0.18 |
| Three-point % (x100) | **-4.19** | +0.30 | +0.30 | -0.27 |

**NBA three-point attempt rate (x100) by game number and decade.**

| Decade | G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|---|
| 1980s | **-0.49** | +0.36 | -0.25 | +0.20 | +0.47 | -0.77 | **+1.60** |
| 1990s | **-1.12** | +0.23 | +0.16 | +0.10 | +0.39 | **+1.03** | **+1.28** |
| 2000s | **-1.40** | -0.06 | +0.08 | **+0.62** | +0.09 | **+1.29** | +0.43 |
| 2010s | **-1.54** | **-0.67** | **+0.69** | +0.49 | **+0.71** | +0.21 | **+1.67** |
| 2020s | -0.26 | +0.11 | +0.15 | -0.29 | +0.16 | +0.08 | +0.45 |

Bold: the 95% interval excludes zero.

**Reading.** NBA: Game 1 differs from the series mean in every decade for fouls per 100 possessions. WNBA: no rate differs from the series mean in every decade (the 1990s holds fewer than 10 series).
<!-- /gen:decades -->

### 8. Fouls and the officials

Question 4 found fewer fouls in Game 1. Two explanations involve the
officials: the league could send lighter-whistled crews to Game 1s, or the
same officials could call Game 1s more loosely. The officials for each game
come from the stats API, which lists them only for recent seasons. Box
scores cannot tell fouls called from fouls committed, so neither result
says which side changed.

<!-- gen:officials -->
| League | Seasons | Games with a crew of three | Game 1 fouls per 100 possessions | Game 1 crew tendency | Same official: Game 1 minus later games | Officials agree with themselves (even vs odd seasons) |
|---|---|---|---|---|---|---|
| NBA | 2001 to 2026 | 1576 of 2156 | -0.85 (-1.18 to -0.53) | +0.00 (-0.03 to +0.04), 240 series | -1.06 (-1.38 to -0.74), 56 officials | r = +0.49 (+0.24 to +0.67), 51 officials |
| WNBA | 2004 to 2026 | 280 of 424 | -0.94 (-1.47 to -0.42) | +0.01 (-0.05 to +0.07), 90 series | -1.33 (-1.71 to -0.96), 24 officials | r = +0.41 (-0.13 to +0.76), 15 officials |

Seasons are the years the seasons end. Fouls per 100 possessions as deviations from the series mean (question 4); the crew tendency is the mean, over a game's officials, of how far above or below the league each runs in other series, as a deviation from the series' average crew. Means with 95% intervals; the split-half correlation has a Fisher interval. Seasons where fewer than half the games list exactly three officials (from 2016-17 most games list four, with no field saying which three worked): NBA 2001, NBA 2003, NBA 2018, NBA 2019, NBA 2024, NBA 2025, NBA 2026, WNBA 2003, WNBA 2018, WNBA 2019, WNBA 2020, WNBA 2021, WNBA 2022, WNBA 2024, WNBA 2025, WNBA 2026.

**Reading.** NBA: Game 1 crews are no lighter-whistled than the series' other crews (the interval includes zero); the same officials call fewer fouls in Game 1 than in later games; officials differ: one who calls more fouls than usual in even seasons does so in odd seasons too. WNBA: Game 1 crews are no lighter-whistled than the series' other crews (the interval includes zero); the same officials call fewer fouls in Game 1 than in later games; no sign that officials differ beyond chance.
<!-- /gen:officials -->

### 9. Experienced against inexperienced teams

Does the less experienced team have a different Game 1? Experience is
measured two ways: the roster's career playoff games before that
postseason, weighted by each player's minutes in the series (the
headline), and the franchise's playoff games in the three previous
postseasons (the check). As with the rest gap, each team is measured
against its own later games, then the more experienced team is compared
with the less experienced one.

<!-- gen:experience -->
| League | Measure | Experience gap (games) | Series | 3P% contrast | Attempt-rate contrast | Fouls per 100 contrast |
|---|---|---|---|---|---|---|
| NBA | Roster (minutes-weighted career playoff games) | up to 14.1 | 209 | -0.95 (-4.45 to +2.54) | +0.78 (-0.21 to +1.78) | -0.00 (-0.72 to +0.71) |
| NBA |  | 14.1 to 34.0 | 210 | +2.57 (-0.02 to +5.15) | +0.63 (-0.55 to +1.80) | -0.62 (-1.32 to +0.08) |
| NBA |  | over 34.0 | 210 | -1.09 (-4.43 to +2.25) | -1.07 (-2.05 to -0.08) | -0.66 (-1.44 to +0.13) |
| NBA |  | any gap | 629 | +0.18 (-1.65 to +2.00) | +0.11 (-0.50 to +0.73) | -0.43 (-0.85 to -0.00) |
| NBA | Franchise (playoff games in the three previous postseasons) | up to 11.0 | 207 | +0.76 (-2.70 to +4.21) | +0.13 (-0.94 to +1.19) | -0.01 (-0.77 to +0.75) |
| NBA |  | 11.0 to 26.0 | 214 | -0.65 (-3.59 to +2.30) | -0.08 (-1.19 to +1.04) | -0.49 (-1.22 to +0.25) |
| NBA |  | over 26.0 | 195 | +1.27 (-1.99 to +4.54) | -0.50 (-1.52 to +0.53) | -1.19 (-1.93 to -0.45) |
| NBA |  | any gap | 616 | +0.43 (-1.43 to +2.29) | -0.14 (-0.76 to +0.48) | -0.55 (-0.98 to -0.12) |
| WNBA | Roster (minutes-weighted career playoff games) | up to 4.7 | 57 | +2.96 (-2.94 to +8.86) | -0.17 (-2.81 to +2.47) | +0.69 (-1.85 to +3.24) |
| WNBA |  | 4.7 to 11.1 | 56 | -1.18 (-7.15 to +4.80) | +1.98 (-1.02 to +4.98) | -0.40 (-2.59 to +1.80) |
| WNBA |  | over 11.1 | 57 | +3.16 (-2.36 to +8.68) | +1.64 (-0.97 to +4.25) | +2.65 (+1.08 to +4.22) |
| WNBA |  | any gap | 170 | +1.66 (-1.68 to +5.01) | +1.15 (-0.44 to +2.73) | +0.99 (-0.25 to +2.23) |
| WNBA | Franchise (playoff games in the three previous postseasons) | up to 5.0 | 56 | +2.01 (-4.58 to +8.59) | -0.83 (-3.64 to +1.98) | +0.09 (-2.15 to +2.34) |
| WNBA |  | 5.0 to 12.0 | 59 | -0.72 (-5.65 to +4.21) | +1.01 (-1.84 to +3.85) | +1.33 (-0.81 to +3.46) |
| WNBA |  | over 12.0 | 50 | +3.88 (-2.50 to +10.25) | +0.97 (-1.77 to +3.71) | +1.81 (-0.32 to +3.95) |
| WNBA |  | any gap | 165 | +1.60 (-1.83 to +5.03) | +0.37 (-1.25 to +1.99) | +1.05 (-0.20 to +2.31) |

Each contrast is the more experienced team's own Game 1 minus its own Games 2+, minus the same for the less experienced team: percentage points for the shooting rates, fouls per 100 possessions for fouls. Gap bins are terciles of the nonzero gap in each league. Mean over series with a 95% interval. Every postseason in both leagues has player rows.

**Reading.** NBA, roster: the more experienced team's Game 1 foul count is relatively lower (the interval only just clears zero). NBA, franchise: the more experienced team's Game 1 foul count is relatively lower. WNBA, roster: no Game 1 difference between more and less experienced teams that the interval can tell from zero. WNBA, franchise: no Game 1 difference between more and less experienced teams that the interval can tell from zero.
<!-- /gen:experience -->

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
