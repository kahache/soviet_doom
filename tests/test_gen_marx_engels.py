"""Contract tests for tools/art/gen_marx_engels.py: the Marx-Engels pair.

The format the CEO approved (2026-10-22): two posters of SDPOSTR1/3's size and
style, 128x256 each, Marx (SDPOSTR4) carrying «ПРОЛЕТАРИИ ВСЕХ / СТРАН,» and
Engels (SDPOSTR5) carrying «СОЕДИНЯЙТЕСЬ!», hung Marx on the left. The
contract is Lenin's (N flat palette inks plus the gold rule, cream border,
the slogan through a hard-cut mask) plus what the pair adds: one slogan size
for both bands, Engels's line on the row of Marx's last line, the optional
mirror of Engels, a clean stop when a photograph is missing, gen_lenin left
exactly as it was, and nothing written to assets/.

The pipeline runs on synthetic plates in a temp directory. The few tests
that need the real photographs (work/art/reference/, gitignored, downloaded
by the PM with the CEO's permission on 2026-10-22) skip when they are absent.
The review sheets, which cut thirty portraits, skip under SD_SKIP_SLOW_ART=1.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_marx_engels -v
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "art"))
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
ASSETS = PROJECT_ROOT / "assets"

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
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART") == "1",
                       "SD_SKIP_SLOW_ART=1: the review sheets cut thirty portraits")

if HAVE_IMAGING:
    import gen_lenin
    import gen_marx_engels as me
    REAL = {"marx": me.MARX[me.DEFAULT_MARX], "engels": me.ENGELS[me.DEFAULT_ENGELS]}
    HAVE_REAL = all(c.photo.is_file() for c in REAL.values())
else:  # pragma: no cover
    REAL, HAVE_REAL = {}, False
real_photos = unittest.skipUnless(
    HAVE_REAL, "reference photographs absent (work/ is gitignored; downloaded only with the CEO's permission)")

# The downloads of 2026-10-22, as recorded in the sourcing doc.
SHA256 = {"marx_1875.jpg": "cc2fb87d222a2659a59496040805cb9911e16527f145edceb142cfe5954617c9",
          "engels_1877.jpg": "c7be6f45ed4f506a56735f2a451d7265f735eda1f8888c8029073c3c984fec31"}
PLATE = (600, 900)


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def colours_of(img) -> set:
    return {tuple(int(v) for v in p) for p in np.asarray(img.convert("RGB")).reshape(-1, 3)}


def rows_with_ink(mask) -> np.ndarray:
    return np.nonzero((np.asarray(mask.convert("L")) > 0).any(axis=1))[0]


def write_synthetic_plate(path: Path, seed: int, flip: bool = False) -> None:
    """A grey gradient with a 'head' off centre and a 'coat': four
    percentile cuts' worth of tone, deterministic, nobody's likeness."""
    w, h = PLATE
    y, x = np.mgrid[0:h, 0:w]
    field = (40 + 150 * (y / h) + 50 * np.sin(x / 37.0)).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(field, "L")
    d = ImageDraw.Draw(im)
    cx = 250 if flip else 350
    d.ellipse([cx - 110, 100, cx + 110, 400], fill=210)
    d.rectangle([120, 520, 480, 880], fill=30)
    noise = np.random.default_rng(seed).integers(-25, 26, size=(h, w))
    a = (np.asarray(im, dtype=int) + noise).clip(0, 255).astype(np.uint8)
    opts = {"quality": 95} if path.suffix.lower() == ".jpg" else {}
    Image.fromarray(a, "L").convert("RGB").save(path, **opts)


class SyntheticPhotos:
    """Point the generator's reference dir at a temp dir holding synthetic
    plates under every candidate's file name, for one test class."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls._saved_ref = me.REFERENCE_DIR
        me.REFERENCE_DIR = cls.tmp
        for i, c in enumerate([*me.MARX.values(), *me.ENGELS.values()]):
            write_synthetic_plate(c.photo, seed=1875 + i, flip=c.person == "engels")

    @classmethod
    def tearDownClass(cls):
        me.REFERENCE_DIR = cls._saved_ref
        cls._tmp.cleanup()


def asset_listing() -> list:
    """assets/textures/ (where a poster lump would land) file by file, plus
    the top of assets/: a walk of all of assets/ costs ~0.9 s."""
    files = list((ASSETS / "textures").rglob("*.png")) + [p for p in ASSETS.iterdir() if p.is_file()]
    return sorted((p.relative_to(ASSETS).as_posix(), p.stat().st_mtime_ns) for p in files)


