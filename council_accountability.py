"""Explain the existing six rule-based council perspectives without trading.

These are deterministic heuristic scores, not six independent AI models.
"""
from math import isfinite
from regime_council import regime_aware_council
from decision_confirmation_experiment import confirmed_assessment
from six_brains import NAMES

def explain_council(closes, assessment_fn=regime_aware_council):
    if not isinstance(closes, (list, tuple)) or len(closes) < 60:
        raise ValueError("At least 60 closes required")
    if any(type(x) not in (int, float) or not isfinite(x) or x <= 0 for x in closes):
        raise ValueError("Invalid close")
    current = assessment_fn(closes)
    confirmation = confirmed_assessment(closes, assessment_fn)
    if not isinstance(current, dict) or not isinstance(confirmation, dict):
        raise ValueError("Invalid council response")
    if current.get("status") != "OK" or confirmation.get("status") != "OK":
        raise ValueError("Insufficient council assessment")
    scores = current.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(NAMES):
        raise ValueError("Incomplete council scores")
    for value in scores.values():
        if type(value) not in (float, int) or not isfinite(value) or not -1 <= value <= 1:
            raise ValueError("Invalid perspective score")
    positive = sum(score > 0 for score in scores.values())
    negative = sum(score < 0 for score in scores.values())
    neutral = sum(score == 0 for score in scores.values())
    veto = current.get("regime_risk_veto")
    if type(veto) is not bool:
        raise ValueError("Missing risk veto")
    original = current.get("decision")
    confirmed = confirmation.get("decision")
    if original not in ("POSITIVE_RESEARCH", "MIXED_RESEARCH", "CAUTIOUS_RESEARCH"):
        raise ValueError("Unexpected council decision")
    if confirmed not in ("POSITIVE_RESEARCH", "MIXED_RESEARCH", "CAUTIOUS_RESEARCH", "WAIT_FOR_CONFIRMATION"):
        raise ValueError("Unexpected confirmation decision")
    reasons = []
    if veto:
        reasons.append("High-risk market regime vetoed positive research")
    if confirmed == "WAIT_FOR_CONFIRMATION":
        reasons.append("Previous close did not confirm current positive research")
    if negative and positive:
        reasons.append("Council perspectives disagree")
    if not reasons:
        reasons.append("No additional veto, confirmation wait, or score disagreement")
    return {"status": "RESEARCH_EXPLANATION", "market_regime": current.get("market_regime"),
            "original_decision": original, "confirmed_decision": confirmed,
            "risk_veto": veto, "aggregate_score": current.get("aggregate_score"),
            "perspectives": {name: {"score": scores[name],
                "stance": "POSITIVE" if scores[name] > 0 else "NEGATIVE" if scores[name] < 0 else "NEUTRAL"}
                for name in NAMES},
            "agreement": {"positive": positive, "negative": negative, "neutral": neutral,
                          "mixed_signs": bool(positive and negative)},
            "reasons": reasons, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Transparent heuristic explanation, not causal attribution, calibrated confidence, investment advice or trading permission."}
