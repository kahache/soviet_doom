#!/usr/bin/env python3
"""Lenin agitation poster (SDPOSTR1) — drawn silhouette + region-guided inks.

Origin (a)+(b): procedural drawing, in this script, over ONE free source
image — the July 1920 Lenin portrait by Pavel Zhukov (1870-1942), public
domain in Russia (author died 1942) and in the United States (published
before 1931). Rights verified in
`docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md` and recorded in
`docs/art/LICENSES.md`. No Soviet poster artwork is copied: the posters the
CEO sent are still protected, only the *technique* is reproduced here.

WHY THIS IS A REWRITE (round 2)
-------------------------------
Round 1 posterised the photograph with a single global threshold on a
128x128 lump. It failed, and the three reasons were specific:

1. A global cut splits the features into loose islands. The eyes, the
   moustache and the beard simply vanish, because at 70x105 pixels those
   features are only a few pixels across and they sit at luminances that
   land on the wrong side of one number.
2. **There was no outline.** The shadow half of the head was printed in the
   same ink as the ground, so the silhouette never closed and the eye read
   a pale vertical smudge instead of a skull. Real posters of this kind
   work because somebody *drew the perimeter of the head* first. A
   threshold cannot invent a perimeter.
3. 128x128 is too little surface for a portrait.

So round 2 changes the three things, in that order:

* **Format 128x256** — two tiles tall, the proportion of a sheet actually
  pinned on a wall. The head goes from ~70x105 to 93x138, +73% in area.
* **The head is a drawn shape, not a threshold result.** `HEAD_UV` and
  `BUST_UV` are hand-authored outlines in normalised head-box coordinates,
  traced off the photograph. They are filled with the mid ink and then
  **eroded by `RIM_PX`**: the ring left between the outline and the eroded
  interior is forced to the rim ink and is never overwritten by shading.
  That ring *is* the drawn contour. Whatever happens inside, the head keeps
  a closed perimeter against the ground.
* **Separation by region, never globally.** Each feature — cranium, brow,
  each eye socket, nose, each cheek, ear, moustache, mouth, beard, jaw —
  is a hand-drawn region with **its own percentile rule** (`dark`: the
  darkest N% of that region's pixels become shadow ink; `light`: the
  lightest N% become light ink). A percentile cannot make a feature
  disappear: the darkest 50% of an eye socket is always half an eye socket,
  whatever the exposure of the negative. Regions marked `core` also carry a
  hand-drawn minimum shape that is stamped if the photograph still yields
  too little, so the eyes and the moustache cannot be lost.

The bust below the jaw (neck, collar, tie, suit) is hand-painted outright:
in the source it is a shapeless dark mass that carries no information, and
a poster artist drew it rather than copying it.

Stage 1 (this script, current state): the DRAWING only, as a variant sheet
for the CEO. No plaque, no wall, no palette indexing, no Cyrillic slogan —
the bottom band is deliberately left as flat ground because the text is
decided after the portrait is chosen.

    .venv/bin/python tools/art/gen_lenin.py
        -> work/art/lenin/lenin_variants.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT_ROOT / "work" / "art" / "reference" / "lenin_1920_zhukov.jpg"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "lenin"
OUT_SHEET = OUT_DIR / "lenin_variants.png"

# ---------------------------------------------------------------------------
# Inks. Three colours of the mod palette and nothing else: a silkscreened
# poster is printed with a countable number of inks and that is the whole
# look. Indices are into the ramps of docs/art/palette.json.
# ---------------------------------------------------------------------------
INK_DARK = artlib.ramp("flag_red")[1]        # 58,12,11   near-black maroon
INK_RED = artlib.ramp("flag_red")[13]        # 211,48,41  flag red
INK_CREAM = artlib.ramp("cream_yellow")[13]  # 230,218,163 aged poster paper

# ---------------------------------------------------------------------------
# Lump geometry. 128x256 = two wall tiles tall, every side a multiple of 8.
# ---------------------------------------------------------------------------
LUMP_W = 128
LUMP_H = 256
SLOGAN_BAND_TOP_PX = 200     # below this line the lump is flat ground, kept for the Cyrillic slogan

# The head box: the rectangle the skull occupies, from the crown to the tip
# of the beard. Everything in this file is drawn in (u, v) coordinates
# normalised to that box, so the drawing survives a re-crop or a re-scale.
HEAD_X = 17
HEAD_Y = 12
HEAD_W = 93                  # 138 * the head's aspect in the source photo (0.675)
HEAD_H = 138

# Where the head box sits in the source photograph, as fractions of its size
# (measured on a coordinate grid laid over the scan; see the module docstring).
# u = 0 is the far edge of the ear, u = 1 the far edge of the lit temple;
# v = 0 is the crown of the skull, v = 1 the tip of the beard.
SRC_LEFT_F = 0.220
SRC_RIGHT_F = 0.770
SRC_TOP_F = 0.030
SRC_BOTTOM_F = 0.630

SUPERSAMPLE = 4              # masks are drawn at 4x and area-averaged down: smooth shapes, hard pixels
MEDIAN_RADIUS = 3            # kills the 1920 emulsion grain before any percentile is taken
BLUR_PX = 1.1                # blur AT LUMP SCALE: wrinkles and freckles must fuse before any cut, or every region prints as confetti
RIM_PX = 2                   # thickness of the drawn contour; 2 survives Doom's mipmapping, 1 does not
DESPECKLE_SIZE = 3           # mode filter on the ink map; 3 is the largest that does not eat an eyelid
CLOSE_PX = 1                 # morphological close per region: turns a cloud of pixels into one solid mark

# Ink slots. The drawing is done in slots; each variant then decides which
# palette ink prints each slot, which is exactly how a two-plate press works.
# SUIT is its own slot because the right ink for it depends on the ground:
# on a dark field a maroon suit would simply disappear.
GROUND, SHADOW, MID, LIGHT, RIM, SUIT = range(6)

# ---------------------------------------------------------------------------
# The drawn outlines. Traced off the photograph on a percentage grid, then
# simplified the way a cartellist simplifies: the ear is one bulge, the jaw
# one curve, no wobble that 93 pixels could not hold anyway.
# ---------------------------------------------------------------------------
HEAD_UV = [
    (0.473, 0.000), (0.600, 0.007), (0.727, 0.042), (0.836, 0.100),
    (0.927, 0.200), (0.973, 0.300), (0.982, 0.400), (0.964, 0.500),
    (0.936, 0.600), (0.891, 0.700), (0.818, 0.800), (0.727, 0.883),
    (0.618, 0.958), (0.527, 1.000), (0.436, 0.975), (0.345, 0.900),
    (0.255, 0.817), (0.164, 0.717), (0.100, 0.617), (0.040, 0.548),
    (-0.010, 0.500), (-0.015, 0.420), (0.030, 0.355), (0.045, 0.283),
    (0.073, 0.208), (0.145, 0.117), (0.255, 0.042), (0.364, 0.010),
]

# Neck and shoulders. They bleed off both sides of the lump on purpose: a
# bust that ends inside the sheet reads as a cut-out, one that runs off the
# edge reads as a poster.
BUST_UV = [
    (0.21, 0.90), (0.79, 0.90), (0.79, 1.06), (0.93, 1.13), (1.15, 1.22),
    (1.45, 1.33), (1.45, 1.36), (-0.45, 1.36), (-0.45, 1.33), (-0.15, 1.22),
    (0.07, 1.13), (0.21, 1.06),
]
NECK_UV = [(0.25, 0.90), (0.75, 0.90), (0.73, 1.10), (0.27, 1.10)]
UNDERCHIN_UV = [(0.25, 0.90), (0.75, 0.90), (0.73, 0.985), (0.27, 0.995)]
SHIRT_UV = [(0.25, 0.99), (0.75, 0.99), (0.68, 1.15), (0.50, 1.36), (0.32, 1.15)]
TIE_UV = [(0.425, 1.06), (0.575, 1.06), (0.565, 1.36), (0.435, 1.36)]

# ---------------------------------------------------------------------------
# The regions. Each one is a hand-drawn patch of the face plus its own rule:
#   dark  = fraction of the region's pixels, taken from the darkest end, that
#           print in the shadow ink
#   light = fraction taken from the lightest end that prints in the light ink
#   core  = minimum shape stamped in the shadow ink if the photograph did not
#           yield at least `floor` of the region as shadow
# Applied in order; later regions win where they overlap.
# ---------------------------------------------------------------------------
REGIONS = [
    {   # the bald cranium: the single most recognisable thing about this head
        "name": "dome",
        "poly": [(0.47, 0.03), (0.60, 0.04), (0.72, 0.09), (0.82, 0.17),
                 (0.89, 0.28), (0.92, 0.38), (0.91, 0.46), (0.75, 0.43),
                 (0.56, 0.42), (0.36, 0.43), (0.17, 0.46), (0.11, 0.38),
                 (0.10, 0.27), (0.14, 0.17), (0.23, 0.09), (0.35, 0.04)],
        "light": 0.62,
    },
    {   # lit rim down the right temple and cheek: it is what gives the skull volume
        "name": "temple_right",
        "poly": [(0.86, 0.26), (0.95, 0.34), (0.94, 0.52), (0.88, 0.64),
                 (0.80, 0.62), (0.82, 0.44)],
        "light": 0.50,
    },
    {
        "name": "cheek_right",
        "poly": [(0.62, 0.58), (0.86, 0.60), (0.84, 0.78), (0.72, 0.86),
                 (0.63, 0.80)],
        "light": 0.45,
    },
    {   # the shadow side of the face: a crescent, the classic poster modelling
        "name": "cheek_left",
        "poly": [(0.10, 0.56), (0.30, 0.56), (0.32, 0.80), (0.22, 0.90),
                 (0.13, 0.78)],
        "dark": 0.50,
    },
    {
        "name": "nose",
        "poly": [(0.44, 0.52), (0.58, 0.53), (0.62, 0.70), (0.58, 0.75),
                 (0.44, 0.74), (0.41, 0.66)],
        "light": 0.45, "dark": 0.15,
    },
    {
        "name": "nose_side",
        "poly": [(0.33, 0.56), (0.44, 0.55), (0.43, 0.74), (0.34, 0.76)],
        "dark": 0.40,
    },
    {   # the brow bar. Lenin's frown is half the portrait
        "name": "brow",
        "poly": [(0.13, 0.470), (0.34, 0.435), (0.56, 0.445), (0.78, 0.465),
                 (0.90, 0.490), (0.89, 0.535), (0.56, 0.505), (0.32, 0.495),
                 (0.12, 0.525)],
        "dark": 0.45,
    },
    {
        "name": "eye_left",
        "poly": [(0.25, 0.495), (0.45, 0.485), (0.47, 0.545), (0.27, 0.555)],
        "dark": 0.50, "floor": 0.30,
        "core": [(0.30, 0.505), (0.42, 0.500), (0.43, 0.535), (0.31, 0.540)],
    },
    {
        "name": "eye_right",
        "poly": [(0.64, 0.515), (0.86, 0.505), (0.88, 0.575), (0.66, 0.585)],
        "dark": 0.50, "floor": 0.30,
        "core": [(0.69, 0.525), (0.83, 0.520), (0.84, 0.565), (0.70, 0.570)],
    },
    {
        "name": "ear",
        "poly": [(0.00, 0.37), (0.10, 0.35), (0.12, 0.50), (0.05, 0.57),
                 (0.00, 0.52)],
        "dark": 0.45,
    },
    {
        "name": "jaw_right",
        "poly": [(0.70, 0.80), (0.86, 0.76), (0.82, 0.90), (0.70, 0.95),
                 (0.65, 0.88)],
        "dark": 0.45,
    },
    {
        "name": "moustache",
        "poly": [(0.29, 0.745), (0.50, 0.725), (0.70, 0.750), (0.68, 0.825),
                 (0.49, 0.805), (0.31, 0.825)],
        "dark": 0.55, "floor": 0.35,
        "core": [(0.34, 0.755), (0.50, 0.740), (0.66, 0.760), (0.64, 0.805),
                 (0.49, 0.790), (0.36, 0.810)],
    },
    {
        "name": "mouth",
        "poly": [(0.37, 0.825), (0.62, 0.815), (0.61, 0.865), (0.38, 0.875)],
        "dark": 0.45,
    },
    {
        "name": "beard",
        "poly": [(0.33, 0.855), (0.66, 0.845), (0.64, 0.925), (0.55, 0.995),
                 (0.44, 0.990), (0.35, 0.920)],
        "dark": 0.50, "floor": 0.35,
        "core": [(0.40, 0.880), (0.60, 0.875), (0.57, 0.940), (0.50, 0.975),
                 (0.43, 0.930)],
    },
]

# ---------------------------------------------------------------------------
# The three colourways. Same drawing in all three — that is the point of the
# sheet: the drawing is settled, only the press run changes. Each entry maps
# the five slots onto the three inks.
# ---------------------------------------------------------------------------
VARIANTS = [
    {
        "key": "D",
        "name": "Night field",
        "why": "Maroon ground, the head printed in flag red with cream lights "
               "and a red contour. The quietest of the three and the one that "
               "sits best on a dark concrete wall at low sector light.",
        "ink": {GROUND: INK_DARK, SHADOW: INK_DARK, MID: INK_RED,
                LIGHT: INK_CREAM, RIM: INK_RED, SUIT: INK_RED},
    },
    {
        "key": "E",
        "name": "Printed paper",
        "why": "Cream paper, the head in flag red, every feature and the "
               "contour in maroon. The literal two-plate agitation print: the "
               "highlights are the paper showing through.",
        "ink": {GROUND: INK_CREAM, SHADOW: INK_DARK, MID: INK_RED,
                LIGHT: INK_CREAM, RIM: INK_DARK, SUIT: INK_DARK},
    },
    {
        "key": "F",
        "name": "Red banner",
        "why": "Solid red field, the head in cream drawn in maroon. The "
               "loudest: it reads as RED from the far end of a corridor and "
               "the face still closes, because the contour is the dark ink.",
        "ink": {GROUND: INK_RED, SHADOW: INK_DARK, MID: INK_CREAM,
                LIGHT: INK_CREAM, RIM: INK_DARK, SUIT: INK_DARK},
    },
]

# ---------------------------------------------------------------------------
# Contact sheet layout (presentation only — none of this is in the lump).
# ---------------------------------------------------------------------------
PREVIEW_ZOOM = 2
PANEL_W = 300
PANEL_H = 540
SHEET_MARGIN = 28
SHEET_GAP = 26
SHEET_BG = (24, 24, 26)
SHEET_FG = (226, 226, 222)
SHEET_DIM = (150, 150, 146)
TITLE_H = 30
CAPTION_H = 76

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def _font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Masks
# ---------------------------------------------------------------------------
def _to_px(points_uv: list[tuple[float, float]], scale: int) -> list[tuple[float, float]]:
    return [((HEAD_X + u * HEAD_W) * scale, (HEAD_Y + v * HEAD_H) * scale)
            for u, v in points_uv]


def poly_mask(points_uv: list[tuple[float, float]]) -> np.ndarray:
    """Rasterise one hand-drawn outline into a hard-edged lump-sized mask.

    Drawn at SUPERSAMPLE, area-averaged down, then cut at 50%: the shape is
    as smooth as the drawing, the pixels are as hard as Doom needs.
    """
    big = Image.new("L", (LUMP_W * SUPERSAMPLE, LUMP_H * SUPERSAMPLE), 0)
    ImageDraw.Draw(big).polygon(_to_px(points_uv, SUPERSAMPLE), fill=255)
    small = big.resize((LUMP_W, LUMP_H), Image.BOX)
    return np.asarray(small) >= 128


def erode(mask: np.ndarray, steps: int, outside: bool = True) -> np.ndarray:
    """Shrink a mask by `steps` pixels.

    `outside` is what lies beyond the lump. True for the body contour, so a
    bust bleeding off the left and right edges does not grow a contour along
    the edge of the texture; False for ordinary shape cleanup.
    """
    out = mask
    for _ in range(steps):
        p = np.pad(out, 1, mode="constant", constant_values=outside)
        out = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1]
               & p[1:-1, :-2] & p[1:-1, 2:])
    return out


def dilate(mask: np.ndarray, steps: int) -> np.ndarray:
    out = mask
    for _ in range(steps):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1]
               | p[1:-1, :-2] | p[1:-1, 2:])
    return out


def consolidate(sel: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    """Turn a cloud of selected pixels into the single mark a brush would make.

    Close the holes, then keep only the largest connected component. A poster
    artist does not paint eleven freckles of shadow in an eye socket; they
    paint one socket. Everything is clipped back to `bounds` so a region can
    never spill into its neighbour.
    """
    sel = erode(dilate(sel, CLOSE_PX), CLOSE_PX, outside=False) & bounds
    if not sel.any():
        return sel
    labels = np.zeros(sel.shape, dtype=np.int32)
    ys, xs = np.nonzero(sel)
    best_label, best_size, label = 0, 0, 0
    for sy, sx in zip(ys, xs):
        if labels[sy, sx]:
            continue
        label += 1
        stack, size = [(sy, sx)], 0
        labels[sy, sx] = label
        while stack:
            y, x = stack.pop()
            size += 1
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if (0 <= ny < sel.shape[0] and 0 <= nx < sel.shape[1]
                        and sel[ny, nx] and not labels[ny, nx]):
                    labels[ny, nx] = label
                    stack.append((ny, nx))
        if size > best_size:
            best_size, best_label = size, label
    return labels == best_label


# ---------------------------------------------------------------------------
# The photograph, reduced to one clean luminance value per lump pixel
# ---------------------------------------------------------------------------
def head_luminance() -> np.ndarray:
    """Luminance of the source head, resampled onto the lump grid.

    Returns a LUMP_H x LUMP_W float array; everything outside the head box is
    left at zero and is never read (the bust is hand-painted).
    """
    src = Image.open(SOURCE).convert("L")
    w, h = src.size
    crop = src.crop((round(SRC_LEFT_F * w), round(SRC_TOP_F * h),
                     round(SRC_RIGHT_F * w), round(SRC_BOTTOM_F * h)))
    work = crop.resize((HEAD_W * SUPERSAMPLE, HEAD_H * SUPERSAMPLE), Image.LANCZOS)
    work = work.filter(ImageFilter.MedianFilter(MEDIAN_RADIUS))
    work = work.resize((HEAD_W, HEAD_H), Image.BOX)
    work = work.filter(ImageFilter.GaussianBlur(BLUR_PX))
    work = ImageOps.autocontrast(work, cutoff=1.0)

    lum = np.zeros((LUMP_H, LUMP_W), dtype=float)
    lum[HEAD_Y:HEAD_Y + HEAD_H, HEAD_X:HEAD_X + HEAD_W] = np.asarray(work, dtype=float)
    return lum


# ---------------------------------------------------------------------------
# The drawing
# ---------------------------------------------------------------------------
def draw_slots() -> np.ndarray:
    """Build the slot map: one of GROUND/SHADOW/MID/LIGHT/RIM per pixel."""
    lum = head_luminance()
    head = poly_mask(HEAD_UV)
    bust = poly_mask(BUST_UV)
    body = head | bust

    slots = np.full((LUMP_H, LUMP_W), GROUND, dtype=np.uint8)

    # --- the bust, hand-painted: the source has no information down there ---
    slots[bust] = SUIT
    slots[poly_mask(NECK_UV) & bust] = MID
    slots[poly_mask(UNDERCHIN_UV) & bust] = SHADOW   # shadow the jaw casts on the neck
    slots[poly_mask(SHIRT_UV) & bust] = LIGHT
    slots[poly_mask(TIE_UV) & bust] = SHADOW

    # --- the head: mid ink everywhere, then one region at a time ---
    slots[head] = MID
    for region in REGIONS:
        mask = poly_mask(region["poly"]) & head
        values = lum[mask]
        if values.size == 0:
            continue
        if "dark" in region:
            cut = np.percentile(values, region["dark"] * 100.0)
            slots[consolidate(mask & (lum <= cut), mask)] = SHADOW
        if "light" in region:
            cut = np.percentile(values, (1.0 - region["light"]) * 100.0)
            slots[consolidate(mask & (lum >= cut), mask)] = LIGHT

    # --- clean up the print, inside the body only ---
    filtered = np.asarray(
        Image.fromarray(slots).filter(ImageFilter.ModeFilter(DESPECKLE_SIZE)))
    slots = np.where(body, np.where(filtered == GROUND, MID, filtered), GROUND)
    slots = slots.astype(np.uint8)

    # --- safety net: a feature the photograph failed to yield is stamped ---
    for region in REGIONS:
        if "core" not in region:
            continue
        mask = poly_mask(region["poly"]) & head
        got = np.count_nonzero((slots == SHADOW) & mask)
        if mask.any() and got < region["floor"] * np.count_nonzero(mask):
            slots[poly_mask(region["core"]) & head] = SHADOW

    # --- the contour, last, so nothing can overwrite it ---
    slots[body & ~erode(body, RIM_PX)] = RIM

    # --- the slogan band stays flat ground ---
    slots[SLOGAN_BAND_TOP_PX:, :] = GROUND
    return slots


def render(slots: np.ndarray, variant: dict) -> Image.Image:
    rgb = np.zeros((LUMP_H, LUMP_W, 3), dtype=np.uint8)
    for slot, colour in variant["ink"].items():
        rgb[slots == slot] = colour
    return Image.fromarray(rgb, "RGB")


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------
def contact_sheet(arts: list[Image.Image]) -> Image.Image:
    art_w, art_h = LUMP_W * PREVIEW_ZOOM, LUMP_H * PREVIEW_ZOOM
    pad_x = (PANEL_W - art_w) // 2
    pad_y = (PANEL_H - art_h) // 2
    sheet_w = SHEET_MARGIN * 2 + PANEL_W * len(arts) + SHEET_GAP * (len(arts) - 1)
    sheet_h = SHEET_MARGIN * 2 + TITLE_H + PANEL_H + CAPTION_H
    sheet = Image.new("RGB", (sheet_w, sheet_h), SHEET_BG)
    d = ImageDraw.Draw(sheet)

    f_key, f_name, f_why = _font(22), _font(15), _font(12)

    for i, (art, variant) in enumerate(zip(arts, VARIANTS)):
        x = SHEET_MARGIN + i * (PANEL_W + SHEET_GAP)
        y = SHEET_MARGIN + TITLE_H
        d.text((x, SHEET_MARGIN), f"{variant['key']}  —  {variant['name']}",
               font=f_key, fill=SHEET_FG)
        panel = Image.new("RGB", (PANEL_W, PANEL_H), variant["ink"][GROUND])
        panel.paste(art.resize((art_w, art_h), Image.NEAREST), (pad_x, pad_y))
        sheet.paste(panel, (x, y))
        d.rectangle([x, y, x + PANEL_W - 1, y + PANEL_H - 1], outline=(70, 70, 74))

        ty = y + PANEL_H + 8
        d.text((x, ty), f"3 inks · {LUMP_W}x{LUMP_H} shown at {PREVIEW_ZOOM}x nearest",
               font=f_name, fill=SHEET_DIM)
        words, line, ly = variant["why"].split(), "", ty + 20
        for word in words:
            probe = (line + " " + word).strip()
            if d.textlength(probe, font=f_why) > PANEL_W:
                d.text((x, ly), line, font=f_why, fill=SHEET_DIM)
                ly += 14
                line = word
            else:
                line = probe
        if line:
            d.text((x, ly), line, font=f_why, fill=SHEET_DIM)

    note = (f"Bottom {LUMP_H - SLOGAN_BAND_TOP_PX} px left as flat ground on purpose: "
            "the Cyrillic slogan is set after the portrait is chosen.")
    d.text((SHEET_MARGIN, sheet_h - 22), note, font=f_name, fill=SHEET_DIM)
    return sheet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slots = draw_slots()
    arts = [render(slots, v) for v in VARIANTS]
    sheet = contact_sheet(arts)
    sheet.save(OUT_SHEET)
    print(f"wrote {OUT_SHEET.relative_to(PROJECT_ROOT)}  {sheet.size[0]}x{sheet.size[1]}")


if __name__ == "__main__":
    main()
