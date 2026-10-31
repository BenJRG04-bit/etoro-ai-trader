"""Public-data shared-portfolio decision diagnostics with strict date alignment."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from portfolio_decision_diagnostics import diagnose_portfolio_decisions

def run_decision_diagnostics(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    tickers = tuple(tickers)
    unavailable = {"status": "UNAVAILABLE", "research_only": True,
                   "orders_allowed": False, "live_trading_approved": False}
    if not tickers or len(set(tickers)) != len(tickers):
        return dict(unavailable, error_type="InvalidWatchlist")
    rows = {}
    for ticker in tickers:
        try:
            data = fetcher(ticker, period=period)
            dates = data["dates"]
            if data["ticker"] != ticker or len(dates) != len(data["closes"]) or dates != sorted(set(dates)):
                raise ValueError("Invalid ticker or dates")
            rows[ticker] = data
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return dict(unavailable, error_type=type(exc).__name__, failed_ticker=ticker)
    dates = rows[tickers[0]]["dates"]
    if any(rows[t]["dates"] != dates for t in tickers):
        return dict(unavailable, error_type="DateMisalignment")
    try:
        report = diagnose_portfolio_decisions({t: rows[t]["closes"] for t in tickers})
    except (ValueError, TypeError, KeyError) as exc:
        return dict(unavailable, error_type=type(exc).__name__)
    return {"status": "EXPLORATORY_ONLY", "first_date": dates[0], "last_date": dates[-1],
            "diagnostics": report, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False}

if __name__ == "__main__":
    print(json.dumps(run_decision_diagnostics(), indent=2))
