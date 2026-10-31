"""Research-only scorecard comparing existing offline strategy simulations.

No broker connections, orders, or profitability approval.
"""
from math import isfinite
from adaptive_comparison import compare_regime_strategy


def research_scorecard(closes, starting_cash=1000.0, fee_rate=0.001,
                       max_allocation=0.05):
    """Compare baseline, regime-aware, and capped holding on the same prices.

    Returns descriptive historical results, not a live-trading recommendation.
    """
    comparison = compare_regime_strategy(
        closes, starting_cash, fee_rate, max_allocation
    )
    baseline = comparison["baseline"]
    adaptive = comparison["regime_aware"]
    held = comparison["capped_buy_and_hold_end_equity"]
    if not isfinite(held):
        raise ValueError("Non-finite benchmark result")

    def row(end_equity, drawdown=None, trades=None):
        return {
            "end_equity": round(end_equity, 4),
            "return_fraction": round(end_equity / starting_cash - 1, 6),
            "max_drawdown_fraction": drawdown,
            "rebalance_events": trades,
        }

    return {
        "mode": "OFFLINE_RESEARCH_SCORECARD_NO_ORDERS",
        "baseline": row(baseline["end_equity"],
                        baseline["max_drawdown_fraction"],
                        baseline["rebalance_events"]),
        "regime_aware": row(adaptive["end_equity"],
                            adaptive["max_drawdown_fraction"],
                            adaptive["rebalance_events"]),
        "capped_buy_and_hold": row(held),
        "regime_minus_baseline_equity": round(
            adaptive["end_equity"] - baseline["end_equity"], 4
        ),
        "regime_minus_hold_equity": round(
            adaptive["end_equity"] - held, 4
        ),
        "live_trading_approved": False,
        "research_only": True,
        "limitations": (
            "In-sample, same-asset, close-only comparison. Holding benchmark "
            "has no reported drawdown or trade count. No spread, slippage, "
            "dividends, taxes, independent ETF benchmark or forward validation."
        ),
    }
