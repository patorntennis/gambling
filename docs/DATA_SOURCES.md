# Data services and acquisition plan

Researched October 26, 2026. Prices are published USD monthly prices, not purchases. Provider trials and contracts must be checked for intended use, retention, and redistribution. No accounts or subscriptions have been purchased.

## Accounts to create

| Service | Purpose | Published starting point | What to obtain |
| --- | --- | --- | --- |
| [The Odds API](https://the-odds-api.com/) | Florida Hard Rock prices, other books, historical price snapshots; NFL later | Free: 500 credits/month, no historical odds. Paid: $30/month for 20,000 credits and historical odds; $59 for 100,000 | API key -> `ODDS_API_KEY` |
| [API Tennis](https://api-tennis.com/) | Historical fixtures, results, available match/point statistics, player season and surface records | Starter $40/month, 8,000 requests/day; advertised 14-day trial | API key -> `TENNIS_API_KEY` |
| [Sportradar](https://developer.sportradar.com/tennis/docs/tennis-ig-overview) | Richer profiles including height/handedness, rankings, detailed match statistics and timelines where covered | Request trial and production quote/package access; no verified production price in this research | Tennis product enabled and key -> `SPORTRADAR_API_KEY` |

Start with The Odds API's free access and API Tennis trial to validate actual tennis coverage. The first two paid entry plans would total $70/month, before model usage, tax, or hosting. This is a pilot budget, not a claim of comprehensive coverage. For richer height/profile coverage, evaluate Sportradar separately rather than buying all services immediately.

There is no need for a Hard Rock login/API key in this tool. No cloud hosting or paid database is needed to run it locally. An AI API account is optional later; no model integration or model subscription is required for the current math/data pipeline. Do not post credentials in GitHub or chat; set environment variables locally. `.env.example` only documents names and is not auto-loaded.

## Odds limitations

[Bookmaker documentation](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html) lists `hardrockbet_fl`. Never substitute Indiana or another state. Validate actual active tennis tournaments and compare several prices with the Florida app. A bookmaker listing does not guarantee all markets, live coverage, tour levels, or historical availability.

[Historical odds documentation](https://the-odds-api.com/liveapi/guides/v4/#get-historical-odds) describes snapshots from June 2020, originally ten-minute intervals and five-minute intervals from September 2022. That is the service-wide archive, not a promise of Florida-book or tennis coverage back to that date. Books/markets exist only from when they were added. Historical queries consume more quota; inspect the documentation and usage before bulk backfills. Actual snapshot time can precede requested time and must be used in analysis.

Historical match results and historical odds are different datasets. Profiles pulled today are not point-in-time historical features. Keep `fetched_at`, event time, source, provider IDs, and raw payloads, and avoid using future rankings, corrected results, or current aggregate records in backtests of earlier dates.

## Tennis depth and gaps

[API Tennis documentation](https://api-tennis.com/documentation) supports date-bounded fixtures and player lookup. Profiles include season records and hard/clay/grass wins and losses in the documented examples. Fixtures may include set scores, match statistics, and point-by-point arrays; empty arrays mean unavailable, not zero. Exact earliest history, completeness by year/tour, retirement treatment, and availability of indoor splits need sample checks/provider confirmation. Height is not established by the documented API Tennis profile example; do not assume it is present.

[Sportradar profile fields](https://developer.sportradar.com/tennis/reference/competitor-profile) explicitly include date of birth, height in cm, weight, handedness, professional year and career-high rankings. [Coverage varies by competition](https://developer.sportradar.com/tennis/docs/tennis-ig-overview). Confirm historical seasons accessible to the purchased package and whether point-by-point and detailed stats exist for each target event. The current optional adapter fetches profiles only; broader Sportradar match/season ingestion remains future work.

The previously common `JeffSackmann/tennis_atp` source returned 404 during this research. Do not build the production pipeline around that URL or silently use a mirror. Any archival replacement requires provenance, current availability and license verification for this project's intended use.

## Target feature dictionary

This is the target analytical dataset, not a promise that all listed fields are implemented or supplied by any one provider. The first implementation archives all available raw fields; normalized feature tables/model training are next.

| Area | Fields to preserve or derive | Availability/handling |
| --- | --- | --- |
| Identity | Provider player ID, canonical ID, full name, nationality, DOB, height, weight, handedness, pro year | Preserve provider IDs; manually review cross-source mappings, never join solely by initials |
| Match context | Opponents, tour, singles/doubles, tournament, level, round, start time, best-of, court surface, indoor/outdoor, location, duration | Do not infer surface solely from tournament name; unknown stays null |
| Outcomes | Winner, set/game scores, completed/retired/walkover/void status | Separate completed and retired matches; retain book-specific settlement rules |
| Serve | Aces, double faults, service points, first serves in, first/second serve points won, service games, break points saved/faced | Store numerator and denominator; aggregate counts before computing rates |
| Return | First/second return points won, return games, break points converted/opportunities | Derive from opponent counts only when compatible denominators exist |
| Pressure/points | Tiebreaks, deciding sets, break opportunities, point-by-point score/serve sequence | Tier-dependent; selective detailed coverage is not a representative full archive |
| Form | Last 5/10/20 matches, rolling 30/90/365 days, opponent strength, rankings at match date | Compute strictly from matches known before prediction time |
| Surface | Career/season/rolling W-L, serve/return rates and surface Elo for hard/clay/grass; indoor split if known | Sample size, tour and singles/doubles filters required; do not mix unknown surfaces |
| Workload | Rest days, matches/sets/minutes in prior 7/14/30 days, travel/timezone changes | Date-only match records limit precision; travel requires verified venues |
| Matchup | H2H overall/surface, opponent handedness/height interaction, strength-adjusted matchup | Shrink small samples; height/record alone is not a model |
| External context | Weather, altitude, ball/court conditions, verified injuries/withdrawals | Not implemented; require separate timestamped sources; absence of injury news is not proof of fitness |
| Market | State/book, market/line/selection, odds, source update/fetch time, opener/closing price | Only compare equivalent market and settlement rules; snapshots may be delayed |

Ask providers for ATP/WTA singles samples across main tour, qualifying, Challenger and ITF; known players with different surfaces; recent and older matches; completed/retired/walkover cases. Measure missing-field rates and compare a small sample to original results before committing to a subscription.
