import unittest
from rendered_evidence import extract_visible_evidence
class EvidenceTests(unittest.TestCase):
    def test_verified_example(self):
        text="Back\nMariko (TeamYouTube)\nGoogle Employee\n•\nOriginal Poster\n4 days ago\n[FIXED] Analytics\nFixed\nHi Creators, the issue is fixed now.\nDetails\nAll Replies (10)\nGoogle Employee"
        x=extract_visible_evidence(text,"[FIXED] Analytics")
        self.assertTrue(x["verified"],x)
    def test_unverified_with_reply_badge_only(self):
        self.assertFalse(extract_visible_evidence("Some text\nAll Replies (1)\nGoogle Employee","Example")["verified"])
    def test_team_youtube_spaced_name_and_stale_badge(self):
        text = "Back\nMichelle (Team YouTube)\nGoogle Employee\n•\nOriginal Poster\nAug 28, 2026\n🚨[Fixed] Livestream Captions\nKnown Issue\nUpdate: This issue has been fixed. Please refresh your app.\nDetails\nAll Replies (5)"
        result = extract_visible_evidence(text, "🚨[Fixed] Livestream Captions")
        self.assertTrue(result["verified"], result)
        self.assertTrue(result["fixed_confirmed"])

    def test_teamyoutube_hyphenated_name(self):
        text = "Back\nCamila - TeamYouTube\nGoogle Employee\n•\nOriginal Poster\nSep 16, 2026\n🚨 [FIXED] Analytics loading\nFixed\nThis is officially fixed! Analytics is working again.\nDetails\nAll Replies (1)"
        self.assertTrue(extract_visible_evidence(text, "🚨 [FIXED] Analytics loading")["verified"])

    def test_locked_staff_thread_without_replies(self):
        text = "Back\nJulia-TeamYouTube\nGoogle Employee\n•\nOriginal Poster\nAug 27, 2026\n🚨 [FIXED] Voice search errors across multiple devices\nFixed\nThe voice search feature is back up and running on all devices.\nDetails\nThis question is locked and replying has been disabled."
        result = extract_visible_evidence(text, "🚨 [FIXED] Voice search errors across multiple devices")
        self.assertTrue(result["verified"], result)
        self.assertTrue(result["locked_thread"])
        self.assertTrue(result["fixed_confirmed"])

    def test_no_replies_and_no_lock_remains_unverified(self):
        text = "Back\nJulia-TeamYouTube\nGoogle Employee\n•\nOriginal Poster\nAug 27, 2026\n[FIXED] Voice search\nFixed\nVoice search recovered."
        self.assertFalse(extract_visible_evidence(text, "[FIXED] Voice search")["verified"])

if __name__ == "__main__":
    unittest.main()
