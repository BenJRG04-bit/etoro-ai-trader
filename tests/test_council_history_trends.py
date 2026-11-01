import unittest
from copy import deepcopy
from council_history_trends import summarize_council_history
from historical_prices import WATCHLIST
from six_brains import NAMES

class CouncilHistoryTests(unittest.TestCase):
    def setUp(self):
        explanation = {"status": "RESEARCH_EXPLANATION", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False,
            "risk_veto": False, "original_decision": "MIXED_RESEARCH",
            "confirmed_decision": "MIXED_RESEARCH", "market_regime": "SIDEWAYS",
            "perspectives": {name: {"score": 0.0, "stance": "NEUTRAL"} for name in NAMES},
            "agreement": {"positive": 0, "negative": 0, "neutral": 6, "mixed_signs": False}}
        self.report = {"status": "RESEARCH_ACCOUNTABILITY_ONLY",
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            "assets": {ticker: {"status": "OBSERVED_RESEARCH", "as_of": "2026-10-29",
                "close": 100.0, "explanation": deepcopy(explanation)} for ticker in WATCHLIST}}

    def test_empty(self):
        r = summarize_council_history([])
        self.assertEqual(r["selected_report_dates"], 0)
        self.assertFalse(r["orders_allowed"])

    def test_one_report(self):
        r = summarize_council_history([self.report])
        self.assertEqual(r["selected_report_dates"], 1)
        self.assertEqual(r["assets"]["SPY"]["observations"], 1)

    def test_identical_duplicates_not_double_counted(self):
        r = summarize_council_history([self.report, deepcopy(self.report)])
        self.assertEqual(r["selected_report_dates"], 1)

    def test_conflicting_date_excluded(self):
        altered = deepcopy(self.report)
        altered["assets"]["SPY"]["close"] = 101.0
        r = summarize_council_history([self.report, altered])
        self.assertEqual(r["selected_report_dates"], 0)
        self.assertEqual(r["rejected_reports"], 1)

    def test_invalid_report_rejected(self):
        bad = deepcopy(self.report)
        bad["orders_allowed"] = True
        r = summarize_council_history([bad])
        self.assertEqual(r["rejected_reports"], 1)

    def test_misaligned_dates_rejected(self):
        bad = deepcopy(self.report)
        bad["assets"]["SPY"]["as_of"] = "2026-10-30"
        self.assertEqual(summarize_council_history([bad])["selected_report_dates"], 0)

    def test_chronological_sort(self):
        newer = deepcopy(self.report)
        for row in newer["assets"].values():
            row["as_of"] = "2026-10-30"
        r = summarize_council_history([newer, self.report])
        self.assertEqual([x["date"] for x in r["timeline"]], ["2026-10-29", "2026-10-30"])

    def test_report_limit(self):
        newer = deepcopy(self.report)
        for row in newer["assets"].values():
            row["as_of"] = "2026-10-30"
        self.assertEqual(summarize_council_history([newer, self.report], max_reports=1)["first_date"], "2026-10-30")

    def test_veto_counts(self):
        for row in self.report["assets"].values():
            row["explanation"]["risk_veto"] = True
            row["explanation"]["original_decision"] = "CAUTIOUS_RESEARCH"
            row["explanation"]["confirmed_decision"] = "CAUTIOUS_RESEARCH"
        r = summarize_council_history([self.report])
        self.assertEqual(r["assets"]["SPY"]["risk_veto"], 1)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            summarize_council_history([], max_reports=0)

if __name__ == "__main__":
    unittest.main()
