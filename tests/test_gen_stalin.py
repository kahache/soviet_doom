"""Contract tests for tools/art/gen_stalin.py, the twin of SDPOSTR1 (Lenin).

The poster's contract is Lenin's (128x256, N flat palette inks plus the gold
rule, the slogan through a hard-cut mask) plus what this generator adds:
an aspect-true crop, a multi-line slogan that shrinks to fit, and the reuse
of gen_lenin's pipeline by patching three of its globals - which must always
be put back, or the Lenin lump would be built with a Stalin crop.

Nothing here needs the reference photograph: the pipeline runs end to end on
a synthetic plate written to a temp directory. The few tests that need the
real photograph (work/art/reference/stalin_<key>.jpg, gitignored, downloaded
by hand with the CEO's permission) skip when it is absent.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_stalin -v
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "art"))
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"

try:
    import numpy as np
    from PIL import Image, ImageDraw
    import artlib
    HAVE_IMAGING = True
    HAVE_FONTS = artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = HAVE_FONTS = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
fonts = unittest.skipUnless(HAVE_FONTS, "system fonts (Impact, Arial Narrow Bold) not present")

if HAVE_IMAGING:
    import gen_lenin
    import gen_stalin as st
    REAL_PHOTO = st.CANDIDATES[st.DEFAULT_CANDIDATE].photo
    HAVE_REAL_PHOTO = REAL_PHOTO.is_file()
else:  # pragma: no cover
    REAL_PHOTO, HAVE_REAL_PHOTO = None, False
real_photo = unittest.skipUnless(
    HAVE_REAL_PHOTO, "reference photograph absent (work/ is gitignored; downloaded only with the CEO's permission)")

PLATE = (600, 900)   # synthetic plate: tall, like a portrait negative


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def colours_of(img) -> set:
    return {tuple(int(v) for v in p) for p in np.asarray(img.convert("RGB")).reshape(-1, 3)}


def gold():
    return artlib.ramp_colour("hazard_yellow", 0.86)


def write_synthetic_plate(path: Path) -> None:
    """A grey plate with a smooth gradient and a few shapes: enough tonal
    range for four percentile cuts, deterministic, and nobody's likeness."""
    w, h = PLATE
    y, x = np.mgrid[0:h, 0:w]
    field = (40 + 150 * (y / h) + 50 * np.sin(x / 37.0)).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(field, "L")
    d = ImageDraw.Draw(im)
    d.ellipse([180, 120, 420, 420], fill=210)
    d.rectangle([120, 520, 480, 880], fill=30)
    # fine noise so no percentile falls on a flat plateau (a tie would merge two inks)
    noise = np.random.default_rng(1930).integers(-25, 26, size=(h, w))
    a = (np.asarray(im, dtype=int) + noise).clip(0, 255).astype(np.uint8)
    Image.fromarray(a, "L").convert("RGB").save(path, quality=95)


