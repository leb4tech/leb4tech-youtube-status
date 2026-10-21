#!/usr/bin/env python3
"""Fetch YouTube known-issue thread index into a conservative public JSON feed."""
import datetime as dt
import html
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

SOURCE = "https://support.google.com/youtube/threads?thread_filter=%28purpose%3Aknown_issue%29&hl=en"
OUTPUT = Path("data/youtube-status.json")

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
    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "version": 1,
        "source": SOURCE,
        "checked_at_utc": generated,
        "scope": "Recent visible known-issue forum threads, not all YouTube incidents",
        "active_count_confirmed": None,
        "items": items[:30],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(payload['items'])} threads; fixed={sum(x['status']=='fixed' for x in items)}, unverified={sum(x['status']=='unverified' for x in items)}")
    print("No active-outage count inferred; timestamps are fetch times, not post times.")

if __name__ == "__main__":
    main()
