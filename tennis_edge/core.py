"""Conservative pre-match two-outcome price comparison, not a prediction model."""
import math
import statistics
from datetime import datetime, timezone

TARGET = "hardrockbet_fl"


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp requires a timezone")
    return result


def decimal_odds(value):
    value = float(value)
    if not math.isfinite(value) or value <= 1:
        raise ValueError("Decimal price must be finite and greater than one")
    return value


def compare(events, now=None, max_age=300, min_books=2, rules=None):
    """Rules map book keys to manually verified equivalent settlement group IDs.

    Books without a verified group are excluded. Same-event IDs from one provider
    are used; no fuzzy player-name matching or cross-provider joins are attempted.
    """
    now = now or datetime.now(timezone.utc)
    if max_age <= 0 or min_books < 2:
        raise ValueError("max_age must be positive; min_books must be at least two")
    rules = rules or {}
    results, skipped = [], []
    for event in events:
        try:
            if not event.get("sport_key", "").startswith("tennis_"):
                raise ValueError("Only tennis is supported")
            if timestamp(event["commence_time"]) <= now:
                raise ValueError("Match has started")
            names = [event["home_team"], event["away_team"]]
            if len(set(names)) != 2:
                raise ValueError("Two distinct players required")
            books = {}
            for book in event.get("bookmakers", []):
                key = book["key"]
                if key in books:
                    raise ValueError("Duplicate bookmaker")
                markets = [m for m in book.get("markets", []) if m["key"] == "h2h"]
                if len(markets) != 1:
                    continue
                market = markets[0]
                age = (now - timestamp(market.get("last_update") or book["last_update"])).total_seconds()
                if not 0 <= age <= max_age:
                    continue
                outcomes = market.get("outcomes", [])
                if len(outcomes) != 2 or {o["name"] for o in outcomes} != set(names):
                    continue
                prices = {o["name"]: decimal_odds(o["price"]) for o in outcomes}
                books[key] = prices
            if TARGET not in books:
                raise ValueError("Fresh complete Florida price unavailable")
            if not rules.get(TARGET):
                raise ValueError("Florida settlement rules not verified")
            refs = {k: v for k, v in books.items()
                    if not k.startswith("hardrockbet") and rules.get(k) == rules[TARGET]}
            if len(refs) < min_books:
                raise ValueError("Too few fresh reference books with matching verified rules")
            for name in names:
                probabilities = [(1 / p[name]) / sum(1 / x for x in p.values())
                                 for p in refs.values()]
                probability = statistics.median(probabilities)
                price = books[TARGET][name]
                ev = probability * price - 1
                results.append({"event_id": event["id"], "player": name,
                                "commence_time": event["commence_time"],
                                "bookmaker": TARGET, "decimal_odds": price,
                                "consensus_probability": probability,
                                "reference_probability_range": [min(probabilities), max(probabilities)],
                                "expected_return_per_dollar": ev,
                                "reference_books": sorted(refs),
                                "status": "research_candidate" if ev > 0 else "pass",
                                "note": "Market estimate; reference books may be correlated. Not validated profit."})
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            skipped.append({"event_id": event.get("id"), "reason": str(exc)})
    return {"as_of": now.isoformat(), "comparisons": sorted(results, key=lambda r: r["expected_return_per_dollar"], reverse=True),
            "skipped": skipped}
