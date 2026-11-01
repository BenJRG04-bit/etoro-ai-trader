import unittest
from copy import deepcopy
from historical_prices import WATCHLIST
from council_history_quality import assess_history_quality

class CouncilHistoryQualityTests(unittest.TestCase):
    def setUp(self):
        self.history = {"status": "RESEARCH_ACCOUNTABILITY_HISTORY", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "selected_report_dates": 1, "first_date": "2026-10-30", "last_date": "2026-10-30",
            "assets": {ticker: {"observations": 1} for ticker in WATCHLIST},
            "timeline": [{"date": "2026-10-30", "assets": {ticker: {
                "status": "OBSERVED_RESEARCH", "original": "MIXED_RESEARCH",
                "confirmed": "MIXED_RESEARCH", "risk_veto": False,
                "mixed_perspectives": False} for ticker in WATCHLIST}}]}

    def test_coverage_not_proof(self):
        result = assess_history_quality(self.history)
        self.assertEqual(result["status"], "NEEDS_MORE_EVIDENCE")
        self.assertFalse(result["orders_allowed"])

    def test_low_threshold_coverage(self):
        result = assess_history_quality(self.history, minimum_dates=1)
        self.assertEqual(result["status"], "COVERAGE_OK")

    def test_missing_asset_flagged(self):
        self.history["timeline"][0]["assets"]["SPY"] = {"status": "UNAVAILABLE"}
        self.history["assets"]["SPY"]["observations"] = 0
        result = assess_history_quality(self.history, minimum_dates=1)
        self.assertIn("EXCESS_MISSING_SPY", result["issues"])

    def test_rejects_live_trading(self):
        self.history["live_trading_approved"] = True
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_unsorted_duplicate_dates(self):
        self.history["timeline"].append(deepcopy(self.history["timeline"][0]))
        self.history["selected_report_dates"] = 2
        self.history["assets"] = {ticker: {"observations": 2} for ticker in WATCHLIST}
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_bad_summary(self):
        self.history["assets"]["SPY"]["observations"] = 99
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_bad_veto(self):
        self.history["timeline"][0]["assets"]["SPY"]["risk_veto"] = True
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_bad_date_boundary(self):
        self.history["first_date"] = "2026-10-29"
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_missing_asset(self):
        self.history["timeline"][0]["assets"].pop("SPY")
        with self.assertRaises(ValueError):
            assess_history_quality(self.history)

    def test_rejects_bad_threshold(self):
        with self.assertRaises(ValueError):
            assess_history_quality(self.history, maximum_missing_fraction=-0.1)

if __name__ == "__main__":
    unittest.main()
