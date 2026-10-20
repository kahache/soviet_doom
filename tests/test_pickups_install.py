"""D80 (2026-10-20): the campaign's health, armour, area map, backpack and
yellow and red passes wear our own sprites (backlog M2a-i).

The CEO chose one option per object of the campaign pickups sweep
(tools/art/gen_items.py, its CHOSEN table): the recommended option except
SDAG C, SDAH C and SDBP B, and the hand Katyusha's floor pickup SDHP A.
MOD-SPEC 6.3, "The campaign pickups, installed by D80". What is checked,
and why:

  classes    every class exists in its file as `SD_X : X replaces X`, is
             included from zscript.txt, overrides only Spawn, and that Spawn
             is the Doom parent's line for line (label, frames, tics,
             Bright, flow) with only the four-letter name changed. Where a
             gzdoom.pk3 is installed the parents' lines are read from it and
             compared with the copy recorded here (g4.14.2)
  defaults   each Default block is exactly the pickup line, plus the passes'
             Species, the armours' icon and the medikit's low-health line
  keys       the passes open their locks by Species: lock 3 lists
             YellowCard, lock 1 RedCard (lockdefs.txt, read from the
             installed gzdoom.pk3 where present), MAP03 places 6 and 13 and
             asks for locks 3 and 1
  sprites    assets/sprites/pickups/ holds every frame each Spawn names, RGBA
             with a grAb chunk (centred, standing), all frames of a set the
             same size, byte-identical to the chosen option's render in
             work/art/items/ (where work/ exists) and not to another option's
  hud        STKEYS0-2 ship as indexed 7x5 graphics byte-identical to the
             generator's key icons; the armours' icons name shipped frames;
             no IWAD-named sprite ships (MEDIA0 stays Freedoom's, MOD-SPEC 1)
  lines      every pickup id and the four lock lines are in [enu default]
             and [ru] with the texts drafted in the preview
  maps       every Doom pickup the campaign maps (MAP01-MAP03) place is
             replaced by a class of ours whose Spawn names only SD sprites,
             and none of the retired Freedoom lumps is named by a state
  docs       MOD-SPEC 5.1 no longer declares the retired lumps, 6.3 reserves
             the names, every file has a licence row, check_pk3's sprites
             and licences categories pass on the built PK3

The hand Katyusha's Spawn lives in zscript/weapons/katyusha.zs, owned by
another task at the install, so its picture waited for the weapon's own
install (D84, 2026-10-20): since then the line names SDHP, SDHPA0 ships like
the rest and the BFUG row is gone from MOD-SPEC 5.1, all checked here with
no skip (MOD-SPEC 6.3, "The Katyusha's pickup, installed with D84").

Stdlib only.
"""

from __future__ import annotations

import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
ZS_DIR = SRC_DIR / "zscript"
PICKUPS = PROJECT_ROOT / "assets" / "sprites" / "pickups"
HUD_GRAPHICS = PROJECT_ROOT / "assets" / "graphics" / "hud"
WORK_ITEMS = PROJECT_ROOT / "work" / "art" / "items"
GEN_ITEMS = TOOLS_DIR / "art" / "gen_items.py"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
LANGUAGE = SRC_DIR / "lumps" / "LANGUAGE"
ZSCRIPT_TXT = SRC_DIR / "lumps" / "zscript.txt"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_pickup_sprites import (PNG_RGBA, PNG_SIGNATURE, block, class_body, installed_gzdoom_pk3,  # noqa: E402
                                 norm, parse_states, read_grab, strip_comments)

PNG_INDEXED = 3   # IHDR colour type


def _still(sprite: str) -> tuple:
    return (("Spawn", sprite, "A", -1, ""), ("Spawn", "->", "Stop", 0, ""))


def _blink(sprite: str, tics_b: int, a: int = 6) -> tuple:
    return (("Spawn", sprite, "A", a, ""), ("Spawn", sprite, "B", tics_b, "bright"), ("Spawn", "->", "loop", 0, ""))


def _cycle(sprite: str, rest: str = "") -> tuple:
    return (("Spawn", sprite, "ABCDCB", 6, rest), ("Spawn", "->", "Loop", 0, ""))


