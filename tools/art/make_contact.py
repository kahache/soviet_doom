"""Contact sheet of a texture batch: every lump side by side, nearest-neighbour
zoom, name above each one. For a quick look in chat; the HTML preview
(make_preview.py) is what the CEO validates on.

Run with the project venv (after gen_soviet_base.py):
  .venv/bin/python tools/art/make_contact.py

Writes work/art/batch1/contact.png (ZOOM x) and contact_half.png (half of
that, for pasting where a 2800 px image is too wide).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import FONT_SMALL  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BATCH_DIR = PROJECT_ROOT / "work" / "art" / "batch1"
MANIFEST = BATCH_DIR / "manifest.json"
CONTACT_OUT = BATCH_DIR / "contact.png"
HALF_OUT = BATCH_DIR / "contact_half.png"

ZOOM = 3                  # 64 px -> 192 px: joints and rivets readable at a glance
GAP = 10                  # px between lumps
LABEL_H = 16              # strip above each lump with its name
LABEL_PX = 10
BG = (30, 30, 34)
INK = (210, 208, 200)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tiles = [(t["lump"], Image.open(PROJECT_ROOT / t["file"]).convert("RGB")) for t in manifest["textures"]]
    width = GAP + sum(im.width * ZOOM + GAP for _, im in tiles)
    height = LABEL_H + max(im.height for _, im in tiles) * ZOOM + GAP
    sheet = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT_SMALL, LABEL_PX)
    x = GAP
    for lump, im in tiles:
        draw.text((x, 3), lump, fill=INK, font=font)
        sheet.paste(im.resize((im.width * ZOOM, im.height * ZOOM), Image.Resampling.NEAREST), (x, LABEL_H))
        x += im.width * ZOOM + GAP
    sheet.save(CONTACT_OUT)
    sheet.resize((width // 2, height // 2), Image.Resampling.LANCZOS).save(HALF_OUT)
    print(f"wrote {CONTACT_OUT} ({width}x{height}) and {HALF_OUT}")


if __name__ == "__main__":
    main()
