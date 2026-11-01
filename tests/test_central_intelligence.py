import unittest
from central_intelligence import central_research_decision


def prices():
    return {"AAA": [100.0] * 65, "BBB": [101.0] * 65}


class CentralIntelligenceTests(unittest.TestCase):
    def test_positive_split_under_total_cap(self):
        r = central_research_decision(prices(), assessment_fn=lambda _: {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False})
        self.assertEqual(r["total_hypothetical_allocation"], .05)
        self.assertEqual(r["hypothetical_target_allocations"]["AAA"], .025)
        self.assertFalse(r["orders_allowed"])

    def test_risk_veto_blocks(self):
        r = central_research_decision(prices(), assessment_fn=lambda _: {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": True})
        self.assertEqual(r["total_hypothetical_allocation"], 0)
        self.assertEqual(r["decisions"]["AAA"]["reason"], "MARKET_RISK_VETO")

    def test_unknown_council_does_not_allocate(self):
        r = central_research_decision(prices(), assessment_fn=lambda _: {"status": "UNAVAILABLE"})
        self.assertEqual(r["total_hypothetical_allocation"], 0)

    def test_bad_prices_rejected(self):
        p = prices()
        p["AAA"][0] = float("nan")
        with self.assertRaises(ValueError):
            central_research_decision(p)

    def test_cap_above_five_percent_rejected(self):
        with self.assertRaises(ValueError):
            central_research_decision(prices(), max_total_allocation=.1)


if __name__ == "__main__":
    unittest.main()
