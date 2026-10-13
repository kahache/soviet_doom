"""Contract tests for the three art generators that produce what ships:

    tools/art/gen_soviet_base.py   batch 1, the MAP01 texture set
    tools/art/gen_lenin.py         SDPOSTR1, the Lenin poster
    tools/art/gen_shell.py         TITLEPIC / INTERPIC / M_DOOM

What is enforced here, and why:

  size and mode      a lump that is not the declared size, or not indexed,
                     is a GZDoom problem, not an art problem
  determinism        docs/art/TEXTURE-INDEX.md records "script + seed" as
                     the origin of every texture; if a rebuild is not
                     byte-identical that record is worthless
  palette            every colour of every shipped PNG comes from
                     docs/art/palette.json (check_pk3 rejects the rest)
  tiling             the textures declared tileable must not show a seam
                     the texture does not already have inside itself
  ink count          SDPOSTR1 is exactly N flat inks: the first build shipped
                     95 antialiased colours off the palette and was rejected
  hard alpha         M_DOOM is the only art with transparency, and Doom
                     patches have no partial alpha

Rules this file follows:
  - nothing is read from work/ (gitignored, absent in a clean clone and in
    CI); every output goes to a tempfile directory. The one exception is the
    Lenin reference photograph, which lives in work/art/reference/ and is
    not redistributable: those tests skip cleanly when it is not there.
  - the generator runs are marked slow and are skipped with
    SD_SKIP_SLOW_ART=1, the way tests/test_smoke.py gates the real engine
    behind SD_ENGINE_TESTS.
  - QA finds, QA does not fix. Two real defects found while writing these
    tests are encoded as expected failures and reported to `art-director`;
    the marker comes off when the generator is fixed.

Run:  .venv/bin/python -m unittest tests.test_generators -v
      SD_SKIP_SLOW_ART=1 .venv/bin/python -m unittest tests.test_generators
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

# The macOS system fonts the generators rasterise Cyrillic with. Without them
# every generator that draws text raises, so those tests skip instead.
HAVE_FONTS = all(Path(p).is_file() for p in
                 ("/System/Library/Fonts/Supplemental/Impact.ttf",
                  "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"))

# The Lenin negative: work/ is gitignored and the photo is not redistributed.
LENIN_PHOTO = PROJECT_ROOT / "work" / "art" / "reference" / "lenin_1920_zhukov.jpg"
HAVE_LENIN_PHOTO = LENIN_PHOTO.is_file()

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
fonts = unittest.skipUnless(HAVE_FONTS, "macOS system fonts not present")
lenin_photo = unittest.skipUnless(
    HAVE_LENIN_PHOTO,
    f"reference photograph absent ({LENIN_PHOTO.relative_to(PROJECT_ROOT)} is under gitignored work/)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the full generator runs")

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
LUMP_RE = re.compile(r"^SD[A-Z0-9]{1,6}$")

# Tiling status as declared in docs/art/TEXTURE-INDEX.md, column "Tiles".
# A texture missing from this table is a texture whose tiling nobody
# declared: add the row to the index and the entry here.
DECLARED_TILEABLE = {
    "SDCONC1": True, "SDCONC2": True, "SDSTAR1": True, "SDSTEL1": True,
    "SDDOOR1": False, "SDPOSTR2": False,
    "SDFLR1": True, "SDFLR2": True, "SDFLR3": True,
    "SDCEIL1": True, "SDCEIL2": True,
}

# tiling_seam_score above this means the wrap edge is several times stronger
# than anything inside the texture, i.e. the noise stopped wrapping (a
# cropped field scores ~12, a full-range gradient ~51). It is deliberately
# NOT 1.0: SDSTEL1, SDCEIL1, SDCEIL2 and SDFLR3 put their panel joint, plate
# bevel or grout *on* the tile edge, so the seam IS the designed feature and
# the ratio exceeds 1 while the texture tiles perfectly. That those joints
# really sit on the edge is checked structurally instead, in
# PrefabWallGridTests and CeilingPanelTests.
SEAM_BROKEN_ABOVE = 3.0


def palette_colours() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours"]}


def colours_of(img) -> set:
    """Every distinct RGB in an image, whatever its mode."""
    return {tuple(int(v) for v in p) for p in np.asarray(img.convert("RGB")).reshape(-1, 3)}


# ===========================================================================
# gen_soviet_base - the declaration table (no pixels, always cheap)
# ===========================================================================
@imaging
class TextureTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        cls.gen = gen

    def test_entries_are_well_formed_and_unique(self):
        lumps = [t[0] for t in self.gen.TEXTURES]
        builders = [t[1] for t in self.gen.TEXTURES]
        self.assertEqual(len(lumps), len(set(lumps)), "two entries claim the same lump")
        self.assertEqual(len(builders), len(set(builders)), "two lumps share one builder")
        for lump, builder, kind, desc_en, desc_ru in self.gen.TEXTURES:
            self.assertRegex(lump, LUMP_RE, lump)
            self.assertLessEqual(len(lump), 8, lump)
            self.assertIn(kind, ("wall", "flat"), lump)
            self.assertTrue(callable(builder), lump)
            self.assertTrue(desc_en.strip(), lump)
            self.assertTrue(desc_ru.strip(), lump)

    def test_every_texture_has_a_russian_description(self):
        """D7: the preview sheet the CEO reads exists in both languages, so
        a Russian description that is really English text is a bug."""
        for lump, _, _, desc_en, desc_ru in self.gen.TEXTURES:
            self.assertTrue(CYRILLIC.search(desc_ru), f"{lump}: description_ru has no Cyrillic")
            self.assertGreater(len(desc_en.split()), 4, f"{lump}: description_en is a stub")

    def test_every_texture_declares_its_tiling_status(self):
        for lump, *_ in self.gen.TEXTURES:
            self.assertIn(lump, DECLARED_TILEABLE,
                          f"{lump} is new: declare 'Tiles' in docs/art/TEXTURE-INDEX.md "
                          f"and add it to DECLARED_TILEABLE here")

    def test_declared_sizes_are_doom_sizes(self):
        g = self.gen
        self.assertEqual((g.WALL_W, g.WALL_H), (64, 128))
        self.assertEqual(g.WIDE_W, 128)
        self.assertEqual(g.FLAT, 64)
        self.assertEqual(g.BATCH_SEED, 1977)   # D8, quoted by TEXTURE-INDEX


# ===========================================================================
# gen_soviet_base - the pixels
# ===========================================================================
@imaging
@fonts
class SovietBaseTextureTests(unittest.TestCase):
    """Builds the whole set once (~1 s) and checks the shipped artefact: the
    indexed PNG on disk, not just the array in memory."""

    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        from artlib import save_indexed, tiling_seam_score
        cls.gen = gen
        cls.seam = staticmethod(tiling_seam_score)
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.built = {}
        for lump, builder, kind, *_ in gen.TEXTURES:
            rgb = builder()
            path = cls.tmp / f"{lump}.png"
            save_indexed(rgb, path)
            cls.built[lump] = (kind, rgb, path)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_saved_pngs_are_indexed_and_the_declared_size(self):
        for lump, (kind, rgb, path) in self.built.items():
            h, w = rgb.shape[:2]
            with Image.open(path) as img:
                self.assertEqual(img.mode, "P", lump)
                self.assertEqual(img.size, (w, h), lump)
                self.assertEqual(w % 8, 0, lump)
                self.assertEqual(h % 8, 0, lump)
                if kind == "flat":
                    self.assertEqual(img.size, (64, 64), lump)
                else:
                    self.assertIn(img.size, [(64, 128), (128, 128), (128, 256)], lump)

    def test_saved_pngs_use_only_palette_colours(self):
        """test_art checks the in-memory quantise; this checks what actually
        reaches the PK3, after Pillow's optimised save and a reload."""
        pal = palette_colours()
        for lump, (_, _, path) in self.built.items():
            with Image.open(path) as img:
                used = colours_of(img)
            self.assertTrue(used <= pal, f"{lump}: off-palette {sorted(used - pal)[:5]}")
            self.assertLessEqual(len(used), 256, lump)

    def test_no_texture_is_flat_or_blank(self):
        """A builder that silently returns its background would pass every
        other check in this file."""
        for lump, (_, rgb, _) in self.built.items():
            self.assertGreater(len(np.unique(rgb.reshape(-1, 3), axis=0)), 8, lump)
            self.assertGreater(float(rgb.std()), 3.0, lump)

    def test_nothing_shows_a_seam_the_texture_does_not_already_have(self):
        for lump, (_, rgb, _) in self.built.items():
            score = self.seam(rgb)
            self.assertLess(score, SEAM_BROKEN_ABOVE,
                            f"{lump}: seam score {score:.2f} - the wrap edge is now the "
                            f"strongest feature in the texture, the noise stopped wrapping")

    def test_textures_declared_tileable_wrap_their_material(self):
        """For the textures whose joints are inside the tile (the concrete
        walls and the plain floors), the wrap edge must be no stronger than
        the strongest interior feature. The textures that carry their joint
        ON the edge by design are covered structurally elsewhere."""
        joint_on_the_edge = {"SDSTEL1", "SDFLR3", "SDCEIL1", "SDCEIL2"}
        for lump, (_, rgb, _) in self.built.items():
            if not DECLARED_TILEABLE[lump] or lump in joint_on_the_edge:
                continue
            score = self.seam(rgb)
            self.assertLessEqual(score, 1.0, f"{lump}: seam score {score:.2f} > 1.0")

    def test_the_red_stripe_of_sdconc2_sits_where_it_is_declared(self):
        """STRIPE_Y0..STRIPE_Y1 straddles the panel joint at y=64: the
        stripe must be red there and nowhere else."""
        g = self.gen
        rgb = self.built["SDCONC2"][1].astype(int)
        redness = rgb[..., 0] - rgb[..., 2]
        inside = redness[g.STRIPE_Y0:g.STRIPE_Y1].mean()
        outside = np.concatenate([redness[:g.STRIPE_Y0 - 2], redness[g.STRIPE_Y1 + 2:]]).mean()
        self.assertGreater(inside, 30, "no red stripe in the declared band")
        self.assertLess(outside, 10, "red paint outside the declared band")
        self.assertLess(g.STRIPE_Y0, g.PANEL_H, "the stripe no longer straddles the joint")
        self.assertGreater(g.STRIPE_Y1, g.PANEL_H)


