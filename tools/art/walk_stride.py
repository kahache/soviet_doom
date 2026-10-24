"""Walk strides for the Legion gunner (SDLG) and the Liberty Colossus (SDLC), D127.

    python tools/art/walk_stride.py derive        # hand strides -> work/art/reference/enemies/gemini/gem_*_strideA/C.png
    python tools/art/walk_stride.py build         # gemini_enemy's build with A/C from them -> work/art/walk_stride/<enemy>/
    python tools/art/walk_stride.py preview       # the CEO's page docs/art/previews/2026-10-24_P4_walks.html
                                                  # + work/art/walk_stride/install.sh and gemini_enemy.py.patch
    python tools/art/walk_stride.py fooocus-job --denoise 0.45   # optional: Fooocus legs repaint job (work/art/walk_fooocus/)
    python tools/art/walk_stride.py fooocus-merge --denoise 0.45 # its crops back -> gem_*_stride?_fx.png; build-fx builds them

Why. Gemini's walk sheets of the two (gem_gunner_walkL/R, gem_colossus_walkL/R)
are the standing pose: walkL and walkR differ in 0.3-0.5 % of their pixels,
so A/C hardly moved (the colossus got a derived +-3 degree rock). Gemini's
quota is spent and it repeats the same image. D127 lets local Fooocus fill in
missing details starting from the Gemini sheets; SDXL cannot pose a leg on
its own (no inpaint model on disk, engine 'None' only), so the stride is
derived by hand from Gemini's own pixels. Fooocus was tried over it (legs
inpaint at denoise 0.45, 2026-10-24): at game size it changes nothing visible
and paints ground shadows under the boots, so CHOICE ships the derivation.

The derivation, per view of the sheet (five figures, left to right: front,
3/4 front, profile, 3/4 back, back; Gemini's 3/4 and profile face RIGHT):
  * a leg is a polygon of sheet pixels (measured on x2 zooms with a 20 px
    grid); its pixels of the keyed figure are lifted out of the body;
  * each piece gets rigid moves: `rot` (degrees, counter-clockwise on screen,
    about a hip pivot), `shift` (dx, dy), `shear` (rows under y0 move k px
    per row: the robe's swing); NEAREST resampling, no new colour;
  * the lifted pieces' old place (and its halo) becomes background; `under`
    bands are copied in place under everything (the seat of the trousers, so
    a rotated thigh leaves no wedge); then the pieces with z < 0, the body,
    the pieces z > 0;
  * the five figures are written SPREAD_GAP px apart on a wider canvas (a
    swung boot would touch the next figure and the cutter would merge them).
A: the LEFT leg forward, the right trailing; C: the RIGHT leg forward. In a
front or back view that reads as one boot higher than the other (the knee
bent toward or away from the camera); in the profile the legs scissor about
the hip (A open, C the near leg passing in front).

`build` runs gemini_enemy.build on the spec with A/C swapped in, then moves
each A/C rotation sideways so its upper body lies over B's (a raised leg
moves the legs' axis the lumps are anchored on; the torso must not jump) and
re-pads one canvas per letter (MOD-SPEC 6.3). Every other lump comes out
byte-identical to the installed set. Sheets are gitignored (D77); nothing
here writes to assets/ (gemini_enemy.guard_out): install.sh does, on the
CEO's OK.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gemini_enemy as ge  # noqa: E402

ROOT = ge.ROOT
REF = ge.REF_DIR
FOOOCUS_DIR = ROOT / "work" / "art" / "walk_fooocus"
FOOOCUS_HOME = Path(r"Z:\Fooocus\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\Fooocus")
FOOOCUS_MODEL = "juggernautXL_v8Rundiffusion.safetensors"   # the D108 armband repaint's checkpoint
FOOOCUS_DENOISE = 0.45  # low: the stride is the derivation's, Fooocus repaints seams and folds (tried 2026-10-24)
FOOOCUS_SEEDS = (7,)
SEAM_PAD = 10           # px round the moved pieces that Fooocus may repaint
FOOOCUS_UP = 4


@dataclass(frozen=True)
class Piece:
    poly: tuple                     # ((x, y), ...) sheet px: the piece is the figure inside it
    ops: tuple = ()                 # ("rot", deg, (px, py)) | ("shift", dx, dy) | ("shear", k, y0)
    z: int = 1                      # < 0 under the body, > 0 over it; drawn in list order within a side


@dataclass(frozen=True)
class View:
    pieces: tuple = ()
    under: tuple = ()               # polygons copied in place under everything (hip seat)


@dataclass(frozen=True)
class Stride:
    base: str                       # the Gemini sheet the strides are cut from
    frames: dict = field(default_factory=dict)   # "A"/"C" -> (View x5)


def _box(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


# ------------------------------------------------------------------ gunner
# gem_gunner_turn.png: B and D are this sheet, so A and C cut from it keep the
# same man (walkL is a redraw a pixel off). Crotch rows: front 335, 3/4 front
# 380, profile (the legs overlap: split along the back leg's front edge),
# 3/4 back 400, back 345. Knees (the pads' bottom): ~440-450.
G_LIFT = 40             # px a raised boot goes up (front/back): ~4 game px at the gunner's scale
G_LIFT34 = 32
G_KNEE = {0: 440, 1: 445, 3: 450, 4: 455}
G_SPLIT = {0: 135, 1: 354, 3: 704, 4: 910}
G_TOP = {0: 336, 1: 336, 3: 336, 4: 345}
G_SPAN = {0: (0, 262), 1: (240, 468), 3: (615, 812), 4: (790, 1024)}   # the figure's columns (not the next one's gun)


def _lift_leg(view: int, side: str, d: int, dx: int = 0) -> tuple:
    """The shin and boot of one leg (`side` of the split, image left/right) moved up `d`
    over its own thigh: a knee bent toward or away from the camera."""
    x0, x1 = G_SPAN[view]
    s = G_SPLIT[view]
    k = G_KNEE[view]
    xa, xb = (x0, s) if side == "l" else (s, x1)
    return (Piece(_box(xa, k, xb, 571), (("shift", dx, -d),), z=1),)


GUNNER_PROFILE_SPLIT = ((548, 339), (543, 380), (536, 420), (536, 455), (537, 480), (538, 571))   # left of the front boot
GUNNER_PROFILE_BACK = ((440, 339),) + GUNNER_PROFILE_SPLIT + ((440, 571),)
# from row 339: the M1919's belt box hangs to 337 at x 589-600
GUNNER_PROFILE_FRONT = ((640, 339),) + GUNNER_PROFILE_SPLIT + ((640, 571),)
G_HIP_BACK, G_HIP_FRONT = (528, 318), (560, 318)
GUNNER_PROFILE_SEAT = (_box(495, 300, 600, 405),)   # the thighs in place: no wedge where they part

GUNNER_STRIDE = Stride("gem_gunner_turn.png", {
    # A: left leg forward. front: his right leg (image left) trails, boot up; 3/4 front the same;
    # profile (facing right, his right side near): the far (left) leg forward, the near trailing;
    # 3/4 back (his left side near, image left): the left leg forward = farther = higher;
    # back: his left leg (image left) forward, higher.
    "A": (
        View(_lift_leg(0, "l", G_LIFT, 4)),
        View(_lift_leg(1, "l", G_LIFT34, 3)),
        View((Piece(GUNNER_PROFILE_FRONT, (("rot", 12, G_HIP_FRONT),), z=-1),
              Piece(GUNNER_PROFILE_BACK, (("rot", -8, G_HIP_BACK),), z=1)), GUNNER_PROFILE_SEAT),
        View(_lift_leg(3, "l", G_LIFT34, 4)),
        View(_lift_leg(4, "l", G_LIFT, 3)),
    ),
    "C": (
        View(_lift_leg(0, "r", G_LIFT, -4)),
        View(_lift_leg(1, "r", G_LIFT34, -3)),
        View((Piece(GUNNER_PROFILE_FRONT, (("rot", -14, G_HIP_FRONT),), z=-1),
              Piece(GUNNER_PROFILE_BACK, (("rot", 30, G_HIP_BACK),), z=1)), GUNNER_PROFILE_SEAT),
        View(_lift_leg(3, "r", G_LIFT34, -4)),
        View(_lift_leg(4, "r", G_LIFT, -3)),
    ),
})

# ---------------------------------------------------------------- colossus
# gem_colossus_walkL.png (as A today; B/D are the smaller turn sheet). The robe
# hides the legs: what shows is a boot under the hem (and in the front and 3/4
# front views the metal shin through the robe's slit). A step reads as one boot
# drawn up under the hem (z < 0: the robe covers it) or, for the slit's metal
# leg, the shin and boot raised over the robe (the knee comes to the camera),
# while the robe under the knees swings toward the stepping side (`shear`).
C_LIFT = 20             # px a boot goes up under the hem: ~5 game px at the colossus' scale
C_LIFT_SHIN = 26        # the slit's metal shin: the knee bent toward the camera
C_SWAY = 0.06           # px per row the robe under C_HEM0 slides sideways: ~7 px at the hem
C_HEM0 = 400            # the row the robe's swing starts from (the knees)
C_ROBE = {0: _box(0, C_HEM0, 290, 571), 1: _box(240, C_HEM0, 485, 571), 2: _box(450, C_HEM0, 632, 571),
          3: _box(625, C_HEM0, 815, 571), 4: _box(775, C_HEM0, 1015, 571)}
# boots from under the hem's last row down (a box reaching into the hem would cut a notch in it)
C_BOOT_L = {0: _box(70, 512, 134, 571), 1: _box(250, 517, 334, 571), 2: _box(455, 518, 535, 571),
            3: _box(635, 524, 712, 571), 4: _box(845, 524, 899, 571)}
C_BOOT_R = {2: _box(545, 527, 630, 571), 3: _box(738, 515, 808, 571), 4: _box(900, 512, 955, 571)}
# the slit's metal leg (image right): the shin between the robe's flaps, the whole boot under them
C_SHIN = {0: ((138, 440), (180, 440), (180, 500), (200, 500), (200, 571), (126, 571), (126, 500), (138, 500)),
          1: _box(382, 440, 458, 571)}


def _robe(view: int, k: float) -> Piece:
    return Piece(C_ROBE[view], (("shear", k, C_HEM0),), z=1)


def _colossus_views(lift_left: bool) -> tuple:
    """Front, 3/4 front, 3/4 back, back: the image-left boot up (A) or the image-right leg up (C)."""
    k = C_SWAY if lift_left else -C_SWAY
    out = []
    for v in (0, 1, 3, 4):
        if lift_left:
            planted = (Piece(C_BOOT_R[v], (), z=-1),) if v in C_BOOT_R else ()   # not slid by the robe
            pieces = (Piece(C_BOOT_L[v], (("shift", 0, -C_LIFT),), z=-1),) + planted + (_robe(v, k),)
        elif v in C_SHIN:
            pieces = (Piece(C_BOOT_L[v], (), z=-1), _robe(v, k),
                      Piece(C_SHIN[v], (("shift", 0, -C_LIFT_SHIN),), z=2))
        else:
            pieces = (Piece(C_BOOT_R[v], (("shift", 0, -C_LIFT),), z=-1), Piece(C_BOOT_L[v], (), z=-1),
                      _robe(v, k))
        if v in C_SHIN and lift_left:   # the slit's shin is claimed first (else the robe takes it): it stays
            pieces = (Piece(C_SHIN[v], (), z=2),) + pieces
        out.append(View(pieces))
    return out


_CA, _CC = _colossus_views(True), _colossus_views(False)
COLOSSUS_STRIDE = Stride("gem_colossus_walkL.png", {
    # profile (facing right): A the front boot forward past the hem, the back boot back with the
    # heel up, the robe's hem forward; C the passing step: the back (near) boot swung forward under
    # the robe, the front one drawn back, the hem back
    "A": (_CA[0], _CA[1],
          View((Piece(C_BOOT_R[2], (("shift", 14, 0),), z=-1),
                Piece(C_BOOT_L[2], (("shift", -12, -10),), z=-1), _robe(2, 0.05))),
          _CA[2], _CA[3]),
    "C": (_CC[0], _CC[1],
          View((Piece(C_BOOT_L[2], (("shift", 34, -12),), z=-1),
                Piece(C_BOOT_R[2], (("shift", -20, 0),), z=-1), _robe(2, -0.04))),
          _CC[2], _CC[3]),
})

STRIDES = {"gunner": GUNNER_STRIDE, "colossus": COLOSSUS_STRIDE}


# ------------------------------------------------------------- derivation
def _poly_mask(shape, poly) -> np.ndarray:
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(im) > 0


VACATE_PX = 3           # px round a lifted piece cleared to the background (Gemini's halo, stray outline)


def _dilate(mask: np.ndarray, r: int) -> np.ndarray:
    return ge._dilate(mask, r)


def _layer(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    rgba = np.dstack([rgb, np.where(mask, 255, 0).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def _apply(layer: Image.Image, ops: tuple) -> Image.Image:
    for op in ops:
        if op[0] == "rot":
            layer = layer.rotate(op[1], resample=Image.NEAREST, center=op[2])
        elif op[0] == "shift":
            a = np.asarray(layer)
            layer = Image.fromarray(ge.shifted(a, int(op[2]), int(op[1])), "RGBA")
        elif op[0] == "shear":
            a = np.asarray(layer)
            out = np.zeros_like(a)
            k, y0 = op[1], op[2]
            for y in range(a.shape[0]):
                dx = int(round(k * max(0, y - y0)))
                out[y] = ge.shifted(a[y:y + 1], 0, dx)[0]
            layer = Image.fromarray(out, "RGBA")
        else:
            raise ValueError(f"unknown op {op[0]}")
    return layer


SPREAD_GAP = 80          # px each next figure moves right on the stride sheet: a swung boot must not touch
#                         the next figure (the cutter would merge them and cut at the emptiest column)
HALO_PX = 4              # px round a figure kept with it when the sheet is spread (Gemini's halo)


def _compose_view(rgb: np.ndarray, figs: list, bg: np.ndarray, vi: int, view: View) -> tuple[np.ndarray, np.ndarray]:
    """The sheet with view `vi`'s leg pieces moved, and the mask of what that view now covers."""
    h, w = rgb.shape[:2]
    fig = figs[vi]
    pieces = np.zeros((h, w), bool)
    under, low, high = [], [], []
    for poly in view.under:
        under.append(_layer(rgb, fig & _poly_mask((h, w), poly)))
    for p in view.pieces:
        m = fig & _poly_mask((h, w), p.poly) & ~pieces
        pieces |= m
        (low if p.z < 0 else high).append(_apply(_layer(rgb, m), p.ops))
    out = rgb.copy()
    body = fig & ~pieces
    vacated = _dilate(pieces, VACATE_PX) & ~body      # the lifted pieces and their halo
    out[vacated] = np.round(bg).astype(np.uint8)
    drawn = np.zeros((h, w), bool)
    for lay, over_body in [(x, False) for x in under + low] + [(x, True) for x in high]:
        a = np.asarray(lay)
        put = a[..., 3] > 0
        if not over_body:
            put &= ~body
        out[put] = a[..., :3][put]
        drawn |= a[..., 3] > 0
    return out, body | drawn


