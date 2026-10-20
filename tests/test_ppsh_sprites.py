"""D79 (2026-10-20): the PPSh-41 is ours in hand, from the CEO's Gemini pair.

The CEO adopted the Gemini-frames method after the PPSh-41 test seen in
engine through the draft overlay ("Haz la 1", D79; D78 superseded): the
three lumps `tools/art/gemini_frames.py ppsh` builds from the CEO's Google
Gemini images (`work/art/reference/gemini_ppsh_A.jpg` ready, `_B.jpg`
firing; gitignored, never distributed, D77) into
`work/art/weapons/hand_G/ppsh/` ship from `assets/sprites/ppsh/`, beside the
pickup SDPQA0 (D48). With the two fixes D79 asked for: the arms leave the
view cleanly (no box edge above the bar at any bob, in 4:3 or 16:9), and
the firing frame kicks 2 px right and 3 px up, its flash with it. The same
pattern as the TT-33's install (tests/test_tt33_sprites.py, N17). What is
checked, and why:

  behaviour  SD_Ppsh's States block is the one that stood at HEAD c3aad1f,
             before D79, line for line (label, frame letters, tics, action,
             flow), with only CHGG renamed SDPP and CHGF SDPF
  sprite     the held and flash states name only SDPP and SDPF (Spawn keeps
             SDPQ), ppsh.zs does not mention CHGG or CHGF even in a comment,
             no state anywhere names them, MOD-SPEC 5.1 no longer declares
             them, every frame a state uses has its lump and every lump is
             used
  files      assets/sprites/ppsh/ holds exactly the three lumps and the
             pickup; each has a grAb chunk before its image data with the
             canvas and offsets below; where work/ exists each is
             byte-identical to work/art/weapons/hand_G/ppsh/, and where the
             Gemini sources exist a fresh build reproduces them (both skip
             cleanly on CI, which has no work/)
  screen     with Pillow: A 56 px above the bar (x1.6 Freedoom's CHGGA0,
             D78's choice), B kicked by gemini_frames.KICK, the flash on B's
             muzzle; no opaque pixel on a sprite border is visible above
             the bar (or the screen bottom, bar off) at any bob within 16:9;
             RGBA with hard alpha, all three in palette v2
  package    the built PK3 carries them flat as sprites/<NAME>.png, and
             check_pk3 passes sprites and licences
  licences   each lump has an own-work row (CC BY-NC-SA 4.0) saying it is
             derived from images the project lead generated with Google
             Gemini and that the sources are not distributed; the in-game
             credits (EN and RU, <= 40 chars a line) and the release's AI
             paragraph name Google Gemini next to Fooocus / SDXL
  overlay    the draft overlay records CHGG -> SDPP and CHGF -> SDPF as
             installed (INSTALLED_WEAPON_FRAMES) and no swap names either
             side or ppsh.zs

Doom's own Chaingun (CHGG, CHGF) is not touched: ours replaces it, so the
player never holds it; its IWAD lumps stay in the IWAD.

Stdlib only, but for the screen, palette and rebuild checks (Pillow, numpy).
"""

from __future__ import annotations

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
PPSH_ZS = SRC_DIR / "zscript" / "weapons" / "ppsh.zs"
LANGUAGE = SRC_DIR / "lumps" / "LANGUAGE"
PPSH_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "ppsh"
WORK_SET = PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G" / "ppsh"
REFERENCES = [PROJECT_ROOT / "work" / "art" / "reference" / f"gemini_ppsh_{k}.jpg" for k in "AB"]
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
import release  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_panzermensch_sprites import (  # noqa: E402  (one PNG/ZScript reader, not two)
    PNG_SIGNATURE, read_grab, states_block, strip_comments)

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy as np
    import gemini_frames as gf
    HAVE_NUMPY = HAVE_PIL
except ImportError:
    HAVE_NUMPY = False

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
RENAMED = {"CHGG": "SDPP", "CHGF": "SDPF"}   # Freedoom's placeholder -> ours
HELD, FLASH, PICKUP = "SDPP", "SDPF", "SDPQ"
PICKUP_LUMP = "SDPQA0"                       # D48, tests/test_weapon_sprites.py
EXPECTED_LUMPS = {"SDPPA0", "SDPPB0", "SDPFA0"}

# (canvas width, height, grAb left, top) per lump, as gemini_frames.py
# built them on 2026-10-20 (D79). The canvases are wide because the right
# arm runs on ARM_EXIT px past the screen's right edge before it curves out
# (the stock, in its own wood, leaves under the bar sooner: 251 since the
# stock/sleeve split of 2026-10-20).
CANVASES = {
    "SDPPA0": (251, 92, -152, -96),
    "SDPPB0": (251, 92, -154, -93),
    "SDPFA0": (35, 35, -144, -81),
}

