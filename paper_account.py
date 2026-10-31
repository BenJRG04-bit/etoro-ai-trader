"""Offline £100 paper account evaluation. Never connects to a broker or places orders."""
from math import isfinite
from backtest import backtest
from regime_council import regime_aware_council

def simulate_paper_account(closes, starting_cash=100.0, fee_rate=0.001):
    """Run a historical hypothetical account with 5% max exposure and capital guard.

    This is NOT a live paper broker account; prices are supplied historical closes.
    """
    if not isinstance(starting_cash, (int, float)) or not isfinite(starting_cash) or starting_cash <= 0:
        raise ValueError("Starting cash must be positive and finite")
    if not isinstance(fee_rate, (int, float)) or not isfinite(fee_rate) or not 0 <= fee_rate < 1:
        raise ValueError("Invalid fee rate")
    result = backtest(
        closes, starting_cash=float(starting_cash), fee_rate=fee_rate,
        max_allocation=0.05, assessment_fn=regime_aware_council,
        use_capital_guard=True,
    )
    result["mode"] = "HISTORICAL_PAPER_ACCOUNT_NO_ORDERS"
    result["currency"] = "GBP"
    result["orders_allowed"] = False
    result["live_trading_approved"] = False
    result["limitations"] += " GBP is a notional denomination; supplied closes must be consistently priced. No FX conversion or broker execution."
    return result
