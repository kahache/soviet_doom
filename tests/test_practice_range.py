"""D41: the weapons test range ships as a practice range; D62: as map RANGE.

The contract is docs/engine/MOD-SPEC.md 4.4 (and the episode-screen row of
6.6); the choice of a second episode over a main-menu item is
docs/engine/adr/007-practice-range-as-a-second-episode.md. What this suite
pins, statically:

  * MAPINFO declares three episodes, the campaign's two first (D104 added
    "The Road to Moscow") and the range last, each named by a `$SD_*` id
    that exists in every language (D7/D21);
  * the range is the lump RANGE, out of the MAPxx slots, which go to the
    campaign (D62: MAP01 -> MAP02 -> MAP03, tests/test_campaign.py);
  * the campaign never runs into the range: no map's `next` is RANGE, and
    no campaign map shares its cluster; the range's own exit ends cleanly,
    through its own cluster's text to the title screen;
  * the episode screen is redeclared as text, so Freedoom's M_EPISOD ("Which
    episode?") is never drawn: the logo, one SDMENU header that fits, and
    SmallFont LAST because the engine builds the episode items at run time
    in the descriptor's last font;
  * the packed PK3 carries all of it (MAPINFO, MENUDEF, LANGUAGE, RANGE).

What it cannot pin is what the engine draws; that is the PM's engine pass
(D26): the episode screen in English and Russian, and the range starting
from it.
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
from test_menudef import (  # noqa: E402  (shared helpers, one definition)
    FONTS,
    LOGO,
    MENU_FONT,
    MenudefTestCase,
    RE_FONT,
    RE_POSITION,
    RE_STATICPATCH,
    RE_STATICTEXT,
    REQUIRED_SECTIONS,
    SCREEN_WIDTH,
    SELECTOR_X_OFFSET,
    SKILL_FONT,
    SKILL_FONT_DIR,
    listmenu,
    text_width,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
MAPINFO = SRC / "lumps" / "MAPINFO"

CAMPAIGN_MAP = "MAP01"
# D62 (2026-10-14): the campaign is MAP01 -> MAP02 -> MAP03; MAP03 ends it.
# The full flow is pinned by tests/test_campaign.py; here only the range's
# isolation. D104 (P4): episode 2 is MAP04 -> MAP05 -> MAP06; D112 (P4):
# episode 3 is MAP07 -> MAP08 -> MAP09.
CAMPAIGN_MAPS = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06",
                 "MAP07", "MAP08", "MAP09")
# D62: the range left the MAPxx slots. Up to 8 characters, a WAD lump name;
# GZDoom's own mapinfo/doom2bfg.txt starts an episode on a non-MAPxx map
# (`episode level01`), which is the precedent this rests on.
RANGE_MAP = "RANGE"
RANGE_WAS = "MAP02"          # its slot until D62
MAX_LUMP_NAME = 8
RANGE_CLUSTER = 2
# MOD-SPEC 4.4: episode order is the menu order, the campaign first and the
# range last. D104 (P4) put episode 2, "The Road to Moscow" (MAP04), between
# them; its id is SD_EP03_NAME, the order the episodes were declared in.
# D112 (P4) put episode 3, "The Portal" (MAP07, SD_EP04_NAME), after it.
EPISODE_2_MAP = "MAP04"
EPISODE_3_MAP = "MAP07"
EPISODES = [(CAMPAIGN_MAP, "SD_EP01_NAME"), (EPISODE_2_MAP, "SD_EP03_NAME"),
            (EPISODE_3_MAP, "SD_EP04_NAME"), (RANGE_MAP, "SD_EP02_NAME")]
RANGE_EXIT_TEXT = "SD_END02_TEXT"
# D46 (2026-10-14): the CEO's player-facing name for the range, printed by
# the automap and the level-load line. It was "Engineering Test Range". The
# id follows the lump since D62 (it was SD_MAP02_NAME).
RANGE_TITLE_ID = "SD_RANGE_NAME"
RANGE_TITLE = {"default": "Training Ground", "ru": "Учебный полигон",
               "ca": "Camp d'instrucció"}   # P6 (D97), for the CEO's review
EPISODE_HEADER = "$SD_MNU_CHOOSEEPISODE"
# The engine's episode screen draws this Freedoom picture of English words.
FREEDOOM_EPISODE_GRAPHIC = "M_EPISOD"
# ZDoom's named end sequence: roll the ending, then the title screen.
END_TO_TITLE = "endtitle"

RE_BLOCK = re.compile(r'^(map|episode|cluster)\s+(\w+)[^{]*\{(.*?)^\}', re.M | re.S | re.I)


def mapinfo_code(text: str) -> str:
    return "\n".join(strip_comment(line) for line in text.splitlines())


def blocks(code: str, kind: str) -> list[tuple[str, str]]:
    """(name, body) of every `kind` block, in file order."""
    return [(name, body) for k, name, body in RE_BLOCK.findall(code) if k.lower() == kind]


def prop(body: str, key: str) -> str | None:
    match = re.search(rf'^\s*{key}\s*=\s*(.+?)\s*$', body, re.M | re.I)
    return match.group(1).strip().strip('"') if match else None


class PracticeRangeMapinfoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code = mapinfo_code(MAPINFO.read_text(encoding="utf-8"))
        cls.maps = dict(blocks(cls.code, "map"))
        cls.episodes = blocks(cls.code, "episode")
        cls.clusters = dict(blocks(cls.code, "cluster"))

    def test_the_episodes_campaign_first_range_last(self):
        self.assertIn("clearepisodes", self.code)
        got = [(name, prop(body, "name")) for name, body in self.episodes]
        self.assertEqual(got, [(m, "$" + ident) for m, ident in EPISODES])

    def test_episode_hotkeys_differ(self):
        keys = [prop(body, "key") for _name, body in self.episodes]
        self.assertTrue(all(keys), "every episode needs a hotkey")
        self.assertEqual(len(keys), len(set(keys)), keys)

    def test_the_campaign_never_runs_into_the_range(self):
        """No map leads to the range (MOD-SPEC 4.4, 4.6)."""
        for name, body in self.maps.items():
            self.assertNotEqual((prop(body, "next") or "").upper(), RANGE_MAP,
                                f"{name} leads into the practice range")

    def test_the_range_holds_no_mapxx_slot(self):
        """D62: the range is not a MAPxx map, its old slot is the metro's, and
        its lump name fits a WAD directory."""
        self.assertIn(RANGE_MAP, self.maps)
        self.assertNotRegex(RANGE_MAP, r"^MAP\d\d$")
        self.assertLessEqual(len(RANGE_MAP), MAX_LUMP_NAME)
        self.assertRegex(RANGE_MAP, r"^[A-Z0-9_]+$")
        self.assertIn(RANGE_WAS, CAMPAIGN_MAPS, "the range's old slot belongs to the campaign")
        self.assertNotEqual(prop(self.maps[RANGE_WAS], "cluster"), str(RANGE_CLUSTER))

    def test_no_campaign_map_shares_the_ranges_cluster(self):
        """Sharing cluster 2 would print the range's text after a campaign
        map, or the campaign's ending after the range."""
        for name in CAMPAIGN_MAPS:
            self.assertNotEqual(prop(self.maps[name], "cluster"), str(RANGE_CLUSTER), name)
        in_range_cluster = [n for n, b in self.maps.items() if prop(b, "cluster") == str(RANGE_CLUSTER)]
        self.assertEqual(in_range_cluster, [RANGE_MAP])

    def test_the_range_ends_cleanly_in_its_own_cluster(self):
        """It used to restart itself (`next = "MAP02"`, its slot then). Now it ends like the
        campaign, through its own cluster's text, not the campaign's ending."""
        body = self.maps[RANGE_MAP]
        self.assertEqual(prop(body, "next"), END_TO_TITLE)
        self.assertEqual(prop(body, "cluster"), str(RANGE_CLUSTER))
        cluster = self.clusters.get(str(RANGE_CLUSTER))
        self.assertIsNotNone(cluster, f"no cluster {RANGE_CLUSTER} block")
        self.assertRegex(cluster, rf'exittext\s*=\s*lookup\s*,\s*"{RANGE_EXIT_TEXT}"')
        self.assertRegex(cluster, r'flat\s*=\s*"SDFLR1"')


