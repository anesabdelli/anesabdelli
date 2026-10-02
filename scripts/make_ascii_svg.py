#!/usr/bin/env python3
"""Render a preprocessed portrait as an animated, self-contained ASCII SVG."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image


GLYPHS = " .:-=+*#%@"


def create_ascii_svg(source: Path, destination: Path, columns: int, rows: int) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Preprocessed portrait does not exist: {source}")

    with Image.open(source) as image:
        gray = image.convert("L").resize((columns, rows), Image.Resampling.LANCZOS)
        pixels = np.asarray(gray, dtype=np.uint8)

    # Compensate for the height of monospaced glyphs, which are taller than they are wide.
    shades = (pixels.astype(np.float32) / 255 * (len(GLYPHS) - 1)).astype(np.uint8)
    width = columns * 9 + 24
    top = 64
    line_height = 10
    height = top + rows * line_height + 34
    text_rows = []
    for row_index, row in enumerate(shades):
        characters = "".join(GLYPHS[index] for index in row)
        text_rows.append(
            f'<text x="12" y="{row_index * line_height + top}">{escape(characters)}</text>'
        )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Animated ASCII portrait of Anes Abdelli</title>
  <desc id="description">A portrait made from ASCII characters with a moving cyan-to-violet light sweep.</desc>
  <defs>
    <linearGradient id="ascii-glow" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{width}" y2="0">
      <stop offset="0" stop-color="#67e8f9"/>
      <stop offset="0.42" stop-color="#c4b5fd"/>
      <stop offset="0.62" stop-color="#e0f2fe"/>
      <stop offset="1" stop-color="#67e8f9"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        values="-{width} 0;{width} 0;-{width} 0" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="scan-glow" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#22d3ee" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#22d3ee" stop-opacity="0.18"/>
      <stop offset="1" stop-color="#22d3ee" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="portrait-clip">
      <rect x="8" y="52" width="{width - 16}" height="{rows * line_height + 5}" rx="10"/>
    </clipPath>
  </defs>
  <rect width="100%" height="100%" rx="18" fill="#0b1220"/>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="none" stroke="#263449" stroke-width="2"/>
  <circle cx="21" cy="25" r="4" fill="#22d3ee"/>
  <text x="34" y="29" fill="#f8fafc" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12" font-weight="700" letter-spacing="1.5">ANES ABD. / ASCII PORTRAIT</text>
  <text x="{width - 76}" y="29" fill="#94a3b8" font-family="ui-monospace, monospace" font-size="9">LIVE ART</text>
  <g clip-path="url(#portrait-clip)">
    <rect x="8" y="52" width="{width - 16}" height="{rows * line_height + 5}" fill="#0e192b"/>
    <g fill="url(#ascii-glow)" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9" font-weight="700" xml:space="preserve">
    {''.join(text_rows)}
    </g>
    <rect x="8" y="52" width="{width - 16}" height="22" fill="url(#scan-glow)">
      <animate attributeName="y" values="52;{top + rows * line_height - 18};52" dur="6s" repeatCount="indefinite"/>
    </rect>
  </g>
  <text x="12" y="{height - 14}" fill="#64748b" font-family="ui-monospace, monospace" font-size="9">TYPE · FORM · LIGHT</text>
  <text x="{width - 65}" y="{height - 14}" fill="#64748b" font-family="ui-monospace, monospace" font-size="9">01 / 01</text>
</svg>
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path, default=Path("data/source-prepped.png"))
    parser.add_argument("-o", "--output", type=Path, default=Path("avi-ascii.svg"))
    parser.add_argument("--columns", type=int, default=56)
    parser.add_argument("--rows", type=int, default=40)
    args = parser.parse_args()
    if args.columns < 8 or args.rows < 8:
        parser.error("--columns and --rows must each be at least 8")

    create_ascii_svg(args.image, args.output, args.columns, args.rows)
    print(f"Animated ASCII portrait saved to {args.output}")


if __name__ == "__main__":
    main()
