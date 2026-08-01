#!/usr/bin/env python3
"""Scrape the public GitHub contribution calendar - no token required.

GitHub serves the calendar as public HTML at
    https://github.com/users/<username>/contributions

Writes data/contributions.json with the raw days plus derived stats.

Usage:
    python scripts/fetch_contributions.py
    python scripts/fetch_contributions.py --demo   # offline placeholder data
"""
import json
import os
import pathlib
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

USER = os.environ.get("GH_USER", "tusharbeckham")
OUT = pathlib.Path("data/contributions.json")
URL = "https://github.com/users/" + USER + "/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art bot)",
    "X-Requested-With": "XMLHttpRequest",
}


def scrape() -> list[dict]:
    import requests
    from bs4 import BeautifulSoup

    html = requests.get(URL, headers=HEADERS, timeout=30)
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")

    # Current markup keeps the number OUT of the day cell: the cell carries only
    # data-date / data-level / id, and a sibling <tool-tip for="<cell id>"> holds
    # "12 contributions on August 1st" or "No contributions on ...".
    tips: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        head = tip.get_text(" ", strip=True).split(" ", 1)[0]
        tips[target] = int(head) if head.isdigit() else 0

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day"):
        day = cell.get("data-date")
        if not day:
            continue

        count = cell.get("data-count")           # older markup
        if count is None:
            cid = cell.get("id")
            if cid in tips:
                count = tips[cid]                # current markup
            else:
                text = cell.get_text(" ", strip=True)
                head = text.split(" ", 1)[0] if text else ""
                count = int(head) if head.isdigit() else None

        level = int(cell.get("data-level") or 0)
        if count is None:
            # last resort: no number anywhere, so approximate from the shade
            count = [0, 2, 6, 12, 20, 30][min(level, 5)]

        days.append({"date": day, "count": int(count), "level": level})

    if not days:
        raise RuntimeError("no day cells found - GitHub markup may have changed")

    if sum(d["count"] for d in days) == 0 and any(d["level"] for d in days):
        raise RuntimeError(
            "parsed every day as zero while the calendar shows activity - "
            "GitHub markup changed, refusing to overwrite good data"
        )

    days.sort(key=lambda d: d["date"])
    return days


def demo() -> list[dict]:
    """Deterministic placeholder calendar so the art renders offline."""
    rng = random.Random(29)
    end = date.today()
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday
    days = []
    d = start
    while d <= end:
        base = 0 if d.weekday() == 6 and rng.random() < 0.35 else rng.randint(0, 14)
        burst = rng.random() < 0.18
        count = base + (rng.randint(10, 28) if burst else 0)
        days.append({"date": d.isoformat(), "count": count, "level": 0})
        d += timedelta(days=1)
    return days


def level_for(count: int) -> int:
    if count <= 0:
        return 0
    if count < 4:
        return 1
    if count < 9:
        return 2
    if count < 16:
        return 3
    if count < 28:
        return 4
    return 5


def derive(days: list[dict]) -> dict:
    for d in days:
        d["level"] = level_for(d["count"])

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)

    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif current or d is not days[-1]:
            break

    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    return {
        "user": USER,
        "generated": date.today().isoformat(),
        "total": total,
        "currentStreak": current,
        "longestStreak": longest,
        "bestDay": {"date": best["date"], "count": best["count"]},
        "monthly": dict(sorted(monthly.items())),
        "days": days,
    }


def main() -> None:
    use_demo = "--demo" in sys.argv
    if use_demo:
        days = demo()
    else:
        try:
            days = scrape()
        except Exception as exc:  # keep the workflow green, keep yesterday's art
            print(f"! fetch failed: {exc}")
            if OUT.exists():
                print("  keeping existing data/contributions.json")
                return
            raise

    payload = derive(days)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1))
    print(
        f"wrote {OUT}  {payload['total']} contributions, "
        f"streak {payload['currentStreak']}d, longest {payload['longestStreak']}d"
    )


if __name__ == "__main__":
    main()
