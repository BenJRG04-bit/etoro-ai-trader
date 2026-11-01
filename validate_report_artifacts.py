"""Offline report artifact contract checks for scheduled research workflows."""
import json
from pathlib import Path

REQUIRED = {
    "council_history_report.json": "RESEARCH_ACCOUNTABILITY_HISTORY",
    "council_history_quality.json": None,
    "research_readiness_report.json": None,
}

def validate_report_artifact(path):
    source = Path(path)
    if source.name not in REQUIRED:
        raise ValueError("Unexpected artifact name")
    report = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Artifact must contain an object")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe artifact")
    expected = REQUIRED[source.name]
    if expected and report.get("status") != expected:
        raise ValueError("Unexpected artifact status")
    if source.name == "council_history_quality.json" and report.get("status") not in ("COVERAGE_OK", "NEEDS_MORE_EVIDENCE"):
        raise ValueError("Unexpected history quality status")
    if source.name == "research_readiness_report.json" and report.get("status") not in ("RESEARCH_COVERAGE_READY", "MORE_EVIDENCE_REQUIRED"):
        raise ValueError("Unexpected readiness status")
    return {"file": source.name, "status": report["status"], "valid": True,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False}

if __name__ == "__main__":
    import sys
    for filename in sys.argv[1:]:
        print(json.dumps(validate_report_artifact(filename)))