class SyntheticPhoto:
    """Point the generator's reference directory at a temp dir holding a
    synthetic stalin_<default>.jpg for the duration of a test class."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls._saved_ref = st.REFERENCE_DIR
        st.REFERENCE_DIR = cls.tmp
        write_synthetic_plate(st.CANDIDATES[st.DEFAULT_CANDIDATE].photo)

    @classmethod
    def tearDownClass(cls):
        st.REFERENCE_DIR = cls._saved_ref
        cls._tmp.cleanup()


# ===========================================================================
# no pixels: declarations and the crop arithmetic
# ===========================================================================
@imaging
class DeclarationTests(unittest.TestCase):

    def test_the_format_is_lenins(self):
        self.assertEqual((st.WIDTH, st.HEIGHT), (gen_lenin.WIDTH, gen_lenin.HEIGHT))
        self.assertEqual((st.WIDTH, st.HEIGHT), (128, 256))
        self.assertEqual(st.SLOGAN_BAND, gen_lenin.SLOGAN_BAND)
        self.assertEqual(st.BORDER, gen_lenin.BORDER)
        self.assertEqual(st.inks(), gen_lenin.inks())

    def test_the_sweep_is_fifteen_cells_like_lenins(self):
        self.assertEqual(len(st.SWEEP_INKS) * len(st.SWEEP_BIASES), 15)
        self.assertEqual(st.SWEEP_BIASES, (-18, -9, 0, 9, 18))
        self.assertIn(st.INK_COUNT, st.SWEEP_INKS)
        self.assertIn(st.CUT_BIAS, st.SWEEP_BIASES)

    def test_every_candidate_lives_in_the_gitignored_reference_dir(self):
        for key, c in st.CANDIDATES.items():
            self.assertEqual(c.key, key)
            self.assertEqual(c.photo.name, f"stalin_{key}.jpg")
            self.assertEqual(c.photo.parent, st.REFERENCE_DIR)
            self.assertTrue(str(c.photo.relative_to(PROJECT_ROOT)).replace("\\", "/")
                            .startswith("work/art/reference/"))
            self.assertTrue(c.commons_file.startswith("File:"))
        self.assertIn(st.DEFAULT_CANDIDATE, st.CANDIDATES)
        self.assertGreaterEqual(len(st.CANDIDATES), 3)

    def test_fit_crop_has_the_portrait_aspect_in_pixels(self):
        """Lenin's crop was set by eye and is ~13% wider once resized; this
        one is derived, so the face keeps its proportions."""
        for c in st.CANDIDATES.values():
            left, top, right, bottom = st.fit_crop(c.plate, c.crop)
            pw, ph = c.plate
            self.assertAlmostEqual((right - left) * pw / ((bottom - top) * ph), st.WIDTH / st.BODY, places=6)
            self.assertTrue(0 <= left < right <= 1 and 0 <= top < bottom <= 1, c.key)

    def test_fit_crop_centres_and_clamps_to_the_plate(self):
        left, _, right, _ = st.fit_crop((1000, 1000), (0.5, 0.1, 0.6))
        self.assertAlmostEqual((left + right) / 2, 0.5)
        left, _, right, _ = st.fit_crop((1000, 1000), (0.02, 0.1, 0.6))   # pushed off the left edge
        self.assertEqual(left, 0)
        left, _, right, _ = st.fit_crop((1000, 1000), (0.98, 0.1, 0.6))
        self.assertAlmostEqual(right, 1.0)

    def test_fit_crop_on_a_too_narrow_plate_raises_the_bottom_not_the_aspect(self):
        left, top, right, bottom = st.fit_crop((100, 1000), (0.5, 0.0, 1.0))   # would need 610 px wide
        self.assertEqual((left, right), (0.0, 1.0))
        self.assertLess(bottom, 1.0)
        self.assertAlmostEqual(100 / ((bottom - top) * 1000), st.WIDTH / st.BODY, places=6)

    def test_fit_crop_rejects_a_crop_outside_the_plate(self):
        for bad in [(0.5, 0.6, 0.4), (0.5, -0.1, 0.5), (1.2, 0.1, 0.5), (0.5, 0.1, 1.1)]:
            with self.assertRaises(ValueError):
                st.fit_crop((1000, 1000), bad)

    def test_slogan_lines_accepts_newline_and_bar(self):
        self.assertEqual(st.slogan_lines("ЗА РОДИНУ!|ЗА СТАЛИНА!"), ["ЗА РОДИНУ!", "ЗА СТАЛИНА!"])
        self.assertEqual(st.slogan_lines(" А \n\n Б "), ["А", "Б"])
        self.assertEqual(st.slogan_lines(""), [])

    def test_a_missing_photograph_stops_with_the_commons_page_not_a_traceback(self):
        saved = st.REFERENCE_DIR
        with tempfile.TemporaryDirectory() as empty:
            st.REFERENCE_DIR = Path(empty)
            try:
                with self.assertRaises(SystemExit) as cm:
                    st.candidate()
            finally:
                st.REFERENCE_DIR = saved
        self.assertIn("commons.wikimedia.org/wiki/File:", str(cm.exception))
        self.assertIn("CEO", str(cm.exception))

    def test_an_unknown_candidate_is_refused(self):
        with self.assertRaises(SystemExit):
            st.candidate("1953")


# ===========================================================================
# the slogan: needs fonts, not the photograph
# ===========================================================================
@imaging
@fonts
class SloganTests(unittest.TestCase):

    def test_every_proposed_slogan_fits_the_band(self):
        for key, text in st.SLOGANS.items():
            mask, size = st.slogan_mask(text)
            self.assertGreaterEqual(size, st.SLOGAN_MIN_SIZE, key)
            self.assertLessEqual(size, st.SLOGAN_SIZE, key)
            a = np.asarray(mask.convert("L")) > 0
            cols, rows = np.nonzero(a.any(axis=0))[0], np.nonzero(a.any(axis=1))[0]
            self.assertLessEqual(int(cols.max() - cols.min() + 1), st.SLOGAN_MAX_WIDTH, key)
            self.assertGreaterEqual(int(cols.min()), st.BORDER, key)
            self.assertLess(int(cols.max()), st.WIDTH - st.BORDER, key)
            self.assertGreaterEqual(int(rows.min()), 1, f"{key} touches the gold rule")
            self.assertLess(int(rows.max()), st.SLOGAN_BAND - st.BORDER, f"{key} touches the border")

    def test_the_two_line_slogans_keep_lenins_size(self):
        """«ЗА РОДИНУ! / ЗА СТАЛИНА!» and «СЛАВА / СТАЛИНУ!» stamp at
        Lenin's 19 px: the poster reads as his twin."""
        for key in ("za_rodinu", "slava_short"):
            self.assertEqual(st.slogan_mask(st.SLOGANS[key])[1], st.SLOGAN_SIZE, key)

    def test_a_slogan_too_long_for_any_size_is_an_error_not_an_overflow(self):
        with self.assertRaises(ValueError):
            st.slogan_mask("СЛАВА ВЕЛИКОМУ СТАЛИНУ ЗОДЧЕМУ КОММУНИЗМА")

    def test_the_band_is_three_palette_colours_and_the_letters_are_hard(self):
        """The regression guard Lenin paid for: antialiased text invented 95
        off-palette colours. Here the band is red ground, cream letters and
        border, gold rule - nothing in between."""
        _, red, _, cream = st.inks()
        for key, text in st.SLOGANS.items():
            band = st.slogan_band(text)
            self.assertEqual(band.size, (st.WIDTH, st.SLOGAN_BAND))
            self.assertEqual(colours_of(band), {red, cream, gold()}, key)
            self.assertTrue(colours_of(band) <= palette_colours(), key)

    def test_an_empty_slogan_leaves_the_band_plain(self):
        _, red, _, cream = st.inks()
        self.assertEqual(st.slogan_mask("")[1], 0)
        plain = np.asarray(st.slogan_band(""))
        inner = plain[2:st.SLOGAN_BAND - st.BORDER, st.BORDER:st.WIDTH - st.BORDER]
        self.assertEqual({tuple(int(v) for v in p) for p in inner.reshape(-1, 3)}, {red})

    def test_the_slogan_sheet_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "s.png"
            st.slogan_sheet(out)
            with Image.open(out) as im:
                self.assertGreater(im.height, len(st.SLOGANS) * st.SLOGAN_BAND)


