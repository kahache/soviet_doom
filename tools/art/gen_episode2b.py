"""Episode 2, round 2 (D112, P4): the textures MAP04-06 still wear as stand-ins.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode2b.py
                            (macOS: .venv/bin/python tools/art/gen_episode2b.py)

DRAFTS for the CEO. PNGs go to work/art/episode2b/<set>/ (sets sky, railway,
dam, moscow), the review sheet to
docs/art/previews/2026-10-22_P4_episode2-textures-round2.html. Nothing is
written into assets/: the approved round (D107) is only read, for the sample
rooms and as the ground of the derived pieces.

What it draws (the "still pending" tables of docs/levels/MAP04-transsib.md
§7.2, MAP05-volga-dam.md §7.2 and MAP06-red-square.md §8):
  sky      SDSKY1, the Urals at night over Sverdlovsk (MAP04); SDSKY2, Moscow
           at night under its own glow (MAP06). 1024x128: one turn of 360
           degrees, where Freedoom's SKY1 (256x128) repeats four times
  railway  wagon roof, gondola bed, the locomotive cab (backhead and side),
           signal-box glazing, the lever frame (top and front), the
           roundhouse stall doors, the station board «СВЕРДЛОВСК /
           СОРТИРОВОЧНЫЙ»
  dam      the window bars SDGRIL1 (masked), the blue key door SDDOORB, the
           high-voltage fence SDHVLT1 (masked) with its «СТОЙ!» plate
  moscow   the Spasskaya clock SDCLOK1 and ruby star SDRUBY1 (masked), the
           GUM shopfronts SDGUMS1-3 and glass roof SDGUMR1, the Historical
           Museum's brick SDMUSE1. Round 2 also drew SDFLAG3/SDFLAG4, the
           occupiers' banners on the Kremlin brick SDKREM1 (D113); since
           D119 they are Soviet flags drawn by gen_soviet_flags.py under
           the same lump names, and this script no longer builds them

Method: ep2lib's (imported, never edited): one seed per piece (BATCH_SEED +
offset), tileable numpy fields, vector overlays at SUPERSAMPLE x, no dither.
Palette v1; a piece adds a v2 ramp only where it says why (`ramps`):
marble_red for brick (D66, D107), mosaic_cobalt for the blue key door (the
cobalt mosaic SDMOSA1 frames it in MAP06). Never mosaic_gold or flesh_pink.

Lettering: never a system font (D27). Words come from our alphabet
(assets/fonts/bigfont, D24) through gen_factory.glyph_masks, each glyph
trimmed to its ink; digits are ep2lib's 3x5 pixels. Every lump therefore
reproduces byte for byte on the Mac and on Windows.

One piece replays an approved recipe on purpose, by setting gen_factory's
module state for the length of one call (`_patched`), never by editing it:
SDDOORB is gen_factory.key_door with a cobalt trim (its leaf is SDDOOR1's,
as SDDOORY's and SDDOORR's are). The sample rooms set ep2lib's
room height and v2 ramps the same way.
"""

from __future__ import annotations

import base64
import contextlib
import dataclasses
import html
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import DIMENSION_MULTIPLE, Overlay, fbm, grain, quantize, shade, star_points, tiling_seam_score, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import col, rivet, wrap_dist  # noqa: E402
import gen_episode2  # noqa: E402  (round 1's sheet CSS and the lump-name check)
import gen_factory  # noqa: E402  (our alphabet, the key door, the banners)
import gen_metro  # noqa: E402  (palette-version helpers)
import gen_moscow  # noqa: E402  (the Kremlin brick)
import palette as palgen  # noqa: E402

PROJECT_ROOT = ep2lib.PROJECT_ROOT
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "episode2b"
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode2-textures-round2.html"
SCRIPT_REL = "tools/art/gen_episode2b.py"
SMALLFONT = PROJECT_ROOT / "assets" / "fonts" / "defsmallfont"
# Own seed space: round 2 of Episode 2. Clear of round 1 (5400/5500/5600)
# and of every older generator (1935+, 1977+, 2077+, 3077+, 4100+).
BATCH_SEED = 5700
SKY_SIZE = (1024, 128)       # one 360-degree turn (GZDoom: 1024 columns per turn, NOT VERIFIED here)
SKY_W, SKY_H = SKY_SIZE
HORIZON = 100                # sky row at eye level: Doom's sky texture mid (NOT VERIFIED in GZDoom's mapping)
EXTRA_RAMPS_ALLOWED = ("marble_red", "mosaic_cobalt")
ALPHA_CUT = ep2lib.ALPHA_CUT
FLAT = 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


@dataclasses.dataclass
class Piece2(ep2lib.Piece):
    set_name: str = ""
    ramps: tuple = ()            # the v2 ramps this piece adds to v1, each with its reason in why_v2
    replays: str = ""            # the approved seeds it replays on purpose, if any
    variants: bool = False       # several lumps that are variants, not animation frames

    def __post_init__(self):
        self.palette = 2 if self.ramps else 1


# ================================================================ palette
def allowed_colours(ramps: tuple = ()) -> list[tuple[int, int, int]]:
    cols = [tuple(c) for c in palgen.colours(1)]
    for name in ramps:
        assert name in EXTRA_RAMPS_ALLOWED, name
        cols += [tuple(c) for c in palgen.ramp_colours(name)]
    return cols