# ===========================================================================
# declarations: no pixels
# ===========================================================================
@imaging
class DeclarationTests(unittest.TestCase):

    def test_the_format_is_lenins(self):
        self.assertEqual((me.WIDTH, me.HEIGHT), (gen_lenin.WIDTH, gen_lenin.HEIGHT))
        self.assertEqual((me.WIDTH, me.HEIGHT), (128, 256))
        self.assertEqual((me.SLOGAN_BAND, me.BORDER), (gen_lenin.SLOGAN_BAND, gen_lenin.BORDER))
        self.assertEqual(me.inks(), gen_lenin.inks())

    def test_the_pair_and_its_lump_names(self):
        self.assertEqual(me.PEOPLE, ("marx", "engels"))          # hanging order, Marx left
        self.assertEqual(me.LUMPS, {"marx": "SDPOSTR4", "engels": "SDPOSTR5"})

    def test_the_proposed_cells_are_in_the_sweep(self):
        self.assertEqual(len(me.SWEEP_INKS) * len(me.SWEEP_BIASES), 15)
        self.assertEqual(me.SWEEP_BIASES, (-18, -9, 0, 9, 18))
        for p in me.PEOPLE:
            self.assertIn(me.INK_COUNT[p], me.SWEEP_INKS)
            self.assertIn(me.CUT_BIAS[p], me.SWEEP_BIASES)
        self.assertEqual(me.cell_name(4, 9), "4D")
        self.assertEqual(me.cell_name(4, 0), "4C")

    def test_the_photographs_have_the_names_the_sourcing_doc_fixes(self):
        self.assertEqual(REAL["marx"].filename, "marx_1875.jpg")
        self.assertEqual(REAL["engels"].filename, "engels_1877.jpg")
        for table, person in ((me.MARX, "marx"), (me.ENGELS, "engels")):
            for key, c in table.items():
                self.assertEqual((c.key, c.person), (key, person))
                self.assertTrue(c.filename.startswith(f"{person}_{key}."), c.filename)
                self.assertEqual(c.photo.parent, me.REFERENCE_DIR)
                self.assertTrue(c.commons_url.startswith("https://commons.wikimedia.org/wiki/File:"))
                self.assertNotIn(" ", c.commons_url)

    def test_the_dirs_are_gitignored_work_and_the_preview_is_dated(self):
        self.assertEqual(me.REFERENCE_DIR.relative_to(PROJECT_ROOT).as_posix(), "work/art/reference")
        self.assertEqual(me.OUT_DIR.relative_to(PROJECT_ROOT).as_posix(), "work/art/marx_engels")
        self.assertEqual(me.PREVIEW_PATH.relative_to(PROJECT_ROOT).as_posix(),
                         "docs/art/previews/2026-10-22_P4_marx-engels-sweep.png")

    def test_every_crop_fits_its_plate_at_the_portrait_aspect(self):
        for c in [*me.MARX.values(), *me.ENGELS.values()]:
            left, top, right, bottom = me.stalin.fit_crop(c.plate, c.crop)
            pw, ph = c.plate
            self.assertTrue(0 <= left < right <= 1 and 0 <= top < bottom <= 1, c.filename)
            self.assertAlmostEqual((right - left) * pw / ((bottom - top) * ph), me.WIDTH / me.BODY, places=6)
            self.assertGreaterEqual((right - left) * pw, 2 * me.WIDTH, f"{c.filename}: would be enlarged")

    def test_missing_photographs_stop_with_every_commons_page(self):
        saved = me.REFERENCE_DIR
        with tempfile.TemporaryDirectory() as empty:
            me.REFERENCE_DIR = Path(empty)
            try:
                with self.assertRaises(SystemExit) as cm:
                    me.pair()
            finally:
                me.REFERENCE_DIR = saved
        msg = str(cm.exception)
        for needle in ("marx_1875.jpg", "engels_1877.jpg", "CEO", "never downloads",
                       "commons.wikimedia.org/wiki/File:Karl_Marx_001.jpg",
                       "commons.wikimedia.org/wiki/File:Friedrich_Engels_portrait.jpg"):
            self.assertIn(needle, msg)

    def test_one_missing_photograph_is_named_alone(self):
        saved = me.REFERENCE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            me.REFERENCE_DIR = Path(tmp)
            write_synthetic_plate(me.MARX[me.DEFAULT_MARX].photo, 1)
            try:
                with self.assertRaises(SystemExit) as cm:
                    me.pair()
            finally:
                me.REFERENCE_DIR = saved
        self.assertIn("engels_1877.jpg", str(cm.exception))
        self.assertNotIn("marx_1875.jpg", str(cm.exception))

    def test_the_cli_without_photographs_exits_cleanly_and_writes_nothing(self):
        saved = me.REFERENCE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            me.REFERENCE_DIR = Path(tmp) / "ref"
            out = Path(tmp) / "out"
            try:
                for argv in ([], ["--sweep"], ["--preview", str(out / "p.png")]):
                    with self.assertRaises(SystemExit) as cm:
                        me.main(["--out-dir", str(out), *argv])
                    self.assertIn("never downloads", str(cm.exception.code), argv)
            finally:
                me.REFERENCE_DIR = saved
            self.assertFalse(out.exists())

    def test_unknown_candidates_are_refused(self):
        with self.assertRaises(SystemExit):
            me.pair(marx="1848")
        with self.assertRaises(SystemExit):
            me.pair(engels="1848")

    def test_the_proposal_never_takes_a_lump_name(self):
        """Nothing is approved: test_art matches assets/ to work/ BY NAME."""
        for p in me.PEOPLE:
            for lump in me.LUMPS.values():
                self.assertNotIn(lump, me.poster_file(p))
            self.assertFalse((ASSETS / "textures" / "soviet_base" / f"{me.LUMPS[p]}.png").exists())


