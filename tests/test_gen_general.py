"""Contract of tools/art/gen_general.py (F5, backlog N12: the General's design sweep).

Cheap tests (no rendering, always run):

  no font     the generator never rasterises text, never writes palette.json
              and never writes under assets/; the contact sheet's letters
              come from its own GLYPHS table
  cells       five cells, A is the brief; every other cell differs from A in
              exactly one dimension; views are rotations 1, 3, 5 and the
              firing frame F; the lump names fit Doom's 8
  table       the material table is a COPY of the Legion trooper's
              (gen_legion): every approved id is where it was, the approved
              table is untouched
  faction     no material uses the Reich's khaki_olive or the world's
              military_green (ART-BIBLE §6.2); the flags are the only
              saturated red (§6.3)
  insignia    the pennant carries the mod's one drawing of the D12 symbol
              (gen_enemy.ARMBAND) and the trooper's US flag, unmirrored; the
              cloak's disc has the same handedness as the armband
  scale       the canvas holds his 100-unit actor; the grAb is the body axis

Render tests (`tools/verify.py art`; SD_SKIP_SLOW_ART skips them):

  palette     every opaque pixel is a palette v2 colour, hard alpha
  faction     the rendered colours keep the contract above; flesh_pink shows
  size        he is drawn to his actor (90-100 px), far taller than the
              56-unit infantry and the approved Panzermensch
  value       he is a light figure, brighter than the approved Panzermensch
              (BESTIARY §9: bright; §8: the brute is the darkest mass)
  insignia    both flags show on the pennants from the front
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

SOURCE = ART_TOOLS / "gen_general.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the General's renders")


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
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(", r"ImageDraw"):
            self.assertIsNone(re.search(pattern, code), pattern)
        self.assertNotIn("palette.json\").write", code)
        # assets/ is read (approved sprites, MAP03's walls), never written
        self.assertNotRegex(code, r"ASSETS\s*/[^\n]*\.(save|write_text|write_bytes)\(")


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_enemy
        import gen_general
        import gen_legion
        cls.g, cls.legion, cls.enemy = gen_general, gen_legion, gen_enemy

    def test_cells_and_views(self):
        g = self.g
        self.assertEqual([c.key for c in g.CELLS], list("ABCDE"))
        a = g.CELLS[0]
        self.assertTrue(a.title.startswith("Brief"))
        self.assertEqual((a.face, a.weapon, a.flags, a.chest), ("plate", "revolver", "pennants", "cuirass"))
        for c in g.CELLS[1:]:
            diff = [f for f in ("face", "weapon", "flags", "chest") if getattr(c, f) != getattr(a, f)]
            self.assertEqual(len(diff), 1, c.key)
        self.assertEqual([r for _, r in g.VIEWS], [1, 3, 5, 1])
        self.assertEqual(g.VIEWS[-1][0], "F")           # general.zs: CYBR F fires (A_SD_GeneralShot)
        self.assertTrue(g.POSES["F"].fire)
        for f, r in g.VIEWS:
            self.assertLessEqual(len(f"{g.SPRITE}{f}{r}"), 8)
        self.assertEqual(g.SPRITE, "SDGN")
        self.assertIn(g.RECOMMENDED, "ABCDE")
        for name in ("VERDICT", "HONEST", "CEO_ASK"):
            self.assertTrue(getattr(g, name), name)
        self.assertLessEqual(set(c.key for c in g.CELLS), set(g.GLYPHS))

    def test_the_actor_is_read_from_the_class(self):
        zs = (PROJECT_ROOT / "src" / "zscript" / "monsters" / "general.zs").read_text(encoding="utf-8")
        self.assertIn(f"SD_GENERAL_HEIGHT     = {self.g.ACTOR_HEIGHT};", zs)
        self.assertIn(f"SD_GENERAL_RADIUS     = {self.g.ACTOR_RADIUS};", zs)

    def test_table_is_a_copy_with_ids_kept(self):
        g, base = self.g, self.legion.MATERIALS
        self.assertIsNot(g.GN_MATERIALS, base)
        self.assertEqual(list(g.GN_MATERIALS)[:len(base)], list(base))
        for name in base:
            self.assertEqual(g.GN_MATERIALS[name], base[name])
        for name in g.GN_NEW:
            self.assertNotIn(name, base)

    def test_faction_materials(self):
        g = self.g
        for name, mat in g.GN_MATERIALS.items():
            self.assertFalse(mat.ramps & g.FORBIDDEN_RAMPS, name)
        red = {n for n, m in g.GN_NEW.items() if "flag_red" in m.ramps}
        self.assertEqual(red, {"pennant_red"})          # the flags and nothing else (ART-BIBLE §6.3)

    def test_pennants_carry_the_mods_insignia(self):
        g = self.g
        self.assertEqual(g.PENNANT_REICH[:7], self.enemy.ARMBAND)
        self.assertEqual(g.PENNANT_US[:len(self.legion.FLAG)], self.legion.FLAG)
        for pat in (g.PENNANT_REICH, g.PENNANT_US, g.CLOAK_DISC, g.CANTON_STARS):
            self.assertEqual(len({len(r) for r in pat}), 1)
            self.assertTrue(set("".join(pat)) <= set(g.STAMP_COLOURS) | {"_"})
        tags = {i.tag for i in g.PENNANT_INSIGNIA}
        self.assertEqual(tags, {"pen_reich", "pen_us"})

    def test_cloak_disc_has_the_armbands_handedness(self):
        disc = self.g.CLOAK_DISC
        arm = [r[1:6] for r in self.enemy.ARMBAND[1:6]]          # the 5x5 symbol inside the band
        sym = [r[2:9] for r in disc[2:9]]                         # the 7x7 symbol inside the disc
        # same arms: the top row runs right from the centre, the bottom row left
        self.assertEqual(arm[0][0], "K")
        self.assertEqual(sym[0][0], "K")
        self.assertTrue(all(c == "K" for c in sym[0][3:]) and all(c == "K" for c in arm[0][2:]))
        self.assertTrue(all(c == "K" for c in sym[6][:4]) and all(c == "K" for c in arm[4][:3]))

    def test_canvas_and_grab(self):
        g = self.g
        gx, gy = g.grab()
        self.assertEqual(gx * 2, g.CV.w)
        self.assertGreater(g.CV.foot_row, g.ACTOR_HEIGHT)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_general as g
        import gen_heavy
        cls.g = g
        cls.front = g.render(g.RECOMMENDED, "A", 1)
        cls.fire = g.render(g.RECOMMENDED, "F", 1)
        cls.brief = g.render("A", "A", 1)
        cls.ramps = ramp_sets()
        cls.pm = gen_heavy.approved("SDPMA1", "panzermensch")

    def colours(self, rgba):
        a = rgba[..., 3] > 0
        return {tuple(int(v) for v in p) for p in rgba[..., :3][a]}

    def test_palette_v2_and_hard_alpha(self):
        v2 = set(self.g.heavy.palette_v2())
        for rgba in (self.front, self.fire, self.brief):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertTrue(self.colours(rgba) <= v2)

    def test_faction_colours(self):
        r = self.ramps
        for rgba in (self.front, self.fire, self.brief):
            cols = self.colours(rgba)
            self.assertFalse(cols & (r["khaki_olive"] | r["military_green"]))
            self.assertTrue(cols & r["flesh_pink"])
            self.assertTrue(cols & r["steel_blue"])
            self.assertTrue(cols & r["hazard_yellow"])

    def test_size(self):
        m = self.g.measure(self.front)
        self.assertGreaterEqual(m["height_px"], 90)
        self.assertLessEqual(m["height_px"], self.g.ACTOR_HEIGHT)
        if self.pm:
            pa = self.pm[0][..., 3] > 0
            self.assertGreater(m["height_px"], int(np.ptp(np.nonzero(pa)[0])) + 15)

    def test_value(self):
        m = self.g.measure(self.front)
        if self.pm:
            a = self.pm[0][..., 3] > 0
            pm_luma = float(self.g.flat.luma(self.pm[0][..., :3])[a].mean())
            self.assertGreater(m["body_luma"], pm_luma + 40)

    def test_flags_from_the_front(self):
        r = self.ramps
        cols = self.colours(self.brief)
        self.assertIn((0, 0, 0), cols)
        self.assertTrue(cols & r["flag_red"])
        self.assertIn(tuple(self.g.core.ramp("steel_blue")[3]), cols)       # the canton

    def test_seed(self):
        np.testing.assert_array_equal(self.g.render(self.g.RECOMMENDED, "A", 1), self.front)


if __name__ == "__main__":
    unittest.main()
