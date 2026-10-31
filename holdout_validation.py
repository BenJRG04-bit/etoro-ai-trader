"""Freeze a strategy configuration before evaluating an untouched holdout.

This is a procedural validation guard, not proof of a genuine holdout:
the operator must ensure the holdout prices were not inspected or used
to choose strategy rules, thresholds or parameters.
"""
import hashlib
import json
from math import isfinite
from adaptive_comparison import compare_regime_strategy

DEFAULT_CONFIG = {"strategy": "regime_risk_veto_v1", "fee_rate": 0.001,
                  "max_allocation": 0.05, "starting_cash": 1000.0}

def config_fingerprint(config):
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def evaluate_holdout(closes, config=None, warmup=60, holdout_size=60):
    cfg = dict(DEFAULT_CONFIG if config is None else config)
    if set(cfg) != set(DEFAULT_CONFIG) or cfg["strategy"] != DEFAULT_CONFIG["strategy"]:
        raise ValueError("Unknown or incomplete frozen strategy configuration")
    if not isinstance(warmup, int) or warmup != 60:
        raise ValueError("Exactly 60 warmup closes required")
    if not isinstance(holdout_size, int) or holdout_size < 2:
        raise ValueError("Holdout must contain at least two closes")
    if len(closes) < warmup + holdout_size:
        raise ValueError("Not enough closes for holdout")
    if any(not isfinite(p) or p <= 0 for p in closes):
        raise ValueError("Invalid close prices")
    # The final holdout_size closes are the evaluation segment. The previous
    # 60 closes are used only for indicator warmup.
    start = len(closes) - holdout_size
    sample = closes[start - warmup:]
    comparison = compare_regime_strategy(
        sample, starting_cash=cfg["starting_cash"],
        fee_rate=cfg["fee_rate"], max_allocation=cfg["max_allocation"])
    return {
        "mode": "HOLDOUT_EVALUATION_NO_ORDERS",
        "config_sha256": config_fingerprint(cfg),
        "holdout_start_index": start,
        "holdout_end_index_exclusive": len(closes),
        "comparison": comparison,
        "research_only": True,
        "warning": ("Only qualifies as untouched out-of-sample evaluation if "
                    "the holdout was never inspected or used for strategy development. "
                    "One holdout cannot establish future profitability.")
    }
