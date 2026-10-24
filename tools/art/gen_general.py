"""F5 — the General, episode boss: design sweep on the 3D rig (backlog N12, D35).

HISTORICAL since D109 (2026-10-22) for the General's rig set (`SDGN`, D71-D73).
The General who ships is redrawn from Google Gemini images by
tools/art/gemini_enemy.py (general); this generator is kept so the approved F5
renders stay reproducible, but its output no longer matches assets/. Still
current: the shell `SDGL` (`shell_model`, `render_shell`), which was not
redrawn.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_general.py               (Windows)
    .venv/bin/python tools/art/gen_general.py                       (macOS)
    ... gen_general.py --stamp 2026-10-14_2157   fixes the sheet's timestamp
    ... gen_general.py --no-sheet                sprites, lineups and metrics only
    ... gen_general.py --only A                  one cell's sprites (a quick look, no sheet)
    ... gen_general.py --turnaround              D71: cell CD (C's front, D's back) turned round, its sheet
    ... gen_general.py --full --jobs 6           D72: CD's full set (81 SDGN + 5 SDGL), GIFs, its sheet
    ... gen_general.py --full --frames P         a few frames only, for a quick look (no sheet)

What this is. The General (`SD_General`, sprite `SDGN`, BESTIARY §9) is the
last enemy still wearing Freedoom (CYBR, the Cyberdemon). He is MAP03's
boss, «Танкоград», met in the portal hall (docs/levels/MAP03-factory.md:
brick SDBRCK1 at light 128, the drum's steel ring, the portal's cobalt).
Before ~60 images exist the CEO makes ONE decision, what he looks like, as
with the heavies (D65): a SWEEP (PIPELINE stage 2) of labelled cells, each
at rotations 1, 3 and 5 and in the firing frame, then at 1x in the portal
hall beside the approved rifleman, trooper, Panzermensch and Schwer and
the Freedoom placeholder, then as a 16-px silhouette. Nothing goes to
assets/.

The brief (BESTIARY §9): "tall and unhurried, a chromed cuirass over a pale
greatcoat that flares at the knee; a peaked cap with too much braid; the
face is a smooth chrome plate with a single slot. A swastika pennant on one
shoulder, a star-spangled one on the other." Colour: steel_blue chrome,
plaster_warm coat, flesh_pink at the throat, hazard_yellow braid; he is the
only actor that wears both insignia (D12) because he is the alliance. His
16-px silhouette is an HOURGLASS (cap wedge on top, coat flare below),
unlike every other enemy's rectangle, and he is BRIGHT: the Legion is the
light faction, and the Panzermensch, the other big man, is the darkest mass
in the game. He orders; he does not brawl (D35): one verb, the summon.

The cells (A is the brief taken literally; each other cell changes one
thing from it, so a cell is read against A):

        face                     weapon (the salvo)          flags                chest
    A   chrome plate, one slot   long chrome revolver        two shoulder pennants  chrome cuirass
    B   pink, aviators and pipe  as A                        as A                   as A
    C   as A                     a field gun on his right    as A                   as A
                                 shoulder; he points a
                                 swagger stick ("Vorwärts")
    D   as A                     as A                        both flags as one      as A
                                                             cloak, Reich | Legion
    E   as A                     as A                        as A                   dress coat: no cuirass,
                                                                                    medals, aiguillette

Scale. His actor is 40 x 100 (BESTIARY §9, Cyberdemon radius, 10 units
shorter); a humanoid's Height is px at 1:1 (rig_core.DOOM_HEIGHT), so he is
drawn ~97 px tall, against the infantry's 56 and the Panzermensch's ~70:
a man of the infantry's proportions at 1.75 times their size, not a brute.

How it is built. Everything that draws is tools/art/rig_core.py, imported,
not edited. The material table is a COPY of the Legion trooper's
(gen_legion.MATERIALS: his chrome, flesh_pink, his belt and boots), with
the General's appended (rig_core.register_material: append-only, so no
approved id moves). gen_legion, gen_heavy and rig_core are imported, never
edited; gen_heavy lends its draft-PNG writer, scale-free helpers and the
16-px silhouette.

Palette: v2 (D45) for flesh_pink; the faction contract of ART-BIBLE §6 /
BESTIARY §2.1: no khaki_olive (the Reich's) and no military_green (the
world's) in any of his materials; the only saturated red on him is on the
two flags (§6.3, accent exclusivity). Scenes are re-quantised to palette v2
whole (the light stand-in, RGB x L/224; NOT VERIFIED against GZDoom).

NO FONTS. The sprites carry no text; the sheet is HTML (sheetlib), labels
are the browser's text; the PNG contact sheet's cell letters are hard-pixel
glyphs drawn from the GLYPHS table below, not a font. tests/test_gen_general.py
keeps it so.

Outputs (work/ is gitignored):
    work/art/general/SDGN_<cell>_<frame><rot>.png     RGBA, hard alpha, grAb
    work/art/general/lineup_<scene>.png, metrics.json
    docs/art/previews/<stamp>_F5_general-sweep.html   the sheet
    docs/art/previews/<stamp>_F5_general-sweep.png    its contact sheet
    work/art/general/turnaround/SDGN_CD_<frame><rot>.png, lineup_<scene>.png, metrics.json (D71)
    docs/art/previews/<stamp>_F5_general-CD-turnaround.html (+ .png)
"""

from __future__ import annotations

import argparse
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
import gen_heavy as heavy  # noqa: E402  (draft writer, approved-sprite reader, silhouette tiles, settling)
import gen_hound as hound  # noqa: E402  (zs reader, pools, crops, GIF runs)
import gen_legion as legion  # noqa: E402  (the Legion's table: chrome, flesh_pink; its flag colours)
import palette as palgen  # noqa: E402
import rig_core as core  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "general"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
ASSETS = PROJECT_ROOT / "assets"

SPRITE = "SDGN"                 # BESTIARY §9, MOD-SPEC §6.3
SEED = 106                      # DoomEdNum 21106: the cloth grain
ACTOR_HEIGHT = 100              # SD_GENERAL_HEIGHT (general.zs): px at 1:1
ACTOR_RADIUS = 40               # SD_GENERAL_RADIUS
V = core.V
Mat = core.Mat
FLESH = legion.FLESH            # palette v2 flesh_pink (D45)

CV = core.Canvas(136, 124, 68, 118)     # ~97 px of man, the pennants, the gun reaching out in profile

# ================================================================ materials
GN_NEW: dict[str, Mat] = {
    # The greatcoat: plaster_warm, cloth, lifted like the trooper's pale
    # trousers so the coat stays the light mass the Legion's value plan wants.
    "greatcoat": Mat((("plaster_warm", 4, 15),), cloth=True, lift=0.08),
    "cap_crown": Mat((("plaster_warm", 5, 15),), lift=0.04),
    "braid": Mat((("hazard_yellow", 6, 15),)),                       # "too much braid"
    "cap_band": Mat((("black",), ("steel_blue", 0, 5))),
    # Patent leather and polished riding boots: black that shines, so chrome
    # shading on a dark run (the reflection, not the light, sets the value).
    "peak": Mat((("black",), ("steel_blue", 0, 9)), "chrome"),
    "boot_polish": Mat((("black",), ("steel_blue", 0, 5)), "chrome"),
    "glove": Mat((("plaster_warm", 12, 15), ("white",)), lift=0.1),  # white dress gloves
    "ivory": Mat((("plaster_warm", 10, 15),)),                      # the revolver's grips
    "slot": Mat((("black",),), flat=True),                          # the face plate's one slot
    # The two flags (D12): the only saturated red and blue on him (ART-BIBLE §6.3).
    "pennant_red": Mat.on_ramp("flag_red", 4, 11),
    "pennant_white": Mat((("plaster_warm", 9, 15),)),
    "us_blue": Mat.on_ramp("steel_blue", 1, 5),
    "lens": Mat((("black",), ("steel_blue", 0, 7)), "chrome"),      # B: aviators
    "corncob": Mat.on_ramp("cream_yellow", 5, 12),                  # B: the pipe's bowl
    "ribbon_blue": Mat.on_ramp("steel_blue", 2, 6),                 # E: medal ribbons
}
GN_MATERIALS: dict[str, Mat] = dict(legion.MATERIALS)
for _n, _m in GN_NEW.items():
    core.register_material(_n, _m, GN_MATERIALS)
VALUE_SHIFT = 0.0               # the Legion is the light faction: no shift (gen_rig darkens the Reich by 0.26)
# The trooper's chrome environment with a darker low sky: on a cuirass four
# times the trooper's, his sky (0.80-1.0) fills the chest with flat white;
# 0.62-0.96 keeps a gradient (gen_heavy did the same for the Doughboy's chrome).
CHROME = core.Chrome(horizon=-0.60, sky_lo=0.62, sky_hi=0.96, ground_lo=0.04, ground_span=0.30,
                     ground_fade=0.8, spec_cos=0.90, key=0.22, ao=0.5)

# What the General may NOT be drawn in (ART-BIBLE §6.2, BESTIARY §2.1); checked by the tests.
FORBIDDEN_RAMPS = {"khaki_olive", "military_green"}
# Light falloff. rig_core darkens the lower body by VERTICAL_FALLOFF over a
# 56-unit man; on a 100-unit one the same slope would make the cap 0.08
# brighter than the infantry's helmets. Lambert parts are re-based so the
# slope spans HIS height (chrome takes its value from the reflection and is
# left as the core draws it).
FALLOFF_SPAN = ACTOR_HEIGHT


# ================================================================ insignia
def stamp_drawer(pattern: tuple[str, ...], colours: dict):
    """An Insignia `draw` from rows of characters, like core.pattern_drawer,
    except that '_' is skipped (the cloth under it shows): a disc on a
    shaded red field, stars on a shaded blue canton. Never mirrored: a
    reversed swastika is wrong (rig_core.armband_draw) and the flags are
    printed on both faces."""
    def draw(rgba: np.ndarray, x0: int, y0: int, mirror: bool) -> None:
        del mirror
        for j, row in enumerate(pattern):
            for i, ch in enumerate(row):
                if ch == "_":
                    continue
                spec = colours[ch]
                col = (0, 0, 0) if spec is None else tuple(core.ramp(spec[0])[spec[1]])
                rgba[y0 + j, x0 + i] = (*col, 255)
    return draw


STAMP_COLOURS = {"R": ("flag_red", 11), "r": ("flag_red", 7), "K": None, ".": ("plaster_warm", 13),
                 "B": ("steel_blue", 3), "*": ("plaster_warm", 15), "W": ("plaster_warm", 14),
                 "Y": ("hazard_yellow", 12)}
# The two pennants, 7 x 12: the D12 armband's 7x7 symbol (gen_enemy.ARMBAND,
# the mod's one drawing of it) over a red tail; the Legion's 7x5 flag
# (gen_legion.FLAG) over a striped tail. A gold fringe ends both.
PENNANT_REICH = (
    "RRRRRRR",
    "RK.KKKR",
    "RK.K..R",
    "RKKKKKR",
    "R..K.KR",
    "RKKK.KR",
    "RRRRRRR",
    "RRRRRRR",
    "RRRRRRR",
    "rRRRRRr",
    "rrRRRrr",
    "YYYYYYY",
)
PENNANT_US = (
    "BBBRRRR",
    "B*BWWWW",
    "BBBRRRR",
    "WWWWWWW",
    "RRRRRRR",
    "WWWWWWW",
    "RRRRRRR",
    "WWWWWWW",
    "RRRRRRR",
    "WWWWWWW",
    "rRRRRRr",
    "YYYYYYY",
)
PENNANT_TILT = 25.0             # degrees: each pennant turned out from the front, so both read at rotation 1
_PEN_OUT = np.sin(np.deg2rad(PENNANT_TILT)), np.cos(np.deg2rad(PENNANT_TILT))
PEN_MIN_PX = 30


def _pennant_insignia(tag: str, pattern, side: int, back: bool) -> core.Insignia:
    s, c = _PEN_OUT
    out = (side * s, 0.0, c) if not back else (-side * s, 0.0, -c)
    return core.Insignia(tag, (len(pattern[0]), len(pattern)), stamp_drawer(pattern, STAMP_COLOURS),
                         outward=out, min_px=PEN_MIN_PX, search=2)


# His LEFT shoulder (+x) carries the Reich's, as the rifleman wears his
# armband; his RIGHT (-x) the Legion's, where the trooper wears his patch
# and the US Army its flag. Each pennant is stamped on whichever face is
# turned to the camera.
PENNANT_INSIGNIA = (
    _pennant_insignia("pen_reich", PENNANT_REICH, core.LEFT, False),
    _pennant_insignia("pen_reich", PENNANT_REICH, core.LEFT, True),
    _pennant_insignia("pen_us", PENNANT_US, core.RIGHT, False),
    _pennant_insignia("pen_us", PENNANT_US, core.RIGHT, True),
)


def _disc_pattern(size: int = 11, r: float = 5.4) -> tuple[str, ...]:
    """D's cloak: a white disc on the (shaded) red field with the 7x7
    symbol, the armband's drawn at 7 instead of 5, same handedness."""
    sym = ("K..KKKK",
           "K..K...",
           "K..K...",
           "KKKKKKK",
           "...K..K",
           "...K..K",
           "KKKK..K")
    c = (size - 1) / 2
    rows = []
    for j in range(size):
        row = ""
        for i in range(size):
            row += "." if (i - c) ** 2 + (j - c) ** 2 <= r * r else "_"
        rows.append(row)
    off = (size - 7) // 2
    out = []
    for j, row in enumerate(rows):
        chars = list(row)
        if off <= j < off + 7:
            for i, ch in enumerate(sym[j - off]):
                if ch == "K":
                    chars[off + i] = "K"
        out.append("".join(chars))
    return tuple(out)


CLOAK_DISC = _disc_pattern()
CLOAK_DISC_RISE = 14            # px above the half's visible centre: between the shoulder blades
CANTON_STARS = (
    "*_*_*",
    "_*_*_",
    "*_*_*",
    "_*_*_",
    "*_*_*",
    "_*_*_",
    "*_*_*",
)
CLOAK_INSIGNIA = (
    core.Insignia("cape_reich", (len(CLOAK_DISC[0]), len(CLOAK_DISC)), stamp_drawer(CLOAK_DISC, STAMP_COLOURS),
                  outward=(0.0, 0.0, -1.0), min_px=60, search=2,
                  anchor=((len(CLOAK_DISC[0]) - 1) / 2, (len(CLOAK_DISC) - 1) / 2 + CLOAK_DISC_RISE)),
    core.Insignia("canton", (len(CANTON_STARS[0]), len(CANTON_STARS)), stamp_drawer(CANTON_STARS, STAMP_COLOURS),
                  outward=(0.0, 0.0, -1.0), min_px=30, search=1),
)


# ================================================================ helpers
def unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def tilt(prim: core.Prim, R: np.ndarray, pivot) -> core.Prim:
    """Rotate one primitive rigidly about a pivot (an ellipsoid has no
    local frame of its own): the cap's crown and peak, a swinging pennant."""
    pivot = np.asarray(pivot, float)
    prim.xm = R @ prim.xm
    prim.xt = R @ (prim.xt - pivot) + pivot
    return prim


def even_light(prims: list[core.Prim], materials: dict[str, Mat]) -> None:
    """Re-base the Lambert parts so the core's vertical falloff spans the
    General's height, not a 56-unit man's (FALLOFF_SPAN). The core adds
    -VERTICAL_FALLOFF * (0.5 - y / 56); this adds back the difference to
    -VERTICAL_FALLOFF * (0.5 - y / FALLOFF_SPAN) at each part's centre."""
    k = core.VERTICAL_FALLOFF * (1.0 / core.DOOM_HEIGHT - 1.0 / FALLOFF_SPAN)
    for p in prims:
        if materials[p.mat].shading == "chrome" or materials[p.mat].flat:
            continue
        y = float(p.bound()[0][1])
        p.base = p.base - k * y


# ================================================================ cells
@dataclass(frozen=True)
class Cell:
    key: str
    face: str           # "plate" (chrome, one slot) | "aviator" (pink, aviators, corncob pipe)
    weapon: str         # "revolver" | "shoulder" (field gun on the shoulder, swagger stick in hand)
    flags: str          # "pennants" | "cloak" | "both" (D71: the pennants and a fitted cloak)
    chest: str          # "cuirass" | "dress"
    title: str


CELLS = (
    Cell("A", "plate", "revolver", "pennants", "cuirass",
         "Brief: chrome face plate, braided cap, cuirass over a flared greatcoat, two pennants, revolver"),
    Cell("B", "aviator", "revolver", "pennants", "cuirass",
         "As A with a face: pink, aviator glasses, a corncob pipe"),
    Cell("C", "plate", "shoulder", "pennants", "cuirass",
         "As A, a field gun on his shoulder fires; his hand only points the stick"),
    Cell("D", "plate", "revolver", "cloak", "cuirass",
         "As A, the two flags worn as one cloak, Reich and Legion halves"),
    Cell("E", "plate", "revolver", "pennants", "dress",
         "As A in dress uniform: no cuirass, medals, aiguillette, buttons"),
)
# D71 (CEO, 2026-10-14): "la C de frente (para que se vean las banderas) y
# la D de espaldas (con esa capa)" ("C from the front, so the flags show,
# and D from the back, with that cloak"). C as drawn, pennants and all, with D's
# cloak hung down his back and FITTED (see _cloak) so that nothing of it
# shows from the front: from rotation 1 he is C, from rotation 5 he is D.
CD = Cell("CD", "plate", "shoulder", "both", "cuirass",
          "D71: C from the front (the gun, both pennants), D's two-flag cloak down his back")
CELL = {c.key: c for c in CELLS + (CD,)}


