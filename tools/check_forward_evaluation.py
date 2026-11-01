"""Research-only forward evaluation readiness checks.

Usage: python tools/check_forward_evaluation.py path/to/forward_evaluation_report.json
No broker connections, secrets, or order endpoints are used.
"""
import json
import sys
from pathlib import Path

EXPECTED = {"AAPL", "MSFT", "NVDA", "SPY", "VTI"}
PENDING = "PENDING_NEW_CLOSE"


def check(report):
    if not isinstance(report, dict):
        raise ValueError("Report must be a JSON object")
    for key, safe in (("research_only", True), ("orders_allowed", False),
                      ("live_trading_approved", False)):
        if report.get(key) is not safe:
            raise ValueError(f"Unsafe or missing top-level flag: {key}")
    evaluation = report.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ValueError("Missing evaluation")
    for key, safe in (("research_only", True), ("orders_allowed", False),
                      ("live_trading_approved", False)):
        if evaluation.get(key) is not safe:
            raise ValueError(f"Unsafe or missing evaluation flag: {key}")
    observations = evaluation.get("observations")
    if not isinstance(observations, dict) or set(observations) != EXPECTED:
        raise ValueError("Unexpected or missing watchlist assets")
    pending = [ticker for ticker, item in observations.items()
               if isinstance(item, dict) and item.get("status") == PENDING]
    if len(pending) == len(EXPECTED):
        if report.get("status") != "PENDING":
            raise ValueError("All observations pending but report status differs")
        return "PENDING: waiting for next market close; no performance claim"
    if pending:
        return f"PARTIAL: {len(pending)} of {len(EXPECTED)} observations pending; manual review required"
    return "REVIEW_REQUIRED: new observations present; verify data before interpreting results"


def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/check_forward_evaluation.py report.json", file=sys.stderr)
        return 2
    try:
        report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(check(report))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
