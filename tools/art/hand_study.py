"""Hand study and weapon scale study (D55), and the TT-33 in Freedoom's hands.

    python tools/art/hand_study.py scale    # weapon size on screen vs Doom/Freedoom
    python tools/art/hand_study.py hands    # one pose, four hand variants H1-H4
    python tools/art/hand_study.py all

Scale: every first-person sprite is placed on the 320x200 virtual screen the
way the engine places it (top-left = (-leftoffset, WEAPONTOP - topoffset),
WEAPONTOP = 32) and measured: opaque area and height above the status bar.
Ours come from the drafts' PNGs (grAb offsets); the references are read
from Freedoom's IWAD (BSD-3). In the scale study they are a yardstick only,
nothing copied.

Hands: a right hand gripping a pistol grip (a neutral grey cylinder, no
weapon), seen from the player: muzzle up-left, so the grip shows its LEFT
side (thumb, the fingertips of middle/ring/little with their nails, the
index forward on the absent trigger). The hand is built from measured
bones (BONES_MM), each segment a tapered capsule shaded per pixel, then
cut to pixel art: outline, part separation lines, nails, knuckles.

Outputs: work/art/hand_study/ (frames, metrics.json) and two previews in
docs/art/previews/. Nothing goes to assets/ (D55: hands first, alone).

Freedoom's pixels ARE copied by the round-3 hands (D58, D61) and by
`build_tt33_fd`: Freedoom 0.13.0's pistol hands (PISGA0-C0) are cut out of
the IWAD, recoloured to our skin and sleeve and set around our own TT-33.
Those frames were installed by hand as `assets/sprites/tt33/SDTT*` (N17):
a derivative of Freedoom's art, shipped under Freedoom's BSD-3 licence with
its notice (LICENSE-FREEDOOM-BSD-3.txt, D75) and credit (docs/art/LICENSES.md,
"Weapon frames: the TT-33 in hand").
"""

from __future__ import annotations

import json
import math
import re
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


# ============================================================ round 3 (A)
# CEO, 2026-10-14: "Vamos con las manos de Freedoom". Freedoom's first-person
# sprites are BSD-3 (copyright notice kept, credited in LICENSES and the
# in-game credits): its pistol hands are the base, recoloured to our skin
# and sleeve, the pistol replaced by our neutral grip, nothing else moved.
# Of Freedoom 0.13's weapon frames only the pistol (PISGA0-C0) and the fist
# (PUNGA0-D0) show hands; PISGA0 is the one that grips.
R3_SOURCE = "PISGA0"
R3_GUN_BOX = (22, 50, 0, 41)          # x0, x1, y0, y1 of the pistol in PISGA0 (measured)
R3_HANDS_TOP = 33                     # first row where the hands close in under the pistol
R3_SEAM = (62, 71)                    # rows of the glove's wrist seam (the dark band)
R3_FOREARM_SPLIT_X = 32               # left forearm starts lower than the right one
R3_GRIP = (29, 43, 22)                # our grip seen from behind: x0, x1 and its top row
R3_SKIN_GAIN = 1.4                    # skin is lighter than Freedoom's glove brown: lifts its values into the pinks
R3_SEAM_LUM = 38                      # only the darkest seam pixels stay a line
R3_SKIN = ("flesh_pink", 1, 15)       # H2c's skin ramp
R3_SLEEVE = ("military_green", 1, 12)


def forearm_row(x: int) -> int:
    """First row of the forearm (below the wrist seam) in PISGA0."""
    return R3_SEAM[1] + (8 if x < R3_FOREARM_SPLIT_X else 0)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def recolour(lum: np.ndarray, mask: np.ndarray, spec, gain: float = 1.0) -> np.ndarray:
    """Freedoom's values onto one of our ramps: each pixel takes the ramp
    colour of nearest luminance (x gain), so the modelling and its contrast
    survive the change of hue."""
    cols = np.array(ramp_cols(spec) if isinstance(spec[0], str) else [c for sp in spec for c in ramp_cols(sp)])
    ramp_l = luminance(cols.astype(np.float32))
    v = lum[mask][:, None] * gain
    return cols[np.argmin(np.abs(v - ramp_l[None, :]), axis=1)]


def freedoom_hands(lumps: dict, pal: np.ndarray) -> tuple[np.ndarray, tuple[int, int], dict]:
    """R3-A: PISGA0 with the pistol taken out, our grip put in, skin and
    sleeve recoloured. Returns the sprite, its offsets and the masks."""
    src, off = decode_patch(lumps[R3_SOURCE], pal)
    h, w = src.shape[:2]
    rgb = src[..., :3].astype(np.float32)
    alpha = src[..., 3] > 0
    sat = rgb.max(-1) - rgb.min(-1)
    yy, xx = np.mgrid[0:h, 0:w]
    gx0, gx1, gy0, gy1 = R3_GUN_BOX
    in_box = (xx >= gx0) & (xx < gx1) & (yy >= gy0) & (yy < gy1)
    gun = alpha & in_box & ((sat < 40) | (yy < R3_HANDS_TOP - 6))
    out = src.copy()
    out[gun] = 0
    # where the pistol hid the hands (beside our grip), extend each hand column upward
    cx0, cx1, cy0 = R3_GRIP
    fill = gun & (yy >= R3_HANDS_TOP) & ((xx < cx0) | (xx >= cx1))
    for x in range(w):
        col = np.flatnonzero(fill[:, x])
        if col.size == 0:
            continue
        below = [y for y in range(col.max() + 1, h) if alpha[y, x] and not gun[y, x]]
        if below:                      # shift the column's own texture up, no streaks
            for y in col:
                out[y, x] = src[min(h - 1, below[0] + (y - col.min())), x]
    alpha2 = out[..., 3] > 0
    sleeve = alpha2 & (yy >= np.vectorize(forearm_row)(xx))
    seam = alpha2 & ~sleeve & (yy >= R3_SEAM[0]) & (luminance(out[..., :3].astype(np.float32)) < R3_SEAM_LUM)
    skin = alpha2 & ~sleeve & ~seam
    lum = luminance(out[..., :3].astype(np.float32))
    res = np.zeros_like(out)
    res[skin, :3] = recolour(lum, skin, R3_SKIN, R3_SKIN_GAIN)
    res[sleeve, :3] = recolour(lum, sleeve, R3_SLEEVE)
    res[seam, :3] = ramp_cols(R3_SKIN)[0]
    res[alpha2, 3] = 255
    # the hand edge that the pistol used to cover: one dark pixel on top
    top = fill & alpha2 & ~np.vstack([np.zeros((1, w), bool), alpha2[:-1]])
    res[top, :3] = ramp_cols(R3_SKIN)[0]
    # our grip from behind: a grey cylinder whose top shows above the hands
    gcols = ramp_cols(GRIP_RAMP)
    grip = np.zeros((h, w), bool)
    for x in range(cx0, cx1):
        t = (x - cx0 + 0.5) / (cx1 - cx0)                 # 0 left .. 1 right
        cap = cy0 + round(2.5 * (1 - math.sin(math.pi * t)))
        for y in range(cap, h):
            if res[y, x, 3] and y >= R3_HANDS_TOP:
                break
            grip[y, x] = True
            shade = 0.85 - 0.75 * t + (0.25 if y < cap + 3 else 0.0)
            res[y, x, :3] = gcols[int(np.clip(shade, 0, 1) * (len(gcols) - 1))]
            res[y, x, 3] = 255
    edge = grip & ~(np.roll(grip, 1, 0) & np.roll(grip, -1, 0) & np.roll(grip, 1, 1) & np.roll(grip, -1, 1))
    res[edge, :3] = artlib.ramp("concrete_cold")[3]
    return res, off, {"gun": gun, "skin": skin, "sleeve": sleeve, "grip": grip}


