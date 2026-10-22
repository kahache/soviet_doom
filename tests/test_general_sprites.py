"""D73 (2026-10-14): the General and his shell wear their own sprites.

REDRAWN by D109 and D114 (2026-10-22): the set that ships now is the
Google Gemini redraw built by `tools/art/gemini_enemy.py general` into
`work/art/enemies_gemini/general/` (MOD-SPEC 6.3, "The seven enemies redrawn
from Google Gemini"), same lump names, frame letters and rotations, so the
state machine below is untouched. The `files` checks read that build; the
rig render named below is history (the generator is kept), and a lump of
it shipping again is a failure. tests/test_gemini_enemy_install.py holds
the install itself.

The CEO combined cells C and D of the General's sweep, C from the front and
D's two-flag cloak on his back (D71), approved the CD turnaround (D72, "OK
al general") and then the full set (D73, "Ok general"): the 81 `SDGN` and
5 `SDGL` lumps rendered by `tools/art/gen_general.py --full` into
`work/art/general/full/SDGN/` and `.../SDGL/` ship from
`assets/sprites/general/`. MOD-SPEC 6.3, "The General and his shell,
installed by D73". The same pattern as the Doughboy's
(tests/test_doughboy_sprites.py, D70) and the Stormtrooper's bolt
(tests/test_storm_sprites.py, D56), with one difference the swap rule
always named (BESTIARY 2.7): the General's two Summon lines borrowed
CYBR E F and now name their own frames, SDGN Q R, and the shell's burst
borrowed MISL B C D and now names SDGL C D E. What is checked, and why:

  behaviour  SD_General's and SD_GeneralShell's States blocks are the ones
             that stood at HEAD 42ac443, before D73, line for line (label,
             tics, action, flow), with only CYBR renamed SDGN and MANF/MISL
             renamed SDGL, plus the Summon and burst letters above: not one
             tic moves; still no Raise and no XDeath; Q is Bright and gives
             the order, every shell frame is Bright, RenderStyle Add stays
  body       it stays 40 x 100 (Cyberdemon radius): every living frame is
             narrower than the 80-unit box and rises over the actor's z no
             higher than Freedoom's CYBR did (105 px), but for Q, whose
             raised fist rises to 109 px, under the 112 ceiling he is built
             to clear; every place a built map puts thing 21106 or 16 fits
             that body (no wall inside its box, the opening over it at least
             100, and over Q's fist too)
  sprite     no state anywhere names CYBR or MANF any more, MOD-SPEC 5.1 no
             longer declares them (nor MISL since D82, when the PG-7V
             grenade and the Katyusha rocket took SDPG/SDKR and the burst
             SDPX), and every frame a state uses has its lumps
  files      assets/sprites/general/ holds exactly the 86 lumps: SDGN A-G
             and Q-R in eight separate rotations (no mirrored pairs: the gun
             rides his right shoulder, the pennants and the cloak's flags
             differ side to side), H-P in rotation 0, SDGL A-E in rotation
             0; each has a grAb chunk before its image data, one canvas and
             one offset per frame group as gen_general drew them; where
             work/ exists each is byte-identical to the approved render;
             with Pillow: SDGN in palette v2 (flesh_pink, D45), SDGL inside
             v1, hard alpha, the deaths carry D49's dark-red blood, the pool
             growing, and the corpse P lies flat
  package    the built PK3 carries them flat as sprites/<NAME>.png, check_pk3
             passes sprites and licences, and each has a licence row
  overlay    the draft overlay records CYBR -> SDGN and MANF -> SDGL as
             installed whole and no swap names either side

Doom's Cyberdemon (CYBR) is not touched: ours replaces it, so a map placing
16 gets ours; its IWAD lumps stay in the IWAD, as Doom's FatShot keeps MANF.

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
GENERAL_ZS = SRC_DIR / "zscript" / "monsters" / "general.zs"
SHELL_ZS = SRC_DIR / "zscript" / "monsters" / "general_shell.zs"
GENERAL_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "general"
WORK_FULL = PROJECT_ROOT / "work" / "art" / "general" / "full"   # the rig set (and the shell SDGL)
WORK_GEMINI = PROJECT_ROOT / "work" / "art" / "enemies_gemini" / "general"   # SDGN since D109
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
OLD, NEW = "CYBR", "SDGN"
SHELL_OLD = ("MANF", "MISL")          # flight, burst: Doom's mancubus shot and rocket burst
SHELL_NEW = "SDGL"
STILL_IWAD = "MISL"                   # the rockets wore it until D82 (SDPG/SDKR, burst SDPX)
# The letters the swap rule named (BESTIARY 2.7): (label, old letters) -> new.
NEW_LETTERS = {("Summon", "E"): "Q", ("Summon", "F"): "R",
               ("Death", "B"): "C", ("Death", "C"): "D", ("Death", "D"): "E"}
ROTATED_FRAMES = "ABCDEFGQR"          # walk A-D, salvo E-F, pain G, summon Q-R: eight rotations each
FLAT_FRAMES = "HIJKLMNOP"             # death H-P: rotation 0
SHELL_FRAMES = "ABCDE"                # flight A-B, burst C-E: rotation 0
ROTATIONS_8 = "12345678"
EXPECTED_LUMPS = {f"{NEW}{f}{r}" for f in ROTATED_FRAMES for r in ROTATIONS_8} \
    | {f"{NEW}{f}0" for f in FLAT_FRAMES} | {f"{SHELL_NEW}{f}0" for f in SHELL_FRAMES}

# (canvas width, height, grAb left, top) per frame, as gemini_enemy.py
# placed the Gemini redraw (D109): one canvas a frame for its rotations,
# `left` the axis, `top` the floor line 4 px over the boots' last row;
# measured on the installed files 2026-10-22. (The rig set had 136 x 124
# for every living frame and 300 x 168 for the death.) The shell, not
# redrawn, keeps gen_general.py's SHELL_CV, centred as the storm bolt.
CANVASES = {"A": (72, 104, 36, 93), "B": (72, 104, 36, 93), "C": (72, 104, 36, 93),
            "D": (72, 104, 36, 93), "E": (72, 104, 36, 93), "F": (112, 104, 56, 93),
            "G": (88, 104, 44, 93), "H": (80, 96, 40, 88), "I": (88, 104, 44, 98),
            "J": (64, 96, 32, 86), "K": (72, 96, 36, 85), "L": (88, 88, 44, 80),
            "M": (88, 88, 44, 80), "N": (152, 40, 76, 34), "O": (152, 40, 76, 34),
            "P": (152, 40, 76, 34), "Q": (72, 104, 36, 93), "R": (72, 104, 36, 93)}
SHELL_CANVAS = (40, 40, 20, 20)

# The body: Cyberdemon radius, 10 units shorter, unchanged by D73.
RADIUS, HEIGHT = 40, 100
CYBR_RISE = 105                       # Freedoom's CYBR rises 96-105 px over its offset row (freedoom2.wad 0.13.0)
SUMMON_FRAME = "Q"                    # the order, his fist raised over the cap ...
LOW_CEILING = 112                     # ... still under the ceiling he is built to clear (BESTIARY 9; measured 109)
GENERAL_NUMBERS = {"21106", "16"}     # ours, and Doom's Cyberdemon, which it replaces

# D49's drawn blood. The band counted is flag_red 0-3, the pool's darkest:
# the pennants and the cloak's flags are flag_red 4-11, so 0-5 would count
# the flags too. Measured: at most 14 px of it in a living frame, the
# deaths 23 (H) growing to 619 (P).
BLOOD_MAX_INDEX = 3

# The corpse lies flat (the CEO's rule since the Legion's first L0). On the
# shipped PNG: on his back across the screen, much wider than tall, and he
# rises over his offset row a fraction of what he does standing
# (measured: 134 x 58 px, rising 27; the living frames rise 89-109).
CORPSE = "P"
CORPSE_MAX_ASPECT = 0.5               # opaque height / width
CORPSE_MAX_RISE_SHARE = 0.4           # its rise / the lowest living rise

# The States blocks as they stood before D73, with Freedoom's CYBR, MANF
# and MISL, read from src/zscript/monsters/general.zs and general_shell.zs
# at HEAD 42ac443 on 2026-10-14 before the swap. One row per line: (label,
# ":", "", 0, "") for a label, (label, sprite, frames, tics, rest) for a
# state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
GENERAL_BEFORE_D73 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "CYBR", "AB", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", ":", "", 0, ""),
    ("See", "CYBR", "AABBCCDD", 3, "A_SD_GeneralChase"),
    ("See", "->", "Loop", 0, ""),
    ("Missile", ":", "", 0, ""),
    ("Missile", "CYBR", "E", 6, "A_FaceTarget"),
    ("Missile", "CYBR", "F", 12, "A_SD_GeneralShot"),
    ("Missile", "CYBR", "E", 12, "A_FaceTarget"),
    ("Missile", "CYBR", "F", 12, "A_SD_GeneralShot"),
    ("Missile", "CYBR", "E", 12, "A_FaceTarget"),
    ("Missile", "CYBR", "F", 12, "A_SD_GeneralShot"),
    ("Missile", "->", "Goto See", 0, ""),
    ("Summon", ":", "", 0, ""),
    ("Summon", "CYBR", "E", 15, "Bright A_SD_GeneralSummon"),
    ("Summon", "CYBR", "F", 15, ""),
    ("Summon", "->", "Goto See", 0, ""),
    ("Pain", ":", "", 0, ""),
    ("Pain", "CYBR", "G", 10, "A_Pain"),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "CYBR", "H", 10, ""),
    ("Death", "CYBR", "I", 10, "A_Scream"),
    ("Death", "CYBR", "JKL", 10, ""),
    ("Death", "CYBR", "M", 10, "A_NoBlocking"),
    ("Death", "CYBR", "NO", 10, ""),
    ("Death", "CYBR", "P", 30, ""),
    ("Death", "CYBR", "P", -1, "A_BossDeath"),
    ("Death", "->", "Stop", 0, ""),
)
SHELL_BEFORE_D73 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "MANF", "AB", 4, "Bright"),
    ("Spawn", "->", "Loop", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "MISL", "B", 8, "Bright"),
    ("Death", "MISL", "C", 6, "Bright"),
    ("Death", "MISL", "D", 4, "Bright"),
    ("Death", "->", "Stop", 0, ""),
)


def states(path: Path) -> list[tuple]:
    """Every line of a States block, labels included, in order (see GENERAL_BEFORE_D73)."""
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


def swapped(before: tuple, olds: tuple[str, ...], new: str) -> list[tuple]:
    """The pre-D73 rows with the sprite renamed and the named letters moved."""
    out = []
    for lb, sp, fr, tics, rest in before:
        if sp in olds:
            sp, fr = new, NEW_LETTERS.get((lb, fr), fr)
        out.append((lb, sp, fr, tics, rest))
    return out


def frame_rows(rows: list[tuple]) -> list[tuple]:
    return [r for r in rows if r[1] not in (":", "->")]


def totals(rows) -> dict[str, int]:
    out: dict[str, int] = {}
    for lb, _, _, tics, _ in rows:
        out[lb] = out.get(lb, 0) + tics
    return out


def installed() -> list[Path]:
    return sorted(GENERAL_SPRITES.glob("*.png")) if GENERAL_SPRITES.is_dir() else []


def canvas_of(stem: str) -> tuple[int, int, int, int]:
    if stem.startswith(SHELL_NEW):
        return SHELL_CANVAS
    return CANVASES[stem[4]]


def opaque_box(name: str) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of the opaque pixels, right/bottom exclusive."""
    with Image.open(GENERAL_SPRITES / f"{name}.png") as img:
        box = img.convert("RGBA").getchannel("A").getbbox()
    assert box is not None, name
    return box


