"""D84 and D88 (2026-10-20): the IZh-58, RPG-7, ROKS-3, hand Katyusha and ice axe in hand.

The CEO approved four of the five weapons built from his Google Gemini
images after seeing them in engine through the draft overlay (D84,
`docs/art/previews/2026-10-20_1037_F4_five-weapons-gemini-in-engine.png`),
and the ice axe once its swing was redone, rotated from the ready frame as
one rigid piece (D88, "Piolet aprobado",
`docs/art/previews/2026-10-20_1112_F4_ice-axe-swing-ABCD.png`). The lumps
`tools/art/gemini_frames.py <weapon>` builds from those images
(`work/art/reference/gemini_*`, gitignored, never distributed, D77) into
`work/art/weapons/hand_G/<weapon>/` ship from `assets/sprites/<weapon>/`,
beside each weapon's world pickup (D48; the hand Katyusha's pickup lives in
`pickups/`, D80, tests/test_pickups_install.py). The same install as the
PPSh-41's (D79, tests/test_ppsh_sprites.py). What is checked, and why:

  behaviour  each States block is the one that stood at HEAD e84c56c,
             before D84 and D88, line for line (label, frame letters, tics, action,
             flow), with only the held and flash names renamed (and the
             Katyusha's pickup, BFUG -> SDHP)
  sprite     the held and flash states name only ours, no .zs of the four
             mentions a retired placeholder even in a comment, no state
             anywhere names one, MOD-SPEC 5.1 no longer declares them, every
             frame a state uses has its lump and every lump is used
  files      each folder holds exactly its lumps (and the pickup); each has
             a grAb chunk before its image data with the canvas and offsets
             below; where work/ exists each is byte-identical to
             work/art/weapons/hand_G/<weapon>/, and where the Gemini sources
             exist a fresh build reproduces them (both skip cleanly on CI)
  screen     with Pillow: every lump stands where the build put it (the
             ready frames 56 px above the bar, x1.6 Freedoom's CHGGA0, +-2),
             the firing frames kicked by gemini_frames.KICK where the gun
             recoils (the ice axe 72 px, D76's long shaft), each flash
             over its gun; every held frame's arms run
             on under the bar (and under the screen bottom, bar off), and a
             fresh build measures no visible cut edge on any lump's canvas
             (gemini_frames.visible_cuts, 16:9 and the bob); RGBA with hard
             alpha, palette v2
  package    the built PK3 carries them flat as sprites/<NAME>.png, no
             source image ships, and check_pk3 passes sprites and licences
  licences   each lump has an own-work row (CC BY-NC-SA 4.0) saying it is
             derived from images the project lead generated with Google
             Gemini and that the sources are not distributed; the release's
             AI paragraph names the five (and the PPSh-41)
  overlay    the draft overlay records the nine pairs as installed
             (INSTALLED_WEAPON_FRAMES) and the Katyusha's pickup with the
             pickups (INSTALLED); no swap names either side

Doom's own Fist, Shotgun, RocketLauncher, PlasmaRifle and BFG9000 are not touched:
ours replace them, so the player never holds one; their IWAD lumps stay in
the IWAD.

Stdlib only, but for the screen, palette and rebuild checks (Pillow, numpy).
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
WEAPONS_ZS = SRC_DIR / "zscript" / "weapons"
ASSET_SPRITES = PROJECT_ROOT / "assets" / "sprites"
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "weapons" / "hand_G"
REF_DIR = PROJECT_ROOT / "work" / "art" / "reference"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
import release  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_panzermensch_sprites import PNG_SIGNATURE, read_grab  # noqa: E402
from test_ppsh_sprites import frame_rows, states  # noqa: E402  (one States parser, not three)

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy  # noqa: F401  (gemini_frames needs it)
    import gemini_frames as gf
    HAVE_NUMPY = HAVE_PIL
except ImportError:
    HAVE_NUMPY = False

# weapon (gemini_frames key and assets/sprites/ folder) -> its .zs, the
# renames (Freedoom's placeholder -> ours), its pickup sprite and whether
# the pickup lump shares the folder.
WEAPONS = {
    "izh": ("izh.zs", {"SHTG": "SDIZ", "SHTF": "SDIF"}, "SDIP", True),
    "rpg7": ("rpg7.zs", {"MISG": "SDRL", "MISF": "SDRF"}, "SDRP", True),
    "roks3": ("roks3.zs", {"PLSG": "SDRK", "PLSF": "SDKF"}, "SDKP", True),
    "katyusha": ("katyusha.zs", {"BFGG": "SDHK", "BFGF": "SDHF", "BFUG": "SDHP"}, "SDHP", False),
    "ice_axe": ("ice_axe.zs", {"PUNG": "SDAX"}, "SDAP", True),     # D88: held only, no flash
}
RETIRED = {old for _, renames, _, _ in WEAPONS.values() for old in renames}

# (canvas width, height, grAb left, top) and px above the status bar per
# lump, as gemini_frames.py built them on 2026-10-20 (D84) and measured on
# the installed files.
CANVASES = {
    "SDIZA0": (266, 93, -136, -95), "SDIZB0": (260, 93, -144, -92), "SDIZC0": (260, 93, -143, -93),
    "SDIZD0": (275, 121, -128, -67), "SDIFA0": (61, 42, -126, -73), "SDIFB0": (37, 25, -145, -84),
    "SDRLA0": (296, 92, -131, -96), "SDRLB0": (296, 92, -133, -93),
    "SDRFA0": (37, 27, -159, -85), "SDRFB0": (29, 21, -164, -88),
    "SDRFC0": (22, 17, -169, -90), "SDRFD0": (13, 11, -175, -93),
    "SDRKA0": (181, 92, -135, -96), "SDRKB0": (181, 92, -135, -96), "SDKFA0": (46, 23, -118, -80),
    "SDHKA0": (169, 92, -146, -96), "SDHKB0": (169, 92, -148, -93),
    "SDHFA0": (74, 51, -127, -72), "SDHFB0": (52, 35, -141, -81),
    "SDAXA0": (104, 108, -185, -80), "SDAXB0": (98, 145, -210, -73),
    "SDAXC0": (268, 124, -131, -94), "SDAXD0": (266, 99, -126, -119),
}
ABOVE_BAR = {"SDIZA0": 57, "SDIZB0": 60, "SDIZC0": 59, "SDIZD0": 85, "SDIFA0": 79, "SDIFB0": 68,
             "SDRLA0": 56, "SDRLB0": 59, "SDRFA0": 67, "SDRFB0": 64, "SDRFC0": 62, "SDRFD0": 59,
             "SDRKA0": 56, "SDRKB0": 56, "SDKFA0": 72,
             "SDHKA0": 56, "SDHKB0": 59, "SDHFA0": 80, "SDHFB0": 71,
             "SDAXA0": 72, "SDAXB0": 79, "SDAXC0": 58, "SDAXD0": 33}
READY = {"izh": "SDIZA0", "rpg7": "SDRLA0", "roks3": "SDRKA0", "katyusha": "SDHKA0"}
AXE_READY_ABOVE_BAR = 72                # gemini_frames: height_mult 72 / 35, D76's long shaft
KICKED = {"rpg7": ("SDRLA0", "SDRLB0"), "katyusha": ("SDHKA0", "SDHKB0")}   # same canvas, B kicked
# each flash lump -> the held frame it plays over
FLASH_OVER = {"SDIFA0": "SDIZA0", "SDIFB0": "SDIZA0", "SDRFA0": "SDRLB0", "SDRFB0": "SDRLB0",
              "SDRFC0": "SDRLB0", "SDRFD0": "SDRLB0", "SDKFA0": "SDRKA0", "SDHFA0": "SDHKB0",
              "SDHFB0": "SDHKB0"}
CHGGA0_ABOVE_BAR, HEIGHT_MULT, HEIGHT_TOLERANCE = 35, 1.6, 2   # D78's choice, kept by D79 and D84
KICK = (2, -3)                          # gemini_frames.KICK: right, up (screen px)
SCREEN_W, SCREEN_H, VIEW_H = 320, 200, 168   # the 3D view above the 32-px status bar
WEAPONTOP = 32                          # psprite y at rest (Doom's p_pspr.h)
BAR_LIFT = 16                           # the view is centred on 168 rows, not 200

# The States blocks as they stood at HEAD e84c56c on 2026-10-20, before D84,
# with Freedoom's names (N9's sound hooks already in). One row per line:
# (label, ":", "", 0, "") for a label, (label, sprite, frames, tics, rest)
# for a state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
_RS = (("Ready", "A_SD_WeaponReady"), ("Deselect", "A_Lower"), ("Select", "A_Raise"))


def _ready(held: str) -> tuple:
    return tuple(row for label, action in _RS
                 for row in ((label, ":", "", 0, ""), (label, held, "A", 1, action), (label, "->", "Loop", 0, "")))


def _tail(flash_rows: tuple, pickup: str) -> tuple:
    return ((("Flash", ":", "", 0, ""),) + flash_rows + (("Flash", "->", "Goto LightDone", 0, ""),
            ("Spawn", ":", "", 0, ""), ("Spawn", pickup, "A", -1, ""), ("Spawn", "->", "Stop", 0, "")))


BEFORE_D84 = {
    "izh": _ready("SHTG") + (
        ("Fire", ":", "", 0, ""),
        ("Fire", "SHTG", "A", 3, ""),
        ("Fire", "SHTG", "A", 6, "A_SD_FireIzh"),
        ("Fire", "SHTG", "B", 4, ""),
        ("Fire", "SHTG", "C", 4, ""),
        ("Fire", "SHTG", "A", 3, 'A_JumpIf(invoker.barrels <= 0, "Reload")'),
        ("Fire", "SHTG", "A", 3, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Reload", ":", "", 0, ""),
        ("Reload", "SHTG", "D", 6, 'A_StartSound("sd/weapon/izh/reload", CHAN_WEAPON)'),
        ("Reload", "SHTG", "C", 8, ""),
        ("Reload", "SHTG", "B", 8, ""),
        ("Reload", "SHTG", "A", 8, "A_SD_ReloadIzh"),
        ("Reload", "->", "Goto Ready", 0, ""),
    ) + _tail((("Flash", "SHTF", "A", 4, "Bright A_Light1"), ("Flash", "SHTF", "B", 3, "Bright A_Light2")), "SDIP"),
    "rpg7": _ready("MISG") + (
        ("Fire", ":", "", 0, ""),
        ("Fire", "MISG", "B", 8, "A_GunFlash"),
        ("Fire", "MISG", "B", 4, 'A_FireProjectile("SD_Pg7Grenade")'),
        ("Fire", "MISG", "B", 10, 'A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON)'),
        ("Fire", "MISG", "B", 4, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
    ) + _tail((("Flash", "MISF", "A", 3, "Bright A_Light1"), ("Flash", "MISF", "B", 4, "Bright"),
               ("Flash", "MISF", "CD", 4, "Bright A_Light2")), "SDRP"),
    "roks3": _ready("PLSG") + (
        ("Fire", ":", "", 0, ""),
        ("Fire", "PLSG", "A", 0, "A_GunFlash"),
        ("Fire", "PLSG", "A", 3, "Bright A_SD_FireRoks3"),
        ("Fire", "PLSG", "B", 20, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
    ) + _tail((("Flash", "PLSF", "A", 3, "Bright A_Light1"),), "SDKP"),
    "katyusha": _ready("BFGG") + (
        ("Fire", ":", "", 0, ""),
        ("Fire", "BFGG", "A", 20, 'A_StartSound("sd/weapon/katyusha/charge", CHAN_WEAPON)'),
        ("Fire", "BFGG", "B", 10, "A_GunFlash"),
        ("Fire", "BFGG", "B", 10, "A_SD_FireKatyusha"),
        ("Fire", "BFGG", "B", 0, 'A_StartSound("sd/weapon/katyusha/reload", SD_KATYUSHA_RELOAD_CHANNEL)'),
        ("Fire", "BFGG", "B", 20, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
    ) + _tail((("Flash", "BFGF", "A", 11, "Bright A_Light1"), ("Flash", "BFGF", "B", 6, "Bright A_Light2")), "BFUG"),
    # no sound hook in Ready (no ammo, no dry click); N9's swing sound on the wind-up
    "ice_axe": tuple(row for label, action in (("Ready", "A_WeaponReady"), ("Deselect", "A_Lower"),
                                               ("Select", "A_Raise"))
                     for row in ((label, ":", "", 0, ""), (label, "PUNG", "A", 1, action),
                                 (label, "->", "Loop", 0, ""))) + (
        ("Fire", ":", "", 0, ""),
        ("Fire", "PUNG", "B", 5, 'A_StartSound("sd/weapon/iceaxe/swing", CHAN_WEAPON)'),
        ("Fire", "PUNG", "C", 5, "A_SD_IceAxeSwing"),
        ("Fire", "PUNG", "D", 6, ""),
        ("Fire", "PUNG", "C", 5, ""),
        ("Fire", "PUNG", "B", 6, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Spawn", ":", "", 0, ""),
        ("Spawn", "SDAP", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
}
FIRE_TICS = {"izh": 23, "rpg7": 26, "roks3": 23, "katyusha": 60, "ice_axe": 27}   # BALANCE.md


def zs(weapon: str) -> Path:
    return WEAPONS_ZS / WEAPONS[weapon][0]


def used_lumps(weapon: str) -> set[str]:
    """Every held and flash lump the weapon's states show (rotation 0)."""
    return {f"{sprite}{f}0" for label, sprite, frames, _, _ in frame_rows(states(zs(weapon)))
            if label != "Spawn" for f in frames}


