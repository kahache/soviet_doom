"""Contract of the Episode 2 texture drafts (D104, P4): tools/art/gen_railway.py,
gen_dam.py, gen_moscow.py (MAP04-06), their shared ep2lib.py and the sheet
builder gen_episode2.py.

DRAFTS: nothing here is approved or installed. What is held:

  names      every lump is an SD name of <= 8 upper-case characters, unique
             across the three sets, not already used in assets/, work/ or
             TEXTURE-INDEX.md, and not readable as a sprite frame
  sizes      walls at an ART-BIBLE §2 size, flats 64x64, multiples of 8
  seeds      one seed per piece in each set's own space (5400/5500/5600),
             except the merlon, which replays the Kremlin wall's seed on purpose
  no font    the generators never rasterise a system font (D27)
  writes     PNGs go to work/art/episode2/, the sheet to docs/art/previews/;
             assets/ is only ever read (approved reference lumps for the scenes)
  palette    v1 pieces carry v1 colours only; v2 pieces add marble_red and
             nothing else (no cobalt, gold or flesh)
  masked     the two masked pieces are RGBA with hard 0/255 alpha
  tiling     each piece's declared axes wrap no harder than its own interior
  animation  the water has four distinct frames and a seamless loop
  shared     SDKREM2's parapet is SDKREM1 pixel for pixel; SDBANR1 hangs on it
  sheet      the review sheet lists every lump and has the vote and copy UI
  repeat     two renders of a set are identical

Text checks run at every tier; the renders skip when SD_SKIP_SLOW_ART is set
(verify.py fast). A full render of the three sets takes ~2 s.
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
SOURCES = [ART_TOOLS / n for n in ("ep2lib.py", "gen_railway.py", "gen_dam.py", "gen_moscow.py", "gen_episode2.py")]
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode2-textures.html"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import ep2lib
    import gen_dam
    import gen_episode2
    import gen_moscow
    import gen_railway
    import palette as palgen
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the Episode 2 renders")
needs_imaging = unittest.skipUnless(HAVE_IMAGING, "numpy/Pillow not available")

SEEDS = {"railway": 5400, "dam": 5500, "moscow": 5600}
SHARED_SEED = {"SDKREM2": "SDKREM1"}     # the merlon replays the wall's bricks
SEAM_LIMIT = 1.25                        # wrap step / largest interior step, per declared axis


def axis_seam(rgb, axis: int) -> float:
    a = rgb[..., :3].astype(float)
    interior = np.abs(np.diff(a, axis=axis)).mean(axis=(1 - axis, 2)).max()
    if axis == 0:
        wrap = np.abs(a[0] - a[-1]).mean()
    else:
        wrap = np.abs(a[:, 0] - a[:, -1]).mean()
    return float(wrap / max(interior, 1e-6))


class SourceTests(unittest.TestCase):
    def test_no_system_font(self):
        for src in SOURCES:
            text = src.read_text(encoding="utf-8")
            for token in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text("):
                self.assertNotIn(token, text, f"{src.name} uses {token}: no system font (D27)")

    def test_never_writes_assets(self):
        for src in SOURCES:
            for line in src.read_text(encoding="utf-8").splitlines():
                if re.search(r"\.(save|write_text|write_bytes|mkdir)\(", line):
                    self.assertNotRegex(line, r"ASSETS|['\"]assets['\"]", f"{src.name}: {line.strip()}")

    def test_sheet_exists_with_every_lump_and_the_vote(self):
        self.assertTrue(SHEET.is_file(), SHEET)
        text = SHEET.read_text(encoding="utf-8")
        for needle in ("Copiar resultado", 'data-v="ok"', 'data-v="no"', 'data-v="q"', "mosaico 3×3", "sala de muestra"):
            self.assertIn(needle, text)
        self.assertNotRegex(text, r"(src|href)=\"https?://", "the sheet must be self-contained")
        if HAVE_IMAGING:
            for mod in (gen_railway, gen_dam, gen_moscow):
                for p in mod.PIECES:
                    for lump in p.lumps:
                        self.assertIn(lump, text)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def all_pieces(self):
        return [(mod, p) for mod in (gen_railway, gen_dam, gen_moscow) for p in mod.PIECES]

    def test_names(self):
        lumps = [l for _, p in self.all_pieces() for l in p.lumps]
        self.assertEqual(gen_episode2.name_problems(lumps, gen_episode2.existing_lumps()), [])
        self.assertEqual(len(lumps), len(set(lumps)))

    def test_sizes(self):
        for _, p in self.all_pieces():
            if p.kind == "flat":
                self.assertEqual(p.size, ep2lib.FLAT_SIZE, p.key)
            else:
                self.assertIn(p.size, ep2lib.ALLOWED_WALL_SIZES, p.key)
            self.assertIn(p.tiles, ("xy", "x", "y", "no"))
            self.assertIn(p.palette, (1, 2))

    def test_seeds(self):
        for mod in (gen_railway, gen_dam, gen_moscow):
            self.assertEqual(mod.BATCH_SEED, SEEDS[mod.SET_NAME])
            offsets = {}
            for p in mod.PIECES:
                if p.key in SHARED_SEED:
                    twin = next(q for q in mod.PIECES if q.key == SHARED_SEED[p.key])
                    self.assertEqual(p.offset, twin.offset)
                    continue
                self.assertNotIn(p.offset, offsets, f"{p.key} shares a seed with {offsets.get(p.offset)}")
                offsets[p.offset] = p.key

    def test_v2_only_for_the_allowed_ramp(self):
        self.assertEqual(ep2lib.V2_RAMPS_ALLOWED, ("marble_red",))
        for _, p in self.all_pieces():
            if p.palette == 2:
                self.assertTrue(p.why_v2, f"{p.key} asks for v2 without saying why")


@needs_imaging
@slow
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = {}
        cls.arrays = {}
        for mod in (gen_railway, gen_dam, gen_moscow):
            d = Path(cls.tmp.name) / mod.SET_NAME
            entries, arrays = mod.build(d)
            cls.out[mod.SET_NAME] = (mod, d, entries)
            cls.arrays.update(arrays)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def pieces(self):
        for mod, d, _ in self.out.values():
            for p in mod.PIECES:
                yield mod, d, p

    def test_files_sizes_and_modes(self):
        for _, d, p in self.pieces():
            for lump in p.lumps:
                with Image.open(d / f"{lump}.png") as im:
                    self.assertEqual(im.size, p.size, lump)
                    self.assertEqual(im.mode, "RGBA" if p.masked else "P", lump)

    def test_palette_membership(self):
        v1 = {tuple(c) for c in palgen.colours(1)}
        v2_ok = v1 | {tuple(c) for c in palgen.ramp_colours("marble_red")}
        for _, _, p in self.pieces():
            allowed = v1 if p.palette == 1 else v2_ok
            for lump in p.lumps:
                a = self.arrays[lump]
                px = a[..., :3][a[..., 3] > 0] if a.shape[2] == 4 else a.reshape(-1, 3)
                used = {tuple(int(v) for v in c) for c in np.unique(px, axis=0)}
                self.assertLessEqual(used, allowed, f"{lump} leaves its palette: {sorted(used - allowed)[:5]}")

    def test_masked_hard_alpha(self):
        for _, _, p in self.pieces():
            if not p.masked:
                continue
            a = self.arrays[p.lumps[0]][..., 3]
            self.assertTrue(set(np.unique(a).tolist()) <= {0, 255}, p.key)
            share = (a == 0).mean()
            self.assertTrue(0.10 < share < 0.90, f"{p.key}: transparent share {share:.2f}")

    def test_declared_axes_tile(self):
        for _, _, p in self.pieces():
            if p.masked or p.tiles == "no":
                continue
            rgb = self.arrays[p.lumps[0]]
            if "x" in p.tiles:
                self.assertLessEqual(axis_seam(rgb, 1), SEAM_LIMIT, f"{p.key} seam in x")
            if "y" in p.tiles:
                self.assertLessEqual(axis_seam(rgb, 0), SEAM_LIMIT, f"{p.key} seam in y")

    def test_water_loop(self):
        frames = [self.arrays[f"SDWATR{i}"].astype(int) for i in range(1, 5)]
        steps = [np.abs(frames[(i + 1) % 4] - frames[i]).mean() for i in range(4)]
        for i in range(4):
            self.assertGreater(steps[i], 0, "two water frames are identical")
        self.assertLessEqual(steps[3], max(steps[:3]) * 1.25, "the loop 4 -> 1 jumps")

    def test_merlon_parapet_is_the_wall(self):
        wall, merlon = self.arrays["SDKREM1"], self.arrays["SDKREM2"]
        below = gen_moscow.MERLON_TOP_H + 1
        self.assertTrue((merlon[below:, :, 3] == 255).all())
        self.assertTrue(np.array_equal(merlon[below:, :, :3], wall[below:]))

    def test_banner_hangs_on_the_wall(self):
        wall, banner = self.arrays["SDKREM1"], self.arrays["SDBANR1"]
        y = gen_moscow.CLOTH[3] + gen_moscow.FRINGE_H + 1
        self.assertTrue(np.array_equal(banner[y:], wall[y:]))

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            for mod, d, _ in self.out.values():
                mod.build(Path(t) / mod.SET_NAME)
                for p in mod.PIECES:
                    for lump in p.lumps:
                        a = (d / f"{lump}.png").read_bytes()
                        b = (Path(t) / mod.SET_NAME / f"{lump}.png").read_bytes()
                        self.assertEqual(a, b, f"{lump} is not reproducible")

    def test_work_renders_match_the_generator(self):
        """The drafts in work/ (what the sheet shows) are what the generators
        build today."""
        for mod, d, _ in self.out.values():
            for p in mod.PIECES:
                for lump in p.lumps:
                    w = ep2lib.WORK_ROOT / mod.SET_NAME / f"{lump}.png"
                    if not w.is_file():
                        self.skipTest("work/art/episode2 not rendered on this machine")
                    self.assertEqual(w.read_bytes(), (d / f"{lump}.png").read_bytes(), lump)


if __name__ == "__main__":
    unittest.main()
