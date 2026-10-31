"""Research-only strategy comparison labels. No orders or broker connections."""
from regime_council import regime_aware_council

def research_strategy_selection(closes):
    """Classify which strategy families merit offline comparison, not investment advice."""
    assessment = regime_aware_council(closes)
    regime = assessment["market_regime"]
    decision = assessment["decision"]
    result = {
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "market_regime": regime,
        "council_decision": decision,
        "candidate_strategies": [],
        "reason": "No reliable assessment",
    }
    if assessment["status"] != "OK" or regime == "INSUFFICIENT_DATA":
        return result
    if assessment["regime_risk_veto"] or regime == "HIGH_RISK":
        result["reason"] = "High-risk regime: withhold directional candidates"
        return result
    if regime == "UPTREND" and decision == "POSITIVE_RESEARCH":
        result["candidate_strategies"] = ["trend_following", "buy_and_hold_benchmark"]
        result["reason"] = "Compare trend strategies against a passive benchmark"
    elif regime == "SIDEWAYS":
        result["candidate_strategies"] = ["mean_reversion", "buy_and_hold_benchmark"]
        result["reason"] = "Compare sideways-market hypotheses against a benchmark"
    else:
        result["candidate_strategies"] = ["buy_and_hold_benchmark"]
        result["reason"] = "Benchmark-only comparison under uncertain or weak conditions"
    return result
