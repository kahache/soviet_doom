"""The LANGUAGE lump: D7 made enforceable.

D7 says in-game copy ships in English and Russian. A half-translated game is
worse than an English one, because the gaps look like engine bugs -- so this
suite fails the build when an `SD_*` id exists in one language and not the
other, and when a lump or a ZScript file asks for an id nobody defined.

Nothing here launches GZDoom: it is a static read of `src/`, so it runs in
the same second as the rest of the suite. The in-engine proof that the
strings actually render is `tools/smoke.py` plus the screenshots in
`docs/qa/`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"
LANGUAGE_LUMP = SRC / "lumps" / "LANGUAGE"

# The prefix the mod owns (MOD-SPEC 1). Ids without it belong to the engine
# or to Freedoom and are deliberately out of scope: AMMO_CLIP and friends
# override engine ids and are checked by test_arsenal.py.
MOD_PREFIX = "SD_"

# Every language section the mod promises to ship, by its GZDoom code. The
# tuple is the contract: adding a language means adding it here, and the
# suite then demands a full translation instead of a partial one.
REQUIRED_SECTIONS = ("default", "ru")

# Ids defined for the engine's benefit but never shown to a player, so they
# are allowed to hold the same text in several languages without that being
# a sign of a forgotten translation.
NON_PROSE_IDS = frozenset({
    "SD_LANG_CODE",   # the probe zscript/sd/language.zs reads; see LANGUAGE
})

# Where an "$SD_..." reference can appear. MAPINFO/MENUDEF quote it, ZScript
# quotes it in a property, and both forms are "$" + id.
REFERENCE_RE = re.compile(r'"\$(' + MOD_PREFIX + r'[A-Za-z0-9_]+)"')
SECTION_RE = re.compile(r"^\[([^\]]+)\]$")
ASSIGNMENT_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$")


def strip_comment(line: str) -> str:
    """Drop a `//` comment, honouring quotes so a // inside a string stays."""
    out = []
    in_string = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"':
            in_string = not in_string
        elif not in_string and char == "/" and line[index + 1:index + 2] == "/":
            break
        out.append(char)
        index += 1
    return "".join(out)


def parse_language(text: str) -> dict[str, dict[str, str]]:
    """LANGUAGE lump -> {language code: {id: raw value}}.

    A header may list several codes (`[enu default]`); each one gets the
    same entries, which is how GZDoom reads it too.
    """
    sections: dict[str, dict[str, str]] = {}
    current: list[str] = []
    for raw in text.splitlines():
        line = strip_comment(raw).strip()
        if not line:
            continue
        header = SECTION_RE.match(line)
        if header:
            current = header.group(1).split()
            for code in current:
                sections.setdefault(code, {})
            continue
        assignment = ASSIGNMENT_RE.match(line)
        if assignment and current:
            key, value = assignment.group(1), assignment.group(2).rstrip(";").strip()
            for code in current:
                sections[code][key] = value
    return sections


def iter_referencing_files() -> list[Path]:
    """Every source file that may reference a string id."""
    files = [p for p in sorted((SRC / "lumps").iterdir())
             if p.is_file() and p.name != "LANGUAGE"]
    files += sorted((SRC / "zscript").rglob("*.zs"))
    return files


class LanguageLumpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = LANGUAGE_LUMP.read_text(encoding="utf-8")
        cls.sections = parse_language(cls.text)

    def test_required_sections_exist(self):
        for code in REQUIRED_SECTIONS:
            self.assertIn(code, self.sections,
                          f"LANGUAGE has no [{code}] section; D7 requires it")

    def test_every_mod_id_is_translated(self):
        """THE D7 TEST: an SD_* id in one language must exist in all of them."""
        per_section = {
            code: {k for k in self.sections.get(code, {}) if k.startswith(MOD_PREFIX)}
            for code in REQUIRED_SECTIONS
        }
        union = set().union(*per_section.values())
        missing = {
            code: sorted(union - ids)
            for code, ids in per_section.items()
            if union - ids
        }
        self.assertEqual(
            missing, {},
            "untranslated string ids (id defined in one language, absent in "
            "another). Write the missing lines, or ask translator-ru:\n"
            + "\n".join(f"  [{code}] is missing: {', '.join(ids)}"
                        for code, ids in sorted(missing.items())),
        )

    def test_translations_are_not_copies_of_the_english(self):
        """A pasted English line is a gap wearing a translation's clothes."""
        english = self.sections["default"]
        copied = []
        for key, value in sorted(self.sections["ru"].items()):
            if not key.startswith(MOD_PREFIX) or key in NON_PROSE_IDS:
                continue
            if value == english.get(key) and re.search(r"[A-Za-z]{3}", value):
                copied.append(f"{key} = {value}")
        self.assertEqual(copied, [],
                         "[ru] repeats the English text verbatim:\n  " + "\n  ".join(copied))

    def test_russian_section_is_actually_cyrillic(self):
        """Catches a section header typo that would silently ship English."""
        russian = "".join(v for k, v in self.sections["ru"].items()
                          if k.startswith(MOD_PREFIX) and k not in NON_PROSE_IDS)
        self.assertRegex(russian, r"[Ѐ-ӿ]",
                         "[ru] contains no Cyrillic at all")

    def test_the_language_probe_is_gone(self):
        """SD_LANG_CODE existed only so ZScript could rewrite the `language`
        CVar, and that write aborts the VM outside menu input handling
        (ADR 004, D-004-4). The id went with the class it served; if it
        comes back, so has the crash."""
        for code in REQUIRED_SECTIONS:
            self.assertNotIn(
                "SD_LANG_CODE", self.sections[code],
                f"[{code}] still defines the SD_LANG_CODE probe. Nothing reads "
                "it; read ADR 004 before reintroducing the mechanism it served.")

    def test_english_section_is_ascii(self):
        """Until debt T9 lands, Freedoom's font cannot draw anything else.

        Non-ASCII in the DEFAULT section prints as a blank in game -- the
        rule MOD-SPEC 6.4 already states for the ammunition names. The
        Russian section is exempt: it is correct and simply waits for the
        glyphs.
        """
        offenders = [
            f"{key} = {value}"
            for key, value in sorted(self.sections["default"].items())
            if any(ord(ch) > 127 for ch in value)
        ]
        self.assertEqual(
            offenders, [],
            "non-ASCII in the [enu default] section; Freedoom's SmallFont and "
            "BigFont have no glyph for it and it renders blank (debt T9):\n  "
            + "\n  ".join(offenders),
        )

    def test_every_referenced_id_is_defined(self):
        """A '$SD_...' nobody defined prints the raw id on screen."""
        defined = set(self.sections["default"])
        dangling: list[str] = []
        for path in iter_referencing_files():
            content = path.read_text(encoding="utf-8")
            for match in REFERENCE_RE.finditer(content):
                if match.group(1) not in defined:
                    dangling.append(f"{path.relative_to(PROJECT_ROOT)}: ${match.group(1)}")
        self.assertEqual(dangling, [],
                         "string ids referenced but never defined in LANGUAGE:\n  "
                         + "\n  ".join(dangling))

    def test_no_duplicate_ids_within_a_section(self):
        """A repeated id silently wins over the first; the loser looks lost."""
        current: list[str] = []
        seen: dict[tuple[str, str], int] = {}
        duplicates: list[str] = []
        for number, raw in enumerate(self.text.splitlines(), start=1):
            line = strip_comment(raw).strip()
            if not line:
                continue
            header = SECTION_RE.match(line)
            if header:
                current = header.group(1).split()
                continue
            assignment = ASSIGNMENT_RE.match(line)
            if assignment and current:
                for code in current:
                    key = (code, assignment.group(1))
                    if key in seen:
                        duplicates.append(
                            f"[{code}] {assignment.group(1)} on lines {seen[key]} and {number}")
                    else:
                        seen[key] = number
        self.assertEqual(duplicates, [], "duplicate ids:\n  " + "\n  ".join(duplicates))


