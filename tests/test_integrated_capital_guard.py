import unittest
from backtest import backtest

def positive(_closes):
    return {"decision": "POSITIVE_RESEARCH"}

class IntegratedCapitalGuardTests(unittest.TestCase):
    def test_default_legacy_behavior_preserved(self):
        result = backtest([100.0] * 80, assessment_fn=positive)
        self.assertFalse(result["capital_guard_enabled"])
        self.assertFalse(result["stopped"])

    def test_profit_giveback_halts(self):
        # A 120% rise at 5% allocation lifts account equity above the
        # 5% profit-lock trigger; a subsequent 90% fall gives back over
        # half of those gains without requiring an invalid zero price.
        prices = [100.0] * 60 + [220.0, 22.0] + [22.0] * 10
        result = backtest(prices, assessment_fn=positive, use_capital_guard=True)
        self.assertTrue(result["capital_guard_enabled"])
        self.assertTrue(result["stopped"])
        self.assertIn(result["halt_reason"], ("PROFIT_GIVEBACK", "MAX_DRAWDOWN"))

    def test_guard_no_halt_flat_prices(self):
        result = backtest([100.0] * 80, assessment_fn=positive,
                          fee_rate=0, use_capital_guard=True)
        self.assertFalse(result["stopped"])
        self.assertIsNone(result["halt_reason"])

if __name__ == "__main__":
    unittest.main()
