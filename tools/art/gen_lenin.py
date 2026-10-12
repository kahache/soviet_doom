#!/usr/bin/env python3
"""Lenin agitation poster (SDPOSTR1) — posterised from a public-domain photo.

Origin (a)+(b): procedural posterisation, in this script, of ONE free source
image — the July 1920 Lenin portrait by Pavel Zhukov (1870-1942), public
domain in Russia (author died 1942) and in the United States (published
before 1931). Rights verified in
`docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md` and recorded in
`docs/art/LICENSES.md`. No Soviet poster artwork is copied: the posters the
CEO sent are still protected, only the *technique* is reproduced here.

The technique: a 1970s agitation poster of this kind is a photograph
posterised to two or three flat inks. So: crop the head, flatten the film
grain, threshold the luminance at fixed levels, paint each level with one
colour taken from `docs/art/palette.json`. Hard edges, no gradients, no
dithering — Doom's palette and the 128x128 lump cannot carry them anyway.

Stage 1 (this script, current state): the DRAWING only, as an A/B/C variant
sheet for the CEO to choose from. No plaque, no wall texture, no palette
indexing, no Cyrillic slogan — the bottom band is left empty on purpose
because the text is decided after the portrait is chosen.

    .venv/bin/python tools/art/gen_lenin.py
        -> work/art/lenin/lenin_variants.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT_ROOT / "work" / "art" / "reference" / "lenin_1920_zhukov.jpg"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "lenin"
OUT_SHEET = OUT_DIR / "lenin_variants.png"

# ---------------------------------------------------------------------------
# Inks. Three colours of the mod palette, nothing else: a real silkscreen
# poster is printed with a countable number of inks and that is the whole
# look. Indices are into the ramps of docs/art/palette.json.
# ---------------------------------------------------------------------------
INK_DARK = artlib.ramp("flag_red")[1]     # 58,12,11  — near-black maroon: the shadow ink
INK_RED = artlib.ramp("flag_red")[13]     # 211,48,41 — flag red: the ground / mid ink
INK_CREAM = artlib.ramp("cream_yellow")[13]  # 230,218,163 — aged poster paper: the light ink

# ---------------------------------------------------------------------------
# Geometry. The lump is 128x128 (the CEO already accepted a wide format for
# SDSTAR1 for the same reason: at 64 the face would be unreadable). The art
# is rendered at the REAL 128x128 and shown at 2x nearest-neighbour, so what
# the CEO judges is literally the final pixels, with no later surprise when
# the texture is reduced.
# ---------------------------------------------------------------------------
LUMP_PX = 128
PREVIEW_ZOOM = 2                 # integer zoom only: non-integer nearest scaling makes uneven blocks
SLOGAN_BAND_PX = 17              # bottom strip kept clear of the portrait for the Cyrillic slogan (text decided later)
PORTRAIT_TOP_PX = 1              # a hair of air above the skull so the head does not touch the lump edge
PORTRAIT_SIDE_PX = 0             # full bleed sideways: the head is tall and narrow, so every pixel of width is needed

# Crop of the source photo, as fractions of its size so the numbers survive a
# different scan of the same negative. Full width, and vertically from just
# above the skull to the start of the shoulders: the head is far taller than
# it is wide (roughly 2:3), so the only way to make it big in a square lump is
# to spend the whole width on it. Everything below the shoulders is dark suit,
# which posterises into a shapeless mass and would only eat the slogan band.
CROP_LEFT_F = 0.000
CROP_RIGHT_F = 1.000
CROP_TOP_F = 0.040
CROP_BOTTOM_F = 0.672

# ---------------------------------------------------------------------------
# Flattening the photograph before thresholding. Thresholding raw film grain
# gives pepper noise, not a poster; these three steps are what turn a
# continuous-tone negative into printable flat shapes.
# ---------------------------------------------------------------------------
WORK_PX = 384                    # work above the lump size, then area-average down: cheap anti-alias before the hard cut
MEDIAN_RADIUS = 5                # kills the 1920 emulsion grain and the skin freckles while keeping the big edges
BLUR_RADIUS = 1.4                # softens what is left so the threshold line is a smooth contour, not a ragged one
AUTOCONTRAST_CUTOFF = 1.0        # % clipped at each end: spreads a flat 1920 negative over the full range so fixed thresholds mean the same thing
DESPECKLE_SIZE = 3               # mode filter on the flat result: removes isolated pixels left by the cut; 3 is the largest that does not eat the eyelids

# Elliptical falloff around the head, applied to the luminance before the cut.
# The photo's backdrop is a mid-grey vignette that would break into blotches
# at the threshold. Pushing the corners down guarantees the backdrop reads as
# one flat ground, which is exactly what the poster artist did with a brush.
VIGNETTE_RX = 0.74               # ellipse radii as a fraction of the crop; the head edge sits at ~0.38, so it is never touched
VIGNETTE_RY = 0.82
VIGNETTE_FALLOFF = 0.90          # how hard the outside is darkened (1.0 = to black at the corners)

# Backdrop control. The 1920 studio backdrop is not flat: there is a lighter
# halo to the right of the head that crosses the threshold and prints as two
# floating blotches. A poster artist cut the head out of the backdrop, so we
# do the same — anything outside the horizontal band occupied by the head is
# forced to the ground ink. The band is measured from the lightest ink's
# largest blob (the lit face) and widened, never hard-coded.
HEAD_BAND_MARGIN_PX = 20         # widening each side: the shadow half of the head extends past the lit half
MIN_BLOB_PX = 10                 # components smaller than this are print dust; merged into their commonest neighbour

# ---------------------------------------------------------------------------
# The three variants. Thresholds are on the autocontrasted luminance, 0-255.
# Band 0 is always the ground ink, so the backdrop and the deepest shadows are
# the same colour — that is what makes a posterised head read as printed on a
# field rather than pasted onto one.
# ---------------------------------------------------------------------------
VARIANTS = [
    {
        "key": "A",
        "name": "Two inks, hard cut",
        "why": "Cream on near-black maroon. The loudest, most graphic reading: "
               "pure chiaroscuro, no mid tone. Holds up at any sector light level.",
        "ground": INK_DARK,
        # (threshold, colour) pairs: a pixel takes the colour of the first band it falls under
        "bands": [(132, INK_DARK), (256, INK_CREAM)],
    },
    {
        "key": "B",
        "name": "Three inks, mid tone",
        "why": "Maroon shadow, flag red mid tone, cream highlight. The most "
               "photographic and the most recognisable face: the red does the "
               "modelling of the skull and the cheek.",
        "ground": INK_DARK,
        "bands": [(88, INK_DARK), (158, INK_RED), (256, INK_CREAM)],
    },
    {
        "key": "C",
        "name": "Cream on full red",
        "why": "Two inks again, but the dark one is flag red: a solid red field "
               "with the lit face in cream. The classic agitation banner — it "
               "reads as RED from the far end of a corridor.",
        "ground": INK_RED,
        "bands": [(124, INK_RED), (256, INK_CREAM)],
    },
]

# ---------------------------------------------------------------------------
# Contact sheet layout (presentation only — none of this is in the lump).
# ---------------------------------------------------------------------------
PANEL_PX = 320                   # the brief's panel size; 128 * 2 art centred inside it
SHEET_MARGIN = 28
SHEET_GAP = 28
SHEET_BG = (24, 24, 26)
SHEET_FG = (226, 226, 222)
SHEET_DIM = (150, 150, 146)
TITLE_H = 30
CAPTION_H = 56

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def flattened_luminance() -> Image.Image:
    """Crop the head and turn the photograph into clean, grain-free tones."""
    src = Image.open(SOURCE).convert("L")
    w, h = src.size

    box_l, box_r = CROP_LEFT_F * w, CROP_RIGHT_F * w
    box_t, box_b = CROP_TOP_F * h, CROP_BOTTOM_F * h

    # Force the crop to the aspect of the portrait area of the lump, growing
    # the short side around the centre so the framing above stays honest.
    target_w = LUMP_PX - 2 * PORTRAIT_SIDE_PX
    target_h = LUMP_PX - SLOGAN_BAND_PX - PORTRAIT_TOP_PX
    target_aspect = target_w / target_h
    cw, ch = box_r - box_l, box_b - box_t
    cx, cy = (box_l + box_r) / 2, (box_t + box_b) / 2
    if cw / ch > target_aspect:
        ch = cw / target_aspect
    else:
        cw = ch * target_aspect
    src = src.crop((round(cx - cw / 2), round(cy - ch / 2),
                    round(cx + cw / 2), round(cy + ch / 2)))

    work_h = round(WORK_PX / target_aspect)
    src = src.resize((WORK_PX, work_h), Image.LANCZOS)
    src = src.filter(ImageFilter.MedianFilter(MEDIAN_RADIUS))
    src = src.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
    src = ImageOps.autocontrast(src, cutoff=AUTOCONTRAST_CUTOFF)

    # Elliptical falloff: multiply, never add, so the lit face keeps its values.
    px = src.load()
    for y in range(work_h):
        ny = (y / (work_h - 1) - 0.5) / VIGNETTE_RY
        for x in range(WORK_PX):
            nx = (x / (WORK_PX - 1) - 0.5) / VIGNETTE_RX
            d = (nx * nx + ny * ny) ** 0.5
            if d > 1.0:
                k = max(0.0, 1.0 - VIGNETTE_FALLOFF * min(1.0, (d - 1.0) / 0.55))
                px[x, y] = int(px[x, y] * k)
    return src


def posterise(lum: Image.Image, variant: dict) -> Image.Image:
    """One variant of the 128x128 lump art: flat inks, hard edges."""
    target_w = LUMP_PX - 2 * PORTRAIT_SIDE_PX
    target_h = LUMP_PX - SLOGAN_BAND_PX - PORTRAIT_TOP_PX
    small = lum.resize((target_w, target_h), Image.LANCZOS)

    # Map each luminance band to an ink index, then mode-filter the INDEX map
    # (filtering colours would invent in-between colours; filtering indices
    # cannot) and finally paint.
    bands = variant["bands"]
    idx = Image.new("L", small.size)
    sp, ip = small.load(), idx.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            v = sp[x, y]
            for i, (limit, _) in enumerate(bands):
                if v < limit:
                    ip[x, y] = i
                    break
    idx = idx.filter(ImageFilter.ModeFilter(DESPECKLE_SIZE))

    art = Image.new("RGB", (LUMP_PX, LUMP_PX), variant["ground"])
    portrait = Image.new("RGB", small.size)
    pp, ip = portrait.load(), idx.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            pp[x, y] = bands[ip[x, y]][1]
    art.paste(portrait, (PORTRAIT_SIDE_PX, PORTRAIT_TOP_PX))
    return art


def contact_sheet(arts: list[Image.Image]) -> Image.Image:
    art_px = LUMP_PX * PREVIEW_ZOOM
    pad = (PANEL_PX - art_px) // 2
    sheet_w = SHEET_MARGIN * 2 + PANEL_PX * len(arts) + SHEET_GAP * (len(arts) - 1)
    sheet_h = SHEET_MARGIN * 2 + TITLE_H + PANEL_PX + CAPTION_H
    sheet = Image.new("RGB", (sheet_w, sheet_h), SHEET_BG)
    d = ImageDraw.Draw(sheet)

    f_key = _font(22)
    f_name = _font(15)
    f_why = _font(12)

    for i, (art, variant) in enumerate(zip(arts, VARIANTS)):
        x = SHEET_MARGIN + i * (PANEL_PX + SHEET_GAP)
        y = SHEET_MARGIN + TITLE_H
        d.text((x, SHEET_MARGIN), f"{variant['key']}  —  {variant['name']}",
               font=f_key, fill=SHEET_FG)
        panel = Image.new("RGB", (PANEL_PX, PANEL_PX), variant["ground"])
        panel.paste(art.resize((art_px, art_px), Image.NEAREST), (pad, pad))
        sheet.paste(panel, (x, y))
        d.rectangle([x, y, x + PANEL_PX - 1, y + PANEL_PX - 1], outline=(70, 70, 74))

        ty = y + PANEL_PX + 8
        d.text((x, ty), f"{len(set(c for _, c in variant['bands']))} inks · "
                        f"{LUMP_PX}x{LUMP_PX} shown at {PREVIEW_ZOOM}x nearest",
               font=f_name, fill=SHEET_DIM)
        # wrap the rationale by hand: no textwrap-aware draw in PIL
        words, line, ly = variant["why"].split(), "", ty + 20
        for word in words:
            probe = (line + " " + word).strip()
            if d.textlength(probe, font=f_why) > PANEL_PX:
                d.text((x, ly), line, font=f_why, fill=SHEET_DIM)
                ly += 14
                line = word
            else:
                line = probe
        if line:
            d.text((x, ly), line, font=f_why, fill=SHEET_DIM)

    return sheet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lum = flattened_luminance()
    arts = [posterise(lum, v) for v in VARIANTS]
    sheet = contact_sheet(arts)
    sheet.save(OUT_SHEET)
    print(f"wrote {OUT_SHEET.relative_to(PROJECT_ROOT)}  {sheet.size[0]}x{sheet.size[1]}")


if __name__ == "__main__":
    main()
