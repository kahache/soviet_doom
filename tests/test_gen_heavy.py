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

The full sets (D65: Doughboy C, Panzermensch D, the Schwer as D with S2):

  zs          the letters come from the classes' .zs files: SDDB A-F at 8
              rotations and G-L at 0; SDPM and SDPS A-H at 8 and I-O at 0;
              no XDeath, so no gib; 54, 71 and 71 lumps, names of 8 or less
  name        the Schwer's proposed sprite SDPS collides with no reserved
              prefix (BESTIARY 2.3, MOD-SPEC 6.3) and no lump in assets/
  sweep       the full sets keep the sweep's poses for SDDB A, D and SDPM A, G
  affine      affine_prims maps an ellipsoid's surface onto the new surface
  blood       the death tables' blood and pool are dark red (D49), flat
  (slow) corpse   the dead lie flat: every part of SDDBL0, SDPMO0 and SDPSO0
              within LYING_MAX of the floor, nothing propped higher than
              LYING_TOP, the supports spread LYING_SPAN, the brutes across the
              screen; and they bleed a lot (blood droplets and pools)
  (slow) render   the full set's sweep views are the sweep's pixels; the
              lumps on disk are palette v2, hard alpha, with their grAb
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


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class FullSetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_heavy
        cls.h = gen_heavy

    def test_frames_come_from_the_zs(self):
        h = self.h
        self.assertEqual(h.full_frames("db"), ("ABCDEF", "GHIJKL"))
        self.assertEqual(h.full_frames("pm"), ("ABCDEFGH", "IJKLMNO"))
        self.assertEqual(h.full_frames("ps"), h.full_frames("pm"))       # the Schwer inherits the states
        for path in (h.DB_ZS, h.PM_ZS):
            self.assertNotIn("XDeath", h.zs_states(path))                # no gib
        for key, n in (("db", 54), ("pm", 71), ("ps", 71)):
            plan = h.full_plan(key)
            self.assertEqual(len(plan), n)
            names = [h.full_lump(key, f, r) for f, r in plan]
            self.assertEqual(len(set(names)), n)
            self.assertTrue(all(len(x) <= 8 for x in names))
            rotated, death = h.full_frames(key)
            for f in rotated:                                            # handed: 8 drawn rotations, no pairs
                self.assertEqual(sorted(r for g, r in plan if g == f), list(range(1, 9)))
            for f in death:
                self.assertEqual([r for g, r in plan if g == f], [0])

    def test_schwer_sprite_name_is_free(self):
        h = self.h
        name = h.PS_SPRITE
        self.assertTrue(re.fullmatch(r"SD[A-Z]{2}", name))
        self.assertNotEqual(name, h.PM_SPRITE)
        reserved = set()
        for doc in ("docs/engine/BESTIARY.md", "docs/engine/MOD-SPEC.md"):
            reserved |= set(re.findall(r"\bSD[A-Z]{2}\b", (PROJECT_ROOT / doc).read_text(encoding="utf-8")))
        self.assertNotIn(name, reserved)
        for png in (PROJECT_ROOT / "assets").rglob("*.png"):
            self.assertFalse(png.stem.startswith(name), png)

    def test_full_poses_keep_the_sweep(self):
        h = self.h
        for f in "AG":
            a, b = h.PM_FULL_POSES[f], h.PM_POSES[f]
            self.assertEqual((a.foot_l, a.foot_r, a.hand_l, a.hand_r, a.hunch, a.shell, a.bob, a.twist, a.charge),
                             (b.foot_l, b.foot_r, b.hand_l, b.hand_r, b.hunch, b.shell, b.bob, b.twist, b.charge))
        self.assertFalse(set("AD") & set(h.DB_FULL_POSES))               # A and D are the sweep's db_model
        self.assertEqual(set(h.DB_FULL_POSES), set("BCEFG"))
        self.assertEqual(set(h.DB_FALLS), set("HIJKL"))
        self.assertEqual(set(h.PM_FALLS), set("IJKLMNO"))
        self.assertEqual(set(h.PS_FALLS), set("IJKLMNO"))

    def test_affine_prims_maps_surface_to_surface(self):
        h, core = self.h, self.h.core
        centre, radii = np.array([1.0, 10.0, 2.0]), np.array([3.0, 4.0, 5.0])
        q = core.ellipsoid("flesh", 0.5, tuple(centre), tuple(radii))
        A = np.diag([1.4, 0.3, 1.2]) @ core.rot_x(50.0) @ core.rot_z(10.0)
        pivot = np.array([0.0, 2.0, 0.0])
        rng = np.random.default_rng(1)
        u = rng.normal(size=(40, 3))
        u /= np.linalg.norm(u, axis=1)[:, None]
        surf = centre + u * radii
        h.affine_prims([q], A, pivot)
        mapped = pivot + (surf - pivot) @ A.T
        np.testing.assert_allclose(q.sd(mapped), 0.0, atol=1e-6)
        inside = centre + 0.5 * (surf - centre)                          # halfway in: still inside
        self.assertTrue(np.all(q.sd(pivot + (inside - pivot) @ A.T) < 0))

    def test_blood_is_dark_red(self):
        h = self.h
        for table in (h.DB_DEATH_MATERIALS, h.PM_FULL_MATERIALS):
            for name in ("blood", "pool"):
                m = table[name]
                self.assertEqual(m.ramps, {"flag_red"})
                self.assertTrue(m.flat)
                self.assertLessEqual(max(s[2] for s in m.spans if s[0] == "flag_red"), 5)
        self.assertEqual(list(h.DB_DEATH_MATERIALS)[:len(h.DB_MATERIALS)], list(h.DB_MATERIALS))
        self.assertEqual(list(h.PM_FULL_MATERIALS)[:len(h.PM_MATERIALS)], list(h.PM_MATERIALS))


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class CorpseTests(unittest.TestCase):
    """The CEO's rule for every corpse (on the Legion's first L0: it looked
    propped on its shoulder): lying with its weight on the floor, measured."""

    @classmethod
    def setUpClass(cls):
        import gen_heavy as h
        cls.h = h
        cls.db = h.db_corpse_metrics("L")
        cls.pm = h.pm_corpse_metrics(h.PM[h.PM_FULL_KEY], "O")
        cls.ps = h.pm_corpse_metrics(h.SCHWER_CELL, "O")

    def test_the_doughboy_lies_flat(self):
        h, m = self.h, self.db
        self.assertEqual(set(m["lowest"]), {"sack", "spine", "helmet"})
        for part, y in m["lowest"].items():
            self.assertLessEqual(abs(y), h.DB_LYING_MAX, part)
        self.assertLess(m["top"], h.DB_LYING_TOP)
        self.assertGreaterEqual(m["span"], h.DB_LYING_SPAN)

    def test_the_brutes_lie_flat(self):
        h = self.h
        for name, m in (("SDPM", self.pm), ("SDPS", self.ps)):
            self.assertGreaterEqual(len(m["lowest"]), 13, name)
            for part, y in m["lowest"].items():
                self.assertLessEqual(abs(y), h.PM_LYING_MAX, f"{name} {part} is {y} units off the floor")
            self.assertLess(m["top"], h.PM_LYING_TOP, name)
            self.assertGreaterEqual(m["span"], h.PM_LYING_SPAN, name)
            self.assertGreater(m["across"], 0.95, name)                  # lying across the screen

    def test_the_dead_bleed_a_lot(self):
        h = self.h
        for key, frame in (("db", "L"), ("pm", "O"), ("ps", "O")):
            P = h.full_prims(key, frame)
            self.assertGreaterEqual(len([p for p in P if p.mat == "blood"]), 40, key)
            self.assertGreaterEqual(len([p for p in P if p.mat == "pool"]), 4, key)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class FullSetRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_heavy as h
        cls.h = h

    def test_the_sweep_views_are_the_sweeps_pixels(self):
        h = self.h
        np.testing.assert_array_equal(h.render_full("db", "A", 1), h.render_db(h.DB_FULL_KEY, "A", 1))
        np.testing.assert_array_equal(h.render_full("pm", "G", 1), h.render_pm(h.PM_FULL_KEY, "G", 1))

    def test_lumps_on_disk(self):
        h = self.h
        v2 = set(h.palette_v2())
        for key in ("db", "pm", "ps"):
            d = h.set_dir(key)
            if not d.is_dir():
                self.skipTest(f"{d} not rendered (gen_heavy.py --full)")
            for f, r in h.full_plan(key):
                path = d / f"{h.full_lump(key, f, r)}.png"
                self.assertTrue(path.is_file(), path)
                with Image.open(path) as im:
                    rgba = np.asarray(im.convert("RGBA"))
                self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, path.name)
                a = rgba[..., 3] > 0
                self.assertTrue({tuple(int(v) for v in p) for p in rgba[..., :3][a]} <= v2, path.name)
                self.assertEqual(tuple(h.core.read_grab(path)), tuple(h.full_grab(key, f)), path.name)


if __name__ == "__main__":
    unittest.main()
