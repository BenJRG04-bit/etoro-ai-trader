import unittest
from datetime import date
from forward_provenance_gate import check_snapshot_provenance

SAFE = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}

class ProvenanceGateTests(unittest.TestCase):
    def doc(self, day):
        return {"status": "SNAPSHOT_RESEARCH_ONLY", "snapshot": {"snapshot_date": day}, **SAFE}
    def test_old_snapshot_eligible(self):
        result = check_snapshot_provenance(self.doc("2026-10-01"), observed_at=date(2026, 10, 3))
        self.assertEqual(result["status"], "ELIGIBLE_FOR_FORWARD_EVALUATION")
        self.assertFalse(result["orders_allowed"])
    def test_same_day_pending(self):
        result = check_snapshot_provenance(self.doc("2026-10-01"), observed_at=date(2026, 10, 1))
        self.assertEqual(result["status"], "PENDING")
    def test_future_snapshot_pending(self):
        result = check_snapshot_provenance(self.doc("2026-10-03"), observed_at=date(2026, 10, 1))
        self.assertEqual(result["status"], "PENDING")
    def test_unsafe_source_rejected(self):
        document = self.doc("2026-10-01")
        document["orders_allowed"] = True
        with self.assertRaises(ValueError):
            check_snapshot_provenance(document, observed_at=date(2026, 10, 3))
    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            check_snapshot_provenance(self.doc("not-a-date"), observed_at=date(2026, 10, 3))
    def test_minimum_age_validation(self):
        with self.assertRaises(ValueError):
            check_snapshot_provenance(self.doc("2026-10-01"), minimum_age_days=0)
