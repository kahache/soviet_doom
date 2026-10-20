"""N9e (D83, D86): the approved enemy sounds and beds, mastered and installed,
and the two music lumps of D83/D86.

What is pinned, and why:

  contract   exactly what the CEO approved, from docs/PRD.md: D83's 30 enemy
             sounds and 5 beds, D86's alternatives (SDRRIATK alt1-3, alt2
             once its final click was lowered; SDLTRATK alt2; SDSTOPAI,
             SDSTODTH, SDPZRPAI alt1-3; the beds SDRRIPAI, SDLTRPAI,
             SDLTRDTH alt1-3); nothing rejected is installed (the D83 NO
             drafts and beds, SDLTRATK alt1 and alt3); D91's seven voice takes
             ship as $random groups (the rifleman's sight, the trooper's idle) and
             the other ten voices keep their Freedoom lumps
  files      assets/sounds/enemies/ holds exactly the 57 OGGs, each the file
             tools/audio/master_enemy_sfx.py installed (SHA-256 pinned),
             each a Vorbis stream
  sndinfo    every approved name resolves: a sound with one take to its
             lump, a sound with several to a `$random` alias over
             <name>/<take> lines (ZDoom wiki SNDINFO; gzdoom.pk3's own
             `$random grunt/sight { ... }`), each member a packed lump; the
             beds live under sd/bed/ and nothing plays them yet (they go
             under the voices, D87); no name is defined twice
  music      D_SDTITL is GameInfo's IntermissionMusic, D_SDM01T is RANGE's
             music, both packed, and D_SDAMUR (D83: NO) no longer ships
  licences   a LICENSES.md row per packed enemy sound, ENEMY-SOUNDS 5.12
             names every installed lump and its OGG hash
  loudness   (numpy + ffmpeg) every installed OGG, decoded, sits within its
             window: the target +-1 dB, or the pinned shortfall; the peak
             never reaches 0 dBFS; the Freedoom references re-measured
  takes      (slow: renders) re-rendering every approved take and mastering
             it gives the pinned WAV master and OGG byte for byte; the D86
             alternatives ship exactly as the CEO heard them; a rejected
             take is not what is installed

The first blocks are stdlib only (CI's python has no numpy). The renders
need the gitignored work/audio/sfx_sources/ and ffmpeg and are skipped with
SD_SKIP_SLOW_ART=1 (`tools/verify.py fast`).

Run:  .venv/Scripts/python.exe -m unittest tests.test_enemy_sfx_install -v
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
SNDINFO = SRC_DIR / "lumps" / "SNDINFO"
MAPINFO = SRC_DIR / "lumps" / "MAPINFO"
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "enemies"
MUSIC_DIR = PROJECT_ROOT / "assets" / "music"
MASTER_PY = TOOLS_DIR / "audio" / "master_enemy_sfx.py"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
ENEMY_SOUNDS = PROJECT_ROOT / "docs" / "sound" / "ENEMY-SOUNDS.md"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "audio"))

import check_pk3  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

try:
    import numpy as np
    import gen_enemy_alts as ea
    import gen_sfx as gs
    import gen_weapon_alts as alts
    import gen_weapon_sfx as gws
    import master_enemy_sfx as mes
except ImportError:                                    # pragma: no cover
    np = ea = gs = alts = gws = mes = None

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the re-render of the 57 masters")

ACTOR = {"RRI": "reichrifleman", "LTR": "legiontrooper", "STO": "stormtrooper", "HND": "reichhound",
         "DGB": "doughboy", "PZR": "panzermensch", "GEN": "general"}
EVENT = {"ACT": "active", "SIT": "sight", "ATK": "attack", "MEL": "melee", "MIS": "missile",
         "EXP": "explode", "PAI": "pain", "DTH": "death", "XDT": "xdeath", "STP": "step"}

# --- D83 and D86, as ratified (docs/PRD.md) ------------------------------------------
D83_SOUNDS = ("SDRRIXDT", "SDLTRXDT", "SDSTOACT", "SDSTOSIT", "SDSTOMEL", "SDSTOMIS", "SDSTOEXP",
              "SDSTOXDT", "SDHNDACT", "SDHNDSIT", "SDHNDATK", "SDHNDPAI", "SDHNDDTH", "SDDGBACT",
              "SDDGBSIT", "SDDGBMEL", "SDDGBMIS", "SDDGBEXP", "SDDGBPAI", "SDDGBDTH", "SDPZRACT",
              "SDPZRSIT", "SDPZRMEL", "SDPZRMIS", "SDPZREXP", "SDPZRDTH", "SDPZRSTP", "SDGENACT",
              "SDGENMIS", "SDGENEXP")
D83_BEDS = ("SDRRIDTH", "SDLTRACT", "SDLTRSIT", "SDGENPAI", "SDGENDTH")
D86_ALTS = {"SDRRIATK": (1, 2, 3), "SDLTRATK": (2,), "SDSTOPAI": (1, 2, 3), "SDSTODTH": (1, 2, 3),
            "SDPZRPAI": (1, 2, 3)}
D86_BEDS = {"SDRRIPAI": (1, 2, 3), "SDLTRPAI": (1, 2, 3), "SDLTRDTH": (1, 2, 3)}
REJECTED = {"drafts": ("SDRRIATK", "SDLTRATK", "SDSTOPAI", "SDSTODTH", "SDPZRPAI"),
            "beds": ("SDRRIPAI", "SDLTRPAI", "SDLTRDTH"),
            "alts": ("SDLTRATK_alt1", "SDLTRATK_alt3")}
# D91: the seven approved voice takes, group -> {member: lump}.
D91_VOICES = {
    "sd/mon/reichrifleman/sight": {"sd/mon/reichrifleman/sight/1": "SDRRISI1",
                                   "sd/mon/reichrifleman/sight/3": "SDRRISI3"},
    "sd/mon/legiontrooper/active": {f"sd/mon/legiontrooper/active/{n}": f"SDLTRAC{n}" for n in range(1, 6)},
}
# The voices still waiting (D91): logical name -> the Freedoom lump it keeps.
VOICES = {"sd/mon/reichrifleman/active": "DSPOSACT",
          "sd/mon/reichrifleman/pain": "DSPOPAIN", "sd/mon/reichrifleman/death": "DSPODTH1",
          "sd/mon/legiontrooper/sight": "DSPOSIT2",
          "sd/mon/legiontrooper/pain": "DSPOPAIN", "sd/mon/legiontrooper/death": "DSPODTH2",
          "sd/mon/general/sight": "DSCYBSIT", "sd/mon/general/summon": "DSVILSIT",
          "sd/mon/general/pain": "DSDMPAIN", "sd/mon/general/death": "DSCYBDTH"}


def name_of(card: str, bed: bool = False) -> str:
    return f"sd/{'bed' if bed else 'mon'}/{ACTOR[card[2:5]]}/{EVENT[card[5:]]}"


def expected() -> dict[str, dict[str, str]]:
    """name the game asks for -> {member name or itself: lump}."""
    out: dict[str, dict[str, str]] = {}
    for card in D83_SOUNDS:
        out[name_of(card)] = {name_of(card): card}
    for card in D83_BEDS:
        out[name_of(card, True)] = {name_of(card, True): f"{card[:6]}B1"}
    for card, takes in D86_ALTS.items():
        g = name_of(card)
        out[g] = {g: card} if len(takes) == 1 else {f"{g}/{n}": f"{card[:7]}{n}" for n in takes}
    for card, takes in D86_BEDS.items():
        g = name_of(card, True)
        out[g] = {f"{g}/{n}": f"{card[:6]}B{n}" for n in takes}
    out.update(D91_VOICES)
    return out


EXPECTED = expected()
EXPECTED_LUMPS = {lump for members in EXPECTED.values() for lump in members.values()}
RANDOM_RE = re.compile(r"^\$random\s+(\S+)\s*\{\s*([^}]*?)\s*\}$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def master_constant(name: str):
    """A literal constant of master_enemy_sfx.py, read without importing it."""
    tree = ast.parse(MASTER_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = [node.target] if isinstance(node, ast.AnnAssign) else getattr(node, "targets", [])
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {MASTER_PY.name}")


def sndinfo() -> tuple[dict[str, str], dict[str, list[str]]]:
    lines: dict[str, str] = {}
    groups: dict[str, list[str]] = {}
    for raw in SNDINFO.read_text(encoding="utf-8").splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        m = RANDOM_RE.match(line)
        if m:
            if m.group(1) in groups or m.group(1) in lines:
                raise AssertionError(f"{m.group(1)} defined twice")
            groups[m.group(1)] = m.group(2).split()
            continue
        logical, lump = line.split()
        if logical in lines or logical in groups:
            raise AssertionError(f"{logical} defined twice")
        lines[logical] = lump
    return lines, groups


def zscript_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in (SRC_DIR / "zscript").rglob("*.zs"))


# --- Contract ------------------------------------------------------------------------

class ContractTests(unittest.TestCase):
    def test_64_lumps_43_sounds_14_beds_7_voices_nine_random_groups(self):
        self.assertEqual(len(EXPECTED_LUMPS), 64)
        self.assertEqual(sum(1 for g in EXPECTED if g.startswith("sd/bed/")), 8)
        self.assertEqual(sum(1 for g, m in EXPECTED.items() if len(m) > 1), 9)

    def test_the_tool_installs_exactly_the_approved(self):
        voices = {lump for g in D91_VOICES.values() for lump in g.values()}
        self.assertEqual(set(master_constant("VOICE_SHA256")), voices)
        self.assertEqual(set(master_constant("INSTALLED_SHA256")), EXPECTED_LUMPS - voices)
        self.assertEqual(set(master_constant("REJECTED_DRAFTS")), set(REJECTED["drafts"]))
        self.assertEqual(set(master_constant("REJECTED_BEDS")), set(REJECTED["beds"]))
        self.assertEqual(set(master_constant("REJECTED_ALTS")), set(REJECTED["alts"]))

    def test_codec_trims_are_small_and_only_on_the_alternatives(self):
        trimmed = master_constant("CODEC_TRIMMED")
        alts_ = {lump for card, takes in D86_ALTS.items() for lump in EXPECTED[name_of(card)].values()}
        alts_ |= {lump for card, takes in D86_BEDS.items() for lump in EXPECTED[name_of(card, True)].values()}
        self.assertLessEqual(set(trimmed), alts_)
        for lump, db in trimmed.items():
            self.assertTrue(0 < db <= 2.0, f"{lump}: {db} dB is a re-voicing, not a codec margin")

    def test_short_of_target_names_only_installed_lumps(self):
        short = master_constant("SHORT_OF_TARGET")
        self.assertLessEqual(set(short), EXPECTED_LUMPS)
        for lump, db in short.items():
            self.assertGreater(db, 1.0, f"{lump}: within the window is not short")

    def test_lump_names_fit_and_take_digits_match(self):
        for lump in EXPECTED_LUMPS:
            self.assertRegex(lump, r"^SD(RRI|LTR|STO|HND|DGB|PZR|GEN)[A-Z0-9]{3}$")
        self.assertFalse(EXPECTED_LUMPS & set(VOICES.values()))


# --- Files -------------------------------------------------------------------------------

class FileTests(unittest.TestCase):
    def test_exactly_the_64_oggs(self):
        self.assertEqual(sorted(p.name for p in ASSET_DIR.iterdir()),
                         sorted(f"{lump}.ogg" for lump in EXPECTED_LUMPS))

    def test_each_is_the_installed_file_and_a_vorbis_stream(self):
        pins = {k: v[1] for k, v in master_constant("INSTALLED_SHA256").items()}
        pins.update(master_constant("VOICE_SHA256"))
        for lump in EXPECTED_LUMPS:
            with self.subTest(lump):
                data = (ASSET_DIR / f"{lump}.ogg").read_bytes()
                self.assertEqual(sha256(data), pins[lump])
                self.assertTrue(data.startswith(b"OggS"))
                self.assertIn(b"\x01vorbis", data[:64])

    def test_no_rejected_or_voice_lump_ships(self):
        names = {p.stem.upper() for p in (PROJECT_ROOT / "assets" / "sounds").rglob("*.ogg")}
        rejected = set(REJECTED["drafts"]) - {"SDLTRATK"}     # SDLTRATK ships as its alt2 (D86)
        self.assertFalse(names & rejected)
        self.assertFalse(names & set(REJECTED["beds"]))        # bed lumps are ...B<n>, never the voice's name
        voices = {"SDRRIACT", "SDRRISIT", "SDRRIPAI", "SDRRIDTH", "SDLTRACT", "SDLTRSIT", "SDLTRPAI",
                  "SDLTRDTH", "SDGENSIT", "SDGENSUM", "SDGENPAI", "SDGENDTH"}
        self.assertFalse(names & voices, "a voice lump shipped before D87's takes")


# --- SNDINFO ---------------------------------------------------------------------------

class SndinfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines, cls.groups = sndinfo()

    def test_every_approved_name_resolves_to_its_lump(self):
        for group, members in EXPECTED.items():
            with self.subTest(group):
                if len(members) == 1:
                    (name, lump), = members.items()
                    self.assertEqual(name, group)
                    self.assertEqual(self.lines.get(group), lump)
                    self.assertNotIn(group, self.groups)
                else:
                    self.assertEqual(self.groups.get(group), list(members))
                    for name, lump in members.items():
                        self.assertEqual(self.lines.get(name), lump, name)

    def test_random_groups_are_exactly_the_multi_take_sounds(self):
        enemy = {g: m for g, m in self.groups.items() if not g.startswith("sd/weapon/")}   # D94's are the weapons'
        self.assertEqual(set(enemy), {g for g, m in EXPECTED.items() if len(m) > 1})
        for group, members in enemy.items():
            for m in members:
                self.assertTrue(m.startswith(f"{group}/"), m)
                self.assertRegex(self.lines[m], r"^SD[A-Z]{5}[0-9]$")

    def test_the_voices_keep_their_freedoom_lumps(self):
        for logical, lump in VOICES.items():
            self.assertEqual(self.lines.get(logical), lump, logical)

    def test_the_beds_are_parked(self):
        code = zscript_text()
        self.assertNotIn("sd/bed/", code, "a bed is played now: SNDINFO and ENEMY-SOUNDS 5.12 must say so")
        beds = [g for g in EXPECTED if g.startswith("sd/bed/")]
        for g in beds:
            voice = g.replace("sd/bed/", "sd/mon/")
            self.assertTrue(voice in VOICES or voice in D91_VOICES, f"{g} has no voice to go under")

    def test_every_sd_mon_name_the_classes_play_is_defined(self):
        played = set(re.findall(r'"(sd/mon/[a-z0-9/_]+)"', zscript_text()))
        defined = set(self.lines) | set(self.groups)
        self.assertLessEqual(played, defined)

    def test_the_izh_shot_is_take_b(self):
        self.assertEqual(self.lines.get("sd/weapon/izh/fire"), "SDIZFIR")


# --- Music and MAPINFO -------------------------------------------------------------------

class MusicTests(unittest.TestCase):
    def setUp(self):
        self.code = "\n".join(line.split("//")[0] for line in MAPINFO.read_text(encoding="utf-8").splitlines())

    def test_intermission_is_d_sdtitl(self):
        gameinfo = re.search(r"^GameInfo\s*\{(.*?)^\}", self.code, re.M | re.S).group(1)
        self.assertRegex(gameinfo, r'(?m)^\s*IntermissionMusic\s*=\s*"D_SDTITL"\s*$')

    def test_the_range_plays_d_sdm01t_and_map01_d_sdm1n2(self):
        blocks = dict(re.findall(r'^map\s+(\w+)[^{]*\{(.*?)^\}', self.code, re.M | re.S))
        self.assertRegex(blocks["RANGE"], r'(?m)^\s*music\s*=\s*"D_SDM01T"\s*$')
        self.assertRegex(blocks["MAP01"], r'(?m)^\s*music\s*=\s*"D_SDM1N2"\s*$')

    def test_the_music_lumps(self):
        names = {p.stem for p in MUSIC_DIR.glob("*.mid")}
        self.assertLessEqual({"D_SDTITL", "D_SDM01T", "D_SDM1N2"}, names)
        self.assertNotIn("D_SDAMUR", names)
        self.assertNotIn("D_SDM01", names)
        work = PROJECT_ROOT / "work" / "audio"
        for lump in ("D_SDTITL", "D_SDM01T"):
            if (work / f"{lump}.mid").is_file():
                self.assertEqual((MUSIC_DIR / f"{lump}.mid").read_bytes(), (work / f"{lump}.mid").read_bytes())


# --- Package ------------------------------------------------------------------------------

class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")
        with zipfile.ZipFile(cls.pk3) as zf:
            cls.names = set(zf.namelist())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_flat_under_sounds_and_music(self):
        for lump in EXPECTED_LUMPS:
            self.assertIn(f"sounds/{lump}.ogg", self.names)
        for lump in ("D_SDTITL", "D_SDM01T"):
            self.assertIn(f"music/{lump}.mid", self.names)
        self.assertNotIn("music/D_SDAMUR.mid", self.names)

    def test_check_pk3_passes(self):
        report = check_pk3.check_pk3(self.pk3)
        self.assertEqual([f.render() for f in report.errors], [])


# --- Licences and documents ----------------------------------------------------------------

class DocumentTests(unittest.TestCase):
    def test_a_licence_row_per_packed_sound(self):
        text = LICENSES.read_text(encoding="utf-8")
        for lump in EXPECTED_LUMPS:
            self.assertRegex(text, rf"(?m)^\| `{lump}`", lump)

    def test_enemy_sounds_records_the_install(self):
        text = ENEMY_SOUNDS.read_text(encoding="utf-8")
        section = text[text.index("### 5.12"):]
        pins = {k: v[1] for k, v in master_constant("INSTALLED_SHA256").items()}
        pins.update(master_constant("VOICE_SHA256"))
        for lump, ogg in pins.items():
            self.assertIn(f"`{lump}`", section, lump)
            self.assertIn(ogg, section, f"{lump}'s OGG hash is not in ENEMY-SOUNDS 5.12")

    def test_the_voice_rows_name_chatterbox(self):
        # tools/release.py reads "Chatterbox" in a register Origin to say voice lines ship (D93)
        text = LICENSES.read_text(encoding="utf-8")
        for members in D91_VOICES.values():
            for lump in members.values():
                row = next(ln for ln in text.splitlines() if ln.startswith(f"| `{lump}` |"))
                self.assertIn("Chatterbox", row)


# --- Loudness (numpy + ffmpeg) ---------------------------------------------------------------

@needs_numpy
class LoudnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if gws.ffmpeg_path() is None:
            raise unittest.SkipTest("ffmpeg is not on the PATH: cannot decode the OGGs")
        cls.decoded = {i.lump: gws.decode(ASSET_DIR / f"{i.lump}.ogg") for i in mes.INSTALLS}

    def test_in_window_or_at_the_pinned_shortfall(self):
        for inst in mes.INSTALLS:
            loud = alts.loud_a_db(self.decoded[inst.lump])
            short = mes.SHORT_OF_TARGET.get(inst.lump)
            with self.subTest(inst.lump, loud=round(loud, 2), target=round(inst.target_db, 2)):
                if short is None:
                    self.assertLessEqual(abs(loud - inst.target_db),
                                         mes.LOUDNESS_TOLERANCE_DB + mes.CODEC_LOUDNESS_DB)
                else:
                    self.assertAlmostEqual(inst.target_db - loud, short,
                                           delta=mes.SHORT_TOLERANCE_DB + mes.CODEC_LOUDNESS_DB)

    def test_never_clips(self):
        # Vorbis lifted seven of the D86 alternatives over -0.1 dBFS (SDLTRATK
        # to +1.4): the codec check limited those (CODEC_TRIMMED).
        for lump, x in self.decoded.items():
            self.assertLess(alts.peak_db(x), mes.DECODED_PEAK_CEILING_DBFS, lump)

    def test_the_voices_are_the_pages_oggs_in_their_window(self):
        for v in mes.VOICE_INSTALLS:
            x = gws.decode(ASSET_DIR / f"{v.lump}.ogg")
            self.assertLess(alts.peak_db(x), mes.DECODED_PEAK_CEILING_DBFS, v.lump)
            self.assertLessEqual(abs(alts.loud_a_db(x) - v.target_db),
                                 mes.LOUDNESS_TOLERANCE_DB + mes.CODEC_LOUDNESS_DB, v.lump)
            if v.path.is_file():
                self.assertEqual((ASSET_DIR / f"{v.lump}.ogg").read_bytes(), v.path.read_bytes(), v.lump)

    def test_a_bed_sits_under_its_voices_stand_in(self):
        for inst in mes.INSTALLS:
            if inst.bed:
                self.assertAlmostEqual(inst.target_db, mes.FREEDOOM_LOUD_A[inst.ref] - 3.0, places=6)

    def test_targets_are_the_freedoom_lumps_sndinfo_played(self):
        # The stand-in each sound replaced, as the M3 sheet and gen_enemy_alts
        # name it (the beds: their voice's).
        for inst in mes.INSTALLS:
            if inst.source == "alt" and not inst.bed:
                self.assertEqual(inst.ref, ea.TARGETS[inst.card][1], inst.lump)
        was = {**VOICES, "sd/mon/legiontrooper/active": "DSPOSACT"}     # its stand-in until D91
        stand_in = {was[g.replace("sd/bed/", "sd/mon/")] for g in EXPECTED if g.startswith("sd/bed/")}
        self.assertEqual({i.ref for i in mes.INSTALLS if i.bed}, stand_in)

    def test_freedoom_references_remeasured(self):
        if not IWAD.is_file():
            self.skipTest("iwads/freedoom2.wad is not on this machine")
        for name, want in mes.FREEDOOM_LOUD_A.items():
            x, rate = alts.read_wav(gws.placeholder_wav(name))
            self.assertAlmostEqual(alts.loud_a_db(x, rate), want, delta=mes.FREEDOOM_TOLERANCE_DB, msg=name)


ALT_PAGE_DIR = PROJECT_ROOT / "work" / "audio" / "enemy_alt"


@unittest.skipUnless(ALT_PAGE_DIR.is_dir(), "work/ not present (CI has no work/)")
class AltIdentityTests(unittest.TestCase):
    def test_the_d86_alternatives_are_the_oggs_the_ceo_heard(self):
        """The OGG the D86 page played (gen_enemy_alts.py, SDRRIATK alt2 as
        re-rendered with its final click lowered) is the one that ships."""
        trimmed = master_constant("CODEC_TRIMMED")
        for card, takes in {**D86_ALTS, **D86_BEDS}.items():
            for n in takes:
                members = EXPECTED[name_of(card, card in D86_BEDS)]
                lump = next(lp for nm, lp in members.items() if len(members) == 1 or nm.endswith(f"/{n}"))
                same = (ASSET_DIR / f"{lump}.ogg").read_bytes() == (ALT_PAGE_DIR / f"{card}_alt{n}.ogg").read_bytes()
                with self.subTest(lump):
                    # the codec-limited ones differ by their trim only (TakeTests)
                    self.assertEqual(same, lump not in trimmed)


# --- Takes: the re-render (slow) ----------------------------------------------------------------

def _have_sources() -> bool:
    if gws is None or gws.ffmpeg_path() is None:
        return False
    return gs.SOURCES_DIR.is_dir()


@needs_numpy
@slow
class TakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _have_sources():
            raise unittest.SkipTest("work/audio/sfx_sources/ or ffmpeg missing")
        cls.done, skipped = mes.build()
        assert not skipped, skipped

    def test_the_approved_takes_give_the_installed_masters(self):
        for m in self.done:
            with self.subTest(m.install.lump):
                wav_pin, ogg_pin = mes.INSTALLED_SHA256[m.install.lump]
                self.assertEqual(sha256(m.wav), wav_pin)
                self.assertEqual(sha256(mes.ogg_of(m)), ogg_pin)

    def test_the_d86_alternatives_ship_as_the_ceo_heard_them(self):
        for m in self.done:
            if m.install.source != "alt":
                continue
            with self.subTest(m.install.lump):
                trim = mes.CODEC_TRIMMED.get(m.install.lump)
                if trim is None:
                    self.assertTrue(m.untouched)
                    self.assertIs(m.x, m.draft)
                else:       # the same take, its peaks limited by the codec check
                    self.assertAlmostEqual(m.codec_db, trim, delta=0.05)
                    self.assertGreater(float(np.corrcoef(m.x, m.draft)[0, 1]), 0.98)
                    self.assertEqual((m.shelf_db, m.limit_db, m.gain_db), (0.0, 0.0, 0.0))

    def test_window_on_the_wav_masters(self):
        for m in self.done:
            loud = alts.loud_a_db(m.x)
            short = mes.SHORT_OF_TARGET.get(m.install.lump)
            with self.subTest(m.install.lump):
                self.assertEqual(m.reached, short is None)
                if short is None:
                    self.assertLessEqual(abs(loud - m.install.target_db), mes.LOUDNESS_TOLERANCE_DB)
                else:
                    self.assertAlmostEqual(m.install.target_db - loud, short, delta=mes.SHORT_TOLERANCE_DB)
                self.assertLessEqual(alts.peak_db(m.x), mes.PEAK_DBFS + 0.01)
                self.assertLessEqual(m.limit_db, mes.MAX_LIMIT_DB)
                self.assertEqual(len(m.x), len(m.draft))

    def test_the_master_is_the_draft_levelled_not_a_new_sound(self):
        for m in self.done:
            if not m.untouched:
                self.assertGreater(float(np.corrcoef(m.x, m.draft)[0, 1]), 0.8, m.install.lump)

    def test_no_rejected_take_is_installed(self):
        installed = {mes.INSTALLED_SHA256[m.install.lump][0] for m in self.done}
        for card in REJECTED["drafts"]:
            x = gs.render(card).samples
            self.assertNotIn(sha256(gws.wav_bytes(x)), installed, card)
        for card in REJECTED["beds"]:
            x = gs.render(f"{card}{gs.BED_SUFFIX}").samples
            self.assertNotIn(sha256(gws.wav_bytes(x)), installed, card)
        for name in REJECTED["alts"]:
            x, _, _ = ea.render(ea.ALTS_BY_NAME[name])
            self.assertNotIn(sha256(gws.wav_bytes(x)), installed, name)
        refused = ([mes.Install(c, c, "draft", 1, "x", "x", "DSPISTOL", "D83") for c in REJECTED["drafts"]]
                   + [mes.Install(c, c, "bed", 1, "x", "x", "DSPOPAIN", "D83") for c in REJECTED["beds"]]
                   + [mes.Install("SDLTRATK", "SDLTRATK", "alt", n, "x", "x", "DSDSHTGN", "D86") for n in (1, 3)])
        for inst in refused:
            with self.assertRaises(ValueError, msg=inst.draft_name):
                mes.render_draft(inst)

    def test_list_writes_nothing(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mes.main(["--list"]), 0)
        self.assertIn("57 approved (D83, D86)", out.getvalue())
        with redirect_stderr(err):
            self.assertEqual(mes.main(["SDSTOPAI"]), 2)
        self.assertIn("SDSTOPAI", err.getvalue())


if __name__ == "__main__":
    unittest.main()
