"""Behaviour tests for the rest of tools/art/gen_menu.py (SDMENU, D22 for D31).

tests/test_gen_menu.py pins the substitution map and the installed font.
This file covers what the module does around it:

  build_font()   clears a stale output folder; REFUSES to write a Latin glyph
                 that is not byte-identical to the installed Cyrillic one
                 ("anything else would be a sixth, unapproved form")
  install()      the target folder ends up an exact copy of the build
  FolderFont     draws text from a folder font, recoloured the way a MENUDEF
                 Font colour would: brightest glyph colour -> body, the rest
                 -> shadow; lower case drawn with the capitals
  _skull()       decodes M_SKULL1 from a Doom patch in the IWAD, or None
  _dimmed_title  the engine's measured menu dim, out = 0.487 * in + (25,20,1)
  mocks          320x200 screens; the main menu's geometry is MENUDEF's;
                 every line is width-checked against the 320-px screen
  sheet()        the menu sweep PNG and the two MENUMOCK screens
  main()         the documented CLI: font + sheet, --install, --no-sheet

D27: nothing is written to work/, assets/ or docs/. OUT_ROOT is redirected
to a temp directory; build_font() and install() only ever get temp paths;
main() runs with its three actions mocked.

Run:  .venv/Scripts/python.exe -m unittest tests.test_cov_gen_menu -v
"""

from __future__ import annotations

import contextlib
import io
import re
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

import gen_menu  # noqa: E402  (stdlib-only at import time)

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

try:
    import artlib
    HAVE_FONTS = artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_FONTS = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
fonts = unittest.skipUnless(HAVE_IMAGING and HAVE_FONTS, "Pillow/numpy or the system label fonts not present")

BIGFONT = PROJECT_ROOT / "assets" / "fonts" / "bigfont"
SDMENU = PROJECT_ROOT / "assets" / "fonts" / "sdmenu"
MENUDEF = PROJECT_ROOT / "src" / "lumps" / "MENUDEF"
SCREEN_W = 320


def listmenu(name: str) -> str:
    """The body of LISTMENU "<name>" in src/lumps/MENUDEF."""
    text = MENUDEF.read_text(encoding="utf-8")
    m = re.search(r'^LISTMENU\s+"%s"\s*\{(.*?)^\}' % re.escape(name), text, re.S | re.M)
    if m is None:
        raise AssertionError(f'LISTMENU "{name}" not found in {MENUDEF}')
    return m.group(1)


def first_pair(body: str, keyword: str) -> tuple[int, int]:
    m = re.search(r"^\s*%s\s+(-?\d+)\s*,\s*(-?\d+)" % keyword, body, re.M)
    if m is None:
        raise AssertionError(f"no {keyword} line")
    return int(m.group(1)), int(m.group(2))


def first_int(body: str, keyword: str) -> int:
    return int(re.search(r"^\s*%s\s+(\d+)" % keyword, body, re.M).group(1))


class GlyphFileTests(unittest.TestCase):
    def test_glyph_files_are_named_by_code_point(self):
        self.assertEqual(gen_menu.glyph_file("R"), "0052.png")
        self.assertEqual(gen_menu.glyph_file("Я"), "042F.png")
        self.assertEqual(gen_menu.glyph_file(" "), "0020.png")

    def test_every_substituted_glyph_exists_in_bigfont(self):
        for latin, cyr in gen_menu.SUBSTITUTION.items():
            with self.subTest(latin=latin):
                self.assertTrue((BIGFONT / gen_menu.glyph_file(latin)).is_file())
                self.assertTrue((BIGFONT / gen_menu.glyph_file(cyr)).is_file())


class InstallTests(unittest.TestCase):
    def test_install_makes_an_exact_copy_and_drops_stale_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "built", Path(tmp) / "installed"
            src.mkdir()
            (src / "0041.png").write_bytes(b"new A")
            (src / "0042.png").write_bytes(b"new B")
            dst.mkdir()
            (dst / "0041.png").write_bytes(b"old A")
            (dst / "FFFF.png").write_bytes(b"a glyph the build no longer has")
            self.assertEqual(gen_menu.install(src, dst), dst)
            self.assertEqual(sorted(p.name for p in dst.iterdir()), ["0041.png", "0042.png"])
            self.assertEqual((dst / "0041.png").read_bytes(), b"new A")

    def test_install_creates_the_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "built"
            src.mkdir()
            (src / "0041.png").write_bytes(b"A")
            dst = gen_menu.install(src, Path(tmp) / "a" / "b")
            self.assertEqual((dst / "0041.png").read_bytes(), b"A")


