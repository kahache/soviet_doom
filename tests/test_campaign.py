"""D60: the campaign grows. MAP01 leads into MAP03, the metro-bunker, and
MAP03 ends the episode until MAP04 is wired.

The contract is docs/engine/MOD-SPEC.md 4.6. What this suite pins,
statically, from MAPINFO and LANGUAGE:

  * every map's `next`: MAP01 -> "MAP03", MAP03 -> endtitle, MAP02 ->
    endtitle;
  * the clusters: cluster 1 is the campaign's ending and holds only MAP03,
    cluster 2 the range's, cluster 3 MAP01's transition; no `entertext`;
  * the flow as the engine walks it (a crossing between clusters prints the
    cluster's text): the campaign prints the transition, then the ending,
    each ONCE; the range prints its own text and nothing of the campaign's;
  * MAP02 is isolated: no map leads to it and the campaign never reaches it;
  * both texts in English and Russian, broken by hand into lines that fit
    SmallFont on a 320-wide screen, with every glyph drawn.

What it cannot pin is what the engine shows: the PM's checks C1-C6 of
MOD-SPEC 4.6 (D26).
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_language import parse_language, strip_comment  # noqa: E402
from test_menudef import SKILL_FONT_DIR, glyph_path, png_width  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
MAPINFO = SRC / "lumps" / "MAPINFO"
LANGUAGE = SRC / "lumps" / "LANGUAGE"

END_TO_TITLE = "endtitle"
REQUIRED_SECTIONS = ("default", "ru")

# MOD-SPEC 4.6: map -> (cluster, next).
CAMPAIGN = {"MAP01": (3, "MAP03"), "MAP03": (1, END_TO_TITLE)}
RANGE = {"MAP02": (2, END_TO_TITLE)}
CAMPAIGN_START = "MAP01"
RANGE_START = "MAP02"
LAST_CAMPAIGN_MAP = "MAP03"

ENDING_CLUSTER = 1
RANGE_CLUSTER = 2
TRANSITION_CLUSTER = 3
TRANSITION_TEXT = "SD_MAP01_EXIT_TEXT"
ENDING_TEXT = "SD_END01_TEXT"
RANGE_TEXT = "SD_END02_TEXT"
CLUSTER_TEXTS = {ENDING_CLUSTER: ENDING_TEXT, RANGE_CLUSTER: RANGE_TEXT,
                 TRANSITION_CLUSTER: TRANSITION_TEXT}
CLUSTER_FLAT = "SDFLR1"

# The text screen: Doom draws a finale text in SmallFont from x 10 on a
# 320 x 200 screen, one line per "\n". 300 px leaves the same 10 px on the
# right. FONT_HEIGHT is font.inf's; 18 lines of it fill the screen below
# the top margin. Pixel widths are the glyph PNGs' sum (no kerning in
# font.inf): an approximation, NOT VERIFIED to the pixel in the engine.
TEXT_X = 10
TEXT_MAX_WIDTH = 300
MAX_LINES = 18
FONT_INF = SKILL_FONT_DIR / "font.inf"

# The ending is the bunker's now, not the cosmodrome's (MOD-SPEC 4.6).
ENDING_LAST_LINE = {"default": "TO BE CONTINUED", "ru": "ПРОДОЛЖЕНИЕ СЛЕДУЕТ"}
ENDING_MUST_NOT_NAME = {"default": ("Zarya", "gantry"), "ru": ("Заря", "башни")}
TRANSITION_NAMES_THE_LIFT = {"default": "lift", "ru": "лифт"}

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


def width(line: str) -> int:
    """SmallFont draws lower case with the capital glyphs."""
    return sum(png_width(glyph_path(SKILL_FONT_DIR, ch)) for ch in line.upper())


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

    def test_the_cluster_blocks(self):
        self.assertEqual(set(self.clusters), {str(c) for c in CLUSTER_TEXTS},
                         "a cluster was added or lost: update MOD-SPEC 4.6 first")
        for number, text in CLUSTER_TEXTS.items():
            body = self.clusters[str(number)]
            self.assertEqual(lookup_id(body, "exittext"), text, f"cluster {number}")
            self.assertEqual(prop(body, "flat"), CLUSTER_FLAT, f"cluster {number}")
            self.assertEqual(prop(body, "music"), "", f"cluster {number}")

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

    def test_the_campaign_flow_prints_the_transition_then_the_ending_once(self):
        played, texts = walk(self.maps, self.clusters, CAMPAIGN_START)
        self.assertEqual(played, ["MAP01", "MAP03"])
        self.assertEqual(texts, [TRANSITION_TEXT, ENDING_TEXT])
        self.assertEqual(texts.count(ENDING_TEXT), 1)

    def test_the_range_flow_is_its_own(self):
        played, texts = walk(self.maps, self.clusters, RANGE_START)
        self.assertEqual(played, [RANGE_START])
        self.assertEqual(texts, [RANGE_TEXT])

    def test_the_episodes_start_where_the_flows_start(self):
        self.assertEqual(list(self.episodes), [CAMPAIGN_START, RANGE_START])

    def test_map02_is_isolated(self):
        """D41: no map leads to the range, and the campaign never reaches it."""
        for name, body in self.maps.items():
            self.assertNotEqual((prop(body, "next") or "").upper(), RANGE_START, name)
        played, texts = walk(self.maps, self.clusters, CAMPAIGN_START)
        self.assertNotIn(RANGE_START, played)
        self.assertNotIn(RANGE_TEXT, texts)
        self.assertNotIn(prop(self.maps[RANGE_START], "cluster"),
                         [prop(self.maps[m], "cluster") for m in CAMPAIGN])

    def test_map01_keeps_its_intermission(self):
        """The order the PM checks: stats screen, then the text, then MAP03."""
        for name in CAMPAIGN:
            self.assertNotRegex(self.maps[name], r"(?im)^\s*nointermission\b", name)


class CampaignTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def lines(self, code: str, ident: str) -> list[str]:
        self.assertIn(ident, self.sections[code], f"[{code}] lacks {ident}")
        return text_lines(self.sections[code][ident])

    def test_both_texts_exist_in_both_languages(self):
        for code in REQUIRED_SECTIONS:
            for ident in (TRANSITION_TEXT, ENDING_TEXT):
                self.assertTrue("".join(self.lines(code, ident)).strip(), f"[{code}] {ident} is empty")

    def test_russian_is_not_the_english(self):
        for ident in (TRANSITION_TEXT, ENDING_TEXT):
            ru = "".join(self.lines("ru", ident))
            self.assertNotEqual(ru, "".join(self.lines("default", ident)), ident)
            self.assertRegex(ru, r"[А-Яа-яЁё]", f"{ident} [ru] is not Cyrillic")

    def test_the_transition_is_not_the_ending(self):
        for code in REQUIRED_SECTIONS:
            self.assertNotEqual(self.lines(code, TRANSITION_TEXT), self.lines(code, ENDING_TEXT), code)

    def test_the_transition_takes_the_lift(self):
        for code, word in TRANSITION_NAMES_THE_LIFT.items():
            self.assertIn(word, " ".join(self.lines(code, TRANSITION_TEXT)).lower(), code)

    def test_the_ending_is_the_bunkers(self):
        for code in REQUIRED_SECTIONS:
            lines = self.lines(code, ENDING_TEXT)
            self.assertEqual(lines[-1], ENDING_LAST_LINE[code], code)
            for word in ENDING_MUST_NOT_NAME[code]:
                self.assertNotIn(word, " ".join(lines), f"[{code}] the ending still names {word!r}")

    def test_every_line_fits_the_text_screen(self):
        self.assertIn("FontHeight", FONT_INF.read_text(encoding="utf-8"))
        for code in REQUIRED_SECTIONS:
            for ident in (TRANSITION_TEXT, ENDING_TEXT):
                lines = self.lines(code, ident)
                self.assertLessEqual(len(lines), MAX_LINES, f"[{code}] {ident}: {len(lines)} lines")
                for line in lines:
                    self.assertLessEqual(width(line), TEXT_MAX_WIDTH,
                                         f"[{code}] {ident}: {line!r} is {width(line)} px from x {TEXT_X}")

    def test_every_glyph_is_drawn(self):
        for code in REQUIRED_SECTIONS:
            for ident in (TRANSITION_TEXT, ENDING_TEXT):
                for ch in set("".join(self.lines(code, ident)).upper()):
                    self.assertTrue(glyph_path(SKILL_FONT_DIR, ch).is_file(),
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
        for name in CAMPAIGN:
            self.assertIn(f"maps/{name}.wad", names)
        played, texts = walk(blocks(code, "map"), blocks(code, "cluster"), CAMPAIGN_START)
        self.assertEqual((played, texts), (["MAP01", "MAP03"], [TRANSITION_TEXT, ENDING_TEXT]))
        for section in REQUIRED_SECTIONS:
            self.assertIn(TRANSITION_TEXT, language[section])


if __name__ == "__main__":
    unittest.main()
