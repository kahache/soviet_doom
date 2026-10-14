"""The diegetic radio (D43): SD_Radio and its two CC0 pieces.

Contract: docs/engine/MOD-SPEC.md 6.7; reasons:
docs/engine/adr/008-diegetic-radio.md. What is pinned here, without ever
starting GZDoom (D26):

  * zscript.txt includes radio.zs once, and the file declares SD_Radio as an
    Actor with balanced braces, a SOLID body and its own sprite SDRD (D63;
    the IWAD placeholder PMAP until then);
  * the behaviour ADR 008 promises is in the code: S_ChangeMusic to swap,
    Level.Music to give back, a hysteresis margin, a transient re-sync after
    a load, and no write to the player's music volume;
  * the numbers MOD-SPEC 6.7 prints are the code's constants;
  * every piece the radio can name is a legal lump, installed in
    assets/music/ byte-identical to its CC0 candidate, licensed in both
    registers, and packed under music/ in the built PK3;
  * PMAP is retired from MOD-SPEC 5.1 (D63) and SDRD is free in freedoom2.wad;
  * editor number 21200 is in the decoration sub-range, written in MOD-SPEC
    6.1, and free: MAPINFO either does not use it yet or gives it to
    SD_Radio, and GZDoom's own MAPINFO does not claim it.

What it cannot pin is what the engine does with any of it: ADR 008's
checklist R1-R6, the PM's engine pass.

Run:  python3 -m unittest tests.test_radio -v
"""

from __future__ import annotations

import hashlib
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS))

import check_pk3  # noqa: E402
import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from sdbuild.wad import validate_lump_name  # noqa: E402
from test_bestiary import (IWAD, iwad_namespace, mapinfo_ednums, state_frames,  # noqa: E402
                           strip_zs_comments, zs_constants, zs_default)

RADIO_ZS = SRC / "zscript" / "sd" / "radio.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
INCLUDE = "zscript/sd/radio.zs"
MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"
CANDIDATES = PROJECT_ROOT / "work" / "audio" / "candidates"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
ADR = PROJECT_ROOT / "docs" / "engine" / "adr" / "008-diegetic-radio.md"

CLASS = "SD_Radio"
EDNUM = 21200                      # MOD-SPEC 6.1
DECORATION_RANGE = range(21200, 21300)
PLACEHOLDER_SPRITE = "PMAP"        # MOD-SPEC 5.1
FINAL_SPRITE = "SDRD"              # MOD-SPEC 6.3
# arg0 -> lump, and the CC0 candidate each lump is an unedited copy of (D43).
PIECES = {
    1: ("D_SDRAD1", "WM_Ej_uchnem.mid", "D_CND09"),
    2: ("D_SDRAD2", "WM_Kolokolchik.mid", "D_CND12"),
}
DEFAULT_PIECE = 1


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def radio_code() -> str:
    return strip_zs_comments(RADIO_ZS.read_text(encoding="utf-8"))


def piece_lumps_in_code(code: str) -> list[str]:
    """Every music lump the class can hand to S_ChangeMusic: the string
    literals of PieceLump."""
    body = re.search(r"String\s+PieceLump\s*\([^)]*\)\s*\{(.*?)^\t\}", code, re.S | re.M)
    assert body, "radio.zs has no PieceLump"
    return re.findall(r'return\s+"([^"]+)"', body.group(1))


