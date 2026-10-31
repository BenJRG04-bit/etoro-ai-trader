"""Historical reports must expose downside risk, not just average returns."""
import unittest
from historical_research_report import summarize_research


class HistoricalDownsideTests(unittest.TestCase):
    def test_worst_return_and_drawdown(self):
        report = summarize_research({
            "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
            "assets": {"SPY": {"status": "EXPLORATORY_ONLY",
                "evaluation": {"windows": [
                    {"baseline_return_fraction": 0.02,
                     "regime_return_fraction": 0.03,
                     "benchmark_return_fraction": 0.01,
                     "regime_max_drawdown_fraction": 0.01},
                    {"baseline_return_fraction": -0.01,
                     "regime_return_fraction": -0.04,
                     "benchmark_return_fraction": -0.02,
                     "regime_max_drawdown_fraction": 0.08},
                ]}}},
        })
        row = report["assets"]["SPY"]
        self.assertEqual(row["adaptive_worst_window_return_fraction"], -0.04)
        self.assertEqual(row["adaptive_worst_window_drawdown_fraction"], 0.08)
        self.assertFalse(report["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
