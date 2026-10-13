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

# D36/D37: the Reich speaks real German and the alphabet has these letters;
# the only non-ASCII characters the English section may contain (T17 otherwise).
GERMAN_LETTERS = frozenset("ÄÖÜäöüßẞ")

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

# Ammunition reskin (CEO 2026-10-13): class, Doom parent it subclasses AND
# replaces, and the LANGUAGE id carrying its pickup line.
AMMO_PICKUPS = [
    ("SD_Clip", "Clip", "SD_GOT_CLIP"),
    ("SD_ClipBox", "ClipBox", "SD_GOT_CLIPBOX"),
    ("SD_Shell", "Shell", "SD_GOT_SHELLS"),
    ("SD_ShellBox", "ShellBox", "SD_GOT_SHELLBOX"),
    ("SD_RocketAmmo", "RocketAmmo", "SD_GOT_ROCKET"),
    ("SD_RocketBox", "RocketBox", "SD_GOT_ROCKBOX"),
    ("SD_Cell", "Cell", "SD_GOT_CELL"),
    ("SD_CellPack", "CellPack", "SD_GOT_CELLPACK"),
    ("SD_Backpack", "Backpack", "SD_GOT_BACKPACK"),
]

# The Tag of each Doom ammo pool; these engine ids ARE ours to override.
AMMO_TAG_IDS = ["AMMO_CLIP", "AMMO_SHELLS", "AMMO_ROCKETS", "AMMO_CELLS"]

# These engine ids are NOT ours to override: Freedoom's DEHACKED lump wins.
DEHACKED_OWNED_IDS = [
    "GOTCLIP", "GOTCLIPBOX", "GOTSHELLS", "GOTSHELLBOX",
    "GOTROCKET", "GOTROCKBOX", "GOTCELL", "GOTCELLBOX", "GOTBACKPACK",
]


def _blocks(text: str, kind: str) -> list[str]:
    return re.findall(rf"^{kind}\s*\{{(.*?)\}}", text, flags=re.S | re.M)


def _udmf_things(text: str) -> list[str]:
    return re.findall(r"^thing\s*\{(.*?)\}", text, flags=re.S | re.M)


# --- A small UDMF reader for the start-inventory test ----------------------
# Read from the TEXTMAP inside the built PK3, not from the map builder, so
# the test sees what the engine sees.

MAX_STEP_UP = 24     # the tallest floor change a player walks up (Doom's 24)
PLAYER_HEIGHT = 56   # the shortest gap a player fits through
ED_PLAYER1_START = 1
SKILL_FLAGS = ("skill1", "skill2", "skill3", "skill4", "skill5")


def _udmf_blocks(text: str) -> dict[str, list[dict]]:
    """{block kind: [{field: value}]}; numbers, booleans and strings."""
    out: dict[str, list[dict]] = {}
    for kind, body in re.findall(r"^(\w+)\s*\{(.*?)\}", text, flags=re.S | re.M):
        fields: dict[str, object] = {}
        for key, raw in re.findall(r"(\w+)\s*=\s*([^;]+);", body):
            raw = raw.strip()
            if raw in ("true", "false"):
                fields[key] = raw == "true"
            elif raw.startswith('"'):
                fields[key] = raw[1:-1]
            else:
                fields[key] = float(raw) if "." in raw else int(raw)
        out.setdefault(kind, []).append(fields)
    return out


def _sector_at(blocks: dict, x: float, y: float) -> int | None:
    """The sector holding (x, y): the nearest linedef crossed by a ray cast
    east, and which side of it the point is on (front = right of v1->v2)."""
    y += 0.25   # never exactly level with a vertex
    verts, sides = blocks["vertex"], blocks["sidedef"]
    best = None
    for ld in blocks["linedef"]:
        a, b = verts[ld["v1"]], verts[ld["v2"]]
        if (a["y"] > y) == (b["y"] > y):
            continue
        cross_x = a["x"] + (y - a["y"]) * (b["x"] - a["x"]) / (b["y"] - a["y"])
        if cross_x > x and (best is None or cross_x < best[0]):
            best = (cross_x, ld, a, b)
    if best is None:
        return None
    _, ld, a, b = best
    right = (b["x"] - a["x"]) * (y - a["y"]) - (b["y"] - a["y"]) * (x - a["x"]) < 0
    if right:
        return sides[ld["sidefront"]]["sector"]
    return sides[ld["sideback"]]["sector"] if "sideback" in ld else None


