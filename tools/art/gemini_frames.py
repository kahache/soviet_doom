"""First-person weapon frames from a pair of Gemini pixel-art images.

    python tools/art/gemini_frames.py ppsh            # the PPSh-41 pair, draft frames + preview
    python tools/art/gemini_frames.py ppsh --no-preview

The CEO's Gemini images (bare hands, flat magenta background, JPEG with black
letterbox bars) live in work/art/reference/gemini_<weapon>_A.jpg (ready) and
_B.jpg (firing, with a muzzle flash). They are gitignored and stay there; this
tool writes its frames under work/art/weapons/hand_G/<weapon>/ (gitignored),
where tools/make_draft_overlay.py picks them up with `--hand G --item <weapon>`.

D79 (2026-10-20): the method is adopted (D78 superseded) and Google Gemini
is credited. The frames are installed by copying them, grAb included, into
assets/sprites/<weapon>/ (the PPSh-41 first: tests/test_ppsh_sprites.py);
the source images never leave work/ (D77).

The pipeline, every step a pure function on arrays (tests/test_gemini_frames.py):
  1. crop_letterbox   - drop the black bars (columns/rows with nothing bright)
  2. key_magenta      - alpha from "magenta-ness" min(r,b)-g, tolerant of JPEG
                        noise, then a 1 px edge cleanup of pink-tinted rim pixels
  3. snap_palette     - every opaque pixel to its nearest palette v2 colour
  4. detect_grid      - Gemini's art pixel (~4-5 screen px): the period and
                        phase of the column/row edge-energy profiles
  5. grid_downsample  - one art pixel per cell, the mode of its indices
  6. split_flash      - the firing frame's flash cut out, the barrel end restored
                        from the ready frame shifted by the measured recoil
  7. mode_resize      - to Doom size: the gun's top TARGET px above the status
                        bar (x1.6 Freedoom's CHGGA0 = 56), 1.2 pixel aspect
  8. extend_edges     - every arm leaves the view cleanly: where the art is
                        cut by the image's side, a plain sleeve (a tube in
                        the sleeve's own shade ramp, dark outline on top,
                        tapering) takes over at the cut and runs on past the
                        widest view plus the bob, curving down out of the
                        canvas before its end, so no box edge is ever on
                        screen above the bar and no skin or wood is repeated
                        (mirroring the edge read as a hairy log, 2026-10-20);
                        the bottom row is smeared under the bar
  9. KICK             - the firing frame (and its flash) sit a few px up and
                        right: the recoil Gemini's pair does not draw
"""
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import palette  # noqa: E402

ROOT = artlib.PROJECT_ROOT
REF_DIR = ROOT / "work" / "art" / "reference"
OUT_ROOT = ROOT / "work" / "art" / "weapons" / "hand_G"
PREVIEW_DIR = OUT_ROOT / "preview"   # Gemini-derived sheets stay local with the frames (D77)
TT33_READY = ROOT / "assets" / "sprites" / "tt33" / "SDTTA0.png"

SCREEN_W, SCREEN_H = 320, 200
VIEW_H = 168                    # above the status bar
WEAPONTOP, BAR_LIFT = 32, 16    # hand_study's psprite model
PIXEL_ASPECT = 1.2              # Doom's 320x200 is shown at 4:3: Gemini's square pixels get squashed
BELOW_BAR = 20                  # px of arm kept under the bar (full-screen view is 16 px lower)
BOB_X = 16                      # Doom's horizontal weapon bob, px either way
WIDE_MARGIN = 54                # 16:9: the view is 200*1.2*16/9 = 427 px wide, 54 past 320 each side
ARM_EXIT = 112                  # px an arm cut by the image side runs on (> WIDE_MARGIN + BOB_X)
EDGE_TILE = 12                  # columns of the bottom row whose mode is the sleeve's colour
SLEEVE_SHADES = (0.3, 1.25, 1.0, 0.72)   # outline, light, mid, shadow: x the sleeve colour
SLEEVE_BANDS = (1, 3, 7)        # rows of outline, light, mid from the tube's top (shadow below)
SLEEVE_TAPER = 6                # the tube's top edge sinks this much more by its end
EXIT_POWER = 3                  # the curve down: drop ~ (k/ARM_EXIT)**3, nearly straight in 4:3
BOTTOM_PAD = 16                 # rows the bottom edge is smeared down (under the bar)
KICK = (2, -3)                  # the firing frame's recoil on screen: 2 px right, 3 px up
CHGG_HEIGHT_FALLBACK = 35       # hand_ref.PPSH_CHGG_HEIGHT, if hand_ref will not import
HEIGHT_MULT = 1.6               # the CEO's PPSh choice (D78): x1.6 of CHGGA0 above the bar
TRANSPARENT = -1
PINK_PALETTE = 40               # a palette colour with min(r,b)-g above this is never used


