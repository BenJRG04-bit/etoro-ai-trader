"""Research-only two-observation confirmation experiment.

A positive signal must appear at two consecutive closes. Risk vetoes always
apply immediately; no delayed safety exit. This is a fixed hypothesis, not
parameter optimization or authorization for trading.
"""
from portfolio_simulator import simulate_portfolio
from regime_council import regime_aware_council

def confirmed_assessment(closes, base_assessment=regime_aware_council):
    current = base_assessment(closes)
    if not isinstance(current, dict):
        raise ValueError("Invalid council assessment")
    if current.get("regime_risk_veto", False):
        return current
    if current.get("status") != "OK" or current.get("decision") != "POSITIVE_RESEARCH":
        return current
    previous = base_assessment(closes[:-1])
    if (not isinstance(previous, dict) or previous.get("status") != "OK"
            or previous.get("regime_risk_veto", False)
            or previous.get("decision") != "POSITIVE_RESEARCH"):
        return {**current, "decision": "WAIT_FOR_CONFIRMATION"}
    return current

def compare_confirmation(price_series, *, starting_cash=100.0,
                         fee_rates=(0.001, 0.005),
                         base_assessment=regime_aware_council):
    if not isinstance(fee_rates, (list, tuple)) or not fee_rates:
        raise ValueError("Missing fee scenarios")
    scenarios = {}
    for fee in fee_rates:
        baseline = simulate_portfolio(price_series, starting_cash=starting_cash,
                                      fee_rate=fee, assessment_fn=base_assessment)
        confirmed = simulate_portfolio(
            price_series, starting_cash=starting_cash, fee_rate=fee,
            assessment_fn=lambda closes: confirmed_assessment(closes, base_assessment))
        scenarios[str(fee)] = {
            "existing_council": baseline,
            "two_close_confirmation": confirmed,
            "confirmed_minus_existing_end_equity": round(
                confirmed["end_equity"] - baseline["end_equity"], 4),
            "rebalance_event_difference": confirmed["rebalance_events"] - baseline["rebalance_events"],
        }
    return {
        "status": "EXPLORATORY_ONLY",
        "scenarios": scenarios,
        "research_only": True, "orders_allowed": False, "live_trading_approved": False,
        "limitations": "Historical in-sample hypothesis only; confirmation can delay profitable entries and does not guarantee lower turnover, better returns or lower risk. Risk vetoes are never delayed. Same 5% total exposure, capital guard and simplified fees; no FX, spread, slippage, dividends or actual execution.",
    }
