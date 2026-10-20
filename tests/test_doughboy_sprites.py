"""D70 (2026-10-14): the Doughboy wears its own sprites.

The CEO chose cell C of the heavies sweep, the head in its M1 helmet,
severed (D65, "Doughboy C"), asked for a bigger flag on the helmet (D67,
"ponle la bandera más grande en la cabeza") and approved the set with it
(D70, "OK"): the 54 `SDDB` lumps rendered by `tools/art/gen_heavy.py --full
db` into `work/art/enemies/heavy/full/SDDB/` ship from
`assets/sprites/doughboy/`. MOD-SPEC 6.3, "The Doughboy, installed by D70".
The same pattern as the Panzermensch's (tests/test_panzermensch_sprites.py,
D67). What is checked, and why:

  behaviour  SD_Doughboy's States block is the one that stood at HEAD
             093db98, before D70, line for line (label, frame letters,
             tics, action, flow; no Melee label, as the cacodemon), with
             only HEAD renamed SDDB: not one tic moves
  body       it stays 31 x 56 (Cacodemon parity): the float and attack
             frames are narrower than the 62-unit box, no frame is wider
             than Freedoom's HEAD (69 px) and none rises above the actor's z
             higher than HEAD did (61-62 px); every place a built map
             puts thing 21104 or 3005 fits that body (no wall inside its
             box, the opening over it at least 56)
  sprite     no state anywhere names HEAD any more, MOD-SPEC 5.1 no longer
             declares it, and every frame a state uses has its lumps; the
             shell, SD_DoughboyShell, names our SDDL since D81 (2026-10-20;
             its install's own suite is tests/test_shells_install.py), and
             BAL2 is retired with it
  files      assets/sprites/doughboy/ holds exactly the 54 lumps: A-F in
             eight separate rotations (no mirrored pairs: the helmet sits
             askew with the flag and the buckle on one side), G-L in
             rotation 0; each has a grAb chunk before its image data, one
             canvas and one offset per frame group as gen_heavy drew them
             (the living frames and G hang by the actor's z, H-L sink onto
             the floor); where work/ exists each is byte-identical to the
             approved render; with Pillow: palette v2 (flesh_pink, D45) with
             hard alpha, the deaths carry D49's dark-red blood (flag_red
             0-5) and the corpse L lies flat
  package    the built PK3 carries them flat as sprites/<NAME>.png, check_pk3
             passes sprites and licences, and each has a licence row
  overlay    the draft overlay records HEAD -> SDDB as installed whole and
             no swap names either side

Doom's Cacodemon (HEAD) is not touched: ours replaces it, so a map placing
3005 gets ours; its IWAD lumps stay in the IWAD.

Stdlib only, but for the palette, blood and corpse checks, which need Pillow.
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
DOUGHBOY_ZS = SRC_DIR / "zscript" / "monsters" / "doughboy.zs"
SHELL_ZS = SRC_DIR / "zscript" / "monsters" / "doughboy_shell.zs"
DOUGHBOY_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "doughboy"
WORK_SET = PROJECT_ROOT / "work" / "art" / "enemies" / "heavy" / "full" / "SDDB"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import make_draft_overlay as mdo  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
# The map geometry the Panzermensch's fit check built (D67): one reader of
# the built maps, not two.
from test_panzermensch_sprites import (  # noqa: E402
    PNG_SIGNATURE, _built_maps, _Geometry, constants, read_grab, states_block, strip_comments)

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")
OLD, NEW = "HEAD", "SDDB"
SHELL_SPRITE = "SDDL"                 # SD_DoughboyShell's own since D81 (was Freedoom's BAL2)
SHELL_OLD = "BAL2"
SHELL_LUMPS = {f"{SHELL_SPRITE}{f}0" for f in "ABCDE"}   # beside the SDDB set, assets/sprites/doughboy/
ROTATED_FRAMES = "ABCDEF"             # float A, attack B-D, pain E-F: eight rotations each
FLAT_FRAMES = "GHIJKL"                # death G-L: rotation 0
ROTATIONS_8 = "12345678"
EXPECTED_LUMPS = {f"{NEW}{f}{r}" for f in ROTATED_FRAMES for r in ROTATIONS_8} \
    | {f"{NEW}{f}0" for f in FLAT_FRAMES}
BLOOD_MAX_INDEX = 5                   # D49: the drawn blood is flag_red 0-5 (gen_heavy.py)

# (canvas width, height, grAb left, top) per frame, as gen_heavy.py drew
# them (DB_CV for A-F, DB_DEATH_CV for G-L; full_grab: the living frames
# and G, still in the air when it dies, hang by the actor's z, H-L sink
# FEET_SINK onto the floor): measured on the approved files 2026-10-14.
LIVING_CANVAS = (80, 96, 40, 76)
CANVASES = {**{f: LIVING_CANVAS for f in ROTATED_FRAMES},
            "G": (160, 108, 72, 80),
            **{f: (160, 108, 72, 76) for f in "HIJKL"}}

# The body: Cacodemon parity, unchanged by D70.
RADIUS, HEIGHT = 31, 56
HEAD_RISE = 62                        # Freedoom's HEAD A-D rise 61-62 px over their offset row (freedoom2.wad 0.13.0)
HEAD_MAX_WIDTH = 69                   # ... and are 61-69 px wide (HEADE3E7); ours lurch to 64 in pain
BOXED_FRAMES = "ABCD"                 # the float and the attack: inside the 2 x RADIUS box (53-55 px)
DOUGHBOY_NUMBERS = {"21104", "3005"}  # ours, and Doom's Cacodemon, which it replaces

# The corpse lies flat (the CEO's rule since the Legion's first L0). The
# model check is test_gen_heavy's (every part of SDDBL0 on the floor); on
# the shipped PNG: the sack seen from above is much wider than tall, and it
# rises over its offset row barely half what the living head does
# (measured: 109 x 54 px, rising 33 px; the living frames rise 60-62).
CORPSE = "L"
CORPSE_MAX_ASPECT = 0.55              # opaque height / width
CORPSE_MAX_RISE_SHARE = 0.6           # its rise / the lowest living rise

# SD_Doughboy's States block as it stood before D70, with Freedoom's HEAD,
# read from src/zscript/monsters/doughboy.zs at HEAD 093db98 on 2026-10-14
# before the swap. One row per line: (label, ":", "", 0, "") for a label,
# (label, sprite, frames, tics, rest) for a state, (label, "->", flow, 0, "")
# for Goto/Loop/Stop.
DOUGHBOY_BEFORE_D70 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "HEAD", "A", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", ":", "", 0, ""),
    ("See", "HEAD", "A", 3, "A_Chase"),
    ("See", "->", "Loop", 0, ""),
    ("Missile", ":", "", 0, ""),
    ("Missile", "HEAD", "B", 5, "A_FaceTarget"),
    ("Missile", "HEAD", "C", 5, "A_FaceTarget"),
    ("Missile", "HEAD", "D", 5,
     'Bright A_SD_MeleeOrMissile(SD_DOUGHBOY_MELEE_DICE, SD_DOUGHBOY_MELEE_MULT, "sd/mon/doughboy/melee", '
     '"SD_DoughboyShell")'),
    ("Missile", "->", "Goto See", 0, ""),
    ("Pain", ":", "", 0, ""),
    ("Pain", "HEAD", "E", 3, ""),
    ("Pain", "HEAD", "E", 3, "A_Pain"),
    ("Pain", "HEAD", "F", 6, ""),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "HEAD", "G", 8, ""),
    ("Death", "HEAD", "H", 8, "A_Scream"),
    ("Death", "HEAD", "I", 8, ""),
    ("Death", "HEAD", "J", 8, ""),
    ("Death", "HEAD", "K", 8, "A_NoBlocking"),
    ("Death", "HEAD", "L", -1, "A_SetFloorClip"),
    ("Death", "->", "Stop", 0, ""),
    ("Raise", ":", "", 0, ""),
    ("Raise", "HEAD", "L", 8, "A_UnSetFloorClip"),
    ("Raise", "HEAD", "KJIHG", 8, ""),
    ("Raise", "->", "Goto See", 0, ""),
)


def states(path: Path) -> list[tuple]:
    """Every line of a States block, labels included, in order (see DOUGHBOY_BEFORE_D70)."""
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


def renamed(new: str) -> list[tuple]:
    return [(lb, new if sp == OLD else sp, fr, tics, rest) for lb, sp, fr, tics, rest in DOUGHBOY_BEFORE_D70]


def frame_rows(rows: list[tuple]) -> list[tuple]:
    return [r for r in rows if r[1] not in (":", "->")]


def installed() -> list[Path]:
    """The SDDB set only: the shell's SDDL A-E share the folder since D81."""
    if not DOUGHBOY_SPRITES.is_dir():
        return []
    return sorted(p for p in DOUGHBOY_SPRITES.glob("*.png") if p.stem not in SHELL_LUMPS)


