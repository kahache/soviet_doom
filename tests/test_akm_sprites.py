"""2026-10-24: the AKM wears its own sprites (it wore the PPSh-41's, D116).

The project lead's ONE Gemini image of the AKM (`work/art/reference/
gemini_akm_A.jfif`, ready; gitignored, never shipped, D77) processed by
`tools/art/gemini_frames.py akm` into `work/art/weapons/hand_G/akm/`: the
ready frame SDAK A, the firing frame SDAK B (A kicked: Gemini's firing image
failed and was not asked again) and the flash SDAF A (the PPSh-41's Gemini
flash grafted at the AKM's muzzle). The floor pickup SDAQ A is drawn on the
weapon pickups' rig by `tools/art/gen_akm_pickup.py`. The four ship from
`assets/sprites/akm/` under the names akm.zs's header reserved (MOD-SPEC
6.12). What is checked, and why:

  behaviour  SD_Akm's States block is the one D116 put in the mod (on the
             PPSh-41's SDPP, SDPF and SDPQ), line for line (label, frame
             letters, tics, action, flow), with only the names changed:
             not one tic moves (4 a round, 525 rpm)
  sprite     the states name only SDAK, SDAF and SDAQ; akm.zs's code names
             no SDPP, SDPF or SDPQ and carries no tint; every frame a state
             uses has its lump and every lump is used
  files      assets/sprites/akm/ holds exactly the four lumps; each has a
             grAb chunk before its image data with the canvas and offsets
             the build gives; where work/ exists each is byte-identical to
             work/art/weapons/hand_G/akm/; where the Gemini sources exist a
             fresh build reproduces them (slow, skipped at verify.py fast)
  screen     with Pillow: A 56 px above the status bar, the PPSh-41's
             SDPPA0 height (the arsenal's x1.6 CHGGA0, D78); B kicked up by
             KICK; the flash round the muzzle of B, at its left end; RGBA
             with hard alpha, all four in palette v2, no flag red in the gun
  package    the built PK3 carries them flat as sprites/<NAME>.png, and
             check_pk3 passes sprites and licences
  licences   each lump has one row, own work; the held and flash rows say
             Gemini and that the sources stay home, the pickup's says code

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
AKM_ZS = SRC_DIR / "zscript" / "weapons" / "akm.zs"
AKM_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "akm"
PPSH_READY = PROJECT_ROOT / "assets" / "sprites" / "ppsh" / "SDPPA0.png"
WORK_SET = PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G" / "akm"
REFERENCES = [PROJECT_ROOT / "work" / "art" / "reference" / n
              for n in ("gemini_akm_A.jfif", "gemini_ppsh_A.jpg", "gemini_ppsh_B.jpg")]
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_panzermensch_sprites import (  # noqa: E402  (one PNG/ZScript reader, not two)
    PNG_SIGNATURE, read_grab, states_block, strip_comments)

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy  # noqa: F401
    import gemini_frames as gf
    import gen_akm_pickup as gap
    HAVE_NUMPY = HAVE_PIL
except ImportError:   # CI's stdlib-only interpreter
    HAVE_NUMPY = False
SLOW_SKIPPED = os.environ.get("SD_SKIP_SLOW_ART") == "1"   # verify.py fast

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
RENAMED = {"SDPP": "SDAK", "SDPF": "SDAF", "SDPQ": "SDAQ"}   # D116's borrowed names -> the AKM's
HELD, FLASH, PICKUP = "SDAK", "SDAF", "SDAQ"
EXPECTED_LUMPS = {"SDAKA0", "SDAKB0", "SDAFA0", "SDAQA0"}
GEMINI_LUMPS = {"SDAKA0", "SDAKB0", "SDAFA0"}

# (canvas width, height, grAb left, top) per lump, as gemini_frames.build
# and gen_akm_pickup drew them (2026-10-24). Weapon sprites hang from
# negative offsets: the canvas's top-left on the 320x200 screen is
# (-left, WEAPONTOP - top), less BAR_LIFT with the status bar on; the pickup
# stands on its lowest pixel, centred (positive offsets).
CANVASES = {
    "SDAKA0": (247, 92, -156, -96),
    "SDAKB0": (247, 92, -158, -93),
    "SDAFA0": (30, 34, -139, -84),
    "SDAQA0": (57, 17, 28, 17),
}

# Where they stand on screen, status bar on: px from the topmost opaque
# pixel down to the bar, as the build measured them.
VIEW_H = 168                            # the 3D view above the 32-px status bar
WEAPONTOP = 32                          # psprite y at rest (Doom's p_pspr.h)
BAR_LIFT = 16                           # the view is centred on 168 rows, not 200
ABOVE_BAR = {"SDAKA0": 56, "SDAKB0": 59, "SDAFA0": 68}
KICK_UP = 3                             # gemini_frames.KICK: B is A 3 px higher

# SD_Akm's States block as D116 put it in the mod, on the PPSh-41's sprites,
# read from src/zscript/weapons/akm.zs on 2026-10-24 before the swap. One
# row per line: (label, ":", "", 0, "") for a label, (label, sprite,
# frames, tics, rest) for a state, (label, "->", flow, 0, "") for a flow.
AKM_BEFORE = (
    ("Ready", ":", "", 0, ""),
    ("Ready", "SDPP", "A", 1, "A_SD_WeaponReady"),
    ("Ready", "->", "Loop", 0, ""),
    ("Deselect", ":", "", 0, ""),
    ("Deselect", "SDPP", "A", 1, "A_Lower"),
    ("Deselect", "->", "Loop", 0, ""),
    ("Select", ":", "", 0, ""),
    ("Select", "SDPP", "A", 1, "A_Raise"),
    ("Select", "->", "Loop", 0, ""),
    ("Fire", ":", "", 0, ""),
    ("Fire", "SDPP", "B", 0, "A_GunFlash"),
    ("Fire", "SDPP", "B", 2, "A_SD_FireAkm"),
    ("Fire", "SDPP", "A", 2, ""),
    ("Fire", "SDPP", "A", 0, "A_ReFire"),
    ("Fire", "->", "Goto Ready", 0, ""),
    ("Flash", ":", "", 0, ""),
    ("Flash", "SDPF", "A", 2, "Bright A_Light1"),
    ("Flash", "->", "Goto LightDone", 0, ""),
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "SDPQ", "A", -1, ""),
    ("Spawn", "->", "Stop", 0, ""),
)


def states(path: Path = AKM_ZS) -> list[tuple]:
    """Every line of the States block, labels included, in order."""
    body = states_block(strip_comments(path.read_text(encoding="utf-8")))
    label, rows = None, []
    for line in body.splitlines():
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
            raise AssertionError(f"{path.name}: unparsed States line {line!r}")
    return rows


def frame_rows(rows: list[tuple]) -> list[tuple]:
    return [r for r in rows if r[1] not in (":", "->")]


def installed() -> list[Path]:
    return sorted(AKM_SPRITES.glob("*.png")) if AKM_SPRITES.is_dir() else []


def opaque_box(path: Path) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of the opaque pixels, right/bottom exclusive."""
    with Image.open(path) as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    assert box is not None, path
    return box


