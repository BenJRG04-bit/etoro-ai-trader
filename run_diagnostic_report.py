"""Public-price, read-only diagnostic report for Project E.T. research decisions."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from decision_diagnostics import diagnose_decisions

def run_diagnostic_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    results = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            results[ticker] = {
                "status": "EXPLORATORY_ONLY",
                "diagnostics": diagnose_decisions(history["closes"]),
                "first_date": history["dates"][0],
                "last_date": history["dates"][-1],
            }
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            results[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "OFFLINE_MARKET_DIAGNOSTICS_NO_ORDERS",
        "assets": results,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Historical hindsight only. Up-day counts do not prove missed profitable trades; no strategy parameter optimization or independent out-of-sample test.",
    }

if __name__ == "__main__":
    print(json.dumps(run_diagnostic_report(), indent=2))
