"""Palette v2 (D45, CEO 2026-10-14) and the version contract of the art.

What is enforced here, and why:

  version     palette.json says v2, dated 2026-10-14, decision D45, and keeps
              its version history (v1 162 colours, v2 226)
  subset      v1 is the EXACT prefix of v2, index for index: no v1 colour
              moved, was edited or was reordered (ART-BIBLE §3: "later sets
              only add ramps in the reserved slots"), so every v1 PNG is a
              valid v2 PNG
  frozen      the v1 colours still hash to the digest recorded when the CEO
              ratified them, in palette.py's build and on disk
  ramps       the four added ramps follow palette.py's own rule (gamma 1.8,
              16 steps), are monotonic per channel, new to the palette, and
              the flesh pink is exactly the Legion drafts' candidate
  layout      the top-level view (colours / ramps / index / count) is still
              v1, which is what artlib.quantize and check_pk3 read: an
              approved v1 texture cannot drift into v2 when it is rebuilt
  assets      no approved asset uses a colour outside the palette version it
              was approved in. Every asset is v1 until it is listed in
              APPROVED_IN_V2 (the Legion trooper's SDLT set since D54)

Run:  .venv/Scripts/python.exe -m unittest tests.test_palette_v2 -v
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
ASSETS = PROJECT_ROOT / "assets"
sys.path.insert(0, str(ART_TOOLS))

import palette as palette_mod  # noqa: E402  (stdlib only, always importable)

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

# Written out, not imported: the test is the second witness.
V1_COUNT = 162
V1_SHA256 = "3c94bf22bf1a758af260bcc67006485c34d1e2123f6a8e434cf44651f7243515"  # = tests/test_artlib.py
V2_COUNT = 226
V2_DATE = "2026-10-14"
V2_DECISION = "D45"
V2_RAMPS = ["marble_red", "mosaic_cobalt", "mosaic_gold", "flesh_pink"]
V2_STEPS = 16
FLESH_DARK, FLESH_LIGHT = (24, 10, 10), (242, 190, 180)   # tools/art/gen_legion.py candidate
MAX_COLOURS = 256

# Approved assets drawn in palette v2, by path relative to assets/. Empty
# until the CEO approves the first v2 texture (e.g. SDMARB1_v2 replacing
# SDMARB1); everything not listed here must stay inside v1.
# D54 (2026-10-14): the Legion trooper's 70 SDLT lumps, drawn with palette
# v2's flesh_pink (gen_legion.py), are the first v2 assets approved.
APPROVED_IN_V2: set[str] = (
    {f"sprites/legion/SDLT{f}{r}.png" for f in "ABCDEFG" for r in "12345678"}
    | {f"sprites/legion/SDLT{f}0.png" for f in "HIJKLMNOPQRSTU"})


def _digest(colours) -> str:
    return hashlib.sha256(
        json.dumps([list(c) for c in colours], separators=(",", ":")).encode()
    ).hexdigest()


class PaletteVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disk = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        cls.built = palette_mod.build_palette()

    def test_file_is_v2_dated_with_its_decision(self):
        self.assertEqual(self.disk["version"], 2)
        self.assertEqual(self.disk["date"], V2_DATE)
        self.assertEqual(self.disk["decision"], V2_DECISION)
        history = {v["version"]: v for v in self.disk["versions"]}
        self.assertEqual(sorted(history), [1, 2])
        self.assertEqual(history[1]["count"], V1_COUNT)
        self.assertEqual(history[2]["count"], V2_COUNT)
        self.assertEqual(history[2]["date"], V2_DATE)
        self.assertIn(V2_DECISION, history[2]["decision"])
        self.assertEqual(history[2]["adds"], V2_RAMPS)

    def test_file_is_what_the_generator_writes(self):
        self.assertEqual(self.built, self.disk)

    def test_v1_is_the_exact_prefix_of_v2(self):
        v1, v2 = self.disk["colours"], self.disk["colours_v2"]
        self.assertEqual(len(v1), V1_COUNT)
        self.assertEqual(len(v2), V2_COUNT)
        self.assertEqual(v2[:V1_COUNT], v1)                       # index for index
        self.assertTrue({tuple(c) for c in v1} <= {tuple(c) for c in v2})

    def test_v1_is_still_the_ratified_v1(self):
        self.assertEqual(_digest(self.disk["colours"]), V1_SHA256)
        self.assertEqual(_digest(self.disk["colours_v2"][:V1_COUNT]), V1_SHA256)
        self.assertEqual(_digest(palette_mod.colours(1)), V1_SHA256)

    def test_v2_fits_and_has_no_duplicate(self):
        v2 = [tuple(c) for c in self.disk["colours_v2"]]
        self.assertLessEqual(len(v2), MAX_COLOURS)
        self.assertEqual(len(v2), len(set(v2)))
        self.assertEqual(palette_mod.colours(2), v2)

    def test_top_level_view_is_still_v1(self):
        """artlib.quantize, check_pk3 and every generator read these keys."""
        self.assertEqual(self.disk["count"], V1_COUNT)
        self.assertEqual([r["name"] for r in self.disk["ramps"]], [r[0] for r in palette_mod.RAMPS])
        self.assertFalse(set(V2_RAMPS) & set(self.disk["index"]))
        self.assertEqual(palette_mod.LATEST_VERSION, 2)

    def test_unknown_version_raises(self):
        with self.assertRaises(KeyError):
            palette_mod.colours(3)


class AddedRampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disk = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        cls.added = {r["name"]: r for r in cls.disk["added_ramps"]}

    def test_the_three_d45_additions_in_slot_order(self):
        self.assertEqual([r["name"] for r in self.disk["added_ramps"]], V2_RAMPS)
        start = V1_COUNT
        for name in V2_RAMPS:
            self.assertEqual(self.disk["added_index"][name], [start, start + V2_STEPS - 1], name)
            self.assertEqual(self.disk["colours_v2"][start:start + V2_STEPS], self.added[name]["colours"], name)
            self.assertEqual(self.added[name]["version"], 2, name)
            start += V2_STEPS

    def test_each_ramp_follows_the_palette_rule(self):
        declared = {r[0]: r for r in palette_mod.ADDED_RAMPS}
        for name, ramp in self.added.items():
            _, dark, light, steps, _, why = declared[name]
            self.assertEqual(steps, V2_STEPS, name)
            self.assertTrue(why.strip(), name)
            expected = [[palette_mod._lerp_gamma(dark[c], light[c], i / (steps - 1)) for c in range(3)]
                        for i in range(steps)]
            self.assertEqual(ramp["colours"], expected, name)
            self.assertEqual(palette_mod.RAMP_GAMMA, 1.8)

    def test_monotonic_per_channel_darkest_first(self):
        for name, ramp in self.added.items():
            for ch in range(3):
                values = [c[ch] for c in ramp["colours"]]
                self.assertEqual(values, sorted(values), f"{name} channel {ch}")

    def test_no_added_colour_was_already_in_v1(self):
        v1 = {tuple(c) for c in self.disk["colours"]}
        for name, ramp in self.added.items():
            self.assertFalse({tuple(c) for c in ramp["colours"]} & v1, name)

    def test_flesh_pink_is_the_legion_candidate(self):
        ramp = [tuple(c) for c in self.added["flesh_pink"]["colours"]]
        self.assertEqual(ramp[0], FLESH_DARK)
        self.assertEqual(ramp[-1], FLESH_LIGHT)
        self.assertEqual(palette_mod.ramp_colours("flesh_pink"), ramp)

    @unittest.skipUnless(HAVE_IMAGING, "gen_legion needs numpy + Pillow (project venv)")
    def test_flesh_pink_matches_gen_legion_today(self):
        """If the Legion generator still carries its own candidate, it must
        be byte-identical to v2's, or the drafts drift from the palette."""
        try:
            import gen_legion
        except Exception as exc:  # pragma: no cover - another agent's file in flux
            self.skipTest(f"gen_legion not importable: {exc}")
        if not hasattr(gen_legion, "flesh_ramp"):
            self.skipTest("gen_legion no longer carries a candidate ramp")
        self.assertEqual([tuple(c) for c in gen_legion.flesh_ramp()],
                         palette_mod.ramp_colours("flesh_pink"))

    def test_ramp_version_lookup(self):
        self.assertEqual(palette_mod.ramp_version("flag_red"), 1)
        for name in V2_RAMPS:
            self.assertEqual(palette_mod.ramp_version(name), 2)
        with self.assertRaises(KeyError):
            palette_mod.ramp_version("no_such_ramp")


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class ApprovedAssetsStayInTheirVersionTests(unittest.TestCase):
    """Every PNG in assets/ uses only colours of the version it was approved
    in. Indexed PNGs are read through their palette (only the entries the
    pixels use); RGBA ones (fonts, M_DOOM) by their opaque pixels."""

    @classmethod
    def setUpClass(cls):
        cls.versions = {1: set(palette_mod.colours(1)), 2: set(palette_mod.colours(2))}
        cls.pngs = sorted(ASSETS.rglob("*.png"))

    @staticmethod
    def used_colours(path: Path) -> set:
        with Image.open(path) as im:
            if im.mode == "P":
                pal = im.getpalette()
                return {tuple(pal[i * 3:i * 3 + 3]) for i in set(im.get_flattened_data())}
            rgba = np.asarray(im.convert("RGBA"))
        opaque = rgba[..., 3] > 0
        return {tuple(int(v) for v in c) for c in rgba[opaque][:, :3]}

    def test_assets_exist(self):
        self.assertGreater(len(self.pngs), 30)

    def test_listed_v2_assets_exist(self):
        for rel in APPROVED_IN_V2:
            self.assertTrue((ASSETS / rel).is_file(), rel)

    def test_every_asset_stays_inside_its_version(self):
        for path in self.pngs:
            rel = path.relative_to(ASSETS).as_posix()
            version = 2 if rel in APPROVED_IN_V2 else 1
            outside = self.used_colours(path) - self.versions[version]
            self.assertFalse(outside, f"{rel} (palette v{version}): {sorted(outside)[:5]}")


if __name__ == "__main__":
    unittest.main()
