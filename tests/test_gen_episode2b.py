"""Contract of Episode 2's second texture round (D112, P4): tools/art/gen_episode2b.py.

APPROVED under D113's standing approval (the CEO approves procedural
textures in advance; PM gate 2026-10-22) and installed in
assets/textures/<sky|railway|dam|moscow>/ and assets/flats/<set>/. What is held:

  installed  assets/ holds the generator's bytes; one approved row per lump
             in TEXTURE-INDEX.md, one in LICENSES.md; the skies are MAPINFO's
             sky1 of MAP04-06

  names      every lump is an SD name of <= 8 upper-case characters, unique,
             not already used in assets/, work/ (this round's own drafts
             aside) or TEXTURE-INDEX.md, not readable as a sprite frame
  sizes      skies 1024x128; walls at an ART-BIBLE §2 size; flats 64x64
  seeds      one seed per piece in its own space (5700 + offset)
  no font    the generator never rasterises a system font (D27)
  writes     PNGs to work/art/episode2b/, the sheet to docs/art/previews/;
             assets/ is only read
  palette    v1 pieces carry v1 colours only; a v2 piece adds only its own
             declared ramps (marble_red, mosaic_cobalt), never gold or flesh
  masked     the three masked pieces are RGBA with hard 0/255 alpha
  tiling     each piece's declared axes wrap no harder than its interior;
             the skies wrap round the full turn
  skies      dark at the zenith, lighter at the horizon; Moscow warmer than
             the Urals; red obstruction lights on both skylines
  derived    SDFLAG3/4 hang on SDKREM1's own brick; SDDOORB differs from the
             approved SDDOORY only where the key colour goes
  text       the words come from our alphabet (letters present, legible ink)
  sheet      the review sheet lists every lump and has the vote and copy UI
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
SOURCE = ART_TOOLS / "gen_episode2b.py"
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode2-textures-round2.html"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import ep2lib
    import gen_episode2b as g
    import gen_factory
    import palette as palgen
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the round-2 renders")
needs_imaging = unittest.skipUnless(HAVE_IMAGING, "numpy/Pillow not available")

SEAM_LIMIT = 1.25
MASKED = {"SDGRIL1", "SDHVLT1", "SDRUBY1"}


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
        """ep2lib and gen_factory are only patched for the length of a call."""
        text = SOURCE.read_text(encoding="utf-8")
        self.assertNotRegex(text, re.compile(r"^\s*(ep2lib|gen_factory)\.\w+\s*=", re.M))

    def test_sheet_exists_with_every_lump_and_the_vote(self):
        self.assertTrue(SHEET.is_file(), SHEET)
        text = SHEET.read_text(encoding="utf-8")
        for needle in ("Copiar resultado", 'data-v="ok"', 'data-v="no"', 'data-v="q"', "mosaico 3×3",
                       "sala de muestra", "panorámica"):
            self.assertIn(needle, text)
        self.assertNotRegex(text, r"(src|href)=\"https?://", "the sheet must be self-contained")
        if HAVE_IMAGING:
            for lump in g.all_lumps():
                self.assertIn(lump, text)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def test_names(self):
        lumps = g.all_lumps()
        self.assertEqual(g.name_problems(), [])
        self.assertEqual(len(lumps), len(set(lumps)))

    def test_own_drafts_are_not_a_clash(self):
        taken = g.existing_lumps(frozenset(g.all_lumps()))
        for lump in g.all_lumps():
            self.assertNotIn(lump, taken)
        self.assertIn("SDKREM1", taken)

    def test_sizes_and_kinds(self):
        for p in g.PIECES:
            if p.kind == "sky":
                self.assertEqual(p.size, g.SKY_SIZE, p.key)
            elif p.kind == "flat":
                self.assertEqual(p.size, ep2lib.FLAT_SIZE, p.key)
            else:
                self.assertIn(p.size, ep2lib.ALLOWED_WALL_SIZES, p.key)
            self.assertIn(p.tiles, ("xy", "x", "y", "no"))
            self.assertEqual(p.masked, p.key in MASKED, p.key)

    def test_seeds(self):
        self.assertEqual(g.BATCH_SEED, 5700)
        offsets = [p.offset for p in g.PIECES]
        self.assertEqual(len(offsets), len(set(offsets)))

    def test_v2_only_for_the_declared_ramps(self):
        for p in g.PIECES:
            self.assertLessEqual(set(p.ramps), set(g.EXTRA_RAMPS_ALLOWED), p.key)
            self.assertEqual(p.palette, 2 if p.ramps else 1, p.key)
            if p.ramps:
                self.assertTrue(p.why_v2, f"{p.key} asks for v2 without saying why")

    def test_patched_restores(self):
        before = gen_factory.banner_ground
        with g._patched(gen_factory, banner_ground=g.kremlin_ground):
            self.assertIs(gen_factory.banner_ground, g.kremlin_ground)
        self.assertIs(gen_factory.banner_ground, before)


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

    def test_files_sizes_and_modes(self):
        for p in g.PIECES:
            for lump in p.lumps:
                with Image.open(self.root / p.set_name / f"{lump}.png") as im:
                    self.assertEqual(im.size, p.size, lump)
                    self.assertEqual(im.mode, "RGBA" if p.masked else "P", lump)

    def test_palette_membership(self):
        for p in g.PIECES:
            allowed = set(g.allowed_colours(p.ramps))
            for lump in p.lumps:
                a = self.A[lump]
                px = a[..., :3][a[..., 3] > 0] if a.shape[2] == 4 else a.reshape(-1, 3)
                used = {tuple(int(v) for v in c) for c in np.unique(px, axis=0)}
                self.assertLessEqual(used, allowed, f"{lump} leaves its palette: {sorted(used - allowed)[:5]}")
        gold_flesh = {tuple(c) for r in ("mosaic_gold", "flesh_pink") for c in palgen.ramp_colours(r)}
        for lump, a in self.A.items():
            used = {tuple(int(v) for v in c) for c in a[..., :3].reshape(-1, 3)}
            self.assertFalse(used & gold_flesh - {(0, 0, 0)}, f"{lump} uses gold or flesh")

    def test_masked_hard_alpha(self):
        for lump in MASKED:
            a = self.A[lump][..., 3]
            self.assertTrue(set(np.unique(a).tolist()) <= {0, 255}, lump)
            self.assertTrue(0.10 < (a == 0).mean() < 0.90, lump)

    def test_declared_axes_tile(self):
        for p in g.PIECES:
            if p.masked or p.tiles == "no":
                continue
            for lump in p.lumps:
                rgb = self.A[lump]
                if "x" in p.tiles:
                    self.assertLessEqual(axis_seam(rgb, 1), SEAM_LIMIT, f"{lump} seam in x")
                if "y" in p.tiles:
                    self.assertLessEqual(axis_seam(rgb, 0), SEAM_LIMIT, f"{lump} seam in y")

    def test_skies(self):
        urals, moscow = self.A["SDSKY1"], self.A["SDSKY2"]
        for sky in (urals, moscow):
            lum = luma(sky)
            self.assertLess(lum[:20].mean(), lum[70:95].mean(), "the zenith should be darker than the low sky")
        warmth = lambda a: float((a[:95, :, 0].astype(int) - a[:95, :, 2].astype(int)).mean())  # noqa: E731
        self.assertGreater(warmth(moscow), warmth(urals) + 5, "Moscow's glow should be warmer than the Urals")
        red = np.array(ep2lib.col("flag_red", 1.0))
        for name, sky in (("SDSKY1", urals), ("SDSKY2", moscow)):
            self.assertGreaterEqual(int((sky[..., :3] == red).all(-1).sum()), 4, f"{name}: red lights on the skyline")

    def test_flags_hang_on_the_kremlin_brick(self):
        wall = self.A["SDKREM1"] if "SDKREM1" in self.A else ep2lib.load_approved("SDKREM1")
        below = gen_factory.CLOTH_Y1 + gen_factory.FRINGE_H + 2
        for lump in ("SDFLAG3", "SDFLAG4"):
            self.assertTrue(np.array_equal(self.A[lump][below:, :, :3], wall[below:, :, :3]), lump)

    def test_blue_door_is_the_key_door_twin(self):
        yellow = ep2lib.load_approved("SDDOORY")[..., :3].astype(int)
        blue = self.A["SDDOORB"][..., :3].astype(int)
        _, frame, ribs, plate, band = gen_factory.door_masks()
        differs = (yellow != blue).any(-1)
        outside = differs & ~(frame | ribs | plate | band)
        self.assertLess(outside.mean(), 0.01, "SDDOORB departs from SDDOORY's leaf")
        cobalt = {tuple(c) for c in palgen.ramp_colours("mosaic_cobalt")}
        self.assertGreater(sum(tuple(c) in cobalt for c in blue[frame]), frame.sum() * 0.5)

    def test_words_are_inked(self):
        ink = np.array(ep2lib.col("concrete_cold", 0.03))
        board = self.A["SDSTAN1"][..., :3]
        self.assertGreater(int((board[8:36] == ink).all(-1).sum()), 600, "«СВЕРДЛОВСК» missing")
        self.assertGreater(int((board[40:56] == ink).all(-1).sum()), 250, "«СОРТИРОВОЧНЫЙ» missing")
        a, b = self.A["SDGUMS1"], self.A["SDGUMS2"]
        s0, s1 = g.SIGN
        self.assertFalse(np.array_equal(a[s0:s1], b[s0:s1]), "the GUM variants must differ in the sign")
        self.assertTrue(np.array_equal(a[s1 + 2:], b[s1 + 2:]), "the GUM variants share the front")

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            g.build_all(Path(t))
            for p in g.PIECES:
                for lump in p.lumps:
                    a = (self.root / p.set_name / f"{lump}.png").read_bytes()
                    b = (Path(t) / p.set_name / f"{lump}.png").read_bytes()
                    self.assertEqual(a, b, f"{lump} is not reproducible")

    def test_work_renders_match_the_generator(self):
        for p in g.PIECES:
            for lump in p.lumps:
                w = g.WORK_ROOT / p.set_name / f"{lump}.png"
                if not w.is_file():
                    self.skipTest("work/art/episode2b not rendered on this machine")
                self.assertEqual(w.read_bytes(), (self.root / p.set_name / f"{lump}.png").read_bytes(), lump)

    def test_installed_lumps_are_what_the_generator_builds(self):
        """D113: assets/ holds exactly the generator's bytes (walls and skies
        under textures/<set>/, flats under flats/<set>/). Runs without work/."""
        for p in g.PIECES:
            kind = "flats" if p.kind == "flat" else "textures"
            for lump in p.lumps:
                installed = PROJECT_ROOT / "assets" / kind / p.set_name / f"{lump}.png"
                self.assertTrue(installed.is_file(), installed)
                self.assertEqual(installed.read_bytes(), (self.root / p.set_name / f"{lump}.png").read_bytes(), lump)
                self.assertEqual(len(list((PROJECT_ROOT / "assets").rglob(f"{lump}.png"))), 1,
                                 f"{lump} installed twice")


@needs_imaging
class PaperTests(unittest.TestCase):
    """D113: every installed lump has one approved row in TEXTURE-INDEX.md and
    one row in LICENSES.md; MAPINFO's sky1 of MAP04-06 names the new skies."""

    @classmethod
    def setUpClass(cls):
        cls.index = (PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md").read_text(encoding="utf-8")
        cls.licenses = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")
        cls.mapinfo = (PROJECT_ROOT / "src" / "lumps" / "MAPINFO").read_text(encoding="utf-8")

    def rows(self, text: str, lump: str) -> list[str]:
        return [line for line in text.splitlines() if line.startswith(f"| `{lump}` |")]

    def test_one_approved_index_row_each(self):
        for lump in g.all_lumps():
            rows = self.rows(self.index, lump)
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in TEXTURE-INDEX.md")
            self.assertIn("approved 2026-10-22 (D113", rows[0], lump)

    def test_a_licence_row_each(self):
        for lump in g.all_lumps():
            rows = self.rows(self.licenses, lump)
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in LICENSES.md")
            self.assertRegex(rows[0], r"\(a\) .*gen_episode2b\.py.*seed \d{4}", lump)
            self.assertIn("CC BY-NC-SA 4.0", rows[0], lump)

    def test_mapinfo_skies(self):
        """MAP04 and MAP05 under the Urals night, MAP06 under Moscow's; the
        other maps keep Freedoom's SKY1 for now."""
        skies = {}
        current = None
        for line in self.mapinfo.splitlines():
            m = re.match(r'^map\s+(\S+)', line)
            if m:
                current = m.group(1)
            s = re.match(r'^\s*sky1\s*=\s*"([^"]*)"', line)
            if s and current:
                skies[current] = s.group(1)
        self.assertEqual({"MAP04": "SDSKY1", "MAP05": "SDSKY1", "MAP06": "SDSKY2"},
                         {k: v for k, v in skies.items() if v.startswith("SDSKY")})
        for name in ("MAP07", "MAP08", "MAP09"):
            self.assertEqual("SKY1", skies.get(name), name)


if __name__ == "__main__":
    unittest.main()
