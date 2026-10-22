"""tools/art/armband_symbol.py: the D12 symbol painted at Gemini resolution (D105, option 1).

Synthetic only (no Gemini sheet, D77): a tall olive "arm" with a red band
and a white field, drawn here. Covers the vector symbol's handedness
against the approved sprite's grid (ge.SYMBOL) and its 45-degree tilt, that
it is never mirrored, the cylinder's foreshortening near the silhouette,
the clip to the field, the multiply that keeps the field's light, the
measured edge softness, the seeded grain, the arm axis (standing, lying,
a hint), and the pipeline hook being OFF by default. D108 (the mix): the
field modes (white, box, plain, ring; flags, sparks and coats refused),
the symbol's parts and their mirror, the frame scaled to a crop, the
objective repaint check (passes its own start, fails the wrong handedness,
a missing arm, extra ink, ink outside the disc), the seed pick, the
cache round trip (missing, fooocus, fallback) and the denoise by size.
"""
from __future__ import annotations

import argparse
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

import armband_symbol as asym  # noqa: E402
import gemini_enemy as ge  # noqa: E402

OLIVE, RED, WHITE, BOOT = (92, 90, 52), (180, 30, 25), (226, 222, 214), (20, 18, 16)


def arm(field_x: int = 15, field_r: int = 7, width: int = 30, height: int = 100, grad: bool = False):
    """A tall figure (the arm) with a red band (rows 38-62) and a white disc on it."""
    rgb = np.zeros((height, width + 10, 3), np.uint8)
    mask = np.zeros(rgb.shape[:2], bool)
    mask[:, 5:5 + width] = True
    rgb[mask] = OLIVE
    rgb[38:63, 5:5 + width] = RED
    rgb[88:, 5:5 + width] = BOOT          # Gemini's black: the ink
    yy, xx = np.mgrid[0:height, 0:width + 10]
    disc = ((yy - 50) ** 2 + (xx - 5 - field_x) ** 2 <= field_r ** 2) & mask
    rgb[disc] = WHITE
    if grad:     # the field darker to the right (the arm's shade)
        k = np.clip(1.0 - (xx - 5 - field_x + field_r) / (4.0 * field_r), 0.5, 1.0)
        rgb[disc] = (np.array(WHITE)[None] * k[disc][:, None]).astype(np.uint8)
    return rgb, mask, disc


