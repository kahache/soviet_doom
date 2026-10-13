"""MENUDEF after D31: the main menu and the skill screen are text in SDMENU.

The contract is docs/engine/MOD-SPEC.md 6.6 and the reasoning
docs/engine/adr/005-menu-text-instead-of-menu-graphics.md. What this suite
pins, statically and in a second:

  * Freedoom's menu pictures (M_NGAME, M_OPTION, ...) are gone from our menus;
    every item is a TextItem reading a `$SD_MNU_*` id that exists in BOTH
    languages (D7/D21);
  * the items use the font SDMENU, and the skill screen ends on SmallFont,
    because the rungs are built at run time in the descriptor's LAST font;
  * the logo stays at the MOD-SPEC 6.6 contract position, 60,0;
  * every SD_MNU_* character has a glyph in assets/fonts/sdmenu/, and every
    string fits on the 320-wide screen at the position MENUDEF gives it.

What it cannot pin is what the engine draws: colours, the exact glyph
advance, the selector. Those are the PM's engine pass (D26).
"""

from __future__ import annotations

import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_language import (  # noqa: E402  (shared parser, one definition)
    LANGUAGE_LUMP,
    PROJECT_ROOT,
    REQUIRED_SECTIONS,
    SRC,
    parse_language,
    strip_comment,
)

MENUDEF = SRC / "lumps" / "MENUDEF"
FONTS = PROJECT_ROOT / "assets" / "fonts"

MENU_FONT = "SDMENU"
# The rungs' font (D-004-1) and where its glyphs live.
SKILL_FONT = "SmallFont"
SKILL_FONT_DIR = FONTS / "defsmallfont"

# Freedoom's pictures of English words that D31 replaced (debt T12).
FREEDOOM_MENU_GRAPHICS = ("M_NGAME", "M_OPTION", "M_LOADG", "M_SAVEG",
                          "M_RDTHIS", "M_QUITG", "M_NEWG", "M_SKILL")

# MOD-SPEC 6.6: M_DOOM (200x64) goes at x=60, y=0. Same numbers as
# test_language.MainMenuLogoTest; change the table there first.
LOGO = (60, 0)

# The engine's Doom main menu, item for item: hotkey -> destination
# (gzdoom.pk3/menudef.txt, LISTMENU "MainMenu", IfGame(Doom) branch).
DOOM_MAIN_ITEMS = {
    "n": "PlayerclassMenu",
    "o": "OptionsMenu",
    "l": "LoadGameMenu",
    "s": "SaveGameMenu",
    "r": "ReadThisMenu",
    "q": "QuitMenu",
}

# Screen geometry. GZDoom lays menus out on a 320x200 virtual screen.
SCREEN_WIDTH = 320
# Doom's DEFAULTLISTMENU: Selector "M_SKULL1", -32, -5. The skull is drawn
# this far left of the selected item, so an item column left of it pushes
# the skull off a 4:3 screen.
SELECTOR_X_OFFSET = -32
# Ids drawn by MENUDEF in SDMENU.
MENU_ID_PREFIX = "SD_MNU_"

RE_LISTMENU = r'LISTMENU\s+"{name}"\s*\{{(.*?)\n\}}'
RE_FONT = re.compile(r'^\s*Font\s+"([^"]+)"(?:\s*,\s*"([^"]+)")?(?:\s*,\s*"([^"]+)")?', re.M)
RE_TEXTITEM = re.compile(r'^\s*TextItem\s+"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*"([^"]+)"', re.M)
RE_PATCHITEM = re.compile(r'^\s*PatchItem\b', re.M)
RE_STATICTEXT = re.compile(r'^\s*StaticText(Centered)?\s+(-?\d+)\s*,\s*(-?\d+)\s*,\s*"([^"]*)"', re.M)
RE_STATICPATCH = re.compile(r'^\s*StaticPatch\s+(-?\d+)\s*,\s*(-?\d+)\s*,\s*"([^"]+)"', re.M)
RE_POSITION = re.compile(r'^\s*Position\s+(-?\d+)\s*,\s*(-?\d+)', re.M)


