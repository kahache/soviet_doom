"""F4 — first-person weapons: the sergeant's hands (D39), the ice axe (D40),
the PPSh-41 and the rest of the arsenal (TT-33, IZh-58, RPG-7, ROKS-3, hand
Katyusha).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_weapon.py hands      (Windows)
    .venv/bin/python tools/art/gen_weapon.py hands              (macOS)
    ... gen_weapon.py axe  --hand E      the ice axe, frames + pickup
    ... gen_weapon.py ppsh --hand E      the PPSh-41, frames, flash + pickup
    ... gen_weapon.py tt33|izh|rpg7|roks3|katyusha --hand E   one weapon, its sheet
    ... gen_weapon.py arsenal --hand E   all five, their sheets and the overview
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
    tt33, izh, rpg7, roks3, katyusha
            held frames with the letters each weapon's state machine in
            src/zscript/weapons/ shows (read, never edited), flash frames,
            pickup; a frame the state machine does not show is a PROPOSAL,
            written as <NAME><F>0_proposed.png (the RPG-7's reload, C-D)
    arsenal all five, plus one overview of all seven weapons at rest

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
    work/art/weapons/tt33/       SDTTA0-C0, SDTFA0, SDTPA0, metrics.json
    work/art/weapons/izh/        SDIZA0-D0, SDIFA0-B0, SDIPA0, metrics.json
    work/art/weapons/rpg7/       SDRLA0-B0 (+ C0, D0 _proposed), SDRFA0-D0, SDRPA0, metrics.json
    work/art/weapons/roks3/      SDRKA0-B0, SDKFA0-B0, SDKPA0, metrics.json
    work/art/weapons/katyusha/   pass 3: SDHKA0-B0 (+ C0, D0 _proposed), SDHFA0-B0, SDHPA0, metrics.json;
                                 variants/ holds variants B and C, launcher_only/ the frames without hands
    docs/art/previews/<stamp>_F4_<slug>.png   the sheet of each delivery
Sprites are RGBA with hard alpha, like the F5 drafts (ART-BIBLE §2
exception); the shipped format is decided with the mod-engineer on
approval.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
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
    # the rest of the arsenal (appended: earlier ids, and so earlier renders,
    # do not move)
    "bakelite": Material("rust_brown", 0, 5, black_floor=True),       # TT-33 and RPG grips
    "wood_walnut": Material("rust_brown", 1, 9, black_floor=True),    # the IZh's stock
    "olive_paint": Material("military_green", 1, 13, black_floor=True),   # PG-7V, the battery frame
    "brass": Material("hazard_yellow", 3, 14, black_floor=True),      # shell heads
    "hull_red": Material("flag_red", 3, 13, black_floor=True),        # shell hulls, rocket noses
    "rubber": Material("concrete_cold", 0, 9, black_floor=True),      # the ROKS hose, nozzles
    "flame_red": Material("flag_red", 10, 15),
    "smoke": Material("concrete_cold", 12, 24),
    "ember": Material("flag_red", 9, 15),
}
MAT_ID = {name: i for i, name in enumerate(MATERIALS)}
METALS = {"steel", "gunmetal", "button"}
FLAT = {"flash_out", "flash_in", "flash_core", "flame_red", "smoke", "ember"}   # no light, no contour


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
              points: int = 8, inner: float = 0.42, squash: float = 1.0, value: float = 0.5) -> None:
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
        self._commit(sl, inside, np.full(X.shape, -1.0 * self.count), np.full(X.shape, value),
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


# The ice axe in Freedoom's fist (N4, D63): the axe alone, its grip set into
# the ring of thumb and index of the approved fist R3-A2 (Freedoom's PUNGC0
# recoloured, tools/art/hand_study.py), which is a near, big sprite. Drawn
# whole at the fist's depth the head would be wider than the screen, so the
# shaft runs from the fist (AXE_FD_GRIP_Z) back to a head placed by screen
# point and depth, and the head is turned to show its profile (the T of pick
# and adze) whatever the shaft's depth: Doom's grammar, the weapon drawn to
# read, not to measure. New code only: nothing above reads it.
AXE_FD_GRIP_Z = 22.0            # cm: the grip ring's depth (R3-A2's fist is drawn about this near)
AXE_FD_SHAFT_K = 0.6            # shaft radius at the fist over AXE_SHAFT_R (fits the fist's ring)
AXE_FD_HEAD_K = 0.9             # ... and under the head (the far end, kept thick enough to read)


def screen_to_cam(sx: float, sy: float, z: float, focal: float = FOCAL) -> np.ndarray:
    """The camera-space point (cm) at depth z that projects to weapon-space (sx, sy)."""
    return np.array([(sx - SCREEN_CX) * z / focal, (sy - SCREEN_CY) * z / focal, z])


def draw_ice_axe_head(rig: Rig, top, A, P, k: float, r: float) -> np.ndarray:
    """draw_ice_axe's collar, pick and adze without shaft or spike, the
    head's top at `top`; returns the shaft's top (where a shaft meets it)."""
    A, P = unit(A), perp(P, unit(A))
    N = unit(np.cross(A, P))
    top = np.asarray(top, np.float64)
    shaft_top = top - A * 5.2 * k
    rig.capsule(shaft_top + A * 0.2, shaft_top - A * 3.4 * k, r * 1.14, r * 1.1, "steel", 0.48, 0.8)
    rig.plate(top, P, A, [(u * k, v * k) for u, v in PICK_POLY], AXE_PLATE * k, "steel", 0.52, 0.85,
              grad=(A, 0.012 / k))
    adze_dir = unit(-P - A * ADZE_DROOP)
    rig.plate(top - (A * 1.5 + P * 1.8) * k, adze_dir, N, [(u * k, w * k) for u, w in ADZE_POLY],
              0.55 * k, "steel", 0.5, 0.85)
    return shaft_top


@dataclass(frozen=True)
class AxeFdPose:
    """One held frame of the ice axe in Freedoom's fist. Screen numbers are
    weapon-space px (320x200, no status bar)."""
    frame: str
    name: str
    fist: tuple             # top-left of the fist sprite
    angle: float            # the shaft on screen, degrees above the horizontal, towards the left
    head_z: float           # cm: the head's depth
    head_y: float | None    # y of the head's top point; None: searched to the D57 height (frame A)
    k: float = 1.1          # head scale (draw_ice_axe's head_scale)
    flat: float = 0.35      # the head's axis: depth part over screen part (0: in the screen plane)
    pick_rot: float = 0.0   # degrees: the pick turned about the view axis (+ clockwise on screen)
    stub: float = 4.0       # cm of shaft drawn below the grip ring (behind the fist)
    r_head: float = AXE_FD_HEAD_K


# A: at rest, lowered (the scale study: the raised pick was 128 px tall,
# PISG's band is 50-61): the fist low on the right, mostly under the bar,
# the head low on the left. Then the swing the .zs plays (PUNG B C D C B):
# B wound up over the right shoulder, C coming down across the view, D the
# pick biting at the centre, far and small.
AXE_FD_POSES = (
    AxeFdPose("A", "ready, lowered", (150, 152), 35.0, 70.0, None, r_head=1.0),
    AxeFdPose("B", "swing 1: wound up", (204, 112), 80.0, 60.0, 66.0, stub=12.0),
    AxeFdPose("C", "swing 2: coming down (the blow)", (170, 128), 22.0, 60.0, 118.0, stub=8.0),
    AxeFdPose("D", "swing 3: the pick in", (140, 146), 75.0, 95.0, 108.0, k=1.6, flat=1.2, pick_rot=-40.0),
)


def render_axe_fd(pose: AxeFdPose, grip_xy, head_y: float) -> Frame:
    """The axe alone for one AxeFdPose: the shaft from the grip ring at
    grip_xy (weapon px, depth AXE_FD_GRIP_Z) to the head, whose top point
    is head_y px high on the line at pose.angle through the ring."""
    gx, gy = grip_xy
    hx = gx - (gy - head_y) / np.tan(np.deg2rad(pose.angle))
    G = screen_to_cam(gx, gy, AXE_FD_GRIP_Z)
    top = screen_to_cam(hx, head_y, pose.head_z)
    ds = np.array([hx - gx, head_y - gy])
    A = unit([ds[0], ds[1], pose.flat * float(np.hypot(*ds))])
    c, s = np.cos(np.deg2rad(pose.pick_rot)), np.sin(np.deg2rad(pose.pick_rot))
    P = unit([A[1] * c + A[0] * s, A[1] * s - A[0] * c, 0.0])     # A turned 90 on screen, then pick_rot
    rig = Rig()
    shaft_top = draw_ice_axe_head(rig, top, A, P, pose.k, AXE_SHAFT_R * pose.r_head)
    rig.capsule(G - unit(top - G) * pose.stub, shaft_top - A * 3.0 * pose.k, AXE_SHAFT_R * AXE_FD_SHAFT_K,
                AXE_SHAFT_R * pose.r_head, "wood_ash", 0.55, 0.8)
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


# ============================================================ the arsenal
# The other five weapons: TT-33 (slot 2), IZh-58 (3), RPG-7 (5), ROKS-3 (6)
# and the hand Katyusha (7). Same rig and hand as the ice axe and the PPSh.
# Each weapon is drawn in its own frame, like draw_ppsh: u forward along the
# bore (cm), v up, w to the weapon's left; `gun_basis` maps it to camera
# space. Frame letters follow each weapon's state machine in
# src/zscript/weapons/ (read, never edited here); a pose with wired=False is
# a PROPOSAL the state machine does not show today, written with a
# `_proposed` suffix so nothing can mistake it for a delivered lump.

def gun_basis(origin, bore, up):
    """(U, V, W, at) of a weapon frame: at(u, v, w) -> camera cm."""
    U = unit(bore)
    V = perp(up, U)
    W = unit(np.cross(V, U))
    o = np.asarray(origin, np.float64)
    return U, V, W, (lambda u, v=0.0, w=0.0: o + U * u + V * v + W * w)


def guard_loop(rig: Rig, at, pts, r: float = 0.32, material: str = "gunmetal") -> None:
    """A trigger guard (or any bent rod) through the (u, v) points."""
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        rig.capsule(at(u0, v0), at(u1, v1), r, r, material, 0.4, 0.8)


@dataclass(frozen=True)
class ArmsPose:
    """One held frame. `state` and `amount` are the weapon's own: slide
    travel, hinge angle, loaded or not. wired=False: a proposal."""
    frame: str
    name: str
    origin: tuple       # the weapon frame's origin, camera cm
    bore: tuple
    up: tuple
    state: str = "ready"
    amount: float = 0.0
    wired: bool = True


# ----------------------------------------------------------------- TT-33
# The Tokarev in profile: a slab-sided slide with rear serrations, the
# exposed hammer, a raked grip with the bakelite panels and their star
# medallion. u from the rear of the slide, v up from the bore.
TT_SLIDE_POLY = ((0.0, -1.1), (0.0, 1.3), (16.8, 1.3), (18.4, 1.0), (18.4, -1.1))
TT_SLIDE_W = 2.5
TT_FRAME_POLY = ((0.6, -1.1), (15.6, -1.1), (15.6, -2.0), (10.6, -2.2), (5.2, -2.4), (4.4, -1.8), (0.6, -1.6))
TT_GRIP_POLY = ((-0.4, -1.0), (5.2, -1.4), (3.2, -11.4), (-2.6, -11.0))
TT_GRIP_W = 2.6
TT_PANEL_POLY = ((0.1, -2.4), (4.3, -2.6), (2.8, -10.4), (-1.9, -10.0))
TT_PANEL_W = 3.0
TT_SERRATIONS = (1.0, 1.6, 2.2, 2.8, 3.4, 4.0)     # u of each groove
TT_BARREL = (12.5, 18.9, 0.72)                     # u from, u to, radius
TT_GRIP_AT = (1.5, -6.6)                           # where the hand closes
TT_GRIP_AXIS = (0.205, 1.0)                        # the rake: up the grip, a little forward
TT_GRIP_R = 2.0
TT_ELBOW = (14.0, 36.0, 4.0)
TT_SPRITE, TT_FLASH, TT_PICKUP = "SDTT", "SDTF", "SDTP"


def draw_tt33(rig: Rig, origin, U, V, slide_back: float = 0.0) -> dict:
    U, V, W, at = gun_basis(origin, U, V)
    s = slide_back
    rig.capsule(at(TT_BARREL[0]), at(TT_BARREL[1]), TT_BARREL[2], TT_BARREL[2], "gunmetal", 0.26, 0.85)
    rig.plate(at(-s), U, V, TT_SLIDE_POLY, TT_SLIDE_W, "gunmetal", PPSH_BLUED + 0.04, 0.85, grad=(V, 0.02))
    for g in TT_SERRATIONS:
        rig.plate(at(g - s), U, V, ((0.0, -0.9), (0.24, -0.9), (0.24, 1.1), (0.0, 1.1)),
                  TT_SLIDE_W + 0.08, "gunmetal", PPSH_BLUED - 0.16, 0.6)
    rig.plate(at(0.6 - s, 1.3), U, V, ((0.0, 0.0), (1.0, 0.0), (0.9, 0.6), (0.1, 0.6)), 1.6, "gunmetal", 0.4, 0.8)
    rig.plate(at(16.4 - s, 1.3), U, V, ((0.0, 0.0), (0.8, 0.0), (0.7, 0.6), (0.2, 0.6)), 0.6, "gunmetal", 0.4, 0.8)
    rig.plate(at(0.0), U, V, TT_FRAME_POLY, TT_SLIDE_W - 0.1, "gunmetal", PPSH_BLUED, 0.85)
    rig.plate(at(0.0), U, V, ((-1.0, 0.2), (0.3, 0.2), (0.3, 2.2), (-0.5, 2.5), (-1.1, 1.6)), 0.9,
              "gunmetal", 0.42, 0.8)                                            # hammer, cocked
    rig.plate(at(0.0), U, V, TT_GRIP_POLY, TT_GRIP_W, "gunmetal", PPSH_BLUED, 0.85)
    rig.plate(at(0.0), U, V, TT_PANEL_POLY, TT_PANEL_W, "bakelite", 0.5, 0.8)
    rig.plate(at(0.0), U, V, ((-2.6, -11.0), (3.2, -11.4), (3.2, -12.0), (-2.6, -11.6)), 2.4,
              "gunmetal", 0.4, 0.8)                                             # magazine floor
    for side in (-1, 1):                                                        # the star medallions
        rig.ellipsoid(at(1.15, -4.7, side * TT_PANEL_W / 2), (U * 0.95, V * 0.95, W * 0.22), "bakelite", 0.75, 0.8)
    guard_loop(rig, at, ((5.4, -2.0), (6.0, -4.4), (9.6, -4.0), (10.6, -2.2)))
    rig.capsule(at(7.7, -2.2), at(7.2, -3.6), 0.35, 0.3, "gunmetal", 0.45, 0.8)
    return {"muzzle": at(TT_BARREL[1] + 0.2), "at": at, "U": U, "V": V}


TT_POSES = (
    ArmsPose("A", "ready", (7.0, 7.0, 20.0), (-0.38, -0.03, 1.0), (0.12, -1.0, -0.15)),
    ArmsPose("B", "fire: slide back", (7.2, 6.3, 19.0), (-0.38, -0.15, 1.0), (0.12, -1.0, -0.15), amount=3.2),
    ArmsPose("C", "kick, slide home", (7.3, 5.7, 18.4), (-0.38, -0.24, 1.0), (0.14, -1.0, -0.15), amount=0.6),
)


def render_tt33_frame(style: HandStyle, pose: ArmsPose) -> tuple[Frame, tuple[float, float]]:
    rig = Rig()
    got = draw_tt33(rig, pose.origin, pose.bore, pose.up, pose.amount)
    at, U, V = got["at"], got["U"], got["V"]
    axis = unit(U * TT_GRIP_AXIS[0] + V * TT_GRIP_AXIS[1])
    draw_grip(rig, style, at(*TT_GRIP_AT), axis, TT_ELBOW, TT_GRIP_R, trigger=True)
    mx, my, _ = rig.project(got["muzzle"])
    return finish(rig), (mx, my)


# The TT-33 seen from behind (D61 gate): the camera sits behind the gun, the
# muzzle points into the screen, and the back of the slide, the rear sight
# and the hammer face the player, as in Freedoom's PISGA0. Gun only: the
# hands are Freedoom's (tools/art/hand_study.py, R3-A1). TT-33 only; no
# other weapon and no existing TT-33 frame reads anything below.
TT_REAR_GRIP_UV = (0.2, -1.0)           # the point set into the hands: the slide's lower rear edge
TT_REAR_UP = (0.0, -1.0, 0.0)


TT_REAR_STRETCH = 1.45                  # first person: the slide this much wider, so it reads at 1x
                                        # like Freedoom's chunky pistol (cf. IZH_HUD_BORE_K)


class StretchRig(Rig):
    """A rig whose picture is stretched sideways by k about screen column
    xc: projection and the ray back through each pixel agree, so depth and
    light stay right. Used by the rear-view TT-33 only."""

    def __init__(self, k: float, xc: float, **kw):
        super().__init__(**kw)
        self.k, self.xc = k, xc

    def project(self, p):
        x, y, s = super().project(p)
        return self.xc + (x - self.xc) * self.k, y, s

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
        Xu = self.xc + (X - self.xc) / self.k                   # undo the stretch for the ray
        d = np.stack([(Xu - self.cx) / self.focal, (Y - self.cy) / self.focal, np.ones_like(X)], -1)
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


@dataclass(frozen=True)
class RearPose:
    frame: str
    name: str
    pitch: float            # muzzle above the line of sight, as the tangent (the recoil kick)
    slide_back: float = 0.0


TT_REAR_POSES = (
    RearPose("A", "ready, from behind", 0.05),
    RearPose("B", "fire: kicks up, slide back", 0.18, 3.2),
    RearPose("C", "coming back down, slide home", 0.09, 0.6),
)


def render_tt33_rear(pose: RearPose, depth: float, grip_xy, focal: float = FOCAL) -> tuple[Frame, tuple[float, float]]:
    """The gun alone, seen from behind, its TT_REAR_GRIP_UV point projected
    onto grip_xy (weapon-space px) with the slide's rear `depth` cm away.
    A longer focal flattens the perspective (Freedoom's pistol is drawn with
    little of it). Returns the frame and the muzzle's screen position."""
    bore = (0.0, -pose.pitch, 1.0)
    U, V, W, at0 = gun_basis((0.0, 0.0, 0.0), bore, TT_REAR_UP)
    d = at0(*TT_REAR_GRIP_UV)
    gz = depth + d[2]
    origin = ((grip_xy[0] - SCREEN_CX) * gz / focal - d[0], (grip_xy[1] - SCREEN_CY) * gz / focal - d[1], depth)
    rig = StretchRig(TT_REAR_STRETCH, grip_xy[0], focal=focal)
    got = draw_tt33(rig, origin, bore, TT_REAR_UP, pose.slide_back)
    mx, my, _ = rig.project(got["muzzle"])
    return finish(rig), (mx, my)


