import unittest
from council_report_integrity import validate_council_report
from historical_prices import WATCHLIST
from six_brains import NAMES

class CouncilReportIntegrityTests(unittest.TestCase):
    def setUp(self):
        ex = {"status": "RESEARCH_EXPLANATION", "research_only": True,
              "orders_allowed": False, "live_trading_approved": False,
              "risk_veto": False, "original_decision": "MIXED_RESEARCH",
              "confirmed_decision": "MIXED_RESEARCH",
              "perspectives": {name: {"score": 0.0, "stance": "NEUTRAL"} for name in NAMES},
              "agreement": {"positive": 0, "negative": 0, "neutral": 6, "mixed_signs": False}}
        self.report = {"status": "RESEARCH_ACCOUNTABILITY_ONLY", "research_only": True,
                       "orders_allowed": False, "live_trading_approved": False,
                       "assets": {ticker: {"status": "OBSERVED_RESEARCH", "as_of": "2026-10-30",
                                          "close": 100.0, "explanation": dict(ex)} for ticker in WATCHLIST}}

    def test_valid(self):
        self.assertEqual(validate_council_report(self.report)["observed_assets"], len(WATCHLIST))

    def test_no_live_trading(self):
        self.report["live_trading_approved"] = True
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_missing_asset(self):
        self.report["assets"].pop("SPY")
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_invalid_price(self):
        self.report["assets"]["SPY"]["close"] = float("inf")
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_invalid_date(self):
        self.report["assets"]["SPY"]["as_of"] = "2026-1-2"
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_inconsistent_stance(self):
        self.report["assets"]["SPY"]["explanation"]["perspectives"] = {
            name: {"score": 0.0, "stance": "POSITIVE"} for name in NAMES}
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_inconsistent_agreement(self):
        self.report["assets"]["SPY"]["explanation"]["agreement"] = {
            "positive": 1, "negative": 0, "neutral": 5, "mixed_signs": False}
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_unavailable_asset(self):
        self.report["assets"]["SPY"] = {"status": "UNAVAILABLE", "error_type": "OSError"}
        self.assertEqual(validate_council_report(self.report)["unavailable_assets"], 1)

    def test_rejects_veto_positive(self):
        self.report["assets"]["SPY"]["explanation"] = {
            **self.report["assets"]["SPY"]["explanation"], "risk_veto": True,
            "original_decision": "POSITIVE_RESEARCH"}
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

    def test_rejects_confirmation_wait_without_positive(self):
        self.report["assets"]["SPY"]["explanation"] = {
            **self.report["assets"]["SPY"]["explanation"],
            "confirmed_decision": "WAIT_FOR_CONFIRMATION"}
        with self.assertRaises(ValueError):
            validate_council_report(self.report)

if __name__ == "__main__":
    unittest.main()