def menudef_code() -> str:
    """MENUDEF without comments: they quote the engine's PatchItem lines."""
    raw = MENUDEF.read_text(encoding="utf-8")
    return "\n".join(strip_comment(line) for line in raw.splitlines())


def listmenu(code: str, name: str) -> str | None:
    match = re.search(RE_LISTMENU.format(name=name), code, re.DOTALL)
    return match.group(1) if match else None


def png_width(path: Path) -> int:
    """Width from the PNG's IHDR; stdlib only, like the rest of the suite."""
    blob = path.read_bytes()[:24]
    if blob[:8] != b"\x89PNG\r\n\x1a\n" or blob[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">I", blob[16:20])[0]


def glyph_path(font_dir: Path, char: str) -> Path:
    """GZDoom's folder-font naming: fonts/<name>/<HEX>.png, upper-case hex."""
    return font_dir / f"{ord(char):04X}.png"


def text_width(font_dir: Path, text: str) -> int:
    """Sum of the glyph PNGs' widths: the advance a folder font with no
    kerning in font.inf gives. An approximation of the engine's own
    measure (NOT VERIFIED to the pixel); missing glyphs count zero and are
    reported by the coverage test instead."""
    return sum(png_width(glyph_path(font_dir, ch)) for ch in text
               if glyph_path(font_dir, ch).is_file())


def unquote(value: str) -> str:
    """A LANGUAGE value as the engine prints it: quotes off, \\n kept."""
    return value.strip().strip('"')


class MenudefTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code = menudef_code()
        cls.main = listmenu(cls.code, "MainMenu")
        cls.skill = listmenu(cls.code, "SkillMenu")
        cls.sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))
        cls.menu_ids = sorted(k for k in cls.sections["default"] if k.startswith(MENU_ID_PREFIX))
        cls.font_dir = FONTS / MENU_FONT.lower()

    def string(self, code: str, string_id: str) -> str:
        return unquote(self.sections[code][string_id])


class MainMenuTextTest(MenudefTestCase):
    def test_main_menu_exists(self):
        self.assertIsNotNone(self.main, "no LISTMENU \"MainMenu\" in MENUDEF")

    def test_no_patch_items_left(self):
        """D31: the items are text, not Freedoom's pictures of English."""
        self.assertIsNone(RE_PATCHITEM.search(self.main),
                          "MainMenu still has a PatchItem; D31 turned every item into a "
                          "TextItem (MOD-SPEC 6.6)")

    def test_no_freedoom_menu_graphic_is_named_anywhere(self):
        named = [g for g in FREEDOOM_MENU_GRAPHICS
                 if re.search(r'"' + g + r'"', self.code)]
        self.assertEqual(named, [],
                         "MENUDEF names a Freedoom menu graphic again (debt T12, D31)")

    def test_every_item_reads_an_sd_mnu_id_in_both_languages(self):
        items = RE_TEXTITEM.findall(self.main)
        self.assertTrue(items, "MainMenu has no TextItem")
        for text, _key, _target in items:
            self.assertTrue(text.startswith("$" + MENU_ID_PREFIX),
                            f"TextItem {text!r} is not a $SD_MNU_* LANGUAGE id")
            for code in REQUIRED_SECTIONS:
                self.assertIn(text[1:], self.sections[code],
                              f"[{code}] has no {text[1:]}; the item would print its raw id")

    def test_hotkeys_and_destinations_are_the_engines(self):
        """Same keys, same menus as the PatchItems they replaced."""
        items = RE_TEXTITEM.findall(self.main)
        seen = {key: target for _text, key, target in items}
        self.assertEqual(seen, DOOM_MAIN_ITEMS)

    def test_both_ifoption_branches_survive(self):
        """The player's "swap menu" and "show ReadThis" settings keep working."""
        for option in ("SwapMenu", "ReadThis"):
            self.assertRegex(self.main, r"IfOption\(" + option + r"\)",
                             f"MainMenu lost its IfOption({option}) branch")
        swap = re.search(r"IfOption\(SwapMenu\)\s*\{(.*?)\}\s*else\s*\{(.*?)\}",
                         self.main, re.DOTALL)
        self.assertIsNotNone(swap, "the SwapMenu branch lost its else")
        for branch in swap.groups():
            self.assertEqual(sorted(k for _t, k, _m in RE_TEXTITEM.findall(branch)),
                             ["l", "o", "s"])

    def test_the_menu_is_drawn_in_sdmenu(self):
        fonts = RE_FONT.findall(self.main)
        self.assertEqual(len(fonts), 1, "MainMenu should set exactly one font")
        name, normal, selected = fonts[0]
        self.assertEqual(name.upper(), MENU_FONT)
        self.assertTrue(normal and selected,
                        "give SDMENU a colour: its glyphs are drawn red and TITLEPIC is red")
        first_item = RE_TEXTITEM.search(self.main).start()
        self.assertLess(RE_FONT.search(self.main).start(), first_item,
                        "Font must come before the items: each takes the font when parsed")

    def test_logo_stays_on_the_title_lockup(self):
        patches = RE_STATICPATCH.findall(self.main)
        self.assertEqual([(int(x), int(y), n) for x, y, n in patches],
                         [(*LOGO, "M_DOOM")])


