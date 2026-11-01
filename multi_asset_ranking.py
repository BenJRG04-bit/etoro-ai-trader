"""Fail-closed, research-only cross-asset candidate ranking.

Scores supplied, independently validated research observations. Never queries
a broker, fetches live prices, or authorizes an order. No claims of profit.
"""
import math

ASSET_CLASSES = frozenset(("stock", "etf", "crypto", "forex", "commodity"))
MIN_HOLDOUT = 100
MAX_DRAWDOWN = 0.10
MAX_COST_FRACTION = 0.01


def _finite_number(value):
    return type(value) in (float, int) and math.isfinite(value)


def rank_candidates(candidates):
    """Return eligible ranked research candidates and excluded reasons.

    Required fields: symbol, asset_class, holdout_samples, excess_return,
    max_drawdown, estimated_round_trip_cost_fraction, validated, data_fresh.
    All return/drawdown/cost fractions use decimals, not percentages.
    """
    ranked, excluded = [], []
    seen = set()
    for candidate in candidates:
        symbol = candidate.get("symbol")
        reasons = []
        if not isinstance(symbol, str) or not symbol or symbol in seen:
            reasons.append("missing_or_duplicate_symbol")
        if isinstance(symbol, str):
            seen.add(symbol)
        if candidate.get("asset_class") not in ASSET_CLASSES:
            reasons.append("unsupported_asset_class")
        if candidate.get("validated") is not True:
            reasons.append("unvalidated_research")
        if candidate.get("data_fresh") is not True:
            reasons.append("stale_or_missing_data")
        samples = candidate.get("holdout_samples")
        if type(samples) is not int or samples < MIN_HOLDOUT:
            reasons.append("insufficient_holdout")
        for field in ("excess_return", "max_drawdown", "estimated_round_trip_cost_fraction"):
            if not _finite_number(candidate.get(field)):
                reasons.append("invalid_" + field)
        if not reasons:
            edge = candidate["excess_return"]
            dd = candidate["max_drawdown"]
            cost = candidate["estimated_round_trip_cost_fraction"]
            if edge <= 0:
                reasons.append("no_positive_out_of_sample_edge")
            if dd < 0 or dd > MAX_DRAWDOWN:
                reasons.append("drawdown_limit")
            if cost < 0 or cost > MAX_COST_FRACTION:
                reasons.append("cost_limit")
            if edge <= cost:
                reasons.append("edge_not_above_cost")
        if reasons:
            excluded.append({"symbol": symbol, "reasons": reasons})
        else:
            # Explicitly a heuristic, NOT expected profit or calibrated probability.
            score = (edge - cost) / (1 + 5 * dd)
            ranked.append({"symbol": symbol, "asset_class": candidate["asset_class"],
                           "research_score": round(score, 8),
                           "holdout_samples": samples})
    ranked.sort(key=lambda item: (-item["research_score"], item["symbol"]))
    return {"mode": "RESEARCH_ONLY_NO_ORDERS", "ranked": ranked,
            "excluded": excluded, "total_checked": len(ranked) + len(excluded),
            "orders_allowed": False,
            "warning": "Scores are not profit forecasts. Validation must be independent and chronological."}