def opaque_box(name: str) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of the opaque pixels, right/bottom exclusive."""
    with Image.open(DOUGHBOY_SPRITES / f"{name}.png") as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    assert box is not None, name
    return box


def rise(name: str) -> int:
    """How many px the drawing rises over its offset row (the actor's z)."""
    _, top = read_grab((DOUGHBOY_SPRITES / f"{name}.png").read_bytes())
    return top - opaque_box(name)[1]


class BehaviourTests(unittest.TestCase):
    def test_the_states_are_the_pre_d70_ones_but_for_the_sprite_name(self):
        self.assertEqual(states(DOUGHBOY_ZS), renamed(NEW))

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        self.assertEqual(totals(states(DOUGHBOY_ZS)), totals(DOUGHBOY_BEFORE_D70))

    def test_still_no_melee_state(self):
        """As the cacodemon: the attack itself picks the bite or the shell."""
        self.assertNotIn("Melee", {r[0] for r in states(DOUGHBOY_ZS)})

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states(DOUGHBOY_ZS))), 16)


class BodyTests(unittest.TestCase):
    def test_the_body_is_unchanged(self):
        c = constants(DOUGHBOY_ZS)
        self.assertEqual((c["SD_DOUGHBOY_RADIUS"], c["SD_DOUGHBOY_HEIGHT"]), (RADIUS, HEIGHT))

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_drawing_fits_the_body_as_head_did(self):
        """No wider and no taller over z than Freedoom's HEAD, the float and
        the attack inside the box, so 31 x 56 hits what it hit before (D67's
        rule: the body follows the drawing; here the drawing follows the
        placeholder)."""
        for f in ROTATED_FRAMES:
            for r in ROTATIONS_8:
                name = f"{NEW}{f}{r}"
                left, _, right, _ = opaque_box(name)
                self.assertLessEqual(right - left, 2 * RADIUS if f in BOXED_FRAMES else HEAD_MAX_WIDTH, name)
                self.assertLessEqual(rise(name), HEAD_RISE, name)


