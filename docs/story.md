# Is Game 1 three-point shooting worse than the rest of a playoff series?

Broadcasters say it every spring: teams come out cold in Game 1, shake off
the layoff, and shoot better once they know the opponent. This study checks
every NBA playoff series since 1984-85 and every WNBA series with more than
one game, comparing each series' Game 1 with the games after it. Game 1
accuracy holds up fine. What changes is volume: NBA teams take a smaller
share of their shots from three in Game 1, and that share keeps climbing as
the series goes on. Game 1 also has the fewest fouls of any game, in both
leagues.

<div class="tiles">
<div class="tile"><div class="label">NBA accuracy</div>
<div class="value">−0.03</div>
<div class="sub">Game 1 three-point percentage minus Games 2 on, in points, across 630 series (95% interval −0.87 to +0.82).</div></div>
<div class="tile"><div class="label">WNBA accuracy</div>
<div class="value">+0.26</div>
<div class="sub">The same comparison across 170 series (−1.14 to +1.67). No Game 1 dip.</div></div>
<div class="tile"><div class="label">NBA volume</div>
<div class="value">−1.32</div>
<div class="sub">Points of field-goal attempts taken from three, Game 1 against Games 2 on (−1.61 to −1.03).</div></div>
<div class="tile"><div class="label">Fouls in Game 1</div>
<div class="value">−1.05</div>
<div class="sub">NBA fouls per 100 possessions against the series average (WNBA −1.00).</div></div>
</div>

<div class="eyebrow beat">The question</div>

## A fair comparison inside each series

Comparing Game 1s across the league with later games would mix in which
teams are still playing: by Game 7 only close series remain. So every
comparison here stays inside one series, with the same two teams. Both
teams' threes are pooled for Game 1 and for Games 2 on, and the difference
is averaged over series. Because Games 6 and 7 exist only in close series,
the same estimate is repeated against Game 2 alone, which every series has.
A Game 1 effect has to show up in both versions to count.

The analysis plan was written down and fixed before any Game 1 number was
computed. It was implemented twice, in Python and in R, and the two agree on
every output cell.

<div class="eyebrow beat">The answer</div>

## Game 1 accuracy is not worse

{{fig:fig1_game1_gap_py|Game 1 minus later games in the same series, in percentage points with 95% intervals. Accuracy sits on zero in both leagues and on both comparisons: the NBA is −0.03 against Games 2 on and −0.32 against Game 2 alone, the WNBA +0.26 and +0.64. NBA attempt rate is lower in Game 1 on both comparisons, −1.32 and −1.02. WNBA attempt rate is not distinguishable from zero.}}

Counting every three-pointer together instead of averaging series, NBA
Game 1s actually shot a little better than later games: 35.11% against
34.83%. Nothing here supports a cold Game 1.

<div class="eyebrow beat">Through a series</div>

## Volume climbs, game by game

Following every rate through the series, with each team measured against
its own average for that series, shows the volume change is not a Game 1
quirk. In the NBA the share of shots from three rises steadily from Game 1
to Game 7, and it still rises when only series that went the distance are
kept, so the climb is not a change in which series are present.

{{fig:fig2_attempts_by_game_py|Share of a team's shots taken from three, against that team's average for the series, by game number. NBA Game 1 sits at −1.07 points and Game 7 at +1.01. The WNBA has no trend.}}

One natural explanation is that the team behind in the series starts
shooting its way back. The data say the opposite: from Game 2 on, the team
trailing in the series takes relatively fewer threes than the leader, by
−1.07 points in the NBA (−1.35 to −0.80) and −2.34 in the WNBA. Trailing
teams have also just lost games, so this sorts teams by recent results
rather than showing intent.

{{fig:fig3_fouls_by_game_py|Fouls per 100 possessions against each team's series average, by game number. Game 1 is the low point in both leagues (NBA −1.05, WNBA −1.00) and Game 2 jumps back up. Free-throw rate follows the same pattern (NBA −2.23 points in Game 1).}}

Fewer fouls in Game 1 can mean fewer called or fewer committed; box scores
cannot separate the two.

<div class="eyebrow beat">Stakes and rest</div>

## Neither the round nor the layoff changes it

No round, from the first round to the Finals, shows a Game 1 accuracy gap
that holds on both comparisons. The NBA's lower Game 1 volume appears in
the first round (−1.60), the conference finals (−1.56), and the Finals
(−1.65), so it is not about stakes. Rest gaps, where one team swept and the
other went long, show at most a hint of rust in the NBA: across 337 series
with a gap, the more-rested team's Game 1 shooting is relatively worse by
2.49 points (−4.92 to −0.06), but no single size of gap clears zero on its
own. Rest also arrives with recent form, so this stays a hint.

<div class="eyebrow beat">Limits</div>

## What this can and cannot say

Box scores record what happened, not why. A difference between Game 1 and
later games mixes scouting adjustments, officiating, rest, and game script,
and this design compares them without separating them. Three-point attempts
are missing from most NBA box scores before 1984-85, so earlier seasons are
left out. The 2026 WNBA Finals was in progress when the data were gathered
and is excluded until it ends.

The game logs come from stats.nba.com and stay local; this page and its
repository publish only summaries, never the game-by-game records.
