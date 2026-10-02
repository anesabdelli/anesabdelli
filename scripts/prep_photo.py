#!/usr/bin/env python3
"""Normalize a portrait photo and remove its background for ASCII conversion."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
def prepare_photo(
    source: Path,
    destination: Path,
    size: int,
    remove_background: bool,
) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Input photo does not exist: {source}")

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGBA")
        image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        if remove_background:
            from rembg import remove

            encoded = BytesIO()
            image.save(encoded, format="PNG")
            image = Image.open(
                BytesIO(remove(encoded.getvalue(), alpha_matting=True))
            ).convert("RGBA")

    prepared = ImageOps.fit(
        image,
        (size, size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.42),
    )
    background = Image.new("RGBA", prepared.size, (11, 18, 32, 255))
    background.alpha_composite(prepared)
    destination.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(destination, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", nargs="?", type=Path, default=Path("data/profile-photo.jpg"))
    parser.add_argument("-o", "--output", type=Path, default=Path("data/source-prepped.png"))
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument(
        "--remove-background",
        action="store_true",
        help="Use rembg to remove the background before preparing the image",
    )
    args = parser.parse_args()
    if args.size < 32:
        parser.error("--size must be at least 32 pixels")

    prepare_photo(args.photo, args.output, args.size, args.remove_background)
    print(f"Prepared portrait saved to {args.output}")


if __name__ == "__main__":
    main()
