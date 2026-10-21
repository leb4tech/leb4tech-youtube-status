#!/usr/bin/env python3
"""Prepare a separate, safe display feed from verified review output."""
import json
from pathlib import Path
source = json.loads(Path("data/youtube-status.json").read_text(encoding="utf-8"))
review = json.loads(Path("preview/incident-verification.json").read_text(encoding="utf-8"))
lookup = {str(x["id"]):x for x in source.get("items",[])}
items = []
for rec in review["records"]:
    original = lookup.get(str(rec["id"]))
    if not original:
        continue
    status = rec["review_status"]
    if status not in ("fixed","unverified"):
        raise ValueError("Unexpected review status: "+str(status))
    if status=="fixed" and not rec.get("structure_verified"):
        raise ValueError("Fixed classification without verified structure")
    items.append({
        "id":str(rec["id"]), "title_ar":original.get("title_ar"),
        "title_en":original["title_en"], "url":original["url"],
        "status":status, "status_reason":rec["reason"],
        "first_seen_at":original.get("first_seen_at"),
        "status_observed_since":original.get("status_observed_since"),
    })
if len(items)<5:
    raise RuntimeError("Too few reviewed posts: refusing overwrite")
out={"version":1,"checked_at_utc":review["checked_at_utc"],
     "scope":"Reviewed recent forum posts, not a complete live outage inventory",
     "official_post_dates_available":False,
     "active_status_enabled":False,
     "items":items}
Path("data/verified-status.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("VERIFIED_DISPLAY_FEED",len(items),"fixed",sum(x["status"]=="fixed" for x in items),
      "unverified",sum(x["status"]=="unverified" for x in items))
