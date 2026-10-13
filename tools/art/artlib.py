"""Shared helpers for the procedural texture scripts in tools/art/.

Everything here is deterministic given a seed, so a texture can be rebuilt
byte-for-byte from its script + seed (the "origin" recorded in
docs/art/TEXTURE-INDEX.md).

Pipeline of every texture:
  numpy float field(s) in [0,1]  ->  RGB uint8 image (Pillow)  ->
  optional vector overlay drawn at SUPERSAMPLE x and box-downsampled  ->
  quantised to docs/art/palette.json (no dithering)  ->  indexed PNG.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"

# Vector overlays (stars, letters, profiles) are drawn at this multiple of the
# texture size and then box-filtered down: it gives anti-aliased edges whose
# intermediate tones still land on the palette ramps. 4 is enough at 64-128 px.
SUPERSAMPLE = 4

# Doom textures must be multiples of 8 (ART-BIBLE §2); checked on save.
DIMENSION_MULTIPLE = 8

# Fonts with Cyrillic glyphs (verified with Pillow getbbox on "ЛЕНИН ЖИВ"
# on macOS). Impact is a condensed grotesque close to Soviet poster
# lettering; Arial Narrow Bold is for small secondary text.
#
# Resolved per machine: the macOS paths (where every approved asset was
# rendered) first, then the Windows font folder (the CEO's PC since
# 2026-10-13). Windows ships Impact but NOT Arial Narrow Bold, which comes
# with Office; Arial Bold is the fallback so the generators still run. It
# is a wider face, so small text and sheet labels rendered here come out
# DIFFERENT from the macOS originals. Rule that follows: approved assets
# are never regenerated on a machine whose FONT_SMALL is the fallback;
# tests/test_art.py compares assets/ with work/, never with a fresh render.


def _first_font(*candidates: str) -> str:
    """First candidate that exists on this machine; the first candidate
    otherwise, so a missing font fails loudly in ImageFont.truetype
    rather than silently here."""
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return candidates[0]


_WIN_FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
FONT_POSTER = _first_font(
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    str(_WIN_FONTS / "impact.ttf"),
)
FONT_SMALL = _first_font(
    "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf",
    str(_WIN_FONTS / "arialnb.ttf"),
    str(_WIN_FONTS / "arialbd.ttf"),
)
# True when both faces resolved to a real file; the text-rendering tests
# skip when it is False (Linux CI).
FONTS_PRESENT = all(Path(f).is_file() for f in (FONT_POSTER, FONT_SMALL))


# ----------------------------------------------------------------- palette
_palette_cache: dict | None = None


def load_palette() -> dict:
    global _palette_cache
    if _palette_cache is None:
        _palette_cache = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    return _palette_cache


def palette_image() -> Image.Image:
    """A 'P' image carrying the mod palette, for Image.quantize(palette=...)."""
    pal = load_palette()
    img = Image.new("P", (1, 1))
    img.putpalette([c for rgb in pal["colours"] for c in rgb])
    return img


def ramp(name: str) -> list[tuple[int, int, int]]:
    """Colours of one ramp, darkest first."""
    pal = load_palette()
    for r in pal["ramps"]:
        if r["name"] == name:
            return [tuple(c) for c in r["colours"]]
    raise KeyError(name)


def ramp_colour(name: str, t: float) -> tuple[int, int, int]:
    """Colour at position t in [0,1] along a ramp (0 = darkest)."""
    cols = ramp(name)
    i = int(round(max(0.0, min(1.0, t)) * (len(cols) - 1)))
    return cols[i]


def quantize(img: Image.Image) -> Image.Image:
    """Snap an RGB image to the mod palette without dithering.

    No dithering on purpose: Doom-era textures read as flat, deliberate
    pixels; Floyd-Steinberg noise looks like JPEG dirt at 4x. Gradients are
    broken up beforehand with fine noise instead (see `grain`).
    """
    return img.convert("RGB").quantize(palette=palette_image(), dither=Image.Dither.NONE)


# ------------------------------------------------------------------- noise
def smoothstep(t: np.ndarray) -> np.ndarray:
    return t * t * (3 - 2 * t)


def value_noise(w: int, h: int, cells_x: int, cells_y: int, rng: np.random.Generator) -> np.ndarray:
    """Tileable value noise in [0,1]: a random lattice of cells_x × cells_y
    values interpolated with smoothstep. Lattice indices wrap, so the result
    tiles exactly in both axes (the lattice *is* the period)."""
    lattice = rng.random((cells_y, cells_x))
    ys = (np.arange(h) / h) * cells_y
    xs = (np.arange(w) / w) * cells_x
    y0 = np.floor(ys).astype(int) % cells_y
    x0 = np.floor(xs).astype(int) % cells_x
    y1 = (y0 + 1) % cells_y
    x1 = (x0 + 1) % cells_x
    ty = smoothstep(ys - np.floor(ys))[:, None]
    tx = smoothstep(xs - np.floor(xs))[None, :]
    a = lattice[y0][:, x0]
    b = lattice[y0][:, x1]
    c = lattice[y1][:, x0]
    d = lattice[y1][:, x1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(w: int, h: int, base_cells: int, octaves: int, rng: np.random.Generator,
        persistence: float = 0.5, aspect: float = 1.0) -> np.ndarray:
    """Tileable fractal noise in [0,1] (sum of value_noise octaves).
    `aspect` > 1 stretches the cells vertically (for streaks)."""
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    cells = base_cells
    for _ in range(octaves):
        cy = max(1, int(round(cells / aspect)))
        total += amp * value_noise(w, h, cells, cy, rng)
        norm += amp
        amp *= persistence
        cells *= 2
    return total / norm


def grain(w: int, h: int, rng: np.random.Generator, amount: float) -> np.ndarray:
    """Per-pixel white noise in [-amount, amount] (always tileable)."""
    return (rng.random((h, w)) * 2 - 1) * amount


def to_rgb(field: np.ndarray, ramp_name: str) -> np.ndarray:
    """Map a [0,1] field through a palette ramp -> (h,w,3) uint8."""
    cols = np.array(ramp(ramp_name), dtype=np.float64)
    idx = np.clip(field, 0, 1) * (len(cols) - 1)
    lo = np.floor(idx).astype(int)
    hi = np.minimum(lo + 1, len(cols) - 1)
    t = (idx - lo)[..., None]
    return np.clip(cols[lo] * (1 - t) + cols[hi] * t, 0, 255).astype(np.uint8)


def shade(rgb: np.ndarray, factor: np.ndarray | float) -> np.ndarray:
    """Multiply an RGB array by a scalar or (h,w) field."""
    f = np.asarray(factor, dtype=np.float64)
    if f.ndim == 2:
        f = f[..., None]
    return np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8)


def blend(rgb: np.ndarray, colour: tuple[int, int, int], mask: np.ndarray) -> np.ndarray:
    """Lerp rgb towards a flat colour by a (h,w) mask in [0,1]."""
    m = np.clip(mask, 0, 1)[..., None]
    col = np.array(colour, dtype=np.float64)[None, None, :]
    return np.clip(rgb * (1 - m) + col * m, 0, 255).astype(np.uint8)


# --------------------------------------------------------- vector overlays
class Overlay:
    """An RGBA canvas at SUPERSAMPLE x for crisp vector shapes and text.
    Coordinates passed to draw methods are in texture pixels (floats ok).

    Every primitive is drawn on its own layer and alpha-composited: Pillow's
    ImageDraw *replaces* RGBA pixels instead of blending them, so a
    semi-transparent or fully transparent fill drawn directly would punch a
    hole through earlier shapes."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.s = SUPERSAMPLE
        self.img = Image.new("RGBA", (w * self.s, h * self.s), (0, 0, 0, 0))

    def _p(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    def _layer(self):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        return layer, ImageDraw.Draw(layer)

    def _commit(self, layer):
        self.img.alpha_composite(layer)

    def polygon(self, pts, fill):
        layer, d = self._layer()
        d.polygon(self._p(pts), fill=fill)
        self._commit(layer)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0):
        layer, d = self._layer()
        d.rectangle([x0 * self.s, y0 * self.s, x1 * self.s - 1, y1 * self.s - 1],
                    fill=fill, outline=outline, width=int(round(width * self.s)))
        self._commit(layer)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0):
        layer, d = self._layer()
        d.ellipse([x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s],
                  fill=fill, outline=outline, width=int(round(width * self.s)))
        self._commit(layer)

    def line(self, pts, fill, width=1.0):
        layer, d = self._layer()
        d.line(self._p(pts), fill=fill, width=int(round(width * self.s)))
        self._commit(layer)

    def line_tiled(self, pts, fill, width=1.0):
        """`line`, but drawn nine times: once in place and once shifted by
        each combination of +-w, +-h. A stroke that leaves one edge therefore
        re-enters on the opposite one, which is what a texture declared
        "Tiles: yes" needs.

        The noise fields wrap by construction (`value_noise` indexes a
        lattice modulo its period) but vector strokes do not: an Overlay
        clips at the canvas, so a crack or a scratch used to stop dead at the
        tile border (QA BUG-ART-001). All nine copies go on ONE layer so a
        semi-transparent stroke that overlaps its own wrapped copy is not
        composited twice and darkened.

        Only strokes whose length is under the texture size wrap correctly
        with a single ring of neighbours; that holds for every stroke in this
        project (cracks reach ~50 px on a 64 px flat).
        """
        layer, d = self._layer()
        w = int(round(width * self.s))
        for dx in (-self.w, 0, self.w):
            for dy in (-self.h, 0, self.h):
                d.line(self._p([(x + dx, y + dy) for x, y in pts]), fill=fill, width=w)
        self._commit(layer)

    def arc_ring(self, cx, cy, r_out, r_in, start, end, fill):
        """Thick arc (ring sector) between angles start..end in degrees
        (Pillow convention: 0 = +x, 90 = +y i.e. down, clockwise)."""
        s = self.s
        layer, d = self._layer()
        d.pieslice([(cx - r_out) * s, (cy - r_out) * s, (cx + r_out) * s, (cy + r_out) * s],
                   start, end, fill=fill)
        d.pieslice([(cx - r_in) * s, (cy - r_in) * s, (cx + r_in) * s, (cy + r_in) * s],
                   start - 1, end + 1, fill=(0, 0, 0, 0))
        self._commit(layer)

    def text(self, cx, cy, txt, size, fill, font=FONT_POSTER, anchor="mm", max_width=None):
        """Centered text. If max_width (texture px) is given, size shrinks
        until the line fits. Returns the size used (texture px)."""
        s = self.s
        px = int(size * s)
        f = ImageFont.truetype(font, px)
        if max_width is not None:
            while px > 4 and f.getlength(txt) > max_width * s:
                px -= 1
                f = ImageFont.truetype(font, px)
        layer, d = self._layer()
        d.text((cx * s, cy * s), txt, font=f, fill=fill, anchor=anchor)
        self._commit(layer)
        return px / s

    def group(self, outline=None, outline_width: float = 1.0) -> "Overlay":
        """A sub-overlay to draw several primitives that form one shape
        (e.g. the blade and handle of a sickle). Pass it to `end_group` to
        stamp it onto this overlay; if `outline` is given, the union of the
        group's pixels is first dilated by `outline_width` texture px and
        painted in that colour underneath, giving a single clean contour
        around the whole shape instead of one per primitive."""
        g = Overlay(self.w, self.h)
        g._outline = (outline, outline_width)
        return g

    def end_group(self, g: "Overlay") -> None:
        outline, width = g._outline
        if outline is not None:
            k = int(round(width * self.s))
            alpha = g.img.getchannel("A").filter(ImageFilter.MaxFilter(2 * k + 1))
            rim = Image.new("RGBA", self.img.size, outline + (255,))
            rim.putalpha(alpha)
            self._commit(rim)
        self._commit(g.img)

    def composite(self, rgb: np.ndarray) -> np.ndarray:
        """Box-downsample the overlay and alpha-blend it over an RGB array."""
        small = self.img.resize((self.w, self.h), Image.Resampling.BOX)
        over = np.asarray(small, dtype=np.float64)
        a = over[..., 3:4] / 255.0
        return np.clip(rgb * (1 - a) + over[..., :3] * a, 0, 255).astype(np.uint8)