# ===========================================================================
# the sentence over two bands: needs fonts, not the photographs
# ===========================================================================
@imaging
@fonts
class SloganTests(unittest.TestCase):

    def test_the_two_bands_read_the_manifesto_line(self):
        for split, (m, e) in me.SPLITS.items():
            self.assertEqual(" ".join((*m, *e)), "ПРОЛЕТАРИИ ВСЕХ СТРАН, СОЕДИНЯЙТЕСЬ!", split)
        self.assertEqual(me.SPLITS[me.DEFAULT_SPLIT], (("ПРОЛЕТАРИИ ВСЕХ", "СТРАН,"), ("СОЕДИНЯЙТЕСЬ!",)))

    def test_one_size_for_both_bands_measured_on_this_machine(self):
        """Impact on Windows (D27): the CEO's split fits at 15 px, the short
        split at 17. Both bands of a pair always stamp at the same size."""
        for split in me.SPLITS:
            size = me.pair_size(split)
            self.assertTrue(me.SLOGAN_MIN_SIZE <= size <= me.SLOGAN_SIZE, split)
            for p in me.PEOPLE:
                self.assertEqual(me.slogan_mask(p, split)[1], size)
        if sys.platform == "win32":
            self.assertEqual((me.pair_size("ceo"), me.pair_size("short")), (15, 17))

    def test_every_band_stays_inside_its_frame(self):
        for split in me.SPLITS:
            for align in me.ALIGNS:
                for p in me.PEOPLE:
                    mask, _ = me.slogan_mask(p, split, align)
                    a = np.asarray(mask.convert("L")) > 0
                    cols, rows = np.nonzero(a.any(axis=0))[0], np.nonzero(a.any(axis=1))[0]
                    key = (split, align, p)
                    self.assertGreaterEqual(int(cols.min()), me.BORDER, key)
                    self.assertLess(int(cols.max()), me.WIDTH - me.BORDER, key)
                    self.assertGreaterEqual(int(rows.min()), 1, f"{key} touches the gold rule")
                    self.assertLess(int(rows.max()), me.SLOGAN_BAND - me.BORDER, f"{key} touches the border")

    def test_the_breve_of_the_short_i_is_not_cut(self):
        """Й carries a breve above the cap height; the stamp must keep it.
        СОЕДИНЯЙТЕСЬ! inks rows above its cap top, so its ink starts higher
        than a line of plain caps on the same row would."""
        f = me.ImageFont.truetype(me.FONT_POSTER, me.pair_size())
        cap_top = f.getbbox(me.CAP_REFERENCE)[1]
        with_breve = me._line_mask("Й", f, cap_top).getbbox()
        plain = me._line_mask("И", f, cap_top).getbbox()
        self.assertLess(with_breve[1], plain[1])
        self.assertGreaterEqual(with_breve[1], 0)

    def test_pair_alignment_puts_engels_on_marxs_last_row(self):
        marx = rows_with_ink(me.slogan_mask("marx", align="pair")[0])
        engels = rows_with_ink(me.slogan_mask("engels", align="pair")[0])
        # the bottoms of the last rows match within the comma's tail
        f = me.ImageFont.truetype(me.FONT_POSTER, me.pair_size())
        cap = f.getbbox(me.CAP_REFERENCE)[3] - f.getbbox(me.CAP_REFERENCE)[1]
        self.assertLessEqual(abs(int(engels.max()) - int(marx.max())), cap // 3)
        self.assertGreater(int(engels.min()), int(marx.min()) + cap // 2, "Engels's word is not on the second row")

    def test_centre_alignment_centres_engels_alone(self):
        rows = rows_with_ink(me.slogan_mask("engels", align="centre")[0])
        mid = (1 + me.SLOGAN_BAND - me.BORDER) / 2
        self.assertLess(abs((rows.min() + rows.max()) / 2 - mid), 5)

    def test_a_bad_alignment_is_refused(self):
        with self.assertRaises(ValueError):
            me.slogan_mask("marx", align="justify")

    def test_the_bands_are_red_cream_and_gold_only(self):
        """Lenin's lesson: antialiased text invented 95 off-palette colours."""
        _, red, _, cream = me.inks()
        for split in me.SPLITS:
            for p in me.PEOPLE:
                band = me.slogan_band(p, split)
                self.assertEqual(band.size, (me.WIDTH, me.SLOGAN_BAND))
                self.assertEqual(colours_of(band), {red, cream, me.gold()}, (split, p))
                self.assertTrue(colours_of(band) <= palette_colours())

    def test_the_slogan_sheet_writes_without_photographs(self):
        saved = me.REFERENCE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            me.REFERENCE_DIR = Path(tmp) / "none"
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(me.main(["--slogans", "--out-dir", tmp]), 0)
            finally:
                me.REFERENCE_DIR = saved
            with Image.open(Path(tmp) / "marx_engels_slogans.png") as im:
                self.assertGreater(im.width, 2 * me.WIDTH)


# ===========================================================================
# the whole pipeline on synthetic plates
# ===========================================================================
@imaging
@fonts
class PipelineTests(SyntheticPhotos, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.img = me.posters()
        cls.plain = {p: me.poster(p, slogan=False) for p in me.PEOPLE}

    def test_each_poster_is_128x256_rgb(self):
        for p, im in self.img.items():
            self.assertEqual((im.size, im.mode), ((128, 256), "RGB"), p)

    def test_exactly_the_ink_count_plus_the_gold_rule(self):
        for p, im in self.img.items():
            self.assertEqual(colours_of(im), set(me.inks()) | {me.gold()}, p)
            self.assertTrue(colours_of(im) <= palette_colours(), p)

    def test_each_sweep_row_has_its_ink_count(self):
        c = me.pair()
        for p in me.PEOPLE:
            for n in me.SWEEP_INKS:
                cell = me.portrait(c[p], 0, n)
                self.assertEqual(cell.shape, (me.BODY, me.WIDTH, 3))
                inner = cell[me.BORDER:, me.BORDER:-me.BORDER]   # inside the printed border
                self.assertEqual(len({tuple(px) for px in inner.reshape(-1, 3)}), n, (p, n))

    def test_the_frame_is_lenins(self):
        cream = me.inks()[3]
        for p, im in self.img.items():
            a = np.asarray(im)
            for y, x in ((0, 0), (0, 127), (255, 0), (255, 127), (0, 64), (255, 64), (100, 0), (100, 127)):
                self.assertEqual(tuple(int(v) for v in a[y, x]), cream, (p, y, x))
            self.assertEqual(tuple(int(v) for v in a[me.BODY, 64]), me.gold(), p)

    def test_the_slogan_changes_only_its_band_and_only_to_cream(self):
        for p in me.PEOPLE:
            a, b = np.asarray(self.img[p]), np.asarray(self.plain[p])
            changed = np.any(a != b, axis=2)
            self.assertTrue(changed.any(), p)
            self.assertFalse(changed[:me.BODY + 1].any(), f"{p}: the slogan leaked above the band")
            self.assertEqual({tuple(int(v) for v in px) for px in a[changed]}, {me.inks()[3]}, p)

    def test_mirroring_flips_the_portrait_and_nothing_else(self):
        c = me.pair()["engels"]
        straight = np.asarray(me.plain_poster(c, 0, 4, mirror=False))
        flipped = np.asarray(me.plain_poster(c, 0, 4, mirror=True))
        self.assertTrue(np.array_equal(straight[:me.BODY, ::-1], flipped[:me.BODY]))
        self.assertTrue(np.array_equal(straight[me.BODY:], flipped[me.BODY:]))
        self.assertFalse(np.array_equal(straight, flipped))

    def test_engels_is_mirrored_by_default_and_marx_never(self):
        self.assertTrue(me.MIRROR_ENGELS)
        c = me.pair()
        self.assertTrue(np.array_equal(np.asarray(self.plain["engels"]),
                                       np.asarray(me.plain_poster(c["engels"], me.CUT_BIAS["engels"],
                                                                  me.INK_COUNT["engels"], True))))
        self.assertTrue(np.array_equal(np.asarray(self.plain["marx"]),
                                       np.asarray(me.plain_poster(c["marx"], me.CUT_BIAS["marx"],
                                                                  me.INK_COUNT["marx"], False))))

    def test_gen_lenin_is_left_exactly_as_it_was(self):
        before = gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT, gen_lenin.WIDTH
        me.poster("marx", bias=9, ink_count=2)
        me.poster("engels")
        self.assertEqual((gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT, gen_lenin.WIDTH), before)
        real = gen_lenin.poster
        gen_lenin.poster = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            with self.assertRaises(RuntimeError):
                me.poster("marx")
        finally:
            gen_lenin.poster = real
        self.assertEqual((gen_lenin.PHOTO, gen_lenin.CROP, gen_lenin.INK_COUNT, gen_lenin.WIDTH), before)

    def test_the_posters_are_deterministic(self):
        for p in me.PEOPLE:
            self.assertEqual(np.asarray(me.poster(p)).tobytes(), np.asarray(self.img[p]).tobytes(), p)

    def test_mounted_hangs_marx_on_the_left(self):
        m = me.mounted(self.img["marx"], self.img["engels"])
        self.assertEqual(m.size, (256, 256))
        a = np.asarray(m)
        self.assertTrue(np.array_equal(a[:, :128], np.asarray(self.img["marx"])))
        self.assertTrue(np.array_equal(a[:, 128:], np.asarray(self.img["engels"])))

    def test_the_cli_writes_indexed_files_under_proposal_names_only(self):
        out = self.tmp / "cli"
        before = asset_listing()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(me.main(["--out-dir", str(out)]), 0)
            self.assertEqual(me.main(["--out-dir", str(out), "--split", "short", "--align", "centre",
                                      "--bias", "-9", "--inks", "3", "--engels-as-photographed",
                                      "--engels", "1891"]), 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["marx_engels_engels_poster.png", "marx_engels_marx_poster.png"])
        for p in out.iterdir():
            with Image.open(p) as im:
                self.assertEqual((im.mode, im.size), ("P", (128, 256)))
                self.assertTrue(colours_of(im) <= palette_colours(), p.name)
        self.assertEqual(asset_listing(), before, "the generator touched assets/")

    @slow
    def test_the_sweep_sheets_have_fifteen_cells(self):
        out = self.tmp / "sweeps"
        out.mkdir()
        paths = me.sweep(out)
        self.assertEqual(len(paths), 2)
        zoom, label, gap, head = 2, 22, 8, 26
        for p in paths:
            with Image.open(p) as im:
                self.assertEqual(im.width, 5 * (me.WIDTH * zoom + gap) + gap)
                self.assertEqual(im.height, 3 * (me.BODY * zoom + label + gap) + gap + head)

    @slow
    def test_the_preview_holds_both_sweeps_and_the_pair(self):
        out = self.tmp / "preview.png"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(me.main(["--preview", str(out)]), 0)
        with Image.open(out) as im:
            self.assertGreaterEqual(im.width, 2 * (5 * (me.WIDTH * 2 + 8) + 8))
            self.assertGreater(im.height, 3 * me.BODY * 2 + me.HEIGHT * 2)


# ===========================================================================
# the real photographs (downloaded 2026-10-22), when they are there
# ===========================================================================
@imaging
@real_photos
class RealPhotographTests(unittest.TestCase):

    def test_the_plates_are_the_recorded_downloads(self):
        for c in REAL.values():
            with Image.open(c.photo) as im:
                self.assertEqual(im.size, c.plate, c.filename)
            self.assertEqual(c.photo.stat().st_size, c.bytes, c.filename)
            self.assertEqual(hashlib.sha256(c.photo.read_bytes()).hexdigest(), SHA256[c.filename])

    def test_every_ink_is_used_in_quantity_at_the_proposed_cells(self):
        """Percentile cuts: no ink collapses to a handful of pixels."""
        for p, c in REAL.items():
            cell = me.portrait(c, me.CUT_BIAS[p], me.INK_COUNT[p])[me.BORDER:, me.BORDER:-me.BORDER]
            _, counts = np.unique(cell.reshape(-1, 3), axis=0, return_counts=True)
            self.assertEqual(len(counts), me.INK_COUNT[p], p)
            self.assertGreaterEqual(float((counts / counts.sum()).min()), 0.05, p)

    @fonts
    def test_the_real_pair_is_four_inks_and_gold(self):
        for p, im in me.posters().items():
            self.assertEqual(colours_of(im), set(me.inks()) | {me.gold()}, p)


if __name__ == "__main__":
    unittest.main()
