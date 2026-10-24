"""tools/art/gen_rgd5_pickups.py: the RGD-5's world sprites (V3, D120).

The pure steps on synthetic arrays (upright, sized, paste behind the walls,
the pickup offsets); then, only where the Gemini pickup image is present
(work/art/reference/ is gitignored, D77), the four lumps rendered: their
sizes, bottom-centre offsets, hard alpha and palette v2.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    import gemini_frames as gf
    import gen_rgd5_pickups as rp
except ImportError:  # pragma: no cover - the art venv is missing
    rp = None


@unittest.skipIf(rp is None, "numpy/Pillow not installed (art venv)")
class PureTests(unittest.TestCase):
    def test_upright_puts_the_fuse_on_top(self):
        art = np.full((3, 5), gf.TRANSPARENT, np.int32)
        art[:, :4] = 1
        art[1, 4] = 2                                   # the fuse, at the right
        up = rp.upright(art)
        self.assertEqual(up.shape, (5, 3))
        self.assertEqual(up[0, 1], 2)

    def test_sized_squashes_rows_by_the_pixel_aspect(self):
        art = np.ones((60, 120), np.int32)
        self.assertEqual(rp.sized(art, 24).shape, (10, 24))           # 12 / 1.2
        self.assertEqual(rp.sized(art, 24, 1.0).shape, (12, 24))

    def test_paste_stays_behind_the_walls(self):
        rgba = np.zeros((6, 6, 4), np.uint8)
        keep = np.zeros((6, 6), bool)
        keep[3:] = True                                 # the front wall
        rp.paste(rgba, np.full((4, 2), 3, np.int32), (3, 3), keep)
        self.assertTrue((rgba[1:3, 2:4, 3] == 255).all())
        self.assertFalse(rgba[3:, ..., 3].any())

    def test_pickup_frame_stands_on_its_lowest_pixel(self):
        rgba = np.zeros((20, 30, 4), np.uint8)
        rgba[5:12, 4:14, 3] = 255
        f = rp.pickup_frame(rgba)
        self.assertEqual(f.rgba.shape[:2], (7, 10))
        self.assertEqual(f.offsets(), (5, 7))


@unittest.skipIf(rp is None or not rp.SOURCE.is_file(), "the Gemini pickup image is local (D77)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = rp.render_all()

    def test_four_lumps_in_palette_v2_with_hard_alpha(self):
        lut = {tuple(c) for c in gf.palette_rgb().tolist()}
        self.assertEqual(sorted(self.frames), sorted(rp.LUMPS))
        for lump, f in self.frames.items():
            with self.subTest(lump=lump):
                self.assertTrue(set(np.unique(f.rgba[..., 3]).tolist()) <= {0, 255})
                self.assertTrue({tuple(c) for c in f.rgba[f.rgba[..., 3] > 0][:, :3].tolist()} <= lut)
                h, w = f.rgba.shape[:2]
                self.assertEqual(f.offsets(), (w // 2, h))     # bottom-centre, as every pickup

    def test_sizes(self):
        w = {k: f.rgba.shape[1] for k, f in self.frames.items()}
        self.assertEqual(w["SDRJA0"], rp.LOOSE_W)
        self.assertLess(w["SDRNA0"], w["SDRJA0"])             # smaller in the air
        self.assertLess(w["SDRJA0"], w["SDRQA0"])             # one grenade < the pouch < the crate
        self.assertLess(w["SDRQA0"], w["SDRZA0"])
        self.assertLess(w["SDRZA0"], 52)                      # smaller than the PG-7V crate SDRB


if __name__ == "__main__":
    unittest.main()