class SpriteTests(unittest.TestCase):
    def test_every_state_names_our_sprite(self):
        self.assertEqual({r[1] for r in frame_rows(states(DOUGHBOY_ZS))}, {NEW})

    def test_no_state_names_head(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertNotIn(OLD, names, path.name)

    def test_mod_spec_retires_head_and_the_shells_bal2(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertNotIn(OLD, declared)
        self.assertNotIn(SHELL_OLD, declared, "D81: the shell is ours")

    def test_the_shell_wears_sddl(self):
        names = {n for n, _ in check_pk3.zscript_state_sprites(SHELL_ZS.read_text(encoding="utf-8"))}
        self.assertEqual(names, {SHELL_SPRITE})

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for _, sprite, frames, _, _ in frame_rows(states(DOUGHBOY_ZS)):
            for f in frames:
                for r in (ROTATIONS_8 if f in ROTATED_FRAMES else "0"):
                    self.assertIn(f"{sprite}{f}{r}", names)

    def test_every_installed_frame_is_used(self):
        self.assertEqual({f for r in frame_rows(states(DOUGHBOY_ZS)) for f in r[2]},
                         set(ROTATED_FRAMES + FLAT_FRAMES))

    def test_the_corpse_is_the_held_frame(self):
        held = [r for r in frame_rows(states(DOUGHBOY_ZS)) if r[3] == -1]
        self.assertEqual([(r[0], r[2]) for r in held], [("Death", CORPSE)])


class FileTests(unittest.TestCase):
    def test_exactly_the_54_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 54)

    def test_nothing_but_the_lumps_in_the_folder(self):
        """No GIF, no metrics.json, no blood_share.json, no before_flag/:
        only the lumps ship (the shell's SDDL A-E beside them since D81)."""
        if DOUGHBOY_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in DOUGHBOY_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS | SHELL_LUMPS))

    def test_every_sprite_carries_its_canvas_and_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height) + tuple(grab), CANVASES[p.stem[4]], p.name)
            left, top = grab
            self.assertTrue(0 < left < width and 0 < top <= height, p.name)
            if p.stem[4] in ROTATED_FRAMES:
                self.assertEqual(left, width // 2, p.name)

    @unittest.skipUnless(WORK_SET.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for p in installed():
            source = WORK_SET / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_palette_v2_and_hard_alpha(self):
        v2 = set(palette_mod.colours(2))
        for p in installed():
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", p.name)
                raw = img.tobytes()
            alphas = set(raw[3::4])
            self.assertLessEqual(alphas, {0, 255}, p.name)
            used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
            self.assertFalse(used - v2, p.name)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_deaths_bleed_dark_red(self):
        """D49: every death frame G-L carries flag_red 0-5 blood, more of it
        than any living frame (the living frames hold some in the stump's
        drip and the pain's wound: at most 301 px, SDDBE1; the deaths 312
        to 1073, growing as the pool spreads)."""
        data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        ramp = next(r for r in data["ramps"] if r["name"] == "flag_red")
        red = {tuple(c) for c in ramp["colours"][:BLOOD_MAX_INDEX + 1]}

        def count(name: str) -> int:
            with Image.open(DOUGHBOY_SPRITES / f"{name}.png") as img:
                raw = img.convert("RGBA").tobytes()
            return sum(1 for i in range(0, len(raw), 4) if raw[i + 3] and tuple(raw[i:i + 3]) in red)

        living = max(count(f"{NEW}{f}{r}") for f in ROTATED_FRAMES for r in ROTATIONS_8)
        deaths = [count(f"{NEW}{f}0") for f in FLAT_FRAMES]
        for f, n in zip(FLAT_FRAMES, deaths):
            self.assertGreater(n, living, f"{NEW}{f}0")
        self.assertEqual(deaths, sorted(deaths), "the pool spreads frame by frame")

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_corpse_lies_flat(self):
        name = f"{NEW}{CORPSE}0"
        left, top, right, bottom = opaque_box(name)
        self.assertLessEqual((bottom - top) / (right - left), CORPSE_MAX_ASPECT, name)
        lowest_living = min(rise(f"{NEW}{f}{r}") for f in ROTATED_FRAMES for r in ROTATIONS_8)
        self.assertLessEqual(rise(name), CORPSE_MAX_RISE_SHARE * lowest_living, name)


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
            self.assertFalse([n for n in names if n.startswith("sprites/doughboy")], "the set folder is dropped")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        missing = sorted(n for n in EXPECTED_LUMPS if n not in declared)
        self.assertEqual([], missing, "no row in docs/art/LICENSES.md")


class MapFitTests(unittest.TestCase):
    """The body did not change, so every placement fits as it did; checked on
    the built maps anyway, 2026-10-14: MAP01 places 3005 once (2760,1300,
    skills 3-5), MAP02 21104 once (2976,896, skills 3-5), MAP03 three times
    (1000,400 on every skill; 1150,520 and 864,1216 on 4-5), the range once
    (1152,1600). The narrowest opening over any of them is 128."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, pk3, TOOLS_DIR, PROJECT_ROOT / "assets")
        cls.maps = _built_maps(pk3)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def placements(self):
        for name, blocks in sorted(self.maps.items()):
            things = [t for t in blocks["thing"] if str(t.get("type")) in DOUGHBOY_NUMBERS]
            if things:
                yield name, _Geometry(blocks), things

    def test_the_doughboy_is_placed_in_every_map(self):
        self.assertEqual({name for name, _, _ in self.placements()}, {"MAP01", "MAP02", "MAP03", "RANGE"})

    def test_every_doughboy_fits_where_it_floats(self):
        for name, geo, things in self.placements():
            for t in things:
                x, y = float(t["x"]), float(t["y"])
                where = f"{name} ({x:.0f}, {y:.0f})"
                self.assertEqual(len(geo.sectors_at(x, y)), 1, f"{where}: not inside exactly one sector")
                walls, touched = geo.stand(x, y, RADIUS)
                self.assertEqual([], walls, f"{where}: a wall inside the {RADIUS}-unit box")
                opening = min(geo.ceiling[s] for s in touched) - max(geo.floor[s] for s in touched)
                self.assertGreaterEqual(opening, HEIGHT, where)


class OverlayTests(unittest.TestCase):
    def test_recorded_as_installed_whole(self):
        self.assertIn((OLD, NEW), mdo.INSTALLED_ENEMIES)
        self.assertIn(NEW, mdo.installed_sprites())

    def test_the_overlay_names_nothing_of_the_doughboy(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & {OLD, NEW}, swap)
            self.assertNotIn("doughboy", swap.zs)

    def test_the_overlay_reads_the_states_as_the_engine_does(self):
        text = DOUGHBOY_ZS.read_text(encoding="utf-8")
        self.assertEqual(mdo.state_letters(text, OLD), "")
        self.assertEqual(mdo.state_letters(text, NEW), ROTATED_FRAMES + FLAT_FRAMES)


if __name__ == "__main__":
    unittest.main()