@dataclass(frozen=True)
class WeaponPair:
    name: str           # gemini_<name>_A.jpg / _B.jpg
    gun: str            # our held sprite (MOD-SPEC 6.3)
    flash: str          # our flash sprite
    height_mult: float = HEIGHT_MULT
    folder: str = ""    # assets/sprites/<folder>/ once installed (defaults to name)


WEAPONS = {"ppsh": WeaponPair("ppsh", "SDPP", "SDPF")}


# ------------------------------------------------------------ palette
def palette_rgb() -> np.ndarray:
    """Palette v2 (v1 + the approved v2 ramps), (n, 3) int."""
    return np.array(palette.colours(2), dtype=np.int32)


def magentaness(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.int32)
    return np.minimum(a[..., 0], a[..., 2]) - a[..., 1]


# ------------------------------------------------------------- 1. crop
def crop_letterbox(rgb: np.ndarray, dark: int = 40, margin: int = 3) -> np.ndarray:
    """Drop the black bars: outer columns/rows whose mean brightness is under
    `dark`, plus `margin` px of JPEG ringing at each cut bar."""
    lum = rgb.max(axis=2).astype(np.float64)
    cols, rows = np.flatnonzero(lum.mean(axis=0) > dark), np.flatnonzero(lum.mean(axis=1) > dark)
    if cols.size == 0:
        return rgb
    h, w = lum.shape
    c0, c1 = cols[0] + (margin if cols[0] > 0 else 0), cols[-1] + 1 - (margin if cols[-1] < w - 1 else 0)
    r0, r1 = rows[0] + (margin if rows[0] > 0 else 0), rows[-1] + 1 - (margin if rows[-1] < h - 1 else 0)
    return rgb[r0:r1, c0:c1]


# -------------------------------------------------------------- 2. key
def neighbours_any(mask: np.ndarray) -> np.ndarray:
    """True where any 4-neighbour is True."""
    out = np.zeros_like(mask)
    out[1:] |= mask[:-1]
    out[:-1] |= mask[1:]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def key_magenta(rgb: np.ndarray, threshold: int = 60, rim: int = 20) -> np.ndarray:
    """Alpha (bool) for a magenta-keyed image. Background: min(r,b)-g above
    `threshold` (JPEG noise keeps flat magenta far above it). Cleanup: an
    opaque pixel touching the background whose tint is still above `rim` is a
    blended fringe pixel and goes too (1 px)."""
    m = magentaness(rgb)
    alpha = m <= threshold
    fringe = alpha & neighbours_any(~alpha) & (m > rim)
    return alpha & ~fringe


# ---------------------------------------------------------- 3. palette
def snap_palette(rgb: np.ndarray, alpha: np.ndarray, pal: np.ndarray, chunk: int = 65536) -> np.ndarray:
    """Index array: nearest palette colour (weighted RGB) per opaque pixel, -1 elsewhere."""
    flat = rgb.reshape(-1, 3).astype(np.int32)
    out = np.full(flat.shape[0], TRANSPARENT, np.int32)
    w = np.array([3, 4, 2], np.int32)        # rough perceptual weights
    idx = np.flatnonzero(alpha.reshape(-1))
    for s in range(0, idx.size, chunk):
        sel = idx[s:s + chunk]
        d = (((flat[sel, None, :] - pal[None, :, :]) ** 2) * w).sum(axis=2)
        out[sel] = d.argmin(axis=1)
    out = out.reshape(alpha.shape)
    # a palette colour that is itself magenta-ish never survives (no pink fringe)
    pink = magentaness(pal) > PINK_PALETTE
    out[(out >= 0) & pink[np.clip(out, 0, None)]] = TRANSPARENT
    return out