@fonts
class BuildFontTests(unittest.TestCase):
    def test_report_and_stale_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sdmenu"
            out.mkdir()
            (out / "FFFF.png").write_bytes(b"left over from an older build")
            report = gen_menu.build_font(out)
            self.assertFalse((out / "FFFF.png").exists(), "a stale glyph survived the rebuild")
            self.assertEqual(report["font"], "sdmenu")
            self.assertEqual(report["files"], len(list(BIGFONT.iterdir())))
            self.assertEqual(report["replaced"], {
                "U+0052 R": "U+042F Я", "U+004E N": "U+0418 И", "U+0045 E": "U+042D Э",
                "U+0057 W": "U+0428 Ш", "U+0041 A": "U+0414 Д"})

    def test_it_refuses_a_glyph_that_is_not_the_installed_cyrillic_one(self):
        """If the alphabet in assets/ and gen_font's stroke code ever disagree,
        the build stops instead of shipping a sixth letterform."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bigfont"
            shutil.copytree(BIGFONT, src)
            shutil.copyfile(BIGFONT / "0041.png", src / "042F.png")   # "Я" is now a Latin A
            with self.assertRaisesRegex(RuntimeError, r"0052\.png: gen_font's Я differs"):
                gen_menu.build_font(Path(tmp) / "out", source_dir=src)


def _write_glyph(folder: Path, ch: str, rgba: list[list[tuple[int, int, int, int]]]) -> None:
    Image.fromarray(np.array(rgba, np.uint8), "RGBA").save(folder / gen_menu.glyph_file(ch))


BRIGHT, DARK, CLEAR = (200, 40, 40, 255), (30, 30, 30, 255), (0, 0, 0, 0)


@imaging
class FolderFontTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        _write_glyph(self.tmp, "A", [[BRIGHT, BRIGHT, CLEAR], [DARK, BRIGHT, DARK]])   # 3 wide
        _write_glyph(self.tmp, "B", [[BRIGHT, CLEAR], [CLEAR, DARK]])                   # 2 wide
        self.font = gen_menu.FolderFont(self.tmp)

    def test_lower_case_is_drawn_with_the_capitals(self):
        self.assertIs(self.font.glyph("a"), self.font.glyph("A"))

    def test_missing_glyphs_are_skipped_not_fatal(self):
        self.assertIsNone(self.font.glyph("Z"))
        self.assertEqual(self.font.width("AZB"), 5)
        self.assertEqual(self.font.render("AZB", (1, 2, 3), (4, 5, 6)).size, (5, 2))

    def test_render_recolours_body_and_shadow(self):
        out = np.asarray(self.font.render("AB", (250, 250, 0), (0, 0, 90)))
        self.assertEqual(out.shape, (2, 5, 4))
        expect = [[(250, 250, 0, 255), (250, 250, 0, 255), None, (250, 250, 0, 255), None],
                  [(0, 0, 90, 255), (250, 250, 0, 255), (0, 0, 90, 255), None, (0, 0, 90, 255)]]
        for y, row in enumerate(expect):
            for x, want in enumerate(row):
                with self.subTest(x=x, y=y):
                    if want is None:
                        self.assertEqual(out[y, x, 3], 0)
                    else:
                        self.assertEqual(tuple(out[y, x]), want)

    def test_an_empty_string_renders_a_transparent_pixel(self):
        img = self.font.render("", (1, 1, 1), (2, 2, 2))
        self.assertEqual(img.size, (1, 1))
        self.assertEqual(img.getpixel((0, 0))[3], 0)


def _wad(lumps: dict[str, bytes]) -> bytes:
    body, directory, pos = b"", b"", 12
    for name, data in lumps.items():
        directory += struct.pack("<ii8s", pos, len(data), name.encode("ascii"))
        body += data
        pos += len(data)
    return struct.pack("<4sii", b"PWAD", len(lumps), 12 + len(body)) + body + directory


def _patch(columns: list[list[tuple[int, list[int]]]], height: int, offsets: tuple[int, int]) -> bytes:
    """A Doom picture: header, column offsets, posts (top, len, pad, px.., pad), 0xFF."""
    w = len(columns)
    head = struct.pack("<hhhh", w, height, *offsets)
    data, offs = b"", []
    base = 8 + 4 * w
    for posts in columns:
        offs.append(base + len(data))
        for top, px in posts:
            data += bytes([top, len(px), 0, *px, 0])
        data += b"\xff"
    return head + struct.pack(f"<{w}I", *offs) + data


@imaging
class SkullTests(unittest.TestCase):
    PAL = bytes(v for i in range(256) for v in (i, (i * 2) % 256, (i * 3) % 256))

    def skull_from(self, wad: bytes | None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.wad"
            if wad is not None:
                path.write_bytes(wad)
            with mock.patch.object(gen_menu, "IWAD", path):
                return gen_menu._skull()

    def test_no_iwad_no_cursor(self):
        self.assertIsNone(self.skull_from(None))

    def test_an_iwad_without_the_lumps_gives_no_cursor(self):
        self.assertIsNone(self.skull_from(_wad({"PLAYPAL": self.PAL})))
        self.assertIsNone(self.skull_from(_wad({"M_SKULL1": _patch([[(0, [1])]], 1, (0, 0))})))

    def test_the_patch_is_decoded_through_the_palette(self):
        pic = _patch([[(0, [1, 2])], [(1, [3, 4])]], 3, (5, -3))
        img, offsets = self.skull_from(_wad({"PLAYPAL": self.PAL, "M_SKULL1": pic}))
        self.assertEqual(offsets, (5, -3))
        self.assertEqual((img.size, img.mode), ((2, 3), "RGBA"))
        pal = lambda i: (i, (i * 2) % 256, (i * 3) % 256, 255)  # noqa: E731
        self.assertEqual(img.getpixel((0, 0)), pal(1))
        self.assertEqual(img.getpixel((0, 1)), pal(2))
        self.assertEqual(img.getpixel((0, 2))[3], 0)
        self.assertEqual(img.getpixel((1, 0))[3], 0)
        self.assertEqual(img.getpixel((1, 1)), pal(3))
        self.assertEqual(img.getpixel((1, 2)), pal(4))

    @unittest.skipUnless(gen_menu.IWAD.is_file(), "iwads/freedoom2.wad not in this clone")
    def test_freedooms_cursor_reads(self):
        img, _ = gen_menu._skull()
        self.assertEqual(img.mode, "RGBA")
        self.assertTrue(8 <= img.width <= 64 and 8 <= img.height <= 64, img.size)
        self.assertGreater(int((np.asarray(img)[..., 3] == 255).sum()), 0)


@imaging
class DimTests(unittest.TestCase):
    def test_the_measured_dim(self):
        """docs/qa/evidence/2026-10-13_1007_F2_mainmenu-ru.png against TITLEPIC:
        black -> (25,20,1); (193,44,37) -> (119,41,18) as measured on screen."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "TITLEPIC.png"
            Image.fromarray(np.array([[[0, 0, 0], [193, 44, 37], [255, 255, 255]]], np.uint8), "RGB").save(src)
            with mock.patch.object(gen_menu, "TITLEPIC", src):
                out = gen_menu._dimmed_title()
        self.assertEqual(out.mode, "RGBA")
        px = [out.getpixel((x, 0)) for x in range(3)]
        self.assertEqual(px[0], (25, 20, 1, 255))
        for got, measured in zip(px[1][:3], (119, 41, 18)):
            self.assertLessEqual(abs(got - measured), 1, px[1])
        self.assertEqual(px[2][:3], tuple(int(255 * gen_menu.DIM_KEEP + a + 0.5) for a in gen_menu.DIM_ADD))


