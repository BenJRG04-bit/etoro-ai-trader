"""Fail-closed, offline preflight for proposed Project E.T. demo BUY orders.

This module never calls eToro, reads credentials, or submits orders.
Inputs must come from independently verified demo-account and market snapshots.
A successful preflight is NOT permission to send a trade without user approval.
"""
from dataclasses import dataclass
from math import isfinite

WATCHLIST = frozenset({"AAPL", "MSFT", "NVDA", "SPY", "VTI"})


@dataclass(frozen=True)
class DemoTradeLimits:
    training_budget_usd: float = 1000.0
    max_position_fraction: float = 0.05
    max_total_fraction: float = 0.10
    max_drawdown_fraction: float = 0.10
    max_quote_age_seconds: float = 120.0


def _valid_nonnegative(value):
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value) and value >= 0)


def assess_demo_buy(
    *,
    account,
    symbol,
    amount_usd,
    leverage,
    market_open,
    quote_age_seconds,
    available_cash_usd,
    current_equity_usd,
    peak_equity_usd,
    total_active_exposure_usd,
    active_symbols,
    limits=DemoTradeLimits(),
):
    """Return a veto report for a hypothetical demo buy; never place an order.

    total_active_exposure_usd MUST include existing positions AND pending buys.
    active_symbols MUST include both open positions and pending orders.
    If either value is unverified, do not invoke this guard to authorize a trade.
    Quotes must be positive-age, broker-sourced and from the actual session.
    """
    reasons = []
    if account != "demo":
        reasons.append("DEMO_ONLY")
    if symbol not in WATCHLIST:
        reasons.append("SYMBOL_NOT_APPROVED")
    if type(leverage) is not int or leverage != 1:
        reasons.append("LEVERAGE_NOT_ALLOWED")
    if market_open is not True:
        reasons.append("MARKET_NOT_VERIFIED_OPEN")
    if (not _valid_nonnegative(quote_age_seconds)
            or quote_age_seconds > limits.max_quote_age_seconds):
        reasons.append("STALE_OR_UNKNOWN_QUOTE")

    amounts = (amount_usd, available_cash_usd, current_equity_usd,
               peak_equity_usd, total_active_exposure_usd)
    if not all(_valid_nonnegative(v) for v in amounts):
        reasons.append("INVALID_ACCOUNT_OR_ORDER_DATA")
    else:
        if amount_usd <= 0:
            reasons.append("INVALID_AMOUNT")
        if current_equity_usd <= 0 or peak_equity_usd <= 0:
            reasons.append("INVALID_EQUITY")
        elif ((peak_equity_usd - current_equity_usd) / peak_equity_usd
              >= limits.max_drawdown_fraction):
            reasons.append("DRAWDOWN_HALT")
        if amount_usd > available_cash_usd:
            reasons.append("INSUFFICIENT_DEMO_CASH")
        if amount_usd > limits.training_budget_usd * limits.max_position_fraction:
            reasons.append("POSITION_SIZE_LIMIT")
        if (total_active_exposure_usd + amount_usd
                > limits.training_budget_usd * limits.max_total_fraction):
            reasons.append("TOTAL_EXPOSURE_LIMIT")

    if not isinstance(active_symbols, (list, tuple, set, frozenset)):
        reasons.append("UNVERIFIED_OPEN_ORDERS")
    elif symbol in active_symbols:
        reasons.append("DUPLICATE_POSITION_OR_ORDER")

    return {
        "approved_for_proposal": not reasons,
        "reasons": reasons,
        "account": "demo",
        "research_only": True,
        "order_submitted": False,
        "needs_explicit_trade_confirmation": True,
    }
