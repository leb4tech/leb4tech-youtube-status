import unittest
from rendered_evidence import extract_visible_evidence
class EvidenceTests(unittest.TestCase):
    def test_verified_example(self):
        text="Back\nMariko (TeamYouTube)\nGoogle Employee\n•\nOriginal Poster\n4 days ago\n[FIXED] Analytics\nFixed\nHi Creators, the issue is fixed now.\nDetails\nAll Replies (10)\nGoogle Employee"
        x=extract_visible_evidence(text,"[FIXED] Analytics")
        self.assertTrue(x["verified"],x)
    def test_unverified_with_reply_badge_only(self):
        self.assertFalse(extract_visible_evidence("Some text\nAll Replies (1)\nGoogle Employee","Example")["verified"])
if __name__ == "__main__":
    unittest.main()
