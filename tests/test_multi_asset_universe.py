import unittest

from multi_asset_universe import (ALL_NEW_SYMBOLS, CRYPTO, FOREX, COMMODITIES,
                                  COMMODITY_ETFS, BOND_ETFS, MIN_EXPOSURE_USD,
                                  multi_asset_research_plan)


class MultiAssetUniverseTests(unittest.TestCase):
    def test_unique_verified_symbols(self):
        self.assertEqual(len(ALL_NEW_SYMBOLS), 27)
        self.assertEqual(len(set(ALL_NEW_SYMBOLS)), 27)

    def test_cost_thresholds_not_assumed_equal(self):
        for ticker in FOREX + COMMODITIES:
            self.assertEqual(MIN_EXPOSURE_USD[ticker], 1000)
        for ticker in CRYPTO + COMMODITY_ETFS + BOND_ETFS:
            self.assertEqual(MIN_EXPOSURE_USD[ticker], 10)

    def test_no_pretend_training_or_trading(self):
        report = multi_asset_research_plan()
        self.assertFalse(report["data_collection_implemented"])
        self.assertFalse(report["model_training_implemented_for_new_assets"])
        self.assertFalse(report["broker_orders_allowed"])
        self.assertFalse(report["demo_trading_approved"])
        self.assertFalse(report["live_trading_approved"])


if __name__ == "__main__":
    unittest.main()
