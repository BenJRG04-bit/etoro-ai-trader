"""Fetch public daily closes and print historical £100 research comparisons.

Run: python run_paper_report.py
No brokerage connection, keys, order placement or live trading.
"""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from paper_performance_report import paper_performance_report

def run_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    results = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            report = paper_performance_report(history["closes"], ticker=ticker)
            report["first_date"] = history["dates"][0]
            report["last_date"] = history["dates"][-1]
            report["price_type"] = history["price_type"]
            results[ticker] = {"status": "EXPLORATORY_ONLY", "report": report}
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            results[ticker] = {"status": "UNAVAILABLE", "error_type": type(exc).__name__}
    return {
        "mode": "HISTORICAL_PAPER_REPORT_NO_ORDERS",
        "starting_cash_gbp_per_asset": 100.0,
        "assets": results,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Each ticker is an independent hypothetical £100 test, not one combined account. Unadjusted closes omit dividends and can distort splits. No FX conversion, spread, slippage or taxes. No future profitability claim.",
    }

if __name__ == "__main__":
    print(json.dumps(run_report(), indent=2))
