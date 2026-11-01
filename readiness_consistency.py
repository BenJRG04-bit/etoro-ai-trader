"""Fail-closed cross-check of combined readiness and underlying evidence reports."""
from datetime import date

def validate_readiness_consistency(report):
    if not isinstance(report, dict) or report.get("status") not in ("RESEARCH_COVERAGE_READY", "MORE_EVIDENCE_REQUIRED"):
        raise ValueError("Unknown readiness status")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe readiness report")
    issues = report.get("issues")
    if not isinstance(issues, list) or not all(isinstance(issue, str) and issue for issue in issues):
        raise ValueError("Invalid readiness issues")
    checks = report.get("checks")
    if checks is None:
        if report["status"] != "MORE_EVIDENCE_REQUIRED" or "MISSING_OR_INVALID_INPUTS" not in issues:
            raise ValueError("Missing checks without explicit failure")
        return {"status": "CONSISTENT_MISSING_INPUTS", "research_only": True,
                "orders_allowed": False, "live_trading_approved": False}
    if not isinstance(checks, dict) or set(checks) != {"history", "forward"}:
        raise ValueError("Incomplete readiness checks")
    expected = []
    for name in ("history", "forward"):
        item = checks[name]
        if not isinstance(item, dict) or item.get("status") not in ("COVERAGE_OK", "NEEDS_MORE_EVIDENCE"):
            raise ValueError("Invalid component status")
        if item.get("research_only") is not True or item.get("orders_allowed") is not False or item.get("live_trading_approved") is not False:
            raise ValueError("Unsafe component")
        if item["status"] != "COVERAGE_OK":
            expected.append(name.upper() + "_COVERAGE_NOT_READY")
    freshness = report.get("archive_freshness")
    if freshness is not None:
        if not isinstance(freshness, dict) or freshness.get("status") not in ("ARCHIVES_CURRENT", "ARCHIVES_STALE_OR_MISSING"):
            raise ValueError("Invalid freshness status")
        if freshness.get("research_only") is not True or freshness.get("orders_allowed") is not False or freshness.get("live_trading_approved") is not False:
            raise ValueError("Unsafe freshness")
        fresh_issues = freshness.get("issues")
        if not isinstance(fresh_issues, list) or not all(isinstance(issue, str) for issue in fresh_issues):
            raise ValueError("Invalid freshness issues")
        if freshness["status"] == "ARCHIVES_CURRENT" and fresh_issues:
            raise ValueError("Contradictory freshness result")
        if freshness["status"] == "ARCHIVES_STALE_OR_MISSING" and not fresh_issues:
            raise ValueError("Missing freshness reasons")
        expected.extend(fresh_issues)
    if set(expected) != set(issues) or len(issues) != len(set(issues)):
        raise ValueError("Readiness reasons disagree with components")
    ready = not expected
    if (report["status"] == "RESEARCH_COVERAGE_READY") != ready:
        raise ValueError("Readiness status disagrees with evidence")
    return {"status": "CONSISTENT_RESEARCH_ONLY", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}
