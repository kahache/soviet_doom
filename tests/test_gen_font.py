"""Contract tests for tools/art/gen_font.py, the D24 alphabet.

The generator draws every glyph from stroke code (no system typeface), in
three styles; style C "Mashina" is the one installed in assets/fonts/
(docs/art/LICENSES.md, "The alphabet"). What is enforced here, and why:

  reproduction   style C regenerated on this machine is byte-identical to
                 assets/fonts/. Unlike the Impact-lettered textures
                 (CLAUDE.md), the glyphs use no system font, so the
                 installed font can be rebuilt on either machine; this test
                 is what makes that claim true rather than hoped for
  determinism    two builds give the same bytes, the precondition of the
                 line above
  coverage       every codepoint LICENSES.md promises, and every character
                 the LANGUAGE lump prints, has a glyph at both sizes, and
                 the installed folders hold exactly the generated set
  metrics        cap 7 / line 9 and cap 11 + 1 shadow / line 16, as
                 LICENSES.md states them; font.inf says the same
  palette        every opaque pixel of every installed glyph is a
                 docs/art/palette.json colour, alpha is hard 0/255
  drawing rules  the few Pen rules whose breakage is invisible at 1x but
                 shifts whole stems (half rounding, mirroring, spacing
                 column, the style switches)

Rules this file follows (same as tests/test_generators.py):
  - nothing is written to work/ or assets/: every output goes to a
    tempfile directory, and gen_font.OUT_ROOT is patched for the sheet and
    CLI paths, which otherwise write to work/art/font/ (the Mac's renders).
  - Pillow/numpy are optional (the CI interpreter has neither): the classes
    skip. gen_font loads the system label fonts at import time, so the
    classes that import it also skip without them.
  - no single test here takes 2 s (all three variants build in ~0.7 s), so
    nothing is marked with SD_SKIP_SLOW_ART.
  - QA finds, QA does not fix: the one real glyph defect found here (H1,
    the slab serifs of M and W) was encoded as an expected failure and
    reported to `art-director`; fixed and installed with the CEO's approval
    on 2026-10-13, it is now an ordinary regression test.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_font -v
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
LICENSES_MD = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
LANGUAGE_LUMP = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
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

# The style the CEO picked (LICENSES.md "The alphabet") and where each size
# is installed. Folder name -> size key of gen_font.
INSTALLED_STYLE = "C"
FOLDERS = {"defsmallfont": "small", "bigfont": "big"}

# What LICENSES.md promises, spelled out: "А-Я and Ё, A-Z, 0-9, and the
# punctuation the project uses including «» × · №, at both sizes".
PROMISED = (
    [chr(c) for c in range(0x0410, 0x0430)] + ["Ё"]
    + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [chr(c) for c in range(ord("0"), ord("9") + 1)]
    + list(".,:;!?-()%'\"") + ["«", "»", "×", "·", "№", " "]
)

# Glyphs drawn symmetric about the vertical axis (most of them by
# Pen.mirror()). Asymmetric by design and left out: У, the slashed 0 of
# style C, I (a 2 px stem in an odd box), and the big "*" diagonals.
SYMMETRIC = list("AHMOTVWXYПЖШФ+-=_.:!'\"")
# Exempted from the symmetry check in style C. Empty since 2026-10-13: the
# H1 serif fix (SlabSerifDefectTests) made M and W symmetric again.
SYMMETRIC_BROKEN_IN_C: list[str] = []


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def licenses_alphabet_rows() -> dict:
    """The two font rows of LICENSES.md, parsed: folder -> (count, cap,
    shadow, line). The test compares the generator against the document
    the licence audit reads, not against a copy of its numbers."""
    text = LICENSES_MD.read_text(encoding="utf-8")
    rows = {}
    for folder in FOLDERS:
        m = re.search(r"^\| `fonts/" + folder + r"/\*\.png` \((\d+)\) \|([^|]*)\|", text, re.M)
        if m is None:
            continue
        desc = m.group(2)
        cap = re.search(r"cap (\d+) px", desc)
        shadow = re.search(r"plus a (\d+) px shadow", desc)
        line = re.search(r"line (\d+)", desc)
        rows[folder] = (int(m.group(1)), int(cap.group(1)) if cap else None,
                        int(shadow.group(1)) if shadow else 0,
                        int(line.group(1)) if line else None)
    return rows


def language_strings() -> str:
    """Every quoted string value in the LANGUAGE lump, comments dropped and
    escapes reduced to their visible character (\\n prints nothing)."""
    out = []
    for raw in LANGUAGE_LUMP.read_text(encoding="utf-8").splitlines():
        line = raw.split("//", 1)[0] if raw.lstrip().startswith("//") else raw
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', line):
            out.append(re.sub(r"\\n", "", m.group(1)).replace('\\"', '"'))
    return "".join(out)


def ink_ascii(ink) -> str:
    return "\n".join("".join("#" if v else "." for v in row) for row in ink)


# ===========================================================================
# the glyph set: what is promised, what is drawn, what is installed
# ===========================================================================
@imaging
@fonts
class AlphabetCoverageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls.order = gen.CYRILLIC + gen.LATIN + gen.DIGITS + gen.PUNCT + [" "]

    def test_build_order_is_exactly_the_drawn_set(self):
        """build_variant() writes the build-order list, GLYPHS is what is
        drawn: a letter drawn but not listed never reaches the PK3, a letter
        listed twice would silently overwrite itself."""
        self.assertEqual(len(self.order), len(set(self.order)), "a codepoint is listed twice")
        self.assertEqual({ord(c) for c in self.order}, set(self.gen.GLYPHS))

    def test_every_promised_codepoint_is_drawn(self):
        missing = [f"U+{ord(c):04X} {c!r}" for c in PROMISED if ord(c) not in self.gen.GLYPHS]
        self.assertEqual(missing, [], "LICENSES.md promises these and gen_font.py draws none of them")

    def test_glyph_count_matches_licenses(self):
        rows = licenses_alphabet_rows()
        self.assertEqual(set(rows), set(FOLDERS), "LICENSES.md lost a font row")
        for folder, (count, *_rest) in rows.items():
            self.assertEqual(count, len(self.order), f"LICENSES.md says {folder} has {count} glyphs")

    def test_installed_folders_hold_exactly_the_generated_set(self):
        expected = {f"{ord(c):04X}.png" for c in self.order} | {"font.inf"}
        for folder in FOLDERS:
            with self.subTest(folder=folder):
                have = {p.name for p in (FONTS_DIR / folder).iterdir()}
                self.assertEqual(sorted(expected - have), [], f"assets/fonts/{folder}: glyphs missing")
                self.assertEqual(sorted(have - expected), [], f"assets/fonts/{folder}: files nobody generates")

    def test_every_character_the_language_lump_prints_has_a_glyph(self):
        """The font exists so LANGUAGE can be shown (D7, D24). A character
        a translator adds that the font lacks prints as nothing in game.
        Lowercase is checked as its capital: the font has capitals only and
        RenderFont.glyph() makes the same assumption about the engine
        (NOT VERIFIED here against GZDoom's FFont)."""
        chars = sorted({c.upper() for c in language_strings()})
        missing = [f"U+{ord(c):04X} {c!r}" for c in chars if ord(c) not in self.gen.GLYPHS]
        self.assertEqual(missing, [], "characters used in src/lumps/LANGUAGE with no glyph")

    def test_the_preview_phrases_need_no_missing_glyph(self):
        for size_key in FOLDERS.values():
            for key, style in self.gen.STYLES.items():
                font = self.gen.RenderFont(style, size_key)
                for _kind, _size, ru, en in self.gen.PHRASES:
                    font.render(ru)
                    font.render(en)
                with self.subTest(style=key, size=size_key):
                    self.assertEqual(font.missing, set())


# ===========================================================================
# metrics: cap height, shadow, line height, spacing
# ===========================================================================
@imaging
@fonts
class MetricsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls.style = gen.STYLES[INSTALLED_STYLE]
        cls.order = gen.CYRILLIC + gen.LATIN + gen.DIGITS + gen.PUNCT + [" "]

    def size(self, size_key):
        return self.style.small if size_key == "small" else self.style.big

    def test_style_metrics_match_licenses(self):
        for folder, (_count, cap, shadow, line) in licenses_alphabet_rows().items():
            size = self.size(FOLDERS[folder])
            with self.subTest(folder=folder):
                self.assertEqual((size.cap, size.shadow, size.line), (cap, shadow, line))

    def test_the_three_styles_share_the_metrics(self):
        """A, B and C differ in width and finish only; the CEO could swap
        styles without touching font.inf or any layout."""
        for key, st in self.gen.STYLES.items():
            for size_key in FOLDERS.values():
                a = st.small if size_key == "small" else st.big
                b = self.size(size_key)
                with self.subTest(style=key, size=size_key):
                    self.assertEqual((a.cap, a.shadow, a.line), (b.cap, b.shadow, b.line))

    def test_installed_glyph_heights(self):
        """Every installed PNG is cap + shadow tall, and that fits the line."""
        for folder, size_key in FOLDERS.items():
            size = self.size(size_key)
            self.assertLessEqual(size.cap + size.shadow, size.line)
            for p in sorted((FONTS_DIR / folder).glob("*.png")):
                with Image.open(p) as img:
                    self.assertEqual(img.height, size.cap + size.shadow, p)

    def test_letters_and_digits_reach_baseline_and_cap_line(self):
        """Cap height is ink, not box: every capital and digit touches both
        the top and the bottom row of the cap box, in every style."""
        for key, st in self.gen.STYLES.items():
            for size_key in FOLDERS.values():
                for ch in self.gen.CYRILLIC + self.gen.LATIN + self.gen.DIGITS:
                    ink, _ = self.gen.render_glyph(ch, st, size_key)
                    cap = (st.small if size_key == "small" else st.big).cap
                    with self.subTest(style=key, size=size_key, ch=ch):
                        self.assertEqual(ink.shape[0], cap)
                        self.assertTrue(ink[0].any() and ink[-1].any(), "\n" + ink_ascii(ink))

    def test_spacing_column_is_empty(self):
        """The image is padded to the advance width; its last column is the
        bearing and must stay transparent or two letters touch."""
        for size_key in FOLDERS.values():
            size = self.size(size_key)
            for ch in self.order:
                ink, advance = self.gen.render_glyph(ch, self.style, size_key)
                img = np.asarray(self.gen.glyph_image(ch, self.style, size_key))
                with self.subTest(size=size_key, ch=ch):
                    self.assertEqual(advance, ink.shape[1] + size.bearing)
                    self.assertEqual(img.shape[1], advance + size.shadow)
                    self.assertFalse(img[:, -1, 3].any())

    def test_font_inf_states_the_line_height(self):
        for folder, size_key in FOLDERS.items():
            text = (FONTS_DIR / folder / "font.inf").read_text(encoding="utf-8")
            with self.subTest(folder=folder):
                self.assertEqual(text.split(), ["FontHeight", str(self.size(size_key).line)])

    def test_big_font_shadow_sits_down_right_of_the_body(self):
        """The 1 px shadow is drawn only where the body is not, and every
        shadow pixel has body ink one pixel up-left of it."""
        body_s, body_b, shadow = self.gen.colours(self.style)
        for ch in self.order:
            rgba = np.asarray(self.gen.glyph_image(ch, self.style, "big"))
            rgb = rgba[..., :3]
            is_body = (rgba[..., 3] == 255) & (rgb == body_b).all(-1)
            is_shadow = (rgba[..., 3] == 255) & (rgb == shadow).all(-1)
            with self.subTest(ch=ch):
                self.assertEqual(int(((rgba[..., 3] == 255) & ~is_body & ~is_shadow).sum()), 0)
                ys, xs = np.nonzero(is_shadow)
                self.assertTrue(all(is_body[y - 1, x - 1] for y, x in zip(ys, xs)))
                if ch != " ":
                    self.assertTrue(is_shadow.any(), "a big glyph with no shadow")

    def test_small_font_is_flat(self):
        body_s, _body_b, _shadow = self.gen.colours(self.style)
        for ch in self.order:
            rgba = np.asarray(self.gen.glyph_image(ch, self.style, "small"))
            opaque = rgba[rgba[..., 3] == 255][:, :3]
            with self.subTest(ch=ch):
                self.assertTrue((opaque == body_s).all())


# ===========================================================================
# palette: the installed glyphs (no generator import needed)
# ===========================================================================
@imaging
class InstalledGlyphPaletteTests(unittest.TestCase):
    """ART-BIBLE §2: colours from docs/art/palette.json only. The glyphs are
    RGBA, not indexed (see the QA report: LICENSES.md still calls M_DOOM the
    only asset with alpha); what is enforced is the part that matters to the
    look - palette colours and hard alpha, like M_DOOM."""

    def test_opaque_pixels_are_palette_colours_and_alpha_is_hard(self):
        palette = palette_colours()
        pngs = sorted(FONTS_DIR.rglob("*.png"))
        self.assertTrue(pngs, "assets/fonts/ holds no glyphs")
        for p in pngs:
            with Image.open(p) as img:
                rgba = np.asarray(img.convert("RGBA"))
            alpha = set(np.unique(rgba[..., 3]).tolist())
            used = {tuple(int(v) for v in c) for c in rgba[rgba[..., 3] == 255][:, :3]}
            with self.subTest(glyph=str(p.relative_to(FONTS_DIR))):
                self.assertLessEqual(alpha, {0, 255})
                self.assertLessEqual(used, palette)


# ===========================================================================
# reproduction: style C rebuilt here == assets/fonts/, byte for byte
# ===========================================================================
@imaging
@fonts
class ReproductionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.reports = {k: gen.build_variant(st, cls.tmp / "first") for k, st in gen.STYLES.items()}
        cls.again = gen.build_variant(gen.STYLES[INSTALLED_STYLE], cls.tmp / "second")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def built(self, run: str) -> dict:
        root = self.tmp / run / INSTALLED_STYLE
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def test_build_is_deterministic(self):
        first, second = self.built("first"), self.built("second")
        # 112 codepoints + font.inf per folder: 224 glyphs since the German
        # letters were installed (D37, 2026-10-13); 214 before.
        self.assertEqual(len(first), 2 * (112 + 1))
        self.assertEqual(sorted(first), sorted(second))
        self.assertEqual([k for k in first if first[k] != second[k]], [])
        self.assertEqual(self.reports[INSTALLED_STYLE], self.again)

    def test_style_c_rebuilt_here_is_byte_identical_to_assets(self):
        """The installed font is reproducible from the script on this
        machine. If this goes red after an edit to gen_font.py, the edit
        changed shipped pixels: that is a new proposal for the CEO, not a
        test to update (CLAUDE.md, "an approved asset is regenerated...")."""
        built = self.built("first")
        differing = []
        for folder in FOLDERS:
            for p in sorted((FONTS_DIR / folder).iterdir()):
                key = f"{folder}/{p.name}"
                self.assertIn(key, built, f"{key}: installed but not generated")
                if p.name == "font.inf":
                    # git's core.autocrlf rewrites this text file on a Windows
                    # checkout, and Path.write_text emits the platform newline;
                    # compare the text, the bytes are the checkout's business.
                    if p.read_text(encoding="utf-8").split() != built[key].decode("utf-8").split():
                        differing.append(f"{key}: text differs")
                    continue
                if p.read_bytes() != built[key]:
                    with Image.open(p) as a, Image.open(io.BytesIO(built[key])) as b:
                        aa, bb = np.asarray(a.convert("RGBA")), np.asarray(b.convert("RGBA"))
                    px = int((aa != bb).any(-1).sum()) if aa.shape == bb.shape else "size"
                    differing.append(f"{key}: {px} px")
        self.assertEqual(differing, [], f"{len(differing)} installed glyph file(s) do not reproduce")

    def test_report_describes_the_installed_files(self):
        """build_variant()'s report (it becomes manifest.json) states the
        image width of each glyph; it must be the width actually shipped."""
        rep = self.reports[INSTALLED_STYLE]
        self.assertEqual(rep["variant"], INSTALLED_STYLE)
        for folder, size_key in FOLDERS.items():
            sz = rep["sizes"][size_key]
            self.assertEqual(sz["folder"], f"fonts/{folder}/")
            self.assertEqual(sz["glyphs"], len(sz["widths"]))
            for cp, width in sz["widths"].items():
                with Image.open(FONTS_DIR / folder / f"{cp[2:]}.png") as img:
                    self.assertEqual(img.width, width, f"{folder} {cp}")

    def test_the_three_styles_are_actually_different(self):
        """A, B and C are offered as a choice: identical folders would mean
        a style switch stopped reaching the pen."""
        trees = {}
        for key in self.gen.STYLES:
            root = self.tmp / "first" / key
            trees[key] = {p.relative_to(root).as_posix(): p.read_bytes()
                          for p in root.rglob("*.png")}
        self.assertNotEqual(trees["A"], trees["B"])
        self.assertNotEqual(trees["B"], trees["C"])
        self.assertNotEqual(trees["A"], trees["C"])


# ===========================================================================
# the Pen and the style switches
# ===========================================================================
@imaging
@fonts
class PenRuleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import gen_font as gen
        cls.gen = gen

    def ink(self, ch, key, size_key):
        return self.gen.render_glyph(ch, self.gen.STYLES[key], size_key)[0]

    def test_rounding_is_half_up_not_half_even(self):
        """Python's round() sends 0.5 and 2.5 to the even neighbour and moves
        the middle stem of Ж, Ш, М by a pixel (the Pen docstring)."""
        self.assertEqual([self.gen.Pen._r(v) for v in (0.5, 1.5, 2.5, 3.49, -0.5)],
                         [1, 2, 3, 3, 0])

    def test_centred_glyphs_have_parity_for_a_middle_stem(self):
        for key, st in self.gen.STYLES.items():
            for size_key in FOLDERS.values():
                size = st.small if size_key == "small" else st.big
                pad = 2 if size.slab else 0
                for cp, (cls, _fn, center) in self.gen.GLYPHS.items():
                    if not center:
                        continue
                    w = self.gen.ink_width(st, size_key, cls, center) - pad
                    with self.subTest(style=key, size=size_key, ch=chr(cp)):
                        self.assertEqual((w - size.stem) % 2, 0)

    def test_symmetric_glyphs_are_symmetric(self):
        for key in self.gen.STYLES:
            for size_key in FOLDERS.values():
                for ch in SYMMETRIC:
                    if key == "C" and ch in SYMMETRIC_BROKEN_IN_C:
                        continue
                    ink = self.ink(ch, key, size_key)
                    with self.subTest(style=key, size=size_key, ch=ch):
                        self.assertTrue((ink == ink[:, ::-1]).all(), "\n" + ink_ascii(ink))

    def test_cyrillic_lookalikes_are_the_latin_drawing(self):
        for lat, cyr in zip("ABEKMHOPCTX", "АВЕКМНОРСТХ"):
            with self.subTest(cyr=cyr):
                self.assertIs(self.gen.GLYPHS[ord(cyr)], self.gen.GLYPHS[ord(lat)])
                self.assertTrue((self.ink(cyr, "C", "big") == self.ink(lat, "C", "big")).all())

    def test_slab_feet_only_in_style_c(self):
        """C's slabs widen the foot of I past the stem; A and B keep the
        bare stem."""
        for key, expect_slab in (("A", False), ("B", False), ("C", True)):
            for size_key in FOLDERS.values():
                st = self.gen.STYLES[key]
                stem = (st.small if size_key == "small" else st.big).stem
                foot = int(self.ink("I", key, size_key)[-1].sum())
                with self.subTest(style=key, size=size_key):
                    self.assertEqual(foot > stem, expect_slab)

    def changed_by(self, key, **flip) -> set:
        """Characters whose drawing changes when a Style switch is flipped."""
        st = self.gen.STYLES[key]
        other = dataclasses.replace(st, **flip)
        changed = set()
        for cp in self.gen.GLYPHS:
            for size_key in FOLDERS.values():
                a = self.gen.render_glyph(chr(cp), st, size_key)[0]
                b = self.gen.render_glyph(chr(cp), other, size_key)[0]
                if a.shape != b.shape or not (a == b).all():
                    changed.add(chr(cp))
        return changed

    def test_flat_apex_switch_reaches_exactly_the_a(self):
        """flat_apex is the poster A (A, C) versus the pointed A (B); it
        must change the two A's and nothing else. Since D37 (2026-10-13)
        the A-umlaut is drawn on the Latin A's stroke code, so it follows."""
        for key in self.gen.STYLES:
            with self.subTest(style=key):
                self.assertEqual(self.changed_by(key, flat_apex=not self.gen.STYLES[key].flat_apex),
                                 {"A", "А", "Ä"})

    def test_slashed_zero_switch_reaches_exactly_the_zero(self):
        for key in self.gen.STYLES:
            with self.subTest(style=key):
                self.assertEqual(
                    self.changed_by(key, slashed_zero=not self.gen.STYLES[key].slashed_zero), {"0"})
        self.assertEqual([k for k, s in self.gen.STYLES.items() if s.slashed_zero], ["C"])

    def test_blob_is_a_ring_when_a_counter_fits_and_solid_otherwise(self):
        st = self.gen.STYLES["A"]
        big = self.gen.Pen(7, st.big, st).blob(0, 1, 0, 1).finish()
        self.assertFalse(big[5, 3], "a 7x11 box with a 2 px stem keeps a counter")
        tiny = self.gen.Pen(3, st.big, st).blob(0, 1, 0.8, 1).finish()
        self.assertTrue(tiny[0:3, 0:3].all(), "a box too small for a counter is filled")

    def test_render_font_folds_case_and_records_what_it_cannot_draw(self):
        """The sheet's "missing in these strings" line comes from here: a
        character with no glyph is skipped and remembered, not drawn as
        garbage; lowercase is drawn with its capital."""
        font = self.gen.RenderFont(self.gen.STYLES["C"], "small")
        self.assertEqual(font.width("ёж"), font.width("ЁЖ"))
        self.assertEqual(font.missing, set())
        line = font.render("Я~Я")
        self.assertEqual(font.missing, {"~"})
        self.assertEqual(line.width, 2 * font.glyph("Я").width)
        self.assertEqual(line.height, font.height)

    def test_run_width_measures_contiguous_ink(self):
        st = self.gen.STYLES["C"]
        pen = self.gen.Pen(6, st.small, st)
        pen.ink[2, 1:4] = True
        self.assertEqual(pen._run_width(2, 2), 3)
        self.assertEqual(pen._run_width(2, 5), 0)


# ===========================================================================
# finding H1: style C slab serifs on M and W (fixed 2026-10-13, regression)
# ===========================================================================
@imaging
@fonts
class SlabSerifDefectTests(unittest.TestCase):
    """QA finding H1 (2026-10-13), shipped in assets/fonts/ at both sizes
    until the fix was installed the same day.

    In style C the slab serifs are placed from Pen.terminals, which the
    mirror() of M and W did not mirror. M got a top-left slab and no
    top-right one. W appended its extra terminal at (1.0, 0.0), the bottom
    right, where no stroke ends, so a floating foot was drawn there, and its
    top-right slab was missing. Both letters stopped being symmetric;
    Cyrillic М is the same drawing as M.

    Fixed by gen_font.MIRROR_TERMINALS = True, approved by the CEO on
    2026-10-13 ("apruebo el arreglo de la fuente") and installed: six PNGs
    in assets/fonts/. The expected-failure marker is gone; this is the
    regression test, on the shipped value of the switch."""

    FIXED = ["M", "М", "W"]          # Latin M, Cyrillic M, W

    def test_m_and_w_are_symmetric_in_style_c(self):
        import gen_font as gen
        broken = []
        for ch in self.FIXED:
            for size_key in FOLDERS.values():
                ink = gen.render_glyph(ch, gen.STYLES["C"], size_key)[0]
                if not (ink == ink[:, ::-1]).all():
                    broken.append(f"{ch} {size_key}\n{ink_ascii(ink)}")
        self.assertEqual(broken, [])


# ===========================================================================
# the preview sheets and the CLI, with OUT_ROOT redirected to a tempdir
# ===========================================================================
@imaging
@fonts
class SheetsAndCliTests(unittest.TestCase):
    """The sheets are text-bearing (system fonts), so their bytes are not
    compared across machines; what is checked is that they are produced,
    where, and that main() writes what it says. OUT_ROOT is patched: the
    unpatched value is work/art/font/, the Mac's renders."""

    def setUp(self):
        import gen_font as gen
        self.gen = gen
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name)
        patcher = mock.patch.object(gen, "OUT_ROOT", self.out)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, *argv) -> list[Path]:
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["gen_font.py", *argv]), contextlib.redirect_stdout(buf):
            self.gen.main()
        return [Path(line) for line in buf.getvalue().splitlines() if line.strip()]

    def assert_under_out(self, paths):
        for p in paths:
            self.assertTrue(p.is_file(), p)
            self.assertEqual(p.resolve().parent, self.out.resolve(), f"{p} escaped the tempdir")

    def test_main_builds_one_variant_its_sheet_and_the_manifest(self):
        printed = self.run_main("--variant", "C", "--stamp", "TEST")
        self.assertEqual([p.name for p in printed],
                         ["TEST_F2_font-C-mashina.png", "TEST_F2_font-compare.png"])
        self.assert_under_out(printed)
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["stamp"], "TEST")
        self.assertEqual(manifest["codepoints"], len(self.gen.GLYPHS))
        self.assertEqual([v["variant"] for v in manifest["variants"]], ["C"])
        for folder in FOLDERS:
            self.assertEqual(len(list((self.out / "C" / folder).glob("*.png"))), len(self.gen.GLYPHS))
        with Image.open(printed[0]) as sheet:
            self.assertEqual(sheet.width, 1500)

    def test_sheets_only_writes_no_glyphs_and_no_manifest(self):
        printed = self.run_main("--sheets", "--variant", "A")
        self.assert_under_out(printed)
        self.assertEqual(printed[0].name, "PREVIEW_F2_font-A-plakat.png")
        self.assertFalse((self.out / "manifest.json").exists())
        self.assertFalse((self.out / "A").exists())


if __name__ == "__main__":
    unittest.main()
