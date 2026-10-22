"""D109 and D114 (2026-10-22): the seven enemies redrawn from Google Gemini ship.

The CEO had the seven enemy classes redone with Google Gemini (D105),
approved them ("Ok enemigos gemini", D109,
docs/art/previews/2026-10-22_P4_enemies-gemini.html) and then the D12
symbol D108's mix put on the Reich armbands ("Ok a lo de las esvásticas!",
D114, docs/art/previews/2026-10-22_P4_armbands-applied.png). The lumps
`tools/art/gemini_enemy.py all` builds into work/art/enemies_gemini/<set>/
overwrite, name for name, the rig-drawn sets in assets/sprites/ (MOD-SPEC
6.3, "The seven enemies redrawn from Google Gemini"). The per-enemy files
(tests/test_<enemy>_sprites.py) keep the state machines, the lump lists,
the canvases and the bodies; this file holds what the install itself
promises. What is checked, and why:

  files     each set is exactly the lump names it had before D109 (no lump
            added, none removed, so no orphan and no duplicate frame); where
            work/ exists each is byte-identical to work/art/enemies_gemini/,
            and where the Gemini sheets and the Fooocus cache exist a fresh
            build reproduces them (both skip cleanly on CI; the rebuild,
            ~1 min, runs at `art`, not at `fast`)
  drawing   gemini_enemy's placement: RGBA with hard alpha (palette v2 is
            tests/test_palette_v2.py's),
            `left` half the canvas, the feet's last row FEET_SINK under
            `top` (the Doughboy's head DOUGHBOY_SINK), one canvas a frame
            across its rotations; the hound keeps its mirrored pairs
  package   check_pk3 passes the sprites and the licences
  licences  each lump has an own-work row (CC BY-NC-SA 4.0) saying it is
            derived from Google Gemini images by gemini_enemy.py and that the
            sources are not distributed; the Reich sets name armband_symbol.py
            and Fooocus/SDXL (D108); the projectiles keep their rig rows
  credits   the release reads `enemies` and `armbands` from the packed rows
            and its AI text says so in English and Russian; the in-game
            credits name the enemies (EN, RU, CA) within 40 characters
  history   the rig generators say they are historical and are not deleted

Stdlib only, but for the drawing checks and the rebuild (Pillow, numpy).
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
ASSET_SPRITES = PROJECT_ROOT / "assets" / "sprites"
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "enemies_gemini"
REF_DIR = PROJECT_ROOT / "work" / "art" / "reference" / "enemies" / "gemini"
FOOOCUS_CACHE = PROJECT_ROOT / "work" / "art" / "armband_fooocus" / "cache"
LANGUAGE = SRC_DIR / "lumps" / "LANGUAGE"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import release  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_rifleman_sprites import PNG_SIGNATURE, read_grab  # noqa: E402

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy  # noqa: F401  (gemini_enemy needs it)
    import gemini_enemy as ge
    HAVE_NUMPY = HAVE_PIL
except ImportError:
    HAVE_NUMPY = False

ROT8 = "12345678"
PAIRS = ("1", "2{f}8", "3{f}7", "4{f}6", "5")


def lumps(prefix: str, rotated: str, flat: str, pairs: bool = False) -> frozenset[str]:
    """The lump names of a set: eight rotations a frame, or Doom's mirrored
    pairs (five lumps a frame), then the rotation-0 frames."""
    if pairs:
        out = {f"{prefix}{f}" + r.format(f=f) for f in rotated for r in PAIRS}
    else:
        out = {f"{prefix}{f}{r}" for f in rotated for r in ROT8}
    return frozenset(out | {f"{prefix}{f}0" for f in flat})


# gemini_enemy key -> (assets/sprites/ folder, prefix, the lump set it had
# before D109 and keeps, whether the D12 symbol is on it: D108).
SETS = {
    "rifleman": ("rifleman", "SDRR", lumps("SDRR", "ABCDEFG", "HIJKLMNOPQRSTU"), True),
    "legion": ("legion", "SDLT", lumps("SDLT", "ABCDEFG", "HIJKLMNOPQRSTU"), False),
    "storm": ("storm", "SDHS", lumps("SDHS", "ABCDEFGH", "IJKLMNOPQRSTU"), True),
    "hound": ("hound", "SDHN", lumps("SDHN", "ABCDEFGH", "IJKLMN", pairs=True), False),
    "doughboy": ("doughboy", "SDDB", lumps("SDDB", "ABCDEF", "GHIJKL"), False),
    "panzer": ("panzermensch", "SDPM", lumps("SDPM", "ABCDEFGH", "IJKLMNO"), True),
    "panzer_heavy": ("panzermensch", "SDPS", lumps("SDPS", "ABCDEFGH", "IJKLMNO"), True),
    "general": ("general", "SDGN", lumps("SDGN", "ABCDEFGQR", "HIJKLMNOP"), True),
}
COUNTS = {"rifleman": 70, "legion": 70, "storm": 77, "hound": 46, "doughboy": 54,
          "panzer": 71, "panzer_heavy": 71, "general": 81}
TOTAL = 540
PROJECTILES = {"SDBL", "SDGL", "SDDL", "SDPL"}    # not redrawn: their rig rows stay
FEET_SINK = 4           # gemini_enemy.FEET_SINK: the feet's last row under `top`
DOUGHBOY_SINK = 14      # gemini_enemy.DOUGHBOY_SINK: the floating head hangs under z
CREDIT_MAX = 40         # tests/test_credits.py MAX_CREDIT_LINE_CHARS
ENEMY_WORD = {"default": "enemies", "ru": "врагов", "ca": "enemics"}
ARMBAND_WORD = {"default": "armbands", "ru": "символ", "ca": "braçals"}
HISTORICAL = ("gen_enemy", "gen_rig", "gen_legion", "gen_storm", "gen_hound", "gen_heavy",
              "gen_general")
SKIP_SLOW = os.environ.get("SD_SKIP_SLOW_ART") == "1"


def installed(key: str) -> dict[str, Path]:
    folder, prefix, _, _ = SETS[key]
    d = ASSET_SPRITES / folder
    return {p.stem: p for p in sorted(d.glob(f"{prefix}*.png"))} if d.is_dir() else {}


def frame_of(name: str) -> str:
    return name[4]


class FileTests(unittest.TestCase):
    def test_every_set_keeps_its_names(self):
        total = 0
        for key, (_, _, expected, _) in SETS.items():
            names = set(installed(key))
            self.assertEqual(names, set(expected), key)
            self.assertEqual(len(names), COUNTS[key], key)
            total += len(names)
        self.assertEqual(total, TOTAL)

    def test_no_orphan_and_no_duplicate_frame(self):
        """Each (sprite, frame, rotation) is drawn by exactly one lump, as
        check_pk3 reads mirrored pairs."""
        for key in SETS:
            slots: dict[tuple[str, str], str] = {}
            for name in installed(key):
                halves = [(name[4], name[5])] + ([(name[6], name[7])] if len(name) == 8 else [])
                for slot in halves:
                    self.assertNotIn(slot, slots, f"{name} and {slots.get(slot)}")
                    slots[slot] = name

    @unittest.skipUnless(WORK_ROOT.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_gemini_build(self):
        for key in SETS:
            for name, path in installed(key).items():
                source = WORK_ROOT / key / path.name
                self.assertTrue(source.is_file(), source)
                self.assertEqual(path.read_bytes(), source.read_bytes(), name)

    @unittest.skipUnless(HAVE_NUMPY, "Pillow and numpy not available in this interpreter")
    @unittest.skipUnless(REF_DIR.is_dir() and FOOOCUS_CACHE.is_dir(),
                         "the Gemini sheets and the Fooocus cache are not here (gitignored, D77)")
    @unittest.skipIf(SKIP_SLOW, "rebuilding the seven sets takes a minute: art tier")
    def test_a_fresh_build_reproduces_the_installed_lumps(self):
        with tempfile.TemporaryDirectory(prefix="sd-gemini-enemy-") as tmp:
            for key in SETS:
                out = Path(tmp) / key
                ge.build(ge.ENEMIES[key], out)
                for name, path in installed(key).items():
                    self.assertEqual((out / path.name).read_bytes(), path.read_bytes(), name)

    @unittest.skipUnless(HAVE_NUMPY, "Pillow and numpy not available in this interpreter")
    def test_the_tool_still_never_writes_assets(self):
        """The install is a copy the PM approved, never a build into assets/."""
        self.assertIn("assets", ge.FORBIDDEN_OUT)
        with self.assertRaises(SystemExit):
            ge.guard_out(ASSET_SPRITES / "rifleman")


@unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
class DrawingTests(unittest.TestCase):
    def test_rgba_hard_alpha(self):
        """Palette v2 is test_palette_v2's check (GEMINI_ENEMIES there)."""
        for key in SETS:
            for name, path in installed(key).items():
                with Image.open(path) as img:
                    self.assertEqual(img.mode, "RGBA", name)
                    hist = img.getchannel("A").histogram()
                self.assertFalse(any(hist[1:255]), f"{name}: soft alpha")

    def test_offsets_are_the_axis_and_the_floor_line(self):
        for key in SETS:
            sink = DOUGHBOY_SINK if key == "doughboy" else FEET_SINK
            for name, path in installed(key).items():
                data = path.read_bytes()
                self.assertTrue(data.startswith(PNG_SIGNATURE), name)
                grab = read_grab(data)
                self.assertIsNotNone(grab, f"{name}: no grAb before IDAT")
                width, height = struct.unpack(">II", data[16:24])
                left, top = grab
                self.assertEqual(left, width // 2, name)
                with Image.open(path) as img:
                    box = img.getchannel("A").getbbox()
                self.assertEqual(box[3] - 1, top + sink, f"{name}: last row {box[3] - 1}, top {top}")

    def test_one_canvas_per_frame_across_rotations(self):
        for key in SETS:
            canvases: dict[str, set] = {}
            for name, path in installed(key).items():
                data = path.read_bytes()
                canvases.setdefault(frame_of(name), set()).add(
                    (struct.unpack(">II", data[16:24]), read_grab(data)))
            for frame, seen in canvases.items():
                self.assertEqual(len(seen), 1, f"{key} {frame}: {seen}")


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


class LicenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
        # Each row names its lumps one by one (backticked stems), so a stem
        # index finds a lump's rows without 540 passes over the register.
        cls.index: dict[str, list] = {}
        for r in rows:
            for t in r.tokens:
                cls.index.setdefault(t.upper(), []).append(r)

    def row(self, name: str):
        found = self.index.get(name, [])
        self.assertEqual(len(found), 1, f"{name}: {len(found)} rows in docs/art/LICENSES.md")
        self.assertTrue(found[0].covers(f"sprites/{name}.png"), name)
        return found[0]

    def test_every_lump_has_a_gemini_row(self):
        for key, (_, _, expected, symbol) in SETS.items():
            for name in sorted(expected):
                row = self.row(name)
                self.assertTrue(row.own_work, name)
                self.assertEqual(row.required, licences.OWN_WORK_CREDITS, name)
                self.assertIn("derived from Google Gemini images", row.origin, name)
                self.assertIn("tools/art/gemini_enemy.py", row.origin, name)
                self.assertIn("the source images are not distributed", row.origin, name)
                for word in ("armband_symbol.py", "Fooocus/SDXL", "D108"):
                    (self.assertIn if symbol else self.assertNotIn)(word, row.origin, name)

    def test_the_projectiles_keep_their_rig_rows(self):
        for prefix in PROJECTILES:
            for frame in "ABCDE":
                row = self.row(f"{prefix}{frame}0")
                self.assertNotIn("Gemini", row.origin, prefix)
                self.assertTrue(row.own_work, prefix)


class CreditTests(unittest.TestCase):
    def test_the_release_reads_the_enemies_from_the_packed_rows(self):
        # one lump a set is enough to read what ships (all 540: the licence tests)
        names = [f"sprites/{min(SETS[key][2])}.png" for key in SETS]
        rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
        credits = release.parse_credit_lines(LANGUAGE.read_text(encoding="utf-8"))
        check = release.check_licences(names, rows, [], credits)
        self.assertEqual(check.errors, [])
        ships = release.ai_ships(check)
        self.assertTrue(ships.enemies)
        self.assertTrue(ships.armbands)
        self.assertFalse(ships.face)

    def test_the_ai_text_follows_what_ships(self):
        on = release.AiShips(enemies=True, armbands=True)
        en = " ".join(release.ai_disclosure(release.LANG_ENGLISH, on))
        ru = " ".join(release.ai_disclosure(release.LANG_RUSSIAN, on))
        self.assertIn("The sprites of the seven enemies were redrawn", en)
        self.assertIn("armbands", en)
        self.assertNotIn("rendered their sprites from it", en)
        self.assertIn("спрайты семи врагов", ru)
        self.assertIn("повязках", ru)
        off = " ".join(release.ai_disclosure(release.LANG_ENGLISH))
        self.assertNotIn("seven enemies", off)
        self.assertNotIn("armbands", off)
        for lang in (release.LANG_ENGLISH, release.LANG_RUSSIAN):
            for line in release.render_made_with(lang, on).splitlines():
                self.assertLessEqual(len(line), 78, line)

    def test_the_in_game_credits_name_the_enemies(self):
        credits = release.parse_credit_lines(LANGUAGE.read_text(encoding="utf-8"))
        for lang, word in ENEMY_WORD.items():
            lines = [text for ident, text in credits[lang] if ident.startswith("SD_CRED_AI_")]
            joined = " ".join(lines)
            self.assertIn("Google Gemini", joined, lang)
            self.assertIn(word, joined, lang)
            self.assertIn(ARMBAND_WORD[lang], joined, lang)
            self.assertIn("Fooocus / SDXL", joined, lang)
            for line in lines:
                self.assertLessEqual(len(line), CREDIT_MAX, f"[{lang}] {line!r}")


class HistoryTests(unittest.TestCase):
    def test_the_rig_generators_say_they_are_history(self):
        for name in HISTORICAL:
            path = TOOLS_DIR / "art" / f"{name}.py"
            self.assertTrue(path.is_file(), path)
            head = path.read_text(encoding="utf-8")[:1200]
            self.assertIn("HISTORICAL since D109", head, name)
            self.assertIn("gemini_enemy.py", head, name)


if __name__ == "__main__":
    unittest.main()
