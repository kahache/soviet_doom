"""No Freedoom text or help page in front of the player (M4 shell).

The audit `docs/qa/2026-10-14_2357_M2-freedoom-audit.md` (H4, H5) found
Freedoom's English in the Russian game: its DEHACKED lump rewrites the
engine's own string ids (pickup lines, the fifteen quit messages, ...), and a
DEHACKED string beats every LANGUAGE section (ADR 003; in gzdoom g4.14.2
src/common/engine/stringtable.cpp, CheckString walks the override table
first and returns the first hit). The only way out is to stop asking for
those ids: our own actor classes carry `$SD_*` pickup lines, and GameInfo
points the quit prompt, the help key and the title loop at things of ours.

This suite pins that, id by id:

* ROUTED: every DEHACKED id a player of our maps can meet, with the place in
  our source that now shows an `SD_` string instead. Each test below checks
  one family.
* NOT_REACHED: ids whose actor, lock or screen our campaign never uses; the
  placement test proves the actors are not placed.
* KNOWN_GAPS: ids the engine prints itself, from C++, which no LANGUAGE or
  actor of ours can reach. Listed so they stay visible (report to the PM).

When the IWAD is present, every id in Freedoom's DEHACKED [STRINGS] must be
in one of the three, so a new Freedoom release cannot slip a line in.
No engine is started (D26).
"""

from __future__ import annotations

import importlib.util
import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_language import parse_language, strip_comment  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
LUMPS = SRC / "lumps"
ZSCRIPT = SRC / "zscript"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
# D104 (P4): episode 2, MAP04-MAP06, joins the campaign's maps.
MAPS = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06", "RANGE")
REQUIRED_SECTIONS = ("default", "ru", "ca")   # Catalan since P6 (D97)

# --- ROUTED: reached in our maps, now ours -------------------------------------
# DEHACKED pickup id -> the Doom class whose replacement must carry an SD_ line.
PICKUP_ROUTES = {
    "GOTARMOR": "GreenArmor", "GOTMEGA": "BlueArmor",
    "GOTHTHBONUS": "HealthBonus", "GOTARMBONUS": "ArmorBonus",
    "GOTSTIM": "Stimpack", "GOTMEDIKIT": "Medikit", "GOTMAP": "Allmap",
    "GOTBLUECARD": "BlueCard", "GOTYELWCARD": "YellowCard", "GOTREDCARD": "RedCard",
    "GOTCLIP": "Clip", "GOTCLIPBOX": "ClipBox",
    "GOTSHELLS": "Shell", "GOTSHELLBOX": "ShellBox",
    "GOTROCKET": "RocketAmmo", "GOTROCKBOX": "RocketBox",
    "GOTCELL": "Cell", "GOTCELLBOX": "CellPack", "GOTBACKPACK": "Backpack",
    "GOTSHOTGUN": "Shotgun", "GOTCHAINGUN": "Chaingun",
    "GOTLAUNCHER": "RocketLauncher", "GOTPLASMA": "PlasmaRifle",
    "GOTBFG9000": "BFG9000",
}
# The weapon names (shown with `displaynametags`): the replacement's Tag.
TAG_ROUTES = {
    "TAG_FIST": "Fist", "TAG_SHOTGUN": "Shotgun", "TAG_CHAINGUN": "Chaingun",
    "TAG_ROCKETLAUNCHER": "RocketLauncher", "TAG_PLASMARIFLE": "PlasmaRifle",
    "TAG_BFG9000": "BFG9000",
}
# Monster deaths: the replacement's Obituary (HitObituary falls back to it).
OBITUARY_ROUTES = {
    "OB_ZOMBIE": "ZombieMan", "OB_SHOTGUY": "ShotgunGuy",
    "OB_IMP": "DoomImp", "OB_IMPHIT": "DoomImp", "OB_DEMONHIT": "Demon",
    "OB_CACO": "Cacodemon", "OB_CACOHIT": "Cacodemon",
    "OB_KNIGHT": "HellKnight", "OB_KNIGHTHIT": "HellKnight",
    "OB_BARON": "BaronOfHell", "OB_BARONHIT": "BaronOfHell",
    "OB_CYBORG": "Cyberdemon",
}
QUIT_IDS = frozenset({"DOSY", "QUITMSG", *(f"QUITMSG{n}" for n in range(1, 15))})
OTHER_ROUTED = {
    "GOTMEDINEED": "SD_Medikit's Health.LowMessage",
    "NIGHTMARE": "skill 5's MustConfirm",
    "SKILL_BABY": "clearskills", "SKILL_EASY": "clearskills",
    "SKILL_NORMAL": "clearskills", "SKILL_HARD": "clearskills",
    "SKILL_NIGHTMARE": "clearskills",
    "TXT_D1E1": "clearepisodes", "TXT_D1E2": "clearepisodes",
    "TXT_D1E3": "clearepisodes", "TXT_D1E4": "clearepisodes",
    "TXT_D2E1": "clearepisodes",
}

