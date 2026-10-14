"""F5 — the two heavies, Doughboy and Panzermensch: design sweeps on the 3D rig (D35).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_heavy.py               (Windows)
    .venv/bin/python tools/art/gen_heavy.py                       (macOS)
    ... gen_heavy.py --stamp 2026-10-14_1924   fixes the sheet's timestamp
    ... gen_heavy.py --no-sheet                sprites, lineups and metrics only

What this is. D35: the most-seen enemies get drawings of their own. Four are
done and approved on the rig (rifleman D38/D55, Legion trooper D48/D54,
Stormtrooper D48/D56, hound D50/D55). Two heavies still wear Freedoom:
the Doughboy (`SD_Doughboy`, sprite `SDDB`, BESTIARY §7, placeholder HEAD)
and the Panzermensch (`SD_Panzermensch`, sprite `SDPM`, BESTIARY §8,
placeholder BOS2), whose 1000 HP variant `SD_PanzermenschSchwer` has no
sprites of its own and today looks identical. Before ~80 images exist the
CEO makes ONE decision per enemy, what it looks like, as with the others:
a SWEEP (PIPELINE stage 2) of four cells each, shown at rotations 1, 3 and
5 and in the attack frame, then at 1x on MAP01's walls beside the two
APPROVED infantries (assets/sprites/rifleman/SDRRA1, assets/sprites/legion/
SDLTA1) and the Freedoom placeholder, then as a 16-px silhouette. A last
section proposes how to tell the Schwer apart. Nothing goes to assets/.

The cells (A is the BESTIARY brief taken literally; every other cell
changes one or two things from it):

  Doughboy      helmet                    face                   extra
    A           dark steel M1 (brief)     one lidless eye, slack mouth   -
    B           dark steel BRODIE (1917)  as A                   -
    C           dark steel M1             as A                   severed: neck stump, spine, dark-red drip
    D           CHROME M1 (the trooper's) chrome bumper jaw      -

  Panzermensch  head                      shoulders              extra
    A           bucket helm, visor slit   spiked pauldrons       red back banner (D12)
    B           giant Stahlhelm, slit     spiked pauldrons       banner
    C           bucket helm, LIT slit     exhaust stacks         banner, side skirts (Schürzen)
    D           bare skull, iron mask     spiked pauldrons       banner, bare arms, bolts that seep
                bolted on

How it is built. Everything that draws is tools/art/rig_core.py, imported,
not edited: primitives, two-bone IK, Doom's rotations, the sphere tracer,
majority vote to 1x, contour and rim, chrome shading, insignia stamps. The
materials are COPIES of the approved figures' tables, new ones appended
(rig_core.register_material: append-only), so no approved id moves:
the Doughboy on gen_legion.py's table (the Legion's chrome, flesh_pink
flesh, no value shift: the light faction), the Panzermensch on gen_rig.py's
(the Reich's khaki_olive, the armband, VALUE_SHIFT -0.26 on the reused
cloth). gen_rig, gen_legion, gen_storm and gen_hound are imported or read,
never edited.

Palette: v2 (D45). The Doughboy's flesh is `flesh_pink`, the only v2 ramp
used; the Panzermensch is v1 only. Blood is dark red (D49): flag_red 1-5
over black. Scenes are re-quantised to palette v2 whole (gen_enemy's light
stand-in, RGB x L/224; NOT VERIFIED against GZDoom's light tables).

The floater. A Doughboy is never on the floor: from memory of Doom's
P_ZMovement, a floater drifts until its bottom is at its target's z plus
half its own height (28 units for a 56-high actor): NOT VERIFIED, and it is
how the lineups hang it (HOVER). HEAD is hung the same way, by its own
offsets.

NO FONTS. The sprites carry no text; the sheet is HTML (sheetlib), labels
are the browser's text. tests/test_gen_heavy.py keeps it so.

Outputs (work/ is gitignored):
    work/art/enemies/heavy/SDDB_<cell>_<frame><rot>.png   RGBA, hard alpha, grAb
    work/art/enemies/heavy/SDPM_<cell>_<frame><rot>.png
    work/art/enemies/heavy/SDPM_schwer_<variant>_A1.png
    work/art/enemies/heavy/lineup_<enemy>_<scene>.png, metrics.json
    docs/art/previews/<stamp>_F5_doughboy-panzermensch-sweep.html
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
if str(ART_TOOLS) not in sys.path:
    sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (light stand-in, far view, silhouette, luma)
import gen_legion as legion  # noqa: E402  (the Legion's table: chrome, flesh_pink; its flag colours)
import gen_rig as rig  # noqa: E402  (the Reich's table: khaki_olive, the armband; its value shift)
import palette as palgen  # noqa: E402
import rig_core as core  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "heavy"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SPRITES = PROJECT_ROOT / "assets" / "sprites"
TEXTURES = PROJECT_ROOT / "assets" / "textures" / "soviet_base"
FLATS = PROJECT_ROOT / "assets" / "flats" / "soviet_base"

DB_SPRITE = "SDDB"              # BESTIARY §7, MOD-SPEC §6.3
PM_SPRITE = "SDPM"              # BESTIARY §8
SEED = 104                      # DoomEdNum 21104 (the Doughboy): the veins' layout and the cloth grain
V = core.V
Mat = core.Mat
FLESH = legion.FLESH            # palette v2 flesh_pink (D45)

DB_CV = core.Canvas(80, 96, 40, 76)     # the floater: row 76 is the actor's z; room below for C's stump
PM_CV = core.Canvas(112, 96, 56, 90)    # the brute: the throw's arm reaches forward, the stacks rise
HOVER = 28                      # px the floater's z sits above the floor (P_ZMovement, from memory: NOT VERIFIED)
LINEUP_WALL_H = 112             # a wall tall enough for a floater hung over a 56-unit man
LINEUP_SLOT = 64
WALL_SHIFT = 16                 # SDCONC1 has a panel seam every 32 px: unshifted, one runs under every slot centre
                                # and the floaters look hung on strings

# ================================================================ palettes
def palette_v2() -> list[tuple[int, int, int]]:
    return palgen.colours(2)


# ================================================================ materials
# Doughboy: the Legion trooper's table (gen_legion.MATERIALS: chrome, flesh,
# void, teeth, belt ...), copied, with the floater's own appended.
DB_NEW: dict[str, Mat] = {
    # BESTIARY §7: helmet steel_blue 2-6, rim highlight 12-15. Lambert, not
    # chrome: the brief wants the helmet DARK on top (§10 rule 5, lamps).
    "helm_dark": Mat((("black",), ("steel_blue", 1, 7), ("steel_blue", 12, 14))),
    "vein": Mat(((FLESH, 3, 10),)),
    "sclera": Mat((("plaster_warm", 9, 15), ("white",))),
    "iris": Mat.on_ramp("steel_blue", 2, 10),
    "pupil": Mat((("black",),)),
    "raw": Mat((("flag_red", 0, 3), (FLESH, 4, 8))),      # torn flesh, the lidless rim, the gullet
    "bone": Mat.on_ramp("plaster_warm", 8, 14),
    "blood": Mat.on_ramp("flag_red", 1, 5, black_floor=True, flat=True),     # D49: dark red, no rim
    # D's jaw: bright steel lit by the key light, not reflective chrome. As
    # chrome it faces the ground and reflects it: a black bar under the eye.
    "jaw_steel": Mat((("steel_blue", 6, 15), ("white",))),
    "sdl_core": Mat((("steel_blue", 13, 15), ("white",)), flat=True),      # SD_DoughboyShell: white-hot ...
    "sdl_trail": Mat.on_ramp("flag_red", 6, 12, flat=True),               # ... with a red trail (§7)
}
DB_MATERIALS: dict[str, Mat] = dict(legion.MATERIALS)
# The trooper's chrome environment with a darker sky: on a helmet four times
# the trooper's, his sky (0.80-1.0) fills the dome with flat white and it
# reads as a hard hat; 0.50-0.92 keeps a gradient. Only cell D wears chrome.
DB_CHROME = core.Chrome(horizon=-0.60, sky_lo=0.50, sky_hi=0.92, ground_lo=0.04, ground_span=0.30,
                        ground_fade=0.8, spec_cos=0.90, key=0.22, ao=0.5)
for _n, _m in DB_NEW.items():
    core.register_material(_n, _m, DB_MATERIALS)

# Panzermensch: the rifleman's table (gen_rig.MATERIALS: coat, helmet,
# leather, flesh, void, band ...), copied, with the brute's appended. Every
# new one keeps the value given here (shift=False); the rifleman's reused
# cloth takes his value shift, so a reused material looks as it does on him.
PLATE_LIFT = -0.12              # most of the plate in black and khaki_olive 0-2: it reads black, not olive drab
PM_NEW: dict[str, Mat] = {
    # BESTIARY §8: "black-painted plate", khaki_olive 1-4 for the darkest
    # shadow. Black, then the olive ramp to 4 on the lit faces: black paint, not olive drab.
    "plate": Mat((("black",), ("khaki_olive", 0, 4)), shift=False, lift=PLATE_LIFT),
    "rivet": Mat.on_ramp("khaki_olive", 5, 11, shift=False),
    "banner": Mat.on_ramp("flag_red", 3, 10, shift=False),
    "exhaust": Mat((("black",), ("rust_brown", 1, 7)), shift=False),
    "glow": Mat.on_ramp("hazard_yellow", 10, 15, shift=False, flat=True),   # C's lit visor (a brightmap, see the sheet)
    "pzl_core": Mat.on_ramp("cream_yellow", 13, 15, shift=False, flat=True),  # SD_PanzerShell: dull yellow
    "pzl_shell": Mat.on_ramp("hazard_yellow", 6, 12, shift=False, flat=True),  # core ...
    "pzl_smoke": Mat.on_ramp("khaki_olive", 3, 8, shift=False, flat=True),    # ... olive smoke edge (§8)
    "seep": Mat.on_ramp("flag_red", 1, 5, black_floor=True, shift=False, flat=True),  # D49, D's bolts
    # The Schwer's recolour candidate (section 7): Dunkelgelb, the late-war
    # German armour yellow, from the same khaki_olive ramp, lighter.
    "plate_gelb": Mat((("black",), ("khaki_olive", 4, 12)), shift=False),
}
PM_MATERIALS: dict[str, Mat] = dict(rig.MATERIALS)
for _n, _m in PM_NEW.items():
    core.register_material(_n, _m, PM_MATERIALS)
PM_VALUE_SHIFT = rig.VALUE_SHIFT

# What each faction may NOT be drawn in (BESTIARY §2.1); checked by the tests.
DB_FORBIDDEN_RAMPS = {"khaki_olive", "military_green"}           # the Reich's, the world's
PM_FORBIDDEN_RAMPS = {"steel_blue", "military_green", FLESH}     # the Legion's, the world's


# ================================================================ insignia
# The Doughboy's "single small US-flag decal on the helmet" (BESTIARY §7):
# 5x4 hard pixels in the trooper's flag colours, on the helmet's front.
DECAL = (
    "BBRRR",
    "BBWWW",
    "RRRRR",
    "WWWWW",
)
DECAL_INSIGNIA = core.Insignia("decal", (len(DECAL[0]), len(DECAL)),
                               core.pattern_drawer(DECAL, legion.FLAG_COLOURS), outward=(0.0, 0.0, 1.0),
                               min_px=8, search=3, turned_away=0.35)
# The Panzermensch's banner (BESTIARY §8, D12): the 7x7 armband symbol on a
# red panel bolted to his back, seen when he turns away.
BANNER_INSIGNIA = core.Insignia("banner", (7, 7), core.armband_draw, outward=(0.0, 0.0, -1.0), min_px=24,
                                turned_away=0.35)


# ================================================================ helpers
def unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def slerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    om = float(np.arccos(np.clip(a @ b, -1.0, 1.0)))
    if om < 1e-4:
        return unit(a + (b - a) * t)
    return (np.sin((1 - t) * om) * a + np.sin(t * om) * b) / np.sin(om)


def scale_prims(prims: list[core.Prim], k: float) -> list[core.Prim]:
    """The primitives scaled by k about the model origin (feet on the floor
    stay on it). Every SDF here is exact or homogeneous of degree 1 in its
    lengths, so scaling every length and the translation scales the shape."""
    out = []
    for p in prims:
        q = copy.deepcopy(p)
        q.a = q.a * k
        if q.b is not None:
            q.b = q.b * k
        q.r = np.asarray(q.r, float) * k if q.kind in ("ellipsoid", "box") else q.r
        q.r1, q.r2, q.h, q.rnd = q.r1 * k, q.r2 * k, q.h * k, q.rnd * k
        q.clip = [(n, off * k) for n, off in q.clip]
        q.cut = [(c * k, half * k) for c, half in q.cut]
        q.xt = q.xt * k
        out.append(q)
    return out


def add_to(P: list):
    def add(grp: str, prim: core.Prim) -> core.Prim:
        prim.grp = grp
        P.append(prim)
        return prim
    return add


# ================================================================ cells
@dataclass(frozen=True)
class DBCell:
    key: str
    helmet: str        # "m1" | "brodie" | "chrome"
    mouth: str         # "slack" | "bumper"
    severed: bool
    title: str


DB_CELLS = (
    DBCell("A", "m1", "slack", False, "Brief: pink veined sphere, one lidless eye, slack mouth, dark M1"),
    DBCell("B", "brodie", "slack", False, "As A, the 1917 Brodie helmet: what a doughboy actually wore"),
    DBCell("C", "m1", "slack", True, "As A, severed: neck stump, dangling spine, dark-red drip"),
    DBCell("D", "chrome", "bumper", False, "Chrome M1 (the trooper's) and a chrome bumper for a jaw"),
)
DB = {c.key: c for c in DB_CELLS}


@dataclass(frozen=True)
class PMCell:
    key: str
    head: str          # "bucket" | "stahlhelm" | "mask"
    top: str           # "spikes" | "stacks" | "both" (the Schwer candidate S2)
    lit_visor: bool
    title: str


PM_CELLS = (
    PMCell("A", "bucket", "spikes", False, "Brief: riveted black slab, visor slit, spiked pauldrons, back banner"),
    PMCell("B", "stahlhelm", "spikes", False, "As A, a giant Stahlhelm: the Reich's flared helmet"),
    PMCell("C", "bucket", "stacks", True, "Walking Panzer: exhaust stacks, side skirts, a lit visor slit"),
    PMCell("D", "mask", "spikes", False, "The man under the iron: bare skull, mask bolted on, bare arms"),
)
PM = {c.key: c for c in PM_CELLS}

# What each cell shows: (frame, rotation). BESTIARY §7: SDDB A float, D the
# attack (Bright); §8: SDPM A walk, G the attack. 1 front, 3 its left side,
# 5 its back (rig_core's rotation convention).
DB_VIEWS = (("A", 1), ("A", 3), ("A", 5), ("D", 1))
PM_VIEWS = (("A", 1), ("A", 3), ("A", 5), ("G", 1))
ROT_NAMES = {1: "front", 3: "its left side", 5: "its back"}


# ================================================================ Doughboy
DB_R = 25.0                     # the sphere: 50 px across (HEAD is 63 wide with its horns; radius 31 actor)
DB_C = V(0.0, DB_R, 0.0)        # bottom of the sphere on the actor's z
EYE_DIR = unit((0.0, 0.20, 1.0))
MOUTH_DIR = unit((0.0, -0.56, 0.83))
N_VEINS = 7
N_LUMPS = 7                     # flesh lumps that break the perfect sphere
HELM_DARK_BASE = 0.30          # the dark M1: most of it in steel_blue 1-7, the lit edge jumps to 12-14
HELMET_TILT = 7.0               # degrees, the helmet sits askew (battered, strapped on)


def _veins(rng) -> list[core.Prim]:
    """Raised veins over the top, the sides and the back, running in to the
    lidless eye's rim (BESTIARY §7: 'veined')."""
    out = []
    e1 = unit(np.cross(EYE_DIR, V(0, 1, 0)))
    e2 = np.cross(e1, EYE_DIR)
    for i in range(N_VEINS):
        while True:
            d0 = unit(rng.normal(size=3))
            if d0[2] < 0.15 and d0[1] > -0.55:
                break
        ang = rng.uniform(0, 2 * np.pi)
        d1 = unit(EYE_DIR * np.cos(0.40) + (e1 * np.cos(ang) + e2 * np.sin(ang)) * np.sin(0.40))
        n = 7
        pts = []
        for j in range(n + 1):
            d = slerp(d0, d1, j / n)
            jitter = rng.normal(scale=0.08, size=3) if 0 < j < n else np.zeros(3)
            pts.append(DB_C + unit(d + jitter) * (DB_R + 0.1))
        for j in range(n):
            r0 = 0.72 - 0.25 * j / n
            out.append(core.rcone("vein", 0.45, pts[j], pts[j + 1], r0, r0 - 0.04))
        k = int(rng.integers(2, n - 2))                 # one branch off the middle
        d2 = unit(pts[k] - DB_C + rng.normal(scale=0.35, size=3) * DB_R)
        b = DB_C + d2 * (DB_R + 0.1)
        out.append(core.rcone("vein", 0.45, pts[k], DB_C + unit(pts[k] - DB_C + b - DB_C) * (DB_R + 0.1), 0.55, 0.4))
    return out