# Each Doom parent's Spawn as GZDoom g4.14.2's gzdoom.pk3 writes it
# (zscript/actors/doom/doomhealth.zs, doomarmor.zs, doomartifacts.zs,
# doomammo.zs, doomkeys.zs, weaponbfg.zs; read 2026-10-20). Rows as in
# tests/test_pickup_sprites.py.
DOOM_SPAWN = {
    "Stimpack": _still("STIM"),
    "Medikit": _still("MEDI"),
    "HealthBonus": _cycle("BON1"),
    "ArmorBonus": (("Spawn", "BON2", "ABCDCB", 6, ""), ("Spawn", "->", "loop", 0, "")),
    "GreenArmor": _blink("ARM1", 7),
    "BlueArmor": _blink("ARM2", 6),
    "Allmap": _cycle("PMAP", "Bright"),
    "Backpack": _still("BPAK"),
    "YellowCard": _blink("YKEY", 10, 10),
    "RedCard": _blink("RKEY", 10, 10),
    "BFG9000": _still("BFUG"),
}
PARENT_FILE = {"Stimpack": "doomhealth.zs", "Medikit": "doomhealth.zs", "HealthBonus": "doomhealth.zs",
               "ArmorBonus": "doomarmor.zs", "GreenArmor": "doomarmor.zs", "BlueArmor": "doomarmor.zs",
               "Allmap": "doomartifacts.zs", "Backpack": "doomammo.zs", "YellowCard": "doomkeys.zs",
               "RedCard": "doomkeys.zs", "BFG9000": "weaponbfg.zs"}

# class -> (file under src/zscript/, Doom parent, gen_items item, option
# chosen in D80, our sprite, frames)
CLASSES = {
    "SD_Stimpack":     ("sd/pickups.zs", "Stimpack", "stim", "A", "SDBN", "A"),
    "SD_Medikit":      ("sd/pickups.zs", "Medikit", "medikit", "A", "SDMD", "A"),
    "SD_HealthBonus":  ("sd/pickups.zs", "HealthBonus", "hbonus", "B", "SDHB", "ABCD"),
    "SD_ArmorBonus":   ("sd/pickups.zs", "ArmorBonus", "abonus", "A", "SDAB", "ABCD"),
    "SD_GreenArmor":   ("sd/pickups.zs", "GreenArmor", "garmor", "C", "SDAG", "AB"),
    "SD_BlueArmor":    ("sd/pickups.zs", "BlueArmor", "barmor", "C", "SDAH", "AB"),
    "SD_Allmap":       ("sd/pickups.zs", "Allmap", "allmap", "A", "SDMP", "ABCD"),
    "SD_Backpack":     ("sd/ammo.zs", "Backpack", "backpack", "B", "SDBP", "A"),
    "SD_YellowPass":   ("sd/keys.zs", "YellowCard", "ykey", "A", "SDKY", "AB"),
    "SD_RedPass":      ("sd/keys.zs", "RedCard", "rkey", "A", "SDKK", "AB"),
    "SD_HandKatyusha": ("weapons/katyusha.zs", "BFG9000", "katyusha", "A", "SDHP", "A"),
}
KATYUSHA = "SD_HandKatyusha"
D80_CHOICE = {item: option for _, _, item, option, _, _ in CLASSES.values()}

# The Default blocks (whitespace collapsed, comments stripped).
DEFAULTS = {
    "SD_Stimpack": 'Inventory.PickupMessage "$SD_GOT_STIMPACK";',
    "SD_Medikit": 'Inventory.PickupMessage "$SD_GOT_MEDIKIT"; '
                  'Health.LowMessage SD_MEDIKIT_LOW_HEALTH, "$SD_GOT_MEDIKIT";',
    "SD_HealthBonus": 'Inventory.PickupMessage "$SD_GOT_HEALTHBONUS";',
    "SD_ArmorBonus": 'Inventory.PickupMessage "$SD_GOT_ARMORBONUS"; Inventory.Icon "SDABA0";',
    "SD_GreenArmor": 'Inventory.PickupMessage "$SD_GOT_ARMOR"; Inventory.Icon "SDAGA0";',
    "SD_BlueArmor": 'Inventory.PickupMessage "$SD_GOT_MEGAARMOR"; Inventory.Icon "SDAHA0";',
    "SD_Allmap": 'Inventory.PickupMessage "$SD_GOT_MAP";',
    "SD_Backpack": 'Inventory.PickupMessage "$SD_GOT_BACKPACK";',
    "SD_YellowPass": 'Species "YellowCard"; Inventory.PickupMessage "$SD_PICKUP_YELLOWPASS";',
    "SD_RedPass": 'Species "RedCard"; Inventory.PickupMessage "$SD_PICKUP_REDPASS";',
}
MEDIKIT_LOW_HEALTH = 25          # Medikit's own threshold, doomhealth.zs

