"""Contract of tools/art/gen_factory.py, the factory set «Танкоград» (MAP04 §7.2, BACKLOG N6).

Drafts for the CEO; nothing of it is approved or installed. What is held:

  names      the thirteen pieces of MAP04 §7.2 and their lumps (<= 8 chars,
             SD prefix), at the sizes §7.2 asks for, multiples of 8
  seeds      one seed per piece, in the set's own seed space; the key doors
             replay SDDOOR1's seed
  no font    the generator never rasterises a system font (D27): the only
             lettering comes from assets/fonts/bigfont (D24), and every glyph
             it needs exists there
  palette    every piece inside the palette version it declares; v1 pieces
             carry no v2 colour
  masked     the chain is RGBA with hard 0/255 alpha, mostly transparent
  doors      outside the trim, plate and band, SDDOORY and SDDOORR are the
             approved SDDOOR1 pixel for pixel; from afar (8x box average)
             each reads in its key's colour, apart from SDDOOR1 and each other
  animation  four distinct frames per animated piece, and the loop's last
             step (4 -> 1) no bigger than its others
  banners    SDFLAG1/2 hang on SDBRCK1's own pixels (no seam beside a brick tile)
  writes     the generator writes to work/ and docs/art/previews/ only, never assets/

The cheap checks (source text, glyph files) run at every tier. The ones that
render run unless SD_SKIP_SLOW_ART is set (verify.py fast sets it); a full
render of the set takes ~2 s.
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
SOURCE = ART_TOOLS / "gen_factory.py"
BIGFONT = PROJECT_ROOT / "assets" / "fonts" / "bigfont"
SDDOOR1 = PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDDOOR1.png"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the factory renders")

# MAP04 §7.2: piece -> (kind, width, height, lumps)
EXPECTED = {
    "SDBRCK1": ("wall", 64, 128, ["SDBRCK1"]),
    "SDBRCK2": ("wall", 64, 128, ["SDBRCK2"]),
    "SDRUST1": ("wall", 64, 128, ["SDRUST1"]),
    "SDCHAN1": ("wall", 64, 128, ["SDCHAN1"]),
    "SDFLR4": ("flat", 64, 64, ["SDFLR4"]),
    "SDGRAT1": ("flat", 64, 64, ["SDGRAT1"]),
    "SDMOLT": ("flat", 64, 64, ["SDMOLT1", "SDMOLT2", "SDMOLT3", "SDMOLT4"]),
    "SDDOORY": ("wall", 128, 128, ["SDDOORY"]),
    "SDDOORR": ("wall", 128, 128, ["SDDOORR"]),
    "SDPORT": ("wall", 128, 128, ["SDPORT1", "SDPORT2", "SDPORT3", "SDPORT4"]),
    "SDGATE1": ("wall", 128, 128, ["SDGATE1"]),
    "SDWIND1": ("wall", 64, 128, ["SDWIND1"]),
    "SDSLOG1": ("wall", 256, 64, ["SDSLOG1"]),
    "SDFLAG1": ("wall", 64, 128, ["SDFLAG1"]),
    "SDFLAG2": ("wall", 64, 128, ["SDFLAG2"]),
}
LUMP_RE = re.compile(r"^SD[A-Z0-9]{1,6}$")
OTHER_BATCH_SEEDS = {1935, 1977, 2077, 3077}     # gen_metro, gen_soviet_base/gen_shell, gen_switch, gen_props


class SourceTests(unittest.TestCase):
    """Text-only checks: run at every tier."""

    def test_generator_uses_no_system_font(self):
        src = SOURCE.read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", src, flags=re.S)      # docstrings may talk about fonts
        for banned in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text(", "truetype"):
            self.assertNotIn(banned, code, banned)

    def test_every_glyph_of_the_lettering_is_in_our_alphabet(self):
        for text in ("ТРАКТОРЫ —", "КОЛХОЗАМ!", "ПРОПУСК"):
            for ch in text:
                self.assertTrue((BIGFONT / f"{ord(ch):04X}.png").is_file(), f"no bigfont glyph for {ch!r}")

    def test_generator_never_names_assets_as_an_output(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertIn('OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch4"', src)
        self.assertNotIn('OUT_DIR = PROJECT_ROOT / "assets"', src)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class RegistryTests(unittest.TestCase):
    """Import-only checks: cheap, no rendering."""

    @classmethod
    def setUpClass(cls):
        import gen_factory
        cls.g = gen_factory

    def test_the_thirteen_pieces_of_map04(self):
        got = {p[0]: (p[2], p[3][0], p[3][1], p[4]) for p in self.g.PIECES}
        self.assertEqual(got, EXPECTED)

    def test_lump_names(self):
        for piece, builder, kind, size, lumps, *_ in self.g.PIECES:
            for lump in lumps:
                self.assertRegex(lump, LUMP_RE)
                self.assertLessEqual(len(lump), 8)
            self.assertEqual(size[0] % 8, 0, piece)
            self.assertEqual(size[1] % 8, 0, piece)

    def test_one_seed_per_piece_in_its_own_space(self):
        self.assertEqual(set(self.g.SEED_OFFSET), {p[0] for p in self.g.PIECES})
        self.assertEqual(len(set(self.g.SEED_OFFSET.values())), len(self.g.SEED_OFFSET))
        self.assertNotIn(self.g.BATCH_SEED, OTHER_BATCH_SEEDS)
        seeds = {self.g.BATCH_SEED + o for o in self.g.SEED_OFFSET.values()}
        for other in OTHER_BATCH_SEEDS:
            self.assertFalse(seeds & set(range(other, other + 32)), other)

    def test_key_doors_replay_sddoor1s_seed(self):
        import gen_soviet_base
        self.assertEqual(self.g.DOOR1_SEED, gen_soviet_base.BATCH_SEED + 5)

    def test_v2_pieces_say_why(self):
        for piece, version in self.g.PALETTE_VERSION.items():
            self.assertIn(version, (1, 2))
            if version == 2:
                self.assertIn(piece, self.g.PALETTE_WHY)

    def test_every_piece_has_a_verdict(self):
        self.assertEqual(set(self.g.RECOMMEND), {p[0] for p in self.g.PIECES})

    def test_outputs_stay_out_of_assets(self):
        assets = PROJECT_ROOT / "assets"
        for path in (self.g.OUT_DIR, self.g.VIEW_DIR, self.g.MANIFEST, self.g.PREVIEW_DIR):
            self.assertNotIn(assets, Path(path).resolve().parents)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_factory
        cls.g = gen_factory
        cls.frames = {}
        cls.quant = {}
        for piece, builder, kind, size, lumps, tiles, masked, desc in gen_factory.PIECES:
            frames = gen_factory.frames_of(piece, builder)
            cls.frames[piece] = frames
            for lump, rgb in zip(lumps, frames):
                cls.quant[lump] = np.asarray(gen_factory.quantise(piece, rgb).convert(
                    "RGBA" if rgb.shape[2] == 4 else "RGB"))

    def test_sizes(self):
        for piece, (kind, w, h, lumps) in EXPECTED.items():
            for lump in lumps:
                self.assertEqual(self.quant[lump].shape[:2], (h, w), lump)

    def test_deterministic(self):
        for piece, builder, *_ in self.g.PIECES:
            again = self.g.frames_of(piece, builder)
            for a, b in zip(self.frames[piece], again):
                self.assertTrue(np.array_equal(a, b), piece)

    def test_inside_the_declared_palette(self):
        import palette as palgen
        v1 = set(palgen.colours(1))
        v2 = set(palgen.colours(2))
        for piece, builder, kind, size, lumps, *_ in self.g.PIECES:
            allowed = v1 if self.g.palette_of(piece) == 1 else v2
            for lump in lumps:
                q = self.quant[lump]
                px = q[..., :3].reshape(-1, 3)
                if q.shape[2] == 4:
                    px = px[q[..., 3].reshape(-1) > 0]
                used = {tuple(int(v) for v in c) for c in px}
                self.assertLessEqual(used, allowed, f"{lump}: {sorted(used - allowed)[:5]}")

    def test_v2_pieces_really_use_v2(self):
        import palette as palgen
        v1 = set(palgen.colours(1))
        for piece, version in self.g.PALETTE_VERSION.items():
            if version != 2 or piece == "SDFLAG1":     # SDFLAG1 is v2 only through its brick ground
                continue
            lump = next(p[4] for p in self.g.PIECES if p[0] == piece)[0]
            used = {tuple(int(v) for v in c) for c in self.quant[lump][..., :3].reshape(-1, 3)}
            self.assertTrue(used - v1, f"{piece} is declared v2 but uses only v1 colours")

    def test_chain_is_masked_with_hard_alpha(self):
        q = self.quant["SDCHAN1"]
        self.assertEqual(q.shape[2], 4)
        self.assertEqual(set(np.unique(q[..., 3]).tolist()), {0, 255})
        self.assertGreater((q[..., 3] == 0).mean(), 0.75, "the ground must be mostly transparent")
        self.assertGreater((q[..., 3] == 255).sum(), 200, "the chain must be there")

    def test_animated_frames_distinct_and_loop_seamless(self):
        for piece in ("SDMOLT", "SDPORT"):
            fr = [f.astype(np.float64) for f in self.frames[piece]]
            self.assertEqual(len(fr), 4)
            steps = [np.abs(fr[(k + 1) % 4] - fr[k]).mean() for k in range(4)]
            self.assertTrue(all(s > 1.0 for s in steps), (piece, steps))
            self.assertLessEqual(steps[-1], 1.5 * max(steps[:-1]), (piece, steps))

    @unittest.skipUnless(SDDOOR1.is_file(), "approved SDDOOR1 not in this clone")
    def test_key_doors_are_sddoor1_outside_their_trim(self):
        with Image.open(SDDOOR1) as im:
            door1 = np.asarray(im.convert("RGB"))
        leaf, frame, ribs, plate, band = self.g.door_masks()
        changed = frame | plate | band
        for ry in self.g.base.DOOR_RIB_YS:
            changed[ry - 1:ry + self.g.base.DOOR_RIB_H + 1, :] = True
        # SDDOOR1's star and "7" stencils sit under the plate's rows; the "7" runs a few rows lower
        changed[:46, :] = True
        changed[self.g.BAND_Y0 - 1:, :] = True
        changed[:, :self.g.base.DOOR_FRAME + 1] = True
        changed[:, -self.g.base.DOOR_FRAME - 1:] = True
        keep = ~changed
        self.assertGreater(keep.mean(), 0.30)
        for lump in ("SDDOORY", "SDDOORR"):
            diff = (self.quant[lump] != door1).any(axis=-1) & keep
            self.assertEqual(int(diff.sum()), 0, f"{lump}: {int(diff.sum())} px of SDDOOR1's leaf differ")

    @unittest.skipUnless(SDDOOR1.is_file(), "approved SDDOOR1 not in this clone")
    def test_key_doors_read_by_colour_from_afar(self):
        import artlib
        with Image.open(SDDOOR1) as im:
            door1 = np.asarray(im.convert("RGB")).astype(np.float64)
        mean = {"SDDOOR1": door1.reshape(-1, 3).mean(0)}
        for lump in ("SDDOORY", "SDDOORR"):
            mean[lump] = self.quant[lump].astype(np.float64).reshape(-1, 3).mean(0)
        dist = lambda a, b: float(np.linalg.norm(mean[a] - mean[b]))  # noqa: E731
        self.assertGreater(dist("SDDOORY", "SDDOOR1"), 60)
        self.assertGreater(dist("SDDOORR", "SDDOOR1"), 45)
        self.assertGreater(dist("SDDOORY", "SDDOORR"), 60)
        # each sits nearer its key's ink than the other door does
        yellow = np.array(artlib.ramp_colour("hazard_yellow", 0.86), np.float64)
        red = np.array(artlib.ramp_colour("flag_red", 0.74), np.float64)
        self.assertLess(np.linalg.norm(mean["SDDOORY"] - yellow), np.linalg.norm(mean["SDDOORR"] - yellow))
        self.assertLess(np.linalg.norm(mean["SDDOORR"] - red), np.linalg.norm(mean["SDDOORY"] - red))
        # and the key colour covers a large share of the door
        _, frame, ribs, plate, band = self.g.door_masks()
        self.assertGreater((frame | ribs | plate).mean(), 0.40)

    def test_banners_hang_on_sdbrck1(self):
        brick = self.quant["SDBRCK1"]
        for lump in ("SDFLAG1", "SDFLAG2"):
            q = self.quant[lump]
            # the edge columns, outside the rod's brackets and the cloth's shadow
            for x in (0, 63):
                rows = slice(self.g.ROD_Y1 + 4, 128)
                self.assertTrue(np.array_equal(q[rows, x], brick[rows, x]), (lump, x))

    def test_slogan_carries_its_letters(self):
        import artlib
        q = self.quant["SDSLOG1"]
        cream = np.array(artlib.ramp_colour("cream_yellow", 0.94))
        letters = (q == cream).all(axis=-1).sum()
        self.assertGreater(letters, 600, "the two lines of the banner must be there")

    def test_tiling_pieces_have_a_quiet_seam(self):
        import artlib
        for piece, builder, kind, size, lumps, tiles, masked, _ in self.g.PIECES:
            if tiles and not masked:
                score = artlib.tiling_seam_score(self.quant[lumps[0]][..., :3])
                self.assertLess(score, 2.0, f"{piece}: seam ratio {score:.2f}")


if __name__ == "__main__":
    unittest.main()
