import unittest
from forward_baseline_comparison import compare_to_baseline


def audit(rows):
    return {"status": "RESEARCH_AUDIT", "results": rows, "research_only": True, "orders_allowed": False, "live_trading_approved": False}


def observed(date, change, original=True, confirmed=False):
    return {"status": "OBSERVED", "snapshot_date": date, "evaluation": {"observations": {"AAPL": {"status": "OBSERVED", "next_close_return": change, "original_positive_at_snapshot": original, "confirmed_positive_at_snapshot": confirmed}}}}


class ForwardBaselineTests(unittest.TestCase):
    def test_empty_is_explicit_not_profitable(self):
        r = compare_to_baseline(audit([]))
        self.assertIsNone(r["comparisons"]["original"]["descriptive_difference"])
        self.assertFalse(r["enough_dates_for_review"])
        self.assertFalse(r["orders_allowed"])

    def test_observed_direction_baseline(self):
        r = compare_to_baseline(audit([observed("2026-10-29", .02), observed("2026-10-30", -.01, False)]), minimum_dates=2)
        self.assertEqual(r["comparisons"]["original"]["signal_up_fraction"], 1.0)
        self.assertEqual(r["comparisons"]["original"]["same_dates_market_up_fraction"], .5)
        self.assertTrue(r["enough_dates_for_review"])

    def test_duplicate_date_rejected(self):
        with self.assertRaises(ValueError):
            compare_to_baseline(audit([observed("2026-10-30", .01)] * 2))

    def test_unsafe_flags_rejected(self):
        r = audit([])
        r["orders_allowed"] = True
        with self.assertRaises(ValueError):
            compare_to_baseline(r)

    def test_nonfinite_return_rejected(self):
        with self.assertRaises(ValueError):
            compare_to_baseline(audit([observed("2026-10-30", float("nan"))]))

    def test_no_positive_signals_is_not_zero_accuracy(self):
        r = compare_to_baseline(audit([observed("2026-10-30", .01, False)]))
        self.assertIsNone(r["comparisons"]["original"]["signal_up_fraction"])


if __name__ == "__main__":
    unittest.main()
