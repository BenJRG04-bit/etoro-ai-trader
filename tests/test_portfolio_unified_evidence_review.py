import unittest
from portfolio_unified_evidence_review import review_evidence


def reports():
    p = {"research_only": True, "orders_allowed": False, "live_trading_approved": False,
         "status": "HISTORICAL_DESCRIPTIVE_ONLY", "fee_scenarios": {"0.001": {"strategies": {
         "council_guarded": {"ending_equity": 101, "max_drawdown_fraction": .01},
         "equal_weight_capped_hold": {"ending_equity": 102, "max_drawdown_fraction": .02}}}}}
    s = {"research_only": True, "orders_allowed": False, "live_trading_approved": False,
         "status": "DESCRIPTIVE_STRESS_REVIEW", "issues": [], "fee_scenarios": {"0.001": {
         "council_guarded": {"worst_scenario_drawdown_fraction": .03, "any_capital_guard_halt": False},
         "equal_weight_capped_hold": {"worst_scenario_drawdown_fraction": .04, "any_capital_guard_halt": False}}}}
    return p, s


class UnifiedEvidenceTests(unittest.TestCase):
    def test_good_historical_inputs_still_require_forward_evidence(self):
        r = review_evidence(*reports())
        self.assertEqual(r["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertFalse(r["strategy_approved"])
        self.assertIn("NO_INDEPENDENT_FORWARD_PROFITABILITY_EVIDENCE", r["blockers"])
        self.assertEqual(r["historical_comparisons"]["0.001"]["council_minus_benchmark_end_equity"], -1)

    def test_stress_issues_block(self):
        p, s = reports()
        s["issues"] = ["EXPOSURE_LIMIT_EXCEEDED"]
        r = review_evidence(p, s)
        self.assertIn("STRESS_SAFETY_ISSUES", r["blockers"])

    def test_unavailable_stress_blocks(self):
        p, s = reports()
        s["status"] = "UNAVAILABLE"
        self.assertIn("STRESS_REVIEW_NOT_CLEAN", review_evidence(p, s)["blockers"])

    def test_fee_mismatch_blocks(self):
        p, s = reports()
        s["fee_scenarios"]["0.005"] = s["fee_scenarios"]["0.001"]
        self.assertIn("FEE_COVERAGE_MISMATCH", review_evidence(p, s)["blockers"])

    def test_unsafe_flags_rejected(self):
        p, s = reports()
        p["orders_allowed"] = True
        with self.assertRaises(ValueError):
            review_evidence(p, s)


if __name__ == "__main__":
    unittest.main()
