import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from .core import compare, timestamp
from .data import archive, odds, tennis, days, sportradar_profile


def main():
    parser = argparse.ArgumentParser(description="Florida tennis research; no bet execution")
    parser.add_argument("--db", default="data/tennis.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sports", help="Discover current provider sport keys")
    fetch = commands.add_parser("odds", help="Fetch and archive odds (uses API credits)")
    fetch.add_argument("--sport", required=True)
    fetch.add_argument("--at", help="Historical ISO timestamp; requires paid odds access")
    analyze = commands.add_parser("compare", help="Compare provider-format JSON from disk")
    analyze.add_argument("input")
    analyze.add_argument("--rules", help="JSON map: bookmaker key to manually verified settlement group")
    analyze.add_argument("--now", help="As-of timestamp; mandatory for historical snapshots")
    analyze.add_argument("--max-age", type=int, default=300)
    history = commands.add_parser("history", help="API Tennis fixture backfill, one request per day")
    history.add_argument("--start", required=True)
    history.add_argument("--end", required=True)
    history.add_argument("--event-type", help="Provider event type ID, e.g. from catalog")
    history.add_argument("--fetch", action="store_true", help="Actually use credits; default is a request preview")
    catalog = commands.add_parser("catalog")
    catalog.add_argument("kind", choices=["events", "tournaments"])
    profile = commands.add_parser("player")
    profile.add_argument("id")
    profile.add_argument("--provider", choices=["api-tennis", "sportradar"], default="api-tennis")
    profile.add_argument("--access", choices=["trial", "production"], default="trial")
    args = parser.parse_args()
    try:
        if args.command == "compare":
            payload = json.loads(Path(args.input).read_text())
            if isinstance(payload, dict) and "timestamp" in payload and not args.now:
                raise ValueError("Historical comparison requires --now matching its snapshot timestamp")
            if isinstance(payload, dict) and "timestamp" in payload and timestamp(args.now) != timestamp(payload["timestamp"]):
                raise ValueError("--now must equal the historical response timestamp (not the requested timestamp)")
            events = payload.get("data", []) if isinstance(payload, dict) else payload
            rules = json.loads(Path(args.rules).read_text()) if args.rules else {}
            result = compare(events, now=timestamp(args.now) if args.now else None,
                             max_age=args.max_age, rules=rules)
        elif args.command == "history":
            dates = list(days(args.start, args.end))
            if not args.fetch:
                result = {"planned_requests": len(dates), "dates": dates, "hint": "Add --fetch to use provider credits"}
            else:
                for day in dates:
                    params = {"date_start": day, "date_stop": day, "timezone": "UTC"}
                    if args.event_type:
                        params["event_type_key"] = args.event_type
                    payload = tennis("get_fixtures", **params)
                    archive(args.db, "api-tennis", json.dumps(params, sort_keys=True), payload)
                    print(json.dumps({"archived_date": day, "fixtures": len(payload.get("result", []))}), file=sys.stderr)
                result = {"archived_days": len(dates), "database": args.db}
        else:
            if args.command == "sports":
                result, provider, resource = odds(), "the-odds-api", "sports"
            elif args.command == "odds":
                result, provider, resource = odds(args.sport, args.at), "the-odds-api", args.sport + ":" + (args.at or "latest")
            elif args.command == "catalog":
                result, provider, resource = tennis("get_" + args.kind), "api-tennis", args.kind
            else:
                result = tennis("get_players", player_key=args.id) if args.provider == "api-tennis" else sportradar_profile(args.id, args.access)
                provider, resource = args.provider, "player:" + args.id
            archive(args.db, provider, resource, result)
        print(json.dumps(result, indent=2))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, "Error: %s\n" % exc)


if __name__ == "__main__":
    main()
