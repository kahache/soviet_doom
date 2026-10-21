#!/usr/bin/env python3
"""Soviet Doom - the mouse pointer: a hammer and sickle (D102, v1.1).

NOT the menu selector. `tools/art/gen_cursor.py` (T12, D48) draws the
blinking list cursor M_SKULL1/M_SKULL2 that Doom's menus put next to the
current row. This file draws the OPERATING-SYSTEM pointer that GZDoom shows
over its window while a menu is open and the mouse is free: the picture
GameInfo's `CursorPic` names (MOD-SPEC 6.6.1).

What the engine does with it (gzdoom g4.14.2 source, read 2026-10-21)
--------------------------------------------------------------------
* `src/d_main.cpp`, CUSTOM_CVAR vid_cursor (default "None"): with "None",
  `I_SetCursor(TexMan.GetGameTextureByName(gameinfo.CursorPic))`; if that
  fails, the engine's own "cursor" graphic. A player who picked another
  cursor in Options > Mouse keeps it.
* Stock value: `cursorpic = "doomcurs"` (gzdoom.pk3 mapinfo/doomcommon.txt);
  game_support.pk3 replaces `graphics/doomcurs.png` with a 22x32 clawed
  hand, grAb (0, 2): the "rabbit or monster" the CEO saw (D102).
* Windows (`src/common/platform/win32/i_system.cpp`, I_SetCursor): refuses a
  picture wider or taller than 32 ("Must be no larger than 32x32") and takes
  the HOT SPOT from the picture's offsets, `GetTexelLeftOffset()` /
  `GetTexelTopOffset()`, i.e. the PNG's grAb chunk, as (x, y) from the
  top-left corner (CreateBitmapCursor(leftofs * scale, topofs * scale, ...)).
  Alpha is kept (CreateAlphaCursor); the picture is scaled by an integer
  factor on high-DPI screens.
* macOS (`posix/cocoa/i_video.mm`, `hotSpot:NSMakePoint(0.0f, 0.0f)`) and
  Linux/SDL (`posix/sdl/i_gui.cpp`, `SDL_CreateColorCursor(surface, 0, 0)`)
  IGNORE the offsets: the hot spot is always the picture's (0, 0).

So the pointer is at most 32x32 with hard alpha, and the point that clicks
is the sickle's tip: the grAb says so on Windows. The tip is a pixel of the
picture's second row (the first is its contour), so on macOS/Linux the click
lands 1 px higher and some 12 px to the left of it. A sickle's point lies on
the blade's circle, never on the corner of its bounding box, so no upright
emblem can put it at (0, 0); GZDoom's own Heretic pointer (herecurs, grAb
4,4) is off the same way on those systems. Tilting the emblem to bring the
tip nearer the corner was tried and read worse at this size (2026-10-21).

The drawing
-----------
The emblem is the approved geometry of SDSTAR1 v5 (the CEO's measurements of
the canonical emblem, D48's cursor B), IMPORTED from gen_soviet_base - never
re-traced - and drawn upright, as on the flag: hammer on top of sickle.
Each tool is a polygon list in unit coordinates, rasterised at
SUPERSAMPLE x and cut to hard alpha at half coverage, then:

  gold body (hazard_yellow), a lighter hammer so the two tools separate,
  a 1 px darker gold on every lower-right edge, and a 1 px dark flag-red
  contour around each tool (the menu selector's contour colour), so the
  hammer's contour also cuts it out of the sickle. The gold reads on the
  dark menu, the contour on a white dialog. A second, near-black outer ring
  was tried and closed the crescent's hole at this size.

No font, no text, no noise: the same pixels on every machine.

Outputs (nothing here writes to assets/ unless --install is given)
------------------------------------------------------------------
  work/art/preview/cursor_SDCURSOR.png   the lump, RGBA + grAb (the source
                                         tests/test_art.py compares against)
  work/art/preview/cursor_preview.png    x8 on light and dark, plus 1x/2x
                                         on the two backgrounds, hot spot marked
  --install  copies the lump to assets/graphics/shell/SDCURSOR.png

Usage
-----
    .venv/Scripts/python.exe tools/art/gen_mouse_cursor.py             # work/ only
    .venv/Scripts/python.exe tools/art/gen_mouse_cursor.py --install   # + assets/
"""
from __future__ import annotations

