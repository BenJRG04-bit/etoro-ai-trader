import json
import tempfile
import unittest
from pathlib import Path
from historical_prices import WATCHLIST
from council_history_dashboard import render_council_history_dashboard, build_council_history_dashboard

class HistoryDashboardTests(unittest.TestCase):
    def setUp(self):
        self.report = {"status": "RESEARCH_ACCOUNTABILITY_HISTORY",
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "selected_report_dates": 1, "rejected_reports": 0,
            "first_date": "2026-10-30", "last_date": "2026-10-30",
            "assets": {ticker: {"observations": 1, "original_positive": 1,
                "confirmed_positive": 0, "risk_veto": 0, "mixed_perspectives": 1,
                "awaiting_confirmation": 1} for ticker in WATCHLIST},
            "timeline": [{"date": "2026-10-30", "assets": {ticker: {
                "status": "OBSERVED_RESEARCH", "original": "POSITIVE_RESEARCH",
                "confirmed": "WAIT_FOR_CONFIRMATION", "risk_veto": False}
                for ticker in WATCHLIST}}]}

    def test_renders_summary_and_timeline(self):
        page = render_council_history_dashboard(self.report)
        self.assertIn("WAIT_FOR_CONFIRMATION", page)
        self.assertIn("2026-10-30", page)
        self.assertIn("Decision frequencies", page)

    def test_rejects_order_enabled(self):
        self.report["orders_allowed"] = True
        with self.assertRaises(ValueError):
            render_council_history_dashboard(self.report)

    def test_rejects_missing_asset(self):
        self.report["assets"].pop("SPY")
        with self.assertRaises(ValueError):
            render_council_history_dashboard(self.report)

    def test_rejects_impossible_count(self):
        self.report["assets"]["SPY"]["risk_veto"] = 2
        with self.assertRaises(ValueError):
            render_council_history_dashboard(self.report)

    def test_rejects_timeline_count_mismatch(self):
        self.report["selected_report_dates"] = 2
        with self.assertRaises(ValueError):
            render_council_history_dashboard(self.report)

    def test_rejects_unsorted_dates(self):
        self.report["timeline"].append(self.report["timeline"][0])
        self.report["selected_report_dates"] = 2
        with self.assertRaises(ValueError):
            render_council_history_dashboard(self.report)

    def test_unavailable_asset(self):
        self.report["timeline"][0]["assets"]["SPY"] = {"status": "UNAVAILABLE"}
        self.assertIn("UNAVAILABLE", render_council_history_dashboard(self.report))

    def test_escapes_untrusted_decision(self):
        self.report["timeline"][0]["assets"]["SPY"]["original"] = "<script>alert(1)</script>"
        page = render_council_history_dashboard(self.report)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_writes_html(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "council_history_report.json").write_text(json.dumps(self.report))
            result = build_council_history_dashboard(folder)
            self.assertTrue(Path(result).is_file())

if __name__ == "__main__":
    unittest.main()
