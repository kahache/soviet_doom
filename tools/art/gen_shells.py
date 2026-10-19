"""F5 — the two enemy shells still on Freedoom: SDDL and SDPL (backlog M2b, audit B4).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_shells.py                 (Windows)
    .venv/bin/python tools/art/gen_shells.py                         (macOS)
    ... gen_shells.py --stamp 2026-10-19_2300    fixes the sheet's timestamp
    ... gen_shells.py --no-sheet                 sprites, scenes and metrics only
    ... gen_shells.py --sweep-only               the six options, no full set, no sheet

What this is. Every enemy draws our own sprites since D73, but two
projectiles still wear Freedoom's: SD_DoughboyShell flies on BAL2 (the
Cacodemon's ball) and SD_PanzerShell, thrown by the Panzermensch and the
Schwer alike, on BAL7 (the Baron's). Their final names are reserved in
BESTIARY §2.7 and MOD-SPEC §6.3: SDDL and SDPL. This generator draws them
on the rig the approved enemies were drawn on, the way SDBL (the storm
bolt, gen_storm.py) and SDGL (the General's shell, gen_general.py) were:
rotation 0, A-B in flight, C-E the burst, every material flat (a glow has
no contour and no rim), RenderStyle "Add" in the engine (only bright
colours count; black adds nothing).

(Not tools/art/gen_shell.py: that one draws the game's SHELL, the title
and intermission screens. This one draws two projectiles.)

The briefs (BESTIARY §7, §8):
  SDDL  "steel_blue white-hot core with a flag_red trail"; it must not read
        as the Stormtrooper's bolt (chrome-white with a red core, SDBL),
        because the right reaction to each differs (dodge sideways vs.
        break line of sight).
  SDPL  "dull hazard_yellow core with an olive smoke edge; Reich ordnance,
        visually heavier and slower-tumbling than the Stormtrooper bolt".
Both are already drawn, small, in approved frames: the Doughboy's attack
(SDDB B C D, the shell kindling in the throat and leaving the mouth:
gen_heavy's sdl_core / sdl_trail) and the Panzermensch's and the Schwer's
(SDPM / SDPS E F G, the shell forming in the right gauntlet and thrown:
gen_heavy's pzl_core / pzl_shell / pzl_smoke). Option A of each sweep IS
that drawing at flight size, its materials imported from gen_heavy, not
copied: an option that changes the colours or the object also asks for
those attack frames to be redrawn (named in the sheet).

The sweep (PIPELINE stage 2): three options per shell, each shown by its
flight frame A and its first burst frame C. A is the brief; B and C change
the object, nothing else (size, timing, letters and RenderStyle stay):

  SDDL  A  comet      the brief: a white-hot steel_blue core in a flag_red
                      corona, a flame tongue that flickers left and right
        B  roundel    the Legion's insignia family (D12): a white star on a
                      cobalt disc in a red ring, spinning 36 degrees a frame
        C  spit       a gob of flesh_pink bile round the white-hot core, red
                      strands, drops trailing: the head spits it
  SDPL  A  ember      the brief: a dull yellow ball in an olive smoke halo,
                      its hot core tumbling round the centre
        B  grenade    a red-hot Stielhandgranate (the Reich's iconic
                      ordnance), tumbling end over end, its fuse sparking
        C  slag       a gout of molten iron from Tankograd's foundry,
                      black crust plates on it (holes, additively)

Each option's full set (A-E) is rendered for the RECOMMENDED one, so the
CEO's yes is an install, not another round.

Geometry. The engine places a rotation-0 sprite by its grAb: x the centre,
y how far the top sits above the actor's z. Freedoom's balls hang their
centre about half the actor's Height above z (BAL2A0: top 12 of 15, Height
8; BAL7A1A5: top 18 of 20, Height 16), so the collision box and the glow
coincide; ours do the same, from the Height read in each .zs. (SDBL and
SDGL are centred on z instead; four and eight px of difference, noted.)
Scale is the rig's, 1 px a unit, as every approved enemy.

The scenes. Each shell at 1x in flight, added onto MAP03's walls at the
light stand-in (RGB x L/224, NOT VERIFIED against GZDoom's light or its
additive blend), next to the approved enemy that throws it in its firing
frame, and the Freedoom placeholder it replaces for comparison (scale only,
BSD-3, read from iwads/ when present). The shell's spawn height is the
enemy's z plus 32 (Doom's P_SpawnMissile, "4*8*FRACUNIT", from memory: NOT
VERIFIED here); the Doughboy hangs gen_heavy.HOVER above the floor.

NO FONTS. Sprites carry no text; the sheet is HTML (sheetlib); the PNG
contact sheet has no letters. Nothing is written under assets/ or src/.

Outputs (work/ is gitignored):
    work/art/shells/sweep/<SPRITE>_<option>_<frame>0.png   the six options' A and C
    work/art/shells/<SPRITE>/<SPRITE><frame>0.png          the recommended full sets, grAb
    work/art/shells/<SPRITE>/*.gif, scene_*.png, metrics.json
    docs/art/previews/<stamp>_F5_enemy-shells.html (+ .png)
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
if str(ART_TOOLS) not in sys.path:
    sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (scene bands, tile_to, the IWAD path)
import gen_heavy as heavy  # noqa: E402  (palette v2, HOVER, the attack frames' shell materials)
import gen_legion as legion  # noqa: E402  (registers flesh_pink with the rig)
import palette as palgen  # noqa: E402
import rig_core as core  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "shells"
SWEEP_DIR = OUT_DIR / "sweep"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
ASSETS = PROJECT_ROOT / "assets"
MONSTERS = PROJECT_ROOT / "src" / "zscript" / "monsters"

SEED = 2104                     # the rig's grain seed (unused by flat glows, fixed anyway)
V = core.V
Mat = core.Mat
E = core.ellipsoid
FLESH = legion.FLESH            # palette v2 flesh_pink (D45)
COBALT = "mosaic_cobalt"        # palette v2 (D45): a true blue, not steel_blue's grey-blue
core.register_ramp(COBALT, palgen.ramp_colours(COBALT))

FLIGHT = "AB"                   # Spawn: A B 4 Bright, Loop (both .zs)
BURST = "CDE"                   # Death: C D E 6 Bright, Stop
FRAMES = FLIGHT + BURST
SWEEP_FRAMES = "AC"             # the sweep shows the flight frame and the first burst frame
SPAWN_HEIGHT = 32               # Doom's P_SpawnMissile: z + 4*8 (from memory: NOT VERIFIED)
SCENE_WALL_H = 128              # a wall taller than the floater's shell
SCENE_SLOT = 72
ZOOM_OPTION = 3                 # the brief: options at 3x
SCENE_ZOOM = 3                  # the 1x scene, blown up once more beside it for the eye
CONTACT_BG = (20, 21, 24)
HOLD_MS = 600                   # a GIF's pause between bursts


# ================================================================ the two shells
@dataclass(frozen=True)
class Shell:
    key: str                    # "doughboy" | "panzer"
    sprite: str                 # the final name reserved in BESTIARY §2.7
    cls: str                    # the ZScript class
    zs: Path
    placeholder: str            # the Freedoom sprite it replaces
    canvas: core.Canvas
    thrower: tuple[str, ...]    # approved firing frames of the enemies that throw it (assets/sprites/...)
    thrower_z: int              # px above the floor of the thrower's z
    wall: str                   # the MAP03 wall it is seen against (docs/levels/MAP03-factory.md)
    light: int
    where: str


def zs_states(path: Path) -> dict[str, list[tuple[str, str, int]]]:
    """The class's state labels and their (sprite, frame letter, tics), in order."""
    out: dict[str, list[tuple[str, str, int]]] = {}
    label, in_states = None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.split("//")[0].rstrip()
        if s.strip() == "States":
            in_states = True
            continue
        if not in_states:
            continue
        m = re.match(r"^\s*([A-Za-z]+):\s*$", s)
        if m:
            label = m.group(1)
            out[label] = []
            continue
        m = re.match(r"^\s*([A-Z0-9]{4})\s+([A-Z]+)\s+(-?\d+)\b", s)
        if m and label:
            out[label] += [(m.group(1), ch, int(m.group(3))) for ch in m.group(2)]
    return out


