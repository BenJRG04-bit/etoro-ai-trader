import unittest
from project_et import analyse_prices, risk_gate

class ResearchTests(unittest.TestCase):
    def test_uptrend(self):
        self.assertEqual(analyse_prices("AAPL", list(range(1, 81)))["signal"], "UPTREND")
    def test_missing_data(self):
        self.assertEqual(analyse_prices("SPY", [100] * 5)["signal"], "NO_DATA")
    def test_unknown_ticker(self):
        with self.assertRaises(ValueError):
            analyse_prices("BAD", [100] * 60)
    def test_drawdown_limit(self):
        self.assertFalse(risk_gate(100, 89, 0.01, 0.02)[0])
    def test_position_limit(self):
        self.assertFalse(risk_gate(100, 99, 0.06, 0.02)[0])
    def test_experimental_limit(self):
        self.assertFalse(risk_gate(100, 99, 0.02, 0.11)[0])
    def test_valid_research_allocation(self):
        self.assertTrue(risk_gate(100, 99, 0.02, 0.05)[0])

if __name__ == "__main__":
    unittest.main()
