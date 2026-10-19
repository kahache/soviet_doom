#!/usr/bin/env python3
"""Soviet Doom - the player's effects and the last Freedoom world sprites (backlog M2c, D75).

D75 put these in the M2 gate: the player's projectiles (the RPG-7's PG-7V,
the hand Katyusha's rocket, the ROKS-3's flame), the burst the two rockets
share, the bullet puff, the blood's SHAPE (its colour stays the D49
BloodColor "AD 27 21"), the teleport fog, the explosive barrel and the
floor lamp (docs/qa/2026-10-14_2357_M2-freedoom-audit.md, items A1-A3).

Two drawing methods, one palette (palette.json v1, RGBA with hard alpha,
every opaque pixel a palette colour, as every sprite of the mod):

  solid things   the PG-7V, the Katyusha rocket, the fuel drum and the lamp
                 are modelled on the bestiary's rig (rig_core: SDF
                 primitives, banded light, contour and rim), so they share
                 the enemies' light and edges. The rockets are drawn at
                 Doom's 8 rotations as 5 lumps (2-8, 3-7, 4-6 mirrored).
  soft effects   fire, smoke, dust, sparks, drops and arcs are 2D fields
                 (fractal noise from artlib, seeded) cut into palette inks.

The contract each sprite keeps is EFFECTS below: frame letters, tics and
RenderStyle read from the code that plays it (src/zscript/weapons/*.zs for
our three projectiles; GZDoom g4.14.2's gzdoom.pk3 for the engine actors,
quoted with their file). tests/test_gen_effects.py checks it against the
.zs and, when iwads/ is present, against Freedoom's lump list.

Install (NOT done here: no assets/, no .zs, no LICENSES.md; the CEO first):
  * our projectiles  new prefix + state edit by mod-engineer: SDPG (PG-7V,
                     MISL A), SDKR (rocket, MISL A), SDPX A-C (the shared
                     burst, today MISL B-D: the letters move B-D -> A-C),
                     SDFJ / SDFX (flame, PLSS / PLSE: a pure rename;
                     SDFJ, not MOD-SPEC 6.3's SDFL: SDFL + frame R +
                     rotation 1 spells SDFLR1, the floor flat's name).
  * engine actors    the IWAD lump names themselves (PUFF, BLUD, TFOG,
                     IFOG, BAR1, BEXP, COLU), every frame of each, so the
                     override is complete and needs no ZScript; see
                     INSTALL_WHY.

    .venv/Scripts/python.exe tools/art/gen_effects.py            # sweep + full set + preview
    .venv/Scripts/python.exe tools/art/gen_effects.py --sweep    # the options only
    .venv/Scripts/python.exe tools/art/gen_effects.py --stamp 2026-10-19_2300

Output: work/art/effects/ (sweep/, <SPRITE>/<LUMP>.png with grAb, gifs/,
manifest.json); the sheet docs/art/previews/<stamp>_F4_player-effects.html
and .png.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import io
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

ART_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_DIR))

import artlib  # noqa: E402
import rig_core as core  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = ART_DIR.parents[1]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "effects"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
ZS_DIR = PROJECT_ROOT / "src" / "zscript"
SEED = 75                       # D75, the decision that put these in M2
TIC_MS = 1000 / 35
SWEEP_ZOOM = 3                  # the brief: options at 3x
GIF_ZOOM = 3
BLOOD_COLOUR = (0xAD, 0x27, 0x21)   # D49, BloodColor "AD 27 21" on every monster

# ================================================================ contract
@dataclass(frozen=True)
class Effect:
    """One sprite we ship: the lumps, how the code plays them, where from."""
    key: str
    sprite: str                 # the 4-letter name we ship
    frames: str                 # frame letters we draw
    rotated: bool               # 8 rotations as 5 lumps (mirrored pairs)
    style: str                  # RenderStyle as the actor sets it
    alpha: float
    bright: str                 # frames the state marks Bright (fullbright)
    replaces: str               # what the player sees today
    actor: str                  # the class that plays it, and its file
    sequences: tuple            # ((label, ((frame, tics), ...)), ...) as played
    install: str                # "rename" | "prefix+letters" | "override"


def _seq(frames: str, tics) -> tuple:
    tics = (tics,) * len(frames) if isinstance(tics, int) else tuple(tics)
    return tuple(zip(frames, tics))


EFFECTS: tuple[Effect, ...] = (
    Effect("pg7", "SDPG", "A", True, "Normal", 1.0, "A", "MISL A (Freedoom rocket, 8 rotations)",
           "SD_Pg7Grenade, src/zscript/weapons/pg7_grenade.zs",
           (("flight", _seq("A", 1)),), "prefix+letters"),
    Effect("katyusha", "SDKR", "A", True, "Normal", 1.0, "A", "MISL A (Freedoom rocket, 8 rotations)",
           "SD_KatyushaRocket, src/zscript/weapons/katyusha_rocket.zs",
           (("flight", _seq("A", 1)),), "prefix+letters"),
    Effect("burst", "SDPX", "ABC", False, "Normal", 1.0, "ABC", "MISL B-D (Freedoom rocket burst)",
           "SD_Pg7Grenade and SD_KatyushaRocket, Death states",
           (("PG-7V", _seq("ABC", (8, 6, 4))), ("Katyusha", _seq("ABC", (6, 5, 4)))), "prefix+letters"),
    Effect("flame", "SDFJ", "AB", False, "Add", 0.85, "AB", "PLSS A-B (Freedoom plasma ball)",
           "SD_FlameBlob, src/zscript/weapons/flame_blob.zs",
           (("flight", _seq("ABABABABABAB", 2)),), "rename"),
    Effect("flamex", "SDFX", "ABCDE", False, "Add", 0.85, "ABCDE", "PLSE A-E (Freedoom plasma impact)",
           "SD_FlameBlob Death, src/zscript/weapons/flame_blob.zs",
           (("impact", _seq("ABCDE", 3)),), "rename"),
    Effect("puff", "PUFF", "ABCD", False, "Translucent", 0.5, "A", "PUFF A-D (Freedoom)",
           "BulletPuff and SD_IceAxePuff, gzdoom.pk3 zscript/actors/doom/doommisc.zs",
           (("hit", _seq("ABCD", 4)),), "override"),
    Effect("blood", "BLUD", "ABC", False, "Normal", 1.0, "", "BLUD A-C (Freedoom, tinted AD 27 21)",
           "Blood, gzdoom.pk3 zscript/actors/shared/blood.zs",
           (("hit", _seq("CBA", 8)),), "override"),
    Effect("tfog", "TFOG", "ABCDEFGHIJ", False, "Add", 1.0, "ABCDEFGHIJ", "TFOG A-J (Freedoom)",
           "TeleportFog, gzdoom.pk3 zscript/actors/shared/teleport.zs (the General's summon)",
           (("summon", _seq("ABABCDEFGHIJ", 6)),), "override"),
    Effect("ifog", "IFOG", "ABCDE", False, "Normal", 1.0, "ABCDE", "IFOG A-E (Freedoom)",
           "ItemFog, gzdoom.pk3 zscript/actors/shared/itemeffects.zs (item respawn only)",
           (("respawn", _seq("ABABCDE", 6)),), "override"),
    Effect("barrel", "BAR1", "AB", False, "Normal", 1.0, "", "BAR1 A-B (Freedoom drum)",
           "ExplosiveBarrel (ednum 2035), gzdoom.pk3 zscript/actors/doom/doommisc.zs",
           (("idle", _seq("AB", 6)),), "override"),
    Effect("bexp", "BEXP", "ABCDE", False, "Normal", 1.0, "ABCDE", "BEXP A-E (Freedoom)",
           "ExplosiveBarrel Death, gzdoom.pk3 zscript/actors/doom/doommisc.zs",
           (("death", _seq("ABCDE", (5, 5, 5, 10, 10))),), "override"),
    Effect("lamp", "COLU", "A", False, "Normal", 1.0, "A", "COLU A (Freedoom floor lamp)",
           "Column (ednum 2028), gzdoom.pk3 zscript/actors/doom/doomdecorations.zs",
           (("still", _seq("A", 1)),), "override"),
)
BY_KEY = {e.key: e for e in EFFECTS}
NEW_PREFIXES = tuple(e.sprite for e in EFFECTS if e.install != "override")
OVERRIDE_PREFIXES = tuple(e.sprite for e in EFFECTS if e.install == "override")

# How each placeholder line reads today in OUR code (the lines the install
# edits). tests check these against the .zs, so a code change shows here.
PLACEHOLDER_STATES = {
    "pg7_grenade.zs": [("Spawn", "MISL", "A", 1), ("Death", "MISL", "B", 8), ("Death", "MISL", "C", 6),
                       ("Death", "MISL", "D", 4)],
    "katyusha_rocket.zs": [("Spawn", "MISL", "A", 1), ("Death", "MISL", "B", 6), ("Death", "MISL", "C", 5),
                           ("Death", "MISL", "D", 4)],
    "flame_blob.zs": [("Spawn", "PLSS", "ABABABABABAB", 2), ("Death", "PLSE", "ABCDE", 3)],
}
# The placeholder letter -> our (sprite, letter), per file.
LETTER_MAP = {
    "pg7_grenade.zs": {("MISL", "A"): ("SDPG", "A"), ("MISL", "B"): ("SDPX", "A"),
                       ("MISL", "C"): ("SDPX", "B"), ("MISL", "D"): ("SDPX", "C")},
    "katyusha_rocket.zs": {("MISL", "A"): ("SDKR", "A"), ("MISL", "B"): ("SDPX", "A"),
                           ("MISL", "C"): ("SDPX", "B"), ("MISL", "D"): ("SDPX", "C")},
    "flame_blob.zs": {("PLSS", "A"): ("SDFJ", "A"), ("PLSS", "B"): ("SDFJ", "B"),
                      **{("PLSE", c): ("SDFX", c) for c in "ABCDE"}},
}

INSTALL_WHY = {
    "prefix+letters": "Our own actor: a new SD prefix and a state edit, the SDBL/SDGL pattern. MISL cannot "
                      "simply be overridden: it is one sprite for two rockets, and Freedoom's MISL A has 5 "
                      "rotation lumps whose names would have to match ours one for one. The shared burst gets "
                      "its own name, SDPX, so the PG-7V and the Katyusha draw the same three lumps; its letters "
                      "move from MISL B-D to SDPX A-C (a sprite must start at A), tics unchanged.",
    "rename": "Our own actor, letters and tics as they are: PLSS -> SDFJ and PLSE -> SDFX is a rename of the "
              "sprite only. MOD-SPEC 6.3 reserves SDFL for the flight; SDFJ ('flame jet') is proposed instead "
              "because SDFL plus frame R and rotation 1 spells SDFLR1, the name of an installed floor flat "
              "(different namespaces, so not an engine clash, but a reader's one). SDFX as reserved. "
              "RenderStyle Add, Alpha 0.85 stay.",
    "override": "An engine actor: ship the IWAD's own lump names (every frame, all rotation 0, so nothing of "
                "Freedoom's is left to mix in). No ZScript: it reaches every path that spawns the actor, "
                "including SD_IceAxePuff (it inherits BulletPuff's PUFF states), the engine's own blood with "
                "the D49 BloodColor, the teleport fog the General spawns, and the barrels and lamps the "
                "maps place by ednum. A new prefix would need a replacing class per actor plus SD_IceAxePuff's "
                "states, for the same pixels.",
}

# ================================================================ inks (v1)
R = artlib.ramp


def _inks(*spec) -> list[tuple[int, int, int]]:
    out = []
    for s in spec:
        if s == "black":
            out.append((0, 0, 0))
        elif s == "white":
            out.append((255, 255, 255))
        else:
            name, i = s
            out.append(tuple(R(name)[i]))
    return out


FIRE = _inks(("flag_red", 2), ("flag_red", 5), ("flag_red", 8), ("flag_red", 11), ("flag_red", 14),
             ("rust_brown", 13), ("rust_brown", 15), ("hazard_yellow", 12), ("hazard_yellow", 15),
             ("cream_yellow", 15), "white")
SMOKE = _inks(("concrete_cold", 2), ("rust_brown", 2), ("concrete_cold", 6), ("rust_brown", 4),
              ("concrete_cold", 10), ("concrete_cold", 14), ("concrete_cold", 18))
DUST = _inks(*[("concrete_cold", i) for i in (14, 17, 20, 23, 26, 28, 30)])
DARK_SMOKE = SMOKE[:5]
PALE = _inks(*[("plaster_warm", i) for i in (6, 8, 10, 12, 14, 15)])
STEEL_GLOW = _inks(("steel_blue", 3), ("steel_blue", 6), ("steel_blue", 9), ("steel_blue", 12),
                   ("steel_blue", 15), "white")
CREAM_GLOW = _inks(*[("cream_yellow", i) for i in (4, 7, 10, 13, 15)], "white")
BLOOD_INKS = _inks(*[("flag_red", i) for i in (1, 3, 5, 7, 9, 11, 13, 15)])
SPARK = _inks(("hazard_yellow", 12), ("hazard_yellow", 15), ("cream_yellow", 15), "white")
CHIP = _inks(("concrete_cold", 3), ("concrete_cold", 6))


def palette_v1() -> set[tuple[int, int, int]]:
    return {tuple(c) for c in artlib.load_palette()["colours"]}


# ============================================================ 2D painters
def _grid(w: int, h: int):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    return xx, yy


def _noise(w: int, h: int, cells: int, octaves: int, seed: int) -> np.ndarray:
    return artlib.fbm(w, h, cells, octaves, np.random.default_rng(seed))


def _paint(rgba: np.ndarray, mask: np.ndarray, t: np.ndarray, inks) -> None:
    cols = np.array(inks, np.uint8)
    idx = np.clip(np.rint(np.clip(t, 0, 1) * (len(cols) - 1)), 0, len(cols) - 1).astype(int)
    rgba[mask, :3] = cols[idx[mask]]
    rgba[mask, 3] = 255


def _clear_border(rgba: np.ndarray) -> np.ndarray:
    rgba[0, :, 3] = rgba[-1, :, 3] = 0
    rgba[:, 0, 3] = rgba[:, -1, 3] = 0
    rgba[rgba[..., 3] == 0] = 0
    return rgba


def fireball(w, h, cx, cy, r, *, heat=1.0, smoke=0.0, seed=0, up=1.0, turb=0.8, cut=0.12, ring=0.0,
             fire=FIRE, smoke_inks=SMOKE, base=None) -> np.ndarray:
    """A noisy ball of fire cut into inks. `smoke` is the temperature below
    which a pixel is smoke, not flame; `up` stretches the top (flames
    rise); `ring` > 0 makes a shock ring of that relative radius."""
    xx, yy = _grid(w, h)
    dx = (xx - cx) / r
    dy = (yy - cy) / r
    dy = np.where(dy < 0, dy / up, dy)
    d = np.hypot(dx, dy)
    if ring:
        d = np.abs(d - ring) / max(1e-6, 1.0 - ring) * 1.6
    n1 = _noise(w, h, max(2, int(w / 10)), 3, seed)
    n2 = _noise(w, h, max(3, int(w / 5)), 2, seed + 1)
    shape = 1.0 - d + (n1 - 0.5) * turb
    opaque = shape > cut
    temp = np.clip(shape, 0, 1) * heat + (n2 - 0.5) * 0.3
    rgba = np.zeros((h, w, 4), np.uint8) if base is None else base
    is_fire = opaque & (temp > smoke)
    is_smoke = opaque & ~is_fire
    _paint(rgba, is_fire, np.clip((temp - smoke) / max(0.05, heat * 0.75 - smoke), 0, 1) ** 0.7, fire)
    lift = np.clip(0.25 + 0.8 * shape - (yy - cy) / (2.5 * r) + (n2 - 0.5) * 0.4, 0, 1)   # lit from above
    _paint(rgba, is_smoke, lift, smoke_inks)
    return rgba


def chips(rgba, pts, inks=CHIP, size=1) -> np.ndarray:
    h, w = rgba.shape[:2]
    for i, (x, y) in enumerate(pts):
        for yy in range(int(y), int(y) + size):
            for xx in range(int(x), int(x) + size):
                if 0 < xx < w - 1 and 0 < yy < h - 1:
                    rgba[yy, xx, :3] = inks[i % len(inks)]
                    rgba[yy, xx, 3] = 255
    return rgba


def radial_points(cx, cy, n, r0, r1, seed, squash=1.0):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a = 2 * np.pi * (i + rng.random() * 0.8) / n
        rr = r0 + (r1 - r0) * rng.random()
        out.append((cx + rr * np.cos(a), cy + rr * np.sin(a) * squash))
    return out


def spark(w, h, cx, cy, arm, seed=0) -> np.ndarray:
    """A hot star: white core, yellow arms (four long, four short)."""
    rgba = np.zeros((h, w, 4), np.uint8)
    xx, yy = _grid(w, h)
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    rng = np.random.default_rng(seed)
    long_ = ((dx < 0.6) & (dy < arm)) | ((dy < 0.6) & (dx < arm))
    diag = (np.abs(dx - dy) < 0.6) & (dx < arm * 0.55)
    core_ = np.hypot(dx, dy) < 1.3
    t = np.clip(1.0 - np.hypot(dx, dy) / (arm + 0.5), 0, 1) + rng.random((h, w)) * 0.1
    _paint(rgba, long_ | diag | core_, t, SPARK)
    return _clear_border(rgba)


def dust(w, h, cx, cy, r, *, seed=0, thin=0.0, inks=DUST, ring=False) -> np.ndarray:
    """A puff of dust or smoke: lighter on top, ragged, thinning as it ages."""
    xx, yy = _grid(w, h)
    d = np.hypot((xx - cx) / r, (yy - cy) / (r * 0.9))
    if ring:
        d = np.abs(d - 0.65) * 2.4
    n = _noise(w, h, max(2, w // 5), 3, seed)
    shape = 1.0 - d + (n - 0.5) * 0.9
    opaque = shape > 0.15 + thin
    t = np.clip(0.35 + 0.45 * shape - (yy - cy) / (2.2 * r) * 0.6 + (n - 0.5) * 0.3, 0, 1)
    rgba = np.zeros((h, w, 4), np.uint8)
    _paint(rgba, opaque, t, inks)
    return _clear_border(rgba)


def drops(w, h, specs, *, ss=4, inks=BLOOD_INKS, highlight=True, rough=0.0, seed=0) -> np.ndarray:
    """Teardrops: specs = (cx, cy, r, tail_dx, tail_dy). Drawn at ss x then
    reduced by coverage; lit from the top left, a highlight on big drops."""
    W, H = w * ss, h * ss
    xx, yy = _grid(W, H)
    xx, yy = xx / ss, yy / ss
    cover = np.zeros((H, W), bool)
    val = np.zeros((H, W))
    n = _noise(W, H, max(2, w // 2), 2, seed) if rough else None
    for cx, cy, r, tdx, tdy in specs:
        d = np.hypot(xx - cx, yy - cy) / r
        m = d < 1.0 + ((n - 0.5) * rough if n is not None else 0)
        L = np.hypot(tdx, tdy)
        if L > 0:
            ux, uy = tdx / L, tdy / L
            s = (xx - cx) * ux + (yy - cy) * uy
            perp = np.abs(-(xx - cx) * uy + (yy - cy) * ux)
            m |= (s > 0) & (s < L) & (perp < r * (1 - s / L) * 0.9)
        lit = np.clip(0.55 - 0.35 * ((xx - cx) + (yy - cy)) / max(r, 0.5) / 1.4, 0.1, 0.95)
        val = np.where(m & ~cover, lit, val)
        cover |= m
    blk = lambda a: a.reshape(h, ss, w, ss).mean(axis=(1, 3))  # noqa: E731
    cov = blk(cover.astype(float))
    v = blk(val * cover) / np.maximum(cov, 1e-6)
    rgba = np.zeros((h, w, 4), np.uint8)
    _paint(rgba, cov >= 0.45, v * 0.85, inks)
    if highlight:
        for cx, cy, r, _, _ in specs:
            if r >= 1.5:
                hx, hy = int(cx - r * 0.35), int(cy - r * 0.35)
                if rgba[hy, hx, 3]:
                    rgba[hy, hx, :3] = inks[-1]
    return _clear_border(rgba)


def arcs(w, h, cx, base_y, top_y, *, n=5, seed=0, k=1.0, spread=9.0, inks=STEEL_GLOW,
         glow=0.45, sparks=6, rings=0) -> np.ndarray:
    """The teleport column: jagged vertical arcs over a soft glow, sparks
    above; `k` fades the whole (Add: darker reads as more transparent)."""
    rng = np.random.default_rng(seed)
    xx, yy = _grid(w, h)
    F = np.zeros((h, w))
    span = max(1.0, base_y - top_y)
    vert = np.clip((yy - top_y) / span, 0, 1)
    F = np.maximum(F, glow * np.exp(-((xx - cx) / (spread * 0.8)) ** 2) * vert ** 0.7 * (yy <= base_y))
    for _ in range(n):
        x = cx + rng.normal(0, spread * 0.8)
        y0 = int(base_y - rng.integers(0, 4))
        y1 = int(top_y + rng.integers(0, int(span * 0.35) + 1))
        for y in range(y0, y1, -1):
            x += rng.integers(-1, 2) + (cx - x) * 0.03
            xi = int(round(x))
            if 1 <= xi < w - 1 and 1 <= y < h - 1:
                F[y, xi] = max(F[y, xi], 1.0)
                F[y, xi - 1] = max(F[y, xi - 1], 0.5)
                F[y, xi + 1] = max(F[y, xi + 1], 0.5)
    for _ in range(sparks):
        x = int(cx + rng.normal(0, spread))
        y = int(top_y + rng.random() * span * 0.8)
        if 1 <= x < w - 1 and 1 <= y < h - 1:
            F[y, x] = max(F[y, x], 0.85)
    for j in range(rings):
        ry = top_y + span * (0.15 + 0.7 * (j + 0.5) / rings) + rng.normal(0, 1)
        e = np.abs(np.hypot((xx - cx) / spread, (yy - ry) / (spread * 0.28)) - 1.0)
        F = np.maximum(F, np.where(e < 0.16, 0.9, 0.0))
    F = F * k
    rgba = np.zeros((h, w, 4), np.uint8)
    _paint(rgba, F > 0.1, (F - 0.1) / 0.9, inks)
    return _clear_border(rgba)


# ============================================================ rig solids
M = core.Mat.on_ramp
MATS: dict[str, core.Mat] = dict(core.MATERIALS)
_NEW_MATS = {
    "fx_olive": M("military_green", 2, 13, shift=False),
    "fx_olive_dark": M("military_green", 0, 9, black_floor=True, shift=False),
    "fx_steel": M("steel_blue", 2, 14, shift=False),
    "fx_steel_dark": M("steel_blue", 0, 9, black_floor=True, shift=False),
    "fx_khaki": M("khaki_olive", 3, 14, shift=False),
    "fx_red": M("flag_red", 2, 12, shift=False),
    "fx_red_drum": M("flag_red", 1, 11, shift=False),
    "fx_cream": M("plaster_warm", 8, 15, shift=False),
    "fx_yellow": M("hazard_yellow", 6, 14, shift=False),
    "fx_brass": M("hazard_yellow", 3, 11, shift=False),
    "fx_wood": M("rust_brown", 2, 10, shift=False),
    "fx_iron": M("concrete_cold", 2, 14, black_floor=True, shift=False),
    "fx_green_enamel": M("military_green", 3, 14, shift=False),
    "fx_wet": M("steel_blue", 0, 4, black_floor=True, shift=False),
    "fx_flame_out": core.Mat((("flag_red", 13, 15), ("rust_brown", 13, 15), ("hazard_yellow", 12, 12)), flat=True,
                             shift=False),
    "fx_flame_in": core.Mat((("hazard_yellow", 12, 15), ("cream_yellow", 15, 15)), flat=True, shift=False),
    "fx_flame_core": core.Mat((("cream_yellow", 14, 15), ("white",)), flat=True, shift=False),
    "fx_shade_glow": core.Mat((("plaster_warm", 11, 15), ("cream_yellow", 13, 15)), flat=True, shift=False),
    "fx_globe": core.Mat((("cream_yellow", 10, 15), ("white",)), flat=True, shift=False),
    "fx_bulb": core.Mat((("cream_yellow", 14, 15), ("white",)), flat=True, shift=False),
}
for _n, _m in _NEW_MATS.items():
    core.register_material(_n, _m, MATS)

V = core.V
PROJ_CV = core.Canvas(72, 24, 36, 24)   # axis at the centre: rotations 6-8 are mirrors
PROJ_Y = 12.0                           # model height that lands on the canvas centre
PROJ_GRAB = (36, 16)                    # centre 4 px above the actor's z (hitbox 8 high), as MISL A
PROJ_SCALE = 1.35                       # Doom draws missiles larger than life (MISL A3 is 37 px long)
BARREL_CV = core.Canvas(32, 40, 16, 37)
BARREL_GRAB = (16, 35)                  # sinks 2 px, as BAR1 (32 high, top 30)
LAMP_CV = core.Canvas(30, 60, 15, 57)
LAMP_GRAB = (15, 54)                    # sinks 3 px, as COLU (48 high, top 45)


def _flame_tail(z_tail: float, size: float, plume: float = 1.0) -> list:
    E = core.ellipsoid
    y = PROJ_Y
    return [E("fx_flame_out", 0.9, (0, y, z_tail - 4.0 * plume), (size * 1.2, size * 1.2, 4.8 * plume)),
            E("fx_flame_in", 0.9, (0, y, z_tail - 2.2 * plume), (size * 0.9, size * 0.9, 2.8 * plume)),
            E("fx_flame_core", 0.95, (0, y, z_tail - 0.7), (size * 0.6, size * 0.6, 1.3))]


def _scaled(prims: list, k: float = PROJ_SCALE) -> list:
    """The model scaled by k about the projectile's axis point."""
    c = V(0, PROJ_Y, 0)
    for p in prims:
        p.a = c + (np.asarray(p.a, float) - c) * k
        if p.b is not None:
            p.b = c + (np.asarray(p.b, float) - c) * k
        p.r = np.asarray(p.r, float) * k
        p.r1, p.r2, p.h = p.r1 * k, p.r2 * k, p.h * k
    return prims


