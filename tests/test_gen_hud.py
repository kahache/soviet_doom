"""Tests for the M2e sweep of the status bar and the face (tools/art/gen_hud.py).
The generator writes to work/ (or a directory it is given) only; nothing here
touches assets/.

  the contract   FD_LUMPS equals the Freedoom 0.13.0 patch headers (when the
                 IWAD is in this clone); every face, digit and bar we draw has
                 exactly the size of the lump it would replace, and the face
                 and STTMINUS carry Freedoom's grAb offsets
  the colours    every opaque pixel is a palette-v2 colour; faces and digits
                 have hard alpha (ART-BIBLE 2 exception)
  the face       the 42 lumps exist, are all different, pain grows
                 monotonically in blood, the turned frames are mirror-ish
                 opposites, nothing is cut by any Freedoom box
  the bar        STARMS is the arms section of STBAR; every label fits its
                 panel in both languages; EN and RU differ only in the label rows
  D27            no system font in the module; rendering is deterministic
  the build      build() writes only under the directory it is given

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_hud -v
"""

from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import gen_hud
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter without Pillow
    HAVE_IMAGING = False

imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not installed")
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"


def palette_v2() -> set:
    return {tuple(c) for c in json.loads(PALETTE_JSON.read_text(encoding="utf-8"))["colours_v2"]}


def wad_headers() -> dict:
    data = IWAD.read_bytes()
    n, off = struct.unpack_from("<4xii", data, 0)
    out = {}
    for i in range(n):
        pos, size, name = struct.unpack_from("<ii8s", data, off + 16 * i)
        name = name.rstrip(b"\0").decode("ascii", "replace")
        if name in gen_hud.FD_LUMPS:
            out[name] = struct.unpack_from("<hhhh", data, pos)
    return out


_FACES: dict = {}


def faces(option="A") -> dict:
    if option not in _FACES:
        _FACES[option] = gen_hud.face_lumps(option)
    return _FACES[option]


@imaging
class ContractTests(unittest.TestCase):
    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad not in this clone")
    def test_table_equals_the_freedoom_headers(self):
        hdr = wad_headers()
        self.assertEqual(set(hdr), set(gen_hud.FD_LUMPS))
        for name, spec in gen_hud.FD_LUMPS.items():
            self.assertEqual(tuple(hdr[name]), spec, name)

    def test_the_42_faces(self):
        self.assertEqual(len(gen_hud.FACE_LUMPS), 42)
        self.assertEqual(len(set(gen_hud.FACE_LUMPS)), 42)

    def test_face_sizes_match(self):
        for name, rgba in faces().items():
            w, h, _, _ = gen_hud.FD_LUMPS[name]
            self.assertEqual(rgba.shape, (h, w, 4), name)

    def test_digit_sizes_match(self):
        for opt in ("N2", "N3"):
            ds = gen_hud.digit_set(opt)
            self.assertEqual(len(ds), 32)
            for name, rgba in ds.items():
                w, h, _, _ = gen_hud.FD_LUMPS[name]
                self.assertEqual(rgba.shape, (h, w, 4), (opt, name))

    def test_bar_sizes_match(self):
        for opt in gen_hud.BAR_OPTIONS:
            for lang in ("en", "ru"):
                self.assertEqual(gen_hud.render_bar(opt, lang).shape, (32, 320, 3))
                self.assertEqual(gen_hud.render_arms(opt, lang).shape, (32, 38, 3))

    def test_grab_written_with_freedoom_offsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = gen_hud.save_rgba(faces()["STFTL40"], Path(tmp) / "x.png", gen_hud.grab_of("STFTL40"))
            data = p.read_bytes()
            i = data.index(b"grAb")
            self.assertEqual(struct.unpack(">ii", data[i + 4:i + 12]), (-1, -1))
            Image.open(p).load()                    # still a valid PNG (CRC right)
        self.assertIsNone(gen_hud.grab_of("STTNUM0"))
        self.assertEqual(gen_hud.grab_of("STTMINUS"), (4, 0))


