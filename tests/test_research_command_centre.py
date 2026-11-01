import unittest
from research_command_centre import build_command_centre


class CommandCentreTests(unittest.TestCase):
    def test_missing_reports_are_visible(self):
        page = build_command_centre({})
        self.assertIn("NOT_AVAILABLE", page)
        self.assertIn("ORDERS DISABLED", page)

    def test_unsafe_reports_are_blocked(self):
        page = build_command_centre({"central_research": {"status": "OK", "orders_allowed": True}})
        self.assertIn("BLOCKED_UNSAFE_REPORT", page)

    def test_escapes_untrusted_content(self):
        report = {"status": "<script>alert(1)</script>", "research_only": True,
                  "orders_allowed": False, "live_trading_approved": False, "asset_count": 1}
        page = build_command_centre({"central_research": report})
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_valid_report_status(self):
        report = {"status": "RESEARCH_CYCLE_COMPLETE", "research_only": True,
                  "orders_allowed": False, "live_trading_approved": False, "asset_count": 5}
        page = build_command_centre({"central_research": report})
        self.assertIn("RESEARCH_CYCLE_COMPLETE", page)
        self.assertIn("Assets: 5", page)


if __name__ == "__main__":
    unittest.main()
