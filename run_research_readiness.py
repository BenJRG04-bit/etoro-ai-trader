"""Produce an end-to-end read-only research readiness report from archived artifacts."""
import json
import sys
from pathlib import Path
from research_readiness import assess_research_readiness

def run_readiness(history_path, audit_path, evidence_path):
    paths = (history_path, audit_path, evidence_path)
    reports = []
    for path in paths:
        with Path(path).open(encoding="utf-8") as handle:
            reports.append(json.load(handle))
    return assess_research_readiness(*reports)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python run_research_readiness.py <history.json> <forward_audit.json> <forward_evidence.json>")
    print(json.dumps(run_readiness(*sys.argv[1:]), indent=2))
