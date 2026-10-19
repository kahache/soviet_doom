"""tools/art/hand_ref.py: the ice axe's held frame derived from the CEO's
reference images (N14 / N4 round 3b: a right hand, the axe polished), a
sweep for review.

Fast tests: the pieces (tones, posterization, masks, the verdict table).
Render tests (SD_SKIP_SLOW_ART skips them; they also skip when the
references or the approved TT-33 frame are not in work/, which is
gitignored): deterministic output, palette-only pixels, size and place
inside the TT-33's envelope, the hand drawn over the shaft.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    import hand_ref as hr
except ImportError:          # art tooling (numpy, Pillow) not installed
    np = hr = None

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the renders")


def inputs_present() -> bool:
    return hr is not None and hr.TT33_A.is_file() and all((hr.REF_DIR / s.file).is_file() for s in hr.REFS.values())


@unittest.skipIf(hr is None, "art tooling (numpy, Pillow) not installed")
class PiecesTest(unittest.TestCase):
    def test_cells_are_round_3as_three_that_passed(self):
        self.assertEqual([c.key for c in hr.CELLS], ["C1", "C3", "C4"])
        self.assertEqual({c.ref for c in hr.CELLS}, {"R1"})
        self.assertTrue({c.size for c in hr.CELLS} <= {0.85, 1.0, 1.15})
        for c in hr.CELLS:
            self.assertIn(c.tones, (3, 4, 5))
            self.assertGreaterEqual(c.grip_x, hr.SCREEN_W / 2)      # centre-right, as Doom's fist and chainsaw

    def test_every_cell_judged_and_the_recommended_one_passes(self):
        self.assertEqual(set(hr.VERDICTS), {c.key for c in hr.CELLS})
        for status, why in hr.VERDICTS.values():
            self.assertIn(status, ("pass", "drop"))
            self.assertTrue(why)
        self.assertEqual(hr.VERDICTS[hr.RECOMMENDED][0], "pass")

    def test_tone_set_takes_distinct_ramp_colours_dark_to_light(self):
        ref = np.linspace(40.0, 200.0, 500)
        tones = hr.tone_set(hr.SKIN, ref, 4)
        ramp = {tuple(c) for c in hr.hs.ramp_cols(hr.SKIN)}
        self.assertEqual(len({tuple(t) for t in tones}), 4)
        self.assertTrue({tuple(t) for t in tones} <= ramp)
        lum = hr.luminance(tones.astype(np.float32))
        self.assertTrue((np.diff(lum) > 0).all())

    def test_posterize_keeps_the_order_of_values(self):
        ref = np.linspace(40.0, 200.0, 500)
        tones = hr.tone_set(hr.SKIN, ref, 4)
        values = np.array([0.9, 0.1, 0.5, 0.3, 0.7])
        idx = hr.posterize(values, ref, tones)
        order = np.argsort(values)
        self.assertTrue((np.diff(idx[order]) >= 0).all())
        self.assertEqual(int(idx[order[0]]), 0)
        self.assertEqual(int(idx[order[-1]]), 3)

    def test_edge_and_component(self):
        m = np.zeros((7, 7), bool)
        m[1:6, 1:6] = True
        e = hr.edge(m)
        self.assertFalse(e[3, 3])
        self.assertTrue(e[1, 3] and e[3, 1])
        m2 = m.copy()
        m2[0, 6] = True                                   # an island, not 4-connected
        comp = hr.component(m2, (3, 3))
        self.assertTrue((comp == m).all())

    def test_masked_box_ignores_pixels_outside_the_mask(self):
        a = np.array([[1.0, 1.0, 9.0]])
        m = np.array([[True, True, False]])
        out = hr.masked_box(a, m, 1)
        self.assertAlmostEqual(float(out[0, 0]), 1.0)
        self.assertAlmostEqual(float(out[0, 1]), 1.0)

    def test_shade_wood_moves_only_wood_and_never_onto_the_rim(self):
        tones = hr.wood_cols()
        cols = np.array([tones[hr.WOOD_LIT], tones[hr.WOOD_SHADE], tones[hr.WOOD_RIM], (1, 2, 3)], np.uint8)
        out = hr.shade_wood(cols, hr.FIST_SHADE)
        self.assertEqual(tuple(out[0]), tuple(tones[hr.WOOD_LIT - hr.FIST_SHADE]))
        self.assertEqual(tuple(out[1]), tuple(tones[hr.WOOD_SHADOW]))
        self.assertEqual(tuple(out[2]), tuple(tones[hr.WOOD_RIM]))
        self.assertEqual(tuple(out[3]), (1, 2, 3))

    def test_wood_tones_are_palette_colours_dark_to_light(self):
        tones = hr.wood_cols()
        self.assertTrue({tuple(int(v) for v in c) for c in tones} <= hr.palette_set())
        self.assertTrue((np.diff(hr.luminance(tones.astype(np.float32))) > 0).all())

    def test_tone_shaft_turns_a_flat_bar_into_a_round_grained_haft(self):
        h, w = 40, 15
        rgba = np.zeros((h, w, 4), np.uint8)
        wood = np.zeros((h, w), bool)
        wood[:, 3:12] = True
        rgba[wood] = (200, 190, 141, 255)
        idx = hr.tone_shaft(rgba, wood, (7.0, 20.0), (0.0, -1.0))
        self.assertGreaterEqual(len(set(idx[wood].tolist())), 4)
        self.assertTrue((idx[:, 3] == hr.WOOD_RIM).all() and (idx[:, 11] == hr.WOOD_RIM).all())
        lit_left = hr.WOOD_LIGHT[0] < 0
        left, right = idx[20, 4], idx[20, 10]
        self.assertGreater(left if lit_left else right, right if lit_left else left)

    def test_d76_pick_is_pinned(self):
        # the CEO's pick: L1.7 H1.8, the shaft straight and as wide as L1.0 H1.8's (D76, D76b)
        self.assertEqual(hr.D76_PICK, {"shaft_k": 1.7, "head_k": 1.8, "straight": True})
        self.assertEqual(next(c for c in hr.CELLS if c.key == "C3").size, 1.15)

    def test_mirrored_spec_is_moved_once(self):
        spec = hr.REFS["R1"]
        self.assertTrue(spec.mirror)                       # the CEO: the player is right-handed
        o = hr.oriented(spec)
        self.assertEqual(o.seed, (hr.PHOTO_W - 1 - spec.seed[0], spec.seed[1]))
        self.assertEqual(o.axis[0][0], hr.PHOTO_W - 1 - spec.axis[0][0])
        self.assertIs(hr.oriented(o), o)
        self.assertIs(hr.oriented(hr.REFS["R2"]), hr.REFS["R2"])


@unittest.skipIf(hr is None, "art tooling (numpy, Pillow) not installed")
@unittest.skipUnless(inputs_present(), "the references or the TT-33 frame are not in work/ (gitignored)")
class RenderTest(unittest.TestCase):
    cells = None
    cache = None

    @classmethod
    def setUpClass(cls):
        if os.environ.get("SD_SKIP_SLOW_ART"):
            return
        cls.cache = {}
        cls.cells = hr.build_all(out_dir=None, cache=cls.cache)

    @slow
    def test_deterministic(self):
        again = hr.build_cell(hr.CELLS[0])
        first = self.cells[hr.CELLS[0].key]
        self.assertEqual(again["offsets"], first["offsets"])
        self.assertTrue(np.array_equal(again["sprite"], first["sprite"]))

    @slow
    def test_palette_only_pixels(self):
        pal = hr.palette_set()
        for k, c in self.cells.items():
            spr = c["sprite"]
            self.assertTrue(set(np.unique(spr[..., 3])) <= {0, 255}, k)
            cols = {tuple(int(v) for v in px) for px in spr[spr[..., 3] > 0][:, :3]}
            self.assertTrue(cols <= pal, f"{k}: {sorted(cols - pal)[:5]}")

    @slow
    def test_inside_the_tt33_envelope(self):
        spr, off = hr.hs.read_png_sprite(hr.TT33_A)
        tt = hr.hs.measure(spr, off)
        palm = hr.tt33_palm_px()
        for k, c in self.cells.items():
            m = c["metrics"]
            self.assertLessEqual(abs(m["height_above_bar"] - tt["height"]), hr.hs.TOLERANCE * tt["height"], k)
            x0, _, x1, _ = m["bbox_bar_on"]
            self.assertGreaterEqual((x0 + x1) / 2, hr.SCREEN_W / 2, k)          # centre-right ...
            self.assertLessEqual((x0 + x1) / 2, 216, k)                         # ... not past the chainsaw
            self.assertLessEqual(x1, hr.SCREEN_W - 40, k)                       # not pushed to the right edge
            self.assertTrue(0.85 * palm - 0.01 <= c["palm_px"] <= 1.15 * palm + 0.01, k)

    @slow
    def test_passing_cells_hold_the_shaft(self):
        for k, c in self.cells.items():
            if hr.VERDICTS[k][0] != "pass":
                continue
            m = c["metrics"]
            self.assertGreater(m["shaft_px_above_fist"], 0, k)
            self.assertGreater(m["shaft_px_below_fist"], 0, k)
            self.assertEqual(m["photo_border_visible_bar"], 0, k)
            # the hand is drawn last: every hand pixel is in the frame as it is
            spr, (lx, ty) = c["sprite"], c["offsets"]
            hand = c["hand"]["rgba"]
            hx, hy = c["hand_xy"]
            mask = hand[..., 3] > 0
            ys, xs = np.nonzero(mask)
            sy, sx = ys + hy - (hr.WEAPONTOP - ty), xs + hx + lx
            ok = (sy >= 0) & (sy < spr.shape[0]) & (sx >= 0) & (sx < spr.shape[1])
            self.assertTrue((spr[sy[ok], sx[ok]] == hand[ys[ok], xs[ok]]).all(), k)


    @slow
    def test_d76b_shaft_is_straight_and_constant_width(self):
        base, gy = hr.c3_grip_row()
        c = hr.build_cell(hr.replace(base, key="D76b", grip_y=gy, **hr.D76_PICK))
        x0, y0 = hr.hs.place(c["sprite"], c["offsets"], bar=False)
        ys, xs = np.nonzero(c["axe_mask"])
        X, Y = xs + x0 + 0.5, ys + y0 + 0.5
        # against one straight line, the shaft's axis through the grip, per step along it
        cx, cy = c["grip"]
        d = np.asarray(c["up"], float)
        n = np.array([-d[1], d[0]])
        t = (X - cx) * d[0] + (Y - cy) * d[1]
        a = (X - cx) * n[0] + (Y - cy) * n[1]
        steps = np.round(t).astype(int)
        centres, widths = [], []
        for k in range(steps.min(), steps.max() + 1):
            m = steps == k
            if m.sum() >= 3:
                centres.append((a[m].min() + a[m].max()) / 2)
                widths.append(a[m].max() - a[m].min())
        # whole cross-sections only: the screen's bottom edge and the collar cut the bar's two ends
        full = [i for i, w in enumerate(widths) if w >= 0.8 * float(np.median(widths))]
        centres = [centres[i] for i in full]
        widths = [widths[i] for i in full]
        self.assertGreater(len(centres), 40)
        self.assertLessEqual(max(abs(v) for v in centres), 1.0)
        self.assertLessEqual(max(widths) - min(widths), 1.5)
        self.assertTrue(8.0 <= float(np.median(widths)) + 1 <= 12.0)   # ~10 px, L1.0 H1.8's

    @slow
    def test_right_handed_the_sleeve_leaves_through_the_bottom_right(self):
        for k, c in self.cells.items():
            spr, off = c["sprite"], c["offsets"]
            x0, y0 = hr.hs.place(spr, off, bar=False)
            sl = hr._hand_mask(spr.shape[:2], c["hand"], c["hand_xy"], x0, y0, "sleeve")
            ys, xs = np.nonzero(sl)
            gx, gy = c["grip"]
            self.assertGreater(ys.size, 0, k)
            # the sleeve sits below and to the right of the grip, and where it meets the
            # bottom of the view (the status bar's line) it is right of the grip
            self.assertGreater(float(np.mean(xs + x0)), gx, k)
            self.assertGreater(float(np.mean(ys + y0)), gy, k)
            bar_row = hr.hs.VIEW_H + hr.BAR_LIFT - 1 - y0
            at_bar = np.flatnonzero(sl[bar_row]) + x0
            self.assertGreater(at_bar.size, 0, k)
            self.assertGreater(float(at_bar.mean()), gx, k)

    @slow
    def test_the_visible_shaft_has_at_least_three_wood_tones(self):
        tones = {tuple(int(v) for v in c) for c in hr.wood_cols()}
        for k, c in self.cells.items():
            spr, off = c["sprite"], c["offsets"]
            x0, y0 = hr.hs.place(spr, off, bar=False)
            vis = c["axe_mask"] & ~hr._hand_mask(spr.shape[:2], c["hand"], c["hand_xy"], x0, y0)
            cols = {tuple(int(v) for v in px) for px in spr[vis][:, :3]}
            self.assertGreaterEqual(len(cols & tones), 3, k)
            self.assertTrue(cols <= tones, k)


@unittest.skipIf(hr is None, "art tooling (numpy, Pillow) not installed")
@unittest.skipUnless(hr is not None and hr.PPSH_REF.is_file() and hr.hs.IWAD.is_file(),
                     "the Gemini PPSh render or the IWAD is not here (both gitignored)")
class PpshSilhouetteTest(unittest.TestCase):
    """D77: the PPSh-41 silhouette from the CEO's Gemini render (never shipped)."""

    @slow
    def test_chaingun_envelope_from_the_bottom_centre_right(self):
        mask = hr.ppsh_mask()
        base = hr.ppsh_height_above_bar()
        for k in hr.PPSH_SIZES:
            scr = hr.ppsh_screen(mask, base * k)
            rows, cols = np.flatnonzero(scr.any(1)), np.flatnonzero(scr.any(0))
            self.assertLessEqual(abs((hr.hs.VIEW_H - rows[0]) - base * k), 1.5, k)
            self.assertEqual(rows[-1], hr.hs.VIEW_H - 1, k)                 # it enters from the bottom
            self.assertTrue(hr.SCREEN_W / 2 <= (cols[0] + cols[-1]) / 2 <= 216, k)
            self.assertLess(cols[-1], hr.SCREEN_W - 1, k)                  # the right sleeve leaves under the bar


