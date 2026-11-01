"""Validate actual readiness report contents, not just artifact existence."""
import json
from pathlib import Path
from readiness_consistency import validate_readiness_consistency
from research_readiness_dashboard import render_readiness_dashboard

def validate_readiness_artifact(report):
    result = validate_readiness_consistency(report)
    page = render_readiness_dashboard(report)
    if not isinstance(page, str) or "NO ORDERS OR LIVE TRADING" not in page:
        raise ValueError("Readiness dashboard lost research-only warning")
    if report["status"] == "RESEARCH_COVERAGE_READY" and report.get("archive_freshness", {}).get("status") != "ARCHIVES_CURRENT":
        raise ValueError("Cannot claim research coverage ready without current archives")
    return {"status": "CONTENT_VALIDATED", "readiness_status": report["status"],
            "consistency_status": result["status"], "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}

def validate_readiness_file(path="research_readiness_report.json"):
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_readiness_artifact(report)

if __name__ == "__main__":
    print(json.dumps(validate_readiness_file(), indent=2))
