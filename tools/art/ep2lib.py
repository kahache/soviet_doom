"""Shared machinery for the Episode 2 texture drafts (D104, phase P4).

Episode 2, «The Road to Moscow»: MAP04 the Sverdlovsk marshalling yard
(tools/art/gen_railway.py), MAP05 the Volga dam at Zhiguli
(tools/art/gen_dam.py), MAP06 Red Square and the Kremlin
(tools/art/gen_moscow.py). tools/art/gen_episode2.py renders the three and
writes the CEO's review sheet.

Everything here follows the method of the approved metro and factory sets
(gen_metro.py, gen_factory.py): one seed per piece (set BATCH_SEED + offset),
numpy fields that wrap, vector overlays at SUPERSAMPLE x, quantised to
docs/art/palette.json without dither, PNG written to work/ only. Nothing is
ever written into assets/: these are drafts until the CEO says yes.

Palette rule for Episode 2: v1. A piece may ask for v2 only for the
`marble_red` ramp (fired-clay brick), the precedent the CEO approved with the
factory brick SDBRCK1 (D66); `V2_RAMPS_ALLOWED` makes the rule mechanical:
a v2 piece is quantised to v1 + marble_red, never to the cobalt and gold of
the metro mosaic and the portal, nor to the Legion's flesh.

Lettering: never a system font (D27). Cyrillic comes from our own alphabet
(assets/fonts/bigfont, D24) through gen_factory.glyph_masks; dial digits and
"labels" are drawn pixel by pixel here.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import DIMENSION_MULTIPLE, fbm, quantize, shade, tiling_seam_score  # noqa: E402
import gen_factory  # noqa: E402  (bigfont glyphs, paste_mask)
import gen_metro  # noqa: E402  (palette-version helpers)
import palette as palgen  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "episode2"
ASSETS = PROJECT_ROOT / "assets"

# ART-BIBLE §2 wall sizes; flats are 64x64.
ALLOWED_WALL_SIZES = ((64, 64), (64, 128), (128, 64), (128, 128), (128, 256), (256, 64))
FLAT_SIZE = (64, 64)
FRAMES = 4                    # animated pieces: four frames, like SDMOLT/SDPORT
V2_RAMPS_ALLOWED = ("marble_red",)
ALPHA_CUT = 128               # masked pieces: hard alpha, >= this is opaque

any_to_rgb = gen_metro.any_to_rgb
any_ramp_colour = gen_metro.any_ramp_colour
glyph_masks = gen_factory.glyph_masks
paste_mask = gen_factory.paste_mask


def col(ramp_name: str, t: float) -> tuple[int, int, int]:
    """One palette colour by ramp and position (0 = darkest)."""
    return tuple(int(v) for v in any_ramp_colour(ramp_name, t))


@dataclasses.dataclass
class Piece:
    key: str                  # piece id; for single-lump pieces, the lump
    builder: Callable         # -> (h, w, 3|4) uint8 array, or a list of frames
    kind: str                 # "wall" | "flat"
    size: tuple[int, int]     # (w, h)
    lumps: list[str]
    offset: int               # seed = set BATCH_SEED + offset
    tiles: str                # "xy" | "x" | "y" | "no"
    title: str                # short name for the CEO's sheet
    desc: str                 # description for the sheet
    palette: int = 1
    masked: bool = False
    why_v2: str = ""
    rec: str = "yes"
    rec_why: str = ""
    scene: dict | None = None  # overrides of the sample room (back/left/right/floor/ceil)


# ================================================================ palette
def allowed_colours(version: int) -> list[tuple[int, int, int]]:
    v1 = [tuple(c) for c in palgen.colours(1)]
    if version == 1:
        return v1
    extra = []
    for name in V2_RAMPS_ALLOWED:
        extra += [tuple(c) for c in palgen.ramp_colours(name)]
    return v1 + extra


def _pal_image(cols) -> Image.Image:
    img = Image.new("P", (1, 1))
    img.putpalette([v for c in cols for v in c])
    return img


def quantise_rgb(rgb: np.ndarray, version: int) -> Image.Image:
    """No-dither quantisation to the piece's palette version, restricted to
    the colours Episode 2 may use. The image carries the full palette of
    its version (v1: 162 entries; v2: 226), like every other generator."""
    if version == 1:
        return quantize(Image.fromarray(np.ascontiguousarray(rgb), "RGB"))
    snapped = Image.fromarray(np.ascontiguousarray(rgb), "RGB").quantize(
        palette=_pal_image(allowed_colours(version)), dither=Image.Dither.NONE).convert("RGB")
    return gen_metro.quantize_version(np.asarray(snapped), version)


def quantise(rgb: np.ndarray, version: int) -> Image.Image:
    """RGB in -> indexed out; RGBA in -> RGBA out with hard alpha and every
    opaque pixel a palette colour (the SDCHAN1 exception, ART-BIBLE §2)."""
    if rgb.shape[2] == 4:
        q = np.asarray(quantise_rgb(rgb[..., :3], version).convert("RGB")).copy()
        alpha = np.where(rgb[..., 3] >= ALPHA_CUT, 255, 0).astype(np.uint8)
        q[alpha == 0] = 0
        return Image.fromarray(np.dstack([q, alpha]).astype(np.uint8), "RGBA")
    return quantise_rgb(rgb, version)


def as_array(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGBA" if img.mode == "RGBA" else "RGB"))


def mean_luma(rgb: np.ndarray) -> float:
    a = rgb[..., :3].astype(np.float64)
    if rgb.shape[2] == 4:
        a = a[rgb[..., 3] > 0]
    return float((0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).mean())


# ================================================================ helpers
def wrap_dist(a: np.ndarray, period: float) -> np.ndarray:
    """Signed distance on a circle of `period` (for tileable geometry)."""
    return (a + period / 2) % period - period / 2


def bevel(f: np.ndarray, x0: int, y0: int, x1: int, y1: int, hi: float = 1.18, lo: float = 0.72,
          w: int = 1) -> None:
    """Light from the top-left: brighten the top and left edges of a box,
    darken the bottom and right ones (in place, on a shading field)."""
    f[y0:y0 + w, x0:x1] *= hi
    f[y0:y1, x0:x0 + w] *= hi
    f[y1 - w:y1, x0:x1] *= lo
    f[y0:y1, x1 - w:x1] *= lo


def rivet(rgb: np.ndarray, x: int, y: int, ramp_name: str, t: float, r: int = 1) -> None:
    """A round rivet head, (2r)x(2r) px: lit top-left, shadow bottom-right,
    a 1 px drop shadow on the plate. Wraps at the tile border."""
    h, w = rgb.shape[:2]
    pts = [(dx, dy) for dy in range(2 * r) for dx in range(2 * r)]
    for dx, dy in pts:
        lit = (dx + dy) < r * 2 - 1
        tone = t + 0.22 if lit else t - 0.10
        rgb[(y + dy) % h, (x + dx) % w] = col(ramp_name, min(1.0, max(0.0, tone)))
    for k in range(2 * r):
        yy, xx = (y + 2 * r) % h, (x + k + 1) % w
        rgb[yy, xx] = (rgb[yy, xx] * 0.62).astype(np.uint8)
        yy, xx = (y + k + 1) % h, (x + 2 * r) % w
        rgb[yy, xx] = (rgb[yy, xx] * 0.75).astype(np.uint8)


def cells_voronoi(w: int, h: int, cell: int, rng: np.random.Generator, jitter: float = 0.8):
    """Tileable Voronoi over a jittered grid of cell x cell px: returns
    (F1, F2, id, ox, oy), where (ox, oy) is the offset from the nearest
    point (for facet shading). Used for ballast stones and setts. Points live on a wrapped lattice,
    so the field tiles exactly in both axes."""
    nx, ny = w // cell, h // cell
    px = (np.arange(nx)[None, :] + 0.5 + (rng.random((ny, nx)) - 0.5) * jitter) * cell
    py = (np.arange(ny)[:, None] + 0.5 + (rng.random((ny, nx)) - 0.5) * jitter) * cell
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    cx, cy = (xx // cell).astype(int), (yy // cell).astype(int)
    f1 = np.full((h, w), 1e9)
    f2 = np.full((h, w), 1e9)
    ident = np.zeros((h, w), int)
    offx = np.zeros((h, w))
    offy = np.zeros((h, w))
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx, gy = (cx + ox) % nx, (cy + oy) % ny
            dx = wrap_dist(xx - px[gy, gx], w)
            dy = wrap_dist(yy - py[gy, gx], h)
            d = np.hypot(dx, dy)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            ident = np.where(closer, gy * nx + gx, ident)
            offx = np.where(closer, dx, offx)
            offy = np.where(closer, dy, offy)
            f1 = np.where(closer, d, f1)
    return f1, f2, ident, offx, offy


def illegible_label(rgb: np.ndarray, x0: int, y0: int, width: int, colour, rng: np.random.Generator,
                    rows: int = 1) -> None:
    """Pixel 'words': runs of 1-3 px dashes with 1 px gaps, so a label reads
    as text at 1x and says nothing at 4x (no font involved)."""
    for r in range(rows):
        x = x0
        y = y0 + 2 * r
        while x < x0 + width:
            run = int(rng.integers(1, 4))
            for k in range(run):
                if x + k < x0 + width and rng.random() > 0.15:
                    rgb[y, x + k] = colour
            x += run + 1 + (1 if rng.random() < 0.25 else 0)


# 3x5 pixel digits for dials and stencils (our own, no font).
DIGITS_3X5 = {
    "0": ("###", "#.#", "#.#", "#.#", "###"), "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"), "3": ("###", "..#", ".##", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"), "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"), "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"), "9": ("###", "#.#", "###", "..#", "###"),
}


def digits_mask(text: str) -> np.ndarray:
    rows = []
    for r in range(5):
        rows.append(".".join(DIGITS_3X5[c][r] for c in text))
    return np.array([[ch == "#" for ch in row] for row in rows], bool)


def stamp(rgb: np.ndarray, mask: np.ndarray, x0: int, y0: int, colour, scale: int = 1) -> None:
    m = np.repeat(np.repeat(mask, scale, 0), scale, 1)
    h, w = m.shape
    region = rgb[y0:y0 + h, x0:x0 + w]
    region[m[:region.shape[0], :region.shape[1]]] = colour


# ================================================================ build
def frames_of(piece: Piece) -> list[np.ndarray]:
    out = piece.builder()
    return out if isinstance(out, list) else [out]


def build_set(set_name: str, pieces: list[Piece], batch_seed: int, script_rel: str,
              out_dir: Path | None = None) -> tuple[list[dict], dict]:
    """Render every piece of a set into work/art/episode2/<set>/. Returns
    (manifest entries, quantised arrays by lump)."""
    out_dir = out_dir or WORK_ROOT / set_name
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for p in pieces:
        frames = frames_of(p)
        assert len(frames) == len(p.lumps), p.key
        for lump, rgb in zip(p.lumps, frames):
            assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
            h, w = rgb.shape[:2]
            assert (w, h) == p.size, (lump, w, h)
            assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, lump
            img = quantise(rgb, p.palette)
            img.save(out_dir / f"{lump}.png", optimize=True)
            arrays[lump] = as_array(img)
        first = arrays[p.lumps[0]]
        colours = {tuple(int(v) for v in c) for c in first[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": p.key, "lumps": p.lumps, "kind": p.kind, "set": set_name,
            "width": p.size[0], "height": p.size[1], "palette_version": p.palette,
            "masked": p.masked, "tiles": p.tiles, "script": script_rel, "seed": batch_seed + p.offset,
            "files": [f"work/art/episode2/{set_name}/{lump}.png" for lump in p.lumps],
            "colours_used": len(colours), "mean_luma": round(mean_luma(first), 1),
            "seam_score": None if p.masked else round(tiling_seam_score(first[..., :3]), 2),
            "title_es": p.title, "description_es": p.desc, "status": "draft, proposed (P4, D104)",
        })
    return entries, arrays


# ================================================================ sample room
# A tiny Doom-like view, for the sheet only: a 320x200 screen, 90 degree
# field of view, eye at 41 units, a corridor whose two side walls, back wall,
# floor and ceiling are textured 1 texel per unit, light falling with
# distance in bands. It is NOT the engine (no colormap, no mipmaps): it shows
# scale and tiling in place. NOT VERIFIED against GZDoom.
SCR_W, SCR_H = 320, 200
FOCAL = 160.0
EYE = 41.0
ROOM_HALF_W = 112
ROOM_DEPTH = 288
ROOM_H = 128
LIGHT_BANDS = 24
SIDE_CONTRAST = 0.90          # Doom's fake contrast: walls along y a little darker


def sky_image(seed: int = 5000) -> np.ndarray:
    """Screen-space overcast sky (Doom's sky is screen-space too)."""
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, SCR_H)[:, None] * np.ones((1, SCR_W))
    clouds = fbm(SCR_W, SCR_H, 6, 4, rng, 0.55, aspect=0.4)
    t = np.clip(0.62 - 0.30 * yy + (clouds - 0.5) * 0.25, 0, 1)
    return any_to_rgb(t, "steel_blue")