@unittest.skipIf(hr is None, "art tooling (numpy, Pillow) not installed")
class PpshCleanTest(unittest.TestCase):
    """D77b: the PPSh-41 redrawn as clean shapes (no reference needed: pure geometry)."""

    @classmethod
    def setUpClass(cls):
        cls.scr = hr.ppsh_clean_screen()
        pad = np.pad(cls.scr, 1, constant_values=False)
        cls.holes = (~cls.scr) & ~hr.component(~pad, (0, 0))[1:-1, 1:-1]
        mask = hr.ppsh_clean_mask()
        cls.slots = hr.ppsh_slot_cells(mask, hr.PPSH_CHGG_HEIGHT * hr.PPSH_CLEAN_SIZE)
        parts = hr.ppsh_clean_parts()
        cls.hands = {k: hr.ppsh_screen(parts[k], hr.PPSH_CHGG_HEIGHT * hr.PPSH_CLEAN_SIZE)
                     for k in ("left", "right")}
        # ppsh_screen scales by the mask's own top row: rescale the hands with the whole mask's transform
        s_, ox, oy, nw, nh = hr.ppsh_transform(mask, hr.PPSH_CHGG_HEIGHT * hr.PPSH_CLEAN_SIZE)
        for k in ("left", "right"):
            img = hr.Image.fromarray(parts[k][:hr.PPSH_HUD_Y].astype(np.float32), "F")
            small = np.asarray(img.resize((nw, nh), hr.Image.Resampling.BOX)) >= hr.COVER
            out = np.zeros_like(cls.scr)
            ys, xs = np.nonzero(small)
            ok = (ys + oy < out.shape[0]) & (xs + ox < out.shape[1]) & (xs + ox >= 0)
            out[ys[ok] + oy, xs[ok] + ox] = True
            cls.hands[k] = out

    def test_the_only_holes_are_the_jacket_slots(self):
        slot_px = {(y, x) for slot in self.slots for x, y in slot}
        holes = set(zip(*np.nonzero(self.holes)))
        self.assertEqual(holes, slot_px)

    def test_no_hole_inside_the_hands(self):
        for k, hand in self.hands.items():
            self.assertTrue(hand.any(), k)
            self.assertFalse((self.holes & hand).any(), k)

    def test_slots_evenly_spaced_along_the_jacket(self):
        d = np.array(hr.PPSH_BORE_D) / np.hypot(*hr.PPSH_BORE_D)
        centres = [np.mean([x * d[0] + y * d[1] for x, y in slot]) for slot in self.slots]
        gaps = np.diff(centres)
        self.assertEqual(len(self.slots), hr.PPSH_SLOTS[2])
        self.assertLessEqual(float(gaps.max() - gaps.min()), 1.0)
        for slot in self.slots:                                         # each one a hole in the gun, not cut open
            for x, y in slot:
                self.assertTrue(self.holes[y, x])

    def test_x16_the_chaingun_from_the_bottom(self):
        rows = np.flatnonzero(self.scr.any(1))
        self.assertLessEqual(abs((hr.hs.VIEW_H - rows[0]) - hr.PPSH_CHGG_HEIGHT * hr.PPSH_CLEAN_SIZE), 1.5)
        self.assertEqual(rows[-1], hr.hs.VIEW_H - 1)


if __name__ == "__main__":
    unittest.main()
