"""N17 (2026-10-15), D111 (2026-10-23): the TT-33 is ours in hand.

N17 installed our TT-33 in Freedoom's recoloured pistol hands (R3-A1, D61,
D63). D111 redid it with Gemini like the other six weapons: the project
lead's pair (`work/art/reference/gemini_tt33_A.png` ready, `_B.png`
firing; gitignored, never shipped, D77) processed by
`tools/art/gemini_frames.py tt33` into `work/art/weapons/hand_G/tt33/`,
and those four lumps ship from `assets/sprites/tt33/`, beside the pickup
SDTPA0 (D48), under the same names. MOD-SPEC 6.3.
The same pattern as the enemies' installs (tests/test_doughboy_sprites.py,
D70). What is checked, and why:

  behaviour  SD_Tokarev's States block is the one that stood at HEAD
             5c05577, before N17, line for line (label, frame letters,
             tics, action, flow), with only PISG renamed SDTT and PISF
             SDTF: not one tic moves
  sprite     the held and flash states name only SDTT and SDTF (the Spawn
             state keeps SDTP), tokarev.zs does not mention PISG or PISF
             even in a comment, no state anywhere names them, MOD-SPEC 5.1
             no longer declares them, and every frame a state uses has its
             lump and every lump is used
  files      assets/sprites/tt33/ holds exactly the four lumps and the
             pickup; each has a grAb chunk before its image data with the
             canvas and offsets the build gives; where work/ exists each is
             byte-identical to work/art/weapons/hand_G/tt33/, where the
             Gemini sources exist a fresh build reproduces them, and none is
             hand E's rejected draft of the same name (D48)
  screen     with Pillow: the frames stand where the build put them (nothing
             in tokarev.zs moves a weapon sprite in code): A 56 px above the
             status bar like every weapon (x1.6 CHGGA0, D78) and inside D57's
             band around Freedoom's PISGA0 (55 +- 10 %), the muzzle flash on
             the crosshair, B kicked up and C between; RGBA with hard alpha,
             all four in palette v2
  package    the built PK3 carries them flat as sprites/<NAME>.png, and
             check_pk3 passes sprites and licences
  licences   each lump has a row, own work derived from Gemini, the
             sources not distributed (as the PPSh-41's, D79)
  overlay    the draft overlay records PISG -> SDTT and PISF -> SDTF as
             installed (INSTALLED_WEAPON_FRAMES) and no swap names either
             side or tokarev.zs

Doom's own Pistol (PISG, PISF) is not touched: ours replaces it, so the
player never holds it; its IWAD lumps stay in the IWAD.

Stdlib only, but for the screen and palette checks, which need Pillow.
"""

from __future__ import annotations

import json
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
TOKAREV_ZS = SRC_DIR / "zscript" / "weapons" / "tokarev.zs"
TT33_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "tt33"
WORK_SET = PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G" / "tt33"
REFERENCES = [PROJECT_ROOT / "work" / "art" / "reference" / f"gemini_tt33_{k}.png" for k in "AB"]
WORK_HAND_E = PROJECT_ROOT / "work" / "art" / "weapons" / "tt33"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from _n9_sound_hooks import with_sound_hooks  # noqa: E402  (N9: the empty click on Ready)
from _v3_reload_states import frame_count, with_reloads  # noqa: E402  (V3 reloads: guards + Reload states)
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
    HAVE_NUMPY = HAVE_PIL
except ImportError:   # CI's stdlib-only interpreter
    HAVE_NUMPY = False

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
RENAMED = {"PISG": "SDTT", "PISF": "SDTF"}   # Freedoom's placeholder -> ours
HELD, FLASH, PICKUP = "SDTT", "SDTF", "SDTP"
PICKUP_LUMP = "SDTPA0"                       # D48, tests/test_weapon_sprites.py
EXPECTED_LUMPS = {"SDTTA0", "SDTTB0", "SDTTC0", "SDTFA0"}

# (canvas width, height, grAb left, top) per lump, as gemini_frames.build
# drew them (2026-10-23, D111). Weapon sprites hang from negative offsets:
# the canvas's top-left on the 320x200 screen is (-left, WEAPONTOP - top),
# less BAR_LIFT with the status bar on.
CANVASES = {
    "SDTTA0": (77, 92, -154, -96),
    "SDTTB0": (77, 92, -156, -93),
    "SDTTC0": (77, 92, -155, -94),
    "SDTFA0": (41, 36, -138, -77),
}

# Where they stand on screen, status bar on (hand_study.measure): px from
# the topmost opaque pixel down to the bar, as the build measured them.
SCREEN_W, VIEW_H = 320, 168             # the 3D view above the 32-px status bar
WEAPONTOP = 32                          # psprite y at rest (Doom's p_pspr.h)
BAR_LIFT = 16                           # the view is centred on 168 rows, not 200
ABOVE_BAR = {"SDTTA0": 56, "SDTTB0": 59, "SDTTC0": 58, "SDTFA0": 75}
PISGA0_ABOVE_BAR = 55                   # Freedoom's ready frame (hand_study.TT_TARGET_TOP 113)
D57_BAND = 0.10                         # D57: the Doom counterpart's height +- 10 %
MUZZLE_TOLERANCE = 4                    # px: the flash's centre from the crosshair (gemini_frames.TT33_X_SHIFT)

