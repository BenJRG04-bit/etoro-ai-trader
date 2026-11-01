import tempfile
import unittest
from pathlib import Path
import json
from forward_evidence_dashboard import render_forward_dashboard, build_forward_dashboard

class ForwardDashboardTests(unittest.TestCase):
    def setUp(self):
        self.audit = {"status": "RESEARCH_AUDIT", "orders_allowed": False,
                      "snapshot_count": 2, "observed_snapshots": 1, "pending_snapshots": 1,
                      "unavailable_snapshots": 0, "rejected_snapshots": 0,
                      "results": [{"snapshot_date": "2026-01-01", "status": "OBSERVED",
                                   "observed_assets": 5, "pending_assets": 0}]}
        self.quality = {"status": "RESEARCH_EVIDENCE_ONLY", "orders_allowed": False,
                        "policies": {"original": {"SPY": {"signals": 3, "up": 2,
                          "down": 1, "flat": 0, "distinct_signal_dates": 3,
                          "minimum_evidence_met": False}}, "confirmed": {}}}

    def test_shows_coverage_and_outcomes(self):
        page = render_forward_dashboard(self.audit, self.quality)
        self.assertIn("INSUFFICIENT SAMPLE", page)
        self.assertIn("SPY", page)
        self.assertIn("2026-01-01", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

    def test_html_escapes_untrusted_data(self):
        self.quality["policies"]["original"]["<script>alert(1)</script>"] = {
            "signals": 1, "up": 1, "down": 0, "flat": 0,
            "distinct_signal_dates": 1, "minimum_evidence_met": False}
        page = render_forward_dashboard(self.audit, self.quality)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_rejects_missing_reports(self):
        with self.assertRaises(ValueError):
            render_forward_dashboard({}, self.quality)

    def test_rejects_order_enabled_report(self):
        self.audit["orders_allowed"] = True
        with self.assertRaises(ValueError):
            render_forward_dashboard(self.audit, self.quality)

    def test_empty_archive_explicit(self):
        self.audit["results"] = []
        self.quality["policies"] = {"original": {}, "confirmed": {}}
        page = render_forward_dashboard(self.audit, self.quality)
        self.assertIn("no observed positive signals yet", page)

    def test_writes_offline_html(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "forward_batch_audit_report.json").write_text(json.dumps(self.audit))
            (p / "forward_evidence_quality_report.json").write_text(json.dumps(self.quality))
            result = build_forward_dashboard(d)
            self.assertTrue(Path(result).exists())
            self.assertNotIn("<script", Path(result).read_text())

if __name__ == "__main__":
    unittest.main()