@imaging
@fonts
class PrefabWallGridTests(unittest.TestCase):
    """prefab_wall is the base of three walls. Its contract: panel joints lie
    ON the texture edges (x=0, y=0) so two tiles side by side continue one
    grid, with the lower row of panels shifted half a panel (running bond).
    Checked at both widths the set uses: 64 for the plain walls, 128 for the
    plaque wall SDSTAR1."""

    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        cls.gen = gen

    def _luma(self, w):
        return self.gen.prefab_wall(self.gen.rng_for(1), w).mean(axis=2)

    def test_horizontal_joints_are_on_the_edge_and_at_the_panel_height(self):
        g = self.gen
        for w in (64, 128):
            rows = self._luma(w).mean(axis=1)
            median = float(np.median(rows))
            for y in (0, g.PANEL_H):
                self.assertLess(rows[y], 0.65 * median, f"w={w}: no groove at y={y}")
                self.assertGreater(rows[y + 2], 1.15 * median,
                                   f"w={w}: no lit lip under the groove at y={y}")
            self.assertGreater(rows[32], 0.85 * median, f"w={w}: unexpected groove at y=32")

    def test_vertical_joints_follow_the_running_bond(self):
        g = self.gen
        for w in (64, 128):
            luma = self._luma(w)
            upper = luma[6:g.PANEL_H - 2].mean(axis=0)
            lower = luma[g.PANEL_H + 6:].mean(axis=0)
            up_median, lo_median = float(np.median(upper)), float(np.median(lower))
            for x in range(0, w, g.WALL_W):                      # upper row
                self.assertLess(upper[x], 0.65 * up_median, f"w={w}: no joint at x={x} (upper)")
                self.assertGreater(lower[x], 0.85 * lo_median, f"w={w}: joint at x={x} in the lower row")
            for x in range(g.PANEL_OFFSET, w, g.WALL_W):         # lower row, half shifted
                self.assertLess(lower[x], 0.65 * lo_median, f"w={w}: no joint at x={x} (lower)")
                self.assertGreater(upper[x], 0.85 * up_median, f"w={w}: joint at x={x} in the upper row")

    def test_the_wide_wall_is_two_panels_wide(self):
        """At 128 the grid must repeat the 64 pattern, not stretch it."""
        g = self.gen
        luma = self._luma(128)
        upper = luma[6:g.PANEL_H - 2].mean(axis=0)
        joints = [x for x in range(128) if upper[x] < 0.65 * float(np.median(upper))]
        self.assertEqual(joints, [0, 64])