def zs_const(path: Path, suffix: str) -> int:
    """`const SD_..._<suffix> = n;` from the class file."""
    m = re.search(rf"const\s+SD_\w+_{suffix}\s*=\s*(\d+)\s*;", path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"{path.name}: no {suffix} constant")
    return int(m.group(1))


def shell_canvas(size: int, height: int) -> core.Canvas:
    """A square canvas whose centre hangs height/2 above the actor's z:
    grAb y = size/2 + height/2 = foot_row - FEET_SINK."""
    return core.Canvas(size, size, size // 2, size // 2 + height // 2 + core.FEET_SINK)


DOUGHBOY_ZS = MONSTERS / "doughboy_shell.zs"
PANZER_ZS = MONSTERS / "panzer_shell.zs"
SHELLS: dict[str, Shell] = {
    "doughboy": Shell("doughboy", "SDDL", "SD_DoughboyShell", DOUGHBOY_ZS, "BAL2",
                      shell_canvas(48, zs_const(DOUGHBOY_ZS, "HEIGHT")),
                      ("doughboy/SDDBD1",), heavy.HOVER, "SDBRCK1", 128,
                      "the foundry's brick, where MAP03 hangs its Doughboys"),
    "panzer": Shell("panzer", "SDPL", "SD_PanzerShell", PANZER_ZS, "BAL7",
                    shell_canvas(56, zs_const(PANZER_ZS, "HEIGHT")),
                    ("panzermensch/SDPMG1", "panzermensch/SDPSG1"), 0, "SDRUST1", 128,
                    "the tank line's corrugated rust, where the Panzermensch and the Schwer stand"),
}
FLOOR = "SDFLR4"                # MAP03's cast-iron floor (foundry gallery, tank line)


def centre_y(sh: Shell) -> float:
    """Model height that projects to the canvas centre (as gen_general's SHELL_Y)."""
    return float(sh.canvas.foot_row - sh.canvas.h // 2)


# ================================================================ materials
# One table for both shells. Option A's materials are gen_heavy's own (the
# approved attack frames' shell), the same objects; the rest are new, flat.
M = Mat.on_ramp
SHELL_NEW: dict[str, Mat] = {
    # SDDL (Legion)
    "sdl_core": heavy.DB_NEW["sdl_core"],                     # steel_blue 13-15 + white
    "sdl_trail": heavy.DB_NEW["sdl_trail"],                   # flag_red 6-12
    "sdl_dim": M("steel_blue", 6, 12, shift=False, flat=True),
    "sdl_trail_dim": M("flag_red", 2, 8, shift=False, flat=True),
    "sdl_disc": M(COBALT, 7, 14, shift=False, flat=True),
    "sdl_disc_dim": M(COBALT, 3, 9, shift=False, flat=True),
    "sdl_star": Mat((("plaster_warm", 14, 15), ("white",)), shift=False, flat=True),
    "sdl_ring": M("flag_red", 8, 13, shift=False, flat=True),
    "sdl_gob": M(FLESH, 8, 15, shift=False, flat=True),
    "sdl_gob_red": M("flag_red", 5, 11, shift=False, flat=True),
    "sdl_gob_dim": M(FLESH, 3, 9, shift=False, flat=True),
    # SDPL (Reich)
    "pzl_core": heavy.PM_NEW["pzl_core"],                     # cream_yellow 13-15
    "pzl_shell": heavy.PM_NEW["pzl_shell"],                   # hazard_yellow 6-12
    "pzl_smoke": heavy.PM_NEW["pzl_smoke"],                   # khaki_olive 3-8
    "pzl_dim": M("hazard_yellow", 3, 9, shift=False, flat=True),
    "pzl_smoke_dim": M("khaki_olive", 1, 5, shift=False, flat=True),
    "pzl_head": M("hazard_yellow", 7, 14, shift=False, flat=True),
    "pzl_handle": M("rust_brown", 5, 11, shift=False, flat=True),
    "pzl_spark": Mat((("cream_yellow", 13, 15), ("white",)), shift=False, flat=True),
    "pzl_slag": M("rust_brown", 8, 15, shift=False, flat=True),
    "pzl_slag_hot": M("hazard_yellow", 10, 15, shift=False, flat=True),
    "pzl_slag_dim": M("rust_brown", 3, 9, shift=False, flat=True),
    "pzl_crust": Mat((("black",), ("rust_brown", 0, 1)), shift=False, flat=True),
}
MATERIALS: dict[str, Mat] = {}
for _n, _m in SHELL_NEW.items():
    core.register_material(_n, _m, MATERIALS)
LEGION_FORBIDDEN = {"khaki_olive", "military_green"}         # ART-BIBLE §6.2: the Reich's and the world's
REICH_FORBIDDEN = {"military_green", FLESH, "steel_blue"}    # the world's; the Legion's flesh and chrome


def _polar(r: float, deg: float, z: float = 0.0) -> np.ndarray:
    q = np.deg2rad(deg)
    return V(r * np.cos(q), r * np.sin(q), z)


def _ring(mat: str, base: float, c: np.ndarray, n: int, rad: float, size: float, phase: float = 0.0,
          z: float = 1.5, sag: float = 0.0) -> list[core.Prim]:
    """n embers on a circle (sag: each falls this far, a late burst)."""
    return [E(mat, base, tuple(c + _polar(rad, 360.0 * (i + phase) / n, z) - V(0, sag, 0)), (size,) * 3)
            for i in range(n)]


def _streak(mat: str, base: float, c: np.ndarray, rad: float, deg: float, length: float, r1: float,
            r2: float, z: float = 1.0) -> core.Prim:
    """A drop thrown outward: a round cone from rad to rad+length along deg."""
    return core.rcone(mat, base, tuple(c + _polar(rad, deg, z)), tuple(c + _polar(rad + length, deg, z)), r1, r2)


# ---------------------------------------------------------------- SDDL options
def sdl_comet(frame: str, c: np.ndarray) -> list[core.Prim]:
    """A (the brief, as the attack frame draws it): a white-hot steel_blue core
    in a flag_red corona; a flame tongue rising off it flickers left (A) and
    right (B). Red OUTSIDE white: the storm bolt is the reverse."""
    if frame in FLIGHT:
        s = -1.0 if frame == "A" else 1.0
        return [E("sdl_trail", 0.62, tuple(c), (6.4, 6.0, 3.0)),
                E("sdl_trail", 0.52, tuple(c + V(1.8 * s, 5.0, -1.2)), (3.0, 4.6, 2.0)),
                E("sdl_trail", 0.48, tuple(c + V(-2.6 * s, 6.6, -1.6)), (1.6, 2.2, 1.4)),
                E("sdl_core", 0.86, tuple(c + V(0.0, -0.6, 2.4)), (3.6, 3.4, 2.0))]
    step = BURST.index(frame)
    P: list[core.Prim] = []
    if step == 0:
        P += [E("sdl_trail", 0.62, tuple(c), (8.2,) * 3), E("sdl_core", 0.86, tuple(c + V(0, 0, 4.0)), (5.6,) * 3)]
    elif step == 1:
        P += [E("sdl_trail_dim", 0.62, tuple(c), (10.0,) * 3), E("sdl_dim", 0.8, tuple(c + V(0, 0, 4.0)), (4.2,) * 3)]
    P += _ring("sdl_trail" if step < 2 else "sdl_trail_dim", 0.7, c, 8 + 2 * step, 10.0 + 3.0 * step,
               1.7 - 0.3 * step, 0.5 * step, sag=1.5 * step)
    if step < 2:
        P += _ring("sdl_core" if step == 0 else "sdl_dim", 0.8, c, 5, 6.0 + 4.0 * step, 1.1, 0.25)
    return P


def _star(c: np.ndarray, spin: float, r_out: float, mat: str = "sdl_star", z: float = 2.2) -> list[core.Prim]:
    """A five-pointed star of round cones from its centre, flattened to the viewer."""
    P = [E(mat, 0.9, tuple(c + V(0, 0, z)), (2.1, 2.1, 1.0))]
    for k in range(5):
        P.append(core.rcone(mat, 0.9, tuple(c + V(0, 0, z)), tuple(c + _polar(r_out, 90.0 + 72.0 * k + spin, z)),
                            1.55, 0.35))
    return P


def sdl_roundel(frame: str, c: np.ndarray) -> list[core.Prim]:
    """B: the US roundel's family (D12, the Legion's insignia): a white star on
    a cobalt disc in a red ring; it spins 36 degrees a frame (A upright, B
    inverted). Burst: the star's five points fly apart."""
    if frame in FLIGHT:
        spin = 0.0 if frame == "A" else 36.0
        return ([E("sdl_ring", 0.68, tuple(c), (8.0, 8.0, 1.4)),
                 E("sdl_disc", 0.66, tuple(c + V(0, 0, 0.9)), (6.4, 6.4, 1.4))]
                + _star(c, spin, 5.8))
    step = BURST.index(frame)
    P: list[core.Prim] = []
    if step == 0:
        P += [E("sdl_disc", 0.66, tuple(c), (8.6,) * 3), E("sdl_star", 0.9, tuple(c + V(0, 0, 4.0)), (4.4,) * 3)]
    elif step == 1:
        P += [E("sdl_disc_dim", 0.66, tuple(c), (10.0,) * 3)]
    for k in range(5):                                       # the points, flying out and tumbling
        deg = 90.0 + 72.0 * k + 12.0 * step
        rad = 6.0 + 4.0 * step
        P.append(_streak("sdl_star" if step < 2 else "sdl_dim", 0.9, c, rad, deg + 8.0 * step,
                         3.6 - 0.6 * step, 1.3 - 0.2 * step, 0.3, z=2.5))
    P += _ring("sdl_ring" if step < 2 else "sdl_trail_dim", 0.7, c, 10 + 2 * step, 10.5 + 3.0 * step,
               1.4 - 0.2 * step, 0.5, sag=1.5 * step)
    return P


def sdl_spit(frame: str, c: np.ndarray) -> list[core.Prim]:
    """C: the head spits it. A gob of flesh_pink bile round the white-hot core,
    a red strand, two drops trailing; it wobbles (A / B)."""
    if frame in FLIGHT:
        s = -1.0 if frame == "A" else 1.0
        return [E("sdl_gob", 0.62, tuple(c), (5.6 - 0.3 * s, 5.0 + 0.3 * s, 3.2)),
                E("sdl_gob", 0.58, tuple(c + V(3.4 * s, 2.6, -0.4)), (2.8, 2.4, 2.0)),
                E("sdl_gob", 0.56, tuple(c + V(-3.0 * s, -3.4, -0.2)), (2.4, 2.6, 1.8)),
                E("sdl_gob_red", 0.62, tuple(c + V(-2.2 * s, 1.8, 1.6)), (2.6, 1.4, 1.2)),
                E("sdl_gob", 0.55, tuple(c + V(5.8 * s, 6.4, -1.0)), (1.4, 1.4, 1.2)),
                E("sdl_gob_red", 0.55, tuple(c + V(-6.6 * s, 3.8, -1.0)), (1.1, 1.1, 1.0)),
                E("sdl_core", 0.86, tuple(c + V(0.4 * s, -0.4, 2.8)), (2.4, 2.2, 1.4))]
    step = BURST.index(frame)
    P: list[core.Prim] = []
    if step == 0:
        P += [E("sdl_gob", 0.62, tuple(c), (7.4, 6.4, 3.0)), E("sdl_core", 0.86, tuple(c + V(0, 0, 3.2)), (3.6,) * 3)]
    elif step == 1:
        P += [E("sdl_gob_dim", 0.6, tuple(c - V(0, 2.0, 0)), (8.6, 5.4, 3.0))]
    n = 9
    for i in range(n):                                       # splashes thrown out, falling as they go
        deg = 360.0 * (i + 0.37 * step) / n + (17.0 if i % 2 else 0.0)
        rad = 7.0 + 4.0 * step
        mat = ("sdl_gob" if i % 3 else "sdl_gob_red") if step < 2 else ("sdl_gob_dim" if i % 3 else "sdl_trail_dim")
        P.append(_streak(mat, 0.62, c - V(0, 2.0 * step * step / 2, 0), rad, deg, 3.4 - 0.4 * step,
                         1.5 - 0.25 * step, 0.6))
    return P


# ---------------------------------------------------------------- SDPL options
def pzl_ember(frame: str, c: np.ndarray) -> list[core.Prim]:
    """A (the brief, as the gauntlet holds it): a dull yellow ball in an olive
    smoke halo; the hot core and two smoke lobes turn a quarter round the
    centre a frame: it tumbles, heavier and slower than the bolt."""
    if frame in FLIGHT:
        a = 0.0 if frame == "A" else 1.0
        P = [E("pzl_smoke", 0.56, tuple(c), (8.6, 8.0, 3.0)),
             E("pzl_shell", 0.62, tuple(c + V(0, 0, 1.6)), (5.6, 5.8, 2.8)),
             E("pzl_core", 0.82, tuple(c + _polar(1.4, 135.0 + 90.0 * a, 3.4)), (2.6, 2.7, 1.4))]
        for ang in ((30.0, 210.0) if frame == "A" else (120.0, 300.0)):
            P.append(E("pzl_smoke", 0.5, tuple(c + _polar(8.4, ang, -0.6)), (3.6, 3.4, 2.4)))
        return P
    step = BURST.index(frame)
    P = []
    if step == 0:
        P += [E("pzl_shell", 0.62, tuple(c), (10.0,) * 3), E("pzl_core", 0.84, tuple(c + V(0, 0, 4.6)), (5.0,) * 3)]
    elif step == 1:
        P += [E("pzl_dim", 0.62, tuple(c), (12.0, 11.0, 3.0)), E("pzl_shell", 0.62, tuple(c + V(0, 0, 3.0)), (4.4,) * 3)]
    P += _ring("pzl_smoke" if step < 2 else "pzl_smoke_dim", 0.55, c + V(0, 1.0 * step, 0), 8 + step,
               12.0 + 3.2 * step, 3.2 + 0.6 * step, 0.5 * step, z=-0.5)
    if step < 2:
        P += _ring("pzl_core" if step == 0 else "pzl_dim", 0.82, c, 6, 7.0 + 5.0 * step, 1.2, 0.33, z=2.5)
    return P


def pzl_grenade(frame: str, c: np.ndarray) -> list[core.Prim]:
    """B: a red-hot Stielhandgranate, the Reich's iconic ordnance: the hot
    head, the glowing handle, the fuse sparking at its end; A and B are
    90 degrees apart, end over end. Burst: a yellow flash, olive smoke and
    the handle's splinters."""
    if frame in FLIGHT:
        ang = 35.0 if frame == "A" else -55.0
        u = _polar(1.0, ang)
        head = c + u * 4.6
        tail = c - u * 9.6
        return [E("pzl_smoke", 0.5, tuple(tail - u * 2.6 + V(0, 0, -1.6)), (4.0, 3.6, 2.4)),
                core.rcone("pzl_handle", 0.62, tuple(c + u * 1.2), tuple(tail), 1.6, 1.4),
                core.rcone("pzl_head", 0.66, tuple(head - u * 2.6), tuple(head + u * 2.6), 3.6, 3.6),
                E("pzl_spark", 0.88, tuple(tail - u * 1.4 + V(0, 0, 1.2)), (1.6, 1.6, 1.2))]
    step = BURST.index(frame)
    P = []
    if step == 0:
        P += [E("pzl_head", 0.66, tuple(c), (9.6,) * 3), E("pzl_spark", 0.88, tuple(c + V(0, 0, 4.4)), (4.6,) * 3)]
    elif step == 1:
        P += [E("pzl_dim", 0.62, tuple(c), (11.0, 10.4, 3.0))]
    P += _ring("pzl_smoke" if step < 2 else "pzl_smoke_dim", 0.55, c + V(0, 1.2 * step, 0), 9,
               11.0 + 3.6 * step, 3.0 + 0.6 * step, 0.2 + 0.5 * step, z=-0.5)
    for k in range(4):                                       # the handle's splinters
        deg = 70.0 + 90.0 * k + 25.0 * step
        P.append(_streak("pzl_handle" if step < 2 else "pzl_slag_dim", 0.62, c - V(0, 1.5 * step, 0),
                         8.0 + 5.0 * step, deg, 3.4, 0.9, 0.6, z=2.0))
    return P


def pzl_slag(frame: str, c: np.ndarray) -> list[core.Prim]:
    """C: a gout of molten iron from Tankograd's foundry (MAP03's SDMOLT
    channel): a hot lump of three lobes with black crust plates on it, which
    the additive blend turns into holes; it turns half round a frame.
    Burst: molten drops thrown out and falling."""
    if frame in FLIGHT:
        s = 1.0 if frame == "A" else -1.0
        return [E("pzl_smoke", 0.5, tuple(c + V(-1.0 * s, 4.6, -2.4)), (5.2, 4.4, 2.0)),
                E("pzl_slag_hot", 0.74, tuple(c), (4.8, 4.4, 3.2)),
                E("pzl_slag", 0.66, tuple(c + V(3.2 * s, 1.8, 0.0)), (3.8, 3.2, 2.8)),
                E("pzl_slag", 0.62, tuple(c + V(-3.2 * s, -1.8, 0.4)), (3.4, 3.6, 2.6)),
                E("pzl_crust", 0.4, tuple(c + V(1.6 * s, -2.6, 2.7)), (2.4, 1.5, 0.8)),
                E("pzl_crust", 0.4, tuple(c + V(-2.2 * s, 2.6, 2.6)), (2.0, 1.3, 0.8)),
                E("pzl_slag", 0.62, tuple(c + V(4.8 * s, -5.4, -0.6)), (1.4, 1.8, 1.2)),
                E("pzl_slag_dim", 0.62, tuple(c + V(-5.6 * s, -6.4, -0.8)), (1.0, 1.3, 1.0))]
    step = BURST.index(frame)
    P = []
    if step == 0:
        P += [E("pzl_slag_hot", 0.74, tuple(c), (8.0, 7.2, 3.0)), E("pzl_spark", 0.88, tuple(c + V(0, 0, 3.6)), (3.4,) * 3)]
    elif step == 1:
        P += [E("pzl_slag", 0.6, tuple(c - V(0, 2.0, 0)), (9.6, 6.0, 3.0))]
    n = 10
    for i in range(n):
        deg = 360.0 * (i + 0.31 * step) / n + (14.0 if i % 2 else 0.0)
        mat = ("pzl_slag_hot" if i % 3 == 0 else "pzl_slag") if step < 2 else "pzl_slag_dim"
        P.append(_streak(mat, 0.66, c - V(0, 2.2 * step * step / 2, 0), 7.5 + 4.6 * step, deg,
                         3.8 - 0.5 * step, 1.6 - 0.25 * step, 0.6))
    P += _ring("pzl_smoke" if step < 2 else "pzl_smoke_dim", 0.5, c + V(0, 2.0 + 1.5 * step, 0), 5,
               7.0 + 3.0 * step, 3.0, 0.1, z=-1.5)
    return P


@dataclass(frozen=True)
class Option:
    key: str                    # "A" | "B" | "C"
    name: str
    model: Callable[[str, np.ndarray], list[core.Prim]]
    what: str
    install: str                # what choosing it costs beyond the five lumps


OPTIONS: dict[str, dict[str, Option]] = {
    "doughboy": {
        "A": Option("A", "comet", sdl_comet,
                    "The brief: a white-hot steel_blue core in a flag_red corona, a flame tongue flickering left "
                    "and right. The same two materials the approved SDDB B-D frames show in the mouth.",
                    "nothing else: the Doughboy's attack frames already draw this shell"),
        "B": Option("B", "roundel", sdl_roundel,
                    "The Legion's insignia family (D12): a white star on a cobalt disc in a red ring, spinning 36 "
                    "degrees a frame; the burst throws the five points apart.",
                    "an insignia on a projectile is the CEO's call (ART-BIBLE §6.3 keeps red-white-blue for the "
                    "flags); the mouth glow of SDDB B-D (24 lumps) reads as a plain blue-white spark, acceptable "
                    "as is or redrawn"),
        "C": Option("C", "spit", sdl_spit,
                    "The head spits it: a gob of flesh_pink bile round the white-hot core, a red strand, drops "
                    "trailing. Grotesque, not funny (D11).",
                    "redraw the mouth of SDDB B-D (24 lumps) with pink bile, or the spit leaves a blue mouth"),
    },
    "panzer": {
        "A": Option("A", "ember", pzl_ember,
                    "The brief: a dull hazard_yellow ball in an olive smoke halo, its hot core tumbling round the "
                    "centre. The same three materials the approved SDPM / SDPS E-G frames hold in the gauntlet.",
                    "nothing else: the Panzermensch's and the Schwer's attack frames already draw this shell"),
        "B": Option("B", "grenade", pzl_grenade,
                    "A red-hot Stielhandgranate, the Reich's iconic ordnance, tumbling end over end with its fuse "
                    "sparking; the burst throws the handle's splinters.",
                    "redraw the gauntlet's ball in SDPM and SDPS E-G as a grenade (48 lumps, rotation by rotation)"),
        "C": Option("C", "slag", pzl_slag,
                    "A gout of molten iron from Tankograd's foundry: three hot lobes, black crust plates that the "
                    "additive blend turns into holes, molten drops in the burst.",
                    "the gauntlet's yellow ball (SDPM / SDPS E-G) passes for molten iron; MAP01 and MAP02 have no "
                    "foundry, so the lore link holds in MAP03 only"),
    },
}
# The art director's pick after the sweep (stage 2: looked at once). See RECOMMENDATION_WHY.
RECOMMENDED = {"doughboy": "A", "panzer": "A"}
RECOMMENDATION_WHY = {
    "doughboy": ("It is the brief and it is already in the game: the approved SDDB B-D frames kindle exactly this "
                 "white core in red in the mouth, so the shell leaving the mouth is the shell that flies. Measured "
                 "against the storm bolt it is the bolt turned inside out (white centre, red rim; the bolt is red "
                 "inside white) and a third larger. B, the roundel, is the most legible of the six and the most "
                 "Legion, but it puts an insignia on a projectile (your call, D12); C, the spit, washes out pale on "
                 "brick and reads as a puff, not a threat."),
    "panzer": ("It is the brief and it is already in the game: the approved SDPM and SDPS E-G frames form and throw "
               "this ball in the right gauntlet. It is the largest flying shell (22 px against the bolt's 12), "
               "dull and olive-edged: heavier, as BESTIARY §8 asks. B, the grenade, is the best idea and the "
               "worst read: at 1x it is a thin stick, and it would cost 48 attack lumps redrawn; C, the slag, is "
               "busy at 1x and its lore holds only in MAP03."),
}


# ================================================================ rendering
def render(shell_key: str, option: str, frame: str) -> np.ndarray:
    sh = SHELLS[shell_key]
    c = V(0.0, centre_y(sh), 0.0)
    prims = OPTIONS[shell_key][option].model(frame, c)
    return core.render(prims, 0, sh.canvas, MATERIALS, seed=SEED,
                       what=f"{sh.sprite}{frame}0 option {option}")


def lump(shell_key: str, frame: str) -> str:
    """Doom's name: rotation 0, one image for every angle."""
    return f"{SHELLS[shell_key].sprite}{frame}0"


def grab(shell_key: str) -> tuple[int, int]:
    return core.grab_offsets(SHELLS[shell_key].canvas)


def sweep_path(shell_key: str, option: str, frame: str) -> Path:
    return SWEEP_DIR / f"{SHELLS[shell_key].sprite}_{option}_{frame}0.png"


def full_path(shell_key: str, frame: str) -> Path:
    return OUT_DIR / SHELLS[shell_key].sprite / f"{lump(shell_key, frame)}.png"


def build_sweep() -> dict:
    out = {}
    for k in SHELLS:
        for o in OPTIONS[k]:
            for f in SWEEP_FRAMES:
                rgba = render(k, o, f)
                heavy.save(rgba, sweep_path(k, o, f), grab(k))
                out[(k, o, f)] = rgba
    return out


def build_full() -> dict:
    out = {}
    for k in SHELLS:
        for f in FRAMES:
            rgba = render(k, RECOMMENDED[k], f)
            heavy.save(rgba, full_path(k, f), grab(k))
            out[(k, f)] = rgba
    return out


def load_full() -> dict:
    out = {}
    for k in SHELLS:
        for f in FRAMES:
            with Image.open(full_path(k, f)) as im:
                out[(k, f)] = np.asarray(im.convert("RGBA")).copy()
    return out


# ================================================================ scenes
def asset_rgb(lump_name: str) -> np.ndarray:
    for folder in ("textures", "flats"):
        for path in sorted((ASSETS / folder).glob(f"*/{lump_name}.png")):
            with Image.open(path) as im:
                return np.asarray(im.convert("RGB"), dtype=np.uint8)
    raise FileNotFoundError(lump_name)


def approved(rel: str) -> tuple[np.ndarray, int, int]:
    path = ASSETS / "sprites" / f"{rel}.png"
    with Image.open(path) as im:
        rgba = np.asarray(im.convert("RGBA")).copy()
    gx, gy = core.read_grab(path)
    return rgba, gx, gy


def additive(rgba: np.ndarray, under: np.ndarray) -> np.ndarray:
    """RenderStyle "Add", Bright: the sprite's colour added to what is behind
    it, unaffected by the sector light. A stand-in, NOT VERIFIED against
    GZDoom's blend."""
    out = under.astype(np.int32).copy()
    a = rgba[..., 3] > 0
    out[a] += rgba[..., :3][a]
    return np.clip(out, 0, 255).astype(np.uint8)


def wall_patch(sh: Shell, w: int, h: int) -> np.ndarray:
    """The shell's wall at its light (the stand-in), for additive tiles."""
    return core.lit(flat.tile_to(asset_rgb(sh.wall), w, h), sh.light, heavy.palette_v2()).copy()


def _paste_add(canvas: np.ndarray, rgba: np.ndarray, x0: int, y0: int) -> None:
    h, w = rgba.shape[:2]
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    ys2, xs2 = ys + y0, xs + x0
    keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < canvas.shape[1])
    v = canvas[ys2[keep], xs2[keep]].astype(np.int32) + rgba[ys[keep], xs[keep], :3]
    canvas[ys2[keep], xs2[keep]] = np.clip(v, 0, 255).astype(np.uint8)


def scene(shell_key: str, shell_rgba: np.ndarray, frame: str = "A") -> np.ndarray:
    """At 1x on the shell's MAP03 wall over SDFLR4: the thrower(s) in the
    firing frame (normal blend, lit), then the shell in flight at spawn height
    and the Freedoom placeholder's same frame at the same height (additive,
    fullbright; its slot stays bare when iwads/ is absent)."""
    sh = SHELLS[shell_key]
    figs = [approved(t) for t in sh.thrower]
    n = len(figs) + 2
    width = SCENE_SLOT * n
    w_rgb = flat.tile_to(asset_rgb(sh.wall), width, SCENE_WALL_H)
    fl = flat.tile_to(asset_rgb(FLOOR), width, flat.FLOOR_H * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, flat.FLOOR_H), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = SCENE_WALL_H + (flat.FLOOR_LINE - flat.WALL_H) - core.FEET_SINK
    for i, (spr, ox, oy) in enumerate(figs):
        x0 = int(round(SCENE_SLOT * (i + 0.5))) - ox
        y0 = base - sh.thrower_z - oy
        ys, xs = np.nonzero(spr[..., 3] > 0)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    canvas = core.lit(canvas, sh.light, heavy.palette_v2()).copy()
    z = sh.thrower_z + SPAWN_HEIGHT
    gx, gy = grab(shell_key)
    i = len(figs)
    _paste_add(canvas, shell_rgba, int(round(SCENE_SLOT * (i + 0.5))) - gx, base - z - gy)
    ph = placeholder_frames(shell_key).get(frame)
    if ph is not None:
        _paste_add(canvas, ph[0], int(round(SCENE_SLOT * (i + 1.5))) - ph[1], base - z - ph[2])
    return canvas


_PLACEHOLDERS: dict[str, dict] = {}


def placeholder_frames(shell_key: str) -> dict[str, tuple[np.ndarray, int, int]]:
    """Freedoom's frames for comparison (the IWAD is optional, not in git)."""
    if shell_key in _PLACEHOLDERS:
        return _PLACEHOLDERS[shell_key]
    sh = SHELLS[shell_key]
    out = {}
    for f in FRAMES:
        for name in (f"{sh.placeholder}{f}0", f"{sh.placeholder}{f}1{f}5", f"{sh.placeholder}{f}1"):
            got = core.freedoom_sprite(name)
            if got is not None:
                out[f] = got
                break
    _PLACEHOLDERS[shell_key] = out
    return out


def save_gif_any(frames: list[np.ndarray], durations: list[int], path: Path) -> Path:
    """core.save_gif (lossless) when the frames hold <= 256 colours; the
    additive scenes can hold more, and are then quantised to one shared
    adaptive palette (said on the sheet)."""
    try:
        return core.save_gif(frames, durations, path)
    except ValueError:
        stack = np.concatenate(frames, axis=0)
        q = Image.fromarray(stack, "RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        h = frames[0].shape[0]
        idx = np.asarray(q)
        pal = q.getpalette()
        ims = []
        for i in range(len(frames)):
            im = Image.fromarray(idx[i * h:(i + 1) * h], "P")
            im.putpalette(pal)
            ims.append(im)
        path.parent.mkdir(parents=True, exist_ok=True)
        ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations, loop=0, optimize=False,
                    disposal=1)
        return path


def _ms(tics: int) -> int:
    return int(round(tics * core.TIC_MS))


def write_gifs(spr: dict) -> dict:
    """Per shell: flight (A B, 4 tics) and flight-then-burst, additive on its
    wall, at 1x (the sheet zooms them); and the 1x scene in flight."""
    out = {}
    for k, sh in SHELLS.items():
        st = zs_states(sh.zs)
        d = OUT_DIR / sh.sprite
        wall = wall_patch(sh, sh.canvas.w, sh.canvas.h)
        add = lambda f: additive(spr[(k, f)], wall)  # noqa: E731
        fl = [(f, t) for _, f, t in st["Spawn"]]
        bu = [(f, t) for _, f, t in st["Death"]]
        out[(k, "flight")] = save_gif_any([add(f) for f, _ in fl], [_ms(t) for _, t in fl], d / "flight.gif")
        seq = fl * 3 + bu
        durs = [_ms(t) for _, t in seq]
        durs[-1] = HOLD_MS
        out[(k, "cycle")] = save_gif_any([add(f) for f, _ in seq] + [wall], durs + [HOLD_MS // 2],
                                         d / "flight_burst.gif")
        frames = [scene(k, spr[(k, f)], f) for f, _ in fl]
        out[(k, "scene")] = save_gif_any(frames, [_ms(t) for _, t in fl], d / "scene_flight.gif")
        big = [np.asarray(Image.fromarray(a, "RGB").resize((a.shape[1] * SCENE_ZOOM, a.shape[0] * SCENE_ZOOM),
                                                           Image.Resampling.NEAREST)) for a in frames]
        out[(k, "scene_zoom")] = save_gif_any(big, [_ms(t) for _, t in fl], d / f"scene_flight_{SCENE_ZOOM}x.gif")
    return out


# ================================================================ metrics
def ramp_of() -> dict[tuple[int, int, int], str]:
    """Palette colour -> its ramp name (v2), black and white by name."""
    out: dict[tuple[int, int, int], str] = {(0, 0, 0): "black", (255, 255, 255): "white"}
    pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
    for r in pal["ramps"] + pal.get("added_ramps", []):
        for c in r["colours"]:
            out.setdefault(tuple(c), r["name"])
    for name in (FLESH, COBALT, "marble_red", "mosaic_gold"):
        for c in palgen.ramp_colours(name):
            out.setdefault(tuple(c), name)
    return out


def _family(rgba: np.ndarray, sel: np.ndarray, rmap: dict) -> str:
    names = [rmap.get(tuple(int(v) for v in p), "?") for p in rgba[..., :3][sel]]
    if not names:
        return "-"
    vals, cnt = np.unique(names, return_counts=True)
    return str(vals[np.argmax(cnt)])


def measure(rgba: np.ndarray, rmap: dict | None = None) -> dict:
    """Size, brightness, and which ramp holds the CENTRE (within 2 px of the
    opaque centroid) and the RIM (opaque pixels with a transparent neighbour):
    the bolt is red inside white; a shell that is the same reads the same."""
    rmap = ramp_of() if rmap is None else rmap
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    cy, cx = ys.mean(), xs.mean()
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    centre = a & ((yy - cy) ** 2 + (xx - cx) ** 2 <= 4.0)
    pad = np.pad(a, 1)
    inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    rim = a & ~inner
    rgb = rgba[..., :3][a].astype(np.float64)
    return {"w": int(xs.max() - xs.min() + 1), "h": int(ys.max() - ys.min() + 1), "px": int(a.sum()),
            "mean_rgb": [round(float(v), 1) for v in rgb.mean(axis=0)],
            "luma": round(float((rgb @ [0.299, 0.587, 0.114]).mean()), 1),
            "centre": _family(rgba, centre, rmap), "rim": _family(rgba, rim, rmap)}


def references() -> dict[str, np.ndarray]:
    """The approved shells, for the legibility row (read only)."""
    out = {}
    for name, rel in (("SDBLA0", "storm/SDBLA0"), ("SDGLA0", "general/SDGLA0")):
        p = ASSETS / "sprites" / f"{rel}.png"
        if p.is_file():
            with Image.open(p) as im:
                out[name] = np.asarray(im.convert("RGBA")).copy()
    return out


# ================================================================ the sheet
def _zoom(rgb: np.ndarray, z: int) -> np.ndarray:
    return np.repeat(np.repeat(rgb, z, axis=0), z, axis=1)


def _rgb_tile(rgb: np.ndarray, zoom: int, cap: str, sub: str = "") -> str:
    return core.tile(core.png_uri(rgb), rgb.shape[1], rgb.shape[0], zoom, cap, sub)


def _strip(tiles: list[str]) -> str:
    return '<div class="strip">' + "".join(tiles) + "</div>"


def write_sheet(sweep: dict, spr: dict, gifs: dict, metrics: dict, stamp: str) -> Path:
    S = []
    refs = references()
    for k, sh in SHELLS.items():
        wall = wall_patch(sh, sh.canvas.w, sh.canvas.h)
        cards = []
        for o, opt in OPTIONS[k].items():
            tiles = []
            for f in SWEEP_FRAMES:
                rgba = sweep[(k, o, f)]
                tiles.append(core.sprite_tile(rgba, ZOOM_OPTION, f"{sh.sprite}{f}0 · {o}",
                                              "flight" if f in FLIGHT else "burst", bg=(0, 0, 0)))
                tiles.append(_rgb_tile(additive(rgba, wall), ZOOM_OPTION, f"{f} added on {sh.wall}",
                                       f"light {sh.light}"))
            tiles.append(_rgb_tile(scene(k, sweep[(k, o, "A")]), 1, "1x in flight", "next to the thrower"))
            m = metrics["sweep"][f"{k}_{o}"]
            rec = o == RECOMMENDED[k]
            cards.append(
                f'<div class="card{" rec" if rec else ""}">'
                + ('<div class="tag">recommended</div>' if rec else "")
                + f"<h3>{sh.sprite} · {o} · {html.escape(opt.name)}</h3>"
                + f'<p class="desc">{html.escape(opt.what)}</p>' + _strip(tiles)
                + f"<dl><dt>flight A</dt><dd>{m['w']}×{m['h']} px, luma {m['luma']}, centre {m['centre']}, "
                  f"rim {m['rim']}</dd><dt>install also needs</dt><dd>{html.escape(opt.install)}</dd></dl></div>")
        lead = (f"<b>{sh.cls}</b> ({html.escape(sh.zs.relative_to(PROJECT_ROOT).as_posix())}) flies on Freedoom's "
                f"<code>{sh.placeholder}</code> today; its own sprite is <code>{sh.sprite}</code> (BESTIARY §2.7). "
                f"Each option: the flight frame A and the first burst frame C at {ZOOM_OPTION}x, raw (what the "
                f"engine adds) and added onto {sh.wall} at light {sh.light} ({html.escape(sh.where)}), then at 1x "
                "beside the thrower and Freedoom's placeholder.")
        S.append((f"{'1' if k == 'doughboy' else '2'} · Sweep: {sh.sprite}, the "
                  f"{'Doughboy' if k == 'doughboy' else 'Panzermensch and Schwer'}'s shell", lead,
                  '<div class="grid">' + "".join(cards) + "</div>"))
    for n, (k, sh) in enumerate(SHELLS.items(), start=3):
        wall = wall_patch(sh, sh.canvas.w, sh.canvas.h)
        o = RECOMMENDED[k]
        st = zs_states(sh.zs)
        raw = [core.sprite_tile(spr[(k, f)], ZOOM_OPTION, lump(k, f), "flight" if f in FLIGHT else "burst",
                                bg=(0, 0, 0)) for f in FRAMES]
        added = [_rgb_tile(additive(spr[(k, f)], wall), ZOOM_OPTION, f"{f} added", sh.wall) for f in FRAMES]
        anim = [core.gif_tile(gifs[(k, "flight")], ZOOM_OPTION, "flight, A B", "4 tics each, looped"),
                core.gif_tile(gifs[(k, "cycle")], ZOOM_OPTION, "flight, then the burst", "C D E, 6 tics each"),
                core.gif_tile(gifs[(k, "scene")], 1, "1x in flight", f"{sh.wall} · light {sh.light}"),
                core.gif_tile(gifs[(k, "scene_zoom")], 1, f"the same scene at {SCENE_ZOOM}x", "")]
        tics = ", ".join(f"{lab} " + " ".join(f"{f}{t}" for _, f, t in seq) for lab, seq in st.items())
        lead = (f"Option {o} ({html.escape(OPTIONS[k][o].name)}), every frame the class's States name ({tics}), "
                f"rotation 0, grAb {grab(k)} on a {sh.canvas.w}×{sh.canvas.h} canvas: the centre "
                f"{sh.canvas.foot_row - core.FEET_SINK - sh.canvas.h // 2} px above the actor's z, half its "
                "Height, as Freedoom hangs its balls. Files in "
                f"<code>work/art/shells/{sh.sprite}/</code>, named as the engine reads them.")
        S.append((f"{n} · The full set: {sh.sprite} A-E (option {o})", lead,
                  _strip(raw) + _strip(added) + _strip(anim)))
    # legibility against the approved shells
    rows = []
    tiles = []
    wall = wall_patch(SHELLS["doughboy"], 48, 48)
    for name, rgba in list(refs.items()) + [(lump(k, "A"), spr[(k, "A")]) for k in SHELLS]:
        pad = np.zeros((56, 56, 4), np.uint8)
        y0, x0 = (56 - rgba.shape[0]) // 2, (56 - rgba.shape[1]) // 2
        pad[y0:y0 + rgba.shape[0], x0:x0 + rgba.shape[1]] = rgba
        tiles.append(_rgb_tile(additive(pad, wall_patch(SHELLS["doughboy"], 56, 56)), ZOOM_OPTION, name,
                               "added on SDBRCK1"))
        m = measure(rgba)
        rows.append([name, f"{m['w']}×{m['h']}", m["px"], m["luma"], m["centre"], m["rim"]])
    del wall
    S.append(("5 · Legibility: every shell in the game side by side",
              "The approved storm bolt (SDBL) and the General's shell (SDGL) next to the two recommended shells, "
              f"flight frame A, at {ZOOM_OPTION}x on the same brick. Measured: the ramp that holds the centre and "
              "the rim of each (the BESTIARY's rule: the Doughboy's shell must not read as the bolt).",
              _strip(tiles) + sheetlib.table(["lump", "size", "px", "luma", "centre", "rim"], rows)))
    S.append(("6 · What you decide, and what the install does", "", verdict_html()))
    intro = ("Backlog M2b (audit B4): the last two Freedoom projectiles on our enemies. A sweep of three options per "
             "shell, then the full set of the one I recommend, so a yes installs at once. Drawn on the rig the "
             "approved enemies were drawn on, as the storm bolt and the General's shell, by "
             "<code>tools/art/gen_shells.py</code>; no system fonts. Draft: nothing in <code>assets/</code> or "
             "<code>src/</code>.")
    footer = ("Sprites: tools/art/gen_shells.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic. Approved "
              "sprites and MAP03 walls read from assets/ (the mod's own). Freedoom's BAL2 / BAL7 shown for "
              "comparison only (BSD-3-Clause), not used as a source. Light and additive blend are stand-ins, NOT "
              "VERIFIED in GZDoom.")
    path = PREVIEW_DIR / f"{stamp}_F5_enemy-shells.html"
    sheetlib.write_sheet(path, lang="en", title="Enemy shells: SDDL and SDPL (F5, M2b)",
                         subtitle="sweep 2 × 3 options · full sets of the recommended · rotation 0 · additive · draft",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", core.SHEET_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    Image.fromarray(contact(sweep, spr), "RGB").save(path.with_suffix(".png"), optimize=True)
    return path


def verdict_html() -> str:
    items = []
    for k, sh in SHELLS.items():
        o = RECOMMENDED[k]
        items.append(f"<li><b>{sh.sprite}: option {o}, {html.escape(OPTIONS[k][o].name)}.</b> "
                     f"{html.escape(RECOMMENDATION_WHY[k])}</li>")
    install = (
        "<p><b>The install, on your yes</b> (mod-engineer and art-director; no tic moves): copy the five "
        "<code>SDDL?0.png</code> to <code>assets/sprites/doughboy/</code> and the five <code>SDPL?0.png</code> to "
        "<code>assets/sprites/panzermensch/</code>; in <code>doughboy_shell.zs</code> and <code>panzer_shell.zs</code> "
        "rename <code>BAL2</code> / <code>BAL7</code> to <code>SDDL</code> / <code>SDPL</code> on the two state lines "
        "and the header comment (and <code>doughboy.zs</code>'s comment); drop BAL2 and BAL7 from MOD-SPEC §5's IWAD "
        "sprites and mark them installed in §6.3, BESTIARY §2.7 / §7 / §8 / §12; ten rows in "
        "<code>docs/art/LICENSES.md</code>; <code>tests/test_doughboy_sprites.py</code> (SHELL_SPRITE = \"BAL2\") and "
        "<code>tests/test_panzermensch_sprites.py</code> move to the new names; then the PM's engine pass. "
        "Freedoom's BAL7 had rotations 1-8 for its flight; ours is rotation 0, one image for every angle, as SDBL "
        "and SDGL.</p>")
    return ('<div class="ask"><ol>' + "".join(items) + "</ol></div>" + install
            + "<p>Or name another option per shell (A, B, C); its full set renders in one command.</p>")


def contact(sweep: dict, spr: dict) -> np.ndarray:
    """No text: per shell a row of its three options (A and C, raw on black,
    at 3x), then the recommended set A-E added on its wall at 3x, then the
    1x scene."""
    gap = 8
    rows: list[list[np.ndarray]] = []
    for k, sh in SHELLS.items():
        wall = wall_patch(sh, sh.canvas.w, sh.canvas.h)
        rows.append([_zoom(core.on_bg(sweep[(k, o, f)], (0, 0, 0)), ZOOM_OPTION)
                     for o in OPTIONS[k] for f in SWEEP_FRAMES])
        rows.append([_zoom(additive(spr[(k, f)], wall), ZOOM_OPTION) for f in FRAMES])
        rows.append([scene(k, spr[(k, "A")])])
    width = max(sum(a.shape[1] + gap for a in r) for r in rows) + gap
    height = gap + sum(max(a.shape[0] for a in r) + gap for r in rows)
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = CONTACT_BG
    y = gap
    for r in rows:
        x = gap
        for a in r:
            canvas[y:y + a.shape[0], x:x + a.shape[1]] = a
            x += a.shape[1] + gap
        y += max(a.shape[0] for a in r) + gap
    return canvas


# ===================================================================== main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=None, help="sheet timestamp YYYY-MM-DD_HHMM (default: now)")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--sweep-only", action="store_true", help="the six options' A and C only")
    args = ap.parse_args(argv)
    stamp = args.stamp or dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    sweep = build_sweep()
    rmap = ramp_of()
    metrics = {"sweep": {f"{k}_{o}": measure(sweep[(k, o, "A")], rmap) for k in SHELLS for o in OPTIONS[k]}}
    if args.sweep_only:
        print(json.dumps(metrics, indent=1))
        return 0
    spr = build_full()
    metrics["full"] = {lump(k, f): measure(spr[(k, f)], rmap) for k, f in spr}
    metrics["references"] = {n: measure(a, rmap) for n, a in references().items()}
    metrics["recommended"] = RECOMMENDED
    gifs = write_gifs(spr)
    for k, sh in SHELLS.items():
        Image.fromarray(scene(k, spr[(k, "A")]), "RGB").save(OUT_DIR / sh.sprite / "scene_A.png", optimize=True)
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    if not args.no_sheet:
        print(write_sheet(sweep, spr, gifs, metrics, stamp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
