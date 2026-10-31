"""Run public historical shared-portfolio benchmark with strict calendar checks."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from portfolio_benchmark import compare_portfolio_policies

def run_benchmark_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    tickers = tuple(tickers)
    if not tickers or len(set(tickers)) != len(tickers):
        return {"status": "UNAVAILABLE", "error_type": "InvalidWatchlist",
                "research_only": True, "orders_allowed": False}
    histories = {}
    for ticker in tickers:
        try:
            row = fetcher(ticker, period=period)
            if row["ticker"] != ticker or len(row["dates"]) != len(row["closes"]):
                raise ValueError("Invalid ticker or dates")
            if row["dates"] != sorted(set(row["dates"])):
                raise ValueError("Non-unique or unsorted dates")
            histories[ticker] = row
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                    "failed_ticker": ticker, "research_only": True, "orders_allowed": False}
    dates = histories[tickers[0]]["dates"]
    if any(histories[t]["dates"] != dates for t in tickers):
        return {"status": "UNAVAILABLE", "error_type": "DateMisalignment",
                "research_only": True, "orders_allowed": False}
    try:
        comparison = compare_portfolio_policies({t: histories[t]["closes"] for t in tickers})
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                "research_only": True, "orders_allowed": False}
    return {"status": "EXPLORATORY_ONLY", "first_date": dates[0], "last_date": dates[-1],
            "price_type": histories[tickers[0]].get("price_type", "unknown"),
            "comparison": comparison, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False}

if __name__ == "__main__":
    print(json.dumps(run_benchmark_report(), indent=2))
