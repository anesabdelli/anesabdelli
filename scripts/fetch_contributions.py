#!/usr/bin/env python3
"""Fetch public GitHub contribution counts without using an API token."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


CONTRIBUTION_PATTERN = re.compile(r"([\d,]+)\s+contributions?", re.IGNORECASE)


def count_for_cell(cell: Tag, tooltip: str) -> int:
    for attribute in ("data-count", "data-total"):
        value = cell.get(attribute)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                pass

    match = CONTRIBUTION_PATTERN.search(tooltip)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def fetch_contributions(username: str, destination: Path) -> int:
    end = date.today()
    start = end - timedelta(days=364)
    contributions: dict[str, dict[str, int]] = {}
    url = f"https://github.com/users/{username}/contributions"
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    for year in range(start.year, end.year + 1):
        response = session.get(
            url,
            params={"from": f"{year}-01-01", "to": f"{year}-12-31"},
            headers={"User-Agent": "profile-art-generator/1.0"},
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        tooltips = {
            tooltip.get("for"): tooltip.get_text(" ", strip=True)
            for tooltip in soup.select("tool-tip[for]")
        }
        for cell in soup.select(".ContributionCalendar-day[data-date][data-level]"):
            day = cell.get("data-date")
            if not day or not start.isoformat() <= day <= end.isoformat():
                continue
            try:
                level = int(cell.get("data-level", "0"))
            except ValueError:
                level = 0
            contributions[day] = {
                "count": count_for_cell(cell, tooltips.get(cell.get("id"), "")),
                "level": min(4, max(0, level)),
            }

    expected_days = (end - start).days + 1
    if len(contributions) != expected_days:
        raise RuntimeError(
            f"Expected {expected_days} public contribution days, found {len(contributions)}. "
            "GitHub may have changed its public page markup or rate-limited this request."
        )

    entries = [
        {"date": day.isoformat(), **contributions[day.isoformat()]}
        for day in sorted(date.fromisoformat(value) for value in contributions)
    ]
    snapshot_updated_at = datetime.now(timezone.utc).isoformat()
    if destination.is_file():
        previous = json.loads(destination.read_text(encoding="utf-8"))
        if (
            previous.get("contributions") == entries
            and previous.get("start_date") == start.isoformat()
            and previous.get("end_date") == end.isoformat()
        ):
            snapshot_updated_at = previous.get("snapshot_updated_at", snapshot_updated_at)

    data = {
        "username": username,
        "snapshot_updated_at": snapshot_updated_at,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "contributions": entries,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return len(contributions)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", nargs="?", default="anesabdelli")
    parser.add_argument("-o", "--output", type=Path, default=Path("data/contributions.json"))
    args = parser.parse_args()
    count = fetch_contributions(args.username, args.output)
    print(f"Saved {count} public contribution days for {args.username} to {args.output}")


if __name__ == "__main__":
    main()
