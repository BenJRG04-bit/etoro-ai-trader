"""Illustrative offline friction sensitivity; never a brokerage price quote."""
from math import isfinite

def cost_scenario(budget, *, exposure=0.05, count=1, minimum=1.0,
                  fee=0.001, spread=0.001, slippage=0.001, fx=0.005):
    values = (budget, exposure, minimum, fee, spread, slippage, fx)
    if any(type(v) not in (int, float) or not isfinite(v) for v in values):
        raise ValueError("Nonfinite or nonnumeric input")
    if type(count) is not int or count < 1 or not 0 < budget <= 100:
        raise ValueError("Invalid budget or count")
    if not 0 <= exposure <= 0.05 or minimum <= 0:
        raise ValueError("Invalid exposure or minimum")
    if any(not 0 <= x < 1 for x in (fee, spread, slippage, fx)):
        raise ValueError("Invalid cost rate")
    notional = budget * exposure / count
    possible = notional >= minimum
    roundtrip = 2 * (fee + spread / 2 + slippage + fx)
    return {
        "status": "ABOVE_ASSUMED_MINIMUM" if possible else "BELOW_ASSUMED_MINIMUM",
        "budget": budget, "assets": count, "per_asset_notional": round(notional, 6),
        "total_exposure_cap": round(budget * exposure, 6),
        "assumed_minimum": minimum, "estimated_roundtrip_cost_fraction": round(roundtrip, 8),
        "estimated_roundtrip_cost": round(notional * count * roundtrip, 6) if possible else None,
        "research_only": True, "orders_allowed": False, "live_trading_approved": False,
        "limitations": "Illustrative linear roundtrip model only. Not eToro pricing or executable order sizing. "
                       "Assumes fee, half-spread, slippage and FX on each leg. No taxes or fixed costs.",
    }

def study():
    return {"status": "ILLUSTRATIVE_COST_STRESS_ONLY",
            "scenarios": [cost_scenario(b, count=n, minimum=m)
                          for b in (20, 40, 100) for n in (1, 5) for m in (1, 10)],
            "research_only": True, "orders_allowed": False, "live_trading_approved": False}

if __name__ == "__main__":
    import json
    from pathlib import Path
    Path("execution_cost_study.json").write_text(json.dumps(study(), indent=2) + "\n", encoding="utf-8")
