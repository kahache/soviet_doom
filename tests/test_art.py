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


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class EmblemGeometryTests(unittest.TestCase):
    """SDSTAR1 v3: the hammer and sickle follow the CEO's reference, not its
    mirror image (the v2 mistake). Points are in the unit square of
    gen_soviet_base (origin top-left, y down); every GOLD point has a RED
    twin at the position the mirrored layout would paint, so a flipped
    emblem fails."""

    BOX = 256
    GOLD, RED = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)  # filled in setUpClass
    # (gold point, its red twin)
    PAIRS = [
        ((0.23, 0.50), (0.77, 0.50)),   # hammer head sits mid-LEFT, never mid-right
        ((0.38, 0.33), (0.62, 0.33)),   # blade sweeps over the head on the left
        ((0.62, 0.18), (0.38, 0.18)),   # top of the crescent leans right
        ((0.91, 0.52), (0.09, 0.52)),   # blade mass hugs the right edge
        ((0.78, 0.71), (0.22, 0.71)),   # hammer handle runs down to the RIGHT
    ]

    @classmethod
    def setUpClass(cls):
        import numpy as np
        import gen_soviet_base as gen
        from artlib import Overlay, ramp_colour
        cls.gen = gen
        cls.gold = np.array(ramp_colour("hazard_yellow", 0.88), dtype=float)
        cls.red = np.array(ramp_colour("flag_red", 0.70), dtype=float)
        bg = np.full((cls.BOX, cls.BOX, 3), cls.red, dtype=np.uint8)
        ov = Overlay(cls.BOX, cls.BOX)
        gen.hammer_sickle(ov, cls.BOX / 2, cls.BOX / 2, cls.BOX / 2,
                          tuple(int(c) for c in cls.gold), ramp_colour("flag_red", 0.25))
        cls.img = ov.composite(bg).astype(float)

    def _is_gold(self, u, v):
        import numpy as np
        px = self.img[int(v * self.BOX), int(u * self.BOX)]
        return np.linalg.norm(px - self.gold) < np.linalg.norm(px - self.red)

    def test_layout_matches_reference_not_mirror(self):
        for gold_pt, red_pt in self.PAIRS:
            self.assertTrue(self._is_gold(*gold_pt), f"expected gold at {gold_pt}")
            self.assertFalse(self._is_gold(*red_pt), f"expected red at {red_pt}")

    def test_hammer_head_clears_sickle_tip(self):
        import numpy as np
        g = self.gen
        c = np.array(g.HAMMER_HEAD_C)
        hs, he = (np.array(p) for p in g.HAMMER_HANDLE)
        hd = (he - hs) / np.linalg.norm(he - hs)
        hn = np.array([-hd[1], hd[0]])
        d = np.array(g.SICKLE_TIP) - c
        over = np.array([max(0.0, abs(d @ hn) - g.HAMMER_HEAD_L / 2),
                         max(0.0, abs(d @ hd) - g.HAMMER_HEAD_W / 2)])
        self.assertGreaterEqual(np.linalg.norm(over), g.HAMMER_TIP_CLEARANCE)

    def test_hammer_butt_reaches_bottom_right_corner(self):
        """CEO 2026-10-12: the butt of the hammer handle must reach the
        bottom-right corner, mirroring the sickle handle end at the
        bottom-left. Both ends are checked against each other so the pair
        stays symmetric if either is retuned."""
        import numpy as np
        g = self.gen
        butt = np.array(g.HAMMER_HANDLE[1])
        sickle_end = np.array(g.SICKLE_HANDLE[1])
        self.assertGreater(butt[0], 0.88)      # hard against the right edge
        self.assertGreater(butt[1], 0.92)      # and against the bottom
        mirrored = np.array([1.0 - sickle_end[0], sickle_end[1]])
        self.assertLess(float(np.linalg.norm(butt - mirrored)), 0.06)

    def test_hammer_handle_slope(self):
        """~41 deg since variant D1 (CEO 2026-10-12): the head moved down to
        mid-height, so the run to the fixed bottom-right butt is flatter."""
        import numpy as np
        hs, he = (np.array(p) for p in self.gen.HAMMER_HANDLE)
        self.assertGreater(he[0], hs[0])   # to the right
        self.assertGreater(he[1], hs[1])   # downwards (y down)
        slope = np.degrees(np.arctan2(he[1] - hs[1], he[0] - hs[0]))
        self.assertAlmostEqual(slope, 41.0, delta=3.0)


