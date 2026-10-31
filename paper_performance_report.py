"""Compare a £100 offline simulated account with a matched 5%-exposure hold.

No network, broker connection, or trading orders. Price inputs must be supplied.
"""
from math import isfinite
from paper_account import simulate_paper_account

def paper_performance_report(closes, ticker="SPY", starting_cash=100.0, fee_rate=0.001):
    if not isinstance(closes, (list, tuple)) or len(closes) < 62:
        raise ValueError("At least 62 prices required")
    if any(not isinstance(x, (int, float)) or not isfinite(x) or x <= 0 for x in closes):
        raise ValueError("Prices must be positive and finite")
    if not isinstance(starting_cash, (int, float)) or not isfinite(starting_cash) or starting_cash <= 0:
        raise ValueError("Invalid starting cash")
    if not isinstance(fee_rate, (int, float)) or not isfinite(fee_rate) or not 0 <= fee_rate < 1:
        raise ValueError("Invalid fee")
    simulation = simulate_paper_account(closes, starting_cash, fee_rate)
    # The benchmark keeps 5% notional exposure, with a single entry fee.
    # It is NOT a full 100% buy-and-hold portfolio.
    entry_price = closes[59]
    benchmark_end = starting_cash * (1 - fee_rate * 0.05) * (
        1 + 0.05 * (closes[-1] / entry_price - 1))
    return {
        "mode": "OFFLINE_PAPER_PERFORMANCE_NO_ORDERS",
        "ticker": ticker,
        "starting_cash": float(starting_cash),
        "strategy_end": simulation["end_equity"],
        "benchmark_end": round(benchmark_end, 4),
        "strategy_minus_benchmark_gbp": round(simulation["end_equity"] - benchmark_end, 4),
        "benchmark": "SAME_ASSET_5_PERCENT_CAPPED_HOLD",
        "strategy": simulation,
        "research_only": True,
        "live_trading_approved": False,
        "limitations": "Hypothetical historical close-price study; benchmark lacks capital guard; no FX, dividends, spread, slippage or tax. Unadjusted prices can be distorted by splits.",
    }
