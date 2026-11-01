"""End-to-end offline smoke tests for safe report publication.

These tests deliberately use fabricated *fixtures* and never claim real observations.
"""
import json
import tempfile
import unittest
from pathlib import Path
from council_history_trends import summarize_council_history
from council_history_quality import assess_history_quality
from publish_council_history import publish_history
from research_readiness_dashboard import build_readiness_dashboard
from archive_freshness import assess_archive_freshness
from historical_prices import WATCHLIST

class PipelineSmokeTests(unittest.TestCase):
    def test_empty_history_pipeline_publishes_needs_evidence(self):
        history = summarize_council_history([])
        self.assertEqual(history["selected_report_dates"], 0)
        self.assertEqual(assess_history_quality(history)["status"], "NEEDS_MORE_EVIDENCE")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "council_history_report.json").write_text(json.dumps(history))
            output = publish_history(directory)
            self.assertTrue(Path(output).is_file())
            quality = json.loads((root / "council_history_quality.json").read_text())
            self.assertEqual(quality["status"], "NEEDS_MORE_EVIDENCE")

    def test_missing_inputs_dashboard_publishes(self):
        report = {"status": "MORE_EVIDENCE_REQUIRED",
                  "issues": ["MISSING_OR_INVALID_INPUTS"],
                  "research_only": True, "orders_allowed": False,
                  "live_trading_approved": False}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "research_readiness_report.json").write_text(json.dumps(report))
            output = build_readiness_dashboard(directory)
            self.assertIn("MISSING_OR_INVALID_INPUTS", Path(output).read_text())

    def test_empty_archives_freshness(self):
        history = summarize_council_history([])
        forward = {"status": "RESEARCH_AUDIT", "research_only": True,
                   "orders_allowed": False, "live_trading_approved": False,
                   "snapshot_count": 0, "results": []}
        result = assess_archive_freshness(history, forward, as_of="2026-11-01")
        self.assertEqual(result["status"], "ARCHIVES_STALE_OR_MISSING")

    def test_no_orders_in_published_reports(self):
        history = summarize_council_history([])
        quality = assess_history_quality(history)
        self.assertFalse(history["orders_allowed"])
        self.assertFalse(quality["live_trading_approved"])

if __name__ == "__main__":
    unittest.main()
