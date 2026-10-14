"""Hand study and weapon scale study (D55): two dated preview PNGs, no asset.

    python tools/art/hand_study.py scale    # weapon size on screen vs Doom/Freedoom
    python tools/art/hand_study.py hands    # one pose, four hand variants H1-H4
    python tools/art/hand_study.py all

Scale: every first-person sprite is placed on the 320x200 virtual screen the
way the engine places it (top-left = (-leftoffset, WEAPONTOP - topoffset),
WEAPONTOP = 32) and measured: opaque area and height above the status bar.
Ours come from the drafts' PNGs (grAb offsets); the references are read
from Freedoom's IWAD (BSD-3, used as a yardstick only, nothing copied).

Hands: a right hand gripping a pistol grip (a neutral grey cylinder, no
weapon), seen from the player: muzzle up-left, so the grip shows its LEFT
side (thumb, the fingertips of middle/ring/little with their nails, the
index forward on the absent trigger). The hand is built from measured
bones (BONES_MM), each segment a tapered capsule shaded per pixel, then
cut to pixel art: outline, part separation lines, nails, knuckles.

Outputs: work/art/hand_study/ (frames, metrics.json) and two previews in
docs/art/previews/. Nothing goes to assets/ (D55: hands first, alone).
"""

from __future__ import annotations

import json
import math
import struct
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402

ROOT = artlib.PROJECT_ROOT
IWAD = ROOT / "iwads" / "freedoom2.wad"
OUT_DIR = ROOT / "work" / "art" / "hand_study"
PREVIEW_DIR = ROOT / "docs" / "art" / "previews"
MAP01_SHOT = ROOT / "docs" / "qa" / "evidence" / "2026-10-13_1448_F3_smoke-map01-windows.png"

# ------------------------------------------------------------ screen model
SCREEN_W, SCREEN_H = 320, 200
STATUS_BAR_H = 32
VIEW_H = SCREEN_H - STATUS_BAR_H          # 168: what the player sees above the bar
WEAPONTOP = 32                            # psprite y at rest (Doom source, p_pspr.h)
TOLERANCE = 0.10                          # target band: reference height +-10 %
# With the status bar on (every capture the CEO has seen) the 3D view is
# 320x168 and the psprite is centred on THAT window (centery 84, not 100):
# the weapon sits 16 px higher than in full-screen. Checked on the filed
# smoke shot: Freedoom's PISGA0 top predicted at y 113, seen at ~112.
BAR_LIFT = (SCREEN_H - VIEW_H) // 2        # 16
PIXEL_ASPECT = 1.2                         # Doom's 320x200 is shown at 4:3
SHOT_BAR_TOP = 243                         # status bar's first row in MAP01_SHOT (measured)
SHOT_PISTOL_BOX = (196, 286, 150)          # x0, x1, y0 of Freedoom's pistol in MAP01_SHOT

# Ours (ready frame of each weapon) -> the Doom weapon it stands in for.
PAIRS = [
    # weapon, folder, ready lump, reference lump, why this reference
    ("TT-33", "tt33", "SDTTA0", "PISGA0", "sidearm"),
    ("IZh-58", "izh", "SDIZA0", "SHTGA0", "shotgun"),
    ("PPSh-41", "ppsh", "SDPPA0", "CHGGA0", "automatic"),
    ("RPG-7", "rpg7", "SDRLA0", "MISGA0", "launcher"),
    ("ROKS-3", "roks3", "SDRKA0", "PLSGA0", "energy/flame slot"),
    ("Hand Katyusha", "katyusha", "SDHKA0", "BFGGA0", "super weapon"),
    # Doom's fist (PUNGA0, 24 px) is too low to model a raised pick: the
    # axe is a one-hand tool, so it is held to the sidearm's band.
    ("Ice axe", "ice_axe", "SDAXA0", "PISGA0", "one-hand tool (PUNG too low to compare)"),
]
DOOM_LUMPS = ["PISGA0", "SHTGA0", "CHGGA0", "MISGA0", "PLSGA0", "BFGGA0", "PUNGA0"]
OUR_SETS = [("2D hands (D52)", ROOT / "work" / "art" / "weapons_2d"),
            ("3D hands (before D52)", ROOT / "work" / "art" / "weapons")]


# ------------------------------------------------------------------ WAD
def read_wad(path: Path = IWAD) -> tuple[dict[str, bytes], np.ndarray]:
    """{lump: bytes} of a WAD plus its PLAYPAL's first palette (256x3)."""
    blob = path.read_bytes()
    _, count, offset = struct.unpack("<4sii", blob[:12])
    lumps: dict[str, bytes] = {}
    for i in range(count):
        pos, size, raw = struct.unpack("<ii8s", blob[offset + 16 * i: offset + 16 * i + 16])
        lumps.setdefault(raw.rstrip(b"\0").decode("ascii", "replace"), blob[pos:pos + size])
    pal = np.frombuffer(lumps["PLAYPAL"][:768], np.uint8).reshape(256, 3)
    return lumps, pal


def decode_patch(data: bytes, pal: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    """Doom picture format -> RGBA array and (leftoffset, topoffset)."""
    w, h, left, top = struct.unpack("<hhhh", data[:8])
    img = np.zeros((h, w, 4), np.uint8)
    for x, col in enumerate(struct.unpack(f"<{w}i", data[8:8 + 4 * w])):
        c = col
        while data[c] != 255:
            y0, n = data[c], data[c + 1]
            for j in range(n):
                if 0 <= y0 + j < h:
                    img[y0 + j, x, :3] = pal[data[c + 3 + j]]
                    img[y0 + j, x, 3] = 255
            c += n + 4
    return img, (left, top)


def read_png_sprite(path: Path) -> tuple[np.ndarray, tuple[int, int]]:
    """RGBA array and grAb offsets (0, 0 when the chunk is missing)."""
    data = path.read_bytes()
    grab = (0, 0)
    i = 8
    while i + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[i:i + 8])
        if ctype == b"grAb":
            grab = struct.unpack(">ii", data[i + 8:i + 16])
            break
        if ctype == b"IDAT":
            break
        i += 12 + length
    return np.array(Image.open(path).convert("RGBA")), grab


# --------------------------------------------------------------- measure
def place(sprite: np.ndarray, offsets: tuple[int, int], bar: bool = True) -> tuple[int, int]:
    """Top-left of a weapon sprite on the 320x200 screen (psprite at rest),
    with the status bar on (bar=True) or full-screen."""
    return -offsets[0], WEAPONTOP - offsets[1] - (BAR_LIFT if bar else 0)


def screen_mask(sprite: np.ndarray, offsets: tuple[int, int], bar: bool = True) -> np.ndarray:
    """Bool 200x320: which screen pixels the sprite covers."""
    x0, y0 = place(sprite, offsets, bar)
    mask = np.zeros((SCREEN_H, SCREEN_W), bool)
    h, w = sprite.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(SCREEN_W, x0 + w), min(SCREEN_H, y0 + h)
    if dx1 > dx0 and dy1 > dy0:
        mask[dy0:dy1, dx0:dx1] = sprite[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0, 3] > 0
    return mask


def measure(sprite: np.ndarray, offsets: tuple[int, int]) -> dict:
    """Area and height on screen, status bar on (the primary numbers):
    `height` = from the topmost pixel down to the bar (what the player
    sees), `area` = covered pixels in the 320x168 view. `height_full` is
    the same weapon in full-screen (no bar, 16 px lower, 32 px more)."""
    m = screen_mask(sprite, offsets, bar=True)[:VIEW_H]
    full = screen_mask(sprite, offsets, bar=False)
    rows = np.flatnonzero(m.any(axis=1))
    frows = np.flatnonzero(full.any(axis=1))
    if rows.size == 0:
        return {"area": 0, "area_pct": 0.0, "top": None, "height": 0, "height_full": 0, "bbox": None}
    cols = np.flatnonzero(m.any(axis=0))
    top = int(rows[0])
    return {
        "area": int(m.sum()),
        "area_pct": round(100.0 * float(m.sum()) / (SCREEN_W * VIEW_H), 1),
        "top": top,
        "height": VIEW_H - top,
        "height_full": SCREEN_H - int(frows[0]) if frows.size else 0,
        "bbox": [int(cols[0]), top, int(cols[-1]) + 1, int(rows[-1]) + 1],
    }


def target_for(ours: dict, ref: dict) -> dict:
    """Linear scale that brings our visible height onto the reference's
    (scaling about the status bar line), and the +-10 % band."""
    s = ref["height"] / ours["height"]
    return {
        "scale": round(s, 3),
        "reduce_pct": round(100.0 * (1.0 - s), 1),
        "band_px": [round(ref["height"] * (1 - TOLERANCE)), round(ref["height"] * (1 + TOLERANCE))],
        "area_after": round(ours["area"] * s * s),
        "height_ratio": round(ours["height"] / ref["height"], 2),
        "area_ratio": round(ours["area"] / max(1, ref["area"]), 2),
    }


