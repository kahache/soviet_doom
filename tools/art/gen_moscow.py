"""Episode 2, MAP06 — the Moscow set: Red Square and the Kremlin (D104, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_moscow.py
The whole episode and the CEO's sheet: tools/art/gen_episode2.py.

DRAFTS for the CEO: PNGs to work/art/episode2/moscow/, never to assets/.
Palette v1, and v2 only for marble_red where a piece is brick (the Kremlin
wall, its merlons, the parade banner hung on it, the Spasskaya tower), as
the factory brick SDBRCK1 was approved (D66). No text anywhere: the parade
banner carries the star and the hammer and sickle only (the approved
geometry, gen_soviet_base.hammer_sickle).

Not drawn on purpose: the red marble of Ploshchad Revolyutsii. The metro set
already has it, approved (SDMARB1, D42); MAP06 reuses that lump.

D12 (LORE.md): the Kremlin and Red Square appear as places and stone; no
figure, no portrait, nothing that touches real victims. The granite of the
tribune is material only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, fbm, grain, shade, star_points, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import Piece, col  # noqa: E402
import gen_factory  # noqa: E402  (brick bond geometry)
import gen_soviet_base as base  # noqa: E402  (the approved hammer and sickle)

SET_NAME = "moscow"
SCRIPT_REL = "tools/art/gen_moscow.py"
BATCH_SEED = 5600
WALL_W, WALL_H, WIDE, FLAT = 64, 128, 128, 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ setts
SETT_W, SETT_H = 8, 8
SETT_TONE = 0.34             # concrete_cold: dark diabase setts
SETT_BLUE = 0.25             # share of bluer stones (steel_blue)


def setts(w: int, h: int, rng: np.random.Generator) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    row = yy // SETT_H
    offs = rng.integers(0, SETT_W, h // SETT_H)
    lx = (xx + offs[row]) % SETT_W
    ly = yy % SETT_H
    cid = row * (w // SETT_W) + ((xx + offs[row]) // SETT_W) % (w // SETT_W)
    n = h // SETT_H * (w // SETT_W)
    tone = SETT_TONE + rng.uniform(-0.07, 0.07, n)
    blue = rng.random(n) < SETT_BLUE
    field = tone[cid] + grain(w, h, rng, 0.03) + (fbm(w, h, 8, 2, rng) - 0.5) * 0.06
    rgb = np.where(blue[cid][..., None], to_rgb(np.clip(field, 0, 1), "steel_blue"),
                   to_rgb(np.clip(field, 0, 1), "concrete_cold"))
    f = np.ones((h, w))
    f[(ly == 1) | (lx == 1)] = 1.22
    f[(ly == SETT_H - 1) | (lx == SETT_W - 1)] = 0.70
    joint = (ly == 0) | (lx == 0)
    f[joint] = 0.30
    corner = ((ly == 1) | (ly == SETT_H - 1)) & ((lx == 1) | (lx == SETT_W - 1))
    f[corner] = 0.55
    return shade(rgb, f)


def tex_cobl1() -> np.ndarray:
    """Red Square paving: dark diabase setts in rows, each row shifted,
    rounded and polished by parades."""
    return setts(FLAT, FLAT, rng_for(1))


STRIPE_Y0, STRIPE_Y1 = 28, 36
SLAB_W = 16


def tex_cobl2() -> np.ndarray:
    """The setts with a line of pale granite kerb slabs: the lines that
    divide Red Square into fields."""
    rng = rng_for(2)
    w = h = FLAT
    rgb = setts(w, h, rng)
    yy, xx = np.mgrid[0:h, 0:w]
    band = (yy >= STRIPE_Y0) & (yy < STRIPE_Y1)
    field = 0.66 + rng.uniform(-0.04, 0.04, w // SLAB_W)[xx // SLAB_W] + grain(w, h, rng, 0.03)
    slab = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    f = np.ones((h, w))
    f[yy == STRIPE_Y0] = 1.15
    f[yy == STRIPE_Y1 - 1] = 0.70
    f[band & (xx % SLAB_W == 0)] = 0.45
    slab = shade(slab, f)
    rgb = np.where(band[..., None], slab, rgb)
    rgb[STRIPE_Y1, :] = shade(rgb[STRIPE_Y1, :], 0.6)
    return rgb


# ================================================================ Kremlin brick
KREM_MID = 0.60              # marble_red: the Kremlin's red, brighter and cleaner than the works' brick
KREM_JITTER = 0.06
KREM_PATCH = 0.07            # share of newer, restored bricks
KREM_MORTAR = 0.64           # plaster_warm: pale lime joints


def kremlin_brick(w: int, h: int, rng: np.random.Generator) -> np.ndarray:
    row, colm, lx, ly = gen_factory.brick_courses(w, h)
    ny, nx = h // gen_factory.BRICK_H, w // gen_factory.BRICK_W
    tone = KREM_MID + rng.uniform(-KREM_JITTER, KREM_JITTER, (ny, nx))
    patch = rng.random((ny, nx)) < KREM_PATCH
    tone = np.where(patch, tone + 0.10, tone)
    field = tone[row, colm] + (fbm(w, h, 8, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    rgb = ep2lib.any_to_rgb(np.clip(field, 0, 1), "marble_red")
    mortar = (lx < gen_factory.MORTAR) | (ly < gen_factory.MORTAR)
    mfield = KREM_MORTAR + (fbm(w, h, 6, 2, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    rgb = np.where(mortar[..., None], to_rgb(np.clip(mfield, 0, 1), "plaster_warm"), rgb)
    f = np.ones((h, w))
    f[(ly == 1) & ~mortar] = 1.12
    f[ly == gen_factory.BRICK_H - 1] *= 0.80
    # rain: faint vertical washes, lighter and darker
    f *= 1 + (fbm(w, h, 8, 3, rng, 0.5, aspect=8.0) - 0.5) * 0.18
    return shade(rgb, f)


def tex_krem1() -> np.ndarray:
    """The Kremlin wall: red brick in running bond, pale lime joints, a few
    restored bricks, rain washes. Cleaner and redder than SDBRCK1."""
    return kremlin_brick(WALL_W, WALL_H, rng_for(3))


MERLON_X = (10, 54)          # one swallowtail merlon per 64 px
MERLON_TOP_H = 64            # merlons occupy rows 0..63; the parapet below
NOTCH_DEPTH, NOTCH_HALF = 22, 17
SLIT = (31, 33, 30, 46)      # the loophole


def tex_krem2() -> np.ndarray:
    """The Kremlin's swallowtail merlon («ласточкин хвост»), MASKED: the
    same brick as SDKREM1 pixel for pixel, cut to an M-shaped merlon with a
    loophole; sky shows between the merlons and in the notch."""
    rgb = kremlin_brick(WALL_W, WALL_H, rng_for(3))
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    inside = (xx >= MERLON_X[0]) & (xx < MERLON_X[1])
    notch = yy < NOTCH_DEPTH - np.abs(xx + 0.5 - 32) * NOTCH_DEPTH / NOTCH_HALF
    solid = (yy >= MERLON_TOP_H) | (inside & ~notch)
    f = np.ones((h, w))
    # light on the merlon's top edges and left side, shade on the right
    top_edge = solid & ~np.roll(solid, 1, axis=0)
    top_edge[0] = solid[0]
    f[top_edge] = 1.35
    f[solid & (xx == MERLON_X[0]) & (yy < MERLON_TOP_H)] = 1.20
    f[solid & (xx == MERLON_X[1] - 1) & (yy < MERLON_TOP_H)] = 0.60
    f[solid & (xx == MERLON_X[1] - 2) & (yy < MERLON_TOP_H)] = 0.80
    rgb = shade(rgb, f)
    x0, x1, y0, y1 = SLIT
    rgb[y0:y1, x0:x1] = col("concrete_cold", 0.04)
    rgb[y0 - 1, x0 - 1:x1 + 1] = col("marble_red", 0.40)
    rgb[y0:y1, x1] = col("marble_red", 0.80)
    alpha = np.where(solid, 255, 0).astype(np.uint8)
    out = np.dstack([np.where(solid[..., None], rgb, 0).astype(np.uint8), alpha])
    return out


# ================================================================ GUM facade
STONE_TONE = 0.74            # plaster_warm: the pale stone of GUM
ARCH_C, ARCH_R = (64, 58), 32
WIN_X0, WIN_X1, WIN_Y1 = 32, 96, 108
PIER = 10                    # half a pilaster at each tile edge


def tex_gum1() -> np.ndarray:
    """GUM's facade, one bay: pale stone in courses, a round-arched window
    (dark glass, white frames, a fanlight), voussoirs and keystone, half a
    rusticated pilaster at each edge, a dentil cornice, the sill."""
    rng = rng_for(4)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w] + 0.0
    course = (yy // 8).astype(int)
    off = (course % 2) * 16
    block = ((xx + off) // 32).astype(int)
    bt = rng.uniform(-0.04, 0.04, (h // 8 + 1, w // 32 + 2))
    field = STONE_TONE + bt[course, block] + (fbm(w, h, 6, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.025)
    rgb = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    f = np.ones((h, w))
    f[(yy % 8) == 0] *= 0.82
    f[((xx + off) % 32) == 0] *= 0.86
    pier = (xx < PIER) | (xx >= w - PIER)
    f[pier] *= 1.06
    f[pier & ((yy % 8) == 0)] *= 0.70          # rustication grooves
    f[pier & ((yy % 8) == 1)] *= 1.12
    f[:, PIER] *= 0.70
    f[:, w - PIER - 1] *= 0.80
    # grime: soot under the cornice and in the joints
    f *= 1 - np.clip(fbm(w, h, 4, 3, rng, aspect=4.0) - 0.55, 0, 1) * 0.4
    rgb = shade(rgb, f)
    cx, cy = ARCH_C
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    r = np.hypot(dx, dy)
    opening = ((xx >= WIN_X0) & (xx < WIN_X1) & (yy >= cy) & (yy < WIN_Y1)) | ((yy < cy) & (r < ARCH_R))
    reveal = ((xx >= WIN_X0 - 3) & (xx < WIN_X1 + 3) & (yy >= cy) & (yy < WIN_Y1)) | ((yy < cy) & (r < ARCH_R + 3))
    vous = (yy < cy) & (r >= ARCH_R + 3) & (r < ARCH_R + 9)
    # voussoirs: lighter ring with radial joints
    ang = np.degrees(np.arctan2(dy, dx))
    vjoint = vous & (np.abs(((ang + 180) % 15) - 7.5) > 6.6)
    rgb = np.where(vous[..., None], shade(rgb, 1.08), rgb)
    rgb = np.where(vjoint[..., None], shade(rgb, 0.70), rgb)
    rgb = np.where((reveal & ~opening)[..., None], shade(rgb, 0.62), rgb)
    glass = to_rgb(np.clip(0.16 + (fbm(w, h, 3, 3, rng) - 0.5) * 0.10 + np.clip(-dy / 140, 0, 0.12), 0, 1), "steel_blue")
    # a reflection streak across the panes
    glass = np.where((np.abs((xx - yy * 0.6) % 48 - 20) < 3)[..., None], shade(glass, 1.6), glass)
    rgb = np.where(opening[..., None], glass, rgb)
    ov = Overlay(w, h)
    frame = col("plaster_warm", 0.95)
    ov.rect(cx - 1, cy - ARCH_R, cx + 1, WIN_Y1, fill=frame)
    ov.rect(WIN_X0, 76, WIN_X1, 78, fill=frame)
    ov.rect(WIN_X0, cy - 1, WIN_X1, cy + 1, fill=frame)
    for a in (30, 60, 120, 150):
        t = np.deg2rad(a)
        ov.line([(cx, cy), (cx - ARCH_R * np.cos(t), cy - ARCH_R * np.sin(t))], frame, 1.3)
    ov.ellipse(cx - 8, cy - 8, cx + 8, cy + 8, outline=frame, width=1.3)
    for xm in (48, 80):
        ov.rect(xm - 0.6, cy, xm + 0.6, WIN_Y1, fill=col("plaster_warm", 0.85))
    # keystone
    ov.polygon([(cx - 5, cy - ARCH_R - 11), (cx + 5, cy - ARCH_R - 11), (cx + 3, cy - ARCH_R - 1),
                (cx - 3, cy - ARCH_R - 1)], col("plaster_warm", 0.92))
    ov.rect(cx + 3, cy - ARCH_R - 11, cx + 5, cy - ARCH_R - 1, fill=col("plaster_warm", 0.55))
    rgb = ov.composite(rgb)
    # sill
    rgb[WIN_Y1:WIN_Y1 + 4, WIN_X0 - 6:WIN_X1 + 6] = col("plaster_warm", 0.86)
    rgb[WIN_Y1, WIN_X0 - 6:WIN_X1 + 6] = col("plaster_warm", 0.98)
    rgb[WIN_Y1 + 4, WIN_X0 - 6:WIN_X1 + 6] = col("plaster_warm", 0.30)
    # cornice with dentils
    rgb[0:3, :] = col("plaster_warm", 0.84)
    rgb[0, :] = col("plaster_warm", 0.96)
    for x in range(w):
        rgb[3:7, x] = col("plaster_warm", 0.80 if x % 4 < 2 else 0.36)
    rgb[7, :] = col("plaster_warm", 0.30)
    return rgb


# ================================================================ tribune granite
BLOCK_W, BLOCK_H = 64, 32
GRANITE_TONE = 0.32          # flag_red low: ox-blood, the dark red granite
BAND_H = 10                  # black labradorite band at the top of each 128


def tex_trib1() -> np.ndarray:
    """Polished dark red granite in 64x32 blocks, speckled black, pink and
    grey, a soft reflection, and a band of black labradorite with blue
    flashes along the top (the tribune's coping)."""
    rng = rng_for(5)
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    row = yy // BLOCK_H
    bt = rng.uniform(-0.03, 0.03, h // BLOCK_H + 1)
    clus = fbm(w, h, 16, 2, rng)
    field = GRANITE_TONE + bt[row] + (clus - 0.5) * 0.12 + grain(w, h, rng, 0.04)
    rgb = to_rgb(np.clip(field, 0, 1), "flag_red")
    r = rng.random((h, w))
    rgb[r < 0.06] = col("concrete_cold", 0.08)
    rgb[(r > 0.93) & (clus > 0.45)] = col("flag_red", 0.48)
    rgb[r > 0.985] = col("plaster_warm", 0.55)
    f = np.ones((h, w))
    f *= 1 + 0.10 * np.exp(-(((xx + yy * 0.5) % 96 - 30) / 9.0) ** 2)
    joint_x = np.where(row % 2 == 0, 0, 32)
    f[(yy % BLOCK_H) == 0] = 0.45
    f[xx == joint_x] = 0.50
    rgb = shade(rgb, f)
    band = yy < BAND_H
    lab = to_rgb(np.clip(0.07 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.06 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    flash = (fbm(w, h, 16, 2, rng, aspect=0.5) > 0.66) & (rng.random((h, w)) < 0.5)
    lab = np.where(flash[..., None], np.array(col("steel_blue", 0.55), np.uint8), lab)
    rgb = np.where(band[..., None], lab, rgb)
    rgb[0, :] = col("concrete_cold", 0.30)
    rgb[BAND_H - 1, :] = col("concrete_cold", 0.02)
    return rgb


# ================================================================ parade banner
CLOTH = (8, 56, 7, 110)      # x0, x1, y0, y1
ROD_Y = 3
FRINGE_H = 4
STAR_C, STAR_R = (32, 30), 11
HS_C, HS_R = (32, 70), 16


def tex_banr1() -> np.ndarray:
    """Parade banner hung on the Kremlin wall (SDKREM1's own pixels): kumach
    red with folds, a gold star and the approved hammer and sickle, a gold
    fringe, the rod and its brackets. No text."""
    rng = rng_for(6)
    w, h = WALL_W, WALL_H
    wall = kremlin_brick(w, h, rng_for(3))
    x0, x1, y0, y1 = CLOTH
    yy, xx = np.mgrid[0:h, 0:w]
    cloth_m = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    red = to_rgb(np.clip(0.72 + grain(w, h, rng, 0.02), 0, 1), "flag_red")
    ov = Overlay(w, h)
    gold = col("hazard_yellow", 0.88)
    dark = col("flag_red", 0.30)
    g = ov.group(outline=dark, outline_width=1.0)
    g.polygon(star_points(STAR_C[0], STAR_C[1], STAR_R), gold)
    ov.end_group(g)
    base.hammer_sickle(ov, HS_C[0], HS_C[1], HS_R, gold, dark)
    ov.rect(x0 + 3, y0 + 3, x1 - 3, y0 + 4, fill=col("hazard_yellow", 0.70))
    ov.rect(x0 + 3, y1 - 5, x1 - 3, y1 - 4, fill=col("hazard_yellow", 0.70))
    cloth = ov.composite(red)
    fold = 1 + 0.12 * np.sin(2 * np.pi * 3 * (xx - x0) / (x1 - x0))
    fold *= 1 + 0.04 * (fbm(w, h, 4, 2, rng, aspect=4.0) - 0.5)
    cloth = shade(cloth, fold)
    shadow = np.roll(np.roll(cloth_m, 2, axis=0), 2, axis=1) & ~cloth_m
    rgb = np.where(shadow[..., None], shade(wall, 0.5), wall)
    rgb = np.where(cloth_m[..., None], cloth, rgb)
    fringe = (xx >= x0) & (xx < x1) & (yy >= y1) & (yy < y1 + FRINGE_H) & ((xx % 2 == 0) | (yy < y1 + 1))
    rgb[fringe] = col("hazard_yellow", 0.70)
    rgb[ROD_Y:ROD_Y + 3, 2:w - 2] = col("steel_blue", 0.30)
    rgb[ROD_Y, 2:w - 2] = col("hazard_yellow", 0.80)
    for bx in (4, w - 6):
        rgb[ROD_Y - 2:ROD_Y + 6, bx:bx + 2] = col("steel_blue", 0.15)
    for cx in (x0 + 2, x1 - 3):
        rgb[ROD_Y + 3:y0, cx] = col("hazard_yellow", 0.60)
    return rgb


# ================================================================ Spasskaya
LIME_TONE = 0.88             # plaster_warm: the tower's white limestone
FRIEZE_H = 26
ARCADE_CELL = 16
STRING_Y0, STRING_Y1 = 102, 110
PILASTER = 5


def tex_spas1() -> np.ndarray:
    """Spasskaya tower: red brick with white limestone dressing, a frieze
    of pointed blind arches with hanging drops, white pilaster strips at
    the tile edges, a dentilled stringcourse."""
    rng = rng_for(7)
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = kremlin_brick(w, h, rng)
    lime = to_rgb(np.clip(LIME_TONE + (fbm(w, h, 6, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.025), 0, 1),
                  "plaster_warm")
    white = (yy < FRIEZE_H) | ((yy >= STRING_Y0) & (yy < STRING_Y1)) | (xx < PILASTER) | (xx >= w - PILASTER)
    rgb = np.where(white[..., None], lime, rgb)
    lx = xx % ARCADE_CELL
    arch = (lx >= 3) & (lx < 13) & (yy >= 6) & (yy < FRIEZE_H - 3) & \
        (yy >= 6 + ((lx + 0.5 - 8) ** 2) / 25.0 * 7)
    rgb = np.where(arch[..., None], shade(lime, 0.58), rgb)
    f = np.ones((h, w))
    arch_top = arch & ~np.roll(arch, 1, axis=0)
    f[arch_top] = 0.70
    f[arch & (lx == 3)] = 0.65
    f[arch & (lx == 12)] = 1.10
    f[FRIEZE_H - 1, :] = 0.55
    f[FRIEZE_H, :] *= 0.60
    f[0, :] = 1.15
    f[STRING_Y0, :] = 1.15
    f[STRING_Y1 - 1, :] = 0.55
    f[STRING_Y1, :] *= 0.55
    dent = (yy >= STRING_Y0 + 3) & (yy < STRING_Y0 + 6) & (xx % 4 >= 2)
    f[dent] *= 0.55
    f[:, PILASTER - 1] *= 0.70
    f[:, w - PILASTER] *= 1.15
    rgb = shade(rgb, f)
    # the hanging drops between the arches
    for x in range(0, w, ARCADE_CELL):
        for k, t in enumerate((0.95, 0.80, 0.55)):
            rgb[FRIEZE_H - 3 + k, (x - 1) % w:(x - 1) % w + 2] = col("plaster_warm", t)
    # soot along the limestone's lower edges
    return rgb


# ================================================================ pieces
V2_BRICK = "v2 solo por marble_red, como SDBRCK1 aprobado (D66): v1 no tiene rojo de ladrillo cocido."
PIECES = [
    Piece("SDCOBL1", tex_cobl1, "flat", (64, 64), ["SDCOBL1"], 1, "xy",
          "Adoquín de la Plaza Roja",
          "Adoquines de diabasa oscura en hiladas, cada hilada desplazada, redondeados y pulidos por los desfiles.",
          rec_why="El suelo del mapa; oscuro a propósito para que la muralla roja mande."),
    Piece("SDCOBL2", tex_cobl2, "flat", (64, 64), ["SDCOBL2"], 2, "x",
          "Adoquín con franja de granito",
          "Los mismos adoquines con una línea de losas de granito claro: las líneas que dividen la plaza en campos.",
          rec_why="Para trazar la plaza; la franja va a lo largo de x (girar en UDMF para la otra dirección)."),
    Piece("SDKREM1", tex_krem1, "wall", (64, 128), ["SDKREM1"], 3, "xy",
          "Muro del Kremlin",
          "Ladrillo rojo del Kremlin en aparejo a soga, juntas de cal claras, algunos ladrillos restaurados, "
          "lavados de lluvia. Más limpio y más rojo que SDBRCK1.",
          palette=2, why_v2=V2_BRICK,
          rec_why="Se distingue del ladrillo industrial (sin hollín, juntas claras): es el mismo material, otro rango."),
    Piece("SDKREM2", tex_krem2, "wall", (64, 128), ["SDKREM2"], 3, "x",
          "Almena «cola de golondrina» (enmascarada)",
          "Remate de la muralla, ENMASCARADA: el mismo ladrillo que SDKREM1 píxel a píxel, recortado en merlón en "
          "M con aspillera; entre merlones y en la muesca se ve el cielo.",
          palette=2, masked=True, why_v2=V2_BRICK,
          rec_why="Misma excepción RGBA que SDCHAN1. Mitad superior merlón, mitad inferior parapeto: colocar con la "
                  "parte de abajo enrasada con SDKREM1. Comparte semilla con SDKREM1 para que el aparejo siga.",
          scene={"left": "SDKREM2", "right": "SDKREM2", "back": "SDKREM2"}),
    Piece("SDGUM1", tex_gum1, "wall", (128, 128), ["SDGUM1"], 4, "x",
          "Fachada de los GUM",
          "Fachada de los almacenes GUM, una crujía: piedra clara en hiladas, ventana de medio punto (vidrio oscuro, "
          "carpintería blanca, abanico), dovelas y clave, media pilastra almohadillada en cada borde, cornisa con "
          "dentículos, alféizar.",
          rec_why="La piedra clara es la pared donde mejor se leerán los enemigos en el mapa (ART-BIBLE §6)."),
    Piece("SDTRIB1", tex_trib1, "wall", (64, 128), ["SDTRIB1"], 5, "xy",
          "Granito de la tribuna",
          "Granito rojo oscuro pulido en bloques de 64x32, moteado negro, rosa y gris, un reflejo suave y una banda "
          "de labradorita negra con destellos azules arriba.",
          rec_why="Solo material (D12): sin inscripción ni referencia al mausoleo. Rojo de flag_red bajo, v1."),
    Piece("SDBANR1", tex_banr1, "wall", (64, 128), ["SDBANR1"], 6, "x",
          "Pancarta del desfile",
          "Pancarta del desfile colgada en el muro del Kremlin (los píxeles de SDKREM1): rojo kumach con pliegues, "
          "estrella dorada y la hoz y el martillo aprobados, flecos dorados, barra y soportes. Sin texto.",
          palette=2, why_v2="v2 solo porque cuelga sobre los píxeles de SDKREM1; la tela es v1.",
          rec_why="Colgar alta, como SDFLAG1/2 (ART-BIBLE §6): delante del pecho de un enemigo rompe la lectura.",
          scene={"left": "SDKREM1", "right": "SDKREM1"}),
    Piece("SDSPAS1", tex_spas1, "wall", (64, 128), ["SDSPAS1"], 7, "xy",
          "Piedra de la torre Spásskaya",
          "Torre Spásskaya: ladrillo rojo con aderezos de piedra caliza blanca, friso de arquillos apuntados con "
          "pinjantes, pilastras blancas en los bordes y una imposta con dentículos.",
          palette=2, why_v2=V2_BRICK,
          rec_why="El blanco sobre rojo es lo que hace «Kremlin» a un golpe de vista; tila en los dos ejes."),
]

# The metro's approved red marble serves MAP06's Ploshchad Revolyutsii.
REUSED = [("SDMARB1", "Mármol rojo de Plóshchad Revolyutsii: ya existe en el set Metro, aprobado (D42). Se reutiliza; "
                      "no se dibuja otro.")]

ROOM = {"wall": "SDKREM1", "floor": "SDCOBL1", "ceil": None, "light": 1.0}
OVERVIEWS = [
    ("La Plaza Roja", {"left": "SDGUM1", "right": "SDBANR1", "back": "SDSPAS1", "floor": "SDCOBL2"}),
    ("La muralla y la tribuna", {"left": "SDTRIB1", "right": "SDTRIB1", "back": "SDKREM2", "floor": "SDCOBL1"}),
]


def build(out_dir: Path | None = None):
    return ep2lib.build_set(SET_NAME, PIECES, BATCH_SEED, SCRIPT_REL, out_dir)


def main() -> None:
    entries, _ = build()
    for e in entries:
        print(f'{e["piece"]:8s} {e["width"]:3d}x{e["height"]:3d} v{e["palette_version"]} '
              f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')


if __name__ == "__main__":
    main()
