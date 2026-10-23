"""Art pipeline checks: palette limits and batch-1 texture contract.

Run:  .venv/bin/python -m unittest tests.test_art -v
(The system python3 may lack Pillow/numpy; those tests are then skipped,
the palette JSON checks always run.)
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(ART_TOOLS))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

# The masked wall textures (D66): RGBA with hard alpha, the one exception to
# the indexed rule under textures/. One set, owned by the package validator,
# so the two checks cannot disagree about which lumps are masked.
from check_pk3 import MASKED_TEXTURES  # noqa: E402
# The declared skies (D113) and their size, the same way: one owner.
from check_pk3 import SKY_SIZES, SKY_TEXTURES  # noqa: E402

# The status bar lumps (M2e-i): Freedoom's names and sizes, one table.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hud_install import FREEDOOM as HUD_FREEDOOM  # noqa: E402
from test_hud_install import LOCALIZED as HUD_LOCALIZED  # noqa: E402

try:
    import numpy  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover
    HAVE_IMAGING = False

LUMP_RE = re.compile(r"^SD[A-Z0-9]{1,6}$")
DIMENSION_MULTIPLE = 8


class PaletteJsonTests(unittest.TestCase):
    def setUp(self):
        self.pal = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))

    def test_at_most_256_unique_colours(self):
        cols = [tuple(c) for c in self.pal["colours"]]
        self.assertLessEqual(len(cols), 256)
        self.assertEqual(len(cols), len(set(cols)))
        self.assertEqual(len(cols), self.pal["count"])

    def test_ramps_are_monotonic_in_luminance(self):
        for ramp in self.pal["ramps"]:
            lum = [sum(c) for c in ramp["colours"]]
            self.assertEqual(lum, sorted(lum), ramp["name"])

    def test_palette_matches_generator(self):
        import palette as palette_cli
        self.assertEqual(palette_cli.build_palette()["colours"], self.pal["colours"])


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class Batch1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_soviet_base as gen
        from artlib import quantize
        from PIL import Image
        cls.gen = gen
        cls.built = {}
        for lump, builder, kind, *_ in gen.TEXTURES:
            rgb = builder()
            cls.built[lump] = (kind, rgb, quantize(Image.fromarray(rgb, "RGB")))

    def test_batch_size_within_rules(self):
        self.assertTrue(8 <= len(self.built) <= 12, len(self.built))

    def test_lump_names(self):
        for lump in self.built:
            self.assertRegex(lump, LUMP_RE)
            self.assertLessEqual(len(lump), 8)

    def test_dimensions(self):
        for lump, (kind, rgb, _) in self.built.items():
            h, w = rgb.shape[:2]
            self.assertEqual(w % DIMENSION_MULTIPLE, 0, lump)
            self.assertEqual(h % DIMENSION_MULTIPLE, 0, lump)
            if kind == "flat":
                self.assertEqual((w, h), (64, 64), lump)
            else:
                self.assertIn((w, h), [(64, 128), (128, 128)], lump)

    def test_quantised_colours_are_palette_subset(self):
        pal = {tuple(c) for c in json.loads(PALETTE_JSON.read_text())["colours"]}
        for lump, (_, _, img) in self.built.items():
            p = img.getpalette()
            used = {tuple(p[i * 3:i * 3 + 3]) for i in set(img.get_flattened_data())}
            self.assertTrue(used <= pal, f"{lump}: {used - pal}")
            self.assertLessEqual(len(used), 256)

    def test_deterministic(self):
        import numpy as np
        lump, builder, *_ = self.gen.TEXTURES[0]
        self.assertTrue(np.array_equal(builder(), self.built[lump][1]))


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class EmblemGeometryTests(unittest.TestCase):
    """SDSTAR1 v3: the hammer and sickle follow the CEO's reference, not its
    mirror image (the v2 mistake). Points are in the unit square of
    gen_soviet_base (origin top-left, y down); every GOLD point has a RED
    twin at the position the mirrored layout would paint, so a flipped
    emblem fails."""

    BOX = 256
    GOLD, RED = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)  # filled in setUpClass
    # (gold point, its red twin)
    PAIRS = [
        ((0.23, 0.50), (0.77, 0.50)),   # hammer head sits mid-LEFT, never mid-right
        ((0.38, 0.33), (0.62, 0.33)),   # blade sweeps over the head on the left
        ((0.62, 0.18), (0.38, 0.18)),   # top of the crescent leans right
        ((0.91, 0.52), (0.09, 0.52)),   # blade mass hugs the right edge
        ((0.78, 0.71), (0.22, 0.71)),   # hammer handle runs down to the RIGHT
    ]

    @classmethod
    def setUpClass(cls):
        import numpy as np
        import gen_soviet_base as gen
        from artlib import Overlay, ramp_colour
        cls.gen = gen
        cls.gold = np.array(ramp_colour("hazard_yellow", 0.88), dtype=float)
        cls.red = np.array(ramp_colour("flag_red", 0.70), dtype=float)
        bg = np.full((cls.BOX, cls.BOX, 3), cls.red, dtype=np.uint8)
        ov = Overlay(cls.BOX, cls.BOX)
        gen.hammer_sickle(ov, cls.BOX / 2, cls.BOX / 2, cls.BOX / 2,
                          tuple(int(c) for c in cls.gold), ramp_colour("flag_red", 0.25))
        cls.img = ov.composite(bg).astype(float)

    def _is_gold(self, u, v):
        import numpy as np
        px = self.img[int(v * self.BOX), int(u * self.BOX)]
        return np.linalg.norm(px - self.gold) < np.linalg.norm(px - self.red)

    def test_layout_matches_reference_not_mirror(self):
        for gold_pt, red_pt in self.PAIRS:
            self.assertTrue(self._is_gold(*gold_pt), f"expected gold at {gold_pt}")
            self.assertFalse(self._is_gold(*red_pt), f"expected red at {red_pt}")

    def test_hammer_head_clears_sickle_tip(self):
        import numpy as np
        g = self.gen
        c = np.array(g.HAMMER_HEAD_C)
        hs, he = (np.array(p) for p in g.HAMMER_HANDLE)
        hd = (he - hs) / np.linalg.norm(he - hs)
        hn = np.array([-hd[1], hd[0]])
        d = np.array(g.SICKLE_TIP) - c
        over = np.array([max(0.0, abs(d @ hn) - g.HAMMER_HEAD_L / 2),
                         max(0.0, abs(d @ hd) - g.HAMMER_HEAD_W / 2)])
        self.assertGreaterEqual(np.linalg.norm(over), g.HAMMER_TIP_CLEARANCE)

    def test_hammer_butt_reaches_bottom_right_corner(self):
        """CEO 2026-10-12: the butt of the hammer handle must reach the
        bottom-right corner, mirroring the sickle handle end at the
        bottom-left. Both ends are checked against each other so the pair
        stays symmetric if either is retuned."""
        import numpy as np
        g = self.gen
        butt = np.array(g.HAMMER_HANDLE[1])
        sickle_end = np.array(g.SICKLE_HANDLE[1])
        self.assertGreater(butt[0], 0.88)      # hard against the right edge
        self.assertGreater(butt[1], 0.92)      # and against the bottom
        mirrored = np.array([1.0 - sickle_end[0], sickle_end[1]])
        self.assertLess(float(np.linalg.norm(butt - mirrored)), 0.06)

    def test_hammer_handle_slope(self):
        """~41 deg since variant D1 (CEO 2026-10-12): the head moved down to
        mid-height, so the run to the fixed bottom-right butt is flatter."""
        import numpy as np
        hs, he = (np.array(p) for p in self.gen.HAMMER_HANDLE)
        self.assertGreater(he[0], hs[0])   # to the right
        self.assertGreater(he[1], hs[1])   # downwards (y down)
        slope = np.degrees(np.arctan2(he[1] - hs[1], he[0] - hs[0]))
        self.assertAlmostEqual(slope, 41.0, delta=3.0)


ASSETS_DIR = PROJECT_ROOT / "assets"
WORK_ART_DIR = PROJECT_ROOT / "work" / "art"
# Our sprite lumps: SD + 2, a frame letter and a rotation, optionally a
# second frame and rotation (Doom's mirrored pair, NAMEFRFR; D55's hound).
SPRITE_LUMP_RE = r"^SD[A-Z0-9]{2}[A-Z][0-8]([A-Z][1-8])?$"
# The one exception to the SD prefix among sprites (D82, MOD-SPEC 1 and
# 5.1): the engine actors' overrides, shipped under the IWAD's own names
# with exactly Freedoom's lump set, all in sprites/effects/
# (tests/test_effects_install.py holds the set).
IWAD_OVERRIDE_SPRITES = ("PUFF", "BLUD", "TFOG", "IFOG", "BAR1", "BEXP", "COLU")
IWAD_OVERRIDE_RE = r"^(" + "|".join(IWAD_OVERRIDE_SPRITES) + r")[A-Z]0$"


def sprite_slots(stem: str) -> list[tuple[str, str]]:
    """The (frame, rotation) slots a sprite lump fills: one for NAMEFR, two
    for a mirrored pair NAMEFRFR (the second half is drawn flipped)."""
    return [(stem[4], stem[5])] + ([(stem[6], stem[7])] if len(stem) == 8 else [])
FLAT_SIZE = (64, 64)
WALL_SIZES = [(64, 64), (64, 128), (128, 64), (128, 128), (128, 256),   # 128x256 for the Lenin poster; 64x64 and 128x64 for the batch-3 crates (D29)
              (256, 64)]                                                # the Tankograd works banner SDSLOG1 (D66)


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class ApprovedAssetsTests(unittest.TestCase):
    """assets/ holds only CEO-approved PNGs, copied byte for byte from work/
    (gitignored). The identity check is skipped where work/ does not exist
    (fresh clone, CI); the layout checks always run."""

    def setUp(self):
        self.pngs = sorted(ASSETS_DIR.rglob("*.png")) if ASSETS_DIR.is_dir() else []

    # Screens the engine names itself. They are the documented exception to
    # the SD prefix (MOD-SPEC 1) and to the indexed-PNG rule: M_DOOM is a menu
    # patch and needs an alpha channel, hard 0/255 (LICENSES.md, D18). The
    # menu cursor B (two blink phases, one size) and the English pause sign
    # P2 joined them in D48 (measured on the installed files, 2026-10-14).
    # D80: the status bar's key icons STKEYS0-2 (blue, yellow, red pass),
    # 7x5 as Freedoom's, which DoomStatusBar names itself.
    SHELL_SIZES = {"TITLEPIC": (320, 200), "INTERPIC": (320, 200), "M_DOOM": (200, 64),
                   "M_SKULL1": (20, 20), "M_SKULL2": (20, 20), "M_PAUSE": (77, 20),
                   "STKEYS0": (7, 5), "STKEYS1": (7, 5), "STKEYS2": (7, 5),
                   # D102: the mouse pointer (GameInfo CursorPic), under 32x32 for Windows.
                   "SDCURSOR": (28, 25)}
    # M2e-i (D89, D90, D92): status bar A, the Gemini face and digits N2 under
    # Freedoom's names and sizes, plus bar A's Russian pictures SDSBRU and
    # SDARRU and, since P6 (D97), the Catalan SDSBCA and SDARCA
    # (tests/test_hud_install.py holds the set and the offsets).
    SHELL_SIZES.update({name: (w, h) for name, (w, h, _, _) in HUD_FREEDOOM.items()})
    SHELL_SIZES.update({local: HUD_FREEDOOM[base][:2] for local, base in HUD_LOCALIZED.items()})
    # V3 B1/B3 (ADR 013, proposal): the operations map, its arrows and
    # markers (tools/art/gen_ops_map.py; an arrow's box is its segment's) and
    # the five awards (tools/art/gen_medals.py). tests/test_ops_map.py and
    # tests/test_awards.py hold them to their generators.
    SHELL_SIZES.update({"SDOPMAP": (320, 200), "SDOPSTAR": (9, 9), "SDOPCUR0": (17, 17),
                        "SDOPCUR1": (17, 17), "SDOPYAH0": (17, 17),
                        "SDOPR02": (13, 13), "SDOPR03": (14, 17), "SDOPR04": (13, 15),
                        "SDOPR05": (38, 14), "SDOPR06": (14, 19), "SDOPR07": (64, 28),
                        "SDOPR08": (29, 17), "SDOPR09": (77, 71)})
    SHELL_SIZES.update({lump: (24, 30) for lump in ("SDAWCOU", "SDAWRST", "SDAWRBN", "SDAWPTW", "SDAWHER")})

    def test_layout_names_and_sizes(self):
        from PIL import Image
        for p in self.pngs:
            kind = p.relative_to(ASSETS_DIR).parts[0]
            self.assertIn(kind, ("textures", "flats", "graphics", "fonts", "sprites", "localized"), p)
            with Image.open(p) as img:
                if kind == "localized":
                    # ADR 010: localized/textures/<BASE>.<lang>.png, the same
                    # size as its base shell picture, RGBA with hard alpha.
                    base, _, lang = p.stem.partition(".")
                    self.assertEqual(p.parent.relative_to(ASSETS_DIR).as_posix(),
                                     "localized/textures", p)
                    self.assertIn(base, self.SHELL_SIZES, p)
                    self.assertRegex(lang, r"^[a-z]{2,3}$", p)
                    self.assertEqual(img.size, self.SHELL_SIZES[base], p)
                    self.assertEqual(img.mode, "RGBA", p)
                    self.assertTrue(set(img.getchannel("A").getdata()) <= {0, 255}, p)
                    continue
                if kind == "sprites":
                    # D48: sprites/<set>/NAMEFR[FR].png, our SD prefix, RGBA
                    # with hard alpha and the grAb offsets inside the file
                    # (tests/test_weapon_sprites.py and, for the enemies,
                    # tests/test_legion_sprites.py (D54),
                    # test_rifleman_sprites.py and test_hound_sprites.py
                    # (D55), test_storm_sprites.py (D56) hold the offsets).
                    # R is 0 (one picture for every angle) or 1-8 (one lump
                    # per rotation). Since D55 a lump may be a Doom MIRRORED
                    # PAIR, eight characters carrying two rotations: the
                    # hound's SDHNA2A8 is frame A rotation 2 and, flipped,
                    # rotation 8. test_sprite_rotation_sets_are_whole below
                    # reads both halves and holds each frame's set together.
                    if p.parent.name == "effects" and p.stem[:4] in IWAD_OVERRIDE_SPRITES:
                        self.assertRegex(p.stem, IWAD_OVERRIDE_RE, p)
                    else:
                        self.assertRegex(p.stem, SPRITE_LUMP_RE, p)
                    self.assertEqual(img.mode, "RGBA", p)
                    alpha = set(img.getchannel("A").getdata())
                    self.assertTrue(alpha <= {0, 255},
                                    f"{p}: alpha must be hard 0/255, found {sorted(alpha)[:6]}")
                    continue
                if kind == "fonts":
                    # A folder font is fonts/<fontname>/<HEX>.png and the
                    # engine identifies the glyph by that hex name. Sizes vary
                    # per glyph by design, so only the naming and the folder
                    # are a contract here.
                    folder = p.relative_to(ASSETS_DIR).parts[1]
                    self.assertIn(folder, ("defsmallfont", "bigfont", "sdmenu"), p)
                    self.assertRegex(p.stem, r"^[0-9A-Fa-f]{4}$",
                                     f"{p}: a glyph is named by its codepoint in hex")
                    self.assertLessEqual(max(img.size), 32, p)
                    continue
                if kind == "graphics":
                    self.assertIn(p.stem, self.SHELL_SIZES,
                                  f"{p}: unexpected shell lump; the engine fixes these names")
                    self.assertEqual(img.size, self.SHELL_SIZES[p.stem], p)
                    self.assertIn(img.mode, ("P", "RGBA"), p)
                    if img.mode == "RGBA":
                        alpha = set(img.getchannel("A").getdata())
                        self.assertTrue(alpha <= {0, 255},
                                        f"{p}: alpha must be hard 0/255, found {sorted(alpha)[:6]}")
                    continue
                self.assertRegex(p.stem, LUMP_RE)
                if kind == "textures" and p.stem in MASKED_TEXTURES:
                    # D66: a masked mid-texture (the chain), RGBA, hard alpha.
                    self.assertEqual(img.mode, "RGBA", p)
                    alpha = set(img.getchannel("A").get_flattened_data())
                    self.assertEqual(alpha, {0, 255},
                                     f"{p}: a masked texture needs hard 0/255 alpha and both values")
                else:
                    self.assertEqual(img.mode, "P", p)
                if kind == "flats":
                    self.assertEqual(img.size, FLAT_SIZE, p)
                elif p.stem in SKY_TEXTURES:
                    # D113: MAPINFO's sky1 of MAP04-06, one 360-degree turn.
                    self.assertIn(img.size, SKY_SIZES, p)
                else:
                    self.assertIn(img.size, WALL_SIZES, p)

    def test_sprite_rotation_sets_are_whole(self):
        """A sprite frame in assets/sprites/ is rotation 0 alone or all of
        rotations 1-8, inside one set folder: a partial set would be filled
        by nothing and the engine would say "Missing sprite" as it turns. A
        mirrored pair (NAMEFRFR, the hound's SDHNA2A8 since D55) fills two
        slots, one per half, each in its own frame."""
        frames: dict[tuple[str, str], set[str]] = {}
        for p in self.pngs:
            rel = p.relative_to(ASSETS_DIR)
            if rel.parts[0] != "sprites":
                continue
            for frame, rotation in sprite_slots(p.stem):
                frames.setdefault((rel.parent.as_posix(), p.stem[:4] + frame), set()).add(rotation)
        for (folder, frame), rots in sorted(frames.items()):
            self.assertIn(rots, ({"0"}, set("12345678")), f"{folder}/{frame}: rotations {sorted(rots)}")

    def test_identical_to_work_source(self):
        if not WORK_ART_DIR.is_dir():
            self.skipTest("work/ not present (gitignored work-in-progress)")
        for p in self.pngs:
            sources = list(WORK_ART_DIR.rglob(p.name))
            if p.relative_to(ASSETS_DIR).parts[0] == "sprites":
                # A redone frame keeps its superseded render beside the new
                # one in an `old_*` folder (the Legion's old_death/, D54), for
                # the before/after sheet. Those never ship, so they are not
                # sources; the installed lump must match the current render.
                # The Doughboy's before_flag/ (gen_heavy.BEFORE_FLAG, the set
                # before D67's bigger flag, D70) is the same kind of folder.
                sources = [q for q in sources
                           if not any(part.startswith("old_") or part == "before_flag"
                                      for part in q.relative_to(WORK_ART_DIR).parts)]
            if p.relative_to(ASSETS_DIR).parts[0] == "fonts":
                # Every font variant generates the same codepoint filenames,
                # so a bare name matches A, B and C at once. What matters is
                # that the installed glyph is byte-identical to the same glyph
                # of exactly one generated variant - we do not pin which, so
                # the CEO can change his mind without editing a test.
                folder = p.relative_to(ASSETS_DIR).parts[1]
                same = [q for q in sources if q.parent.name == folder]
                self.assertTrue(same, f"{p}: no generated source under work/")
                self.assertTrue(any(q.read_bytes() == p.read_bytes() for q in same),
                                f"{p}: matches no generated variant")
                continue
            if not sources:
                # Some assets are RENAMED on the way in, because the generator
                # names by variant and the engine names by role: the shell
                # screens (TITLEPIC_A -> TITLEPIC, D18) and the switches
                # (SDSWT_B_off -> SDSW1B). The contract is still that nothing
                # reaches assets/ that the pipeline did not produce, so the
                # bytes must match some generated file even when the name does
                # not.
                blob = p.read_bytes()
                self.assertTrue(
                    any(q.read_bytes() == blob for q in WORK_ART_DIR.rglob("*.png")),
                    f"{p}: matches no file generated under work/")
                continue
            if len(sources) > 1 and (p.relative_to(ASSETS_DIR).parts[0] == "sprites"
                                     or p.parent.name == "statusbar"):
                # A sweep names every option as it would ship (the pickups,
                # work/art/pickups/<object>/<A|B>/SDCLA0.png, D63): the
                # installed lump must be byte-identical to exactly one of them.
                # D80: a sweep option may BE an earlier render (the campaign
                # sweep's Katyusha option A is the D51 draft,
                # work/art/weapons_2d/katyusha/), so the same bytes may sit in
                # two pipelines; what must stay unambiguous is the option:
                # never two siblings of one sweep (<object>/A and <object>/B).
                # M2e-i: the status bar sweep names its options the same way
                # (work/art/hud/bar/<A|B|C>/<en|ru>/STBAR.png, digits/<N2|N3>/,
                # face/<A|B|C>/ and face_gemini/).
                same = [q for q in sources if q.read_bytes() == p.read_bytes()]
                self.assertTrue(same, f"{p.name}: matches none of {sources}")
                self.assertEqual(len({q.parent.parent for q in same}), len(same),
                                 f"{p.name}: matches {len(same)} of {sources}")
                continue
            self.assertEqual(len(sources), 1, f"{p.name}: expected one source in work/, got {sources}")
            self.assertEqual(p.read_bytes(), sources[0].read_bytes(), f"{p} differs from {sources[0]}")


class MaskedTexturesTests(unittest.TestCase):
    """D66: every declared masked texture is installed under textures/."""

    def test_every_masked_texture_is_installed(self):
        walls = {p.stem for p in (ASSETS_DIR / "textures").rglob("*.png")}
        self.assertTrue(MASKED_TEXTURES)
        self.assertLessEqual(set(MASKED_TEXTURES), walls)

    def test_no_masked_flat(self):
        flats = {p.stem for p in (ASSETS_DIR / "flats").rglob("*.png")}
        self.assertFalse(set(MASKED_TEXTURES) & flats)


# Episode 2 «The Road to Moscow» (D104 drafts, approved 25/25 on 2026-10-22,
# D107): lump -> (folder under assets/, size, masked). Written out, not
# imported from the generators, so a renamed or resized piece shows up here.
EP2_INSTALLED = {
    # MAP04 railway (gen_railway.py)
    "SDTRAK1": ("flats/railway", (64, 64), False), "SDBLST1": ("flats/railway", (64, 64), False),
    "SDWAGN1": ("textures/railway", (128, 128), False), "SDTANK1": ("textures/railway", (128, 128), False),
    "SDARMR1": ("textures/railway", (128, 128), False), "SDARMR2": ("textures/railway", (64, 128), False),
    "SDSIGL1": ("textures/railway", (64, 128), False), "SDBRCK3": ("textures/railway", (64, 128), False),
    "SDGATE2": ("textures/railway", (128, 128), False),
    # MAP05 dam (gen_dam.py)
    "SDDAM1": ("textures/dam", (64, 128), False), "SDDAM2": ("textures/dam", (64, 128), False),
    "SDTURB1": ("textures/dam", (128, 128), False), "SDCTRL1": ("textures/dam", (128, 128), False),
    "SDSPIL1": ("textures/dam", (64, 128), False), "SDINSL1": ("textures/dam", (64, 128), True),
    "SDWATR1": ("flats/dam", (64, 64), False), "SDWATR2": ("flats/dam", (64, 64), False),
    "SDWATR3": ("flats/dam", (64, 64), False), "SDWATR4": ("flats/dam", (64, 64), False),
    "SDGRAT2": ("flats/dam", (64, 64), False),
    # MAP06 moscow (gen_moscow.py)
    "SDCOBL1": ("flats/moscow", (64, 64), False), "SDCOBL2": ("flats/moscow", (64, 64), False),
    "SDKREM1": ("textures/moscow", (64, 128), False), "SDKREM2": ("textures/moscow", (64, 128), True),
    "SDGUM1": ("textures/moscow", (128, 128), False), "SDTRIB1": ("textures/moscow", (64, 128), False),
    "SDBANR1": ("textures/moscow", (64, 128), False), "SDSPAS1": ("textures/moscow", (64, 128), False),
}
# Episode 2, round 2 (D112 drafts, installed 2026-10-22 under D113's standing
# approval, PM gate 2026-10-22): the same three set folders plus textures/sky.
EP2B_INSTALLED = {
    # the two night skies, MAPINFO sky1 (1024x128, SKY_SIZES)
    "SDSKY1": ("textures/sky", (1024, 128), False), "SDSKY2": ("textures/sky", (1024, 128), False),
    # MAP04 railway
    "SDWROF1": ("flats/railway", (64, 64), False), "SDGOND1": ("flats/railway", (64, 64), False),
    "SDLEVR1": ("flats/railway", (64, 64), False),
    "SDCAB1": ("textures/railway", (128, 128), False), "SDCAB2": ("textures/railway", (64, 128), False),
    "SDSBOX1": ("textures/railway", (64, 64), False), "SDLEVR2": ("textures/railway", (64, 64), False),
    "SDRHDR1": ("textures/railway", (128, 128), False), "SDSTAN1": ("textures/railway", (256, 64), False),
    # MAP05 dam
    "SDGRIL1": ("textures/dam", (64, 128), True), "SDDOORB": ("textures/dam", (128, 128), False),
    "SDHVLT1": ("textures/dam", (64, 128), True),
    # MAP06 moscow
    "SDCLOK1": ("textures/moscow", (128, 128), False), "SDRUBY1": ("textures/moscow", (128, 128), True),
    "SDGUMS1": ("textures/moscow", (64, 128), False), "SDGUMS2": ("textures/moscow", (64, 128), False),
    "SDGUMS3": ("textures/moscow", (64, 128), False), "SDGUMR1": ("flats/moscow", (64, 64), False),
    "SDMUSE1": ("textures/moscow", (64, 128), False), "SDFLAG3": ("textures/moscow", (64, 128), False),
    "SDFLAG4": ("textures/moscow", (64, 128), False),
}
# Episode 3's three skies (gen_episode3_skies.py, installed 2026-10-22 under
# D113's standing approval): MAPINFO sky1 of MAP07-09, in the same
# textures/sky/ as round 2's two. Episode2InstallTests leaves them out.
EP3_SKIES_INSTALLED = {
    "SDSKY3": ("textures/sky", (1024, 128), False), "SDSKY4": ("textures/sky", (1024, 128), False),
    "SDSKY5": ("textures/sky", (1024, 128), False),
}
# Episode 1's two skies (gen_episode1_skies.py, installed 2026-10-22 under
# D113's standing approval): MAPINFO sky1 of MAP01 and RANGE (SDSKY6) and
# MAP03 (SDSKY7), in the same textures/sky/. Episode2InstallTests leaves them out.
EP1_SKIES_INSTALLED = {
    "SDSKY6": ("textures/sky", (1024, 128), False), "SDSKY7": ("textures/sky", (1024, 128), False),
}
EP2_FOLDERS = ("textures/railway", "textures/dam", "textures/moscow", "textures/sky",
               "flats/railway", "flats/dam", "flats/moscow")


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class Episode2InstallTests(unittest.TestCase):
    """D107: the 25 approved pieces, 28 lumps, in their set folders; D113:
    round 2's 21 pieces, 23 lumps, in the same folders and textures/sky/."""

    def installed(self) -> dict[str, Path]:
        out = {}
        for folder in EP2_FOLDERS:
            for p in sorted((ASSETS_DIR / folder).glob("*.png")):
                if p.stem in EP3_SKIES_INSTALLED or p.stem in EP1_SKIES_INSTALLED:
                    continue
                self.assertNotIn(p.stem, out, f"{p.stem} installed twice")
                out[p.stem] = p
        return out

    def table(self) -> dict:
        return {**EP2_INSTALLED, **EP2B_INSTALLED}

    def test_exactly_the_approved_lumps(self):
        self.assertEqual(28, len(EP2_INSTALLED))
        self.assertEqual(23, len(EP2B_INSTALLED))
        self.assertFalse(set(EP2_INSTALLED) & set(EP2B_INSTALLED))
        self.assertEqual(set(self.table()), set(self.installed()))

    def test_folder_size_mode_and_name(self):
        from PIL import Image
        for lump, p in self.installed().items():
            folder, size, masked = self.table()[lump]
            self.assertEqual(folder, p.parent.relative_to(ASSETS_DIR).as_posix(), lump)
            self.assertRegex(lump, LUMP_RE)
            self.assertLessEqual(len(lump), 8)
            with Image.open(p) as img:
                self.assertEqual(size, img.size, lump)
                self.assertEqual("RGBA" if masked else "P", img.mode, lump)

    def test_masked_set_agrees_with_check_pk3(self):
        ep2_masked = {lump for lump, (_f, _s, masked) in EP2_INSTALLED.items() if masked}
        self.assertEqual({"SDKREM2", "SDINSL1"}, ep2_masked)
        self.assertLessEqual(ep2_masked, set(MASKED_TEXTURES))
        self.assertFalse({lump for lump, (folder, _s, _m) in EP2_INSTALLED.items()
                          if folder.startswith("flats/")} & set(MASKED_TEXTURES))
        ep2b_masked = {lump for lump, (_f, _s, masked) in EP2B_INSTALLED.items() if masked}
        self.assertEqual({"SDGRIL1", "SDHVLT1", "SDRUBY1"}, ep2b_masked)
        self.assertLessEqual(ep2b_masked, set(MASKED_TEXTURES))

    def test_skies_agree_with_check_pk3(self):
        skies = {lump for lump, (folder, _s, _m) in EP2B_INSTALLED.items() if folder == "textures/sky"}
        self.assertEqual({"SDSKY1", "SDSKY2"}, skies)
        self.assertEqual(skies | set(EP3_SKIES_INSTALLED) | set(EP1_SKIES_INSTALLED), set(SKY_TEXTURES))

    def test_episode3_skies_installed(self):
        from PIL import Image
        for lump, (folder, size, _m) in {**EP3_SKIES_INSTALLED, **EP1_SKIES_INSTALLED}.items():
            p = ASSETS_DIR / folder / f"{lump}.png"
            self.assertTrue(p.is_file(), p)
            with Image.open(p) as img:
                self.assertEqual(size, img.size, lump)
                self.assertEqual("P", img.mode, lump)
            self.assertEqual(1, len(list(ASSETS_DIR.rglob(f"{lump}.png"))), lump)

    def test_no_name_clash_with_any_other_installed_lump(self):
        ours = {p.resolve() for p in self.installed().values()}
        others = {p.stem.upper() for p in ASSETS_DIR.rglob("*.png") if p.resolve() not in ours}
        self.assertFalse(set(self.table()) & others)


# Episode 3 «The Portal» (D112 drafts, installed 2026-10-22 under D113's
# standing approval, PM gate 2026-10-22): lump -> (folder, size, masked).
EP3_INSTALLED = {
    # MAP07 arctic (gen_arctic.py)
    "SDSNOW1": ("flats/arctic", (64, 64), False), "SDICE1": ("flats/arctic", (64, 64), False),
    "SDICE2": ("textures/arctic", (64, 128), False), "SDRADM1": ("textures/arctic", (128, 128), False),
    "SDHUT1": ("textures/arctic", (64, 128), False),
    **{f"SDRADR{i}": ("textures/arctic", (128, 128), False) for i in range(1, 5)},
    "SDHERM1": ("textures/arctic", (128, 128), False),
    "SDRWY1": ("flats/arctic", (64, 64), False), "SDRWY2": ("flats/arctic", (64, 64), False),
    # MAP08 naval (gen_naval.py)
    "SDHULL1": ("textures/naval", (128, 128), False), "SDHULL2": ("textures/naval", (128, 128), False),
    "SDRUBR1": ("flats/naval", (64, 64), False), "SDRUBR2": ("flats/naval", (64, 64), False),
    "SDROCK1": ("textures/naval", (64, 128), False), "SDROCK2": ("flats/naval", (64, 64), False),
    "SDBULK1": ("textures/naval", (128, 128), False), "SDNAVC1": ("textures/naval", (128, 128), False),
    "SDCONT1": ("textures/naval", (128, 128), False), "SDCRAN1": ("textures/naval", (64, 128), True),
    "SDPIER1": ("flats/naval", (64, 64), False),
    # MAP09 taiga (gen_taiga.py)
    "SDBARK1": ("textures/taiga", (64, 128), False), "SDBARK2": ("textures/taiga", (64, 128), False),
    "SDLOGW1": ("textures/taiga", (128, 128), False), "SDPEAT1": ("flats/taiga", (64, 64), False),
    "SDBURN1": ("flats/taiga", (64, 64), False), "SDMOSS1": ("flats/taiga", (64, 64), False),
    "SDALNM1": ("textures/taiga", (128, 128), False),
    **{f"SDACID{i}": ("flats/taiga", (64, 64), False) for i in range(1, 5)},
    "SDGLYP1": ("textures/taiga", (64, 128), False), "SDPRTE1": ("textures/taiga", (64, 128), False),
}
EP3_FOLDERS = ("textures/arctic", "textures/naval", "textures/taiga",
               "flats/arctic", "flats/naval", "flats/taiga")


@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class Episode3InstallTests(unittest.TestCase):
    """D113: Episode 3's 30 pieces, 36 lumps, in their set folders."""

    def installed(self) -> dict[str, Path]:
        out = {}
        for folder in EP3_FOLDERS:
            for p in sorted((ASSETS_DIR / folder).glob("*.png")):
                self.assertNotIn(p.stem, out, f"{p.stem} installed twice")
                out[p.stem] = p
        return out

    def test_exactly_the_approved_lumps(self):
        self.assertEqual(36, len(EP3_INSTALLED))
        self.assertEqual(set(EP3_INSTALLED), set(self.installed()))

    def test_folder_size_mode_and_name(self):
        from PIL import Image
        for lump, p in self.installed().items():
            folder, size, masked = EP3_INSTALLED[lump]
            self.assertEqual(folder, p.parent.relative_to(ASSETS_DIR).as_posix(), lump)
            self.assertRegex(lump, LUMP_RE)
            self.assertLessEqual(len(lump), 8)
            with Image.open(p) as img:
                self.assertEqual(size, img.size, lump)
                self.assertEqual("RGBA" if masked else "P", img.mode, lump)

    def test_masked_set_agrees_with_check_pk3(self):
        masked = {lump for lump, (_f, _s, m) in EP3_INSTALLED.items() if m}
        self.assertEqual({"SDCRAN1"}, masked)
        self.assertLessEqual(masked, set(MASKED_TEXTURES))

    def test_no_name_clash_with_any_other_installed_lump(self):
        ours = {p.resolve() for p in self.installed().values()}
        others = {p.stem.upper() for p in ASSETS_DIR.rglob("*.png") if p.resolve() not in ours}
        self.assertFalse(set(EP3_INSTALLED) & others)


class SpriteNameTests(unittest.TestCase):
    """The two sprite checks above accept Doom's mirrored pairs (D55)."""

    def test_names(self):
        for good in ("SDHNA1", "SDHNA2A8", "SDHNH4H6", "SDHNI0", "SDLTA8"):
            self.assertRegex(good, SPRITE_LUMP_RE)
        for bad in ("SDHNA2A", "SDHNA2A0", "SDHNA9", "POSSA1", "SDHNA2A8X"):
            self.assertNotRegex(bad, SPRITE_LUMP_RE)

    def test_slots(self):
        self.assertEqual(sprite_slots("SDHNA1"), [("A", "1")])
        self.assertEqual(sprite_slots("SDHNA2A8"), [("A", "2"), ("A", "8")])
        cover = {r for stem in ("SDHNA1", "SDHNA2A8", "SDHNA3A7", "SDHNA4A6", "SDHNA5")
                 for _, r in sprite_slots(stem)}
        self.assertEqual(cover, set("12345678"))


if __name__ == "__main__":
    unittest.main()