def on_screen(path: Path) -> tuple[int, int, int]:
    """(px above the status bar, opaque x0, opaque x1) with the bar on."""
    left, top = read_grab(path.read_bytes())
    x0, y0 = -left, WEAPONTOP - top - BAR_LIFT
    bx0, by0, bx1, _ = opaque_box(path)
    return VIEW_H - (y0 + by0), x0 + bx0, x0 + bx1


def lump(name: str) -> Path:
    return AKM_SPRITES / f"{name}.png"


class BehaviourTests(unittest.TestCase):
    def test_states_are_d116s_but_for_the_names(self):
        expected = [(lb, RENAMED.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in AKM_BEFORE]
        self.assertEqual(states(), expected)

    def test_four_tics_a_round(self):
        fire = [r for r in frame_rows(states()) if r[0] == "Fire"]
        self.assertEqual(sum(r[3] for r in fire), 4, "2 + 2 tics a round, 525 rpm (BALANCE.md slot 4b)")
        self.assertEqual(len(frame_rows(states())), 9)


class SpriteTests(unittest.TestCase):
    def test_states_name_only_the_akms(self):
        rows = frame_rows(states())
        self.assertEqual({r[1] for r in rows if r[0] not in ("Spawn", "Flash")}, {HELD})
        self.assertEqual({r[1] for r in rows if r[0] == "Flash"}, {FLASH})
        self.assertEqual([r[1:4] for r in rows if r[0] == "Spawn"], [(PICKUP, "A", -1)])

    def test_no_borrowed_name_and_no_tint_in_code(self):
        code = strip_comments(AKM_ZS.read_text(encoding="utf-8"))
        for old in RENAMED:
            self.assertNotIn(old, code)
        self.assertNotIn("Translation", code)
        self.assertNotIn("PROVISIONAL", AKM_ZS.read_text(encoding="utf-8"))

    def test_every_frame_used_is_installed_and_every_lump_used(self):
        used = {f"{sprite}{f}0" for _, sprite, frames, _, _ in frame_rows(states()) for f in frames}
        self.assertEqual(used, EXPECTED_LUMPS)
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)


