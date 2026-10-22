"""Contract of Episode 1's skies (P4, D113): tools/art/gen_episode1_skies.py.

SDSKY6 (MAP01 and RANGE, the Zarya-7 cosmodrome before a November dawn) and
SDSKY7 (MAP03, Tankograd at night). Approved under D113's standing approval
(the CEO approves procedural textures in advance) and installed in
assets/textures/sky/. What is held:

  format     1024x128 indexed, the SDSKY1-5 contract (check_pk3 SKY_SIZES);
             the horizon row is gen_episode2b's; one turn that wraps in x
  seeds      6010 + offset, one per sky, clear of Episode 3's 6000-6003
  no font    the generator never rasterises a system font (D27)
  writes     PNGs to work/art/episode1_skies/, the preview to docs/art/
             previews/; assets/ is only read
  palette    v1 only (no v2 ramp: MAP03's portal is inside its drum)
  looks      dark zenith; SDSKY6: stars above the horizon and none below,
             the floodlit rocket on the pad, a warm dawn in the east and a
             cold west, red lights; SDSKY7: low sky lit warm by the
             furnaces, their flares, red lights
  installed  assets/ holds the generator's bytes; one approved row each in
             TEXTURE-INDEX.md and LICENSES.md; MAPINFO sky1 of MAP01, MAP03
             and RANGE; MAP02 (no sky sector) keeps SKY1
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
SOURCE = ART_TOOLS / "gen_episode1_skies.py"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode1-skies.png"
LUMPS = ("SDSKY6", "SDSKY7")
MAP_SKIES = {"MAP01": "SDSKY6", "MAP03": "SDSKY7", "RANGE": "SDSKY6"}
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import ep2lib
    import gen_episode2b
    import gen_episode1_skies as g
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


def count(a, colour) -> int:
    return int((a[..., :3] == np.array(colour)).all(-1).sum())


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
        self.assertNotRegex(text, re.compile(r"^\s*(ep2lib|e2b|e3s|gen_episode2b|gen_episode3_skies|gen_metro)\.\w+\s*=", re.M))

    def test_preview_exists(self):
        self.assertTrue(PREVIEW.is_file(), PREVIEW)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def test_lumps(self):
        self.assertEqual(list(LUMPS), g.all_lumps())

    def test_the_sky_format(self):
        self.assertEqual((1024, 128), g.SKY_SIZE)
        self.assertEqual(gen_episode2b.SKY_SIZE, g.SKY_SIZE)
        self.assertEqual(gen_episode2b.HORIZON, g.HORIZON)
        for p in g.PIECES:
            self.assertEqual("sky", p.kind, p.key)
            self.assertEqual(g.SKY_SIZE, p.size, p.key)
            self.assertEqual("x", p.tiles, p.key)

    def test_seeds(self):
        self.assertEqual(6010, g.BATCH_SEED)
        offsets = [p.offset for p in g.PIECES]
        self.assertEqual(len(offsets), len(set(offsets)))

    def test_palette_v1_only(self):
        for p in g.PIECES:
            self.assertEqual((), p.ramps, p.key)
            self.assertEqual(1, p.palette, p.key)

    def test_map_table(self):
        self.assertEqual(MAP_SKIES, g.MAP_SKIES)


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
        allowed = set(g.allowed_colours())
        for lump in LUMPS:
            a = self.A[lump]
            used = {tuple(int(v) for v in c) for c in np.unique(a[..., :3].reshape(-1, 3), axis=0)}
            self.assertLessEqual(used, allowed, f"{lump} leaves palette v1: {sorted(used - allowed)[:5]}")

    def test_wraps_round_the_turn(self):
        for lump in LUMPS:
            self.assertLessEqual(axis_seam(self.A[lump], 1), SEAM_LIMIT, lump)

    def test_dark_zenith(self):
        for lump in LUMPS:
            lum = luma(self.A[lump])
            self.assertLess(lum[:20].mean(), lum[70:g.HORIZON].mean(), f"{lump}: the zenith should be darker")

    def test_red_obstruction_lights(self):
        red = ep2lib.col("flag_red", 1.0)
        for lump in LUMPS:
            self.assertGreaterEqual(count(self.A[lump], red), 4, lump)

    def test_steppe_stars_above_the_horizon_only(self):
        a = self.A["SDSKY6"]
        star = ep2lib.col("cream_yellow", 0.96)
        self.assertGreater(count(a[:g.HORIZON], star), 30, "SDSKY6: too few bright stars")
        self.assertEqual(0, count(a[g.HORIZON:], star), "SDSKY6: a star below the horizon")

    def test_the_rocket_on_its_pad(self):
        a = self.A["SDSKY6"]
        rocket = luma(a[g.ROCKET_TIP:g.HORIZON, g.PAD_X - 1:g.PAD_X + 1])
        self.assertGreater(float(rocket.mean()), 110, "the floodlit rocket should be pale")
        self.assertLess(float(luma(a[:g.ROCKET_TIP - 4, g.PAD_X]).mean()), 60, "sky above the rocket")

    def test_dawn_in_the_east_cold_in_the_west(self):
        a = self.A["SDSKY6"][..., :3].astype(float)
        low = a[g.HORIZON - 6:g.HORIZON]
        east = low[:, g.DAWN_X - 40:g.DAWN_X + 40]
        west_x = (g.DAWN_X + 512) % 1024
        west = low[:, west_x - 40:west_x + 40]
        self.assertGreater(float((east[..., 0] - east[..., 2]).mean()), 15, "the dawn should be warm")
        self.assertLessEqual(float((west[..., 0] - west[..., 2]).mean()), 2, "the west should stay cold")

    def test_tankograd_glows_warm(self):
        a = self.A["SDSKY7"][..., :3].astype(float)
        low = a[40:g.HORIZON - 12]
        self.assertGreater(float((low[..., 0] - low[..., 2]).mean()), 25, "the cloud should be lit orange")
        top = a[:12]
        self.assertLess(float(luma(top).mean()), float(luma(low).mean()), "colder, darker zenith")

    def test_furnace_flares(self):
        a = self.A["SDSKY7"]
        white = (a[..., :3] == 255).all(-1)
        for fx, _s in g.FURNACES:
            self.assertTrue(white[:g.HORIZON, fx].any(), f"the flare over the furnace at x={fx}")

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
                self.skipTest("work/art/episode1_skies not rendered on this machine")
            self.assertEqual(w.read_bytes(), self.path(lump).read_bytes(), lump)

    def test_installed_lumps_are_what_the_generator_builds(self):
        for lump in LUMPS:
            installed = PROJECT_ROOT / "assets" / "textures" / "sky" / f"{lump}.png"
            self.assertTrue(installed.is_file(), installed)
            self.assertEqual(installed.read_bytes(), self.path(lump).read_bytes(), lump)


class PaperTests(unittest.TestCase):
    """One approved row each in TEXTURE-INDEX.md and LICENSES.md; MAPINFO's
    sky1 of MAP01, MAP03 and RANGE names them, MAP02 keeps SKY1; check_pk3
    declares them."""

    @classmethod
    def setUpClass(cls):
        cls.index = (PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md").read_text(encoding="utf-8")
        cls.licenses = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")
        cls.mapinfo = (PROJECT_ROOT / "src" / "lumps" / "MAPINFO").read_text(encoding="utf-8")

    def rows(self, text: str, lump: str) -> list[str]:
        return [line for line in text.splitlines() if line.startswith(f"| `{lump}` |")]

    def skies(self) -> dict:
        skies, current = {}, None
        for line in self.mapinfo.splitlines():
            m = re.match(r"^map\s+(\S+)", line)
            if m:
                current = m.group(1)
            s = re.match(r'^\s*sky1\s*=\s*"([^"]*)"', line)
            if s and current:
                skies[current] = s.group(1)
        return skies

    def test_one_approved_index_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.index, lump)
            self.assertEqual(1, len(rows), f"{lump}: expected one row in TEXTURE-INDEX.md")
            self.assertIn("approved 2026-10-22 (D113", rows[0], lump)
            self.assertIn("gen_episode1_skies", rows[0], lump)

    def test_a_licence_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.licenses, lump)
            self.assertEqual(1, len(rows), f"{lump}: expected one row in LICENSES.md")
            self.assertRegex(rows[0], r"\(a\) .*gen_episode1_skies\.py.*seed 601\d", lump)
            self.assertIn("CC BY-NC-SA 4.0", rows[0], lump)

    def test_mapinfo_skies(self):
        skies = self.skies()
        self.assertEqual(MAP_SKIES, {k: v for k, v in skies.items() if v in LUMPS})
        self.assertEqual("SKY1", skies["MAP02"], "MAP02 has no sky sector: it keeps SKY1")

    def test_check_pk3_declares_them(self):
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        import check_pk3
        self.assertLessEqual(set(LUMPS), set(check_pk3.SKY_TEXTURES))
        self.assertFalse(set(LUMPS) & set(check_pk3.PALETTE_V2_LUMPS))


if __name__ == "__main__":
    unittest.main()
