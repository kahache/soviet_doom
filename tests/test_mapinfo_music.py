"""D43, D62: MAPINFO wires the title and every map's music to lumps that ship.

Contract: docs/engine/MOD-SPEC.md 4.5. The lumps themselves (legal names,
clean MIDI, rights, reproducibility) are tests/test_music.py's, owned by
sound-designer; this suite pins only the wiring:

  * GameInfo's TitleMusic is D_SDINTL, its IntermissionMusic D_SDTITL
    (D83: the stats screen, instead of Freedoom's D_DM2INT), and MAP01's
    music is D_SDM1N2 (D95: composed for it under D92; D_SDM01 no longer ships);
  * D62 (N8): every map of the campaign plays music, walked from MAP01 along
    `next` to the end, so a map added to the chain without a piece fails
    here; MAP02 (the metro) and MAP03 (Tankograd) play the pieces assigned
    to them, and RANGE D_SDM01T since D86 (MAP01's theme cut to its melodic
    part; D83 rejected D_SDAMUR, which no longer ships);
  * D104 (P4): episode 2, walked from MAP04 to its end, plays music too;
    D106 gave it its own pieces: MAP04 D_SDM04A, MAP05 D_SDM05A, MAP06
    D_SDM06A (the A of each pair; SD_MusicVariant swaps in the B and MAP06's
    boss loop, tests/test_music_variant.py), and the stats screens after
    MAP04 and MAP05 play D_SDE2IA (`intermusic`), while every other map's
    falls back to GameInfo's D_SDTITL;
  * every lump MAPINFO names has a licence row in docs/art/LICENSES.md (the
    register check_pk3 reads) and a row in MUSIC-RIGHTS.md 4.5 (the one
    tools/release.py reads), and SOUNDTRACK.md still calls each draft one;
  * every `music` / `intermusic` / `TitleMusic` / `IntermissionMusic` value in MAPINFO is "" or a lump the PK3
    packs under music/. A misspelt music lump is the silent failure GZDoom
    does not log (SOUNDTRACK.md 7, qa gap 1), so a test is the only net;
  * the same holds in the built package.

What it cannot pin is that the engine plays them: the PM's engine pass
(`currentmusic` in the console, D26).
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_language import strip_comment  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
MAPINFO = SRC / "lumps" / "MAPINFO"
MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"

TITLE_MUSIC = "D_SDINTL"
INTERMISSION_MUSIC = "D_SDTITL"        # D83 (N9e): instead of Freedoom's D_DM2INT
MAP_MUSIC = {"MAP01": "D_SDM1N2",      # D95 (N9e): compose_map01.py's D_SDM01N2
             "MAP02": "D_SDFUNR",      # D62 draft: «Вы жертвою пали», the metro
             "MAP03": "D_SDGATE",      # D62 draft: «Богатырские ворота», Tankograd
             "RANGE": "D_SDM01T",      # D86: D_SDM01E from bar 49, MAP01's theme cut (N9e)
             # D106: episode 2's own pieces, the A of each approved pair.
             "MAP04": "D_SDM04A",
             "MAP05": "D_SDM05A",
             "MAP06": "D_SDM06A"}
# D106: the stats screen after these maps plays episode 2's intermission
# piece; no other map sets `intermusic` (they keep GameInfo's D_SDTITL).
INTER_MUSIC = {"MAP04": "D_SDE2IA", "MAP05": "D_SDE2IA"}
# D106: installed with their A but played only by SD_MusicVariant (or, for
# D_SDE2IB, the approved alternative nobody wires yet): never a MAPINFO value.
EPISODE2_UNWIRED = ("D_SDM04B", "D_SDM05B", "D_SDM06B", "D_SDBS6A", "D_SDBS6B", "D_SDE2IB")
RETIRED = ("D_SDAMUR", "D_SDM01")     # D83: NO for the range; D95: MAP01's new piece. Neither packed
# Assigned by N8 and wired so the CEO hears them in play.
DRAFTS = ("D_SDFUNR", "D_SDGATE")
CAMPAIGN_START = "MAP01"
# D104: each campaign episode's first map and its maps in play order.
EPISODE_CHAINS = {"MAP01": ["MAP01", "MAP02", "MAP03"],
                  "MAP04": ["MAP04", "MAP05", "MAP06"]}
END_OF_CHAIN = "endtitle"
DOCS = PROJECT_ROOT / "docs"
LICENSES = DOCS / "art" / "LICENSES.md"
MUSIC_RIGHTS = DOCS / "sound" / "MUSIC-RIGHTS.md"
SOUNDTRACK = DOCS / "sound" / "SOUNDTRACK.md"
DRAFT_MARK = "pending the CEO's ear"

RE_MUSIC_VALUE = re.compile(r'^\s*(music|intermusic|TitleMusic|IntermissionMusic)\s*=\s*"([^"]*)"',
                            re.M | re.I)
RE_MAP_BLOCK = re.compile(r'^map\s+(\w+)[^{]*\{(.*?)^\}', re.M | re.S | re.I)
RE_GAMEINFO = re.compile(r'^GameInfo\s*\{(.*?)^\}', re.M | re.S | re.I)
RE_NEXT = re.compile(r'^\s*next\s*=\s*"?(\w+)"?', re.M | re.I)


def mapinfo_code(text: str) -> str:
    return "\n".join(strip_comment(line) for line in text.splitlines())


def music_of(body: str, key: str = "music") -> str | None:
    for k, value in RE_MUSIC_VALUE.findall(body):
        if k.lower() == key.lower():
            return value
    return None


class MapinfoMusicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code = mapinfo_code(MAPINFO.read_text(encoding="utf-8"))
        cls.maps = dict(RE_MAP_BLOCK.findall(cls.code))
        cls.packed = {p.stem.upper() for p in MUSIC_ASSETS.glob("*.mid")}

    def test_title_music_is_the_internationale(self):
        gameinfo = RE_GAMEINFO.search(self.code)
        self.assertIsNotNone(gameinfo, "MAPINFO has no GameInfo block")
        self.assertEqual(music_of(gameinfo.group(1), "TitleMusic"), TITLE_MUSIC)

    def test_intermission_music_is_ours(self):
        gameinfo = RE_GAMEINFO.search(self.code)
        self.assertEqual(music_of(gameinfo.group(1), "IntermissionMusic"), INTERMISSION_MUSIC)
        self.assertIn(INTERMISSION_MUSIC, self.packed)

    def test_the_rejected_range_piece_is_gone(self):
        for lump in RETIRED:
            self.assertNotIn(lump, self.packed)
            self.assertNotIn(f'"{lump}"', self.code)

    def test_each_map_plays_its_music(self):
        for name, lump in MAP_MUSIC.items():
            self.assertIn(name, self.maps, f"no map {name} block")
            self.assertEqual(music_of(self.maps[name]), lump, name)

    def test_episode_2s_stats_screens_play_its_intermission(self):
        for name, block in self.maps.items():
            with self.subTest(map=name):
                self.assertEqual(INTER_MUSIC.get(name), music_of(block, "intermusic"))

    def test_episode_2s_other_pieces_ship_but_are_not_mapinfo_values(self):
        values = {value for _key, value in RE_MUSIC_VALUE.findall(self.code)}
        for lump in EPISODE2_UNWIRED:
            with self.subTest(lump=lump):
                self.assertIn(lump, self.packed)
                self.assertNotIn(lump, values)

    def test_every_music_value_is_silence_or_a_packed_lump(self):
        values = RE_MUSIC_VALUE.findall(self.code)
        self.assertTrue(values, "MAPINFO names no music at all")
        for key, value in values:
            if value:
                self.assertIn(value.upper(), self.packed,
                              f'{key} = "{value}" is not in assets/music/: it would play nothing')

    def campaign(self, start: str = CAMPAIGN_START) -> list[str]:
        chain, name = [], start
        while name.lower() != END_OF_CHAIN:
            self.assertIn(name, self.maps, f"the campaign leads to {name}, which has no block")
            self.assertNotIn(name, chain, f"the campaign loops back to {name}")
            chain.append(name)
            following = RE_NEXT.search(self.maps[name])
            self.assertIsNotNone(following, f"{name} has no next")
            name = following.group(1)
        return chain

    def test_every_campaign_map_plays_music(self):
        for start, order in EPISODE_CHAINS.items():
            chain = self.campaign(start)
            self.assertEqual(order, chain, "D62's and D104's campaign order")
            for name in chain:
                with self.subTest(map=name):
                    self.assertTrue(music_of(self.maps[name]),
                                    f"{name} is silent: every campaign map has a piece (D62, N8)")

    def test_every_music_lump_named_has_a_licence_in_both_registers(self):
        licenses = LICENSES.read_text(encoding="utf-8")
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        ships = rights.split("### 4.5", 1)[1].split("\n### ", 1)[0]
        for _key, value in RE_MUSIC_VALUE.findall(self.code):
            if value:
                with self.subTest(lump=value):
                    self.assertIn(f"| `{value}` |", licenses, "no row in LICENSES.md")
                    self.assertIn(f"| `{value}` |", ships, "no row in MUSIC-RIGHTS.md 4.5")

    def test_the_drafts_are_marked_as_drafts_in_the_soundtrack(self):
        text = SOUNDTRACK.read_text(encoding="utf-8")
        for lump in DRAFTS:
            with self.subTest(lump=lump):
                rows = [line for line in text.splitlines()
                        if line.startswith("|") and f"`{lump}`" in line and DRAFT_MARK in line]
                self.assertTrue(rows, f"SOUNDTRACK.md has no row calling {lump} a draft {DRAFT_MARK}")


class PackedMusicTest(unittest.TestCase):
    def test_the_package_carries_what_mapinfo_names(self):
        sys.path.insert(0, str(TOOLS))
        from sdbuild.pk3 import build as build_pk3

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            build_pk3(SRC, out, TOOLS, PROJECT_ROOT / "assets")
            with zipfile.ZipFile(out) as zf:
                packed = {Path(n).stem.upper() for n in zf.namelist()
                          if n.lower().startswith("music/")}
                code = mapinfo_code(zf.read("MAPINFO").decode("utf-8"))
        for key, value in RE_MUSIC_VALUE.findall(code):
            if value:
                self.assertIn(value.upper(), packed, f'{key} = "{value}" is not packed')


if __name__ == "__main__":
    unittest.main()