# --------------------------------------------------------------- backdrop
def map01_backdrop() -> np.ndarray:
    """A 320x200 MAP01 frame from the filed Windows smoke shot (464x281,
    GZDoom's widescreen view): the 4:3 middle of the 3D view is taken,
    Freedoom's pistol is painted out with floor from the left, and the
    status bar strip is kept."""
    shot = np.array(Image.open(MAP01_SHOT).convert("RGB"))
    w = shot.shape[1]
    bar_top = SHOT_BAR_TOP
    patched = shot.copy()
    gx0, gx1, gy0 = SHOT_PISTOL_BOX
    patched[gy0:bar_top, gx0:gx1] = shot[gy0:bar_top, gx0 - 100:gx1 - 100]
    view_w = round(bar_top * SCREEN_W / VIEW_H / PIXEL_ASPECT)   # the 320 units of the view
    vx0 = max(0, (w - view_w) // 2)
    view = Image.fromarray(patched[:bar_top, vx0:vx0 + view_w]).resize((SCREEN_W, VIEW_H), Image.Resampling.BOX)
    bar = Image.fromarray(shot[bar_top:, :]).resize((SCREEN_W, STATUS_BAR_H), Image.Resampling.BOX)
    out = Image.new("RGB", (SCREEN_W, SCREEN_H))
    out.paste(view, (0, 0))
    out.paste(bar, (0, VIEW_H))
    return np.array(out)


def composite(bg: np.ndarray, sprite: np.ndarray, xy: tuple[int, int]) -> np.ndarray:
    out = bg.copy()
    x0, y0 = xy
    h, w = sprite.shape[:2]
    for y in range(max(0, y0), min(bg.shape[0], y0 + h)):
        row = sprite[y - y0]
        xs = slice(max(0, x0), min(bg.shape[1], x0 + w))
        src = row[xs.start - x0: xs.stop - x0]
        a = src[:, 3] > 0
        seg = out[y, xs]
        seg[a] = src[a, :3]
        out[y, xs] = seg
    return out


def draw_on_screen(bg: np.ndarray, sprite: np.ndarray, offsets, with_bar: bool = True) -> np.ndarray:
    out = composite(bg, sprite, place(sprite, offsets))
    if with_bar:   # the status bar is drawn over the weapon, as in the engine
        out[VIEW_H:] = bg[VIEW_H:]
    return out


def scaled_sprite(sprite: np.ndarray, offsets, s: float) -> tuple[np.ndarray, tuple[int, int]]:
    """Nearest-neighbour scale about the point where the sprite's right edge
    meets the status bar: a preview of the target, not a re-render."""
    h, w = sprite.shape[:2]
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    img = np.array(Image.fromarray(sprite).resize((nw, nh), Image.Resampling.NEAREST))
    x0, y0 = place(sprite, offsets)
    ax = min(SCREEN_W, x0 + w)                 # anchor: right edge, clipped
    ay = VIEW_H                                # anchor: the status bar line
    nx0 = round(ax - (ax - x0) * s)
    ny0 = round(ay - (ay - y0) * s)
    return img, (-nx0, WEAPONTOP - BAR_LIFT - ny0)


# ------------------------------------------------------------------- text
def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(artlib.FONT_SMALL, size)


INK = (232, 226, 206)
DIM = (150, 150, 150)
GOLD = (230, 190, 60)
RED = (220, 70, 60)
SHEET_BG = (30, 31, 34)


def zoom(arr: np.ndarray, k: int) -> Image.Image:
    img = Image.fromarray(arr)
    return img.resize((img.width * k, img.height * k), Image.Resampling.NEAREST)


def wrap(draw: ImageDraw.ImageDraw, xy, text: str, f, fill, max_w: int, gap: int = 4) -> int:
    x, y = xy
    line = ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=f) > max_w and line:
            draw.text((x, y), line, font=f, fill=fill)
            y += f.size + gap
            line = word
        else:
            line = trial
    if line:
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


# ------------------------------------------------------------- scale sheet
def scale_study() -> dict:
    lumps, pal = read_wad()
    refs = {}
    for name in DOOM_LUMPS:
        spr, off = decode_patch(lumps[name], pal)
        refs[name] = {"sprite": spr, "offsets": off, "m": measure(spr, off)}
    rows = []
    for set_name, folder in OUR_SETS:
        for weapon, sub, lump, ref, why in PAIRS:
            path = folder / sub / f"{lump}.png"
            if not path.is_file():
                continue
            spr, off = read_png_sprite(path)
            m = measure(spr, off)
            rows.append({"set": set_name, "weapon": weapon, "lump": lump, "path": str(path.relative_to(ROOT)),
                         "offsets": list(off), "size": [spr.shape[1], spr.shape[0]], "ref": ref, "why": why,
                         "m": m, "target": target_for(m, refs[ref]["m"]), "_sprite": spr})
    return {"refs": refs, "rows": rows}


SCALE_VERDICT = (
    "Verdict: every weapon is 1.2x to 2.4x the height of its Doom counterpart and 2.8x to 4.6x its area (RPG-7 and "
    "ROKS-3 excepted on area: they are thin), with either hand set, so the size comes from the poses' offsets and "
    "the render scale, not from the hands. Rule proposed: each weapon at its reference's height +-10 %, which means "
    "about x0.6-0.7 for most (TT-33 x0.68, IZh-58 x0.58, RPG-7 x0.70, ROKS-3 x0.64), x0.52 for the hand Katyusha and "
    "x0.42 for the PPSh-41 (Freedoom's chaingun sits very low; if x0.42 reads too small, the PPSh can take the "
    "pistol's band instead, 50-61 px, x0.66). The ice axe is the outlier, 128 px: Doom's fist is no model for a "
    "raised pick, so it is held to the pistol's band too, which needs a lower rest pose rather than x0.43. The "
    "third column is a nearest-neighbour preview, for size only: the real fix is a re-render at the new scale, after "
    "the hands are chosen.")


