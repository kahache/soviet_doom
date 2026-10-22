"""D60, D62, D104, D112: the campaign is three episodes, in slot order.

Episode 1, "Soviet Doom": MAP01 -> MAP02 -> MAP03. D60 grew it past MAP01;
D62 (2026-10-14) gave the map slots the campaign's order: MAP01 Zarya-7,
MAP02 the metro-bunker (built as MAP03), MAP03 the factory, Tankograd (built
as MAP04), and the practice range left the MAPxx sequence for the lump RANGE
(it was MAP02).

Episode 2, "The Road to Moscow" (D104, P4): MAP04 the Trans-Siberian yard
at Sverdlovsk -> MAP05 the Volga dam -> MAP06 Red Square and the Kremlin. It
is a second episode on the New Game screen, between the first and the
range, and starts on MAP04; episode 1 does not run into it.

Episode 3, "The Portal" (D112, P4): MAP07 the Arctic radar station on Novaya
Zemlya -> MAP08 the Northern Fleet's submarine base at Severomorsk -> MAP09
the invaders' main portal at Tunguska. A third episode on the New Game
screen, after the second and before the range, started on MAP07; it ends
the first cycle, so its ending closes on THE END, not TO BE CONTINUED.

The contract is docs/engine/MOD-SPEC.md 4.6. What this suite pins,
statically, from MAPINFO and LANGUAGE:

  * each episode's order, each map leading to the next slot, the last one
    to endtitle; RANGE -> endtitle; the episodes are separate chains;
  * the clusters (MOD-SPEC 4.6's rule): cluster 1 is episode 1's ending and
    holds only MAP03, cluster 2 the range's, one transition cluster per
    earlier map numbered from 3 in play order (3 = MAP01's, 4 = MAP02's,
    5 = MAP04's, 6 = MAP05's, 8 = MAP07's, 9 = MAP08's), cluster 7 episode
    2's ending, MAP06's alone, and cluster 10 episode 3's, MAP09's alone;
    no `entertext`;
  * the flow as the engine walks it (a crossing between clusters prints the
    cluster's text): each episode prints its own transitions, then its own
    ending, each ONCE, and nothing of the other's; the range prints its own
    text and nothing of the campaign's;
  * the range is isolated: no map leads to it, no episode reaches it, and it
    holds no MAPxx slot;
  * every text in English, Russian and Catalan, broken by hand into lines
    that fit SmallFont on a 320-wide screen, with every glyph drawn.

What it cannot pin is what the engine shows: the PM's checks of MOD-SPEC
4.6 (D26).
"""

from __future__ import annotations

import re
import sys
import tempfile
import unicodedata
import unittest
import zipfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_language import CATALAN_UNDRAWN_ACCENTS, parse_language, strip_comment  # noqa: E402
from test_menudef import SKILL_FONT_DIR, glyph_path, png_width  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
MAPINFO = SRC / "lumps" / "MAPINFO"
LANGUAGE = SRC / "lumps" / "LANGUAGE"

END_TO_TITLE = "endtitle"
REQUIRED_SECTIONS = ("default", "ru", "ca")   # Catalan since P6 (D97)


@dataclass(frozen=True)
class Episode:
    """One campaign episode of MOD-SPEC 4.6: its maps in play order, the
    cluster that holds its last map and the ending that cluster prints."""
    order: tuple[str, ...]
    ending_cluster: int
    ending_text: str

    @property
    def start(self) -> str:
        return self.order[0]

    @property
    def last(self) -> str:
        return self.order[-1]


# D62: episode 1, in play order; the slots follow it. MAP03 ends it.
EPISODE_1 = Episode(("MAP01", "MAP02", "MAP03"), 1, "SD_END01_TEXT")
# D104 (P4): episode 2, "The Road to Moscow", on the next slots. Its ending
# is SD_END03_TEXT: the ids number the episodes in the order they were
# declared (the range took 02 in D41), not their place on the menu.
EPISODE_2 = Episode(("MAP04", "MAP05", "MAP06"), 7, "SD_END03_TEXT")
# D112 (P4): episode 3, "The Portal", on the next slots; the fourth episode
# declared, so SD_END04_TEXT. Cluster 7 being episode 2's ending, its
# chapters are 8 and 9 and its ending 10.
EPISODE_3 = Episode(("MAP07", "MAP08", "MAP09"), 10, "SD_END04_TEXT")
CAMPAIGN_EPISODES = (EPISODE_1, EPISODE_2, EPISODE_3)
ALL_CAMPAIGN_MAPS = tuple(m for ep in CAMPAIGN_EPISODES for m in ep.order)
# MOD-SPEC 4.6: map -> (cluster, next).
CAMPAIGN = {"MAP01": (3, "MAP02"), "MAP02": (4, "MAP03"), "MAP03": (1, END_TO_TITLE),
            "MAP04": (5, "MAP05"), "MAP05": (6, "MAP06"), "MAP06": (7, END_TO_TITLE),
            "MAP07": (8, "MAP08"), "MAP08": (9, "MAP09"), "MAP09": (10, END_TO_TITLE)}