import argparse
import io
import math
import struct
import sys
import zlib
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import palette  # noqa: E402  (reads docs/art/palette.json)

LUMP = "SDCURSOR"                     # MAPINFO GameInfo CursorPic
OUT_DIR = PROJECT_ROOT / "work" / "art" / "preview"
WORK_LUMP = OUT_DIR / f"cursor_{LUMP}.png"
PREVIEW = OUT_DIR / "cursor_preview.png"
ASSET = PROJECT_ROOT / "assets" / "graphics" / "shell" / f"{LUMP}.png"

# ------------------------------------------------------------- engine facts
MAX_SIZE = 32                         # win32 I_SetCursor: "no larger than 32x32"

# ------------------------------------------------------------------ drawing
EMBLEM_PX = 28                        # the emblem's unit square, in pixels (-> 28x25)
SUPERSAMPLE = 16
COVERAGE_CUT = 0.5                    # half a pixel covered -> opaque
ARC_STEPS = 64

_GOLD = palette.ramp_colours("hazard_yellow")
_RED = palette.ramp_colours("flag_red")
SICKLE_FILL = _GOLD[12]               # (223, 185, 35)
HAMMER_FILL = _GOLD[15]               # (250, 208, 40), lighter: the tool on top
SHADE = _GOLD[9]                      # (192, 160, 30), lower-right edge of both tools
CONTOUR = _RED[3]                     # (97, 22, 19), as M_SKULL1's contour

PREVIEW_ZOOM = 8
PREVIEW_LIGHT = (232, 232, 228)       # a white dialog
PREVIEW_DARK = (24, 24, 26)           # the dimmed menu
HOTSPOT_MARK = (0, 200, 255)


