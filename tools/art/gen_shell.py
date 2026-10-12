"""Shell batch 1 — the screens the player sees before and around the game.

Run with the project venv:  .venv/bin/python tools/art/gen_shell.py

Produces three complete "kits" (A, B, C), each one a different treatment of
the same brief, so the CEO chooses a direction by looking at it:

    TITLEPIC   320x200   title screen
    INTERPIC   320x200   intermission background (sober sibling of the title)
    M_DOOM     200x64    main-menu logo, transparent

plus, per kit, a MENUMOCK_* preview image (TITLEPIC with the logo composited
where the menu draws it) which is NOT a lump: it only exists in the sheet.

Everything is written to work/art/shell/ (never assets/: only CEO-approved
art is copied there) together with a manifest and a self-contained HTML
variants sheet in English and Russian (D7).

Art rules obeyed (docs/art/ART-BIBLE.md):
  - every colour comes from docs/art/palette.json v1 (ratified 2026-10-12);
  - no soft gradients: skies are posterised into flat bands, shapes are flat
    fills with hard edges, no dithering at quantisation;
  - drawn at the final size (320x200), never drawn big and downscaled;
  - Cyrillic set in Impact (headlines) and Arial Narrow Bold (small text),
    the two fonts ratified with batch 1 (docs/art/LICENSES.md).

Three things about Doom's shell that drive these compositions:

1. **Pixel aspect.** A 320x200 full-screen graphic is displayed at 4:3, i.e.
   stretched vertically by 1.2. Circles are therefore drawn squashed
   (ASPECT) so they are round on screen. The sheet shows both the 1:1 pixels
   and the 4:3 "as in game" view.
2. **The menu lands on top of the title.** When the player opens the menu,
   M_DOOM is drawn over TITLEPIC. Instead of fighting it, each kit draws its
   name lockup inside LOCKUP_BOX and M_DOOM *is that same lockup*, generated
   by the same function with an offset, so the logo registers exactly over
   the title it covers. The register coordinates go in the manifest for
   `mod-engineer` to put in MENUDEF.
3. **The intermission draws text over INTERPIC.** The level name sits at the
   top and the kill/item/secret counters across the middle, so INTERPIC
   keeps its centre dark and empty and its incident at the edges.

Every image is 100% procedural (origin (a) in the art bible): flat fills,
posterised bands and vector overlays quantised to the mod palette.
Rebuilding with the same seed gives the same bytes.
"""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    FONT_POSTER, FONT_SMALL, Overlay, fbm, grain, palette_image, quantize,
    ramp_colour, shade, star_points,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "shell"
MANIFEST = OUT_DIR / "manifest.json"
SCRIPT_REL = "tools/art/gen_shell.py"

BATCH_SEED = 1977  # the year of the invasion (D8), as in batch 1

# ---------------------------------------------------------------- geometry
SCREEN_W, SCREEN_H = 320, 200
LOGO_W, LOGO_H = 200, 64          # M_DOOM; 64 instead of 60 keeps it on the
                                  # 8-px grid the rest of the art uses
# Where the name lockup lives on every TITLEPIC, and therefore where M_DOOM
# is cropped from: centred horizontally, hard against the top, clear of the
# menu items (classic Doom draws them from y~72 down).
LOCKUP_X0 = (SCREEN_W - LOGO_W) // 2     # 60
LOCKUP_Y0 = 0

# Doom displays 320x200 at 4:3, i.e. 1.2x vertical stretch. Circles are drawn
# this much flatter so they come out round.
ASPECT = 1.2

# Area the intermission writes over (level name on top, counters across the
# middle). Nothing bright goes here. Shown as a guide in the HTML sheet.
INTER_SAFE = (40, 38, 280, 112)
INTER_SAFE_LOW = (40, 150, 280, 186)

# ------------------------------------------------------------------ colour
RED_GROUND = 0.74       # flag_red ramp position of a printed poster red
RED_DEEP = 0.30
CREAM = 0.92            # cream_yellow: poster paper / headline ink
GOLD = 0.88             # hazard_yellow: stars, flame, sun
PAPER_AGE = 0.07        # amplitude of the print-ageing mottle (kept low:
                        # enough to kill the vector flatness, not enough to
                        # read as noise after quantisation)

BLACK = (0, 0, 0)


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


def red(t: float) -> tuple[int, int, int]:
    return ramp_colour("flag_red", t)


def cream(t: float = CREAM) -> tuple[int, int, int]:
    return ramp_colour("cream_yellow", t)


def gold(t: float = GOLD) -> tuple[int, int, int]:
    return ramp_colour("hazard_yellow", t)


def grey(t: float) -> tuple[int, int, int]:
    return ramp_colour("concrete_cold", t)


def blue(t: float) -> tuple[int, int, int]:
    return ramp_colour("steel_blue", t)


# ------------------------------------------------------------- base fields
def solid(w: int, h: int, colour) -> np.ndarray:
    return np.tile(np.array(colour, dtype=np.uint8)[None, None, :], (h, w, 1))


def bands(w: int, h: int, stops) -> np.ndarray:
    """Posterised field from a list of (y_end, colour): flat horizontal bands
    with hard edges. This is how the skies are made — a serigraph, not a
    gradient."""
    out = np.zeros((h, w, 3), dtype=np.uint8)
    y = 0
    for y_end, colour in stops:
        out[y:y_end] = np.array(colour, dtype=np.uint8)
        y = y_end
    if y < h:
        out[y:] = np.array(stops[-1][1], dtype=np.uint8)
    return out


def age(rgb: np.ndarray, rng: np.random.Generator, amount: float = PAPER_AGE) -> np.ndarray:
    """Print ageing: slow blotches plus a whisper of grain, multiplicative."""
    h, w = rgb.shape[:2]
    f = 1 - amount * (fbm(w, h, 4, 3, rng) - 0.4) + grain(w, h, rng, amount * 0.25)
    return shade(rgb, f)


# -------------------------------------------------------- drawing helpers
def rot(points, angle_deg, cx, cy):
    """Rotate points about (cx, cy). Screen coords (y down), so a positive
    angle turns clockwise."""
    a = np.deg2rad(angle_deg)
    c, s = np.cos(a), np.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def squash(points, cy: float, k: float = ASPECT):
    """Flatten a shape vertically about cy so it looks right after Doom's
    4:3 stretch."""
    return [(x, cy + (y - cy) / k) for x, y in points]


def star_sq(cx: float, cy: float, r: float, rotation: float = -90.0):
    """Five-pointed star that is regular *on screen* (aspect compensated)."""
    return squash(star_points(cx, cy, r, rot=rotation), cy)


