"""Fail-closed historical portfolio comparison scorecard; never a trade signal."""
import json
from pathlib import Path


def build_scorecard(report):
    if not isinstance(report, dict) or report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe portfolio report")
    if report.get("status") != "EXPLORATORY_ONLY":
        return {"status": "UNAVAILABLE", "reason": report.get("error_type", "NO_VALID_REPORT"),
                "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    comparison = report.get("comparison")
    if not isinstance(comparison, dict) or comparison.get("research_only") is not True or comparison.get("orders_allowed") is not False or comparison.get("live_trading_approved") is not False:
        raise ValueError("Unsafe comparison")
    scenarios = comparison.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("Missing scenarios")
    rows = {}
    for fee, scenario in scenarios.items():
        if not isinstance(scenario, dict):
            raise ValueError("Invalid scenario")
        strategies = {}
        for label in ("council_guarded", "equal_weight_capped_hold"):
            result = scenario.get(label)
            if not isinstance(result, dict) or result.get("research_only") is not True or result.get("orders_allowed") is not False or result.get("live_trading_approved") is not False:
                raise ValueError("Unsafe strategy")
            audit = result.get("profit_protection_audit")
            if not isinstance(audit, dict) or audit.get("research_only") is not True or audit.get("orders_allowed") is not False or audit.get("live_trading_approved") is not False:
                raise ValueError("Missing safe profit audit")
            strategies[label] = {
                "ending_equity": result["end_equity"],
                "return_fraction": result["return_fraction"],
                "max_drawdown_fraction": audit["maximum_drawdown_fraction"],
                "peak_profit_given_back_fraction": audit["peak_profit_given_back_fraction"],
                "longest_underwater_observations": audit["longest_underwater_observations"],
                "rebalance_events": result["rebalance_events"],
                "max_observed_total_allocation": result["max_observed_total_allocation"],
            }
        rows[fee] = {"strategies": strategies, "council_minus_capped_hold_equity": scenario["council_minus_hold"]}
    return {"status": "HISTORICAL_DESCRIPTIVE_ONLY", "fee_scenarios": rows,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "In-sample retrospective simulated returns, not verified forward performance. Fixed 5% maximum exposure, simplified execution, no FX, spread, slippage, dividends or taxes. No trading approval or guaranteed profit."}


if __name__ == "__main__":
    report = json.loads(Path("portfolio_benchmark_report.json").read_text(encoding="utf-8"))
    Path("portfolio_performance_scorecard.json").write_text(json.dumps(build_scorecard(report), indent=2) + "\n", encoding="utf-8")
