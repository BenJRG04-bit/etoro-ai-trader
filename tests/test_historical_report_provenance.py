"""Report must retain provenance and distinguish raw closes from total returns."""
import unittest
from historical_research_report import summarize_research


class HistoricalReportProvenanceTests(unittest.TestCase):
    def test_provenance_visible_to_reader(self):
        report = summarize_research({
            "mode": "HISTORICAL_RESEARCH_NO_ORDERS",
            "assets": {
                "AAPL": {
                    "status": "EXPLORATORY_ONLY",
                    "data_audit": {
                        "ticker": "AAPL",
                        "first_date": "2024-01-02",
                        "last_date": "2025-01-02",
                        "observation_count": 250,
                        "valid_for_total_return_comparison": False,
                    },
                    "evaluation": {"windows": [{
                        "baseline_return_fraction": 0.01,
                        "regime_return_fraction": 0.02,
                        "benchmark_return_fraction": 0.01,
                        "regime_max_drawdown_fraction": 0.03,
                    }]},
                }
            },
        })
        source = report["assets"]["AAPL"]["data_provenance"]
        self.assertEqual(source["first_date"], "2024-01-02")
        self.assertEqual(source["observation_count"], 250)
        self.assertFalse(source["total_return_validated"])
        self.assertFalse(report["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
