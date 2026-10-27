#!/usr/bin/env python3
"""The end-of-episode illustrations (V3 B2, D132): Gemini paintings -> SDEND1-3, 320x200.

    .venv/Scripts/python.exe tools/art/gen_endings.py                 # the three + the CEO's preview
    .venv/Scripts/python.exe tools/art/gen_endings.py --install       # ... and copy them to assets/
    .venv/Scripts/python.exe tools/art/gen_endings.py --ref-dir <main checkout>/work/art/reference

The paintings are the project lead's Gemini images (D77: local only, never
committed or shipped), one per episode end, shown full screen after the
episode's ending text (MAPINFO `Intermission SD_EndingN`, MOD-SPEC 6.14):

  SDEND1  gemini_ending_ep1.jfif     Tankograd: the sergeant pulls the breaker,
                                     the portal goes dark, the invaders march
                                     on Moscow; a fallen Reich soldier in front.
  SDEND2  gemini_ending_ep2_v2.jfif  Red Square: our Liberty Colossus thrown
                                     down (chrome plates, US patch, tablet,
                                     pink flesh at the joints), the banner.
  SDEND3  gemini_ending_ep3_v3.jfif  Tunguska: the sergeant raises the banner
                                     between the Consortium's two halves.

The v2 paintings of episodes 2 and 3 were asked of Gemini with our enemy
sheets attached, after the CEO judged the first round's enemies wrong ("no
han dibujado bien los enemigos", "they did not draw the enemies right").
The superseded first round is shown small in the preview as a reference.
Episode 3's v3 (D135, 2026-10-27): the CEO approved SDEND1 and SDEND2 and saw
in the v2 painting that the Legion half carried the chest piece (the cracked
core) the Reich half already had; the v3 painting, asked of Gemini by the PM,
keeps the composition and draws the chest piece once.

The pipeline is gen_titlepic.py's (D126), the one the CEO approved:

  1. symbol   - the D12 symbol painted on the Reich's armband at the
                painting's own resolution, the way the enemies and the title
                screen got it (D108/D114/D128): armband_symbol's field finder
                (`ring`: Gemini's white square OUTLINE on red becomes one
                white field; `white`: a filled white square) and its warp
                along the arm. Episode 1 (the fallen soldier, bottom right;
                the CEO asked for it, "a la primera le falta una esvastica en
                el brazalete", "the first one lacks a swastika on the
                armband") and episode 3 (the Consortium's Reich half).
     5b (after the resize) draws the field and the symbol again at the
                screen's own pixels through the same warp, super-sampled, and
                snaps them without dither: at 7 screen px (episode 1) the
                reduction alone left a blob.
  2. clean    - Gemini's red scribble of a signature (bottom right) filled
                from its surroundings where the window keeps it.
  3. pad      - a 320x200 screen is shown at 4:3, so the window must be 4:3:
                where the painting is wider than the window may cut, rows are
                added above (its own top rows mirrored, blurred to sky) and
                below (the ground mirrored, blurred, darkened).
  4. crop     - the 4:3 window keeping what matters (per episode, below).
  5. resize   - Lanczos to 320x200 (the 1.2 vertical squash of a Doom screen
                is the 4:3 window itself), light unsharp mask.
  6. palette  - palette v3 (D128: its reich_greygreen ramp keeps the Reich
                skin grey-green, as on the Consortium's sprites), nearest colour in CIELAB with gen_titlepic's 4x4
                Bayer dither: the TITLEPIC's look, indexed.

Outputs in work/art/endings_gemini/ (gitignored): SDEND1-3.png (indexed,
what --install copies to assets/graphics/endings/), raw_*.png (before the
palette), armband_*.png (the painted band at source resolution, before and
after) and manifest.json; the preview
docs/art/previews/2026-10-25_V3_episode-endings.html (English, D129).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
import artlib  # noqa: E402
import gen_titlepic as gt  # noqa: E402
import palette  # noqa: E402

ROOT = artlib.PROJECT_ROOT
REF_DIR = ROOT / "work" / "art" / "reference"
OUT_DIR = ROOT / "work" / "art" / "endings_gemini"
INSTALL_DIR = ROOT / "assets" / "graphics" / "endings"
PREVIEW = ROOT / "docs" / "art" / "previews" / "2026-10-25_V3_episode-endings.html"

SCREEN = gt.SCREEN                 # (320, 200)
DISPLAY_ASPECT = gt.DISPLAY_ASPECT  # 4:3
UNSHARP = gt.UNSHARP
SYMBOL_SEED = 132                  # D132: the armband's grain is seeded, the build repeatable
SCREEN_REACH = 1.0                 # 5b: x the field's radius the symbol's tips reach when drawn at
                                   # screen px (armband_symbol's 0.82 left a dark dot in a 7-px field;
                                   # at 1.0 the arms show; compared 2026-10-25 at tilts 0-45)

# 1. the armband: where Gemini put it, how to find its field, the arm's axis
@dataclass(frozen=True)
class Armband:
    box: tuple[int, int, int, int]  # source px (x0, y0, x1, y1) searched for the field
    how: str                        # armband_symbol.select_fields mode
    hint_deg: float                 # the arm's axis toward the shoulder, screen degrees
    field_max: int                  # source px: the longest field accepted


# 2. the signature: red strokes in this box are filled from round them
SIG_RED_MARGIN = 45                # a stroke pixel's R over its G and B by this much
SIG_GROW = 2                       # px the stroke mask grows (its soft edge)
SIG_FILL_ITERS = 60                # diffusion steps of the fill
# 3. pad. Two ways to make the added rows:
#   mirror - the edge rows mirrored and blurred (a cloudy sky: episode 2);
#   extend - each column's edge colour carried outward, blurred across, fading
#            to the sky's (or the ground's) darkest; seeded stars in a night
#            sky (episode 3: a mirror would copy the banner and the fires).
PAD_MODES = ("mirror", "extend")
PAD_BLUR = 14.0                    # px: the mirrored rows become sky / ground, not a copy
PAD_SEAM = 20                      # source px blended across each seam
PAD_TOP_DARK = 0.80                # mirror: x at the very top of the top pad (1.0 at its seam)
PAD_BOTTOM_DARK = 0.55             # x at the very bottom of the bottom pad
PAD_CAP_PCT = 70                   # mirror: the top pad's luminance capped at this percentile of itself
EDGE_ROWS = 14                     # extend: rows averaged into a column's edge colour
EDGE_BLUR_X = 40.0                 # extend: px of horizontal blur of the edge colours
EDGE_FADE = 0.55                   # extend: fraction of the pad over which the edge fades out
EDGE_RED_MARGIN = 50               # extend: a red pixel (the banner) is left out of the edge colour
STARS_PER_MPX = 180                # extend, top: stars per million px of pad (the painting's sky has ~this)
STAR_RADIUS = (1.0, 2.2)           # source px
STAR_RGB = (226, 232, 255)


@dataclass(frozen=True)
class Ending:
    lump: str
    episode: int
    ref: str                        # under REF_DIR
    window: tuple[int, int]         # source x0, x1 of the 4:3 window
    pad_top: int                    # source rows added above
    pad_bottom: int                 # ... and below
    keeps: str                      # what the window keeps (the preview says it)
    pad_mode: str = "mirror"        # PAD_MODES
    palette_version: int = 3        # palette v3 (D128): the Reich skin's grey-green ramp
    armband: Armband | None = None
    signature: tuple[int, int, int, int] | None = None
    superseded: str | None = None   # the first round's painting (the preview's reference)


ENDINGS = (
    # 1312x816: a 4:3 window is 1088 wide at full height; x 150 keeps the
    # breaker's lever and the fallen Reich soldier's armband (x 1122-1146).
    Ending("SDEND1", 1, "gemini_ending_ep1.jfif", (150, 1238), 0, 0,
           "the breaker and its lever, the sergeant, the dying portal, the column "
           "marching out to Moscow, the Legion and Reich dead with the armband",
           armband=Armband((1080, 680, 1200, 790), "ring", 80.0, 60),
           signature=(1262, 760, 1312, 806)),
    # 1376x768: from the crown's left spike (x ~245) to the portal (x ~1300)
    # is 1080 px, so 42 rows of sky are added above: 1080 x 810 is 4:3.
    Ending("SDEND2", 2, "gemini_ending_ep2_v2.jfif", (235, 1315), 42, 0,
           "the whole Colossus (crown to torch, the US patch, the tablet), the "
           "sergeant and the banner, the Kremlin tower, St Basil's, the portal",
           signature=(1295, 718, 1362, 768), superseded="gemini_ending_ep2.jfif"),
    # 1312x816 (v3, D135: the chest piece drawn once, the Legion half's opened
    # chest; the v2 painting gave both halves the same piece). Both halves and their helmets span
    # x 96-1312 (the Legion's projector runs off the right edge, as in v2),
    # so 1216 wide needs 912 rows: 60 of sky above, 36 of ground below.
    Ending("SDEND3", 3, "gemini_ending_ep3_v3.jfif", (96, 1312), 60, 36,
           "the sergeant and the banner before the imploding portal, the Reich "
           "half with its armband and rocket tubes, the Legion half with its "
           "opened chest, projector and US patch, both helmets",
           pad_mode="extend",
           armband=Armband((250, 550, 430, 700), "white", 120.0, 90),
           superseded="gemini_ending_ep3.jfif"),
)


# ------------------------------------------------------------------ steps
def load(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB")).copy()


def paint_armband(rgb: np.ndarray, band: Armband) -> tuple[np.ndarray, dict]:
    """The symbol on the armband in `band.box` (armband_symbol's fields + warp)."""
    import armband_symbol as ab
    x0, y0, x1, y1 = band.box
    crop = rgb[y0:y1, x0:x1].copy()
    mask = np.ones(crop.shape[:2], bool)
    filled, fields = ab.select_fields(crop, mask, band.how, field_max=band.field_max)
    if not fields and band.how == "ring":          # a band in shade (gen_titlepic's fallback)
        filled, fields = gt.shaded_ring(crop)
    if not fields:
        raise RuntimeError(f"no armband field in {band.box} ({band.how})")
    field = max(fields, key=lambda f: int(f.sum()))   # the square, not a stray
    painted, info = ab.paint_symbol(filled, mask, hint_deg=band.hint_deg, seed=SYMBOL_SEED, fields=[field])
    out = rgb.copy()
    out[y0:y1, x0:x1] = painted
    ys, xs = np.nonzero(field)
    report = {"field_px": int(field.sum()), "how": band.how, "hint_deg": band.hint_deg,
              "box": [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0],
              "ink_px": round(info.ink_px, 1), "sigma": round(info.sigma, 2)}
    painted_band = PaintedBand(band.box, field, info.frames[0],
                               filled[field].astype(float).mean(axis=0), ab.ink_colour(crop, mask))
    return out, report, painted_band


@dataclass(frozen=True)
class PaintedBand:
    """What step 5b needs to draw the symbol again at the screen's pixels."""
    box: tuple[int, int, int, int]  # the crop the field and the arm frame are measured in
    field: np.ndarray               # bool, crop px
    frame: object                   # armband_symbol.ArmFrame, crop px
    white: np.ndarray               # the field's own (shaded) white, RGB
    ink: np.ndarray                 # Gemini's black on that figure, RGB


def screen_to_source(end: Ending, sx: np.ndarray, sy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Screen px (continuous, pixel centres at +0.5) -> painting px (pixel centres at integers)."""
    x0, x1 = end.window
    kx = SCREEN[0] / (x1 - x0)
    ky = SCREEN[1] / ((x1 - x0) / DISPLAY_ASPECT)
    return x0 + sx / kx - 0.5, sy / ky - 0.5 - end.pad_top


def crisp_symbol(img: np.ndarray, end: Ending, band: PaintedBand) -> tuple[np.ndarray, np.ndarray]:
    """5b: the field and its symbol drawn again at the screen's own pixels,
    super-sampled through the same arm frame (armband_symbol's warp): a field
    of 7 screen px still shows the four arms, where the reduction alone left
    a blob. Returns the picture and each pixel's field coverage."""
    import armband_symbol as ab
    bx0, by0, bx1, by1 = band.box
    ys, xs = np.nonzero(band.field)
    corners = np.array([[xs.min() + bx0, ys.min() + by0], [xs.max() + bx0 + 1, ys.max() + by0 + 1]], float)
    x0, x1 = end.window
    kx = SCREEN[0] / (x1 - x0)
    ky = SCREEN[1] / ((x1 - x0) / DISPLAY_ASPECT)
    px0, px1 = int(np.floor((corners[0, 0] - x0) * kx)) - 1, int(np.ceil((corners[1, 0] - x0) * kx)) + 1
    py0 = int(np.floor((corners[0, 1] + end.pad_top) * ky)) - 1
    py1 = int(np.ceil((corners[1, 1] + end.pad_top) * ky)) + 1
    px0, py0 = max(px0, 0), max(py0, 0)
    px1, py1 = min(px1, SCREEN[0]), min(py1, SCREEN[1])
    ss = ab.SUPERSAMPLE
    off = (np.arange(ss) + 0.5) / ss
    gy, gx = np.mgrid[py0:py1, px0:px1].astype(float)
    fsum = np.zeros(gy.shape)
    isum = np.zeros(gy.shape)
    fh, fw = band.field.shape
    for oy in off:
        for ox in off:
            sx, sy = screen_to_source(end, gx + ox, gy + oy)
            cx, cy = sx - bx0, sy - by0
            ix, iy = np.rint(cx).astype(int), np.rint(cy).astype(int)
            inside = (ix >= 0) & (iy >= 0) & (ix < fw) & (iy < fh)
            f = np.zeros(gy.shape, bool)
            f[inside] = band.field[iy[inside], ix[inside]]
            ink = ab.symbol_ink(*ab._surface(cx, cy, band.frame), ab.TILT_DEG, SCREEN_REACH) & f
            fsum += f
            isum += ink
    ff, ic = fsum / ss ** 2, isum / ss ** 2
    out = img.copy()
    sub = out[py0:py1, px0:px1]
    sub[:] = sub * (1 - ff[..., None]) + band.white * (ff - ic)[..., None] + band.ink * ic[..., None]
    cover = np.zeros(img.shape[:2])
    cover[py0:py1, px0:px1] = ff
    return out, cover


def _grow(mask: np.ndarray, r: int) -> np.ndarray:
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def clean_signature(rgb: np.ndarray, box: tuple[int, int, int, int]) -> tuple[np.ndarray, int]:
    """Gemini's red scribble filled by diffusion from the pixels round it."""
    x0, y0, x1, y1 = box
    a = rgb[y0:y1, x0:x1].astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    stroke = (r - np.maximum(g, b)) > SIG_RED_MARGIN
    hole = _grow(stroke, SIG_GROW)
    hole[0, :] = hole[-1, :] = hole[:, 0] = hole[:, -1] = False   # the border stays the known ring
    fill = a.copy()
    fill[hole] = a[~hole].mean(axis=0)
    for _ in range(SIG_FILL_ITERS):
        avg = (np.roll(fill, 1, 0) + np.roll(fill, -1, 0) + np.roll(fill, 1, 1) + np.roll(fill, -1, 1)) / 4
        fill[hole] = avg[hole]
    out = rgb.copy()
    out[y0:y1, x0:x1] = np.clip(fill + 0.5, 0, 255).astype(np.uint8)
    return out, int(hole.sum())


def _mirror_pad(rows: np.ndarray, n: int, dark_end: float, cap_pct: float | None) -> np.ndarray:
    """n rows made from `rows` (the edge rows, nearest the seam first): mirrored,
    blurred, optionally capped in luminance, darkened toward the far edge."""
    src = rows.astype(float)
    pad = gt.gaussian(src, PAD_BLUR)
    if cap_pct is not None:
        lum = pad @ np.array([0.299, 0.587, 0.114])
        cap = np.percentile(lum, cap_pct)
        pad *= np.minimum(1.0, cap / np.maximum(lum, 1e-6))[..., None]
    pad *= np.linspace(1.0, dark_end, n)[:, None, None]
    return pad


def _edge_colours(rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Each column's colour at an edge: the mean of `rows` leaving out the
    banner's red, blurred across."""
    a = rows.astype(float)
    red = (a[..., 0] - np.maximum(a[..., 1], a[..., 2])) > EDGE_RED_MARGIN
    w = (~red).astype(float)[..., None]
    col = (a * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1.0)
    dark = np.percentile(a.reshape(-1, 3), 5, axis=0)
    col[(w.sum(axis=0) == 0)[:, 0]] = dark
    blurred = gt.gaussian(np.repeat(col[None], 8, axis=0), EDGE_BLUR_X)[4]
    return blurred, dark


def _extend_pad(rows: np.ndarray, n: int, dark_end: float) -> np.ndarray:
    """n rows, the seam row first: the edge colour fading to the edge's darkest."""
    edge, dark = _edge_colours(rows)
    t = np.clip(np.arange(n, dtype=float) / max(1.0, EDGE_FADE * n), 0, 1)[:, None, None]
    t = t * t * (3 - 2 * t)
    pad = edge[None] * (1 - t) + dark[None, None] * t
    return pad * np.linspace(1.0, dark_end, n)[:, None, None]


def _stars(pad: np.ndarray, seed: int) -> np.ndarray:
    """Seeded soft stars, fewer near the seam (where the painting's glow is)."""
    h, w = pad.shape[:2]
    rng = np.random.default_rng(seed)
    count = int(round(STARS_PER_MPX * h * w / 1e6))
    yy, xx = np.mgrid[0:h, 0:w]
    out = pad.copy()
    star = np.array(STAR_RGB, float)
    for _ in range(count):
        cy, cx = rng.uniform(0, h * 0.85), rng.uniform(0, w)
        r = rng.uniform(*STAR_RADIUS)
        a = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * (r / 2) ** 2)) * rng.uniform(0.5, 1.0)
        out = out * (1 - a[..., None]) + star * a[..., None]
    return out


def pad_rows(rgb: np.ndarray, top: int, bottom: int, mode: str = "mirror") -> np.ndarray:
    """Rows of sky added above and ground below, blended at the seams (PAD_MODES)."""
    if mode not in PAD_MODES:
        raise ValueError(f"unknown pad mode {mode!r}")
    out = rgb.astype(float)
    if top:
        if mode == "mirror":
            sky = _mirror_pad(rgb[:top], top, PAD_TOP_DARK, PAD_CAP_PCT)
        else:
            sky = _stars(_extend_pad(rgb[:EDGE_ROWS], top, 1.0), SYMBOL_SEED)
        sky = sky[::-1]                                    # far edge at row 0
        seam = min(PAD_SEAM, top)
        for i in range(seam):
            t = (i + 1) / (seam + 1)
            out[i] = sky[-1] * (1 - t) + out[i] * t
        out = np.concatenate([sky, out], axis=0)
    if bottom:
        if mode == "mirror":
            ground = _mirror_pad(rgb[-bottom:][::-1], bottom, PAD_BOTTOM_DARK, None)
        else:
            ground = _extend_pad(rgb[-EDGE_ROWS:][::-1], bottom, PAD_BOTTOM_DARK)
        seam = min(PAD_SEAM, bottom)
        for i in range(seam):
            t = (i + 1) / (seam + 1)
            out[-1 - i] = ground[0] * (1 - t) + out[-1 - i] * t
        out = np.concatenate([out, ground], axis=0)
    return out


def frame(rgb: np.ndarray, end: Ending) -> np.ndarray:
    padded = pad_rows(rgb, end.pad_top, end.pad_bottom, end.pad_mode)
    x0, x1 = end.window
    h = padded.shape[0]
    w = x1 - x0
    if abs(w / h - DISPLAY_ASPECT) > 0.005:
        raise ValueError(f"{end.lump}: window {w}x{h} is not 4:3")
    if x0 < 0 or x1 > padded.shape[1]:
        raise ValueError(f"{end.lump}: window {end.window} outside the painting ({padded.shape[1]} wide)")
    win = Image.fromarray(np.clip(padded[:, x0:x1] + 0.5, 0, 255).astype(np.uint8))
    small = win.resize(SCREEN, Image.LANCZOS)
    r, p, t = UNSHARP
    small = small.filter(ImageFilter.UnsharpMask(radius=r, percent=p, threshold=t))
    return np.asarray(small).astype(float)


def source_to_screen(end: Ending, x: float, y: float) -> tuple[float, float]:
    """A painting pixel's place on the 320x200 screen (for the preview's zooms)."""
    x0, x1 = end.window
    k = SCREEN[0] / (x1 - x0)
    ky = SCREEN[1] / ((x1 - x0) / DISPLAY_ASPECT)
    return (x - x0) * k, (y + end.pad_top) * ky


# ------------------------------------------------------------------ build
def render(end: Ending, ref_dir: Path = REF_DIR) -> tuple[Image.Image, dict, dict]:
    """(indexed 320x200 picture, manifest entry, intermediate images)."""
    src = load(ref_dir / end.ref)
    entry = {"source": end.ref, "source_size": list(src.shape[1::-1]), "window": list(end.window),
             "pad_top": end.pad_top, "pad_bottom": end.pad_bottom, "keeps": end.keeps}
    extra = {}
    pic = src
    band = None
    if end.armband is not None:
        pic, info, band = paint_armband(pic, end.armband)
        entry["armband"] = info
        x0, y0, x1, y1 = end.armband.box
        extra["armband_before"] = src[y0:y1, x0:x1]
        extra["armband_after"] = pic[y0:y1, x0:x1]
    if end.signature is not None:
        pic, n = clean_signature(pic, end.signature)
        entry["signature_px_filled"] = n
    img = frame(pic, end)
    cover = np.zeros(img.shape[:2])
    if band is not None:
        img, cover = crisp_symbol(img, end, band)
    extra["raw"] = np.clip(img + 0.5, 0, 255).astype(np.uint8)
    pal = np.array(palette.colours(end.palette_version), np.int64)
    idx = gt.snap(img, pal)
    if cover.any():                                    # the field without dither: clean ink edges
        clean = gt.snap(img, pal, dither=0.0)
        idx = np.where(cover > 0, clean, idx)
    final = gt.indexed(idx, pal)
    entry["colours"] = len(set(np.asarray(final).ravel().tolist()))
    entry["palette"] = (f"docs/art/palette.json v{end.palette_version} ({len(pal)}), "
                        f"CIELAB nearest, Bayer 4x4 +-{gt.DITHER_AMP}")
    return final, entry, extra


def build(out_dir: Path = OUT_DIR, ref_dir: Path = REF_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"decision": "D132 (V3 B2)", "files": {}}
    for end in ENDINGS:
        final, entry, extra = render(end, ref_dir)
        final.save(out_dir / f"{end.lump}.png", optimize=True)
        Image.fromarray(extra["raw"]).save(out_dir / f"raw_{end.lump}.png")
        if "armband_after" in extra:
            Image.fromarray(extra["armband_before"]).save(out_dir / f"armband_{end.lump}_before.png")
            Image.fromarray(extra["armband_after"]).save(out_dir / f"armband_{end.lump}_after.png")
        manifest["files"][f"{end.lump}.png"] = entry
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    return manifest


def install(out_dir: Path = OUT_DIR, dest: Path = INSTALL_DIR) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    done = []
    for end in ENDINGS:
        target = dest / f"{end.lump}.png"
        shutil.copyfile(out_dir / f"{end.lump}.png", target)
        done.append(target)
    return done


# ---------------------------------------------------------------- preview
def _b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _zoom(img: Image.Image, k: int) -> Image.Image:
    return img.convert("RGB").resize((img.width * k, img.height * k), Image.NEAREST)


ARMBAND_ZOOM = 6
ARMBAND_CROP = 34                  # screen px square round the armband in the x6 zoom
SHOT_ZOOM = 3
THUMB_W = 330                      # px: the paintings shown small


def _armband_zoom(end: Ending, pic: Image.Image, info: dict) -> Image.Image:
    bx0, by0, bx1, by1 = info["box"]
    cx, cy = source_to_screen(end, (bx0 + bx1) / 2, (by0 + by1) / 2)
    h = ARMBAND_CROP // 2
    x0 = int(min(max(0, round(cx) - h), SCREEN[0] - ARMBAND_CROP))
    y0 = int(min(max(0, round(cy) - h), SCREEN[1] - ARMBAND_CROP))
    return _zoom(pic.crop((x0, y0, x0 + ARMBAND_CROP, y0 + ARMBAND_CROP)), ARMBAND_ZOOM)


def _thumb(path: Path) -> Image.Image:
    with Image.open(path) as im:
        im = im.convert("RGB")
        return im.resize((THUMB_W, round(im.height * THUMB_W / im.width)), Image.LANCZOS)


CSS = """
:root{--bg:#16171b;--panel:#202227;--ink:#e9e6df;--muted:#a7a39a;--red:#c8312a;--line:#34363d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}
p,li{color:var(--ink)}.muted{color:var(--muted)}
img{image-rendering:pixelated;image-rendering:crisp-edges;display:block;max-width:100%;height:auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;margin:14px 0}
.row{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start}
.tag{display:inline-block;font:12px ui-monospace,Consolas,monospace;background:#2c2e35;border-radius:4px;padding:1px 6px}
.seq{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}
.step{background:#2a2c33;border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:14px}
.step.new{border-color:var(--red);box-shadow:0 0 0 1px var(--red) inset}
.arrow{color:var(--muted)}
.smooth{image-rendering:auto}
table{border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
"""

SEQUENCE = (
    ("Stats", "kills, items, secrets, time over the operations map (ADR 013, B1)", False),
    ("Awards", "the five medals revealed one by one (ADR 013, B3); a key shows all, the next leaves", False),
    ("Ending text", "the cluster's SD_ENDnn_TEXT over SDFLR1, as today", False),
    ("Illustration", "SDEND1/2/3 full screen, 4:3, no text over it; waits for a key", True),
    ("Title screen", "TITLEPIC and the title music, as today", False),
)


def write_preview(manifest: dict, out_dir: Path = OUT_DIR, ref_dir: Path = REF_DIR,
                  path: Path = PREVIEW) -> Path:
    cards = []
    for end in ENDINGS:
        entry = manifest["files"][f"{end.lump}.png"]
        with Image.open(out_dir / f"{end.lump}.png") as im:
            pic = im.copy()
        parts = [f'<div class="card"><h3 style="margin:0 0 6px">Episode {end.episode} '
                 f'<span class="tag">{end.lump}</span></h3>',
                 f'<img src="{_b64(_zoom(pic, SHOT_ZOOM))}" width="{SCREEN[0] * SHOT_ZOOM}" '
                 f'alt="{end.lump} at x{SHOT_ZOOM}">',
                 f'<p class="muted">x{SHOT_ZOOM}, nearest neighbour, as the engine draws it at 960x600 '
                 f'(on a 16:9 monitor it is pillarboxed like TITLEPIC). Window keeps: {end.keeps}. '
                 f'Source {end.ref} {entry["source_size"][0]}x{entry["source_size"][1]}, window x '
                 f'{end.window[0]}-{end.window[1]}' +
                 (f', {end.pad_top} rows of sky added above' if end.pad_top else '') +
                 (f', {end.pad_bottom} rows of ground below' if end.pad_bottom else '') +
                 f'; {entry["colours"]} colours of palette v{end.palette_version}.</p>']
        row = []
        if "armband" in entry:
            info = entry["armband"]
            before = Image.open(out_dir / f"armband_{end.lump}_before.png")
            after = Image.open(out_dir / f"armband_{end.lump}_after.png")
            row.append(f'<div><img src="{_b64(_zoom(before, 2))}" alt="armband before"><p class="muted">'
                       f'Gemini\'s blank band, painting px x2</p></div>')
            row.append(f'<div><img src="{_b64(_zoom(after, 2))}" alt="armband after"><p class="muted">'
                       f'the symbol painted (armband_symbol, `{info["how"]}` field, arm axis '
                       f'{info["hint_deg"]:.0f} deg), x2</p></div>')
            row.append(f'<div><img src="{_b64(_armband_zoom(end, pic, info))}" alt="armband in game">'
                       f'<p class="muted">in the 320x200 picture, x{ARMBAND_ZOOM}</p></div>')
        if end.superseded and (ref_dir / end.superseded).is_file():
            row.append(f'<div><img class="smooth" src="{_b64(_thumb(ref_dir / end.superseded))}" '
                       f'width="{THUMB_W}" alt="first round"><p class="muted">reference only: the first '
                       f'round ({end.superseded}), whose enemies the CEO turned down; replaced by the v2 '
                       f'painting asked with our enemy sheet attached</p></div>')
        if row:
            parts.append('<div class="row">' + "".join(row) + "</div>")
        parts.append("</div>")
        cards.append("".join(parts))
    seq = []
    for i, (name, what, new) in enumerate(SEQUENCE):
        if i:
            seq.append('<span class="arrow">&rarr;</span>')
        seq.append(f'<div class="step{" new" if new else ""}"><b>{name}</b><br>'
                   f'<span class="muted">{what}</span></div>')
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Episode Endings</title><style>{CSS}</style></head><body><main>
<h1>Episode endings: the three illustrations</h1>
<p class="muted">V3 B2 (D132), 2026-10-25. Generated by <span class="tag">tools/art/gen_endings.py</span>
from the Gemini paintings (local, D77). Proposed and installed on the branch as provisional:
nothing is released until the CEO says yes. Engine pass pending (D26).</p>

<h2>1. When they show: the proposed order</h2>
<div class="seq">{''.join(seq)}</div>
<p>At the end of MAP03, MAP06 and MAP09 the player sees the stats, then the awards, then the
episode's ending text, then <b>the illustration full screen</b>, and a key goes to the title.
This is Doom's own order (Doom 1's episode 1: the text, then a picture), so it needs no new code:
the map's <span class="tag">next</span> names our end sequence instead of the plain
<span class="tag">endtitle</span>, and that sequence is the picture, then the title.
The text tells what happened; the picture closes on it with nothing printed over the art.</p>
<table>
<tr><th>Option</th><th>What it means</th><th>Verdict</th></tr>
<tr><td><b>A. text, then picture</b> (recommended)</td><td>the engine's built-in order; the ending texts
stay in their clusters, unchanged in English, Russian and Catalan</td><td>installed</td></tr>
<tr><td>B. picture, then text</td><td>the three ending texts move out of the clusters into our sequence;
they would be drawn by a different path (colour, font, layout to be checked again)</td>
<td>possible, if the CEO prefers it</td></tr>
<tr><td>C. picture behind the text</td><td>8-10 lines over a busy painting would not read without dimming
it to half, which loses the art</td><td>not recommended</td></tr>
</table>

<h2>2. The three illustrations</h2>
{''.join(cards)}

<h2>3. What to decide</h2>
<ul>
<li>Approve the three pictures (or name the ones to redo).</li>
<li>Approve the armband symbol on episode 1's fallen soldier and on the Consortium's Reich half (D105: shown first).</li>
<li>Keep order A (text, then picture), or ask for B.</li>
</ul>
</main></body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref-dir", type=Path, default=REF_DIR, help="the Gemini references (work/art/reference)")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--install", action="store_true", help="copy SDEND1-3 to assets/graphics/endings/")
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args(argv)
    m = build(args.out_dir, args.ref_dir)
    print(json.dumps(m, indent=1, ensure_ascii=False))
    if args.install:
        for p in install(args.out_dir):
            print("installed", p)
    if not args.no_preview:
        print(write_preview(m, args.out_dir, args.ref_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