class EpisodeScreenTest(MenudefTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.episode = listmenu(cls.code, "EpisodeMenu")

    def test_episode_menu_is_redeclared(self):
        self.assertIsNotNone(self.episode, 'no LISTMENU "EpisodeMenu" in MENUDEF')

    def test_m_episod_is_never_drawn(self):
        self.assertNotIn(FREEDOOM_EPISODE_GRAPHIC, self.code)
        patches = RE_STATICPATCH.findall(self.episode)
        self.assertEqual([(int(x), int(y), n) for x, y, n in patches], [(*LOGO, "M_DOOM")])

    def test_netgame_message_is_kept(self):
        """The engine's body refuses New Game in a net game with $NEWGAME."""
        self.assertRegex(self.episode, r'^\s*NetgameMessage\s+"\$NEWGAME"', )

    def test_header_is_sdmenu_text_in_both_languages(self):
        texts = RE_STATICTEXT.findall(self.episode)
        self.assertEqual([t[3] for t in texts], [EPISODE_HEADER])
        fonts = [(m.start(), m.group(1)) for m in RE_FONT.finditer(self.episode)]
        match = RE_STATICTEXT.search(self.episode)
        in_force = [name for pos, name in fonts if pos < match.start()]
        self.assertEqual(in_force[-1].upper(), MENU_FONT)
        for code in REQUIRED_SECTIONS:
            self.assertIn(EPISODE_HEADER[1:], self.sections[code], f"[{code}]")

    def test_the_episode_names_font_comes_last(self):
        """The items are built at run time in the descriptor's LAST font. The
        names are proper nouns (D22): SmallFont, never SDMENU."""
        fonts = RE_FONT.findall(self.episode)
        self.assertEqual(fonts[-1][0], SKILL_FONT)

    def test_header_fits_on_screen(self):
        if not (FONTS / MENU_FONT.lower()).is_dir():
            self.skipTest("no SDMENU yet; test_menudef reports it")
        for _c, x, _y, text in RE_STATICTEXT.findall(self.episode):
            for code in REQUIRED_SECTIONS:
                width = text_width(self.font_dir, self.string(code, text[1:]))
                self.assertLessEqual(int(x) + width, SCREEN_WIDTH, f"[{code}] {text} is {width} px")

    def test_episode_names_and_selector_fit_on_screen(self):
        positions = RE_POSITION.findall(self.episode)
        self.assertEqual(len(positions), 1, "the episode screen needs one Position")
        x = int(positions[0][0])
        self.assertGreaterEqual(x + SELECTOR_X_OFFSET, 0, "the skull would leave a 4:3 screen")
        for code in REQUIRED_SECTIONS:
            for _map, ident in EPISODES:
                self.assertIn(ident, self.sections[code], f"[{code}] lacks {ident}")
                name = self.string(code, ident).upper()
                width = text_width(SKILL_FONT_DIR, name)
                self.assertLessEqual(x + width, SCREEN_WIDTH, f"[{code}] {ident} is {width} px")

    def test_range_exit_text_exists_in_both_languages(self):
        for code in REQUIRED_SECTIONS:
            self.assertIn(RANGE_EXIT_TEXT, self.sections[code], f"[{code}]")

    def test_the_range_carries_the_ceos_name(self):
        """D46: "Training Ground" / «Учебный полигон», in both languages."""
        self.assertEqual(set(RANGE_TITLE), set(REQUIRED_SECTIONS))
        for code in REQUIRED_SECTIONS:
            self.assertEqual(self.string(code, RANGE_TITLE_ID), RANGE_TITLE[code], f"[{code}]")


class PracticeRangePk3Test(unittest.TestCase):
    """The same facts in the package the engine loads."""

    def test_the_package_carries_the_range(self):
        sys.path.insert(0, str(TOOLS))
        from sdbuild.pk3 import build as build_pk3

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            build_pk3(SRC, out, TOOLS)
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
                self.assertIn(f"maps/{RANGE_MAP}.wad", names)
                mapinfo = mapinfo_code(zf.read("MAPINFO").decode("utf-8"))
                menudef = zf.read("MENUDEF").decode("utf-8")
        self.assertRegex(mapinfo, rf"episode\s+{RANGE_MAP}\b")
        self.assertIsNotNone(listmenu(mapinfo_code(menudef), "EpisodeMenu"))


if __name__ == "__main__":
    unittest.main()
