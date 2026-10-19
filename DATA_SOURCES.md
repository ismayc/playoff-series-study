# Data sources

One row per dataset. A dataset is not used until its **License** cell is filled
from the source's own page (quote it), or marked "unverified" with the reason.
Commercial use and redistribution matter whenever the work is paid, published,
or preloaded for learners.

| Dataset | URL | License (quoted) | Commercial use | Redistribution | Retrieved | Local file |
|---|---|---|---|---|---|---|
| NBA and WNBA team game logs (LeagueGameLog, team mode; Regular Season, Playoffs, PlayIn) | https://stats.nba.com/stats/leaguegamelog | NBA.com Terms of Use (https://www.nba.com/termsofuse, "LAST UPDATED: July 13, 2026"), section 9 (ii): "the NBA Statistics may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes;" (re-fetched October 18, 2026) | no | no public republishing of the raw tables; private, non-commercial use only | October 18, 2026 | data/raw/gamelogs/ |
| NBA liveData box scores (team statistics, officials with their assignment), NBA 2019-20 on and WNBA 2022 on, as cached by the October 19, 2026 audit | https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/{NBA,WNBA}/liveData/boxscore/boxscore_<GAME_ID>.json (the URL in the audit script `pcheck.py`) | unverified: assumed to fall under the same NBA.com Terms of Use as the stats API; the feed carries no terms of its own that were checked | no | no; kept local in `data/raw/live/`, and the tables derived from it (`data/live_officials.csv`, `data/live_team_box.csv`) list games one by one, so they are gitignored too | on or before October 19, 2026 (the exact fetch time is not recorded; files copied from `../.audit-cache-2026-10-19/audit_contract_playoff/live/` on October 19, 2026, checksums identical); cannot be re-fetched from this machine (403) | data/raw/live/ |

## Notes

- Section 9 (i) requires "a prominent attribution to NBA.com in connection
  with such use, display, or publication;" and (vii) bars use "in connection
  with any website, product, or service that features a database (in any
  medium or format) of comprehensive, regularly updated statistics from NBA,
  WNBA or G-League games, competitions, or events" "without the Operator's
  express prior consent." Both re-fetched October 18, 2026, from the page
  above (through a fetch tool that returns short verbatim segments; the
  middle of clause (vii) was not returned in full).
- Reading (October 18, 2026, not legal advice): "private, non-commercial"
  can mean both private and non-commercial, which a free public website is
  not; it can also be read as personal, non-business use. Clause (vii) does
  not turn on money at all. A page listing every playoff game's box score
  sits close to (vii), so whether the series review page can be public is
  Chester's open decision, not settled here. The derived analysis (README
  tables, averages by game number) is the kind of output the family's other
  public studies already publish.
- Data retrieved with nba_api 1.11.4 (https://github.com/swar/nba_api, MIT
  license for the client library itself; the license does not cover the data).