class IncludeAndParseTest(unittest.TestCase):
    def test_zscript_txt_includes_the_radio_once(self):
        lines = [ln.split("//")[0].strip() for ln in ZSCRIPT_TXT.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(1, lines.count(f'#include "{INCLUDE}"'))
        self.assertTrue(RADIO_ZS.is_file())

    def test_the_class_is_an_actor_and_the_braces_balance(self):
        code = radio_code()
        self.assertRegex(code, rf"\bclass\s+{CLASS}\s*:\s*Actor\b")
        self.assertEqual(1, len(re.findall(r"\bclass\s+\w+", code)), "one class per file")
        self.assertEqual(code.count("{"), code.count("}"))
        self.assertEqual(code.count("("), code.count(")"))

    def test_it_replaces_nothing(self):
        """A decoration with its own number; no Doom thing turns into a radio."""
        self.assertNotRegex(radio_code(), r"\breplaces\b")

    def test_a_solid_body_the_size_of_the_placeholder(self):
        code = radio_code()
        consts = zs_constants(code)
        self.assertEqual("SD_RADIO_RADIUS", zs_default(code, "Radius"))
        self.assertEqual("SD_RADIO_HEIGHT", zs_default(code, "Height"))
        self.assertEqual(16, consts["SD_RADIO_RADIUS"], "half the 32-pixel-wide PMAP A")
        self.assertEqual(28, consts["SD_RADIO_HEIGHT"], "PMAP A is 28 pixels tall")
        self.assertRegex(code, r"\+SOLID\b")

    def test_the_states_wear_the_final_sprite(self):
        """D63: SDRD A replaced PMAP A (tests/test_pickup_sprites.py pins the tics)."""
        frames = state_frames(RADIO_ZS.read_text(encoding="utf-8"))
        self.assertEqual([(FINAL_SPRITE, "A")], frames)


class BehaviourInTheCodeTest(unittest.TestCase):
    """ADR 008's decisions, read in the code. The engine pass proves them."""

    @classmethod
    def setUpClass(cls):
        cls.code = radio_code()
        cls.consts = zs_constants(cls.code)

    def test_it_swaps_with_s_changemusic_and_gives_back_the_levels_music(self):
        self.assertIn("S_ChangeMusic(piece)", self.code)
        self.assertIn("S_ChangeMusic(Level.Music, Level.musicorder)", self.code)

    def test_it_gives_back_only_what_it_took(self):
        """D-008-4: the restore is guarded by the name of the song playing."""
        restore = self.code.index("S_ChangeMusic(Level.Music")
        guard = self.code.rfind("musplaying.name ~== piece", 0, restore)
        self.assertGreater(guard, 0, "the restore must check that the radio's piece is still playing")

    def test_hysteresis(self):
        """D-008-2: off strictly farther out than on."""
        self.assertGreater(self.consts["SD_RADIO_HYSTERESIS"], 0)
        self.assertIn("distance <= reach", self.code)
        self.assertIn("distance > reach + SD_RADIO_HYSTERESIS", self.code)

    def test_the_players_music_volume_is_never_touched(self):
        """D-008-3."""
        for forbidden in ("SetMusicVolume", "snd_musicvolume", "CVar.", "S_StopMusic", "StopMusic"):
            self.assertNotIn(forbidden, self.code, forbidden)

    def test_saved_games_resync(self):
        """D-008-5: the ownership is saved, the re-sync flag is not."""
        self.assertRegex(self.code, r"(?m)^\s*bool\s+playing\s*;", "playing must be an ordinary (saved) field")
        self.assertRegex(self.code, r"(?m)^\s*transient\s+bool\s+synced\s*;")
        self.assertNotRegex(self.code, r"transient\s+bool\s+playing")

    def test_the_listener_is_the_local_player(self):
        self.assertIn("players[consoleplayer].mo", self.code)


class ContractNumbersTest(unittest.TestCase):
    """The code is the truth; MOD-SPEC 6.7 must print the same numbers."""

    @classmethod
    def setUpClass(cls):
        cls.consts = zs_constants(radio_code())
        spec = MOD_SPEC.read_text(encoding="utf-8")
        match = re.search(r"^## 6\.7 .*?$(.*?)(?=^## )", spec, re.S | re.M)
        assert match, "MOD-SPEC has no section 6.7"
        cls.section = match.group(1)

    def test_default_reach(self):
        value = int(self.consts["SD_RADIO_DEFAULT_REACH"])
        self.assertIn(f"`0` = **{value}** (`SD_RADIO_DEFAULT_REACH`)", self.section)

    def test_hysteresis(self):
        value = int(self.consts["SD_RADIO_HYSTERESIS"])
        self.assertIn(f"reach + {value}** (`SD_RADIO_HYSTERESIS`)", self.section)

    def test_editor_number_and_pieces(self):
        self.assertIn(f"**{EDNUM}**", self.section)
        for arg, (lump, _file, _cnd) in PIECES.items():
            self.assertIn(f"`{arg}` = `{lump}`", self.section)

    def test_piece_constants_match_the_table(self):
        self.assertEqual(1, self.consts["SD_RADIO_PIECE_EJ_UKHNEM"])
        self.assertEqual(2, self.consts["SD_RADIO_PIECE_KOLOKOLCHIK"])

    def test_the_adr_exists(self):
        self.assertTrue(ADR.is_file())
        self.assertIn(ADR.name, self.section)


class PiecesTest(unittest.TestCase):
    def test_the_code_names_exactly_the_two_pieces(self):
        lumps = piece_lumps_in_code(radio_code())
        self.assertEqual(sorted(lump for lump, _f, _c in PIECES.values()), sorted(set(lumps)))
        # the fall-through return is the default piece
        self.assertEqual(PIECES[DEFAULT_PIECE][0], lumps[-1])

    def test_each_piece_is_installed_byte_identical_to_its_cc0_candidate(self):
        for lump, source, _cnd in PIECES.values():
            with self.subTest(lump=lump):
                self.assertEqual(lump, validate_lump_name(lump))
                installed = MUSIC_ASSETS / f"{lump}.mid"
                self.assertTrue(installed.is_file(), installed)
                self.assertEqual(sha256(CANDIDATES / source), sha256(installed))

    def test_the_candidate_registry_agrees(self):
        registry = (CANDIDATES / "LUMPS.txt").read_text(encoding="utf-8")
        for _lump, source, cnd in PIECES.values():
            self.assertRegex(registry, rf"(?m)^{cnd}\s+{re.escape(source)}\s*$")

    def test_each_piece_is_licensed_in_both_registers(self):
        licenses = LICENSES.read_text(encoding="utf-8")
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        declared = check_pk3.licensed_names(LICENSES)
        for lump, _source, _cnd in PIECES.values():
            with self.subTest(lump=lump):
                self.assertIn(lump, declared, "tools/check_pk3.py would refuse to ship it")
                row = next(ln for ln in licenses.splitlines() if ln.startswith(f"| `{lump}`"))
                self.assertIn("CC0", row)
                self.assertIn("Peter Gerloff", row)
                self.assertIn(f"`{lump}`", rights)


class PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC, out, TOOLS, PROJECT_ROOT / "assets")
        with zipfile.ZipFile(out) as zf:
            cls.names = set(zf.namelist())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_class_and_both_pieces_are_packed(self):
        self.assertIn(INCLUDE, self.names)
        for lump, _source, _cnd in PIECES.values():
            self.assertIn(f"music/{lump}.mid", self.names)


