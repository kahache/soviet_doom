"""D67 (2026-10-14): the Panzermensch and the Schwer wear their own sprites.

REDRAWN by D109 and D114 (2026-10-22): the set that ships now is the
Google Gemini redraw built by `tools/art/gemini_enemy.py panzer` and `panzer_heavy` into
`work/art/enemies_gemini/panzer` and `panzer_heavy/` (MOD-SPEC 6.3, "The seven enemies redrawn
from Google Gemini"), same lump names, frame letters and rotations, so the
state machine below is untouched. The `files` checks read that build; the
rig render named below is history (the generator is kept), and a lump of
it shipping again is a failure. tests/test_gemini_enemy_install.py holds
the install itself.

The CEO chose cell D of the heavies sweep, the bare skull in a riveted iron
mask (D65, "Panzermensch D"), and approved its full set with the Schwer, its
black variant, alongside (D67, "OK al Panzermensch"): the 71 `SDPM` and 71
`SDPS` lumps rendered by `tools/art/gen_heavy.py --full` into
`work/art/enemies/heavy/full/SDPM/` and `.../SDPS/` ship from
`assets/sprites/panzermensch/`. MOD-SPEC 6.3, "The Panzermensch and the
Schwer, installed by D67". The same pattern as the Stormtrooper's
(tests/test_storm_sprites.py, D56), with two differences: the Schwer gets a
States block of its own (it had none and drew whatever the base drew), and
its body grows with its drawing (D65's S2 is modelled 12 % larger). What
is checked, and why:

  behaviour  SD_Panzermensch's States block is the one that stood at HEAD
             9fe6479, before D67, line for line (label, frame letters,
             tics, action, flow; the empty `Melee:` label that falls
             through to `Missile:` included), with only BOS2 renamed SDPM;
             SD_PanzermenschSchwer's new block is that same block with
             SDPS: not one tic moves in either class
  body       the base keeps 24 x 64; the Schwer is 27 x 72 (x 1.12) and
             every place a built map puts thing 21107 or 3003 fits that
             body: no wall inside its box, the opening over it at least 72,
             no step over 24, and no passage in that map that admits the
             base's 64 but not the Schwer's 72
  sprite     no state anywhere names BOS2 any more, MOD-SPEC 5.1 no longer
             declares it, and every frame a state uses has its lumps
  files      assets/sprites/panzermensch/ holds exactly the 142 lumps:
             A-H in eight separate rotations (no mirrored pairs: the banner
             carries the D12 symbol and he throws with his right), I-O in
             rotation 0, for each of SDPM and SDPS; each has a grAb chunk
             before its image data, one canvas and one offset per frame
             group as gen_heavy drew them (living frames centred, the death
             on the body's axis column of a wider canvas, since he falls
             forward off it); where work/ exists each is byte-identical to
             the approved render; the deaths carry D49's dark-red blood
             (flag_red 0-5), checked where Pillow is installed
  package    the built PK3 carries them flat as sprites/<NAME>.png, check_pk3
             passes sprites and licences, and each has a licence row
  overlay    the draft overlay never carried the Panzermensch and names it
             nowhere

Doom's HellKnight (BOS2) and BaronOfHell (BOSS) are not touched: ours replace
them, so a map placing 69 or 3003 gets ours; their IWAD lumps stay in the
IWAD. SD_PanzerShell wears our SDPL since D81 (2026-10-20), its five lumps
in the same folder (SHELL_LUMPS); that install has its own suite,
tests/test_shells_install.py.

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
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
PANZER_ZS = SRC_DIR / "zscript" / "monsters" / "panzermensch.zs"
SCHWER_ZS = SRC_DIR / "zscript" / "monsters" / "panzermensch_schwer.zs"
PANZER_SPRITES = PROJECT_ROOT / "assets" / "sprites" / "panzermensch"
WORK_FULL = PROJECT_ROOT / "work" / "art" / "enemies" / "heavy" / "full"   # the rig sets, history since D109
WORK_GEMINI = {"SDPM": PROJECT_ROOT / "work" / "art" / "enemies_gemini" / "panzer",   # what ships since D109
               "SDPS": PROJECT_ROOT / "work" / "art" / "enemies_gemini" / "panzer_heavy"}
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
OLD, BASE, HEAVY = "BOS2", "SDPM", "SDPS"
ROTATED_FRAMES = "ABCDEFGH"           # walk A-D, attack E-G, pain H: eight rotations each
FLAT_FRAMES = "IJKLMNO"               # death I-O: rotation 0
ROTATIONS_8 = "12345678"
EXPECTED_LUMPS = {f"{s}{f}{r}" for s in (BASE, HEAVY) for f in ROTATED_FRAMES for r in ROTATIONS_8} \
    | {f"{s}{f}0" for s in (BASE, HEAVY) for f in FLAT_FRAMES}
BLOOD_MAX_INDEX = 5                   # D49: the drawn blood is flag_red 0-5 (gen_heavy.py PM_BLOOD)

# (canvas width, height, grAb left, top) per sprite and frame, as
# gemini_enemy.py placed the Gemini redraw (D109): one canvas a frame for
# its rotations, `left` the axis, `top` the floor line 4 px over the feet's
# last row: measured on the installed files 2026-10-22. (The rig sets had
# one living and one death canvas a sprite: SDPM 112 x 96 and 176 x 120,
# SDPS 128 x 104 and 192 x 140.)
CANVASES = {
    BASE: {"A": (136, 72, 68, 65), "B": (112, 72, 56, 65), "C": (104, 72, 52, 66),
           "D": (112, 72, 56, 65), "E": (128, 72, 64, 67), "F": (128, 72, 64, 67),
           "G": (128, 72, 64, 66), "H": (120, 72, 60, 66), "I": (96, 72, 48, 66),
           "J": (88, 72, 44, 67), "K": (72, 72, 36, 60), "L": (88, 72, 44, 61),
           "M": (80, 72, 40, 63), "N": (96, 56, 48, 46), "O": (96, 56, 48, 46)},
    HEAVY: {"A": (144, 80, 72, 73), "B": (120, 80, 60, 73), "C": (120, 80, 60, 74),
            "D": (120, 80, 60, 73), "E": (136, 80, 68, 75), "F": (136, 80, 68, 75),
            "G": (144, 80, 72, 74), "H": (128, 80, 64, 74), "I": (112, 80, 56, 74),
            "J": (96, 80, 48, 75), "K": (80, 80, 40, 68), "L": (104, 80, 52, 68),
            "M": (88, 80, 44, 71), "N": (112, 64, 56, 52), "O": (112, 64, 56, 52)},
}

# The body (D65: the Schwer is modelled x 1.12; D67: its Height and Radius
# follow, the PM's call after the fit check below).
BASE_RADIUS, BASE_HEIGHT = 24, 64
HEAVY_RADIUS, HEAVY_HEIGHT = 27, 72
MAX_STEP_UP = 24                      # Doom's MaxStepHeight
DOOR_OPENS_BELOW_CEILING = 4          # a door rises to the lowest neighbour ceiling - 4
SCHWER_NUMBERS = {"21107", "3003"}    # ours, and Doom's Baron, which it replaces

# The base's States block as it stood before D67, with Freedoom's BOS2, read
# from src/zscript/monsters/panzermensch.zs at HEAD 9fe6479 on 2026-10-14
# before the swap; panzermensch_schwer.zs had no States block at that HEAD
# (it inherited this one). One row per line: (label, ":", "", 0, "") for a
# label, (label, sprite, frames, tics, rest) for a state, (label, "->",
# flow, 0, "") for Goto/Loop/Stop.
PANZER_BEFORE_D67 = (
    ("Spawn", ":", "", 0, ""),
    ("Spawn", "BOS2", "AB", 10, "A_Look"),
    ("Spawn", "->", "Loop", 0, ""),
    ("See", ":", "", 0, ""),
    ("See", "BOS2", "A", 3, "A_SD_PanzerStep"),
    ("See", "BOS2", "ABBCCDD", 3, "A_Chase"),
    ("See", "->", "Loop", 0, ""),
    ("Melee", ":", "", 0, ""),
    ("Missile", ":", "", 0, ""),
    ("Missile", "BOS2", "EF", 8, "A_FaceTarget"),
    ("Missile", "BOS2", "G", 8,
     'A_SD_MeleeOrMissile(SD_PANZER_MELEE_DICE, SD_PANZER_MELEE_MULT, "sd/mon/panzermensch/melee", "SD_PanzerShell")'),
    ("Missile", "->", "Goto See", 0, ""),
    ("Pain", ":", "", 0, ""),
    ("Pain", "BOS2", "H", 2, ""),
    ("Pain", "BOS2", "H", 2, "A_Pain"),
    ("Pain", "->", "Goto See", 0, ""),
    ("Death", ":", "", 0, ""),
    ("Death", "BOS2", "I", 8, ""),
    ("Death", "BOS2", "J", 8, "A_Scream"),
    ("Death", "BOS2", "K", 8, ""),
    ("Death", "BOS2", "L", 8, "A_NoBlocking"),
    ("Death", "BOS2", "MN", 8, ""),
    ("Death", "BOS2", "O", -1, ""),
    ("Death", "->", "Stop", 0, ""),
    ("Raise", ":", "", 0, ""),
    ("Raise", "BOS2", "O", 8, ""),
    ("Raise", "BOS2", "NMLKJI", 8, ""),
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


def states(path: Path) -> list[tuple]:
    """Every line of a States block, labels included, in order (see PANZER_BEFORE_D67)."""
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
    return [(lb, new if sp == OLD else sp, fr, tics, rest) for lb, sp, fr, tics, rest in PANZER_BEFORE_D67]


def frame_rows(rows: list[tuple]) -> list[tuple]:
    return [r for r in rows if r[1] not in (":", "->")]


def constants(path: Path) -> dict[str, int]:
    text = strip_comments(path.read_text(encoding="utf-8"))
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", text)}


# D81 (2026-10-20): SD_PanzerShell's SDPL A-E share the folder
# (tests/test_shells_install.py); they are not the Panzermensch's set.
SHELL_LUMPS = {f"SDPL{f}0" for f in "ABCDE"}


def installed() -> list[Path]:
    """SDPM and SDPS only: the shell's lumps share the folder since D81."""
    if not PANZER_SPRITES.is_dir():
        return []
    return sorted(p for p in PANZER_SPRITES.glob("*.png") if p.stem not in SHELL_LUMPS)


