"""Create conservative forward evidence summary from archived audit report."""
import json
import sys
from forward_evidence_quality import assess_forward_evidence

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python run_forward_evidence_quality.py <audit.json>")
    with open(sys.argv[1], encoding="utf-8") as handle:
        audit = json.load(handle)
    if audit.get("status") != "RESEARCH_AUDIT":
        print(json.dumps({"status": "UNAVAILABLE", "research_only": True,
                          "orders_allowed": False, "live_trading_approved": False,
                          "reason": "Forward audit unavailable"}, indent=2))
    else:
        print(json.dumps(assess_forward_evidence(audit), indent=2))
