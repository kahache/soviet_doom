"""D100 (v1.1): "Press <key> to continue" on the dead player's screen.

Contract: docs/engine/MOD-SPEC.md 6.10. What is pinned here, without ever
starting GZDoom (D26):

  * zscript.txt includes death_prompt.zs once; the file declares one class,
    SD_DeathPrompt : EventHandler, overriding WorldTick and RenderOverlay
    only, and changes no rule (it never writes playerstate or a CVar);
  * MAPINFO's GameInfo registers it in AddEventHandlers, after
    SD_LoadReporter (tests/test_build.py reads the first name);
  * the timing (shown after ~1-2 s, blinking), the LANGUAGE id with its %s,
    the +use lookup through the engine's key table and the fallback string;
  * LANGUAGE has SD_DEATH_PROMPT in every section with exactly one %s, and
    every character of it, in every language, has a glyph in both fonts the
    handler may draw with (BigFont and SmallFont, the mod's folder fonts);
  * every engine name the handler relies on is declared in the installed
    gzdoom.pk3 (skipped where GZDoom is absent, as in CI).

What it cannot pin is what the engine draws and what USE does: the PM's
engine pass (MOD-SPEC 6.10).

Run:  python3 -m unittest tests.test_death_prompt -v
"""

from __future__ import annotations

import csv
import io
import re
import sys
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS))

import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from test_language import parse_language  # noqa: E402
from test_pause_sign import strip_comments_and_strings  # noqa: E402

DEATH_PROMPT_ZS = SRC / "zscript" / "sd" / "death_prompt.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
MAPINFO = SRC / "lumps" / "MAPINFO"
LANGUAGE = SRC / "lumps" / "LANGUAGE"
FONTS = PROJECT_ROOT / "assets" / "fonts"

INCLUDE = "zscript/sd/death_prompt.zs"
CLASS = "SD_DeathPrompt"
PARENT = "EventHandler"
FIRST_HANDLER = "SD_LoadReporter"
OVERRIDES = ["WorldTick", "RenderOverlay"]
STRING_ID = "SD_DEATH_PROMPT"
PLACEHOLDER = "%s"
USE_COMMAND = "+use"
FALLBACK_ID = "CNTRLMNU_USE"          # gzdoom.pk3:language.0, "Use / Open"
TICRATE = 35
DELAY_RANGE = (TICRATE, 2 * TICRATE)  # D100's brief: "~1-2 s" after death
# The folder fonts the handler may draw with: BigFont, and SmallFont when
# the line does not fit (fonts/defsmallfont/ is the mod's SmallFont).
DRAW_FONTS = ("bigfont", "defsmallfont")
# Key names the engine can substitute (src/common/console/c_bind.cpp,
# KeyNames): letters, digits and these words; checked against the fonts too.
SAMPLE_KEYS = ("E", "Space", "Mouse2", "Enter", "Ctrl")


def code() -> str:
    return strip_comments_and_strings(DEATH_PROMPT_ZS.read_text(encoding="utf-8"))


def raw() -> str:
    return DEATH_PROMPT_ZS.read_text(encoding="utf-8")


def strip_lump_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def const(name: str) -> str:
    match = re.search(rf"\bconst\s+{name}\s*=\s*([^;]+);", raw())
    assert match, f"no const {name}"
    return match.group(1).strip()


def gzdoom_pk3() -> Path | None:
    return next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                 if (c.parent / "gzdoom.pk3").is_file()), None)


def unquote(value: str) -> str:
    """A LANGUAGE value: one or more quoted pieces, concatenated."""
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', value))