# ---------------------------------------------------------------- IZh-58
# A side-by-side 12-gauge: two blued barrels touching, a rib between them,
# a grey box-lock action, walnut fore-end and stock. The barrels, rib and
# fore-end hinge down about the pin at IZH_HINGE (the break-open reload).
IZH_BARREL_LEN = 72.0
IZH_BARREL_R = 1.05
IZH_BARREL_W = 1.06             # half the centre distance: the barrels touch
IZH_HUD_BORE_K = 1.6            # first person: barrels this much fatter, so the pair reads at 1x
IZH_HINGE = (0.4, -2.2)         # u, v of the hinge pin
IZH_ACTION_POLY = ((-6.5, 1.1), (0.4, 1.1), (0.4, -2.9), (-1.5, -3.6), (-6.5, -2.8))
IZH_ACTION_W = 4.2
IZH_FOREEND_POLY = ((3.0, -0.7), (25.0, -0.7), (25.0, -1.9), (23.0, -2.7), (6.0, -3.3), (3.0, -3.1))
IZH_FOREEND_W = 3.8
IZH_STOCK_POLY_HUD = ((-6.5, 0.9), (-14.0, -0.6), (-14.0, -6.8), (-10.0, -6.4), (-8.5, -4.2), (-6.5, -2.8))
IZH_STOCK_POLY = ((-6.5, 0.9), (-16.0, -0.8), (-40.0, -2.0), (-40.0, -14.0), (-24.0, -9.0),
                  (-12.0, -6.6), (-8.5, -4.2), (-6.5, -2.8))
IZH_STOCK_W = 3.6
IZH_SHELL_R = 0.98
IZH_RIGHT_GRIP, IZH_RIGHT_AXIS = (-10.6, -2.4), (1.0, 0.45)
IZH_LEFT_GRIP_U = 21.0
IZH_SPRITE, IZH_FLASH, IZH_PICKUP = "SDIZ", "SDIF", "SDIP"


def draw_izh(rig: Rig, origin, bore, up, open_deg: float = 0.0, hud: bool = True) -> dict:
    U, V, W, at = gun_basis(origin, bore, up)
    k = IZH_HUD_BORE_K if hud else 1.0
    br, bw = IZH_BARREL_R * k, IZH_BARREL_W * k
    th = np.deg2rad(open_deg)
    hu, hv = IZH_HINGE

    def bat(u, v=0.0, w=0.0):           # a point of the barrel group, hinged
        du, dv = u - hu, v - hv
        return at(hu + du * np.cos(th) + dv * np.sin(th), hv - du * np.sin(th) + dv * np.cos(th), w)

    Ub = unit(bat(1.0) - bat(0.0))
    Vb = unit(bat(0.0, 1.0) - bat(0.0))
    for side in (-1, 1):
        rig.capsule(bat(0.0, 0.0, side * bw), bat(IZH_BARREL_LEN, 0.0, side * bw),
                    br, br * 0.92, "gunmetal", PPSH_BLUED + 0.04, 0.85, open_ends=True)
    rig.capsule(bat(0.6, 0.85 * k), bat(IZH_BARREL_LEN, 0.85 * k), 0.3 * k, 0.3 * k, "gunmetal", 0.45, 0.8)  # rib
    rig.ellipsoid(bat(IZH_BARREL_LEN - 0.8, 1.2 * k), (Ub * 0.28 * k, Vb * 0.28 * k, W * 0.28 * k), "brass", 0.75, 0.8)
    rig.plate(bat(0.0), Ub, Vb, IZH_FOREEND_POLY, IZH_FOREEND_W, "wood_walnut", 0.55, 0.8)
    if open_deg > 0:
        # the breech: left chamber loaded, the right shell going in
        for side in (-1, 1):
            rig.capsule(bat(-0.2, 0.0, side * bw), bat(0.08, 0.0, side * bw),
                        br * 1.12, br * 1.12, "brass", 0.6, 0.8, open_ends=True)
        w, sr = -bw, IZH_SHELL_R * k
        rig.capsule(bat(-5.2, 0.0, w), bat(-0.1, 0.0, w), sr, sr, "hull_red", 0.55, 0.8, open_ends=True)
        rig.capsule(bat(-6.4, 0.0, w), bat(-5.0, 0.0, w), sr * 1.04, sr * 1.04, "brass", 0.62, 0.8, open_ends=True)
    rig.plate(at(0.0), U, V, IZH_ACTION_POLY, IZH_ACTION_W, "steel", 0.4, 0.85)
    rig.plate(at(0.0), U, V, ((-6.2, 1.1), (-3.0, 1.1), (-3.2, 1.7), (-6.0, 1.8)), 1.2, "steel", 0.45, 0.8)
    rig.plate(at(0.0), U, V, IZH_STOCK_POLY_HUD if hud else IZH_STOCK_POLY, IZH_STOCK_W,
              "wood_walnut", 0.55, 0.8, grad=(V, 0.008))
    guard_loop(rig, at, ((-6.0, -3.0), (-5.0, -5.8), (-0.8, -5.6), (0.0, -3.4)))
    rig.capsule(at(-3.6, -3.3), at(-3.9, -5.0), 0.3, 0.28, "gunmetal", 0.45, 0.8)
    rig.capsule(at(-2.3, -3.3), at(-2.6, -4.8), 0.3, 0.28, "gunmetal", 0.45, 0.8)
    return {"muzzle": bat(IZH_BARREL_LEN + 0.6), "at": at, "bat": bat, "U": U, "V": V, "Ub": Ub}


IZH_POSES = (
    ArmsPose("A", "ready / fire", (4.0, 10.5, 15.0), (-0.07, -0.06, 1.0), (0.06, -1.0, 0.0)),
    ArmsPose("B", "kick; reload 3: coming up", (4.2, 9.6, 14.0), (-0.07, -0.14, 1.0), (0.06, -1.0, 0.0)),
    ArmsPose("C", "settle low; reload 2: snapped shut", (4.4, 14.0, 15.0), (-0.07, -0.05, 1.0), (0.08, -1.0, 0.0)),
    ArmsPose("D", "reload 1: broken open, loading", (4.0, 10.0, 17.0), (-0.07, -0.42, 1.0), (0.12, -1.0, 0.0),
             state="open", amount=38.0),
)
IZH_LEFT_ELBOW = (-18.0, 40.0, 30.0)
IZH_RIGHT_ELBOW = (20.0, 40.0, 5.0)


def render_izh_frame(style: HandStyle, pose: ArmsPose) -> tuple[Frame, tuple[float, float]]:
    rig = Rig()
    got = draw_izh(rig, pose.origin, pose.bore, pose.up, pose.amount if pose.state == "open" else 0.0)
    at, bat, U, V = got["at"], got["bat"], got["U"], got["V"]
    draw_grip(rig, style, at(*IZH_RIGHT_GRIP), unit(U * IZH_RIGHT_AXIS[0] + V * IZH_RIGHT_AXIS[1]),
              IZH_RIGHT_ELBOW, 1.8, trigger=True)
    draw_grip(rig, style, bat(IZH_LEFT_GRIP_U, -2.2), got["Ub"], IZH_LEFT_ELBOW, 2.0, side="left")
    mx, my, _ = rig.project(got["muzzle"])
    return finish(rig), (mx, my)


# ----------------------------------------------------------------- RPG-7
# The launcher on the right shoulder: a long tube running in towards the
# crosshair, the birch heat guard, the bakelite pistol grip under it, and
# the PG-7V's olive warhead out of the muzzle (exaggerated, as Doom's
# pickups and weapons are, so the cone reads at 1x). u from the rear of the
# venturi.
RPG_TUBE_R = 2.2
RPG_VENTURI = (0.0, 9.0, 4.4, 2.4)
RPG_GUARD = (36.0, 60.0, 3.3)
RPG_MUZZLE_U = 95.0
RPG_GRIP_U = 47.0
RPG_LEFT_U = 70.0              # at rest the left hand sits low on the tube, at the edge of the view
RPG_HUD_Z0 = 12.0               # cm: in first person the tube is drawn from this depth on (the rest is behind the eye)
PG7_TAIL = (0.0, 14.0, 1.4)     # beyond the muzzle: u from, u to, radius
PG7_BODY = (14.0, 21.0, 4.25)
PG7_CONE = (21.0, 38.0, 4.25, 0.9)
PG7_FUSE = (38.0, 41.0, 0.7)
PG7_HUD_SCALE = 1.5
RPG_SPRITE, RPG_FLASH, RPG_PICKUP = "SDRL", "SDRF", "SDRP"


def draw_pg7(rig: Rig, base, U, k: float = 1.0) -> dict:
    """The PG-7V grenade from the base of its tail tube along U."""
    U = unit(U)
    b = np.asarray(base, np.float64)
    at = lambda u: b + U * u * k
    rig.capsule(at(PG7_TAIL[0]), at(PG7_TAIL[1]), PG7_TAIL[2] * k, PG7_TAIL[2] * k, "steel", 0.42, 0.8, open_ends=True)
    rig.capsule(at(PG7_BODY[0]), at(PG7_BODY[1]), PG7_BODY[2] * k * 0.9, PG7_BODY[2] * k, "olive_paint", 0.55,
                0.8, open_ends=True)
    rig.capsule(at(PG7_CONE[0]), at(PG7_CONE[1]), PG7_CONE[2] * k, PG7_CONE[3] * k, "olive_paint", 0.6, 0.8)
    rig.capsule(at(PG7_FUSE[0]), at(PG7_FUSE[1]), PG7_FUSE[2] * k, PG7_FUSE[2] * k * 0.6, "steel", 0.55, 0.8)
    return {"at": at}


def draw_rpg7(rig: Rig, origin, bore, up, loaded: bool = True, hud: bool = True, k: float = PG7_HUD_SCALE) -> dict:
    U, V, W, at = gun_basis(origin, bore, up)
    # first person: start the tube where it comes in front of the eye
    u0 = max(0.0, (RPG_HUD_Z0 - float(np.asarray(origin)[2])) / max(U[2], 1e-6)) if hud else 0.0
    if not hud:
        v0, v1, r0, r1 = RPG_VENTURI
        rig.capsule(at(v0), at(v1), r0, r1, "gunmetal", 0.38, 0.85, open_ends=True)
    rig.capsule(at(max(u0, RPG_VENTURI[1] - 0.5)), at(RPG_MUZZLE_U), RPG_TUBE_R, RPG_TUBE_R * 0.95,
                "gunmetal", PPSH_BLUED + 0.06, 0.85, open_ends=True)
    g0, g1, gr = RPG_GUARD
    rig.capsule(at(max(u0, g0)), at(g1), gr, gr, "wood_birch", 0.55, 0.8, bands=(4.0, 0.35, 0.12), open_ends=True)
    rig.capsule(at(RPG_MUZZLE_U - 1.4), at(RPG_MUZZLE_U), RPG_TUBE_R * 1.15, RPG_TUBE_R * 1.15, "gunmetal",
                0.42, 0.85, open_ends=True)
    rig.plate(at(RPG_MUZZLE_U - 3.0, RPG_TUBE_R), U, V, ((0.0, 0.0), (1.0, 0.0), (0.8, 1.8), (0.2, 1.8)), 0.5,
              "gunmetal", 0.45, 0.8)                                            # front sight
    grip_seen = (not hud) or at(RPG_GRIP_U - 3.0)[2] >= RPG_HUD_Z0     # behind the eye, it is not drawn
    if grip_seen:
        rig.plate(at(RPG_GRIP_U, -RPG_TUBE_R - 1.0), U, V, ((-1.6, 0.4), (2.0, 0.4), (0.6, -9.5), (-2.9, -9.1)),
                  2.6, "bakelite", 0.5, 0.8)
        guard_loop(rig, at, ((RPG_GRIP_U + 1.6, -3.4), (RPG_GRIP_U + 2.4, -6.0), (RPG_GRIP_U + 6.2, -5.6),
                             (RPG_GRIP_U + 6.8, -3.2)))
    if loaded:
        draw_pg7(rig, at(RPG_MUZZLE_U), U, k)
    return {"muzzle": at(RPG_MUZZLE_U + 0.5), "at": at, "U": U, "V": V, "grip_seen": grip_seen}


RPG_POSES = (
    ArmsPose("A", "ready, loaded", (11.0, 12.5, -55.0), (-0.025, -0.012, 1.0), (0.12, -1.0, 0.0)),
    ArmsPose("B", "fired, tube empty", (11.3, 11.6, -56.5), (-0.025, -0.03, 1.0), (0.12, -1.0, 0.0), state="empty"),
    ArmsPose("C", "PROPOSED reload 1: new round", (13.5, 19.0, -45.0), (-0.08, -0.06, 1.0), (0.2, -1.0, 0.0),
             state="reload1", wired=False),
    ArmsPose("D", "PROPOSED reload 2: round in", (12.5, 16.0, -50.0), (-0.06, -0.04, 1.0), (0.18, -1.0, 0.0),
             state="reload2", wired=False),
)
RPG_RIGHT_ELBOW = (18.0, 40.0, 4.0)
RPG_LEFT_ELBOW = (-18.0, 40.0, 26.0)
RPG_RELOAD_ELBOW = (-26.0, 40.0, 16.0)
RPG_NEW_ROUND = ((-14.0, 15.0, 40.0), (0.40, -0.45, 0.80))   # C: tail base, axis (camera cm)


def render_rpg7_frame(style: HandStyle, pose: ArmsPose) -> tuple[Frame, tuple[float, float]]:
    rig = Rig()
    got = draw_rpg7(rig, pose.origin, pose.bore, pose.up, loaded=pose.state == "ready")
    at, U, V = got["at"], got["U"], got["V"]
    if got["grip_seen"]:        # the right hand is on the grip, behind the eye in every pose drawn today
        draw_grip(rig, style, at(RPG_GRIP_U - 0.8, -RPG_TUBE_R - 5.4), unit(V + U * 0.16), RPG_RIGHT_ELBOW, 1.6,
                  trigger=True)
    if pose.state == "reload1":
        base, ax = RPG_NEW_ROUND
        ax = unit(ax)
        draw_pg7(rig, base, ax, PG7_HUD_SCALE)
        draw_grip(rig, style, np.asarray(base) + ax * 7.0 * PG7_HUD_SCALE, ax, RPG_RELOAD_ELBOW,
                  PG7_TAIL[2] * PG7_HUD_SCALE, side="left")
    elif pose.state == "reload2":
        base = at(RPG_MUZZLE_U - 6.0)
        draw_pg7(rig, base, U, PG7_HUD_SCALE)
        draw_grip(rig, style, base + U * 11.0 * PG7_HUD_SCALE, U, RPG_RELOAD_ELBOW,
                  PG7_TAIL[2] * PG7_HUD_SCALE, side="left")
    else:
        draw_grip(rig, style, at(RPG_LEFT_U, -RPG_TUBE_R * 0.4), U, RPG_LEFT_ELBOW, RPG_TUBE_R, side="left")
    mx, my, _ = rig.project(got["muzzle"])
    return finish(rig), (mx, my)


# ---------------------------------------------------------------- ROKS-3
# The ROKS-3 gun is built like a rifle: birch stock, a fat valve body, the
# fuel tube, and at the muzzle the drum of igniter cartridges round the
# nozzle; the hose runs from under the valve to the tank on the back.
ROKS_STOCK_POLY_HUD = ((-12.0, -1.0), (-8.0, -0.6), (0.0, -1.2), (6.0, -1.2), (6.0, -3.6), (2.0, -4.4),
                       (-3.0, -5.8), (-7.0, -7.6), (-12.0, -8.4))