def build_scale_sheet(study: dict, stamp: str) -> Path:
    bg = map01_backdrop()
    refs, rows = study["refs"], study["rows"]
    main = [r for r in rows if r["set"] == OUR_SETS[0][0]]
    K = 2
    pw, ph = SCREEN_W * K, SCREEN_H * K
    pad, gap = 28, 14
    head_h = 196
    cap_h = 46
    table_h = 70 + 26 * (len(rows) + 3) + 40 + 22 * len(PAIRS) + 130
    W = pad * 2 + pw * 3 + gap * 2
    H = head_h + len(main) * (ph + cap_h + gap) + table_h + 120
    sheet = Image.new("RGB", (W, H), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    f_t, f_b, f_s = font(30), font(17), font(15)
    d.text((pad, 20), "Weapon scale on screen: ours vs Doom/Freedoom (D55, \"se ven gigantes\")", font=f_t, fill=INK)
    y = wrap(d, (pad, 66), (
        "Each sprite is placed as the engine places a psprite at rest on the 320x200 virtual screen WITH the "
        "status bar on, as in every capture so far (the view is 320x168 and the weapon is centred on it, so "
        "top-left = -leftoffset, 32 - topoffset - 16; checked on the smoke shot, PISGA0 top predicted 113, seen 112). "
        "HEIGHT = from its topmost pixel down to the status bar (what the player sees); AREA = its pixels in the "
        "320x168 view; 'h full' = height in full-screen (no bar). Ours: the ready frame of each weapon in "
        "work/art/weapons_2d (the D52 2D hands). References: Freedoom 0.13 IWAD (BSD-3), yardstick only. "
        "Backdrop: MAP01, filed Windows smoke shot, Freedoom's pistol painted out. Shown at 2x."), f_b, INK, W - 2 * pad)
    y = wrap(d, (pad, y + 4), (
        "Columns: OURS as drawn (red line = our top, gold lines = target band, reference height +-10 %)  |  DOOM REFERENCE  |  "
        "OURS SCALED to the reference height (nearest-neighbour preview of the target, not a re-render)."),
        f_b, GOLD, W - 2 * pad)
    y = head_h
    for r in main:
        ref = refs[r["ref"]]
        a = draw_on_screen(bg, r["_sprite"], r["offsets"])
        b = draw_on_screen(bg, ref["sprite"], ref["offsets"])
        s = r["target"]["scale"]
        sspr, soff = scaled_sprite(r["_sprite"], r["offsets"], s)
        c = draw_on_screen(bg, sspr, soff)
        panels = [zoom(a, K), zoom(b, K), zoom(c, K)]
        pd = ImageDraw.Draw(panels[0])
        for hb in r["target"]["band_px"]:
            yy = (VIEW_H - hb) * K
            pd.line([(0, yy), (pw, yy)], fill=GOLD, width=2)
        pd.line([(0, r["m"]["top"] * K), (pw, r["m"]["top"] * K)], fill=RED, width=2)
        for i, p in enumerate(panels):
            sheet.paste(p, (pad + i * (pw + gap), y))
        t = r["target"]
        cap = (f"{r['weapon']} {r['lump']}: height {r['m']['height']} px, area {r['m']['area']} px "
               f"({r['m']['area_pct']} % of view)   |   {r['ref']}: height {ref['m']['height']} px, "
               f"area {ref['m']['area']} px   |   x{t['height_ratio']} taller, x{t['area_ratio']} area  ->  "
               f"scale {t['scale']} (reduce {t['reduce_pct']} %), area after ~{t['area_after']} px")
        d.text((pad, y + ph + 6), cap, font=f_s, fill=INK)
        d.text((pad, y + ph + 26), f"target: height {t['band_px'][0]}-{t['band_px'][1]} px "
               f"({r['ref']} {ref['m']['height']} px +-10 %), reference role: {r['why']}", font=f_s, fill=GOLD)
        y += ph + cap_h + gap
    # table, both sets
    y += 10
    d.text((pad, y), "Table: all ready frames (both drafts), heights and areas on 320x200", font=f_b, fill=INK)
    y += 30
    cols = [("set", 0), ("weapon", 210), ("lump", 360), ("height", 450), ("h full", 520), ("area px", 590),
            ("% view", 670), ("ref", 740), ("ref h", 810), ("ref area", 870), ("h ratio", 950),
            ("area ratio", 1030), ("scale", 1130), ("reduce", 1200), ("target h band", 1290)]
    for name, x in cols:
        d.text((pad + x, y), name, font=f_s, fill=GOLD)
    y += 24
    for r in rows:
        ref = refs[r["ref"]]["m"]
        t = r["target"]
        vals = [r["set"], r["weapon"], r["lump"], r["m"]["height"], r["m"]["height_full"], r["m"]["area"],
                r["m"]["area_pct"], r["ref"], ref["height"], ref["area"], f"x{t['height_ratio']}", f"x{t['area_ratio']}",
                t["scale"], f"{t['reduce_pct']} %", f"{t['band_px'][0]}-{t['band_px'][1]}"]
        for (name, x), v in zip(cols, vals):
            d.text((pad + x, y), str(v), font=f_s, fill=INK if r["set"] == OUR_SETS[0][0] else DIM)
        y += 24
    y += 10
    wrap(d, (pad, y), (
        "Reading: 'h ratio' = our height / reference height; 'scale' = linear factor that puts our height on the "
        "reference (about the status bar line); 'reduce' = 1 - scale. Area falls with the square of the scale. "
        "Bright rows: the D52 2D hands (the current drafts); grey rows: the earlier 3D-hand renders."),
        f_s, DIM, W - 2 * pad)
    y += 66
    d.text((pad, y), "Proposed target per weapon (status bar on; height from the weapon's top to the bar)", font=f_b, fill=GOLD)
    y += 28
    for r in main:
        ref, t = refs[r["ref"]]["m"], r["target"]
        d.text((pad, y), (f"{r['weapon']}: {r['m']['height']} px -> {t['band_px'][0]}-{t['band_px'][1]} px, at the height "
                          f"of {r['ref'][:4]} ({ref['height']} px) +-10 %: scale x{t['scale']} (reduce {t['reduce_pct']} %), "
                          f"area {r['m']['area']} -> ~{t['area_after']} px ({r['ref'][:4]}: {ref['area']})"),
               font=f_s, fill=INK)
        y += 22
    y = wrap(d, (pad, y + 8), SCALE_VERDICT, f_s, INK, W - 2 * pad)
    path = PREVIEW_DIR / f"{stamp}_F4_weapon-scale-vs-doom.png"
    sheet.crop((0, 0, W, y + 20)).save(path, optimize=True)
    return path


def save_scale_metrics(study: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "refs": {k: {"offsets": list(v["offsets"]), "size": [v["sprite"].shape[1], v["sprite"].shape[0]], **v["m"]}
                 for k, v in study["refs"].items()},
        "ours": [{k: v for k, v in r.items() if not k.startswith("_")} for r in study["rows"]],
    }
    path = OUT_DIR / "scale_metrics.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


# ================================================================== hands
# Adult hand, approximate means in mm (bone lengths after Buryanov & Kotiuk
# 2010, finger widths from adult-male anthropometry; values written from
# memory, NOT VERIFIED against the papers in this session). Palm = the
# third metacarpal; the visible finger adds ~5 mm of fingertip pad.
PALM_MM = 65.0
PALM_BREADTH_MM = 84.0
TIP_PAD_MM = 5.0
BONES_MM = {
    # finger: (metacarpal, proximal, middle, distal), width at the PIP joint
    "thumb": ((46, 31, 0, 22), 21),
    "index": ((68, 40, 22, 16), 19),
    "middle": ((65, 45, 26, 17), 19),
    "ring": ((58, 41, 26, 17), 18),
    "little": ((53, 33, 18, 16), 16),
}
MIN_FINGER_RATIO = 4.0      # the brief: length:width 4:1 or more (thumb exempt)


def finger_ratio(name: str) -> float:
    """Visible length (knuckle to tip) : width, the unrolled finger."""
    (_, p1, p2, p3), width = BONES_MM[name]
    return (p1 + p2 + p3 + TIP_PAD_MM) / width


def relative_to_palm() -> dict[str, list[float]]:
    return {k: [round(b / PALM_MM, 2) for b in bones if b] for k, (bones, _) in BONES_MM.items()}


# The grip pose, in the grip's own frame, mm: u runs DOWN the grip from its
# top, v runs BACK from the front strap. We look at the grip's LEFT side
# (the thumb side): that is what the player sees of a right-hand pistol
# held right of centre with the muzzle up-left.
GRIP_RAKE_DEG = 13          # grip axis behind the vertical (TT-33 ~ 100-105 deg to the bore)
MUZZLE_RAISE_DEG = 25       # the pose's muzzle above horizontal, pointing left
GRIP_DEPTH = 44
GRIP_LEN = 100


def pose_parts(fat: float = 0.0, sleeve_len: float = 330.0) -> list[dict]:
    """Each part: name, group, z (painter's order), material, nail flag and a
    chain of (u, v, r) in mm. fat: mm added to every hand radius (gloves).
    Segment lengths follow BONES_MM; the curled ones are foreshortened."""
    def ch(*pts):
        return [(u, v, r + fat) for u, v, r in pts]
    g = GRIP_DEPTH / 2
    return [
        # far side first: the index along the frame, last joint on the trigger
        dict(name="index", group="index", z=0, mat="hand",
             chain=ch((13, 40, 9.5), (11, 0, 9.0), (13, -21, 8.2), (28, -31, 7.2))),
        # the P1s of middle/ring/little run along the far side; only their
        # PIP knuckles show in front of the front strap
        dict(name="middle_p1", group="middle", z=1, mat="hand", chain=ch((28, 42, 9.5), (30, -4, 9.2))),
        dict(name="ring_p1", group="ring", z=1, mat="hand", chain=ch((46, 42, 9.0), (48, -3, 8.7))),
        dict(name="little_p1", group="little", z=1, mat="hand", chain=ch((62, 41, 8.0), (64, -1, 7.8))),
        # the grip: a neutral grey cylinder, no weapon
        dict(name="grip", group="grip", z=2, mat="grip", chain=[(4, g, g), (GRIP_LEN - 4, g, g)]),
        # near side: the palm (thenar) behind, then the fingertips with nails
        dict(name="thenar", group="palm", z=3, mat="hand", chain=ch((6, 46, 14.5), (28, 50, 16.0), (46, 56, 13.5))),
        dict(name="heel", group="palm", z=3, mat="hand", chain=ch((48, 52, 14.0), (62, 60, 12.5))),
        dict(name="wrist", group="palm", z=3, mat="hand", chain=ch((38, 62, 19.5), (50, 92, 18.5))),
        # P2 crosses the front strap edge-on (~14 of 26 mm), P3 lies on the side
        dict(name="little_tip", group="little", z=4, mat="hand", nail=True,
             chain=ch((64, -1, 7.8), (67, 9, 7.0), (69, 24, 6.4))),
        dict(name="ring_tip", group="ring", z=5, mat="hand", nail=True,
             chain=ch((48, -3, 8.7), (51, 10, 7.8), (53, 28, 7.0))),
        dict(name="middle_tip", group="middle", z=6, mat="hand", nail=True,
             chain=ch((30, -4, 9.2), (33, 10, 8.2), (35, 31, 7.4))),
        # the thumb rides high along the side, forward, ~8 deg above the bore
        dict(name="thumb", group="thumb", z=7, mat="hand", nail=True,
             chain=ch((14, 50, 12.0), (2, 35, 10.5), (-4, 9, 9.6), (-9, -15, 8.4))),
        dict(name="sleeve", group="sleeve", z=8, mat="sleeve",
             chain=[(50, 90, 23.0), (50 + 0.25 * sleeve_len, 90 + 0.97 * sleeve_len, 30.0)]),
    ]


def grip_to_screen(u, v, k: float, origin: tuple[float, float]):
    """Grip frame (mm) -> screen px: rake the grip, then raise the muzzle."""
    t = math.radians(GRIP_RAKE_DEG)
    fwd = -u * math.sin(t) - v * math.cos(t)
    down = u * math.cos(t) - v * math.sin(t)
    a = math.radians(MUZZLE_RAISE_DEG)
    x0, y0 = -fwd, down                          # muzzle to the left
    return (origin[0] + k * (x0 * math.cos(a) - y0 * math.sin(a)),
            origin[1] + k * (x0 * math.sin(a) + y0 * math.cos(a)))


LIGHT = np.array([-0.55, -0.75, 0.62])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = (LIGHT + np.array([0.0, 0.0, 1.0])) / np.linalg.norm(LIGHT + np.array([0.0, 0.0, 1.0]))
SS = 4                      # supersampling of the raster before the pixel cut


def raster(parts: list[dict], k: float, origin, size=(SCREEN_W, SCREEN_H), mapper=None) -> dict:
    """Paint the capsule chains at SS x: part index, segment, |d|/r, light,
    specular, signed side of the axis, and the nail mask."""
    W, H = size[0] * SS, size[1] * SS
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    xs, ys = (xs + 0.5) / SS, (ys + 0.5) / SS
    buf = {"pid": np.full((H, W), -1, np.int16), "seg": np.zeros((H, W), np.int16),
           "edge": np.zeros((H, W), np.float32), "shade": np.zeros((H, W), np.float32),
           "spec": np.zeros((H, W), np.float32), "side": np.zeros((H, W), np.float32),
           "nail": np.zeros((H, W), bool)}
    height = np.zeros((H, W), np.float32)      # surface height, for smooth unions inside a group
    for i in sorted(range(len(parts)), key=lambda j: parts[j]["z"]):
        p = parts[i]
        to_px = mapper or grip_to_screen
        pts = [(*to_px(u, v, k, origin), r * k) for u, v, r in p["chain"]]
        last = len(pts) - 2
        for s_i, ((ax, ay, ar), (bx, by, br)) in enumerate(zip(pts[:-1], pts[1:])):
            x_lo = max(0, int((min(ax - ar, bx - br) - 1) * SS))
            y_lo = max(0, int((min(ay - ar, by - br) - 1) * SS))
            x_hi = min(W, int((max(ax + ar, bx + br) + 1) * SS))
            y_hi = min(H, int((max(ay + ar, by + br) + 1) * SS))
            if x_hi <= x_lo or y_hi <= y_lo:
                continue
            sl = (slice(y_lo, y_hi), slice(x_lo, x_hi))
            sx, sy = xs[sl], ys[sl]
            dx, dy = bx - ax, by - ay
            L2 = max(1e-6, dx * dx + dy * dy)
            t = np.clip(((sx - ax) * dx + (sy - ay) * dy) / L2, 0, 1)
            rr = ar + t * (br - ar)
            ox, oy = sx - (ax + t * dx), sy - (ay + t * dy)
            dist = np.sqrt(ox * ox + oy * oy)
            inside = dist < rr
            nx, ny = ox / rr, oy / rr
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            # inside one group and depth, overlapping capsules merge: the
            # higher surface wins, so joints and bellies do not show as rings
            cur = buf["pid"][sl]
            same = np.zeros_like(inside)
            for j in range(len(parts)):
                if parts[j]["group"] == p["group"] and parts[j]["z"] == p["z"]:
                    same |= cur == j
            inside &= ~same | (nz * rr >= height[sl])
            if not inside.any():
                continue
            hsl = height[sl]
            hsl[inside] = (nz * rr)[inside]
            side = (ox * -dy + oy * dx) / (math.sqrt(L2) * rr)
            vals = {"pid": i, "seg": s_i, "edge": dist / rr,
                    "shade": nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2],
                    "spec": np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1), "side": side}
            for key, val in vals.items():
                tgt = buf[key][sl]
                tgt[inside] = val[inside] if isinstance(val, np.ndarray) else val
            nailm = buf["nail"][sl]
            nailm[inside] = False
            if p.get("nail") and s_i == last:
                # distal ~55 % of the last segment, middle ~60 % of its width,
                # on the face turned to us (the thumb's: its upper edge)
                off, half = (-0.30, 0.40) if p["group"] == "thumb" else (0.0, 0.50)
                off = p.get("nail_side", off)
                nailm[inside & (t > 0.45) & (t < 0.98) & (np.abs(side - off) < half)] = True
    return buf


