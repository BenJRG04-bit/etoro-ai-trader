import copy
import unittest
from portfolio_stress_resilience import assess_stress_resilience


def sample():
    row = {"end_equity": 99.0, "max_drawdown_fraction": .01, "profit_given_back_fraction": None,
           "halted": False, "max_observed_total_allocation": .05}
    return {"status": "SYNTHETIC_STRESS_ONLY", "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "cases": {case: {"0.001": {policy: copy.deepcopy(row) for policy in ("council_guarded", "equal_weight_capped_hold")}}
                      for case in ("unchanged", "drop_10pct", "drop_25pct")}}


class StressResilienceTests(unittest.TestCase):
    def test_valid_scenarios_are_descriptive(self):
        r = assess_stress_resilience(sample())
        self.assertEqual(r["status"], "DESCRIPTIVE_STRESS_REVIEW")
        self.assertFalse(r["orders_allowed"])

    def test_exposure_limit_detects_issue(self):
        r = assess_stress_resilience(sample(), maximum_exposure=.04)
        self.assertEqual(r["status"], "SAFETY_ISSUES")
        self.assertTrue(r["issues"])

    def test_missing_scenario_fails(self):
        r = sample()
        del r["cases"]["drop_25pct"]
        with self.assertRaises(ValueError):
            assess_stress_resilience(r)

    def test_missing_policy_fails(self):
        r = sample()
        del r["cases"]["drop_10pct"]["0.001"]["council_guarded"]
        with self.assertRaises(ValueError):
            assess_stress_resilience(r)

    def test_unsafe_flags_fail(self):
        r = sample()
        r["orders_allowed"] = True
        with self.assertRaises(ValueError):
            assess_stress_resilience(r)

    def test_nonfinite_metrics_fail(self):
        r = sample()
        r["cases"]["unchanged"]["0.001"]["council_guarded"]["end_equity"] = float("nan")
        with self.assertRaises(ValueError):
            assess_stress_resilience(r)

    def test_unavailable_is_not_success(self):
        r = {"status": "UNAVAILABLE", "research_only": True, "orders_allowed": False, "live_trading_approved": False}
        self.assertEqual(assess_stress_resilience(r)["status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
