"""Fail-closed evidence audit of Project E.T.'s historical paper experiments.

This evaluates an existing research JSON report, NOT a broker account.
It never uses credentials, network requests, or places orders.
Historical outperformance is NEVER permission to trade.
"""
import json
import math
import sys
from pathlib import Path

WATCHLIST = ("AAPL", "MSFT", "NVDA", "SPY", "VTI")


def _safe_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def audit_historical_paper_edge(document):
    safe = {"research_only": True, "orders_allowed": False,
            "live_trading_approved": False, "demo_trading_approved": False,
            "source": "HISTORICAL_PAPER_ONLY"}

    def blocked(reason):
        return {**safe, "status": "INSUFFICIENT_EVIDENCE",
                "blockers": [reason], "asset_results": {},
                "outperformed_count": 0, "evaluated_count": 0}

    if not isinstance(document, dict) or (
        document.get("mode") != "HISTORICAL_PAPER_REPORT_NO_ORDERS"
        or document.get("research_only") is not True
        or document.get("orders_allowed") is not False
        or document.get("live_trading_approved") is not False
    ):
        return blocked("INVALID_OR_UNSAFE_SOURCE_REPORT")

    rows = document.get("assets")
    if not isinstance(rows, dict) or set(rows) != set(WATCHLIST):
        return blocked("WATCHLIST_INCOMPLETE_OR_UNEXPECTED")

    starting_cash = document.get("starting_cash_gbp_per_asset")
    if not _safe_number(starting_cash) or starting_cash <= 0:
        return blocked("INVALID_STARTING_CASH")

    asset_results, blockers = {}, []
    for ticker in WATCHLIST:
        row = rows[ticker]
        if not isinstance(row, dict) or row.get("status") != "EXPLORATORY_ONLY":
            blockers.append(ticker + "_NOT_EVALUATED")
            continue
        report = row.get("report")
        if not isinstance(report, dict) or (
            report.get("mode") != "OFFLINE_PAPER_PERFORMANCE_NO_ORDERS"
            or report.get("research_only") is not True
            or report.get("live_trading_approved") is not False
            or report.get("ticker") != ticker
        ):
            blockers.append(ticker + "_INVALID_REPORT")
            continue
        strategy = report.get("strategy_end")
        benchmark = report.get("benchmark_end")
        delta = report.get("strategy_minus_benchmark_gbp")
        report_start = report.get("starting_cash")
        if not all(_safe_number(x) for x in (strategy, benchmark, delta, report_start)):
            blockers.append(ticker + "_INVALID_METRICS")
            continue
        if strategy < 0 or benchmark < 0 or abs(report_start - starting_cash) > 0.000001:
            blockers.append(ticker + "_INCONSISTENT_CAPITAL")
            continue
        if abs((strategy - benchmark) - delta) > 0.02:
            blockers.append(ticker + "_INCONSISTENT_COMPARISON")
            continue
        asset_results[ticker] = {
            "strategy_end_gbp": round(strategy, 2),
            "benchmark_end_gbp": round(benchmark, 2),
            "strategy_minus_benchmark_gbp": round(delta, 2),
            "outperformed": delta > 0,
        }

    if blockers:
        return {**safe, "status": "INSUFFICIENT_EVIDENCE",
                "blockers": sorted(blockers), "asset_results": asset_results,
                "outperformed_count": sum(row["outperformed"] for row in asset_results.values()),
                "evaluated_count": len(asset_results),
                "limitations": "Missing or inconsistent historical data blocks a complete comparison."}

    outperformed_count = sum(row["outperformed"] for row in asset_results.values())
    return {
        **safe,
        "status": ("HISTORICAL_OUTPERFORMANCE_OBSERVED" if outperformed_count == len(WATCHLIST)
                   else "NO_CONSISTENT_HISTORICAL_EDGE"),
        "asset_results": asset_results,
        "outperformed_count": outperformed_count,
        "evaluated_count": len(WATCHLIST),
        "underperformed_or_equal_count": len(WATCHLIST) - outperformed_count,
        "blockers": [
            "NO_VERIFIED_FORWARD_BROKER_TRACK_RECORD",
            "HISTORICAL_BACKTEST_NOT_INDEPENDENT_PROOF",
            "TRADING_APPROVAL_NOT_GRANTED",
        ],
        "limitations": (
            "Five independent £100 historical comparisons, not one portfolio. "
            "No demonstrated future predictive edge. Source lacks full spread, "
            "slippage, dividends, FX and tax. Capped passive benchmark is not "
            "an unrestricted buy-and-hold comparison. No demo or real orders."
        ),
    }


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("Usage: python paper_edge_audit.py <historical_paper_report.json>", file=sys.stderr)
        return 2
    try:
        with Path(arguments[0]).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        result = audit_historical_paper_edge(payload)
    except (OSError, ValueError, TypeError, UnicodeError):
        result = audit_historical_paper_edge(None)
    print(json.dumps(result, indent=2, sort_keys=True))
    # Evidence gaps are represented in the report rather than hidden.
    return 0


if __name__ == "__main__":
    sys.exit(main())