class DifficultyLadderTest(unittest.TestCase):
    """The five skills: MAPINFO owns the mechanics, LANGUAGE owns the names."""

    SKILL_IDS = tuple(f"SD_SKILL_{n}" for n in range(1, 6))

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapinfo = (SRC / "lumps" / "MAPINFO").read_text(encoding="utf-8")
        cls.sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))
        # Comments are stripped first: a block that *mentions* AmmoFactor in
        # a comment must not read as a block that *sets* it.
        code_only = "\n".join(strip_comment(line) for line in cls.mapinfo.splitlines())
        cls.skill_blocks = re.findall(
            r"^skill\s+(\w+)\s*\{(.*?)^\}", code_only, re.MULTILINE | re.DOTALL)

    def test_five_skills_and_a_clearskills(self):
        self.assertRegex(
            self.mapinfo, r"(?m)^clearskills\b",
            "without `clearskills` the engine's five skills keep their PicName "
            "and the menu draws Freedoom's graphics instead of our names")
        self.assertEqual(len(self.skill_blocks), 5,
                         f"expected 5 skill blocks, found {len(self.skill_blocks)}")

    def test_each_skill_is_named_from_language(self):
        names = [re.search(r'Name\s*=\s*"\$(\w+)"', body) for _n, body in self.skill_blocks]
        self.assertTrue(all(names), "a skill block has no Name = \"$SD_SKILL_n\"")
        self.assertEqual([m.group(1) for m in names], list(self.SKILL_IDS),
                         "skill order must match SD_SKILL_1..5")

    def test_no_skill_carries_a_picname(self):
        """A PicName would override Name and the ladder would be invisible."""
        for name, body in self.skill_blocks:
            self.assertNotIn("PicName", body,
                             f"skill {name} has a PicName; the localized Name would be ignored")

    def test_doom_mechanics_are_preserved(self):
        """Renaming a rung must not rebalance it (CEO, 2026-10-13).

        The expected values are GZDoom 4.14.2's own mapinfo/doomcommon.txt.
        """
        expected = {
            1: ("SpawnFilter = Baby", "AmmoFactor = 2", "DamageFactor = 0.5",
                "AutoUseHealth", "EasyBossBrain"),
            2: ("SpawnFilter = Easy", "EasyBossBrain"),
            3: ("SpawnFilter = Normal", "DefaultSkill"),
            4: ("SpawnFilter = Hard",),
            5: ("SpawnFilter = Nightmare", "AmmoFactor = 2", "FastMonsters",
                "InstantReaction", "DisableCheats", "RespawnTime = 12"),
        }
        for index, (name, body) in enumerate(self.skill_blocks, start=1):
            for prop in expected[index]:
                self.assertIn(prop, body,
                              f"skill {index} ({name}) lost Doom's `{prop}`")

    def test_skill_four_gets_no_discounts(self):
        """'No pasaran' is the honest-Doom rung: no factor of any kind."""
        _name, body = self.skill_blocks[3]
        for forbidden in ("AmmoFactor", "DamageFactor", "AutoUseHealth", "EasyBossBrain"):
            self.assertNotIn(forbidden, body,
                             f"skill 4 must not soften the game, found {forbidden}")

    def test_skill_five_really_is_nightmare(self):
        """The fifth name is a joke about dying twice; it has to be earned."""
        _name, body = self.skill_blocks[4]
        respawn = re.search(r"RespawnTime\s*=\s*(\d+)", body)
        self.assertIsNotNone(respawn, "skill 5 does not respawn monsters")
        self.assertGreater(int(respawn.group(1)), 0)
        self.assertIn("FastMonsters", body, "skill 5 does not speed up projectiles")

    def test_skill_names_are_translated(self):
        for code in REQUIRED_SECTIONS:
            for skill_id in self.SKILL_IDS:
                self.assertIn(skill_id, self.sections[code],
                              f"[{code}] has no {skill_id}")


