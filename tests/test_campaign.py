"""D60 and D62: the campaign is MAP01 -> MAP02 -> MAP03, in slot order.

D60 grew the campaign past MAP01; D62 (2026-10-14) gave the map slots the
campaign's order: MAP01 Zarya-7, MAP02 the metro-bunker (built as MAP03),
MAP03 the factory, Tankograd (built as MAP04), and the practice range left
the MAPxx sequence for the lump RANGE (it was MAP02).

The contract is docs/engine/MOD-SPEC.md 4.6. What this suite pins,
statically, from MAPINFO and LANGUAGE:

  * the campaign's order: MAP01, MAP02, MAP03 in that order, each map
    leading to the next slot, the last one to endtitle; RANGE -> endtitle;
  * the clusters (MOD-SPEC 4.6's rule): cluster 1 is the campaign's ending
    and holds only its last map, cluster 2 the range's, and one transition
    cluster per earlier map (3 = MAP01's, 4 = MAP02's); no `entertext`;
  * the flow as the engine walks it (a crossing between clusters prints the
    cluster's text): the campaign prints each transition, then the ending,
    each ONCE; the range prints its own text and nothing of the campaign's;
  * the range is isolated: no map leads to it, the campaign never reaches
    it, and it holds no MAPxx slot;
  * every text in English and Russian, broken by hand into lines that fit
    SmallFont on a 320-wide screen, with every glyph drawn.

What it cannot pin is what the engine shows: the PM's checks C1-C6 of
MOD-SPEC 4.6 (D26).
"""

from __future__ import annotations

import re
import sys
import tempfile
import unicodedata
import unittest
import zipfile
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

# D62: the campaign, in play order. The slots follow it.
CAMPAIGN_ORDER = ("MAP01", "MAP02", "MAP03")
# MOD-SPEC 4.6: map -> (cluster, next).
CAMPAIGN = {"MAP01": (3, "MAP02"), "MAP02": (4, "MAP03"), "MAP03": (1, END_TO_TITLE)}
RANGE_MAP = "RANGE"          # D62: the practice range's lump, out of the MAPxx slots
RANGE = {RANGE_MAP: (2, END_TO_TITLE)}
CAMPAIGN_START = "MAP01"
RANGE_START = RANGE_MAP
LAST_CAMPAIGN_MAP = "MAP03"
MAX_LUMP_NAME = 8            # a map name is a WAD lump name
RE_MAP_SLOT = re.compile(r"^MAP\d\d$")

ENDING_CLUSTER = 1
RANGE_CLUSTER = 2
# One chapter cluster per campaign map before the last, in order, each
# printing SD_MAPnn_EXIT_TEXT on the way into the next map (MOD-SPEC 4.6).
TRANSITIONS = {"MAP01": (3, "SD_MAP01_EXIT_TEXT"), "MAP02": (4, "SD_MAP02_EXIT_TEXT")}
TRANSITION_TEXTS = tuple(text for _cluster, text in TRANSITIONS.values())
ENDING_TEXT = "SD_END01_TEXT"
RANGE_TEXT = "SD_END02_TEXT"
CLUSTER_TEXTS = {ENDING_CLUSTER: ENDING_TEXT, RANGE_CLUSTER: RANGE_TEXT,
                 **{cluster: text for cluster, text in TRANSITIONS.values()}}
CLUSTER_FLAT = "SDFLR1"
CAMPAIGN_TEXTS = TRANSITION_TEXTS + (ENDING_TEXT,)

# The text screen: Doom draws a finale text in SmallFont from x 10 on a
# 320 x 200 screen, one line per "\n". 300 px leaves the same 10 px on the
# right. FONT_HEIGHT is font.inf's; 18 lines of it fill the screen below
# the top margin. Pixel widths are the glyph PNGs' sum (no kerning in
# font.inf): an approximation, NOT VERIFIED to the pixel in the engine.
TEXT_X = 10
TEXT_MAX_WIDTH = 300
MAX_LINES = 18
FONT_INF = SKILL_FONT_DIR / "font.inf"

