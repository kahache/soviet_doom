#!/usr/bin/env python3
"""Soviet Doom V3 B3 - the five end-of-episode awards (ADR 013).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_medals.py             # work/ only
    .venv/Scripts/python.exe tools/art/gen_medals.py --install   # + assets/

The awards a player can receive when an episode ends (MAP03, MAP06, MAP09),
drawn by SD_StatusScreen (zscript/sd/status_screen.zs) on its awards page;
the thresholds are docs/engine/BALANCE.md section 9 and ADR 013.

  lump     award                                   ribbon (stylised)
  SDAWCOU  Medal "For Courage" (Za otvagu)         grey, blue edges
  SDAWRST  Order of the Red Star                   claret, grey centre stripe
  SDAWRBN  Order of the Red Banner                 red, white edges and centre
  SDAWPTW  Order of the Patriotic War              claret, red centre stripe
  SDAWHER  Gold Star of the Hero of the Soviet Union   red bar, gold frame

What is deliberately NOT drawn (the CEO's brief, V3): no portrait of any
real person, so no Order of Lenin (Lenin's profile); no inscription, so no
font (D27) and nothing to translate on the pictures; and no Order of Glory,
whose orange-and-black ribbon is today read as a political emblem of its
own (ADR 013 explains the swap for the Order of the Patriotic War). The
star is artlib.star_points (the approved star of SDSTAR1 and the flags).

Every award is 24x30 RGBA with hard alpha, palette v2 (mosaic_gold for the
gold, marble_red for the claret), a 1 px near-black contour, and the same
silhouette layout: a ribbon mount on top (Soviet pentagonal mount, or the
Gold Star's small rectangular bar), the decoration hanging under it.
Drawn at SUPERSAMPLE x as polygons and discs, cut to hard alpha, snapped to
the palette: deterministic, the same bytes on every machine.

Outputs: work/art/v3_medals/<LUMP>.png; with --install also
assets/graphics/medals/<LUMP>.png (proposal: the CEO sees the preview first,
these are political symbols - D113's standing approval does not cover them).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import palette  # noqa: E402
import v3lib  # noqa: E402

OUT_DIR = PROJECT_ROOT / "work" / "art" / "v3_medals"
ASSET_DIR = PROJECT_ROOT / "assets" / "graphics" / "medals"

WIDTH, HEIGHT = 24, 30
SUPERSAMPLE = 8
CX = WIDTH / 2                       # every award hangs on the centre line

# --------------------------------------------------------------- colours
_GOLD = palette.ramp_colours("mosaic_gold")
_RED = palette.ramp_colours("flag_red")
_CLARET = palette.ramp_colours("marble_red")
_SILVER = palette.ramp_colours("concrete_cold")
_BLUE = palette.ramp_colours("mosaic_cobalt")
_CREAM = palette.ramp_colours("cream_yellow")

CONTOUR = _SILVER[0]                 # (10, 11, 14): the near-black outline
GOLD_LIGHT, GOLD, GOLD_DARK = _GOLD[15], _GOLD[12], _GOLD[8]
RED_LIGHT, RED, RED_DARK = _RED[14], _RED[11], _RED[6]
SILVER_LIGHT, SILVER, SILVER_DARK = _SILVER[30], _SILVER[24], _SILVER[14]
CLARET = _CLARET[4]
RIBBON_GREY = _SILVER[20]
RIBBON_BLUE = _BLUE[9]
WHITE_ENAMEL = _CREAM[15]
STEEL = _SILVER[9]
RELIEF = _SILVER[5]                  # the dark relief on a silver medal

# ------------------------------------------------------------- geometry
# Pentagonal mount (pyatiugolnaya kolodka): flat top, straight sides, two
# sloped edges meeting at the point the award hangs from.
MOUNT = ((5, 1), (19, 1), (19, 8), (12, 12), (5, 8))
MOUNT_X0, MOUNT_X1 = 5, 19
LINK = (12, 13, 1.6)                 # the suspension ring: centre and radius
BODY = (12, 21, 7.5)                 # a round medal's centre and radius
STAR_C, STAR_R = (12, 20), 9.6       # an order's star
INNER_RATIO = 0.42                   # star inner radius / outer (a fat, cast star)


class Canvas:
    """RGBA drawing at SUPERSAMPLE x; coordinates in sprite pixels."""

    def __init__(self):
        from PIL import Image, ImageDraw
        self.img = Image.new("RGBA", (WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)

    def _p(self, pts):
        return [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in pts]

    def poly(self, pts, colour):
        self.draw.polygon(self._p(pts), fill=colour + (255,))

    def disc(self, cx, cy, r, colour):
        s = SUPERSAMPLE
        self.draw.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=colour + (255,))

    def line(self, pts, colour, width):
        self.draw.line(self._p(pts), fill=colour + (255,), width=max(1, int(round(width * SUPERSAMPLE))))

    def shaded_disc(self, cx, cy, r, ramp, lo, hi):
        """A disc lit from the top-left: ramp[lo] at the lower-right rim,
        ramp[hi] at the upper-left."""
        import numpy as np
        s = SUPERSAMPLE
        h, w = self.img.size[1], self.img.size[0]
        yy, xx = np.mgrid[0:h, 0:w]
        dx = (xx + 0.5) / s - cx
        dy = (yy + 0.5) / s - cy
        inside = dx * dx + dy * dy <= r * r
        t = np.clip(0.5 - (dx + dy) / (2.6 * r), 0, 1)
        idx = np.round(lo + t * (hi - lo)).astype(int)
        cols = np.array(ramp, dtype=np.uint8)[idx]
        arr = np.asarray(self.img).copy()
        arr[inside, :3] = cols[inside]
        arr[inside, 3] = 255
        from PIL import Image, ImageDraw
        self.img = Image.fromarray(arr, "RGBA")
        self.draw = ImageDraw.Draw(self.img)

    def stripes(self, x0, x1, bands):
        """Vertical ribbon stripes across the mount: bands = [(width_px, colour)]
        from left to right, scaled to fill x0..x1, clipped to the mount."""
        from PIL import Image, ImageDraw
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        total = sum(b[0] for b in bands)
        x = float(x0)
        s = SUPERSAMPLE
        for wpx, colour in bands:
            nx = x + (x1 - x0) * wpx / total
            d.rectangle([x * s, 0, nx * s, HEIGHT * s], fill=colour + (255,))
            x = nx
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).polygon(self._p(MOUNT), fill=255)
        self.img.paste(layer, (0, 0), mask)
        self.draw = ImageDraw.Draw(self.img)


def star(cx, cy, r_out, r_in=None, rot=-90.0):
    if r_in is None:
        r_in = r_out * INNER_RATIO
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def faceted_star(cv: Canvas, cx, cy, r_out, light, dark, r_in=None):
    """A cast star: each point split along its ridge, the upper-left half lit."""
    pts = star(cx, cy, r_out, r_in)
    for i in range(0, 10, 2):
        tip = pts[i]
        left, right = pts[i - 1], pts[(i + 1) % 10]
        # the half facing the light (towards the upper-left) is the lit one
        for side in (left, right):
            mx, my = (tip[0] + side[0]) / 2 - cx, (tip[1] + side[1]) / 2 - cy
            lit = (mx + my) < 0
            cv.poly([(cx, cy), tip, side], light if lit else dark)


def mount(cv: Canvas, bands):
    cv.poly(MOUNT, RIBBON_GREY)
    cv.stripes(MOUNT_X0, MOUNT_X1, bands)
    cx, cy, r = LINK
    cv.disc(cx, cy, r, SILVER)


# --------------------------------------------------------------- awards
def courage(cv: Canvas):
    """Medal "For Courage": a silver disc; three aircraft above the red
    enamel band of the inscription (left blank: no font), a tank below."""
    mount(cv, [(2, RIBBON_BLUE), (10, RIBBON_GREY), (2, RIBBON_BLUE)])
    x, y, r = BODY
    cv.shaded_disc(x, y, r, _SILVER, 16, 30)
    cv.shaded_disc(x, y, r - 1.2, _SILVER, 20, 27)
    for px in (x - 3.2, x, x + 3.2):                 # the three aircraft
        cv.poly([(px - 1.5, y - 5.4), (px + 1.5, y - 5.4), (px, y - 3.6)], RELIEF)
    cv.poly([(x - 5.2, y - 2.4), (x + 5.2, y - 2.4), (x + 5.2, y + 0.4), (x - 5.2, y + 0.4)], RED)
    cv.poly([(x - 4.6, y + 2.6), (x + 3.8, y + 2.6), (x + 4.6, y + 4.8), (x - 4.8, y + 4.8)], RELIEF)
    cv.poly([(x - 2.4, y + 1.2), (x + 1.2, y + 1.2), (x + 1.6, y + 2.8), (x - 2.6, y + 2.8)], RELIEF)
    cv.line([(x + 1.2, y + 1.8), (x + 5.0, y + 1.4)], RELIEF, 0.8)


def red_star(cv: Canvas):
    """Order of the Red Star: a red enamel star, its centre a silver disc
    (the soldier of the real order is not drawn: a red point instead)."""
    mount(cv, [(5, CLARET), (4, RIBBON_GREY), (5, CLARET)])
    (x, y), r = STAR_C, STAR_R
    faceted_star(cv, x, y, r, RED_LIGHT, RED_DARK)
    cv.disc(x, y, 3.4, SILVER_DARK)
    cv.shaded_disc(x, y, 2.8, _SILVER, 20, 30)
    cv.disc(x, y, 1.1, RED)


def red_banner(cv: Canvas):
    """Order of the Red Banner: a gold wreath round a white field, the red
    star in it, the red banner unfurled over the top."""
    mount(cv, [(2, WHITE_ENAMEL), (4, RED_DARK), (2, WHITE_ENAMEL), (4, RED_DARK), (2, WHITE_ENAMEL)])
    x, y, r = BODY
    cv.shaded_disc(x, y, r, _GOLD, 7, 15)             # the wreath
    for k in range(12):                                # leaf notches round the wreath
        a = math.radians(k * 30 + 15)
        cv.disc(x + (r - 0.7) * math.cos(a), y + (r - 0.7) * math.sin(a), 0.5, GOLD_DARK)
    cv.disc(x, y, r - 1.7, WHITE_ENAMEL)
    faceted_star(cv, x, y + 0.4, r - 2.0, RED_LIGHT, RED_DARK)
    # the banner: a red cloth on a gold staff over the wreath's top, its
    # lower edge lined in gold so it does not melt into the red ribbon
    cv.poly([(x - 5.2, y - 6.2), (x + 5.6, y - 6.2), (x + 5.6, y - 5.3), (x - 5.2, y - 5.3)], GOLD_DARK)
    cv.poly([(x - 5.2, y - 9.2), (x - 1.5, y - 9.9), (x + 2.0, y - 9.0), (x + 5.6, y - 9.7),
             (x + 5.0, y - 8.0), (x + 5.6, y - 6.3), (x - 5.2, y - 6.3)], RED_LIGHT)
    cv.line([(x - 5.6, y - 10.2), (x - 5.6, y - 4.0)], GOLD, 0.9)


def patriotic_war(cv: Canvas):
    """Order of the Patriotic War: the gold sunburst, a crossed rifle and
    sabre behind it, the red star on top, the hammer-and-sickle disc at the
    centre (a red disc with a gold point at this size)."""
    mount(cv, [(5, CLARET), (4, RED), (5, CLARET)])
    (x, y), r = STAR_C, STAR_R
    cv.line([(x - 9, y - 6), (x + 9, y + 8)], STEEL, 1.0)     # the rifle
    cv.line([(x + 9, y - 6), (x - 9, y + 8)], SILVER, 0.9)    # the sabre
    faceted_star(cv, x, y, r, GOLD_LIGHT, GOLD_DARK, r_in=r * 0.62)
    faceted_star(cv, x, y, r - 2.6, RED_LIGHT, RED_DARK)
    cv.disc(x, y, 2.3, GOLD)
    cv.disc(x, y, 1.5, RED_DARK)
    cv.disc(x, y, 0.6, GOLD_LIGHT)


def hero(cv: Canvas):
    """Gold Star of the Hero of the Soviet Union: the plain gold star on its
    small rectangular red ribbon bar with a gold frame."""
    cv.poly([(6, 1), (18, 1), (18, 7), (6, 7)], GOLD_DARK)
    cv.poly([(6.8, 1.8), (17.2, 1.8), (17.2, 6.2), (6.8, 6.2)], RED)
    cv.disc(12, 8.0, 1.2, GOLD)
    faceted_star(cv, 12, 18.5, 10.0, GOLD_LIGHT, GOLD_DARK, r_in=3.9)


AWARDS = (
    # lump,     drawer
    ("SDAWCOU", courage),
    ("SDAWRST", red_star),
    ("SDAWRBN", red_banner),
    ("SDAWPTW", patriotic_war),
    ("SDAWHER", hero),
)


def render(drawer):
    """-> RGBA PIL image, WIDTH x HEIGHT, hard alpha, palette v2, contoured."""
    import numpy as np
    from PIL import Image
    cv = Canvas()
    drawer(cv)
    img = v3lib.sprite_from_rgba(cv.img, (WIDTH, HEIGHT))
    arr = np.asarray(img).copy()
    opaque = arr[..., 3] == 255
    grown = opaque.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= np.roll(np.roll(opaque, dy, axis=0), dx, axis=1)
    ring = grown & ~opaque
    arr[ring, :3] = CONTOUR
    arr[ring, 3] = 255
    return Image.fromarray(arr, "RGBA")


def build(out_dir: Path = OUT_DIR) -> dict[str, bytes]:
    out_dir.mkdir(parents=True, exist_ok=True)
    blobs = {}
    for lump, drawer in AWARDS:
        blob = v3lib.png_bytes(render(drawer))
        (out_dir / f"{lump}.png").write_bytes(blob)
        blobs[lump] = blob
    return blobs


def install(blobs: dict[str, bytes], asset_dir: Path = ASSET_DIR) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    for lump, blob in blobs.items():
        (asset_dir / f"{lump}.png").write_bytes(blob)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--install", action="store_true", help="also copy the lumps to assets/graphics/medals/")
    args = ap.parse_args()
    blobs = build()
    print(f"wrote {len(blobs)} awards to {OUT_DIR}")
    if args.install:
        install(blobs)
        print(f"installed into {ASSET_DIR}")


if __name__ == "__main__":
    main()