def derive_frame(rgb: np.ndarray, figs: list, bg: np.ndarray, views: tuple) -> tuple[np.ndarray, np.ndarray]:
    """One stride sheet: the five figures with their leg pieces moved, view v
    moved v x SPREAD_GAP px right on a wider canvas (same rows, same scale).
    Each figure keeps Gemini's own pixels round it (its halo, HALO_PX), so the
    cutter reads it as it reads the Gemini sheet. Also returns the mask of
    every pixel that differs from the unmoved sheet spread the same way (the
    seams Fooocus may repaint)."""
    h, w = rgb.shape[:2]
    others = np.zeros((h, w), bool)
    for f in figs:
        others |= f
    wide = np.empty((h, w + SPREAD_GAP * (len(figs) - 1), 3), np.uint8)
    wide[:] = np.round(bg).astype(np.uint8)
    plain = wide.copy()
    for vi in range(len(figs)):
        view = views[vi] if vi < len(views) else View()
        out, covers = _compose_view(rgb, figs, bg, vi, view)
        region = _dilate(covers, HALO_PX) & ~(others & ~figs[vi] & ~covers)
        keep = _dilate(figs[vi], HALO_PX) & ~(others & ~figs[vi])
        x = vi * SPREAD_GAP
        wide[:, x:x + w][region] = out[region]
        plain[:, x:x + w][keep] = rgb[keep]
    changed = np.abs(wide.astype(np.int32) - plain.astype(np.int32)).max(axis=-1) > 0
    return wide, changed