def downsample(r: dict) -> dict:
    """SS -> 1x: each pixel takes the part covering most of its cell, and
    that part's mean values."""
    pid = r["pid"]
    H, W = pid.shape[0] // SS, pid.shape[1] // SS

    def blocks(a):
        return a.reshape(H, SS, W, SS).swapaxes(1, 2).reshape(H, W, SS * SS)
    pb = blocks(pid)
    ids = np.unique(pid)
    counts = np.stack([(pb == i).sum(-1) for i in ids], -1)
    best = ids[np.argmax(counts, -1)]
    sel = pb == best[..., None]
    n = np.maximum(1, sel.sum(-1))
    out = {"pid": best.astype(np.int16)}
    for key in ("seg", "edge", "shade", "spec", "side"):
        out[key] = (blocks(r[key]).astype(np.float32) * sel).sum(-1) / n
    out["seg"] = np.round(out["seg"]).astype(np.int16)
    out["nail"] = (blocks(r["nail"]) & sel).sum(-1) > 0.45 * n
    return out


VARIANTS = {
    "H1": dict(k=0.45, fat=0.0, ramp=("flesh_pink", 3, 14), tones=7, outline="ramp", nails=True,
               title="H1  pixel art, measured fingers",
               note="Bare hand at the in-game scale (0.45 px/mm): fingers 7-9 px wide, nails on three fingertips "
                    "and the thumb, joints notched, palm wider than tall."),
    "H2": dict(k=0.34, fat=0.0, ramp=("flesh_pink", 2, 14), tones=4, outline="black", nails=True,
               title="H2  classic Doom: fewer pixels, more contrast",
               note="Same hand at 0.34 px/mm (the size of Freedoom PISGA0's hand), four flat tones, black outline; "
                    "nails and joints in one or two pixels."),
    "H3": dict(k=0.45, fat=1.2, ramp=("rust_brown", 1, 10), tones=7, outline="ramp", nails=False,
               seams=True, leather=True,
               title="H3  tight leather glove, stitched",
               note="H1 plus 1.2 mm of leather: sheen hot spots, a stitched seam along each finger and around the "
                    "thumb base, a wrist strap with a snap."),
    "H4": dict(k=0.45, fat=3.5, ramp=("khaki_olive", 1, 10), tones=6, outline="ramp", nails=False, knit=True,
               title="H4  thick winter glove",
               note="H1 plus 3.5 mm of wool: fingers ~3.5:1 instead of 4.5:1, still five separate digits, ribbed "
                    "knit cuff, seams across the knuckles."),
}
SLEEVE_RAMP = ("military_green", 2, 13)
GRIP_RAMP = ("concrete_cold", 5, 21)
NEUTRAL_BG = (96, 96, 100)


def ramp(name: str) -> list[tuple[int, int, int]]:
    """A palette ramp, v1 or v2 (flesh_pink is a v2 ramp, D-palette v2)."""
    for r in artlib.load_palette().get("added_ramps", []):
        if r["name"] == name:
            return [tuple(c) for c in r["colours"]]
    return artlib.ramp(name)


def ramp_cols(spec) -> list[tuple[int, int, int]]:
    name, lo, hi = spec
    return ramp(name)[lo:hi + 1]


def tone_index(shade: np.ndarray, n: int) -> np.ndarray:
    """Banded light: shade (cosine) -> 0..n-1, 0 darkest."""
    v = np.clip(0.18 + 0.82 * np.clip(shade, 0, 1), 0, 1)
    return np.clip((v * n).astype(int), 0, n - 1)


