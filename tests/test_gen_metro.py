"""Contract of tools/art/gen_metro.py and of the metro set in assets/ (D42).

The CEO approved the metro's first six pieces as drawn in palette v1
(D42, 2026-10-13: «OK a las 6 piezas de metro»). What is checked:

  installed   assets/textures/metro/ and assets/flats/metro/ hold exactly the
              approved lumps, at the declared sizes, indexed PNGs
  generator   each installed lump is pixel-identical to what gen_metro.py
              builds from its seed today, so a later edit of the generator
              (the set is being filled out) cannot silently drift away from
              the approved art
  no font     the generator never rasterises text with a system font, which
              is why its lumps reproduce byte for byte on the Mac and on
              Windows (CLAUDE.md, "Text-bearing assets do not reproduce")
  paper       every installed lump has an approved row in TEXTURE-INDEX.md
              and a row in LICENSES.md

All of it is cheap: the six builders run in well under a second, so nothing
here is gated behind SD_SKIP_SLOW_ART.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
ASSETS = PROJECT_ROOT / "assets"
METRO_WALLS = ASSETS / "textures" / "metro"
METRO_FLATS = ASSETS / "flats" / "metro"
TEXTURE_INDEX = PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

# D42: the six approved pieces, lump -> (kind, width, height).
APPROVED_D42 = {
    "SDTILE1": ("wall", 64, 128),
    "SDTILE2": ("wall", 64, 128),
    "SDMARB1": ("wall", 64, 128),
    "SDMOSA1": ("wall", 128, 128),
    "SDBRAS1": ("wall", 64, 128),
    "SDMFLR1": ("flat", 64, 64),
}
D42_BATCH_SEED = 1935
INSTALLED = dict(APPROVED_D42)      # every metro lump in assets/, approved


def installed_files() -> dict[str, Path]:
    out = {}
    for base in (METRO_WALLS, METRO_FLATS):
        if base.is_dir():
            for p in sorted(base.glob("*.png")):
                out[p.stem] = p
    return out


class NoFontTests(unittest.TestCase):
    def test_generator_uses_no_system_font(self):
        src = (ART_TOOLS / "gen_metro.py").read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", src, flags=re.S)       # docstrings may talk about fonts
        for banned in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text(", "truetype"):
            self.assertNotIn(banned, code, banned)


class PaperTrailTests(unittest.TestCase):
    def test_every_installed_lump_is_indexed_as_approved(self):
        text = TEXTURE_INDEX.read_text(encoding="utf-8")
        for lump in INSTALLED:
            rows = [ln for ln in text.splitlines() if ln.startswith(f"| `{lump}` |")]
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in TEXTURE-INDEX.md")
            status = rows[0].split("|")[7]
            self.assertIn("approved", status, f"{lump}: {status.strip()}")

    def test_every_installed_lump_has_a_licence_row(self):
        text = LICENSES.read_text(encoding="utf-8")
        for lump in INSTALLED:
            self.assertIn(f"`{lump}`", text, lump)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class InstalledMetroTests(unittest.TestCase):
    def test_exactly_the_approved_lumps_are_installed(self):
        self.assertEqual(set(installed_files()), set(INSTALLED))

    def test_walls_and_flats_in_their_folders(self):
        files = installed_files()
        for lump, (kind, _, _) in INSTALLED.items():
            folder = METRO_FLATS if kind == "flat" else METRO_WALLS
            self.assertEqual(files[lump].parent, folder, lump)

    def test_sizes_and_indexed(self):
        from PIL import Image
        for lump, path in installed_files().items():
            _, w, h = INSTALLED[lump]
            with Image.open(path) as img:
                self.assertEqual(img.size, (w, h), lump)
                self.assertEqual(img.mode, "P", lump)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class GeneratorHoldsApprovedArtTests(unittest.TestCase):
    """Rebuild each approved lump from its seed and compare pixels with the
    installed file. Pixels, not bytes: PNG encoding is not the contract, the
    image is."""

    @classmethod
    def setUpClass(cls):
        import gen_metro
        cls.g = gen_metro
        cls.builders = {lump: builder for lump, builder, *_ in gen_metro.TEXTURES}

    def test_d42_seeds_unchanged(self):
        self.assertEqual(self.g.BATCH_SEED, D42_BATCH_SEED)
        expected = {"SDTILE1": 1, "SDTILE2": 2, "SDMARB1": 3,
                    "SDMOSA1": 4, "SDBRAS1": 5, "SDMFLR1": 6}
        for lump, offset in expected.items():
            self.assertEqual(self.g.SEED_OFFSET[lump], offset, lump)

    def test_installed_pixels_match_generator(self):
        import numpy as np
        from PIL import Image
        from artlib import quantize
        for lump, path in installed_files().items():
            built = quantize(Image.fromarray(self.builders[lump](), "RGB")).convert("RGB")
            with Image.open(path) as img:
                shipped = img.convert("RGB")
            a, b = np.asarray(built), np.asarray(shipped)
            self.assertEqual(a.shape, b.shape, lump)
            diff = int((a != b).any(axis=-1).sum())
            self.assertEqual(diff, 0, f"{lump}: {diff} px differ from the approved file")


if __name__ == "__main__":
    unittest.main()
