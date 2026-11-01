"""Record actual research input provenance without treating missing inputs as success."""
import hashlib
import json
from pathlib import Path

INPUTS = {
    "history": "inputs/history/council_history_report.json",
    "forward_audit": "inputs/forward/forward_batch_audit_report.json",
    "forward_quality": "inputs/forward/forward_evidence_quality_report.json",
}
def inspect_inputs(root="."):
    root = Path(root)
    entries = {}
    for label, relative in INPUTS.items():
        path = root / relative
        item = {"path": relative, "status": "MISSING"}
        try:
            data = path.read_bytes()
            report = json.loads(data)
            if not isinstance(report, dict):
                raise ValueError("Expected JSON object")
            safe = (report.get("research_only") is True and
                    report.get("orders_allowed") is False and
                    report.get("live_trading_approved") is False)
            item["status"] = "VALID_SAFE_JSON" if safe else "UNSAFE_JSON"
            item["sha256"] = hashlib.sha256(data).hexdigest()
            item["bytes"] = len(data)
            item["report_status"] = report.get("status")
        except FileNotFoundError:
            pass
        except (OSError, ValueError, UnicodeError, TypeError):
            item["status"] = "UNREADABLE_OR_INVALID_JSON"
        entries[label] = item
    missing = [label for label, item in entries.items() if item["status"] != "VALID_SAFE_JSON"]
    return {"status": "INPUTS_PRESENT" if not missing else "INPUTS_INCOMPLETE",
            "inputs": entries, "blockers": missing,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Input presence and basic safety only; SHA256 hashes identify content but do not establish correctness, authenticity, research skill or financial performance."}

if __name__ == "__main__":
    print(json.dumps(inspect_inputs(), indent=2))