def ink_of(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    return np.abs(after.astype(int) - before.astype(int)).sum(axis=-1) > 60


class SymbolTests(unittest.TestCase):
    def cells(self, tilt: float, reach: float = math.sqrt(2.0)) -> np.ndarray:
        c = (np.arange(5) + 0.5) / 5 * 2 - 1           # the 5 cell centres, -1..1
        x, y = np.meshgrid(c, -c)                        # row 0 on top (y up)
        return asym.symbol_ink(x, y, tilt, reach)

    def test_upright_grid_is_the_approved_sprite_symbol(self):
        want = np.array([[ch == "K" for ch in row] for row in ge.SYMBOL])
        np.testing.assert_array_equal(self.cells(0.0), want)

    def test_four_fold_but_never_mirror_symmetric(self):
        g = self.cells(0.0)
        np.testing.assert_array_equal(np.rot90(g), g)
        self.assertFalse(np.array_equal(g[:, ::-1], g))
        self.assertFalse(np.array_equal(g[::-1], g))

    def test_tilt_rotates_without_flipping(self):
        rng = np.random.default_rng(1)
        x, y = rng.uniform(-1, 1, 4000), rng.uniform(-1, 1, 4000)
        r = math.radians(45.0)
        # a point of the tilted symbol is the upright one's point turned back by 45 degrees
        u, v = math.cos(r) * x + math.sin(r) * y, -math.sin(r) * x + math.cos(r) * y
        np.testing.assert_array_equal(asym.symbol_ink(x, y, 45.0), asym.symbol_ink(u, v, 0.0))
        self.assertEqual(asym.TILT_DEG, 45.0)

    def test_tips_stay_inside_reach(self):
        rng = np.random.default_rng(2)
        x, y = rng.uniform(-1.2, 1.2, 20000), rng.uniform(-1.2, 1.2, 20000)
        ink = asym.symbol_ink(x, y)
        self.assertTrue(ink.any())
        self.assertLessEqual(float(np.hypot(x, y)[ink].max()), asym.SYMBOL_REACH + 1e-9)


class PaintTests(unittest.TestCase):
    def test_paints_only_inside_the_field(self):
        rgb, mask, disc = arm()
        out, info = asym.paint_symbol(rgb, mask)
        self.assertEqual(info.fields, 1)
        changed = (out != rgb).any(axis=-1)
        self.assertTrue(changed.any())
        self.assertFalse((changed & ~ge._dilate(disc, asym.FIELD_GROW)).any())
        self.assertFalse((changed & ~mask).any())

    def test_never_mirrored(self):
        rgb, mask, _ = arm()
        out, _ = asym.paint_symbol(rgb, mask, sigma=asym.SIGMA_MIN, grain=0.0)
        flip, _ = asym.paint_symbol(rgb[:, ::-1].copy(), mask[:, ::-1].copy(), sigma=asym.SIGMA_MIN, grain=0.0)
        # the picture is symmetric, so painting its mirror and mirroring back would match only if the symbol flipped
        self.assertFalse(np.array_equal(flip[:, ::-1], out))
        n0, n1 = int(ink_of(rgb, out).sum()), int(ink_of(rgb[:, ::-1], flip).sum())
        self.assertLess(abs(n0 - n1), 0.15 * n0)          # the same symbol, the same size

    def test_cylinder_foreshortens_near_the_silhouette(self):
        def spans(fx):
            rgb, mask, _ = arm(field_x=fx, field_r=6)
            ys, xs = np.nonzero(ink_of(rgb, asym.paint_symbol(rgb, mask, grain=0.0)[0]))
            return np.ptp(xs) + 1, np.ptp(ys) + 1
        w0, h0 = spans(15)                 # facing the viewer
        w1, h1 = spans(25)                 # near the arm's edge
        self.assertLess(w1 / h1, 0.85 * w0 / h0)

    def test_multiply_keeps_the_fields_light(self):
        rgb, mask, disc = arm()
        shaded = rgb.copy()
        right = disc & (np.arange(rgb.shape[1])[None, :] > 20)    # the field's right half in shade
        shaded[right] = (shaded[right] * 0.75).astype(np.uint8)   # still the strict white
        flat_out, _ = asym.paint_symbol(rgb, mask, grain=0.0, sigma=asym.SIGMA_MIN)
        shade_out, _ = asym.paint_symbol(shaded, mask, grain=0.0, sigma=asym.SIGMA_MIN)
        L = asym.lum(flat_out)
        full = right & ink_of(rgb, flat_out) & (L < 1.2 * L[disc].min())   # fully inked pixels
        self.assertGreater(int(full.sum()), 3)
        ratio = float(asym.lum(shade_out)[full].mean()) / float(L[full].mean())
        self.assertLess(ratio, 0.85)                              # the ink is in the field's shade too
        self.assertLess(float(L[full].mean()), 0.25 * float(asym.lum(rgb)[full].mean()))

    def test_no_field_no_change(self):
        rgb, mask, disc = arm()
        rgb[disc] = RED
        out, info = asym.paint_symbol(rgb, mask)
        self.assertEqual(info.fields, 0)
        np.testing.assert_array_equal(out, rgb)

    def test_grain_is_seeded(self):
        rgb, mask, _ = arm()
        a = asym.paint_symbol(rgb, mask, seed=3, grain=6.0)[0]
        b = asym.paint_symbol(rgb, mask, seed=3, grain=6.0)[0]
        c = asym.paint_symbol(rgb, mask, seed=4, grain=6.0)[0]
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, c))


