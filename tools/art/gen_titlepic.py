#!/usr/bin/env python3
"""The epic title screen (D126): Gemini's cover painting -> TITLEPIC 320x200.

    .venv/Scripts/python.exe tools/art/gen_titlepic.py            # both variants + preview
    .venv/Scripts/python.exe tools/art/gen_titlepic.py --no-preview

The CEO asked for a title screen "epica como la del Doom" ("epic, like Doom's", D126). The
painting is the project lead's Gemini image `work/art/reference/
gemini_titlepic_A.jfif` (1376x768, about 16:9; D77: it stays local, never
committed or shipped). This module turns it into the engine's TITLEPIC:

  1. symbol    - variant A only: the D12 symbol painted on the Reich's
                 armbands at the painting's own resolution, the way the
                 enemies got it (D108/D114): tools/art/armband_symbol.py's
                 `ring` fields (Gemini drew a white square OUTLINE on the red
                 band, which becomes one white field) and its warp. Variant B
                 keeps Gemini's empty square. D105: the CEO sees the symbol
                 before it is applied, so both are produced and he chooses.
  2. sky       - the painting is 16:9 and the logo needs the top 58 rows of a
                 320x200 screen: SKY_PAD rows of sky are added above it (its
                 own top rows mirrored, blurred to smoke, darkened), so the
                 sergeant's helmet clears the logo instead of being cut.
  3. crop      - a 4:3 window (CROP_X0, the padded height): a 320x200 Doom
                 screen is shown at 4:3, each pixel 1.2 times taller than wide,
                 so the window is 4:3 and the resize squashes it 1.2 vertically.
                 It keeps the muzzle flash, the hero, the banner, the Kremlin
                 tower and the whole statue-robot.
  4. resize    - Lanczos to 320x200, then a light unsharp mask (Gemini's brush
                 strokes survive the 4x reduction).
  5. logo band - the logo's band (rows 0-LOGO_BAND_END) darkened and softened,
                 strongest behind the logo box, so the torch and the banner's
                 tip sit as a dim glow behind the letters; the hero untouched.
  6. palette   - nearest colour of palette v2 in CIELAB with a 4x4 ordered
                 (Bayer) dither of DITHER_AMP: clean, repeatable pixels, no
                 error-diffusion dirt. (Weighted RGB, the enemies' snap, turned
                 the fire-lit face's highlights hazard yellow: glowing eyes.)
  7. logo      - M_DOOM composited at the MOD-SPEC 6.6 contract, (60, 0), so
                 the title loop shows the name and the menu's own M_DOOM lands
                 on it pixel for pixel. Two logo treatments:
                   free  - M_DOOM_free.png: the approved lockup with its black
                           plate keyed out (alpha 0) and a 1-px black outline,
                           so the painting shows round the letters (recommended;
                           replaces assets/graphics/shell/M_DOOM.png too);
                   plate - today's M_DOOM unchanged, its 200x58 black plate
                           over the sky (no other asset changes).

Outputs, in work/art/titlepic_gemini/ (never assets/; install.sh there copies
the CEO's choice): TITLEPIC_<A|B>_<free|plate>.png (indexed, palette v2),
M_DOOM_free.png (RGBA, hard alpha), the menu simulations and the preview
docs/art/previews/2026-10-24_P4_titlepic.html. The installed names are never
used here (tests/test_art.py matches assets/ to work/ by bytes when the name
differs, and by name when it is the same, which must then be unique).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
import artlib  # noqa: E402
import palette  # noqa: E402

ROOT = artlib.PROJECT_ROOT
REF = ROOT / "work" / "art" / "reference" / "gemini_titlepic_A.jfif"
OUT_DIR = ROOT / "work" / "art" / "titlepic_gemini"
PREVIEW = ROOT / "docs" / "art" / "previews" / "2026-10-24_P4_titlepic.html"
SHELL = ROOT / "assets" / "graphics" / "shell"
CUR_TITLEPIC = SHELL / "TITLEPIC.png"
CUR_M_DOOM = SHELL / "M_DOOM.png"

SCREEN = (320, 200)
LOGO_POS = (60, 0)                 # MOD-SPEC 6.6, the contract (tests/test_language.py::MainMenuLogoTest)
LOGO_SIZE = (200, 64)
DISPLAY_ASPECT = 4 / 3             # a 320x200 full-screen picture is shown at 4:3

# 2. sky: rows added above the painting so the helmet clears the logo.
SKY_PAD = 110                      # source px; the helmet's top (source y ~158) lands on row ~61
SKY_BLUR = 18.0                    # px: the mirrored rows become smoke (the torch a glow, not a copy)
SKY_CAP_PCT = 60                   # the smoke's luminance is capped at this percentile of itself
SKY_TOP_DARK = 0.55                # x at the very top of the pad, 1.0 at the seam
SKY_SEAM = 24                      # source px blended across the seam
# 3. crop: a 4:3 window over the padded painting.
CROP_X0 = 140                      # keeps the muzzle flash (x~195) and the statue (to x~1260)
# 4. resize
UNSHARP = (1.2, 60, 2)             # radius, percent, threshold
# 5. logo band (screen px)
LOGO_BAND_FULL = 36                # rows 0..this fully treated
LOGO_BAND_END = 60                 # ... fading to nothing here (the helmet starts at ~61)
BAND_DARK = 0.50                   # x the band's colour behind the logo box
BAND_DARK_SIDES = 0.78             # ... and at the screen's left and right edges
BAND_BLUR = 1.1                    # px (screen) of softening in the band
BOX_FEATHER = 22                   # px over which the logo box's strength fades sideways
# 6. palette
DITHER_AMP = 5.0                   # +- per channel, 0-255, of the 4x4 Bayer threshold
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16 - 0.469
SRGB_XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
D65 = np.array([0.9505, 1.0, 1.089])
# 7. free logo
PLATE_RGB = (0, 0, 0)              # M_DOOM's plate colour (exact; letters' darks are never pure black)
OUTLINE_RGB = (0, 0, 0)

# 1. armbands: (name, source box x0, y0, x1, y1, arm axis toward the shoulder, screen degrees)
ARMBANDS = (
    ("front", 555, 650, 700, 768, 118.0),   # the Reich soldier in front, his band toward us
    ("left", 215, 700, 330, 768, 95.0),     # the one on the left, his band cut by the frame
)
FIELD_MAX = 90                     # source px: the white square is ~55 px at this size
RING_RED_R, RING_RED_G = 70, 45    # shaded_ring: the band's red in shade
RING_LIGHT_G = 80                  # ... its white wall in shade (G channel)
RING_W, RING_WALL, RING_MIN_PX = 3, 0.5, 60
SYMBOL_SEED = 126


# ------------------------------------------------------------------ helpers
def load_ref(path: Path = REF) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def gaussian(img: np.ndarray, sigma: float) -> np.ndarray:
    pil = Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8))
    return np.asarray(pil.filter(ImageFilter.GaussianBlur(sigma))).astype(float)


# ------------------------------------------------------------- 1. symbol
def shaded_ring(crop: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    """armband_symbol's `ring` for a band in shade: a red patch (R over
    RING_RED_R, G under RING_RED_G) not touching the crop's edge, walled by
    RING_WALL of RING_W-px ring of light pixels (G over RING_LIGHT_G, R >= G:
    the square's white in shade, ~(150,115,108)). The patch and wall become
    one field painted the wall's brightest quarter (the shade is kept)."""
    import gemini_enemy as ge
    a = crop.astype(np.int32)
    r, g = a[..., 0], a[..., 1]
    light = (g > RING_LIGHT_G) & (r >= g)
    red = (r > RING_RED_R) & (g < RING_RED_G)
    lab, n = ge.label(red)
    out = crop.copy()
    fields = []
    for i in range(1, n + 1):
        comp = lab == i
        ys, xs = np.nonzero(comp)
        if comp.sum() < RING_MIN_PX or ys.min() == 0 or xs.min() == 0 \
                or ys.max() == crop.shape[0] - 1 or xs.max() == crop.shape[1] - 1:
            continue
        ring = ge._dilate(comp, RING_W) & ~comp
        if (ring & light).sum() < RING_WALL * ring.sum():
            continue
        wall = ring & light
        L = a[wall].sum(axis=1)
        top = a[wall][L >= np.percentile(L, 75)]
        out[comp | wall] = top.mean(axis=0).astype(crop.dtype)
        fields.append(comp | wall)
    return out, fields


def paint_armbands(rgb: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    """The symbol on each Reich armband (armband_symbol's ring fields + warp)."""
    import armband_symbol as ab
    out = rgb.copy()
    report = []
    for name, x0, y0, x1, y1, hint in ARMBANDS:
        crop = out[y0:y1, x0:x1].copy()
        mask = np.ones(crop.shape[:2], bool)
        filled, fields = ab.select_fields(crop, mask, "ring", field_max=FIELD_MAX)
        if not fields:                       # a band in shade: its wall is too grey for ab's white
            filled, fields = shaded_ring(crop)
        if not fields:
            report.append({"armband": name, "fields": 0})
            continue
        fields = [max(fields, key=lambda f: int(f.sum()))]   # the square, not a stray
        painted, info = ab.paint_symbol(filled, mask, hint_deg=hint, seed=SYMBOL_SEED, fields=fields)
        ys, xs = np.nonzero(fields[0])
        report.append({"armband": name, "fields": 1, "field_px": int(fields[0].sum()),
                       "box": [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0],
                       "ink_px": round(info.ink_px, 1), "sigma": round(info.sigma, 2)})
        out[y0:y1, x0:x1] = painted
    return out, report


# ---------------------------------------------------------- 2-4. framing
def pad_sky(rgb: np.ndarray, pad: int = SKY_PAD) -> np.ndarray:
    top = rgb[:pad][::-1].astype(float)
    smoke = gaussian(top, SKY_BLUR)
    lum = smoke @ np.array([0.299, 0.587, 0.114])
    cap = np.percentile(lum, SKY_CAP_PCT)
    smoke *= np.minimum(1.0, cap / np.maximum(lum, 1e-6))[..., None]   # the torch's mirror: no second sun
    rng = np.random.default_rng(SYMBOL_SEED)
    clouds = artlib.fbm(rgb.shape[1], pad, 12, 4, rng)
    clouds = (clouds - clouds.min()) / max(1e-6, np.ptp(clouds))
    smoke *= (0.85 + 0.3 * clouds)[..., None]
    ramp = np.linspace(SKY_TOP_DARK, 1.0, pad)[:, None, None]
    smoke *= ramp
    # the seam: the painting's own top rows fade in over the smoke
    out = np.concatenate([smoke, rgb.astype(float)], axis=0)
    for i in range(SKY_SEAM):
        t = (i + 1) / (SKY_SEAM + 1)
        r = pad + i
        out[r] = smoke[-1] * (1 - t) + rgb[i] * t
    return out


def crop_window(h: int, x0: int = CROP_X0) -> tuple[int, int, int, int]:
    w = int(round(h * DISPLAY_ASPECT))
    return x0, 0, x0 + w, h


def frame(rgb: np.ndarray) -> np.ndarray:
    padded = pad_sky(rgb)
    x0, y0, x1, y1 = crop_window(padded.shape[0])
    assert x1 <= padded.shape[1], (x1, padded.shape)
    win = Image.fromarray(np.clip(padded[y0:y1, x0:x1] + 0.5, 0, 255).astype(np.uint8))
    small = win.resize(SCREEN, Image.LANCZOS)
    r, p, t = UNSHARP
    small = small.filter(ImageFilter.UnsharpMask(radius=r, percent=p, threshold=t))
    return np.asarray(small).astype(float)


# ---------------------------------------------------------- 5. logo band
def band_strength() -> np.ndarray:
    h, w = SCREEN[1], SCREEN[0]
    y = np.arange(h, dtype=float)
    v = np.clip((LOGO_BAND_END - y) / (LOGO_BAND_END - LOGO_BAND_FULL), 0, 1)
    v = v * v * (3 - 2 * v)
    x = np.arange(w, dtype=float)
    lx0, lx1 = LOGO_POS[0], LOGO_POS[0] + LOGO_SIZE[0]
    dx = np.maximum(np.maximum(lx0 - x, x - lx1), 0)
    inbox = np.clip(1 - dx / BOX_FEATHER, 0, 1)
    dark = BAND_DARK_SIDES + (BAND_DARK - BAND_DARK_SIDES) * inbox      # darkness multiplier per column
    return v[:, None], dark[None, :]


def logo_band(img: np.ndarray) -> np.ndarray:
    v, dark = band_strength()
    soft = gaussian(img, BAND_BLUR)
    treated = soft * dark[..., None]
    a = v[..., None]
    return img * (1 - a) + treated * a


# ------------------------------------------------------------ 6. palette
def pal_v2() -> np.ndarray:
    return np.array(palette.colours(2), np.int64)


def to_lab(rgb: np.ndarray) -> np.ndarray:
    """sRGB (0-255) -> CIELAB (D65)."""
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ SRGB_XYZ.T / D65
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def snap(img: np.ndarray, pal: np.ndarray, dither: float = DITHER_AMP) -> np.ndarray:
    """Nearest palette colour in CIELAB after a 4x4 Bayer offset of +-dither.
    (The enemies' weighted-RGB snap sends the fire-lit skin to hazard yellow:
    the sergeant's eyes glowed; Lab keeps it in the browns and reds.)"""
    h, w = img.shape[:2]
    thr = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w] * 2 * dither
    src = to_lab(np.clip(img + thr[..., None], 0, 255).reshape(-1, 3))
    pl = to_lab(pal)
    d = ((src[:, None, :] - pl[None]) ** 2).sum(axis=2)
    return d.argmin(axis=1).reshape(h, w)


def indexed(idx: np.ndarray, pal: np.ndarray) -> Image.Image:
    im = Image.fromarray(idx.astype(np.uint8), "P")
    im.putpalette([int(c) for rgb in pal for c in rgb])
    return im


# --------------------------------------------------------------- 7. logo
def free_logo(src: Path = CUR_M_DOOM) -> Image.Image:
    """Today's M_DOOM with its black plate keyed out and a 1-px black outline."""
    a = np.asarray(Image.open(src).convert("RGBA")).copy()
    plate = (a[..., 3] == 255) & (a[..., :3] == PLATE_RGB).all(-1)
    ink = (a[..., 3] == 255) & ~plate
    grown = ink.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= np.roll(np.roll(ink, dy, 0), dx, 1)
    out = np.zeros_like(a)
    out[ink] = a[ink]
    ring = grown & ~ink
    out[ring, :3] = OUTLINE_RGB
    out[ring, 3] = 255
    return Image.fromarray(out, "RGBA")


def compose(idx_img: Image.Image, logo: Image.Image, pal: np.ndarray) -> Image.Image:
    """The logo pasted at the contract position, back in the palette (the
    logo's colours are already palette v1/v2 colours: snapped without dither)."""
    rgba = idx_img.convert("RGBA")
    rgba.alpha_composite(logo, LOGO_POS)
    rgb = np.asarray(rgba.convert("RGB")).astype(float)
    return indexed(snap(rgb, pal, dither=0.0), pal)


# ---------------------------------------------------------------- build
def build(out_dir: Path = OUT_DIR, ref: Path = REF) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    pal = pal_v2()
    src = load_ref(ref)
    painted, report = paint_armbands(src)
    logos = {"free": free_logo(), "plate": Image.open(CUR_M_DOOM).convert("RGBA")}
    logos["free"].save(out_dir / "M_DOOM_free.png", optimize=True)
    manifest = {"decision": "D126", "source": ref.relative_to(ROOT).as_posix(),
                "source_size": list(src.shape[1::-1]), "sky_pad": SKY_PAD,
                "crop_padded": list(crop_window(src.shape[0] + SKY_PAD)),
                "armbands": report, "palette": "docs/art/palette.json v2 (226)",
                "dither": f"CIELAB nearest, Bayer 4x4 +-{DITHER_AMP}", "logo_pos": list(LOGO_POS), "files": {}}
    for variant, picture in (("A", painted), ("B", src)):
        img = frame(picture)
        Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8)).save(out_dir / f"raw_{variant}.png")
        for treat, logo in logos.items():
            base = img if treat == "plate" else logo_band(img)
            screen = indexed(snap(base, pal), pal)
            final = compose(screen, logo, pal)
            name = f"TITLEPIC_{variant}_{treat}.png"
            final.save(out_dir / name, optimize=True)
            manifest["files"][name] = {"colours": len(set(np.asarray(final).ravel().tolist()))}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args(argv)
    m = build()
    print(json.dumps(m, indent=1, ensure_ascii=False))
    if not args.no_preview:
        import titlepic_preview
        print(titlepic_preview.write())
    return 0


if __name__ == "__main__":
    sys.exit(main())