# --- NOT_REACHED: the campaign never shows these ---------------------------------
# Pickups and monsters never placed (proved by NotPlacedTest).
NOT_PLACED_IDS = {
    "GOTSUPER": 2013, "GOTMSPHERE": 83, "GOTINVUL": 2022, "GOTBERSERK": 2023,
    "GOTINVIS": 2024, "GOTSUIT": 2025, "GOTVISOR": 2045,
    "GOTBLUESKUL": 40, "GOTYELWSKUL": 39, "GOTREDSKULL": 38,
    "GOTCHAINSAW": 2005, "GOTSHOTGUN2": 82,
    "TAG_CHAINSAW": 2005, "TAG_SUPERSHOTGUN": 82,
    "OB_SPECTREHIT": 58, "OB_CHAINGUY": 65, "OB_UNDEAD": 66, "OB_UNDEADHIT": 66,
    "OB_FATSO": 67, "OB_BABY": 68, "OB_VILE": 64, "OB_SKULL": 3006,
    "OB_SPIDER": 7, "OB_WOLFSS": 84,
}
# Doom's Pain Elemental spawns lost souls; it must not be placed either.
EXTRA_NOT_PLACED = {71: "PainElemental (spawns LostSoul, OB_SKULL)"}
# Whole families, by prefix, with the reason.
NOT_REACHED_PREFIXES = {
    "HUSTR_": "map names: every map block of ours has `lookup \"SD_...\"`",
    "PHUSTR_": "Plutonia map names",
    "THUSTR_": "TNT map names",
    "CC_": "the cast call; our ending is `endtitle`, no cast",
    "BGFLAT": "text-screen flats of Doom's clusters; ours set their own",
    "OB_STEALTH": "stealth monsters, never placed",
    "OB_MP": "multiplayer obituaries; the campaign is single-player",
}
NOT_REACHED = {
    "OB_RAILGUN": "multiplayer",
    "HUSTR_PLRGREEN": "multiplayer chat", "HUSTR_PLRINDIGO": "multiplayer chat",
    "HUSTR_PLRBROWN": "multiplayer chat", "HUSTR_PLRRED": "multiplayer chat",
    **{f"E{n}TEXT": "Doom 1 episode texts" for n in range(1, 5)},
    **{f"C{n}TEXT": "Doom 2 cluster texts; our maps use clusters 1-4 of ours"
       for n in range(1, 7)},
    # Locks (gzdoom.pk3 lockdefs.txt). Our coloured doors work by tag, so the
    # player reads the remote PD_*CO lines, which DEHACKED does not touch and
    # LANGUAGE overrides in EN and RU; PD_*C would need a tag-0 door (none).
    "PD_BLUEC": "tag-0 lock 2 door; none", "PD_REDC": "tag-0 lock 1 door; none",
    "PD_YELLOWC": "tag-0 lock 3 door; none",
    "PD_BLUEO": "object locks; none", "PD_REDO": "object locks; none",
    "PD_YELLOWO": "object locks; none",
    "PD_BLUEK": "locks 129-131 (card or skull); none",
    "PD_REDK": "locks 129-131; none", "PD_YELLOWK": "locks 129-131; none",
    "PD_BLUES": "skull locks; none", "PD_REDS": "skull locks; none",
    "PD_YELLOWS": "skull locks; none",
    "PD_ANY": "lock 100; none", "PD_ALL3": "lock 101; none", "PD_ALL6": "lock 229; none",
}

