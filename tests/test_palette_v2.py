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
              APPROVED_IN_V2 (the Legion trooper's SDLT set since D54, the
              metro mosaic SDMOSA1 since D56, the Doughboy's SDDB set
              since D70, the General's SDGN set since D73, the TT-33's
              held SDTT A-C since N17, the PPSh-41's SDPP A-B and
              SDPF A since D79, the blue pass's status bar icon STKEYS0
              since D80, the IZh-58's, RPG-7's, ROKS-3's and hand
              Katyusha's held and flash frames since D84, the ice axe's
              SDAX A-D since D88, the sergeant's 42 Gemini faces STF* since
              D90, Episode 2's bricks since D107, the portal rim and Episode
              2 round 2's six v2 walls since D113)

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
# D56 (2026-10-14, «mosaico V2»): the metro mosaic SDMOSA1 is replaced by its
# v2 rendering (mosaic_cobalt, mosaic_gold; gen_metro.py), same lump name.
# The marble SDMARB1 stays v1.
# D63 (2026-10-14): the blue pass SDKB A/B (gen_pickups.py, option B), drawn
# with v2's mosaic_cobalt so Doom's blue key reads blue (D45). RGBA, so
# check_pk3's PALETTE_V2_LUMPS (indexed lumps only) does not list it.
# D66 (2026-10-14): Tankograd (gen_factory.py). The brick SDBRCK1/2 in
# marble_red, the banners SDFLAG1/2 hung on that brick (SDFLAG2's canton in
# mosaic_cobalt) and the portal's four frames SDPORT1-4 in mosaic_cobalt.
# All indexed, so check_pk3's PALETTE_V2_LUMPS lists them too.
# D70 (2026-10-14): the Doughboy's 54 SDDB lumps (gen_heavy.py --full db,
# cell C with D67's bigger flag), drawn with v2's flesh_pink as the Legion
# trooper. RGBA, so check_pk3's PALETTE_V2_LUMPS does not list them.
# D73 (2026-10-14): the General's 81 SDGN lumps (gen_general.py --full, the
# CD design), drawn on the Legion's table with v2's flesh_pink. RGBA, so
# check_pk3's PALETTE_V2_LUMPS does not list them. His shell's 5 SDGL lumps
# (same folder) stay inside v1 and are not listed.
# N17 (2026-10-15): the TT-33's held frames SDTT A-C (hand_study.py
# build_tt33_fd, D61/D63), Freedoom's hands recoloured to v2's flesh_pink.
# RGBA, so check_pk3's PALETTE_V2_LUMPS does not list them. Its flash SDTFA0
# (same folder) stays inside v1 and is not listed.
# D79 (2026-10-20): the PPSh-41's SDPP A-B and its flash SDPF A
# (gemini_frames.py snaps the CEO's Gemini pair to all of palette v2: the
# skin and the flash's warm tones are v2). RGBA, not in PALETTE_V2_LUMPS.
# D80 (2026-10-20): the blue pass's 7x5 status bar icon STKEYS0
# (gen_items.py key_icon, mosaic_cobalt like SDKB). Indexed, so check_pk3's
# PALETTE_V2_LUMPS lists it. STKEYS1-2 are written on the v2 PLTE but use v1
# colours only, so they are not listed. The campaign pickups of D80 are all
# v1 (the heavy armour is option C, bare steel, not A's cobalt).
# D84 (2026-10-20): the IZh-58's SDIZ A-D / SDIF A-B, the RPG-7's SDRL A-B /
# SDRF A-D, the ROKS-3's SDRK A-B / SDKF A and the hand Katyusha's SDHK A-B /
# SDHF A-B, gemini_frames.py like the PPSh-41's (all of palette v2). RGBA,
# not in PALETTE_V2_LUMPS. The Katyusha's floor pickup SDHPA0 (D80) and the
# two enemy shells SDDL / SDPL (D81) are v1 and not listed.
# D88 (2026-10-20): the ice axe's SDAX A-D, the same way (no flash).
# D82 (2026-10-20): the player effects (assets/sprites/effects/, SDPG, SDKR,
# SDPX, SDFJ, SDFX and the IWAD-named PUFF, BLUD, TFOG, IFOG, BAR1, BEXP,
# COLU) are all v1 (gen_effects.py, palette_v1) and not listed.
# D89, D90, D92 (2026-10-20, M2e-i): the status bar (assets/graphics/statusbar/).
# The sergeant's 42 STF* faces (gemini_face.py snaps the Gemini sheets to all
# of palette v2: flesh_pink in the skin) are listed; RGBA, so check_pk3's
# PALETTE_V2_LUMPS (indexed lumps only) does not list them. Bar A (STBAR,
# STARMS, SDSBRU, SDARRU; indexed on the v2 PLTE) and digits N2 (RGBA) use v1
# colours only and are not listed.
HUD_FACES = ([f"STFST{level}{glance}" for level in range(5) for glance in range(3)]
             + [f"{kind}{level}" for kind in ("STFOUCH", "STFEVL", "STFKILL") for level in range(5)]
             + [f"STFT{side}{level}0" for side in "LR" for level in range(5)]
             + ["STFGOD0", "STFDEAD0"])
# D107 (2026-10-22): Episode 2's five bricks (gen_railway.py, gen_moscow.py),
# v1 plus marble_red only, as SDBRCK1 (D66): the roundhouse SDBRCK3, the
# Kremlin wall SDKREM1, its merlon SDKREM2 (RGBA, masked: check_pk3 lists it in
# PALETTE_V2_MASKED, not PALETTE_V2_LUMPS), the banner SDBANR1 hung on the wall
# and the Spasskaya stone SDSPAS1. Every other Episode 2 lump is v1.
EP2_BRICKS = (("railway", "SDBRCK3"), ("moscow", "SDKREM1"), ("moscow", "SDKREM2"),
              ("moscow", "SDBANR1"), ("moscow", "SDSPAS1"))
# D113 (installed 2026-10-22): Episode 3's portal rim SDPRTE1 (gen_taiga.py,
# mosaic_cobalt, the look of SDPORT1-4) and Episode 2 round 2's v2 pieces
# (gen_episode2b.py): the blue key door SDDOORB (mosaic_cobalt), the Spasskaya
# clock SDCLOK1 and the Historical Museum SDMUSE1 (marble_red), and the two
# banners on SDKREM1, SDFLAG3 (marble_red) and SDFLAG4 (marble_red and, in the
# canton, mosaic_cobalt). All indexed. Every other lump of both batches is v1,
# the three round-2 masked pieces and the crane included.
D113_V2 = (("taiga", "SDPRTE1"), ("dam", "SDDOORB"), ("moscow", "SDCLOK1"),
           ("moscow", "SDMUSE1"), ("moscow", "SDFLAG3"), ("moscow", "SDFLAG4"),
           # MAP09's sky (gen_episode3_skies.py): the portal's glow in
           # mosaic_cobalt, only where the portal lights it. SDSKY3/4 are v1.
           ("sky", "SDSKY5"))
# D109, D114 (installed 2026-10-22): the seven enemies redrawn from Google
# Gemini (gemini_enemy.py snaps every set to all of palette v2): SDRR, SDLT,
# SDHS, SDHN, SDDB, SDPM, SDPS and SDGN, 540 RGBA lumps (not in
# PALETTE_V2_LUMPS). The lump lists are tests/test_gemini_enemy_install.py's.
# Their projectiles SDBL, SDGL, SDDL and SDPL were not redrawn and stay v1.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_gemini_enemy_install import SETS as GEMINI_ENEMY_SETS  # noqa: E402
GEMINI_ENEMIES = {f"sprites/{folder}/{name}.png"
                  for folder, _, names, _ in GEMINI_ENEMY_SETS.values() for name in names}
D84_FRAMES = {"izh": ("SDIZ", "ABCD", "SDIF", "AB"), "rpg7": ("SDRL", "AB", "SDRF", "ABCD"),
              "roks3": ("SDRK", "AB", "SDKF", "A"), "katyusha": ("SDHK", "AB", "SDHF", "AB"),
              "ice_axe": ("SDAX", "ABCD", "SDAX", "")}
APPROVED_IN_V2: set[str] = (
    {f"sprites/legion/SDLT{f}{r}.png" for f in "ABCDEFG" for r in "12345678"}
    | {f"sprites/legion/SDLT{f}0.png" for f in "HIJKLMNOPQRSTU"}
    | {"textures/metro/SDMOSA1.png"}
    | {"sprites/pickups/SDKBA0.png", "sprites/pickups/SDKBB0.png"}
    | {f"textures/factory/{lump}.png" for lump in ("SDBRCK1", "SDBRCK2", "SDFLAG1", "SDFLAG2")}
    | {f"textures/factory/SDPORT{i}.png" for i in range(1, 5)}
    | {f"sprites/doughboy/SDDB{f}{r}.png" for f in "ABCDEF" for r in "12345678"}
    | {f"sprites/doughboy/SDDB{f}0.png" for f in "GHIJKL"}
    | {f"sprites/general/SDGN{f}{r}.png" for f in "ABCDEFGQR" for r in "12345678"}
    | {f"sprites/general/SDGN{f}0.png" for f in "HIJKLMNOP"}
    | {f"sprites/tt33/SDTT{f}0.png" for f in "ABC"}
    | {"sprites/ppsh/SDPPA0.png", "sprites/ppsh/SDPPB0.png", "sprites/ppsh/SDPFA0.png"}
    | {"graphics/hud/STKEYS0.png"}
    | {f"sprites/{folder}/{name}{f}0.png" for folder, (held, hf, flash, ff) in D84_FRAMES.items()
       for name, frames in ((held, hf), (flash, ff)) for f in frames}
    | {f"graphics/statusbar/{name}.png" for name in HUD_FACES}
    | {f"textures/{folder}/{lump}.png" for folder, lump in EP2_BRICKS}
    | {f"textures/{folder}/{lump}.png" for folder, lump in D113_V2}
    | GEMINI_ENEMIES)


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


class CheckPk3KnowsTheV2Lumps(unittest.TestCase):
    """check_pk3 lets exactly the indexed lumps approved in v2 use the v2 ramps."""

    def test_check_pk3_v2_list_matches_the_approved_indexed_lumps(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "check_pk3", Path(__file__).resolve().parents[1] / "tools" / "check_pk3.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("check_pk3", mod)  # dataclasses look the module up
        spec.loader.exec_module(mod)
        # Sprites are RGBA by rule; a graphic may be either (the faces are
        # RGBA, the key icon STKEYS0 indexed), so its PNG header decides.
        indexed = {Path(p).stem.upper() for p in APPROVED_IN_V2
                   if not p.startswith("sprites/") and (ASSETS / p).read_bytes()[25] == 3}
        self.assertEqual(set(mod.PALETTE_V2_LUMPS), indexed)
        # D107: the masked walls approved in v2 (RGBA under textures/).
        masked = {Path(p).stem.upper() for p in APPROVED_IN_V2
                  if p.startswith("textures/") and (ASSETS / p).read_bytes()[25] == 6}
        self.assertEqual(set(mod.PALETTE_V2_MASKED), masked)