def _fins(z: float, span: float, mat: str) -> list:
    y = PROJ_Y
    return [core.box(mat, 0.5, (0, y, z), (span, 0.35, 1.3)), core.box(mat, 0.5, (0, y, z), (0.35, span, 1.3))]


def pg7_model(opt: str) -> list:
    """The PG-7V: the fat 85 mm warhead with its ogive, the thin motor, the
    fin cross, the motor's flame. Nose to +z (rotation 1 faces you)."""
    y = PROJ_Y
    rc = core.rcone
    if opt == "C":       # tracer comet: almost all flame
        return [core.ellipsoid("fx_flame_out", 0.6, (0, y, -3), (2.8, 2.8, 9.0)),
                core.ellipsoid("fx_flame_in", 0.7, (0, y, 0), (1.9, 1.9, 6.0)),
                core.ellipsoid("fx_flame_core", 0.8, (0, y, 3), (1.3, 1.3, 2.6)),
                rc("fx_olive_dark", 0.5, (0, y, 4), (0, y, 8), 1.6, 0.6)]
    head = "fx_olive" if opt == "A" else "fx_steel"
    P = [rc(head, 0.75, (0, y, 13.0), (0, y, 8.0), 0.5, 3.2),
         rc(head, 0.62, (0, y, 8.0), (0, y, 4.5), 3.2, 3.2),
         rc("fx_steel_dark", 0.45, (0, y, 4.5), (0, y, 2.5), 2.8, 1.4),
         rc("fx_steel", 0.5, (0, y, 2.5), (0, y, -7.0), 1.4, 1.4),
         *_fins(-7.5, 3.0, "fx_steel_dark")]
    return P + _flame_tail(-8.6, 1.7, plume=1.0 if opt == "A" else 1.8)


