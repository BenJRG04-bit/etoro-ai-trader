"""Paired forward directional attribution on immutable archived snapshots.

Measures selection vs the same observed asset/date universe; NOT P&L or causal alpha.
"""
import json
from math import isfinite
from pathlib import Path


def forward_attribution(audit, minimum_dates=20):
    if not isinstance(audit, dict) or audit.get("status") != "RESEARCH_AUDIT" or audit.get("research_only") is not True or audit.get("orders_allowed") is not False or audit.get("live_trading_approved") is not False:
        raise ValueError("Unsafe or unavailable forward audit")
    if type(minimum_dates) is not int or minimum_dates < 2:
        raise ValueError("Invalid minimum dates")
    results = audit.get("results")
    if not isinstance(results, list):
        raise ValueError("Invalid results")
    dates = set()
    policies = {name: {"signals": 0, "signal_up": 0, "matched_assets": 0,
                       "matched_up": 0, "signal_return_sum": 0.0, "matched_return_sum": 0.0,
                       "observed_dates_with_signals": set()} for name in ("original", "confirmed")}
    for entry in results:
        if not isinstance(entry, dict) or entry.get("status") != "OBSERVED":
            continue
        date = entry.get("snapshot_date")
        if not isinstance(date, str) or not date or date in dates:
            raise ValueError("Missing or duplicate observed snapshot date")
        dates.add(date)
        evaluation = entry.get("evaluation")
        observations = evaluation.get("observations") if isinstance(evaluation, dict) else None
        if not isinstance(observations, dict):
            raise ValueError("Invalid observations")
        for asset in observations.values():
            if not isinstance(asset, dict) or asset.get("status") != "OBSERVED":
                continue
            change = asset.get("next_close_return")
            if type(change) not in (int, float) or not isfinite(change) or change < -1:
                raise ValueError("Invalid forward return")
            for name, flag in (("original", "original_positive_at_snapshot"), ("confirmed", "confirmed_positive_at_snapshot")):
                selected = asset.get(flag)
                if type(selected) is not bool:
                    raise ValueError("Missing recorded signal flag")
                row = policies[name]
                row["matched_assets"] += 1
                row["matched_up"] += int(change > 0)
                row["matched_return_sum"] += change
                if selected:
                    row["signals"] += 1
                    row["signal_up"] += int(change > 0)
                    row["signal_return_sum"] += change
                    row["observed_dates_with_signals"].add(date)
    summary = {}
    for name, row in policies.items():
        count, universe = row["signals"], row["matched_assets"]
        summary[name] = {
            "positive_signals": count, "observed_dates_with_signals": len(row["observed_dates_with_signals"]),
            "same_date_asset_observations": universe,
            "signal_up_fraction": round(row["signal_up"] / count, 6) if count else None,
            "same_date_asset_up_fraction": round(row["matched_up"] / universe, 6) if universe else None,
            "mean_selected_next_close_return": round(row["signal_return_sum"] / count, 8) if count else None,
            "mean_unconditional_next_close_return": round(row["matched_return_sum"] / universe, 8) if universe else None,
            "selection_minus_unconditional_mean_return": round(row["signal_return_sum"] / count - row["matched_return_sum"] / universe, 8) if count and universe else None,
        }
    return {"status": "MORE_EVIDENCE_REQUIRED" if len(dates) < minimum_dates else "DESCRIPTIVE_FORWARD_ONLY",
            "observed_dates": len(dates), "minimum_dates": minimum_dates, "policies": summary,
            "strategy_approved": False, "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Observed forward next-close direction/return is not executed strategy P&L. Selected assets and unconditional same-date universe differ; correlated dates/assets, sample selection, missing observations, fees, FX and slippage prevent claims of causal alpha or profitable trading. Minimum dates is only a coverage gate."}


if __name__ == "__main__":
    audit = json.loads(Path("forward_batch_audit_report.json").read_text(encoding="utf-8"))
    Path("forward_attribution_report.json").write_text(json.dumps(forward_attribution(audit), indent=2) + "\n", encoding="utf-8")