# --- KNOWN_GAPS: printed by the engine's C++ code, beyond LANGUAGE ------------------
# Reaching these needs a DEHACKED of our own (each value "$$SD_..." so
# CheckString's "$$" indirection picks our LANGUAGE line per language). That
# is a new root lump and an amendment of ADR 003; proposed to the PM, not done.
KNOWN_GAPS = {
    "AMSTR_FOLLOWON": "automap follow toggle", "AMSTR_FOLLOWOFF": "automap follow toggle",
    "AMSTR_GRIDON": "automap grid toggle", "AMSTR_GRIDOFF": "automap grid toggle",
    "AMSTR_MARKEDSPOT": "automap mark", "AMSTR_MARKSCLEARED": "automap marks cleared",
    "STSTR_MUS": "cheat", "STSTR_NOMUS": "cheat", "STSTR_DQDON": "cheat",
    "STSTR_DQDOFF": "cheat", "STSTR_KFAADDED": "cheat", "STSTR_FAADDED": "cheat",
    "STSTR_NCON": "cheat", "STSTR_NCOFF": "cheat", "STSTR_CHOPPERS": "cheat",
    "STSTR_BEHOLD": "cheat",
    "STARTUP5": "the startup console banner, before the game",
}

QUIT_LINE_MAX = 40  # characters per line of a quit message (the message box width)


def read_zscript() -> str:
    """Every .zs file under src/zscript, comments stripped, concatenated."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(ZSCRIPT.rglob("*.zs")))
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def class_bodies(code: str) -> dict[str, tuple[str, str, str | None]]:
    """class name -> (parent, body, replaced class) for each ZScript class."""
    out = {}
    pattern = re.compile(r"\bclass\s+(\w+)\s*(?::\s*(\w+))?\s*(?:replaces\s+(\w+))?[^{;]*\{")
    for m in pattern.finditer(code):
        depth, i = 1, m.end()
        while depth and i < len(code):
            depth += {"{": 1, "}": -1}.get(code[i], 0)
            i += 1
        out[m.group(1)] = (m.group(2) or "", code[m.end():i - 1], m.group(3))
    return out


def gameinfo_block(mapinfo: str) -> str:
    code = "\n".join(strip_comment(line) for line in mapinfo.splitlines())
    m = re.search(r"^GameInfo\s*\{(.*?)^\}", code, re.S | re.M | re.I)
    assert m, "MAPINFO has no GameInfo block"
    return m.group(1)


def gameinfo_list(block: str, key: str) -> list[str]:
    m = re.search(rf"^\s*{key}\s*=\s*((?:\"[^\"]*\"\s*,\s*)*\"[^\"]*\")", block, re.M | re.I)
    return re.findall(r'"([^"]*)"', m.group(1)) if m else []


def dehacked_string_ids(wad: Path) -> set[str]:
    """The ids of the [STRINGS] section of the IWAD's DEHACKED lump."""
    data = wad.read_bytes()
    count, offset = struct.unpack("<4xii", data[:12])
    for i in range(count):
        pos, size, name = struct.unpack("<ii8s", data[offset + 16 * i:offset + 16 * i + 16])
        if name.rstrip(b"\0") == b"DEHACKED":
            text = data[pos:pos + size].decode("latin-1")
            strings = text.split("[STRINGS]", 1)[1]
            return set(re.findall(r"^([A-Z][A-Z0-9_]*)\s*=", strings, re.M))
    raise AssertionError("no DEHACKED lump in the IWAD")


def is_classified(ident: str) -> bool:
    routed = (set(PICKUP_ROUTES) | set(TAG_ROUTES) | set(OBITUARY_ROUTES)
              | QUIT_IDS | set(OTHER_ROUTED))
    return (ident in routed or ident in NOT_PLACED_IDS or ident in NOT_REACHED
            or ident in KNOWN_GAPS
            or any(ident.startswith(p) for p in NOT_REACHED_PREFIXES))


