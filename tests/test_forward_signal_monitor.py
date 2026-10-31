import unittest
from forward_signal_monitor import create_signal_snapshot, evaluate_snapshot
from run_forward_snapshot import run_forward_snapshot

def positive(_):
    return {"status": "OK", "decision": "POSITIVE_RESEARCH", "regime_risk_veto": False}

class ForwardSignalTests(unittest.TestCase):
    def setUp(self):
        self.dates = [f"2025-{1 + i // 28:02}-{1 + i % 28:02}" for i in range(70)]
        self.rows = {"AAPL": {"dates": self.dates, "closes": [100. + i for i in range(70)]},
                     "SPY": {"dates": self.dates, "closes": [200. + i for i in range(70)]}}

    def test_freeze_current_decisions(self):
        snap = create_signal_snapshot(self.rows, positive)
        self.assertEqual(snap["snapshot_date"], self.dates[-1])
        self.assertTrue(snap["assets"]["AAPL"]["confirmed_positive"])
        self.assertFalse(snap["orders_allowed"])

    def test_future_is_pending_without_new_close(self):
        snap = create_signal_snapshot(self.rows, positive)
        r = evaluate_snapshot(snap, self.rows)
        self.assertEqual(r["observations"]["AAPL"]["status"], "PENDING_NEW_CLOSE")

    def test_future_observed_only_when_new_close_exists(self):
        snap = create_signal_snapshot(self.rows, positive)
        later = {t: {"dates": row["dates"] + ["2025-04-01"],
                     "closes": row["closes"] + [row["closes"][-1] * 1.01]}
                 for t, row in self.rows.items()}
        r = evaluate_snapshot(snap, later)
        self.assertEqual(r["observations"]["AAPL"]["status"], "OBSERVED")
        self.assertAlmostEqual(r["observations"]["AAPL"]["next_close_return"], 0.01)

    def test_reject_revised_old_price(self):
        snap = create_signal_snapshot(self.rows, positive)
        changed = {t: {"dates": row["dates"], "closes": list(row["closes"])}
                   for t, row in self.rows.items()}
        changed["AAPL"]["closes"][-1] *= 1.1
        with self.assertRaises(ValueError):
            evaluate_snapshot(snap, changed)

    def test_misaligned_dates_fail_closed(self):
        changed = {t: {"dates": list(row["dates"]), "closes": row["closes"]}
                   for t, row in self.rows.items()}
        changed["SPY"]["dates"][-1] = "2025-04-01"
        with self.assertRaises(ValueError):
            create_signal_snapshot(changed, positive)

    def test_runner_rejects_mismatched_ticker(self):
        def fetch(ticker, period="2y"):
            return {"ticker": "WRONG", **self.rows["AAPL"]}
        self.assertEqual(run_forward_snapshot(fetcher=fetch, tickers=("AAPL",))["status"], "UNAVAILABLE")

    def test_no_future_lookahead_at_snapshot(self):
        observed = []
        def assessor(closes):
            observed.append(len(closes))
            return positive(closes)
        create_signal_snapshot(self.rows, assessor)
        self.assertEqual(observed, [70, 70, 69, 70, 70, 69])
        self.assertTrue(all(n <= 70 for n in observed))

if __name__ == "__main__":
    unittest.main()
