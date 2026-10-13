"""Tests for the H1 slab-serif fix and the H3 newline fix in gen_font.py.

QA's tests/test_gen_font.py encodes the shipped state: style C rebuilt is
byte-identical to assets/fonts/, and M/W are symmetric (the H1 regression
test). This file is the art director's side of the same finding:

  the fix works   with gen_font.MIRROR_TERMINALS True, M, Cyrillic M and W
                  come out symmetric at both sizes, every glyph that is
                  meant to be symmetric still is, and nothing but those
                  three glyphs changes against the switch turned off
  the fix is on   the shipped value is True since the CEO approved the
                  proposal sheet (docs/art/previews/*_F2_font-C-serif-fix.png)
                  on 2026-10-13 and the six glyphs were installed
  the "before"    False still reproduces the historical render (M and W
                  asymmetric, W's floating foot), so the sheet's before
                  column and the diff below stay honest
  the install     build_serif_fix() is byte for byte what assets/fonts/
                  holds; the historical render differs from assets/fonts/
                  in exactly the six PNGs; the sheet is produced
  font.inf (H3)   written with LF on every machine, so this PC's bytes equal
                  the Mac's renders in work/art/font/C/

Rules: nothing is written to work/ or assets/ (every output goes to a
tempfile directory); the module switch is changed only through
mock.patch.object or gen_font.mirror_terminals, both of which restore it;
Pillow/numpy and the system label fonts are optional, the classes skip
without them.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_font_fix -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
MAC_FONT_C = PROJECT_ROOT / "work" / "art" / "font" / "C"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

try:
    import artlib as _artlib  # noqa: E402
    HAVE_FONTS = _artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_FONTS = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
fonts = unittest.skipUnless(HAVE_FONTS, "system fonts (Impact, Arial Narrow Bold) not present")

FOLDERS = {"defsmallfont": "small", "bigfont": "big"}
FIXED = ["M", "М", "W"]                       # Latin M, Cyrillic M, W
# Same list as tests/test_gen_font.py SYMMETRIC: drawn symmetric by design.
SYMMETRIC = list("AHMOTVWXYПЖШФ+-=_.:!'\"")
# The files the fix changes: the three glyphs at both sizes.
FIXED_FILES = {f"{folder}/{ord(c):04X}.png" for folder in FOLDERS for c in FIXED}


def ink_ascii(ink) -> str:
    return "\n".join("".join("#" if v else "." for v in row) for row in ink)


@imaging
@fonts
class MirrorTerminalsFixTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen

    def ink(self, ch, key, size_key):
        return self.gen.render_glyph(ch, self.gen.STYLES[key], size_key)[0]

    def test_shipped_value_is_on(self):
        """The CEO approved the fix on 2026-10-13 and its six glyphs are in
        assets/fonts/; turning it off again would change shipped pixels."""
        self.assertIs(self.gen.MIRROR_TERMINALS, True)

    def test_switch_off_still_draws_the_historical_defect(self):
        """False is the "before" of the sheet: M and W asymmetric at both
        sizes, and W's floating foot in the bottom-right corner."""
        with mock.patch.object(self.gen, "MIRROR_TERMINALS", False):
            for ch in FIXED:
                for size_key in FOLDERS.values():
                    ink = self.ink(ch, "C", size_key)
                    with self.subTest(ch=ch, size=size_key):
                        self.assertFalse((ink == ink[:, ::-1]).all(), "\n" + ink_ascii(ink))
            for size_key in FOLDERS.values():
                ink = self.ink("W", "C", size_key)
                with self.subTest(ch="W foot", size=size_key):
                    self.assertTrue(ink[-1, -1], "\n" + ink_ascii(ink))

    def test_m_and_w_are_symmetric_with_the_fix(self):
        with mock.patch.object(self.gen, "MIRROR_TERMINALS", True):
            for ch in FIXED:
                for size_key in FOLDERS.values():
                    ink = self.ink(ch, "C", size_key)
                    with self.subTest(ch=ch, size=size_key):
                        self.assertTrue((ink == ink[:, ::-1]).all(), "\n" + ink_ascii(ink))

    def test_w_has_two_top_slabs_and_no_floating_foot(self):
        """The defect itself, pixel by pixel: the top row of W carries a slab
        at both ends, and the bottom-right corner (where QA saw the stray
        foot) is empty."""
        with mock.patch.object(self.gen, "MIRROR_TERMINALS", True):
            for size_key in FOLDERS.values():
                ink = self.ink("W", "C", size_key)
                with self.subTest(size=size_key):
                    self.assertTrue(ink[0, 0] and ink[0, -1], "\n" + ink_ascii(ink))
                    self.assertFalse(ink[-1, -1], "\n" + ink_ascii(ink))

    def test_every_symmetric_glyph_stays_symmetric_in_every_style(self):
        with mock.patch.object(self.gen, "MIRROR_TERMINALS", True):
            for key in self.gen.STYLES:
                for size_key in FOLDERS.values():
                    for ch in SYMMETRIC:
                        ink = self.ink(ch, key, size_key)
                        with self.subTest(style=key, size=size_key, ch=ch):
                            self.assertTrue((ink == ink[:, ::-1]).all(), "\n" + ink_ascii(ink))

    def test_the_fix_reaches_exactly_m_cyrillic_m_and_w_in_style_c(self):
        changed = set()
        for key, st in self.gen.STYLES.items():
            for size_key in FOLDERS.values():
                for cp in self.gen.GLYPHS:
                    with mock.patch.object(self.gen, "MIRROR_TERMINALS", False):
                        a = self.gen.render_glyph(chr(cp), st, size_key)[0]
                    with mock.patch.object(self.gen, "MIRROR_TERMINALS", True):
                        b = self.gen.render_glyph(chr(cp), st, size_key)[0]
                    if a.shape != b.shape or not (a == b).all():
                        changed.add((key, size_key, chr(cp)))
        expected = {("C", s, c) for s in FOLDERS.values() for c in FIXED}
        self.assertEqual(changed, expected)

    def test_context_manager_restores_the_switch(self):
        before = self.gen.MIRROR_TERMINALS
        with self.gen.mirror_terminals(not before):
            self.assertIs(self.gen.MIRROR_TERMINALS, not before)
        self.assertIs(self.gen.MIRROR_TERMINALS, before)