# The ending is the factory's since D62: the portal's power cut. It was the
# cosmodrome's until D60 and the bunker's until D62 (MOD-SPEC 4.6).
ENDING_LAST_LINE = {"default": "TO BE CONTINUED", "ru": "ПРОДОЛЖЕНИЕ СЛЕДУЕТ",
                    "ca": "CONTINUARÀ"}
ENDING_NAMES = {"default": ("portal", "Tankograd"), "ru": ("портал", "Танкоград"),
                "ca": ("portal", "Tankograd")}
ENDING_MUST_NOT_NAME = {"default": ("Zarya", "gantry", "bunker", "station"),
                        "ru": ("Заря", "башни", "бункер", "Станция"),
                        "ca": ("Zarya", "búnquer", "estació")}
# What each transition must say it is: MAP01's goes down the lift into the
# metro; MAP02's comes out of the tunnel at the tractor works.
TRANSITION_NAMES = {
    "SD_MAP01_EXIT_TEXT": {"default": ("lift",), "ru": ("лифт",), "ca": ("ascensor",)},
    "SD_MAP02_EXIT_TEXT": {"default": ("tunnel", "tractor", "Tankograd"),
                           "ru": ("тоннель", "трактор", "Танкоград"),
                           "ca": ("túnel", "tractor", "Tankograd")},
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
        4.6) first: in the campaign or outside it."""
        self.assertEqual(set(self.maps), set(CAMPAIGN) | set(RANGE))

    def test_the_slots_follow_the_campaign(self):
        """D62: MAP01, MAP02, MAP03 in play order; each campaign map leads to
        the next slot, and only the last one ends the game."""
        self.assertEqual(tuple(sorted(CAMPAIGN)), CAMPAIGN_ORDER)
        for here, there in zip(CAMPAIGN_ORDER, CAMPAIGN_ORDER[1:]):
            self.assertEqual(prop(self.maps[here], "next"), there, f"{here} must lead to {there}")
        self.assertEqual(prop(self.maps[CAMPAIGN_ORDER[-1]], "next"), END_TO_TITLE)
        self.assertEqual(CAMPAIGN_ORDER[-1], LAST_CAMPAIGN_MAP)

    def test_each_campaign_map_is_led_to_once(self):
        """Every campaign map but the first is some map's `next`, exactly
        once: no orphan, no fork."""
        leads = [(prop(b, "next") or "").upper() for b in self.maps.values()]
        self.assertNotIn(CAMPAIGN_START, leads, "something leads back to the start")
        for name in CAMPAIGN_ORDER[1:]:
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
        """MOD-SPEC 4.6: every campaign map before the last owns a chapter
        cluster, numbered from 3 in play order, whose text is
        SD_MAPnn_EXIT_TEXT."""
        self.assertEqual(tuple(TRANSITIONS), CAMPAIGN_ORDER[:-1])
        for index, (name, (cluster, text)) in enumerate(TRANSITIONS.items()):
            self.assertEqual(cluster, 3 + index, name)
            self.assertEqual(text, f"SD_{name}_EXIT_TEXT")
            self.assertEqual(prop(self.maps[name], "cluster"), str(cluster), name)
            holders = [n for n, b in self.maps.items() if prop(b, "cluster") == str(cluster)]
            self.assertEqual(holders, [name], f"cluster {cluster} is {name}'s alone")

    def test_no_cluster_has_an_entertext(self):
        """One crossing, one text: an entertext would replace or compete with
        the exittext of the cluster being left (MOD-SPEC 4.6)."""
        for number, body in self.clusters.items():
            self.assertIsNone(prop(body, "entertext"), f"cluster {number}")

    def test_the_ending_cluster_holds_only_the_last_campaign_map(self):
        holders = [n for n, b in self.maps.items() if prop(b, "cluster") == str(ENDING_CLUSTER)]
        self.assertEqual(holders, [LAST_CAMPAIGN_MAP])
        carriers = [n for n, b in self.clusters.items()
                    if ENDING_TEXT in (lookup_id(b, "exittext"), lookup_id(b, "entertext"))]
        self.assertEqual(carriers, [str(ENDING_CLUSTER)], "the ending is carried by more than one cluster")

    def test_consecutive_campaign_maps_are_in_different_clusters(self):
        """Same cluster = no text between them (ZDoom wiki, MAPINFO/Cluster)."""
        for name, (_cluster, nxt) in CAMPAIGN.items():
            if nxt == END_TO_TITLE:
                continue
            self.assertNotEqual(prop(self.maps[name], "cluster"), prop(self.maps[nxt], "cluster"),
                                f"{name} -> {nxt} would print no transition text")

    def test_the_campaign_flow_prints_each_transition_then_the_ending_once(self):
        played, texts = walk(self.maps, self.clusters, CAMPAIGN_START)
        self.assertEqual(tuple(played), CAMPAIGN_ORDER)
        self.assertEqual(texts, list(CAMPAIGN_TEXTS))
        self.assertEqual(texts.count(ENDING_TEXT), 1)
        self.assertEqual(texts[-1], ENDING_TEXT, "the ending must come last")

    def test_the_range_flow_is_its_own(self):
        played, texts = walk(self.maps, self.clusters, RANGE_START)
        self.assertEqual(played, [RANGE_START])
        self.assertEqual(texts, [RANGE_TEXT])

    def test_the_episodes_start_where_the_flows_start(self):
        self.assertEqual(list(self.episodes), [CAMPAIGN_START, RANGE_START])

    def test_the_range_is_outside_the_campaign(self):
        """D41, D62: no map leads to the range, the campaign never reaches
        it or its cluster, and it holds no MAPxx slot."""
        for name, body in self.maps.items():
            self.assertNotEqual((prop(body, "next") or "").upper(), RANGE_START, name)
        played, texts = walk(self.maps, self.clusters, CAMPAIGN_START)
        self.assertNotIn(RANGE_START, played)
        self.assertNotIn(RANGE_TEXT, texts)
        self.assertNotIn(prop(self.maps[RANGE_START], "cluster"),
                         [prop(self.maps[m], "cluster") for m in CAMPAIGN])
        self.assertNotRegex(RANGE_MAP, RE_MAP_SLOT)
        self.assertLessEqual(len(RANGE_MAP), MAX_LUMP_NAME)
        slots = sorted(n for n in self.maps if RE_MAP_SLOT.match(n))
        self.assertEqual(tuple(slots), CAMPAIGN_ORDER, "every MAPxx slot is a campaign map")

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

    def test_every_text_exists_in_both_languages(self):
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
        for ident, by_code in TRANSITION_NAMES.items():
            for code, words in by_code.items():
                text = " ".join(self.lines(code, ident)).lower()
                for word in words:
                    self.assertIn(word.lower(), text, f"[{code}] {ident} does not say {word!r}")

    def test_the_ending_is_the_factorys(self):
        for code in REQUIRED_SECTIONS:
            lines = self.lines(code, ENDING_TEXT)
            self.assertEqual(lines[-1], ENDING_LAST_LINE[code], code)
            text = " ".join(lines)
            for word in ENDING_NAMES[code]:
                self.assertIn(word.lower(), text.lower(), f"[{code}] the ending does not name {word!r}")
            for word in ENDING_MUST_NOT_NAME[code]:
                self.assertNotIn(word, text, f"[{code}] the ending still names {word!r}")

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
        played, texts = walk(blocks(code, "map"), blocks(code, "cluster"), CAMPAIGN_START)
        self.assertEqual((tuple(played), tuple(texts)), (CAMPAIGN_ORDER, CAMPAIGN_TEXTS))
        for section in REQUIRED_SECTIONS:
            for ident in CAMPAIGN_TEXTS:
                self.assertIn(ident, language[section])


if __name__ == "__main__":
    unittest.main()
