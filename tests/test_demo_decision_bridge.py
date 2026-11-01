"""Offline test cases for read-only eToro demo research review bridge."""
import unittest
from copy import deepcopy
from demo_decision_bridge import build_demo_review

def fixtures():
    research = {
        "status": "RESEARCH_CYCLE_COMPLETE", "research_only": True,
        "orders_allowed": False, "live_trading_approved": False,
        "as_of_date": "2026-10-30",
        "intelligence": {
            "status": "RESEARCH_ONLY", "research_only": True,
            "orders_allowed": False,
            "decisions": {"SPY": {"label": "ELIGIBLE_FOR_SIMULATION"}},
            "hypothetical_target_allocations": {"SPY": 0.05},
        },
    }
    portfolio = {
        "statusCode": 200, "account": "demo", "accountCurrency": "USD",
        "timestamp": "2026-11-01T17:29:59",
        "totals": {"totalValue": 100000.0, "availableCash": 100000.0},
        "holdings": [], "pendingOrders": [], "copiedTraders": [],
    }
    positions = {
        "statusCode": 200, "account": "demo", "accountCurrency": "USD",
        "timestamp": "2026-11-01T17:29:59Z",
        "direct": {"positions": [], "orders": [], "positionCount": 0},
        "mirrors": [],
    }
    markets = {"statusCode": 200, "instruments": [{
        "market": {"symbol": "SPY"},
        "quote": {"ask": 755.29, "asOf": "2026-11-01T17:29:59Z"},
        "eligibility": {"allowOpenPosition": True,
                        "allowedLeveragesLong": [1, 2, 5],
                        "minPositionExposure": 10.0},
    }]}
    return [research, portfolio, positions, markets]

def review(rows=None, **overrides):
    defaults = {"now_utc": "2026-11-01T17:30:00Z",
                "market_open_verified": True, "peak_equity_usd": 100000.0}
    defaults.update(overrides)
    return build_demo_review(*(deepcopy(rows) if rows else fixtures()), **defaults)

class DemoBridgeTests(unittest.TestCase):
    def test_safe_proposal_is_never_an_order(self):
        report = review()
        self.assertEqual(report["candidates"][0]["status"], "READY_FOR_USER_REVIEW")
        self.assertEqual(report["candidates"][0]["proposed_amount_usd"], 25)
        self.assertEqual(report["orders_submitted"], 0)
        self.assertFalse(report["orders_allowed"])

    def test_closed_market_is_blocked(self):
        report = review(market_open_verified=False)
        self.assertIn("MARKET_NOT_VERIFIED_OPEN", report["candidates"][0]["reasons"])

    def test_stale_quote_is_blocked(self):
        rows = fixtures()
        rows[3]["instruments"][0]["quote"]["asOf"] = "2026-10-30T19:59:57Z"
        self.assertIn("STALE_OR_UNKNOWN_QUOTE", review(rows)["candidates"][0]["reasons"])

    def test_real_account_is_blocked(self):
        rows = fixtures()
        rows[1]["account"] = "real"
        self.assertIn("DEMO_ONLY", review(rows)["reasons"])

    def test_unknown_historical_peak_is_blocked(self):
        self.assertIn("HISTORICAL_PEAK_REQUIRED",
                      review(peak_equity_usd=None)["reasons"])

    def test_existing_order_is_blocked(self):
        rows = fixtures()
        rows[1]["pendingOrders"] = [{"orderId": 1}]
        rows[2]["direct"]["orders"] = [{"orderId": 1}]
        self.assertIn("PENDING_ORDERS_PRESENT", review(rows)["reasons"])

    def test_exposure_limit_with_existing_holding(self):
        rows = fixtures()
        rows[1]["holdings"] = [{"market": {"symbol": "AAPL"},
                               "positionCount": 1, "exposure": 90}]
        rows[2]["direct"]["positions"] = [{"positionId": 1}]
        rows[2]["direct"]["positionCount"] = 1
        self.assertIn("TOTAL_EXPOSURE_LIMIT", review(rows)["candidates"][0]["reasons"])

    def test_missing_holdings_exposure_fails_closed(self):
        rows = fixtures()
        rows[1]["holdings"] = [{"market": {"symbol": "SPY"}, "positionCount": 1}]
        self.assertIn("UNVERIFIED_HOLDING_EXPOSURE", review(rows)["reasons"])

    def test_partial_broker_read_is_blocked(self):
        rows = fixtures()
        rows[1]["warnings"] = ["incomplete"]
        self.assertIn("PARTIAL_BROKER_READ", review(rows)["reasons"])

    def test_research_cannot_enable_trading(self):
        rows = fixtures()
        rows[0]["orders_allowed"] = True
        self.assertIn("UNVERIFIED_RESEARCH_MODE", review(rows)["reasons"])

    def test_drawdown_blocks(self):
        rows = fixtures()
        rows[1]["totals"]["totalValue"] = 89000
        self.assertIn("DRAWDOWN_HALT", review(rows)["candidates"][0]["reasons"])

    def test_no_positive_research_yields_no_proposals(self):
        rows = fixtures()
        rows[0]["intelligence"]["decisions"]["SPY"]["label"] = "WAIT_RESEARCH"
        self.assertEqual(review(rows)["status"], "NO_RESEARCH_CANDIDATES")

if __name__ == "__main__":
    unittest.main()
