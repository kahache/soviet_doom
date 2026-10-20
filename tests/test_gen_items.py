"""Contract of tools/art/gen_items.py (backlog M2a; audit B3, B5, H2: our
own health, armour, map, backpack, yellow and red pass and Katyusha
pickups).

Always (text and small files only, the `fast` tier):

  names      eleven rows, each lump four letters SD + two, all distinct;
             SDHP is the name MOD-SPEC 6.3 already reserves for the hand
             Katyusha's pickup; every other lump collides with nothing: the
             only PNGs in assets/ that start with one are the frames of the
             option the CEO chose (D80) in assets/sprites/pickups/ (and the
             fullscreen HUD's MEDIA0, a copy of SDMDA0, which does not start
             with one), no other generator in tools/art/
             names it, every MOD-SPEC line that names it is about its own
             class, and no lump of the IWAD starts with it (when present)
  frames     each row's frames are the ones Doom's class plays, and the
             generator's SPAWN table is Doom's Spawn state (gzdoom.pk3
             g4.14.2, quoted below)
  no font    the generator never rasterises text with a system font
  chosen     CHOSEN is D80: the recommended option except SDAG C, SDAH C,
             SDBP B; the cross is the first-aid sign (white on green), not
             the red-cross emblem (D80)

Renders (skipped under SD_SKIP_SLOW_ART, which `verify.py fast` sets):

  palette    every opaque pixel is a palette v1 colour (v2 only for an
             option marked palette=2), alpha hard 0/255
  placement  every sprite stands on its lowest pixel, centred
  size       each option within SIZE_RANGE of the Freedoom sprite it replaces
  frames     the recommended and the chosen option have every frame, each
             the size and offsets of frame A and different from it
  emblem     the chosen dressing packet and first-aid box show the white
             cross on green and no flag red (D80)
  family     the yellow and red passes' option A is SDKB's card: in cobalt
             it renders exactly as gen_pickups' pass B; each key reads its
             colour (KEY_SHARE_MIN); the Katyusha's option A is the D51 draft
  tables     rendering leaves gen_weapon's material tables as they were
  seed       the same option renders identically twice
  hud        the three STKEYS icons are 7x5, palette v2, all different
  work/      no PNG under work/art/ outside this generator's folder starts
             with one of the new lumps (a parallel batch's names)
"""

from __future__ import annotations

import json
import os
import re
import struct
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

SOURCE = ART_TOOLS / "gen_items.py"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
SLOW = bool(os.environ.get("SD_SKIP_SLOW_ART"))

ROW = re.compile(r'\("(\w+)", "(SD[A-Z]{2}|\w+)", "([A-Z]+)", "(\w+)", "([A-Z0-9]{4})"\)')
# The frames each Doom class's Spawn state plays (gzdoom.pk3 g4.14.2,
# zscript/actors/doom/*.zs): BON1 ABCDCB 6; BON2 ABCDCB 6; ARM1 A 6, B 7
# bright; ARM2 A 6, B 6 bright; PMAP ABCDCB 6 Bright; YKEY/RKEY A 10, B 10
# bright; STIM, MEDI, BPAK, BFUG A -1.
DOOM_FRAMES = {"Stimpack": "A", "Medikit": "A", "HealthBonus": "ABCD", "ArmorBonus": "ABCD", "GreenArmor": "AB",
               "BlueArmor": "AB", "Allmap": "ABCD", "Backpack": "A", "YellowCard": "AB", "RedCard": "AB",
               "BFG9000": "A"}
FREEDOOM = {"Stimpack": "STIM", "Medikit": "MEDI", "HealthBonus": "BON1", "ArmorBonus": "BON2",
            "GreenArmor": "ARM1", "BlueArmor": "ARM2", "Allmap": "PMAP", "Backpack": "BPAK",
            "YellowCard": "YKEY", "RedCard": "RKEY", "BFG9000": "BFUG"}
RESERVED = "SDHP"               # MOD-SPEC 6.3: the hand Katyusha's pickup
INSTALLED = PROJECT_ROOT / "assets" / "sprites" / "pickups"   # D80
D80 = {"stim": "A", "medikit": "A", "hbonus": "B", "abonus": "A", "garmor": "C", "barmor": "C",
       "allmap": "A", "backpack": "B", "ykey": "A", "rkey": "A", "katyusha": "A"}
