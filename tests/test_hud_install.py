"""M2e-i (2026-10-20): status bar A, the sergeant's Gemini face and digits N2 ship.

The CEO chose status bar A (D89) and the numbers N2 (D92) from the M2e sweep
(`docs/art/previews/2026-10-20_1127_M4_hud-face-sweep.html`, drawn by
`tools/art/gen_hud.py`), and approved the face built from his Gemini sheets
(D90, `tools/art/gemini_face.py`, `docs/art/previews/2026-10-20_1148_M4_face-gemini.png`).
The 78 lumps ship in `assets/graphics/statusbar/`. Contract: MOD-SPEC 1 (the
IWAD-name exception), 6.5 and 6.5.1. What is checked, and why:

  files      exactly the 80 lumps: Freedoom's 76 status bar names that the
             sweep redraws (STBAR, STARMS, the 42 STF faces, STTNUM0-9,
             STTMINUS, STTPRCNT, STYSNUM0-9, STGNUM0-9), the two Russian
             pictures SDSBRU / SDARRU and, since P6 (D97), the two Catalan
             ones SDSBCA / SDARCA; each the size and grAb offsets of
             Freedoom 0.13.0's lump (written out below; IwadTests re-reads
             the IWAD where it is present); the bars indexed, the rest RGBA
             with hard alpha; bars and digits inside palette v1, the faces in
             palette v2 and listed in test_palette_v2's APPROVED_IN_V2; where
             work/ exists each is the approved render byte for byte
  labels     the Russian and Catalan bars differ from the English one only
             inside the label band SD_StatusBar redraws (its constants, read from
             status_bar.zs), and that band misses every number, key, face
             and table DoomStatusBar draws (positions from doom_sbar.zs,
             re-read from the installed gzdoom.pk3 where present)
  language   SD_SBAR_IMAGE / SD_SBAR_ARMS_IMAGE name the engine pictures in
             English, the packed Russian ones in [ru] and the Catalan in [ca]
  package    the PK3 carries them flat as graphics/<NAME>.png and check_pk3
             passes; the release reads the face as shipped (AiShips.face)
  licences   one row per lump: the face rows say Google Gemini and that the
             sources are not distributed; bar and digit rows name gen_hud.py

What it cannot pin is what the engine draws: the PM's checks (MOD-SPEC 6.5.1).

Stdlib only, but for the pixel checks (Pillow, numpy).
"""

from __future__ import annotations

import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
STATUSBAR = PROJECT_ROOT / "assets" / "graphics" / "statusbar"
WORK_HUD = PROJECT_ROOT / "work" / "art" / "hud"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
STATUS_BAR_ZS = SRC_DIR / "zscript" / "sd" / "status_bar.zs"
LANGUAGE = SRC_DIR / "lumps" / "LANGUAGE"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
import release  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from sdbuild.pk3 import collect_assets  # noqa: E402
from test_language import parse_language  # noqa: E402
from test_panzermensch_sprites import PNG_SIGNATURE, read_grab  # noqa: E402
from test_pause_sign import gzdoom_pk3, status_bar_code  # noqa: E402

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_IMAGING = False

