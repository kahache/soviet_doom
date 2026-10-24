"""F5 — the two heavies, Doughboy and Panzermensch: design sweeps on the 3D rig (D35).

HISTORICAL since D109 (2026-10-22) for the Doughboy's and the Panzermensch's
rig sets (`SDDB`, `SDPM`, `SDPS`, D65-D70). The heavies that ship is redrawn
from Google Gemini images by tools/art/gemini_enemy.py (doughboy, panzer,
panzer_heavy); this generator is kept so the approved F5 renders stay
reproducible, but its output no longer matches assets/.

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
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
if str(ART_TOOLS) not in sys.path:
    sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (light stand-in, far view, silhouette, luma)
import gen_hound as hound  # noqa: E402  (the full sets: zs_states, settle_part, pool, crop_common, _gif_runs)
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
# D67 (CEO, 2026-10-14, on the Doughboy's full set): "ponle la bandera más
# grande en la cabeza" ("make the flag on its head bigger"). The full set's decal: 11 x 7 instead of 5 x 4, a
# canton with stars and seven stripes, so it reads at 1x. The sweep keeps
# its own small DECAL (its PNGs do not change).
DECAL_BIG = (
    "BBBBBRRRRRR",
    "B*B*BWWWWWW",
    "BB*BBRRRRRR",
    "B*B*BWWWWWW",
    "RRRRRRRRRRR",
    "WWWWWWWWWWW",
    "RRRRRRRRRRR",
)
DECAL_BIG_INSIGNIA = core.Insignia("decal", (len(DECAL_BIG[0]), len(DECAL_BIG)),
                                   core.pattern_drawer(DECAL_BIG, legion.FLAG_COLOURS), outward=(0.0, 0.0, 1.0),
                                   min_px=24, search=3, turned_away=0.35)
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


def _db_mouth(cell: DBCell, attack: bool, add, sphere: core.Prim, opening: float | None = None) -> np.ndarray:
    """The mouth; returns the point the shell leaves from. `opening` (the
    full set's poses) overrides the slack mouth's half height."""
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
    opn = (6.0 if attack else 3.4) if opening is None else opening
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


def db_model(cell: DBCell, frame: str = "A", seed: int = SEED,
             pose: "DBPose | None" = None) -> tuple[list[core.Prim], np.ndarray]:
    """The Doughboy in rig_core's model space (the actor's z on y=0, facing
    +z, +x its LEFT). Returns (prims, the point the shell leaves from).
    `pose` (the full set, D65) varies the mouth, the eye, the shell and the
    head's tilt; with none, frame A or D is the sweep's figure, unchanged."""
    rng = np.random.default_rng(seed)
    P: list[core.Prim] = []
    add = add_to(P)
    attack = frame == "D" if pose is None else pose.gape
    sphere = add("head", core.ellipsoid("flesh", 0.78, tuple(DB_C), (DB_R, DB_R * 0.97, DB_R)))
    for v in _veins(rng):
        add("head", v)
    # the lidless eye: a raw rim, the sclera, a cold blue iris, the pupil
    for lump_ in _lumps(rng):
        add("head", lump_)
    add("head", core.ellipsoid("raw", 0.40, tuple(DB_C + EYE_DIR * (DB_R - 4.4)), (11.6, 10.2, 6.6)))
    if pose is not None and pose.eye == "burst":
        _db_burst_eye(add)
    else:
        pk = 1.0 if pose is None else pose.pupil
        add("head", core.ellipsoid("sclera", 0.66, tuple(DB_C + EYE_DIR * (DB_R - 4.0)), (10.2, 9.0, 7.0)))
        add("head", core.ellipsoid("iris", 0.55, tuple(DB_C + EYE_DIR * (DB_R + 2.4)), (5.0, 5.0, 1.3)))
        add("head", core.ellipsoid("pupil", 0.0, tuple(DB_C + EYE_DIR * (DB_R + 3.4)), (2.3 * pk, 2.7 * pk, 0.6)))
    muzzle = _db_mouth(cell, attack, add, sphere, None if pose is None else pose.mouth)
    if attack and cell.mouth == "bumper":
        hinge = V(0.0, DB_C[1] + MOUTH_DIR[1] * DB_R + 2.0, 4.0)
        core.transform(P, {}, {"jaw"}, core.rot_x(-18.0), hinge, V(0, -3.0, 0.5))
    helmet = _db_helmet(cell, add)
    knock = 0.0 if pose is None else pose.knock
    core.transform(P, {}, {"helmet"}, core.rot_z(-HELMET_TILT - knock), DB_C)      # askew, to his right
    del helmet
    if cell.severed:
        _db_severed(add, rng)
    shell = ("out" if attack else "") if pose is None else pose.shell
    if shell == "out":      # SD_DoughboyShell leaving the mouth: white-hot core, red trail behind it
        add("shell", core.ellipsoid("sdl_trail", 0.6, tuple(muzzle + V(0, 0, 1.0)), (4.6, 4.2, 3.0)))
        add("shell", core.ellipsoid("sdl_core", 0.8, tuple(muzzle + V(0, 0, 3.4)), (2.9, 2.9, 2.0)))
    elif shell == "glow":   # B: the shell kindles deep in the throat
        add("shell", core.ellipsoid("sdl_trail", 0.45, tuple(muzzle + V(0, 0, -3.2)), (3.4, 2.6, 2.0)))
    elif shell == "core":   # C: white-hot in the open mouth, the red trail round it
        add("shell", core.ellipsoid("sdl_trail", 0.55, tuple(muzzle + V(0, 0, -1.6)), (4.4, 3.6, 2.4)))
        add("shell", core.ellipsoid("sdl_core", 0.75, tuple(muzzle + V(0, 0, -0.4)), (2.4, 2.4, 1.6)))
    if pose is not None:
        _db_pose_extras(pose, add)
        groups = {p.grp for p in P}
        if pose.roll:
            core.transform(P, {}, groups, core.rot_z(pose.roll), DB_C)
        if pose.pitch:
            core.transform(P, {}, groups, core.rot_x(pose.pitch), DB_C)
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
    # The full set's posing (D65); every default leaves the sweep's figure as it was.
    title: str = ""
    bob: float = 0.0            # units the hips (and all above them) drop: the knees bend
    twist: float = 0.0          # degrees about the waist; + brings his LEFT shoulder forward
    lean: float = 0.0           # degrees sideways about the waist; + tips him to his left
    head_pitch: float = 0.0     # degrees about the neck; + tips the head back (chin up)
    head_turn: float = 0.0      # degrees about the neck; + turns the face to his left
    charge: float = 0.0         # a shell forming in the right fist (its size, 1 = the thrown one)
    throw_arm: bool = False     # the right elbow bends as in the throw (pole down and out)
    spurt: float = 0.0          # pain: s since a round opened the chest (a few drops fly)
    arm_z: float = 0.0          # the dead: the arms shifted towards the floor side (a slack shoulder rolls)
    leg_z: float = 0.0          # ... and the legs (the hips settle: a thigh is as deep as the faulds)


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


def pm_model(cell: PMCell, frame: str = "A", plate: str = "plate", seed: int = SEED,
             pose: PMPose | None = None, anchors: dict | None = None) -> list[core.Prim]:
    """The Panzermensch in rig_core's model space (feet on y=0, facing +z,
    +x his LEFT), posed. `plate` names the armour's material (the Schwer's
    recolour candidate swaps it). `pose` overrides PM_POSES[frame] (the full
    set); `anchors`, when given, is filled with the joints, posed, as
    rig_core anchors {name: (point, group)}."""
    pose = PM_POSES[frame] if pose is None else pose
    anch: dict = {} if anchors is None else anchors
    P: list[core.Prim] = []
    add = add_to(P)

    def label(start: int, limb: str, side: int) -> None:
        for q in P[start:]:
            q.limb, q.side = limb, side

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((core.LEFT, pose.foot_l, "leg_l"), (core.RIGHT, pose.foot_r, "leg_r")):
        start = len(P)
        hip = V(side * PM_HIP_X, PM_HIP_Y + pose.bob, 0.0)
        knee, ankle = core.two_bone(hip, foot, PM_THIGH, PM_SHIN, V(0, 0, 1))
        s = "l" if side == core.LEFT else "r"
        anch[f"hip_{s}"], anch[f"knee_{s}"], anch[f"ankle_{s}"] = (hip, grp), (knee, grp), (ankle, grp)
        add(grp, core.rcone("plate", 0.50, hip, knee, 4.7, 4.0))                                   # cuisse
        add(grp, core.ellipsoid("flesh", 0.40, tuple(knee + V(0, 0, -2.2)), (2.8, 2.6, 2.0)))     # the joint shows
        add(grp, core.ellipsoid("plate", 0.62, tuple(knee + V(0, 0.3, 1.8)), (3.8, 3.4, 2.8)))   # knee cop
        add(grp, core.rcone("plate", 0.46, knee, ankle + V(0, 2.0, 0), 4.0, 3.5))                  # greave
        add(grp, core.box("plate", 0.38, (ankle[0], ankle[1] - 1.5, ankle[2] + 1.8), (3.0, 1.7, 4.8), rnd=0.9))
        add(grp, core.ellipsoid("rivet", 0.6, tuple(knee + V(0, 0.4, 4.4)), (0.8, 0.8, 0.6)))
        if cell.top in ("stacks", "both"):     # Schürzen: a side skirt plate hung from the belt
            add(grp, core.box("plate", 0.46, (side * 11.4, 23.0 + pose.bob, 0.0), (0.6, 7.0, 7.0), rnd=0.3))
            for z in (-4.5, 4.5):
                add(grp, core.ellipsoid("rivet", 0.6, (side * 12.0, 28.4 + pose.bob, z), (0.5, 0.8, 0.8)))
        label(start, "leg", side)
    add("upper", core.ccone("plate", 0.48, 24.5, 34.0, 10.8, 9.6, kz=0.84, tag="faulds"))                    # faulds
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
        throw = (pose.shell or pose.throw_arm) and side == core.RIGHT
        pole = V(side * 1.0, -1.0, -0.4) if throw else V(side * 1.0, -0.3, -1.0)
        elbow, wrist = core.two_bone(sh, grips[side], PM_UPPER_ARM, PM_FOREARM, pole)
        fd = unit(wrist - elbow)
        s = "l" if side == core.LEFT else "r"
        anch[f"shoulder_{s}"], anch[f"elbow_{s}"], anch[f"wrist_{s}"] = (sh, "arm"), (elbow, "arm"), (wrist, "arm")
        anch[f"fist_{s}"] = (wrist + fd * 4.2, "arm")
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
        if side == core.RIGHT and pose.charge:      # E, F: the shell forming in the gauntlet's grip
            k = pose.charge
            s = fist + fd * 4.6
            add("shell", core.ellipsoid("pzl_smoke", 0.5, tuple(s), (4.0 * k, 4.0 * k, 4.0 * k)))
            add("shell", core.ellipsoid("pzl_shell", 0.6, tuple(s + fd * 0.8), (2.8 * k, 2.9 * k, 2.8 * k)))
            add("shell", core.ellipsoid("pzl_core", 0.8, tuple(s + fd * 1.6), (1.4 * k, 1.5 * k, 1.4 * k)))

    if pose.arm_z:
        core.transform(P, anch, {"arm"}, np.eye(3), V(0, 0, 0), V(0, 0, pose.arm_z))
    if pose.leg_z:
        core.transform(P, anch, {"leg_l", "leg_r"}, np.eye(3), V(0, 0, 0), V(0, 0, pose.leg_z))
    anch["neck"] = (V(0.0, 56.0, 0.0), "upper")
    anch["crown"] = (V(0.0, 68.0, 0.6), "helmet")
    anch["waist"] = (PM_WAIST.copy(), "upper")

    # ------------------------------------------------------------- posing
    if pose.head_turn:
        core.transform(P, anch, {"helmet"}, core.rot_y(pose.head_turn), anch["neck"][0])
    if pose.head_pitch:
        core.transform(P, anch, {"helmet"}, core.rot_x(pose.head_pitch), anch["neck"][0])
    if pose.twist:
        core.transform(P, anch, PM_UPPER, core.rot_y(pose.twist), PM_WAIST)
    if pose.hunch:
        core.transform(P, anch, PM_UPPER, core.rot_x(-pose.hunch), PM_WAIST)
    if pose.lean:
        core.transform(P, anch, PM_UPPER, core.rot_z(pose.lean), PM_WAIST)
    if pose.bob:
        core.transform(P, anch, PM_UPPER, np.eye(3), V(0, 0, 0), V(0, pose.bob, 0))
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


# ================================================================ the full sets (D65)
# D65 (CEO, 2026-10-14): "Doughboy C · Panzermensch D", and the Schwer is
# the PM's call: cell D with the sweep's S2 treatment (black plate, 12 %
# larger, spikes and stacks, lit slit), a sprite set of its own. This
# section renders every frame the three classes' states name, with the
# letters and tics read from their ZScript files (read, never edited):
#
#   SD_Doughboy (doughboy.zs, on Freedoom's HEAD today): Spawn A, See A,
#     Missile B C D, Pain E E F, Death G H I J K L (L held). No XDeath, so
#     no gib. 8 rotations for A-F, rotation 0 for G-L: 54 lumps SDDB.
#   SD_Panzermensch (panzermensch.zs, on BOS2): Spawn A B, See A-D,
#     Melee/Missile E F G, Pain H, Death I-N and O held. No XDeath. 8
#     rotations for A-H, 0 for I-O: 71 lumps SDPM.
#   SD_PanzermenschSchwer: today it inherits SD_Panzermensch's states. Its
#     own set is the same 71 frames under the proposed name SDPS (the
#     mod-engineer's change is in the sheet and in SCHWER_HANDOFF).
#
# Eight drawn rotations, no mirrored pairs: both figures are handed. The
# Doughboy's helmet sits askew to its right with the flag decal and the
# buckle on one side; the Panzermensch's back banner carries the D12
# symbol (a mirror reverses it) and he throws with his right.
#
# The sweep's pixels the CEO chose stay: SDDB A1 A3 A5 D1 are the sweep's
# SDDB_C_* and SDPM A1 A3 A5 G1 the sweep's SDPM_D_*, byte for byte.
#
# The dead (the CEO's rule since the Legion's first L0, "parece que se
# apoye en el hombro", "it looks as if it leans on its shoulder"): the corpse lies with its weight on the floor and
# is measured, not judged by eye. The Doughboy, a floater, drops when it
# dies (GZDoom's Die() clears +FLOAT and +NOGRAVITY: NOT VERIFIED here, it
# is what every dead cacodemon does) and lands as a deflated sack, the
# helmet knocked off beside it and the spine on the floor; the
# Panzermensch falls back over his heels, twisting across the screen, and
# his head, arms and legs are each let fall about their joint until they
# touch (gen_hound.settle_part, bisection on rig_core.lowest_y). Blood is
# D49's: dark red, flag_red 0-5 and black, abundant.
#
# As the approved hound's death (gen_hound.DEATH_TILT), the frames on the
# floor are drawn from higher, ramping in as they fall: a player looks
# down at a corpse. The Doughboy's ramp stops at 18 degrees (27 in all):
# its sack is 50 units across, and from the hound's 28 its top filled a
# disc taller on screen than any approved corpse. Only the render is tipped; the lying test measures the
# model on its floor.
FULL_DIR = OUT_DIR / "full"
ZS_DIR = PROJECT_ROOT / "src" / "zscript" / "monsters"
DB_ZS = ZS_DIR / "doughboy.zs"
PM_ZS = ZS_DIR / "panzermensch.zs"
PS_ZS = ZS_DIR / "panzermensch_schwer.zs"
DB_FULL_KEY = "C"               # D65
PM_FULL_KEY = "D"               # D65
PS_SPRITE = "SDPS"              # proposed: free of every reserved prefix (BESTIARY 2.3, MOD-SPEC 6.3)
BLOOD_GRAVITY = 400.0           # units / s^2, as every approved death's droplets
TIC_S = 1.0 / 35


def zs_states(path: Path) -> dict[str, list[tuple[str, int]]]:
    """A class's state labels and their (frame letter, tics), read from its
    ZScript file (gen_hound's reader; the sprite name is ignored)."""
    return hound.zs_states(path)


def zs_frames(path: Path) -> tuple[str, str]:
    """(the letters drawn at 8 rotations, the death letters at rotation 0):
    every letter of the living states, then Death's in order."""
    st = zs_states(path)
    living = sorted({f for lab, seq in st.items() if lab not in ("Death", "XDeath", "Raise") for f, _ in seq})
    death = "".join(dict.fromkeys(f for f, _ in st.get("Death", [])))
    return "".join(living), death


# ---------------------------------------------------------------- the Doughboy's poses
@dataclass(frozen=True)
class DBPose:
    key: str
    title: str
    mouth: float | None = None  # the slit's half height (None: the sweep's)
    gape: bool = False          # the attack's mouth: lower teeth, the tongue out, the lip dropped
    shell: str = ""             # "" | "glow" (deep in the throat) | "core" (in the mouth) | "out" (the sweep's D)
    pupil: float = 1.0          # the pupil's size (pain: a pinpoint)
    eye: str = "open"           # "open" | "burst" (the death)
    pitch: float = 0.0          # degrees the whole head tips back (+) about its centre
    roll: float = 0.0           # degrees it rolls (+: top to its left, screen right from the front)
    knock: float = 0.0          # degrees the helmet is knocked further askew
    wound: float = 0.0          # pain: s since a round opened its cheek (0: no wound)


DB_FULL_POSES = {
    "B": DBPose("B", "draws breath: the shell kindles in the throat", mouth=4.8, shell="glow", pitch=6.0),
    "C": DBPose("C", "the mouth gapes, the shell white-hot in it", mouth=6.4, gape=True, shell="core", pitch=-3.0),
    "E": DBPose("E", "hit: it jerks back and screams", mouth=7.0, gape=True, pupil=0.45, pitch=16.0, roll=9.0,
                knock=8.0, wound=0.05),
    "F": DBPose("F", "it rights itself, bleeding", mouth=4.6, pupil=0.7, pitch=7.0, roll=4.0, knock=4.0,
                wound=0.16),
    "G": DBPose("G", "killed: the eye bursts", mouth=5.6, gape=True, eye="burst", pitch=14.0, roll=-6.0,
                knock=14.0),
}
DB_FRAME_TITLES = {"A": "floats (the sweep's)", "D": "spits the shell (the sweep's)",
                   **{k: p.title for k, p in DB_FULL_POSES.items()}}
DB_WOUND_DIR = unit((0.66, 0.02, 0.75))     # its left cheek, beside the eye: screen right from the front
STAIN_DEPTH = 12.0              # a stain is a big sphere sunk in the surface: a thin cap, any orientation
STAIN_PROUD = 0.6               # ... standing this far proud of it


def _stain(mat: str, base: float, centre: np.ndarray, normal: np.ndarray, radius: float, depth: float = STAIN_DEPTH,
           grp: str = "head") -> core.Prim:
    """A flat cap of `radius` on a surface whose outward normal is `normal`
    at `centre`: a sphere sunk `depth` into it, STAIN_PROUD out of it."""
    rr = float(np.hypot(radius, depth))
    c = centre - normal * (rr - STAIN_PROUD)
    return core.ellipsoid(mat, base, tuple(c), (rr, rr, rr), grp=grp)


def _surface_run(start_dir: np.ndarray, drop: float, steps: int, r0: float, r1: float, radius: float = DB_R,
                 grp: str = "head", mat: str = "blood") -> list[core.Prim]:
    """A run of blood down the sphere from `start_dir`: segments on its surface."""
    pts = [DB_C + unit(start_dir + V(0, -drop * k / steps, 0)) * (radius + 0.25) for k in range(steps + 1)]
    out = []
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        out.append(core.rcone(mat, 0.42, a, b, r0 + (r1 - r0) * k / steps, r0 + (r1 - r0) * (k + 1) / steps, grp=grp))
    return out


def _db_burst_eye(add) -> None:
    """The death: the eye gone, a dark socket in the raw rim, rags of the
    sclera at its edge, blood welling in its lower lid."""
    c = DB_C + EYE_DIR * (DB_R - 3.0)
    add("head", core.ellipsoid("void", 0.05, tuple(c + EYE_DIR * 0.5), (8.4, 7.4, 5.2)))
    add("head", core.ellipsoid("blood", 0.40, tuple(c + EYE_DIR * 3.0 + V(0, -5.5, 0)), (6.5, 2.4, 2.6)))
    e1 = unit(np.cross(EYE_DIR, V(0, 1, 0)))
    e2 = np.cross(e1, EYE_DIR)
    for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
        d = e1 * np.cos(a) + e2 * np.sin(a)
        add("head", core.ellipsoid("sclera", 0.55, tuple(c + EYE_DIR * 2.6 + d * 8.6), (2.2, 2.0, 1.2)))


def _db_pose_extras(pose: DBPose, add) -> None:
    """Pain's wound: a hole in its left cheek, the stain, a run, a spurt."""
    if pose.eye == "burst":         # the socket runs down the face
        for dx, drop, steps in ((-0.10, 0.85, 5), (0.12, 1.05, 6)):
            for q in _surface_run(EYE_DIR + V(dx, -0.36, 0), drop, steps, 1.1, 0.7):
                add("head", q)
    if not pose.wound:
        return
    t = pose.wound
    w = DB_C + DB_WOUND_DIR * DB_R
    add("head", _stain("blood", 0.45, w, DB_WOUND_DIR, 3.6 + 6.0 * t))
    add("head", core.ellipsoid("void", 0.05, tuple(DB_C + DB_WOUND_DIR * (DB_R + 0.2)), (1.4, 1.5, 1.0)))
    for q in _surface_run(DB_WOUND_DIR + V(0, -0.1, 0), 0.5 + 3.0 * t, 3 if t < 0.1 else 5, 0.9, 0.6):
        add("head", q)
    rng = np.random.default_rng(SEED + 31)
    for _ in range(10):
        v = DB_WOUND_DIR * rng.uniform(25, 70) + V(rng.uniform(-8, 8), rng.uniform(0, 25), rng.uniform(-8, 8))
        p = w + v * t + V(0, -0.5 * BLOOD_GRAVITY * t * t, 0)
        r = rng.uniform(0.8, 1.2)
        add("spray", core.ellipsoid("blood", 0.62, tuple(p), (r, r * 1.15, r)))


# ---------------------------------------------------------------- the Doughboy's death
@dataclass(frozen=True)
class DBFall:
    """A death frame on the floor (H-L)."""
    title: str
    t: float                    # s after the kill
    squash: float               # the sack's height scale (1: round)
    spread: float               # its width and depth scale
    helmet: str                 # "flying" | "down"
    helmet_roll: float          # degrees the helmet is turned (upside down is 180)
    spine: float                # how far the spine has fallen out along the floor (0..1)
    pool: float                 # share of the full pool
    tilt: float                 # degrees the render looks further down (as gen_hound.DEATH_TILT)
    mouth: float
    back: float = 0.0           # degrees it has rolled back onto its crown (the face turns up)
    roll: float = 0.0           # degrees it has rolled to its side


DB_FALLS = {                    # doughboy.zs: G H I J K 8 tics, L held; G at the kill
    "H": DBFall("lands: it splits, the helmet flies", 0.30, 0.80, 1.10, "flying", -55.0, 0.55, 0.25, 6.0, 5.0,
                back=20.0, roll=4.0),
    "I": DBFall("rolls back, deflating", 0.53, 0.60, 1.16, "down", -165.0, 0.85, 0.50, 10.0, 4.6, back=38.0, roll=7.0),
    "J": DBFall("sinks", 0.76, 0.46, 1.21, "down", -152.0, 1.0, 0.70, 14.0, 4.2, back=46.0, roll=9.0),
    "K": DBFall("collapses", 0.99, 0.36, 1.25, "down", -148.0, 1.0, 0.88, 16.0, 3.8, back=50.0, roll=10.0),
    "L": DBFall("dead: a flat sack face up in its blood", 3.0, 0.28, 1.28, "down", -150.0, 1.0, 1.0, 18.0, 3.6,
                back=52.0, roll=10.0),
}
DB_G_T = 0.06                   # s after the kill, frame G (still in the air)
DB_HELMET_DOWN = V(38.0, 0.0, -12.0)     # where the knocked-off helmet lies: beside and behind the sack
DB_HELMET_FLY = V(24.0, 48.0, -4.0)      # ... and where it is in H, flying off
DB_SPINE = (V(-6.0, 0.0, 4.0), V(-44.0, 0.0, 14.0))   # the spine on the floor: from under the sack, out
DB_N_SPRAY = 44
DB_POOL = (46.0, 21.0)          # (x, z) radii of the full pool: it spreads out round the sack
DB_POOL_Z = 16.0
DB_STUMP_POOL = (12.0, 8.0)
DB_SPRAY_X = (-66.0, 80.0)      # landed splats stay inside the death canvas (check_edges)
DB_SPRAY_Z = (-20.0, 24.0)
DB_AIR_Y = 70.0
DB_NOSEVER = DBCell("C", "m1", "slack", False, "C without its hanging stump (the death lays its own)")
DB_DEATH_CV = core.Canvas(160, 108, 72, 80)
DB_DEATH_MATERIALS: dict[str, Mat] = dict(DB_MATERIALS)
core.register_material("pool", Mat.on_ramp("flag_red", 0, 3, black_floor=True, flat=True), DB_DEATH_MATERIALS)
DB_LYING_MAX = 2.0              # units: a part this far above the floor still lies on it
DB_LYING_TOP = 18.0             # nothing of the body (blood and the helmet aside) higher than this
DB_LYING_SPAN = 40.0            # the parts on the floor spread at least this far


def affine_prims(prims: list[core.Prim], A: np.ndarray, pivot) -> None:
    """Map primitives by the linear map A about `pivot`, in place: a body
    that tips over and deflates. Exact for ellipsoids (an ellipsoid's affine
    image is an ellipsoid: its axes and radii are the SVD of A, its old
    rotation and its radii); a round cone's ends are mapped and its radii
    take A's mean scale; a cut box is replaced by the box that holds its
    image (a little larger: a mouth cut stays open). Clip planes are not
    supported (the head has none)."""
    pivot = np.asarray(pivot, float)
    A = np.asarray(A, float)
    g = float(abs(np.linalg.det(A)) ** (1 / 3))
    for p in prims:
        if p.clip:
            raise ValueError("affine_prims: clip planes are not supported")
        w = lambda q: pivot + A @ (p.xm @ q + p.xt - pivot)  # noqa: E731  (old local -> new world)
        if p.kind == "ellipsoid":
            U, sig, _ = np.linalg.svd(A @ p.xm @ np.diag(np.asarray(p.r, float)))
            if np.linalg.det(U) < 0:
                U[:, -1] *= -1
            c = w(p.a)
            cuts = [(U.T @ w(cc), np.abs(U.T @ A @ p.xm) @ half) for cc, half in p.cut]
            p.xm, p.xt, p.a, p.r, p.cut = U, np.zeros(3), U.T @ c, sig, cuts
        elif p.kind == "roundcone":
            if p.cut:
                raise ValueError("affine_prims: a cut round cone is not supported")
            p.a, p.b = w(p.a), w(p.b)
            p.xm, p.xt = np.eye(3), np.zeros(3)
            p.r1, p.r2 = p.r1 * g, p.r2 * g
        else:
            raise ValueError(f"affine_prims: {p.kind} not supported")


def db_full_cell() -> DBCell:
    return DB[DB_FULL_KEY]


def _db_eye_at_g() -> np.ndarray:
    """Where the eye burst (frame G, model space): the burst's origin."""
    pose = DB_FULL_POSES["G"]
    e = DB_C + EYE_DIR * (DB_R + 1.0)
    e = core.rot_z(pose.roll) @ (e - DB_C) + DB_C
    return core.rot_x(pose.pitch) @ (e - DB_C) + DB_C


def _droplet(p0, v, t: float, r: float, xr, zr, air: float) -> core.Prim:
    """A drop `t` s after leaving p0 at v: in the air, or a flat splat once
    landed (the approved deaths' droplet, clamped to this canvas)."""
    p0, v = np.asarray(p0, float), np.asarray(v, float)
    rest = r * 0.3
    tl = (v[1] + np.sqrt(v[1] ** 2 + 2 * BLOOD_GRAVITY * max(p0[1] - rest, 0.0))) / BLOOD_GRAVITY
    tt = min(t, tl)
    p = p0 + v * tt + V(0, -0.5 * BLOOD_GRAVITY * tt * tt, 0)
    x, z = float(np.clip(p[0], *xr)), float(np.clip(p[2], *zr))
    if t >= tl:
        return core.ellipsoid("blood", 0.42, (x, 0.2, z), (r * 2.0, 0.35, r * 1.5), grp="splat")
    return core.ellipsoid("blood", 0.62, (x, min(float(p[1]), air), z), (r, r * 1.15, r), grp="spray")


def _burst(origin, t: float, n: int, rng, forward: np.ndarray, xr, zr, air: float,
           speed=(30.0, 100.0)) -> list[core.Prim]:
    """A wound's spray: n droplets out of `origin`, mostly along `forward`,
    up and sideways, every fifth a heavy gout."""
    out = []
    for i in range(n):
        d = unit(forward * rng.uniform(0.3, 1.0) + V(rng.uniform(-0.9, 0.9), rng.uniform(-0.1, 0.9),
                                                     rng.uniform(-0.6, 0.4)))
        gout = i % 5 == 0
        sp = rng.uniform(8, 24) if gout else rng.uniform(*speed)
        r = rng.uniform(1.2, 1.7) if gout else rng.uniform(0.6, 1.1)
        out.append(_droplet(origin, d * sp, t, r, xr, zr, air))
    return out


def db_death_model(frame: str, seed: int = SEED) -> tuple[list[core.Prim], dict]:
    """The Doughboy of death frame H-L on the floor (y = 0), untilted, without
    the floor's blood; and its parts by name (sack, spine, helmet)."""
    f = DB_FALLS[frame]
    pose = DBPose(frame, f.title, mouth=f.mouth, gape=True, eye="burst")
    P, _ = db_model(DB_NOSEVER, "A", seed, pose)
    helmet = [p for p in P if p.grp == "helmet"]
    head = [p for p in P if p.grp != "helmet"]
    # the sack: the round head, squashed about its bottom, sitting on the floor
    # it lands face up: tipped back (and a little to its side) about its centre, then squashed on the floor
    affine_prims(head, core.rot_z(f.roll) @ core.rot_x(f.back), DB_C)
    affine_prims(head, np.diag([f.spread, f.squash, f.spread]), V(0.0, 0.0, 0.0))
    core.rest_on_floor(head, {}, {p.grp for p in head})
    sack = head[0]
    # the torn neck where it meets the floor, the spine fallen out of it
    rng = np.random.default_rng(seed + 41)
    a, b = DB_SPINE
    b = a + (b - a) * f.spine
    neck = a + V(-DB_R * f.spread * 0.55, 0.0, 0.0)
    gore = []
    for i in range(7):
        q = neck + V(rng.uniform(-3, 3), 0.0, rng.uniform(-4, 4))
        gore.append(core.ellipsoid("raw", 0.40, (q[0], 1.6, q[2]), (3.6, 1.8, 3.2), grp="spine"))
    n_vert = 8
    for j in range(n_vert):
        q = neck + (b - neck) * (j + 0.5) / n_vert + V(0, 0, 1.6 * np.sin(j * 1.1))
        gore.append(core.ellipsoid("bone", 0.62, (q[0], 1.0, q[2]), (1.9 - 0.08 * j, 1.0, 1.7 - 0.07 * j),
                                   grp="spine"))
    for k, (dz, length) in enumerate(((-3.0, 16.0), (4.0, 22.0), (1.0, 11.0))):     # torn vessels
        q0 = neck + V(0, 0.9, dz)
        q1 = q0 + V(-length * f.spine, 0.0, dz * 0.8 + 3.0 * np.sin(k))
        gore.append(core.rcone("raw", 0.35, q0, V(q1[0], 0.7, q1[2]), 1.0, 0.6, grp="spine"))
    # the helmet, knocked off: flying in H, upside down beside the sack from I
    if f.helmet == "down":
        helmet = [p for p in helmet if p.mat not in ("belt",) and p.kind != "box"]      # the strap tears
        for p in helmet:
            p.tag = ""          # upside down: no decal (a stamp cannot turn over with it)
    hc = np.mean([p.bound()[0] for p in helmet], axis=0)
    target = DB_HELMET_FLY if f.helmet == "flying" else DB_HELMET_DOWN
    core.transform(helmet, {}, {"helmet"}, core.rot_z(f.helmet_roll), hc, target - hc)
    if f.helmet == "down":
        core.rest_on_floor(helmet, {}, {"helmet"})
    P = head + gore + helmet
    parts = {"sack": [sack], "spine": [p for p in gore if p.mat == "bone"], "helmet": helmet}
    return P, parts


def _front_z(sack: core.Prim, x: float, y: float, z_far: float = 80.0) -> float | None:
    """The sack's front surface at (x, y): bisection along z on its SDF."""
    f = lambda z: float(sack.sd(np.array([[x, y, z]]))[0])  # noqa: E731
    lo, hi = -z_far, z_far
    zs = np.linspace(hi, lo, 161)
    d = sack.sd(np.stack([np.full_like(zs, x), np.full_like(zs, y), zs], axis=1))
    inside = np.nonzero(d < 0)[0]
    if not len(inside):
        return None
    k = int(inside[0])
    a, b = zs[k - 1], zs[k]             # outside, inside
    for _ in range(24):
        m = (a + b) / 2
        a, b = (m, b) if f(m) > 0 else (a, m)
    return float((a + b) / 2)


def sdf_normal(prim: core.Prim, p: np.ndarray, h: float = 0.05) -> np.ndarray:
    """The outward normal of a primitive's surface at p (central differences)."""
    e = np.eye(3) * h
    pts = np.concatenate([p + e, p - e])
    d = prim.sd(pts)
    return unit(d[:3] - d[3:])


def db_death_point(frame: str, model_point: np.ndarray, sack: core.Prim) -> np.ndarray:
    """Where a point of the round head (model space) is on the sack of death
    frame H-L: tipped back, squashed, set on the floor as db_death_model does."""
    f = DB_FALLS[frame]
    q = core.rot_z(f.roll) @ core.rot_x(f.back) @ (np.asarray(model_point, float) - DB_C) + DB_C
    return np.diag([f.spread, f.squash, f.spread]) @ q + sack.xt


def _sack_run(sack: core.Prim, start: np.ndarray, dx: float, steps: int = 7) -> list[core.Prim]:
    """A run of blood from `start` down the sack's front to the floor."""
    pts = []
    for k in range(steps + 1):
        y = float(start[1]) * (1.0 - k / steps) + 0.4 * k / steps
        x = float(start[0]) + dx * k / steps
        z = _front_z(sack, x, y)
        if z is None:
            break
        pts.append(V(x, y, z + 0.35))
    return [core.rcone("blood", 0.42, a, b, 1.2 - 0.05 * k, 1.15 - 0.05 * k, grp="spray")
            for k, (a, b) in enumerate(zip(pts[:-1], pts[1:]))]


def db_death_blood(frame: str, P: list[core.Prim], seed: int = SEED) -> list[core.Prim]:
    """The blood off the head for death frame G-L: the eye's burst, runs on
    the sack, the neck's spurt, the pools."""
    xr, zr = DB_SPRAY_X, DB_SPRAY_Z
    rng = np.random.default_rng(seed + 43)
    if frame == "G":
        return _burst(_db_eye_at_g(), DB_G_T, DB_N_SPRAY, rng, EYE_DIR, xr, zr, DB_AIR_Y)
    f = DB_FALLS[frame]
    # the eye's burst, landed or landing round the head (it fell with it)
    out = _burst(DB_C + EYE_DIR * (DB_R + 1.0) + V(0, 6.0, 0), f.t, DB_N_SPRAY, rng, EYE_DIR, xr, zr, DB_AIR_Y)
    # runs down the sack's face, from the socket and the mouth to the floor
    sack = P[0]
    socket = db_death_point(frame, DB_C + EYE_DIR * (DB_R - 1.0), sack)
    mouth = db_death_point(frame, DB_C + MOUTH_DIR * DB_R, sack)
    for start, dx in ((socket + V(-3.0, -2.0, 0), -2.0), (socket + V(3.5, -2.5, 0), 3.0), (mouth, 1.0),
                      (mouth + V(-6.0, 0, 0), -3.0)):
        out += _sack_run(sack, start, dx)
    rng3 = np.random.default_rng(seed + 47)
    for _ in range(int(3 + 6 * f.pool)):        # it soaks: dark stains spread over the face and the crown
        q = DB_C + unit(EYE_DIR + V(rng3.uniform(-0.9, 0.9), rng3.uniform(-0.2, 0.9), rng3.uniform(-0.6, 0.1))) * DB_R
        c = db_death_point(frame, q, sack)
        out.append(_stain("blood", 0.40, c, sdf_normal(sack, c), rng3.uniform(2.5, 5.0), grp="spray"))
    # the neck pumps while it lands (H, I)
    if frame in "HI":
        rng2 = np.random.default_rng(seed + 44)
        neck = DB_SPINE[0] + V(-DB_R * f.spread * 0.55, 2.0, 0.0)
        for k in range(12):
            age = 0.02 + 0.025 * k
            v = V(rng2.uniform(-30, -5), rng2.uniform(10, 45), rng2.uniform(-5, 15))
            out.append(_droplet(neck, v, age, rng2.uniform(0.7, 1.1), xr, zr, DB_AIR_Y))
    if f.pool:
        g = f.pool
        out += hound.pool(-4.0, DB_POOL_Z, DB_POOL[0] * g, DB_POOL[1] * (0.45 + 0.55 * g),
                          np.random.default_rng(seed + 45))
        n = DB_SPINE[0] + V(-DB_R * f.spread * 0.55, 0, 0)
        out += hound.pool(float(n[0]) - 4.0, 6.0, DB_STUMP_POOL[0] * g, DB_STUMP_POOL[1] * g,
                          np.random.default_rng(seed + 46))
    return out


def db_corpse_metrics(frame: str = "L") -> dict:
    """The lying checks on the untilted model: each part's lowest point above
    the floor, the body's highest point, how far the supports spread."""
    P, parts = db_death_model(frame)
    rep = {k: round(core.lowest_y(v), 2) for k, v in parts.items()}
    body = parts["sack"] + parts["spine"] + [p for p in P if p.grp == "spine"]
    xs = [float(np.mean([p.bound()[0][0] for p in parts[k]])) for k, v in rep.items() if v <= DB_LYING_MAX]
    return {"lowest": rep, "top": round(hound.highest_y(body), 2), "span": round(max(xs) - min(xs), 1)}


# ---------------------------------------------------------------- the Panzermensch's poses
A_ = PM_ANKLE
PM_FULL_POSES: dict[str, PMPose] = {
    "A": replace(PM_POSES["A"], title="stands / walk, feet together (the sweep's)"),
    "B": PMPose("B", (7.0, A_, 8.0), (-7.0, A_ + 1.4, -7.5), (16.0, 31.0, -3.5), (-15.5, 31.5, 8.5), 7.0,
                title="left foot forward", bob=-1.6, twist=-4.0),
    "C": PMPose("C", (7.0, A_, -1.5), (-6.6, A_ + 5.0, 2.5), (16.5, 30.5, 1.5), (-16.5, 30.5, 2.5), 6.5,
                title="right leg passing", bob=0.4),
    "D": PMPose("D", (7.0, A_ + 1.4, -7.5), (-7.0, A_, 8.0), (15.5, 31.5, 8.5), (-16.0, 31.0, -3.5), 7.0,
                title="right foot forward", bob=-1.6, twist=4.0),
    "E": PMPose("E", (7.0, A_, 5.0), (-7.0, A_, -5.5), (14.0, 38.0, 10.0), (-18.0, 38.0, -8.0), 8.0,
                title="draws back: the shell forms in his fist", twist=14.0, charge=0.7, throw_arm=True),
    "F": PMPose("F", (7.0, A_, 5.0), (-7.0, A_, -5.0), (13.0, 44.0, 11.0), (-12.0, 66.0, -9.0), 2.0,
                title="cocks the arm over his head", twist=18.0, head_pitch=6.0, charge=0.85, throw_arm=True),
    "G": replace(PM_POSES["G"], title="throws (the sweep's)"),
    "H": PMPose("H", (7.0, A_, 2.0), (-7.0, A_, -4.0), (19.0, 40.0, 5.0), (-19.0, 40.0, 5.0), -8.0,
                title="pain: struck, he rocks back", bob=-1.0, head_pitch=22.0, head_turn=10.0, spurt=0.05),
}
PM_WOUND = (1.5, 45.0)          # (x, y) of the round's hole on the breastplate, upright
PLATE_STAIN_DEPTH = 0.9         # x the stain's radius: on the curved breastplate the sunk sphere stays inside him


@dataclass(frozen=True)
class PMFall:
    """A death frame (I-O): the pose he is in, then how far he has fallen."""
    pose: PMPose
    t: float                    # s after the hit
    fall: float                 # degrees back over his heels
    yaw: float                  # degrees he has twisted (90: lying across the screen)
    settle: tuple = ()          # what is let fall to the floor: keys of PM_SETTLE
    pool: float = 0.0           # share of the full pool
    stain: float = 2.6          # half width of the stain round the wound
    tilt: float = 0.0           # degrees the render looks further down (as gen_hound.DEATH_TILT)


DEAD_ANKLE = 2.3                # the dead legs reach out straight (hip to ankle 28.9 of 29 units)
_DEAD = PMPose("O", (8.0, DEAD_ANKLE, -2.0), (-8.0, DEAD_ANKLE, -1.0), (16.0, 34.0, -2.0), (-16.0, 33.0, -2.0), 0.0,
               title="dead", head_pitch=10.0, leg_z=-4.3)
PM_SETTLE_ALL = ("head", "arm_l", "arm_r", "fore_l", "fore_r", "leg_l", "leg_r", "shin_l", "shin_r")
PM_FALLS = {                    # panzermensch.zs: I J K L M N 8 tics, O held (A_Scream on J, A_NoBlocking on L)
    "I": PMFall(PMPose("I", (7.0, A_, 3.0), (-7.0, A_, -2.0), (18.0, 46.0, 6.0), (-17.0, 44.0, 8.0), -16.0,
                       title="hit: the chest opens", bob=-0.5, head_pitch=28.0), 0.06, 0.0, 0.0, stain=2.6),
    "J": PMFall(PMPose("J", (7.5, A_, 4.0), (-7.5, A_, 1.0), (18.0, 36.0, 2.0), (-18.0, 34.0, 4.0), -10.0,
                       title="his knees go", bob=-7.0, head_pitch=30.0, head_turn=8.0), 0.29, 14.0, 12.0, stain=3.6),
    "K": PMFall(PMPose("K", (7.5, A_, 4.0), (-7.5, A_, 1.0), (17.0, 44.0, 0.0), (-18.0, 40.0, 0.0), -6.0,
                       title="falling back", bob=-6.0, head_pitch=24.0), 0.52, 48.0, 45.0, stain=4.4, tilt=8.0),
    "L": PMFall(replace(_DEAD, key="L", title="hits the floor"), 0.75, 84.0, 78.0, ("head",), stain=5.2, tilt=18.0),
    "M": PMFall(replace(_DEAD, key="M", title="the limbs fall"), 0.98, 90.0, 88.0, ("head", "arm_l", "arm_r"),
                pool=0.4, stain=5.8, tilt=24.0),
    "N": PMFall(replace(_DEAD, key="N", title="still"), 1.21, 90.0, 90.0, PM_SETTLE_ALL, pool=0.7, stain=6.3,
                tilt=28.0),
    "O": PMFall(replace(_DEAD, head_turn=25.0), 3.0, 90.0, 90.0, PM_SETTLE_ALL, pool=1.0, stain=6.8, tilt=28.0),
}
PM_FALL_PIVOT = V(0.0, 0.0, -6.0)       # behind his heels: he falls back over them
# The Schwer cannot lie on his back: the exhaust stacks bolted to it would
# prop him 2-3 units off the floor (the fault the CEO named on the Legion's
# first L0). He folds forward and falls on his face, the stacks and the
# banner on top, which also tells the two brutes apart when dead.
PS_FALL_PIVOT = V(0.0, 0.0, 9.0)        # in front of his toes
_PRONE = PMPose("O", (8.0, A_, 2.0), (-8.0, A_, 1.0), (16.0, 34.0, 2.0), (-16.0, 33.0, 2.0), -3.0,
                title="dead, face down", bob=-1.5, head_pitch=-6.0)
PS_FALLS = {
    "I": PM_FALLS["I"],
    "J": PMFall(PMPose("J", (7.5, A_, 4.0), (-7.5, A_, 1.0), (17.0, 30.0, 8.0), (-17.0, 30.0, 8.0), 18.0,
                       title="he folds forward", bob=-9.0, head_pitch=-10.0), 0.29, -10.0, -8.0, stain=3.6),
    "K": PMFall(PMPose("K", (7.5, A_, 4.0), (-7.5, A_, 1.0), (16.0, 40.0, 14.0), (-16.0, 40.0, 14.0), 12.0,
                       title="falls on his face", bob=-8.0, head_pitch=-8.0), 0.52, -48.0, -40.0, stain=4.4,
                tilt=8.0),
    "L": PMFall(replace(_PRONE, key="L", title="hits the floor"), 0.75, -84.0, -78.0, ("head",), stain=5.2,
                tilt=18.0),
    "M": PMFall(replace(_PRONE, key="M", title="the limbs fall"), 0.98, -90.0, -88.0, ("head", "arm_l", "arm_r"),
                pool=0.4, stain=5.8, tilt=24.0),
    "N": PMFall(replace(_PRONE, key="N", title="still"), 1.21, -90.0, -90.0, PM_SETTLE_ALL, pool=0.7, stain=6.3, tilt=28.0),
    "O": PMFall(replace(_PRONE, head_turn=25.0), 3.0, -90.0, -90.0, PM_SETTLE_ALL,
                pool=1.0, stain=6.8, tilt=28.0),
}
PM_SETTLE = {                   # (limb, side, group or "", the prims turned, the prims that must touch, pivot, tip)
    "head": ("", 0, "helmet", None, None, "neck", "crown"),
    "arm_l": ("arm", core.LEFT, "", None, slice(0, 3), "shoulder_l", "fist_l"),    # the arm from the shoulder
    "arm_r": ("arm", core.RIGHT, "", None, slice(0, 3), "shoulder_r", "fist_r"),   # till the upper arm lies,
    "fore_l": ("arm", core.LEFT, "", slice(3, None), None, "elbow_l", "fist_l"),   # then the forearm from the
    "fore_r": ("arm", core.RIGHT, "", slice(3, None), None, "elbow_r", "fist_r"),  # elbow till the gauntlet does
    "leg_l": ("leg", core.LEFT, "", None, slice(0, 3), "hip_l", "ankle_l"),
    "leg_r": ("leg", core.RIGHT, "", None, slice(0, 3), "hip_r", "ankle_r"),
    "shin_l": ("leg", core.LEFT, "", slice(3, 5), None, "knee_l", "ankle_l"),     # greave and boot from the knee
    "shin_r": ("leg", core.RIGHT, "", slice(3, 5), None, "knee_r", "ankle_r"),
}
PM_SETTLE_RIDE = {"head": ("crown",), **{f"arm_{s}": (f"elbow_{s}", f"wrist_{s}", f"fist_{s}") for s in "lr"},
                  **{f"fore_{s}": (f"wrist_{s}", f"fist_{s}") for s in "lr"},
                  **{f"leg_{s}": (f"knee_{s}", f"ankle_{s}") for s in "lr"}, **{f"shin_{s}": (f"ankle_{s}",) for s in "lr"}}
SETTLE_DOWN = 75.0              # degrees a part may swing down to the floor ...
SETTLE_UP = 70.0                # ... or up out of it
SETTLE_STEPS = 16
PM_N_SPRAY = 42
PM_POOL = (26.0, 14.0)          # (x, z) radii of the full pool under his chest
PM_POOL_Z = 6.0
PM_SPRAY_X = (-58.0, 104.0)     # landed splats stay inside the death canvas
PM_SPRAY_Z = (-20.0, 30.0)
PM_AIR_Y = 84.0
PM_LYING_MAX = 2.0
PM_LYING_SUPPORT = 1.0
PM_LYING_TOP = 26.0             # a brute's breastplate is thick: nothing of him higher than this, lying
PM_LYING_SPAN = 40.0
PM_BLOOD = {
    "blood": Mat.on_ramp("flag_red", 1, 5, black_floor=True, shift=False, flat=True),    # spray, splats, stains
    "pool": Mat.on_ramp("flag_red", 0, 3, black_floor=True, shift=False, flat=True),     # standing blood
}
PM_FULL_MATERIALS: dict[str, Mat] = dict(PM_MATERIALS)
for _n, _m in PM_BLOOD.items():
    core.register_material(_n, _m, PM_FULL_MATERIALS)
SCHWER_CELL = PMCell("DS2", "mask", "both", True, "D with S2: black, x1.12, spikes and stacks, lit slit")
PM_DEATH_CV = core.Canvas(176, 120, 64, 96)
PS_CV = core.Canvas(128, 104, 64, 98)
PS_DEATH_CV = core.Canvas(192, 140, 68, 104)


def _pm_rigid(P: list[core.Prim], anch: dict, R: np.ndarray, pivot, offset=(0.0, 0.0, 0.0)) -> None:
    """Every primitive and every anchor, rotated by R about pivot, then moved."""
    pivot, offset = np.asarray(pivot, float), np.asarray(offset, float)
    for p in P:
        p.xm = R @ p.xm
        p.xt = R @ (p.xt - pivot) + pivot + offset
    for k, (pt, g) in list(anch.items()):
        anch[k] = (R @ (pt - pivot) + pivot + offset, g)


def pm_falls(cell: PMCell) -> dict[str, PMFall]:
    """The Schwer (stacks on his back) falls on his face; the base brute on his back."""
    return PS_FALLS if cell.top in ("stacks", "both") else PM_FALLS


def pm_settle_prims(P: list[core.Prim], what: str) -> list[core.Prim]:
    limb, side, grp, part, _, _, _ = PM_SETTLE[what]
    if grp:
        return [p for p in P if p.grp == grp]
    out = [p for p in P if p.limb == limb and p.side == side]
    return out if part is None else out[part]


def pm_settle_probe(P: list[core.Prim], what: str) -> list[core.Prim]:
    limb, side, grp, _, probe, _, _ = PM_SETTLE[what]
    if grp or probe is None:
        return pm_settle_prims(P, what)
    return [p for p in P if p.limb == limb and p.side == side][probe]


def pm_settle(part: list[core.Prim], probe: list[core.Prim], pivot: np.ndarray, tip: np.ndarray) -> np.ndarray:
    """Swing `part` about `pivot` (the tip going down for +) until the lowest
    point of `probe` (a subset of it) is on the floor: down if it hangs above,
    up if it is in it. Bisection on rig_core.lowest_y; returns the rotation."""
    v = unit(tip - pivot)
    axis = np.cross(v, V(0, -1, 0))
    if np.linalg.norm(axis) < 1e-6:
        return np.eye(3)
    keep = [(p.xm, p.xt) for p in part]

    def low_at(deg):
        hound._rigid(part, hound.axis_rot(axis, deg), pivot)
        y = core.lowest_y(probe)
        for p, (xm, xt) in zip(part, keep):
            p.xm, p.xt = xm, xt
        return y

    y0 = low_at(0.0)
    if abs(y0) < 0.05:
        return np.eye(3)
    lo, hi = (0.0, SETTLE_DOWN) if y0 > 0 else (-SETTLE_UP, 0.0)
    if y0 > 0 and low_at(hi) > 0:
        lo = hi
    elif y0 < 0 and low_at(lo) < 0:
        hi = lo
    else:
        for _ in range(SETTLE_STEPS):
            mid = (lo + hi) / 2
            if (low_at(mid) > 0) == (y0 > 0):
                lo, hi = (mid, hi) if y0 > 0 else (lo, mid)
            else:
                lo, hi = (lo, mid) if y0 > 0 else (mid, hi)
    R = hound.axis_rot(axis, lo if y0 > 0 else hi)
    hound._rigid(part, R, pivot)
    return R


def pm_death_model(cell: PMCell, frame: str, seed: int = SEED) -> tuple[list[core.Prim], dict]:
    """The Panzermensch of death frame I-O in model space (floor y = 0),
    untilted, unscaled, without the floor's blood; and its anchors (points)."""
    f = pm_falls(cell)[frame]
    anch: dict = {}
    P = pm_model(cell, frame, seed=seed, pose=f.pose, anchors=anch)
    if f.fall or f.yaw:
        pivot = PS_FALL_PIVOT if f.fall < 0 else PM_FALL_PIVOT
        _pm_rigid(P, anch, core.rot_y(f.yaw) @ core.rot_x(f.fall), pivot)
    falling = {id(p) for w in f.settle for p in pm_settle_prims(P, w)}
    resting = [p for p in P if id(p) not in falling]
    _pm_rigid(P, anch, np.eye(3), V(0, 0, 0), V(0, -core.lowest_y(resting), 0))
    for what in f.settle:
        *_, root, tip = PM_SETTLE[what]
        part = pm_settle_prims(P, what)
        R = pm_settle(part, pm_settle_probe(P, what), anch[root][0], anch[tip][0])
        pivot = anch[root][0]
        for k in PM_SETTLE_RIDE[what]:         # the joints further out ride along
            pt, g = anch[k]
            anch[k] = (R @ (pt - pivot) + pivot, g)
    return P, {k: v[0] for k, v in anch.items()}


def _pm_attached(prim: core.Prim, to: core.Prim, grp: str = "blood") -> core.Prim:
    """`prim`, given in the upright model space, rides `to`'s rigid transform."""
    prim.xm, prim.xt, prim.grp = to.xm.copy(), to.xt.copy(), grp
    return prim


def _torso_of(P: list[core.Prim]) -> core.Prim:
    return next(p for p in P if p.tag == "torso")


def _mask_of(P: list[core.Prim]) -> core.Prim:
    return next(p for p in P if p.grp == "helmet" and p.mat == "plate")


def pm_wound_world(P: list[core.Prim]) -> np.ndarray:
    t = _torso_of(P)
    x, y = PM_WOUND
    return t.xm @ V(x, y, _torso_front(x, y) + 0.3) + t.xt


_PM_HIT: dict = {}


def pm_wound_at_hit(cell: PMCell) -> np.ndarray:
    """Where the wound was when the round hit (frame I): the burst's origin."""
    if cell.key not in _PM_HIT:
        _PM_HIT[cell.key] = pm_wound_world(pm_death_model(cell, "I")[0])
    return _PM_HIT[cell.key]


def pm_body_blood(P: list[core.Prim], stain: float, run: int, mouth_run: int) -> list[core.Prim]:
    """The blood ON him, riding the plate: the hole, the stain soaking wider,
    the run down the breastplate, the run from under the mask."""
    out = []
    t, x, y = _torso_of(P), *PM_WOUND
    zf = _torso_front(x, y)
    n = unit(V(x * 0.02, 0.0, 1.0))
    out.append(_pm_attached(_stain("blood", 0.48, V(x, y - stain * 0.2, zf), n, stain, depth=PLATE_STAIN_DEPTH * stain),
                            t))
    out.append(_pm_attached(core.ellipsoid("void", 0.05, (x, y, zf + 0.35), (1.1, 1.2, 0.8)), t))
    if run:
        y1 = y - 4.0 - 3.0 * run
        out.append(_pm_attached(core.rcone("blood", 0.40, V(x + 0.3, y - 1.5, _torso_front(x, y - 1.5) + 0.5),
                                           V(x + 1.0, y1, _torso_front(x + 1.0, y1) + 0.5), 1.4, 1.0), t))
    if mouth_run:                   # from under the mask, down the jowls and the gorget
        m = _mask_of(P)
        a = V(0.6, 56.6, 6.2)
        out.append(_pm_attached(core.rcone("blood", 0.42, a, a + V(0.4, -1.6 - 1.4 * mouth_run, 1.2), 0.75, 0.55),
                                m))
    return out


def pm_death_blood(cell: PMCell, frame: str, P: list[core.Prim], anch: dict, seed: int = SEED) -> list[core.Prim]:
    """All the blood of death frame I-O, on him and on the floor."""
    f = pm_falls(cell)[frame]
    k = "IJKLMNO".index(frame)
    out = pm_body_blood(P, f.stain, max(k - 1, 0), k)
    hit = pm_wound_at_hit(cell)
    out += _burst(hit, f.t, PM_N_SPRAY, np.random.default_rng(seed + 51), V(0, 0.2, 1.0),
                  PM_SPRAY_X, PM_SPRAY_Z, PM_AIR_Y, speed=(25.0, 75.0))
    w = pm_wound_world(P)
    if frame in "JKL":              # the wound bleeds while he falls
        rng = np.random.default_rng(seed + 52 + k)
        for j in range(6):
            v = V(rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(4, 14))
            out.append(_droplet(w, v, 0.02 + 0.03 * j, rng.uniform(0.6, 0.95), PM_SPRAY_X, PM_SPRAY_Z, PM_AIR_Y))
    if f.pool:
        g = f.pool
        out += hound.pool(float(w[0]), PM_POOL_Z, PM_POOL[0] * g, PM_POOL[1] * (0.45 + 0.55 * g),
                          np.random.default_rng(seed + 54))
        m = _mask_of(P)
        mp = m.xm @ V(0.0, 56.0, 6.0) + m.xt
        out += hound.pool(float(mp[0]), PM_POOL_Z - 2.0, 5.0 + 4.0 * g, 4.0 + 2.0 * g,
                          np.random.default_rng(seed + 55))
    return out


def pm_pain_blood(P: list[core.Prim], t: float, seed: int = SEED) -> list[core.Prim]:
    """H: the round's hole and a short spurt out of the breastplate."""
    out = pm_body_blood(P, 2.2, 0, 0)
    w = pm_wound_world(P)
    rng = np.random.default_rng(seed + 57)
    for _ in range(9):
        v = V(rng.uniform(-14, 14), rng.uniform(0, 30), rng.uniform(25, 60))
        p = w + v * t + V(0, -0.5 * BLOOD_GRAVITY * t * t, 0)
        r = rng.uniform(0.7, 1.1)
        out.append(core.ellipsoid("blood", 0.62, tuple(p), (r, r * 1.15, r), grp="spray"))
    return out


def pm_corpse_parts(P: list[core.Prim]) -> dict[str, list[core.Prim]]:
    """The lying brute's parts by name: what must rest on the floor."""
    out = {"torso": [_torso_of(P)], "hips": [p for p in P if p.tag == "faulds"],
           "head": [p for p in P if p.grp == "helmet"]}
    for name, side in (("left", core.LEFT), ("right", core.RIGHT)):
        arm = [p for p in P if p.limb == "arm" and p.side == side]
        leg = [p for p in P if p.limb == "leg" and p.side == side]
        out[f"upper_arm_{name}"], out[f"gauntlet_{name}"] = arm[:1], arm[5:6]
        out[f"thigh_{name}"], out[f"greave_{name}"], out[f"boot_{name}"] = leg[:1], leg[3:4], leg[4:5]
    return out


def pm_corpse_metrics(cell: PMCell, frame: str = "O") -> dict:
    """The lying checks on the untilted model (unscaled; the Schwer is the
    same model x1.12): parts above the floor, the top, the supports' spread,
    and how far the torso lies across the screen."""
    P, _ = pm_death_model(cell, frame)
    parts = pm_corpse_parts(P)
    rep = {k: round(core.lowest_y(v), 2) for k, v in parts.items() if v}
    xs = [float(np.mean([p.bound()[0][0] for p in parts[k]])) for k, v in rep.items() if v <= PM_LYING_SUPPORT]
    torso = parts["torso"][0]
    return {"lowest": rep, "top": round(hound.highest_y(P), 2), "span": round(max(xs) - min(xs), 1),
            "across": round(abs(float((torso.xm @ V(0, 1, 0))[0])), 3)}


# ---------------------------------------------------------------- one machinery for the three sets
@dataclass(frozen=True)
class FullSpec:
    key: str                    # "db" | "pm" | "ps"
    sprite: str
    zs: Path                    # the states the set is drawn for (the Schwer inherits panzermensch.zs')
    name: str
    slug: str


FULL_SPECS = {
    "db": FullSpec("db", DB_SPRITE, DB_ZS, "Doughboy, cell C", "doughboy-C-full-set"),
    "pm": FullSpec("pm", PM_SPRITE, PM_ZS, "Panzermensch, cell D", "panzermensch-D-full-set"),
    "ps": FullSpec("ps", PS_SPRITE, PM_ZS, "Panzermensch Schwer, D with S2", "panzermensch-schwer-full-set"),
}


def full_frames(key: str) -> tuple[str, str]:
    """(the letters at 8 rotations, the death letters) from the class's .zs."""
    return zs_frames(FULL_SPECS[key].zs)


def full_plan(key: str) -> list[tuple[str, int]]:
    """(frame, rotation) of every lump: 8 drawn rotations (handed figures, no
    mirrored pairs) for the living frames, rotation 0 for the death."""
    rotated, death = full_frames(key)
    return [(f, r) for f in rotated for r in range(1, core.ROTATIONS + 1)] + [(f, 0) for f in death]


def full_lump(key: str, frame: str, rotation: int) -> str:
    """The lump name: SDDBA1 ... SDDBL0, SDPMA1 ... SDPMO0, SDPSA1 ..."""
    return f"{FULL_SPECS[key].sprite}{frame}{rotation}"


def full_canvas(key: str, frame: str) -> core.Canvas:
    rotated, _ = full_frames(key)
    live = frame in rotated
    if key == "db":
        return DB_CV if live else DB_DEATH_CV
    if key == "pm":
        return PM_CV if live else PM_DEATH_CV
    return PS_CV if live else PS_DEATH_CV


def full_grab(key: str, frame: str) -> tuple[int, int]:
    """grAb: the living Doughboy hangs by the actor's z (no feet to sink), as
    in the sweep, and so does G (it is still in the air when it dies); what
    lies on the floor sinks FEET_SINK as every approved corpse does."""
    cv = full_canvas(key, frame)
    rotated, _ = full_frames(key)
    if key == "db" and (frame in rotated or frame == "G"):
        return cv.cx, cv.foot_row
    return core.grab_offsets(cv)


def full_table(key: str, frame: str) -> dict[str, Mat]:
    rotated, _ = full_frames(key)
    if key == "db":
        return DB_MATERIALS if frame in rotated else DB_DEATH_MATERIALS
    return PM_MATERIALS if frame in "ABCDEFG" else PM_FULL_MATERIALS


def _tilted(P: list[core.Prim], deg: float) -> list[core.Prim]:
    if deg:
        hound._rigid(P, core.rot_x(-deg), V(0, 0, 0))
    return P


def full_prims(key: str, frame: str, seed: int = SEED) -> list[core.Prim]:
    """Every primitive of one frame, model space, ready to render."""
    if key == "db":
        cell = db_full_cell()
        if frame in "AD":
            return db_model(cell, frame, seed)[0]           # the sweep's figure, as chosen
        if frame in DB_FULL_POSES:
            P = db_model(cell, "A", seed, DB_FULL_POSES[frame])[0]
            return P + db_death_blood("G", P, seed) if frame == "G" else P
        P, _ = db_death_model(frame, seed)
        return _tilted(P + db_death_blood(frame, P, seed), DB_FALLS[frame].tilt)
    cell = PM[PM_FULL_KEY] if key == "pm" else SCHWER_CELL
    if frame in PM_FULL_POSES:
        pose = PM_FULL_POSES[frame]
        P = pm_model(cell, frame, seed=seed, pose=pose)
        if pose.spurt:
            P = P + pm_pain_blood(P, pose.spurt, seed)
    else:
        P, anch = pm_death_model(cell, frame, seed)
        P = _tilted(P + pm_death_blood(cell, frame, P, anch, seed), pm_falls(cell)[frame].tilt)
    return scale_prims(P, SCHWER_SCALE) if key == "ps" else P


def render_full_layers(key: str, frame: str, rotation: int, seed: int = SEED,
                       prims: list[core.Prim] | None = None) -> core.Layers:
    P = full_prims(key, frame, seed) if prims is None else prims
    cv, table = full_canvas(key, frame), full_table(key, frame)
    what = full_lump(key, frame, rotation)
    if key == "db":
        return core.render_layers(P, rotation, cv, table, seed=seed, value_shift=0.0, chrome=DB_CHROME,
                                  insignia=(DECAL_BIG_INSIGNIA,), what=what)       # D67: the big flag
    return core.render_layers(P, rotation, cv, table, seed=seed, value_shift=PM_VALUE_SHIFT,
                              insignia=(BANNER_INSIGNIA,), what=what)


def render_full(key: str, frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One lump of a full set, RGBA."""
    return render_full_layers(key, frame, rotation, seed).rgba


def blood_share(lay: core.Layers, table: dict[str, Mat]) -> float:
    """Share of the opaque pixels painted in the blood and pool materials."""
    ids = core.material_ids(table)
    want = [ids[n] for n in ("blood", "pool") if n in ids]
    return round(float(np.isin(lay.mat, want).sum() / max((lay.mat >= 0).sum(), 1)), 3)


def _frame_job(job: tuple[str, str, int]) -> tuple[str, str, dict, float | None]:
    """A worker's unit: one frame of one set at every rotation it needs (the
    model is built once, the death's settling is the slow part)."""
    key, frame, seed = job
    rotated, _ = full_frames(key)
    rots = range(1, core.ROTATIONS + 1) if frame in rotated else (0,)
    P = full_prims(key, frame, seed)
    out, share = {}, None
    for r in rots:
        lay = render_full_layers(key, frame, r, seed, prims=P)
        out[r] = lay.rgba
        if r == 0:
            share = blood_share(lay, full_table(key, frame))
    return key, frame, out, share


def set_dir(key: str) -> Path:
    return FULL_DIR / FULL_SPECS[key].sprite


def build_full(keys=("db", "pm", "ps"), jobs: int = 1, seed: int = SEED, only: set[str] | None = None) -> dict:
    """Render the sets' lumps (PNG with grAb) into work/art/enemies/heavy/full/<SPRITE>/."""
    work = [(k, f, seed) for k in keys for f in dict.fromkeys(f for f, _ in full_plan(k))
            if not only or f"{k}:{f}" in only]
    sprites: dict = {k: {} for k in keys}
    shares: dict = {k: {} for k in keys}

    def take(res):
        key, frame, out, share = res
        for r, rgba in out.items():
            save(rgba, set_dir(key) / f"{full_lump(key, frame, r)}.png", full_grab(key, frame))
            sprites[key][(frame, r)] = rgba
        if share is not None:
            shares[key][frame] = share
        print(key, frame, "done", flush=True)

    for k in keys:
        set_dir(k).mkdir(parents=True, exist_ok=True)
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            for res in ex.map(_frame_job, work):
                take(res)
    else:
        for w in work:
            take(_frame_job(w))
    for k in keys:                      # merged, so a partial render (--only) keeps the other frames' shares
        path = set_dir(k) / "blood_share.json"
        old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        old.update(shares[k])
        _, death = full_frames(k)
        path.write_text(json.dumps({f: old[f] for f in death if f in old}, indent=2) + "\n", encoding="utf-8")
    return sprites


def load_full(key: str) -> dict:
    out = {}
    for f, r in full_plan(key):
        with Image.open(set_dir(key) / f"{full_lump(key, f, r)}.png") as im:
            out[(f, r)] = np.asarray(im.convert("RGBA")).copy()
    return out


# ---------------------------------------------------------------- GIFs, lineups, numbers
HOLD_MS = 1600                  # a -1 frame (the corpse) held this long before the GIF loops
LEAD_TICS = 20                  # the living frame before a cycle, as the approved sheets show it
FULL_SLOT = 72
DEAD_SLOT = 168
APPROVED = (("SDRRA1", "rifleman", "Reich rifleman"), ("SDLTA1", "legion", "Legion trooper"),
            ("SDHSA1", "storm", "Stormtrooper"), ("SDHNA1", "hound", "Reich hound"))
APPROVED_DEAD = (("SDRRL0", "rifleman", "rifleman"), ("SDLTL0", "legion", "Legion trooper"),
                 ("SDHSM0", "storm", "Stormtrooper"), ("SDHNN0", "hound", "hound"))
DOOM_GRAVITY = 1.0              # units / tic^2 a falling actor gains (Doom's GRAVITY, FRACUNIT: NOT VERIFIED in GZDoom)


def _ms(tics: int) -> int:
    return HOLD_MS if tics < 0 else int(round(tics * core.TIC_MS))


def _gif(path: Path, frames: list[np.ndarray], durs: list[int]) -> Path:
    return core.save_gif(frames, durs, path)


def _neutral(arrs: list[np.ndarray]) -> list[np.ndarray]:
    return [core.on_bg(x, core.NEUTRAL) for x in hound.crop_common(arrs)]


def fall_z(tic: float, hover: float = HOVER) -> float:
    """Height of a dead floater `tic` tics after it died: it drops from its
    hover under Doom's gravity (P_ZMovement, from memory: NOT VERIFIED)."""
    return max(hover - 0.5 * DOOM_GRAVITY * tic * (tic + 1), 0.0)


def write_full_gifs(key: str, spr: dict) -> dict[str, Path]:
    """Every cycle at game speed, the tics read from the class's .zs."""
    d = set_dir(key)
    st = zs_states(FULL_SPECS[key].zs)
    runs = {lab: hound._gif_runs(seq) for lab, seq in st.items()}
    sprite = FULL_SPECS[key].sprite
    out: dict[str, Path] = {}

    def cyc(name, seq, rot):
        out[name] = _gif(d / f"{sprite}_{name}.gif", _neutral([spr[(f, rot)] for f, _ in seq]), [_ms(t) for _, t in seq])

    out["turntable"] = _gif(d / f"{sprite}_turntable.gif", _neutral([spr[("A", r)] for r in range(1, 9)]),
                            [_ms(12)] * 8)
    lead = [("A", LEAD_TICS)]
    if key == "db":
        for r in range(1, 9):
            cyc(f"attack_rot{r}", lead + runs["Missile"], r)
        for r in (1, 3, 5, 7):
            cyc(f"pain_rot{r}", lead + runs["Pain"], r)
    else:
        see = runs["See"]
        for r in range(1, 9):
            cyc(f"see_rot{r}", see, r)
        for r in (1, 3, 5, 7):
            cyc(f"attack_rot{r}", see + runs["Missile"], r)
            cyc(f"pain_rot{r}", see + runs["Pain"] + see, r)
        cyc("spawn_rot1", runs["Spawn"], 1)
    death = runs["Death"]
    out["death"] = _gif(d / f"{sprite}_death.gif", _neutral([spr[(f, 0)] for f, _ in death]),
                        [_ms(t) for _, t in death])
    # the death on MAP01's floor, from the living frame, each sprite by its own offsets
    wall, light = ("SDCONC1", 176) if key == "db" else ("SDCONC1", 144)
    cvd = full_canvas(key, death[0][0])
    width = 2 * max(cvd.cx, cvd.w - cvd.cx)
    frames, durs = [], []
    alive = ("A", 1)
    ga = full_grab(key, "A")
    hover = HOVER if key == "db" else 0
    frames.append(tall_lineup([(spr[alive], ga[0], ga[1] + hover)], wall, light, width))
    durs.append(_ms(LEAD_TICS))
    tic = 0
    for f, t in death:
        g = full_grab(key, f)
        if key == "db" and f == "G":        # it is still falling: the actor drops under gravity
            for a, b in ((0, t // 2), (t // 2, t)):
                z = fall_z((a + b) / 2)
                frames.append(tall_lineup([(spr[(f, 0)], g[0], g[1] + int(round(z)))], wall, light, width))
                durs.append(_ms(b - a))
        else:
            frames.append(tall_lineup([(spr[(f, 0)], g[0], g[1])], wall, light, width))
            durs.append(_ms(t))
        tic += max(t, 0)
    out["death_floor"] = _gif(d / f"{sprite}_death_floor.gif", frames, durs)
    return out


def _approved(table) -> tuple[list, list[str]]:
    figs, labels = [], []
    for name, folder, label in table:
        r = approved(name, folder)
        if r:
            figs.append(r)
            labels.append(f"{name} {label} (approved)")
    return figs, labels


def full_lineups(key: str, spr: dict, base_pm: dict | None = None) -> dict:
    """At 1x on MAP01, beside the approved enemies (assets/sprites/, read only):
    the living frames in each scene, then the corpses on the floor."""
    d = set_dir(key)
    sprite = FULL_SPECS[key].sprite
    hover = HOVER if key == "db" else 0
    picks = {"db": (("A", 1), ("A", 3), ("D", 1), ("E", 1)),
             "pm": (("A", 1), ("A", 3), ("A", 5), ("G", 1)),
             "ps": (("A", 1), ("A", 3), ("A", 5), ("G", 1))}[key]
    figs, labels = [], []
    if key == "ps" and base_pm:
        figs.append((base_pm[("A", 1)], *full_grab("pm", "A")))
        labels.append("SDPMA1 (the 500 HP Panzermensch, this batch)")
    for f, r in picks:
        g = full_grab(key, f)
        figs.append((spr[(f, r)], g[0], g[1] + hover))
        labels.append(f"{sprite}{f}{r}")
    af, al = _approved(APPROVED if key != "ps" else APPROVED[:2])
    figs += af
    labels += al
    scenes = DB_SCENES if key == "db" else PM_SCENES
    out = {"labels": labels, "scenes": {}}
    for sk, wall, light, what in scenes:
        sc = tall_lineup(figs, wall, light, FULL_SLOT * len(figs))
        Image.fromarray(sc, "RGB").save(d / f"lineup_{sk}.png", optimize=True)
        out["scenes"][sk] = (sc, wall, light, what)
    _, death = full_frames(key)
    corpse = death[-1]
    dead = []
    dlabels = []
    if key == "ps" and base_pm:
        dead.append((base_pm[(corpse, 0)], *full_grab("pm", corpse)))
        dlabels.append(f"SDPM{corpse}0")
    dead.append((spr[(corpse, 0)], *full_grab(key, corpse)))
    dlabels.append(f"{sprite}{corpse}0")
    df, dl = _approved(APPROVED_DEAD)
    dead += df
    dlabels += [x.replace(" (approved)", ", approved") for x in dl]
    for light in (176, 128):
        sd = tall_lineup(dead, "SDCONC1", light, DEAD_SLOT * len(dead), wall_h=72)
        Image.fromarray(sd, "RGB").save(d / f"lineup_dead_{light}.png", optimize=True)
        out[f"dead_{light}"] = sd
    out["dead_labels"] = dlabels
    return out


def full_metrics(key: str, spr: dict) -> dict:
    rotated, death = full_frames(key)
    scenes = DB_SCENES if key == "db" else PM_SCENES
    m = {"lumps": len(full_plan(key)), "front": measure(spr[("A", 1)], scenes), "side": measure(spr[("A", 3)], scenes)}
    m["heights"] = {full_lump(key, f, r): int(np.ptp(np.nonzero(spr[(f, r)][..., 3] > 0)[0]) + 1)
                    for f, r in full_plan(key)}
    path = set_dir(key) / "blood_share.json"
    m["blood_share"] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if key == "db":
        m["corpse"] = db_corpse_metrics(death[-1])
    else:
        m["corpse"] = pm_corpse_metrics(PM[PM_FULL_KEY] if key == "pm" else SCHWER_CELL, death[-1])
        if key == "ps":
            m["corpse"]["scaled_by"] = SCHWER_SCALE
    (set_dir(key) / "metrics.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    return m


def sweep_identity(key: str, spr: dict, sweep_dir: Path = OUT_DIR) -> dict[str, bool | None]:
    """Whether the set's sweep views are the sweep's pixels the CEO chose
    (None where the sweep PNG is not on disk; the Schwer has no sweep cell)."""
    if key == "ps":
        return {}
    sprite, cell, views = ((DB_SPRITE, DB_FULL_KEY, DB_VIEWS) if key == "db" else (PM_SPRITE, PM_FULL_KEY, PM_VIEWS))
    out: dict[str, bool | None] = {}
    for f, r in views:
        path = sweep_dir / f"{lump(sprite, cell, f, r)}.png"
        if not path.is_file():
            out[full_lump(key, f, r)] = None
            continue
        with Image.open(path) as im:
            out[full_lump(key, f, r)] = bool(np.array_equal(np.asarray(im.convert("RGBA")), spr[(f, r)]))
    return out


# ---------------------------------------------------------------- the sheets
FULL_ROT_NAMES = {1: "front", 2: "front-left", 3: "its left", 4: "back-left", 5: "back", 6: "back-right",
                  7: "its right", 8: "front-right"}
SCHWER_HANDOFF = [
    "Lump name proposed: SDPS (SD + Panzermensch Schwer). It is free: no weapon or bestiary prefix of BESTIARY "
    "2.3 or MOD-SPEC 6.3 starts with it, no lump of ours in assets/ or src/ does, and freedoom2.wad has none "
    "starting with SD. It needs a line in MOD-SPEC 6.3's bestiary table and in BESTIARY 2.3's prefix list.",
    "What mod-engineer changes in SD_PanzermenschSchwer (src/zscript/monsters/panzermensch_schwer.zs): today the "
    "class has no States and inherits SD_Panzermensch's, so it draws whatever the base draws. It gets its own "
    "States block, a copy of the base's with SDPS for the sprite name and nothing else changed (Spawn SDPS AB 10 "
    "A_Look; See SDPS A 3 A_SD_PanzerStep, SDPS ABBCCDD 3 A_Chase; Melee/Missile SDPS EF 8, SDPS G 8 "
    "A_SD_MeleeOrMissile(...); Pain SDPS H 2, H 2 A_Pain; Death SDPS I-N 8 with A_Scream on J and A_NoBlocking "
    "on L, SDPS O -1; Raise SDPS O 8, NMLKJI 8). About 30 lines; A_SD_PanzerStep and the constants are "
    "inherited, so they resolve as they do today. The header comment's 'a Translation recolours it' goes.",
    "Two consequences to weigh. (1) The sprite is 12 % taller (about 84 px) than the actor's Height 64, which the "
    "class inherits: a player shooting the top of the stacks hits nothing. Height 72 (64 x 1.12) would match "
    "the drawing and still clear the 72-unit arenas BESTIARY 8 asks for, but it changes where he fits, which is "
    "the level-designer's and the PM's call, not art's. Radius 24 x 1.12 = 27 likewise. (2) Its death differs "
    "on purpose (it falls on its face, the stacks forbid lying on its back): the Raise state reverses it as "
    "for the base.",
]


def _states_rows(key: str) -> list[list]:
    """Each state of the class: its frames and tics (runs merged), the rotations they are drawn at."""
    st = zs_states(FULL_SPECS[key].zs)
    rotated, _ = full_frames(key)
    rows = []
    for label, seq in st.items():
        if not seq:
            continue
        letters = "".join(dict.fromkeys(f for f, _ in seq))
        rows.append([label, " ".join(f"{f} {t}" for f, t in hound._gif_runs(seq)),
                     "1-8" if all(f in rotated for f in letters) else "0", letters])
    return rows


def _crop_tiles(arrs: list[np.ndarray], zoom: int, caps: list[str], subs: list[str] | None = None) -> str:
    subs = subs or [""] * len(arrs)
    return _strip([core.sprite_tile(a, zoom, c, s) for a, c, s in zip(hound.crop_common(arrs), caps, subs)])


def _verdict(key: str, met: dict, ident: dict) -> tuple[list[str], list[str]]:
    c = met["corpse"]
    shares = met["blood_share"]
    same = [k for k, v in ident.items() if v]
    if key == "db":
        verdict = [
            "WHAT THIS IS. D65: cell C as chosen, the severed head with the spine hanging and the dark-red drip, drawn "
            "to its hitbox (50 px across, radius 31 actor). Every letter doughboy.zs names: A floats (Spawn and See), "
            "B C D the attack (it draws breath and the shell kindles in its throat, the mouth gapes with the shell "
            "white-hot in it, it spits), E F the pain (it jerks back screaming, a round's hole in its left cheek, then "
            "rights itself bleeding), at 8 drawn rotations; G-L the death at rotation 0. 54 lumps. No gib: the class "
            "has no XDeath. The sweep's views are its pixels byte for byte except where the flag decal shows, "
            f"made bigger by D67 (identical: {', '.join(same) or 'none'}).",
            "EIGHT ROTATIONS, NOT MIRRORED PAIRS. The figure is handed: the helmet sits askew to its right, the flag "
            "decal and the buckle are on one side, the wound on the other. A mirror would move them.",
            "THE DEATH. G: the eye bursts while it is still in the air (the burst flies from the socket). The engine "
            "drops a dead floater (its +FLOAT and +NOGRAVITY go when it dies: what every Doom cacodemon visibly "
            "does, NOT VERIFIED in GZDoom here); the floor GIF lets it fall under Doom's gravity from its hover. H: it "
            "lands, splits and the helmet flies off; I-K it rolls back onto its crown and deflates; L lies face up as "
            "a flat sack in a wide pool, the socket and the mouth to the sky, the spine fallen out across the floor, "
            "the helmet upside down beside it. "
            f"Measured (section 5): sack, spine and helmet each touch the floor; the body stands {c['top']} units "
            f"at most (the test: under {DB_LYING_TOP:.0f}); what touches spreads {c['span']} units. Blood is "
            + ", ".join(f"{k} {v:.0%}" for k, v in shares.items()) + " of the death frames' pixels.",
            "WHAT DOES NOT, HONESTLY. The attack's three frames differ mostly inside the mouth: at 1x B, C and D read "
            "as 'the mouth opens' more than as three moments. The pain's tilt is small at range. The corpse is seen "
            "from 27 degrees (the hound's approved corpse is seen from 37; from there the sack's top filled the "
            "screen), and it is still the biggest corpse in the game: the head is 50 units across (the hitbox), "
            "deflated it spreads to about 64, and the upside-down helmet beside it is the tallest thing on the "
            "floor (about 25 units). The helmet keeps no decal (a stamp cannot turn over with it). The veins still read as cracks (the sweep said so).",
            "NOT VERIFIED. Outside the engine (D26): the light is gen_enemy's stand-in, rotations are rig_core's "
            "reading of r_things.c, the hover (28 units) and the fall are from memory of P_ZMovement. The PM's "
            "engine pass, with the draft overlay (MOD-SPEC 6.9), is pending.",
        ]
        ask = ["Approve the 54 SDDB lumps as drawn, or name the frames to redo (the corpse L above all: does the "
               "flat sack read as the dead Doughboy?).",
               "On approval: mod-engineer renames HEAD to SDDB in doughboy.zs (the letters already match) and the "
               "lumps go to assets/sprites/; the shell SDDL is not drawn yet (next batch)."]
    else:
        schwer = key == "ps"
        verdict = [
            ("WHAT THIS IS. D65: the Schwer is cell D with the sweep's S2 treatment, the PM's call: black plate, 12 % "
             "larger, the spikes AND the exhaust stacks and side skirts, the mask's slit lit. Its own set of every "
             "frame the Panzermensch's states name, under the proposed sprite SDPS (section 8 for the name and the "
             "class change). 71 lumps."
             if schwer else
             "WHAT THIS IS. D65: cell D as chosen, the bare khaki skull under a riveted iron mask, bare arms bolted "
             "through, the red banner on his back. Every letter panzermensch.zs names: A-D the walk (Spawn idles on "
             "A B), E F G the attack (he draws back with the shell forming in his fist, cocks it over his head, "
             "throws: the sweep's G), H the pain, at 8 drawn rotations; I-O the death at rotation 0. 71 lumps. No "
             "XDeath: Doom's bruisers do not gib (BESTIARY 8). The sweep's views are its pixels byte for byte "
             f"({', '.join(same) or 'sweep PNGs not on disk'})."),
            "EIGHT ROTATIONS, NOT MIRRORED PAIRS. The banner carries the D12 symbol, which a mirror reverses, and he "
            "throws with his right.",
            ("THE DEATH. He cannot lie on his back: the stacks would prop him off the floor (the Legion's first L0 "
             "fault). Hit at I, he folds forward (J), falls on his face (K, L), and lies prone across the screen with "
             "the stacks and the banner on top, the pool spreading from under his chest."
             if schwer else
             "THE DEATH. Hit in the chest at I (the burst, the stain on the plate), his knees go at J, he falls back "
             "over his heels twisting (K), hits the floor (L) and lies on his back across the screen; head, arms "
             "(from the shoulder, then the forearm from the elbow) and legs are each let fall until they touch, "
             "and the pool grows under his chest and head (M-O).")
            + f" Measured on the corpse O: every part within {PM_LYING_MAX:.0f} units of the floor (section 5), the "
              f"body {c['top']} units high at most unscaled (the test: under {PM_LYING_TOP:.0f}), the supports spread "
              f"{c['span']} units, the torso lying across the screen ({c['across']}). Blood is "
            + ", ".join(f"{k} {v:.0%}" for k, v in shares.items()) + " of the death frames' pixels.",
            "WHAT DOES NOT, HONESTLY. He is the darkest thing in the mod, as BESTIARY 2.1 wants, so in Z10 at light "
            "96 he is a dark shape with khaki arms and skull; the plate reads very dark olive, not neutral black. "
            "The walk's four frames differ mostly in the legs from the front (side views show the stride). The "
            "wind-up E hides the forming shell behind him from the front. The corpse is seen from 37 degrees, as the "
            "approved hound's. The death frames' blood spray is 1-2 px dots at 1x: spray in motion, noise on a still."
            + (" The sprite is 12 % taller than the hitbox it inherits (section 8)." if schwer else ""),
            "NOT VERIFIED. Outside the engine (D26): the light stand-in, the rotation order, the grAb offsets "
            "(rig_core's, as every approved enemy). The PM's engine pass is pending.",
        ]
        ask = (["Approve the 71 SDPS lumps as drawn, or name the frames to redo; and the name SDPS.",
                "On approval: mod-engineer gives SD_PanzermenschSchwer its own States on SDPS (section 8) and the "
                "lumps go to assets/sprites/; whether its Height and Radius grow with the drawing is the PM's and "
                "level-designer's call."]
               if schwer else
               ["Approve the 71 SDPM lumps as drawn, or name the frames to redo (the corpse O: lying naturally?).",
                "On approval: mod-engineer renames BOS2 to SDPM in panzermensch.zs (the letters already match) and "
                "the lumps go to assets/sprites/; the shell SDPL is not drawn yet (next batch)."])
    return verdict, ask


BEFORE_FLAG = "before_flag"     # SDDB's lumps as the CEO saw them before D67, kept for the before/after
FLAG_VIEWS = (("A", 1), ("A", 2), ("A", 8), ("D", 1), ("E", 1), ("G", 0), ("H", 0))


def flag_changes(spr: dict, before: dict) -> tuple[list[str], tuple[int, int]]:
    """The lumps whose pixels differ from the set before D67, and the size of
    the largest box the differences fit in (the decal's, if nothing else moved)."""
    changed, box = [], (0, 0)
    for (f, r), a in spr.items():
        b = before.get((f, r))
        if b is None or a.shape != b.shape:
            changed.append(full_lump("db", f, r))
            continue
        d = np.any(a != b, axis=-1)
        if d.any():
            ys, xs = np.nonzero(d)
            changed.append(full_lump("db", f, r))
            box = (max(box[0], int(np.ptp(xs)) + 1), max(box[1], int(np.ptp(ys)) + 1))
    return sorted(changed), box


def _flag_section(spr: dict, before: dict) -> tuple[str, str, str]:
    """D67: the flag on the helmet, before and after, at 3x and 1x and in the hangar."""
    changed, box = flag_changes(spr, before)
    body = ""
    for zoom in (3, 1):
        tiles = []
        for f, r in FLAG_VIEWS:
            pair = hound.crop_common([before[(f, r)], spr[(f, r)]])
            name = full_lump("db", f, r)
            tiles += [core.sprite_tile(pair[0], zoom, f"{name} before"), core.sprite_tile(pair[1], zoom, f"{name} now")]
        body += _strip(tiles)
    ga = full_grab("db", "A")
    figs = [(before[("A", 1)], ga[0], ga[1] + HOVER), (spr[("A", 1)], ga[0], ga[1] + HOVER),
            (before[("A", 8)], ga[0], ga[1] + HOVER), (spr[("A", 8)], ga[0], ga[1] + HOVER)]
    af, al = _approved(APPROVED[:2])
    figs += af
    for sk, wall, light, what in DB_SCENES[:2]:
        sc = tall_lineup(figs, wall, light, FULL_SLOT * len(figs))
        body += _strip([_img_tile(sc, 1, f"{sk} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{sk} 2x")])
    body += ('<p class="lead">Left to right: SDDBA1 before, now; SDDBA8 before, now; '
             + html.escape(" · ".join(al)) + f", hung {HOVER} px as a floater. The decal was 5 x 4 px; it is "
             f"{len(DECAL_BIG[0])} x {len(DECAL_BIG)} now (a starred canton and seven stripes), stamped wherever "
             f"the helmet's front faces you: {len(changed)} of {len(spr)} lumps changed, every change inside a "
             f"{box[0]} x {box[1]} px box (the flag); the other lumps are byte for byte the set you saw.</p>")
    lead = ("Your note: \"ponle la bandera más grande en la cabeza\" (\"make the flag on its head bigger\"). The US flag on the helmet, before (left) and "
            "now (right), 3x then 1x, then in the hangar beside the approved infantries.")
    return "0 · The flag on the helmet (D67): before and now", lead, body


def build_full_sheet(key: str, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    spec = FULL_SPECS[key]
    spr = load_full(key)
    gifs = write_full_gifs(key, spr)
    base = load_full("pm") if key == "ps" and (set_dir("pm") / "SDPMA1.png").is_file() else None
    lines = full_lineups(key, spr, base)
    met = full_metrics(key, spr)
    ident = sweep_identity(key, spr)
    rotated, death = full_frames(key)
    sprite = spec.sprite
    titles = DB_FRAME_TITLES if key == "db" else {f: p.title for f, p in PM_FULL_POSES.items()}
    dtitles = ({"G": DB_FULL_POSES["G"].title, **{f: x.title for f, x in DB_FALLS.items()}} if key == "db" else
               {f: x.pose.title for f, x in pm_falls(PM[PM_FULL_KEY] if key == "pm" else SCHWER_CELL).items()})
    S = []
    before_dir = set_dir(key) / BEFORE_FLAG
    flagged = key == "db" and before_dir.is_dir()
    if flagged:
        before = {}
        for f, r in full_plan(key):
            with Image.open(before_dir / f"{full_lump(key, f, r)}.png") as im:
                before[(f, r)] = np.asarray(im.convert("RGBA")).copy()
        S.append(_flag_section(spr, before))
    # 1. the set
    body = sheetlib.table(["state", f"frames and tics ({spec.zs.name})", "rotations", "letters"], _states_rows(key), 9)
    body += (f"<p class=\"lead\">{len(full_plan(key))} lumps in <code>work/art/enemies/heavy/full/{sprite}/</code>, "
             f"named as the engine reads them: <code>{sprite}A1</code> ... <code>{sprite}{rotated[-1]}8</code>, "
             f"<code>{sprite}{death[0]}0</code> ... <code>{sprite}{death[-1]}0</code>. Eight drawn rotations (no "
             "mirrored pairs: the figure is handed). Each PNG carries its grAb offsets. No XDeath state, so no gib."
             "</p>")
    if key == "ps":
        body += ("<p class=\"lead\">The Schwer has no states of its own today: it inherits these from "
                 "<code>panzermensch.zs</code>. Section 8 says what changes.</p>")
    S.append(("1 · The set", f"Every frame {spec.name} needs, read from {spec.zs.name} (read, not edited).", body))
    # 2. turnaround
    body = _crop_tiles([spr[("A", r)] for r in range(1, 9)], 3, [full_lump(key, "A", r) for r in range(1, 9)],
                       [FULL_ROT_NAMES[r] for r in range(1, 9)])
    body += _strip([core.sprite_tile(spr[("A", r)], 1, full_lump(key, "A", r)) for r in range(1, 9)]
                   + [core.gif_tile(gifs["turntable"], 3, "turntable", "12 tics a rotation")])
    if ident:
        body += ("<p class=\"lead\">The sweep's views, byte for byte: "
                 + html.escape(", ".join(f"{k} {'identical' if v else ('differs' if v is False else 'no sweep PNG')}"
                                         for k, v in ident.items())) + ".</p>")
    S.append(("2 · Turnaround: frame A at the 8 rotations", "3x on neutral grey, then 1x. 1 faces you, 3 shows its "
              "left side, 5 its back, 7 its right.", body))
    # 3. cycles
    body = ""
    if key == "db":
        body += _strip([core.gif_tile(gifs[f"attack_rot{r}"], 3, f"attack, rotation {r}", "A, B 5, C 5, D 5")
                        for r in range(1, 9)])
        body += _strip([core.gif_tile(gifs[f"pain_rot{r}"], 3, f"pain, rotation {r}", "A, E 6, F 6")
                        for r in (1, 3, 5, 7)])
        lead = ("At the tics of doughboy.zs, 35 a second. Spawn and See hold A (Doom's one-frame float); the attack "
                "is Missile B C D at 5 tics (D Bright); the pain E E F at 3, 3, 6. Each loop starts on A for 20 tics.")
    else:
        body += _strip([core.gif_tile(gifs[f"see_rot{r}"], 3, f"walk, rotation {r}", "A B C D, 6 tics each")
                        for r in range(1, 9)])
        body += _strip([core.gif_tile(gifs[f"attack_rot{r}"], 3, f"attack, rotation {r}", "walk, E 8, F 8, G 8")
                        for r in (1, 3, 5, 7)])
        body += _strip([core.gif_tile(gifs[f"pain_rot{r}"], 3, f"pain, rotation {r}", "walk, H 4, walk")
                        for r in (1, 3, 5, 7)] + [core.gif_tile(gifs["spawn_rot1"], 3, "Spawn", "A B, 10 tics")])
        lead = ("At the tics of panzermensch.zs, 35 a second: See SDPM AABBCCDD at 3 tics (6 a picture; the plated "
                "footstep sounds on A), Melee/Missile E F G at 8, Pain H H at 2, Spawn A B at 10.")
    S.append(("3 · The cycles at game speed", lead, body))
    # 4. every frame
    body = ""
    for f in rotated:
        body += _crop_tiles([spr[(f, r)] for r in range(1, 9)], 2, [full_lump(key, f, r) for r in range(1, 9)],
                            [titles.get(f, "")] + [""] * 7)
    S.append(("4 · Every living frame at every rotation", "2x, each row one frame letter.", body))
    # 5. death
    max_tilt = max(x.tilt for x in (DB_FALLS.values() if key == "db" else
                                    pm_falls(PM[PM_FULL_KEY] if key == "pm" else SCHWER_CELL).values()))
    body = _crop_tiles([spr[(f, 0)] for f in death], 3, [f"{sprite}{f}0" for f in death],
                       [dtitles.get(f, "") for f in death])
    body += _strip([core.gif_tile(gifs["death"], 3, "death, game speed", " ".join(
                        f"{f} {t}" for f, t in hound._gif_runs(zs_states(spec.zs)["Death"]))),
                    core.gif_tile(gifs["death_floor"], 1, "on MAP01's floor, 1x", "from the living frame"),
                    core.gif_tile(gifs["death_floor"], 3, "on MAP01's floor, 3x"),
                    core.sprite_tile(hound.crop_common([spr[(death[-1], 0)]])[0], 5, f"{sprite}{death[-1]}0 at 5x",
                                     "the corpse")])
    c = met["corpse"]
    body += sheetlib.table([f"part of {sprite}{death[-1]}0", "lowest point above the floor (units)"],
                           [[k, v] for k, v in c["lowest"].items()], 1)
    lim = (DB_LYING_MAX, DB_LYING_TOP) if key == "db" else (PM_LYING_MAX, PM_LYING_TOP)
    body += (f"<p class=\"lead\">The corpse measured on its model, untilted{' and unscaled' if key == 'ps' else ''}: "
             f"each part within {lim[0]:.0f} units of the floor (above or below), the body's highest point "
             f"{c['top']} units (under {lim[1]:.0f}), the parts on the floor spread {c['span']} units. "
             "tests/test_gen_heavy.py holds it. Blood, share of the death frames' pixels: "
             + ", ".join(f"{k} {v:.0%}" for k, v in met["blood_share"].items()) + ".</p>")
    S.append(("5 · The death, rotation 0, with the blood",
              "Dark red only, flag_red 0-5 and black (D49). The frames on the floor are seen from higher as they "
              f"fall (up to {9 + max_tilt:.0f} degrees; the approved hound's corpse is seen from 37), because a "
              "player looks down at a body.", body))
    # 6. at 1x on MAP01
    body = ""
    for sk, (sc, wall, light, what) in lines["scenes"].items():
        body += _strip([_img_tile(sc, 1, f"{sk} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{sk} 2x, for the eye")])
    worst = list(lines["scenes"].values())[0][0]
    farv = flat.far(worst)
    val = np.repeat(flat.luma(farv)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
    body += _strip([_img_tile(farv, 5, "game distance /4", "first scene"), _img_tile(val, 5, "the same, value only")])
    body += ('<p class="lead">Left to right: ' + html.escape(" · ".join(lines["labels"]))
             + (f". The Doughboy hangs {HOVER} px above the floor (a floater's height beside a man; NOT VERIFIED)"
                if key == "db" else "") + ". Each sprite by its own offsets, as the engine places it.</p>")
    for light in (176, 128):
        sd = lines[f"dead_{light}"]
        body += _strip([_img_tile(sd, 1, f"the dead, 1x, SDCONC1 at {light}"), _img_tile(sd, 2, "2x")])
    body += '<p class="lead">The dead: ' + html.escape(" · ".join(lines["dead_labels"])) + ".</p>"
    S.append(("6 · At 1x on MAP01 beside the approved enemies",
              "Approved sprites read from assets/sprites/ (rifleman D55, Legion trooper D54, Stormtrooper D56, "
              "hound D55). Light is gen_enemy's stand-in re-quantised to palette v2, NOT VERIFIED against GZDoom.",
              body))
    # 7. numbers
    fm, sm = met["front"], met["side"]
    rows = [["front A1", f"{fm['height_px']} x {fm['width_px']}", fm["body_luma"], fm["worst_gap"], fm["worst_sep"]],
            ["side A3", f"{sm['height_px']} x {sm['width_px']}", sm["body_luma"], sm["worst_gap"], sm["worst_sep"]]]
    body = sheetlib.table(["view", "h x w px", "body luma", "worst gap", "worst share apart"], rows, 2)
    hts = met["heights"]
    body += sheetlib.table(["lump", "height px"], [[k, v] for k, v in hts.items() if k[5] in "15" or k[5] == "0"], 1)
    S.append(("7 · Numbers", "Size and value as the sweep measured them; the height of every lump at rotations 1, "
              "5 and 0.", body))
    # 8. verdict
    verdict, ask = _verdict(key, met, ident)
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in verdict) + "</div>"
    if key == "ps":
        body += "<h3>The name and the class change (for mod-engineer)</h3><div class=\"verdict\">" + "".join(
            f"<p>{html.escape(v)}</p>" for v in SCHWER_HANDOFF) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in ask) + "</ol></div>"
    S.append(("8 · Honest verdict and what you decide", "", body))
    intro = (f"D65: \"Doughboy C · Panzermensch D\". {html.escape(spec.name)}: every frame its states name, "
             "rendered on the rig the four approved enemies were drawn on, with D49's dark red blood and a corpse "
             f"that lies flat on the floor. Built by <code>tools/art/gen_heavy.py --full {key}</code> on "
             f"rig_core (imported, not edited), seed {SEED}, no system fonts. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_heavy.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic. Approved "
              "sprites read from assets/sprites/ for scale. MAP01 walls and flats are the mod's own.")
    path = out_dir / f"{stamp}_F5_{'doughboy-C-big-flag' if flagged else spec.slug}.html"
    sheetlib.write_sheet(path, lang="en", title=f"{spec.name}: full set (F5, D65)",
                         subtitle=f"{sprite} · {len(full_plan(key))} lumps · 8 rotations · death with blood · draft",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--full", default="", help="D65: the full sets, comma-separated keys db,pm,ps (or 'all'), "
                                                 "into work/art/enemies/heavy/full/<SPRITE>/ (the sweep is untouched)")
    ap.add_argument("--jobs", type=int, default=1, help="with --full: worker processes")
    ap.add_argument("--sheet-only", action="store_true", help="with --full: GIFs, lineups and sheets from the lumps on disk")
    ap.add_argument("--only", default="", help="with --full: frames to render, e.g. db:L,pm:O (no sheet)")
    args = ap.parse_args()
    if args.full:
        keys = tuple(FULL_SPECS) if args.full == "all" else tuple(k.strip() for k in args.full.split(","))
        only = {x.strip() for x in args.only.split(",") if x.strip()} or None
        if not args.sheet_only:
            build_full(keys, jobs=args.jobs, only=only)
        if only or args.no_sheet:
            return
        for key in keys:
            print("sheet:", build_full_sheet(key, args.stamp).relative_to(PROJECT_ROOT), flush=True)
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_all()
    lines = write_lineups(data)
    print(json.dumps(data["metrics"], indent=1))
    if not args.no_sheet:
        print(build_sheet(data, lines, args.stamp))


if __name__ == "__main__":
    main()
