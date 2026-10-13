"""F4 — first-person weapons: the sergeant's hands (D39), the ice axe (D40),
the PPSh-41.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_weapon.py hands      (Windows)
    .venv/bin/python tools/art/gen_weapon.py hands              (macOS)
    ... gen_weapon.py axe  --hand E      the ice axe, frames + pickup
    ... gen_weapon.py ppsh --hand E      the PPSh-41, frames, flash + pickup
    ... --stamp 2026-10-13_1900          fixes the sheet's timestamp

What this is. D39 (CEO, 2026-10-13): the first-person hands are Freedoom's
placeholder ("mismo color de piel y manos"), so we design our own hand: the
sergeant's, gloved or bare, with the cuff of his sleeve, in palette v1.
D40: slot 1 becomes an ice axe (piolet, ледоруб) instead of the sapper's
shovel. Three deliveries, each its own sheet for the CEO's gate:

    hands   a SWEEP of six hand styles (PIPELINE stage 2), each shown in the
            idle grip of the ice axe, plus the hand kit every weapon uses:
            power grip, trigger grip, support hand
    axe     the ice axe in the chosen style: idle, a three-frame swing and a
            recovery frame, and the world pickup (two options)
    ppsh    the PPSh-41: idle, recoil, two flash frames, pickup

How it is drawn. Claude does not draw freehand, and HUD sprites are big
(100-250 px), so the flat shape painter of gen_enemy.py would show its
seams. Instead every pose is a small 3D scene in CAMERA SPACE, in
centimetres: X right, Y down, Z away from the eye. Points are projected
with Doom's own view, a 90-degree field on 320 columns, so the focal length
is 160 px and the weapon space is the 320x200 screen with its centre at
(160, 100): a fist 35 cm from the eye comes out the size a fist should.
Primitives are tapered capsules (fingers, forearms, shafts), ellipsoids
(the back of the hand, the drum) and extruded plates (the ice axe's head);
each computes, per sub-pixel, its depth and its normal, and a z-buffer
keeps the nearest. Light is fixed to the camera (key from the top left, a
little from the front) and cut into LIGHT_BANDS bands, plus a hard
specular band on steel. Every primitive carries a MATERIAL: a slice of one
palette ramp, so every pixel is a palette.json colour by construction.

Reduction to 1x is gen_enemy.py's majority vote per SSxSS block, then two
pixel-art passes: a dark contour where something sits in front of a pixel
(a depth jump, or a different part slightly in front: finger over finger),
and a darker rim on the silhouette, so the hand reads on any wall.

NO FONTS. The sprites carry no text; the sheets' labels are set in the
mod's own small font (D24) through gen_enemy.Text, so the sheets reproduce
byte for byte on the Mac and on Windows. tests/test_gen_weapon.py keeps it.

Sprite names: MOD-SPEC §6.3. The ice axe (`SD_IceAxe`, D40) is SDAX A-E
held and SDAP A pickup (they replace the shovel's SDSH / SDSP); the PPSh-41
is SDPP A-B held, SDPF A-B flash, SDPQ A pickup.

Offsets. A HUD sprite's grAb offsets place it in the 320x200 weapon space:
vanilla draws its left edge at x = -leftoffset (plus one) and its top at
y = 32 - topoffset at rest (WEAPONTOP = 32), so a pose authored in screen
coordinates gives its offsets directly. Freedoom's own HUD sprites obey the
same arithmetic (PUNGA0: 96x46, offsets -96 / -128, top at y = 160). The
weapon bob only moves a sprite down and sideways, and widescreen shows
about 53 px either side of the 320 columns, so the authoring canvas runs
from x = -64 to 384 and down to y = 232 and anything that leaves the screen
keeps going. NOT VERIFIED in GZDoom: the first engine pass (owed, D26)
confirms the position; the classic status bar hides the bottom 32 rows.

Outputs (work/ is gitignored):
    work/art/weapons/hands/      one idle grip per style, the hand kit
    work/art/weapons/ice_axe/    SDAXA0-E0, SDAPA0 (+ options A, B), metrics.json
    work/art/weapons/ppsh/       SDPPA0-B0, SDPFA0-B0, SDPQA0, metrics.json
    docs/art/previews/<stamp>_F4_<slug>.png   the sheet of each delivery
Sprites are RGBA with hard alpha, like the F5 drafts (ART-BIBLE §2
exception); the shipped format is decided with the mod-engineer on
approval.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
from gen_enemy import Material, Text, zoom, luma  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "weapons"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
TEX = PROJECT_ROOT / "assets" / "textures" / "soviet_base"
FLATS = PROJECT_ROOT / "assets" / "flats" / "soviet_base"

# ------------------------------------------------------------------ camera
FOCAL = 160.0                   # px: a 90-degree view on 320 columns
SCREEN_W, SCREEN_H = 320, 200   # Doom's weapon space
SCREEN_CX, SCREEN_CY = 160.0, 100.0
WEAPONTOP = 32                  # vanilla psprite y at rest
CANVAS_X0, CANVAS_Y0 = -64, 0   # authoring canvas, screen px (see docstring)
CANVAS_W, CANVAS_H = 448, 232
STATUSBAR_TOP = 168             # the classic status bar covers y >= 168
SS = 3                          # sub-pixels per pixel side

# ------------------------------------------------------------------- light
LIGHT = np.array([-0.45, -0.72, -0.53])         # towards the light, camera space
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0.0, 0.0, -1.0])       # Blinn half vector, viewer at -Z
HALF = HALF / np.linalg.norm(HALF)
LIGHT_BANDS = 6                 # Lambert cut into this many flat bands
AMBIENT = 0.30                  # a face turned from the key light is not black
LAMBERT_MID = 0.55              # the band that maps to a material's base value
SPEC_POWER = 24
SPEC_CUT = 0.55                 # steel shows a hard highlight above this
SPEC_GAIN = 0.32

# ---------------------------------------------------------- pixel passes
DEPTH_EDGE_CM = 1.6             # a jump this deep gets the full contour
CONTOUR_STEPS = 3               # ramp steps darker, behind a depth jump
CREASE_STEPS = 1                # ramp steps darker, behind another part touching it
RIM_STEPS = 3                   # ramp steps darker on the silhouette
COVER_MIN = 4                   # of SS*SS sub-pixels: below this, transparent


# =============================================================== materials
MATERIALS: dict[str, Material] = {
    # sleeves
    "sleeve_field": Material("military_green", 1, 12, black_floor=True),
    "sleeve_coat": Material("plaster_warm", 0, 9, black_floor=True),
    "sleeve_quilt": Material("military_green", 0, 7, black_floor=True),
    "tel_white": Material("plaster_warm", 7, 15),
    "tel_blue": Material("steel_blue", 0, 4, black_floor=True),
    # hands
    "glove_brown": Material("rust_brown", 0, 8, black_floor=True),
    "glove_black": Material("concrete_cold", 0, 8, black_floor=True),
    "skin": Material("rust_brown", 4, 13, black_floor=True),
    "button": Material("concrete_cold", 4, 20, black_floor=True),
    # weapons
    "wood_ash": Material("cream_yellow", 2, 12, black_floor=True),
    "wood_birch": Material("rust_brown", 3, 12, black_floor=True),
    "steel": Material("steel_blue", 0, 15, black_floor=True),
    "gunmetal": Material("concrete_cold", 0, 16, black_floor=True),
    "dummy": Material("concrete_cold", 2, 14, black_floor=True),
    "flash_out": Material("hazard_yellow", 9, 15),
    "flash_in": Material("cream_yellow", 12, 15),
    "flash_core": Material("cream_yellow", 15, 15),
}
MAT_ID = {name: i for i, name in enumerate(MATERIALS)}
METALS = {"steel", "gunmetal", "button"}
FLAT = {"flash_out", "flash_in", "flash_core"}      # no light, no contour


def unit(v) -> np.ndarray:
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


def perp(v, to) -> np.ndarray:
    """The part of v perpendicular to the unit vector `to`, normalised."""
    v = np.asarray(v, np.float64)
    return unit(v - np.dot(v, to) * to)


# ===================================================================== rig
class Rig:
    """A z-buffered canvas of material ids, values (ramp position 0..1),
    part ids and depths, at SS sub-pixels per pixel."""

    def __init__(self, x0=CANVAS_X0, y0=CANVAS_Y0, w=CANVAS_W, h=CANVAS_H, ss=SS,
                 focal=FOCAL, centre=(SCREEN_CX, SCREEN_CY)):
        self.x0, self.y0, self.w, self.h, self.ss = x0, y0, w, h, ss
        self.focal, self.cx, self.cy = focal, centre[0], centre[1]
        shape = (h * ss, w * ss)
        self.depth = np.full(shape, np.inf)
        self.mat = np.full(shape, -1, np.int16)
        self.val = np.zeros(shape)
        self.part = np.zeros(shape, np.int32)
        self.count = 0

    # --- geometry
    def project(self, p) -> tuple[float, float, float]:
        x, y, z = p
        s = self.focal / z
        return self.cx + x * s, self.cy + y * s, s

    def _window(self, xmin, ymin, xmax, ymax):
        ss = self.ss
        i0 = max(0, int(np.floor((ymin - self.y0) * ss)))
        i1 = min(self.h * ss, int(np.ceil((ymax - self.y0) * ss)) + 1)
        j0 = max(0, int(np.floor((xmin - self.x0) * ss)))
        j1 = min(self.w * ss, int(np.ceil((xmax - self.x0) * ss)) + 1)
        if i0 >= i1 or j0 >= j1:
            return None
        ys = self.y0 + (np.arange(i0, i1) + 0.5) / ss
        xs = self.x0 + (np.arange(j0, j1) + 0.5) / ss
        Y, X = np.meshgrid(ys, xs, indexing="ij")
        return (slice(i0, i1), slice(j0, j1)), X, Y, (self.x0 + j0 / ss, self.y0 + i0 / ss)

    def _poly_mask(self, pts2, X, origin) -> np.ndarray:
        img = Image.new("L", (X.shape[1], X.shape[0]), 0)
        ox, oy = origin
        ImageDraw.Draw(img).polygon([((x - ox) * self.ss, (y - oy) * self.ss) for x, y in pts2], fill=255)
        return np.asarray(img) > 0

    # --- light
    @staticmethod
    def shade(n: np.ndarray, base: float, gain: float, material: str) -> np.ndarray:
        if material in FLAT:
            return np.full(n.shape[:-1], base)
        lam = AMBIENT + (1.0 - AMBIENT) * np.clip(n @ LIGHT, 0.0, 1.0)
        lam = np.floor(lam * LIGHT_BANDS + 0.5) / LIGHT_BANDS
        v = base + gain * (lam - LAMBERT_MID)
        if material in METALS:
            spec = np.clip(n @ HALF, 0.0, 1.0) ** SPEC_POWER
            v = v + SPEC_GAIN * (spec > SPEC_CUT)
        return v

    def _commit(self, sl, inside, depth, val, mat) -> None:
        self.count += 1
        cur = self.depth[sl]
        win = inside & (depth < cur)
        cur[win] = depth[win]
        self.val[sl][win] = np.clip(val[win], 0.0, 1.0)
        m = np.broadcast_to(np.asarray(mat, np.int16), win.shape)
        self.mat[sl][win] = m[win]
        self.part[sl][win] = self.count

    # --- primitives
    def capsule(self, p0, p1, r0, r1=None, material="dummy", base=0.55, gain=0.75,
                stripes=None, bands=None, open_ends=False) -> None:
        """Tapered capsule from p0 (radius r0, cm) to p1 (r1). The section is
        lit as a true cylinder when the axis lies across the view, which is
        how every capsule here is used. stripes=(period_cm, other_material)
        alternates two materials along the axis (the telnyashka);
        bands=(period_cm, width_cm, dv) darkens rings (quilting, seams).
        open_ends=True cuts the round caps off: a tube (a cuff, a sleeve)
        whose cap would otherwise swallow its short neighbour."""
        r1 = r0 if r1 is None else r1
        x0, y0, s0 = self.project(p0)
        x1, y1, s1 = self.project(p1)
        R0, R1 = r0 * s0, r1 * s1
        win = self._window(min(x0 - R0, x1 - R1), min(y0 - R0, y1 - R1),
                           max(x0 + R0, x1 + R1), max(y0 + R0, y1 + R1))
        if win is None:
            return
        sl, X, Y, _ = win
        ax, ay = x1 - x0, y1 - y0
        L2 = ax * ax + ay * ay
        t_raw = np.zeros_like(X) if L2 < 1e-9 else ((X - x0) * ax + (Y - y0) * ay) / L2
        t = np.clip(t_raw, 0, 1)
        dx, dy = X - (x0 + t * ax), Y - (y0 + t * ay)
        d2 = dx * dx + dy * dy
        R = R0 + (R1 - R0) * t
        inside = d2 <= R * R
        if open_ends and L2 >= 1e-9:
            inside &= (t_raw >= 0) & (t_raw <= 1)
        h = np.sqrt(np.clip(R * R - d2, 0, None))
        s = s0 + (s1 - s0) * t
        depth = p0[2] + (p1[2] - p0[2]) * t - h / s
        Rs = np.maximum(R, 1e-9)
        n = np.stack([dx / Rs, dy / Rs, -h / Rs], -1)
        val = self.shade(n, base, gain, material)
        along = t * float(np.linalg.norm(np.subtract(p1, p0)))
        mat = np.full(X.shape, MAT_ID[material], np.int16)
        if stripes is not None:
            period, other = stripes
            mat = np.where((np.floor(along / period) % 2) == 1, MAT_ID[other], mat).astype(np.int16)
        if bands is not None:
            period, width, dv = bands
            val = np.where((along % period) < width, val - dv, val)
        self._commit(sl, inside, depth, val, mat)

    def ellipsoid(self, c, axes, material="dummy", base=0.55, gain=0.75, seams=None) -> None:
        """Ellipsoid with centre c and three semi-axis VECTORS (cm). The
        projection is linearised at the centre. seams=[(axis, pos, width,
        dv)] darkens the band |local[axis] - pos| < width (glove stitching)."""
        cx, cy, s = self.project(c)
        M = np.column_stack([np.asarray(a, np.float64) for a in axes]) * s
        Minv = np.linalg.inv(M)
        ex = float(np.sqrt((M[0] ** 2).sum()))
        ey = float(np.sqrt((M[1] ** 2).sum()))
        win = self._window(cx - ex, cy - ey, cx + ex, cy + ey)
        if win is None:
            return
        sl, X, Y, _ = win
        o = np.stack([X - cx, Y - cy, np.zeros_like(X)], -1)
        p = o @ Minv.T
        q = Minv[:, 2]
        a = float(q @ q)
        b = 2.0 * (p @ q)
        cc = (p * p).sum(-1) - 1.0
        disc = b * b - 4 * a * cc
        inside = disc >= 0
        t = (-b - np.sqrt(np.clip(disc, 0, None))) / (2 * a)
        loc = p + t[..., None] * q
        n = loc @ Minv
        n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        depth = c[2] + t / s
        val = self.shade(n, base, gain, material)
        for axis, pos, width, dv in (seams or ()):
            val = np.where(np.abs(loc[..., axis] - pos) < width, val - dv, val)
        self._commit(sl, inside, depth, val, MAT_ID[material])

    def _plane(self, pts3, material, base, gain, grad=None) -> None:
        pts3 = [np.asarray(p, np.float64) for p in pts3]
        n = np.cross(pts3[1] - pts3[0], pts3[2] - pts3[0])
        if np.linalg.norm(n) < 1e-12:
            return
        n = unit(n)
        pts2 = [self.project(p)[:2] for p in pts3]
        xs, ys = [p[0] for p in pts2], [p[1] for p in pts2]
        win = self._window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)
        if win is None:
            return
        sl, X, Y, origin = win
        inside = self._poly_mask(pts2, X, origin)
        d = np.stack([(X - self.cx) / self.focal, (Y - self.cy) / self.focal, np.ones_like(X)], -1)
        denom = d @ n
        safe = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
        depth = float(n @ pts3[0]) / safe
        depth = np.where(np.abs(denom) < 1e-6, np.mean([p[2] for p in pts3]), depth)
        facing = n if n[2] < 0 else -n
        nn = np.broadcast_to(facing, X.shape + (3,))
        val = self.shade(nn, base, gain, material)
        if grad is not None:
            g_axis, g_origin, g_amount = grad
            hit = d * depth[..., None]
            val = val + g_amount * ((hit - g_origin) @ g_axis)
        self._commit(sl, inside, depth, val, MAT_ID[material])

    def plate(self, origin, U, V, poly, thick, material="steel", base=0.55, gain=0.8,
              grad=None) -> None:
        """A flat solid: polygon `poly` [(u, v) cm] in the plane spanned by
        the unit vectors U, V at `origin`, extruded `thick` cm both ways.
        Front, back and every side wall are drawn, so it turns correctly.
        grad=(axis_vector, amount_per_cm) brightens along an axis."""
        U, V = unit(U), unit(V)
        N = unit(np.cross(U, V))
        o = np.asarray(origin, np.float64)
        g = None if grad is None else (unit(grad[0]), o, grad[1])
        faces = []
        for sign in (-1, 1):
            off = o + N * sign * thick / 2
            faces.append([off + u * U + v * V for u, v in poly])
        for f in faces:
            self._plane(f, material, base, gain, g)
        k = len(poly)
        for i in range(k):
            a, b = faces[0][i], faces[0][(i + 1) % k]
            c, d = faces[1][(i + 1) % k], faces[1][i]
            self._plane([a, b, c, d], material, base - 0.08, gain, g)

    def burst(self, cx: float, cy: float, size: float, rot: float, material: str,
              points: int = 8, inner: float = 0.42, squash: float = 1.0) -> None:
        """A flat star in screen px (muzzle flash, Doom's grammar), drawn in
        front of everything. squash < 1 flattens it vertically."""
        pts = []
        for i in range(2 * points):
            ang = np.deg2rad(rot + i * 180.0 / points)
            r = size if i % 2 == 0 else size * inner
            pts.append((cx + r * np.cos(ang), cy + r * np.sin(ang) * squash))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        win = self._window(min(xs), min(ys), max(xs), max(ys))
        if win is None:
            return
        sl, X, Y, origin = win
        inside = self._poly_mask(pts, X, origin)
        self._commit(sl, inside, np.full(X.shape, -1.0 * self.count), np.full(X.shape, 0.5),
                     MAT_ID[material])

    # --- reduction
    def reduce(self):
        """Majority vote per SSxSS block (ties to the nearer part). Returns
        material id (-1 transparent), value, part id and depth at 1x."""
        ss, h, w = self.ss, self.h, self.w
        blk = lambda a: a.reshape(h, ss, w, ss).transpose(0, 2, 1, 3).reshape(h, w, ss * ss)
        part, val, mat, dep = blk(self.part), blk(self.val), blk(self.mat), blk(self.depth)
        eq = (part[..., :, None] == part[..., None, :]) & (part[..., :, None] > 0)
        counts = eq.sum(-1)
        # tie-break: nearer sub-sample wins (tiny bias, never beats a count)
        score = counts - np.where(np.isfinite(dep), dep, 1e9) * 1e-6
        k = np.argmax(score, -1)
        take = lambda a: np.take_along_axis(a, k[..., None], -1)[..., 0]
        win_part = take(part)
        covered = (part > 0).sum(-1)
        n_win = take(counts)
        sel = part == win_part[..., None]
        out_val = (val * sel).sum(-1) / np.maximum(sel.sum(-1), 1)
        out_dep = np.where(sel, dep, 0).sum(-1) / np.maximum(sel.sum(-1), 1)
        ok = (covered >= COVER_MIN) & (n_win > 0) & (win_part > 0)
        out_mat = np.where(ok, take(mat), -1).astype(np.int16)
        return out_mat, out_val, np.where(ok, win_part, 0), np.where(ok, out_dep, np.inf)


def to_rgba(mat, val, part, depth) -> np.ndarray:
    """Material + value -> palette RGBA, with the contour, crease and rim
    passes (module docstring)."""
    h, w = mat.shape
    names = list(MATERIALS)
    idx = np.zeros((h, w), np.int16)
    for i, name in enumerate(names):
        n = len(MATERIALS[name].colours())
        sel = mat == i
        idx[sel] = np.rint(val[sel] * (n - 1)).astype(np.int16)
    opaque = mat >= 0
    flat = np.isin(mat, [MAT_ID[f] for f in FLAT])
    dark = np.zeros((h, w), np.int16)
    pad = lambda a, fill: np.pad(a, 1, constant_values=fill)
    P_op, P_part, P_dep, P_flat = pad(opaque, False), pad(part, 0), pad(depth, np.inf), pad(flat, False)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb = lambda a: a[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        nb_op, nb_part, nb_dep, nb_flat = nb(P_op), nb(P_part), nb(P_dep), nb(P_flat)
        live = opaque & ~flat & ~nb_flat
        jump = live & nb_op & (nb_dep < depth - DEPTH_EDGE_CM)
        crease = live & nb_op & (nb_part != part) & (nb_dep < depth)
        rim = opaque & ~flat & ~nb_op
        dark = np.maximum(dark, np.where(crease, CREASE_STEPS, 0))
        dark = np.maximum(dark, np.where(jump, CONTOUR_STEPS, 0))
        dark = np.maximum(dark, np.where(rim, RIM_STEPS, 0))
    idx = np.maximum(idx - dark, 0)
    rgba = np.zeros((h, w, 4), np.uint8)
    for i, name in enumerate(names):
        cols = np.array(MATERIALS[name].colours(), np.uint8)
        sel = mat == i
        rgba[sel, :3] = cols[np.clip(idx[sel], 0, len(cols) - 1)]
    rgba[opaque, 3] = 255
    return rgba


@dataclass
class Frame:
    """A rendered sprite: RGBA cropped to its content, its material map,
    and its position in the weapon space (or its pickup offsets)."""
    rgba: np.ndarray
    mat: np.ndarray
    left: int           # screen x of column 0 (HUD) / grAb x (pickup)
    top: int            # screen y of row 0 (HUD) / grAb y (pickup)
    hud: bool = True

    def offsets(self) -> tuple[int, int]:
        """grAb (leftoffset, topoffset), the engine's convention."""
        if self.hud:
            return -self.left, WEAPONTOP - self.top
        return self.left, self.top


def finish(rig: Rig, hud: bool = True, pickup_floor: int | None = None) -> Frame:
    mat, val, part, depth = rig.reduce()
    rgba = to_rgba(mat, val, part, depth)
    a = rgba[..., 3] > 0
    if not a.any():
        raise ValueError("empty frame")
    ys, xs = np.nonzero(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = rgba[y0:y1, x0:x1].copy()
    cmat = mat[y0:y1, x0:x1].copy()
    if hud:
        return Frame(crop, cmat, int(rig.x0 + x0), int(rig.y0 + y0), True)
    # pickup: centred, standing on its lowest pixel (plus a sink, like Freedoom's)
    floor = (y1 - y0) if pickup_floor is None else pickup_floor
    return Frame(crop, cmat, (x1 - x0) // 2, floor, False)


def save_sprite(frame: Frame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *frame.offsets()))
    Image.fromarray(frame.rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


# ================================================================== hands
@dataclass(frozen=True)
class HandStyle:
    key: str
    hand: str           # material of the hand: a glove or skin
    sleeve: str         # material of the sleeve
    cuff: str           # "field" | "coat" | "quilt": how the sleeve ends
    telnyashka: bool    # the striped undershirt showing at the wrist
    title: str


HAND_STYLES = (
    HandStyle("A", "skin", "sleeve_field", "field", False,
              "Bare hand, field-shirt sleeve"),
    HandStyle("B", "glove_brown", "sleeve_field", "field", False,
              "Brown glove, field-shirt sleeve"),
    HandStyle("C", "glove_black", "sleeve_field", "field", False,
              "Black glove, field-shirt sleeve"),
    HandStyle("D", "glove_brown", "sleeve_coat", "coat", False,
              "Brown glove, greatcoat sleeve"),
    HandStyle("E", "glove_brown", "sleeve_field", "field", True,
              "Brown glove, field sleeve, telnyashka"),
    HandStyle("F", "glove_black", "sleeve_quilt", "quilt", False,
              "Black glove, quilted telogreika"),
)
HAND = {s.key: s for s in HAND_STYLES}
RECOMMENDED_HAND = "E"

# Hand dimensions, cm (a gloved adult hand).
FINGER_W = 2.05         # one finger's share of the grip along the shaft
FINGER_R = 1.14         # finger radius (glove leather included); fingers overlap
THUMB_R = 1.15
WRIST_R = 2.75
GLOVE_CUFF_R = 3.05
GLOVE_CUFF_LEN = 3.2
TEL_LEN = 4.2           # telnyashka showing between glove and sleeve
TEL_PERIOD = 1.05       # one stripe, cm (a little wider than life, to read at 1x)
SLEEVE_R0, SLEEVE_R1 = 3.9, 5.0     # at the cuff, at the elbow
FIELD_CUFF_LEN, FIELD_CUFF_DR = 3.4, 0.35
COAT_CUFF_LEN, COAT_CUFF_DR = 6.5, 1.0
QUILT_PERIOD, QUILT_LINE = 3.2, 0.35


def draw_grip(rig: Rig, style: HandStyle, g, axis, elbow, shaft_r: float,
              side: str = "right", trigger: bool = False, forearm: bool = True) -> dict:
    """A hand closed round a cylinder of radius shaft_r whose axis passes
    through g along `axis` (towards the business end: the axe's head, the
    gun's muzzle). The forearm goes to `elbow`. trigger=True straightens
    the index finger along the axis, onto a trigger. Returns the key points.

    The ring basis: phi = 0 is the back of the hand (K), 90 is away from the
    wrist (Fw), 180 the palm side. Fingers wrap from the knuckles round the
    far side; the thumb closes over them from the palm side."""
    g = np.asarray(g, np.float64)
    A = unit(axis)
    to_elbow = np.asarray(elbow, np.float64) - g
    Dw = perp(to_elbow, A)                       # towards the wrist, across the shaft
    K = unit(np.cross(A, Dw)) if side == "right" else unit(np.cross(Dw, A))
    Fw = -Dw
    R = shaft_r + FINGER_R * 0.85
    ring = lambda off, phi, r=R: g + A * off + r * (np.cos(np.deg2rad(phi)) * K + np.sin(np.deg2rad(phi)) * Fw)
    hand = style.hand
    glove = hand != "skin"
    base = 0.58 if hand == "skin" else 0.62
    # wrist and the back of the hand
    wrist = g + Dw * (shaft_r + 6.2) + K * 0.6 - A * 0.3 * FINGER_W
    knuckle_mid = ring(0.25 * FINGER_W, -20)
    back_c = (wrist + knuckle_mid) / 2 + K * 0.35
    long_ax = (knuckle_mid - wrist) / 2 * 1.12
    width_ax = A * (2.05 * FINGER_W)
    thick_ax = unit(np.cross(long_ax, width_ax)) * 1.55
    if np.dot(thick_ax, K) < 0:
        thick_ax = -thick_ax
    seams = [(1, p, 0.035, 0.12) for p in (-0.33, 0.0, 0.33)] if glove else None
    # palm/thenar first (mostly hidden), then fingers, then the back, then the thumb
    rig.ellipsoid(wrist + (g - wrist) * 0.45 - K * 1.6 + A * 0.9 * FINGER_W,
                  (A * 2.2, unit(g - wrist) * 2.8, K * 1.6), hand, base - 0.05)
    tips = []
    for j in range(4):
        off = (1.5 - j) * FINGER_W
        fr = FINGER_R * (0.86 if j == 3 else 1.0)
        if trigger and j == 0:
            p0 = ring(off, -15)
            p1 = p0 + Fw * 2.6 + A * 0.4 * FINGER_W
            p2 = p1 + Fw * 1.6 + A * 0.9 + (-K) * 0.9
            p3 = p2 + (-K) * 1.4 + Fw * 0.3
            for a, b, r0, r1 in ((p0, p1, fr, fr), (p1, p2, fr, fr * 0.92), (p2, p3, fr * 0.92, fr * 0.85)):
                rig.capsule(a, b, r0, r1, hand, base, 0.8)
            tips.append(p3)
            continue
        phis = (-25, 50, 120, 182)
        radii = (fr * 1.05, fr, fr * 0.93, fr * 0.85)
        pts = [ring(off, ph, R + (0.15 if k == 0 else 0.0)) for k, ph in enumerate(phis)]
        for k in range(3):
            rig.capsule(pts[k], pts[k + 1], radii[k], radii[k + 1], hand, base, 0.8)
        tips.append(pts[-1])
    rig.ellipsoid(back_c, (long_ax, width_ax, thick_ax), hand, base + 0.04, 0.8, seams=seams)
    # knuckle row: the bumps that say "fist" at 1x
    for j in range(4 if not trigger else 3):
        jj = j + (1 if trigger else 0)
        off = (1.5 - jj) * FINGER_W
        rig.ellipsoid(ring(off, -22, R + 0.35), (K * 0.95, A * 0.95, Fw * 0.95), hand, base + 0.08, 0.8)
    # thumb, from the palm side near the wrist, over the index and middle
    t0 = ring(1.75 * FINGER_W, 255, R + 1.0)
    t1 = ring(1.35 * FINGER_W, 212, R + 1.35)
    t2 = ring(0.75 * FINGER_W, 178, R + 1.25)
    if trigger:
        t1, t2 = ring(1.4 * FINGER_W, 205, R + 1.0), ring(1.2 * FINGER_W, 172, R + 0.8)
    rig.ellipsoid(t0, (A * 1.9, K * 1.5, Fw * 1.5), hand, base, 0.8)       # thenar
    rig.capsule(t0, t1, THUMB_R * 1.15, THUMB_R, hand, base + 0.05, 0.8)
    rig.capsule(t1, t2, THUMB_R, THUMB_R * 0.9, hand, base + 0.08, 0.8)
    if forearm:
        draw_forearm(rig, style, wrist, elbow)
    return {"wrist": wrist, "K": K, "A": A, "Dw": Dw, "tips": tips}


def draw_forearm(rig: Rig, style: HandStyle, wrist, elbow) -> None:
    """Wrist to elbow: glove cuff (or bare wrist), the telnyashka if the
    style shows it, the sleeve's cuff and the sleeve."""
    wrist = np.asarray(wrist, np.float64)
    elbow = np.asarray(elbow, np.float64)
    d = unit(elbow - wrist)
    at = lambda cm: wrist + d * cm
    glove = style.hand != "skin"
    if glove:
        rig.capsule(at(-0.6), at(GLOVE_CUFF_LEN), WRIST_R * 0.98, GLOVE_CUFF_R, style.hand, 0.56, 0.8,
                    bands=(GLOVE_CUFF_LEN - 0.5, 0.35, 0.10), open_ends=True)
        x = GLOVE_CUFF_LEN - 0.4
    else:
        rig.capsule(at(-0.8), at(2.6), WRIST_R * 0.95, WRIST_R * 1.05, style.hand, 0.56, 0.8)
        x = 2.0
    if style.telnyashka:
        # the undershirt's sleeve bunches at the wrist: wider than the glove cuff
        rig.capsule(at(x - 0.3), at(x + TEL_LEN), GLOVE_CUFF_R * 1.08, GLOVE_CUFF_R * 1.14, "tel_white", 0.6, 0.6,
                    stripes=(TEL_PERIOD, "tel_blue"), open_ends=True)
        x += TEL_LEN - 0.4
    sl, sb = style.sleeve, 0.55
    if style.cuff == "coat":
        rig.capsule(at(x), at(x + COAT_CUFF_LEN), SLEEVE_R0 + COAT_CUFF_DR, SLEEVE_R0 + COAT_CUFF_DR * 1.1,
                    sl, sb + 0.04, 0.8, bands=(COAT_CUFF_LEN - 0.4, 0.4, 0.14), open_ends=True)
        rig.capsule(at(x + COAT_CUFF_LEN - 0.5), elbow, SLEEVE_R0 + 0.3, SLEEVE_R1, sl, sb, 0.8)
    elif style.cuff == "quilt":
        rig.capsule(at(x), at(x + 1.6), SLEEVE_R0 * 0.92, SLEEVE_R0 * 0.95, sl, sb - 0.06, 0.8, open_ends=True)
        rig.capsule(at(x + 1.4), elbow, SLEEVE_R0 + 0.45, SLEEVE_R1 + 0.4, sl, sb, 0.8,
                    bands=(QUILT_PERIOD, QUILT_LINE, 0.16))
    else:
        rig.capsule(at(x), at(x + FIELD_CUFF_LEN), SLEEVE_R0 + FIELD_CUFF_DR, SLEEVE_R0 + FIELD_CUFF_DR,
                    sl, sb + 0.03, 0.8, bands=(FIELD_CUFF_LEN - 0.35, 0.35, 0.12), open_ends=True)
        rig.capsule(at(x + FIELD_CUFF_LEN - 0.3), elbow, SLEEVE_R0, SLEEVE_R1, sl, sb, 0.8)
        # the cuff's button, on the outer side of the wrist
        side = perp(np.array([0.0, -1.0, -0.6]), d)
        rig.ellipsoid(at(x + FIELD_CUFF_LEN * 0.55) + side * (SLEEVE_R0 + FIELD_CUFF_DR + 0.05),
                      (d * 0.5, np.cross(d, side) * 0.5, side * 0.3), "button", 0.5, 0.8)


# ================================================================ ice axe
# A Soviet climbing ice axe of the 1970s (ледоруб): wooden shaft, forged
# steel head with a toothed pick and a flat adze, steel collar and spike.
AXE_SHAFT_LEN = 66.0        # cm, spike tip to the top of the head
AXE_SHAFT_R = 1.65
AXE_SPIKE_LEN = 7.0
AXE_PLATE = 0.9             # head thickness
# The pick in the head's plane: u along the pick, v up the shaft; origin at
# the top of the shaft. Upper edge out to the tip, then the toothed lower
# edge back, then down the socket. Hand-set numbers, centimetres.
PICK_POLY = (
    (-2.3, 2.6), (2.0, 3.0), (7.0, 2.3), (11.5, 0.4), (15.2, -2.4), (18.6, -6.4),
    (17.6, -5.6), (16.6, -5.2), (16.3, -4.3), (15.2, -3.9), (14.9, -3.0), (13.8, -2.6),
    (13.5, -1.8), (12.2, -1.3), (8.0, 0.1), (3.6, 0.1), (2.3, -0.6),
    (2.1, -6.2), (-2.1, -6.2), (-2.3, 2.6),
)
# The adze, flat and across the pick's plane: (along, across) in cm.
ADZE_POLY = ((0.0, -1.5), (9.5, -2.9), (10.6, -1.5), (10.9, 0.0), (10.6, 1.5), (9.5, 2.9), (0.0, 1.5))
ADZE_DROOP = 0.22           # the adze points slightly down (tan of the angle)


def draw_ice_axe(rig: Rig, head_top, A, P, shaft_len: float = AXE_SHAFT_LEN,
                 head_scale: float = 1.0, shaft_scale: float = 1.0) -> dict:
    """The axe with the top of its head at head_top, shaft along -A, pick
    pointing along P (perpendicular to A). head_scale and shaft_scale
    exaggerate the head and the shaft's thickness, as Doom's pickups do."""
    A, P = unit(A), perp(P, unit(A))
    N = unit(np.cross(A, P))
    k, r = head_scale, AXE_SHAFT_R * shaft_scale
    top = np.asarray(head_top, np.float64)
    shaft_top = top - A * 5.2 * k
    spike_base = top - A * (shaft_len - AXE_SPIKE_LEN)
    # shaft, ferrule, spike
    rig.capsule(shaft_top, spike_base, r, r * 1.04, "wood_ash", 0.55, 0.8)
    rig.capsule(spike_base + A * 2.2, spike_base - A * 0.4, r * 1.12, r * 1.1, "steel", 0.5, 0.8)
    rig.capsule(spike_base - A * 0.3, spike_base - A * AXE_SPIKE_LEN, r * 0.95, 0.12, "steel", 0.5, 0.8)
    # collar under the head
    rig.capsule(shaft_top + A * 0.2, shaft_top - A * 3.4 * k, r * 1.14, r * 1.1, "steel", 0.48, 0.8)
    # head: the pick plate, then the adze plate across it
    pick = [(u * k, v * k) for u, v in PICK_POLY]
    rig.plate(top, P, A, pick, AXE_PLATE * k, "steel", 0.52, 0.85, grad=(A, 0.012 / k))
    adze_dir = unit(-P - A * ADZE_DROOP)
    adze = [(u * k, w * k) for u, w in ADZE_POLY]
    rig.plate(top - (A * 1.5 + P * 1.8) * k, adze_dir, N, adze, 0.55 * k, "steel", 0.5, 0.85)
    return {"top": top, "spike": spike_base - A * AXE_SPIKE_LEN, "A": A, "P": P}


@dataclass(frozen=True)
class AxePose:
    frame: str          # sprite frame letter
    name: str
    grip: tuple         # where the hand closes on the shaft, camera cm
    axis: tuple         # shaft direction, towards the head
    pick: tuple         # pick direction (made perpendicular to axis)
    grip_from_top: float    # cm from the head's top down to the grip
    elbow: tuple


# Camera space, cm. Idle: the axe held mid-shaft in front of the right
# shoulder, head up, pick towards the centre of the screen. The swing is an
# overhead pick blow into whatever is in front: raise (B), coming down (C),
# the pick in (D), and the pull back (E).
AXE_POSES = (
    AxePose("A", "idle / ready", (11.0, 12.0, 28.0), (-0.25, -0.76, 0.60), (-1.0, 0.3, 0.1),
            26.0, (30.0, 36.0, 18.0)),
    AxePose("B", "swing 1: raised", (19.0, -4.0, 31.0), (0.30, -0.90, -0.10), (-0.4, -0.3, 0.85),
            40.0, (34.0, 30.0, 22.0)),
    AxePose("C", "swing 2: coming down", (14.0, -2.0, 34.0), (-0.55, -0.55, 0.63), (-0.5, 0.75, 0.4),
            40.0, (32.0, 30.0, 22.0)),
    AxePose("D", "swing 3: the pick in", (5.0, 12.0, 40.0), (-0.35, -0.45, 0.82), (-0.4, 0.8, 0.45),
            40.0, (22.0, 40.0, 24.0)),
    AxePose("E", "recovery", (13.0, 15.0, 31.0), (-0.10, -0.85, 0.50), (-1.0, 0.45, 0.2),
            30.0, (29.0, 38.0, 15.0)),
)
AXE_POSE = {p.frame: p for p in AXE_POSES}
AXE_SPRITE, AXE_PICKUP = "SDAX", "SDAP"


def render_axe_frame(style: HandStyle, pose: AxePose) -> Frame:
    rig = Rig()
    A = unit(pose.axis)
    grip = np.asarray(pose.grip, np.float64)
    top = grip + A * pose.grip_from_top
    draw_ice_axe(rig, top, A, pose.pick)
    draw_grip(rig, style, grip, A, pose.elbow, AXE_SHAFT_R)
    return finish(rig)


# ----------------------------------------------------------------- pickup
PICKUP_W, PICKUP_H = 96, 48     # pickup canvas, px
PICKUP_DIST = 400.0             # cm: far enough that the view is nearly flat
PICKUP_PX_PER_CM = 0.66         # 66 cm of axe -> ~44 px, Doom's pickup scale
                                # (Freedoom's chainsaw CSAWA0 is 47 px long)
PICKUP_PITCH = 25.0             # degrees: pickups are seen from a little above
PICKUP_HEAD_SCALE = 1.9         # the head exaggerated, so the T and the pick read
PICKUP_SHAFT_SCALE = 1.5
PICKUP_HEAD_TURN = 40.0         # degrees


def pickup_rig() -> Rig:
    return Rig(0, 0, PICKUP_W, PICKUP_H, ss=4, focal=PICKUP_PX_PER_CM * PICKUP_DIST,
               centre=(PICKUP_W / 2, PICKUP_H / 2))


def floor_basis(pitch_deg: float = PICKUP_PITCH):
    """Camera-space directions of the floor seen from `pitch` above:
    right, away (along the floor) and up (the floor's normal)."""
    a = np.deg2rad(pitch_deg)
    right = np.array([1.0, 0.0, 0.0])
    away = np.array([0.0, -np.sin(a), np.cos(a)])
    up = np.array([0.0, -np.cos(a), -np.sin(a)])
    return right, away, up


@dataclass(frozen=True)
class PickupOption:
    key: str
    title: str


PICKUP_OPTIONS = (
    PickupOption("A", "Lying, in profile"),
    PickupOption("B", "Lying flat, from above"),
    PickupOption("C", "Upright, as in a rack"),
)
RECOMMENDED_PICKUP = "C"
PLANT_SINK = 2                  # px of spike below the floor line (option C)


def render_axe_pickup(option: str) -> Frame:
    """The world pickup: the ice axe on the floor, no hand."""
    if option == "C":       # tall, not wide: the canvas turned on its side
        rig = Rig(0, 0, PICKUP_H, PICKUP_W, ss=4, focal=PICKUP_PX_PER_CM * PICKUP_DIST,
                  centre=(PICKUP_H / 2, PICKUP_W / 2))
    else:
        rig = pickup_rig()
    centre = np.array([0.0, 0.0, PICKUP_DIST])
    right, away, up = floor_basis()
    if option == "C":
        # the climber's silhouette: standing on its spike, head on top, pick
        # to the left, as it would stand in the dorm's rack
        A = unit(up + right * 0.10)
        P = unit(-right + away * 0.5)
        top = centre + A * (AXE_SHAFT_LEN / 2)
        draw_ice_axe(rig, top, A, P, head_scale=PICKUP_HEAD_SCALE, shaft_scale=PICKUP_SHAFT_SCALE)
        f = finish(rig, hud=False)
        f.top = f.rgba.shape[0] - PLANT_SINK
        return f
    if option == "A":
        # on its side, head to the left, pick down, as Doom draws a shotgun
        A = unit(-right + up * 0.05)
        # pick down, the head turned PICKUP_HEAD_TURN about the shaft so the
        # adze shows its width instead of a one-pixel edge
        t = np.deg2rad(PICKUP_HEAD_TURN)
        P = np.array([0.0, np.cos(t), np.sin(t)])
    else:
        # flat on the floor, the shaft running away to the left, pick on the floor
        A = unit(-right * 0.92 + away * 0.40)
        P = unit(np.cross(up, A))
        if np.dot(P, away) < 0:
            P = -P
    top = centre + A * (AXE_SHAFT_LEN / 2)
    draw_ice_axe(rig, top, A, P, head_scale=PICKUP_HEAD_SCALE, shaft_scale=PICKUP_SHAFT_SCALE)
    return finish(rig, hud=False)


# =================================================================== kit
def render_kit(style: HandStyle, which: str) -> Frame:
    """The hand kit (every weapon uses one of these): a power grip on a
    shaft, a trigger grip on a stock's wrist, a support hand under a
    fore-end. A dark dummy cylinder stands in for the weapon."""
    rig = Rig()
    if which == "grip":
        g, A, el = (12.0, 14.0, 34.0), unit((-0.3, -0.86, 0.42)), (25.0, 40.0, 18.0)
        rig.capsule(np.add(g, A * 10), np.subtract(g, A * 8), 1.65, 1.65, "dummy", 0.5, 0.7)
        draw_grip(rig, style, g, A, el, 1.65)
    elif which == "trigger":
        g, A, el = (9.0, 15.0, 32.0), unit((-0.05, -0.25, 0.97)), (20.0, 40.0, 14.0)
        rig.capsule(np.subtract(g, A * 6), np.add(g, A * 16), 1.9, 1.5, "dummy", 0.5, 0.7)
        draw_grip(rig, style, g, A, el, 1.9, trigger=True)
    else:   # support: the left hand under a fore-end, from the bottom left
        g, A, el = (-6.0, 15.0, 44.0), unit((0.06, -0.20, 0.98)), (-22.0, 42.0, 22.0)
        rig.capsule(np.subtract(g, A * 12), np.add(g, A * 14), 2.2, 2.2, "dummy", 0.5, 0.7)
        draw_grip(rig, style, g, A, el, 2.2, side="left")
    return finish(rig)


# ================================================================ context
def iwad_lumps() -> tuple[bytes, dict] | None:
    if not IWAD.is_file():
        return None
    wad = IWAD.read_bytes()
    _, n, off = struct.unpack("<4sii", wad[:12])
    lumps = {}
    for i in range(n):
        pos, size, name = struct.unpack("<ii8s", wad[off + 16 * i:off + 16 * i + 16])
        lumps[name.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
    return wad, lumps


def freedoom_sprite(name: str) -> Frame | None:
    """A Freedoom sprite for COMPARISON on the sheet only (BSD-3; iwads/ is
    not in git, so this is optional and nothing of it enters a sprite)."""
    got = iwad_lumps()
    if got is None:
        return None
    wad, lumps = got
    if name not in lumps or "PLAYPAL" not in lumps:
        return None
    pp = lumps["PLAYPAL"][0]
    pal = np.frombuffer(wad[pp:pp + 768], np.uint8).reshape(256, 3)
    pos, size = lumps[name]
    d = wad[pos:pos + size]
    w, h, lo, to = struct.unpack("<hhhh", d[:8])
    img = np.zeros((h, w, 4), np.uint8)
    for x, c in enumerate(struct.unpack(f"<{w}i", d[8:8 + 4 * w])):
        while d[c] != 255:
            top, ln = d[c], d[c + 1]
            for j in range(ln):
                img[top + j, x, :3] = pal[d[c + 3 + j]]
                img[top + j, x, 3] = 255
            c += ln + 4
    return Frame(img, np.zeros((h, w), np.int16), -lo, WEAPONTOP - to, True)


def texture(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), np.uint8)


def view_backdrop(light: float = 0.82) -> np.ndarray:
    """A 320x200 MAP01-like view for the mock screen: SDCONC1 wall over the
    SDFLR2 floor foreshortened, both at a fixed light."""
    wall = texture(TEX / "SDCONC1.png")
    floor = texture(FLATS / "SDFLR2.png")
    out = np.zeros((SCREEN_H, SCREEN_W, 3), np.uint8)
    horizon = 118
    for y in range(horizon):
        out[y] = np.tile(wall[(y + 20) % wall.shape[0]], (SCREEN_W // wall.shape[1] + 1, 1))[:SCREEN_W]
    for y in range(horizon, SCREEN_H):
        dist = 900.0 / (y - horizon + 6)
        row = floor[int(dist) % floor.shape[0]]
        xs = ((np.arange(SCREEN_W) - SCREEN_CX) * dist / 70.0).astype(int) % floor.shape[1]
        out[y] = row[xs]
    out = np.clip(out.astype(np.float64) * light, 0, 255).astype(np.uint8)
    return np.asarray(artlib.quantize(Image.fromarray(out, "RGB")).convert("RGB"))


def on_screen(frames, backdrop: np.ndarray | None = None, statusbar_line: bool = True) -> np.ndarray:
    """Composite HUD frames onto the 320x200 weapon space at rest."""
    scr = (view_backdrop() if backdrop is None else backdrop).copy()
    for f in frames:
        if f is None:
            continue
        h, w = f.rgba.shape[:2]
        for yy in range(h):
            sy = f.top + yy
            if not 0 <= sy < SCREEN_H:
                continue
            x0, x1 = max(0, f.left), min(SCREEN_W, f.left + w)
            if x0 >= x1:
                continue
            row = f.rgba[yy, x0 - f.left:x1 - f.left]
            a = row[:, 3] > 0
            scr[sy, x0:x1][a] = row[a, :3]
    if statusbar_line:
        scr[STATUSBAR_TOP, ::4] = (250, 208, 40)
        scr[STATUSBAR_TOP, 1::4] = (250, 208, 40)
    return scr


def mat_luma(frame: Frame, names) -> float | None:
    ids = [MAT_ID[n] for n in names]
    sel = np.isin(frame.mat, ids) & (frame.rgba[..., 3] > 0)
    if not sel.any():
        return None
    return float(luma(frame.rgba[..., :3])[sel].mean())


def hand_metrics(style: HandStyle, frame: Frame) -> dict:
    """D39's complaint, measured: how far apart hand and sleeve are."""
    h = mat_luma(frame, [style.hand])
    s = mat_luma(frame, [style.sleeve])
    return {"hand_luma": round(h, 1), "sleeve_luma": round(s, 1),
            "hand_sleeve_gap": round(abs(h - s), 1),
            "size": list(frame.rgba.shape[1::-1]), "offsets": list(frame.offsets())}


# ================================================================== sheets
class Sheet:
    """A tall PNG laid out top to bottom, labels in the mod's font."""

    def __init__(self, width: int, title: str, stamp: str):
        self.T = Text(2)
        self.width, self.pad = width, 24
        self.bg = artlib.ramp("concrete_cold")[3]
        self.ink = artlib.ramp("cream_yellow")[14]
        self.dim = artlib.ramp("concrete_cold")[22]
        self.gold = artlib.ramp("hazard_yellow")[13]
        self.red = artlib.ramp("flag_red")[14]
        self.neutral = artlib.ramp("concrete_cold")[14]
        self.img = Image.new("RGBA", (width, 12000), (*self.bg, 255))
        self.y = self.pad
        self.T.put(self.img, (self.pad, self.y), title, self.gold)
        self.T.put(self.img, (width - self.pad - self.T.width(stamp), self.y), stamp, self.dim)
        self.y += self.T.line_h() + 6

    def para(self, text: str, colour=None, x: int | None = None, max_w: int | None = None) -> None:
        x = self.pad if x is None else x
        max_w = (self.width - x - self.pad) if max_w is None else max_w
        self.y = self.T.para(self.img, (x, self.y), text, colour or self.ink, max_w) + 4

    def label(self, xy, text: str, colour=None) -> None:
        self.T.put(self.img, xy, text, colour or self.dim)

    def paste(self, arr: np.ndarray, xy, k: int = 1) -> tuple[int, int]:
        im = zoom(arr, k).convert("RGBA")
        self.img.alpha_composite(im, (int(xy[0]), int(xy[1])))
        return im.width, im.height

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.crop((0, 0, self.width, self.y + self.pad)).convert("RGB").save(path, optimize=True)
        return path


def on_backdrop(frame: Frame, colour, pad: int = 4) -> np.ndarray:
    h, w = frame.rgba.shape[:2]
    bg = np.zeros((h + 2 * pad, w + 2 * pad, 3), np.uint8)
    bg[:] = colour
    a = frame.rgba[..., 3] > 0
    bg[pad:pad + h, pad:pad + w][a] = frame.rgba[..., :3][a]
    return bg


def crop_screen(scr: np.ndarray, box) -> np.ndarray:
    x0, y0, x1, y1 = box
    return scr[y0:y1, x0:x1]


HANDS_VERDICT = [
    "WHY E. The CEO's note was that hand and sleeve are one colour. The gap under each cell measures it: "
    "the bare hand A sits 7 luma from its sleeve, which is that complaint reproduced; the brown and black "
    "gloves on the field sleeve sit 24-26 apart, and differ in hue as well. E adds the one detail that says who he is: "
    "the blue and white telnyashka of the airborne and Spetsnaz showing between glove and cuff. It is "
    "period-correct for a 1970s Spetsnaz sergeant, it is ours and nobody else's, and it is small "
    "enough not to pull the eye from the crosshair. Brown leather separates from the green sleeve better "
    "than black (C, F): black on the dark quilted sleeve (F) is back down to a gap of 9.",
    "A IS THE CONTROL. A bare hand needs a skin colour, and palette v1 has none (the flesh ramp is "
    "reserved for the Liberty Legion); rust_brown is the closest, and it is exactly the orange-brown "
    "hand the CEO did not like. Asking for A means asking for palette v2.",
    "D AND F are the cold-weather sergeant: a greatcoat or a quilted telogreika. Good for a winter map "
    "later; indoors at a cosmodrome the field shirt is the right clothing. Any glove can go with any "
    "sleeve: say a letter, or two (B's glove on D's sleeve).",
    "HONEST LIMITS. The hand is built from capsules and ellipsoids, lit in six bands, so it is clean and "
    "consistent from frame to frame but has no painted folds or creases; at 1x, the size it is in the "
    "game, it reads as a gloved fist. Positions on screen follow Doom's arithmetic and are NOT VERIFIED "
    "in GZDoom until the engine pass (owed, D26).",
]


def build_hands(stamp: str, out_dir: Path = OUT_DIR, preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    hdir = out_dir / "hands"
    frames, metrics = {}, {}
    for st in HAND_STYLES:
        f = render_axe_frame(st, AXE_POSE["A"])
        save_sprite(f, hdir / f"hand_{st.key}_idle.png")
        frames[st.key] = f
        metrics[st.key] = hand_metrics(st, f)
    kit = {w: render_kit(HAND[RECOMMENDED_HAND], w) for w in ("grip", "trigger", "support")}
    for w, f in kit.items():
        save_sprite(f, hdir / f"kit_{RECOMMENDED_HAND}_{w}.png")
    (hdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    S = Sheet(1980, "SOVIET DOOM  ·  F4  ·  THE SERGEANT'S HAND  ·  STYLE SWEEP (D39)", stamp)
    S.para("D39: the first-person hands were Freedoom's placeholder, hand and sleeve one colour. Six "
           "styles of OUR hand, each shown in the idle grip of the new slot-1 weapon, the ice axe (D40). "
           "Point at a letter. Built by tools/art/gen_weapon.py: a small 3D pose in centimetres, projected "
           "with Doom's own 90-degree view, palette v1 only, no system fonts. Draft, nothing in assets/.",
           max_w=S.width - 2 * S.pad - 420)
    S.para("Each cell: the whole 320x200 view at 2x with the frame where it sits at rest (the dotted line "
           "is the top of the classic status bar), and the hand at 4x. Under it: hand and sleeve luma and "
           "their gap, which is what the CEO's note was about.", S.dim, max_w=S.width - 2 * S.pad - 420)
    # before: Freedoom's fist, top right
    fd = freedoom_sprite("PUNGA0")
    if fd is not None:
        bx = S.width - S.pad - 400
        S.label((bx, S.pad + 34), "TODAY: FREEDOOM PUNGA0, 2X")
        S.paste(crop_screen(on_screen([fd]), (40, 100, 240, 200)), (bx, S.pad + 34 + S.T.line_h()), 2)
    S.y = max(S.y, S.pad + 34 + S.T.line_h() + 200 + 16)
    col_w = (S.width - 2 * S.pad) // 2
    for i, st in enumerate(HAND_STYLES):
        if i % 2 == 0:
            row_y = S.y
        x = S.pad + (i % 2) * col_w
        f, m = frames[st.key], metrics[st.key]
        tag = f"{st.key}  ·  {st.title.upper()}"
        if st.key == RECOMMENDED_HAND:
            tag += "  <<< RECOMMENDED"
        S.label((x, row_y), tag, S.red if st.key == RECOMMENDED_HAND else S.gold)
        yy = row_y + S.T.line_h() + 4
        scr = on_screen([f])
        w2, h2 = S.paste(crop_screen(scr, (120, 40, 320, 200)), (x, yy), 2)
        hand_box = hand_crop_box(f)
        S.paste(hand_box, (x + w2 + 12, yy), 4 if hand_box.shape[0] * 4 <= 330 else 3)
        S.label((x, yy + h2 + 6),
                f"HAND LUMA {m['hand_luma']:.0f}  ·  SLEEVE {m['sleeve_luma']:.0f}  ·  GAP {m['hand_sleeve_gap']:.0f}"
                f"   ·   SPRITE {m['size'][0]}X{m['size'][1]}")
        if i % 2 == 1:
            S.y = yy + h2 + 6 + S.T.line_h() + 18
    S.label((S.pad, S.y), f"THE HAND KIT, STYLE {RECOMMENDED_HAND}: EVERY WEAPON USES ONE OF THESE THREE "
            "(A DARK DUMMY STANDS IN FOR THE WEAPON). 1X AND 3X.", S.gold)
    S.y += S.T.line_h() + 6
    x = S.pad
    kit_h = 0
    kit_names = {"grip": ("POWER GRIP", "ICE AXE, RPG-7"), "trigger": ("TRIGGER GRIP", "TT-33, PPSH, IZH, ROKS"),
                 "support": ("SUPPORT HAND, LEFT", "FORE-ENDS, THE DRUM")}
    for w, f in kit.items():
        arr = on_backdrop(f, S.neutral)
        w3, h3 = S.paste(arr, (x, S.y), 3)
        S.paste(arr, (x, S.y + h3 + 6), 1)
        ly = S.y + h3 + 6 + arr.shape[0] + 6
        S.label((x, ly), kit_names[w][0], S.ink)
        S.label((x, ly + S.T.line_h()), kit_names[w][1])
        x += max(w3, 420) + 40
        kit_h = max(kit_h, h3 + 12 + arr.shape[0] + 2 * S.T.line_h())
    S.y += kit_h + 18
    S.label((S.pad, S.y), f"RECOMMENDATION: {RECOMMENDED_HAND}.", S.red)
    S.y += S.T.line_h() + 2
    for v in HANDS_VERDICT:
        S.para(v)
    path = S.save(preview_dir / f"{stamp}_F4_hand-glove-sweep.png")
    return path, metrics


def hand_crop_box(f: Frame) -> np.ndarray:
    """The hand region of an idle frame: a box round the glove/skin pixels."""
    hand_ids = [MAT_ID[n] for n in ("glove_brown", "glove_black", "skin")]
    sel = np.isin(f.mat, hand_ids)
    ys, xs = np.nonzero(sel)
    pad = 10
    y0, y1 = max(0, ys.min() - pad), min(f.rgba.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(f.rgba.shape[1], xs.max() + pad)
    sub = Frame(f.rgba[y0:y1, x0:x1], f.mat[y0:y1, x0:x1], 0, 0)
    return on_backdrop(sub, artlib.ramp("concrete_cold")[14], pad=0)


# ===================================================================== axe
LIGHT_FULL = 224                # gen_enemy's light stand-in: RGB x L/224
PICKUP_SCENE_W, PICKUP_WALL_H, PICKUP_FLOOR_H = 96, 56, 28
PICKUP_FLOOR_LINE = 12          # px into the floor band
PICKUP_LIGHT = 144              # the dorm of MAP01, where the axe is found


def light_rgb(rgb: np.ndarray, light: int) -> np.ndarray:
    """Sector-light stand-in, re-quantised. NOT VERIFIED against GZDoom."""
    f = min(1.0, light / LIGHT_FULL)
    out = np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8)
    return np.asarray(artlib.quantize(Image.fromarray(out, "RGB")).convert("RGB"))


def pickup_scene(frame: Frame | None, light: int = PICKUP_LIGHT, wall_lump: str = "SDLOCK1") -> np.ndarray:
    """The pickup on SDFLR2 in front of a wall (by default SDLOCK1, the
    dorm's lockers), both in the same light, placed by its own grAb offsets."""
    wall = texture(TEX / f"{wall_lump}.png")
    floor = texture(FLATS / "SDFLR2.png")
    w = np.tile(wall, (2, 2, 1))[:PICKUP_WALL_H, :PICKUP_SCENE_W]
    fl = np.tile(floor, (2, 2, 1))[:PICKUP_FLOOR_H * 3, :PICKUP_SCENE_W]
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((PICKUP_SCENE_W, PICKUP_FLOOR_H),
                                                      Image.Resampling.NEAREST))
    canvas = np.concatenate([w, fl], 0).copy()
    if frame is not None:
        gx, gy = frame.offsets()
        x0, y0 = PICKUP_SCENE_W // 2 - gx, PICKUP_WALL_H + PICKUP_FLOOR_LINE - gy
        h, wd = frame.rgba.shape[:2]
        for yy in range(h):
            for xx in range(wd):
                cy, cx = y0 + yy, x0 + xx
                if frame.rgba[yy, xx, 3] and 0 <= cy < canvas.shape[0] and 0 <= cx < canvas.shape[1]:
                    canvas[cy, cx] = frame.rgba[yy, xx, :3]
    return light_rgb(canvas, light)


AXE_VERDICT = [
    "THE SWING. A is the rest pose: the axe held mid-shaft, head up, the pick pointing at the middle of the "
    "screen, so it reads as an ice axe before it moves. B raises it over the right shoulder (the head leaves "
    "the screen, as Doom's own wind-ups do), C brings it down across the view, D is the pick driven in at "
    "the crosshair, E pulls it back towards rest. Today's state machine plays B C D C B, which works "
    "unchanged with these frames; E is there if the mod-engineer prefers B C D E B (same 27 tics).",
    "THE PICKUP. The CEO read Freedoom's chainsaw as a chainsaw because it is one. Looked at in the dorm at "
    "1x, C is the only one of the three that reads as an ice axe without being told: standing on its spike, "
    "head on top, the silhouette on every mountaineering badge, and it is how the axe would stand in the "
    "dorm's rack, where MAP01 places it. A, lying in profile (Doom's convention), turns the T on its side and "
    "reads more like a crossbow or a pickaxe; B, flat and seen from above, is the realistic one and the "
    "weakest read. All three exaggerate the head, as Doom exaggerates every pickup.",
    "HONEST LIMITS. Same method as the hand sheet: clean and consistent, no painted wear. The pick's teeth "
    "are a few pixels at rest and vanish in the swing. Swing frames are posed, not motion-blurred, like "
    "Doom's. Screen positions follow Doom's arithmetic and are NOT VERIFIED in GZDoom (engine pass owed, D26).",
]


def build_axe(stamp: str, hand: str = RECOMMENDED_HAND, out_dir: Path = OUT_DIR,
              preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    style = HAND[hand]
    adir = out_dir / "ice_axe"
    frames, pickups, metrics = {}, {}, {}
    for pose in AXE_POSES:
        f = render_axe_frame(style, pose)
        save_sprite(f, adir / f"{AXE_SPRITE}{pose.frame}0.png")
        frames[pose.frame] = f
        metrics[f"{AXE_SPRITE}{pose.frame}0"] = {"pose": pose.name, "size": list(f.rgba.shape[1::-1]),
                                                 "offsets": [int(v) for v in f.offsets()]}
    for opt in PICKUP_OPTIONS:
        f = render_axe_pickup(opt.key)
        name = f"{AXE_PICKUP}A0" if opt.key == RECOMMENDED_PICKUP else f"{AXE_PICKUP}A0_option{opt.key}"
        save_sprite(f, adir / f"{name}.png")
        pickups[opt.key] = f
        metrics[name] = {"pickup": opt.title, "size": list(f.rgba.shape[1::-1]),
                         "offsets": [int(v) for v in f.offsets()]}
    (adir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    S = Sheet(2000, "SOVIET DOOM  ·  F4  ·  SLOT 1: THE ICE AXE (D40)  ·  FIRST PERSON AND PICKUP", stamp)
    S.para(f"D40: the ice axe replaces the sapper's shovel. Held in hand style {hand} of the hand sweep "
           "(its recommendation; any letter re-renders with --hand). A Soviet climbing axe of the 1970s: ash "
           "shaft, forged steel head with a toothed pick and a flat adze, steel collar and spike. Built by "
           "tools/art/gen_weapon.py, palette v1 only, no system fonts. Draft, nothing in assets/.")
    S.para("SPRITE NAMES: MOD-SPEC 6.3 after the D40 rename, SD_IceAxe: SDAX A-E held, SDAP A pickup "
           "(they replace the shovel's SDSH / SDSP). Frame letters follow today's state machine, so the art "
           "drops in by changing only the four-letter name in each state line.", S.dim)
    S.y += 6
    order = [p.frame for p in AXE_POSES]
    for row in (order[:3], order[3:]):
        x, h_row = S.pad, 0
        for k in row:
            f, m = frames[k], metrics[f"{AXE_SPRITE}{k}0"]
            S.label((x, S.y), f"{AXE_SPRITE}{k}0  ·  {AXE_POSE[k].name.upper()}", S.gold)
            S.label((x, S.y + S.T.line_h()),
                    f"{m['size'][0]}X{m['size'][1]} PX  ·  GRAB {m['offsets'][0]}, {m['offsets'][1]}")
            w2, h2 = S.paste(on_screen([f]), (x, S.y + 2 * S.T.line_h() + 4), 2)
            x += w2 + 16
            h_row = max(h_row, h2 + 2 * S.T.line_h() + 4)
        if len(row) < 3:        # the idle head at 4x in the free cell
            S.label((x, S.y), "A: THE HEAD AT 4X", S.gold)
            sub = frames["A"]
            ys, xs = np.nonzero(sub.mat == MAT_ID["steel"])
            crop = Frame(sub.rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1],
                         sub.mat[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 0, 0)
            S.paste(on_backdrop(crop, S.neutral), (x, S.y + S.T.line_h() + 4), 4)
        S.y += h_row + 18
    S.para("Each view is the whole 320x200 weapon space at 2x with the frame at rest (no bob); the dotted "
           "line is the top of the classic status bar.", S.dim)
    S.y += 8
    S.label((S.pad, S.y), f"THE PICKUP ({AXE_PICKUP}A0) ON SDFLR2 BEFORE THE DORM LOCKER SDLOCK1, LIGHT "
            f"{PICKUP_LIGHT}: 4X, 1X AND HALF SIZE (FURTHER AWAY)", S.gold)
    S.y += S.T.line_h() + 6
    cells = [(opt.key, opt.title, pickups[opt.key]) for opt in PICKUP_OPTIONS]  # titles fit a cell
    fd = freedoom_sprite("CSAWA0")
    if fd is not None:
        cells.append(("TODAY", "Freedoom chainsaw",
                      Frame(fd.rgba, fd.mat, fd.rgba.shape[1] // 2, fd.rgba.shape[0], False)))
    x, h_cell = S.pad, 0
    for key, title, f in cells:
        sc = pickup_scene(f)
        tag = f"{key} · {title.upper()}"
        S.label((x, S.y), tag, S.red if key == RECOMMENDED_PICKUP else S.gold)
        if key == RECOMMENDED_PICKUP:
            S.label((x, S.y + S.T.line_h()), "<<< RECOMMENDED", S.red)
        top = S.y + 2 * S.T.line_h() + 4
        w4, h4 = S.paste(sc, (x, top), 4)
        yy = top + h4 + 6
        S.paste(sc, (x, yy), 1)
        half = np.asarray(Image.fromarray(sc, "RGB").resize((sc.shape[1] // 2, sc.shape[0] // 2),
                                                            Image.Resampling.NEAREST))
        S.paste(half, (x + sc.shape[1] + 10, yy), 1)
        S.label((x + sc.shape[1] + half.shape[1] + 20, yy), f"{f.rgba.shape[1]}X{f.rgba.shape[0]}")
        x += w4 + 20
        h_cell = max(h_cell, 2 * S.T.line_h() + 4 + h4 + 6 + sc.shape[0])
    S.y += h_cell + 18
    S.label((S.pad, S.y), f"RECOMMENDATION: THE SWING AS DRAWN; PICKUP {RECOMMENDED_PICKUP}.", S.red)
    S.y += S.T.line_h() + 2
    for v in AXE_VERDICT:
        S.para(v)
    path = S.save(preview_dir / f"{stamp}_F4_ice-axe.png")
    return path, metrics


# ==================================================================== PPSh
# The PPSh-41 in its own frame: u forward along the bore (cm from the rear of
# the receiver), v up, w to the gun's left. Birch stock running under the
# receiver to the barrel jacket, blued receiver, perforated jacket with the
# slanted compensator, the 71-round drum ahead of the trigger guard.
PPSH_STOCK_POLY = (
    (-38.0, -1.8), (-24.0, -1.2), (-8.0, -0.6), (0.0, -1.4), (24.0, -1.4), (24.6, -3.0),
    (21.0, -4.2), (8.0, -4.6), (2.0, -4.8), (-3.0, -5.8), (-7.0, -7.6), (-12.0, -8.4),
    (-20.0, -9.6), (-30.0, -11.8), (-38.0, -12.6),
)
# First person: the butt is beside the body, behind the eye, where a
# projection flips; the HUD model stops at the wrist (off-screen anyway).
PPSH_STOCK_POLY_HUD = (
    (-12.0, -1.0), (-8.0, -0.6), (0.0, -1.4), (24.0, -1.4), (24.6, -3.0), (21.0, -4.2),
    (8.0, -4.6), (2.0, -4.8), (-3.0, -5.8), (-7.0, -7.6), (-12.0, -8.4),
)
PPSH_STOCK_W = 3.6              # stock thickness
PPSH_RECEIVER = (-1.0, 23.0, 1.7)       # u from, u to, radius
PPSH_JACKET = (23.0, 47.0, 1.6)
PPSH_JACKET_SLOTS = (2.4, 1.0, 0.30)    # period, width, darkening (the perforations)
PPSH_DRUM = (10.5, -9.8, 7.0, 2.6)      # u, v of the centre, radius, half thickness
PPSH_MUZZLE_U = 50.0
PPSH_BLUED = 0.32               # blued steel sits low on the gunmetal ramp
PPSH_SPRITE, PPSH_FLASH, PPSH_PICKUP = "SDPP", "SDPF", "SDPQ"


def draw_ppsh(rig: Rig, origin, U, V, stock=PPSH_STOCK_POLY) -> dict:
    """The gun with the rear of its receiver at `origin`, bore along U, up V."""
    U = unit(U)
    V = perp(V, U)
    W = unit(np.cross(V, U))
    o = np.asarray(origin, np.float64)
    at = lambda u, v=0.0, w=0.0: o + U * u + V * v + W * w
    # stock and fore-end, one birch piece
    rig.plate(at(0, 0), U, V, stock, PPSH_STOCK_W, "wood_birch", 0.55, 0.8,
              grad=(V, 0.008))
    # receiver and its rear sight
    u0, u1, r = PPSH_RECEIVER
    rig.capsule(at(u0), at(u1), r, r * 0.95, "gunmetal", PPSH_BLUED, 0.85)
    rig.plate(at(3.0, r + 0.2), U, V, ((-1.2, -0.6), (1.2, -0.6), (1.0, 1.0), (-0.6, 1.0)), 1.4,
              "gunmetal", 0.4, 0.8)
    # trigger guard
    rig.capsule(at(-1.2, -4.8), at(3.6, -6.4), 0.35, 0.35, "gunmetal", 0.4, 0.8)
    rig.capsule(at(3.6, -6.4), at(5.4, -4.4), 0.35, 0.35, "gunmetal", 0.4, 0.8)
    # perforated barrel jacket, compensator, front sight
    j0, j1, jr = PPSH_JACKET
    rig.capsule(at(j0), at(j1), jr, jr, "gunmetal", PPSH_BLUED + 0.06, 0.85, bands=PPSH_JACKET_SLOTS)
    rig.capsule(at(j1 - 0.2), at(PPSH_MUZZLE_U - 0.4), jr * 1.08, jr * 1.08, "gunmetal", 0.4, 0.85)
    rig.plate(at(PPSH_MUZZLE_U - 1.6, jr + 0.1), U, V, ((-0.6, 0.0), (0.6, 0.0), (0.3, 1.2), (-0.3, 1.2)),
              0.5, "gunmetal", 0.45, 0.8)
    # the drum
    du, dv, dr, dt = PPSH_DRUM
    c = at(du, dv)
    rig.ellipsoid(c, (U * dr, V * dr, W * dt), "gunmetal", PPSH_BLUED + 0.04, 0.85,
                  seams=[(2, 0.0, 0.08, 0.15)])
    rig.ellipsoid(c + W * dt * 0.75, (U * 1.6, V * 1.6, W * 0.6), "gunmetal", 0.62, 0.8)
    return {"muzzle": at(PPSH_MUZZLE_U), "at": at}


@dataclass(frozen=True)
class GunPose:
    frame: str
    name: str
    origin: tuple       # rear of the receiver, camera cm
    bore: tuple
    up: tuple


# Held at the hip on the right, the bore running in towards the middle of
# the screen (a three-quarter view from the right and behind: straight from
# behind the gun collapses to its receiver); B is the same pose kicked back
# and up by a round.
PPSH_POSES = (
    GunPose("A", "idle / firing, round 1", (14.0, 9.0, 18.0), (-17.9, -2.0, 44.0), (0.2, -1.0, 0.0)),
    GunPose("B", "recoil, round 2", (14.3, 8.4, 16.8), (-17.9, -3.6, 44.0), (0.25, -1.0, 0.0)),
)
PPSH_POSE = {p.frame: p for p in PPSH_POSES}
PPSH_RIGHT_ELBOW = (20.0, 40.0, 5.0)
PPSH_LEFT_ELBOW = (-18.0, 40.0, 30.0)


def render_ppsh_frame(style: HandStyle, pose: GunPose) -> tuple[Frame, tuple[float, float]]:
    """A held frame and the muzzle's screen position (for the flash)."""
    rig = Rig()
    U, V = unit(pose.bore), perp(pose.up, unit(pose.bore))
    got = draw_ppsh(rig, pose.origin, U, V, stock=PPSH_STOCK_POLY_HUD)
    at = got["at"]
    # right hand on the stock's wrist, index on the trigger
    wrist_axis = unit(U + V * 0.55)
    draw_grip(rig, style, at(-5.0, -5.6), wrist_axis, PPSH_RIGHT_ELBOW, 2.0, trigger=True)
    # left hand under the fore-end, ahead of the drum
    draw_grip(rig, style, at(20.5, -3.0), U, PPSH_LEFT_ELBOW, 2.0, side="left")
    mx, my, _ = rig.project(got["muzzle"])
    return finish(rig), (mx, my)


PPSH_FLASH_SIZE = (15.0, 11.0)          # px: frame A's burst, frame B's


def render_ppsh_flash(which: str, muzzle_xy) -> Frame:
    """SDPF A/B: a hard burst at the muzzle, plus the compensator's upward
    jets (the PPSh's slanted muzzle throws its gas up)."""
    rig = Rig()
    mx, my = muzzle_xy
    size = PPSH_FLASH_SIZE[0 if which == "A" else 1]
    rot = 11.0 if which == "A" else 33.0
    rig.burst(mx, my - size * 0.55, size * 0.55, rot + 7, "flash_out", 5, 0.35, squash=1.5)
    rig.burst(mx, my, size, rot, "flash_out")
    rig.burst(mx, my, size * 0.62, rot + 22.5, "flash_in")
    rig.burst(mx, my, size * 0.25, 0.0, "flash_core", 6, 0.8)
    return finish(rig)


def render_ppsh_pickup() -> Frame:
    """SDPQ: the gun lying on its side, muzzle to the left, drum down."""
    rig = Rig(0, 0, PICKUP_W, PICKUP_H, ss=4, focal=PICKUP_GUN_PX_PER_CM * PICKUP_DIST,
              centre=(PICKUP_W / 2, PICKUP_H / 2))
    right, away, up = floor_basis()
    U = -right
    origin = np.array([0.0, 0.0, PICKUP_DIST]) - U * 6.0 + up * 3.0
    draw_ppsh(rig, origin, U, up)
    return finish(rig, hud=False)


PICKUP_GUN_PX_PER_CM = 0.62     # 88 cm of PPSh -> ~55 px (Freedoom's MGUNA0 is 50)

PPSH_VERDICT = [
    "WHAT IT IS. The icon of the mod, held at the hip in both hands: the birch stock, the perforated "
    "jacket running in towards the crosshair, the drum under it, our glove on the wrist with the finger on "
    "the trigger and the left hand under the fore-end. Two held frames as the state machine wants (A fires round one, B is "
    "the kick of round two) and two flash frames; today's Flash state shows SDPF A only, so B is spare "
    "until the mod-engineer alternates them.",
    "THE PICKUP lies on its side, drum down: the drum and the slotted jacket are what say PPSh at 1x, and "
    "neither is in Freedoom's chaingun.",
    "HONEST LIMITS. Straight from behind, the gun collapsed to its receiver, so it is held in a "
    "three-quarter view from the right: the jacket and the stock read, the drum shows only its lower edge "
    "behind the left hand, and the stock is a smooth brown block without the PPSh's sharp lines. Same "
    "method and limits as the hand and the ice axe; positions NOT VERIFIED in GZDoom (engine pass owed, D26).",
]


def build_ppsh(stamp: str, hand: str = RECOMMENDED_HAND, out_dir: Path = OUT_DIR,
               preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    style = HAND[hand]
    pdir = out_dir / "ppsh"
    frames, flashes, metrics = {}, {}, {}
    for pose in PPSH_POSES:
        f, muzzle = render_ppsh_frame(style, pose)
        save_sprite(f, pdir / f"{PPSH_SPRITE}{pose.frame}0.png")
        fl = render_ppsh_flash(pose.frame, muzzle)
        save_sprite(fl, pdir / f"{PPSH_FLASH}{pose.frame}0.png")
        frames[pose.frame], flashes[pose.frame] = f, fl
        for name, fr in ((f"{PPSH_SPRITE}{pose.frame}0", f), (f"{PPSH_FLASH}{pose.frame}0", fl)):
            metrics[name] = {"size": list(fr.rgba.shape[1::-1]), "offsets": [int(v) for v in fr.offsets()]}
    pk = render_ppsh_pickup()
    save_sprite(pk, pdir / f"{PPSH_PICKUP}A0.png")
    metrics[f"{PPSH_PICKUP}A0"] = {"size": list(pk.rgba.shape[1::-1]), "offsets": [int(v) for v in pk.offsets()]}
    (pdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    S = Sheet(2000, "SOVIET DOOM  ·  F4  ·  SLOT 4: THE PPSH-41  ·  FIRST PERSON, FLASH AND PICKUP", stamp)
    S.para(f"The PPSh-41 in hand style {hand} of the hand sweep, same rig as the ice axe. MOD-SPEC 6.3 "
           "names: SDPP A-B held, SDPF A-B flash, SDPQ A pickup. Built by tools/art/gen_weapon.py, palette "
           "v1 only, no system fonts. Draft, nothing in assets/.")
    S.y += 6
    x, h_row = S.pad, 0
    views = [("SDPPA0", [frames["A"]]), ("SDPPA0 + SDPFA0", [frames["A"], flashes["A"]]),
             ("SDPPB0 + SDPFB0", [frames["B"], flashes["B"]])]
    for title, fs in views:
        S.label((x, S.y), title, S.gold)
        w2, h2 = S.paste(on_screen(fs), (x, S.y + S.T.line_h() + 4), 2)
        x += w2 + 16
        h_row = max(h_row, h2 + S.T.line_h() + 4)
    S.y += h_row + 10
    items = [f"{k} {m['size'][0]}X{m['size'][1]} GRAB {m['offsets'][0]},{m['offsets'][1]}"
             for k, m in metrics.items()]
    for i in range(0, len(items), 3):
        S.label((S.pad, S.y), "  ·  ".join(items[i:i + 3]))
        S.y += S.T.line_h()
    S.y += 14
    # today, for comparison
    x = S.pad
    fd = [freedoom_sprite(n) for n in ("CHGGA0", "CHGFA0")]
    if all(f is not None for f in fd):
        S.label((x, S.y), "TODAY: CHGGA0 + CHGFA0", S.gold)
        S.paste(on_screen(fd), (x, S.y + S.T.line_h() + 4), 1)
        x += SCREEN_W + 60
    S.label((x, S.y), f"{PPSH_PICKUP}A0 BEFORE SDSTEL1, LIGHT 176 (HANGAR): 4X, 1X", S.gold)
    sc = pickup_scene(pk, 176, "SDSTEL1")
    w4, h4 = S.paste(sc, (x, S.y + S.T.line_h() + 4), 4)
    S.paste(sc, (x + w4 + 12, S.y + S.T.line_h() + 4), 1)
    mg = freedoom_sprite("MGUNA0")
    if mg is not None:
        mg = Frame(mg.rgba, mg.mat, mg.rgba.shape[1] // 2, mg.rgba.shape[0], False)
        S.label((x + w4 + 12, S.y + S.T.line_h() + 4 + sc.shape[0] + 8), "TODAY: MGUNA0")
        S.paste(pickup_scene(mg, 176, "SDSTEL1"), (x + w4 + 12, S.y + 2 * S.T.line_h() + 4 + sc.shape[0] + 12), 1)
    S.y += S.T.line_h() + 4 + max(h4, SCREEN_H) + 18
    S.label((S.pad, S.y), "RECOMMENDATION: AS DRAWN, WITH THE HAND THE CEO PICKS.", S.red)
    S.y += S.T.line_h() + 2
    for v in PPSH_VERDICT:
        S.para(v)
    path = S.save(preview_dir / f"{stamp}_F4_ppsh41.png")
    return path, metrics


# ==================================================================== main
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("what", choices=("hands", "axe", "ppsh"))
    ap.add_argument("--hand", default=RECOMMENDED_HAND, choices=sorted(HAND))
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    args = ap.parse_args(argv)
    if args.what == "hands":
        path, metrics = build_hands(args.stamp)
    elif args.what == "axe":
        path, metrics = build_axe(args.stamp, args.hand)
    else:
        path, metrics = build_ppsh(args.stamp, args.hand)
    for k, m in metrics.items():
        print(k, m)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
