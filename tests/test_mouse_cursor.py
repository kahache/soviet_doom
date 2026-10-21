"""D102 (v1.1): the mouse pointer is our hammer and sickle, SDCURSOR.

Contract: docs/engine/MOD-SPEC.md 6.6.1. Not the menu selector M_SKULL1/2
(tests/test_gen_cursor.py). What is pinned here, without starting GZDoom
(D26):

  * MAPINFO's GameInfo names the picture with CursorPic, once;
  * the asset is where the build packs it as graphics/SDCURSOR.png;
  * the engine's limits (g4.14.2 source, quoted in tools/art/gen_mouse_cursor.py):
    at most 32x32 (win32 I_SetCursor), RGBA with hard alpha, and a grAb
    chunk, which is the hot spot on Windows;
  * the hot spot is the sickle's tip: an opaque pixel of the sickle's gold,
    in the picture's top rows;
  * the generator, which uses no font, reproduces the installed pixels and
    offsets (skipped without Pillow/numpy, as in a bare CI interpreter).

What it cannot pin is what the window shows: the PM's engine pass.

Run:  python3 -m unittest tests.test_mouse_cursor -v
"""

from __future__ import annotations

import re
import struct
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "art"))

from sdbuild.pk3 import collect_assets  # noqa: E402

MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
ASSETS = PROJECT_ROOT / "assets"
ASSET = ASSETS / "graphics" / "shell" / "SDCURSOR.png"
PACKED = "graphics/SDCURSOR.png"
LUMP = "SDCURSOR"
MAX_SIZE = 32                 # win32 I_SetCursor: "Must be no larger than 32x32"
TIP_MAX_ROW = 2               # the tip sits under its own contour, near the top
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RGBA_COLOUR_TYPE = 6

try:
    import numpy  # noqa: F401  (gen_soviet_base, whose geometry the generator imports)
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - bare interpreter
    HAVE_IMAGING = False


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def gameinfo_block(text: str) -> str:
    match = re.search(r"(?im)^\s*GameInfo\s*\{(.*?)^\s*\}", text, re.S)
    assert match, "MAPINFO has no GameInfo block"
    return match.group(1)


def png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    assert data[:8] == PNG_SIGNATURE
    chunks, i = [], 8
    while i < len(data):
        (length,) = struct.unpack(">I", data[i:i + 4])
        kind = data[i + 4:i + 8]
        chunks.append((kind, data[i + 8:i + 8 + length]))
        i += 12 + length
    return chunks


def pixels(img) -> list:
    """Pillow >= 12 renamed getdata (deprecated) to get_flattened_data."""
    flat = getattr(img, "get_flattened_data", None)
    return list(flat() if flat else img.getdata())


def grab_of(data: bytes) -> tuple[int, int] | None:
    for kind, body in png_chunks(data):
        if kind == b"grAb":
            return struct.unpack(">ii", body)
    return None


class MapinfoTest(unittest.TestCase):
    def test_gameinfo_names_the_cursor_once(self):
        text = strip_comments(MAPINFO.read_text(encoding="utf-8"))
        everywhere = re.findall(r'(?im)^\s*CursorPic\s*=\s*"([^"]*)"', text)
        self.assertEqual(everywhere, [LUMP])
        self.assertRegex(gameinfo_block(text), rf'(?im)^\s*CursorPic\s*=\s*"{LUMP}"\s*$')


class AssetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ASSET.read_bytes()
        cls.chunks = png_chunks(cls.data)

    def test_packed_where_the_engine_finds_it(self):
        self.assertIn(PACKED, {e.path for e in collect_assets(ASSETS)})

    def test_within_the_engine_size_and_rgba(self):
        kind, ihdr = self.chunks[0]
        self.assertEqual(kind, b"IHDR")
        width, height, depth, colour_type = struct.unpack(">IIBB", ihdr[:10])
        self.assertLessEqual(width, MAX_SIZE)
        self.assertLessEqual(height, MAX_SIZE)
        self.assertEqual((depth, colour_type), (8, RGBA_COLOUR_TYPE))

    def test_grab_comes_before_the_image_data_and_lies_inside(self):
        kinds = [k for k, _ in self.chunks]
        self.assertIn(b"grAb", kinds)
        self.assertLess(kinds.index(b"grAb"), kinds.index(b"IDAT"))
        width, height = struct.unpack(">II", self.chunks[0][1][:8])
        x, y = grab_of(self.data)
        self.assertTrue(0 <= x < width and 0 <= y <= TIP_MAX_ROW, (x, y))
        self.assertLess(y, height)


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class PixelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_mouse_cursor
        cls.gen = gen_mouse_cursor
        with Image.open(ASSET) as img:
            cls.img = img.convert("RGBA")
        cls.grab = grab_of(ASSET.read_bytes())

    def test_hard_alpha(self):
        self.assertEqual(set(pixels(self.img.getchannel("A"))), {0, 255})

    def test_only_the_generators_colours(self):
        g = self.gen
        allowed = {g.SICKLE_FILL, g.HAMMER_FILL, g.SHADE, g.CONTOUR}
        used = {px[:3] for px in pixels(self.img) if px[3] == 255}
        self.assertLessEqual(used, allowed)

    def test_the_hot_spot_is_the_sickle_tip(self):
        r, g, b, a = self.img.getpixel(self.grab)
        self.assertEqual(a, 255)
        self.assertIn((r, g, b), (self.gen.SICKLE_FILL, self.gen.SHADE))
        # The tip is the topmost gold of the sickle at its column's left end:
        # nothing gold above it, its contour right above.
        x, y = self.grab
        self.assertEqual(self.img.getpixel((x, y - 1))[:3], self.gen.CONTOUR)

    def test_the_contour_reaches_every_edge_of_the_picture(self):
        """Cropped tight: the picture is the drawing plus its 1 px contour."""
        w, h = self.img.size
        alpha = self.img.getchannel("A")
        self.assertTrue(any(alpha.getpixel((x, 0)) for x in range(w)))
        self.assertTrue(any(alpha.getpixel((x, h - 1)) for x in range(w)))
        self.assertTrue(any(alpha.getpixel((0, y)) for y in range(h)))
        self.assertTrue(any(alpha.getpixel((w - 1, y)) for y in range(h)))

    def test_the_generator_reproduces_the_asset(self):
        img, hot = self.gen.render()
        self.assertEqual(hot, self.grab)
        self.assertEqual(img.size, self.img.size)
        self.assertEqual(pixels(img), pixels(self.img))

    def test_the_generator_uses_no_font(self):
        source = (TOOLS / "art" / "gen_mouse_cursor.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"ImageFont|truetype|FONT_")


if __name__ == "__main__":
    unittest.main()
