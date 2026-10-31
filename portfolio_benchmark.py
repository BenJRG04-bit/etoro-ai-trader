"""Compare fixed offline shared-portfolio policies on exactly the same price dates.

Both policies use a single hypothetical account, the same 5% TOTAL exposure,
the same fee and capital guard. Neither places orders or learns/tunes parameters.
"""
from portfolio_simulator import simulate_portfolio

def _always_eligible(_closes):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

def compare_portfolio_policies(price_series, *, starting_cash=100.0,
                               fee_rates=(0.001, 0.005)):
    if not isinstance(fee_rates, (tuple, list)) or not fee_rates:
        raise ValueError("Provide fee scenarios")
    scenarios = {}
    for fee in fee_rates:
        if type(fee) not in (float, int) or not 0 <= fee < 1:
            raise ValueError("Invalid fee scenario")
        # Use the same historical prices and 5% total exposure for both.
        guarded = simulate_portfolio(price_series, starting_cash=starting_cash,
                                     fee_rate=fee)
        benchmark = simulate_portfolio(price_series, starting_cash=starting_cash,
                                       fee_rate=fee, assessment_fn=_always_eligible)
        scenarios[str(fee)] = {
            "council_guarded": guarded,
            "equal_weight_capped_hold": benchmark,
            "council_minus_hold": round(guarded["end_equity"] - benchmark["end_equity"], 4),
        }
    return {
        "scenarios": scenarios,
        "research_only": True,
        "orders_allowed": False,
        "live_trading_approved": False,
        "limitations": "Retrospective in-sample comparison. Equal-weight capped hold rebalances to fixed target weights; not a full-investment buy-and-hold. Same 5% total allocation and guard for both. No FX, spread, slippage, dividends, taxes, or actual execution. Fee sensitivity is not a forecast.",
    }
