"""Explain historical research decisions without changing strategy or trading orders."""
from math import isfinite
from collections import Counter
from regime_council import regime_aware_council

def diagnose_decisions(closes):
    if not isinstance(closes, (list, tuple)) or len(closes) < 62:
        raise ValueError("Need at least 62 closes")
    if any(not isinstance(p, (int, float)) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Invalid closes")
    decisions = Counter()
    regimes = Counter()
    veto_days = 0
    invested_days = 0
    missed_positive_days = 0
    for t in range(59, len(closes) - 1):
        assessment = regime_aware_council(closes[:t + 1])
        decision = assessment["decision"]
        regime = assessment["market_regime"]
        decisions[decision] += 1
        regimes[regime] += 1
        veto_days += bool(assessment["regime_risk_veto"])
        invested = decision == "POSITIVE_RESEARCH"
        invested_days += invested
        if not invested and closes[t + 1] > closes[t]:
            missed_positive_days += 1
    days = len(closes) - 60
    return {
        "mode": "OFFLINE_DECISION_DIAGNOSTICS_NO_ORDERS",
        "evaluated_days": days,
        "decision_counts": dict(decisions),
        "regime_counts": dict(regimes),
        "risk_veto_days": veto_days,
        "positive_research_days": invested_days,
        "nonpositive_decision_before_up_day": missed_positive_days,
        "positive_research_fraction": round(invested_days / days, 6),
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Descriptive hindsight, not predictive skill. 'Missed' counts next-day up moves after cautious/mixed decisions, without estimating foregone profit. No strategy thresholds are tuned.",
    }