def _lumps(rng) -> list[core.Prim]:
    """Flesh swellings over the top, sides and back: not a ball, a growth."""
    out = []
    for i in range(N_LUMPS):
        while True:
            d = unit(rng.normal(size=3))
            if d[2] < 0.35 and d[1] > -0.6:
                break
        r = rng.uniform(5.0, 8.5)
        out.append(core.ellipsoid("flesh", 0.76, tuple(DB_C + d * (DB_R - r * 0.55)), (r, r * 0.85, r)))
    return out


def _db_mouth(cell: DBCell, attack: bool, add, sphere: core.Prim) -> np.ndarray:
    """The mouth; returns the point the shell leaves from."""
    m = DB_C + MOUTH_DIR * DB_R
    if cell.mouth == "bumper":
        # a chrome jaw over the lower face, a 1950s grille: a shell hinged at
        # the sides, dark grille slots, a lip bar; the attack drops it open
        jaw_top = m[1] + 2.0
        opn = 6.5 if attack else 2.6
        sphere.cut.append((V(0, jaw_top + 0.4, m[2]), V(11.0, opn, 8.0)))
        add("head", core.ellipsoid("void", 0.05, tuple(DB_C + MOUTH_DIR * (DB_R - 6.0) + V(0, 2.5, 0)),
                                   (12.0, opn + 2.4, 5.0)))
        for x in (-8.0, -4.6, -1.4, 2.2, 5.6, 8.4):                                             # his own teeth above
            add("head", core.ellipsoid("teeth", 0.85, tuple(V(x, jaw_top + opn - 0.6, m[2] - 1.6)), (0.95, 1.3, 0.8)))
        RJ = DB_R + 1.4
        add("jaw", core.ellipsoid("jaw_steel", 0.72, tuple(DB_C), (RJ, RJ * 0.97, RJ),
                                  clip=[(V(0, 1, 0), jaw_top), (V(0, 0, -1), -9.0), (V(1, 0, 0), 15.5),
                                        (V(-1, 0, 0), 15.5), (V(0, -1, 0), -(DB_C[1] - 21.0))]))
        for x in (-7.5, -4.5, -1.5, 1.5, 4.5, 7.5):                                             # grille slots
            pts = []
            for y in (jaw_top - 2.0, jaw_top - 8.5):
                z = float(np.sqrt(max((RJ + 0.1) ** 2 - x * x - (y - DB_C[1]) ** 2, 0.0))) + DB_C[2]
                pts.append(V(x, y, z))
            add("jaw", core.rcone("void", 0.0, pts[0], pts[1], 0.6))
        arc = []
        for th in np.linspace(-0.62, 0.62, 7):                                                   # the lip bar
            rr = float(np.sqrt(max((RJ + 0.6) ** 2 - (jaw_top - DB_C[1]) ** 2, 0.0)))
            arc.append(V(rr * np.sin(th), jaw_top - 0.4, rr * np.cos(th) + DB_C[2]))
        for a, b in zip(arc[:-1], arc[1:]):
            add("jaw", core.rcone("jaw_steel", 0.85, a, b, 1.2))
        for sx in (1, -1):                                                                       # hinge bolts
            add("jaw", core.ellipsoid("jaw_steel", 0.9, tuple(arc[0 if sx < 0 else -1] + V(0, -1.6, -0.6)),
                                      (1.5, 1.5, 1.5)))
        return V(0, jaw_top + opn * 0.2, m[2] + 3.5)
    # slack mouth: a slot cut into the sphere, the dark inside, a hanging lip
    opn = 6.0 if attack else 3.4
    sphere.cut.append((m + V(0, -0.5, 0), V(12.5 if attack else 11.5, opn, 7.0)))
    add("head", core.ellipsoid("void", 0.05, tuple(DB_C + MOUTH_DIR * (DB_R - 6.0)), (12.5, opn + 2.0, 5.0)))
    add("head", core.ellipsoid("raw", 0.40, tuple(m + V(1.5, -opn + 0.6, -0.4 + (1.0 if attack else 0.0))),
                               (6.4, 1.8, 3.2)))                                               # the tongue lolls
    for x in (-8.0, -4.6, -1.4, 2.2, 5.6, 8.4):                                                 # a few teeth
        add("head", core.ellipsoid("teeth", 0.85, tuple(m + V(x, opn - 1.2, -1.4)), (0.95, 1.3, 0.8)))
    if attack:
        for x in (-6.0, -2.0, 2.4, 6.2):
            add("head", core.ellipsoid("teeth", 0.80, tuple(m + V(x, -opn + 0.9, -1.0)), (0.9, 1.2, 0.8)))
    add("head", core.ellipsoid("flesh", 0.60, tuple(m + V(0, -opn - 2.6, 1.4 + (1.4 if attack else 0.0))),
                               (11.5, 3.0, 3.4)))                                              # the slack lip hangs
    return m + V(0, 0, 3.5)


