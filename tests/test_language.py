"""The LANGUAGE lump: D7 made enforceable.

D7 says in-game copy ships in English and Russian; D97 (P6) adds Catalan. A
half-translated game is worse than an English one, because the gaps look
like engine bugs -- so this suite fails the build when an `SD_*` id exists
in one language and not the others, and when a lump or a ZScript file asks
for an id nobody defined.

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
REQUIRED_SECTIONS = ("default", "ru", "ca")

# The translations: every required section but the English default.
TRANSLATIONS = tuple(code for code in REQUIRED_SECTIONS if code != "default")

# [ca] ids whose text is the English text on purpose: the game's title, the
# proper nouns and designations D97 keeps as in English (Tankograd, PPSh-41,
# RPG-7, Zelyonka, Panzermensch, Doughboy), and the pause sign's graphic name
# until a Catalan plaque exists. Anything else equal to the English is a gap.
CATALAN_SAME_AS_ENGLISH = frozenset({
    "SD_EP01_NAME", "SD_OPTMNU_TITLE", "SD_MAP03_NAME",
    "SD_TAG_PPSH", "SD_TAG_RPG7", "SD_GOT_HEALTHBONUS",
    "SD_TAG_DOUGHBOY", "SD_TAG_PANZER", "SD_PAUSE_SIGN",
    # Credit lines made only of names, URLs and licences ("local" is Catalan too).
    "SD_CRED_ENGINE_1", "SD_CRED_IWAD_1", "SD_CRED_AI_7",
})

# Letters Catalan needs that the mod's fonts (assets/fonts/, D24) do not draw
# yet. GZDoom draws a missing accented capital with its base letter
# (FFont::GetCharCode strips the accent; read in the engine source, NOT
# VERIFIED on screen, D26), so "MUNICIÓ" would print "MUNICIO". Listed so
# the debt is explicit: a glyph added to the fonts can leave this set, and
# any OTHER character [ca] uses without a glyph still fails.
# Emptied 2026-10-21: art-director drew À È É Í Ï Ò Ó Ú Ç in all three fonts
# (tools/art/gen_font.py, CATALAN_ACCENTS).
CATALAN_UNDRAWN_ACCENTS = frozenset()

# Placeholders a line carries for the engine to fill (%o victim, %k killer,
# %s a string, %d a number). A translation must keep exactly the English set.
PLACEHOLDER_RE = re.compile(r"%[okds]")

# Ids defined for the engine's benefit but never shown to a player, so they
# are allowed to hold the same text in several languages without that being
# a sign of a forgotten translation. Empty today: the last member was
# SD_LANG_CODE, which went with zscript/sd/language.zs (ADR 004, D-004-4);
# test_the_language_probe_is_gone keeps it out.
NON_PROSE_IDS: frozenset[str] = frozenset()

# The only non-ASCII characters the English section may hold until debt T17:
# the German letters, because the Reich speaks real German since D36 and the
# alphabet draws them since D37 (2026-10-13). Lowercase prints with the
# capital glyph; both sharp-s codepoints are installed.
GERMAN_LETTERS = frozenset("ÄÖÜäöüßẞ")

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
        allowed = {"ru": NON_PROSE_IDS, "ca": NON_PROSE_IDS | CATALAN_SAME_AS_ENGLISH}
        for code in TRANSLATIONS:
            copied = []
            for key, value in sorted(self.sections[code].items()):
                if not key.startswith(MOD_PREFIX) or key in allowed[code]:
                    continue
                if value == english.get(key) and re.search(r"[A-Za-z]{3}", value):
                    copied.append(f"{key} = {value}")
            self.assertEqual(copied, [],
                             f"[{code}] repeats the English text verbatim:\n  " + "\n  ".join(copied))

    def test_catalan_exceptions_really_are_the_english(self):
        """The allow-list may not hide a line that has since been translated."""
        english, catalan = self.sections["default"], self.sections["ca"]
        for key in sorted(CATALAN_SAME_AS_ENGLISH):
            self.assertEqual(catalan.get(key), english.get(key), key)

    def test_placeholders_survive_translation(self):
        """A lost %o prints an obituary without its victim; an extra %s
        prints garbage. Every translation keeps the English placeholders."""
        english = self.sections["default"]
        wrong = [
            f"[{code}] {key}: {sorted(PLACEHOLDER_RE.findall(value))} != "
            f"{sorted(PLACEHOLDER_RE.findall(english[key]))}"
            for code in TRANSLATIONS
            for key, value in sorted(self.sections[code].items())
            if key.startswith(MOD_PREFIX) and key in english
            and sorted(PLACEHOLDER_RE.findall(value)) != sorted(PLACEHOLDER_RE.findall(english[key]))
        ]
        self.assertEqual(wrong, [], "placeholders differ from the English:\n  " + "\n  ".join(wrong))

    def test_russian_section_is_actually_cyrillic(self):
        """Catches a section header typo that would silently ship English."""
        russian = "".join(v for k, v in self.sections["ru"].items()
                          if k.startswith(MOD_PREFIX) and k not in NON_PROSE_IDS)
        self.assertRegex(russian, r"[Ѐ-ӿ]",
                         "[ru] contains no Cyrillic at all")

    def test_catalan_section_is_actually_catalan(self):
        """Catches a header typo or a pasted Spanish/English block: the
        Catalan letters (à è ò ç, the l·l of col·laboradors) must be there."""
        catalan = "".join(v for k, v in self.sections["ca"].items()
                          if k.startswith(MOD_PREFIX) and k not in NON_PROSE_IDS)
        for letter in ("à", "è", "ò", "ç", "l·l"):
            self.assertIn(letter, catalan, f"[ca] never uses {letter!r}")
        self.assertNotRegex(catalan, r"[ñÑ]", "[ca] contains a Spanish ñ")
        self.assertNotRegex(catalan, r"l\.l", "[ca] writes l.l: the punt volat is ·")

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
        """The English section is ASCII by record, not by necessity (T17).

        Debt T9 (no Cyrillic glyphs on Freedoom) was paid by D24 on
        2026-10-13, so non-ASCII no longer prints blank. The English
        designations are still the Latin transliteration, and this test
        pins that so the switch to the Cyrillic forms D17 asks for (MOD-SPEC
        6.4, debt T17) is a deliberate change with an engine screenshot,
        not a stray character. Flip or delete this test in that change.

        One explicit exception: the German letters. Since D36 the Reich
        speaks real German, and since D37 (2026-10-13) the alphabet draws
        Ä Ö Ü and the sharp s, so "Vorwärts" is written as such in English
        too. Only those characters are allowed; any other non-ASCII
        character still fails here.
        """
        offenders = [
            f"{key} = {value}"
            for key, value in sorted(self.sections["default"].items())
            if any(ord(ch) > 127 and ch not in GERMAN_LETTERS for ch in value)
        ]
        self.assertEqual(
            offenders, [],
            "non-ASCII in the [enu default] section. The glyphs exist since D24; "
            "if this is the deliberate move to Cyrillic designations (debt T17), "
            "update this test in the same change:\n  "
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
        # SDLanguageOption = OptionMenuItemSDLanguageOption, the engine's
        # Option row that names "eng"/"enu"/"rus" instead of "Unknown"
        # (QA-G6-1); LanguageRowTest below pins what it may do.
        self.assertRegex(
            self.menudef,
            r'(?m)^\s*SDLanguageOption\s+"\$SD_OPTMNU_LANGUAGE",\s*"language",\s*"SD_LanguageValues"',
            "the language row must drive GZDoom's own archived `language` CVar, "
            "so the choice persists without the mod writing a CVar of its own")

    def test_every_language_is_offered_explicitly(self):
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
        self.assertEqual(offered, ["auto", "default", "ru", "ca"],
                         "the list must name every value `language` can hold "
                         "here: auto, English, Russian and Catalan (D97)")

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
        were reproduced in-engine on 2026-10-13. The only menu code is the
        language row's class, which READS the CVar (LanguageRowTest); every
        write is the engine's own, from MenuEvent.
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



class LanguageRowTest(unittest.TestCase):
    """Bug QA-G6-1: the Language row read "Unknown" for "eng", "enu", "rus".

    The engine's Option row draws "Unknown" when the CVar's value is not in
    the list (gzdoom.pk3:zscript/engine/ui/menu/optionmenuitems.zs,
    OptionMenuItemOptionBase.Draw). src/zscript/sd/language_option.zs maps
    every other spelling onto the list entry of the language the mod's text
    is actually shown in, and may only READ the CVar (ADR 004, D-004-4).
    """

    ZS = SRC / "zscript" / "sd" / "language_option.zs"
    CLASS = "OptionMenuItemSDLanguageOption"

    # What the row must show for each value the `language` CVar can hold.
    # The mod ships [enu default], [ru] and [ca] (D97), so every code that is
    # not auto, Russian or Catalan reads the default (English) section. "default" is
    # GZDoom's own "English (US)" (gzdoom.pk3:menudef.txt, LanguageOptions).
    # "" shows Automatic (the PM's call for QA-G6-1); what the engine does
    # with an empty `language` is NOT VERIFIED, and no menu writes it.
    EXPECTED = {
        "auto": "auto", "AUTO": "auto",
        "default": "default", "enu": "default", "eng": "default",
        "en": "default", "EN": "default", "fr": "default", "": "auto",
        "ru": "ru", "RU": "ru", "rus": "ru",
        "ca": "ca", "CA": "ca", "cat": "ca", "es": "default",
    }

    @classmethod
    def setUpClass(cls) -> None:
        raw = cls.ZS.read_text(encoding="utf-8")
        cls.code = "\n".join(strip_comment(line) for line in raw.splitlines())
        menudef = (SRC / "lumps" / "MENUDEF").read_text(encoding="utf-8")
        menudef = "\n".join(strip_comment(line) for line in menudef.splitlines())
        values = re.search(r'OptionString\s+"SD_LanguageValues"\s*\{(.*?)\}', menudef, re.DOTALL)
        cls.offered = re.findall(r'"([^"]*)",\s*"\$', values.group(1))
        cls.consts = dict(re.findall(r'const\s+(VALUE_\w+)\s*=\s*"([^"]*)"\s*;', cls.code))

    @staticmethod
    def reference(value: str) -> str:
        """Python twin of ListEntryFor; the source checks below tie them."""
        if value == "" or value.lower() == "auto":
            return "auto"
        if value[:2].lower() == "ru":
            return "ru"
        if value[:2].lower() == "ca":
            return "ca"
        return "default"

    def function_body(self, name: str) -> str:
        match = re.search(r"\b" + name + r"\s*\([^)]*\)\s*\{(.*?)\n\t\}", self.code, re.DOTALL)
        self.assertIsNotNone(match, f"{name} not found in {self.ZS.name}")
        return match.group(1)

    def test_the_class_extends_the_engines_option_row(self):
        self.assertRegex(self.code, r"\bclass\s+" + self.CLASS + r"\s*:\s*OptionMenuItemOption\b")

    def test_the_file_is_included_once(self):
        entry = (SRC / "lumps" / "zscript.txt").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'^#include\s+"zscript/sd/language_option\.zs"', entry, re.M)), 1)

    def test_it_overrides_only_the_reading_of_the_cvar(self):
        # SetSelection and MenuEvent are where the CVar is written; they stay
        # the engine's so the write happens during input handling only.
        self.assertEqual(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", self.code), ["GetSelection"])
        self.assertNotRegex(self.code, r"\.Set(String|Int|Float|Bool)\s*\(")

    def test_its_constants_are_the_menudef_entries(self):
        self.assertEqual(self.offered, ["auto", "default", "ru", "ca"])
        self.assertEqual(self.consts, {"VALUE_AUTO": "auto", "VALUE_ENGLISH": "default",
                                       "VALUE_RUSSIAN": "ru", "VALUE_CATALAN": "ca"})

    def test_every_plausible_value_names_a_listed_language(self):
        for value, entry in self.EXPECTED.items():
            with self.subTest(value=value):
                self.assertEqual(self.reference(value), entry)
                self.assertIn(entry, self.offered)

    def test_the_zscript_rule_is_the_reference_rule(self):
        body = self.function_body("ListEntryFor")
        steps = [r"value\.Length\(\)\s*==\s*0\s*\|\|\s*value\s*~==\s*VALUE_AUTO",
                 r"return\s+VALUE_AUTO\s*;",
                 r"value\.Left\(2\)\s*~==\s*VALUE_RUSSIAN",
                 r"return\s+VALUE_RUSSIAN\s*;",
                 r"value\.Left\(2\)\s*~==\s*VALUE_CATALAN",
                 r"return\s+VALUE_CATALAN\s*;",
                 r"return\s+VALUE_ENGLISH\s*;\s*$"]
        position = 0
        for step in steps:
            match = re.compile(step).search(body, position)
            self.assertIsNotNone(match, f"ListEntryFor lost the step /{step}/ or its order")
            position = match.end()

    def test_get_selection_keeps_exact_matches_and_maps_the_rest(self):
        body = self.function_body("GetSelection")
        self.assertRegex(body, r"Super\.GetSelection\(\)", "an exact entry must still win")
        self.assertRegex(body, r"ListEntryFor\(\s*mCVar\.GetString\(\)\s*\)")


class CatalanTest(unittest.TestCase):
    """P6 (D97): the third language, [ca]. What the D7 tests above do not say.

    The parity of ids, the copies of the English and the placeholders are
    checked for every language above; here: the ids P6 added, the glyphs the
    Catalan text needs, and what the status bar draws for [ca]."""

    FONT_DIR = PROJECT_ROOT / "assets" / "fonts" / "defsmallfont"
    # Not text: names of graphics, never drawn as letters.
    GRAPHIC_NAME_IDS = frozenset({"SD_PAUSE_SIGN", "SD_SBAR_IMAGE", "SD_SBAR_ARMS_IMAGE"})

    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))

    def value(self, code: str, key: str) -> str:
        self.assertIn(key, self.sections[code], f"[{code}] has no {key}")
        return self.sections[code][key].strip('"')

    def glyph(self, ch: str) -> bool:
        return (self.FONT_DIR / f"{ord(ch):04X}.png").is_file()

    def test_the_language_names_its_own_row(self):
        """The fourth row of the language list (MENUDEF) in every language."""
        self.assertEqual(self.value("default", "SD_LANGVAL_CA"), "Catalan")
        self.assertEqual(self.value("ru", "SD_LANGVAL_CA"), "Каталанский")
        self.assertEqual(self.value("ca", "SD_LANGVAL_CA"), "Català")

    def test_the_death_prompt_has_one_key_slot(self):
        """SD_DEATH_PROMPT (D100): the code fills %s with a key's name."""
        expected = {"default": "Press %s to continue",
                    "ru": "Нажмите %s, чтобы продолжить",
                    "ca": "Prem %s per continuar"}
        self.assertEqual(set(expected), set(REQUIRED_SECTIONS))
        for code, text in expected.items():
            self.assertEqual(self.value(code, "SD_DEATH_PROMPT"), text, code)
            self.assertEqual(text.count("%s"), 1)

    def test_every_catalan_character_is_drawn_or_a_known_accent(self):
        """SmallFont draws lower case with the capitals (the skill names in
        the 0955 screenshot), so each character is looked up as a capital.
        A character with no glyph must be one of CATALAN_UNDRAWN_ACCENTS,
        whose base letter is drawn instead (NOT VERIFIED on screen)."""
        import unicodedata
        missing = set()
        for key, raw in self.sections["ca"].items():
            if not key.startswith(MOD_PREFIX) or key in self.GRAPHIC_NAME_IDS:
                continue
            for ch in set(raw.strip('"').replace("\\n", "").upper()):
                if self.glyph(ch):
                    continue
                if ch in CATALAN_UNDRAWN_ACCENTS and self.glyph(unicodedata.normalize("NFD", ch)[0]):
                    continue
                missing.add(f"{key}: {ch!r} (U+{ord(ch):04X})")
        self.assertEqual(sorted(missing), [], "[ca] uses characters the fonts cannot draw")

    def test_the_undrawn_accents_really_are_undrawn(self):
        """When the fonts gain a Catalan glyph, it leaves the debt list."""
        drawn = sorted(ch for ch in CATALAN_UNDRAWN_ACCENTS if self.glyph(ch))
        self.assertEqual(drawn, [], "these accents have glyphs now: drop them from "
                                    "CATALAN_UNDRAWN_ACCENTS")

    def test_the_status_bar_names_the_catalan_pictures(self):
        self.assertEqual(self.value("ca", "SD_SBAR_IMAGE"), "SDSBCA")
        self.assertEqual(self.value("ca", "SD_SBAR_ARMS_IMAGE"), "SDARCA")

    def test_the_skill_ladder_keeps_its_references(self):
        """DIFFICULTY-NAMES.md: Order 227 and the Republican slogan, in
        their Catalan form ("No passaran", not the Spanish "No pasarán")."""
        self.assertEqual(self.value("ca", "SD_SKILL_3"), "Ni un pas enrere")
        self.assertTrue(self.value("ca", "SD_SKILL_4").startswith("No passaran"))


