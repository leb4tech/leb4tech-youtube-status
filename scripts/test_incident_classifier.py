import unittest
from incident_classifier import classify, classify_from_official_page

class ClassifierTests(unittest.TestCase):
    def test_fixed_title(self):
        self.assertEqual(classify_from_official_page("[FIXED] Video upload errors", "")[0], "fixed")
    def test_untagged_is_not_active(self):
        self.assertEqual(classify_from_official_page("Problems with analytics", "")[0], "unverified")
    def test_issue_without_verified_official_body_is_not_active(self):
        self.assertEqual(classify_from_official_page("[Known Issue] Analytics", "")[0], "unverified")
    def test_explicit_issue_and_ongoing_official_text(self):
        self.assertEqual(classify("[Known Issue] Analytics", "We're investigating an issue.")[0], "active")
    def test_resolution_overrides_old_ongoing_phrase(self):
        self.assertEqual(classify("[Known Issue] Analytics", "We're investigating. This issue has been resolved.")[0], "unverified")

if __name__ == "__main__":
    unittest.main()
