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

    def test_language_probe_matches_its_section(self):
        """zscript/sd/language.zs trusts SD_LANG_CODE to name its section."""
        for code in REQUIRED_SECTIONS:
            value = self.sections[code].get("SD_LANG_CODE")
            self.assertIsNotNone(value, f"[{code}] defines no SD_LANG_CODE probe")
            self.assertEqual(
                value, f'"{code}"',
                f"[{code}] SD_LANG_CODE must be the section's own GZDoom code, "
                "or zscript/sd/language.zs will pin the wrong language",
            )

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
        cls.menudef = (SRC / "lumps" / "MENUDEF").read_text(encoding="utf-8")

    def test_the_option_drives_the_engine_language_cvar(self):
        self.assertRegex(
            self.menudef, r'Option\s+"\$SD_OPTMNU_LANGUAGE",\s*"language"',
            "the language row must drive GZDoom's own archived `language` CVar, "
            "so the choice persists without the mod writing a CVar of its own")

    def test_both_languages_are_offered_explicitly(self):
        # OptionString, not OptionValue: `language` is a string CVar and
        # OptionValue parses its left column with SC_GetFloat, which aborted
        # the engine at startup on "default" (CEO, 2026-10-13). The test
        # accepts only the string form so the crash cannot come back.
        values = re.search(r'OptionString\s+"SD_LanguageValues"\s*\{(.*?)\}',
                           self.menudef, re.DOTALL)
        self.assertIsNotNone(values, "no SD_LanguageValues list")
        offered = re.findall(r'"([^"]+)",\s*"\$', values.group(1))
        self.assertEqual(offered, ["default", "ru"],
                         "the menu must offer English and Russian explicitly, "
                         "and must not fall back on the system locale")

    def test_the_menu_is_reachable(self):
        self.assertRegex(self.menudef, r'AddOptionMenu\s+"OptionsMenu"',
                         "the mod's menu is never attached to GZDoom's Options menu")
        self.assertRegex(self.menudef, r'Submenu\s+"\$SD_OPTMNU_TITLE",\s*"SD_OptionsMenu"')

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