def shift(a: np.ndarray, dy: int, dx: int, fill) -> np.ndarray:
    """a moved so out[y, x] = a[y + dy, x + dx] (fill outside)."""
    H, W = a.shape
    out = np.full_like(a, fill)
    out[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)] = \
        a[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
    return out


def pixel_cut(parts: list[dict], d: dict, var: dict) -> np.ndarray:
    """1x buffers -> RGBA pixel art: light bands, outline, separation lines
    between overlapping digits, joint notches, nails, seams."""
    pid = d["pid"]
    H, W = pid.shape
    rgba = np.zeros((H, W, 4), np.uint8)
    full = ramp_cols(var["ramp"])
    n = var["tones"]
    tone_cols = [full[i] for i in np.linspace(0, len(full) - 1, n).round().astype(int)]
    mats = {"hand": tone_cols,
            "grip": [ramp_cols(GRIP_RAMP)[i] for i in np.linspace(0, len(ramp_cols(GRIP_RAMP)) - 1, 5).round().astype(int)],
            "sleeve": [ramp_cols(SLEEVE_RAMP)[i] for i in np.linspace(0, 11, 5).round().astype(int)],
            "cuff": [ramp_cols(SLEEVE_RAMP)[i] for i in np.linspace(0, 10, 5).round().astype(int)]}
    black = (0, 0, 0)
    line_col = {"hand": black if var["outline"] == "black" else ramp(var["ramp"][0])[1],
                "grip": artlib.ramp("concrete_cold")[3], "sleeve": artlib.ramp("military_green")[1],
                "cuff": artlib.ramp("military_green")[0]}
    rng = np.random.default_rng(55)
    level = np.zeros((H, W), int)
    for i, p in enumerate(parts):
        m = pid == i
        if not m.any():
            continue
        cols = mats[p["mat"]]
        sh = d["shade"][m]
        if p["mat"] == "hand" and var.get("leather"):
            sh = sh + 0.6 * d["spec"][m] ** 16                 # leather: tight hot spot
        lv = tone_index(sh, len(cols))
        if p["mat"] == "hand" and var.get("knit"):             # wool: a little broken
            lv = np.clip(lv + rng.integers(-1, 2, lv.shape) * (rng.random(lv.shape) < 0.22), 0, len(cols) - 1)
        level[m] = lv
        for li, c in enumerate(cols):
            rgba[m & (level == li), :3] = c
        rgba[m, 3] = 255
    inside = pid >= 0
    zs = np.array([p["z"] for p in parts] + [-1])
    grp = np.array([p["group"] for p in parts] + ["-"])
    safe = np.where(inside, pid, len(parts))
    sep = np.zeros((H, W), bool)
    joint = np.zeros((H, W), bool)
    outer = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        q = shift(pid, dy, dx, -1)
        qsafe = np.where(q >= 0, q, len(parts))
        outer |= inside & (q < 0)
        other = inside & (q >= 0) & (grp[qsafe] != grp[safe])
        sep |= other & (zs[qsafe] > zs[safe])
        sep |= other & (zs[qsafe] == zs[safe]) & (dy + dx > 0)
        joint |= inside & (q == pid) & (shift(d["seg"], dy, dx, -1) != d["seg"]) & (d["edge"] > 0.5)
    is_hand = np.isin(pid, [i for i, p in enumerate(parts) if p["mat"] == "hand"])
    lines = outer | sep
    if var.get("nails"):          # two steps lighter, its proximal rim one tone dark
        nm = d["nail"] & is_hand & ~lines
        lit = np.clip(level + 3, 0, n - 1)
        for li in range(n):
            rgba[nm & (lit == li), :3] = tone_cols[li]
        rim = nm & ~(shift(nm, 0, 1, False) & shift(nm, 0, -1, False) & shift(nm, 1, 0, False) & shift(nm, -1, 0, False))
        rgba[rim, :3] = tone_cols[max(0, n - 3)]
    stitch_col = ramp("cream_yellow")[9]
    yy, xx = np.mgrid[0:H, 0:W]
    dotted = (xx + yy) % 2 == 0
    wrist = pid == [i for i, p in enumerate(parts) if p["name"] == "wrist"][0]
    thumb_i = [i for i, p in enumerate(parts) if p["name"] == "thumb"][0]
    if var.get("seams"):
        digits = np.isin(pid, [i for i, p in enumerate(parts) if p["group"] in
                               ("index", "middle", "ring", "little", "thumb") and p["mat"] == "hand"])
        rgba[digits & (np.abs(d["side"] - 0.55) < 0.13) & dotted & ~lines, :3] = stitch_col
        rgba[(pid == thumb_i) & joint & (d["seg"] == 0) & ~lines, :3] = stitch_col   # thumb-base seam
        strap = wrist & (d["seg"] == 0)
        rgba[strap & ~lines, :3] = artlib.ramp("rust_brown")[4]
        rgba[strap & ~lines & (level >= 3), :3] = artlib.ramp("rust_brown")[7]
        rgba[strap & (d["edge"] < 0.22), :3] = artlib.ramp("steel_blue")[13]
    if var.get("knit"):
        rib = wrist & (np.round(d["side"] * 4) % 2 == 0) & ~lines
        rgba[wrist & ~lines, :3] = artlib.ramp("khaki_olive")[4]
        rgba[rib, :3] = artlib.ramp("khaki_olive")[2]
        rgba[joint & is_hand & ~lines, :3] = artlib.ramp("khaki_olive")[1]
    for i, p in enumerate(parts):              # sleeve cuff band (segment 0) and its hem
        if p["name"] == "sleeve" and len(p["chain"]) > 2:
            band = (pid == i) & (d["seg"] == 0) & ~lines
            rgba[band, :3] = np.array(mats["sleeve"])[np.clip(level[band] - 1, 0, 4)]
            hem = np.zeros_like(band)
            for dy, dx in ((0, -1), (-1, 0), (0, 1), (1, 0)):
                hem |= (pid == i) & (d["seg"] == 1) & (shift(pid, dy, dx, -1) == i) & (shift(d["seg"], dy, dx, 1) == 0)
            rgba[hem & ~outer, :3] = line_col["sleeve"]
    for i, p in enumerate(parts):
        m = pid == i
        dark = line_col[p["mat"]]
        if p["mat"] == "hand" and not var.get("knit"):
            rgba[m & joint & ~outer, :3] = tone_cols[1]
        rgba[m & sep, :3] = dark if (var["outline"] == "black" or p["mat"] != "hand") else tone_cols[0]
        rgba[m & outer, :3] = dark
    return rgba


HAND_ORIGIN = (198.0, 108.0)      # screen px of the grip frame's origin (top of the front strap)


def render_variant(key: str) -> tuple[np.ndarray, dict]:
    var = VARIANTS[key]
    parts = pose_parts(fat=var["fat"])
    d = downsample(raster(parts, var["k"], HAND_ORIGIN))
    rgba = pixel_cut(parts, d, var)
    hand = np.isin(d["pid"], [i for i, p in enumerate(parts) if p["group"] not in ("sleeve",)])
    rows, cols = np.flatnonzero(hand.any(1)), np.flatnonzero(hand.any(0))
    m = 4
    box = [int(cols[0]) - m, int(rows[0]) - m, int(cols[-1]) + 1 + m, int(rows[-1]) + 1 + m]
    widths = {g: round((BONES_MM[g][1] + 2 * var["fat"]) * var["k"], 1) for g in ("index", "middle", "ring", "little")}
    return rgba, {"key": key, "k_px_per_mm": var["k"], "glove_mm": var["fat"], "box": box,
                  "finger_width_px": widths, "top": int(rows[0])}


def neutral(rgba: np.ndarray, box) -> np.ndarray:
    x0, y0, x1, y1 = box
    crop = rgba[max(0, y0):y1, max(0, x0):x1]
    out = np.zeros(crop.shape[:2] + (3,), np.uint8)
    out[:] = NEUTRAL_BG
    a = crop[..., 3] > 0
    out[a] = crop[..., :3][a]
    return out


def on_map(rgba: np.ndarray, bg: np.ndarray) -> np.ndarray:
    out = bg.copy()
    a = rgba[..., 3] > 0
    out[a] = rgba[..., :3][a]
    out[VIEW_H:] = bg[VIEW_H:]
    return out


def flat_hand(k: float = 1.7) -> tuple[np.ndarray, list]:
    """The proportions panel: an open right hand seen from the back, every
    segment at its BONES_MM length and width. Labels as (x, y, text)."""
    W, H = int(190 * k), int(235 * k)
    wx, wy = W * 0.55, H - 6 * k
    cols = ramp_cols(("flesh_pink", 3, 14))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    fan = {"index": (-0.40, -7), "middle": (-0.13, -1), "ring": (0.13, 5), "little": (0.38, 12)}
    chains, labels, knucks = [], [], []
    for name, (fx, ang) in fan.items():
        (mc, p1, p2, p3), wdt = BONES_MM[name]
        a = math.radians(ang)
        ux, uy = math.sin(a), -math.cos(a)
        base = (wx + fx * 0.62 * PALM_BREADTH_MM * k, wy - 12 * k)
        kn = (wx + fx * PALM_BREADTH_MM * k, base[1] - mc * k)
        pts = [kn]
        for L in (p1, p2, p3 + TIP_PAD_MM):
            pts.append((pts[-1][0] + ux * L * k, pts[-1][1] + uy * L * k))
        rs = np.linspace(wdt / 2, (wdt - 4) / 2, len(pts)) * k
        chains.append(list(zip(pts, rs)))
        knucks.append(kn)
        labels.append((pts[-1][0], pts[-1][1] - 22, f"{finger_ratio(name):.1f}:1"))
    (mc, p1, _, p3), wdt = BONES_MM["thumb"]
    a = math.radians(-52)
    ux, uy = math.sin(a), -math.cos(a)
    pts = [(wx - 0.30 * PALM_BREADTH_MM * k, wy - 14 * k)]
    for L in (mc, p1, p3 + TIP_PAD_MM):
        pts.append((pts[-1][0] + ux * L * k, pts[-1][1] + uy * L * k))
    rs = np.linspace(wdt * 0.62, (wdt - 4) / 2, len(pts)) * k
    chains.append(list(zip(pts, rs)))
    labels.append((max(20.0, pts[-1][0] + 6), pts[-1][1] - 24, f"thumb {finger_ratio('thumb'):.1f}:1"))
    palm = knucks + [(wx + 0.40 * PALM_BREADTH_MM * k, wy), (wx - 0.38 * PALM_BREADTH_MM * k, wy)]
    dr.polygon(palm, fill=cols[7] + (255,), outline=cols[0] + (255,))
    for chain in chains:
        for ((ax, ay), ar), ((bx, by), br) in zip(chain[:-1], chain[1:]):
            n = max(2, int(math.hypot(bx - ax, by - ay)))
            for j in range(n + 1):
                t = j / n
                x, y, r = ax + t * (bx - ax), ay + t * (by - ay), ar + t * (br - ar)
                dr.ellipse([x - r, y - r, x + r, y + r], fill=cols[8] + (255,))
    arr = np.array(img)
    a_ = arr[..., 3] > 0
    edge = a_ & ~(np.roll(a_, 1, 0) & np.roll(a_, -1, 0) & np.roll(a_, 1, 1) & np.roll(a_, -1, 1))
    arr[edge, :3] = cols[0]
    img = Image.fromarray(arr)
    dr = ImageDraw.Draw(img)
    for chain in chains:                       # joint lines across each digit
        for ((ax, ay), ar), ((bx, by), br) in zip(chain[:-1], chain[1:-1] + [chain[-1]]):
            pass
        for ((x, y), r), ((nx_, ny_), _) in zip(chain[1:-1], chain[2:]):
            dxn, dyn = nx_ - x, ny_ - y
            L = math.hypot(dxn, dyn) or 1
            px_, py_ = -dyn / L * r, dxn / L * r
            dr.line([(x - px_, y - py_), (x + px_, y + py_)], fill=cols[2] + (255,), width=2)
    return np.array(img), labels


def current_hand_crop() -> np.ndarray | None:
    """The rejected D52 hand on the TT-33 (SDTTA0), for comparison."""
    path = ROOT / "work" / "art" / "weapons_2d" / "tt33" / "SDTTA0.png"
    if not path.is_file():
        return None
    a = np.array(Image.open(path).convert("RGBA"))
    out = np.zeros(a.shape[:2] + (3,), np.uint8)
    out[:] = NEUTRAL_BG
    m = a[..., 3] > 0
    out[m] = a[..., :3][m]
    return out


MAP_CROP = (120, 60, 280, 168)     # the 4x crop of the screen around the hand


def build_hand_sheet(stamp: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bg = map01_backdrop()
    lumps, pal = read_wad()
    pisg, _ = decode_patch(lumps["PISGA0"], pal)
    renders = {}
    for key in VARIANTS:
        rgba, info = render_variant(key)
        Image.fromarray(rgba).save(OUT_DIR / f"{key}_screen.png")
        renders[key] = (rgba, info)
    (OUT_DIR / "hands_metrics.json").write_text(json.dumps(
        {"variants": {k: v[1] for k, v in renders.items()}, "bones_mm": BONES_MM,
         "relative_to_palm": relative_to_palm(),
         "finger_ratio": {g: round(finger_ratio(g), 2) for g in BONES_MM}}, indent=2), encoding="utf-8")
    pad, gap = 28, 18
    f_t, f_b, f_s = font(30), font(17), font(15)
    consola = Path(artlib._WIN_FONTS) / "consola.ttf"
    mono = ImageFont.truetype(str(consola), 15) if consola.is_file() else f_s
    W = 2260
    flat, labels = flat_hand()
    head_h = 118
    prop_h = flat.shape[0] + 40
    sheet = Image.new("RGB", (W, 6000), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), "Hands alone (D55): one pose, right hand on a pistol grip, no weapon - H1 to H4",
           font=f_t, fill=INK)
    wrap(d, (pad, 60), (
        "What the player sees of a right hand holding the TT-33 right of centre, muzzle up-left: the grip's LEFT "
        "side, so the thumb along the top, the tips of middle, ring and little finger wrapped round the front with "
        "their nails, the index forward on the absent trigger. The grip is a neutral grey cylinder. Each variant at "
        "1x, 2x, 4x on neutral grey, then on MAP01 (status bar on) at 1x, 2x and a 4x crop. Built from measured "
        "bones (panel below), not drawn by eye; no Freedoom or Blood pixel is used."), f_b, INK, W - 2 * pad)
    y = head_h
    fl = Image.fromarray(flat)
    sheet.paste(fl, (pad, y), fl)
    for lx, ly, txt in labels:
        d.text((pad + lx - 14, y + ly), txt, font=f_s, fill=GOLD)
    tx = pad + fl.width + 40
    d.text((tx, y), "Proportions used (adult hand; palm = 3rd metacarpal = 1.00 = 65 mm)", font=f_b, fill=GOLD)
    rows_ = ["digit     metacarpal  proximal  middle  distal  width  length:width (+5 mm pad)"]
    for g, (bones, wdt) in BONES_MM.items():
        mc, p1, p2, p3 = bones
        mid = f"{p2 / PALM_MM:.2f}" if p2 else "  -  "
        rows_.append(f"{g:<9} {mc / PALM_MM:>6.2f}    {p1 / PALM_MM:>7.2f}  {mid:>6}  {p3 / PALM_MM:>6.2f}  "
                     f"{wdt / PALM_MM:>5.2f}  {finger_ratio(g):.1f}:1")
    yy = y + 30
    for ln in rows_:
        d.text((tx, yy), ln, font=mono, fill=INK)
        yy += 21
    yy = wrap(d, (tx, yy + 8), (
        "In words: the proximal phalanx is about two thirds of the palm (index 0.62, middle 0.69, ring 0.63, "
        "little 0.51); the middle phalanx about 0.4 (index 0.34, middle 0.40, ring 0.40, little 0.28); the distal "
        "about a quarter (0.25-0.26). The thumb has no middle phalanx: metacarpal 0.71, proximal 0.48, distal 0.34. "
        "A finger is 0.25-0.29 of the palm wide, so every finger is 4.4:1 to 4.9:1 long (the brief asks 4:1 or "
        f"more); the thumb is stubbier, 2.8:1. The back of the hand is wider than long: {PALM_BREADTH_MM:.0f} mm "
        f"across the knuckles for {PALM_MM:.0f} mm of metacarpal (1.29:1). Lengths after Buryanov & Kotiuk (2010) "
        "adult means, widths after adult-male anthropometry, both written from memory: NOT VERIFIED against the "
        "sources in this session, good to about +-10 %."), f_s, INK, W - tx - pad)
    yy = wrap(d, (tx, yy + 6), (
        "In the grip the curled fingers are foreshortened: from this side the P2 crosses the front strap edge-on "
        "(about 14 of its 26 mm) and the P3 lies on the side with its nail; the full 4:1+ length is the panel's. "
        "The thumb points forward about 8 deg above the bore; the index lies along the frame and curls its last "
        "joint onto the trigger. Grip: 100 mm long, 44 mm deep, 13 deg rake (TT-33)."), f_s, DIM, W - tx - pad)
    cur = current_hand_crop()
    if cur is not None:
        d.text((tx, yy + 8), "For comparison: the rejected D52 hand on the TT-33 (SDTTA0), 1x and 2x", font=f_s, fill=RED)
        c1 = Image.fromarray(cur)
        sheet.paste(c1, (tx, yy + 30))
        sheet.paste(c1.resize((c1.width * 2, c1.height * 2), Image.Resampling.NEAREST), (tx + c1.width + 20, yy + 30))
        yy += 30 + 2 * c1.height
    y = max(y + prop_h, yy + 20)
    for key, (rgba, info) in renders.items():
        var = VARIANTS[key]
        d.text((pad, y), var["title"], font=f_b, fill=GOLD)
        d.text((pad + 470, y + 2), var["note"], font=f_s, fill=INK)
        y += 30
        nb_ = neutral(rgba, info["box"])
        x, row_h = pad, 0
        for z in (1, 2, 4):
            im = zoom(nb_, z)
            sheet.paste(im, (x, y))
            d.text((x, y + im.height + 4), f"{z}x", font=f_s, fill=DIM)
            x += im.width + gap
            row_h = max(row_h, im.height)
        if key == "H2":   # Freedoom's pistol hand as a scale reference only, never copied
            pim = np.zeros(pisg.shape[:2] + (3,), np.uint8)
            pim[:] = NEUTRAL_BG
            pim[pisg[..., 3] > 0] = pisg[..., :3][pisg[..., 3] > 0]
            im = zoom(pim, 2)
            sheet.paste(im, (x, y))
            d.text((x, y + im.height + 4), "PISGA0 2x, scale only", font=f_s, fill=DIM)
            x += im.width + gap
        scr = on_map(rgba, bg)
        sheet.paste(zoom(scr, 1), (x, y))
        d.text((x, y + SCREEN_H + 4), "MAP01 1x", font=f_s, fill=DIM)
        x += SCREEN_W + gap
        sheet.paste(zoom(scr, 2), (x, y))
        d.text((x, y + 2 * SCREEN_H + 4), "MAP01 2x", font=f_s, fill=DIM)
        x += 2 * SCREEN_W + gap
        cimg = zoom(scr[MAP_CROP[1]:MAP_CROP[3], MAP_CROP[0]:MAP_CROP[2]], 4)
        if x + cimg.width <= W:
            sheet.paste(cimg, (x, y))
            d.text((x, y + cimg.height + 4), "MAP01 4x crop", font=f_s, fill=DIM)
        row_h = max(row_h, 2 * SCREEN_H, cimg.height)
        fw = info["finger_width_px"]
        d.text((pad, y + 4 * nb_.shape[0] + 26),
               f"{info['k_px_per_mm']} px/mm, glove +{info['glove_mm']} mm: finger width "
               f"{fw['little']}-{fw['index']} px", font=f_s, fill=DIM)
        y += row_h + 56
    path = PREVIEW_DIR / f"{stamp}_F4_hand-only-H1-H4.png"
    sheet.crop((0, 0, W, y)).save(path, optimize=True)
    return path


# ============================================================ round 2 (H2)
# CEO on H2 (2026-10-14): base approved, two faults. (1) "el brazo como un
# puto palo": the forearm must taper from below the elbow to the wrist, with
# a slight curve, muscle mass and a visible wrist joint, the cuff following
# it. (2) "la mano sin dedos es pequeña": the hand body was too small. Cause,
# found on re-checking: round 1 took the palm as the metacarpal alone (65
# mm) and forgot the carpus. Hand body = wrist joint to knuckles = metacarpal
# + carpus ~ 65 + 23 = 88 mm, about the middle finger's 93 mm (NOT VERIFIED
# figures, as above; the CEO's rule "body ~ longest finger" agrees).
CARPUS_MM = 23.0
CUFF_MM = 12.0                              # sleeve cuff band, drawn as the sleeve's first segment
HAND_BODY_MM = PALM_MM + CARPUS_MM          # 88
WRIST_BREADTH_MM = 58.0                     # across the wrist joint, back view
WRIST_DEPTH_MM = 38.0                       # thickness, as seen from the thumb side
ELBOW_BREADTH_MM = 78.0                     # forearm just below the elbow, side view

ROUND2 = {
    # palm: hand-body scale vs round 1's anatomy; curve: forearm bow, mm;
    # elbow_r: half-width of the forearm below the elbow, mm
    "H2a": dict(palm=1.00, curve=7.0, elbow_r=36.0, belly=0.30,
                note="hand body = 88 mm (0.95 of the middle finger), light taper and bow"),
    "H2b": dict(palm=1.08, curve=11.0, elbow_r=39.0, belly=0.36,
                note="hand body x1.08 (= the middle finger), more taper, more muscle"),
    "H2c": dict(palm=1.16, curve=15.0, elbow_r=42.0, belly=0.42,
                note="hand body x1.16 (1.1 of the finger), strongest taper and bow"),
}


def middle_finger_mm() -> float:
    (_, p1, p2, p3), _ = BONES_MM["middle"]
    return p1 + p2 + p3 + TIP_PAD_MM


def forearm_chain(start: tuple[float, float], r_wrist: float, elbow_r: float, curve: float,
                  length: float = 330.0, steps: int = 7) -> list[tuple[float, float, float]]:
    """Grip frame (u, v, r): from the wrist back along the arm, widening fast
    to the belly below the elbow, bowed upward (toward -u) by `curve`."""
    du, dv = 0.25, 0.97                        # the arm runs back along the bore
    nu, nv = -0.97, 0.25                       # 'up' across the arm
    out = []
    for j in range(steps + 1):
        s = length * j / steps
        f = s / length
        r = r_wrist + (elbow_r - r_wrist) * min(1.0, (f / 0.55) ** 0.7)
        bow = curve * math.sin(math.pi * f)
        out.append((start[0] + du * s + nu * bow, start[1] + dv * s + nv * bow, r))
    return out


def pose_parts_r2(palm: float = 1.0, curve: float = 7.0, elbow_r: float = 36.0, belly: float = 0.3) -> list[dict]:
    """Round 1's grip pose with a bigger hand body (palm scales it about the
    knuckle line) and a shaped forearm with wrist, cuff and muscle belly."""
    ax, av = 30.0, 44.0                        # knuckle line, far side

    def body(*pts):
        return [(ax + (u - ax) * palm, av + (v - av) * palm, r * palm) for u, v, r in pts]
    base = {p["name"]: p for p in pose_parts()}
    parts = [base[n] for n in ("index", "middle_p1", "ring_p1", "little_p1", "grip")]
    # hand body: thenar, heel and the mass between, one group, no lines inside
    parts += [
        dict(name="thenar", group="palm", z=3, mat="hand", chain=body((0, 44, 17), (18, 58, 21), (38, 72, 20))),
        dict(name="heel", group="palm", z=3, mat="hand", chain=body((58, 54, 16), (62, 74, 16))),
        dict(name="mass", group="palm", z=3, mat="hand", chain=body((30, 64, 23), (46, 86, 19))),
    ]
    wu, wv, _ = body((45, 100, 0))[0]
    r_w = WRIST_DEPTH_MM / 2
    # the wrist joint: its own group, so a crease line marks where the hand meets it
    parts += [dict(name="wrist", group="wrist", z=2.5, mat="hand",
                   chain=[(wu, wv - 8, r_w + 1.5), (wu + 2, wv + 10, r_w)]),
              dict(name="styloid", group="wrist", z=2.5, mat="hand",
                   chain=[(wu - r_w * 0.75, wv + 2, 4.0), (wu - r_w * 0.7, wv + 6, 3.5)])]
    arm = forearm_chain((wu + 4, wv + 16), r_w + 2.5, elbow_r, curve)
    lip = (arm[0][0] - 0.25 * CUFF_MM, arm[0][1] - 0.97 * CUFF_MM, arm[0][2] + 3.0)   # the cuff band
    arm = [lip, (arm[0][0], arm[0][1], arm[0][2] + 3.0)] + arm[1:]
    parts += [
        dict(name="sleeve", group="sleeve", z=8, mat="sleeve", chain=arm),
        # muscle belly on the upper side (brachioradialis/extensors), same cloth
        dict(name="belly", group="sleeve", z=8, mat="sleeve",
             chain=[(arm[2][0] - 0.97 * elbow_r * belly, arm[2][1] + 0.25 * elbow_r * belly, elbow_r * 0.55),
                    (arm[5][0] - 0.97 * elbow_r * belly, arm[5][1] + 0.25 * elbow_r * belly, elbow_r * 0.75)]),
    ]
    parts += [base[n] for n in ("little_tip", "ring_tip", "middle_tip", "thumb")]
    return parts


def open_hand_parts(palm: float = 1.0) -> list[dict]:
    """The same hand open, palm down (back view), fingers up; x right, y
    down, mm, wrist joint at (0, 0). Fingers at BONES_MM, hand body at
    HAND_BODY_MM x palm."""
    hb, P = HAND_BODY_MM * palm, palm
    knuckles = {"index": (-28 * P, -hb + 4), "middle": (-9 * P, -hb), "ring": (10 * P, -hb + 3),
                "little": (27 * P, -hb + 12)}
    fan = {"index": -6, "middle": -1, "ring": 4, "little": 11}
    parts = [
        dict(name="sleeve", group="sleeve", z=0, mat="sleeve",
             chain=[(0, 26, 33), (0, 26 + CUFF_MM, 33), (5, 95, 36), (10, 160, 39)]),
        dict(name="wrist", group="wrist", z=2, mat="hand", chain=[(0, 6, WRIST_BREADTH_MM / 2), (0, 30, 28)]),
        dict(name="body_k", group="palm", z=3, mat="hand",
             chain=[(*knuckles[g], 11.5 * P) for g in ("index", "middle", "ring", "little")]),
        dict(name="body_c", group="palm", z=3, mat="hand", chain=[(-2 * P, -hb + 22 * P, 31 * P), (0, -22 * P, 28 * P)]),
        dict(name="body_h", group="palm", z=3, mat="hand", chain=[(-12 * P, -16 * P, 17 * P), (12 * P, -14 * P, 17 * P)]),
    ]
    z = 5
    for g in ("little", "ring", "middle", "index"):
        (_, p1, p2, p3), wdt = BONES_MM[g]
        a = math.radians(fan[g])
        ux, uy = math.sin(a), -math.cos(a)
        pts = [knuckles[g]]
        for L in (p1, p2, p3 + TIP_PAD_MM):
            pts.append((pts[-1][0] + ux * L, pts[-1][1] + uy * L))
        rs = [wdt / 2, wdt / 2 - 0.5, (wdt - 3) / 2, (wdt - 4) / 2]
        parts.append(dict(name=g, group=g, z=z, mat="hand", nail=True, nail_side=0.0,
                          chain=[(x, y, float(r)) for (x, y), r in zip(pts, rs)]))
        z += 1
    (mc, p1, _, p3), wdt = BONES_MM["thumb"]
    a = math.radians(-36)
    ux, uy = math.sin(a), -math.cos(a)
    pts = [(-12 * P, -14 * P)]                 # CMC joint, inside the hand body
    for L in (mc, p1, p3 + TIP_PAD_MM):
        pts.append((pts[-1][0] + ux * L, pts[-1][1] + uy * L))
    rs = [17.0 * P, 12.0, 10.5, 8.5]
    parts.append(dict(name="thumb", group="thumb", z=4, mat="hand", nail=True, nail_side=0.0,
                      chain=[(x, y, r) for (x, y), r in zip(pts, rs)]))
    return parts


def render_parts(parts: list[dict], var: dict, origin=HAND_ORIGIN, size=(SCREEN_W, SCREEN_H), mapper=None):
    d = downsample(raster(parts, var["k"], origin, size, mapper))
    return pixel_cut(parts, d, var), d


def alpha_box(rgba: np.ndarray, margin: int = 3) -> list[int]:
    a = rgba[..., 3] > 0
    rows, cols = np.flatnonzero(a.any(1)), np.flatnonzero(a.any(0))
    return [max(0, int(cols[0]) - margin), max(0, int(rows[0]) - margin),
            int(cols[-1]) + 1 + margin, int(rows[-1]) + 1 + margin]


OPEN_HAND_ZOOM = 2          # the open hand is drawn at twice the game scale so its shapes read


def render_open_hand(palm: float, var: dict) -> np.ndarray:
    var = dict(var, k=var["k"] * OPEN_HAND_ZOOM)
    k = var["k"]
    size = (int(200 * k) + 8, int(260 * k) + 8)
    origin = (size[0] * 0.58, size[1] - 70 * k)

    def flat(u, v, kk, o):
        return o[0] + kk * u, o[1] + kk * v
    rgba, _ = render_parts(open_hand_parts(palm), var, origin, size, flat)
    return rgba


def build_round2_sheet(stamp: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bg = map01_backdrop()
    var = VARIANTS["H2"]
    rows = [("H2 round 1 (rejected)", "the stick arm, the small hand body", pose_parts())]
    rows += [(key, cfg["note"], pose_parts_r2(cfg["palm"], cfg["curve"], cfg["elbow_r"], cfg["belly"]))
             for key, cfg in ROUND2.items()]
    renders = []
    for key, note, parts in rows:
        rgba, _ = render_parts(parts, var)
        name = key.split()[0] + ("_r1" if "round 1" in key else "")
        Image.fromarray(rgba).save(OUT_DIR / f"{name}_screen.png")
        renders.append((key, note, rgba))
    open_a = render_open_hand(ROUND2["H2a"]["palm"], var)
    Image.fromarray(open_a).save(OUT_DIR / "H2a_open.png")
    metrics = {k: dict(cfg, hand_body_mm=round(HAND_BODY_MM * cfg["palm"], 1),
                       body_to_middle_finger=round(HAND_BODY_MM * cfg["palm"] / middle_finger_mm(), 2))
               for k, cfg in ROUND2.items()}
    (OUT_DIR / "round2_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    pad, gap = 24, 16
    f_t, f_b, f_s = font(26), font(16), font(14)
    W = 2600
    sheet = Image.new("RGB", (W, 4000), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), "H2 round 2 (D55): forearm shaped, hand body enlarged - same grip pose, no weapon",
           font=f_t, fill=INK)
    y = wrap(d, (pad, 52), (
        "Fixes asked by the CEO on H2: the forearm tapers from below the elbow to a visible wrist joint, with a "
        "slight bow and a muscle belly, the cuff following it; the hand body is bigger against the fingers. Why it "
        f"was small: round 1 took the palm as the metacarpal alone ({PALM_MM:.0f} mm) and left out the carpus "
        f"(~{CARPUS_MM:.0f} mm), so the hand body from wrist joint to knuckles is ~{HAND_BODY_MM:.0f} mm, about "
        f"the middle finger's {middle_finger_mm():.0f} mm, and {PALM_BREADTH_MM:.0f} mm wide against a "
        f"{WRIST_BREADTH_MM:.0f} mm wrist (figures from memory, NOT VERIFIED, +-10 %). H2 style kept: 0.34 px/mm, "
        "four tones, black outline. Each row: 1x, 2x, 4x on grey, then MAP01 1x, 2x and a 4x crop."),
        f_b, INK, W - 2 * pad)
    y += 10
    for key, note, rgba in renders:
        d.text((pad, y), key, font=f_b, fill=RED if "round 1" in key else GOLD)
        d.text((pad + 260, y + 1), note, font=f_s, fill=INK)
        y += 26
        box = alpha_box(rgba)
        nb_ = neutral(rgba, box)
        x, row_h = pad, 0
        for z in (1, 2, 4):
            im = zoom(nb_, z)
            sheet.paste(im, (x, y))
            d.text((x, y + im.height + 2), f"{z}x", font=f_s, fill=DIM)
            x += im.width + gap
            row_h = max(row_h, im.height)
        scr = on_map(rgba, bg)
        sheet.paste(zoom(scr, 1), (x, y))
        d.text((x, y + SCREEN_H + 2), "MAP01 1x", font=f_s, fill=DIM)
        x += SCREEN_W + gap
        sheet.paste(zoom(scr, 2), (x, y))
        d.text((x, y + 2 * SCREEN_H + 2), "MAP01 2x", font=f_s, fill=DIM)
        x += 2 * SCREEN_W + gap
        cx0 = min(max(0, box[0] - 6), SCREEN_W - 100)
        cimg = zoom(scr[95:VIEW_H, cx0:cx0 + 100], 4)
        if x + cimg.width <= W:
            sheet.paste(cimg, (x, y))
            d.text((x, y + cimg.height + 2), "MAP01 4x crop", font=f_s, fill=DIM)
        row_h = max(row_h, 2 * SCREEN_H, cimg.height)
        y += row_h + 34
    d.text((pad, y), "H2a open, back of the hand (no foreshortening), drawn at 2x the game scale (0.68 px/mm) "
                     "in the same H2 style; shown 1x, 2x, 4x", font=f_b, fill=GOLD)
    y += 26
    on = np.zeros(open_a.shape[:2] + (3,), np.uint8)
    on[:] = NEUTRAL_BG
    a = open_a[..., 3] > 0
    on[a] = open_a[..., :3][a]
    x = pad
    for z in (1, 2, 4):
        im = zoom(on, z)
        sheet.paste(im, (x, y))
        x += im.width + gap
    tall = 4 * on.shape[0]
    mid = middle_finger_mm()
    wrap(d, (x + 10, y), (
        f"Hand body (wrist joint to knuckles) {HAND_BODY_MM:.0f} mm = metacarpal {PALM_MM:.0f} + carpus "
        f"{CARPUS_MM:.0f}; middle finger {mid:.0f} mm (P1 45, P2 26, P3 17 + pad 5): body / finger = "
        f"{HAND_BODY_MM / mid:.2f} (H2b {HAND_BODY_MM * 1.08 / mid:.2f}, H2c {HAND_BODY_MM * 1.16 / mid:.2f}). "
        f"Width across the knuckles {PALM_BREADTH_MM:.0f} mm against a {WRIST_BREADTH_MM:.0f} mm wrist (x"
        f"{PALM_BREADTH_MM / WRIST_BREADTH_MM:.2f}). Fingers 4.4:1 to 4.9:1, thumb 2.8:1. Relative to the hand "
        f"body (1.00): proximal phalanx 0.38-0.51, middle 0.20-0.30, distal + pad 0.24-0.25. Round 1's "
        f"panel was right on the fingers and wrong on the palm, which it measured as the metacarpal only."),
        f_s, INK, W - x - 10 - pad)
    y += tall + 20
    path = PREVIEW_DIR / f"{stamp}_F4_hand-H2-round2.png"
    sheet.crop((0, 0, W, y)).save(path, optimize=True)
    return path


# ------------------------------------------------------------------ main
def main(argv: list[str]) -> None:
    what = argv[1] if len(argv) > 1 else "all"
    stamp = argv[2] if len(argv) > 2 else datetime.now().strftime("%Y-%m-%d_%H%M")
    if what in ("scale", "all"):
        study = scale_study()
        print(save_scale_metrics(study))
        print(build_scale_sheet(study, stamp))
    if what in ("hands", "all"):
        print(build_hand_sheet(stamp))
    if what == "round2":
        print(build_round2_sheet(stamp))


if __name__ == "__main__":
    main(sys.argv)
