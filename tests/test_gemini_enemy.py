"""tools/art/gemini_enemy.py: the enemy pipeline on small synthetic sheets.

Needs no Gemini sheet (they are gitignored, work/art/reference/enemies/gemini/,
D77): every image here is drawn in the test. Covers the background estimate
(pale pink, dark magenta, figures touching the border), the key and its halo
cleanup, the figure segmentation (a stray piece dropped, a near piece kept,
two figures merged by a flash cut apart), the armband blanking, the facing
normalisation, the helmet scale, palette-only hard-alpha output with a
neutral outline, the placement (feet on the floor line, one canvas per
frame), the lump names against the shipped set and the states, an
end-to-end build of a tiny spec, the overlay and the review sheet, and that
nothing is ever written under assets/, src/ or dist/. D105 (the Legion
trooper and the hybrid stormtrooper): the armband side marker that keeps a
body part on its side, the derived sole under boots cut by the sheet's
edge, the `box` and `none` armband modes, the quality gate, a per-enemy
in-game height, and the two new specs against the shipped sets and their
classes. GeneratedSetTests reads the real builds in work/ (skips without
them; art tier). D105 batch 2 (hound, doughboy, Panzermensch and Schwer,
General): the 2 x 4 grid sheet and its view pick, the painted ground shadow,
mirror-pair lump names, a floating head's sink, the glow / ember erase, the
projectile dropped, a bridged pair cut at a fixed column with the flash
given to its owner, the lettered armband turned into a plain field (and a
glove, a flag, a glint left alone), the hand-named field, the black plate,
the death sheet drawn smaller, and the five new specs against the shipped
sets and their classes. D108 (the mix): which enemies carry the symbol (the
General's flag left alone), the close pictures (profiles and corpses), the
symbol drawn after the mirror and before the black plate, the cache read
(missing, then a repaint), the per-lump report of a build and the control sheet.
D119 (the Legion gunner, pending the CEO): a merged pair cut along a path, the
guided split of a sheet painted over another (the flash to its owner, the
neighbour healed from the guide, the registration), the spec against the
actor, the install patch as the documented swap, and the frontal shot in F1.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The rig-drawn sets the Gemini ones replaced (D109): history, gitignored renders.
RIG_RENDERS = {
    "rifleman": ROOT / "work" / "art" / "enemies" / "rig",
    "legion": ROOT / "work" / "art" / "enemies" / "legion" / "full_C",
    "storm": ROOT / "work" / "art" / "enemies" / "storm" / "full_E",
    "hound": ROOT / "work" / "art" / "enemies" / "hound_gsd" / "full_A",
    "doughboy": ROOT / "work" / "art" / "enemies" / "heavy" / "full" / "SDDB",
    "panzer": ROOT / "work" / "art" / "enemies" / "heavy" / "full" / "SDPM",
    "general": ROOT / "work" / "art" / "general" / "full" / "SDGN",
}
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    from PIL import Image
    import gemini_enemy as ge
except ImportError:  # pragma: no cover - the art venv is missing
    ge = None

PINK = (252, 196, 252)
DARK_MAGENTA = (184, 64, 138)
MAGENTA = (252, 4, 250)
OLIVE = (98, 96, 58)
DARK = (30, 28, 20)
WOOD = (120, 70, 30)
RED = (190, 30, 28)
WHITE = (236, 232, 222)


def person(h: int = 60, facing: str = "left", rifle: bool = True, band: bool = True,
           symbol: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """(rgb, mask) of a crude standing figure, `h` px tall: helmet, coat,
    legs, a levelled rifle reaching far to the facing side, an armband."""
    w = h
    rgb = np.zeros((h, w, 3), np.uint8)
    m = np.zeros((h, w), bool)
    cx = w // 2

    def fill(y0, y1, x0, x1, col):
        rgb[y0:y1, x0:x1] = col
        m[y0:y1, x0:x1] = True
    fill(0, h // 8, cx - h // 10, cx + h // 10, DARK)              # helmet
    fill(h // 8, h * 3 // 4, cx - h // 7, cx + h // 7, OLIVE)       # coat
    fill(h * 3 // 4, h, cx - h // 8, cx - 1, DARK)                  # legs
    fill(h * 3 // 4, h, cx + 1, cx + h // 8, DARK)
    if rifle:
        y = h // 3
        if facing == "left":
            fill(y, y + 2, 1, cx, WOOD)
        else:
            fill(y, y + 2, cx, w - 1, WOOD)
    if band:
        by, bx = h // 4, cx + h // 7 - 6
        fill(by, by + 8, bx, bx + 6, RED)
        fill(by + 2, by + 6, bx + 1, bx + 5, WHITE)
        if symbol:
            rgb[by + 3:by + 5, bx + 2:bx + 4] = (10, 10, 10)
    return rgb, m


def _png(p) -> np.ndarray:
    with Image.open(p) as im:
        return np.asarray(im.convert("RGBA"))


def _size(p) -> tuple[int, int]:
    with Image.open(p) as im:
        return im.size


def _near(mask, r):
    for _ in range(r):
        mask = mask | ge.neighbours8(mask)
    return mask


def sheet(figs, bg=MAGENTA, gap: int = 30, pad: int = 6, halo: bool = True) -> np.ndarray:
    """Figures side by side on `bg`, bottoms on the image's last row (as Gemini's feet)."""
    h = max(f[0].shape[0] for f in figs) + pad
    w = sum(f[0].shape[1] for f in figs) + gap * (len(figs) + 1)
    img = np.empty((h, w, 3), np.uint8)
    img[:] = bg
    x = gap
    for rgb, m in figs:
        fh, fw = m.shape
        sub = img[h - fh:h, x:x + fw]
        sub[m] = rgb[m]
        if halo:   # a blended rim, half figure half background
            rim = ge.neighbours8(m) & ~m
            blend = ((np.array(bg, float) + np.array(OLIVE, float)) / 2).astype(np.uint8)
            sub[rim] = blend
        x += fw + gap
    return img


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class KeyTests(unittest.TestCase):
    def test_background_estimated_per_image(self):
        for bg in (PINK, DARK_MAGENTA, MAGENTA):
            img = sheet([person()], bg=bg)
            est = ge.estimate_background(img)
            self.assertLess(np.abs(est - np.array(bg)).max(), 3, bg)

    def test_noisy_background_and_halo_are_keyed_out(self):
        rng = np.random.default_rng(1)
        rgb, m = person()
        img = sheet([(rgb, m)], bg=DARK_MAGENTA).astype(np.int32)
        img = np.clip(img + rng.integers(-8, 9, img.shape), 0, 255).astype(np.uint8)
        fg = ge.key_background(img)
        lab, n = ge.label(fg)
        self.assertEqual(n, 1)
        # no halo: nothing outside the figure's own pixels survives
        self.assertLessEqual(fg.sum(), m.sum())
        self.assertGreaterEqual(fg.sum(), m.sum() * 0.85)


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class SegmentTests(unittest.TestCase):
    def test_label_is_eight_connected(self):
        m = np.zeros((5, 5), bool)
        m[0, 0] = m[1, 1] = m[3, 3] = True
        lab, n = ge.label(m)
        self.assertEqual(n, 2)
        self.assertEqual(lab[0, 0], lab[1, 1])

    def test_figures_drop_far_stray_and_keep_near_piece(self):
        img = sheet([person(), person(), person()], halo=False)
        h = img.shape[0]
        img[2:10, 120:130] = DARK          # a stray helmet far from every figure (between 2 and 3? far above)
        fg = ge.key_background(img)
        # a near piece: a flash 3 px off the first figure's muzzle
        img2 = img.copy()
        img2[25:28, 24:27] = (255, 220, 120)
        fg2 = ge.key_background(img2)
        figs = ge.figures(fg2, 3)
        self.assertEqual(len(figs), 3)
        self.assertTrue(figs[0][26, 25], "the flash near figure 1 joins it")
        self.assertFalse(any(f[5, 125] for f in figs), "the stray piece is dropped")
        self.assertTrue(all(f.any() for f in figs))
        self.assertLess(h, 100)
        self.assertEqual(len(ge.figures(fg, 3)), 3)

    def test_merged_pair_is_cut_apart(self):
        a, b = person(), person(facing="right")
        img = sheet([a, b], gap=10, halo=False)
        img[20:23, 40:100] = (255, 220, 120)   # two flashes touching: one bridge
        figs = ge.figures(ge.key_background(img), 2)
        self.assertEqual(len(figs), 2)
        x0 = [np.flatnonzero(f.any(axis=0))[0] for f in figs]
        self.assertLess(x0[0], x0[1])
        self.assertFalse((figs[0] & figs[1]).any())

    def test_letters_far_below_are_dropped(self):
        img = sheet([person(80)], gap=40, halo=False)
        img[-12:-2, 3:9] = (255, 255, 255)     # an "A" label at the bottom-left corner
        figs = ge.figures(ge.key_background(img), 1)
        self.assertFalse(figs[0][-5, 5])


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class ArmbandTests(unittest.TestCase):
    def test_symbol_inside_the_field_is_blanked(self):
        rgb, m = person(symbol=True)
        out, painted = ge.blank_armband(rgb, m)
        self.assertGreater(painted, 0)
        fields = ge.armband_fields(out, m)
        self.assertEqual(len(fields), 1)
        y0, x0, y1, x1 = fields[0]
        self.assertTrue(ge.white_mask(out[y0:y1, x0:x1]).all())

    def test_plain_field_is_left_alone(self):
        rgb, m = person(symbol=False)
        out, painted = ge.blank_armband(rgb, m)
        self.assertEqual(painted, 0)
        self.assertTrue((out == rgb).all())

    def test_no_band_no_field(self):
        rgb, m = person(band=False)
        self.assertEqual(ge.armband_fields(rgb, m), [])

    def test_badge_is_the_rig_symbol(self):
        """The badge is the 5x5 symbol the rig rifleman wore (gen_rig.py's
        stamp). Since D109 that set is history (its renders stay in
        work/art/enemies/rig/); the shipped one wears D108's warped symbol."""
        p = ROOT / "work" / "art" / "enemies" / "rig" / "SDRRA1.png"
        if not p.is_file():
            self.skipTest("the rig rifleman's render is not here (work/ is gitignored)")
        a = _png(p).astype(int)
        white = (a[..., 3] > 0) & (a[..., :3].min(axis=-1) > 170)
        red = (a[..., 3] > 0) & (a[..., 0] > 120) & (a[..., 1] < 90) & _near(white, 4)
        ys, xs = np.nonzero(red)                 # the badge's red frame; the field is inside it
        field = a[ys.min() + 1:ys.min() + 6, xs.min() + 1:xs.min() + 6]
        got = tuple("".join("W" if p[:3].min() > 170 else "K" for p in row) for row in field)
        self.assertEqual(got, ge.SYMBOL)

    def test_stamp_never_flips_the_symbol(self):
        pal = ge.palette_rgb()
        rgb, m = person(40)
        idx = ge.downscale(rgb, m, 1.0, 1.0, pal)
        for q in (0, 1):
            out = ge.stamp_badge(idx, pal, 7, q)
            diff = np.argwhere(out != idx)
            self.assertTrue(len(diff))
            y0, x0 = diff.min(axis=0)
            patch = out[y0:y0 + 7, x0:x0 + 7]
            black = int(ge.snap(np.array([[[0, 0, 0]]]), pal)[0, 0])
            k = (patch[1:-1, 1:-1] == black)
            want = np.array([[c == "K" for c in row] for row in ge.SYMBOL])
            self.assertTrue((k == np.rot90(want, -q)).all())
            self.assertFalse((k == np.fliplr(np.rot90(want, -q))).all())


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class FacingTests(unittest.TestCase):
    def test_detect_facing_by_the_rifle(self):
        self.assertEqual(ge.detect_facing(person(facing="left")[1]), "left")
        self.assertEqual(ge.detect_facing(person(facing="right")[1]), "right")
        self.assertIsNone(ge.detect_facing(person(rifle=False, band=False)[1]))

    def test_right_facing_side_view_is_mirrored(self):
        rgb, m = person(facing="right")
        r2, m2, mir = ge.normalise(rgb, m, "right")
        self.assertTrue(mir)
        self.assertEqual(ge.detect_facing(m2), "left")
        r3, m3, mir3 = ge.normalise(rgb, m, "left")
        self.assertFalse(mir3)
        self.assertTrue((m3 == m).all())

    def test_auto_facing_on_a_sheet(self):
        figs = [person(facing="left", rifle=False), person(facing="right"), person(facing="right"),
                person(facing="left"), person(facing="left", rifle=False)]
        sc = ge.cut_sheet(sheet(figs, halo=False), ge.Sheet("x.png", 5, ge.SIDES_AUTO))
        self.assertEqual([f.facing for f in sc.figs], ["front", "right", "right", "left", "back"])
        self.assertEqual([f.mirrored for f in sc.figs], [False, True, True, False, False])
        self.assertTrue(all(ge.detect_facing(f.mask) == "left" for f in sc.figs[1:4]))

    def test_ambiguous_auto_facing_refuses(self):
        rgb, m = person(rifle=False, band=False)
        with self.assertRaises(ValueError):
            ge.facing_of(ge.Sheet("x.png", 5, ge.SIDES_AUTO), 1, m)

    def test_rotation_map(self):
        self.assertEqual(sorted(ge.VIEW_OF_ROT), list(range(1, 9)))
        for r in ge.MIRRORED_ROTS:
            self.assertEqual(ge.VIEW_OF_ROT[r], ge.VIEW_OF_ROT[10 - r])


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class PixelTests(unittest.TestCase):
    def test_helmet_width(self):
        rgb, m = person(80)
        self.assertEqual(ge.helmet_width(m, 6), 2 * (80 // 10))

    def test_downscale_palette_and_hard_alpha(self):
        pal = ge.palette_rgb()
        rgb, m = person(80)
        idx = ge.downscale(rgb, m, 0.5 * ge.PIXEL_ASPECT, 0.5, pal)
        self.assertEqual(idx.shape[0], 40)
        self.assertEqual(idx.shape[1], round(80 * 0.5 * ge.PIXEL_ASPECT))
        self.assertTrue(((idx == ge.TRANSPARENT) | ((idx >= 0) & (idx < len(pal)))).all())
        rgba = ge.to_rgba(idx, pal)
        self.assertEqual(set(np.unique(rgba[..., 3])), {0, 255})

    def test_outline_is_neutral_dark(self):
        pal = ge.palette_rgb()
        idx = np.full((12, 12), ge.TRANSPARENT, np.int32)
        olive = int(ge.snap(np.array([[OLIVE]]), pal)[0, 0])
        pink = int(ge.snap(np.array([[(200, 90, 160)]]), pal)[0, 0])
        idx[2:10, 2:10] = olive
        idx[2, 2:10] = pink                 # a pink rim the key left
        out = ge.outline(idx, pal)
        rim = out[2, 4]
        self.assertLess(pal[rim].max(), pal[olive].max())
        r, g, b = pal[rim]
        self.assertLessEqual(min(r, b) - g, 10, "no magenta-ish outline")

    def test_tilt_keeps_feet_and_leans(self):
        rgb, m = person(60, rifle=False, band=False)
        r2, m2 = ge.tilt(rgb, m, 10)
        self.assertEqual(m2.shape[0] >= 58, True)
        top = np.flatnonzero(m2[0])
        self.assertGreater(top.mean(), ge.body_axis(m2))

    def test_blood_only_adds_blood(self):
        pal = ge.palette_rgb()
        rgb, m = person(60)
        idx = ge.downscale(rgb, m, 1, 1, pal)
        blood = {int(ge.snap(np.array([[c]]), pal)[0, 0]) for c in ge.BLOOD_RGB}
        for level in range(1, 7):
            out = ge.add_blood(idx, level, pal, seed=3)
            changed = out != idx
            self.assertTrue(changed.any())
            self.assertTrue(set(np.unique(out[changed])) <= blood)
            self.assertTrue((ge.add_blood(idx, level, pal, seed=3) == out).all(), "deterministic")
        self.assertTrue((ge.add_blood(idx, 0, pal, 3) == idx).all())


def banded(cross: bool = True, h: int = 80) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """A figure whose armband is a red band with a WHITE cross on it (the
    hybrid's), returned with the cross' box."""
    rgb, m = person(h, band=False)
    cx = h // 2
    by, bx = h // 4, cx + h // 7 - 10
    rgb[by:by + 12, bx:bx + 10] = RED
    m[by:by + 12, bx:bx + 10] = True
    box = (by + 3, bx + 2, by + 9, bx + 8)
    if cross:
        rgb[by + 3:by + 9, bx + 4:bx + 6] = WHITE
        rgb[by + 5:by + 7, bx + 2:bx + 8] = WHITE
    return rgb, m, box


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D105ArmbandTests(unittest.TestCase):
    def test_box_mode_turns_a_white_cross_into_a_plain_field(self):
        rgb, m, (y0, x0, y1, x1) = banded()
        out, painted = ge.blank_armband(rgb, m, "box")
        self.assertGreater(painted, 0)
        self.assertTrue(ge.white_mask(out[y0:y1, x0:x1]).all())
        self.assertTrue((out[:y0 - 1] == rgb[:y0 - 1]).all())         # nothing above the band moved

    def test_blank_mode_leaves_a_cross_on_red(self):
        rgb, m, _ = banded()
        out, painted = ge.blank_armband(rgb, m, "blank")
        self.assertEqual(painted, 0)
        self.assertTrue((out == rgb).all())

    def test_none_mode_leaves_everything(self):
        rgb, m = person(symbol=True)
        out, painted = ge.blank_armband(rgb, m, "none")
        self.assertEqual(painted, 0)
        self.assertTrue((out == rgb).all())

    def test_box_mode_spares_a_highlight_that_only_touches_the_band(self):
        rgb, m, _ = banded(cross=False)
        cx = 40
        by, bx = 20, cx + 80 // 7 - 10
        grey = np.array([[(170, 170, 176) if (i + j) % 3 == 0 else (90, 92, 100) for i in range(8)] for j in range(8)],
                        np.uint8)      # gun metal: pale highlights among mid greys
        rgb[by + 12:by + 20, bx:bx + 8] = grey
        m[by + 12:by + 20, bx:bx + 8] = True
        out, painted = ge.blank_armband(rgb, m, "box")
        self.assertEqual(painted, 0)
        self.assertLess(ge.field_purity(rgb, m, (by + 12, bx, by + 20, bx + 8)), ge.BOX_PURITY)

    def test_box_mode_refuses_a_field_too_big_for_an_armband(self):
        rgb, m, _ = banded(cross=False)
        h = ge.FIELD_BOX_MAX + 6
        rgb[2:2 + h, 2:2 + h] = WHITE        # a glowing ball touching the red
        m[2:2 + h, 2:2 + h] = True
        rgb[2 + h:4 + h, 2:2 + h] = RED
        m[2 + h:4 + h, 2:2 + h] = True
        out, _ = ge.blank_armband(rgb, m, "box")
        self.assertTrue((out[2:2 + h, 2:2 + h] == rgb[2:2 + h, 2:2 + h]).all())


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D105SideAndSoleTests(unittest.TestCase):
    def test_marker_side_reads_the_band(self):
        rgb, m = person(rifle=False)
        self.assertEqual(ge.marker_side(rgb, m), "right")
        self.assertEqual(ge.marker_side(rgb[:, ::-1], m[:, ::-1]), "left")
        rgb2, m2 = person(rifle=False, band=False)
        self.assertIsNone(ge.marker_side(rgb2, m2))

    def test_a_front_view_drawn_mirrored_is_put_back(self):
        good = person(80, rifle=False)
        flipped = (good[0][:, ::-1].copy(), good[1][:, ::-1].copy())
        img = sheet([good, person(80), person(80), person(80), flipped], halo=False)
        sh = ge.Sheet("x.png", 5, ("front", "left", "left", "left", "front"))
        sc = ge.cut_sheet(img, sh, "blank", armband_side="right")
        self.assertEqual([f.mirrored for f in sc.figs], [False, False, False, False, True])
        self.assertEqual(sc.figs[4].marker, "left")                  # read before the fix
        self.assertEqual(ge.marker_side(sc.figs[4].rgb, sc.figs[4].mask), "right")
        sc2 = ge.cut_sheet(img, sh, "blank")                          # no rule: nothing mirrored
        self.assertEqual([f.mirrored for f in sc2.figs], [False] * 5)

    def test_back_view_expects_the_other_side(self):
        rgb, m = person(80, rifle=False)
        img = sheet([(rgb[:, ::-1].copy(), m[:, ::-1].copy())], halo=False)
        sc = ge.cut_sheet(img, ge.Sheet("x.png", 1, ("back",)), "blank", armband_side="right")
        self.assertFalse(sc.figs[0].mirrored)

    def test_sole_under_feet_cut_by_the_edge(self):
        img = sheet([person(80)], pad=0, halo=False)                   # feet on the last row
        self.assertIn("bottom", ge.touched_edges(ge.key_background(img)))
        sc = ge.cut_sheet(img, ge.Sheet("x.png", 1, (), sole=4))
        f = sc.figs[0]
        self.assertEqual(f.sole, 4)
        self.assertEqual(f.mask.shape[0], 84)
        self.assertTrue((f.mask[-4:] == f.mask[-5]).all())
        self.assertTrue((f.rgb[-4:][f.mask[-4:]] == ge.SOLE_RGB).all())
        roomy_img = np.concatenate([img, np.full((6, img.shape[1], 3), MAGENTA, np.uint8)])
        roomy = ge.cut_sheet(roomy_img, ge.Sheet("x.png", 1, (), sole=4))
        self.assertEqual(roomy.figs[0].sole, 0)                         # not cut: nothing added
        self.assertEqual(roomy.figs[0].mask.shape[0], 80)

    def test_quality_gate_names_cut_art_and_sole(self):
        img = sheet([person(80), person(80)], pad=0, halo=False)
        cuts = {"a": ge.cut_sheet(img, ge.Sheet("a.png", 2, ())),
                "b": ge.cut_sheet(img, ge.Sheet("b.png", 2, (), sole=3))}
        spec = ge.EnemySpec(name="g", sprite="SDGG", folder="g",
                            sheets={"a": ge.Sheet("a.png", 2, ()), "b": ge.Sheet("b.png", 2, (), sole=3)},
                            rotated={}, single={"A": ge.Src("a", 0)})
        gate = ge.quality_gate(spec, cuts, ["SDGGA0"])
        self.assertEqual(sum("a.png" in g and "cortado" in g for g in gate), 2)
        self.assertEqual(sum("b.png" in g and "suela derivada (3 px)" in g for g in gate), 2)
        self.assertIn("los lumps escritos no son el conjunto de la spec", ge.quality_gate(spec, cuts, ["SDGGB0"]))


def _state_letters(zs: Path, sprite: str) -> set:
    letters = set()
    for m in re.finditer(rf"^\s*{sprite}\s+([A-Z]+)\s", zs.read_text(encoding="utf-8"), re.M):
        letters |= set(m.group(1))
    return letters


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D105SpecTests(unittest.TestCase):
    CASES = (("LEGION", "legion_trooper.zs", 70, "G"), ("STORM", "stormtrooper.zs", 77, "H"))

    def test_names_are_the_shipped_sets(self):
        for attr, _, count, last_rot in self.CASES:
            spec = getattr(ge, attr)
            names = ge.lump_names(spec)
            self.assertEqual(len(names), count, attr)
            for n in names:
                self.assertRegex(n, rf"^{spec.sprite}[A-U][0-8]$")
                self.assertEqual(n[5] == "0", n[4] > last_rot, n)
            shipped = ge.current_names(spec)
            if shipped:
                self.assertEqual(names, shipped, attr)

    def test_every_state_letter_is_drawn(self):
        for attr, zs_name, _, _ in self.CASES:
            spec = getattr(ge, attr)
            zs = ROOT / "src" / "zscript" / "monsters" / zs_name
            if not zs.is_file():
                self.skipTest(f"{zs_name} not present")
            drawn = set(spec.rotated) | set(spec.single)
            self.assertEqual(_state_letters(zs, spec.sprite), drawn, attr)
            self.assertFalse(set(spec.rotated) & set(spec.single), attr)

    def test_sources_exist_on_their_sheets(self):
        for attr, _, _, _ in self.CASES:
            spec = getattr(ge, attr)
            for letter, rot in spec.rotated.items():
                self.assertIn(rot.sheet, spec.sheets, letter)
                self.assertGreaterEqual(spec.sheets[rot.sheet].count, 5, letter)
                for _, src in rot.override:
                    self.assertLess(src.view, spec.sheets[src.sheet].count, letter)
            for letter, src in spec.single.items():
                self.assertLess(src.view, spec.sheets[src.sheet].count, letter)

    def test_d105_rules_in_the_specs(self):
        self.assertEqual(ge.LEGION.armband, "none")          # the US flag is not an armband
        self.assertEqual(ge.STORM.armband, "box")            # the white cross goes to a plain field
        self.assertEqual(ge.RIFLEMAN.armband, "blank")
        self.assertEqual(ge.STORM.armband_side, "right")
        self.assertTrue(all(s.sole for s in ge.STORM.sheets.values()))
        self.assertEqual((ge.LEGION.target_height, ge.STORM.target_height, ge.RIFLEMAN.target_height),
                         (ge.LEGION_HEIGHT, ge.STORM_HEIGHT, ge.TARGET_HEIGHT))
        for spec in (ge.LEGION, ge.STORM):
            self.assertTrue(spec.reask)
            for f, prompt in spec.reask:
                self.assertTrue(f.startswith("gem_") and prompt, f)
        self.assertEqual(set(ge.ENEMIES), {"rifleman", "legion", "storm", "hound", "doughboy", "panzer",
                                           "panzer_heavy", "general"})

    def test_shipped_heights_are_the_targets(self):
        """The targets are the rig sets' frame A1 heights (D105: as tall in
        game as the set replaced); since D109 the shipped set is the Gemini
        one, whose standing view (frame B, rotation 1) is that tall."""
        for spec in (ge.RIFLEMAN, ge.LEGION, ge.STORM):
            p = ROOT / "assets" / "sprites" / spec.folder / f"{spec.sprite}B1.png"
            if not p.is_file():
                self.skipTest("shipped sprites not present")
            a = _png(p)[..., 3] > 0
            ys = np.flatnonzero(a.any(axis=1))
            self.assertEqual(ys[-1] - ys[0] + 1, spec.target_height, spec.name)
            old = RIG_RENDERS[spec.name] / f"{spec.sprite}A1.png"
            if old.is_file():
                a = _png(old)[..., 3] > 0
                ys = np.flatnonzero(a.any(axis=1))
                self.assertEqual(ys[-1] - ys[0] + 1, spec.target_height, f"{spec.name} (rig)")


PINKF = (210, 120, 118)    # the doughboy's flesh
BLUE = (60, 120, 250)
YELLOW = (255, 210, 60)
GREY = (170, 170, 172)


def blob(h, w, col):
    rgb = np.zeros((h, w, 3), np.uint8)
    rgb[:] = col
    return rgb, np.ones((h, w), bool)


def grid_sheet(rows_of_figs, bg=MAGENTA, cell=(90, 70)) -> np.ndarray:
    """Figures in a grid of cells, feet near each cell's last row."""
    ch, cw = cell
    img = np.empty((ch * len(rows_of_figs), cw * max(len(r) for r in rows_of_figs), 3), np.uint8)
    img[:] = bg
    for r, row in enumerate(rows_of_figs):
        for c, (rgb, m) in enumerate(row):
            fh, fw = m.shape
            y, x = ch * (r + 1) - fh - 4, cw * c + (cw - fw) // 2
            img[y:y + fh, x:x + fw][m] = rgb[m]
    return img


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class Batch2PixelTests(unittest.TestCase):
    def test_grid_order_is_row_by_row(self):
        figs = [[person(40 + 2 * i) for i in range(4)], [person(60 - 2 * i) for i in range(4)]]
        img = grid_sheet(figs)
        fg = ge.key_background(img)
        ms = ge.grid_order(ge.figures(fg, 8), 2, img.shape[0])
        heights = [int(np.ptp(np.flatnonzero(m.any(axis=1)))) + 1 for m in ms]
        self.assertEqual(heights, [40, 42, 44, 46, 60, 58, 56, 54])
        sheet_spec = ge.Sheet("x", 8, ge.STAND, None, rows=2, pick=(0, 1, 2, 6, 3))
        sc = ge.cut_sheet(img, sheet_spec, "none")
        self.assertEqual([f.mask.shape[0] for f in sc.figs], [40, 42, 44, 56, 46])

    def test_painted_shadow_is_keyed_out(self):
        rgb, m = person(50, band=False)
        clean = sheet([(rgb, m)], pad=8, halo=False)
        img = clean.copy()
        under = np.zeros(img.shape[:2], bool)
        under[-6:, 10:80] = True
        under &= (img == MAGENTA).all(axis=-1)
        img[under] = (120, 4, 118)                            # a darker magenta ellipse round the feet
        self.assertTrue(ge.shadow_mask(img)[under].all())
        self.assertFalse(ge.shadow_mask(np.array([[PINKF, RED, OLIVE, DARK]], np.uint8)).any())
        want = ge.cut_sheet(clean, ge.Sheet("x", 1, ("front",), None), "none").figs[0].mask.shape
        plain = ge.cut_sheet(img, ge.Sheet("x", 1, ("front",), None), "none").figs[0]
        keyed = ge.cut_sheet(img, ge.Sheet("x", 1, ("front",), None, shadow=True), "none").figs[0]
        self.assertGreater(plain.mask.shape[1], keyed.mask.shape[1])
        self.assertEqual(keyed.mask.shape, want)

    def test_erase_glow_keeps_the_head(self):
        rgb, m = blob(40, 40, PINKF)
        rgb[10:30, 32:40] = BLUE                             # a glow painted on the back of the head
        rgb[2:4, 2:4] = WHITE                                # the eye's white, outside the box
        out = ge.erase_glow(rgb, m, (0.7, 0.0, 1.0, 1.0))
        self.assertFalse(out[10:30, 32:40].any())
        self.assertTrue(out[2:4, 2:4].all())
        self.assertEqual(int(out.sum()), 40 * 40 - 20 * 8)
        rgb2, m2 = blob(40, 40, OLIVE)
        rgb2[0:8, 30:40] = YELLOW                            # an ember stuck to the fist
        self.assertFalse(ge.erase_glow(rgb2, m2, (0.7, 0.0, 1.0, 0.3), "fire")[0:8, 30:40].any())
        self.assertTrue(ge.erase_glow(rgb2, m2, (0.7, 0.0, 1.0, 0.3), "glow")[0:8, 30:40].all())
        self.assertFalse(ge.erase_glow(rgb2, m2, (0.0, 0.0, 0.5, 0.5), "all")[0:20, 0:20].any())

    def test_core_keeps_the_biggest_piece(self):
        m = np.zeros((30, 60), bool)
        m[5:25, 5:25] = True
        m[10:14, 40:46] = True                               # the projectile in flight
        self.assertEqual(int(ge.largest(m).sum()), 400)

    def test_bridged_pair_cut_with_the_flash_to_its_owner(self):
        rgb = np.zeros((40, 100, 3), np.uint8)
        m = np.zeros((40, 100), bool)
        rgb[:, 5:35], m[:, 5:35] = OLIVE, True               # the left figure
        rgb[:, 60:95], m[:, 60:95] = OLIVE, True             # the right figure
        rgb[8:14, 35:70], m[8:14, 35:70] = YELLOW, True      # its flash, over the right one's face
        left, right = ge.split_merged(m, ((50, "fire"),), rgb)
        self.assertTrue(left[8:14, 35:70].all())
        self.assertFalse(right[8:14, 60:70].any())
        self.assertTrue(right[20:, 60:95].all())
        plain_l, _ = ge.split_merged(m, ((50, ""),), rgb)
        self.assertFalse(plain_l[:, 50:].any())
        rgb[8:14, 35:70] = GREY                              # smoke of the right figure, sent right
        left, right = ge.split_merged(m, ((50, "smoke>"),), rgb)
        self.assertTrue(right[8:14, 35:70].all())
        self.assertFalse(left[:, 35:].any())

    def test_fixed_cut_waits_for_its_piece(self):
        img = np.zeros((40, 300, 3), np.uint8)
        img[:] = MAGENTA
        fg = np.zeros((40, 300), bool)
        for x0, x1 in ((5, 60), (70, 140), (150, 220), (230, 295)):
            img[:, x0:x1], fg[:, x0:x1] = OLIVE, True
        for x0, x1 in ((60, 70), (140, 150), (220, 230)):
            img[10:14, x0:x1], fg[10:14, x0:x1] = YELLOW, True    # every pair bridged
        ms = ge.figures(fg, 4, ((145, "fire"),), img)
        spans = [tuple(int(v) for v in np.flatnonzero(mm[20])[[0, -1]]) for mm in ms]
        self.assertEqual(spans[1], (70, 139))
        self.assertEqual(spans[2], (150, 219))

    def test_lettered_armband_becomes_a_plain_field(self):
        rgb, m = blob(40, 40, OLIVE)
        rgb[10:22, 8:28] = RED
        rgb[13:19, 12:14] = WHITE                            # the «E», white on the red
        rgb[13, 14:18] = rgb[15, 14:17] = rgb[18, 14:18] = WHITE
        rgb[30:36, 30:36] = WHITE                            # a glove, not on the band
        out, n = ge.patch_armband(rgb, m, 20)
        self.assertGreater(n, 0)
        self.assertTrue((out[13:19, 12:18] == ge.PATCH_RGB).all())
        self.assertTrue((out[30:36, 30:36] == WHITE).all())
        self.assertTrue((out[10:12, 8:28] == RED).all())
        flag = rgb.copy()
        flag[11:14, 6:11] = BLUE                              # a canton next to it: a US flag
        self.assertEqual(ge.patch_armband(flag, m, 20)[1], 0)
        glint = rgb.copy()
        glint[13:19, 12:18] = RED
        glint[15:17, 10:24] = WHITE                          # two rows: a glint between the eyes
        self.assertEqual(ge.patch_armband(glint, m, 20)[1], 0)
        self.assertEqual(ge.blank_armband(rgb, m, "patch", 20)[1], n)

    def test_beige_coat_is_not_a_light_mark(self):
        self.assertFalse(ge.light_mask(np.array([[(214, 210, 175)]], np.uint8))[0, 0])
        self.assertTrue(ge.light_mask(np.array([[(199, 147, 140)]], np.uint8))[0, 0])   # the E in shade
        self.assertTrue(ge.light_mask(np.array([[(235, 238, 240)]], np.uint8))[0, 0])   # a cold white

    def test_black_plate_spares_red_white_and_glow(self):
        rgb = np.array([[OLIVE, RED, WHITE, YELLOW]], np.uint8)
        out = ge.darken(rgb, np.ones((1, 4), bool), 0.5)
        self.assertEqual(out[0, 0].tolist(), [49, 48, 29])
        self.assertEqual(out[0, 1:].tolist(), rgb[0, 1:].tolist())
        self.assertIs(ge.darken(rgb, np.ones((1, 4), bool), 1.0), rgb)

    def test_mirror_pair_names(self):
        spec = ge.EnemySpec(name="p", sprite="SDPP", folder="p", sheets={}, rotated={"A": ge.Rotated("turn")},
                            single={"B": ge.Src("death", 0)}, pairs=True, ref_view=2)
        self.assertEqual(ge.lump_names(spec), ["SDPPA1", "SDPPA2A8", "SDPPA3A7", "SDPPA4A6", "SDPPA5", "SDPPB0"])
        self.assertEqual(ge.ref_lump(spec), "SDPPB3B7")
        self.assertEqual(ge.ref_lump(ge.RIFLEMAN), "SDRRB1")


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class Batch2BuildTests(unittest.TestCase):
    """A tiny grid-sheet enemy in mirror pairs, hanging under its origin, with a hand-named field."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sd_gemini_b2_"))
        ref = cls.tmp / "ref"
        ref.mkdir()
        row1 = [person(50, rifle=False), person(50), person(50), person(50, rifle=False)]
        row2 = [person(50, rifle=False), person(52), person(50), person(50, rifle=False)]
        Image.fromarray(grid_sheet([row1, row2])).save(ref / "gem_g_turn.png")
        Image.fromarray(sheet([person(40, symbol=True), person(40)], bg=DARK_MAGENTA)).save(ref / "gem_g_death.png")
        cls.spec = ge.EnemySpec(
            name="grid", sprite="SDGG", folder="grid", pairs=True, feet_sink=14, target_height=30,
            armband="none",
            sheets={"turn": ge.Sheet("gem_g_turn.png", 8, ge.STAND, None, rows=2, pick=(0, 1, 2, 6, 3)),
                    "death": ge.Sheet("gem_g_death.png", 2, (), None, rel_scale=0.8,
                                      patch=((0, (17, 0, 23, 5)),))},
            rotated={"A": ge.Rotated("turn"),
                     "B": ge.Rotated("turn", tilt=6.0, override=((3, ge.Src("death", 1, mirror=True)),))},
            single={"C": ge.Src("death", 0), "D": ge.Src("death", 0, core=True)})
        cls.out = cls.tmp / "out"
        cls.metrics = ge.build(cls.spec, cls.out, ref_dir=ref)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_pairs_written(self):
        names = sorted(p.stem for p in self.out.glob("SDGG*.png"))
        self.assertEqual(names, ge.lump_names(self.spec))
        self.assertIn("SDGGA2A8", names)
        self.assertNotIn("SDGGA8", names)

    def test_floating_sink(self):
        for lump in ("SDGGA1", "SDGGC0"):
            a = _png(self.out / f"{lump}.png")[..., 3]
            self.assertEqual(np.flatnonzero(a.any(axis=1))[-1], ge.read_grab(self.out / f"{lump}.png")[1] + 14)

    def test_hand_named_field_and_rel_scale(self):
        death = self.metrics["sheets"]["death"]
        self.assertEqual(death["figures"][0]["armband_px_blanked"], 30)   # the helmet under the box
        self.assertEqual(death["scale"], 1.25)

    def test_override_mirror_in_a_pair_set(self):
        bad = ge.EnemySpec(**{**self.spec.__dict__,
                              "rotated": {"A": ge.Rotated("turn", override=((7, ge.Src("death", 0)),))}})
        with self.assertRaises(ValueError):
            ge.build(bad, self.tmp / "bad", ref_dir=self.tmp / "ref")

    def test_review_sheet_reads_pairs(self):
        spec = ge.EnemySpec(**{**self.spec.__dict__, "name": "out"})
        html = ge.review_sheet([spec], out=self.tmp / "sheet.html", out_root=self.tmp, sprites_dir=self.tmp / "none")
        text = html.read_text(encoding="utf-8")
        self.assertIn("SDGGA2A8", text)
        self.assertIn("scaleX(-1)", text)


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class Batch2SpecTests(unittest.TestCase):
    CASES = (("HOUND", "reich_hound.zs", 46), ("DOUGHBOY", "doughboy.zs", 54),
             ("PANZER", "panzermensch.zs", 71), ("PANZER_HEAVY", "panzermensch_schwer.zs", 71),
             ("GENERAL", "general.zs", 81))

    def test_names_are_the_shipped_sets(self):
        for attr, _, count in self.CASES:
            spec = getattr(ge, attr)
            names = ge.lump_names(spec)
            self.assertEqual(len(names), count, attr)
            shipped = ge.current_names(spec)
            if shipped:
                self.assertEqual(names, shipped, attr)
        self.assertTrue(ge.HOUND.pairs)
        self.assertFalse(any(getattr(ge, a).pairs for a, _, _ in self.CASES[1:]))

    def test_every_state_letter_is_drawn(self):
        for attr, zs_name, _ in self.CASES:
            spec = getattr(ge, attr)
            zs = ROOT / "src" / "zscript" / "monsters" / zs_name
            if not zs.is_file():
                self.skipTest(f"{zs_name} not present")
            drawn = set(spec.rotated) | set(spec.single)
            self.assertEqual(_state_letters(zs, spec.sprite), drawn, attr)
            self.assertFalse(set(spec.rotated) & set(spec.single), attr)

    def test_sources_exist_on_their_sheets(self):
        for attr, _, _ in self.CASES:
            spec = getattr(ge, attr)
            views = {k: len(s.pick) if s.pick else s.count for k, s in spec.sheets.items()}
            for letter, rot in spec.rotated.items():
                self.assertGreaterEqual(views[rot.sheet], 5, letter)
                for r, src in rot.override:
                    self.assertLess(src.view, views[src.sheet], letter)
                    if spec.pairs:
                        self.assertIn(r, ge.PAIR_ROTS, letter)
            for letter, src in spec.single.items():
                self.assertLess(src.view, views[src.sheet], letter)
            for k, s in spec.sheets.items():
                self.assertTrue(all(i < s.count for i in s.pick), s.file)
                self.assertTrue(all(e[0] < views[k] for e in s.erase), s.file)
                self.assertTrue(all(v < views[k] for v, _ in s.patch), s.file)

    def test_d105_rules(self):
        # no symbol anywhere: every Reich band ends as a plain field, the US flags are left alone
        self.assertEqual((ge.HOUND.armband, ge.DOUGHBOY.armband, ge.GENERAL.armband), ("none", "none", "none"))
        self.assertEqual((ge.PANZER.armband, ge.PANZER_HEAVY.armband), ("patch", "patch"))
        self.assertEqual(len(ge.GENERAL.sheets["death"].patch), 4)
        self.assertIs(ge.PANZER_HEAVY.sheets, ge.PANZER.sheets)          # the Schwer shares the art
        self.assertEqual(ge.PANZER_HEAVY.target_height, round(ge.PANZER_HEIGHT * 1.12))
        self.assertLess(ge.PANZER_HEAVY.shade, 1.0)
        self.assertEqual(ge.DOUGHBOY.feet_sink, ge.DOUGHBOY_SINK)
        self.assertEqual(ge.HOUND.sheets["turn"].pick, ge.HOUND_PICK)
        for attr, _, _ in self.CASES:
            spec = getattr(ge, attr)
            self.assertTrue(spec.reask and spec.derived, attr)
            for f, prompt in spec.reask:
                self.assertTrue(f.startswith("gem_") and prompt, f)

    def test_shipped_heights_are_the_targets(self):
        """As above: the rig sets' frame A at the reference view set the
        targets; the shipped Gemini set's standing view B is that tall."""
        for attr in ("HOUND", "DOUGHBOY", "PANZER", "GENERAL"):
            spec = getattr(ge, attr)
            p = ROOT / "assets" / "sprites" / spec.folder / f"{ge.rot_lump(spec, 'B', spec.ref_view + 1)}.png"
            if not p.is_file():
                self.skipTest("shipped sprites not present")
            a = _png(p)[..., 3] > 0
            ys = np.flatnonzero(a.any(axis=1))
            self.assertEqual(ys[-1] - ys[0] + 1, spec.target_height, attr)
            old = RIG_RENDERS[spec.name] / f"{ge.rot_lump(spec, 'A', spec.ref_view + 1)}.png"
            if old.is_file():
                a = _png(old)[..., 3] > 0
                ys = np.flatnonzero(a.any(axis=1))
                self.assertEqual(ys[-1] - ys[0] + 1, spec.target_height, f"{attr} (rig)")


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class PlaceTests(unittest.TestCase):
    def test_one_canvas_feet_on_floor(self):
        pal = ge.palette_rgb()
        a = ge.downscale(*person(50), 1, 1, pal)
        b = ge.downscale(*person(40, facing="right"), 1, 1, pal)
        canv, (left, top) = ge.place_frame({"XA1": a, "XA2": b})
        shapes = {c.shape for c in canv.values()}
        self.assertEqual(len(shapes), 1)
        h, w = shapes.pop()
        self.assertEqual((h % 8, w % 8), (0, 0))
        self.assertEqual(left, w // 2)
        for c in canv.values():
            last = np.flatnonzero((c >= 0).any(axis=1))[-1]
            self.assertEqual(last, top + ge.FEET_SINK)
            self.assertLessEqual(abs(ge.body_axis(c >= 0) - left), 1.0)


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class NameTests(unittest.TestCase):
    def test_rifleman_names_are_the_shipped_set(self):
        names = ge.lump_names(ge.RIFLEMAN)
        self.assertEqual(len(names), 70)
        for n in names:
            self.assertRegex(n, r"^SDRR[A-U][0-8]$")
            self.assertEqual(n[5] == "0", n[4] >= "H")
        shipped = ge.current_names(ge.RIFLEMAN)
        if shipped:
            self.assertEqual(names, shipped)

    def test_every_state_letter_is_drawn(self):
        zs = ROOT / "src" / "zscript" / "monsters" / "reich_rifleman.zs"
        if not zs.is_file():
            self.skipTest("rifleman class not present")
        letters = set()
        for m in re.finditer(r"^\s*SDRR\s+([A-Z]+)\s", zs.read_text(encoding="utf-8"), re.M):
            letters |= set(m.group(1))
        drawn = set(ge.RIFLEMAN.rotated) | set(ge.RIFLEMAN.single)
        self.assertEqual(letters, drawn)
        self.assertFalse(set(ge.RIFLEMAN.rotated) & set(ge.RIFLEMAN.single))

    def test_rifleman_spec_sheets(self):
        s = ge.RIFLEMAN
        for letter, rot in s.rotated.items():
            self.assertIn(rot.sheet, s.sheets, letter)
            self.assertEqual(s.sheets[rot.sheet].count >= 5, True)
        for letter, src in s.single.items():
            self.assertLess(src.view, 4 if src.sheet == "death" else s.sheets[src.sheet].count, letter)


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class GuardTests(unittest.TestCase):
    def test_refuses_assets_src_dist(self):
        for top in ge.FORBIDDEN_OUT:
            with self.assertRaises(SystemExit):
                ge.guard_out(ROOT / top / "sprites" / "SDRRA1.png")
        ge.guard_out(ROOT / "work" / "art" / "enemies_gemini" / "x.png")

    def test_save_sprite_and_overlay_refuse_assets(self):
        rgba = np.zeros((8, 8, 4), np.uint8)
        with self.assertRaises(SystemExit):
            ge.save_sprite(rgba, (4, 4), ROOT / "assets" / "sprites" / "rifleman" / "SDRRZ9.png")
        self.assertFalse((ROOT / "assets" / "sprites" / "rifleman" / "SDRRZ9.png").exists())
        with self.assertRaises(SystemExit):
            ge.write_overlay({"sprites/X.png": Path(__file__)}, ROOT / "dist" / "x.pk3")

    def test_defaults_point_outside_assets(self):
        for p in (ge.OUT_ROOT, ge.OVERLAY, ge.SHEET_HTML, ge.ARMBAND_PNG):
            ge.guard_out(p)
        self.assertEqual(ge.OVERLAY.name, "sd-draft-enemies.pk3")


TINY = None


def tiny_spec():
    turn = ge.Sheet("gem_t_turn.png", 5, ge.STAND)
    aim = ge.Sheet("gem_t_aim.png", 5, ge.SIDES_AUTO)
    death = ge.Sheet("gem_t_death.png", 2)
    return ge.EnemySpec(
        name="tiny", sprite="SDTY", folder="tiny",
        sheets={"turn": turn, "aim": aim, "death": death},
        rotated={"A": ge.Rotated("turn"), "B": ge.Rotated("aim"),
                 "C": ge.Rotated("turn", tilt=6.0, override=((1, ge.Src("death", 0)),))},
        single={"D": ge.Src("death", 1), "E": ge.Src("death", 1, blood=5)},
        anims=(("walk", (("A", 4), ("B", 4)), True),))


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sd_gemini_enemy_"))
        ref = cls.tmp / "ref"
        ref.mkdir()
        stand = [person(80, rifle=False), person(80), person(80), person(80), person(80, rifle=False)]
        Image.fromarray(sheet(stand, bg=MAGENTA)).save(ref / "gem_t_turn.png")
        aim = [person(80, rifle=False), person(80, facing="right"), person(80, facing="right"),
               person(80), person(80, rifle=False)]
        Image.fromarray(sheet(aim, bg=PINK)).save(ref / "gem_t_aim.png")
        lying_rgb, lying_m = person(80, symbol=True)
        lying = (np.rot90(lying_rgb).copy(), np.rot90(lying_m).copy())
        Image.fromarray(sheet([person(80, symbol=True), lying], bg=DARK_MAGENTA)).save(ref / "gem_t_death.png")
        cls.spec = tiny_spec()
        cls.assets_before = sorted(p.as_posix() for p in (ROOT / "assets").rglob("*")) \
            if (ROOT / "assets").is_dir() else []
        cls.out = cls.tmp / "out"
        cls.metrics = ge.build(cls.spec, cls.out, ref_dir=ref)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_lumps_and_offsets(self):
        names = sorted(p.stem for p in self.out.glob("SDTY*.png"))
        self.assertEqual(names, ge.lump_names(self.spec))
        self.assertEqual(len(names), 3 * 8 + 2)
        for letter in "ABC":
            grabs = {ge.read_grab(self.out / f"SDTY{letter}{r}.png") for r in range(1, 9)}
            sizes = {_size(self.out / f"SDTY{letter}{r}.png") for r in range(1, 9)}
            self.assertEqual(len(grabs), 1, letter)
            self.assertEqual(len(sizes), 1, letter)
            (left, top), (w, h) = grabs.pop(), sizes.pop()
            self.assertEqual(left, w // 2)
            a = _png(self.out / f"SDTY{letter}1.png")[..., 3]
            self.assertEqual(np.flatnonzero(a.any(axis=1))[-1], top + ge.FEET_SINK)

    def test_height_matches_target(self):
        a = _png(self.out / "SDTYA1.png")[..., 3] > 0
        ys = np.flatnonzero(a.any(axis=1))
        self.assertLessEqual(abs((ys[-1] - ys[0] + 1) - ge.TARGET_HEIGHT), 1)

    def test_per_enemy_target_height(self):
        spec = ge.EnemySpec(**{**self.spec.__dict__, "target_height": 40})
        out = self.tmp / "h40"
        m = ge.build(spec, out, ref_dir=self.tmp / "ref")
        a = _png(out / "SDTYA1.png")[..., 3] > 0
        ys = np.flatnonzero(a.any(axis=1))
        self.assertLessEqual(abs((ys[-1] - ys[0] + 1) - 40), 1)
        self.assertEqual(m["target_height"], 40)
        self.assertIn("gate", m)
        self.assertIn("reask", m)

    def test_mirrored_rotations_and_facing(self):
        for r in ge.MIRRORED_ROTS:
            a = _png(self.out / f"SDTYA{r}.png")
            b = _png(self.out / f"SDTYA{10 - r}.png")
            self.assertEqual(ge.detect_facing(a[..., 3] > 0), "right")
            self.assertEqual(ge.detect_facing(b[..., 3] > 0), "left")
        aim = self.metrics["sheets"]["aim"]["figures"]
        self.assertEqual([f["mirrored"] for f in aim], [False, True, True, False, False])
        self.assertEqual(ge.detect_facing(_png(self.out / "SDTYB2.png")[..., 3] > 0), "left")

    def test_output_is_palette_and_hard_alpha(self):
        pal = {tuple(c) for c in ge.palette_rgb().tolist()}
        for p in self.out.glob("SDTY*.png"):
            a = _png(p)
            self.assertEqual(set(np.unique(a[..., 3])) - {0, 255}, set(), p.name)
            cols = {tuple(int(v) for v in c) for c in a[a[..., 3] == 255][:, :3]}
            self.assertTrue(cols <= pal, p.name)

    def test_symbol_blanked_and_metrics(self):
        death = self.metrics["sheets"]["death"]
        self.assertGreater(death["figures"][0]["armband_px_blanked"], 0)
        self.assertEqual(self.metrics["lumps"], 26)
        self.assertTrue((self.out / "metrics.json").is_file())

    def test_nothing_written_to_assets(self):
        after = sorted(p.as_posix() for p in (ROOT / "assets").rglob("*")) if (ROOT / "assets").is_dir() else []
        self.assertEqual(after, self.assets_before)
        self.assertFalse(any((ROOT / "assets").rglob("SDTY*")) if (ROOT / "assets").is_dir() else False)

    def test_overlay_is_complete_and_reproducible(self):
        files = ge.overlay_plan(self.tmp / "", enemies=[ge.EnemySpec(**{**self.spec.__dict__, "name": "out"})])
        self.assertEqual(sorted(files), [f"sprites/{n}.png" for n in ge.lump_names(self.spec)])
        o1, o2 = self.tmp / "o1.pk3", self.tmp / "o2.pk3"
        ge.write_overlay(files, o1)
        ge.write_overlay(files, o2)
        self.assertEqual(o1.read_bytes(), o2.read_bytes())
        with zipfile.ZipFile(o1) as z:
            self.assertEqual(len(z.namelist()), 26)
            self.assertEqual(z.read("sprites/SDTYA1.png"), (self.out / "SDTYA1.png").read_bytes())
        self.assertTrue(o1.with_suffix(".txt").is_file())

    def test_overlay_refuses_an_incomplete_set(self):
        part = self.tmp / "part" / "out"
        part.mkdir(parents=True)
        shutil.copy(self.out / "SDTYA1.png", part / "SDTYA1.png")
        with self.assertRaises(SystemExit):
            ge.overlay_plan(self.tmp / "part", enemies=[ge.EnemySpec(**{**self.spec.__dict__, "name": "out"})])

    def test_review_sheet(self):
        spec = ge.EnemySpec(**{**self.spec.__dict__, "name": "out"})
        html = ge.review_sheet([spec], out=self.tmp / "sheet.html", out_root=self.tmp, sprites_dir=self.tmp / "none")
        text = html.read_text(encoding="utf-8")
        self.assertIn("SDTYA1", text)
        self.assertIn("Copiar resultado", text)
        self.assertIn("image-rendering:pixelated", text)
        self.assertNotIn("/*ITEMS*/", text)
        self.assertNotIn("gem_t_", text.split("const ITEMS")[1].split("SDTY")[0])

    def test_review_sheet_carries_gate_and_reask(self):
        spec = ge.EnemySpec(**{**self.spec.__dict__, "name": "out",
                               "reask": (("gem_t_turn.png", "redraw with room under the boots"),)})
        folder = self.tmp / "out"
        metrics = (folder / "metrics.json").read_text(encoding="utf-8")
        try:
            import json
            m = json.loads(metrics)
            m["reask"] = [list(r) for r in spec.reask]
            m["gate"] = ["gem_t_turn.png figura 1: botas cortadas"]
            (folder / "metrics.json").write_text(json.dumps(m), encoding="utf-8")
            html = ge.review_sheet([spec], out=self.tmp / "sheet2.html", out_root=self.tmp,
                                   sprites_dir=self.tmp / "none")
            text = html.read_text(encoding="utf-8")
            self.assertIn("redraw with room under the boots", text)
            self.assertIn("botas cortadas", text)
            self.assertIn("Pedir otra vez a Gemini", text)
        finally:
            (folder / "metrics.json").write_text(metrics, encoding="utf-8")


def armed(width: int = 30, height: int = 100, field_r: int = 7):
    """(rgb, mask) of a tall olive figure with a red band and a white disc off its axis."""
    rgb = np.zeros((height, width + 10, 3), np.uint8)
    mask = np.zeros(rgb.shape[:2], bool)
    mask[:, 5:5 + width] = True
    rgb[mask] = OLIVE
    rgb[38:63, 5:5 + width] = RED
    rgb[88:, 5:5 + width] = DARK
    yy, xx = np.mgrid[0:height, 0:width + 10]
    rgb[((yy - 50) ** 2 + (xx - 18) ** 2 <= field_r ** 2) & mask] = WHITE
    return rgb, mask


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D108SymbolTests(unittest.TestCase):
    """D108, "la mezcla": option 1 on the Reich, option 2 from the cache on the close pictures."""
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sd_d108_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_which_enemies_carry_it(self):
        want = {"rifleman": "white", "storm": "box", "panzer": "plain", "panzer_heavy": "plain", "general": "ring"}
        for name, spec in ge.ENEMIES.items():
            if name in want:
                self.assertEqual(spec.symbol, "warp", name)
                self.assertEqual(spec.symbol_fields, want[name], name)
                self.assertTrue(spec.corpse and set(spec.corpse) <= set(spec.single), name)
                self.assertIsNotNone(ge.symbol_pass(spec))
            else:      # the Legion, the doughboy, the hound: none
                self.assertEqual(spec.symbol, "none", name)
                self.assertIsNone(ge.symbol_pass(spec))
        self.assertIsNone(ge.symbol_pass(ge.RIFLEMAN, "none"))
        self.assertIsNotNone(ge.symbol_pass(ge.LEGION, "warp"))

    def test_the_general_keeps_his_flag(self):
        # his flag has white and red side by side: the ring mode wants a red patch walled in white, and no blue
        import armband_symbol as asym
        rgb = np.zeros((60, 60, 3), np.uint8)
        mask = np.ones((60, 60), bool)
        rgb[:] = (226, 214, 180)                               # the cream coat
        for k in range(8):                                     # stripes
            rgb[20 + 2 * k:21 + 2 * k, 10:40] = RED
            rgb[21 + 2 * k:22 + 2 * k, 10:40] = WHITE
        rgb[20:28, 10:22] = (30, 40, 150)                      # the canton
        self.assertEqual(asym.select_fields(rgb, mask, "ring", ge.GENERAL_FIELD_MAX)[1], [])

    def test_close_sources_are_profiles_and_corpses(self):
        close = ge.close_sources(ge.RIFLEMAN)
        for key in (("turn", 2, False, False), ("turn", 2, True, False), ("walkL", 2, True, False),
                    ("death2", 2, False, False), ("death2", 1, False, False)):
            self.assertIn(key, close)
        self.assertNotIn(("turn", 0, False, False), close)
        self.assertNotIn(("turn", 1, False, False), close)
        src = ge.lump_sources(ge.RIFLEMAN)
        for lump in ("SDRRB3", "SDRRB7", "SDRRG3", "SDRRL0", "SDRRU0", "SDRRK0"):
            self.assertIn(src[lump][:4], close, lump)       # U: the gib's corpse is the corpse's picture
        self.assertNotIn(src["SDRRB1"][:4], close)
        self.assertEqual(set(src), set(ge.lump_names(ge.RIFLEMAN)))

    def test_symbol_after_the_mirror(self):
        rgb, mask = armed()
        cut = ge.Cut(rgb, mask, "left", False, 0)
        sp = ge.SymbolPass("warp", "white")
        got, gmask, st = ge.source_picture(cut, mirror=True, symbol=sp)
        self.assertEqual(st, "option1")
        want, _ = ge.symbolise(np.ascontiguousarray(rgb[:, ::-1]), np.ascontiguousarray(mask[:, ::-1]), sp)
        np.testing.assert_array_equal(got, want)
        painted_then_flipped = ge.symbolise(rgb, mask, sp)[0][:, ::-1]
        self.assertFalse(np.array_equal(got, painted_then_flipped))    # a flipped symbol would be the wrong way round
        self.assertFalse(np.array_equal(got, rgb[:, ::-1]))

    def test_plate_after_the_symbol(self):
        rgb, mask = armed()
        cut = ge.Cut(rgb, mask, "left", False, 0)
        sp = ge.SymbolPass("warp", "white")
        plain = ge.source_picture(cut, symbol=sp)[0]
        dark = ge.source_picture(cut, shade=ge.PLATE_SHADE, symbol=sp)[0]
        np.testing.assert_array_equal(dark, ge.darken(plain, mask, ge.PLATE_SHADE))

    def test_no_field_no_symbol(self):
        rgb, mask = armed()
        rgb[rgb.min(axis=-1) > 200] = OLIVE
        out, st = ge.symbolise(rgb, mask, ge.SymbolPass())
        self.assertEqual(st, "nofield")
        self.assertIs(out, rgb)

    def test_the_cache_is_used(self):
        import armband_symbol as asym
        rgb, mask = armed()
        cut = ge.Cut(rgb, mask, "left", False, 0)
        sp = ge.SymbolPass("warp", "white", fooocus=True, cache_dir=self.tmp)
        opt1 = ge.source_picture(cut, symbol=ge.SymbolPass("warp", "white"))[0]
        got, _, st = ge.source_picture(cut, symbol=sp)
        self.assertEqual(st, "missing")                          # nothing generated: option 1 stays
        np.testing.assert_array_equal(got, opt1)
        key = asym.picture_key(rgb, mask)
        field = asym.select_fields(rgb, mask, "white")[1][0]
        ty, tx, n = asym.crop_box(field)
        patch = np.zeros((n, n, 4), np.uint8)
        patch[...] = (0, 250, 0, 255)
        asym.write_cache(key, {"label": "t", "fields": [{"k": 0, "status": "fooocus", "crop": [ty, tx, n]}]},
                         {0: patch}, self.tmp)
        got, _, st = ge.source_picture(cut, symbol=sp)
        self.assertEqual(st, "fooocus")
        self.assertTrue((got == (0, 250, 0)).all(axis=-1)[field].all())
        mir = ge.source_picture(cut, mirror=True, symbol=sp)       # the mirror is another picture: its own key
        self.assertEqual(mir[2], "missing")

    @unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART") == "1", "art tier: two builds and a control sheet, 2.5 s")
    def test_build_reports_the_symbol_per_lump(self):
        ref = self.tmp / "ref"
        ref.mkdir()
        stand = [person(80, rifle=False), person(80), person(80), person(80), person(80, rifle=False)]
        Image.fromarray(sheet(stand, bg=MAGENTA)).save(ref / "gem_t_turn.png")
        aim = [person(80, rifle=False), person(80, facing="right"), person(80, facing="right"),
               person(80), person(80, rifle=False)]
        Image.fromarray(sheet(aim, bg=PINK)).save(ref / "gem_t_aim.png")
        Image.fromarray(sheet([person(80), person(80)], bg=DARK_MAGENTA)).save(ref / "gem_t_death.png")
        spec = ge.EnemySpec(**{**tiny_spec().__dict__, "symbol": "warp", "corpse": ("D",)})
        m = ge.build(spec, self.tmp / "out", ref_dir=ref, cache_dir=self.tmp / "cache")
        close = set(m["symbol_close"])
        self.assertTrue({"SDTYA3", "SDTYA7", "SDTYB3", "SDTYB7", "SDTYD0", "SDTYE0"} <= close)
        self.assertNotIn("SDTYA1", close)
        for lump, st in m["symbol"].items():
            self.assertIn(st, ("missing", "nofield") if lump in close else ("option1", "nofield"), lump)
        self.assertIn("option1", m["symbol"].values())
        self.assertIn("missing", m["symbol"].values())
        off = ge.build(spec, self.tmp / "off", ref_dir=ref, symbol="none")
        self.assertEqual(off["symbol"], {})
        self.assertIn("missing", ge.symbol_summary(m))
        png = ge.control_sheet([spec], out=self.tmp / "ctl.png", ref_dir=ref, cache_dir=self.tmp / "cache")
        self.assertTrue(png.is_file())

    def test_control_sheet_never_under_assets(self):
        with self.assertRaises(SystemExit):
            ge.control_sheet([], out=ROOT / "assets" / "x.png")
        ge.guard_out(ge.CONTROL_PNG)


def two_overlapping(flash: bool):
    """(rgb, fg, guide rgb, guide masks): figure 0 top-left, figure 1 lower-right, their
    columns overlapping (30..40) so no column cuts them; with `flash`, figure 0's flash
    bridges them and lies over figure 1's body (rows 32..36, columns 38..50)."""
    img = np.empty((64, 90, 3), np.uint8)
    img[:] = MAGENTA
    img[0:30, 5:40] = OLIVE
    img[32:62, 30:75] = OLIVE
    guide = img.copy()
    if flash:
        img[26:36, 38:50] = YELLOW
    gm = ge.figures(ge.key_background(guide), 2)
    return img, ge.key_background(img), guide, gm


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D119GunnerPixelTests(unittest.TestCase):
    """D119: the gunner's fire sheet (turn plus flashes) and death_v2 (boots on the corpse)."""
    def test_path_below_is_inside_its_columns(self):
        b = ge.path_below((20, 30), ((5, 10), (20, 12)))
        self.assertTrue(b[10, 5] and b[19, 20] and not b[9, 5] and not b[11, 20])
        self.assertFalse(b[:, :5].any() or b[:, 21:].any())

    def test_merged_pair_cut_along_the_path(self):
        fg = np.zeros((60, 100), bool)
        fg[0:42, 10:40] = True                  # the falling man, his boots down to row 41
        fg[40:50, 20:95] = True                 # the corpse under them
        ms = ge.figures(fg, 2, path=((15, 40), (98, 40)))
        self.assertEqual(len(ms), 2)
        lower = max(ms, key=lambda m: int(np.flatnonzero(m.any(axis=1))[0]))
        self.assertTrue(lower[40:50, 20:95].all())
        self.assertFalse(lower[:40].any())
        with self.assertRaises(ValueError):
            ge.figures(fg, 2, path=((15, 55), (98, 55)))      # crosses nothing merged

    def test_guided_split_gives_the_flash_to_its_owner_and_heals_the_neighbour(self):
        img, fg, guide, gm = two_overlapping(flash=True)
        self.assertEqual(ge.label(fg)[1], 1)    # one piece: the flash bridges them
        masks, heals, g_rgb = ge.guided_figures(fg, img, guide, gm, ((30, 60, 0),))
        self.assertTrue(masks[0][26:36, 38:50].all())           # the flash, whole, to figure 0
        self.assertFalse(masks[1][26:32, 38:50].any())
        self.assertTrue(heals[1][32:36, 38:50].all())            # figure 1's body under it, from the guide
        self.assertTrue((g_rgb[32:36, 38:50] == OLIVE).all())
        self.assertTrue((masks[1] | heals[1])[32:62, 30:75].all())

    def test_guided_split_without_a_flash_entry_keeps_the_growth(self):
        img, fg, guide, gm = two_overlapping(flash=True)
        masks, heals, _ = ge.guided_figures(fg, img, guide, gm, ())
        self.assertTrue(masks[1][32:36, 38:50].all())
        self.assertFalse(heals[1].any())

    def test_guide_registered_a_pixel_off(self):
        img, _, guide, _ = two_overlapping(flash=False)
        moved = ge.shifted(img, 1, 0, 0)
        moved[0] = MAGENTA
        fg = ge.key_background(moved)
        self.assertEqual(ge.align_guide(moved, guide, fg), (1, 0))
        self.assertFalse(ge.new_paint(moved, ge.shifted(guide, 1, 0), fg).any())

    def test_plan_uses_the_guide(self):
        tmp = Path(tempfile.mkdtemp(prefix="sd_gemini_gunner_"))
        try:
            img, _, guide, _ = two_overlapping(flash=True)
            Image.fromarray(guide).save(tmp / "gem_x_turn.png")
            Image.fromarray(img).save(tmp / "gem_x_fire.png")
            spec = ge.EnemySpec(name="x", sprite="SDXX", folder="x", armband="none", sheets={
                "turn": ge.Sheet("gem_x_turn.png", 2, ("front", "back"), None),
                "fire": ge.Sheet("gem_x_fire.png", 2, ("front", "back"), None, guide="turn",
                                 flash=((30, 60, 0),))},
                rotated={}, single={})
            f0, f1 = ge.plan(spec, tmp)["fire"].figs
            self.assertEqual(f0.mask.shape, (36, 45))              # figure 0 and its flash (columns 5..49)
            self.assertEqual(f1.mask.shape, (30, 45))              # figure 1 whole, healed
            self.assertTrue(f1.mask.all())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_guide_must_be_a_plain_sheet(self):
        spec = ge.EnemySpec(name="x", sprite="SDXX", folder="x", sheets={
            "turn": ge.Sheet("t.png", 8, (), None, rows=2), "fire": ge.Sheet("f.png", 5, guide="turn")},
            rotated={}, single={})
        with self.assertRaises(ValueError):
            ge.guide_of(spec, "fire", {"turn": None, "fire": None})


@unittest.skipIf(ge is None, "art venv (numpy, Pillow) missing")
class D119GunnerSpecTests(unittest.TestCase):
    ZS = ROOT / "src" / "zscript" / "monsters" / "legion_gunner.zs"

    def test_names_letters_and_rules(self):
        spec = ge.GUNNER
        names = ge.lump_names(spec)
        self.assertEqual(len(names), 70)                         # design doc section 4
        for n in names:
            self.assertRegex(n, r"^SDLG[A-U][0-8]$")
            self.assertEqual(n[5] == "0", n[4] > "G", n)
        self.assertEqual(spec.target_height, ge.LEGION_HEIGHT)   # the trooper's height
        self.assertEqual((spec.armband, spec.symbol), ("none", "none"))   # the US flag only, no swastika
        self.assertEqual(spec.sheets["aim"].file, "gem_gunner_aim_v3.png")
        self.assertEqual(spec.sheets["death"].file, "gem_gunner_death_v2.png")
        self.assertEqual(spec.sheets["fire"].guide, "turn")
        self.assertEqual(sorted(spec.sheets["death"].pick), list(range(5)))
        self.assertTrue(all(v < spec.sheets["fire"].count for *_, v in spec.sheets["fire"].flash))
        self.assertNotIn("gunner", ge.ENEMIES)                   # built by its own command, not by `all` (installed by D123)
        self.assertIs(ge.PENDING["gunner"], spec)
        self.assertTrue(spec.reask and spec.derived)

    def test_every_state_letter_is_drawn(self):
        if not self.ZS.is_file():
            self.skipTest("legion_gunner.zs not present")
        text = self.ZS.read_text(encoding="utf-8")
        sprite = "SDLG" if re.search(r"^\s*SDLG ", text, re.M) else "SDLT"   # provisional today (D116)
        self.assertEqual(_state_letters(self.ZS, sprite), set(ge.GUNNER.rotated) | set(ge.GUNNER.single))

    def test_installed_actor_is_the_documented_swap(self):
        if not self.ZS.is_file():
            self.skipTest("legion_gunner.zs not present")
        text = self.ZS.read_text(encoding="utf-8")
        if "PROVISIONAL-D116" not in text:
            self.skipTest("already installed")
        sys.path.insert(0, str(ROOT / "tests"))
        import _p4_mod as p4
        swapped, _ = p4.apply_documented_swap(text)
        done = ge.installed_actor(text)

        def code(t):
            return [l.rstrip() for l in p4.strip_comments(t).splitlines() if l.strip()]
        self.assertEqual(code(done), code(swapped))
        self.assertNotIn("PROVISIONAL", done)
        self.assertNotIn("SDLT", p4.strip_comments(done))
        self.assertIn("SDLG", done)

    def test_built_set(self):
        """The real build (work/, gitignored): the set, the height, and D119's
        complaint answered: in F1 (the front) the flash is on the body's axis,
        firing at the player; in F3 (the profile) it is off to the side."""
        folder = ge.OUT_ROOT / "gunner"
        if not (folder / "SDLGF1.png").is_file():
            self.skipTest("work/art/enemies_gemini/gunner/ not built")
        self.assertEqual(sorted(p.stem for p in folder.glob("SDLG*.png")), ge.lump_names(ge.GUNNER))
        a = _png(folder / "SDLGB1.png")[..., 3] > 0
        ys = np.flatnonzero(a.any(axis=1))
        self.assertLessEqual(abs((ys[-1] - ys[0] + 1) - ge.GUNNER.target_height), 1)

        def flash_offset(lump):
            px = _png(folder / f"{lump}.png").astype(int)
            fire = (px[..., 3] > 0) & (px[..., 0] > 200) & (px[..., 1] > 150) & (px[..., 2] < px[..., 1])
            self.assertGreater(int(fire.sum()), 3, lump)
            return abs(float(np.nonzero(fire)[1].mean()) - ge.read_grab(folder / f"{lump}.png")[0])
        self.assertLess(flash_offset("SDLGF1"), 4)
        self.assertGreater(flash_offset("SDLGF3"), 8)


@unittest.skipIf(ge is None or os.environ.get("SD_SKIP_SLOW_ART") == "1", "art tier only")
class GeneratedSetTests(unittest.TestCase):
    """The real builds in work/ (gitignored), if they exist."""
    def test_builds(self):
        built = 0
        for spec in ge.ENEMIES.values():
            folder = ge.OUT_ROOT / spec.name
            if not folder.is_dir():
                continue
            built += 1
            names = sorted(p.stem for p in folder.glob(f"{spec.sprite}*.png"))
            self.assertEqual(names, ge.lump_names(spec), spec.name)
            for p in folder.glob(f"{spec.sprite}*.png"):
                self.assertIsNotNone(ge.read_grab(p), p.name)
            a = _png(folder / f"{ge.ref_lump(spec)}.png")[..., 3] > 0
            ys = np.flatnonzero(a.any(axis=1))
            self.assertLessEqual(abs((ys[-1] - ys[0] + 1) - spec.target_height), 1, spec.name)
        if not built:
            self.skipTest("work/art/enemies_gemini/ not built")


if __name__ == "__main__":
    unittest.main()
