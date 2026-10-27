"""Insignia on the same arm in every rotation (V3, 2026-10-27; the CEO: "algunos enemigos tienen
inconsistencias visuales con los brazaletes: en unas imágenes salen con el brazalete en el lado
derecho, en otras en el izquierdo; unas veces es nazi, otras USA").

    python tools/art/insignia_fix.py audit  [--work DIR]   # the per-lump table, before and after, on stdout
    python tools/art/insignia_fix.py build  [--work DIR]   # the fixed lumps -> <work>/art/insignia_fix/
    python tools/art/insignia_fix.py sheet  [--work DIR]   # docs/art/previews/2026-10-27_V3_insignia-audit.html
    python tools/art/insignia_fix.py all    [--work DIR]   # build, then the sheet

`--work` is the tree whose work/ holds the Gemini sheets and the Fooocus
cache (gitignored, D77): by default this checkout's.

Why. gemini_enemy.py makes rotations 6-8 by mirroring 4-2, and turns every
side view Gemini drew facing right into a left-facing one by mirroring it
too. A mirror moves an arm's insignia to the other arm, and Gemini itself was
not consistent (the General wears the US flag where his armband goes in half
of the views). Doom's own sprites accept a weapon changing hands in the
mirrored rotations; an armband changing arm, or turning into a flag, reads
as a different soldier.

The rule (one per faction, by the character's own arms, every letter and
rotation):
  * the Reich: the armband on the LEFT upper arm (as the historical one);
  * the Legion: the US flag patch on the RIGHT shoulder (as the US Army
    wears it, and as Gemini drew the trooper and the gunner);
  * the General (the alliance's commander, both insignia, BESTIARY): the
    armband on his left arm, the US flag on his right;
  * the Chrome Marshal (D123: the General tinted chrome, a Legion boss):
    the General's set with the armband replaced by the US flag (his own
    sprite SDCM, the General's SDGN untouched);
  * the Consortium: Reich half on its left, Legion half on its right by its
    own build (consortium_gemini.py, rotations 6-8 not mirrored): audited only.
Bodies that are themselves mirrored with the rotation (the stormtrooper's
mechanical right arm, the Liberty Colossus's torch and tablet) keep the
insignia on the same limb of the body as drawn: moving it would put the
armband on the machine arm. They are audited and reported, not repainted;
the exact fix is Gemini's other side (as for the Consortium).

How (at Gemini's resolution, through gemini_enemy.build's `retouch` hook,
after the mirror and BEFORE the D108 symbol, so armband_symbol paints the
symbol on every new field the way it does on the approved ones):
  1. find_marks   - the insignia of a picture: `reich` (a small red band with
                    the white field next to it) and `us` (a flag: saturated
                    blue with red next to it); the General's striped cape,
                    the Panzermensch's back emblem are not marks
  2. arm_of       - the character's arm a mark sits on, from the rotation
                    (Doom: 1 front, 2-4 facing the viewer's left, 5 back,
                    6-8 facing right) and its side of the legs' axis; in a
                    profile the visible arm is the near one
  3. plan         - a mark on the wrong arm is (a) converted in place to the
                    insignia that belongs to that arm (the General: flag <->
                    armband, from a template of the same sheet), or (b)
                    erased and pasted, flipped, at the mirror position about
                    the axis on the right arm: whole when that arm is the
                    near one, its outer sliver when it is the far one, not at
                    all when the body hides it (a profile's far arm)
  4. erase/paste  - the erased pixels are filled from the sleeve round them
                    (diffusion from the edge inward); a paste never leaves
                    the silhouette (the mask, and so every canvas, is the
                    approved one)
Then the pipeline reduces each picture as for the approved set: every lump
whose picture has no repaint comes out byte-identical (the tests check the
hook-off build against assets/).

Output: <work>/art/insignia_fix/<enemy>/ (the whole rebuilt set and its
metrics), <work>/art/insignia_fix/lumps/<folder>/ (only the lumps that
change, plus the Marshal's SDCM), install.sh (copies them into assets/ and
points SD_ChromeGeneral at SDCM; the PM runs it on the CEO's OK). The CEO's
page (before / after, every rotation, the incoherences in red) goes to
docs/art/previews/. Nothing here writes to assets/, src/ or dist/
(gemini_enemy.guard_out).
"""
from __future__ import annotations

import argparse
import base64
import dataclasses
import html
import io
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import gemini_enemy as ge  # noqa: E402

ROOT = artlib.PROJECT_ROOT
SHEET_HTML = ROOT / "docs" / "art" / "previews" / "2026-10-27_V3_insignia-audit.html"
MARSHAL_ACTOR = ROOT / "src" / "zscript" / "monsters" / "chrome_general.zs"
SPRITES_DIR = ROOT / "assets" / "sprites"

# ------------------------------------------------------------------ the rule
LEFT, RIGHT = "L", "R"
REICH, US = "reich", "us"
RULE: dict[str, dict[str, str]] = {   # enemy -> insignia -> the arm(s) it is worn on
    "rifleman": {REICH: LEFT},
    "panzer": {REICH: LEFT},
    "panzer_heavy": {REICH: LEFT},
    "general": {REICH: LEFT, US: RIGHT},
    "legion": {US: RIGHT},
    "gunner": {US: RIGHT},
    "marshal": {US: LEFT + RIGHT},
}
REPLACE = {"marshal": {REICH: US}}     # an insignia a character does not wear: becomes this one in place
AUDIT_ONLY = {   # enemy -> why it is reported and not repainted
    "storm": "the mechanical right arm is mirrored with the body in 6-8: the armband stays on the flesh arm "
             "(moving it would put it on the machine); exact fix: Gemini's other side",
    "colossus": "the whole statue is mirrored in 2-4 (torch and tablet change hands): the flag stays on the "
                "tablet arm in every view, as Gemini drew it in the five; exact fix: Gemini's other side",
    "consortium": "built with rotations 6-8 of its own (consortium_gemini.py): Reich half on its left, "
                  "Legion half on its right in every rotation",
    "doughboy": "the flag decal is on the helmet's front: the same place from every side",
    "hound": "no insignia (BESTIARY: a dog wears no armband)",
}
NOMINAL = {   # the faction's arm, for the audit of the enemies not repainted
    "storm": {REICH: LEFT}, "colossus": {US: LEFT}, "consortium": {REICH: LEFT, US: RIGHT}, "doughboy": {US: LEFT + RIGHT},
}
ARM_NAME = {LEFT: "left", RIGHT: "right"}
KIND_NAME = {REICH: "Reich armband", US: "US flag"}

# Doom's rotations: 1 faces the viewer, 2-4 turn to the viewer's left, 5 the back, 6-8 the viewer's right.
# LEFT_SIGN: the side of the legs' axis (+1 the viewer's right) the character's LEFT arm is on.
LEFT_SIGN = {1: 1, 2: 1, 4: -1, 5: -1, 6: -1, 8: 1}
NEAR_ARM = {2: LEFT, 3: LEFT, 4: LEFT, 6: RIGHT, 7: RIGHT, 8: RIGHT}   # the arm nearer the viewer
PROFILES = (3, 7)
VIEW_ROT = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}          # a picture's view (not mirrored) -> its rotation
VIEW_ROT_MIRROR = {3: 6, 2: 7, 1: 8}               # ... mirrored


NEAR_SLACK = 0.12   # x the figure's width: in a 3/4 view a mark this little past the axis is still the near arm's


# Sheets whose profile shows the FAR arm's band: the rifleman aiming, his support arm reaching forward
# past the body (measured on x3 zooms: the band sits on the forward upper arm in both profiles).
PROFILE_FORWARD = {("rifleman", "aim"), ("rifleman", "fire")}


def arm_of(rot: int, dx: float, width: float = 0.0, forward: bool = False) -> str:
    """The character's arm a mark `dx` px right of the legs' axis is on, in rotation `rot`.
    Front and back: the side. A profile: the near arm (the far one is behind the body).
    A 3/4 view: the near arm unless the mark is clearly on the far side (the near
    arm reaches across the body to hold a rifle forward)."""
    if rot in PROFILES:
        near = NEAR_ARM[rot]
        return (RIGHT if near == LEFT else LEFT) if forward else near
    side = LEFT if (dx > 0) == (LEFT_SIGN[rot] > 0) else RIGHT
    if rot in NEAR_ARM and side != NEAR_ARM[rot] and abs(dx) < NEAR_SLACK * width:
        return NEAR_ARM[rot]
    return side