class SpriteTest(unittest.TestCase):
    def test_the_placeholder_is_retired_from_mod_spec_5_1(self):
        """D63: no state names PMAP, and a 5.1 row nobody names is stale."""
        self.assertNotIn(PLACEHOLDER_SPRITE, check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC))

    def test_the_final_name_is_reserved(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertIn(f"**`{FINAL_SPRITE}`** A", spec)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not present (CI has no IWAD)")
    def test_frame_a_is_in_the_iwad_and_the_final_name_is_free(self):
        sprites, lumps = iwad_namespace(IWAD)
        self.assertIn(f"{PLACEHOLDER_SPRITE}A0", sprites)
        self.assertFalse(any(name.startswith(FINAL_SPRITE) for name in lumps))


class EditorNumberTest(unittest.TestCase):
    def test_in_the_decoration_sub_range_and_in_mod_spec_6_1(self):
        self.assertIn(EDNUM, DECORATION_RANGE)
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertRegex(spec, rf"\|\s*{EDNUM}\s*\|\s*`{CLASS}`")

    def test_mapinfo_does_not_give_it_to_anything_else(self):
        """The PM adds `21200 = SD_Radio`; until then the number is unused."""
        ednums = mapinfo_ednums()
        self.assertIn(ednums.get(EDNUM, CLASS), (CLASS,), f"{EDNUM} already belongs to {ednums.get(EDNUM)}")
        others = [num for num, cls in ednums.items() if cls == CLASS and num != EDNUM]
        self.assertEqual([], others, f"{CLASS} has a second number")

    def test_gzdoom_does_not_claim_it(self):
        pk3 = next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                    if (c.parent / "gzdoom.pk3").is_file()), None)
        if pk3 is None:
            self.skipTest("no gzdoom.pk3 on this machine (CI)")
        claimed = re.compile(rf"(?m)^\s*{EDNUM}\s*=")
        with zipfile.ZipFile(pk3) as zf:
            for name in zf.namelist():
                low = name.lower()
                if low.startswith(("mapinfo/", "filter/")) and low.endswith(".txt") or low == "mapinfo.txt":
                    text = zf.read(name).decode("latin-1")
                    self.assertIsNone(claimed.search(text), f"{name} assigns {EDNUM}")


if __name__ == "__main__":
    unittest.main()
