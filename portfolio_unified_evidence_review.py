"""Conservative combined evidence review. No ranking as profitable, no trade permissions."""
import json
from pathlib import Path


def review_evidence(performance, stress):
    flags = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}
    for label, report in (("performance", performance), ("stress", stress)):
        if not isinstance(report, dict) or any(report.get(key) is not value for key, value in flags.items()):
            raise ValueError("Unsafe " + label + " report")
    blockers = []
    if performance.get("status") != "HISTORICAL_DESCRIPTIVE_ONLY":
        blockers.append("PERFORMANCE_NOT_AVAILABLE")
    if stress.get("status") != "DESCRIPTIVE_STRESS_REVIEW":
        blockers.append("STRESS_REVIEW_NOT_CLEAN")
    if stress.get("issues"):
        blockers.append("STRESS_SAFETY_ISSUES")
    fee_rows = performance.get("fee_scenarios", {})
    stress_rows = stress.get("fee_scenarios", {})
    if not isinstance(fee_rows, dict) or not isinstance(stress_rows, dict) or not fee_rows or set(fee_rows) != set(stress_rows):
        blockers.append("FEE_COVERAGE_MISMATCH")
    if not blockers:
        for fee in fee_rows:
            perf = fee_rows[fee].get("strategies", {})
            stressed = stress_rows[fee]
            if set(perf) != {"council_guarded", "equal_weight_capped_hold"} or set(stressed) != set(perf):
                blockers.append("POLICY_COVERAGE_MISMATCH")
                break
    comparisons = {}
    if not blockers:
        for fee in sorted(fee_rows):
            council = fee_rows[fee]["strategies"]["council_guarded"]
            benchmark = fee_rows[fee]["strategies"]["equal_weight_capped_hold"]
            comparisons[fee] = {
                "council_minus_benchmark_end_equity": round(council["ending_equity"] - benchmark["ending_equity"], 4),
                "council_max_drawdown_fraction": council["max_drawdown_fraction"],
                "benchmark_max_drawdown_fraction": benchmark["max_drawdown_fraction"],
                "council_worst_synthetic_drawdown_fraction": stressed["council_guarded"]["worst_scenario_drawdown_fraction"],
                "benchmark_worst_synthetic_drawdown_fraction": stressed["equal_weight_capped_hold"]["worst_scenario_drawdown_fraction"],
                "council_any_capital_guard_halt": stressed[fee]["council_guarded"]["any_capital_guard_halt"],
            }
    blockers.append("NO_INDEPENDENT_FORWARD_PROFITABILITY_EVIDENCE")
    return {**flags, "status": "MORE_EVIDENCE_REQUIRED", "blockers": blockers,
            "historical_comparisons": comparisons,
            "strategy_approved": False,
            "limitations": "Descriptive in-sample and synthetic risk review only. No independent forward profitability proof. Not a trading recommendation, strategy selection, or live authorization."}


if __name__ == "__main__":
    performance = json.loads(Path("portfolio_performance_scorecard.json").read_text(encoding="utf-8"))
    stress = json.loads(Path("portfolio_stress_resilience.json").read_text(encoding="utf-8"))
    report = review_evidence(performance, stress)
    Path("portfolio_unified_evidence_review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"], report["blockers"])
