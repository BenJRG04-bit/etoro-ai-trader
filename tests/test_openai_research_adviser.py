"""No-key unit tests for fail-closed AI adviser and prompt-injection resistance."""
import copy
import json
from urllib.error import HTTPError
import unittest
from datetime import datetime, timezone

from historical_prices import WATCHLIST
from openai_research_adviser import (
    SAFE, build_openai_request, run_openai_adviser, VALID_BRAINS,
)


def report():
    rows = {}
    for ticker in WATCHLIST:
        rows[ticker] = {
            "status": "EXPLORATORY_ONLY", "as_of_date": "2026-10-30",
            "latest_pattern": {
                **SAFE,
                "signal": "RESEARCH_CANDIDATE" if ticker == "AAPL" else "RISK_BLOCKED",
                "pattern_score": 5 if ticker == "AAPL" else 2,
                "pattern_labels": ["BREAKOUT_ABOVE_PRIOR_20D_HIGH"] if ticker == "AAPL" else [],
                "risk_vetoes": [] if ticker == "AAPL" else ["HIGH_DAILY_VOLATILITY"],
                "indicators": {"rsi14": 52.1, "momentum20_fraction": .02},
            },
        }
    return {"mode": "DAILY_PATTERN_RESEARCH_NO_ORDERS", **SAFE, "assets": rows}


def response(*, override=None):
    items = []
    for ticker in WATCHLIST:
        items.append({
            "ticker": ticker,
            "verdict": "INVESTIGATE_FURTHER" if ticker == "AAPL" else "AVOID",
            "rationale": "Price-only signal; further independent validation needed.",
            "perspectives": [
                {"name": name, "assessment": "No independently confirmed edge."}
                for name in VALID_BRAINS
            ],
        })
    if override:
        override(items)
    return {"status": "completed", "output": [{
        "type": "message", "role": "assistant", "content": [{
            "type": "output_text",
            "text": json.dumps({"assessments": items,
                                "overall_caution": "No trading authority."}),
        }],
    }]}


class OpenAIResearchAdviserTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 19, tzinfo=timezone.utc)

    def test_missing_key_returns_no_assessments_without_network(self):
        result = run_openai_adviser(report(), api_key="",
                                   transport=lambda *a: self.fail("network"),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "NOT_CONFIGURED")
        self.assertFalse(result["orders_allowed"])
        self.assertEqual(result["assessments"], [])

    def test_valid_response_six_perspectives_research_only(self):
        captured = []
        def transport(payload, secret):
            captured.append((payload, secret))
            return response()
        result = run_openai_adviser(report(), api_key="test-fake",
                                   transport=transport, now_utc=self.now)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertEqual(len(result["assessments"]), 5)
        self.assertEqual(len(result["assessments"][0]["perspectives"]), 6)
        self.assertEqual(result["assessments"][0]["verdict"], "INVESTIGATE_FURTHER")
        self.assertFalse(result["orders_allowed"])
        self.assertFalse(result["demo_trading_approved"])
        self.assertFalse(result["live_trading_approved"])
        self.assertEqual(captured[0][0]["store"], False)
        self.assertEqual(captured[0][0]["text"]["format"]["type"], "json_schema")
        self.assertNotIn("test-fake", json.dumps(captured[0][0]))

    def test_model_cannot_override_blocked_risk(self):
        def make_unsafe(items):
            items[1]["verdict"] = "INVESTIGATE_FURTHER"
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: response(override=make_unsafe),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(result["assessments"], [])

    def test_model_cannot_output_order_commands(self):
        def add_order(items):
            items[0]["place_order"] = {"account": "real", "size": 99999}
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: response(override=add_order),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_model_cannot_skip_asset_or_duplicate_asset(self):
        def duplicate(items):
            items[1]["ticker"] = "AAPL"
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: response(override=duplicate),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_model_cannot_skip_council_member(self):
        def skip(items):
            items[0]["perspectives"].pop()
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: response(override=skip),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_rejects_incomplete_model_response(self):
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: {
                                       "status": "incomplete", "output": []},
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_http_401_is_safe_and_identifies_authentication(self):
        def rejected(*args):
            raise HTTPError("https://api.openai.com/v1/responses", 401,
                            "PRIVATE SECRET RESPONSE", {}, None)
        result = run_openai_adviser(report(), api_key="private-secret",
                                   transport=rejected, now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(result["diagnostic"], {
            "stage": "OPENAI_REQUEST", "category": "AUTHENTICATION",
            "http_status": 401})
        self.assertNotIn("private-secret", json.dumps(result))
        self.assertNotIn("PRIVATE SECRET RESPONSE", json.dumps(result))

    def test_invalid_ai_response_reports_validation_stage(self):
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=lambda *_: {"status": "incomplete"},
                                   now_utc=self.now)
        self.assertEqual(result["diagnostic"]["stage"], "RESPONSE_VALIDATION")
        self.assertEqual(result["diagnostic"]["category"],
                         "INVALID_INPUT_OR_RESPONSE")

    def test_network_error_fails_closed(self):
        def offline(*args):
            raise OSError("API not reachable")
        result = run_openai_adviser(report(), api_key="fake",
                                   transport=offline, now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["orders_allowed"])

    def test_no_account_data_or_key_in_model_payload(self):
        r = report()
        r["portfolio"] = {"account": "real", "balance": 100000}
        r["secrets"] = {"api_key": "DONT_SEND"}
        sent = []
        def transport(payload, secret):
            sent.append(json.dumps(payload))
            return response()
        result = run_openai_adviser(r, api_key="fake",
                                   transport=transport, now_utc=self.now)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertNotIn("DONT_SEND", sent[0])
        self.assertNotIn("balance", sent[0])
        self.assertNotIn("portfolio", sent[0])

    def test_unsafe_input_never_calls_model(self):
        r = report()
        r["orders_allowed"] = True
        result = run_openai_adviser(r, api_key="fake",
                                   transport=lambda *_: self.fail("unsafe"),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_invalid_indicator_fails_closed(self):
        r = report()
        r["assets"]["AAPL"]["latest_pattern"]["indicators"]["rsi14"] = float("nan")
        result = run_openai_adviser(r, api_key="fake",
                                   transport=lambda *_: self.fail("unsafe"),
                                   now_utc=self.now)
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_schema_uses_strict_no_extra_fields(self):
        payload = build_openai_request([])
        schema = payload["text"]["format"]["schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["assessments"]["items"]["additionalProperties"])
        self.assertFalse(schema["properties"]["assessments"]["items"]["properties"]["perspectives"]["items"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
