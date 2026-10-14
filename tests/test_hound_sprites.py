"""D55 (2026-10-14): the Reich hound wears its own sprites.

The CEO chose the German shepherd of cell A (D50, "Perro A") and approved
its full set (D55, "OK perro"): the 46 `SDHN` lumps rendered by
`tools/art/gen_hound.py --full` into `work/art/enemies/hound_gsd/full_A/`
ship from `assets/sprites/hound/`. MOD-SPEC 6.3, "The Reich rifleman and
the Reich hound, installed by D55". The same pattern as the Legion's
(tests/test_legion_sprites.py, D54), with one difference: the hound is
drawn symmetric, so frames A-H use Doom's MIRRORED PAIRS, eight-character
lumps such as `SDHNA2A8` (frame A, rotation 2, drawn flipped for rotation
8). What is checked, and why:

  behaviour  the hound's States block is the one that stood at HEAD
             8b4ef67, before D55, line for line (label, frame letters,
             tics, flags, action, flow), with only SARG renamed SDHN: not
             one tic moves
  sprite     no state anywhere names SARG any more, MOD-SPEC 5.1 no longer
             declares it, and every frame a state uses has all its
             rotations covered
  files      assets/sprites/hound/ holds exactly the 46 lumps: frames A-H as
             1, 2A8, 3A7, 4A6, 5 (each pair names the same frame twice), I-N
             in rotation 0; each has a grAb chunk before its image data,
             centred (left = width / 2, the axis a mirrored pair flips
             about) with the floor line inside the canvas; where work/
             exists each is byte-identical to the approved render; the
             death frames carry D49's dark-red blood (flag_red 0-5),
             checked where Pillow is installed
  package    the built PK3 carries them flat as sprites/<NAME>.png, every
             rotation set is complete for check_pk3 (which reads both
             halves of an eight-character name), and each has a licence row
  overlay    the draft overlay never carried the hound and names it nowhere

The death was judged at a 37-degree camera (gen_hound.py, "the full set"):
that is how the art was drawn, not anything the engine is told; the class
is unchanged. Freedoom's DeadDemon (editor number 21) and Doom's Spectre
(58) are not ours and are not touched: they derive from Doom's Demon, not
from SD_ReichHound, so they keep the IWAD's SARG (no map of ours places
either).

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
HOUND_ZS = SRC_DIR / "zscript" / "monsters" / "reich_hound.zs"
HOUND_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "hound"
WORK_FULL_A = PROJECT_ROOT / "work" / "art" / "enemies" / "hound_gsd" / "full_A"
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
OLD, NEW = "SARG", "SDHN"
ROTATED_FRAMES = "ABCDEFGH"           # gallop A-D, bite E-G, pain H: eight rotations each
FLAT_FRAMES = "IJKLMN"                # death I-N: rotation 0
ROTATIONS_8 = "12345678"
# Rotations 1 and 5 face the camera and away from it, drawn once; 2-4 are
# drawn and flipped for 8-6 (rig_core's mirror mode).
ROTATION_LUMPS = ("1", "2{f}8", "3{f}7", "4{f}6", "5")
EXPECTED_LUMPS = ({f"{NEW}{f}" + r.format(f=f) for f in ROTATED_FRAMES for r in ROTATION_LUMPS}
                  | {f"{NEW}{f}0" for f in FLAT_FRAMES})
BLOOD_MAX_INDEX = 5                   # D49: the drawn blood is flag_red 0-5 (gen_hound.py)

# The States block as it stood before D55, with Freedoom's SARG, read from
# src/zscript/monsters/reich_hound.zs at HEAD 8b4ef67 on 2026-10-14 before
# the swap. One row per line: (label, sprite, frames, tics, rest) for a
# state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
BEFORE_D55 = (
    ("Spawn", "SARG", "AB", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", "SARG", "AABBCCDD", 2, "Fast A_Chase"),
    ("See", "->", "Loop", 0, ""),
    ("Melee", "SARG", "EF", 8, "Fast A_FaceTarget"),
    ("Melee", "SARG", "G", 8, "Fast A_SD_Melee(SD_HOUND_MELEE_DICE, SD_HOUND_MELEE_MULT)"),
    ("Melee", "->", "Goto See", 0, ""),
    ("Pain", "SARG", "H", 2, "Fast"),
    ("Pain", "SARG", "H", 2, "Fast A_Pain"),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", "SARG", "I", 8, ""),
    ("Death", "SARG", "J", 8, "A_Scream"),
    ("Death", "SARG", "K", 4, ""),
    ("Death", "SARG", "L", 4, "A_NoBlocking"),
    ("Death", "SARG", "M", 4, ""),
    ("Death", "SARG", "N", -1, ""),
    ("Death", "->", "Stop", 0, ""),
    ("Raise", "SARG", "N", 5, ""),
    ("Raise", "SARG", "MLKJI", 5, ""),
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
    """Every line of the hound's States block, in order (see BEFORE_D55)."""
    body = states_block(strip_comments(HOUND_ZS.read_text(encoding="utf-8")))
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
            raise AssertionError(f"reich_hound.zs: unparsed States line {line!r}")
    return rows


