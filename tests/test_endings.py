"""The episode endings' illustrations (V3 B2, D132; MOD-SPEC 6.16).

Leaving an episode's last map (MAP03, MAP06, MAP09) shows the stats, the
awards page (ADR 013), the ending cluster's text, then the end sequence the
map's `next` names: `Intermission SD_EndingN`, one full-screen picture
`SDENDn` waiting for a key, then the title screen. This file holds what can
be held offline (the engine pass is the PM's, D26):

  * MAPINFO: the three sequences (Image with the picture, no Time, no Music;
    then GotoTitle), each episode's last map naming its own, the range still
    on `endtitle`, the ending clusters still printing their text first;
  * the pictures: installed, 320x200, indexed, inside palette v3;
  * the generator (tools/art/gen_endings.py): its lumps are MAPINFO's, its
    windows are 4:3, its pure steps behave (pad, signature fill, mapping);
  * the CEO's preview exists, in English (D129).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
sys.path.insert(0, str(TESTS))

from test_death_prompt import strip_lump_comments  # noqa: E402

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the project venv has both
    HAVE_IMAGING = False

MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
ENDINGS_DIR = PROJECT_ROOT / "assets" / "graphics" / "endings"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-25_V3_episode-endings.html"
SCREEN = (320, 200)
PALETTE_VERSION = 3

# episode's last map -> (its end sequence, the picture, its ending cluster)
EPISODE_ENDS = {"MAP03": ("SD_Ending1", "SDEND1", 1),
                "MAP06": ("SD_Ending2", "SDEND2", 7),
                "MAP09": ("SD_Ending3", "SDEND3", 10)}

RE_MAP = re.compile(r'(?ims)^map\s+(\w+)[^{]*\{(.*?)^\}')
RE_CLUSTER = re.compile(r'(?ims)^cluster\s+(\d+)\s*\{(.*?)^\}')
RE_INTERMISSION = re.compile(r'(?ims)^intermission\s+(\w+)\s*\{(.*?)^\}')
RE_ACTION = re.compile(r'(?is)(\w+)\s*\{([^{}]*)\}')


def mapinfo() -> str:
    return strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))


def intermissions(text: str) -> dict[str, list[tuple[str, str]]]:
    """name -> [(action, body)] in order."""
    return {name: [(a, b) for a, b in RE_ACTION.findall(body)] for name, body in RE_INTERMISSION.findall(text)}


def next_of(body: str) -> str | None:
    m = re.search(r'(?im)^\s*next\s*=\s*(.+?)\s*$', body)
    return m.group(1) if m else None


class MapinfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = mapinfo()
        cls.maps = {n.upper(): b for n, b in RE_MAP.findall(cls.text)}
        cls.clusters = {int(n): b for n, b in RE_CLUSTER.findall(cls.text)}
        cls.seqs = intermissions(cls.text)

    def test_each_episode_end_names_its_own_sequence(self):
        for name, (seq, _pic, _cluster) in EPISODE_ENDS.items():
            self.assertEqual(next_of(self.maps[name]), f'EndSequence, "{seq}"', name)

    def test_the_range_still_ends_on_the_engines_endtitle(self):
        self.assertEqual(next_of(self.maps["RANGE"]), "endtitle")

    def test_no_other_map_ends_the_game(self):
        enders = {n for n, b in self.maps.items()
                  if (next_of(b) or "").lower().startswith(("endtitle", "endsequence"))}
        self.assertEqual(enders, set(EPISODE_ENDS) | {"RANGE"})

    def test_each_sequence_is_the_picture_then_the_title(self):
        for _map, (seq, pic, _cluster) in EPISODE_ENDS.items():
            self.assertIn(seq, self.seqs, f"no Intermission {seq}")
            actions = self.seqs[seq]
            self.assertEqual([a.lower() for a, _b in actions], ["image", "gototitle"], seq)
            image = actions[0][1]
            self.assertRegex(image, rf'(?im)^\s*Background\s*=\s*"{pic}"\s*$', seq)
            # no Time: the picture waits for a key; no Music: silent, as the text before it
            self.assertNotRegex(image, r'(?im)^\s*(Time|Music|Draw)\s*=', seq)

    def test_only_these_sequences(self):
        self.assertEqual(set(self.seqs), {seq for seq, _p, _c in EPISODE_ENDS.values()})

    def test_the_text_still_comes_first(self):
        """The engine prints the ending cluster's exittext and then links to
        the map's end sequence: the clusters keep their texts."""
        for name, (_seq, _pic, cluster) in EPISODE_ENDS.items():
            self.assertRegex(self.maps[name], rf'(?im)^\s*cluster\s*=\s*{cluster}\s*$', name)
            self.assertRegex(self.clusters[cluster], r'(?im)^\s*exittext\s*=\s*lookup\s*,\s*"SD_END0\d_TEXT"', name)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class PictureTests(unittest.TestCase):
    def test_installed_320x200_indexed_in_palette_v3(self):
        import palette
        allowed = set(palette.colours(PALETTE_VERSION))
        for _map, (_seq, pic, _cluster) in EPISODE_ENDS.items():
            path = ENDINGS_DIR / f"{pic}.png"
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as im:
                self.assertEqual(im.size, SCREEN, pic)
                self.assertEqual(im.mode, "P", pic)
                pal = im.getpalette()
                used = {tuple(pal[i * 3:i * 3 + 3]) for i in set(im.get_flattened_data())}
            self.assertFalse(used - allowed, pic)
            self.assertGreater(len(used), 100, f"{pic}: a painting, not a flat picture")

    def test_nothing_else_in_the_folder(self):
        self.assertEqual({p.name for p in ENDINGS_DIR.iterdir()},
                         {f"{pic}.png" for _s, pic, _c in EPISODE_ENDS.values()})


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_endings
        cls.g = gen_endings

    def test_the_generators_lumps_are_mapinfos(self):
        self.assertEqual([e.lump for e in self.g.ENDINGS], [pic for _s, pic, _c in EPISODE_ENDS.values()])
        self.assertEqual([e.episode for e in self.g.ENDINGS], [1, 2, 3])
        self.assertEqual(self.g.INSTALL_DIR, ENDINGS_DIR)

    # the Gemini paintings' heights (gemini_ending_ep1 1312x816, ep2_v2 1376x768, ep3_v2 1586x672)
    PAINTING_HEIGHTS = {"SDEND1": 816, "SDEND2": 768, "SDEND3": 672}

    def test_every_window_is_4_3(self):
        """A 320x200 screen is shown at 4:3: the window's width is 4/3 of the
        painting's height plus the rows added (frame() checks it on the file)."""
        for e in self.g.ENDINGS:
            w = e.window[1] - e.window[0]
            self.assertGreaterEqual(e.window[0], 0, e.lump)
            self.assertEqual(w * 3, (self.PAINTING_HEIGHTS[e.lump] + e.pad_top + e.pad_bottom) * 4, e.lump)
            self.assertIn(e.pad_mode, self.g.PAD_MODES, e.lump)
            self.assertEqual(e.palette_version, PALETTE_VERSION, e.lump)

    def test_the_reich_armbands_get_the_symbol(self):
        """D105/D108: episode 1's fallen soldier and the Consortium's Reich half."""
        self.assertEqual([e.lump for e in self.g.ENDINGS if e.armband is not None], ["SDEND1", "SDEND3"])

    def test_frame_refuses_a_window_that_is_not_4_3(self):
        bad = self.g.Ending("SDENDX", 9, "x", (0, 100), 0, 0, "nothing")
        with self.assertRaises(ValueError):
            self.g.frame(np.zeros((100, 200, 3), np.uint8), bad)

    def test_frame_makes_a_screen(self):
        e = self.g.Ending("SDENDX", 9, "x", (10, 410), 20, 10, "nothing", pad_mode="extend")
        rgb = np.random.default_rng(1).integers(0, 255, (270, 420, 3)).astype(np.uint8)
        out = self.g.frame(rgb, e)
        self.assertEqual(out.shape, (SCREEN[1], SCREEN[0], 3))

    def test_pads_add_rows_in_both_modes(self):
        rgb = np.full((60, 80, 3), 90, np.uint8)
        for mode in self.g.PAD_MODES:
            out = self.g.pad_rows(rgb, 12, 7, mode)
            self.assertEqual(out.shape, (79, 80, 3), mode)
            self.assertTrue(np.allclose(out[12 + 30], 90), mode)       # the painting itself is untouched
        with self.assertRaises(ValueError):
            self.g.pad_rows(rgb, 1, 0, "stretch")

    def test_extend_pad_leaves_the_banner_out(self):
        rgb = np.full((40, 60, 3), (30, 40, 80), np.uint8)
        rgb[:20, 20:40] = (200, 20, 20)                  # a red banner at the top edge
        out = self.g.pad_rows(rgb, 30, 0, "extend")
        top = out[:30]
        self.assertFalse(((top[..., 0] - np.maximum(top[..., 1], top[..., 2])) > 60).any())

    def test_signature_fill_removes_the_red(self):
        rgb = np.full((40, 40, 3), (70, 70, 75), np.uint8)
        rgb[15:25, 12:28] = (170, 30, 30)
        out, n = self.g.clean_signature(rgb, (0, 0, 40, 40))
        self.assertGreater(n, 0)
        a = out.astype(int)
        self.assertFalse(((a[..., 0] - np.maximum(a[..., 1], a[..., 2])) > 20).any())

    def test_source_to_screen_maps_the_window(self):
        e = self.g.ENDINGS[2]
        x, y = self.g.source_to_screen(e, e.window[0], -e.pad_top)
        self.assertEqual((round(x, 6), round(y, 6)), (0, 0))
        h = (e.window[1] - e.window[0]) * 3 / 4
        x, y = self.g.source_to_screen(e, e.window[1], h - e.pad_top)
        self.assertEqual((round(x, 6), round(y, 6)), SCREEN)
        sx, sy = self.g.screen_to_source(e, np.array([0.5]), np.array([0.5]))
        bx, by = self.g.source_to_screen(e, sx[0] + 0.5, sy[0] + 0.5)
        self.assertAlmostEqual(bx, 0.5, places=6)
        self.assertAlmostEqual(by, 0.5, places=6)


class PreviewTests(unittest.TestCase):
    def test_the_ceos_preview_exists_in_english(self):
        self.assertTrue(PREVIEW.is_file(), PREVIEW)
        html = PREVIEW.read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)
        for _seq, pic, _c in EPISODE_ENDS.values():
            self.assertIn(pic, html)
        for step in ("Stats", "Awards", "Ending text", "Illustration", "Title screen"):
            self.assertIn(step, html)


if __name__ == "__main__":
    unittest.main()
