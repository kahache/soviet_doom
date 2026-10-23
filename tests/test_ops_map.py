"""Contract of V3 B1, the operations map between levels (ADR 013;
tools/art/gen_ops_map.py, src/lumps/SDOPSCR, MAPINFO).

  wiring     every campaign map (MAP01-MAP09) names "$SDOPSCR" as exitpic AND
             enterpic; the range (no intermission) does not; the script is a
             root lump in the package
  script     only the words of gzdoom.pk3's own intermission scripts
             (in_epi1-3.txt), each checked against the engine's copy when
             it is installed; every picture it names is packed; it is the
             generator's text, byte for byte (newlines aside)
  sites      the nine maps in campaign order, on screen, apart from one
             another, clear of the band where the engine prints the map
             name and "Entering"; the pointer fits the screen on every site
             (the engine draws it only if it does)
  semantics  read back the way the engine draws it (gen_ops_map.visible):
             on the stats page of MAPn the arrows into MAP02..MAPn, a star
             on MAP01..MAPn and the pulse on MAPn; on the entering page of
             MAPn+1 the arrows into MAP02..MAPn+1, the stars on MAP01..MAPn
             and the pointer on MAPn+1; nothing of a later map
  pictures   the background 320x200 indexed, the overlays RGBA with hard
             alpha, all in palette v2; the markers' grAb at their centre,
             the arrows' at 0,0; the installed files are the generator's
             bytes (renders skip under SD_SKIP_SLOW_ART)
  D27        no system font in the generators

Run:  .venv/Scripts/python.exe -m unittest tests.test_ops_map -v
"""

from __future__ import annotations

import math
import os
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
sys.path.insert(0, str(TESTS))

import gen_ops_map  # noqa: E402  (stdlib at import time)
import v3lib  # noqa: E402
from test_death_prompt import gzdoom_pk3, strip_lump_comments  # noqa: E402

MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
SCRIPT = PROJECT_ROOT / "src" / "lumps" / "SDOPSCR"
ASSETS = PROJECT_ROOT / "assets" / "graphics" / "opsmap"
CAMPAIGN = tuple(f"MAP0{i}" for i in range(1, 10))
SCRIPT_REF = "$SDOPSCR"
RE_MAP_BLOCK = re.compile(r'^map\s+(\w+)[^{]*\{(.*?)^\}', re.M | re.S | re.I)
# The engine prints the map name and "Finished" / "Entering" (BigFont, two
# lines from y=5) in this band: no site may sit in it.
TEXT_BAND_BOTTOM = 45
MIN_SITE_DISTANCE = 10.0
# The words gzdoom's intermission-script parser knows (the strings next to
# one another in gzdoom.exe; the shipped in_epi*.txt use the ones we use).
ENGINE_WORDS = {"background", "screensize", "splat", "pointer", "spots", "ifleaving", "ifentering", "pic",
                "animation"}

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover
    HAVE_IMAGING = False
imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not installed")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the renders")


def png_size(blob: bytes) -> tuple[int, int, int]:
    """(width, height, colour type) from a PNG's IHDR, stdlib only."""
    assert blob[:8] == b"\x89PNG\r\n\x1a\n"
    w, h, _, colour = struct.unpack(">IIBB", blob[16:26])
    return w, h, colour


def map_blocks() -> dict[str, str]:
    text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
    return {m.group(1).upper(): m.group(2) for m in RE_MAP_BLOCK.finditer(text)}


def parsed():
    return gen_ops_map.parse_script(SCRIPT.read_text(encoding="ascii"))


class WiringTest(unittest.TestCase):
    def test_every_campaign_map_names_the_script_both_ways(self):
        blocks = map_blocks()
        for m in CAMPAIGN:
            body = blocks[m]
            for key in ("exitpic", "enterpic"):
                values = re.findall(rf'(?im)^\s*{key}\s*=\s*"([^"]*)"', body)
                self.assertEqual(values, [SCRIPT_REF], f"{m} {key}")

    def test_the_range_keeps_no_intermission(self):
        body = map_blocks()["RANGE"]
        self.assertRegex(body, r"(?im)^\s*nointermission\b")
        self.assertNotRegex(body, r"(?i)exitpic|enterpic")

    def test_the_script_is_a_root_lump_of_the_package(self):
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        from sdbuild.pk3 import build
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "t.pk3"
            build(PROJECT_ROOT / "src", out, PROJECT_ROOT / "tools", PROJECT_ROOT / "assets")
            names = {n.lower() for n in zipfile.ZipFile(out).namelist()}
        self.assertIn("sdopscr", names)
        for lump in self.lumps_named():
            self.assertIn(f"graphics/{lump.lower()}.png", names, lump)

    def lumps_named(self) -> set[str]:
        p = parsed()
        names = {p["background"], p["splat"], *p["pointer"]}
        for *_, frames in p["anims"]:
            names.update(frames)
        return names


