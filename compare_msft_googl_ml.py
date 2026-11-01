"""Compare MSFT and GOOGL using Project E.T.'s existing free local ML.

This is research, not a recommendation or an order. Refuse to rank assets
unless both have sufficient out-of-sample evidence.
"""
import json
from local_ml_research import run_local_ml_research

CANDIDATES = ("MSFT", "GOOGL")
MIN_HOLDOUT = 60


def compare_candidates(fetcher=None):
    kwargs = {"tickers": CANDIDATES}
    if fetcher is not None:
        kwargs["fetcher"] = fetcher
    result = run_local_ml_research(**kwargs)
    assessments = {}
    for symbol in CANDIDATES:
        item = result["assets"][symbol]
        valid = (item.get("status") == "EXPLORATORY_HOLDOUT_ONLY"
                 and item.get("holdout_samples", 0) >= MIN_HOLDOUT)
        edge = (item["hypothetical_model_simple_return_fraction"]
                - item["hypothetical_capped_hold_simple_return_fraction"]) if valid else None
        assessments[symbol] = {
            "status": item.get("status"), "valid_holdout": valid,
            "holdout_samples": item.get("holdout_samples"),
            "holdout_accuracy": item.get("holdout_accuracy"),
            "majority_baseline_accuracy": item.get("majority_class_baseline_accuracy"),
            "illustrative_edge_vs_passive_fraction": round(edge, 6) if edge is not None else None,
            "latest_up_probability_uncalibrated": item.get("latest_model_up_probability_uncalibrated"),
            "error_type": item.get("error_type"),
        }
    eligible = [s for s, a in assessments.items()
                if a["valid_holdout"]
                and a["illustrative_edge_vs_passive_fraction"] > 0
                and a["holdout_accuracy"] > a["majority_baseline_accuracy"]]
    # Even passing these exploratory filters is not sufficient to authorize a trade.
    ranked = sorted(eligible, key=lambda s: assessments[s]["illustrative_edge_vs_passive_fraction"], reverse=True)
    return {"mode": "RESEARCH_ONLY_NO_ORDERS", "candidates": assessments,
            "exploratory_shortlist": ranked, "trade_authorized": False,
            "requires_walk_forward_validation": True,
            "requires_execution_cost_validation": True,
            "requires_market_hours_check": True,
            "requires_manual_demo_order_approval": True,
            "model_probabilities_calibrated": False}


if __name__ == "__main__":
    print(json.dumps(compare_candidates(), indent=2))