@imaging
class ColourTests(unittest.TestCase):
    def assert_palette(self, rgb, what):
        cols = {tuple(int(v) for v in c) for c in rgb.reshape(-1, 3)}
        self.assertLessEqual(cols, palette_v2(), what)

    def test_faces_palette_and_hard_alpha(self):
        for name, rgba in faces().items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, name)
            self.assert_palette(rgba[rgba[..., 3] == 255][:, :3][None], name)

    def test_other_faces_palette(self):
        for opt in ("B", "C"):
            c = gen_hud.render_face(opt)
            self.assert_palette(c[c[..., 3] == 255][:, :3][None], opt)

    def test_digits_palette_and_alpha(self):
        for opt in ("N2", "N3"):
            for name, rgba in gen_hud.digit_set(opt).items():
                self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, name)
                self.assertTrue((rgba[..., 3] == 255).any(), name)
                self.assert_palette(rgba[rgba[..., 3] == 255][:, :3][None], name)

    def test_bars_palette(self):
        for opt in gen_hud.BAR_OPTIONS:
            self.assert_palette(gen_hud.render_bar(opt, "ru"), opt)
        self.assert_palette(gen_hud.render_bar("B", "bi"), "BI")


@imaging
class FaceTests(unittest.TestCase):
    def test_all_lumps_differ(self):
        seen = {}
        for name, rgba in faces().items():
            key = rgba.tobytes() + bytes(rgba.shape[:2])
            self.assertNotIn(key, seen, f"{name} == {seen.get(key)}")
            seen[key] = name

    def test_blood_grows_with_pain(self):
        counts = []
        for p in range(5):
            c = gen_hud.render_face("A", p, "st", 0).astype(int)
            face = c[8:28, 8:26]                    # below the hat's star
            reds = (face[..., 0] > 60) & (face[..., 0] > 2.2 * face[..., 1]) & (face[..., 3] == 255)
            counts.append(int(reds.sum()))
        self.assertEqual(counts, sorted(counts), counts)
        self.assertGreater(counts[4], counts[0] + 20)

    def test_turns_move_the_features_opposite_ways(self):
        st = gen_hud.render_face("A", 0, "st", 0)
        tl = gen_hud.render_face("A", 0, "tl", 0)
        tr = gen_hud.render_face("A", 0, "tr", 0)
        # same silhouette (the warp keeps every layer's outline)
        self.assertTrue(np.array_equal(st[..., 3], tl[..., 3]))
        self.assertTrue(np.array_equal(st[..., 3], tr[..., 3]))
        # the eye row's darkest pixels move left for TL, right for TR
        def dark_x(c):
            row = c[gen_hud.EYE_Y, :, :3].astype(int).sum(-1)
            xs = np.nonzero((row < 200) & (c[gen_hud.EYE_Y, :, 3] == 255))[0]
            return xs.mean()
        self.assertLess(dark_x(tl), dark_x(st))
        self.assertGreater(dark_x(tr), dark_x(st))

    def test_nothing_cut_by_any_box(self):
        """Every opaque canvas pixel of every frame lies inside that lump's box."""
        for name in gen_hud.FACE_LUMPS:
            c = gen_hud.render_face("A", *gen_hud.face_lump_spec(name))
            w, h, lo, to = gen_hud.FD_LUMPS[name]
            inside = np.zeros(c.shape[:2], bool)
            inside[-to:-to + h, -lo:-lo + w] = True
            self.assertFalse(((c[..., 3] == 255) & ~inside).any(), name)

    def test_spec_parsing(self):
        self.assertEqual(gen_hud.face_lump_spec("STFST42"), (4, "st", 1))
        self.assertEqual(gen_hud.face_lump_spec("STFTL30"), (3, "tl", 0))
        self.assertEqual(gen_hud.face_lump_spec("STFKILL2"), (2, "kill", 0))
        self.assertEqual(gen_hud.face_lump_spec("STFDEAD0"), (4, "dead", 0))
        with self.assertRaises(KeyError):
            gen_hud.face_lump_spec("STFXX0")

    def test_deterministic(self):
        a = gen_hud.render_face("C", 2, "tr", 0)
        b = gen_hud.render_face("C", 2, "tr", 0)
        self.assertTrue(np.array_equal(a, b))


