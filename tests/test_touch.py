"""Touch mode (Android, D137; ADR 015): `sd_touch` and the lines that name keys.

Contract: docs/engine/MOD-SPEC.md 6.17; the study of what a phone needs:
docs/engine/2026-10-27_A1_mod-touch-adaptations.md. What is pinned here,
without ever starting GZDoom (D26):

  * CVARINFO declares `user noarchive bool sd_touch = false;` next to
    sd_reloads, and nothing of ours ever WRITES it (ADR 004);
  * zscript.txt includes touch.zs once; SD_Touch reads the CVar (missing =
    off) and names the bound key through the engine's key table;
    OptionMenuItemSDKeyText is a StaticText that fills its "%s" when drawn;
  * the death prompt, the reload note and the magazine readout each branch
    on SD_Touch.On() to their touch form (the LANGUAGE _TOUCH line with the
    button's label; the readout centred on x 160);
  * LANGUAGE: the touch ids exist in [enu default], [ru] and [ca] with one
    "%s" where a label goes and none in the labels, the English ASCII, the
    translations their own, every character of the touch prompt drawable
    in BigFont and SmallFont, the filled notes one menu row long;
  * NO string of ours, in any of the three languages, names a key by its
    letter ("Press E", "R reloads", "F1") outside the exceptions below.

The exceptions, and why: the fifteen quit lines carry "(Press Y to quit.)"
because the engine's own yes/no box takes Y and N (and, verified in
gzdoom.pk3's messagebox.zs, a mouse click on its Yes/No rows, which is what
a tap sends); the [ca] section mirrors seven ENGINE strings (PRESSKEY,
PRESSYN...) whose English and Russian are the engine's own wording. Both
are listed in the doc as the app's to cover, not the mod's.

What it cannot pin is what the engine draws: the PM's engine pass.

Run:  python3 -m unittest tests.test_touch -v
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
LUMPS = SRC / "lumps"
TOOLS = PROJECT_ROOT / "tools"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS))

import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from test_language import parse_language  # noqa: E402
from test_pause_sign import strip_comments_and_strings  # noqa: E402

CVARINFO = LUMPS / "CVARINFO"
MENUDEF = LUMPS / "MENUDEF"
LANGUAGE = LUMPS / "LANGUAGE"
ZSCRIPT_TXT = LUMPS / "zscript.txt"
TOUCH_ZS = SRC / "zscript" / "sd" / "touch.zs"
DEATH_PROMPT_ZS = SRC / "zscript" / "sd" / "death_prompt.zs"
MAGAZINE_HUD_ZS = SRC / "zscript" / "sd" / "magazine_hud.zs"
FONTS = PROJECT_ROOT / "assets" / "fonts"
DOC = PROJECT_ROOT / "docs" / "engine" / "2026-10-27_A1_mod-touch-adaptations.md"
ADR = PROJECT_ROOT / "docs" / "engine" / "adr" / "015-touch-mode.md"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"

CVAR = "sd_touch"
INCLUDE = "zscript/sd/touch.zs"
LANGS = ("enu", "ru", "ca")
# The ids the touch mode adds; which carry a "%s" for a label, which ARE labels.
WITH_PLACEHOLDER = ("SD_DEATH_PROMPT_TOUCH", "SD_OPTMNU_RELOADHELP_TOUCH", "SD_OPTMNU_RELOADHELP")
LABELS = ("SD_TOUCH_BTN_USE", "SD_TOUCH_BTN_RELOAD")
# The row the SDKeyText item takes in MENUDEF: note, command, touch note, label.
KEY_TEXT_ROW = ('SDKeyText "$SD_OPTMNU_RELOADHELP", "+reload", '
                '"$SD_OPTMNU_RELOADHELP_TOUCH", "$SD_TOUCH_BTN_RELOAD"')
HELP_MAX = 48            # one option row (tests/test_reloads.py's limit)
DRAW_FONTS = ("bigfont", "defsmallfont")
SCREEN_W = 320

# Strings allowed to name a key, and why (the module docstring).
QUIT_LINES = tuple(f"SD_QUIT_{n:02d}" for n in range(1, 16))
ENGINE_MIRRORS_CA = ("QSPROMPT", "QLPROMPT", "QSAVESPOT", "SAVEDEAD", "ENDGAME", "PRESSYN", "PRESSKEY")

# What "names a key" means here, on the text with its %s taken out:
# a press verb followed by a single capital letter or digit; a single
# capital letter doing the reloading; a function key; the engine's names
# for the special keys.
KEY_PATTERNS = (
    r"\b(?:Press|Prem|Premeu|Нажмите|Нажми|Toca|Tap)\s+(?:the\s+)?[A-Z0-9](?![\w-])",
    r"(?<![\w%])[A-Z](?:\s+-\s+|\s+)(?:reloads|recarrega|перезарядка)",
    r"\bF(?:1[0-2]|[1-9])\b",
    r"\b(?:Esc|Escape|Enter|Tab|Ctrl|Shift|Alt|Space|Backspace|Mouse[0-9])\b",
)


def code(path: Path) -> str:
    return strip_comments_and_strings(path.read_text(encoding="utf-8"))


def raw(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_lump_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def const(path: Path, name: str) -> str:
    match = re.search(rf"\bconst\s+{name}\s*=\s*([^;]+);", raw(path))
    assert match, f"no const {name} in {path.name}"
    return match.group(1).strip()


def unquote(value: str) -> str:
    """A LANGUAGE value: one or more quoted pieces, concatenated."""
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', value))


def gzdoom_pk3() -> Path | None:
    return next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                 if (c.parent / "gzdoom.pk3").is_file()), None)


class CvarTest(unittest.TestCase):
    def test_declared_user_noarchive_off(self):
        lines = [ln.strip() for ln in strip_lump_comments(raw(CVARINFO)).splitlines() if ln.strip()]
        self.assertIn(f"user noarchive bool {CVAR} = false;", lines)
        self.assertEqual(len([ln for ln in lines if CVAR in ln]), 1)

    def test_the_code_reads_that_name_and_a_missing_cvar_is_off(self):
        self.assertEqual(const(TOUCH_ZS, "SD_TOUCH_CVAR"), f'"{CVAR}"')
        c = code(TOUCH_ZS)
        self.assertRegex(c, r"static\s+bool\s+On\s*\(\s*\)\s*\{\s*CVar\s+cv\s*=\s*CVar\.FindCVar\(\s*SD_TOUCH_CVAR\s*\)"
                            r"\s*;\s*return\s+cv\s*!=\s*null\s*&&\s*cv\.GetBool\(\)\s*;")

    def test_nothing_of_ours_writes_it(self):
        """ADR 004: the app sets it on the command line; ZScript only reads."""
        for path in SRC.rglob("*.zs"):
            c = code(path)
            self.assertNotRegex(c, r"(?i)\bSetBool\b|\bSetInt\b|\bSetString\b|\bSetFloat\b", path.name)
        self.assertNotRegex(raw(LUMPS / "KEYCONF"), rf"(?i){CVAR}")
        self.assertNotRegex(raw(LUMPS / "MAPINFO"), rf"(?i){CVAR}")


class WiringTest(unittest.TestCase):
    def test_zscript_txt_includes_the_file_once_and_first_among_the_users(self):
        text = strip_lump_comments(raw(ZSCRIPT_TXT))
        includes = re.findall(r'#include\s+"([^"]+)"', text)
        self.assertEqual(includes.count(INCLUDE), 1)
        self.assertTrue(TOUCH_ZS.is_file())
        # ZScript resolves names regardless of order; this only keeps the
        # table of contents readable: the switch before what reads it.
        self.assertLess(includes.index(INCLUDE), includes.index("zscript/sd/death_prompt.zs"))
        self.assertLess(includes.index(INCLUDE), includes.index("zscript/sd/magazine_hud.zs"))

    def test_two_classes_the_switch_and_the_row(self):
        c = code(TOUCH_ZS)
        self.assertEqual(re.findall(r"\bclass\s+(\w+)(?:\s*:\s*(\w+))?\s*\{", c),
                         [("SD_Touch", ""), ("OptionMenuItemSDKeyText", "OptionMenuItemStaticText")])
        self.assertEqual(c.count("{"), c.count("}"), "unbalanced braces")

    def test_the_key_lookup_is_the_engines_key_table(self):
        c = code(TOUCH_ZS)
        self.assertRegex(c, r"static\s+ui\s+String\s+KeyNameFor\s*\(\s*String\s+command\s*,\s*String\s+fallbackId\s*\)")
        self.assertRegex(c, r"Bindings\.GetKeysForCommand\(\s*command\s*\)")
        self.assertRegex(c, r"KeyBindings\.NameKeys\(\s*first\s*,\s*0\s*\)")
        self.assertRegex(c, r"StringTable\.Localize\(\s*fallbackId\s*\)")

    def test_the_row_overrides_draw_only_and_fills_the_placeholder(self):
        c = code(TOUCH_ZS)
        self.assertEqual(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", c), ["Draw"])
        self.assertEqual(const(TOUCH_ZS, "SD_KEY_PLACEHOLDER"), '"%s"')
        self.assertEqual(const(TOUCH_ZS, "SD_CONTROL_NAME_PREFIX"), '"$CNTRLMNU_"')
        self.assertRegex(c, r"OptionMenuItemSDKeyText\s+Init\s*\(\s*String\s+label\s*,\s*String\s+command\s*,"
                            r"\s*String\s+touchLabel\s*,\s*String\s+buttonId\s*,\s*int\s+cr\s*=\s*-1\s*\)")
        # Touch: the _TOUCH line with the label; desktop: the line with the key.
        self.assertRegex(c, r"if\s*\(\s*SD_Touch\.On\(\)\s*\)\s*\{\s*text\s*=\s*StringTable\.Localize\(\s*mTouchLabel\s*\)\s*;"
                            r"\s*text\.Substitute\(\s*SD_KEY_PLACEHOLDER\s*,\s*StringTable\.Localize\(\s*mButtonId\s*\)\s*\)")
        self.assertRegex(c, r"text\.Substitute\(\s*SD_KEY_PLACEHOLDER\s*,\s*SD_Touch\.KeyNameFor\(\s*mCommand\s*,\s*fallback\s*\)\s*\)")
        # Drawn as the engine draws a centred StaticText (drawLabel).
        self.assertRegex(c, r"Menu\.OptionWidth\(\s*text\s*\)\s*\*\s*CleanXfac_1")
        self.assertRegex(c, r"drawText\(\s*x\s*,\s*y\s*,\s*mColor\s*,\s*text\s*\)")

    def test_the_command_stem(self):
        c = code(TOUCH_ZS)
        self.assertRegex(c, r"static\s+String\s+SD_CommandStem\s*\(\s*String\s+command\s*\)")
        self.assertRegex(raw(TOUCH_ZS), r'stem\.Left\(\s*1\s*\)\s*==\s*"\+"')
        self.assertRegex(c, r"return\s+stem\.MakeUpper\(\)\s*;")


class UsersTest(unittest.TestCase):
    def test_the_death_prompt_branches_to_the_touch_line(self):
        self.assertEqual(const(DEATH_PROMPT_ZS, "SD_PROMPT_TOUCH_ID"), '"$SD_DEATH_PROMPT_TOUCH"')
        self.assertEqual(const(DEATH_PROMPT_ZS, "SD_TOUCH_BUTTON_ID"), '"$SD_TOUCH_BTN_USE"')
        c = code(DEATH_PROMPT_ZS)
        self.assertRegex(c, r"if\s*\(\s*SD_Touch\.On\(\)\s*\)\s*\{\s*text\s*=\s*StringTable\.Localize\(\s*SD_PROMPT_TOUCH_ID\s*\)\s*;"
                            r"\s*text\.Substitute\(\s*SD_KEY_PLACEHOLDER\s*,\s*StringTable\.Localize\(\s*SD_TOUCH_BUTTON_ID\s*\)\s*\)")
        # The desktop path is untouched (tests/test_death_prompt.py pins it).
        self.assertRegex(c, r"else\s*\{\s*text\s*=\s*StringTable\.Localize\(\s*SD_PROMPT_ID\s*\)")

    def test_the_magazine_readout_is_centred(self):
        self.assertEqual(int(const(MAGAZINE_HUD_ZS, "SD_MAG_TOUCH_CENTRE")), SCREEN_W // 2)
        c = code(MAGAZINE_HUD_ZS)
        self.assertRegex(c, r"if\s*\(\s*SD_Touch\.On\(\)\s*\)\s*\{\s*left\s*=\s*SD_MAG_TOUCH_CENTRE\s*-\s*fnt\.StringWidth\(\s*text\s*\)\s*/\s*2\.")
        # The heights do not move: the bar's and the fullscreen HUD's rows.
        self.assertRegex(c, r"Screen\.DrawText\(\s*fnt\s*,\s*colour\s*,\s*left\s*,\s*top\s*,\s*text\s*,")

    def test_the_menu_row(self):
        menu = strip_lump_comments(raw(MENUDEF))
        block = re.search(r'OptionMenu\s+"SD_OptionsMenu"\s*\{(.*?)\n\}', menu, re.S).group(1)
        self.assertIn(KEY_TEXT_ROW, block)
        self.assertNotIn('StaticText "$SD_OPTMNU_RELOADHELP"', block)
        self.assertLess(block.index('Option "$SD_OPTMNU_RELOADS"'), block.index("SDKeyText"))


class LanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def test_every_language_has_the_ids(self):
        for lang in LANGS:
            for ident in WITH_PLACEHOLDER + LABELS:
                with self.subTest(lang=lang, ident=ident):
                    self.assertIn(ident, self.sections[lang])
                    self.assertTrue(unquote(self.sections[lang][ident]).strip())

    def test_placeholders(self):
        for lang in LANGS:
            for ident in WITH_PLACEHOLDER:
                self.assertEqual(unquote(self.sections[lang][ident]).count("%s"), 1, f"[{lang}] {ident}")
                self.assertEqual(unquote(self.sections[lang][ident]).count("%"), 1, f"[{lang}] {ident}")
            for ident in LABELS:
                text = unquote(self.sections[lang][ident])
                self.assertNotIn("%", text, f"[{lang}] {ident}")
                self.assertEqual(text, text.upper(), f"[{lang}] {ident}: BigFont has no lowercase")

    def test_english_is_ascii_and_the_translations_are_their_own(self):
        for ident in WITH_PLACEHOLDER + LABELS:
            unquote(self.sections["enu"][ident]).encode("ascii")
            for lang in ("ru", "ca"):
                self.assertNotEqual(self.sections[lang][ident], self.sections["enu"][ident], f"[{lang}] {ident}")
        self.assertRegex(unquote(self.sections["ru"]["SD_DEATH_PROMPT_TOUCH"]), r"[Ѐ-ӿ]")
        self.assertRegex(unquote(self.sections["ru"]["SD_TOUCH_BTN_USE"]), r"^[Ѐ-ӿ]+$")

    def test_the_touch_prompt_is_drawable_in_both_fonts(self):
        """The death prompt draws BigFont, or SmallFont when it does not fit."""
        for lang in LANGS:
            text = unquote(self.sections[lang]["SD_DEATH_PROMPT_TOUCH"]).replace(
                "%s", unquote(self.sections[lang]["SD_TOUCH_BTN_USE"]))
            for folder in DRAW_FONTS:
                missing = sorted({ch for ch in text.upper()
                                  if not (FONTS / folder / f"{ord(ch):04X}.png").is_file()})
                self.assertEqual(missing, [], f"[{lang}] {text!r} in {folder}")

    def test_the_filled_notes_fit_one_menu_row(self):
        for lang in LANGS:
            touch = unquote(self.sections[lang]["SD_OPTMNU_RELOADHELP_TOUCH"]).replace(
                "%s", unquote(self.sections[lang]["SD_TOUCH_BTN_RELOAD"]))
            self.assertLessEqual(len(touch), HELP_MAX, f"[{lang}] {touch!r}")
            desktop = unquote(self.sections[lang]["SD_OPTMNU_RELOADHELP"]).replace("%s", "R")
            self.assertLessEqual(len(desktop), HELP_MAX, f"[{lang}] {desktop!r}")

    def test_no_string_names_a_key_outside_the_exceptions(self):
        """The inventory of docs/engine/2026-10-27_A1_mod-touch-adaptations.md 2."""
        offenders = []
        for lang in LANGS:
            for ident, value in self.sections[lang].items():
                if ident in QUIT_LINES or (lang == "ca" and ident in ENGINE_MIRRORS_CA):
                    continue
                text = unquote(value).replace("%s", "").replace("\\n", "\n")
                for pattern in KEY_PATTERNS:
                    if re.search(pattern, text):
                        offenders.append((lang, ident, pattern, text))
        self.assertEqual(offenders, [])

    def test_the_exceptions_are_what_they_say(self):
        """Keep the list honest: every excepted id really names Y or a key."""
        for lang in LANGS:
            for ident in QUIT_LINES:
                self.assertRegex(unquote(self.sections[lang][ident]),
                                 r"(?:Press|Нажмите|Prem) Y\b", f"[{lang}] {ident}")
        for ident in ENGINE_MIRRORS_CA:
            self.assertIn(ident, self.sections["ca"], ident)
            self.assertNotIn(ident, self.sections["enu"], f"{ident} is the engine's in English")
            self.assertNotIn(ident, self.sections["ru"], f"{ident} is the engine's in Russian")


class DocsTest(unittest.TestCase):
    def test_the_docs_exist_and_cross_reference(self):
        for path in (DOC, ADR):
            self.assertTrue(path.is_file(), path)
        doc = DOC.read_text(encoding="utf-8")
        for ref in (CVAR, "ADR 015", "MOD-SPEC.md", "+sd_touch 1", "cl_run", "con_centernotify",
                    "NOT VERIFIED", "SD_TOUCH_BTN_USE", "SD_TOUCH_BTN_RELOAD"):
            self.assertIn(ref, doc, ref)
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertIn("## 6.17 Touch mode", spec)
        for ident in LABELS + ("SD_DEATH_PROMPT_TOUCH", "SD_OPTMNU_RELOADHELP_TOUCH"):
            self.assertIn(ident, spec, ident)

    def test_the_button_labels_are_tabled_for_the_app(self):
        """The app copies the labels from the doc's table: every language's
        label must be in it, word for word."""
        doc = DOC.read_text(encoding="utf-8")
        sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))
        for lang in LANGS:
            for ident in LABELS:
                self.assertIn(unquote(sections[lang][ident]), doc, f"[{lang}] {ident}")


@unittest.skipUnless(gzdoom_pk3() is not None, "no gzdoom.pk3 on this machine (CI)")
class EngineNamesTest(unittest.TestCase):
    """The engine facts the code and the doc lean on, read from gzdoom.pk3."""

    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(gzdoom_pk3()) as z:
            cls.files = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()
                         if n.startswith(("zscript/", "engine/")) or n in ("menudef.txt",)}
            cls.language = {}
            for n in z.namelist():
                if n.lower().startswith("language.") and n.lower() != "language.def":
                    rows = list(csv.reader(io.StringIO(z.read(n).decode("utf-8", "replace"))))
                    cls.language.update({r[1]: r[0] for r in rows[1:] if len(r) > 1})

    def test_the_static_text_row_we_derive_from(self):
        items = self.files["zscript/engine/ui/menu/optionmenuitems.zs"]
        self.assertRegex(items, r"class\s+OptionMenuItemStaticText\s*:\s*OptionMenuItem\b")
        self.assertRegex(items, r"OptionMenuItemStaticText\s+Init\s*\(\s*String\s+label\s*,\s*int\s+cr\s*=\s*-1\s*\)")
        self.assertRegex(items, re.compile(r"^\s*int\s+mColor\s*;", re.M), msg="mColor is a plain field")
        self.assertRegex(items, re.compile(r"^\s*bool\s+mCentered\s*;", re.M))
        self.assertRegex(items, r"protected\s+void\s+drawText\s*\(\s*int\s+x\s*,\s*int\s+y\s*,\s*int\s+color\s*,\s*String\s+text")
        self.assertRegex(items, r"Menu\.OptionWidth\(\s*\w+\s*\)\s*\*\s*CleanXfac_1")
        self.assertRegex(items, r"override\s+int\s+Draw\s*\(\s*OptionMenuDescriptor\s+desc\s*,\s*int\s+y\s*,\s*int\s+indent\s*,\s*bool\s+selected\s*\)")

    def test_the_string_methods(self):
        base = self.files["zscript/engine/base.zs"]
        self.assertRegex(base, r"native\s+String\s+MakeUpper\s*\(\s*\)\s*const\s*;")
        self.assertRegex(base, r"native\s+String\s+Left\s*\(\s*int\s+len\s*\)\s*const\s*;")
        self.assertRegex(base, r"native\s+String\s+Mid\s*\(")
        self.assertRegex(base, r"native\s+void\s+Substitute\s*\(\s*String\s+\w+\s*,\s*String")

    def test_the_fallback_control_names_exist(self):
        for ident in ("CNTRLMNU_USE", "CNTRLMNU_RELOAD"):
            self.assertTrue(self.language.get(ident), ident)

    def test_the_quit_box_takes_a_tap_on_yes_or_no(self):
        """Why SD_QUIT_* may keep "(Press Y to quit.)": the engine's box also
        draws Yes/No rows and takes a mouse click on them."""
        box = self.files["zscript/engine/ui/menu/messagebox.zs"]
        self.assertIn('"$TXT_YES"', box)
        self.assertIn('"$TXT_NO"', box)
        self.assertRegex(box, r"override\s+bool\s+MouseEvent\s*\(\s*int\s+type\s*,\s*int\s+x\s*,\s*int\s+y\s*\)")
        self.assertRegex(box, r"type\s*==\s*MOUSE_Release")

    def test_the_menus_take_the_mouse(self):
        """Taps reach the menus as clicks: both menu kinds handle MouseEvent."""
        for name in ("zscript/engine/ui/menu/listmenu.zs", "zscript/engine/ui/menu/optionmenu.zs"):
            self.assertRegex(self.files[name], r"override\s+bool\s+MouseEvent\s*\(", name)
        items = self.files["zscript/engine/ui/menu/optionmenuitems.zs"]
        # A click on an Option row is Enter, which steps the value.
        self.assertRegex(items, r"type\s*==\s*Menu\.MOUSE_Release\s*\)\s*\{\s*return\s+Menu\.GetCurrentMenu\(\)\.MenuEvent\(\s*Menu\.MKEY_Enter")

    def test_the_rows_the_app_sets(self):
        """The CVars the doc tells the app to pass exist in the engine's menus."""
        menudef = self.files["menudef.txt"]
        for cvar in ("cl_run", "con_centernotify", "uiscale", "st_scale", "m_use_mouse", "use_mouse"):
            self.assertRegex(menudef, rf'"{cvar}"|\b{cvar}\b', cvar)

    def test_the_default_binds_the_doc_tables(self):
        binds = "\n".join(t for n, t in self.files.items() if n.startswith("engine/") and n.endswith("binds.txt"))
        for key, command in (("e", "+use"), ("w", "+forward"), ("s", "+back"), ("a", "+moveleft"),
                             ("d", "+moveright"), ("space", "+jump"), ("mouse1", "+attack"),
                             ("tab", "togglemap"), ("mwheelup", "weapprev"), ("mwheeldown", "weapnext"),
                             ("f6", "quicksave"), ("f9", "quickload"), ("8", '"slot 8"')):
            self.assertRegex(binds, rf"(?im)^\s*{re.escape(key)}\s+{re.escape(command)}\s*$", f"{key} {command}")

    def test_option_menu_settings_cannot_be_changed_at_run_time(self):
        """Why the row height stays the engine's: the settings are read-only."""
        self.assertRegex(self.files["zscript/engine/base.zs"],
                         r"native\s+readonly\s+@FOptionMenuSettings\s+OptionMenuSettings\s*;")


if __name__ == "__main__":
    unittest.main()