# ------------------------------------------------------------- 4. grid
def edge_profile(lum: np.ndarray, alpha: np.ndarray, axis: int) -> np.ndarray:
    """Edge energy between neighbouring columns (axis=1) or rows (axis=0)."""
    d = np.abs(np.diff(lum, axis=axis)) * (np.diff(alpha.astype(np.int8), axis=axis) == 0)
    both = alpha[:, 1:] & alpha[:, :-1] if axis == 1 else alpha[1:] & alpha[:-1]
    e = (d * both).sum(axis=1 - axis).astype(np.float64)
    return e / (e.mean() or 1.0)


def _best_phase(e: np.ndarray, p: float) -> tuple[float, float]:
    best = (-1.0, 0.0)
    for ph in np.arange(0.0, p, 0.25):
        pos = np.floor(ph + np.arange(0, (e.size - ph) / p) * p).astype(int)
        pos = pos[pos < e.size]
        if pos.size:
            best = max(best, (float(e[pos].mean()), float(ph)))
    return best


def detect_grid(rgb: np.ndarray, alpha: np.ndarray, lo: float = 2.5, hi: float = 8.0,
                step: float = 0.05) -> tuple[float, float, float]:
    """(period, x phase, y phase): the source px per art pixel. The smallest
    period scoring within 85 % of the best wins (2p, 3p score alike)."""
    lum = rgb.astype(np.float64) @ np.array([0.299, 0.587, 0.114])
    ex, ey = edge_profile(lum, alpha, 1), edge_profile(lum, alpha, 0)
    scores = []
    for p in np.arange(lo, hi + 1e-9, step):
        sx, phx = _best_phase(ex, p)
        sy, phy = _best_phase(ey, p)
        scores.append((sx + sy, float(p), phx, phy))
    top = max(s[0] for s in scores)
    for s, p, phx, phy in scores:
        if s >= 0.85 * top:
            return round(p, 2), phx + 1.0, phy + 1.0   # an edge after column x: the cell starts at x+1
    raise AssertionError("unreachable")


# ---------------------------------------------------- 5/7. mode sampling
def _mode(vals: np.ndarray, pal: np.ndarray | None) -> int:
    """Opaque if at least half the samples are; then the commonest index,
    ties to the darkest (outlines survive)."""
    op = vals[vals >= 0]
    if op.size * 2 < vals.size or op.size == 0:
        return TRANSPARENT
    u, c = np.unique(op, return_counts=True)
    cand = u[c == c.max()]
    if cand.size > 1 and pal is not None:
        return int(cand[np.argmin(pal[cand].sum(axis=1))])
    return int(cand[0])


def sample_boxes(idx: np.ndarray, xs: np.ndarray, ys: np.ndarray, pal: np.ndarray | None) -> np.ndarray:
    """Mode of idx in the boxes [xs[i], xs[i+1]) x [ys[j], ys[j+1]) (float edges)."""
    h, w = idx.shape
    xi = np.clip(np.round(xs).astype(int), 0, w)
    yi = np.clip(np.round(ys).astype(int), 0, h)
    out = np.full((len(yi) - 1, len(xi) - 1), TRANSPARENT, np.int32)
    for j in range(len(yi) - 1):
        y0, y1 = yi[j], max(yi[j + 1], yi[j] + 1)
        for i in range(len(xi) - 1):
            x0, x1 = xi[i], max(xi[i + 1], xi[i] + 1)
            box = idx[y0:min(y1, h), x0:min(x1, w)]
            if box.size:
                out[j, i] = _mode(box.ravel(), pal)
    return out


