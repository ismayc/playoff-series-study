# Playoff series study: design notes

Started October 18, 2026. Status: **question 1 run on October 18, 2026,
after the analysis below was fixed; results are in the README's generated
regions. Question 4 run the same day, after its definitions below were
fixed. Question 2 (the local review page, descriptive) and question 3 built
the same day, question 3 after its definitions below were fixed.** The analysis was specified
before any outcome was looked at, the same discipline as the contract-year
study: the metric, the sample, and the baseline do not change without a
dated amendment that says why. Every claim about the data was
checked by loading it on October 18, 2026, unless marked UNVERIFIED.

Origin: the backlog entry "the Game 1 effect, and how stats move through a
series" (hub/ideas, filed October 17, 2026). Its sub-ideas map to the
questions below.

## Questions

1. **The Game 1 three-point dip.** Is Game 1 three-point shooting worse
   than the rest of the series, for both teams, across NBA and WNBA playoff
   series? (Confirmatory.)
2. **Series and team review page.** Every series and every franchise over
   time, as a browsable page. (Descriptive.)
3. **Stakes and layoffs.** Does the Game 1 gap change by round and by the
   rest gap between the two teams? (Exploratory.)
4. **The whole box score by game number.** How fouls, free throws,
   turnovers, pace, and the other counts move from Game 1 to the last game.
   (Exploratory.)

Only question 1 is a test. Questions 3 and 4 are many comparisons on one
dataset, so they are reported as estimates with intervals and no
significance claims.

## Data

stats.nba.com `LeagueGameLog`, team mode, via nba_api 1.11.4: one call per
league, season, and season type (Regular Season, Playoffs, and PlayIn for
the NBA from 2019-20). 01_harvest.py writes them to `data/raw/gamelogs/`
(gitignored). See DATA_SOURCES.md for terms.

What loading it showed:

- **Series and game numbers are rebuilt from the games, not read from the
  ID.** Game IDs for seasons ending before 2002 are a running count through
  the postseason (NBA 0049600001, WNBA 1040100001). From 2002 in both
  leagues the ID ends in round, series, and game digits, and 02 checks every
  one of those against date order (they agree in every season).
- **Counts are missing in early NBA seasons.** `output/coverage.csv` holds
  the share of playoff rows carrying each count, by league-season. In the
  NBA, three-point attempts, turnovers, and offensive rebounds are complete
  from 1984-85; before that most rows leave them blank, even though the line
  arrived in 1979-80 (makes are complete from then). Fouls are complete from
  1982-83, free-throw attempts from 1963-64. Every WNBA season is complete.
  Each question's era starts where its counts are complete.
- **Invalid series** (`output/series.csv`): 02 rejects a pairing whose
  games are not one unbroken run for each team, are tied, do not end on the
  clinching win, or exceed 2W - 1 games, and a series that needs fewer wins
  than another in its round or than any earlier round (the Finals). Two
  cases are invalid, both listed as known: the 1954 NBA division round
  robins, and the 2026 WNBA Finals, one game in at harvest. Each check was
  seen to fire on its real case before the case was listed: the ID check on
  2000-01 (NBA) and 1997 to 2001 (WNBA), the run check on 1954, and the
  format check on the 2026 Finals, which the win-count rules alone passed as
  a complete one-game series.
- **Checked against known results:** the Finals of 1970, 1984, 1998, 2016,
  and 2025 (NBA) and of 2005, 2016, and 2025 (WNBA) come out with the right
  teams and lengths, and modern seasons have 15 NBA and 7 WNBA series.
- **Rest** includes play-in games: Portland's 3 days before its 2020 first
  round count from its August 15 play-in.
- **Single-game rounds** (the 1997 WNBA playoffs, early NBA tiebreakers)
  are valid series with no "rest of series", so question 1 drops them.

- **Possible gap, UNVERIFIED:** the build cannot tell a missing game from
  a series that was shorter. A dropped Game 3 would renumber Games 4 on.
  Checking each season's game count against an independent source
  (Basketball-Reference series lengths) would settle it.

