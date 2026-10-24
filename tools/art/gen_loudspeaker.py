"""V3 B5 — the propaganda radio's loudspeaker, sprite SDLS (SD_Loudspeaker, 21201).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_loudspeaker.py [--preview]
                            (macOS: .venv/bin/python tools/art/gen_loudspeaker.py)

A 1970s Soviet street loudspeaker: a steel pole on a cast-iron foot, a
cross-arm at the top carrying two aluminium horns («колокол») that point
out and a little down at the crowd, each with its round driver can behind,
and a small junction box on the pole with a red star and a pilot lamp.
SD_Loudspeaker stands where level-designer puts it, often in the middle of
a room or a square (MOD-SPEC 6.14), so the sprite is the pole, which reads
from every side: one picture for every angle (rotation 0).

  frame A   silent (the pilot lamp dark)
  frame B   speaking: the pilot lamp lit and the horns a hair forward on
            their axis, the shake of a loud driver; the actor alternates
            A and B while a line plays (the v3 patch)

Two options for the CEO, the same model in two paints:

  A  grey: aluminium horns, grey pole (recommended: the street loudspeaker
     of the photographs, and it stands apart from the red Kremlin brick
     and from the mod's 4BO-green doors and crates)
  B  olive: everything in 4BO military green, the army's set

Drawn from code on gen_effects' rig (tools/art/rig_core.py, the solids of
the floor lamp COLU and the drum BAR1): no photograph, no typeface, no
pack. Every opaque pixel is a palette v1 colour, alpha is 0/255, and the
star is a 7x7 hard-pixel stamp. Size: 69 units from the floor to the top
of the horns, half again the floor lamp COLU (48) and a head over the
player (56): the horns hang above a man, as on a street.

Output: work/art/loudspeaker/<A|B>/SDLSA0.png and SDLSB0.png (grAb inside
each PNG), and with --preview the CEO's sheet
docs/art/previews/2026-10-24_V3_loudspeaker.png: the four sprites at x4,
both options at x1 and x4 beside the mod's floor lamp, drum, radio and a
rifleman, and the Red Square wall (SDKREM1 over the cobbles SDCOBL1) with
the loudspeaker standing against it, at x1 and x4. Sheet labels in our own
alphabet (assets/fonts/, D24). Installing is work/art/loudspeaker/install.sh
on the v3 branch, after the CEO's verdict (sprites go to the CEO, D113).
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

ART_DIR = Path(__file__).resolve().parent
if str(ART_DIR) not in sys.path:
    sys.path.insert(0, str(ART_DIR))

import artlib  # noqa: E402
import rig_core as core  # noqa: E402

PROJECT_ROOT = ART_DIR.parents[1]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "loudspeaker"
ASSETS = PROJECT_ROOT / "assets"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-24_V3_loudspeaker.png"

SPRITE = "SDLS"
FRAMES = ("A", "B")
OPTIONS = ("A", "B")
RECOMMENDED = "A"
SEED = 21201                    # the actor's editor number
ROTATION = 0                    # one picture for every angle

# ------------------------------------------------------------ dimensions
# World units = pixels at 1:1 (rig_core: orthographic, DOOM_HEIGHT 56 px).
CANVAS = core.Canvas(56, 80, 28, 77)
SINK = 3                        # sinks 3 px into the floor, as COLU (gen_effects.LAMP_GRAB)
GRAB = (CANVAS.cx, CANVAS.foot_row - SINK)
TOP_HEIGHT = 69                 # floor to the top of the horns, the size the docstring promises
POLE_TOP = 71.0
POLE_R = 1.15
ARM_Y = 68.0                    # the cross-arm
ARM_HALF = 7.5                  # half its span
HORN_LEN = 15.0
HORN_R_THROAT = 1.7
HORN_R_MOUTH = 6.2
HORN_OUT_DEG = 54.0             # from the camera axis: mostly sideways, the mouth seen as an ellipse
HORN_DOWN = -0.22               # they aim a little down, at the crowd
HORN_SHAKE = 0.6                # frame B: the horn forward on its axis (units)
DRIVER_LEN = 4.2
DRIVER_R = 2.5
MOUTH_DEPTH = 3.2               # the dark throat seen through the mouth
MOUTH_RIM = 0.75                # the horn's lip left around the dark mouth
BOX_Y = 56.0                    # the junction box's centre
BOX_HALF = (3.3, 3.6, 1.6)
STAR_R_OUT = 3.2

# ------------------------------------------------------------ materials
M = core.Mat.on_ramp
MATS: dict[str, core.Mat] = dict(core.MATERIALS)
_NEW_MATS = {
    "ls_alu": M("concrete_cold", 7, 24, shift=False),             # aluminium bell, grey
    "ls_alu_dark": M("concrete_cold", 2, 16, black_floor=True, shift=False),
    "ls_steel": M("concrete_cold", 4, 20, black_floor=True, shift=False),
    "ls_olive": M("military_green", 3, 13, shift=False),           # 4BO green
    "ls_olive_dark": M("military_green", 0, 9, black_floor=True, shift=False),
    "ls_iron": M("concrete_cold", 1, 12, black_floor=True, shift=False),
    "ls_throat": M("concrete_cold", 0, 3, black_floor=True, shift=False),
    "ls_cable": M("concrete_cold", 0, 4, black_floor=True, shift=False),
    "ls_lamp_off": M("flag_red", 1, 5, black_floor=True, shift=False),
    "ls_lamp_on": core.Mat((("cream_yellow", 12, 15), ("white",)), flat=True, shift=False),
}
for _n, _m in _NEW_MATS.items():
    core.register_material(_n, _m, MATS)

PAINT = {   # option -> (bell, driver can and arm, pole, junction box)
    "A": ("ls_alu", "ls_alu_dark", "ls_steel", "ls_olive"),
    "B": ("ls_olive", "ls_olive_dark", "ls_olive_dark", "ls_olive"),
}

STAR_PATTERN = (       # '.' leaves the box's own pixel
    "...r...",
    "..rRr..",
    "rrRRRrr",
    ".rRRRr.",
    "..rRr..",
    ".rr.rr.",
    ".r...r.",
)
STAR_COLOURS = {"R": ("flag_red", 12), "r": ("flag_red", 8)}


def star_draw(rgba: np.ndarray, x0: int, y0: int, mirror: bool) -> None:
    """The 7x7 red star on the junction box (symmetric: mirroring is moot)."""
    for j, row in enumerate(STAR_PATTERN):
        for i, ch in enumerate(row):
            if ch in STAR_COLOURS and rgba[y0 + j, x0 + i, 3]:
                name, k = STAR_COLOURS[ch]
                rgba[y0 + j, x0 + i] = (*artlib.ramp(name)[k], 255)


STAR = core.Insignia("box", (7, 7), star_draw, outward=(0.0, 0.0, 1.0), min_px=12)


# ------------------------------------------------------------ the model
def _frame_for(axis: np.ndarray) -> np.ndarray:
    """A rotation whose second column is `axis` (cappedcone's local y)."""
    y = axis / np.linalg.norm(axis)
    helper = np.array([0.0, 1.0, 0.0]) if abs(y[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(helper, y)
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    return np.column_stack([x, y, z])


def _along(mat: str, base: float, start: np.ndarray, axis: np.ndarray, length: float,
           r0: float, r1: float, **kw) -> core.Prim:
    """A capped cone from `start` (radius r0) `length` units along `axis` (r1)."""
    d = axis / np.linalg.norm(axis)
    centre = start + d * (length / 2)
    return core.Prim("cappedcone", mat, base, centre, h=length / 2, r1=r0, r2=r1,
                     rot=_frame_for(d), **kw)


def horn_axis(side: int) -> np.ndarray:
    """side +1 = screen right, -1 = screen left; z points at the camera."""
    a = np.deg2rad(HORN_OUT_DEG)
    v = np.array([side * np.sin(a), HORN_DOWN, np.cos(a)])
    return v / np.linalg.norm(v)


def horn(side: int, bell: str, can: str, shake: float = 0.0) -> list[core.Prim]:
    d = horn_axis(side)
    throat = np.array([side * ARM_HALF, ARM_Y, 0.0]) + d * (1.2 + shake)
    mouth = throat + d * HORN_LEN
    P = [_along(can, 0.55, throat - d * DRIVER_LEN, d, DRIVER_LEN, DRIVER_R, DRIVER_R * 0.92),
         _along(can, 0.5, throat - d * (DRIVER_LEN + 0.8), d, 0.9, DRIVER_R * 0.55, DRIVER_R * 0.75),
         _along(bell, 0.6, throat, d, HORN_LEN, HORN_R_THROAT, HORN_R_MOUTH),
         # the lip: a short flare so the rim catches the light
         _along(bell, 0.66, mouth - d * 0.9, d, 0.9, HORN_R_MOUTH, HORN_R_MOUTH + 0.35),
         # the dark throat seen through the open mouth
         _along("ls_throat", 0.2, mouth - d * MOUTH_DEPTH, d, MOUTH_DEPTH + 0.3,
                HORN_R_MOUTH - 2.4, HORN_R_MOUTH + 0.35 - MOUTH_RIM)]
    # the clamp band where the bell meets the arm
    P.append(_along(can, 0.6, throat - d * 0.2, d, 1.1, HORN_R_THROAT + 0.7, HORN_R_THROAT + 0.7))
    return P


def model(opt: str, frame: str = "A") -> list[core.Prim]:
    bell, can, pole, box_mat = PAINT[opt]
    cc, rc, E = core.ccone, core.rcone, core.ellipsoid
    shake = HORN_SHAKE if frame == "B" else 0.0
    P = [cc("ls_iron", 0.45, 0.0, 1.6, 7.0, 6.4), cc("ls_iron", 0.5, 1.6, 4.5, 3.6, 1.9),
         cc(pole, 0.6, 4.5, POLE_TOP, POLE_R + 0.15, POLE_R),
         cc(pole, 0.55, 20.0, 21.2, POLE_R + 0.45, POLE_R + 0.45),           # a joint of the pipe
         cc(can, 0.6, POLE_TOP - 0.2, POLE_TOP + 1.3, 1.9, 1.0),             # the cap
         rc(can, 0.6, (-ARM_HALF, ARM_Y, 0.0), (ARM_HALF, ARM_Y, 0.0), 0.85),
         cc(can, 0.55, ARM_Y - 1.8, ARM_Y + 1.8, POLE_R + 0.6, POLE_R + 0.6),  # the arm's collar
         # struts from the pole up to the arm's ends
         rc(can, 0.55, (0.0, ARM_Y - 6.0, 0.0), (-ARM_HALF + 1.2, ARM_Y - 0.4, 0.0), 0.45),
         rc(can, 0.55, (0.0, ARM_Y - 6.0, 0.0), (ARM_HALF - 1.2, ARM_Y - 0.4, 0.0), 0.45)]
    P += horn(-1, bell, can, shake) + horn(+1, bell, can, shake)
    # the junction box, its lid, the pilot lamp and the cables to the drivers
    bx = core.box(box_mat, 0.6, (0.0, BOX_Y, POLE_R + BOX_HALF[2] - 0.4), BOX_HALF, rnd=0.5, tag="box")
    P += [bx,
          core.box(box_mat, 0.66, (0.0, BOX_Y + BOX_HALF[1] + 0.3, POLE_R + BOX_HALF[2] - 0.4),
                   (BOX_HALF[0] + 0.4, 0.45, BOX_HALF[2] + 0.4), rnd=0.2),
          E("ls_lamp_on" if frame == "B" else "ls_lamp_off", 0.8,
            (BOX_HALF[0] - 0.9, BOX_Y - BOX_HALF[1] + 1.0, POLE_R + 2 * BOX_HALF[2] - 0.2), (0.75, 0.75, 0.6))]
    for side in (-1, 1):
        d = horn_axis(side)
        can_back = np.array([side * ARM_HALF, ARM_Y, 0.0]) + d * (1.2 + shake - DRIVER_LEN * 0.5)
        P.append(rc("ls_cable", 0.3, (side * 1.6, BOX_Y + BOX_HALF[1] - 0.5, POLE_R + 0.6),
                    tuple(can_back + np.array([0.0, -DRIVER_R * 0.8, 0.0])), 0.32))
    return P


def render(opt: str, frame: str = "A") -> np.ndarray:
    """One lump, RGBA (h, w, 4) on CANVAS, the star stamped on the box."""
    if opt not in OPTIONS or frame not in FRAMES:
        raise ValueError(f"no option {opt!r} frame {frame!r}")
    return core.render(model(opt, frame), ROTATION, CANVAS, MATS, seed=SEED, insignia=(STAR,),
                       what=f"loudspeaker{opt}{frame}")


def lump_name(frame: str) -> str:
    return f"{SPRITE}{frame}0"


def save(rgba: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *GRAB))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def build(out_dir: Path = OUT_DIR) -> dict[tuple[str, str], np.ndarray]:
    """Render every option and frame; write <out_dir>/<opt>/SDLS<F>0.png."""
    out: dict[tuple[str, str], np.ndarray] = {}
    for opt in OPTIONS:
        for frame in FRAMES:
            rgba = render(opt, frame)
            save(rgba, out_dir / opt / f"{lump_name(frame)}.png")
            out[(opt, frame)] = rgba
    return out


def top_height(rgba: np.ndarray) -> int:
    """Units from the floor (grAb y) to the topmost opaque pixel."""
    rows = np.nonzero((rgba[..., 3] > 0).any(axis=1))[0]
    return GRAB[1] - int(rows[0])


# ============================================================ the CEO's sheet
FONT_BIG = ASSETS / "fonts" / "bigfont"
FONT_SMALL = ASSETS / "fonts" / "defsmallfont"
SHEET_BG = artlib.ramp("concrete_cold")[3]
PANEL_BG = artlib.ramp("concrete_cold")[6]
INK = artlib.ramp("cream_yellow")[15]
INK_MUTE = artlib.ramp("concrete_cold")[22]
INK_SHADOW = artlib.ramp("concrete_cold")[0]
ACCENT = artlib.ramp("hazard_yellow")[12]
GAP = 12
ZOOM = 4
SCENE_W, WALL_H, FLOOR_H = 256, 128, 40
SCENE_LIGHT = (1.0, 0.72)       # the full-bright square and a dimmer corner (about light 160)
NEIGHBOURS = (("COLU A0, LAMP", "sprites/effects/COLUA0.png"),
              ("BAR1 A0, DRUM", "sprites/effects/BAR1A0.png"),
              ("SDRD A0, RADIO", "sprites/pickups/SDRDA0.png"),
              ("SDRR A1, RIFLEMAN", "sprites/rifleman/SDRRA1.png"))


def label(text: str, small: bool = False, ink=INK) -> np.ndarray:
    """A line in our own alphabet (assets/fonts, D24): no system font."""
    folder = FONT_SMALL if small else FONT_BIG
    glyphs = []
    for ch in text.upper():
        p = folder / f"{ord(ch):04X}.png"
        if not p.is_file():
            raise FileNotFoundError(f"no glyph for {ch!r} in {folder}")
        with Image.open(p) as im:
            glyphs.append(np.asarray(im.convert("RGBA")))
    h = max(g.shape[0] for g in glyphs)
    w = sum(g.shape[1] for g in glyphs)
    out = np.zeros((h, w, 4), np.uint8)
    x = 0
    for g in glyphs:
        on = g[..., 3] > 0
        lum = g[..., :3].astype(int).sum(-1)
        bright = on & (lum >= lum[on].max() * 0.5) if on.any() else on
        gh, gw = on.shape
        out[:gh, x:x + gw][on & ~bright] = (*INK_SHADOW, 255)
        out[:gh, x:x + gw][bright] = (*ink, 255)
        x += gw
    return out


def zoom(rgba: np.ndarray, k: int) -> np.ndarray:
    return rgba.repeat(k, axis=0).repeat(k, axis=1)


def paste(canvas: np.ndarray, tile: np.ndarray, x: int, y: int) -> None:
    h, w = tile.shape[:2]
    h = min(h, canvas.shape[0] - y)
    w = min(w, canvas.shape[1] - x)
    if h <= 0 or w <= 0:
        return
    tile = tile[:h, :w]
    if tile.shape[2] == 4:
        a = tile[..., 3:4] > 0
        canvas[y:y + h, x:x + w] = np.where(a, tile[..., :3], canvas[y:y + h, x:x + w])
    else:
        canvas[y:y + h, x:x + w] = tile


def read_png(rel: str) -> tuple[np.ndarray, tuple[int, int]]:
    """An installed lump as RGBA and its grAb (0, 0 when it has none)."""
    path = ASSETS / rel
    data = path.read_bytes()
    grab = (0, 0)
    i = 8
    while i < len(data):
        n, = struct.unpack(">I", data[i:i + 4])
        if data[i + 4:i + 8] == b"grAb":
            grab = struct.unpack(">ii", data[i + 8:i + 16])
            break
        i += 12 + n
    with Image.open(path) as im:
        return np.asarray(im.convert("RGBA")), grab


def lineup(sprites: list[tuple[str, np.ndarray, tuple[int, int]]], k: int,
           floor_y: int, gap: int) -> tuple[np.ndarray, list[tuple[int, str]]]:
    """Sprites standing on one floor line at zoom k (each by its grAb)."""
    width = sum(s.shape[1] * k + gap for _, s, _ in sprites) + gap
    height = (floor_y + 4) * k
    out = np.zeros((height, width, 4), np.uint8)
    x = gap
    names = []
    for name, s, (gx, gy) in sprites:
        top = floor_y * k - gy * k
        z = zoom(s, k)
        hh = min(z.shape[0], height - top)
        region = out[top:top + hh, x:x + z.shape[1]]
        a = z[:hh, ..., 3:4] > 0
        out[top:top + hh, x:x + z.shape[1]] = np.where(a, z[:hh], region)
        names.append((x + z.shape[1] // 2, name))
        x += z.shape[1] + gap
    out[floor_y * k:floor_y * k + max(1, k // 2), :, :3] = INK_MUTE
    out[floor_y * k:floor_y * k + max(1, k // 2), :, 3] = 255
    return out, names


def floor_band(flat: np.ndarray, w: int, h: int) -> np.ndarray:
    """The cobbles in a cheap perspective: each row samples the flat at a
    depth that shrinks toward the wall."""
    out = np.zeros((h, w, 3), np.uint8)
    for j in range(h):
        depth = 1.0 + 3.0 * (1 - j / max(1, h - 1))        # far at the wall, near at the bottom
        v = int((j * 1.6) % flat.shape[0])
        us = ((np.arange(w) - w / 2) * depth / 2.2 + 1000).astype(int) % flat.shape[1]
        out[j] = flat[v, us, :3]
        out[j] = (out[j].astype(float) * (0.78 + 0.22 * j / max(1, h - 1))).astype(np.uint8)
    return out


def red_square(opt: str, frame: str, light: float) -> np.ndarray:
    """SDKREM1 (merlons SDKREM2 on top) over a strip of SDCOBL1, the
    loudspeaker at 1:1 standing at the wall's foot, under `light`."""
    wall, _ = read_png("textures/moscow/SDKREM1.png")
    merlon, _ = read_png("textures/moscow/SDKREM2.png")
    cobble, _ = read_png("flats/moscow/SDCOBL1.png")
    sky = np.array(artlib.ramp("steel_blue")[3], np.uint8)
    h = 64 + WALL_H + FLOOR_H
    scene = np.zeros((h, SCENE_W, 3), np.uint8)
    scene[:] = sky
    for x in range(0, SCENE_W, wall.shape[1]):
        paste(scene, merlon[0:64], x, 0)                    # the swallowtail merlons above the wall
        paste(scene, wall[..., :3], x, 64)
    scene[64 + WALL_H:] = floor_band(cobble, SCENE_W, FLOOR_H)
    scene = (scene.astype(float) * light).astype(np.uint8)
    spr = render(opt, frame)
    lit = spr.copy()
    lit[..., :3] = (spr[..., :3].astype(float) * light).astype(np.uint8)
    foot = 64 + WALL_H + 6                                  # a step in front of the wall
    paste(scene, lit, SCENE_W // 2 - GRAB[0], foot - GRAB[1])
    other, (gx, gy) = read_png("sprites/rifleman/SDRRA1.png")
    other = other.copy()
    other[..., :3] = (other[..., :3].astype(float) * light).astype(np.uint8)
    paste(scene, other, SCENE_W // 2 + 74 - gx, foot + 10 - gy)
    return scene


def preview(sprites: dict[tuple[str, str], np.ndarray], path: Path = PREVIEW) -> Path:
    width = 960
    blocks: list[tuple[int, np.ndarray]] = []           # (x, rgba or rgb) stacked top to bottom
    y = GAP

    def add(tile: np.ndarray, x: int = GAP, after: int = GAP) -> None:
        nonlocal y
        blocks.append((x, y, tile))
        y += tile.shape[0] + after

    add(label("SOVIET DOOM V3 - SDLS, THE PROPAGANDA LOUDSPEAKER (SD_LOUDSPEAKER 21201)"), after=4)
    add(label("PROPOSAL FOR THE CEO 2026-10-24. ONE PICTURE FOR EVERY ANGLE (A0). FRAME B ALTERNATES "
              "WITH A WHILE A LINE PLAYS.", small=True, ink=INK_MUTE), after=3)
    add(label(f"{TOP_HEIGHT} UNITS TALL (LAMP COLU 48, PLAYER 56). GRAB {GRAB[0]},{GRAB[1]}. CANVAS "
              f"{CANVAS.w}X{CANVAS.h}. PALETTE V1, HARD ALPHA, DRAWN FROM CODE "
              "(TOOLS/ART/GEN_LOUDSPEAKER.PY).", small=True, ink=INK_MUTE), after=GAP + 4)

    # 1. the four lumps at x4
    add(label("1. THE LUMPS AT X4: OPTION A GREY (RECOMMENDED) AND OPTION B OLIVE, "
              "FRAME A SILENT, FRAME B SPEAKING"), after=6)
    row_y = y
    x = GAP
    for opt in OPTIONS:
        for frame in FRAMES:
            z = zoom(sprites[(opt, frame)], ZOOM)
            panel = np.zeros((z.shape[0] + 8, z.shape[1] + 8, 3), np.uint8)
            panel[:] = PANEL_BG
            if opt == RECOMMENDED:
                panel[:2] = ACCENT
                panel[-2:] = ACCENT
                panel[:, :2] = ACCENT
                panel[:, -2:] = ACCENT
            paste(panel, z, 4, 4)
            blocks.append((x, row_y, panel))
            cap = label(f"{opt}  {lump_name(frame)}  {'SILENT' if frame == 'A' else 'SPEAKING'}", small=True)
            blocks.append((x + (panel.shape[1] - cap.shape[1]) // 2, row_y + panel.shape[0] + 3, cap))
            x += panel.shape[1] + GAP
    # x1 beside them
    x1x = x + GAP
    blocks.append((x1x, row_y, label("X1", small=True)))
    for i, opt in enumerate(OPTIONS):
        for j, frame in enumerate(FRAMES):
            s = sprites[(opt, frame)]
            panel = np.zeros((s.shape[0] + 4, s.shape[1] + 4, 3), np.uint8)
            panel[:] = PANEL_BG
            paste(panel, s, 2, 2)
            blocks.append((x1x + j * (s.shape[1] + 8), row_y + 12 + i * (s.shape[0] + 16), panel))
            blocks.append((x1x + j * (s.shape[1] + 8) + 2, row_y + 12 + i * (s.shape[0] + 16) + s.shape[0] + 5,
                           label(f"{opt}{frame}", small=True)))
    y = row_y + CANVAS.h * ZOOM + 8 + 14 + GAP

    # 2. beside the mod's own objects, x1 and x4
    add(label("2. BESIDE THE MOD'S OBJECTS ON ONE FLOOR LINE, X1 AND X4"), after=6)
    others = [(name, *read_png(rel)) for name, rel in NEIGHBOURS]
    row = [("SDLS A0 (A)", sprites[("A", "A")], GRAB), ("SDLS A0 (B)", sprites[("B", "A")], GRAB)] + \
          [(n, s, g) for n, s, g in others]
    floor_y = max(g[1] for _, _, g in row) + 4
    small_row, small_names = lineup(row, 1, floor_y, 30)
    big_row, big_names = lineup(row, ZOOM, floor_y, 24)
    row_y = y
    blocks.append((GAP, row_y, small_row))
    for cx, name in small_names:
        lab = label(name.split(",")[0].replace(" A0", "").replace(" A1", ""), small=True)
        blocks.append((GAP + cx - lab.shape[1] // 2, row_y + small_row.shape[0] + 2, lab))
    bx0 = GAP + small_row.shape[1] + 3 * GAP
    blocks.append((bx0, row_y, big_row))
    for cx, name in big_names:
        lab = label(name, small=True)
        blocks.append((bx0 + cx - lab.shape[1] // 2, row_y + big_row.shape[0] + 3, lab))
    y = row_y + big_row.shape[0] + 14 + GAP

    # 3. Red Square
    add(label("3. RED SQUARE: THE KREMLIN WALL SDKREM1 OVER THE COBBLES SDCOBL1, "
              "THE LOUDSPEAKER AT 1:1 WITH A RIFLEMAN"), after=6)
    row_y = y
    x = GAP
    for light in SCENE_LIGHT:
        sc = red_square(RECOMMENDED, "A", light)
        blocks.append((x, row_y, sc))
        blocks.append((x, row_y + sc.shape[0] + 3,
                       label(f"X1, OPTION {RECOMMENDED}, LIGHT {'FULL' if light == 1.0 else 'DIM'}", small=True)))
        x += sc.shape[1] + GAP
    sc_b = red_square("B", "A", 1.0)
    blocks.append((x, row_y, sc_b))
    blocks.append((x, row_y + sc_b.shape[0] + 3, label("X1, OPTION B, LIGHT FULL", small=True)))
    y = row_y + sc_b.shape[0] + 14 + GAP
    sc = red_square(RECOMMENDED, "A", 1.0)
    crop = sc[24:, SCENE_W // 2 - 48:SCENE_W // 2 + 112]           # the loudspeaker and the rifleman, x4
    z = zoom(crop, ZOOM)
    add(z, after=3)
    add(label(f"X4, OPTION {RECOMMENDED}: THE POLE STANDS A STEP IN FRONT OF THE WALL; THE HORNS HANG "
              "OVER A MAN'S HEAD.", small=True), after=GAP)

    height = y + GAP
    width = max(width, max(bx + t.shape[1] for bx, _, t in blocks) + GAP)
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = SHEET_BG
    for bx, by, tile in blocks:
        paste(canvas, tile, bx, by)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canvas).save(path, optimize=True)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preview", action="store_true", help="also write the CEO's sheet")
    args = ap.parse_args()
    sprites = build()
    for (opt, frame), rgba in sprites.items():
        print(f"{opt} {lump_name(frame)}: {rgba.shape[1]}x{rgba.shape[0]}, top {top_height(rgba)} units")
    if args.preview:
        print("sheet:", preview(sprites).relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