def _db_helmet(cell: DBCell, add) -> list[core.Prim]:
    """The helmet strapped on top: M1 pot (dark or chrome) or the Brodie."""
    mat = "chrome" if cell.helmet == "chrome" else "helm_dark"
    dome = 0.62 if mat == "chrome" else HELM_DARK_BASE
    H: list[core.Prim] = []
    if cell.helmet == "brodie":
        # the British-pattern 'soup bowl' the AEF wore in 1917: a shallow bowl, a wide flat brim
        H.append(add("helmet", core.ellipsoid(mat, dome, (0, 46.0, -0.5), (18.0, 13.0, 18.5),
                                              clip=[(V(0, -1, 0), -46.0)], tag="decal")))
        H.append(add("helmet", core.ccone(mat, 0.45, 45.2, 46.6, 29.0, 27.5, kz=0.96, z=-0.5)))
        H.append(add("helmet", core.ccone(mat, 0.75, 46.4, 47.1, 27.6, 18.4, kz=0.96, z=-0.5)))
        rim_y, rim_x = 45.6, 26.0
    else:
        H.append(add("helmet", core.ellipsoid(mat, dome, (0, 40.0, -1.0), (21.5, 22.0, 22.5),
                                              clip=[(V(0, -1, 0), -43.0)],
                                              cut=[(V(9.5, 61.5, 4.0), V(3.5, 1.6, 3.5))],   # a dent
                                              tag="decal")))
        H.append(add("helmet", core.ccone(mat, 0.48, 41.6, 43.4, 23.2, 22.0, kz=1.0, z=-1.0)))   # the rim
        rim_y, rim_x = 42.4, 21.6
    for sx in (1, -1):          # a chinstrap that goes nowhere: hangs loose beside the head
        a = V(sx * rim_x, rim_y, 2.0)
        b = V(sx * (rim_x + 3.2), rim_y - 13.0, 4.5)
        c = V(sx * (rim_x + 2.0), rim_y - 19.0, 7.0)
        H.append(add("helmet", core.rcone("belt", 0.40, a, b, 0.75)))
        H.append(add("helmet", core.rcone("belt", 0.40, b, c, 0.75)))
        if sx > 0:
            H.append(add("helmet", core.box("chrome", 0.8, tuple(c + V(0, -0.8, 0.3)), (1.0, 1.2, 0.5), rnd=0.2)))
    return H


def _db_severed(add, rng) -> None:
    """Cell C: the thing kept the helmet and lost the body, literally: a torn
    neck under the sphere, the spine hanging out of it, dark-red drip."""
    ring_y = 2.6
    for i in range(10):
        a = 2 * np.pi * i / 10
        p = V(np.sin(a) * 9.5, ring_y - 0.4 * (i % 3), np.cos(a) * 8.5 - 1.0)
        add("head", core.ellipsoid("raw", 0.40, tuple(p), (3.8, 3.0, 3.4)))
    add("head", core.ellipsoid("void", 0.05, (0, 0.8, -1.0), (6.0, 2.2, 5.0)))        # the throat
    spine = [V(0, 1.2, -3.0)]
    for i in range(6):                                                                 # vertebrae, dangling
        spine.append(spine[-1] + V(0.6 * np.sin(i * 1.3), -2.6, 0.35))
    for j, p in enumerate(spine[1:]):
        add("head", core.ellipsoid("bone", 0.62, tuple(p), (2.0 - 0.15 * j, 1.0, 1.7 - 0.12 * j)))
    for sx, length in ((1, 9.0), (-1, 12.0), (0.4, 6.0)):                              # torn vessels
        a = V(sx * 5.0, 1.0, 2.0)
        add("head", core.rcone("raw", 0.35, a, a + V(sx * 1.5, -length, 1.0), 1.1, 0.6))
    for i in range(7):                                                                 # drops falling
        x = rng.uniform(-7, 7)
        add("blood", core.ellipsoid("blood", 0.55, (x, -rng.uniform(5, 16), rng.uniform(-1, 4)), (0.8, 1.2, 0.8)))
    for i in range(6):                                                                 # runs on the lower sphere
        th = rng.uniform(-1.1, 1.1)
        d = unit((np.sin(th), -0.75, np.cos(th)))
        add("blood", core.rcone("blood", 0.45, DB_C + d * (DB_R + 0.2), DB_C + unit(d + V(0, -0.35, 0)) * (DB_R + 0.2),
                                1.1, 0.7))