class MainMenuLogoTest(unittest.TestCase):
    """The menu's M_DOOM must land on the lockup painted into TITLEPIC.

    Bug E1: with no MainMenu of our own the engine used its own
    `StaticPatch 94, 2, "M_DOOM"`, which sits 34 px right and 2 px below the
    name block of TITLEPIC, so a "CO" of the latter showed past its left
    edge. The correct origin is the contract row in docs/engine/MOD-SPEC.md
    6.6; measured 2026-10-13, overlaying M_DOOM on TITLEPIC at (60,0) gives
    a mean per-channel difference of 6 against 22+ at every neighbouring
    offset. (The generator's manifest under gitignored work/art/shell/ is
    evidence of the measurement, not the contract: it is not in every clone.)
    """

    # From MOD-SPEC 6.6 (the contract). Changing this means art moved the
    # lockup: change the table there first, then MENUDEF, then this.
    LOGO_X, LOGO_Y = 60, 0

    @classmethod
    def setUpClass(cls) -> None:
        # Comments only: MENUDEF quotes the engine's own `StaticPatch 94, 2`
        # to explain why ours differs, and a test that reads comments would
        # count that as a second logo.
        raw = (SRC / "lumps" / "MENUDEF").read_text(encoding="utf-8")
        cls.menudef = "\n".join(strip_comment(line) for line in raw.splitlines())

    def test_the_main_menu_places_the_logo_itself(self):
        body = re.search(r'LISTMENU\s+"MainMenu"\s*\{(.*?)\n\}',
                         self.menudef, re.DOTALL)
        self.assertIsNotNone(body, "no MainMenu block: the engine's own 94,2 wins (bug E1)")
        patches = re.findall(r'StaticPatch\s+(-?\d+)\s*,\s*(-?\d+)\s*,\s*"M_DOOM"',
                             body.group(1))
        self.assertEqual(
            len(patches), 1,
            "expected exactly one M_DOOM StaticPatch in MainMenu. Zero means "
            "no logo; two means a second logo is being drawn next to the first.")
        self.assertEqual(
            (int(patches[0][0]), int(patches[0][1])), (self.LOGO_X, self.LOGO_Y),
            "the menu logo no longer sits on the TITLEPIC lockup")

    def test_every_logo_in_menudef_sits_on_the_lockup(self):
        """Since D31 the skill screen draws M_DOOM too, over the same
        TITLEPIC, so it is held to the same contract position."""
        patches = re.findall(r'StaticPatch\s+(-?\d+)\s*,\s*(-?\d+)\s*,\s*"M_DOOM"',
                             self.menudef)
        self.assertTrue(patches)
        self.assertEqual({(int(x), int(y)) for x, y in patches}, {(self.LOGO_X, self.LOGO_Y)})

    def test_the_main_menu_is_redeclared_whole(self):
        """A redeclared LISTMENU REPLACES the engine's: a missing item is a
        deleted item. These five destinations are the Doom main menu.

        Since D31 the items are TextItems, not Freedoom's PatchItems
        (tests/test_menudef.py holds that), so what is checked here is where
        each item leads, which is what the engine's copy must keep."""
        body = re.search(r'LISTMENU\s+"MainMenu"\s*\{(.*?)\n\}',
                         self.menudef, re.DOTALL)
        self.assertIsNotNone(body, "no MainMenu block")
        for target in ("PlayerclassMenu", "OptionsMenu", "LoadGameMenu",
                       "SaveGameMenu", "QuitMenu"):
            self.assertRegex(body.group(1), r'Item\s+"[^"]+",\s*"\w",\s*"' + target + '"',
                             f"MainMenu lost its {target} item; redeclaring the list "
                             "menu drops every item not restated")

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
