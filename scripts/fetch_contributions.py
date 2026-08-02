#!/usr/bin/env python3
"""
fetch_contributions.py — scrape the public contribution calendar HTML fragment
(no token needed) and write data/contributions.json with raw days + derived stats.

Usage:
    python scripts/fetch_contributions.py [username]

If username is omitted, reads GITHUB_USERNAME env var, else falls back to
the git remote origin owner.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

URL_TMPL = "https://github.com/users/{username}/contributions"


def guess_username() -> str:
    if os.environ.get("GITHUB_USERNAME"):
        return os.environ["GITHUB_USERNAME"]
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        # handles git@github.com:user/repo.git and https://github.com/user/repo.git
        remote = remote.replace(".git", "")
        if remote.startswith("git@"):
            owner = remote.split(":")[1].split("/")[0]
        else:
            owner = remote.rstrip("/").split("/")[-2]
        return owner
    except Exception:
        print("Could not determine username; pass it as an argument or set GITHUB_USERNAME.")
        sys.exit(1)


def fetch_days(username: str) -> list[dict]:
    url = URL_TMPL.format(username=username)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        cells = soup.select("[data-date]")

    # Counts live in separate <tool-tip for="<td-id>">N contributions on ...</tool-tip>
    # elements, not on the <td> itself. Build id -> count map first.
    count_by_id = {}
    for tip in soup.select("tool-tip"):
        target_id = tip.get("for")
        if not target_id:
            continue
        text = tip.get_text(strip=True)
        m = re.match(r"No contributions", text)
        if m:
            count_by_id[target_id] = 0
            continue
        m = re.match(r"([\d,]+)\s+contributions?", text)
        if m:
            count_by_id[target_id] = int(m.group(1).replace(",", ""))

    days = []
    for cell in cells:
        d = cell.get("data-date")
        level = cell.get("data-level")
        cell_id = cell.get("id")
        if d is None:
            continue
        level = int(level) if level is not None else 0
        count = count_by_id.get(cell_id)
        if count is None:
            # fall back to data-count attr if present, else infer from level
            count_attr = cell.get("data-count")
            count = int(count_attr) if count_attr and count_attr.isdigit() else 0
        days.append({"date": d, "level": level, "count": count})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] or 0 for d in days)

    # streaks
    current_streak = 0
    longest_streak = 0
    running = 0
    today = date.today().isoformat()
    for d in days:
        active = (d["count"] or 0) > 0 or (d["level"] or 0) > 0
        if active:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
    # current streak: walk backwards from most recent day
    for d in reversed(days):
        active = (d["count"] or 0) > 0 or (d["level"] or 0) > 0
        if active:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"] or 0, default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + (d["count"] or 0)

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly,
        "generated_at": date.today().isoformat(),
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else guess_username()
    print(f"Fetching contributions for {username}...")
    days = fetch_days(username)
    if not days:
        print("Warning: no contribution cells parsed. GitHub's markup may have changed.")
    stats = compute_stats(days)

    out = {"username": username, "days": days, "stats": stats}
    os.makedirs("data", exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote data/contributions.json ({len(days)} days, {stats['total_contributions']} contributions)")
