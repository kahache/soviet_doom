"""The AKM's floor pickup SDAQ A0 (D112; art D116): the rifle lying on its
side, drawn on gen_weapon's rig like every weapon pickup since D48.

    .venv/Scripts/python.exe tools/art/gen_akm_pickup.py     (Windows)
    .venv/bin/python tools/art/gen_akm_pickup.py             (macOS)

Why procedural. The held frames come from the project lead's Gemini image
(tools/art/gemini_frames.py akm), but Gemini drew no pickup and the CEO
saves the quota (2026-10-24); every other weapon pickup is this rig's
(D48, D80: the PPSh-41's SDPQ, the TT-33's SDTP...). So the AKM lies on the
floor as the PPSh does: side view from PICKUP_PITCH above, muzzle to the
left, magazine down, at the PPSh's scale (both rifles are about 88 cm).

What says AKM at 1x, where the PPSh says drum and slotted jacket: the long
curved magazine, the pistol grip, the slanted muzzle brake, the gas tube
over the barrel and the stock dropping from the receiver. The wood and the
magazine are in palette v2's marble_red, the reddish-brown the held frames
snap to (gemini_frames.py drops flag_red for the AKM), so the rifle on the
floor and in the hand is the same rifle; the steel is gen_weapon's gunmetal.
No text, no fonts: the sprite reproduces byte for byte on any machine.

The materials are added to gen_weapon's tables only for the render
(`akm_materials`, the way gen_pickups.py does it) and restored afterwards,
so gen_weapon's own ids, and so its renders, never move.

Output (work/ is gitignored): work/art/weapons/hand_G/akm/SDAQA0.png, with
the three held lumps, so one install copies the AKM's four lumps.
"""
from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_weapon as gw  # noqa: E402
import palette as palette_mod  # noqa: E402
from gen_enemy import Material  # noqa: E402

OUT_DIR = gw.PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G" / "akm"
LUMP = "SDAQA0"
PX_PER_CM = gw.PICKUP_GUN_PX_PER_CM   # the PPSh-41's: 88 cm of rifle -> ~55 px, as SDPQ
LIFT = 3.0                            # cm the gun's axis lies above the floor (as the PPSh)
SHIFT = 2.0                           # cm the butt is moved right so the whole gun centres

# Side profile, cm: u along the bore from the butt plate (0) to the muzzle
# brake's end (MUZZLE_U), v up from the bore's axis. AKM 1959 dimensions
# rounded (880 mm, 415 mm barrel); the magazine and the brake a little
# fat, as every pickup's small parts are (gen_weapon: a round would be 1 px).
STOCK = ((-0.5, 0.0), (0.0, 1.2), (24.0, 0.9), (24.0, -3.4), (10.0, -6.8), (0.0, -11.2), (-0.5, -10.6))
RECEIVER = ((24.0, -3.4), (52.0, -3.4), (52.0, 1.6), (49.0, 2.8), (26.0, 2.8), (24.0, 1.8))
GRIP = ((29.5, -3.4), (34.5, -3.4), (32.8, -12.8), (28.4, -12.4))
MAGAZINE = ((40.0, -3.4), (47.6, -3.4), (50.4, -9.0), (54.8, -16.8), (57.6, -21.4),
            (51.6, -24.2), (47.4, -18.0), (44.0, -11.0))
HANDGUARD = ((52.0, -3.0), (68.0, -2.2), (68.0, 0.6), (52.0, 0.6))
UPPER_GUARD = (52.0, 63.0, 2.4, 1.35)    # u from, u to, v of its axis, radius (over the gas tube)
GAS_TUBE = (52.0, 70.0, 2.4, 0.9)
GAS_BLOCK = (68.5, 71.5, 1.3, 1.7)
BARREL = (52.0, 84.0, 0.0, 0.9)
ROD = (69.0, 84.0, -1.6, 0.35)           # the cleaning rod under the barrel
REAR_SIGHT = ((50.5, 1.6), (55.5, 1.6), (55.5, 3.6), (51.5, 3.6))
FRONT_SIGHT = ((78.0, 0.5), (79.8, 0.5), (79.6, 4.6), (78.4, 4.6))
BRAKE = (84.0, 88.0, 0.0, 1.2)
MUZZLE_U = 88.0
STOCK_W, STEEL_W, GRIP_W, MAG_W = 3.6, 3.0, 2.8, 2.6   # thickness, cm

