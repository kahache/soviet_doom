"""Tests for src/lumps/ANIMDEFS: the switch pairs of MOD-SPEC 4.3 (debt T16)
and the Tankograd animations (N6c, D66).

The engine pass (pressing each switch, watching the molten metal and the
portal move in GZDoom) is the PM's (D26). What can be proved without the
engine is proved here: the lump ships at the PK3 root, every approved OFF
face (SDSW1x) has exactly one `switch` line, every line pairs SDSW1x with its
own SDSW2x, and every name is an approved asset; the molten-metal flat and
the portal texture each have one animation that names its four installed
frames in order at their rate (8 tics; the radar 12, D113), a flat as `flat` and a wall as `texture`.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"
ANIMDEFS = SRC_DIR / "lumps" / "ANIMDEFS"
SWITCH_ASSETS = ASSETS_DIR / "textures" / "soviet_base"
FACTORY_WALLS = ASSETS_DIR / "textures" / "factory"
FACTORY_FLATS = ASSETS_DIR / "flats" / "factory"
DAM_FLATS = ASSETS_DIR / "flats" / "dam"          # Episode 2, MAP05 (D107)
ARCTIC_WALLS = ASSETS_DIR / "textures" / "arctic"  # Episode 3, MAP07 (D113)
TAIGA_FLATS = ASSETS_DIR / "flats" / "taiga"       # Episode 3, MAP09 (D113)
sys.path.insert(0, str(TOOLS_DIR))

from check_pk3 import animdefs_anim_textures, animdefs_switch_textures  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

# MOD-SPEC 4.3: SDSW + state digit (1 off, 2 on) + variant letter.
RE_OFF = re.compile(r"^SDSW1([A-Z])$")
RE_SWITCH_ASSET = re.compile(r"^SDSW([12])([A-Z])\.png$")
# The exact form the engine uses for its own Doom switches (gzdoom.pk3 ->
# animdefs.txt, GZDoom g4.14.2): game filter, OFF, `on pic` ON, `tics 0`.
RE_SWITCH_LINE = re.compile(r"^switch\s+doom\s+1\s+(\S+)\s+on\s+pic\s+(\S+)\s+tics\s+0$")
# Animations (N6c): the form FTextureAnimator::ParseAnim reads (GZDoom
# g4.14.2, src/gamedata/textures/animations.cpp): a header `flat NAME` or
# `texture NAME`, then one `pic FRAME tics N` line per frame.
RE_ANIM_HEAD = re.compile(r"^(flat|texture)\s+(\S+)$")
RE_ANIM_PIC = re.compile(r"^pic\s+(\S+)\s+tics\s+(\d+)$")
ANIM_TICS = 8                      # art-director's rate, 8/35 s a frame (D66)
RADAR_TICS = 12                    # D113: the radar sweep, 90 degrees a frame, a 1.4 s turn
ANIM_FRAMES = 4
# First frame -> (keyword, folder, tics): the molten metal is a floor, the portal a wall.
ANIMATIONS = {
    "SDMOLT1": ("flat", FACTORY_FLATS, ANIM_TICS),
    "SDPORT1": ("texture", FACTORY_WALLS, ANIM_TICS),
    "SDWATR1": ("flat", DAM_FLATS, ANIM_TICS),      # the Volga's water, like Doom's FWATER (D107)
    "SDRADR1": ("texture", ARCTIC_WALLS, RADAR_TICS),  # the radar console, MAP07 (D113)
    "SDACID1": ("flat", TAIGA_FLATS, ANIM_TICS),    # the invaders' acid, as the water (D113)
}


def switch_lines() -> list[str]:
    """Non-comment lines of the lump that start with `switch`."""
    out = []
    for raw in ANIMDEFS.read_text(encoding="ascii").splitlines():
        line = raw.split("//", 1)[0].strip()
        if line.lower().startswith("switch"):
            out.append(line)
    return out


def animations() -> dict[str, tuple[str, list[tuple[str, int]]]]:
    """{first frame: (keyword, [(frame, tics), ...])} for every flat/texture
    animation of the lump, read line by line in the project's own layout."""
    out: dict[str, tuple[str, list[tuple[str, int]]]] = {}
    current = None
    for raw in ANIMDEFS.read_text(encoding="ascii").splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        head = RE_ANIM_HEAD.match(line)
        pic = RE_ANIM_PIC.match(line)
        if head:
            current = head.group(2)
            if current in out:
                raise AssertionError(f"{current} is animated twice")
            out[current] = (head.group(1), [])
        elif pic and current is not None:
            out[current][1].append((pic.group(1), int(pic.group(2))))
        else:
            current = None
    return out


def approved_variants() -> dict[str, set[str]]:
    """{'1': {'A', ...}, '2': {...}} from assets/textures/soviet_base/."""
    found: dict[str, set[str]] = {"1": set(), "2": set()}
    for p in SWITCH_ASSETS.iterdir():
        m = RE_SWITCH_ASSET.match(p.name)
        if m:
            found[m.group(1)].add(m.group(2))
    return found