SCREEN_W, VIEW_H = 320, 168             # the 3D view above the 32-px status bar
WEAPONTOP = 32                          # psprite y at rest (Doom's p_pspr.h)
BAR_LIFT = 16                           # the view is centred on 168 rows, not 200
ABOVE_BAR = {"SDPPA0": 56, "SDPPB0": 59, "SDPFA0": 71}
CHGGA0_ABOVE_BAR = 35                   # Freedoom's ready frame (hand_ref.PPSH_CHGG_HEIGHT)
HEIGHT_MULT = 1.6                       # D78's choice, kept by D79
KICK = (2, -3)                          # gemini_frames.KICK: right, up (screen px)

# SD_Ppsh's States block as it stood before D79, with Freedoom's CHGG and
# CHGF, read from src/zscript/weapons/ppsh.zs at HEAD c3aad1f on 2026-10-20
# before the swap (N9's A_SD_WeaponReady already in). One row per line:
# (label, ":", "", 0, "") for a label, (label, sprite, frames, tics, rest)
# for a state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
PPSH_BEFORE_D79 = (
    ("Ready", ":", "", 0, ""),
    ("Ready", "CHGG", "A", 1, "A_SD_WeaponReady"),
    ("Ready", "->", "Loop", 0, ""),
    ("Deselect", ":", "", 0, ""),
    ("Deselect", "CHGG", "A", 1, "A_Lower"),
    ("Deselect", "->", "Loop", 0, ""),
    ("Select", ":", "", 0, ""),
    ("Select", "CHGG", "A", 1, "A_Raise"),
    ("Select", "->", "Loop", 0, ""),
    ("Fire", ":", "", 0, ""),
    ("Fire", "CHGG", "A", 0, "A_GunFlash"),
    ("Fire", "CHGG", "A", 3, "A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE)"),
    ("Fire", "CHGG", "B", 0, "A_GunFlash"),
    ("Fire", "CHGG", "B", 3, "A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE)"),
    ("Fire", "CHGG", "B", 0, "A_ReFire"),
    ("Fire", "->", "Goto Ready", 0, ""),
    ("Flash", ":", "", 0, ""),
    ("Flash", "CHGF", "A", 3, "Bright A_Light1"),
    ("Flash", "->", "Goto LightDone", 0, ""),
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "SDPQ", "A", -1, ""),
    ("Spawn", "->", "Stop", 0, ""),
)


def states(path: Path = PPSH_ZS) -> list[tuple]:
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
    if not PPSH_SPRITES.is_dir():
        return []
    return sorted(p for p in PPSH_SPRITES.glob("*.png") if p.stem != PICKUP_LUMP)


def opaque_box(name: str) -> tuple[int, int, int, int]:
    with Image.open(PPSH_SPRITES / f"{name}.png") as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    assert box is not None, name
    return box


def on_screen(name: str) -> tuple[int, int, int]:
    """(px above the status bar, opaque x0, opaque x1) with the bar on."""
    left, top = read_grab((PPSH_SPRITES / f"{name}.png").read_bytes())
    x0, y0 = -left, WEAPONTOP - top - BAR_LIFT
    bx0, by0, bx1, _ = opaque_box(name)
    return VIEW_H - (y0 + by0), x0 + bx0, x0 + bx1


def credit_lines() -> tuple[list[str], list[str]]:
    """The AI block, SD_CRED_AI_1.._8 (D93; SD_CRED_SRC_4.._6 until then), in
    [enu default] and in [ru], in file order."""
    found = re.findall(r'^\s*SD_CRED_AI_([1-8])\s*=\s*"([^"]*)"\s*;', LANGUAGE.read_text(encoding="utf-8"), re.M)
    assert [k for k, _ in found] == list("12345678" * 2), found
    return [t for _, t in found[:8]], [t for _, t in found[8:]]


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d79_ones_but_for_the_names(self):
        expected = [(lb, RENAMED.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in PPSH_BEFORE_D79]
        self.assertEqual(states(), expected)

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states()), totals(PPSH_BEFORE_D79))
        self.assertEqual(totals(states())["Fire"], 6, "3 tics a round, two rounds (BALANCE.md)")

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states())), 10)


