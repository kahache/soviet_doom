"""The Liberty Colossus (SDLC) from the PM's Gemini sheets (D104, D116, D119): the
steps gemini_enemy.py does not do for him, around its build.

    python tools/art/colossus_gemini.py split     # aim/fire: views 3-4-5 pulled apart -> *_sep.png (work/, D77)
    python tools/art/colossus_gemini.py build     # split + gemini_enemy.build(COLOSSUS) -> work/art/enemies_gemini/colossus/
    python tools/art/colossus_gemini.py sheet     # the CEO's preview + the install patch (needs build)
    python tools/art/colossus_gemini.py all       # the three

Why a split. On gem_colossus_aim.png and gem_colossus_fire.png the profile's
arm (torch levelled, flame jet, rocket) lies over the 3/4 back view's
shoulders, and that view's torch touches the back view's tablet: three
figures in one component whose columns overlap, so no column cut parts them
(gemini_enemy's split_x / path). They are parted by mask instead:

  1. every pixel goes to the figure of gem_colossus_walkL.png (registered on
     this sheet) it grows from, as gemini_enemy.guided_figures does: the
     walk sheet is the same five bodies standing;
  2. hand polygons (sheet pixels, measured on x4 zooms) override that where
     the guide cannot know: OWN_* polygons give everything inside to one
     figure (the profile's arm and torch; the 3/4 back's torch and smoke);
     DROP_* polygons are the two rockets in flight on the fire sheet (the
     rocket is its own actor, SD_ColossusRocket, as the Panzermensch's
     projectile is dropped from his sheet); KEEP_FIRE keeps only flame
     colours inside (the 3/4 front's rocket out of its burst);
  3. what the profile's arm (or its flame and rocket) covers of the 3/4 back
     view is repainted from the walk sheet (aim) or from the aim result
     (fire), registered, so that body has no hole;
  4. the five figures are written on a wider canvas, views 4 and 5 moved
     right by SEP_GAP, the background colour estimated on the sheet: the
     plain cutter then finds five figures.

Nothing here writes outside work/ (gemini_enemy.guard_out); the preview goes
to docs/art/previews/ (an HTML page, no source image), the install patch to
work/art/enemies_gemini/colossus/ and is run by the PM on the CEO's OK.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import gemini_enemy as ge  # noqa: E402

ROOT = ge.ROOT
WALK = "gem_colossus_walkL.png"
AIM, FIRE = "gem_colossus_aim.png", "gem_colossus_fire.png"
AIM_SEP, FIRE_SEP = "gem_colossus_aim_sep.png", "gem_colossus_fire_sep.png"
SEP_GAP = 120          # px views 4 and 5 move right, each (fig 3's torch ends at 724, fig 4 starts at 632)
VIEWS = 5
PROFILE, BACK34, BACK = 2, 3, 4    # figure indices on the sheet, left to right

# (figure, polygon): everything of the sheet inside goes to that figure.
OWN_AIM = (
    # the profile's arm, hand and levelled torch (barrel x 692-711, glow to 723), over the 3/4 back
    # view's shoulders; under the hand (y > 184) that view's flag, right of the barrel its neck and robe
    (PROFILE, ((590, 150), (650, 150), (690, 151), (692, 143), (711, 143), (711, 151), (718, 152), (723, 160),
               (723, 178), (718, 185), (711, 186), (711, 196), (692, 196), (690, 186), (668, 184), (640, 184),
               (590, 187))),
    # the 3/4 back view's torch arm and disc, down to the back view's tablet (its top edge runs from
    # (787, 212) up to (825, 188)) and left of that view's flag (x 828 on)
    (BACK34, ((735, 128), (840, 128), (840, 158), (826, 166), (826, 182), (800, 197), (790, 201), (735, 201))),
)
OWN_FIRE = (
    # the profile's smoke and flame jet along the arm, tapered to a tongue where the rocket's tail was
    (PROFILE, ((540, 150), (560, 139), (600, 136), (650, 137), (668, 145), (684, 147), (699, 157), (701, 165),
               (699, 174), (684, 185), (660, 186), (600, 191), (540, 191))),
    (BACK34, ((735, 108), (842, 108), (842, 158), (826, 166), (826, 182), (800, 197), (790, 201), (735, 201))),
)
# the profile's rocket in flight (tail at x 700, nose at 771) and the flame round its tail, over the
# 3/4 back view; the jet's tongue (OWN_FIRE) is kept out of it
DROP_FIRE = (((678, 143), (735, 145), (746, 149), (759, 155), (772, 165), (759, 176), (741, 178),
              (723, 178), (713, 187), (678, 187)),)
# the 3/4 front's rocket leaving its burst: only flame colours stay in this box
KEEP_FIRE = ((1, (447, 126, 514, 172)),)


def poly_mask(shape: tuple[int, int], pts) -> np.ndarray:
    im = Image.new("1", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1)
    return np.asarray(im, bool)


def guide_masks(walk_rgb: np.ndarray) -> list[np.ndarray]:
    return ge.figures(ge.key_background(walk_rgb, ge.estimate_background(walk_rgb)), VIEWS)


def owners(rgb: np.ndarray, fg: np.ndarray, guide_rgb: np.ndarray, gmasks: list[np.ndarray],
           own: tuple) -> tuple[list[np.ndarray], np.ndarray, list[np.ndarray]]:
    """(per-figure masks, the guide registered on this sheet, the guide's masks registered)."""
    masks, _, g_rgb = ge.guided_figures(fg, rgb, guide_rgb, gmasks)
    union = np.zeros_like(fg)
    for g in gmasks:
        union |= g
    dy, dx = ge.align_guide(rgb, guide_rgb, union & fg)
    gm = [ge.shifted(g, dy, dx, False) for g in gmasks]
    for k, pts in own:
        p = poly_mask(fg.shape, pts) & fg
        for j in range(len(masks)):
            masks[j] = masks[j] & ~p
        masks[k] = masks[k] | p
    return masks, g_rgb, gm


def compose(figs: list[tuple[np.ndarray, np.ndarray]], bg, gap: int = SEP_GAP) -> np.ndarray:
    """The figures (full-sheet rgb, mask) on a canvas `gap` wider per moved view."""
    h, w = figs[0][1].shape
    out = np.empty((h, w + 2 * gap, 3), np.uint8)
    out[:] = np.array(bg, np.uint8)
    for k, (rgb, m) in enumerate(figs):
        off = 0 if k < BACK34 else gap * (k - PROFILE)
        ys, xs = np.nonzero(m)
        out[ys, xs + off] = rgb[ys, xs]
    return out


def split_aim(ref_dir: Path = ge.REF_DIR) -> tuple[np.ndarray, list[tuple[np.ndarray, np.ndarray]]]:
    walk, aim = ge.load_rgb(ref_dir / WALK), ge.load_rgb(ref_dir / AIM)
    fg = ge.key_background(aim, ge.estimate_background(aim))
    masks, g_rgb, gm = owners(aim, fg, walk, guide_masks(walk), OWN_AIM)
    figs = [(aim, m) for m in masks]
    # the 3/4 back view under the profile's arm: the walk sheet's pixels of that figure
    cover = poly_mask(fg.shape, OWN_AIM[0][1]) & fg & gm[BACK34]
    rgb4 = aim.copy()
    rgb4[cover] = g_rgb[cover]
    figs[BACK34] = (rgb4, masks[BACK34] | cover)
    figs = [(rgb, ge._drop_crumbs(m)) for rgb, m in figs]
    return compose(figs, ge.estimate_background(aim)), figs


def split_fire(aim_figs, ref_dir: Path = ge.REF_DIR) -> np.ndarray:
    walk, fire = ge.load_rgb(ref_dir / WALK), ge.load_rgb(ref_dir / FIRE)
    fg = ge.key_background(fire, ge.estimate_background(fire))
    masks, _, _ = owners(fire, fg, walk, guide_masks(walk), OWN_FIRE)
    drop = np.zeros_like(fg)
    for pts in DROP_FIRE:
        drop |= poly_mask(fg.shape, pts)
    drop &= ~poly_mask(fg.shape, OWN_FIRE[0][1])
    for k, (x0, y0, x1, y1) in KEEP_FIRE:
        box = np.zeros_like(fg)
        box[y0:y1, x0:x1] = True
        masks[k] &= ~(box & ~ge.bridge_mask(fire, "fire"))
    masks = [m & ~drop for m in masks]
    figs = [(fire, m) for m in masks]
    # the 3/4 back view behind the flame and the rocket: the aim result's figure, registered
    a_rgb, a_mask = aim_figs[BACK34]
    dy, dx = ge.align_guide(fire, a_rgb, a_mask & masks[BACK34])
    a_rgb, a_mask = ge.shifted(a_rgb, dy, dx), ge.shifted(a_mask, dy, dx, False)
    cover = (poly_mask(fg.shape, OWN_FIRE[0][1]) | drop) & fg & a_mask
    rgb4 = fire.copy()
    rgb4[cover] = a_rgb[cover]
    figs[BACK34] = (rgb4, masks[BACK34] | cover)
    figs = [(rgb, ge._drop_crumbs(m)) for rgb, m in figs]
    return compose(figs, ge.estimate_background(fire))


def split(ref_dir: Path = ge.REF_DIR) -> list[Path]:
    aim_sep, aim_figs = split_aim(ref_dir)
    fire_sep = split_fire(aim_figs, ref_dir)
    out = []
    for name, img in ((AIM_SEP, aim_sep), (FIRE_SEP, fire_sep)):
        p = ref_dir / name
        ge.guard_out(p)
        Image.fromarray(img, "RGB").save(p)
        out.append(p)
    return out


# ------------------------------------------------------------ the CEO's sheet
SHEET_HTML = ROOT / "docs" / "art" / "previews" / "2026-10-23_P4_colossus-gemini.html"
ACTOR = ROOT / "src" / "zscript" / "monsters" / "liberty_colossus.zs"
PROV_FOLDER, PROV_SPRITE, PROV_SCALE = "general", "SDGN", 1.3   # what he wears today (PROVISIONAL-D116)
# liberty_colossus.zs: Translation "0:255=%[0.05,0.05,0.10]:[1.60,1.60,1.80]": the palette by luminance
# onto that ramp. Imitated here for the comparison only (NOT VERIFIED against the engine's palettised tint).
PROV_RAMP = ((0.05, 0.05, 0.10), (1.60, 1.60, 1.80))
LINEUP_ZOOM = 2
LINEUP = (   # (label, lump, kind): the provisional, the new set, the General as he is, then the attacks
    ("provisional today B1 (SDGN x1.3 chrome)", "SDGNB1", "prov"), ("new SDLC B1", "SDLCB1", "new"),
    ("The General SDGN B1", "SDGNB1", "general"),
    ("new E1 (aims)", "SDLCE1", "new"), ("new F1 (fires)", "SDLCF1", "new"),
    ("new Q1 (foot up)", "SDLCQ1", "new"), ("new R1 (stomp)", "SDLCR1", "new"),
)


def tint_provisional(rgba: np.ndarray, ramp=PROV_RAMP) -> np.ndarray:
    out = rgba.copy()
    lum = (0.299 * rgba[..., 0] + 0.587 * rgba[..., 1] + 0.114 * rgba[..., 2]) / 255.0
    lo, hi = ramp
    for c in range(3):
        out[..., c] = np.clip((lo[c] + lum * (hi[c] - lo[c])) * 255.0, 0, 255).astype(np.uint8)
    return out


def scaled(rgba: np.ndarray, grab: tuple[int, int], k: float) -> tuple[np.ndarray, tuple[int, int]]:
    """The engine's `Scale k`, nearest neighbour, offsets scaled with it."""
    if k == 1.0:
        return rgba, grab
    h, w = rgba.shape[:2]
    im = Image.fromarray(rgba, "RGBA").resize((max(1, round(w * k)), max(1, round(h * k))), Image.NEAREST)
    return np.asarray(im), (round(grab[0] * k), round(grab[1] * k))


def provisional_frames(spec, sprites_dir: Path = ge.SPRITES_DIR) -> dict:
    """The lumps the actor wears today (SDGN, tinted, x1.3) under the new names (SDGNB1 -> SDLCB1)."""
    out = {}
    for p in sorted((sprites_dir / PROV_FOLDER).glob(f"{PROV_SPRITE}*.png")):
        with Image.open(p) as im:
            rgba, g = scaled(tint_provisional(np.asarray(im.convert("RGBA"))), ge.read_grab(p) or (0, 0),
                             PROV_SCALE)
        img = Image.fromarray(rgba, "RGBA")
        out[spec.sprite + p.stem.upper()[len(PROV_SPRITE):]] = {"src": ge._b64(img), "w": img.width,
                                                               "h": img.height, "left": g[0], "top": g[1]}
    return out


def lineup(new_dir: Path, sprites_dir: Path = ge.SPRITES_DIR, z: int = LINEUP_ZOOM) -> Image.Image:
    """The scale check: provisional, new, the General, then the attack poses, on one floor line."""
    pics = []
    for label_txt, lump, kind in LINEUP:
        p = (new_dir if kind == "new" else sprites_dir / PROV_FOLDER) / f"{lump}.png"
        with Image.open(p) as im:
            rgba = np.asarray(im.convert("RGBA"))
        grab = ge.read_grab(p) or (0, 0)
        if kind == "prov":
            rgba, grab = scaled(tint_provisional(rgba), grab, PROV_SCALE)
        op = rgba[..., 3] > 0
        rows = np.flatnonzero(op.any(axis=1))
        pics.append((f"{label_txt}: {rows[-1] - rows[0] + 1} px", rgba, grab))
    above = max(g[1] for _, _, g in pics)
    below = max(a.shape[0] - g[1] for _, a, g in pics)
    cell = max(max(g[0], a.shape[1] - g[0]) for _, a, g in pics) * 2 * z + 16
    head, foot = 10, 44
    img = Image.new("RGB", (cell * len(pics), head + (above + below) * z + foot), (59, 61, 66))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 12)
    except OSError:  # pragma: no cover - no system font
        font = ImageFont.load_default()
    floor = head + above * z
    dr.line([(0, floor), (img.width, floor)], fill=(110, 112, 118))
    for i, (label_txt, rgba, (left, top)) in enumerate(pics):
        big = Image.fromarray(rgba, "RGBA").resize((rgba.shape[1] * z, rgba.shape[0] * z), Image.NEAREST)
        img.paste(big, (i * cell + cell // 2 - left * z, floor - top * z), big)
        y = floor + below * z + 6
        for part in label_txt.split(": "):
            dr.text((i * cell + 6, y), part, fill=(230, 226, 218), font=font)
            y += 15
    return img


INTRO = (
    "<p>The <b>Liberty Colossus</b> (<code>SD_LibertyColossus</code>, Episode 2's boss, final sprite "
    "<code>SDLC</code>, 81 lumps with the General's letters: design <code>docs/engine/2026-10-22_P4_ep2-enemies.md</code> "
    "§4), taken from today's Gemini sheets: <code>turn</code> (standing), <code>walkL</code>, <code>walkR</code>, <code>aim</code>, <code>fire</code>, "
    "<code>stomp</code> (2 rows) and <code>death</code>. <b>Current</b> = what he wears in the game today: the General "
    "<code>SDGN</code> ×1.3 tinted chrome (D116, what you saw «en blanco y negro» (\"in black and white\"); the tint here is an imitation of the "
    "<code>Translation</code>, NOT VERIFIED). <b>New</b> = SDLC, at boss size: 128 px tall with the torch "
    "(the body is 110 units), no <code>Scale</code> and no tint. Everything ×3 without smoothing on its floor line (the light "
    "line) with the real offsets. What you asked for (D119): <b>from the front he fires at you</b>: in E1/F1 the torch aims "
    "at the camera. Only insignia: the US flag on the shoulder; the tablet, blank. Nothing installed: the lumps are in "
    "<code>work/art/enemies_gemini/colossus/</code> with the actor patch (removes the provisional tint and scale). "
    "Mark OK / NO / ? per row and press <b>Copy result</b>.</p>")


def colossus_sheet(spec, out: Path = SHEET_HTML, out_root: Path = ge.OUT_ROOT,
                   sprites_dir: Path = ge.SPRITES_DIR) -> Path:
    new_dir = out_root / spec.name
    metrics = json.loads((new_dir / "metrics.json").read_text(encoding="utf-8"))
    item = {
        "id": spec.name, "sprite": spec.sprite, "letters": sorted(spec.rotated),
        "anims": [{"label": a[0], "seq": [list(s) for s in a[1]]} for a in spec.anims],
        "cur": provisional_frames(spec, sprites_dir), "new": ge._frames_json(new_dir, spec.sprite),
        "derived": list(spec.derived), "notes": spec.notes,
        "gate": metrics.get("gate", []), "reask": metrics.get("reask", []), "symbol": "",
        "sheets": {k: [f["facing"] + (" (mirrored)" if f["mirrored"] else "") for f in v["figures"]]
                   for k, v in metrics["sheets"].items()},
    }
    intro = INTRO + (f'<h3>Scale: provisional, new and the General (×{LINEUP_ZOOM})</h3><p><img alt="Scale line-up" '
                     f'style="max-width:100%;image-rendering:pixelated" src="{ge._b64(lineup(new_dir, sprites_dir))}"></p>')
    html = ge.SHEET_TEMPLATE
    for old, new in (
            ("<title>Gemini Enemies</title>", "<title>Gemini Colossus</title>"),
            ("Soviet Doom · Enemies redrawn with Gemini (draft)",
             "Soviet Doom · The Liberty Colossus with Gemini (draft, D119)"),
            ('const KEY = "sd-2026-10-22_P4_enemies-gemini";', 'const KEY = "sd-2026-10-23_P4_colossus-gemini";'),
            ("Gemini enemies (2026-10-22_P4, D104/D105)", "Gemini Colossus (2026-10-23_P4, D119)")):
        if html.count(old) != 1:
            raise ValueError(f"colossus_sheet: the review template changed ({old!r})")
        html = html.replace(old, new)
    i0 = html.index("<p>Each enemy")
    i1 = html.index("</p>", i0) + len("</p>")
    html = html[:i0] + intro + html[i1:]
    html = html.replace("/*ITEMS*/[]", json.dumps([item]))
    ge.guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


# ------------------------------------------------------------- the install
PROVISIONAL_HEADER_START = "// PROVISIONAL LOOK (D116):"
PROVISIONAL_HEADER_END = "// (MOD-SPEC 6.12; tests/test_ep2_enemies.py pins both halves).\n"
INSTALLED_HEADER = (
    "// LOOK (D119): SDLC, his own 81 lumps drawn from the CEO's Gemini sheets by\n"
    "// tools/art/colossus_gemini.py (gemini_enemy.py's COLOSSUS), in\n"
    "// assets/sprites/colossus/ (the General's frame letters: design doc section\n"
    "// 4), drawn at full size: no Scale, no tint. Rotation 1 aims and fires the\n"
    "// torch at the player (E1, F1).\n")
TEXT_FIXES = (   # comments that describe the provisional look
    ("// BESTIARY section 12 (row 10). In the mod since D116 (2026-10-22), on a\n// provisional sprite; placed in no map yet",
     "// BESTIARY section 12 (row 10). In the mod since D116 (2026-10-22), on his\n// own sprite since D119; placed in no map yet"),
    ("// the foot goes up (placeholder: the General's raised fist)", "// the foot goes up"),
)


def installed_actor(text: str, old: str = "SDGN", new: str = "SDLC") -> str:
    """liberty_colossus.zs once SDLC is installed: the header's documented swap
    (MOD-SPEC 6.12: the sprite renamed at the start of each state line, every
    PROVISIONAL-D116 code line deleted), the comment lines right above a deleted
    line (the tint's explanation), the provisional header paragraph replaced by
    what he wears and the comments that name the placeholder updated."""
    i0 = text.index(PROVISIONAL_HEADER_START)
    i1 = text.index(PROVISIONAL_HEADER_END, i0) + len(PROVISIONAL_HEADER_END)
    text = text[:i0] + INSTALLED_HEADER + text[i1:]
    for a, b in TEXT_FIXES:
        if text.count(a) != 1:
            raise ValueError(f"installed_actor: liberty_colossus.zs changed ({a[:40]!r}...)")
        text = text.replace(a, b)
    out: list[str] = []
    for line in text.splitlines():
        st = line.strip()
        if "PROVISIONAL-D116" in line and st and not st.startswith("/"):
            while out and out[-1].strip().startswith("//") and out[-1].startswith("\t"):
                out.pop()
            continue
        out.append(re.sub(rf"^(\s*){old} ", rf"\g<1>{new} ", line))
    return "\n".join(out) + "\n"


def install_patch(spec, actor: Path = ACTOR, out_root: Path = ge.OUT_ROOT) -> list[Path]:
    """In work/art/enemies_gemini/colossus/: liberty_colossus.zs.patch (git apply)
    and install.sh (copies the lumps, applies it). Writes nothing outside work/."""
    d = out_root / spec.name
    ge.guard_out(d)
    have = sorted(p.stem.upper() for p in d.glob(f"{spec.sprite}*.png"))
    if have != ge.lump_names(spec):
        raise SystemExit(f"colossus_gemini: build {spec.name} first (its lumps differ from the spec)")
    text = actor.read_text(encoding="utf-8")
    rel = actor.relative_to(ROOT).as_posix()
    diff = difflib.unified_diff(text.splitlines(keepends=True), installed_actor(text).splitlines(keepends=True),
                                f"a/{rel}", f"b/{rel}")
    patch = d / "liberty_colossus.zs.patch"
    patch.write_text("".join(diff), encoding="utf-8", newline="\n")
    sh = d / "install.sh"
    sh.write_text(
        "#!/usr/bin/env bash\n"
        "# D119: install the Liberty Colossus's SDLC set ONLY after the CEO's OK on\n"
        f"# {SHEET_HTML.relative_to(ROOT).as_posix()}. Run from the repo root.\n"
        "# Also at install, by hand: the licence rows in docs/art/LICENSES.md (as the\n"
        "# General's section, sources gem_colossus_*.png, processed by\n"
        "# tools/art/colossus_gemini.py), drop SD_LibertyColossus from SWAPS in\n"
        "# tests/test_ep2_enemies.py (its provisional test is red once SDLC exists,\n"
        "# by design), MOD-SPEC 6.12's table row and the design doc's 'Scale\n"
        "# (provisional)' row (2026-10-22_P4_ep2-enemies.md section 3).\n"
        "set -euo pipefail\n"
        f"mkdir -p assets/sprites/{spec.folder}\n"
        f"cp work/art/enemies_gemini/{spec.name}/{spec.sprite}*.png assets/sprites/{spec.folder}/\n"
        f"git apply work/art/enemies_gemini/{spec.name}/liberty_colossus.zs.patch\n"
        f"echo \"installed {len(have)} lumps in assets/sprites/{spec.folder}/ and patched {rel}\"\n",
        encoding="utf-8", newline="\n")
    return [patch, sh]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("split", "build", "sheet", "all"))
    args = ap.parse_args(argv)
    spec = ge.PENDING["colossus"]
    if args.what in ("split", "build", "all"):
        for p in split():
            print(f"colossus_gemini: wrote {p.relative_to(ROOT).as_posix()}")
    if args.what in ("build", "all"):
        m = ge.build(spec, symbol="none")
        print(f"colossus_gemini: {m['lumps']} lumps -> work/art/enemies_gemini/{spec.name}/ "
              f"(base scale {m['base_scale']}), {len(m['gate'])} gate notes")
    if args.what in ("sheet", "all"):
        print(f"colossus_gemini: wrote {colossus_sheet(spec).relative_to(ROOT).as_posix()}")
        for f in install_patch(spec):
            print(f"colossus_gemini: wrote {f.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