def db_model(cell: DBCell, frame: str = "A", seed: int = SEED) -> tuple[list[core.Prim], np.ndarray]:
    """The Doughboy in rig_core's model space (the actor's z on y=0, facing
    +z, +x its LEFT). Returns (prims, the point the shell leaves from)."""
    rng = np.random.default_rng(seed)
    P: list[core.Prim] = []
    add = add_to(P)
    attack = frame == "D"
    sphere = add("head", core.ellipsoid("flesh", 0.78, tuple(DB_C), (DB_R, DB_R * 0.97, DB_R)))
    for v in _veins(rng):
        add("head", v)
    # the lidless eye: a raw rim, the sclera, a cold blue iris, the pupil
    for lump_ in _lumps(rng):
        add("head", lump_)
    add("head", core.ellipsoid("raw", 0.40, tuple(DB_C + EYE_DIR * (DB_R - 4.4)), (11.6, 10.2, 6.6)))
    add("head", core.ellipsoid("sclera", 0.66, tuple(DB_C + EYE_DIR * (DB_R - 4.0)), (10.2, 9.0, 7.0)))
    add("head", core.ellipsoid("iris", 0.55, tuple(DB_C + EYE_DIR * (DB_R + 2.4)), (5.0, 5.0, 1.3)))
    add("head", core.ellipsoid("pupil", 0.0, tuple(DB_C + EYE_DIR * (DB_R + 3.4)), (2.3, 2.7, 0.6)))
    muzzle = _db_mouth(cell, attack, add, sphere)
    if attack and cell.mouth == "bumper":
        hinge = V(0.0, DB_C[1] + MOUTH_DIR[1] * DB_R + 2.0, 4.0)
        core.transform(P, {}, {"jaw"}, core.rot_x(-18.0), hinge, V(0, -3.0, 0.5))
    helmet = _db_helmet(cell, add)
    core.transform(P, {}, {"helmet"}, core.rot_z(-HELMET_TILT), DB_C)      # askew, to his right
    del helmet
    if cell.severed:
        _db_severed(add, rng)
    if attack:      # SD_DoughboyShell leaving the mouth: white-hot core, red trail behind it
        add("shell", core.ellipsoid("sdl_trail", 0.6, tuple(muzzle + V(0, 0, 1.0)), (4.6, 4.2, 3.0)))
        add("shell", core.ellipsoid("sdl_core", 0.8, tuple(muzzle + V(0, 0, 3.4)), (2.9, 2.9, 2.0)))
    return P, muzzle


def db_grab() -> tuple[int, int]:
    """A floater's offsets: the actor's z is the canvas's foot row (no feet to sink)."""
    return DB_CV.cx, DB_CV.foot_row


def render_db(key: str, frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    prims, _ = db_model(DB[key], frame, seed)
    return core.render(prims, rotation, DB_CV, DB_MATERIALS, seed=seed, value_shift=0.0, chrome=DB_CHROME,
                       insignia=(DECAL_INSIGNIA,), what=f"SDDB {key} {frame}{rotation}")


# ============================================================ Panzermensch
PM_ANKLE = 3.2
PM_HIP_Y, PM_HIP_X = 31.0, 5.8
PM_THIGH, PM_SHIN = 15.0, 14.0
PM_UPPER_ARM, PM_FOREARM = 13.0, 12.0
PM_SHOULDER = (13.5, 53.0, -0.5)
PM_WAIST = V(0.0, 33.0, 0.0)
TORSO_Y0, TORSO_Y1 = 33.0, 55.0
TORSO_R0, TORSO_R1, TORSO_KZ = 9.5, 12.5, 0.82
PM_UPPER = {"upper", "arm", "head", "helmet", "banner", "shell", "stacks"}


@dataclass(frozen=True)
class PMPose:
    key: str
    foot_l: tuple
    foot_r: tuple
    hand_l: tuple
    hand_r: tuple
    hunch: float        # degrees forward about the waist
    shell: bool = False


PM_POSES = {
    "A": PMPose("A", (7.0, PM_ANKLE, 1.2), (-7.0, PM_ANKLE, -1.2), (16.5, 30.0, 3.0), (-16.5, 30.0, 2.0), 6.0),
    # G: the throw's release. Right fist forward and up, the shell just out of it.
    "G": PMPose("G", (7.0, PM_ANKLE, 5.0), (-7.0, PM_ANKLE, -5.0), (14.0, 36.0, 10.0), (-11.0, 67.0, 8.0), 10.0,
                shell=True),
}


def _torso_front(x: float, y: float) -> float:
    r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - TORSO_Y0) / (TORSO_Y1 - TORSO_Y0)
    return TORSO_KZ * float(np.sqrt(max(r * r - x * x, 0.0)))


def _pm_head(cell: PMCell, add) -> None:
    slit = "glow" if cell.lit_visor else "void"
    if cell.head == "bucket":
        add("helmet", core.ccone("plate", 0.50, 55.5, 66.0, 5.7, 5.2, kz=0.95, z=0.6))
        add("helmet", core.ellipsoid("plate", 0.56, (0, 66.0, 0.6), (5.2, 2.2, 4.95)))
        add("helmet", core.rcone("plate", 0.66, V(0, 68.0, 1.0), V(0, 58.0, 5.9), 0.75))           # the ridge
        add("helmet", core.box(slit, 0.0, (0, 61.6, 5.3), (3.6, 0.62, 0.9)))                      # the slit
        for y in (64.6, 58.6):
            for x in (-3.4, 3.4):
                add("helmet", core.ellipsoid("rivet", 0.6, (x, y, 5.45), (0.75, 0.75, 0.6)))
    elif cell.head == "stahlhelm":
        add("helmet", core.box("plate", 0.42, (0, 60.0, 4.2), (4.6, 4.4, 1.6), rnd=1.2))           # face plate
        add("helmet", core.box(slit, 0.0, (0, 61.0, 5.7), (3.4, 0.62, 0.6)))
        add("helmet", core.ellipsoid("helmet", 0.62, (0, 63.6, 0.0), (7.0, 7.4, 7.4),
                                     clip=[(V(0, -1, 0), -63.2)]))                                  # the dome
        add("helmet", core.ccone("helmet", 0.42, 62.6, 64.0, 8.0, 7.6, kz=1.0, z=0.0,
                                 clip=[(V(0, 0, 1), 6.8)]))                                         # the ledge
        add("helmet", core.ccone("helmet", 0.30, 55.0, 63.0, 11.4, 7.8, kz=0.96, z=-0.4,
                                 clip=[(V(0, 0, 1), 4.6)],
                                 cut=[(V(0, 58.0, 7.0), V(5.2, 5.6, 4.4))]))                        # flared skirt
        add("helmet", core.ellipsoid("helmet", 0.40, (0, 63.0, 6.6), (5.8, 0.9, 2.2)))           # brim
    else:   # "mask": a bald khaki skull, an iron mask bolted onto the face
        add("helmet", core.ellipsoid("flesh", 0.56, (0, 61.2, 0.2), (6.6, 7.0, 6.6)))
        add("helmet", core.ellipsoid("flesh", 0.50, (0, 57.4, 1.2), (5.4, 3.0, 5.0)))             # jowls on the gorget
        add("helmet", core.ellipsoid("plate", 0.50, (0, 60.6, 3.4), (6.0, 5.6, 3.6),
                                     clip=[(V(0, 0, -1), -4.0)]))                                   # the mask
        add("helmet", core.box(slit, 0.0, (0, 61.6, 6.7), (3.6, 0.62, 0.7)))
        for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
            p = V(4.9 * np.sin(a), 60.6 + 4.4 * np.cos(a), 0.0)
            p[2] = 3.4 + 3.6 * float(np.sqrt(max(1 - (p[0] / 6.0) ** 2 - ((p[1] - 60.6) / 5.6) ** 2, 0.0)))
            add("helmet", core.ellipsoid("rivet", 0.7, tuple(p + V(0, 0, 0.2)), (0.8, 0.8, 0.6)))
            if np.cos(a) < -0.3:          # the lower bolts seep into the jowls
                add("helmet", core.rcone("seep", 0.5, p + V(0, -0.6, 0.1), p + V(0.2, -3.6, 0.2), 0.55, 0.4))


