import unittest
from execution_cost_study import cost_scenario, study

class CostScenarioTests(unittest.TestCase):
    def test_minimum(self):
        self.assertEqual(cost_scenario(20, count=5)["status"], "BELOW_ASSUMED_MINIMUM")
    def test_capped(self):
        result = cost_scenario(100)
        self.assertEqual(result["total_exposure_cap"], 5)
        self.assertFalse(result["orders_allowed"])
    def test_spread(self):
        self.assertGreater(cost_scenario(100, spread=.01)["estimated_roundtrip_cost"], cost_scenario(100, spread=0)["estimated_roundtrip_cost"])
    def test_validation(self):
        with self.assertRaises(ValueError):
            cost_scenario(20, exposure=.06)
    def test_matrix(self):
        self.assertEqual(len(study()["scenarios"]), 12)