@imaging
class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        _write_glyph(self.tmp, "W", [[BRIGHT] * 100])          # one 100-px glyph
        self.font = gen_menu.FolderFont(self.tmp)
        self.screen = Image.new("RGBA", gen_menu.SCREEN, (0, 0, 0, 255))

    def test_a_line_past_the_right_edge_is_reported(self):
        over = []
        gen_menu._put_text(self.screen, self.font, "WW", (100, 10), (1, 2, 3), (0, 0, 0), over)
        self.assertEqual(over, [])
        gen_menu._put_text(self.screen, self.font, "WWW", (100, 20), (1, 2, 3), (0, 0, 0), over)
        self.assertEqual(over, ["'WWW' ends at x=400"])
        self.assertEqual(self.screen.getpixel((319, 20)), (1, 2, 3, 255))

    def test_selector_sits_at_doom_offset_and_never_off_screen(self):
        dot = Image.new("RGBA", (1, 1), (9, 9, 9, 255))
        gen_menu._put_selector(self.screen, None, (97, 72))     # no IWAD: nothing drawn
        self.assertEqual(self.screen.getpixel((65, 67)), (0, 0, 0, 255))
        gen_menu._put_selector(self.screen, (dot, (0, 0)), (97, 72))
        dx, dy = gen_menu.SELECTOR_OFFSET
        self.assertEqual((dx, dy), (-32, -5))                    # Doom's DEFAULTLISTMENU
        self.assertEqual(self.screen.getpixel((97 + dx, 72 + dy)), (9, 9, 9, 255))
        gen_menu._put_selector(self.screen, (dot, (2, -1)), (97, 72))   # patch offsets subtract
        self.assertEqual(self.screen.getpixel((97 + dx - 2, 72 + dy + 1)), (9, 9, 9, 255))
        gen_menu._put_selector(self.screen, (dot, (0, 0)), (10, 2))     # clamped to the screen
        self.assertEqual(self.screen.getpixel((0, 0)), (9, 9, 9, 255))