def pm_model(cell: PMCell, frame: str = "A", plate: str = "plate", seed: int = SEED) -> list[core.Prim]:
    """The Panzermensch in rig_core's model space (feet on y=0, facing +z,
    +x his LEFT), posed. `plate` names the armour's material (the Schwer's
    recolour candidate swaps it)."""
    pose = PM_POSES[frame]
    P: list[core.Prim] = []
    add = add_to(P)

    def label(start: int, limb: str, side: int) -> None:
        for q in P[start:]:
            q.limb, q.side = limb, side

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((core.LEFT, pose.foot_l, "leg_l"), (core.RIGHT, pose.foot_r, "leg_r")):
        start = len(P)
        hip = V(side * PM_HIP_X, PM_HIP_Y, 0.0)
        knee, ankle = core.two_bone(hip, foot, PM_THIGH, PM_SHIN, V(0, 0, 1))
        add(grp, core.rcone("plate", 0.50, hip, knee, 4.7, 4.0))                                   # cuisse
        add(grp, core.ellipsoid("flesh", 0.40, tuple(knee + V(0, 0, -2.2)), (2.8, 2.6, 2.0)))     # the joint shows
        add(grp, core.ellipsoid("plate", 0.62, tuple(knee + V(0, 0.3, 1.8)), (3.8, 3.4, 2.8)))   # knee cop
        add(grp, core.rcone("plate", 0.46, knee, ankle + V(0, 2.0, 0), 4.0, 3.5))                  # greave
        add(grp, core.box("plate", 0.38, (ankle[0], ankle[1] - 1.5, ankle[2] + 1.8), (3.0, 1.7, 4.8), rnd=0.9))
        add(grp, core.ellipsoid("rivet", 0.6, tuple(knee + V(0, 0.4, 4.4)), (0.8, 0.8, 0.6)))
        if cell.top in ("stacks", "both"):     # Schürzen: a side skirt plate hung from the belt
            add(grp, core.box("plate", 0.46, (side * 11.4, 23.0, 0.0), (0.6, 7.0, 7.0), rnd=0.3))
            for z in (-4.5, 4.5):
                add(grp, core.ellipsoid("rivet", 0.6, (side * 12.0, 28.4, z), (0.5, 0.8, 0.8)))
        label(start, "leg", side)
    add("upper", core.ccone("plate", 0.48, 24.5, 34.0, 10.8, 9.6, kz=0.84))                      # faulds
    for y in (27.6, 30.8):
        add("upper", core.ccone("plate", 0.22, y - 0.3, y + 0.3, 10.9 - (y - 24.5) * 0.13, 10.8 - (y - 24.5) * 0.13,
                                kz=0.85))                                                          # lames

    # ---------------------------------------------------------------- torso
    add("upper", core.Prim("cappedcone", "plate", 0.52, V(0, (TORSO_Y0 + TORSO_Y1) / 2, 0.0),
                           h=(TORSO_Y1 - TORSO_Y0) / 2, r1=TORSO_R0, r2=TORSO_R1, scale=V(1.0, 1.0, TORSO_KZ),
                           tag="torso"))
    add("upper", core.rcone("plate", 0.68, V(0, 36.0, _torso_front(0, 36.0)), V(0, 54.0, _torso_front(0, 54.0)), 1.1))
    for y in (52.4, 36.4):
        for x in (-8.0, -4.0, 4.0, 8.0):
            add("upper", core.ellipsoid("rivet", 0.62, (x, y, _torso_front(x, y) + 0.2), (0.8, 0.8, 0.6)))
    add("upper", core.ccone("plate", 0.46, 54.0, 58.4, 7.8, 6.6, kz=0.95))                        # gorget
    # back banner (D12): a red panel bolted between the shoulder blades
    bz = -_torso_front(0, 46.0) - 0.5
    add("banner", core.box("banner", 0.55, (0, 45.5, bz), (4.6, 6.6, 0.45), tag="banner"))
    for x in (-3.8, 3.8):
        for y in (51.0, 40.0):
            add("banner", core.ellipsoid("rivet", 0.6, (x, y, bz - 0.4), (0.7, 0.7, 0.5)))

    # ------------------------------------------------------------- shoulders
    sx, sy, sz = PM_SHOULDER
    for side in (core.LEFT, core.RIGHT):
        c = V(side * (sx + 0.5), sy + 2.5, sz)
        add("upper", core.ellipsoid("plate", 0.62, tuple(c), (6.8, 5.2, 6.8), clip=[(V(0, -1, 0), -(sy - 1.5))]))
        add("upper", core.ellipsoid("plate", 0.50, tuple(c + V(side * 0.6, -3.6, 0)), (6.2, 3.0, 6.2),
                                    clip=[(V(0, -1, 0), -(sy - 3.6))]))
        for z in (-3.0, 3.0):
            add("upper", core.ellipsoid("rivet", 0.62, tuple(c + V(side * 2.0, 4.0, z)), (0.75, 0.75, 0.75)))
        if cell.top in ("spikes", "both"):     # BESTIARY §8's 16-px tell: shoulder horns
            add("upper", core.rcone("plate", 0.64, c + V(side * 2.2, 3.4, 0.0), c + V(side * 5.4, 11.2, -1.0), 2.1, 0.45))
    if cell.top in ("stacks", "both"):     # exhaust stacks from the back, past the shoulders: the horns
        for side in (core.LEFT, core.RIGHT):
            a = V(side * 6.4, 40.0, -9.0)
            b = V(side * 9.4, 69.0, -10.0)
            add("stacks", core.rcone("exhaust", 0.26, a, b, 2.9, 2.7))                          # iron pipe
            add("stacks", core.rcone("exhaust", 0.55, b - unit(b - a) * 2.0, b + unit(b - a) * 0.3, 3.5))  # rusted cap
            add("stacks", core.ellipsoid("void", 0.0, tuple(b + V(0, 0.35, 0)), (2.2, 0.5, 2.2)))
            for t in (0.30, 0.58):
                p = a + (b - a) * t
                add("stacks", core.rcone("plate", 0.45, p - unit(b - a) * 0.6, p + unit(b - a) * 0.6, 3.3))   # clamps

    _pm_head(cell, add)

    # ---------------------------------------------------------------- arms
    grips = {core.LEFT: V(*pose.hand_l), core.RIGHT: V(*pose.hand_r)}
    for side in (core.LEFT, core.RIGHT):
        start = len(P)
        sh = V(side * sx, sy, sz)
        pole = V(side * 1.0, -1.0, -0.4) if (pose.shell and side == core.RIGHT) else V(side * 1.0, -0.3, -1.0)
        elbow, wrist = core.two_bone(sh, grips[side], PM_UPPER_ARM, PM_FOREARM, pole)
        fd = unit(wrist - elbow)
        upper_mat = "flesh" if cell.head == "mask" else "plate"
        add("arm", core.rcone(upper_mat, 0.52, sh, elbow, 5.0 if cell.head == "mask" else 3.8,
                              4.2 if cell.head == "mask" else 3.4))
        add("arm", core.ellipsoid("flesh", 0.40, tuple(elbow - fd * 0.5 + V(0, 0, 1.2)), (2.6, 2.6, 2.6)))
        add("arm", core.ellipsoid("plate", 0.60, tuple(elbow + V(side * 0.6, 0, -1.4)), (3.4, 3.4, 3.2)))  # couter
        add("arm", core.rcone("plate", 0.50, elbow, wrist, 3.5, 4.0))                              # vambrace
        fist = wrist + fd * 4.2
        add("arm", core.rcone("plate", 0.54, wrist - fd * 1.0, wrist + fd * 1.2, 4.6, 5.4))         # flared cuff
        add("arm", core.ellipsoid("plate", 0.56, tuple(fist), (5.8, 6.4, 6.0)))                    # the gauntlet
        add("arm", core.rcone("plate", 0.64, fist + fd * 3.4 + V(-3.4, 0, 1.4), fist + fd * 3.4 + V(3.4, 0, 1.4), 1.9))
        for k in (-2.6, 0.0, 2.6):
            add("arm", core.ellipsoid("rivet", 0.62, tuple(fist + fd * 4.6 + V(k, 0, 2.4)), (0.8, 0.8, 0.8)))
        if cell.head == "mask":        # the vambrace is bolted through the bare arm
            for k in (-1.6, 1.6):
                b0 = elbow - fd * 1.4 + V(k, 1.2, 3.6)
                add("arm", core.ellipsoid("rivet", 0.7, tuple(b0), (0.8, 0.8, 0.7)))
                add("arm", core.rcone("seep", 0.5, b0 + V(0, -0.5, 0.2), b0 + V(0, -2.6, 0.3), 0.5, 0.35))
        label(start, "arm", side)
        if side == core.RIGHT and pose.shell:
            s = fist + fd * 7.4
            add("shell", core.ellipsoid("pzl_smoke", 0.5, tuple(s - V(0, 0, 0.6)), (4.4, 4.4, 3.0)))
            add("shell", core.ellipsoid("pzl_shell", 0.6, tuple(s + V(0, 0, 1.6)), (3.0, 3.2, 2.2)))
            add("shell", core.ellipsoid("pzl_core", 0.8, tuple(s + V(0, 0, 3.2)), (1.6, 1.7, 1.0)))

    # ------------------------------------------------------------- posing
    if pose.hunch:
        core.transform(P, {}, PM_UPPER, core.rot_x(-pose.hunch), PM_WAIST)
    del plate
    return P


def pm_prims(cell: PMCell, frame: str = "A", plate: str = "plate", scale: float = 1.0) -> list[core.Prim]:
    P = pm_model(cell, frame)
    if plate != "plate":
        for q in P:
            if q.mat == "plate":
                q.mat = plate
    return scale_prims(P, scale) if scale != 1.0 else P


def render_pm(key: str, frame: str, rotation: int, seed: int = SEED, plate: str = "plate",
              scale: float = 1.0) -> np.ndarray:
    prims = pm_prims(PM[key], frame, plate, scale)
    return core.render(prims, rotation, PM_CV, PM_MATERIALS, seed=seed, value_shift=PM_VALUE_SHIFT,
                       insignia=(BANNER_INSIGNIA,), what=f"SDPM {key} {frame}{rotation}")


# ================================================================ the Schwer
# BESTIARY §2.7/§8: SD_PanzermenschSchwer (1000 HP, MAP03) inherits every
# state of SD_Panzermensch, so today it looks identical. Two ways to tell
# it apart, rendered on the recommended cell:
#   S1  "Dunkelgelb": the same sprite, the plate in the late-war armour
#       yellow (khaki_olive 4-12), i.e. what a recolour would do;
#   S2  "Schwer": a sprite set of its own from the same rig, 12 % bigger,
#       black still, with BOTH the spikes and the stacks and the lit slit.
SCHWER_SCALE = 1.12
SCHWER = {
    "S1": dict(plate="plate_gelb", scale=1.0, lit=None, top=None, title="Dunkelgelb: the plate recoloured"),
    "S2": dict(plate="plate", scale=SCHWER_SCALE, lit=True, top="both",
               title="Black, x1.12, spikes and stacks, lit slit"),
}


def render_schwer(base_key: str, variant: str, rotation: int = 1, seed: int = SEED) -> np.ndarray:
    v = SCHWER[variant]
    base = PM[base_key]
    cell = PMCell(f"{base_key}{variant}", base.head, v["top"] or base.top,
                  base.lit_visor if v["lit"] is None else v["lit"], v["title"])
    prims = pm_prims(cell, "A", v["plate"], v["scale"])
    return core.render(prims, rotation, PM_CV, PM_MATERIALS, seed=seed, value_shift=PM_VALUE_SHIFT,
                       insignia=(BANNER_INSIGNIA,), what=f"SDPM schwer {variant}")