def rise(name: str) -> int:
    """How many px the drawing rises over its offset row (the actor's z)."""
    _, top = read_grab((GENERAL_SPRITES / f"{name}.png").read_bytes())
    return top - opaque_box(name)[1]


class BehaviourTests(unittest.TestCase):
    def test_the_general_is_the_pre_d73_one_but_for_the_sprite(self):
        self.assertEqual(states(GENERAL_ZS), swapped(GENERAL_BEFORE_D73, (OLD,), NEW))

    def test_the_shell_is_the_pre_d73_one_but_for_the_sprite(self):
        self.assertEqual(states(SHELL_ZS), swapped(SHELL_BEFORE_D73, SHELL_OLD, SHELL_NEW))

    def test_tic_totals_per_label_unchanged(self):
        for path, before in ((GENERAL_ZS, GENERAL_BEFORE_D73), (SHELL_ZS, SHELL_BEFORE_D73)):
            self.assertEqual(totals(states(path)), totals(before), path.name)

    def test_the_summon_lines_name_q_and_r(self):
        """The file's own comment and the preview's section 8: Q 15 Bright
        gives the order, R 15 follows."""
        summon = [r for r in frame_rows(states(GENERAL_ZS)) if r[0] == "Summon"]
        self.assertEqual([(r[1], r[2], r[3], r[4]) for r in summon],
                         [(NEW, "Q", 15, "Bright A_SD_GeneralSummon"), (NEW, "R", 15, "")])

    def test_still_no_raise_and_no_xdeath(self):
        """A boss, as the Cyberdemon: no Raise; and no gib, so no XDeath."""
        labels = {r[0] for r in states(GENERAL_ZS)}
        self.assertFalse(labels & {"Raise", "XDeath"})

    def test_the_shell_is_bright_and_additive(self):
        """Additive, so only bright colours show; every frame Bright, as the
        placeholders were (the preview's additive look is NOT VERIFIED)."""
        for r in frame_rows(states(SHELL_ZS)):
            self.assertTrue(r[4].startswith("Bright"), r)
        self.assertRegex(strip_comments(SHELL_ZS.read_text(encoding="utf-8")), r'RenderStyle\s+"Add"\s*;')

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states(GENERAL_ZS))), 18)
        self.assertEqual(len(frame_rows(states(SHELL_ZS))), 4)