def spread_base(rgb: np.ndarray, figs: list, bg: np.ndarray) -> np.ndarray:
    """The unmoved sheet spread like the stride sheets (what Fooocus' masks are measured against)."""
    return derive_frame(rgb, figs, bg, ())[0]


def load(sheet: str):
    rgb = np.asarray(Image.open(REF / sheet).convert("RGB"))
    bg = ge.estimate_background(rgb)
    fg = ge.key_background(rgb, bg)
    figs = ge.figures(fg, 5)
    return rgb, bg, figs


def stride_name(enemy: str, letter: str, fooocus: bool = False) -> str:
    return f"gem_{enemy}_stride{letter}{'_fx' if fooocus else ''}.png"


def derive(enemy: str) -> dict:
    st = STRIDES[enemy]
    rgb, bg, figs = load(st.base)
    report = {}
    for letter, views in st.frames.items():
        out, changed = derive_frame(rgb, figs, bg, views)
        path = REF / stride_name(enemy, letter)
        ge.guard_out(path)
        Image.fromarray(out).save(path)
        report[letter] = {"file": path.name, "changed_px": int(changed.sum())}
        print(f"[stride] {enemy} {letter}: {path.name} ({int(changed.sum())} px moved)")
    return report


# ---------------------------------------------------------------- fooocus
INPAINT_SCRIPT = ROOT / "work" / "art" / "armband_fooocus" / "fooocus_inpaint.py"   # D108's no-download runner
FOOOCUS_PY = FOOOCUS_HOME.parent / "python_embeded" / "python.exe"
LEG_TOP = {"gunner": 300, "colossus": 380}      # crop rows from here to the sheet's bottom
MASK_TOP = {"gunner": 330, "colossus": 450}     # no repaint above: the belt and gun; the statue's pink knee joint (SDXL turns it orange)
CLOSE_PX = 6            # the derived silhouette closed by this much: Fooocus may fill a notch, not grow a blob
PROMPTS = {
    "gunner": ("pixel art sprite, 16-bit video game soldier walking, mid stride, khaki trousers with folds, "
               "black laced combat boots, hard dark outline, flat shading, flat magenta background",
               "photo, realistic, 3d render, blurry, soft, extra legs, extra feet, deformed, text, watermark, "
               "shadow on the ground, floor, gradient background"),
    "colossus": ("pixel art sprite, 16-bit video game, stone statue of liberty walking, heavy grey-green robe "
                 "with deep folds swinging, metal armoured boots under the hem, hard dark outline, flat magenta "
                 "background",
                 "photo, realistic, 3d render, blurry, soft, bare feet, extra legs, deformed, text, watermark, "
                 "shadow on the ground, floor, gradient background"),
}


