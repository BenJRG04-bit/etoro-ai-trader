import unittest
from profit_protection_audit import audit_equity_curve


class ProfitProtectionAuditTests(unittest.TestCase):
    def test_profit_given_back_after_peak(self):
        r = audit_equity_curve([100, 120, 110])
        self.assertEqual(r["peak_profit_given_back_fraction"], .5)
        self.assertEqual(r["maximum_drawdown_fraction"], round(10 / 120, 6))
        self.assertEqual(r["drawdown_peak_index"], 1)
        self.assertEqual(r["drawdown_trough_index"], 2)

    def test_no_peak_profit_is_undefined(self):
        r = audit_equity_curve([100, 95, 90])
        self.assertIsNone(r["peak_profit_given_back_fraction"])
        self.assertFalse(r["orders_allowed"])

    def test_recovered_peak(self):
        r = audit_equity_curve([100, 110, 100, 115])
        self.assertEqual(r["peak_profit_given_back_fraction"], 0)
        self.assertEqual(r["longest_underwater_observations"], 1)

    def test_invalid_curve_fails(self):
        for curve in ([], [100], [100, 0], [100, float("nan")], [100, True]):
            with self.subTest(curve=curve), self.assertRaises(ValueError):
                audit_equity_curve(curve)


if __name__ == "__main__":
    unittest.main()
