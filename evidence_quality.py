"""Conservative evidence-quality gates for retrospective holdout risk studies.

These gates assess *sample adequacy*, never authorize trades or claim alpha.
"""
from math import isfinite

def assess_evidence_quality(audit, min_signals_per_group=30, horizons=("1", "5", "20")):
    if type(min_signals_per_group) is not int or min_signals_per_group < 10:
        raise ValueError("Minimum group size must be an integer >= 10")
    if not isinstance(audit, dict) or "segments" not in audit:
        raise ValueError("Invalid audit")
    results = {}
    for horizon in horizons:
        counts = {}
        reasons = []
        for segment in ("earlier", "later_holdout"):
            for group in ("veto", "non_veto"):
                item = audit["segments"][segment]["horizons"][horizon][group]
                n = item["observations"]
                if type(n) is not int or n < 0:
                    raise ValueError("Invalid observation count")
                key = segment + "_" + group
                counts[key] = n
                if n < min_signals_per_group:
                    reasons.append(key + "_INSUFFICIENT_SAMPLE")
                mean = item["mean_forward_return_fraction"]
                if n == 0 and mean is not None:
                    raise ValueError("Empty group cannot have a mean")
                if n > 0 and (type(mean) not in (int, float) or not isfinite(mean)):
                    raise ValueError("Invalid mean")
        results[horizon] = {
            "counts": counts,
            "sample_adequate": not reasons,
            "warnings": reasons,
        }
    return {
        "status": "DESCRIPTIVE_SAMPLE_ADEQUACY_ONLY",
        "horizons": results,
        "all_horizons_sample_adequate": all(x["sample_adequate"] for x in results.values()),
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Adequate counts do not establish independent samples, causality, statistical significance, forecast quality, or profitable execution. Overlapping windows inflate effective sample size; a viewed holdout is not untouched.",
    }
