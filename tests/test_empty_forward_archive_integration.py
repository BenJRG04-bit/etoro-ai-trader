import unittest
from unittest.mock import Mock
from run_forward_batch_audit import run_batch
from forward_evidence_quality import assess_forward_evidence_quality

class EmptyForwardArchiveIntegrationTests(unittest.TestCase):
    def test_empty_archive_returns_safe_audit_without_network(self):
        fetch = Mock(side_effect=AssertionError("Network must not be used"))
        result = run_batch([], fetcher=fetch)
        fetch.assert_not_called()
        self.assertEqual(result["status"], "RESEARCH_AUDIT")
        self.assertEqual(result["snapshot_count"], 0)
        self.assertFalse(result["orders_allowed"])

    def test_empty_archive_does_not_imply_trading_readiness(self):
        result = run_batch([], fetcher=Mock(side_effect=AssertionError("No fetch")))
        self.assertFalse(result["live_trading_approved"])

    def test_empty_archive_reports_zero_observed(self):
        result = run_batch([], fetcher=Mock(side_effect=AssertionError("No fetch")))
        self.assertEqual(result["observed_snapshots"], 0)
        self.assertEqual(result["pending_snapshots"], 0)

if __name__ == "__main__":
    unittest.main()
