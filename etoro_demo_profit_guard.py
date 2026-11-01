"""Offline profit-protection proposal; no API calls or automatic orders.

The user must approve any broker-side take-profit/stop-loss edit separately.
"""
from math import isfinite


def assess_demo_profit_exit(*, account, symbol, invested_usd, unrealized_pnl_usd,
                            profit_target_fraction=0.05,
                            loss_limit_fraction=0.05,
                            data_age_seconds=None):
    reasons = []
    if account != "demo":
        reasons.append("DEMO_ONLY")
    if symbol != "ETHEUR":
        reasons.append("POSITION_NOT_APPROVED")
    numbers = (invested_usd, unrealized_pnl_usd, profit_target_fraction, loss_limit_fraction)
    if any(type(x) not in (float, int) or not isfinite(x) for x in numbers):
        reasons.append("INVALID_NUMERIC_INPUT")
    elif invested_usd <= 0 or not (0 < profit_target_fraction <= 0.20) or not (0 < loss_limit_fraction <= 0.20):
        reasons.append("INVALID_LIMITS")
    if (type(data_age_seconds) not in (int, float) or
            not isfinite(data_age_seconds) or data_age_seconds < 0 or data_age_seconds > 120):
        reasons.append("STALE_OR_UNVERIFIED_POSITION")
    decision = "BLOCKED"
    if not reasons:
        gain_fraction = unrealized_pnl_usd / invested_usd
        if gain_fraction >= profit_target_fraction:
            decision = "PROPOSE_TAKE_PROFIT"
        elif gain_fraction <= -loss_limit_fraction:
            decision = "PROPOSE_STOP_LOSS"
        else:
            decision = "HOLD_MONITOR"
    return {"decision": decision, "reasons": reasons,
            "account": "demo", "symbol": symbol,
            "broker_order_sent": False, "position_modified": False,
            "requires_explicit_broker_edit_approval": True,
            "note": "A periodic monitor is not a guaranteed exit; broker-side stops require a separately approved edit."}
