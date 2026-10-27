"""2026-10-24: the RGD-5 wears its own sprites (it wore borrowed ones, D116).

The project lead's Gemini images of the throw (`work/art/reference/
gemini_rgd5_A/B/C.jfif`; gitignored, never shipped, D77) processed by
`tools/art/gemini_frames.py rgd5` into `work/art/weapons/hand_G/rgd5/`: held
SDRG A ready, B the pin out and the arm back (Gemini's third hand cut away),
C the release, D the follow-through (C without the grenade, lower). The
world sprites by `tools/art/gen_rgd5_pickups.py` from the Gemini image of
the grenade lying: SDRJ A one grenade (and the HUD icon), SDRN A in flight,
SDRQ A the pouch and SDRZ A the crate (both on the pickup rig with that
grenade in them). The eight ship from `assets/sprites/rgd5/` under the
names the three files' headers reserved (MOD-SPEC 6.12). What is checked:

  behaviour  each class's States block is the one D116 put in the mod, line
             for line (label, frame letters, tics, action, flow), with only
             the names changed: not one tic moves (33 a throw)
  sprite     the states name only the RGD-5's own sprites (and the PG-7V's
             burst SDPX, which stays); every frame used has its lump and
             every lump is used (SDRJ A0 also as the icon)
  files      assets/sprites/rgd5/ holds exactly the eight lumps, each with
             its grAb before the image data and the canvas the build gave;
             where work/ exists each is byte-identical to the built set;
             where the Gemini sources and the tools exist a fresh build
             reproduces them (slow, skipped at verify.py fast)
  screen     with Pillow: A 56 px above the status bar like every weapon's;
             RGBA with hard alpha, all eight in palette v2
  package    the built PK3 carries them flat as sprites/<NAME>.png, no
             Gemini source in it, and check_pk3 passes sprites and licences
  licences   each lump has one row, own work; every row names Gemini and
             says the source stays home, the pouch's and crate's the rig

Stdlib only, but for the screen and palette checks, which need Pillow.
"""

from __future__ import annotations

import os
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
WEAPONS = SRC_DIR / "zscript" / "weapons"
RGD5_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "rgd5"
WORK_SET = PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G" / "rgd5"
REFERENCES = [PROJECT_ROOT / "work" / "art" / "reference" / f"gemini_rgd5_{k}.jfif" for k in ("A", "B", "C", "pickup")]
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_panzermensch_sprites import (  # noqa: E402  (one PNG/ZScript reader, not two)
    PNG_SIGNATURE, read_grab, states_block, strip_comments)
import _p4_mod as p4  # noqa: E402

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy  # noqa: F401
    import gemini_frames as gf
    import gen_rgd5_pickups as rp
    HAVE_TOOLS = HAVE_PIL and "rgd5" in gf.WEAPONS
except ImportError:   # CI's stdlib-only interpreter, or the tools not merged in yet
    HAVE_TOOLS = False
SLOW_SKIPPED = os.environ.get("SD_SKIP_SLOW_ART") == "1"   # verify.py fast

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
# D116's borrowed names -> the RGD-5's, per class (each header's swap).
RENAMED = {"SD_Rgd5": {"SDAX": "SDRG", "SDHB": "SDRQ"}, "SD_Rgd5Ammo": {"SDHB": "SDRJ"},
           "SD_Rgd5Box": {"SDRB": "SDRZ"}, "SD_Rgd5Grenade": {"SDHB": "SDRN"}}
FILES = {"SD_Rgd5": "rgd5.zs", "SD_Rgd5Ammo": "rgd5_ammo.zs", "SD_Rgd5Box": "rgd5_ammo.zs",
         "SD_Rgd5Grenade": "rgd5_grenade.zs"}
EXPECTED_LUMPS = {"SDRGA0", "SDRGB0", "SDRGC0", "SDRGD0", "SDRJA0", "SDRNA0", "SDRQA0", "SDRZA0"}
HELD_LUMPS = {"SDRGA0", "SDRGB0", "SDRGC0", "SDRGD0"}
RIG_LUMPS = {"SDRQA0", "SDRZA0"}
ICON = "SDRJA0"

