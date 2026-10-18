# Playoff series study: design notes

Started October 18, 2026. Status: **data layer built; no Game 1 comparison
has been computed.** The analysis below is specified before any outcome is
looked at, the same discipline as the contract-year study: once the first
comparison runs, the metric, the sample, and the baseline do not change
without a dated amendment that says why. Every claim about the data was
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

Fixed now, before any Game 1 number exists. Points marked PROPOSED wait on
Chester's decision.

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
  home and road in Game 1. The 2020 NBA bubble is neutral-site and is
  reported in neither split.
- **Secondary outcome.** Three-point attempt rate (3PA / FGA), same
  structure. A lower Game 1 rate with unchanged accuracy is a different
  finding from a lower accuracy.
- **Eras.** PROPOSED: one headline per league over every complete season,
  plus decade panels.

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
