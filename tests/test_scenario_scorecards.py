import unittest
from scenario_scorecards import run_scenario_scorecards


class ScenarioScorecardTests(unittest.TestCase):
    def test_six_scenarios_with_three_strategies(self):
        result = run_scenario_scorecards()
        self.assertEqual(result["scenario_count"], 6)
        self.assertEqual(set(result["scenarios"]), {
            "rising", "falling", "sideways", "shock",
            "crash_recovery", "volatile"
        })
        for scorecard in result["scenarios"].values():
            self.assertEqual(set(("baseline", "regime_aware",
                                  "capped_buy_and_hold")) -
                             set(scorecard), set())
            self.assertTrue(scorecard["research_only"])
            self.assertFalse(scorecard["live_trading_approved"])

    def test_zero_allocation_never_changes_equity(self):
        result = run_scenario_scorecards(max_allocation=0)
        for scorecard in result["scenarios"].values():
            for name in ("baseline", "regime_aware", "capped_buy_and_hold"):
                self.assertEqual(scorecard[name]["end_equity"], 1000.0)

    def test_excess_allocation_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario_scorecards(max_allocation=0.5)


if __name__ == "__main__":
    unittest.main()