class MenudefGeometryTests(unittest.TestCase):
    """gen_menu's "Engine geometry (src/lumps/MENUDEF, MOD-SPEC 6.6)"."""

    def test_main_menu_geometry_is_menudefs(self):
        body = listmenu("MainMenu")
        self.assertEqual(first_pair(body, "StaticPatch"), gen_menu.LOGO_POS)
        self.assertEqual(first_pair(body, "Position"), gen_menu.MAIN_POS)
        self.assertEqual(first_int(body, "LineSpacing"), gen_menu.MAIN_SPACING)

    def test_skill_screen_logo_and_spacing_are_menudefs(self):
        body = listmenu("SkillMenu")
        self.assertEqual(first_pair(body, "StaticPatch"), gen_menu.LOGO_POS)
        self.assertEqual(first_int(body, "LineSpacing"), gen_menu.SKILL_SPACING)

    @unittest.expectedFailure
    def test_suggested_skill_layout_is_the_one_menudef_ships(self):
        """B4 (docs/qa/COVERAGE.md): MENUDEF moved the header and the rungs
        to x = 32 (rung 5 is 288 px: 32 + 288 = 320), gen_menu still mocks
        them at x = 48, so a regenerated sheet shows a layout the game does
        not have and reports rung 5 overflowing to x = 336. Remove the
        marker when SUGGEST_HEADER / SUGGEST_ITEMS follow MENUDEF."""
        body = listmenu("SkillMenu")
        self.assertEqual((first_pair(body, "StaticText"), first_pair(body, "Position")),
                         (gen_menu.SUGGEST_HEADER, gen_menu.SUGGEST_ITEMS))


@fonts
class MockScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.col = gen_menu._colours()
        cls.menu_font = gen_menu.FolderFont(SDMENU)
        cls.small_font = gen_menu.FolderFont(gen_menu.SMALLFONT_DIR)
        cls.skull = gen_menu._skull()
        with Image.open(gen_menu.M_DOOM) as im:
            cls.logo = np.asarray(im.convert("RGBA"))

    def logo_drawn(self, screen) -> bool:
        x, y = gen_menu.LOGO_POS
        h, w = self.logo.shape[:2]
        region = np.asarray(screen)[y:y + h, x:x + w]
        opaque = self.logo[..., 3] == 255
        return bool(np.array_equal(region[opaque][:, :3], self.logo[opaque][:, :3]))

    def band_has(self, screen, y0: int, h: int, colour) -> bool:
        a = np.asarray(screen)[y0:y0 + h, :, :3]
        return bool(np.all(a == np.array(colour), axis=2).any())

    def test_main_menu_screens(self):
        for lang in ("en", "ru"):
            with self.subTest(lang=lang):
                screen, over = gen_menu.mock_main(lang, self.menu_font, self.skull, self.col)
                self.assertEqual((screen.size, screen.mode), ((320, 200), "RGBA"))
                self.assertEqual(over, [], "a main-menu line runs off the 320-px screen")
                self.assertTrue(self.logo_drawn(screen))
                y0, sp = gen_menu.MAIN_POS[1], gen_menu.MAIN_SPACING
                self.assertTrue(self.band_has(screen, y0, sp, self.col["gold"]), "item 0 is not selected")
                self.assertFalse(self.band_has(screen, y0 + sp, sp, self.col["gold"]))
                self.assertTrue(self.band_has(screen, y0 + sp, sp, self.col["cream"]))

    def test_english_is_drawn_with_d22_letterforms_russian_untouched(self):
        en = self.menu_font.render("NEW", (255, 255, 255), (0, 0, 0))
        drawn = self.menu_font.render(gen_menu.reads_as("NEW"), (255, 255, 255), (0, 0, 0))
        self.assertTrue(np.array_equal(np.asarray(en), np.asarray(drawn)))
        ru = self.menu_font.render("НОВАЯ", (255, 255, 255), (0, 0, 0))
        big = gen_menu.FolderFont(BIGFONT).render("НОВАЯ", (255, 255, 255), (0, 0, 0))
        self.assertTrue(np.array_equal(np.asarray(ru), np.asarray(big)))

    def test_skill_screens(self):
        for lang in ("en", "ru"):
            stock, _ = gen_menu.mock_skill(lang, "stock", self.menu_font, self.small_font, self.skull, self.col)
            suggest, over = gen_menu.mock_skill(lang, "suggest", self.menu_font, self.small_font,
                                                self.skull, self.col)
            with self.subTest(lang=lang):
                self.assertTrue(self.logo_drawn(suggest), "the suggested layout keeps the logo")
                self.assertFalse(self.logo_drawn(stock), "the stock layout has no logo")
                y0, sp = gen_menu.SUGGEST_ITEMS[1], gen_menu.SKILL_SPACING
                self.assertTrue(self.band_has(suggest, y0 + 2 * sp, sp, self.col["gold"]), "rung 3 not selected")
                self.assertTrue(self.band_has(suggest, y0, sp, self.col["red"]))
                if lang == "ru":
                    self.assertEqual(over, [])

    def test_every_rung_fits_at_menudefs_column(self):
        """MENUDEF: x = 32 is the largest x that keeps rung 5 on screen."""
        x = first_pair(listmenu("SkillMenu"), "Position")[0]
        widths = {}
        for lang in ("en", "ru"):
            for rung in gen_menu.SKILL_ITEMS[lang]:
                widths[rung] = self.small_font.width(rung)
                with self.subTest(rung=rung):
                    self.assertLessEqual(x + widths[rung], SCREEN_W)
        self.assertEqual(x + max(widths.values()), SCREEN_W, "x = 32 is no longer the tight column")