RANGE_MAP = "RANGE"          # D62: the practice range's lump, out of the MAPxx slots
RANGE = {RANGE_MAP: (2, END_TO_TITLE)}
RANGE_START = RANGE_MAP
# MOD-SPEC 4.4: the episode blocks in file order are the New Game screen's.
EPISODE_STARTS = [EPISODE_1.start, EPISODE_2.start, EPISODE_3.start, RANGE_START]
MAX_LUMP_NAME = 8            # a map name is a WAD lump name
RE_MAP_SLOT = re.compile(r"^MAP(\d\d)$")

RANGE_CLUSTER = 2
FIRST_TRANSITION_CLUSTER = 3
# One chapter cluster per campaign map before its episode's last, numbered
# from 3 upward in play order across the episodes, each printing
# SD_MAPnn_EXIT_TEXT on the way into the next map (MOD-SPEC 4.6). An
# episode's ending cluster takes the next number after its chapters, so
# episode 3's chapters start at 8, after episode 2's ending, 7.
TRANSITIONS = {"MAP01": (3, "SD_MAP01_EXIT_TEXT"), "MAP02": (4, "SD_MAP02_EXIT_TEXT"),
               "MAP04": (5, "SD_MAP04_EXIT_TEXT"), "MAP05": (6, "SD_MAP05_EXIT_TEXT"),
               "MAP07": (8, "SD_MAP07_EXIT_TEXT"), "MAP08": (9, "SD_MAP08_EXIT_TEXT")}
TRANSITION_TEXTS = tuple(text for _cluster, text in TRANSITIONS.values())
ENDING_TEXTS = tuple(ep.ending_text for ep in CAMPAIGN_EPISODES)
RANGE_TEXT = "SD_END02_TEXT"
CLUSTER_TEXTS = {RANGE_CLUSTER: RANGE_TEXT,
                 **{ep.ending_cluster: ep.ending_text for ep in CAMPAIGN_EPISODES},
                 **{cluster: text for cluster, text in TRANSITIONS.values()}}
CLUSTER_FLAT = "SDFLR1"
CAMPAIGN_TEXTS = TRANSITION_TEXTS + ENDING_TEXTS


def expected_cluster_numbers() -> dict[str, int]:
    """MOD-SPEC 4.6's numbering, map -> cluster: from 3 upward in play order,
    each episode taking its chapter clusters and then, from episode 2 on, its
    ending cluster (episode 1's ending is cluster 1, D60). So episode 2 is
    5, 6, 7 and episode 3 (D112) 8, 9, 10."""
    numbers: dict[str, int] = {}
    following = FIRST_TRANSITION_CLUSTER
    for episode in CAMPAIGN_EPISODES:
        for name in episode.order[:-1]:
            numbers[name] = following
            following += 1
        if episode is EPISODE_1:
            numbers[episode.last] = episode.ending_cluster
        else:
            numbers[episode.last] = following
            following += 1
    return numbers


def episode_texts(episode: Episode) -> tuple[str, ...]:
    """What an episode prints, in order: its transitions, then its ending."""
    return tuple(TRANSITIONS[m][1] for m in episode.order[:-1]) + (episode.ending_text,)


# The text screen: Doom draws a finale text in SmallFont from x 10 on a
# 320 x 200 screen, one line per "\n". 300 px leaves the same 10 px on the
# right. FONT_HEIGHT is font.inf's; 18 lines of it fill the screen below
# the top margin. Pixel widths are the glyph PNGs' sum (no kerning in
# font.inf): an approximation, NOT VERIFIED to the pixel in the engine.
TEXT_X = 10
TEXT_MAX_WIDTH = 300
MAX_LINES = 18
FONT_INF = SKILL_FONT_DIR / "font.inf"