@imaging
@fonts
class CeilingPanelTests(unittest.TestCase):
    """The ceiling flats are one panel per tile with the groove on the edge,
    which is why their seam score is above 1 and why the groove position is
    checked here instead."""

    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        cls.gen = gen
        cls.panel = gen.ceiling_panel(gen.rng_for(11)).mean(axis=2)

    def test_the_groove_runs_along_the_top_and_left_edges(self):
        median = float(np.median(self.panel))
        self.assertLess(self.panel[0].mean(), 0.7 * median, "no groove on the top edge")
        self.assertLess(self.panel[:, 0].mean(), 0.7 * median, "no groove on the left edge")
        self.assertGreater(self.panel[-1].mean(), 0.95 * median, "bottom edge is not the lit lip")
        self.assertGreater(self.panel[:, -1].mean(), 0.95 * median, "right edge is not the lit lip")

    def test_the_middle_of_the_panel_is_clean(self):
        median = float(np.median(self.panel))
        self.assertGreater(self.panel[32].mean(), 0.85 * median)
        self.assertGreater(self.panel[:, 32].mean(), 0.85 * median)


@imaging
class CracksTilingTests(unittest.TestCase):
    """cracks() draws polylines on a plain Overlay, which has no notion of
    the tile wrapping."""

    DARK = 120   # the flat is painted 140; a crack pixel is well under it

    @classmethod
    def _dark(cls, line):
        """Where along one edge line a crack pixel sits."""
        return set(np.nonzero(line.mean(axis=1) < cls.DARK)[0].tolist())

    def test_cracks_tile(self):
        """QA BUG-ART-001, found by QA, fixed by art-director, and the
        assertion corrected by the PM on 2026-10-13 when the two disagreed.

        The bug was real: cracks() drew polylines on an Overlay that clips at
        the canvas, so a hairline died at the tile border on the three floors,
        the largest tiled surface in MAP01. art-director fixed it with
        Overlay.line_tiled.

        The ORIGINAL assertion here was wrong and would have stayed red over a
        correct fix. It required row 0 and row 63 to carry dark pixels at the
        same x. That only holds for a perfectly vertical crack: a diagonal
        one leaves the top edge at x and re-enters the bottom edge at x minus
        its run, so the sets differ by the slope. Measured after the fix,
        seeds 0 and 1 still fail equality while tiling perfectly.

        What seamlessness actually means is that the seam is no sharper than
        the texture's own detail, which is what the project's seam metric
        measures. After the fix the cracked flat scores 0.03 to 0.24 across
        six seeds; a vertical gradient, the canonical non-tiling case, scores
        51. The threshold below is generous by an order of magnitude and
        would still catch a crack that stopped dead at the border."""
        import gen_soviet_base as gen
        from artlib import tiling_seam_score
        base = np.full((64, 64, 3), 140, dtype=np.uint8)
        for seed in range(6):
            out = gen.cracks(base.copy(), np.random.default_rng(seed), 3)
            score = tiling_seam_score(out)
            self.assertLess(score, 3.0,
                            f"seed {seed}: seam score {score:.2f}, a crack dies at the border")

    def test_cracks_are_deterministic_and_darken_only_a_little(self):
        """What cracks() does get right, kept as a regression guard: same
        seed, same hairlines, and the lines stay hairlines."""
        import gen_soviet_base as gen
        base = np.full((64, 64, 3), 140, dtype=np.uint8)
        a = gen.cracks(base.copy(), np.random.default_rng(3), 2)
        b = gen.cracks(base.copy(), np.random.default_rng(3), 2)
        self.assertTrue(np.array_equal(a, b))
        darkened = (a.mean(axis=2) < 130).mean()
        self.assertGreater(darkened, 0.0, "no crack drawn at all")
        self.assertLess(darkened, 0.10, "the 'hairline' cracks cover a tenth of the flat")


