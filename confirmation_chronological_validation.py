"""Chronological validation of a predeclared two-close confirmation hypothesis.

Uses disjoint evaluation return periods with sufficient warm-up history.
Because the confirmation idea was selected after viewing historical results,
this is a retrospective robustness check, NOT a genuinely untouched holdout.
"""
from decision_confirmation_experiment import compare_confirmation

def validate_confirmation_chronologically(price_series, *, split_fraction=0.70,
                                          starting_cash=100.0, fee_rates=(0.001, 0.005)):
    if not isinstance(price_series, dict) or not price_series:
        raise ValueError("Missing historical prices")
    if type(split_fraction) not in (int, float) or not 0.55 <= split_fraction <= 0.85:
        raise ValueError("Invalid split")
    tickers = sorted(price_series)
    n = len(price_series[tickers[0]])
    if n < 160:
        raise ValueError("Need at least 160 aligned closes")
    for ticker in tickers:
        values = price_series[ticker]
        if (not isinstance(ticker, str) or not ticker or not isinstance(values, (list, tuple))
                or len(values) != n):
            raise ValueError("Invalid or misaligned history")
    split = int(n * split_fraction)
    # First evaluation uses closes 59..split-1. Second uses closes split..n-2.
    # The second period receives 59 prior closes for indicators, but none of
    # the earlier-period returns are counted in its simulated P&L.
    earlier = {ticker: price_series[ticker][:split + 1] for ticker in tickers}
    later = {ticker: price_series[ticker][split - 59:] for ticker in tickers}
    if min(len(next(iter(earlier.values()))), len(next(iter(later.values())))) < 62:
        raise ValueError("Insufficient evaluation history")
    return {
        "status": "EXPLORATORY_ONLY",
        "split_index": split,
        "earlier_evaluation_return_intervals": split - 59,
        "later_evaluation_return_intervals": n - split - 1,
        "earlier": compare_confirmation(earlier, starting_cash=starting_cash, fee_rates=fee_rates),
        "later": compare_confirmation(later, starting_cash=starting_cash, fee_rates=fee_rates),
        "research_only": True, "orders_allowed": False, "live_trading_approved": False,
        "limitations": "Retrospective chronological robustness check, not untouched out-of-sample validation: the hypothesis was chosen after inspecting historical results. Disjoint P&L intervals; 59 earlier closes supplied only as indicator warm-up. Starting cash resets for each period. Simplified fees, no FX, spread, slippage, dividends or execution.",
    }
