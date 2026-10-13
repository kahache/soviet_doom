"""Tests for the menu font SDMENU (tools/art/gen_menu.py; D22 built for D31).

  the map        the D22 substitution is exactly level 2 - R->Я, N->И, E->Э,
                 W->Ш, A->Д - and nothing else
  the install    assets/fonts/sdmenu/ is assets/fonts/bigfont/ with exactly
                 five files changed, each one byte-identical to the installed
                 Cyrillic glyph it borrows; every other file, Cyrillic
                 included, is identical byte for byte
  the build      gen_menu.build_font() reproduces assets/fonts/sdmenu/ byte
                 for byte (needs Pillow/numpy and the label fonts gen_font
                 opens at import; skipped without them)

Nothing is written to work/ or assets/: the build goes to a temp directory.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_menu -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

import gen_menu  # noqa: E402  (stdlib-only at import time)

BIGFONT = PROJECT_ROOT / "assets" / "fonts" / "bigfont"
SDMENU = PROJECT_ROOT / "assets" / "fonts" / "sdmenu"

# Written out here, not imported, so the test pins the decision (D22 level 2)
# rather than whatever the module happens to say.
D22_LEVEL_2 = {"R": "Я", "N": "И", "E": "Э", "W": "Ш", "A": "Д"}
CHANGED_FILES = {"0052.png": "042F.png", "004E.png": "0418.png", "0045.png": "042D.png",
                 "0057.png": "0428.png", "0041.png": "0414.png"}

try:
    import numpy  # noqa: F401
    from PIL import Image  # noqa: F401
    import artlib
    HAVE_BUILD = artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_BUILD = False


class SubstitutionMapTests(unittest.TestCase):
    def test_map_is_exactly_d22_level_2(self):
        self.assertEqual(gen_menu.SUBSTITUTION, D22_LEVEL_2)

    def test_reads_as_matches_the_documented_examples(self):
        # docs/product/LANGUAGE-SWITCH.md: ZARYA-7 renders as ZДЯYД-7 at level 2
        # (Z and Y are not in the map); digits and punctuation pass through.
        self.assertEqual(gen_menu.reads_as("ZARYA-7"), "ZДЯYД-7")
        self.assertEqual(gen_menu.reads_as("New Game"), "ИЭШ GДMЭ")
        self.assertEqual(gen_menu.reads_as("Options"), "OPTIOИS")
        self.assertEqual(gen_menu.reads_as("Новая игра"), "НОВАЯ ИГРА")

    def test_no_other_latin_letter_is_touched(self):
        others = "".join(c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in D22_LEVEL_2)
        self.assertEqual(gen_menu.reads_as(others), others)


class InstalledFontTests(unittest.TestCase):
    def test_same_files_as_bigfont(self):
        self.assertTrue(SDMENU.is_dir(), "assets/fonts/sdmenu/ is not installed")
        self.assertEqual(sorted(p.name for p in SDMENU.iterdir()),
                         sorted(p.name for p in BIGFONT.iterdir()))

    def test_only_the_five_d22_glyphs_differ(self):
        differ = sorted(p.name for p in SDMENU.iterdir()
                        if p.read_bytes() != (BIGFONT / p.name).read_bytes())
        self.assertEqual(differ, sorted(CHANGED_FILES))

    def test_each_changed_glyph_is_the_installed_cyrillic_one(self):
        for latin_file, cyr_file in CHANGED_FILES.items():
            with self.subTest(glyph=latin_file):
                self.assertEqual((SDMENU / latin_file).read_bytes(),
                                 (BIGFONT / cyr_file).read_bytes())

    def test_changed_files_follow_the_map(self):
        derived = {gen_menu.glyph_file(l): gen_menu.glyph_file(c)
                   for l, c in gen_menu.SUBSTITUTION.items()}
        self.assertEqual(derived, CHANGED_FILES)


@unittest.skipUnless(HAVE_BUILD, "Pillow/numpy or the label fonts gen_font opens are not available")
class BuildReproducesInstallTests(unittest.TestCase):
    def test_build_font_equals_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sdmenu"
            report = gen_menu.build_font(out)
            self.assertEqual(len(report["replaced"]), 5)
            for p in SDMENU.iterdir():
                with self.subTest(file=p.name):
                    self.assertEqual((out / p.name).read_bytes(), p.read_bytes())
            self.assertEqual(sorted(q.name for q in out.iterdir()),
                             sorted(q.name for q in SDMENU.iterdir()))


if __name__ == "__main__":
    unittest.main()