# SD_Tokarev's States block as it stood before N17, with Freedoom's PISG
# and PISF, read from src/zscript/weapons/tokarev.zs at HEAD 5c05577 on
# 2026-10-15 before the swap. One row per line: (label, ":", "", 0, "") for
# a label, (label, sprite, frames, tics, rest) for a state, (label, "->",
# flow, 0, "") for Goto/Loop/Stop.
TOKAREV_BEFORE_N17 = (
    ("Ready", ":", "", 0, ""),
    ("Ready", "PISG", "A", 1, "A_WeaponReady"),
    ("Ready", "->", "Loop", 0, ""),
    ("Deselect", ":", "", 0, ""),
    ("Deselect", "PISG", "A", 1, "A_Lower"),
    ("Deselect", "->", "Loop", 0, ""),
    ("Select", ":", "", 0, ""),
    ("Select", "PISG", "A", 1, "A_Raise"),
    ("Select", "->", "Loop", 0, ""),
    ("Fire", ":", "", 0, ""),
    ("Fire", "PISG", "A", 4, ""),
    ("Fire", "PISG", "B", 0, "A_GunFlash"),
    ("Fire", "PISG", "B", 6, "A_FireBullets(SD_TT_SPREAD, 0, SD_TT_BULLETS, SD_TT_DAMAGE)"),
    ("Fire", "PISG", "C", 3, ""),
    ("Fire", "PISG", "B", 3, "A_ReFire"),
    ("Fire", "->", "Goto Ready", 0, ""),
    ("Flash", ":", "", 0, ""),
    ("Flash", "PISF", "A", 5, "Bright A_Light1"),
    ("Flash", "->", "Goto LightDone", 0, ""),
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "SDTP", "A", -1, ""),
    ("Spawn", "->", "Stop", 0, ""),
)


def states(path: Path = TOKAREV_ZS) -> list[tuple]:
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
    """The held and flash lumps (the pickup shares the folder since D48)."""
    if not TT33_SPRITES.is_dir():
        return []
    return sorted(p for p in TT33_SPRITES.glob("*.png") if p.stem != PICKUP_LUMP)


