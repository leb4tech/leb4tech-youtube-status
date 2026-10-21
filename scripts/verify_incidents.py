#!/usr/bin/env python3
"""Read-only incident verification; never modifies the live Blogger feed."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from rendered_evidence import extract_visible_evidence

FEED = Path("data/youtube-status.json")
OUT = Path("preview/incident-verification.json")

def classify(item, evidence):
    if not evidence.get("verified"):
        return "unverified", evidence.get("reason", "verification_failed")
    if evidence.get("fixed_confirmed"):
        return "fixed", "verified_original_post_fixed_confirmation"
    # A Known Issue badge is not proof an old issue is still active.
    if evidence.get("status_label") == "Known Issue":
        return "unverified", "known_issue_without_current_ongoing_confirmation"
    return "unverified", "insufficient_current_evidence"

def main():
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for item in feed.get("items", [])[:20]:
            page = browser.new_page(locale="en-US")
            record = {"id": item["id"], "url": item["url"], "title_en": item["title_en"]}
            try:
                response = page.goto(item["url"], wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(1800)
                body = page.locator("body").inner_text(timeout=10000)
                evidence = extract_visible_evidence(body, item["title_en"])
                if not response or response.status != 200:
                    evidence = {"verified": False, "reason": "unexpected_http"}
            except Exception as exc:
                evidence = {"verified": False, "reason": "render_error", "detail": str(exc)[:100]}
            finally:
                page.close()
            status, reason = classify(item, evidence)
            record.update({"review_status": status, "reason": reason,
                           "author": evidence.get("author"),
                           "status_label": evidence.get("status_label"),
                           "structure_verified": bool(evidence.get("verified"))})
            records.append(record)
            print("THREAD", item["id"], "status", status, "reason", reason)
        browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "publication_ready": False,
        "review_only": True,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Not a real-time outage list. Unverified never implies no outages.",
        "records": records,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("SUMMARY",len(records),"verified fixed",sum(x["review_status"]=="fixed" for x in records),
          "unverified",sum(x["review_status"]=="unverified" for x in records))
    for rec in records:
        if rec["review_status"] == "unverified":
            print("REVIEW_REQUIRED", rec["id"], "reason:", rec["reason"],
                  "label:", rec.get("status_label"), "title:", rec["title_en"][:120])

if __name__ == "__main__":
    main()
