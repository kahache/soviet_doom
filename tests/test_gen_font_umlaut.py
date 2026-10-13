"""Tests for the German letters of tools/art/gen_font.py (D36, F5 proposal).

D36 makes the Reich speak real German and the General shout "Vorwaerts".
The alphabet (D24, style C "Mashina", 214 glyphs) has no A-umlaut, O-umlaut,
U-umlaut or sharp s, so until now the screen spelled "VORWAERTS". The art
director drew them behind a switch that is OFF (gen_font.GERMAN_UMLAUTS),
the way MIRROR_TERMINALS was before its approval; nothing is installed.
What is enforced here, and why:

  untouched     with the switch off (the shipped state) the 214 glyphs of
                every style are what they were: C rebuilt is byte-identical
                to assets/fonts/, and turning the German letters ON changes
                not one pixel of any existing glyph. This is the contract
                that lets the proposal exist without a CEO decision first
  exist         U+00C4, U+00D6, U+00DC, U+1E9E and U+00DF are drawn at both
                sizes, in all three styles, only inside the switch
  metrics       exactly the cap height, the dots touch the cap line, the
                letter touches the baseline and sits on the baseline of its
                base capital, the spacing column stays empty
  dots          two stem-sized dots, a blank row between them and the
                letter (they cannot touch the letter or leave the cap box),
                symmetric about the axis; the letter under them is the base
                capital drawn in the shorter box
  palette       only docs/art/palette.json colours, hard alpha, the small
                font flat and the big font with its drop shadow
  output        build_german() writes the ten files and the SDMENU copies
                where it is told, ss and sharp-s identical; the SDMENU
                generator carries them over unchanged once bigfont has them
  engine fold   RenderFont no longer chokes on "ss" (Python's own
                "\\u00df".upper() is "SS")

Rules this file follows (same as tests/test_gen_font.py):
  - nothing is written to work/, assets/ or docs/: every output goes to a
    tempfile directory (OUT_ROOT_UMLAUT and PREVIEW_DIR are passed or
    patched).
  - the module switch is turned on only through gen_font.german_umlauts(),
    which restores it, and every test that does so checks it came back.
  - Pillow/numpy and the system label fonts are optional: the classes skip.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_font_umlaut -v
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
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
A_UMLAUT, O_UMLAUT, U_UMLAUT = "Ä", "Ö", "Ü"
ESZETT_CAPITAL, ESZETT_SMALL = "ẞ", "ß"
UMLAUTS = {A_UMLAUT: "A", O_UMLAUT: "O", U_UMLAUT: "U"}
NEW = [A_UMLAUT, O_UMLAUT, U_UMLAUT, ESZETT_CAPITAL, ESZETT_SMALL]
NEW_FILES = ["00C4.png", "00D6.png", "00DC.png", "1E9E.png", "00DF.png"]
EXISTING_CODEPOINTS = 107                     # 214 PNG per style = 107 x 2 sizes


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def ink_ascii(ink) -> str:
    return "\n".join("".join("#" if v else "." for v in row) for row in ink)


def png_arrays(path_or_bytes) -> "np.ndarray":
    src = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes
    with Image.open(src) as img:
        return np.asarray(img.convert("RGBA"))


class GermanOn:
    """Mixin: the German letters on for the length of one test, and a check
    in cleanup that the module state came back."""

    def switch_on(self):
        gen = self.gen
        before = (len(gen.GLYPHS), list(gen.PUNCT))
        ctx = gen.german_umlauts(True)
        ctx.__enter__()

        def restore():
            ctx.__exit__(None, None, None)
            self.assertEqual((len(gen.GLYPHS), gen.PUNCT), before, "the switch did not restore the module")
        self.addCleanup(restore)


# ===========================================================================
# the 214 shipped glyphs do not move
# ===========================================================================
@imaging
@fonts
class ShippedGlyphsAreUntouchedTests(GermanOn, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_switch_is_off_and_the_default_set_is_the_214(self):
        gen = self.gen
        self.assertIs(gen.GERMAN_UMLAUTS, False, "turning it on is the CEO's call, with an install")
        self.assertEqual(len(gen.GLYPHS), EXISTING_CODEPOINTS)
        for ch in NEW:
            self.assertNotIn(ord(ch), gen.GLYPHS, f"U+{ord(ch):04X} leaked into the default set")
            self.assertNotIn(ch, gen.PUNCT)
        order = gen.CYRILLIC + gen.LATIN + gen.DIGITS + gen.PUNCT + [" "]
        self.assertEqual({ord(c) for c in order}, set(gen.GLYPHS))

    def test_style_c_default_build_is_byte_identical_to_assets(self):
        """The existing reproduction test, restated for this proposal: the
        German section must not move a pixel of what is installed."""
        report = self.gen.build_variant(self.gen.STYLES["C"], self.tmp / "default")
        built = self.tmp / "default" / "C"
        differing = []
        for folder in FOLDERS:
            pngs = sorted((FONTS_DIR / folder).glob("*.png"))
            self.assertTrue(pngs, f"assets/fonts/{folder} is empty")
            for p in pngs:
                if p.name in NEW_FILES:        # installed later, checked below
                    continue
                if p.read_bytes() != (built / folder / p.name).read_bytes():
                    differing.append(f"{folder}/{p.name}")
        self.assertEqual(differing, [])
        self.assertEqual(sum(len(r["widths"]) for r in report["sizes"].values()), 2 * EXISTING_CODEPOINTS)

    def test_switch_on_changes_no_existing_glyph_in_any_style(self):
        gen = self.gen
        old = list(gen.GLYPHS)
        off = {}
        for key, st in gen.STYLES.items():
            for size_key in FOLDERS.values():
                for cp in old:
                    off[(key, size_key, cp)] = np.asarray(gen.glyph_image(chr(cp), st, size_key)).copy()
        self.switch_on()
        changed = []
        for (key, size_key, cp), before in off.items():
            after = np.asarray(gen.glyph_image(chr(cp), gen.STYLES[key], size_key))
            if before.shape != after.shape or not (before == after).all():
                changed.append(f"{key} {size_key} U+{cp:04X}")
        self.assertEqual(changed, [], "the German section moved an existing glyph")

    def test_build_variant_with_the_switch_on_only_adds_the_ten_files(self):
        gen = self.gen
        gen.build_variant(gen.STYLES["C"], self.tmp / "off")
        self.switch_on()
        gen.build_variant(gen.STYLES["C"], self.tmp / "on")
        off = {p.relative_to(self.tmp / "off").as_posix(): p.read_bytes()
               for p in (self.tmp / "off").rglob("*") if p.is_file()}
        on = {p.relative_to(self.tmp / "on").as_posix(): p.read_bytes()
              for p in (self.tmp / "on").rglob("*") if p.is_file()}
        added = sorted(set(on) - set(off))
        self.assertEqual(added, sorted(f"C/{folder}/{name}" for folder in FOLDERS for name in NEW_FILES))
        self.assertEqual(set(off) - set(on), set())
        self.assertEqual([k for k in off if off[k] != on[k]], [])

    def test_the_switch_restores_state_even_when_the_block_fails(self):
        gen = self.gen
        before = (len(gen.GLYPHS), list(gen.PUNCT))
        with self.assertRaises(RuntimeError):
            with gen.german_umlauts(True):
                self.assertEqual(len(gen.GLYPHS), EXISTING_CODEPOINTS + len(NEW))
                raise RuntimeError("boom")
        self.assertEqual((len(gen.GLYPHS), gen.PUNCT), before)

    def test_installed_german_files_must_equal_the_generated_ones(self):
        """Vacuous today (nothing is installed). Once the CEO approves and
        the files land in assets/fonts/, they must be what the generator
        draws, or the next regeneration silently changes them."""
        gen = self.gen
        self.switch_on()
        for folder, size_key in FOLDERS.items():
            for ch in NEW:
                p = FONTS_DIR / folder / f"{ord(ch):04X}.png"
                if not p.is_file():
                    continue
                buf = io.BytesIO()
                gen.glyph_image(ch, gen.STYLES["C"], size_key).save(buf, "PNG")
                with self.subTest(folder=folder, ch=ch):
                    self.assertEqual(p.read_bytes(), buf.getvalue())


# ===========================================================================
# the new glyphs: metrics, dots, palette
# ===========================================================================
@imaging
@fonts
class GermanGlyphTests(GermanOn, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen

    def setUp(self):
        self.switch_on()

    def size(self, style, size_key):
        return style.small if size_key == "small" else style.big

    def every(self):
        for key, st in self.gen.STYLES.items():
            for size_key in FOLDERS.values():
                for ch in NEW:
                    yield key, st, size_key, ch

    def test_all_five_are_drawn_at_both_sizes_in_every_style(self):
        self.assertTrue(all(ord(ch) in self.gen.GLYPHS for ch in NEW))
        for key, st, size_key, ch in self.every():
            ink, advance = self.gen.render_glyph(ch, st, size_key)
            with self.subTest(style=key, size=size_key, ch=ch):
                self.assertTrue(ink.any())
                self.assertEqual(advance, ink.shape[1] + self.size(st, size_key).bearing)

    def test_height_is_the_cap_height_and_both_lines_are_touched(self):
        for key, st, size_key, ch in self.every():
            size = self.size(st, size_key)
            ink, _ = self.gen.render_glyph(ch, st, size_key)
            img = self.gen.glyph_image(ch, st, size_key)
            with self.subTest(style=key, size=size_key, ch=ch):
                self.assertEqual(ink.shape[0], size.cap)
                self.assertEqual(img.height, size.cap + size.shadow)
                self.assertLessEqual(img.height, size.line)
                self.assertTrue(ink[0].any(), "touches no cap line\n" + ink_ascii(ink))
                self.assertTrue(ink[-1].any(), "touches no baseline\n" + ink_ascii(ink))

    def test_spacing_column_is_empty(self):
        for key, st, size_key, ch in self.every():
            size = self.size(st, size_key)
            arr = np.asarray(self.gen.glyph_image(ch, st, size_key))
            with self.subTest(style=key, size=size_key, ch=ch):
                self.assertFalse(arr[:, -1, 3].any())
                self.assertEqual(arr.shape[1], self.gen.render_glyph(ch, st, size_key)[1] + size.shadow)

    def test_umlaut_dots_fit_the_cap_box_and_never_touch_the_letter(self):
        gen = self.gen
        for key, st in gen.STYLES.items():
            for size_key in FOLDERS.values():
                size = self.size(st, size_key)
                dot = size.stem
                for ch in UMLAUTS:
                    ink, _ = gen.render_glyph(ch, st, size_key)
                    top = ink[:dot]
                    cols = np.nonzero(top.any(axis=0))[0]
                    runs = np.split(cols, np.nonzero(np.diff(cols) > 1)[0] + 1)
                    with self.subTest(style=key, size=size_key, ch=ch):
                        self.assertEqual(len(runs), 2, "\n" + ink_ascii(ink))
                        for run in runs:
                            self.assertEqual(len(run), dot, "a dot is stem x stem")
                            self.assertTrue(top[:, run].all())
                        self.assertEqual(int(top.sum()), 2 * dot * dot)
                        self.assertFalse(ink[dot:dot + gen.UMLAUT_GAP].any(),
                                         "dots touch the letter\n" + ink_ascii(ink))
                        self.assertTrue(ink[dot + gen.UMLAUT_GAP].any(), "the letter starts after the gap")
                        self.assertEqual(ink.shape[0], size.cap, "dots stay inside the cap box")

    def test_umlaut_body_is_the_base_capital_on_its_baseline(self):
        gen = self.gen
        for key, st in gen.STYLES.items():
            for size_key in FOLDERS.values():
                size = self.size(st, size_key)
                body_rows = size.cap - size.stem - gen.UMLAUT_GAP
                for ch, base in UMLAUTS.items():
                    cls, fn, center = gen.GLYPHS[ord(base)]
                    w = gen.ink_width(st, size_key, cls, center)
                    pen = gen.Pen(w, dataclasses.replace(size, cap=body_rows), st)
                    fn(pen)
                    expected = pen.finish()
                    ink, _ = gen.render_glyph(ch, st, size_key)
                    plain, _ = gen.render_glyph(base, st, size_key)
                    with self.subTest(style=key, size=size_key, ch=ch):
                        self.assertEqual(ink.shape[1], plain.shape[1], "same width as its base")
                        self.assertTrue((ink[-body_rows:] == expected).all(), "\n" + ink_ascii(ink))
                        self.assertTrue(ink[-1].any())
                        if key == "C":
                            # square corners, no diagonals: the foot is the base letter's.
                            # (A and B re-raster their diagonals in the shorter box.)
                            self.assertTrue((ink[-1] == plain[-1]).all(),
                                            "baseline differs from the base letter")

    def test_umlaut_letters_are_symmetric_and_distinct(self):
        gen = self.gen
        seen = {}
        for key, st in gen.STYLES.items():
            for size_key in FOLDERS.values():
                for ch in UMLAUTS:
                    ink, _ = gen.render_glyph(ch, st, size_key)
                    with self.subTest(style=key, size=size_key, ch=ch):
                        self.assertTrue((ink == ink[:, ::-1]).all(), "\n" + ink_ascii(ink))
                    seen.setdefault((key, size_key), []).append(ink.tobytes())
        for pair, shapes in seen.items():
            with self.subTest(pair=pair):
                self.assertEqual(len(set(shapes)), 3)

    def test_sharp_s_is_not_a_b_and_both_codepoints_are_one_drawing(self):
        gen = self.gen
        for key, st in gen.STYLES.items():
            for size_key in FOLDERS.values():
                cap = gen.render_glyph(ESZETT_CAPITAL, st, size_key)[0]
                small = gen.render_glyph(ESZETT_SMALL, st, size_key)[0]
                b = gen.render_glyph("B", st, size_key)[0]
                with self.subTest(style=key, size=size_key):
                    self.assertTrue((cap == small).all())
                    self.assertEqual(cap.shape, b.shape)
                    self.assertFalse((cap == b).all(), "the sharp s must not be a B\n" + ink_ascii(cap))
                    self.assertFalse((cap == cap[:, ::-1]).all(), "a sharp s is not symmetric")

    def test_only_palette_colours_and_hard_alpha(self):
        palette = palette_colours()
        for key, st, size_key, ch in self.every():
            rgba = np.asarray(self.gen.glyph_image(ch, st, size_key))
            used = {tuple(int(v) for v in c) for c in rgba[rgba[..., 3] == 255][:, :3]}
            with self.subTest(style=key, size=size_key, ch=ch):
                self.assertLessEqual(set(np.unique(rgba[..., 3]).tolist()), {0, 255})
                self.assertLessEqual(used, palette)

    def test_small_font_is_flat_and_big_font_has_the_down_right_shadow(self):
        gen = self.gen
        st = gen.STYLES["C"]
        body_s, body_b, shadow = gen.colours(st)
        for ch in NEW:
            small = np.asarray(gen.glyph_image(ch, st, "small"))
            opaque = small[small[..., 3] == 255][:, :3]
            rgba = np.asarray(gen.glyph_image(ch, st, "big"))
            rgb = rgba[..., :3]
            is_body = (rgba[..., 3] == 255) & (rgb == body_b).all(-1)
            is_shadow = (rgba[..., 3] == 255) & (rgb == shadow).all(-1)
            with self.subTest(ch=ch):
                self.assertTrue((opaque == body_s).all())
                self.assertEqual(int(((rgba[..., 3] == 255) & ~is_body & ~is_shadow).sum()), 0)
                ys, xs = np.nonzero(is_shadow)
                self.assertTrue(is_shadow.any())
                self.assertTrue(all(is_body[y - 1, x - 1] for y, x in zip(ys, xs)))

    def test_yo_is_the_precedent_and_is_not_redrawn(self):
        """Ё (U+0401) is shipped with its dots on the letter; the new
        letters do not touch it."""
        gen = self.gen
        st = gen.STYLES["C"]
        shipped = {}
        for size_key, folder in (("small", "defsmallfont"), ("big", "bigfont")):
            shipped[size_key] = (FONTS_DIR / folder / "0401.png")
        for size_key, path in shipped.items():
            if not path.is_file():
                self.skipTest("assets/fonts not present")
            arr = np.asarray(gen.glyph_image("Ё", st, size_key))
            self.assertTrue((arr == png_arrays(path)).all(), f"Ё {size_key} moved")


# ===========================================================================
# what the proposal writes, and the SDMENU generator
# ===========================================================================
@imaging
@fonts
class GermanOutputTests(GermanOn, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.report = gen.build_german(cls.tmp / "umlaut")
        cls.root = cls.tmp / "umlaut"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_default_output_folder_is_work_not_assets(self):
        self.assertEqual(self.gen.OUT_ROOT_UMLAUT, PROJECT_ROOT / "work" / "art" / "font_umlaut")
        self.assertNotIn("assets", self.gen.OUT_ROOT_UMLAUT.relative_to(PROJECT_ROOT).parts)

    def test_build_german_writes_exactly_the_proposal_files(self):
        got = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file())
        want = sorted([f"C/{folder}/{n}" for folder in FOLDERS for n in NEW_FILES]
                      + [f"sdmenu/{n}" for n in NEW_FILES] + ["manifest.json"])
        self.assertEqual(got, want)
        self.assertEqual(set(self.report["files"]), {"fonts/defsmallfont/", "fonts/bigfont/", "fonts/sdmenu/"})
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest, self.report)
        self.assertIs(manifest["GERMAN_UMLAUTS"], False)

    def test_files_are_the_glyph_images_and_the_report_states_their_widths(self):
        gen = self.gen
        self.switch_on()
        st = gen.STYLES["C"]
        for folder, size_key in FOLDERS.items():
            for ch in NEW:
                p = self.root / "C" / folder / f"{ord(ch):04X}.png"
                with self.subTest(folder=folder, ch=ch):
                    arr = png_arrays(p)
                    self.assertTrue((arr == np.asarray(gen.glyph_image(ch, st, size_key))).all())
                    self.assertEqual(self.report["files"][f"fonts/{folder}/"][f"U+{ord(ch):04X}"], arr.shape[1])

    def test_sharp_s_files_are_byte_identical(self):
        for folder in FOLDERS:
            d = self.root / "C" / folder
            self.assertEqual((d / "1E9E.png").read_bytes(), (d / "00DF.png").read_bytes())

    def test_sdmenu_files_are_bigfonts(self):
        for name in NEW_FILES:
            self.assertEqual((self.root / "sdmenu" / name).read_bytes(),
                             (self.root / "C" / "bigfont" / name).read_bytes())

    def test_build_is_deterministic(self):
        again = self.tmp / "again"
        self.gen.build_german(again)
        a = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        b = {p.relative_to(again).as_posix(): p.read_bytes() for p in again.rglob("*") if p.is_file()}
        self.assertEqual(a, b)

    def test_gen_menu_carries_the_new_letters_over_and_keeps_its_five(self):
        """SDMENU is bigfont plus five Cyrillic redraws. Once bigfont holds
        the new files, regenerating SDMENU must copy them untouched (so its
        A-umlaut is bigfont's, a Latin A with dots) and still substitute
        R N E W A. gen_menu.py is not edited by this proposal."""
        big = FONTS_DIR / "bigfont"
        if not big.is_dir():
            self.skipTest("assets/fonts/bigfont not present")
        import gen_menu
        src = self.tmp / "bigfont_with_german"
        shutil.copytree(big, src)
        for name in NEW_FILES:
            shutil.copyfile(self.root / "C" / "bigfont" / name, src / name)
        out = self.tmp / "sdmenu_built"
        gen_menu.build_font(out_dir=out, source_dir=src)
        for name in NEW_FILES:
            with self.subTest(name=name):
                self.assertEqual((out / name).read_bytes(), (self.root / "sdmenu" / name).read_bytes())
        for latin, cyr in gen_menu.SUBSTITUTION.items():
            self.assertEqual((out / gen_menu.glyph_file(latin)).read_bytes(),
                             (src / gen_menu.glyph_file(cyr)).read_bytes())
        self.assertNotEqual((out / "0041.png").read_bytes(), (out / "00C4.png").read_bytes())

    def test_the_sheet_is_produced_where_told_and_leaves_the_switch_alone(self):
        gen = self.gen
        before = (len(gen.GLYPHS), list(gen.PUNCT))
        out = self.tmp / "previews"
        path = gen.sheet_german("TEST", out)
        self.assertEqual(path, out / "TEST_F5_font-german-umlauts.png")
        with Image.open(path) as sheet:
            self.assertEqual(sheet.width, 1500)
        self.assertEqual((len(gen.GLYPHS), gen.PUNCT), before)

    def test_cli_flag_builds_and_prints_the_sheet(self):
        gen = self.gen
        out, prev = self.tmp / "cli_font", self.tmp / "cli_prev"
        buf = io.StringIO()
        with mock.patch.object(gen, "OUT_ROOT_UMLAUT", out), mock.patch.object(gen, "PREVIEW_DIR", prev), \
                mock.patch.object(sys, "argv", ["gen_font.py", "--german-umlauts", "--stamp", "T"]), \
                contextlib.redirect_stdout(buf):
            gen.main()
        printed = [Path(line) for line in buf.getvalue().splitlines() if line.strip()]
        self.assertEqual([p.name for p in printed], ["T_F5_font-german-umlauts.png"])
        self.assertTrue(printed[0].is_file())
        self.assertTrue((out / "C" / "bigfont" / "00C4.png").is_file())


# ===========================================================================
# the words on screen
# ===========================================================================
@imaging
@fonts
class GermanTextTests(GermanOn, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen

    def test_vorwaerts_renders_with_no_missing_glyph_and_fits_a_doom_line(self):
        self.switch_on()
        for size_key in FOLDERS.values():
            f = self.gen.RenderFont(self.gen.STYLES["C"], size_key)
            for text in ("VORWÄRTS", "Vorwärts.", "THE GENERAL: VORWÄRTS!",
                         "GRÜSSE ÜBER STRAẞE, ÖL"):
                line = f.render(text)
                with self.subTest(size=size_key, text=text):
                    self.assertEqual(f.missing, set())
                    self.assertLessEqual(line.width, self.gen.SCREEN_W)
                    self.assertEqual(line.height, f.height)

    def test_lowercase_umlauts_and_the_sharp_s_fold_onto_the_capital_glyphs(self):
        self.switch_on()
        f = self.gen.RenderFont(self.gen.STYLES["C"], "small")
        self.assertEqual(f.width("äöü"), f.width("ÄÖÜ"))
        self.assertEqual(f.glyph(ESZETT_SMALL).tobytes(), f.glyph(ESZETT_CAPITAL).tobytes())
        self.assertEqual(f.missing, set())

    def test_with_the_switch_off_the_german_letters_are_missing_not_a_crash(self):
        """Today's state. Before the fix in RenderFont.glyph, the sharp s
        died in ord('SS'); now it is recorded as missing like any other
        character the font lacks, and the sheet says so."""
        f = self.gen.RenderFont(self.gen.STYLES["C"], "small")
        line = f.render("VORWÄRTS ß")
        self.assertEqual(f.missing, {A_UMLAUT, ESZETT_SMALL})
        self.assertEqual(line.width, f.width("VORWRTS "))


if __name__ == "__main__":
    unittest.main()