# ================================================================ scenes
# Where MAP01 puts them (docs/levels/MAP01-zarya-7.md §8, §17.2): the
# Doughboy comes out of E1 in the hangar with wave 2 (SDCONC1, light 176,
# 144 in the bay shadows; BESTIARY §10 rule 5: seen against the lamp flat
# SDCEIL1); the Panzermensch stands on the lift in Z10, the darkest room of
# the map (SDCONC1 over an SDSTEL1 dado, light 96, 144 on the exit switch;
# BESTIARY §10 rule 3: the brute in the dark).
DB_SCENES = (
    ("H1", "SDCONC1", 176, "hangar wall, wave 2"),
    ("H2", "SDCONC1", 144, "bay shadow, under the catwalk"),
    ("H3", "SDCEIL1", 192, "against the lamp flat (BESTIARY §10 rule 5)"),
)
PM_SCENES = (
    ("Z1", "SDCONC1", 96, "Z10 lift room, his stand (worst case, §10 rule 3)"),
    ("Z2", "SDSTEL1", 96, "Z10 dado"),
    ("Z3", "SDCONC1", 144, "Z10 exit switch"),
)


def wall_rgb(lump: str) -> np.ndarray:
    path = TEXTURES / f"{lump}.png"
    if not path.is_file():
        path = FLATS / f"{lump}.png"
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def tall_lineup(figures: list[tuple[np.ndarray, int, int]], wall: str, light: int, width: int,
                wall_h: int = LINEUP_WALL_H, floor: str = "SDFLR2") -> np.ndarray:
    """rig_core.lineup on a taller wall (a floater hangs above a man's head):
    each sprite by its own offsets, the actor's z on the floor line minus
    the feet's sink, a MAP01 wall over a floor flat foreshortened 3:1, the
    light stand-in, re-quantised to palette v2."""
    w_rgb = flat.tile_to(np.roll(wall_rgb(wall), WALL_SHIFT, axis=1), width, wall_h)
    fl = flat.tile_to(wall_rgb(floor), width, flat.FLOOR_H * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, flat.FLOOR_H), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = wall_h + (flat.FLOOR_LINE - flat.WALL_H) - core.FEET_SINK
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = base - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return core.lit(canvas, light, palette_v2())


def approved(name: str, folder: str) -> tuple[np.ndarray, int, int] | None:
    """An APPROVED sprite from assets/ (read only): RGBA and its grAb."""
    path = SPRITES / folder / f"{name}.png"
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    gx, gy = core.read_grab(path)
    return arr, gx, gy


def references(placeholder: str, hover: int = 0) -> tuple[list, list[str]]:
    """The two approved infantries and the Freedoom placeholder (hung by
    `hover` px when it floats), for the 1x lineups."""
    figs, labels = [], []
    for name, folder, label in (("SDRRA1", "rifleman", "SDRRA1 Reich rifleman (approved, D38/D55)"),
                                ("SDLTA1", "legion", "SDLTA1 Legion trooper (approved, D48/D54)")):
        r = approved(name, folder)
        if r:
            figs.append(r)
            labels.append(label)
    fd = core.freedoom_sprite(placeholder)
    if fd:
        img, left, top = fd
        figs.append((img, left, top + hover))
        labels.append(f"{placeholder} Freedoom, today's placeholder" + (" (hung as a floater)" if hover else ""))
    return figs, labels


# ================================================================ metrics
SEP_LIT = 12.0                  # lit luma: a pixel this far from the wall's mean separates from it


def measure(rgba: np.ndarray, scenes) -> dict:
    """Size and value; gap_<scene> is |body - wall| luma under that scene's
    light (gen_enemy's stand-in), as every sweep measures it. A mean hides a
    two-tone figure (a dark helmet on a light head averages to concrete), so
    sep_<scene> is the share of its pixels that separate from the wall:
    |pixel - wall| x light >= SEP_LIT."""
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    body = flat.luma(rgba[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "body_luma": round(float(body.mean()), 1), "mass_luma": round(float(np.median(body)), 1)}
    for key, wall, light, _ in scenes:
        f = min(1.0, light / flat.LIGHT_FULL)
        out[f"gap_{key}"] = round(abs(float(body.mean()) - float(flat.luma(wall_rgb(wall)).mean())) * f, 1)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in scenes)
    lum = flat.luma(rgba[..., :3])[a]
    for key, wall, light, _ in scenes:
        f = min(1.0, light / flat.LIGHT_FULL)
        w = float(flat.luma(wall_rgb(wall)).mean())
        out[f"sep_{key}"] = round(float((np.abs(lum - w) * f >= SEP_LIT).mean()), 2)
    out["worst_sep"] = min(out[f"sep_{k}"] for k, *_ in scenes)
    return out


def ramp_share(rgba: np.ndarray, ramp_names: set[str]) -> float:
    """Share of opaque pixels whose colour belongs to the named ramps."""
    cols = set()
    for n in ramp_names:
        cols |= {tuple(c) for c in palgen.ramp_colours(n)}
    a = rgba[..., 3] > 0
    px = [tuple(int(v) for v in p) for p in rgba[..., :3][a]]
    return sum(p in cols for p in px) / max(len(px), 1)


def silhouette_rgb(rgba: np.ndarray) -> np.ndarray:
    sil = flat.silhouette(rgba)
    return np.where(sil[..., None], 0, 235).astype(np.uint8).repeat(3, -1)


# ================================================================ output
def lump(sprite: str, key: str, frame: str, rot: int) -> str:
    """Draft file name: SDDB_<cell>_<frame><rot> (the lump would be SDDB<frame><rot>)."""
    return f"{sprite}_{key}_{frame}{rot}"


def save(rgba: np.ndarray, path: Path, grab: tuple[int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    import struct
    from PIL.PngImagePlugin import PngInfo
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *grab))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def build_all(out_dir: Path = OUT_DIR, seed: int = SEED) -> dict:
    out: dict = {"db": {}, "pm": {}, "schwer": {}, "metrics": {"db": {}, "pm": {}, "schwer": {}}}
    for c in DB_CELLS:
        for frame, rot in DB_VIEWS:
            rgba = render_db(c.key, frame, rot, seed)
            save(rgba, out_dir / f"{lump(DB_SPRITE, c.key, frame, rot)}.png", db_grab())
            out["db"][(c.key, frame, rot)] = rgba
            print(lump(DB_SPRITE, c.key, frame, rot), flush=True)
        out["metrics"]["db"][c.key] = measure(out["db"][(c.key, "A", 1)], DB_SCENES)
    for c in PM_CELLS:
        for frame, rot in PM_VIEWS:
            rgba = render_pm(c.key, frame, rot, seed)
            save(rgba, out_dir / f"{lump(PM_SPRITE, c.key, frame, rot)}.png", core.grab_offsets(PM_CV))
            out["pm"][(c.key, frame, rot)] = rgba
            print(lump(PM_SPRITE, c.key, frame, rot), flush=True)
        out["metrics"]["pm"][c.key] = measure(out["pm"][(c.key, "A", 1)], PM_SCENES)
    for var in SCHWER:
        for rot in (1, 5):
            rgba = render_schwer(PM_RECOMMENDED, var, rot, seed)
            save(rgba, out_dir / f"{PM_SPRITE}_schwer_{var}_A{rot}.png", core.grab_offsets(PM_CV))
            out["schwer"][(var, rot)] = rgba
            print(f"schwer {var} A{rot}", flush=True)
        out["metrics"]["schwer"][var] = measure(out["schwer"][(var, 1)], PM_SCENES)
    (out_dir / "metrics.json").write_text(json.dumps(out["metrics"], indent=2) + "\n", encoding="utf-8")
    return out


def db_figure(rgba: np.ndarray) -> tuple[np.ndarray, int, int]:
    gx, gy = db_grab()
    return rgba, gx, gy + HOVER


def pm_figure(rgba: np.ndarray) -> tuple[np.ndarray, int, int]:
    return (rgba, *core.grab_offsets(PM_CV))


def write_lineups(data: dict, out_dir: Path = OUT_DIR) -> dict:
    """The 1x lineups: the four cells, the two approved infantries, the placeholder."""
    res = {}
    for enemy, cells, scenes, fig, ph, hover in (
            ("db", DB_CELLS, DB_SCENES, db_figure, "HEADA1", HOVER),
            ("pm", PM_CELLS, PM_SCENES, pm_figure, "BOS2A1", 0)):
        figs = [fig(data[enemy][(c.key, "A", 1)]) for c in cells]
        labels = [f"{DB_SPRITE if enemy == 'db' else PM_SPRITE} {c.key}" for c in cells]
        rf, rl = references(ph, hover)
        figs += rf
        labels += rl
        for key, wall, light, _ in scenes:
            sc = tall_lineup(figs, wall, light, LINEUP_SLOT * len(figs))
            Image.fromarray(sc, "RGB").save(out_dir / f"lineup_{enemy}_{key}.png", optimize=True)
            res[(enemy, key)] = sc
        res[(enemy, "labels")] = labels
    return res


