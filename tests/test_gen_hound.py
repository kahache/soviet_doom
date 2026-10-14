"""Contract of tools/art/gen_hound.py (F5, the Reich hound as a German shepherd, D48).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  cells      3-4 cells, unique keys, the recommended one among them, the
             BESTIARY sprite name, the frame plan (gallop A-D, bite E-G at
             rotations 1, 3, 5)
  materials  each cell's table is a COPY of rig_core's: no base id moves,
             rig_core.MATERIALS is untouched; no military_green anywhere;
             flag_red only inside the mouth (BESTIARY §6, D48)
  breed      the anatomy D48 asks for, measured on the posed skeleton and
             primitives: the withers above the sacrum (sloping top line),
             the hind paw behind the hip (angulation), the ears the highest
             point and erect, the head ahead of the withers, the tail hung
             below the croup, a black saddle and a collar with a steel tag;
             the graft only on cell D, symmetric (mirror mode stays valid)
  canvas     the axis is centred (mirror mode)

The render tests run under `tools/verify.py art`, not `fast`
(SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is a palette.json v1 colour, alpha hard 0/255
  height     side and front under BESTIARY §6's 40 px
  red        no red pixel in a gallop frame; the open mouth may show some
  brown      the profile is mostly tan (it reads brown) with a black saddle
  mirror     rotation 7 is rotation 3 flipped, exactly
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

SOURCE = ART_TOOLS / "gen_hound.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the German shepherd renders")


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
        import rig_core
        cls.base_before = list(rig_core.MATERIALS)
        import gen_hound
        cls.g, cls.core = gen_hound, rig_core

    def model(self, key="A", frame="C"):
        return self.g.gsd_model(self.g.CELL[key], frame)

    def test_cells_and_plan(self):
        g = self.g
        self.assertTrue(3 <= len(g.CELLS) <= 4)
        self.assertEqual(len(g.CELL), len(g.CELLS))
        self.assertIn(g.RECOMMENDED, g.CELL)
        self.assertEqual(g.SPRITE, "SDHN")
        plan = g.frame_plan()
        self.assertEqual({f for f, _ in plan}, set("ABCDEFG"))
        self.assertEqual({r for _, r in plan}, {1, 3, 5})

    def test_materials_are_a_copy(self):
        g, core = self.g, self.core
        self.assertEqual(list(core.MATERIALS), self.base_before)
        for c in g.CELLS:
            table = g.materials_for(c)
            self.assertEqual(list(table)[:len(self.base_before)], self.base_before)
            for name in ("tan", "cream", *g.FIXED_MATERIALS):
                self.assertIn(name, table)
        self.assertEqual(list(core.MATERIALS), self.base_before)

    def test_faction_colours(self):
        g = self.g
        for c in g.CELLS:
            table = g.materials_for(c)
            used = {p.mat for f in ("C", "F") for p in g.gsd_model(c, f)}
            for name in used:
                self.assertNotIn("military_green", table[name].ramps, name)
                if "flag_red" in table[name].ramps:
                    self.assertIn(name, g.RED_MATERIALS)

    def test_red_only_when_the_mouth_is_open(self):
        for f in "ABCD":
            self.assertFalse([p for p in self.model("A", f) if p.mat == "mouth"], f)
        self.assertTrue([p for p in self.model("A", "F") if p.mat == "mouth"])

    def test_breed_skeleton(self):
        g, core = self.g, self.core
        rigs = [core.pose_quadruped(g.GSD_BUILD, core.QuadPose("A", "gallop", k / 8)) for k in range(8)]
        # over a stride (the gallop pitches the body) the withers ride above the sacrum
        withers_y = np.mean([q.spine[-1][1] for q in rigs])
        sacrum_y = np.mean([q.spine[0][1] for q in rigs])
        self.assertGreater(withers_y, sacrum_y + 2.0, "the top line slopes down to the croup")
        for leg in ("hl", "hr"):
            # over a whole stride the hind paw works behind the hip: the breed's angulation
            paw_z = np.mean([q.legs[leg][3][2] for q in rigs])
            hip_z = np.mean([q.legs[leg][0][2] for q in rigs])
            self.assertLess(paw_z, hip_z - 2.0, "angulation: the hind paw behind the hip")

    def test_breed_shapes(self):
        P = self.model("A", "C")
        def top(p):
            c, r = p.bound()
            return c[1] + r
        ears = [p for p in P if p.kind == "cappedcone" and p.grp == "head"]
        self.assertEqual(len(ears), 2)
        for e in ears:
            axis = e.xm @ e.rot @ np.array([0.0, 1.0, 0.0])
            self.assertGreater(axis[1], 0.7, "erect: the ear points up")
        head_z = max(p.bound()[0][2] for p in P if p.grp == "head")
        body_z = max(p.bound()[0][2] for p in P if p.grp == "body")
        self.assertGreater(head_z, body_z)
        tail = [p for p in P if p.grp == "tail"]
        self.assertTrue(tail)
        tip = min(tail, key=lambda p: p.bound()[0][2])
        croup = [p for p in P if p.grp == "body"]
        self.assertLess(tip.bound()[0][2], min(p.bound()[0][2] for p in croup))
        self.assertTrue(any(p.mat == "saddle" and p.grp == "body" for p in P), "the black blanket")
        self.assertTrue([p for p in P if p.tag == "collar"])
        self.assertTrue([p for p in P if p.tag == "tag" and p.mat == "steel"])
        self.assertLess(max(top(p) for p in P), self.g.MAX_H + 2)

    def test_graft_only_on_d_and_symmetric(self):
        g = self.g
        for c in g.CELLS:
            P = g.gsd_model(c, "C")
            scars = [p for p in P if p.mat == "scar"]
            self.assertEqual(bool(scars), c.graft, c.key)
            if c.graft:
                xs = sorted(round(float(p.bound()[0][0]), 1) for p in scars)
                self.assertEqual(xs, sorted(-x for x in xs), "graft symmetric about the axis")

    def test_canvas_axis_centred(self):
        self.assertEqual(self.g.CV.cx * 2, self.g.CV.w)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("SD_SKIP_SLOW_ART"):
            raise unittest.SkipTest("SD_SKIP_SLOW_ART is set")
        import gen_hound
        cls.g = gen_hound
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        rec = gen_hound.CELL[gen_hound.RECOMMENDED]
        cls.spr = {(f, r): gen_hound.render(rec, f, r) for f, r in (("C", 3), ("A", 1), ("F", 3))}

    @staticmethod
    def opaque(rgba):
        a = rgba[..., 3] > 0
        return {tuple(int(v) for v in c) for c in rgba[..., :3][a]}

    @staticmethod
    def height(rgba):
        ys = np.nonzero(rgba[..., 3] > 0)[0]
        return int(ys.max() - ys.min() + 1)

    @slow
    def test_palette_and_hard_alpha(self):
        for k, rgba in self.spr.items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, k)
            self.assertLessEqual(self.opaque(rgba), self.palette, k)

    @slow
    def test_height(self):
        self.assertLess(self.height(self.spr[("C", 3)]), self.g.MAX_H)
        self.assertLess(self.height(self.spr[("A", 1)]), self.g.MAX_H)

    @slow
    def test_red_only_in_the_mouth(self):
        import rig_core as core
        red = set(core.ramp("flag_red"))
        self.assertFalse(self.opaque(self.spr[("C", 3)]) & red)
        self.assertFalse(self.opaque(self.spr[("A", 1)]) & red)
        bite = self.spr[("F", 3)]
        a = bite[..., 3] > 0
        n_red = sum(1 for c in bite[..., :3][a] if tuple(int(v) for v in c) in red)
        self.assertLess(n_red / a.sum(), 0.03)

    @slow
    def test_reads_brown_with_a_black_saddle(self):
        m = self.g.metrics_for(self.g.CELL[self.g.RECOMMENDED],
                               {**self.spr, ("A", 1): self.spr[("A", 1)]})
        self.assertGreater(m["tan_share"], 0.5)
        self.assertGreater(m["saddle_share"], 0.15)

    @slow
    def test_mirror_and_seed(self):
        g = self.g
        rec = g.CELL[g.RECOMMENDED]
        again = g.render(rec, "C", 3)
        self.assertTrue(np.array_equal(again, self.spr[("C", 3)]))
        seven = g.render(rec, "C", 7)
        self.assertTrue(np.array_equal(seven, self.spr[("C", 3)][:, ::-1]))


if __name__ == "__main__":
    unittest.main()
