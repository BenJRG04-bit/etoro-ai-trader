"""Fail-closed readiness summary across independent read-only research reports.

Research readiness is NOT financial performance validation or live-trading approval.
"""
from datetime import date
from council_history_quality import assess_history_quality
from forward_archive_health import assess_archive_health

def assess_research_readiness(history, forward_audit, forward_quality, *, minimum_history_dates=20, minimum_forward_observed=20):
    history_result = assess_history_quality(history, minimum_dates=minimum_history_dates)
    forward_result = assess_archive_health(forward_audit, forward_quality, minimum_observed=minimum_forward_observed)
    if history_result.get("research_only") is not True or history_result.get("orders_allowed") is not False:
        raise ValueError("Unsafe history assessment")
    if forward_result.get("research_only") is not True or forward_result.get("orders_allowed") is not False:
        raise ValueError("Unsafe forward assessment")
    history_ok = history_result["status"] == "COVERAGE_OK"
    forward_ok = forward_result["status"] == "COVERAGE_OK"
    issues = []
    if not history_ok:
        issues.append("HISTORY_COVERAGE_NOT_READY")
    if not forward_ok:
        issues.append("FORWARD_COVERAGE_NOT_READY")
    return {"status": "RESEARCH_COVERAGE_READY" if not issues else "MORE_EVIDENCE_REQUIRED",
            "checks": {"history": history_result, "forward": forward_result},
            "issues": issues, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Research data coverage only. Neither readiness nor passing tests establishes predictive skill, net profitability, execution realism or live trading approval."}
