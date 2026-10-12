"""F4 arsenal: structural checks on the built PK3 (stdlib unittest).

These tests do not run GZDoom. They guard the contract in
docs/engine/MOD-SPEC.md: the seven weapon classes exist in their own files,
every class named from MAPINFO or from a weapon slot really exists, editor
numbers stay inside the reserved range, SNDINFO is well formed and every
logical sound the ZScript asks for is defined, and MAP02 actually places
the arsenal.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(TOOLS_DIR))

from sdbuild import wad  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

# The arsenal ratified by the CEO (D13), one weapon per Doom slot.
# slot -> (class name, source file under zscript/weapons/, editor number)
ARSENAL = {
    1: ("SD_Shovel", "zscript/weapons/shovel.zs", 21001),
    2: ("SD_Tokarev", "zscript/weapons/tokarev.zs", 21002),
    3: ("SD_Izh", "zscript/weapons/izh.zs", 21003),
    4: ("SD_Ppsh", "zscript/weapons/ppsh.zs", 21004),
    5: ("SD_Rpg7", "zscript/weapons/rpg7.zs", 21005),
    6: ("SD_Roks3", "zscript/weapons/roks3.zs", 21006),
    7: ("SD_HandKatyusha", "zscript/weapons/katyusha.zs", 21007),
}

PLAYER_CLASS = "SD_Player"

# docs/engine/adr/002: 14000-14999 collides with AmbientSound / MusicChanger.
RESERVED_EDNUM_MIN = 21000
RESERVED_EDNUM_MAX = 21999

# Editor numbers deliberately mapped to None: the arsenal is exactly seven.
REMOVED_EDNUMS = {82, 2005}

MAX_LUMP_NAME = 8


def _blocks(text: str, kind: str) -> list[str]:
    return re.findall(rf"^{kind}\s*\{{(.*?)\}}", text, flags=re.S | re.M)


def _udmf_things(text: str) -> list[str]:
    return re.findall(r"^thing\s*\{(.*?)\}", text, flags=re.S | re.M)


class ArsenalPk3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, out, TOOLS_DIR)
        cls.zf = zipfile.ZipFile(out)
        cls.names = cls.zf.namelist()
        cls.lowered = {n.lower() for n in cls.names}
        cls.mapinfo = cls.zf.read("MAPINFO").decode("utf-8")
        cls.language = cls.zf.read("LANGUAGE").decode("utf-8")
        cls.sndinfo = cls.zf.read("SNDINFO").decode("utf-8")
        cls.zs = {
            n: cls.zf.read(n).decode("utf-8")
            for n in cls.names
            if n.lower().startswith("zscript/")
        }
        cls.zs_all = "\n".join(cls.zs.values())

    @classmethod
    def tearDownClass(cls):
        cls.zf.close()
        cls.tmp.cleanup()

    # --- ZScript structure -------------------------------------------------

    def test_one_weapon_class_per_file(self):
        for slot, (cls_name, path, _) in ARSENAL.items():
            self.assertIn(path, self.names, f"slot {slot}: {path} missing from the pk3")
            body = self.zs[path]
            declared = re.findall(r"^class\s+(\w+)", body, flags=re.M)
            self.assertEqual(
                declared, [cls_name],
                f"{path} must declare exactly {cls_name}, found {declared}",
            )

    def test_every_weapon_file_is_included(self):
        entry = self.zf.read("zscript.txt").decode("utf-8")
        included = {inc.lower() for inc in re.findall(r'#include\s+"([^"]+)"', entry)}
        for slot, (_, path, _) in ARSENAL.items():
            self.assertIn(path.lower(), included, f"slot {slot}: {path} not #included")
        # and nothing under zscript/ is orphaned
        for name in self.zs:
            self.assertIn(name.lower(), included, f"{name} is in the pk3 but never included")

    def test_every_weapon_replaces_its_doom_counterpart(self):
        """Without `replaces`, Freedoom's weapons would still spawn on maps."""
        for _, (cls_name, path, _) in ARSENAL.items():
            self.assertRegex(
                self.zs[path],
                re.compile(rf"class\s+{cls_name}\s*:\s*\w+\s+replaces\s+\w+", re.M),
                f"{cls_name} must declare `replaces`",
            )

    def test_every_weapon_declares_its_slot(self):
        for slot, (cls_name, path, _) in ARSENAL.items():
            self.assertRegex(
                self.zs[path],
                re.compile(rf"Weapon\.SlotNumber\s+{slot}\s*;", re.M),
                f"{cls_name} must set Weapon.SlotNumber {slot}",
            )

    def test_player_class_exists_and_owns_every_slot(self):
        self.assertIn(f"class {PLAYER_CLASS}", self.zs_all)
        player = next(b for n, b in self.zs.items() if f"class {PLAYER_CLASS}" in b)
        for slot, (cls_name, _, _) in ARSENAL.items():
            self.assertRegex(
                player,
                re.compile(rf'Player\.WeaponSlot\s+{slot}\s*,\s*"{cls_name}"', re.M),
                f"{PLAYER_CLASS} must put {cls_name} in slot {slot}",
            )
        # The sergeant starts with the sidearm and the shovel, nothing else armed.
        self.assertRegex(player, r'Player\.StartItem\s+"SD_Tokarev"')
        self.assertRegex(player, r'Player\.StartItem\s+"SD_Shovel"')

    def test_mapinfo_declares_the_player_class(self):
        m = re.search(r'PlayerClasses\s*=\s*"([^"]+)"', self.mapinfo)
        self.assertIsNotNone(m, "MAPINFO gameinfo must set PlayerClasses")
        self.assertEqual(m.group(1), PLAYER_CLASS)

    def test_no_decorate_lump(self):
        """ZScript for everything new; DECORATE needs an ADR first."""
        self.assertNotIn("decorate", self.lowered)

    # --- Editor numbers ----------------------------------------------------

    def _ednums(self) -> dict[int, str]:
        block = re.search(r"^DoomEdNums\s*\{(.*?)^\}", self.mapinfo, flags=re.S | re.M)
        self.assertIsNotNone(block, "MAPINFO must have a DoomEdNums block")
        out: dict[int, str] = {}
        for line in block.group(1).splitlines():
            line = line.split("//")[0].strip()
            if not line:
                continue
            num, _, cls_name = line.partition("=")
            key = int(num.strip())
            self.assertNotIn(key, out, f"editor number {key} assigned twice")
            out[key] = cls_name.strip()
        return out

    def test_every_weapon_has_its_editor_number(self):
        ednums = self._ednums()
        for slot, (cls_name, _, ednum) in ARSENAL.items():
            self.assertIn(ednum, ednums, f"slot {slot}: editor number {ednum} not assigned")
            self.assertEqual(ednums[ednum], cls_name)

    def test_editor_numbers_stay_in_the_reserved_range(self):
        """14000-14999 collides with AmbientSound/MusicChanger (ADR 002)."""
        for num, cls_name in self._ednums().items():
            if cls_name == "None":
                self.assertIn(num, REMOVED_EDNUMS, f"{num} = None is undocumented")
                continue
            self.assertTrue(
                RESERVED_EDNUM_MIN <= num <= RESERVED_EDNUM_MAX,
                f"{cls_name} uses {num}, outside the reserved "
                f"{RESERVED_EDNUM_MIN}-{RESERVED_EDNUM_MAX}",
            )

    def test_weapons_with_no_soviet_counterpart_are_unplaceable(self):
        ednums = self._ednums()
        for num in REMOVED_EDNUMS:
            self.assertEqual(ednums.get(num), "None", f"editor number {num} must map to None")

    def test_every_class_named_in_mapinfo_exists(self):
        for cls_name in self._ednums().values():
            if cls_name == "None":
                continue
            self.assertIn(f"class {cls_name}", self.zs_all, f"{cls_name} has a number but no class")

    # --- Sounds ------------------------------------------------------------

    def _sndinfo_names(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in self.sndinfo.splitlines():
            line = raw.split("//")[0].strip()
            if not line:
                continue
            parts = line.split()
            self.assertEqual(len(parts), 2, f"SNDINFO line is not `logical lump`: {raw!r}")
            logical, lump = parts
            self.assertLessEqual(len(lump), MAX_LUMP_NAME, f"{lump} is longer than a lump name")
            self.assertNotIn(logical, out, f"{logical} defined twice in SNDINFO")
            out[logical] = lump
        return out

    def test_every_sound_the_code_plays_is_defined(self):
        defined = self._sndinfo_names()
        used = set(re.findall(r'"(sd/[a-z0-9/_]+)"', self.zs_all))
        self.assertTrue(used, "no sd/... sound names found in the ZScript")
        for name in sorted(used):
            self.assertIn(name, defined, f"{name} is played but not defined in SNDINFO")

    def test_every_defined_sound_is_used(self):
        """A dead SNDINFO entry means the sound-designer gets a wrong brief."""
        used = set(re.findall(r'"(sd/[a-z0-9/_]+)"', self.zs_all))
        for name in self._sndinfo_names():
            self.assertIn(name, used, f"{name} is defined in SNDINFO but nothing plays it")

    # --- LANGUAGE ----------------------------------------------------------

    def test_every_language_id_used_by_the_arsenal_exists_in_both_languages(self):
        ids = set(re.findall(r'"\$(SD_[A-Z0-9_]+)"', self.zs_all))
        ids |= set(re.findall(r'lookup\s+"(SD_[A-Z0-9_]+)"', self.mapinfo))
        self.assertTrue(ids, "the arsenal must use LANGUAGE ids, not literals")
        enu, _, ru = self.language.partition("[ru]")
        self.assertTrue(ru, "LANGUAGE must have a [ru] section (D7)")
        for ident in sorted(ids):
            self.assertRegex(enu, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [enu default]")
            self.assertRegex(ru, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [ru]")

    # --- MAP02 test range --------------------------------------------------

    def test_map02_is_packed_and_well_formed(self):
        self.assertIn("maps/MAP02.wad", self.names)
        blob = self.zf.read("maps/MAP02.wad")
        self.assertEqual(blob[:4], b"PWAD")
        self.assertEqual([n for n, _, _ in wad.read_directory(blob)], ["MAP02", "TEXTMAP", "ENDMAP"])

    def test_map02_places_the_whole_arsenal_and_a_player_start(self):
        blob = self.zf.read("maps/MAP02.wad")
        text = wad.read_lump(blob, "TEXTMAP").decode("ascii")
        types = [int(re.search(r"type\s*=\s*(\d+);", t).group(1)) for t in _udmf_things(text)]
        self.assertIn(1, types, "MAP02 has no player start")
        for slot, (cls_name, _, ednum) in ARSENAL.items():
            self.assertIn(ednum, types, f"MAP02 does not place {cls_name} ({ednum})")

    def test_map02_is_in_mapinfo_with_a_localized_name(self):
        self.assertRegex(self.mapinfo, r'map\s+MAP02\s+lookup\s+"SD_MAP02_NAME"')
        enu, _, ru = self.language.partition("[ru]")
        self.assertRegex(enu, re.compile(r"^SD_MAP02_NAME\s*=", re.M))
        self.assertRegex(ru, re.compile(r"^SD_MAP02_NAME\s*=", re.M))


class BalanceDocTest(unittest.TestCase):
    """The balance doc is part of the deliverable, and D7 wants a mirror."""

    def test_balance_doc_and_russian_mirror_exist(self):
        en = PROJECT_ROOT / "docs/engine/BALANCE.md"
        ru = PROJECT_ROOT / "docs/ru/engine/BALANCE.md"
        self.assertTrue(en.is_file(), "docs/engine/BALANCE.md missing")
        self.assertTrue(ru.is_file(), "docs/ru/engine/BALANCE.md missing (D7)")

    def test_balance_doc_covers_every_weapon(self):
        text = (PROJECT_ROOT / "docs/engine/BALANCE.md").read_text(encoding="utf-8")
        for _, (cls_name, _, _) in ARSENAL.items():
            human = cls_name.removeprefix("SD_")
            self.assertIn(
                human.lower(),
                text.lower(),
                f"BALANCE.md says nothing about {cls_name}",
            )


if __name__ == "__main__":
    unittest.main()
