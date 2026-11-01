"""Offline synchronized multi-asset portfolio simulation; never sends orders.

A single £100 hypothetical account, maximum 5% TOTAL exposure, equal weights
among positive council signals. Signals use only closes available at decision time.
"""
from math import isfinite
from profit_protection_audit import audit_equity_curve
from capital_guard import CapitalGuard
from regime_council import regime_aware_council

def simulate_portfolio(price_series, starting_cash=100.0, fee_rate=0.001,
                       max_total_allocation=0.05, assessment_fn=regime_aware_council):
    if not isinstance(price_series, dict) or not price_series:
        raise ValueError("Need a nonempty ticker-to-price mapping")
    if not isinstance(starting_cash, (float, int)) or isinstance(starting_cash, bool) or not isfinite(starting_cash) or starting_cash <= 0:
        raise ValueError("Invalid starting cash")
    if any(not isinstance(v, (float, int)) or isinstance(v, bool) or not isfinite(v) for v in (fee_rate, max_total_allocation)):
        raise ValueError("Invalid fee or allocation")
    if not 0 <= fee_rate < 1 or not 0 <= max_total_allocation <= 0.05:
        raise ValueError("Fee or total exposure outside safety bounds")
    symbols = sorted(price_series)
    n = len(price_series[symbols[0]])
    if n < 62:
        raise ValueError("Need at least 62 aligned closes")
    for ticker in symbols:
        values = price_series[ticker]
        if not isinstance(ticker, str) or not ticker or not isinstance(values, (list, tuple)) or len(values) != n:
            raise ValueError("Prices must be aligned and tickers valid")
        if any(type(x) not in (int, float) or not isfinite(x) or x <= 0 for x in values):
            raise ValueError("Invalid historical close")
    equity = float(starting_cash)
    guard = CapitalGuard(equity)
    allocations = {ticker: 0.0 for ticker in symbols}
    curve = [equity]
    rebalances = 0
    max_observed_allocation = 0.0
    halted = False
    halt_reason = None
    for t in range(59, n - 1):
        state = guard.observe(equity)
        if state["halted"]:
            halted, halt_reason = True, state["reason"]
        eligible = []
        if not halted:
            for ticker in symbols:
                assessment = assessment_fn(price_series[ticker][:t + 1])
                if (assessment.get("status") == "OK" and
                    not assessment.get("regime_risk_veto", False) and
                    assessment.get("decision") == "POSITIVE_RESEARCH"):
                    eligible.append(ticker)
        per_asset = max_total_allocation / len(eligible) if eligible else 0.0
        desired = {ticker: (per_asset if ticker in eligible else 0.0) for ticker in symbols}
        turnover = sum(abs(desired[ticker] - allocations[ticker]) for ticker in symbols)
        if turnover > 1e-12:
            equity *= (1 - fee_rate * turnover)
            rebalances += 1
        allocations = desired
        max_observed_allocation = max(max_observed_allocation, sum(allocations.values()))
        period_return = sum(
            allocations[ticker] * (price_series[ticker][t + 1] / price_series[ticker][t] - 1)
            for ticker in symbols
        )
        equity *= 1 + period_return
        state = guard.observe(equity)
        if state["halted"]:
            halted, halt_reason = True, state["reason"]
        curve.append(equity)
    peak = curve[0]
    max_drawdown = 0.0
    for value in curve:
        peak = max(peak, value)
        max_drawdown = max(max_drawdown, (peak - value) / peak)
    return {
        "mode": "OFFLINE_SHARED_PORTFOLIO_NO_ORDERS",
        "assets": symbols,
        "starting_cash": float(starting_cash),
        "end_equity": round(equity, 4),
        "return_fraction": round(equity / starting_cash - 1, 6),
        "max_drawdown_fraction": round(max_drawdown, 6),
        "profit_protection_audit": audit_equity_curve(curve),
        "rebalance_events": rebalances,
        "max_observed_total_allocation": round(max_observed_allocation, 6),
        "max_total_allocation": max_total_allocation,
        "fee_rate": fee_rate,
        "capital_guard_enabled": True,
        "halted": halted,
        "halt_reason": halt_reason,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Single historical shared cash account; simplified target-weight rebalance at close, no FX, spread, slippage, taxes, dividends or actual execution. Guard cannot prevent gaps. All dates must be aligned exactly; no forward filling. No live trading.",
    }
