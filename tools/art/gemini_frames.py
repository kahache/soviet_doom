"""First-person weapon frames from a pair of Gemini pixel-art images.

    python tools/art/gemini_frames.py ppsh            # the PPSh-41 pair, draft frames + preview
    python tools/art/gemini_frames.py ppsh --no-preview
    python tools/art/gemini_frames.py izh             # also rpg7, roks3, katyusha, ice_axe (drafts)

The CEO's Gemini images (bare hands, flat magenta background, JPEG with black
letterbox bars) live in work/art/reference/gemini_<weapon>_A.jpg (ready) and
_B.jpg (firing, with a muzzle flash). They are gitignored and stay there; this
tool writes its frames under work/art/weapons/hand_G/<weapon>/ (gitignored),
where tools/make_draft_overlay.py picks them up with `--hand G --item <weapon>`.
The second round (the five other weapons) is 1024x765 PNGs on a 320x240 art
grid, the IZh's ready image a 1200x896 JPEG; each WEAPONS entry names its
images (`sources`, the IZh has a third: the reload) and its lumps (`frames`:
which image, flash or gun, kick, pose, a fading flash's scale), so the
states' letters each get a frame. Per weapon, where Gemini's art needs it:
`drop` (a stray hand), `restore` (smoke drawn over the gun at the image's
side: A's pixels there), `flash_halo` (sparks and fringe round the flash),
`taper` (a flame cut by the side ends in a point), `arm_band` (an arm leaving
through the side at mid-height runs on as a tube, not a wedge).

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
# What the art carries out through its side, per row (edge_materials): only
# the sleeve (and skin, which ends in the sleeve's cuff) runs on as the tube;
# wood is a stock and runs on as its own straight bar, in front of the sleeve.
OUTLINE, METAL, SKIN, WOOD, SLEEVE = "outline", "metal", "skin", "wood", "sleeve"
DARK_VALUE = 40                 # max channel below this: an outline pixel
GREY_SAT = 0.2                  # saturation below this (or blue >= red): metal
SLEEVE_HUE = 8                  # degrees from the sleeve's hue: still sleeve
SKIN_SAT, SKIN_VALUE = 0.55, 150   # light and less saturated than wood: skin
EDGE_PROBE = 3                  # last columns whose per-row majority is the row's material
STOCK_PROBE = 8                 # last columns the stock's axis is measured over
STOCK_EXIT = 0.75               # the stock has left the canvas by this fraction of the run-on
WOOD_BANDS = (1, 3, 0.6)        # rows of outline, light, then mid down to this fraction (shadow, outline below)
WOOD_GRAIN = 0.5                # x the wood colour: the dashed grain line along the stock
GRAIN_DASH = (7, 4)             # grain period and dash length, columns
KICK = (2, -3)                  # the firing frame's recoil on screen: 2 px right, 3 px up
CHGG_HEIGHT_FALLBACK = 35       # hand_ref.PPSH_CHGG_HEIGHT, if hand_ref will not import
HEIGHT_MULT = 1.6               # the CEO's PPSh choice (D78): x1.6 of CHGGA0 above the bar
TRANSPARENT = -1
PINK_PALETTE = 40               # a palette colour with min(r,b)-g above this is never used
SPARK_MAX = 40                  # art px: a piece of B this small that A lacks is a spark (split_flash, halo on)
TAPER_LEN = 14                  # art columns a flame cut by the image side narrows over to a point
TAPER_GAP = 2                   # columns left empty before the side, so nothing touches it
BOTTOM_GAP = 12                 # rows of background Gemini may leave under the arms (fill_bottom)
ROT_UP = 8                      # RotSprite: the art scale2x'd to 8x before a turn (D86)
PIVOT_BELOW = 50                # px under the bar line: the elbow a swing frame turns about (D86)
RUN_ON_FIT = 16                 # last art rows a piece leaving the bottom is followed up for its axis
SWING_WINDUP, SWING_STRIKE, SWING_FOLLOW = -11, 38, 48   # the ice axe's swing, degrees CCW (D86)
SWING_LIFT = 34                 # screen px C is raised after its turn (D the same, 6 px lower): the hand stays in view
SWING_PAD = 0.5                 # x the art's width added each side before a turn (nothing is cut)


@dataclass(frozen=True)
class Frame:
    """One lump cut from one of a weapon's Gemini images."""
    lump: str                        # e.g. "SDIZB0"
    src: str = "A"                   # the image it comes from (WeaponPair.sources)
    flash: bool = False              # the flash alone (else the art, its flash cut out)
    kick: tuple[int, int] = (0, 0)   # screen px right and down (KICK on a firing frame)
    pose: str = ""                   # "A": moved by -recoil onto the ready image's pose
    scale: float = 1.0               # a flash shrunk about its root (a fading frame)
    rot: float = 0.0                 # degrees counter-clockwise: src turned about the elbow (swing, D86)
    lift: int = 0                    # screen px the turned piece is raised (the elbow comes up with it)