OWNER_WORDS = {"BFG9000": ("Katyusha", "BFG9000")}   # MOD-SPEC names the Katyusha's row by the weapon
MAY_NAME_SDHP = {"gen_weapon.py", "gen_hands_2d.py", "gen_items.py"}


def rows():
    return ROW.findall(SOURCE.read_text(encoding="utf-8"))


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = re.sub(r'""".*?"""', "", SOURCE.read_text(encoding="utf-8"), flags=re.S)
        for pattern in (r"ImageFont", r"truetype\(", r"\.text\(", r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


class NameTests(unittest.TestCase):
    """Read from the source and the docs: no imaging."""

    @classmethod
    def setUpClass(cls):
        cls.rows = rows()
        cls.lumps = [r[1] for r in cls.rows]

    def test_eleven_rows_one_per_class(self):
        self.assertEqual(len(self.rows), 11)
        self.assertEqual({r[3] for r in self.rows}, set(DOOM_FRAMES))

    def test_names_are_sprite_names(self):
        self.assertEqual(len(self.lumps), len(set(self.lumps)))
        for lump in self.lumps:
            self.assertRegex(lump, r"^SD[A-Z]{2}$")

    def test_frames_are_dooms(self):
        for slug, lump, frames, doom, freedoom in self.rows:
            with self.subTest(slug=slug):
                self.assertEqual(frames, DOOM_FRAMES[doom])
                self.assertEqual(freedoom, FREEDOOM[doom])

    def test_katyusha_keeps_its_reserved_name(self):
        row = next(r for r in self.rows if r[3] == "BFG9000")
        self.assertEqual(row[1], RESERVED)
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertRegex(spec, r"Hand Katyusha \|.*`SDHP` A")

    def test_no_installed_sprite_starts_with_a_new_name(self):
        """Since D80 the chosen frames are installed; nothing else may take
        one of the names."""
        new = [lump for lump in self.lumps if lump != RESERVED]
        ours = {f"{lump}{fr}0" for _, lump, frames, _, _ in self.rows for fr in frames}
        for p in (PROJECT_ROOT / "assets").rglob("*.png"):
            for lump in new:
                if p.stem.upper().startswith(lump):
                    self.assertEqual(p.parent, INSTALLED, f"{p} collides with {lump}")
                    self.assertIn(p.stem.upper(), ours, f"{p} collides with {lump}")

    def test_chosen_is_d80(self):
        text = SOURCE.read_text(encoding="utf-8")
        m = re.search(r"CHOSEN = \{(.*?)\}", text, re.S)
        self.assertEqual(dict(re.findall(r'"(\w+)": "([ABC])"', m.group(1))), D80)

    def test_no_other_generator_names_them(self):
        for p in sorted(ART_TOOLS.glob("*.py")):
            if p.name == SOURCE.name:
                continue
            text = p.read_text(encoding="utf-8")
            for lump in self.lumps:
                if lump == RESERVED and p.name in MAY_NAME_SDHP:
                    continue
                self.assertIsNone(re.search(rf"\b{lump}", text), f"{p.name} names {lump}")

    def test_mod_spec_names_them_only_for_their_own_class(self):
        """After the install MOD-SPEC will list them: each line that names a
        lump must then be about its own class."""
        spec = MOD_SPEC.read_text(encoding="utf-8").splitlines()
        for slug, lump, frames, doom, freedoom in self.rows:
            owners = OWNER_WORDS.get(doom, (doom,))
            for line in spec:
                if re.search(rf"\b{lump}", line):
                    with self.subTest(lump=lump, line=line[:80]):
                        self.assertTrue(any(w in line for w in owners))

    def test_no_iwad_lump_starts_with_them(self):
        if not IWAD.is_file():
            self.skipTest("iwads/freedoom2.wad absent")
        with IWAD.open("rb") as f:
            magic, n, table = struct.unpack("<4sii", f.read(12))
            f.seek(table)
            names = [f.read(16)[8:16].rstrip(b"\0").decode("ascii", "replace") for _ in range(n)]
        for lump in self.lumps:
            self.assertFalse([nm for nm in names if nm.startswith(lump)], lump)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class SpawnTableTests(unittest.TestCase):
    def test_spawn_frames_match_the_rows(self):
        import gen_items
        for slug, lump, frames, doom, freedoom in rows():
            played = "".join(sorted({f for f, _, _ in gen_items.SPAWN[doom]}))
            self.assertEqual(played, frames, doom)

    def test_items_are_the_names_table(self):
        import gen_items
        got = tuple((it.slug, it.lump, it.frames, it.doom, it.placeholder) for it in gen_items.ITEMS)
        self.assertEqual(got, gen_items.NAMES)

    def test_chosen_table(self):
        import gen_items
        self.assertEqual(gen_items.CHOSEN, D80)
        differ = {it.lump: gen_items.CHOSEN[it.slug] for it in gen_items.ITEMS
                  if gen_items.CHOSEN[it.slug] != it.recommended}
        self.assertEqual(differ, {"SDAG": "C", "SDAH": "C", "SDBP": "B"})

    def test_the_cross_is_the_first_aid_sign(self):
        import gen_items
        self.assertEqual(gen_items.CROSS_MATERIAL, "tel_white")
        self.assertEqual(gen_items.FIELD_MATERIAL, "aid_green")
        self.assertEqual(gen_items.ITEM_MATERIALS["aid_green"].ramp, "military_green")
        self.assertNotIn("hull_red", re.findall(r"CROSS_MATERIAL, CROSS_BASE = \"(\w+)\"",
                                                SOURCE.read_text(encoding="utf-8")))

    def test_three_options_and_a_recommendation(self):
        import gen_items
        for it in gen_items.ITEMS:
            self.assertEqual([o.key for o in it.options], ["A", "B", "C"], it.slug)
            self.assertIn(it.recommended, "ABC", it.slug)
            self.assertTrue(it.msg_id.startswith(("SD_GOT_", "SD_PICKUP_")), it.slug)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
@unittest.skipIf(SLOW, "SD_SKIP_SLOW_ART is set: skipping the pickup renders")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_items
        import gen_pickups
        import gen_weapon
        cls.g, cls.gp, cls.gw = gen_items, gen_pickups, gen_weapon
        cls.before = (gen_weapon.MATERIALS, gen_weapon.MAT_ID, gen_weapon.METALS, gen_weapon.FLAT)
        cls.frames = gen_items.render_all()
        cls.after = (gen_weapon.MATERIALS, gen_weapon.MAT_ID, gen_weapon.METALS, gen_weapon.FLAT)
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.v1 = {tuple(c) for c in pal["colours"]}
        cls.v2 = {tuple(c) for c in pal["colours_v2"]}

    def opaque(self, f):
        return {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}

    def each(self):
        for it in self.g.ITEMS:
            for o in it.options:
                for fr, f in self.frames[it.slug][o.key].items():
                    yield it, o, fr, f

    def test_palette_and_hard_alpha(self):
        for it, o, fr, f in self.each():
            with self.subTest(item=it.slug, opt=o.key, frame=fr):
                self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
                self.assertLessEqual(self.opaque(f), self.v2 if o.palette == 2 else self.v1)

    def test_v2_only_where_declared(self):
        """An option marked palette=2 really needs it (else it should be v1)."""
        for it, o, fr, f in self.each():
            if o.palette == 2:
                self.assertTrue(self.opaque(f) - self.v1, (it.slug, o.key))

    def test_stands_on_the_floor(self):
        for it, o, fr, f in self.each():
            lo, to = f.offsets()
            h, w = f.rgba.shape[:2]
            with self.subTest(item=it.slug, opt=o.key, frame=fr):
                self.assertLessEqual(abs(int(lo) - w // 2), 1)
                self.assertEqual(int(to), h)

    def test_size_of_the_placeholder(self):
        lo, hi = self.g.SIZE_RANGE
        for it in self.g.ITEMS:
            ref = max(self.g.PLACEHOLDER_SIZE[it.placeholder])
            for o in it.options:
                f = self.frames[it.slug][o.key]["A"]
                with self.subTest(item=it.slug, opt=o.key):
                    self.assertTrue(lo <= max(f.rgba.shape[:2]) / ref <= hi)

    def test_recommended_and_chosen_sets_are_complete_and_animate(self):
        for it in self.g.ITEMS:
            for key in {it.recommended, self.g.CHOSEN[it.slug]}:
                got = self.frames[it.slug][key]
                self.assertEqual("".join(sorted(got)), it.frames, (it.slug, key))
                a = got["A"]
                for fr in it.frames[1:]:
                    with self.subTest(item=it.slug, opt=key, frame=fr):
                        self.assertEqual(got[fr].rgba.shape, a.rgba.shape)
                        self.assertEqual(tuple(map(int, got[fr].offsets())), tuple(map(int, a.offsets())))
                        self.assertFalse(np.array_equal(got[fr].rgba, a.rgba))

    def test_render_chosen_is_render_all(self):
        chosen = self.g.render_chosen()
        for it in self.g.ITEMS:
            for fr, f in chosen[it.slug].items():
                self.assertTrue(np.array_equal(f.rgba, self.frames[it.slug][self.g.CHOSEN[it.slug]][fr].rgba),
                                (it.slug, fr))

    def test_first_aid_sign_on_the_medical_items(self):
        """D80: white cross on green, no flag red, on the installed options."""
        import palette
        red = set(map(tuple, palette.ramp_colours("flag_red")))
        green = set(map(tuple, palette.ramp_colours("military_green")))
        white = set(map(tuple, palette.ramp_colours("plaster_warm")))
        for slug in ("stim", "medikit"):
            f = self.frames[slug][self.g.CHOSEN[slug]]["A"]
            px = self.opaque(f)
            with self.subTest(item=slug):
                self.assertFalse(px & red)
                self.assertTrue(px & green)
                self.assertTrue(px & white)

    def test_saved_names(self):
        for it in self.g.ITEMS:
            for fr in it.frames:
                self.assertEqual(self.g.lump_name(it, fr), f"{it.lump}{fr}0")

    def test_keys_are_sdkb_family(self):
        """render_card in cobalt with SDKB's red star is gen_pickups' pass B."""
        for fr in ("A", "B"):
            with self.g.item_materials():
                ours = self.g.render_card("cobalt", 0.56, "hull_red", 0.55, fr)
            with self.gp.pickup_materials():
                theirs = self.gp.render_pass_b(fr)
            self.assertTrue(np.array_equal(ours.rgba, theirs.rgba), fr)

    def test_keys_read_their_colour(self):
        import palette
        for slug, ramp in self.g.KEY_RAMP.items():
            cols = set(map(tuple, palette.ramp_colours(ramp)))
            f = self.frames[slug]["A"]["A"]
            px = f.rgba[f.rgba[..., 3] > 0][:, :3]
            share = np.mean([tuple(int(v) for v in p) in cols for p in px])
            self.assertGreaterEqual(share, self.g.KEY_SHARE_MIN, slug)

    def test_katyusha_a_is_the_d51_draft(self):
        import gen_hands_2d
        draft = self.gw.render_katyusha_pickup(gen_hands_2d.HK_VARIANT_2D)
        self.assertTrue(np.array_equal(self.frames["katyusha"]["A"]["A"].rgba, draft.rgba))

    def test_material_tables_restored(self):
        self.assertTrue(all(x is y for x, y in zip(self.before, self.after)))
        for name in self.g.ITEM_MATERIALS:
            self.assertNotIn(name, self.gw.MATERIALS)

    def test_extra_materials_append(self):
        old = dict(self.gw.MAT_ID)
        with self.g.item_materials():
            for name, i in old.items():
                self.assertEqual(self.gw.MAT_ID[name], i)

    def test_deterministic(self):
        it = self.g.ITEM["abonus"]
        again = self.g.render_option(it, it.option(it.recommended), "C")
        self.assertTrue(np.array_equal(again.rgba, self.frames["abonus"][it.recommended]["C"].rgba))

    def test_hud_key_icons(self):
        icons = {lump: self.g.key_icon(lump) for lump in self.g.KEY_ICON_COLOURS}
        self.assertEqual(set(icons), {"STKEYS0", "STKEYS1", "STKEYS2"})
        for lump, rgb in icons.items():
            self.assertEqual(rgb.shape, (5, 7, 3), lump)
            self.assertLessEqual({tuple(int(v) for v in p) for p in rgb.reshape(-1, 3)}, self.v2, lump)
        vals = list(icons.values())
        self.assertFalse(np.array_equal(vals[0], vals[1]) or np.array_equal(vals[1], vals[2]))

    def test_no_work_sprite_starts_with_a_new_name(self):
        new = [lump for lump in self.g.ITEM_LUMPS if lump != RESERVED]
        own = PROJECT_ROOT / "work" / "art" / "items"
        for p in (PROJECT_ROOT / "work" / "art").rglob("*.png"):
            if own in p.parents:
                continue
            for lump in new:
                self.assertFalse(p.stem.upper().startswith(lump), f"{p} collides with {lump}")


if __name__ == "__main__":
    unittest.main()
