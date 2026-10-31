"""Compare baseline and risk-veto research strategies on identical historical closes.

No orders, broker access, optimization or profitability claims.
"""
from backtest import backtest
from regime_council import regime_aware_council

def compare_regime_strategy(closes, starting_cash=1000.0, fee_rate=0.001,
                            max_allocation=0.05):
    baseline = backtest(closes, starting_cash, fee_rate, max_allocation)
    adaptive = backtest(closes, starting_cash, fee_rate, max_allocation,
                        assessment_fn=regime_aware_council)
    # Both strategies begin at index 59 and have the same capped exposure.
    entry = closes[59]
    held = starting_cash * (1 - fee_rate * max_allocation) * (
        1 + max_allocation * (closes[-1] / entry - 1))
    return {
        "mode": "OFFLINE_REGIME_COMPARISON_NO_ORDERS",
        "baseline": baseline,
        "regime_aware": adaptive,
        "capped_buy_and_hold_end_equity": round(held, 4),
        "regime_minus_baseline_return_fraction": round(
            adaptive["return_fraction"] - baseline["return_fraction"], 6),
        "research_only": True,
        "limitations": "Illustrative in-sample close-only results. No spread, slippage, dividends, taxes or out-of-sample testing."
    }
