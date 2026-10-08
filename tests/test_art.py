"""Art pipeline checks: palette limits and batch-1 texture contract.

Run:  .venv/bin/python -m unittest tests.test_art -v
(The system python3 may lack Pillow/numpy; those tests are then skipped,
the palette JSON checks always run.)
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover
    HAVE_IMAGING = False

LUMP_RE = re.compile(r"^SD[A-Z0-9]{1,6}$")
DIMENSION_MULTIPLE = 8


class PaletteJsonTests(unittest.TestCase):
    def setUp(self):
        self.pal = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))

    def test_at_most_256_unique_colours(self):
        cols = [tuple(c) for c in self.pal["colours"]]
        self.assertLessEqual(len(cols), 256)
        self.assertEqual(len(cols), len(set(cols)))
        self.assertEqual(len(cols), self.pal["count"])

    def test_ramps_are_monotonic_in_luminance(self):
        for ramp in self.pal["ramps"]:
            lum = [sum(c) for c in ramp["colours"]]
            self.assertEqual(lum, sorted(lum), ramp["name"])

    def test_palette_matches_generator(self):
        import palette as palette_cli
        self.assertEqual(palette_cli.build_palette()["colours"], self.pal["colours"])


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class Batch1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        from artlib import quantize
        from PIL import Image
        cls.gen = gen
        cls.built = {}
        for lump, builder, kind, *_ in gen.TEXTURES:
            rgb = builder()
            cls.built[lump] = (kind, rgb, quantize(Image.fromarray(rgb, "RGB")))

    def test_batch_size_within_rules(self):
        self.assertTrue(8 <= len(self.built) <= 12, len(self.built))

    def test_lump_names(self):
        for lump in self.built:
            self.assertRegex(lump, LUMP_RE)
            self.assertLessEqual(len(lump), 8)

    def test_dimensions(self):
        for lump, (kind, rgb, _) in self.built.items():
            h, w = rgb.shape[:2]
            self.assertEqual(w % DIMENSION_MULTIPLE, 0, lump)
            self.assertEqual(h % DIMENSION_MULTIPLE, 0, lump)
            if kind == "flat":
                self.assertEqual((w, h), (64, 64), lump)
            else:
                self.assertIn((w, h), [(64, 128), (128, 128)], lump)

    def test_quantised_colours_are_palette_subset(self):
        pal = {tuple(c) for c in json.loads(PALETTE_JSON.read_text())["colours"]}
        for lump, (_, _, img) in self.built.items():
            p = img.getpalette()
            used = {tuple(p[i * 3:i * 3 + 3]) for i in set(img.get_flattened_data())}
            self.assertTrue(used <= pal, f"{lump}: {used - pal}")
            self.assertLessEqual(len(used), 256)

    def test_deterministic(self):
        import numpy as np
        lump, builder, *_ = self.gen.TEXTURES[0]
        self.assertTrue(np.array_equal(builder(), self.built[lump][1]))


if __name__ == "__main__":
    unittest.main()