ASSETS_DIR = PROJECT_ROOT / "assets"
WORK_ART_DIR = PROJECT_ROOT / "work" / "art"
FLAT_SIZE = (64, 64)
WALL_SIZES = [(64, 128), (128, 128), (128, 256)]   # 128x256 added for the Lenin poster (D18 era)


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class ApprovedAssetsTests(unittest.TestCase):
    """assets/ holds only CEO-approved PNGs, copied byte for byte from work/
    (gitignored). The identity check is skipped where work/ does not exist
    (fresh clone, CI); the layout checks always run."""

    def setUp(self):
        self.pngs = sorted(ASSETS_DIR.rglob("*.png")) if ASSETS_DIR.is_dir() else []

    # Screens the engine names itself. They are the documented exception to
    # the SD prefix (MOD-SPEC 1) and to the indexed-PNG rule: M_DOOM is a menu
    # patch and needs an alpha channel, hard 0/255 (LICENSES.md, D18).
    SHELL_SIZES = {"TITLEPIC": (320, 200), "INTERPIC": (320, 200), "M_DOOM": (200, 64)}

    def test_layout_names_and_sizes(self):
        from PIL import Image
        for p in self.pngs:
            kind = p.relative_to(ASSETS_DIR).parts[0]
            self.assertIn(kind, ("textures", "flats", "graphics", "fonts"), p)
            with Image.open(p) as img:
                if kind == "fonts":
                    # A folder font is fonts/<fontname>/<HEX>.png and the
                    # engine identifies the glyph by that hex name. Sizes vary
                    # per glyph by design, so only the naming and the folder
                    # are a contract here.
                    folder = p.relative_to(ASSETS_DIR).parts[1]
                    self.assertIn(folder, ("defsmallfont", "bigfont"), p)
                    self.assertRegex(p.stem, r"^[0-9A-Fa-f]{4}$",
                                     f"{p}: a glyph is named by its codepoint in hex")
                    self.assertLessEqual(max(img.size), 32, p)
                    continue
                if kind == "graphics":
                    self.assertIn(p.stem, self.SHELL_SIZES,
                                  f"{p}: unexpected shell lump; the engine fixes these names")
                    self.assertEqual(img.size, self.SHELL_SIZES[p.stem], p)
                    self.assertIn(img.mode, ("P", "RGBA"), p)
                    if img.mode == "RGBA":
                        alpha = set(img.getchannel("A").getdata())
                        self.assertTrue(alpha <= {0, 255},
                                        f"{p}: alpha must be hard 0/255, found {sorted(alpha)[:6]}")
                    continue
                self.assertRegex(p.stem, LUMP_RE)
                self.assertEqual(img.mode, "P", p)
                if kind == "flats":
                    self.assertEqual(img.size, FLAT_SIZE, p)
                else:
                    self.assertIn(img.size, WALL_SIZES, p)

    def test_identical_to_work_source(self):
        if not WORK_ART_DIR.is_dir():
            self.skipTest("work/ not present (gitignored work-in-progress)")
        for p in self.pngs:
            sources = list(WORK_ART_DIR.rglob(p.name))
            if p.relative_to(ASSETS_DIR).parts[0] == "fonts":
                # Every font variant generates the same codepoint filenames,
                # so a bare name matches A, B and C at once. What matters is
                # that the installed glyph is byte-identical to the same glyph
                # of exactly one generated variant - we do not pin which, so
                # the CEO can change his mind without editing a test.
                folder = p.relative_to(ASSETS_DIR).parts[1]
                same = [q for q in sources if q.parent.name == folder]
                self.assertTrue(same, f"{p}: no generated source under work/")
                self.assertTrue(any(q.read_bytes() == p.read_bytes() for q in same),
                                f"{p}: matches no generated variant")
                continue
            if not sources:
                # Some assets are RENAMED on the way in, because the generator
                # names by variant and the engine names by role: the shell
                # screens (TITLEPIC_A -> TITLEPIC, D18) and the switches
                # (SDSWT_B_off -> SDSW1B). The contract is still that nothing
                # reaches assets/ that the pipeline did not produce, so the
                # bytes must match some generated file even when the name does
                # not.
                blob = p.read_bytes()
                self.assertTrue(
                    any(q.read_bytes() == blob for q in WORK_ART_DIR.rglob("*.png")),
                    f"{p}: matches no file generated under work/")
                continue
            self.assertEqual(len(sources), 1, f"{p.name}: expected one source in work/, got {sources}")
            self.assertEqual(p.read_bytes(), sources[0].read_bytes(), f"{p} differs from {sources[0]}")


if __name__ == "__main__":
    unittest.main()
