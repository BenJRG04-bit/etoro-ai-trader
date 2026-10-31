"""Offline benchmark comparison for Project E.T. No brokerage connectivity or orders."""
from math import isfinite
from backtest import backtest

def compare_to_buy_and_hold(closes, starting_cash=1000.0, fee_rate=0.001,
                            max_allocation=0.05):
    """Compare the council to an equally capped, continuously held position.

    Both use the same price series and initial allocation cap. Benchmark pays
    one entry fee; neither model includes spread, slippage, dividends or taxes.
    """
    strategy = backtest(closes, starting_cash, fee_rate, max_allocation)
    if not (isfinite(starting_cash) and starting_cash > 0):
        raise ValueError("Invalid starting cash")
    if not (isfinite(fee_rate) and 0 <= fee_rate < 1):
        raise ValueError("Invalid fee")
    if not (isfinite(max_allocation) and 0 <= max_allocation <= 0.05):
        raise ValueError("Invalid allocation")
    # Match the backtest's first eligible close (index 59).
    entry = closes[59]
    benchmark_end = starting_cash * (1 - fee_rate * max_allocation) * (
        1 + max_allocation * (closes[-1] / entry - 1))
    benchmark_return = benchmark_end / starting_cash - 1
    return {
        "mode": "OFFLINE_COMPARISON_NO_ORDERS",
        "strategy": strategy,
        "benchmark": "CAPPED_BUY_AND_HOLD_SAME_ASSET",
        "benchmark_end_equity": round(benchmark_end, 4),
        "benchmark_return_fraction": round(benchmark_return, 6),
        "strategy_minus_benchmark_fraction": round(
            strategy["return_fraction"] - benchmark_return, 6),
        "limitations": "In-sample illustrative comparison, not independent ETF benchmark; no spread/slippage/dividends/taxes.",
        "research_only": True,
    }
