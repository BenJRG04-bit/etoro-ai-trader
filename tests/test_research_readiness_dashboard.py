import json
import tempfile
import unittest
from pathlib import Path
from research_readiness_dashboard import render_readiness_dashboard, build_readiness_dashboard

class ReadinessDashboardTests(unittest.TestCase):
    def setUp(self):
        self.report = {"status": "MORE_EVIDENCE_REQUIRED", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "issues": ["HISTORY_COVERAGE_NOT_READY"],
            "checks": {"history": {"status": "NEEDS_MORE_EVIDENCE", "dates": 2,
                         "issues": ["INSUFFICIENT_ARCHIVED_DATES"], "research_only": True,
                         "orders_allowed": False, "live_trading_approved": False},
                       "forward": {"status": "COVERAGE_OK", "observed_snapshots": 21,
                         "issues": [], "research_only": True, "orders_allowed": False,
                         "live_trading_approved": False}}}

    def test_renders_component_status(self):
        page = render_readiness_dashboard(self.report)
        self.assertIn("HISTORY_COVERAGE_NOT_READY", page)
        self.assertIn("21", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

    def test_rejects_unsafe_report(self):
        self.report["orders_allowed"] = True
        with self.assertRaises(ValueError):
            render_readiness_dashboard(self.report)

    def test_rejects_unsafe_component(self):
        self.report["checks"]["forward"]["live_trading_approved"] = True
        with self.assertRaises(ValueError):
            render_readiness_dashboard(self.report)

    def test_rejects_contradictory_ready_status(self):
        self.report["status"] = "RESEARCH_COVERAGE_READY"
        with self.assertRaises(ValueError):
            render_readiness_dashboard(self.report)

    def test_rejects_ready_without_checks(self):
        self.report["status"] = "RESEARCH_COVERAGE_READY"
        self.report["issues"] = []
        self.report["checks"] = {}
        with self.assertRaises(ValueError):
            render_readiness_dashboard(self.report)

    def test_missing_inputs_are_visible(self):
        self.report["checks"] = {}
        page = render_readiness_dashboard(self.report)
        self.assertIn("Report unavailable", page)

    def test_escapes_untrusted_issue(self):
        self.report["issues"] = ["<script>alert(1)</script>"]
        page = render_readiness_dashboard(self.report)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_writes_dashboard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "research_readiness_report.json").write_text(json.dumps(self.report))
            output = build_readiness_dashboard(folder)
            self.assertTrue(Path(output).exists())

if __name__ == "__main__":
    unittest.main()