def katyusha_model(opt: str) -> list:
    """The hand Katyusha's rocket: slim and long, a red band, a fin cross."""
    y = PROJ_Y
    rc = core.rcone
    if opt == "C":
        return [core.ellipsoid("fx_flame_out", 0.6, (0, y, -2), (2.0, 2.0, 11.0)),
                core.ellipsoid("fx_flame_in", 0.7, (0, y, 1), (1.3, 1.3, 7.0)),
                core.ellipsoid("fx_flame_core", 0.8, (0, y, 4), (0.9, 0.9, 3.0))]
    body, nose = ("fx_steel", "fx_steel_dark") if opt == "A" else ("fx_khaki", "fx_cream")
    P = [rc(nose, 0.7, (0, y, 13.5), (0, y, 9.0), 0.4, 1.9),
         rc(body, 0.6, (0, y, 9.0), (0, y, -7.5), 1.9, 1.9),
         *_fins(-7.0, 2.8, "fx_steel_dark")]
    if opt == "A":
        P.insert(1, rc("fx_red", 0.7, (0, y, 6.2), (0, y, 4.4), 2.05, 2.05))
    return P + _flame_tail(-8.8, 1.5)


def render_projectile(kind: str, opt: str, rotation: int) -> np.ndarray:
    prims = _scaled(pg7_model(opt) if kind == "pg7" else katyusha_model(opt))
    return core.render(prims, rotation, PROJ_CV, MATS, seed=SEED, what=f"{kind}{opt}{rotation}")