class SkillScreenTest(MenudefTestCase):
    def test_skill_menu_exists(self):
        self.assertIsNotNone(self.skill, "no LISTMENU \"SkillMenu\" in MENUDEF")

    def test_header_is_sdmenu_text(self):
        texts = RE_STATICTEXT.findall(self.skill)
        self.assertTrue(texts, "the skill screen has no StaticText header")
        for _centered, _x, _y, text in texts:
            self.assertTrue(text.startswith("$" + MENU_ID_PREFIX), text)
        # Each static item takes the font in force where it is parsed.
        fonts = [(m.start(), m.group(1)) for m in RE_FONT.finditer(self.skill)]
        for match in RE_STATICTEXT.finditer(self.skill):
            in_force = [name for pos, name in fonts if pos < match.start()]
            self.assertTrue(in_force and in_force[-1].upper() == MENU_FONT,
                            f"{match.group(4)} is not drawn in {MENU_FONT}")

    def test_the_rungs_font_comes_last(self):
        """The rungs are built at run time in the descriptor's LAST font.
        If SDMENU came last, D22 letterforms would reach the CEO's skill names
        and rung 5 would not fit (BUG E4 again)."""
        fonts = RE_FONT.findall(self.skill)
        self.assertTrue(fonts, "the skill screen sets no font")
        self.assertEqual(fonts[-1][0], SKILL_FONT)

    def test_only_the_logo_is_a_graphic(self):
        patches = RE_STATICPATCH.findall(self.skill)
        self.assertEqual([(int(x), int(y), n) for x, y, n in patches],
                         [(*LOGO, "M_DOOM")])


