"""The propaganda radio (V3 B5, D124): SD_Loudspeaker, its sounds and where it stands.

Contract: docs/engine/MOD-SPEC.md 6.14; design and room table:
docs/sound/2026-10-23_V3_propaganda-radio.md 5. What is pinned here, without
ever starting GZDoom (D26):

  * zscript.txt includes loudspeaker.zs once; the file declares
    SD_Loudspeaker as an Actor, replaces nothing, and its editor number 21201
    is in the decoration sub-range, in MAPINFO and in MOD-SPEC 6.1;
  * the behaviour the design promises is in the code (a positional sound
    over the music, never a music change; the shuffle bag; the hysteresis;
    the line in progress finishes; the jingle's cooldown; the bed; the
    transient re-sync after a load) and MOD-SPEC 6.14 prints the code's
    numbers;
  * every sound the class can ask for is in SNDINFO, maps to a lump installed
    in assets/sounds/radio/ (pinned by SHA-256; equal to its candidate when
    the main checkout's work/ is here), carries a $rolloff, is packed, and
    has a row in docs/art/LICENSES.md;
  * the placements: one or two a map in the whole campaign (Episode 1 since
    2026-10-24), in the rooms the design names, the playlists' story filter
    (RAD11 Episode 1's only, RAD15 from Tankograd on, RAD02 from MAP06 on), no
    two zones overlapping, nor MAP01's SD_Radio.

What it cannot pin is what the engine does with any of it (MOD-SPEC 6.14,
"NOT VERIFIED"): the PM's engine pass.

Run:  python3 -m unittest tests.test_loudspeaker -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
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

import route  # noqa: E402  (MapData: the maps as their sources build them)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_bestiary import mapinfo_ednums, strip_zs_comments, zs_constants  # noqa: E402

ZS = SRC / "zscript" / "sd" / "loudspeaker.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
SNDINFO = SRC / "lumps" / "SNDINFO"
INCLUDE = "zscript/sd/loudspeaker.zs"
ASSETS = PROJECT_ROOT / "assets" / "sounds" / "radio"
CANDIDATES = PROJECT_ROOT / "work" / "audio" / "candidates" / "radio"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
INSTALLER = TOOLS / "audio" / "install_radio.py"

CLASS = "SD_Loudspeaker"
EDNUM = 21201
RADIO_EDNUM = 21200                 # SD_Radio, the music swap (MOD-SPEC 6.7)
RADIO_HYSTERESIS = 64
RADIO_DEFAULT_REACH = 128
DECORATION_RANGE = range(21200, 21300)
LINES = range(1, 17)
LINE_LUMPS = {f"sd/radio/line/{n:02d}": f"SDRAD{n:02d}" for n in LINES}
JINGLE_LUMPS = {f"sd/radio/jingle/{k}": f"SDRADJ{k}" for k in (1, 2, 3)}
BED = ("sd/radio/bed", "SDRADBED")
ROLLOFF = ("128", "768")

# What install_radio.py wrote (2026-10-24): the takes byte for byte, the bed
# rendered (deterministic: seed 21201, the same OGG on a rerun).
INSTALLED_SHA256 = {
    "SDRAD01": "0e17e0a29a3f0ae02225d89cc3241e638441c299e525bf7a65498f28ec881bbd",
    "SDRAD02": "d1328c6db4f599d2a6d75dc1eadd3e9c510ca0fa4edab1cea001774dfc140c98",
    "SDRAD03": "9bfba7daac42f5b4e92f29d995a0cf1f77b96341b866a1c60a790d1f9aadcff0",
    "SDRAD04": "3bcff3bd8be7160659ca4a75b5467ca15bc59d4806fd01a94f5614e37c8a13d4",
    "SDRAD05": "f497879984c685e50718ef1480da0fe3132cc0f222bcf563b8ee1455bc7c4289",
    "SDRAD06": "9dab563fece4f8850dd9dbd32be65020838e056219365bb21f138c5d02729e5a",
    "SDRAD07": "dca1861df449b39476c8287c07b65afba490c6736a752fa68101b399036d350a",
    "SDRAD08": "6820dfb573952e29af2b3ace3aa7c3571f60283d27de09ccd5823e1a597d373d",
    "SDRAD09": "4030c9295c6173113887a44dd405af615a872d9ec06e832317f96064da809036",
    "SDRAD10": "fe183cfb4097fc6587f1d14f6fcbcfa664f8c039c30317309e90b8b1f4ddc53b",
    "SDRAD11": "2b8a1d86907f4149370e45d137a3b164bb973fe8b299be72fc9a6d8b76a3aebe",
    "SDRAD12": "97516080de8414838a30040e57d4d812fceec5a162c2b7d9a2e199c9902b9c23",
    "SDRAD13": "2a35e5dd2e98c74179188c792689def6a3d51a39bb98a9f6f2902781543ffd8e",
    "SDRAD14": "11d9abfef875da7c2a22838a357f423056c868ccadd93bc62dd5f13ab34fa795",
    "SDRAD15": "543c6fdfffbff39aee68fd7add0abf82307b436a7483c9457114d92342507920",
    "SDRAD16": "afddafcfa05cc9a1792bfbe98cdc33023882e1b8162aa713e096e2cba40e0a24",
    "SDRADBED": "689509ccbc28da0c411f803a0c8fabeed63f0c751ba19145dcf5a26333558d1e",
    "SDRADJ1": "b1bf154abf6d6f0a2c365fbab1613ba04a6953fef3142f70b98344bb4f58f735",
    "SDRADJ2": "4150dfee316cfa8f55e6cd392b329627252510d60b25a1665104954ab97c619e",
    "SDRADJ3": "ca61d52540e55aee03cea39c84b74de35dda0421a4903e1a79964d636b225c6a",
}

# The design's room table (docs/sound/2026-10-23_V3_propaganda-radio.md 5.4),
# as built: map -> the zones its loudspeakers stand in. Episode 1 since
# 2026-10-24 (the PM's V3 schedule; each map's design document, "V3").
ROOMS = {
    "MAP01": {"z4_komnata", "z6_hangar"},
    "MAP02": {"z3_hall"},
    "MAP03": {"z3_hall"},
    "MAP04": {"z6_platform"},
    "MAP05": {"z5_hall"},
    "MAP06": {"z6_square", "z5_atrium"},
    "MAP07": {"z4_barracks"},
    "MAP08": {"z6_mess"},
    "MAP09": {"z3_yard"},
}
EPISODE_1 = ("MAP01", "MAP02", "MAP03")
LINE_ZARYA = 11            # "Zarya-7 holds": Episode 1's only
LINE_DAM = 2               # the Volga dam's victory: from MAP06 on
DAM_FROM = "MAP06"
LINE_TANKOGRAD = 15        # Tankograd's plan: once the player has reached it (MAP03 on)
TANKOGRAD_FROM = "MAP03"
ZARYA_ROOM = ("MAP01", "z4_komnata")   # the garrison report, in the base it is about
RED_SQUARE_PARADE = 9      # «the parade is not cancelled» on Red Square itself


def code() -> str:
    return strip_zs_comments(ZS.read_text(encoding="utf-8"))


def sndinfo() -> tuple[dict[str, str], dict[str, list[str]], dict[str, tuple[str, ...]]]:
    """(name -> lump, $random alias -> members, $rolloff name -> its numbers), sd/radio only."""
    names, randoms, rolloffs = {}, {}, {}
    for raw in SNDINFO.read_text(encoding="ascii").splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        m = re.match(r"\$random\s+(\S+)\s*\{([^}]*)\}", line)
        if m and m.group(1).startswith("sd/radio"):
            randoms[m.group(1)] = m.group(2).split()
            continue
        m = re.match(r"\$rolloff\s+(\S+)\s+(.*)$", line)
        if m and m.group(1).startswith("sd/radio"):
            rolloffs[m.group(1)] = tuple(m.group(2).split())
            continue
        parts = line.split()
        if len(parts) == 2 and parts[0].startswith("sd/radio"):
            names[parts[0]] = parts[1]
    return names, randoms, rolloffs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("sd_install_radio", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = code()
        cls.consts = zs_constants(ZS.read_text(encoding="utf-8"))

    def test_zscript_txt_includes_it_once(self):
        lines = [ln.split("//")[0].strip() for ln in ZSCRIPT_TXT.read_text(encoding="ascii").splitlines()]
        self.assertEqual(1, lines.count(f'#include "{INCLUDE}"'))

    def test_one_actor_class_balanced_and_replacing_nothing(self):
        self.assertRegex(self.code, rf"\bclass\s+{CLASS}\s*:\s*Actor\b")
        self.assertEqual(1, len(re.findall(r"\bclass\s+\w+", self.code)))
        self.assertEqual(self.code.count("{"), self.code.count("}"))
        self.assertEqual(self.code.count("("), self.code.count(")"))
        self.assertNotRegex(self.code, r"\breplaces\b")

    def test_the_editor_number(self):
        self.assertIn(EDNUM, DECORATION_RANGE)
        self.assertEqual(CLASS, mapinfo_ednums().get(EDNUM))
        self.assertIn(f"| {EDNUM} | `{CLASS}`", MOD_SPEC.read_text(encoding="utf-8"))

    def test_a_sound_over_the_music_never_a_music_change(self):
        for forbidden in ("S_ChangeMusic", "S_StopMusic", "SetMusicVolume", "snd_musicvolume", "ATTN_NONE"):
            self.assertNotIn(forbidden, self.code, forbidden)
        self.assertIn("A_StartSound(LineSound(NextLine()), CHAN_VOICE", self.code)

    def test_the_listener_is_the_local_player_measured_in_3d(self):
        self.assertIn("players[consoleplayer].mo", self.code)
        self.assertIn("Distance3D(listener)", self.code)

    def test_on_within_reach_off_beyond_the_hysteresis(self):
        self.assertIn("distance <= reach", self.code)
        self.assertIn("distance > reach + SD_LS_HYSTERESIS", self.code)

    def test_the_line_in_progress_finishes(self):
        """Turning off never stops CHAN_VOICE; the bed stops only once the voice is silent."""
        self.assertNotIn("A_StopSound(CHAN_VOICE)", self.code)
        self.assertRegex(self.code, r"else if \(!speaking && bedOn\)\s*\{\s*(?:\s*)A_StopSound\(CHAN_BODY\)")

    def test_a_shuffle_bag_never_the_same_line_twice_in_a_row(self):
        body = re.search(r"void RefillBag\(\)\s*\{(.*?)^\t\}", self.code, re.S | re.M).group(1)
        self.assertIn("random(0, i)", body, "Fisher-Yates")
        self.assertIn("== lastLine", body)
        self.assertIn("bag.Pop()", self.code)

    def test_the_jingle_waits_for_its_cooldown(self):
        self.assertIn("Level.maptime - offSince >= SD_LS_JINGLE_COOLDOWN * TICRATE", self.code)

    def test_saved_games(self):
        for field in ("turnedOn", "everOn", "speaking", "bedOn"):
            self.assertRegex(self.code, rf"(?m)^\s*bool\s+{field}\s*;", field)
        self.assertRegex(self.code, r"(?m)^\s*Array<int>\s+bag\s*;")
        self.assertRegex(self.code, r"(?m)^\s*transient\s+bool\s+synced\s*;")

    def test_provisional_body(self):
        """No horn drawn yet (MOD-SPEC 6.12): invisible and intangible, marked."""
        raw = ZS.read_text(encoding="utf-8")
        self.assertIn("TNT1 A -1", self.code)
        self.assertIn("+NOINTERACTION", self.code)
        self.assertGreaterEqual(raw.count("PROVISIONAL-D116"), 2)

    def test_mod_spec_prints_the_codes_numbers(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        section = re.search(r"^## 6\.14 .*?$(.*?)(?=^## )", spec, re.S | re.M).group(1)
        c = {k: (int(v) if float(v).is_integer() else v) for k, v in self.consts.items()}
        for text in (f"**{EDNUM}**",
                     f"`0` = **{c['SD_LS_DEFAULT_REACH']}** (`SD_LS_DEFAULT_REACH`)",
                     f"`0` = **{c['SD_LS_DEFAULT_PAUSE']}** (`SD_LS_DEFAULT_PAUSE`), plus a random 0-**{c['SD_LS_PAUSE_JITTER']}**",
                     f"**{c['SD_LS_FLAG_NO_JINGLE']}** = no jingle", f"**{c['SD_LS_FLAG_BED']}** = the valve bed",
                     f"every **{c['SD_LS_POLL_TICS']}** tics", f"**{c['SD_LS_JINGLE_GAP']}** s after the jingle",
                     f"reach + {c['SD_LS_HYSTERESIS']}** (`SD_LS_HYSTERESIS`)",
                     f"after **{c['SD_LS_JINGLE_COOLDOWN']}** s away",
                     f"`SD_LS_VOLUME` **{c['SD_LS_VOLUME']}**", f"`SD_LS_BED_VOLUME` **{c['SD_LS_BED_VOLUME']}**",
                     f"full within {ROLLOFF[0]}, silent at {ROLLOFF[1]}"):
            self.assertIn(text, section)
        self.assertEqual(len(LINES), c["SD_LS_LINES"])
        self.assertEqual(3, c["SD_LS_JINGLES"])


class SoundsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names, cls.randoms, cls.rolloffs = sndinfo()

    def test_every_line_jingle_and_the_bed_are_named(self):
        expected = dict(LINE_LUMPS) | dict(JINGLE_LUMPS) | {BED[0]: BED[1]}
        self.assertEqual(expected, self.names)
        self.assertEqual({"sd/radio/jingle": sorted(JINGLE_LUMPS)},
                         {k: sorted(v) for k, v in self.randoms.items()})

    def test_the_code_asks_only_for_names_sndinfo_has(self):
        c = code()
        self.assertIn('"sd/radio/line/%02d"', c)
        self.assertIn('"sd/radio/jingle/%d"', c)
        for literal in re.findall(r'"(sd/radio/[a-z/]+)"', c):
            self.assertTrue(literal in self.names or literal in self.randoms, literal)

    def test_every_name_rolls_off_inside_a_room(self):
        for name in list(self.names) + list(self.randoms):
            self.assertIn(name, self.rolloffs, name)
            self.assertEqual(ROLLOFF, self.rolloffs[name][-2:], name)

    def test_installed_as_pinned(self):
        self.assertEqual(sorted(INSTALLED_SHA256), sorted(p.stem for p in ASSETS.glob("*.ogg")))
        for lump, digest in INSTALLED_SHA256.items():
            self.assertEqual(digest, sha256(ASSETS / f"{lump}.ogg"), lump)

    def test_one_take_per_line_the_measurements_best(self):
        """install_radio.py's take is METRICS.json's rank 1, never a flagged runaway."""
        inst = load_installer()
        self.assertEqual(set(LINES), set(inst.TAKES))
        self.assertEqual(1, inst.TAKES[7], "RAD07 t03 runs 6.04 s for 3.7 s")
        metrics = CANDIDATES / "METRICS.json"
        if not metrics.is_file():
            self.skipTest("the candidates live in the main checkout's gitignored work/")
        rows = json.loads(metrics.read_text(encoding="utf-8"))
        for r in rows:
            if r["rank"] == 1:
                n = int(r["code"][3:])
                self.assertEqual(r["take"], inst.TAKES[n], r["code"])
                self.assertFalse(r["runaway"], r["code"])

    def test_the_takes_are_the_candidates_byte_for_byte(self):
        if not CANDIDATES.is_dir():
            self.skipTest("the candidates live in the main checkout's gitignored work/")
        for lump, src in load_installer().plan(CANDIDATES):
            if src is not None:
                self.assertEqual(sha256(src), INSTALLED_SHA256[lump], lump)

    def test_packed_under_sounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            pk3 = Path(tmp) / "sd.pk3"
            build_pk3(SRC, pk3, TOOLS, PROJECT_ROOT / "assets")
            with zipfile.ZipFile(pk3) as zf:
                packed = set(zf.namelist())
        for lump in INSTALLED_SHA256:
            self.assertIn(f"sounds/{lump}.ogg", packed, lump)

    def test_a_licence_row_per_lump_naming_chatterbox_for_the_voices(self):
        text = LICENSES.read_text(encoding="utf-8")
        self.assertIn("me fío para dar OK a TODO", text, "D124's verdict, literal")
        for lump in INSTALLED_SHA256:
            row = next((ln for ln in text.splitlines() if ln.startswith(f"| `{lump}` |")), None)
            self.assertIsNotNone(row, lump)
            if lump in LINE_LUMPS.values():
                self.assertIn("Chatterbox", row, lump)
                self.assertTrue("Thorsten" in row or "«Elena»" in row, lump)


class PlacementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consts = zs_constants(ZS.read_text(encoding="utf-8"))
        cls.maps = {name: route.load_map_data(name) for name in ROOMS}

    def speakers(self, name):
        return [t for t in self.maps[name].textmap.things if t.type == EDNUM]

    def reach(self, t):
        return t.extra.get("arg1") or self.consts["SD_LS_DEFAULT_REACH"]

    def lines(self, t):
        mask = t.extra.get("arg0", 0) or (1 << len(LINES)) - 1
        return {n for n in LINES if mask & (1 << (n - 1))}

    def test_every_map_of_the_campaign_has_its_table(self):
        for name in ROOMS:
            text = (SRC / "maps" / name / "map.py").read_text(encoding="utf-8")
            self.assertIn("ED_LOUDSPEAKER = 21201", text, name)
            self.assertIn("LOUDSPEAKERS = (", text, name)
        self.assertTrue(set(EPISODE_1) <= set(ROOMS))

    def test_one_or_two_a_map_in_the_designs_rooms_on_every_skill(self):
        for name, rooms in ROOMS.items():
            md, found = self.maps[name], self.speakers(name)
            self.assertIn(len(found), (1, 2), name)
            self.assertEqual(rooms, {md.name_of(md.sector_at(t.x, t.y)) for t in found}, name)
            for t in found:
                self.assertTrue(all(getattr(t, f"skill{n}") for n in range(1, 6)), name)

    def test_the_arguments_are_in_range(self):
        for name in ROOMS:
            for t in self.speakers(name):
                self.assertEqual(0, t.extra.get("arg0", 0) & ~((1 << len(LINES)) - 1), name)
                self.assertGreaterEqual(t.extra.get("arg1", 0), 0)
                self.assertIn(t.extra.get("arg4", 0), (0, 1, 2, 3), name)

    def test_the_story_filter(self):
        """RAD11 (Zarya-7 holds) is Episode 1's, and plays in MAP01's komnata;
        RAD15 (Tankograd's plan) waits for MAP03; RAD02 (the dam) for MAP06."""
        for name in ROOMS:
            for t in self.speakers(name):
                lines = self.lines(t)
                if name not in EPISODE_1:
                    self.assertNotIn(LINE_ZARYA, lines, name)
                if name < TANKOGRAD_FROM:
                    self.assertNotIn(LINE_TANKOGRAD, lines, name)
                if name < DAM_FROM:
                    self.assertNotIn(LINE_DAM, lines, name)
        name, room = ZARYA_ROOM
        md = self.maps[name]
        here = [t for t in self.speakers(name) if md.name_of(md.sector_at(t.x, t.y)) == room]
        self.assertIn(LINE_ZARYA, self.lines(here[0]), "the garrison report, in the base itself")
        square = [t for t in self.speakers("MAP06")
                  if self.maps["MAP06"].name_of(self.maps["MAP06"].sector_at(t.x, t.y)) == "z6_square"]
        self.assertIn(RED_SQUARE_PARADE, self.lines(square[0]), "the parade is not cancelled, on Red Square")

    def test_no_two_zones_overlap(self):
        hysteresis = self.consts["SD_LS_HYSTERESIS"]
        for name in ROOMS:
            things = self.maps[name].textmap.things
            zones = [((t.x, t.y), self.reach(t) + hysteresis) for t in things if t.type == EDNUM]
            zones += [((t.x, t.y), (t.extra.get("arg1") or RADIO_DEFAULT_REACH) + RADIO_HYSTERESIS)
                      for t in things if t.type == RADIO_EDNUM]
            for i, (a, ra) in enumerate(zones):
                for b, rb in zones[i + 1:]:
                    self.assertGreater(math.dist(a, b), ra + rb, f"{name}: {a} and {b}")

    def test_the_bed_only_where_the_design_asks_a_far_station(self):
        flag = int(self.consts["SD_LS_FLAG_BED"])
        with_bed = {name for name in ROOMS for t in self.speakers(name) if t.extra.get("arg3", 0) & flag}
        self.assertEqual({"MAP09"}, with_bed)


if __name__ == "__main__":
    unittest.main()
