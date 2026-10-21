"""Conservative YouTube Community incident classification.

Never infer an active outage from an unlabeled post, a generic alert emoji,
or an excerpt alone. Statuses remain compatible with the Blogger widget.
"""
import re

FIXED_TAG = re.compile(r"\[\s*(?:fixed|resolved)\s*\]", re.I)
ISSUE_TAG = re.compile(r"\[\s*(?:known\s+issue|ongoing\s+issue)\s*\]", re.I)
RESOLVED_TEXT = re.compile(
    r"\b(?:this issue (?:has been|is) resolved|issue (?:has been|is) fixed|"
    r"this issue has been fixed|we have fixed (?:the|this) issue|"
    r"the issue (?:has been|is) resolved)\b", re.I
)
ONGOING_TEXT = re.compile(
    r"\b(?:we(?:'re| are) (?:aware of|investigating|working on)|"
    r"our team is (?:aware|investigating|working on)|"
    r"we have identified an issue|currently investigating)\b", re.I
)

def classify(title, body_text=None):
    """Return status, reason; body_text must be from the specific official thread."""
    if FIXED_TAG.search(title):
        return "fixed", "explicit_fixed_title"
    if not ISSUE_TAG.search(title):
        return "unverified", "no_explicit_issue_marker"
    if not body_text:
        return "unverified", "details_unavailable"
    if RESOLVED_TEXT.search(body_text):
        return "unverified", "resolved_text_without_updated_title"
    if ONGOING_TEXT.search(body_text):
        return "active", "explicit_issue_title_and_ongoing_statement"
    return "unverified", "no_ongoing_confirmation"

def classify_from_official_page(title, url):
    """A headline-only feed cannot safely establish an active outage.

    A future release may verify the original staff post with a validated
    page selector. Until then, explicit FIXED tags are safe and the rest
    remain unverified.
    """
    if FIXED_TAG.search(title):
        return "fixed", "explicit_fixed_title"
    if ISSUE_TAG.search(title):
        return "unverified", "official_body_not_verified"
    return "unverified", "no_explicit_issue_marker"