class MenuStringsTest(MenudefTestCase):
    def test_there_are_menu_strings(self):
        self.assertTrue(self.menu_ids, "no SD_MNU_* ids in LANGUAGE")

    def test_every_menu_id_exists_in_both_languages(self):
        for code in REQUIRED_SECTIONS:
            missing = [i for i in self.menu_ids if i not in self.sections[code]]
            self.assertEqual(missing, [], f"[{code}] lacks {missing}")

    def test_menu_strings_are_capitals(self):
        """SDMENU has no lowercase glyphs; what the engine does with
        lowercase in it is NOT VERIFIED, so the strings do not ask."""
        for code in REQUIRED_SECTIONS:
            for string_id in self.menu_ids:
                value = self.string(code, string_id)
                self.assertEqual(value, value.upper(), f"[{code}] {string_id} = {value!r}")

    def test_the_font_is_installed(self):
        """MENUDEF names SDMENU; without assets/fonts/sdmenu/ the PK3 has no
        such font (tools/check_pk3.py says the same about the package)."""
        self.assertTrue((self.font_dir / "font.inf").is_file(),
                        f"{self.font_dir.relative_to(PROJECT_ROOT)} is missing: "
                        "art-director's font has not been installed")

    def test_every_character_has_a_glyph(self):
        if not self.font_dir.is_dir():
            self.skipTest("no SDMENU yet; test_the_font_is_installed reports it")
        missing = sorted({
            f"[{code}] {string_id}: {ch!r} (U+{ord(ch):04X})"
            for code in REQUIRED_SECTIONS
            for string_id in self.menu_ids
            for ch in self.string(code, string_id)
            if not glyph_path(self.font_dir, ch).is_file()
        })
        self.assertEqual(missing, [], "SDMENU cannot draw:\n  " + "\n  ".join(missing))

    def test_main_items_fit_on_screen(self):
        if not self.font_dir.is_dir():
            self.skipTest("no SDMENU yet; test_the_font_is_installed reports it")
        x = min(int(px) for px, _py in RE_POSITION.findall(self.main))
        for text, _key, _target in RE_TEXTITEM.findall(self.main):
            for code in REQUIRED_SECTIONS:
                width = text_width(self.font_dir, self.string(code, text[1:]))
                self.assertLessEqual(x + width, SCREEN_WIDTH,
                                     f"[{code}] {text} is {width} px from x={x}")

    def test_skill_header_fits_on_screen(self):
        if not self.font_dir.is_dir():
            self.skipTest("no SDMENU yet; test_the_font_is_installed reports it")
        for centered, x, _y, text in RE_STATICTEXT.findall(self.skill):
            for code in REQUIRED_SECTIONS:
                width = text_width(self.font_dir, self.string(code, text[1:]))
                left = int(x) - width // 2 if centered else int(x)
                self.assertGreaterEqual(left, 0, f"[{code}] {text}")
                self.assertLessEqual(left + width, SCREEN_WIDTH,
                                     f"[{code}] {text} is {width} px from x={left}")

    def test_skill_rungs_and_selector_fit_on_screen(self):
        """BUG E4's sequel: rung 5 must fit on the right and the skull on
        the left. The rungs are mixed case in LANGUAGE and SmallFont draws
        them in capitals (seen in the 0955 screenshot), hence upper()."""
        positions = RE_POSITION.findall(self.skill)
        self.assertEqual(len(positions), 1, "the skill screen needs one Position")
        x = int(positions[0][0])
        self.assertGreaterEqual(x + SELECTOR_X_OFFSET, 0,
                                "the skull selector would leave a 4:3 screen")
        for code in REQUIRED_SECTIONS:
            for n in range(1, 6):
                name = self.string(code, f"SD_SKILL_{n}").upper()
                width = text_width(SKILL_FONT_DIR, name)
                self.assertLessEqual(x + width, SCREEN_WIDTH,
                                     f"[{code}] SD_SKILL_{n} is {width} px from x={x}")


class FontReferenceTest(MenudefTestCase):
    # Fonts the engine itself provides (names in gzdoom.exe g4.14.2 and in
    # gzdoom.pk3/menudef.txt). Anything else must be a folder in assets/fonts.
    ENGINE_FONTS = frozenset(n.upper() for n in (
        "SmallFont", "SmallFont2", "BigFont", "BigUpper", "ConsoleFont",
        "NewSmallFont", "NewConsoleFont", "IntermissionFont",
        "OriginalSmallFont", "OriginalBigFont"))

    def test_every_font_menudef_names_exists(self):
        names = {m.group(1) for m in RE_FONT.finditer(self.code)}
        missing = [n for n in sorted(names)
                   if n.upper() not in self.ENGINE_FONTS
                   and not (FONTS / n.lower()).is_dir()]
        self.assertEqual(missing, [],
                         "MENUDEF names a font that is neither the engine's nor in assets/fonts/")

    def test_sdmenu_is_used_only_by_the_two_menus(self):
        """D22's exception list (proper nouns, calibres, key prompts keep
        Latin) is honoured by WHERE SDMENU is used. Anywhere else, check it
        first (MOD-SPEC 6.6)."""
        blocks = re.findall(r'^(?:LISTMENU|ListMenu|OptionMenu|AddOptionMenu|AddListMenu)\s+"([^"]+)"[^{]*\{(.*?)^\}',
                            self.code, re.DOTALL | re.MULTILINE)
        users = sorted(name for name, body in blocks
                       if re.search(r'Font\s+"' + MENU_FONT + '"', body, re.I))
        self.assertEqual(users, ["MainMenu", "SkillMenu"])


if __name__ == "__main__":
    unittest.main()
