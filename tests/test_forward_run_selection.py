import unittest
from forward_run_selection import select_prior_snapshot_run

START = "2026-11-01T12:00:00Z"

def row(id, stamp, **extra):
    return {"id": id, "updated_at": stamp, "status": "completed",
            "conclusion": "success", "head_branch": "main", **extra}

class ForwardRunSelectionTests(unittest.TestCase):
    def test_single_prior_run_is_eligible(self):
        self.assertEqual(select_prior_snapshot_run(
            [row(12, "2026-11-01T11:00:00Z")], evaluation_started_at=START), 12)
    def test_latest_prior_run_chosen(self):
        self.assertEqual(select_prior_snapshot_run(
            [row(11, "2026-11-01T10:00:00Z"), row(12, "2026-11-01T11:00:00Z")],
            evaluation_started_at=START), 12)
    def test_future_run_ignored(self):
        self.assertIsNone(select_prior_snapshot_run(
            [row(13, "2026-11-01T13:00:00Z")], evaluation_started_at=START))
    def test_failed_and_wrong_branch_ignored(self):
        self.assertIsNone(select_prior_snapshot_run(
            [row(12, "2026-11-01T11:00:00Z", conclusion="failure"),
             row(13, "2026-11-01T11:00:00Z", head_branch="feature")],
            evaluation_started_at=START))
    def test_empty_list_pending(self):
        self.assertIsNone(select_prior_snapshot_run([], evaluation_started_at=START))
    def test_invalid_cutoff_rejected(self):
        with self.assertRaises(ValueError):
            select_prior_snapshot_run([], evaluation_started_at="not-a-date")
