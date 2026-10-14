"""Contract of tools/art/gen_hands_2d.py (F4, D48: the sergeant's hand drawn
in 2D over our rendered weapons, a trial against the 3D capsule hand).

What is checked:

  no font      the module never rasterises text with a system font
  no edit      gen_weapon.draw_grip is swapped only inside handless() and
               is restored afterwards, even when the render raises
  freedoom     Freedoom's sprites are read only by the sheet builder, so no
               Freedoom pixel can reach a sprite (static check)
  palette      every opaque pixel of a 2D-hand frame is a palette.json
               colour, alpha is hard 0/255
  handless     the re-rendered weapon carries no hand material (glove,
               sleeve, telnyashka, cuff button): the 3D hand really is gone
  hand drawn   the 2D frame adds the hand: style E's sleeve green and both
               telnyashka stripe colours appear where the forearm shows
  placement    a frame reaches the bottom of the 320x200 weapon space and
               its grAb offsets follow Doom's arithmetic
  seed         the same frame renders identically twice
  designs      every weapon has one drawing per grip its pose records

The renders (three frames, about two seconds) are skipped under
SD_SKIP_SLOW_ART, as verify.py fast sets it; the static checks always run.
"""

from __future__ import annotations

import ast
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

SOURCE = ART_TOOLS / "gen_hands_2d.py"
SLOW_SKIPPED = bool(os.environ.get("SD_SKIP_SLOW_ART"))
SCREEN_H = 200
WEAPONTOP = 32


class StaticTests(unittest.TestCase):
    def setUp(self):
        self.code = SOURCE.read_text(encoding="utf-8")

    def test_no_system_font(self):
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, self.code), pattern)

    def test_freedoom_only_on_the_sheet(self):
        tree = ast.parse(self.code)
        callers = set()
        for fn in ast.walk(tree):
            if isinstance(fn, ast.FunctionDef):
                for node in ast.walk(fn):
                    if isinstance(node, ast.Attribute) and node.attr in ("freedoom_sprite", "iwad_lumps"):
                        callers.add(fn.name)
        self.assertEqual(callers, {"build_sheet"})

    def test_gen_weapon_is_imported_not_written(self):
        self.assertNotRegex(self.code, r"gen_weapon\.py['\"]\s*\)\.write|open\([^)]*gen_weapon")


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class HandlessTests(unittest.TestCase):
    def test_draw_grip_restored(self):
        import gen_hands_2d as h
        import gen_weapon as gw
        original = gw.draw_grip
        with h.handless():
            self.assertIsNot(gw.draw_grip, original)
        self.assertIs(gw.draw_grip, original)
        with self.assertRaises(RuntimeError):
            with h.handless():
                raise RuntimeError("boom")
        self.assertIs(gw.draw_grip, original)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
@unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: skipping the 2D-hand renders")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_hands_2d as h
        import gen_weapon as gw
        cls.h, cls.gw = h, gw
        cls.frames = {}
        for weapon, (_, poses, _, _, _) in h.WEAPONS.items():
            cls.frames[weapon] = h.render_2d(weapon, poses[0])
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def colours(self, rgba) -> set:
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for weapon, (f2, _, _) in self.frames.items():
            with self.subTest(weapon=weapon):
                self.assertTrue(set(np.unique(f2.rgba[..., 3])) <= {0, 255})
                self.assertLessEqual(self.colours(f2.rgba), self.palette)

    def test_handless_has_no_hand(self):
        hand_mats = {self.gw.MAT_ID[m] for m in
                     ("glove_brown", "glove_black", "skin", "sleeve_field", "sleeve_coat", "sleeve_quilt",
                      "tel_white", "tel_blue", "button")}
        for weapon, (_, bare, _) in self.frames.items():
            with self.subTest(weapon=weapon):
                self.assertFalse(set(np.unique(bare.mat).tolist()) & hand_mats)

    def test_hand_is_drawn(self):
        for weapon, (_, _, n) in self.frames.items():
            with self.subTest(weapon=weapon):
                self.assertGreater(n, 1500)
        f2 = self.frames["ice_axe"][0]          # the axe's idle shows the forearm
        got = self.colours(f2.rgba)
        for mat in ("sleeve_field", "tel_white", "tel_blue"):
            with self.subTest(material=mat):
                self.assertTrue(got & set(self.gw.MATERIALS[mat].colours()), mat)

    def test_placement(self):
        for weapon, (f2, _, _) in self.frames.items():
            with self.subTest(weapon=weapon):
                self.assertTrue(f2.hud)
                self.assertGreaterEqual(f2.top + f2.rgba.shape[0], SCREEN_H)
                lo, to = f2.offsets()
                self.assertEqual(f2.left, -lo)
                self.assertEqual(f2.top, WEAPONTOP - to)

    def test_seed(self):
        f2 = self.frames["tt33"][0]
        again = self.h.render_2d("tt33", self.h.WEAPONS["tt33"][1][0])[0]
        self.assertTrue(np.array_equal(f2.rgba, again.rgba))
        self.assertEqual((f2.left, f2.top), (again.left, again.top))

    def test_one_design_per_grip(self):
        for weapon, (_, poses, fn, dkey, _) in self.h.WEAPONS.items():
            with self.subTest(weapon=weapon):
                with self.h.handless() as grips:
                    fn(self.gw.HAND[self.h.STYLE_KEY], poses[0])
                self.assertEqual(len(grips), len(self.h.DESIGNS[dkey]))


if __name__ == "__main__":
    unittest.main()
