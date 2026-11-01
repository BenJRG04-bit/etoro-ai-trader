"""Single fail-closed, offline research decision gateway; no brokerage connection."""
from math import isfinite
from regime_council import regime_aware_council


def central_research_decision(price_series, *, max_total_allocation=0.05, assessment_fn=regime_aware_council):
    if type(max_total_allocation) not in (int, float) or not isfinite(max_total_allocation) or not 0 <= max_total_allocation <= .05:
        raise ValueError("Unsafe allocation cap")
    if not isinstance(price_series, dict) or not price_series:
        raise ValueError("Missing market data")
    if not callable(assessment_fn):
        raise ValueError("Invalid council")
    decisions = {}
    for ticker, closes in sorted(price_series.items()):
        if not isinstance(ticker, str) or not ticker or not isinstance(closes, (list, tuple)) or len(closes) < 60:
            raise ValueError("Insufficient market history")
        if any(type(x) not in (int, float) or not isfinite(x) or x <= 0 for x in closes):
            raise ValueError("Invalid market history")
        result = assessment_fn(closes)
        if not isinstance(result, dict) or result.get("status") != "OK":
            decisions[ticker] = {"label": "NO_DECISION", "reason": "COUNCIL_UNAVAILABLE"}
        elif result.get("regime_risk_veto") is True:
            decisions[ticker] = {"label": "AVOID_RESEARCH", "reason": "MARKET_RISK_VETO"}
        elif result.get("decision") == "POSITIVE_RESEARCH":
            decisions[ticker] = {"label": "ELIGIBLE_FOR_SIMULATION", "reason": "POSITIVE_RESEARCH_ONLY"}
        else:
            decisions[ticker] = {"label": "WAIT_RESEARCH", "reason": "NO_POSITIVE_CONSENSUS"}
    eligible = [ticker for ticker, row in decisions.items() if row["label"] == "ELIGIBLE_FOR_SIMULATION"]
    weight = max_total_allocation / len(eligible) if eligible else 0.0
    allocations = {ticker: round(weight if ticker in eligible else 0.0, 12) for ticker in decisions}
    return {"status": "RESEARCH_ONLY", "decisions": decisions,
            "hypothetical_target_allocations": allocations,
            "total_hypothetical_allocation": round(sum(allocations.values()), 12),
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Council heuristic research labels are not orders or validated forecasts. Allocation is hypothetical only; no execution or portfolio state."}