## Pre-specified analysis for question 1

Fixed before any Game 1 number existed. Implemented twice, in
`python/03_game1.py` and `R/03_game1.R`, and `python/04_reconcile.py`
fails unless every output cell agrees.

- **Sample.** Every valid series with at least two games, in every
  league-season whose playoff rows all carry FG3M and FG3A: NBA 1984-85 to
  2025-26, WNBA 1998 to 2026 (1997 had single games only). Leagues are
  reported separately, never pooled.
- **Unit.** The series, with both teams pooled, because both teams'
  shooting in one game shares the officials, the pace, and the building.
  For series s: d_s = (3PM / 3PA in Game 1) minus (3PM / 3PA over Games 2
  through the last), both teams' makes and attempts summed.
- **Estimate.** The mean of d_s over series, with a 95% interval of mean
  plus or minus 1.96 sd / sqrt(n) (sample sd). Analytic, so the Python and
  R implementations reconcile exactly (family rule: no bootstrap).
- **Selection-free version.** Games 6 and 7 exist only in close series, so
  the same estimate with Game 2 alone in place of "Games 2 through the
  last" is reported beside the headline. If the two disagree in sign, the
  headline is not claimed.
- **Baseline.** Each team-game gets an expected 3P% from the regular
  season: the team's 3P% plus its opponent's 3P% allowed minus the league
  3P%. Game 1 minus expected and later games minus expected are reported
  separately, so "Game 1 is cold" can be told apart from "later games are
  hot."