class ScriptTest(unittest.TestCase):
    def test_only_the_engines_words(self):
        body = re.sub(r"//[^\n]*", "", SCRIPT.read_text(encoding="ascii"))
        words = {w.lower() for w in re.findall(r"(?m)^\s*([A-Za-z0-9_]+)", body)}
        words -= {m.lower() for m in CAMPAIGN} | {"sdopcur0", "sdopcur1"}
        self.assertLessEqual(words, ENGINE_WORDS)

    def test_the_words_are_the_engines_own(self):
        """Each word appears in gzdoom.pk3's own Doom 1 scripts, read from the
        installed engine (skipped where GZDoom is not installed)."""
        pk3 = gzdoom_pk3()
        if pk3 is None:
            self.skipTest("gzdoom.pk3 not installed")
        with zipfile.ZipFile(pk3) as z:
            engine = " ".join(z.read(n).decode("latin-1") for n in z.namelist()
                              if re.match(r"(?i)^in_epi[123]\.txt$", n)).lower()
        for word in ENGINE_WORDS:
            self.assertIn(word, engine, word)
        self.assertRegex(engine, r"ifleaving e\dm\d pic \d+ \d+ \w+")
        self.assertRegex(engine, r"ifentering e\dm\d animation \d+ \d+ \d+")

    def test_every_picture_is_installed(self):
        installed = {p.stem.upper() for p in ASSETS.glob("*.png")}
        self.assertLessEqual({n.upper() for n in WiringTest.lumps_named(self)}, installed)

    def test_it_parses_and_has_the_header(self):
        p = parsed()
        self.assertEqual(p["background"], "SDOPMAP")
        self.assertEqual(p["size"], (gen_ops_map.WIDTH, gen_ops_map.HEIGHT))
        self.assertEqual(p["splat"], "SDOPSTAR")
        self.assertEqual(p["pointer"], ["SDOPYAH0"])

    @imaging
    def test_it_is_the_generators_text(self):
        on_disk = SCRIPT.read_text(encoding="ascii").replace("\r\n", "\n")
        self.assertEqual(on_disk, gen_ops_map.script_text())


