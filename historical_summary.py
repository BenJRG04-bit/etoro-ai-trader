"""Summarize research reports conservatively; never infer profitability from failures."""
import json
from pathlib import Path

def summarize(report):
    assets = report.get("assets", {})
    rows = []
    for ticker, asset in sorted(assets.items()):
        if asset.get("status") != "OK":
            rows.append({"ticker": ticker, "status": "UNAVAILABLE", "reason": asset.get("reason", "unknown")})
            continue
        windows = asset["evaluation"]["windows"]
        if not windows:
            rows.append({"ticker": ticker, "status": "NO_TEST_WINDOWS"})
            continue
        better = sum(w["regime_return_fraction"] > w["baseline_return_fraction"] for w in windows)
        worse = sum(w["regime_return_fraction"] < w["baseline_return_fraction"] for w in windows)
        rows.append({
            "ticker": ticker, "status": "EVALUATED", "windows": len(windows),
            "regime_better_windows": better, "regime_worse_windows": worse,
            "regime_equal_windows": len(windows) - better - worse,
            "mean_baseline_return_fraction": round(sum(w["baseline_return_fraction"] for w in windows) / len(windows), 6),
            "mean_regime_return_fraction": round(sum(w["regime_return_fraction"] for w in windows) / len(windows), 6),
            "mean_benchmark_return_fraction": round(sum(w["benchmark_return_fraction"] for w in windows) / len(windows), 6),
            "worst_regime_window_drawdown_fraction": max(w["regime_max_drawdown_fraction"] for w in windows),
        })
    return {
        "mode": "RESEARCH_SUMMARY_NO_ORDERS",
        "source_generated_at_utc": report.get("generated_at_utc"),
        "assets": rows, "research_only": True,
        "interpretation": ("Window averages are not compounded portfolio returns. "
                           "These historical results are not independent out-of-sample proof. "
                           "Do not treat as trading advice or evidence of future profits.")
    }

if __name__ == "__main__":
    report = json.loads(Path("historical_evaluation_report.json").read_text(encoding="utf-8"))
    print(json.dumps(summarize(report), indent=2))