def star_points(cx: float, cy: float, r_out: float, r_in: float | None = None, rot: float = -90.0):
    """Five-pointed star polygon. r_in default is the regular pentagram ratio."""
    if r_in is None:
        r_in = r_out * 0.382
    pts = []
    for i in range(10):
        ang = np.deg2rad(rot + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * np.cos(ang), cy + r * np.sin(ang)))
    return pts


# -------------------------------------------------------------------- save
def save_indexed(rgb: np.ndarray, path: Path) -> Image.Image:
    """Quantise an (h,w,3) array and save as indexed PNG. Returns the image."""
    h, w = rgb.shape[:2]
    assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, (w, h)
    img = quantize(Image.fromarray(rgb, "RGB"))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return img


def tiling_seam_score(rgb: np.ndarray) -> float:
    """How visible the wrap seam is, relative to the texture's own features.

    = (mean |difference| between the last and first row/column, i.e. the
    edge that touches itself when tiled) / (max mean |difference| between
    any two adjacent interior rows/columns). <= 1.0 means the seam is no
    stronger than a feature already inside the texture (a panel joint, a
    stripe edge). Shown in the preview as information, not as proof: the
    2x2 tile is what the eye checks.
    """
    a = rgb.astype(np.float64)
    row_diffs = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    col_diffs = np.abs(np.diff(a, axis=1)).mean(axis=(0, 2))
    wrap = max(np.abs(a[0] - a[-1]).mean(), np.abs(a[:, 0] - a[:, -1]).mean())
    interior = max(row_diffs.max(), col_diffs.max(), 1e-6)
    return float(wrap / interior)