ROKS_STOCK_POLY = ((-36.0, -1.4), (-20.0, -1.0), (0.0, -1.2), (6.0, -1.2), (6.0, -3.6), (2.0, -4.4),
                   (-3.0, -5.8), (-7.0, -7.6), (-14.0, -9.0), (-28.0, -11.6), (-36.0, -12.4))
ROKS_BODY = (0.0, 7.0, 1.9)
ROKS_TUBE = (7.0, 58.0, 1.2)
ROKS_IGNITER = (57.0, 62.0, 2.4)
ROKS_NOZZLE = (62.0, 67.0, 0.8)
ROKS_HOSE_R = 1.35
ROKS_HOSE_END = (12.0, 46.0, 10.0)      # camera cm: off the bottom of the screen, to the tank
ROKS_SPRITE, ROKS_FLASH, ROKS_PICKUP = "SDRK", "SDKF", "SDKP"


def bezier(p0, p1, p2, p3, n: int) -> list[np.ndarray]:
    p0, p1, p2, p3 = (np.asarray(p, np.float64) for p in (p0, p1, p2, p3))
    out = []
    for t in np.linspace(0.0, 1.0, n):
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return out


def draw_hose(rig: Rig, pts, r: float = ROKS_HOSE_R) -> None:
    for a, b in zip(pts, pts[1:]):
        rig.capsule(a, b, r, r, "rubber", 0.5, 0.8, bands=(1.6, 0.3, 0.12))


def draw_roks3(rig: Rig, origin, bore, up, hud: bool = True, hose_end=ROKS_HOSE_END) -> dict:
    U, V, W, at = gun_basis(origin, bore, up)
    rig.plate(at(0.0), U, V, ROKS_STOCK_POLY_HUD if hud else ROKS_STOCK_POLY, PPSH_STOCK_W, "wood_birch",
              0.55, 0.8, grad=(V, 0.008))
    b0, b1, br = ROKS_BODY
    rig.capsule(at(b0), at(b1), br, br * 0.9, "gunmetal", PPSH_BLUED + 0.04, 0.85)
    rig.capsule(at(3.5, br - 0.2), at(3.5, br + 1.3), 0.9, 0.8, "gunmetal", 0.42, 0.8)     # the valve stem
    t0, t1, tr = ROKS_TUBE
    rig.capsule(at(t0), at(t1), tr, tr, "gunmetal", PPSH_BLUED + 0.08, 0.85, bands=(9.0, 0.5, 0.14))
    i0, i1, ir = ROKS_IGNITER
    rig.capsule(at(i0), at(i1), ir, ir, "steel", 0.45, 0.85, bands=(1.25, 0.25, 0.18), open_ends=True)
    n0, n1, nr = ROKS_NOZZLE
    rig.capsule(at(n0), at(n1), nr * 1.3, nr, "gunmetal", 0.4, 0.85)
    guard_loop(rig, at, ((1.0, -2.0), (1.6, -4.6), (5.2, -4.4), (6.0, -2.0)))
    rig.capsule(at(3.4, -2.0), at(3.0, -3.6), 0.35, 0.3, "gunmetal", 0.45, 0.8)
    start = at(7.5, -br - 0.4)
    draw_hose(rig, bezier(start, start + V * -4.0 - U * 2.0, np.asarray(hose_end) - V * -10.0,
                          hose_end, 10))
    return {"muzzle": at(n1 + 0.4), "at": at, "U": U, "V": V}


ROKS_POSES = (
    ArmsPose("A", "ready / jet (shown Bright)", (13.0, 9.5, 18.0), (-17.5, -2.4, 44.0), (0.2, -1.0, 0.0)),
    ArmsPose("B", "after the jet: nozzle smoulders", (13.2, 9.9, 17.4), (-17.5, -1.8, 44.0), (0.2, -1.0, 0.0),
             state="ember"),
)
ROKS_RIGHT_ELBOW = (20.0, 40.0, 5.0)
ROKS_LEFT_ELBOW = (-18.0, 40.0, 30.0)


def render_roks3_frame(style: HandStyle, pose: ArmsPose) -> tuple[Frame, tuple[float, float]]:
    rig = Rig()
    got = draw_roks3(rig, pose.origin, pose.bore, pose.up)
    at, U, V = got["at"], got["U"], got["V"]
    draw_grip(rig, style, at(-5.0, -5.6), unit(U + V * 0.55), ROKS_RIGHT_ELBOW, 2.0, trigger=True)
    draw_grip(rig, style, at(22.0, -0.4), U, ROKS_LEFT_ELBOW, ROKS_TUBE[2] + 0.5, side="left")
    mx, my, _ = rig.project(got["muzzle"])
    if pose.state == "ember":
        # a burning drop on the nozzle and a curl of smoke (not Bright: B is
        # the cool-down frame)
        rig.burst(mx - 3, my - 7, 5.5, 10.0, "smoke", 6, 0.6, value=0.35)
        rig.burst(mx - 1, my - 3, 3.5, 30.0, "smoke", 5, 0.6, value=0.55)
        rig.burst(mx, my, 2.6, 0.0, "ember", 5, 0.55, value=0.6)
    return finish(rig), (mx, my)


# ------------------------------------------------- hand Katyusha, pass 1
# PASS 1 (sheet 2026-10-13_2219, judged NOT YET by its own verdict): six
# short rockets on open rails in two rows of three, an olive frame, a
# bakelite pistol grip and a forward handle, carried on the right shoulder.
# Along the rails the rockets read as a bundle of sticks and the pickup as a
# bench. Kept only so the pass-2 sheet can show it beside the launch box;
# nothing is written from it. u from the rear of the frame, v up, w left.
HK_LEN = 44.0
HK_ROWS = (0.0, 5.4)
HK_COLS = (-5.3, 0.0, 5.3)
HK_ROCKET = (1.5, 33.0, 1.45)           # tail u, nose u, radius
HK_NOSE_LEN = 7.0
HK_FRAME_V = (-2.3, 7.6)
HK_FRAME_W = 8.1
HK_GRIP_U, HK_HANDLE_U = 13.0, 33.0
HK_SPRITE, HK_FLASH, HK_PICKUP = "SDHK", "SDHF", "SDHP"


def hk_rails():
    return [(v, w) for v in HK_ROWS for w in HK_COLS]


def draw_katyusha(rig: Rig, origin, bore, up, loaded: bool = True) -> dict:
    U, V, W, at = gun_basis(origin, bore, up)
    v0, v1 = HK_FRAME_V
    fw = HK_FRAME_W
    corners = ((v0, -fw), (v0, fw), (v1, fw), (v1, -fw))
    for u in (HK_LEN - 2.0,):                           # the front cross frame (a rear one hides the tails)
        for (va, wa), (vb, wb) in zip(corners, corners[1:] + corners[:1]):
            rig.capsule(at(u, va, wa), at(u, vb, wb), 0.6, 0.6, "olive_paint", 0.55, 0.8)
    rig.plate(at(0.0, v0, 0.0), U, W, ((2.0, -fw), (HK_LEN - 2.0, -fw), (HK_LEN - 2.0, fw), (2.0, fw)), 0.5,
              "olive_paint", 0.45, 0.8)                 # the floor of the battery
    for va, wa in corners:                              # the four long bars
        rig.capsule(at(1.0, va, wa), at(HK_LEN - 2.0, va, wa), 0.5, 0.5, "olive_paint", 0.5, 0.8)
    for v, w in hk_rails():                             # the rails
        rig.plate(at(0.0, v - HK_ROCKET[2] - 0.25, w), U, W, ((0.0, -0.75), (HK_LEN, -0.75), (HK_LEN, 0.75),
                                                              (0.0, 0.75)), 0.4, "steel", 0.42, 0.85)
    if loaded:
        t, n, r = HK_ROCKET
        for v, w in hk_rails():
            rig.capsule(at(t, v, w), at(n - HK_NOSE_LEN, v, w), r, r, "steel", 0.5, 0.85, open_ends=True)
            rig.capsule(at(n - HK_NOSE_LEN, v, w), at(n, v, w), r, r * 0.25, "hull_red", 0.55, 0.8)
            rig.capsule(at(t - 0.7, v, w), at(t + 0.3, v, w), r * 0.7, r * 0.75, "rubber", 0.15, 0.6,
                        open_ends=True)                 # the nozzle
            for dv, dw in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                d = unit(V * dv + W * dw)
                rig.plate(at(t, v, w), U, d, ((0.0, r * 0.9), (3.0, r * 0.9), (2.4, r * 1.45), (0.0, r * 1.45)),
                          0.22, "steel", 0.5, 0.8)
    rig.plate(at(HK_GRIP_U, v0 - 0.4), U, V, ((-1.6, 0.4), (2.0, 0.4), (0.8, -9.0), (-2.6, -8.6)), 2.6,
              "bakelite", 0.5, 0.8)
    guard_loop(rig, at, ((HK_GRIP_U + 1.6, v0 - 1.2), (HK_GRIP_U + 2.4, v0 - 3.6),
                         (HK_GRIP_U + 6.0, v0 - 3.2), (HK_GRIP_U + 6.6, v0 - 0.8)))
    rig.capsule(at(HK_HANDLE_U, v0 - 0.4), at(HK_HANDLE_U + 0.8, v0 - 9.5), 1.3, 1.2, "bakelite", 0.5, 0.8)
    rails_rear = [at(0.0, v, w) for v, w in hk_rails()]
    rails_front = [at(HK_LEN, v, w) for v, w in hk_rails()]
    return {"at": at, "U": U, "V": V, "rear": rails_rear, "front": rails_front,
            "muzzle": at(HK_LEN, (v0 + v1) / 2)}


HK_RAILS_POSES = (
    ArmsPose("A", "ready, six loaded", (6.5, 10.0, 24.0), (-0.05, -0.06, 1.0), (0.08, -1.0, 0.0)),
    ArmsPose("B", "salvo: rails up, empty", (6.8, 8.6, 23.0), (-0.05, -0.16, 1.0), (0.08, -1.0, 0.0),
             state="empty"),
)
HK_RIGHT_ELBOW = (18.0, 40.0, 5.0)
HK_LEFT_ELBOW = (-18.0, 40.0, 30.0)


def render_katyusha_rails_frame(style: HandStyle, pose: ArmsPose) -> tuple[Frame, list]:
    """Pass 1: a held frame and the screen positions of the six rails' rear ends."""
    rig = Rig()
    got = draw_katyusha(rig, pose.origin, pose.bore, pose.up, loaded=pose.state != "empty")
    at, U, V = got["at"], got["U"], got["V"]
    v0 = HK_FRAME_V[0]
    draw_grip(rig, style, at(HK_GRIP_U - 0.8, v0 - 5.0), unit(V + U * 0.16), HK_RIGHT_ELBOW, 1.6, trigger=True)
    draw_grip(rig, style, at(HK_HANDLE_U + 0.4, v0 - 5.0), unit(V - U * 0.08), HK_LEFT_ELBOW, 1.3, side="left")
    rear = [rig.project(p) for p in got["rear"]]
    return finish(rig), rear


# ------------------------------------------------- hand Katyusha, pass 2
# PASS 2 (sheet 2026-10-13_2243; D48: "algo pobre y deforme", redone as pass
# 3 below). Kept only so the pass-3 sheet can show it, as GZDoom showed it
# and composited; nothing is written from it. Its renderers carry _box_ /
# HKB_ names; the public names (HK_POSES, render_katyusha_frame, ...) are
# pass 3's. PASS 2: a CLOSED LAUNCH BOX, after the portable salvo launchers (six tubes
# in an olive case, fired from the shoulder). Seen from behind, the weapon's
# face is the box's rear end with the six tube mouths in two rows of three,
# and a rocket's tail in each: a dark nozzle in the middle and the X of its
# fins, so the salvo counts as six at 1x. Three variants of the same idea:
#   A  closed box, the mouths flush with its rear face
#   B  six tubes in the open, held by three clamp bands (a pod, no case)
#   C  the box, with the six tube ends standing proud of it at both ends
# u from the rear of the tubes, v up, w left; all in cm.
HKB_LEN = 50.0                  # the box
HKB_PITCH = 5.2                 # tube centre to centre
HKB_TUBE_R = 2.3                # tube, outer
HKB_BORE_R = 1.8                # tube, inner
HKB_CASE = 0.6                  # case wall beyond the outer tubes
HKB_COLS = (-1.0, 0.0, 1.0)     # x pitch, w
HKB_ROWS = (-0.5, 0.5)          # x pitch, v
HKB_HW = HKB_PITCH + HKB_TUBE_R + HKB_CASE              # half width of the case
HKB_HH = HKB_PITCH / 2 + HKB_TUBE_R + HKB_CASE          # half height
HKB_BAND = 0.35                 # how far a reinforcing band stands off the case
HKB_BANDS = ((1.2, 3.0), (HKB_LEN - 3.0, HKB_LEN - 1.2))
HKB_PACK_BANDS = ((2.5, 5.5), (HKB_LEN / 2 - 1.5, HKB_LEN / 2 + 1.5), (HKB_LEN - 5.5, HKB_LEN - 2.5))
HKB_PROUD = (2.6, 2.0)          # variant C: tube ends out of the case, rear and front
HKB_RECESS = 1.3                # how deep a rocket's tail sits in its tube
HKB_NOZZLE = 0.42               # nozzle radius, as a share of the bore
HKB_RING = 0.74                 # the red base ring of a loaded rocket, same share
HKB_FIN_W = 0.45                # a fin seen end on, cm
HKB_LIFT = HKB_TUBE_R           # cm: a mouth's layers drawn this much nearer the eye
HKB_THROAT = 4.0                # cm: how deep the dark throat of an empty tube starts
HKB_NOSE = 2.4                  # a rocket's red nose out of the front mouth (pickup)
HKB_GRIP_U, HKB_HANDLE_U = 9.0, 31.0
HKB_SIGHT_U = (6.0, 24.0)       # the folding frame sight's two posts, on top left
HKB_STAR_U = 30.0               # the red star stencilled on the left side
HKB_STAR_R = 3.4
HKB_DISC_N = 28                 # vertices of a mouth's circle
HKB_EPS = 0.02                  # cm: layers of a mouth, drawn just nearer the eye


@dataclass(frozen=True)
class HKVariant:
    key: str
    kind: str               # "box" | "pack" | "proud"
    title: str


HK_VARIANTS = (
    HKVariant("A", "box", "Closed box, mouths flush"),
    HKVariant("B", "pack", "Six tubes, three clamp bands"),
    HKVariant("C", "proud", "Box, tube ends standing proud"),
)
HK_VARIANT = {v.key: v for v in HK_VARIANTS}
RECOMMENDED_HK = "A"


def hkb_tubes():
    return [(r * HKB_PITCH, c * HKB_PITCH) for r in HKB_ROWS for c in HKB_COLS]


def hkb_circle(at, u, v, w, r, n: int = HKB_DISC_N):
    """The 3D points of a circle across the bore at (u, v, w)."""
    return [at(u, v + r * np.cos(2 * np.pi * k / n), w + r * np.sin(2 * np.pi * k / n)) for k in range(n)]


def hkb_layer(rig: Rig, clip2, poly2, depth: float, val: float, material: str) -> None:
    """Paint screen polygon poly2, clipped to the screen polygon clip2, at a
    fixed depth: what is seen INSIDE a tube mouth (the tail, the nozzle, the
    fins, or the far end of an empty tube) is clipped by the mouth's rim."""
    xs, ys = [p[0] for p in clip2], [p[1] for p in clip2]
    win = rig._window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)
    if win is None:
        return
    sl, X, Y, origin = win
    inside = rig._poly_mask(clip2, X, origin) & rig._poly_mask(poly2, X, origin)
    rig._commit(sl, inside, np.full(X.shape, depth), np.full(X.shape, val), MAT_ID[material])


def hkb_mouth(rig: Rig, at, u: float, v: float, w: float, loaded: bool) -> None:
    """One tube's rear mouth: the steel rim, the bore's shadow and either a
    rocket's tail (a red base ring round a dark nozzle, crossed by the X of
    four fins) or, empty, the lit inner wall round a dark throat. Every
    layer is lifted HKB_LIFT towards the eye: a tube end seen end on is a
    capsule whose bulge would otherwise cover the mouth, and the lift also
    outlines each mouth (the contour pass)."""
    proj = lambda pts: [rig.project(p)[:2] for p in pts]
    z0 = float(at(u, v, w)[2]) - HKB_LIFT
    rim = proj(hkb_circle(at, u, v, w, HKB_TUBE_R))
    hkb_layer(rig, rim, rim, z0, 0.62, "steel")
    bore = proj(hkb_circle(at, u, v, w, HKB_BORE_R))
    hkb_layer(rig, bore, bore, z0 - HKB_EPS, 0.10, "gunmetal")
    if loaded:
        layers = ((HKB_BORE_R - 0.12, 0.40, "steel"), (HKB_BORE_R * HKB_RING, 0.62, "hull_red"),
                  (HKB_BORE_R * HKB_NOZZLE, 0.05, "rubber"))
        for k, (r, val, mat) in enumerate(layers):
            disc = proj(hkb_circle(at, u + HKB_RECESS, v, w, r))
            hkb_layer(rig, bore, disc, z0 - (2 + k) * HKB_EPS, val, mat)
        for a in (45.0, 135.0):             # the four fins, end on: an X
            ca, sa = np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))
            d = np.array([ca, sa]) * (HKB_BORE_R - 0.1)
            n = np.array([-sa, ca]) * HKB_FIN_W / 2
            q = [(d + n), (d - n), (-d - n), (-d + n)]
            fin = proj([at(u + HKB_RECESS, v + y, w + x) for x, y in q])
            hkb_layer(rig, bore, fin, z0 - 6 * HKB_EPS, 0.66, "steel")
        noz = proj(hkb_circle(at, u + HKB_RECESS, v, w, HKB_BORE_R * HKB_NOZZLE * 0.6))
        hkb_layer(rig, bore, noz, z0 - 7 * HKB_EPS, 0.0, "rubber")
    else:
        # empty: the tube's inner wall catches the light as a crescent round
        # the dark throat, which is the same bore a few cm deeper (seen from
        # off the axis, the far end of a 50 cm tube is never in view)
        hkb_layer(rig, bore, bore, z0 - 2 * HKB_EPS, 0.30, "gunmetal")
        throat = proj(hkb_circle(at, u + HKB_THROAT, v, w, HKB_BORE_R))
        hkb_layer(rig, bore, throat, z0 - 3 * HKB_EPS, 0.06, "gunmetal")


