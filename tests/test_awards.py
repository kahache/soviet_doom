"""Contract of V3 B3, the end-of-episode awards (ADR 013;
zscript/sd/awards.zs, zscript/sd/status_screen.zs, MAPINFO, LANGUAGE,
tools/art/gen_medals.py, docs/engine/BALANCE.md 9).

  wiring      both files included once; SD_AwardsRecorder registered once
              after SD_LoadReporter; GameInfo statscreen_single names
              SD_StatusScreen, which derives from the engine's
              DoomStatusScreen and overrides only the three ShowNextLoc
              virtuals the engine declares (checked against gzdoom.pk3 when
              installed)
  ledger      an Inventory the player keeps across maps (InterHubAmount 1,
              undroppable, unclearable), one slot per MAPxx level number;
              the recorder only writes the level's counters into it
  thresholds  the ZScript constants, BALANCE.md 9's table and this test's
              mirror of the rules agree; the rules give the expected
              awards on worked cases; skill 3 is SpawnFilter Normal in
              MAPINFO
  episodes    an episode ends on MAP03, MAP06 and MAP09 exactly, the maps
              whose `next` is an end sequence
  awards      five lumps, in the same order in the ZScript and the
              generator, 24x30 RGBA, hard alpha, palette v2, the
              generator's bytes (render skipped under SD_SKIP_SLOW_ART)
  text        every id in [enu default], [ru] and [ca]; every character
              drawn by the font that prints it; names fit one line, rules
              two, summary cells their column (widths from the glyphs'
              PNG headers, as the engine measures them)
  layout      the page's constants are the preview's (opsmap_preview)

Run:  .venv/Scripts/python.exe -m unittest tests.test_awards -v
"""

from __future__ import annotations

import os
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
sys.path.insert(0, str(TESTS))

import gen_medals  # noqa: E402
import opsmap_preview  # noqa: E402
from test_death_prompt import gzdoom_pk3, strip_lump_comments  # noqa: E402
from test_language import parse_language  # noqa: E402

SRC = PROJECT_ROOT / "src"
AWARDS_ZS = SRC / "zscript" / "sd" / "awards.zs"
SCREEN_ZS = SRC / "zscript" / "sd" / "status_screen.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
MAPINFO = SRC / "lumps" / "MAPINFO"
LANGUAGE = SRC / "lumps" / "LANGUAGE"
BALANCE = PROJECT_ROOT / "docs" / "engine" / "BALANCE.md"
MEDALS = PROJECT_ROOT / "assets" / "graphics" / "medals"
FONTS = PROJECT_ROOT / "assets" / "fonts"
SECTIONS = ("default", "ru", "ca")

AWARD_KEYS = ("COURAGE", "REDSTAR", "REDBANNER", "PATRIOTIC", "HERO")
IDS = (["SD_AWARDS_TITLE", "SD_AWARDS_KILLS", "SD_AWARDS_SECRETS", "SD_AWARDS_TIME", "SD_AWARDS_PAR"]
       + [f"SD_MEDAL_{k}_{part}" for k in AWARD_KEYS for part in ("NAME", "RULE")])
THRESHOLDS = ("SD_REDSTAR_KILLS_PCT", "SD_REDBANNER_SECRETS_PCT", "SD_HERO_KILLS_PCT",
              "SD_HERO_MIN_SPAWNFILTER", "SD_MAPS_PER_EPISODE")
SPAWNFILTER_BITS = {"baby": 1, "easy": 2, "normal": 4, "hard": 8, "nightmare": 16}

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover
    HAVE_IMAGING = False
imaging = unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not installed")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping the renders")


def code(path: Path) -> str:
    return strip_lump_comments(path.read_text(encoding="utf-8"))


def const(path: Path, name: str) -> int:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([^;]+);", code(path))
    assert m, name
    return int(m.group(1), 0)


def balance_table() -> dict[str, int]:
    """BALANCE.md 9's table: `| ... | `SD_NAME` | value |` rows."""
    text = BALANCE.read_text(encoding="utf-8")
    section = text[text.index("## 9. Medals"):]
    return {k: int(v) for k, v in re.findall(r"`(SD_[A-Z_]+)`\s*\|\s*(\d+)\s*\|", section)}