def installed() -> list[Path]:
    return sorted(HOUND_SPRITES.glob("*.png")) if HOUND_SPRITES.is_dir() else []


def coverage(stems) -> dict[tuple[str, str], set[str]]:
    """(sprite, frame) -> the rotations its lumps fill: NAMEFR fills one,
    NAMEFRFR two (the second half is the flipped one)."""
    out: dict[tuple[str, str], set[str]] = {}
    for s in stems:
        halves = [s[4:6]] + ([s[6:8]] if len(s) == 8 else [])
        for frame, rotation in halves:
            out.setdefault((s[:4], frame), set()).add(rotation)
    return out


def blood_colours() -> set[tuple[int, int, int]]:
    """flag_red 0-5, the band D49's drawn blood lives in."""
    data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    ramp = next(r for r in data["ramps"] if r["name"] == "flag_red")
    return {tuple(c) for c in ramp["colours"][:BLOOD_MAX_INDEX + 1]}


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d55_ones_but_for_the_sprite_name(self):
        expected = [(lb, NEW if sp == OLD else sp, fr, tics, rest) for lb, sp, fr, tics, rest in BEFORE_D55]
        self.assertEqual(states(), expected)

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states()), totals(BEFORE_D55))

    def test_the_parser_sees_every_line(self):
        self.assertEqual(sum(1 for r in states() if r[1] != "->"), 14)


class SpriteTests(unittest.TestCase):
    def test_every_state_names_sdhn(self):
        self.assertEqual({r[1] for r in states() if r[1] != "->"}, {NEW})

    def test_no_state_names_sarg(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertNotIn(OLD, names, f"{path.name} still names {OLD}")

    def test_mod_spec_retires_sarg(self):
        self.assertNotIn(OLD, check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC))

    def test_every_frame_a_state_uses_is_covered(self):
        cov = coverage(p.stem for p in installed())
        for _, sprite, frames, _, _ in (r for r in states() if r[1] != "->"):
            for f in frames:
                want = set(ROTATIONS_8) if f in ROTATED_FRAMES else {"0"}
                self.assertEqual(cov.get((sprite, f)), want, f"{sprite}{f}")

    def test_every_installed_frame_is_used(self):
        used = {f for r in states() if r[1] != "->" for f in r[2]}
        self.assertEqual(used, set(ROTATED_FRAMES + FLAT_FRAMES))

    def test_coverage_reads_both_halves_of_a_pair(self):
        self.assertEqual(coverage(["SDHNA1", "SDHNA2A8", "SDHNI0"]),
                         {("SDHN", "A"): {"1", "2", "8"}, ("SDHN", "I"): {"0"}})


