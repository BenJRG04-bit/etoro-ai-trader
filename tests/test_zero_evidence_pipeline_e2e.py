"""Real-module integration test for zero-evidence research pipeline.

No network, broker, orders, mocks, or simulated trading profits.
"""
import unittest
from datetime import date
from council_history_trends import summarize_council_history
from council_history_quality import assess_history_quality
from forward_batch_audit import audit_forward_snapshots
from forward_evidence_quality import assess_forward_evidence
from forward_archive_health import assess_archive_health
from research_readiness import assess_research_readiness
from archive_freshness import assess_archive_freshness
from readiness_consistency import validate_readiness_consistency
from readiness_artifact_contract import validate_readiness_artifact
from research_readiness_dashboard import render_readiness_dashboard

def pipeline():
    def forbidden_fetch(*args, **kwargs):
        raise AssertionError("No network expected for empty evidence")
    history = summarize_council_history([])
    audit = audit_forward_snapshots([], forbidden_fetch)
    quality = assess_forward_evidence(audit)
    health = assess_archive_health(audit, quality)
    readiness = assess_research_readiness(history, audit, quality)
    freshness = assess_archive_freshness(history, audit, as_of=date.today().isoformat())
    readiness["archive_freshness"] = freshness
    if freshness["status"] != "ARCHIVES_CURRENT":
        readiness["status"] = "MORE_EVIDENCE_REQUIRED"
        readiness["issues"] = sorted(set(readiness["issues"] + freshness["issues"]))
    return history, audit, quality, health, readiness

class ZeroEvidenceEndToEndTests(unittest.TestCase):
    def test_real_modules_agree_on_no_evidence(self):
        history, audit, quality, health, readiness = pipeline()
        self.assertEqual(history["selected_report_dates"], 0)
        self.assertEqual(audit["snapshot_count"], 0)
        self.assertEqual(quality["observed_snapshot_dates"], 0)
        self.assertEqual(health["status"], "NEEDS_MORE_EVIDENCE")
        self.assertEqual(readiness["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertIn("HISTORY_MISSING_OR_STALE", readiness["issues"])
        self.assertIn("FORWARD_MISSING_OR_STALE", readiness["issues"])
        self.assertEqual(validate_readiness_consistency(readiness)["status"], "CONSISTENT_RESEARCH_ONLY")

    def test_actual_report_renders_and_validates(self):
        readiness = pipeline()[-1]
        self.assertEqual(validate_readiness_artifact(readiness)["status"], "CONTENT_VALIDATED")
        page = render_readiness_dashboard(readiness)
        self.assertIn("MORE_EVIDENCE_REQUIRED", page)
        self.assertIn("NO ORDERS OR LIVE TRADING", page)

    def test_no_live_trading_permission_anywhere(self):
        for report in pipeline():
            self.assertIs(report["research_only"], True)
            self.assertIs(report["orders_allowed"], False)
            self.assertIs(report["live_trading_approved"], False)

if __name__ == "__main__":
    unittest.main()
