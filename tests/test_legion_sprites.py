"""D54 (2026-10-14): the Liberty Legion trooper wears its own sprites.

The CEO approved cell C of the Legion sweep (D48) and, after it was redone
so the corpse lies flat, its death (D54, "Muerte legion OK"): the full set
of 70 `SDLT` lumps rendered by `tools/art/gen_legion.py --full` into
`work/art/enemies/legion/full_C/` ships from `assets/sprites/legion/`.
MOD-SPEC 6.3, "The Legion trooper, installed by D54". What is checked, and
why:

  behaviour  the trooper's States block is the one that stood before D54,
             line for line (label, frame letters, tics, flags, action,
             flow), with only SPOS renamed SDLT: not one tic moves
  sprite     no state anywhere names SPOS any more, MOD-SPEC 5.1 no longer
             declares it, and every frame a state uses has its lumps
  files      assets/sprites/legion/ holds exactly the 70 lumps: frames A-G
             in eight separate rotations (no mirrored pairs), H-U in
             rotation 0; each has a grAb chunk before its image data,
             centred (left = width / 2) with the floor line inside the
             canvas; where work/ exists each is byte-identical to the
             approved render, never to the superseded old_death/ one
  package    the built PK3 carries them flat as sprites/<NAME>.png, every
             rotation set is complete for check_pk3, and each has a
             licence row
  overlay    the draft overlay carries nothing of the Legion

Freedoom's DeadShotgunGuy (editor number 19) is not ours and is not touched:
it derives from Doom's ShotgunGuy, not from SD_LegionTrooper, so it keeps
showing the IWAD's SPOS L corpse (no map of ours places it).

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
TROOPER_ZS = SRC_DIR / "zscript" / "monsters" / "legion_trooper.zs"
LEGION_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "legion"
WORK_FULL_C = PROJECT_ROOT / "work" / "art" / "enemies" / "legion" / "full_C"
sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
OLD, NEW = "SPOS", "SDLT"
ROTATED_FRAMES = "ABCDEFG"            # walk A-D, aim E, fire F, pain G: eight rotations each
FLAT_FRAMES = "HIJKLMNOPQRSTU"        # death H-L, gib M-U: rotation 0
ROTATIONS_8 = "12345678"
EXPECTED_LUMPS = ({f"{NEW}{f}{r}" for f in ROTATED_FRAMES for r in ROTATIONS_8}
                  | {f"{NEW}{f}0" for f in FLAT_FRAMES})

# The States block as it stood before D54, with Freedoom's SPOS, read from
# src/zscript/monsters/legion_trooper.zs (HEAD 0182785) on 2026-10-14 before
# the swap. One row per line: (label, sprite, frames, tics, rest) for a
# state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
BEFORE_D54 = (
    ("Spawn", "SPOS", "AB", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", "SPOS", "AABBCCDD", 3, "A_Chase"),
    ("See", "->", "Loop", 0, ""),
    ("Missile", "SPOS", "E", 10, "A_FaceTarget"),
    ("Missile", "SPOS", "F", 10, "Bright A_SD_Hitscan(SD_TROOPER_SHOTS, SD_TROOPER_HIT_DICE, SD_TROOPER_HIT_MULT)"),
    ("Missile", "SPOS", "E", 10, ""),
    ("Missile", "->", "Goto See", 0, ""),
    ("Pain", "SPOS", "G", 3, ""),
    ("Pain", "SPOS", "G", 3, "A_Pain"),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", "SPOS", "H", 5, ""),
    ("Death", "SPOS", "I", 5, "A_Scream"),
    ("Death", "SPOS", "J", 5, "A_NoBlocking"),
    ("Death", "SPOS", "K", 5, ""),
    ("Death", "SPOS", "L", -1, ""),
    ("Death", "->", "Stop", 0, ""),
    ("XDeath", "SPOS", "M", 5, ""),
    ("XDeath", "SPOS", "N", 5, 'A_StartSound("sd/mon/legiontrooper/xdeath", CHAN_VOICE)'),
    ("XDeath", "SPOS", "O", 5, "A_NoBlocking"),
    ("XDeath", "SPOS", "PQRST", 5, ""),
    ("XDeath", "SPOS", "U", -1, ""),
    ("XDeath", "->", "Stop", 0, ""),
    ("Raise", "SPOS", "L", 5, ""),
    ("Raise", "SPOS", "KJIH", 5, ""),
    ("Raise", "->", "Goto See", 0, ""),
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


def states() -> list[tuple]:
    """Every line of the trooper's States block, in order (see BEFORE_D54)."""
    body = states_block(strip_comments(TROOPER_ZS.read_text(encoding="utf-8")))
    label, rows = None, []
    for line in body.splitlines():
        if not line.strip():
            continue
        if (m := RE_LABEL.match(line)):
            label = m.group(1)
        elif (m := RE_STATE.match(line)):
            rows.append((label, m.group(1), m.group(2), int(m.group(3)), m.group(4)))
        elif (m := RE_FLOW.match(line)):
            rows.append((label, "->", " ".join(m.group(1).split()), 0, ""))
        else:
            raise AssertionError(f"legion_trooper.zs: unparsed States line {line!r}")
    return rows


