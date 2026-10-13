"""Contract of tools/art/gen_enemy.py (F5, Reich rifleman design sweep).

Cheap on purpose: renders two sprites, never the sheet. What is checked:

  palette    every opaque pixel is a palette.json colour, alpha is hard 0/255
  faction    no military_green on a Reich figure (ART-BIBLE §6.2)
  scale      the figure is about Doom's 56-unit actor, inside a 48x64 canvas
  armband    the D12 stamp lands whole on the sprite
  seed       the same cell renders identically twice
  no font    the generator never rasterises text with a system font
"""

from __future__ import annotations

import json
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

SOURCE = ART_TOOLS / "gen_enemy.py"


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        # the docstring may NAME ImageFont; code may not import or call it
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class SpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_enemy
        cls.g = gen_enemy
        cls.idle = gen_enemy.render(gen_enemy.CELL["A"], "idle")
        cls.fire = gen_enemy.render(gen_enemy.CELL["E"], "fire")
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        cls.green = {tuple(c) for r in pal["ramps"] if r["name"] == "military_green" for c in r["colours"]}

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for rgba in (self.idle, self.fire):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.palette)

    def test_no_military_green(self):
        for rgba in (self.idle, self.fire):
            self.assertFalse(self.opaque(rgba) & self.green)

    def test_scale(self):
        self.assertEqual(self.idle.shape, (self.g.H, self.g.W, 4))
        m = self.g.measure(self.idle)
        self.assertLessEqual(abs(m["height_px"] - self.g.DOOM_HEIGHT), 3)

    def test_armband_whole(self):
        x0, y0 = self.g.armband_anchor(self.g.arm_pose(self.g.CELL["A"], "idle")[1])
        band = self.idle[y0:y0 + 7, x0:x0 + 7]
        self.assertEqual(band.shape[:2], (7, 7))
        self.assertTrue((band[..., 3] == 255).all())

    def test_deterministic(self):
        again = self.g.render(self.g.CELL["A"], "idle")
        self.assertTrue(np.array_equal(again, self.idle))


if __name__ == "__main__":
    unittest.main()
