"""Offline, look-ahead-safe toy backtest. Research only, never sends orders.

Decision at close t is applied to next close-to-close return t -> t+1.
Long/cash only. Includes configurable per-side transaction cost.
"""
from math import isfinite
from six_brains import council

def backtest(closes, starting_cash=1000.0, fee_rate=0.001, max_allocation=0.05, *, assessment_fn=None):
    if len(closes) < 62 or any(not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Need at least 62 finite positive closes")
    if starting_cash <= 0 or not isfinite(starting_cash):
        raise ValueError("Invalid starting cash")
    if not (0 <= fee_rate < 1 and 0 <= max_allocation <= 0.05):
        raise ValueError("Invalid fee or allocation")
    if assessment_fn is None:
        assessment_fn = council
    equity = starting_cash
    peak = equity
    position = 0.0
    trades = 0
    curve = [equity]
    stopped = False
    for t in range(59, len(closes) - 1):
        assessment = assessment_fn(closes[:t + 1])
        desired = max_allocation if assessment["decision"] == "POSITIVE_RESEARCH" else 0.0
        if stopped or equity <= 0.9 * peak:
            stopped = True
            desired = 0.0
        # Charge a simple turnover fee at the rebalance close.
        turnover = abs(desired - position)
        if turnover > 1e-12:
            equity *= (1 - fee_rate * turnover)
            trades += 1
        position = desired
        period_return = closes[t + 1] / closes[t] - 1
        equity *= 1 + position * period_return
        peak = max(peak, equity)
        curve.append(equity)
    return {"mode": "OFFLINE_BACKTEST_NO_ORDERS", "start_equity": starting_cash,
            "end_equity": round(equity, 4), "return_fraction": round(equity / starting_cash - 1, 6),
            "max_drawdown_fraction": round(max((max(curve[:i + 1]) - v) / max(curve[:i + 1])
                                               for i, v in enumerate(curve)), 6),
            "rebalance_events": trades, "stopped": stopped,
            "fee_rate": fee_rate, "max_allocation": max_allocation,
            "limitations": "Illustrative: close prices, simple fees, no spread/slippage/taxes, no benchmark or out-of-sample validation.",
            "research_only": True}
