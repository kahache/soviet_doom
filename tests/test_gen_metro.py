"""Contract of tools/art/gen_metro.py and of the metro set in assets/ (D42, D48).

The CEO approved the metro's first six pieces as drawn in palette v1
(D42, 2026-10-13: «OK a las 6 piezas de metro») and then the ten fill
pieces of gen_metro.py --fill, also as drawn in palette v1 (D48,
2026-10-14: «PERFECTO»). Then the CEO took the mosaic in palette v2 (D56,
2026-10-14: «mosaico V2»): SDMOSA1 is now its v2 rendering, the only metro
lump outside v1; SDMARB1 stays v1. What is checked:

  installed   assets/textures/metro/ and assets/flats/metro/ hold exactly the
              approved lumps, at the declared sizes, indexed PNGs
  generator   each installed lump is pixel-identical to what gen_metro.py
              builds from its seed today, quantised to the palette version
              it was approved in, so a later edit of the generator
              (the set is being filled out) cannot silently drift away from
              the approved art
  no font     the generator never rasterises text with a system font, which
              is why its lumps reproduce byte for byte on the Mac and on
              Windows (CLAUDE.md, "Text-bearing assets do not reproduce")
  paper       every installed lump has an approved row in TEXTURE-INDEX.md
              and a row in LICENSES.md
  mosaic v2   D56: SDMOSA1 is the v2 build byte for byte, the D42 v1 stays
              reachable as history (--mosaic-v1) and is never installed
  fill        the fill pieces (--fill, approved in D48): names, seeds,
              sizes, palette v1, determinism, and the generator never writes
              them into assets/ (the PM installs approved files by hand)

All of it is cheap: the builders run in well under a second, so nothing
here is gated behind SD_SKIP_SLOW_ART.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
ASSETS = PROJECT_ROOT / "assets"
METRO_WALLS = ASSETS / "textures" / "metro"
METRO_FLATS = ASSETS / "flats" / "metro"
TEXTURE_INDEX = PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

# D42: the six approved pieces, lump -> (kind, width, height).
APPROVED_D42 = {
    "SDTILE1": ("wall", 64, 128),
    "SDTILE2": ("wall", 64, 128),
    "SDMARB1": ("wall", 64, 128),
    "SDMOSA1": ("wall", 128, 128),
    "SDBRAS1": ("wall", 64, 128),
    "SDMFLR1": ("flat", 64, 64),
}
D42_BATCH_SEED = 1935
# D48: the ten fill pieces (gen_metro.py --fill), lump -> (kind, width, height).
APPROVED_D48 = {
    "SDMFLR2": ("flat", 64, 64),
    "SDMFLR3": ("flat", 64, 64),
    "SDMEDG1": ("wall", 64, 64),
    "SDTUNL1": ("wall", 64, 128),
    "SDTUBB1": ("wall", 128, 128),
    "SDRAIL1": ("flat", 64, 64),
    "SDMCEIL1": ("flat", 64, 64),
    "SDMCEIL2": ("flat", 64, 64),
    "SDMARB2": ("wall", 64, 128),
    "SDTILE3": ("wall", 64, 128),
}
INSTALLED = {**APPROVED_D42, **APPROVED_D48}   # every metro lump in assets/, approved


def installed_files() -> dict[str, Path]:
    out = {}
    for base in (METRO_WALLS, METRO_FLATS):
        if base.is_dir():
            for p in sorted(base.glob("*.png")):
                out[p.stem] = p
    return out


class NoFontTests(unittest.TestCase):
    def test_generator_uses_no_system_font(self):
        src = (ART_TOOLS / "gen_metro.py").read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", src, flags=re.S)       # docstrings may talk about fonts
        for banned in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text(", "truetype"):
            self.assertNotIn(banned, code, banned)


class PaperTrailTests(unittest.TestCase):
    def test_every_installed_lump_is_indexed_as_approved(self):
        text = TEXTURE_INDEX.read_text(encoding="utf-8")
        for lump in INSTALLED:
            rows = [ln for ln in text.splitlines() if ln.startswith(f"| `{lump}` |")]
            self.assertEqual(len(rows), 1, f"{lump}: expected one row in TEXTURE-INDEX.md")
            status = rows[0].split("|")[7]
            self.assertIn("approved", status, f"{lump}: {status.strip()}")

    def test_every_installed_lump_has_a_licence_row(self):
        text = LICENSES.read_text(encoding="utf-8")
        for lump in INSTALLED:
            self.assertIn(f"`{lump}`", text, lump)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class InstalledMetroTests(unittest.TestCase):
    def test_exactly_the_approved_lumps_are_installed(self):
        self.assertEqual(set(installed_files()), set(INSTALLED))

    def test_walls_and_flats_in_their_folders(self):
        files = installed_files()
        for lump, (kind, _, _) in INSTALLED.items():
            folder = METRO_FLATS if kind == "flat" else METRO_WALLS
            self.assertEqual(files[lump].parent, folder, lump)

    def test_sizes_and_indexed(self):
        from PIL import Image
        for lump, path in installed_files().items():
            _, w, h = INSTALLED[lump]
            with Image.open(path) as img:
                self.assertEqual(img.size, (w, h), lump)
                self.assertEqual(img.mode, "P", lump)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class GeneratorHoldsApprovedArtTests(unittest.TestCase):
    """Rebuild each approved lump from its seed and compare pixels with the
    installed file. Pixels, not bytes: PNG encoding is not the contract, the
    image is."""

    @classmethod
    def setUpClass(cls):
        import gen_metro
        cls.g = gen_metro
        cls.builders = {lump: builder for lump, builder, *_ in
                        gen_metro.TEXTURES + gen_metro.FILL_TEXTURES}

    def test_d42_seeds_unchanged(self):
        self.assertEqual(self.g.BATCH_SEED, D42_BATCH_SEED)
        expected = {"SDTILE1": 1, "SDTILE2": 2, "SDMARB1": 3,
                    "SDMOSA1": 4, "SDBRAS1": 5, "SDMFLR1": 6}
        for lump, offset in expected.items():
            self.assertEqual(self.g.SEED_OFFSET[lump], offset, lump)

    def test_d48_seeds_unchanged(self):
        expected = {"SDMFLR2": 7, "SDMFLR3": 8, "SDMEDG1": 9, "SDTUNL1": 10,
                    "SDTUBB1": 11, "SDRAIL1": 12, "SDMCEIL1": 13, "SDMCEIL2": 14,
                    "SDMARB2": 15, "SDTILE3": 16}
        self.assertEqual(set(expected), set(APPROVED_D48))
        for lump, offset in expected.items():
            self.assertEqual(self.g.SEED_OFFSET[lump], offset, lump)

    def test_every_installed_lump_has_a_builder(self):
        self.assertEqual(set(self.builders), set(INSTALLED))

    def test_installed_pixels_match_generator(self):
        import numpy as np
        from PIL import Image
        for lump, path in installed_files().items():
            built = self.g.quantize_lump(lump, self.builders[lump]()).convert("RGB")
            with Image.open(path) as img:
                shipped = img.convert("RGB")
            a, b = np.asarray(built), np.asarray(shipped)
            self.assertEqual(a.shape, b.shape, lump)
            diff = int((a != b).any(axis=-1).sum())
            self.assertEqual(diff, 0, f"{lump}: {diff} px differ from the approved file")


WALL_SIZES = {(64, 64), (64, 128), (128, 64), (128, 128), (128, 256)}   # ART-BIBLE §2
LUMP_RE = re.compile(r"^SD[A-Z0-9]{1,6}$")


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class FillDraftTests(unittest.TestCase):
    """The fill pieces (gen_metro.py --fill, drafted 2026-10-13, approved by
    the CEO 2026-10-14 in D48, «PERFECTO»): the generator's contract for
    them, palette v1. The installed files are held to the generator by
    GeneratorHoldsApprovedArtTests; here --fill still writes to work/ only,
    never into the approved folder (the PM copies approved files by hand)."""

    @classmethod
    def setUpClass(cls):
        import gen_metro
        from artlib import quantize
        from PIL import Image
        cls.g = gen_metro
        cls.built = {}
        for lump, builder, kind, _ in gen_metro.FILL_TEXTURES:
            rgb = builder()
            cls.built[lump] = (kind, rgb, quantize(Image.fromarray(rgb, "RGB")))

    def test_names_and_seeds(self):
        approved = {t[0] for t in self.g.TEXTURES}
        self.assertEqual(set(self.built), set(self.g.FILL_SEED_OFFSET))
        self.assertFalse(set(self.built) & approved, "a draft reuses an approved lump name")
        for lump in self.built:
            self.assertRegex(lump, LUMP_RE)
        offsets = list(self.g.SEED_OFFSET.values())
        self.assertEqual(len(offsets), len(set(offsets)), "two metro pieces share a seed")
        self.assertGreater(min(self.g.FILL_SEED_OFFSET.values()),
                           max(self.g.SEED_OFFSET[l] for l in APPROVED_D42))

    def test_drafts_never_write_into_the_approved_folder(self):
        self.assertNotEqual(self.g.FILL_DIR, self.g.OUT_DIR)

    def test_batch_size_within_rules(self):
        self.assertTrue(6 <= len(self.built) <= 12, len(self.built))

    def test_sizes(self):
        for lump, (kind, rgb, _) in self.built.items():
            h, w = rgb.shape[:2]
            if kind == "flat":
                self.assertEqual((w, h), (64, 64), lump)
            else:
                self.assertIn((w, h), WALL_SIZES, lump)

    def test_palette_v1_only(self):
        import json
        pal_json = PROJECT_ROOT / "docs" / "art" / "palette.json"
        pal = {tuple(c) for c in json.loads(pal_json.read_text(encoding="utf-8"))["colours"]}
        for lump, (_, _, img) in self.built.items():
            p = img.getpalette()
            used = {tuple(p[i * 3:i * 3 + 3]) for i in set(img.get_flattened_data())}
            self.assertTrue(used <= pal, f"{lump}: {used - pal}")

    def test_deterministic(self):
        import numpy as np
        for lump, builder, *_ in self.g.FILL_TEXTURES:
            self.assertTrue(np.array_equal(builder(), self.built[lump][1]), lump)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class PaletteV2ProposalTests(unittest.TestCase):
    """gen_metro.py --v2 (D45, 2026-10-14): SDMARB1 and SDMOSA1 redrawn in
    palette v2 as proposals. Same seed and geometry as the approved lumps,
    new inks only; written to work/art/batch2/metro_v2/, never to assets/
    and never under an approved lump's file name."""

    @classmethod
    def setUpClass(cls):
        import gen_metro
        import palette
        cls.g = gen_metro
        cls.v1 = set(palette.colours(1))
        cls.v2 = set(palette.colours(2))
        cls.built = {lump: builder() for lump, builder, _ in gen_metro.V2_TEXTURES}
        cls.quant = {lump: np.asarray(gen_metro.quantize_version(rgb, 2).convert("RGB"))
                     for lump, rgb in cls.built.items()}

    def test_exactly_the_two_palette_limited_pieces(self):
        self.assertEqual(set(self.built), {"SDMARB1", "SDMOSA1"})
        self.assertEqual(set(self.built), set(self.g.PALETTE_LIMITED))
        self.assertTrue(set(self.built) <= set(APPROVED_D42))

    def test_same_size_as_the_approved_lump(self):
        for lump, rgb in self.built.items():
            _, w, h = APPROVED_D42[lump]
            self.assertEqual(rgb.shape[:2], (h, w), lump)

    def test_inside_v2_and_really_using_it(self):
        for lump, q in self.quant.items():
            used = {tuple(int(v) for v in c) for c in q.reshape(-1, 3)}
            self.assertTrue(used <= self.v2, f"{lump}: {used - self.v2}")
            self.assertGreaterEqual(len(used - self.v1), 8, f"{lump}: hardly any v2 colour")

    def test_deterministic(self):
        for lump, builder, _ in self.g.V2_TEXTURES:
            self.assertTrue(np.array_equal(builder(), self.built[lump]), lump)

    def test_same_geometry_only_the_inks_change(self):
        """With the v1 inks, the shared builders give back the D42 lumps
        exactly: the v2 proposals differ in colour alone. Since D56 the
        mosaic's D42 v1 is tex_mosa1_v1 and tex_mosa1 is the v2 build."""
        g = self.g
        self.assertTrue(np.array_equal(
            g.marble_field(g.WALL_W, g.WALL_H, g.rng_for("SDMARB1"), g.STONE_V1), g.tex_marb1()))
        self.assertTrue(np.array_equal(g.mosaic_panel(g.rng_for("SDMOSA1"), g.MOSA_INKS_V1), g.tex_mosa1_v1()))
        self.assertTrue(np.array_equal(g.tex_mosa1_v2(), g.tex_mosa1()))

    def test_quantize_version_1_is_artlib(self):
        from PIL import Image
        from artlib import quantize
        rgb = self.built["SDMOSA1"]
        a = np.asarray(self.g.quantize_version(rgb, 1).convert("RGB"))
        b = np.asarray(quantize(Image.fromarray(rgb, "RGB")).convert("RGB"))
        self.assertTrue(np.array_equal(a, b))

    def test_proposals_never_land_on_an_approved_name_or_folder(self):
        g = self.g
        self.assertNotEqual(g.V2_DIR, g.OUT_DIR)
        self.assertNotIn("assets", g.V2_DIR.relative_to(PROJECT_ROOT).parts)
        for lump, *_ in g.V2_TEXTURES:
            self.assertNotEqual(lump + g.V2_SUFFIX, lump)

    def test_build_and_sheet_in_a_temp_dir(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with mock.patch.object(self.g, "V2_DIR", tmp / "metro_v2"):
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    entries, files = self.g.build_v2()
                sheet = self.g.build_v2_sheet(entries, files, "2099-01-01_0000", out_dir=tmp / "previews")
            names = {p.name for p in (tmp / "metro_v2").glob("*.png")}
            self.assertIn("SDMARB1_v2.png", names)
            self.assertIn("SDMOSA1_v2.png", names)
            self.assertFalse(names & {f"{lump}.png" for lump in INSTALLED},
                             "a work file named like an approved lump breaks tests/test_art.py")
            for e in entries:
                self.assertEqual(e["palette_version"], 2)
                self.assertGreater(e["v2_colours_used"], 0)
            text = sheet.read_text(encoding="utf-8")
            self.assertEqual(sheet.name, "2099-01-01_0000_F3_metro-palette-v2.html")
            # D56: SDMOSA1's "v1" view is its rendered history, not assets/
            self.assertIn("SDMOSA1_v1.png", names)
            for lump in ("SDMARB1", "SDMOSA1"):
                self.assertIn(f"{lump} &rarr; {lump}_v2", text)
            self.assertIn("v1 approved", text)
            self.assertNotIn('src="http', text)            # self-contained


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class MosaicV2InstalledTests(unittest.TestCase):
    """D56 (2026-10-14, «mosaico V2»): SDMOSA1 is the palette v2 rendering,
    the lump name unchanged; the D42 v1 is history; nothing else moved."""

    @classmethod
    def setUpClass(cls):
        import gen_metro
        import palette
        cls.g = gen_metro
        cls.v1 = set(palette.colours(1))
        cls.v2 = set(palette.colours(2))
        cls.installed = installed_files()["SDMOSA1"]

    @staticmethod
    def png_bytes(img) -> bytes:
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    @staticmethod
    def used(img) -> set:
        pal = img.getpalette()
        return {tuple(pal[i * 3:i * 3 + 3]) for i in set(img.get_flattened_data())}

    def test_only_the_mosaic_is_v2(self):
        self.assertEqual(self.g.palette_version("SDMOSA1"), 2)
        for lump in INSTALLED:
            if lump != "SDMOSA1":
                self.assertEqual(self.g.palette_version(lump), 1, lump)
        self.assertEqual(self.g.palette_version("SDMARB1"), 1)     # D56: the marble stays v1

    def test_installed_is_the_v2_build_byte_for_byte(self):
        built = self.png_bytes(self.g.quantize_lump("SDMOSA1", self.g.tex_mosa1()))
        self.assertEqual(self.installed.read_bytes(), built)

    def test_installed_uses_palette_v2(self):
        from PIL import Image
        with Image.open(self.installed) as img:
            used = self.used(img)
        self.assertTrue(used <= self.v2, used - self.v2)
        self.assertGreaterEqual(len(used - self.v1), 8, "the installed mosaic is hardly v2")

    def test_v1_history_is_v1_and_not_installed(self):
        hist = self.g.quantize_version(self.g.tex_mosa1_v1(), 1)
        self.assertTrue(self.used(hist) <= self.v1)
        self.assertNotEqual(self.png_bytes(hist), self.installed.read_bytes())

    def test_v1_lumps_save_exactly_as_artlib(self):
        """save_lump on a v1 lump is artlib.save_indexed: the other fifteen
        metro lumps keep their bytes."""
        import tempfile
        from artlib import save_indexed
        rgb = self.g.tex_tile1()
        with tempfile.TemporaryDirectory() as tmp:
            a = self.g.save_lump("SDTILE1", rgb, Path(tmp) / "a.png")
            save_indexed(rgb, Path(tmp) / "b.png")
            self.assertEqual((Path(tmp) / "a.png").read_bytes(), (Path(tmp) / "b.png").read_bytes())
            self.assertEqual(a.mode, "P")

    def test_mosaic_v1_flag_writes_history_only(self):
        import contextlib
        import io
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "metro_history"
            with mock.patch.object(self.g, "HIST_DIR", hist),                     mock.patch.object(sys, "argv", ["gen_metro.py", "--mosaic-v1"]),                     contextlib.redirect_stdout(io.StringIO()):
                self.g.main()
            names = {p.name for p in hist.glob("*.png")}
            self.assertEqual(names, {"SDMOSA1_v1.png"})
            self.assertFalse(names & {f"{lump}.png" for lump in INSTALLED})
        self.assertNotIn("assets", self.g.HIST_DIR.relative_to(PROJECT_ROOT).parts)


if __name__ == "__main__":
    unittest.main()