def projectile_rotations(kind: str, opt: str) -> dict[int, np.ndarray]:
    """Rotations 1-5 traced, 6-8 their mirrors, as the engine draws them."""
    out = {r: render_projectile(kind, opt, r) for r in range(1, 6)}
    for r, src in core.MIRRORED.items():
        out[r] = core.mirror_sprite(out[src], PROJ_CV)
    return dict(sorted(out.items()))


DRUM_STYLE = {   # body, band, hoop
    "A": ("fx_red_drum", "fx_cream", "fx_red_drum"),       # red fuel drum, cream band
    "B": ("fx_olive", "fx_yellow", "fx_olive_dark"),       # 4BO green drum, yellow band
    "C": ("fx_steel", "fx_red", "fx_steel_dark"),          # bare steel drum, red band
}


def drum_model(opt: str, frame: str = "A", bulge: float = 0.0) -> list:
    """A 200-litre drum (0.88 x 0.58 m: 28 x 19 units), two rolling hoops,
    a painted band, the bung on the lid. B: a drop of fuel runs down from
    the bung; `bulge` swells it (BEXP B)."""
    body, band, hoop = DRUM_STYLE[opt]
    cc = core.ccone
    r = 9.5 + bulge
    P = [cc(body, 0.55, 0.0, 14.0, 9.3, r), cc(body, 0.55, 14.0, 28.0, r, 9.3),
         cc(hoop, 0.62, 8.6, 9.8, r * 0.98 + 0.6, r * 0.98 + 0.6),
         cc(hoop, 0.62, 18.2, 19.4, r * 0.98 + 0.6, r * 0.98 + 0.6),
         cc(hoop, 0.6, 0.0, 1.0, 9.8, 9.8), cc(hoop, 0.66, 27.2, 28.4, 9.8, 9.8),
         cc("fx_iron", 0.45, 27.8, 28.2, 9.0, 9.0),
         cc("fx_iron", 0.65, 28.2, 29.4, 1.5, 1.5, x=4.2, z=2.0),
         cc(band, 0.62, 12.2, 15.6, r + 0.15, r + 0.15)]
    if frame == "B":
        P.append(core.box("fx_wet", 0.3, (3.6, 23.2, 8.7), (0.55, 4.6, 0.6), rnd=0.3))
        P.append(core.ellipsoid("fx_wet", 0.5, (3.6, 18.0, 9.2), (0.9, 1.2, 0.8)))
    elif frame == "A":
        P.append(core.box("fx_wet", 0.3, (3.6, 26.0, 8.9), (0.55, 1.8, 0.6), rnd=0.3))
    return P


def render_drum(opt: str, frame: str = "A", bulge: float = 0.0, extra: list | None = None) -> np.ndarray:
    return core.render(drum_model(opt, frame, bulge) + (extra or []), 0, BARREL_CV, MATS, seed=SEED,
                       what=f"drum{opt}{frame}")


def lamp_model(opt: str) -> list:
    """A Soviet standing lamp, 48 units tall (COLU's height)."""
    cc, rc, E = core.ccone, core.rcone, core.ellipsoid
    if opt == "A":       # the torshier: tripod, brass pole, glowing cloth shade
        P = [rc("fx_wood", 0.5, (0, 9, 0), (s * 6.5, 0.6, c * 6.5), 0.7, 0.5)
             for s, c in ((0.0, 1.0), (0.87, -0.5), (-0.87, -0.5))]
        P += [cc("fx_brass", 0.6, 8.0, 10.0, 1.4, 1.1), rc("fx_brass", 0.62, (0, 9, 0), (0, 37, 0), 0.6, 0.6),
              cc("fx_shade_glow", 0.75, 36.0, 47.5, 8.2, 5.6),
              cc("fx_wood", 0.45, 35.6, 36.6, 8.4, 8.4), cc("fx_wood", 0.45, 47.0, 48.0, 5.8, 5.8),
              E("fx_bulb", 0.9, (0, 37.4, 0), (2.2, 1.0, 2.2))]
        return P
    if opt == "B":       # milk-glass globe on a cast-iron standard
        return [cc("fx_iron", 0.45, 0.0, 2.2, 6.5, 5.0), cc("fx_iron", 0.5, 2.2, 5.0, 2.6, 1.4),
                rc("fx_iron", 0.6, (0, 5, 0), (0, 38, 0), 0.8, 0.8),
                cc("fx_brass", 0.6, 37.5, 40.0, 1.6, 2.6),
                E("fx_globe", 0.8, (0, 44.5, 0), (5.6, 5.6, 5.6))]
    # C: the factory lamp, green enamel reflector over a bare bulb
    return [cc("fx_iron", 0.45, 0.0, 2.5, 7.0, 6.0), rc("fx_iron", 0.6, (0, 2, 0), (0, 42, 0), 1.0, 1.0),
            cc("fx_green_enamel", 0.65, 40.5, 47.5, 8.5, 1.8),
            cc("fx_iron", 0.5, 47.0, 49.0, 1.5, 1.2),
            E("fx_bulb", 0.9, (0, 40.0, 0), (2.4, 2.0, 2.4))]


def render_lamp(opt: str) -> np.ndarray:
    return core.render(lamp_model(opt), 0, LAMP_CV, MATS, seed=SEED, what=f"lamp{opt}")


# ============================================================ frames
# Each returns (RGBA, (grab x, grab y)). Canvas sizes follow Freedoom's for
# scale (MISL B-D 73-91 px wide, PUFF up to 17, TFOG 50 x 60 standing on
# the floor, BEXP C-E standing on the floor).
BURST_W, BURST_H, BURST_GRAB = 92, 84, (46, 55)
BURST_STEPS = {"A": (19.0, 1.0, 0.0), "B": (28.0, 0.9, 0.3), "C": (32.0, 0.6, 0.5)}    # radius, heat, smoke


def burst_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    r, heat, smoke = BURST_STEPS[frame]
    s = SEED + 10 * "ABC".index(frame)
    cx, cy = BURST_W / 2, BURST_H / 2 + 2
    if opt == "A":       # dirty fireball: TNT's orange and black smoke
        img = fireball(BURST_W, BURST_H, cx, cy, r, heat=heat, smoke=smoke, seed=s, up=1.25,
                       smoke_inks=DARK_SMOKE)
        if frame != "A":
            chips(img, radial_points(cx, cy, 6 + 4 * "ABC".index(frame), r * 0.9, r * 1.2, s), size=2)
    elif opt == "B":     # white flash and concrete dust
        img = fireball(BURST_W, BURST_H, cx, cy, r * 0.95, heat=min(1.0, heat + 0.25), smoke=smoke * 0.8,
                       seed=s, up=1.1, smoke_inks=DUST)
        chips(img, radial_points(cx, cy, 10 + 5 * "ABC".index(frame), r * 0.8, r * 1.25, s + 3), size=2)
    else:                # flak ring: a bright core and a shock ring of sparks
        img = fireball(BURST_W, BURST_H, cx, cy, r, heat=heat, smoke=smoke, seed=s, ring=0.6, turb=0.5)
        fireball(BURST_W, BURST_H, cx, cy, r * 0.45, heat=heat, smoke=1.0 if frame == "C" else 0.0,
                 seed=s + 5, base=img)
        chips(img, radial_points(cx, cy, 14, r * 1.05, r * 1.25, s + 4), inks=SPARK[:2])
    return _clear_border(img), BURST_GRAB