@imaging
class BarTests(unittest.TestCase):
    def test_starms_is_the_bars_arms_section(self):
        for opt in gen_hud.BAR_OPTIONS:
            bar = gen_hud.render_bar(opt, "en")
            self.assertTrue(np.array_equal(gen_hud.render_arms(opt, "en"), bar[:, 104:142]))

    def test_labels_fit_their_panels(self):
        panels = {"ammo": (3, 47), "health": (49, 104), "arms": (105, 141), "armor": (179, 236)}
        for lang, words in gen_hud.LABELS.items():
            for key, word in words.items():
                w = gen_hud.text_mask(word).shape[1]
                x0 = int(round(gen_hud.LABEL_CX[key] - w / 2))
                lo, hi = panels[key]
                self.assertGreaterEqual(x0, lo, (lang, word))
                self.assertLessEqual(x0 + w + 1, hi, (lang, word))     # +1: the shadow

    def test_every_label_letter_has_a_glyph(self):
        for words in gen_hud.LABELS.values():
            for word in words.values():
                for ch in word:
                    self.assertIn(ch, gen_hud.FONT5, ch)
        for ch, data in gen_hud.FONT5.items():
            rows = data.split("|")
            self.assertEqual(len(rows), 5, ch)
            self.assertEqual(len({len(r) for r in rows}), 1, ch)

    def test_languages_differ_only_in_the_label_rows(self):
        for opt in gen_hud.BAR_OPTIONS:
            en, ru = gen_hud.render_bar(opt, "en"), gen_hud.render_bar(opt, "ru")
            diff = np.nonzero((en != ru).any(-1))[0]
            self.assertTrue(len(diff))
            self.assertGreaterEqual(diff.min(), gen_hud.LABEL_Y, opt)

    def test_wells_are_dark_for_the_red_digits(self):
        for opt in gen_hud.BAR_OPTIONS:
            bar = gen_hud.render_bar(opt, "en").astype(int)
            for x0, y0, x1, y1 in gen_hud.WELL.values():
                inner = bar[y0 + 2:y1 - 1, x0 + 2:x1 - 1]
                self.assertLess(inner.sum(-1).mean(), 120, opt)

    def test_mock_draws_the_real_start_numbers(self):
        ds = gen_hud.digit_set("N2")
        bar = gen_hud.render_bar("A", "en")
        scr = gen_hud.mock(bar, bar[:, 104:142], ds, None, "start")
        self.assertEqual(scr.shape, (200, 320, 3))
        # "50" right-aligned at x = 44: the cell of '5' starts at 44 - 26 = 18
        self.assertFalse(np.array_equal(scr[171:187, 18:31], bar[3:19, 18:31]))
        self.assertTrue(np.array_equal(scr[171:187, 5:18], bar[3:19, 5:18]))  # no third digit


@imaging
class HygieneTests(unittest.TestCase):
    def test_no_system_font(self):
        src = (ART_TOOLS / "gen_hud.py").read_text(encoding="utf-8")
        for bad in ("truetype", "ImageFont", "FONT_POSTER", "FONT_SMALL"):
            self.assertNotIn(bad, src)

    def test_no_writes_outside_the_given_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            man = gen_hud.build(Path(tmp))
            files = [p for p in Path(tmp).rglob("*") if p.is_file()]
            self.assertEqual(len(files), len(man["files"]) + 1)          # + manifest.json
            self.assertEqual(sum(1 for k in man["files"] if "/full/" in k), 42)
            for rel, name in man["files"].items():
                with Image.open(Path(tmp) / rel) as im:
                    size = im.size
                w, h, _, _ = gen_hud.FD_LUMPS[name]
                self.assertEqual(size, (w, h), rel)


if __name__ == "__main__":
    unittest.main()