# (canvas width, height, grAb left, top) per lump, as gemini_frames.build and
# gen_rgd5_pickups drew them (2026-10-24). Held frames hang from negative
# offsets; the world sprites stand on their lowest pixel, centred.
CANVASES = {
    "SDRGA0": (99, 100, -200, -96),
    "SDRGB0": (393, 132, -39, -64),
    "SDRGC0": (101, 112, -198, -84),
    "SDRGD0": (101, 86, -198, -118),
    "SDRJA0": (16, 9, 8, 9),
    "SDRNA0": (13, 9, 6, 9),
    "SDRQA0": (24, 23, 12, 23),
    "SDRZA0": (32, 22, 16, 22),
}
VIEW_H = 168                            # the 3D view above the 32-px status bar
WEAPONTOP = 32                          # psprite y at rest (Doom's p_pspr.h)
BAR_LIFT = 16                           # the view is centred on 168 rows, not 200
ABOVE_BAR = {"SDRGA0": 56, "SDRGB0": 88, "SDRGC0": 68, "SDRGD0": 34}
ARSENAL_TOP = 56                        # every weapon's ready frame (x1.6 CHGGA0, D78)

# The States blocks as D116 put them in the mod (read from the v3 branch on
# 2026-10-24, before the swap), on the borrowed sprites.
BEFORE = {
    "SD_Rgd5": (
        ("Ready", ":", "", 0, ""), ("Ready", "SDAX", "A", 1, "A_WeaponReady"), ("Ready", "->", "Loop", 0, ""),
        ("Deselect", ":", "", 0, ""), ("Deselect", "SDAX", "A", 1, "A_Lower"), ("Deselect", "->", "Loop", 0, ""),
        ("Select", ":", "", 0, ""), ("Select", "SDAX", "A", 1, "A_Raise"), ("Select", "->", "Loop", 0, ""),
        ("Fire", ":", "", 0, ""),
        ("Fire", "SDAX", "B", 8, 'A_StartSound("sd/weapon/rgd5/pin", CHAN_WEAPON)'),
        ("Fire", "SDAX", "C", 3, 'A_StartSound("sd/weapon/rgd5/throw", CHAN_WEAPON)'),
        ("Fire", "SDAX", "C", 2, "A_SD_ThrowRgd5"), ("Fire", "SDAX", "D", 8, ""),
        ("Fire", "SDAX", "A", 12, "A_CheckReload"), ("Fire", "->", "Goto Ready", 0, ""),
        ("Spawn", ":", "", 0, ""), ("Spawn", "SDHB", "A", -1, ""), ("Spawn", "->", "Stop", 0, "")),
    "SD_Rgd5Ammo": (("Spawn", ":", "", 0, ""), ("Spawn", "SDHB", "A", -1, ""), ("Spawn", "->", "Stop", 0, "")),
    "SD_Rgd5Box": (("Spawn", ":", "", 0, ""), ("Spawn", "SDRB", "A", -1, ""), ("Spawn", "->", "Stop", 0, "")),
    "SD_Rgd5Grenade": (
        ("Spawn", ":", "", 0, ""), ("Spawn", "SDHB", "A", 1, "A_SD_BurnFuse"), ("Spawn", "->", "Loop", 0, ""),
        ("Death", ":", "", 0, ""), ("Death", "SDHB", "A", 1, "A_SD_BurnFuse"), ("Death", "->", "Loop", 0, ""),
        ("Detonate", ":", "", 0, ""), ("Detonate", "SDPX", "A", 8, "Bright A_SD_Detonate"),
        ("Detonate", "SDPX", "B", 6, "Bright"), ("Detonate", "SDPX", "C", 4, "Bright"),
        ("Detonate", "->", "Stop", 0, "")),
}


def states(cls: str) -> list[tuple]:
    """Every line of cls's States block, labels included, in order."""
    _, body = p4.class_blocks((WEAPONS / FILES[cls]).read_text(encoding="utf-8"))[cls]
    block = states_block(strip_comments("class X {" + body + "}"))
    label, rows = None, []
    for line in block.splitlines():
        if not line.strip():
            continue
        if (m := RE_LABEL.match(line)):
            label = m.group(1)
            rows.append((label, ":", "", 0, ""))
        elif (m := RE_STATE.match(line)):
            rows.append((label, m.group(1), m.group(2), int(m.group(3)), m.group(4)))
        elif (m := RE_FLOW.match(line)):
            rows.append((label, "->", " ".join(m.group(1).split()), 0, ""))
        else:
            raise AssertionError(f"{cls}: unparsed States line {line!r}")
    return rows


def installed() -> list[Path]:
    return sorted(RGD5_SPRITES.glob("*.png")) if RGD5_SPRITES.is_dir() else []


def lump(name: str) -> Path:
    return RGD5_SPRITES / f"{name}.png"


def above_bar(path: Path) -> int:
    """Px from the topmost opaque pixel down to the status bar (bar on)."""
    left, top = read_grab(path.read_bytes())
    with Image.open(path) as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    return VIEW_H - (WEAPONTOP - top - BAR_LIFT + box[1])


