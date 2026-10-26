# Florida tennis odds research

First working command-line foundation for comparing Hard Rock Bet Florida with other books and collecting historical tennis data. NFL is planned. No wager execution or proven predictive edge.

## Implemented

- Decimal match-winner comparison: margin removal per reference book, median market probability, expected return, reference disagreement range.
- Excludes stale/future prices, started matches, other Hard Rock states, incomplete markets, and unverified settlement-rule groups. At least two reference books are required; correlation can still make consensus misleading.
- The Odds API adapters for sport discovery, current odds, and historical snapshots.
- API Tennis adapters for catalogs, date-range fixture backfill, and player profiles with provider-supplied season/surface records.
- Optional Sportradar profile adapter for richer biographical fields.
- Local SQLite raw-response archive with source, resource, UTC fetch time and payload hash. Nested statistics and point-by-point fields are retained without converting missing values to zeros.

Provider adapters follow documentation and are tested with mocks; authenticated coverage/end-to-end requests have not yet been verified. No historical dataset has been downloaded because API credentials are not configured. No player-model training, cross-provider identity matching, AI integration, normalized feature warehouse, automatic scheduler, results settlement, or UI is included yet.

## Run locally

Python 3.9+; standard library only, no package install required. Run commands from the repository root. Configure environment variables locally as documented in `.env.example`.

```sh
python3 -m unittest discover -s tests -v
python3 -m tennis_edge compare examples/odds.synthetic.json --now 2026-10-26T12:00:00Z --rules examples/rules.synthetic.json
python3 -m tennis_edge sports
```

Choose an active `tennis_...` key returned by `sports`; keys can be tournament-specific. Substitute it below:

```sh
python3 -m tennis_edge odds --sport TENNIS_SPORT_KEY > data/current-odds.json
python3 -m tennis_edge odds --sport TENNIS_SPORT_KEY --at 2026-10-01T12:00:00Z
python3 -m tennis_edge catalog events
python3 -m tennis_edge catalog tournaments
python3 -m tennis_edge history --start 2025-01-01 --end 2025-01-07
python3 -m tennis_edge history --start 2025-01-01 --end 2025-01-07 --fetch
python3 -m tennis_edge player PROVIDER_PLAYER_ID
python3 -m tennis_edge player sr:competitor:PROVIDER_ID --provider sportradar
```

Create `data/` before shell redirection (`mkdir -p data`); successful provider commands also create it for SQLite storage. Historical fixture preview uses no credits; adding `--fetch` makes one request per day, with at most 366 days per command. Successfully fetched days are archived immediately if a later request fails. Re-running appends snapshots and uses additional requests; automatic resume/deduplication is not implemented.

The default database is `data/tennis.sqlite3`. Use `python3 -m tennis_edge --db PATH ...` to override. Inspect `snapshots` using Python's sqlite3 module or any SQLite viewer; `payload` contains complete JSON. Provider responses are also printed as JSON except backfill, which prints a summary and progress. Raw data and credentials are gitignored.

## Using comparisons

Only `h2h` two-player pre-match decimal prices are supported. Event identity comes from one provider; no fuzzy matching is attempted. References default to Pinnacle, DraftKings and FanDuel, subject to actual availability. Exchange commission is not modeled.

For actual data, create a local JSON map of bookmaker keys to a shared settlement-group label **only after verifying the same rules** for the intended tennis market (retirement, walkover, completion requirements). The synthetic rules file is fictional and must not be used with real markets. Missing verified rules produces a skip, not a bet. Historic comparisons require `--now` equal to the returned snapshot's `timestamp`; do not use the requested timestamp if the response is earlier.

Positive estimated EV is a research candidate, not a guaranteed-profit recommendation. Reference spread is not a statistical confidence interval. Any future validation must use held-out chronological periods and include missing prices, settlement, limits, delays, and costs.

## Services and next steps

See [the data service/account guide](docs/DATA_SOURCES.md) for current published prices, historical limitations, player/statistic coverage, and the target feature dictionary. Start by validating trial coverage against the Florida app; then build player-ID mappings, normalized match/stat tables, time-safe surface/form features and paper-result evaluation. Add NFL only with separate market and settlement handling.
