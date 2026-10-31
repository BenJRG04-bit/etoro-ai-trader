"""Research-only multi-horizon severity of historical risk-veto signals.

Each observation is classified using only prices available at signal time.
Future outcomes are computed solely for retrospective evaluation.
Overlapping horizons are correlated and are NOT independent observations.
"""
from math import isfinite
from regime_council import regime_aware_council

HORIZONS = (1, 5, 20)

def _stats(values):
    ordered = sorted(values)
    count = len(values)
    return {
        "observations": count,
        "positive_count": sum(x > 0 for x in values),
        "negative_count": sum(x < 0 for x in values),
        "mean_return_fraction": round(sum(values) / count, 8) if count else None,
        "median_return_fraction": round((ordered[(count - 1) // 2] + ordered[count // 2]) / 2, 8) if count else None,
        "worst_return_fraction": round(ordered[0], 8) if count else None,
        "best_return_fraction": round(ordered[-1], 8) if count else None,
        "loss_at_least_5pct_count": sum(x <= -0.05 for x in values),
        "gain_at_least_5pct_count": sum(x >= 0.05 for x in values),
    }

def evaluate_risk_severity(closes, horizons=HORIZONS, assessment_fn=regime_aware_council):
    if not isinstance(closes, (list, tuple)) or len(closes) < 62:
        raise ValueError("At least 62 daily closes required")
    if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("All closes must be finite positive numbers")
    if not isinstance(horizons, (list, tuple)) or not horizons or any(type(h) is not int or h < 1 or h > 60 for h in horizons) or len(set(horizons)) != len(horizons):
        raise ValueError("Unique horizons of 1 to 60 days required")
    buckets = {h: {"veto": [], "non_veto": []} for h in horizons}
    veto_signals = non_veto_signals = 0
    for t in range(59, len(closes) - 1):
        decision = assessment_fn(closes[:t + 1])
        veto = decision["regime_risk_veto"]
        if type(veto) is not bool:
            raise ValueError("Risk veto must be boolean")
        if veto:
            veto_signals += 1
        else:
            non_veto_signals += 1
        for horizon in horizons:
            if t + horizon < len(closes):
                change = closes[t + horizon] / closes[t] - 1
                buckets[horizon]["veto" if veto else "non_veto"].append(change)
    return {
        "mode": "HISTORICAL_RISK_SEVERITY_RESEARCH_ONLY",
        "signal_days": {"veto": veto_signals, "non_veto": non_veto_signals},
        "horizons": {str(h): {name: _stats(values) for name, values in groups.items()} for h, groups in buckets.items()},
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Overlapping future windows, survivorship/selection effects and unadjusted prices; comparisons are descriptive not causal or predictive. No costs, dividends, FX or out-of-sample validation. No risk-rule changes.",
    }
