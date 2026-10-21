"""Experimental evidence extractor. Does not affect the public JSON feed."""
import re

def extract_visible_evidence(body, expected_title):
    boundary = re.search(r"(?m)^All Replies\s*\(\d+\)", body)
    if not boundary:
        return {"verified": False, "reason": "reply_boundary_missing"}
    before = body[:boundary.start()]
    lines = [line.strip() for line in before.splitlines() if line.strip()]
    op_indices = [i for i, line in enumerate(lines) if line == "Original Poster"]
    if len(op_indices) != 1:
        return {"verified": False, "reason": "original_poster_marker_ambiguous"}
    i = op_indices[0]
    if i < 2 or lines[i - 2] != "Google Employee":
        return {"verified": False, "reason": "staff_badge_not_adjacent"}
    author = lines[i - 3] if i >= 3 else ""
    if not author or not re.search(r"(TeamYouTube|TYT)", author, re.I):
        return {"verified": False, "reason": "not_identified_teamyoutube_author"}
    title_positions = [j for j in range(i + 1, len(lines)) if lines[j] == expected_title]
    if len(title_positions) != 1:
        return {"verified": False, "reason": "title_not_located_uniquely"}
    p = title_positions[0]
    status = lines[p + 1] if p + 1 < len(lines) else ""
    if status not in ("Fixed", "Known Issue"):
        return {"verified": False, "reason": "unrecognized_status_label"}
    end = next((j for j in range(p + 2, len(lines)) if lines[j] in ("Details", "Reply")), len(lines))
    message = "\n".join(lines[p + 2:end])
    if len(message) < 25:
        return {"verified": False, "reason": "message_too_short"}
    return {"verified": True, "author": author, "status_label": status,
            "message_preview": message[:550], "reply_boundary": True}