class LanguageMenuTest(unittest.TestCase):
    """MENUDEF: the switch exists, offers both languages, and owns no CVar."""

    @classmethod
    def setUpClass(cls) -> None:
        # Comments stripped: MENUDEF quotes engine source and the wrong
        # spellings it warns against, and none of that is the lump's code.
        raw = (SRC / "lumps" / "MENUDEF").read_text(encoding="utf-8")
        cls.menudef = "\n".join(strip_comment(line) for line in raw.splitlines())

    def test_the_option_drives_the_engine_language_cvar(self):
        self.assertRegex(
            self.menudef, r'Option\s+"\$SD_OPTMNU_LANGUAGE",\s*"language"',
            "the language row must drive GZDoom's own archived `language` CVar, "
            "so the choice persists without the mod writing a CVar of its own")

    def test_both_languages_are_offered_explicitly(self):
        # OptionString, not OptionValue: `language` is a string CVar, and
        # OptionValue parses its left column as a number. Swapping the
        # keyword makes GZDoom 4.14.2 abort during startup (exit 255, log
        # stops at "M_Init: Init menus.") -- reproduced 2026-10-13, the game
        # does not launch at all. The test accepts only the string form.
        values = re.search(r'OptionString\s+"SD_LanguageValues"\s*\{(.*?)\}',
                           self.menudef, re.DOTALL)
        self.assertIsNotNone(values, "no SD_LanguageValues list")
        offered = re.findall(r'"([^"]+)",\s*"\$', values.group(1))
        # "auto" is first because it is the value of every untouched config.
        # A row whose CVar holds a value absent from its list draws
        # "Unknown", and the alternative -- ZScript rewriting the CVar --
        # aborts the VM outside menu input handling. ADR 004, D-004-4.
        self.assertEqual(offered, ["auto", "default", "ru"],
                         "the list must name every value `language` can hold "
                         "here: auto, English and Russian")

    def test_the_menu_is_reachable_from_both_options_screens(self):
        """GZDoom has two options screens and opens the SHORT one by default.

        `m_simpleoptions` is archived and defaults to true, so activating
        "Options" lands on "OptionsMenuSimple" (gzdoom 4.14.2,
        src/menu/doommenu.cpp:271). Attaching to "OptionsMenu" alone left
        the switch unreachable on a fresh install -- bug E2, found in the
        engine. Both names are required.
        """
        for screen in ("OptionsMenu", "OptionsMenuSimple"):
            self.assertRegex(
                self.menudef, r'AddOptionMenu\s+"' + screen + r'"',
                f"the mod's menu is not attached to GZDoom's {screen}; "
                "a player on the default settings cannot reach it")
        self.assertEqual(
            len(re.findall(r'Submenu\s+"\$SD_OPTMNU_TITLE",\s*"SD_OptionsMenu"',
                           self.menudef)), 2,
            "each AddOptionMenu block needs its own Submenu line")

    def test_the_mod_owns_no_menu_zscript(self):
        """No ZScript may write the `language` CVar. ADR 004, D-004-4.

        GZDoom raises DMenu::InMenu only around OnUIEvent, OnInputEvent and
        MenuEvent (src/common/menu/menu.cpp). A CVar write from Init, Ticker
        or Drawer aborts the VM with "Attempt to change CVAR 'language'
        outside of menu code" and drops the player to the console -- both
        were reproduced in-engine on 2026-10-13. The menu is pure MENUDEF so
        that there is nothing left that can abort.
        """
        self.assertFalse(
            (SRC / "zscript" / "sd" / "language.zs").exists(),
            "zscript/sd/language.zs is back. If a menu really needs code, it "
            "may only touch a CVar from MenuEvent; read ADR 004 first.")
        offenders = [
            f"{path.relative_to(PROJECT_ROOT)}: {line.strip()}"
            for path in sorted((SRC / "zscript").rglob("*.zs"))
            for line in path.read_text(encoding="utf-8").splitlines()
            if "CVar." in line and ("SetString" in line or "SetInt" in line
                                    or "SetFloat" in line or "SetBool" in line)
        ]
        self.assertEqual(offenders, [],
                         "ZScript writes a CVar; see ADR 004 before allowing it:\n  "
                         + "\n  ".join(offenders))