def blood_colours() -> set[tuple[int, int, int]]:
    """flag_red 0-5, the band D49's drawn blood lives in."""
    data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    ramp = next(r for r in data["ramps"] if r["name"] == "flag_red")
    return {tuple(c) for c in ramp["colours"][:BLOOD_MAX_INDEX + 1]}


class BehaviourTests(unittest.TestCase):
    def test_the_base_states_are_the_pre_d67_ones_but_for_the_sprite_name(self):
        self.assertEqual(states(PANZER_ZS), renamed(BASE))

    def test_the_schwer_states_are_the_base_ones_with_sdps(self):
        self.assertEqual(states(SCHWER_ZS), renamed(HEAVY))

    def test_tic_totals_per_label_unchanged(self):
        def totals(rows):
            out: dict[str, int] = {}
            for lb, _, _, tics, _ in rows:
                out[lb] = out.get(lb, 0) + tics
            return out
        for path in (PANZER_ZS, SCHWER_ZS):
            self.assertEqual(totals(states(path)), totals(PANZER_BEFORE_D67), path.name)

    def test_melee_still_falls_through_to_missile(self):
        for path in (PANZER_ZS, SCHWER_ZS):
            rows = states(path)
            i = rows.index(("Melee", ":", "", 0, ""))
            self.assertEqual(rows[i + 1], ("Missile", ":", "", 0, ""), path.name)

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(frame_rows(states(PANZER_ZS))), 15)
        self.assertEqual(len(frame_rows(states(SCHWER_ZS))), 15)

    def test_the_schwer_still_derives_from_the_base_and_recolours_nothing(self):
        text = strip_comments(SCHWER_ZS.read_text(encoding="utf-8"))
        self.assertRegex(text, r"class\s+SD_PanzermenschSchwer\s*:\s*SD_Panzermensch\s+replaces\s+BaronOfHell")
        self.assertNotRegex(text, r"\bTranslation\b")


