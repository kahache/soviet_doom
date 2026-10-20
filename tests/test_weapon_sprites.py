"""D48 (2026-10-14): the six weapon pickups are our own sprites.

The CEO approved hand E and six weapons as drawn, then found the hand
deformed in MAP01; so only the world pickups shipped: `SDAP` (the ice axe,
option C), `SDTP`, `SDIP`, `SDPQ`, `SDRP`, `SDKP`. MOD-SPEC 6.3, "Installed
since D48". What is checked, and why:

  behaviour  every States block of the six weapons is the one that stood
             before D48, line for line (label, frame letters, tics, flags,
             action, flow), with only the pickup's four-letter name
             changed: the swap is cosmetic, not one tic moves (and, since
             N17, the TT-33's held and flash names, and since D79 the
             PPSh-41's, HELD_RENAMED; those installs have their own suites,
             tests/test_tt33_sprites.py and tests/test_ppsh_sprites.py)
  pickups    each Spawn state shows its SD..P sprite, and no state names the
             retired IWAD pickups (CSAW, PIST, SHOT, MGUN, LAUN, PLAS); the
             held and flash frames of the other five are still the IWAD's
             (hand held back), and the Katyusha (being redrawn) is untouched
  files      assets/sprites/<weapon>/ holds exactly the six pickup PNGs
             (beside the TT-33's held and flash frames since N17 and the
             PPSh-41's since D79), each with
             a grAb chunk before its image data (GZDoom's offsets), and,
             where work/ exists, byte-identical to the render
  package    the built PK3 carries them as sprites/<NAME>.png, check_pk3
             passes, and every one has a licence row

Stdlib only.
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
WEAPONS_ZS = SRC_DIR / "zscript" / "weapons"
ASSET_SPRITES = PROJECT_ROOT / "assets" / "sprites"
WORK_WEAPONS = PROJECT_ROOT / "work" / "art" / "weapons"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from _n9_sound_hooks import with_sound_hooks  # noqa: E402  (N9's sound hooks, the only other edit)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# IWAD placeholder -> our pickup (MOD-SPEC 6.3). Nothing else was renamed.
RENAMED = {"CSAW": "SDAP", "PIST": "SDTP", "SHOT": "SDIP", "MGUN": "SDPQ", "LAUN": "SDRP", "PLAS": "SDKP"}

# weapon folder under assets/sprites/ (and work/art/weapons/) -> its .zs
FOLDERS = {"ice_axe": "ice_axe.zs", "tt33": "tokarev.zs", "izh": "izh.zs",
           "ppsh": "ppsh.zs", "rpg7": "rpg7.zs", "roks3": "roks3.zs"}

# The held and flash sprites still on Freedoom (the hand is being redrawn).
# The TT-33's left with N17 (2026-10-15), the PPSh-41's with D79
# (2026-10-20): HELD_RENAMED.
STILL_IWAD = {"ice_axe.zs": {"PUNG"}, "izh.zs": {"SHTG", "SHTF"},
              "rpg7.zs": {"MISG", "MISF"}, "roks3.zs": {"PLSG", "PLSF"}}

# Held and flash sprites installed after D48, per weapon: IWAD -> ours.
# N17 (2026-10-15): the TT-33 in the D61 hands (tests/test_tt33_sprites.py).
# D79 (2026-10-20): the PPSh-41 from the CEO's Gemini pair (tests/test_ppsh_sprites.py).
HELD_RENAMED = {"tokarev.zs": {"PISG": "SDTT", "PISF": "SDTF"},
                "ppsh.zs": {"CHGG": "SDPP", "CHGF": "SDPF"}}

# The States blocks as they stood before D48, with the IWAD names, read from
# src/zscript/weapons/ on 2026-10-14 before the swap. One row per line:
# (label, sprite, frames, tics, rest) for a state, (label, "->", flow, 0, "")
# for Goto/Loop/Stop.
BEFORE_D48 = {
    "ice_axe.zs": (
        ("Ready", "PUNG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "PUNG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "PUNG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "PUNG", "B", 5, ""),
        ("Fire", "PUNG", "C", 5, "A_SD_IceAxeSwing"),
        ("Fire", "PUNG", "D", 6, ""),
        ("Fire", "PUNG", "C", 5, ""),
        ("Fire", "PUNG", "B", 6, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Spawn", "CSAW", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
    "tokarev.zs": (
        ("Ready", "PISG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "PISG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "PISG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "PISG", "A", 4, ""),
        ("Fire", "PISG", "B", 0, "A_GunFlash"),
        ("Fire", "PISG", "B", 6, "A_FireBullets(SD_TT_SPREAD, 0, SD_TT_BULLETS, SD_TT_DAMAGE)"),
        ("Fire", "PISG", "C", 3, ""),
        ("Fire", "PISG", "B", 3, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Flash", "PISF", "A", 5, "Bright A_Light1"),
        ("Flash", "->", "Goto LightDone", 0, ""),
        ("Spawn", "PIST", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
    "izh.zs": (
        ("Ready", "SHTG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "SHTG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "SHTG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "SHTG", "A", 3, ""),
        ("Fire", "SHTG", "A", 6, "A_SD_FireIzh"),
        ("Fire", "SHTG", "B", 4, ""),
        ("Fire", "SHTG", "C", 4, ""),
        ("Fire", "SHTG", "A", 3, 'A_JumpIf(invoker.barrels <= 0, "Reload")'),
        ("Fire", "SHTG", "A", 3, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Reload", "SHTG", "D", 6, 'A_StartSound("sd/weapon/izh/reload", CHAN_WEAPON)'),
        ("Reload", "SHTG", "C", 8, ""),
        ("Reload", "SHTG", "B", 8, ""),
        ("Reload", "SHTG", "A", 8, "A_SD_ReloadIzh"),
        ("Reload", "->", "Goto Ready", 0, ""),
        ("Flash", "SHTF", "A", 4, "Bright A_Light1"),
        ("Flash", "SHTF", "B", 3, "Bright A_Light2"),
        ("Flash", "->", "Goto LightDone", 0, ""),
        ("Spawn", "SHOT", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
    "ppsh.zs": (
        ("Ready", "CHGG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "CHGG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "CHGG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "CHGG", "A", 0, "A_GunFlash"),
        ("Fire", "CHGG", "A", 3, "A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE)"),
        ("Fire", "CHGG", "B", 0, "A_GunFlash"),
        ("Fire", "CHGG", "B", 3, "A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE)"),
        ("Fire", "CHGG", "B", 0, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Flash", "CHGF", "A", 3, "Bright A_Light1"),
        ("Flash", "->", "Goto LightDone", 0, ""),
        ("Spawn", "MGUN", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
    "rpg7.zs": (
        ("Ready", "MISG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "MISG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "MISG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "MISG", "B", 8, "A_GunFlash"),
        ("Fire", "MISG", "B", 14, 'A_FireProjectile("SD_Pg7Grenade")'),
        ("Fire", "MISG", "B", 4, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Flash", "MISF", "A", 3, "Bright A_Light1"),
        ("Flash", "MISF", "B", 4, "Bright"),
        ("Flash", "MISF", "CD", 4, "Bright A_Light2"),
        ("Flash", "->", "Goto LightDone", 0, ""),
        ("Spawn", "LAUN", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
    "roks3.zs": (
        ("Ready", "PLSG", "A", 1, "A_WeaponReady"),
        ("Ready", "->", "Loop", 0, ""),
        ("Deselect", "PLSG", "A", 1, "A_Lower"),
        ("Deselect", "->", "Loop", 0, ""),
        ("Select", "PLSG", "A", 1, "A_Raise"),
        ("Select", "->", "Loop", 0, ""),
        ("Fire", "PLSG", "A", 0, "A_GunFlash"),
        ("Fire", "PLSG", "A", 3, "Bright A_SD_FireRoks3"),
        ("Fire", "PLSG", "B", 20, "A_ReFire"),
        ("Fire", "->", "Goto Ready", 0, ""),
        ("Flash", "PLSF", "A", 3, "Bright A_Light1"),
        ("Flash", "->", "Goto LightDone", 0, ""),
        ("Spawn", "PLAS", "A", -1, ""),
        ("Spawn", "->", "Stop", 0, ""),
    ),
}

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def states_block(text: str) -> str:
    """The body of the first `States { ... }` block, braces balanced."""
    m = re.search(r"\bStates\s*\{", text)
    if m is None:
        raise AssertionError("no States block")
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[m.end():i - 1]


def states(zs_file: str) -> list[tuple]:
    """Every line of the weapon's States block, in order (see BEFORE_D48)."""
    body = states_block(strip_comments((WEAPONS_ZS / zs_file).read_text(encoding="utf-8")))
    label, rows = None, []
    for line in body.splitlines():
        if not line.strip():
            continue
        if (m := RE_LABEL.match(line)):
            label = m.group(1)
        elif (m := RE_STATE.match(line)):
            rows.append((label, m.group(1), m.group(2), int(m.group(3)), m.group(4)))
        elif (m := RE_FLOW.match(line)):
            rows.append((label, "->", re.sub(r"\s+", " ", m.group(1)), 0, ""))
        else:
            raise AssertionError(f"{zs_file}: unparsed States line {line!r}")
    return rows