@dataclass(frozen=True)
class Pose:
    key: str
    title: str
    foot_l: tuple
    foot_r: tuple
    hand_r: tuple       # the right wrist's target (the weapon hand)
    hand_l: tuple       # the left wrist's target (behind his back: unhurried)
    aim: tuple          # the weapon's direction (the revolver's barrel, the stick)
    aim_up: tuple       # roughly the weapon's top
    twist: float = 0.0          # degrees about the waist; - brings his RIGHT shoulder forward
    swing_r: float = 0.0        # degrees the right pennant swings out of the raised arm's way
    fire: bool = False
    # The full set's posing (D72); every default leaves the sweep's and the
    # turnaround's figure exactly as it was.
    bob: float = 0.0            # units the hips (and all above them) move up (+) or down (-): knees bend
    lean: float = 0.0           # degrees about the waist, chest and head only; + tips him back
    head_pitch: float = 0.0     # degrees about the neck; + tips the head back (chin up)
    head_turn: float = 0.0      # degrees about the neck; + turns the face to his left
    hem_tilt: float = 0.0       # degrees the coat's skirt swings about the waist; + hem forward
    hem_roll: float = 0.0       # degrees it swings sideways; + hem to his right
    cloak_swing: float = 0.0    # degrees CD's cloak (its lower half) trails; + hem backward
    swing_l: float = 0.0        # degrees the left pennant swings out of the raised arm's way
    pole_l: tuple | None = None     # the elbows' bend direction, when the default does not fit the pose
    pole_r: tuple | None = None
    no_cap: bool = False        # the death: the cap has come off (drawn apart, see death_model)
    no_sgun: bool = False       # ... and the field gun off his shoulder
    sgun_knock: float = 0.0     # degrees the field gun is knocked up on its cradle (the death's I)
    coat_flat: bool = False     # the dead: the coat's skirt collapses (no tent over the legs)
    spread: bool = False        # the dead: the cloak lies spread under him instead of hanging


ANKLE_Y = 3.6
# BESTIARY §9's frames, Cyberdemon layout: A-D walk, E-F the salvo (F fires).
POSES = {
    "A": Pose("A", "walk (A)", (6.8, ANKLE_Y, 5.5), (-6.8, ANKLE_Y, -4.5),
              (-17.0, 46.5, 5.5), (5.5, 53.5, -11.5), (0.05, -0.80, 0.60), (0.0, 0.30, 1.0)),
    "F": Pose("F", "fires (F)", (7.0, ANKLE_Y, 2.5), (-7.5, ANKLE_Y, -2.5),
              (-13.0, 70.5, 25.5), (5.5, 53.5, -11.5), (-0.10, 0.02, 1.0), (0.0, 1.0, 0.0),
              twist=-8.0, swing_r=32.0, fire=True),
}
# What each cell shows: (frame, rotation). 1 front, 3 his left side, 5 his back.
VIEWS = (("A", 1), ("A", 3), ("A", 5), ("F", 1))
ROT_NAMES = {1: "front", 3: "his left side", 5: "his back"}

# ================================================================ the body
# A man of the infantry's proportions, ~1.75 times their size (BESTIARY §9:
# 100 units against their 56). +x is his LEFT, +z forward, feet on y = 0.
HIP_Y, HIP_X = 47.0, 6.2
THIGH, SHIN = 22.4, 21.6
UPPER_ARM, FOREARM = 17.0, 15.5
SHOULDER = (15.0, 73.5, -0.5)
WAIST_Y, CHEST_Y = 55.0, 73.0
TORSO_R0, TORSO_R1, TORSO_KZ, TORSO_Z = 10.5, 14.0, 0.70, -0.4
HEM_Y, HEM_R, COAT_KZ, COAT_Z = 21.0, 18.5, 0.80, -0.6   # the flare: the coat ends just under the knee
HEAD_C, HEAD_R = (0.0, 84.6, 0.8), (5.3, 6.4, 5.7)
NECK = V(0.0, 77.0, 0.0)
WAIST = V(0.0, WAIST_Y, 0.0)
UPPER = {"upper", "arm", "head", "cap", "pen_l", "pen_r", "gun", "cape", "coat", "sgun", "cape_lo", "spread"}
# What the waist's lean moves: the chest, arms and head, not what hangs from
# the waist (the coat's skirt and the cloak's lower half keep hanging).
LEAN = UPPER - {"coat", "cape_lo", "spread"}
CLOAKS = {"cape", "cape_lo"}
FLASH_SIZE = 9.0                # his salvo's flash: half again the rifle's 6
CAPE_Y0, CAPE_Y1 = 20.0, 75.5
CAPE_R0, CAPE_R1, CAPE_KZ, CAPE_Z, CAPE_BACK = 21.5, 15.5, 0.85, -1.0, -2.2
US_STRIPES = 13
CANTON_STRIPES = 7              # the canton covers the first seven stripes ...
CANTON_DROP = 22.0              # ... for this many units down from the shoulders (a flag hung vertically)
# CD's fitted cloak (D71, fitted_segments): from under the pauldrons to just
# above the coat's hem, never wider than the body in front of it.
CD_CAPE_Y0 = HEM_Y + 1.5        # its bottom: the hem hides it from the front
CD_CAPE_WAIST = WAIST_Y + 1.0   # the two trims meet at the coat's top
CD_CAPE_Y1 = 71.0               # its top: under the pauldrons (clipped at 70.5) and the cuirass's shoulders
CD_TRIM = 1.2                   # units inside the coat's / cuirass's width
CD_CAPE_KZ = 0.72               # flatter than D's 0.85: it stands ~1 unit off the coat's back at the hem, so
                                # at rotations 2 and 8 only a sliver of its edge shows past the coat


def torso_z(x: float, y: float) -> float:
    """The cuirass's front surface at (x, y)."""
    r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - WAIST_Y) / (CHEST_Y - WAIST_Y)
    return TORSO_KZ * float(np.sqrt(max(r * r - x * x, 0.0))) + TORSO_Z


def coat_r(y: float) -> float:
    """The greatcoat skirt's radius (across) at height y."""
    return HEM_R + (TORSO_R0 + 1.2 - HEM_R) * (y - HEM_Y) / (WAIST_Y + 1.0 - HEM_Y)


def coat_front(y: float, kz: float = COAT_KZ, z: float = COAT_Z) -> float:
    """The greatcoat skirt's front surface at height y (x = 0)."""
    return kz * coat_r(y) + z


def gun_axes(aim, aim_up) -> tuple[np.ndarray, np.ndarray]:
    u = unit(aim)
    v = np.asarray(aim_up, float)
    v = unit(v - (v @ u) * u)
    return u, v