class BodyTests(unittest.TestCase):
    def test_the_base_keeps_its_body(self):
        c = constants(PANZER_ZS)
        self.assertEqual((c["SD_PANZER_RADIUS"], c["SD_PANZER_HEIGHT"]), (BASE_RADIUS, BASE_HEIGHT))

    def test_the_schwer_grows_with_its_drawing(self):
        c = constants(SCHWER_ZS)
        self.assertEqual((c["SD_PANZER_HEAVY_RADIUS"], c["SD_PANZER_HEAVY_HEIGHT"]), (HEAVY_RADIUS, HEAVY_HEIGHT))
        self.assertEqual(round(BASE_RADIUS * 1.12), HEAVY_RADIUS)
        self.assertEqual(round(BASE_HEIGHT * 1.12), HEAVY_HEIGHT)
        text = strip_comments(SCHWER_ZS.read_text(encoding="utf-8"))
        self.assertRegex(text, r"Radius\s+SD_PANZER_HEAVY_RADIUS\s*;")
        self.assertRegex(text, r"Height\s+SD_PANZER_HEAVY_HEIGHT\s*;")


class SpriteTests(unittest.TestCase):
    def test_every_state_names_our_sprites(self):
        self.assertEqual({r[1] for r in frame_rows(states(PANZER_ZS))}, {BASE})
        self.assertEqual({r[1] for r in frame_rows(states(SCHWER_ZS))}, {HEAVY})

    def test_no_state_names_bos2(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertNotIn(OLD, names, path.name)

    def test_mod_spec_retires_bos2(self):
        self.assertNotIn(OLD, check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC))

    def test_every_frame_a_state_uses_is_installed(self):
        names = {p.stem for p in installed()}
        for path in (PANZER_ZS, SCHWER_ZS):
            for _, sprite, frames, _, _ in frame_rows(states(path)):
                for f in frames:
                    for r in (ROTATIONS_8 if f in ROTATED_FRAMES else "0"):
                        self.assertIn(f"{sprite}{f}{r}", names)

    def test_every_installed_frame_is_used(self):
        for path in (PANZER_ZS, SCHWER_ZS):
            self.assertEqual({f for r in frame_rows(states(path)) for f in r[2]},
                             set(ROTATED_FRAMES + FLAT_FRAMES), path.name)


