"""Contract of tools/art/gen_soviet_flags.py (D119) and of the four flags as
installed in assets/.

D119 (CEO playtest, 2026-10-23): the occupiers' banners SDFLAG1-4 read as
part of the setting, not the enemy's; all four are Soviet flags now, under
the same lump names and sizes, so the nine maps change without edits.
Installed under D113's standing approval for procedural textures. What is
held:

  names      the four lumps, 64x128, in the folders the old banners had
             (SDFLAG1/2 textures/factory, SDFLAG3/4 textures/moscow)
  seeds      one seed per lump in the generator's own space (6119 + offset)
  no font    the generator never rasterises a system font (D27)
  writes     PNGs to work/art/soviet_flags/, the sheet to docs/art/previews/;
             assets/ is only read
  installed  assets/ holds exactly the generator's bytes, once each; the
             work/ render too where work/ exists
  ground     every pixel the flag leaves alone is the approved wall's
             (SDBRCK1 or SDKREM1, as their generators build them, which are
             the installed files): the edge columns and the bottom rows are
             the wall's, so a flag tile continues the bond with no seam
  palette    the flag's own pixels are v1 + marble_red only: no mosaic_gold,
             no flesh_pink, no mosaic_cobalt (the Legion's canton is gone)
  Soviet     red cloth and gold on every flag, the emblem's gold in its
             box; nothing left of the old banners' white disc, black cross,
             stripes or canton; four distinct variants
  battle     SDFLAG4 shows the wall through its bullet holes and has charred
             pixels at its torn foot
  paper      one approved D119 row per lump in TEXTURE-INDEX.md and in
             LICENSES.md, none of them about the occupiers' banners
  sheet      the CEO's before/after PNG exists, at x4

The renders skip when SD_SKIP_SLOW_ART is set (verify.py fast); a full
render of the four takes about a second.
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
SOURCE = ART_TOOLS / "gen_soviet_flags.py"
ASSETS = PROJECT_ROOT / "assets"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-23_P4_soviet-flags.png"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import gen_soviet_flags as g
    import palette as palgen
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the flag renders")
needs_imaging = unittest.skipUnless(HAVE_IMAGING, "numpy/Pillow not available")

LUMPS = ("SDFLAG1", "SDFLAG2", "SDFLAG3", "SDFLAG4")
INSTALLED = {"SDFLAG1": "textures/factory", "SDFLAG2": "textures/factory",
             "SDFLAG3": "textures/moscow", "SDFLAG4": "textures/moscow"}
GROUNDS = {"SDFLAG1": "SDBRCK1", "SDFLAG2": "SDBRCK1", "SDFLAG3": "SDKREM1", "SDFLAG4": "SDKREM1"}
WALL_FILES = {"SDBRCK1": ASSETS / "textures" / "factory" / "SDBRCK1.png",
              "SDKREM1": ASSETS / "textures" / "moscow" / "SDKREM1.png"}
OTHER_BATCH_SEEDS = {1935, 1977, 2077, 3077, 4100, 5400, 5500, 5600, 5700, 5800, 5900, 6000, 6010}
MIN_RED_PX = 1500          # the cloth: about 50x80 px of flag_red at least
MIN_GOLD_PX = 120          # star border, hammer and sickle, fringe, finials
MIN_EMBLEM_GOLD = 40       # gold inside the emblem's own box
MAX_LIGHT_PX = 20          # what is left of a white disc or white stripes: nothing
DISTINCT_SHARE = 0.20      # two variants differ on at least this share of pixels
BOTTOM_ROWS = 3            # rows at the foot of every flag that are the wall's own


def read_rgb(path: Path) -> "np.ndarray":
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"))


def ramp_set(name: str) -> set:
    return {tuple(int(v) for v in c) for c in palgen.ramp_colours(name)}


class SourceTests(unittest.TestCase):
    def test_no_system_font(self):
        code = re.sub(r'""".*?"""', "", SOURCE.read_text(encoding="utf-8"), flags=re.S)
        for token in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text(", "truetype"):
            self.assertNotIn(token, code, f"uses {token}: no system font (D27)")

    def test_never_writes_assets(self):
        for line in SOURCE.read_text(encoding="utf-8").splitlines():
            if re.search(r"\.(save|write_text|write_bytes|mkdir)\(", line):
                self.assertNotRegex(line, r"ASSETS|['\"]assets['\"]", line.strip())
        self.assertIn('OUT_DIR = PROJECT_ROOT / "work" / "art" / "soviet_flags"', SOURCE.read_text(encoding="utf-8"))

    def test_no_occupier_symbols_left(self):
        code = SOURCE.read_text(encoding="utf-8")
        for token in ("SWASTIKA", "CANTON", "STRIPES", "mosaic_cobalt", "STAR_STEP"):
            self.assertNotIn(token, code)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def test_lumps_grounds_and_folders(self):
        self.assertEqual(g.LUMPS, LUMPS)
        self.assertEqual(g.GROUND, GROUNDS)
        self.assertEqual({k: f"textures/{v}" for k, v in g.FOLDER.items()}, INSTALLED)
        self.assertEqual((g.WALL_W, g.WALL_H), (64, 128))

    def test_seeds_in_their_own_space(self):
        self.assertEqual(g.BATCH_SEED, 6119)
        self.assertEqual(set(g.SEED_OFFSET), set(LUMPS))
        self.assertEqual(len(set(g.SEED_OFFSET.values())), len(LUMPS))
        seeds = {g.BATCH_SEED + o for o in g.SEED_OFFSET.values()}
        for other in OTHER_BATCH_SEEDS:
            self.assertFalse(seeds & set(range(other, other + 32)), other)

    def test_outputs_stay_out_of_assets(self):
        for path in (g.OUT_DIR, g.BEFORE_DIR, g.PREVIEW):
            self.assertNotIn(ASSETS, Path(path).resolve().parents)

    def test_old_generators_no_longer_build_the_flags(self):
        import gen_episode2b
        import gen_factory
        self.assertFalse(set(LUMPS) & {lump for p in gen_factory.PIECES for lump in p[4]})
        self.assertFalse(set(LUMPS) & set(gen_episode2b.all_lumps()))


@needs_imaging
class InstalledTests(unittest.TestCase):
    def test_installed_once_each_at_64x128_indexed(self):
        for lump, folder in INSTALLED.items():
            hits = list(ASSETS.rglob(f"{lump}.png"))
            self.assertEqual(hits, [ASSETS / folder / f"{lump}.png"], lump)
            with Image.open(hits[0]) as im:
                self.assertEqual(im.size, (64, 128), lump)
                self.assertEqual(im.mode, "P", lump)


@needs_imaging
@slow
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.A = g.build(cls.root)
        cls.walls = {name: g.ground(name) for name in set(GROUNDS.values())}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def changed(self, lump):
        return (self.A[lump] != self.walls[GROUNDS[lump]]).any(-1)

    def own_pixels(self, lump):
        return {tuple(int(v) for v in c) for c in np.unique(self.A[lump][self.changed(lump)], axis=0)}

    def count(self, lump, colours) -> int:
        a = self.A[lump]
        return int(sum(((a == np.array(c)).all(-1)).sum() for c in colours))

    def test_installed_bytes_are_the_generator_bytes(self):
        for lump, folder in INSTALLED.items():
            built = (self.root / f"{lump}.png").read_bytes()
            self.assertEqual((ASSETS / folder / f"{lump}.png").read_bytes(), built, lump)

    def test_work_renders_match_the_generator(self):
        for lump in LUMPS:
            w = g.OUT_DIR / f"{lump}.png"
            if not w.is_file():
                self.skipTest("work/art/soviet_flags not rendered on this machine")
            self.assertEqual(w.read_bytes(), (self.root / f"{lump}.png").read_bytes(), lump)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            g.build(Path(t))
            for lump in LUMPS:
                self.assertEqual((Path(t) / f"{lump}.png").read_bytes(), (self.root / f"{lump}.png").read_bytes(), lump)

    def test_grounds_are_the_approved_walls(self):
        for name, path in WALL_FILES.items():
            self.assertTrue(np.array_equal(self.walls[name], read_rgb(path)), name)

    def test_edges_are_the_wall(self):
        for lump in LUMPS:
            a, wall = self.A[lump], self.walls[GROUNDS[lump]]
            for x in (0, 63):
                self.assertTrue(np.array_equal(a[:, x], wall[:, x]), (lump, x))
            self.assertTrue(np.array_equal(a[-BOTTOM_ROWS:], wall[-BOTTOM_ROWS:]), lump)

    def test_flag_pixels_stay_in_v1_and_marble_red(self):
        allowed = {tuple(c) for c in palgen.colours(1)} | ramp_set("marble_red")
        banned = ramp_set("mosaic_gold") | ramp_set("flesh_pink") | ramp_set("mosaic_cobalt")
        for lump in LUMPS:
            own = self.own_pixels(lump)
            self.assertLessEqual(own, allowed, f"{lump}: {sorted(own - allowed)[:5]}")
            self.assertFalse(own & banned - {(0, 0, 0)}, lump)
            self.assertEqual(self.count(lump, ramp_set("mosaic_cobalt")), 0, lump)

    def test_soviet_red_and_gold(self):
        red, gold = ramp_set("flag_red"), ramp_set("hazard_yellow")
        for lump in LUMPS:
            self.assertGreater(self.count(lump, red), MIN_RED_PX, lump)
            self.assertGreater(self.count(lump, gold), MIN_GOLD_PX, lump)

    def test_the_emblem_is_there(self):
        gold = np.array(sorted(ramp_set("hazard_yellow")))
        boxes = {"SDFLAG1": g.STATE_HS, "SDFLAG2": g.STD_HS, "SDFLAG3": g.GONF_HS, "SDFLAG4": g.STATE_HS}
        for lump, (cx, cy, r) in boxes.items():
            box = self.A[lump][int(cy - r):int(cy + r), int(cx - r):int(cx + r)]
            n = int((box[..., None, :] == gold[None, None]).all(-1).any(-1).sum())
            self.assertGreater(n, MIN_EMBLEM_GOLD, lump)

    def test_nothing_of_the_old_banners(self):
        """No white disc and black cross, no white stripes: the light
        plaster tones and pure black are absent from what the flag drew."""
        light = {c for c in ramp_set("plaster_warm") if sum(c) > 3 * 200}
        for lump in LUMPS:
            ch = self.changed(lump)
            a = self.A[lump]
            n_light = int(sum(((a == np.array(c)).all(-1) & ch).sum() for c in light))
            self.assertLessEqual(n_light, MAX_LIGHT_PX, lump)

    def test_four_distinct_variants(self):
        for i, a in enumerate(LUMPS):
            for b in LUMPS[i + 1:]:
                diff = (self.A[a] != self.A[b]).any(-1).mean()
                self.assertGreater(diff, DISTINCT_SHARE, (a, b))

    def test_battle_flag_is_holed_and_burnt(self):
        a, wall = self.A["SDFLAG4"], self.walls["SDKREM1"]
        x0, x1, y0, _ = g.STATE_CLOTH
        inner = (slice(56, 92), slice(x0 + 3, x1 - 3))
        self.assertGreater(int((a[inner] == wall[inner]).all(-1).sum()), 6, "no brick shows through the holes")
        char = np.array(g.col(g.CHAR))
        self.assertGreater(int((a[60:] == char).all(-1).sum()), 30, "no charred edge at the foot")


@needs_imaging
class PaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md").read_text(encoding="utf-8")
        cls.licenses = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")

    def rows(self, text, lump):
        return [ln for ln in text.splitlines() if ln.startswith(f"| `{lump}` |")]

    def test_one_approved_index_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.index, lump)
            self.assertEqual(len(rows), 1, lump)
            self.assertIn("approved 2026-10-23 (D119", rows[0], lump)
            self.assertIn("gen_soviet_flags", rows[0], lump)

    def test_one_licence_row_each(self):
        for lump in LUMPS:
            rows = self.rows(self.licenses, lump)
            self.assertEqual(len(rows), 1, lump)
            self.assertRegex(rows[0], r"\(a\) `tools/art/gen_soviet_flags\.py`, seed 61\d\d", lump)
            self.assertIn("CC BY-NC-SA 4.0", rows[0], lump)

    def test_no_row_speaks_of_the_occupiers_banners(self):
        for text in (self.index, self.licenses):
            for lump in LUMPS:
                row = self.rows(text, lump)[0]
                for word in ("Reich", "Legion", "swastika", "hooked", "US flag", "canton", "stripes"):
                    self.assertNotIn(word, row, (lump, word))

    def test_the_ceo_sheet_exists_at_x4(self):
        self.assertTrue(PREVIEW.is_file(), PREVIEW)
        with Image.open(PREVIEW) as im:
            w, h = im.size
        self.assertEqual(w % 4, 0)
        self.assertEqual(h % 4, 0)
        self.assertGreaterEqual(w, 4 * len(LUMPS) * 3 * 64)


if __name__ == "__main__":
    unittest.main()
