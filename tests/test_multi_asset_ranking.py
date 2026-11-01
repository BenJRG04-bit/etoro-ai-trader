import unittest
from multi_asset_ranking import rank_candidates


def candidate(**changes):
    row = {"symbol": "SPY", "asset_class": "etf", "holdout_samples": 150,
           "excess_return": .04, "max_drawdown": .04,
           "estimated_round_trip_cost_fraction": .002,
           "validated": True, "data_fresh": True}
    row.update(changes)
    return row


class CrossAssetRankingTests(unittest.TestCase):
    def test_ranks_only_valid_research(self):
        report = rank_candidates([candidate(), candidate(symbol="BTC", asset_class="crypto", excess_return=.08)])
        self.assertEqual([r["symbol"] for r in report["ranked"]], ["BTC", "SPY"])
        self.assertFalse(report["orders_allowed"])

    def test_missing_validation_and_short_holdout(self):
        report = rank_candidates([candidate(validated=False, holdout_samples=12)])
        self.assertEqual(report["ranked"], [])
        self.assertIn("insufficient_holdout", report["excluded"][0]["reasons"])

    def test_risk_and_cost_gates(self):
        for changes in ({"max_drawdown": .25}, {"estimated_round_trip_cost_fraction": .02},
                        {"excess_return": -.01}, {"excess_return": .001}):
            self.assertFalse(rank_candidates([candidate(**changes)])["ranked"])

    def test_nan_infinity_boolean_and_duplicate(self):
        self.assertFalse(rank_candidates([candidate(excess_return=float("nan"))])["ranked"])
        self.assertFalse(rank_candidates([candidate(max_drawdown=float("inf"))])["ranked"])
        self.assertFalse(rank_candidates([candidate(holdout_samples=True)])["ranked"])
        self.assertEqual(len(rank_candidates([candidate(), candidate()])["excluded"]), 1)


if __name__ == "__main__":
    unittest.main()