class FileTests(unittest.TestCase):
    def test_exactly_the_142_lumps_are_installed(self):
        self.assertEqual({p.stem for p in installed()}, EXPECTED_LUMPS)
        self.assertEqual(len(EXPECTED_LUMPS), 142)
        self.assertEqual(sum(n.startswith(BASE) for n in EXPECTED_LUMPS), 71)

    def test_nothing_but_the_lumps_in_the_folder(self):
        """No GIF, no metrics.json, no blood_share.json, no lineup_*: only
        the lumps ship (the shell's SDPL A-E beside them since D81)."""
        if PANZER_SPRITES.is_dir():
            self.assertEqual(sorted(p.name for p in PANZER_SPRITES.iterdir()),
                             sorted(f"{n}.png" for n in EXPECTED_LUMPS | SHELL_LUMPS))

    def test_every_sprite_carries_its_canvas_and_offsets(self):
        for p in installed():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{p}: no grAb before IDAT, GZDoom would draw it at 0,0")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height) + tuple(grab), CANVASES[p.stem[:4]][p.stem[4]], p.name)
            left, top = grab
            self.assertTrue(0 < left < width and 0 < top <= height, p.name)
            self.assertEqual(left, width // 2, p.name)

    @unittest.skipUnless(all(d.is_dir() for d in WORK_GEMINI.values()), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for p in installed():
            source = WORK_GEMINI[p.stem[:4]] / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_the_corpse_lies_lowest(self):
        """The rig sets bled D49's flag_red in every death frame; Gemini's
        death sheet, approved as drawn (D109), barely bleeds (0-24 px a
        frame), so the engine's BloodColor spray carries the blood now. What
        holds: the corpse O, held for ever, is the lowest frame of its set,
        no higher over z than any death frame before it and lower than every
        living frame (measured: SDPMO0 rises 44 px, the living 63-65; SDPSO0
        50, the living 71-73)."""
        def rise(name: str) -> int:
            data = (PANZER_SPRITES / f"{name}.png").read_bytes()
            with Image.open(PANZER_SPRITES / f"{name}.png") as img:
                top = img.getchannel("A").getbbox()[1]
            return read_grab(data)[1] - top

        for sprite in (BASE, HEAVY):
            corpse = rise(f"{sprite}{FLAT_FRAMES[-1]}0")
            living = min(rise(f"{sprite}{f}{r}") for f in ROTATED_FRAMES for r in ROTATIONS_8)
            self.assertLess(corpse, living, sprite)
            for f in FLAT_FRAMES[:-1]:
                self.assertLessEqual(corpse, rise(f"{sprite}{f}0"), f"{sprite}{f}0")


    @unittest.skipUnless(WORK_FULL.is_dir(), "work/ not present (CI has no work/)")
    def test_the_rig_set_no_longer_ships(self):
        """D109: every lump of the set is the Gemini redraw, none the rig
        render it replaced (that set stays in work/, history)."""
        for p in installed():
            if not p.stem.startswith((BASE, HEAVY)):
                continue
            old = WORK_FULL / p.stem[:4] / p.name
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
            self.assertFalse([n for n in names if n.startswith("sprites/panzermensch")], "the set folder is dropped")

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)
        self.assertGreaterEqual(report.stats["sprites"], len(installed()))

    def test_every_lump_has_a_licence_row(self):
        declared = check_pk3.licensed_names(check_pk3.DEFAULT_LICENSES)
        missing = sorted(n for n in EXPECTED_LUMPS if n not in declared)
        self.assertEqual([], missing, "no row in docs/art/LICENSES.md")


def _built_maps(pk3: Path) -> dict[str, dict[str, list[dict]]]:
    """{map: {kind: [fields]}} for every map in the PK3, from its TEXTMAP."""
    out = {}
    with zipfile.ZipFile(pk3) as zf:
        for name in zf.namelist():
            if not (name.startswith("maps/") and name.endswith(".wad")):
                continue
            blob = zf.read(name)
            directory = check_pk3.read_wad_directory(blob)
            textmap = next(blob[o:o + s] for n, o, s in directory if n == "TEXTMAP")
            udmf = check_pk3.parse_udmf(textmap.decode("latin-1"))
            out[Path(name).stem] = {k: [b.fields for b in udmf.of_kind(k)]
                                    for k in ("vertex", "linedef", "sidedef", "sector", "thing")}
    return out


class _Geometry:
    """Just enough of a UDMF map to place a body: sectors, lines, doors."""

    def __init__(self, blocks: dict[str, list[dict]]):
        verts = [(float(v["x"]), float(v["y"])) for v in blocks["vertex"]]
        sides = blocks["sidedef"]
        self.floor = [float(s.get("heightfloor", 0)) for s in blocks["sector"]]
        self.ceiling = [float(s.get("heightceiling", 0)) for s in blocks["sector"]]
        self.lines = []
        for ld in blocks["linedef"]:
            front = int(sides[int(ld["sidefront"])]["sector"])
            back = int(sides[int(ld["sideback"])]["sector"]) if "sideback" in ld else None
            solid = back is None or ld.get("blocking") == "true" or ld.get("blockmonsters") == "true"
            self.lines.append((verts[int(ld["v1"])], verts[int(ld["v2"])], front, back, solid))
        neighbours = defaultdict(set)
        for _, _, f, b, _ in self.lines:
            if b is not None and b != f:
                neighbours[f].add(b)
                neighbours[b].add(f)
        # Every shut door open, as a monster chasing the player finds it.
        self.open_ceiling = [
            (min(self.ceiling[n] for n in neighbours[i]) - DOOR_OPENS_BELOW_CEILING)
            if self.ceiling[i] == self.floor[i] and neighbours[i] else self.ceiling[i]
            for i in range(len(self.floor))]

    def sectors_at(self, x: float, y: float) -> list[int]:
        crossings: dict[int, int] = defaultdict(int)
        for (x1, y1), (x2, y2), f, b, _ in self.lines:
            if f == b or (y1 > y) == (y2 > y):
                continue
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
                for s in (f, b):
                    if s is not None:
                        crossings[s] += 1
        return [s for s, n in crossings.items() if n % 2]

    @staticmethod
    def crosses_box(a, b, x0, y0, x1, y1) -> bool:
        (ax, ay), (bx, by) = a, b
        dx, dy, t0, t1 = bx - ax, by - ay, 0.0, 1.0
        for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
            if p == 0:
                if q < 0:
                    return False
            else:
                r = q / p
                t0, t1 = (max(t0, r), t1) if p < 0 else (t0, min(t1, r))
        return t0 <= t1

    def stand(self, x: float, y: float, radius: int) -> tuple[list, set[int]]:
        """(walls inside the body's box, sectors the box touches)."""
        walls, touched = [], set(self.sectors_at(x, y))
        for a, b, f, back, solid in self.lines:
            if not self.crosses_box(a, b, x - radius, y - radius, x + radius, y + radius):
                continue
            if solid:
                walls.append((a, b))
            else:
                touched |= {f, back}
        return walls, touched

    def passages_between(self, low: int, high: int) -> list:
        """Two-sided lines, doors open, whose opening is in [low, high)."""
        out = []
        for a, b, f, back, solid in self.lines:
            if solid or back == f:
                continue
            opening = min(self.open_ceiling[f], self.open_ceiling[back]) - max(self.floor[f], self.floor[back])
            if low <= opening < high:
                out.append((a, b, opening))
        return out


class MapFitTests(unittest.TestCase):
    """D67, step 5: the Schwer's 27 x 72 is only raised if it fits where the
    maps put him. Measured on the built maps, 2026-10-14: MAP03 places him
    twice on skills 4-5 (3290,256 on the tank line, ceiling 256; 520,1550 in
    the portal hall, ceiling 384), the range once (1600,1600, ceiling 192);
    MAP01 and MAP02 never."""

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
            things = [t for t in blocks["thing"] if t.get("type") in SCHWER_NUMBERS]
            if things:
                yield name, _Geometry(blocks), things

    def test_the_schwer_is_placed_where_the_design_says(self):
        self.assertIn("MAP03", {name for name, _, _ in self.placements()})

    def test_every_schwer_fits_where_it_stands(self):
        for name, geo, things in self.placements():
            for t in things:
                x, y = float(t["x"]), float(t["y"])
                where = f"{name} ({x:.0f}, {y:.0f})"
                own = geo.sectors_at(x, y)
                self.assertEqual(len(own), 1, f"{where}: not inside exactly one sector")
                walls, touched = geo.stand(x, y, HEAVY_RADIUS)
                self.assertEqual([], walls, f"{where}: a wall inside the {HEAVY_RADIUS}-unit box")
                opening = min(geo.ceiling[s] for s in touched) - max(geo.floor[s] for s in touched)
                self.assertGreaterEqual(opening, HEAVY_HEIGHT, where)
                step = max(geo.floor[s] for s in touched) - geo.floor[own[0]]
                self.assertLessEqual(step, MAX_STEP_UP, where)

    def test_no_route_admits_the_base_but_not_the_schwer(self):
        for name, geo, _ in self.placements():
            self.assertEqual([], geo.passages_between(BASE_HEIGHT, HEAVY_HEIGHT), name)


class OverlayTests(unittest.TestCase):
    def test_the_overlay_names_nothing_of_the_panzermensch(self):
        for swap in mdo.SWAPS:
            self.assertFalse({swap.placeholder, swap.draft} & {OLD, BASE, HEAVY}, swap)
            self.assertNotIn("panzer", swap.zs)


if __name__ == "__main__":
    unittest.main()
