"""Experimental, conservative rendered post evidence extraction. No live feed changes."""
import re

TEAM = re.compile(r"(?:Team\s*YouTube|TYT)", re.I)
FIXED = re.compile(r"\[\s*(?:fixed|resolved)\s*\]", re.I)
FIXED_TEXT = re.compile(r"\b(?:this (?:issue|is) (?:has been |is )?fixed|this issue has been resolved|this is officially fixed|issue has been resolved|issue has been fixed)\b", re.I)

def extract_visible_evidence(body, expected_title):
    boundary = re.search(r"(?m)^All Replies\s*\(\d+\)", body)
    locked = re.search(r"(?mi)^This question is locked and replying has been disabled\\.$", body)
    if not boundary and not locked:
        return {"verified": False, "reason": "reply_boundary_missing"}
    stop = boundary.start() if boundary else locked.start()
    lines = [s.strip() for s in body[:stop].splitlines() if s.strip()]
    title_positions = [i for i, s in enumerate(lines) if s == expected_title]
    if len(title_positions) != 1:
        return {"verified": False, "reason": "title_not_located_uniquely"}
    p = title_positions[0]
    # Find the closest Original Poster badge preceding the title, not a site-wide count.
    candidates = [i for i in range(max(0,p-12),p) if lines[i] == "Original Poster"]
    if not candidates:
        return {"verified": False, "reason": "original_poster_not_near_title"}
    i = candidates[-1]
    if i < 3 or lines[i-2] != "Google Employee" or lines[i-1] != "•":
        return {"verified": False, "reason": "staff_badge_not_adjacent"}
    author = lines[i-3]
    if not TEAM.search(author):
        return {"verified": False, "reason": "not_identified_teamyoutube_author"}
    label = lines[p+1] if p+1<len(lines) else ""
    if label not in ("Fixed","Known Issue"):
        return {"verified":False,"reason":"unrecognized_status_label"}
    end = next((j for j in range(p+2,len(lines)) if lines[j] in ("Details","Reply")),len(lines))
    message = "\n".join(lines[p+2:end])
    if len(message)<25:
        return {"verified":False,"reason":"message_too_short"}
    # A headline with [FIXED] and explicit staff confirmation is stronger than a stale Known Issue badge.
    fixed_confirmed = bool(FIXED.search(expected_title) and (label=="Fixed" or FIXED_TEXT.search(message)))
    return {"verified":True,"author":author,"status_label":label,
            "fixed_confirmed":fixed_confirmed,
            "message_preview":message[:550],"reply_boundary":bool(boundary),
            "locked_thread":bool(locked and not boundary)}
