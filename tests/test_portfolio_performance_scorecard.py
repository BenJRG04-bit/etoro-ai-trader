import unittest
from portfolio_performance_scorecard import build_scorecard


def sample():
    audit = {"maximum_drawdown_fraction": .02, "peak_profit_given_back_fraction": .3,
             "longest_underwater_observations": 5, "research_only": True,
             "orders_allowed": False, "live_trading_approved": False}
    policy = {"end_equity": 101, "return_fraction": .01, "rebalance_events": 2,
              "max_observed_total_allocation": .05, "profit_protection_audit": audit,
              "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    return {"status": "EXPLORATORY_ONLY", "research_only": True, "orders_allowed": False,
            "live_trading_approved": False, "comparison": {"research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "scenarios": {"0.001": {"council_guarded": policy, "equal_weight_capped_hold": policy,
                                   "council_minus_hold": 0}}}}


class PerformanceScorecardTests(unittest.TestCase):
    def test_valid_scorecard_is_research_only(self):
        result = build_scorecard(sample())
        self.assertEqual(result["status"], "HISTORICAL_DESCRIPTIVE_ONLY")
        self.assertFalse(result["orders_allowed"])
        self.assertEqual(result["fee_scenarios"]["0.001"]["strategies"]["council_guarded"]["peak_profit_given_back_fraction"], .3)

    def test_unavailable_remains_unavailable(self):
        r = sample()
        r["status"] = "UNAVAILABLE"
        self.assertEqual(build_scorecard(r)["status"], "UNAVAILABLE")

    def test_rejects_missing_audit(self):
        r = sample()
        del r["comparison"]["scenarios"]["0.001"]["council_guarded"]["profit_protection_audit"]
        with self.assertRaises(ValueError):
            build_scorecard(r)

    def test_rejects_unsafe_input(self):
        r = sample()
        r["orders_allowed"] = True
        with self.assertRaises(ValueError):
            build_scorecard(r)


if __name__ == "__main__":
    unittest.main()
