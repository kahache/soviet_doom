"""The in-game credits (G6): every attribution a licence obliges is on screen.

The screen is `OptionMenu "SD_CreditsMenu"` in MENUDEF, reached from the
mod's own options screen (Options -> Soviet Doom -> Credits); its text is the
`SD_CRED_*` ids of LANGUAGE, one id per screen line. The decision is
docs/engine/adr/009-in-game-credits.md, the contract docs/engine/MOD-SPEC.md
6.8.

What this suite pins, statically:

  * the screen exists, is reachable from our options screen, and is NOT on
    the CEO's approved text menus (D31/D32) - that is his call (ADR 009);
  * every SD_CRED_* id the menu names exists in both languages, and every
    one LANGUAGE defines is on the menu;
  * every line fits the row: an option-menu StaticText does not wrap;
  * Jerry Engelbach's credit is on screen WORD FOR WORD as
    docs/sound/MUSIC-RIGHTS.md 4.5 gives it;
  * every name a licence register obliges us to credit - read from the
    registers themselves, docs/art/LICENSES.md and MUSIC-RIGHTS 4.5 - is in
    the credits of BOTH languages. A new register row whose licence needs
    attribution turns this suite red until the credits carry the name.

What it cannot pin is what the engine draws (fit, colours, scrolling): the
PM's engine pass (D26).
"""

from __future__ import annotations

import re
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
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"

CREDITS_MENU = "SD_CreditsMenu"
OWN_OPTIONS_MENU = "SD_OptionsMenu"
CREDIT_PREFIX = "SD_CRED_"
TITLE_ID = "SD_CRED_TITLE"

# An option-menu StaticText row is one line in NewSmallFont, centred, never
# wrapped (gzdoom.pk3:zscript/engine/ui/menu/optionmenuitems.zs:56-66). The
# font is the engine's hex font, 8-px cells for Latin and Cyrillic alike, so
# 40 characters are about 360 clean pixels; the narrowest clean width we
# expect at common resolutions is about 400. Both numbers are NOT VERIFIED
# in the engine (ADR 009); the PM's engine pass checks the longest line.
MAX_CREDIT_LINE_CHARS = 40

# Credited whatever the registers say, and the licence each one is under.
# The team and its two licences (LICENSE.md, D15); the engine and the base
# game data, which the player needs and which we do not redistribute
# (docs/art/LICENSES.md "Base IWAD"; ADR 009 says why a credit anyway).
# Each entry is (what, English form, Russian form): the Russian credits keep
# the Latin proper names, so most forms are the same.
ALWAYS_CREDITED = (
    ("the team", "Soviet Doom", "Soviet Doom"),
    ("code licence", "GNU GPL 3.0", "GNU GPL 3.0"),
    ("asset licence", "CC BY-NC-SA 4.0", "CC BY-NC-SA 4.0"),
    ("engine", "GZDoom", "GZDoom"),
    ("engine licence", "GPL 3.0", "GPL 3.0"),
    ("base game data", "Freedoom", "Freedoom"),
    ("base game data licence", "BSD", "BSD"),
)

# --- Reading the licence registers -------------------------------------------

# A licence cell that obliges a credit (or, for CC0, the courtesy credit the
# project gives anyway: ADR 009, D-009-3). Our own rows (D15) are credited
# by the team line and are skipped before this is asked.
ATTRIBUTION_RE = re.compile(
    r"credit\b|\{\{Attribution|\bCC[ -]?BY\b|\bCC0\b|\bBSD\b|\bMIT\b|\bOFL\b",
    re.IGNORECASE)
OWN_WORK_RE = re.compile(r"\(D15\)|Soviet Doom project")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
QUOTED_CREDIT_RE = re.compile(r'credit\s+"([^"]+)"', re.IGNORECASE)


class RegisterError(ValueError):
    """A register row needs a credit but does not say whom to credit."""