class SpriteTests(unittest.TestCase):
    def test_held_and_flash_states_name_only_ours(self):
        rows = frame_rows(states())
        self.assertEqual({r[1] for r in rows if r[0] != "Spawn"}, {HELD, FLASH})
        self.assertEqual({r[1] for r in rows if r[0] == "Flash"}, {FLASH})
        self.assertEqual([r[1:4] for r in rows if r[0] == "Spawn"], [(PICKUP, "A", -1)])

    def test_ppsh_zs_does_not_mention_the_placeholders(self):
        text = PPSH_ZS.read_text(encoding="utf-8")
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
    def test_exactly_the_three_lumps_and_the_pickup(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(sorted(p.name for p in PPSH_SPRITES.iterdir()),
                         sorted(f"{n}.png" for n in EXPECTED_LUMPS | {PICKUP_LUMP}),
                         "nothing but lumps: no source image, no preview")

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
            res = gf.build(gf.WEAPONS["ppsh"], out_dir=Path(tmp))
            for p in installed():
                self.assertEqual(p.read_bytes(), res["frames"][p.stem]["path"].read_bytes(), p.name)


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class ScreenTests(unittest.TestCase):
    def test_they_stand_where_the_build_put_them(self):
        for name, above in ABOVE_BAR.items():
            self.assertEqual(on_screen(name)[0], above, name)

    def test_the_ready_frame_is_x1_6_chgg(self):
        self.assertEqual(on_screen("SDPPA0")[0], round(CHGGA0_ABOVE_BAR * HEIGHT_MULT))

    def test_the_firing_frame_kicks_up_and_right(self):
        a, b = (read_grab((PPSH_SPRITES / f"{n}.png").read_bytes()) for n in ("SDPPA0", "SDPPB0"))
        self.assertEqual((a[0] - b[0], b[1] - a[1]), (KICK[0], -KICK[1]), "grAb: B sits 2 px right, 3 px up")
        if HAVE_NUMPY:
            self.assertEqual(gf.KICK, KICK)

    def test_the_flash_sits_on_the_muzzle_of_b(self):
        """SDPF A plays over SDPP B (and A): its box overlaps the left,
        muzzle end of B's drawing, at the barrel's height."""
        b_above, b_x0, _ = on_screen("SDPPB0")
        f_above, f_x0, f_x1 = on_screen("SDPFA0")
        self.assertTrue(f_x0 < b_x0 < f_x1, (f_x0, b_x0, f_x1))
        self.assertLessEqual(abs(f_above - b_above), 15)

    @unittest.skipUnless(HAVE_NUMPY, "numpy not available in this interpreter")
    def test_no_cut_edge_is_visible_at_any_bob(self):
        """D79: the right forearm ended in a hard vertical cut. No opaque
        pixel on a held frame's border shows above the bar (or the screen
        bottom, bar off) within the 16:9 view plus the horizontal bob."""
        lut = {tuple(c): i for i, c in enumerate(gf.palette_rgb().tolist())}
        for name in ("SDPPA0", "SDPPB0"):
            p = PPSH_SPRITES / f"{name}.png"
            with Image.open(p) as img:
                rgba = np.asarray(img.convert("RGBA"))
            idx = np.full(rgba.shape[:2], gf.TRANSPARENT, np.int32)
            op = rgba[..., 3] > 0
            idx[op] = [lut[tuple(c)] for c in rgba[op][:, :3].tolist()]
            grab = read_grab(p.read_bytes())
            self.assertEqual(gf.visible_cuts(idx, grab, bar_on=True), 0, name)
            self.assertEqual(gf.visible_cuts(idx, grab, bar_on=False), 0, name)
            # and the canvas reaches past the widest view on the right
            self.assertGreaterEqual(-grab[0] + idx.shape[1], SCREEN_W + gf.WIDE_MARGIN + gf.BOB_X, name)

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
            self.assertFalse([n for n in names if n.startswith("sprites/ppsh")], "the set folder is dropped")
            self.assertFalse([n for n in names if "gemini" in n.lower()], "no source image ships (D77)")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


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

    def test_the_in_game_credits_name_gemini_in_both_languages(self):
        for lang, lines in zip(("en", "ru"), credit_lines()):
            joined = " ".join(lines)
            self.assertIn("Google Gemini", joined, lang)
            self.assertIn("Fooocus / SDXL", joined, lang)
            for line in lines:
                self.assertLessEqual(len(line), 40, f"[{lang}] {line!r}")

    def test_the_release_names_gemini_in_both_languages(self):
        for lang, text in release.AI_DISCLOSURE.items():
            self.assertIn("Google Gemini", text, lang)
            self.assertIn("Fooocus / SDXL", text, lang)


class OverlayTests(unittest.TestCase):
    def test_recorded_as_installed(self):
        self.assertLessEqual(set(RENAMED.items()), set(mdo.INSTALLED_WEAPON_FRAMES))
        self.assertLessEqual({HELD, FLASH}, mdo.installed_sprites())

    def test_the_overlay_names_nothing_of_the_ppsh(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & (set(RENAMED) | {HELD, FLASH}), swap)
            self.assertNotIn("ppsh", swap.zs)

    def test_the_overlay_reads_the_states_as_the_engine_does(self):
        text = PPSH_ZS.read_text(encoding="utf-8")
        for old in RENAMED:
            self.assertEqual(mdo.state_letters(text, old), "")
        self.assertEqual(mdo.state_letters(text, HELD), "AB")
        self.assertEqual(mdo.state_letters(text, FLASH), "A")


if __name__ == "__main__":
    unittest.main()