FLAME_W, FLAME_H, FLAME_GRAB = 30, 28, (15, 18)
FIRE_ADD = FIRE[2:]             # under Add the darkest reds add almost nothing
FLAMEX_W, FLAMEX_H, FLAMEX_GRAB = 44, 42, (22, 30)
FLAMEX_STEPS = {"A": (6.5, 1.0, 0.12), "B": (9.5, 0.95, 0.12), "C": (12.5, 0.8, 0.14),
                "D": (13.5, 0.6, 0.22), "E": (12.5, 0.4, 0.32)}   # radius, heat, cut


def flame_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    """SDFJ A-B: the burning gob in flight (Add, alpha 0.85, Bright)."""
    s = SEED + 100 + "AB".index(frame) * 7
    w, h, cx, cy = FLAME_W, FLAME_H, FLAME_W / 2, FLAME_H / 2 + 2
    if opt == "A":
        img = fireball(w, h, cx, cy, 8.0, heat=1.0, seed=s, up=1.5, turb=0.9, fire=FIRE_ADD)
    elif opt == "B":
        img = fireball(w, h, cx, cy + 3, 6.5, heat=0.95, seed=s, up=2.6, turb=1.2, cut=0.18, fire=FIRE_ADD)
    else:
        img = np.zeros((h, w, 4), np.uint8)
        rng = np.random.default_rng(s)
        for _ in range(4):
            fireball(w, h, cx + rng.normal(0, 4), cy + rng.normal(0, 3.5), 3.8, heat=0.95,
                     seed=int(rng.integers(1 << 30)), up=1.4, base=img, fire=FIRE_ADD)
    return _clear_border(img), FLAME_GRAB


def flamex_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    """SDFX A-E: the gob bursts on what it hits, flares and dies to embers."""
    r, heat, cut = FLAMEX_STEPS[frame]
    s = SEED + 200 + "ABCDE".index(frame) * 11
    w, h = FLAMEX_W, FLAMEX_H
    up = {"A": 1.5, "B": 2.4, "C": 1.8}.get(opt, 1.5)
    img = fireball(w, h, w / 2, h / 2 + 5, r, heat=heat, seed=s, up=up, turb=0.9 + 0.15 * "ABCDE".index(frame),
                   cut=cut, fire=FIRE_ADD)
    if frame in "DE":
        chips(img, radial_points(w / 2, h / 2, 8, r * 0.7, r * 1.25, s, squash=0.8), inks=SPARK[:2])
    return _clear_border(img), FLAMEX_GRAB


PUFF_W, PUFF_H, PUFF_GRAB = 20, 18, (10, 11)
PUFF_STEPS = {"B": (4.5, 0.0), "C": (6.0, 0.06), "D": (7.4, 0.16)}    # radius, thinning


def puff_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    """PUFF A the spark (Bright), B-D the dust rising and thinning. The
    engine draws it Translucent 0.5 (BulletPuff)."""
    s = SEED + 300 + "ABCD".index(frame) * 13
    w, h, cx, cy = PUFF_W, PUFF_H, PUFF_W / 2, PUFF_H / 2 + 1
    if frame == "A":
        if opt == "B":
            img = dust(w, h, cx, cy, 2.6, seed=s, inks=_inks(("cream_yellow", 12), ("cream_yellow", 15), "white"))
        else:
            img = spark(w, h, cx, cy, 3.6 if opt == "A" else 2.6, seed=s)
        return img, PUFF_GRAB
    r, thin = PUFF_STEPS[frame]
    if opt == "A":
        img = dust(w, h, cx, cy, r, seed=s, thin=thin)
        chips(img, radial_points(cx, cy, 2 + "BCD".index(frame), r + 0.5, r + 2.0, s))
    elif opt == "B":
        img = dust(w, h, cx, cy, r, seed=s, thin=thin, inks=PALE, ring=frame == "D")
    else:
        img = dust(w, h, cx, cy, r * 0.75, seed=s, thin=thin + 0.1)
        chips(img, radial_points(cx, cy, 5 + 2 * "BCD".index(frame), r * 0.6, r + 2.5, s + 1), size=1)
    return _clear_border(img), PUFF_GRAB


# Blood: the engine plays C, B, A (8 tics each), starting later for small
# hits; it falls (no NOGRAVITY). C the spurt, B the drops stretching as
# they fall, A the spatter spreading at the end.
BLOOD_CANVAS = {"C": (12, 12, (6, 7)), "B": (16, 16, (8, 9)), "A": (22, 14, (11, 8))}
BLOOD_SPECS = {
    "A": {"C": [(6, 6, 2.6, 0, -2.5), (3.2, 4.0, 1.0, 0, 0), (8.8, 3.6, 0.9, 0, 0)],
          "B": [(8, 7, 2.2, 0, -3.2), (4.4, 5.6, 1.3, -0.6, -2.0), (11.6, 6.0, 1.2, 0.6, -2.2),
                (7.0, 12.0, 0.9, 0, 0)],
          "A": [(11, 8, 2.0, 0, -1.6), (6, 7.4, 1.4, -1.2, -0.6), (16, 7.2, 1.4, 1.4, -0.6),
                (3, 9.6, 0.9, 0, 0), (19, 9.4, 0.9, 0, 0), (8.6, 11, 0.8, 0, 0), (13.6, 10.8, 0.9, 0, 0)]},
}


def _spray_specs(frame: str, w: int, h: int, seed: int, n: int, rmax: float) -> list:
    rng = np.random.default_rng(seed)
    spread = {"C": 0.45, "B": 0.7, "A": 1.0}[frame]
    out = [(w / 2, h / 2, rmax, 0, -rmax)]
    for _ in range(n):
        out.append((w / 2 + rng.normal(0, w * 0.22 * spread), h / 2 + rng.normal(0, h * 0.18 * spread),
                    0.6 + rng.random() * rmax * 0.4, 0, 0))
    return out


def blood_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    w, h, grab = BLOOD_CANVAS[frame]
    s = SEED + 400 + "ABC".index(frame) * 17
    if opt == "A":
        img = drops(w, h, BLOOD_SPECS["A"][frame], seed=s)
    elif opt == "B":
        img = drops(w, h, _spray_specs(frame, w, h, s, {"C": 5, "B": 8, "A": 12}[frame], 1.6), seed=s,
                    highlight=False)
    else:
        big = {"C": [(6, 6, 3.4, 0, -1.6)],
               "B": [(8, 8, 3.6, 0, -2.4), (4.5, 11.5, 1.6, 0, 0)],
               "A": [(11, 7.5, 3.4, 0, -1.0), (5.4, 8.6, 2.0, 0, 0), (16.6, 8.8, 2.2, 0, 0)]}[frame]
        img = drops(w, h, big, seed=s, rough=0.6, inks=BLOOD_INKS[:6])
    return img, grab


def blood_tint(rgba: np.ndarray, colour=BLOOD_COLOUR) -> np.ndarray:
    """What BloodColor does to a drop: each colour becomes the blood colour
    scaled by the colour's brightest channel (GZDoom's blood translation,
    r_translate.cpp CreateBloodTranslation, read from memory: NOT VERIFIED
    against our engine; the result is then snapped to the game palette)."""
    out = rgba.copy()
    b = rgba[..., :3].max(axis=-1).astype(np.float64) / 255.0
    for c in range(3):
        out[..., c] = np.rint(colour[c] * b).astype(np.uint8)
    out[rgba[..., 3] == 0] = 0
    return out


TFOG_W, TFOG_H, TFOG_GRAB = 52, 64, (26, 60)
IFOG_W, IFOG_H, IFOG_GRAB = 40, 48, (20, 38)
# A and B flicker at full strength, C-J rise, thin and fade.
TFOG_FADE = dict(zip("ABCDEFGHIJ", (1.0, 1.0, 0.92, 0.82, 0.7, 0.58, 0.46, 0.34, 0.24, 0.15)))
IFOG_FROM_TFOG = dict(zip("ABCDE", "ABEGI"))


