"""Synthetic, offline portfolio shock probes; not forecasts."""
from math import isfinite
from portfolio_benchmark import compare_portfolio_policies


def shock_prices(prices, fraction=-0.25):
    if not isinstance(prices, dict) or not prices:
        raise ValueError("Missing prices")
    if type(fraction) not in (int, float) or not isfinite(fraction) or not -0.9 <= fraction <= 0:
        raise ValueError("Invalid shock")
    lengths = {len(v) for v in prices.values() if isinstance(v, (list, tuple))}
    if len(lengths) != 1 or any(not isinstance(v, (list, tuple)) for v in prices.values()):
        raise ValueError("Unaligned prices")
    n = lengths.pop()
    if n < 62:
        raise ValueError("Insufficient prices")
    index = n // 2
    result = {}
    for ticker, values in prices.items():
        if not isinstance(ticker, str) or not ticker or any(type(p) not in (int, float) or not isfinite(p) or p <= 0 for p in values):
            raise ValueError("Invalid prices")
        result[ticker] = [float(p) * (1 + fraction) if i > index else float(p) for i, p in enumerate(values)]
    return result


def stress_audit(prices, fee_rates=(0.001, 0.005)):
    cases = {}
    for name, fraction in (("unchanged", 0.0), ("drop_10pct", -0.10), ("drop_25pct", -0.25)):
        comparison = compare_portfolio_policies(shock_prices(prices, fraction), fee_rates=fee_rates)
        cases[name] = {}
        for fee, scenario in comparison["scenarios"].items():
            cases[name][fee] = {}
            for policy in ("council_guarded", "equal_weight_capped_hold"):
                result = scenario[policy]
                cases[name][fee][policy] = {
                    "end_equity": result["end_equity"],
                    "max_drawdown_fraction": result["max_drawdown_fraction"],
                    "profit_given_back_fraction": result["profit_protection_audit"]["peak_profit_given_back_fraction"],
                    "halted": result["halted"],
                    "max_observed_total_allocation": result["max_observed_total_allocation"]}
    return {"status": "SYNTHETIC_STRESS_ONLY", "cases": cases, "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Uniform synthetic shock applied after the series midpoint; not a crash forecast or probability. Simplified execution and 5% exposure cap; no spreads, slippage, FX, dividends or taxes."}