def _crop_box(fig: np.ndarray, top: int) -> tuple[int, int, int, int]:
    xs = np.flatnonzero(fig.any(axis=0))
    return int(max(0, xs[0] - 8)), int(top), int(min(fig.shape[1], xs[-1] + 9)), int(fig.shape[0])


def _erode(mask: np.ndarray, r: int) -> np.ndarray:
    return ~ge._dilate(~mask, r)


def fooocus_job(enemy: str, denoise: float = FOOOCUS_DENOISE, seeds=FOOOCUS_SEEDS) -> list[dict]:
    """Per stride frame and view: the legs' crop x4 (NEAREST: SDXL sees Gemini's pixels, not a blur)
    and the mask of what the derivation moved, padded by SEAM_PAD."""
    st = STRIDES[enemy]
    runs = []
    d = FOOOCUS_DIR / enemy
    d.mkdir(parents=True, exist_ok=True)
    for letter in st.frames:
        rgb = np.asarray(Image.open(REF / stride_name(enemy, letter)).convert("RGB"))
        b_rgb, bg, b_figs = load(st.base)
        base = spread_base(b_rgb, b_figs, bg)
        changed = np.abs(rgb.astype(np.int32) - base.astype(np.int32)).max(axis=-1) > 0
        figs = ge.figures(ge.key_background(rgb, bg), 5)
        for v, fig in enumerate(figs):
            x0, y0, x1, y1 = _crop_box(fig, LEG_TOP[enemy])
            m = ge._dilate(changed & ge._dilate(fig, SEAM_PAD), SEAM_PAD)
            m[:MASK_TOP[enemy]] = False
            m = m[y0:y1, x0:x1]
            if not m.any():
                continue
            name = f"{enemy}_{letter}{v}"
            up = (x1 - x0) * FOOOCUS_UP, (y1 - y0) * FOOOCUS_UP
            Image.fromarray(rgb[y0:y1, x0:x1]).resize(up, Image.NEAREST).save(d / f"{name}_init.png")
            Image.fromarray(np.where(m, 255, 0).astype(np.uint8)).resize(up, Image.NEAREST).save(d / f"{name}_mask.png")
            runs.append({"name": name, "image": str(d / f"{name}_init.png"), "mask": str(d / f"{name}_mask.png"),
                         "prompt": PROMPTS[enemy][0], "negative": PROMPTS[enemy][1], "denoise": denoise,
                         "seeds": list(seeds), "steps": 30, "cfg": 5.0, "box": [x0, y0, x1, y1]})
    return runs