def quantise_rgb(rgb: np.ndarray, ramps: tuple = ()) -> Image.Image:
    """No dither, to v1 plus the piece's own v2 ramps. A v2 piece carries
    the full v2 palette (226 entries) like every other v2 generator."""
    rgb = np.ascontiguousarray(rgb[..., :3])
    if not ramps:
        return quantize(Image.fromarray(rgb, "RGB"))
    pal = Image.new("P", (1, 1))
    pal.putpalette([v for c in allowed_colours(ramps) for v in c])
    snapped = Image.fromarray(rgb, "RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    return gen_metro.quantize_version(np.asarray(snapped), 2)


def quantise(rgb: np.ndarray, ramps: tuple = ()) -> Image.Image:
    """RGB in -> indexed out; RGBA in -> RGBA with hard alpha (ART-BIBLE §2)."""
    if rgb.shape[2] == 4:
        q = np.asarray(quantise_rgb(rgb, ramps).convert("RGB")).copy()
        alpha = np.where(rgb[..., 3] >= ALPHA_CUT, 255, 0).astype(np.uint8)
        q[alpha == 0] = 0
        return Image.fromarray(np.dstack([q, alpha]).astype(np.uint8), "RGBA")
    return quantise_rgb(rgb, ramps)


@contextlib.contextmanager
def _patched(target, **attrs):
    """Set attributes of a module for the length of a with-block, then put
    the originals back (the module's file is never touched)."""
    saved = {k: getattr(target, k) for k in attrs}
    try:
        for k, v in attrs.items():
            setattr(target, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(target, k, v)


# ================================================================ lettering
def word_masks(text: str, folder: Path = gen_factory.BIGFONT_DIR, spacing: int = 1,
               space: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """Our alphabet with each glyph trimmed to its ink and set `spacing` px
    apart: the font's own advance leaves 3 px between letters, too loose for
    a board. Returns (body, shadow) like gen_factory.glyph_masks."""
    parts = []
    for ch in text:
        if ch == " ":
            parts.append(None)
            continue
        b, s = gen_factory.glyph_masks(ch, folder)
        xs = np.flatnonzero((b | s).any(0))
        parts.append((b[:, xs[0]:xs[-1] + 1], s[:, xs[0]:xs[-1] + 1]))
    h = max(p[0].shape[0] for p in parts if p)
    width = sum(p[0].shape[1] if p else space for p in parts) + spacing * (len(parts) - 1)
    body = np.zeros((h, width), bool)
    shadow = np.zeros((h, width), bool)
    x = 0
    for p in parts:
        if p is None:
            x += space + spacing
            continue
        pb, ps = p
        body[:pb.shape[0], x:x + pb.shape[1]] |= pb
        shadow[:ps.shape[0], x:x + ps.shape[1]] |= ps
        x += pb.shape[1] + spacing
    return body, shadow


def put_word(rgb: np.ndarray, text: str, colour, cx: float, cy: float, scale: int = 1, spacing: int = 1,
             shadow_colour=None, folder: Path = gen_factory.BIGFONT_DIR) -> tuple[int, int]:
    """Paint a word centred on (cx, cy); returns its (w, h) in px."""
    body, shadow = word_masks(text, folder, spacing)
    if shadow_colour is not None:
        gen_factory.paste_mask(rgb, shadow, shadow_colour, cx, cy, scale)
    gen_factory.paste_mask(rgb, body, colour, cx, cy, scale)
    return body.shape[1] * scale, body.shape[0] * scale


def mask_of(draw, w: int, h: int) -> np.ndarray:
    """Hard mask of what `draw(ov, colour)` paints on an Overlay."""
    ov = Overlay(w, h)
    draw(ov, (255, 255, 255))
    return ov.composite(np.zeros((h, w, 3), np.uint8))[..., 0] >= ALPHA_CUT


def clip01(a):
    return np.clip(a, 0, 1)


# ================================================================ skies
URALS_ZENITH, URALS_LOW = 0.05, 0.22      # steel_blue, top of the sky and just above the hills
URALS_GLOWS = ((180, 1.0), (560, 0.80), (884, 0.55))   # (x, strength): Sverdlovsk, Uralmash, the yard's floodlights
MOON = (704, 24, 6)                        # x, y, radius: a moon behind broken cloud
CLOUD_T = 0.50                             # fbm above this: cloud
STAR_P = 0.006


def sky_coords():
    yy, xx = np.mgrid[0:SKY_H, 0:SKY_W]
    return yy.astype(float), xx.astype(float)


def ridge_row(rng, lift: float, amp: float, cells: int) -> np.ndarray:
    """A tileable skyline: the row of a ridge per column (wraps at 1024)."""
    return HORIZON - (lift + amp * fbm(SKY_W, 1, cells, 4, rng)[0])


def horizon_glow(xx, yy, glows, spread_x: float, rise: float) -> np.ndarray:
    g = np.zeros_like(xx)
    for gx, s in glows:
        g += s * np.exp(-(wrap_dist(xx - gx, SKY_W) / spread_x) ** 2) * np.exp(-(np.clip(HORIZON - yy, 0, None) / rise) ** 2)
    return clip01(g)


def lights(rgb, rng, rows: tuple[int, int], density: np.ndarray, colours, x_allowed=None) -> None:
    """Scattered window and street lights, one pixel each, denser where
    `density` (per column) is high."""
    y0, y1 = rows
    for y in range(y0, y1):
        hits = np.flatnonzero(rng.random(SKY_W) < density)
        for x in hits:
            if x_allowed is not None and not x_allowed[y, x]:
                continue
            rgb[y, x] = colours[int(rng.integers(0, len(colours)))]


def lattice_mast(rgb, x: int, top: int, base: int, red_rows) -> None:
    """A thin radio mast: 1 px dark line, red obstruction lights."""
    rgb[top:base, x % SKY_W] = col("concrete_cold", 0.08)
    for r in red_rows:
        rgb[r, x % SKY_W] = col("flag_red", 1.0)
        rgb[r, (x - 1) % SKY_W] = col("flag_red", 0.55)
        rgb[r, (x + 1) % SKY_W] = col("flag_red", 0.55)


def smoke(rgb, rng, x0: float, y0: float, length: int, glow_rgb) -> None:
    """A plume drifting east from a chimney top, lit from below by the town."""
    yy, xx = sky_coords()
    acc = np.zeros((SKY_H, SKY_W))
    for k in range(length):
        cx, cy = x0 + k * 1.7, y0 - 1 - k * 0.22 + np.sin(k * 0.35) * 0.8
        r = 1.6 + k * 0.10
        acc = np.maximum(acc, np.exp(-((wrap_dist(xx - cx, SKY_W) ** 2 + (yy - cy) ** 2) / (r * r))) * (1 - k / length))
    acc *= 0.5 + 0.5 * fbm(SKY_W, SKY_H, 64, 2, rng)
    a = clip01(acc * 0.85)[..., None]
    rgb[:] = rgb * (1 - a) + np.array(glow_rgb, float) * a


def tex_sky1() -> np.ndarray:
    """The Urals at night over Sverdlovsk (MAP04): broken cloud with a moon
    behind it and silver edges near it, a few stars in the gaps, the warm
    glow of the city and of the Uralmash works low on the clouds, the dark
    taiga ridges, chimneys and a mast with red lights, the yard's two
    floodlight towers far off."""
    rng = rng_for(1)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    sky_t = URALS_ZENITH + (URALS_LOW - URALS_ZENITH) * t ** 1.8
    glow = horizon_glow(xx, yy, URALS_GLOWS, 140.0, 36.0)
    mx, my, mr = MOON
    dmx = wrap_dist(xx - mx, w)
    halo = np.exp(-(np.hypot(dmx, yy - my) / 58.0) ** 2)
    sky_t = sky_t + (fbm(w, h, 32, 3, rng, 0.5, aspect=4.0) - 0.5) * 0.05   # breaks the gradient's bands
    c = fbm(w, h, 16, 5, rng, 0.55, aspect=2.0) + (t - 0.5) * 0.10
    cover = clip01((c - CLOUD_T) / 0.12)
    detail = fbm(w, h, 64, 3, rng, 0.5, aspect=2.0)
    edge = cover * (1 - cover) * 4
    cloud_t = 0.10 + 0.08 * t + 0.10 * glow + (detail - 0.5) * 0.07 + edge * halo * 0.45 + halo * 0.05
    field = sky_t * (1 - cover) + cloud_t * cover
    rgb = to_rgb(clip01(field), "steel_blue").astype(float)
    warm = to_rgb(clip01(0.16 + 0.26 * glow), "rust_brown").astype(float)
    a = np.clip(glow * (0.30 + 0.50 * cover), 0, 0.8)[..., None]
    rgb = rgb * (1 - a) + warm * a
    stars = (rng.random((h, w)) < STAR_P) & (cover < 0.15) & (yy < 72) & (halo < 0.45)
    bright = stars & (rng.random((h, w)) < 0.25)
    rgb[stars] = col("steel_blue", 0.78)
    rgb[bright] = col("cream_yellow", 0.96)
    moon = np.hypot(dmx, yy - my) < mr
    rgb[moon & (cover < 0.55)] = col("cream_yellow", 0.86)
    rgb[moon & (cover >= 0.55) & (cover < 0.85)] = col("steel_blue", 0.62)
    # chimney smoke before the skyline, so the stacks stand in front of it
    stacks = ((534, 60, 3), (546, 64, 3), (566, 57, 4), (588, 68, 2), (166, 70, 2), (205, 66, 3))
    for x, top, _ in stacks:
        smoke(rgb, rng, x + 1, top, 46, col("rust_brown", 0.30))
    # far range, blue-grey; near ridge, black, with conifer tips
    far = ridge_row(rng, 7, 13, 6)
    near = ridge_row(rng, 2, 7, 12) - (rng.random(w) < 0.45) * rng.integers(1, 4, w)
    far_rgb = to_rgb(clip01(0.11 + 0.08 * glow), "steel_blue").astype(float)
    rgb = np.where((yy >= far[None, :])[..., None], far_rgb, rgb)
    ground = to_rgb(clip01(0.02 + 0.05 * glow), "concrete_cold").astype(float)
    rgb = np.where((yy >= near[None, :])[..., None], ground, rgb)
    # the towns: low blocks over the near ridge where the glow is
    gcol = horizon_glow(np.arange(w, dtype=float)[None, :], np.full((1, w), float(HORIZON)), URALS_GLOWS, 140.0, 36.0)[0]
    x = 0
    while x < w:
        bw = int(rng.integers(4, 14))
        if gcol[x] > 0.45:
            bh = int(rng.integers(2, 4 + int(7 * gcol[x])))
            top = int(near[x:x + bw].min()) - bh
            rgb[top:, x:x + bw] = col("concrete_cold", 0.04)
            for yy0 in range(top + 1, HORIZON + 1, 2):
                for xx0 in range(x + 1, min(x + bw - 1, w), 2):
                    if rng.random() < 0.10:
                        rgb[yy0, xx0] = col("cream_yellow", float(rng.uniform(0.55, 0.85)))
        x += bw
    lights(rgb, rng, (HORIZON - 3, HORIZON + 9), 0.001 + 0.05 * gcol,
           (col("cream_yellow", 0.80), col("hazard_yellow", 0.70), col("cream_yellow", 0.60)),
           x_allowed=yy >= near[None, :] + 1)
    for x, top, sw in stacks:
        rgb[top:HORIZON + 2, x:x + sw] = col("concrete_cold", 0.06)
        rgb[top, x:x + sw] = col("concrete_cold", 0.20)
        for r in (top + 1, top + (HORIZON - top) // 2):
            rgb[r, x + sw // 2] = col("flag_red", 1.0)
    lattice_mast(rgb, 252, 46, HORIZON, (47, 62, 78))
    # the yard's floodlight towers, far off to the east
    for fx in (872, 897):
        rgb[66:HORIZON, fx] = col("concrete_cold", 0.10)
        rgb[63:66, fx - 2:fx + 3] = col("cream_yellow", 0.95)
        rgb[64, fx - 1:fx + 2] = (255, 255, 255)
    return np.clip(rgb, 0, 255).astype(np.uint8)


MOSCOW_SISTERS = ((150, 1.35), (472, 1.05), (812, 1.20))   # (x, scale): Stalin's high-rises on the skyline
OSTANKINO_X = 640            # the TV tower (1967), the needle of 1970s Moscow


def stalin_tower(rgb, rng, x: int, s: float) -> None:
    """A stepped Stalin high-rise: wings, tiers, a tower, a spire, a star."""
    tiers = ((38, 10), (24, 10), (15, 9), (9, 8), (5, 5))     # (width, height) from the bottom up
    base = HORIZON + 2
    for wdt, hgt in tiers:
        wdt, hgt = max(2, int(round(wdt * s))), max(2, int(round(hgt * s)))
        x0 = x - wdt // 2
        cols = [(x0 + k) % SKY_W for k in range(wdt)]
        rgb[base - hgt:base, cols] = col("concrete_cold", 0.05)
        for yy0 in range(base - hgt + 1, base - 1, 2):
            for k in range(1, wdt - 1, 2):
                if rng.random() < 0.18:
                    rgb[yy0, (x0 + k) % SKY_W] = col("cream_yellow", float(rng.uniform(0.55, 0.85)))
        base -= hgt
    spire = int(round(13 * s))
    rgb[base - spire:base, x % SKY_W] = col("concrete_cold", 0.10)
    sy = base - spire - 2
    rgb[sy:sy + 3, x % SKY_W] = col("flag_red", 0.95)
    rgb[sy + 1, (x - 1) % SKY_W] = col("flag_red", 0.70)
    rgb[sy + 1, (x + 1) % SKY_W] = col("flag_red", 0.70)


def tex_sky2() -> np.ndarray:
    """Moscow at night (MAP06): a low overcast lit orange-brown from below by
    the city's sodium light, colder and darker at the zenith; the skyline of
    blocks with lit windows, three Stalin high-rises with their stars and the
    Ostankino tower's needle with its red lights."""
    rng = rng_for(2)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    deck = fbm(w, h, 16, 5, rng, 0.55, aspect=2.5)
    warm_t = 0.10 + 0.30 * t ** 1.5 + (deck - 0.5) * 0.14
    warm = to_rgb(clip01(warm_t), "rust_brown").astype(float)
    breaks = clip01((0.42 - deck) / 0.10) * (1 - t)
    cold = to_rgb(clip01(0.07 + 0.06 * t), "steel_blue").astype(float)
    a = np.clip(0.60 * (1 - t) ** 1.6 + 0.40 * breaks, 0, 0.9)[..., None]
    rgb = warm * (1 - a) + cold * a
    band = np.exp(-(np.clip(HORIZON - yy, 0, None) / 14.0) ** 2)[..., None] * 0.35
    rgb = rgb * (1 - band) + to_rgb(clip01(0.42 + 0.06 * (deck - 0.5)), "plaster_warm").astype(float) * band
    # Ostankino first, then the city in front of its foot
    top = 12
    for y in range(top, HORIZON + 2):
        half = (y - top) / (HORIZON - top) * 2.6
        if 33 <= y <= 37:
            half = 3.5
        for dx in range(-int(np.ceil(half)), int(np.ceil(half)) + 1):
            if abs(dx) <= half:
                rgb[y, (OSTANKINO_X + dx) % w] = col("concrete_cold", 0.07 if dx > 0 else 0.11)
    for r in (top + 6, 30, 46, 62, 80):
        rgb[r, OSTANKINO_X - 1] = col("flag_red", 1.0)
        rgb[r, OSTANKINO_X + 1] = col("flag_red", 0.85)
    rgb[top - 1, OSTANKINO_X] = (255, 255, 255)
    rgb[35, OSTANKINO_X - 3:OSTANKINO_X + 4:2] = col("cream_yellow", 0.85)
    for x, s in MOSCOW_SISTERS:
        stalin_tower(rgb, rng, x, s)
    # the mass of the city: blocks of every height, lit windows
    x = 0
    while x < w:
        bw = int(rng.integers(4, 18))
        bh = int(rng.integers(1, 7)) if rng.random() > 0.18 else int(rng.integers(7, 13))
        topb = HORIZON - bh
        cols = [(x + k) % w for k in range(bw)]
        rgb[topb:, cols] = col("concrete_cold", float(rng.uniform(0.03, 0.07)))
        for yy0 in range(topb + 1, h, 2):
            p = 0.10 if yy0 < HORIZON + 8 else 0.03
            for k in range(1, bw - 1, 2):
                if rng.random() < p:
                    rgb[yy0, (x + k) % w] = col("cream_yellow", float(rng.uniform(0.50, 0.85)))
        x += bw
    # sodium streets: rows of orange dots, closer and sparser downwards
    for y, p in ((HORIZON + 6, 0.10), (HORIZON + 13, 0.07), (HORIZON + 22, 0.05)):
        hits = rng.random(w) < p
        rgb[y, hits] = col("hazard_yellow", 0.80)
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ MAP04: the yard
ROOF_RIB = 16                # transverse roof ribs every 16 px along y
ROOF_TONE = 0.44             # rust_brown: the wagons' red oxide, darker with soot
WALK = (24, 41)              # the running board along y (x span)
WALK_PLANKS = (24, 30, 35, 41)


def tex_wrof1() -> np.ndarray:
    """A goods wagon's roof from above: red-oxide steel sheets with raised
    ribs across, soot from the engines, rust along the ribs, and the wooden
    running board along y on its brackets."""
    rng = rng_for(3)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    field = ROOF_TONE + (fbm(w, h, 4, 4, rng) - 0.5) * 0.14 + grain(w, h, rng, 0.025)
    rgb = to_rgb(clip01(field), "rust_brown")
    soot = clip01(fbm(w, h, 4, 3, rng) - 0.42) * 1.5
    rgb = shade(rgb, 1 - soot * 0.55)
    ly = yy % ROOF_RIB
    f = np.ones((h, w))
    f[ly == 0] = 1.32
    f[ly == 1] = 1.12
    f[ly == 2] = 0.60
    rgb = shade(rgb, f)
    rust = (ly < 4) & (fbm(w, h, 16, 2, rng) > 0.56)
    rgb = np.where(rust[..., None], to_rgb(clip01(0.56 + grain(w, h, rng, 0.05)), "rust_brown"), rgb)
    # running board
    gr = fbm(w, h, 4, 3, rng, 0.5, aspect=6.0)
    plank = np.digitize(xx, WALK_PLANKS) - 1
    ptone = 0.40 + rng.uniform(-0.05, 0.05, len(WALK_PLANKS) + 1)
    wood = to_rgb(clip01(ptone[plank] + (gr - 0.5) * 0.18 + grain(w, h, rng, 0.02)), "plaster_warm")
    wood = shade(wood, 0.82)
    on_walk = (xx >= WALK[0]) & (xx < WALK[1])
    rgb = np.where(on_walk[..., None], wood, rgb)
    for px in WALK_PLANKS[1:-1]:
        rgb[:, px] = shade(rgb[:, px], 0.45)
    rgb[:, WALK[0]] = shade(rgb[:, WALK[0]], 1.20)
    for k, x in enumerate((WALK[1], WALK[1] + 1)):
        rgb[:, x] = shade(rgb[:, x], (0.50, 0.70)[k])
    for i, px in enumerate(WALK_PLANKS[:-1]):
        joint = (i * 21 + 7) % h            # butt joints, staggered
        rgb[joint, px + 1:WALK_PLANKS[i + 1]] = shade(rgb[joint, px + 1:WALK_PLANKS[i + 1]], 0.50)
    for y in range(0, h, ROOF_RIB):
        for px0, px1 in zip(WALK_PLANKS[:-1], WALK_PLANKS[1:]):
            rgb[y + 1, (px0 + px1) // 2] = col("concrete_cold", 0.10)
        rgb[y:y + 3, WALK[0] - 2:WALK[0]] = col("concrete_cold", 0.12)
        rgb[y:y + 3, WALK[1] + 2:WALK[1] + 4] = col("concrete_cold", 0.12)
    return rgb


HATCH = 32                   # floor hatches 32x32: a Soviet gondola's bottom doors
COAL_T = 0.55


def tex_gond1() -> np.ndarray:
    """An open wagon's bed from above: the bottom hatches (seams, two pressed
    stiffeners each, hinges at the sides), rust, coal dust and lumps of coal
    left in the corners."""
    rng = rng_for(4)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    base = 0.24 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    steel = to_rgb(clip01(base), "concrete_cold")
    rust = to_rgb(clip01(base + 0.02), "rust_brown")
    rmix = clip01((fbm(w, h, 6, 4, rng) - 0.38) * 2.2)[..., None]
    rgb = (steel * (1 - rmix) + rust * rmix).astype(np.uint8)
    lx, ly = xx % HATCH, yy % HATCH
    f = np.ones((h, w))
    for s in (9, 22):
        f[(ly == s) & (lx > 2) & (lx < HATCH - 3)] = 1.30
        f[(ly == s + 1) & (lx > 2) & (lx < HATCH - 3)] = 1.10
        f[(ly == s + 2) & (lx > 2) & (lx < HATCH - 3)] = 0.62
    f[lx == 0] = 0.30
    f[ly == 0] = 0.30
    f[lx == 1] *= 1.18
    f[ly == 1] *= 1.18
    rgb = shade(rgb, f)
    for y0 in range(0, h, HATCH):
        for x0 in range(0, w, HATCH):
            for hy in (y0 + 6, y0 + HATCH - 9):
                rgb[hy:hy + 3, x0 + 2:x0 + 4] = col("concrete_cold", 0.16)
                rgb[hy, x0 + 2:x0 + 4] = col("concrete_cold", 0.40)
    # coal: dust everywhere, lumps where it piles
    dust = clip01(fbm(w, h, 8, 3, rng) - 0.35) * 0.9
    rgb = shade(rgb, 1 - dust * 0.55)
    f1, f2, ident, ox, oy = ep2lib.cells_voronoi(w, h, 4, rng, 0.9)
    lumps = (fbm(w, h, 4, 3, rng) > COAL_T) & ((f2 - f1) > 0.6)
    tone = 0.04 + 0.10 * clip01(-oy / 2.0) + rng.uniform(0, 0.04, ident.max() + 1)[ident]
    coal = to_rgb(clip01(tone), "concrete_cold")
    glint = lumps & (oy < -1.2) & (ox < 0) & (rng.random((h, w)) < 0.35)
    rgb = np.where(lumps[..., None], coal, rgb)
    rgb[glint] = col("steel_blue", 0.55)
    return rgb


# ---------------------------------------------------------------- cab, backhead
CAB_SIDE = 10                # the cab's side walls at the tile edges
PLATE_BOX = (14, 12, 114, 120)
PLATE_R = 26                 # rounded top corners of the backhead
FIREDOOR = (44, 86, 84, 110)
GAUGES = ((64, 28, 11), (101, 32, 7))   # boiler pressure, brake
WATER_GLASSES = (27, 101)
GLASS_Y = (50, 80)
REG_HUB, REG_END = (62, 56), (106, 64)
VALVES = ((40, 70, 5), (86, 74, 4))
SPECTACLES = ((24, 16, 7), (104, 16, 7))  # the cab front's round windows either side of the boiler
TIME_GAUGE = (0.62, 0.30)    # gauge needles as a share of the scale


def gauge(ov: Overlay, cx: float, cy: float, r: float, share: float) -> None:
    ov.ellipse(cx - r - 1, cy - r, cx + r + 1, cy + r + 2, fill=col("concrete_cold", 0.04))
    ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=col("hazard_yellow", 0.62))
    ov.ellipse(cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, fill=col("hazard_yellow", 0.35))
    ov.ellipse(cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2, fill=col("plaster_warm", 0.93))
    ov.arc_ring(cx, cy, r - 2.5, r - 4.5, -20, 40, col("flag_red", 0.70))
    for k in range(9):
        a = np.deg2rad(135 + k * 33.75)
        ov.line([(cx + (r - 3) * np.cos(a), cy + (r - 3) * np.sin(a)),
                 (cx + (r - 5) * np.cos(a), cy + (r - 5) * np.sin(a))], col("concrete_cold", 0.10), 0.8)
    a = np.deg2rad(135 + share * 270)
    ov.line([(cx, cy), (cx + (r - 3) * np.cos(a), cy + (r - 3) * np.sin(a))], col("concrete_cold", 0.02), 1.2)
    ov.ellipse(cx - 1.2, cy - 1.2, cx + 1.2, cy + 1.2, fill=col("concrete_cold", 0.02))


def handwheel(ov: Overlay, cx: float, cy: float, r: float) -> None:
    ov.arc_ring(cx, cy, r, r - 1.6, 0, 360, col("flag_red", 0.55))
    ov.arc_ring(cx, cy, r, r - 0.8, 190, 300, col("flag_red", 0.85))
    for k in range(3):
        a = np.deg2rad(k * 60)
        ov.line([(cx - r * np.cos(a), cy - r * np.sin(a)), (cx + r * np.cos(a), cy + r * np.sin(a))],
                col("flag_red", 0.45), 1.0)
    ov.ellipse(cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5, fill=col("steel_blue", 0.70))


def tex_cab1() -> np.ndarray:
    """The steam locomotive's cab, looking forward: the boiler's backhead in
    black with its rivets, the firebox door glowing through its gap and air
    holes, the boiler and brake gauges in brass, two water gauge glasses, the
    regulator lever, red valve wheels on the steam pipes, the cab front's
    round windows on the night; the green cab walls at the edges."""
    rng = rng_for(5)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    cab = to_rgb(clip01(0.36 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.025)), "military_green")
    rgb = cab.copy()
    x0, y0, x1, y1 = PLATE_BOX
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    for cx in (x0 + PLATE_R, x1 - PLATE_R):
        corner = (yy < y0 + PLATE_R) & (np.abs(xx + 0.5 - cx) < PLATE_R) & ((xx < x0 + PLATE_R) if cx < 64 else (xx >= x1 - PLATE_R))
        inside &= ~(corner & (np.hypot(xx + 0.5 - cx, yy + 0.5 - (y0 + PLATE_R)) > PLATE_R))
    plate = to_rgb(clip01(0.12 + (fbm(w, h, 6, 4, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)), "concrete_cold")
    heat = np.exp(-((xx - 64) / 26.0) ** 2 - ((yy - 98) / 18.0) ** 2)
    plate = (plate * (1 - 0.35 * heat[..., None]) + to_rgb(clip01(0.30 + 0.0 * heat), "rust_brown") * 0.35 * heat[..., None]).astype(np.uint8)
    rgb = np.where(inside[..., None], plate, rgb)
    rim = inside & ~(np.roll(inside, 1, 0) & np.roll(inside, -1, 0) & np.roll(inside, 1, 1) & np.roll(inside, -1, 1))
    rgb[rim] = col("concrete_cold", 0.26)
    rgb[np.roll(rim, 1, 1) & ~inside] = col("military_green", 0.14)
    # rivets along the plate's edge
    edge_pts = np.argwhere(rim)
    for i, (y, x) in enumerate(edge_pts[::7]):
        cy, cx = y + (2 if y < 64 else -3), x + (3 if x < 64 else -4)
        if inside[min(cy, h - 1), min(cx, w - 1)]:
            rivet(rgb, int(cx), int(cy), "concrete_cold", 0.26)
    # spectacle windows onto the night, with the line's signal far ahead
    for sx, sy, r in SPECTACLES:
        d = np.hypot(xx + 0.5 - sx, yy + 0.5 - sy)
        rgb[(d < r + 2) & (d >= r)] = col("hazard_yellow", 0.40)
        glass = d < r
        rgb[glass] = to_rgb(clip01(0.10 + (sy - yy[glass]) * 0.004 + 0.02), "steel_blue")
        rgb[sy + 2, sx + 2] = col("flag_red", 0.95)
        rgb[sy - 3:sy - 1, sx - 4] = col("steel_blue", 0.45)
    # cab side walls: panel seam and rivets
    for x in (CAB_SIDE - 1, w - CAB_SIDE):
        rgb[:, x] = col("military_green", 0.14)
    for y in range(6, h, 10):
        rivet(rgb, 3, y, "military_green", 0.40)
        rivet(rgb, w - 6, y, "military_green", 0.40)
    ov = Overlay(w, h)
    # the steam pipe across, brass
    ov.rect(16, 64, 112, 67, fill=col("hazard_yellow", 0.40))
    ov.rect(16, 64, 112, 65, fill=col("hazard_yellow", 0.70))
    for px in (40, 86):
        ov.rect(px - 1, 44, px + 1, 64, fill=col("hazard_yellow", 0.45))
    for cx, cy, r in GAUGES:
        ov.rect(cx - 1, cy + r, cx + 1, 64, fill=col("hazard_yellow", 0.40))
    for (cx, cy, r), share in zip(GAUGES, TIME_GAUGE):
        gauge(ov, cx, cy, r, share)
    # water gauge glasses with brass cocks
    for gx in WATER_GLASSES:
        gy0, gy1 = GLASS_Y
        ov.rect(gx - 4, gy0 - 4, gx + 4, gy0, fill=col("hazard_yellow", 0.55))
        ov.rect(gx - 4, gy1, gx + 4, gy1 + 4, fill=col("hazard_yellow", 0.55))
        ov.rect(gx - 4, gy0 - 4, gx + 4, gy0 - 3, fill=col("hazard_yellow", 0.85))
        ov.rect(gx - 2, gy0, gx + 2, gy1, fill=col("steel_blue", 0.30))
        ov.rect(gx - 1, gy0, gx + 1, gy1, fill=col("plaster_warm", 0.85))
        lvl = gy0 + (gy1 - gy0) * 0.45
        ov.rect(gx - 1, lvl, gx + 1, gy1, fill=col("steel_blue", 0.55))
        ov.line([(gx + 3, gy0 + 4), (gx + 6, gy0 + 4)], col("flag_red", 0.70), 1.4)
    # the firebox door: butterfly leaves, the fire showing through
    fx0, fy0, fx1, fy1 = FIREDOOR
    ov.rect(fx0 - 3, fy0 - 3, fx1 + 3, fy1 + 3, fill=col("concrete_cold", 0.04))
    ov.rect(fx0 - 2, fy0 - 2, fx1 + 2, fy1 + 2, fill=col("concrete_cold", 0.30))
    ov.rect(fx0, fy0, fx1, fy1, fill=col("concrete_cold", 0.16))
    ov.rect(fx0, fy0, fx1, fy0 + 1, fill=col("concrete_cold", 0.40))
    ov.rect(63, fy0, 66, fy1, fill=col("hazard_yellow", 0.95))
    ov.rect(64, fy0 + 2, 65, fy1 - 2, fill=col("cream_yellow", 1.0))
    for k in range(3):
        for side in (-1, 1):
            hx = 64 + side * (8 + k * 6)
            ov.ellipse(hx - 1.5, 96 - 1.5, hx + 1.5, 96 + 1.5, fill=col("hazard_yellow", 0.90 - 0.1 * k))
    for hx in (fx0 + 3, fx1 - 4):
        ov.rect(hx - 1, fy0 + 6, hx + 2, fy0 + 9, fill=col("concrete_cold", 0.45))
    ov.line([(56, fy1 - 4), (72, fy1 - 4)], col("steel_blue", 0.70), 1.6)
    # regulator: hub, lever and wooden grip
    ov.line([REG_HUB, REG_END], col("steel_blue", 0.30), 3.4)
    ov.line([(REG_HUB[0], REG_HUB[1] - 1), (REG_END[0], REG_END[1] - 1)], col("steel_blue", 0.80), 1.0)
    ov.ellipse(REG_HUB[0] - 5, REG_HUB[1] - 5, REG_HUB[0] + 5, REG_HUB[1] + 5, fill=col("steel_blue", 0.40))
    ov.ellipse(REG_HUB[0] - 2, REG_HUB[1] - 3, REG_HUB[0] + 2, REG_HUB[1] + 1, fill=col("steel_blue", 0.80))
    ov.ellipse(REG_END[0] - 3, REG_END[1] - 3, REG_END[0] + 4, REG_END[1] + 4, fill=col("rust_brown", 0.40))
    ov.ellipse(REG_END[0] - 2, REG_END[1] - 2, REG_END[0] + 1, REG_END[1] + 1, fill=col("rust_brown", 0.65))
    ov.arc_ring(REG_HUB[0], REG_HUB[1], 30, 27, 0, 35, col("steel_blue", 0.45))
    for cx, cy, r in VALVES:
        handwheel(ov, cx, cy, r)
    # the maker's plate on the boiler: brass, illegible
    ov.rect(50, 74, 78, 82, fill=col("hazard_yellow", 0.55))
    ov.rect(50, 74, 78, 75, fill=col("hazard_yellow", 0.80))
    rgb = ov.composite(rgb)
    ep2lib.illegible_label(rgb, 52, 77, 24, col("hazard_yellow", 0.20), rng, rows=2)
    # firelight on the floor plate and the fireman's shovel edge
    floor = yy >= y1
    fl = to_rgb(clip01(0.22 + ((xx + yy) % 2) * 0.06 + grain(w, h, rng, 0.02)), "concrete_cold")
    glow = np.exp(-((xx - 64) / 22.0) ** 2)[..., None]
    fl = (fl * (1 - 0.5 * glow) + np.array(col("hazard_yellow", 0.50), float) * 0.5 * glow).astype(np.uint8)
    rgb = np.where(floor[..., None], fl, rgb)
    rgb[y1, :] = col("concrete_cold", 0.04)
    grime = clip01(fbm(w, h, 8, 3, rng) - 0.55) * 0.6
    return shade(rgb, 1 - grime * 0.5)


# ---------------------------------------------------------------- cab, side
SIDE_WIN = (10, 16, 54, 62)  # x0, y0, x1, y1 of the side window
SIDE_DADO = 96


def tex_cab2() -> np.ndarray:
    """The cab's side from inside: green-painted steel on riveted seams, the
    sliding side window onto the night yard (a lit signal far off, a
    reflection), the wooden armrest, a valve wheel and an enamel plate, the
    darker dado scuffed by boots."""
    rng = rng_for(6)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = 0.40 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.025)
    field = np.where(yy >= SIDE_DADO, field - 0.12, field)
    rgb = to_rgb(clip01(field), "military_green")
    f = np.ones((h, w))
    f[:, 0] = 1.10                 # the panel joint falls on the tile edge: soft, so a longer cab tiles
    f[:, w - 1] = 0.80
    f[SIDE_DADO, :] = 1.25
    f[SIDE_DADO - 1, :] = 0.55
    scuff = (yy > 112) & (fbm(w, h, 16, 2, rng) > 0.58)
    rgb = shade(rgb, f)
    rgb = np.where(scuff[..., None], to_rgb(clip01(0.34 + grain(w, h, rng, 0.05)), "steel_blue"), rgb)
    for y in range(6, h, 10):
        rivet(rgb, 2, y, "military_green", 0.42)
    for x in range(8, w - 4, 10):
        rivet(rgb, x, SIDE_DADO + 3, "military_green", 0.34)
    x0, y0, x1, y1 = SIDE_WIN
    win = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    sky = to_rgb(clip01(0.10 + (y1 - yy) * 0.002 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.04), "steel_blue")
    rgb = np.where(win[..., None], sky, rgb)
    rgb[44:y1, x0:x1] = to_rgb(clip01(np.full((y1 - 44, x1 - x0), 0.04)), "concrete_cold")
    for lx, ly, c in ((18, 42, ("cream_yellow", 0.90)), (24, 43, ("cream_yellow", 0.70)),
                      (44, 41, ("flag_red", 0.95)), (47, 43, ("military_green", 0.95))):
        rgb[ly, lx] = col(*c)
    ov = Overlay(w, h)
    ov.line([(x0 + 4, y1 - 2), (x0 + 16, y0 + 2)], col("steel_blue", 0.42) + (150,), 1.2)
    ov.line([(x0 + 9, y1 - 2), (x0 + 20, y0 + 8)], col("steel_blue", 0.36) + (110,), 0.8)
    wood = col("rust_brown", 0.36)
    ov.rect(x0 - 3, y0 - 3, x1 + 3, y0, fill=wood)
    ov.rect(x0 - 3, y1, x1 + 3, y1 + 3, fill=wood)
    ov.rect(x0 - 3, y0, x0, y1, fill=wood)
    ov.rect(x1, y0, x1 + 3, y1, fill=wood)
    ov.rect(31, y0, 33, y1, fill=wood)
    ov.rect(x0 - 3, y0 - 3, x1 + 3, y0 - 2, fill=col("rust_brown", 0.58))
    ov.rect(32, 36, 35, 41, fill=col("hazard_yellow", 0.60))
    # armrest
    ov.rect(6, y1 + 5, 58, y1 + 9, fill=col("rust_brown", 0.42))
    ov.rect(6, y1 + 5, 58, y1 + 6, fill=col("rust_brown", 0.62))
    ov.rect(6, y1 + 9, 58, y1 + 10, fill=col("military_green", 0.12))
    # enamel plate (illegible), valve and its pipe
    ov.rect(9, 78, 29, 87, fill=col("concrete_cold", 0.06))
    ov.rect(10, 79, 28, 86, fill=col("plaster_warm", 0.88))
    ov.rect(46, 84, 48, h, fill=col("hazard_yellow", 0.38))
    ov.rect(46, 84, 47, h, fill=col("hazard_yellow", 0.62))
    handwheel(ov, 47, 84, 6)
    rgb = ov.composite(rgb)
    ep2lib.illegible_label(rgb, 12, 81, 14, col("concrete_cold", 0.10), rng, rows=2)
    grime = clip01(fbm(w, h, 8, 3, rng) - 0.55) * 0.6
    return shade(rgb, 1 - grime * 0.45)


# ---------------------------------------------------------------- signal box glazing
GLASS_ROWS = (8, 56)         # the 48 rows that fill the box's openings (sills 160...208)
SASH_X = (0, 16, 32, 48)     # glazing bars (the first one is split across the tile edge)
SASH_Y = (24, 40)


def tex_sbox1() -> np.ndarray:
    """The signal box's window seen from the yard at night, lit from
    inside: white-painted glazing bars, warm light brighter under the lamp,
    the levers' silhouettes along the bottom, one cracked pane; concrete
    lintel above and sill below. Rows 8-55 are the 48-high opening."""
    rng = rng_for(7)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    g0, g1 = GLASS_ROWS
    conc = to_rgb(clip01(0.44 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)), "concrete_cold")
    rgb = conc.copy()
    lamp = np.exp(-((wrap_dist(xx - 32, w)) / 22.0) ** 2) * np.exp(-((yy - g0) / 26.0) ** 2)
    lit = 0.50 + 0.38 * lamp - 0.10 * (yy - g0) / (g1 - g0) + (fbm(w, h, 8, 2, rng) - 0.5) * 0.08
    glass = to_rgb(clip01(lit), "cream_yellow")
    dirt = clip01(fbm(w, h, 8, 3, rng) - 0.5) * 0.5
    glass = shade(glass, 1 - dirt)
    band = (yy >= g0) & (yy < g1)
    rgb = np.where(band[..., None], glass, rgb)
    # the lamp shade on its flex
    rgb[g0:g0 + 4, 32] = col("concrete_cold", 0.14)
    for k, y in enumerate(range(g0 + 4, g0 + 8)):
        rgb[y, 30 - 2 * k:35 + 2 * k] = col("concrete_cold", 0.12 + 0.03 * k)
    rgb[g0 + 8, 23:42] = col("cream_yellow", 1.0)
    rgb[g0 + 8, 29:36] = (255, 255, 255)
    # the levers' tops along the bottom of the glass
    for k, lx in enumerate(range(3, w, 6)):
        top = g1 - 9 - int(rng.integers(0, 4))
        rgb[top:g1, lx] = col("concrete_cold", 0.10)
        rgb[top:top + 2, lx:lx + 2] = col("concrete_cold", 0.06)
    rgb[g1 - 3:g1, :] = col("concrete_cold", 0.08)
    # glazing bars
    bar = col("plaster_warm", 0.72)
    bar_d = col("plaster_warm", 0.40)
    for x in SASH_X:
        for dx, c in ((-1, bar_d), (0, bar), (1, bar)):
            rgb[g0:g1, (x + dx) % w] = c
    for y in SASH_Y:
        rgb[y, :] = bar
        rgb[y + 1, :] = bar_d
    rgb[g0:g0 + 2, :] = bar
    rgb[g1 - 2:g1, :] = bar_d
    # a cracked pane, top right
    ov = Overlay(w, h)
    ov.line([(52, 12), (58, 18), (61, 15)], col("plaster_warm", 0.96), 0.8)
    ov.line([(58, 18), (55, 23)], col("plaster_warm", 0.96), 0.8)
    rgb = ov.composite(rgb)
    # lintel and sill
    rgb[g0 - 1, :] = col("concrete_cold", 0.10)
    rgb[g1, :] = col("concrete_cold", 0.70)
    rgb[g1 + 1:g1 + 3, :] = col("concrete_cold", 0.56)
    rgb[g1 + 3, :] = col("concrete_cold", 0.16)
    return rgb


# ---------------------------------------------------------------- lever frame
LEVER_PITCH = 8              # eight levers per 64 px
LEVER_COLOURS = (("flag_red", 0.66), ("flag_red", 0.66), ("concrete_cold", 0.10), ("steel_blue", 0.46),
                 ("hazard_yellow", 0.80), ("concrete_cold", 0.10), ("flag_red", 0.66), ("plaster_warm", 0.90))
REVERSED = (1, 4, 6)          # levers pulled over (the route set)
BED = (18, 40)                # the frame's cast-iron bed (y span, top view)


def tex_levr1() -> np.ndarray:
    """The mechanical lever frame from above: the cast-iron bed and its
    slots across the box's floorboards, eight levers in their paint (red
    signals, black points, blue lock, yellow distant, white spare) with
    polished handles, three pulled over, brass number plates 1-8, the boards
    worn pale where the signalman stands."""
    rng = rng_for(8)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    board = yy // 8
    bt = 0.30 + rng.uniform(-0.04, 0.04, h // 8 + 1)
    gr = fbm(w, h, 8, 3, rng, 0.5, aspect=0.2)
    wear = clip01(1 - np.abs(yy - 54) / 10.0) * 0.12
    rgb = to_rgb(clip01(bt[board] + (gr - 0.5) * 0.12 + wear + grain(w, h, rng, 0.02)), "rust_brown")
    rgb[yy % 8 == 0] = shade(rgb[yy % 8 == 0], 0.55)
    b0, b1 = BED
    iron = to_rgb(clip01(0.12 + grain(w, h, rng, 0.02) + (fbm(w, h, 8, 2, rng) - 0.5) * 0.05), "concrete_cold")
    rgb = np.where(((yy >= b0) & (yy < b1))[..., None], iron, rgb)
    rgb[b0, :] = col("concrete_cold", 0.30)
    rgb[b1 - 1, :] = col("concrete_cold", 0.04)
    rgb[b1, :] = shade(rgb[b1, :], 0.5)
    for i in range(w // LEVER_PITCH):
        cx = i * LEVER_PITCH + LEVER_PITCH // 2
        rgb[b0 + 2:b1 - 2, cx - 1:cx + 1] = col("concrete_cold", 0.02)
        ramp_name, t = LEVER_COLOURS[i]
        pulled = i in REVERSED
        y0 = b1 - 4 if pulled else b0 - 1
        y1 = y0 + 8
        body = col(ramp_name, t)
        dark = col(ramp_name, max(0.0, t - 0.25)) if ramp_name != "concrete_cold" else col("concrete_cold", 0.03)
        rgb[y0:y1, cx - 2:cx] = body
        rgb[y0:y1, cx] = dark
        hy = y1 if pulled else y0 - 3
        rgb[hy:hy + 3, cx - 2:cx + 1] = col("steel_blue", 0.80)
        rgb[hy, cx - 2] = (255, 255, 255)
        rgb[(hy + 3) if pulled else (hy - 1), cx - 1] = col("concrete_cold", 0.06)
        # number plate
        m = ep2lib.digits_mask(str(i + 1))
        px0, py0 = cx - 3, b1 + 3
        rgb[py0:py0 + 7, px0:px0 + 5] = col("hazard_yellow", 0.58)
        rgb[py0, px0:px0 + 5] = col("hazard_yellow", 0.82)
        ep2lib.stamp(rgb, m, px0 + 1, py0 + 1, col("concrete_cold", 0.04))
    return rgb


LEVER_FRAME_TOP = 42          # front view: the frame's top rail
LEVER_TOP = 6                 # a normal lever's handle top; a pulled one leans out at us


def tex_levr2() -> np.ndarray:
    """The lever frame from the front: eight levers rising from the
    cast-iron frame, painted by function, polished handles and catch
    handles, three pulled towards us (shorter, the handle larger), brass
    number plates on the frame, the box's green wall behind."""
    rng = rng_for(9)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = to_rgb(clip01(0.30 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)), "military_green")
    ft = LEVER_FRAME_TOP
    iron = to_rgb(clip01(0.14 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.05 + grain(w, h, rng, 0.02)), "concrete_cold")
    rgb = np.where((yy >= ft)[..., None], iron, rgb)
    rgb[ft, :] = col("concrete_cold", 0.40)
    rgb[ft + 1, :] = col("concrete_cold", 0.26)
    rgb[ft + 3, :] = col("concrete_cold", 0.04)
    rgb[ft - 1, :] = shade(rgb[ft - 1, :], 0.5)
    # ornamental arches between the frame's brackets
    for i in range(w // LEVER_PITCH):
        cx = i * LEVER_PITCH + LEVER_PITCH // 2
        arch = (yy >= ft + 13) & (yy < h - 2) & (np.abs(xx + 0.5 - (cx + 4)) < 3 - np.clip(ft + 16 - yy, 0, 3))
        rgb[arch] = col("concrete_cold", 0.05)
    for i in range(w // LEVER_PITCH):
        cx = i * LEVER_PITCH + LEVER_PITCH // 2
        ramp_name, t = LEVER_COLOURS[i]
        pulled = i in REVERSED
        top = LEVER_TOP + (8 if pulled else 0)
        body = col(ramp_name, t)
        hi = col(ramp_name, min(1.0, t + 0.15)) if ramp_name != "concrete_cold" else col("concrete_cold", 0.30)
        lo = col(ramp_name, max(0.0, t - 0.25)) if ramp_name != "concrete_cold" else col("concrete_cold", 0.03)
        rgb[top + 8:ft, cx - 1] = hi
        rgb[top + 8:ft, cx] = body
        rgb[top + 8:ft, cx + 1] = lo
        hw = 2 if pulled else 1
        rgb[top:top + 8, cx - hw:cx + hw + 1] = col("steel_blue", 0.72)
        rgb[top:top + 8, cx - hw] = col("steel_blue", 0.92)
        rgb[top:top + 8, cx + hw] = col("steel_blue", 0.40)
        rgb[top + 9:top + 12, cx + 2] = col("steel_blue", 0.55)       # the catch handle
        rgb[ft - 2:ft, cx - 2:cx + 3] = col("concrete_cold", 0.08)    # the quadrant
        m = ep2lib.digits_mask(str(i + 1))
        px0, py0 = cx - 3, ft + 4
        rgb[py0:py0 + 8, px0:px0 + 6] = col("hazard_yellow", 0.56)
        rgb[py0, px0:px0 + 6] = col("hazard_yellow", 0.84)
        rgb[py0 + 7, px0:px0 + 6] = col("hazard_yellow", 0.30)
        ep2lib.stamp(rgb, m, px0 + 2, py0 + 1, col("concrete_cold", 0.04))
    return rgb


# ---------------------------------------------------------------- roundhouse doors
RH_RAILS = ((0, 8), (37, 43), (77, 83), (118, 124))
RH_GLAZING = (9, 36)
RH_PANES = 4                 # panes across each leaf
RH_GREEN = 0.36              # military_green: depot paint, sun-faded
RH_WEAR = 0.70


def tex_rhdr1() -> np.ndarray:
    """A roundhouse stall's wooden doors, one pair per tile: two leaves of
    vertical boards in faded depot green worn to the wood, glazed panes on
    top (two broken, one boarded), rails and braces, black strap hinges,
    a drop bar, soot over the top from the engines. No number: stalls 2 and
    3 and S2's panel wear the same face."""
    rng = rng_for(10)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    gr = fbm(w, h, 8, 3, rng, 0.5, aspect=6.0)
    boards = xx // 6
    bt = RH_GREEN + rng.uniform(-0.04, 0.04, w // 6 + 1)
    paint = to_rgb(clip01(bt[boards] + (gr - 0.5) * 0.12 + grain(w, h, rng, 0.025)), "military_green")
    wood = to_rgb(clip01(0.34 + (gr - 0.5) * 0.20 + grain(w, h, rng, 0.03)), "plaster_warm")
    worn = (fbm(w, h, 6, 4, rng) > RH_WEAR) & (rng.random((h, w)) < 0.85)
    rgb = np.where(worn[..., None], wood, paint)
    f = np.ones((h, w))
    f[:, ::6] = 0.70
    f[:, 1::6] *= 1.05
    for a, b in RH_RAILS:
        f[a:b] *= 1.10
        f[a, :] *= 1.18
        f[b - 1, :] *= 0.72
        f[min(b, h - 1), :] *= 0.55
    rgb = shade(rgb, f)
    # glazing: four panes per leaf, two rows
    g0, g1 = RH_GLAZING
    mid = (g0 + g1) // 2
    pane_w = 64 // RH_PANES
    glass = to_rgb(clip01(0.12 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.06 + (g1 - yy) * 0.003), "steel_blue")
    glaze = (yy >= g0) & (yy < g1)
    rgb = np.where(glaze[..., None], glass, rgb)
    for lx in range(0, w, pane_w):
        rgb[g0:g1, lx:lx + 2] = col("military_green", 0.28)
    rgb[mid:mid + 2, :] = col("military_green", 0.28)
    for px, py in ((1, 0), (6, 1)):                     # broken panes: black holes, jagged
        x0, y0 = px * pane_w + 2, (g0 if py == 0 else mid + 2)
        y1 = mid if py == 0 else g1
        hole = (rng.random((y1 - y0, pane_w - 2)) < 0.55) | (np.add.outer(np.arange(y1 - y0), np.arange(pane_w - 2)) % 5 < 3)
        region = rgb[y0:y1, x0:x0 + pane_w - 2]
        region[hole] = col("concrete_cold", 0.02)
    bx0 = 3 * pane_w + 2                                 # a boarded pane
    rgb[g0:mid, bx0:bx0 + pane_w - 2] = to_rgb(clip01(0.40 + grain(pane_w - 2, mid - g0, rng, 0.04)), "plaster_warm")
    rgb[g0 + 4, bx0:bx0 + pane_w - 2] = col("concrete_cold", 0.20)
    # braces (bottom on the hinge side up to the latch side)
    ov = Overlay(w, h)
    for (pa, pb) in ((43, 77), (83, 118)):
        ov.line([(4, pb - 2), (60, pa + 2)], col("military_green", 0.24), 5.0)
        ov.line([(4, pb - 4), (60, pa)], col("military_green", 0.46), 1.0)
        ov.line([(124, pb - 2), (68, pa + 2)], col("military_green", 0.24), 5.0)
        ov.line([(124, pb - 4), (68, pa)], col("military_green", 0.46), 1.0)
    # strap hinges
    iron = col("concrete_cold", 0.06)
    for y in (40, 121):
        ov.polygon([(0, y - 2), (34, y - 1), (36, y), (34, y + 1), (0, y + 2)], iron)
        ov.polygon([(128, y - 2), (94, y - 1), (92, y), (94, y + 1), (128, y + 2)], iron)
    # meeting stiles, cover strip, drop bar and hasp
    ov.rect(63, 0, 65, 128, fill=col("concrete_cold", 0.04))
    ov.rect(65, 0, 69, 128, fill=col("military_green", 0.30))
    ov.rect(65, 0, 66, 128, fill=col("military_green", 0.50))
    ov.rect(71, 56, 74, 104, fill=col("concrete_cold", 0.12))
    ov.rect(71, 56, 72, 104, fill=col("concrete_cold", 0.36))
    ov.rect(68, 72, 80, 76, fill=col("concrete_cold", 0.10))
    rgb = ov.composite(rgb)
    for y in (40, 121):
        for x in (6, 14, 22, 30, 98, 106, 114, 122):
            rgb[y - 1, x] = col("concrete_cold", 0.40)
    # soot over the top, kicks at the foot
    soot = clip01(1 - yy / 70.0) * (0.55 + 0.45 * fbm(w, h, 8, 3, rng))
    rgb = shade(rgb, 1 - 0.55 * soot)
    kick = (yy > 112) & (fbm(w, h, 16, 2, rng) > 0.6)
    rgb = np.where(kick[..., None], shade(rgb, 0.7), rgb)
    return rgb


# ---------------------------------------------------------------- the station board
BOARD_W, BOARD_H = 256, 64
BOARD_FRAME = 3
STATION = ("СВЕРДЛОВСК", "СОРТИРОВОЧНЫЙ")   # Sverdlovsk-Sortirovochny, the marshalling yard's station
BOLTS = ((8, 8), (247, 8), (8, 55), (247, 55))


def tex_stan1() -> np.ndarray:
    """The station board: white enamel in a steel frame, «СВЕРДЛОВСК» large
    and «СОРТИРОВОЧНЫЙ» under it in black from our alphabet, enamel chipped
    to rust, rust run from the four bolts, soot along the top. A middle
    texture over the platform, drawn once (256x64, the size of SDSLOG1)."""
    rng = rng_for(11)
    w, h = BOARD_W, BOARD_H
    yy, xx = np.mgrid[0:h, 0:w]
    enamel = to_rgb(clip01(0.93 + (fbm(w, h, 8, 3, rng) - 0.5) * 0.05 + grain(w, h, rng, 0.01)), "plaster_warm")
    soot = clip01(1 - yy / 26.0) * 0.18 * (0.6 + 0.4 * fbm(w, h, 16, 2, rng))
    rgb = shade(enamel, 1 - soot)
    ink = col("concrete_cold", 0.03)
    put_word(rgb, STATION[0], ink, w / 2, 22, scale=2, spacing=1)
    put_word(rgb, STATION[1], ink, w / 2, 47, scale=1, spacing=2)
    rgb[33, 40:216] = col("flag_red", 0.62)
    rgb[34, 40:216] = col("flag_red", 0.50)
    for _ in range(6):                                 # enamel chips, rust ringed
        cx, cy = int(rng.integers(6, w - 6)), int(rng.choice([int(rng.integers(5, 12)), int(rng.integers(52, 59))]))
        r = float(rng.uniform(0.8, 1.8))
        d = np.hypot(xx - cx, yy - cy)
        rgb[d < r + 1.2] = col("rust_brown", 0.42)
        rgb[d < r] = col("concrete_cold", 0.10)
    for bx, by in BOLTS:
        ln = int(rng.integers(6, 14))
        for k in range(ln):
            y = by + 2 + k
            if y < h - BOARD_FRAME:
                rgb[y, bx] = shade(np.array([col("rust_brown", 0.48)], np.uint8), 1 - k / ln * 0.3)[0]
        rgb[by - 1:by + 2, bx - 1:bx + 2] = col("concrete_cold", 0.20)
        rgb[by - 1, bx - 1] = col("concrete_cold", 0.60)
    fr = BOARD_FRAME
    frame = (xx < fr) | (xx >= w - fr) | (yy < fr) | (yy >= h - fr)
    rgb[frame] = col("concrete_cold", 0.14)
    rgb[0, :] = col("concrete_cold", 0.40)
    rgb[:, 0] = col("concrete_cold", 0.34)
    rgb[h - 1, :] = col("concrete_cold", 0.04)
    rgb[:, w - 1] = col("concrete_cold", 0.06)
    rgb[fr, fr:w - fr] = shade(rgb[fr, fr:w - fr], 0.72)
    return rgb


# ================================================================ MAP05: the dam
GRILL_PITCH = 16
GRILL_FLATS = (14, 66)        # flat bars across, both inside the 80-high window
ROD = (0.62, 0.48, 0.34, 0.20)  # a round bar's shading, left to right


def tex_gril1() -> np.ndarray:
    """Window bars, MASKED: four round bars per tile through two riveted
    flat bars, dark paint chipped to rust. RGBA with hard alpha, for the
    control room's two windows onto the hall (a middle texture)."""
    rng = rng_for(12)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = np.zeros((h, w, 3), np.uint8)
    solid = np.zeros((h, w), bool)
    for bx in range(GRILL_PITCH // 2 - 2, w, GRILL_PITCH):
        for k, t in enumerate(ROD):
            rgb[:, bx + k] = col("concrete_cold", t * 0.6 + 0.05)
            solid[:, bx + k] = True
    for fy in GRILL_FLATS:
        for k, t in enumerate((0.42, 0.30, 0.26, 0.22, 0.16, 0.06)):
            rgb[fy + k, :] = col("concrete_cold", t)
            solid[fy + k, :] = True
        for bx in range(GRILL_PITCH // 2 - 2, w, GRILL_PITCH):
            rivet(rgb, bx + 1, fy + 2, "concrete_cold", 0.30)
    rust = (fbm(w, h, 8, 3, rng) > 0.60) | ((fbm(w, h, 16, 2, rng, aspect=6.0) > 0.66) & (yy > GRILL_FLATS[0]))
    rtone = to_rgb(clip01(0.34 + grain(w, h, rng, 0.06)), "rust_brown")
    rgb = np.where((rust & solid)[..., None], shade(rtone, 0.7 + 0.3 * (rgb[..., 0:1].mean(-1) / 120.0)), rgb)
    alpha = np.where(solid, 255, 0).astype(np.uint8)
    return np.dstack([rgb, alpha])


DOORB_INK = ("mosaic_cobalt", 0.66, ("cream_yellow", 0.92))   # trim, tone, the pass plate's letters
DOORB_OFFSET = 13


def tex_doorb() -> np.ndarray:
    """The blue key door: gen_factory.key_door (SDDOORY's and SDDOORR's
    recipe, SDDOOR1's leaf) with the trim, ribs, plate and hazard band in
    cobalt and the plate's «ПРОПУСК» in cream. Its own seed for the wear
    of the paint (5713)."""
    inks = dict(gen_factory.KEY_INKS)
    inks["SDDOORB"] = DOORB_INK
    offsets = dict(gen_factory.SEED_OFFSET)
    offsets["SDDOORB"] = BATCH_SEED + DOORB_OFFSET - gen_factory.BATCH_SEED
    with _patched(gen_factory, KEY_INKS=inks, SEED_OFFSET=offsets, ramp_colour=gen_metro.any_ramp_colour):
        return gen_factory.key_door("SDDOORB")


FENCE_MESH = 8                # chain-link diamonds, 8 px
FENCE_TOP_RAIL = 20
FENCE_BOTTOM = 124
BARBS = (6, 13)               # barbed-wire strands
HV_PLATE = (5, 42, 59, 90)    # x0, y0, x1, y1


def tex_hvlt1() -> np.ndarray:
    """The substation's fence, MASKED: galvanised chain link between steel
    posts (the post sits on the tile's edge), a top rail, two strands of
    barbed wire, and the Soviet danger plate «СТОЙ!» with the red lightning
    arrow wired to the mesh. RGBA with hard alpha, for a two-sided line:
    the transformers show through."""
    rng = rng_for(14)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = np.zeros((h, w, 3), np.uint8)
    solid = np.zeros((h, w), bool)
    zinc = to_rgb(clip01(0.52 + (fbm(w, h, 8, 3, rng) - 0.5) * 0.16 + grain(w, h, rng, 0.04)), "steel_blue")
    rusty = fbm(w, h, 6, 3, rng) > 0.62
    zinc = np.where(rusty[..., None], to_rgb(clip01(0.40 + grain(w, h, rng, 0.05)), "rust_brown"), zinc)
    mesh = (((xx + yy) % FENCE_MESH == 0) | ((xx - yy) % FENCE_MESH == 0)) & (yy > FENCE_TOP_RAIL) & (yy < FENCE_BOTTOM)
    rgb[mesh] = zinc[mesh]
    knots = mesh & ((xx + yy) % FENCE_MESH == 0) & ((xx - yy) % FENCE_MESH == 0)
    rgb[knots] = shade(zinc[knots], 1.3)
    solid |= mesh
    for y0, tones in ((FENCE_TOP_RAIL - 1, (0.70, 0.50, 0.28)), (FENCE_BOTTOM, (0.55, 0.40, 0.22))):
        for k, t in enumerate(tones):
            rgb[y0 + k, :] = col("steel_blue", t)
            solid[y0 + k, :] = True
    for by in BARBS:
        for x in range(w):
            y = by + (1 if (x // 2) % 2 else 0)
            rgb[y, x] = col("steel_blue", 0.60 if x % 2 else 0.40)
            solid[y, x] = True
        for x in range(3 + (by % 4), w, 7):
            for dx, dy in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
                rgb[by + dy, (x + dx) % w] = col("steel_blue", 0.66)
                solid[by + dy, (x + dx) % w] = True
    for k, t in enumerate((0.30, 0.46, 0.24, 0.12)):   # the post: an angle iron on the seam
        x = (k - 2) % w
        rgb[2:h, x] = col("concrete_cold", t)
        solid[2:h, x] = True
    # the plate
    x0, y0, x1, y1 = HV_PLATE
    plate = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    rgb[plate] = to_rgb(clip01(0.94 + grain(w, h, rng, 0.015)), "plaster_warm")[plate]
    border = plate & ((xx < x0 + 3) | (xx >= x1 - 3) | (yy < y0 + 3) | (yy >= y1 - 3))
    rgb[border] = col("flag_red", 0.66)
    solid |= plate
    chips = plate & ~border & (fbm(w, h, 16, 2, rng) > 0.76) & (rng.random((h, w)) < 0.5)
    rgb[chips] = col("rust_brown", 0.40)
    put_word(rgb, "СТОЙ!", col("concrete_cold", 0.03), (x0 + x1) / 2, y0 + 11, spacing=1)
    ov = Overlay(w, h)
    cx = (x0 + x1) / 2
    ov.polygon([(cx + 4, y0 + 19), (cx - 6, y0 + 33), (cx, y0 + 33), (cx - 5, y0 + 45),
                (cx + 7, y0 + 29), (cx + 1, y0 + 29), (cx + 7, y0 + 19)], col("flag_red", 0.70))
    ov.polygon([(cx - 5, y0 + 45), (cx - 8, y0 + 38), (cx - 1, y0 + 41)], col("flag_red", 0.70))
    rgb = ov.composite(rgb)
    for px, py in ((x0 + 1, y0 + 1), (x1 - 2, y0 + 1), (x0 + 1, y1 - 2), (x1 - 2, y1 - 2)):
        rgb[py, px] = col("concrete_cold", 0.20)
    alpha = np.where(solid, 255, 0).astype(np.uint8)
    rgb[~solid] = 0
    return np.dstack([rgb, alpha])


# ================================================================ MAP06: Red Square
CLOCK_C = (64, 64)
DIAL_R = 46
SURROUND = 6                 # the white stone square round the dial starts here
CLOCK_TIME = (11, 55)        # five to midnight


def hand_points(cx, cy, ang, length, width, tail):
    """A tapered clock hand as a polygon, ang in radians clockwise from 12."""
    s, c = np.sin(ang), np.cos(ang)
    ux, uy = s, -c
    px, py = c, s
    return [(cx - ux * tail + px * width * 0.6, cy - uy * tail + py * width * 0.6),
            (cx + ux * length * 0.75 + px * width, cy + uy * length * 0.75 + py * width),
            (cx + ux * length, cy + uy * length),
            (cx + ux * length * 0.75 - px * width, cy + uy * length * 0.75 - py * width),
            (cx - ux * tail - px * width * 0.6, cy - uy * tail - py * width * 0.6)]


def tex_clok1() -> np.ndarray:
    """The Spasskaya tower's clock: a black dial in a gilded rim, gold hour
    markers and minute dots, a gold inner ring and sun at the centre, gilded
    hands at five to midnight; the dial set in a square of white limestone
    with gold rosettes in the spandrels, on the tower's red brick."""
    rng = rng_for(15)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = gen_moscow.kremlin_brick(w, h, rng)
    lime = to_rgb(clip01(0.86 + (fbm(w, h, 6, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)), "plaster_warm")
    s0, s1 = SURROUND, w - SURROUND
    square = (xx >= s0) & (xx < s1) & (yy >= s0) & (yy < s1)
    rgb = np.where(square[..., None], lime, rgb)
    f = np.ones((h, w))
    f[s0, s0:s1] = 1.15
    f[s0:s1, s0] = 1.10
    f[s1 - 1, s0:s1] = 0.55
    f[s0:s1, s1 - 1] = 0.60
    f[s0 + 4, s0 + 4:s1 - 4] = 0.70
    f[s0 + 4:s1 - 4, s0 + 4] = 0.72
    f[s1 - 5, s0 + 4:s1 - 4] = 1.12
    f[s0 + 4:s1 - 4, s1 - 5] = 1.10
    streak = clip01(fbm(w, h, 8, 2, rng, aspect=8.0) - 0.55) * 0.7
    f *= 1 - streak * (yy > 90)
    rgb = shade(rgb, f)
    cx, cy = CLOCK_C
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    rgb[(d >= DIAL_R) & (d < DIAL_R + 2.5)] = col("concrete_cold", 0.30)
    dial = to_rgb(clip01(0.05 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.03), "concrete_cold")
    rgb = np.where((d < DIAL_R)[..., None], dial, rgb)
    ov = Overlay(w, h)
    gold, gold_hi, gold_lo = col("hazard_yellow", 0.78), col("cream_yellow", 0.92), col("hazard_yellow", 0.36)
    ov.arc_ring(cx, cy, DIAL_R, DIAL_R - 4, 0, 360, gold)
    ov.arc_ring(cx, cy, DIAL_R, DIAL_R - 1.5, 160, 290, gold_hi)
    ov.arc_ring(cx, cy, DIAL_R - 3, DIAL_R - 4, -20, 110, gold_lo)
    for k in range(60):
        a = np.deg2rad(k * 6)
        r = DIAL_R - 7
        ov.ellipse(cx + r * np.sin(a) - 0.6, cy - r * np.cos(a) - 0.6, cx + r * np.sin(a) + 0.6, cy - r * np.cos(a) + 0.6, fill=gold)
    for k in range(12):
        a = np.deg2rad(k * 30)
        r0, r1 = DIAL_R - 19, DIAL_R - 9
        wdt = 2.2 if k % 3 == 0 else 1.5
        s, c = np.sin(a), np.cos(a)
        ov.polygon([(cx + s * r0, cy - c * r0), (cx + s * (r0 + r1) / 2 + c * wdt, cy - c * (r0 + r1) / 2 + s * wdt),
                    (cx + s * r1, cy - c * r1), (cx + s * (r0 + r1) / 2 - c * wdt, cy - c * (r0 + r1) / 2 - s * wdt)], gold)
    for k in range(24):
        a = np.deg2rad(k * 15 + 7.5)
        r = DIAL_R - 23
        ov.ellipse(cx + r * np.sin(a) - 0.7, cy - r * np.cos(a) - 0.7, cx + r * np.sin(a) + 0.7, cy - r * np.cos(a) + 0.7, fill=gold_lo)
    hh, mm = CLOCK_TIME
    a_m = np.deg2rad(mm * 6)
    a_h = np.deg2rad((hh % 12 + mm / 60) * 30)
    g = ov.group(outline=col("concrete_cold", 0.02), outline_width=0.8)
    g.polygon(hand_points(cx, cy, a_m, DIAL_R - 9, 1.6, 6), gold)
    g.polygon(hand_points(cx, cy, a_h, DIAL_R - 22, 2.6, 5), gold)
    tip_r = DIAL_R - 24
    g.ellipse(cx + tip_r * np.sin(a_h) - 3, cy - tip_r * np.cos(a_h) - 3, cx + tip_r * np.sin(a_h) + 3, cy - tip_r * np.cos(a_h) + 3, fill=gold)
    ov.end_group(g)
    ov.polygon(star_points(cx, cy, 5.5, 2.4), gold_hi)
    ov.ellipse(cx - 2, cy - 2, cx + 2, cy + 2, fill=gold)
    for sx, sy in ((s0 + 9, s0 + 9), (s1 - 9, s0 + 9), (s0 + 9, s1 - 9), (s1 - 9, s1 - 9)):
        for k in range(6):
            a = np.deg2rad(k * 60)
            ov.ellipse(sx + 3 * np.cos(a) - 1.4, sy + 3 * np.sin(a) - 1.4, sx + 3 * np.cos(a) + 1.4, sy + 3 * np.sin(a) + 1.4, fill=gold)
        ov.ellipse(sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5, fill=col("flag_red", 0.55))
    return ov.composite(rgb)


RUBY_C = (64, 58)
RUBY_R = 50
RUBY_IN = 0.40               # inner radius / outer
STEM = (61, 67, 104, 128)


def tex_ruby1() -> np.ndarray:
    """The Kremlin's ruby star, MASKED: five arms of ruby glass, each split
    into a lit and a shaded facet and lit from within, a gilded frame and
    ribs, an inner gold star; under it the gilded ball and stem of the
    spire. RGBA with hard alpha, for a middle texture against the sky."""
    w = h = 128
    cx, cy = RUBY_C
    pts_out = star_points(cx, cy, RUBY_R + 2, (RUBY_R + 2) * RUBY_IN)
    pts = star_points(cx, cy, RUBY_R - 1, (RUBY_R - 1) * RUBY_IN)
    gold, gold_hi = col("hazard_yellow", 0.80), col("cream_yellow", 0.94)
    x0, x1, y0, y1 = STEM

    def outline(ov, fill):
        ov.polygon(pts_out, fill)
        ov.rect(x0, y0, x1, y1, fill=fill)
        ov.ellipse(cx - 6, y0 - 6, cx + 6, y0 + 6, fill=fill)

    solid = mask_of(outline, w, h)
    rgb = np.zeros((h, w, 3), np.uint8)
    ov = Overlay(w, h)
    outline(ov, gold)
    for i in range(5):
        tip = pts[2 * i]
        left, right = pts[(2 * i - 1) % 10], pts[2 * i + 1]
        ov.polygon([(cx, cy), left, tip], col("flag_red", 0.92))
        ov.polygon([(cx, cy), tip, right], col("flag_red", 0.62))
    rgb = ov.composite(rgb)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    inner = shade(rgb, np.clip(1.25 - 0.45 * r / RUBY_R, 0.75, 1.25))
    red = rgb[..., 0].astype(int) > rgb[..., 1].astype(int) + 40
    rgb = np.where(red[..., None], inner, rgb)
    ov = Overlay(w, h)
    for i in range(5):
        ov.line([(cx, cy), pts[2 * i]], gold, 1.0)
    ov.polygon(star_points(cx, cy, 13, 13 * RUBY_IN), col("cream_yellow", 0.80))
    ov.polygon(star_points(cx, cy, 10, 10 * RUBY_IN), col("flag_red", 1.0))
    ov.ellipse(cx - 2, cy - 2, cx + 2, cy + 2, fill=(255, 255, 255))
    ov.ellipse(cx - 5, y0 - 5, cx + 5, y0 + 5, fill=gold)
    ov.ellipse(cx - 3, y0 - 4, cx, y0 - 1, fill=gold_hi)
    ov.rect(x0 + 1, y0 + 5, x0 + 2, y1, fill=gold_hi)
    ov.rect(x1 - 2, y0 + 5, x1, y1, fill=col("hazard_yellow", 0.45))
    rgb = ov.composite(rgb)
    rgb[~solid] = 0
    return np.dstack([rgb, np.where(solid, 255, 0).astype(np.uint8)])


GUM_WORDS = ("ТКАНИ", "ОБУВЬ", "ЧАСЫ")     # fabrics, shoes, watches: three shopfronts
SIGN = (4, 21)                             # the gilt sign band (rows)
SHOP_ARCH_C, SHOP_ARCH_R = (32, 48), 26
SHOP_X = (6, 58)
STALLRISER = 104
GUM_HOLE = [(11, 72), (16, 66), (19, 70), (25, 67), (27, 75), (24, 80), (28, 88), (20, 86), (16, 95), (13, 86),
            (9, 83), (12, 78)]


def gum_front(word: str) -> np.ndarray:
    """One GUM shopfront (same seed for every variant: only the word moves)."""
    rng = rng_for(17)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    stone = to_rgb(clip01(0.74 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)), "plaster_warm")
    rgb = stone.copy()
    f = np.ones((h, w))
    f[:, 3] = 0.65
    f[:, w - 4] = 1.12
    f[yy % 16 == 0] *= 0.85
    rgb = shade(rgb, f)
    # interior: dark, an empty shelf or two, a fallen one
    cx, cy = SHOP_ARCH_C
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    opening = ((xx >= SHOP_X[0]) & (xx < SHOP_X[1]) & (yy >= cy) & (yy < STALLRISER)) | ((yy < cy) & (d < SHOP_ARCH_R))
    dark = to_rgb(clip01(0.08 + (fbm(w, h, 4, 2, rng) - 0.5) * 0.06 + np.clip((cy - yy) * 0.002, 0, 0.05)), "concrete_cold")
    for sy in (66, 82):
        dark[sy, SHOP_X[0]:SHOP_X[1]] = col("rust_brown", 0.16)
        dark[sy + 1, SHOP_X[0]:SHOP_X[1]] = col("concrete_cold", 0.03)
    ov0 = Overlay(w, h)
    ov0.line([(36, 101), (54, 88)], col("rust_brown", 0.24), 2.0)
    dark = ov0.composite(dark)
    glass = shade(dark, 1.0)
    streak = (np.abs((xx - yy * 0.5) % 40 - 14) < 2) & opening
    glass[streak] = shade(glass[streak], 2.2)
    rgb = np.where(opening[..., None], glass, rgb)
    # the broken pane (lower left): the shop seen straight through a jagged
    # hole with a bright broken edge, cracks running out of it
    hole = mask_of(lambda o, c: o.polygon(GUM_HOLE, c), w, h)
    rim = hole & ~(np.roll(hole, 1, 0) & np.roll(hole, -1, 0) & np.roll(hole, 1, 1) & np.roll(hole, -1, 1))
    rgb = np.where(hole[..., None], shade(dark, 0.8), rgb)
    rgb[rim] = col("steel_blue", 0.74)
    ov = Overlay(w, h)
    for a, b in (((17, 64), (13, 52)), ((26, 66), (30, 56)), ((29, 86), (30, 100)), ((9, 80), (7, 92))):
        ov.line([a, b], col("steel_blue", 0.70), 0.7)
    frame = col("rust_brown", 0.22)
    frame_hi = col("hazard_yellow", 0.62)
    ov.arc_ring(cx, cy, SHOP_ARCH_R + 2, SHOP_ARCH_R, 180, 360, frame)
    ov.arc_ring(cx, cy, SHOP_ARCH_R + 2, SHOP_ARCH_R + 1, 200, 300, frame_hi)
    ov.rect(SHOP_X[0] - 2, cy, SHOP_X[0], STALLRISER, fill=frame)
    ov.rect(SHOP_X[1], cy, SHOP_X[1] + 2, STALLRISER, fill=frame)
    ov.rect(SHOP_X[0], cy - 1, SHOP_X[1], cy + 1, fill=frame)
    ov.rect(31, cy, 33, STALLRISER, fill=frame)
    for a in (45, 90, 135):
        t = np.deg2rad(a)
        ov.line([(cx, cy), (cx - SHOP_ARCH_R * np.cos(t), cy - SHOP_ARCH_R * np.sin(t))], frame, 1.2)
    ov.ellipse(cx - 5, cy - 5, cx + 5, cy + 5, outline=frame, width=1.2)
    rgb = ov.composite(rgb)
    sh = (rng.random((h, w)) < 0.25) & (yy >= STALLRISER + 1) & (yy < STALLRISER + 3) & (xx > 8) & (xx < 32)
    # the stallriser: dark polished panels on a brass kick rail
    sr = (yy >= STALLRISER) & (xx >= SHOP_X[0] - 2) & (xx < SHOP_X[1] + 2)
    wood = to_rgb(clip01(0.24 + (fbm(w, h, 8, 2, rng, aspect=0.3) - 0.5) * 0.08), "rust_brown")
    rgb = np.where(sr[..., None], wood, rgb)
    rgb[STALLRISER:STALLRISER + 2, SHOP_X[0] - 2:SHOP_X[1] + 2] = col("hazard_yellow", 0.60)
    for px0, px1 in ((9, 29), (35, 55)):
        rgb[STALLRISER + 5, px0:px1] = col("rust_brown", 0.40)
        rgb[STALLRISER + 5:120, px0] = col("rust_brown", 0.40)
        rgb[119, px0:px1] = col("rust_brown", 0.10)
        rgb[STALLRISER + 5:120, px1 - 1] = col("rust_brown", 0.10)
    rgb[sh] = col("steel_blue", 0.80)
    rgb[124:, :] = col("plaster_warm", 0.56)
    rgb[124, :] = col("plaster_warm", 0.80)
    # the gilt sign: black glass, gold letters from our alphabet, gold frame
    s0, s1 = SIGN
    rgb[s0:s1, 3:61] = to_rgb(clip01(np.full((s1 - s0, 58), 0.05) + grain(58, s1 - s0, rng, 0.01)), "concrete_cold")
    rgb[s0, 3:61] = col("hazard_yellow", 0.82)
    rgb[s1 - 1, 3:61] = col("hazard_yellow", 0.46)
    rgb[s0:s1, 3] = col("hazard_yellow", 0.70)
    rgb[s0:s1, 60] = col("hazard_yellow", 0.46)
    put_word(rgb, word, col("hazard_yellow", 0.86), 32, (s0 + s1) / 2, spacing=1, shadow_colour=col("hazard_yellow", 0.40))
    rgb[s1:s1 + 2, 3:61] = shade(rgb[s1:s1 + 2, 3:61], 0.6)
    return rgb


def tex_gums() -> list[np.ndarray]:
    """The GUM's galleries, three shopfronts in one cut: a gilt sign
    (black glass, gold letters «ТКАНИ», «ОБУВЬ», «ЧАСЫ»), round-arched
    glazing on a dark empty shop, one pane smashed (looted), the polished
    stallriser on a brass kick rail, stone piers at the edges."""
    return [gum_front(word) for word in GUM_WORDS]


ROOF_BAR = 16                 # glazing bars every 16 px along x
ROOF_PURLIN = 32


def tex_gumr1() -> np.ndarray:
    """The GUM's glass vault from below: iron arch rib along x on the tile
    edge, purlin across the middle, glazing bars, dirty panes dark with the
    night and warm with the city's glow, grime against the bars, two panes
    gone (darker), one cracked."""
    rng = rng_for(18)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    pane_id = (xx // ROOF_BAR) + (yy // ROOF_PURLIN) * (w // ROOF_BAR)
    pt = 0.24 + rng.uniform(-0.03, 0.03, (w // ROOF_BAR) * (h // ROOF_PURLIN))
    ly = yy % ROOF_PURLIN
    grime = clip01((ly - 18) / 14.0) * 0.10 + clip01(fbm(w, h, 8, 3, rng) - 0.55) * 0.18
    cold = to_rgb(clip01(pt[pane_id] - grime), "steel_blue").astype(float)
    warm = to_rgb(clip01(0.30 - grime), "rust_brown").astype(float)
    rgb = (cold * 0.78 + warm * 0.22).astype(np.uint8)
    gone = (pane_id == 1) | (pane_id == 6)
    rgb[gone] = to_rgb(clip01(np.full(gone.sum(), 0.08)), "steel_blue")
    for x in range(0, w, ROOF_BAR):
        rgb[:, x] = col("concrete_cold", 0.07)
        rgb[:, (x + 1) % w] = col("concrete_cold", 0.26)
    rgb[ROOF_PURLIN - 1:ROOF_PURLIN + 1, :] = col("concrete_cold", 0.10)
    rgb[ROOF_PURLIN - 1, :] = col("concrete_cold", 0.28)
    for k, t in enumerate((0.30, 0.16, 0.10, 0.05)):           # the arch rib, split over the edge
        rgb[(k - 2) % h, :] = col("concrete_cold", t)
    for x in range(2, w, 4):
        rgb[h - 2, x] = col("concrete_cold", 0.40)
        rgb[1, x] = col("concrete_cold", 0.22)
    ov = Overlay(w, h)
    ov.line([(36, 40), (42, 47), (46, 44)], col("steel_blue", 0.62), 0.7)
    ov.line([(42, 47), (40, 54)], col("steel_blue", 0.62), 0.7)
    return ov.composite(rgb)


MUSE_BAND = (0, 20)           # the white band of recessed square panels at the top
MUSE_PANEL = 16               # one panel per 16 px
MUSE_STRING = (92, 100)
MUSE_BRICK = 0.44             # marble_red: deeper and browner than the Kremlin's 0.60


def tex_muse1() -> np.ndarray:
    """The Historical Museum's red brick with its white trim: a deeper,
    browner brick than the Kremlin's in thin pale joints, a white band of
    recessed square panels («ширинки») each with a brick lozenge, a row of
    white drops under it, a white dentilled string course lower down."""
    rng = rng_for(19)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    row, colm, lx, ly = gen_factory.brick_courses(w, h)
    ny, nx = h // gen_factory.BRICK_H, w // gen_factory.BRICK_W
    tone = MUSE_BRICK + rng.uniform(-0.06, 0.06, (ny, nx))
    brown = rng.random((ny, nx)) < 0.18
    field = tone[row, colm] + (fbm(w, h, 8, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    brick = ep2lib.any_to_rgb(clip01(field), "marble_red")
    brick = np.where(brown[row, colm][..., None], to_rgb(clip01(field - 0.02), "rust_brown"), brick)
    mortar = (lx < gen_factory.MORTAR) | (ly < gen_factory.MORTAR)
    rgb = np.where(mortar[..., None], to_rgb(clip01(0.56 + grain(w, h, rng, 0.03)), "plaster_warm"), brick)
    f = np.ones((h, w))
    f[(ly == 1) & ~mortar] = 1.12
    f[ly == gen_factory.BRICK_H - 1] *= 0.80
    f *= 1 + (fbm(w, h, 8, 3, rng, 0.5, aspect=8.0) - 0.5) * 0.16
    rgb = shade(rgb, f)
    lime = to_rgb(clip01(0.88 + (fbm(w, h, 6, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)), "plaster_warm")
    b0, b1 = MUSE_BAND
    s0, s1 = MUSE_STRING
    white = ((yy >= b0) & (yy < b1)) | ((yy >= s0) & (yy < s1))
    rgb = np.where(white[..., None], lime, rgb)
    g = np.ones((h, w))
    g[b0, :] = 1.10
    g[b0 + 3, :] = 0.62
    plx = xx % MUSE_PANEL
    panel = (yy >= b0 + 6) & (yy < b1 - 3) & (plx >= 2) & (plx < MUSE_PANEL - 2)
    g[panel] = 0.80
    g[(yy == b0 + 6) & panel] = 0.55
    g[panel & (plx == 2)] = 0.62
    g[panel & (plx == MUSE_PANEL - 3)] = 1.08
    g[b1 - 1, :] = 0.55
    g[s0, :] = 1.12
    g[s1 - 1, :] = 0.55
    g[(yy >= s0 + 3) & (yy < s0 + 6) & (xx % 4 >= 2)] *= 0.55
    rgb = shade(rgb, g)
    lc = (yy - (b0 + 6 + b1 - 3) / 2.0, plx + 0.5 - MUSE_PANEL / 2)
    loz = panel & (np.abs(lc[0]) + np.abs(lc[1]) < 4.2)
    rgb[loz] = col("marble_red", 0.50)
    rgb[loz & (lc[0] < 0) & (lc[1] < 0)] = col("marble_red", 0.66)
    for x in range(3, w, 8):                            # the white drops under the band
        rgb[b1:b1 + 3, x:x + 2] = col("plaster_warm", 0.86)
        rgb[b1 + 3, x:x + 2] = col("plaster_warm", 0.55)
        rgb[b1 + 4, x:x + 2] = shade(rgb[b1 + 4, x:x + 2], 0.6)
    rgb[b1, :] = shade(rgb[b1, :], 0.7)
    rgb[s1, :] = shade(rgb[s1, :], 0.6)
    return rgb


# ================================================================ pieces
WHY_BRICK = "v2 solo por marble_red, como SDBRCK1 y SDKREM1 aprobados (D66, D107): v1 no tiene rojo de ladrillo cocido."
PIECES = [
    # ---- skies
    Piece2("SDSKY1", tex_sky1, "sky", SKY_SIZE, ["SDSKY1"], 1, "x",
           "Noche de los Urales (cielo MAP04)",
           "Cielo nocturno sobre Sverdlovsk: nubes rotas con la luna detrás y bordes plateados cerca de ella, "
           "alguna estrella en los claros, el resplandor cálido de la ciudad y de Uralmash bajo las nubes, las "
           "lomas de taiga en negro, chimeneas con su humo y luces rojas, un mástil de radio y, al este, las dos "
           "torres de focos de la propia playa de vías.",
           set_name="sky",
           rec_why="Es lo que más pantalla ocupa en MAP04 (todo el patio es exterior). Oscuro arriba para que los "
                   "enemigos se recorten; las luces lejanas están en la franja del horizonte."),
    Piece2("SDSKY2", tex_sky2, "sky", SKY_SIZE, ["SDSKY2"], 2, "x",
           "Noche de Moscú (cielo MAP06)",
           "Cielo nocturno de Moscú: techo de nubes bajo, iluminado en naranja pardo por el sodio de la ciudad, "
           "más frío y oscuro en el cénit; el perfil de bloques con ventanas encendidas, tres rascacielos de "
           "Stalin con su estrella y la aguja de la torre de Ostankino (1967) con sus luces rojas.",
           set_name="sky",
           rec_why="El resplandor naranja dice «gran ciudad» al instante y contrasta con el Kremlin rojo. Sin San "
                   "Basilio a propósito: el cielo gira 360° y no puedo garantizar en qué dirección caería."),
    # ---- MAP04
    Piece2("SDWROF1", tex_wrof1, "flat", (64, 64), ["SDWROF1"], 3, "xy",
           "Techo de vagón (con pasarela)",
           "Techo de vagón de mercancías visto desde arriba: chapa en minio rojo-óxido con nervios transversales "
           "cada 16 px, hollín de las locomotoras, óxido en los nervios y la pasarela de tablas a lo largo de y "
           "sobre sus soportes.",
           set_name="railway",
           rec_why="Mismo rojo-óxido que SDWAGN1, así techo y lateral son el mismo vagón. La pasarela va en y: girar "
                   "en UDMF para que siga al tren."),
    Piece2("SDGOND1", tex_gond1, "flat", (64, 64), ["SDGOND1"], 4, "xy",
           "Suelo de góndola",
           "Fondo de un vagón abierto soviético: las trampillas de descarga (juntas, dos nervios estampados cada "
           "una, bisagras a los lados), óxido, polvo de carbón y terrones de carbón en los rincones.",
           set_name="railway",
           rec_why="Las trampillas son lo que distingue un полувагон soviético. Oscuro para que el suelo no compita."),
    Piece2("SDCAB1", tex_cab1, "wall", (128, 128), ["SDCAB1"], 5, "no",
           "Cabina de locomotora: frontal (caldera)",
           "Mirando hacia delante dentro de la cabina de vapor: el frontal negro de la caldera con remaches, la "
           "puerta del hogar con el fuego asomando por la rendija y los agujeros de aire, manómetros de caldera y de "
           "freno en latón, dos niveles de agua, la palanca del regulador, volantes rojos en los tubos de vapor y "
           "las ventanas redondas de la cabina a la noche (con una señal roja a lo lejos).",
           set_name="railway",
           rec_why="Pieza única para la pared delantera de la cabina. El brillo del hogar marca el sitio del "
                   "interruptor de salida (que sigue siendo SDSW1D; un par de interruptores a juego sería otra tarea)."),
    Piece2("SDCAB2", tex_cab2, "wall", (64, 128), ["SDCAB2"], 6, "x",
           "Cabina de locomotora: lateral",
           "El costado de la cabina por dentro: chapa pintada de verde sobre juntas remachadas, la ventana "
           "corredera a la playa de noche (una señal y luces lejanas, un reflejo), el reposabrazos de madera, un "
           "volante de válvula y una placa esmaltada, el zócalo más oscuro rozado por las botas.",
           set_name="railway",
           rec_why="Casa con SDCAB1 (mismo verde y latón). Tila en x por si la cabina es más larga que 64."),
    Piece2("SDSBOX1", tex_sbox1, "wall", (64, 64), ["SDSBOX1"], 7, "x",
           "Cristal de la cabina de señales",
           "La ventana del puesto de señales vista desde la playa, de noche y encendida por dentro: junquillos "
           "pintados de blanco, luz cálida más fuerte bajo la lámpara colgante, las siluetas de las palancas abajo, "
           "un cristal rajado; dintel de hormigón arriba y alféizar abajo. Las filas 8-55 son el hueco de 48.",
           set_name="railway",
           rec_why="Con offsety 8 el cristal llena exactamente los huecos de 48 (umbrales 160-208). Para que brille "
                   "de noche conviene luz alta en ese sector o un brightmap (mod-engineer)."),
    Piece2("SDLEVR1", tex_levr1, "flat", (64, 64), ["SDLEVR1"], 8, "x",
           "Palanquero (visto desde arriba)",
           "El palanquero mecánico desde arriba: la bancada de hierro con sus ranuras sobre el entarimado, ocho "
           "palancas pintadas por función (rojo señales, negro agujas, azul cerrojo, amarillo avanzada, blanco "
           "reserva) con empuñaduras pulidas, tres echadas, placas de latón 1-8, la madera gastada donde se pone el "
           "guardavías.",
           set_name="railway",
           rec_why="El pedestal de la llave amarilla. Ocho palancas por 64: tila en x para un palanquero más largo."),
    Piece2("SDLEVR2", tex_levr2, "wall", (64, 64), ["SDLEVR2"], 9, "x",
           "Palanquero (frente)",
           "El palanquero de frente: ocho palancas saliendo de la bancada de hierro fundido con arquillos, "
           "pintadas por función, empuñadura y gatillo pulidos, tres echadas hacia nosotros, placas de latón "
           "numeradas, la pared verde de la cabina detrás.",
           set_name="railway",
           rec_why="64x64 (el mapa pedía 64x16: no es tamaño de pared acordado). Mismas palancas y colores que "
                   "SDLEVR1, para que suelo y frente digan lo mismo."),
    Piece2("SDRHDR1", tex_rhdr1, "wall", (128, 128), ["SDRHDR1"], 10, "x",
           "Puertas del cocherón",
           "Las puertas de una vía del cocherón, un par por tesela: dos hojas de tablas verticales en verde de "
           "depósito desvaído hasta la madera, cristales arriba (dos rotos, uno tapado con una tabla), peinazos y "
           "riostras, pernios de hierro negro, una tranca, hollín de las locomotoras sobre la parte alta. Sin "
           "número: las vías 2 y 3 y el panel de S2 tienen que llevar la misma cara.",
           set_name="railway",
           rec_why="Distinta de SDGATE1 (chapa de fábrica) y de SDGATE2 (corredera roja del almacén); el hollín "
                   "arriba cuenta que dentro hay vapor."),
    Piece2("SDSTAN1", tex_stan1, "wall", (256, 64), ["SDSTAN1"], 11, "no",
           "Cartel de la estación «СВЕРДЛОВСК»",
           "El letrero de la estación: esmalte blanco en marco de acero, «СВЕРДЛОВСК» grande y «СОРТИРОВОЧНЫЙ» "
           "debajo, en negro con nuestro alfabeto (sin fuentes del sistema, sale igual en el Mac y en Windows), "
           "un filete rojo, el esmalte saltado hasta el óxido, chorreones de los cuatro tornillos, hollín arriba.",
           set_name="railway",
           rec_why="Textura media sobre el andén, una sola vez (256x64, el tamaño de SDSLOG1). Se lee a 1x desde el "
                   "andén; el nombre completo es el de la estación real de clasificación."),
    # ---- MAP05
    Piece2("SDGRIL1", tex_gril1, "wall", (64, 128), ["SDGRIL1"], 12, "x",
           "Barrotes de ventana (enmascarada)",
           "Rejas, ENMASCARADA: cuatro barrotes redondos por tesela que atraviesan dos pletinas remachadas, "
           "pintura oscura saltada hasta el óxido. RGBA con alfa dura, para las dos ventanas de la sala de control "
           "sobre la nave (textura media).",
           set_name="dam", masked=True,
           rec_why="Las dos pletinas caen dentro del hueco de 80 de alto. Misma excepción RGBA que SDCHAN1 y SDINSL1.",
           ),
    Piece2("SDDOORB", tex_doorb, "wall", (128, 128), ["SDDOORB"], DOORB_OFFSET, "no",
           "Puerta de la llave azul",
           "La puerta de la llave azul: la receta de SDDOORY y SDDOORR (la hoja verde de SDDOOR1, su volante y sus "
           "remaches) con el marco, los nervios, la placa y la banda de peligro en cobalto y «ПРОПУСК» en crema.",
           set_name="dam", ramps=("mosaic_cobalt",),
           why_v2="v2 solo por mosaic_cobalt: el azul de v1 (steel_blue) es gris y no se lee como llave azul. Es el "
                  "cobalto del mosaico SDMOSA1, que enmarca esta misma puerta en MAP06.",
           replays="hoja: semilla 1982 (SDDOOR1), como SDDOORY/SDDOORR",
           rec_why="Gemela de las puertas amarilla y roja aprobadas: el jugador ya sabe leerla. La usan MAP05 (la "
                   "puerta azul) y MAP06 (la puerta azul entre mosaicos)."),
    Piece2("SDHVLT1", tex_hvlt1, "wall", (64, 128), ["SDHVLT1"], 14, "x",
           "Valla de alta tensión con placa (enmascarada)",
           "La valla de la subestación, ENMASCARADA: tela metálica galvanizada entre postes de angular (el poste "
           "cae en el borde de la tesela), pasamanos, dos hilos de espino y la placa soviética de peligro «СТОЙ!» "
           "con la flecha-rayo roja, atada a la malla.",
           set_name="dam", masked=True,
           rec_why="Al ser enmascarada se ven los transformadores a través: pide que la valla sea una línea de dos "
                   "caras (level-designer). «НАПРЯЖЕНИЕ» no cabe en 64 px con nuestra letra pequeña; la flecha lo dice."),
    # ---- MAP06
    Piece2("SDCLOK1", tex_clok1, "wall", (128, 128), ["SDCLOK1"], 15, "no",
           "Reloj de la Spásskaya",
           "La esfera de la torre Spásskaya: negra en un aro dorado, marcas horarias y puntos de minuto en oro, "
           "anillo interior y sol dorados en el centro, agujas doradas a las doce menos cinco; la esfera en un "
           "cuadrado de caliza blanca con rosetas de oro en las enjutas, sobre el ladrillo rojo de la torre.",
           set_name="moscow", ramps=("marble_red",), why_v2=WHY_BRICK,
           rec_why="Sustituye a la placa SDSTAR1 en el piso del reloj. Marcas en vez de números: a 128 px los "
                   "números de la esfera real no se leerían."),
    Piece2("SDRUBY1", tex_ruby1, "wall", (128, 128), ["SDRUBY1"], 16, "no",
           "Estrella de rubí (enmascarada)",
           "La estrella de rubí del Kremlin, ENMASCARADA: cinco brazos de cristal rubí, cada uno con una faceta "
           "clara y otra en sombra, iluminada desde dentro, marco y nervios dorados, estrella interior de oro; "
           "debajo la bola dorada y el vástago de la aguja.",
           set_name="moscow", masked=True,
           rec_why="Textura media sobre la torre, contra el cielo: con SDSKY2 detrás es la silueta del final."),
    Piece2("SDGUMS", tex_gums, "wall", (64, 128), [f"SDGUMS{i}" for i in (1, 2, 3)], 17, "x",
           "Escaparates del GUM (3 variantes)",
           "Las tiendas de las galerías del GUM: rótulo de cristal negro con letras doradas de nuestro alfabeto "
           "(«ТКАНИ» telas, «ОБУВЬ» calzado, «ЧАСЫ» relojes), escaparate de medio punto sobre la tienda vacía y "
           "oscura, un cristal reventado (saqueo), zócalo de madera pulida sobre una barra de latón, pilastras de "
           "piedra en los bordes.",
           set_name="moscow", variants=True,
           rec_why="Tres variantes con la misma fachada y otra palabra, para alternarlas a lo largo de la galería; "
                   "una sola repetida diría «ТКАНИ ТКАНИ ТКАНИ»."),
    Piece2("SDGUMR1", tex_gumr1, "flat", (64, 64), ["SDGUMR1"], 18, "xy",
           "Techo de cristal del GUM",
           "La bóveda de cristal del GUM desde abajo: costilla de hierro del arco en el borde, correa en el centro, "
           "junquillos, cristales sucios oscuros de noche y templados por el resplandor de la ciudad, mugre contra "
           "los hierros, dos cristales que faltan y uno rajado.",
           set_name="moscow",
           rec_why="Hace de techo de la galería y del atrio (hoy es cielo). La costilla va en x: girar en UDMF para "
                   "seguir la bóveda."),
    Piece2("SDMUSE1", tex_muse1, "wall", (64, 128), ["SDMUSE1"], 19, "xy",
           "Ladrillo del Museo Histórico",
           "El ladrillo rojo del Museo Histórico con sus remates blancos: un rojo más hondo y más pardo que el "
           "del Kremlin con juntas finas claras, una banda blanca de casetones cuadrados («ширинки») con un rombo "
           "de ladrillo cada uno, una fila de pinjantes blancos debajo y una imposta blanca con dentículos.",
           set_name="moscow", ramps=("marble_red",), why_v2=WHY_BRICK,
           rec_why="Distinto de SDKREM1 (más pardo) y de SDSPAS1 (sin pilastras, con casetones): tres rojos de "
                   "ladrillo que se distinguen en la misma plaza."),
]

SETS = (("sky", "Cielos", "MAP04 y MAP06"),
        ("railway", "MAP04 · Railway — la playa de Sverdlovsk (segunda ronda)", "MAP04"),
        ("dam", "MAP05 · Dam — la presa del Volga (segunda ronda)", "MAP05"),
        ("moscow", "MAP06 · Moscow — la Plaza Roja (segunda ronda)", "MAP06"))
SET_LEADS = {
    "sky": "Formato: 1024×128, una vuelta completa de 360° sin repetirse (el SKY1 de Freedoom es 256×128 y se repite "
           "cuatro veces). La fila 100 queda a la altura de los ojos: las siluetas lejanas suben por encima de ella "
           "para que se vean por encima de los muros. Se registran como textura y se nombran en MAPINFO (`sky1 = "
           "\"SDSKY1\"` en MAP04, `\"SDSKY2\"` en MAP06): eso y añadir 1024×128 a los tamaños de check_pk3 es del "
           "mod-engineer. NO VERIFICADO en GZDoom (posición vertical y estiramiento con freelook; si hace falta, "
           "`skyoffset` en TEXTURES).",
    "railway": "Luz recomendada de noche: patio 112-144 bajo SDSKY1, cabina 128-160 (el hogar), puesto de señales 144-176.",
    "dam": "Las dos enmascaradas son RGBA como SDCHAN1/SDINSL1: van en `MASKED_TEXTURES` de check_pk3 al instalarse.",
    "moscow": "Con SDSKY2 la plaza pasa a ser de noche: la luz recomendada en el índice (160-192, «a plena luz») "
              "habría que bajarla a 128-160 (decisión del level-designer).",
}

# The sample rooms: approved lumps (read from assets/) and this round's. ceil None shows the sky.
SCENES = {
    "SDSKY1": {"back": "SDWAGN1", "left": "SDBRCK3", "right": "SDTANK1", "floor": "SDTRAK1", "low": True},
    "SDSKY2": {"back": "SDKREM2", "left": "SDGUM1", "right": "SDKREM1", "floor": "SDCOBL1", "low": True},
    "SDWROF1": {"back": "SDWAGN1", "left": "SDWAGN1", "right": "SDWAGN1", "floor": "SDWROF1", "low": True},
    "SDGOND1": {"back": "SDWAGN1", "left": "SDWAGN1", "right": "SDWAGN1", "floor": "SDGOND1"},
    "SDCAB1": {"back": "SDCAB1", "left": "SDCAB2", "right": "SDCAB2", "floor": "SDFLR4", "ceil": "SDFLR4"},
    "SDCAB2": {"back": "SDCAB1", "left": "SDCAB2", "right": "SDCAB2", "floor": "SDFLR4", "ceil": "SDFLR4"},
    "SDSBOX1": {"back": ("stack", "SDSBOX1", "SDBRCK1"), "left": "SDBRCK1", "right": "SDBRCK1", "floor": "SDBLST1"},
    "SDLEVR1": {"back": ("stack", "SDSBOX1", "SDLEVR2"), "left": "SDBRCK3", "right": "SDBRCK3", "floor": "SDLEVR1",
                "ceil": "SDCEIL2"},
    "SDLEVR2": {"back": ("stack", "SDSBOX1", "SDLEVR2"), "left": "SDBRCK3", "right": "SDBRCK3", "floor": "SDLEVR1",
                "ceil": "SDCEIL2"},
    "SDRHDR1": {"back": "SDRHDR1", "left": "SDBRCK3", "right": "SDBRCK3", "floor": "SDTRAK1"},
    "SDSTAN1": {"back": ("stack", "SDSTAN1", "SDBRCK1"), "left": "SDBRCK1", "right": "SDBRCK1", "floor": "SDBLST1"},
    "SDGRIL1": {"back": ("over", "SDGRIL1", "SDTURB1"), "left": "SDCTRL1", "right": "SDCTRL1", "floor": "SDFLR4",
                "ceil": "SDCEIL1"},
    "SDDOORB": {"back": "SDDOORB", "left": "SDMOSA1", "right": "SDMOSA1", "floor": "SDFLR3", "ceil": "SDCEIL1"},
    "SDHVLT1": {"back": "SDHVLT1", "left": "SDHVLT1", "right": "SDHVLT1", "floor": "SDBLST1"},
    "SDCLOK1": {"back": "SDCLOK1", "left": "SDSPAS1", "right": "SDSPAS1", "floor": "SDCOBL1"},
    "SDRUBY1": {"back": "SDRUBY1", "left": "SDKREM2", "right": "SDKREM2", "floor": "SDCOBL1"},
    "SDGUMS": {"back": "SDGUMS2", "left": "SDGUMS1", "right": "SDGUMS3", "floor": "SDMARB1f", "ceil": "SDGUMR1"},
    "SDGUMR1": {"back": "SDGUMS3", "left": "SDGUMS1", "right": "SDGUMS2", "floor": "SDMARB1f", "ceil": "SDGUMR1"},
    "SDMUSE1": {"back": "SDMUSE1", "left": "SDMUSE1", "right": "SDKREM1", "floor": "SDCOBL1"},
}
SCENE_SKY = {"railway": "SDSKY1", "moscow": "SDSKY2", "sky": None, "dam": None}
OVERVIEWS = {
    "railway": [("La cabina y el cocherón", {"back": "SDCAB1", "left": "SDCAB2", "right": "SDRHDR1", "floor": "SDFLR4"}),
                ("El andén de noche", {"back": ("stack", "SDSTAN1", "SDBRCK1"), "left": "SDWAGN1",
                                       "right": ("stack", "SDSBOX1", "SDBRCK1"), "floor": "SDBLST1"})],
    "dam": [("La subestación", {"back": "SDHVLT1", "left": "SDDOORB", "right": "SDHVLT1", "floor": "SDBLST1"})],
    "moscow": [("La torre", {"back": "SDCLOK1", "left": "SDFLAG3", "right": "SDFLAG4", "floor": "SDCOBL1"}),
               ("La galería del GUM", {"back": "SDGUMS1", "left": "SDGUMS2", "right": "SDGUMS3", "floor": "SDMARB1f",
                                      "ceil": "SDGUMR1"}),
               ("El museo", {"back": "SDMUSE1", "left": "SDMUSE1", "right": "SDRUBY1", "floor": "SDCOBL2"})],
}
# v2 ramps of the approved lumps the scenes borrow (so the room keeps their colours).
APPROVED_RAMPS = {"SDMOSA1": ("mosaic_cobalt",), "SDKREM1": ("marble_red",), "SDKREM2": ("marble_red",),
                  "SDSPAS1": ("marble_red",), "SDBRCK1": ("marble_red",), "SDBRCK3": ("marble_red",),
                  "SDBANR1": ("marble_red",), "SDMARB1": ("marble_red",), "SDMARB1f": ("marble_red",),
                  "SDFLAG3": ("marble_red",), "SDFLAG4": ("marble_red",)}   # D119: gen_soviet_flags.py
SKY_YAWS = (0, 90, 180, 270)
SKY_VIEW_ROOM_H = 64          # the sky views: walls half as high, so more sky shows
GIF_MS = gen_episode2.GIF_MS


def pieces_of(set_name: str) -> list[Piece2]:
    return [p for p in PIECES if p.set_name == set_name]


def all_lumps() -> list[str]:
    return [l for p in PIECES for l in p.lumps]


# ================================================================ build
def frames_of(p: Piece2) -> list[np.ndarray]:
    out = p.builder()
    return out if isinstance(out, list) else [out]


def build_set(set_name: str, out_dir: Path | None = None) -> tuple[list[dict], dict]:
    """Render one set into work/art/episode2b/<set>/ (or out_dir). Returns
    (manifest entries, quantised arrays by lump)."""
    out_dir = out_dir or WORK_ROOT / set_name
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for p in pieces_of(set_name):
        frames = frames_of(p)
        assert len(frames) == len(p.lumps), p.key
        for lump, rgb in zip(p.lumps, frames):
            assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
            h, w = rgb.shape[:2]
            assert (w, h) == p.size, (lump, w, h)
            assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, lump
            assert (rgb.shape[2] == 4) == p.masked, lump
            img = quantise(rgb, p.ramps)
            img.save(out_dir / f"{lump}.png", optimize=True)
            arrays[lump] = ep2lib.as_array(img)
        first = arrays[p.lumps[0]]
        colours = {tuple(int(v) for v in c) for c in first[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": p.key, "lumps": p.lumps, "kind": p.kind, "set": set_name, "width": p.size[0],
            "height": p.size[1], "palette_version": p.palette, "v2_ramps": list(p.ramps), "masked": p.masked,
            "tiles": p.tiles, "script": SCRIPT_REL, "seed": BATCH_SEED + p.offset, "replays": p.replays,
            "files": [f"work/art/episode2b/{set_name}/{lump}.png" for lump in p.lumps],
            "colours_used": len(colours), "mean_luma": round(ep2lib.mean_luma(first), 1),
            "seam_score": None if p.masked else round(tiling_seam_score(first[..., :3]), 2),
            "title_es": p.title, "description_es": p.desc, "status": "draft, proposed (P4, D112)",
        })
    return entries, arrays


def build_all(out_root: Path | None = None) -> tuple[dict, dict]:
    entries, arrays = {}, {}
    for set_name, *_ in SETS:
        e, a = build_set(set_name, None if out_root is None else out_root / set_name)
        entries[set_name] = e
        arrays.update(a)
    return entries, arrays


# ================================================================ views
def sky_screen(sky: np.ndarray, yaw_deg: float = 0.0) -> np.ndarray:
    """The sky as the sample room's screen sees it: 1024 columns per turn,
    texture row = screen row (vanilla's sky mid at the horizon), the bottom
    row held below the texture. NOT VERIFIED against GZDoom's own mapping."""
    h, w = sky.shape[:2]
    xs = np.arange(ep2lib.SCR_W) + 0.5 - ep2lib.SCR_W / 2
    ang = np.deg2rad(yaw_deg) + np.arctan(xs / ep2lib.FOCAL)
    u = np.floor(ang / (2 * np.pi) * w).astype(int) % w
    v = np.clip(np.arange(ep2lib.SCR_H), 0, h - 1)
    return sky[v[:, None], u[None, :], :3]


def lookup(lump, A: dict) -> np.ndarray:
    if isinstance(lump, tuple):
        kind, a, b = lump
        ta, tb = lookup(a, A), lookup(b, A)
        if kind == "stack":                               # a 64-high piece over the lower rows of a wall
            hb = 128 - ta.shape[0]
            low = np.tile(tb[..., :3], (1, max(1, ta.shape[1] // tb.shape[1]), 1))[-hb:, :ta.shape[1]]
            return np.vstack([ta[..., :3], low])
        if kind == "over":                                # a masked piece over another (tiled to its width)
            top = np.tile(ta, (1, tb.shape[1] // ta.shape[1], 1))
            return ep2lib.composite_over(top, tb)
        if kind == "row":                                 # wall, banner, wall
            return np.hstack([ta[..., :3], tb[..., :3], ta[..., :3]])
        raise ValueError(kind)
    if lump in A:
        return A[lump]
    if lump == "SDMARB1f":                                # the metro marble's top 64 rows as a floor
        A[lump] = ep2lib.load_approved("SDMARB1")[:64, :64]
        return A[lump]
    A[lump] = ep2lib.load_approved(lump)
    return A[lump]


def scene_ramps(spec: dict) -> tuple:
    names = set()
    own = {l: p for p in PIECES for l in p.lumps}

    def walk(x):
        if isinstance(x, tuple):
            for y in x[1:]:
                walk(y)
        elif x:
            names.update(own[x].ramps if x in own else APPROVED_RAMPS.get(x, ()))
    for k in ("back", "left", "right", "floor", "ceil"):
        walk(spec.get(k))
    return tuple(r for r in EXTRA_RAMPS_ALLOWED if r in names)


def render_scene(spec: dict, A: dict, sky_lump: str | None, yaw: float = 0.0, light: float = 0.9) -> np.ndarray:
    get = lambda k: None if spec.get(k) is None else lookup(spec[k], A)  # noqa: E731
    sky = sky_screen(A[sky_lump], yaw) if sky_lump else None
    ramps = scene_ramps(spec)
    room_h = SKY_VIEW_ROOM_H if spec.get("low") else ep2lib.ROOM_H
    with _patched(ep2lib, V2_RAMPS_ALLOWED=ramps, ROOM_H=room_h):
        return ep2lib.render_room(get("back"), get("left"), get("right"), get("floor"), get("ceil"),
                                  light=light, version=2 if ramps else 1, sky=sky)


def make_views(entries: dict, A: dict) -> dict:
    V = {}
    for set_name, *_ in SETS:
        vdir = WORK_ROOT / set_name / "views"
        vdir.mkdir(parents=True, exist_ok=True)
        sky = SCENE_SKY[set_name]
        for p in pieces_of(set_name):
            if p.kind == "sky":
                for yaw in SKY_YAWS:
                    path = vdir / f"{p.key}_yaw{yaw}.png"
                    Image.fromarray(render_scene(SCENES[p.key], A, p.key, yaw, 0.85)).save(path, optimize=True)
                    V[f"{p.key}_yaw{yaw}"] = path
                continue
            path = vdir / f"{p.key}_room.png"
            Image.fromarray(render_scene(SCENES[p.key], A, sky)).save(path, optimize=True)
            V[p.key + "_room"] = path
        for i, (_, spec) in enumerate(OVERVIEWS.get(set_name, ())):
            path = vdir / f"overview{i}.png"
            Image.fromarray(render_scene(spec, A, sky)).save(path, optimize=True)
            V[f"{set_name}_overview{i}"] = path
    door = np.hstack([lookup("SDDOORY", A)[..., :3], lookup("SDDOORR", A)[..., :3], A["SDDOORB"][..., :3]])
    path = WORK_ROOT / "dam" / "views" / "SDDOORB_compare.png"
    Image.fromarray(door).save(path, optimize=True)
    V["SDDOORB_compare"] = path
    return V


# ================================================================ sheet
def png_uri(arr: np.ndarray) -> str:
    return gen_episode2.png_uri(arr)


def file_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


TILES_TXT = {"xy": "x e y", "x": "solo x", "y": "solo y", "no": "no (pieza única)"}
KIND_TXT = {"wall": "pared", "flat": "suelo/techo", "sky": "cielo"}

CSS_EXTRA = """
.pano{overflow-x:auto;max-width:100%;border:1px solid var(--line);background:var(--well)}
.pano img{max-width:none !important;border:0}
.yaws{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px;margin:8px 0}
.yaws img{width:100%;height:auto}
.var{display:flex;gap:8px}
"""

JS = r"""
const KEY = "sd-2026-10-22_P4_episode2-textures-round2";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
const st = id => (S[id] = S[id] || {v:"", n:""});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function zoomFor(w){ return w <= 64 ? 4 : (w <= 128 ? 3 : 2); }
function vote(it){
  return `<div class="vote">
    <div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
    <textarea class="note" placeholder="Notas (qué cambiar, más claro, otro color…)">${esc(st(it.id).n)}</textarea>
  </div>`;
}
function meta(it){
  return `<div class="name"><code>${esc(it.lumps.join(", "))}</code><span class="ev">${it.kind} · ${it.w}×${it.h} · tila: ${esc(it.tilesTxt)} · paleta ${it.palTxt}${it.masked ? " · enmascarada (RGBA)" : ""}</span></div>
    <p class="meta"><b>${esc(it.title)}.</b> ${esc(it.desc)}</p>`;
}
function foot(it){
  return `<p class="rec"><b>Recomiendo: ${esc(it.rec)}.</b> ${esc(it.recWhy)}${it.whyV2 ? ` <i>Paleta: ${esc(it.whyV2)}</i>` : ""}</p>
    <p class="meta">Origen (a) ${esc(it.script)}, semilla ${it.seed}${it.replays ? ` (repite a propósito: ${esc(it.replays)})` : ""} · colores ${it.colours} · luma media ${it.luma} · costura ${it.seam === null ? "n/a" : it.seam}</p>`;
}
function skyCard(it){
  const yaws = it.yaws.map((src, i) => `<div class="v"><b>mirando a ${[0,90,180,270][i]}°</b><img class="px" src="${src}" alt=""></div>`).join("");
  return `<div class="card"><div class="row" id="r-${it.id}" data-id="${it.id}"><div>${meta(it)}
    <div class="v"><b>panorámica completa, 360° (2×; desliza a los lados)</b><div class="pano"><img class="px" src="${it.imgs[0]}" width="${it.w*2}" height="${it.h*2}" alt=""></div></div>
    <div class="v"><b>la costura: el final y el principio juntos (2×)</b><div class="pano"><img class="px" src="${it.seamImg}" width="512" height="256" alt=""></div></div>
    <h3>En el juego, cuatro direcciones (vista mínima tipo Doom con muros bajos; no es el motor)</h3>
    <div class="yaws">${yaws}</div>${foot(it)}</div>${vote(it)}</div></div>`;
}
function card(it){
  if (it.sky) return skyCard(it);
  const z = zoomFor(it.w), mz = it.w <= 64 ? 2 : 1;
  const mk = it.masked ? " masked" : "";
  const solo = it.imgs.map((src, i) => `<div class="v"><b>${it.imgs.length > 1 ? esc(it.lumps[i]) + " " : ""}sola 1×</b><img class="px${mk}" src="${src}" width="${it.w}" height="${it.h}" alt=""></div>`).join("");
  const zoom = it.imgs.map((src, i) => `<div class="v"><b>${it.imgs.length > 1 ? esc(it.lumps[i]) + " " : ""}${z}×</b><img class="px${mk}" src="${src}" width="${it.w*z}" height="${it.h*z}" alt=""></div>`).join("");
  const mosaic = it.tilesTxt.startsWith("no") ? "" : `<div class="v"><b>mosaico 3×3 (${mz}×)</b><div class="mosaic${mk}" style="width:${it.w*3*mz}px;height:${it.h*3*mz}px;background-image:url(${it.imgs[0]});background-size:${it.w*mz}px ${it.h*mz}px"></div></div>`;
  const extra = it.extra ? `<div class="views"><div class="v"><b>${esc(it.extra.label)}</b><img class="px" src="${it.extra.img}" width="${it.extra.w}" height="${it.extra.h}" alt=""></div></div>` : "";
  return `<div class="card"><div class="row" id="r-${it.id}" data-id="${it.id}"><div>${meta(it)}
    <div class="views">${solo}</div><div class="views">${zoom}${mosaic}</div>${extra}
    <div class="views"><div class="v"><b>sala de muestra (2×; no es el motor)</b><img class="px" src="${it.room}" width="640" height="400" alt=""></div></div>
    ${foot(it)}</div>${vote(it)}</div></div>`;
}
function build(){
  for (const set of SETS) document.getElementById("cards-" + set).innerHTML = ITEMS.filter(i => i.set === set).map(card).join("");
  ITEMS.forEach(i => paint(i.id));
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
}
function summary(){
  const label = {ok:"OK", no:"NO", q:"?"};
  const done = ITEMS.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  const L = [`Texturas Episodio 2, segunda ronda (2026-10-22_P4, D112): ${done}/${ITEMS.length} juzgadas`];
  let cur = "";
  for (const i of ITEMS) {
    if (i.set !== cur) { cur = i.set; L.push(`[${i.set}]`); }
    const s = st(i.id), n = (s.n || "").trim().replace(/\s+/g, " ");
    L.push(`${i.lumps.join("/")}: ${label[s.v] || "sin juzgar"}${n ? ` — «${n}»` : ""}`);
  }
  const g = (document.getElementById("general").value || "").trim().replace(/\s+/g, " ");
  if (g) L.push(`General: «${g}»`);
  document.getElementById("result").value = L.join("\n");
}
function copy(which){
  const t = document.getElementById("result"), msg = document.getElementById(which);
  summary();
  const ok = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(ok, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  if (e.target.id === "general") { S._general = e.target.value; save(); summary(); return; }
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.getElementById("copyTop").addEventListener("click", () => copy("copiedTop"));
document.getElementById("copyBottom").addEventListener("click", () => copy("copiedBottom"));
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar las respuestas y notas de esta hoja?")) { S = {}; save(); document.getElementById("general").value = ""; build(); summary(); } });
document.getElementById("general").value = S._general || "";
build(); summary();
"""

EXTRAS = {"SDDOORB": ("Las tres puertas de llave juntas: SDDOORY, SDDOORR (aprobadas) y SDDOORB, 2×", "SDDOORB_compare")}


def items_json(entries: dict, A: dict, V: dict) -> list[dict]:
    items = []
    for set_name, *_ in SETS:
        by_key = {e["piece"]: e for e in entries[set_name]}
        for p in pieces_of(set_name):
            e = by_key[p.key]
            it = {
                "id": p.key, "set": set_name, "lumps": p.lumps, "kind": KIND_TXT[p.kind], "w": p.size[0], "h": p.size[1],
                "tilesTxt": TILES_TXT[p.tiles], "palTxt": "v1" if not p.ramps else "v2 (" + " + ".join(p.ramps) + ")",
                "masked": p.masked, "title": p.title, "desc": p.desc, "rec": p.rec, "recWhy": p.rec_why,
                "whyV2": p.why_v2, "script": SCRIPT_REL, "seed": e["seed"], "replays": p.replays,
                "colours": e["colours_used"], "luma": e["mean_luma"], "seam": e["seam_score"],
                "imgs": [png_uri(A[l]) for l in p.lumps], "sky": p.kind == "sky",
            }
            if p.kind == "sky":
                a = A[p.lumps[0]]
                it["yaws"] = [file_uri(V[f"{p.key}_yaw{y}"]) for y in SKY_YAWS]
                it["seamImg"] = png_uri(np.hstack([a[:, -128:], a[:, :128]]))
            else:
                it["room"] = file_uri(V[p.key + "_room"])
            if p.key in EXTRAS:
                label, key = EXTRAS[p.key]
                with Image.open(V[key]) as im:
                    it["extra"] = {"label": label, "img": file_uri(V[key]), "w": im.width * 2, "h": im.height * 2}
            items.append(it)
    return items


def lump_table(entries: dict) -> str:
    rows = []
    for set_name, *_ in SETS:
        by_key = {e["piece"]: e for e in entries[set_name]}
        for p in pieces_of(set_name):
            e = by_key[p.key]
            rows.append(
                f"<tr><td><code>{html.escape(', '.join(p.lumps))}</code></td><td>{set_name}</td>"
                f"<td>{html.escape(p.title)}</td><td>{KIND_TXT[p.kind]}</td><td>{p.size[0]}×{p.size[1]}</td>"
                f"<td>{TILES_TXT[p.tiles]}</td><td>{'v1' if not p.ramps else 'v2: ' + ', '.join(p.ramps)}"
                f"{' RGBA' if p.masked else ''}</td><td>{e['seed']}</td><td>propuesta</td></tr>")
    head = ("<tr><th>Lump</th><th>Set</th><th>Qué es</th><th>Tipo</th><th>Tamaño</th><th>Tila</th><th>Paleta</th>"
            "<th>Semilla</th><th>Estado</th></tr>")
    return f'<div class="tablewrap"><table class="t">{head}{"".join(rows)}</table></div>'


def build_sheet(entries: dict, A: dict, V: dict, problems: list[str], out: Path = SHEET) -> Path:
    items = items_json(entries, A, V)
    n_lumps = sum(len(i["lumps"]) for i in items)
    sections = []
    for set_name, heading, maps in SETS:
        ovs = "".join(
            f'<div class="v"><b>{html.escape(label)} (2×)</b><img class="px" src="{file_uri(V[f"{set_name}_overview{i}"])}" '
            f'width="640" height="400" alt=""></div>' for i, (label, _) in enumerate(OVERVIEWS.get(set_name, ())))
        sections.append(
            f'<h2>{html.escape(heading)}</h2><p class="lead">{html.escape(SET_LEADS[set_name])}</p>'
            + (f'<h3>El set montado</h3><div class="ov">{ovs}</div>' if ovs else "")
            + f'<h3>Las piezas</h3><div id="cards-{set_name}"></div>')
    prob_html = ("<p><b>Comprobación de nombres:</b> los " + str(n_lumps) + " lumps propuestos son SD, de ≤ 8 "
                 "caracteres, y ninguno choca con un nombre existente en <code>assets/</code>, <code>work/</code> ni "
                 "<code>TEXTURE-INDEX.md</code>, ni se lee como fotograma de un sprite.</p>") if not problems else (
        "<p><b>Problemas de nombres:</b></p><ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in problems) + "</ul>")
    intro = f"""
<div class="intro">
<p><b>Qué es (D112, P4).</b> La segunda ronda de texturas del Episodio 2: lo que los tres mapas todavía cubren con
sustitutos. {len(items)} piezas, {n_lumps} lumps, en <b>borrador</b>, con el mismo método que la primera ronda (D107):
procedurales, semilla fija, paleta v1 (v2 solo donde la pieza dice por qué), estilo Doom, 64/128 px. Nada está en
<code>assets/</code> ni en el índice: si dices OK, el PM las instala tal cual.</p>
<ul>
<li><b>Primero los cielos</b>: es lo que más se ve. Panorámica completa y cuatro direcciones como se verían en el juego.</li>
<li>Cada textura se ve <b>sola</b>, ampliada, en <b>mosaico 3×3</b> si tila, y en una <b>sala de muestra</b> (vista
mínima tipo Doom; no es GZDoom, sirve para escala y repetición). Las salas de MAP04 y MAP06 ya llevan los cielos nuevos.</li>
<li><b>Texto:</b> ninguna fuente del sistema. «СВЕРДЛОВСК / СОРТИРОВОЧНЫЙ», «СТОЙ!», «ПРОПУСК», «ТКАНИ», «ОБУВЬ» y
«ЧАСЫ» salen de nuestro alfabeto (bigfont, D24), así que se generan igual en el Mac y en Windows; los números de las
palancas son los dígitos de 3×5 píxeles.</li>
<li><b>Pieza derivada:</b> <code>SDDOORB</code> repite la receta de las puertas amarilla y roja. Es un lump nuevo: las
aprobadas (<code>SDDOORY/R</code>) no se tocan ni se regeneran.</li>
<li><b>D12:</b> lugares y piedra.</li>
</ul>
<p>Marca <b>OK / NO / ?</b> en cada una, escribe notas si quieres y pulsa <b>Copiar resultado</b> para pegármelo.</p>
</div>"""
    ask = """
<div class="ask"><p><b>Además del OK/NO, cuatro preguntas:</b></p><ol>
<li><b>Formato del cielo.</b> 1024×128, una vuelta entera sin repetirse (mi recomendación), o 256×128 repetido cuatro
veces como el SKY1 de Freedoom (más pequeño, pero las chimeneas y los rascacielos se verían cuatro veces).</li>
<li><b>La puerta azul en cobalto</b> (v2), como el mosaico que la enmarca en MAP06. La alternativa
en v1 es gris azulado y no se lee como «azul». Recomiendo cobalto.</li>
<li><b>La valla de alta tensión enmascarada</b> (se ve a través): el level-designer tendría que convertir la valla de la
subestación en una línea de dos caras. Si prefieres una valla opaca (chapa con la placa), es una variante rápida.</li>
<li><b>El reloj a las doce menos cinco.</b> ¿Te vale, o prefieres otra hora (o las agujas en las doce)?</li>
</ol></div>"""
    data = json.dumps(items, ensure_ascii=False)
    sets_js = json.dumps([s for s, *_ in SETS])
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Texturas Episodio 2, ronda 2</title>
<style>{gen_episode2.CSS}{CSS_EXTRA}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Soviet Doom · Texturas del Episodio 2, segunda ronda (borrador)</h1>
  <span class="prog"><b id="pDone">0</b> / {len(items)} juzgadas</span>
  <button class="primary" id="copyTop">Copiar resultado</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
{intro}
{"".join(sections)}
<h2>Nombres de lump propuestos</h2>
{prob_html}
{lump_table(entries)}
<h2>Preguntas</h2>
{ask}
<h2>Resultado</h2>
<p class="meta">Comentario general (opcional):</p>
<textarea class="note" id="general" placeholder="Algo sobre la ronda en conjunto"></textarea>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copiar resultado</button><span class="copied" id="copiedBottom"></span> <button id="reset">Borrar respuestas</button></p>
<footer>Origen (a): procedural, <code>{SCRIPT_REL}</code> (semilla {BATCH_SEED}+n), máquinas comunes en
<code>tools/art/ep2lib.py</code> (sin modificar); PNG en <code>work/art/episode2b/&lt;set&gt;/</code>; tests
<code>tests/test_gen_episode2b.py</code>. Paleta <code>docs/art/palette.json</code> sin modificar. Licencia: obra propia,
CC BY-NC-SA 4.0 (D15). La sala de muestra NO es el colormap ni el cielo del motor (NO VERIFICADO en GZDoom). Nada
instalado: si una vale, la instala el PM con tu OK.</footer>
</div>
<script>
const SETS = {sets_js};
const ITEMS = {data};
{JS}
</script>
</body>
</html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return out


# ================================================================ main
def existing_lumps(own: frozenset[str] = frozenset()) -> set[str]:
    """Every lump name in use: files under assets/ and work/ and every SD
    name in TEXTURE-INDEX.md, this round's own drafts (work/art/episode2b/)
    aside. `own`: this round's lumps, whose copies in assets/<set>/ and rows
    in the index (once the CEO approves and the PM installs) are themselves,
    not a clash; a file of the same name anywhere else still is."""
    names = set()
    sets = {s for s, *_ in SETS}
    for root in (PROJECT_ROOT / "assets", PROJECT_ROOT / "work"):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.is_relative_to(WORK_ROOT):
                continue
            if root.name == "assets" and path.stem.upper() in own and path.parent.name in sets:
                continue
            names.add(path.stem.upper())
    if gen_episode2.TEXTURE_INDEX.is_file():
        text = gen_episode2.TEXTURE_INDEX.read_text(encoding="utf-8")
        names |= set(re.findall(r"SD[A-Z0-9]{1,6}", text)) - own
    return names


def name_problems() -> list[str]:
    lumps = all_lumps()
    return gen_episode2.name_problems(lumps, existing_lumps(frozenset(lumps)))


def main() -> None:
    problems = name_problems()
    entries, A = build_all()
    for set_name, *_ in SETS:
        (WORK_ROOT / set_name / "manifest.json").write_text(json.dumps({
            "episode": 2, "phase": "P4", "decision": "D112", "round": 2, "set": set_name, "script": SCRIPT_REL,
            "batch_seed": BATCH_SEED, "status": "drafts for the CEO; nothing in assets/",
            "preview": SHEET.relative_to(PROJECT_ROOT).as_posix(), "pieces": entries[set_name],
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        for e in entries[set_name]:
            print(f'{set_name:8s} {e["piece"]:8s} {e["width"]:4d}x{e["height"]:3d} v{e["palette_version"]} '
                  f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')
    V = make_views(entries, A)
    sheet = build_sheet(entries, A, V, problems)
    print("name problems:", problems or "none")
    print(f"sheet: {sheet} ({sheet.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
