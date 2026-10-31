import unittest
from holdout_validation import DEFAULT_CONFIG, config_fingerprint, evaluate_holdout

class HoldoutValidationTests(unittest.TestCase):
    def test_frozen_config_fingerprint_deterministic(self):
        self.assertEqual(config_fingerprint(DEFAULT_CONFIG),
                         config_fingerprint(dict(reversed(list(DEFAULT_CONFIG.items())))))

    def test_holdout_boundaries(self):
        result = evaluate_holdout([100 + i * .1 for i in range(180)], holdout_size=60)
        self.assertEqual(result["holdout_start_index"], 120)
        self.assertEqual(result["holdout_end_index_exclusive"], 180)
        self.assertTrue(result["research_only"])
        self.assertTrue(result["comparison"]["research_only"])

    def test_insufficient_data(self):
        with self.assertRaises(ValueError):
            evaluate_holdout([100.0] * 119)

    def test_reject_unrecognized_strategy(self):
        cfg = dict(DEFAULT_CONFIG, strategy="unreviewed_strategy")
        with self.assertRaises(ValueError):
            evaluate_holdout([100.0] * 120, config=cfg)

    def test_reject_excess_allocation(self):
        cfg = dict(DEFAULT_CONFIG, max_allocation=0.5)
        with self.assertRaises(ValueError):
            evaluate_holdout([100.0] * 120, config=cfg)

if __name__ == "__main__":
    unittest.main()
