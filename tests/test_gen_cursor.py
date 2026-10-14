"""Tests for the T12 sweep of the menu cursor and the pause sign
(tools/art/gen_cursor.py). The generator writes to work/ only; these tests
READ assets/ (the menu font, and the three shell lumps the CEO approved in
D48), never write it.

  the pictures   every cursor option has two blink phases of one size that
                 differ; every picture is RGBA, hard alpha, palette colours
                 only (ART-BIBLE 2, the exception for drawn-over assets)
  the geometry   the cursor fits the 32 px the selector leaves left of the
                 text and stays on screen at the skill rungs' x = 32
  the languages  each worded pause option has ONE size for both languages
                 (GZDoom refuses a localised variant of another size) and
                 every letter has a glyph in assets/fonts/sdmenu/
  D27            no system font anywhere in the module, and the build is
                 deterministic; the approved font is read, never rewritten
  the build      build() writes only under the directory it is given
  installed (D48) M_SKULL1/M_SKULL2 are cursor B and M_PAUSE is pause sign
                 P2 in English, byte for byte what the generator saves today

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_cursor -v
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

import gen_cursor  # noqa: E402  (stdlib-only at import time)

PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
SDMENU = PROJECT_ROOT / "assets" / "fonts" / "sdmenu"
SHELL = PROJECT_ROOT / "assets" / "graphics" / "shell"

# D48 (CEO, 2026-10-14): menu cursor B and pause sign P2, a plaque per
# language. Only the English plaque is installed: the Russian one waits on
# the packer's localized/ support (MOD-SPEC 10, T12).
APPROVED_CURSOR = "B"
APPROVED_PAUSE = ("P2", "en")

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter without Pillow
    HAVE_IMAGING = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not installed")
font = unittest.skipUnless(SDMENU.is_dir(), "assets/fonts/sdmenu/ not installed")


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def folder_hashes(folder: Path) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}


class SourceTests(unittest.TestCase):
    """D27: a system font rasterises differently on the Mac and on Windows,
    so nothing that could reach the game may use one."""

    def test_no_system_font_in_the_module(self):
        src = (ART_TOOLS / "gen_cursor.py").read_text(encoding="utf-8")
        for needle in ("ImageFont", "truetype", "FONT_POSTER", "FONT_SMALL"):
            self.assertNotIn(needle, src)

    def test_does_not_sweep_m_episod(self):
        # D41 replaced M_EPISOD by a text header; the sweep must not bring it back.
        self.assertNotIn("M_EPISOD", json.dumps(gen_cursor.CURSORS) + json.dumps(gen_cursor.PAUSE_OPTIONS))

    def test_blink_matches_the_engine_animdefs(self):
        # gzdoom.pk3 animdefs.txt (g4.14.2): pic M_SKULL1 tics 8 / pic M_SKULL2 tics 8
        self.assertEqual(gen_cursor.BLINK_TICS, 8)
        self.assertEqual(gen_cursor.SELECTOR, (-32, -5))


@imaging
class CursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette = palette_colours()
        cls.imgs = {(o, ph): gen_cursor.cursor_image(o, ph) for o in gen_cursor.CURSORS for ph in (1, 2)}

    def test_five_options(self):
        self.assertEqual(len(gen_cursor.CURSORS), 5)

    def test_phases_same_size_and_different(self):
        for o in gen_cursor.CURSORS:
            with self.subTest(option=o):
                a, b = self.imgs[(o, 1)], self.imgs[(o, 2)]
                self.assertEqual(a.size, b.size)
                self.assertEqual(a.size, (gen_cursor.CURSOR_W, gen_cursor.CURSOR_H))
                self.assertNotEqual(a.tobytes(), b.tobytes(), "the two phases must blink")

    def test_rgba_hard_alpha_palette_only(self):
        for key, img in self.imgs.items():
            with self.subTest(cursor=key):
                self.assertEqual(img.mode, "RGBA")
                a = np.asarray(img)
                self.assertLessEqual(set(np.unique(a[..., 3]).tolist()), {0, 255})
                used = {tuple(int(v) for v in c) for c in a[a[..., 3] == 255][:, :3]}
                self.assertTrue(used, "empty cursor")
                self.assertLessEqual(used, self.palette)

    def test_fits_left_of_the_text_and_on_screen(self):
        # The selector puts the canvas 32 px left of the item; the ink must
        # leave a gap before the text, and at the skill rungs (x = 32) the
        # canvas starts at x = 0, so nothing may be clipped by the screen.
        for key, img in self.imgs.items():
            with self.subTest(cursor=key):
                x0, _y0, x1, _y1 = img.getbbox()
                self.assertLessEqual(x1, gen_cursor.CURSOR_MAX_W)
        self.assertGreaterEqual(gen_cursor.SKILL_CURSOR_AT[0], 0)
        self.assertEqual(gen_cursor.MAIN_CURSOR_AT, (97 - 32, 72 - 5))

    def test_deterministic(self):
        for o in gen_cursor.CURSORS:
            with self.subTest(option=o):
                self.assertEqual(gen_cursor.cursor_image(o, 1).tobytes(), self.imgs[(o, 1)].tobytes())


@imaging
@font
class PauseTests(unittest.TestCase):
    def test_every_letter_has_a_sdmenu_glyph(self):
        for lang, word in gen_cursor.PAUSE_WORDS.items():
            with self.subTest(lang=lang):
                self.assertEqual(gen_cursor.missing_glyphs(word), [])

    def test_worded_options_have_one_size_for_both_languages(self):
        # "Localized texture %s must be the same size as the one it replaces"
        # (gzdoom.exe g4.14.2): the Russian variant must match the English one.
        for opt in ("P2", "P3"):
            with self.subTest(option=opt):
                sizes = {gen_cursor.pause_image(opt, lang).size for lang in gen_cursor.PAUSE_WORDS}
                self.assertEqual(sizes, {gen_cursor.pause_canvas_size(opt)})
                en, ru = (gen_cursor.pause_image(opt, lang) for lang in ("en", "ru"))
                self.assertNotEqual(en.tobytes(), ru.tobytes())

    def test_rgba_hard_alpha_palette_only(self):
        palette = palette_colours()
        for opt in gen_cursor.PAUSE_OPTIONS:
            for lang in gen_cursor.PAUSE_WORDS:
                with self.subTest(option=opt, lang=lang):
                    a = np.asarray(gen_cursor.pause_image(opt, lang))
                    self.assertLessEqual(set(np.unique(a[..., 3]).tolist()), {0, 255})
                    used = {tuple(int(v) for v in c) for c in a[a[..., 3] == 255][:, :3]}
                    self.assertLessEqual(used, palette)

    def test_fits_the_screen(self):
        for opt in gen_cursor.PAUSE_OPTIONS:
            w, _h = gen_cursor.pause_canvas_size(opt)
            self.assertLessEqual(w, gen_cursor.SCREEN[0])


@imaging
@font
class BuildTests(unittest.TestCase):
    def test_build_writes_only_its_directory_and_leaves_the_font_alone(self):
        before = folder_hashes(SDMENU)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "shell_extra"
            manifest = gen_cursor.build(out)
            written = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
            self.assertEqual(written, set(manifest["files"]) | {"manifest.json"})
            for o in gen_cursor.CURSORS:
                self.assertIn(f"cursor_{o}_1.png", written)
                self.assertIn(f"cursor_{o}_2.png", written)
            for opt in ("P2", "P3"):
                for lang in ("en", "ru"):
                    self.assertIn(f"pause_{opt}_{lang}.png", written)
            self.assertIn("pause_P1_xx.png", written)
            # every generated name is unique across the tree, so a later
            # install (renamed to M_SKULL1/M_PAUSE) cannot match two sources
            # in tests/test_art.py's identity check
            names = [Path(w).name for w in written if w.endswith(".png") and not w.startswith("context/")]
            self.assertEqual(len(names), len(set(names)))
            lumps = {"M_SKULL1.png", "M_SKULL2.png", "M_PAUSE.png", "M_DOOM.png", "TITLEPIC.png"}
            self.assertFalse({Path(w).name for w in written} & lumps,
                             "no work file may carry a shell lump's name")
        self.assertEqual(folder_hashes(SDMENU), before)


def png_bytes(img) -> bytes:
    """The bytes build() writes for a picture: Pillow PNG, optimize=True."""
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@imaging
@font
@unittest.skipUnless((SHELL / "M_SKULL1.png").is_file(), "D48 shell lumps not installed")
class InstalledShellTests(unittest.TestCase):
    """D48: the PM copied cursor_B_1/2.png and pause_P2_en.png into assets/
    under the engine's names. The installed bytes must be exactly what the
    generator saves today for B and P2, so a later edit of gen_cursor.py
    cannot drift away from the approved art unnoticed."""

    def test_cursor_b_is_m_skull(self):
        for phase in (1, 2):
            with self.subTest(phase=phase):
                built = png_bytes(gen_cursor.cursor_image(APPROVED_CURSOR, phase))
                self.assertEqual((SHELL / f"M_SKULL{phase}.png").read_bytes(), built)

    def test_pause_p2_en_is_m_pause(self):
        built = png_bytes(gen_cursor.pause_image(*APPROVED_PAUSE))
        self.assertEqual((SHELL / "M_PAUSE.png").read_bytes(), built)


if __name__ == "__main__":
    unittest.main()
