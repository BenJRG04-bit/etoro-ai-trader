import unittest
from capital_guard import CapitalGuard

class CapitalGuardTests(unittest.TestCase):
    def test_no_halt_in_small_fluctuation(self):
        guard = CapitalGuard(100)
        self.assertFalse(guard.observe(98)["halted"])

    def test_drawdown_halts_and_stays_halted(self):
        guard = CapitalGuard(100)
        self.assertEqual(guard.observe(89)["reason"], "MAX_DRAWDOWN")
        self.assertTrue(guard.observe(120)["halted"])

    def test_profit_giveback_halts(self):
        guard = CapitalGuard(100)
        guard.observe(110)
        self.assertEqual(guard.observe(104)["reason"], "PROFIT_GIVEBACK")

    def test_gain_without_large_giveback_not_halted(self):
        guard = CapitalGuard(100)
        guard.observe(110)
        self.assertFalse(guard.observe(108)["halted"])

    def test_invalid_equity_rejected(self):
        guard = CapitalGuard(100)
        with self.assertRaises(ValueError):
            guard.observe(float("nan"))

    def test_max_drawdown_limit(self):
        with self.assertRaises(ValueError):
            CapitalGuard(100, max_drawdown=0.5)

if __name__ == "__main__":
    unittest.main()
