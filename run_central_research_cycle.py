"""One autonomous read-only market research cycle; no trading or credentials."""
import json
from pathlib import Path
from historical_prices import WATCHLIST, fetch_daily_closes
from central_intelligence import central_research_decision


def run_research_cycle(fetcher=fetch_daily_closes, tickers=WATCHLIST, period="2y",
                       decision_fn=central_research_decision):
    safe = {"research_only": True, "orders_allowed": False, "live_trading_approved": False}
    try:
        if not isinstance(tickers, (list, tuple)) or not tickers or len(set(tickers)) != len(tickers):
            raise ValueError("Invalid watchlist")
        rows = {}
        for ticker in tickers:
            history = fetcher(ticker, period=period)
            if not isinstance(history, dict) or history.get("ticker") != ticker:
                raise ValueError("Ticker mismatch")
            dates, closes = history["dates"], history["closes"]
            if not isinstance(dates, list) or len(dates) != len(closes) or dates != sorted(set(dates)):
                raise ValueError("Invalid historical dates")
            rows[ticker] = history
        dates = rows[tickers[0]]["dates"]
        if any(rows[t]["dates"] != dates for t in tickers):
            raise ValueError("DateMisalignment")
        decisions = decision_fn({t: rows[t]["closes"] for t in tickers})
        if not isinstance(decisions, dict) or any(decisions.get(k) is not v for k, v in safe.items()):
            raise ValueError("Unsafe intelligence result")
        if decisions.get("status") != "RESEARCH_ONLY":
            raise ValueError("Invalid intelligence status")
        return {**safe, "status": "RESEARCH_CYCLE_COMPLETE", "as_of_date": dates[-1],
                "asset_count": len(tickers), "intelligence": decisions,
                "limitations": "Public daily closes only; no orders, brokerage positions, broker account access, or performance approval."}
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        return {**safe, "status": "UNAVAILABLE", "error_type": type(exc).__name__,
                "intelligence": None}


if __name__ == "__main__":
    report = run_research_cycle()
    Path("central_research_cycle.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