def _sample(tex: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    th, tw = tex.shape[:2]
    return tex[np.floor(v).astype(int) % th, np.floor(u).astype(int) % tw]


def render_room(back: np.ndarray, left: np.ndarray, right: np.ndarray, floor: np.ndarray,
                ceil: np.ndarray | None = None, light: float = 1.0, version: int = 1,
                sky: np.ndarray | None = None) -> np.ndarray:
    """Walls may be RGBA (masked): where alpha is 0 the sky shows through."""
    sky = sky_image() if sky is None else sky
    sx = (np.arange(SCR_W) + 0.5 - SCR_W / 2) / FOCAL
    sy = (SCR_H / 2 - (np.arange(SCR_H) + 0.5)) / FOCAL
    dx = np.broadcast_to(sx[None, :], (SCR_H, SCR_W))
    dz = np.broadcast_to(sy[:, None], (SCR_H, SCR_W))
    big = 1e9
    with np.errstate(divide="ignore", invalid="ignore"):
        t_side = np.where(np.abs(dx) > 1e-9, ROOM_HALF_W / np.abs(dx), big)
        t_floor = np.where(dz < -1e-9, EYE / -dz, big)
        t_ceil = np.where(dz > 1e-9, (ROOM_H - EYE) / dz, big)
    t_back = np.full((SCR_H, SCR_W), float(ROOM_DEPTH))
    T = np.stack([t_back, t_side, t_floor, t_ceil])
    which = T.argmin(0)
    t = T.min(0)
    x, y, z = dx * t, t, EYE + dz * t
    out = sky.astype(np.float64).copy()
    lit = np.ones((SCR_H, SCR_W))

    def put(mask, tex, u, v, factor=1.0):
        s = _sample(tex, u[mask], v[mask])
        if s.shape[-1] == 4:
            opaque = s[..., 3] > 0
            idx = np.argwhere(mask)[opaque]
            out[idx[:, 0], idx[:, 1]] = s[opaque][..., :3]
            lit[idx[:, 0], idx[:, 1]] = factor
            sky_idx = np.argwhere(mask)[~opaque]
            lit[sky_idx[:, 0], sky_idx[:, 1]] = -1          # sky: never darkened
        else:
            out[mask] = s
            lit[mask] = factor

    put(which == 0, back, x + ROOM_HALF_W, ROOM_H - z)
    m = (which == 1) & (dx < 0)
    put(m, left, y, ROOM_H - z, SIDE_CONTRAST)
    m = (which == 1) & (dx > 0)
    put(m, right, -y, ROOM_H - z, SIDE_CONTRAST)
    put(which == 2, floor, x + ROOM_HALF_W, -y)
    if ceil is not None:
        put(which == 3, ceil, x + ROOM_HALF_W, y)
    else:
        lit[which == 3] = -1
    fall = np.clip(1.12 - t / 700.0, 0.30, 1.0) * light
    fall = np.round(fall * LIGHT_BANDS) / LIGHT_BANDS
    factor = np.where(lit < 0, 1.0, fall * lit)
    rgb = np.clip(out * factor[..., None], 0, 255).astype(np.uint8)
    return as_array(quantise_rgb(rgb, version))


def tile_grid(rgb: np.ndarray, n: int = 3) -> np.ndarray:
    return np.tile(rgb, (n, n, 1))


def composite_over(top: np.ndarray, ground: np.ndarray) -> np.ndarray:
    """A masked texture over an opaque one of the same size (RGB out)."""
    a = (top[..., 3:4] > 0)
    return np.where(a, top[..., :3], ground[..., :3]).astype(np.uint8)


def load_approved(lump: str) -> np.ndarray:
    """An approved lump from assets/, read only (reference in the scenes)."""
    p = next(iter(ASSETS.glob(f"*/*/{lump}.png")), None)
    if p is None:
        raise FileNotFoundError(lump)
    with Image.open(p) as im:
        return as_array(im)


def shade_field(h: int, w: int) -> np.ndarray:
    return np.ones((h, w))


def apply(rgb: np.ndarray, f: np.ndarray) -> np.ndarray:
    return shade(rgb, f)
