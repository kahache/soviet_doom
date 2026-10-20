"""D63 (2026-10-14): the ammunition, the blue pass and the radio wear our own
sprites.

The CEO chose one option per object of the pickups sweep
(tools/art/gen_pickups.py): SDCL B, SDCB B, SDSL A, SDSB B, SDRA A, SDRB A,
SDFU A, SDFB B, SDKB B (the pass, frames A and B) and SDRD B (the radio).
MOD-SPEC 6.3, "The pickups, installed by D63". What is checked, and why:

  behaviour  the eight ammunition classes and SD_BluePass had no States
             block before D63: their Spawn was their Doom parent's. Each now
             declares only a Spawn label, and that label is the parent's
             line for line (label, frame letters, tics, Bright, flow) with
             only the four-letter name changed; the radio's States block is
             the pre-D63 one with PMAP renamed. Where a gzdoom.pk3 is
             installed the parents' lines are read from it and compared
             with the copy recorded here, so the "before" is the engine's
             and not a guess. Default blocks are untouched: nothing but the
             picture moves
  names      no state of the mod names a retired placeholder (CLIP, AMMO,
             SHEL, SBOX, ROCK, BROK, CELL, CELP, BKEY, PMAP); MOD-SPEC 5.1
             no longer declares PMAP and 6.3 reserves the ten names
  files      assets/sprites/pickups/ holds exactly the eleven PNGs, RGBA,
             each with a grAb chunk before its image data, centred and
             standing on the floor, and, where work/ exists, byte-identical
             to the CHOSEN option's render (and not to the other one)
  palette    the pass is the only one approved in palette v2 (cobalt, D45);
             it is RGBA, so it is in test_palette_v2's APPROVED_IN_V2 and
             not in check_pk3's PALETTE_V2_LUMPS (indexed lumps only)
  package    the built PK3 carries them as sprites/<NAME>.png, check_pk3's
             sprites and licences categories pass, every one has a row

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
SD_ZS = SRC_DIR / "zscript" / "sd"
PICKUPS = PROJECT_ROOT / "assets" / "sprites" / "pickups"
WORK_PICKUPS = PROJECT_ROOT / "work" / "art" / "pickups"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402
import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_palette_v2 import APPROVED_IN_V2  # noqa: E402

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_RGBA = 6   # IHDR colour type

# class -> (file under src/zscript/sd/, the gen_pickups object, the option
# the CEO chose in D63, the sprite before D63, ours)
PICKUP_CLASSES = {
    "SD_Clip":       ("ammo.zs",  "clip",      "B", "CLIP", "SDCL"),
    "SD_ClipBox":    ("ammo.zs",  "clipbox",   "B", "AMMO", "SDCB"),
    "SD_Shell":      ("ammo.zs",  "shell",     "A", "SHEL", "SDSL"),
    "SD_ShellBox":   ("ammo.zs",  "shellbox",  "B", "SBOX", "SDSB"),
    "SD_RocketAmmo": ("ammo.zs",  "rocket",    "A", "ROCK", "SDRA"),
    "SD_RocketBox":  ("ammo.zs",  "rocketbox", "A", "BROK", "SDRB"),
    "SD_Cell":       ("ammo.zs",  "fuel",      "A", "CELL", "SDFU"),
    "SD_CellPack":   ("ammo.zs",  "fuelpack",  "B", "CELP", "SDFB"),
    "SD_BluePass":   ("keys.zs",  "pass",      "B", "BKEY", "SDKB"),
    "SD_Radio":      ("radio.zs", "radio",     "B", "PMAP", "SDRD"),
}
RENAMED = {before: ours for _, _, _, before, ours in PICKUP_CLASSES.values()}

# The Doom parent each class inherited its Spawn from before D63 (the radio
# had its own States block and no parent's to read).
PARENT = {"SD_Clip": "Clip", "SD_ClipBox": "ClipBox", "SD_Shell": "Shell", "SD_ShellBox": "ShellBox",
          "SD_RocketAmmo": "RocketAmmo", "SD_RocketBox": "RocketBox", "SD_Cell": "Cell",
          "SD_CellPack": "CellPack", "SD_BluePass": "BlueCard"}
PARENT_FILE = {"BlueCard": "zscript/actors/doom/doomkeys.zs"}   # else doomammo.zs


def _ammo(sprite: str) -> tuple:
    return (("Spawn", sprite, "A", -1, ""), ("Spawn", "->", "Stop", 0, ""))


# The States each class ran with before D63, with the IWAD names: for the
# ammunition and the pass, the parent's, as GZDoom g4.14.2's gzdoom.pk3
# writes them (zscript/actors/doom/doomammo.zs, doomkeys.zs, read
# 2026-10-14); for the radio, src/zscript/sd/radio.zs as it stood at HEAD
# cdb47a9. Rows as in tests/test_weapon_sprites.py: (label, sprite, frames,
# tics, rest) for a state, (label, "->", flow, 0, "") for Goto/Loop/Stop.
# Flow keywords and flags are compared case-insensitively (the engine's own
# file writes `bright` and `loop`).
BEFORE_D63 = {
    "SD_Clip": _ammo("CLIP"), "SD_ClipBox": _ammo("AMMO"),
    "SD_Shell": _ammo("SHEL"), "SD_ShellBox": _ammo("SBOX"),
    "SD_RocketAmmo": _ammo("ROCK"), "SD_RocketBox": _ammo("BROK"),
    "SD_Cell": _ammo("CELL"), "SD_CellPack": _ammo("CELP"),
    "SD_BluePass": (("Spawn", "BKEY", "A", 10, ""), ("Spawn", "BKEY", "B", 10, "bright"),
                    ("Spawn", "->", "loop", 0, "")),
    "SD_Radio": _ammo("PMAP"),
}

# The Default blocks as they stood before D63 (whitespace collapsed,
# comments stripped): D63 changes pictures, not properties.
DEFAULTS_BEFORE_D63 = {
    "SD_Clip": 'Inventory.PickupMessage "$SD_GOT_CLIP";',
    "SD_ClipBox": 'Inventory.PickupMessage "$SD_GOT_CLIPBOX";',
    "SD_Shell": 'Inventory.PickupMessage "$SD_GOT_SHELLS";',
    "SD_ShellBox": 'Inventory.PickupMessage "$SD_GOT_SHELLBOX";',
    "SD_RocketAmmo": 'Inventory.PickupMessage "$SD_GOT_ROCKET";',
    "SD_RocketBox": 'Inventory.PickupMessage "$SD_GOT_ROCKBOX";',
    "SD_Cell": 'Inventory.PickupMessage "$SD_GOT_CELL";',
    "SD_CellPack": 'Inventory.PickupMessage "$SD_GOT_CELLPACK";',
    "SD_BluePass": 'Species "BlueCard"; Inventory.PickupMessage "$SD_PICKUP_BLUEPASS";',
    "SD_Radio": "Radius SD_RADIO_RADIUS; Height SD_RADIO_HEIGHT; +SOLID",
}

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$", re.I)


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def braced(text: str, open_at: int) -> str:
    """The body between the brace at `open_at - 1` and its match."""
    depth, i = 1, open_at
    while depth:
        if i >= len(text):
            raise AssertionError("unbalanced braces")
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[open_at:i - 1]


def class_body(code: str, name: str) -> str:
    m = re.search(rf"\bclass\s+{name}\b[^{{]*\{{", code)
    if m is None:
        raise AssertionError(f"no class {name}")
    return braced(code, m.end())


def block(body: str, keyword: str) -> str | None:
    m = re.search(rf"\b{keyword}\s*\{{", body)
    return None if m is None else braced(body, m.end())


def parse_states(body: str, where: str) -> list[tuple]:
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
            raise AssertionError(f"{where}: unparsed States line {line!r}")
    return rows


def norm(rows) -> list[tuple]:
    """Case-fold flow and flags only; sprite names and frames stay exact."""
    return [(lb, sp, fr, tics, rest.lower()) if sp != "->" else (lb, sp, fr.lower(), tics, rest)
            for lb, sp, fr, tics, rest in rows]


def source(zs_file: str) -> str:
    return strip_comments((SD_ZS / zs_file).read_text(encoding="utf-8"))


def states(cls: str) -> list[tuple]:
    body = block(class_body(source(PICKUP_CLASSES[cls][0]), cls), "States")
    if body is None:
        raise AssertionError(f"{cls}: no States block")
    return parse_states(body, cls)


def installed_gzdoom_pk3() -> Path | None:
    for exe in smoke.gzdoom_candidates():
        pk3 = exe.parent / "gzdoom.pk3"
        if pk3.is_file():
            return pk3
    return None


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


def expected_files() -> dict[str, tuple[str, str]]:
    """PNG name -> (gen_pickups object, chosen option)."""
    out = {}
    for _, obj, option, _, ours in PICKUP_CLASSES.values():
        for frame in ("AB" if ours == "SDKB" else "A"):
            out[f"{ours}{frame}0.png"] = (obj, option)
    return out


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d63_ones_but_for_the_name(self):
        for cls, before in BEFORE_D63.items():
            want = [(lb, RENAMED.get(sp, sp), fr, tics, rest) for lb, sp, fr, tics, rest in before]
            self.assertEqual(norm(states(cls)), norm(want), cls)

    def test_tic_totals_unchanged(self):
        for cls, before in BEFORE_D63.items():
            self.assertEqual(sum(r[3] for r in states(cls)), sum(r[3] for r in before), cls)

    def test_only_spawn_is_overridden(self):
        """A label declared in a subclass replaces that label only: nothing
        but Spawn may appear, or the pickup would behave differently."""
        for cls in PICKUP_CLASSES:
            self.assertEqual({r[0] for r in states(cls)}, {"Spawn"}, cls)

    def test_the_pass_blinks_like_dooms_keys(self):
        rows = [r for r in states("SD_BluePass") if r[1] != "->"]
        self.assertEqual([(r[1], r[2], r[3]) for r in rows], [("SDKB", "A", 10), ("SDKB", "B", 10)])
        self.assertEqual(rows[1][4].lower(), "bright")
        self.assertEqual(states("SD_BluePass")[-1][2].lower(), "loop")

    def test_default_blocks_unchanged(self):
        for cls, want in DEFAULTS_BEFORE_D63.items():
            body = block(class_body(source(PICKUP_CLASSES[cls][0]), cls), "Default")
            self.assertEqual(" ".join(body.split()), want, cls)

    def test_parents_are_unchanged_where_a_gzdoom_pk3_is_installed(self):
        """The recorded "before" is the engine's own: read the parents'
        Spawn from the installed gzdoom.pk3 (CI has none and skips)."""
        pk3 = installed_gzdoom_pk3()
        if pk3 is None:
            self.skipTest("no gzdoom.pk3 installed (CI): the recorded g4.14.2 copy stands in")
        with zipfile.ZipFile(pk3) as zf:
            files = {f: strip_comments(zf.read(f).decode("utf-8", "replace"))
                     for f in ("zscript/actors/doom/doomammo.zs", "zscript/actors/doom/doomkeys.zs")}
        for cls, parent in PARENT.items():
            code = files[PARENT_FILE.get(parent, "zscript/actors/doom/doomammo.zs")]
            rows = parse_states(block(class_body(code, parent), "States"), parent)
            self.assertEqual(norm(rows), norm(BEFORE_D63[cls]), parent)

    def test_the_parser_sees_every_line(self):
        self.assertEqual(len(states("SD_BluePass")), 3)
        with self.assertRaises(AssertionError):
            parse_states("  nonsense here\n", "x")
        with self.assertRaises(AssertionError):
            class_body("class Y {}", "X")


class NameTests(unittest.TestCase):
    def test_no_state_names_a_retired_placeholder(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            code = strip_comments(path.read_text(encoding="utf-8"))
            for old in RENAMED:
                self.assertNotRegex(code, rf"(?m)^\s*{old}\s+[A-Z]", f"{path.name} still names {old}")

    def test_mod_spec_5_1_retires_pmap(self):
        self.assertNotIn("PMAP", check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC))

    def test_mod_spec_6_3_reserves_the_ten_names(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        section = spec[spec.index("### 6.3 "):spec.index("### 6.4 ")]
        for cls, (_, _, _, _, ours) in PICKUP_CLASSES.items():
            self.assertRegex(section, rf"\| `{cls}` \| `{ours}` \|", cls)

    def test_names_are_distinct_and_ours(self):
        names = [v[4] for v in PICKUP_CLASSES.values()]
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertRegex(name, r"^SD[A-Z]{2}$")


class FileTests(unittest.TestCase):
    def test_exactly_the_chosen_pickups_are_installed(self):
        """D63's eleven, and since D80 the campaign pickups
        (tests/test_pickups_install.py owns those)."""
        from test_pickups_install import expected_files as d80_files
        self.assertFalse(set(expected_files()) & set(d80_files()))
        self.assertEqual({p.name for p in PICKUPS.glob("*")}, set(expected_files()) | set(d80_files()))

    def test_rgba_with_offsets_standing_on_the_floor(self):
        for name in expected_files():
            data = (PICKUPS / name).read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), name)
            width, height, _, colour_type = struct.unpack(">IIBB", data[16:26])
            self.assertEqual(colour_type, PNG_RGBA, f"{name}: sprites are RGBA (ART-BIBLE 2)")
            grab = read_grab(data)
            self.assertIsNotNone(grab, f"{name}: no grAb before IDAT, GZDoom would draw it at 0,0")
            self.assertEqual(grab, (width // 2, height), name)

    @unittest.skipUnless(WORK_PICKUPS.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_chosen_render(self):
        for name, (obj, option) in expected_files().items():
            installed = (PICKUPS / name).read_bytes()
            self.assertEqual(installed, (WORK_PICKUPS / obj / option / name).read_bytes(), name)
            other = WORK_PICKUPS / obj / ("A" if option == "B" else "B") / name
            if other.is_file():
                self.assertNotEqual(installed, other.read_bytes(), f"{name}: the other option")


class PaletteTests(unittest.TestCase):
    def test_only_the_pass_is_approved_in_v2(self):
        listed = {Path(p).name for p in APPROVED_IN_V2 if p.startswith("sprites/pickups/")}
        self.assertEqual(listed, {"SDKBA0.png", "SDKBB0.png"})
        for p in APPROVED_IN_V2:
            if p.startswith("sprites/pickups/"):
                self.assertTrue((PROJECT_ROOT / "assets" / p).is_file(), p)

    def test_the_pass_is_rgba_so_check_pk3_does_not_list_it(self):
        self.assertNotIn("SDKBA0", check_pk3.PALETTE_V2_LUMPS)
        self.assertNotIn("SDKBB0", check_pk3.PALETTE_V2_LUMPS)


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
            for name in expected_files():
                self.assertIn(f"sprites/{name}", names)
                self.assertEqual(zf.read(f"sprites/{name}"), (PICKUPS / name).read_bytes(), name)

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)

    def test_every_pickup_has_a_licence_row(self):
        licensed = check_pk3.licensed_names(LICENSES)
        for name in expected_files():
            self.assertIn(Path(name).stem, licensed, name)


if __name__ == "__main__":
    unittest.main()