class FileTests(unittest.TestCase):
    def test_exactly_the_four_lumps(self):
        if AKM_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in AKM_SPRITES.iterdir()),
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
    def test_byte_identical_to_the_built_frames(self):
        for p in installed():
            source = WORK_SET / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipIf(SLOW_SKIPPED, "renders: slow tier only")
    @unittest.skipUnless(HAVE_NUMPY and all(r.is_file() for r in REFERENCES),
                         "the Gemini sources are not here (gitignored, D77) or numpy/Pillow is missing")
    def test_a_fresh_build_reproduces_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = gf.build(gf.WEAPONS["akm"], out_dir=Path(tmp))
            for name in GEMINI_LUMPS:
                self.assertEqual(lump(name).read_bytes(), res["frames"][name]["path"].read_bytes(), name)
            self.assertEqual(gap.main(["--out", tmp]), 0)
            self.assertEqual(lump("SDAQA0").read_bytes(), (Path(tmp) / "SDAQA0.png").read_bytes())


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class ScreenTests(unittest.TestCase):
    def test_they_stand_where_the_build_put_them(self):
        for name, above in ABOVE_BAR.items():
            self.assertEqual(on_screen(lump(name))[0], above, name)

    def test_the_ready_frame_is_at_the_ppshs_height(self):
        self.assertEqual(on_screen(lump("SDAKA0"))[0], on_screen(PPSH_READY)[0])

    def test_the_firing_frame_kicks_up(self):
        a, b = (on_screen(lump(n))[0] for n in ("SDAKA0", "SDAKB0"))
        self.assertEqual(b - a, KICK_UP)

    def test_the_flash_sits_round_the_muzzle_of_b(self):
        """SDAF A plays over SDAK B (the Flash state rides on Fire's B): its
        box spans B's left end, the muzzle, and bursts above B's top."""
        b_above, b_x0, _ = on_screen(lump("SDAKB0"))
        f_above, f_x0, f_x1 = on_screen(lump("SDAFA0"))
        self.assertTrue(f_x0 < b_x0 < f_x1)
        self.assertGreater(f_above, b_above)

    def test_rgba_hard_alpha_palette_v2_no_flag_red(self):
        v2 = set(palette_mod.colours(2))
        flag = set(palette_mod.ramp_colours("flag_red"))
        for p in installed():
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", p.name)
                raw = img.tobytes()
            self.assertLessEqual(set(raw[3::4]), {0, 255}, p.name)
            used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
            self.assertFalse(used - v2, p.name)
            if p.stem != "SDAFA0":
                self.assertFalse(used & flag, p.name)


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
            self.assertFalse([n for n in names if n.startswith("sprites/akm")], "the set folder is dropped")
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
        for name in sorted(GEMINI_LUMPS):
            origin = self.row(name).origin
            self.assertIn("generated by the project lead with Google Gemini", origin, name)
            self.assertIn("not distributed", origin, name)
        self.assertIn("gen_akm_pickup.py", self.row("SDAQA0").origin)


if __name__ == "__main__":
    unittest.main()