# ===========================================================================
# the whole pipeline on a synthetic plate
# ===========================================================================
@imaging
@fonts
class PipelineTests(SyntheticPhoto, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.img = st.poster()
        cls.plain = st.poster(slogan="")

    def test_the_poster_is_the_declared_size_and_mode(self):
        self.assertEqual(self.img.size, (128, 256))
        self.assertEqual(self.img.mode, "RGB")

    def test_exactly_ink_count_inks_plus_the_gold_rule(self):
        self.assertEqual(colours_of(self.img), set(st.inks()) | {gold()})
        self.assertTrue(colours_of(self.img) <= palette_colours())

    def test_the_slogan_changes_only_its_band_and_only_to_cream(self):
        a, b = np.asarray(self.img), np.asarray(self.plain)
        changed = np.any(a != b, axis=2)
        self.assertTrue(changed.any())
        self.assertFalse(changed[:st.BODY + 1].any(), "the slogan leaked above the band or over the gold rule")
        self.assertEqual({tuple(int(v) for v in p) for p in a[changed]}, {st.inks()[3]})

    def test_the_frame_is_lenins(self):
        a = np.asarray(self.img)
        cream = st.inks()[3]
        for px in (a[0, 0], a[0, -1], a[-1, 0], a[-1, -1], a[0, 64], a[-1, 64]):
            self.assertEqual(tuple(int(v) for v in px), cream)
        self.assertEqual(tuple(int(v) for v in a[st.BODY, 64]), gold())

    def test_each_sweep_row_has_its_ink_count(self):
        for n in st.SWEEP_INKS:
            p = st.portrait(0, ink_count=n)
            self.assertEqual(p.shape, (st.BODY, st.WIDTH, 3))
            self.assertEqual(len({tuple(px) for px in p.reshape(-1, 3)}), n)

    def test_gen_lenin_is_left_exactly_as_it_was(self):
        """The patch is undone after every call, success or failure: the
        Lenin lump must never be built from a Stalin crop."""
        before = gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT
        st.poster(bias=9, ink_count=2)
        self.assertEqual((gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT), before)
        real = gen_lenin.portrait
        gen_lenin.portrait = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            with self.assertRaises(RuntimeError):
                st.portrait(0)
        finally:
            gen_lenin.portrait = real
        self.assertEqual((gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT), before)

    def test_the_poster_is_deterministic(self):
        self.assertEqual(np.asarray(st.poster()).tobytes(), np.asarray(self.img).tobytes())

    def test_the_sweep_sheet_has_fifteen_cells(self):
        out = self.tmp / "sweep.png"
        st.sweep(out)
        zoom, label, gap = 2, 22, 8   # the layout of Lenin's sheet
        with Image.open(out) as im:
            self.assertEqual(im.width, 5 * (st.WIDTH * zoom + gap) + gap)
            self.assertEqual(im.height, 3 * (st.BODY * zoom + label + gap) + gap + 24)

    def test_the_preview_sheet_holds_the_sweep_and_every_slogan(self):
        out = self.tmp / "preview.png"
        st.preview(out)
        with Image.open(out) as im:
            self.assertEqual(im.width, 5 * (st.WIDTH * 2 + 8) + 8)
            self.assertGreater(im.height, 3 * st.BODY * 2 + st.HEIGHT * 2)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if "sweep_part" in p.name), [])

    def test_the_cli_writes_an_indexed_lump(self):
        """The approved parameters (D55) write the file named after the lump."""
        out_dir = self.tmp / "cli"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(st.main(["--out-dir", str(out_dir), "--slogan", "slava_short"]), 0)
        with Image.open(out_dir / f"{st.LUMP}.png") as im:
            self.assertEqual(im.mode, "P")
            self.assertEqual(im.size, (128, 256))
            self.assertTrue(colours_of(im) <= palette_colours())

    def test_other_parameters_never_write_a_file_named_after_the_lump(self):
        """test_art matches assets/SDPOSTR3.png to work/ BY NAME: an
        exploratory render must not take that name."""
        out_dir = self.tmp / "cli_other"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(st.main(["--out-dir", str(out_dir), "--slogan", "za_rodinu"]), 0)
            self.assertEqual(st.main(["--out-dir", str(out_dir), "--bias", "9"]), 0)
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()), ["stalin_poster.png"])

    def test_lump_is_exactly_what_the_cli_writes(self):
        """lump() (the identity test's renderer) and a plain CLI run (what
        was copied into assets/) are the same image."""
        out_dir = self.tmp / "cli_lump"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(st.main(["--out-dir", str(out_dir)]), 0)
        with Image.open(out_dir / f"{st.LUMP}.png") as im:
            self.assertTrue(np.array_equal(np.asarray(st.lump().convert("RGB")),
                                           np.asarray(im.convert("RGB"))))


