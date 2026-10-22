"""D56 (2026-10-14): the Hybrid Stormtrooper and his bolt wear their own sprites.

REDRAWN by D109 and D114 (2026-10-22): the set that ships now is the
Google Gemini redraw built by `tools/art/gemini_enemy.py storm` into
`work/art/enemies_gemini/storm/` (MOD-SPEC 6.3, "The seven enemies redrawn
from Google Gemini"), same lump names, frame letters and rotations, so the
state machine below is untouched. The `files` checks read that build; the
rig render named below is history (the generator is kept), and a lump of
it shipping again is a failure. tests/test_gemini_enemy_install.py holds
the install itself.

The CEO approved cell E of the Stormtrooper sweep (D48, "muy macarra"), its
full set but for the death (D53), and the redone death, the corpse lying
flat (D56, "Muerte OK"): the 77 `SDHS` and 5 `SDBL` lumps rendered by
`tools/art/gen_storm.py --full` (death redone by `--death`) into
`work/art/enemies/storm/full_E/` ship from `assets/sprites/storm/`. MOD-SPEC
6.3, "The Hybrid Stormtrooper and his bolt, installed by D56". The same
pattern as the Legion's (tests/test_legion_sprites.py, D54). What is
checked, and why:

  behaviour  SD_Stormtrooper's and SD_StormBolt's States blocks are the ones
             that stood at HEAD 8b4ef67, before D56, line for line (label,
             frame letters, tics, Bright, action, flow; the empty `Melee:`
             label that falls through to `Missile:` included), with only
             TROO renamed SDHS and BAL1 renamed SDBL: not one tic moves
  sprite     no state anywhere names TROO or BAL1 any more, MOD-SPEC 5.1 no
             longer declares them, and every frame a state uses has its
             lumps
  files      assets/sprites/storm/ holds exactly the 82 lumps: SDHS A-H in
             eight separate rotations (no mirrored pairs: the chrome plate
             is on his right, the armband on his left), I-U in rotation 0,
             SDBL A-E in rotation 0; each has a grAb chunk before its image
             data, centred (left = width / 2) with its offset inside the
             canvas; where work/ exists each is byte-identical to the
             approved render and never to the superseded old_death/ one, and
             the proposed claw frames V W did not ship; the death and gib
             carry D49's dark-red blood (flag_red 0-5), checked where Pillow
             is installed
  package    the built PK3 carries them flat as sprites/<NAME>.png, every
             rotation set is complete for check_pk3, and each has a
             licence row
  overlay    the draft overlay never carried the Stormtrooper and names it
             nowhere

Freedoom's DeadDoomImp (editor number 20) and Doom's StealthDoomImp are not
ours and are not touched: they derive from Doom's DoomImp, not from
SD_Stormtrooper, so they keep the IWAD's TROO; Doom's DoomImpBall keeps BAL1
(no map of ours places 20 or a stealth imp).

Stdlib only, but for the blood check, which needs Pillow.
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
STORM_ZS = SRC_DIR / "zscript" / "monsters" / "stormtrooper.zs"
BOLT_ZS = SRC_DIR / "zscript" / "monsters" / "storm_bolt.zs"
STORM_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "storm"
WORK_FULL_E = PROJECT_ROOT / "work" / "art" / "enemies" / "storm" / "full_E"   # the rig set (and the bolt SDBL)
WORK_GEMINI = PROJECT_ROOT / "work" / "art" / "enemies_gemini" / "storm"       # SDHS since D109
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
OLD, NEW = "TROO", "SDHS"
BOLT_OLD, BOLT_NEW = "BAL1", "SDBL"
RENAMES = {OLD: NEW, BOLT_OLD: BOLT_NEW}
ROTATED_FRAMES = "ABCDEFGH"           # walk A-D, attack E-G, pain H: eight rotations each
FLAT_FRAMES = "IJKLMNOPQRSTU"         # death I-M, gib N-U: rotation 0
BOLT_FRAMES = "ABCDE"                 # flight A-B, burst C-E: rotation 0
ROTATIONS_8 = "12345678"
EXPECTED_LUMPS = ({f"{NEW}{f}{r}" for f in ROTATED_FRAMES for r in ROTATIONS_8}
                  | {f"{NEW}{f}0" for f in FLAT_FRAMES}
                  | {f"{BOLT_NEW}{f}0" for f in BOLT_FRAMES})
BLOOD_MAX_INDEX = 5                   # D49: the drawn blood is flag_red 0-5 (gen_storm.py)

# The States blocks as they stood before D56, with Freedoom's TROO and BAL1,
# read from src/zscript/monsters/stormtrooper.zs and storm_bolt.zs at HEAD
# 8b4ef67 on 2026-10-14 before the swap. One row per line: (label, ":", "",
# 0, "") for a label, (label, sprite, frames, tics, rest) for a state,
# (label, "->", flow, 0, "") for Goto/Loop/Stop.
STORM_BEFORE_D56 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "TROO", "AB", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", ":", "", 0, ""),
    ("See", "TROO", "AABBCCDD", 3, "A_Chase"),
    ("See", "->", "Loop", 0, ""),
    ("Melee", ":", "", 0, ""),
    ("Missile", ":", "", 0, ""),
    ("Missile", "TROO", "EF", 8, "A_FaceTarget"),
    ("Missile", "TROO", "G", 6,
     'A_SD_MeleeOrMissile(SD_STORM_MELEE_DICE, SD_STORM_MELEE_MULT, "sd/mon/stormtrooper/melee", "SD_StormBolt")'),
    ("Missile", "->", "Goto See", 0, ""),
    ("Pain", ":", "", 0, ""),
    ("Pain", "TROO", "H", 2, ""),
    ("Pain", "TROO", "H", 2, "A_Pain"),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "TROO", "I", 8, ""),
    ("Death", "TROO", "J", 8, "A_Scream"),
    ("Death", "TROO", "K", 6, ""),
    ("Death", "TROO", "L", 6, "A_NoBlocking"),
    ("Death", "TROO", "M", -1, ""),
    ("Death", "->", "Stop", 0, ""),
    ("XDeath", ":", "", 0, ""),
    ("XDeath", "TROO", "N", 5, ""),
    ("XDeath", "TROO", "O", 5, 'A_StartSound("sd/mon/stormtrooper/xdeath", CHAN_VOICE)'),
    ("XDeath", "TROO", "P", 5, ""),
    ("XDeath", "TROO", "Q", 5, "A_NoBlocking"),
    ("XDeath", "TROO", "RST", 5, ""),
    ("XDeath", "TROO", "U", -1, ""),
    ("XDeath", "->", "Stop", 0, ""),
    ("Raise", ":", "", 0, ""),
    ("Raise", "TROO", "ML", 8, ""),
    ("Raise", "TROO", "KJI", 6, ""),
    ("Raise", "->", "Goto See", 0, ""),
)
BOLT_BEFORE_D56 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "BAL1", "AB", 4, "Bright"),
    ("Spawn", "->", "Loop", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "BAL1", "CDE", 6, "Bright"),
    ("Death", "->", "Stop", 0, ""),
)


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


def states(path: Path) -> list[tuple]:
    """Every line of a States block, labels included, in order (see STORM_BEFORE_D56)."""
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
    return sorted(STORM_SPRITES.glob("*.png")) if STORM_SPRITES.is_dir() else []


def blood_colours() -> set[tuple[int, int, int]]:
    """flag_red 0-5, the band D49's drawn blood lives in."""
    data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    ramp = next(r for r in data["ramps"] if r["name"] == "flag_red")
    return {tuple(c) for c in ramp["colours"][:BLOOD_MAX_INDEX + 1]}


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d56_ones_but_for_the_sprite_names(self):
        for path, before in ((STORM_ZS, STORM_BEFORE_D56), (BOLT_ZS, BOLT_BEFORE_D56)):
            expected = [(lb, RENAMES.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in before]
            self.assertEqual(states(path), expected, path.name)

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states(STORM_ZS)), totals(STORM_BEFORE_D56))
        self.assertEqual(totals(states(BOLT_ZS)), totals(BOLT_BEFORE_D56))

    def test_melee_still_falls_through_to_missile(self):
        rows = states(STORM_ZS)
        i = rows.index(("Melee", ":", "", 0, ""))
        self.assertEqual(rows[i + 1], ("Missile", ":", "", 0, ""))

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states(STORM_ZS))), 19)
        self.assertEqual(len(frame_rows(states(BOLT_ZS))), 2)


