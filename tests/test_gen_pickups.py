"""Contract of tools/art/gen_pickups.py (T8: the ammunition pickups; the
blue pass of MAP03; T23: the radio's SDRD A).

Cheap: renders every option once (about a second), never the sheet. What
is checked:

  palette    every opaque pixel is a palette.json colour, alpha is hard
             0/255; v1 only, but for the pass, which may use v2 (cobalt, D45)
  placement  every pickup stands on its lowest pixel, centred (grAb
             left = width / 2, top = height), as the D48 weapon pickups do
  size       each option is in the range of the Freedoom sprite it replaces
  names      four letters, SD prefix, all distinct; SDRD is the one MOD-SPEC
             6.3 reserves for the radio, the proposals collide with no name
             the spec reserves
  classes    every ammo class of zscript/sd/ammo.zs but the backpack has a
             pickup here, and the placeholder named is that class's sprite
  pass       two frames, A and B, that differ (Doom's key cards blink)
  tables     rendering leaves gen_weapon's material tables as they were
  seed       the same option renders identically twice
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

SOURCE = ART_TOOLS / "gen_pickups.py"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
AMMO_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "ammo.zs"

# An option may be this much smaller or larger than the Freedoom sprite it
# replaces, on its larger side (the radio stands on a stool and carries an
# aerial, hence the wide upper bound).
SIZE_RANGE = (0.6, 1.9)
# Doom's ammo classes and the sprite each wears in Freedoom.
DOOM_AMMO_SPRITE = {"Clip": "CLIP", "ClipBox": "AMMO", "Shell": "SHEL", "ShellBox": "SBOX",
                    "RocketAmmo": "ROCK", "RocketBox": "BROK", "Cell": "CELL", "CellPack": "CELP"}


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = re.sub(r'""".*?"""', "", SOURCE.read_text(encoding="utf-8"), flags=re.S)
        for pattern in (r"ImageFont", r"truetype\(", r"\.text\(", r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class PickupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_pickups
        import gen_weapon
        cls.g, cls.gw = gen_pickups, gen_weapon
        before = (gen_weapon.MATERIALS, gen_weapon.MAT_ID, gen_weapon.METALS, gen_weapon.FLAT)
        cls.frames = {}
        for p in gen_pickups.PICKUPS:
            for o in p.options:
                for fr in p.frames:
                    cls.frames[(p.slug, o.key, fr)] = gen_pickups.render_option(p, o, fr)
        cls.after = (gen_weapon.MATERIALS, gen_weapon.MAT_ID, gen_weapon.METALS, gen_weapon.FLAT)
        cls.before = before
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.v1 = {tuple(c) for c in pal["colours"]}
        cls.v2 = {tuple(c) for c in pal["colours_v2"]}

    def opaque(self, f):
        return {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for (slug, opt, fr), f in self.frames.items():
            with self.subTest(slug=slug, opt=opt, frame=fr):
                self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
                allowed = self.v2 if slug == self.g.PASS_SLUG else self.v1
                self.assertLessEqual(self.opaque(f), allowed)

    def test_the_pass_is_cobalt(self):
        """The reason the pass is in v2 at all: it must read blue."""
        import palette
        cobalt = set(map(tuple, palette.ramp_colours("mosaic_cobalt")))
        for (slug, opt, fr), f in self.frames.items():
            if slug == self.g.PASS_SLUG:
                a = f.rgba[..., 3] > 0
                share = np.mean([tuple(int(v) for v in px) in cobalt for px in f.rgba[a][:, :3]])
                self.assertGreater(share, 0.4, (opt, fr, share))

    def test_stands_on_the_floor(self):
        for key, f in self.frames.items():
            lo, to = f.offsets()
            h, w = f.rgba.shape[:2]
            with self.subTest(key=key):
                self.assertLessEqual(abs(lo - w // 2), 1)
                self.assertEqual(to, h)

    def test_size_of_the_placeholder(self):
        sizes = {"CLIP": (7, 12), "AMMO": (17, 16), "SHEL": (14, 10), "SBOX": (34, 13), "ROCK": (10, 24),
                 "BROK": (52, 20), "CELL": (19, 12), "CELP": (32, 20), "BKEY": (14, 21), "PMAP": (32, 28)}
        for p in self.g.PICKUPS:
            ref = max(sizes[p.placeholder])
            for o in p.options:
                f = self.frames[(p.slug, o.key, "A")]
                with self.subTest(slug=p.slug, opt=o.key):
                    r = max(f.rgba.shape[:2]) / ref
                    self.assertTrue(SIZE_RANGE[0] <= r <= SIZE_RANGE[1], r)

    def test_the_pass_blinks(self):
        for o in self.g.PICKUP["pass"].options:
            a, b = self.frames[("pass", o.key, "A")], self.frames[("pass", o.key, "B")]
            self.assertEqual(a.rgba.shape, b.rgba.shape)
            self.assertFalse(np.array_equal(a.rgba, b.rgba), o.key)

    def test_material_tables_restored(self):
        self.assertTrue(all(x is y for x, y in zip(self.before, self.after)))
        self.assertNotIn("cobalt", self.gw.MATERIALS)

    def test_extra_materials_append(self):
        """Inside the context gen_weapon's ids keep their numbers."""
        old = dict(self.gw.MAT_ID)
        with self.g.pickup_materials():
            for name, i in old.items():
                self.assertEqual(self.gw.MAT_ID[name], i)
            for name in self.g.EXTRA_MATERIALS:
                self.assertGreaterEqual(self.gw.MAT_ID[name], len(old))

    def test_deterministic(self):
        p = self.g.PICKUP["clipbox"]
        again = self.g.render_option(p, p.options[1])
        self.assertTrue(np.array_equal(again.rgba, self.frames[("clipbox", p.options[1].key, "A")].rgba))

    def test_recommendation_is_an_option(self):
        for p in self.g.PICKUPS:
            self.assertIn(p.recommended, {o.key for o in p.options}, p.slug)
            self.assertEqual(len(p.options), 2, p.slug)