@dataclass(frozen=True)
class WeaponPair:
    name: str           # gemini_<name>_A.jpg / _B.jpg unless `sources` says otherwise
    gun: str            # our held sprite (MOD-SPEC 6.3)
    flash: str          # our flash sprite
    height_mult: float = HEIGHT_MULT
    folder: str = ""    # assets/sprites/<folder>/ once installed (defaults to name)
    sources: tuple[tuple[str, str], ...] = ()   # (key, file in REF_DIR); "A" is the ready image
    frames: tuple[Frame, ...] = ()              # default: the PPSh's gun A, gun B kicked, flash A kicked
    drop: tuple[tuple[str, int, int], ...] = () # (key, x, y): the art piece at (x, y) of that image's
                                                # art grid is removed (a stray hand Gemini drew)
    restore: tuple[tuple[str, int, int, int, int], ...] = ()   # (key, x0, y0, x1, y1): in that box of
                                                # the art grid the image is A's, moved by the recoil
                                                # (smoke Gemini drew over the gun, cut by the side)
    x_shift: int = 0    # screen px right of the default placement (the art's right side on the screen's)
    flash_grow: int = 3 # rings of B-only pixels the flash grows over (its smoke)
    flash_halo: int = 0 # px round the flash whose B-only pixels go with it (split_flash)
    arm_band: bool = False  # an arm cut by the side runs on as a tube of its own thickness (extend_edges)
    arm_curve: bool = True  # False: that tube runs on straight along the forearm's axis (the ice axe, D84)
    taper: bool = False # a flash cut by the image's side ends in a point (taper_cut; the PPSh's is as built)
    mocks: tuple[tuple[str, tuple[str, ...]], ...] = ()   # preview: (label, lumps drawn in order)

    def files(self) -> dict[str, str]:
        return dict(self.sources) or {"A": f"gemini_{self.name}_A.jpg", "B": f"gemini_{self.name}_B.jpg"}

    def frame_list(self) -> tuple[Frame, ...]:
        return self.frames or (Frame(f"{self.gun}A0"), Frame(f"{self.gun}B0", "B", kick=KICK),
                               Frame(f"{self.flash}A0", "B", flash=True, kick=KICK))

    def mock_list(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return self.mocks or (("ready (A)", (f"{self.gun}A0",)),
                              ("firing (B, flash on)", (f"{self.gun}B0", f"{self.flash}A0")))


HALF_KICK = (KICK[0] // 2, KICK[1] // 2)
GEM = "gemini_{}_{}.png"   # the 1024x765 PNGs of D79's second round (320x240 art pixels each)

WEAPONS = {
    "ppsh": WeaponPair("ppsh", "SDPP", "SDPF"),
    # IZh-58 (izh.zs, SHTG/SHTF): fire A+flash, B, C, A; reload D, C, B, A.
    # B is the shot's recoil, C half of it (the gun settling, or rising as it
    # snaps shut after the reload), D the break-open reload (image C). The
    # flash plays over A (the ready pose), so it is moved onto A's pose.
    "izh": WeaponPair(
        "izh", "SDIZ", "SDIF", taper=True, flash_halo=6,
        sources=(("A", "gemini_izh_A.jfif"), ("B", GEM.format("izh", "B")), ("C", GEM.format("izh", "C"))),
        frames=(Frame("SDIZA0"), Frame("SDIZB0", "B", kick=KICK), Frame("SDIZC0", "B", kick=HALF_KICK),
                Frame("SDIZD0", "C"),
                Frame("SDIFA0", "B", flash=True, pose="A"), Frame("SDIFB0", "B", flash=True, pose="A", scale=0.6)),
        mocks=(("ready (A)", ("SDIZA0",)), ("firing (A + SDIF A)", ("SDIZA0", "SDIFA0")),
               ("recoil (B)", ("SDIZB0",)), ("reload (D)", ("SDIZD0",)))),
    # RPG-7 (rpg7.zs, MISG/MISF): B is every firing tic; the flash A-D plays
    # over B, fading. The backblast cloud at the image's right side is
    # dropped (behind the shooter; cut by the image side).
    "rpg7": WeaponPair(
        "rpg7", "SDRL", "SDRF", taper=True,
        sources=(("A", GEM.format("rpg7", "A")), ("B", GEM.format("rpg7", "B"))),
        frames=(Frame("SDRLA0"), Frame("SDRLB0", "B", kick=KICK),
                Frame("SDRFA0", "B", flash=True, kick=KICK), Frame("SDRFB0", "B", flash=True, kick=KICK, scale=0.8),
                Frame("SDRFC0", "B", flash=True, kick=KICK, scale=0.6),
                Frame("SDRFD0", "B", flash=True, kick=KICK, scale=0.4)),
        restore=(("B", 286, 150, 321, 240),), flash_grow=12, flash_halo=12, arm_band=True),
    # ROKS-3 (roks3.zs, PLSG/PLSF): the flame plays over A while the trigger
    # is held; B (20 tics) is the gun once it is let go, in A's pose.
    "roks3": WeaponPair(
        "roks3", "SDRK", "SDKF", taper=True, flash_halo=6,
        sources=(("A", GEM.format("roks3", "A")), ("B", GEM.format("roks3", "B"))),
        frames=(Frame("SDRKA0"), Frame("SDRKB0", "B", pose="A"), Frame("SDKFA0", "B", flash=True, pose="A")),
        mocks=(("ready (A)", ("SDRKA0",)), ("firing (A + SDKF A)", ("SDRKA0", "SDKFA0"))),
        flash_grow=12),
    # Hand Katyusha (katyusha.zs, BFGG/BFGF): B fires and reloads, the flash
    # and its smoke A-B play over B.
    "katyusha": WeaponPair(
        "katyusha", "SDHK", "SDHF", taper=True, flash_halo=6,
        sources=(("A", GEM.format("katyusha", "A")), ("B", GEM.format("katyusha", "B"))),
        frames=(Frame("SDHKA0"), Frame("SDHKB0", "B", kick=KICK),
                Frame("SDHFA0", "B", flash=True, kick=KICK), Frame("SDHFB0", "B", flash=True, kick=KICK, scale=0.7)),
        flash_grow=12),
    # Ice axe (ice_axe.zs, PUNG): fire B, C (the blow), D, C, B. A ready.
    # D86: the whole swing is A turned as one rigid piece (hand, axe and
    # forearm) about the elbow, PIVOT_BELOW under the bar, so the hand
    # never deforms (Gemini's strike image B kept a crooked hand, dropped):
    # B the wind-up (head back to the right), C the strike (head to the
    # left, pick down towards the centre), D the follow-through (further
    # and a little lower). Taller than the guns (D76: long shaft, big head).
    "ice_axe": WeaponPair(
        "ice_axe", "SDAX", "", height_mult=72 / CHGG_HEIGHT_FALLBACK,
        sources=(("A", GEM.format("iceaxe", "A")),),
        frames=(Frame("SDAXA0"), Frame("SDAXB0", rot=SWING_WINDUP), Frame("SDAXC0", rot=SWING_STRIKE, lift=SWING_LIFT),
                Frame("SDAXD0", rot=SWING_FOLLOW, lift=SWING_LIFT - 6)),
        arm_band=True, arm_curve=False,
        mocks=(("ready (A)", ("SDAXA0",)), ("wind-up (B)", ("SDAXB0",)), ("strike (C)", ("SDAXC0",)),
               ("follow-through (D)", ("SDAXD0",)))),
}


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


def split_flash(a: np.ndarray, b: np.ndarray, pal: np.ndarray,
                grow: int = 3, halo: int = 0) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """(B without its flash, the flash alone, recoil). The flash is the
    flash-coloured component of B with most pixels where shifted A is empty;
    it grows into its outline (B pixels where shifted A is empty, next to it,
    `grow` rings: more takes in a smoke cloud round it; then any B-only
    pixel within `halo` px of it, across the background: the loose sparks
    and fringe Gemini scatters round a flash);
    its place in B is refilled from shifted A (the barrel end)."""
    dx, dy = estimate_recoil(a, b)
    a_s = shift(a, dx, dy)
    rgb_b = np.where((b >= 0)[..., None], pal[np.clip(b, 0, None)], 0)
    cand = flash_coloured(rgb_b) & (b >= 0)
    comps = components(cand)
    if not comps:
        return b.copy(), np.full_like(b, TRANSPARENT), (dx, dy)
    flash = max(comps, key=lambda c: int((c & (a_s < 0)).sum()))
    for _ in range(grow):   # the outline: B-only pixels touching the flash
        flash = flash | (neighbours_any(flash) & (b >= 0) & (a_s < 0))
    near = flash.copy()
    for _ in range(halo):
        near = near | neighbours_any(near)
    flash = flash | (near & (b >= 0) & (a_s < 0))
    if halo:   # loose sparks further out: small pieces of B that A does not have
        for c in components((b >= 0) & ~flash):
            if c.sum() <= SPARK_MAX and (a_s[c] < 0).mean() > 0.5:
                flash = flash | c
    clean = b.copy()
    clean[flash] = a_s[flash]
    only = np.where(flash, b, TRANSPARENT)
    return clean, only, (dx, dy)


def flash_root(flash: np.ndarray, gun: np.ndarray) -> tuple[float, float]:
    """(row, column) the flash comes out of: the mean of its pixels touching
    the gun (the muzzle), or of all of them if none does."""
    op = flash >= 0
    root = op & neighbours_any(gun >= 0)
    ys, xs = np.nonzero(root if root.any() else op)
    return float(ys.mean()), float(xs.mean())


def shrink_flash(flash: np.ndarray, gun: np.ndarray, f: float, pal: np.ndarray) -> np.ndarray:
    """The flash scaled by `f` about its root (flash_root): a fading frame."""
    if f == 1.0 or not (flash >= 0).any():
        return flash.copy()
    ry, rx = flash_root(flash, gun)
    rows, cols = np.flatnonzero((flash >= 0).any(axis=1)), np.flatnonzero((flash >= 0).any(axis=0))
    y0, x0 = int(rows[0]), int(cols[0])
    sub = flash[y0:rows[-1] + 1, x0:cols[-1] + 1]
    small = mode_resize(sub, max(1, round(sub.shape[1] * f)), max(1, round(sub.shape[0] * f)), pal)
    out = np.full_like(flash, TRANSPARENT)
    ty, tx = round(ry - (ry - y0) * f), round(rx - (rx - x0) * f)
    h, w = out.shape
    sh, sw = small.shape
    ys, xs = slice(max(0, ty), min(h, ty + sh)), slice(max(0, tx), min(w, tx + sw))
    out[ys, xs] = small[ys.start - ty:ys.stop - ty, xs.start - tx:xs.stop - tx]
    return out


def taper_cut(flash: np.ndarray, length: int = TAPER_LEN, gap: int = TAPER_GAP) -> np.ndarray:
    """A flash (a flame jet) cut by the image's left or right side or its top
    ends in a point instead: over the last `length` columns before the cut
    each column keeps only the middle of its pixels, the kept height
    shrinking linearly to nothing `gap` columns short of the side."""
    out = flash.copy()
    views = ((lambda a: a), (lambda a: a[:, ::-1]), (lambda a: a.T))   # left, right, top
    for view in views:
        v = view(out)                   # a view: writing into it writes `out`
        op = v >= 0
        if not op[:, 0].any():
            continue
        n = min(length, v.shape[1] - 1)
        for c in range(n):
            rs = np.flatnonzero(op[:, c])
            if not rs.size:
                continue
            mid, half = (rs[0] + rs[-1]) / 2, (rs[-1] - rs[0]) / 2
            keep = half * max(0.0, (c - gap) / max(1, n - gap)) if c >= gap else -1.0
            v[np.abs(np.arange(v.shape[0]) - mid) > keep, c] = TRANSPARENT
    return out


def fill_bottom(idx: np.ndarray, reach: int = BOTTOM_GAP) -> np.ndarray:
    """Gemini sometimes leaves a strip of background under the arms: the row
    above the art's last one is smeared down to the image's bottom when the
    art ends within `reach` rows of it (its own last row is often an
    outline)."""
    rows = np.flatnonzero((idx >= 0).any(axis=1))
    h = idx.shape[0]
    if not rows.size or rows[-1] == h - 1 or h - 1 - rows[-1] > reach or rows[-1] < 1:
        return idx
    out = idx.copy()
    out[rows[-1]:] = idx[rows[-1] - 1]
    return out


def drop_piece(idx: np.ndarray, x: int, y: int) -> np.ndarray:
    """idx without the 4-connected piece of art holding pixel (x, y)."""
    if idx[y, x] < 0:
        raise ValueError(f"drop_piece: art pixel ({x}, {y}) is empty")
    out = idx.copy()
    op = idx >= 0
    h, w = idx.shape
    stack, seen = [(y, x)], np.zeros_like(op)
    seen[y, x] = True
    while stack:
        cy, cx = stack.pop()
        out[cy, cx] = TRANSPARENT
        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
            if 0 <= ny < h and 0 <= nx < w and op[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
    return out


# ------------------------------------------------------------ 7b. swing
def scale2x(idx: np.ndarray) -> np.ndarray:
    """EPX/Scale2x: each pixel becomes 2x2, a corner taking a neighbour's
    colour where two neighbours agree, so diagonals stay clean steps."""
    p = np.pad(idx, 1, mode="edge")
    c = p[1:-1, 1:-1]
    up, down, left, right = p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]
    h, w = idx.shape
    out = np.empty((2 * h, 2 * w), idx.dtype)
    out[0::2, 0::2] = np.where((left == up) & (left != down) & (up != right), up, c)
    out[0::2, 1::2] = np.where((up == right) & (up != left) & (right != down), right, c)
    out[1::2, 0::2] = np.where((down == left) & (down != right) & (left != up), left, c)
    out[1::2, 1::2] = np.where((right == down) & (right != up) & (down != left), down, c)
    return out


def block_mode(big: np.ndarray, f: int, chunk: int = 16) -> np.ndarray:
    """big downscaled f times: each f x f block opaque if at least half of
    it is (as _mode), then its commonest index."""
    h, w = big.shape[0] // f, big.shape[1] // f
    out = np.full((h, w), TRANSPARENT, np.int32)
    n = 257                                          # TRANSPARENT and the 256 palette indices
    for r0 in range(0, h, chunk):
        r1 = min(h, r0 + chunk)
        v = big[r0 * f:r1 * f, :w * f].reshape(r1 - r0, f, w, f).transpose(0, 2, 1, 3).reshape(-1, f * f)
        v = v.astype(np.int64) + 1
        counts = np.bincount((np.arange(len(v))[:, None] * n + v).ravel(), minlength=len(v) * n).reshape(-1, n)
        opaque = counts[:, 0] * 2 <= f * f
        out[r0:r1] = np.where(opaque, counts[:, 1:].argmax(axis=1), TRANSPARENT).reshape(r1 - r0, w)
    return out


def rotsprite(idx: np.ndarray, deg: float, pivot: tuple[float, float], up: int = ROT_UP,
              out_h: int | None = None, lift: float = 0.0) -> np.ndarray:
    """idx turned `deg` degrees counter-clockwise as seen (y down) about
    pivot (x, y) in idx's pixels, same shape (its first `out_h` rows), RotSprite-style: scale2x to
    `up` times, turned by nearest sampling, back down by block mode. No
    pixel is blended, so the result is still palette indices. `lift`:
    then raised that many pixels (what was under the last row comes in)."""
    big = idx.astype(np.int16)
    for _ in range(int(round(np.log2(up)))):
        big = scale2x(big)
    hb, wb = big.shape
    t = np.radians(deg)
    c, s = np.cos(t), np.sin(t)
    ys, xs = np.mgrid[0:(hb if out_h is None else out_h * up), 0:wb].astype(np.float32)
    ex, ey = xs + 0.5 - pivot[0] * up, ys + 0.5 + (lift - pivot[1]) * up
    sx = np.floor(c * ex - s * ey + pivot[0] * up).astype(np.int64)
    sy = np.floor(s * ex + c * ey + pivot[1] * up).astype(np.int64)
    inside = (sx >= 0) & (sx < wb) & (sy >= 0) & (sy < hb)
    out = np.full(xs.shape, TRANSPARENT, np.int16)
    out[inside] = big[sy[inside], sx[inside]]
    return block_mode(out, up)


def bottom_pieces(idx: np.ndarray, fit: int = RUN_ON_FIT) -> list[tuple[int, int, float]]:
    """(x0, x1, dx per row down) of each run of art on the last row (the
    sleeve, the axe's handle): its middle followed up `fit` rows, each
    row's runs those overlapping the row below's."""
    h = idx.shape[0]
    out = []
    for a, b in _runs(np.flatnonzero(idx[-1] >= 0).tolist(), gap=1):
        mids, lo, hi = [], a, b
        for r in range(h - 1, max(-1, h - 1 - fit), -1):
            near = [(x0, x1) for x0, x1 in _runs(np.flatnonzero(idx[r] >= 0).tolist(), gap=1)
                    if x1 >= lo - 2 and x0 <= hi + 2]
            if not near:
                break
            lo, hi = near[0][0], near[-1][1]
            mids.append(((lo + hi) / 2, r))
        slope = 0.0
        if len(mids) > 2:
            m = np.array(mids)
            slope = float(np.polyfit(m[:, 1], m[:, 0], 1)[0])
        out.append((a, b, slope))
    return out


def run_on_down(idx: np.ndarray, rows: int) -> np.ndarray:
    """idx with `rows` more rows: each piece leaving the bottom runs on
    straight along its own axis (bottom_pieces), its last row copied and
    slid along, so the sleeve stays a straight sleeve and the handle a handle."""
    h, w = idx.shape
    out = np.full((h + rows, w), TRANSPARENT, np.int32)
    out[:h] = idx
    for a, b, slope in bottom_pieces(idx):
        for k in range(1, rows + 1):
            d = int(round(slope * k))
            x0, x1 = max(0, a + d), min(w, b + 1 + d)
            if x0 < x1:
                out[h - 1 + k, x0:x1] = idx[-1, x0 - d:x1 - d]
    return out


def swing(art: np.ndarray, deg: float, pivot: tuple[float, float], pad: int, below: int,
          lift: float = 0.0, keep: int = 0) -> np.ndarray:
    """A swing frame from the ready art (D86): `pad` columns each side,
    every piece leaving the bottom run on `below` rows along its axis, all
    turned `deg` counter-clockwise about pivot (art px of the unpadded
    art) as one rigid piece, raised `lift` rows, cut back to the art's rows
    plus `keep` under them (so a hand turned low is not cut, just hidden). The hand never
    deforms and the sleeve stays a straight tube to the bottom."""
    h, w = art.shape
    wide = np.full((h, w + 2 * pad), TRANSPARENT, np.int32)
    wide[:, pad:pad + w] = art
    long = run_on_down(wide, below)
    return rotsprite(long, deg, (pivot[0] + pad, pivot[1]), out_h=h + keep, lift=lift)


def forearm_pivot(art: np.ndarray, depth: float) -> tuple[float, float]:
    """The elbow: on the widest piece leaving the bottom (the sleeve), its
    axis carried on `depth` art rows under the art's last row."""
    a, b, slope = max(bottom_pieces(art), key=lambda p: p[1] - p[0])
    return (a + b + 1) / 2 + slope * depth, art.shape[0] - 0.5 + depth


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


def _hue(rgb) -> float:
    r, g, b = (float(c) for c in rgb)
    hi, lo = max(r, g, b), min(r, g, b)
    if hi == lo:
        return 0.0
    if hi == r:
        return 60.0 * (((g - b) / (hi - lo)) % 6)
    return 60.0 * ((b - r) / (hi - lo) + 2) if hi == g else 60.0 * ((r - g) / (hi - lo) + 4)


def material(rgb, sleeve_rgb) -> str:
    """One palette colour's material by its ramp: near-black is OUTLINE;
    grey or blue-ish is METAL; within SLEEVE_HUE of the sleeve's hue is
    SLEEVE; light and soft is SKIN; any other warm colour is WOOD (its dark
    red grain included). A rule of thumb, not a segmentation."""
    r, g, b = (float(c) for c in rgb)
    hi = max(r, g, b)
    sat = (hi - min(r, g, b)) / hi if hi else 0.0
    if hi < DARK_VALUE:
        return OUTLINE
    if sat < GREY_SAT or b >= r:
        return METAL
    if abs(_hue(rgb) - _hue(sleeve_rgb)) <= SLEEVE_HUE:
        return SLEEVE
    if sat < SKIN_SAT and hi > SKIN_VALUE:
        return SKIN
    return WOOD


def edge_materials(idx: np.ndarray, pal: np.ndarray, sleeve_rgb, probe: int = EDGE_PROBE) -> list[str | None]:
    """Per row, the material the art carries out through its right side:
    the majority over the last `probe` columns' opaque pixels of that row,
    None where the edge column itself is empty."""
    out: list[str | None] = []
    for row in idx[:, -probe:]:
        if row[-1] < 0:
            out.append(None)
            continue
        kinds = [material(pal[i], sleeve_rgb) for i in row if i >= 0]
        out.append(max(set(kinds), key=lambda m: (kinds.count(m), m == kinds[-1])))
    return out


def _runs(rows: list[int], gap: int = 2) -> list[tuple[int, int]]:
    """Sorted row numbers grouped into (first, last) runs, gaps <= `gap` closed."""
    runs: list[list[int]] = []
    for r in rows:
        if runs and r - runs[-1][1] <= gap + 1:
            runs[-1][1] = r
        else:
            runs.append([r, r])
    return [(a, b) for a, b in runs]


def stock_axis(idx: np.ndarray, pal: np.ndarray, sleeve_rgb, run: tuple[int, int],
               probe: int = STOCK_PROBE, mats: tuple[str, ...] = (WOOD,)) -> float:
    """Rows per column the stock's centre line falls over the last `probe`
    columns (least squares on the wood pixels near the run); 0 if unknown.
    With `mats` (SLEEVE, SKIN) it is the forearm's axis instead."""
    a, b = run
    h, w = idx.shape
    xs, ys = [], []
    for c in range(max(0, w - probe), w):
        rows = [r for r in range(max(0, a - 4), min(h, b + 5))
                if idx[r, c] >= 0 and material(pal[idx[r, c]], sleeve_rgb) in mats]
        if rows:
            xs.append(c)
            ys.append((rows[0] + rows[-1]) / 2)
    return float(np.polyfit(xs, ys, 1)[0]) if len(xs) >= 2 else 0.0


def wood_ramp(base, pal: np.ndarray) -> list[int]:
    """(outline, light, mid, shadow, grain) for a stock of colour `base`."""
    base = np.asarray(base, float)
    return [nearest_colour(base * f, pal) for f in SLEEVE_SHADES + (WOOD_GRAIN,)]


def extend_edges(idx: np.ndarray, right: int, bottom: int, tile: int = EDGE_TILE,
                 power: float = EXIT_POWER, pal: np.ndarray | None = None, band: bool = False,
                 curve: bool = True) -> np.ndarray:
    """The last row smeared `bottom` rows down; then, if the art touches its
    right side, `right` columns more, built per material (edge_materials)
    so the stock and the sleeve stay separate (the CEO, 2026-10-20: the
    tube had turned the stock into sleeve):
    - SLEEVE and SKIN rows: plain sleeve (sleeve_ramp), a tube from the top
      of those rows down, a 1-px dark seam where it takes over (the cuff
      for skin), shaded outline-light-mid-shadow from its top edge. Column
      k's top drops round(D * (k/right)**power) rows plus SLEEVE_TAPER *
      k/right, D its height down to the canvas bottom, so it curves down
      and has left by the last column (always empty).
    - WOOD rows: a stock. It runs on as a straight bar in its own wood ramp
      (wood_ramp), as thick as it leaves, along its own axis (stock_axis),
      no steeper than needed to leave the canvas bottom by STOCK_EXIT of
      the run-on (it heads for the shoulder, under the status bar). It is
      in front: the sleeve never shows above it and its dark bottom outline
      parts the two.
    - Anything else at the edge (metal, outline) ends in a 1-px dark cap.
    With `band`, the sleeve is a tube only as thick as the first run of soft
    rows it leaves (a dark outline under it) instead of filling everything below:
    an arm leaving through the side at mid-height (the ice axe's strike)
    would otherwise turn into a wedge in 16:9.
    With `band` and not `curve`, that tube does not bend down: it runs on
    straight along the forearm's own axis (stock_axis over its soft rows),
    as thick as it leaves, until the canvas's side or bottom (the CEO, D84:
    the ice axe's strike arm came out curved).
    No column of the art is repeated: mirroring the edge repeated skin and
    stock wood."""
    h, w = idx.shape
    hb = h + bottom
    out = np.full((hb, w + right), TRANSPARENT, np.int32)
    out[:h, :w] = idx
    out[h:, :w] = idx[h - 1:h, :]
    if right <= 0 or not (idx[:, w - 1] >= 0).any():
        return out
    pal = palette_rgb() if pal is None else pal
    tile = max(1, min(tile, w))
    s_ramp = sleeve_ramp(out[:, :w], pal, tile)
    sleeve_rgb = pal[s_ramp[2]]
    kinds = edge_materials(out[:, :w], pal, sleeve_rgb)
    cut = [r for r, m in enumerate(kinds) if m is not None]
    # the stocks: (top row at the edge, thickness, slope, ramp)
    stocks = []
    for a, b in _runs([r for r, m in enumerate(kinds) if m == WOOD]):
        while b + 1 < hb and kinds[b + 1] == OUTLINE:   # its own bottom outline
            b += 1
        need = (hb - a) / (STOCK_EXIT * right)
        slope = max(stock_axis(out[:, :w], pal, sleeve_rgb, (a, b)), need)
        wood = [out[r, w - 1] for r in range(a, b + 1) if kinds[r] == WOOD and out[r, w - 1] >= 0]
        stocks.append((a, b - a + 1, slope, wood_ramp(pal[_mode(np.array(wood), None)], pal)))
    soft = [r for r, m in enumerate(kinds) if m in (SLEEVE, SKIN)]
    for r in cut:                                        # the cap: closes whatever is not run on
        out[r, w] = s_ramp[0]
    if soft:
        top0 = soft[0]
        drop_total = hb - top0
        edges = np.cumsum(SLEEVE_BANDS)
        straight = band and not curve
        if straight:
            arm_slope = stock_axis(out[:, :w], pal, sleeve_rgb, _runs(soft)[0], mats=(SLEEVE, SKIN))
        for k in range(1, right + 1):
            f = k / right
            if straight:
                t = min(hb, max(0, top0 + int(round(arm_slope * k))))
            else:
                t = min(hb, top0 + int(round(drop_total * f ** power + SLEEVE_TAPER * f)))
            for a, _, slope, _ in stocks:                # behind the stock: never above it
                if a <= top0:
                    t = max(t, min(hb, a + int(round(slope * k))))
            s = np.arange(hb - t)
            col = np.select([s < edges[0], s < edges[1], s < edges[2]], s_ramp[:3], s_ramp[3])
            if band:
                first, last = _runs(soft)[0]
                thick = last - first + 1
                col = col[:thick].copy()
                col[-1:] = s_ramp[0]
                out[t:t + thick, w - 1 + k] = s_ramp[0] if k == 1 else col[:max(0, min(thick, hb - t))]
            else:
                out[t:, w - 1 + k] = s_ramp[0] if k == 1 else col
    n_out, n_light, mid_frac = WOOD_BANDS
    period, dash = GRAIN_DASH
    for a, thick, slope, (outline, light, mid, shadow, grain) in stocks:
        s = np.arange(thick)
        col = np.select([s < n_out, s < n_out + n_light, s < round(thick * mid_frac), s < thick - 1],
                        [outline, light, mid, shadow], outline)
        for k in range(1, right + 1):
            t = a + int(round(slope * k))
            if t >= hb:
                break
            c = col.copy()
            if (k - 1) % period < dash and thick > n_out + n_light + 3:
                c[thick // 2] = grain
            n = min(thick, hb - t)
            out[t:t + n, w - 1 + k] = c[:n]
    return out


def arm_exits(idx: np.ndarray, length: int = ARM_EXIT, bottom: int = BOTTOM_PAD,
              band: bool = False, curve: bool = True) -> tuple[np.ndarray, int]:
    """extend_edges on both sides: (canvas, columns added on the left). An
    arm cut by the left side of the image runs on leftwards the same way."""
    out = extend_edges(idx, length, bottom, band=band, curve=curve)
    if not (idx[:, 0] >= 0).any():
        return out, 0
    flipped = extend_edges(out[:, ::-1], length, 0, band=band, curve=curve)
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
    names = tuple(n for n in names if n)   # a weapon with no flash sprite names ""
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
    """Every lump of w.frame_list() into out_dir (default hand_G/<name>/).
    One scale for all of them: A's top row `target` px above the bar."""
    pal = palette_rgb()
    out_dir = out_dir or OUT_ROOT / w.name
    check_prefixes(w.gun, w.flash, own=w.folder or w.name)
    arts, periods = {}, {}
    for key, fname in w.files().items():
        art, periods[key] = load_art(REF_DIR / fname, pal)
        for k, x, y in w.drop:
            if k == key:
                art = drop_piece(art, x, y)
        arts[key] = fill_bottom(art)
    hh, ww = min(v.shape[0] for v in arts.values()), min(v.shape[1] for v in arts.values())
    arts = {k: v[:hh, :ww] for k, v in arts.items()}
    a = arts["A"]
    for k, bx0, by0, bx1, by1 in w.restore:
        dx, dy = estimate_recoil(a, arts[k])
        arts[k] = arts[k].copy()
        arts[k][by0:by1, bx0:bx1] = shift(a, dx, dy)[by0:by1, bx0:bx1]
    # the images whose flash is cut out: (art without it, the flash, recoil from A)
    split = {f.src: split_flash(a, arts[f.src], pal, w.flash_grow, w.flash_halo) for f in w.frame_list() if f.flash}
    recoils = {k: v[2] for k, v in split.items()}
    for f in w.frame_list():
        if f.pose == "A" and f.src not in recoils:
            recoils[f.src] = estimate_recoil(a, arts[f.src])
    # scale: A's top row TARGET px above the bar, BELOW_BAR px of arm under it
    target = round(chgg_height() * w.height_mult)
    top = int(np.flatnonzero((a >= 0).any(axis=1))[0])
    sy = (target + BELOW_BAR) / (hh - top)
    sx = sy * PIXEL_ASPECT
    nw, nh = round(ww * sx), round(hh * sy)
    y0 = VIEW_H - target - round(top * sy)       # screen row of the canvas top
    x0 = SCREEN_W - nw + w.x_shift               # the canvas's right edge on the screen's (+ x_shift)
    frames = {}
    for f in w.frame_list():
        if f.flash:
            clean, flash, _ = split[f.src]
            art = shrink_flash(flash, clean, f.scale, pal)
        else:
            art = split[f.src][0] if f.src in split else arts[f.src]
        if f.pose == "A" and f.src != "A":
            dx, dy = recoils[f.src]
            art = shift(art, -dx, -dy)
        if f.flash and w.taper:
            art = taper_cut(art)
        pad = 0
        if f.rot:                                # a swing frame: the art turned about the elbow
            pad = round(ww * SWING_PAD)
            depth = (VIEW_H + PIVOT_BELOW - (y0 + nh)) / sy
            art = swing(art, f.rot, forearm_pivot(art, depth), pad, round(2 * depth + f.lift / sy) + RUN_ON_FIT,
                        lift=f.lift / sy, keep=round(depth))
        small = mode_resize(art, nw + 2 * round(pad * sx), round(art.shape[0] * sy) if f.rot else nh, pal)
        left = round(pad * sx)
        if not f.flash:
            small, added = arm_exits(small, band=w.arm_band, curve=w.arm_curve)
            left += added
        cx, cy = x0 - left + f.kick[0], y0 + f.kick[1]   # the canvas's top-left on the screen
        canvas_grab = (-cx, WEAPONTOP - BAR_LIFT - cy)
        cuts = visible_cuts(small, canvas_grab, True) + visible_cuts(small, canvas_grab, False)
        sub, grab = crop_with_grab(small, cx, cy)
        rgba = to_rgba(sub, pal)
        frames[f.lump] = {"rgba": rgba, "grab": grab, "cuts": cuts,
                          "path": save_sprite(rgba, grab, out_dir / f"{f.lump}.png")}
    first_b = next((k for k in w.files() if k != "A"), "A")
    return {"frames": frames, "period": tuple(periods.values()), "recoil": recoils.get(first_b, (0, 0)),
            "recoils": recoils, "kick": KICK, "target": target,
            "scale": (round(sx, 3), round(sy, 3)), "out_dir": out_dir}


# -------------------------------------------------------------- preview
def wide_backdrop() -> np.ndarray:
    """MAP01 at 16:9 in screen units: (200, 320 + 2 * WIDE_MARGIN) RGB. The
    filed shot (hand_study.MAP01_SHOT, its pistol painted out as in
    map01_backdrop) is narrower than 16:9: its sides are mirrored out."""
    import hand_study as hs
    shot = np.array(Image.open(hs.MAP01_SHOT).convert("RGB"))
    bar_top = hs.SHOT_BAR_TOP
    gx0, gx1, gy0 = hs.SHOT_PISTOL_BOX
    shot[gy0:bar_top, gx0:gx1] = shot[gy0:bar_top, gx0 - 100:gx1 - 100]
    view_w = round(bar_top * SCREEN_W / VIEW_H / PIXEL_ASPECT)       # the shot's px per 320 units
    units = round(shot.shape[1] * SCREEN_W / view_w)
    wide = SCREEN_W + 2 * WIDE_MARGIN
    view = np.array(Image.fromarray(shot[:bar_top]).resize((units, VIEW_H), Image.Resampling.BOX))
    bar = np.array(Image.fromarray(shot[bar_top:]).resize((units, SCREEN_H - VIEW_H), Image.Resampling.BOX))
    img = np.concatenate([view, bar], axis=0)
    pad = (wide - units) // 2
    return np.pad(img, ((0, 0), (pad, wide - units - pad), (0, 0)), mode="reflect")


def wide_mock(layers: list[tuple[np.ndarray, tuple[int, int]]], zoom: int = 2) -> Image.Image:
    """The sprites (rgba, grAb) over wide_backdrop() with the bar on, as a
    `zoom`x image at the 16:9 shape the player sees (pixels 1.2 tall); the
    4:3 screen's edges are ticked at the top."""
    import hand_study as hs
    bg = wide_backdrop()
    out = bg.copy()
    for rgba, grab in layers:
        x, y = hs.place(rgba, grab)
        out = hs.composite(out, rgba, (x + WIDE_MARGIN, y))
    out[VIEW_H:] = bg[VIEW_H:]
    for x in (WIDE_MARGIN, WIDE_MARGIN + SCREEN_W - 1):
        out[:4, x] = (255, 255, 0)
    w = out.shape[1] * zoom
    return Image.fromarray(out).resize((w, round(SCREEN_H * PIXEL_ASPECT * zoom)), Image.Resampling.NEAREST)


def preview(w: WeaponPair, res: dict, stamp: str) -> Path:
    """One sheet: every lump 3x with its size and grAb, then each mock of
    w.mock_list() at 2x 16:9, the TT-33 last for scale. Local only (D77)."""
    import hand_study as hs
    frames = res["frames"]
    pad, lab, z = 16, 26, 3
    zooms = [(k, Image.fromarray(v["rgba"]).resize((v["rgba"].shape[1] * z, v["rgba"].shape[0] * z),
                                                    Image.Resampling.NEAREST)) for k, v in frames.items()]
    tt, tt_grab = hs.read_png_sprite(TT33_READY)
    mocks = [(name, wide_mock([(frames[k]["rgba"], frames[k]["grab"]) for k in lumps]), frames[lumps[0]])
             for name, lumps in w.mock_list()]
    mocks.append(("TT-33 SDTTA0 for scale", wide_mock([(tt, tt_grab)]), {"rgba": tt, "grab": tt_grab}))
    mw, mh = mocks[0][1].size
    per_row = 2
    zrows: list[list] = [[]]
    for k, im in zooms:                          # zoomed lumps, wrapped at the sheet width
        if zrows[-1] and sum(i.width + pad for _, i in zrows[-1]) + im.width > per_row * (mw + pad):
            zrows.append([])
        zrows[-1].append((k, im))
    W = max(per_row * (mw + pad) + pad, max(sum(i.width + pad for _, i in r) + pad for r in zrows))
    zh = sum(max(i.height for _, i in r) + lab + pad for r in zrows)
    n_mrows = -(-len(mocks) // per_row)
    H = 40 + zh + n_mrows * (mh + lab + pad)
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    f = hs.font(16)
    periods = "/".join(f"{p:.2f}" for p in res["period"])
    title = (f"{w.name} from Gemini {'/'.join(w.files())} (D79) - art pixel {periods} src px, recoil "
             f"{res['recoils']} art px, target {res['target']} px above the bar, scale {res['scale']}")
    d.rectangle((0, 0, W, 30), fill=hs.SHEET_BG + (255,))
    d.text((pad, 6), title, font=f, fill=hs.INK)
    y = 40
    for r in zrows:
        x = pad
        for k, im in r:
            g = frames[k]
            d.rectangle((x, y, x + max(im.width, 330), y + lab - 4), fill=hs.SHEET_BG + (255,))
            d.text((x + 4, y + 2), f"{k} {im.width // z}x{im.height // z} grAb {g['grab'][0]},{g['grab'][1]}"
                   f" cuts {g['cuts']}", font=f, fill=hs.INK)
            sheet.alpha_composite(im, (x, y + lab))
            x += max(im.width, 330) + pad
        y += max(i.height for _, i in r) + lab + pad
    for i, (name, img, g) in enumerate(mocks):
        mx, my = pad + (i % per_row) * (mw + pad), y + (i // per_row) * (mh + lab + pad)
        m = hs.measure(g["rgba"], g["grab"])
        d.rectangle((mx, my, mx + mw, my + lab - 4), fill=hs.SHEET_BG + (255,))
        d.text((mx + 4, my + 2), f"{name}: {m['height']} px above the bar, {m['area_pct']} % of the 4:3 view "
               f"(16:9, 2x)", font=f, fill=hs.INK)
        sheet.paste(img, (mx, my + lab))
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
        print(f"{k}: {v['rgba'].shape[1]}x{v['rgba'].shape[0]} grAb {v['grab'][0]},{v['grab'][1]} "
              f"cuts {v['cuts']} -> "
              f"{v['path'].relative_to(ROOT).as_posix()}")
    print(f"art pixel {res['period']}, recoils {res['recoils']}, scale {res['scale']}, target {res['target']}")
    if not args.no_preview:
        print("preview:", preview(w, res, datetime.now().strftime("%Y-%m-%d_%H%M")).relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
