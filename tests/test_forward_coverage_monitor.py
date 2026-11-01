import unittest
from forward_coverage_monitor import summarize_forward_coverage

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

def audit(rows, rejected=0):
    return {"status": "RESEARCH_AUDIT", "results": rows, "snapshot_count": len(rows),
            "observed_snapshots": sum(r["status"] == "OBSERVED" for r in rows),
            "pending_snapshots": sum(r["status"] == "PENDING" for r in rows),
            "unavailable_snapshots": sum(r["status"] == "UNAVAILABLE" for r in rows),
            "rejected_snapshots": rejected, **SAFE}

class CoverageMonitorTests(unittest.TestCase):
    def test_empty_archive_reports_no_forward_evidence(self):
        result = summarize_forward_coverage(audit([]))
        self.assertIn("NO_OBSERVED_FORWARD_DATES", result["blockers"])
        self.assertEqual(result["live_trading_readiness"], "BLOCKED")
    def test_observed_and_pending_distinct(self):
        rows = [{"snapshot_date": "2026-10-01", "status": "OBSERVED"},
                {"snapshot_date": "2026-10-02", "status": "PENDING"}]
        result = summarize_forward_coverage(audit(rows))
        self.assertEqual(result["observed_dates"], 1)
        self.assertEqual(result["pending_dates"], 1)
    def test_rejected_and_unavailable_flagged(self):
        result = summarize_forward_coverage(audit(
            [{"snapshot_date": "2026-10-01", "status": "UNAVAILABLE"}], rejected=1))
        self.assertIn("REJECTED_ARCHIVED_SNAPSHOTS", result["blockers"])
        self.assertIn("UNAVAILABLE_FORWARD_EVALUATIONS", result["blockers"])
    def test_duplicate_dates_rejected(self):
        rows = [{"snapshot_date": "2026-10-01", "status": "OBSERVED"}] * 2
        with self.assertRaises(ValueError):
            summarize_forward_coverage(audit(rows))
    def test_mismatched_counts_rejected(self):
        item = audit([{"snapshot_date": "2026-10-01", "status": "OBSERVED"}])
        item["observed_snapshots"] = 0
        with self.assertRaises(ValueError):
            summarize_forward_coverage(item)
    def test_unsafe_source_rejected(self):
        item = audit([])
        item["orders_allowed"] = True
        with self.assertRaises(ValueError):
            summarize_forward_coverage(item)
