"""D106, D113: episodes 2 and 3's A/B music and the boss loops of MAP06 and
MAP09 (SD_MusicVariant).

Contract: docs/engine/MOD-SPEC.md 4.5 and 6.11. What is pinned here, without
ever starting GZDoom (D26):

  * zscript.txt includes music_variant.zs once; the file declares one class,
    SD_MusicVariant : EventHandler, registered once in MAPINFO's
    AddEventHandlers after SD_LoadReporter;
  * the switches SD_MUSIC_VARIANTS_ENABLED and SD_BOSS_MUSIC_ENABLED exist
    and are on;
  * the table: SD_MUSIC_ROWS rows of SD_MUSIC_COLS cells, exactly MAP04-MAP06
    (D106) and MAP07-MAP09 (D113); each A is that map's `music` in MAPINFO,
    each B its approved pair, only MAP06 and MAP09 have boss lumps (MAP03,
    whose General is also a BOSS, has no row), and every lump is packed
    under music/ and licensed;
  * the behaviour the contract promises is in the code: a load is left to
    the engine (IsSaveGame), the draw uses a named play RNG, the B and the
    boss loop go through S_ChangeMusic, the boss is found by the BOSS flag
    and engaged by a player target or player damage, the guard puts back
    what the radio's hand-back of Level.Music undid, and no CVar, volume or
    map is written;
  * every engine name it relies on is declared in the installed gzdoom.pk3
    (skipped where GZDoom is absent, as in CI).

What it cannot pin is what the engine plays: the PM's pass (`currentmusic`
in MAP04-09 over several New Games, a save/load on a B, the boss loop on
MAP06 and MAP09 and none on MAP03).

Run:  python3 -m unittest tests.test_music_variant -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_death_prompt import gzdoom_pk3, strip_lump_comments  # noqa: E402
from test_mapinfo_music import RE_MAP_BLOCK, mapinfo_code, music_of  # noqa: E402
from test_pause_sign import strip_comments_and_strings  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
ZS = SRC / "zscript" / "sd" / "music_variant.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
MAPINFO = SRC / "lumps" / "MAPINFO"
MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"

INCLUDE = "zscript/sd/music_variant.zs"
CLASS = "SD_MusicVariant"
PARENT = "EventHandler"
FIRST_HANDLER = "SD_LoadReporter"
OVERRIDES = {"WorldLoaded", "WorldThingSpawned", "WorldThingDamaged", "WorldTick"}

# D106, D113: map -> (A, B, boss with A, boss with B). The A is MAPINFO's `music`.
TABLE = {"MAP04": ("D_SDM04A", "D_SDM04B", "", ""),
         "MAP05": ("D_SDM05A", "D_SDM05B", "", ""),
         "MAP06": ("D_SDM06A", "D_SDM06B", "D_SDBS6A", "D_SDBS6B"),
         "MAP07": ("D_SDM07A", "D_SDM07B", "", ""),
         "MAP08": ("D_SDM08A", "D_SDM08B", "", ""),
         "MAP09": ("D_SDM09A", "D_SDM09B", "D_SDBS9A", "D_SDBS9B")}
# The maps with a boss loop (D106: MAP06; D113: MAP09, the final boss).
BOSS_MAPS = {"MAP06", "MAP09"}
# MAP03's General must not swap the music.
NO_ROW = ("MAP01", "MAP02", "MAP03", "RANGE")


def raw() -> str:
    return ZS.read_text(encoding="utf-8")


def code() -> str:
    return strip_comments_and_strings(raw())


def const(name: str) -> str:
    match = re.search(rf"\bconst\s+{name}\s*=\s*([^;]+);", raw())
    assert match, f"no const {name}"
    return match.group(1).strip()


def table() -> dict[str, tuple[str, ...]]:
    body = re.search(r"SD_MUSIC_TABLE\[\]\s*=\s*\{(.*?)\};", raw(), re.S)
    assert body, "no SD_MUSIC_TABLE"
    text = re.sub(r"//[^\n]*", "", body.group(1))
    cells = re.findall(r'"([^"]*)"', text)
    cols = int(const("SD_MUSIC_COLS"))
    assert len(cells) % cols == 0, cells
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    return {row[0]: tuple(row[1:]) for row in rows}


class WiringTest(unittest.TestCase):
    def test_included_once(self):
        text = strip_lump_comments(ZSCRIPT_TXT.read_text(encoding="utf-8"))
        self.assertEqual(len(re.findall(rf'#include\s+"{re.escape(INCLUDE)}"', text)), 1)
        self.assertTrue(ZS.is_file())

    def test_one_event_handler_class(self):
        c = code()
        self.assertEqual(re.findall(r"\bclass\s+(\w+)\s*:\s*(\w+)", c), [(CLASS, PARENT)])
        self.assertEqual(c.count("{"), c.count("}"), "unbalanced braces")
        self.assertEqual(OVERRIDES, set(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", c)))

    def test_registered_once_after_the_load_reporter(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        lines = re.findall(r"(?im)^\s*AddEventHandlers\s*=\s*(.+)$", text)
        self.assertEqual(len(lines), 1, lines)
        names = re.findall(r'"([^"]+)"', lines[0])
        self.assertEqual(names[0], FIRST_HANDLER)
        self.assertEqual(names.count(CLASS), 1, names)

    def test_the_switches_exist_and_are_on(self):
        self.assertEqual("1", const("SD_MUSIC_VARIANTS_ENABLED"))
        self.assertEqual("1", const("SD_BOSS_MUSIC_ENABLED"))


class TableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = table()
        cls.maps = dict(RE_MAP_BLOCK.findall(mapinfo_code(MAPINFO.read_text(encoding="utf-8"))))

    def test_the_table_is_d106s_and_d113s(self):
        self.assertEqual(TABLE, self.table)
        self.assertEqual(len(TABLE), int(const("SD_MUSIC_ROWS")))
        self.assertEqual(5, int(const("SD_MUSIC_COLS")))

    def test_each_a_is_the_maps_mapinfo_music(self):
        for name, (a, *_rest) in self.table.items():
            with self.subTest(map=name):
                self.assertEqual(a, music_of(self.maps[name]))

    def test_no_other_map_has_a_row(self):
        for name in NO_ROW:
            self.assertNotIn(name, self.table)
        self.assertEqual(BOSS_MAPS, {m for m, row in self.table.items() if row[2] or row[3]})

    def test_every_lump_is_packed_and_licensed(self):
        packed = {p.stem for p in MUSIC_ASSETS.glob("*.mid")}
        licenses = LICENSES.read_text(encoding="utf-8")
        ships = MUSIC_RIGHTS.read_text(encoding="utf-8").split("### 4.5", 1)[1].split("\n### ", 1)[0]
        for row in self.table.values():
            for lump in filter(None, row):
                with self.subTest(lump=lump):
                    self.assertLessEqual(len(lump), 8)
                    self.assertIn(lump, packed)
                    self.assertIn(f"| `{lump}` |", licenses)
                    self.assertIn(f"| `{lump}` |", ships)

    def test_column_constants_match_the_layout(self):
        self.assertEqual(["0", "1", "2", "3", "4"],
                         [const(n) for n in ("SD_COL_MAP", "SD_COL_A", "SD_COL_B",
                                             "SD_COL_BOSS_A", "SD_COL_BOSS_B")])


class BehaviourTest(unittest.TestCase):
    def test_a_load_is_left_to_the_engine(self):
        c = code()
        self.assertRegex(c, r"e\.IsSaveGame\s*\|\|\s*e\.IsReopen")

    def test_the_draw_is_a_named_play_rng(self):
        self.assertRegex(code(), r"random\[SD_MusicVariant\]\(0,\s*1\)")
        self.assertIn("SD_MUSIC_VARIANTS_ENABLED &&", code())

    def test_the_music_changes_only_through_s_changemusic(self):
        c = code()
        self.assertGreaterEqual(c.count("S_ChangeMusic("), 3)
        for forbidden in ("SetMusicVolume", "snd_musicvolume", "CVar.", "S_StopMusic", "ACS_"):
            self.assertNotIn(forbidden, c)

    def test_the_boss_is_found_by_its_flag_and_engaged_by_a_player(self):
        c = code()
        self.assertIn("mo.bBOSS && mo.bISMONSTER", c)
        self.assertIn("mo.target.player != null", c)
        self.assertIn("e.DamageSource.player != null", c)
        self.assertNotIn("SD_General", c, "any BOSS monster, not the General's class")

    def test_the_guard_undoes_the_radios_hand_back(self):
        c = code()
        self.assertIn("musplaying.name ~== a", c)
        self.assertGreaterEqual(int(const("SD_MUSIC_GUARD_TICS")), 35)
        self.assertGreaterEqual(int(const("SD_BOSS_POLL_TICS")), 1)


class EngineNamesTest(unittest.TestCase):
    """Every engine name the handler uses is declared in gzdoom.pk3."""

    DECLARATIONS = {
        "S_ChangeMusic": r"native static bool S_ChangeMusic\(",
        "musplaying": r"@MusPlayingInfo musplaying",
        "IsSaveGame": r"native readonly bool IsSaveGame",
        "IsReopen": r"native readonly bool IsReopen",
        "DamageSource": r"native readonly Actor DamageSource",
        "WorldThingDamaged": r"virtual void WorldThingDamaged\(WorldEvent e\)",
        "WorldThingSpawned": r"virtual void WorldThingSpawned\(WorldEvent e\)",
        "maptime": r"native readonly int maptime",
        "MapName": r"native readonly String MapName",
        "ThinkerIterator": r"class ThinkerIterator",
    }

    @classmethod
    def setUpClass(cls):
        pk3 = gzdoom_pk3()
        if pk3 is None:
            raise unittest.SkipTest("GZDoom not installed here (CI)")
        with zipfile.ZipFile(pk3) as z:
            cls.corpus = "\n".join(z.read(n).decode("utf-8", "replace")
                                   for n in z.namelist() if n.lower().endswith(".zs"))

    def test_declared(self):
        for name, pattern in self.DECLARATIONS.items():
            with self.subTest(name=name):
                self.assertRegex(self.corpus, re.compile(pattern, re.M | re.I))
                self.assertRegex(code(), rf"\b{name}\b")


class PackageTest(unittest.TestCase):
    def test_the_package_carries_the_handler_and_every_lump(self):
        sys.path.insert(0, str(TOOLS))
        from sdbuild.pk3 import build as build_pk3

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            build_pk3(SRC, out, TOOLS, PROJECT_ROOT / "assets")
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
        self.assertIn(INCLUDE, names)
        for row in TABLE.values():
            for lump in filter(None, row):
                self.assertIn(f"music/{lump}.mid", names)


if __name__ == "__main__":
    unittest.main()
