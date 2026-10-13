"""Contract of tools/art/gen_storm.py (F5, Stormtrooper and Reich hound sweeps, D35).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  cells      4-5 cells per enemy, unique keys, the BESTIARY sprite names
  rig        appending the new materials never moves one of gen_rig's ids
  faction    no military_green in either enemy; no flag_red on the hound
             outside its forbidden list (BESTIARY §6: no red at all)
  leg        the three-segment hind leg keeps its bone lengths and puts the
             knee forward and the hock behind the paw

The render tests run under `tools/verify.py art`, not `fast`
(SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is a palette.json colour, alpha hard 0/255
  storm      Doom's 56-unit actor; the recommended cell's Legion share from
             the front is under BESTIARY §5's 25 %
  hound      a horizontal bar under 40 px tall, no red pixel, a black
             bottom edge (BESTIARY §10 rule 4)
  seed       the same sprite renders identically twice
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_storm.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the storm and hound renders")


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class CheapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_rig
        cls.before = dict(gen_rig.MAT_ID)        # whatever was registered before this import
        import gen_storm
        cls.rig, cls.g = gen_rig, gen_storm

    def test_cells(self):
        g = self.g
        for cells in (g.STORM_CELLS, g.HOUND_CELLS):
            self.assertTrue(4 <= len(cells) <= 5)
            self.assertEqual(len({c.key for c in cells}), len(cells))
        self.assertIn(g.STORM_RECOMMENDED, g.STORM)
        self.assertIn(g.HOUND_RECOMMENDED, g.HOUND)
        self.assertEqual((g.STORM_SPRITE, g.HOUND_SPRITE), ("SDHS", "SDHN"))
        self.assertRegex(g.lump(g.STORM_SPRITE, "A", "G", 1), r"^SDHS_A_G1$")

    def test_registration_appends_only(self):
        rig, g = self.rig, self.g
        for name, i in self.before.items():
            self.assertEqual(rig.MAT_ID[name], i, name)
        for name in g.NEW_MATERIALS:
            self.assertEqual(rig.MAT_NAMES[rig.MAT_ID[name]], name)
        g.register_materials()                   # idempotent
        self.assertEqual(len(rig.MAT_NAMES), len(set(rig.MAT_NAMES)))

    def _ramps(self, prims):
        return {self.rig.MATERIALS[p.mat].ramp for p in prims}

    def test_faction_colours(self):
        g = self.g
        for c in g.STORM_CELLS:
            for pose in ("idle", "attack"):
                self.assertNotIn("military_green", self._ramps(g.storm_model(c, pose)), c.key)
        for c in g.HOUND_CELLS:
            for pose in ("idle", "bite"):
                ramps = self._ramps(g.hound_model(c, pose))
                self.assertNotIn("military_green", ramps, c.key)
                self.assertNotIn("flag_red", ramps, c.key)

    def test_hind_leg(self):
        g = self.g
        hip, paw = g.V(3, 20.5, -17), g.V(3, g.PAW_Y, -19.5)
        knee, hock, end = g.three_bone_hind(hip, paw)
        self.assertAlmostEqual(float(np.linalg.norm(knee - hip)), g.HIND_FEMUR, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(hock - knee)), g.HIND_TIBIA, places=6)
        self.assertTrue(np.allclose(end, paw))
        self.assertGreater(knee[2], hip[2] - 1e-9)       # the knee points forward
        self.assertLess(hock[2], paw[2])                 # the hock sits behind the paw


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_storm
        cls.g = gen_storm
        cls.storm, cls.storm_mat = gen_storm.render_storm(gen_storm.STORM_RECOMMENDED, "A", 1)
        cls.hound, _ = gen_storm.render_hound(gen_storm.HOUND_RECOMMENDED, "A", 3)
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        ramps = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
        cls.red, cls.green = ramps["flag_red"], ramps["military_green"]

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for rgba in (self.storm, self.hound):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.palette)
            self.assertFalse(self.opaque(rgba) & self.green)

    def test_storm_scale_and_legion_share(self):
        g = self.g
        self.assertEqual(self.storm.shape, (g.STORM_CV.h, g.STORM_CV.w, 4))
        m = g.measure(self.storm)
        self.assertLessEqual(abs(m["height_px"] - g.rig.DOOM_HEIGHT), 4)
        self.assertLessEqual(g.legion_fraction(self.storm_mat), g.LEGION_MAX)
        self.assertGreater(g.legion_fraction(self.storm_mat), 0.05)     # the graft is there

    def test_hound_is_a_low_bar_without_red(self):
        g = self.g
        m = g.measure(self.hound)
        self.assertLess(m["height_px"], g.HOUND_MAX_H)
        self.assertGreater(m["width_px"], 1.5 * m["height_px"])
        self.assertLessEqual(abs(m["lowest_row"] - g.HOUND_CV.foot_row), 1)
        self.assertFalse(self.opaque(self.hound) & self.red)
        self.assertGreater(g.belly_black_share(self.hound), 0.5)

    def test_deterministic(self):
        again, _ = self.g.render_hound(self.g.HOUND_RECOMMENDED, "A", 3)
        self.assertTrue(np.array_equal(again, self.hound))


if __name__ == "__main__":
    unittest.main()
