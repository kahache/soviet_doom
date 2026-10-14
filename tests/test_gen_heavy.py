"""Contract of tools/art/gen_heavy.py (F5, D35: the Doughboy and Panzermensch
design sweeps, and the Schwer's two candidates).

Cheap tests (no rendering, always run):

  no font     the generator never rasterises text and never writes palette.json
  cells       four cells per enemy, A is the brief; views are rotations 1, 3,
              5 and the attack; the lump names they stand for fit Doom's 8
  tables      both material tables are COPIES of the approved figures'
              (gen_legion, gen_rig): every approved id is where it was, and
              the approved tables are untouched
  faction     no Doughboy material uses the Reich's khaki_olive or the
              world's military_green; no Panzermensch material uses the
              Legion's steel_blue or flesh_pink; blood is dark red (D49)
  scale       scale_prims scales a primitive about the origin exactly

Render tests (`tools/verify.py art`; SD_SKIP_SLOW_ART skips them):

  palette     every opaque pixel is a palette v2 colour, hard alpha
  faction     the rendered colours keep the contract above
  size        the Doughboy fills its 31-radius hitbox; the Panzermensch is
              taller than the 56-unit infantry and close to BOS2's 69
  insignia    the banner (D12) shows from the back, not the front; the
              Doughboy's flag decal shows from the front
  seed        the same sprite renders identically twice
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

SOURCE = ART_TOOLS / "gen_heavy.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the heavies' renders")


def ramp_sets() -> dict[str, set]:
    """Every ramp of palette v1 and v2 (v2's added ramps through palette.py)."""
    import palette as palgen
    pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
    out = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
    for name in ("flesh_pink", "marble_red", "mosaic_cobalt", "mosaic_gold"):
        out.setdefault(name, {tuple(c) for c in palgen.ramp_colours(name)})
    return out


class NoFontTests(unittest.TestCase):
    def test_no_system_font_and_no_palette_write(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\("):
            self.assertIsNone(re.search(pattern, code), pattern)
        self.assertNotIn("palette.json\").write", code)
        # assets/ is read (the approved sprites), never written: every save goes under OUT_DIR
        self.assertNotRegex(code, r"(SPRITES|TEXTURES|FLATS)\s*/[^\n]*\.save\(")


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_heavy
        import gen_legion
        import gen_rig
        cls.h, cls.legion, cls.rig = gen_heavy, gen_legion, gen_rig

    def test_cells_and_views(self):
        h = self.h
        self.assertEqual([c.key for c in h.DB_CELLS], list("ABCD"))
        self.assertEqual([c.key for c in h.PM_CELLS], list("ABCD"))
        self.assertTrue(h.DB_CELLS[0].title.startswith("Brief"))
        self.assertTrue(h.PM_CELLS[0].title.startswith("Brief"))
        self.assertEqual([r for _, r in h.DB_VIEWS], [1, 3, 5, 1])
        self.assertEqual([r for _, r in h.PM_VIEWS], [1, 3, 5, 1])
        self.assertEqual(h.DB_VIEWS[-1][0], "D")       # BESTIARY §7: SDDB D is the attack
        self.assertEqual(h.PM_VIEWS[-1][0], "G")       # BESTIARY §8: SDPM G is the attack
        for sprite, views in ((h.DB_SPRITE, h.DB_VIEWS), (h.PM_SPRITE, h.PM_VIEWS)):
            for f, r in views:
                self.assertLessEqual(len(f"{sprite}{f}{r}"), 8)
        self.assertIn(h.DB_RECOMMENDED, "ABCD")
        self.assertIn(h.PM_RECOMMENDED, "ABCD")
        for name in ("DB_VERDICT", "PM_VERDICT", "SCHWER_NOTE", "HONEST", "CEO_ASK"):
            self.assertTrue(getattr(h, name), name)

    def test_tables_are_copies_with_ids_kept(self):
        h = self.h
        for table, base in ((h.DB_MATERIALS, self.legion.MATERIALS), (h.PM_MATERIALS, self.rig.MATERIALS)):
            self.assertIsNot(table, base)
            self.assertEqual(list(table)[:len(base)], list(base))
            for name in base:
                self.assertEqual(table[name], base[name])
        for name in h.DB_NEW:
            self.assertNotIn(name, self.legion.MATERIALS)
        for name in h.PM_NEW:
            self.assertNotIn(name, self.rig.MATERIALS)

    def test_faction_materials(self):
        h = self.h
        for name, mat in h.DB_MATERIALS.items():
            self.assertFalse(mat.ramps & h.DB_FORBIDDEN_RAMPS, name)
        for name, mat in h.PM_NEW.items():
            self.assertFalse(mat.ramps & h.PM_FORBIDDEN_RAMPS, name)
        for table, name in ((h.DB_MATERIALS, "blood"), (h.PM_MATERIALS, "seep")):
            m = table[name]
            self.assertEqual(m.ramps, {"flag_red"})
            self.assertTrue(m.flat)
            self.assertLessEqual(max(s[2] for s in m.spans if s[0] == "flag_red"), 5)

    def test_scale_prims(self):
        h, core = self.h, self.h.core
        p = core.ellipsoid("plate", 0.5, (1.0, 10.0, 2.0), (3.0, 4.0, 5.0), clip=[(core.V(0, -1, 0), -9.0)])
        q = h.scale_prims([p], 2.0)[0]
        pts = np.array([[1.0, 14.0, 2.0], [7.0, 10.0, 2.0], [0.0, 0.0, 0.0]])
        np.testing.assert_allclose(q.sd(pts * 2.0), p.sd(pts) * 2.0, rtol=1e-9, atol=1e-9)
        self.assertEqual(p.a.tolist(), [1.0, 10.0, 2.0])     # the original is untouched


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_heavy as h
        cls.h = h
        cls.db = h.render_db(h.DB_RECOMMENDED, "A", 1)
        cls.db_attack = h.render_db(h.DB_RECOMMENDED, "D", 1)
        cls.pm = h.render_pm(h.PM_RECOMMENDED, "A", 1)
        cls.pm_back = h.render_pm(h.PM_RECOMMENDED, "A", 5)
        cls.ramps = ramp_sets()

    def colours(self, rgba):
        a = rgba[..., 3] > 0
        return {tuple(int(v) for v in p) for p in rgba[..., :3][a]}

    def test_palette_v2_and_hard_alpha(self):
        v2 = set(self.h.palette_v2())
        for rgba in (self.db, self.db_attack, self.pm, self.pm_back):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertTrue(self.colours(rgba) <= v2)

    def test_faction_colours(self):
        r = self.ramps
        for rgba in (self.db, self.db_attack):
            cols = self.colours(rgba)
            self.assertFalse(cols & (r["khaki_olive"] | r["military_green"]))
            self.assertTrue(cols & r["flesh_pink"])
        for rgba in (self.pm, self.pm_back):
            cols = self.colours(rgba)
            self.assertFalse(cols & (r["steel_blue"] | r["flesh_pink"] | r["military_green"]))

    def test_sizes(self):
        m = self.h.measure(self.db, self.h.DB_SCENES)
        self.assertGreaterEqual(m["width_px"], 48)       # fills a radius-31 hitbox (HEAD is 63 wide)
        p = self.h.measure(self.pm, self.h.PM_SCENES)
        self.assertGreater(p["height_px"], 60)           # taller than the 56-unit infantry
        self.assertLess(p["height_px"], 84)
        self.assertLess(p["body_luma"], 63)              # the darkest mass in the game (BESTIARY §2.1)

    def test_insignia_sides(self):
        red = self.ramps["flag_red"]
        black = (0, 0, 0)
        front, back = self.colours(self.pm), self.colours(self.pm_back)
        self.assertTrue(back & red)
        self.assertIn(black, back)
        self.assertFalse(front & red)                    # the banner is on his back
        self.assertTrue(self.colours(self.db) & red)     # the flag decal on the helmet

    def test_seed(self):
        np.testing.assert_array_equal(self.h.render_pm(self.h.PM_RECOMMENDED, "A", 1), self.pm)


if __name__ == "__main__":
    unittest.main()
