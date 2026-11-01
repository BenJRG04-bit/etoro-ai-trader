"""Local-only demo review runner. Reads JSON snapshots, never makes API calls.

Usage:
python tools/run_demo_review.py research.json portfolio.json positions.json markets.json --peak-equity-usd 100000

For safety, market-open verification defaults to FALSE even if prices look fresh.
This produces a human-review document; nothing is sent to eToro.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

# Allow invocation from the repository root or from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo_decision_bridge import build_demo_review


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline demo trade review; never submits orders")
    parser.add_argument("research", type=Path)
    parser.add_argument("demo_portfolio", type=Path)
    parser.add_argument("demo_positions", type=Path)
    parser.add_argument("market_overview", type=Path)
    parser.add_argument("--peak-equity-usd", required=True, type=float,
                        help="Independently tracked historical peak; do NOT reset after losses")
    parser.add_argument("--market-open-verified", action="store_true",
                        help="Use only after independently verifying the current trading session")
    args = parser.parse_args(argv)
    try:
        payloads = []
        for path in (args.research, args.demo_portfolio, args.demo_positions, args.market_overview):
            with path.open("r", encoding="utf-8") as handle:
                payloads.append(json.load(handle))
        report = build_demo_review(
            *payloads,
            now_utc=datetime.now(timezone.utc),
            market_open_verified=args.market_open_verified,
            peak_equity_usd=args.peak_equity_usd,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in ("REVIEW_AVAILABLE", "NO_RESEARCH_CANDIDATES") else 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        print(json.dumps({"status": "BLOCKED", "reasons": ["INVALID_INPUT_FILE"],
                          "orders_submitted": 0, "research_only": True}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