# Every ending closes on the same line, but the last of the first cycle.
TO_BE_CONTINUED = {"default": "TO BE CONTINUED", "ru": "ПРОДОЛЖЕНИЕ СЛЕДУЕТ",
                   "ca": "CONTINUARÀ"}
# D112: episode 3 closes the portal the first two left open, the end of the
# first cycle; it closes on THE END (and keeps one line open above it).
THE_END = {"default": "THE END", "ru": "КОНЕЦ", "ca": "FI"}
ENDING_LAST_LINE = {"SD_END01_TEXT": TO_BE_CONTINUED, "SD_END03_TEXT": TO_BE_CONTINUED,
                    "SD_END04_TEXT": THE_END}
# Episode 1's ending is the factory's since D62: the portal's power cut. It
# was the cosmodrome's until D60 and the bunker's until D62 (MOD-SPEC 4.6).
# Episode 2's (D104) is the Kremlin's, and leaves the invaders' main portal
# open, the hook for an episode 3.
ENDING_NAMES = {
    "SD_END01_TEXT": {"default": ("portal", "Tankograd"), "ru": ("портал", "Танкоград"),
                      "ca": ("portal", "Tankograd")},
    "SD_END03_TEXT": {"default": ("Kremlin", "portal", "still open"),
                      "ru": ("Кремл", "портал", "открыт"),
                      "ca": ("Kremlin", "portal", "obert")},
    # D112: the portal at Tunguska closes.
    "SD_END04_TEXT": {"default": ("portal", "Tunguska", "taiga"),
                      "ru": ("портал", "Тунгуск", "тайг"),
                      "ca": ("portal", "Tunguska", "taigà")},
}
ENDING_MUST_NOT_NAME = {
    "SD_END01_TEXT": {"default": ("Zarya", "gantry", "bunker", "station"),
                      "ru": ("Заря", "башни", "бункер", "Станция"),
                      "ca": ("Zarya", "búnquer", "estació")},
    "SD_END03_TEXT": {"default": ("Zarya", "dam"), "ru": ("Заря", "плотин"),
                      "ca": ("Zarya", "presa")},
    "SD_END04_TEXT": {"default": ("Kremlin", "dam", "TO BE CONTINUED"),
                      "ru": ("Кремл", "плотин", "ПРОДОЛЖЕНИЕ"),
                      "ca": ("Kremlin", "presa", "CONTINUARÀ")},
}
# What each transition must say it is: MAP01's goes down the lift into the
# metro; MAP02's comes out of the tunnel at the tractor works; MAP04's takes
# the armoured train to the Volga dam; MAP05's crosses the dam to Moscow;
# MAP07's radar goes dark and points to Severomorsk; MAP08's submarine base
# points to Tunguska.
TRANSITION_NAMES = {
    "SD_MAP01_EXIT_TEXT": {"default": ("lift",), "ru": ("лифт",), "ca": ("ascensor",)},
    "SD_MAP02_EXIT_TEXT": {"default": ("tunnel", "tractor", "Tankograd"),
                           "ru": ("тоннель", "трактор", "Танкоград"),
                           "ca": ("túnel", "tractor", "Tankograd")},
    "SD_MAP04_EXIT_TEXT": {"default": ("armoured train", "Volga", "dam"),
                           "ru": ("бронепоезд", "Волг", "плотин"),
                           "ca": ("tren blindat", "Volga", "presa")},
    "SD_MAP05_EXIT_TEXT": {"default": ("dam", "Moscow", "Red Square"),
                           "ru": ("плотин", "Москв", "Красная площадь"),
                           "ca": ("presa", "Moscou", "plaça Roja")},
    "SD_MAP07_EXIT_TEXT": {"default": ("radar", "Severomorsk"),
                           "ru": ("радар", "Североморск"),
                           "ca": ("radar", "Severomorsk")},
    "SD_MAP08_EXIT_TEXT": {"default": ("submarine", "Tunguska"),
                           "ru": ("подлодк", "Тунгуск"),
                           "ca": ("submarí", "Tunguska")},
}

RE_BLOCK = re.compile(r'^(map|episode|cluster)\s+(\w+)[^{]*\{(.*?)^\}', re.M | re.S | re.I)
LINE_BREAK = "\\n"   # LANGUAGE writes a line break as backslash-n


def mapinfo_code(text: str) -> str:
    return "\n".join(strip_comment(line) for line in text.splitlines())