# ==================================================================== sheet
DB_RECOMMENDED = "C"
PM_RECOMMENDED = "C"
# Written after looking at the renders (PIPELINE stage 2); see the sheet.
DB_VERDICT = [
    "RECOMMENDED: C, the severed head. The lore joke of BESTIARY 7 (the thing kept the helmet and lost the "
    "body) made literal: a torn neck under the sphere, the spine hanging out of it, dark-red drip (D49). It "
    "is the only cell whose 16-px silhouette is more than an egg (the stump is a tail under the circle), and "
    "it is on the line the CEO has approved so far: grotesque, serious, bleeding dark red. Valid "
    "combination: C's stump under B's Brodie helmet, which gives the top a brim at 16 px as well.",
    "B, the Brodie: the flat 'soup bowl' the AEF actually wore in 1917; 'Doughboy' is that war's word, the "
    "M1 pot is 1941. Its brim is the helmet tell that survives at 16 px. A is the brief taken literally. D "
    "puts the trooper's chrome M1 on him and a steel grille for a jaw (1950s chrome): the most 'Liberty "
    "Legion', but chrome on top breaks BESTIARY 10 rule 5 (dark helmet on top, for the lamps), and it has "
    "the lowest separation against the lamp flat (H3).",
]
PM_VERDICT = [
    "RECOMMENDED: C, the walking Panzer. MAP01 puts him in Z10, the darkest room of the map (light 96), "
    "and BESTIARY 10 rule 3 says the brute disappears there. C answers it with the one thing that reads in "
    "the dark: a lit visor slit, two yellow eyes in a black slab. The exhaust stacks are its shoulder "
    "horns and the side skirts widen the hips, so the 'rectangle with horns' of BESTIARY 8 holds from the "
    "front and the back. The lit slit is one material and fits any cell: 'D with C's slit' is a valid "
    "combination if you prefer the man under the iron.",
    "A is the brief: riveted black slab, spiked pauldrons, a visor slit, the red banner on his back with "
    "the D12 symbol (rotation 5). B puts a giant Stahlhelm on him, the Reich's helmet, but at 1x it reads "
    "as a rounded head more than as a Stahlhelm. D is the most brutal: a bald khaki skull with an iron mask "
    "bolted on, bare arms, bolts through the flesh that seep dark red.",
    "MEASURED. 68-75 px tall (BOS2 is 69; the rifleman 56), 44 wide. Body luma 47-59, the darkest mass in "
    "the game as BESTIARY 2.1 wants, below the rifleman's 63-75. In Z10 at 96 he separates from SDCONC1 on "
    "almost every pixel (a black shape on lighter concrete) and from the SDSTEL1 dado on about 73 %.",
]
SCHWER_NOTE = [
    "TODAY. SD_PanzermenschSchwer inherits every state of SD_Panzermensch: same sprites, so in game the two "
    "are told apart only by the time they take to die. BESTIARY 2.7 planned a Translation (a palette "
    "recolour) once SDPM lands.",
    "WHY NOT A TRANSLATION, AS PLANNED. A Translation remaps palette indices. Our sprites are truecolour "
    "PNGs and the mod ships no PLAYPAL, so GZDoom would remap them through Freedoom's palette: what the "
    "Schwer would look like is NOT VERIFIED and probably not our colours. The rig makes the alternative "
    "cheap: render the Schwer as a sprite set of its own (about 47 lumps, the same script, minutes of "
    "compute) under a new sprite name, and mod-engineer gives SD_PanzermenschSchwer its own States block "
    "(about 20 lines). The name (SDPS is not in BESTIARY 2.3's lists) is mod-engineer's to check against "
    "MOD-SPEC 6.3.",
    "TWO CANDIDATES, on cell C. S1, Dunkelgelb: the plate in the late-war German armour yellow (khaki_olive "
    "4-12), Panzergrau then Dunkelgelb as in 1943. It is the clearest tell, the Doom way (the Baron and the "
    "Hell Knight differ by colour), but it costs legibility: his value moves onto the concrete's (pixels "
    "that separate from SDCONC1 at 96 drop from 98 % to 33 %), and a light Reich brute leans towards the "
    "Legion's 'light faction'. S2, Schwer: still black, 12 % bigger, with both the spikes and the stacks. "
    "It keeps every number of the base cell, but size reads only side by side, and 12 % at an unknown "
    "distance is a weak tell.",
    "RECOMMENDATION: S2, as its own sprite set, keeping the dark mass. If you want a tell that reads at a "
    "glance, the next step is S2 with Dunkelgelb only on the pauldrons and the helm (the mass stays dark); "
    "that is one parameter, not drawn here.",
]
HONEST = [
    "DOUGHBOY. (1) Size: BESTIARY 7 says 'the size of a man's torso', but the actor has Cacodemon parity "
    "(radius 31, a 62-unit hitbox). Drawn torso-sized (about 18 px), shots would hit where nothing is "
    "drawn, so he is drawn to his hitbox: 50 px across, as big as Freedoom's HEAD. If you want him smaller, "
    "his Radius shrinks with him (mod-engineer, balance). (2) Value: his mean luma (141-170) sits on "
    "SDCONC1's 147, so cells A-C have a mean gap of 0-4 in the hangar, the worst of any enemy. The mean misleads for a two-tone "
    "figure (light pink, dark helmet): 82-94 % of his pixels separate from the wall in every scene, and hue (pink on "
    "grey-blue) helps; NOT VERIFIED in engine. (3) At 16 px A and D are an egg: the 'flat notch on top' is "
    "not readable; only B's brim and C's stump survive. (4) The veins read at 1x as fine cracks, not as "
    "veins. (5) In profile (rotation 3) the hanging lip shows as a small knob.",
    "PANZERMENSCH. (1) At 16 px the four cells are nearly the same shape (a rectangle with two horns); the "
    "choice between them is made at 1x, not at range. (2) In profile he is thin (23 px): plate seen edge "
    "on. He is a slab only from the front. (3) The contract's 'black plate' (true black and khaki_olive "
    "0-3) reads as a very dark olive, not as a neutral black: those are the Reich's only dark colours. "
    "(4) C's lit slit: a GZDoom 'Bright' frame lights the WHOLE sprite, not the slit. For the slit alone to "
    "glow in the dark it needs a brightmap (GLDEFS, hardware renderer), NOT VERIFIED here and "
    "mod-engineer's. Without one it is yellow paint; the lineup at 96 shows that case, and it still reads, "
    "dimmer. (5) C's rust stacks may read at range as two clubs carried on his back. (6) The attack (G1) is "
    "the overarm moment with the shell over his head; the wind-up frames E and F are not drawn yet.",
    "BOTH. Light is gen_enemy's stand-in (RGB x L/224), NOT VERIFIED against GZDoom. The Doughboy's hover "
    "height comes from memory of P_ZMovement, NOT VERIFIED. Nothing here has been in the engine.",
]
CEO_ASK = [
    "Doughboy: approve C (recommended), or C with B's Brodie, or name another cell. Then its 36 images "
    "(float, attack, pain at 8 rotations; the death that sinks) and the shell's 5 are rendered on the rig, "
    "for your gate in GZDoom.",
    "Panzermensch: approve C (recommended), or 'D with C's lit slit'. Then its 47 images and the shell's 5.",
    "Schwer: approve S2 as a sprite set of its own (recommended), or S1 Dunkelgelb. Either way it is a "
    "second sprite set, not a Translation, and mod-engineer gives the class its own States.",
    "One deviation to ratify: the Doughboy drawn to its hitbox (Cacodemon size), not 'torso-sized'.",
]

EXTRA_CSS = core.SHEET_CSS + """
.cards{display:flex;flex-direction:column;gap:14px}
.num{font:12px Menlo,monospace;color:var(--mute);margin:0 0 10px}
"""


def _tile(arr: np.ndarray, zoom: int, cap: str, sub: str = "") -> str:
    return core.sprite_tile(arr, zoom, cap, sub)


def _img_tile(rgb: np.ndarray, zoom: int, cap: str, sub: str = "") -> str:
    return core.tile(core.png_uri(rgb), rgb.shape[1], rgb.shape[0], zoom, cap, sub)


def _strip(items) -> str:
    return '<div class="strip">' + "".join(items) + "</div>"


def _cards(sprite: str, cells, views, sprites: dict, metrics: dict, recommended: str, frame_names: dict) -> str:
    out = []
    for c in cells:
        m = metrics[c.key]
        rec = c.key == recommended
        big = [_tile(sprites[(c.key, f, r)], 3, f"{sprite}{f}{r}",
                     ROT_NAMES[r] if f == "A" else frame_names[f]) for f, r in views]
        one = [_tile(sprites[(c.key, f, r)], 1, f"{f}{r} 1x") for f, r in views]
        sil = silhouette_rgb(sprites[(c.key, "A", 1)])
        sil3 = silhouette_rgb(sprites[(c.key, "A", 3)])
        sils = [_img_tile(sil, 4, "16 px, front", "shown 4x"), _img_tile(sil3, 4, "16 px, side", "shown 4x"),
                _img_tile(sil, 1, "16 px 1x")]
        facts = (f'{m["height_px"]} x {m["width_px"]} px · body luma {m["body_luma"]:.0f} (median {m["mass_luma"]:.0f}) · '
                 + " ".join(f"gap {k[4:]} {v:.0f}" for k, v in m.items() if k.startswith("gap_")))
        out.append(f'<div class="card{" rec" if rec else ""}">'
                   + ('<span class="tag">recommended</span>' if rec else "")
                   + f"<h3>{c.key} · {html.escape(c.title)}</h3><p class=\"num\">{html.escape(facts)}</p>"
                   + _strip(big) + _strip(one + sils) + "</div>")
    return '<div class="cards">' + "".join(out) + "</div>"