class BehaviourTests(unittest.TestCase):
    def test_states_are_d116s_but_for_the_names(self):
        for cls, before in BEFORE.items():
            with self.subTest(cls=cls):
                renamed = [(l, RENAMED[cls].get(s, s), f, t, r) for l, s, f, t, r in before]
                self.assertEqual(states(cls), renamed)

    def test_33_tics_a_throw(self):
        fire = [r for r in states("SD_Rgd5") if r[0] == "Fire" and r[1] not in (":", "->")]
        self.assertEqual(sum(r[3] for r in fire), 33)


class SpriteTests(unittest.TestCase):
    def test_states_name_only_the_rgd5s(self):
        used = {r[1] for cls in BEFORE for r in states(cls) if r[1] not in (":", "->")}
        self.assertEqual(used, {"SDRG", "SDRQ", "SDRJ", "SDRZ", "SDRN", "SDPX"})

    def test_every_frame_used_is_installed_and_every_lump_used(self):
        used = {f"{r[1]}{r[2]}0" for cls in BEFORE for r in states(cls) if r[1] not in (":", "->", "SDPX")}
        self.assertEqual(used | {ICON}, EXPECTED_LUMPS)
        for name in used:
            self.assertTrue(lump(name).is_file(), name)


class FileTests(unittest.TestCase):
    def test_exactly_the_eight_lumps(self):
        self.assertTrue(RGD5_SPRITES.is_dir())
        self.assertEqual(sorted(p.name for p in RGD5_SPRITES.iterdir()),
                         sorted(f"{n}.png" for n in EXPECTED_LUMPS), "nothing but lumps")

    def test_every_sprite_carries_its_canvas_and_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height) + tuple(grab), CANVASES[p.stem], p.name)

    @unittest.skipUnless(WORK_SET.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_built_set(self):
        for p in installed():
            source = WORK_SET / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipIf(SLOW_SKIPPED, "renders: slow tier only")
    @unittest.skipUnless(HAVE_TOOLS and all(r.is_file() for r in REFERENCES),
                         "the Gemini sources are not here (gitignored, D77), or numpy/Pillow or the tools are missing")
    def test_a_fresh_build_reproduces_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = gf.build(gf.WEAPONS["rgd5"], out_dir=Path(tmp))
            for name in HELD_LUMPS:
                self.assertEqual(lump(name).read_bytes(), res["frames"][name]["path"].read_bytes(), name)
            self.assertEqual(rp.main(["--out", tmp]), 0)
            for name in EXPECTED_LUMPS - HELD_LUMPS:
                self.assertEqual(lump(name).read_bytes(), (Path(tmp) / f"{name}.png").read_bytes(), name)


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class ScreenTests(unittest.TestCase):
    def test_they_stand_where_the_build_put_them(self):
        for name, above in ABOVE_BAR.items():
            self.assertEqual(above_bar(lump(name)), above, name)

    def test_the_ready_frame_is_at_the_arsenals_height(self):
        self.assertEqual(above_bar(lump("SDRGA0")), ARSENAL_TOP)

    def test_rgba_hard_alpha_palette_v2(self):
        v2 = set(palette_mod.colours(2))
        for p in installed():
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", p.name)
                raw = img.tobytes()
            self.assertLessEqual(set(raw[3::4]), {0, 255}, p.name)
            used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
            self.assertFalse(used - v2, p.name)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_flat_under_sprites(self):
        with zipfile.ZipFile(self.pk3) as zf:
            names = set(zf.namelist())
            for p in installed():
                self.assertIn(f"sprites/{p.name}", names)
                self.assertEqual(zf.read(f"sprites/{p.name}"), p.read_bytes())
            self.assertFalse([n for n in names if n.startswith("sprites/rgd5")], "the set folder is dropped")
            self.assertFalse([n for n in names if "gemini" in n.lower()], "no source image ships (D77)")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


class LicenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))

    def row(self, name: str):
        found = [r for r in self.rows if r.covers(f"sprites/{name}.png")]
        self.assertEqual(len(found), 1, f"{name}: {len(found)} rows in docs/art/LICENSES.md")
        return found[0]

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        self.assertEqual([], sorted(n for n in EXPECTED_LUMPS if n not in declared))

    def test_the_rows_say_where_each_comes_from(self):
        for name in sorted(EXPECTED_LUMPS):
            row = self.row(name)
            self.assertTrue(row.own_work, name)
            self.assertEqual(row.required, licences.OWN_WORK_CREDITS, name)
            self.assertNotIn("Freedoom", row.origin, name)
            self.assertIn("generated by the project lead with Google Gemini", row.origin, name)
            self.assertIn("not distributed", row.origin, name)
        for name in sorted(RIG_LUMPS):
            self.assertIn("gen_weapon.py", self.row(name).origin, name)


if __name__ == "__main__":
    unittest.main()
