import unittest
from research_dashboard import render_dashboard

class WeeklyStrategyDashboardTests(unittest.TestCase):
    def test_shows_later_strategy_and_fee_stress(self):
        reports = {
            "strategies": {"assets": {
                "SPY": {"status": "EXPLORATORY_ONLY", "evaluation": {"segments": {
                    "later_holdout": {"scenarios": {
                        "0.001": {"council_guarded": {"end_equity": 101.11}, "capped_hold": {"end_equity": 103.33}},
                        "0.005": {"council_guarded": {"end_equity": 100.77}},
                    }}
                }}}
            }}
        }
        page = render_dashboard(reports, generated_at="test")
        self.assertIn("£101.11", page)
        self.assertIn("£103.33", page)
        self.assertIn("£100.77", page)
        self.assertIn("Later council higher fee", page)
        self.assertIn("1/7", page)

    def test_missing_strategy_report_explicit_na(self):
        page = render_dashboard({"paper": {"assets": {"SPY": {"status": "UNAVAILABLE"}}}})
        self.assertIn("SPY", page)
        self.assertIn("N/A", page)
        self.assertIn("strategies", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

if __name__ == "__main__":
    unittest.main()