class IncludeTest(unittest.TestCase):
    def test_zscript_txt_includes_the_file_once(self):
        text = strip_lump_comments(ZSCRIPT_TXT.read_text(encoding="utf-8"))
        self.assertEqual(len(re.findall(rf'#include\s+"{re.escape(INCLUDE)}"', text)), 1)
        self.assertTrue(DEATH_PROMPT_ZS.is_file())

    def test_one_event_handler_class(self):
        c = code()
        self.assertEqual(re.findall(r"\bclass\s+(\w+)\s*:\s*(\w+)", c), [(CLASS, PARENT)])
        self.assertEqual(c.count("{"), c.count("}"), "unbalanced braces")

    def test_overrides_world_tick_and_render_overlay_only(self):
        self.assertEqual(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", code()), OVERRIDES)
        self.assertRegex(code(), r"\boverride\s+void\s+RenderOverlay\s*\(\s*RenderEvent\s+\w+\s*\)")

    def test_changes_no_rule(self):
        """It only draws: no player state, CVar or console command is written."""
        c = code()
        self.assertNotRegex(c, r"playerstate\s*=[^=]")
        self.assertNotRegex(c, r"(?i)\bCVar\b|SetInt|SetBool|SetString|SetFloat|SendNetworkEvent")
        self.assertNotRegex(c, r"(?i)\bSetBind\b|\bUnbindACommand\b")


class MapinfoTest(unittest.TestCase):
    def test_registered_after_the_load_reporter(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        lines = re.findall(r"(?im)^\s*AddEventHandlers\s*=\s*(.+)$", text)
        self.assertEqual(len(lines), 1, lines)
        names = re.findall(r'"([^"]+)"', lines[0])
        self.assertEqual(names[0], FIRST_HANDLER)
        self.assertEqual(names.count(CLASS), 1, names)


class BehaviourTest(unittest.TestCase):
    def test_shown_after_one_to_two_seconds(self):
        delay = int(const("SD_PROMPT_DELAY_TICS"))
        self.assertGreaterEqual(delay, DELAY_RANGE[0])
        self.assertLessEqual(delay, DELAY_RANGE[1])

    def test_it_blinks(self):
        period, on = int(const("SD_BLINK_PERIOD_TICS")), int(const("SD_BLINK_ON_TICS"))
        self.assertTrue(0 < on < period, (on, period))
        self.assertRegex(code(), r"%\s*SD_BLINK_PERIOD_TICS\s*>=\s*SD_BLINK_ON_TICS")

    def test_counts_on_the_play_side_while_dead(self):
        self.assertRegex(code(), r"override\s+void\s+WorldTick\s*\(\s*\)\s*\{\s*if\s*\("
                                 r"[^)]*playerstate\s*==\s*PST_DEAD\s*\)\s*\{\s*deadTics\+\+")
        self.assertRegex(raw(), r"\btransient\s+int\s+deadTics\s*;")

    def test_draws_only_for_a_dead_player_in_a_level(self):
        c = code()
        self.assertRegex(c, r"gamestate\s*!=\s*GS_LEVEL")
        self.assertRegex(c, r"playerstate\s*!=\s*PST_DEAD")

    def test_the_text_comes_from_language_with_the_key(self):
        self.assertEqual(const("SD_PROMPT_ID"), f'"${STRING_ID}"')
        self.assertEqual(const("SD_KEY_PLACEHOLDER"), f'"{PLACEHOLDER}"')
        self.assertRegex(code(), r"StringTable\.Localize\(\s*SD_PROMPT_ID\s*\)")
        self.assertRegex(code(), r"\.Substitute\(\s*SD_KEY_PLACEHOLDER\s*,\s*SD_UseKeyName\(\)\s*\)")

    def test_the_key_is_the_one_bound_to_use(self):
        self.assertEqual(const("SD_USE_COMMAND"), f'"{USE_COMMAND}"')
        self.assertRegex(code(), r"Bindings\.GetKeysForCommand\(\s*SD_USE_COMMAND\s*\)")
        self.assertRegex(code(), r"KeyBindings\.NameKeys\(")
        self.assertEqual(const("SD_USE_FALLBACK_ID"), f'"${FALLBACK_ID}"')

    def test_fonts_are_the_mods_and_never_sdmenu(self):
        """D22: key prompts stay Latin; SDMENU draws E as Э (MOD-SPEC 6.6)."""
        c = code()
        self.assertRegex(c, r"\bBigFont\b")
        self.assertRegex(c, r"\bSmallFont\b")
        self.assertNotRegex(raw(), r'(?i)"SDMENU"|GetFont')
        for folder in DRAW_FONTS:
            self.assertTrue((FONTS / folder).is_dir(), folder)

    def test_fits_the_screen(self):
        self.assertRegex(c := code(), r"Screen\.GetWidth\(\)\s*\*\s*SD_MAX_WIDTH")
        self.assertLess(float(const("SD_MAX_WIDTH")), 1.0)
        self.assertRegex(c, r"CleanXFac")


class LanguageTest(unittest.TestCase):
    """SD_DEATH_PROMPT is added by the LANGUAGE owner; this pins its shape."""

    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def test_every_section_has_it_with_one_placeholder(self):
        for code_, entries in self.sections.items():
            with self.subTest(section=code_):
                self.assertIn(STRING_ID, entries)
                self.assertEqual(unquote(entries[STRING_ID]).count(PLACEHOLDER), 1)
                self.assertEqual(unquote(entries[STRING_ID]).count("%"), 1)

    def test_every_character_has_a_glyph_in_both_fonts(self):
        for code_, entries in self.sections.items():
            if STRING_ID not in entries:
                continue
            for key in SAMPLE_KEYS:
                text = unquote(entries[STRING_ID]).replace(PLACEHOLDER, key)
                for folder in DRAW_FONTS:
                    missing = sorted({ch for ch in text.upper()
                                      if not (FONTS / folder / f"{ord(ch):04X}.png").is_file()})
                    self.assertEqual(missing, [], f"[{code_}] {text!r} in {folder}")


class EngineNamesTest(unittest.TestCase):
    """Every engine name the handler relies on is declared by gzdoom.pk3."""

    DECLARATIONS = {
        "EventHandler": r"^class\s+EventHandler\s*:\s*StaticEventHandler\b",
        "WorldTick": r"virtual\s+void\s+WorldTick\s*\(\s*\)",
        "RenderOverlay": r"virtual\s+ui\s+void\s+RenderOverlay\s*\(\s*RenderEvent\s+\w+\s*\)",
        "PST_DEAD": r"^\s*PST_DEAD\s*,",
        "playerstate": r"native\s+uint8\s+playerstate\s*;",
        "playeringame": r"native\s+readonly\s+bool\s+playeringame\s*\[",
        "consoleplayer": r"native\s+readonly\s+int\s+consoleplayer\s*;",
        "gamestate": r"native\s+readonly\s+int\s+gamestate\s*;",
        "GS_LEVEL": r"^\s*GS_LEVEL\s*,",
        "Bindings": r"native\s+@KeyBindings\s+Bindings\s*;",
        "GetKeysForCommand": r"native\s+int\s*,\s*int\s+GetKeysForCommand\s*\(\s*String\s+\w+\s*\)",
        "NameKeys": r"native\s+static\s+String\s+NameKeys\s*\(\s*int\s+\w+\s*,\s*int\s+\w+\s*\)",
        "Localize": r"native\s+static\s+String\s+Localize\s*\(\s*String",
        "Substitute": r"native\s+void\s+Substitute\s*\(\s*String\s+\w+\s*,\s*String",
        "BigFont": r"native\s+readonly\s+Font\s+bigfont\s*;",
        "SmallFont": r"native\s+readonly\s+Font\s+smallfont\s*;",
        "NewSmallFont": r"native\s+readonly\s+Font\s+NewSmallFont\s*;",
        "generic_ui": r"native\s+readonly\s+bool\s+generic_ui\s*;",
        "CleanXFac": r"native\s+readonly\s+int\s+CleanXFac\s*;",
        "StringWidth": r"native\s+int\s+StringWidth\s*\(\s*String",
        "GetHeight": r"native\s+int\s+GetHeight\s*\(\s*\)",
        "DrawText": r"native\s+static\s+vararg\s+void\s+DrawText\s*\(\s*Font\s+\w+\s*,\s*int\s+\w+\s*,\s*double\s+\w+\s*,\s*double\s+\w+\s*,\s*String",
        "DTA_ScaleX": r"^\s*DTA_ScaleX\s*,",
        "DTA_ScaleY": r"^\s*DTA_ScaleY\s*,",
        "CR_GOLD": r"^\s*CR_GOLD\s*,",
    }

    @classmethod
    def setUpClass(cls):
        pk3 = gzdoom_pk3()
        if pk3 is None:
            raise unittest.SkipTest("GZDoom not installed here (CI)")
        with zipfile.ZipFile(pk3) as z:
            cls.corpus = "\n".join(z.read(n).decode("utf-8", "replace")
                                   for n in z.namelist() if n.lower().endswith(".zs"))
            cls.language = {}
            for n in z.namelist():
                if n.lower().startswith("language.") and n.lower() != "language.def":
                    rows = list(csv.reader(io.StringIO(z.read(n).decode("utf-8", "replace"))))
                    cls.language.update({r[1]: r[0] for r in rows[1:] if len(r) > 1})

    def test_declared(self):
        for name, pattern in self.DECLARATIONS.items():
            with self.subTest(name=name):
                self.assertRegex(self.corpus, re.compile(pattern, re.M | re.I))
                self.assertRegex(code(), rf"(?i)\b{name}\b")

    def test_the_fallback_string_exists(self):
        self.assertTrue(self.language.get(FALLBACK_ID), FALLBACK_ID)


if __name__ == "__main__":
    unittest.main()
