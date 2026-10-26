"""Documented provider clients and append-only local response archive."""
import hashlib
import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


def get_json(base, params, headers=None):
    # Never log request URLs: two providers authenticate in query parameters.
    request = Request(base + ("?" + urlencode(params) if params else ""), headers=headers or {})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError("Provider HTTP error %s; check access, quota and request parameters" % exc.code) from None
    except (URLError, TimeoutError, ValueError):
        raise RuntimeError("Provider network or JSON response error") from None


def secret(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError("Set %s in your local environment" % name)
    return value


def archive(db, source, resource, payload):
    """Retain nested point-by-point and stat fields without lossy normalization."""
    directory = os.path.dirname(db)
    if directory:
        os.makedirs(directory, exist_ok=True)
    serialized = json.dumps(payload, sort_keys=True)
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, source TEXT NOT NULL, resource TEXT NOT NULL, fetched_at TEXT NOT NULL, sha256 TEXT NOT NULL, payload TEXT NOT NULL)")
        connection.execute("INSERT INTO snapshots(source,resource,fetched_at,sha256,payload) VALUES (?,?,?,?,?)",
                           (source, resource, datetime.now(timezone.utc).isoformat(),
                            hashlib.sha256(serialized.encode()).hexdigest(), serialized))


def odds(sport=None, at=None):
    root = "https://api.the-odds-api.com/v4/"
    params = {"apiKey": secret("ODDS_API_KEY")}
    if sport is None:
        return get_json(root + "sports", params)
    if not sport.startswith("tennis_"):
        raise ValueError("Select a tennis sport key from the sports command")
    params.update(bookmakers="hardrockbet_fl,pinnacle,draftkings,fanduel", markets="h2h", oddsFormat="decimal")
    if at:
        parsed = datetime.fromisoformat(at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Historical timestamp requires a timezone")
        params["date"] = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    path = ("historical/" if at else "") + "sports/" + quote(sport, safe="") + "/odds"
    return get_json(root + path, params)


def tennis(method, **params):
    payload = get_json("https://api.api-tennis.com/tennis/",
                       dict(params, method=method, APIkey=secret("TENNIS_API_KEY")))
    if not isinstance(payload, dict) or payload.get("success") != 1:
        raise RuntimeError("API Tennis returned an unsuccessful response; check plan and parameters")
    return payload


def days(start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first:
        raise ValueError("End date precedes start date")
    if (last - first).days >= 366:
        raise ValueError("Backfill at most 366 days per command to bound request usage")
    while first <= last:
        yield first.isoformat()
        first += timedelta(days=1)


def sportradar_profile(player_id, access="trial"):
    if access not in ("trial", "production"):
        raise ValueError("Invalid access level")
    return get_json("https://api.sportradar.com/tennis/%s/v3/en/competitors/%s/profile.json" %
                    (access, quote(player_id, safe="")), {},
                    {"x-api-key": secret("SPORTRADAR_API_KEY")})
