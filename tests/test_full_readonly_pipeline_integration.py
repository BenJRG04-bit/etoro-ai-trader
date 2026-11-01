"""End-to-end research-only pipeline integration with zero evidence and no network."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from council_history_trends import summarize_council_history
from council_history_quality import assess_history_quality
from run_forward_batch_audit import run_batch
from forward_evidence_quality import assess_forward_evidence
from forward_archive_health import assess_archive_health
from research_readiness import assess_research_readiness
from archive_freshness import assess_archive_freshness
from readiness_consistency import validate_readiness_consistency
from research_readiness_dashboard import build_readiness_dashboard
from workflow_diagnostics_dashboard import render_pipeline_dashboard

class FullReadOnlyPipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = Mock(side_effect=AssertionError("Empty archive must not access the internet"))
        self.history = summarize_council_history([])
        self.forward = run_batch([], fetcher=self.fetcher)
        self.quality = assess_forward_evidence(self.forward)

    def test_empty_archives_do_not_call_network(self):
        self.fetcher.assert_not_called()
        self.assertEqual(self.forward["snapshot_count"], 0)

    def test_empty_history_is_explicitly_not_ready(self):
        result = assess_history_quality(self.history)
        self.assertEqual(result["status"], "NEEDS_MORE_EVIDENCE")

    def test_empty_forward_archive_is_explicitly_not_ready(self):
        result = assess_archive_health(self.forward, self.quality)
        self.assertEqual(result["status"], "NEEDS_MORE_EVIDENCE")

    def test_combined_readiness_fails_closed(self):
        report = assess_research_readiness(self.history, self.forward, self.quality)
        self.assertEqual(report["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertIn("HISTORY_COVERAGE_NOT_READY", report["issues"])
        self.assertIn("FORWARD_COVERAGE_NOT_READY", report["issues"])
        self.assertFalse(report["orders_allowed"])

    def test_archive_freshness_fails_closed(self):
        freshness = assess_archive_freshness(self.history, self.forward)
        self.assertEqual(freshness["status"], "ARCHIVES_STALE_OR_MISSING")
        self.assertIn("FORWARD_MISSING_OR_STALE", freshness["issues"])

    def test_readiness_consistency_and_html_from_real_modules(self):
        report = assess_research_readiness(self.history, self.forward, self.quality)
        freshness = assess_archive_freshness(self.history, self.forward)
        report["archive_freshness"] = freshness
        report["issues"] = sorted(set(report["issues"] + freshness["issues"]))
        self.assertEqual(validate_readiness_consistency(report)["status"], "CONSISTENT_RESEARCH_ONLY")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "research_readiness_report.json").write_text(json.dumps(report))
            page = Path(build_readiness_dashboard(folder)).read_text()
        self.assertIn("MORE_EVIDENCE_REQUIRED", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

if __name__ == "__main__":
    unittest.main()