def model(cell: Cell, frame: str = "A", pose: Pose | None = None) -> tuple[list[core.Prim], dict]:
    """The General as rig_core primitives in model space, posed. Returns
    (prims, anchors); anchors["muzzle"] is where the salvo leaves. `pose`
    overrides POSES[frame] (the full set)."""
    pose = POSES[frame] if pose is None else pose
    P: list[core.Prim] = []
    anch: dict = {}
    E, RC, CC, BX = core.ellipsoid, core.rcone, core.ccone, core.box

    def add(grp: str, prim: core.Prim) -> core.Prim:
        prim.grp = grp
        P.append(prim)
        return prim

    def label(start: int, limb: str, side: int) -> None:
        for q in P[start:]:
            q.limb, q.side = limb, side

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((core.LEFT, pose.foot_l, "leg_l"), (core.RIGHT, pose.foot_r, "leg_r")):
        start = len(P)
        hip = V(side * HIP_X, HIP_Y + pose.bob, 0.0)
        knee, ankle = core.two_bone(hip, V(*foot), THIGH, SHIN, V(0, 0, 1))
        s = "l" if side == core.LEFT else "r"
        anch[f"hip_{s}"], anch[f"knee_{s}"], anch[f"ankle_{s}"] = (hip, grp), (knee, grp), (ankle, grp)
        add(grp, RC("greatcoat", 0.55, hip, knee, 5.2, 4.3))                                  # breeches (under the coat)
        add(grp, RC("boot_polish", 0.6, knee + V(0, 1.2, 0), ankle + V(0, 1.4, 0), 4.0, 3.2))   # riding boot
        add(grp, RC("boot_polish", 0.6, knee + V(0, 0.4, 0), knee + V(0, 2.4, 0.2), 4.5))      # its top
        add(grp, BX("boot_polish", 0.5, (ankle[0], ankle[1] - 1.6, ankle[2] + 2.4), (2.9, 2.0, 5.6), rnd=1.2))
        label(start, "leg", side)

    # ---------------------------------------------------------------- coat
    ckz, cz = (DEAD_COAT_KZ, DEAD_COAT_Z) if pose.coat_flat else (COAT_KZ, COAT_Z)
    add("coat", CC("greatcoat", 0.62, HEM_Y, WAIST_Y + 1.0, HEM_R, TORSO_R0 + 1.2, kz=ckz, z=cz, tag="coat"))
    add("coat", RC("cap_band", 0.2, V(0, HEM_Y + 0.6, coat_front(HEM_Y + 0.6, ckz, cz) - 0.15),
                   V(0, WAIST_Y - 1.5, coat_front(WAIST_Y - 1.5, ckz, cz) - 0.15), 0.55))   # the coat's opening
    for sx in (-1, 1):                                                                       # two fold lines
        a = V(sx * 8.5, HEM_Y + 1.0, 0)
        b = V(sx * 5.0, WAIST_Y - 6.0, 0)
        for p in (a, b):
            r = coat_r(p[1])
            p[2] = ckz * float(np.sqrt(max(r * r - p[0] * p[0], 0.0))) + cz - 0.3
        add("coat", RC("greatcoat", 0.42, a, b, 0.6, 0.35))
    add("upper", CC("belt", 0.45, WAIST_Y - 1.6, WAIST_Y + 1.6, TORSO_R0 + 1.5, TORSO_R0 + 1.4, kz=0.76,
                    z=TORSO_Z, tag="belt"))
    add("upper", BX("chrome", 0.65, (0, WAIST_Y, (TORSO_R0 + 1.5) * 0.76 + TORSO_Z + 0.3), (2.1, 1.5, 0.45)))

    # ---------------------------------------------------------------- torso
    chest_mat = "chrome" if cell.chest == "cuirass" else "greatcoat"
    add("upper", core.Prim("cappedcone", chest_mat, 0.62, V(0, (WAIST_Y + CHEST_Y) / 2, TORSO_Z),
                           h=(CHEST_Y - WAIST_Y) / 2, r1=TORSO_R0, r2=TORSO_R1, scale=V(1.0, 1.0, TORSO_KZ),
                           tag="torso"))
    if cell.chest == "cuirass":
        for sx in (-1, 1):                                                                   # the muscle cuirass
            add("upper", E("chrome", 0.70, (sx * 5.6, 67.4, torso_z(sx * 5.6, 67.4) - 1.7), (6.0, 4.4, 3.2)))
            for y in (62.4, 58.9):
                add("upper", E("chrome", 0.64, (sx * 2.8, y, torso_z(sx * 2.8, y) - 0.9), (2.9, 1.8, 1.4)))
        add("upper", CC("chrome", 0.58, WAIST_Y + 0.6, WAIST_Y + 3.0, TORSO_R0 + 1.7, TORSO_R0 + 0.5, kz=0.76,
                        z=TORSO_Z))                                                          # its flared lip
        add("upper", CC("chrome", 0.62, 72.0, 75.2, 9.6, 7.4, kz=0.92, z=-0.2))             # gorget
    else:                                                                                    # E: the dress coat
        for y in (70.0, 66.2, 62.4, 58.6):                                                   # double-breasted
            for sx in (-1, 1):
                add("upper", E("braid", 0.72, (sx * 4.4, y, torso_z(sx * 4.4, y) + 0.25), (0.95, 0.95, 0.6)))
        ribbons = ("pennant_red", "ribbon_blue", "braid", "pennant_white", "ribbon_blue", "pennant_red",
                   "braid", "pennant_red", "ribbon_blue")
        for i, mat in enumerate(ribbons):                                                    # his left breast
            x, y = 7.0 + 2.1 * (i % 3), 70.6 - 1.7 * (i // 3)
            add("upper", BX(mat, 0.62, (x, y, torso_z(x, y) + 0.1), (1.0, 0.75, 0.45)))
        for drop in (0.0, 2.6):                                                              # the aiguillette
            pts = [V(-13.2, 72.2, 0), V(-12.0, 65.2 - drop, 0), V(-8.2, 63.0 - drop, 0), V(-4.6, 66.6, 0)]
            for p in pts:
                p[2] = torso_z(p[0], p[1]) + 0.45
            for a, b in zip(pts, pts[1:]):
                add("upper", RC("braid", 0.7, a, b, 0.6))
        add("upper", CC("greatcoat", 0.6, 72.0, 75.0, 9.4, 7.6, kz=0.92, z=-0.2))
    # Sam Browne strap: left hip, across the chest, over the RIGHT shoulder.
    pts = [V(7.6, WAIST_Y + 1.6, 0), V(0.0, 63.5, 0), V(-6.4, 69.0, 0), V(-10.4, 72.6, 0)]
    for p in pts:
        p[2] = torso_z(p[0], p[1]) + 0.5
    for a, b in zip(pts, pts[1:]):
        add("upper", RC("belt", 0.45, a, b, 0.95))

    # --------------------------------------------------------------- collar
    add("head", RC("flesh", 0.62, V(0, 73.5, 0.2), V(0, 80.0, 0.9), 4.3, 3.8))                # pink at the throat
    add("upper", CC("greatcoat", 0.55, 74.4, 79.6, 7.2, 6.5, kz=0.95, z=-0.3,
                    clip=[(V(0, 0, 1), 1.6)]))                                               # standing collar, open
    add("upper", CC("braid", 0.7, 79.0, 79.9, 6.6, 6.55, kz=0.95, z=-0.3, clip=[(V(0, 0, 1), 1.6)]))

    # ---------------------------------------------------------------- head
    add("head", E("flesh", 0.70, HEAD_C, HEAD_R))
    if cell.face == "plate":
        zc, rz, yc, ry = 2.6, 4.0, 84.0, 5.9
        add("head", E("chrome", 0.7, (0, yc, zc), (5.0, ry, rz), clip=[(V(0, 0, -1), -3.2)], tag="plate"))
        ys = 84.4
        zf = zc + rz * float(np.sqrt(1 - ((ys - yc) / ry) ** 2))
        add("head", BX("slot", 0.0, (0, ys, zf - 0.3), (2.5, 0.7, 0.8)))
    else:                                                                                    # B: the face
        add("head", E("flesh", 0.66, (0, 80.8, 2.6), (4.7, 2.7, 3.6)))                       # jaw
        add("head", E("flesh", 0.80, (0, 86.9, 5.0), (4.3, 1.0, 1.3)))                       # brow
        add("head", E("flesh", 0.74, (0, 83.4, 6.1), (0.95, 1.7, 1.1)))                      # nose
        add("head", E("void", 0.3, (0, 80.9, 5.75), (1.8, 0.35, 0.5)))                       # mouth
        for sx in (-1, 1):
            add("head", E("lens", 0.6, (sx * 2.25, 85.1, 5.35), (1.95, 1.55, 0.7)))         # aviators
            add("head", RC("chrome", 0.7, V(sx * 4.0, 85.8, 4.7), V(sx * 5.3, 85.5, 0.2), 0.3))
        add("head", RC("chrome", 0.7, V(-0.7, 86.0, 5.9), V(0.7, 86.0, 5.9), 0.3))
        add("head", RC("belt", 0.4, V(-1.2, 80.9, 5.6), V(-4.2, 79.9, 9.4), 0.4))            # corncob pipe
        add("head", CC("corncob", 0.6, 79.0, 83.4, 1.5, 1.7, x=-4.5, z=9.9))
        add("head", E("void", 0.2, (-4.5, 83.3, 9.9), (1.2, 0.3, 1.2)))

    # ----------------------------------------------------------------- cap
    if not pose.no_cap:
        _cap(add)
    anch["neck"] = (NECK.copy(), "head")
    anch["head_top"] = (V(0.0, HEAD_C[1] + HEAD_R[1], HEAD_C[2]), "head")
    anch["cap_c"] = (V(0.0, 91.0, 0.8), "cap")

    # ------------------------------------------------------------ shoulders
    _shoulders(cell, pose, add, anch)

    # --------------------------------------------------------------- arms
    _arms_and_weapon(cell, pose, add, label, anch, P)

    # ------------------------------------------------------------- posing
    _pose(cell, pose, P, anch)
    even_light(P, GN_MATERIALS)
    return P, anch


def _cap(add) -> None:
    """The peaked cap: band, a crown whose front rises, the eagle, the
    patent-leather peak with its braid, the chin cord."""
    E, RC, CC = core.ellipsoid, core.rcone, core.ccone
    add("cap", CC("cap_band", 0.5, 87.4, 91.0, 6.25, 6.45, kz=0.98, z=0.8))
    crown_pivot = V(0, 91.0, 0.8)
    crown_tilt = core.rot_x(13.0)               # the front of the crown rises: the officer's saddle
    add("cap", tilt(E("cap_crown", 0.66, (0, 92.3, 0.4), (9.0, 2.6, 9.4)), crown_tilt, crown_pivot))
    add("cap", tilt(E("braid", 0.85, (0, 91.6, 9.3), (2.0, 1.5, 0.7)), crown_tilt, crown_pivot))   # eagle badge
    peak_pivot = V(0, 88.2, 4.2)
    peak_tilt = core.rot_x(-20.0)               # the peak dips over the face
    add("cap", tilt(E("peak", 0.5, (0, 88.0, 5.6), (6.0, 0.75, 4.6), clip=[(V(0, 0, -1), -4.2)]),
                    peak_tilt, peak_pivot))
    add("cap", tilt(E("braid", 0.75, (0, 88.55, 5.9), (5.2, 0.5, 3.8), clip=[(V(0, 0, -1), -5.0)]),
                    peak_tilt, peak_pivot))     # scrambled eggs on the peak
    for sx in (-1, 1):                                                                       # chin cord
        add("cap", RC("braid", 0.7, V(sx * 6.1, 89.2, 2.4), V(0, 89.2, 7.3), 0.45))


def _shoulders(cell: Cell, pose: Pose, add, anch: dict) -> None:
    """Pauldrons, epaulettes and their fringe, the pennants, the cloak."""
    E, RC, BX = core.ellipsoid, core.rcone, core.box
    sx_, sy_, sz_ = SHOULDER
    for side in (core.LEFT, core.RIGHT):
        c = V(side * (sx_ + 0.8), sy_ + 0.2, sz_)
        if cell.chest == "cuirass":
            add("upper", E("chrome", 0.66, tuple(c), (6.2, 4.6, 6.0), clip=[(V(0, -1, 0), -(sy_ - 3.0))]))
        add("upper", BX("braid", 0.62, (c[0], sy_ + 2.6, sz_), (5.2, 1.0, 4.0), rnd=0.6,
                        rot=core.rot_z(side * 8.0)))                                         # epaulette
        for z in np.linspace(-3.2, 3.2, 5):                                                  # its fringe
            top = V(side * (sx_ + 5.4), sy_ + 1.7, sz_ + z)
            add("upper", RC("braid", 0.66, top, top + V(side * 0.6, -3.6, 0), 0.7, 0.55))
    if cell.flags in ("pennants", "both"):
        for side, grp, tag, mat in ((core.LEFT, "pen_l", "pen_reich", "pennant_red"),
                                    (core.RIGHT, "pen_r", "pen_us", "pennant_white")):
            R = core.rot_y(-side * PENNANT_TILT)
            centre = V(side * 17.8, 63.6, 5.6)
            add(grp, BX(mat, 0.6, tuple(centre), (4.4, 7.4, 0.35), rot=R, tag=tag))
            add(grp, BX("braid", 0.6, tuple(centre + V(0, -7.9, 0)), (4.5, 0.7, 0.5), rot=R))      # gold fringe
            add(grp, RC("braid", 0.7, centre + R @ V(-4.8, 7.6, 0), centre + R @ V(4.8, 7.6, 0), 0.6))  # its bar
            add(grp, RC("braid", 0.66, centre + R @ V(0, 7.6, 0), V(side * 17.0, sy_ + 1.8, sz_ + 3.0), 0.4))
            anch[f"hinge_{grp}"] = (centre + V(0, 7.6, 0), grp)
    if cell.flags in ("cloak", "both"):                                                      # D, CD: the cloak
        if pose.spread:
            _spread_cloak(add)
        else:
            _cloak(add, fit=cell.flags == "both")


def _arms_and_weapon(cell: Cell, pose: Pose, add, label, anch: dict, P: list) -> None:
    """The arms by two-bone IK to the pose's wrists, the gloves, the weapon."""
    E, RC, BX = core.ellipsoid, core.rcone, core.box
    sx_, sy_, sz_ = SHOULDER
    u, v = gun_axes(pose.aim, pose.aim_up)
    grips = {core.LEFT: V(*pose.hand_l), core.RIGHT: V(*pose.hand_r)}
    poles = {core.LEFT: V(*pose.pole_l) if pose.pole_l else V(1.0, -0.2, -0.3),
             core.RIGHT: V(*pose.pole_r) if pose.pole_r else
             (V(-0.6, -1.0, 0.0) if pose.fire else V(-0.4, 0.0, -1.0))}
    for side in (core.LEFT, core.RIGHT):
        start = len(P)
        sh = V(side * sx_, sy_, sz_)
        elbow, wrist = core.two_bone(sh, grips[side], UPPER_ARM, FOREARM, poles[side])
        fd = unit(wrist - elbow)
        s = "l" if side == core.LEFT else "r"
        anch[f"shoulder_{s}"], anch[f"elbow_{s}"], anch[f"wrist_{s}"] = (sh, "arm"), (elbow, "arm"), (wrist, "arm")
        add("arm", RC("greatcoat", 0.62, sh, elbow, 4.6, 4.0))
        add("arm", RC("greatcoat", 0.58, elbow, wrist, 4.0, 3.5))
        add("arm", RC("braid", 0.62, wrist - fd * 2.4, wrist - fd * 1.6, 3.75))              # braided cuff
        hand = wrist + fd * 2.3
        add("arm", E("glove", 0.66, tuple(hand), (2.8, 3.2, 2.8)))
        anch[f"hand_{s}"] = (hand, "arm")
        label(start, "arm", side)

    hand = anch["hand_r"][0]
    at = lambda s, hh=0.0: hand + u * s + v * hh  # noqa: E731
    if cell.weapon == "revolver":       # a long-barrelled chrome service revolver, ivory grips
        add("gun", RC("ivory", 0.62, at(-1.8, -2.6), at(0.3, 1.2), 1.55, 1.35))
        add("gun", RC("chrome", 0.62, at(0.0, 2.3), at(3.8, 2.7), 1.6))
        add("gun", RC("chrome", 0.66, at(1.7, 2.9), at(5.7, 2.9), 2.1))                      # cylinder
        add("gun", RC("chrome", 0.66, at(5.4, 3.4), at(17.0, 3.4), 0.95, 0.9))               # barrel
        add("gun", RC("gunmetal", 0.4, at(5.6, 2.2), at(14.0, 2.2), 0.5))                    # ejector rod
        add("gun", RC("gunmetal", 0.5, at(0.2, 3.5), at(-1.3, 4.7), 0.6))                    # hammer
        anch["muzzle"] = (at(17.6, 3.4), "gun")
    else:                               # C: the swagger stick in the hand, the field gun on the shoulder
        add("gun", RC("belt", 0.5, at(-4.0), at(9.5), 0.6))
        for s_ in (-4.0, 9.5):
            add("gun", E("chrome", 0.7, tuple(at(s_)), (0.95, 0.95, 0.95)))
        anch["stick_tip"] = (at(9.5), "gun")
        if not pose.no_sgun:
            start = len(P)
            _field_gun(add, anch)
            if pose.sgun_knock:             # knocked up on its cradle, about the cradle's back
                core.transform(P[start:], anch, {"sgun"}, core.rot_x(-pose.sgun_knock) @ core.rot_z(8.0),
                               SGUN_CRADLE)
        else:
            anch["muzzle"] = (anch["shoulder_r"][0].copy(), "upper")


SGUN_CRADLE = V(-(SHOULDER[0] + 0.8), SHOULDER[1] + 4.8, -5.0)


def _field_gun(add, anch: dict) -> None:
    """C's field gun on his right shoulder: cradle, breech, barrel, sleeve, brake."""
    E, RC, BX = core.ellipsoid, core.rcone, core.box
    sx_, sy_, _ = SHOULDER
    gx, gy = -(sx_ + 0.8), sy_ + 7.4
    add("sgun", BX("gunmetal", 0.5, (gx, sy_ + 4.8, -1.0), (2.8, 1.8, 4.2), rnd=0.6, tag="sgun"))  # cradle
    add("sgun", E("chrome", 0.6, (gx, gy, -10.6), (3.8, 3.8, 4.4)))                                # breech
    add("sgun", RC("chrome", 0.66, V(gx, gy, -10.0), V(gx, gy + 0.6, 21.0), 2.6, 2.2))             # barrel
    add("sgun", RC("gunmetal", 0.45, V(gx, gy + 0.1, -2.0), V(gx, gy + 0.25, 6.0), 3.1))           # recoil sleeve
    add("sgun", RC("gunmetal", 0.5, V(gx, gy + 0.55, 19.6), V(gx, gy + 0.6, 22.6), 3.0))           # muzzle brake
    add("sgun", E("slot", 0.0, (gx, gy + 0.6, 25.4), (1.3, 1.3, 0.5)))                              # the bore, end on
    anch["muzzle"] = (V(gx, gy + 0.6, 26.4), "sgun")    # past the brake's rounded end, or the flash hides


def _pose(cell: Cell, pose: Pose, P: list, anch: dict) -> None:
    """The pose's rigid moves, in order: the pennants out of the arms' way,
    the coat's hem and the cloak swaying, the head, the twist, the lean, the bob."""
    for grp, ang in (("pen_r", pose.swing_r), ("pen_l", -pose.swing_l)):
        if ang and f"hinge_{grp}" in anch:
            core.transform(P, anch, {grp}, core.rot_z(ang), anch[f"hinge_{grp}"][0])   # swings out, away from him
    if pose.hem_tilt or pose.hem_roll:
        R = core.rot_z(pose.hem_roll) @ core.rot_x(pose.hem_tilt)
        core.transform(P, anch, {"coat"}, R, WAIST)
    if pose.cloak_swing or pose.hem_roll:
        R = core.rot_z(pose.hem_roll) @ core.rot_x(-pose.cloak_swing)
        core.transform(P, anch, {"cape_lo"}, R, WAIST)       # it follows the hem sideways, trails behind
    if pose.head_turn:
        core.transform(P, anch, {"head", "cap"}, core.rot_y(pose.head_turn), NECK)
    if pose.head_pitch:
        core.transform(P, anch, {"head", "cap"}, core.rot_x(pose.head_pitch), NECK)
    if pose.twist:
        # CD's fitted cloak hangs from his back and does not turn with the
        # chest: it hangs ~16 units behind the axis, so the 8 degrees that
        # bring his right shoulder forward would swing its edge ~2 units out
        # past the coat's (seen at F1 before this). D's full cloak turns, as drawn in the sweep.
        twisted = UPPER - CLOAKS if cell.flags == "both" else UPPER
        core.transform(P, anch, twisted, core.rot_y(pose.twist), WAIST)
    if pose.lean:
        core.transform(P, anch, LEAN - (CLOAKS if cell.flags == "both" else set()) | {"cape"},
                       core.rot_x(pose.lean), WAIST + V(0, pose.bob, 0))
    if pose.bob:
        core.transform(P, anch, UPPER, np.eye(3), V(0, 0, 0), V(0, pose.bob, 0))


def _plane_x_le(slope: float, x0: float, y0: float, side: int) -> tuple[np.ndarray, float]:
    """The half-space side * x <= x0 + slope * (y - y0), as a unit clip plane."""
    n = V(side, -slope, 0.0)
    k = float(np.linalg.norm(n))
    return n / k, (x0 - slope * y0) / k


def fitted_segments() -> list[list]:
    """CD's cloak (D71), as clip sets: a lower segment trimmed to the coat's
    width less CD_TRIM, an upper one to the cuirass's, both inside the body's
    front silhouette. The camera looks down 9 degrees, so a point at the
    cloak's back (z ~ -19) shows ~3 px higher than the same height at the
    coat's edge: the trims narrow upwards on the coat (it tapers) and the
    margin covers the rest. Its bottom stays above the coat's hem and its
    top under the pauldrons, so neither edge shows above or below him."""
    coat_slope = (TORSO_R0 + 1.2 - HEM_R) / (WAIST_Y + 1.0 - HEM_Y)
    torso_slope = (TORSO_R1 - TORSO_R0) / (CHEST_Y - WAIST_Y)
    lower = [(V(0, -1, 0), -CD_CAPE_Y0), (V(0, 1, 0), CD_CAPE_WAIST)]
    upper = [(V(0, -1, 0), -CD_CAPE_WAIST), (V(0, 1, 0), CD_CAPE_Y1)]
    for side in (1, -1):
        lower.append(_plane_x_le(coat_slope, HEM_R - CD_TRIM, HEM_Y, side))
        upper.append(_plane_x_le(torso_slope, TORSO_R0 - CD_TRIM, WAIST_Y, side))
    return [lower, upper]


def _cloak(add, fit: bool = False) -> None:
    """D: both flags as one cloak hung from the epaulettes to the boots: the
    Reich's red with the white disc on his LEFT half, the Legion's stars and
    stripes on his RIGHT, hung vertically (stripes running down the back,
    the canton at the top by the spine). A half cone behind him.
    fit (CD, D71): the same cloth, trimmed by fitted_segments() so it hangs
    inside his front silhouette: two primitives per piece instead of one."""
    back = [(V(0, 0, 1), CAPE_BACK)]                   # keep z <= CAPE_BACK: the half behind him
    segments = fitted_segments() if fit else [[]]

    def cone(mat, clips, tag=""):
        for i, seg in enumerate(segments):
            add("cape_lo" if fit and i == 0 else "cape",
                core.ccone(mat, 0.6, CAPE_Y0, CAPE_Y1, CAPE_R0, CAPE_R1, kz=CD_CAPE_KZ if fit else CAPE_KZ,
                                   z=CAPE_Z,
                                   clip=back + clips + seg, tag=tag))

    cone("pennant_red", [(V(-1, 0, 0), 0.0)], tag="cape_reich")          # x >= 0: his left half
    # His right half, sliced into stripes by planes through the cone's axis:
    # phi = 0 at the spine, 90 at his right side.
    c = V(0, 0, CAPE_Z)
    phis = np.linspace(0.0, 90.0, US_STRIPES + 1)
    y_canton = CAPE_Y1 - CANTON_DROP

    def wedge(a: float, b: float) -> list:
        ra, rb = np.deg2rad(a), np.deg2rad(b)
        n_a = V(np.cos(ra), 0, -np.sin(ra))          # keep phi >= a
        n_b = V(-np.cos(rb), 0, np.sin(rb))          # keep phi <= b
        out = []
        if a > 0:
            out.append((n_a, float(n_a @ c)))
        else:
            out.append((V(1, 0, 0), 0.0))            # x <= 0
        if b < 90:
            out.append((n_b, float(n_b @ c)))
        return out

    below = [(V(0, 1, 0), y_canton)]                 # y <= y_canton
    above = [(V(0, -1, 0), -y_canton)]               # y >= y_canton
    cone("us_blue", wedge(phis[0], phis[CANTON_STRIPES]) + above, tag="canton")
    for i in range(US_STRIPES):
        mat = "pennant_red" if i % 2 == 0 else "pennant_white"
        clips = wedge(phis[i], phis[i + 1])
        cone(mat, clips + below if i < CANTON_STRIPES else clips)


def insignia_for(cell: Cell) -> tuple[core.Insignia, ...]:
    return {"pennants": PENNANT_INSIGNIA, "cloak": CLOAK_INSIGNIA,
            "both": PENNANT_INSIGNIA + CLOAK_INSIGNIA}[cell.flags]


def render(key: str, frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    cell = CELL[key]
    prims, anch = model(cell, frame)
    pose = POSES[frame]
    return core.render(prims, rotation, CV, GN_MATERIALS, seed=seed, value_shift=VALUE_SHIFT,
                       insignia=insignia_for(cell), muzzle=anch["muzzle"][0] if pose.fire else None,
                       flash_size=FLASH_SIZE, chrome=CHROME, what=f"{SPRITE} {key} {frame}{rotation}")


def grab() -> tuple[int, int]:
    return core.grab_offsets(CV)


# ================================================================ scenes
# Where MAP03 puts him (docs/levels/MAP03-factory.md §9, §15): the portal
# hall, brick SDBRCK1 at light 128 over the SDFLR4 casting-floor plates; he
# comes round the drum (SDSTEL1 outside, light 144); on the dais the
# portal's cobalt field SDPORT1 is behind him.
SCENES = (
    ("P1", "SDBRCK1", 128, "portal hall, the brick (his arena)"),
    ("P2", "SDSTEL1", 144, "round the drum, its steel ring"),
    ("P3", "SDPORT1", 144, "on the dais, the portal behind him"),
)
FLOOR = "SDFLR4"
LINEUP_WALL_H = 128             # a wall taller than he is
LINEUP_SLOT = 76
SEP_LIT = heavy.SEP_LIT


def asset_rgb(lump: str) -> np.ndarray:
    """A wall or flat from assets/ by lump name, any set (read only)."""
    for folder in ("textures", "flats"):
        for path in sorted((ASSETS / folder).glob(f"*/{lump}.png")):
            with Image.open(path) as im:
                return np.asarray(im.convert("RGB"), dtype=np.uint8)
    raise FileNotFoundError(lump)


def lineup(figures: list[tuple[np.ndarray, int, int]], wall: str, light: int) -> np.ndarray:
    """heavy.tall_lineup's composition with MAP03's walls: each sprite by its
    own offsets on a factory wall over SDFLR4 (foreshortened 3:1), the light
    stand-in, re-quantised to palette v2."""
    width = LINEUP_SLOT * len(figures)
    w_rgb = flat.tile_to(asset_rgb(wall), width, LINEUP_WALL_H)
    fl = flat.tile_to(asset_rgb(FLOOR), width, flat.FLOOR_H * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, flat.FLOOR_H), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = LINEUP_WALL_H + (flat.FLOOR_LINE - flat.WALL_H) - core.FEET_SINK
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = base - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return core.lit(canvas, light, heavy.palette_v2())


REFERENCES = (
    ("SDRRA1", "rifleman", "Reich rifleman (approved)"),
    ("SDLTA1", "legion", "Legion trooper (approved)"),
    ("SDPMA1", "panzermensch", "Panzermensch (approved, D67)"),
    ("SDPSA1", "panzermensch", "Schwer (approved, D67)"),
)
PLACEHOLDER = "CYBRA1"


def references() -> tuple[list, list[str]]:
    """The approved figures he must read apart from, and today's Freedoom placeholder."""
    figs, labels = [], []
    for name, folder, label in REFERENCES:
        r = heavy.approved(name, folder)
        if r:
            figs.append(r)
            labels.append(f"{name} {label}")
    fd = core.freedoom_sprite(PLACEHOLDER)
    if fd:
        figs.append(fd)
        labels.append(f"{PLACEHOLDER} Freedoom, today's placeholder")
    return figs, labels


def measure(rgba: np.ndarray) -> dict:
    """heavy.measure against MAP03's walls: size, value, and per scene the
    mean gap and the share of pixels that separate from the wall."""
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    lum = flat.luma(rgba[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "body_luma": round(float(lum.mean()), 1), "mass_luma": round(float(np.median(lum)), 1)}
    for key, wall, light, _ in SCENES:
        f = min(1.0, light / flat.LIGHT_FULL)
        w = float(flat.luma(asset_rgb(wall)).mean())
        out[f"gap_{key}"] = round(abs(float(lum.mean()) - w) * f, 1)
        out[f"sep_{key}"] = round(float((np.abs(lum - w) * f >= SEP_LIT).mean()), 2)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in SCENES)
    out["worst_sep"] = min(out[f"sep_{k}"] for k, *_ in SCENES)
    return out


def ramp_share(rgba: np.ndarray, ramp_names: set[str]) -> float:
    return heavy.ramp_share(rgba, ramp_names)


# ================================================================ output
def lump(key: str, frame: str, rot: int) -> str:
    """Draft file name: SDGN_<cell>_<frame><rot> (the lump would be SDGN<frame><rot>)."""
    return f"{SPRITE}_{key}_{frame}{rot}"


def build_all(out_dir: Path = OUT_DIR, seed: int = SEED, keys: str | None = None) -> dict:
    out: dict = {"sprites": {}, "metrics": {}}
    for c in CELLS:
        if keys and c.key not in keys:
            continue
        for frame, rot in VIEWS:
            rgba = render(c.key, frame, rot, seed)
            heavy.save(rgba, out_dir / f"{lump(c.key, frame, rot)}.png", grab())
            out["sprites"][(c.key, frame, rot)] = rgba
            print(lump(c.key, frame, rot), flush=True)
        out["metrics"][c.key] = measure(out["sprites"][(c.key, "A", 1)])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(out["metrics"], indent=2) + "\n", encoding="utf-8")
    return out


def figure(rgba: np.ndarray) -> tuple[np.ndarray, int, int]:
    return (rgba, *grab())


def write_lineups(data: dict, out_dir: Path = OUT_DIR) -> dict:
    figs = [figure(data["sprites"][(c.key, "A", 1)]) for c in CELLS]
    labels = [f"{SPRITE} {c.key}" for c in CELLS]
    rf, rl = references()
    figs += rf
    labels += rl
    res = {"labels": labels}
    for key, wall, light, _ in SCENES:
        sc = lineup(figs, wall, light)
        Image.fromarray(sc, "RGB").save(out_dir / f"lineup_{key}.png", optimize=True)
        res[key] = sc
    return res


# ======================================================== contact sheet PNG
# Hard-pixel capitals for the contact sheet's row labels (5 x 7): drawn
# from this table, not rasterised from a font (NO FONTS).
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
}
CONTACT_BG = (38, 39, 43)
CONTACT_INK = (232, 230, 224)
CONTACT_REC = artlib.ramp("hazard_yellow")[12]
CONTACT_ZOOM = 2
GLYPH_ZOOM = 4