# Freedoom 0.13.0 (iwads/freedoom2.wad): name -> (width, height, left, top),
# read from the patch headers on 2026-10-20. Written out, not imported from
# gen_hud.FD_LUMPS: the test is the second witness.
FACE_29 = (24, 29, -5, -2)
FACE_30 = (24, 30, -5, -2)
FACE_31 = (24, 31, -5, -1)
FREEDOOM: dict[str, tuple[int, int, int, int]] = {
    "STBAR": (320, 32, 0, 0), "STARMS": (38, 32, 0, 0),
    "STTMINUS": (13, 16, 4, 0), "STTPRCNT": (13, 16, 0, 0),
    **{f"STTNUM{d}": (13, 16, 0, 0) for d in range(10)},
    **{f"STYSNUM{d}": (4, 6, 0, 0) for d in range(10)},
    **{f"STGNUM{d}": (4, 6, 0, 0) for d in range(10)},
    **{f"STFST0{g}": FACE_29 for g in range(3)}, **{f"STFST1{g}": FACE_29 for g in range(3)},
    **{f"STFST2{g}": (24, 30, -5, -2) for g in range(3)},
    **{f"STFST3{g}": FACE_31 for g in range(3)}, **{f"STFST4{g}": FACE_31 for g in range(3)},
    "STFTL00": (26, 30, -5, -1), "STFTL10": (26, 30, -5, -2), "STFTL20": (27, 30, -4, -1),
    "STFTL30": (29, 31, -2, -1), "STFTL40": (30, 31, -1, -1),
    "STFTR00": (26, 30, -3, -2), "STFTR10": (26, 30, -3, -2), "STFTR20": (27, 30, -4, -1),
    "STFTR30": (28, 30, -3, -2), "STFTR40": (28, 30, -3, -2),
    **{f"STFOUCH{p}": FACE_31 for p in range(5)},
    **{f"STFEVL{p}": FACE_30 for p in range(5)},
    **{f"STFKILL{p}": FACE_30 for p in range(5)},
    "STFGOD0": FACE_29, "STFDEAD0": FACE_31,
}
# The Russian pictures of bar A, our own names (ADR 010: localized textures
# are not drawn in g4.14.2; SD_StatusBar draws these by a LANGUAGE id).
RUSSIAN = {"SDSBRU": "STBAR", "SDARRU": "STARMS"}
# P6 (D97): the Catalan pictures, drawn the same way for [ca]
# (tools/art/gen_hud.py --catalan; only these two, never the approved EN/RU).
CATALAN = {"SDSBCA": "STBAR", "SDARCA": "STARMS"}
# Every language variant of the bar: our name -> the engine picture it shadows.
LOCALIZED = {**RUSSIAN, **CATALAN}
FACES = sorted(n for n in FREEDOOM if n.startswith("STF"))
BARS = ("STBAR", "STARMS", *LOCALIZED)
DIGITS = sorted(n for n in FREEDOOM if n.startswith(("STT", "STYS", "STG")))
LUMP_COUNT = 80
# Freedoom's status bar lumps the sweep did not redraw; they stay the IWAD's:
# the multiplayer face backgrounds, the skull-key icons and their pairs
# (no skull key exists in the mod), and the HUD message font STCFN*.
LEFT_FREEDOOM = (*(f"STFB{i}" for i in range(4)), *(f"STPB{i}" for i in range(4)),
                 *(f"STKEYS{i}" for i in range(3, 9)))

# Where work/art/hud/ keeps the approved renders (D89 bar A, D90 the Gemini
# face, D92 digits N2); the Russian pictures are renamed on the way in.
def work_source(name: str) -> Path:
    if name in RUSSIAN:
        return WORK_HUD / "bar" / "A" / "ru" / f"{RUSSIAN[name]}.png"
    if name in CATALAN:
        return WORK_HUD / "bar" / "A" / "ca" / f"{CATALAN[name]}.png"
    if name in ("STBAR", "STARMS"):
        return WORK_HUD / "bar" / "A" / "en" / f"{name}.png"
    if name.startswith("STF"):
        return WORK_HUD / "face_gemini" / f"{name}.png"
    return WORK_HUD / "digits" / "N2" / f"{name}.png"


# gzdoom.pk3 g4.14.2, zscript/ui/statusbar/doom_sbar.zs: what DoomStatusBar
# draws over STBAR, as (x0, y0, x1, y1) inclusive on the 320x200 bar screen.
# Big numbers: three 14-px cells right-aligned at x (HUDFONT_DOOM = STTNUM*,
# 16 rows); the percent signs at 90 and 221; the arms digits 4x6 at their
# six places; the keys 7x5 (ours, STKEYS0-2) at 239; the ammo table's
# INDEXFONT_DOOM (STYSNUM*, 4x6) right-aligned at 288 and 314; the face
# canvas 35x32 at 143,168 (STFST* offsets keep it inside); the frags.
BIG_CELL, BIG_H, SMALL_W, SMALL_H = 14, 16, 4, 6
DYNAMIC = {
    "ammo": (44 - 3 * BIG_CELL, 171, 43, 171 + BIG_H - 1),
    "health": (90 - 3 * BIG_CELL, 171, 89, 171 + BIG_H - 1),
    "armor": (221 - 3 * BIG_CELL, 171, 220, 171 + BIG_H - 1),
    "health %": (90, 171, 102, 186), "armor %": (221, 171, 233, 186),
    "frags": (138 - 3 * BIG_CELL, 171, 137, 171 + BIG_H - 1),
    **{f"arms {s}": (x, y, x + SMALL_W - 1, y + SMALL_H - 1)
       for s, (x, y) in {2: (111, 172), 3: (123, 172), 4: (135, 172),
                         5: (111, 182), 6: (123, 182), 7: (135, 182)}.items()},
    **{f"key {i}": (239, y, 245, y + 4) for i, y in enumerate((171, 181, 191))},
    "table": (288 - 3 * SMALL_W, 173, 313, 191 + SMALL_H - 1),
    "face": (143, 168, 177, 199),
}


