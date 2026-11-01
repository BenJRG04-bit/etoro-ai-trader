"""Chronological accountability trends from immutable read-only daily reports.

Descriptive frequencies are not probabilities, strategy performance or trade advice.
"""
from collections import defaultdict
from datetime import date
from council_report_integrity import validate_council_report
from historical_prices import WATCHLIST

def summarize_council_history(reports, *, max_reports=90):
    if not isinstance(reports, list):
        raise ValueError("Reports must be a list")
    if type(max_reports) is not int or not 1 <= max_reports <= 365:
        raise ValueError("Invalid report limit")
    by_date = {}
    rejected = 0
    for report in reports:
        try:
            validate_council_report(report)
            observed_dates = {row["as_of"] for row in report["assets"].values()
                              if row["status"] == "OBSERVED_RESEARCH"}
            if len(observed_dates) != 1:
                raise ValueError("Missing or misaligned report dates")
            stamp = next(iter(observed_dates))
            date.fromisoformat(stamp)
        except (ValueError, TypeError, KeyError):
            rejected += 1
            continue
        if stamp not in by_date:
            by_date[stamp] = report
        elif by_date[stamp] is None or by_date[stamp] != report:
            by_date[stamp] = None
            rejected += 1
    selected = [(stamp, row) for stamp, row in sorted(by_date.items()) if row is not None][-max_reports:]
    stats = {ticker: {"observations": 0, "original_positive": 0,
                      "confirmed_positive": 0, "risk_veto": 0,
                      "mixed_perspectives": 0, "awaiting_confirmation": 0,
                      "regimes": defaultdict(int)} for ticker in WATCHLIST}
    timeline = []
    for stamp, report in selected:
        item = {"date": stamp, "assets": {}}
        for ticker, row in sorted(report["assets"].items()):
            if row["status"] != "OBSERVED_RESEARCH":
                item["assets"][ticker] = {"status": "UNAVAILABLE"}
                continue
            ex = row["explanation"]
            st = stats[ticker]
            st["observations"] += 1
            st["original_positive"] += int(ex["original_decision"] == "POSITIVE_RESEARCH")
            st["confirmed_positive"] += int(ex["confirmed_decision"] == "POSITIVE_RESEARCH")
            st["risk_veto"] += int(ex["risk_veto"])
            st["mixed_perspectives"] += int(ex["agreement"]["mixed_signs"])
            st["awaiting_confirmation"] += int(ex["confirmed_decision"] == "WAIT_FOR_CONFIRMATION")
            regime = ex.get("market_regime") or "UNKNOWN"
            st["regimes"][regime] += 1
            item["assets"][ticker] = {
                "status": "OBSERVED_RESEARCH", "original": ex["original_decision"],
                "confirmed": ex["confirmed_decision"], "risk_veto": ex["risk_veto"],
                "mixed_perspectives": ex["agreement"]["mixed_signs"]}
        timeline.append(item)
    for item in stats.values():
        item["regimes"] = dict(sorted(item["regimes"].items()))
    return {"status": "RESEARCH_ACCOUNTABILITY_HISTORY",
            "selected_report_dates": len(selected), "rejected_reports": rejected,
            "first_date": selected[0][0] if selected else None,
            "last_date": selected[-1][0] if selected else None,
            "assets": stats, "timeline": timeline,
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "limitations": "Counts archived decision labels only. Not observed market outcomes, predictive accuracy, portfolio P&L or evidence of trading skill."}