def write_job(enemies, denoise: float) -> Path:
    runs = [r for e in enemies for r in fooocus_job(e, denoise)]
    job = {"fooocus": str(FOOOCUS_HOME), "model": FOOOCUS_MODEL, "out": str(FOOOCUS_DIR / "out"), "runs": runs}
    path = FOOOCUS_DIR / f"job_d{int(denoise * 100)}.json"
    path.write_text(json.dumps(job, indent=1), encoding="utf-8")
    print(f"[stride] {len(runs)} inpaint runs -> {path.relative_to(ROOT).as_posix()}; run with: "
          f"{FOOOCUS_PY} -s {INPAINT_SCRIPT} {path}")
    return path


def merge_fooocus(enemy: str, job: Path) -> dict:
    """The repainted crops back into the stride sheets, inside each mask and
    inside the derived silhouette closed by CLOSE_PX -> gem_<enemy>_stride<L>_fx.png."""
    spec = json.loads(job.read_text(encoding="utf-8"))
    out_dir = Path(spec["out"])
    st = STRIDES[enemy]
    report = {}
    for letter in st.frames:
        rgb = np.asarray(Image.open(REF / stride_name(enemy, letter)).convert("RGB")).copy()
        bg = ge.estimate_background(rgb)
        fg = ge.key_background(rgb, bg)
        allowed = _erode(ge._dilate(fg, CLOSE_PX), CLOSE_PX)
        used = 0
        for run in spec["runs"]:
            if not run["name"].startswith(f"{enemy}_{letter}"):
                continue
            res = out_dir / f"{run['name']}_s{run['seeds'][0]}.png"
            if not res.is_file():
                continue
            x0, y0, x1, y1 = run["box"]
            small = np.asarray(Image.open(res).convert("RGB").resize((x1 - x0, y1 - y0), Image.BOX))
            m = np.asarray(Image.open(run["mask"]).convert("L").resize((x1 - x0, y1 - y0), Image.NEAREST)) > 127
            sub = rgb[y0:y1, x0:x1]
            keep = m & allowed[y0:y1, x0:x1]
            sub[keep] = small[keep]
            sub[m & ~allowed[y0:y1, x0:x1]] = np.round(bg).astype(np.uint8)
            used += 1
        path = REF / stride_name(enemy, letter, fooocus=True)
        Image.fromarray(rgb).save(path)
        report[letter] = {"file": path.name, "crops": used}
        print(f"[stride] {enemy} {letter}: {used} Fooocus crops -> {path.name}")
    return report


