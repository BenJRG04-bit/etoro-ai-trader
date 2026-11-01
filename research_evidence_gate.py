"""Conservative research evidence gate; never authorizes brokerage trading."""
from math import isfinite

def evaluate_research_evidence(audit, rolling, *, minimum_windows=4):
    if type(minimum_windows) is not int or minimum_windows < 2:
        raise ValueError("Invalid minimum windows")
    if not isinstance(audit, dict) or not isinstance(rolling, dict):
        raise ValueError("Reports required")
    for report in (audit, rolling):
        if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
            raise ValueError("Unsafe source report")
    blockers = []
    if audit.get("status") != "IN_SAMPLE_ONLY_NO_TRADING_APPROVAL":
        blockers.append("DECISION_AUDIT_UNAVAILABLE")
    if rolling.get("status") != "RETROSPECTIVE_ROLLING_AUDIT_ONLY":
        blockers.append("ROLLING_AUDIT_UNAVAILABLE")
    if rolling.get("windows_evaluated", 0) < minimum_windows:
        blockers.append("INSUFFICIENT_HISTORICAL_WINDOWS")
    if audit.get("forward_validation") != "ESTABLISHED" or rolling.get("forward_validation") != "ESTABLISHED":
        blockers.append("NO_INDEPENDENT_FORWARD_VALIDATION")
    if not blockers:
        blockers.append("MANUAL_BROKER_RISK_REVIEW_REQUIRED")
    return {
        "status": "RESEARCH_ONLY_EVIDENCE_REVIEW",
        "historical_windows": rolling.get("windows_evaluated", 0),
        "historical_council_win_fraction": rolling.get("council_win_fraction"),
        "blockers": blockers,
        "evidence_gate": "BLOCKED",
        "orders_allowed": False,
        "live_trading_approved": False,
        "research_only": True,
        "limitations": "Historical windows overlap and are not independent forward evidence. "
                       "This gate never authorizes orders; forward proof and human review remain necessary.",
    }