def fog_frame(opt: str, frame: str, kind: str = "tfog") -> tuple[np.ndarray, tuple[int, int]]:
    tf = frame if kind == "tfog" else IFOG_FROM_TFOG[frame]
    w, h, grab = (TFOG_W, TFOG_H, TFOG_GRAB) if kind == "tfog" else (IFOG_W, IFOG_H, IFOG_GRAB)
    i = "ABCDEFGHIJ".index(tf)
    k = TFOG_FADE[tf]
    s = SEED + 500 + i * 19 + (0 if kind == "tfog" else 1000)
    base = h - 3
    top = 4 + i * 2.6 if kind == "tfog" else 3 + i * 2.0
    lift = max(0, i - 2) * (2.2 if kind == "tfog" else 1.6)
    if opt == "A":       # Tesla arcs: the invaders' machinery
        img = arcs(w, h, w / 2, base - lift, top, n=max(2, 7 - i // 2), seed=s, k=k, spread=w * 0.2,
                   sparks=4 + i, glow=0.28)
    elif opt == "B":     # smoke and sparks, warm
        img = fireball(w, h, w / 2, base - h * 0.33 - lift, w * 0.3, heat=0.75 * k, smoke=0.0, seed=s,
                       up=2.0, turb=1.1, cut=0.12 + 0.3 * (1 - k))
        chips(img, radial_points(w / 2, base - h * 0.45 - lift, 6 + i, w * 0.1, w * 0.4, s, squash=1.6),
              inks=SPARK[:2])
        img = _clear_border(img)
    else:                # radio rings rising round a beam
        img = arcs(w, h, w / 2, base - lift, top, n=0, seed=s, k=k, spread=w * 0.3, inks=CREAM_GLOW,
                   glow=0.35, sparks=0, rings=4)
    return img, grab


BEXP_CANVAS = {"C": (44, 48, (22, 46)), "D": (60, 58, (30, 56)), "E": (64, 62, (32, 60))}


def barrel_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    return render_drum(opt, frame), BARREL_GRAB


def bexp_frame(opt: str, frame: str) -> tuple[np.ndarray, tuple[int, int]]:
    """BEXP A the drum as it is hit (Bright: the engine lights it fully), B
    the drum swelling with fire at the bung, C-E the fireball standing on
    the floor, pieces of the drum thrown out on D."""
    if frame == "A":
        return render_drum(opt, "A"), BARREL_GRAB
    if frame == "B":
        y = 29.0
        jet = [core.ellipsoid("fx_flame_out", 0.6, (4.2, y + 3.4, 2.0), (2.6, 4.2, 2.6)),
               core.ellipsoid("fx_flame_in", 0.7, (4.2, y + 1.8, 2.0), (1.5, 2.4, 1.5)),
               core.ellipsoid("fx_flame_out", 0.55, (-9.6, 14.0, 2.0), (1.0, 2.6, 1.0)),
               core.ellipsoid("fx_flame_out", 0.55, (9.6, 20.0, 2.0), (1.0, 2.0, 1.0))]
        return render_drum(opt, "C_none", bulge=0.8, extra=jet), BARREL_GRAB
    w, h, grab = BEXP_CANVAS[frame]
    step = "CDE".index(frame)
    s = SEED + 600 + step * 23
    heat, smoke = (1.0, 0.0) if frame == "C" else ((0.9, 0.28) if frame == "D" else (0.6, 0.5))
    r = (13.0, 20.0, 23.0)[step]
    img = fireball(w, h, w / 2, h - r * 0.95, r, heat=heat, smoke=smoke, seed=s, up=1.35, smoke_inks=DARK_SMOKE)
    if frame == "D":
        body_ink = MATS[DRUM_STYLE[opt][0]].colours()
        chips(img, radial_points(w / 2, h - r, 7, r * 0.9, r * 1.25, s, squash=0.8),
              inks=[body_ink[3], body_ink[6], (0, 0, 0)], size=2)
    return _clear_border(img), grab


def lamp_frame(opt: str, frame: str = "A") -> tuple[np.ndarray, tuple[int, int]]:
    return render_lamp(opt), LAMP_GRAB


def proj_frame(kind: str):
    def f(opt: str, frame: str, rotation: int = 3):
        return render_projectile(kind, opt, rotation), PROJ_GRAB
    return f


FRAME_FN = {
    "pg7": proj_frame("pg7"), "katyusha": proj_frame("katyusha"), "burst": burst_frame,
    "flame": flame_frame, "flamex": flamex_frame, "puff": puff_frame, "blood": blood_frame,
    "tfog": lambda o, f: fog_frame(o, f, "tfog"), "ifog": lambda o, f: fog_frame(o, f, "ifog"),
    "barrel": barrel_frame, "bexp": bexp_frame, "lamp": lamp_frame,
}

# ============================================================ the sweep
@dataclass(frozen=True)
class Option:
    letter: str
    name: str
    why: str


# Nine items reviewed as options; flamex rides with flame, ifog with tfog
# and bexp with the barrel (the same drawing carries on).
SWEEP: dict[str, tuple[str, tuple[Option, ...], str]] = {
    "pg7": ("A", (
        Option("A", "olive warhead", "the PG-7V as a soldier knows it: fat green warhead, thin motor, fins, "
               "a short yellow-white plume"),
        Option("B", "steel warhead, long plume", "the same round unpainted, the plume twice as long"),
        Option("C", "tracer comet", "almost all flame: reads at range, but nothing says RPG")), "rotation 3 (side)"),
    "katyusha": ("A", (
        Option("A", "steel body, red band", "slim and long, a red identification band: unlike the PG-7V's "
               "silhouette at a glance, six of them fan out together"),
        Option("B", "khaki body, white nose", "a period paint scheme, softer against concrete"),
        Option("C", "tracer streak", "only the motor's fire")), "rotation 3 (side)"),
    "burst": ("A", (
        Option("A", "dirty fireball", "TNT's orange with black smoke and flying grit; Rocket draws it "
               "Normal, so the smoke shows"),
        Option("B", "white flash, concrete dust", "hotter and cleaner; the dust ties it to the walls"),
        Option("C", "flak ring", "a shock ring of sparks round a core: graphic, less of a weapon")), "frame B"),
    "flame": ("A", (
        Option("A", "fire gob", "a burning ball of fuel with a white heart, flames licking up; Add keeps it "
               "glowing, never plasma-blue"),
        Option("B", "flame tongues", "taller licks, a narrower jet"),
        Option("C", "ember cluster", "four small fires: busier, reads less as one jet")), "SDFJ A, SDFX C"),
    "puff": ("A", (
        Option("A", "spark and concrete dust", "a yellow-white spark (A, Bright) then grey dust with chips "
               "of the wall"),
        Option("B", "pale smoke", "a cream flash and warm smoke, ring at the end"),
        Option("C", "stone chips", "a small spark and more flying chips, less dust")), "frames A and C"),
    "blood": ("A", (
        Option("A", "glossy drops", "fat teardrops with a highlight, few and heavy, like Blood's; tinted "
               "AD 27 21 by BloodColor"),
        Option("B", "fine spray", "a mist of small drops"),
        Option("C", "heavy gouts", "clotted blobs, darker")), "frame B, drawn and tinted"),
    "tfog": ("A", (
        Option("A", "Tesla arcs", "jagged arcs over a pale glow, the invaders' machinery; steel-blue and "
               "white, not the portal's cobalt"),
        Option("B", "smoke and sparks", "warm, a churning fire column"),
        Option("C", "radio rings", "cream rings rising round a beam: clean, a little sci-fi")), "frame A"),
    "barrel": ("A", (
        Option("A", "red fuel drum", "a red 200-litre fuel drum with a cream band: says flammable at once and "
               "matches the factory's brick and rust; warm against MAP01's cold concrete"),
        Option("B", "4BO green drum", "army green with a yellow band: Soviet, but it melts into the 4BO "
               "doors and crates"),
        Option("C", "grey steel drum", "bare steel, red band: honest, but grey on grey in MAP01")),
               "BAR1 A, BEXP D"),
    "lamp": ("A", (
        Option("A", "torshier", "the Soviet home floor lamp: tripod, brass pole, a glowing cloth shade"),
        Option("B", "milk-glass globe", "a cast-iron standard with a frosted globe, a club-room lamp"),
        Option("C", "factory lamp", "green enamel reflector over a bare bulb: the light hides under it")),
             "COLU A"),
}
SWEEP_FRAMES = {   # the key frame(s) shown per item
    "pg7": [("pg7", "A")], "katyusha": [("katyusha", "A")], "burst": [("burst", "B")],
    "flame": [("flame", "A"), ("flamex", "C")], "puff": [("puff", "A"), ("puff", "C")],
    "blood": [("blood", "B")], "tfog": [("tfog", "A")], "barrel": [("barrel", "A"), ("bexp", "D")],
    "lamp": [("lamp", "A")],
}
# The option each full-set sprite is drawn in.
OPTION_OF = {"pg7": "pg7", "katyusha": "katyusha", "burst": "burst", "flame": "flame", "flamex": "flame",
             "puff": "puff", "blood": "blood", "tfog": "tfog", "ifog": "tfog", "barrel": "barrel",
             "bexp": "barrel", "lamp": "lamp"}


def recommended(key: str) -> str:
    return SWEEP[OPTION_OF[key]][0]


# ============================================================ lumps
def lump_names(e: Effect) -> list[str]:
    if e.rotated:
        out = []
        for f in e.frames:
            out += [f"{e.sprite}{f}1", f"{e.sprite}{f}2{f}8", f"{e.sprite}{f}3{f}7", f"{e.sprite}{f}4{f}6",
                    f"{e.sprite}{f}5"]
        return out
    return [f"{e.sprite}{f}0" for f in e.frames]


def all_lumps() -> list[str]:
    return [n for e in EFFECTS for n in lump_names(e)]


def render_set(key: str, opt: str | None = None) -> dict[str, tuple[np.ndarray, tuple[int, int]]]:
    """Every lump of one sprite in its recommended option: name -> (RGBA, grAb)."""
    e = BY_KEY[key]
    opt = opt or recommended(key)
    out = {}
    if e.rotated:
        rots = {r: render_projectile(key, opt, r) for r in range(1, 6)}
        for name, r in zip(lump_names(e), range(1, 6)):
            out[name] = (rots[r], PROJ_GRAB)
        return out
    for f, name in zip(e.frames, lump_names(e)):
        out[name] = FRAME_FN[key](opt, f)
    return out


def save_lump(rgba: np.ndarray, grab: tuple[int, int], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *grab))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


# ============================================================ scenes
def texture_rgb(name: str) -> np.ndarray:
    hits = sorted((PROJECT_ROOT / "assets").rglob(f"{name}.png"))
    if not hits:
        raise FileNotFoundError(name)
    with Image.open(hits[0]) as im:
        return np.asarray(im.convert("RGB"), np.uint8)