class MainMenuLogoTest(unittest.TestCase):
    """The menu's M_DOOM must land on the lockup painted into TITLEPIC.

    Bug E1: with no MainMenu of our own the engine used its own
    `StaticPatch 94, 2, "M_DOOM"`, which sits 34 px right and 2 px below the
    name block of TITLEPIC, so a "CO" of the latter showed past its left
    edge. `art-director` records the correct origin in
    work/art/shell/manifest.json; measured 2026-10-13, overlaying M_DOOM on
    TITLEPIC at (60,0) gives a mean per-channel difference of 6 against 22+
    at every neighbouring offset.
    """

    # From work/art/shell/manifest.json (menudef_x / menudef_y). Changing
    # this means art moved the lockup: change it there first.
    LOGO_X, LOGO_Y = 60, 0

    @classmethod
    def setUpClass(cls) -> None:
        # Comments only: MENUDEF quotes the engine's own `StaticPatch 94, 2`
        # to explain why ours differs, and a test that reads comments would
        # count that as a second logo.
        raw = (SRC / "lumps" / "MENUDEF").read_text(encoding="utf-8")
        cls.menudef = "\n".join(strip_comment(line) for line in raw.splitlines())

    def test_the_main_menu_places_the_logo_itself(self):
        patches = re.findall(r'StaticPatch\s+(-?\d+)\s*,\s*(-?\d+)\s*,\s*"M_DOOM"',
                             self.menudef)
        self.assertEqual(
            len(patches), 1,
            "expected exactly one M_DOOM StaticPatch. Zero means the engine's "
            "own 94,2 wins again (bug E1); two means a second logo is being "
            "drawn next to the first.")
        self.assertEqual(
            (int(patches[0][0]), int(patches[0][1])), (self.LOGO_X, self.LOGO_Y),
            "the menu logo no longer sits on the TITLEPIC lockup")

    def test_the_main_menu_is_redeclared_whole(self):
        """A redeclared LISTMENU REPLACES the engine's: a missing item is a
        deleted item. These five are the Doom main menu."""
        body = re.search(r'LISTMENU\s+"MainMenu"\s*\{(.*?)\n\}',
                         self.menudef, re.DOTALL)
        self.assertIsNotNone(body, "no MainMenu block")
        for patch in ("M_NGAME", "M_OPTION", "M_LOADG", "M_SAVEG", "M_QUITG"):
            self.assertIn(patch, body.group(1),
                          f"MainMenu lost {patch}; redeclaring the list menu "
                          "drops every item not restated")

    def test_the_skill_names_are_not_drawn_in_bigfont(self):
        """Bug E4: rung 5 is 38 characters and BigFont fits about 26, so
        "Hero of the Soviet Union, posthumously" ran off the screen. The
        names are the CEO's; the font is ours."""
        body = re.search(r'LISTMENU\s+"SkillMenu"\s*\{(.*?)\n\}',
                         self.menudef, re.DOTALL)
        self.assertIsNotNone(
            body, "no SkillMenu block: the engine's default font clips rung 5")
        self.assertRegex(body.group(1), r'Font\s+"SmallFont"',
                         "the skill menu must set a font that fits the names")

    def test_the_mod_declares_no_cvar_of_its_own(self):
        """Scope limit from the CEO: the player's config gains one key, not two."""
        self.assertFalse(
            (SRC / "lumps" / "CVARINFO").exists(),
            "a CVARINFO appeared: every CVar in it is archived into the player's "
            "gzdoom.ini. The language switch deliberately reuses the engine's "
            "`language` CVar; if a gameplay option now needs one, say so in an "
            "ADR and update this test.")


if __name__ == "__main__":
    unittest.main()
