"""D43: MAPINFO wires the title and MAP01 music to the lumps that ship.

Contract: docs/engine/MOD-SPEC.md 4.5. The lumps themselves (legal names,
clean MIDI, rights, reproducibility) are tests/test_music.py's, owned by
sound-designer; this suite pins only the wiring:

  * GameInfo's TitleMusic is D_SDINTL and MAP01's music is D_SDM01;
  * every `music` / `TitleMusic` value in MAPINFO is "" or a lump the PK3
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
MAP_MUSIC = {"MAP01": "D_SDM01", "MAP02": ""}

RE_MUSIC_VALUE = re.compile(r'^\s*(music|TitleMusic)\s*=\s*"([^"]*)"', re.M | re.I)
RE_MAP_BLOCK = re.compile(r'^map\s+(\w+)[^{]*\{(.*?)^\}', re.M | re.S | re.I)
RE_GAMEINFO = re.compile(r'^GameInfo\s*\{(.*?)^\}', re.M | re.S | re.I)


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

    def test_each_map_plays_its_music(self):
        for name, lump in MAP_MUSIC.items():
            self.assertIn(name, self.maps, f"no map {name} block")
            self.assertEqual(music_of(self.maps[name]), lump, name)

    def test_every_music_value_is_silence_or_a_packed_lump(self):
        values = RE_MUSIC_VALUE.findall(self.code)
        self.assertTrue(values, "MAPINFO names no music at all")
        for key, value in values:
            if value:
                self.assertIn(value.upper(), self.packed,
                              f'{key} = "{value}" is not in assets/music/: it would play nothing')


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
