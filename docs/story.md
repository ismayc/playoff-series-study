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

<div class="eyebrow beat">Across eras</div>

## The game changed around Game 1

The NBA of 1984-85 barely used the three: in that season's Game 1s, 4.3% of
shots came from beyond the arc. By 2025-26 it was 40.1%. Game 1 and later
games rose together, and accuracy in Game 1 kept pace with accuracy later
in the series the whole way. The lines cross back and forth from season to
season in both leagues, and neither sits consistently below the other.

{{fig:fig6_season_pct_py|Three-point percentage by season, every series pooled. Game 1 is solid, Games 2 on dashed. The two lines trade places from season to season in both leagues. WNBA seasons hold only a few multi-game series, so its lines jump more.}}

Split by decade, the Game 1 accuracy gap includes zero in every NBA
decade. The one WNBA decade that clears zero is the 1990s, at −6.55
points, but that rests on just 6 series from the league's first two
postseasons.

{{fig:fig4_decade_accuracy_py|Game 1 minus Games 2 on, three-point percentage, by decade, with 95% intervals. Every NBA decade includes zero, from −1.16 in the 1980s to +0.82 in the 2010s. The WNBA's 1990s point comes from 6 series.}}

Volume is where the eras differ. NBA teams took a smaller share of their
shots from three in Game 1 than in the rest of the series in every season
from 1984-85 through 2019-20. The gap was −1.43 points in the 1990s and
−1.79 in both the 2000s and the 2010s. In the 2020s it shrinks to −0.30
(−1.14 to +0.54), and some recent seasons reverse it. The decade is not
over, so this is a narrowing to watch rather than a settled change. The
WNBA shows no decade with a volume gap that holds up beyond its first
two seasons.

{{fig:fig7_season_rate_py|Share of field-goal attempts taken from three, by season, every series pooled. Game 1 is solid, Games 2 on dashed. The NBA's Game 1 line sits under its later-games line every season through 2019-20, and the two meet in the 2020s.}}

{{fig:fig5_decade_volume_py|Game 1 minus Games 2 on, share of shots from three, by decade, with 95% intervals. The NBA gap is −1.79 points in the 2000s and 2010s and −0.30 in the 2020s, an interval that includes zero.}}

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

{{fig:fig8_stakes_py|Game 1 minus Games 2 on, by round, with 95% intervals. Darker points are the share of shots from three, lighter points three-point percentage. Every accuracy point includes zero. The NBA's volume gap clears zero in every round but the second.}}

{{fig:fig9_rest_py|The more-rested team's own Game 1 minus its own later games, minus the same for the less-rested team, by the size of the rest gap, NBA. The all-gaps point sits just below zero, but no single gap size clears it.}}

<div class="eyebrow beat">Follow-ups</div>

## Winning Game 1 matters; outshooting in it does not

The team that shoots better from three in Game 1 goes on to win the series
59.8% of the time in the NBA. But that team usually won Game 1 as well, and
Game 1 winners take most series. With the Game 1 result held fixed, the
edge disappears: NBA Game 1 winners took the series 76.7% of the time when
they also outshot their opponent from three, and 76.8% when they did not.
In the WNBA the difference is +7.7 points, with an interval from −7.0 to
+22.5 across 167 series.

{{fig:fig10_outshoot_py|Share of series won by the Game 1 winner, split by whether it also outshot its opponent from three in that game, with 95% intervals. The NBA's two shares are level. The WNBA's differ, but their intervals overlap widely.}}

## The 2020 bubble had no Game 1 foul dip

The NBA's 2020 playoffs, played in one arena without fans, are the
exception to the Game 1 foul pattern. Game 1 ran +0.63 fouls per 100
possessions against the series average (−0.35 to +1.61), against −1.09 in
every other season. That rests on 15 series, so it is a lead to follow
rather than a finding. Otherwise the dip is steady: it appears in every
NBA decade, from −1.53 in the 1980s to −0.64 in the 2010s, and in
best-of-5 and best-of-7 series alike.

{{fig:fig11_fouls_eras_py|NBA Game 1 fouls per 100 possessions against the series average, with 95% intervals. Every decade sits below zero. The 2020 single-site playoffs are the one point above it, with the widest interval, from a single season of series.}}

## The same officials whistle Game 1 more lightly

Since 2001-02 (apart from 2002-03) the stats record lists each game's
officials. Two things
could make Game 1 the low point for fouls: lighter-whistled crews assigned
to Game 1s, or the same officials calling Game 1s differently. The data
point to the second. Game 1 crews run +0.00 fouls per 100 possessions
against the series' other crews by their usual tendency (−0.03 to +0.04,
across 240 NBA series), so assignment explains little or none of it. But the same
NBA officials call 1.06 fewer fouls per 100 possessions in their Game 1s
than in their later games, across 56 officials, and the WNBA's do the
same. Officials do differ from one another: in the NBA an official's foul
level in even-numbered seasons tracks their level in odd ones, at r =
+0.49. Recent games mostly list four officials with no note of which three
worked, so seasons from 2016-17 on are thin here.

{{fig:fig12_officials_py|Fouls per 100 possessions against the series mean, by game number (solid), and the usual tendency of the game's crew (dashed), in the same units. Fouls dip at Game 1 in both leagues while the crew line stays flat at zero, so Game 1s get ordinary crews. WNBA games past Game 3 are left off; too few series reach them.}}

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
