"""Human-readable offline research summary, not an investment recommendation."""
from historical_research_pipeline import run_historical_research


def summarize_research(result):
    if result.get("mode") != "HISTORICAL_RESEARCH_NO_ORDERS":
        raise ValueError("Unrecognized research report")
    rows = {}
    for ticker, asset in result["assets"].items():
        if asset["status"] != "EXPLORATORY_ONLY":
            rows[ticker] = {"status": "UNAVAILABLE", "reason": asset.get("error_type", "UNKNOWN")}
            continue
        windows = asset["evaluation"]["windows"]
        if not windows:
            rows[ticker] = {"status": "UNAVAILABLE", "reason": "NO_WINDOWS"}
            continue
        rows[ticker] = {
            "status": "EXPLORATORY_ONLY",
            "data_provenance": {
                "ticker": asset["data_audit"]["ticker"],
                "first_date": asset["data_audit"]["first_date"],
                "last_date": asset["data_audit"]["last_date"],
                "observation_count": asset["data_audit"]["observation_count"],
                "total_return_validated": asset["data_audit"]["valid_for_total_return_comparison"],
            } if "data_audit" in asset else None,
            "windows": len(windows),
            "mean_baseline_return_fraction": round(
                sum(w["baseline_return_fraction"] for w in windows) / len(windows), 6),
            "mean_adaptive_return_fraction": round(
                sum(w["regime_return_fraction"] for w in windows) / len(windows), 6),
            "mean_hold_return_fraction": round(
                sum(w["benchmark_return_fraction"] for w in windows) / len(windows), 6),
            "adaptive_wins_vs_hold": sum(
                w["regime_return_fraction"] > w["benchmark_return_fraction"]
                for w in windows),
            "adaptive_worst_window_return_fraction": min(
                w["regime_return_fraction"] for w in windows),
            "adaptive_worst_window_drawdown_fraction": (
                max(w["regime_max_drawdown_fraction"] for w in windows)
                if all("regime_max_drawdown_fraction" in w for w in windows)
                else None),
        }
    return {
        "mode": "EXPLORATORY_HISTORICAL_REPORT_NO_ORDERS",
        "assets": rows,
        "research_only": True,
        "live_trading_approved": False,
        "warning": (
            "Window means are descriptive, not compounded portfolio returns. "
            "Prices are unadjusted and omit dividends. Past results do not "
            "establish future profitability or live-trading readiness."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summarize_research(run_historical_research()), indent=2))