# The lines drafted in the preview for the chosen options (EN, RU).
LINES = {
    "SD_GOT_STIMPACK": ("A field dressing.", "Перевязочный пакет."),
    "SD_GOT_MEDIKIT": ("A first-aid box.", "Аптечка."),
    "SD_GOT_HEALTHBONUS": ("Zelyonka.", "Зелёнка."),
    "SD_GOT_ARMORBONUS": ("A steel helmet.", "Стальной шлем."),
    "SD_GOT_ARMOR": ("A flak vest and a helmet.", "Бронежилет и каска."),
    "SD_GOT_MEGAARMOR": ("A steel breastplate and helmet!", "Стальной нагрудник и каска!"),
    "SD_GOT_MAP": ("A commander's map case. The whole area is on it.",
                   "Командирский планшет. На карте — вся местность."),
    "SD_GOT_BACKPACK": ("A paratrooper's pack. Everything you can carry!", "Рюкзак десантника. Всё, что можно унести!"),
    "SD_PICKUP_YELLOWPASS": ("Yellow pass.", "Жёлтый пропуск."),
    "SD_PICKUP_REDPASS": ("Red pass.", "Красный пропуск."),
    "SD_PICKUP_KATYUSHA": ("You got the hand Katyusha. Prototype. Do not drop it.",
                           "Вы подобрали ручную «Катюшу». Опытный образец. Не ронять."),
    "PD_YELLOWC": ("You need a yellow pass to open this door", "Для открытия нужен жёлтый пропуск"),
    "PD_YELLOWCO": ("You need a yellow pass to activate this object", "Для применения нужен жёлтый пропуск"),
    "PD_REDC": ("You need a red pass to open this door", "Для открытия нужен красный пропуск"),
    "PD_REDCO": ("You need a red pass to activate this object", "Для применения нужен красный пропуск"),
}

# Locks the passes open: lock -> the key class lockdefs.txt lists (g4.14.2).
LOCKS = {3: "YellowCard", 1: "RedCard"}
KEY_EDNUMS = {6: "YellowCard", 13: "RedCard"}
RETIRED = ("STIM", "MEDI", "BON1", "BON2", "ARM1", "ARM2", "PMAP", "BPAK", "YKEY", "RKEY")

# Doom's own pickups by editor number (the Doom II set). A campaign map that
# places one must find a class of ours replacing it.
DOOM_PICKUPS = {
    2011: "Stimpack", 2012: "Medikit", 2013: "Soulsphere", 2014: "HealthBonus", 2015: "ArmorBonus",
    2018: "GreenArmor", 2019: "BlueArmor", 2022: "InvulnerabilitySphere", 2023: "Berserk",
    2024: "BlurSphere", 2025: "RadSuit", 2026: "Allmap", 2045: "Infrared", 83: "Megasphere",
    8: "Backpack", 5: "BlueCard", 6: "YellowCard", 13: "RedCard", 38: "RedSkull", 39: "YellowSkull",
    40: "BlueSkull", 2007: "Clip", 2048: "ClipBox", 2008: "Shell", 2049: "ShellBox", 2010: "RocketAmmo",
    2046: "RocketBox", 2047: "Cell", 17: "CellPack", 2001: "Shotgun", 2002: "Chaingun",
    2003: "RocketLauncher", 2004: "PlasmaRifle", 2006: "BFG9000",
}
CAMPAIGN = ("MAP01", "MAP02", "MAP03")
ARSENAL_EDNUMS = range(21001, 21100)   # MAPINFO DoomEdNums: the arsenal's own numbers

RE_REPLACES = re.compile(r"\bclass\s+(\w+)\s*:\s*(\w+)\s+replaces\s+(\w+)")
RE_LINE = re.compile(r'^\s*(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', re.M)


