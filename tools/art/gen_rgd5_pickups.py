"""The RGD-5's world sprites (V3, D120; art D116/D127): the loose grenade
SDRJ A0 (and its HUD icon), the grenade in flight SDRN A0, the pouch of two
SDRQ A0 and the crate SDRZ A0.

    .venv/Scripts/python.exe tools/art/gen_rgd5_pickups.py     (Windows)
    .venv/bin/python tools/art/gen_rgd5_pickups.py             (macOS)

Where each comes from. The project lead's ONE Gemini pickup image
(work/art/reference/gemini_rgd5_pickup.jfif, local, D77: the grenade lying
on its side, fuse and spoon to the right, the ring hanging under them, on
flat magenta) is the grenade, everywhere:
  SDRJ  the image through gemini_frames' own steps (letterbox, magenta key,
        palette v2, its art-pixel grid, which is coarser than the held
        frames', so detect_grid is asked up to GRID_MAX) and mode-resized to
        LOOSE_W px, pixels 1.2 tall as Doom shows them (as the Gemini
        enemies, gemini_enemy.PIXEL_ASPECT): it lies on the floor.
  SDRN  the same grenade turned FLIGHT_DEG (RotSprite on the art grid, no
        blended pixel) and a little smaller: one frame in flight and at rest.
  SDRQ  a two-cell canvas pouch drawn on the weapon pickups' rig
        (gen_pickups' Box and open_box, gen_weapon's renderer), the two
        grenades standing in it, fuses up: the Gemini grenade turned upright
        and pasted into each cell, behind the pouch's front and side walls
        (a second render of those walls alone is the mask).
  SDRZ  a small green crate, open, drawn the same way as the PG-7V crate
        SDRB, four Gemini grenades lying in it in two rows (the back row
        pasted first, the front row over it, the crate's near walls over
        both).
Gemini drew no pouch and no crate and the CEO saves the quota: they are the
rig's, as every ammunition pickup is (D48, D80), and the grenade in them is
Gemini's. No text, no fonts.

Scale. The loose grenade is LOOSE_W px long, the TT-33 pickup's px per cm
(SDTP is 27 px for a 19.6 cm pistol, ~1.4 px/cm; a grenade with its fuse is
~11.5 cm); the pouch and the crate are drawn at POUCH_PX_PER_CM and
CRATE_PX_PER_CM, with the grenades pasted at the rig's own scale (the rig
draws square pixels, as every rig pickup).

Output (work/ is gitignored): work/art/weapons/hand_G/rgd5/, beside the
four held frames of `gemini_frames.py rgd5`, so one install copies all.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_frames as gf  # noqa: E402
import gen_pickups as gp  # noqa: E402
import gen_weapon as gw  # noqa: E402

SOURCE = gf.REF_DIR / "gemini_rgd5_pickup.jfif"
OUT_DIR = gf.OUT_ROOT / "rgd5"
LUMPS = ("SDRJA0", "SDRNA0", "SDRQA0", "SDRZA0")

GRID_MAX = 16.0          # source px: the pickup image's art pixel is ~10 (the held frames' 3.75)
LOOSE_W = 16             # px: the loose grenade, fuse and spoon included (~1.4 px/cm, the TT-33 pickup's)
FLIGHT_W = 13            # px: the grenade in flight, before the turn (a little smaller: it is in the air)
FLIGHT_DEG = 35.0        # degrees counter-clockwise: tumbling, fuse up
FLIGHT_PAD = 0.4         # x the art's size added each side before the turn (nothing is cut)

POUCH_PX_PER_CM = 1.3    # the pouch: ~15 cm across -> ~20 px
POUCH = (15.0, 6.5, 8.0)    # w, d, h cm: two cells side by side
POUCH_MAT = "wood_ash"   # cream_yellow: khaki tarpaulin (brezent), apart from the grenades' olive
POUCH_YAW = 20.0         # degrees: the front and the left side show
POUCH_WALL = 0.7         # cm of canvas
POUCH_GRENADE_CM = 12.5  # the upright grenade's height (the image's width: body, fuse and ring)
POUCH_SINK = 0.40        # fraction of the upright grenade under the pouch's rim
FLAP_LEN = 6.0           # cm: each cell's flap, thrown back
FLAP_TILT = 0.35         # the flap's rise as it goes back (0 flat, 1 straight up)

CRATE_PX_PER_CM = 1.0    # the crate: ~31 cm -> ~31 px (the PG-7V crate SDRB is 52)
CRATE = (27.0, 15.0, 7.0)   # w, d, h cm: four grenades lying in two rows
CRATE_MAT = "wood_birch" # bare wood: the olive grenades read against it (an olive crate swallowed them)
CRATE_WALL = 1.2
CRATE_GRENADE_CM = 11.5  # a lying grenade's length, ring included
CRATE_ROW_LIFT = 2.6     # cm: a lying grenade's axis above the crate's inner floor


# ------------------------------------------------------------ the grenade
def grenade_art() -> np.ndarray:
    """The Gemini pickup image as palette v2 indices on its own art grid,
    cropped to the grenade (gemini_frames' steps; the grid up to GRID_MAX)."""
    pal = gf.palette_rgb()
    rgb = gf.crop_letterbox(np.asarray(Image.open(SOURCE).convert("RGB")))
    alpha = gf.key_magenta(rgb)
    period, phx, phy = gf.detect_grid(rgb, alpha, hi=GRID_MAX)
    art = gf.grid_downsample(gf.snap_palette(rgb, alpha, pal), period, phx, phy, pal)
    biggest = max(gf.components(art >= 0), key=lambda c: int(c.sum()))
    art = np.where(biggest, art, gf.TRANSPARENT)        # JPEG specks on the magenta go
    return crop(art)


def crop(idx: np.ndarray) -> np.ndarray:
    rows, cols = np.flatnonzero((idx >= 0).any(axis=1)), np.flatnonzero((idx >= 0).any(axis=0))
    return idx[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def sized(art: np.ndarray, width: int, aspect: float = gf.PIXEL_ASPECT) -> np.ndarray:
    """`art` mode-resized to `width` px, its rows divided by `aspect`."""
    h, w = art.shape
    return crop(gf.mode_resize(art, width, max(1, round(width * h / w / aspect)), gf.palette_rgb()))


def turned(art: np.ndarray, deg: float, pad: float = FLIGHT_PAD) -> np.ndarray:
    """`art` turned `deg` counter-clockwise about its centre (RotSprite)."""
    h, w = art.shape
    ph, pw = round(h * pad) + 2, round(w * pad) + 2
    big = np.pad(art, ((ph, ph), (pw, pw)), constant_values=gf.TRANSPARENT)
    return crop(gf.rotsprite(big, deg, (big.shape[1] / 2, big.shape[0] / 2)))


def upright(art: np.ndarray) -> np.ndarray:
    """The lying grenade stood on its base, fuse up (it lies fuse right)."""
    return np.rot90(art, 1).copy()


# ------------------------------------------------------------- rendering
def full_canvas(rig: gw.Rig) -> np.ndarray:
    """The rig's render as RGBA on its whole canvas (gen_weapon.finish
    without the crop, so a second render of the same camera lines up)."""
    return gw.to_rgba(*rig.reduce())


def paste(rgba: np.ndarray, sprite: np.ndarray, centre: tuple[float, float], keep: np.ndarray) -> None:
    """`sprite` (palette indices) over rgba, centred on `centre` (x, y),
    except where `keep` (the walls in front of it) is set."""
    pal = gf.palette_rgb()
    sh, sw = sprite.shape
    x0, y0 = round(centre[0] - sw / 2), round(centre[1] - sh / 2)
    H, W = keep.shape
    for (y, x) in zip(*np.nonzero(sprite >= 0)):
        cy, cx = y0 + y, x0 + x
        if 0 <= cy < H and 0 <= cx < W and not keep[cy, cx]:
            rgba[cy, cx, :3] = pal[sprite[y, x]]
            rgba[cy, cx, 3] = 255


def pickup_frame(rgba: np.ndarray) -> gw.Frame:
    """Cropped to its content, standing on its lowest pixel, centred (the
    rig pickups' offsets, gen_weapon.finish)."""
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop_ = rgba[y0:y1, x0:x1].copy()
    return gw.Frame(crop_, np.zeros(crop_.shape[:2], np.int16), (x1 - x0) // 2, y1 - y0, False)


def sprite_frame(idx: np.ndarray) -> gw.Frame:
    return pickup_frame(gf.to_rgba(idx, gf.palette_rgb()))


def project(rig: gw.Rig, p) -> tuple[float, float]:
    x, y, _ = rig.project(p)
    return x, y


def draw_pouch(rig: gw.Rig, near_only: bool = False) -> dict:
    """The two-cell pouch on the floor; with `near_only` just the walls in
    front of the grenades (front, sides, the divider). Returns the cells'
    rim centres."""
    X, Y, Z = gp.yawed(POUCH_YAW)
    w, d, h = POUCH
    b = gp.Box(gp.centre() - Z * h / 2, X, Y, Z, w, d, h)
    t = POUCH_WALL
    if not near_only:
        gp.Box(b.c, X, Y, Z, w, d, t).draw(rig, POUCH_MAT, 0.20)                       # floor
        gp.Box(b.c + Y * (d - t) / 2, X, Y, Z, w - 2 * t, t, h).draw(rig, POUCH_MAT, 0.30)   # back
        for s in (-w / 4, w / 4):                                                           # the flaps
            hinge = b.c + Y * d / 2 + Z * h + X * s
            V = gw.unit(Y * (1 - FLAP_TILT) + Z * FLAP_TILT)
            rig.plate(hinge, X, V, gp.rect(w / 2 - 0.8, FLAP_LEN), 0.5, POUCH_MAT, 0.62, 0.8)
    gp.Box(b.c - Y * (d - t) / 2, X, Y, Z, w - 2 * t, t, h).draw(rig, POUCH_MAT, 0.56)  # front
    for sx in (-1, 1):
        gp.Box(b.c + X * sx * (w - t) / 2, X, Y, Z, t, d, h).draw(rig, POUCH_MAT, 0.50)
    gp.Box(b.c, X, Y, Z, t, d, h).draw(rig, POUCH_MAT, 0.40)                          # the divider
    front = gp.Box(b.c, X, Y, Z, w, d, h)
    front.decal(rig, "front", -0.35, 0.8, 0.35, h - 0.6, POUCH_MAT, 0.22)              # the seam
    for s in (-w / 4, w / 4):                                                               # the buttons
        front.decal(rig, "front", s - 0.7, h - 2.4, s + 0.7, h - 1.0, "button", 0.45)
    return {"cells": [b.c + Z * h + X * s for s in (-w / 4, w / 4)]}


def render_pouch() -> gw.Frame:
    """SDRQ: the pouch of two, the grenades standing in it, fuses up."""
    up = upright(grenade_art())
    sprite = sized(up, max(1, round(up.shape[1] * POUCH_GRENADE_CM * POUCH_PX_PER_CM / up.shape[0])), 1.0)
    with gp.pickup_materials():
        rig = gp.rig_for(POUCH_PX_PER_CM)
        cells = draw_pouch(rig)["cells"]
        rgba = full_canvas(rig)
        near = gp.rig_for(POUCH_PX_PER_CM)
        draw_pouch(near, near_only=True)
        keep = full_canvas(near)[..., 3] > 0
        for c in cells:
            cx, cy = project(rig, c)
            paste(rgba, sprite, (cx, cy - sprite.shape[0] * (0.5 - POUCH_SINK)), keep)
    return pickup_frame(rgba)


def draw_crate(rig: gw.Rig, near_only: bool = False) -> dict:
    """The open crate; with `near_only` just its front and left walls.
    Returns the four grenades' centres, back row first."""
    X, Y, Z = gp.yawed(gp.BOX_YAW, gp.OPEN_PITCH)
    w, d, h = CRATE
    b = gp.Box(gp.centre() - Z * h / 2, X, Y, Z, w, d, h)
    t = CRATE_WALL
    if near_only:
        gp.Box(b.c - Y * (d - t) / 2, X, Y, Z, w - 2 * t, t, h).draw(rig, CRATE_MAT, 0.55)
        gp.Box(b.c - X * (w - t) / 2, X, Y, Z, t, d, h).draw(rig, CRATE_MAT, 0.55)
        gp.Box(b.c + X * (w - t) / 2, X, Y, Z, t, d, h).draw(rig, CRATE_MAT, 0.55)
    else:
        inside = gp.open_box(rig, b, t, CRATE_MAT, 0.55, 0.10)
        gp.crate_planks(rig, b, faces=("front", "left"), n=2, px_per_cm=CRATE_PX_PER_CM)
        b.decal(rig, "front", -8.0, 2.4, 2.0, 5.6, "rubber", 0.20)        # the stencil block
    lift = Z * (t + CRATE_ROW_LIFT)
    return {"grenades": [b.c + lift + Y * sy * d / 4 + X * sx * w / 4 for sy in (1, -1) for sx in (-1, 1)]}


def render_crate() -> gw.Frame:
    """SDRZ: the crate open, four grenades in two rows."""
    art = grenade_art()
    sprite = sized(art, round(CRATE_GRENADE_CM * CRATE_PX_PER_CM), 1.0)
    with gp.pickup_materials():
        rig = gp.rig_for(CRATE_PX_PER_CM)
        spots = draw_crate(rig)["grenades"]
        rgba = full_canvas(rig)
        near = gp.rig_for(CRATE_PX_PER_CM)
        draw_crate(near, near_only=True)
        keep = full_canvas(near)[..., 3] > 0
        for p in spots:                                   # back row first: the front row lies over it
            paste(rgba, sprite, project(rig, p), keep)
    return pickup_frame(rgba)


def render_all() -> dict[str, gw.Frame]:
    art = grenade_art()
    return {"SDRJA0": sprite_frame(sized(art, LOOSE_W)),
            "SDRNA0": sprite_frame(sized(turned(art, FLIGHT_DEG), FLIGHT_W)),
            "SDRQA0": render_pouch(),
            "SDRZA0": render_crate()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    for lump, f in render_all().items():
        path = gw.save_sprite(f, args.out / f"{lump}.png")
        h, w = f.rgba.shape[:2]
        print(f"{lump}: {w}x{h} offsets {tuple(int(v) for v in f.offsets())} -> {path.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