def _lineup_body(lines: dict, enemy: str, scenes) -> str:
    body = ""
    for key, wall, light, what in scenes:
        sc = lines[(enemy, key)]
        body += _strip([_img_tile(sc, 1, f"{key} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{key} 2x, for the eye")])
    worst = lines[(enemy, scenes[0][0] if enemy == "pm" else scenes[1][0])]
    farv = flat.far(worst)
    val = np.repeat(flat.luma(farv)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
    body += _strip([_img_tile(farv, 5, "game distance /4", "worst scene"),
                    _img_tile(val, 5, "the same, value only")])
    body += ('<p class="lead">Left to right: ' + html.escape(" · ".join(lines[(enemy, "labels")]))
             + ". Each sprite stands (or hangs) by its own offsets, as the engine places it.</p>")
    return body


def build_sheet(data: dict, lines: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    S = []
    met = data["metrics"]
    rows = [[c.key + (" (rec.)" if c.key == DB_RECOMMENDED else ""), c.helmet, c.mouth,
             "severed" if c.severed else "-"] for c in DB_CELLS]
    rows += [[f"PM {c.key}" + (" (rec.)" if c.key == PM_RECOMMENDED else ""), c.head, c.top,
              "lit visor" if c.lit_visor else "-"] for c in PM_CELLS]
    S.append(("1 · Two decisions, four cells each", "",
              sheetlib.table(["cell", "helmet / head", "mouth / shoulders", "extra"], rows, 99)))

    S.append(("2 · Doughboy (SDDB): the cells at 3x, then 1x and the 16-px silhouette",
              "BESTIARY §7: a pink, veined sphere of flesh, one huge lidless eye, a slack mouth, a battered "
              "steel M1 strapped on top with a chinstrap that goes nowhere; dark helmet on top (§10 rule 5). "
              "Rotation 1 (front), 3 (its left side), 5 (its back) and D1, the attack (SD_DoughboyShell leaving "
              "the mouth: white-hot steel_blue core, flag_red trail). Flesh is palette v2's flesh_pink (D45).",
              _cards(DB_SPRITE, DB_CELLS, DB_VIEWS, data["db"], met["db"], DB_RECOMMENDED,
                     {"D": "attack, the shell"})))
    S.append(("3 · Doughboy at 1x in the hangar, beside the approved rifleman and trooper",
              f"The four cells hung {HOVER} px above the floor (a floater's height beside a 56-unit man, from "
              "memory of P_ZMovement: NOT VERIFIED), then SDRRA1 and SDLTA1 from assets/ (approved), then "
              "Freedoom's HEADA1 hung the same way. Light is gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.",
              _lineup_body(lines, "db", DB_SCENES)))

    S.append(("4 · Panzermensch (SDPM): the cells at 3x, then 1x and the 16-px silhouette",
              "BESTIARY §8: a man-shaped slab of riveted black plate, gauntlets too big for him, no face behind "
              "the visor slit, a red banner panel bolted to his back (D12; rotation 5). Rotation 1, 3, 5 and G1, "
              "the attack (SD_PanzerShell leaving the right gauntlet: dull hazard_yellow core, olive smoke "
              "edge). Palette v1 only; the reused cloth takes the rifleman's value shift.",
              _cards(PM_SPRITE, PM_CELLS, PM_VIEWS, data["pm"], met["pm"], PM_RECOMMENDED,
                     {"G": "attack, the throw"})))
    S.append(("5 · Panzermensch at 1x in Z10, beside the approved rifleman and trooper",
              "Z10 is where MAP01 puts him: the darkest room of the map, light 96, SDCONC1 over an SDSTEL1 "
              "dado, 144 on the exit switch. Then SDRRA1, SDLTA1 (approved) and Freedoom's BOS2A1.",
              _lineup_body(lines, "pm", PM_SCENES)))

    sils = []
    for c in DB_CELLS:
        sils.append(_img_tile(silhouette_rgb(data["db"][(c.key, "A", 1)]), 5, f"SDDB {c.key}"))
    for c in PM_CELLS:
        sils.append(_img_tile(silhouette_rgb(data["pm"][(c.key, "A", 1)]), 5, f"SDPM {c.key}"))
    for name, folder in (("SDRRA1", "rifleman"), ("SDLTA1", "legion")):
        r = approved(name, folder)
        if r:
            sils.append(_img_tile(silhouette_rgb(r[0]), 5, name, "approved"))
    for name in ("HEADA1", "BOS2A1"):
        fd = core.freedoom_sprite(name)
        if fd:
            sils.append(_img_tile(silhouette_rgb(fd[0]), 5, name, "placeholder"))
    S.append(("6 · Every cell at 16 px (ART-BIBLE §6.4), beside the approved infantries",
              "Black shape, 16 px tall, shown 5x. Front views.", _strip(sils)))

    base = data["pm"][(PM_RECOMMENDED, "A", 1)]
    tiles = [_tile(base, 3, f"SDPM {PM_RECOMMENDED}", "SD_Panzermensch, 500 HP")]
    for var, v in SCHWER.items():
        tiles.append(_tile(data["schwer"][(var, 1)], 3, f"Schwer {var}", v["title"]))
    tiles.append(_tile(data["schwer"][("S2", 5)], 3, "Schwer S2, back"))
    figs = [pm_figure(base), pm_figure(data["schwer"][("S1", 1)]), pm_figure(data["schwer"][("S2", 1)])]
    rf, _ = references("BOS2A1")
    figs += rf[:2]
    sc = tall_lineup(figs, "SDCONC1", 96, LINEUP_SLOT * len(figs))
    sc2 = tall_lineup(figs, "SDCONC1", 144, LINEUP_SLOT * len(figs))
    Image.fromarray(sc, "RGB").save(OUT_DIR / "lineup_schwer_Z1.png", optimize=True)
    sils = [_img_tile(silhouette_rgb(f[0]), 5, n) for f, n in zip(figs[:3], ("SDPM", "S1", "S2"))]
    rows = [[k, m["height_px"], m["body_luma"], m["gap_Z1"], m["gap_Z2"], m["gap_Z3"]]
            for k, m in [("SDPM " + PM_RECOMMENDED, met["pm"][PM_RECOMMENDED])] + list(met["schwer"].items())]
    body = (_strip(tiles) + _strip([_img_tile(sc, 2, "Z1 at 96, 2x", "SDPM, S1, S2, SDRRA1, SDLTA1"),
                                    _img_tile(sc2, 2, "Z3 at 144, 2x")] + sils)
            + sheetlib.table(["figure", "h px", "body luma", "gap Z1", "gap Z2", "gap Z3"], rows)
            + '<div class="verdict">' + "".join(f"<p>{html.escape(p)}</p>" for p in SCHWER_NOTE) + "</div>")
    S.append(("7 · The Schwer: today identical; how to tell it apart", "", body))

    body = '<div class="verdict">'
    for title, paras in (("Doughboy", DB_VERDICT), ("Panzermensch", PM_VERDICT), ("What does not work, honestly", HONEST)):
        body += f"<h3>{html.escape(title)}</h3>" + "".join(f"<p>{html.escape(p)}</p>" for p in paras)
    body += "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in CEO_ASK) \
            + "</ol></div>"
    S.append((f"8 · Recommendation: Doughboy {DB_RECOMMENDED}, Panzermensch {PM_RECOMMENDED}", "", body))

    intro = ("D35: the two heavies still on Freedoom placeholders, the Doughboy (<code>SD_Doughboy</code>, BESTIARY "
             "§7) and the Panzermensch (<code>SD_Panzermensch</code>, §8), drawn on the 3D rig the four approved "
             "enemies were drawn on. One decision per enemy before ~80 images: what it looks like. Four cells "
             "each, rotations 1, 3, 5 and the attack, every cell at 1x on MAP01 beside the approved rifleman and "
             "Legion trooper, and its 16-px silhouette; then how to tell the 1000 HP Schwer apart. Built by "
             "<code>tools/art/gen_heavy.py</code> on <code>tools/art/rig_core.py</code> (imported, not edited), "
             f"palette v2 (flesh_pink on the Doughboy only), seed {SEED}, no system fonts. "
             "Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_heavy.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Approved sprites read from assets/sprites/ (rifleman, legion). Freedoom sprites "
              "shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause (© the Freedoom contributors), "
              "not used as a source.")
    path = out_dir / f"{stamp}_F5_doughboy-panzermensch-sweep.html"
    sheetlib.write_sheet(path, lang="en", title="Doughboy and Panzermensch — design sweeps (F5, D35)",
                         subtitle="SDDB · SDPM · 4 + 4 cells on the rig · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    ap.add_argument("--no-sheet", action="store_true")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_all()
    lines = write_lineups(data)
    print(json.dumps(data["metrics"], indent=1))
    if not args.no_sheet:
        print(build_sheet(data, lines, args.stamp))


if __name__ == "__main__":
    main()