- **Home and road.** Game 1 is at the higher seed. The team-level version
  of d (each team's own Game 1 minus its own later games) is split by
  home and road in Game 1. The 2020 seasons are neutral-site and are
  reported in neither split (Amendment 1).
- **Secondary outcome.** Three-point attempt rate (3PA / FGA), same
  structure. A lower Game 1 rate with unchanged accuracy is a different
  finding from a lower accuracy.
- **Eras.** One headline per league over every complete season, plus
  decade panels (decided by Chester, October 18, 2026). A decade is the
  season's end year rounded down to a multiple of 10, so the NBA's
  1980s panel holds only 1984-85 to 1988-89.
- **Undefined values.** A series with zero three-point attempts (both
  teams) in Game 1, in Games 2 on, or in Game 2 drops from the estimates
  that need that value, and the count dropped is reported with each one.
  In the team-level split, a team with zero attempts on either side drops
  the same way.
- **Expected 3P%, exactly.** For team t against opponent o in season y:
  e = t's regular-season 3PM / 3PA, plus o's regular-season 3PM / 3PA
  allowed, minus the league's regular-season 3PM / 3PA. A series' Game 1
  residual is (sum of 3PM minus sum of e times 3PA) / sum of 3PA over both
  teams' Game 1 rows, and likewise for Games 2 on.

### Amendment 1 (October 18, 2026, before any outcome was computed)

The 2020 WNBA season was also played at a single neutral site (IMG Academy,
Bradenton), like the 2020 NBA bubble. Both 2020 seasons are left out of the
home and road split. They stay in every other estimate.

### Amendment 2 (October 18, 2026, before any outcome was looked at)

The 1984-85 NBA regular season records three-point attempts in 8.4% of its
team-game rows (makes in all of them), so its regular-season 3P% cannot be
computed: a plain sum gave the 1984-85 Lakers 90 makes on 6 attempts. The
playoff rows that season are complete. Regular-season totals are now blank
unless every game behind them carries the count, so 1984-85 has no
expected 3P%. Its 15 series stay in the Game 1 versus later comparisons
and drop from the two residual estimates, with the count dropped reported
there. Found when the first run reported 3 team-games without a baseline,
before the summary table was opened; it moved the expected-3P% definition,
not the comparison.

## Questions 3 and 4 (exploratory, fixed definitions)

- **Rest gap.** Days of rest before Game 1 for one team minus the other's
  (decided October 17, 2026), from each team's full schedule including
  regular season and play-in. Reported in bins (0, 1 to 2, 3 to 5, 6+ days).
- **Round.** From the encoded ID where it exists (2002 on); before that,
  only the Finals (the series holding the postseason's last game) is
  identified, plus each team's series ordinal.
- **Per-game profiles.** For each count (PF, FTA per FGA, TOV per 100
  possessions, pace, OREB rate, AST per FGM, points per 100 possessions),
  the team-game value minus that team's own series mean, averaged by game
  number with a 95% interval. Possessions: FGA + 0.44 FTA - OREB + TOV,
  averaged over both teams.

### Question 3, fixed October 18, 2026 before any of it was computed

Implemented in `python/stagelib.py` and `R/functions.R`, run by
`python/08_stakes_rest.py` and `R/08_stakes_rest.R`, reconciled by 04. This
replaces the two looser bullets above.

- **Stage, not round number.** Round numbers are not comparable across
  formats (the WNBA has run two to four rounds, some single-game, with
  byes), so a series' stage is its distance from the Finals: 0 for the
  Finals, 1 for the round before, and so on. It comes from the winner's
  path: a series' stage is one more than the stage of the next series its
  winner played. This handles byes and needs no game ID. Check: wherever
  the ID encodes a round (2002 on), stage must equal the season's highest
  round minus the series' round, for every series; 08 fails otherwise. A
  series whose winner's path does not reach a valid Finals (the 2026 WNBA
  semifinals, while the Finals is excluded) has no stage and is counted.
- **Stakes.** The question 1 sample and series values (D_PCT, D2_PCT,
  D_RATE), summarized by league and stage with the question 1 interval.
- **Opponent strength.** The backlog entry proposed adjusting for both
  teams' regular-season ratings. Every outcome here is a within-series
  difference (the same two teams in Game 1 and later), so team strength
  cancels by construction and no rating adjustment is added.
- **Rest gap** (decided October 17, 2026). For each Game 1, gap = the
  difference in days of rest between the two teams, from each team's full
  schedule including play-in games. When the gap is not zero, the contrast
  is the more-rested team's own Game 1 minus own Games 2 on, minus the same
  for the less-rested team, for three-point percentage and for attempt rate
  (FG3A / FGA). Each team is measured against its own later games, so team
  quality cancels; a positive contrast means extra rest goes with a
  relatively better (or more three-heavy) Game 1. Summarized by league for
  gaps of 1 to 2, 3 to 5, and 6 or more days, and for every nonzero gap,
  with the count of zero-gap series reported. Sample: the question 1
  sample, 2020 included (rest in the bubble was real). A team with no
  three-point attempts in Game 1 or in Games 2 on drops from that contrast
  and is counted.
- Exploratory throughout: estimates and intervals, no significance claims.
- **What the stage checks showed** (October 18, 2026, first run). Stage
  equals the encoded round in all 543 series with one (2002 on, both
  leagues, including the WNBA's bye and single-game years). Before 2002,
  every NBA season from 1984-85 to 2000-01 has exactly 8, 4, 2, and 1
  series at stages 3 to 0, the fixed 16-team bracket. The only series
  without a stage are the six 2026 WNBA series, whose Finals is excluded;
  08 fails if a series lacks a stage in any season that has a Finals.

### Question 4, fixed October 18, 2026 before any profile was computed

Implemented in `python/profilelib.py` and `R/functions.R`, run by
`python/06_profiles.py` and `R/06_profiles.R`, reconciled by 04.

- **Sample.** Valid series of two or more games in league-seasons whose
  playoff rows all carry FGA, FTA, OREB, DREB, TOV, PF, AST, FGM, FG3A,
  and MIN: NBA 1984-85 on, every WNBA season with a multi-game series.
- **Metrics, per team-game.** Possessions P = the mean of both teams'
  FGA + 0.44 FTA - OREB + TOV, so one game has one P.
  - PF100 = 100 PF / P; TOV100 = 100 TOV / P; ORTG = 100 PTS / P.
  - FTR = FTA / FGA; AST_RATE = AST / FGM; OREB_PCT = OREB / (OREB +
    opponent DREB).
  - PACE = P per regulation game: P times (regulation minutes / game
    minutes), where game minutes are team MIN / 5 and regulation is 48
    (NBA) or 40 (WNBA). This removes overtime.
  - FG3A_RATE = FG3A / FGA and FG3_PCT = FG3M / FG3A, for continuity
    with question 1.
- **Deviation.** Each team-game value minus the mean of that team's values
  over the series (an unweighted mean over its games). A game's deviation
  is the mean of its two teams' deviations, so the game is the unit (for
  PACE the two teams are identical by construction). A blank value (no
  attempts) drops that team from the game's mean; a game with both blank
  drops, and is counted.
- **Profile.** Mean deviation by league and game number with the 95%
  interval of question 1 (mean plus or minus 1.96 sd / sqrt(n)).
- **Composition.** Game 7 exists only in long series, so a second profile
  uses only full-length series (N_GAMES = 2 x WINS_NEEDED - 1). Its
  game-number mix is constant, so a trend in it is not a change in which
  series are present.
- **Series state, for the three-point volume question.** For Game 2 on,
  in games where one team leads the series: the trailing team's FG3A_RATE
  deviation minus the leading team's. Positive means the team behind in the
  series takes relatively more threes. Reported per league with the same
  interval, plus the count of games tied in the series (left out).
- Exploratory throughout: estimates and intervals, no significance claims.

### Era and season breakdown, added October 18, 2026 (exploratory)

Requested by Chester after question 1 was published; it changes nothing in
the pre-specified analysis above. The decade panels of question 1 are
reported for both leagues, and a new table, `output/game1_season.csv`
(`game1lib.season_values`, R twin `season_values`), gives per league and
season the attempt-weighted Game 1 and Games 2+ totals: 3P% = sum of 3PM /
sum of 3PA, attempt rate = sum of 3PA / sum of FGA, over every series in the
question 1 sample. These are levels with no intervals, read as description.
The table holds season totals, not series or games, so it is committed.

## Follow-ups 5 to 8, fixed October 19, 2026 before any of them was computed

Chester asked on October 19, 2026 for the four parts of the backlog entry
that questions 1 to 4 left out. All four are exploratory: estimates and
intervals, no significance claims. Each is implemented in Python and in R
and reconciled by 04, like questions 1 to 4. Proportions use the Wald
interval p plus or minus 1.96 sqrt(p (1 - p) / n), a difference of two
proportions sqrt(p1 q1 / n1 + p2 q2 / n2), and means the question 1
interval, so both implementations agree exactly.

### 5. Does the Game 1 three-point winner win the series?

From the backlog's question 2. The obvious version is confounded: the team
that outshoots its opponent from three in Game 1 usually also wins Game 1,
and Game 1 winners usually win the series. So the comparison is made
within the Game 1 result.

- **Sample.** The question 1 sample (valid series, two or more games,
  complete three-point seasons). A series drops, and is counted, when
  either team has no three-point attempts in Game 1 or the two Game 1
  three-point percentages are equal.
- **Per series, from the Game 1 winner's side.** OUTSHOT is true when the
  Game 1 winner's Game 1 3P% is higher than the loser's. SERIES_WIN is
  true when the Game 1 winner also wins the series.
- **Estimates, per league.** (a) The share of series won by the team with
  the higher Game 1 3P%, whichever team won Game 1. (b) The Game 1 winner's
  series-win share when OUTSHOT and when not, and the difference (OUTSHOT
  minus not). A difference near zero means Game 1 three-point shooting says
  nothing about the series beyond who won the game.

### 6. Format breaks: the 2020 bubble and series length

From the backlog's question 3 ("natural breaks").

- **Sample.** The question 1 series values (D_PCT, D2_PCT, D_RATE,
  D2_RATE), plus each series' Game 1 deviation in PF100 and FTR from the
  question 4 game table (G1_PF100, G1_FTR), joined on the series key. A
  series outside the question 4 sample has those two blank.
- **Bubble.** Per league, 2020 against every other season, for each of the
  six metrics. Both 2020 postseasons were played at a single site with no
  home crowd (Amendment 1).
- **Series length.** Per league, by wins needed: best-of-5 (3) and
  best-of-7 (4) in the NBA (best-of-5 first rounds through 2001-02), and
  best-of-3 (2), best-of-5 (3), and best-of-7 (4) in the WNBA (the only
  WNBA best-of-7 in the sample is the 2025 Finals, so it gets no interval).
  Length is confounded with round and era (short series are early rounds,
  and the NBA's ended in 2002); the table is description.

### 7. Question 4 profiles by decade

From the backlog's question 4 ("by era"). The question 4 "every series"
profile (mean deviation by game number with its interval), computed
separately per league and decade, where a decade is the season's end year
rounded down to a multiple of 10, as in question 1. Written to
`output/profile_decade.csv`.

### 8. Fouls and the officials

From the backlog's question 4 ("split by referee crew where the data
allows"). Question 4 found fewer fouls per 100 possessions in Game 1. This
asks whether the officials assigned explain it, and whether officials
differ at all.

- **Data.** BoxScoreSummaryV3 officials per game, harvested by
  `python/10_harvest_officials.py` into `data/raw/officials/` (gitignored).
  A probe on October 19, 2026 found officials listed from about 2001-02
  (NBA) and 2004 (WNBA) and none earlier; 2002-03 had one empty game in
  the probe, so coverage is measured, not assumed.
- **Sample.** Question 4 games (PF100 deviation from `profile_games`)
  that list exactly three officials. Other games drop and are counted per
  league and season in `output/officials_coverage.csv`. Each league is
  analyzed alone; an official's games are pooled across seasons.
- **8a, the Game 1 dip in this sample.** The question 4 PF100 profile at
  Game 1, recomputed on the officials sample, so 8b has a comparison.
- **8b, crew assignment.** Each game's residual is its PF100 deviation
  minus the league's mean deviation at that game number in the officials
  sample (so a Game 1 is not counted as low just for being a Game 1). An
  official's tendency for a given series is the mean residual over the
  games they worked in other series of the same league; an official with
  fewer than five such games is left out of the crew. A game's CREW value
  is the mean tendency of its listed officials who have one. CREW
  deviation is CREW minus its mean over the series' games, using only
  series whose every game has a CREW value. The mean CREW deviation by game
  number shows whether low-whistle crews get Game 1s; compare its Game 1
  value with 8a. (The league mean at each game number includes the game
  itself; with hundreds of games per game number this is not corrected.)
- **8c, the same official in Game 1 and later.** For each official with at
  least three Game 1s and three later games in the sample: their mean PF100
  deviation in Game 1s minus their mean in Games 2 on. The mean over
  officials with its interval shows whether the dip holds with the person
  fixed. An official's games are not independent of other officials' (three
  share each game), so the interval is approximate.
- **8d, do officials differ?** For each official with at least ten games in
  even-numbered seasons and ten in odd-numbered seasons: their mean residual
  (as in 8b) in each half. The Pearson correlation of the two halves over
  officials, with the Fisher interval tanh(atanh(r) plus or minus 1.96 /
  sqrt(n - 3)). A correlation near zero means the spread between officials
  is noise; a clearly positive one means some officials call more fouls,
  year after year.
- **What the harvest showed** (October 19, 2026, before any follow-up 8
  result was looked at). All 2,604 games from 2000-01 (NBA) and 2003
  (WNBA) on were fetched. No officials are listed for any 2000-01 or
  2002-03 NBA playoff game, and none for 2003 WNBA. From 2016-17 (NBA) and
  2018 (WNBA) most games list four officials, and one 2004 NBA game lists
  six; the records have no field saying which three worked the game (the
  `assignment` field is blank), so the fourth is probably an alternate but
  that is unverified. Those games stay out as specified, which leaves the
  recent seasons thin; `output/officials_coverage.csv` gives the counts.
- **What stays local.** Per-game crews and per-official values name people
  next to game-level statistics, so they stay in gitignored files; the
  committed tables are the coverage counts and the summaries.
