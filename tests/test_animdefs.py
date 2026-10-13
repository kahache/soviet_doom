"""Tests for src/lumps/ANIMDEFS: the switch pairs of MOD-SPEC 4.3 (debt T16).

The engine pass (pressing each switch in GZDoom) is the PM's (D26). What can
be proved without the engine is proved here: the lump ships at the PK3 root,
every approved OFF face (SDSW1x) has exactly one `switch` line, every line
pairs SDSW1x with its own SDSW2x, and every name is an approved asset.

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
sys.path.insert(0, str(TOOLS_DIR))

from check_pk3 import animdefs_switch_textures  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

# MOD-SPEC 4.3: SDSW + state digit (1 off, 2 on) + variant letter.
RE_OFF = re.compile(r"^SDSW1([A-Z])$")
RE_SWITCH_ASSET = re.compile(r"^SDSW([12])([A-Z])\.png$")
# The exact form the engine uses for its own Doom switches (gzdoom.pk3 ->
# animdefs.txt, GZDoom g4.14.2): game filter, OFF, `on pic` ON, `tics 0`.
RE_SWITCH_LINE = re.compile(r"^switch\s+doom\s+1\s+(\S+)\s+on\s+pic\s+(\S+)\s+tics\s+0$")


def switch_lines() -> list[str]:
    """Non-comment lines of the lump that start with `switch`."""
    out = []
    for raw in ANIMDEFS.read_text(encoding="ascii").splitlines():
        line = raw.split("//", 1)[0].strip()
        if line.lower().startswith("switch"):
            out.append(line)
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


if __name__ == "__main__":
    unittest.main()
