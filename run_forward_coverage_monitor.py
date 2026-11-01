"""Build forward coverage report from an already generated batch audit."""
import json
import sys
from pathlib import Path
from forward_coverage_monitor import summarize_forward_coverage, SAFE

if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("forward_batch_audit_report.json")
    try:
        report = summarize_forward_coverage(json.loads(source.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report = {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                  "blockers": ["FORWARD_COVERAGE_UNAVAILABLE"],
                  "forward_validation": "NOT_ESTABLISHED", "live_trading_readiness": "BLOCKED", **SAFE}
    Path("forward_coverage_monitor.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