class MeasureTests(unittest.TestCase):
    def test_edge_sigma_reads_the_softness(self):
        rgb, mask, disc = arm()
        hard = asym.edge_sigma(rgb, mask, disc)
        soft_rgb = np.dstack([asym.gaussian_blur(rgb[..., k].astype(float), 1.0) for k in range(3)])
        soft = asym.edge_sigma(np.clip(soft_rgb, 0, 255).astype(np.uint8), mask, disc)
        self.assertEqual(hard, asym.SIGMA_MIN)
        self.assertGreater(soft, hard)
        self.assertLessEqual(soft, asym.SIGMA_MAX)

    def test_grain_sigma_flat_is_zero_noisy_is_not(self):
        rgb = np.full((40, 40, 3), 30, np.uint8)
        mask = np.ones((40, 40), bool)
        self.assertEqual(asym.grain_sigma(rgb, mask), 0.0)
        noisy = np.clip(30 + np.random.default_rng(0).normal(0, 5, (40, 40, 1)), 0, 255).astype(np.uint8)
        self.assertGreater(asym.grain_sigma(np.repeat(noisy, 3, axis=2), mask), 2.0)

    def test_arm_axis(self):
        tall = np.zeros((60, 20), bool)
        tall[:, 5:15] = True
        np.testing.assert_allclose(asym.body_along(tall), [0, -1], atol=1e-6)     # up the screen
        lying = tall.T.copy()
        np.testing.assert_allclose(asym.body_along(lying), [1, 0], atol=1e-6)     # to the right
        np.testing.assert_allclose(asym.body_along(tall, 180.0), [-1, 0], atol=1e-6)
        np.testing.assert_allclose(asym._perp(np.array([0.0, -1.0])), [1, 0])     # right-handed


class HookTests(unittest.TestCase):
    def test_off_by_default(self):
        # the function paints nothing unless asked; the CLI's default is each enemy's own (D108)
        self.assertEqual(asym.DEFAULT_SYMBOL, "none")
        ap = asym.add_symbol_arg(argparse.ArgumentParser())
        self.assertEqual(ap.parse_args([]).symbol, "spec")
        self.assertEqual(ap.parse_args(["--symbol", "warp"]).symbol, "warp")
        self.assertEqual(ap.parse_args(["--symbol", "none"]).symbol, "none")
        rgb, mask, _ = arm()
        self.assertIs(asym.apply_symbol(rgb, mask), rgb)
        self.assertFalse(np.array_equal(asym.apply_symbol(rgb, mask, "warp"), rgb))
        with self.assertRaises(ValueError):
            asym.apply_symbol(rgb, mask, "stamp")

    def test_comparison_never_written_under_assets(self):
        with self.assertRaises(SystemExit):
            asym._draw([], ROOT / "assets" / "x.png", "SDRR")


# ------------------------------------------------------------- D108: the mix
def band_with(field_rgb, ring_rgb=RED, size: int = 8, at: tuple = (40, 10), height: int = 80, width: int = 40,
              wall: int = 1):
    """An olive figure with a red band (rows at[0]-6 .. at[0]+size+6) and a
    `size` square field of `field_rgb` on it (ring_rgb: its wall)."""
    rgb = np.zeros((height, width, 3), np.uint8)
    mask = np.ones((height, width), bool)
    rgb[:] = OLIVE
    y, x = at
    rgb[y - 6:y + size + 6, :] = RED
    rgb[y - wall:y + size + wall, x - wall:x + size + wall] = ring_rgb
    rgb[y:y + size, x:x + size] = field_rgb
    return rgb, mask


class FieldModeTests(unittest.TestCase):
    def test_white_finds_the_disc(self):
        rgb, mask, disc = arm()
        out, fields = asym.select_fields(rgb, mask, "white")
        self.assertIs(out, rgb)
        self.assertEqual(len(fields), 1)
        self.assertTrue((fields[0] & disc).sum() >= 0.9 * disc.sum())

    def test_plain_is_the_painted_colour_exactly(self):
        rgb, mask = band_with(ge.PATCH_RGB)
        self.assertEqual(len(asym.select_fields(rgb, mask, "plain")[1]), 1)
        near = tuple(c - 3 for c in ge.PATCH_RGB)             # a cream coat, close but not painted
        rgb2, mask2 = band_with(near)
        self.assertEqual(asym.select_fields(rgb2, mask2, "plain")[1], [])

    def test_ring_becomes_one_plain_field(self):
        rgb, mask = band_with(RED, ring_rgb=WHITE, size=10, wall=3)   # a white wall round red: the General's
        out, fields = asym.select_fields(rgb, mask, "ring", 40)
        self.assertEqual(len(fields), 1)
        inner = (slice(40, 50), slice(10, 20))
        self.assertTrue(ge.white_mask(out[inner]).all())        # the enclosed red is white now
        self.assertTrue(ge.red_mask(rgb[inner]).all())          # the input is not touched

    def test_flag_spark_and_size_are_refused(self):
        rgb, mask = band_with(WHITE)
        self.assertEqual(len(asym.select_fields(rgb, mask, "white")[1]), 1)
        flag = rgb.copy()
        flag[28:36, 18:30] = (20, 30, 160)                      # a canton's blue beside it
        self.assertEqual(asym.select_fields(flag, mask, "white")[1], [])
        spark, smask = band_with(WHITE)
        spark[34:56, :] = OLIVE                                 # the white is not ON the band
        self.assertEqual(asym.select_fields(spark, smask, "box")[1], [])
        big, bmask = band_with(WHITE, size=asym.FIELD_MAX + 4)
        self.assertEqual(asym.select_fields(big, bmask, "white")[1], [])
        with self.assertRaises(ValueError):
            asym.select_fields(rgb, mask, "stamp")


