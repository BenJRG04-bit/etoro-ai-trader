"""Validate research-only council accountability report consistency.

A passing check is data integrity, not strategy performance or trade approval.
"""
from datetime import date
from math import isfinite
from historical_prices import WATCHLIST
from six_brains import NAMES

def validate_council_report(report):
    if not isinstance(report, dict) or report.get("status") != "RESEARCH_ACCOUNTABILITY_ONLY":
        raise ValueError("Invalid accountability report")
    if report.get("research_only") is not True or report.get("orders_allowed") is not False or report.get("live_trading_approved") is not False:
        raise ValueError("Unsafe accountability report")
    assets = report.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(WATCHLIST):
        raise ValueError("Unexpected asset universe")
    observed = unavailable = vetoes = disagreement = awaiting = 0
    for ticker, row in assets.items():
        if not isinstance(row, dict):
            raise ValueError("Invalid asset row")
        if row.get("status") == "UNAVAILABLE":
            unavailable += 1
            if not isinstance(row.get("error_type"), str):
                raise ValueError("Missing failure type")
            continue
        if row.get("status") != "OBSERVED_RESEARCH":
            raise ValueError("Unknown asset status")
        stamp = row.get("as_of")
        if not isinstance(stamp, str) or date.fromisoformat(stamp).isoformat() != stamp:
            raise ValueError("Invalid research date")
        price = row.get("close")
        if type(price) not in (int, float) or not isfinite(price) or price <= 0:
            raise ValueError("Invalid closing price")
        ex = row.get("explanation")
        if not isinstance(ex, dict) or ex.get("status") != "RESEARCH_EXPLANATION" or ex.get("research_only") is not True or ex.get("orders_allowed") is not False or ex.get("live_trading_approved") is not False:
            raise ValueError("Unsafe explanation")
        scores = ex.get("perspectives")
        if not isinstance(scores, dict) or set(scores) != set(NAMES):
            raise ValueError("Missing perspective")
        positive = negative = neutral = 0
        for name in NAMES:
            data = scores[name]
            if not isinstance(data, dict):
                raise ValueError("Malformed perspective")
            score = data.get("score")
            if type(score) not in (int, float) or not isfinite(score) or not -1 <= score <= 1:
                raise ValueError("Invalid score")
            stance = "POSITIVE" if score > 0 else "NEGATIVE" if score < 0 else "NEUTRAL"
            if data.get("stance") != stance:
                raise ValueError("Score and stance disagree")
            if score > 0: positive += 1
            elif score < 0: negative += 1
            else: neutral += 1
        agreement = ex.get("agreement")
        if not isinstance(agreement, dict) or any(type(agreement.get(k)) is not int for k in ("positive", "negative", "neutral")):
            raise ValueError("Invalid agreement")
        if (agreement["positive"], agreement["negative"], agreement["neutral"]) != (positive, negative, neutral):
            raise ValueError("Agreement counts inconsistent")
        if agreement.get("mixed_signs") is not bool(positive and negative):
            raise ValueError("Disagreement flag inconsistent")
        veto = ex.get("risk_veto")
        if type(veto) is not bool:
            raise ValueError("Invalid veto")
        original, confirmed = ex.get("original_decision"), ex.get("confirmed_decision")
        if original not in ("POSITIVE_RESEARCH", "CAUTIOUS_RESEARCH", "MIXED_RESEARCH"):
            raise ValueError("Invalid original decision")
        if confirmed not in ("POSITIVE_RESEARCH", "CAUTIOUS_RESEARCH", "MIXED_RESEARCH", "WAIT_FOR_CONFIRMATION"):
            raise ValueError("Invalid confirmed decision")
        if veto and (original != "CAUTIOUS_RESEARCH" or confirmed != "CAUTIOUS_RESEARCH"):
            raise ValueError("Vetoed decision not cautious")
        if confirmed == "WAIT_FOR_CONFIRMATION" and (original != "POSITIVE_RESEARCH" or veto):
            raise ValueError("Invalid confirmation wait")
        observed += 1
        vetoes += int(veto)
        disagreement += int(bool(positive and negative))
        awaiting += int(confirmed == "WAIT_FOR_CONFIRMATION")
    return {"status": "ACCOUNTABILITY_INTEGRITY_OK",
            "observed_assets": observed, "unavailable_assets": unavailable,
            "risk_veto_assets": vetoes, "disagreement_assets": disagreement,
            "awaiting_confirmation_assets": awaiting,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Structural validation only. Not a profitability, predictive accuracy or trading approval assessment."}