class _Sources(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.language = parse_language((LUMPS / "LANGUAGE").read_text(encoding="utf-8"))
        cls.mapinfo = (LUMPS / "MAPINFO").read_text(encoding="utf-8")
        cls.gameinfo = gameinfo_block(cls.mapinfo)
        cls.classes = class_bodies(read_zscript())

    def assert_translated(self, ident: str, where: str) -> None:
        for section in REQUIRED_SECTIONS:
            self.assertIn(ident, self.language[section], f"{where}: {ident} missing in [{section}]")

    def replacement_of(self, doom_class: str) -> tuple[str, str]:
        hits = [(name, body) for name, (_, body, repl) in self.classes.items()
                if repl and repl.lower() == doom_class.lower()]
        self.assertEqual(len(hits), 1, f"exactly one class must replace {doom_class}")
        return hits[0]

    def sd_property(self, doom_class: str, prop: str) -> str:
        name, body = self.replacement_of(doom_class)
        m = re.search(rf"{re.escape(prop)}\s+\"\$(\w+)\"", body)
        parent = self.classes[name][0]
        while m is None and parent in self.classes:  # inherited from a class of ours
            m = re.search(rf"{re.escape(prop)}\s+\"\$(\w+)\"", self.classes[parent][1])
            parent = self.classes[parent][0]
        self.assertIsNotNone(m, f"{name} (replaces {doom_class}) sets no {prop} \"$...\"")
        ident = m.group(1)
        self.assertTrue(ident.startswith("SD_"), f"{name}.{prop} is {ident}, a Freedoom-owned id")
        return ident


class RoutedActorTextTest(_Sources):
    def test_every_pickup_line_is_ours(self):
        for deh_id, doom_class in PICKUP_ROUTES.items():
            with self.subTest(deh_id):
                self.assert_translated(self.sd_property(doom_class, "Inventory.PickupMessage"),
                                       deh_id)

    def test_the_low_health_medikit_line_is_ours(self):
        _, body = self.replacement_of("Medikit")
        m = re.search(r"Health\.LowMessage\s+[^,]+,\s*\"\$(\w+)\"", body)
        self.assertIsNotNone(m, "SD_Medikit must set Health.LowMessage (GOTMEDINEED)")
        self.assertTrue(m.group(1).startswith("SD_"))
        self.assert_translated(m.group(1), "GOTMEDINEED")

    def test_every_weapon_tag_is_ours(self):
        for deh_id, doom_class in TAG_ROUTES.items():
            with self.subTest(deh_id):
                self.assert_translated(self.sd_property(doom_class, "Tag"), deh_id)

    def test_every_monster_obituary_is_ours(self):
        for deh_id, doom_class in OBITUARY_ROUTES.items():
            with self.subTest(deh_id):
                self.assert_translated(self.sd_property(doom_class, "Obituary"), deh_id)


class QuitMessagesTest(_Sources):
    def test_the_quit_list_is_ours_and_never_appends_dosy(self):
        entries = gameinfo_list(self.gameinfo, "QuitMessages")
        self.assertEqual(len(entries), 15, "fifteen quit lines, as many as Freedoom's")
        for entry in entries:
            with self.subTest(entry):
                self.assertTrue(entry.startswith("$*SD_QUIT_"),
                                f"{entry}: '$*' + an SD_ id, or DOSY (Freedoom's English) is appended")
                self.assert_translated(entry[2:], "quitmessages")
        self.assertEqual(len(set(entries)), len(entries), "a quit line is listed twice")
        self.assertNotRegex(self.gameinfo, r"(?i)addquitmessages",
                            "addquitmessages APPENDS to Freedoom's list")

    def test_each_quit_line_is_short_and_carries_its_own_prompt(self):
        ids = sorted(i for i in self.language["default"] if i.startswith("SD_QUIT_"))
        self.assertEqual(len(ids), 15)
        prompts = {"default": "(Press Y to quit.)", "ru": "(Нажмите Y, чтобы выйти.)",
                   "ca": "(Prem Y per sortir.)"}
        for section, prompt in prompts.items():
            for ident in ids:
                with self.subTest(f"{section}:{ident}"):
                    value = self.language[section][ident].strip().strip('"')
                    lines = value.split("\\n")
                    self.assertEqual(lines[-1], prompt, "the prompt DOSY used to give")
                    for line in lines:
                        self.assertLessEqual(len(line), QUIT_LINE_MAX, line)


class HelpAndTitleLoopTest(_Sources):
    def test_no_freedoom_page_is_named(self):
        for key in ("InfoPage", "CreditPage", "FinalePage"):
            with self.subTest(key):
                pages = gameinfo_list(self.gameinfo, key)
                self.assertEqual(pages, ["TITLEPIC"], f"{key} must show our title only")
        self.assertNotRegex(self.gameinfo, r"(?i)\badd(info|credit)page\b",
                            "the add... keys APPEND to Freedoom's HELP/CREDIT")

    def test_f1_opens_our_class_and_it_opens_the_credits(self):
        names = gameinfo_list(self.gameinfo, "HelpMenuClass")
        self.assertEqual(names, ["SD_HelpMenu"])
        self.assertIn("SD_HelpMenu", self.classes,
                      "an undefined HelpMenuClass is a fatal startup error")
        parent, body, _ = self.classes["SD_HelpMenu"]
        self.assertEqual(parent, "GenericMenu", "M_SetMenu builds only GenericMenu subclasses")
        self.assertIn("Menu.SetMenu('SD_CreditsMenu')", body)
        self.assertIn("Close();", body)
        menudef = (LUMPS / "MENUDEF").read_text(encoding="utf-8")
        self.assertRegex(menudef, r'(?m)^OptionMenu\s+"SD_CreditsMenu"')
        zscript_txt = (LUMPS / "zscript.txt").read_text(encoding="utf-8")
        self.assertIn('#include "zscript/sd/help_menu.zs"', zscript_txt)

    def test_the_help_menu_writes_no_cvar(self):
        _, body, _ = self.classes["SD_HelpMenu"]
        self.assertNotIn("CVar", body, "ADR 004: menu code must not touch CVars")


class SkillAndEpisodeTextTest(_Sources):
    def test_doom_skills_and_episodes_are_cleared(self):
        code = "\n".join(strip_comment(line) for line in self.mapinfo.splitlines())
        self.assertRegex(code, r"(?m)^clearskills\b")
        self.assertRegex(code, r"(?m)^clearepisodes\b")
        confirm = re.search(r'MustConfirm\s*=\s*"\$(\w+)"', code)
        self.assertIsNotNone(confirm, "NIGHTMARE is Freedoom's; skill 5 needs its own line")
        self.assert_translated(confirm.group(1), "NIGHTMARE")

    def test_every_map_name_is_ours(self):
        code = "\n".join(strip_comment(line) for line in self.mapinfo.splitlines())
        maps = re.findall(r"(?m)^map\s+(\w+)\s+(.*)$", code)
        self.assertEqual({m for m, _ in maps}, set(MAPS))
        for name, rest in maps:
            self.assertRegex(rest, r'lookup\s+"SD_\w+"', f"{name}: HUSTR_* would show")


class NotPlacedTest(unittest.TestCase):
    """The NOT_PLACED ids are honest only while no map places their actors."""

    def test_no_map_places_an_unreplaced_actor(self):
        sys.path.insert(0, str(TOOLS))
        forbidden = {ednum: ident for ident, ednum in NOT_PLACED_IDS.items()}
        forbidden.update(EXTRA_NOT_PLACED)
        for name in MAPS:
            spec = importlib.util.spec_from_file_location(f"sdmap_ft_{name}",
                                                          SRC / "maps" / name / "map.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            placed = {t.type for t in module.build_textmap().things}
            with self.subTest(name):
                self.assertEqual(sorted(placed & set(forbidden)), [],
                                 f"{name} places actors whose Freedoom text is not routed: "
                                 + ", ".join(str(forbidden[e]) for e in placed & set(forbidden)))


class ClassificationTest(unittest.TestCase):
    def test_the_lists_do_not_overlap(self):
        groups = {
            "routed": set(PICKUP_ROUTES) | set(TAG_ROUTES) | set(OBITUARY_ROUTES)
                      | QUIT_IDS | set(OTHER_ROUTED),
            "not placed": set(NOT_PLACED_IDS), "not reached": set(NOT_REACHED),
            "gaps": set(KNOWN_GAPS),
        }
        names = list(groups)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                self.assertEqual(groups[a] & groups[b], set(), f"{a} / {b}")

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not present (CI has no IWAD)")
    def test_every_freedoom_dehacked_string_is_accounted_for(self):
        ids = dehacked_string_ids(IWAD)
        self.assertGreater(len(ids), 300, "the DEHACKED [STRINGS] parse looks wrong")
        unclassified = sorted(i for i in ids if not is_classified(i))
        self.assertEqual(unclassified, [],
                         "Freedoom DEHACKED ids this suite does not route, rule out or "
                         "list as a known gap")


if __name__ == "__main__":
    unittest.main()
