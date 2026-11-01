"""Regression tests for price-only pattern recognition and lagged simulations."""
import unittest
from datetime import date, datetime, timedelta, timezone
from math import inf, nan
from unittest.mock import patch

from pattern_recognition import analyze_price_patterns
from pattern_strategy_evaluation import (
    _simulate_period, evaluate_pattern_strategies, POLICIES,
)
from run_pattern_research import run_pattern_research


def synthetic_trend(n=280):
    # Modest upward drift with alternating down/up returns to avoid RSI=100.
    return [100 + 0.15 * i + (0.5 if i % 2 else -0.5) for i in range(n)]


class PatternRecognitionTests(unittest.TestCase):
    def test_fixed_breakout_pattern_is_descriptive_not_an_order(self):
        report = analyze_price_patterns(synthetic_trend())
        self.assertEqual(report["signal"], "RESEARCH_CANDIDATE")
        self.assertIn("BREAKOUT_ABOVE_PRIOR_20D_HIGH", report["pattern_labels"])
        self.assertTrue(report["research_only"])
        self.assertFalse(report["orders_allowed"])
        self.assertFalse(report["demo_trading_approved"])
        self.assertFalse(report["live_trading_approved"])
        self.assertFalse(report.get("probability", False))

    def test_crash_does_not_trigger_buy(self):
        prices = synthetic_trend()
        prices[-1] *= 0.8
        report = analyze_price_patterns(prices)
        self.assertEqual(report["signal"], "RISK_BLOCKED")
        self.assertIn("SHARP_LAST_DAY_DECLINE", report["risk_vetoes"])

    def test_flat_prices_do_not_force_a_trade(self):
        report = analyze_price_patterns([100.0] * 280)
        self.assertNotEqual(report["signal"], "RESEARCH_CANDIDATE")

    def test_insufficient_history_fails_closed(self):
        report = analyze_price_patterns([100.0] * 119)
        self.assertEqual(report["signal"], "NO_CANDIDATE")
        self.assertEqual(report["status"], "INSUFFICIENT_HISTORY")

    def test_rejects_nonfinite_boolean_or_zero_prices(self):
        for bad in (0, nan, inf, True, -1):
            prices = synthetic_trend()
            prices[10] = bad
            with self.assertRaises(ValueError):
                analyze_price_patterns(prices)

    def test_does_not_observe_future_prices(self):
        prices = synthetic_trend()
        baseline = analyze_price_patterns(prices[:210])
        prices[210:] = [1.0] * (len(prices) - 210)
        comparison = analyze_price_patterns(prices[:210])
        self.assertEqual(baseline, comparison)


class PatternEvaluationTests(unittest.TestCase):
    def test_equal_periods_for_all_four_policies(self):
        report = evaluate_pattern_strategies(synthetic_trend())
        self.assertEqual(set(report["policies"]), set(POLICIES))
        self.assertEqual(set(report["segments"]), {"earlier", "later_holdout"})
        for segment in report["segments"].values():
            self.assertTrue(segment["signal_information_last_index_is_t_minus_one"])
            self.assertEqual(set(segment["scenarios"]), {"0.001", "0.005"})
            for scenario in segment["scenarios"].values():
                self.assertEqual(set(scenario["policies"]), set(POLICIES))
        split = report["split_price_index"]
        self.assertEqual(report["segments"]["earlier"]["scored_return_periods"], split - 120)
        self.assertEqual(report["segments"]["later_holdout"]["scored_return_periods"], 279 - split)
        self.assertFalse(report["strategy_selection_automated"])
        self.assertFalse(report["orders_allowed"])

    def test_all_signals_lagged_by_one_full_close(self):
        prices = synthetic_trend()
        seen = []

        def inspect(history):
            seen.append(tuple(history))
            return {"signal": "RESEARCH_CANDIDATE"}

        with patch("pattern_strategy_evaluation.analyze_price_patterns", side_effect=inspect):
            result = _simulate_period(prices, 150, 151, "pattern_confluence", .001, .001)
        self.assertEqual(seen, [tuple(prices[:150])])
        self.assertEqual(result["invested_return_periods"], 1)

    def test_fee_stress_lower_equity_for_buy_and_hold(self):
        report = evaluate_pattern_strategies(synthetic_trend())
        later = report["segments"]["later_holdout"]["scenarios"]
        self.assertLess(
            later["0.005"]["policies"]["capped_hold"]["end_equity"],
            later["0.001"]["policies"]["capped_hold"]["end_equity"],
        )

    def test_never_autoselect_strategy_even_if_pattern_wins(self):
        report = evaluate_pattern_strategies(synthetic_trend())
        self.assertFalse(report["demo_trading_approved"])
        self.assertFalse(report["live_trading_approved"])
        self.assertFalse(report["strategy_selection_automated"])

    def test_bad_history_and_cost_inputs_rejected(self):
        for invalid in ([100.0] * 249, synthetic_trend()[:-1] + [nan]):
            with self.assertRaises(ValueError):
                evaluate_pattern_strategies(invalid)
        with self.assertRaises(ValueError):
            evaluate_pattern_strategies(synthetic_trend(), slippage_rate=-0.5)
        with self.assertRaises(ValueError):
            evaluate_pattern_strategies(synthetic_trend(), fee_rates=(nan,))


class PatternRunnerTests(unittest.TestCase):
    def setUp(self):
        self.prices = synthetic_trend()
        first = date(2026, 1, 1)
        self.dates = [(first + timedelta(days=i)).isoformat() for i in range(len(self.prices))]
        self.latest = date.fromisoformat(self.dates[-1])

    def fetch(self, ticker, period="2y"):
        return {"ticker": ticker, "dates": self.dates,
                "closes": self.prices, "price_type": "unadjusted_daily_close"}

    def test_fresh_public_data_is_research_only(self):
        now = datetime.combine(self.latest + timedelta(days=1), datetime.min.time(), timezone.utc)
        report = run_pattern_research(fetcher=self.fetch, tickers=("SPY",), now_utc=now)
        self.assertEqual(report["assets"]["SPY"]["status"], "EXPLORATORY_ONLY")
        self.assertEqual(report["assets"]["SPY"]["latest_pattern"]["signal"],
                         "RESEARCH_CANDIDATE")
        self.assertFalse(report["orders_allowed"])

    def test_stale_data_cannot_create_current_candidate(self):
        now = datetime.combine(self.latest + timedelta(days=10), datetime.min.time(), timezone.utc)
        report = run_pattern_research(fetcher=self.fetch, tickers=("SPY",), now_utc=now)
        self.assertEqual(report["assets"]["SPY"]["status"], "STALE_PUBLIC_DATA")
        self.assertEqual(report["assets"]["SPY"]["latest_pattern"]["signal"], "NO_CANDIDATE")

    def test_missing_prices_do_not_invent_signals(self):
        def failing(ticker, period="2y"):
            raise OSError("Missing provider")
        report = run_pattern_research(fetcher=failing, tickers=("SPY",),
                                      now_utc=datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(report["assets"]["SPY"]["status"], "UNAVAILABLE")
        self.assertEqual(report["assets"]["SPY"]["latest_pattern"]["signal"], "NO_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
