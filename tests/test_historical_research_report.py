import unittest
from historical_research_report import summarize_research


class HistoricalResearchReportTests(unittest.TestCase):
    def test_summary_and_no_live_approval(self):
        sample = {
            "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
            "assets": {
                "SPY": {"status": "EXPLORATORY_ONLY", "evaluation": {
                    "windows": [
                        {"baseline_return_fraction": 0.01,
                         "regime_return_fraction": 0.02,
                         "benchmark_return_fraction": 0.015},
                        {"baseline_return_fraction": -0.01,
                         "regime_return_fraction": -0.02,
                         "benchmark_return_fraction": -0.01},
                    ]}},
                "NVDA": {"status": "DATA_OR_EVALUATION_UNAVAILABLE",
                         "error_type": "ValueError"},
            },
        }
        report = summarize_research(sample)
        self.assertFalse(report["live_trading_approved"])
        self.assertEqual(report["assets"]["SPY"]["adaptive_wins_vs_hold"], 1)
        self.assertEqual(report["assets"]["SPY"]["mean_adaptive_return_fraction"], 0)
        self.assertEqual(report["assets"]["NVDA"]["status"], "UNAVAILABLE")

    def test_empty_windows_not_success(self):
        sample = {"mode": "HISTORICAL_RESEARCH_NO_ORDERS",
                  "assets": {"AAPL": {"status": "EXPLORATORY_ONLY",
                                      "evaluation": {"windows": []}}}}
        self.assertEqual(summarize_research(sample)["assets"]["AAPL"]["status"],
                         "UNAVAILABLE")

    def test_reject_wrong_report(self):
        with self.assertRaises(ValueError):
            summarize_research({"mode": "LIVE_TRADING", "assets": {}})


if __name__ == "__main__":
    unittest.main()
