# Data sources

One row per dataset. A dataset is not used until its **License** cell is filled
from the source's own page (quote it), or marked "unverified" with the reason.
Commercial use and redistribution matter whenever the work is paid, published,
or preloaded for learners.

| Dataset | URL | License (quoted) | Commercial use | Redistribution | Retrieved | Local file |
|---|---|---|---|---|---|---|
| NBA and WNBA team game logs (LeagueGameLog, team mode; Regular Season, Playoffs, PlayIn) | https://stats.nba.com/stats/leaguegamelog | NBA.com Terms of Use, section 9: "The NBA Statistics may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes" (quoted from nba-shot-charts/DATA_SOURCES.md, checked there September 30, 2026; not re-fetched for this repo) | no | no public republishing of the raw tables; private, non-commercial use only | October 18, 2026 | data/raw/gamelogs/ |

## Notes

- Section 9 also requires "a prominent attribution to NBA.com" on any use,
  and bars use "in connection with any website, product, or service that
  features a database ... of comprehensive, regularly updated statistics
  from NBA, WNBA or G-League games" without consent (same source as above).
  A page listing every playoff series game by game sits close to that
  clause, so whether the series review page can be public is an open
  decision, not settled here.
- Data retrieved with nba_api 1.11.4 (https://github.com/swar/nba_api, MIT
  license for the client library itself; the license does not cover the data).
