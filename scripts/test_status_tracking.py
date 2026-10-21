#!/usr/bin/env python3
import unittest
from status_tracking import reconcile


def item(status="unverified", title="Example issue"):
    return {"id":"123","status":status,"title_en":title,"title_ar":"مثال","url":"https://support.google.com/youtube/thread/123"}


class TrackingTests(unittest.TestCase):
    def test_first_observation(self):
        rows, history, stats = reconcile([item()], {}, {}, "2026-10-21T20:00:00+00:00")
        self.assertEqual(stats, {"new":1,"status_changes":0,"title_changes":0})
        self.assertEqual(rows[0]["first_seen_at"], "2026-10-21T20:00:00+00:00")
        self.assertEqual(history["threads"]["123"]["changes"], [])

    def test_repeated_scan_does_not_create_change(self):
        first, hist, _ = reconcile([item()], {}, {}, "2026-10-21T20:00:00+00:00")
        second, hist, stats = reconcile([item()], {"items":first}, hist, "2026-10-21T21:00:00+00:00")
        self.assertEqual(stats, {"new":0,"status_changes":0,"title_changes":0})
        self.assertEqual(second[0]["first_seen_at"], first[0]["first_seen_at"])
        self.assertEqual(second[0]["status_observed_since"], first[0]["status_observed_since"])

    def test_fixed_transition_preserves_identity(self):
        first, hist, _ = reconcile([item()], {}, {}, "2026-10-21T20:00:00+00:00")
        second, hist, stats = reconcile([item("fixed")], {"items":first}, hist, "2026-10-21T21:00:00+00:00")
        self.assertEqual(stats["status_changes"], 1)
        self.assertEqual(second[0]["first_seen_at"], first[0]["first_seen_at"])
        self.assertEqual(second[0]["status_observed_since"], "2026-10-21T21:00:00+00:00")
        self.assertEqual(hist["threads"]["123"]["changes"][0]["from"], "unverified")
        self.assertEqual(hist["threads"]["123"]["changes"][0]["to"], "fixed")

    def test_missing_from_page_is_not_deleted(self):
        first, hist, _ = reconcile([item()], {}, {}, "2026-10-21T20:00:00+00:00")
        _, hist, _ = reconcile([], {"items":first}, hist, "2026-10-21T21:00:00+00:00")
        self.assertIn("123", hist["threads"])

    def test_title_change_is_not_status_change(self):
        first, hist, _ = reconcile([item()], {}, {}, "2026-10-21T20:00:00+00:00")
        _, hist, stats = reconcile([item(title="Revised title")], {"items":first}, hist, "2026-10-21T21:00:00+00:00")
        self.assertEqual(stats["status_changes"], 0)
        self.assertEqual(stats["title_changes"], 1)


if __name__ == "__main__":
    unittest.main()
