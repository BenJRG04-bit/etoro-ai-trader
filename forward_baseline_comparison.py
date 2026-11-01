"""Descriptive forward signal vs same-date market baseline; never trading approval."""
import json
import math
from pathlib import Path


def compare_to_baseline(audit, *, minimum_dates=20):
    if not isinstance(audit, dict) or audit.get("status") != "RESEARCH_AUDIT":
        raise ValueError("Expected forward research audit")
    if audit.get("research_only") is not True or audit.get("orders_allowed") is not False or audit.get("live_trading_approved") is not False:
        raise ValueError("Unsafe audit flags")
    if type(minimum_dates) is not int or minimum_dates < 2:
        raise ValueError("Invalid minimum_dates")
    dates = set()
    per_policy = {p: {"signal_up": 0, "signal_count": 0, "matched_market_up": 0, "matched_market_count": 0} for p in ("original", "confirmed")}
    for entry in audit.get("results", []):
        if entry.get("status") != "OBSERVED":
            continue
        stamp = entry.get("snapshot_date")
        if not isinstance(stamp, str) or stamp in dates:
            raise ValueError("Missing or duplicate observed date")
        dates.add(stamp)
        observations = (entry.get("evaluation") or {}).get("observations", {})
        if not isinstance(observations, dict):
            raise ValueError("Invalid observations")
        for asset in observations.values():
            if asset.get("status") != "OBSERVED":
                continue
            change = asset.get("next_close_return")
            if type(change) not in (int, float) or not math.isfinite(change) or change < -1:
                raise ValueError("Invalid next close return")
            for policy, flag in (("original", "original_positive_at_snapshot"), ("confirmed", "confirmed_positive_at_snapshot")):
                if asset.get(flag) not in (True, False):
                    raise ValueError("Invalid signal flag")
                row = per_policy[policy]
                row["matched_market_count"] += 1
                row["matched_market_up"] += int(change > 0)
                if asset[flag]:
                    row["signal_count"] += 1
                    row["signal_up"] += int(change > 0)
    comparisons = {}
    for policy, counts in per_policy.items():
        signals = counts["signal_count"]
        market = counts["matched_market_count"]
        comparisons[policy] = {**counts,
            "signal_up_fraction": round(counts["signal_up"] / signals, 4) if signals else None,
            "same_dates_market_up_fraction": round(counts["matched_market_up"] / market, 4) if market else None,
            "descriptive_difference": round(counts["signal_up"] / signals - counts["matched_market_up"] / market, 4) if signals and market else None}
    return {"status": "DESCRIPTIVE_ONLY", "observed_dates": len(dates),
        "minimum_dates": minimum_dates, "enough_dates_for_review": len(dates) >= minimum_dates,
        "comparisons": comparisons, "research_only": True, "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Unconditional same-date asset direction is a descriptive baseline, not buy-and-hold P&L. Asset selection and correlated dates bias comparisons; no transaction costs, execution, risk adjustment or significance tests. Never infer profitable skill."}


if __name__ == "__main__":
    audit = json.loads(Path("forward_batch_audit_report.json").read_text(encoding="utf-8"))
    Path("forward_baseline_comparison.json").write_text(json.dumps(compare_to_baseline(audit), indent=2) + "\n", encoding="utf-8")
