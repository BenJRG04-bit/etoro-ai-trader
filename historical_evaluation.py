"""Chronological historical evaluation with 60-close warmup per test window.

Research-only. Supply real, adjusted historical closes externally; this module
does not download prices, tune parameters, or access a brokerage.
"""
from math import isfinite
from adaptive_comparison import compare_regime_strategy

def evaluate_windows(closes, test_size=60, starting_cash=1000.0,
                     fee_rate=0.001, max_allocation=0.05):
    if not isinstance(test_size, int) or test_size < 2:
        raise ValueError("test_size must be an integer >= 2")
    if len(closes) < 60 + test_size:
        raise ValueError("Need 60 warmup closes and a full test window")
    if any(not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Prices must be finite and positive")
    windows = []
    # Nonoverlapping test periods; prior 60 closes only provide indicators.
    for start in range(60, len(closes) - test_size + 1, test_size):
        segment = closes[start - 60:start + test_size]
        comparison = compare_regime_strategy(
            segment, starting_cash=starting_cash, fee_rate=fee_rate,
            max_allocation=max_allocation)
        windows.append({
            "test_start_index": start,
            "test_end_index_exclusive": start + test_size,
            "baseline_return_fraction": comparison["baseline"]["return_fraction"],
            "regime_return_fraction": comparison["regime_aware"]["return_fraction"],
            "benchmark_return_fraction": round(
                comparison["capped_buy_and_hold_end_equity"] / starting_cash - 1, 6),
            "baseline_max_drawdown_fraction": comparison["baseline"]["max_drawdown_fraction"],
            "regime_max_drawdown_fraction": comparison["regime_aware"]["max_drawdown_fraction"],
            "regime_minus_baseline_return_fraction":
                comparison["regime_minus_baseline_return_fraction"],
        })
    return {
        "mode": "HISTORICAL_WINDOW_RESEARCH_NO_ORDERS",
        "test_size": test_size,
        "window_count": len(windows),
        "windows": windows,
        "research_only": True,
        "limitations": ("Chronological, nonoverlapping evaluation, but not a true untouched "
                        "out-of-sample test if rules were chosen after viewing these prices. "
                        "Close-only, simplified fees, no spread, slippage, dividends or taxes.")
    }
