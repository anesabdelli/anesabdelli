#!/usr/bin/env python3
"""Generate the editable profile information card as a standalone SVG."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path


NAME = "Anes Abdelli"
ROLE = "Software Engineer"
CORE_TECHNOLOGIES = ("TypeScript", "Java", "Python")
ALSO_USED = ("C", "Angular", "PHP", "Symfony", "HTML", "CSS")
HIGHLIGHTS = ("Based in Paris, France", "Focused on practical, well-structured applications")


def text_element(
    text: str,
    x: int,
    y: int,
    *,
    size: int = 15,
    color: str = "#dce8f5",
    weight: int = 400,
) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}">{escape(text)}</text>'
    )


def technology_chip(label: str, x: int, y: int, *, accent: str) -> str:
    width = max(56, len(label) * 9 + 24)
    return (
        f'<g><rect x="{x}" y="{y}" width="{width}" height="29" rx="14.5" '
        f'fill="#172438" stroke="#30445f"/>'
        f'<circle cx="{x + 13}" cy="{y + 14.5}" r="3" fill="{accent}"/>'
        f'{text_element(label, x + 23, y + 19, size=12, weight=600)}</g>'
    )


def create_card(destination: Path) -> None:
    core_positions = (28, 164, 264)
    other_positions = (28, 133, 234, 28, 137, 222)
    core_chips = "".join(
        technology_chip(name, x, 143, accent=accent)
        for name, x, accent in zip(
            CORE_TECHNOLOGIES, core_positions, ("#38bdf8", "#fb923c", "#a78bfa")
        )
    )
    other_chips = "".join(
        technology_chip(name, x, y, accent="#34d399")
        for name, x, y in zip(
            ALSO_USED,
            other_positions,
            (224, 224, 224, 260, 260, 260),
        )
    )
    content = [
        text_element(NAME, 28, 52, size=26, color="#ffffff", weight=700),
        text_element(ROLE, 29, 79, size=14, color="#7dd3fc", weight=600),
        text_element("CORE STACK", 28, 125, size=11, color="#94a3b8", weight=700),
        core_chips,
        text_element("ALSO USED", 28, 208, size=11, color="#94a3b8", weight=700),
        other_chips,
        text_element("HIGHLIGHTS", 28, 318, size=11, color="#94a3b8", weight=700),
        text_element(HIGHLIGHTS[0], 44, 347, size=14),
        text_element(HIGHLIGHTS[1], 44, 374, size=14),
        '<circle cx="33" cy="342" r="2.5" fill="#34d399"/>',
        '<circle cx="33" cy="369" r="2.5" fill="#34d399"/>',
    ]
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="560" height="410" viewBox="0 0 560 410" role="img" aria-labelledby="title description">
  <title id="title">{escape(NAME)} — profile card</title>
  <desc id="description">Role, core and additional technologies, and highlights.</desc>
  <defs>
    <linearGradient id="card-background" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#101b2e"/><stop offset="1" stop-color="#0b1220"/>
    </linearGradient>
  </defs>
  <rect width="560" height="410" rx="20" fill="url(#card-background)"/>
  <rect x="1" y="1" width="558" height="408" rx="19" fill="none" stroke="#263449" stroke-width="2"/>
  <path d="M28 96H532M28 303H532" stroke="#263449"/>
  <rect x="28" y="91" width="68" height="3" rx="1.5" fill="#38bdf8"/>
  {''.join(content)}
</svg>
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=Path("info-card.svg"))
    args = parser.parse_args()
    create_card(args.output)
    print(f"Profile card saved to {args.output}")


if __name__ == "__main__":
    main()
