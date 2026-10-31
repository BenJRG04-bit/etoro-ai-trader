import unittest
from paper_account import simulate_paper_account

class PaperAccountTests(unittest.TestCase):
    def test_flat_market_preserves_notional_cash(self):
        result = simulate_paper_account([100.0] * 80)
        self.assertEqual(result["start_equity"], 100.0)
        self.assertEqual(result["end_equity"], 100.0)
        self.assertEqual(result["rebalance_events"], 0)

    def test_crash_never_approves_orders(self):
        result = simulate_paper_account([100.0] * 60 + [70.0] * 20)
        self.assertFalse(result["orders_allowed"])
        self.assertFalse(result["live_trading_approved"])
        self.assertTrue(result["capital_guard_enabled"])

    def test_bad_prices_rejected(self):
        with self.assertRaises(ValueError):
            simulate_paper_account([100.0] * 79 + [0.0])

    def test_invalid_cash_rejected(self):
        with self.assertRaises(ValueError):
            simulate_paper_account([100.0] * 80, starting_cash=-100.0)

if __name__ == "__main__":
    unittest.main()
