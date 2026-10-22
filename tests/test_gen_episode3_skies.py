"""Contract of Episode 3's skies (P4, D113): tools/art/gen_episode3_skies.py.

SDSKY3 (MAP07, the polar night with aurora), SDSKY4 (MAP08, the Kola fjord
at night) and SDSKY5 (MAP09, the Tunguska taiga with the portal's glow).
Approved under D113's standing approval (the CEO approves procedural
textures in advance) and installed in assets/textures/sky/. What is held:

  format     1024x128 indexed, the SDSKY1/2 contract (check_pk3 SKY_SIZES);
             the horizon row is gen_episode2b's; one turn that wraps in x
  seeds      6000 + offset (the index's seed note), one per sky
  no font    the generator never rasterises a system font (D27)
  writes     PNGs to work/art/episode3_skies/, the preview to docs/art/
             previews/; assets/ is only read
  palette    SDSKY3/4 v1 only; SDSKY5 v1 plus mosaic_cobalt, and the cobalt
             only near the portal; never gold or flesh
  looks      dark zenith; the aurora's green above the horizon in SDSKY3;
             the lighthouse's white lamp and red lights in SDSKY4; no stars
             below the horizon
  installed  assets/ holds the generator's bytes; one approved row each in
             TEXTURE-INDEX.md and LICENSES.md; MAPINFO sky1 of MAP07-09
  repeat     two renders are identical

Text checks run at every tier; the renders skip when SD_SKIP_SLOW_ART is set.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
SOURCE = ART_TOOLS / "gen_episode3_skies.py"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode3-skies.png"
LUMPS = ("SDSKY3", "SDSKY4", "SDSKY5")
MAP_SKIES = {"MAP07": "SDSKY3", "MAP08": "SDSKY4", "MAP09": "SDSKY5"}
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import ep2lib
    import gen_episode2b
    import gen_episode3_skies as g
    import palette as palgen
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the sky renders")
needs_imaging = unittest.skipUnless(HAVE_IMAGING, "numpy/Pillow not available")

SEAM_LIMIT = 1.25


def axis_seam(rgb, axis: int) -> float:
    a = rgb[..., :3].astype(float)
    interior = np.abs(np.diff(a, axis=axis)).mean(axis=(1 - axis, 2)).max()
    wrap = np.abs(a[0] - a[-1]).mean() if axis == 0 else np.abs(a[:, 0] - a[:, -1]).mean()
    return float(wrap / max(interior, 1e-6))


def luma(a):
    a = a[..., :3].astype(float)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


class SourceTests(unittest.TestCase):
    def test_no_system_font(self):
        text = SOURCE.read_text(encoding="utf-8")
        for token in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text("):
            self.assertNotIn(token, text, f"uses {token}: no system font (D27)")

    def test_never_writes_assets(self):
        for line in SOURCE.read_text(encoding="utf-8").splitlines():
            if re.search(r"\.(save|write_text|write_bytes|mkdir)\(", line):
                self.assertNotRegex(line, r"ASSETS|['\"]assets['\"]", line.strip())

    def test_does_not_edit_the_shared_modules(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertNotRegex(text, re.compile(r"^\s*(ep2lib|e2b|gen_episode2b|gen_metro)\.\w+\s*=", re.M))

    def test_preview_exists(self):
        self.assertTrue(PREVIEW.is_file(), PREVIEW)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def test_lumps(self):
        self.assertEqual(list(LUMPS), g.all_lumps())

    def test_the_sdsky1_2_format(self):
        self.assertEqual((1024, 128), g.SKY_SIZE)
        self.assertEqual(gen_episode2b.SKY_SIZE, g.SKY_SIZE)
        self.assertEqual(gen_episode2b.HORIZON, g.HORIZON)
        for p in g.PIECES:
            self.assertEqual("sky", p.kind, p.key)
            self.assertEqual(g.SKY_SIZE, p.size, p.key)
            self.assertEqual("x", p.tiles, p.key)

    def test_seeds(self):
        self.assertEqual(6000, g.BATCH_SEED)
        offsets = [p.offset for p in g.PIECES]
        self.assertEqual(len(offsets), len(set(offsets)))

    def test_palette_versions(self):
        ramps = {p.key: p.ramps for p in g.PIECES}
        self.assertEqual({"SDSKY3": (), "SDSKY4": (), "SDSKY5": ("mosaic_cobalt",)}, ramps)
        self.assertTrue(next(p for p in g.PIECES if p.key == "SDSKY5").why_v2)


@needs_imaging
@slow
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.entries, cls.A = g.build_all(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def path(self, lump: str) -> Path:
        return self.root / g.SET_NAME / f"{lump}.png"

    def test_names(self):
        """Not used anywhere else (scans assets/ and work/, hence slow)."""
        self.assertEqual([], g.name_problems())

    def test_files_sizes_and_modes(self):
        for lump in LUMPS:
            with Image.open(self.path(lump)) as im:
                self.assertEqual((1024, 128), im.size, lump)
                self.assertEqual("P", im.mode, lump)

    def test_palette_membership(self):
        gold_flesh = {tuple(c) for r in ("mosaic_gold", "flesh_pink") for c in palgen.ramp_colours(r)}
        for p in g.PIECES:
            a = self.A[p.key]
            used = {tuple(int(v) for v in c) for c in np.unique(a[..., :3].reshape(-1, 3), axis=0)}
            allowed = set(g.allowed_colours(p.ramps))
            self.assertLessEqual(used, allowed, f"{p.key} leaves its palette: {sorted(used - allowed)[:5]}")
            self.assertFalse(used & gold_flesh - {(0, 0, 0)}, f"{p.key} uses gold or flesh")

    def test_cobalt_only_near_the_portal(self):
        cobalt = {tuple(c) for c in palgen.ramp_colours("mosaic_cobalt")}
        a = self.A["SDSKY5"][..., :3]
        is_cobalt = np.array([[tuple(int(v) for v in px) in cobalt for px in row] for row in a])
        cols = np.flatnonzero(is_cobalt.any(0))
        self.assertGreater(int(is_cobalt.sum()), 1500, "the portal's glow should be cobalt")
        far = np.abs(ep2lib.wrap_dist(cols - g.PORTAL_X, 1024)) > g.PORTAL_REACH
        self.assertFalse(far.any(), "cobalt away from the portal")

    def test_wraps_round_the_turn(self):
        for lump in LUMPS:
            self.assertLessEqual(axis_seam(self.A[lump], 1), SEAM_LIMIT, lump)

    def test_dark_zenith_and_no_stars_below_the_horizon(self):
        for lump in LUMPS:
            lum = luma(self.A[lump])
            self.assertLess(lum[:20].mean(), lum[70:g.HORIZON].mean(), f"{lump}: the zenith should be darker")
        star = np.array(ep2lib.col("cream_yellow", 0.96))
        for lump in ("SDSKY3", "SDSKY5"):
            low = self.A[lump][g.HORIZON:, :, :3]
            self.assertEqual(0, int((low == star).all(-1).sum()), f"{lump}: a star below the horizon")

    def test_aurora(self):
        green = {tuple(c) for c in palgen.ramp_colours("military_green")}
        a = self.A["SDSKY3"][:g.HORIZON - 20, :, :3]
        n = sum(tuple(int(v) for v in px) in green for px in a.reshape(-1, 3))
        self.assertGreater(n, 2000, "SDSKY3: the aurora's green is missing")

    def test_fjord_lights(self):
        a = self.A["SDSKY4"][..., :3]
        white = (a == 255).all(-1)
        self.assertTrue(white[:, g.LIGHTHOUSE_X - 1:g.LIGHTHOUSE_X + 1].any(), "the lighthouse's lamp")
        red = np.array(ep2lib.col("flag_red", 1.0))
        self.assertGreaterEqual(int((a == red).all(-1).sum()), 4, "red obstruction lights")

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            g.build_all(Path(t))
            for lump in LUMPS:
                self.assertEqual(self.path(lump).read_bytes(),
                                 (Path(t) / g.SET_NAME / f"{lump}.png").read_bytes(), f"{lump} is not reproducible")

    def test_work_renders_match_the_generator(self):
        for lump in LUMPS:
            w = g.WORK_ROOT / g.SET_NAME / f"{lump}.png"
            if not w.is_file():
                self.skipTest("work/art/episode3_skies not rendered on this machine")
            self.assertEqual(w.read_bytes(), self.path(lump).read_bytes(), lump)

    def test_installed_lumps_are_what_the_generator_builds(self):
        for lump in LUMPS:
            installed = PROJECT_ROOT / "assets" / "textures" / "sky" / f"{lump}.png"
            self.assertTrue(installed.is_file(), installed)
            self.assertEqual(installed.read_bytes(), self.path(lump).read_bytes(), lump)


class PaperTests(unittest.TestCase):
    """One approved row each in TEXTURE-INDEX.md and LICENSES.md; MAPINFO's
    sky1 of MAP07-09 names the three; check_pk3 declares them."""

    @classmethod
    def setUpClass(cls):
        cls.index = (PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md").read_text(encoding="utf-8")
        cls.licenses = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")
        cls.mapinfo = (PROJECT_ROOT / "src" / "lumps" / "MAPINFO").read_text(encoding="utf-8")

    def rows(self, text: str, lump: str) -> list[str]:
        return [line for line in text.splitlines() if line.startswith(f"| `{lump}` |")]

    def test_one_approved_index_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.index, lump)
            self.assertEqual(1, len(rows), f"{lump}: expected one row in TEXTURE-INDEX.md")
            self.assertIn("approved 2026-10-22 (D113", rows[0], lump)
            self.assertIn("gen_episode3_skies", rows[0], lump)

    def test_a_licence_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.licenses, lump)
            self.assertEqual(1, len(rows), f"{lump}: expected one row in LICENSES.md")
            self.assertRegex(rows[0], r"\(a\) .*gen_episode3_skies\.py.*seed 600\d", lump)
            self.assertIn("CC BY-NC-SA 4.0", rows[0], lump)

    def test_mapinfo_skies(self):
        skies, current = {}, None
        for line in self.mapinfo.splitlines():
            m = re.match(r"^map\s+(\S+)", line)
            if m:
                current = m.group(1)
            s = re.match(r'^\s*sky1\s*=\s*"([^"]*)"', line)
            if s and current:
                skies[current] = s.group(1)
        self.assertEqual(MAP_SKIES, {k: v for k, v in skies.items() if v in LUMPS})

    def test_check_pk3_declares_them(self):
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        import check_pk3
        self.assertLessEqual(set(LUMPS), set(check_pk3.SKY_TEXTURES))
        self.assertIn("SDSKY5", check_pk3.PALETTE_V2_LUMPS)
        self.assertFalse({"SDSKY3", "SDSKY4"} & set(check_pk3.PALETTE_V2_LUMPS))


if __name__ == "__main__":
    unittest.main()
