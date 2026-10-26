import copy
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from tennis_edge.core import compare, decimal_odds
from tennis_edge.data import archive, days, get_json, odds, tennis

NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
RULES = {k: "demo-only" for k in ["hardrockbet_fl", "pinnacle", "draftkings"]}


def event():
    books = []
    for key, prices in [("hardrockbet_fl", [2.2, 1.7]), ("pinnacle", [1.91, 1.91]), ("draftkings", [1.9, 1.9])]:
        books.append({"key": key, "last_update": "2026-10-26T11:59:00Z", "markets": [
            {"key": "h2h", "outcomes": [{"name": n, "price": p} for n, p in zip(["Demo A", "Demo B"], prices)]}]})
    return {"id": "synthetic", "sport_key": "tennis_demo", "commence_time": "2026-10-27T12:00:00Z",
            "home_team": "Demo A", "away_team": "Demo B", "bookmakers": books}


class EngineTests(unittest.TestCase):
    def test_margin_removal_and_ev(self):
        result = compare([event()], NOW, rules=RULES)["comparisons"]
        self.assertAlmostEqual(result[0]["consensus_probability"], .5)
        self.assertAlmostEqual(result[0]["expected_return_per_dollar"], .1)
        self.assertEqual(result[1]["status"], "pass")

    def test_target_not_in_consensus(self):
        item = event()
        item["bookmakers"][0]["markets"][0]["outcomes"][0]["price"] = 10
        self.assertEqual(compare([item], NOW, rules=RULES)["comparisons"][0]["consensus_probability"], .5)

    def test_unverified_rules_rejected(self):
        self.assertFalse(compare([event()], NOW)["comparisons"])

    def test_stale_future_started_and_wrong_state_rejected(self):
        for mode in ["stale", "future", "started", "wrong_state", "duplicate", "incomplete", "nan"]:
            item = event()
            if mode == "stale":
                item["bookmakers"][0]["last_update"] = "2026-10-26T11:00:00Z"
            elif mode == "future":
                item["bookmakers"][0]["last_update"] = "2026-10-26T12:01:00Z"
            elif mode == "started":
                item["commence_time"] = "2026-10-26T12:00:00Z"
            elif mode == "wrong_state":
                item["bookmakers"][0]["key"] = "hardrockbet"
            elif mode == "duplicate":
                item["bookmakers"].append(copy.deepcopy(item["bookmakers"][1]))
            elif mode == "incomplete":
                item["bookmakers"][0]["markets"][0]["outcomes"].pop()
            else:
                item["bookmakers"][0]["markets"][0]["outcomes"][0]["price"] = float("nan")
            with self.subTest(mode=mode):
                self.assertFalse(compare([item], NOW, rules=RULES)["comparisons"])

    def test_different_rules_excluded(self):
        self.assertFalse(compare([event()], NOW, rules=dict(RULES, pinnacle="different"))["comparisons"])

    def test_invalid_prices(self):
        for value in [0, 1, -110, float("inf")]:
            with self.assertRaises(ValueError):
                decimal_odds(value)

    def test_bounded_backfill(self):
        self.assertEqual(len(list(days("2024-02-28", "2024-03-01"))), 3)
        with self.assertRaises(ValueError):
            list(days("2020-01-01", "2026-01-01"))

    def test_raw_archive_preserves_nested_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "test.sqlite3")
            payload = {"statistics": [{"stat_value": None}], "pointbypoint": [1, 2]}
            archive(db, "test", "fixture", payload)
            archive(db, "test", "fixture", payload)
            with sqlite3.connect(db) as connection:
                rows = connection.execute("SELECT payload FROM snapshots").fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(json.loads(rows[0][0]), payload)

    @patch.dict("os.environ", {"ODDS_API_KEY": "secret"})
    @patch("tennis_edge.data.get_json")
    def test_historical_request_uses_florida_decimal(self, get):
        odds("tennis_demo", "2026-10-25T12:00:00Z")
        url, params = get.call_args.args
        self.assertIn("historical/sports/tennis_demo/odds", url)
        self.assertIn("hardrockbet_fl", params["bookmakers"])
        self.assertEqual(params["oddsFormat"], "decimal")

    @patch.dict("os.environ", {"TENNIS_API_KEY": "secret"})
    @patch("tennis_edge.data.get_json", return_value={"success": 0})
    def test_provider_failure(self, get):
        with self.assertRaises(RuntimeError):
            tennis("get_players", player_key="123")

    @patch("tennis_edge.data.urlopen", side_effect=HTTPError("https://x?apiKey=secret", 401, "secret", {}, None))
    def test_http_errors_redact_credentials(self, get):
        with self.assertRaises(RuntimeError) as error:
            get_json("https://x", {"apiKey": "secret"})
        self.assertNotIn("secret", str(error.exception))


if __name__ == "__main__":
    unittest.main()