def opaque_box(name: str) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of the opaque pixels, right/bottom exclusive."""
    with Image.open(TT33_SPRITES / f"{name}.png") as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    assert box is not None, name
    return box


def on_screen(name: str) -> tuple[int, int, int]:
    """(px above the status bar, opaque x0, opaque x1) with the bar on."""
    left, top = read_grab((TT33_SPRITES / f"{name}.png").read_bytes())
    x0, y0 = -left, WEAPONTOP - top - BAR_LIFT
    bx0, by0, bx1, _ = opaque_box(name)
    return VIEW_H - (y0 + by0), x0 + bx0, x0 + bx1


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_n17_ones_but_for_the_names(self):
        expected = [(lb, RENAMED.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in TOKAREV_BEFORE_N17]
        self.assertEqual(states(), with_reloads("tokarev.zs", with_sound_hooks("tokarev.zs", expected)))

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states()), totals(with_reloads("tokarev.zs", TOKAREV_BEFORE_N17)))
        self.assertEqual(totals(states())["Fire"], 16, "4 + 6 + 3 + 3 tics per shot (BALANCE.md)")

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states())), 10 + frame_count("tokarev.zs"))


class SpriteTests(unittest.TestCase):
    def test_held_and_flash_states_name_only_ours(self):
        rows = frame_rows(states())
        self.assertEqual({r[1] for r in rows if r[0] != "Spawn"}, {HELD, FLASH})
        self.assertEqual({r[1] for r in rows if r[0] == "Flash"}, {FLASH})
        self.assertEqual([r[1:4] for r in rows if r[0] == "Spawn"], [(PICKUP, "A", -1)])

    def test_tokarev_zs_does_not_mention_the_placeholders(self):
        text = TOKAREV_ZS.read_text(encoding="utf-8")
        for old in RENAMED:
            self.assertNotIn(old, text, "not even in a comment")

    def test_no_state_anywhere_names_the_placeholders(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & set(RENAMED), path.name)

    def test_mod_spec_retires_the_placeholders(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        for old in RENAMED:
            self.assertNotIn(old, declared, f"MOD-SPEC 5.1 still declares {old}")

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for label, sprite, frames, _, _ in frame_rows(states()):
            if label == "Spawn":
                continue
            for f in frames:
                self.assertIn(f"{sprite}{f}0", names)

    def test_every_installed_frame_is_used(self):
        used = {f"{sprite}{f}0" for label, sprite, frames, _, _ in frame_rows(states())
                if label != "Spawn" for f in frames}
        self.assertEqual(used, EXPECTED_LUMPS)


class FileTests(unittest.TestCase):
    def test_exactly_the_four_lumps_and_the_pickup(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        if TT33_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in TT33_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS | {PICKUP_LUMP}),
                             "no metrics.json, nothing but lumps")

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

    @unittest.skipUnless(HAVE_NUMPY and all(r.is_file() for r in REFERENCES),
                         "the Gemini sources are not here (gitignored, D77) or numpy/Pillow is missing")
    def test_a_fresh_build_reproduces_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = gf.build(gf.WEAPONS["tt33"], out_dir=Path(tmp))
            for p in installed():
                self.assertEqual(p.read_bytes(), res["frames"][p.stem]["path"].read_bytes(), p.name)

    @unittest.skipUnless(WORK_HAND_E.is_dir(), "work/ not present (CI has no work/)")
    def test_not_hand_e(self):
        """Hand E's drafts carry the same names (D48 rejected the hand): the
        installed lumps must not be them."""
        for p in installed():
            draft = WORK_HAND_E / p.name
            if draft.is_file():
                self.assertNotEqual(p.read_bytes(), draft.read_bytes(), p.name)


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class ScreenTests(unittest.TestCase):
    def test_they_stand_where_the_build_put_them(self):
        for name, above in ABOVE_BAR.items():
            self.assertEqual(on_screen(name)[0], above, name)

    def test_the_ready_frame_is_at_pisg_height(self):
        above = on_screen("SDTTA0")[0]
        self.assertLessEqual(abs(above - PISGA0_ABOVE_BAR), D57_BAND * PISGA0_ABOVE_BAR)

    def test_the_muzzle_is_on_the_crosshair(self):
        """The pistol is the one weapon held at the centre (Doom's, the D61
        TT-33): its flash, at the muzzle, is centred; the hand is right of it."""
        _, f_x0, f_x1 = on_screen("SDTFA0")
        self.assertLessEqual(abs((f_x0 + f_x1) / 2 - SCREEN_W / 2), MUZZLE_TOLERANCE)
        _, x0, x1 = on_screen("SDTTA0")
        self.assertTrue(x0 < SCREEN_W / 2 < x1)

    def test_the_firing_frame_kicks_up_and_c_settles(self):
        a, b, c = (on_screen(n)[0] for n in ("SDTTA0", "SDTTB0", "SDTTC0"))
        self.assertTrue(a < c < b)

    def test_the_flash_sits_on_the_muzzle_of_b(self):
        """SDTF A plays over SDTT B (the Flash state rides on Fire's B):
        its box overlaps the top of B's drawing on screen."""
        b_above, b_x0, b_x1 = on_screen("SDTTB0")
        f_above, f_x0, f_x1 = on_screen("SDTFA0")
        self.assertTrue(b_x0 < f_x1 and f_x0 < b_x1)
        with Image.open(TT33_SPRITES / "SDTFA0.png") as img:
            f_h = img.convert("RGBA").getchannel("A").getbbox()
        f_bottom = f_above - (f_h[3] - f_h[1])
        self.assertTrue(f_bottom < b_above <= f_above)

    def test_rgba_hard_alpha_and_palette_v2(self):
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
            self.assertFalse([n for n in names if n.startswith("sprites/tt33")], "the set folder is dropped")
            self.assertFalse([n for n in names if "gemini" in n.lower()], "no source image ships (D77)")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))


class LicenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))

    def row(self, lump: str):
        found = [r for r in self.rows if r.covers(f"sprites/{lump}.png")]
        self.assertEqual(len(found), 1, f"{lump}: {len(found)} rows in docs/art/LICENSES.md")
        return found[0]

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        self.assertEqual([], sorted(n for n in EXPECTED_LUMPS if n not in declared))

    def test_the_rows_say_gemini_and_that_the_sources_stay_home(self):
        for lump in sorted(EXPECTED_LUMPS):
            row = self.row(lump)
            self.assertTrue(row.own_work, lump)
            self.assertEqual(row.required, licences.OWN_WORK_CREDITS, lump)
            self.assertIn("generated by the project lead with Google Gemini", row.origin, lump)
            self.assertIn("processed into pixel art", row.origin, lump)
            self.assertIn("the source images are not distributed", row.origin, lump)
            self.assertNotIn("Freedoom", row.origin, f"{lump}: no Freedoom pixel since D111")


class OverlayTests(unittest.TestCase):
    def test_recorded_as_installed(self):
        # D79 added the PPSh-41's pairs after these (tests/test_ppsh_sprites.py)
        self.assertLessEqual(set(RENAMED.items()), set(mdo.INSTALLED_WEAPON_FRAMES))
        self.assertLessEqual({HELD, FLASH}, mdo.installed_sprites())

    def test_the_overlay_names_nothing_of_the_tt33(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & (set(RENAMED) | {HELD, FLASH}), swap)
            self.assertNotIn("tokarev", swap.zs)

    def test_the_overlay_reads_the_states_as_the_engine_does(self):
        text = TOKAREV_ZS.read_text(encoding="utf-8")
        for old in RENAMED:
            self.assertEqual(mdo.state_letters(text, old), "")
        self.assertEqual(mdo.state_letters(text, HELD), "ABC")
        self.assertEqual(mdo.state_letters(text, FLASH), "A")


if __name__ == "__main__":
    unittest.main()
