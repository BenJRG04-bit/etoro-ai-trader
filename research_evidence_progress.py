"""Conservative human-readable progress summary for Project E.T. research evidence."""
import json
from pathlib import Path


def summarize(readiness):
    if not isinstance(readiness, dict):
        raise ValueError("Readiness must be a JSON object")
    if readiness.get("research_only") is not True or readiness.get("orders_allowed") is not False or readiness.get("live_trading_approved") is not False:
        raise ValueError("Unsafe or incomplete readiness flags")
    status = readiness.get("status")
    if status not in {"MORE_EVIDENCE_REQUIRED", "RESEARCH_COVERAGE_READY"}:
        raise ValueError("Unknown readiness status")
    checks = readiness.get("checks") or {}
    issues = readiness.get("issues")
    if not isinstance(issues, list) or any(not isinstance(x, str) for x in issues):
        raise ValueError("Invalid blockers")
    return {
        "status": status,
        "blockers": issues,
        "component_status": {
            "history": (checks.get("history") or {}).get("status", "UNAVAILABLE"),
            "forward": (checks.get("forward") or {}).get("status", "UNAVAILABLE"),
        },
        "coverage_target": {"distinct_history_dates": 20, "observed_forward_snapshots": 20},
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "note": "Workflow success is not predictive skill, net profitability or approval to trade. Distinct real observations must accumulate over time.",
    }


def main():
    readiness = json.loads(Path("research_readiness_report.json").read_text(encoding="utf-8"))
    summary = summarize(readiness)
    Path("research_evidence_progress.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
