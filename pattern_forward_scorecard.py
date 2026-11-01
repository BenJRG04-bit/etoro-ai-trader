"""Fail-closed accountability scorecard for *archived* pattern forward outcomes.

Counts all valid frozen signals, including NO_CANDIDATE and RISK_BLOCKED.
Never automatically optimizes thresholds or approves a broker trade.
Observations are clustered by signal date; five same-date assets are correlated,
not five independent statistical trials.
"""
from datetime import date, datetime, timezone
from math import isfinite
from statistics import mean, median

from historical_prices import WATCHLIST
from run_pattern_forward_snapshot import VERSION

SAFE = {
    "research_only": True, "orders_allowed": False,
    "demo_trading_approved": False, "live_trading_approved": False,
}
SIGNALS = ("RESEARCH_CANDIDATE", "NO_CANDIDATE", "RISK_BLOCKED")


def _price(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def _date(stamp):
    if not isinstance(stamp, str):
        raise ValueError("Date missing")
    parsed = date.fromisoformat(stamp)
    if parsed.isoformat() != stamp:
        raise ValueError("Noncanonical date")
    return parsed


def _archived(stamp):
    if not isinstance(stamp, str):
        raise ValueError("Archive timestamp missing")
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC archive timestamp required")
    return parsed.astimezone(timezone.utc)


def _validate_observed(record):
    if not isinstance(record, dict) or record.get("status") != "OBSERVED":
        raise ValueError("Expected completed observation")
    for key, expected in SAFE.items():
        if record.get(key) is not expected:
            raise ValueError("Unsafe forward report")
    if record.get("strategy_version") != VERSION:
        raise ValueError("Mixed or modified strategy version")
    signal_day = _date(record.get("signal_close_date"))
    created = _archived(record.get("archived_at_utc"))
    if not 0 <= (created.date() - signal_day).days <= 4:
        raise ValueError("Invalid signal archive chronology")
    fee, slip = record.get("comparison_fee_rate"), record.get("comparison_slippage_rate")
    if (type(fee) not in (int, float) or not isfinite(fee) or not 0 <= fee < .1
        or type(slip) not in (int, float) or not isfinite(slip) or not 0 <= slip < .05):
        raise ValueError("Invalid recorded costs")
    rows = record.get("observations")
    if not isinstance(rows, dict) or set(rows) != set(WATCHLIST):
        raise ValueError("Incomplete forward observation universe")
    if record.get("observed_count") != len(WATCHLIST) or record.get("pending_count") != 0:
        raise ValueError("Partial observations incorrectly marked complete")
    candidate_count = 0
    entries, exits = set(), set()
    for ticker, row in rows.items():
        if not isinstance(row, dict) or row.get("status") != "OBSERVED":
            raise ValueError("Partial observation " + ticker)
        if row.get("archived_signal") not in SIGNALS:
            raise ValueError("Invalid archived signal " + ticker)
        entry, exit_ = _date(row.get("entry_close_date")), _date(row.get("exit_close_date"))
        if not (signal_day < entry < exit_ and created.date() < entry):
            raise ValueError("Outcome used prices before archive: " + ticker)
        entries.add(entry)
        exits.add(exit_)
        ret = row.get("raw_price_return")
        strat, hold, delta = (row.get("hypothetical_signal_equity"),
                              row.get("hypothetical_matched_hold_equity"),
                              row.get("signal_minus_matched_hold"))
        if (type(ret) not in (int, float) or not isfinite(ret) or ret < -1
            or not all(_price(x) for x in (strat, hold))
            or type(delta) not in (int, float) or not isfinite(delta)):
            raise ValueError("Invalid return metrics " + ticker)
        candidate = row["archived_signal"] == "RESEARCH_CANDIDATE"
        candidate_count += int(candidate)
        cost = .05 * (fee + slip)
        expected_hold = 100 * (1 - cost) ** 2 * (1 + .05 * ret)
        expected_strat = expected_hold if candidate else 100.0
        if (abs(strat - expected_strat) > 0.00002 or
            abs(hold - expected_hold) > 0.00002 or
            abs(delta - (strat - hold)) > 0.00002):
            raise ValueError("Inconsistent hypothetical return " + ticker)
        if (type(row.get("signal_beat_matched_hold")) is not bool or
            row["signal_beat_matched_hold"] != (strat > hold)):
            raise ValueError("False relative performance flag " + ticker)
    if len(entries) != 1 or len(exits) != 1:
        raise ValueError("Incompatible market observation windows")
    if (type(record.get("research_candidates_observed")) is not int or
        record["research_candidates_observed"] != candidate_count):
        raise ValueError("Inconsistent candidate count")
    return signal_day, rows


def summarize_pattern_forward_outcomes(documents, *, minimum_dates=20,
                                      minimum_candidates=10):
    if type(minimum_dates) is not int or minimum_dates < 10:
        raise ValueError("At least ten unique signal dates required")
    if type(minimum_candidates) is not int or minimum_candidates < 5:
        raise ValueError("At least five candidate observations required")
    if not isinstance(documents, (tuple, list)):
        raise ValueError("Archive documents must be an explicit list")
    seen, pending, duplicates = {}, 0, 0
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError("Malformed archived evaluation")
        for key, expected in SAFE.items():
            if doc.get(key) is not expected:
                raise ValueError("Unsafe archived result")
        if doc.get("status") == "PENDING":
            pending += 1
            continue
        if doc.get("status") != "OBSERVED":
            raise ValueError("Invalid or unavailable archive cannot be silently skipped")
        day, rows = _validate_observed(doc)
        if day in seen:
            # Permits repeated identical frozen outcomes, NEVER contradictory
            # post-hoc reports on the same archived day.
            if rows != seen[day]:
                raise ValueError("Conflicting historical outcome for the same date")
            duplicates += 1
            continue
        seen[day] = rows

    ordered = sorted(seen)
    candidates = positive_net = negative_net = 0
    avoided_bad = missed_good = avoided_neutral = 0
    per_date_mean_delta = []
    per_asset = {
        ticker: {"candidate_days": 0, "noncandidate_days": 0,
                 "candidate_positive_net": 0, "mean_excess_per_day": None}
        for ticker in WATCHLIST
    }
    asset_deltas = {ticker: [] for ticker in WATCHLIST}
    for day in ordered:
        changes = []
        for ticker in WATCHLIST:
            item = seen[day][ticker]
            delta = item["signal_minus_matched_hold"]
            asset_deltas[ticker].append(delta)
            changes.append(delta)
            if item["archived_signal"] == "RESEARCH_CANDIDATE":
                candidates += 1
                per_asset[ticker]["candidate_days"] += 1
                if item["hypothetical_signal_equity"] > 100:
                    positive_net += 1
                    per_asset[ticker]["candidate_positive_net"] += 1
                else:
                    negative_net += 1
            else:
                per_asset[ticker]["noncandidate_days"] += 1
                if item["hypothetical_matched_hold_equity"] < 100:
                    avoided_bad += 1
                elif item["hypothetical_matched_hold_equity"] > 100:
                    missed_good += 1
                else:
                    avoided_neutral += 1
        per_date_mean_delta.append(mean(changes))
    for ticker in WATCHLIST:
        per_asset[ticker]["mean_excess_per_day"] = (
            round(mean(asset_deltas[ticker]), 6) if asset_deltas[ticker] else None
        )

    reasons = []
    if len(ordered) < minimum_dates:
        reasons.append("TOO_FEW_UNIQUE_FORWARD_DATES")
    if candidates < minimum_candidates:
        reasons.append("TOO_FEW_PRECOMMITTED_RESEARCH_CANDIDATES")
    if not reasons:
        reasons.extend(("NO_INDEPENDENT_BROKER_EXECUTION_RECORD",
                        "NO_AUTOMATED_TRADING_APPROVAL"))
    return {
        **SAFE,
        "status": ("MORE_FORWARD_EVIDENCE_REQUIRED" if len(ordered) < minimum_dates
                   or candidates < minimum_candidates
                   else "SAMPLE_AVAILABLE_FOR_MANUAL_REVIEW_ONLY"),
        "strategy_version": VERSION,
        "unique_signal_dates": len(ordered),
        "first_signal_date": ordered[0].isoformat() if ordered else None,
        "last_signal_date": ordered[-1].isoformat() if ordered else None,
        "observed_asset_days": len(ordered) * len(WATCHLIST),
        "candidate_asset_days": candidates,
        "candidate_net_positive_days": positive_net,
        "candidate_net_nonpositive_days": negative_net,
        "noncandidate_avoided_net_loss": avoided_bad,
        "noncandidate_missed_net_gain": missed_good,
        "noncandidate_neutral": avoided_neutral,
        "mean_excess_vs_capped_hold_per_asset_day": (
            round(mean(per_date_mean_delta), 6) if per_date_mean_delta else None),
        "median_daily_cross_asset_excess_vs_hold": (
            round(median(per_date_mean_delta), 6) if per_date_mean_delta else None),
        "per_asset": per_asset,
        "pending_archive_reports": pending,
        "identical_duplicate_reports_ignored": duplicates,
        "minimum_dates": minimum_dates,
        "minimum_candidate_asset_days": minimum_candidates,
        "blockers": reasons,
        "limitations": (
            "Each asset-day is an independent *hypothetical* £100 capped comparison, "
            "not actual portfolio P&L. Five assets on the same date are correlated. "
            "Candidate positions and matched holding are identical exposure when "
            "active, so relative edge comes from the cash/skip decision; positive "
            "candidate direction alone is NOT excess return versus passive. "
            "Historical unadjusted daily closes omit split/dividend, FX and "
            "real broker fills. 90-day GitHub archive retention limits history. "
            "Never infer a statistically proven strategy or auto-enable orders."
        ),
    }