def visible(rot: int, arm: str) -> bool:
    """A profile shows only its near arm."""
    return rot not in PROFILES or NEAR_ARM[rot] == arm


def is_far(rot: int, arm: str) -> bool:
    """The arm turned away in a 3/4 view: only its outer edge shows."""
    return rot in NEAR_ARM and rot not in PROFILES and NEAR_ARM[rot] != arm


def side_of(rot: int, arm: str) -> int:
    """+1 when `arm` is on the viewer's right of the axis in `rot` (front, back, 3/4)."""
    s = LEFT_SIGN[rot]
    return s if arm == LEFT else -s


# ----------------------------------------------------------------- 1. marks
BLUE_OVER_R, BLUE_OVER_G, BLUE_MIN = 30, 18, 60      # a flag's canton: saturated blue
RED_MIN_LOOSE, RED_RATIO = 70, 1.8                   # the band's and the stripes' red, in shade too
FIELD_WHITE = 120                                    # the band's white field (its darkest channel)
LOOSE_FIELD, LOOSE_SPREAD = 85, 90                   # ... seen edge-on or in shade (armband_symbol's loose white)
NEAR_PX = 3                                          # px: a field / red this close belongs to the mark
MIN_RED_PX, MIN_BLUE_PX = 8, 3
MAX_H_FRAC, MAX_W_FRAC = 0.20, 0.25                  # x the figure: a taller red is a cape stripe, not a band
EMBLEM_DX_FRAC = 0.08                                # x the figure's width: a red this near the axis on a back is the emblem
BAND_PIECES = 2                                      # passes joining the band's broken red pieces
FIRE_MIN = 3                                         # yellow px next to a red: a muzzle flash, not a band
REACH_DX_FRAC = 0.4                                  # x the figure's width: a red further out is a muzzle's flash
VISOR_FRAC = 0.14                                    # x the figure's height: a red this high is a visor (the Panzermensch's band is at ~0.2)
HEAD_FRAC = 0.2                                      # x the figure's height: a blue up here is an eye's glow
STRIPE_R_OVER_G, STRIPE_R_OVER_B, STRIPE_R_MIN = 40, 30, 90   # a stripe's red at a flag's small size (mixed with white)
FLAG_GROW_PASSES = 3                                 # stripe pieces joined outward from the canton
FLAG_REACH = 2.0                                     # x the canton's size: how far the stripes reach from it


@dataclass
class Mark:
    kind: str
    region: np.ndarray          # bool, the picture's shape
    cy: float
    cx: float
    box: tuple[int, int, int, int]   # y0, x0, y1, x1


def blue_mask(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (b > r + BLUE_OVER_R) & (b > g + BLUE_OVER_G) & (b > BLUE_MIN)


def fire_mask(rgb: np.ndarray) -> np.ndarray:
    """A flash's yellow and orange core."""
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 220) & (g > 170) & (b < 170) & (r - b > 70)


def red_loose(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > RED_MIN_LOOSE) & (r > RED_RATIO * g) & (r > RED_RATIO * b)


def _comps(m: np.ndarray, min_px: int) -> list[np.ndarray]:
    lab, n = ge.label(m)
    return [c for c in (lab == i for i in range(1, n + 1)) if c.sum() >= min_px]


