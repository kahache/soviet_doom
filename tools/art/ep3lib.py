"""Shared machinery for the Episode 3 texture drafts (D112, phase P4).

Episode 3, «The Portal»: MAP07 the Arctic radar station on Novaya Zemlya
(tools/art/gen_arctic.py), MAP08 the Northern Fleet submarine base at
Severomorsk (tools/art/gen_naval.py), MAP09 the invaders' portal at the
Tunguska site (tools/art/gen_taiga.py). tools/art/gen_episode3.py renders
the three and writes the CEO's review sheet.

Same method as Episode 2 (ep2lib, read and reused, never modified): one
seed per piece (set BATCH_SEED + offset), numpy fields that wrap, vector
overlays at SUPERSAMPLE x, quantised to docs/art/palette.json without
dither, PNGs written to work/art/episode3/ only. Nothing is ever written
into assets/: these are drafts until the CEO says yes.

Palette rule for Episode 3: v1. A piece may ask for v2 only on the D66
precedent, and only for the ramp that precedent names:

  marble_red     fired-clay brick (SDBRCK1, D66)
  mosaic_cobalt  the portal (SDPORT1-4, D66: «nothing in the world may
                 share its colour»), so only the portal's own pieces may
                 use it (COBALT_PIECES; tests/test_gen_episode3.py holds it)

Gold and flesh never: the gold is the metro mosaic's, the flesh the Legion's.
ep2lib's quantiser only knows marble_red, so this module carries its own
(same rule, a per-piece list of ramps) and its own copy of the sample room's
last step.

Lettering: never a system font (D27). Cyrillic and digits come from our own
alphabet (assets/fonts/bigfont, D24) through ep2lib.glyph_masks, or from the
3x5 pixel digits of ep2lib; the invaders' glyphs are built here from rings,
ticks and dots, so they are no alphabet at all.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import DIMENSION_MULTIPLE, quantize, tiling_seam_score  # noqa: E402
import ep2lib  # noqa: E402
import gen_metro  # noqa: E402
import palette as palgen  # noqa: E402

PROJECT_ROOT = ep2lib.PROJECT_ROOT
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "episode3"
ASSETS = ep2lib.ASSETS
DECISION = "D112"

ALLOWED_WALL_SIZES = ep2lib.ALLOWED_WALL_SIZES
FLAT_SIZE = ep2lib.FLAT_SIZE
FRAMES = ep2lib.FRAMES
ALPHA_CUT = ep2lib.ALPHA_CUT
V2_RAMPS_ALLOWED = ("marble_red", "mosaic_cobalt")
COBALT_PIECES = ("SDPRTE1",)          # the portal's own pieces: the only ones that may use cobalt

col = ep2lib.col
rivet = ep2lib.rivet
wrap_dist = ep2lib.wrap_dist
cells_voronoi = ep2lib.cells_voronoi
illegible_label = ep2lib.illegible_label
digits_mask = ep2lib.digits_mask
stamp = ep2lib.stamp
glyph_masks = ep2lib.glyph_masks
paste_mask = ep2lib.paste_mask
any_to_rgb = gen_metro.any_to_rgb
as_array = ep2lib.as_array
mean_luma = ep2lib.mean_luma
tile_grid = ep2lib.tile_grid


@dataclasses.dataclass
class Piece(ep2lib.Piece):
    """ep2lib.Piece plus the v2 ramps a v2 piece asks for (empty for v1)."""
    v2_ramps: tuple = ()


# ================================================================ palette
def allowed_colours(version: int, ramps: tuple = ()) -> list[tuple[int, int, int]]:
    v1 = [tuple(c) for c in palgen.colours(1)]
    if version == 1:
        return v1
    extra = []
    for name in ramps:
        assert name in V2_RAMPS_ALLOWED, name
        extra += [tuple(c) for c in palgen.ramp_colours(name)]
    return v1 + extra


def quantise_rgb(rgb: np.ndarray, version: int, ramps: tuple = ()) -> Image.Image:
    """No-dither quantisation restricted to v1 plus the piece's own v2 ramps;
    the image carries the full palette of its version (v1: 162; v2: 226)."""
    if version == 1:
        return quantize(Image.fromarray(np.ascontiguousarray(rgb), "RGB"))
    pimg = Image.new("P", (1, 1))
    pimg.putpalette([v for c in allowed_colours(version, ramps) for v in c])
    snapped = Image.fromarray(np.ascontiguousarray(rgb), "RGB").quantize(
        palette=pimg, dither=Image.Dither.NONE).convert("RGB")
    return gen_metro.quantize_version(np.asarray(snapped), version)


def quantise(rgb: np.ndarray, version: int, ramps: tuple = ()) -> Image.Image:
    """RGB in -> indexed out; RGBA in -> RGBA out with hard alpha and every
    opaque pixel a palette colour (the SDCHAN1 exception, ART-BIBLE §2)."""
    if rgb.shape[2] == 4:
        q = np.asarray(quantise_rgb(rgb[..., :3], version, ramps).convert("RGB")).copy()
        alpha = np.where(rgb[..., 3] >= ALPHA_CUT, 255, 0).astype(np.uint8)
        q[alpha == 0] = 0
        return Image.fromarray(np.dstack([q, alpha]).astype(np.uint8), "RGBA")
    return quantise_rgb(rgb, version, ramps)


# ================================================================ helpers
def overlay_to_rgba(ov) -> np.ndarray:
    """An artlib.Overlay box-downsampled to texture size with hard alpha
    (premultiplied, so edge pixels keep their colour; the SDINSL1 recipe)."""
    small = np.asarray(ov.img.resize((ov.w, ov.h), Image.Resampling.BOX), dtype=np.uint8).copy()
    alpha = np.where(small[..., 3] >= ALPHA_CUT, 255, 0).astype(np.uint8)
    rgb = np.where(alpha[..., None] > 0, small[..., :3], 0).astype(np.uint8)
    return np.dstack([rgb, alpha])


def cylinder(t: np.ndarray, lo: float = 0.55, hi: float = 1.25) -> np.ndarray:
    """Shading across a cylinder, t in [0,1] from its lit edge to its dark
    one: bright just past the lit edge, dark at the far rim."""
    t = np.clip(t, 0, 1)
    return lo + (hi - lo) * np.clip(np.sin(np.pi * (t * 0.85 + 0.08)) * (1.15 - 0.6 * t), 0, 1)


def ridged(f: np.ndarray) -> np.ndarray:
    """1 at the 0.5 contour of a [0,1] field, falling off to 0: filaments."""
    return 1 - np.abs(2 * f - 1)


# ================================================================ build
def build_set(set_name: str, pieces: list[Piece], batch_seed: int, script_rel: str,
              out_dir: Path | None = None) -> tuple[list[dict], dict]:
    """Render every piece of a set into work/art/episode3/<set>/. Returns
    (manifest entries, quantised arrays by lump)."""
    out_dir = out_dir or WORK_ROOT / set_name
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for p in pieces:
        frames = ep2lib.frames_of(p)
        assert len(frames) == len(p.lumps), p.key
        assert (p.palette == 2) == bool(p.v2_ramps), p.key
        assert "mosaic_cobalt" not in p.v2_ramps or p.key in COBALT_PIECES, p.key
        for lump, rgb in zip(p.lumps, frames):
            assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
            h, w = rgb.shape[:2]
            assert (w, h) == p.size, (lump, w, h)
            assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, lump
            img = quantise(rgb, p.palette, p.v2_ramps)
            img.save(out_dir / f"{lump}.png", optimize=True)
            arrays[lump] = as_array(img)
        first = arrays[p.lumps[0]]
        colours = {tuple(int(v) for v in c) for c in first[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": p.key, "lumps": p.lumps, "kind": p.kind, "set": set_name,
            "width": p.size[0], "height": p.size[1], "palette_version": p.palette,
            "v2_ramps": list(p.v2_ramps), "masked": p.masked, "tiles": p.tiles, "script": script_rel,
            "seed": batch_seed + p.offset,
            "files": [f"work/art/episode3/{set_name}/{lump}.png" for lump in p.lumps],
            "colours_used": len(colours), "mean_luma": round(mean_luma(first), 1),
            "seam_score": None if p.masked else round(tiling_seam_score(first[..., :3]), 2),
            "title_es": p.title, "description_es": p.desc, "status": f"draft, proposed (P4, {DECISION})",
        })
    return entries, arrays


# ================================================================ sample room
def render_room(back, left, right, floor, ceil=None, light: float = 1.0, version: int = 1,
                ramps: tuple = (), sky=None) -> np.ndarray:
    """ep2lib.render_room (the 320x200 Doom-like view; NOT the engine) with
    this module's quantiser as the last step, so a cobalt rim survives."""
    sky = ep2lib.sky_image() if sky is None else sky
    S_W, S_H, F = ep2lib.SCR_W, ep2lib.SCR_H, ep2lib.FOCAL
    sx = (np.arange(S_W) + 0.5 - S_W / 2) / F
    sy = (S_H / 2 - (np.arange(S_H) + 0.5)) / F
    dx = np.broadcast_to(sx[None, :], (S_H, S_W))
    dz = np.broadcast_to(sy[:, None], (S_H, S_W))
    big = 1e9
    half, depth, eye, room_h = ep2lib.ROOM_HALF_W, ep2lib.ROOM_DEPTH, ep2lib.EYE, ep2lib.ROOM_H
    with np.errstate(divide="ignore", invalid="ignore"):
        t_side = np.where(np.abs(dx) > 1e-9, half / np.abs(dx), big)
        t_floor = np.where(dz < -1e-9, eye / -dz, big)
        t_ceil = np.where(dz > 1e-9, (room_h - eye) / dz, big)
    T = np.stack([np.full((S_H, S_W), float(depth)), t_side, t_floor, t_ceil])
    which = T.argmin(0)
    t = T.min(0)
    x, y, z = dx * t, t, eye + dz * t
    out = sky.astype(np.float64).copy()
    lit = np.ones((S_H, S_W))

    def put(mask, tex, u, v, factor=1.0):
        s = ep2lib._sample(tex, u[mask], v[mask])
        if s.shape[-1] == 4:
            opaque = s[..., 3] > 0
            idx = np.argwhere(mask)[opaque]
            out[idx[:, 0], idx[:, 1]] = s[opaque][..., :3]
            lit[idx[:, 0], idx[:, 1]] = factor
            sky_idx = np.argwhere(mask)[~opaque]
            lit[sky_idx[:, 0], sky_idx[:, 1]] = -1
        else:
            out[mask] = s[..., :3]
            lit[mask] = factor

    put(which == 0, back, x + half, room_h - z)
    put((which == 1) & (dx < 0), left, y, room_h - z, ep2lib.SIDE_CONTRAST)
    put((which == 1) & (dx > 0), right, -y, room_h - z, ep2lib.SIDE_CONTRAST)
    put(which == 2, floor, x + half, -y)
    if ceil is not None:
        put(which == 3, ceil, x + half, y)
    else:
        lit[which == 3] = -1
    fall = np.clip(1.12 - t / 700.0, 0.30, 1.0) * light
    fall = np.round(fall * ep2lib.LIGHT_BANDS) / ep2lib.LIGHT_BANDS
    factor = np.where(lit < 0, 1.0, fall * lit)
    rgb = np.clip(out * factor[..., None], 0, 255).astype(np.uint8)
    return as_array(quantise_rgb(rgb, version, ramps))


def night_sky(seed: int = 5701) -> np.ndarray:
    """Screen-space polar night for the Arctic and taiga rooms: dark
    steel-blue, a band of lighter cloud low down."""
    from artlib import fbm
    rng = np.random.default_rng(seed)
    S_W, S_H = ep2lib.SCR_W, ep2lib.SCR_H
    yy = np.linspace(0, 1, S_H)[:, None] * np.ones((1, S_W))
    clouds = fbm(S_W, S_H, 6, 4, rng, 0.55, aspect=0.4)
    t = np.clip(0.18 + 0.22 * yy + (clouds - 0.5) * 0.18, 0, 1)
    return any_to_rgb(t, "steel_blue")


def load_approved(lump: str) -> np.ndarray:
    return ep2lib.load_approved(lump)
