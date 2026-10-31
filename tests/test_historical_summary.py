import unittest
from historical_summary import summarize

class HistoricalSummaryTests(unittest.TestCase):
    def test_unavailable_not_mistaken_for_success(self):
        result = summarize({"assets": {"AAPL": {"status": "DATA_OR_EVALUATION_ERROR", "reason": "offline"}}})
        self.assertEqual(result["assets"][0]["status"], "UNAVAILABLE")
        self.assertTrue(result["research_only"])

    def test_window_counts_and_averages(self):
        windows = [
            {"baseline_return_fraction": 0.01, "regime_return_fraction": 0.02,
             "benchmark_return_fraction": 0.03, "regime_max_drawdown_fraction": 0.01},
            {"baseline_return_fraction": -0.01, "regime_return_fraction": -0.02,
             "benchmark_return_fraction": -0.03, "regime_max_drawdown_fraction": 0.04}
        ]
        report = {"assets": {"SPY": {"status": "OK", "evaluation": {"windows": windows}}}}
        row = summarize(report)["assets"][0]
        self.assertEqual(row["regime_better_windows"], 1)
        self.assertEqual(row["regime_worse_windows"], 1)
        self.assertEqual(row["worst_regime_window_drawdown_fraction"], 0.04)
        self.assertEqual(row["mean_regime_return_fraction"], 0.0)

    def test_no_windows(self):
        report = {"assets": {"VTI": {"status": "OK", "evaluation": {"windows": []}}}}
        self.assertEqual(summarize(report)["assets"][0]["status"], "NO_TEST_WINDOWS")

if __name__ == "__main__":
    unittest.main()