def png_header(data: bytes) -> tuple[int, int, int]:
    """(width, height, colour type) from IHDR."""
    assert data[:8] == PNG_SIGNATURE and data[12:16] == b"IHDR"
    w, h = struct.unpack(">II", data[16:24])
    return w, h, data[25]


def lumps() -> list[Path]:
    return sorted(STATUSBAR.glob("*.png")) if STATUSBAR.is_dir() else []


def zs_consts() -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    for name, value in re.findall(r"const\s+(SD_\w+)\s*=\s*([^;]+);",
                                  STATUS_BAR_ZS.read_text(encoding="utf-8")):
        value = value.strip()
        out[name] = value.strip('"') if value.startswith('"') else int(value)
    return out


def label_bands() -> dict[str, tuple[int, int, int, int]]:
    """The rectangles SD_StatusBar redraws, (x0, y0, x1, y1) inclusive on the
    320x200 screen, from status_bar.zs's own constants."""
    c = zs_consts()
    y0, y1 = c["SD_LABEL_TOP"], c["SD_LABEL_TOP"] + c["SD_LABEL_HEIGHT"] - 1
    return {"bar left": (c["SD_SBAR_X"], y0, c["SD_LABEL_LEFT_END"] - 1, y1),
            "bar right": (c["SD_LABEL_RIGHT_X"], y0, c["SD_LABEL_RIGHT_END"] - 1, y1),
            "arms": (c["SD_SBAR_ARMS_X"], y0, c["SD_SBAR_ARMS_END"] - 1, y1)}