def zs_source(rel: str) -> str:
    return strip_comments((ZS_DIR / rel).read_text(encoding="utf-8"))


def body(cls: str) -> str:
    return class_body(zs_source(CLASSES[cls][0]), cls)


def spawn_rows(cls: str) -> list[tuple]:
    states = block(body(cls), "States")
    if states is None:
        raise AssertionError(f"{cls}: no States block")
    return parse_states(states, cls)


def our_spawn(cls: str) -> list[tuple]:
    """The Spawn label's rows only (a weapon has other labels)."""
    return parse_states_lenient(block(body(cls), "States"))


def renamed(cls: str) -> list[tuple]:
    _, parent, _, _, ours, _ = CLASSES[cls]
    old = DOOM_SPAWN[parent][0][1]
    return [(lb, ours if sp == old else sp, fr, tics, rest) for lb, sp, fr, tics, rest in DOOM_SPAWN[parent]]


def expected_files() -> dict[str, tuple[str, str]]:
    """PNG name -> (gen_items item, chosen option), the Katyusha's included
    since D84."""
    out = {}
    for cls, (_, _, item, option, ours, frames) in CLASSES.items():
        for fr in frames:
            out[f"{ours}{fr}0.png"] = (item, option)
    return out


def language_sections() -> dict[str, dict[str, str]]:
    """{section header: {id: text}} for the single-line entries."""
    text = re.sub(r"(?m)^\s*//[^\n]*$", "", LANGUAGE.read_text(encoding="utf-8"))
    parts = re.split(r"(?m)^\[([^\]]+)\]\s*$", text)
    return {parts[i].strip(): dict(RE_LINE.findall(parts[i + 1])) for i in range(1, len(parts), 2)}


def png_header(data: bytes) -> tuple[int, int, int]:
    width, height, _, colour_type = struct.unpack(">IIBB", data[16:26])
    return width, height, colour_type


def built_things(pk3: Path) -> dict[str, list[dict]]:
    out = {}
    with zipfile.ZipFile(pk3) as zf:
        for name in zf.namelist():
            if not (name.startswith("maps/") and name.endswith(".wad")):
                continue
            blob = zf.read(name)
            directory = check_pk3.read_wad_directory(blob)
            textmap = next(blob[o:o + s] for n, o, s in directory if n == "TEXTMAP")
            udmf = check_pk3.parse_udmf(textmap.decode("latin-1"))
            out[Path(name).stem] = [b.fields for b in udmf.of_kind("thing")]
    return out


def all_replacers() -> dict[str, tuple[str, str]]:
    """Doom class -> (our class, its file) for every `replaces` in src/zscript."""
    out = {}
    for path in sorted(ZS_DIR.rglob("*.zs")):
        code = strip_comments(path.read_text(encoding="utf-8"))
        for ours, _parent, doom in RE_REPLACES.findall(code):
            out[doom] = (ours, path.relative_to(ZS_DIR).as_posix())
    return out


def doomednums() -> dict[int, str]:
    text = (SRC_DIR / "lumps" / "MAPINFO").read_text(encoding="utf-8")
    m = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S)
    return {int(n): c for n, c in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\w+)", m.group(1))}


