"""Generate machine-readable forward archive health from research reports."""
import json
import sys
from forward_archive_health import assess_archive_health

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python run_forward_archive_health.py <audit.json> <evidence.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        audit = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        evidence = json.load(f)
    print(json.dumps(assess_archive_health(audit, evidence), indent=2))