def disc_sq(ov: Overlay, cx: float, cy: float, r: float, fill):
    ov.ellipse(cx - r, cy - r / ASPECT, cx + r, cy + r / ASPECT, fill=fill)


def bar(p0, p1, width: float):
    """Quad of a thick bar between two points (the constructivist diagonal)."""
    p0, p1 = np.array(p0, dtype=float), np.array(p1, dtype=float)
    d = p1 - p0
    d /= np.linalg.norm(d)
    n = np.array([-d[1], d[0]]) * width / 2
    return [tuple(p0 + n), tuple(p1 + n), tuple(p1 - n), tuple(p0 - n)]


def tracked_text(ov: Overlay, cx: float, cy: float, txt: str, size: float, fill,
                 *, tracking: float = 0.0, font: str = FONT_POSTER, angle: float = 0.0,
                 max_width: float | None = None, outline=None, outline_width: float = 1.0,
                 align: str = "center") -> float:
    """Text with letter-spacing, optional rotation and optional contour.

    Pillow has no tracking and no rotated text, and `Overlay.text` has
    neither; both are needed here (Soviet poster lettering is spaced, and the
    Rodchenko treatment is built on rotated type). Drawn on its own layer at
    SUPERSAMPLE x, rotated about the anchor, then alpha-composited — the same
    path every other overlay primitive takes, so the edges land on the
    palette ramps. Returns the size actually used (texture px)."""
    s = ov.s
    px = max(6, int(round(size * s)))

    def measure(f: ImageFont.FreeTypeFont) -> float:
        return sum(f.getlength(c) for c in txt) + tracking * s * max(0, len(txt) - 1)

    f = ImageFont.truetype(font, px)
    if max_width is not None:
        while px > 6 and measure(f) > max_width * s:
            px -= 1
            f = ImageFont.truetype(font, px)
    total = measure(f)
    x = {"center": cx * s - total / 2, "left": cx * s, "right": cx * s - total}[align]

    layer = Image.new("RGBA", ov.img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for ch in txt:
        d.text((x, cy * s), ch, font=f, fill=fill, anchor="lm")
        x += f.getlength(ch) + tracking * s
    if angle:
        layer = layer.rotate(angle, resample=Image.Resampling.BICUBIC, center=(cx * s, cy * s))
    if outline is not None:
        k = max(1, int(round(outline_width * s)))
        alpha = layer.getchannel("A").filter(ImageFilter.MaxFilter(2 * k + 1))
        rim = Image.new("RGBA", ov.img.size, tuple(outline) + (255,))
        rim.putalpha(alpha)
        ov.img.alpha_composite(rim)
    ov.img.alpha_composite(layer)
    return px / s


# ===========================================================================
# Name lockups
# ===========================================================================
# Each kit answers the naming question differently; the lockup is drawn by
# one function so TITLEPIC and M_DOOM can never drift apart. Coordinates are
# TITLEPIC coordinates; (dx, dy) shifts them into the logo's own 200x64 frame
# (dx = -LOCKUP_X0). `plate` is False when drawing over the title screen if
# the title screen already provides the ground.

LOCKUP_A_LINE = "СОВЕТСКИЙ DOOM"      # hybrid: Cyrillic adjective, Latin DOOM
LOCKUP_B_LINE1, LOCKUP_B_LINE2 = "SOVIET DOOM", "СОВЕТСКИЙ ДУМ"   # bilingual
LOCKUP_C_LINE1, LOCKUP_C_LINE2 = "СОВЕТСКИЙ ДУМ", "SOVIET DOOM"   # Cyrillic-led
ERA_LINE = "ЗАРЯ-7 · 1977"
ERA_LINE_EN = "ZARYA-7 · 1977"

MASTHEAD_H = 58          # kit A: height of the black masthead band
BAR_ANGLE = 10.1         # kit C: the constructivist diagonal, degrees


def lockup_a(ov: Overlay, dx: float = 0.0, dy: float = 0.0, *, plate: bool = False) -> None:
    """Kit A — one hybrid line in a black masthead, a gold rule under it."""
    if plate:
        ov.rect(LOCKUP_X0 + dx, 0 + dy, LOCKUP_X0 + LOGO_W + dx, MASTHEAD_H + dy, fill=BLACK)
    tracked_text(ov, 160 + dx, 26 + dy, LOCKUP_A_LINE, 34, cream(),
                 tracking=1.0, max_width=186)
    ov.rect(74 + dx, 42 + dy, 246 + dx, 44 + dy, fill=gold(0.80))
    tracked_text(ov, 160 + dx, 51 + dy, ERA_LINE, 10, cream(0.70),
                 tracking=2.2, font=FONT_SMALL, max_width=160)


def lockup_b(ov: Overlay, dx: float = 0.0, dy: float = 0.0, *, plate: bool = False) -> None:
    """Kit B — bilingual stack, Latin dominant, contour so it survives on a
    sky that changes value behind it."""
    if plate:
        pass  # kit B's lockup is pure outlined type: no plate, no box
    tracked_text(ov, 160 + dx, 26 + dy, LOCKUP_B_LINE1, 36, cream(),
                 tracking=2.0, max_width=186, outline=BLACK, outline_width=1.5)
    tracked_text(ov, 160 + dx, 50 + dy, LOCKUP_B_LINE2, 14, gold(0.85),
                 tracking=3.0, max_width=176, outline=BLACK, outline_width=1.0)


def lockup_c(ov: Overlay, dx: float = 0.0, dy: float = 0.0, *, plate: bool = False) -> None:
    """Kit C — Cyrillic first, set on the diagonal black bar.

    Both lines stay *inside* the bar: outside it the ground is cream and a
    gold secondary line simply disappears (that is exactly what the first
    version did)."""
    if plate:
        ov.polygon([(x + dx, y + dy) for x, y in bar(C_BAR_P0, C_BAR_P1, C_BAR_W)], BLACK)
    tracked_text(ov, 160 + dx, 27 + dy, LOCKUP_C_LINE1, 26, cream(),
                 tracking=1.5, angle=BAR_ANGLE, max_width=168)
    tracked_text(ov, 160 + dx, 46 + dy, LOCKUP_C_LINE2, 10, gold(0.85),
                 tracking=4.0, angle=BAR_ANGLE, max_width=150)


# ===========================================================================
# Kit A — "Plakat": propaganda poster, rocket and star
# ===========================================================================
RAY_COUNT = 7
RAY_PIVOT = (26, 172)
RAY_LEN = 430
ROCKET_C = (196, 102)
ROCKET_K = 2.2            # scale of the rocket profile from SDPOSTR2
ROCKET_ANGLE = -45.0

# The rocket profile is the one approved on SDPOSTR2 (the cosmonautics
# mural), scaled up: the title screen and the mural must read as the same
# poster campaign.
ROCKET_BODY = [(-30, -5), (18, -5), (30, 0), (18, 5), (-30, 5)]
ROCKET_FIN_T = [(-30, -5), (-22, -5), (-16, -12), (-30, -12)]
ROCKET_FIN_B = [(-30, 5), (-22, 5), (-16, 12), (-30, 12)]
ROCKET_FLAME = [(-30, -3), (-48, 0), (-30, 3)]
ROCKET_FLAME_IN = [(-30, -2), (-40, 0), (-30, 2)]


def rocket(ov: Overlay, cx: float, cy: float, k: float, angle: float) -> None:
    def P(pts):
        return rot([(x * k, y * k) for x, y in pts], angle, cx, cy)
    ov.polygon(P(ROCKET_FLAME), gold())
    ov.polygon(P(ROCKET_FLAME_IN), cream())
    ov.polygon(P(ROCKET_FIN_T), BLACK)
    ov.polygon(P(ROCKET_FIN_B), BLACK)
    ov.polygon(P(ROCKET_BODY), cream())
    # shadow side: the half of the body away from the light, flat black at
    # 35 % — one extra tone, not a gradient
    ov.polygon(P([(-30, 0), (18, 0), (30, 0), (18, 5), (-30, 5)]), BLACK + (90,))
    ov.polygon(P([(18, -5), (30, 0), (18, 0)]), BLACK)


def titlepic_a() -> np.ndarray:
    rng = rng_for(1)
    rgb = age(solid(SCREEN_W, SCREEN_H, red(RED_GROUND)), rng)
    ov = Overlay(SCREEN_W, SCREEN_H)
    # rays from the lower left: cream at low alpha = one flat intermediate
    for k in range(RAY_COUNT):
        a = -6 - k * 12.5
        ov.polygon(rot([(0, 0), (RAY_LEN, -4), (RAY_LEN, 4)], a, *RAY_PIVOT),
                   cream() + (70,))
    rocket(ov, *ROCKET_C, ROCKET_K, ROCKET_ANGLE)
    ov.polygon(star_sq(268, 150, 26), gold())
    # masthead and bottom rule
    ov.polygon([(0, 0), (SCREEN_W, 0), (SCREEN_W, MASTHEAD_H - 8), (0, MASTHEAD_H)], BLACK)
    lockup_a(ov)
    ov.rect(0, 184, SCREEN_W, SCREEN_H, fill=BLACK)
    tracked_text(ov, 10, 192, "ЗАРЯ-7 · КОСМОДРОМ · 1977", 10, cream(0.70),
                 tracking=2.0, font=FONT_SMALL, align="left")
    tracked_text(ov, 310, 192, ERA_LINE_EN, 10, cream(0.45),
                 tracking=2.0, font=FONT_SMALL, align="right")
    return ov.composite(rgb)


def interpic_a() -> np.ndarray:
    """Same poster, lights down: the rays survive as a dark red watermark so
    the intermission belongs to the title, and the centre stays empty."""
    rng = rng_for(2)
    rgb = age(solid(SCREEN_W, SCREEN_H, red(0.22)), rng, 0.05)
    ov = Overlay(SCREEN_W, SCREEN_H)
    for k in range(RAY_COUNT):
        a = -6 - k * 12.5
        ov.polygon(rot([(0, 0), (RAY_LEN, -4), (RAY_LEN, 4)], a, *RAY_PIVOT),
                   red(0.40) + (170,))
    ov.polygon(star_sq(292, 178, 13), gold(0.45))
    ov.rect(0, 0, SCREEN_W, 4, fill=BLACK)
    ov.rect(0, 192, SCREEN_W, SCREEN_H, fill=BLACK)
    tracked_text(ov, 10, 186, ERA_LINE, 10, cream(0.55),
                 tracking=2.0, font=FONT_SMALL, align="left")
    return ov.composite(rgb)


# ===========================================================================
# Kit B — "Zarya-7": the cosmodrome in silhouette against a red sky
# ===========================================================================
HORIZON = 128
SKY_STOPS = [(30, 0.18), (52, 0.26), (72, 0.36), (90, 0.46), (106, 0.56), (118, 0.66)]
SUN_C, SUN_R = (216, HORIZON), 34


def ellipse_pts(cx: float, cy: float, rx: float, ry: float, n: int = 40):
    return [(cx + rx * np.cos(2 * np.pi * i / n), cy + ry * np.sin(2 * np.pi * i / n))
            for i in range(n)]


def skyline(ov: Overlay, horizon: float, ink, scale: float = 1.0,
            beacon=None, lit=None) -> None:
    """The Zarya-7 skyline as flat silhouette: hangar, dish, pylons, gantry
    with a rocket on the pad, blockhouse. Everything one ink colour — the
    shape has to carry it, which is also rule §6.4 of the art bible applied
    to architecture. The pad sits right of x=260 so it never fouls the name
    lockup. `lit` is the colour of the windows: a black block with a row of
    lit windows reads as a building, the same block without them reads as a
    hill (which is what the first version did)."""
    def y(dy: float) -> float:
        return horizon - dy * scale

    # hangar: block with a shallow barrel roof (rise 10, not a dome), roof
    # vents on the right half, a row of lit windows along the wall
    ov.rect(4, y(18), 104, horizon, fill=ink)
    ov.ellipse(4, y(28), 104, y(8), fill=ink)
    for sx in (74, 86):
        ov.rect(sx, y(32), sx + 5, y(20), fill=ink)
    if lit is not None:
        for wx in range(14, 96, 14):
            ov.rect(wx, y(12), wx + 6, y(8), fill=lit)
    # parabolic dish on a mast, tilted up to the right so it is a dish and
    # not a street lamp
    ov.rect(124, y(26), 129, horizon, fill=ink)
    ov.polygon(squash(rot([(x - 128, yy - y(32)) for x, yy in
                           ellipse_pts(128, y(32), 16, 7)], -32, 128, y(32)), y(32)), ink)
    ov.rect(132, y(38), 135, y(30), fill=ink)   # feed arm at the focus
    # two power pylons
    for px in (152, 178):
        ov.rect(px, y(42), px + 3, horizon, fill=ink)
        for ay in (30, 38):
            ov.rect(px - 8, y(ay) - 2, px + 11, y(ay), fill=ink)
    # launch gantry: two legs, cross bracing, service arms
    for lx in (252, 284):
        ov.rect(lx, y(82), lx + 5, horizon, fill=ink)
    for ay in range(10, 86, 14):
        ov.rect(252, y(ay) - 2, 289, y(ay), fill=ink)
    # rocket on the pad between the legs
    ov.rect(264, y(72), 278, horizon, fill=ink)
    ov.polygon([(264, y(72)), (278, y(72)), (271, y(90))], ink)
    ov.polygon([(258, horizon), (264, y(16)), (264, horizon)], ink)
    ov.polygon([(284, horizon), (278, y(16)), (278, horizon)], ink)
    # blockhouse, right edge
    ov.rect(298, y(12), SCREEN_W, horizon, fill=ink)
    if lit is not None:
        for wx in (302, 311):
            ov.rect(wx, y(8), wx + 5, y(5), fill=lit)
    if beacon is not None:
        ov.rect(285, y(84), 288, y(81), fill=beacon)


def titlepic_b() -> np.ndarray:
    stops = [(y, red(t)) for y, t in SKY_STOPS]
    stops.append((HORIZON, ramp_colour("hazard_yellow", 0.45)))
    stops.append((SCREEN_H, red(0.08)))
    rgb = bands(SCREEN_W, SCREEN_H, stops)
    ov = Overlay(SCREEN_W, SCREEN_H)
    disc_sq(ov, *SUN_C, SUN_R, gold(0.80))
    ov.rect(0, HORIZON, SCREEN_W, SCREEN_H, fill=red(0.08))
    skyline(ov, HORIZON, BLACK, beacon=red(0.95), lit=cream(0.80))
    # ground: one darker apron so the silhouettes have something to stand on
    ov.rect(0, 168, SCREEN_W, SCREEN_H, fill=red(0.05))
    ov.rect(0, 166, SCREEN_W, 168, fill=red(0.14))
    lockup_b(ov)
    tracked_text(ov, 310, 192, ERA_LINE, 10, cream(0.60),
                 tracking=2.0, font=FONT_SMALL, align="right")
    return ov.composite(rgb)


def interpic_b() -> np.ndarray:
    """Night over the same cosmodrome: the sky drops to steel blue, the
    horizon drops to 150 so the counters have empty sky to sit on."""
    horizon = 150
    rgb = bands(SCREEN_W, SCREEN_H, [
        (54, blue(0.03)), (92, blue(0.07)), (122, blue(0.10)),
        (horizon, blue(0.14)), (SCREEN_H, red(0.04)),
    ])
    ov = Overlay(SCREEN_W, SCREEN_H)
    rng = rng_for(3)
    for _ in range(26):
        sx, sy = rng.uniform(4, SCREEN_W - 4), rng.uniform(4, 96)
        ov.rect(sx, sy, sx + 1, sy + 1, fill=cream(0.50))
    ov.rect(0, horizon, SCREEN_W, SCREEN_H, fill=red(0.05))
    skyline(ov, horizon, BLACK, scale=0.80, beacon=red(0.90), lit=cream(0.72))
    return ov.composite(rgb)


# ===========================================================================
# Kit C — "Rodchenko": type, diagonals and nothing else
# ===========================================================================
C_BAR_P0, C_BAR_P1, C_BAR_W = (-20, 64), (340, 0), 44
C_RED_FIELD = [(0, SCREEN_H), (0, 118), (SCREEN_W, 58), (SCREEN_W, SCREEN_H)]
C_RULE_OFFSETS = (34, 42, 50)
C_YEAR = "1977"


def titlepic_c() -> np.ndarray:
    rng = rng_for(4)
    rgb = age(solid(SCREEN_W, SCREEN_H, cream(0.86)), rng)
    ov = Overlay(SCREEN_W, SCREEN_H)
    ov.polygon(C_RED_FIELD, red(RED_GROUND))
    # hairlines parallel to the bar, running the full width
    for off in C_RULE_OFFSETS:
        ov.polygon(bar((C_BAR_P0[0], C_BAR_P0[1] + off), (C_BAR_P1[0], C_BAR_P1[1] + off), 1.5),
                   red(0.55))
    ov.polygon(star_sq(272, 104, 27), gold())
    tracked_text(ov, 112, 150, C_YEAR, 58, BLACK, tracking=2.0, angle=BAR_ANGLE)
    tracked_text(ov, 300, 150, ERA_LINE, 11, cream(0.92),
                 tracking=3.0, angle=90, font=FONT_SMALL)
    lockup_c(ov, plate=True)
    rgb = ov.composite(rgb)
    return rgb


def interpic_c() -> np.ndarray:
    """The same geometry emptied out: two dark bars top and bottom, nothing
    in between."""
    rng = rng_for(5)
    rgb = age(solid(SCREEN_W, SCREEN_H, red(0.07)), rng, 0.05)
    ov = Overlay(SCREEN_W, SCREEN_H)
    ov.polygon(bar(C_BAR_P0, C_BAR_P1, C_BAR_W), red(0.30))
    for off in C_RULE_OFFSETS:
        ov.polygon(bar((C_BAR_P0[0], C_BAR_P0[1] + off), (C_BAR_P1[0], C_BAR_P1[1] + off), 1.5),
                   red(0.42))
    ov.polygon(bar((-20, 196), (340, 176), 26), red(0.22))
    ov.polygon(star_sq(286, 182, 12), gold(0.45))
    tracked_text(ov, 18, 36, ERA_LINE, 10, cream(0.60),
                 tracking=2.5, angle=BAR_ANGLE, font=FONT_SMALL, align="left")
    return ov.composite(rgb)


# ===========================================================================
# Menu logos (M_DOOM): the lockup alone, transparent
# ===========================================================================
def logo(lockup, plate: bool) -> Image.Image:
    """Render one lockup into a 200x64 RGBA image. Colours are snapped to the
    mod palette; alpha is hard 0/255 (Doom patches have no partial alpha, and
    a binary edge is the house style anyway)."""
    ov = Overlay(LOGO_W, LOGO_H)
    lockup(ov, dx=-LOCKUP_X0, dy=-LOCKUP_Y0, plate=plate)
    small = ov.img.resize((LOGO_W, LOGO_H), Image.Resampling.BOX)
    arr = np.asarray(small, dtype=np.uint8)
    alpha = (arr[..., 3] >= 128).astype(np.uint8) * 255
    flat = quantize(Image.fromarray(arr[..., :3], "RGB")).convert("RGB")
    out = np.dstack([np.asarray(flat, dtype=np.uint8), alpha])
    return Image.fromarray(out, "RGBA")


def menu_mock(title_rgb: np.ndarray, logo_img: Image.Image) -> Image.Image:
    """TITLEPIC with M_DOOM drawn where the menu puts it — the check that the
    logo registers on the title instead of fighting it. Preview only."""
    base = Image.fromarray(title_rgb, "RGB").convert("RGBA")
    base.alpha_composite(logo_img, (LOCKUP_X0, LOCKUP_Y0))
    return base.convert("RGB")


# ===========================================================================
# Build
# ===========================================================================
KITS = [
    {
        "key": "A", "slug": "plakat",
        "name_en": "A — Plakat", "name_ru": "А — Плакат",
        "lockup": lockup_a, "plate": True,
        "titlepic": titlepic_a, "interpic": interpic_a,
        "name_treatment_en": "Hybrid one-liner «СОВЕТСКИЙ DOOM»: Cyrillic adjective, Latin DOOM.",
        "name_treatment_ru": "Гибридная строка «СОВЕТСКИЙ DOOM»: кириллическое определение, латинское DOOM.",
        "concept_en": (
            "A printed propaganda poster. Flag red ground, a cream ray fan from the "
            "lower left, the SDPOSTR2 rocket climbing to the upper right, a gold star "
            "in the lower right, and a black masthead across the top carrying the name. "
            "It states the campaign: this is the country's own poster, printed before "
            "the invasion."),
        "concept_ru": (
            "Печатный агитплакат. Красный фон, веер кремовых лучей из нижнего левого угла, "
            "ракета из SDPOSTR2, идущая вверх вправо, золотая звезда в нижнем правом углу "
            "и чёрная шапка с названием сверху. Это собственный плакат страны, отпечатанный "
            "ещё до вторжения."),
        "inter_en": (
            "The same poster with the lights down: the ray fan survives as a dark red "
            "watermark, the centre is empty for the counters, the star shrinks into the "
            "lower right corner."),
        "inter_ru": (
            "Тот же плакат при погашенном свете: веер лучей остаётся тёмно-красным водяным "
            "знаком, центр пуст под статистику, звезда уходит в нижний правый угол."),
    },
    {
        "key": "B", "slug": "zarya",
        "name_en": "B — Zarya-7", "name_ru": "Б — Заря-7",
        "lockup": lockup_b, "plate": False,
        "titlepic": titlepic_b, "interpic": interpic_b,
        "name_treatment_en": "Bilingual stack: Latin \"SOVIET DOOM\" dominant, Cyrillic «СОВЕТСКИЙ ДУМ» under it in gold.",
        "name_treatment_ru": "Двуязычный блок: латинское «SOVIET DOOM» ведущее, кириллическое «СОВЕТСКИЙ ДУМ» под ним золотом.",
        "concept_en": (
            "The place, not the poster. A posterised red dusk in six flat bands, a gold "
            "sun half below the horizon, and the Zarya-7 skyline in pure black: hangar, "
            "dish, pylons, the gantry with a rocket still on the pad, a red beacon on top. "
            "The most cinematic of the three and the one that says 'cosmodrome' "
            "without a word."),
        "concept_ru": (
            "Место, а не плакат. Постеризованный красный закат в шесть плоских полос, "
            "золотое солнце наполовину за горизонтом и силуэт Зари-7 чистым чёрным: ангар, "
            "антенна, опоры ЛЭП, стартовая башня с ракетой на столе, красный проблесковый "
            "огонь наверху. Самый кинематографичный вариант: он произносит слово "
            "«космодром» без единой буквы."),
        "inter_en": (
            "Night over the same cosmodrome: steel-blue sky in four bands, scattered stars, "
            "the horizon dropped to y=150 so the counters sit on empty sky, the beacon "
            "still blinking."),
        "inter_ru": (
            "Ночь над тем же космодромом: стально-синее небо в четыре полосы, редкие звёзды, "
            "горизонт опущен до y=150, чтобы статистика легла на пустое небо, проблесковый "
            "огонь на месте."),
    },
    {
        "key": "C", "slug": "rodchenko",
        "name_en": "C — Rodchenko", "name_ru": "В — Родченко",
        "lockup": lockup_c, "plate": True,
        "titlepic": titlepic_c, "interpic": interpic_c,
        "name_treatment_en": "Cyrillic first: «СОВЕТСКИЙ ДУМ» large on the diagonal, \"SOVIET DOOM\" small underneath.",
        "name_treatment_ru": "Сначала кириллица: «СОВЕТСКИЙ ДУМ» крупно по диагонали, «SOVIET DOOM» мелко под ним.",
        "concept_en": (
            "Typography and nothing else. Cream paper cut by a red field on the diagonal, "
            "a black bar carrying the name at the angle of the composition, three hairlines "
            "for rhythm, a gold star as counterweight and 1977 set large in black. The most "
            "graphic and the most modern; also the cheapest to localise, since it is almost "
            "all type."),
        "concept_ru": (
            "Только типографика. Кремовая бумага, разрезанная красным полем по диагонали, "
            "чёрная плашка с названием под углом композиции, три волосяные линии для ритма, "
            "золотая звезда как противовес и крупная чёрная цифра 1977. Самый графичный и "
            "самый современный вариант; и самый дешёвый в локализации, потому что он почти "
            "весь состоит из шрифта."),
        "inter_en": (
            "The same geometry emptied: a dark red bar top, a second one bottom, three "
            "hairlines, a dim star. Nothing at all in the middle."),
        "inter_ru": (
            "Та же геометрия, опустошённая: тёмно-красная плашка сверху, вторая снизу, три "
            "волосяные линии, приглушённая звезда. В середине нет ничего."),
    },
]

SCREENS = [
    ("TITLEPIC", "titlepic", SCREEN_W, SCREEN_H,
     "Title screen (full screen, shown at 4:3)",
     "Титульный экран (во весь экран, показывается в 4:3)"),
    ("INTERPIC", "interpic", SCREEN_W, SCREEN_H,
     "Intermission background (the engine writes the level name and the counters over it)",
     "Фон межуровневого экрана (движок пишет поверх название уровня и статистику)"),
    ("M_DOOM", "logo", LOGO_W, LOGO_H,
     "Main-menu logo, transparent background",
     "Логотип главного меню, прозрачный фон"),
]


def count_colours(img: Image.Image) -> int:
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    return len({tuple(p) for p in np.asarray(rgb).reshape(-1, 3)})


def save_screen(rgb: np.ndarray, path: Path) -> Image.Image:
    img = quantize(Image.fromarray(rgb, "RGB"))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return img


def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for kit in KITS:
        k = kit["key"]
        title_rgb = kit["titlepic"]()
        inter_rgb = kit["interpic"]()
        logo_img = logo(kit["lockup"], kit["plate"])

        title_img = save_screen(title_rgb, OUT_DIR / f"TITLEPIC_{k}.png")
        inter_img = save_screen(inter_rgb, OUT_DIR / f"INTERPIC_{k}.png")
        logo_path = OUT_DIR / f"M_DOOM_{k}.png"
        logo_img.save(logo_path, optimize=True)
        mock = menu_mock(np.asarray(title_img.convert("RGB")), logo_img)
        mock.save(OUT_DIR / f"MENUMOCK_{k}.png", optimize=True)

        entry = {
            "kit": k, "slug": kit["slug"],
            "name_en": kit["name_en"], "name_ru": kit["name_ru"],
            "concept_en": kit["concept_en"], "concept_ru": kit["concept_ru"],
            "inter_en": kit["inter_en"], "inter_ru": kit["inter_ru"],
            "name_treatment_en": kit["name_treatment_en"],
            "name_treatment_ru": kit["name_treatment_ru"],
            "screens": {
                "TITLEPIC": {"file": f"TITLEPIC_{k}.png", "w": SCREEN_W, "h": SCREEN_H,
                             "colours": count_colours(title_img)},
                "INTERPIC": {"file": f"INTERPIC_{k}.png", "w": SCREEN_W, "h": SCREEN_H,
                             "colours": count_colours(inter_img)},
                "M_DOOM": {"file": f"M_DOOM_{k}.png", "w": LOGO_W, "h": LOGO_H,
                           "colours": count_colours(logo_img),
                           "menudef_x": LOCKUP_X0, "menudef_y": LOCKUP_Y0,
                           "alpha": "binary (0/255)"},
                "MENUMOCK": {"file": f"MENUMOCK_{k}.png", "w": SCREEN_W, "h": SCREEN_H,
                             "preview_only": True},
            },
        }
        out.append(entry)
        for name, d in entry["screens"].items():
            if name == "MENUMOCK":
                continue
            print(f"{k}  {name:9s} {d['w']:3d}x{d['h']:3d}  colours={d['colours']:3d}")

    manifest = {
        "batch": "shell 1", "phase": "F2", "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "palette": "docs/art/palette.json v1",
        "fonts": [FONT_POSTER, FONT_SMALL],
        "screen": [SCREEN_W, SCREEN_H], "logo": [LOGO_W, LOGO_H],
        "aspect": ASPECT, "lockup_origin": [LOCKUP_X0, LOCKUP_Y0],
        "inter_safe": [INTER_SAFE, INTER_SAFE_LOW],
        "kits": out,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"manifest: {MANIFEST}")
    return manifest


# ===========================================================================
# Variants sheet (self-contained HTML, one per language — D7)
# ===========================================================================
def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


STRINGS = {
    "en": {
        "title": "Soviet Doom — shell batch 1: title, intermission, menu logo",
        "subtitle": ("Three treatments of the same brief. Nothing here is in <code>assets/</code>: "
                     "the CEO picks a direction (or parts of several) and only then does anything ship."),
        "meta": "Phase F2 · art-director · palette v1 (162 colours, ratified 2026-10-12) · "
                "100 % procedural, seed {seed} · script <code>{script}</code>",
        "howto": "How to read this sheet",
        "howto_items": [
            "<b>1× pixels</b> is the file as it is: 320×200 real pixels, no smoothing.",
            "<b>2× nearest</b> is the same pixels doubled, to judge the drawing.",
            "<b>4:3 in game</b> is what the player sees: Doom stretches 320×200 vertically by 1.2. "
            "Circles and stars are drawn flattened so they come out round there.",
            "<b>Menu</b> shows the title screen with the menu logo composited where the engine "
            "draws it. The logo is the title's own lockup, so it registers instead of clashing.",
            "The dashed boxes on the intermission mark where the engine writes the level name "
            "and the kill/item/secret counters. Those areas are kept dark and empty on purpose.",
        ],
        "concept": "Concept",
        "name_treatment": "Name on screen",
        "lumps": "Lumps",
        "px": "1× pixels",
        "x2": "2× nearest",
        "x43": "4:3 in game",
        "menu": "Menu (logo over title)",
        "logo_on": "Logo alone (2×, on a dark ground)",
        "inter_title": "INTERPIC — intermission",
        "title_title": "TITLEPIC — title screen",
        "logo_title": "M_DOOM — menu logo",
        "decide": "What the CEO has to decide",
        "decide_items": [
            "<b>Treatment:</b> A, B or C (they can also be mixed: any lockup fits any ground).",
            "<b>The name on screen:</b> hybrid «СОВЕТСКИЙ DOOM» (A), bilingual with Latin "
            "dominant (B), or Cyrillic-led «СОВЕТСКИЙ ДУМ» with the Latin line small (C). "
            "Note that «ДУМ» is a transliteration: Russian players normally write the game's "
            "name in Latin.",
            "<b>Bilingual or not:</b> every lockup here shows both scripts. A single-script "
            "version of any of them is one line of code.",
            "Anything that is wrong but close: say what is wrong, it is redrawn from the script.",
        ],
        "origin": "Origin and licence",
        "origin_text": ("All three kits: origin (a), procedural — script <code>{script}</code>, seed {seed}, "
                        "palette <code>docs/art/palette.json</code> v1. Own work, CC BY-NC-SA 4.0 (D15). "
                        "Cyrillic set in Impact (headlines) and Arial Narrow Bold (small text), the macOS "
                        "system fonts ratified with batch 1: the fonts are never redistributed, only the "
                        "rasterised pixels ship. No asset from any commercial game."),
        "notes": "Notes for the rest of the team",
        "notes_items": [
            "<code>TITLEPIC</code>, <code>INTERPIC</code> and <code>M_DOOM</code> are names the "
            "engine fixes: they are the exception to the <code>SD</code> prefix rule, which "
            "covers our own new textures.",
            "<code>M_DOOM</code> is the only art in the project with an alpha channel (hard 0/255, "
            "no partial alpha, all colours from the palette). A menu patch needs transparency; "
            "the art bible's indexed-PNG rule is written for world textures.",
            "Placement for MENUDEF: the logo registers on the title at x={lx}, y={ly}.",
            "The engine side (MENUDEF, the TITLEPIC/INTERPIC entries in MAPINFO) belongs to "
            "<code>mod-engineer</code>; this sheet only proposes the pictures.",
        ],
    },
    "ru": {
        "title": "Soviet Doom — «оболочка», партия 1: титул, межуровневый экран, логотип меню",
        "subtitle": ("Три трактовки одного задания. Ничего из этого не лежит в <code>assets/</code>: "
                     "сначала CEO выбирает направление (или части нескольких), и только потом что-то идёт в игру."),
        "meta": "Фаза F2 · art-director · палитра v1 (162 цвета, утверждена 2026-10-12) · "
                "100 % процедурно, сид {seed} · скрипт <code>{script}</code>",
        "howto": "Как читать этот лист",
        "howto_items": [
            "<b>1× пиксели</b> — файл как есть: 320×200 реальных пикселей, без сглаживания.",
            "<b>2× nearest</b> — те же пиксели, удвоенные, чтобы судить рисунок.",
            "<b>4:3 в игре</b> — то, что видит игрок: Doom растягивает 320×200 по вертикали в 1,2 раза. "
            "Круги и звёзды нарисованы приплюснутыми, чтобы там выйти круглыми.",
            "<b>Меню</b> — титульный экран с наложенным логотипом там, где его рисует движок. "
            "Логотип — это тот же блок названия, что и на титуле, поэтому он совмещается, а не спорит.",
            "Пунктирные рамки на межуровневом экране отмечают, где движок пишет название уровня и "
            "статистику по врагам, предметам и тайникам. Эти зоны намеренно оставлены тёмными и пустыми.",
        ],
        "concept": "Идея",
        "name_treatment": "Название на экране",
        "lumps": "Лампы",
        "px": "1× пиксели",
        "x2": "2× nearest",
        "x43": "4:3 в игре",
        "menu": "Меню (логотип поверх титула)",
        "logo_on": "Логотип отдельно (2×, на тёмном фоне)",
        "inter_title": "INTERPIC — межуровневый экран",
        "title_title": "TITLEPIC — титульный экран",
        "logo_title": "M_DOOM — логотип меню",
        "decide": "Что должен решить CEO",
        "decide_items": [
            "<b>Трактовка:</b> A, B или C (их можно и смешивать: любой блок названия ложится на любой фон).",
            "<b>Название на экране:</b> гибрид «СОВЕТСКИЙ DOOM» (A), двуязычный блок с ведущей "
            "латиницей (B) или кириллица впереди «СОВЕТСКИЙ ДУМ» с мелкой латинской строкой (C). "
            "Учтите: «ДУМ» — это транслитерация, русские игроки обычно пишут название игры латиницей.",
            "<b>Двуязычно или нет:</b> все блоки здесь показывают обе письменности. Вариант с одной "
            "письменностью — это одна строка в скрипте.",
            "Если что-то не так, но близко: скажите, что именно, — перерисовывается из скрипта.",
        ],
        "origin": "Происхождение и лицензия",
        "origin_text": ("Все три комплекта: происхождение (a), процедурное — скрипт <code>{script}</code>, "
                        "сид {seed}, палитра <code>docs/art/palette.json</code> v1. Собственная работа, "
                        "CC BY-NC-SA 4.0 (D15). Кириллица набрана шрифтами Impact (заголовки) и Arial Narrow "
                        "Bold (мелкий текст), системными шрифтами macOS, утверждёнными с партией 1: шрифты не "
                        "распространяются, в игру попадают только растровые пиксели. Ни одного ассета из "
                        "коммерческих игр."),
        "notes": "Замечания для остальной команды",
        "notes_items": [
            "<code>TITLEPIC</code>, <code>INTERPIC</code> и <code>M_DOOM</code> — имена, заданные "
            "движком: это исключение из правила о префиксе <code>SD</code>, которое касается наших "
            "собственных новых текстур.",
            "<code>M_DOOM</code> — единственная графика проекта с альфа-каналом (жёсткий 0/255, без "
            "полупрозрачности, все цвета из палитры). Патчу меню нужна прозрачность; правило "
            "art bible об индексированном PNG написано для текстур мира.",
            "Размещение для MENUDEF: логотип совмещается с титулом в точке x={lx}, y={ly}.",
            "Движковая часть (MENUDEF, записи TITLEPIC/INTERPIC в MAPINFO) — зона "
            "<code>mod-engineer</code>; этот лист предлагает только картинки.",
        ],
    },
}

CSS = """
:root{--bg:#141416;--panel:#1d1d20;--ink:#e6e3dc;--dim:#9b978f;--line:#33333a;
      --accent:#d8322c;--gold:#e0b522}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:14px/1.55 "Helvetica Neue",Arial,sans-serif;padding:28px 32px 80px}
h1{font-size:23px;margin:0 0 6px;letter-spacing:.02em}
h2{font-size:19px;margin:0;letter-spacing:.02em}
h3{font-size:13px;margin:22px 0 8px;color:var(--dim);text-transform:uppercase;
   letter-spacing:.14em;font-weight:600}
a{color:var(--gold)}
code{background:#000;padding:1px 5px;border-radius:3px;font-size:12px;color:#cfcac0}
.sub{color:var(--dim);max-width:900px}
.meta{color:var(--dim);font-size:12px;margin-top:8px;border-top:1px solid var(--line);
      border-bottom:1px solid var(--line);padding:8px 0}
.howto{background:var(--panel);border-left:3px solid var(--accent);padding:12px 18px;
       margin:22px 0;max-width:1000px}
.howto ul{margin:6px 0 0;padding-left:20px}
.howto li{margin:3px 0;color:#cdc9c1}
.kit{background:var(--panel);border:1px solid var(--line);border-radius:4px;
     padding:20px 22px 24px;margin:26px 0}
.kit > header{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--line);
              padding-bottom:10px;margin-bottom:4px}
.key{background:var(--accent);color:#fff;font-weight:700;padding:2px 10px;border-radius:3px}
.concept{max-width:900px;color:#cdc9c1;margin:12px 0 0}
.treat{max-width:900px;color:var(--gold);margin:8px 0 0;font-size:13px}
.row{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start;margin-top:10px}
figure{margin:0}
figcaption{color:var(--dim);font-size:11px;margin-top:5px;letter-spacing:.06em;
           text-transform:uppercase}
.shot{image-rendering:pixelated;image-rendering:crisp-edges;background-repeat:no-repeat;
      background-size:100% 100%;border:1px solid #000;display:block;position:relative}
.x1{width:320px;height:200px}
.x2{width:640px;height:400px}
.x43{width:640px;height:480px}
.l2{width:400px;height:128px}
.checker{background-color:#2a2a2e;
         background-image:linear-gradient(45deg,#232327 25%,transparent 25%,transparent 75%,#232327 75%),
                          linear-gradient(45deg,#232327 25%,transparent 25%,transparent 75%,#232327 75%);
         background-size:16px 16px;background-position:0 0,8px 8px;padding:12px;
         display:inline-block;border:1px solid #000}
.checker .shot{background-color:transparent}
.safe{position:absolute;border:1px dashed rgba(255,255,255,.45);pointer-events:none}
.tag{color:var(--dim);font-size:11px;margin-top:4px}
ul.plain{max-width:1000px}
ul.plain li{margin:5px 0;color:#cdc9c1}
footer{color:var(--dim);font-size:12px;margin-top:34px;border-top:1px solid var(--line);
       padding-top:12px;max-width:1000px}
"""


def sheet(manifest: dict, lang: str) -> str:
    t = STRINGS[lang]
    styles, body = [], []
    for kit in manifest["kits"]:
        for name, d in kit["screens"].items():
            key = f"i-{name}-{kit['kit']}"
            styles.append(f".{key}{{background-image:url(data:image/png;base64,"
                          f"{b64(OUT_DIR / d['file'])})}}")

    sx0, sy0, sx1, sy1 = INTER_SAFE
    lx0, ly0, lx1, ly1 = INTER_SAFE_LOW

    def safe_boxes(scale: int) -> str:
        return (f'<div class="safe" style="left:{sx0*scale}px;top:{sy0*scale}px;'
                f'width:{(sx1-sx0)*scale}px;height:{(sy1-sy0)*scale}px"></div>'
                f'<div class="safe" style="left:{lx0*scale}px;top:{ly0*scale}px;'
                f'width:{(lx1-lx0)*scale}px;height:{(ly1-ly0)*scale}px"></div>')

    for kit in manifest["kits"]:
        k = kit["kit"]
        s = kit["screens"]
        body.append(f'''
<section class="kit">
  <header><span class="key">{k}</span><h2>{kit[f"name_{lang}"]}</h2></header>
  <p class="concept"><b>{t["concept"]}.</b> {kit[f"concept_{lang}"]}</p>
  <p class="treat"><b>{t["name_treatment"]}:</b> {kit[f"name_treatment_{lang}"]}</p>

  <h3>{t["title_title"]} — {s["TITLEPIC"]["w"]}×{s["TITLEPIC"]["h"]} · {s["TITLEPIC"]["colours"]} col.</h3>
  <div class="row">
    <figure><div class="shot x2 i-TITLEPIC-{k}"></div><figcaption>{t["x2"]}</figcaption></figure>
    <figure><div class="shot x43 i-TITLEPIC-{k}"></div><figcaption>{t["x43"]}</figcaption></figure>
    <figure><div class="shot x1 i-TITLEPIC-{k}"></div><figcaption>{t["px"]}</figcaption></figure>
  </div>

  <h3>{t["menu"]}</h3>
  <div class="row">
    <figure><div class="shot x2 i-MENUMOCK-{k}"></div><figcaption>{t["menu"]} — {t["x2"]}</figcaption></figure>
    <figure>
      <div class="checker"><div class="shot l2 i-M_DOOM-{k}"></div></div>
      <figcaption>{t["logo_title"]} — {s["M_DOOM"]["w"]}×{s["M_DOOM"]["h"]} · {t["logo_on"]}</figcaption>
    </figure>
  </div>

  <h3>{t["inter_title"]} — {s["INTERPIC"]["w"]}×{s["INTERPIC"]["h"]} · {s["INTERPIC"]["colours"]} col.</h3>
  <p class="concept">{kit[f"inter_{lang}"]}</p>
  <div class="row">
    <figure><div class="shot x2 i-INTERPIC-{k}">{safe_boxes(2)}</div><figcaption>{t["x2"]}</figcaption></figure>
    <figure><div class="shot x43 i-INTERPIC-{k}"></div><figcaption>{t["x43"]}</figcaption></figure>
    <figure><div class="shot x1 i-INTERPIC-{k}"></div><figcaption>{t["px"]}</figcaption></figure>
  </div>
</section>''')

    fmt = {"script": SCRIPT_REL, "seed": BATCH_SEED,
           "lx": LOCKUP_X0, "ly": LOCKUP_Y0}
    howto = "".join(f"<li>{i}</li>" for i in t["howto_items"])
    decide = "".join(f"<li>{i.format(**fmt)}</li>" for i in t["decide_items"])
    notes = "".join(f"<li>{i.format(**fmt)}</li>" for i in t["notes_items"])

    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<title>{t["title"]}</title><style>{CSS}
{chr(10).join(styles)}
</style></head><body>
<h1>{t["title"]}</h1>
<p class="sub">{t["subtitle"]}</p>
<p class="meta">{t["meta"].format(**fmt)}</p>
<div class="howto"><b>{t["howto"]}</b><ul>{howto}</ul></div>
{"".join(body)}
<h3>{t["decide"]}</h3><ul class="plain">{decide}</ul>
<h3>{t["origin"]}</h3><p class="sub">{t["origin_text"].format(**fmt)}</p>
<h3>{t["notes"]}</h3><ul class="plain">{notes}</ul>
<footer>Soviet Doom · {datetime.now():%Y-%m-%d %H:%M} · work/art/shell/ (gitignored) ·
nothing on this sheet is in <code>assets/</code>.</footer>
</body></html>
"""


def contact_sheet(manifest: dict, path: Path) -> None:
    """One flat montage of everything, for a single quick look in chat."""
    cols, pad = 3, 8
    cell_w, cell_h = SCREEN_W, SCREEN_H
    rows = 3
    img = Image.new("RGB", (cols * cell_w + (cols + 1) * pad,
                            rows * cell_h + (rows + 1) * pad), (20, 20, 22))
    for ci, kit in enumerate(manifest["kits"]):
        k = kit["kit"]
        for ri, name in enumerate(("TITLEPIC", "MENUMOCK", "INTERPIC")):
            tile = Image.open(OUT_DIR / kit["screens"][name]["file"]).convert("RGB")
            img.paste(tile, (pad + ci * (cell_w + pad), pad + ri * (cell_h + pad)))
    img.save(path)


def main() -> None:
    manifest = build()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    for lang in ("en", "ru"):
        suffix = "" if lang == "en" else "_ru"
        path = OUT_DIR / f"{stamp}_F2_shell-batch1{suffix}.html"
        path.write_text(sheet(manifest, lang), encoding="utf-8")
        print(f"sheet ({lang}): {path}")
    contact_sheet(manifest, OUT_DIR / "contact.png")
    print(f"contact: {OUT_DIR / 'contact.png'}")


if __name__ == "__main__":
    main()
