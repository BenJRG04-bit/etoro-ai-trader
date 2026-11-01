"""Project E.T. offline paper trading: simulation only, never broker orders.

Example:
python tools/paper_trade.py --prices examples/paper_prices.json --output paper_results.json

Input JSON: {"date":"2026-11-02","prices":{"AAPL":250,"MSFT":500,"NVDA":200,"SPY":700,"VTI":350}}
All values are illustrative until replaced with verified closing prices.
"""
import argparse
import json
from datetime import date
from pathlib import Path
from math import isfinite

WATCHLIST = ("AAPL", "MSFT", "NVDA", "SPY", "VTI")
START_GBP = 100.0
FEE_GBP = 0.0  # Placeholder; real fee assumptions must be validated.
MAX_ALLOCATION = 0.20

def run(prices, fx_usd_per_gbp, session_date):
    if not isinstance(prices, dict) or set(prices) != set(WATCHLIST):
        raise ValueError("Prices must contain exactly the five watchlist tickers")
    if not isinstance(session_date, str):
        raise ValueError("Missing session date")
    date.fromisoformat(session_date)
    if not isinstance(fx_usd_per_gbp, (int, float)) or isinstance(fx_usd_per_gbp, bool) or not isfinite(fx_usd_per_gbp) or fx_usd_per_gbp <= 0:
        raise ValueError("Valid USD-per-GBP FX rate required")
    for ticker, price in prices.items():
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not isfinite(price) or price <= 0:
            raise ValueError(f"Invalid price: {ticker}")
    # No automatic trade decision yet: baseline is 100% cash until signals validated.
    return {
        "mode": "OFFLINE_PAPER_ONLY", "date": session_date,
        "starting_cash_gbp": START_GBP, "cash_gbp": START_GBP,
        "holdings": {}, "trades": [], "equity_gbp": START_GBP,
        "fees_assumption_gbp": FEE_GBP, "max_allocation_per_asset": MAX_ALLOCATION,
        "market_prices_usd": prices, "fx_usd_per_gbp": fx_usd_per_gbp,
        "orders_allowed": False, "live_trading_approved": False,
        "research_only": True,
        "note": "Cash-only baseline. No broker integration or trading signals."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prices", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.prices).read_text(encoding="utf-8"))
    report = run(raw["prices"], raw["fx_usd_per_gbp"], raw["date"])
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Paper baseline saved: no trades, no broker orders.")

if __name__ == "__main__":
    main()
