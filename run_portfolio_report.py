"""Fetch public historical data and simulate one synchronized research portfolio."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from portfolio_simulator import simulate_portfolio

def run_portfolio_report(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    histories = {}
    for ticker in tickers:
        try:
            history = fetcher(ticker, period=period)
            if history["ticker"] != ticker:
                raise ValueError("Ticker mismatch")
            if len(history["dates"]) != len(history["closes"]):
                raise ValueError("Dates and prices mismatch")
            if len(set(history["dates"])) != len(history["dates"]) or history["dates"] != sorted(history["dates"]):
                raise ValueError("Invalid date order")
            histories[ticker] = history
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return {"status": "UNAVAILABLE", "error_type": type(exc).__name__,
                    "failed_ticker": ticker, "orders_allowed": False, "research_only": True,
                    "live_trading_approved": False}
    if not histories:
        return {"status": "UNAVAILABLE", "error_type": "NoAssets", "orders_allowed": False,
                "research_only": True, "live_trading_approved": False}
    dates = histories[tickers[0]]["dates"]
    # Do not silently align different calendars or bridge missing days.
    if any(histories[ticker]["dates"] != dates for ticker in tickers):
        return {"status": "UNAVAILABLE", "error_type": "DateMisalignment", "orders_allowed": False,
                "research_only": True, "live_trading_approved": False}
    try:
        simulation = simulate_portfolio({ticker: histories[ticker]["closes"] for ticker in tickers})
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "UNAVAILABLE", "error_type": type(exc).__name__, "orders_allowed": False,
                "research_only": True, "live_trading_approved": False}
    return {"status": "EXPLORATORY_ONLY", "first_date": dates[0], "last_date": dates[-1],
            "price_type": histories[tickers[0]].get("price_type", "unknown"),
            "simulation": simulation, "orders_allowed": False, "research_only": True,
            "live_trading_approved": False}

if __name__ == "__main__":
    print(json.dumps(run_portfolio_report(), indent=2))
