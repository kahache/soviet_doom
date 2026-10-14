"""tools/art/hand_ref.py: the ice axe's held frame derived from the CEO's
reference images (N14 / N4 round 3), a sweep for review.

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
    def test_cells_sweep_the_brief(self):
        self.assertTrue(4 <= len(hr.CELLS) <= 6)
        self.assertEqual({c.ref for c in hr.CELLS}, set(hr.REFS))
        self.assertEqual({c.size for c in hr.CELLS}, {0.85, 1.0, 1.15})
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

    def test_shade_wood_moves_only_wood(self):
        ramp = hr.artlib.ramp(hr.WOOD_RAMP)
        cols = np.array([ramp[8], (1, 2, 3)], np.uint8)
        out = hr.shade_wood(cols, hr.FIST_SHADE)
        self.assertEqual(tuple(out[0]), tuple(ramp[8 - hr.FIST_SHADE]))
        self.assertEqual(tuple(out[1]), (1, 2, 3))


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
            self.assertGreaterEqual((x0 + x1) / 2, hr.SCREEN_W / 2 - 10, k)     # centre-right ...
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


if __name__ == "__main__":
    unittest.main()
