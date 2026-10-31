import unittest
from scenario_suite import sample_scenarios, run_scenario_suite

class ScenarioSuiteTests(unittest.TestCase):
    def test_scenario_names_and_lengths(self):
        scenarios = sample_scenarios()
        self.assertEqual(set(scenarios), {"rising", "falling", "sideways", "shock", "crash_recovery", "volatile"})
        for prices in scenarios.values():
            self.assertEqual(len(prices), 180)
            self.assertTrue(all(price > 0 for price in prices))

    def test_comparison_is_research_only(self):
        result = run_scenario_suite()
        self.assertTrue(result["research_only"])
        for comparison in result["scenarios"].values():
            self.assertTrue(comparison["research_only"])
            self.assertLessEqual(comparison["baseline"]["max_allocation"], 0.05)
            self.assertLessEqual(comparison["regime_aware"]["max_allocation"], 0.05)

    def test_invalid_allocation_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario_suite(max_allocation=0.5)

    def test_reject_short_series(self):
        with self.assertRaises(ValueError):
            sample_scenarios(61)

if __name__ == "__main__":
    unittest.main()