R3_FIST = "PUNGC0"                    # Freedoom's fist: the clearest single human hand it has
R3_FIST_PAD = 10                      # columns added on the left for the grip's end
# The glove's wrist seam in PUNGC0 is a curved dark line: it is traced per
# column (darkest pixel within +-3 rows of this guide polyline, then a
# 5-column median), and the sleeve is everything below it. D61: the first,
# straight split put green inside the hand and left the right edge skin.
R3_FIST_SEAM_GUIDE = ((56, 70), (58, 67), (60, 64), (64, 61), (68, 58), (72, 56), (78, 54), (90, 53), (97, 53), (101, 55))
R3_FIST_SEAM_X = (58, 102)            # seam traced on these source columns; right of it all is forearm
R3_FIST_SEAM_RIGHT_Y = 55             # right of the traced part, the forearm starts at this row
R3_FIST_SEAM_DARK = 100               # a seam pixel darker than this stays a line
R3_FIST_SEAM_WIN = 3                  # rows searched either side of the guide
R3_FIST_SEAM_THICK = 3                # the stitched seam is up to 3 rows deep where it runs flat
R3_FIST_GRIP = (27, 40)               # rows of the grip's end where the thumb and index ring it


def fist_seam_rows(src: np.ndarray) -> dict[int, int]:
    """{source column: seam row} for PUNGC0's wrist seam; columns right of
    the traced part get R3_FIST_SEAM_RIGHT_Y."""
    h, w = src.shape[:2]
    alpha = src[..., 3] > 0
    lum = luminance(src[..., :3].astype(np.float32))
    lum[~alpha] = 1e9
    gx = [p[0] for p in R3_FIST_SEAM_GUIDE]
    gy = [p[1] for p in R3_FIST_SEAM_GUIDE]
    x0, x1 = R3_FIST_SEAM_X
    raw = {}
    for x in range(x0, x1):
        g = int(round(np.interp(x, gx, gy)))
        y0, y1 = max(0, g - R3_FIST_SEAM_WIN), min(h, g + R3_FIST_SEAM_WIN + 1)
        raw[x] = y0 + int(np.argmin(lum[y0:y1, x]))
    xs = sorted(raw)
    rows = {x: int(np.median([raw[k] for k in xs[max(0, i - 2):i + 3]])) for i, x in enumerate(xs)}
    for x in range(x1, w):
        rows[x] = R3_FIST_SEAM_RIGHT_Y
    return rows


