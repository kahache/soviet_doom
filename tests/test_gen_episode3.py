"""Contract of the Episode 3 texture drafts (D112, P4): tools/art/gen_arctic.py,
gen_naval.py, gen_taiga.py (MAP07-09), their shared ep3lib.py (on top of
ep2lib.py, read only) and the sheet builder gen_episode3.py.

APPROVED under D113's standing approval (PM gate 2026-10-22) and installed
in assets/{textures,flats}/<arctic|naval|taiga>/. What is held:

  names      every lump is an SD name of <= 8 upper-case characters, unique
             across the three sets, not already used in assets/, work/ or
             TEXTURE-INDEX.md (its own installed copy and rows aside), and
             not readable as a sprite frame
  installed  assets/ holds the generators' bytes; one approved row per lump
             in TEXTURE-INDEX.md, one in LICENSES.md
  sizes      walls at an ART-BIBLE §2 size, flats 64x64, multiples of 8
  seeds      one seed per piece in each set's own space (5700/5800/5900),
             except the twins that replay a seed on purpose (SDRWY2,
             SDHULL2, SDRUBR2), which equal their twin outside the paint
  no font    the generators never rasterise a system font (D27)
  writes     PNGs go to work/art/episode3/, the sheet to docs/art/previews/;
             assets/ is only ever read (approved reference lumps for the
             scenes)
  palette    v1 pieces carry v1 colours only; the one v2 piece is the
             portal rim, with mosaic_cobalt and nothing else (D66)
  masked     the crane is RGBA with hard 0/255 alpha
  tiling     each piece's declared axes wrap no harder than its own interior
  animation  the radar and the acid have four distinct frames and a loop
             that does not jump
  sheet      the review sheet lists every lump and has the vote and copy UI
  repeat     two renders of a set are identical; work/ holds today's renders

Text checks run at every tier; the renders skip when SD_SKIP_SLOW_ART is set
(verify.py fast). A full render of the three sets takes ~3 s.
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
SOURCES = [ART_TOOLS / n for n in ("ep3lib.py", "gen_arctic.py", "gen_naval.py", "gen_taiga.py", "gen_episode3.py")]
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode3-textures.html"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import ep3lib
    import gen_arctic
    import gen_episode3
    import gen_naval
    import gen_taiga
    import palette as palgen
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the Episode 3 renders")
needs_imaging = unittest.skipUnless(HAVE_IMAGING, "numpy/Pillow not available")

SEEDS = {"arctic": 5700, "naval": 5800, "taiga": 5900}
TWINS = {"SDRWY2": "SDRWY1", "SDHULL2": "SDHULL1", "SDRUBR2": "SDRUBR1"}
ANIMATED = {"SDRADR": "SDRADR", "SDACID": "SDACID"}
SEAM_LIMIT = 1.25                        # wrap step / largest interior step, per declared axis


def axis_seam(rgb, axis: int) -> float:
    a = rgb[..., :3].astype(float)
    interior = np.abs(np.diff(a, axis=axis)).mean(axis=(1 - axis, 2)).max()
    if axis == 0:
        wrap = np.abs(a[0] - a[-1]).mean()
    else:
        wrap = np.abs(a[:, 0] - a[:, -1]).mean()
    return float(wrap / max(interior, 1e-6))


def modules():
    return (gen_arctic, gen_naval, gen_taiga)


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

    def test_ep2lib_is_only_read(self):
        """ep3lib reuses ep2lib and never assigns into it."""
        text = (ART_TOOLS / "ep3lib.py").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"ep2lib\.[A-Za-z_]+\s*=[^=]")

    def test_sheet_exists_with_every_lump_and_the_vote(self):
        self.assertTrue(SHEET.is_file(), SHEET)
        text = SHEET.read_text(encoding="utf-8")
        for needle in ("Copiar resultado", 'data-v="ok"', 'data-v="no"', 'data-v="q"', "mosaico 3×3", "sala de muestra",
                       "sd-2026-10-22_P4_episode3-textures", "Texturas Episodio 3"):
            self.assertIn(needle, text)
        self.assertNotIn("sd-2026-10-22_P4_episode2-textures", text, "the sheet must not share Episode 2's storage")
        self.assertNotRegex(text, r"(src|href)=\"https?://", "the sheet must be self-contained")
        if HAVE_IMAGING:
            for mod in modules():
                for p in mod.PIECES:
                    for lump in p.lumps:
                        self.assertIn(lump, text)


@needs_imaging
class DefinitionTests(unittest.TestCase):
    def all_pieces(self):
        return [(mod, p) for mod in modules() for p in mod.PIECES]

    def test_names(self):
        lumps = [lump for _, p in self.all_pieces() for lump in p.lumps]
        self.assertEqual(gen_episode3.name_problems(lumps, gen_episode3.existing_lumps(frozenset(lumps))), [])
        self.assertEqual(len(lumps), len(set(lumps)))

    def test_installed_copies_are_not_a_clash_but_strangers_are(self):
        # D113: the installed copies and the index rows are the lumps themselves.
        self.assertIn("SDSNOW1", gen_episode3.existing_lumps())
        self.assertNotIn("SDSNOW1", gen_episode3.existing_lumps(frozenset({"SDSNOW1"})))
        self.assertIn("SDKREM1", gen_episode3.existing_lumps(frozenset({"SDSNOW1"})))

    def test_sprite_prefix_is_caught(self):
        # SDRD is a sprite: a console called SDRDR1 would read as one of its frames.
        self.assertTrue(gen_episode3.name_problems(["SDRDR1"], gen_episode3.existing_lumps()))

    def test_every_lump_has_a_new_family(self):
        for _, p in self.all_pieces():
            self.assertTrue(gen_episode3.family_of(p.lumps[0]), p.key)

    def test_sizes(self):
        for _, p in self.all_pieces():
            if p.kind == "flat":
                self.assertEqual(p.size, ep3lib.FLAT_SIZE, p.key)
            else:
                self.assertIn(p.size, ep3lib.ALLOWED_WALL_SIZES, p.key)
            self.assertIn(p.tiles, ("xy", "x", "y", "no"))
            self.assertIn(p.palette, (1, 2))

    def test_seeds(self):
        for mod in modules():
            self.assertEqual(mod.BATCH_SEED, SEEDS[mod.SET_NAME])
            offsets = {}
            for p in mod.PIECES:
                if p.key in TWINS:
                    twin = next(q for q in mod.PIECES if q.key == TWINS[p.key])
                    self.assertEqual(p.offset, twin.offset)
                    self.assertEqual(mod.SHARED_SEED.get(p.key), TWINS[p.key])
                    continue
                self.assertNotIn(p.offset, offsets, f"{p.key} shares a seed with {offsets.get(p.offset)}")
                offsets[p.offset] = p.key

    def test_v2_only_for_the_portal_and_its_cobalt(self):
        self.assertEqual(ep3lib.V2_RAMPS_ALLOWED, ("marble_red", "mosaic_cobalt"))
        v2 = [p for _, p in self.all_pieces() if p.palette == 2]
        self.assertEqual([p.key for p in v2], ["SDPRTE1"])
        for p in v2:
            self.assertEqual(p.v2_ramps, ("mosaic_cobalt",))
            self.assertTrue(p.why_v2)
            self.assertIn(p.key, ep3lib.COBALT_PIECES)
        for _, p in self.all_pieces():
            if p.palette == 1:
                self.assertEqual(p.v2_ramps, ())


@needs_imaging
@slow
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = {}
        cls.arrays = {}
        for mod in modules():
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
        for _, _, p in self.pieces():
            allowed = set(v1)
            for ramp in p.v2_ramps:
                allowed |= {tuple(c) for c in palgen.ramp_colours(ramp)}
            for lump in p.lumps:
                a = self.arrays[lump]
                px = a[..., :3][a[..., 3] > 0] if a.shape[2] == 4 else a.reshape(-1, 3)
                used = {tuple(int(v) for v in c) for c in np.unique(px, axis=0)}
                self.assertLessEqual(used, allowed, f"{lump} leaves its palette: {sorted(used - allowed)[:5]}")

    def test_the_rim_really_is_cobalt(self):
        cobalt = {tuple(c) for c in palgen.ramp_colours("mosaic_cobalt")}
        a = self.arrays["SDPRTE1"].reshape(-1, 3)
        share = np.mean([tuple(int(v) for v in c) in cobalt for c in a])
        self.assertGreater(share, 0.20)

    def test_masked_hard_alpha(self):
        masked = [p for _, _, p in self.pieces() if p.masked]
        self.assertEqual([p.key for p in masked], ["SDCRAN1"])
        for p in masked:
            a = self.arrays[p.lumps[0]][..., 3]
            self.assertTrue(set(np.unique(a).tolist()) <= {0, 255}, p.key)
            share = (a == 0).mean()
            self.assertTrue(0.10 < share < 0.90, f"{p.key}: transparent share {share:.2f}")

    def test_declared_axes_tile(self):
        for _, _, p in self.pieces():
            if p.masked or p.tiles == "no":
                continue
            for lump in p.lumps:
                rgb = self.arrays[lump]
                if "x" in p.tiles:
                    self.assertLessEqual(axis_seam(rgb, 1), SEAM_LIMIT, f"{lump} seam in x")
                if "y" in p.tiles:
                    self.assertLessEqual(axis_seam(rgb, 0), SEAM_LIMIT, f"{lump} seam in y")

    def test_masked_crane_tiles_by_alpha(self):
        a = self.arrays["SDCRAN1"][..., 3] > 0
        self.assertTrue(np.array_equal(a[:64], a[64:]), "the two 64 px bays differ: it would not tile in y")
        # the chords run the whole height and the battens the whole width
        for x0, x1 in gen_naval.CHORDS:
            self.assertTrue(a[:, x0 + 1:x1 - 1].all())
        self.assertTrue(a[1].all() and a[65].all())

    def test_animation_loops(self):
        for prefix in ANIMATED:
            frames = [self.arrays[f"{prefix}{i}"].astype(int) for i in range(1, 5)]
            steps = [np.abs(frames[(i + 1) % 4] - frames[i]).mean() for i in range(4)]
            for i in range(4):
                self.assertGreater(steps[i], 0, f"{prefix}: two frames are identical")
            self.assertLessEqual(steps[3], max(steps[:3]) * 1.25, f"{prefix}: the loop 4 -> 1 jumps")

    def test_twins_equal_outside_the_paint(self):
        for mod in modules():
            for key, box in mod.PAINT_BOX.items():
                twin = mod.SHARED_SEED[key]
                a, b = self.arrays[key].copy(), self.arrays[twin].copy()
                x0, y0, x1, y1 = box
                a[y0:y1, x0:x1] = 0
                b[y0:y1, x0:x1] = 0
                self.assertTrue(np.array_equal(a, b), f"{key} differs from {twin} outside its paint")
                self.assertFalse(np.array_equal(self.arrays[key], self.arrays[twin]), f"{key} paints nothing")

    def test_no_large_flat_black(self):
        """ART-BIBLE §5: no pure-black area larger than an 8 px blob."""
        for _, _, p in self.pieces():
            for lump in p.lumps:
                a = self.arrays[lump]
                black = (a[..., :3].sum(-1) == 0)
                if a.shape[2] == 4:
                    black &= a[..., 3] > 0
                h, w = black.shape
                for y in range(0, h - 8):
                    for x in range(0, w - 8, 4):
                        self.assertFalse(black[y:y + 9, x:x + 9].all(), f"{lump}: black block at {x},{y}")

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
                    w = ep3lib.WORK_ROOT / mod.SET_NAME / f"{lump}.png"
                    if not w.is_file():
                        self.skipTest("work/art/episode3 not rendered on this machine")
                    self.assertEqual(w.read_bytes(), (d / f"{lump}.png").read_bytes(), lump)

    def test_installed_lumps_are_what_the_generators_build(self):
        """D113: assets/ holds exactly the generators' bytes (walls under
        textures/<set>/, flats under flats/<set>/). Runs without work/."""
        for mod, d, p in self.pieces():
            kind = "flats" if p.kind == "flat" else "textures"
            for lump in p.lumps:
                installed = PROJECT_ROOT / "assets" / kind / mod.SET_NAME / f"{lump}.png"
                self.assertTrue(installed.is_file(), installed)
                self.assertEqual(installed.read_bytes(), (d / f"{lump}.png").read_bytes(), lump)
                self.assertEqual(len(list((PROJECT_ROOT / "assets").rglob(f"{lump}.png"))), 1,
                                 f"{lump} installed twice")


@needs_imaging
class PaperTests(unittest.TestCase):
    """D113: every installed lump has one approved row in TEXTURE-INDEX.md and
    one row in LICENSES.md naming its generator and seed."""

    @classmethod
    def setUpClass(cls):
        cls.index = (PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md").read_text(encoding="utf-8")
        cls.licenses = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")
        cls.lumps = [lump for mod in modules() for p in mod.PIECES for lump in p.lumps]

    def rows(self, text: str, lump: str) -> list[str]:
        return [line for line in text.splitlines() if line.startswith(f"| `{lump}` |")]

    def test_one_approved_index_row_each(self):
        for lump in self.lumps:
            rows = self.rows(self.index, lump)
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in TEXTURE-INDEX.md")
            self.assertIn("approved 2026-10-22 (D113", rows[0], lump)

    def test_a_licence_row_each(self):
        for lump in self.lumps:
            rows = self.rows(self.licenses, lump)
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in LICENSES.md")
            self.assertRegex(rows[0], r"\(a\) .*gen_(arctic|naval|taiga)\.py.*seed \d{4}", lump)
            self.assertIn("CC BY-NC-SA 4.0", rows[0], lump)

    def test_the_acid_row_leaves_the_damage_to_the_map(self):
        # The damage is the map's sector special, not the texture's.
        self.assertIn("sector special", self.rows(self.index, "SDACID1")[0])


if __name__ == "__main__":
    unittest.main()
