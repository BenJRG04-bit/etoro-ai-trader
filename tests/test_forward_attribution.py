import unittest
from forward_attribution import forward_attribution


def audit():
    return {"status": "RESEARCH_AUDIT", "research_only": True, "orders_allowed": False,
            "live_trading_approved": False, "results": [
                {"snapshot_date": "2026-10-30", "status": "OBSERVED", "evaluation": {"observations": {
                    "AAPL": {"status": "OBSERVED", "next_close_return": .02, "original_positive_at_snapshot": True, "confirmed_positive_at_snapshot": False},
                    "SPY": {"status": "OBSERVED", "next_close_return": -.01, "original_positive_at_snapshot": False, "confirmed_positive_at_snapshot": True}}}},
                {"snapshot_date": "2026-10-31", "status": "PENDING"}]}


class ForwardAttributionTests(unittest.TestCase):
    def test_pending_does_not_count(self):
        r = forward_attribution(audit())
        self.assertEqual(r["observed_dates"], 1)
        self.assertEqual(r["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertFalse(r["strategy_approved"])

    def test_paired_direction_and_returns(self):
        r = forward_attribution(audit())["policies"]
        self.assertEqual(r["original"]["signal_up_fraction"], 1.0)
        self.assertEqual(r["confirmed"]["signal_up_fraction"], 0.0)
        self.assertEqual(r["original"]["selection_minus_unconditional_mean_return"], .015)

    def test_duplicate_dates_rejected(self):
        a = audit()
        a["results"].append(a["results"][0])
        with self.assertRaises(ValueError):
            forward_attribution(a)

    def test_nonfinite_returns_rejected(self):
        a = audit()
        a["results"][0]["evaluation"]["observations"]["AAPL"]["next_close_return"] = float("nan")
        with self.assertRaises(ValueError):
            forward_attribution(a)

    def test_missing_flag_rejected(self):
        a = audit()
        del a["results"][0]["evaluation"]["observations"]["AAPL"]["confirmed_positive_at_snapshot"]
        with self.assertRaises(ValueError):
            forward_attribution(a)

    def test_unsafe_report_rejected(self):
        a = audit()
        a["orders_allowed"] = True
        with self.assertRaises(ValueError):
            forward_attribution(a)

    def test_zero_evidence_stays_unapproved(self):
        a = audit()
        a["results"] = []
        r = forward_attribution(a)
        self.assertIsNone(r["policies"]["original"]["signal_up_fraction"])
        self.assertFalse(r["strategy_approved"])


if __name__ == "__main__":
    unittest.main()