def installed() -> list[Path]:
    return sorted(LEGION_SPRITES.glob("*.png")) if LEGION_SPRITES.is_dir() else []


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d54_ones_but_for_the_sprite_name(self):
        expected = [(lb, NEW if sp == OLD else sp, fr, tics, rest) for lb, sp, fr, tics, rest in BEFORE_D54]
        self.assertEqual(states(), expected)

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states()), totals(BEFORE_D54))

    def test_the_parser_sees_every_line(self):
        self.assertEqual(sum(1 for r in states() if r[1] != "->"), 19)


class SpriteTests(unittest.TestCase):
    def test_every_state_names_sdlt(self):
        self.assertEqual({r[1] for r in states() if r[1] != "->"}, {NEW})

    def test_no_state_names_spos(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertNotIn(OLD, names, f"{path.name} still names {OLD}")

    def test_mod_spec_retires_spos(self):
        self.assertNotIn(OLD, check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC))

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for _, sprite, frames, _, _ in (r for r in states() if r[1] != "->"):
            for f in frames:
                rots = ROTATIONS_8 if f in ROTATED_FRAMES else "0"
                for r in rots:
                    self.assertIn(f"{sprite}{f}{r}", names)

    def test_every_installed_frame_is_used(self):
        used = {f for r in states() if r[1] != "->" for f in r[2]}
        self.assertEqual(used, set(ROTATED_FRAMES + FLAT_FRAMES))


class FileTests(unittest.TestCase):
    def test_exactly_the_70_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 70)

    def test_nothing_but_the_lumps_in_the_folder(self):
        if LEGION_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in LEGION_SPRITES.iterdir()),
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
            self.assertTrue(0 < top <= height, f"{p}: floor line {top} outside the {height}-px canvas")

    def test_one_canvas_per_frame_across_rotations(self):
        """The eight rotations of a frame share their canvas and offsets, so
        the trooper does not jump as he turns."""
        for f in ROTATED_FRAMES:
            seen = set()
            for r in ROTATIONS_8:
                data = (LEGION_SPRITES / f"{NEW}{f}{r}.png").read_bytes()
                seen.add((struct.unpack(">II", data[16:24]), read_grab(data)))
            self.assertEqual(len(seen), 1, f"{NEW}{f}: {seen}")

    @unittest.skipUnless(WORK_FULL_C.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for p in installed():
            source = WORK_FULL_C / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless((WORK_FULL_C / "old_death").is_dir(), "work/ not present (CI has no work/)")
    def test_the_death_is_the_redone_one(self):
        """D54 approved the redone death (the corpse lies flat): the old L0
        and U0 stay in work/, superseded, and did not ship."""
        for name in ("SDLTL0.png", "SDLTU0.png"):
            old = WORK_FULL_C / "old_death" / name
            if old.is_file():
                self.assertNotEqual((LEGION_SPRITES / name).read_bytes(), old.read_bytes(), name)


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
            self.assertFalse([n for n in names if n.startswith("sprites/legion")], "the set folder is dropped")

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
    def test_the_overlay_names_nothing_of_the_legion(self):
        for swap in mdo.SWAPS:
            self.assertNotIn(swap.placeholder, (OLD, NEW))
            self.assertNotIn(swap.draft, (OLD, NEW))
            self.assertNotIn("legion", swap.zs)

    def test_the_legion_is_recorded_as_installed(self):
        self.assertIn((OLD, NEW), mdo.INSTALLED_ENEMIES)
        self.assertIn(NEW, mdo.installed_sprites())


if __name__ == "__main__":
    unittest.main()