class PartTests(unittest.TestCase):
    def grid(self, mirror=False):
        c = (np.arange(5) + 0.5) / 5 * 2 - 1
        x, y = np.meshgrid(c, -c)
        return asym.symbol_parts(x, y, 0.0, math.sqrt(2.0), mirror)

    def test_parts_are_the_symbol_cells(self):
        g = self.grid()
        black = np.array([[ch == "K" for ch in row] for row in ge.SYMBOL])
        np.testing.assert_array_equal(g > 0, black)
        self.assertEqual(int((g == 1).sum()), 1)
        for a in asym.ARMS:
            self.assertEqual(int((g == a).sum()), 4)

    def test_mirror_is_the_other_handedness(self):
        g, m = self.grid(), self.grid(mirror=True)
        np.testing.assert_array_equal(m, g[:, ::-1])
        self.assertFalse(np.array_equal(m > 0, g > 0))

    def test_scaled_frame_draws_the_same_symbol_larger(self):
        rgb, mask, disc = arm()
        frame = asym.arm_frame(rgb, mask, disc)
        small = asym.coverage(mask.shape, frame, disc)
        k = 4
        big_clip = np.kron(disc, np.ones((k, k), bool))
        big = asym.coverage(big_clip.shape, asym.scale_frame(frame, k, (0, 0)), big_clip, ss=2)
        self.assertAlmostEqual(big.sum() / k ** 2, small.sum(), delta=0.12 * small.sum())
        ys, xs = np.nonzero(small > 0.5)
        bys, bxs = np.nonzero(big > 0.5)
        self.assertAlmostEqual((bys.mean() + 0.5) / k - 0.5, ys.mean(), delta=0.5)
        self.assertAlmostEqual((bxs.mean() + 0.5) / k - 0.5, xs.mean(), delta=0.5)


class RepaintScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rgb, mask, disc = arm(field_r=8)
        cls.rgb, cls.mask, cls.disc = rgb, mask, disc
        cls.prep = asym.prepare_field(rgb, mask, disc, up=256)

    def test_the_start_passes(self):
        s = asym.score_repaint(self.prep.init, self.prep, res=128)
        self.assertTrue(s.passed, s)
        self.assertGreater(s.iou - s.iou_mirror, asym.HAND_MARGIN)

    def test_the_plain_field_fails(self):
        self.assertFalse(asym.score_repaint(self.prep.base, self.prep, res=128).passed)

    def test_wrong_handedness_fails(self):
        p = self.prep
        flipped = asym.Prepared(p.crop, p.base, p.init, p.inpaint, p.clip, p.parts_m, p.parts, p.denoise)
        s = asym.score_repaint(p.init, flipped, res=128)     # the start judged against the mirror template
        self.assertFalse(s.passed)
        self.assertIn("mirror", s.why)

    def test_a_missing_arm_fails(self):
        img = self.prep.init.copy()
        arm2 = np.asarray(Image.fromarray(ge._dilate(self.prep.parts == 2, 6).astype(np.uint8) * 255)) > 0
        img[arm2 & (self.prep.parts != 1)] = (230, 226, 218)  # one arm painted out
        s = asym.score_repaint(img, self.prep, res=128)
        self.assertFalse(s.passed)
        self.assertIn("arm", s.why)

    def test_ink_outside_the_disc_fails(self):
        img = self.prep.init.copy()
        ring = self.prep.inpaint & ~self.prep.clip
        img[ring] = (10, 10, 10)
        s = asym.score_repaint(img, self.prep, res=128)
        self.assertFalse(s.passed)
        self.assertIn("outside", s.why)

    def test_extra_ink_in_the_disc_fails(self):
        img = self.prep.init.copy()
        img[self.prep.clip & (self.prep.parts == 0)] = (10, 10, 10)
        s = asym.score_repaint(img, self.prep, res=128)
        self.assertFalse(s.passed)
        self.assertIn("extra", s.why)

    def test_pick_takes_the_best_passing_or_none(self):
        worse = self.prep.init.copy()
        bad = self.prep.base
        best, scores = asym.pick_seed({"a": bad, "b": self.prep.init, "c": worse}, self.prep)
        self.assertIn(best, ("b", "c"))
        self.assertFalse(scores["a"].passed)
        self.assertIsNone(asym.pick_seed({"a": bad}, self.prep)[0])

    def test_denoise_by_disc_size(self):
        small = np.zeros((40, 40), bool)
        small[10:16, 10:18] = True
        big = np.zeros((40, 40), bool)
        big[5:20, 5:20] = True
        self.assertEqual(asym.denoise_for(small), asym.DENOISE_BY_SIDE[-1][1])
        self.assertEqual(asym.denoise_for(big), asym.DENOISE_BY_SIDE[0][1])
        self.assertLess(asym.denoise_for(small), asym.denoise_for(big))


class FooocusCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sd_armband_cache_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_key_reads_pixels_and_mask(self):
        rgb, mask, _ = arm()
        k = asym.picture_key(rgb, mask)
        self.assertEqual(k, asym.picture_key(rgb.copy(), mask.copy()))
        other = rgb.copy()
        other[0, 0, 0] ^= 1
        self.assertNotEqual(k, asym.picture_key(other, mask))
        self.assertNotEqual(k, asym.picture_key(rgb[:, ::-1].copy(), mask[:, ::-1].copy()))

    def test_round_trip_missing_and_fallback(self):
        rgb, mask, disc = arm()
        key = asym.picture_key(rgb, mask)
        out, st = asym.apply_fooocus(rgb, mask, key, self.tmp)
        self.assertEqual(st, "missing")
        self.assertIs(out, rgb)
        ty, tx, n = asym.crop_box(disc)
        patch = np.zeros((n, n, 4), np.uint8)
        patch[...] = (0, 255, 0, 255)
        asym.write_cache(key, {"label": "t", "fields": [{"k": 0, "status": "fooocus", "crop": [ty, tx, n]}]},
                         {0: patch}, self.tmp)
        out, st = asym.apply_fooocus(rgb, mask, key, self.tmp)
        self.assertEqual(st, "fooocus")
        green = (out == (0, 255, 0)).all(axis=-1)
        self.assertTrue(green[disc].all())
        self.assertFalse(green[~mask].any())                  # inside the figure only
        asym.write_cache(key, {"label": "t", "fields": [{"k": 0, "status": "fallback", "crop": [ty, tx, n]}]},
                         {}, self.tmp)
        out, st = asym.apply_fooocus(rgb, mask, key, self.tmp)
        self.assertEqual(st, "fallback")
        np.testing.assert_array_equal(out, rgb)

    def test_patch_alpha_is_the_mask(self):
        rgb, mask, disc = arm(field_r=8)
        prep = asym.prepare_field(rgb, mask, disc, up=192)
        patch = asym.patch_from(prep.init, prep)
        self.assertEqual(patch.shape, (prep.crop[2], prep.crop[2], 4))
        ty, tx, n = prep.crop
        sub = np.zeros((n, n), bool)
        H, W = disc.shape
        sub[max(0, -ty):min(n, H - ty), max(0, -tx):min(n, W - tx)] = \
            disc[max(0, ty):min(H, ty + n), max(0, tx):min(W, tx + n)]
        self.assertTrue((patch[..., 3][sub] == 255).mean() > 0.9)
        far = ~ge._dilate(sub, 4)
        self.assertEqual(int(patch[..., 3][far].max()), 0)

    def test_cache_never_written_under_assets(self):
        with self.assertRaises(SystemExit):
            asym.write_cache("x", {"fields": []}, {}, ROOT / "assets" / "cache")


if __name__ == "__main__":
    unittest.main()
