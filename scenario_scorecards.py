"""Compare Project E.T. research strategies across synthetic market regimes.

All prices are artificial; no orders, forecasts, or profitability claims.
"""
from scenario_suite import sample_scenarios
from research_scorecard import research_scorecard


def run_scenario_scorecards(starting_cash=1000.0, fee_rate=0.001,
                            max_allocation=0.05):
    scenarios = {}
    for name, closes in sample_scenarios().items():
        scenarios[name] = research_scorecard(
            closes, starting_cash=starting_cash, fee_rate=fee_rate,
            max_allocation=max_allocation
        )
    return {
        "mode": "SYNTHETIC_SCORECARDS_NO_ORDERS",
        "scenarios": scenarios,
        "scenario_count": len(scenarios),
        "research_only": True,
        "live_trading_approved": False,
        "limitations": (
            "Artificial deterministic prices only, not historical evidence, "
            "forward validation, or a forecast. No real brokerage access."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_scenario_scorecards(), indent=2))
