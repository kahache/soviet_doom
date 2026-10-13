"""Behaviour tests for the three art-review tools no test imported until now.

  tools/art/make_preview.py   the self-contained HTML sheet the CEO validates
                              a batch on (ART-BIBLE §7): status read from the
                              texture index, every PNG inlined, EN + RU
  tools/art/make_contact.py   the contact sheet for a quick look in chat:
                              every lump side by side, nearest zoom, name above
  tools/art/emblem_check.py   the SDSTAR1 hammer-and-sickle check sheet: the
                              emblem alone, the same with the CEO's reference
                              guides, and SDSTAR1 at 8x nearest

D27: nothing here writes to work/, assets/ or docs/. Every output path a
tool holds as a module constant is redirected to a temp directory with
mock.patch.object, and the only files read from the repo are the palette,
the texture index, SDSTAR1 and M_DOOM-free fixtures (read-only).

Run:  .venv/Scripts/python.exe -m unittest tests.test_cov_art_previews -v
"""

from __future__ import annotations

import base64
import contextlib
import html
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

import make_preview  # noqa: E402  (stdlib only)

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

try:
    import artlib
    HAVE_FONTS = artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_FONTS = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
fonts = unittest.skipUnless(HAVE_FONTS, "system label fonts not present")

PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
SDSTAR1 = PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDSTAR1.png"
WORK_MANIFEST = PROJECT_ROOT / "work" / "art" / "batch1" / "manifest.json"


# ============================================================ make_preview
def _texture(lump: str, file: str, w: int, h: int, kind: str = "wall", desc: str = "a wall") -> dict:
    return {"lump": lump, "kind": kind, "set": "test_set", "width": w, "height": h, "file": file,
            "script": "tools/art/gen_test.py", "seed": 1978, "seed_offset": 1,
            "colours_used": 33, "seam_score": 0.849,
            "description_en": desc, "description_ru": "стена " + desc}


def _manifest(textures: list[dict]) -> dict:
    return {"batch": 1, "set": "test_set", "script": "tools/art/gen_test.py", "batch_seed": 1977,
            "font_note_en": "fonts note", "font_note_ru": "заметка о шрифтах", "textures": textures}