class FileTests(unittest.TestCase):
    def test_exactly_the_46_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 46)

    def test_nothing_but_the_lumps_in_the_folder(self):
        """No GIF, no metrics.json, no lineup: only the lumps ship."""
        if HOUND_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in HOUND_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS))

    def test_every_pair_mirrors_its_own_frame(self):
        """SDHNA2A8 is legal Doom, but SDHNA2B8 would put frame A's drawing
        on frame B: every pair here names one frame twice."""
        for p in installed():
            if len(p.stem) == 8:
                self.assertEqual(p.stem[4], p.stem[6], p)
                self.assertEqual(int(p.stem[5]) + int(p.stem[7]), 10, p)

    def test_every_sprite_carries_centred_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            left, top = grab
            self.assertEqual(left, width // 2, f"{p}: a mirrored pair flips about its offset")
            self.assertTrue(0 < top <= height, f"{p}: floor line {top} outside the {height}-px canvas")

    def test_one_canvas_per_frame_across_rotations(self):
        """The five drawings of a frame share their canvas and offsets, so
        the hound does not jump as it turns."""
        for f in ROTATED_FRAMES:
            seen = set()
            for r in ROTATION_LUMPS:
                data = (HOUND_SPRITES / f"{NEW}{f}{r.format(f=f)}.png").read_bytes()
                seen.add((struct.unpack(">II", data[16:24]), read_grab(data)))
            self.assertEqual(len(seen), 1, f"{NEW}{f}: {seen}")

    @unittest.skipUnless(WORK_FULL_A.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for p in installed():
            source = WORK_FULL_A / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_death_bleeds_dark_red(self):
        """D49/D50: the death I-N is drawn with flag_red 0-5 blood (measured
        38 to 447 pixels a frame), and the standing frames carry none."""
        red = blood_colours()

        def count(name: str) -> int:
            with Image.open(HOUND_SPRITES / f"{name}.png") as img:
                raw = img.convert("RGBA").tobytes()
            return sum(1 for i in range(0, len(raw), 4) if raw[i + 3] and tuple(raw[i:i + 3]) in red)

        for f in FLAT_FRAMES:
            self.assertGreater(count(f"{NEW}{f}0"), 0, f"{NEW}{f}0 has no flag_red 0-{BLOOD_MAX_INDEX} blood")
        for f in "ABCD":
            self.assertEqual(count(f"{NEW}{f}1"), 0, f"{NEW}{f}1: blood on a running dog")


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
            self.assertFalse([n for n in names if n.startswith("sprites/hound")], "the set folder is dropped")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))

    def test_check_pk3_sees_the_pairs_as_whole_frames(self):
        """46 lumps fill 14 frames: check_pk3 reads NAMEFRFR as two slots."""
        report = check_pk3.check_pk3(self.pk3)
        with zipfile.ZipFile(self.pk3) as zf:
            ours = {Path(n).stem for n in zf.namelist() if n.startswith("sprites/SDHN")}
        self.assertEqual(ours, EXPECTED_LUMPS)
        self.assertEqual(len(coverage(ours)), len(ROTATED_FRAMES + FLAT_FRAMES))
        self.assertFalse([f for f in report.errors if "SDHN" in f.path or "SDHN" in f.message])

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        missing = sorted(n for n in EXPECTED_LUMPS if n not in declared)
        self.assertEqual([], missing, "no row in docs/art/LICENSES.md")


class OverlayTests(unittest.TestCase):
    def test_the_overlay_names_nothing_of_the_hound(self):
        for swap in mdo.SWAPS:
            self.assertNotIn(swap.placeholder, (OLD, NEW))
            self.assertNotIn(swap.draft, (OLD, NEW))
            self.assertNotIn("reich_hound", swap.zs)

    def test_the_hound_is_recorded_as_installed(self):
        self.assertIn((OLD, NEW), mdo.INSTALLED_ENEMIES)
        self.assertIn(NEW, mdo.installed_sprites())


if __name__ == "__main__":
    unittest.main()
