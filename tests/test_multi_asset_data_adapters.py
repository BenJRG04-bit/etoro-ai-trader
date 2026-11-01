import unittest
from datetime import date, timedelta
from multi_asset_data_adapters import research_data_plan, validate_research_history


class MultiAssetAdapterTests(unittest.TestCase):
    def test_fx_mapping_not_assumed_executable(self):
        plan = research_data_plan("EURUSD")
        self.assertEqual(plan["provider_symbol_candidate"], "EURUSD=X")
        self.assertFalse(plan["history_validated"])
        self.assertFalse(plan["broker_orders_allowed"])

    def test_crypto_mapping(self):
        self.assertEqual(research_data_plan("BTC")["provider_symbol_candidate"], "BTC-USD")

    def test_direct_oil_blocked(self):
        self.assertEqual(research_data_plan("OIL")["status"], "BLOCKED_MAPPING_UNVERIFIED")
        with self.assertRaises(ValueError):
            validate_research_history("OIL", [], [])

    def test_unknown_blocked(self):
        with self.assertRaises(ValueError):
            research_data_plan("UNKNOWN")

    def test_valid_history_does_not_imply_executable_prices(self):
        days = [(date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(120)]
        report = validate_research_history("BTC", days, [100 + i for i in range(120)])
        self.assertTrue(report["shape_validated"])
        self.assertFalse(report["provider_provenance_validated"])
        self.assertFalse(report["execution_quote_comparable"])

    def test_missing_or_reordered_history_rejected(self):
        days = [(date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(120)]
        with self.assertRaises(ValueError):
            validate_research_history("ETH", days, [1.0] * 119)
        with self.assertRaises(ValueError):
            validate_research_history("ETH", days[::-1], [1.0] * 120)
        with self.assertRaises(ValueError):
            validate_research_history("ETH", days, [1.0] * 119 + [float("nan")])


if __name__ == "__main__":
    unittest.main()