class AnimdefsSourceTest(unittest.TestCase):
    def test_lump_exists_and_is_ascii(self):
        self.assertTrue(ANIMDEFS.is_file(), "src/lumps/ANIMDEFS is missing (T16)")
        ANIMDEFS.read_bytes().decode("ascii")   # raises on non-ASCII

    def test_every_line_has_the_engine_form(self):
        lines = switch_lines()
        self.assertTrue(lines)
        for line in lines:
            self.assertRegex(line, RE_SWITCH_LINE)

    def test_one_line_per_approved_pair(self):
        variants = approved_variants()
        self.assertEqual(variants["1"], variants["2"], "an approved OFF face has no ON face, or vice versa")
        self.assertTrue(variants["1"], "no SDSW1x/SDSW2x in assets/")
        offs = [RE_SWITCH_LINE.match(line).group(1) for line in switch_lines()]
        self.assertEqual(sorted(offs), sorted(set(offs)), "an OFF texture has two switch lines")
        self.assertEqual({f"SDSW1{v}" for v in variants["1"]}, set(offs))

    def test_each_off_pairs_with_its_own_on(self):
        for line in switch_lines():
            off, on = RE_SWITCH_LINE.match(line).groups()
            m = RE_OFF.match(off)
            self.assertIsNotNone(m, f"{off} is not an OFF face (SDSW1x)")
            self.assertEqual(f"SDSW2{m.group(1)}", on, f"{off} must flip to its own ON face")

    def test_every_name_is_an_approved_asset(self):
        names = {name for name, _line, _role in animdefs_switch_textures(ANIMDEFS.read_text(encoding="ascii"))}
        self.assertEqual(8, len(names))
        for name in names:
            self.assertTrue((SWITCH_ASSETS / f"{name}.png").is_file(), f"{name} is not in {SWITCH_ASSETS}")


class AnimdefsAnimationTest(unittest.TestCase):
    """N6c: SDMOLT1-4 (flat) and SDPORT1-4 (texture); D107: SDWATR1-4 (flat);
    D113: SDRADR1-4 (texture, 12 tics) and SDACID1-4 (flat). Four frames
    each, at 8 tics but for the radar."""

    def test_exactly_the_five_animations(self):
        self.assertEqual(set(ANIMATIONS), set(animations()))

    def test_keyword_matches_the_kind_of_surface(self):
        # `flat` looks its names up as flats and `texture` as walls
        # (ParseAnim); whether the wrong keyword falls back is NOT VERIFIED,
        # so it is held as an error here.
        for first, (keyword, folder, _tics) in ANIMATIONS.items():
            self.assertEqual(keyword, animations()[first][0], first)
            self.assertTrue((folder / f"{first}.png").is_file(), f"{first} is not in {folder}")

    def test_frames_in_order_at_their_rate(self):
        for first, (_keyword, frames) in animations().items():
            stem = first[:-1]
            self.assertEqual([f"{stem}{i}" for i in range(1, ANIM_FRAMES + 1)],
                             [name for name, _tics in frames], first)
            self.assertEqual({ANIMATIONS[first][2]}, {tics for _name, tics in frames}, first)

    def test_every_frame_is_an_installed_asset(self):
        for first, (_keyword, folder, _tics) in ANIMATIONS.items():
            for name, _tics in animations()[first][1]:
                self.assertTrue((folder / f"{name}.png").is_file(), f"{name} is not in {folder}")

    def test_validator_reads_the_same_frames(self):
        # check_pk3's token parser and this file's line reader agree.
        names = {name for name, _line, _role in animdefs_anim_textures(ANIMDEFS.read_text(encoding="ascii"))}
        self.assertEqual({f"{first[:-1]}{i}" for first in ANIMATIONS for i in range(1, ANIM_FRAMES + 1)}, names)

    def test_switch_parser_ignores_the_animations(self):
        names = {name for name, _line, _role in animdefs_switch_textures(ANIMDEFS.read_text(encoding="ascii"))}
        self.assertFalse(names & set(ANIMATIONS))


class AnimdefsPackedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, out, TOOLS_DIR, ASSETS_DIR)
        with zipfile.ZipFile(out) as zf:
            cls.names = zf.namelist()
            cls.animdefs = zf.read("ANIMDEFS") if "ANIMDEFS" in cls.names else None

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_lump_is_at_the_pk3_root_unchanged(self):
        self.assertIn("ANIMDEFS", self.names)
        self.assertEqual(ANIMDEFS.read_bytes(), self.animdefs)

    def test_every_switch_texture_is_packed(self):
        packed = {Path(n).stem.upper() for n in self.names if n.startswith("textures/")}
        for name, line, role in animdefs_switch_textures(self.animdefs.decode("ascii")):
            self.assertIn(name, packed, f"ANIMDEFS:{line} {role} texture {name} is not in textures/")

    def test_every_animation_frame_is_packed_in_its_namespace(self):
        folder = {"flat": "flats/", "texture": "textures/"}
        for name, line, role in animdefs_anim_textures(self.animdefs.decode("ascii")):
            packed = {Path(n).stem.upper() for n in self.names if n.startswith(folder[role])}
            self.assertIn(name, packed, f"ANIMDEFS:{line} {role} frame {name} is not in {folder[role]}")


if __name__ == "__main__":
    unittest.main()
