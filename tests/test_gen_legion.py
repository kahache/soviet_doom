"""Contract of tools/art/gen_legion.py (F5, Liberty Legion trooper design sweep, D35).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  ramp       the candidate flesh ramp is palette.py's rule, 16 new colours,
             none of them already in palette v1, and v1 + it fits 256
  cells      six cells, A is the brief, every lump name fits Doom's 8 chars
  flag       the D12 flag stamp is 7x5 and mirrors so the canton leads

The render tests run under `tools/verify.py art`, not `fast` (each sprite
is a sphere trace of a few seconds; SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is palette v1 or the candidate ramp, hard alpha
  faction    no military_green (the world's), no khaki_olive (the Reich's);
             the only flag_red is the flag; the body is LIGHTER than concrete
  scale      the standing figure is Doom's 56-unit actor
  flash      frame F carries the muzzle flash
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

SOURCE = ART_TOOLS / "gen_legion.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the Legion renders")


def palette_ramps() -> dict:
    pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
    return pal, {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)

    def test_palette_json_is_not_written(self):
        code = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("PALETTE_JSON", code)
        self.assertIsNone(re.search(r"palette\.json[^\n]*write", code))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class CheapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_legion
        cls.g = gen_legion

    def test_flesh_ramp_is_new_and_fits(self):
        g = self.g
        pal, _ = palette_ramps()
        ramp = g.flesh_ramp()
        self.assertEqual(len(ramp), 16)
        self.assertEqual(ramp[0], g.FLESH_DARK)
        self.assertEqual(ramp[-1], g.FLESH_LIGHT)
        lum = [0.299 * r + 0.587 * gg + 0.114 * b for r, gg, b in ramp]
        self.assertEqual(lum, sorted(lum))                      # darkest first, like every ramp
        v1 = {tuple(c) for c in pal["colours"]}
        self.assertFalse(set(ramp) & v1)
        self.assertLessEqual(len(v1) + len(set(ramp)), 256)
        for r, gg, b in ramp[4:]:
            self.assertGreater(r, b)                            # flesh, not grey or blue

    def test_cells_and_names(self):
        g = self.g
        self.assertEqual([c.key for c in g.CELLS], list("ABCDEF"))
        a = g.CELL["A"]
        self.assertEqual((a.face, a.torso, a.shoulders), ("smooth", "cuirass", "pauldron"))
        self.assertIn(g.RECOMMENDED, g.CELL)
        for c in g.CELLS:
            for frame, rot in g.VIEWS:
                lump = g.lump_name(c, frame, rot).replace(f"_{c.key}_", "")
                self.assertRegex(lump, r"^SDLT[A-U][0-8]$")
                self.assertLessEqual(len(lump), 8)

    def test_flag_mirrors_canton_first(self):
        g = self.g
        self.assertEqual({len(r) for r in g.FLAG}, {7})
        self.assertEqual(len(g.FLAG), 5)
        blue = g.artlib.ramp("steel_blue")[3]
        plain = {(i, j): c for i, j, c in g.flag_pixels(False)}
        mirror = {(i, j): c for i, j, c in g.flag_pixels(True)}
        self.assertEqual(plain[(0, 0)], blue)
        self.assertEqual(mirror[(6, 0)], blue)
        for (i, j), c in plain.items():
            self.assertEqual(mirror[(6 - i, j)], c)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_legion
        g = cls.g = gen_legion
        cls.idle = g.render(g.CELL["A"], "A", 1)
        cls.fire = g.render(g.CELL[g.RECOMMENDED], "F", 1)
        pal, ramps = palette_ramps()
        cls.allowed = {tuple(c) for c in pal["colours"]} | set(g.flesh_ramp())
        cls.ramps = ramps

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for rgba in (self.idle, self.fire):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.allowed)

    def test_faction_contract(self):
        for rgba in (self.idle, self.fire):
            cols = self.opaque(rgba)
            self.assertFalse(cols & self.ramps["military_green"])
            self.assertFalse(cols & self.ramps["khaki_olive"])
            self.assertTrue(cols & set(self.g.flesh_ramp()))
        red = self.ramps["flag_red"]
        flag_red = {self.g.artlib.ramp(n)[k] for n, k in self.g.FLAG_COLOURS.values()} & red
        self.assertTrue(self.opaque(self.idle) & flag_red)      # the D12 flag is on the front view

    def test_lighter_than_concrete(self):
        g = self.g
        m = g.measure(self.idle)
        concrete = float(g.flat.luma(g.wall_rgb("SDCONC1")).mean())
        self.assertGreater(m["mass_luma"], concrete + 20)       # BESTIARY §2.1: the light faction
        self.assertGreater(m["body_luma"], concrete)

    def test_scale_and_canvas(self):
        g = self.g
        self.assertEqual(self.idle.shape, (g.STAND.h, g.STAND.w, 4))
        self.assertLessEqual(abs(g.measure(self.idle)["height_px"] - g.DOOM_HEIGHT), 4)

    def test_fire_has_flash(self):
        cols = self.opaque(self.fire)
        self.assertTrue(cols & (self.ramps["cream_yellow"] | self.ramps["hazard_yellow"]))
        self.assertFalse(self.opaque(self.idle) & self.ramps["hazard_yellow"])

    def test_deterministic(self):
        again = self.g.render(self.g.CELL["A"], "A", 1)
        self.assertTrue(np.array_equal(again, self.idle))


if __name__ == "__main__":
    unittest.main()