def _tile(rgb: np.ndarray, w: int, h: int) -> np.ndarray:
    reps = (h // rgb.shape[0] + 1, w // rgb.shape[1] + 1, 1)
    return np.tile(rgb, reps)[:h, :w].copy()


SCENES = (("MAP01 corridor", "SDCONC1", "SDFLR2", 128), ("MAP03 factory", "SDBRCK1", "SDFLR4", 144))
SCENE_W, SCENE_WALL, SCENE_FLOOR = 320, 112, 40
SCENE_FLOOR_ROW = SCENE_WALL + 18            # where an actor at floor height stands


def backdrop(wall: str, floor: str, light: int, w: int = SCENE_W) -> np.ndarray:
    top = _tile(texture_rgb(wall), w, SCENE_WALL)
    fl = _tile(texture_rgb(floor), w, SCENE_FLOOR * 3)
    fl = np.asarray(Image.fromarray(fl).resize((w, SCENE_FLOOR), Image.Resampling.NEAREST))
    return core.lit(np.concatenate([top, fl], axis=0), light).copy()


def composite(bg: np.ndarray, rgba: np.ndarray, x0: int, y0: int, style: str, alpha: float,
              light_f: float = 1.0) -> np.ndarray:
    """Draw a sprite onto an RGB image the engine's way, near enough:
    Normal replaces, Translucent mixes at alpha, Add adds at alpha. A
    stand-in, NOT VERIFIED against GZDoom's blending or its light tables."""
    h, w = rgba.shape[:2]
    H, W = bg.shape[:2]
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    ty, tx = ys + y0, xs + x0
    k = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
    ys, xs, ty, tx = ys[k], xs[k], ty[k], tx[k]
    src = rgba[ys, xs, :3].astype(np.float64) * light_f
    dst = bg[ty, tx].astype(np.float64)
    if style == "Add":
        out = dst + src * alpha
    elif style == "Translucent":
        out = dst * (1 - alpha) + src * alpha
    else:
        out = src
    bg[ty, tx] = np.clip(out, 0, 255).astype(np.uint8)
    return bg


def place(bg, rgba, grab, x, z, e: Effect, frame: str, light: int, blood=False):
    """Stand a sprite at column x, z units above the floor, by its grAb."""
    if blood:
        rgba = blood_tint(rgba)
    f = 1.0 if frame in e.bright else min(1.0, light / 224)
    return composite(bg, rgba, int(x - grab[0]), int(SCENE_FLOOR_ROW - z - grab[1]), e.style, e.alpha, f)


def scene_image(full: dict, wall: str, floor: str, light: int) -> np.ndarray:
    """The recommended set at 1x: lamp, drums, a drum going up, a PG-7V
    leaving (rotation 5) and one passing (3), a burst, the flame, puffs on
    the wall, blood, and the General's fog."""
    bg = backdrop(wall, floor, light)
    g = lambda key, lump: full[key][lump]  # noqa: E731
    E = BY_KEY
    items = [("lamp", "COLUA0", "A", 18, 0), ("barrel", "BAR1A0", "A", 44, 0), ("barrel", "BAR1B0", "B", 64, 0),
             ("bexp", "BEXPD0", "D", 96, 0), ("puff", "PUFFA0", "A", 128, 46), ("puff", "PUFFC0", "C", 140, 30),
             ("pg7", "SDPGA5", "A", 150, 34), ("pg7", "SDPGA3A7", "A", 176, 44),
             ("burst", "SDPXB0", "B", 214, 8), ("katyusha", "SDKRA5", "A", 252, 40),
             ("flame", "SDFJA0", "A", 262, 22), ("flamex", "SDFXC0", "C", 238, 0),
             ("blood", "BLUDB0", "B", 278, 30), ("tfog", "TFOGA0", "A", 300, 0)]
    for key, lump, frame, x, z in items:
        rgba, grab = g(key, lump)
        place(bg, rgba, grab, x, z, E[key], frame, light, blood=key == "blood")
    return bg


def anim_frames(key: str, full: dict, seq, light: int = 128, wall: str = "SDCONC1") -> list[np.ndarray]:
    """One sequence on a swatch of the corridor wall, at GIF_ZOOM."""
    e = BY_KEY[key]
    lumps = full[key]
    by_frame = {n[4]: lumps[n] for n in lumps}
    w = max(v[0].shape[1] for v in by_frame.values()) + 12
    h = max(v[0].shape[0] for v in by_frame.values()) + 12
    base = core.lit(_tile(texture_rgb(wall), w, h), light).copy()
    out = []
    for f, _ in seq:
        rgba, grab = by_frame[f]
        if e.rotated:
            rgba = lumps[f"{e.sprite}{f}3{f}7"][0]
        if key == "blood":
            rgba = blood_tint(rgba)
        img = composite(base.copy(), rgba, (w - rgba.shape[1]) // 2, (h - rgba.shape[0]) // 2, e.style, e.alpha,
                        1.0 if f in e.bright else light / 224)
        out.append(np.asarray(Image.fromarray(img).resize((w * GIF_ZOOM, h * GIF_ZOOM),
                                                          Image.Resampling.NEAREST)))
    return out


def save_gif(frames: list[np.ndarray], tics: list[int], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ms = [max(20, int(round(t * TIC_MS))) for t in tics]
    try:
        return core.save_gif(frames, ms, path)
    except ValueError:        # Add/Translucent mixes leave the palette: quantise once, shared
        strip = Image.fromarray(np.concatenate(frames, axis=0)).quantize(255, dither=Image.Dither.NONE)
        h = frames[0].shape[0]
        ims = [strip.crop((0, i * h, frames[0].shape[1], (i + 1) * h)) for i in range(len(frames))]
        ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)
        return path


# ============================================================ sheets
def _font(size: int):
    try:
        return ImageFont.truetype(artlib.FONT_SMALL, size)
    except OSError:
        return ImageFont.load_default()


def _zoom(rgb: np.ndarray, z: int) -> Image.Image:
    im = Image.fromarray(rgb)
    return im.resize((im.width * z, im.height * z), Image.Resampling.NEAREST)


def _on_wall(rgba: np.ndarray, e: Effect, frame: str, w: int, h: int, light: int = 128,
             blood: bool = False) -> np.ndarray:
    bg = core.lit(_tile(texture_rgb("SDCONC1"), w, h), light).copy()
    if blood:
        rgba = blood_tint(rgba)
    return composite(bg, rgba, (w - rgba.shape[1]) // 2, (h - rgba.shape[0]) // 2, e.style, e.alpha,
                     1.0 if frame in e.bright else light / 224)


def render_sweep() -> dict:
    """Every option's key frame(s): {(item, letter): [(label, rgba, key, frame), ...]}."""
    out = {}
    for item, (_, opts, _) in SWEEP.items():
        for o in opts:
            cells = []
            for key, frame in SWEEP_FRAMES[item]:
                rgba, _ = FRAME_FN[key](o.letter, frame)
                cells.append((f"{BY_KEY[key].sprite} {frame}", rgba, key, frame))
            out[(item, o.letter)] = cells
    return out


def freedoom_ref(item: str):
    names = {"pg7": "MISLA7A3", "katyusha": "MISLA7A3", "burst": "MISLC0", "flame": "PLSSA0", "puff": "PUFFC0",
             "blood": "BLUDB0", "tfog": "TFOGA0", "barrel": "BAR1A0", "lamp": "COLUA0"}
    r = core.freedoom_sprite(names[item])
    return (names[item], r[0]) if r else None


def sweep_png(sweep: dict, path: Path, scenes: list[tuple[str, np.ndarray]] | None = None) -> Path:
    """The options at 3x on one sheet (the Freedoom sprite being replaced in
    the first column, for scale only), then the 1x scenes."""
    z = SWEEP_ZOOM
    f_title, f_lab = _font(22), _font(14)
    pad, head = 14, 40
    rows = []
    for item, (rec, opts, what) in SWEEP.items():
        cells = []
        ref = freedoom_ref(item)
        if ref:
            e = BY_KEY[SWEEP_FRAMES[item][0][0]]
            ww, hh = ref[1].shape[1] + 8, ref[1].shape[0] + 8
            cells.append((f"Freedoom {ref[0]} (today)", [_zoom(_on_wall(ref[1], e, "A", ww, hh), z)]))
        for o in opts:
            ims = []
            for lab, rgba, key, frame in sweep[(item, o.letter)]:
                e = BY_KEY[key]
                ims.append(_zoom(_on_wall(rgba, e, frame, rgba.shape[1] + 8, rgba.shape[0] + 8,
                                          blood=key == "blood"), z))
            star = "  << recommended" if o.letter == rec else ""
            cells.append((f"{item} {o.letter}: {o.name}{star}", ims))
        rows.append((f"{item} - {what}", cells))
    col_w = []
    for _, cells in rows:
        for i, (_, ims) in enumerate(cells):
            wsum = sum(im.width for im in ims) + 6 * (len(ims) - 1)
            while len(col_w) <= i:
                col_w.append(0)
            col_w[i] = max(col_w[i], wsum, 260)
    width = pad + sum(c + pad for c in col_w)
    heights = [max(max(im.height for im in ims) for _, ims in cells) + head + 22 for _, cells in rows]
    scene_h = sum(s.shape[0] * 2 + 40 for _, s in (scenes or [])) + (40 if scenes else 0)
    sheet = Image.new("RGB", (max(width, SCENE_W * 3 + 2 * pad), 60 + sum(heights) + scene_h), (24, 24, 26))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), "M2c - the player's effects and the world sprites: options at 3x on SDCONC1, light 128",
           fill=(230, 230, 230), font=f_title)
    y = 60
    for (title, cells), hgt in zip(rows, heights):
        d.text((pad, y), title, fill=(250, 208, 40), font=f_lab)
        x = pad
        for i, (lab, ims) in enumerate(cells):
            d.text((x, y + 18), lab, fill=(200, 200, 200), font=f_lab)
            xx = x
            for im in ims:
                sheet.paste(im, (xx, y + head))
                xx += im.width + 6
            x += col_w[i] + pad
        y += hgt
    if scenes:
        d.text((pad, y + 8), "At 1x (and 2x below it): the recommended set in place", fill=(250, 208, 40),
               font=f_lab)
        y += 34
        for name, img in scenes:
            d.text((pad, y), name, fill=(200, 200, 200), font=f_lab)
            sheet.paste(Image.fromarray(img), (pad, y + 18))
            sheet.paste(_zoom(img, 2), (pad + img.shape[1] + pad, y + 18))
            y += img.shape[0] * 2 + 40
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)
    return path


