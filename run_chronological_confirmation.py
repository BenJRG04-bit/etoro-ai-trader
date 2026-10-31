"""Run retrospective chronological confirmation robustness report."""
import json
from historical_prices import WATCHLIST, fetch_daily_closes
from confirmation_chronological_validation import validate_confirmation_chronologically

def run_chronological_confirmation(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y"):
    tickers = tuple(tickers)
    unavailable = {"status": "UNAVAILABLE", "research_only": True,
                   "orders_allowed": False, "live_trading_approved": False}
    if not tickers or len(set(tickers)) != len(tickers):
        return dict(unavailable, error_type="InvalidWatchlist")
    histories = {}
    for ticker in tickers:
        try:
            row = fetcher(ticker, period=period)
            dates = row["dates"]
            if row["ticker"] != ticker or len(dates) != len(row["closes"]) or dates != sorted(set(dates)):
                raise ValueError("Invalid ticker or dates")
            histories[ticker] = row
        except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
            return dict(unavailable, error_type=type(exc).__name__, failed_ticker=ticker)
    dates = histories[tickers[0]]["dates"]
    if any(histories[t]["dates"] != dates for t in tickers):
        return dict(unavailable, error_type="DateMisalignment")
    try:
        result = validate_confirmation_chronologically({t: histories[t]["closes"] for t in tickers})
    except (ValueError, TypeError, KeyError) as exc:
        return dict(unavailable, error_type=type(exc).__name__)
    return {"status": "EXPLORATORY_ONLY", "first_date": dates[0], "last_date": dates[-1],
            "earlier_last_date": dates[result["split_index"]],
            "later_first_decision_date": dates[result["split_index"]],
            "validation": result, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False}

if __name__ == "__main__":
    print(json.dumps(run_chronological_confirmation(), indent=2))
