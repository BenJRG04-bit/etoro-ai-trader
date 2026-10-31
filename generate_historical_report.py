"""Generate an exploratory historical scorecard artifact; no brokerage access."""
import json
from datetime import datetime, timezone
from pathlib import Path
from historical_research_pipeline import run_historical_research
from historical_research_report import summarize_research


def main():
    research = run_historical_research()
    summary = summarize_research(research)
    summary["generated_utc"] = datetime.now(timezone.utc).isoformat()
    summary["data_period_requested"] = "2y"
    summary["price_source"] = "Yahoo Finance public daily chart endpoint"
    summary["assets_unavailable"] = [
        ticker for ticker, row in summary["assets"].items()
        if row["status"] != "EXPLORATORY_ONLY"
    ]
    Path("historical_research_report.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "mode": summary["mode"],
        "asset_count": len(summary["assets"]),
        "unavailable": summary["assets_unavailable"],
        "output": "historical_research_report.json",
        "live_trading_approved": False,
    }, indent=2))
    return 0 if not summary["assets_unavailable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