def blocks(code: str, kind: str) -> dict[str, str]:
    return {name: body for k, name, body in RE_BLOCK.findall(code) if k.lower() == kind}


def prop(body: str, key: str) -> str | None:
    match = re.search(rf'^\s*{key}\s*=\s*(.+?)\s*$', body, re.M | re.I)
    return match.group(1).strip().strip('"') if match else None


def lookup_id(body: str, key: str) -> str | None:
    """`exittext = lookup, "SD_X"` -> "SD_X"; a literal text -> None."""
    match = re.search(rf'^\s*{key}\s*=\s*lookup\s*,\s*"([^"]+)"', body, re.M | re.I)
    return match.group(1) if match else None


def walk(maps: dict[str, str], clusters: dict[str, str], start: str) -> tuple[list[str], list[str]]:
    """Follow `next` from `start` the way GZDoom's G_WorldDone does and
    return (maps played, text ids printed). At an end sequence the current
    cluster's exittext is printed; between two maps, only when the cluster
    changes: the next cluster's entertext if it has one, else the current
    cluster's exittext. Raises on a loop or a missing map."""
    played: list[str] = []
    texts: list[str] = []
    current = start
    while True:
        if current in played:
            raise AssertionError(f"the flow loops back into {current}: {played}")
        if current not in maps:
            raise AssertionError(f"{played[-1] if played else start} leads to {current}, which has no map block")
        played.append(current)
        body = maps[current]
        here = clusters.get(prop(body, "cluster") or "", "")
        nxt = prop(body, "next")
        if nxt is None:
            raise AssertionError(f"{current} has no `next`")
        if nxt.lower() == END_TO_TITLE:
            if lookup_id(here, "exittext"):
                texts.append(lookup_id(here, "exittext"))
            return played, texts
        target = maps.get(nxt.upper())
        if target is not None and prop(target, "cluster") != prop(body, "cluster"):
            there = clusters.get(prop(target, "cluster") or "", "")
            text = lookup_id(there, "entertext") or lookup_id(here, "exittext")
            if text:
                texts.append(text)
        current = nxt.upper()


def text_lines(value: str) -> list[str]:
    return value.strip().strip('"').split(LINE_BREAK)


def drawn_as(ch: str) -> str:
    """The glyph SmallFont draws for `ch` (already a capital). A Catalan
    accented capital the fonts lack (test_language.CATALAN_UNDRAWN_ACCENTS)
    is drawn with its base letter by the engine (NOT VERIFIED on screen), so
    that letter's width is what a line measures."""
    if ch in CATALAN_UNDRAWN_ACCENTS and not glyph_path(SKILL_FONT_DIR, ch).is_file():
        return unicodedata.normalize("NFD", ch)[0]
    return ch


def width(line: str) -> int:
    """SmallFont draws lower case with the capital glyphs."""
    return sum(png_width(glyph_path(SKILL_FONT_DIR, drawn_as(ch))) for ch in line.upper())


class CampaignMapinfoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        code = mapinfo_code(MAPINFO.read_text(encoding="utf-8"))
        cls.maps = blocks(code, "map")
        cls.clusters = blocks(code, "cluster")
        cls.episodes = blocks(code, "episode")

    def test_each_maps_next(self):
        for name, (_cluster, nxt) in {**CAMPAIGN, **RANGE}.items():
            self.assertIn(name, self.maps, f"no map block for {name}")
            self.assertEqual(prop(self.maps[name], "next"), nxt, name)

    def test_each_maps_cluster(self):
        for name, (cluster, _next) in {**CAMPAIGN, **RANGE}.items():
            self.assertEqual(prop(self.maps[name], "cluster"), str(cluster), name)

    def test_every_map_block_is_known(self):
        """A map added to MAPINFO must find its place here (and in MOD-SPEC
        4.6) first: in an episode or outside the campaign."""
        self.assertEqual(set(self.maps), set(CAMPAIGN) | set(RANGE))
        self.assertEqual(set(CAMPAIGN), set(ALL_CAMPAIGN_MAPS))

    def test_the_slots_follow_the_campaign(self):
        """D62, D104: the MAPxx slots run MAP01, MAP02... in play order with
        no gap, episode after episode; each map leads to the next slot of its
        episode, and only an episode's last map ends the game."""
        numbers = [int(RE_MAP_SLOT.match(m).group(1)) for m in ALL_CAMPAIGN_MAPS]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))
        for episode in CAMPAIGN_EPISODES:
            for here, there in zip(episode.order, episode.order[1:]):
                self.assertEqual(prop(self.maps[here], "next"), there, f"{here} must lead to {there}")
            self.assertEqual(prop(self.maps[episode.last], "next"), END_TO_TITLE, episode.last)

    def test_each_campaign_map_is_led_to_once(self):
        """Every campaign map but an episode's first is some map's `next`,
        exactly once: no orphan, no fork. Nothing leads to an episode's
        start, so no episode runs into another."""
        leads = [(prop(b, "next") or "").upper() for b in self.maps.values()]
        for episode in CAMPAIGN_EPISODES:
            self.assertNotIn(episode.start, leads, f"something leads into {episode.start}")
            for name in episode.order[1:]:
                self.assertEqual(leads.count(name), 1, f"{name} is led to {leads.count(name)} times")

    def test_the_cluster_blocks(self):
        self.assertEqual(set(self.clusters), {str(c) for c in CLUSTER_TEXTS},
                         "a cluster was added or lost: update MOD-SPEC 4.6 first")
        for number, text in CLUSTER_TEXTS.items():
            body = self.clusters[str(number)]
            self.assertEqual(lookup_id(body, "exittext"), text, f"cluster {number}")
            self.assertEqual(prop(body, "flat"), CLUSTER_FLAT, f"cluster {number}")
            self.assertEqual(prop(body, "music"), "", f"cluster {number}")

    def test_each_earlier_map_has_its_own_transition_cluster(self):
        """MOD-SPEC 4.6: every campaign map before its episode's last owns a
        chapter cluster, numbered from 3 in play order across the episodes
        (each later episode's ending cluster taking the number after its
        chapters), whose text is SD_MAPnn_EXIT_TEXT."""
        earlier = tuple(m for ep in CAMPAIGN_EPISODES for m in ep.order[:-1])
        self.assertEqual(tuple(TRANSITIONS), earlier)
        expected = expected_cluster_numbers()
        for name, (cluster, text) in TRANSITIONS.items():
            self.assertEqual(cluster, expected[name], name)
            self.assertEqual(text, f"SD_{name}_EXIT_TEXT")
            self.assertEqual(prop(self.maps[name], "cluster"), str(cluster), name)
            holders = [n for n, b in self.maps.items() if prop(b, "cluster") == str(cluster)]
            self.assertEqual(holders, [name], f"cluster {cluster} is {name}'s alone")

    def test_no_cluster_has_an_entertext(self):
        """One crossing, one text: an entertext would replace or compete with
        the exittext of the cluster being left (MOD-SPEC 4.6)."""
        for number, body in self.clusters.items():
            self.assertIsNone(prop(body, "entertext"), f"cluster {number}")

    def test_each_ending_cluster_holds_only_its_episodes_last_map(self):
        for episode in CAMPAIGN_EPISODES:
            holders = [n for n, b in self.maps.items()
                       if prop(b, "cluster") == str(episode.ending_cluster)]
            self.assertEqual(holders, [episode.last])
            carriers = [n for n, b in self.clusters.items()
                        if episode.ending_text in (lookup_id(b, "exittext"), lookup_id(b, "entertext"))]
            self.assertEqual(carriers, [str(episode.ending_cluster)],
                             f"{episode.ending_text} is carried by more than one cluster")

    def test_the_cluster_numbers_follow_the_rule(self):
        """D104, D112: every campaign map's cluster is MOD-SPEC 4.6's number;
        each episode's ending cluster is the one its Episode names."""
        expected = expected_cluster_numbers()
        self.assertEqual(expected, {m: c for m, (c, _next) in CAMPAIGN.items()})
        for episode in CAMPAIGN_EPISODES:
            self.assertEqual(expected[episode.last], episode.ending_cluster, episode.last)

    def test_episode_two_still_ends_at_the_kremlin(self):
        """D112 leaves episode 2 as it was: MAP06 in cluster 7, the ending
        SD_END03_TEXT, then the title screen; nothing leads on to MAP07."""
        self.assertEqual(EPISODE_2, Episode(("MAP04", "MAP05", "MAP06"), 7, "SD_END03_TEXT"))
        self.assertEqual(prop(self.maps["MAP06"], "next"), END_TO_TITLE)

    def test_episode_one_still_ends_at_tankograd(self):
        """D104 and D112 leave episode 1 as it was: MAP03 in cluster 1, the ending
        SD_END01_TEXT, then the title screen."""
        self.assertEqual(EPISODE_1, Episode(("MAP01", "MAP02", "MAP03"), 1, "SD_END01_TEXT"))
        self.assertEqual(prop(self.maps["MAP03"], "next"), END_TO_TITLE)

    def test_consecutive_campaign_maps_are_in_different_clusters(self):
        """Same cluster = no text between them (ZDoom wiki, MAPINFO/Cluster)."""
        for name, (_cluster, nxt) in CAMPAIGN.items():
            if nxt == END_TO_TITLE:
                continue
            self.assertNotEqual(prop(self.maps[name], "cluster"), prop(self.maps[nxt], "cluster"),
                                f"{name} -> {nxt} would print no transition text")

    def test_each_episode_prints_its_transitions_then_its_ending_once(self):
        for episode in CAMPAIGN_EPISODES:
            with self.subTest(episode=episode.start):
                played, texts = walk(self.maps, self.clusters, episode.start)
                self.assertEqual(tuple(played), episode.order)
                self.assertEqual(tuple(texts), episode_texts(episode))
                self.assertEqual(texts.count(episode.ending_text), 1)
                self.assertEqual(texts[-1], episode.ending_text, "the ending must come last")
                others = set(CAMPAIGN_TEXTS) - set(episode_texts(episode))
                self.assertFalse(others & set(texts), "an episode prints another's text")

    def test_the_range_flow_is_its_own(self):
        played, texts = walk(self.maps, self.clusters, RANGE_START)
        self.assertEqual(played, [RANGE_START])
        self.assertEqual(texts, [RANGE_TEXT])

    def test_the_episodes_start_where_the_flows_start(self):
        """MOD-SPEC 4.4: Soviet Doom, The Road to Moscow, The Portal, the range."""
        self.assertEqual(list(self.episodes), EPISODE_STARTS)

    def test_the_range_is_outside_the_campaign(self):
        """D41, D62: no map leads to the range, no episode reaches it or its
        cluster, and it holds no MAPxx slot."""
        for name, body in self.maps.items():
            self.assertNotEqual((prop(body, "next") or "").upper(), RANGE_START, name)
        for episode in CAMPAIGN_EPISODES:
            played, texts = walk(self.maps, self.clusters, episode.start)
            self.assertNotIn(RANGE_START, played)
            self.assertNotIn(RANGE_TEXT, texts)
        self.assertNotIn(prop(self.maps[RANGE_START], "cluster"),
                         [prop(self.maps[m], "cluster") for m in CAMPAIGN])
        self.assertIsNone(RE_MAP_SLOT.match(RANGE_MAP))
        self.assertLessEqual(len(RANGE_MAP), MAX_LUMP_NAME)
        slots = sorted(n for n in self.maps if RE_MAP_SLOT.match(n))
        self.assertEqual(tuple(slots), ALL_CAMPAIGN_MAPS, "every MAPxx slot is a campaign map")

    def test_campaign_maps_keep_their_intermission(self):
        """The order the PM checks: stats screen, then the text, then the
        next map."""
        for name in CAMPAIGN:
            self.assertNotRegex(self.maps[name], r"(?im)^\s*nointermission\b", name)