def hkb_box(rig: Rig, at, U, W, u0: float, u1: float, hw: float, hh: float, material: str = "olive_paint",
            base: float = 0.52) -> None:
    """A closed rectangular solid from u0 to u1 (the U-W rectangle extruded
    along V, both ways)."""
    rig.plate(at(0.0, 0.0, 0.0), U, W, ((u0, -hw), (u1, -hw), (u1, hw), (u0, hw)), 2 * hh, material, base, 0.8)


def hkb_star(rig: Rig, at, u: float, w: float, r: float) -> None:
    """The red star stencilled on the case's left side."""
    pts = []
    for i in range(10):
        ang = np.deg2rad(90.0 + i * 36.0)
        rr = r if i % 2 == 0 else r * 0.40
        pts.append(at(u + rr * np.cos(ang), rr * np.sin(ang), w))
    rig._plane(pts, "hull_red", 0.62, 0.6)


def draw_launch_box(rig: Rig, origin, bore, up, variant: HKVariant, loaded: bool = True, grip: bool = True,
                    handle: bool = True, noses: bool = False) -> dict:
    """The pass-2 Katyusha in its own frame. grip=False folds the pistol grip
    away and lays the sight flat; handle=False folds the forward handle (the
    pickups: at most ONE thing hangs under the box, so it cannot stand on
    legs like pass 1's 'bench'); noses=True shows the six red noses out of
    the front mouths (the pickup, seen from the front)."""
    U, V, W, at = gun_basis(origin, bore, up)
    tubes = hkb_tubes()
    kind = variant.kind
    rear_u, front_u = (-HKB_PROUD[0], HKB_LEN + HKB_PROUD[1]) if kind == "proud" else (0.0, HKB_LEN)
    if kind == "pack":
        hw, hh = HKB_HW - HKB_CASE + 0.3, HKB_HH - HKB_CASE + 0.3
        for v, w in tubes:
            rig.capsule(at(0.0, v, w), at(HKB_LEN, v, w), HKB_TUBE_R, HKB_TUBE_R, "olive_paint", 0.52, 0.8,
                        open_ends=True)
        for b0, b1 in HKB_PACK_BANDS:
            hkb_box(rig, at, U, W, b0, b1, hw, hh, "olive_paint", 0.44)
    else:
        hw, hh = HKB_HW, HKB_HH
        hkb_box(rig, at, U, W, 0.0, HKB_LEN, hw, hh)
        for b0, b1 in HKB_BANDS:
            hkb_box(rig, at, U, W, b0, b1, hw + HKB_BAND, hh + HKB_BAND, "olive_paint", 0.46)
        if kind == "proud":
            for v, w in tubes:
                rig.capsule(at(rear_u, v, w), at(0.2, v, w), HKB_TUBE_R, HKB_TUBE_R, "steel", 0.42, 0.85,
                            open_ends=True)
                rig.capsule(at(HKB_LEN - 0.2, v, w), at(front_u, v, w), HKB_TUBE_R, HKB_TUBE_R, "steel", 0.42,
                            0.85, open_ends=True)
        for side in (1.0, -1.0):                        # a star on each side of the case
            hkb_star(rig, at, HKB_STAR_U, side * (hw + 0.03), HKB_STAR_R)
    for v, w in tubes:
        hkb_mouth(rig, at, rear_u - HKB_EPS, v, w, loaded)
    if noses:
        for v, w in tubes:
            rig.capsule(at(front_u - 0.5, v, w), at(front_u + HKB_NOSE, v, w), HKB_BORE_R, HKB_BORE_R * 0.3,
                        "hull_red", 0.6, 0.8)
    # the folding frame sight: two posts on the top left, a ring on the front one
    sw = hw - 1.6
    for su, hgt in zip(HKB_SIGHT_U, (2.2, 3.4)):
        if grip:
            rig.plate(at(su, hh, sw), U, V, ((-0.4, 0.0), (0.4, 0.0), (0.3, hgt), (-0.3, hgt)), 0.4,
                      "gunmetal", 0.42, 0.8)
        else:       # folded flat on the lid
            rig.plate(at(su, hh + 0.2, sw), U, W, ((-0.4, -0.5), (hgt, -0.5), (hgt, 0.5), (-0.4, 0.5)), 0.3,
                      "gunmetal", 0.42, 0.8)
    if grip:
        rig.capsule(at(HKB_SIGHT_U[1], hh + 3.4, sw), at(HKB_SIGHT_U[1], hh + 3.4, sw), 0.9, 0.9,
                    "gunmetal", 0.45, 0.8)
        rig.plate(at(HKB_GRIP_U, -hh - 0.2), U, V, ((-1.6, 0.4), (2.0, 0.4), (0.8, -9.0), (-2.6, -8.6)), 2.6,
                  "bakelite", 0.5, 0.8)
        guard_loop(rig, at, ((HKB_GRIP_U + 1.6, -hh - 1.0), (HKB_GRIP_U + 2.4, -hh - 3.4),
                             (HKB_GRIP_U + 6.0, -hh - 3.0), (HKB_GRIP_U + 6.6, -hh - 0.6)))
    if handle:
        rig.capsule(at(HKB_HANDLE_U, -hh - 0.2, 2.0), at(HKB_HANDLE_U + 0.8, -hh - 9.0, 2.6), 1.3, 1.2,
                    "bakelite", 0.5, 0.8)
    rear = [at(rear_u, v, w) for v, w in tubes]
    return {"at": at, "U": U, "V": V, "W": W, "rear": rear, "bottom": -hh}


# Off the eye's axis, to the right and below: a box that crossed the axis
# would run to the vanishing point and sit on the crosshair (HK_AIM_CLEAR).
HKB_POSES = (
    ArmsPose("A", "ready, six loaded", (11.5, 8.0, 32.0), (0.02, 0.0, 1.0), (0.06, -1.0, 0.0)),
    ArmsPose("B", "salvo: box up, tubes empty", (11.5, 7.2, 31.0), (0.03, -0.05, 1.0), (0.06, -1.0, 0.0),
             state="empty"),
    ArmsPose("C", "wind-up, box up, loaded", (11.5, 7.2, 31.0), (0.03, -0.05, 1.0), (0.06, -1.0, 0.0),
             wired=False),
)
HK_AIM_CLEAR = (16, 0.15)       # px round the crosshair, and the most of that disc a held frame may cover
# the elbows are pass 1's HK_RIGHT_ELBOW / HK_LEFT_ELBOW, unchanged


def render_katyusha_box_frame(style: HandStyle, pose: ArmsPose, variant: str = RECOMMENDED_HK) -> tuple[Frame, list]:
    """Pass 2: a held frame of the launch box and the screen positions (x, y, px
    per cm) of the six tube mouths, where the flash's motors light."""
    rig = Rig()
    got = draw_launch_box(rig, pose.origin, pose.bore, pose.up, HK_VARIANT[variant], loaded=pose.state != "empty")
    at, U, V = got["at"], got["U"], got["V"]
    b = got["bottom"]
    draw_grip(rig, style, at(HKB_GRIP_U - 0.8, b - 5.0), unit(V + U * 0.16), HK_RIGHT_ELBOW, 1.6, trigger=True)
    draw_grip(rig, style, at(HKB_HANDLE_U + 0.4, b - 5.0, 2.3), unit(V - U * 0.08), HK_LEFT_ELBOW, 1.3,
              side="left")
    rear = [rig.project(p) for p in got["rear"]]
    return finish(rig), rear


# ------------------------------------------------- hand Katyusha, pass 3
# PASS 3 (D48: the CEO found pass 2 "algo pobre y deforme": in the engine
# the box was a flat olive board with six circles and a hand beside it).
# Pass 3 turns the weapon side-on, as Blood holds its heavy weapons: carried
# low at the right hip, the bore running in to the left so the eye sees its
# LEFT SIDE AND TOP along its whole length, the near (rear) end big at the
# bottom right and the six warheads at the far end, under the crosshair;
# both hands on it. The salvo is six rockets in two rows of three, the
# BM-13's own arrangement on the rails (one rocket riding over each rail,
# one slung under it), so katyusha.zs's six projectiles stay true. Three
# variants of the carrier, sharing the frame, grips, sling and ignition box:
#   A  open rails: six steel rockets on three I-section rails, two riveted
#      frame rings; the rockets are seen whole, fins to warheads
#   B  six bare launch tubes in three riveted bands, warheads out of the
#      front mouths
#   C  the riveted launch box (pass 2's idea) turned side-on
# u from the rear end, v up, w left (gun_basis); all in cm.
HK3_R = 2.3                     # rocket body radius (46 mm: a hand rocket, not the BM-13's 132)
HK3_PITCH_W = 6.2               # column pitch, w
HK3_ROW_V = 3.9                 # rocket centre above / below the rail's axis
HK3_COLS = (1.0, 0.0, -1.0)     # x pitch: left (towards the eye), middle, right
HK3_ROWS = (1.0, -1.0)          # over the rail, slung under it
HK3_ROCKET_U = 2.0              # where a loaded rocket's tail sits on the rails
HK3_BODY = 36.0                 # body length, tail to the red band
HK3_BAND = 1.6                  # the red band at the warhead's base: LOADED reads by it
HK3_WAR = 11.0                  # the ogive warhead
HK3_WAR_K = 1.2                 # warhead radius over body radius (exaggerated, as the PG-7V is)
HK3_FUSE = 1.6
HK3_FIN = (5.0, 0.85, 1.7)      # fin length along u, inner and outer radius (in rocket radii)
HK3_FIN_W = 0.28
HK3_FLANGE = (1.3, 0.5)         # rail flange half width, thickness
HK3_WEB = (0.6, 1.4)            # rail web thickness, half height
HK3_FRAMES = ((7.0, 9.6), (30.5, 33.1))  # u of the rear and front frame rings (variant A)
HK3_BANDS = ((5.0, 7.8), (20.0, 22.8))   # variant B: the third band sits HK3_BAND_FRONT from the mouths
HK3_BAND_FRONT = (6.0, 3.2)
HK3_FRAME_T = 0.7               # ring bar thickness
HK3_RIVET_R = 0.36
HK3_GRIP_U, HK3_HANDLE_U = 20.0, 35.0
HK3_IGN = (3.0, 12.5, -3.6, 2.6, 2.6)    # ignition box: u from, u to, v from, v to, thickness
HK3_STAR_R = 2.4
HK3_SLING_W = 2.4               # strap width
HK3_SLING_TO = (36.0, 46.0, 14.0)        # camera cm, off the bottom right: where the strap goes (the shoulder)
HK3_SIDE = 1.0                  # the side that faces the eye: +w, the left (the bore runs in to the left)
HK3_TUBE = (0.4, 0.1)           # variant B/C: tube outer and bore radius over the rocket's
HK3_BOX_PAD = 1.15              # variant C: case wall beyond the outer rockets


@dataclass(frozen=True)
class HK3Variant:
    key: str
    kind: str               # "rails" | "tubes" | "box"
    length: float           # rails, tubes or case, from u = 0
    title: str


HK3_VARIANTS = (
    HK3Variant("A", "rails", 37.6, "Open rails, rockets over and under"),
    HK3Variant("B", "tubes", 41.0, "Six bare tubes in riveted bands"),
    HK3Variant("C", "box", 41.0, "The riveted launch box, side-on"),
)
HK3_VARIANT = {v.key: v for v in HK3_VARIANTS}
RECOMMENDED_HK3 = "A"


def hk3_slots():
    """(v, w) of the six rockets: the top row first, left to right."""
    return [(r * HK3_ROW_V, c * HK3_PITCH_W) for r in HK3_ROWS for c in HK3_COLS]


def hk3_half(kind: str) -> tuple[float, float]:
    """Half width and half height of the outline (frame ring, band or case)."""
    pad = HK3_BOX_PAD if kind == "box" else (0.55 if kind == "rails" else 0.75 + HK3_TUBE[0])
    return HK3_PITCH_W + HK3_R + pad, HK3_ROW_V + HK3_R + pad


def hk3_rivet(rig: Rig, p, n, r: float = HK3_RIVET_R, base: float = 0.62) -> None:
    """A round rivet head on a surface of normal n."""
    n = unit(n)
    a = perp(np.array([0.3, 1.0, 0.2]), n)
    b = np.cross(n, a)
    rig.ellipsoid(np.asarray(p, np.float64) + n * r * 0.25, (a * r, b * r, n * r * 0.6), "steel", base, 0.8)


def hk3_rocket(rig: Rig, at, u0: float, v: float, w: float, body: bool = True) -> None:
    """One rocket from its tail at u0: nozzle, four fins, steel body (or,
    body=False, only what shows out of a tube: the band and the warhead),
    the red band, the olive ogive and the fuse."""
    r = HK3_R
    rw = r * HK3_WAR_K
    ub = u0 + HK3_BODY
    if body:
        rig.capsule(at(u0 - 0.7, v, w), at(u0 + 0.4, v, w), r * 0.55, r * 0.8, "rubber", 0.2, 0.6, open_ends=True)
        rig.capsule(at(u0 + 0.3, v, w), at(ub, v, w), r, r, "steel", 0.46, 0.85, open_ends=True,
                    bands=(HK3_BODY / 3, 0.3, 0.14))
        L, ri, ro = HK3_FIN
        U = unit(at(1.0) - at(0.0))
        for a in (45.0, 135.0, 225.0, 315.0):
            D = unit(at(0.0, np.sin(np.deg2rad(a)), np.cos(np.deg2rad(a))) - at(0.0))
            rig.plate(at(u0, v, w), U, D, ((0.0, r * ri), (L, r * ri), (L - 1.2, r * ro), (0.0, r * ro)),
                      HK3_FIN_W, "steel", 0.52, 0.8)
    rig.capsule(at(ub - 0.6, v, w), at(ub, v, w), r, rw, "steel", 0.5, 0.85, open_ends=True)
    rig.capsule(at(ub - 0.05, v, w), at(ub + HK3_BAND, v, w), rw * 1.02, rw * 1.02, "hull_red", 0.6, 0.8,
                open_ends=True)
    uw = ub + HK3_BAND
    rig.capsule(at(uw - 0.1, v, w), at(uw + HK3_WAR * 0.4, v, w), rw, rw * 0.88, "olive_paint", 0.58, 0.8,
                open_ends=True)
    rig.capsule(at(uw + HK3_WAR * 0.4 - 0.1, v, w), at(uw + HK3_WAR, v, w), rw * 0.88, rw * 0.28,
                "olive_paint", 0.62, 0.8)
    rig.capsule(at(uw + HK3_WAR - 0.5, v, w), at(uw + HK3_WAR + HK3_FUSE, v, w), rw * 0.3, rw * 0.2,
                "steel", 0.62, 0.85)


def hk3_ring(rig: Rig, at, U, V, W, u0: float, u1: float, hw: float, hh: float, t: float,
             base: float = 0.5) -> None:
    """A rectangular ring of flat olive bars round the bundle (a frame or a
    clamp band), from u0 to u1, outer half sizes hw, hh, bars t thick, with
    a row of rivets on the side that faces the eye and along the top."""
    du = u1 - u0
    for sv in (1.0, -1.0):
        rig.plate(at(u0, sv * (hh - t / 2), 0.0), U, W, ((0.0, -hw), (du, -hw), (du, hw), (0.0, hw)), t,
                  "olive_paint", base + 0.04 * sv, 0.8)
    for sw in (1.0, -1.0):
        rig.plate(at(u0, 0.0, sw * (hw - t / 2)), U, V, ((0.0, -hh), (du, -hh), (du, hh), (0.0, hh)), t,
                  "olive_paint", base, 0.8)
    um = u0 + du / 2
    for vv in np.linspace(-hh + 1.2, hh - 1.2, 4):
        hk3_rivet(rig, at(um, vv, HK3_SIDE * hw), W * HK3_SIDE)
    for ww in np.linspace(-hw + 1.2, hw - 1.2, 5):
        hk3_rivet(rig, at(um, hh, ww), V)


def hk3_strap(rig: Rig, pts, face, width: float, base: float = 0.46) -> None:
    """A flat leather strap through 3D points, its face turned to `face`
    (walnut-brown: the glove's material stays the hands' own)."""
    pts = [np.asarray(p, np.float64) for p in pts]
    for a, b in zip(pts, pts[1:]):
        t = unit(b - a)
        n = perp(np.cross(t, face), t) * width / 2
        rig._plane([a - n, b - n, b + n, a + n], "wood_walnut", base, 0.8)


