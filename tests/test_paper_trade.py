import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.paper_trade import run

PRICES = {"AAPL":250,"MSFT":500,"NVDA":200,"SPY":700,"VTI":350}
class PaperTradingTests(unittest.TestCase):
    def test_baseline_is_cash_only(self):
        result = run(PRICES, 1.3, "2026-11-02")
        self.assertEqual(result["equity_gbp"], 100)
        self.assertEqual(result["trades"], [])
        self.assertFalse(result["orders_allowed"])
    def test_rejects_bad_price(self):
        with self.assertRaises(ValueError):
            run({**PRICES,"AAPL":float("nan")},1.3,"2026-11-02")
    def test_rejects_missing_asset(self):
        with self.assertRaises(ValueError):
            run({"AAPL":250},1.3,"2026-11-02")
    def test_rejects_bad_fx(self):
        with self.assertRaises(ValueError):
            run(PRICES,0,"2026-11-02")
if __name__ == "__main__":
    unittest.main()