class SitesTest(unittest.TestCase):
    def test_nine_sites_in_campaign_order(self):
        self.assertEqual(tuple(parsed()["spots"]), CAMPAIGN)
        self.assertEqual(gen_ops_map.MAPS, CAMPAIGN)

    def test_on_screen_and_clear_of_the_text_band(self):
        for m, (x, y) in parsed()["spots"].items():
            self.assertTrue(0 <= x < gen_ops_map.WIDTH and TEXT_BAND_BOTTOM <= y < gen_ops_map.HEIGHT, (m, x, y))

    def test_apart(self):
        spots = list(parsed()["spots"].values())
        for i, a in enumerate(spots):
            for b in spots[i + 1:]:
                self.assertGreaterEqual(math.dist(a, b), MIN_SITE_DISTANCE, (a, b))

    def test_the_script_sites_are_the_generators(self):
        self.assertEqual(parsed()["spots"], gen_ops_map.sites())

    def test_the_mod_spec_lists_the_sites(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        section = spec[spec.index("## 6.13"):spec.index("## 7. Commands")]
        listed = {m: (int(x), int(y)) for m, x, y in re.findall(r"(MAP0\d) \((\d+),(\d+)\)", section)}
        self.assertEqual(listed, parsed()["spots"])

    def test_the_pointer_fits_on_every_site(self):
        """DInterBackground::drawOnLnode draws a pointer only if it lies wholly
        on the 320x200 screen."""
        p = parsed()
        blob = (ASSETS / f"{p['pointer'][0]}.png").read_bytes()
        w, h, _ = png_size(blob)
        gx, gy = v3lib.read_grab(blob)
        for m, (x, y) in p["spots"].items():
            left, top = x - gx, y - gy
            self.assertTrue(left >= 0 and top >= 0 and left + w < 320 and top + h < 200, m)

    def test_the_warp_is_monotonic(self):
        rs = [i * 0.25 for i in range(int(gen_ops_map.WARP_RADIUS * 4) + 8)]
        out = [gen_ops_map.warp_radius(r) for r in rs]
        self.assertTrue(all(b > a for a, b in zip(out, out[1:])))
        self.assertAlmostEqual(gen_ops_map.warp_radius(gen_ops_map.WARP_RADIUS - 1e-9), gen_ops_map.WARP_RADIUS, 5)


class SemanticsTest(unittest.TestCase):
    def setUp(self):
        self.p = parsed()

    def drawn(self, page, current, nxt):
        return gen_ops_map.visible(self.p, page, current, nxt, visited=CAMPAIGN[:CAMPAIGN.index(current) + 1])

    def arrows(self, items):
        return sorted(l for l, *_ in items if l.startswith("SDOPR"))

    def stars_at(self, items):
        return {(x, y) for l, x, y in items if l == "SDOPSTAR"}

    def test_the_stats_page_of_each_map(self):
        spots = self.p["spots"]
        for n, m in enumerate(CAMPAIGN, start=1):
            items = self.drawn("stats", m, CAMPAIGN[n] if n < 9 else "")
            self.assertEqual(self.arrows(items), [f"SDOPR0{k}" for k in range(2, n + 1)], m)
            self.assertEqual(self.stars_at(items), {spots[x] for x in CAMPAIGN[:n]}, m)
            pulses = [(x, y) for l, x, y in items if l.startswith("SDOPCUR")]
            self.assertEqual(pulses, [spots[m]], m)
            self.assertFalse(any(l == "SDOPYAH0" for l, *_ in items), m)

    def test_the_entering_page_of_each_map(self):
        spots = self.p["spots"]
        for n in range(1, 9):
            cur, nxt = CAMPAIGN[n - 1], CAMPAIGN[n]
            items = self.drawn("entering", cur, nxt)
            self.assertEqual(self.arrows(items), [f"SDOPR0{k}" for k in range(2, n + 2)], nxt)
            self.assertEqual(self.stars_at(items), {spots[x] for x in CAMPAIGN[:n]}, nxt)
            self.assertEqual([(x, y) for l, x, y in items if l == "SDOPYAH0"], [spots[nxt]], nxt)
            self.assertFalse(any(l.startswith("SDOPCUR") for l, *_ in items), nxt)

    def test_progress_does_not_depend_on_visited(self):
        """A New Game of episode 2 visits only MAP04: the road from Zarya-7 is
        still drawn as travelled (the script never uses IfVisited)."""
        items = gen_ops_map.visible(self.p, "stats", "MAP04", "MAP05", visited=("MAP04",))
        self.assertEqual(self.arrows(items), ["SDOPR02", "SDOPR03", "SDOPR04"])
        self.assertNotIn("ifvisited", {a[0] for a in self.p["anims"]})

    def test_every_condition_names_a_campaign_map(self):
        for cond, cmap, *_ in self.p["anims"]:
            if cond:
                self.assertIn(cmap, CAMPAIGN)


@imaging
class PicturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import palette
        cls.v2 = {tuple(c) for c in palette.colours(2)}

    def test_background(self):
        im = Image.open(ASSETS / "SDOPMAP.png")
        self.assertEqual(im.size, (320, 200))
        self.assertEqual(im.mode, "P")
        used = {c for _, c in im.convert("RGB").getcolors(4096)}
        self.assertLessEqual(used, self.v2)

    def test_overlays(self):
        for path in ASSETS.glob("*.png"):
            if path.stem == "SDOPMAP":
                continue
            blob = path.read_bytes()
            im = Image.open(path)
            self.assertEqual(im.mode, "RGBA", path.name)
            a = np.asarray(im)
            self.assertLessEqual(set(np.unique(a[..., 3]).tolist()), {0, 255}, path.name)
            opaque = {tuple(c) for c in a[a[..., 3] == 255][:, :3].tolist()}
            self.assertLessEqual(opaque, self.v2, path.name)
            grab = v3lib.read_grab(blob)
            if path.stem.startswith("SDOPR"):
                self.assertEqual(grab, (0, 0), path.name)
            else:
                self.assertEqual(grab, (im.width // 2, im.height // 2), path.name)

    @slow
    def test_installed_is_the_generators_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            blobs = gen_ops_map.build(Path(tmp))
            self.assertTrue(all(Path(tmp, n).is_file() for n in blobs))
        for name, blob in blobs.items():
            if name == gen_ops_map.SCRIPT_LUMP:
                continue
            self.assertEqual((ASSETS / name).read_bytes(), blob, name)
        self.assertEqual({p.name for p in ASSETS.glob("*.png")}, {n for n in blobs if n.endswith(".png")})

    @slow
    def test_build_writes_only_where_it_is_told(self):
        before = {p: p.stat().st_mtime_ns for p in ASSETS.glob("*")}
        with tempfile.TemporaryDirectory() as tmp:
            gen_ops_map.build(Path(tmp))
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in ASSETS.glob("*")})


class NoSystemFontTest(unittest.TestCase):
    def test_no_font_is_opened(self):
        for name in ("gen_ops_map.py", "gen_medals.py", "v3lib.py", "opsmap_preview.py", "opsmap_geo.py"):
            text = (ART_TOOLS / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"ImageFont|truetype|\.ttf|\.otf|FONT_POSTER|FONT_SMALL", name)


if __name__ == "__main__":
    unittest.main()