def hk3_mouth(rig: Rig, at, u: float, v: float, w: float) -> None:
    """An EMPTY tube's front mouth: the steel lip, the bore's shadow and the
    dark throat. Only for empty tubes: its layers lie at one depth, and on a
    loaded tube, seen side-on, they would hide the warhead's red band."""
    proj = lambda pts: [rig.project(p)[:2] for p in pts]
    ro, ri = HK3_R + HK3_TUBE[0] + 0.3, HK3_R + HK3_TUBE[1]
    z0 = float(at(u, v, w)[2])
    rim = proj(hkb_circle(at, u, v, w, ro))
    hkb_layer(rig, rim, rim, z0, 0.66, "steel")
    bore = proj(hkb_circle(at, u, v, w, ri))
    hkb_layer(rig, bore, bore, z0 - HKB_EPS, 0.14, "gunmetal")
    throat = proj(hkb_circle(at, u - 3.5, v, w, ri))
    hkb_layer(rig, bore, throat, z0 - 2 * HKB_EPS, 0.03, "gunmetal")


def draw_katyusha3(rig: Rig, origin, bore, up, variant: HK3Variant, loaded: bool = True, grip: bool = True,
                   handle: bool = True, sling_to=HK3_SLING_TO) -> dict:
    """The pass-3 Katyusha in its own frame. grip / handle False fold the
    pistol grip and the forward handle (the pickup lies on neither, so it
    cannot stand on two legs like pass 1's 'bench'); sling_to is the point
    (camera cm) the strap runs to from the rear swivel, or None."""
    U, V, W, at = gun_basis(origin, bore, up)
    kind, L = variant.kind, variant.length
    hw, hh = hk3_half(kind)
    S = HK3_SIDE
    slots = hk3_slots()
    if kind == "rails":
        f0, f1 = HK3_FLANGE
        wt, wh = HK3_WEB
        for w in [c * HK3_PITCH_W for c in HK3_COLS]:
            for sv in (1.0, -1.0):
                rig.plate(at(0.0, sv * (wh + f1 / 2), w), U, W, ((0.0, -f0), (L, -f0), (L, f0), (0.0, f0)), f1,
                          "gunmetal", 0.46, 0.85)
            rig.plate(at(0.0, 0.0, w), U, V, ((0.0, -wh), (L, -wh), (L, wh), (0.0, wh)), wt, "gunmetal", 0.26, 0.85)
        for u0, u1 in HK3_FRAMES:
            hk3_ring(rig, at, U, V, W, u0, u1, hw, hh, HK3_FRAME_T)
            rig.plate(at(u0, 0.0, 0.0), U, W, ((0.0, -hw), (u1 - u0, -hw), (u1 - u0, hw), (0.0, hw)), 0.9,
                      "olive_paint", 0.44, 0.8)            # the cross bar the rails hang from
        if loaded:
            for v, w in slots:
                hk3_rocket(rig, at, HK3_ROCKET_U, v, w)
    else:
        if kind == "tubes":
            ro = HK3_R + HK3_TUBE[0]
            for v, w in slots:
                rig.capsule(at(0.0, v, w), at(L, v, w), ro, ro, "gunmetal", 0.5, 0.85, open_ends=True,
                            bands=(L / 4, 0.3, 0.12))
                rig.capsule(at(-0.2, v, w), at(1.0, v, w), ro + 0.3, ro + 0.3, "steel", 0.46, 0.85, open_ends=True)
                rig.capsule(at(L - 1.0, v, w), at(L, v, w), ro + 0.3, ro + 0.3, "steel", 0.52, 0.85, open_ends=True)
            for u0, u1 in (*HK3_BANDS, (L - HK3_BAND_FRONT[0], L - HK3_BAND_FRONT[1])):
                hk3_ring(rig, at, U, V, W, u0, u1, hw, hh, HK3_FRAME_T + 0.2, 0.48)
        else:
            hkb_box(rig, at, U, W, 0.0, L, hw, hh, "olive_paint", 0.5)
            for b0, b1 in ((4.0, 6.0), (L - 3.0, L - 1.0)):
                hkb_box(rig, at, U, W, b0, b1, hw + 0.35, hh + 0.35, "olive_paint", 0.44)
            for uu in np.arange(8.5, L - 3.0, 4.0):        # rivet lines along the edges that face the eye
                hk3_rivet(rig, at(uu, hh, S * (hw - 0.8)), V)
                hk3_rivet(rig, at(uu, hh - 0.8, S * hw), W * S)
                hk3_rivet(rig, at(uu, -hh + 0.8, S * hw), W * S)
            hkb_star(rig, at, L * 0.52, S * (hw + 0.03), 3.2)
        for v, w in slots:
            if not loaded:
                hk3_mouth(rig, at, L + HKB_EPS, v, w)
            else:
                hk3_rocket(rig, at, L - HK3_BODY + 0.4, v, w, body=False)
    # the ignition box with its star, on the side that faces the eye (the
    # box variant carries its star on the case)
    if kind != "box":
        i0, i1, j0, j1, bt = HK3_IGN
        rig.plate(at(0.0, 0.0, S * (hw + bt / 2)), U, V, ((i0, j0), (i1, j0), (i1, j1), (i0, j1)), bt,
                  "olive_paint", 0.52, 0.8)
        hkb_star(rig, at, (i0 + i1) / 2, S * (hw + bt + 0.03), HK3_STAR_R)
        for uu in (i0 + 0.8, i1 - 0.8):
            for vv in (j0 + 0.7, j1 - 0.7):
                hk3_rivet(rig, at(uu, vv, S * (hw + bt)), W * S, 0.3)
    # the frame sight: a post and a ring on the front, a notch at the rear
    fu = HK3_FRAMES[1][0] + 1.0 if kind == "rails" else L - 4.5
    if grip:
        rig.plate(at(fu, hh, 0.0), U, V, ((-0.4, 0.0), (0.4, 0.0), (0.3, 2.2), (-0.3, 2.2)), 0.5,
                  "gunmetal", 0.42, 0.8)
        c = at(fu, hh + 3.6, 0.0)
        ring = [c + 1.5 * (np.cos(a) * V + np.sin(a) * W) for a in np.linspace(0, 2 * np.pi, 13)]
        for a, b in zip(ring, ring[1:]):
            rig.capsule(a, b, 0.28, 0.28, "gunmetal", 0.45, 0.8)
    gu = HK3_GRIP_U
    if grip:
        rig.plate(at(gu - 3.5, -hh - 0.4, 0.0), U, V, ((0.0, 0.4), (6.5, 0.4), (6.5, -1.2), (0.0, -1.2)), 2.2,
                  "gunmetal", 0.38, 0.85)                  # the grip's bracket
        rig.plate(at(gu, -hh - 1.2), U, V, ((-1.6, 0.4), (2.0, 0.4), (0.8, -9.0), (-2.6, -8.6)), 2.6,
                  "bakelite", 0.5, 0.8)
        guard_loop(rig, at, ((gu + 1.6, -hh - 2.0), (gu + 2.4, -hh - 4.4), (gu + 6.0, -hh - 4.0),
                             (gu + 6.6, -hh - 1.4)))
        rig.capsule(at(gu + 3.2, -hh - 1.6), at(gu + 2.8, -hh - 3.4), 0.35, 0.3, "gunmetal", 0.45, 0.8)
        if kind != "box":                                   # the firing cable, grip to ignition box
            i0, i1, j0, _, bt = HK3_IGN
            cab = bezier(at(gu - 1.6, -hh - 2.0, S * 1.0), at(gu - 3.0, -hh - 3.0, S * hw),
                         at(i1 + 1.5, j0 - 2.5, S * (hw + bt + 0.8)), at(i1 - 1.0, j0 + 0.8, S * (hw + bt)), 8)
            for a, b in zip(cab, cab[1:]):
                rig.capsule(a, b, 0.32, 0.32, "rubber", 0.3, 0.7)
    if handle:
        hu = HK3_HANDLE_U
        rig.plate(at(hu - 1.5, -hh - 0.4, 0.0), U, V, ((0.0, 0.4), (4.0, 0.4), (4.0, -1.2), (0.0, -1.2)), 2.0,
                  "gunmetal", 0.38, 0.85)
        rig.capsule(at(hu, -hh - 1.0), at(hu + 0.6, -hh - 8.0), 1.35, 1.25, "wood_birch", 0.55, 0.8,
                    bands=(2.2, 0.3, 0.10))
    # the sling: a leather strap from the rear swivel to the shoulder
    a = at(2.0, -hh + 0.4, S * (hw + 0.3))
    rig.capsule(a - V * 0.9, a + V * 0.9, 0.35, 0.35, "steel", 0.55, 0.85)          # swivel
    b = at(HK3_FRAMES[1][1] + 2.0 if kind == "rails" else L - 1.0, -hh + 0.4, S * (hw + 0.3))
    rig.capsule(b - V * 0.9, b + V * 0.9, 0.35, 0.35, "steel", 0.55, 0.85)          # front swivel, strap off
    if sling_to is not None:
        end = np.asarray(sling_to, np.float64)
        pts = bezier(a, a - V * 6.0 + W * S * 1.0, end - (end - a) * 0.35 - V * 3.0, end, 10)
        hk3_strap(rig, pts, W * S, HK3_SLING_W)
        t = unit(pts[3] - pts[1])
        rig.plate(pts[2] + W * S * 0.25, t, perp(-V, t), ((-0.8, -1.5), (0.8, -1.5), (0.8, 1.5), (-0.8, 1.5)),
                  0.4, "steel", 0.52, 0.85)                # the buckle
    front_u = HK3_ROCKET_U + HK3_BODY if kind == "rails" else L
    return {"at": at, "U": U, "V": V, "W": W, "hw": hw, "hh": hh,
            "front": [at(front_u + HK3_BAND + HK3_WAR * 0.5, v, w) for v, w in slots], "rear": at(-1.0)}


# Carried low at the right hip, Blood's way, the bore running in to the left
# and the top rolled towards the eye so the top row of rockets shows. B is
# the salvo with Blood's exaggerated kick (the muzzle thrown up, the launcher
# pushed back); C and D are PROPOSALS for a fuller animation (the wind-up
# before the launch, and the way back down from the kick).
HK_POSES = (
    ArmsPose("A", "ready, six loaded", (37.0, 11.5, 33.0), (-1.0, -0.02, 0.8), (0.25, -1.0, -0.45)),
    ArmsPose("B", "salvo: the kick, empty", (39.5, 11.0, 30.0), (-1.0, -0.33, 0.8), (0.32, -1.0, -0.4),
             state="empty"),
    ArmsPose("C", "wind-up, loaded", (41.0, 12.2, 32.5), (-1.0, -0.12, 0.8), (0.27, -1.0, -0.45),
             wired=False),
    ArmsPose("D", "recovery, empty", (37.5, 11.8, 33.0), (-1.0, -0.11, 0.8), (0.28, -1.0, -0.45),
             state="empty", wired=False),
)
HK3_RIGHT_ELBOW = (24.0, 44.0, 6.0)
HK3_LEFT_ELBOW = (-16.0, 44.0, 24.0)


def render_katyusha_frame(style: HandStyle, pose: ArmsPose, variant: str = RECOMMENDED_HK3,
                          hands: bool = True) -> tuple[Frame, dict]:
    """A held frame and its anchors, screen (x, y, px per cm): the six
    warheads ("front", where the flash shows the motors leaving), the rear
    end ("rear", the backblast) and where each hand closes ("grips": the
    pistol grip and the forward handle). hands=False draws the launcher
    alone, for the hands being redrawn after Blood (D49)."""
    rig = Rig()
    got = draw_katyusha3(rig, pose.origin, pose.bore, pose.up, HK3_VARIANT[variant], loaded=pose.state != "empty")
    at, U, V, hh = got["at"], got["U"], got["V"], got["hh"]
    right_at, left_at = at(HK3_GRIP_U - 0.8, -hh - 6.2), at(HK3_HANDLE_U + 0.4, -hh - 4.8)
    if hands:
        draw_grip(rig, style, right_at, unit(V + U * 0.16), HK3_RIGHT_ELBOW, 1.6, trigger=True)
        draw_grip(rig, style, left_at, unit(V - U * 0.09), HK3_LEFT_ELBOW, 1.35, side="left")
    return finish(rig), {"front": [rig.project(p) for p in got["front"]], "rear": rig.project(got["rear"]),
                         "grips": {"right": rig.project(right_at), "left": rig.project(left_at)}}


HK_FLASH_ON = {"A": "B", "B": "B"}
HK3_FLASH_MOTOR = 2.3           # a motor's burst, in rocket radii: six stars, not one ball
HK3_FLASH_BLAST = 5.0           # the backblast at the rear end, cm
HK3_FLASH_SMOKE = (1.2, 1.8)    # smoke puff size in rocket radii, frames A and B


def render_katyusha_flash(which: str, anchors: dict) -> Frame:
    """SDHF A: the six motors burning just off the rails' fronts, and the
    backblast out of the rear end, low on the right (Blood's grammar: the
    shot is loud on screen); B: their smoke, an ember in each."""
    rig = Rig()
    rx, ry, rs = anchors["rear"]
    if which == "A":
        smoke_puffs(rig, rx, ry, HK3_FLASH_BLAST * rs * 0.8, 4, 90, 0.5)
        rig.burst(rx, ry, HK3_FLASH_BLAST * rs, 12.0, "flame_red", 9, 0.5)
        muzzle_burst(rig, rx, ry, HK3_FLASH_BLAST * rs * 0.7, 3.0)
    else:
        smoke_puffs(rig, rx, ry - HK3_FLASH_BLAST * rs * 0.4, HK3_FLASH_BLAST * rs, 5, 91, 0.35)
    for i, (x, y, s) in enumerate(anchors["front"]):
        r = HK3_R * s
        if which == "A":
            smoke_puffs(rig, x, y, r * HK3_FLASH_SMOKE[0], 2, 92 + i, 0.5)
            muzzle_burst(rig, x, y, r * HK3_FLASH_MOTOR, 7.0 * i)
        else:
            smoke_puffs(rig, x, y - r * 0.6, r * HK3_FLASH_SMOKE[1], 3, 98 + i, 0.4)
            rig.burst(x, y, r * 0.6, 9.0 * i, "ember", 6, 0.5)
    return finish(rig)


HK3_PICKUP_PX_PER_CM = 1.2      # 52 cm of launcher -> ~64 px (Freedoom's BFUGA0 is about 62 wide)
HK3_PICKUP_TURN = (0.93, 0.36)  # the bore on the floor: (right, towards the eye) parts
HK3_PICKUP_ROLL = -40.0         # degrees: dropped onto its right side, the pistol grip turned to the eye
HK3_PICKUP_TILT = 8.0           # degrees, nose down: it rests on the grip and the warheads


def render_katyusha_pickup(variant: str = RECOMMENDED_HK3) -> Frame:
    """SDHP: the launcher where it was dropped, loaded, the warheads to the
    right and turned a little towards the eye, rolled HK3_PICKUP_ROLL onto
    its right side and tilted onto its nose. The forward handle is folded,
    so it rests on ONE grip and the warheads, never on two legs (pass 1
    read as a bench); the pistol grip and its guard are what say WEAPON at
    1x rather than a crate of rockets (Doom's box of rockets is exactly
    that shape)."""
    rig = gun_pickup_rig(HK3_PICKUP_PX_PER_CM, PICKUP_W, 56)
    right, away, up = floor_basis()
    U = unit(right * HK3_PICKUP_TURN[0] - away * HK3_PICKUP_TURN[1])
    t = np.deg2rad(HK3_PICKUP_ROLL)
    side = unit(np.cross(U, up))                 # the launcher's left at rest
    roll_up = unit(up * np.cos(t) + side * np.sin(t))
    k = np.deg2rad(HK3_PICKUP_TILT)
    U, roll_up = unit(U * np.cos(k) - up * np.sin(k)), perp(roll_up, unit(U * np.cos(k) - up * np.sin(k)))
    v = HK3_VARIANT[variant]
    draw_katyusha3(rig, np.array([0.0, 0.0, PICKUP_DIST]) - U * 26.0, U, roll_up, v, handle=False, sling_to=None)
    return finish(rig, hud=False)



# ----------------------------------------- hand Katyusha: the in-game check
# The pass-3 sheet judges the frames on the MAP01 view the engine itself
# drew (QA's draft-overlay captures of 2026-10-13 23:10, GZDoom g4.14.2):
# several screenshots from one standing point, each with a different weapon
# up, so per pixel the colour most of them agree on is the room without a
# weapon. Comparison only: nothing of it enters a sprite.
HK3_ENGINE_SHOTS = (
    ("docs/qa/evidence/2026-10-13_2310_F4_draft-overlay-roks-katyusha.png", 2, (0, 2)),
    ("docs/qa/evidence/2026-10-13_2310_F4_draft-overlay-in-map01.png", 2, (0, 1, 2, 3, 4, 5)),
)                               # (capture, tiles per row, tiles taken: one per weapon, all the same view)
HK3_ENGINE_TILE = (480, 300)    # px of one tile: the 320x200 weapon space at 1.5x
HK3_ENGINE_AGREE = 6            # RGB distance under which two tiles agree on a pixel
HK3_ENGINE_PASS2_TILE = (0, 2)  # (capture, tile) of pass 2's SDHKA0 as GZDoom drew it
HK3_ENGINE_BAR_TOP = 186        # y in the 320x200 space where GZDoom's status bar starts at this size