class NameTests(unittest.TestCase):
    """Names and classes are read from the source and the docs: no imaging."""

    @classmethod
    def setUpClass(cls):
        src = SOURCE.read_text(encoding="utf-8")
        cls.rows = re.findall(r'Pickup\("(\w+)", "(\w+)", (?:\("A",\)|PASS_FRAMES), "([^"]+)", "(\w+)"', src)
        cls.spec = MOD_SPEC.read_text(encoding="utf-8")

    def test_rows_found(self):
        self.assertEqual(len(self.rows), 10)

    def test_names_are_sprite_names(self):
        lumps = [r[1] for r in self.rows]
        self.assertEqual(len(lumps), len(set(lumps)))
        for lump in lumps:
            self.assertRegex(lump, r"^SD[A-Z]{2}$")

    def test_radio_is_the_reserved_name(self):
        radio = next(r for r in self.rows if r[0] == "radio")
        self.assertEqual(radio[1], "SDRD")
        self.assertIn("final sprite **`SDRD`** A", self.spec)

    def test_each_name_is_reserved_for_its_own_class(self):
        """D63 reserved the names in MOD-SPEC 6.3: every lump has exactly one
        table row naming a class, and it is its own (SD_BluePass for the pass)."""
        rows = re.findall(r"(?m)^\| `(\w+)` \| `(SD[A-Z]{2})` \|", self.spec)
        for slug, lump, actor, *_ in self.rows:
            owner = "SD_BluePass" if slug == "pass" else actor
            self.assertEqual([c for c, name in rows if name == lump], [owner], slug)

    def test_every_ammo_class_is_covered(self):
        zs = AMMO_ZS.read_text(encoding="utf-8")
        classes = dict(re.findall(r"class (SD_\w+) : (\w+) replaces", zs))
        covered = {r[2] for r in self.rows}
        for ours, doom in classes.items():
            if doom == "Backpack":
                continue                    # not in this sweep
            self.assertIn(ours, covered)
            row = next(r for r in self.rows if r[2] == ours)
            self.assertEqual(row[3], DOOM_AMMO_SPRITE[doom], ours)


if __name__ == "__main__":
    unittest.main()