def _walkable_from(blocks: dict, start: int) -> set[int]:
    """Sectors a player walks to from `start` as the map loads: every door
    shut (a shut door is a sector whose ceiling sits on its floor, so no
    player fits through it), no switch thrown, no step over 24 units."""
    sectors, sides = blocks["sector"], blocks["sidedef"]
    links: dict[int, set[int]] = {}
    for ld in blocks["linedef"]:
        if "sideback" not in ld or ld.get("blocking") or ld.get("blockplayers"):
            continue
        a, b = sides[ld["sidefront"]]["sector"], sides[ld["sideback"]]["sector"]
        for src, dst in ((a, b), (b, a)):
            s, d = sectors[src], sectors[dst]
            gap = min(s["heightceiling"], d["heightceiling"]) - max(s["heightfloor"], d["heightfloor"])
            if gap >= PLAYER_HEIGHT and d["heightfloor"] - s["heightfloor"] <= MAX_STEP_UP:
                links.setdefault(src, set()).add(dst)
    seen, stack = {start}, [start]
    while stack:
        for nxt in links.get(stack.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


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

    def _start_items(self) -> list[str]:
        """The class names of SD_Player's StartItem lines, in order."""
        player = next(b for n, b in self.zs.items() if f"class {PLAYER_CLASS}" in b)
        code = "\n".join(line.split("//")[0] for line in player.splitlines())
        return re.findall(r'Player\.StartItem\s+"(\w+)"', code)

    def test_the_player_starts_with_the_tt33_and_its_rounds_only(self):
        """The TT-33 is the only start weapon, so it is the one raised on
        spawn; no Fist and no shovel, so slot 1 is empty until a pickup. The
        rounds come after the weapon, in Doom's order: GiveDefaultInventory
        readies a weapon only if its ammo is already there (BALANCE 2)."""
        items = self._start_items()
        weapons = {cls_name for cls_name, _, _ in ARSENAL.values()} | {"Fist", "Pistol"}
        self.assertEqual(["SD_Tokarev"], [n for n in items if n in weapons])
        self.assertEqual(["SD_Tokarev", "Clip"], items)
        self.assertNotIn("Fist", items)

    def test_the_shovel_is_picked_up_in_map01s_dorm_on_every_skill(self):
        """The player does not start with the shovel; it is got by picking it
        up, and MAP01 puts it on the dorm's rack, reached from the player
        start on every skill with no door opened (CEO bug, 2026-10-13: the
        rack showed a pickup the player could not take because he already
        owned one)."""
        self.assertNotIn("SD_Shovel", self._start_items())
        shovel = self.zs["zscript/weapons/shovel.zs"]
        spawn = re.search(r"^\s*Spawn:(.*?)^\s*Stop;", shovel, flags=re.S | re.M)
        self.assertIsNotNone(spawn, "SD_Shovel needs a Spawn state to lie on a map")
        frames = re.findall(r"^\s*([A-Z0-9]{4})\s+A\s+-1\s*;", spawn.group(1), flags=re.M)
        self.assertTrue(frames and "TNT1" not in frames,
                        "SD_Shovel's Spawn state must show a sprite, or the pickup is invisible")
        self.assertIn("Inventory.PickupMessage", shovel)

        blob = self.zf.read("maps/MAP01.wad")
        blocks = _udmf_blocks(wad.read_lump(blob, "TEXTMAP").decode("ascii"))
        starts = [t for t in blocks["thing"] if t["type"] == ED_PLAYER1_START]
        shovels = [t for t in blocks["thing"] if t["type"] == ARSENAL[1][2]]
        self.assertEqual(1, len(starts), "MAP01 needs one player 1 start")
        self.assertEqual(1, len(shovels), "MAP01 places exactly one shovel")
        rack = shovels[0]
        for flag in SKILL_FLAGS:
            self.assertTrue(rack.get(flag), f"the MAP01 shovel is missing on {flag}")
        start = _sector_at(blocks, starts[0]["x"], starts[0]["y"])
        where = _sector_at(blocks, rack["x"], rack["y"])
        self.assertIsNotNone(start, "the player start is outside the map")
        self.assertIsNotNone(where, "the MAP01 shovel is inside a wall")
        self.assertIn(where, _walkable_from(blocks, start),
                      "the MAP01 shovel cannot be reached from the start without a door")

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

    def _language_sections(self) -> tuple[str, str]:
        """Split LANGUAGE on the `[ru]` HEADER, not on the first `[ru]` text.

        A comment mentioning the section name used to cut the English half in
        two and make the checks below pass on strings that were not there.
        """
        parts = re.split(r"^\[ru\]\s*$", self.language, flags=re.M)
        self.assertEqual(len(parts), 2, "LANGUAGE must have exactly one [ru] header (D7)")
        return parts[0], parts[1]

    def test_every_language_id_used_by_the_arsenal_exists_in_both_languages(self):
        ids = set(re.findall(r'"\$(SD_[A-Z0-9_]+)"', self.zs_all))
        ids |= set(re.findall(r'lookup\s+"(SD_[A-Z0-9_]+)"', self.mapinfo))
        self.assertTrue(ids, "the arsenal must use LANGUAGE ids, not literals")
        enu, ru = self._language_sections()
        self.assertTrue(ru, "LANGUAGE must have a [ru] section (D7)")
        for ident in sorted(ids):
            self.assertRegex(enu, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [enu default]")
            self.assertRegex(ru, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [ru]")


    # --- Ammunition (CEO 2026-10-13) ---------------------------------------

    def test_every_ammo_pickup_is_reskinned_and_keeps_its_doom_pool(self):
        """Freedoom's DEHACKED beats our LANGUAGE for GOTCLIP & friends, so
        the Soviet pickup lines must come from our own subclasses."""
        body = self.zs["zscript/sd/ammo.zs"]
        for cls_name, parent, ident in AMMO_PICKUPS:
            self.assertRegex(
                body,
                re.compile(rf"class\s+{cls_name}\s*:\s*{parent}\s+replaces\s+{parent}\b"),
                f"{cls_name} must subclass AND replace {parent} "
                f"(subclassing is what keeps the Doom ammo pool)",
            )
            self.assertIn(
                f'"${ident}"', body, f"{cls_name} must take its pickup line from ${ident}"
            )

    def test_no_ammo_string_relies_on_an_engine_pickup_id(self):
        """GOTCLIP/GOTSHELLS/... are overridden by Freedoom's DEHACKED lump:
        setting them here would look right and do nothing (verified 2026-10-13)."""
        enu, ru = self._language_sections()
        for ident in DEHACKED_OWNED_IDS:
            for section, name in ((enu, "[enu default]"), (ru, "[ru]")):
                self.assertNotRegex(
                    section,
                    re.compile(rf"^{ident}\s*=", re.M),
                    f"{ident} is a DEHACKED-owned id; use an SD_GOT_* id instead ({name})",
                )

    def test_the_four_ammo_pools_are_renamed_in_both_languages(self):
        enu, ru = self._language_sections()
        for ident in AMMO_TAG_IDS:
            self.assertRegex(enu, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [enu default]")
            self.assertRegex(ru, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in [ru]")

    def test_the_english_section_is_ascii_until_t17(self):
        """The English section is ASCII by record, not by necessity (T17).

        Debt T9 (no Cyrillic glyphs on Freedoom) was paid by D24 on
        2026-10-13, so non-ASCII no longer prints blank. The English
        designations are still the Latin transliteration, and this test pins
        that so the switch to the Cyrillic forms D17 asks for (MOD-SPEC 6.4,
        debt T17) is a deliberate change with an engine screenshot, not a
        stray character. Flip or delete this test in that change.
        """
        enu, _ = self._language_sections()
        for line in enu.splitlines():
            code = line.split("//")[0]
            self.assertTrue(
                all(ch.isascii() or ch in GERMAN_LETTERS for ch in code),
                f"non-ASCII in the English section: switching to Cyrillic is debt T17, do it deliberately: {line!r}",
            )

    # --- Sounds: regressions -----------------------------------------------

    def test_no_chainsaw_lump_is_used_as_a_placeholder(self):
        """The CEO heard a chainsaw when swinging the shovel (2026-10-13)."""
        for logical, lump in self._sndinfo_names().items():
            self.assertNotIn(
                "SAW", lump.upper(), f"{logical} points at the chainsaw lump {lump}"
            )

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
        enu, ru = self._language_sections()
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
