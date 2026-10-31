"""Regime-aware research council. No orders, no brokerage access."""
from six_brains import council
from market_regime import classify_regime

def regime_aware_council(closes):
    base = council(closes)
    market = classify_regime(closes)
    result = dict(base)
    result["market_regime"] = market["regime"]
    result["regime_risk_veto"] = False
    if base["status"] != "OK" or market["regime"] == "INSUFFICIENT_DATA":
        return result
    # A high-risk regime can veto a positive research label.
    # Never upgrades a cautious or mixed assessment to positive.
    if market["regime"] == "HIGH_RISK":
        result["regime_risk_veto"] = True
        result["decision"] = "CAUTIOUS_RESEARCH"
    result["research_only"] = True
    return result