class PaletteV2Material(Material):
    """A material on one of the palette's v2 ramps (D45): gen_enemy's
    Material reads the v1 ramps only (as gen_pickups.py's)."""

    def colours(self) -> list[tuple[int, int, int]]:
        cols = palette_mod.ramp_colours(self.ramp)[self.lo:self.hi + 1]
        return ([(0, 0, 0)] + cols) if self.black_floor else cols


AKM_MATERIALS: dict[str, Material] = {
    "laminate": PaletteV2Material("marble_red", 2, 11, black_floor=True),     # stock, grip, handguards
    "mag_bakelite": PaletteV2Material("marble_red", 3, 13, black_floor=True),  # a shade lighter: the magazine
}


@contextlib.contextmanager
def akm_materials():
    """gen_weapon's material tables with AKM_MATERIALS appended (every
    gen_weapon id keeps its number), restored on the way out."""
    saved = (gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT)
    mats = dict(gw.MATERIALS)
    mats.update(AKM_MATERIALS)
    gw.MATERIALS = mats
    gw.MAT_ID = {name: i for i, name in enumerate(mats)}
    try:
        yield
    finally:
        gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT = saved


def draw_akm(rig: gw.Rig, origin, U, V) -> dict:
    """The rifle with its butt plate at `origin`, bore along U, up V."""
    U = gw.unit(U)
    V = gw.perp(V, U)
    o = np.asarray(origin, np.float64)

    def at(u, v=0.0):
        return o + U * u + V * v

    def tube(spec, material, base, gain=0.85):
        u0, u1, v, r = spec
        rig.capsule(at(u0, v), at(u1, v), r, r, material, base, gain)

    rig.plate(at(0, 0), U, V, STOCK, STOCK_W, "laminate", 0.55, 0.8, grad=(V, 0.008))
    rig.plate(at(0, 0), U, V, GRIP, GRIP_W, "laminate", 0.45, 0.8)
    rig.plate(at(0, 0), U, V, RECEIVER, STEEL_W, "gunmetal", 0.32, 0.85)
    rig.plate(at(0, 0), U, V, MAGAZINE, MAG_W, "mag_bakelite", 0.5, 0.8)
    rig.plate(at(0, 0), U, V, HANDGUARD, STOCK_W, "laminate", 0.55, 0.8)
    tube(GAS_TUBE, "gunmetal", 0.36)
    tube(UPPER_GUARD, "laminate", 0.5, 0.8)
    tube(GAS_BLOCK, "gunmetal", 0.4)
    tube(BARREL, "gunmetal", 0.34)
    tube(ROD, "gunmetal", 0.42)
    rig.plate(at(0, 0), U, V, REAR_SIGHT, 1.4, "gunmetal", 0.4, 0.8)
    rig.plate(at(0, 0), U, V, FRONT_SIGHT, 0.8, "gunmetal", 0.4, 0.8)
    tube(BRAKE, "gunmetal", 0.42)
    # the brake's slanted cut: its top edge runs on past the bottom one
    rig.plate(at(0, 0), U, V, ((MUZZLE_U - 0.2, -0.4), (MUZZLE_U + 0.9, 0.2), (MUZZLE_U + 0.9, 1.2),
                               (MUZZLE_U - 0.2, 1.2)), 2.0, "gunmetal", 0.42, 0.8)
    return {"muzzle": at(MUZZLE_U), "at": at}


def render_akm_pickup() -> gw.Frame:
    """SDAQ: the rifle on its side, muzzle to the left, magazine down."""
    with akm_materials():
        rig = gw.gun_pickup_rig(PX_PER_CM)
        right, _, up = gw.floor_basis()
        U = -right
        origin = np.array([0.0, 0.0, gw.PICKUP_DIST]) - U * (MUZZLE_U / 2 + SHIFT) + up * LIFT
        draw_akm(rig, origin, U, up)
        return gw.finish(rig, hud=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    f = render_akm_pickup()
    path = gw.save_sprite(f, args.out / f"{LUMP}.png")
    h, w = f.rgba.shape[:2]
    print(f"{LUMP}: {w}x{h} offsets {tuple(int(v) for v in f.offsets())} -> {path.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
