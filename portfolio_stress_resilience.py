"""Cross-scenario stress resilience checks; no tuning or trade authorization."""
import json
from math import isfinite
from pathlib import Path

POLICIES = ("council_guarded", "equal_weight_capped_hold")


def assess_stress_resilience(stress, *, maximum_exposure=.05):
    if not isinstance(stress, dict) or stress.get("research_only") is not True or stress.get("orders_allowed") is not False or stress.get("live_trading_approved") is not False:
        raise ValueError("Unsafe stress report")
    if stress.get("status") == "UNAVAILABLE":
        return {"status": "UNAVAILABLE", "issues": ["STRESS_INPUT_UNAVAILABLE"],
                "research_only": True, "orders_allowed": False, "live_trading_approved": False}
    if stress.get("status") != "SYNTHETIC_STRESS_ONLY":
        raise ValueError("Invalid stress status")
    if type(maximum_exposure) not in (int, float) or not isfinite(maximum_exposure) or not 0 <= maximum_exposure <= .05:
        raise ValueError("Invalid exposure limit")
    cases = stress.get("cases")
    if not isinstance(cases, dict) or set(cases) != {"unchanged", "drop_10pct", "drop_25pct"}:
        raise ValueError("Incomplete stress scenarios")
    fee_sets = [set(cases[name]) for name in ("unchanged", "drop_10pct", "drop_25pct")]
    if not fee_sets[0] or any(s != fee_sets[0] for s in fee_sets):
        raise ValueError("Inconsistent fee scenarios")
    rows = {}
    issues = []
    for fee in sorted(fee_sets[0]):
        try:
            fee_value = float(fee)
        except (ValueError, TypeError):
            raise ValueError("Invalid fee key") from None
        if not isfinite(fee_value) or not 0 <= fee_value < 1:
            raise ValueError("Invalid fee value")
        rows[fee] = {}
        for policy in POLICIES:
            samples = {}
            for scenario in ("unchanged", "drop_10pct", "drop_25pct"):
                group = cases[scenario][fee]
                if not isinstance(group, dict) or set(group) != set(POLICIES):
                    raise ValueError("Incomplete policy comparison")
                row = group[policy]
                if not isinstance(row, dict) or type(row.get("halted")) is not bool:
                    raise ValueError("Invalid policy result")
                for key in ("end_equity", "max_drawdown_fraction", "max_observed_total_allocation"):
                    value = row.get(key)
                    if type(value) not in (int, float) or not isfinite(value):
                        raise ValueError("Invalid stress metric")
                if row["end_equity"] <= 0 or not 0 <= row["max_drawdown_fraction"] <= 1 or not 0 <= row["max_observed_total_allocation"] <= .05:
                    raise ValueError("Out-of-range stress metric")
                giveback = row.get("profit_given_back_fraction")
                if giveback is not None and (type(giveback) not in (int, float) or not isfinite(giveback) or not 0 <= giveback <= 1):
                    raise ValueError("Invalid profit giveback")
                if row["max_observed_total_allocation"] > maximum_exposure + 1e-10:
                    issues.append(f"EXPOSURE_LIMIT_EXCEEDED:{fee}:{scenario}:{policy}")
                samples[scenario] = row
            rows[fee][policy] = {
                "normal_end_equity": samples["unchanged"]["end_equity"],
                "drop_10pct_end_equity": samples["drop_10pct"]["end_equity"],
                "drop_25pct_end_equity": samples["drop_25pct"]["end_equity"],
                "drop_25pct_minus_normal_equity": round(samples["drop_25pct"]["end_equity"] - samples["unchanged"]["end_equity"], 4),
                "worst_scenario_drawdown_fraction": max(row["max_drawdown_fraction"] for row in samples.values()),
                "any_capital_guard_halt": any(row["halted"] for row in samples.values()),
            }
    return {"status": "SAFETY_ISSUES" if issues else "DESCRIPTIVE_STRESS_REVIEW",
            "issues": issues, "fee_scenarios": rows, "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Synthetic shock sensitivity, not a pass/fail prediction of real market resilience. No probability calibration, no guaranteed profit protection, no broker execution."}


if __name__ == "__main__":
    stress = json.loads(Path("portfolio_stress_report.json").read_text(encoding="utf-8"))
    report = assess_stress_resilience(stress)
    Path("portfolio_stress_resilience.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"], report["issues"])