def read_grab(data: bytes) -> tuple[int, int] | None:
    """The grAb chunk (ZDoom's sprite offsets) if it comes before IDAT."""
    i = len(PNG_SIGNATURE)
    while i + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[i:i + 8])
        if kind == b"grAb":
            return struct.unpack(">ii", data[i + 8:i + 16])
        if kind == b"IDAT":
            return None
        i += 12 + length
    return None


PICKUP_FILES = {f"{ours}A0.png" for ours in RENAMED.values()}


def installed() -> list[Path]:
    """The weapon pickups: the six weapon folders only, pickup lumps only.
    Other sets share assets/sprites/ (the Legion's legion/ since D54,
    tests/test_legion_sprites.py), and the TT-33's held and flash frames
    share tt33/ since N17 (tests/test_tt33_sprites.py), the PPSh-41's
    ppsh/ since D79 (tests/test_ppsh_sprites.py)."""
    return sorted(p for folder in FOLDERS for p in (ASSET_SPRITES / folder).glob("*.png")
                  if p.name in PICKUP_FILES)


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d48_ones_but_for_the_pickup_name(self):
        """...and for N9's sound hooks (tests/_n9_sound_hooks.py), which add
        actions and split one frame but move no tic (next test)."""
        for zs_file, before in BEFORE_D48.items():
            renamed = {**RENAMED, **HELD_RENAMED.get(zs_file, {})}
            expected = [(lb, renamed.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in before]
            self.assertEqual(states(zs_file), with_sound_hooks(zs_file, expected), zs_file)

    def test_tic_totals_per_label_unchanged(self):
        for zs_file, before in BEFORE_D48.items():
            totals: dict[str, int] = {}
            for lb, _, _, tics, _ in before:
                totals[lb] = totals.get(lb, 0) + tics
            now: dict[str, int] = {}
            for lb, _, _, tics, _ in states(zs_file):
                now[lb] = now.get(lb, 0) + tics
            self.assertEqual(now, totals, zs_file)

    def test_the_parser_sees_every_line(self):
        rows = states("ice_axe.zs")
        self.assertEqual(sum(1 for r in rows if r[1] != "->"), 9)
        with self.assertRaises(AssertionError):
            states_block("class X {}")


class PickupTests(unittest.TestCase):
    def test_each_spawn_state_shows_our_pickup(self):
        spawns = {}
        for zs_file in FOLDERS.values():
            spawn = [r for r in states(zs_file) if r[0] == "Spawn" and r[1] != "->"]
            self.assertEqual(len(spawn), 1, zs_file)
            spawns[zs_file] = spawn[0][1:4]
        self.assertEqual(spawns, {
            "ice_axe.zs": ("SDAP", "A", -1), "tokarev.zs": ("SDTP", "A", -1), "izh.zs": ("SDIP", "A", -1),
            "ppsh.zs": ("SDPQ", "A", -1), "rpg7.zs": ("SDRP", "A", -1), "roks3.zs": ("SDKP", "A", -1)})

    def test_held_and_flash_frames_stay_on_the_iwad(self):
        """The hand is being redrawn (D48): only the pickup changed name,
        but for the TT-33's held and flash frames, installed by N17, and
        the PPSh-41's, installed by D79."""
        self.assertEqual(set(STILL_IWAD) | set(HELD_RENAMED), set(FOLDERS.values()))
        for zs_file, iwad in STILL_IWAD.items():
            used = {r[1] for r in states(zs_file) if r[1] != "->" and r[0] != "Spawn"}
            self.assertEqual(used, iwad, zs_file)
        for zs_file, renamed in HELD_RENAMED.items():
            used = {r[1] for r in states(zs_file) if r[1] != "->" and r[0] != "Spawn"}
            self.assertEqual(used, set(renamed.values()), zs_file)

    def test_no_state_names_a_retired_pickup(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            code = strip_comments(path.read_text(encoding="utf-8"))
            for old in RENAMED:
                self.assertNotRegex(code, rf"(?m)^\s*{old}\s+[A-Z]", f"{path.name} still names {old}")

    def test_the_katyusha_is_untouched(self):
        used = {r[1] for r in states("katyusha.zs") if r[1] != "->"}
        self.assertEqual(used, {"BFGG", "BFGF", "BFUG"})

    def test_mod_spec_retires_the_old_pickups(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        for old in RENAMED:
            self.assertNotIn(old, declared, f"MOD-SPEC 5.1 still declares {old}")
        for iwad in STILL_IWAD.values():
            self.assertLessEqual(iwad, declared)


class FileTests(unittest.TestCase):
    def test_exactly_the_six_pickups_are_installed(self):
        got = {(p.parent.name, p.name) for p in installed()}
        want = {(folder, f"{RENAMED[old]}A0.png") for folder, old in
                zip(FOLDERS, ("CSAW", "PIST", "SHOT", "MGUN", "LAUN", "PLAS"))}
        self.assertEqual(got, want)

    def test_every_sprite_carries_its_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            self.assertIsNotNone(read_grab(data), f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")

    def test_pickups_stand_on_the_floor(self):
        """A pickup's top offset is its height (minus at most the axe's
        planted spike, PLANT_SINK 2 px), and it is centred."""
        for p in installed():
            data = p.read_bytes()
            width, height = struct.unpack(">II", data[16:24])
            left, top = read_grab(data)
            self.assertLessEqual(abs(left - width // 2), 1, p)
            self.assertIn(height - top, (0, 1, 2), p)

    @unittest.skipUnless(WORK_WEAPONS.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_render(self):
        for p in installed():
            source = WORK_WEAPONS / p.parent.name / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)


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

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))


if __name__ == "__main__":
    unittest.main()
