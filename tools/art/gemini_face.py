"""Soviet Doom - the sergeant's face (the 42 STF lumps) from the CEO's Gemini sheets (D89).

    python tools/art/gen_hud.py --face gemini [--stamp YYYY-MM-DD_HHMM]

Sources (local only, gitignored, never copied out of work/; D77, D79):
  work/art/reference/gemini_face_grid.png      1024x1024, 5x5 cells on magenta.
      Columns: straight / head turned to screen-left / head turned to
      screen-right / ouch / evil grin. Rows: damage 0 (healthy) .. 4.
      (Measured on the image, not on the brief: column 2 shows the ear on the
      viewer's right and the star left of centre, so the head faces the
      viewer's LEFT; column 3 the opposite.)
  work/art/reference/gemini_face_god_dead.png  the same grid, but cells (0,0)
      and (1,0) are the GOD face (glowing eyes) and (0,3), (0,4) the DEAD face.

Doom's mapping, per damage level N (st_stuff.c): STFST{N}0..2 straight (the
engine cycles them as idle glances), STFTR{N}0 / STFTL{N}0 when hit from the
player's right / left (the face looks toward the attacker: TR looks to the
screen's right, TL to the screen's left), STFOUCH{N} a big hit, STFEVL{N} a
weapon pick-up, STFKILL{N} sustained fire; STFGOD0, STFDEAD0.

Pipeline (one cell -> the 35x32 face canvas = the bar's face area; the lump
is then the Freedoom box cut out of it, gen_hud.crop_face):
  1. cut the cell, key the magenta (gemini_frames.key_magenta);
  2. one fixed mapping for every cell (FIT): the cell's hat-top row to the
     canvas row 2, its bottom row to row 31, its centre column to the face
     axis; x scale = y scale x FACE_ASPECT (Doom's 1.2 tall pixels, partly
     corrected: a full correction leaves the face 5 rows short of its box);
  3. each canvas pixel is a box of ~6x7 source pixels; colour = the mean of
     the box, except that a salient class wins when it covers enough of the
     box (dark outline > red star / blood > yellow god glow > eye whites), so
     the 1-2 px features survive the reduction;
  4. snap to palette v2 (warm pixels to the warm ramps, as gen_hud does for
     skin, so the brown skin does not turn khaki); a 1-px dark outline on the
     silhouette (not on the bottom cut);
  5. STFST{N}0 / STFST{N}2 are STFST{N}1 with the eyes moved 1 px left /
     right (the two eye boxes are found as the eye-white blobs of the cell);
     STFKILL{N} is the straight cell's frown over the grin's bared teeth (the
     rows below the nose come from the grin cell): Doom's rampage snarl.
"""

from __future__ import annotations

import functools
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_hud as gh  # noqa: E402
from gemini_frames import key_magenta, neighbours_any  # noqa: E402

REF_DIR = gh.PROJECT_ROOT / "work" / "art" / "reference"
GRID = REF_DIR / "gemini_face_grid.png"
GOD_DEAD = REF_DIR / "gemini_face_god_dead.png"
OUT_SUB = "face_gemini"                 # work/art/hud/face_gemini/

CELLS = 5
COL = {"st": 0, "tl": 1, "tr": 2, "ouch": 3, "evl": 4}
GOD_CELL = (0, 0)                       # (row, col) in GOD_DEAD
DEAD_CELL = (0, 3)
CELL_INSET = 3                          # px of seam dropped at each cell side
FACE_ASPECT = 1.1                       # x scale / y scale (Doom pixels are 1.2 tall)
SRC_TOP, SRC_BOTTOM = 0, 199            # trimmed-cell rows: the hat touches the top; the cell bottom
CANVAS_TOP, CANVAS_BOTTOM = 2, 31       # canvas rows they land on (STFST box: rows 2..30)
OPAQUE_MIN = 0.5                        # fraction of keyed pixels for an opaque canvas pixel
DARK_V, DARK_MIN = 52, 0.42             # max channel below DARK_V: outline ink
RED_MIN = 0.28                          # star / blood
GLOW_MIN = 0.22                         # the god eyes
WARM_MAX_G = 175                        # brighter green: a yellow glow, not skin (full palette)
WHITE_MIN = 0.35                        # eye whites
WHITE_V = 200                           # min channel of an eye white (the dead grey skin is below)
KILL_SPLIT = 0.70                       # cell fraction: below this row the grin's mouth
OUTLINE = (27, 23, 20)                  # snapped later
EYE_BAND = (0.42, 0.62)                 # cell fraction where eye whites are looked for