def hk3_engine_tiles(shot: int) -> list | None:
    rel, cols, keep = HK3_ENGINE_SHOTS[shot]
    path = PROJECT_ROOT / rel
    if not path.is_file():
        return None
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB"))
    tw, th = HK3_ENGINE_TILE
    return [a[(i // cols) * th:(i // cols + 1) * th, (i % cols) * tw:(i % cols + 1) * tw] for i in keep]


def hk3_engine_backdrop() -> np.ndarray | None:
    """MAP01 without a weapon, 320x200, from the engine captures (None if
    they are missing): per pixel, the tile most other tiles agree with."""
    tiles = []
    for shot in range(len(HK3_ENGINE_SHOTS)):
        got = hk3_engine_tiles(shot)
        if got is None:
            return None
        tiles += got
    st = np.stack(tiles).astype(np.int16)
    support = np.zeros(st.shape[:3], np.int16)
    for i in range(len(tiles)):
        for j in range(len(tiles)):
            support[i] += (np.abs(st[i] - st[j]).max(-1) <= HK3_ENGINE_AGREE)
    pick = support.argmax(0)
    bg = np.take_along_axis(st, pick[None, ..., None].repeat(3, -1), 0)[0].astype(np.uint8)
    return np.asarray(Image.fromarray(bg).resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS))


def hk3_engine_view(frames, bg: np.ndarray | None) -> np.ndarray:
    """Frames over the MAP01 engine view, under GZDoom's own status bar."""
    if bg is None:
        return on_screen(frames)
    scr = on_screen(frames, backdrop=bg, statusbar_line=False)
    scr[HK3_ENGINE_BAR_TOP:] = bg[HK3_ENGINE_BAR_TOP:]
    return scr


def hk3_engine_pass2() -> np.ndarray | None:
    """Pass 2's SDHKA0 exactly as GZDoom showed it (the 2310 capture)."""
    shot, tile = HK3_ENGINE_PASS2_TILE
    got = hk3_engine_tiles(shot)
    if got is None:
        return None
    return np.asarray(Image.fromarray(got[HK3_ENGINE_SHOTS[shot][2].index(tile)]).resize(
        (SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS))


# ------------------------------------------------------------------ flashes
def muzzle_burst(rig: Rig, mx: float, my: float, size: float, rot: float) -> None:
    rig.burst(mx, my, size, rot, "flash_out")
    rig.burst(mx, my, size * 0.62, rot + 22.5, "flash_in")
    rig.burst(mx, my, size * 0.25, 0.0, "flash_core", 6, 0.8)


def smoke_puffs(rig: Rig, mx: float, my: float, size: float, n: int, seed: int, value: float = 0.45) -> None:
    rng = np.random.RandomState(seed)
    for _ in range(n):
        dx, dy = rng.uniform(-1.0, 1.0) * size, rng.uniform(-1.2, 0.3) * size
        rig.burst(mx + dx, my + dy, size * rng.uniform(0.45, 0.8), rng.uniform(0, 45), "smoke", 7, 0.7,
                  value=value + rng.uniform(-0.12, 0.12))


TT_FLASH_ON = {"A": "B"}                # flash letter -> held frame it shows over
TT_FLASH_SIZE = 10.0


def render_tt33_flash(which: str, muzzle_xy) -> Frame:
    rig = Rig()
    mx, my = muzzle_xy
    muzzle_burst(rig, mx, my, TT_FLASH_SIZE, 9.0)
    return finish(rig)


IZH_FLASH_ON = {"A": "A", "B": "A"}
IZH_FLASH_SIZE = {"A": 19.0, "B": 13.0}


def render_izh_flash(which: str, muzzle_xy) -> Frame:
    """Both barrels' muzzles are a few px apart at that distance: one burst
    covers either barrel, which is all the state machine can tell apart."""
    rig = Rig()
    mx, my = muzzle_xy
    size = IZH_FLASH_SIZE[which]
    if which == "B":
        smoke_puffs(rig, mx, my - 4, 6.0, 4, 31)
    muzzle_burst(rig, mx, my, size, 4.0 if which == "A" else 27.0)
    return finish(rig)


RPG_FLASH_ON = {"A": "B", "B": "B", "C": "B", "D": "B"}


def render_rpg7_flash(which: str, muzzle_xy) -> Frame:
    """MISF's four frames: the blast, then the smoke the grenade leaves."""
    rig = Rig()
    mx, my = muzzle_xy
    if which == "A":
        muzzle_burst(rig, mx, my, 24.0, 6.0)
    elif which == "B":
        smoke_puffs(rig, mx, my - 2, 9.0, 6, 51, 0.5)
        muzzle_burst(rig, mx, my, 15.0, 24.0)
    elif which == "C":
        smoke_puffs(rig, mx, my - 6, 12.0, 8, 52, 0.4)
        rig.burst(mx, my, 7.0, 12.0, "flame_red", 6, 0.5)
        rig.burst(mx, my, 4.0, 40.0, "flash_out", 5, 0.5)
    else:
        smoke_puffs(rig, mx, my - 10, 15.0, 9, 53, 0.3)
    return finish(rig)


ROKS_FLASH_ON = {"A": "A", "B": "A"}
ROKS_JET_CM = 400.0                     # how far down the jet the flash is drawn
ROKS_JET_STEPS = 18


def render_roks3_flash(which: str, nozzle_cam, U_cam) -> Frame:
    """SDKF: the burning jet from the nozzle into the room. Built in 3D: a
    chain of bursts along the bore, each growing as the jet spreads and
    shrinking with distance, rising a little as it goes."""
    rig = Rig()
    rng = np.random.RandomState(61 if which == "A" else 62)
    n = np.asarray(nozzle_cam, np.float64)
    U = unit(U_cam)
    pts = []
    for i in range(ROKS_JET_STEPS):
        d = 2.0 + ROKS_JET_CM * (i / (ROKS_JET_STEPS - 1)) ** 1.4
        p = n + U * d + np.array([0.0, -0.035 * d, 0.0]) + rng.uniform(-1, 1, 3) * 0.04 * d
        x, y, s = rig.project(p)
        r_cm = 0.8 + 0.12 * d
        pts.append((x, y, r_cm * s, d))
    for x, y, rpx, d in reversed(pts):          # far first: the near flame sits on top
        rot = rng.uniform(0, 45)
        rig.burst(x, y, rpx * 1.15, rot, "flame_red", 7, 0.55)
        rig.burst(x, y, rpx * 0.8, rot + 20, "flash_out", 7, 0.5)
        if d < ROKS_JET_CM * 0.6:
            rig.burst(x, y, rpx * 0.45, rot + 10, "flash_in", 6, 0.6)
    x, y, rpx, _ = pts[0]
    rig.burst(x, y, max(3.0, rpx * 0.5), 0.0, "flash_core", 6, 0.8)
    return finish(rig)


HKB_FLASH_ON = {"A": "B", "B": "B"}
HK_FLASH_BURST = 1.25           # a motor's burst, in bore radii: six stars, not one ball
HK_FLASH_SMOKE = (1.0, 1.4)     # smoke puff size in bore radii, frames A and B


def render_katyusha_box_flash(which: str, rear_xy) -> Frame:
    """Pass 2's SDHF A: the six motors lighting in the six tube mouths (the backblast
    comes out of the rear, towards the eye); B: their smoke, a red ember
    still in each mouth."""
    rig = Rig()
    for i, (x, y, s) in enumerate(rear_xy):
        r = HKB_BORE_R * s
        if which == "A":
            smoke_puffs(rig, x, y, r * HK_FLASH_SMOKE[0], 2, 70 + i, 0.5)
            muzzle_burst(rig, x, y, r * HK_FLASH_BURST, 7.0 * i)
        else:
            smoke_puffs(rig, x, y - r * 0.6, r * HK_FLASH_SMOKE[1], 3, 80 + i, 0.35)
            rig.burst(x, y, r * 0.7, 9.0 * i, "flame_red", 6, 0.5)
    return finish(rig)


# ------------------------------------------------------------------ pickups
def gun_pickup_rig(px_per_cm: float, w: int = PICKUP_W, h: int = PICKUP_H) -> Rig:
    return Rig(0, 0, w, h, ss=4, focal=px_per_cm * PICKUP_DIST, centre=(w / 2, h / 2))


# px per cm, chosen so each pickup is the size of the Freedoom one it
# replaces (measured on freedoom2.wad 0.13.0, the size in the comment)
TT_PICKUP_PX_PER_CM = 1.15      # 20 cm -> ~23 px  (PISTA0)
IZH_PICKUP_PX_PER_CM = 0.55     # 113 cm -> ~62 px (SHOTA0)
RPG_PICKUP_PX_PER_CM = 0.46     # 136 cm -> ~62 px (LAUNA0)
ROKS_PICKUP_PX_PER_CM = 0.62    # gun and tank -> ~56 px (PLASA0)
HK_PICKUP_PX_PER_CM = 1.25      # 44 cm battery -> ~60 px (BFUGA0)


def render_tt33_pickup() -> Frame:
    rig = gun_pickup_rig(TT_PICKUP_PX_PER_CM)
    right, away, up = floor_basis()
    draw_tt33(rig, np.array([0.0, 0.0, PICKUP_DIST]) + right * 8.0 + up * 5.0, -right, up)
    return finish(rig, hud=False)


def render_izh_pickup() -> Frame:
    rig = gun_pickup_rig(IZH_PICKUP_PX_PER_CM)
    right, away, up = floor_basis()
    draw_izh(rig, np.array([0.0, 0.0, PICKUP_DIST]) + right * 16.0 + up * 3.0, -right, up, hud=False)
    return finish(rig, hud=False)


def render_rpg7_pickup() -> Frame:
    rig = gun_pickup_rig(RPG_PICKUP_PX_PER_CM)
    right, away, up = floor_basis()
    draw_rpg7(rig, np.array([0.0, 0.0, PICKUP_DIST]) + right * 66.0 + up * 4.0, -right, up, hud=False, k=1.15)
    return finish(rig, hud=False)


def render_roks3_pickup() -> Frame:
    """The gun, its hose and the cylindrical tank behind it: the tank is
    what says flamethrower from across a room."""
    rig = gun_pickup_rig(ROKS_PICKUP_PX_PER_CM)
    right, away, up = floor_basis()
    c = np.array([0.0, 0.0, PICKUP_DIST])
    tank0 = c + away * 18.0 + right * 22.0 + up * 9.0
    rig.capsule(tank0, tank0 - right * 40.0, 9.0, 9.0, "olive_paint", 0.5, 0.8)
    rig.capsule(tank0 - right * 40.0, tank0 - right * 43.0, 3.0, 2.0, "steel", 0.5, 0.85)
    draw_roks3(rig, c + right * 14.0 + up * 3.0 - away * 6.0, -right, up, hud=False,
               hose_end=tank0 - right * 40.0)
    return finish(rig, hud=False)


def render_katyusha_rails_pickup() -> Frame:
    """Pass 1's pickup (the 'bench'), for the comparison on the sheet."""
    rig = gun_pickup_rig(HK_PICKUP_PX_PER_CM, PICKUP_W, 56)
    right, away, up = floor_basis()
    U = unit(-right * 0.85 + away * 0.55)
    draw_katyusha(rig, np.array([0.0, 0.0, PICKUP_DIST]) - U * (HK_LEN / 2) + up * 10.0, U, up)
    return finish(rig, hud=False)


HK_PICKUP_TURN = (0.90, 0.44)   # the box's bore on the floor: (right, towards the eye) parts
HK_PICKUP_OPTIONS = (
    PickupOption("D", "Dropped: grip down, nose on the floor"),
    PickupOption("F", "Flat: grip folded"),
)
RECOMMENDED_HK_PICKUP = "D"
HK_DROP_TILT = 12.0             # degrees, nose down: the box rests on its grip and its front edge


def render_katyusha_box_pickup(variant: str = RECOMMENDED_HK, option: str = RECOMMENDED_HK_PICKUP) -> Frame:
    """Pass 2: the launch box on the floor, its front end turned towards the
    eye so the six red noses show in their mouths. D, dropped: the pistol
    grip down and the box tilted onto its nose, the way a launcher lies
    where it fell; one grip, not two legs (pass 1's 'bench'). F, flat: grip
    and sight folded, nothing under it. Placed by its lowest pixel (finish),
    so only the orientation matters here."""
    rig = gun_pickup_rig(HK_PICKUP_PX_PER_CM, PICKUP_W, 56)
    right, away, up = floor_basis()
    U = unit(right * HK_PICKUP_TURN[0] - away * HK_PICKUP_TURN[1])
    if option == "D":
        t = np.deg2rad(HK_DROP_TILT)
        U = unit(U * np.cos(t) - up * np.sin(t))
    v = HK_VARIANT[variant]
    draw_launch_box(rig, np.array([0.0, 0.0, PICKUP_DIST]) - U * (HKB_LEN / 2), U, up, v, grip=option == "D",
                    handle=False, noses=True)
    return finish(rig, hud=False)


# ------------------------------------------------------------------ specs
@dataclass(frozen=True)
class WeaponSpec:
    key: str                # the CLI name and the work/ folder
    title: str
    slot: int
    zs: str                 # src/zscript/weapons/<zs>
    held: str               # final names, MOD-SPEC 6.3
    flash: str
    pickup: str
    ph_held: str            # the Freedoom placeholder the .zs names today
    ph_flash: str
    ph_pickup: str
    reserved: str           # MOD-SPEC's held range, for the sheet
    slug: str
    pickup_wall: str
    pickup_light: int


WEAPONS = {
    "tt33": WeaponSpec("tt33", "SLOT 2: THE TT-33 TOKAREV", 2, "tokarev.zs", TT_SPRITE, TT_FLASH, TT_PICKUP,
                       "PISG", "PISF", "PIST", "A-E", "tt33", "SDCONC1", 144),
    "izh": WeaponSpec("izh", "SLOT 3: THE IZH-58", 3, "izh.zs", IZH_SPRITE, IZH_FLASH, IZH_PICKUP,
                      "SHTG", "SHTF", "SHOT", "A-F", "izh58", "SDLOCK1", 144),
    "rpg7": WeaponSpec("rpg7", "SLOT 5: THE RPG-7", 5, "rpg7.zs", RPG_SPRITE, RPG_FLASH, RPG_PICKUP,
                       "MISG", "MISF", "LAUN", "A-B", "rpg7", "SDSTEL1", 176),
    "roks3": WeaponSpec("roks3", "SLOT 6: THE ROKS-3 FLAMETHROWER", 6, "roks3.zs", ROKS_SPRITE, ROKS_FLASH,
                        ROKS_PICKUP, "PLSG", "PLSF", "PLAS", "A-B", "roks3", "SDSTEL1", 176),
    "katyusha": WeaponSpec("katyusha", "SLOT 7: THE HAND KATYUSHA", 7, "katyusha.zs", HK_SPRITE, HK_FLASH,
                           HK_PICKUP, "BFGG", "BFGF", "BFUG", "A-C", "hand-katyusha", "SDSTEL1", 176),
}
WEAPON_POSES = {"tt33": TT_POSES, "izh": IZH_POSES, "rpg7": RPG_POSES, "roks3": ROKS_POSES, "katyusha": HK_POSES}
FLASH_ON = {"tt33": TT_FLASH_ON, "izh": IZH_FLASH_ON, "rpg7": RPG_FLASH_ON, "roks3": ROKS_FLASH_ON,
            "katyusha": HK_FLASH_ON}
PICKUP_RENDER = {"tt33": render_tt33_pickup, "izh": render_izh_pickup, "rpg7": render_rpg7_pickup,
                 "roks3": render_roks3_pickup, "katyusha": render_katyusha_pickup}


def render_weapon(key: str, style: HandStyle) -> tuple[dict, dict, Frame]:
    """Every held frame, every flash frame and the pickup of one weapon:
    ({letter: Frame}, {letter: Frame}, pickup)."""
    poses = WEAPON_POSES[key]
    held, anchor = {}, {}
    for pose in poses:
        if key == "tt33":
            held[pose.frame], anchor[pose.frame] = render_tt33_frame(style, pose)
        elif key == "izh":
            held[pose.frame], anchor[pose.frame] = render_izh_frame(style, pose)
        elif key == "rpg7":
            held[pose.frame], anchor[pose.frame] = render_rpg7_frame(style, pose)
        elif key == "roks3":
            held[pose.frame], anchor[pose.frame] = render_roks3_frame(style, pose)
        else:
            held[pose.frame], anchor[pose.frame] = render_katyusha_frame(style, pose)
    flashes = {}
    for letter, on in FLASH_ON[key].items():
        if key == "tt33":
            flashes[letter] = render_tt33_flash(letter, anchor[on])
        elif key == "izh":
            flashes[letter] = render_izh_flash(letter, anchor[on])
        elif key == "rpg7":
            flashes[letter] = render_rpg7_flash(letter, anchor[on])
        elif key == "roks3":
            pose = next(p for p in poses if p.frame == on)
            U, V, W, at = gun_basis(pose.origin, pose.bore, pose.up)
            flashes[letter] = render_roks3_flash(letter, at(ROKS_NOZZLE[1] + 0.4), U)
        else:
            flashes[letter] = render_katyusha_flash(letter, anchor[on])
    return held, flashes, PICKUP_RENDER[key]()


def zs_letters(spec: WeaponSpec) -> tuple[set, set]:
    """The frame letters the weapon's state machine names for its held and
    flash placeholders (read from src/zscript/weapons/, never edited), or
    for our own names once installed (N17: the TT-33's PISG/PISF are
    SDTT/SDTF since 2026-10-15; the letters did not change)."""
    text = (PROJECT_ROOT / "src" / "zscript" / "weapons" / spec.zs).read_text(encoding="utf-8")
    out = []
    for sprites in ((spec.ph_held, spec.held), (spec.ph_flash, spec.flash)):
        letters = set()
        for sprite in sprites:
            for m in re.finditer(rf"^\s*{sprite}\s+([A-Z]+)\s", text, re.M):
                letters |= set(m.group(1))
        out.append(letters)
    return out[0], out[1]


def sprite_name(name: str, letter: str, wired: bool = True) -> str:
    return f"{name}{letter}0" if wired else f"{name}{letter}0_proposed"


WEAPON_TEXT = {
    "tt33": {
        "recommend": "AS DRAWN, WITH THE HAND THE CEO PICKS.",
        "intro": "The TT-33 in the right hand alone, as Doom holds its pistol, seen from behind and a little to "
                 "the right so the slab side of the slide, the rear serrations, the cocked hammer and the "
                 "bakelite grip with its star medallion show. Three frames, as tokarev.zs plays them: A at rest, "
                 "B the shot (the slide thrown back over the barrel, the muzzle up), C the top of the kick with "
                 "the slide home; then B again on the way down.",
        "verdict": [
            "WHY AS DRAWN. One hand, centred-right, the muzzle a little under the crosshair: the TT reads by its "
            "slab slide and the rake of the grip, and both stay on screen through the kick.",
            "WEAKNESSES. The serrations and the medallion are one or two pixels at 1x; at that size the star is a "
            "dot, not a star. The pistol is small, so the glove is half the sprite. MOD-SPEC reserves SDTT A-E; "
            "the state machine shows A-C only, so D and E are not drawn. Positions NOT VERIFIED in GZDoom "
            "(engine pass owed, D26).",
        ],
    },
    "izh": {
        "recommend": "AS DRAWN, A-D; E-F ONLY IF THE CEO WANTS A FULLER RELOAD (A STATE EDIT).",
        "intro": "The IZh-58 side-by-side in both hands, the two barrels running in to the crosshair. izh.zs "
                 "shares frames between the shot and the reload, so each frame has to work in both: Fire "
                 "plays A (flash) B C A, Reload plays D C B A. A rest; B the kick, which on the way back "
                 "up from the reload reads as raising the gun; C the gun low and shut, which after D reads "
                 "as the snap closed; D broken open on its hinge, the left chamber loaded and the right "
                 "shell going in.",
        "verdict": [
            "WHY AS DRAWN. Two barrels side by side are the IZh's face. Doom II's super shotgun is a double "
            "too, but the mod removes it (editor number 82 maps to None), so the shape is ours. The barrels are "
            "drawn 1.6 times fatter than life so the pair reads at 1x, as Doom exaggerates its own weapons. "
            "D is the only open frame because the state machine has one; it is the "
            "frame that sells the reload, so it is the most detailed: breech towards the eye, brass heads, "
            "a red hull half in.",
            "WEAKNESSES. With B and C shared, the reload is open, shut, up: there is no frame of the barrels "
            "swinging home. MOD-SPEC reserves SDIZ A-F; E (barrels half closed) and F (shell ejected) would "
            "give a proper break-open, at the price of a Reload edit by the mod-engineer (D E F C B A). Not "
            "drawn until asked. One flash covers both barrels: at the muzzle they are a few px apart. Positions NOT "
            "VERIFIED in GZDoom (engine pass owed, D26).",
        ],
    },
    "rpg7": {
        "recommend": "A-B AS DRAWN; THE RELOAD C-D IF THE CEO WANTS ONE (MOD-SPEC AND A STATE EDIT).",
        "intro": "The RPG-7 on the right shoulder, the tube running in from the bottom right to just under the "
                 "crosshair, the PG-7V's olive cone sitting out of the muzzle. rpg7.zs plays A at rest and B "
                 "for the whole 26-tic shot (the grenade gone, the tube kicked), with MISF's four flash frames "
                 "over B: the blast, then smoke. It has NO reload state: the loaded A simply comes back. C "
                 "and D are drawn as a PROPOSAL for that reload.",
        "verdict": [
            "WHY AS DRAWN. The warhead's cone is the RPG-7's whole silhouette, so A shows it exaggerated (x1.5, as "
            "Doom exaggerates) and B shows the empty muzzle: the player sees the round leave.",
            "PROPOSAL, NOT WIRED: SDRLC0_proposed (the left hand brings up a new round) and SDRLD0_proposed "
            "(the round seated, the hand pushing it home). Using them needs MOD-SPEC 6.3 to reserve SDRL A-D "
            "and the mod-engineer to add them to Fire (for example B 8, C 8, D 6 inside today's 26 tics). "
            "Until then they are files in work/ and nothing else.",
            "WEAKNESSES. Even at x1.5 the warhead is small at rest (about 15 px across), smaller than the round "
            "in the reload frames. The tube runs past the eye, so the pistol grip, the right hand and the birch "
            "heat guard are behind it and never on screen; the left hand only shows its knuckles at the bottom "
            "right. No PGO-7 optic: the eye would be at it, so it is left off. Positions NOT VERIFIED in GZDoom "
            "(engine pass owed, D26).",
        ],
    },
    "roks3": {
        "recommend": "AS DRAWN, WITH THE HAND THE CEO PICKS.",
        "intro": "The ROKS-3 gun at the hip like the PPSh: birch stock, the valve body, the fuel tube and the "
                 "drum of igniter cartridges round the nozzle; the hose runs down to the tank on the back, out of view in "
                 "first person and shown on the pickup. "
                 "roks3.zs: A at rest and, Bright, while the jet runs (3 tics a jet); B for 20 tics when the "
                 "trigger is let go; the flash is SDKF A, the burning jet. B of the flash is drawn as a spare "
                 "with a different flicker, unused today.",
        "verdict": [
            "WHY AS DRAWN. The igniter drum at the muzzle says flamethrower before it fires; the jet is drawn in "
            "3D along the bore, so it grows as it goes into the room where the projectile goes. The pickup adds "
            "the tank and hose, which is what says flamethrower from across a room.",
            "WEAKNESSES. Held at the hip, the bore points away from the eye, so the jet foreshortens into a "
            "ball of fire about 45 px long rather than a long tongue across the screen. It is a cluster of stars, "
            "Doom's flash grammar, not a fluid. The flash covers part of the gun while it fires, as Doom's plasma does. "
            "SDKF B is unused until the mod-engineer alternates the flash. Positions NOT VERIFIED in GZDoom "
            "(engine pass owed, D26).",
        ],
    },
    "katyusha": {
        "recommend": "VARIANT A (OPEN RAILS) AS DRAWN, ITS PICKUP; C AND D IF THE MOD-ENGINEER TAKES THE FIRE EDIT. "
                     "THE HANDS FOLLOW D49.",
        "intro": "THIRD PASS (D48: the CEO found pass 2 \"algo pobre y deforme\"; in GZDoom the launch box was a "
                 "flat olive board with six circles and a hand beside it). Pass 3 turns the weapon SIDE-ON and "
                 "carries it as Blood carries its heavy weapons (D49): low at the right hip, both hands on it, the "
                 "bore running in to the left and the top rolled towards the eye, so the eye gets its length, its "
                 "top and its left side instead of a rear face. The salvo is six rockets in two rows of three, "
                 "the BM-13's own arrangement (one rocket riding over each rail, one slung under it), so "
                 "katyusha.zs's six projectiles stay true. Material: steel rockets with a hard highlight, a red "
                 "band and an olive ogive warhead each, riveted olive frame rings, an ignition box with the red "
                 "star and its firing cable, a birch forward handle, the bakelite pistol grip and a leather sling "
                 "running back to the shoulder. Three variants of the carrier: A open rails (the rockets seen "
                 "whole), B six bare tubes in riveted bands, C pass 2's launch box turned side-on.",
        "verdict": [
            "WHY A. It is the only one of the three in which the rockets are seen: fins, steel body, red band, "
            "warhead, six times, which is what 'Katyusha' means and what makes the salvo count as rockets "
            "rather than as holes. Side-on it has volume (top, side and front read as three planes), and the "
            "detail the CEO asked for sits where the eye is: rivets on the rings, the starred ignition box, the "
            "cable, the sling. B and C are seen from behind their front face, so only the tips of the "
            "warheads stick out past it. B reads at 1x as a heavier, industrial pod, but only those tips say "
            "rockets. "
            "C is the cleanest outline and the largest plain olive area of the three: the risk of pass 2's "
            "'pobre' again, so it is offered for comparison, not recommended.",
            "BLOOD (D49). Held low, both hands on it, and the shot is loud: SDHK B throws the muzzle up about "
            "13 degrees and the launcher back towards the eye, with six motor bursts at the warheads and "
            "the backblast out of the rear end. Two PROPOSED frames make the Fire a six-frame animation: "
            "SDHK C (raised to fire, still loaded) and SDHK D (coming down, empty). Wiring them is the "
            "mod-engineer's state edit and needs MOD-SPEC 6.3 to reserve SDHK D (it reserves A-C today); same "
            "60 tics as now: SDHK A 20 (charge sound) · SDHK C 10 · SDHK B 0 A_GunFlash · SDHK B 10 "
            "A_SD_FireKatyusha · SDHK B 10 · SDHK D 10 A_ReFire. The rockets then leave on the tic the flash "
            "shows, which also cures pass 1's weakness (today B, empty, shows for 10 tics before the launch).",
            "THE PICKUP. Dropped where it fell: on its right side, nose down, resting on the warheads and ONE "
            "pistol grip (the forward handle folds: pass 1 stood on two and read as a bench). The grip and its "
            "guard are what say WEAPON at 1x, the red bands and warheads say rockets; 65 px wide, Freedoom's "
            "BFUGA0 is about 62.",
            "THE IN-GAME CHECK. Section 1 puts every pass on MAP01 as GZDoom drew it, at the size the game "
            "shows it; the first two views are pass 2's SDHKA0 as the engine showed it and the same sprite "
            "composited here, so the composite can be trusted to place the frames where the engine does "
            "(NOT VERIFIED for pass 3 until its own engine pass, owed, D26).",
            "WEAKNESSES. The hands are the 3D placeholder of hand E: D49 is redrawing them after Blood, so the "
            "launcher is also delivered without hands (launcher_only/, with the screen position of each grip "
            "in metrics.json). At rest the bottom row of rockets hides under the top one: the six read by "
            "their warheads, not by their bodies. The warheads of frame A cover 9 percent of the 16 px round "
            "the crosshair, all in its lower half (the nearest pixel is 11 px under it; pass 2 covered up to 12 "
            "percent); the proposed C, raised to fire, covers 21 percent and comes to 7 px of it. In B the rear end and most "
            "of the backblast are off the 4:3 screen (they show on widescreen). The MAP01 backdrop keeps a few "
            "ghost pixels of the captured weapons low on the right, under where the launcher sits.",
        ],
    },
}


def build_weapon(key: str, stamp: str, hand: str = RECOMMENDED_HAND, out_dir: Path = OUT_DIR,
                 preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    if key == "katyusha":           # pass 2 has its own sheet: variants, pass 1, proposals
        return build_katyusha(stamp, hand, out_dir, preview_dir)
    spec, style = WEAPONS[key], HAND[hand]
    poses = WEAPON_POSES[key]
    wdir = out_dir / key
    held, flashes, pickup = render_weapon(key, style)
    metrics = {}
    for pose in poses:
        name = sprite_name(spec.held, pose.frame, pose.wired)
        save_sprite(held[pose.frame], wdir / f"{name}.png")
        metrics[name] = {"pose": pose.name, "wired": pose.wired, "size": list(held[pose.frame].rgba.shape[1::-1]),
                         "offsets": [int(v) for v in held[pose.frame].offsets()]}
    for letter, f in flashes.items():
        name = sprite_name(spec.flash, letter)
        save_sprite(f, wdir / f"{name}.png")
        metrics[name] = {"over": f"{spec.held}{FLASH_ON[key][letter]}0", "size": list(f.rgba.shape[1::-1]),
                         "offsets": [int(v) for v in f.offsets()]}
    pname = f"{spec.pickup}A0"
    save_sprite(pickup, wdir / f"{pname}.png")
    metrics[pname] = {"pickup": True, "size": list(pickup.rgba.shape[1::-1]),
                      "offsets": [int(v) for v in pickup.offsets()]}
    zs_held, zs_flash = zs_letters(spec)
    metrics["_state_machine"] = {"file": f"src/zscript/weapons/{spec.zs}", "held_placeholder": spec.ph_held,
                                 "held_letters": "".join(sorted(zs_held)), "flash_placeholder": spec.ph_flash,
                                 "flash_letters": "".join(sorted(zs_flash)), "hand": hand}
    (wdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    text = WEAPON_TEXT[key]
    S = Sheet(2000, f"SOVIET DOOM  ·  F4  ·  {spec.title}  ·  FIRST PERSON, FLASH AND PICKUP", stamp)
    S.para(text["intro"])
    S.para(f"HAND STYLE {hand} OF THE HAND SWEEP (ANY LETTER RE-RENDERS: GEN_WEAPON.PY {key.upper()} --HAND X). "
           f"NAMES, MOD-SPEC 6.3: {spec.held} {spec.reserved} HELD, {spec.flash} FLASH, {spec.pickup} A PICKUP. "
           f"STATE MACHINE ({spec.zs}, READ, NOT EDITED): {spec.ph_held} {''.join(sorted(zs_held))} -> "
           f"{spec.held}, {spec.ph_flash} {''.join(sorted(zs_flash))} -> {spec.flash}, {spec.ph_pickup} A -> "
           f"{spec.pickup}. Built by tools/art/gen_weapon.py, palette v1 only, no system fonts. Draft, nothing "
           "in assets/.", S.dim)
    S.y += 6
    views = []
    for pose in poses:
        tag = f"{sprite_name(spec.held, pose.frame, pose.wired)}  ·  {pose.name.upper()}"
        views.append((tag, [held[pose.frame]], pose.wired))
    for letter, on in FLASH_ON[key].items():
        views.append((f"{spec.held}{on}0 + {spec.flash}{letter}0", [held[on], flashes[letter]], True))
    for i in range(0, len(views), 3):
        x, h_row = S.pad, 0
        for tag, fs, wired in views[i:i + 3]:
            S.label((x, S.y), tag, S.gold if wired else S.red)
            w2, h2 = S.paste(on_screen(fs), (x, S.y + S.T.line_h() + 4), 2)
            x += w2 + 16
            h_row = max(h_row, h2 + S.T.line_h() + 4)
        S.y += h_row + 14
    items = [f"{k} {m['size'][0]}X{m['size'][1]} GRAB {m['offsets'][0]},{m['offsets'][1]}"
             for k, m in metrics.items() if not k.startswith("_")]
    for i in range(0, len(items), 3):
        S.label((S.pad, S.y), "  ·  ".join(items[i:i + 3]))
        S.y += S.T.line_h()
    S.para("Each view is the whole 320x200 weapon space at 2x with the frame at rest (no bob); the dotted line "
           "is the top of the classic status bar. Red labels: proposed frames the state machine does not show.",
           S.dim)
    S.y += 8
    x = S.pad
    fd = [freedoom_sprite(f"{spec.ph_held}A0"), freedoom_sprite(f"{spec.ph_flash}A0")]
    if fd[0] is not None:
        today = f"TODAY: {spec.ph_held}A0 + {spec.ph_flash}A0, 1X"
        S.label((x, S.y), today, S.gold)
        S.paste(on_screen([f for f in fd if f is not None]), (x, S.y + S.T.line_h() + 4), 1)
        x += max(SCREEN_W, S.T.width(today)) + 40
    S.label((x, S.y), f"{pname} BEFORE {spec.pickup_wall}, LIGHT {spec.pickup_light}: 4X, 1X; "
            f"FREEDOOM {spec.ph_pickup}A0 BESIDE IT AT 1X", S.gold)
    sc = pickup_scene(pickup, spec.pickup_light, spec.pickup_wall)
    top = S.y + S.T.line_h() + 4
    w4, h4 = S.paste(sc, (x, top), 4)
    S.label((x + w4 + 12, top), "OURS")
    S.paste(sc, (x + w4 + 12, top + S.T.line_h() + 2), 1)
    ph = freedoom_sprite(f"{spec.ph_pickup}A0")
    if ph is not None:
        ph = Frame(ph.rgba, ph.mat, ph.rgba.shape[1] // 2, ph.rgba.shape[0], False)
        yy = top + S.T.line_h() + 2 + sc.shape[0] + 10
        S.label((x + w4 + 12, yy), f"TODAY: {spec.ph_pickup}A0")
        S.paste(pickup_scene(ph, spec.pickup_light, spec.pickup_wall), (x + w4 + 12, yy + S.T.line_h() + 2), 1)
    S.y = top + max(h4, SCREEN_H) + 18
    S.label((S.pad, S.y), f"RECOMMENDATION: {text['recommend']}", S.red)
    S.y += S.T.line_h() + 2
    for v in text["verdict"]:
        S.para(v)
    path = S.save(preview_dir / f"{stamp}_F4_{spec.slug}.png")
    return path, metrics


HK_PICKUP_CELL_K = 3            # zoom of a pickup cell on the Katyusha sheet
HK3_STRIP = ("A", "C", "B", "B", "D", "A")      # the proposed Fire, frame by frame
HK3_STRIP_FLASH = (None, None, "A", "B", None, None)


def build_katyusha(stamp: str, hand: str = RECOMMENDED_HAND, out_dir: Path = OUT_DIR,
                   preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    """The hand Katyusha's third pass: the three side-on variants judged at
    1x on the MAP01 view GZDoom drew, beside passes 1 and 2 (pass 2 also as
    the engine showed it); every frame of the recommended variant, the
    proposed animation, the pickups, and the launcher without hands. The
    lumps in work/art/weapons/katyusha/ are the recommended variant;
    variants/ holds B and C, launcher_only/ the frames without hands."""
    spec, style = WEAPONS["katyusha"], HAND[hand]
    wdir = out_dir / "katyusha"
    vdir, ldir = wdir / "variants", wdir / "launcher_only"
    held = {v.key: {p.frame: render_katyusha_frame(style, p, v.key) for p in HK_POSES} for v in HK3_VARIANTS}
    rec = held[RECOMMENDED_HK3]
    flashes = {k: render_katyusha_flash(k, rec[on][1]) for k, on in HK_FLASH_ON.items()}
    pickups = {v.key: render_katyusha_pickup(v.key) for v in HK3_VARIANTS}
    bare = {p.frame: render_katyusha_frame(style, p, RECOMMENDED_HK3, hands=False) for p in HK_POSES}
    metrics = {}

    def keep(f: Frame, path: Path, info: dict) -> None:
        save_sprite(f, path)
        key = path.stem if path.parent == wdir else f"{path.parent.name}/{path.stem}"
        metrics[key] = {**info, "size": list(f.rgba.shape[1::-1]), "offsets": [int(v) for v in f.offsets()]}

    rnd = lambda xy: [round(float(c), 1) for c in xy[:2]]
    for pose in HK_POSES:
        name = sprite_name(spec.held, pose.frame, pose.wired)
        keep(rec[pose.frame][0], wdir / f"{name}.png", {"pose": pose.name, "wired": pose.wired,
                                                         "variant": RECOMMENDED_HK3})
        for v in HK3_VARIANTS:
            if v.key != RECOMMENDED_HK3:
                keep(held[v.key][pose.frame][0], vdir / f"{name}_variant{v.key}.png",
                     {"pose": pose.name, "wired": False, "variant": v.key})
        f, anc = bare[pose.frame]
        keep(f, ldir / f"{name}_nohands.png", {"pose": pose.name, "variant": RECOMMENDED_HK3, "hands": False,
                                               "grip_right_xy": rnd(anc["grips"]["right"]),
                                               "grip_left_xy": rnd(anc["grips"]["left"])})
    for letter, f in flashes.items():
        keep(f, wdir / f"{sprite_name(spec.flash, letter)}.png", {"over": f"{spec.held}{HK_FLASH_ON[letter]}0"})
    pname = f"{spec.pickup}A0"
    for vk, f in pickups.items():
        path = wdir / f"{pname}.png" if vk == RECOMMENDED_HK3 else vdir / f"{pname}_variant{vk}.png"
        keep(f, path, {"pickup": True, "variant": vk})
    zs_held, zs_flash = zs_letters(spec)
    metrics["_state_machine"] = {"file": f"src/zscript/weapons/{spec.zs}", "held_placeholder": spec.ph_held,
                                 "held_letters": "".join(sorted(zs_held)), "flash_placeholder": spec.ph_flash,
                                 "flash_letters": "".join(sorted(zs_flash)), "hand": hand, "pass": 3,
                                 "variant": RECOMMENDED_HK3}
    (wdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    bg = hk3_engine_backdrop()
    view = lambda fs: hk3_engine_view(fs, bg)
    text = WEAPON_TEXT["katyusha"]
    S = Sheet(2000, f"SOVIET DOOM  ·  F4  ·  {spec.title}, PASS 3  ·  SIDE-ON, CARRIED THE BLOOD WAY", stamp)
    S.para(text["intro"])
    S.para(f"HAND STYLE {hand} (A PLACEHOLDER: THE HANDS ARE BEING REDRAWN AFTER BLOOD, D49). NAMES, MOD-SPEC 6.3: "
           f"{spec.held} {spec.reserved} HELD, {spec.flash} A-B FLASH, {spec.pickup} A PICKUP. STATE MACHINE "
           f"({spec.zs}, READ, NOT EDITED): {spec.ph_held} {''.join(sorted(zs_held))} -> {spec.held}, "
           f"{spec.ph_flash} {''.join(sorted(zs_flash))} -> {spec.flash}, {spec.ph_pickup} A -> {spec.pickup}. "
           "Built by tools/art/gen_weapon.py katyusha, palette v1 only, no system fonts. Draft, nothing in "
           "assets/. The room behind every view is MAP01 as GZDoom drew it (the 2310 draft-overlay captures, "
           "the weapon removed by taking, per pixel, what the captures agree on), under GZDoom's own status bar.",
           S.dim)
    S.y += 6

    def row(cells, k: int = 2, gap: int = 16) -> None:
        x, h_row = S.pad, 0
        for tag, colour, scr in cells:
            S.label((x, S.y), tag, colour)
            w2, h2 = S.paste(scr, (x, S.y + S.T.line_h() + 4), k)
            x += w2 + gap
            h_row = max(h_row, h2 + S.T.line_h() + 4)
        S.y += h_row + 14

    def heading(t: str) -> None:
        S.label((S.pad, S.y), t, S.gold)
        S.y += S.T.line_h() + 6

    old1 = render_katyusha_rails_frame(style, HK_RAILS_POSES[0])[0]
    old2 = render_katyusha_box_frame(style, HKB_POSES[0])[0]
    fd = freedoom_sprite(f"{spec.ph_held}A0")
    heading("1. IN THE GAME AT 1X: PASS 2 IN GZDOOM AND COMPOSITED HERE, PASS 1, TODAY; PASS 3 A-C")
    first = []
    eng = hk3_engine_pass2()
    if eng is not None:
        first.append(("PASS 2 IN GZDOOM", S.dim, eng))
    first += [("PASS 2 COMPOSITED", S.dim, view([old2])), ("PASS 1", S.dim, view([old1]))]
    if fd is not None:
        first.append((f"TODAY {spec.ph_held}A0", S.dim, view([fd])))
    row(first, 1, 10)
    row([(f"PASS 3 {v.key}" + ("  <<<" if v.key == RECOMMENDED_HK3 else ""),
          S.red if v.key == RECOMMENDED_HK3 else S.gold, view([held[v.key]["A"][0]])) for v in HK3_VARIANTS], 1, 10)
    row([(f"PASS 3 {v.key} SALVO", S.gold,
          view([held[v.key]["B"][0], render_katyusha_flash("A", held[v.key]["B"][1])])) for v in HK3_VARIANTS], 1, 10)
    heading("2. PASS 2 AGAINST PASS 3 (RECOMMENDED), 2X")
    row([("PASS 2 · THE LAUNCH BOX", S.dim, view([old2])),
         (f"PASS 3 {RECOMMENDED_HK3} · READY", S.red, view([rec["A"][0]])),
         (f"PASS 3 {RECOMMENDED_HK3} · SALVO", S.gold, view([rec["B"][0], flashes["A"]]))])
    heading("3. THE THREE VARIANTS, FRAME A, 2X")
    row([(f"{v.key} · {v.title.upper()}" + ("  <<<" if v.key == RECOMMENDED_HK3 else ""),
          S.red if v.key == RECOMMENDED_HK3 else S.gold, view([held[v.key]["A"][0]])) for v in HK3_VARIANTS])
    heading(f"4. VARIANT {RECOMMENDED_HK3}, EVERY FRAME, 2X (RED: PROPOSED, NOT WIRED)")
    tag = lambda p: f"{sprite_name(spec.held, p.frame, p.wired)}  ·  {p.name.upper()}"
    pose = {p.frame: p for p in HK_POSES}
    row([(tag(pose[k]), S.gold if pose[k].wired else S.red, view([rec[k][0]])) for k in "ACB"])
    row([(tag(pose["D"]), S.red, view([rec["D"][0]])),
         (f"{spec.held}B0 + {spec.flash}A0", S.gold, view([rec["B"][0], flashes["A"]])),
         (f"{spec.held}B0 + {spec.flash}B0", S.gold, view([rec["B"][0], flashes["B"]]))])
    items = [f"{k} {m['size'][0]}X{m['size'][1]} GRAB {m['offsets'][0]},{m['offsets'][1]}"
             for k, m in metrics.items() if not k.startswith(("_", "variants/", "launcher_only/"))]
    for i in range(0, len(items), 3):
        S.label((S.pad, S.y), "  ·  ".join(items[i:i + 3]))
        S.y += S.T.line_h()
    S.y += 8
    heading("5. THE PROPOSED FIRE, FRAME BY FRAME AT 1X: A (CHARGE) · C · B + FLASH A · B + FLASH B · D · A")
    strip = []
    for k, fl in zip(HK3_STRIP, HK3_STRIP_FLASH):
        strip.append((f"{spec.held}{k}" + (f" + {spec.flash}{fl}" if fl else ""),
                      S.gold if pose[k].wired else S.red, view([rec[k][0]] + ([flashes[fl]] if fl else []))))
    row(strip, 1, 6)
    heading(f"6. THE PICKUP ON SDFLR2 BEFORE {spec.pickup_wall}, LIGHT {spec.pickup_light}, {HK_PICKUP_CELL_K}X, "
            "THEN 1X BEFORE IT AND BEFORE SDCONC1 (LIGHT 160)")
    cells = [(f"{vk}" + ("  <<<" if vk == RECOMMENDED_HK3 else ""),
              S.red if vk == RECOMMENDED_HK3 else S.gold, f) for vk, f in pickups.items()]
    cells.append(("PASS 2 (D)", S.dim, render_katyusha_box_pickup()))
    cells.append(("PASS 1 (BENCH)", S.dim, render_katyusha_rails_pickup()))
    ph = freedoom_sprite(f"{spec.ph_pickup}A0")
    if ph is not None:
        cells.append((f"TODAY: {spec.ph_pickup}A0", S.dim, Frame(ph.rgba, ph.mat, ph.rgba.shape[1] // 2,
                                                                ph.rgba.shape[0], False)))
    cell_w = PICKUP_SCENE_W * HK_PICKUP_CELL_K + 18
    per_row = (S.width - 2 * S.pad + 18) // cell_w
    for i in range(0, len(cells), per_row):
        x, h_row = S.pad, 0
        for tg, colour, f in cells[i:i + per_row]:
            S.label((x, S.y), tg, colour)
            _, h3 = S.paste(pickup_scene(f, spec.pickup_light, spec.pickup_wall),
                            (x, S.y + S.T.line_h() + 4), HK_PICKUP_CELL_K)
            x += cell_w
            h_row = max(h_row, h3 + S.T.line_h() + 4)
        S.y += h_row + 14
    for j, (_, _, f) in enumerate(cells):
        x = S.pad + j * (PICKUP_SCENE_W + ONE_X_GAP)
        S.paste(pickup_scene(f, spec.pickup_light, spec.pickup_wall), (x, S.y), 1)
        S.paste(pickup_scene(f, 160, "SDCONC1"), (x, S.y + PICKUP_WALL_H + PICKUP_FLOOR_H + ONE_X_GAP), 1)
    S.y += 2 * (PICKUP_WALL_H + PICKUP_FLOOR_H) + ONE_X_GAP + 18
    heading(f"7. THE LAUNCHER WITHOUT HANDS, 1X (FOR THE HANDS OF D49: WORK/ART/WEAPONS/KATYUSHA/LAUNCHER_ONLY/, "
            "GRIP POSITIONS IN METRICS.JSON)")
    row([(sprite_name(spec.held, k, pose[k].wired), S.gold if pose[k].wired else S.red, view([bare[k][0]]))
         for k in "ACBD"], 1, 10)
    S.label((S.pad, S.y), f"RECOMMENDATION: {text['recommend']}", S.red)
    S.y += S.T.line_h() + 2
    for v in text["verdict"]:
        S.para(v)
    path = S.save(preview_dir / f"{stamp}_F4_{spec.slug}-pass3.png")
    return path, metrics


ONE_X_GAP = 10                  # px between the 1x views of the overview


def build_arsenal(stamp: str, hand: str = RECOMMENDED_HAND, out_dir: Path = OUT_DIR,
                  preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    """The five weapons above, each with its own sheet, then one overview:
    all seven weapons at rest, side by side at 1x, to judge them as a set."""
    style = HAND[hand]
    out = {}
    for key in WEAPONS:
        path, _ = build_weapon(key, stamp, hand, out_dir, preview_dir)
        out[key] = str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path)
    idle = [("1 ICE AXE  SDAXA0", render_axe_frame(style, AXE_POSE["A"]))]
    for key, label in (("tt33", "2 TT-33  SDTTA0"), ("izh", "3 IZH-58  SDIZA0")):
        idle.append((label, render_weapon_idle(key, style)))
    idle.append(("4 PPSH-41  SDPPA0", render_ppsh_frame(style, PPSH_POSE["A"])[0]))
    for key, label in (("rpg7", "5 RPG-7  SDRLA0"), ("roks3", "6 ROKS-3  SDRKA0"), ("katyusha", "7 HAND KATYUSHA  SDHKA0")):
        idle.append((label, render_weapon_idle(key, style)))
    S = Sheet(2000, "SOVIET DOOM  ·  F4  ·  THE ARSENAL AT REST  ·  ALL SEVEN SLOTS, 1X AND 2X", stamp)
    S.para(f"Every slot's frame A in hand style {hand}, on the same MAP01 view, so the seven can be judged as one "
           "set: size on screen, where each sits, how much of the view each takes. Top: 2x. Bottom: 1x, the size "
           "the game shows them on a 320x200 screen. The ice axe and the PPSh-41 are the drafts already on the "
           "CEO's gate; the other five are new. Draft, nothing in assets/.")
    S.y += 6
    for i in range(0, len(idle), 3):
        x, h_row = S.pad, 0
        for label, f in idle[i:i + 3]:
            S.label((x, S.y), label, S.gold)
            w2, h2 = S.paste(on_screen([f]), (x, S.y + S.T.line_h() + 4), 2)
            x += w2 + 16
            h_row = max(h_row, h2 + S.T.line_h() + 4)
        S.y += h_row + 14
    per_row = (S.width - 2 * S.pad + ONE_X_GAP) // (SCREEN_W + ONE_X_GAP)
    for i in range(0, len(idle), per_row):
        for j, (_, f) in enumerate(idle[i:i + per_row]):
            S.paste(on_screen([f]), (S.pad + j * (SCREEN_W + ONE_X_GAP), S.y), 1)
        S.y += SCREEN_H + ONE_X_GAP
    S.y += 4
    S.label((S.pad, S.y), "RECOMMENDATION: THE SET AS DRAWN; THE HAND KATYUSHA IS PASS 2, THE LAUNCH BOX.", S.red)
    S.y += S.T.line_h() + 2
    S.para("THE SET. All seven share one hand, one light and one palette, and each is held where its real "
           "counterpart would be: the pistol in one hand, the long guns at the hip, the tubes on the shoulder. "
           "Weak points of the set: the hand Katyusha's launch box is seen almost square from behind; the RPG-7 "
           "shows almost no hand at rest (the grip is behind the eye); the TT-33 is the smallest by far, as "
           "Doom's pistol is. Every "
           "position is NOT VERIFIED in GZDoom until the engine pass (owed, D26).")
    path = S.save(preview_dir / f"{stamp}_F4_arsenal-at-rest.png")
    out["arsenal"] = str(path.relative_to(PROJECT_ROOT))
    return path, out


def render_weapon_idle(key: str, style: HandStyle) -> Frame:
    pose = WEAPON_POSES[key][0]
    fn = {"tt33": render_tt33_frame, "izh": render_izh_frame, "rpg7": render_rpg7_frame,
          "roks3": render_roks3_frame, "katyusha": render_katyusha_frame}[key]
    return fn(style, pose)[0]


# ==================================================================== main
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("what", choices=("hands", "axe", "ppsh", *WEAPONS, "arsenal"))
    ap.add_argument("--hand", default=RECOMMENDED_HAND, choices=sorted(HAND))
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    args = ap.parse_args(argv)
    if args.what == "hands":
        path, metrics = build_hands(args.stamp)
    elif args.what == "axe":
        path, metrics = build_axe(args.stamp, args.hand)
    elif args.what == "ppsh":
        path, metrics = build_ppsh(args.stamp, args.hand)
    elif args.what == "arsenal":
        path, metrics = build_arsenal(args.stamp, args.hand)
    else:
        path, metrics = build_weapon(args.what, args.stamp, args.hand)
    for k, m in metrics.items():
        print(k, m)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
