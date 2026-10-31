import unittest
from readiness_assessment import assess_research_readiness

class ReadinessAssessmentTests(unittest.TestCase):
    def test_empty_report_never_approved(self):
        result = assess_research_readiness({"assets": {}})
        self.assertEqual(result["status"], "NOT_READY_FOR_LIVE_TRADING")
        self.assertFalse(result["checks"]["all_assets_evaluated"])
        self.assertTrue(result["research_only"])

    def test_five_assets_still_not_approved(self):
        window = {"baseline_return_fraction": .01, "regime_return_fraction": .02,
                  "benchmark_return_fraction": .01, "regime_max_drawdown_fraction": 0.0}
        report = {"assets": {ticker: {"status": "OK", "evaluation": {
            "windows": [window, window]}} for ticker in
            ("AAPL", "MSFT", "NVDA", "SPY", "VTI")}}
        result = assess_research_readiness(report)
        self.assertTrue(result["checks"]["all_assets_evaluated"])
        self.assertTrue(result["checks"]["multiple_windows_each"])
        self.assertFalse(result["checks"]["independent_untouched_holdout_verified"])
        self.assertEqual(result["status"], "NOT_READY_FOR_LIVE_TRADING")

    def test_data_failure_not_silent(self):
        report = {"assets": {"AAPL": {"status": "DATA_OR_EVALUATION_ERROR",
                                     "reason": "network unavailable"}}}
        result = assess_research_readiness(report)
        self.assertIn("AAPL", result["unavailable_assets"])

if __name__ == "__main__":
    unittest.main()