def overlaps(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def iwad_headers() -> dict[str, tuple[int, int, int, int]]:
    data = IWAD.read_bytes()
    count, offset = struct.unpack("<ii", data[4:12])
    out = {}
    for i in range(count):
        pos, size, raw = struct.unpack("<ii8s", data[offset + 16 * i: offset + 16 * i + 16])
        name = raw.rstrip(b"\0").decode("latin-1")
        if name.startswith("ST") and size >= 8:
            out[name] = struct.unpack("<hhhh", data[pos:pos + 8])
    return out


class FileTests(unittest.TestCase):
    def test_exactly_the_80_lumps(self):
        self.assertEqual({p.stem for p in lumps()}, set(FREEDOOM) | set(LOCALIZED))
        self.assertEqual(len(FREEDOOM) + len(LOCALIZED), LUMP_COUNT)

    def test_every_face_is_present(self):
        names = {p.stem for p in lumps()}
        self.assertEqual(len(FACES), 42)
        for level in range(5):
            for lump in (*(f"STFST{level}{g}" for g in range(3)), f"STFTL{level}0", f"STFTR{level}0",
                         f"STFOUCH{level}", f"STFEVL{level}", f"STFKILL{level}"):
                self.assertIn(lump, names)
        self.assertIn("STFGOD0", names)
        self.assertIn("STFDEAD0", names)

    def test_sizes_and_offsets_are_freedooms(self):
        for p in lumps():
            data = p.read_bytes()
            base = LOCALIZED.get(p.stem, p.stem)
            w, h, left, top = FREEDOOM[base]
            self.assertEqual(png_header(data)[:2], (w, h), p.name)
            self.assertEqual(read_grab(data), None if (left, top) == (0, 0) else (left, top), p.name)

    def test_bars_indexed_the_rest_rgba(self):
        for p in lumps():
            colour_type = png_header(p.read_bytes())[2]
            self.assertEqual(colour_type, 3 if p.stem in BARS else 6, p.name)

    def test_none_left_to_freedoom_ships(self):
        self.assertFalse({p.stem for p in lumps()} & set(LEFT_FREEDOOM))

    @unittest.skipUnless(WORK_HUD.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_renders(self):
        for p in lumps():
            source = work_source(p.stem)
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p.name)


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class PixelTests(unittest.TestCase):
    @staticmethod
    def rgba(name: str):
        with Image.open(STATUSBAR / f"{name}.png") as img:
            return np.asarray(img.convert("RGBA"))

    def test_hard_alpha(self):
        for p in lumps():
            alpha = set(np.unique(self.rgba(p.stem)[..., 3]).tolist())
            self.assertLessEqual(alpha, {0, 255}, p.name)
            if p.stem in BARS:
                self.assertEqual(alpha, {255}, p.name)

    def test_palette_versions(self):
        """Bars and digits inside v1; the faces need v2 (flesh_pink skin)."""
        v1, v2 = set(palette_mod.colours(1)), set(palette_mod.colours(2))
        from test_palette_v2 import APPROVED_IN_V2
        listed = {Path(rel).stem for rel in APPROVED_IN_V2 if rel.startswith("graphics/statusbar/")}
        self.assertEqual(listed, set(FACES))
        for p in lumps():
            a = self.rgba(p.stem)
            used = {tuple(int(v) for v in c) for c in a[a[..., 3] > 0][:, :3]}
            if p.stem in FACES:
                self.assertLessEqual(used, v2, p.name)
            else:
                self.assertLessEqual(used, v1, p.name)
        self.assertTrue(any({tuple(int(v) for v in c) for c in self.rgba(f)[self.rgba(f)[..., 3] > 0][:, :3]} - v1
                            for f in FACES), "no face uses v2: then none needs listing")

    def test_localized_bars_differ_only_in_the_label_band(self):
        """[ru] and [ca] (P6): SD_StatusBar redraws only the band, so a label
        pixel outside it (an accent too high, a word too wide) never shows."""
        bands = label_bands()
        xs = {"STBAR": zs_consts()["SD_SBAR_X"], "STARMS": zs_consts()["SD_SBAR_ARMS_X"]}
        for local, en in LOCALIZED.items():
            x = xs[en]
            diff = (self.rgba(local) != self.rgba(en)).any(axis=2)
            self.assertTrue(diff.any(), f"{local} is {en}")
            redrawn = np.zeros_like(diff)
            for key, (x0, y0, x1, y1) in bands.items():
                if (en == "STARMS") != (key == "arms"):
                    continue
                redrawn[max(y0 - 168, 0):y1 - 168 + 1, max(x0 - x, 0):max(x1 - x + 1, 0)] = True
            self.assertFalse((diff & ~redrawn).any(), f"{local}: a label pixel outside the band")

    def test_the_catalan_bar_is_not_the_russian(self):
        self.assertFalse(np.array_equal(self.rgba("SDSBCA"), self.rgba("SDSBRU")))
        self.assertFalse(np.array_equal(self.rgba("SDARCA"), self.rgba("SDARRU")))


class LabelBandTests(unittest.TestCase):
    def test_the_band_misses_everything_doom_draws_on_the_bar(self):
        for band, rect in label_bands().items():
            for what, other in DYNAMIC.items():
                self.assertFalse(overlaps(rect, other), f"{band} {rect} covers {what} {other}")

    def test_the_constants_are_draw_main_bars_positions(self):
        c = zs_consts()
        self.assertEqual((c["SD_SBAR_X"], c["SD_SBAR_Y"], c["SD_SBAR_ARMS_X"]), (0, 168, 104))
        self.assertEqual(c["SD_SBAR_ARMS_END"] - c["SD_SBAR_ARMS_X"], FREEDOOM["STARMS"][0])
        self.assertEqual(c["SD_LABEL_TOP"] + c["SD_LABEL_HEIGHT"], 200, "the band runs to the bar's bottom")
        self.assertEqual((c["SD_SBAR_ENGINE_IMAGE"], c["SD_SBAR_ENGINE_ARMS"]), ("STBAR", "STARMS"))
        self.assertEqual((c["SD_SBAR_IMAGE_ID"], c["SD_SBAR_ARMS_IMAGE_ID"]),
                         ("$SD_SBAR_IMAGE", "$SD_SBAR_ARMS_IMAGE"))

    def test_the_draw_override_redraws_only_through_the_band(self):
        code = status_bar_code()
        self.assertEqual(len(re.findall(r"\bDrawImage\(", code)), 1)
        self.assertRegex(code, r"SetClipRect\(\s*left\s*,\s*SD_LABEL_TOP\s*,\s*right\s*-\s*left\s*,\s*SD_LABEL_HEIGHT\s*\)\s*;"
                               r"\s*DrawImage\(\s*image\s*,\s*\(\s*imageX\s*,\s*SD_SBAR_Y\s*\)\s*,\s*DI_ITEM_OFFSETS\s*\)\s*;"
                               r"\s*Screen\.SetClipRect\(\s*cx\s*,\s*cy\s*,\s*cw\s*,\s*ch\s*\)\s*;")
        self.assertRegex(code, r"if\s*\(\s*state\s*!=\s*HUD_StatusBar\s*\|\|\s*isInventoryBarVisible\(\)\s*\)")
        self.assertRegex(code, r"if\s*\(\s*bar\s*!=\s*SD_SBAR_ENGINE_IMAGE\s*\)")
        self.assertRegex(code, r"if\s*\(\s*arms\s*!=\s*SD_SBAR_ENGINE_ARMS\s*&&")


class EngineTests(unittest.TestCase):
    """DYNAMIC and the constants are doom_sbar.zs's (skipped without GZDoom)."""

    @classmethod
    def setUpClass(cls):
        pk3 = gzdoom_pk3()
        if pk3 is None:
            raise unittest.SkipTest("no gzdoom.pk3 on this machine (CI)")
        with zipfile.ZipFile(pk3) as zf:
            cls.sbar = zf.read("zscript/ui/statusbar/doom_sbar.zs").decode("latin-1")
            cls.fontdefs = zf.read("fontdefs.txt").decode("latin-1")

    def test_draw_main_bar_is_not_virtual(self):
        """Why Draw is overridden instead: DrawMainBar cannot be."""
        self.assertRegex(self.sbar, r"protected\s+void\s+DrawMainBar\s*\(")
        self.assertNotRegex(self.sbar, r"virtual\s+void\s+DrawMainBar")

    def test_the_pictures_and_numbers_are_where_dynamic_says(self):
        for needle in ('DrawImage("STBAR", (0, 168), DI_ITEM_OFFSETS)',
                       'DrawImage("STARMS", (104, 168), DI_ITEM_OFFSETS)',
                       'DrawImage("STTPRCNT", (90, 171), DI_ITEM_OFFSETS)',
                       'DrawImage("STTPRCNT", (221, 171), DI_ITEM_OFFSETS)',
                       "(44, 171)", "(90, 171)", "(221, 171)", "(138, 171)",
                       "(239, 171)", "(239, 181)", "(239, 191)",
                       "(288, 191)", "(314, 191)", "(143, 168)",
                       "(111, 172)", "(123, 172)", "(135, 172)",
                       "(111, 182)", "(123, 182)", "(135, 182)"):
            self.assertIn(needle, self.sbar)

    def test_the_fonts_are_our_digits(self):
        """The bar's numbers are drawn with fonts built from these lumps, so
        N2 reaches the fullscreen HUD and the ammo table too."""
        hud = re.search(r"HUDFONT_DOOM\s*\{(.*?)\}", self.fontdefs, re.S).group(1)
        index = re.search(r"INDEXFONT_DOOM\s*\{(.*?)\}", self.fontdefs, re.S).group(1)
        self.assertEqual(set(re.findall(r"\b(ST\w+)", hud)),
                         {f"STTNUM{d}" for d in range(10)} | {"STTMINUS", "STTPRCNT"})
        self.assertEqual(set(re.findall(r"\b(ST\w+)", index)), {f"STYSNUM{d}" for d in range(10)})


@unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not in git")
class IwadTests(unittest.TestCase):
    def test_the_table_is_freedooms(self):
        headers = iwad_headers()
        for name, want in FREEDOOM.items():
            self.assertEqual(headers.get(name), want, name)

    def test_every_freedoom_face_is_replaced_but_the_backgrounds(self):
        faces = {n for n in iwad_headers() if n.startswith("STF") and not n.startswith("STFB")}
        self.assertEqual(faces, set(FACES))

    def test_what_stays_freedooms_is_in_the_iwad(self):
        headers = iwad_headers()
        for name in LEFT_FREEDOOM:
            self.assertIn(name, headers)


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def value(self, lang: str, ident: str) -> str:
        return self.sections[lang][ident].strip('"')

    def test_english_names_the_engine_pictures(self):
        self.assertEqual(self.value("default", "SD_SBAR_IMAGE"), "STBAR")
        self.assertEqual(self.value("default", "SD_SBAR_ARMS_IMAGE"), "STARMS")

    def test_russian_names_the_packed_russian_pictures(self):
        packed = {e.path for e in collect_assets(PROJECT_ROOT / "assets")}
        for ident, name in (("SD_SBAR_IMAGE", "SDSBRU"), ("SD_SBAR_ARMS_IMAGE", "SDARRU")):
            self.assertEqual(self.value("ru", ident), name)
            self.assertIn(f"graphics/{name}.png", packed)

    def test_catalan_names_the_packed_catalan_pictures(self):
        packed = {e.path for e in collect_assets(PROJECT_ROOT / "assets")}
        for ident, name in (("SD_SBAR_IMAGE", "SDSBCA"), ("SD_SBAR_ARMS_IMAGE", "SDARCA")):
            self.assertEqual(self.value("ca", ident), name)
            self.assertIn(f"graphics/{name}.png", packed)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")
        with zipfile.ZipFile(cls.pk3) as zf:
            cls.names = zf.namelist()
            cls.data = {n: zf.read(n) for n in cls.names if n.startswith("graphics/")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_flat_under_graphics(self):
        for p in lumps():
            self.assertEqual(self.data.get(f"graphics/{p.name}"), p.read_bytes(), p.name)

    def test_check_pk3_passes(self):
        report = check_pk3.check_pk3(self.pk3)
        self.assertEqual([], [f"{f.category}: {f.path}: {f.message}" for f in report.errors])

    def test_the_release_reads_the_face_as_shipped(self):
        self.assertTrue(all(release.FACE_LUMP_RE.match(f) for f in FACES))
        rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
        check = release.check_licences(self.names, rows, [], {})
        self.assertTrue(release.ai_ships(check).face)


class LicenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))

    def row(self, name: str):
        found = [r for r in self.rows if r.covers(f"graphics/{name}.png")]
        self.assertEqual(len(found), 1, f"{name}: {len(found)} rows in docs/art/LICENSES.md")
        return found[0]

    def test_every_lump_has_one_own_work_row(self):
        for p in lumps():
            row = self.row(p.stem)
            self.assertTrue(row.own_work, p.stem)
            self.assertEqual(row.required, licences.OWN_WORK_CREDITS, p.stem)

    def test_the_face_rows_say_gemini_and_that_the_sources_stay_home(self):
        for name in FACES:
            origin = self.row(name).origin
            self.assertIn("generated by the project lead with Google Gemini", origin, name)
            self.assertIn("tools/art/gemini_face.py", origin, name)
            self.assertIn("the source images are not distributed", origin, name)

    def test_the_bar_and_digit_rows_name_the_generator_and_option(self):
        for name in BARS:
            self.assertIn("tools/art/gen_hud.py", self.row(name).origin, name)
            self.assertIn("bar A", self.row(name).origin, name)
        for name in DIGITS:
            self.assertIn("tools/art/gen_hud.py", self.row(name).origin, name)
            self.assertIn("N2", self.row(name).origin, name)


class DocumentTests(unittest.TestCase):
    def test_mod_spec_lists_the_iwad_name_exception(self):
        identity = re.search(r"\| Prefix \|.*", MOD_SPEC.read_text(encoding="utf-8")).group(0)
        for needle in ("`STBAR`", "`STARMS`", "`STF*`", "`STTNUM0-9`", "`STYSNUM0-9`", "`STGNUM0-9`"):
            self.assertIn(needle, identity)


if __name__ == "__main__":
    unittest.main()