def _paste(canvas: np.ndarray, img: np.ndarray, x: int, y: int, zoom: int) -> None:
    big = np.repeat(np.repeat(img, zoom, axis=0), zoom, axis=1)
    h, w = big.shape[:2]
    if big.shape[-1] == 4:
        a = big[..., 3] > 0
        region = canvas[y:y + h, x:x + w]
        region[a] = big[..., :3][a]
    else:
        canvas[y:y + h, x:x + w] = big


def _glyph(canvas: np.ndarray, ch: str, x: int, y: int, colour) -> None:
    for j, row in enumerate(GLYPHS[ch]):
        for i, c in enumerate(row):
            if c == "#":
                canvas[y + j * GLYPH_ZOOM:y + (j + 1) * GLYPH_ZOOM, x + i * GLYPH_ZOOM:x + (i + 1) * GLYPH_ZOOM] = colour


def contact_sheet(data: dict, lines: dict) -> np.ndarray:
    """One row per cell (its letter, then A1 A3 A5 F1 at 2x on the neutral
    grey), the recommended cell's letter in braid yellow; under them the
    P1 lineup at 2x (the cells, then the approved figures and CYBRA1)."""
    z, gap, lab = CONTACT_ZOOM, 12, 7 * GLYPH_ZOOM + 16
    row_h = CV.h * z + gap
    lw = lines["P1"].shape[1] * z
    width = max(lab + len(VIEWS) * (CV.w * z + gap), lw) + 2 * gap
    height = gap + row_h * len(CELLS) + lines["P1"].shape[0] * z + 2 * gap
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = CONTACT_BG
    for i, c in enumerate(CELLS):
        y = gap + i * row_h
        _glyph(canvas, c.key, gap, y + (CV.h * z - 7 * GLYPH_ZOOM) // 2,
               CONTACT_REC if c.key == RECOMMENDED else CONTACT_INK)
        for j, (f, r) in enumerate(VIEWS):
            x = gap + lab + j * (CV.w * z + gap)
            canvas[y:y + CV.h * z, x:x + CV.w * z] = core.NEUTRAL
            _paste(canvas, data["sprites"][(c.key, f, r)], x, y, z)
    _paste(canvas, lines["P1"], gap, gap + row_h * len(CELLS) + gap, z)
    return canvas


