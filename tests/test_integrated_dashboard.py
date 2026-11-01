import unittest
from research_command_centre import build_command_centre


class IntegratedDashboardTests(unittest.TestCase):
    def test_multiple_current_reports_visible(self):
        safe = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}
        page = build_command_centre({
            "central_research": {**safe, "status": "RESEARCH_CYCLE_COMPLETE", "asset_count": 5, "as_of_date": "2026-10-30"},
            "small_budget": {**safe, "status": "EXPLORATORY_SMALL_BUDGET_ONLY", "budgets": {"20.0": {}, "40.0": {}, "100.0": {}}},
        })
        self.assertIn("RESEARCH_CYCLE_COMPLETE", page)
        self.assertIn("EXPLORATORY_SMALL_BUDGET_ONLY", page)
        self.assertIn("20.0", page)
        self.assertIn("NOT_AVAILABLE", page)
        self.assertIn("LIVE TRADING NOT APPROVED", page)


if __name__ == "__main__":
    unittest.main()
