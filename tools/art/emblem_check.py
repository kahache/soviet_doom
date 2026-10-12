"""Verification sheet for the SDSTAR1 hammer-and-sickle emblem.

Run with the project venv (after gen_soviet_base.py):
  .venv/bin/python tools/art/emblem_check.py

Writes to work/art/batch1/:
  emblem_check.png       left: the emblem alone (no plaque, no star) at
                         CHECK_PX x CHECK_PX; right: the same with the two
                         reference circles and the CEO's reference points
                         drawn on top, to compare with the CEO's image.
  SDSTAR1_emblem_8x.png  the batch PNG of SDSTAR1 upscaled 8x, nearest.

All coordinates annotated on the right panel are in the unit square of
gen_soviet_base (origin top-left, y down), the frame the CEO measured in.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_soviet_base as gen  # noqa: E402
from artlib import FONT_SMALL, Overlay, ramp_colour  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BATCH_DIR = PROJECT_ROOT / "work" / "art" / "batch1"
CHECK_OUT = BATCH_DIR / "emblem_check.png"
ZOOM_OUT = BATCH_DIR / "SDSTAR1_emblem_8x.png"
ZOOM = 8

CHECK_PX = 256            # size of each panel (the emblem fills it)
GAP = 16                  # between the two panels
GUIDE = (0, 220, 255)     # cyan guides over gold/red
POINT_R = 3.0
LABEL_PX = 9

# (label, point) in unit-square coordinates: the CEO's reference points.
REFERENCE_POINTS = [
    ("tip", gen.SICKLE_TIP),
    ("R", (0.98, 0.56)),
    ("B", (0.56, 0.98)),
    ("J", (0.24, 0.80)),
    ("sh0", gen.SICKLE_HANDLE[0]),
    ("sh1", gen.SICKLE_HANDLE[1]),
    ("hc", gen.HAMMER_HEAD_C),
    ("hh0", gen.HAMMER_HANDLE[0]),
    ("hh1", gen.HAMMER_HANDLE[1]),
]


def emblem_panel(with_guides: bool) -> np.ndarray:
    px = CHECK_PX
    red = ramp_colour("flag_red", 0.70)
    gold = ramp_colour("hazard_yellow", 0.88)
    dark = ramp_colour("flag_red", 0.25)
    bg = np.full((px, px, 3), red, dtype=np.uint8)
    ov = Overlay(px, px)
    gen.hammer_sickle(ov, px / 2, px / 2, px / 2, gold, dark)
    if with_guides:
        for c, r in ((gen.SICKLE_OUTER_C, gen.SICKLE_OUTER_R), (gen.SICKLE_INNER_C, gen.SICKLE_INNER_R)):
            ov.ellipse((c[0] - r) * px, (c[1] - r) * px, (c[0] + r) * px, (c[1] + r) * px,
                       outline=GUIDE, width=1.0)
        # the hammer's axis, to read its slope against the horizontal
        ov.line([(gen.HAMMER_HANDLE[0][0] * px, gen.HAMMER_HANDLE[0][1] * px),
                 (gen.HAMMER_HANDLE[1][0] * px, gen.HAMMER_HANDLE[1][1] * px)], GUIDE, 1.0)
        for label, (u, v) in REFERENCE_POINTS:
            x, y = u * px, v * px
            ov.line([(x - POINT_R, y), (x + POINT_R, y)], GUIDE, 1.0)
            ov.line([(x, y - POINT_R), (x, y + POINT_R)], GUIDE, 1.0)
            ov.text(x + 4, y - 4, f"{label} ({u:.2f},{v:.2f})", LABEL_PX, (255, 255, 255),
                    font=FONT_SMALL, anchor="lm")
    return ov.composite(bg)


def main() -> None:
    left = emblem_panel(False)
    right = emblem_panel(True)
    sheet = np.full((CHECK_PX, CHECK_PX * 2 + GAP, 3), 40, dtype=np.uint8)
    sheet[:, :CHECK_PX] = left
    sheet[:, CHECK_PX + GAP:] = right
    Image.fromarray(sheet, "RGB").save(CHECK_OUT)
    print(f"wrote {CHECK_OUT}")
    tex = Image.open(gen.OUT_DIR / "SDSTAR1.png").convert("RGB")
    tex.resize((tex.width * ZOOM, tex.height * ZOOM), Image.Resampling.NEAREST).save(ZOOM_OUT)
    print(f"wrote {ZOOM_OUT}")


if __name__ == "__main__":
    main()