class CampaignMapFoldersTest(unittest.TestCase):
    """D62 in the sources: one folder per map, named after its lump."""

    def test_every_map_has_its_source_folder(self):
        for name in (*CAMPAIGN, *RANGE):
            source = SRC / "maps" / name / "map.py"
            self.assertTrue(source.is_file(), f"no {source.relative_to(PROJECT_ROOT)}")
            self.assertRegex(source.read_text(encoding="utf-8"), rf'(?m)^MAP_NAME = "{name}"')

    def test_no_stray_map_folder(self):
        folders = {d.name for d in (SRC / "maps").iterdir()
                   if d.is_dir() and (d / "map.py").is_file()}
        self.assertEqual(folders, set(CAMPAIGN) | set(RANGE))


class CampaignTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def lines(self, code: str, ident: str) -> list[str]:
        self.assertIn(ident, self.sections[code], f"[{code}] lacks {ident}")
        return text_lines(self.sections[code][ident])

    def test_every_text_exists_in_every_language(self):
        for code in REQUIRED_SECTIONS:
            for ident in CAMPAIGN_TEXTS:
                self.assertTrue("".join(self.lines(code, ident)).strip(), f"[{code}] {ident} is empty")

    def test_russian_is_not_the_english(self):
        for ident in CAMPAIGN_TEXTS:
            ru = "".join(self.lines("ru", ident))
            self.assertNotEqual(ru, "".join(self.lines("default", ident)), ident)
            self.assertRegex(ru, r"[А-Яа-яЁё]", f"{ident} [ru] is not Cyrillic")

    def test_catalan_is_not_the_english(self):
        for ident in CAMPAIGN_TEXTS:
            ca = "".join(self.lines("ca", ident))
            self.assertNotEqual(ca, "".join(self.lines("default", ident)), ident)
            self.assertRegex(ca, r"[àèéíïòóúç]", f"{ident} [ca] has no Catalan letter")

    def test_the_texts_are_all_different(self):
        for code in REQUIRED_SECTIONS:
            texts = [tuple(self.lines(code, ident)) for ident in CAMPAIGN_TEXTS]
            self.assertEqual(len(set(texts)), len(texts), code)

    def test_each_transition_says_where_it_goes(self):
        self.assertEqual(set(TRANSITION_NAMES), set(TRANSITION_TEXTS))
        for ident, by_code in TRANSITION_NAMES.items():
            for code, words in by_code.items():
                text = " ".join(self.lines(code, ident)).lower()
                for word in words:
                    self.assertIn(word.lower(), text, f"[{code}] {ident} does not say {word!r}")

    def test_each_ending_is_its_episodes(self):
        self.assertEqual(set(ENDING_NAMES), set(ENDING_TEXTS))
        for ident in ENDING_TEXTS:
            for code in REQUIRED_SECTIONS:
                lines = self.lines(code, ident)
                self.assertEqual(lines[-1], ENDING_LAST_LINE[ident][code], f"[{code}] {ident}")
                text = " ".join(lines)
                for word in ENDING_NAMES[ident][code]:
                    self.assertIn(word.lower(), text.lower(), f"[{code}] {ident} does not name {word!r}")
                for word in ENDING_MUST_NOT_NAME[ident][code]:
                    self.assertNotIn(word, text, f"[{code}] {ident} still names {word!r}")

    def test_every_line_fits_the_text_screen(self):
        self.assertIn("FontHeight", FONT_INF.read_text(encoding="utf-8"))
        for code in REQUIRED_SECTIONS:
            for ident in CAMPAIGN_TEXTS:
                lines = self.lines(code, ident)
                self.assertLessEqual(len(lines), MAX_LINES, f"[{code}] {ident}: {len(lines)} lines")
                for line in lines:
                    self.assertLessEqual(width(line), TEXT_MAX_WIDTH,
                                         f"[{code}] {ident}: {line!r} is {width(line)} px from x {TEXT_X}")

    def test_every_glyph_is_drawn(self):
        for code in REQUIRED_SECTIONS:
            for ident in CAMPAIGN_TEXTS:
                for ch in set("".join(self.lines(code, ident)).upper()):
                    self.assertTrue(glyph_path(SKILL_FONT_DIR, drawn_as(ch)).is_file(),
                                    f"[{code}] {ident}: SmallFont has no {ch!r} (U+{ord(ch):04X})")


class CampaignPk3Test(unittest.TestCase):
    """The same flow in the package the engine loads."""

    def test_the_package_carries_the_campaign(self):
        sys.path.insert(0, str(TOOLS))
        from sdbuild.pk3 import build as build_pk3

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            build_pk3(SRC, out, TOOLS)
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
                code = mapinfo_code(zf.read("MAPINFO").decode("utf-8"))
                language = parse_language(zf.read("LANGUAGE").decode("utf-8"))
        for name in (*CAMPAIGN, *RANGE):
            self.assertIn(f"maps/{name}.wad", names)
        self.assertEqual({n for n in names if n.startswith("maps/")},
                         {f"maps/{n}.wad" for n in (*CAMPAIGN, *RANGE)})
        for episode in CAMPAIGN_EPISODES:
            played, texts = walk(blocks(code, "map"), blocks(code, "cluster"), episode.start)
            self.assertEqual((tuple(played), tuple(texts)), (episode.order, episode_texts(episode)))
        for section in REQUIRED_SECTIONS:
            for ident in CAMPAIGN_TEXTS:
                self.assertIn(ident, language[section])


if __name__ == "__main__":
    unittest.main()