class ClassTests(unittest.TestCase):
    def test_each_class_replaces_its_doom_class(self):
        for cls, (rel, parent, *_rest) in CLASSES.items():
            with self.subTest(cls=cls):
                self.assertRegex(zs_source(rel), rf"\bclass\s+{cls}\s*:\s*{parent}\s+replaces\s+{parent}\b")

    def test_pickups_zs_is_included_once(self):
        text = ZSCRIPT_TXT.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'(?m)^#include "zscript/sd/pickups\.zs"', text)), 1)

    def test_spawn_is_dooms_with_the_name_changed(self):
        for cls in CLASSES:
            with self.subTest(cls=cls):
                self.assertEqual(norm(our_spawn(cls)), norm(renamed(cls)))
                self.assertEqual(sum(r[3] for r in our_spawn(cls)), sum(r[3] for r in DOOM_SPAWN[CLASSES[cls][1]]))

    def test_only_spawn_is_overridden(self):
        for cls in CLASSES:
            if cls == KATYUSHA:
                continue
            self.assertEqual({r[0] for r in spawn_rows(cls)}, {"Spawn"}, cls)

    def test_spawn_names_only_the_frames_installed(self):
        for cls, (_, _, _, _, ours, frames) in CLASSES.items():
            named = {f for r in our_spawn(cls) if r[1] != "->" for f in r[2]}
            self.assertEqual("".join(sorted(named)), frames, cls)

    def test_default_blocks(self):
        for cls, want in DEFAULTS.items():
            got = block(body(cls), "Default")
            self.assertEqual(" ".join(got.split()), want, cls)

    def test_medikit_low_health_is_dooms_threshold(self):
        self.assertRegex(body("SD_Medikit"), rf"const\s+SD_MEDIKIT_LOW_HEALTH\s*=\s*{MEDIKIT_LOW_HEALTH}\s*;")

    def test_katyusha_pickup(self):
        self.assertEqual(norm(our_spawn(KATYUSHA)), norm(renamed(KATYUSHA)))

    def test_doom_parents_where_a_gzdoom_pk3_is_installed(self):
        pk3 = installed_gzdoom_pk3()
        if pk3 is None:
            self.skipTest("no gzdoom.pk3 installed (CI): the recorded g4.14.2 copy stands in")
        with zipfile.ZipFile(pk3) as zf:
            files = {f: strip_comments(zf.read(f"zscript/actors/doom/{f}").decode("utf-8", "replace"))
                     for f in set(PARENT_FILE.values())}
        for parent, rows in DOOM_SPAWN.items():
            with self.subTest(parent=parent):
                states = parse_states_lenient(block(class_body(files[PARENT_FILE[parent]], parent), "States"))
                self.assertEqual(norm([r for r in states if r[0] == "Spawn"]), norm(rows))

    def test_the_icons_and_states_name_no_retired_lump(self):
        for path in sorted(ZS_DIR.rglob("*.zs")):
            code = strip_comments(path.read_text(encoding="utf-8"))
            for old in RETIRED:
                with self.subTest(file=path.name, lump=old):
                    self.assertNotRegex(code, rf"(?m)^\s*{old}\s+[A-Z]")
                    self.assertNotIn(f'"{old}A0"', code)


def parse_states_lenient(states: str) -> list[tuple]:
    """A weapon's States block carries action calls (`BFGG A 1 A_Raise;`)
    the strict parser rejects; keep the Spawn label's rows only."""
    label, keep = None, []
    for line in states.splitlines():
        m = re.match(r"^\s*(\w+):\s*$", line)
        if m:
            label = m.group(1)
            continue
        if label == "Spawn" and line.strip():
            keep.append(line)
    return [("Spawn",) + r[1:] for r in parse_states("Spawn:\n" + "\n".join(keep), "Spawn")]


class KeyTests(unittest.TestCase):
    def test_species_is_the_lock_s_key(self):
        for cls in ("SD_YellowPass", "SD_RedPass"):
            parent = CLASSES[cls][1]
            self.assertRegex(block(body(cls), "Default"), rf'Species\s+"{parent}"\s*;', cls)
            self.assertIn(parent, LOCKS.values())

    def test_locks_list_the_doom_keys_where_a_gzdoom_pk3_is_installed(self):
        pk3 = installed_gzdoom_pk3()
        if pk3 is None:
            self.skipTest("no gzdoom.pk3 installed (CI)")
        with zipfile.ZipFile(pk3) as zf:
            text = zf.read("lockdefs.txt").decode("utf-8", "replace")
        for lock, key in LOCKS.items():
            m = re.search(rf"Lock\s+{lock}\s+Doom\s*\{{(.*?)\}}", text, re.S)
            self.assertIsNotNone(m, lock)
            members = re.findall(r"(?m)^\s*([A-Za-z]\w*)\s*$", strip_comments(m.group(1)))
            self.assertIn(key, members, lock)

    def test_map03_asks_for_the_locks(self):
        text = (SRC_DIR / "maps" / "MAP03" / "map.py").read_text(encoding="utf-8")
        self.assertRegex(text, r"LOCK_RED_CARD\s*=\s*1\b")
        self.assertRegex(text, r"LOCK_YELLOW_CARD\s*=\s*3\b")


