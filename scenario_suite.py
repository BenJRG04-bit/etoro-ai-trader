"""Offline deterministic market-scenario comparison. Not forecasts or trade advice."""
from adaptive_comparison import compare_regime_strategy

def sample_scenarios(length=180):
    if length < 62:
        raise ValueError("Need at least 62 observations")
    # Synthetic prices, not historical observations.
    return {
        "rising": [100 * (1.002 ** i) for i in range(length)],
        "falling": [100 * (0.998 ** i) for i in range(length)],
        "sideways": [100 * (1 + 0.008 * ((i % 10) - 4.5) / 4.5) for i in range(length)],
        "shock": [100 * (1.001 ** i) * (0.72 if i >= length // 2 else 1)
                  for i in range(length)],
        "crash_recovery": [100 * (1.001 ** i) * (0.65 if length // 3 <= i < 2 * length // 3 else 1)
                           for i in range(length)],
        "volatile": [100 * (1 + 0.06 * ((-1) ** i)) for i in range(length)],
    }

def run_scenario_suite(starting_cash=1000.0, fee_rate=0.001, max_allocation=0.05):
    results = {}
    for name, prices in sample_scenarios().items():
        results[name] = compare_regime_strategy(
            prices, starting_cash=starting_cash, fee_rate=fee_rate,
            max_allocation=max_allocation)
    return {
        "mode": "SYNTHETIC_SCENARIO_RESEARCH_NO_ORDERS",
        "scenarios": results,
        "research_only": True,
        "limitations": "Synthetic scenarios only. Not real market data, independent validation or evidence of profitability."
    }

if __name__ == "__main__":
    import json
    print(json.dumps(run_scenario_suite(), indent=2))