def _cells(line: str) -> list[str]:
    return [c.strip() for c in CELL_SPLIT_RE.split(line.strip().strip("|"))]


def _tables(text: str):
    """Yield (header cells, [row cells...]) for every Markdown table."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and re.match(r"^\s*\|[\s|:-]+\|\s*$", lines[i + 1]):
            header = _cells(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            yield header, rows
            i = j
        else:
            i += 1


def _names_in_row(row: list[str], licence_cell: str) -> list[str]:
    """Whom a row obliges us to credit: `credit "X"` in the licence cell,
    else every bold span of the row that is a name, not a sentence."""
    quoted = QUOTED_CREDIT_RE.findall(licence_cell)
    if quoted:
        return quoted
    names = []
    for cell in row:
        for span in BOLD_RE.findall(cell):
            if not re.search(r"\b(credit|required|accepted|licen[cs]e)\b", span, re.I):
                names.append(span.strip())
    return names


def attribution_names_from_licences(text: str) -> list[str]:
    """Every name docs/art/LICENSES.md obliges the credits to carry.

    A row of any table with a Licence column counts when that cell matches
    ATTRIBUTION_RE and the row is not our own work. `idem` repeats the row
    above. A row that needs a credit and names nobody in bold (or as
    `credit "X"`) raises RegisterError: the register must say whom.
    """
    names: list[str] = []
    for header, rows in _tables(text):
        col = next((k for k, h in enumerate(header) if re.search(r"licen[cs]e", h, re.I)), None)
        if col is None:
            continue
        previous_needs = False
        previous_names: list[str] = []
        for row in rows:
            if col >= len(row):
                continue
            cell = row[col]
            if cell.lower().startswith("idem"):
                needs, row_names = previous_needs, (_names_in_row(row, cell) or previous_names)
            elif OWN_WORK_RE.search(cell):
                needs, row_names = False, []
            else:
                needs = bool(ATTRIBUTION_RE.search(cell))
                row_names = _names_in_row(row, cell) if needs else []
            if needs and not row_names:
                raise RegisterError(
                    f"register row needs a credit but names nobody in bold: {' | '.join(row)}")
            if needs:
                names.extend(n for n in row_names if n not in names)
            previous_needs, previous_names = needs, row_names
    return names


def _section(text: str, heading_re: str) -> str:
    match = re.search(heading_re + r"[^\n]*\n(.*?)(?=\n#{1,3} |\Z)", text, re.S | re.M)
    return match.group(1) if match else ""


def attribution_names_from_music_rights(text: str) -> list[str]:
    """Names in the Obligation column of MUSIC-RIGHTS 4.5 ("what ships")."""
    names: list[str] = []
    for header, rows in _tables(_section(text, r"^### 4\.5 ")):
        col = next((k for k, h in enumerate(header) if h.lower().startswith("obligation")), None)
        if col is None:
            continue
        for row in rows:
            cell = row[col].replace("*", "").strip()
            match = re.match(r"credit\s+(.+?)\s*$", cell, re.I)
            if match and match.group(1) not in names:
                names.append(match.group(1))
    return names


def verbatim_music_credit(text: str) -> str:
    """The credit line MUSIC-RIGHTS 4.5 says to reproduce verbatim, as plain
    text: the blockquote after "The credit line", Markdown emphasis and code
    marks dropped, whitespace collapsed."""
    section = _section(text, r"^### 4\.5 ")
    after = section.split("The credit line", 1)[1]
    quote = []
    for line in after.splitlines():
        if line.startswith(">"):
            quote.append(line.lstrip("> ").strip())
        elif quote:
            break
    return normalise(" ".join(quote).replace("*", "").replace("`", ""))


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def missing_from(credits: str, names) -> list[str]:
    return [n for n in names if n not in credits]


# --- Reading the screen ---------------------------------------------------------

def _menudef_code() -> str:
    raw = MENUDEF.read_text(encoding="utf-8")
    return "\n".join(strip_comment(line) for line in raw.splitlines())


def _block(code: str, kind: str, name: str) -> str | None:
    match = re.search(kind + r'\s+"' + re.escape(name) + r'"\s*\{(.*?)\n\}', code, re.S)
    return match.group(1) if match else None


def credit_ids(code: str) -> list[str]:
    """The SD_CRED_* ids the credits menu prints, in screen order (title
    excluded)."""
    body = _block(code, "OptionMenu", CREDITS_MENU) or ""
    return re.findall(r'^\s*StaticText\s+"\$(' + CREDIT_PREFIX + r'\w+)"', body, re.M)


def unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value


def credits_text(sections, code: str, lang: str) -> str:
    """What a player reads, top to bottom, as one string."""
    table = sections[lang]
    return normalise(" ".join(unquote(table.get(i, "")) for i in credit_ids(code)))


class CreditsScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code = _menudef_code()
        cls.sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))
        cls.ids = credit_ids(cls.code)

    def test_the_screen_exists_with_a_localized_title(self):
        body = _block(self.code, "OptionMenu", CREDITS_MENU)
        self.assertIsNotNone(body, f'MENUDEF has no OptionMenu "{CREDITS_MENU}"')
        self.assertRegex(body, r'Title\s+"\$' + TITLE_ID + '"')
        self.assertGreater(len(self.ids), 0, "the credits menu prints nothing")

    def test_it_is_reached_from_our_own_options_screen(self):
        body = _block(self.code, "OptionMenu", OWN_OPTIONS_MENU) or ""
        self.assertRegex(body, r'Submenu\s+"\$' + TITLE_ID + r'"\s*,\s*"' + CREDITS_MENU + '"',
                         f"{OWN_OPTIONS_MENU} has no Submenu row to the credits")

    def test_the_approved_text_menus_are_untouched(self):
        """D31/D32: the main, skill and episode screens are the CEO's approved
        look. Linking the credits from one of them is his decision (ADR 009,
        option C); until he takes it, no list menu points at the credits."""
        for name in ("MainMenu", "SkillMenu", "EpisodeMenu"):
            body = _block(self.code, "LISTMENU", name) or ""
            self.assertNotIn(CREDITS_MENU, body, f"{name} links the credits: ask the CEO first")
            self.assertNotIn(CREDIT_PREFIX, body, f"{name} prints a credits string: ask the CEO first")

    def test_every_line_exists_in_both_languages(self):
        for lang in REQUIRED_SECTIONS:
            missing = [i for i in [TITLE_ID, *self.ids] if i not in self.sections[lang]]
            self.assertEqual(missing, [], f"[{lang}] lacks credits ids")

    def test_no_credit_string_is_left_off_the_screen(self):
        defined = {k for k in self.sections["default"] if k.startswith(CREDIT_PREFIX)}
        on_screen = set(self.ids) | {TITLE_ID}
        self.assertEqual(sorted(defined - on_screen), [],
                         "LANGUAGE defines credits lines the menu never prints")
        self.assertEqual(len(self.ids), len(set(self.ids)), "a credits line is printed twice")

    def test_every_line_fits_one_row(self):
        too_long = [
            f"[{lang}] {i} ({len(unquote(self.sections[lang][i]))}): {unquote(self.sections[lang][i])}"
            for lang in REQUIRED_SECTIONS
            for i in [TITLE_ID, *self.ids]
            if len(unquote(self.sections[lang].get(i, ""))) > MAX_CREDIT_LINE_CHARS
            or "\\n" in self.sections[lang].get(i, "")
        ]
        self.assertEqual(too_long, [],
                         f"credits lines over {MAX_CREDIT_LINE_CHARS} characters or with a "
                         "line break; an option-menu row does not wrap - split the id")


class AttributionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        code = _menudef_code()
        sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))
        cls.credits = {lang: credits_text(sections, code, lang) for lang in REQUIRED_SECTIONS}
        cls.licences = LICENSES.read_text(encoding="utf-8")
        cls.music_rights = MUSIC_RIGHTS.read_text(encoding="utf-8")

    def test_engelbach_line_is_on_screen_word_for_word(self):
        """MUSIC-RIGHTS 4.5: "to be reproduced verbatim wherever the mod
        credits anyone". The English credits must contain it exactly."""
        line = verbatim_music_credit(self.music_rights)
        self.assertIn("Jerry Engelbach", line, "could not read the credit line from MUSIC-RIGHTS 4.5")
        self.assertIn(line, self.credits["default"])

    def test_every_register_attribution_is_credited_in_both_languages(self):
        names = (attribution_names_from_licences(self.licences)
                 + attribution_names_from_music_rights(self.music_rights))
        for lang in REQUIRED_SECTIONS:
            self.assertEqual(
                missing_from(self.credits[lang], names), [],
                f"[{lang}] credits lack a name a licence register obliges us to credit; "
                "add SD_CRED_* lines (ADR 009)")

    def test_always_credited_parties_are_in_both_languages(self):
        for what, english, russian in ALWAYS_CREDITED:
            self.assertIn(english, self.credits["default"], f"English credits lack {what}")
            self.assertIn(russian, self.credits["ru"], f"Russian credits lack {what}")

    def test_the_registers_still_parse(self):
        """Guards the readers: if a heading or a column moves, the names
        found must not silently drop to none."""
        self.assertIn("Jerry Engelbach", attribution_names_from_licences(self.licences))
        self.assertIn("Jerry Engelbach", attribution_names_from_music_rights(self.music_rights))


