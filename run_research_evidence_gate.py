"""Compile fail-closed research evidence status from prior local reports."""
import json
from pathlib import Path
from research_evidence_gate import evaluate_research_evidence

def run():
    audit = json.loads(Path("decision_quality_audit.json").read_text(encoding="utf-8"))
    rolling = json.loads(Path("rolling_decision_audit.json").read_text(encoding="utf-8"))
    return evaluate_research_evidence(audit, rolling)

if __name__ == "__main__":
    try:
        report = run()
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        report = {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                  "blockers": ["REQUIRED_EVIDENCE_UNAVAILABLE"], "evidence_gate": "BLOCKED",
                  "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    Path("research_evidence_gate.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["evidence_gate"])
