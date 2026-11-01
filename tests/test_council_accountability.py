import unittest
from council_accountability import explain_council
from run_council_accountability import run_accountability
from historical_prices import WATCHLIST

class CouncilAccountabilityTests(unittest.TestCase):
    def setUp(self):
        self.closes = [100.0 + i * 0.4 for i in range(80)]

    def test_six_perspectives_explained(self):
        result = explain_council(self.closes)
        self.assertEqual(len(result["perspectives"]), 6)
        self.assertEqual(sum(result["agreement"][k] for k in ("positive", "negative", "neutral")), 6)
        self.assertFalse(result["orders_allowed"])

    def test_rejects_insufficient_prices(self):
        with self.assertRaises(ValueError):
            explain_council([100.0] * 30)

    def test_rejects_invalid_price(self):
        with self.assertRaises(ValueError):
            explain_council([100.0] * 79 + [float("nan")])

    def test_detects_disagreement(self):
        def fake(closes):
            return {"status": "OK", "decision": "MIXED_RESEARCH", "regime_risk_veto": False,
                    "market_regime": "SIDEWAYS", "aggregate_score": 0.0,
                    "scores": dict(zip(("optimist", "skeptic", "historian", "trend_hunter",
                                        "risk_manager", "strategist"), (1, -1, 0, 0, 0, 0)))}
        result = explain_council(self.closes, fake)
        self.assertTrue(result["agreement"]["mixed_signs"])

    def test_rejects_missing_scores(self):
        def fake(closes):
            return {"status": "OK", "decision": "MIXED_RESEARCH",
                    "regime_risk_veto": False, "scores": {}}
        with self.assertRaises(ValueError):
            explain_council(self.closes, fake)

    def test_report_all_watchlist_assets(self):
        def fetch(ticker, period="2y"):
            return {"ticker": ticker, "dates": [f"2026-01-{i:02d}" for i in range(1, 29)] +
                    [f"2026-02-{i:02d}" for i in range(1, 29)] +
                    [f"2026-03-{i:02d}" for i in range(1, 25)],
                    "closes": self.closes}
        result = run_accountability(fetch)
        self.assertEqual(set(result["assets"]), set(WATCHLIST))
        self.assertTrue(all(v["status"] == "OBSERVED_RESEARCH" for v in result["assets"].values()))

    def test_fetch_failure_is_explicit(self):
        def broken(ticker, period="2y"):
            raise OSError("offline")
        result = run_accountability(broken)
        self.assertTrue(all(v["status"] == "UNAVAILABLE" for v in result["assets"].values()))

if __name__ == "__main__":
    unittest.main()