class FileTests(unittest.TestCase):
    def test_every_frame_is_installed(self):
        names = {p.name for p in PICKUPS.glob("*.png")}
        for name in expected_files():
            self.assertIn(name, names)

    def test_the_katyusha_picture_ships_with_its_line(self):
        """D84: SD_HandKatyusha's Spawn names SDHP and SDHPA0 ships."""
        self.assertEqual([r[1:4] for r in our_spawn(KATYUSHA) if r[1] != "->"], [("SDHP", "A", -1)])
        self.assertTrue((PICKUPS / "SDHPA0.png").is_file())

    def test_rgba_with_offsets_standing_on_the_floor(self):
        for name in expected_files():
            data = (PICKUPS / name).read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), name)
            width, height, colour_type = png_header(data)
            self.assertEqual(colour_type, PNG_RGBA, name)
            self.assertEqual(read_grab(data), (width // 2, height), name)

    def test_frames_of_a_set_share_size_and_offsets(self):
        for cls, (_, _, _, _, ours, frames) in CLASSES.items():
            heads = {(png_header((PICKUPS / f"{ours}{fr}0.png").read_bytes())[:2],
                      read_grab((PICKUPS / f"{ours}{fr}0.png").read_bytes())) for fr in frames}
            self.assertEqual(len(heads), 1, ours)

    def test_frames_differ(self):
        for cls, (_, _, _, _, ours, frames) in CLASSES.items():
            data = [(PICKUPS / f"{ours}{fr}0.png").read_bytes() for fr in frames]
            self.assertEqual(len(set(data)), len(data), ours)

    def test_chosen_options_are_the_generators(self):
        text = GEN_ITEMS.read_text(encoding="utf-8")
        m = re.search(r"CHOSEN = \{(.*?)\}", text, re.S)
        self.assertEqual(dict(re.findall(r'"(\w+)": "([ABC])"', m.group(1))), D80_CHOICE)

    @unittest.skipUnless(WORK_ITEMS.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_chosen_render(self):
        for name, (item, option) in expected_files().items():
            installed_bytes = (PICKUPS / name).read_bytes()
            self.assertEqual(installed_bytes, (WORK_ITEMS / item / option / name).read_bytes(), name)
            for other in "ABC":
                p = WORK_ITEMS / item / other / name
                if other != option and p.is_file():
                    self.assertNotEqual(installed_bytes, p.read_bytes(), f"{name}: option {other}")


class HudTests(unittest.TestCase):
    def test_key_icons_are_indexed_7x5(self):
        for i in range(3):
            data = (HUD_GRAPHICS / f"STKEYS{i}.png").read_bytes()
            self.assertEqual(png_header(data), (7, 5, PNG_INDEXED), i)

    @unittest.skipUnless((WORK_ITEMS / "hud").is_dir(), "work/ not present (CI has no work/)")
    def test_key_icons_are_the_generators(self):
        for i in range(3):
            name = f"STKEYS{i}.png"
            self.assertEqual((HUD_GRAPHICS / name).read_bytes(), (WORK_ITEMS / "hud" / name).read_bytes(), name)

    def test_only_the_three_key_icons(self):
        self.assertEqual({p.name for p in HUD_GRAPHICS.iterdir()}, {f"STKEYS{i}.png" for i in range(3)})

    def test_no_iwad_named_sprite_ships(self):
        """MEDIA0 (the fullscreen HUD's health icon) stays Freedoom's: our
        sprites carry the SD prefix (MOD-SPEC 1). The one documented
        exception is D82's engine-actor overrides (PUFF, BLUD, TFOG, IFOG,
        BAR1, BEXP, COLU), all in assets/sprites/effects/
        (tests/test_effects_install.py)."""
        sprites = PROJECT_ROOT / "assets" / "sprites"
        overrides = ("PUFF", "BLUD", "TFOG", "IFOG", "BAR1", "BEXP", "COLU")
        self.assertEqual([p for p in sprites.rglob("*.png") if not p.stem.startswith("SD")
                          and not (p.stem[:4] in overrides and p.parent.name == "effects")], [])

    def test_armour_icons_are_shipped_frames(self):
        for cls in ("SD_ArmorBonus", "SD_GreenArmor", "SD_BlueArmor"):
            icon = re.search(r'Inventory\.Icon\s+"(\w+)"', block(body(cls), "Default")).group(1)
            self.assertTrue((PICKUPS / f"{icon}.png").is_file(), cls)
            self.assertTrue(icon.startswith(CLASSES[cls][4]), cls)


class LineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = language_sections()

    def test_both_languages_carry_every_line(self):
        for key, (en, ru) in LINES.items():
            with self.subTest(id=key):
                self.assertEqual(self.sections["enu default"].get(key), en)
                self.assertEqual(self.sections["ru"].get(key), ru)

    def test_every_pickup_message_is_a_line(self):
        for cls in CLASSES:
            m = re.search(r'Inventory\.PickupMessage\s+"\$(\w+)"', block(body(cls), "Default"))
            self.assertIsNotNone(m, cls)
            self.assertIn(m.group(1), LINES, cls)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")
        cls.things = built_things(cls.pk3)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_under_the_engine_names(self):
        with zipfile.ZipFile(self.pk3) as zf:
            names = set(zf.namelist())
        for name in expected_files():
            self.assertIn(f"sprites/{name}", names)
        for i in range(3):
            self.assertIn(f"graphics/STKEYS{i}.png", names)

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        self.assertEqual([], [f for f in report.errors if f.category in ("sprites", "licences")])

    def test_campaign_maps_place_the_keys(self):
        placed = {int(t["type"]) for t in self.things["MAP03"]}
        self.assertLessEqual(set(KEY_EDNUMS), placed)

    def test_every_doom_pickup_in_the_campaign_wears_our_sprite(self):
        replacers = all_replacers()
        seen = set()
        for level in CAMPAIGN:
            for t in self.things[level]:
                ed = int(t["type"])
                if ed in DOOM_PICKUPS:
                    seen.add(ed)
        self.assertTrue(seen)
        for ed in sorted(seen):
            doom = DOOM_PICKUPS[ed]
            with self.subTest(ednum=ed, doom=doom):
                self.assertIn(doom, replacers)
                ours, rel = replacers[doom]
                code = strip_comments((ZS_DIR / rel).read_text(encoding="utf-8"))
                spawn = parse_states_lenient(block(class_body(code, ours), "States"))
                sprites = {r[1] for r in spawn if r[1] != "->"}
                self.assertTrue(sprites)
                self.assertTrue(all(s.startswith("SD") for s in sprites), sprites)

    def test_our_own_editor_numbers_in_the_campaign(self):
        """The arsenal's own numbers (21001-21007): every pickup state SD,
        the hand Katyusha's included since D84."""
        eds = doomednums()
        for level in CAMPAIGN:
            for t in self.things[level]:
                ed = int(t["type"])
                if ed not in ARSENAL_EDNUMS or not eds.get(ed, "").startswith("SD_"):
                    continue
                cls = eds[ed]
                path = next(p for p in ZS_DIR.rglob("*.zs")
                            if re.search(rf"\bclass\s+{cls}\b", p.read_text(encoding="utf-8")))
                states = block(class_body(strip_comments(path.read_text(encoding="utf-8")), cls), "States")
                spawn = parse_states_lenient(states)
                with self.subTest(level=level, cls=cls):
                    self.assertTrue(spawn)
                    self.assertTrue(all(r[1].startswith("SD") for r in spawn if r[1] != "->"))


class DocTests(unittest.TestCase):
    def test_mod_spec_5_1_retires_them(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        for old in RETIRED:
            self.assertNotIn(old, declared)
        self.assertNotIn("BFUG", declared, "the Katyusha's Spawn names SDHP: its row is retired (D84)")

    def test_mod_spec_6_3_reserves_the_names(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        section = spec[spec.index("### 6.3 "):spec.index("### 6.4 ")]
        for cls, (_, parent, _, _, ours, _) in CLASSES.items():
            self.assertRegex(section, rf"\| `{cls}` \(`{parent}`\)[^|]*\| `{ours}` \|", cls)

    def test_every_file_has_a_licence_row(self):
        licensed = check_pk3.licensed_names(LICENSES)
        for name in list(expected_files()) + [f"STKEYS{i}.png" for i in range(3)]:
            self.assertIn(Path(name).stem, licensed, name)


if __name__ == "__main__":
    unittest.main()