# ------------------------------------------------------------ source
def available() -> bool:
    return GRID.is_file() and GOD_DEAD.is_file()


@functools.lru_cache(maxsize=2)
def _sheet(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).copy()


def cell(sheet: np.ndarray, row: int, col: int) -> tuple[np.ndarray, np.ndarray]:
    """(rgb, alpha) of one cell, the seam trimmed."""
    h, w = sheet.shape[:2]
    ch, cw = h / CELLS, w / CELLS
    y0, y1 = int(round(row * ch)) + CELL_INSET, int(round((row + 1) * ch)) - CELL_INSET
    x0, x1 = int(round(col * cw)) + CELL_INSET, int(round((col + 1) * cw)) - CELL_INSET
    rgb = sheet[y0:y1, x0:x1].copy()
    return rgb, key_magenta(rgb)


# ------------------------------------------------------------ classes
def classes(rgb: np.ndarray) -> dict[str, np.ndarray]:
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1)
    return {
        "dark": mx < DARK_V,
        "red": (r > 120) & (r > 2 * g) & (r > 2 * b),
        "glow": (r > 225) & (g > 190) & (b < 170) & (r - b > 60),
        "white": (r > WHITE_V) & (g > WHITE_V) & (b > WHITE_V - 25) & (mx - a.min(-1) < 50),
    }


def _edges(n_out: int, src0: float, src1: float, size: int) -> np.ndarray:
    return np.clip(np.round(np.linspace(src0, src1, n_out + 1)).astype(int), 0, size)


def canvas_map(cell_w: int):
    """Source x/y edges of every canvas column/row (the fixed FIT)."""
    sy = (CANVAS_BOTTOM - CANVAS_TOP) / (SRC_BOTTOM - SRC_TOP)
    sx = sy * FACE_ASPECT
    cx_src = cell_w / 2
    xs = cx_src + (np.arange(gh.FW + 1) - gh.CX) / sx
    ys = SRC_TOP + (np.arange(gh.FH + 1) - CANVAS_TOP) / sy
    return xs, ys