# --- the rules, mirrored (SD_Awards.Earned) ---------------------------------
def earned(rec: dict) -> list[bool]:
    t = {n: const(AWARDS_ZS, n) for n in THRESHOLDS}
    pct = lambda p, w: 100 if w <= 0 else p * 100 // w  # noqa: E731
    kills = pct(rec["kills"], rec["max_kills"])
    secrets = pct(rec["secrets"], rec["max_secrets"])
    par = rec["par"] > 0 and rec["tics"] // 35 <= rec["par"]
    return [
        rec["maps"] > 0,
        kills >= t["SD_REDSTAR_KILLS_PCT"],
        secrets >= t["SD_REDBANNER_SECRETS_PCT"],
        par,
        rec["maps"] >= t["SD_MAPS_PER_EPISODE"] and kills >= t["SD_HERO_KILLS_PCT"]
        and secrets >= t["SD_REDBANNER_SECRETS_PCT"] and par
        and rec["filter"] >= t["SD_HERO_MIN_SPAWNFILTER"],
    ]


def record(**kw) -> dict:
    base = dict(maps=3, kills=0, max_kills=100, secrets=0, max_secrets=9, tics=0, par=1050, filter=4)
    base.update(kw)
    return base


class WiringTest(unittest.TestCase):
    def test_included_once(self):
        text = strip_lump_comments(ZSCRIPT_TXT.read_text(encoding="utf-8"))
        for inc in ("zscript/sd/awards.zs", "zscript/sd/status_screen.zs"):
            self.assertEqual(len(re.findall(rf'#include\s+"{re.escape(inc)}"', text)), 1, inc)

    def test_recorder_registered_once_after_the_load_reporter(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        lines = re.findall(r"(?im)^\s*AddEventHandlers\s*=\s*(.+)$", text)
        self.assertEqual(len(lines), 1)
        names = re.findall(r'"([^"]+)"', lines[0])
        self.assertEqual(names[0], "SD_LoadReporter")
        self.assertEqual(names.count("SD_AwardsRecorder"), 1)

    def test_the_stats_screen_class(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        gameinfo = re.search(r"(?is)^GameInfo\s*\{(.*?)^\}", text, re.M).group(1)
        self.assertEqual(re.findall(r'(?im)^\s*statscreen_single\s*=\s*"([^"]+)"', gameinfo), ["SD_StatusScreen"])
        c = code(SCREEN_ZS)
        self.assertEqual(re.findall(r"\bclass\s+(\w+)\s*:\s*(\w+)", c), [("SD_StatusScreen", "DoomStatusScreen")])
        self.assertEqual(set(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", c)),
                         {"initShowNextLoc", "updateShowNextLoc", "drawShowNextLoc"})
        self.assertEqual(c.count("{"), c.count("}"))

    def test_the_overrides_exist_in_the_engine(self):
        pk3 = gzdoom_pk3()
        if pk3 is None:
            self.skipTest("gzdoom.pk3 not installed")
        with zipfile.ZipFile(pk3) as z:
            base = z.read("zscript/ui/statscreen/statscreen.zs").decode("utf-8", "replace")
            sp = z.read("zscript/ui/statscreen/statscreen_sp.zs").decode("utf-8", "replace")
            common = z.read("mapinfo/doomcommon.txt").decode("utf-8", "replace")
        for name in ("initShowNextLoc", "updateShowNextLoc", "drawShowNextLoc"):
            self.assertRegex(base, rf"protected virtual void {name}\s*\(", name)
        self.assertRegex(base, r'if \(wbs\.next == ""\)')
        self.assertIn("class DoomStatusScreen : StatusScreen", sp)
        self.assertRegex(common, r'statscreen_single\s*=\s*"DoomStatusScreen"')
        self.assertRegex(base, r"native virtual void drawBackground\(int CurState, bool drawsplat, bool snl_pointeron\)")


class LedgerTest(unittest.TestCase):
    def test_the_ledger_travels_with_the_player(self):
        c = code(AWARDS_ZS)
        m = re.search(r"class SD_CampaignLedger : Inventory\s*\{(.*?)\n\}", c, re.S)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertRegex(body, r"Inventory\.InterHubAmount\s+1;")
        for flag in ("UNDROPPABLE", "UNTOSSABLE", "UNCLEARABLE"):
            self.assertIn(f"+INVENTORY.{flag}", body)
        self.assertEqual(const(AWARDS_ZS, "SD_FIRST_SLOT"), 1)
        self.assertEqual(const(AWARDS_ZS, "SD_LAST_SLOT"), 9)
        self.assertEqual(const(AWARDS_ZS, "SD_SLOTS"), 10)

    def test_the_recorder_copies_the_levels_counters(self):
        c = code(AWARDS_ZS)
        m = re.search(r"class SD_AwardsRecorder : EventHandler\s*\{(.*?)\n\}", c, re.S)
        body = m.group(1)
        self.assertEqual(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", body), ["WorldTick"])
        call = re.search(r"ledger\.Record\(([^;]*)\);", body, re.S).group(1)
        for field in ("Level.killed_monsters", "Level.total_monsters", "Level.found_secrets",
                      "Level.total_secrets", "Level.time", "Level.partime"):
            self.assertIn(field, call)
        self.assertIn("G_SkillPropertyInt(SKILLP_SpawnFilter)", body)
        self.assertNotRegex(c, r"(?i)\bCVar\b|SendNetworkEvent|consoleplayer")


class ThresholdTest(unittest.TestCase):
    def test_zscript_and_balance_agree(self):
        table = balance_table()
        for name in THRESHOLDS:
            self.assertEqual(table.get(name), const(AWARDS_ZS, name), name)

    def test_skill_three_is_spawnfilter_normal(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        block = re.search(r"(?is)skill\s+sd_notonestep\s*\{(.*?)\}", text).group(1)
        flt = re.search(r"(?i)SpawnFilter\s*=\s*(\w+)", block).group(1).lower()
        self.assertEqual(SPAWNFILTER_BITS[flt], const(AWARDS_ZS, "SD_HERO_MIN_SPAWNFILTER"))

    def test_the_rules_are_the_mirrors(self):
        """The ZScript Earned() says what the mirror above says."""
        c = re.sub(r"\s+", " ", code(AWARDS_ZS))
        for clause in ("case SD_AWARD_COURAGE: return r.mapsPlayed > 0;",
                       "case SD_AWARD_REDSTAR: return killPct >= SD_REDSTAR_KILLS_PCT;",
                       "case SD_AWARD_REDBANNER: return secretPct >= SD_REDBANNER_SECRETS_PCT;",
                       "case SD_AWARD_PATRIOTIC: return BeatPar(r);",
                       "return r.mapsPlayed >= SD_MAPS_PER_EPISODE && killPct >= SD_HERO_KILLS_PCT "
                       "&& secretPct >= SD_REDBANNER_SECRETS_PCT && BeatPar(r) "
                       "&& r.minSpawnFilter >= SD_HERO_MIN_SPAWNFILTER;",
                       "return r.parSecs > 0 && TimeSecs(r) <= r.parSecs;",
                       "return whole <= 0 ? 100 : part * 100 / whole;"):
            self.assertIn(clause, c)

    def test_worked_cases(self):
        par_tics = 1050 * 35
        cases = {
            "finished, nothing else": (record(kills=10, tics=par_tics + 35), [1, 0, 0, 0, 0]),
            "75% kills exactly": (record(kills=75, tics=par_tics + 35), [1, 1, 0, 0, 0]),
            "74% kills": (record(kills=74, tics=par_tics + 35), [1, 0, 0, 0, 0]),
            "every secret": (record(secrets=9, tics=par_tics + 35), [1, 0, 1, 0, 0]),
            "no secrets in the episode": (record(max_secrets=0, tics=par_tics + 35), [1, 0, 1, 0, 0]),
            "on par to the second": (record(tics=par_tics + 34), [1, 0, 0, 1, 0]),
            "everything, skill 3": (record(kills=90, secrets=9, tics=par_tics), [1, 1, 1, 1, 1]),
            "everything, skill 2": (record(kills=95, secrets=9, tics=par_tics, filter=2), [1, 1, 1, 1, 0]),
            "everything, 89% kills": (record(kills=89, secrets=9, tics=par_tics), [1, 1, 1, 1, 0]),
            "everything, two maps only": (record(maps=2, kills=100, secrets=9, tics=1), [1, 1, 1, 1, 0]),
            "no par known": (record(par=0, tics=1), [1, 0, 0, 0, 0]),
        }
        for name, (rec, want) in cases.items():
            self.assertEqual([int(b) for b in earned(rec)], want, name)


class EpisodeTest(unittest.TestCase):
    def test_the_episode_ends_where_mapinfo_ends_it(self):
        text = strip_lump_comments(MAPINFO.read_text(encoding="utf-8"))
        ends = set()
        for m in re.finditer(r"(?ims)^map\s+MAP0(\d)[^{]*\{(.*?)^\}", text):
            # V3 B2: `EndSequence, "SD_EndingN"` (MOD-SPEC 6.15) ends it as `endtitle` did.
            if re.search(r"(?im)^\s*next\s*=\s*(endtitle|EndSequence)\b", m.group(2)):
                ends.add(int(m.group(1)))
        per = const(AWARDS_ZS, "SD_MAPS_PER_EPISODE")
        episodes = const(AWARDS_ZS, "SD_EPISODES")
        mirror = {n for n in range(1, 10) if per <= n <= per * episodes and n % per == 0}
        self.assertEqual(ends, mirror)
        self.assertEqual(ends, {3, 6, 9})

    def test_the_screen_starts_the_page_only_at_an_episode_end(self):
        c = re.sub(r"\s+", " ", code(SCREEN_ZS))
        self.assertIn('if (wbs.next == "" && SD_Awards.IsEpisodeEnd(Level.levelnum))', c)
        self.assertIn("Super.initShowNextLoc();", c)
        self.assertIn("Super.updateShowNextLoc();", c)
        self.assertIn("Super.drawShowNextLoc();", c)


class AwardPicturesTest(unittest.TestCase):
    def test_five_awards_in_one_order(self):
        c = code(AWARDS_ZS)
        enum = re.search(r"enum EAward\s*\{(.*?)\}", c, re.S).group(1)
        members = re.findall(r"\b(SD_AWARD_\w+)", enum)
        self.assertEqual(members[-1], "SD_AWARD_COUNT")
        self.assertEqual(len(members) - 1, len(gen_medals.AWARDS))
        self.assertEqual(const(SCREEN_ZS, "SD_AWARD_SLOTS"), len(gen_medals.AWARDS))
        lumps = re.findall(r'case (SD_AWARD_\w+):\s*return "(SDAW\w+)";', c)
        tail = re.search(r'return "(SDAW\w+)";\s*\}\s*static clearscope String NameOf', c).group(1)
        order = [l for _, l in lumps] + [tail]
        self.assertEqual(order, [l for l, _ in gen_medals.AWARDS])
        self.assertEqual([m for m, _ in lumps], members[:-2])

    def test_installed(self):
        for lump, _ in gen_medals.AWARDS:
            blob = (MEDALS / f"{lump}.png").read_bytes()
            w, h = struct.unpack(">II", blob[16:24])
            colour = blob[25]                        # IHDR colour type; 6 = RGBA
            self.assertEqual((w, h, colour), (gen_medals.WIDTH, gen_medals.HEIGHT, 6), lump)
        self.assertEqual({p.stem for p in MEDALS.glob("*.png")}, {l for l, _ in gen_medals.AWARDS})

    @imaging
    def test_hard_alpha_palette_v2(self):
        import palette
        v2 = {tuple(c) for c in palette.colours(2)}
        for lump, _ in gen_medals.AWARDS:
            a = np.asarray(Image.open(MEDALS / f"{lump}.png"))
            self.assertLessEqual(set(np.unique(a[..., 3]).tolist()), {0, 255}, lump)
            self.assertLessEqual({tuple(c) for c in a[a[..., 3] == 255][:, :3].tolist()}, v2, lump)

    @imaging
    @slow
    def test_installed_is_the_generators_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            blobs = gen_medals.build(Path(tmp))
        for lump, blob in blobs.items():
            self.assertEqual((MEDALS / f"{lump}.png").read_bytes(), blob, lump)

    def test_no_portrait_award(self):
        """No Order of Lenin (a real person's profile) and no Order of Glory."""
        drawers = " ".join(f"{l} {d.__name__}" for l, d in gen_medals.AWARDS).upper()
        self.assertNotRegex(drawers, r"LENIN|GLORY|SDAWLEN|SDAWGLR")
        self.assertIn("no Order of Lenin", gen_medals.__doc__)


class TextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))
        cls.widths = {f: cls.glyph_widths(f) for f in ("bigfont", "defsmallfont")}

    @staticmethod
    def glyph_widths(font: str) -> dict[int, int]:
        out = {}
        for p in (FONTS / font).glob("*.png"):
            try:
                out[int(p.stem, 16)] = struct.unpack(">I", p.read_bytes()[16:20])[0]
            except ValueError:
                pass
        return out

    def text(self, code_: str, ident: str) -> str:
        value = self.sections[code_][ident]
        return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', value))

    def glyph(self, font: str, ch: str) -> int | None:
        w = self.widths[font]
        return w.get(ord(ch), w.get(ord(ch.upper())) if len(ch.upper()) == 1 else None)

    def width(self, font: str, s: str) -> int:
        return sum(self.glyph(font, ch) or 0 for ch in s)

    def wrap(self, font: str, s: str, room: int) -> list[str]:
        lines, cur = [], ""
        for word in s.split(" "):
            trial = word if not cur else cur + " " + word
            if self.width(font, trial) <= room or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        return lines + ([cur] if cur else [])

    def test_every_id_in_every_language(self):
        for code_ in SECTIONS:
            missing = [i for i in IDS if i not in self.sections[code_]]
            self.assertEqual(missing, [], code_)

    def test_every_character_has_a_glyph(self):
        for code_ in SECTIONS:
            for ident in IDS:
                font = "bigfont" if ident == "SD_AWARDS_TITLE" else "defsmallfont"
                for ch in self.text(code_, ident):
                    self.assertIsNotNone(self.glyph(font, ch), f"[{code_}] {ident}: {ch!r} in {font}")

    def test_it_fits_the_page(self):
        L = opsmap_preview.AWARDS_LAYOUT
        room = L["TEXT_RIGHT"] - L["TEXT_X"]
        for code_ in SECTIONS:
            self.assertLessEqual(self.width("bigfont", self.text(code_, "SD_AWARDS_TITLE")), L["SCREEN_W"])
            for k in AWARD_KEYS:
                name = self.text(code_, f"SD_MEDAL_{k}_NAME")
                self.assertLessEqual(self.width("defsmallfont", name), room, f"[{code_}] {name}")
                rule = self.text(code_, f"SD_MEDAL_{k}_RULE")
                self.assertLessEqual(len(self.wrap("defsmallfont", rule, room)), L["RULE_MAX_LINES"],
                                     f"[{code_}] {rule}")
            for ident in ("SD_AWARDS_KILLS", "SD_AWARDS_SECRETS", "SD_AWARDS_TIME", "SD_AWARDS_PAR"):
                label = self.text(code_, ident)
                self.assertLessEqual(self.width("defsmallfont", label), L["SUMMARY_COLUMN_W"], f"[{code_}] {label}")
        self.assertLessEqual(self.width("defsmallfont", "1:23:45"), L["SUMMARY_COLUMN_W"])

    def test_the_page_names_its_ids(self):
        c = code(SCREEN_ZS) + code(AWARDS_ZS)
        for ident in IDS:
            self.assertIn(f'"${ident}"', c, ident)


class LayoutTest(unittest.TestCase):
    def test_the_preview_draws_the_screens_layout(self):
        for key, value in opsmap_preview.AWARDS_LAYOUT.items():
            self.assertEqual(const(SCREEN_ZS, f"SD_{key}"), value, key)

    def test_the_rows_fit_the_screen(self):
        L = opsmap_preview.AWARDS_LAYOUT
        last_row = L["ROWS_Y"] + (len(gen_medals.AWARDS) - 1) * L["ROW_H"]
        self.assertLessEqual(last_row + gen_medals.HEIGHT, 200)
        self.assertLessEqual(last_row + L["RULE_DY"] + L["RULE_MAX_LINES"] * L["RULE_LINE_H"], 200)
        self.assertGreaterEqual(L["ROWS_Y"], L["SUMMARY_VALUE_Y"] + L["RULE_LINE_H"])


if __name__ == "__main__":
    unittest.main()
