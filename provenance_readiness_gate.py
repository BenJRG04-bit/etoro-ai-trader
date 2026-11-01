"""Cross-check input provenance with published readiness; fail closed."""
import json
from pathlib import Path
from readiness_consistency import validate_readiness_consistency

def verify_provenance_readiness(provenance, readiness):
    if not isinstance(provenance, dict) or provenance.get("status") not in ("INPUTS_PRESENT", "INPUTS_INCOMPLETE"):
        raise ValueError("Invalid provenance")
    if provenance.get("research_only") is not True or provenance.get("orders_allowed") is not False or provenance.get("live_trading_approved") is not False:
        raise ValueError("Unsafe provenance")
    checks = provenance.get("inputs")
    if not isinstance(checks, dict) or set(checks) != {"history", "forward_audit", "forward_quality"}:
        raise ValueError("Incomplete provenance inputs")
    missing = sorted(label for label, item in checks.items() if not isinstance(item, dict) or item.get("status") != "VALID_SAFE_JSON")
    blockers = provenance.get("blockers")
    if not isinstance(blockers, list) or sorted(blockers) != missing or len(blockers) != len(set(blockers)):
        raise ValueError("Provenance blockers inconsistent")
    if (provenance["status"] == "INPUTS_PRESENT") != (not missing):
        raise ValueError("Provenance status inconsistent")
    validate_readiness_consistency(readiness)
    if missing and readiness.get("status") == "RESEARCH_COVERAGE_READY":
        raise ValueError("Cannot be ready with missing inputs")
    if missing and "MISSING_OR_INVALID_INPUTS" not in readiness.get("issues", []):
        raise ValueError("Missing inputs not disclosed in readiness report")
    if not missing and "MISSING_OR_INVALID_INPUTS" in readiness.get("issues", []):
        raise ValueError("Readiness reports missing inputs despite complete provenance")
    return {"status": "PROVENANCE_CONSISTENT", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}

def verify_files(root="."):
    root = Path(root)
    provenance = json.loads((root / "readiness_input_provenance_report.json").read_text(encoding="utf-8"))
    readiness = json.loads((root / "research_readiness_report.json").read_text(encoding="utf-8"))
    return verify_provenance_readiness(provenance, readiness)

if __name__ == "__main__":
    print(json.dumps(verify_files(), indent=2))