def reduce_cell(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """The cell on the 35x32 canvas: RGBA float (alpha 0/1), unsnapped."""
    h, w = alpha.shape
    xs, ys = canvas_map(w)
    xi = np.clip(np.round(xs).astype(int), 0, w)
    yi = np.clip(np.round(ys).astype(int), 0, h)
    cls = classes(rgb)
    out = np.zeros((gh.FH, gh.FW, 4), float)
    for j in range(gh.FH):
        for i in range(gh.FW):
            y0, y1, x0, x1 = yi[j], yi[j + 1], xi[i], xi[i + 1]
            if y1 <= y0 or x1 <= x0:
                continue
            a = alpha[y0:y1, x0:x1]
            if a.mean() < OPAQUE_MIN:
                continue
            px = rgb[y0:y1, x0:x1][a].astype(float)
            col = px.mean(0)
            for name, need in (("dark", DARK_MIN), ("red", RED_MIN), ("glow", GLOW_MIN), ("white", WHITE_MIN)):
                m = cls[name][y0:y1, x0:x1][a]
                if m.mean() >= need:
                    col = px[m].mean(0)
                    break
            out[j, i, :3], out[j, i, 3] = col, 1.0
    return out


# ------------------------------------------------------------ palette
# gen_hud's warm ramps minus flesh_pink: palette v2 has no light orange tan,
# and Gemini's skin highlights (~222,150,100) snap to flesh_pink's greyish
# pinks, which read as lilac streaks on the brown face. Without it they go to
# rust_brown's top step.
FACE_WARM_RAMPS = tuple(r for r in gh.SKIN_RAMPS if r != "flesh_pink")
_WARM_PAL = np.array([c for r in FACE_WARM_RAMPS for c in gh.palette.ramp_colours(r)], float)


def snap_face(rgba: np.ndarray) -> np.ndarray:
    """RGBA uint8: warm pixels to the warm ramps (skin, blood), the rest to all of palette v2."""
    rgb, a = rgba[..., :3], rgba[..., 3] > 0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    warm = a & (r > g + 12) & (g >= b - 4) & (r > 60) & (g < WARM_MAX_G)
    out = np.zeros(rgba.shape[:2] + (4,), np.uint8)
    if warm.any():
        out[warm, :3] = gh.snap(rgb[warm][None], _WARM_PAL)[0]
    rest = a & ~warm
    if rest.any():
        out[rest, :3] = gh.snap(rgb[rest][None])[0]
    out[a, 3] = 255
    return out


def outline(rgba: np.ndarray) -> np.ndarray:
    """Darken the silhouette's edge pixels (not the bottom rows cut by the bar)."""
    out = rgba.copy()
    a = out[..., 3] > 0
    edge = a & neighbours_any(~a)
    edge[CANVAS_BOTTOM - 3:] = False
    lum = out[..., :3].max(-1)
    ink = np.array(gh.snap1(OUTLINE), np.uint8)
    out[edge & (lum > 70), :3] = ink
    return out


# ------------------------------------------------------------ eyes
def eye_boxes(rgb: np.ndarray, alpha: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Canvas boxes (x0, y0, x1, y1) of the two eyes: the eye-white blobs of
    the cell in EYE_BAND, either side of the axis, padded to cover the iris."""
    h, w = alpha.shape
    white = classes(rgb)["white"] & alpha
    band = np.zeros_like(white)
    band[int(EYE_BAND[0] * h):int(EYE_BAND[1] * h)] = True
    white &= band
    xs, ys = canvas_map(w)
    boxes = []
    for side in (slice(0, w // 2), slice(w // 2, w)):
        m = np.zeros_like(white)
        m[:, side] = white[:, side]
        yy, xx = np.nonzero(m)
        if xx.size < 6:
            continue
        cx0, cx1 = np.searchsorted(xs, [xx.min(), xx.max()]) - 1
        cy0, cy1 = np.searchsorted(ys, [yy.min(), yy.max()]) - 1
        boxes.append((int(cx0) - 1, int(cy0), int(cx1) + 2, int(cy1) + 1))
    return boxes


def glance(canvas: np.ndarray, boxes, dx: int) -> np.ndarray:
    """Move what is inside each eye box dx px (the trailing column is kept)."""
    out = canvas.copy()
    for x0, y0, x1, y1 in boxes:
        src = canvas[y0:y1, x0:x1]
        moved = np.roll(src, dx, axis=1)
        if dx > 0:
            moved[:, :dx] = src[:, :1]
        elif dx < 0:
            moved[:, dx:] = src[:, -1:]
        keep = src[..., 3] > 0
        out[y0:y1, x0:x1][keep] = moved[keep]
    return out


# ------------------------------------------------------------ the 42
def finish(raw: np.ndarray) -> np.ndarray:
    return outline(snap_face(raw))


def _cell(kind: str, level: int):
    if kind == "god":
        return cell(_sheet(str(GOD_DEAD)), *GOD_CELL)
    if kind == "dead":
        return cell(_sheet(str(GOD_DEAD)), *DEAD_CELL)
    return cell(_sheet(str(GRID)), level, COL[kind])


@functools.lru_cache(maxsize=64)
def canvas(kind: str, level: int, gaze: int = 0) -> np.ndarray:
    """One face on the 35x32 canvas (RGBA uint8); kind as gen_hud.face_lump_spec."""
    if kind == "st":
        rgb, a = _cell("st", level)
        base = finish(reduce_cell(rgb, a))
        # the eyes are found on the healthy face (the framing is the same in
        # every row; blood and the grey skin of row 4 confuse the search)
        return glance(base, eye_boxes(*_cell("st", 0)), gaze) if gaze else base
    if kind == "kill":
        rgb, a = _cell("st", level)
        g_rgb, g_a = _cell("evl", level)
        cut = int(KILL_SPLIT * rgb.shape[0])
        rgb, a = rgb.copy(), a.copy()
        rgb[cut:], a[cut:] = g_rgb[cut:], g_a[cut:]
        return finish(reduce_cell(rgb, a))
    return finish(reduce_cell(*_cell(kind, level)))


def face_lumps() -> dict[str, np.ndarray]:
    out = {}
    for name in gh.FACE_LUMPS:
        level, kind, gaze = gh.face_lump_spec(name)
        out[name] = gh.crop_face(canvas(kind, level, gaze), name)
    return out


def build(out_dir: Path) -> dict[str, Path]:
    """Write the 42 lumps (RGBA PNG with Freedoom's grAb) under out_dir/face_gemini."""
    if not available():
        raise FileNotFoundError(f"Gemini face sheets not found under {REF_DIR}")
    out = {}
    for name, rgba in face_lumps().items():
        out[name] = gh.save_rgba(rgba, Path(out_dir) / OUT_SUB / f"{name}.png", gh.grab_of(name))
    return out


# ------------------------------------------------------------ preview
LADDER_COLS = ("STFST{}0", "STFST{}1", "STFST{}2", "STFTL{}0", "STFTR{}0", "STFOUCH{}", "STFEVL{}", "STFKILL{}")
LADDER_ZOOM, MOCK_ZOOM = 4, 2
MOCKS = (  # (caption, gen_hud state for the numbers, face lump)
    ("HEALTHY STFST01", "start", "STFST01"),
    ("HURT STFST31", "fight", "STFST31"),
    ("OUCH STFOUCH3", "fight", "STFOUCH3"),
    ("GRIN STFEVL0", "start", "STFEVL0"),
)
INK, PAPER = (226, 214, 180), (34, 36, 32)


def _zoom(a: np.ndarray, z: int) -> np.ndarray:
    return np.kron(a, np.ones((z, z) + (1,) * (a.ndim - 2), a.dtype))


def _label(img, text, cx, y, z=2):
    m = gh.text_mask(text)
    big = _zoom(m.astype(np.uint8), z).astype(bool)
    x = int(cx - big.shape[1] / 2)
    gh.stamp_mask(img, big, x, y, INK)


def preview(path: Path) -> Path:
    """The 42 lumps at 4x in Doom's ladder (each on status bar A's face
    recess, placed by its own offsets) over four MAP01 mocks at 2x."""
    lumps = face_lumps()
    bar = gh.render_bar("A", "en")
    arms = gh.render_arms("A", "en")
    digits = gh.digit_set(gh.RECOMMENDED["digits"])
    recess = bar[:, gh.FACE_BOX[0]:gh.FACE_BOX[2]]
    cw, chh = gh.FW * LADDER_ZOOM, gh.FH * LADDER_ZOOM
    pad, lab = 10, 16
    W = len(LADDER_COLS) * (cw + pad) + pad
    rows = []
    for lv in range(6):
        names = [c.format(lv) for c in LADDER_COLS] if lv < 5 else ["STFGOD0", "STFDEAD0"]
        strip = np.zeros((chh + lab + pad, W, 3), np.uint8)
        strip[:] = PAPER
        for k, name in enumerate(names):
            tile = recess.copy()
            w, h, lo, to = gh.FD_LUMPS[name]
            gh._blit(tile, lumps[name], -lo, -to)    # the recess starts at POS_FACE
            x = pad + k * (cw + pad)
            strip[lab:lab + chh, x:x + cw] = _zoom(tile, LADDER_ZOOM)
            _label(strip, name, x + cw // 2, 2)
        rows.append(strip)
    shots = []
    for cap, state, name in MOCKS:
        w, h, lo, to = gh.FD_LUMPS[name]
        scr = gh.mock(bar, arms, digits, None, state, face_rgba=lumps[name], face_off=(lo, to))
        tile = np.zeros((200 * MOCK_ZOOM + lab, 320 * MOCK_ZOOM, 3), np.uint8)
        tile[:] = PAPER
        tile[lab:] = _zoom(scr, MOCK_ZOOM)
        _label(tile, cap, tile.shape[1] // 2, 2)
        shots.append(tile)
    mw = 2 * shots[0].shape[1] + 3 * pad
    grid = np.zeros((2 * shots[0].shape[0] + 3 * pad, mw, 3), np.uint8)
    grid[:] = PAPER
    for i, s in enumerate(shots):
        y, x = pad + (i // 2) * (s.shape[0] + pad), pad + (i % 2) * (s.shape[1] + pad)
        grid[y:y + s.shape[0], x:x + s.shape[1]] = s
    full_w = max(W, mw)
    ladder = np.vstack(rows)
    out = np.zeros((ladder.shape[0] + grid.shape[0], full_w, 3), np.uint8)
    out[:] = PAPER
    out[:ladder.shape[0], (full_w - W) // 2:(full_w - W) // 2 + W] = ladder
    out[ladder.shape[0]:, (full_w - mw) // 2:(full_w - mw) // 2 + mw] = grid
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGB").save(path, optimize=True)
    return path