class BodyTests(unittest.TestCase):
    def test_the_body_is_unchanged(self):
        c = constants(GENERAL_ZS)
        self.assertEqual((c["SD_GENERAL_RADIUS"], c["SD_GENERAL_HEIGHT"]), (RADIUS, HEIGHT))

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_drawing_fits_the_body(self):
        """Inside the box and no taller over z than CYBR, but for Q's fist,
        which stays under the low ceiling he is built to clear."""
        for f in ROTATED_FRAMES:
            for r in ROTATIONS_8:
                name = f"{NEW}{f}{r}"
                left, _, right, _ = opaque_box(name)
                self.assertLessEqual(right - left, 2 * RADIUS, name)
                self.assertLessEqual(rise(name), LOW_CEILING if f == SUMMON_FRAME else CYBR_RISE, name)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_no_frame_goes_over_his_height(self):
        """The rig set's Q raised his fist over the 100-unit body (103-109
        px); Gemini drew no order, so Q is the standing view since D109
        (gemini_enemy's `derived`) and every living frame rises 86-91 px."""
        over = sorted({f"{NEW}{f}" for f in ROTATED_FRAMES for r in ROTATIONS_8
                       if rise(f"{NEW}{f}{r}") > HEIGHT})
        self.assertEqual(over, [])