# ===========================================================================
# the real photograph, when it is there
# ===========================================================================
@imaging
@fonts
@real_photo
class RealPhotographTests(unittest.TestCase):

    def test_the_real_plate_matches_the_declared_size(self):
        c = st.CANDIDATES[st.DEFAULT_CANDIDATE]
        with Image.open(c.photo) as im:
            self.assertEqual(im.size, c.plate)

    def test_every_ink_is_used_in_quantity(self):
        """Percentile cuts: no ink collapses to a handful of pixels."""
        _, counts = np.unique(st.portrait().reshape(-1, 3), axis=0, return_counts=True)
        self.assertEqual(len(counts), st.INK_COUNT)
        self.assertGreaterEqual(float((counts / counts.sum()).min()), 0.05)

    def test_the_real_poster_is_four_inks_and_gold(self):
        self.assertEqual(colours_of(st.poster()), set(st.inks()) | {gold()})


# ===========================================================================
# SDPOSTR3, the approved lump (D55)
# ===========================================================================
@imaging
class ApprovedCellTests(unittest.TestCase):
    """D55, 2026-10-14: the CEO approved cell 4C with «СЛАВА / СТАЛИНУ!»."""

    def test_the_parameters_are_the_cell_and_slogan_the_ceo_chose(self):
        self.assertEqual((st.INK_COUNT, st.CUT_BIAS), (4, 0))
        self.assertEqual(st.SLOGAN_KEY, "slava_short")
        self.assertEqual(st.slogan_lines(st.SLOGAN), ["СЛАВА", "СТАЛИНУ!"])
        self.assertEqual(st.DEFAULT_CANDIDATE, "1930")

    def test_the_lump_name_and_paths(self):
        self.assertEqual(st.LUMP, "SDPOSTR3")
        self.assertEqual(st.LUMP_PATH.name, "SDPOSTR3.png")
        self.assertEqual(st.ASSET_PATH.relative_to(PROJECT_ROOT).as_posix(),
                         "assets/textures/soviet_base/SDPOSTR3.png")

    @fonts
    def test_the_approved_slogan_stamps_at_lenins_19_px(self):
        self.assertEqual(st.slogan_mask(st.SLOGAN)[1], st.SLOGAN_SIZE)
        self.assertEqual(st.SLOGAN_SIZE, 19)


