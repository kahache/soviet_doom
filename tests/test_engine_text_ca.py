"""D119: the engine's own in-game lines in Catalan.

The CEO's playtest of Episodes 2 and 3 (2026-10-23): "'A secret is
revealed' is not translated into Catalan". GZDoom g4.14.2 ships no Catalan,
so with `language ca` every string of the engine's own (the secret line,
saving and loading, the Y/N confirmations, the stats screen, the deaths with
no enemy) fell back to English. src/lumps/LANGUAGE now gives each one a
[ca] line.

What is pinned, without starting GZDoom (D26):

* every id in ENGINE_IDS has a [ca] line that is not the English, keeps the
  engine's %s / %o / %k placeholders and uses only characters the mod's
  fonts draw;
* those ids are defined ONLY in [ca]: English and Russian come from the
  engine (its language.csv has both), and a [default] line of ours would
  replace the engine's other translations too;
* none of them is rewritten by Freedoom's DEHACKED (a DEHACKED string beats
  every LANGUAGE section, ADR 003), when the IWAD is present;
* the engine really defines each id, with a Russian translation, when an
  installed gzdoom.pk3 is found (skipped at `verify.py fast`, which reads no
  engine file: tests/_tiers.py's rule).
"""

from __future__ import annotations

import csv
import io
import os
import re
import struct
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from test_language import parse_language  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
FONTS = (PROJECT_ROOT / "assets" / "fonts" / "defsmallfont",
         PROJECT_ROOT / "assets" / "fonts" / "bigfont")

# Engine id -> the engine's English (gzdoom.pk3 g4.14.2 language.csv), the
# reference for the placeholders and for "not a copy". Every id here is one
# a player of our campaign can see.
ENGINE_IDS = {
    # the secret sector's line (the CEO's report)
    "SECRETMESSAGE": "A secret is revealed!",
    # saving and loading
    "GGSAVED": "Game saved.",
    "TXT_SAVEFAILED": "Save failed",
    "QSPROMPT": "Quicksave over your game named\n\n'%s'?\n\nPress Y or N.",
    "QLPROMPT": "Do you want to quickload the game named\n\n'%s'?\n\nPress Y or N.",
    "QSAVESPOT": "You haven't picked a quicksave slot yet!\n\nPress a key.",
    "SAVEDEAD": "You can't save if you aren't playing!\n\nPress a key.",
    "NEWSAVE": "<New Save Game>",
    "MNU_LOADGAME": "Load Game",
    "MNU_SAVEGAME": "Save Game",
    "MNU_NOFILES": "No files",
    "MNU_NOPICTURE": "No Picture",
    "MNU_DIFFVERSION": "Different Version",
    "MNU_DELETESG": "Do you really want to delete the savegame?\n",
    # confirmations and toggles
    "ENDGAME": "Are you sure you want to end the game?\n\nPress Y or N.",
    "PRESSYN": "Press Y or N.",
    "PRESSKEY": "Press a key.",
    "TXT_YES": "Yes",
    "TXT_NO": "No",
    "MSGON": "Messages: ON",
    "MSGOFF": "Messages: OFF",
    # the stats screen between maps
    "WI_FINISHED": "Finished",
    "WI_ENTERING": "Entering",
    "TXT_IMKILLS": "Kills",
    "TXT_IMITEMS": "Items",
    "TXT_IMSECRETS": "Secrets",
    "TXT_IMTIME": "Time",
    "TXT_IMPAR": "Par",
    # the automap's level stats
    "AM_MONSTERS": "Monsters:",
    "AM_ITEMS": "Items:",
    "AM_SECRETS": "Secrets:",
    # deaths with no enemy (the own RPG-7, acid, a fall...)
    "OB_DEFAULT": "%o died.",
    "OB_KILLEDSELF": "%o killed %hself.",
    "OB_SUICIDE": "%o suicides.",
    "OB_FALLING": "%o fell too far.",
    "OB_CRUSH": "%o was squished.",
    "OB_SLIME": "%o mutated.",
    "OB_LAVA": "%o melted.",
    "OB_WATER": "%o can't swim.",
    "OB_EXIT": "%o tried to leave.",
    "OB_BARREL": "%o went boom.",
    "OB_MONTELEFRAG": "%o was telefragged.",
}
# Catalan words that are the English ones: "No" is "No"; "Secrets" is the
# Catalan plural of "secret" too.
SAME_IN_CATALAN = frozenset({"TXT_NO", "TXT_IMSECRETS", "AM_SECRETS"})
# What the engine fills in. %h (his/her) is left out: Catalan's reflexive
# needs no pronoun, as the engine's own Russian drops it.
PLACEHOLDER_RE = re.compile(r"%[oks]")
# The keys the engine's message box accepts are Y and N in every language.
YN_IDS = ("QSPROMPT", "QLPROMPT", "ENDGAME", "PRESSYN")


