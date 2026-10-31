"""Generate a timestamped, read-only forward signal snapshot from public data."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from forward_signal_monitor import create_signal_snapshot

def run_forward_snapshot(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    tickers = tuple(tickers)
    if not tickers or len(set(tickers)) != len(tickers):
        return {"status": "UNAVAILABLE", "error_type": "InvalidWatchlist",
                "orders_allowed": False, "research_only": True}
    histories = {}
    for ticker in tickers:
        try:
            row = fetcher(ticker, period=period)
            if row["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            histories[ticker] = row
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return {"status": "UNAVAILABLE", "failed_ticker": ticker,
                    "error_type": type(exc).__name__, "orders_allowed": False,
                    "research_only": True}
    try:
        snapshot = create_signal_snapshot(histories)
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "UNAVAILABLE", "error_type": str(exc),
                "orders_allowed": False, "research_only": True}
    return {"status": "SNAPSHOT_RESEARCH_ONLY", "snapshot": snapshot,
            "orders_allowed": False, "research_only": True,
            "live_trading_approved": False}

if __name__ == "__main__":
    print(json.dumps(run_forward_snapshot(), indent=2))
