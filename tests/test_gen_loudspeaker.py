"""Contract of tools/art/gen_loudspeaker.py (V3 B5: the propaganda radio's
loudspeaker, sprite SDLS for SD_Loudspeaker, 21201).

Fast (reads constants only):

  names      the lumps are SDLSA0 and SDLSB0 (one picture for every angle),
             two options A/B, the recommended one among them
  prefix     SDLS (and SDLO, option B's installed name, D132) collide with
             no other sprite in assets/
  grab       the grAb sinks the foot 3 px, as the floor lamp COLU

Slow (renders; skipped under SD_SKIP_SLOW_ART=1, as verify.py fast sets):

  palette    every opaque pixel is a palette.json v1 colour, alpha 0/255
  canvas     nothing touches the canvas edge (rig_core.check_edges)
  size       floor to the top of the horns is TOP_HEIGHT; the pole stands
             on the grAb column
  star       the junction box carries red pixels (the star)
  frames     B differs from A (the lamp lit, the horns shaken), but only a
             little; A and B options differ
  seed       the same lump renders identically twice
  files      build() writes <opt>/SDLS<F>0.png with the grAb chunk

Run:  python -m unittest tests.test_gen_loudspeaker -v
"""

from __future__ import annotations

import os
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
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SKIP_SLOW = os.environ.get("SD_SKIP_SLOW_ART") == "1"


def read_grab(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    i = 8
    while i < len(data):
        n, = struct.unpack(">I", data[i:i + 4])
        if data[i + 4:i + 8] == b"grAb":
            return struct.unpack(">ii", data[i + 8:i + 16])
        i += 12 + n
    return None


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not installed")
class FastTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_loudspeaker as gl
        cls.gl = gl

    def test_lump_names(self):
        self.assertEqual([self.gl.lump_name(f) for f in self.gl.FRAMES], ["SDLSA0", "SDLSB0"])
        self.assertEqual(self.gl.ROTATION, 0)
        self.assertEqual(self.gl.OPTIONS, ("A", "B"))
        self.assertIn(self.gl.RECOMMENDED, self.gl.OPTIONS)

    def test_prefix_is_free_in_assets(self):
        others = {p.stem[:4] for p in (PROJECT_ROOT / "assets" / "sprites").rglob("*.png")
                  if p.parent.name != "loudspeaker"}
        self.assertNotIn(self.gl.SPRITE, others)
        self.assertEqual(set(self.gl.INSTALLED), set(self.gl.OPTIONS))
        self.assertEqual(self.gl.INSTALLED[self.gl.RECOMMENDED], self.gl.SPRITE)
        self.assertEqual(len(set(self.gl.INSTALLED.values())), len(self.gl.OPTIONS))
        for name in self.gl.INSTALLED.values():
            self.assertNotIn(name, others)

    def test_grab_sinks_like_the_floor_lamp(self):
        cv = self.gl.CANVAS
        self.assertEqual(self.gl.GRAB, (cv.cx, cv.foot_row - 3))
        self.assertEqual(cv.cx * 2, cv.w, "the pole on the canvas centre")
        self.assertEqual(cv.w % 8, 0)
        self.assertEqual(cv.h % 8, 0)

    def test_unknown_option_raises(self):
        with self.assertRaises(ValueError):
            self.gl.render("C", "A")
        with self.assertRaises(ValueError):
            self.gl.render("A", "C")


@unittest.skipIf(SKIP_SLOW or not HAVE_IMAGING, "slow art tier (renders)")
class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import artlib
        import gen_loudspeaker as gl
        cls.gl = gl
        cls.v1 = {tuple(c) for c in artlib.load_palette()["colours"]}
        cls.red = set(artlib.ramp("flag_red"))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.sprites = gl.build(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_palette_v1_and_hard_alpha(self):
        for key, rgba in self.sprites.items():
            a = rgba[..., 3]
            self.assertTrue(set(np.unique(a)) <= {0, 255}, key)
            used = {tuple(int(v) for v in px) for px in rgba[a > 0][:, :3]}
            self.assertTrue(used <= self.v1, f"{key}: {sorted(used - self.v1)[:4]}")

    def test_nothing_touches_the_edge(self):
        for key, rgba in self.sprites.items():
            a = rgba[..., 3] > 0
            self.assertFalse(a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any(), key)

    def test_height_and_the_pole_on_the_grab_column(self):
        gx, gy = self.gl.GRAB
        for key, rgba in self.sprites.items():
            self.assertEqual(self.gl.top_height(rgba), self.gl.TOP_HEIGHT, key)
            a = rgba[..., 3] > 0
            self.assertTrue(a[gy - 30, gx - 1:gx + 2].any(), f"{key}: no pole at the grAb column")
            rows = np.nonzero(a.any(axis=1))[0]
            self.assertLessEqual(abs(int(rows[-1]) - gy), self.gl.SINK, key)

    def test_the_star_is_red(self):
        for key, rgba in self.sprites.items():
            a = rgba[..., 3] > 0
            reds = sum(1 for px in rgba[a][:, :3] if tuple(int(v) for v in px) in self.red)
            self.assertGreaterEqual(reds, 12, key)

    def test_frames_and_options_differ(self):
        for opt in self.gl.OPTIONS:
            a, b = self.sprites[(opt, "A")], self.sprites[(opt, "B")]
            diff = int((a != b).any(axis=2).sum())
            self.assertGreater(diff, 0, opt)
            self.assertLess(diff, a.shape[0] * a.shape[1] // 10, f"{opt}: B must stay subtle")
        self.assertFalse(np.array_equal(self.sprites[("A", "A")], self.sprites[("B", "A")]))

    def test_deterministic(self):
        self.assertTrue(np.array_equal(self.gl.render("A", "A"), self.sprites[("A", "A")]))

    def test_files_carry_the_grab(self):
        for opt in self.gl.OPTIONS:
            for frame in self.gl.FRAMES:
                p = self.out / opt / f"{self.gl.lump_name(frame)}.png"
                self.assertTrue(p.is_file(), p)
                self.assertEqual(read_grab(p), self.gl.GRAB, p)
                with Image.open(p) as im:
                    self.assertEqual(im.mode, "RGBA")
                    self.assertEqual(im.size, (self.gl.CANVAS.w, self.gl.CANVAS.h))


if __name__ == "__main__":
    unittest.main()