@fonts
class SheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        real_mocks = sorted(gen_menu.OUT_ROOT.glob("MENUMOCK_*.png"))
        cls.before = {p: p.stat().st_mtime_ns for p in real_mocks}
        with mock.patch.object(gen_menu, "OUT_ROOT", cls.tmp):
            cls.path = gen_menu.sheet("2099-01-02_0304", font_dir=SDMENU, out_dir=cls.tmp / "previews")
        cls.after = {p: p.stat().st_mtime_ns for p in real_mocks}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_sweep_is_written_where_asked(self):
        self.assertEqual(self.path, self.tmp / "previews" / "2099-01-02_0304_F2_menu-sweep.png")
        with Image.open(self.path) as im:
            self.assertEqual(im.mode, "RGB")
            pad, z = 28, gen_menu.ZOOM
            self.assertEqual(im.width, pad * 3 + 2 * 320 * z + 320 + 20)
            self.assertGreater(im.height, 3 * 200 * z)

    def test_the_main_menu_mocks_are_the_mock_screens(self):
        col = gen_menu._colours()
        font = gen_menu.FolderFont(SDMENU)
        skull = gen_menu._skull()
        for lang in ("en", "ru"):
            with self.subTest(lang=lang):
                with Image.open(self.tmp / f"MENUMOCK_main_{lang}.png") as im:
                    self.assertEqual((im.size, im.mode), ((320, 200), "RGB"))
                    got = np.asarray(im)
                want = np.asarray(gen_menu.mock_main(lang, font, skull, col)[0].convert("RGB"))
                self.assertTrue(np.array_equal(got, want))

    def test_work_was_not_touched(self):
        self.assertEqual(self.before, self.after)


class MainCliTests(unittest.TestCase):
    """The usage lines of the module docstring, with the three actions mocked."""

    def run_main(self, *argv: str):
        out = io.StringIO()
        with mock.patch.object(gen_menu, "build_font", return_value={"font": "sdmenu"}) as bf, \
                mock.patch.object(gen_menu, "install", return_value=Path("installed")) as inst, \
                mock.patch.object(gen_menu, "sheet", return_value=Path("sheet.png")) as sh, \
                mock.patch.object(sys, "argv", ["gen_menu.py", *argv]), \
                contextlib.redirect_stdout(out):
            gen_menu.main()
        return bf, inst, sh, out.getvalue()

    def test_default_builds_the_font_and_the_sheet(self):
        bf, inst, sh, printed = self.run_main()
        bf.assert_called_once_with()
        inst.assert_not_called()
        sh.assert_called_once_with("PREVIEW")
        self.assertIn("sdmenu", printed)

    def test_install_and_stamp(self):
        _, inst, sh, printed = self.run_main("--install", "--stamp", "2026-10-13_1552")
        inst.assert_called_once_with()
        sh.assert_called_once_with("2026-10-13_1552")
        self.assertIn("installed:", printed)

    def test_no_sheet(self):
        bf, _, sh, _ = self.run_main("--no-sheet")
        bf.assert_called_once_with()
        sh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