def _uri_png(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return core._uri(buf.getvalue(), "png")


def write_html(path: Path, sweep_path: Path, full: dict, gifs: dict, scenes: list, manifest: dict) -> Path:
    T = core.tile
    secs = []
    # 1. the sweep
    lead = ("Nine items, three options each, one key frame each at 3x on MAP01's concrete at light 128, drawn "
            "in the engine's RenderStyle (Add for the flame and the fog, Translucent 0.5 for the puff, "
            "the blood already tinted AD 27 21). First column: the Freedoom sprite you see today, for scale.")
    rows = []
    for item, (rec, opts, what) in SWEEP.items():
        for o in opts:
            rows.append([html.escape(item), o.letter + (" <b>(recommended)</b>" if o.letter == rec else ""),
                         html.escape(o.name), html.escape(o.why)])
    body = (f'<img class="px" src="{_uri_png(Image.open(sweep_path))}" alt="sweep" style="max-width:100%">'
            + sheetlib.table(["Item", "Option", "Name", "What it is"], rows, numeric_from=99))
    secs.append(("1 · The sweep: options at 3x", lead, body))
    # 2. the full sets
    parts = []
    for e in EFFECTS:
        lumps = full[e.key]
        strip = []
        for name, (rgba, grab) in lumps.items():
            frame = name[4]
            wall = _on_wall(rgba, e, frame, rgba.shape[1] + 6, rgba.shape[0] + 6, blood=e.key == "blood")
            strip.append(T(core.png_uri(wall), wall.shape[1], wall.shape[0], 3, name, f"{rgba.shape[1]}x"
                           f"{rgba.shape[0]} grAb {grab[0]},{grab[1]}"))
            if e.key == "blood":
                strip.append(core.sprite_tile(rgba, 3, f"{name} as drawn", "before BloodColor"))
        if e.rotated:
            rots = projectile_rotations(e.key, recommended(e.key))
            for r in range(1, 9):
                strip.append(core.sprite_tile(rots[r], 2, f"rot {r}", "mirror" if r in core.MIRRORED else ""))
        for label, gp in gifs.get(e.key, []):
            strip.append(core.gif_tile(gp, 1, label, "game speed"))
        head = (f"<h3>{e.sprite} &middot; {html.escape(e.key)} &middot; option {recommended(e.key)} &middot; "
                f"{html.escape(e.style)}{' ' + str(e.alpha) if e.alpha != 1 else ''} &middot; replaces "
                f"{html.escape(e.replaces)}</h3><p class=\"cap\">{html.escape(e.actor)}</p>")
        parts.append(head + '<div class="strip">' + "".join(strip) + "</div>")
    secs.append(("2 · The full set of each recommended option",
                 f"{len(all_lumps())} lumps, every frame the code plays, each PNG with its grAb, written to "
                 "work/art/effects/&lt;SPRITE&gt;/. Tiles at 3x on SDCONC1, GIFs at 35 tics a second.",
                 "".join(parts)))
    # 3. scenes
    sc = "".join(T(core.png_uri(img), img.shape[1], img.shape[0], 1, name, "1x") +
                 T(core.png_uri(img), img.shape[1], img.shape[0], 3, name, "3x") for name, img in scenes)
    secs.append(("3 · At 1x: a MAP01 corridor and the MAP03 factory",
                 "The set stood by its own offsets on SDCONC1/SDFLR2 at light 128 and on SDBRCK1/SDFLR4 at 144. "
                 "Bright frames ignore the light, as in the engine. Blending is a stand-in (NOT VERIFIED).",
                 f'<div class="strip">{sc}</div>'))
    # 4. install plan
    rows = []
    for e in EFFECTS:
        n = len(lump_names(e))
        if e.install == "override":
            how = f"ship as {e.sprite}*.png (the IWAD's own names), no ZScript"
        elif e.key == "burst":
            how = "pg7_grenade.zs and katyusha_rocket.zs Death: MISL B/C/D -> SDPX A/B/C, same tics"
        elif e.key in ("pg7", "katyusha"):
            how = f"Spawn: MISL A -> {e.sprite} A, same tics"
        else:
            how = f"flame_blob.zs: {e.replaces.split()[0]} -> {e.sprite}, letters and tics as they are"
        rows.append([e.sprite, str(n), html.escape(e.install), html.escape(how), html.escape(e.actor)])
    why = "".join(f"<p><b>{k}</b>: {html.escape(v)}</p>" for k, v in INSTALL_WHY.items())
    secs.append(("4 · Install plan (after your OK; nothing is installed yet)",
                 "mod-engineer edits three .zs files; the rest is files under assets/sprites/effects/. "
                 "MOD-SPEC 5.1 (IWAD sprites) and 6.3 (reserved names) and LICENSES.md follow the install.",
                 sheetlib.table(["Sprite", "Lumps", "Method", "Edit", "Actor"], rows, numeric_from=99) + why))
    intro = ("Backlog M2c (D75): the RPG-7's PG-7V, the hand Katyusha's rocket, the ROKS-3's flame, the burst the "
             "rockets share, the bullet puff, the blood's shape, the teleport fog, the barrel and the floor lamp, "
             "drawn by tools/art/gen_effects.py (procedural, palette v1, seed 75). Approve the recommended "
             "options, or name another letter per item.")
    footer = (f"tools/art/gen_effects.py &middot; {manifest['lumps']} lumps &middot; work/art/effects/ &middot; "
              "the engine pass is owed (D26).")
    sheetlib.write_sheet(path, lang="en", title="M2c · Player effects and world sprites",
                         subtitle="F4/M2 · options and the recommended full set", intro=intro,
                         sections=secs, footer=footer)
    css_extra = core.SHEET_CSS
    txt = path.read_text(encoding="utf-8").replace("</style>", css_extra + "</style>", 1)
    path.write_text(txt, encoding="utf-8")
    return path


# ============================================================ main
def build_full(out_dir: Path = OUT_DIR) -> dict:
    full = {}
    for e in EFFECTS:
        full[e.key] = render_set(e.key)
        for name, (rgba, grab) in full[e.key].items():
            save_lump(rgba, grab, out_dir / e.sprite / f"{name}.png")
    return full


def write_gifs(full: dict, out_dir: Path = OUT_DIR) -> dict:
    gifs = {}
    for e in EFFECTS:
        if len(e.frames) < 2 and not e.rotated:
            continue
        for label, seq in e.sequences:
            if e.rotated:
                continue
            frames = anim_frames(e.key, full, seq)
            p = save_gif(frames, [t for _, t in seq], out_dir / "gifs" / f"{e.sprite}_{label.replace(' ', '_')}.gif")
            gifs.setdefault(e.key, []).append((f"{e.sprite} {label}", p))
    return gifs


def manifest_of(full: dict) -> dict:
    return {"generator": "tools/art/gen_effects.py", "seed": SEED, "palette": "v1",
            "lumps": sum(len(v) for v in full.values()),
            "sprites": {e.sprite: {"key": e.key, "option": recommended(e.key), "install": e.install,
                                   "style": e.style, "alpha": e.alpha, "replaces": e.replaces, "actor": e.actor,
                                   "lumps": {n: {"size": [int(r.shape[1]), int(r.shape[0])], "grab": list(g)}
                                             for n, (r, g) in full[e.key].items()}}
                        for e in EFFECTS}}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sweep", action="store_true", help="the options sheet only")
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    a = ap.parse_args(argv)
    sweep = render_sweep()
    for (item, letter), cells in sweep.items():
        for lab, rgba, key, frame in cells:
            save_lump(rgba, (0, 0), OUT_DIR / "sweep" / f"{item}_{letter}_{lab.replace(' ', '')}.png")
    stem = f"{a.stamp}_F4_player-effects"
    if a.sweep:
        print(sweep_png(sweep, OUT_DIR / "sweep" / "sweep.png"))
        return
    full = build_full()
    gifs = write_gifs(full)
    scenes = [(name, scene_image(full, wall, floor, light)) for name, wall, floor, light in SCENES]
    man = manifest_of(full)
    (OUT_DIR / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    png = sweep_png(sweep, PREVIEW_DIR / f"{stem}.png", scenes)
    out = write_html(PREVIEW_DIR / f"{stem}.html", png, full, gifs, scenes, man)
    print(png)
    print(out)
    print(f"{man['lumps']} lumps -> {OUT_DIR}")


if __name__ == "__main__":
    main()