# ------------------------------------------------------------------ build
OUT = ROOT / "work" / "art" / "walk_stride"     # the stride builds: NOT work/art/enemies_gemini/ (what assets/ matches)
BASE_SPECS = {"gunner": "GUNNER", "colossus": "COLOSSUS"}


def stride_spec(enemy: str, fooocus: bool = False):
    """gemini_enemy's spec with A and C read from the stride sheets (no rock: the legs move)."""
    import dataclasses
    spec = ge.PENDING[enemy]
    old = spec.sheets.get("walkL") or spec.sheets["strideA"]     # before or after gemini_enemy.py.patch
    sheets = {k: v for k, v in spec.sheets.items() if k not in ("walkL", "walkR")}
    for letter in "AC":
        sheets[f"stride{letter}"] = dataclasses.replace(old, file=stride_name(enemy, letter, fooocus))
    rotated = dict(spec.rotated)
    rotated["A"], rotated["C"] = ge.Rotated("strideA"), ge.Rotated("strideC")
    return dataclasses.replace(spec, sheets=sheets, rotated=rotated)


ALIGN_MAX = 8           # game px searched each way to put A/C's upper body over B's
UPPER_FRAC = 0.5        # the top half of the figure (helmet to belt): what must not jump sideways


def _screen_alpha(path: Path) -> tuple[np.ndarray, tuple[int, int]]:
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGBA"))
    return a, ge.read_grab(path)