class AttributionGuardTest(unittest.TestCase):
    """The tripwire works: a register row that needs a credit and is not in
    the credits is reported. Synthetic registers, the real credits."""

    @classmethod
    def setUpClass(cls) -> None:
        code = _menudef_code()
        sections = parse_language(LANGUAGE_LUMP.read_text(encoding="utf-8"))
        cls.credits = credits_text(sections, code, "default")

    REGISTER = (
        "## Third-party packs\n\n"
        "| Lump | What it is | Origin | Licence |\n"
        "|---|---|---|---|\n"
        "| `SDOWN1` | ours | (a) generator | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |\n"
        "| `OTEXW1` | wall | OTEX 1.1 by **Ola Bjorling (ukiro)** | non-commercial, credit \"Ola Bjorling (ukiro)\" required |\n"
        "| `OTEXW2` | wall | idem | idem |\n"
        "| `D_RADIO` | radio | sequenced by **Anna Example** | `{{self\\|Cc-zero}}` - CC0 |\n"
        "| `D_PDPIECE` | piano | Mutopia | Public Domain |\n"
    )

    def test_a_new_attribution_row_is_reported_missing(self):
        names = attribution_names_from_licences(self.REGISTER)
        self.assertEqual(names, ["Ola Bjorling (ukiro)", "Anna Example"])
        self.assertEqual(missing_from(self.credits, names), names)

    def test_a_row_that_names_nobody_is_an_error(self):
        register = ("| Lump | Origin | Licence |\n|---|---|---|\n"
                    "| `SDX` | a pack | CC BY 3.0 |\n")
        with self.assertRaises(RegisterError):
            attribution_names_from_licences(register)

    def test_a_new_music_obligation_is_reported_missing(self):
        rights = ("### 4.5 What ships\n\n"
                  "| Lump | Cue | Obligation |\n|---|---|---|\n"
                  "| `D_SDBALD` | alien areas | **credit Robert Clausecker / Mutopia Project** |\n"
                  "| `D_SDM01` | MAP01 | none; ours |\n"
                  "\n## 5. Next\n")
        names = attribution_names_from_music_rights(rights)
        self.assertEqual(names, ["Robert Clausecker / Mutopia Project"])
        self.assertEqual(missing_from(self.credits, names), names)


if __name__ == "__main__":
    unittest.main()