@imaging
@fonts
@real_photo
@unittest.skipUnless(sys.platform == "win32",
                     "D27: SDPOSTR3 was rendered on Windows (Impact rasterises differently on "
                     "the Mac); it is regenerated, and so checked against the generator, only on Windows")
class InstalledLumpIdentityTests(unittest.TestCase):
    """The generator still produces the installed SDPOSTR3 pixel for pixel.

    D27 (CLAUDE.md): a text-bearing lump is regenerated only on the machine
    that rendered it. SDPOSTR3 was rendered on the CEO's Windows PC on
    2026-10-14, so this test runs ONLY ON WINDOWS (and only where the
    gitignored reference photograph work/art/reference/stalin_1930.jpg is
    present). On the Mac it skips: there the slogan would rasterise
    differently and a red test would be the fonts, not the generator.

    Pixels, not PNG bytes: the bytes depend on Pillow's zlib build. The
    byte-for-byte copy work/ -> assets/ is tests/test_art.py's check."""

    def test_the_asset_is_installed_and_indexed(self):
        self.assertTrue(st.ASSET_PATH.is_file(), st.ASSET_PATH)
        with Image.open(st.ASSET_PATH) as im:
            self.assertEqual(im.mode, "P")
            self.assertEqual(im.size, (128, 256))
            self.assertTrue(colours_of(im) <= palette_colours())

    def test_the_generator_reproduces_the_installed_lump(self):
        regenerated = st.lump()
        with Image.open(st.ASSET_PATH) as installed:
            self.assertEqual(regenerated.mode, installed.mode)
            self.assertEqual(regenerated.size, installed.size)
            self.assertTrue(np.array_equal(np.asarray(regenerated.convert("RGB")),
                                           np.asarray(installed.convert("RGB"))),
                            "gen_stalin.lump() no longer renders the installed SDPOSTR3")


if __name__ == "__main__":
    unittest.main()