# --------------------------------------------------------------- geometry
def _geometry():
    """The emblem as two polygon lists in unit coordinates (y down)."""
    import gen_soviet_base as g   # constants only; it writes nothing on import

    def arc(c, r, a0, a1):
        return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / ARC_STEPS)),
                 c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / ARC_STEPS)))
                for i in range(ARC_STEPS + 1)]

    def bar(p0, p1, w):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n * w / 2, dx / n * w / 2
        return [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
                (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]

    outer = arc(g.SICKLE_OUTER_C, g.SICKLE_OUTER_R, g.SICKLE_TIP_OUTER_DEG, g.SICKLE_BASE_DEG)
    inner = arc(g.SICKLE_INNER_C, g.SICKLE_INNER_R, g.SICKLE_TIP_INNER_DEG, g.SICKLE_BASE_DEG)
    sickle = [[tuple(g.SICKLE_TIP)] + outer + inner[::-1],
              bar(*g.SICKLE_HANDLE, g.SICKLE_HANDLE_W)]

    hs, he = g.HAMMER_HANDLE
    dx, dy = he[0] - hs[0], he[1] - hs[1]
    n = math.hypot(dx, dy)
    hd = (dx / n, dy / n)                 # along the handle
    hn = (-hd[1], hd[0])                  # across it: the head's long axis
    c, hl, hw = g.HAMMER_HEAD_C, g.HAMMER_HEAD_L / 2, g.HAMMER_HEAD_W / 2
    head = [(c[0] + sa * hn[0] * hl + sb * hd[0] * hw, c[1] + sa * hn[1] * hl + sb * hd[1] * hw)
            for sa, sb in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    hammer = [bar(hs, he, g.HAMMER_HANDLE_W), head]
    return sickle, hammer, tuple(g.SICKLE_TIP)


def _mask(polys, size: int) -> set[tuple[int, int]]:
    """Pixels at least COVERAGE_CUT covered by the polygons (unit coords)."""
    from PIL import Image, ImageDraw
    big = size * SUPERSAMPLE
    im = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([(x * big, y * big) for x, y in poly], fill=255)
    small = im.resize((size, size), Image.Resampling.BOX)
    cut = round(255 * COVERAGE_CUT)
    return {(x, y) for y in range(size) for x in range(size) if small.getpixel((x, y)) >= cut}


def _ring(mask: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """The 8-connected 1 px ring just outside a mask."""
    return {(x + dx, y + dy) for x, y in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - mask


def compose():
    """-> (pixels {(x, y): rgb}, width, height, hotspot (x, y))."""
    sickle_polys, hammer_polys, tip = _geometry()
    sickle = _mask(sickle_polys, EMBLEM_PX)
    hammer = _mask(hammer_polys, EMBLEM_PX)

    px: dict[tuple[int, int], tuple[int, int, int]] = {}

    def paint(group, fill):
        for p in _ring(group):
            px[p] = CONTOUR
        for x, y in group:
            px[(x, y)] = SHADE if (x + 1, y + 1) not in group else fill

    paint(sickle, SICKLE_FILL)
    paint(hammer, HAMMER_FILL)          # on top: its contour cuts it out of the sickle

    # The hot spot: the sickle pixel nearest the blade's tip.
    tx, ty = tip[0] * EMBLEM_PX, tip[1] * EMBLEM_PX
    hot = min(sickle - hammer, key=lambda p: ((p[0] + 0.5 - tx) ** 2 + (p[1] + 0.5 - ty) ** 2, p))

    # Crop to the drawing (contour included).
    x0 = min(x for x, _ in px)
    y0 = min(y for _, y in px)
    w = max(x for x, _ in px) - x0 + 1
    h = max(y for _, y in px) - y0 + 1
    out = {(x - x0, y - y0): c for (x, y), c in px.items()}
    return out, w, h, (hot[0] - x0, hot[1] - y0)


def render():
    """-> (PIL RGBA image, hotspot)."""
    from PIL import Image
    px, w, h, hot = compose()
    if w > MAX_SIZE or h > MAX_SIZE:
        raise ValueError(f"cursor {w}x{h} exceeds the engine's {MAX_SIZE}x{MAX_SIZE}")
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        img.putpixel((x, y), c + (255,))
    return img, hot


def png_with_grab(img, grab: tuple[int, int]) -> bytes:
    """PNG bytes with a grAb chunk (the offsets GZDoom reads) after IHDR."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    body = b"grAb" + struct.pack(">ii", *grab)
    chunk = struct.pack(">I", 8) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    return data[:33] + chunk + data[33:]


def preview(img, hot):
    """x8 on light and dark (hot spot outlined), then 1x and 2x samples."""
    from PIL import Image, ImageDraw
    z, pad = PREVIEW_ZOOM, 16
    w, h = img.size
    big = img.resize((w * z, h * z), Image.Resampling.NEAREST)
    cell_w, cell_h = w * z + 2 * pad, h * z + 2 * pad
    small_h = h * 2 + 2 * pad
    sheet = Image.new("RGBA", (2 * cell_w, cell_h + small_h), PREVIEW_LIGHT + (255,))
    d = ImageDraw.Draw(sheet)
    for i, bg in enumerate((PREVIEW_LIGHT, PREVIEW_DARK)):
        x = i * cell_w
        d.rectangle((x, 0, x + cell_w - 1, cell_h + small_h - 1), fill=bg + (255,))
        sheet.alpha_composite(big, (x + pad, pad))
        hx, hy = x + pad + hot[0] * z, pad + hot[1] * z
        d.rectangle((hx - 1, hy - 1, hx + z, hy + z), outline=HOTSPOT_MARK + (255,), width=1)
        sheet.alpha_composite(img, (x + pad, cell_h + pad))
        sheet.alpha_composite(img.resize((w * 2, h * 2), Image.Resampling.NEAREST),
                              (x + pad + w + pad, cell_h + pad))
    return sheet


def build(out_dir: Path = OUT_DIR) -> dict:
    img, hot = render()
    out_dir.mkdir(parents=True, exist_ok=True)
    lump = out_dir / WORK_LUMP.name
    lump.write_bytes(png_with_grab(img, hot))
    prev = out_dir / PREVIEW.name
    preview(img, hot).save(prev)
    return {"lump": lump, "preview": prev, "size": img.size, "hotspot": hot}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--install", action="store_true",
                    help=f"also copy the lump to {ASSET.relative_to(PROJECT_ROOT).as_posix()}")
    args = ap.parse_args(argv)
    info = build(args.out)
    print(f"{LUMP}: {info['size'][0]}x{info['size'][1]}, hot spot {info['hotspot']} -> {info['lump']}")
    print(f"preview -> {info['preview']}")
    if args.install:
        ASSET.parent.mkdir(parents=True, exist_ok=True)
        ASSET.write_bytes(info["lump"].read_bytes())
        print(f"installed -> {ASSET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
