#!/usr/bin/env python3
"""Render public contribution data as a GitHub-style SVG heatmap."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape


COLORS = ("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39")


def render_heatmap(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Contribution data does not exist: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    entries = data.get("contributions")
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"No contribution days found in {source}")

    by_day = {date.fromisoformat(item["date"]): item for item in entries}
    start = min(by_day)
    end = max(by_day)
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    week_count = ((end - grid_start).days // 7) + 1
    cell = 12
    gap = 3
    left = 36
    top = 32
    width = left + week_count * (cell + gap) + 10
    height = top + 7 * (cell + gap) + 30
    elements = []

    month_positions: dict[tuple[int, int], int] = {}
    for week in range(week_count):
        for weekday in range(7):
            day = grid_start + timedelta(days=week * 7 + weekday)
            if day > end or day < start:
                continue
            record = by_day.get(day, {"count": 0, "level": 0})
            level = min(4, max(0, int(record.get("level", 0))))
            x = left + week * (cell + gap)
            y = top + weekday * (cell + gap)
            label = f'{record.get("count", 0)} contributions on {day.isoformat()}'
            elements.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{COLORS[level]}"><title>{escape(label)}</title></rect>'
            )
            if day.day == 1:
                month_positions.setdefault((day.year, day.month), x)

    labels = []
    for (year, month), x in sorted(month_positions.items()):
        labels.append(
            f'<text x="{x}" y="19">{date(year, month, 1).strftime("%b")}</text>'
        )

    username = escape(str(data.get("username", "GitHub user")))
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">{username}'s public GitHub contributions</title>
  <desc id="description">Daily contribution activity from {start.isoformat()} through {end.isoformat()}.</desc>
  <style>text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #57606a; font-size: 11px; }}</style>
  {''.join(labels)}
  <text x="4" y="{top + 26}">Mon</text><text x="4" y="{top + 56}">Wed</text><text x="4" y="{top + 86}">Fri</text>
  {''.join(elements)}
</svg>
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", type=Path, default=Path("data/contributions.json"))
    parser.add_argument("-o", "--output", type=Path, default=Path("contrib-heatmap.svg"))
    args = parser.parse_args()
    render_heatmap(args.input, args.output)
    print(f"Contribution heatmap saved to {args.output}")


if __name__ == "__main__":
    main()
