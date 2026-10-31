import unittest
from six_brains import council, NAMES

class CouncilTests(unittest.TestCase):
    def test_six_perspectives(self):
        result = council([100 + i for i in range(80)])
        self.assertEqual(result["status"], "OK")
        self.assertEqual(set(result["scores"]), set(NAMES))
        self.assertTrue(result["research_only"])
    def test_insufficient_history(self):
        self.assertEqual(council([100] * 10)["decision"], "NO_ASSESSMENT")
    def test_invalid_prices(self):
        self.assertEqual(council([100] * 59 + [0])["status"], "INSUFFICIENT_DATA")
    def test_flat_market(self):
        self.assertEqual(council([100] * 80)["decision"], "MIXED_RESEARCH")

if __name__ == "__main__":
    unittest.main()