def unquote(value: str) -> str:
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', value)).replace("\\n", "\n")


def engine_pk3() -> Path | None:
    try:
        import smoke  # only its engine-locating helper; nothing is run
    except ImportError:
        return None
    return next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                 if (c.parent / "gzdoom.pk3").is_file()), None)


class CatalanEngineTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))
        cls.ca = {k: unquote(v) for k, v in cls.sections["ca"].items()}

    def test_every_engine_id_has_a_catalan_line(self):
        missing = sorted(set(ENGINE_IDS) - set(self.ca))
        self.assertEqual(missing, [], "[ca] lacks these engine ids")
        self.assertEqual(self.ca["SECRETMESSAGE"], "Has descobert un secret!")

    def test_the_lines_are_not_the_english(self):
        copied = [k for k in ENGINE_IDS if k not in SAME_IN_CATALAN and self.ca[k] == ENGINE_IDS[k]]
        self.assertEqual(copied, [])

    def test_placeholders_survive(self):
        for key, english in ENGINE_IDS.items():
            with self.subTest(key):
                self.assertEqual(sorted(PLACEHOLDER_RE.findall(self.ca[key])),
                                 sorted(PLACEHOLDER_RE.findall(english)))

    def test_the_confirmations_keep_the_y_and_n_keys(self):
        for key in YN_IDS:
            with self.subTest(key):
                self.assertIn("Prem Y o N.", self.ca[key])

    def test_the_line_breaks_are_the_engines(self):
        """A message box laid out like the engine's: same number of breaks."""
        for key, english in ENGINE_IDS.items():
            with self.subTest(key):
                self.assertEqual(self.ca[key].count("\n"), english.count("\n"))

    def test_only_in_catalan(self):
        """English and Russian are the engine's own; a [default] line of ours
        would also drop the engine's other translations of the id."""
        for code in ("default", "ru"):
            with self.subTest(code):
                self.assertEqual(sorted(set(ENGINE_IDS) & set(self.sections[code])), [])

    def test_every_character_is_drawn(self):
        """SmallFont and BigFont draw lower case with the capitals."""
        for font in FONTS:
            if not font.is_dir():
                self.skipTest(f"{font} not on disk")
            missing = sorted({f"{k}: {ch!r}" for k in ENGINE_IDS
                              for ch in set(self.ca[k].replace("\n", "").upper())
                              if not (font / f"{ord(ch):04X}.png").is_file()})
            self.assertEqual(missing, [], f"{font.name} cannot draw")

    def test_freedooms_dehacked_does_not_rewrite_them(self):
        if not IWAD.is_file():
            self.skipTest("no iwads/freedoom2.wad")
        data = IWAD.read_bytes()
        count, offset = struct.unpack("<4xii", data[:12])
        text = ""
        for i in range(count):
            pos, size, name = struct.unpack("<ii8s", data[offset + 16 * i:offset + 16 * i + 16])
            if name.rstrip(b"\0") == b"DEHACKED":
                text = data[pos:pos + size].decode("latin-1")
        self.assertTrue(text, "no DEHACKED lump in the IWAD")
        ids = set(re.findall(r"^([A-Z][A-Z0-9_]*)\s*=", text, re.M))
        self.assertEqual(sorted(ids & set(ENGINE_IDS)), [])
        self.assertNotRegex(text, r"(?m)^Text\s", "old-style DEHACKED text blocks")


@unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART") == "1",
                 "reads gzdoom.pk3: art and full tiers only (tests/_tiers.py)")
class EngineDefinesThemTest(unittest.TestCase):
    """The ids are the engine's, and [ru] needs nothing of ours."""

    @classmethod
    def setUpClass(cls) -> None:
        pk3 = engine_pk3()
        if pk3 is None:
            raise unittest.SkipTest("no installed gzdoom.pk3")
        cls.rows: dict[str, dict[str, str]] = {}
        with zipfile.ZipFile(pk3) as z:
            for name in z.namelist():
                if not re.fullmatch(r"language\.(csv|\d+)", name):
                    continue
                reader = csv.reader(io.StringIO(z.read(name).decode("utf-8", "replace")))
                header = next(reader)
                ru = header.index("ru")
                for row in reader:
                    if len(row) > ru and row[1] and not row[3]:   # no game filter
                        cls.rows.setdefault(row[1], {"en": row[0], "ru": row[ru]})

    def test_every_id_is_an_engine_id_with_english_and_russian(self):
        for key, english in ENGINE_IDS.items():
            with self.subTest(key):
                self.assertIn(key, self.rows)
                self.assertEqual(self.rows[key]["en"].replace("\r\n", "\n"), english)
                self.assertRegex(self.rows[key]["ru"], r"[Ѐ-ӿ]")


if __name__ == "__main__":
    unittest.main()