def grid_downsample(idx: np.ndarray, period: float, phx: float, phy: float,
                    pal: np.ndarray | None = None) -> np.ndarray:
    """One art pixel per detected cell (partial cells at the borders included)."""
    h, w = idx.shape
    phx, phy = phx % period, phy % period
    xs = np.concatenate([[0.0], np.arange(phx if phx > 0.5 else phx + period, w, period), [w]])
    ys = np.concatenate([[0.0], np.arange(phy if phy > 0.5 else phy + period, h, period), [h]])
    return sample_boxes(idx, xs, ys, pal)


def mode_resize(idx: np.ndarray, new_w: int, new_h: int, pal: np.ndarray | None = None) -> np.ndarray:
    h, w = idx.shape
    return sample_boxes(idx, np.linspace(0, w, new_w + 1), np.linspace(0, h, new_h + 1), pal)


# ------------------------------------------------------------ 6. flash
def shift(idx: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.full_like(idx, TRANSPARENT)
    h, w = idx.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = \
        idx[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def estimate_recoil(a: np.ndarray, b: np.ndarray, r: int = 10) -> tuple[int, int]:
    """(dx, dy) moving A onto B: the shift with the best alpha overlap."""
    ob = b >= 0
    best = (-1.0, (0, 0))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            oa = shift(a, dx, dy) >= 0
            best = max(best, ((oa & ob).sum() / max(1, (oa | ob).sum()), (dx, dy)))
    return best[1]


def flash_coloured(rgb: np.ndarray) -> np.ndarray:
    r, g, b = (rgb[..., k].astype(np.int32) for k in range(3))
    warm = (r >= 200) & (g >= 90) & (b * 4 <= r * 3)
    white = rgb.min(axis=-1) >= 225
    return warm | white


def components(mask: np.ndarray) -> list[np.ndarray]:
    """4-connected components, as boolean masks (small images only)."""
    seen = np.zeros_like(mask)
    out = []
    h, w = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        comp = np.zeros_like(mask)
        stack = [(y0, x0)]
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            comp[y, x] = True
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append(comp)
    return out


def split_flash(a: np.ndarray, b: np.ndarray, pal: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """(B without its flash, the flash alone, recoil). The flash is the
    flash-coloured component of B with most pixels where shifted A is empty;
    it grows into its outline (B pixels where shifted A is empty, next to it);
    its place in B is refilled from shifted A (the barrel end)."""
    dx, dy = estimate_recoil(a, b)
    a_s = shift(a, dx, dy)
    rgb_b = np.where((b >= 0)[..., None], pal[np.clip(b, 0, None)], 0)
    cand = flash_coloured(rgb_b) & (b >= 0)
    comps = components(cand)
    if not comps:
        return b.copy(), np.full_like(b, TRANSPARENT), (dx, dy)
    flash = max(comps, key=lambda c: int((c & (a_s < 0)).sum()))
    for _ in range(3):   # the outline: B-only pixels touching the flash
        flash = flash | (neighbours_any(flash) & (b >= 0) & (a_s < 0))
    clean = b.copy()
    clean[flash] = a_s[flash]
    only = np.where(flash, b, TRANSPARENT)
    return clean, only, (dx, dy)


# ------------------------------------------------------------ 8. edges
def nearest_colour(rgb, pal: np.ndarray) -> int:
    """The palette index nearest to `rgb`, never a pink one."""
    d = ((pal.astype(np.int32) - np.clip(np.asarray(rgb, float), 0, 255).astype(np.int32)) ** 2).sum(axis=1)
    d[magentaness(pal) > PINK_PALETTE] = 1 << 30
    return int(np.argmin(d))


def sleeve_ramp(idx: np.ndarray, pal: np.ndarray, tile: int = EDGE_TILE) -> list[int]:
    """(outline, light, mid, shadow) for the sleeve the arm leaves in: its
    colour is the mode of the bottom row's last `tile` opaque pixels (the
    sleeve is what enters the frame from below), or of the edge column."""
    row = idx[-1, -tile:]
    vals = row[row >= 0]
    if not vals.size:
        vals = idx[:, -1][idx[:, -1] >= 0]
    base = pal[_mode(vals, None)].astype(float)
    return [nearest_colour(base * f, pal) for f in SLEEVE_SHADES]


def extend_edges(idx: np.ndarray, right: int, bottom: int, tile: int = EDGE_TILE,
                 power: float = EXIT_POWER, pal: np.ndarray | None = None) -> np.ndarray:
    """The last row smeared `bottom` rows down; then, if the art touches its
    right side, `right` columns more of plain sleeve (sleeve_ramp): a tube
    as tall as the cut (so it hides it) with a 1-px dark seam where it takes
    over, shaded down from its top edge outline-light-mid-shadow. No column
    of the art is repeated: mirroring the edge repeated skin and stock wood.
    Column k's top drops round(D * (k/right)**power) rows plus a taper of
    SLEEVE_TAPER * k/right, D the cut's height down to the canvas bottom, so
    the arm curves down and has left the canvas by the last column (always
    empty)."""
    h, w = idx.shape
    hb = h + bottom
    out = np.full((hb, w + right), TRANSPARENT, np.int32)
    out[:h, :w] = idx
    out[h:, :w] = idx[h - 1:h, :]
    if right <= 0 or not (idx[:, w - 1] >= 0).any():
        return out
    tile = max(1, min(tile, w))
    outline, light, mid, shadow = sleeve_ramp(out[:, :w], palette_rgb() if pal is None else pal, tile)
    top0 = int(np.flatnonzero(out[:, w - 1] >= 0)[0])
    drop_total = hb - top0
    edges = np.cumsum(SLEEVE_BANDS)
    for k in range(1, right + 1):
        f = k / right
        t = min(hb, top0 + int(round(drop_total * f ** power + SLEEVE_TAPER * f)))
        s = np.arange(hb - t)
        col = np.select([s < edges[0], s < edges[1], s < edges[2]], [outline, light, mid], shadow)
        out[t:, w - 1 + k] = outline if k == 1 else col
    return out


def arm_exits(idx: np.ndarray, length: int = ARM_EXIT, bottom: int = BOTTOM_PAD) -> tuple[np.ndarray, int]:
    """extend_edges on both sides: (canvas, columns added on the left). An
    arm cut by the left side of the image runs on leftwards the same way."""
    out = extend_edges(idx, length, bottom)
    if not (idx[:, 0] >= 0).any():
        return out, 0
    flipped = extend_edges(out[:, ::-1], length, 0)
    return flipped[:, ::-1], length


def visible_cuts(sub: np.ndarray, grab: tuple[int, int], bar_on: bool = True,
                 margin: int = WIDE_MARGIN + BOB_X) -> int:
    """Opaque pixels on the sprite's left, right or bottom border that some
    view could show: above the status bar (or above the screen bottom with
    the bar off, BAR_LIFT lower), within `margin` px of the 320-px screen
    at any horizontal bob. Doom's vertical bob only lowers the weapon. 0 is
    a clean exit."""
    x0, y0 = -grab[0], WEAPONTOP - grab[1] - (BAR_LIFT if bar_on else 0)
    floor = VIEW_H if bar_on else SCREEN_H
    h, w = sub.shape
    ys, xs = np.nonzero(sub >= 0)
    border = (xs == 0) | (xs == w - 1) | (ys == h - 1)
    sx, sy = x0 + xs[border], y0 + ys[border]
    return int(((sy < floor) & (sx >= -margin) & (sx < SCREEN_W + margin)).sum())


# --------------------------------------------------------------- output
def to_rgba(idx: np.ndarray, pal: np.ndarray) -> np.ndarray:
    rgba = np.zeros(idx.shape + (4,), np.uint8)
    op = idx >= 0
    rgba[op, :3] = pal[idx[op]]
    rgba[op, 3] = 255
    return rgba


def crop_with_grab(idx: np.ndarray, x0: int, y0: int) -> tuple[np.ndarray, tuple[int, int]]:
    """Crop to the opaque bbox. (x0, y0) is where idx's top-left sits on the
    320x200 screen with the bar on; grAb follows hand_study.place."""
    rows, cols = np.flatnonzero((idx >= 0).any(axis=1)), np.flatnonzero((idx >= 0).any(axis=0))
    r0, c0 = int(rows[0]), int(cols[0])
    sub = idx[r0:rows[-1] + 1, c0:cols[-1] + 1]
    sx, sy = x0 + c0, y0 + r0
    return sub, (-sx, WEAPONTOP - BAR_LIFT - sy)


def save_sprite(rgba: np.ndarray, grab: tuple[int, int], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *grab))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def chgg_height() -> int:
    try:
        import hand_ref
        return int(hand_ref.PPSH_CHGG_HEIGHT)
    except Exception:   # noqa: BLE001 - the pinned number is enough
        return CHGG_HEIGHT_FALLBACK


def check_prefixes(*names: str, own: str = "") -> None:
    """Our names must not be IWAD sprites nor installed by anything else
    (assets/sprites/<own>/ is this weapon's install: rebuilding is fine)."""
    sprites = ROOT / "assets" / "sprites"
    installed = {p.stem[:4].upper() for p in sprites.rglob("*.png")
                 if not (own and p.parent == sprites / own)}
    clash = [n for n in names if n in installed]
    iwad = ROOT / "iwads" / "freedoom2.wad"
    if iwad.is_file():
        import hand_study
        lumps, _ = hand_study.read_wad(iwad)
        clash += [n for n in names if any(k.startswith(n) for k in lumps)]
    if clash:
        raise SystemExit(f"gemini_frames: sprite names already taken: {sorted(set(clash))}")


# ---------------------------------------------------------------- build
def load_art(path: Path, pal: np.ndarray) -> tuple[np.ndarray, float]:
    rgb = crop_letterbox(np.asarray(Image.open(path).convert("RGB")))
    alpha = key_magenta(rgb)
    period, phx, phy = detect_grid(rgb, alpha)
    return grid_downsample(snap_palette(rgb, alpha, pal), period, phx, phy, pal), period


def build(w: WeaponPair, out_dir: Path | None = None) -> dict:
    pal = palette_rgb()
    out_dir = out_dir or OUT_ROOT / w.name
    check_prefixes(w.gun, w.flash, own=w.folder or w.name)
    a, pa = load_art(REF_DIR / f"gemini_{w.name}_A.jpg", pal)
    b, pb = load_art(REF_DIR / f"gemini_{w.name}_B.jpg", pal)
    hh, ww = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    a, b = a[:hh, :ww], b[:hh, :ww]
    clean, flash, recoil = split_flash(a, b, pal)
    # scale: A's top row TARGET px above the bar, BELOW_BAR px of arm under it
    target = round(chgg_height() * w.height_mult)
    top = int(np.flatnonzero((a >= 0).any(axis=1))[0])
    sy = (target + BELOW_BAR) / (hh - top)
    sx = sy * PIXEL_ASPECT
    nw, nh = round(ww * sx), round(hh * sy)
    y0 = VIEW_H - target - round(top * sy)       # screen row of the canvas top
    x0 = SCREEN_W - nw                           # the canvas's right edge on the screen's
    frames = {}
    still = (0, 0)
    for lump, art, pad, (kx, ky) in ((f"{w.gun}A0", a, True, still), (f"{w.gun}B0", clean, True, KICK),
                                     (f"{w.flash}A0", flash, False, KICK)):
        small, left = mode_resize(art, nw, nh, pal), 0
        if pad:
            small, left = arm_exits(small)
        sub, grab = crop_with_grab(small, x0 - left + kx, y0 + ky)
        rgba = to_rgba(sub, pal)
        frames[lump] = {"rgba": rgba, "grab": grab, "path": save_sprite(rgba, grab, out_dir / f"{lump}.png")}
    return {"frames": frames, "period": (pa, pb), "recoil": recoil, "kick": KICK, "target": target,
            "scale": (round(sx, 3), round(sy, 3)), "out_dir": out_dir}


# -------------------------------------------------------------- preview
def preview(w: WeaponPair, res: dict, stamp: str) -> Path:
    import hand_study as hs
    frames = res["frames"]
    gun_a, gun_b, fl = (frames[k] for k in (f"{w.gun}A0", f"{w.gun}B0", f"{w.flash}A0"))
    bg = hs.map01_backdrop()
    tt, tt_grab = hs.read_png_sprite(TT33_READY)
    ready = hs.draw_on_screen(bg, gun_a["rgba"], gun_a["grab"])
    firing = hs.draw_on_screen(hs.draw_on_screen(bg, gun_b["rgba"], gun_b["grab"]), fl["rgba"], fl["grab"])
    tt33 = hs.draw_on_screen(bg, tt, tt_grab)
    pad, lab = 16, 26
    zooms = [(k, Image.fromarray(v["rgba"]).resize((v["rgba"].shape[1] * 3, v["rgba"].shape[0] * 3),
                                                    Image.Resampling.NEAREST)) for k, v in frames.items()]
    row1_h = max(z.height for _, z in zooms) + lab
    mocks = [("ready (A)", ready, gun_a), ("firing (B, flash on)", firing, gun_b), ("TT-33 SDTTA0 for scale", tt33, None)]
    W = max(sum(z.width for _, z in zooms) + pad * (len(zooms) + 1), 3 * 640 + 4 * pad)
    H = 40 + row1_h + pad + lab + 400 + pad
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    f = hs.font(16)
    title = (f"{w.name} from Gemini A/B (D79) - art pixel {res['period'][0]:.2f}/"
             f"{res['period'][1]:.2f} src px, recoil {res['recoil']} art px, target {res['target']} px above the bar")
    d.rectangle((0, 0, W, 30), fill=hs.SHEET_BG + (255,))
    d.text((pad, 6), title, font=f, fill=hs.INK)
    x = pad
    for k, z in zooms:
        g = frames[k]
        d.rectangle((x, 40, x + z.width, 40 + lab - 4), fill=hs.SHEET_BG + (255,))
        d.text((x + 4, 42), f"{k} {z.width // 3}x{z.height // 3} grAb {g['grab'][0]},{g['grab'][1]}", font=f, fill=hs.INK)
        sheet.alpha_composite(z, (x, 40 + lab))
        x += z.width + pad
    y = 40 + row1_h + pad
    for i, (name, img, g) in enumerate(mocks):
        mx = pad + i * (640 + pad)
        m = hs.measure(g["rgba"], g["grab"]) if g else hs.measure(tt, tt_grab)
        d.rectangle((mx, y, mx + 640, y + lab - 4), fill=hs.SHEET_BG + (255,))
        d.text((mx + 4, y + 2), f"{name}: {m['height']} px above the bar, {m['area_pct']} % of view",
               font=f, fill=hs.INK)
        sheet.paste(Image.fromarray(img).resize((640, 400), Image.Resampling.NEAREST), (mx, y + lab))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    out = PREVIEW_DIR / f"{stamp}_F4_{w.name}-gemini-frames.png"
    sheet.save(out, optimize=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("weapon", choices=sorted(WEAPONS))
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args(argv)
    w = WEAPONS[args.weapon]
    res = build(w)
    for k, v in res["frames"].items():
        print(f"{k}: {v['rgba'].shape[1]}x{v['rgba'].shape[0]} grAb {v['grab'][0]},{v['grab'][1]} -> "
              f"{v['path'].relative_to(ROOT).as_posix()}")
    print(f"art pixel {res['period']}, recoil {res['recoil']}, scale {res['scale']}, target {res['target']}")
    if not args.no_preview:
        print("preview:", preview(w, res, datetime.now().strftime("%Y-%m-%d_%H%M")).relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