def _box(m: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(m)
    return int(ys.min()), int(xs.min()), int(ys.max()) + 1, int(xs.max()) + 1


def _mark(kind: str, region: np.ndarray) -> Mark:
    ys, xs = np.nonzero(region)
    return Mark(kind, region, float(ys.mean()), float(xs.mean()), _box(region))


SHADED_MIN_PX = 60       # a red this big ...
SHADED_ASPECT = 2.5      # ... no longer than this across ...
SHADED_FILL = 0.4        # ... and filling its box this much is a band in shade (a rifle's wood is long and thin)


def _band_shaped(c: np.ndarray) -> bool:
    y0, x0, y1, x1 = _box(c)
    h, w = y1 - y0, x1 - x0
    return int(c.sum()) >= SHADED_MIN_PX and max(h, w) <= SHADED_ASPECT * min(h, w)         and c.sum() >= SHADED_FILL * h * w


def find_marks(rgb: np.ndarray, mask: np.ndarray, back: bool = False) -> list[Mark]:
    """The insignia of a picture (before the symbol): flags first (blue-seeded),
    then Reich armbands (red with a white field) that are not part of a flag.
    `back`: a back view, where a red on the axis is the Panzermensch's emblem."""
    H, W = mask.shape
    fy0, fx0, fy1, fx1 = _box(mask)
    fh, fw = fy1 - fy0, fx1 - fx0
    ax = ge.body_axis(mask)
    red = red_loose(rgb) & mask
    white = ge.white_mask(rgb, FIELD_WHITE) & mask
    a = rgb.astype(np.int32)
    loose = mask & (a.min(axis=-1) > LOOSE_FIELD) & (a.max(axis=-1) - a.min(axis=-1) < LOOSE_SPREAD)
    blue = blue_mask(rgb) & mask
    fire = fire_mask(rgb) & mask
    marks, used = [], np.zeros_like(mask)
    a = rgb.astype(np.int32)
    stripe = mask & (a[..., 0] > a[..., 1] + STRIPE_R_OVER_G) & (a[..., 0] > a[..., 2] + STRIPE_R_OVER_B)         & (a[..., 0] > STRIPE_R_MIN)
    for c in _comps(blue, MIN_BLUE_PX):
        if (ge._dilate(c, NEAR_PX) & (red | stripe)).sum() < MIN_BLUE_PX:
            continue
        if _box(c)[0] < fy0 + HEAD_FRAC * fh:
            continue                                   # the eyes' glow
        y0, x0, y1, x1 = _box(c)
        ry, rx = int(FLAG_REACH * max(2, y1 - y0)), int(FLAG_REACH * max(2, x1 - x0))
        win = np.zeros_like(mask)
        win[max(0, y0 - ry // 2):y1 + ry, max(0, x0 - rx):x1 + rx] = True
        reds = (red | stripe) & win
        lab, _ = ge.label(reds)
        region = c.copy()
        for _ in range(FLAG_GROW_PASSES):        # the stripes next to the canton, and the ones next to those
            touch = ge._dilate(region, NEAR_PX) & reds
            ids = np.unique(lab[touch])
            more = np.isin(lab, ids[ids > 0]) & ~region
            if not more.any():
                break
            region |= more
        by0, bx0, by1, bx1 = _box(region)
        region = np.zeros_like(mask)
        region[by0:by1, bx0:bx1] = True             # the white stripes and stars between them
        region &= mask
        if (region & used).any():
            continue
        used |= region
        marks.append(_mark(US, region))
    for c in _comps(red & ~used, MIN_RED_PX):
        y0, x0, y1, x1 = _box(c)
        if (y1 - y0) > MAX_H_FRAC * fh or (x1 - x0) > MAX_W_FRAC * fh:
            continue                                   # a cape stripe
        near = ge._dilate(c, NEAR_PX)
        if (near & white).sum() < MIN_BLUE_PX and not _band_shaped(c):
            continue                                   # a seam, a glow: no field (a band in shade has a grey one)
        if (near & fire).sum() >= FIRE_MIN:
            continue                                   # a muzzle flash
        m = _mark(REICH, c)
        if y0 < fy0 + VISOR_FRAC * fh:
            continue                                   # a visor's or an eye's red
        if abs(m.cx - ax) > REACH_DX_FRAC * fw:
            continue                                   # out at the muzzle: a flash
        if back and abs(m.cx - ax) < EMBLEM_DX_FRAC * fw:
            continue                                   # the back emblem
        region = (c | (near & white & ge._dilate(c, 2 * NEAR_PX))) & mask
        # the field the band encloses: white inside the band's box
        by0, bx0, by1, bx1 = _box(region)
        inside = np.zeros_like(mask)
        inside[by0:by1, bx0:bx1] = True
        region |= inside & white & mask
        for _ in range(BAND_PIECES):       # the band's red on the field's other side, broken by it
            more = ge._dilate(region, NEAR_PX) & red & ~region
            if not more.any():
                break
            lab2, _ = ge.label(red & ~used)
            for i in np.unique(lab2[more]):
                if i:
                    piece = lab2 == i
                    if piece.sum() <= region.sum() * 2:
                        region |= piece
        if (region & used).any():
            continue
        used |= region
        marks.append(_mark(REICH, region))
    return marks


# The General draws both insignia, on one arm or the other, among medals, a striped cape and its red
# lining: his marks are looked for in a window per view (Gemini drew one on his upper arm in every
# view), measured on x2 zooms of the unmirrored views as fractions of the figure's box (x0, x1, y0, y1);
# the death sheet's by the D105 field boxes (GENERAL_DEATH_FIELDS) grown WINDOW_GROW px.
GENERAL_WINDOWS = {   # (sheet group, view): the standing sheets show his medals, the aiming ones hide them
    ("stand", 0): (0.74, 0.98, 0.25, 0.43),    # front: his left arm on the viewer's right
    ("stand", 1): (0.76, 1.00, 0.25, 0.43),    # 3/4 front (facing left): the near arm
    ("aim", 0): (0.62, 0.95, 0.25, 0.43),
    ("aim", 1): (0.72, 1.00, 0.25, 0.43),
    2: (0.45, 0.78, 0.24, 0.41),               # profile: the near arm
    3: (0.00, 0.22, 0.28, 0.45),               # 3/4 back: the near arm on the viewer's left
    4: (0.00, 0.22, 0.29, 0.45),               # back
}
GENERAL_GROUP = {"turn": "stand", "walkL": "stand", "walkR": "stand", "aim": "aim", "fire": "aim"}
WINDOW_GROW = 12
WINDOW_INSIDE = 0.7       # a colour piece with less of itself inside the window runs past it (a cape stripe)
STRICT_WHITE, STRICT_SPREAD = 165, 45
MAX_MARK_FRAC = 0.10     # x the figure's height: an insignia is never taller or wider (a cape's lining is)
CREAM_BLUE_DROP = 25      # px of blue under red that a clean white may have (the coat's cream has ~40)


def window_box(mask: np.ndarray, win: tuple, mirror: bool) -> tuple[int, int, int, int]:
    """(y0, x0, y1, x1) of a fractional window on the figure's box (mirrored with the picture)."""
    y0, x0, y1, x1 = _box(mask)
    fx0, fx1, fy0, fy1 = win
    if mirror:
        fx0, fx1 = 1.0 - fx1, 1.0 - fx0
    w, h = x1 - x0, y1 - y0
    return (int(y0 + fy0 * h), int(x0 + fx0 * w), int(np.ceil(y0 + fy1 * h)), int(np.ceil(x0 + fx1 * w)))


def insignia_white(rgb: np.ndarray) -> np.ndarray:
    """The field's and the stripes' white: clean, not the cream of a coat (blue well under red)."""
    a = rgb.astype(np.int32)
    lo, hi = a.min(axis=-1), a.max(axis=-1)
    return (lo > STRICT_WHITE) & (hi - lo < STRICT_SPREAD) & (a[..., 2] >= a[..., 0] - CREAM_BLUE_DROP)


def window_marks(rgb: np.ndarray, mask: np.ndarray, box: tuple[int, int, int, int]) -> list[Mark]:
    """The insignia inside a window: the biggest red piece mostly inside it, grown by the
    insignia-coloured pieces (red, flag blue, clean white) that touch it and stay inside;
    its box filled (the field, the stars). A flag when it has blue."""
    blue = blue_mask(rgb) & mask
    red = red_loose(rgb) & mask
    colour = red | blue | (insignia_white(rgb) & mask)
    y0, x0, y1, x1 = box
    win = np.zeros_like(mask)
    win[max(0, y0):y1, max(0, x0):x1] = True
    lab, _ = ge.label(colour)
    inside = {}
    for i in np.unique(lab[win & colour]):
        if i:
            c = lab == i
            if (c & win).sum() >= WINDOW_INSIDE * c.sum():
                inside[int(i)] = c
    flags = [c for c in inside.values() if (c & blue).sum() >= MIN_BLUE_PX]
    reds = [c for c in inside.values() if (c & red).sum() >= MIN_RED_PX]
    if flags:          # a flag: from its canton
        region = max(flags, key=lambda c: int((c & blue).sum())).copy()
    elif reds:
        region = max(reds, key=lambda c: int((c & red).sum())).copy()
    else:
        return []
    fy0, _, fy1, _ = _box(mask)
    cap = MAX_MARK_FRAC * (fy1 - fy0)
    grown = True
    while grown:
        grown = False
        by0, bx0, by1, bx1 = _box(region)
        near = np.zeros_like(mask)
        near[max(0, by0 - NEAR_PX):by1 + NEAR_PX, max(0, bx0 - NEAR_PX):bx1 + NEAR_PX] = True
        for c in inside.values():
            if (c & near).any() and (c & ~region).any():
                cy0, cx0, cy1, cx1 = _box(c | region)
                if cy1 - cy0 <= cap and cx1 - cx0 <= cap:
                    region |= c
                    grown = True
    by0, bx0, by1, bx1 = _box(region)
    region = np.zeros_like(mask)
    region[by0:by1, bx0:bx1] = True
    region &= mask
    kind = US if (blue & region).sum() >= MIN_BLUE_PX else REICH
    return [_mark(kind, region)]


# ---------------------------------------------------------- 4. erase, paste
ERASE_REACH = 4          # px round a mark where its tinted rim is looked for
RIM_TINT, RIM_LIGHT = 25, 110   # a rim pixel: red or blue by this much, or this light
ERASE_GROW = 1           # px round a mark also refilled (its antialiased rim)
FILL_DARK = 45           # luminance under which a pixel is an outline, not used as fill
RIM_PX = 3               # px of the silhouette's edge (outline, halo) never used as fill
SMOOTH_PASSES = 2        # box-filter passes over the filled pixels (the diffusion's streaks)
SLIVER = 0.45            # the outer fraction of a mark pasted on a far arm
LUM = np.array([0.299, 0.587, 0.114])
NEIGH = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)


def erase(rgb: np.ndarray, mask: np.ndarray, region: np.ndarray) -> np.ndarray:
    """The region (grown ERASE_GROW px, inside the silhouette) refilled from the
    figure round it, ring by ring from its edge inward, then smoothed."""
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    tinted = ((r > g + RIM_TINT) & (r > b + RIM_TINT)) | ((b > r + RIM_TINT) & (b > g)) | (a.min(axis=-1) > RIM_LIGHT)
    E = (region | (ge._dilate(region, ERASE_REACH) & tinted)) & mask     # the band's rim: darker red, pink, light
    E = ge._dilate(E, ERASE_GROW) & mask
    if not E.any():
        return rgb
    y0, x0, y1, x1 = _box(E)
    pad = 2 + ERASE_GROW
    y0, x0, y1, x1 = max(0, y0 - pad), max(0, x0 - pad), min(rgb.shape[0], y1 + pad), min(rgb.shape[1], x1 + pad)
    sub = rgb[y0:y1, x0:x1].astype(np.float64)
    m, e = mask[y0:y1, x0:x1], E[y0:y1, x0:x1]
    inner = mask & ~ge.neighbours8(~mask)
    for _ in range(RIM_PX - 1):
        inner &= ~ge.neighbours8(~inner)
    lit = (sub @ LUM) > FILL_DARK                          # an inner outline is no sleeve either
    known, todo = inner[y0:y1, x0:x1] & ~e & lit, e.copy()   # the dark rim and its halo are no sleeve
    while todo.any():
        acc = np.zeros_like(sub)
        cnt = np.zeros(m.shape)
        for dy, dx in NEIGH:
            k = ge.shifted(known, dy, dx, False)
            acc += ge.shifted(sub, dy, dx, 0.0) * k[..., None]
            cnt += k
        front = todo & (cnt > 0)
        if not front.any():          # an island with no figure round it: leave it
            break
        sub[front] = acc[front] / cnt[front][:, None]
        known |= front
        todo &= ~front
    for _ in range(SMOOTH_PASSES):
        acc = sub * m[..., None]
        cnt = m.astype(np.float64)
        for dy, dx in NEIGH:
            acc += ge.shifted(sub * m[..., None], dy, dx, 0.0)
            cnt += ge.shifted(m.astype(np.float64), dy, dx, 0.0)
        sm = acc / np.maximum(cnt, 1)[..., None]
        sub[e] = sm[e]
    out = rgb.copy()
    out[y0:y1, x0:x1][e] = np.clip(np.round(sub[e]), 0, 255).astype(np.uint8)
    return out


@dataclass
class Patch:
    rgb: np.ndarray
    mask: np.ndarray

    def flipped(self) -> "Patch":
        return Patch(self.rgb[:, ::-1].copy(), self.mask[:, ::-1].copy())

    def scaled(self, k: float) -> "Patch":
        if abs(k - 1.0) < 1e-6:
            return self
        h, w = self.mask.shape
        nh, nw = max(1, round(h * k)), max(1, round(w * k))
        rgb = np.asarray(Image.fromarray(self.rgb).resize((nw, nh), Image.LANCZOS))
        m = np.asarray(Image.fromarray(self.mask.astype(np.uint8) * 255).resize((nw, nh), Image.LANCZOS)) >= 128
        return Patch(rgb.copy(), m)


def patch_of(rgb: np.ndarray, mark: Mark) -> Patch:
    y0, x0, y1, x1 = mark.box
    return Patch(rgb[y0:y1, x0:x1].copy(), mark.region[y0:y1, x0:x1].copy())


def sliver(p: Patch, outer: int, band: bool = True) -> Patch:
    """The outer SLIVER of a patch (outer +1: its right columns), white made band red:
    a band on the far arm shows its edge, not its field."""
    h, w = p.mask.shape
    keep = max(1, round(w * SLIVER))
    m = p.mask.copy()
    if outer > 0:
        m[:, :w - keep] = False
    else:
        m[:, keep:] = False
    rgb = p.rgb.copy()
    red = red_loose(rgb) & p.mask
    white = ge.white_mask(rgb, FIELD_WHITE) & m
    if band and red.any() and white.any():
        lum = rgb.astype(np.float64) @ LUM
        base = np.median(rgb[red].astype(np.float64), axis=0)
        k = lum[white] / max(1.0, float(np.median(lum[white])))
        rgb[white] = np.clip(base[None, :] * np.clip(k, 0.6, 1.2)[:, None], 0, 255).astype(np.uint8)
    return Patch(rgb, m)


def paste(rgb: np.ndarray, mask: np.ndarray, p: Patch, cy: float, cx: float) -> tuple[np.ndarray, np.ndarray]:
    """The patch centred on (cy, cx), only over the figure. Returns (picture, pasted pixels)."""
    h, w = p.mask.shape
    y0, x0 = int(round(cy - h / 2)), int(round(cx - w / 2))
    H, W = mask.shape
    out = rgb.copy()
    done = np.zeros_like(mask)
    sy0, sx0 = max(0, -y0), max(0, -x0)
    ty0, tx0 = max(0, y0), max(0, x0)
    ty1, tx1 = min(H, y0 + h), min(W, x0 + w)
    if ty1 <= ty0 or tx1 <= tx0:
        return out, done
    pm = p.mask[sy0:sy0 + ty1 - ty0, sx0:sx0 + tx1 - tx0]
    sel = pm & mask[ty0:ty1, tx0:tx1]
    out[ty0:ty1, tx0:tx1][sel] = p.rgb[sy0:sy0 + ty1 - ty0, sx0:sx0 + tx1 - tx0][sel]
    done[ty0:ty1, tx0:tx1] = sel
    return out, done


# ----------------------------------------------------------------- 3. plan
@dataclass
class Op:
    what: str                   # erase | convert | move | add
    kind: str                   # the insignia painted (convert/move/add) or erased
    mark: int = -1              # index in the picture's marks
    at: tuple = ()              # (cy, cx) where it is painted
    far: bool = False
    note: str = ""


@dataclass
class Fix:
    """A picture's verdict and repaint."""
    rot: int
    marks: list                 # (kind, arm, ok) per mark, before
    ops: list = field(default_factory=list)


def judge(enemy: str, rot: int, marks: list[Mark], ax: float, width: float = 0.0,
          forward: bool = False) -> list[tuple[str, str, bool]]:
    """(kind, arm, ok) per mark; rotation 0 (a death frame) has no arm to judge: only the kind.
    An audited-only enemy is judged against its faction's nominal arm (NOMINAL)."""
    rule = RULE.get(enemy) or NOMINAL.get(enemy, {})
    out = []
    for m in marks:
        if rot == 0:
            out.append((m.kind, "?", m.kind in rule))
            continue
        arm = arm_of(rot, m.cx - ax, width, forward)
        out.append((m.kind, arm, arm in rule.get(m.kind, "")))
    return out


def plan(enemy: str, rot: int, marks: list[Mark], ax: float, manual: dict | None = None,
         width: float = 0.0, forward: bool = False) -> Fix:
    """What to repaint in one picture (rotation `rot`) so every mark is on its arm."""
    rule = RULE[enemy]
    manual = manual or {}
    fix = Fix(rot, judge(enemy, rot, marks, ax, width, forward))
    for i, (m, (kind, arm, ok)) in enumerate(zip(marks, fix.marks)):
        if ok or i in manual.get("keep", ()):
            continue
        repl = REPLACE.get(enemy, {}).get(kind)
        other = repl or next((k for k, arms in rule.items() if k != kind and arm in arms), None)
        if other is not None:
            fix.ops.append(Op("convert", other, i, (m.cy, m.cx), note=f"{KIND_NAME[kind]} -> {KIND_NAME[other]}"))
            continue
        fix.ops.append(Op("erase", kind, i, note=f"{KIND_NAME[kind]} off the {ARM_NAME[arm]} arm"))
        want = rule.get(kind, "")
        if not want or i in manual.get("no_move", ()):
            continue
        target = want[0]
        if not visible(rot, target):
            continue                     # the profile's far arm: hidden by the body
        if any(k == kind and a == target and good for k, a, good in fix.marks):
            continue                     # that arm already wears one (Gemini drew a band on each arm)
        dy, dx = manual.get("shift", {}).get(i, (0, 0))
        tx = 2 * ax - m.cx + dx
        fix.ops.append(Op("move", kind, i, (m.cy + dy, tx), far=is_far(rot, target),
                          note=f"to the {ARM_NAME[target]} arm" + (" (far: its edge)" if is_far(rot, target) else "")))
    for kind, cy, cx in manual.get("add", ()):
        fix.ops.append(Op("add", kind, -1, (cy, cx), note=f"{KIND_NAME[kind]} added (Gemini drew none)"))
    return fix


def apply(rgb: np.ndarray, mask: np.ndarray, marks: list[Mark], fix: Fix, templates: dict, ax: float) -> np.ndarray:
    """The repaint: erases first (every mark that goes), then the pastes."""
    out = rgb
    for op in fix.ops:
        if op.what in ("erase", "convert"):
            out = erase(out, mask, marks[op.mark].region)
    for op in fix.ops:
        if op.what == "move":
            p = patch_of(rgb, marks[op.mark]).flipped()
            if not op.far and op.kind in templates:
                p = templates[op.kind]
            if op.far:
                p = sliver(p, 1 if op.at[1] > ax else -1, band=op.kind == REICH)
            out, _ = paste(out, mask, p, *op.at)
        elif op.what in ("convert", "add"):
            t = templates.get(op.kind)
            if t is None:
                raise ValueError(f"no {op.kind} template for this sheet")
            out, _ = paste(out, mask, t, *op.at)
    return out


# ------------------------------------------------------------- the enemies
MANUAL: dict[tuple, dict] = {}   # (enemy, sheet, view, mirror) -> {keep, no_move, shift, add}: set after the review

MARSHAL_SPRITE, MARSHAL_FOLDER = "SDCM", "chrome_marshal"


def spec_of(enemy: str) -> ge.EnemySpec:
    if enemy == "marshal":
        return dataclasses.replace(ge.GENERAL, name="marshal", sprite=MARSHAL_SPRITE, folder=MARSHAL_FOLDER)
    return ge.ENEMIES.get(enemy) or ge.PENDING[enemy]


def rotations(spec: ge.EnemySpec) -> dict[tuple, int]:
    """(sheet, view, mirror, core) -> the rotation its picture is drawn in (0: a death frame)."""
    out: dict[tuple, int] = {}
    for lump, src in ge.lump_sources(spec).items():
        key = src[:4]
        r = int(lump[len(spec.sprite) + 1]) if lump[len(spec.sprite) + 1].isdigit() else 0
        out[key] = max(out.get(key, 0), r)
    return out


def picture(cut, mirror: bool, core: bool) -> tuple[np.ndarray, np.ndarray]:
    """source_picture's picture before the retouch and the symbol."""
    rgb, mask = cut.rgb, cut.mask
    if core:
        rgb, mask = ge.crop(rgb, ge.largest(mask))
    if mirror:
        rgb, mask = rgb[:, ::-1], mask[:, ::-1]
    return np.ascontiguousarray(rgb), np.ascontiguousarray(mask)


WINDOWED = ("general", "marshal")
MANUAL_WINDOWS: dict[tuple, tuple] = {   # (enemy, sheet, view, mirror) -> (x0, x1, y0, y1) of the picture's box:
    # marks the colours miss (a flag seen edge-on at the silhouette, its stripes pink at that size)
    ("legion", "walkL", 3, True): (0.05, 0.22, 0.25, 0.35),
    ("legion", "walkR", 3, True): (0.05, 0.22, 0.25, 0.35),
}


# The enemies not repainted are judged by how their set is built (the colour finder is not reliable on
# chrome, glows and seams): the rotations whose whole body is a mirror of Gemini's drawing.
MIRRORED_BODY = {"storm": (6, 7, 8), "colossus": (2, 3, 4), "consortium": (), "doughboy": ()}
STRUCTURE_NOTE = {
    "storm": "mirrored body: the band stays on the flesh arm, now his right",
    "colossus": "mirrored statue: torch, tablet and flag change sides together",
}
AUDIT_KINDS = {"storm": (REICH,), "colossus": (US,), "doughboy": (US,), "consortium": (REICH, US), "hound": ()}


def kinds_of(enemy: str) -> tuple[str, ...]:
    """The insignia an enemy can wear (a red-and-white flag stripe on a Legion soldier is no armband)."""
    if enemy in RULE:
        return tuple(RULE[enemy]) + tuple(REPLACE.get(enemy, {}))
    return AUDIT_KINDS.get(enemy, (REICH, US))


def marks_of(enemy: str, key: tuple, rgb: np.ndarray, mask: np.ndarray, rot: int) -> list[Mark]:
    """A picture's marks of the insignia the enemy wears."""
    kinds = kinds_of(enemy)
    return [m for m in _marks_of(enemy, key, rgb, mask, rot) if m.kind in kinds]


def _marks_of(enemy: str, key: tuple, rgb: np.ndarray, mask: np.ndarray, rot: int) -> list[Mark]:
    """By window for the General's set (and where MANUAL_WINDOWS names one), by colour elsewhere."""
    sheet, view, mirror, _core = key
    win = MANUAL_WINDOWS.get((enemy, sheet, view, mirror))
    if win is not None:
        return window_marks(rgb, mask, window_box(mask, win, False))
    if enemy in WINDOWED:
        if sheet == "death":
            box = dict(ge.GENERAL_DEATH_FIELDS).get(view)
            if box is None:
                return []
            x0, y0, x1, y1 = box
            g = WINDOW_GROW
            if mirror:
                W = mask.shape[1]
                x0, x1 = W - x1, W - x0
            return window_marks(rgb, mask, (y0 - g, x0 - g, y1 + g, x1 + g))
        win = GENERAL_WINDOWS.get((GENERAL_GROUP.get(sheet, "stand"), view)) or GENERAL_WINDOWS[view]
        return window_marks(rgb, mask, window_box(mask, win, mirror))
    return find_marks(rgb, mask, back=rot in (4, 5, 6))


TEMPLATE_FROM = {   # the General: where each insignia is drawn on its own arm, in order of preference
    REICH: ((1, False), (3, False), (0, False)),     # the 3/4 front's band (rotation 2), the 3/4 back's, a front's
    US: ((2, True), (0, False), (4, False)),         # the profile's flag (rotation 7), else Gemini's front or back one
}


TEMPLATE_SHEET = "turn"
# The aiming sheets' own band is small and half in shade: pasted on the profile and the back it loses
# its ring, and armband_symbol finds no field (no symbol). Their template is the standing sheet's band.
TEMPLATE_FROM_REF = ("aim", "fire", "death")


BAND_TEMPLATE_VIEW = 2    # a Reich soldier's whole band moved to his near arm: his standing profile's (the clearest field)


def reich_band_templates(cuts: dict, enemy: str) -> dict[str, dict[str, Patch]]:
    """Every sheet -> {reich: the standing profile's band}, to scale: a band moved WHOLE to the near arm
    takes this one (a band in shade, flipped and pasted, loses its field and armband_symbol paints nothing)."""
    if REICH not in RULE.get(enemy, {}) or TEMPLATE_SHEET not in cuts:
        return {}
    rgb, mask = picture(cuts[TEMPLATE_SHEET].figs[BAND_TEMPLATE_VIEW], False, False)
    ms = [m for m in find_marks(rgb, mask) if m.kind == REICH]
    if not ms:
        return {}
    t = patch_of(rgb, max(ms, key=lambda m: m.region.sum()))
    return {k: {REICH: t.scaled(cuts[TEMPLATE_SHEET].scale / cuts[k].scale)} for k in cuts}


def templates(spec: ge.EnemySpec, cuts: dict, enemy: str) -> dict[str, dict[str, Patch]]:
    """sheet -> insignia -> a patch worn right, from that sheet (or turn's, to scale)."""
    if enemy not in ("general", "marshal"):
        return reich_band_templates(cuts, enemy)
    base: dict[str, dict[str, Patch]] = {}
    for key in cuts:
        got = {}
        for kind, sources in TEMPLATE_FROM.items():
            for view, mirror in sources:
                if key == "death" or view >= len(cuts[key].figs):
                    continue
                rgb, mask = picture(cuts[key].figs[view], mirror, False)
                ms = [m for m in marks_of(enemy, (key, view, mirror, False), rgb, mask, 0) if m.kind == kind]
                if ms:
                    got[kind] = patch_of(rgb, max(ms, key=lambda m: m.region.sum()))
                    break
        base[key] = got
    ref = base.get(TEMPLATE_SHEET, {})
    for key in cuts:
        for kind in (REICH, US):
            if kind in ref and (key in TEMPLATE_FROM_REF or kind not in base[key]):
                base[key][kind] = ref[kind].scaled(cuts[TEMPLATE_SHEET].scale / cuts[key].scale)
    return base


@dataclass
class Picture:
    key: tuple
    rot: int
    rgb: np.ndarray
    mask: np.ndarray
    ax: float
    marks: list
    fix: Fix
    after: np.ndarray | None = None
    after_marks: list = field(default_factory=list)
    after_judge: list = field(default_factory=list)


def survey(enemy: str, ref_dir: Path) -> tuple[ge.EnemySpec, dict, dict[tuple, Picture]]:
    """Every picture of an enemy, its marks, its verdict and (if it is ruled) its repaint."""
    spec = spec_of(enemy)
    cuts = ge.plan(spec, ref_dir)
    tpl = templates(spec, cuts, enemy)
    pics = {}
    for key, rot in rotations(spec).items():
        sheet, view, mirror, core = key
        rgb, mask = picture(cuts[sheet].figs[view], mirror, core)
        ax = ge.body_axis(mask)
        y0, x0, y1, x1 = _box(mask)
        width = float(x1 - x0)
        marks = marks_of(enemy, key, rgb, mask, rot)
        forward = (enemy, sheet) in PROFILE_FORWARD
        if enemy in RULE:
            fix = plan(enemy, rot, marks, ax, MANUAL.get((enemy, sheet, view, mirror)), width, forward)
        else:
            fix = Fix(rot, judge(enemy, rot, marks, ax, width, forward))
        pic = Picture(key, rot, rgb, mask, ax, marks, fix)
        if fix.ops:
            pic.after = apply(rgb, mask, marks, fix, tpl.get(sheet, {}), ax)
            pic.after_marks = marks_of(enemy, key, pic.after, mask, rot)
            pic.after_judge = judge(enemy, rot, pic.after_marks, ax, width, forward)
        pics[key] = pic
    return spec, cuts, pics


def retouch_of(pics: dict[tuple, Picture]):
    def retouch(key, rgb, mask):
        p = pics.get(key)
        return rgb if p is None or p.after is None else p.after.copy()
    return retouch


# ------------------------------------------------------------------ build
FIXED = ("rifleman", "panzer", "panzer_heavy", "general", "legion", "gunner", "marshal")
AUDITED = FIXED[:-1] + ("storm", "colossus", "consortium", "doughboy", "hound")
STRIDE_ALIGNED = ("gunner", "colossus")      # A/C re-aligned on B by walk_stride (D127)


def out_root(work: Path) -> Path:
    return work / "art" / "insignia_fix"


def same_pixels(a: Path, b: Path) -> bool:
    if not b.exists():
        return False
    with Image.open(a) as x, Image.open(b) as y:
        xa, ya = np.asarray(x.convert("RGBA")), np.asarray(y.convert("RGBA"))
    return xa.shape == ya.shape and bool((xa == ya).all()) and ge.read_grab(a) == ge.read_grab(b)


def build(enemy: str, work: Path, sprites_dir: Path = SPRITES_DIR) -> dict:
    """The enemy's whole set with the repaint -> <work>/art/insignia_fix/<enemy>/; the lumps that
    differ from assets/ (all of the Marshal's) copied to lumps/<folder>/. Returns the report."""
    ref_dir = work / "art" / "reference" / "enemies" / "gemini"
    cache = work / "art" / "armband_fooocus" / "cache"
    spec, cuts, pics = survey(enemy, ref_dir)
    out = out_root(work) / enemy
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ge.guard_out(out)
    metrics = ge.build(spec, out_dir=out, ref_dir=ref_dir, cache_dir=cache, retouch=retouch_of(pics))
    if enemy in STRIDE_ALIGNED:
        import walk_stride
        walk_stride.align_letters(out, spec.sprite)
    folder = sprites_dir / (ge.GENERAL.folder if enemy == "marshal" else spec.folder)
    lumps_dir = out_root(work) / "lumps" / spec.folder
    lumps_dir.mkdir(parents=True, exist_ok=True)
    changed = []
    for p in sorted(out.glob(f"{spec.sprite}*.png")):
        installed = folder / p.name
        if enemy == "marshal" or not same_pixels(p, installed):
            shutil.copy2(p, lumps_dir / p.name)
            changed.append(p.stem)
    report = {
        "enemy": enemy, "sprite": spec.sprite, "folder": spec.folder, "lumps": metrics["lumps"],
        "changed": changed, "symbol": metrics.get("symbol", {}),
        "pictures": {"/".join(map(str, k)): {"rot": p.rot, "marks": [list(m) for m in p.fix.marks],
                                             "ops": [op.note or op.what for op in p.fix.ops],
                                             "after": [list(m) for m in p.after_judge]}
                     for k, p in pics.items() if p.marks or p.fix.ops},
    }
    (out / "insignia.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


# ------------------------------------------------------------------ the sheet
TITLE = {"rifleman": "Reich rifleman (SDRR)", "panzer": "Panzermensch (SDPM)",
         "panzer_heavy": "Panzermensch Schwer (SDPS)", "general": "The General (SDGN)",
         "legion": "Legion trooper (SDLT)", "gunner": "Legion gunner (SDLG)",
         "marshal": "The Chrome Marshal (new SDCM; today the General's SDGN)", "storm": "Hybrid stormtrooper (SDHS)",
         "colossus": "Liberty Colossus (SDLC)", "consortium": "The Consortium (SDCN)", "doughboy": "Doughboy (SDDB)",
         "hound": "Reich hound (SDHN)"}
SHEET_ORDER = ("general", "marshal", "rifleman", "panzer", "panzer_heavy", "legion", "gunner",
               "storm", "colossus", "consortium", "doughboy", "hound")
THUMB_ZOOM = 2


AUDIT_LETTERS = 3      # an enemy that is not repainted shows its first letters only (the walk and the stand)


def _b64(path: Path) -> str:
    """The lump as an indexed PNG (its colours are the palette's, at most 256): a sheet of ~1000 lumps stays small."""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
    colours = rgba.getcolors(256)
    buf = io.BytesIO()
    if colours is not None:
        pal = [c for _, c in colours]
        index = {c: i for i, c in enumerate(pal)}
        a = np.asarray(rgba).reshape(-1, 4)
        idx = np.array([index[tuple(int(v) for v in px)] for px in a], np.uint8).reshape(rgba.size[1], rgba.size[0])
        p = Image.fromarray(idx, "P")
        p.putpalette([v for c in pal for v in c[:3]] + [0] * (3 * (256 - len(pal))))
        p.info["transparency"] = bytes(c[3] for c in pal)
        p.save(buf, "PNG", optimize=True, transparency=bytes(c[3] for c in pal))
    else:
        rgba.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _label(judged: list) -> str:
    if not judged:
        return "&mdash;"
    return "<br>".join(f"{html.escape(KIND_NAME[k])} &middot; {ARM_NAME.get(a, 'death frame')}" for k, a, _ in judged)


def lump_audit(pics: dict, spec: ge.EnemySpec) -> dict[str, dict]:
    """lump -> {before, ok_before, ops, after, ok_after} for the rotated letters (rotations 1-8)."""
    out = {}
    for lump, src in ge.lump_sources(spec).items():
        rot = lump[len(spec.sprite) + 1:]
        if not rot.isdigit() or rot == "0":
            continue
        p = pics[src[:4]]
        ok_b = all(ok for *_, ok in p.fix.marks)
        ops = [op.note for op in p.fix.ops]
        after = p.after_judge if p.fix.ops else p.fix.marks
        out[lump] = {"before": p.fix.marks, "ok_before": ok_b, "ops": ops, "after": after,
                     "ok_after": ok_b or bool(ops)}
    return out


def _cell(img: Path | None, label: str, cls: str) -> str:
    if img is None or not img.exists():
        return '<td class="none">&mdash;</td>'
    with Image.open(img) as im:
        w, h = im.size
    return (f'<td class="{cls}"><img src="data:image/png;base64,{_b64(img)}" width="{w * THUMB_ZOOM}" '
            f'height="{h * THUMB_ZOOM}" alt=""><div class="lab">{label}</div></td>')


def enemy_section(enemy: str, work: Path, sprites_dir: Path = SPRITES_DIR) -> tuple[str, dict]:
    """One enemy's grid: installed lumps (and the proposed ones under them), every rotation."""
    ref_dir = work / "art" / "reference" / "enemies" / "gemini"
    spec, _cuts, pics = survey(enemy, ref_dir)
    audit = lump_audit(pics, spec)
    fixed = enemy in RULE
    new_dir = out_root(work) / enemy
    old_folder = sprites_dir / (ge.GENERAL.folder if enemy == "marshal" else spec.folder)
    old_sprite = ge.GENERAL.sprite if enemy == "marshal" else spec.sprite
    letters = sorted({lu[len(spec.sprite)] for lu in audit})
    if not fixed:
        letters = letters[:AUDIT_LETTERS]
    if fixed:
        bad_before = sorted(lu for lu, a in audit.items() if not a["ok_before"])
    else:
        bad_before = sorted(lu for lu in audit if int(lu[len(spec.sprite) + 1]) in MIRRORED_BODY.get(enemy, ()))
    changed = sorted(lu for lu, a in audit.items() if a["ops"])
    left = sorted(lu for lu, a in audit.items() if not a["ok_after"]) if fixed else bad_before
    rows = []
    for L in letters:
        cb, ca = [], []
        for r in range(1, 9):
            lu = f"{spec.sprite}{L}{r}"
            a = audit.get(lu)
            if a is None:
                cb.append('<td class="none">&mdash;</td>')
                ca.append('<td class="none"></td>')
                continue
            old = old_folder / f"{old_sprite}{L}{r}.png"
            if fixed:
                cb.append(_cell(old, _label(a["before"]), "ok" if a["ok_before"] else "bad"))
            elif r in MIRRORED_BODY.get(enemy, ()):
                cb.append(_cell(old, html.escape(STRUCTURE_NOTE[enemy]), "warn"))
            else:
                cb.append(_cell(old, "as drawn", "ok"))
            if fixed and (a["ops"] or enemy == "marshal"):
                lab = "<br>".join(html.escape(n) for n in a["ops"]) or _label(a["after"])
                ca.append(_cell(new_dir / f"{lu}.png", lab, "fixed" if a["ops"] else "ok"))
            elif fixed:
                ca.append('<td class="same">unchanged</td>' if a["ok_before"] else '<td class="bad">not fixed</td>')
        rows.append(f'<tr><th>{L}<br><small>installed</small></th>{"".join(cb)}</tr>')
        if fixed:
            rows.append(f'<tr class="after"><th>{L}<br><small>proposed</small></th>{"".join(ca)}</tr>')
    extra = ""
    if enemy == "marshal":
        cells_b, cells_a = [], []
        for L in sorted(ge.GENERAL.single):
            cells_b.append(_cell(old_folder / f"SDGN{L}0.png", f"SDGN{L}0", "warn"))
            cells_a.append(_cell(new_dir / f"{spec.sprite}{L}0.png", f"{spec.sprite}{L}0", "fixed"))
        extra = ('<h4>Death frames (rotation 0): the armband becomes the flag</h4><div class="scroll"><table class="grid">'
                 f'<tr><th>SDGN</th>{"".join(cells_b)}</tr><tr class="after"><th>SDCM</th>{"".join(cells_a)}</tr>'
                 '</table></div>')
    note = AUDIT_ONLY.get(enemy, "")
    rule = RULE.get(enemy) or NOMINAL.get(enemy, {})
    rule_txt = "; ".join(f"{KIND_NAME[k]} on the {' and '.join(ARM_NAME[a] for a in arms)} arm"
                         for k, arms in rule.items())
    if enemy == "marshal":
        summary = (f"The General's armband is on every lump: {len(changed)} of {len(audit)} rotated lumps and the "
                   f"{len(ge.GENERAL.single)} death frames repainted with the US flag, as the new sprite SDCM "
                   "(the General's SDGN is untouched).")
    elif enemy == "hound":
        summary = html.escape(note)
    elif fixed:
        summary = (f"{len(bad_before)} of {len(audit)} rotated lumps wear an insignia on the wrong arm or of the "
                   f"wrong kind; {len(changed)} repainted; {len(left)} left.")
    else:
        summary = (f"{len(bad_before)} of {len(audit)} rotated lumps are a mirror of the whole body. Not repainted: "
                   f"{html.escape(note)}.")
    grid = "" if enemy == "hound" else (
        '<div class="scroll"><table class="grid"><tr><th></th>'
        + "".join(f"<th>{r}</th>" for r in range(1, 9)) + f'</tr>{"".join(rows)}</table></div>')
    html_out = (f'<section id="{enemy}"><h2>{html.escape(TITLE[enemy])}</h2>'
                f'<p class="rule">Rule: {html.escape(rule_txt) or "none"}</p><p class="sum">{summary}</p>'
                f"{grid}{extra}</section>")
    return html_out, {"lumps": len(audit), "bad_before": bad_before, "changed": changed, "left": left}


CSS = """
:root{--bg:#f4f1ea;--fg:#1d1d1b;--muted:#6b665c;--card:#fffdf8;--line:#d9d3c7;--bad:#c62828;
--warn:#b26a00;--fix:#1565c0;--cell:#5a6e5a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#17181a;--fg:#ecebe7;--muted:#a19d94;
--card:#202124;--line:#3a3b3f;--bad:#ef5350;--warn:#ffb74d;--fix:#64b5f6;--cell:#4a5a4a}}
:root[data-theme="dark"]{--bg:#17181a;--fg:#ecebe7;--muted:#a19d94;--card:#202124;--line:#3a3b3f;
--bad:#ef5350;--warn:#ffb74d;--fix:#64b5f6;--cell:#4a5a4a}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px}
main{max-width:1500px;margin:0 auto}h1{font-size:1.5em;margin:.2em 0}h2{margin:.4em 0 .2em}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:16px 0}
.rule{color:var(--muted);margin:.2em 0}.sum{font-weight:600}.scroll{overflow-x:auto}
table.grid{border-collapse:separate;border-spacing:4px}table.grid th{font-weight:600;color:var(--muted);font-size:.85em}
table.grid td{background:var(--cell);border:3px solid transparent;border-radius:4px;text-align:center;
vertical-align:bottom;padding:2px;min-width:40px}
table.grid td img{image-rendering:pixelated;display:block;margin:0 auto}
td .lab{font-size:10px;line-height:1.2;color:#fff;background:rgba(0,0,0,.55);padding:1px 2px;border-radius:2px;
max-width:150px;margin:0 auto}
td.bad{border-color:var(--bad)}td.warn{border-color:var(--warn)}td.fixed{border-color:var(--fix)}
td.same,td.none{background:transparent;color:var(--muted);font-size:.8em}
tr.after th{color:var(--fix)}.legend span{display:inline-block;border:3px solid;border-radius:4px;padding:0 6px;margin:0 8px 4px 0}
table.tot{border-collapse:collapse}table.tot td,table.tot th{border-bottom:1px solid var(--line);padding:4px 10px;text-align:left}
"""

INTRO = """
<h1>Insignia audit: one arm per faction, in every rotation (V3, 2026-10-27)</h1>
<p>The CEO: some enemies (the Colossus, the General and others) wear the armband on the right in some pictures and
on the left in others, and sometimes it is the Nazi one, sometimes the US one. <b>Cause.</b>
<code>gemini_enemy.py</code> makes rotations 6-8 by mirroring 4-2, and turns every side view Gemini drew facing
right into a left-facing one by mirroring it too: a mirror moves an insignia to the other arm. Gemini also drew the
General with the US flag where his armband goes in half of his views (front, profile, back). The «Colossus» with
the Nazi armband is the Chrome Marshal: the General's own sprites tinted chrome (D123).</p>
<h3>The rule (proposed and applied)</h3>
<ul><li><b>Reich</b>: the armband on the <b>left</b> upper arm.</li>
<li><b>Legion</b>: the US flag patch on the <b>right</b> shoulder (as Gemini drew the trooper and the gunner).</li>
<li><b>The General</b> (both insignia, the alliance's commander): the armband on his left arm, the US flag on his right.</li>
<li><b>The Chrome Marshal</b> (a Legion boss): the General's pictures with the armband replaced by the US flag, as
a new sprite <code>SDCM</code>; the General's <code>SDGN</code> stays as it is.</li>
<li><b>The Consortium</b>: Reich half on its left, Legion half on its right (already built so, its own rotations 6-8).</li>
<li>Bodies mirrored with the rotation (the stormtrooper's machine arm, the Colossus's torch and tablet) keep the
insignia on the limb Gemini drew it on: moving it would put an armband on the machine arm or the flag on the torch
arm. Reported in amber, not repainted; the exact fix is a Gemini sheet of their other side (as for the Consortium).</li></ul>
<p class="legend"><span style="border-color:var(--bad)">wrong arm or kind</span><span style="border-color:var(--warn)">
off the faction's arm, body mirrored (not repainted)</span><span style="border-color:var(--fix)">repainted</span></p>
<p>Rotations: 1 front, 2-4 turning to the viewer's left, 5 back, 6-8 turning to the viewer's right. Labels name the
character's own arm. &mdash; = no insignia found (the arm is turned away, or it is only a few pixels).</p>
<h3>How the repaint is made</h3>
<p>At Gemini's resolution, before the reduction and before the D108 symbol (<code>tools/art/insignia_fix.py</code>,
through a hook in <code>gemini_enemy.build</code>): a misplaced insignia is erased (refilled from the sleeve round it)
and pasted, flipped, on the right arm: whole on the near arm, its edge on the far arm of a 3/4 view, not at all where
the body hides it (the far arm of a profile). The General's insignia swap in place (the armband from his 3/4 front,
the flag from his profile). The Reich armbands then get the symbol from <code>armband_symbol.py</code> as the approved
ones did. Every other pixel and every canvas is the approved set's: a lump with no repaint comes out byte-identical
and is not reinstalled. <b>Nothing is installed</b>: the lumps wait in <code>work/art/insignia_fix/lumps/</code>
with <code>install.sh</code>, for the CEO's OK.</p>
"""


def sheet(work: Path, out: Path = SHEET_HTML, sprites_dir: Path = SPRITES_DIR) -> Path:
    sections, totals = [], []
    for enemy in SHEET_ORDER:
        s, st = enemy_section(enemy, work, sprites_dir)
        sections.append(s)
        totals.append((enemy, st))
    tot_rows = "".join(
        f'<tr><td><a href="#{e}">{html.escape(TITLE[e])}</a></td><td>{st["lumps"]}</td>'
        f'<td>{len(st["bad_before"])}</td><td>{len(st["changed"]) if e in RULE else "&mdash;"}</td>'
        f'<td>{len(st["left"])}</td></tr>'
        for e, st in totals if e != "hound")
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Insignia Audit V3</title>'
            f"<style>{CSS}</style></head><body><main>{INTRO}"
            '<h3>Totals</h3><div class="scroll"><table class="tot"><tr><th>enemy</th><th>rotated lumps</th>'
            "<th>incoherent (installed)</th><th>repainted</th><th>left</th></tr>"
            f'{tot_rows}</table></div>{"".join(sections)}</main></body></html>')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    return out


# ------------------------------------------------------------------ install
INSTALL_TAIL = r"""# the Marshal's states: SDGN -> SDCM (his comment block keeps its history)
sed -i -E 's/^(\t+)SDGN /\1SDCM /' src/zscript/monsters/chrome_general.zs
sed -i 's|^// The look: SDGN (assets/sprites/general/), Scale 1.3|// The look: SDCM (assets/sprites/chrome_marshal/: the General'"'"'s set with the US flag for his armband, V3 insignia_fix.py), Scale 1.3|' src/zscript/monsters/chrome_general.zs
sed -i 's/^CHROME_SPRITE = "SDGN"/CHROME_SPRITE = "SDCM"   # V3: his own set (tools\/art\/insignia_fix.py)/' tests/test_ep2_enemies.py
grep -q "SDCM A" src/zscript/monsters/chrome_general.zs
if grep -qE "^[[:space:]]+SDGN " src/zscript/monsters/chrome_general.zs; then echo "SDGN left in the Marshal"; exit 1; fi
echo "installed; now: python tools/verify.py fast"
"""


LICENSES_PART = "licenses_insignia.md"


def licenses_section(reports: list[dict]) -> str:
    """The rows install.sh appends to docs/art/LICENSES.md: the Marshal's new SDCM (check_pk3's
    licence check), and a note on the repainted lumps of the others (same names, same rows)."""
    marshal = next((r for r in reports if r["enemy"] == "marshal"), None)
    others = [r for r in reports if r["enemy"] != "marshal" and r["changed"]]
    out = ["", "", "### The Chrome Marshal's own set (`SDCM`) and the insignia repaint (V3, 2026-10-27)", "",
           "`tools/art/insignia_fix.py` (the CEO's complaint: the armband changing arm between rotations and the "
           "General's US flag and armband swapping places): each faction's insignia on the same arm of the "
           "character in every rotation. The repaint is made at Gemini's resolution through "
           "`gemini_enemy.build`'s `retouch` hook, before the D108 symbol (`tools/art/armband_symbol.py`); every "
           "other pixel is the approved set's. Same names and rows as before for "
           + ", ".join(f"`{r['sprite']}` ({len(r['changed'])} lumps)" for r in others)
           + ". Files copied byte for byte from `work/art/insignia_fix/lumps/`. Preview: "
           "`docs/art/previews/2026-10-27_V3_insignia-audit.html`.", ""]
    if marshal:
        out += ["| Lump | What it is | Origin | Licence |", "|---|---|---|---|"]
        by_letter: dict[str, list[str]] = {}
        for lu in marshal["changed"]:
            by_letter.setdefault(lu[4], []).append(lu)
        for n, (letter, lumps) in enumerate(sorted(by_letter.items())):
            names = ", ".join(f"`{x}`" for x in sorted(lumps))
            if n == 0:
                out.append(f"| {names} | `SD_ChromeGeneral` (D123), frame {letter}: the General's `SDGN` with his "
                           "armband repainted as the US flag (he is a Legion boss); Scale 1.3 and the chrome "
                           "Translation are in the actor | (a) derived from the General's Gemini images as `SDGN` "
                           "(rows above), repainted by `tools/art/insignia_fix.py`; the source images are not "
                           "distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in "
                           "the game's and the release's credits (D79, D109) |")
            else:
                out.append(f"| {names} | idem, frame {letter} | (a) idem | idem |")
    return "\n".join(out) + "\n"


def install_script(work: Path, reports: list[dict]) -> Path:
    """<work>/art/insignia_fix/install.sh: copy the changed lumps into assets/ and point the Marshal at SDCM.
    The PM runs it from the repo root on the CEO's OK."""
    lines = ["#!/usr/bin/env bash",
             "# V3 insignia fix (tools/art/insignia_fix.py): run from the repo root on the CEO's OK.",
             "# Copies the repainted lumps over the installed ones and gives the Chrome Marshal his own SDCM.",
             "set -euo pipefail",
             'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
             'test -f src/zscript/monsters/chrome_general.zs || { echo "run from the repo root"; exit 1; }']
    for r in reports:
        if r["changed"]:
            lines.append(f'mkdir -p assets/sprites/{r["folder"]}')
            lines.append(f'cp "$HERE/lumps/{r["folder"]}/"{r["sprite"]}*.png assets/sprites/{r["folder"]}/   '
                         f'# {r["enemy"]}: {len(r["changed"])} lumps')
    (out_root(work) / LICENSES_PART).write_text(licenses_section(reports), encoding="utf-8", newline="\n")
    lines.append(f'grep -q "SDCMA1" docs/art/LICENSES.md || cat "$HERE/{LICENSES_PART}" >> docs/art/LICENSES.md')
    path = out_root(work) / "install.sh"
    path.write_text("\n".join(lines) + "\n" + INSTALL_TAIL, encoding="utf-8", newline="\n")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Insignia on the same arm in every rotation (V3)")
    ap.add_argument("what", choices=("audit", "build", "sheet", "all"))
    ap.add_argument("--work", type=Path, default=ROOT / "work", help="the tree's work/ (Gemini sheets, Fooocus cache)")
    args = ap.parse_args(argv)
    work = args.work
    if args.what == "audit":
        for enemy in SHEET_ORDER:
            _spec, _c, pics = survey(enemy, work / "art" / "reference" / "enemies" / "gemini")
            for key, p in sorted(pics.items(), key=lambda kv: (kv[0][0], kv[1].rot)):
                if p.fix.ops or not all(ok for *_, ok in p.fix.marks):
                    print(enemy, "/".join(map(str, key[:3])), "rot", p.rot, p.fix.marks, [o.note for o in p.fix.ops])
        return 0
    if args.what in ("build", "all"):
        reports = []
        for enemy in FIXED:
            r = build(enemy, work)
            reports.append(r)
            print(f"[insignia] {enemy}: {len(r['changed'])} of {r['lumps']} lumps changed")
        print(f"[insignia] {install_script(work, reports)}")
    if args.what in ("sheet", "all"):
        print(f"[insignia] {sheet(work)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