def torso_shift(a: np.ndarray, ga: tuple, b: np.ndarray, gb: tuple) -> int:
    """Columns A's picture moves right so its upper body lies over B's (most
    alpha overlap). The legs' axis (the cutter's anchor) moves when a leg
    does; the torso of a walk cycle must not."""
    def upper(rgba, grab):
        al = rgba[..., 3] > 0
        ys = np.flatnonzero(al.any(axis=1))
        cut = ys[0] + int((ys[-1] - ys[0] + 1) * UPPER_FRAC)
        al[cut:] = False
        return al, grab
    ma, (gax, gay) = upper(a, ga)
    mb, (gbx, gby) = upper(b, gb)
    oy = max(gay, gby) + 2                       # the floor line's row in a shared screen
    H = oy + max(ma.shape[0] - gay, mb.shape[0] - gby) + 2
    ox = max(gax, gbx) + ALIGN_MAX + 2
    W = ox + max(ma.shape[1] - gax, mb.shape[1] - gbx) + ALIGN_MAX + 2

    def put(m, gx, gy, dx):
        c = np.zeros((H, W), bool)
        y0, x0 = oy - gy, ox - gx + dx
        c[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
        return c
    cb = put(mb, gbx, gby, 0)
    best = max(range(-ALIGN_MAX, ALIGN_MAX + 1),
               key=lambda dx: (int((put(ma, gax, gay, dx) & cb).sum()), -abs(dx)))
    return best


def align_letters(folder: Path, sprite: str, letters: str = "AC", ref: str = "B") -> dict:
    """Each A/C rotation moved sideways onto B's upper body; one canvas per
    letter again (left = half the width, the floor line kept: MOD-SPEC 6.3)."""
    shifts = {}
    for letter in letters:
        pics = {}
        for r in "12345678":
            p = folder / f"{sprite}{letter}{r}.png"
            a, ga = _screen_alpha(p)
            b, gb = _screen_alpha(folder / f"{sprite}{ref}{r}.png")
            dx = torso_shift(a, ga, b, gb)
            shifts[f"{sprite}{letter}{r}"] = dx
            pics[p] = (a, ga[0] - dx, ga[1])          # the column that lands on the actor's axis
        half = max(max(ax + 1, a.shape[1] - ax) for a, ax, _ in pics.values())
        for p, (a, ax, top) in pics.items():
            canvas = np.zeros((a.shape[0], 2 * half, 4), np.uint8)
            x0 = half - ax
            canvas[:, x0:x0 + a.shape[1]] = a
            ge.save_sprite(canvas, (half, top), p)
    return shifts


def build(enemy: str, fooocus: bool = False) -> Path:
    out = OUT / (enemy + ("_fx" if fooocus else ""))
    out.mkdir(parents=True, exist_ok=True)
    spec = stride_spec(enemy, fooocus)
    m = ge.build(spec, out_dir=out)
    shifts = align_letters(out, spec.sprite)
    (out / "align.json").write_text(json.dumps(shifts, indent=1), encoding="utf-8")
    print(f"[stride] torso shifts (game px): {shifts}")
    print(f"[stride] built {enemy}{' (fooocus)' if fooocus else ''}: {m['lumps']} lumps -> {out.relative_to(ROOT).as_posix()}")
    return out


# ------------------------------------------------------------ the patch
GE_PATH = Path(ge.__file__)
SPEC_EDITS = {   # gemini_enemy.py once the CEO approves: A/C read the stride sheets (exact text, once each)
    # The left side of each pair is gemini_enemy.py's text before the patch, matched byte for byte, so its
    # Spanish notes (written before D129) stay as they were; D128 applied the patch, so this is now history.
    "gunner": (
        ('        "walkL": Sheet("gem_gunner_walkL.png", 5, SIDES_RIGHT, None),\n'
         '        "walkR": Sheet("gem_gunner_walkR.png", 5, SIDES_RIGHT, None),\n',
         '        "strideA": Sheet("gem_gunner_strideA.png", 5, SIDES_RIGHT, None),   # D127: tools/art/walk_stride.py\n'
         '        "strideC": Sheet("gem_gunner_strideC.png", 5, SIDES_RIGHT, None),\n'),
        ('path=GUNNER_DEATH_PATH),\n    },\n    rotated={\n'
         '        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),\n',
         'path=GUNNER_DEATH_PATH),\n    },\n    rotated={\n'
         '        "A": Rotated("strideA"), "B": Rotated("turn"), "C": Rotated("strideC"), "D": Rotated("turn"),\n'),
        ('"B y D: la vista de pie (turn); A = walkL, C = walkR. OJO: walkL y walkR son casi la misma imagen "\n'
         '        "(difieren en un 0,5 % de los píxeles) y solo la vista de frente levanta un pie; 3/4, perfil y espalda "\n'
         '        "son la vista de pie: el ciclo de andar apenas se mueve (ver la lista)",',
         '"B and D: the standing view (turn). A and C (D127): Gemini gave no strides (walkL = walkR = turn), so "\n'
         '        "they come from turn with the legs cut out and moved (tools/art/walk_stride.py): A the left leg "\n'
         '        "forward, C the right; from the front and the back one boot goes up, in profile the legs open (A) and "\n'
         '        "the near one passes in front (C). walk_stride.py build puts the torso of A and C over B\'s (the "\n'
         '        "raised leg moves the legs\' axis): build them with it, not with this command",'),
        ('        ("gem_gunner_walkL.png, gem_gunner_walkR.png", "Same Liberty Legion gunner, same style, scale and "\n'
         '         "magenta background, 5 views (front, 3/4 front, profile, 3/4 back, back) mid-stride: in walkL the LEFT "\n'
         '         "leg forward, in walkR the RIGHT leg forward, in EVERY view (the side views must show the stride, "\n'
         '         "not the standing pose); M1919 at the hip, belt over the shoulder"),\n', ''),
    ),
    "colossus": (
        ('        "walkL": Sheet("gem_colossus_walkL.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),\n'
         '        "walkR": Sheet("gem_colossus_walkR.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),\n',
         '        "strideA": Sheet("gem_colossus_strideA.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),   # D127\n'
         '        "strideC": Sheet("gem_colossus_strideC.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),\n'),
        ('"A": Rotated("walkL", tilt=COLOSSUS_SWAY), "B": Rotated("turn"),\n'
         '        "C": Rotated("walkR", tilt=-COLOSSUS_SWAY), "D": Rotated("turn"),',
         '"A": Rotated("strideA"), "B": Rotated("turn"),\n'
         '        "C": Rotated("strideC"), "D": Rotated("turn"),'),
        ("COLOSSUS_SWAY = 3.0     # degrees: the walk's derived rock from foot to foot (Gemini's two strides are one pose)\n",
         ""),
        ("OJO: walkL y walkR son casi la misma imagen (difieren en un 0,3 % de los píxeles): Gemini no dio zancadas. "
         "A = walkL inclinada 3 grados, C = walkR inclinada -3 grados: se balancea de un pie a otro, pesado, como una "
         "estatua (ver la lista)",
         "A and C (D127): Gemini gave no strides (walkL = walkR), so they come from walkL with the boots cut out and "
         "moved (tools/art/walk_stride.py): one boot goes up under the robe (or the metal leg in the slit, in "
         "front) and the robe swings; in profile the front boot steps forward (A) and the back one passes (C). "
         "walk_stride.py build puts the torso of A and C over B's: build them with it, not with this command"),
        ('        ("gem_colossus_walkL.png, gem_colossus_walkR.png", "Same colossus, same style, scale and background, 5 "\n'
         '         "views mid-stride: in walkL the LEFT leg forward, in walkR the RIGHT leg forward, in EVERY view (the "\n'
         '         "side and back views must show the stride, the robe swinging), torch raised"),\n', ''),
    ),
}


def patched_spec_text(text: str, enemies=("gunner", "colossus")) -> str:
    for e in enemies:
        for old, new in SPEC_EDITS[e]:
            if text.count(old) != 1:
                raise SystemExit(f"walk_stride: gemini_enemy.py changed, re-measure the patch ({e}: {old[:60]!r}...)")
            text = text.replace(old, new)
    return text


def install_patch(enemies=("gunner", "colossus")) -> list[Path]:
    """work/art/walk_stride/: gemini_enemy.py.patch (git apply) and install.sh,
    which copies A1-A8 and C1-C8 of each into assets/sprites/<folder>/ AND
    work/art/enemies_gemini/<name>/ (tests/test_gemini_enemy_install.py wants the
    two identical). Writes nothing outside work/."""
    import difflib
    text = GE_PATH.read_text(encoding="utf-8")
    rel = GE_PATH.relative_to(ROOT).as_posix()
    diff = difflib.unified_diff(text.splitlines(keepends=True), patched_spec_text(text, enemies).splitlines(keepends=True),
                                f"a/{rel}", f"b/{rel}")
    patch = OUT / "gemini_enemy.py.patch"
    ge.guard_out(patch)
    patch.write_text("".join(diff), encoding="utf-8", newline="\n")
    lines = ["#!/usr/bin/env bash",
             f"# D127: the new walk letters A and C, ONLY after the CEO's OK on {PREVIEW.relative_to(ROOT).as_posix()}.",
             "# Run from the repo root. B, D and every other letter stay as installed by D123.",
             "set -euo pipefail"]
    for e in enemies:
        spec = ge.PENDING[e]
        src = OUT / (e + ("_fx" if CHOICE[e] == "fooocus" else ""))
        for dest in (f"assets/sprites/{FOLDERS[e]}", f"work/art/enemies_gemini/{e}"):
            lines.append(f"cp {src.relative_to(ROOT).as_posix()}/{spec.sprite}[AC][1-8].png {dest}/")
    lines += [f"git apply {patch.relative_to(ROOT).as_posix()}",
              'echo "installed A1-A8 and C1-C8 of SDLG and SDLC; gemini_enemy.py now reads the stride sheets"']
    sh = OUT / "install.sh"
    sh.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return [patch, sh]


# ---------------------------------------------------------------- preview
CHOICE = {"gunner": "derived", "colossus": "derived"}   # derived | fooocus: what goes to the CEO (the pick)
PREVIEW = ROOT / "docs" / "art" / "previews" / "2026-10-24_P4_walks.html"
WALK_TICS = 6           # See: A A B B C C D D at 3 tics = each letter 6 tics (both actors)
ZOOM = {"gunner": 3, "colossus": 2}
FOLDERS = {"gunner": "legion_gunner", "colossus": "colossus"}


def _frames(folder: Path, sprite: str) -> dict:
    import base64
    out = {}
    for letter in "ABCD":
        for r in "12345678":
            p = folder / f"{sprite}{letter}{r}.png"
            with Image.open(p) as im:
                size = im.size
            gx, gy = ge.read_grab(p)
            out[f"{letter}{r}"] = {"src": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode(),
                                   "gx": gx, "gy": gy, "w": size[0], "h": size[1]}
    return out


def preview(choice: dict, out: Path = PREVIEW) -> Path:
    """The CEO's page: per enemy and rotation, the walk cycle looping before (assets/) and after."""
    items = []
    for enemy, variant in choice.items():
        spec = ge.PENDING[enemy]
        new_dir = OUT / (enemy + ("_fx" if variant == "fooocus" else ""))
        items.append({"id": enemy, "sprite": spec.sprite, "zoom": ZOOM[enemy], "variant": variant,
                      "before": _frames(ge.SPRITES_DIR / FOLDERS[enemy], spec.sprite),
                      "after": _frames(new_dir, spec.sprite)})
    html = (Path(__file__).with_name("walk_stride_preview.html").read_text(encoding="utf-8")
            .replace("/*ITEMS*/[]", json.dumps(items)).replace("/*TICS*/6", str(WALK_TICS)))
    ge.guard_out(out)
    out.write_text(html, encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("derive", "build", "fooocus-job", "fooocus-merge", "build-fx", "preview"))
    ap.add_argument("--denoise", type=float, default=FOOOCUS_DENOISE)
    ap.add_argument("enemy", nargs="?", default="all")
    a = ap.parse_args(argv)
    names = list(STRIDES) if a.enemy == "all" else [a.enemy]
    FOOOCUS_DIR.mkdir(parents=True, exist_ok=True)
    if a.cmd == "derive":
        for n in names:
            derive(n)
    if a.cmd == "build":
        for n in names:
            build(n)
    if a.cmd == "fooocus-job":
        write_job(names, a.denoise)
    if a.cmd == "fooocus-merge":
        for n in names:
            merge_fooocus(n, FOOOCUS_DIR / f"job_d{int(a.denoise * 100)}.json")
    if a.cmd == "preview":
        print(f"[stride] wrote {preview(CHOICE).relative_to(ROOT).as_posix()}")
        for f in install_patch():
            print(f"[stride] wrote {f.relative_to(ROOT).as_posix()}")
    if a.cmd == "build-fx":
        for n in names:
            build(n, fooocus=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
