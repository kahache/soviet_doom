"""tools/art/gen_akm_pickup.py: the AKM's floor pickup SDAQ A0 (2026-10-24).

The held frames come from Gemini (tools/art/gemini_frames.py akm); the
pickup is drawn on gen_weapon's rig like every weapon pickup since D48.
Checked: it renders reproducibly, at the PPSh-41's pickup size (both rifles
are ~88 cm; SDPQA0 is the installed one), standing on its lowest pixel and
centred (gen_weapon.finish's pickup offsets), RGBA with hard alpha, inside
palette v2 and in it the held frames' reddish-brown (marble_red) with no
flag red; gen_weapon's material tables are the same after the render as
before (no id moves, so no other render moves); where work/ holds the
drawn lump, it is this render byte for byte.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    import gen_akm_pickup as gap
    import gen_weapon as gw
    import hand_study as hs
    import palette as palette_mod
except ImportError:  # pragma: no cover - the art venv is missing
    gap = None

PPSH_PICKUP = ROOT / "assets" / "sprites" / "ppsh" / "SDPQA0.png"
SIZE_SLACK = 0.15         # the AKM's pickup within 15 % of the PPSh's width
MIN_MARBLE = 0.3          # at least this share of its pixels is the laminate's reddish-brown


@unittest.skipIf(gap is None, "numpy/Pillow not installed (art venv)")
class AkmPickupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = (dict(gw.MATERIALS), dict(gw.MAT_ID), set(gw.METALS), set(gw.FLAT))
        cls.frame = gap.render_akm_pickup()
        cls.pal = [tuple(c) for c in palette_mod.colours(2)]

    def test_tables_restored(self):
        self.assertEqual((gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT), self.before)
        self.assertFalse(set(gap.AKM_MATERIALS) & set(gw.MATERIALS))

    def test_reproducible(self):
        again = gap.render_akm_pickup()
        self.assertTrue((again.rgba == self.frame.rgba).all())
        self.assertEqual(again.offsets(), self.frame.offsets())

    def test_size_and_offsets_like_the_ppshs(self):
        rgba = self.frame.rgba
        h, w = rgba.shape[:2]
        ppsh, _ = hs.read_png_sprite(PPSH_PICKUP)
        self.assertLess(abs(w - ppsh.shape[1]) / ppsh.shape[1], SIZE_SLACK)
        self.assertGreater(h, ppsh.shape[0])               # the magazine hangs under it
        self.assertEqual(tuple(int(v) for v in self.frame.offsets()), (w // 2, h))
        self.assertTrue(set(np.unique(rgba[..., 3]).tolist()) <= {0, 255})

    def test_palette_v2_reddish_brown_no_flag_red(self):
        rgba = self.frame.rgba
        cols = [tuple(c) for c in rgba[rgba[..., 3] > 0][:, :3].tolist()]
        self.assertTrue(set(cols) <= set(self.pal))
        marble = set(palette_mod.ramp_colours("marble_red"))
        flag = set(palette_mod.ramp_colours("flag_red"))
        self.assertGreater(sum(c in marble for c in cols) / len(cols), MIN_MARBLE)
        self.assertFalse(any(c in flag for c in cols))

    def test_written_with_grab(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gap.main(["--out", tmp]), 0)
            rgba, grab = hs.read_png_sprite(Path(tmp) / f"{gap.LUMP}.png")
        self.assertTrue((rgba == self.frame.rgba).all())
        self.assertEqual(grab, tuple(int(v) for v in self.frame.offsets()))

    def test_work_copy_is_this_render(self):
        path = gap.OUT_DIR / f"{gap.LUMP}.png"
        if not path.is_file():
            self.skipTest("work/ not present (gitignored)")
        rgba, grab = hs.read_png_sprite(path)
        self.assertTrue((rgba == self.frame.rgba).all())
        self.assertEqual(grab, tuple(int(v) for v in self.frame.offsets()))


if __name__ == "__main__":
    unittest.main()
