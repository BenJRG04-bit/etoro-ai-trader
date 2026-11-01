"""Unit tests for the fail-closed eToro demo order preflight."""
import unittest

from demo_trade_guard import assess_demo_buy


def safe_proposal(**overrides):
    values = {
        "account": "demo",
        "symbol": "SPY",
        "amount_usd": 25.0,
        "leverage": 1,
        "market_open": True,
        "quote_age_seconds": 2.0,
        "available_cash_usd": 1000.0,
        "current_equity_usd": 100000.0,
        "peak_equity_usd": 100000.0,
        "total_active_exposure_usd": 0.0,
        "active_symbols": [],
    }
    values.update(overrides)
    return assess_demo_buy(**values)


class DemoTradeGuardTests(unittest.TestCase):
    def test_small_eligible_proposal_is_still_not_an_order(self):
        result = safe_proposal()
        self.assertTrue(result["approved_for_proposal"])
        self.assertFalse(result["order_submitted"])
        self.assertTrue(result["needs_explicit_trade_confirmation"])

    def test_blocks_real_account(self):
        self.assertIn("DEMO_ONLY", safe_proposal(account="real")["reasons"])

    def test_blocks_leverage(self):
        self.assertIn("LEVERAGE_NOT_ALLOWED", safe_proposal(leverage=5)["reasons"])

    def test_blocks_pending_duplicate(self):
        self.assertIn("DUPLICATE_POSITION_OR_ORDER",
                      safe_proposal(active_symbols=["SPY"])["reasons"])

    def test_blocks_large_position(self):
        self.assertIn("POSITION_SIZE_LIMIT",
                      safe_proposal(amount_usd=51)["reasons"])

    def test_blocks_combined_exposure(self):
        self.assertIn("TOTAL_EXPOSURE_LIMIT",
                      safe_proposal(total_active_exposure_usd=80)["reasons"])

    def test_blocks_closed_market(self):
        self.assertIn("MARKET_NOT_VERIFIED_OPEN",
                      safe_proposal(market_open=False)["reasons"])

    def test_blocks_stale_quote(self):
        self.assertIn("STALE_OR_UNKNOWN_QUOTE",
                      safe_proposal(quote_age_seconds=3600)["reasons"])

    def test_blocks_invalid_or_missing_account_data(self):
        self.assertIn("INVALID_ACCOUNT_OR_ORDER_DATA",
                      safe_proposal(available_cash_usd=float("nan"))["reasons"])

    def test_blocks_drawdown(self):
        self.assertIn("DRAWDOWN_HALT",
                      safe_proposal(current_equity_usd=890, peak_equity_usd=1000)["reasons"])

    def test_blocks_insufficient_cash(self):
        self.assertIn("INSUFFICIENT_DEMO_CASH",
                      safe_proposal(available_cash_usd=10)["reasons"])

    def test_blocks_unverified_orders(self):
        self.assertIn("UNVERIFIED_OPEN_ORDERS",
                      safe_proposal(active_symbols=None)["reasons"])

    def test_blocks_unknown_asset(self):
        self.assertIn("SYMBOL_NOT_APPROVED",
                      safe_proposal(symbol="UNKNOWN")["reasons"])


if __name__ == "__main__":
    unittest.main()
