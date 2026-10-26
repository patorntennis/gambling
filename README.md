# Gambling

Tennis odds research for Hard Rock Bet in Florida, with NFL planned next.

## Status

Planning stage. Live odds ingestion, prediction models, AI analysis, and bet execution are not implemented. Profitability is unproven.

## Initial scope

- Compare pre-match tennis match-winner odds from the user's state-specific Hard Rock feed with other sportsbooks.
- Match events, selections, timestamps, and settlement rules; reject stale or incompatible comparisons.
- Remove bookmaker margin from complete opposing reference prices and estimate a consensus probability independently of the Hard Rock target price.
- Calculate expected net return per dollar as probability times decimal odds minus one for markets without pushes. Display uncertainty and supporting sources.
- Track paper selections, closing prices, settlement, ROI, drawdown, and data costs before claiming an edge.

## AI analysis

ChatGPT or Claude may summarize sourced news and explain calculations. Model confidence alone is not a validated probability estimate. Missing or conflicting evidence should result in passing on a bet.

## Data

The Odds API lists state-specific Hard Rock feeds in its documentation: https://the-odds-api.com/sports-odds-data/bookmaker-apis.html

Target betting state: **Florida**. The initial candidate feed is `hardrockbet_fl`; do not substitute another state's feed if it is unavailable.

Verify tennis market coverage against the Florida app, freshness, and subscription costs before choosing a provider. A bookmaker listing does not guarantee every event or market. Store API keys outside Git. No Hard Rock account credentials are required for odds comparison.

## Roadmap

1. Sample/manual data importer and tested odds calculations.
2. Verified live feed and timestamped snapshots.
3. Paper results tracking and held-out model evaluation.
4. Sourced AI explanations and review interface.
5. NFL moneylines, spreads, and totals with push and settlement handling.

The tool is for research and human review; it does not place wagers or guarantee profit.
