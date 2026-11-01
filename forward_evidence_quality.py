"""Conservative quality assessment for archived forward signal observations.

This is descriptive evidence, never a signal optimizer or trade permission.
"""
from collections import defaultdict

def assess_forward_evidence(audit, *, minimum_dates=20, minimum_signals=30):
    if not isinstance(audit, dict) or audit.get("status") != "RESEARCH_AUDIT":
        raise ValueError("Expected completed forward research audit")
    if type(minimum_dates) is not int or minimum_dates < 2:
        raise ValueError("Invalid minimum dates")
    if type(minimum_signals) is not int or minimum_signals < 2:
        raise ValueError("Invalid minimum signals")
    per_policy = {"original": defaultdict(lambda: {"signals": 0, "up": 0, "down": 0, "flat": 0}),
                  "confirmed": defaultdict(lambda: {"signals": 0, "up": 0, "down": 0, "flat": 0})}
    observed_dates = set()
    signal_dates = {"original": defaultdict(set), "confirmed": defaultdict(set)}
    for entry in audit.get("results", []):
        if entry.get("status") != "OBSERVED":
            continue
        stamp = entry["snapshot_date"]
        if stamp in observed_dates:
            raise ValueError("Duplicate observed date")
        observed_dates.add(stamp)
        obs = entry.get("evaluation", {}).get("observations", {})
        for ticker, value in obs.items():
            if value.get("status") != "OBSERVED":
                continue
            change = value["next_close_return"]
            if type(change) not in (int, float) or not -1 <= change < float("inf"):
                raise ValueError("Invalid return")
            for policy, key in (("original", "original_positive_at_snapshot"),
                                ("confirmed", "confirmed_positive_at_snapshot")):
                if value.get(key) is not True:
                    continue
                counts = per_policy[policy][ticker]
                counts["signals"] += 1
                counts["up" if change > 0 else "down" if change < 0 else "flat"] += 1
                signal_dates[policy][ticker].add(stamp)
    report = {}
    for policy in per_policy:
        assets = {}
        for ticker, counts in sorted(per_policy[policy].items()):
            distinct_dates = len(signal_dates[policy][ticker])
            adequate = distinct_dates >= minimum_dates and counts["signals"] >= minimum_signals
            assets[ticker] = {**counts, "distinct_signal_dates": distinct_dates,
                              "descriptive_up_fraction": round(counts["up"] / counts["signals"], 4),
                              "minimum_evidence_met": adequate}
        report[policy] = assets
    return {"status": "RESEARCH_EVIDENCE_ONLY",
            "observed_snapshot_dates": len(observed_dates),
            "minimum_distinct_dates": minimum_dates,
            "minimum_positive_signals": minimum_signals,
            "policies": report, "research_only": True, "orders_allowed": False,
            "live_trading_approved": False,
            "limitations": "Counts positive signals followed by next-close rises, not profitability, skill, independent observations, a calibrated forecast, or statistical significance. Overlapping assets and clustered dates are correlated. Insufficient evidence does not imply failure or success."}