class IndexStatusesTests(unittest.TestCase):
    """make_preview's card status comes from docs/art/TEXTURE-INDEX.md, "the
    single owner of that fact": any row whose first cell is a back-quoted
    lump, the status from the "Status" column of the nearest header above."""

    def parse(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "INDEX.md"
            p.write_text(text, encoding="utf-8")
            return make_preview.index_statuses(p)

    def test_status_column_is_found_by_name_per_table(self):
        md = "\n".join([
            "| Lump | Kind | Status | Date |",
            "|---|---|---|---|",
            "| `SDAAA1` | wall | approved | 2026-10-12 |",
            "",
            "Prose between the tables, | with a pipe | that is not a table row.",
            "",
            "| Lump | Status |",           # second table: the column moved
            "|---|---|",
            "| `SDBBB1` | discarded (reason) |",
        ])
        self.assertEqual(self.parse(md), {"SDAAA1": "approved", "SDBBB1": "discarded (reason)"})

    def test_rows_that_are_not_lump_rows_are_ignored(self):
        md = "\n".join([
            "| `SDEARLY` | before any header | approved |",   # no Status header yet
            "| Lump | Kind | Status |",
            "|---|---|---|",
            "| SDPLAIN | not back-quoted | approved |",
            "| `SDSHORT` |",                                  # too few cells
            "| `SDOK1` | wall | proposed v2 |",
        ])
        self.assertEqual(self.parse(md), {"SDOK1": "proposed v2"})

    def test_the_real_index_reads_the_approved_switches(self):
        """TEXTURE-INDEX.md: all eight switches are approved (CEO, 2026-10-13)."""
        statuses = make_preview.index_statuses()
        for lump in ("SDSW1A", "SDSW2A", "SDSW1B", "SDSW2B", "SDSW1C", "SDSW2C", "SDSW1D", "SDSW2D"):
            with self.subTest(lump=lump):
                self.assertEqual(statuses.get(lump), "approved")
        self.assertTrue(statuses["SDSTAR1"].startswith("approved"), statuses["SDSTAR1"])


class PreviewBuildTests(unittest.TestCase):
    """build(): one self-contained page per language (no external
    dependencies: inline CSS/JS, data: URIs), one card per manifest texture."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / "tex").mkdir()
        self.wall_bytes = b"\x89PNG wall bytes"
        self.flat_bytes = b"\x89PNG flat bytes"
        (self.tmp / "tex" / "SDTST1.png").write_bytes(self.wall_bytes)
        (self.tmp / "tex" / "SDTST2.png").write_bytes(self.flat_bytes)
        self.manifest = _manifest([
            _texture("SDTST1", "tex/SDTST1.png", 64, 128, desc="wall <script>alert(1)</script> & co"),
            _texture("SDTST2", "tex/SDTST2.png", 64, 64, kind="flat", desc="a floor"),
        ])
        self.palette = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        for patcher in (mock.patch.object(make_preview, "PROJECT_ROOT", self.tmp),
                        mock.patch.object(make_preview, "index_statuses",
                                          return_value={"SDTST1": "approved"})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def build(self, lang: str) -> str:
        return make_preview.build(lang, self.manifest, self.palette, "2099-01-02_0304")

    def test_one_card_per_texture_with_its_inlined_png(self):
        page = self.build("en")
        self.assertEqual(page.count('class="card"'), 2)
        for lump, data in (("SDTST1", self.wall_bytes), ("SDTST2", self.flat_bytes)):
            with self.subTest(lump=lump):
                self.assertIn(f'id="c-{lump}"', page)
                uri = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
                # 1x, 4x and the 2x2 tile all use the same embedded bytes
                self.assertEqual(page.count(uri), 3)

    def test_the_page_is_self_contained(self):
        for lang in ("en", "ru"):
            page = self.build(lang)
            with self.subTest(lang=lang):
                self.assertNotRegex(page, r"(src|href)\s*=\s*[\"']?(https?:|//)")
                self.assertNotIn("<link", page)
                self.assertNotIn("<script src", page)
                self.assertIn("<style>", page)

    def test_zoom_sizes_follow_the_declared_factors(self):
        page = self.build("en")
        z, tz = make_preview.ZOOM, make_preview.TILE_ZOOM
        self.assertIn(f'width="64" height="128" alt="SDTST1"', page)
        self.assertIn(f'width="{64 * z}" height="{128 * z}" alt="SDTST1 x{z}"', page)
        self.assertIn(f"width:{64 * 2 * tz}px;height:{128 * 2 * tz}px", page)
        self.assertIn(f"background-size:{64 * tz}px {128 * tz}px", page)

    def test_status_comes_from_the_index_with_proposed_as_fallback(self):
        page = self.build("en")
        card1 = page.split('id="c-SDTST1"')[1].split('id="c-SDTST2"')[0]
        card2 = page.split('id="c-SDTST2"')[1]
        self.assertIn("status: approved", card1)
        self.assertIn(f"status: {make_preview.STATUS_FALLBACK}", card2)
        self.assertEqual(make_preview.STATUS_FALLBACK, "proposed")

    def test_manifest_text_is_escaped(self):
        page = self.build("en")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("wall &lt;script&gt;alert(1)&lt;/script&gt; &amp; co", page)

    def test_card_metadata(self):
        page = self.build("en")
        card = page.split('id="c-SDTST1"')[1].split('id="c-SDTST2"')[0]
        self.assertIn("<dd>wall</dd>", card)
        self.assertIn("<dd>64×128</dd>", card)
        self.assertIn("seed 1978 (BATCH_SEED 1977 + 1)", card)
        self.assertIn(f"<dd>33 / {self.palette['count']}</dd>", card)
        self.assertIn(">0.85</dd>", card)                     # seam score, two decimals
        self.assertIn("CC BY-NC-SA 4.0 (D15)", card)
        flat = page.split('id="c-SDTST2"')[1]
        self.assertIn("<dd>flat</dd>", flat)

    def test_header_palette_and_stamp(self):
        page = self.build("en")
        self.assertIn("2099-01-02_0304", page)
        self.assertIn("2 textures", page)
        note = f"{self.palette['count']} colours in {len(self.palette['ramps'])} ramps (max 256)"
        self.assertIn(note, page)
        self.assertEqual(page.count('<div class="ramp">'), len(self.palette["ramps"]) + 1)  # + extras
        self.assertIn("fonts note", page)

    def test_russian_page_is_in_russian(self):
        page = self.build("ru")
        self.assertIn('<html lang="ru">', page)
        self.assertIn(make_preview.LABELS["ru"]["title"], page)
        self.assertIn("стена a floor", page)
        self.assertIn("Одобрить", page)
        self.assertIn("заметка о шрифтах", page)
        self.assertNotIn(">Approve<", page)

    def test_both_languages_label_the_same_keys(self):
        self.assertEqual(set(make_preview.LABELS["en"]), set(make_preview.LABELS["ru"]))

    def test_summary_labels_reach_the_script_as_json(self):
        for lang in ("en", "ru"):
            page = self.build(lang)
            m = re.search(r"const L=(\{.*?\});const state", page)
            self.assertIsNotNone(m, "the JS labels object is missing")
            labels = json.loads(m.group(1))
            want = {k: make_preview.LABELS[lang][k] for k in ("approved", "discarded", "undecided", "none")}
            self.assertEqual(labels, want)

    def test_main_writes_the_english_page_and_the_russian_mirror(self):
        mpath = self.tmp / "manifest.json"
        mpath.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
        en_dir, ru_dir = self.tmp / "out" / "en", self.tmp / "out" / "ru"
        out = io.StringIO()
        with mock.patch.object(make_preview, "MANIFEST", mpath), \
                mock.patch.object(make_preview, "PREVIEW_DIR_EN", en_dir), \
                mock.patch.object(make_preview, "PREVIEW_DIR_RU", ru_dir), \
                mock.patch.object(sys, "argv", ["make_preview.py", "--stamp", "2099-01-02_0304"]), \
                contextlib.redirect_stdout(out):
            make_preview.main()
        name = "2099-01-02_0304_F2_batch1-soviet-base.html"
        self.assertEqual([p.name for p in en_dir.iterdir()], [name])
        self.assertEqual([p.name for p in ru_dir.iterdir()], [name])
        self.assertIn('<html lang="en">', (en_dir / name).read_text(encoding="utf-8"))
        self.assertIn('<html lang="ru">', (ru_dir / name).read_text(encoding="utf-8"))
        self.assertEqual(out.getvalue().count("wrote "), 2)

    def test_main_default_stamp_is_now(self):
        mpath = self.tmp / "manifest.json"
        mpath.write_text(json.dumps(self.manifest), encoding="utf-8")
        en_dir, ru_dir = self.tmp / "en", self.tmp / "ru"
        with mock.patch.object(make_preview, "MANIFEST", mpath), \
                mock.patch.object(make_preview, "PREVIEW_DIR_EN", en_dir), \
                mock.patch.object(make_preview, "PREVIEW_DIR_RU", ru_dir), \
                mock.patch.object(sys, "argv", ["make_preview.py"]), \
                contextlib.redirect_stdout(io.StringIO()):
            make_preview.main()
        [page] = list(en_dir.iterdir())
        self.assertRegex(page.name, r"^\d{4}-\d{2}-\d{2}_\d{4}_F2_batch1-soviet-base\.html$")


@unittest.skipUnless(WORK_MANIFEST.is_file(), "work/art/batch1/manifest.json absent (gitignored work/)")
class PreviewOnTheRealBatchTests(unittest.TestCase):
    """The real batch-1 manifest builds (read-only; nothing is written)."""

    def test_every_batch1_texture_gets_its_index_status(self):
        manifest = json.loads(WORK_MANIFEST.read_text(encoding="utf-8"))
        palette = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        statuses = make_preview.index_statuses()
        page = make_preview.build("en", manifest, palette, "2099-01-02_0304")
        for t in manifest["textures"]:
            lump = t["lump"]
            with self.subTest(lump=lump):
                self.assertIn(f'id="c-{lump}"', page)
                card = page.split(f'id="c-{lump}"')[1].split('<div class="card"')[0]
                status = statuses.get(lump, make_preview.STATUS_FALLBACK)
                self.assertIn(html.escape(f"status: {status}"), card)


# ============================================================ make_contact
@imaging
@fonts
class ContactSheetTests(unittest.TestCase):
    """make_contact: every lump of the manifest side by side, in manifest
    order, at ZOOM x nearest, its name in a strip above it; plus a half-size
    copy."""

    def setUp(self):
        import make_contact
        self.mc = make_contact
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        rng = np.random.default_rng(7)
        self.tiles = []
        for lump, (w, h) in (("SDAAA1", (64, 128)), ("SDBBB1", (128, 128)), ("SDCCC1", (64, 64))):
            arr = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
            Image.fromarray(arr, "RGB").save(self.tmp / f"{lump}.png")
            self.tiles.append((lump, arr))
        manifest = {"textures": [{"lump": l, "file": f"{l}.png"} for l, _ in self.tiles]}
        (self.tmp / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        out = io.StringIO()
        with mock.patch.object(make_contact, "PROJECT_ROOT", self.tmp), \
                mock.patch.object(make_contact, "MANIFEST", self.tmp / "manifest.json"), \
                mock.patch.object(make_contact, "CONTACT_OUT", self.tmp / "contact.png"), \
                mock.patch.object(make_contact, "HALF_OUT", self.tmp / "contact_half.png"), \
                contextlib.redirect_stdout(out):
            make_contact.main()
        self.printed = out.getvalue()
        self.sheet = np.asarray(Image.open(self.tmp / "contact.png").convert("RGB"))

    def test_sheet_geometry(self):
        mc = self.mc
        width = mc.GAP + sum(a.shape[1] * mc.ZOOM + mc.GAP for _, a in self.tiles)
        height = mc.LABEL_H + max(a.shape[0] for _, a in self.tiles) * mc.ZOOM + mc.GAP
        self.assertEqual(self.sheet.shape[:2], (height, width))
        self.assertIn(f"({width}x{height})", self.printed)

    def test_each_lump_is_a_nearest_zoom_in_manifest_order(self):
        mc = self.mc
        x = mc.GAP
        for lump, arr in self.tiles:
            h, w = arr.shape[:2]
            with self.subTest(lump=lump):
                cell = self.sheet[mc.LABEL_H:mc.LABEL_H + h * mc.ZOOM, x:x + w * mc.ZOOM]
                expected = arr.repeat(mc.ZOOM, axis=0).repeat(mc.ZOOM, axis=1)
                self.assertTrue(np.array_equal(cell, expected))
                strip = self.sheet[:mc.LABEL_H, x:x + w * mc.ZOOM]
                self.assertTrue((strip != np.array(mc.BG)).any(axis=2).any(), "no name label above the lump")
            x += w * mc.ZOOM + mc.GAP

    def test_gaps_are_background(self):
        mc = self.mc
        self.assertTrue((self.sheet[:, :mc.GAP] == np.array(mc.BG)).all())
        self.assertTrue((self.sheet[-mc.GAP:, :] == np.array(mc.BG)).all())

    def test_half_size_copy(self):
        with Image.open(self.tmp / "contact_half.png") as half:
            size = half.size
        h, w = self.sheet.shape[:2]
        self.assertEqual(size, (w // 2, h // 2))


# ============================================================ emblem_check
@imaging
@fonts
class EmblemCheckTests(unittest.TestCase):
    """emblem_check: left panel the emblem alone, right panel the same with
    the reference circles and the CEO's points in cyan; and SDSTAR1 at 8x
    nearest. Coordinates are gen_soviet_base's unit square."""

    @classmethod
    def setUpClass(cls):
        import emblem_check
        cls.ec = emblem_check
        cls.tmp = Path(tempfile.mkdtemp())
        shutil.copyfile(SDSTAR1, cls.tmp / "SDSTAR1.png")        # read a copy, never assets/
        out = io.StringIO()
        with mock.patch.object(emblem_check, "CHECK_OUT", cls.tmp / "emblem_check.png"), \
                mock.patch.object(emblem_check, "ZOOM_OUT", cls.tmp / "SDSTAR1_emblem_8x.png"), \
                mock.patch.object(emblem_check.gen, "OUT_DIR", cls.tmp), \
                contextlib.redirect_stdout(out):
            emblem_check.main()
        cls.printed = out.getvalue()
        cls.sheet = np.asarray(Image.open(cls.tmp / "emblem_check.png").convert("RGB"))
        cls.left = cls.ec.emblem_panel(False)
        cls.right = cls.ec.emblem_panel(True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def cyan(self, a):
        return np.all(np.abs(a.astype(int) - np.array(self.ec.GUIDE)) < 40, axis=2).sum()

    def test_sheet_is_two_panels_and_a_gap(self):
        px, gap = self.ec.CHECK_PX, self.ec.GAP
        self.assertEqual(self.sheet.shape, (px, 2 * px + gap, 3))
        self.assertTrue((self.sheet[:, px:px + gap] == 40).all())
        self.assertTrue(np.array_equal(self.sheet[:, :px], self.left))
        self.assertTrue(np.array_equal(self.sheet[:, px + gap:], self.right))
        self.assertIn("emblem_check.png", self.printed)

    def test_left_is_the_bare_emblem_right_carries_the_guides(self):
        self.assertEqual(self.cyan(self.left), 0)
        self.assertGreater(self.cyan(self.right), 100)

    def test_the_emblem_fills_its_panel_on_flag_red(self):
        px = self.ec.CHECK_PX
        red = np.array(artlib.ramp_colour("flag_red", 0.70))
        for corner in (self.left[0, 0], self.left[0, -1]):
            self.assertTrue(np.array_equal(corner, red))
        gold = np.array(artlib.ramp_colour("hazard_yellow", 0.88))
        ys, xs = np.nonzero(np.all(np.abs(self.left.astype(int) - gold) < 10, axis=2))
        self.assertGreater(xs.max() - xs.min(), 0.6 * px)
        self.assertGreater(ys.max() - ys.min(), 0.6 * px)

    def test_the_panel_is_deterministic(self):
        self.assertTrue(np.array_equal(self.ec.emblem_panel(False), self.left))

    def test_zoom_is_sdstar1_at_8x_nearest(self):
        z = self.ec.ZOOM
        self.assertEqual(z, 8)
        src = np.asarray(Image.open(SDSTAR1).convert("RGB"))
        big = np.asarray(Image.open(self.tmp / "SDSTAR1_emblem_8x.png").convert("RGB"))
        self.assertEqual(big.shape, (src.shape[0] * z, src.shape[1] * z, 3))
        self.assertTrue(np.array_equal(big, src.repeat(z, axis=0).repeat(z, axis=1)))

    def test_reference_points_track_the_generator(self):
        """The guides are read from gen_soviet_base, so the sheet always shows
        the drawing that ships, not a stale copy of its numbers."""
        gen = self.ec.gen
        points = dict(self.ec.REFERENCE_POINTS)
        self.assertEqual(len(points), len(self.ec.REFERENCE_POINTS), "duplicate labels")
        self.assertEqual(points["tip"], gen.SICKLE_TIP)
        self.assertEqual((points["sh0"], points["sh1"]), tuple(gen.SICKLE_HANDLE))
        self.assertEqual(points["hc"], gen.HAMMER_HEAD_C)
        self.assertEqual((points["hh0"], points["hh1"]), tuple(gen.HAMMER_HANDLE))
        for label, (u, v) in self.ec.REFERENCE_POINTS:
            with self.subTest(point=label):
                self.assertTrue(0.0 <= u <= 1.0 and 0.0 <= v <= 1.0, (u, v))


if __name__ == "__main__":
    unittest.main()