# ==================================================================== sheet
RECOMMENDED = "C"
# Written after looking at the renders (PIPELINE stage 2); see the sheet.
VERDICT = [
    "RECOMMENDED: C, the gun on the shoulder. BESTIARY 9 and D35 say he orders, he does not brawl; C draws "
    "that sentence. His hand only points a swagger stick (the 'Vorwärts!' of his summon, D36), and the "
    "salvo comes from a field gun riding his right shoulder, so the attack frame reads as a command "
    "carried out, not as a big man firing a big pistol. It also gives him the one asymmetric shape in the "
    "bestiary: in profile (rotation 3) a long barrel over the shoulder, which nothing else carries, and "
    "at 16 px a notch on one shoulder that the Panzermensch's two horns never make.",
    "A is the brief taken literally and already works: the hourglass the brief promises (cap wedge, narrow "
    "waist, coat flare), chrome on the chest and the face, the two pennants carrying the two insignia. "
    "B gives him a face (aviators and a corncob pipe: the Yankee general as the 1950s drew him); the most "
    "characterful at 3x, but at 1x it reads as a pink face, i.e. as a big trooper, and the chrome plate "
    "is what says 'not a man'. D wears the two flags as one cloak: the strongest back view (rotation 5 is "
    "the whole alliance in one picture) but from the front the cloak is two red-striped edges and the "
    "hourglass becomes a trapezoid. E, in dress uniform, is the most 'officer', but without the cuirass "
    "his chest is the coat's pale plaster and he loses the Legion's chrome: he reads as a statue.",
    "Valid combinations, one parameter each: C with B's face; C with D's cloak (the gun is on the shoulder, "
    "the cloak hangs behind it); A or C with E's medals over the cuirass.",
]
HONEST = [
    "(1) At 1x his flags are 7 px wide: the swastika is the armband's 5x5 drawing and the US flag the "
    "trooper's 7x5 patch, both hard-stamped; they read as 'a red flag and a striped flag', which is what "
    "the brief asks, not as detailed emblems. (2) The cap's braid and the epaulettes' fringe are a yellow "
    "line and a yellow edge at 1x; 'too much braid' reads at 3x only. (3) Rotation 1 of the firing frame "
    "points the revolver at the camera, so the gun is a short chrome blob under a flash (Doom's own "
    "convention: the Cyberdemon's arm reads the same way); C's gun is on the shoulder and its flash sits "
    "beside the head. (4) The coat is a rigid cone: in the walk frames the boots must swing under a hem "
    "that does not move; the full set will need a coat that sways (the hem tilted per frame), not drawn "
    "here. (5) He is HANDED (a different flag on each shoulder, the gun on one side), so his set costs "
    "eight drawn rotations per frame, not the five of Doom's mirroring that BESTIARY 9's 54 assumed: nine "
    "rotated frames (walk A-D, salvo E-F, pain G, summon Q-R) x 8 = 72, plus nine death frames, 81 images "
    "and the shell's 5. (6) Light is gen_enemy's stand-in (RGB x L/224), NOT VERIFIED "
    "against GZDoom; nothing here has been in the engine.",
]
CEO_ASK = [
    "Choose the General: C (recommended), A, B, D or E, or a combination named above (e.g. 'C with B's face').",
    "Then the full set is rendered on the rig (walk A-D, salvo E-F, pain G, death H-P, the summon Q-R at "
    "eight rotations; the shell SDGL A-E), for your gate in GZDoom.",
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


def _cards(data: dict) -> str:
    out = []
    for c in CELLS:
        m = data["metrics"][c.key]
        sp = data["sprites"]
        big = [_tile(sp[(c.key, f, r)], 3, f"{SPRITE}{f}{r}", ROT_NAMES[r] if f == "A" else "fires, the salvo")
               for f, r in VIEWS]
        one = [_tile(sp[(c.key, f, r)], 1, f"{f}{r} 1x") for f, r in VIEWS]
        sils = [_img_tile(heavy.silhouette_rgb(sp[(c.key, "A", 1)]), 4, "16 px, front", "shown 4x"),
                _img_tile(heavy.silhouette_rgb(sp[(c.key, "A", 3)]), 4, "16 px, side", "shown 4x"),
                _img_tile(heavy.silhouette_rgb(sp[(c.key, "A", 1)]), 1, "16 px 1x")]
        facts = (f'{m["height_px"]} x {m["width_px"]} px · body luma {m["body_luma"]:.0f} '
                 f'(median {m["mass_luma"]:.0f}) · '
                 + " ".join(f"sep {k[4:]} {v:.0%}" for k, v in m.items() if k.startswith("sep_")))
        rec = c.key == RECOMMENDED
        out.append(f'<div class="card{" rec" if rec else ""}">'
                   + ('<span class="tag">recommended</span>' if rec else "")
                   + f"<h3>{c.key} · {html.escape(c.title)}</h3><p class=\"num\">{html.escape(facts)}</p>"
                   + _strip(big) + _strip(one + sils) + "</div>")
    return '<div class="cards">' + "".join(out) + "</div>"


def _lineup_body(lines: dict) -> str:
    body = ""
    for key, wall, light, what in SCENES:
        sc = lines[key]
        body += _strip([_img_tile(sc, 1, f"{key} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{key} 2x, for the eye")])
    farv = flat.far(lines["P1"])
    val = np.repeat(flat.luma(farv)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
    body += _strip([_img_tile(farv, 5, "game distance /4", "P1, the brick"),
                    _img_tile(val, 5, "the same, value only")])
    body += ('<p class="lead">Left to right: ' + html.escape(" · ".join(lines["labels"]))
             + ". Each sprite stands by its own offsets, as the engine places it.</p>")
    return body


def build_sheet(data: dict, lines: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    S = []
    rows = [[c.key + (" (rec.)" if c.key == RECOMMENDED else ""), c.face, c.weapon, c.flags, c.chest]
            for c in CELLS]
    S.append(("1 · One decision, five cells", "A is the brief; every other cell changes one thing from A.",
              sheetlib.table(["cell", "face", "weapon (the salvo)", "flags (D12)", "chest"], rows, 99)))
    S.append(("2 · The cells at 3x, then 1x and the 16-px silhouette",
              "BESTIARY §9: tall and unhurried, a chromed cuirass over a pale greatcoat that flares at the knee, a "
              "peaked cap with too much braid, a smooth chrome face plate with a single slot, a swastika pennant "
              "on his left shoulder and the stars and stripes on his right (D12; he is the only actor that wears "
              "both). Rotation 1 (front), 3 (his left side), 5 (his back) and F1, the frame that fires "
              "(general.zs: CYBR F, A_SD_GeneralShot). Legion palette: steel_blue chrome, plaster_warm coat, "
              "flesh_pink (v2) at the throat, hazard_yellow braid; sep = share of his pixels that separate from "
              "that MAP03 wall under its light.",
              _cards(data)))
    S.append(("3 · At 1x in the portal hall, beside the approved enemies and the placeholder",
              "MAP03's portal hall: SDBRCK1 at light 128 over SDFLR4, the drum's steel SDSTEL1 at 144, the "
              "portal's SDPORT1 at 144. The five cells, then the approved rifleman (56), Legion trooper, "
              "Panzermensch and Schwer from assets/, then Freedoom's CYBRA1, today's placeholder. Light is "
              "gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.",
              _lineup_body(lines)))
    sils = [_img_tile(heavy.silhouette_rgb(data["sprites"][(c.key, "A", 1)]), 5, f"SDGN {c.key}") for c in CELLS]
    for name, folder, _ in REFERENCES:
        r = heavy.approved(name, folder)
        if r:
            sils.append(_img_tile(heavy.silhouette_rgb(r[0]), 5, name, "approved"))
    fd = core.freedoom_sprite(PLACEHOLDER)
    if fd:
        sils.append(_img_tile(heavy.silhouette_rgb(fd[0]), 5, PLACEHOLDER, "placeholder"))
    S.append(("4 · Every cell at 16 px (ART-BIBLE §6.4), beside the approved enemies",
              "Black shape, 16 px tall, shown 5x, front views. BESTIARY §9 asks for an hourglass, unlike every "
              "other enemy's rectangle; the Panzermensch is the one he must not resemble.", _strip(sils)))
    body = '<div class="verdict">'
    for title, paras in (("The cells", VERDICT), ("What does not work, honestly", HONEST)):
        body += f"<h3>{html.escape(title)}</h3>" + "".join(f"<p>{html.escape(p)}</p>" for p in paras)
    body += "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in CEO_ASK) \
            + "</ol></div>"
    S.append((f"5 · Recommendation: {RECOMMENDED}", "", body))

    intro = ("Backlog N12: the General (<code>SD_General</code>, BESTIARY §9), MAP03's boss and the last enemy "
             "still on Freedoom (CYBR), drawn on the 3D rig the approved enemies were drawn on. One decision "
             "before ~80 images: what he looks like. Five cells, rotations 1, 3, 5 and the firing frame, each "
             "at 1x in the portal hall beside the approved rifleman, trooper, Panzermensch and Schwer, and its "
             "16-px silhouette. Built by <code>tools/art/gen_general.py</code> on "
             "<code>tools/art/rig_core.py</code> (imported, not edited), palette v2 (flesh_pink), seed "
             f"{SEED}, no system fonts. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_general.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Approved sprites read from assets/sprites/ (rifleman, legion, panzermensch). "
              "Freedoom's CYBRA1 shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause (© the Freedoom "
              "contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_general-sweep.html"
    sheetlib.write_sheet(path, lang="en", title="The General — design sweep (F5, N12)",
                         subtitle="SDGN · 5 cells on the rig · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    Image.fromarray(contact_sheet(data, lines), "RGB").save(path.with_suffix(".png"), optimize=True)
    return path


# ======================================================= the turnaround (D71)
# The CEO's choice: "la C de frente (para que se vean las banderas) y la D
# de espaldas (con esa capa)" ("C from the front, so the flags show, and D
# from the back, with that cloak"). Before the full set (~81 images), one cell,
# CD, turned all the way round: the walk/idle frame A at the eight rotations
# and the firing frame F at 1, 3 and 5, then at 1x in the portal hall. Its
# front is checked against C's, pixel for pixel, and the cloak's visible
# pixels are counted per view from the renderer's primitive ids.
TURN_IDLE = tuple(("A", r) for r in range(1, core.ROTATIONS + 1))
TURN_FIRE = (("F", 1), ("F", 3), ("F", 5))
TURN_VIEWS = TURN_IDLE + TURN_FIRE
TURN_DIR = OUT_DIR / "turnaround"
ROT_LONG = {1: "front", 2: "front, his left", 3: "his left side", 4: "back, his left", 5: "back",
            6: "back, his right", 7: "his right side", 8: "front, his right"}


def render_cd(frame: str, rotation: int, seed: int = SEED) -> tuple[np.ndarray, int]:
    """CD at one view: (RGBA, cloak pixels visible)."""
    prims, anch = model(CD, frame)
    pose = POSES[frame]
    lay = core.render_layers(prims, rotation, CV, GN_MATERIALS, seed=seed, value_shift=VALUE_SHIFT,
                             insignia=insignia_for(CD), muzzle=anch["muzzle"][0] if pose.fire else None,
                             flash_size=FLASH_SIZE, chrome=CHROME, what=f"{SPRITE} CD {frame}{rotation}")
    cape = [i for i, q in enumerate(prims) if q.grp in CLOAKS]
    return lay.rgba, int(np.isin(lay.pid, cape).sum())


def silhouette_width(rgba: np.ndarray) -> int:
    xs = np.nonzero((rgba[..., 3] > 0).any(axis=0))[0]
    return int(xs.max() - xs.min() + 1)


def build_turnaround(out_dir: Path = TURN_DIR, seed: int = SEED) -> dict:
    out: dict = {"cd": {}, "cape_px": {}, "c": {}}
    for frame, rot in TURN_VIEWS:
        rgba, n = render_cd(frame, rot, seed)
        heavy.save(rgba, out_dir / f"{lump('CD', frame, rot)}.png", grab())
        out["cd"][(frame, rot)] = rgba
        out["cape_px"][f"{frame}{rot}"] = n
        print(lump("CD", frame, rot), "cloak px", n, flush=True)
    for frame, rot in (("A", 1), ("F", 1)):                 # what the front must equal
        out["c"][(frame, rot)] = render("C", frame, rot, seed)
    m = measure(out["cd"][("A", 1)])
    for frame, rot in (("A", 1), ("F", 1)):
        a, b = out["cd"][(frame, rot)], out["c"][(frame, rot)]
        m[f"front_{frame}{rot}_px_unlike_C"] = int((a != b).any(axis=-1).sum())
        m[f"front_{frame}{rot}_width"] = silhouette_width(a)
        m[f"front_{frame}{rot}_width_C"] = silhouette_width(b)
    m["back_worst_sep"] = measure(out["cd"][("A", 5)])["worst_sep"]
    m["cape_px"] = out["cape_px"]
    out["metrics"] = m
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    figs = [figure(out["cd"][("A", 1)]), figure(out["cd"][("A", 5)])]
    labels = ["SDGN CD front", "SDGN CD back"]
    rf, rl = references()
    out["lines"] = {"labels": labels + rl}
    for key, wall, light, _ in SCENES:
        sc = lineup(figs + rf, wall, light)
        Image.fromarray(sc, "RGB").save(out_dir / f"lineup_{key}.png", optimize=True)
        out["lines"][key] = sc
    return out


TURN_NOTES = [
    "WHAT KEEPS THE CLOAK OUT OF THE FRONT. It is D's cloth (the same half cone, the Reich's red and the white "
    "disc on his left half, the stars and stripes hung vertically on his right) cut in two and trimmed: below "
    "the waist to the coat's width less 1.2 units, above it to the cuirass's, so from the front it is always "
    "inside his own outline. Its bottom stops 1.5 units above the coat's hem (the hem hides it; the camera "
    "looks down 9 degrees, so the back of the cloak shows a little HIGHER than the coat's edge, never lower), "
    "and its top at 71, under the pauldrons, so it never peeks over the shoulders. It is flatter than D's "
    "(depth 0.72 of its width against 0.85): it stands about one unit off the coat's back at the hem, which "
    "keeps rotations 2 and 8 to a sliver. The pennants hang in front of the shoulders and the cloak behind "
    "the back: they never meet.",
    "MEASURED (section 3; tests/test_gen_general.py holds it). At rotation 1, standing and firing, not one "
    "pixel of the cloak shows; the silhouette is C's, the same width, the hourglass untouched. The sprite "
    "differs from C's in 4 pixels (9 when firing), all shading: the hidden cloak, close behind the coat's "
    "edge, darkens the renderer's ambient occlusion there by one ramp step. "
    "Rotations 2 and 8 show its edge as a 2-3 px strip behind the coat's back edge, about 100 px of "
    "cloth: what a cloak seen three-quarters from the front shows; the silhouette stays the hourglass. "
    "From 3 to 7 it is D's cloak: the whole alliance across his back at 5.",
    "SWAY (a note, not drawn). In the full set the coat's hem and the cloak should swing with the walk: the "
    "hem tilted a few degrees against the leading leg in each of A-D, the cloak's lower segment hinged at the "
    "waist and lagging one frame behind the hem; in the death frames the cloak falls with him and spreads "
    "on the floor (the corpse flat, as D55). Both are pose parameters on the rig, no new method.",
    "HONEST. (1) The trim makes the cloak narrower than D's: from the back he is the cloak plus a band of "
    "chrome back-plate and the pennants above and beside it, where D's covered him shoulder to shoulder. "
    "(2) The canton's stars are a 1-px checker at 1x. (3) In profile (3, 7) the cloak's trimmed side is a "
    "flat face of stripes or red, a panel behind the coat. (4) From the back the red half sits on the "
    "portal hall's red brick: only 58 % of his back's pixels separate from SDBRCK1 at 128 (85 % from the "
    "front); the chrome, the cap and the white stripes carry his outline there, and against the drum's steel "
    "and the portal he separates on 72 % and 96 %. (5) When he fires, the cloak stays with his hips while "
    "the chest turns 8 degrees (so its edge never swings out past the coat at F1). (6) Light is gen_enemy's "
    "stand-in, NOT VERIFIED against GZDoom; nothing here has been in the engine.",
]
TURN_ASK = [
    "Approve CD as turned here; then the full set (walk A-D, salvo E-F, pain G, summon Q-R at eight "
    "rotations, death H-P, the shell SDGL A-E) is rendered on the rig for your gate in GZDoom.",
    "Or ask for a wider cloak: D's full width shows from the back, at the price of red edges round the coat "
    "from the front (the sweep's D1).",
]


def build_turnaround_sheet(t: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    m = t["metrics"]
    S = []
    idle = [_tile(t["cd"][("A", r)], 3, f"SDGNA{r}", f"{ROT_LONG[r]} · cloak {t['cape_px'][f'A{r}']} px")
            for _, r in TURN_IDLE]
    one = [_tile(t["cd"][("A", r)], 1, f"A{r} 1x") for _, r in TURN_IDLE]
    S.append(("1 · Walk/idle frame A at the eight rotations",
              "Doom's rotations: 1 front, 3 his left side, 5 his back, 7 his right side. He is handed (a "
              "different flag on each shoulder, the gun on his right), so all eight are drawn, none mirrored. "
              "Under each: the cloak's pixels visible in that view.", _strip(idle) + _strip(one)))
    fire = [_tile(t["cd"][("F", r)], 3, f"SDGNF{r}", f"fires · {ROT_LONG[r]} · cloak {t['cape_px'][f'F{r}']} px")
            for _, r in TURN_FIRE]
    S.append(("2 · The firing frame F at 1, 3 and 5",
              "general.zs: F fires (A_SD_GeneralShot). The field gun on his right shoulder fires; his hand "
              "points the swagger stick.", _strip(fire)))
    cmp_ = [_tile(t["c"][("A", 1)], 3, "C A1", "the sweep's C"), _tile(t["cd"][("A", 1)], 3, "CD A1", "this"),
            _tile(t["c"][("F", 1)], 3, "C F1", "the sweep's C"), _tile(t["cd"][("F", 1)], 3, "CD F1", "this")]
    rows = [[f"{f}1", m[f"front_{f}1_px_unlike_C"], m[f"front_{f}1_width"], m[f"front_{f}1_width_C"],
             t["cape_px"][f"{f}1"]] for f in ("A", "F")]
    S.append(("3 · From the front he is C",
              "The CEO's condition: C from the front, so the flags show and the hourglass stays.",
              _strip(cmp_) + sheetlib.table(["view", "pixels unlike C", "width px", "C's width", "cloak px"],
                                            rows)))
    lines = t["lines"]
    body = ""
    for key, wall, light, what in SCENES:
        sc = lines[key]
        body += _strip([_img_tile(sc, 1, f"{key} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{key} 2x, for the eye")])
    body += ('<p class="lead">Left to right: ' + html.escape(" · ".join(lines["labels"]))
             + ". Each sprite stands by its own offsets, as the engine places it.</p>")
    S.append(("4 · At 1x in the portal hall, front and back, beside the approved enemies",
              "MAP03's portal hall (SDBRCK1 at 128 over SDFLR4, the drum's SDSTEL1 at 144, the portal's SDPORT1 "
              "at 144). Light is gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.", body))
    sils = [_img_tile(heavy.silhouette_rgb(t["cd"][("A", r)]), 5, f"A{r}") for r in (1, 2, 3, 5)]
    S.append(("5 · 16 px (ART-BIBLE §6.4)", "Black shape, 16 px tall, shown 5x.", _strip(sils)))
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(p)}</p>" for p in TURN_NOTES) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in TURN_ASK) \
            + "</ol></div>"
    S.append(("6 · How it is built, what does not work, what next", "", body))
    intro = ("D71: the General is C from the front and D from the back. This is that one cell, CD, turned all the "
             "way round before the full set: frame A at the eight rotations, the firing frame at 1, 3 and 5, and "
             "at 1x in the portal hall. Built by <code>tools/art/gen_general.py</code> on "
             "<code>tools/art/rig_core.py</code> (imported, not edited), palette v2, seed "
             f"{SEED}, no system fonts. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_general.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Approved sprites read from assets/sprites/ (rifleman, legion, panzermensch). "
              "Freedoom's CYBRA1 shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause (© the Freedoom "
              "contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_general-CD-turnaround.html"
    sheetlib.write_sheet(path, lang="en", title="The General, cell CD — turnaround (F5, D71)",
                         subtitle="SDGN · C from the front, D from the back · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    Image.fromarray(turnaround_contact(t), "RGB").save(path.with_suffix(".png"), optimize=True)
    return path


def turnaround_contact(t: dict) -> np.ndarray:
    """Row 1: A1-A8 at 2x; row 2: F1 F3 F5, then C's A1 for the front check;
    under them the P1 lineup at 2x."""
    z, gap = CONTACT_ZOOM, 12
    rows = [[t["cd"][v] for v in TURN_IDLE], [t["cd"][v] for v in TURN_FIRE] + [t["c"][("A", 1)]]]
    cell_w, cell_h = CV.w * z + gap, CV.h * z + gap
    lw = t["lines"]["P1"].shape[1] * z
    width = max(len(rows[0]) * cell_w, lw) + 2 * gap
    height = gap + cell_h * len(rows) + t["lines"]["P1"].shape[0] * z + 2 * gap
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = CONTACT_BG
    for i, row in enumerate(rows):
        for j, spr in enumerate(row):
            x, y = gap + j * cell_w, gap + i * cell_h
            canvas[y:y + CV.h * z, x:x + CV.w * z] = core.NEUTRAL
            _paste(canvas, spr, x, y, z)
    _paste(canvas, t["lines"]["P1"], gap, gap + cell_h * len(rows) + gap, z)
    return canvas


# ====================================================== the full set (D72)
# D72 (CEO, 2026-10-14): "OK al general", the CD turnaround. This section
# renders every frame SD_General's states name (general.zs, read, never
# edited), on the turnaround's figure:
#
#   Spawn A B 10, See AABBCCDD 3, Missile E 6 F 12 E 12 F 12 E 12 F 12,
#   Pain G 10, Death H I J K L M N O 10, P 30, P -1 (A_BossDeath). Summon
#   borrows CYBR E F today and becomes SDGN Q 15 Bright / R 15 when the art
#   lands (general.zs says so on those lines): the plan reads the class and
#   swaps the Summon state's two letters for SUMMON_FINAL.
#   Living A-G and Q R at 8 drawn rotations (handed: a different flag on
#   each shoulder, the gun on his right; no mirrored pairs), death H-P at
#   rotation 0: 72 + 9 = 81 lumps SDGN.
#   SD_GeneralShell (general_shell.zs) flies on MANF A B and bursts on
#   MISL B C D today; its own sprite is SDGL A-B flight, C-E burst
#   (BESTIARY 2.7): 5 lumps at rotation 0.
#
# The turnaround's pixels the CEO approved stay: SDGN A1-A8 and F1 F3 F5
# are the turnaround's SDGN_CD_*, byte for byte (full_identity()).
#
# The death (the CEO's rule since the Legion's first L0, "parece que se
# apoye en el hombro", "it looks as if it leans on its shoulder"; SDHSM0 was redone for the same reason): the corpse
# lies with its weight on the floor and is MEASURED, not judged by eye. Hit
# in the chest (H), his knees go and the cap flies off (I), he falls back
# over his heels twisting (J, K) while the field gun is torn off its cradle,
# and he lies on his back across the screen ON HIS CLOAK, spread under him
# on the floor: the Reich's red with the disc on the near side, the stars
# and stripes on the far side (L). Head, arms and legs are each let fall
# about their joint until they touch (gen_heavy.pm_settle, bisection on
# rig_core.lowest_y); the cap and the gun lie beside him, nothing of them
# standing up; the coat's skirt collapses (no tent over the legs); dark-red
# blood (D49) runs from the chest into a pool on the cloak (M-P). As every
# approved corpse, the frames on the floor are drawn from higher (up to 28
# degrees more) as they fall: a player looks down at a body.
GENERAL_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "general.zs"
SHELL_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "general_shell.zs"
SHELL_SPRITE = "SDGL"           # BESTIARY §9, 2.7
SUMMON_FINAL = "QR"             # general.zs: "final art: SDGN Q" / "SDGN R"
SHELL_FRAMES = "ABCDE"          # A-B flight, C-E burst (BESTIARY 2.7)
FULL_DIR = OUT_DIR / "full"
DEATH_CV = core.Canvas(300, 168, 150, 140)   # lying ~100 units across, the cloak's fan, the spray; H stands 100
SHELL_CV = core.Canvas(40, 40, 20, 24)       # grAb (20, 20): centred, as the storm bolt's
SHELL_Y = SHELL_CV.foot_row - SHELL_CV.h // 2
BLOOD_GRAVITY = heavy.BLOOD_GRAVITY
DEAD_COAT_KZ, DEAD_COAT_Z = 0.30, -5.0       # the skirt collapsed: its back still on the cloak, nothing tented
# The cloak spread on the floor (L-P), built in his upright frame as a fan
# in the plane just behind his back: when he lies on his back it is the
# floor under him. From the hinge between the shoulder blades, out to his
# calves, opening to 44 degrees each side.
SPREAD_Z = -10.9
SPREAD_HINGE = V(0.0, 71.0, SPREAD_Z)
SPREAD_R0, SPREAD_LEN = 6.0, 58.0
SPREAD_ANG = (2.0, 44.0)
SPREAD_DISC = (32.0, 44.0)      # (degrees, distance from the hinge) of the Reich's disc on his left half
GN_BLOOD = {
    "blood": Mat.on_ramp("flag_red", 1, 5, black_floor=True, shift=False, flat=True),    # spray, splats, stains
    "pool": Mat.on_ramp("flag_red", 0, 3, black_floor=True, shift=False, flat=True),     # standing blood
    # SD_GeneralShell (additive in the engine: only bright colours count)
    "gls_core": Mat((("cream_yellow", 13, 15), ("white",)), shift=False, flat=True),
    "gls_ring": Mat.on_ramp("hazard_yellow", 9, 15, shift=False, flat=True),
    "gls_ember": Mat.on_ramp("flag_red", 7, 11, shift=False, flat=True),
    "gls_dim": Mat.on_ramp("hazard_yellow", 4, 10, shift=False, flat=True),
}
GN_FULL_MATERIALS: dict[str, Mat] = dict(GN_MATERIALS)
for _n, _m in GN_BLOOD.items():
    core.register_material(_n, _m, GN_FULL_MATERIALS)
FLOOR_SYMBOL = tuple(r[1:6].replace(".", "_") for r in flat.ARMBAND[1:6])   # the armband's 5x5, black only
FLOOR_DISC_INSIGNIA = core.Insignia("floor_disc", (5, 5), stamp_drawer(FLOOR_SYMBOL, STAMP_COLOURS),
                                    outward=(0.0, 0.0, 1.0), min_px=10, search=1)
FULL_INSIGNIA = PENNANT_INSIGNIA + CLOAK_INSIGNIA + (FLOOR_DISC_INSIGNIA,)

A_ = ANKLE_Y
_F = POSES["F"]
FULL_POSES: dict[str, Pose] = {
    "A": POSES["A"],                                            # the turnaround's, as approved
    "B": replace(POSES["A"], key="B", title="right leg passing", foot_l=(6.8, A_, 0.5),
                 foot_r=(-6.8, A_ + 3.0, -0.5), hand_r=(-17.0, 46.5, 3.0), hem_tilt=4.5, hem_roll=1.5,
                 cloak_swing=4.0),
    "C": replace(POSES["A"], key="C", title="right foot forward", foot_l=(6.8, A_, -4.5),
                 foot_r=(-6.8, A_, 5.5), hand_r=(-17.0, 46.5, 0.5), cloak_swing=1.5),
    "D": replace(POSES["A"], key="D", title="left leg passing", foot_l=(6.8, A_ + 3.0, -0.5),
                 foot_r=(-6.8, A_, 0.5), hand_r=(-17.0, 46.5, 3.0), hem_tilt=4.5, hem_roll=-1.5,
                 cloak_swing=4.0),
    "E": replace(_F, key="E", title="aims: the stick on the target", hand_r=(-13.5, 67.5, 22.0),
                 aim=(-0.10, -0.06, 1.0), twist=-6.0, swing_r=28.0, fire=False),
    "F": _F,                                                    # the turnaround's, as approved
    "G": Pose("G", "pain: struck in the chest, he rocks back", (7.0, A_, 3.0), (-7.5, A_, -2.0),
              (-26.0, 57.0, 6.0), (9.0, 60.0, 11.5), (-0.5, -0.5, 0.7), (0.0, 1.0, 0.0),
              swing_r=30.0, lean=8.0, head_pitch=18.0, head_turn=12.0, hem_tilt=-2.0,
              pole_l=(1.0, -1.0, 0.2), pole_r=(-1.0, -0.6, -0.6)),
    "Q": Pose("Q", "the order: 'Vorwärts!', his fist raised", (7.0, A_, 2.5), (-7.5, A_, -2.5),
              (-13.5, 67.5, 22.0), (18.0, 105.5, 3.0), (-0.10, 0.25, 1.0), (0.0, 1.0, 0.0),
              twist=-4.0, swing_r=28.0, lean=3.0, head_pitch=10.0, pole_l=(1.0, 0.0, -0.6)),
    "R": Pose("R", "... and he points them on", (6.0, A_, 5.0), (-7.0, A_, -4.0),
              (-17.0, 46.5, 5.5), (12.0, 75.0, 28.0), (0.05, -0.80, 0.60), (0.0, 0.30, 1.0),
              swing_l=30.0, lean=-5.0, head_pitch=-4.0, cloak_swing=3.0, pole_l=(1.0, -1.0, 0.0)),
}
FULL_TITLES = {f: p.title for f, p in FULL_POSES.items()}
FULL_TITLES["A"], FULL_TITLES["F"] = "walk: left foot forward (the turnaround's)", "fires (the turnaround's)"
WOUND = (5.5, 66.0)             # (x, y) of the round's hole, on his left pectoral, upright


@dataclass(frozen=True)
class Fall:
    """A death frame (H-P): the pose, then how far he has fallen."""
    pose: Pose
    t: float                    # s after the hit
    fall: float                 # degrees back over his heels
    yaw: float                  # degrees he has twisted (90: lying across the screen)
    cap: str = "on"             # "on" | "fly1" | "fly2" | "floor"
    gun: str = "on"             # "on" | "knock" | "fly" | "floor"
    settle: tuple = ()          # what is let fall to the floor: keys of SETTLE
    pool: float = 0.0           # share of the full pool
    stain: float = 3.0          # radius of the stain round the wound
    tilt: float = 0.0           # degrees the render looks further down


_DEAD = Pose("P", "dead", (8.5, A_, -1.0), (-8.5, A_, -2.0), (-31.0, 50.0, -8.0), (44.0, 70.0, -6.0),
             (-0.6, -0.7, -0.2), (0.0, 0.0, 1.0), head_pitch=10.0, no_cap=True, no_sgun=True,
             pole_l=(1.0, 0.0, -1.0), pole_r=(-1.0, 0.0, -1.0))
_LYING = replace(_DEAD, coat_flat=True, spread=True)
SETTLE_ALL = ("head", "arm_l", "arm_r", "fore_l", "fore_r", "leg_l", "leg_r")
FALLS: dict[str, Fall] = {              # general.zs: H-O 10 tics, P 30 then held (A_Scream on I, A_NoBlocking on M)
    "H": Fall(Pose("H", "hit: the chest opens", (7.0, A_, 3.0), (-7.5, A_, -3.0), (-26.0, 60.0, 4.0),
                   (24.0, 62.0, 4.0), (-0.3, -0.5, 0.8), (0.0, 1.0, 0.0), swing_r=30.0, swing_l=30.0,
                   lean=8.0, head_pitch=22.0, pole_l=(1.0, -0.5, -0.5), pole_r=(-1.0, -0.5, -0.5)),
              0.06, 0.0, 0.0, stain=3.0),
    "I": Fall(Pose("I", "his knees go, the cap flies", (7.5, A_, 4.0), (-7.5, A_, 1.0), (-28.0, 66.0, -2.0),
                   (28.0, 66.0, -2.0), (-0.4, 0.2, 0.8), (0.0, 1.0, 0.0), swing_r=30.0, swing_l=30.0,
                   bob=-3.0, lean=12.0, head_pitch=30.0, no_cap=True, sgun_knock=28.0, hem_tilt=7.0,
                   pole_l=(1.0, -0.5, -0.5), pole_r=(-1.0, -0.5, -0.5)),
              0.35, 12.0, 10.0, cap="fly1", gun="knock", stain=4.0),
    "J": Fall(Pose("J", "falling back, the gun torn off", (7.5, A_, 4.0), (-7.5, A_, 1.0), (-27.0, 70.0, -6.0),
                   (27.0, 70.0, -6.0), (-0.4, 0.4, 0.6), (0.0, 1.0, 0.0), swing_r=30.0, swing_l=30.0,
                   bob=-2.0, lean=6.0, head_pitch=30.0, no_cap=True, no_sgun=True, hem_tilt=6.0,
                   spread=True,                     # the cloak flares out behind him as he goes
                   pole_l=(1.0, -0.5, -0.5), pole_r=(-1.0, -0.5, -0.5)),
              0.64, 40.0, 38.0, cap="fly2", gun="fly", stain=5.0, tilt=4.0),
    "K": Fall(replace(_LYING, key="K", title="he lands on his cloak"), 0.93, 82.0, 80.0, cap="floor",
              gun="floor", stain=4.6, tilt=14.0),
    "L": Fall(replace(_LYING, key="L", title="on his back, the cloak spread"), 1.21, 90.0, 86.0,
              cap="floor", gun="floor", settle=("head",), stain=5.0, tilt=20.0),
    "M": Fall(replace(_LYING, key="M", title="the limbs fall (A_NoBlocking)"), 1.50, 90.0, 88.0,
              cap="floor", gun="floor", settle=SETTLE_ALL, pool=0.35, stain=5.4, tilt=25.0),
    "N": Fall(replace(_LYING, key="N", title="the blood runs onto the flags"), 1.79, 90.0, 90.0,
              cap="floor", gun="floor", settle=SETTLE_ALL, pool=0.65, stain=5.7, tilt=28.0),
    "O": Fall(replace(_LYING, key="O", title="still"), 2.07, 90.0, 90.0, cap="floor", gun="floor",
              settle=SETTLE_ALL, pool=0.85, stain=5.9, tilt=28.0),
    "P": Fall(replace(_LYING, key="P", title="dead (held; A_BossDeath)", head_turn=-22.0), 3.0, 90.0, 90.0,
              cap="floor", gun="floor", settle=SETTLE_ALL, pool=1.0, stain=6.0, tilt=28.0),
}
FALL_PIVOT = V(0.0, 0.0, -6.0)          # behind his heels: he falls back over them
# (the prims turned, the probe that must touch, pivot anchor, tip anchor, anchors that ride)
SETTLE = {
    "head": ("head", None, "neck", "head_top", ("head_top",)),
    "arm_l": ("arm_l", slice(0, 1), "shoulder_l", "hand_l", ("elbow_l", "wrist_l", "hand_l")),
    "arm_r": ("arm_r", slice(0, 1), "shoulder_r", "hand_r", ("elbow_r", "wrist_r", "hand_r", "stick_tip")),
    "fore_l": ("fore_l", slice(2, 3), "elbow_l", "hand_l", ("wrist_l", "hand_l")),          # till the glove touches
    "fore_r": ("fore_r", slice(2, None), "elbow_r", "hand_r", ("wrist_r", "hand_r", "stick_tip")),  # glove, stick
    "leg_l": ("leg_l", slice(1, 4), "hip_l", "ankle_l", ("knee_l", "ankle_l")),
    "leg_r": ("leg_r", slice(1, 4), "hip_r", "ankle_r", ("knee_r", "ankle_r")),
}
LYING_MAX = 2.0                 # units: a part this far above the floor still lies on it
LYING_SUPPORT = 1.0
LYING_TOP = 28.0                # his chest (the cuirass and pauldrons) is thick: nothing higher than this, lying
LYING_SPAN = 60.0               # the parts that touch spread at least this far
N_SPRAY = 48
POOL = (30.0, 16.0)             # (x, z) radii of the full pool under his chest
SPRAY_X = (-128.0, 128.0)       # landed splats stay inside the death canvas
SPRAY_Z = (-30.0, 44.0)
AIR_Y = 118.0


def _spread_cloak(add) -> None:
    """The cloak lying spread (L-P), a fan in the plane behind his back
    (SPREAD_Z): his left half the Reich's red with the white disc, his right
    half the stars and stripes radiating from the hinge, the canton by it."""
    zv = V(0.0, 0.0, 1.0)

    def ray(theta: float, side: int) -> tuple[np.ndarray, np.ndarray]:
        t = np.deg2rad(theta)
        d = V(side * np.sin(t), -np.cos(t), 0.0)
        e = np.cross(d, zv)
        return d, np.column_stack([e, d, zv])

    def piece(mat, theta, side, r0, length, width, dz, tag=""):
        d, rot = ray(theta, side)
        c = SPREAD_HINGE + d * (r0 + length / 2) + V(0, 0, dz)
        return add("spread", core.box(mat, 0.6, tuple(c), (width / 2, length / 2, 0.25), rot=rot, tag=tag))

    a0, a1 = SPREAD_ANG
    edges = np.linspace(a0, a1, US_STRIPES + 1)
    far = SPREAD_R0 + SPREAD_LEN
    for i in range(US_STRIPES):                       # his right: the stripes radiate
        th = (edges[i] + edges[i + 1]) / 2
        w = far * np.deg2rad(edges[i + 1] - edges[i]) * 1.25
        red = i % 2 == 0
        piece("pennant_red" if red else "pennant_white", th, core.RIGHT, SPREAD_R0, SPREAD_LEN, w,
              0.08 if red else 0.0)
    cth = (edges[0] + edges[CANTON_STRIPES]) / 2      # the canton, by the hinge
    clen = CANTON_DROP + 2.0
    cw = (SPREAD_R0 + clen) * np.deg2rad(edges[CANTON_STRIPES] - edges[0]) * 1.05
    piece("us_blue", cth, core.RIGHT, SPREAD_R0, clen, cw, 0.16, tag="spread_canton")
    for r_, th in ((12.0, 8.0), (18.0, 16.0), (24.0, 8.0), (12.0, 20.0), (24.0, 20.0), (18.0, 4.0)):
        d, _ = ray(th, core.RIGHT)
        add("spread", core.ellipsoid("pennant_white", 0.9, tuple(SPREAD_HINGE + d * r_ + V(0, 0, 0.45)),
                                     (0.75, 0.75, 0.2)))       # stars
    for th in np.linspace(a0 + 4.0, a1 - 4.0, 6):    # his left: the Reich's red
        w = far * np.deg2rad((a1 - a0) / 5.0) * 1.3
        piece("pennant_red", th, core.LEFT, SPREAD_R0, SPREAD_LEN, w, 0.0)
    th, r_ = SPREAD_DISC
    d, _ = ray(th, core.LEFT)
    add("spread", core.ellipsoid("pennant_white", 0.8, tuple(SPREAD_HINGE + d * r_ + V(0, 0, 0.2)),
                                 (6.0, 6.0, 0.35), tag="floor_disc"))


def _settle_parts(P: list[core.Prim], what: str) -> list[core.Prim]:
    """The primitives one settle step turns: the head; an arm from the
    shoulder (with the stick in the right hand) or its forearm from the
    elbow; a leg from the hip."""
    if what == "head":
        return [p for p in P if p.grp == "head"]
    limb, s = what.split("_")
    side = core.LEFT if s == "l" else core.RIGHT
    if limb in ("arm", "fore"):
        arm = [p for p in P if p.limb == "arm" and p.side == side]
        stick = [p for p in P if p.grp == "gun"] if side == core.RIGHT else []
        return (arm if limb == "arm" else arm[1:]) + stick
    return [p for p in P if p.limb == "leg" and p.side == side]


def _rigid(P: list[core.Prim], anch: dict, R: np.ndarray, pivot, offset=(0.0, 0.0, 0.0)) -> None:
    heavy._pm_rigid(P, anch, R, pivot, offset)


def _loose(kind: str) -> list[core.Prim]:
    """The cap or the field gun on their own, as they sat on him upright (A)."""
    P: list[core.Prim] = []

    def add(grp: str, prim: core.Prim) -> core.Prim:
        prim.grp = grp
        P.append(prim)
        return prim
    if kind == "cap":
        _cap(add)
    else:
        _field_gun(add, {})
    for p in P:
        p.grp = "loose"
    even_light(P, GN_MATERIALS)
    return P


def _place_loose(kind: str, state: str, anch: dict, lying_mid: float) -> list[core.Prim]:
    """The cap and the gun once off him. In the air they follow his head and
    shoulder; on the floor they lie beside him on the near side, every part
    down (rest_on_floor), nothing standing up."""
    P = _loose(kind)
    centre = V(0.0, 91.0, 0.8) if kind == "cap" else V(-(SHOULDER[0] + 0.8), SHOULDER[1] + 7.4, 5.0)
    if state in ("fly1", "fly2", "fly"):
        if kind == "cap":
            ref = anch["head_top"]
            R = core.rot_x(-40.0 if state == "fly1" else -110.0) @ core.rot_z(25.0)
            off = V(-3.0, 10.0, -6.0) if state == "fly1" else V(6.0, 6.0, -16.0)
        else:
            ref = anch["shoulder_r"]
            R = core.rot_y(35.0) @ core.rot_x(-30.0)
            off = V(-8.0, 9.0, 10.0)
        _rigid(P, {}, R, centre, ref - centre + off)
        return P
    # on the floor (K-P)
    if kind == "cap":
        R = core.rot_y(-30.0) @ core.rot_z(14.0)          # on its side a little, the peak to the camera
        at = V(lying_mid + 58.0, 0.0, 20.0)
    else:
        R = core.rot_y(68.0)                              # the barrel along the floor
        at = V(lying_mid + 6.0, 0.0, 34.0)
    _rigid(P, {}, R, centre, at - centre)
    core.rest_on_floor(P, {}, {"loose"})
    return P


def death_model(frame: str) -> tuple[list[core.Prim], dict, list[core.Prim]]:
    """Death frame H-P in model space (floor y = 0), untilted, without the
    blood: (his primitives, his anchors as points, the cap and gun apart)."""
    f = FALLS[frame]
    P, anch = model(CD, pose=f.pose)
    if f.fall or f.yaw:
        _rigid(P, anch, core.rot_y(f.yaw) @ core.rot_x(f.fall), FALL_PIVOT)
    turning = {id(p) for w in f.settle for p in _settle_parts(P, w)}
    pens = [p for p in P if p.grp in ("pen_l", "pen_r")]
    resting = [p for p in P if id(p) not in turning and p.grp not in ("pen_l", "pen_r")]
    low = core.lowest_y(resting)
    if f.fall >= 60.0 or low < 0.0:                  # down on the floor (or on his cloak): his lowest part on it
        _rigid(P, anch, np.eye(3), V(0, 0, 0), V(0, -low, 0))
    for what in f.settle:
        _, probe, root, tip, rides = SETTLE[what]
        part = _settle_parts(P, what)
        pr = part if probe is None else part[probe]
        R = heavy.pm_settle(part, pr, anch[root][0], anch[tip][0])
        pivot = anch[root][0]
        for k in rides:
            if k in anch:
                pt, g = anch[k]
                anch[k] = (R @ (pt - pivot) + pivot, g)
    if f.fall >= 85.0:                                # the pennants, hanging from nothing now, lie on the floor
        for grp in ("pen_l", "pen_r"):
            core.rest_on_floor([p for p in pens if p.grp == grp], {}, {grp})
    mid = float(np.mean([p.bound()[0][0] for p in P if p.grp in ("upper", "coat", "head")]))
    shift = -mid * min(f.fall / 90.0, 1.0)            # slid to the actor's axis as he goes down
    _rigid(P, anch, np.eye(3), V(0, 0, 0), V(shift, 0, 0))
    loose: list[core.Prim] = []
    pts = {k: v[0] for k, v in anch.items()}
    if f.cap != "on":
        loose += _place_loose("cap", f.cap, pts, 0.0)
    if f.gun not in ("on", "knock"):
        loose += _place_loose("gun", f.gun, pts, 0.0)
    return P, pts, loose


def _torso_of(P: list[core.Prim]) -> core.Prim:
    return next(p for p in P if p.tag == "torso")


def wound_world(P: list[core.Prim]) -> tuple[np.ndarray, np.ndarray]:
    """The wound on his left pectoral, and its outward normal, where his torso is now."""
    t = _torso_of(P)
    x, y = WOUND
    p = V(x, y, torso_z(x, y) + 1.4)
    n = unit(V(0.25, 0.1, 1.0))
    return t.xm @ p + t.xt, t.xm @ n


def _droplet(p0, v, t: float, r: float, air: float = AIR_Y) -> core.Prim:
    """gen_heavy's droplet, its landed splats a little higher: on the
    spread cloak (0.5 thick) they must sit on the cloth, not under it."""
    q = heavy._droplet(p0, v, t, r, SPRAY_X, SPRAY_Z, air)
    if q.grp == "splat":
        q.a = V(q.a[0], 0.62, q.a[2])
    return q


def _body_blood(P: list[core.Prim], stain: float, run: bool) -> list[core.Prim]:
    """On him, riding the torso: the hole, the stain soaking the chrome, a run."""
    t = _torso_of(P)
    x, y = WOUND
    zf = torso_z(x, y) + 1.4
    n = unit(V(0.25, 0.1, 1.0))
    out = [heavy._stain("blood", 0.48, V(x, y - stain * 0.15, zf), n, stain, depth=0.9 * stain, grp="blood"),
           core.ellipsoid("void", 0.05, (x, y, zf + 0.35), (1.3, 1.4, 0.8), grp="blood")]
    if run:
        out.append(core.rcone("blood", 0.4, V(x + 0.3, y - 2.0, torso_z(x, y - 2.0) + 1.3),
                              V(x + 1.2, y - 11.0, torso_z(x + 1.2, y - 11.0) + 0.9), 1.6, 1.1, grp="blood"))
    for q in out:
        q.xm, q.xt = t.xm.copy(), t.xt.copy()
    return out


_HIT: dict = {}


def wound_at_hit() -> tuple[np.ndarray, np.ndarray]:
    if "H" not in _HIT:
        _HIT["H"] = wound_world(death_model("H")[0])
    return _HIT["H"]


def death_blood(frame: str, P: list[core.Prim]) -> list[core.Prim]:
    """All the blood of death frame H-P: on him, in the air, on the floor."""
    f = FALLS[frame]
    k = "HIJKLMNOP".index(frame)
    out = _body_blood(P, f.stain, k >= 1)
    hit, n = wound_at_hit()
    rng = np.random.default_rng(SEED + 61)
    for i in range(N_SPRAY):
        d = unit(n * rng.uniform(0.4, 1.0) + V(rng.uniform(-0.8, 0.8), rng.uniform(-0.1, 0.9), rng.uniform(-0.4, 0.4)))
        gout = i % 5 == 0
        sp = rng.uniform(10, 28) if gout else rng.uniform(30, 95)
        r = rng.uniform(1.4, 2.0) if gout else rng.uniform(0.7, 1.2)
        out.append(_droplet(hit, d * sp, f.t, r))
    w, wn = wound_world(P)
    if frame in "IJK":                                     # it pumps while he falls
        rr = np.random.default_rng(SEED + 62 + k)
        for j in range(7):
            v = wn * rr.uniform(8, 20) + V(rr.uniform(-5, 5), rr.uniform(0, 8), rr.uniform(-5, 5))
            out.append(_droplet(w, v, 0.03 + 0.03 * j, rr.uniform(0.7, 1.1)))
    if f.pool:
        g = f.pool
        out += hound.pool(float(w[0]), float(w[2]) + 6.0, POOL[0] * g, POOL[1] * (0.45 + 0.55 * g),
                          np.random.default_rng(SEED + 64))
        for q in out[-4:]:
            q.a = V(q.a[0], q.a[1] + 0.4, q.a[2])            # on the cloth
    return out


def pain_blood(P: list[core.Prim], t: float = 0.05) -> list[core.Prim]:
    """G: the round's hole and a spurt out of the cuirass."""
    out = _body_blood(P, 2.6, False)
    w, n = wound_world(P)
    rng = np.random.default_rng(SEED + 67)
    for _ in range(10):
        v = n * rng.uniform(30, 65) + V(rng.uniform(-14, 14), rng.uniform(0, 30), rng.uniform(-8, 8))
        p = w + v * t + V(0, -0.5 * BLOOD_GRAVITY * t * t, 0)
        r = rng.uniform(0.8, 1.2)
        out.append(core.ellipsoid("blood", 0.62, tuple(p), (r, r * 1.15, r), grp="spray"))
    return out


def _tilted(P: list[core.Prim], deg: float) -> list[core.Prim]:
    if deg:
        hound._rigid(P, core.rot_x(-deg), V(0, 0, 0))
    return P


def corpse_parts(P: list[core.Prim]) -> dict[str, list[core.Prim]]:
    """The lying General's parts by name: what must rest on the floor."""
    out = {"torso": [_torso_of(P)], "coat": [p for p in P if p.tag == "coat"],
           "head": [p for p in P if p.grp == "head"], "cloak": [p for p in P if p.grp == "spread"]}
    for name, side in (("left", core.LEFT), ("right", core.RIGHT)):
        arm = [p for p in P if p.limb == "arm" and p.side == side]
        leg = [p for p in P if p.limb == "leg" and p.side == side]
        out[f"upper_arm_{name}"], out[f"glove_{name}"] = arm[:1], arm[3:4]
        out[f"boot_{name}"], out[f"foot_{name}"] = leg[1:2], leg[3:4]
    return out


def corpse_metrics(frame: str = "P") -> dict:
    """The lying checks on the untilted model: each part's lowest point above
    the floor, the highest point of him (cap, gun and blood aside), the
    spread of what touches, how far the torso lies across the screen, and
    the cap and gun lying (their tops)."""
    P, _, loose = death_model(frame)
    parts = corpse_parts(P)
    rep = {k: round(core.lowest_y(v), 2) for k, v in parts.items() if v}
    xs = [float(np.mean([p.bound()[0][0] for p in parts[k]])) for k, v in rep.items()
          if v <= LYING_SUPPORT and k != "cloak"]
    torso = parts["torso"][0]
    caps = [p for p in loose if p.mat in ("cap_crown", "cap_band", "peak") or p.mat == "braid"]
    return {"lowest": rep, "top": round(hound.highest_y(P), 2), "span": round(max(xs) - min(xs), 1),
            "across": round(abs(float((torso.xm @ V(0, 1, 0))[0])), 3),
            "loose_top": round(hound.highest_y(loose), 2) if loose else None,
            "loose_lowest": round(core.lowest_y(loose), 2) if loose else None,
            "n_cap_parts": len(caps)}


# ---------------------------------------------------------------- the shell SDGL
def shell_model(frame: str) -> list[core.Prim]:
    """SD_GeneralShell, SDGL A-E at rotation 0: A-B the shell flying at you
    (a white-hot core in a braid-yellow fire, an ember ring, sparks that
    swap), C-E the burst. Additive in the engine (general_shell.zs)."""
    c = V(0, SHELL_Y, 0)
    E = core.ellipsoid
    if frame in "AB":
        a = 0.0 if frame == "A" else 1.0
        P = [E("gls_ember", 0.6, tuple(c), (5.0 + 0.5 * a, 4.6 - 0.4 * a, 3.0)),
             E("gls_ring", 0.75, tuple(c + V(0, 0, 1.2)), (3.6, 3.4, 2.4)),
             E("gls_core", 0.9, tuple(c + V(0.2 * a, 0.2 * a, 2.6)), (1.9, 1.9, 1.2))]
        for ang in ((45.0, 225.0) if frame == "A" else (135.0, 315.0)):
            q = np.deg2rad(ang)
            P.append(E("gls_ring", 0.8, tuple(c + V(7.4 * np.cos(q), 7.4 * np.sin(q), 1.0)), (1.2, 1.2, 1.2)))
        return P
    step = "CDE".index(frame)
    P = []
    if step < 2:
        P.append(E("gls_ring" if step == 0 else "gls_dim", 0.65, tuple(c), (6.0 + 2.2 * step,) * 3))
        P.append(E("gls_core" if step == 0 else "gls_ring", 0.85, tuple(c + V(0, 0, 4.0 + step)),
                   (3.4 - 0.8 * step,) * 3))
    n = 7 + 2 * step
    for i in range(n):
        q = 2 * np.pi * (i + 0.5 * step) / n
        rad = 8.0 + 3.2 * step
        P.append(E("gls_ember" if step < 2 else "gls_dim", 0.7, tuple(c + V(rad * np.cos(q), rad * np.sin(q), 1.5)),
                   (1.5 - 0.2 * step,) * 3))
    return P


def render_shell(frame: str) -> np.ndarray:
    return core.render(shell_model(frame), 0, SHELL_CV, GN_FULL_MATERIALS, seed=SEED, what=f"{SHELL_SPRITE}{frame}0")


# ---------------------------------------------------------------- the plan
def zs_states(path: Path = GENERAL_ZS) -> dict[str, list[tuple[str, int]]]:
    """The class's states (letter, tics), read from its ZScript; the Summon
    state's borrowed CYBR E F become SDGN Q R (SUMMON_FINAL)."""
    st = hound.zs_states(path)
    if "Summon" in st:
        seq = st["Summon"]
        st["Summon"] = [(SUMMON_FINAL[i], t) for i, (_, t) in enumerate(seq)]
    return st


def full_frames() -> tuple[str, str]:
    """(the letters drawn at 8 rotations, the death letters at rotation 0)."""
    st = zs_states()
    living = sorted({f for lab, seq in st.items() if lab not in ("Death", "XDeath", "Raise") for f, _ in seq})
    death = "".join(dict.fromkeys(f for f, _ in st.get("Death", [])))
    return "".join(living), death


def full_plan() -> list[tuple[str, int]]:
    rotated, death = full_frames()
    return [(f, r) for f in rotated for r in range(1, core.ROTATIONS + 1)] + [(f, 0) for f in death]


def full_lump(frame: str, rotation: int, sprite: str = SPRITE) -> str:
    return f"{sprite}{frame}{rotation}"


def full_canvas(frame: str) -> core.Canvas:
    return CV if frame in FULL_POSES else DEATH_CV


def full_prims(frame: str) -> tuple[list[core.Prim], np.ndarray | None]:
    """Every primitive of one frame, ready to render, and the muzzle (F)."""
    if frame in FULL_POSES:
        P, anch = model(CD, frame, pose=FULL_POSES[frame])
        if frame == "G":
            P = P + pain_blood(P)
        return P, anch["muzzle"][0] if FULL_POSES[frame].fire else None
    P, _, loose = death_model(frame)
    return _tilted(P + loose + death_blood(frame, P), FALLS[frame].tilt), None


def render_full_layers(frame: str, rotation: int, prims=None) -> core.Layers:
    P, muzzle = full_prims(frame) if prims is None else prims
    return core.render_layers(P, rotation, full_canvas(frame), GN_FULL_MATERIALS, seed=SEED,
                              value_shift=VALUE_SHIFT, insignia=FULL_INSIGNIA, muzzle=muzzle,
                              flash_size=FLASH_SIZE, chrome=CHROME, what=full_lump(frame, rotation))


def cloak_pixels(lay: core.Layers, prims: list[core.Prim]) -> int:
    ids = [i for i, q in enumerate(prims) if q.grp in CLOAKS]
    return int(np.isin(lay.pid, ids).sum())


def blood_share(lay: core.Layers) -> float:
    ids = core.material_ids(GN_FULL_MATERIALS)
    want = [ids["blood"], ids["pool"]]
    return round(float(np.isin(lay.mat, want).sum() / max((lay.mat >= 0).sum(), 1)), 3)


def _frame_job(frame: str) -> tuple[str, dict, dict]:
    """A worker's unit: one frame at every rotation it needs (built once)."""
    rotated, _ = full_frames()
    rots = range(1, core.ROTATIONS + 1) if frame in rotated else (0,)
    prims = full_prims(frame)
    out, info = {}, {}
    for r in rots:
        lay = render_full_layers(frame, r, prims)
        out[r] = lay.rgba
        info[f"cloak_{r}"] = cloak_pixels(lay, prims[0])
        if r == 0:
            info["blood"] = blood_share(lay)
    return frame, out, info


def build_full(jobs: int = 1, only: set[str] | None = None) -> dict:
    """Render the set's lumps (PNG with grAb) into work/art/general/full/SDGN/
    and the shell's into .../SDGL/; the per-frame numbers to info.json."""
    sdir, gdir = FULL_DIR / SPRITE, FULL_DIR / SHELL_SPRITE
    sdir.mkdir(parents=True, exist_ok=True)
    gdir.mkdir(parents=True, exist_ok=True)
    frames = [f for f in dict.fromkeys(f for f, _ in full_plan()) if not only or f in only]
    info_path = sdir / "info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.is_file() else {}

    def take(res):
        frame, out, inf = res
        g = grab() if frame in FULL_POSES else core.grab_offsets(DEATH_CV)
        for r, rgba in out.items():
            heavy.save(rgba, sdir / f"{full_lump(frame, r)}.png", g)
        info[frame] = inf
        print(frame, "done", inf, flush=True)

    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            for res in ex.map(_frame_job, frames):
                take(res)
    else:
        for f in frames:
            take(_frame_job(f))
    if not only or set(SHELL_FRAMES) & set(only or ()):
        for f in SHELL_FRAMES:
            heavy.save(render_shell(f), gdir / f"{full_lump(f, 0, SHELL_SPRITE)}.png", core.grab_offsets(SHELL_CV))
    info_path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return info


def load_full() -> dict:
    out = {}
    for f, r in full_plan():
        with Image.open(FULL_DIR / SPRITE / f"{full_lump(f, r)}.png") as im:
            out[(f, r)] = np.asarray(im.convert("RGBA")).copy()
    for f in SHELL_FRAMES:
        with Image.open(FULL_DIR / SHELL_SPRITE / f"{full_lump(f, 0, SHELL_SPRITE)}.png") as im:
            out[("shell", f)] = np.asarray(im.convert("RGBA")).copy()
    return out


def full_identity(spr: dict, src: Path = TURN_DIR) -> dict[str, bool | None]:
    """Whether A1-A8, F1, F3, F5 are the approved turnaround's pixels."""
    out: dict[str, bool | None] = {}
    for f, r in TURN_VIEWS:
        path = src / f"{lump('CD', f, r)}.png"
        if not path.is_file():
            out[full_lump(f, r)] = None
            continue
        with Image.open(path) as im:
            out[full_lump(f, r)] = bool(np.array_equal(np.asarray(im.convert("RGBA")), spr[(f, r)]))
    return out


# ---------------------------------------------------------------- GIFs, lineups, numbers
HOLD_MS = heavy.HOLD_MS
LEAD_TICS = heavy.LEAD_TICS
FULL_SLOT = 80
DEAD_SLOT = 290                 # the death canvas is 300 wide: the corpse lies ~130 units either side of his axis
CORRIDOR = ("C1", "SDTILE2", 128, "SDFLR3", "the office corridor (MAP03 §15, O1)")
APPROVED_DEAD = (("SDRRL0", "rifleman", "rifleman"), ("SDLTL0", "legion", "Legion trooper"),
                 ("SDPMO0", "panzermensch", "Panzermensch"), ("SDDBL0", "doughboy", "Doughboy"))


def _runs(seq: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """gen_hound's runs, a held last frame (-1) kept held: SDGN P 30, P -1."""
    out = hound._gif_runs([x for x in seq if x[1] >= 0])
    if seq and seq[-1][1] < 0:
        out.append((seq[-1][0], -1))
    return out


def _ms(tics: int) -> int:
    return HOLD_MS if tics < 0 else int(round(tics * core.TIC_MS))


def _neutral(arrs: list[np.ndarray]) -> list[np.ndarray]:
    return [core.on_bg(x, core.NEUTRAL) for x in hound.crop_common(arrs)]


def _scene(figs, wall: str, light: int, floor: str = FLOOR, wall_h: int = LINEUP_WALL_H,
           slot: int = LINEUP_SLOT) -> np.ndarray:
    """lineup() with any MAP03 wall and floor."""
    width = slot * len(figs)
    w_rgb = flat.tile_to(asset_rgb(wall), width, wall_h)
    fl = flat.tile_to(asset_rgb(floor), width, flat.FLOOR_H * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, flat.FLOOR_H), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = wall_h + (flat.FLOOR_LINE - flat.WALL_H) - core.FEET_SINK
    for i, (spr, ox, oy) in enumerate(figs):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = base - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return core.lit(canvas, light, heavy.palette_v2())


def write_full_gifs(spr: dict) -> dict[str, Path]:
    """Every cycle at game speed, the tics read from general.zs."""
    d = FULL_DIR / SPRITE
    runs = {lab: _runs(seq) for lab, seq in zs_states().items()}
    out: dict[str, Path] = {}

    def cyc(name, seq, rot):
        out[name] = core.save_gif(_neutral([spr[(f, rot)] for f, _ in seq]), [_ms(t) for _, t in seq],
                                  d / f"{SPRITE}_{name}.gif")

    out["turntable"] = core.save_gif(_neutral([spr[("A", r)] for r in range(1, 9)]), [_ms(12)] * 8,
                                     d / f"{SPRITE}_turntable.gif")
    see = runs["See"]
    for r in range(1, 9):
        cyc(f"see_rot{r}", see, r)
    for r in (1, 3, 5, 7):
        cyc(f"attack_rot{r}", see + runs["Missile"], r)
        cyc(f"pain_rot{r}", see + runs["Pain"] + see, r)
        cyc(f"summon_rot{r}", see + runs["Summon"] + see, r)
    cyc("spawn_rot1", runs["Spawn"], 1)
    death = runs["Death"]
    out["death"] = core.save_gif(_neutral([spr[(f, 0)] for f, _ in death]), [_ms(t) for _, t in death],
                                 d / f"{SPRITE}_death.gif")
    width = 2 * max(DEATH_CV.cx, DEATH_CV.w - DEATH_CV.cx)
    frames = [_scene([(spr[("A", 1)], *grab())], "SDBRCK1", 128, slot=width)]
    durs = [_ms(LEAD_TICS)]
    for f, t in death:
        frames.append(_scene([(spr[(f, 0)], *core.grab_offsets(DEATH_CV))], "SDBRCK1", 128, slot=width))
        durs.append(_ms(t))
    out["death_floor"] = core.save_gif(frames, durs, d / f"{SPRITE}_death_floor.gif")
    wall = flat.tile_to(asset_rgb("SDBRCK1"), SHELL_CV.w, SHELL_CV.h)
    add = lambda rgba: _additive(rgba, wall)  # noqa: E731
    out["shell_flight"] = core.save_gif([add(spr[("shell", f)]) for f in "AB"], [_ms(4)] * 2,
                                        FULL_DIR / SHELL_SPRITE / "shell_flight.gif")
    out["shell_burst"] = core.save_gif([add(spr[("shell", f)]) for f in "CDE"], [_ms(t) for t in (8, 6, 4)],
                                       FULL_DIR / SHELL_SPRITE / "shell_burst.gif")
    return out


def _additive(rgba: np.ndarray, under: np.ndarray) -> np.ndarray:
    """RenderStyle "Add" (the shell): the sprite's colour added to what is
    behind it. A stand-in, NOT VERIFIED against GZDoom's blending."""
    out = (under.astype(np.int32) * 128 // 224).copy()       # the brick at light 128
    a = rgba[..., 3] > 0
    out[a] += rgba[..., :3][a]
    return np.clip(out, 0, 255).astype(np.uint8)


def full_lineups(spr: dict) -> dict:
    """At 1x in MAP03: the portal hall and the office corridor, beside the
    approved enemies; then the corpse beside the approved corpses."""
    d = FULL_DIR / SPRITE
    picks = (("A", 1), ("A", 3), ("A", 5), ("F", 1), ("Q", 1), ("G", 1))
    figs = [(spr[v], *grab()) for v in picks]
    labels = [full_lump(*v) for v in picks]
    rf, rl = references()
    figs += rf
    labels += rl
    out = {"labels": labels, "scenes": {}}
    for key, wall, light, what in SCENES[:2]:
        sc = _scene(figs, wall, light, slot=FULL_SLOT)
        Image.fromarray(sc, "RGB").save(d / f"lineup_{key}.png", optimize=True)
        out["scenes"][key] = (sc, wall, light, what)
    key, wall, light, floor, what = CORRIDOR
    sc = _scene(figs, wall, light, floor, slot=FULL_SLOT)
    Image.fromarray(sc, "RGB").save(d / f"lineup_{key}.png", optimize=True)
    out["scenes"][key] = (sc, wall, light, what)
    dead = [(spr[("P", 0)], *core.grab_offsets(DEATH_CV))]
    dlabels = [f"{SPRITE}P0"]
    for name, folder, label in APPROVED_DEAD:
        r = heavy.approved(name, folder)
        if r:
            dead.append(r)
            dlabels.append(f"{name} {label}, approved")
    for light in (176, 128):
        sd = _scene(dead, "SDBRCK1", light, wall_h=72, slot=DEAD_SLOT)
        Image.fromarray(sd, "RGB").save(d / f"lineup_dead_{light}.png", optimize=True)
        out[f"dead_{light}"] = sd
    out["dead_labels"] = dlabels
    return out


def full_metrics(spr: dict) -> dict:
    info_path = FULL_DIR / SPRITE / "info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.is_file() else {}
    rotated, death = full_frames()
    m = {"lumps": len(full_plan()), "shell_lumps": len(SHELL_FRAMES),
         "front": measure(spr[("A", 1)]), "back": measure(spr[("A", 5)])}
    m["front_cloak_px"] = {f: info.get(f, {}).get("cloak_1") for f in rotated}
    m["cloak_px"] = {f: {r: info.get(f, {}).get(f"cloak_{r}") for r in range(1, 9)} for f in rotated}
    m["blood_share"] = {f: info.get(f, {}).get("blood") for f in death}
    m["heights"] = {full_lump(f, r): int(np.ptp(np.nonzero(spr[(f, r)][..., 3] > 0)[0]) + 1)
                    for f, r in full_plan()}
    m["corpse"] = corpse_metrics(death[-1])
    (FULL_DIR / SPRITE / "metrics.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    return m


# ---------------------------------------------------------------- the sheet
FULL_ROT_NAMES = {1: "front", 2: "front, his left", 3: "his left side", 4: "back, his left", 5: "back",
                  6: "back, his right", 7: "his right side", 8: "front, his right"}


def _crop_tiles(arrs: list[np.ndarray], zoom: int, caps: list[str], subs: list[str] | None = None) -> str:
    subs = subs or [""] * len(arrs)
    return _strip([core.sprite_tile(a, zoom, c, s) for a, c, s in zip(hound.crop_common(arrs), caps, subs)])


def _states_rows() -> list[list]:
    st = zs_states()
    rotated, _ = full_frames()
    rows = []
    for label, seq in st.items():
        if not seq:
            continue
        letters = "".join(dict.fromkeys(f for f, _ in seq))
        rows.append([label, " ".join(f"{f} {t}" for f, t in hound._gif_runs(seq)),
                     "1-8" if all(f in rotated for f in letters) else "0", letters])
    return rows


CODE_NEEDS = [
    "general.zs: rename CYBR to SDGN in every state line. The letters already match for A-P. The two Summon "
    "lines change their LETTERS too, as the file's comments say: 'CYBR E 15 Bright A_SD_GeneralSummon' "
    "becomes 'SDGN Q 15 Bright A_SD_GeneralSummon' and 'CYBR F 15' becomes 'SDGN R 15'.",
    "general_shell.zs: Spawn 'MANF AB 4 Bright' becomes 'SDGL AB 4 Bright'; Death 'MISL B 8 Bright', "
    "'MISL C 6 Bright', 'MISL D 4 Bright' become 'SDGL C 8 Bright', 'SDGL D 6 Bright', 'SDGL E 4 Bright' "
    "(new letters, BESTIARY 2.7). RenderStyle Add stays.",
    "Lumps: 81 SDGN (A-G, Q, R at rotations 1-8; H-P at 0) and 5 SDGL (A-E at 0), each PNG with its grAb, "
    "to assets/sprites/general/ on the CEO's approval; MOD-SPEC 6.3 and check_pk3's placeholder list lose "
    "CYBR, MANF and MISL for this class.",
    "Nothing else: no state, tic or action changes. The Q frame is Bright: GZDoom lights the WHOLE sprite on "
    "a Bright frame, which suits the order being shouted.",
]


def _full_verdict(met: dict, ident: dict) -> tuple[list[str], list[str]]:
    c = met["corpse"]
    same = [k for k, v in ident.items() if v]
    fc = met["front_cloak_px"]
    return [
        "WHAT THIS IS. D72: the CD turnaround, approved, drawn in every frame general.zs names: A-D the walk (the "
        "coat's hem and the cloak sway; Spawn idles on A B), E F the salvo (E aims the stick, F fires: the "
        "field gun's flash on his shoulder), G the pain (struck in the chest, he rocks back and clutches it), "
        "Q R the summon (Q, Bright: 'Vorwärts!', his fist raised; R: he points the recruits on), at 8 drawn "
        "rotations; H-P the death at rotation 0. 81 SDGN lumps and the shell's 5 SDGL. The turnaround's views "
        f"are its pixels byte for byte ({len(same)} of {len(ident)}: {', '.join(same) or 'turnaround PNGs not on disk'}).",
        "THE CLOAK FROM THE FRONT. At rotation 1 not one pixel of the cloak shows in any living frame: "
        + ", ".join(f"{f} {v}" for f, v in fc.items()) + " (tests/test_gen_general.py holds it). It sways only "
        "backwards and with the hem, never out past the coat.",
        "THE DEATH. Hit in the chest at H (the burst, the hole in the chrome), his knees go and the cap flies off "
        "at I (the field gun knocked up on its cradle), he falls back over his heels twisting at J while the gun "
        "is torn off, lands at K, and from L lies on his back across the screen on his cloak, spread under him "
        "on the floor: the Reich's red with its disc on the near side, the stars and stripes on the far side. "
        "Head, arms and legs are each let fall until they touch; the cap and the gun lie beside him; the pool "
        "grows from his chest onto the flags (M-P). "
        f"Measured on the corpse P (section 5): every part within {LYING_MAX:.0f} units of the floor, the body "
        f"{c['top']} units high at most (the test: under {LYING_TOP:.0f}; his cuirass is thick), the supports "
        f"spread {c['span']} units, the torso across the screen ({c['across']}); the cap and the gun lie "
        f"{c['loose_top']} units high at most. Blood is "
        + ", ".join(f"{k} {v:.0%}" for k, v in met["blood_share"].items() if v is not None)
        + " of the death frames' pixels.",
        "WHAT DOES NOT, HONESTLY. (1) E and F share the pose but for the stick and the flash: from the front "
        "E reads as 'F without the flash', which is Doom's own E/F rhythm (the Cyberdemon's). (2) The walk's "
        "four frames differ mostly in the legs under a coat that only sways: from the front the stride is "
        "boots; the side views show it. (3) Q's raised fist makes the sprite taller than his 100-unit actor "
        "(the arm over the cap), as Doom's raised arms do. (4) The corpse is big: he is 100 units, so lying he "
        "is ~100 px across, the cloak's fan wider still; it is the biggest corpse in the game, as he is the "
        "biggest man. (5) The spread cloak is drawn as straight stripes radiating from his shoulders: cloth "
        "seen from 37 degrees, not folds. (6) Light is gen_enemy's stand-in, NOT VERIFIED against GZDoom; "
        "nothing here has been in the engine.",
    ], [
        "Approve the 81 SDGN and 5 SDGL lumps as drawn, or name the frames to redo (the corpse P above all: "
        "does he lie naturally on his flags?).",
        "On approval: mod-engineer installs them and makes the code changes listed in section 8.",
    ]


def build_full_sheet(stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    spr = load_full()
    gifs = write_full_gifs(spr)
    lines = full_lineups(spr)
    met = full_metrics(spr)
    ident = full_identity(spr)
    rotated, death = full_frames()
    S = []
    body = sheetlib.table(["state", "frames and tics (general.zs; Summon with its final letters)", "rotations",
                           "letters"], _states_rows(), 9)
    body += (f"<p class=\"lead\">{len(full_plan())} SDGN lumps in <code>work/art/general/full/SDGN/</code> and "
             f"{len(SHELL_FRAMES)} SDGL in <code>.../SDGL/</code>, named as the engine reads them: "
             f"<code>SDGNA1</code> ... <code>SDGNR8</code>, <code>SDGNH0</code> ... <code>SDGNP0</code>, "
             "<code>SDGLA0</code> ... <code>SDGLE0</code>. Eight drawn rotations (handed). Each PNG carries its "
             "grAb. No XDeath state, so no gib.</p>")
    S.append(("1 · The set", "Every frame SD_General needs, read from general.zs (read, not edited).", body))
    body = _crop_tiles([spr[("A", r)] for r in range(1, 9)], 3, [full_lump("A", r) for r in range(1, 9)],
                       [FULL_ROT_NAMES[r] for r in range(1, 9)])
    body += _strip([core.sprite_tile(spr[("A", r)], 1, full_lump("A", r)) for r in range(1, 9)]
                   + [core.gif_tile(gifs["turntable"], 3, "turntable", "12 tics a rotation")])
    body += ("<p class=\"lead\">The turnaround's views, byte for byte: "
             + html.escape(", ".join(f"{k} {'identical' if v else ('differs' if v is False else 'no PNG')}"
                                     for k, v in ident.items())) + ".</p>")
    S.append(("2 · Turnaround: frame A at the 8 rotations", "3x on neutral grey, then 1x.", body))
    body = _strip([core.gif_tile(gifs[f"see_rot{r}"], 2, f"walk, rotation {r}", "A B C D, 6 tics each")
                   for r in range(1, 9)])
    body += _strip([core.gif_tile(gifs[f"attack_rot{r}"], 2, f"salvo, rotation {r}", "walk, E 6 F 12 E 12 F 12 E 12 F 12")
                    for r in (1, 3, 5, 7)])
    body += _strip([core.gif_tile(gifs[f"summon_rot{r}"], 2, f"summon, rotation {r}", "walk, Q 15 R 15, walk")
                    for r in (1, 3, 5, 7)])
    body += _strip([core.gif_tile(gifs[f"pain_rot{r}"], 2, f"pain, rotation {r}", "walk, G 10, walk")
                    for r in (1, 3, 5, 7)] + [core.gif_tile(gifs["spawn_rot1"], 2, "Spawn", "A B, 10 tics")])
    S.append(("3 · The cycles at game speed", "At the tics of general.zs, 35 a second: See SDGN AABBCCDD at 3 "
              "(6 a picture), Missile E 6 then F 12 / E 12 three times, Pain G 10, Summon Q 15 R 15, Spawn A B "
              "at 10.", body))
    body = ""
    for f in rotated:
        body += _crop_tiles([spr[(f, r)] for r in range(1, 9)], 2, [full_lump(f, r) for r in range(1, 9)],
                            [FULL_TITLES.get(f, "")] + [f"cloak {met['cloak_px'][f][r]} px" if r == 1 else ""
                                                        for r in range(2, 9)])
    S.append(("4 · Every living frame at every rotation", "2x, each row one frame letter. Under rotation 1: the "
              "cloak's pixels visible from the front (0 everywhere).", body))
    body = _crop_tiles([spr[(f, 0)] for f in death], 3, [f"SDGN{f}0" for f in death],
                       [FALLS[f].pose.title for f in death])
    body += _strip([core.gif_tile(gifs["death"], 3, "death, game speed", " ".join(
                        f"{f} {t}" for f, t in hound._gif_runs(zs_states()["Death"]))),
                    core.gif_tile(gifs["death_floor"], 1, "in the portal hall, 1x", "from the living frame"),
                    core.gif_tile(gifs["death_floor"], 2, "in the portal hall, 2x"),
                    core.sprite_tile(hound.crop_common([spr[("P", 0)]])[0], 4, "SDGNP0 at 4x", "the corpse")])
    c = met["corpse"]
    body += sheetlib.table(["part of SDGNP0", "lowest point above the floor (units)"],
                           [[k, v] for k, v in c["lowest"].items()], 1)
    body += (f"<p class=\"lead\">The corpse measured on its model, untilted: each part within {LYING_MAX:.0f} "
             f"units of the floor, his highest point {c['top']} units (under {LYING_TOP:.0f}), the parts on the "
             f"floor spread {c['span']} units, the torso across the screen ({c['across']}); the cap and the gun "
             f"lie on the floor ({c['loose_lowest']} to {c['loose_top']} units). tests/test_gen_general.py holds "
             "it. Blood, share of the death frames' pixels: "
             + ", ".join(f"{k} {v:.0%}" for k, v in met["blood_share"].items() if v is not None) + ".</p>")
    S.append(("5 · The death, rotation 0, with the blood",
              "Dark red only, flag_red 0-5 and black (D49, BloodColor AD 27 21's family). The frames on the "
              "floor are seen from higher as they fall (up to 37 degrees, as the approved corpses).", body))
    shell = [spr[("shell", f)] for f in SHELL_FRAMES]
    body = _strip([core.sprite_tile(a, 4, f"SDGL{f}0", t) for a, f, t in
                   zip(shell, SHELL_FRAMES, ("flight", "flight", "burst", "burst", "burst"))]
                  + [core.gif_tile(gifs["shell_flight"], 4, "flight, additive on SDBRCK1", "A B, 4 tics"),
                     core.gif_tile(gifs["shell_burst"], 4, "burst, additive", "C 8, D 6, E 4")])
    S.append(("6 · The shell SD_GeneralShell (SDGL A-E)", "A white-hot core in a braid-yellow fire with an ember "
              "ring, flying at you (A B), then the burst (C D E). RenderStyle Add in general_shell.zs: only "
              "bright colours count; the additive preview is a stand-in, NOT VERIFIED.", body))
    body = ""
    for sk, (sc, wall, light, what) in lines["scenes"].items():
        body += _strip([_img_tile(sc, 1, f"{sk} 1x: {wall} at light {light}", what),
                        _img_tile(sc, 2, f"{sk} 2x, for the eye")])
    body += ('<p class="lead">Left to right: ' + html.escape(" · ".join(lines["labels"])) + ".</p>")
    for light in (176, 128):
        sd = lines[f"dead_{light}"]
        body += _strip([_img_tile(sd, 1, f"the dead, 1x, SDBRCK1 at {light}"), _img_tile(sd, 2, "2x")])
    body += '<p class="lead">The dead: ' + html.escape(" · ".join(lines["dead_labels"])) + ".</p>"
    S.append(("7 · At 1x in MAP03: the portal hall and a corridor, beside the approved enemies",
              "The portal hall's brick at 128 and the drum's steel at 144 over SDFLR4; the office corridor's "
              "SDTILE2 at 128 over SDFLR3. Light is gen_enemy's stand-in re-quantised to palette v2, NOT VERIFIED.",
              body))
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(x)}</p>" for x in CODE_NEEDS) + "</div>"
    S.append(("8 · What the code needs (for mod-engineer; nothing is edited here)", "", body))
    fm, bm = met["front"], met["back"]
    rows = [["front A1", f"{fm['height_px']} x {fm['width_px']}", fm["body_luma"], fm["worst_sep"]],
            ["back A5", f"{bm['height_px']} x {bm['width_px']}", bm["body_luma"], bm["worst_sep"]]]
    body = sheetlib.table(["view", "h x w px", "body luma", "worst share apart"], rows, 2)
    body += sheetlib.table(["lump", "height px"], [[k, v] for k, v in met["heights"].items()
                                                   if k[5] in "150"], 1)
    S.append(("9 · Numbers", "Size and value as the sweep measured them; the heights at rotations 1, 5 and 0.", body))
    verdict, ask = _full_verdict(met, ident)
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in verdict) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in ask) + "</ol></div>"
    S.append(("10 · Honest verdict and what you decide", "", body))
    intro = ("D72: \"OK al general\". The CD turnaround in every frame his states name, rendered on the rig the "
             "approved enemies were drawn on, with D49's dark red blood and a corpse that lies flat on his flags. "
             "Built by <code>tools/art/gen_general.py --full</code> on rig_core (imported, not edited), seed "
             f"{SEED}, no system fonts. Draft: nothing in <code>assets/</code> or <code>src/</code>.")
    footer = ("Sprites: tools/art/gen_general.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic. Approved "
              "sprites read from assets/sprites/ for scale. MAP03 walls and flats are the mod's own. Freedoom's "
              "CYBRA1 shown for scale only (BSD-3-Clause), not used as a source.")
    path = out_dir / f"{stamp}_F5_general-CD-full-set.html"
    sheetlib.write_sheet(path, lang="en", title="The General, CD: full set (F5, D72)",
                         subtitle=f"SDGN · SDGL · {len(full_plan())} + {len(SHELL_FRAMES)} lumps · 8 rotations · "
                                  "death with blood · draft", intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    Image.fromarray(full_contact(spr, lines), "RGB").save(path.with_suffix(".png"), optimize=True)
    return path


def full_contact(spr: dict, lines: dict) -> np.ndarray:
    """Each living frame a row of its 8 rotations at 1x (cropped alike), then
    the death H-P and the shell at 1x, then the portal hall lineup and the
    dead at 1x."""
    gap = 8
    rotated, death = full_frames()
    rows = [hound.crop_common([spr[(f, r)] for r in range(1, 9)]) for f in rotated]
    drow = hound.crop_common([spr[(f, 0)] for f in death])
    srow = [spr[("shell", f)] for f in SHELL_FRAMES]
    scenes = [lines["scenes"]["P1"][0], lines["dead_128"]]
    width = max(max(sum(a.shape[1] + gap for a in r) for r in rows + [drow, srow]),
                max(s.shape[1] for s in scenes)) + 2 * gap
    height = gap + sum(max(a.shape[0] for a in r) + gap for r in rows + [drow, srow]) \
        + sum(s.shape[0] + gap for s in scenes) + gap
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = CONTACT_BG
    y = gap
    for r in rows + [drow, srow]:
        x = gap
        h = max(a.shape[0] for a in r)
        for a in r:
            canvas[y:y + a.shape[0], x:x + a.shape[1]] = core.NEUTRAL
            _paste(canvas, a, x, y, 1)
            x += a.shape[1] + gap
        y += h + gap
    for s in scenes:
        _paste(canvas, s, gap, y, 1)
        y += s.shape[0] + gap
    return canvas


# ===================================================================== main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=None, help="sheet timestamp YYYY-MM-DD_HHMM (default: now)")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--only", default=None, help="cell letters to render (no sheet)")
    ap.add_argument("--turnaround", action="store_true", help="D71: cell CD turned round, and its sheet")
    ap.add_argument("--full", action="store_true", help="D72: the full set SDGN + SDGL into work/art/general/full/")
    ap.add_argument("--jobs", type=int, default=1, help="with --full: worker processes")
    ap.add_argument("--frames", default="", help="with --full: frame letters to render only (no sheet), e.g. P or AQ")
    ap.add_argument("--sheet-only", action="store_true", help="with --full: GIFs, lineups and sheet from the lumps on disk")
    args = ap.parse_args(argv)
    if args.full:
        only = set(args.frames) or None
        if not args.sheet_only:
            build_full(jobs=args.jobs, only=only)
        if only or args.no_sheet:
            return 0
        stamp = args.stamp or dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        print(build_full_sheet(stamp))
        return 0
    if args.turnaround:
        t = build_turnaround()
        print(json.dumps(t["metrics"], indent=2))
        if not args.no_sheet:
            stamp = args.stamp or dt.datetime.now().strftime("%Y-%m-%d_%H%M")
            print(build_turnaround_sheet(t, stamp))
        return 0
    data = build_all(keys=args.only)
    if args.only:
        return 0
    lines = write_lineups(data)
    print(json.dumps(data["metrics"], indent=2))
    if not args.no_sheet:
        stamp = args.stamp or dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        print(build_sheet(data, lines, stamp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