@imaging
@fonts
class ProposalBuildTests(unittest.TestCase):
    """build_serif_fix() and sheet_serif_fix(), pointed at a tempdir (their
    defaults are work/art/font_fix/ and docs/art/previews/), plus the
    historical render (switch off) built next to them."""

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.report = gen.build_serif_fix(cls.tmp / "fix")
        # The historical render predates the German letters too (D37), so
        # both switches go back to their pre-2026-10-13 values.
        with gen.mirror_terminals(False), gen.german_umlauts(False):
            gen.build_variant(gen.STYLES["C"], cls.tmp / "before")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def differing_from_assets(self, root: Path) -> set:
        differing = set()
        for folder in FOLDERS:
            for p in sorted((root / folder).glob("*.png")):
                if p.read_bytes() != (FONTS_DIR / folder / p.name).read_bytes():
                    differing.add(f"{folder}/{p.name}")
        return differing

    def test_proposal_is_what_assets_holds(self):
        """Installed 2026-10-13: every PNG of the approved proposal is in
        assets/fonts/ byte for byte, the six fixed glyphs included."""
        root = self.tmp / "fix" / "C"
        for folder in FOLDERS:
            with self.subTest(folder=folder):
                self.assertEqual(sorted(p.name for p in (root / folder).glob("*.png")),
                                 sorted(p.name for p in (FONTS_DIR / folder).glob("*.png")))
        self.assertEqual(self.differing_from_assets(root), set())

    def test_historical_render_differs_from_assets_in_exactly_the_six_files(self):
        """What the install changed, and nothing else: the font as it
        shipped before the fix differs from assets/fonts/ in M, Cyrillic M
        and W at both sizes."""
        self.assertEqual(self.differing_from_assets(self.tmp / "before" / "C"), FIXED_FILES)

    @unittest.skipUnless(MAC_FONT_C.is_dir(), "work/art/font/C (the Mac's renders) not present")
    def test_historical_render_is_the_macs(self):
        """The switch turned off rebuilds the Mac's render of style C (the
        font as installed before 2026-10-13) byte for byte on this machine."""
        root = self.tmp / "before" / "C"
        for folder in FOLDERS:
            for p in sorted((root / folder).glob("*.png")):
                with self.subTest(file=f"{folder}/{p.name}"):
                    self.assertEqual(p.read_bytes(), (MAC_FONT_C / folder / p.name).read_bytes())

    def test_building_the_proposal_restores_the_switch(self):
        self.assertIs(self.gen.MIRROR_TERMINALS, True)

    def test_proposal_manifest_says_what_it_is(self):
        import json
        manifest = json.loads((self.tmp / "fix" / "manifest.json").read_text(encoding="utf-8"))
        self.assertIs(manifest["MIRROR_TERMINALS"], True)
        self.assertEqual([v["variant"] for v in manifest["variants"]], ["C"])

    def test_sheet_is_written_where_asked(self):
        path = self.gen.sheet_serif_fix("TEST", self.tmp / "sheet")
        self.assertEqual(path.name, "TEST_F2_font-C-serif-fix.png")
        self.assertEqual(path.parent.resolve(), (self.tmp / "sheet").resolve())
        self.assertTrue(path.is_file())
        self.assertIs(self.gen.MIRROR_TERMINALS, True)


@imaging
@fonts
class FontInfNewlineTests(unittest.TestCase):
    """H3: font.inf is LF on every machine."""

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name) / "C"
        gen.build_variant(gen.STYLES["C"], Path(cls._tmp.name))
        cls.gen = gen

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_font_inf_is_lf(self):
        for folder, size_key in FOLDERS.items():
            size = self.gen.STYLES["C"].small if size_key == "small" else self.gen.STYLES["C"].big
            with self.subTest(folder=folder):
                self.assertEqual((self.root / folder / "font.inf").read_bytes(),
                                 f"FontHeight {size.line}\n".encode("ascii"))

    @unittest.skipUnless(MAC_FONT_C.is_dir(), "work/art/font/C (the Mac's renders) not present")
    def test_font_inf_matches_the_macs_render_byte_for_byte(self):
        for folder in FOLDERS:
            with self.subTest(folder=folder):
                self.assertEqual((self.root / folder / "font.inf").read_bytes(),
                                 (MAC_FONT_C / folder / "font.inf").read_bytes())


if __name__ == "__main__":
    unittest.main()
