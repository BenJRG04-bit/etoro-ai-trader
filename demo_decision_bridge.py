"""Offline bridge: Project E.T. research -> eToro DEMO trade-review candidates.

Receives data snapshots provided by a caller; never authenticates to a broker,
uses secrets, issues network requests, or submits orders. It fails closed when
market/account/research evidence is missing, inconsistent, or stale.
"""
from datetime import datetime, timezone
from math import isfinite

from demo_trade_guard import DemoTradeLimits, assess_demo_buy


def _number(value):
    return type(value) in (int, float) and isfinite(value) and value >= 0


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("Missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    # eToro's portfolio summary currently returns an ISO UTC timestamp
    # without a suffix, whereas its orders endpoint includes Z.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age(now, stamp):
    age = (now - _utc(stamp)).total_seconds()
    if age < 0 or age > 120:
        raise ValueError("Stale or future broker snapshot")


def _blocked(reason):
    return {"status": "BLOCKED", "reasons": [reason], "candidates": [],
            "research_only": True, "orders_allowed": False,
            "orders_submitted": 0, "needs_user_confirmation": True}


def build_demo_review(
    research_cycle,
    portfolio,
    positions,
    markets,
    *,
    now_utc,
    market_open_verified=False,
    peak_equity_usd=None,
    limits=DemoTradeLimits(),
):
    """Create review-only suggestions from independent research and DEMO reads.

    A caller must provide a genuine COMPLETE, unfiltered demo portfolio and
    positions snapshot, current market quotes, independently verified market
    open status, and a maintained historical peak-equity figure.
    The bridge deliberately has NO way to call the eToro trading API.
    """
    try:
        now = _utc(now_utc) if isinstance(now_utc, str) else now_utc
        if not isinstance(now, datetime) or now.tzinfo is None:
            return _blocked("INVALID_NOW")
        now = now.astimezone(timezone.utc)
        for row in (research_cycle, portfolio, positions, markets):
            if not isinstance(row, dict):
                return _blocked("MISSING_INPUT")
        if research_cycle.get("status") != "RESEARCH_CYCLE_COMPLETE" or (
            research_cycle.get("research_only") is not True
            or research_cycle.get("orders_allowed") is not False
            or research_cycle.get("live_trading_approved") is not False
        ):
            return _blocked("UNVERIFIED_RESEARCH_MODE")
        decision = research_cycle.get("intelligence")
        if not isinstance(decision, dict) or (
            decision.get("status") != "RESEARCH_ONLY"
            or decision.get("research_only") is not True
            or decision.get("orders_allowed") is not False
        ):
            return _blocked("INVALID_RESEARCH_DECISION")
        research_day = datetime.fromisoformat(research_cycle["as_of_date"]).date()
        if not 0 <= (now.date() - research_day).days <= 4:
            return _blocked("STALE_RESEARCH")
        if portfolio.get("account") != "demo" or positions.get("account") != "demo":
            return _blocked("DEMO_ONLY")
        if portfolio.get("statusCode") != 200 or positions.get("statusCode") != 200:
            return _blocked("BROKER_READ_FAILED")
        if markets.get("statusCode") != 200:
            return _blocked("MARKET_READ_FAILED")
        if portfolio.get("accountCurrency") != "USD" or positions.get("accountCurrency") != "USD":
            return _blocked("UNSUPPORTED_CURRENCY")
        if portfolio.get("warnings") or positions.get("warnings") or markets.get("warnings"):
            return _blocked("PARTIAL_BROKER_READ")
        _age(now, portfolio.get("timestamp"))
        _age(now, positions.get("timestamp"))
        if positions.get("filter"):
            return _blocked("FILTERED_POSITIONS")
        direct = positions.get("direct")
        if not isinstance(direct, dict) or not isinstance(positions.get("mirrors"), list):
            return _blocked("INCOMPLETE_POSITION_READ")
        if positions["mirrors"]:
            return _blocked("COPIED_POSITIONS_REQUIRE_REVIEW")
        open_positions, open_orders = direct.get("positions"), direct.get("orders")
        if not isinstance(open_positions, list) or not isinstance(open_orders, list):
            return _blocked("INCOMPLETE_POSITION_READ")
        if type(direct.get("positionCount")) is not int or direct["positionCount"] != len(open_positions):
            return _blocked("POSITION_COUNT_MISMATCH")
        pending = portfolio.get("pendingOrders")
        if not isinstance(pending, list) or len(pending) != len(open_orders):
            return _blocked("ORDER_COUNT_MISMATCH")
        if pending:
            return _blocked("PENDING_ORDERS_PRESENT")
        copied = portfolio.get("copiedTraders")
        if not isinstance(copied, list) or copied:
            return _blocked("COPIED_TRADERS_REQUIRE_REVIEW")

        totals = portfolio.get("totals")
        if not isinstance(totals, dict):
            return _blocked("MISSING_ACCOUNT_TOTALS")
        equity, cash = totals.get("totalValue"), totals.get("availableCash")
        if not _number(equity) or equity <= 0 or not _number(cash):
            return _blocked("INVALID_ACCOUNT_TOTALS")
        if not _number(peak_equity_usd) or peak_equity_usd <= 0:
            return _blocked("HISTORICAL_PEAK_REQUIRED")
        # Unlike a single snapshot, historical peak must be tracked independently.
        peak = max(peak_equity_usd, equity)
        holdings = portfolio.get("holdings")
        if not isinstance(holdings, list):
            return _blocked("MISSING_HOLDINGS")
        active, exposure, held_count = [], 0.0, 0
        for holding in holdings:
            if not isinstance(holding, dict) or not isinstance(holding.get("market"), dict):
                return _blocked("INVALID_HOLDING")
            count, amount = holding.get("positionCount"), holding.get("exposure")
            if type(count) is not int or count < 0 or not _number(amount):
                return _blocked("UNVERIFIED_HOLDING_EXPOSURE")
            if count:
                ticker = holding["market"].get("symbol")
                if not isinstance(ticker, str) or not ticker:
                    return _blocked("UNKNOWN_HELD_SYMBOL")
                active.append(ticker)
                held_count += count
                exposure += amount
        if held_count != len(open_positions):
            return _blocked("POSITION_COUNT_MISMATCH")

        labels, allocations = decision.get("decisions"), decision.get("hypothetical_target_allocations")
        if not isinstance(labels, dict) or not isinstance(allocations, dict):
            return _blocked("MISSING_RESEARCH_ALLOCATIONS")
        if set(labels) != set(allocations) or not labels:
            return _blocked("MISMATCHED_RESEARCH_ALLOCATIONS")
        if not all(_number(v) and v <= 0.05 for v in allocations.values()):
            return _blocked("INVALID_RESEARCH_ALLOCATIONS")
        if sum(allocations.values()) > 0.050000001:
            return _blocked("OVERALLOCATED_RESEARCH")
        instrument_rows = markets.get("instruments")
        if not isinstance(instrument_rows, list):
            return _blocked("MISSING_MARKET_ROWS")
        by_ticker = {}
        for row in instrument_rows:
            if not isinstance(row, dict) or not isinstance(row.get("market"), dict):
                return _blocked("INVALID_MARKET_ROW")
            ticker = row["market"].get("symbol")
            if not isinstance(ticker, str) or ticker in by_ticker:
                return _blocked("DUPLICATE_OR_UNKNOWN_MARKET")
            by_ticker[ticker] = row
        candidates = []
        for symbol, row in sorted(labels.items()):
            if not isinstance(row, dict) or row.get("label") != "ELIGIBLE_FOR_SIMULATION":
                continue
            allocation = allocations[symbol]
            if allocation <= 0:
                continue
            # A small, separate training-budget cap; never use 5% of $100k demo.
            amount = round(min(25.0, limits.training_budget_usd * allocation), 2)
            market = by_ticker.get(symbol, {})
            quote, eligibility = market.get("quote") or {}, market.get("eligibility") or {}
            reasons = []
            if not isinstance(quote, dict) or not isinstance(eligibility, dict):
                reasons.append("INVALID_MARKET_DETAILS")
                quote, eligibility = {}, {}
            ask = quote.get("ask")
            if not _number(ask) or ask <= 0:
                reasons.append("MISSING_ASK_PRICE")
            if eligibility.get("allowOpenPosition") is not True or (
                1 not in eligibility.get("allowedLeveragesLong", [])
            ):
                reasons.append("BROKER_ELIGIBILITY_NOT_VERIFIED")
            minimum = eligibility.get("minPositionExposure")
            if not _number(minimum) or amount < minimum:
                reasons.append("MINIMUM_POSITION_NOT_MET")
            try:
                quote_age = (now - _utc(quote.get("asOf"))).total_seconds()
            except (ValueError, TypeError):
                quote_age = float("inf")
            gate = assess_demo_buy(
                account="demo", symbol=symbol, amount_usd=amount, leverage=1,
                market_open=market_open_verified, quote_age_seconds=quote_age,
                available_cash_usd=cash, current_equity_usd=equity,
                peak_equity_usd=peak, total_active_exposure_usd=exposure,
                active_symbols=active, limits=limits,
            )
            reasons.extend(gate["reasons"])
            candidates.append({
                "symbol": symbol,
                "proposed_amount_usd": amount,
                "status": "READY_FOR_USER_REVIEW" if not reasons else "BLOCKED",
                "reasons": sorted(set(reasons)),
                "order_submitted": False,
                "requires_user_confirmation": True,
            })
        return {
            "status": "REVIEW_AVAILABLE" if candidates else "NO_RESEARCH_CANDIDATES",
            "candidates": candidates,
            "research_only": True,
            "orders_allowed": False,
            "orders_submitted": 0,
            "needs_user_confirmation": True,
            "limitations": (
                "No execution, live market-status verification, or autonomous learning. "
                "Market eligibility may differ on the demo account; eToro must recheck "
                "quotes, costs, settlement type and eligibility before an approved trade."
            ),
        }
    except (TypeError, ValueError, KeyError, OverflowError):
        return _blocked("INVALID_OR_MISSING_SNAPSHOT_DATA")
