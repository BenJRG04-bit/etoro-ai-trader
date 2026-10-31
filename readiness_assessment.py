"""Conservative research readiness assessment, never a live-trading approval."""
from historical_summary import summarize

def assess_research_readiness(report):
    summary = summarize(report)
    rows = summary["assets"]
    evaluated = [row for row in rows if row["status"] == "EVALUATED"]
    missing = [row["ticker"] for row in rows if row["status"] != "EVALUATED"]
    total_windows = sum(row["windows"] for row in evaluated)
    # No profit threshold can substitute for independent validation.
    checks = {
        "all_assets_evaluated": len(rows) == 5 and len(evaluated) == 5,
        "multiple_windows_each": len(evaluated) == 5 and all(
            row["windows"] >= 2 for row in evaluated),
        "fees_modelled_simplistically": True,
        "independent_untouched_holdout_verified": False,
        "spread_slippage_dividends_taxes_modelled": False,
        "demo_forward_performance_verified": False,
    }
    return {
        "mode": "RESEARCH_READINESS_NO_ORDERS",
        "status": "NOT_READY_FOR_LIVE_TRADING",
        "checks": checks,
        "evaluated_assets": len(evaluated),
        "total_evaluation_windows": total_windows,
        "unavailable_assets": missing,
        "summary": summary,
        "research_only": True,
        "limitations": ("Historical window summaries are not independently verified "
                        "out-of-sample results. No automated approval for real trading.")
    }
