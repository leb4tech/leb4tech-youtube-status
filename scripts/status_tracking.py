"""State tracking for Leb4Tech known-issue monitoring.

Times are when our crawler observed a change, NOT official publication times.
"""
from datetime import datetime, timezone


def reconcile(items, old_feed, old_history, checked_at):
    known = dict(old_history.get("threads", {}))
    old_visible = {str(x.get("id")): x for x in old_feed.get("items", [])}
    transitions = 0
    new_posts = 0
    changed_titles = 0

    for item in items:
        pid = str(item["id"])
        status = item["status"]
        title = item["title_en"]
        old = known.get(pid) or old_visible.get(pid) or {}
        existing = bool(old)
        history = list(old.get("changes", []))
        first_seen = old.get("first_seen_at") or checked_at
        previous_status = old.get("status")
        previous_title = old.get("title_en")
        status_changed = existing and previous_status is not None and previous_status != status
        title_changed = existing and previous_title is not None and previous_title != title
        if status_changed:
            transitions += 1
            history.append({"observed_at": checked_at, "field": "status", "from": previous_status, "to": status})
        if title_changed:
            changed_titles += 1
            history.append({"observed_at": checked_at, "field": "title_en", "from": previous_title, "to": title})
        if not existing:
            new_posts += 1
        status_since = checked_at if status_changed else old.get("status_observed_since") or first_seen
        title_since = checked_at if title_changed else old.get("title_observed_since") or first_seen

        record = {
            "id": pid, "title_en": title, "status": status,
            "first_seen_at": first_seen, "last_seen_at": checked_at,
            "status_observed_since": status_since,
            "title_observed_since": title_since,
            "changes": history[-30:]
        }
        known[pid] = record
        # Backwards-compatible with existing Blogger widgets.
        item["first_seen_at"] = first_seen
        item["last_seen_at"] = checked_at
        item["status_observed_since"] = status_since
        item["title_observed_since"] = title_since

    return items, {
        "version": 1,
        "time_meaning": "Crawler observation time (UTC), not official YouTube publication or fix time",
        "updated_at_utc": checked_at,
        "threads": known,
    }, {"new": new_posts, "status_changes": transitions, "title_changes": changed_titles}