def freedoom_fist(lumps: dict, pal: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    """R3-A2: Freedoom's fist recoloured, with the end of our grip showing in
    the ring of thumb and index (the grip runs across the fist)."""
    src, off = decode_patch(lumps[R3_FIST], pal)
    h, w = src.shape[:2]
    pad = R3_FIST_PAD
    canvas = np.zeros((h, w + pad, 4), np.uint8)
    canvas[:, pad:] = src
    alpha = canvas[..., 3] > 0
    yy, xx = np.mgrid[0:h, 0:w + pad]
    lum = luminance(canvas[..., :3].astype(np.float32))
    line = fist_seam_rows(src)
    seam_y = np.full(w + pad, 10_000)
    for x, y in line.items():
        seam_y[x + pad] = y
    seam = alpha & (yy >= seam_y[None, :]) & (yy <= seam_y[None, :] + R3_FIST_SEAM_THICK - 1) & (lum < R3_FIST_SEAM_DARK)
    sleeve = alpha & (yy > seam_y[None, :]) & ~seam
    # no green pixel may touch skin directly: such a pixel becomes seam
    skin0 = alpha & ~sleeve & ~seam
    touch = sleeve & (shift(skin0, -1, 0, False) | shift(skin0, 0, -1, False) | shift(skin0, 0, 1, False))
    seam |= touch
    sleeve &= ~touch
    skin = alpha & ~sleeve & ~seam
    res = np.zeros_like(canvas)
    res[skin, :3] = recolour(lum, skin, R3_SKIN, R3_SKIN_GAIN)
    res[sleeve, :3] = recolour(lum, sleeve, R3_SLEEVE)
    res[seam, :3] = ramp_cols(R3_SKIN)[0]
    res[alpha, 3] = 255
    gcols = ramp_cols(GRIP_RAMP)
    g0, g1 = R3_FIST_GRIP
    grip = np.zeros((h, w + pad), bool)
    for y in range(g0, g1):
        t = (y - g0 + 0.5) / (g1 - g0)
        cap = round(3 * (1 - math.sin(math.pi * t)))
        for x in range(cap, pad + 14):
            if alpha[y, x]:
                continue
            grip[y, x] = True
            shade = 0.9 - 0.7 * t + (0.15 if x < cap + 3 else 0.0)
            res[y, x, :3] = gcols[int(np.clip(shade, 0, 1) * (len(gcols) - 1))]
            res[y, x, 3] = 255
    edge = grip & ~(np.roll(grip, 1, 0) & np.roll(grip, -1, 0) & np.roll(grip, 1, 1) & np.roll(grip, -1, 1))
    res[edge, :3] = artlib.ramp("concrete_cold")[3]
    return res, (off[0] - pad, off[1])


def map01_fullscreen() -> np.ndarray:
    """MAP01 without the status bar: the shot's 3D view stretched to
    320x200, pistol painted out."""
    shot = np.array(Image.open(MAP01_SHOT).convert("RGB"))
    w = shot.shape[1]
    patched = shot.copy()
    gx0, gx1, gy0 = SHOT_PISTOL_BOX
    patched[gy0:SHOT_BAR_TOP, gx0:gx1] = shot[gy0:SHOT_BAR_TOP, gx0 - 100:gx1 - 100]
    view_w = round(SHOT_BAR_TOP * SCREEN_W / VIEW_H / PIXEL_ASPECT)
    vx0 = max(0, (w - view_w) // 2)
    view = Image.fromarray(patched[:SHOT_BAR_TOP, vx0:vx0 + view_w]).resize((SCREEN_W, SCREEN_H), Image.Resampling.BOX)
    return np.array(view)


def full_layer(sprite: np.ndarray, offsets) -> np.ndarray:
    """A weapon sprite on a 320x200 layer, full-screen (no status bar)."""
    layer = np.zeros((SCREEN_H, SCREEN_W, 4), np.uint8)
    x0, y0 = place(sprite, offsets, bar=False)
    h, w = sprite.shape[:2]
    lx0, lx1 = max(0, x0), min(SCREEN_W, x0 + w)
    for y in range(max(0, y0), min(SCREEN_H, y0 + h)):
        layer[y, lx0:lx1] = sprite[y - y0, lx0 - x0:lx1 - x0]
    return layer


def screen_layer(sprite: np.ndarray, offsets) -> np.ndarray:
    """A weapon sprite placed on a transparent 320x200 layer (status bar on)."""
    layer = np.zeros((SCREEN_H, SCREEN_W, 4), np.uint8)
    x0, y0 = place(sprite, offsets)
    h, w = sprite.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x1, y1 = min(SCREEN_W, x0 + w), min(SCREEN_H, y0 + h)
    sub = sprite[sy0:sy0 + y1 - max(0, y0), sx0:sx0 + x1 - max(0, x0)]
    layer[max(0, y0):y1, max(0, x0):x1] = sub
    return layer


R3_LICENCE_ROW = (
    "| work/art/hand_study/R3A_* (draft, not in assets) | Freedoom 0.13.0 `freedoom2.wad`, lumps PISGA0 "
    "(pistol, two-hand grip) and PUNGC0 (fist) | BSD-3-Clause, Copyright (c) 2001-2024 Contributors to the Freedoom project | modified: "
    "pistol pixels removed (PISGA0), hidden hand pixels extended upward, recoloured to palette v2 flesh_pink and "
    "military_green, a neutral grey grip added | credit: Freedoom project (LICENSES + in-game credits) |")


def build_round3_sheet(stamp: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bg = map01_backdrop()
    lumps, pal = read_wad()
    src, src_off = decode_patch(lumps[R3_SOURCE], pal)
    a_spr, a_off, _ = freedoom_hands(lumps, pal)
    f_spr, f_off = freedoom_fist(lumps, pal)
    fist_src, _ = decode_patch(lumps[R3_FIST], pal)
    Image.fromarray(a_spr).save(OUT_DIR / "R3A_PISGA0_recoloured.png")
    Image.fromarray(f_spr).save(OUT_DIR / "R3A2_PUNGC0_recoloured.png")
    var = VARIANTS["H2"]
    c = ROUND2["H2c"]
    r1, _ = render_parts(pose_parts(), var)
    r2c, _ = render_parts(pose_parts_r2(c["palm"], c["curve"], c["elbow_r"], c["belly"]), var)
    fs_bg = map01_fullscreen()
    rows = [
        ("R3-A1  Freedoom's pistol hands (PISGA0)", "two-hand grip as Freedoom draws it; pistol out, our grip in, "
         "skin and sleeve recoloured", screen_layer(a_spr, a_off), full_layer(a_spr, a_off), True),
        ("R3-A2  Freedoom's fist (PUNGC0)", "one hand; the grip runs across the fist, its end in the ring of "
         "thumb and index; recoloured", screen_layer(f_spr, f_off), full_layer(f_spr, f_off), True),
        ("H2 round 1 (for comparison)", "rejected: the stick arm", r1, None, False),
        ("H2c round 2 (for comparison)", "rejected: the long arm, the sausage", r2c, None, False),
    ]
    pad, gap = 24, 16
    f_t, f_b, f_s = font(26), font(16), font(14)
    W = 3100
    sheet = Image.new("RGB", (W, 3000), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), "Hands round 3 (D58): Freedoom's pistol hands as the base - same grip, no weapon",
           font=f_t, fill=INK)
    y = wrap(d, (pad, 52), (
        "R3-A uses Freedoom 0.13's own hand pixels (BSD-3: usable and modifiable with its copyright notice and "
        "credit). Of Freedoom's weapon frames only two show hands: the pistol (PISGA0, a two-hand grip seen from "
        "behind) and the fist (PUNGC0). A1: PISGA0 with the pistol's pixels removed, the hand pixels it hid "
        "extended upward, a neutral grey grip where the pistol's back was. A2: PUNGC0, the end of the grip showing "
        "in the ring of thumb and index. Both: the glove recoloured by value onto H2c's skin ramp (flesh_pink), "
        "the forearm below the wrist seam onto the sleeve (military_green); framing, foreshortening and every "
        "pixel's value are Freedoom's, placed with Freedoom's own offsets. Honest reading: A1 needs the pistol to "
        "read as hands (with the status bar on, its forearms and most of the hands sit under the bar, as in "
        "Doom); A2 reads as a human hand at 1x and 2x on its own."), f_b, INK, W - 2 * pad)
    y += 6
    d.text((pad, y), "Freedoom sources at 1x, unchanged: PISGA0, PUNGC0", font=f_s, fill=DIM)
    sheet.paste(Image.fromarray(neutral(src, [0, 0, src.shape[1], src.shape[0]])), (pad + 400, y))
    sheet.paste(Image.fromarray(neutral(fist_src, [0, 0, fist_src.shape[1], fist_src.shape[0]])),
                (pad + 420 + src.shape[1], y))
    y += src.shape[0] + 16
    for title, note, layer, full, main in rows:
        d.text((pad, y), title, font=f_b, fill=GOLD if main else RED)
        d.text((pad + 520, y + 1), note, font=f_s, fill=INK)
        y += 26
        box = alpha_box(layer)
        box[3] = min(box[3], SCREEN_H)
        nb_ = neutral(layer, box)
        x, row_h = pad, 0
        for z in (1, 2, 4):
            im = zoom(nb_, z)
            sheet.paste(im, (x, y))
            d.text((x, y + im.height + 2), f"{z}x", font=f_s, fill=DIM)
            x += im.width + gap
            row_h = max(row_h, im.height)
        scr = on_map(layer, bg)
        sheet.paste(zoom(scr, 1), (x, y))
        d.text((x, y + SCREEN_H + 2), "MAP01 1x", font=f_s, fill=DIM)
        x += SCREEN_W + gap
        sheet.paste(zoom(scr, 2), (x, y))
        d.text((x, y + 2 * SCREEN_H + 2), "MAP01 2x", font=f_s, fill=DIM)
        x += 2 * SCREEN_W + gap
        cx0 = min(max(0, box[0] - 8), SCREEN_W - 100)
        cimg = zoom(scr[88:VIEW_H, cx0:cx0 + 100], 4)
        sheet.paste(cimg, (x, y))
        d.text((x, y + cimg.height + 2), "MAP01 4x crop", font=f_s, fill=DIM)
        x += cimg.width + gap
        if full is not None:
            fscr = fs_bg.copy()
            fa = full[..., 3] > 0
            fscr[fa] = full[..., :3][fa]
            sheet.paste(zoom(fscr, 2), (x, y))
            d.text((x, y + 2 * SCREEN_H + 2), "MAP01 2x, full-screen (no status bar)", font=f_s, fill=DIM)
        row_h = max(row_h, 2 * SCREEN_H, cimg.height)
        y += row_h + 34
    path = PREVIEW_DIR / f"{stamp}_F4_hand-R3-freedoom.png"
    sheet.crop((0, 0, W, y)).save(path, optimize=True)
    return path


# ====================================================== TT-33 on R3-A1 (D61)
# The approved Freedoom hands (R3-A1, PISGA0-C0 recoloured) holding our own
# TT-33, rendered from behind by gen_weapon.render_tt33_rear (D61 gate: the
# side view did not sit in hands seen from behind). The gun's grip point is
# projected onto the grip of each Freedoom frame; the eye-to-gun distance
# is searched once, on frame A, so the weapon stands at PISG's height (D57:
# 55 px above the bar, +-10 %), and kept for B (kick up) and C (coming
# down). Centred like PISGA0. Written to work/art/weapons_fd/tt33/ with grAb
# offsets, for make_draft_overlay.py --weapons-dir work/art/weapons_fd.
TT_OUT_DIR = ROOT / "work" / "art" / "weapons_fd" / "tt33"
TT_FRAMES = (("SDTTA0", "PISGA0", "A"), ("SDTTB0", "PISGB0", "B"), ("SDTTC0", "PISGC0", "C"))
TT_FLASH = ("SDTFA0", "SDTTB0")          # our flash and the held frame it shows over
TT_TARGET_TOP = 113                      # PISGA0's top with the status bar on: 55 px above the bar
TT_DEPTH_RANGE = (8.0, 60.0)             # cm searched for the eye-to-slide distance (at focal 160)
TT_FOCALS = (160.0,)                    # px: tried 160-480; with TT_REAR_STRETCH the plain 90-degree lens fits best
TT_GUN_WIDTH = 26                        # px: Freedoom PISGA0's pistol, rear view (measured)
FD_SEAM_PROBE = (50, 55, 85)             # column and rows where PISG's wrist seam is looked for
TT_GRIP_BACK_ROWS = 16                   # rows above the grip point that may show the grip's back


def fd_hands_for_gun(lumps: dict, pal: np.ndarray, lump: str):
    """One PISG frame recoloured like R3-A1, its pistol removed and nothing
    put in (our gun goes behind). Returns sprite, offsets and the grip point
    (centre of the removed pistol's lowest rows) in sprite pixels."""
    src, off = decode_patch(lumps[lump], pal)
    a_src, _ = decode_patch(lumps[R3_SOURCE], pal)
    h, w = src.shape[:2]
    rgb = src[..., :3].astype(np.float32)
    alpha = src[..., 3] > 0
    sat = rgb.max(-1) - rgb.min(-1)
    red = (rgb[..., 0] > 2 * rgb[..., 1]) & (rgb[..., 0] > 120)
    skinlike = alpha & (sat >= 40) & ~red
    rows = np.flatnonzero(skinlike.sum(1) >= 6)
    hands_top = int(rows[0])
    yy, xx = np.mgrid[0:h, 0:w]
    lum0 = luminance(rgb)
    steel = alpha & ((sat < 40) | red)
    # the pistol: grey/red pixels 8-connected to its part above the hands,
    # then every non-skin pixel between its ends on each row (sights, dots)
    gun = alpha & (yy < hands_top) & steel
    while True:
        grown = gun.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                grown |= shift(gun, dy, dx, False)
        grown &= steel
        if (grown == gun).all():
            break
        gun = grown
    for y in range(h):
        xs_ = np.flatnonzero(gun[y])
        if xs_.size:
            span = np.zeros(w, bool)
            span[xs_.min():xs_.max() + 1] = True
            gun[y] |= span & alpha[y] & ((sat[y] < 40) | red[y] | (lum0[y] < 60))
    ys, xs = np.nonzero(gun)
    grip = (float(xs[ys >= ys.max() - 3].mean()), float(ys.max()))
    # the wrist seam moves with the recoil: probe it and shift R3-A1's split
    def seam_row(img):
        col = luminance(img[FD_SEAM_PROBE[1]:FD_SEAM_PROBE[2], FD_SEAM_PROBE[0], :3].astype(np.float32))
        return FD_SEAM_PROBE[1] + int(np.argmin(col))
    dy = seam_row(src) - seam_row(a_src)
    alpha2 = alpha & ~gun
    lum = luminance(rgb)
    sleeve = alpha2 & (yy >= np.vectorize(forearm_row)(xx) + dy)
    seam = alpha2 & ~sleeve & (yy >= R3_SEAM[0] + dy) & (lum < R3_SEAM_LUM)
    skin = alpha2 & ~sleeve & ~seam
    res = np.zeros_like(src)
    res[skin, :3] = recolour(lum, skin, R3_SKIN, R3_SKIN_GAIN)
    res[sleeve, :3] = recolour(lum, sleeve, R3_SLEEVE)
    res[seam, :3] = ramp_cols(R3_SKIN)[0]
    res[alpha2, 3] = 255
    return res, off, grip, gun


def write_sprite(path: Path, rgba: np.ndarray, offsets: tuple[int, int]) -> None:
    from PIL import PngImagePlugin
    info = PngImagePlugin.PngInfo()
    info.add(b"grAb", struct.pack(">ii", *offsets))
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info)


def _gw():
    import gen_weapon
    return gen_weapon


TT_STEEL = ("concrete_cold", 0, 31)      # the gun's tones: Freedoom's pistol is dark steel with bright edges
TT_STEEL_LUM = (16.0, 150.0, 6.0)        # target luminance: darkest, brightest, curve over the value rank
TT_STEEL_RIM = ("concrete_cold", 0)      # its outline


def steel_contrast(rgba: np.ndarray) -> np.ndarray:
    """Our render's even mid-grey re-toned like Freedoom's pistol. Each
    pixel takes a luminance from its value's rank (equal values share a
    rank, so a flat face stays one tone): most of the gun dark, only the
    lit edges bright. Nearest steel tone by luminance, outline on the rim."""
    out = rgba.copy()
    a = out[..., 3] > 0
    lum = luminance(out[..., :3].astype(np.float32))
    vals = lum[a]
    uniq, inv, counts = np.unique(vals, return_inverse=True, return_counts=True)
    cum = np.cumsum(counts)
    rank = (cum - counts / 2) / cum[-1]                  # mid-rank of each distinct value
    lo, hi, curve = TT_STEEL_LUM
    target = lo + (hi - lo) * rank[inv] ** curve
    cols = np.array(ramp_cols(TT_STEEL))
    col_l = luminance(cols.astype(np.float32))
    out[a, :3] = cols[np.argmin(np.abs(target[:, None] - col_l[None, :]), axis=1)]
    edge = a & ~(shift(a, 1, 0, False) & shift(a, -1, 0, False) & shift(a, 0, 1, False) & shift(a, 0, -1, False))
    out[edge, :3] = ramp(TT_STEEL_RIM[0])[TT_STEEL_RIM[1]]
    return out


def tt33_rear_frame(gw, letter: str, depth: float, hands, h_off, grip, hole, focal: float = 160.0):
    """Our rear-view gun behind one Freedoom frame's hands, on one canvas.
    Returns (rgba, offsets, muzzle_xy); everything in weapon-space px."""
    hx0, hy0 = place(hands, h_off, bar=False)
    pose = {p.frame: p for p in gw.TT_REAR_POSES}[letter]
    frame, muzzle = gw.render_tt33_rear(pose, depth, (hx0 + grip[0], hy0 + grip[1]), focal)
    g, gx0, gy0 = steel_contrast(frame.rgba), frame.left, frame.top
    x0, y0 = min(gx0, hx0), min(gy0, hy0)
    x1 = max(gx0 + g.shape[1], hx0 + hands.shape[1])
    y1 = max(gy0 + g.shape[0], hy0 + hands.shape[0])
    canvas = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    for layer, (lx, ly) in ((g, (gx0, gy0)), (hands, (hx0, hy0))):
        sub = canvas[ly - y0:ly - y0 + layer.shape[0], lx - x0:lx - x0 + layer.shape[1]]
        m = layer[..., 3] > 0
        sub[m] = layer[m]
    # where Freedoom's pistol sat between the hands and our gun does not reach
    sub = canvas[hy0 - y0:hy0 - y0 + hands.shape[0], hx0 - x0:hx0 - x0 + hands.shape[1]]
    rows = np.mgrid[0:hole.shape[0], 0:hole.shape[1]][0]
    gap_ = hole & (sub[..., 3] == 0) & (rows >= grip[1] - TT_GRIP_BACK_ROWS)
    cols_ = np.flatnonzero(gap_.any(0))
    steel_ = ramp_cols(GRIP_RAMP)
    for xg in cols_:
        t = (xg - cols_.min() + 0.5) / max(1, cols_.max() - cols_.min() + 1)
        sub[gap_[:, xg], xg, :3] = steel_[int((0.4 - 0.35 * t) * (len(steel_) - 1))]
        sub[gap_[:, xg], xg, 3] = 255
    return canvas, (-x0, WEAPONTOP - y0), muzzle


def build_tt33_fd() -> dict:
    """The three held frames and the flash; returns their sprites/offsets."""
    gw = _gw()
    lumps, pal = read_wad()
    hands = {ours: fd_hands_for_gun(lumps, pal, theirs) for ours, theirs, _ in TT_FRAMES}
    first, _, letter_a = TT_FRAMES[0]
    hs_a, off_a, grip_a, hole_a = hands[first]

    def depth_for(focal):
        lo, hi = TT_DEPTH_RANGE[0] * focal / 160.0, TT_DEPTH_RANGE[1] * focal / 160.0
        for _ in range(16):                 # nearer = bigger = higher top
            mid = (lo + hi) / 2
            rgba, off, _ = tt33_rear_frame(gw, letter_a, mid, hs_a, off_a, grip_a, hole_a, focal)
            if measure(rgba, off)["top"] < TT_TARGET_TOP:
                lo = mid
            else:
                hi = mid
        return round((lo + hi) / 2, 2)

    def gun_width(focal, depth):
        pose = {p.frame: p for p in gw.TT_REAR_POSES}[letter_a]
        hx0, hy0 = place(hs_a, off_a, bar=False)
        fr, _ = gw.render_tt33_rear(pose, depth, (hx0 + grip_a[0], hy0 + grip_a[1]), focal)
        return fr.rgba.shape[1]
    # the focal whose gun is as wide as Freedoom's pistol, at PISG's height
    best = None
    for focal in TT_FOCALS:
        dep = depth_for(focal)
        err = abs(gun_width(focal, dep) - TT_GUN_WIDTH)
        if best is None or err < best[0]:
            best = (err, focal, dep)
    _, focal, depth = best
    frames = {}
    for ours, _, letter in TT_FRAMES:
        hs_, off_, grip_, hole_ = hands[ours]
        rgba, offs, muzzle = tt33_rear_frame(gw, letter, depth, hs_, off_, grip_, hole_, focal)
        frames[ours] = {"sprite": rgba, "offsets": offs, "muzzle": muzzle}
    fl = gw.render_tt33_flash("A", frames[TT_FLASH[1]]["muzzle"])
    frames[TT_FLASH[0]] = {"sprite": fl.rgba, "offsets": fl.offsets()}
    meta = {"_state_machine": {"file": "src/zscript/weapons/tokarev.zs", "held_placeholder": "PISG",
                               "held_letters": "ABC", "flash_placeholder": "PISF", "flash_letters": "A",
                               "hand": "E", "hands": "freedoom-R3A1"},
            "_view": "rear (gen_weapon.render_tt33_rear)", "_depth_cm": depth, "_focal_px": focal}
    for name, f in frames.items():
        write_sprite(TT_OUT_DIR / f"{name}.png", f["sprite"], f["offsets"])
        meta[name] = {"size": [f["sprite"].shape[1], f["sprite"].shape[0]], "offsets": list(f["offsets"]),
                      "height_above_bar": measure(f["sprite"], f["offsets"])["height"]}
    (TT_OUT_DIR / "metrics.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return frames | {"_depth": depth, "_focal": focal}


def build_d61_sheet(stamp: str) -> Path:
    """One sheet: the fixed fist (A2) and the TT-33 on Freedoom's hands."""
    lumps, pal = read_wad()
    bg = map01_backdrop()
    fist, _ = freedoom_fist(lumps, pal)
    Image.fromarray(fist).save(OUT_DIR / "R3A2_PUNGC0_recoloured.png")
    frames = build_tt33_fd()
    depth = frames.pop("_depth")
    focal = frames.pop("_focal")
    pisg, pisg_off = decode_patch(lumps["PISGA0"], pal)
    pad, gap = 24, 16
    f_t, f_b, f_s = font(26), font(16), font(14)
    W = 2200
    sheet = Image.new("RGB", (W, 2600), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), "D61: the fist's sleeve fixed, and the TT-33 from behind in Freedoom's hands (R3-A1)",
           font=f_t, fill=INK)
    y = 56
    d.text((pad, y), "R3-A2 fixed: the sleeve now starts under the wrist seam, traced column by column; no green "
           "inside the hand, the green reaches the right edge; a seam pixel always separates skin and sleeve.",
           font=f_s, fill=INK)
    y += 26
    fn = neutral(fist, [0, 0, fist.shape[1], fist.shape[0]])
    x = pad
    for z in (1, 2, 4):
        im = zoom(fn, z)
        sheet.paste(im, (x, y))
        d.text((x, y + im.height + 2), f"{z}x", font=f_s, fill=DIM)
        x += im.width + gap
    y += 4 * fist.shape[0] + 34
    a_m = measure(frames["SDTTA0"]["sprite"], frames["SDTTA0"]["offsets"])
    p_m = measure(pisg, pisg_off)
    y = wrap(d, (pad, y), (
        f"TT-33 frames for tokarev.zs (SDTT A ready, B fire: kick up, C coming down; SDTF A flash on B): our "
        f"TT-33 rendered from behind (gen_weapon.render_tt33_rear, the slide's back {depth:.1f} cm from the eye, focal "
        f"{focal:.0f} px, drawn {_gw().TT_REAR_STRETCH}x wider for first person like Freedoom's chunky pistol, "
        f"re-toned to dark steel with bright edges), "
        f"the muzzle into the screen like Freedoom's pistol, so frame A stands "
        f"{a_m['height']} px above the status bar, PISGA0 {p_m['height']} px (D57 band "
        f"{round(p_m['height'] * 0.9)}-{round(p_m['height'] * 1.1)}); the grip set into the grip of Freedoom's "
        f"PISGA0/B0/C0 hands (recoloured as R3-A1), so the weapon is centred like PISGA0. Written with grAb "
        f"offsets to work/art/weapons_fd/tt33/. Each frame at 1x and 2x on MAP01 (status bar on), beside "
        f"Freedoom's PISGA0 at the same place."), f_s, INK, W - 2 * pad)
    y += 8
    for name, theirs, _ in TT_FRAMES:
        ref, ref_off = decode_patch(lumps[theirs], pal)
        p_scr = draw_on_screen(bg, ref, ref_off)
        if theirs == "PISGB0":
            pf, pf_off = decode_patch(lumps["PISFA0"], pal)
            p_scr = composite(p_scr, pf, place(pf, pf_off))
            p_scr[VIEW_H:] = bg[VIEW_H:]
        f = frames[name]
        scr = draw_on_screen(bg, f["sprite"], f["offsets"])
        if name == "SDTTB0":
            fl = frames["SDTFA0"]
            scr = composite(scr, fl["sprite"], place(fl["sprite"], fl["offsets"]))
            scr[VIEW_H:] = bg[VIEW_H:]
        m = measure(f["sprite"], f["offsets"])
        label = {"SDTTA0": "A ready", "SDTTB0": "B fire, kick up + SDTF A flash", "SDTTC0": "C coming down"}[name]
        d.text((pad, y), f"{name} ({label}): {m['height']} px above the bar, x {m['bbox'][0]}-{m['bbox'][2]}",
               font=f_b, fill=GOLD)
        y += 24
        x = pad
        sheet.paste(zoom(scr, 1), (x, y))
        x += SCREEN_W + gap
        sheet.paste(zoom(scr, 2), (x, y))
        x += 2 * SCREEN_W + gap
        sheet.paste(zoom(p_scr, 2), (x, y))
        d.text((x, y + 2 * SCREEN_H + 2), f"Freedoom {theirs}, same place, 2x", font=f_s, fill=DIM)
        x += 2 * SCREEN_W + gap
        sheet.paste(zoom(p_scr, 1), (x, y))
        y += 2 * SCREEN_H + 30
    path = PREVIEW_DIR / f"{stamp}_F4_tt33-on-freedoom-hands.png"
    sheet.crop((0, 0, W, y)).save(path, optimize=True)
    return path


# ================================================ ice axe on R3-A2 (N4, D63)
# The other weapons follow the TT-33 one at a time (D63). The ice axe is a
# one-hand tool: it is held in the approved fist R3-A2 (Freedoom's PUNGC0
# recoloured, freedoom_fist), the fist without its grey grip stub, and our
# own axe (gen_weapon.render_axe_fd) runs out of the ring of thumb and
# index. Frame A is lowered to PISG's height (the scale study: PUNG is no
# model for a raised pick, so the axe is held to the sidearm's band, D57),
# and its letters are the ones ice_axe.zs plays on PUNG. Written to
# work/art/weapons_fd/ice_axe/ with grAb offsets, like the TT-33.
WEAPONS_FD_DIR = ROOT / "work" / "art" / "weapons_fd"
AXE_FD_OUT_DIR = WEAPONS_FD_DIR / "ice_axe"
AXE_FD_ZS = ROOT / "src" / "zscript" / "weapons" / "ice_axe.zs"
AXE_FD_PLACEHOLDER, AXE_FD_SPRITE = "PUNG", "SDAX"
AXE_FD_RING_INSET = 3                 # px from the fist's left edge to the shaft's axis, at the ring's row


def zs_held_letters(zs: Path, sprite: str) -> str:
    """The frame letters a weapon's .zs plays on one sprite (read only)."""
    text = zs.read_text(encoding="utf-8")
    letters = set()
    for m in re.finditer(rf"^\s*{sprite}\s+([A-Z]+)\s", text, re.M):
        letters |= set(m.group(1))
    return "".join(sorted(letters))


def freedoom_fist_bare(lumps: dict, pal: np.ndarray) -> tuple[np.ndarray, tuple[int, int], tuple[float, float]]:
    """R3-A2 without the grey grip end (only PUNGC0's own pixels, recoloured
    by freedoom_fist), and the ring point in sprite px: where the shaft's
    axis leaves the fist between thumb and index."""
    fist, off = freedoom_fist(lumps, pal)
    src, _ = decode_patch(lumps[R3_FIST], pal)
    own = np.zeros(fist.shape[:2], bool)
    own[:, R3_FIST_PAD:] = src[..., 3] > 0
    bare = fist.copy()
    bare[~own] = 0
    ry = (R3_FIST_GRIP[0] + R3_FIST_GRIP[1]) / 2
    edge = int(np.flatnonzero(own[int(ry)])[0])
    return bare, off, (float(edge + AXE_FD_RING_INSET), ry)


# The CEO on the first sheet: "el piolet tiene sentido, pero el puño que no
# lo coge no": a punching fist with the shaft poked through it does not
# hold anything. Freedoom's chainsaw (SAWG) shows no hand at all; the hand
# that GRIPS something in Freedoom 0.13 is the shotgun's pump hand, SHTG
# B-D. SHTGD0's (the clearest: thumb and index closed over the top, the
# fingers curled round) is cut from its gun, toned onto the approved fist's
# skin values, given a sleeve below the wrist, and turned (RotSprite: three
# Scale2x passes, a nearest-neighbour turn, one sample per cell) so the
# shaft runs through it at the angle each frame gives the shaft.
AXE_GRIP_SOURCE = "SHTGD0"
AXE_GRIP_MIN_X = 45                   # SHTGD0 columns left of this are the gun's olive highlight, not skin
AXE_GRIP_AXIS = (78.0, 98.0)          # SHTGD0 px: the column the gun's grip ran up, and the row the shaft is held at
AXE_GRIP_SCALE = 1.35                 # the pump hand is smaller than the fist; this puts the shaft in its ring
AXE_GRIP_SLEEVE = (90, 5)             # rows of sleeve added below the wrist, one px wider every N rows
AXE_GRIP_SLEEVE_LIGHT = 0.35          # across the sleeve, where its light falls (0 left .. 1 right)
ROTSPRITE_K = 8                       # three Scale2x passes


def scale2x(a: np.ndarray) -> np.ndarray:
    """EPX / Scale2x: twice the size, diagonals kept sharp (no new colour)."""
    h, w = a.shape[:2]
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    A, B, C, D, E = p[:-2, 1:-1], p[1:-1, 2:], p[1:-1, :-2], p[2:, 1:-1], p[1:-1, 1:-1]
    eq = lambda x, y: (x == y).all(-1)
    out = np.zeros((2 * h, 2 * w) + a.shape[2:], a.dtype)
    out[0::2, 0::2] = np.where((eq(C, A) & ~eq(C, D) & ~eq(A, B))[..., None], A, E)
    out[0::2, 1::2] = np.where((eq(A, B) & ~eq(A, C) & ~eq(B, D))[..., None], B, E)
    out[1::2, 0::2] = np.where((eq(D, C) & ~eq(D, B) & ~eq(C, A))[..., None], C, E)
    out[1::2, 1::2] = np.where((eq(B, D) & ~eq(B, A) & ~eq(D, C))[..., None], D, E)
    return out


def rotsprite(rgba: np.ndarray, angle: float, scale: float, pivot) -> tuple[np.ndarray, tuple[int, int]]:
    """rgba turned `angle` degrees counter-clockwise and scaled about pivot
    (x, y px), palette colours only. Returns the cropped sprite and where
    the pivot landed in it."""
    big = rgba
    for _ in range(3):
        big = scale2x(big)
    k = ROTSPRITE_K
    h, w = big.shape[:2]
    pad = max(h, w)
    canvas = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.uint8)
    canvas[pad:pad + h, pad:pad + w] = big
    px, py = pivot[0] * k + pad + k / 2, pivot[1] * k + pad + k / 2
    rot = np.array(Image.fromarray(canvas).rotate(angle, resample=Image.Resampling.NEAREST, center=(px, py)))
    step = k / scale
    H, W = rot.shape[:2]
    nx0, ny0 = int(px // step), int(py // step)
    xi = np.clip((px - (nx0 - np.arange(int(W / step))) * step).astype(int), 0, W - 1)
    yi = np.clip((py - (ny0 - np.arange(int(H / step))) * step).astype(int), 0, H - 1)
    out = rot[yi][:, xi]
    a = out[..., 3] > 0
    r, c = np.flatnonzero(a.any(1)), np.flatnonzero(a.any(0))
    return out[r[0]:r[-1] + 1, c[0]:c[-1] + 1], (nx0 - int(c[0]), ny0 - int(r[0]))


def tone_match(lum: np.ndarray, mask: np.ndarray, ref: np.ndarray, spec) -> np.ndarray:
    """Freedoom's values onto one of our ramps by rank: each pixel takes the
    luminance at its percentile among `ref` (equal values share a rank),
    then the ramp colour nearest to it. The pump hand comes out as light
    and as contrasted as the approved fist, not just recoloured."""
    cols = np.array(ramp_cols(spec))
    col_l = luminance(cols.astype(np.float32))
    v = lum[mask]
    _, inv = np.unique(v, return_inverse=True)
    order = np.empty(len(v))
    order[np.argsort(v, kind="stable")] = np.arange(len(v))
    pct = np.bincount(inv, weights=order) / np.bincount(inv) / max(1, len(v) - 1)
    target = np.quantile(np.sort(ref), pct[inv])
    return cols[np.argmin(np.abs(target[:, None] - col_l[None, :]), axis=1)]


def shtg_grip_hand(lumps: dict, pal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """SHTGD0's hand without its gun, toned like R3-A2's skin, with a sleeve
    added below the wrist (a seam row, then military_green shaded as a
    cylinder, widening). Returns (rgba in SHTGD0's orientation, the mask of
    SHTGD0's own hand pixels)."""
    src, _ = decode_patch(lumps[AXE_GRIP_SOURCE], pal)
    rgb = src[..., :3].astype(int)
    alpha = src[..., 3] > 0
    sat = rgb.max(-1) - rgb.min(-1)
    warm = alpha & (rgb[..., 0] > rgb[..., 2] + 12) & (sat >= 20)
    h, w = alpha.shape
    hand = np.zeros_like(alpha)
    for y in range(h):                     # the hand: from its first warm pixel to the right, gun pixels out
        xs = np.flatnonzero(warm[y, AXE_GRIP_MIN_X:])
        if xs.size:
            x0 = AXE_GRIP_MIN_X + int(xs[0])
            hand[y, x0:] = alpha[y, x0:]
    fist, _, _ = freedoom_fist_bare(lumps, pal)
    skin_cols = np.array(ramp_cols(R3_SKIN), np.uint8)
    f_skin = (fist[..., 3] > 0) & (fist[..., None, :3] == skin_cols[None, None]).all(-1).any(-1)
    ref = luminance(fist[..., :3].astype(np.float32))[f_skin]
    rows, grow = AXE_GRIP_SLEEVE
    out = np.zeros((h + rows, w + rows // grow + 2, 4), np.uint8)
    top = out[:h, :w]
    top[hand, :3] = tone_match(luminance(src[..., :3].astype(np.float32)), hand, ref, R3_SKIN)
    top[hand, 3] = 255
    green = ramp_cols(R3_SLEEVE)
    last = np.flatnonzero(hand[h - 1])
    x0, x1 = int(last[0]), int(last[-1])
    for k in range(rows):
        g = k // grow
        lo, hi = x0 - g // 2, x1 + 1 + g - g // 2
        for x in range(max(0, lo), min(out.shape[1], hi)):
            t = (x - lo + 0.5) / max(1, hi - lo)
            if k <= 1:
                col = ramp_cols(R3_SKIN)[0]           # the seam between hand and sleeve
            elif x in (lo, hi - 1):
                col = green[0]
            else:
                shade = 0.25 + 0.75 * max(0.0, math.cos((t - AXE_GRIP_SLEEVE_LIGHT) * math.pi * 1.1))
                col = green[int(round(shade * (len(green) - 2)))]
            out[h + k, x, :3] = col
            out[h + k, x, 3] = 255
    return out, hand


def axe_grip_xy(pose, ring) -> tuple[float, float]:
    """Where the shaft is held, weapon px: round 1's fist ring, kept so the
    axe stands exactly where round 1 put it, whichever hand holds it."""
    return pose.fist[0] + ring[0], pose.fist[1] + ring[1]


def axe_fd_frame(gw, pose, ring, hand: np.ndarray, hand_xy, head_y: float):
    """One frame: our axe, then a hand sprite on top at hand_xy (weapon px).
    Returns (rgba, offsets) in the engine's convention."""
    f = gw.render_axe_fd(pose, axe_grip_xy(pose, ring), head_y)
    hx, hy = hand_xy
    x0, y0 = min(f.left, hx), min(f.top, hy)
    x1 = max(f.left + f.rgba.shape[1], hx + hand.shape[1])
    y1 = max(f.top + f.rgba.shape[0], hy + hand.shape[0])
    canvas = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    for layer, (lx, ly) in ((f.rgba, (f.left, f.top)), (hand, (hx, hy))):
        sub = canvas[ly - y0:ly - y0 + layer.shape[0], lx - x0:lx - x0 + layer.shape[1]]
        m = layer[..., 3] > 0
        sub[m] = layer[m]
    return canvas, (-x0, WEAPONTOP - y0)


def axe_hand_placer(lumps: dict, pal: np.ndarray, hand: str):
    """(placer, ring): placer(pose) -> (hand sprite, its top-left) for one
    hand: "fist" (R3-A2, round 1) or "grip" (SHTGD0, turned per frame)."""
    fist, _, ring = freedoom_fist_bare(lumps, pal)
    if hand == "fist":
        return (lambda pose: (fist, pose.fist)), ring
    base, _ = shtg_grip_hand(lumps, pal)

    def place_grip(pose):
        rot, piv = rotsprite(base, 90.0 - pose.angle, AXE_GRIP_SCALE, AXE_GRIP_AXIS)
        gx, gy = axe_grip_xy(pose, ring)
        return rot, (int(round(gx - piv[0])), int(round(gy - piv[1])))
    return place_grip, ring


def build_axe_fd(hand: str = "grip", out_dir: Path | None = AXE_FD_OUT_DIR) -> dict:
    """The held frames the .zs plays; written with grAb to out_dir (None:
    not written). hand: "grip" (SHTGD0, the candidate) or "fist" (R3-A2)."""
    gw = _gw()
    lumps, pal = read_wad()
    placer, ring = axe_hand_placer(lumps, pal, hand)
    letters = zs_held_letters(AXE_FD_ZS, AXE_FD_PLACEHOLDER)
    poses = {p.frame: p for p in gw.AXE_FD_POSES}
    missing = set(letters) - set(poses)
    if missing:
        raise ValueError(f"ice_axe.zs plays PUNG {''.join(sorted(missing))}, which has no pose")
    frames = {}
    for letter in letters:
        pose = poses[letter]
        sprite, xy = placer(pose)
        head_y = pose.head_y
        if head_y is None:               # frame A: the head's height that puts the top on PISG's
            lo, hi = 0.0, float(SCREEN_H)
            for _ in range(20):
                mid = (lo + hi) / 2
                rgba, off = axe_fd_frame(gw, pose, ring, sprite, xy, mid)
                if measure(rgba, off)["top"] < TT_TARGET_TOP:
                    lo = mid
                else:
                    hi = mid
            head_y = round((lo + hi) / 2, 2)
        rgba, off = axe_fd_frame(gw, pose, ring, sprite, xy, head_y)
        frames[f"{AXE_FD_SPRITE}{letter}0"] = {"sprite": rgba, "offsets": off, "pose": pose, "head_y": head_y,
                                               "hand": sprite, "hand_xy": xy}
    if out_dir is None:
        return frames
    hands = {"grip": f"freedoom-{AXE_GRIP_SOURCE}-grip", "fist": "freedoom-R3A2"}[hand]
    meta = {"_state_machine": {"file": "src/zscript/weapons/ice_axe.zs", "held_placeholder": AXE_FD_PLACEHOLDER,
                               "held_letters": letters, "hand": "E", "hands": hands},
            "_view": f"gen_weapon.render_axe_fd, the hand on top ({hands})", "_target_top": TT_TARGET_TOP}
    for name, f in frames.items():
        write_sprite(out_dir / f"{name}.png", f["sprite"], f["offsets"])
        m = measure(f["sprite"], f["offsets"])
        meta[name] = {"size": [f["sprite"].shape[1], f["sprite"].shape[0]], "offsets": list(f["offsets"]),
                      "height_above_bar": m["height"], "bbox_bar_on": m["bbox"], "pose": f["pose"].name,
                      "head_y": f["head_y"], "hand_turn_deg": round(90.0 - f["pose"].angle, 1)}
    (out_dir / "metrics.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return frames


def build_axe_fd_sheet(stamp: str) -> Path:
    """The ice axe's sheet, round 2: the hand that grips (SHTGD0) against
    round 1's fist, frame by frame (D63: one weapon, one sheet)."""
    lumps, pal = read_wad()
    bg = map01_backdrop()
    frames = build_axe_fd("grip")
    before = build_axe_fd("fist", out_dir=None)
    pisg, pisg_off = decode_patch(lumps["PISGA0"], pal)
    p_m = measure(pisg, pisg_off)
    shtg, _ = decode_patch(lumps[AXE_GRIP_SOURCE], pal)
    base, _ = shtg_grip_hand(lumps, pal)
    pad, gap = 24, 16
    f_t, f_b, f_s = font(26), font(16), font(14)
    W = 2400
    sheet = Image.new("RGB", (W, 4000), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), "N4 / D63, weapon 1 of 6, round 2: the ice axe in a hand that grips it", font=f_t, fill=INK)
    a = frames[f"{AXE_FD_SPRITE}A0"]
    a_m = measure(a["sprite"], a["offsets"])
    y = wrap(d, (pad, 56), (
        "CEO on round 1: the axe makes sense, the fist does not hold it. Freedoom's chainsaw (SAWG A-D) has no "
        f"hand in it, only the saw, so the hand here is Freedoom's shotgun pump hand {AXE_GRIP_SOURCE} (Freedoom "
        "0.13, BSD-3), the one Freedoom hand that closes round something: cut from its gun, toned onto the "
        "approved fist's skin values (rank matching, so it is as light and as contrasted as R3-A2), a "
        f"military_green sleeve added below its wrist, scaled x{AXE_GRIP_SCALE} and turned per frame (RotSprite) "
        "so the shaft runs up through the ring of thumb and index at the angle the shaft has in that frame: "
        "thumb and index close over the shaft, the fingers wrap round its far side. Kept from round 1: the axe "
        "(head, pick, adze, ash shaft), its place in every frame, the frame letters (SDAX "
        f"{''.join(sorted(n[4] for n in frames))} for PUNG in ice_axe.zs) and the heights: A stands "
        f"{a_m['height']} px above the bar, PISGA0 {p_m['height']} px (D57 band {round(p_m['height'] * 0.9)}-"
        f"{round(p_m['height'] * 1.1)}). Written with grAb offsets to work/art/weapons_fd/ice_axe/ (round 1's "
        "fist frames are replaced there; hand_study.build_axe_fd('fist') rebuilds them)."), f_s, INK, W - 2 * pad)
    y += 8
    d.text((pad, y), f"The Freedoom source, {AXE_GRIP_SOURCE}, unchanged (3x), and the hand cut from it, toned and "
           "sleeved, before any turn (3x)", font=f_b, fill=GOLD)
    y += 24
    s_img = zoom(neutral(shtg, [0, 0, shtg.shape[1], shtg.shape[0]]), 3)
    sheet.paste(s_img, (pad, y))
    b_img = zoom(neutral(base, [0, 0, base.shape[1], base.shape[0]]), 3)
    sheet.paste(b_img, (pad + s_img.width + gap, y))
    y += max(s_img.height, b_img.height) + 26
    d.text((pad, y), "The blow as the .zs plays it, 1x: A (rest), B, C, D, C, B", font=f_b, fill=GOLD)
    y += 24
    x = pad
    for letter in "ABCDCB":
        f = frames.get(f"{AXE_FD_SPRITE}{letter}0")
        if f is None:
            continue
        sheet.paste(zoom(draw_on_screen(bg, f["sprite"], f["offsets"]), 1), (x, y))
        d.text((x, y + SCREEN_H + 2), letter, font=f_s, fill=DIM)
        x += SCREEN_W + 8
    y += SCREEN_H + 30
    for name, f in sorted(frames.items()):
        scr = draw_on_screen(bg, f["sprite"], f["offsets"])
        old_scr = draw_on_screen(bg, before[name]["sprite"], before[name]["offsets"])
        m = measure(f["sprite"], f["offsets"])
        turn = 90.0 - f["pose"].angle
        d.text((pad, y), f"{name} ({f['pose'].name}): {m['height']} px above the bar, x {m['bbox'][0]}-"
               f"{m['bbox'][2]}; the hand turned {turn:.0f} deg", font=f_b, fill=GOLD)
        y += 24
        x = pad
        sheet.paste(zoom(scr, 1), (x, y))
        d.text((x, y + SCREEN_H + 2), "now, 1x", font=f_s, fill=DIM)
        x += SCREEN_W + gap
        sheet.paste(zoom(scr, 2), (x, y))
        d.text((x, y + 2 * SCREEN_H + 2), "now, 2x", font=f_s, fill=DIM)
        x += 2 * SCREEN_W + gap
        hx, hy = f["hand_xy"]
        cx0 = int(np.clip(hx - 12, 0, SCREEN_W - 110))
        cy0 = int(np.clip(hy - 12, 0, VIEW_H - 90))
        crop = zoom(scr[cy0:cy0 + 90, cx0:cx0 + 110], 4)
        sheet.paste(crop, (x, y))
        d.text((x, y + crop.height + 2), "now, 4x on the hand", font=f_s, fill=DIM)
        x += crop.width + gap
        sheet.paste(zoom(old_scr, 1), (x, y))
        d.text((x, y + SCREEN_H + 2), "before (round 1, fist R3-A2), 1x", font=f_s, fill=DIM)
        hand_img = zoom(neutral(f["hand"], [0, 0, f["hand"].shape[1], f["hand"].shape[0]]), 1)
        sheet.paste(hand_img, (x, y + SCREEN_H + 24))
        d.text((x + hand_img.width + 8, y + SCREEN_H + 24), f"{AXE_GRIP_SOURCE} hand,", font=f_s, fill=DIM)
        d.text((x + hand_img.width + 8, y + SCREEN_H + 42), f"turned {turn:.0f} deg, 1x", font=f_s, fill=DIM)
        y += max(2 * SCREEN_H + 20, crop.height + 20, SCREEN_H + 24 + hand_img.height) + 24
    y = wrap(d, (pad, y), (
        f"Licence: the hand's pixels are Freedoom's ({AXE_GRIP_SOURCE}, Freedoom 0.13.0, BSD-3-Clause, Copyright "
        "(c) 2001-2024 Contributors to the Freedoom project), cut from the gun, toned to palette v2 flesh_pink, "
        "rescaled and turned; the sleeve below the wrist and the axe are ours. Credited with R3-A1/R3-A2. No pixel "
        "of a commercial game."), f_s, DIM, W - 2 * pad)
    path = PREVIEW_DIR / f"{stamp}_F4_ice-axe-gripping-hand.png"
    sheet.crop((0, 0, W, y + 10)).save(path, optimize=True)
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
    if what == "round3":
        print(build_round3_sheet(stamp))
    if what == "d61":
        print(build_d61_sheet(stamp))
    if what == "axe_fd":
        print(build_axe_fd_sheet(stamp))


if __name__ == "__main__":
    main(sys.argv)