class SpriteTests(unittest.TestCase):
    def test_every_state_names_our_sprites(self):
        self.assertEqual({r[1] for r in frame_rows(states(STORM_ZS))}, {NEW})
        self.assertEqual({r[1] for r in frame_rows(states(BOLT_ZS))}, {BOLT_NEW})

    def test_no_state_names_troo_or_bal1(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & {OLD, BOLT_OLD}, f"{path.name} still names {names & {OLD, BOLT_OLD}}")

    def test_mod_spec_retires_troo_and_bal1(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertNotIn(OLD, declared)
        self.assertNotIn(BOLT_OLD, declared)

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for _, sprite, frames, _, _ in frame_rows(states(STORM_ZS)) + frame_rows(states(BOLT_ZS)):
            for f in frames:
                rots = ROTATIONS_8 if sprite == NEW and f in ROTATED_FRAMES else "0"
                for r in rots:
                    self.assertIn(f"{sprite}{f}{r}", names)

    def test_every_installed_frame_is_used(self):
        self.assertEqual({f for r in frame_rows(states(STORM_ZS)) for f in r[2]},
                         set(ROTATED_FRAMES + FLAT_FRAMES))
        self.assertEqual({f for r in frame_rows(states(BOLT_ZS)) for f in r[2]}, set(BOLT_FRAMES))


class FileTests(unittest.TestCase):
    def test_exactly_the_82_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 82)
        self.assertEqual(sum(n.startswith(NEW) for n in EXPECTED_LUMPS), 77)

    def test_nothing_but_the_lumps_in_the_folder(self):
        """No GIF, no metrics.json, no blood_* comparison, no old_death/,
        no proposed_melee/: only the lumps ship."""
        if STORM_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in STORM_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS))

    def test_every_sprite_carries_centred_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            left, top = grab
            self.assertEqual(left, width // 2, p)
            self.assertTrue(0 < top <= height, f"{p}: offset {top} outside the {height}-px canvas")

    def test_one_canvas_per_frame_across_rotations(self):
        """The eight rotations of a frame share their canvas and offsets, so
        the Stormtrooper does not jump as he turns."""
        for f in ROTATED_FRAMES:
            seen = set()
            for r in ROTATIONS_8:
                data = (STORM_SPRITES / f"{NEW}{f}{r}.png").read_bytes()
                seen.add((struct.unpack(">II", data[16:24]), read_grab(data)))
            self.assertEqual(len(seen), 1, f"{NEW}{f}: {seen}")

    @unittest.skipUnless(WORK_GEMINI.is_dir() and WORK_FULL_E.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        """SDHS from the Gemini build (D109); the bolt SDBL, not redrawn,
        from the rig render."""
        for p in installed():
            source = (WORK_GEMINI if p.stem.startswith(NEW) else WORK_FULL_E) / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(WORK_FULL_E.is_dir(), "work/ not present (CI has no work/)")
    def test_the_rig_set_no_longer_ships(self):
        """D109: every lump of the set is the Gemini redraw, none the rig
        render it replaced (that set stays in work/, history)."""
        for p in installed():
            if not p.stem.startswith(NEW):
                continue
            old = WORK_FULL_E / p.name
            if old.is_file():
                self.assertNotEqual(p.read_bytes(), old.read_bytes(), p.name)

    def test_the_proposed_claw_frames_did_not_ship(self):
        """V and W (proposed_melee/) show only if Melee is split from
        Missile, a ZScript change nobody approved."""
        self.assertFalse([p for p in installed() if p.stem[4] in "VW"])

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_deaths_bleed_dark_red(self):
        """D49: death I-M and gib N-U carry flag_red 0-5 blood (the Gemini
        redraw, D109: 7 to 166 pixels a frame, the derived gib's procedural
        blood the most). The rig set's "standing frames carry none" is gone:
        the redrawn armband's red is flag_red too (15 px on SDHSA1)."""
        red = blood_colours()

        def count(name: str) -> int:
            with Image.open(STORM_SPRITES / f"{name}.png") as img:
                raw = img.convert("RGBA").tobytes()
            return sum(1 for i in range(0, len(raw), 4) if raw[i + 3] and tuple(raw[i:i + 3]) in red)

        for f in FLAT_FRAMES:
            self.assertGreater(count(f"{NEW}{f}0"), 0, f"{NEW}{f}0 has no flag_red 0-{BLOOD_MAX_INDEX} blood")


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
            self.assertFalse([n for n in names if n.startswith("sprites/storm")], "the set folder is dropped")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        missing = sorted(n for n in EXPECTED_LUMPS if n not in declared)
        self.assertEqual([], missing, "no row in docs/art/LICENSES.md")


class OverlayTests(unittest.TestCase):
    def test_the_overlay_names_nothing_of_the_stormtrooper(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & {OLD, NEW, BOLT_OLD, BOLT_NEW}, swap)
            self.assertNotIn("storm", swap.zs)

    def test_the_stormtrooper_is_recorded_as_installed(self):
        self.assertIn((OLD, NEW), mdo.INSTALLED_ENEMIES)
        self.assertIn((BOLT_OLD, BOLT_NEW), mdo.INSTALLED_ENEMIES)
        self.assertTrue({NEW, BOLT_NEW} <= mdo.installed_sprites())


if __name__ == "__main__":
    unittest.main()