def installed(weapon: str) -> list[Path]:
    """The held and flash lumps in the weapon's folder (not its pickup)."""
    folder = ASSET_SPRITES / weapon
    pickup = WEAPONS[weapon][2]
    return sorted(p for p in folder.glob("*.png") if not p.stem.startswith(pickup)) if folder.is_dir() else []


def all_lumps() -> list[Path]:
    return [p for w in WEAPONS for p in installed(w)]


def lump_path(name: str) -> Path:
    return next(p for p in all_lumps() if p.stem == name)


def on_screen(name: str) -> tuple[int, int, int, int]:
    """(px above the status bar, opaque x0, x1, the opaque top's screen y)."""
    p = lump_path(name)
    left, top = read_grab(p.read_bytes())
    x0, y0 = -left, WEAPONTOP - top - BAR_LIFT
    with Image.open(p) as img:
        bx0, by0, bx1, by1 = img.convert("RGBA").getchannel("A").getbbox()
    return VIEW_H - (y0 + by0), x0 + bx0, x0 + bx1, y0 + by1


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d84_ones_but_for_the_names(self):
        for weapon, before in BEFORE_D84.items():
            renames = WEAPONS[weapon][1]
            expected = [(lb, renames.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in before]
            self.assertEqual(states(zs(weapon)), expected, weapon)

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        for weapon, before in BEFORE_D84.items():
            self.assertEqual(totals(states(zs(weapon))), totals(before), weapon)
            self.assertEqual(totals(before)["Fire"], FIRE_TICS[weapon], weapon)

    def test_the_parser_sees_every_line(self):
        self.assertEqual({w: len(frame_rows(states(zs(w)))) for w in WEAPONS},
                         {"izh": 16, "rpg7": 11, "roks3": 8, "katyusha": 11, "ice_axe": 9})


class SpriteTests(unittest.TestCase):
    def test_held_and_flash_states_name_only_ours(self):
        for weapon, (_, renames, pickup, _) in WEAPONS.items():
            rows = frame_rows(states(zs(weapon)))
            ours = [renames[old] for old in list(renames)[:2] if renames[old] != pickup]
            self.assertEqual({r[1] for r in rows if r[0] != "Spawn"}, set(ours), weapon)
            self.assertEqual({r[1] for r in rows if r[0] == "Flash"}, set(ours[1:]), weapon)
            self.assertEqual([r[1:4] for r in rows if r[0] == "Spawn"], [(pickup, "A", -1)], weapon)

    def test_the_zs_do_not_mention_the_placeholders(self):
        for weapon in WEAPONS:
            text = zs(weapon).read_text(encoding="utf-8")
            for old in RETIRED:
                self.assertNotIn(old, text, f"{weapon}: not even in a comment")

    def test_no_state_anywhere_names_the_placeholders(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & RETIRED, path.name)

    def test_mod_spec_retires_the_placeholders(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertFalse(RETIRED & declared, "MOD-SPEC 5.1 still declares them")
        self.assertLessEqual({"MISL", "PLSS", "PLSE"}, declared, "the projectiles still wear the IWAD's")

    def test_every_frame_a_state_uses_is_installed_and_every_lump_is_used(self):
        for weapon in WEAPONS:
            self.assertEqual({p.stem for p in installed(weapon)}, used_lumps(weapon), weapon)
        self.assertEqual({p.stem for p in all_lumps()}, set(CANVASES))
        self.assertEqual(len(CANVASES), 23)


class FileTests(unittest.TestCase):
    def test_nothing_but_the_lumps_and_the_pickup_in_each_folder(self):
        for weapon, (_, _, pickup, shares) in WEAPONS.items():
            want = sorted(f"{n}.png" for n in used_lumps(weapon)) + ([f"{pickup}A0.png"] if shares else [])
            self.assertEqual(sorted(p.name for p in (ASSET_SPRITES / weapon).iterdir()), sorted(want),
                             f"{weapon}: nothing but lumps, no source image, no preview")

    def test_every_sprite_carries_its_canvas_and_offsets(self):
        for p in all_lumps():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height) + tuple(grab), CANVASES[p.stem], p.name)

    @unittest.skipUnless(all((WORK_ROOT / w).is_dir() for w in WEAPONS), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_built_frames(self):
        for weapon in WEAPONS:
            for p in installed(weapon):
                source = WORK_ROOT / weapon / p.name
                self.assertTrue(source.is_file(), source)
                self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_NUMPY and REF_DIR.is_dir(),
                         "the Gemini sources are not here (gitignored, D77) or numpy/Pillow is missing")
    def test_a_fresh_build_reproduces_them(self):
        ran = 0
        for weapon in WEAPONS:
            if not all((gf.REF_DIR / f).is_file() for f in gf.WEAPONS[weapon].files().values()):
                continue
            ran += 1
            with tempfile.TemporaryDirectory() as tmp:
                res = gf.build(gf.WEAPONS[weapon], out_dir=Path(tmp))
                self.assertEqual(set(res["frames"]), {p.stem for p in installed(weapon)}, weapon)
                for p in installed(weapon):
                    self.assertEqual(p.read_bytes(), res["frames"][p.stem]["path"].read_bytes(), p.name)
                    self.assertEqual(res["frames"][p.stem]["cuts"], 0, p.name)
        if not ran:
            self.skipTest("no weapon's Gemini sources are here")


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class ScreenTests(unittest.TestCase):
    def test_they_stand_where_the_build_put_them(self):
        for name, above in ABOVE_BAR.items():
            self.assertEqual(on_screen(name)[0], above, name)

    def test_the_ready_frames_are_x1_6_chgg(self):
        target = round(CHGGA0_ABOVE_BAR * HEIGHT_MULT)
        for weapon, name in READY.items():
            self.assertLessEqual(abs(on_screen(name)[0] - target), HEIGHT_TOLERANCE, weapon)
        self.assertEqual(on_screen("SDAXA0")[0], AXE_READY_ABOVE_BAR, "the ice axe stands taller")
        if HAVE_NUMPY:
            self.assertAlmostEqual(gf.WEAPONS["ice_axe"].height_mult * CHGGA0_ABOVE_BAR, AXE_READY_ABOVE_BAR)

    def test_the_firing_frames_kick_up_and_right(self):
        for weapon, (a_name, b_name) in KICKED.items():
            a, b = (read_grab(lump_path(n).read_bytes()) for n in (a_name, b_name))
            self.assertEqual((a[0] - b[0], b[1] - a[1]), (KICK[0], -KICK[1]), weapon)
        self.assertEqual(read_grab(lump_path("SDRKA0").read_bytes()), read_grab(lump_path("SDRKB0").read_bytes()),
                         "the ROKS-3 does not kick: B is the gun let go, in A's pose")
        if HAVE_NUMPY:
            self.assertEqual(gf.KICK, KICK)

    def test_each_flash_sits_over_its_gun(self):
        for flash, gun in FLASH_OVER.items():
            f_above, f_x0, f_x1, _ = on_screen(flash)
            g_above, g_x0, g_x1, _ = on_screen(gun)
            self.assertTrue(f_x0 < g_x1 and g_x0 < f_x1, (flash, gun))
            self.assertLessEqual(abs(f_above - g_above), 30, (flash, gun))

    def test_the_arms_run_on_under_the_bar(self):
        """The arms leave the view with no cut edge: every held frame's
        bottom row lies under the status bar (bar on) and under the screen
        bottom (bar off, the weapon drawn BAR_LIFT lower). The lumps are
        cropped tight, so their left and right borders are the drawing's own
        outline (the muzzle, the Katyusha's butt plate); gemini_frames
        measures cut edges on the uncropped canvas, 0 for every lump
        (test_a_fresh_build_reproduces_them)."""
        for p in all_lumps():
            if p.stem in FLASH_OVER:
                continue
            _, _, _, bottom = on_screen(p.stem)
            self.assertGreaterEqual(bottom, VIEW_H, p.name)
            self.assertGreaterEqual(bottom + BAR_LIFT, SCREEN_H, p.name)

    def test_rgba_hard_alpha_and_palette_v2(self):
        v2 = set(palette_mod.colours(2))
        for p in all_lumps():
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
            for p in all_lumps() + [ASSET_SPRITES / "pickups" / "SDHPA0.png"]:
                self.assertIn(f"sprites/{p.name}", names)
                self.assertEqual(zf.read(f"sprites/{p.name}"), p.read_bytes())
            for weapon in WEAPONS:
                self.assertFalse([n for n in names if n.startswith(f"sprites/{weapon}/")], "the folder is dropped")
            self.assertFalse([n for n in names if "gemini" in n.lower()], "no source image ships (D77)")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


class LicenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))

    def test_the_rows_say_gemini_and_that_the_sources_stay_home(self):
        for name in sorted(CANVASES):
            found = [r for r in self.rows if r.covers(f"sprites/{name}.png")]
            self.assertEqual(len(found), 1, f"{name}: {len(found)} rows in docs/art/LICENSES.md")
            row = found[0]
            self.assertTrue(row.own_work, name)
            self.assertEqual(row.required, licences.OWN_WORK_CREDITS, name)
            self.assertIn("generated by the project lead with Google Gemini", row.origin, name)
            self.assertIn("processed into pixel art", row.origin, name)
            self.assertIn("the source images are not distributed", row.origin, name)

    def test_the_release_names_the_five(self):
        text = release.AI_DISCLOSURE[release.LANG_ENGLISH]
        for weapon in ("PPSh-41", "IZh-58", "RPG-7", "ROKS-3", "hand Katyusha", "ice axe"):
            self.assertIn(weapon, text)
        self.assertIn("Google Gemini", release.AI_DISCLOSURE[release.LANG_RUSSIAN])


class OverlayTests(unittest.TestCase):
    def test_recorded_as_installed(self):
        pairs = {(old, ours) for _, renames, _, _ in WEAPONS.values() for old, ours in renames.items()}
        self.assertLessEqual(pairs - {("BFUG", "SDHP")}, set(mdo.INSTALLED_WEAPON_FRAMES))
        self.assertIn(("BFUG", "SDHP"), mdo.INSTALLED)
        self.assertLessEqual({ours for _, ours in pairs}, mdo.installed_sprites())

    def test_the_overlay_names_nothing_of_the_five(self):
        ours = {n for _, renames, _, _ in WEAPONS.values() for n in renames.values()}
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & (RETIRED | ours), swap)
            self.assertNotIn(swap.zs, {f"weapons/{v[0]}" for v in WEAPONS.values()}, swap)

    def test_the_overlay_reads_the_states_as_the_engine_does(self):
        for weapon, (_, renames, _, _) in WEAPONS.items():
            text = zs(weapon).read_text(encoding="utf-8")
            for old, new in renames.items():
                self.assertEqual(mdo.state_letters(text, old), "", weapon)
                self.assertEqual(mdo.state_letters(text, new),
                                 "".join(sorted({f for r in BEFORE_D84[weapon] if r[1] == old for f in r[2]})),
                                 f"{weapon} {new}")


if __name__ == "__main__":
    unittest.main()
