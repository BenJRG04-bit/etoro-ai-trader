"""Evaluate every selected archived pattern prediction using ONE price download.

A rolling batch prevents missed predictions during holidays, weekends and
workflow retries. Outputs one research-only JSON per archive run for the
cumulative scorecard. No orders, broker credentials or real/demo account reads.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

from historical_prices import WATCHLIST, fetch_daily_closes
from run_pattern_forward_evaluation import (
    SAFE, evaluate_pattern_forward_snapshot,
)

def run_pattern_forward_batch(archive_directory, output_directory, *,
                              fetcher=fetch_daily_closes, evaluated_at=None):
    now = datetime.now(timezone.utc) if evaluated_at is None else evaluated_at
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Aware evaluation timestamp required")
    now = now.astimezone(timezone.utc)
    input_root, output_root = Path(archive_directory), Path(output_directory)
    if not input_root.is_dir():
        raise ValueError("Missing archive input directory")
    output_root.mkdir(parents=True, exist_ok=True)
    dirs = sorted(path for path in input_root.iterdir() if path.is_dir())
    if not dirs:
        status = output_root / "status"
        status.mkdir()
        (status / "pattern_forward_evaluation.json").write_text(
            json.dumps({**SAFE, "status": "PENDING",
                        "reason": "NO_MATURE_ARCHIVES_YET"}, indent=2), encoding="utf-8")
        return {**SAFE, "status": "PENDING", "archives": 0,
                "observed": 0, "pending": 0, "unavailable": 0,
                "market_downloads": 0}

    # One strictly read-only public price download for all snapshots, instead
    # of potentially hundreds of repeated Yahoo Finance requests.
    market_error = None
    try:
        histories = {ticker: fetcher(ticker, period="2y") for ticker in WATCHLIST}
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        market_error = type(exc).__name__
        histories = None

    statuses = []
    for folder in dirs:
        result = None
        snapshot_file = folder / "pattern_forward_snapshot.json"
        try:
            if snapshot_file.exists() and histories is not None:
                with snapshot_file.open(encoding="utf-8") as source:
                    record = json.load(source)
                result = evaluate_pattern_forward_snapshot(
                    record, histories, evaluated_at=now)
            else:
                result = {**SAFE, "status": "UNAVAILABLE",
                          "reason": "MISSING_SNAPSHOT_OR_MARKET_DATA",
                          "error_type": market_error or "MissingArchive"}
        except (OSError, ValueError, TypeError, KeyError, IndexError,
                OverflowError) as exc:
            result = {**SAFE, "status": "UNAVAILABLE",
                      "reason": "ARCHIVE_OR_MARKET_VALIDATION_FAILED",
                      "error_type": type(exc).__name__}
        destination = output_root / folder.name
        destination.mkdir()
        (destination / "pattern_forward_evaluation.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8")
        statuses.append(result["status"])

    return {
        **SAFE, "status": "BATCH_COMPLETE" if "UNAVAILABLE" not in statuses else "BATCH_INCOMPLETE",
        "archives": len(statuses),
        "observed": statuses.count("OBSERVED"),
        "pending": statuses.count("PENDING"),
        "unavailable": statuses.count("UNAVAILABLE"),
        "market_downloads": 0 if market_error else len(WATCHLIST),
        "limitations": ("Archive outcomes require two future dated closes. "
                        "Repeated historical evaluations are NOT independent trials; "
                        "the accountability scorecard deduplicates signal dates. "
                        "No broker fills or live trading."),
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python run_pattern_forward_batch.py <archive_dir> <output_dir>")
    try:
        result = run_pattern_forward_batch(sys.argv[1], sys.argv[2])
    except (OSError, ValueError, TypeError) as exc:
        result = {**SAFE, "status": "BATCH_INCOMPLETE",
                  "archives": 0, "observed": 0, "pending": 0,
                  "unavailable": 1, "error_type": type(exc).__name__}
    print(json.dumps(result, indent=2))
