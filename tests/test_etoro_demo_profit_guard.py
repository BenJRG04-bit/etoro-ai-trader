import unittest
from etoro_demo_profit_guard import assess_demo_profit_exit


class ProfitGuardTests(unittest.TestCase):
    def check(self, pnl, **overrides):
        args = dict(account="demo", symbol="ETHEUR", invested_usd=100,
                    unrealized_pnl_usd=pnl, data_age_seconds=10)
        args.update(overrides)
        return assess_demo_profit_exit(**args)

    def test_take_profit(self):
        self.assertEqual(self.check(5)["decision"], "PROPOSE_TAKE_PROFIT")

    def test_stop_loss(self):
        self.assertEqual(self.check(-5)["decision"], "PROPOSE_STOP_LOSS")

    def test_hold(self):
        self.assertEqual(self.check(1)["decision"], "HOLD_MONITOR")

    def test_no_automatic_execution(self):
        report = self.check(100)
        self.assertFalse(report["broker_order_sent"])
        self.assertFalse(report["position_modified"])
        self.assertTrue(report["requires_explicit_broker_edit_approval"])

    def test_reject_real_and_stale(self):
        self.assertEqual(self.check(10, account="real")["decision"], "BLOCKED")
        self.assertEqual(self.check(10, data_age_seconds=None)["decision"], "BLOCKED")
        self.assertEqual(self.check(10, data_age_seconds=121)["decision"], "BLOCKED")

    def test_reject_invalid(self):
        self.assertEqual(self.check(float("nan"))["decision"], "BLOCKED")
        self.assertEqual(self.check(5, invested_usd=0)["decision"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
