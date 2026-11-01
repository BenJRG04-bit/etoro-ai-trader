import unittest
from forward_archive_health import assess_archive_health

class ArchiveHealthTests(unittest.TestCase):
    def setUp(self):
        self.audit = {"status": "RESEARCH_AUDIT", "research_only": True,
                      "orders_allowed": False, "live_trading_approved": False,
                      "snapshot_count": 2, "observed_snapshots": 1,
                      "pending_snapshots": 1, "unavailable_snapshots": 0,
                      "rejected_snapshots": 0,
                      "results": [{"snapshot_date": "2026-10-29", "status": "OBSERVED"},
                                  {"snapshot_date": "2026-10-30", "status": "PENDING"}]}
        self.quality = {"status": "RESEARCH_EVIDENCE_ONLY", "research_only": True,
                        "orders_allowed": False, "live_trading_approved": False,
                        "observed_snapshot_dates": 1}

    def test_reports_insufficient_evidence(self):
        r = assess_archive_health(self.audit, self.quality)
        self.assertEqual(r["status"], "NEEDS_MORE_EVIDENCE")
        self.assertIn("minimum_observed_snapshots", r["issues"])

    def test_coverage_ok_with_relaxed_minimum(self):
        r = assess_archive_health(self.audit, self.quality, minimum_observed=1)
        self.assertEqual(r["status"], "COVERAGE_OK")
        self.assertFalse(r["orders_allowed"])

    def test_empty_archive_not_ok(self):
        self.audit.update(snapshot_count=0, observed_snapshots=0, pending_snapshots=0, results=[])
        self.quality["observed_snapshot_dates"] = 0
        r = assess_archive_health(self.audit, self.quality)
        self.assertIn("has_archived_snapshots", r["issues"])

    def test_disagreed_totals_fail_closed(self):
        self.audit["observed_snapshots"] = 2
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality)

    def test_evidence_disagreement_fail_closed(self):
        self.quality["observed_snapshot_dates"] = 2
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality)

    def test_duplicate_dates_fail_closed(self):
        self.audit["results"][1]["snapshot_date"] = "2026-10-29"
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality)

    def test_unsafe_report_rejected(self):
        self.quality["orders_allowed"] = True
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality)

    def test_unknown_status_rejected(self):
        self.audit["results"][1]["status"] = "PROFIT"
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality)

    def test_pending_threshold_flags_archive(self):
        r = assess_archive_health(self.audit, self.quality, minimum_observed=1, maximum_pending_fraction=0.2)
        self.assertIn("pending_fraction_acceptable", r["issues"])

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            assess_archive_health(self.audit, self.quality, maximum_pending_fraction=-0.1)

if __name__ == "__main__":
    unittest.main()
