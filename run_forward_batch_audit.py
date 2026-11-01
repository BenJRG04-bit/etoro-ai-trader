"""Audit downloaded GitHub Actions forward snapshots using one data fetch per asset."""
import json
import sys
from pathlib import Path
from forward_batch_audit import audit_forward_snapshots
from historical_prices import WATCHLIST, fetch_daily_closes

def run_batch(paths, fetcher=fetch_daily_closes):
    documents = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                documents.append(json.load(handle))
        except (OSError, ValueError):
            documents.append({})
    # No archived evidence must not require an external market-data request.
    if not documents:
        return audit_forward_snapshots([], lambda ticker, period="2y": (_ for _ in ()).throw(
            AssertionError("Empty archive must not fetch market data")))
    histories = {}
    for ticker in WATCHLIST:
        try:
            row = fetcher(ticker, period="2y")
            if row["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            histories[ticker] = row
        except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
            return {"status": "UNAVAILABLE", "failed_ticker": ticker,
                    "error_type": type(exc).__name__, "research_only": True,
                    "orders_allowed": False, "live_trading_approved": False}
    def cached(ticker, period="2y"):
        return histories[ticker]
    return audit_forward_snapshots(documents, cached)

if __name__ == "__main__":
    paths = sorted(Path(sys.argv[1]).glob("*/forward_signal_snapshot.json")) if len(sys.argv) == 2 else []
    print(json.dumps(run_batch(paths), indent=2))
