#!/usr/bin/env python3
"""Fetch YouTube known-issue thread index into a conservative public JSON feed."""
import datetime as dt
import html
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlencode
import time
from bs4 import BeautifulSoup
from status_tracking import reconcile

SOURCE = "https://support.google.com/youtube/threads?thread_filter=%28purpose%3Aknown_issue%29&hl=en"
OUTPUT = Path("data/youtube-status.json")
HISTORY = Path("data/status-history.json")

def translate_ar(text):
    """Best-effort unofficial public translation endpoint; may be rate-limited."""
    params = urlencode({"client":"gtx", "sl":"en", "tl":"ar", "dt":"t", "q":text})
    req = urllib.request.Request("https://translate.googleapis.com/translate_a/single?" + params, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            result = json.load(res)
        translated = "".join(part[0] for part in result[0] if part and part[0])
        if re.search("[\u0600-\u06ff]", translated):
            return translated.strip()
    except Exception as exc:
        print("Translation service unavailable:", type(exc).__name__)
    return None

def main():
    request = urllib.request.Request(SOURCE, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Leb4TechStatusMonitor/1.0)"
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP status {response.status}")
        body = response.read(3_000_000).decode("utf-8", "replace")
    soup = BeautifulSoup(body, "html.parser")
    items, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = urljoin("https://support.google.com", html.unescape(a["href"]))
        match = re.match(r"^/youtube/thread/(\d+)", urlsplit(href).path)
        if not match:
            continue
        post_id = match.group(1)
        if post_id in seen:
            continue
        parts = list(a.stripped_strings)
        if not parts:
            continue
        title = re.sub(r"\s+", " ", parts[0]).strip()
        title = re.split(r"\b(?:Hi Creators|Hey Everyone|Hi all|Update:)\b", title, maxsplit=1, flags=re.I)[0].strip()
        if len(title) < 8:
            continue
        # Only report 'fixed' when the headline explicitly labels it.
        fixed = bool(re.search(r"\[\s*fixed\s*\]", title, re.I))
        # Unlabeled content is NOT automatically an active outage.
        status = "fixed" if fixed else "unverified"
        items.append({
            "id": post_id,
            "title_en": title[:180],
            "status": status,
            "url": f"https://support.google.com/youtube/thread/{post_id}?hl=en",
            "excerpt_en": re.sub(r"\s+", " ", " ".join(parts))[:300],
        })
        seen.add(post_id)
    if len(items) < 5:
        raise RuntimeError(f"Too few extracted threads ({len(items)}); preserving previous feed")
    previous_items = {}
    old_feed = {}
    if OUTPUT.exists():
        try:
            old_feed = json.loads(OUTPUT.read_text(encoding="utf-8"))
            previous_items = {x["id"]:x for x in old_feed.get("items", [])}
        except (OSError, ValueError, KeyError):
            pass
    translated_count = 0
    for item in items:
        clean = re.sub(r"^\s*🚨?\s*\[\s*fixed\s*\]\s*", "", item["title_en"], flags=re.I).strip()
        previous = previous_items.get(item["id"], {})
        if previous.get("title_en") == item["title_en"] and previous.get("title_ar"):
            item["title_ar"] = previous["title_ar"]
        else:
            item["title_ar"] = translate_ar(clean)
            if item["title_ar"]:
                translated_count += 1
                time.sleep(0.4)
        item["summary_ar"] = ("أعلن فريق YouTube إصلاح المشكلة. التفاصيل في المصدر الرسمي." if item["status"] == "fixed" else None)
    print("New Arabic translations:", translated_count)
    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    old_history = {}
    if HISTORY.exists():
        try:
            old_history = json.loads(HISTORY.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError("Cannot read existing history; refusing to overwrite") from exc
    items, history, changes = reconcile(items, old_feed, old_history, generated)
    print("Tracking:", changes)
    payload = {
        "version": 3,
        "source": SOURCE,
        "checked_at_utc": generated,
        "scope": "Recent visible known-issue forum threads, not all YouTube incidents",
        "active_count_confirmed": None,
        "date_field_note": "first_seen_at and status_observed_since are crawler observation times, not official post dates",
        "items": items[:30],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(payload['items'])} threads; fixed={sum(x['status']=='fixed' for x in items)}, unverified={sum(x['status']=='unverified' for x in items)}")
    print("No active-outage count inferred; timestamps are fetch times, not post times.")

if __name__ == "__main__":
    main()
