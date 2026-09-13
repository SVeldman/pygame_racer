"""Generate simple placeholder PNG sprites for the racer project.

These are stand-ins so class time goes to coding, not art. Swap in real
sprites later - keep the same filenames and folder (`images/`, lowercase).

Usage:
    python assets/make_placeholder_assets.py week_1/images
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw


def car(path: Path, body, *, w=44, h=78):
    """A top-down car facing UP: rounded body, darker windshield, wheels."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # wheels (drawn first so the body overlaps them)
    wheel = (25, 25, 25, 255)
    d.rounded_rectangle([2, 12, 12, 30], radius=3, fill=wheel)
    d.rounded_rectangle([w - 12, 12, w - 2, 30], radius=3, fill=wheel)
    d.rounded_rectangle([2, h - 30, 12, h - 12], radius=3, fill=wheel)
    d.rounded_rectangle([w - 12, h - 30, w - 2, h - 12], radius=3, fill=wheel)
    # body
    d.rounded_rectangle([6, 2, w - 6, h - 2], radius=12, fill=body)
    # windshield (toward the front / top)
    d.rounded_rectangle([12, 12, w - 12, 30], radius=5, fill=(180, 220, 255, 255))
    # rear window
    d.rounded_rectangle([12, h - 26, w - 12, h - 12], radius=5, fill=(120, 160, 190, 255))
    img.save(path)
    print("wrote", path)


def tile(path: Path, color, *, size=64):
    img = Image.new("RGBA", (size, size), color)
    img.save(path)
    print("wrote", path)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "week_1/images")
    out.mkdir(parents=True, exist_ok=True)

    car(out / "car_red.png", (210, 55, 45, 255))
    car(out / "car_blue.png", (50, 110, 210, 255))
    car(out / "car_green.png", (60, 170, 90, 255))
    car(out / "car_yellow.png", (230, 195, 60, 255))

    # optional textures - the week 1 code draws the road with rectangles,
    # but later weeks can use these.
    tile(out / "road.png", (60, 60, 68, 255))
    tile(out / "grass.png", (40, 120, 55, 255))


if __name__ == "__main__":
    main()