@imaging
@fonts
@slow
class SovietBaseDeterminismTests(unittest.TestCase):
    """docs/art/TEXTURE-INDEX.md records script + seed as the origin of every
    approved texture. That is only provenance if a rebuild is identical."""

    def test_two_runs_produce_identical_arrays_and_identical_png_bytes(self):
        import gen_soviet_base as gen
        from artlib import save_indexed
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for lump, builder, *_ in gen.TEXTURES:
                first, second = builder(), builder()
                self.assertTrue(np.array_equal(first, second), f"{lump}: not deterministic")
                a, b = root / f"{lump}.a.png", root / f"{lump}.b.png"
                save_indexed(first, a)
                save_indexed(second, b)
                self.assertEqual(a.read_bytes(), b.read_bytes(), f"{lump}: PNG bytes differ")


@imaging
@fonts
@slow
class SovietBaseMainTests(unittest.TestCase):
    """main() writes the PNGs and the manifest the preview sheet is built
    from. Run with OUT_DIR/MANIFEST redirected into a tempfile directory, so
    the test never touches work/ and never depends on it existing."""

    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        cls.gen = gen
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "soviet_base"
        manifest = Path(cls._tmp.name) / "manifest.json"
        # main() records each file as a path relative to PROJECT_ROOT, so
        # that moves to the temporary root as well: nothing is written into
        # the repository, and work/ is never touched.
        old = (gen.OUT_DIR, gen.MANIFEST, gen.PROJECT_ROOT)
        gen.OUT_DIR, gen.MANIFEST, gen.PROJECT_ROOT = cls.out, manifest, Path(cls._tmp.name)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                gen.main()
        finally:
            gen.OUT_DIR, gen.MANIFEST, gen.PROJECT_ROOT = old
        cls.manifest = json.loads(manifest.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_one_png_per_declared_texture(self):
        files = sorted(p.name for p in self.out.glob("*.png"))
        self.assertEqual(files, sorted(f"{t[0]}.png" for t in self.gen.TEXTURES))

    def test_manifest_describes_every_texture(self):
        entries = {e["lump"]: e for e in self.manifest["textures"]}
        self.assertEqual(set(entries), {t[0] for t in self.gen.TEXTURES})
        for lump, _, kind, *_ in self.gen.TEXTURES:
            e = entries[lump]
            self.assertEqual(e["kind"], kind, lump)
            with Image.open(self.out / f"{lump}.png") as img:
                self.assertEqual((e["width"], e["height"]), img.size, lump)
                self.assertEqual(e["colours_used"], len(set(img.get_flattened_data())), lump)
            self.assertGreater(e["colours_used"], 1, lump)
            self.assertTrue(CYRILLIC.search(e["description_ru"]), lump)
            self.assertIsInstance(e["seam_score"], (int, float), lump)

    def test_manifest_records_the_batch_header(self):
        self.assertEqual(self.manifest["batch_seed"], self.gen.BATCH_SEED)
        self.assertEqual(self.manifest["script"], "tools/art/gen_soviet_base.py")
        self.assertTrue(CYRILLIC.search(self.manifest["font_note_ru"]))

    def test_the_recorded_seed_is_the_seed_the_texture_was_built_with(self):
        """QA BUG-ART-003 (owner: art-director, severity medium).

        Repro: build the manifest and compare each entry's "seed" with the
        offset the builder actually passes to rng_for().
        Expected: equal. The seed column of docs/art/TEXTURE-INDEX.md and
        the preview sheet quote this number as the origin of the texture;
        "rebuild with seed N" has to reproduce the bytes.
        Observed: 6 of the 11 entries are off by one -
            SDPOSTR2 recorded 1983, built with 1984
            SDFLR1   recorded 1984, built with 1985
            SDFLR2   recorded 1985, built with 1986
            SDFLR3   recorded 1986, built with 1987
            SDCEIL1  recorded 1987, built with 1988
            SDCEIL2  recorded 1988, built with 1989
        Cause: main() derives the seed from the position in TEXTURES
        (`enumerate(..., start=1)`) while each builder hardcodes its own
        `rng_for(n)`. Dropping SDPOSTR1 from TEXTURES shifted every entry
        after SDDOOR1. TEXTURE-INDEX.md still lists the pre-shift seeds, so
        the index and the manifest now disagree too.
        Fix direction: record the offset the builder uses (give TEXTURES an
        explicit seed_offset column) instead of its position in the list.
        Remove this marker when the manifest records the real seed."""
        gen = self.gen
        entries = {e["lump"]: e for e in self.manifest["textures"]}
        real = gen.rng_for
        used = []

        def recording(offset):
            used.append(offset)
            return real(offset)

        gen.rng_for = recording
        try:
            for lump, builder, *_ in gen.TEXTURES:
                used.clear()
                builder()
                self.assertTrue(used, f"{lump}: builder never asked for a seed")
                self.assertEqual(entries[lump]["seed"], gen.BATCH_SEED + used[0],
                                 f"{lump}: manifest seed is not the seed used")
        finally:
            gen.rng_for = real


# ===========================================================================
# gen_lenin - SDPOSTR1
# ===========================================================================
@imaging
@fonts
@lenin_photo
class LeninPosterTests(unittest.TestCase):
    """The poster that cost four rounds. The hard contract, in the words of
    its own docstring and of docs/art/TEXTURE-INDEX.md: 128x256, exactly
    INK_COUNT flat inks plus the gold rule, every one of them a palette
    colour, and the Cyrillic slogan stamped through a HARD-CUT mask -
    Pillow's antialiasing had invented 95 off-palette colours and check_pk3
    rejected the first build."""

    @classmethod
    def setUpClass(cls):
        import gen_lenin as lenin
        from artlib import ramp_colour
        cls.lenin = lenin
        cls.gold = ramp_colour("hazard_yellow", 0.86)
        cls.img = lenin.poster()
        cls.plain = lenin.poster(slogan="")

    def test_the_poster_is_the_declared_size_and_mode(self):
        self.assertEqual(self.img.size, (self.lenin.WIDTH, self.lenin.HEIGHT))
        self.assertEqual(self.img.size, (128, 256))
        self.assertEqual(self.img.mode, "RGB")
        self.assertEqual(self.img.width % 8, 0)
        self.assertEqual(self.img.height % 8, 0)

    def test_exactly_the_declared_number_of_inks(self):
        """The regression guard for the 95-colour build: the poster is
        INK_COUNT flat inks plus the single gold rule, and nothing else."""
        expected = set(self.lenin.inks()) | {self.gold}
        self.assertEqual(len(expected), self.lenin.INK_COUNT + 1)
        self.assertEqual(colours_of(self.img), expected)
        self.assertEqual(len(colours_of(self.img)), self.lenin.INK_COUNT + 1)

    def test_every_ink_is_a_palette_colour(self):
        self.assertTrue(colours_of(self.img) <= palette_colours())

    def test_the_portrait_itself_is_exactly_ink_count_colours(self):
        body = self.lenin.HEIGHT - self.lenin.SLOGAN_BAND
        portrait = self.lenin.portrait()
        self.assertEqual(portrait.shape, (body, self.lenin.WIDTH, 3))
        self.assertEqual(len({tuple(p) for p in portrait.reshape(-1, 3)}), self.lenin.INK_COUNT)
        self.assertEqual(set(map(tuple, np.unique(portrait.reshape(-1, 3), axis=0))),
                         set(self.lenin.inks()))

    def test_the_portrait_uses_all_four_inks_in_quantity(self):
        """Percentile cuts, not absolute greys: no ink may collapse to a
        handful of pixels whatever the exposure of the negative."""
        portrait = self.lenin.portrait()
        _, counts = np.unique(portrait.reshape(-1, 3), axis=0, return_counts=True)
        share = counts / counts.sum()
        self.assertGreaterEqual(float(share.min()), 0.05, f"ink shares {sorted(share.round(3))}")

    def test_the_slogan_is_stamped_hard_inside_its_own_band(self):
        """A hard cut, so: only the slogan band changes, the change is
        exactly one ink (no antialiased in-between tone), and it is the
        cream the design asks for."""
        a, b = np.asarray(self.img), np.asarray(self.plain)
        changed = np.any(a != b, axis=2)
        body = self.lenin.HEIGHT - self.lenin.SLOGAN_BAND
        self.assertTrue(changed.any(), "the slogan drew nothing")
        self.assertFalse(changed[:body].any(), "the slogan leaked out of its band")
        rows = np.nonzero(changed.any(axis=1))[0]
        self.assertGreaterEqual(int(rows.min()), body)
        self.assertLess(int(rows.max()), self.lenin.HEIGHT)
        self.assertEqual({tuple(int(v) for v in p) for p in a[changed]}, {self.lenin.inks()[3]})
        self.assertEqual(colours_of(self.plain), colours_of(self.img))

    def test_an_empty_slogan_still_builds_a_valid_poster(self):
        self.assertEqual(self.plain.size, (128, 256))
        self.assertTrue(colours_of(self.plain) <= palette_colours())

    def test_the_printed_border_frames_the_whole_poster(self):
        a = np.asarray(self.img)
        cream = self.lenin.inks()[3]
        for px in (a[0, 0], a[0, -1], a[-1, 0], a[-1, -1], a[0, 64], a[-1, 64]):
            self.assertEqual(tuple(int(v) for v in px), cream)

    def test_the_cut_parameters_are_the_cell_the_ceo_chose(self):
        """CEO 2026-10-12 picked cell 4C of the sweep: four inks, cut +0."""
        self.assertEqual(self.lenin.INK_COUNT, 4)
        self.assertEqual(self.lenin.CUT_BIAS, 0)
        self.assertEqual((self.lenin.WIDTH, self.lenin.HEIGHT), (128, 256))

    def test_the_poster_is_deterministic(self):
        self.assertEqual(np.asarray(self.lenin.poster()).tobytes(),
                         np.asarray(self.img).tobytes())

    def test_a_different_cut_bias_changes_the_image_but_not_the_ink_count(self):
        other = self.lenin.poster(bias=12)
        self.assertNotEqual(np.asarray(other).tobytes(), np.asarray(self.img).tobytes())
        self.assertTrue(colours_of(other) <= set(self.lenin.inks()) | {self.gold})


@imaging
@fonts
@lenin_photo
@slow
class LeninSweepTests(unittest.TestCase):
    """--sweep is the review tool the CEO points at. It must not blow up,
    and it must leave the module as it found it: it drives INK_COUNT through
    a module global."""

    def test_sweep_writes_a_sheet_and_restores_the_ink_count(self):
        import gen_lenin as lenin
        before = lenin.INK_COUNT
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lenin_sweep.png"
            lenin.sweep(out)
            self.assertTrue(out.is_file())
            with Image.open(out) as sheet:
                self.assertGreater(sheet.width, lenin.WIDTH * 5)
                self.assertGreater(sheet.height, lenin.HEIGHT)
                self.assertEqual(sheet.mode, "RGB")
        self.assertEqual(lenin.INK_COUNT, before)

    def test_every_sweep_cell_posterises_to_its_own_ink_count(self):
        """The sheet is only a review tool if each row really is 2, 3 and 4
        inks. Checked through the same global the sweep drives."""
        import gen_lenin as lenin
        before = lenin.INK_COUNT
        try:
            for n in (2, 3, 4):
                lenin.INK_COUNT = n
                for bias in (-18, 0, 18):
                    cell = lenin.portrait(bias)
                    self.assertLessEqual(len({tuple(p) for p in cell.reshape(-1, 3)}), n,
                                         f"{n} inks, bias {bias:+d}")
        finally:
            lenin.INK_COUNT = before


# ===========================================================================
# gen_shell - TITLEPIC / INTERPIC / M_DOOM
# ===========================================================================
@imaging
class ShellDeclarationTests(unittest.TestCase):
    """Cheap checks on the shell contract: the sizes the engine expects and
    the three kits the CEO is to choose between."""

    @classmethod
    def setUpClass(cls):
        import gen_shell as shell
        cls.shell = shell

    def test_screen_and_logo_sizes_are_the_doom_ones(self):
        s = self.shell
        self.assertEqual((s.SCREEN_W, s.SCREEN_H), (320, 200))
        self.assertEqual((s.LOGO_W, s.LOGO_H), (200, 64))
        self.assertEqual(s.LOGO_H % 8, 0)
        self.assertEqual(s.LOCKUP_X0, (s.SCREEN_W - s.LOGO_W) // 2)
        self.assertEqual(s.ASPECT, 1.2)

    def test_the_screens_table_declares_the_real_sizes(self):
        s = self.shell
        declared = {name: (w, h) for name, _, w, h, *_ in s.SCREENS}
        self.assertEqual(declared["TITLEPIC"], (320, 200))
        self.assertEqual(declared["INTERPIC"], (320, 200))
        self.assertEqual(declared["M_DOOM"], (200, 64))

    def test_three_kits_with_unique_keys_and_both_languages(self):
        keys = [k["key"] for k in self.shell.KITS]
        self.assertEqual(keys, ["A", "B", "C"])
        for kit in self.shell.KITS:
            self.assertTrue(CYRILLIC.search(kit["concept_ru"]), kit["key"])
            self.assertTrue(kit["concept_en"].strip(), kit["key"])
            self.assertTrue(callable(kit["titlepic"]) and callable(kit["interpic"]), kit["key"])
            self.assertTrue(callable(kit["lockup"]), kit["key"])


@imaging
@fonts
@slow
class ShellScreenTests(unittest.TestCase):
    """Runs build() once (~5 s) with OUT_DIR/MANIFEST redirected to a
    tempfile directory, then checks the files it wrote: what the engine will
    load, not an intermediate array."""

    @classmethod
    def setUpClass(cls):
        import gen_shell as shell
        cls.shell = shell
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name)
        old = (shell.OUT_DIR, shell.MANIFEST)
        shell.OUT_DIR, shell.MANIFEST = cls.out, cls.out / "manifest.json"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cls.manifest = shell.build()
        finally:
            shell.OUT_DIR, shell.MANIFEST = old

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_titlepic_and_interpic_are_320x200_indexed(self):
        for kit in self.shell.KITS:
            for name in ("TITLEPIC", "INTERPIC"):
                path = self.out / f"{name}_{kit['key']}.png"
                with Image.open(path) as img:
                    self.assertEqual(img.size, (320, 200), path.name)
                    self.assertEqual(img.mode, "P", path.name)

    def test_m_doom_is_200x64_with_hard_alpha(self):
        """Doom patches have no partial alpha: anything between 0 and 255
        would come out as a fringe of wrong pixels around the logo."""
        for kit in self.shell.KITS:
            path = self.out / f"M_DOOM_{kit['key']}.png"
            with Image.open(path) as img:
                self.assertEqual(img.size, (200, 64), path.name)
                self.assertEqual(img.mode, "RGBA", path.name)
                alpha = np.asarray(img)[..., 3]
            self.assertEqual(set(np.unique(alpha).tolist()), {0, 255}, path.name)
            share = float((alpha == 255).mean())
            self.assertGreater(share, 0.02, f"{path.name}: the logo is practically empty")
            self.assertLess(share, 0.98, f"{path.name}: the logo has no transparent ground")

    def test_all_three_screens_use_only_palette_colours(self):
        pal = palette_colours()
        for kit in self.shell.KITS:
            for name in ("TITLEPIC", "INTERPIC", "M_DOOM"):
                path = self.out / f"{name}_{kit['key']}.png"
                with Image.open(path) as img:
                    used = colours_of(img)
                self.assertTrue(used <= pal, f"{path.name}: off-palette {sorted(used - pal)[:5]}")
                self.assertLessEqual(len(used), 256, path.name)

    def test_the_manifest_matches_the_files_on_disk(self):
        for entry in self.manifest["kits"]:
            for name, declared in entry["screens"].items():
                path = self.out / declared["file"]
                self.assertTrue(path.is_file(), declared["file"])
                if declared.get("preview_only"):
                    continue
                with Image.open(path) as img:
                    self.assertEqual((declared["w"], declared["h"]), img.size, declared["file"])
            logo = entry["screens"]["M_DOOM"]
            self.assertEqual(logo["alpha"], "binary (0/255)")
            self.assertEqual((logo["menudef_x"], logo["menudef_y"]),
                             (self.shell.LOCKUP_X0, self.shell.LOCKUP_Y0))
        self.assertEqual(self.manifest["screen"], [320, 200])
        self.assertEqual(self.manifest["logo"], [200, 64])

    def test_the_logo_registers_on_the_title_it_covers(self):
        """M_DOOM is the title's own lockup: pasted at the MENUDEF origin it
        must land on the lockup already painted there, not beside it."""
        for kit in self.shell.KITS:
            with Image.open(self.out / f"TITLEPIC_{kit['key']}.png") as t:
                title = np.asarray(t.convert("RGB"), dtype=int)
            with Image.open(self.out / f"M_DOOM_{kit['key']}.png") as m:
                logo = np.asarray(m, dtype=int)
            x0, y0 = self.shell.LOCKUP_X0, self.shell.LOCKUP_Y0
            under = title[y0:y0 + logo.shape[0], x0:x0 + logo.shape[1]]
            opaque = logo[..., 3] == 255
            diff = np.abs(under[opaque] - logo[opaque][..., :3]).mean()
            self.assertLess(diff, 40.0, f"kit {kit['key']}: the logo does not register on the title")

    def test_the_screens_are_deterministic(self):
        for kit in self.shell.KITS[:1]:   # one kit is enough and keeps this cheap
            self.assertTrue(np.array_equal(kit["titlepic"](), kit["titlepic"]()))
            self.assertTrue(np.array_equal(
                np.asarray(self.shell.logo(kit["lockup"], kit["plate"])),
                np.asarray(self.shell.logo(kit["lockup"], kit["plate"]))))


if __name__ == "__main__":
    unittest.main()