class SpriteTests(unittest.TestCase):
    def test_every_state_names_our_sprites(self):
        self.assertEqual({r[1] for r in frame_rows(states(GENERAL_ZS))}, {NEW})
        self.assertEqual({r[1] for r in frame_rows(states(SHELL_ZS))}, {SHELL_NEW})

    def test_no_state_names_cybr_or_manf(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & {OLD, "MANF"}, path.name)

    def test_mod_spec_retires_cybr_and_manf_and_since_d82_misl(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertNotIn(OLD, declared)
        self.assertNotIn("MANF", declared)
        self.assertNotIn(STILL_IWAD, declared)

    def test_misl_left_the_weapons_with_d82(self):
        weapons = SRC_DIR / "zscript" / "weapons"
        for zs in ("pg7_grenade.zs", "katyusha_rocket.zs"):
            names = {n for n, _ in check_pk3.zscript_state_sprites((weapons / zs).read_text(encoding="utf-8"))}
            self.assertNotIn(STILL_IWAD, names, zs)
            self.assertIn("SDPX", names, zs)

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for path in (GENERAL_ZS, SHELL_ZS):
            for _, sprite, frames, _, _ in frame_rows(states(path)):
                for f in frames:
                    rots = ROTATIONS_8 if sprite == NEW and f in ROTATED_FRAMES else "0"
                    for r in rots:
                        self.assertIn(f"{sprite}{f}{r}", names)

    def test_every_installed_frame_is_used(self):
        self.assertEqual({f for r in frame_rows(states(GENERAL_ZS)) for f in r[2]},
                         set(ROTATED_FRAMES + FLAT_FRAMES))
        self.assertEqual({f for r in frame_rows(states(SHELL_ZS)) for f in r[2]}, set(SHELL_FRAMES))

    def test_the_corpse_is_the_held_frame(self):
        held = [r for r in frame_rows(states(GENERAL_ZS)) if r[3] == -1]
        self.assertEqual([(r[0], r[2], r[4]) for r in held], [("Death", CORPSE, "A_BossDeath")])


class FileTests(unittest.TestCase):
    def test_exactly_the_86_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 86)
        self.assertEqual(sum(1 for n in EXPECTED_LUMPS if n.startswith(NEW)), 81)

    def test_nothing_but_the_lumps_in_the_folder(self):
        """No GIF, no info.json, no metrics.json, no lineup: only the lumps ship."""
        if GENERAL_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in GENERAL_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS))

    def test_every_sprite_carries_its_canvas_and_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height) + tuple(grab), canvas_of(p.stem), p.name)
            left, top = grab
            self.assertTrue(0 < left < width and 0 < top <= height, p.name)
            self.assertEqual(left, width // 2, p.name)

    @unittest.skipUnless(WORK_GEMINI.is_dir() and WORK_FULL.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        """SDGN from the Gemini build (D109); the shell SDGL, not redrawn,
        from the rig render."""
        for p in installed():
            source = WORK_GEMINI / p.name if p.stem.startswith(NEW) else WORK_FULL / p.stem[:4] / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_palette_and_hard_alpha(self):
        """SDGN in v2 (flesh_pink at the throat, D45); SDGL inside v1."""
        palettes = {NEW: set(palette_mod.colours(2)), SHELL_NEW: set(palette_mod.colours(1))}
        for p in installed():
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", p.name)
                raw = img.tobytes()
            alphas = set(raw[3::4])
            self.assertLessEqual(alphas, {0, 255}, p.name)
            used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
            self.assertFalse(used - palettes[p.stem[:4]], p.name)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_deaths_bleed_dark_red(self):
        """D49: every death frame H-P carries the pool's flag_red 0-3. The rig
        set had more of it in each death frame than in any living one, the
        pool growing onto the flags; Gemini's death sheet, approved as drawn
        (D109), shows 92 to 274 px a frame, the living coat's shadows up to
        ~200, so what holds is that each death frame shows some."""
        data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
        ramp = next(r for r in data["ramps"] if r["name"] == "flag_red")
        red = {tuple(c) for c in ramp["colours"][:BLOOD_MAX_INDEX + 1]}

        def count(name: str) -> int:
            with Image.open(GENERAL_SPRITES / f"{name}.png") as img:
                raw = img.convert("RGBA").tobytes()
            return sum(1 for i in range(0, len(raw), 4) if raw[i + 3] and tuple(raw[i:i + 3]) in red)

        for f in FLAT_FRAMES:
            self.assertGreater(count(f"{NEW}{f}0"), 0, f"{NEW}{f}0")

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_corpse_lies_flat(self):
        name = f"{NEW}{CORPSE}0"
        left, top, right, bottom = opaque_box(name)
        self.assertLessEqual((bottom - top) / (right - left), CORPSE_MAX_ASPECT, name)
        lowest_living = min(rise(f"{NEW}{f}{r}") for f in ROTATED_FRAMES for r in ROTATIONS_8)
        self.assertLessEqual(rise(name), CORPSE_MAX_RISE_SHARE * lowest_living, name)


    @unittest.skipUnless(WORK_FULL.is_dir(), "work/ not present (CI has no work/)")
    def test_the_rig_set_no_longer_ships(self):
        """D109: every lump of the set is the Gemini redraw, none the rig
        render it replaced (that set stays in work/, history)."""
        for p in installed():
            if not p.stem.startswith(NEW):
                continue
            old = WORK_FULL / NEW / p.name
            if old.is_file():
                self.assertNotEqual(p.read_bytes(), old.read_bytes(), p.name)


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
            self.assertFalse([n for n in names if n.startswith("sprites/general")], "the set folder is dropped")

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
    the built maps anyway, 2026-10-14: MAP03 places 21106 once (480,1216,
    the portal hall, every skill, ceiling 384), the range once (1824,1600,
    ceiling 192); MAP01 and MAP02 never, and no map places 16."""

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
            things = [t for t in blocks["thing"] if str(t.get("type")) in GENERAL_NUMBERS]
            if things:
                yield name, _Geometry(blocks), things

    def test_the_general_is_placed_in_map03_and_the_range(self):
        self.assertEqual({name for name, _, _ in self.placements()}, {"MAP03", "MAP06", "MAP09", "RANGE"})  # MAP06, MAP09: stand-in bosses until episodes 2 and 3 have their own (D104, D112)

    def test_every_general_fits_where_he_stands(self):
        for name, geo, things in self.placements():
            for t in things:
                x, y = float(t["x"]), float(t["y"])
                where = f"{name} ({x:.0f}, {y:.0f})"
                self.assertEqual(len(geo.sectors_at(x, y)), 1, f"{where}: not inside exactly one sector")
                walls, touched = geo.stand(x, y, RADIUS)
                self.assertEqual([], walls, f"{where}: a wall inside the {RADIUS}-unit box")
                opening = min(geo.ceiling[s] for s in touched) - max(geo.floor[s] for s in touched)
                self.assertGreaterEqual(opening, max(HEIGHT, LOW_CEILING), where)


class OverlayTests(unittest.TestCase):
    def test_recorded_as_installed_whole(self):
        self.assertIn((OLD, NEW), mdo.INSTALLED_ENEMIES)
        self.assertIn(("MANF", SHELL_NEW), mdo.INSTALLED_ENEMIES)
        self.assertTrue({NEW, SHELL_NEW} <= mdo.installed_sprites())

    def test_misl_is_not_an_installed_enemy(self):
        """MISL was the rockets' (retired by D82, not by an enemy install)."""
        self.assertNotIn(STILL_IWAD, {name for pair in mdo.INSTALLED_ENEMIES for name in pair})

    def test_the_overlay_names_nothing_of_the_general(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & {OLD, NEW, "MANF", SHELL_NEW}, swap)
            self.assertNotIn("general", swap.zs)

    def test_the_overlay_reads_the_states_as_the_engine_does(self):
        text = GENERAL_ZS.read_text(encoding="utf-8")
        self.assertEqual(mdo.state_letters(text, OLD), "")
        self.assertEqual(set(mdo.state_letters(text, NEW)), set(ROTATED_FRAMES + FLAT_FRAMES))
        shell = SHELL_ZS.read_text(encoding="utf-8")
        self.assertEqual(mdo.state_letters(shell, "MANF") + mdo.state_letters(shell, STILL_IWAD), "")
        self.assertEqual(mdo.state_letters(shell, SHELL_NEW), SHELL_FRAMES)


if __name__ == "__main__":
    unittest.main()
