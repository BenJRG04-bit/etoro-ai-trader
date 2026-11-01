import unittest
from forward_evidence_quality import assess_forward_evidence

class ForwardEvidenceQualityTests(unittest.TestCase):
    def entry(self, stamp, change=0.01, original=True, confirmed=False):
        return {"status": "OBSERVED", "snapshot_date": stamp,
                "evaluation": {"observations": {"SPY": {
                    "status": "OBSERVED", "next_close_return": change,
                    "original_positive_at_snapshot": original,
                    "confirmed_positive_at_snapshot": confirmed}}}}

    def test_counts_only_observed_signals(self):
        audit = {"status": "RESEARCH_AUDIT", "results": [
            self.entry("2026-01-01"), self.entry("2026-01-02", -0.01),
            {"status": "PENDING", "snapshot_date": "2026-01-03"}]}
        r = assess_forward_evidence(audit, minimum_dates=2, minimum_signals=2)
        a = r["policies"]["original"]["SPY"]
        self.assertEqual(a["signals"], 2)
        self.assertEqual(a["up"], 1)
        self.assertEqual(a["down"], 1)
        self.assertTrue(a["minimum_evidence_met"])
        self.assertFalse(r["orders_allowed"])

    def test_insufficient_samples(self):
        r = assess_forward_evidence({"status": "RESEARCH_AUDIT",
                                     "results": [self.entry("2026-01-01")]})
        self.assertFalse(r["policies"]["original"]["SPY"]["minimum_evidence_met"])

    def test_no_positive_signal_not_counted(self):
        r = assess_forward_evidence({"status": "RESEARCH_AUDIT",
                                     "results": [self.entry("2026-01-01", original=False)]})
        self.assertEqual(r["policies"]["original"], {})

    def test_confirmation_is_separate(self):
        r = assess_forward_evidence({"status": "RESEARCH_AUDIT",
                                     "results": [self.entry("2026-01-01", confirmed=True)]})
        self.assertEqual(r["policies"]["confirmed"]["SPY"]["signals"], 1)

    def test_duplicate_observed_date_rejected(self):
        with self.assertRaises(ValueError):
            assess_forward_evidence({"status": "RESEARCH_AUDIT",
                                     "results": [self.entry("2026-01-01"), self.entry("2026-01-01")]})

    def test_reject_invalid_audit(self):
        with self.assertRaises(ValueError):
            assess_forward_evidence({})

    def test_zero_move_not_a_win(self):
        r = assess_forward_evidence({"status": "RESEARCH_AUDIT",
                                     "results": [self.entry("2026-01-01", change=0)]})
        self.assertEqual(r["policies"]["original"]["SPY"]["flat"], 1)
        self.assertEqual(r["policies"]["original"]["SPY"]["up"], 0)

    def test_empty_archive_is_explicit(self):
        r = assess_forward_evidence({"status": "RESEARCH_AUDIT", "results": []})
        self.assertEqual(r["observed_snapshot_dates"], 0)
        self.assertEqual(r["policies"]["original"], {})

if __name__ == "__main__":
    unittest.main()
