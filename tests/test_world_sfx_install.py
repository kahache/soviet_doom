#!/usr/bin/env python3
"""D125: the world sounds the CEO approved, installed (tools/audio/master_world_sfx.py).

What is pinned, and why:

  contract   exactly the CEO's verdict of docs/PRD.md D125: the 50 OKs and
             SDPLOOF_w1 laid over SDPLOOF_w3's impact ship, the five NO do
             not, the jump keeps Freedoom's DSJUMP; names fit 8 characters
             and end in the candidate's number
  files      assets/sounds/world/ holds exactly the 51 OGGs, each the file the
             tool installed (SHA-256 pinned), each a Vorbis stream; all but
             SDSGOOF1 are the CEO's page OGGs byte for byte (when work/ is here)
  sndinfo    the tool's block is in src/lumps/SNDINFO: every sound a
             `$random` group over its takes, each take a packed lump; the
             world's groups sit on the engine's own names (gzdoom.pk3's
             doors/dr1_open ... misc/teleport, and misc/k_pkup for keys,
             members <name>/<take>); the
             player's are reached by `$playeralias` for every Doom player
             sound but *jump, *gibbed and *fist, in all three genders
  hook       SD_Izh plays sd/weapon/izh/pickup
  package    the PK3 packs them flat under sounds/ and check_pk3 passes
  documents  a LICENSES.md row per lump (Chatterbox named where a take is AI,
             Freedoom credited where our DSSLOP gib is a layer); WORLD-SOUNDS
             names each lump and its OGG hash; PRD D125 quotes the verdict
  loudness   (numpy + ffmpeg) every decoded OGG under the peak ceiling and in
             its window, or at its pinned shortfall
  layered    (slow: renders from work/) SDSGOOF1 re-renders byte for byte

Run:  .venv/Scripts/python.exe -m unittest tests.test_world_sfx_install -v
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
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "world"
MASTER_PY = TOOLS_DIR / "audio" / "master_world_sfx.py"
CAND_DIR = PROJECT_ROOT / "work" / "audio" / "candidates" / "world"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
WORLD_SOUNDS = PROJECT_ROOT / "docs" / "sound" / "WORLD-SOUNDS.md"
PRD = PROJECT_ROOT / "docs" / "PRD.md"
IZH_ZS = SRC_DIR / "zscript" / "weapons" / "izh.zs"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "audio"))

import check_pk3  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

try:
    import numpy as np
    import gen_weapon_alts as alts
    import gen_weapon_sfx as gws
    import master_world_sfx as mws
except ImportError:                                    # pragma: no cover
    np = alts = gws = mws = None

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "renders audio: verify.py art")

# --- D125, as ratified (docs/PRD.md) -------------------------------------------------
VERDICT_OK = (
    "SDPLPAIN_w1 SDPLPAIN_w2 SDPLPAIN_w3 SDPLDETH_w1 SDPLDETH_w3 SDPLXDTH_w1 SDPLXDTH_w2 SDPLXDTH_w3 "
    "SDPLOOF_w2 SDPLOOF_w3 SDPLNOWY_w1 SDPLNOWY_w2 SDPLNOWY_w3 SDDOROPN_w1 SDDOROPN_w2 SDDOROPN_w3 "
    "SDDORCLS_w1 SDDORCLS_w2 SDDORCLS_w3 SDBDOPN_w1 SDBDOPN_w2 SDBDOPN_w3 SDBDCLS_w1 SDBDCLS_w2 SDBDCLS_w3 "
    "SDSWTCHN_w1 SDSWTCHN_w2 SDSWTCHN_w3 SDSWTCHX_w1 SDSWTCHX_w2 SDSWTCHX_w3 SDITEMUP_w1 SDITEMUP_w2 "
    "SDITEMUP_w3 SDGETPOW_w1 SDGETPOW_w2 SDGETPOW_w3 SDIZPKP_w1 SDIZPKP_w2 SDPSTART_w1 SDPSTART_w2 "
    "SDPSTART_w3 SDPSTOP_w1 SDPSTOP_w2 SDPSTOP_w3 SDPMOVE_w1 SDPMOVE_w2 SDPMOVE_w3 SDTELEPT_w1 SDTELEPT_w2"
).split()
VERDICT_NO = ("SDPLDETH_w2", "SDPLJUMP_w1", "SDPLJUMP_w2", "SDIZPKP_w3", "SDTELEPT_w3")
VERDICT_ASKED = "SDPLOOF_w1"           # "?": its voice over w3's impact, as SDSGOOF1
LAYERED = "SDSGOOF1"
# The engine names gzdoom.pk3 g4.14.2 plays them by (filter/game-doomchex/sndinfo.txt)
ENGINE_NAMES = {"doors/dr1_open", "doors/dr1_clos", "doors/dr2_open", "doors/dr2_clos",
                "switches/normbutn", "switches/exitbutn", "misc/i_pkup", "misc/k_pkup", "misc/p_pkup",
                "plats/pt1_strt", "plats/pt1_stop", "plats/pt1_mid", "misc/teleport"}
PLAYER_REFS = {"*pain100", "*pain75", "*pain50", "*pain25", "*death", "*xdeath", "*grunt", "*land", "*usefail"}
KEPT_FREEDOOM_REFS = {"*jump", "*gibbed", "*fist"}
GENDERS = {"male", "female", "other"}
AI_TAKES = {"SDSGPAI2", "SDSGXDT2", "SDSGOOF1"}     # Chatterbox in them (MANIFEST "AI voice")
GIB_TAKES = {"SDSGXDT1", "SDSGXDT2"}               # our SDRRIXDT, i.e. Freedoom's DSSLOP, under them

RANDOM_RE = re.compile(r"^\$random\s+(\S+)\s*\{\s*([^}]*?)\s*\}\s*$")
OGG_MAGIC = b"OggS"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def constant(name: str):
    """A literal constant of master_world_sfx.py, read without importing it."""
    tree = ast.parse(MASTER_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = [node.target] if isinstance(node, ast.AnnAssign) else getattr(node, "targets", [])
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {MASTER_PY.name}")


CARDS = constant("CARDS")
APPROVED = constant("APPROVED")
PINS = constant("INSTALLED_SHA256")
SHORT = constant("SHORT_OF_TARGET")
ALSO = constant("ALSO_PLAYED_AS")
PLAYER = constant("PLAYER_SOUNDS")


def lump_of(card: str, n: int) -> str:
    return f"{CARDS[card][0]}{n}"


def member_of(card: str, n: int) -> str:
    return f"{CARDS[card][1]}/{n}"


EXPECTED = {lump_of(c, n): (c, n) for c, ns in APPROVED.items() for n in ns}


def sndinfo() -> tuple[dict[str, str], dict[str, list[str]], list[list[str]]]:
    lines: dict[str, str] = {}
    groups: dict[str, list[str]] = {}
    aliases: list[list[str]] = []
    for raw in SNDINFO.read_text(encoding="utf-8").splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        m = RANDOM_RE.match(line)
        if m:
            assert m.group(1) not in groups, f"{m.group(1)} defined twice"
            groups[m.group(1)] = m.group(2).split()
        elif line.startswith("$playeralias"):
            aliases.append(line.split()[1:])
        elif not line.startswith("$"):
            logical, lump = line.split()
            assert logical not in lines, f"{logical} defined twice"
            lines[logical] = lump
    return lines, groups, aliases


# --- Contract -------------------------------------------------------------------------

class ContractTests(unittest.TestCase):
    def test_the_tool_installs_the_verdict(self):
        approved = {f"{c}_w{n}" for c, ns in APPROVED.items() for n in ns}
        self.assertEqual(approved - {VERDICT_ASKED}, set(VERDICT_OK))
        self.assertIn(VERDICT_ASKED, approved)
        self.assertFalse(approved & set(VERDICT_NO))
        self.assertEqual(lump_of("SDPLOOF", 1), LAYERED)
        self.assertEqual(constant("LAYERED"), LAYERED)
        self.assertEqual(len(EXPECTED), 51)
        self.assertEqual(set(PINS), set(EXPECTED))

    def test_the_rejected_and_the_jump(self):
        rejected = {f"{c}_w{n}" for c, ns in constant("REJECTED").items() for n in ns}
        self.assertEqual(rejected, set(VERDICT_NO))
        self.assertNotIn("SDPLJUMP", CARDS)

    def test_lump_names_fit_and_end_in_the_take(self):
        for lump, (card, n) in EXPECTED.items():
            self.assertRegex(lump, r"^SD[A-Z]{5}[1-3]$")
            self.assertTrue(lump.endswith(str(n)), lump)
            if card.startswith("SDPL"):     # SDPL is the Panzermensch shell's sprite prefix
                self.assertEqual(lump[:7], "SDSG" + card[4:7], (card, lump))
            else:
                self.assertTrue(card.startswith(lump[:5]), (card, lump))
            self.assertFalse(lump.startswith("SDPL"), lump)
        self.assertEqual(len({CARDS[c][0] for c in CARDS}), len(CARDS))

    def test_shortfalls_are_installed_lumps(self):
        self.assertLessEqual(set(SHORT), set(EXPECTED))


# --- Files ----------------------------------------------------------------------------

class FileTests(unittest.TestCase):
    def test_exactly_the_51_oggs(self):
        self.assertEqual(sorted(p.name for p in ASSET_DIR.iterdir()), sorted(f"{l}.ogg" for l in EXPECTED))

    def test_each_is_the_installed_file_and_a_vorbis_stream(self):
        for lump, pin in PINS.items():
            with self.subTest(lump):
                data = (ASSET_DIR / f"{lump}.ogg").read_bytes()
                self.assertEqual(sha256(data), pin)
                self.assertTrue(data.startswith(OGG_MAGIC))
                self.assertIn(b"\x01vorbis", data[:64])

    def test_no_card_name_or_rejected_take_ships(self):
        names = {p.stem.upper() for p in (PROJECT_ROOT / "assets").rglob("*.ogg")}
        self.assertFalse(names & set(CARDS) | names & {"SDPLJUMP"})
        for c in VERDICT_NO:
            card, n = c.split("_w")
            if card in CARDS:
                self.assertNotIn(lump_of(card, int(n)), names, c)

    @unittest.skipUnless(CAND_DIR.is_dir(), "work/ not present (CI has no work/)")
    def test_the_oks_are_the_pages_oggs(self):
        for lump, (card, n) in EXPECTED.items():
            with self.subTest(lump):
                same = (ASSET_DIR / f"{lump}.ogg").read_bytes() == (CAND_DIR / f"{card}_w{n}.ogg").read_bytes()
                self.assertEqual(same, lump != LAYERED)


# --- SNDINFO ----------------------------------------------------------------------------

class SndinfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines, cls.groups, cls.aliases = sndinfo()

    def test_every_sound_is_a_group_of_its_takes(self):
        for card, ns in APPROVED.items():
            group = CARDS[card][1]
            with self.subTest(group):
                members = [member_of(card, n) for n in ns]
                self.assertEqual(self.groups.get(group), members)
                self.assertNotIn(group, self.lines)
                for n, m in zip(ns, members):
                    self.assertEqual(self.lines.get(m), lump_of(card, n), m)

    def test_world_groups_sit_on_the_engine_names(self):
        on_engine = {CARDS[c][1] for c in CARDS if not CARDS[c][1].startswith("sd/")} | set(ALSO)
        self.assertEqual(on_engine, ENGINE_NAMES)
        for alias, target in ALSO.items():      # the keys: own members, the item's lumps
            self.assertEqual(self.groups[alias], [m.replace(target, alias, 1) for m in self.groups[target]])
            self.assertEqual([self.lines[m] for m in self.groups[alias]],
                             [self.lines[m] for m in self.groups[target]])

    def test_the_player_aliases(self):
        self.assertEqual(set(PLAYER), PLAYER_REFS)
        got = {(g, ref): target for cls, g, ref, target in self.aliases}
        self.assertEqual({cls for cls, *_ in self.aliases}, {"player"})
        self.assertEqual(set(got), {(g, r) for g in GENDERS for r in PLAYER_REFS})
        for (g, ref), target in got.items():
            self.assertEqual(target, PLAYER[ref], (g, ref))
            self.assertIn(target, self.groups)
        self.assertEqual(got[("male", "*land")], got[("male", "*grunt")])   # one oof on a hard landing
        self.assertFalse(KEPT_FREEDOOM_REFS & {r for _, r in got})
        self.assertNotRegex(SNDINFO.read_text(encoding="utf-8"), r"(?m)^\s*\$playersound\b")

    def test_every_member_is_a_packed_lump(self):
        names = {p.stem.upper() for p in ASSET_DIR.glob("*.ogg")}
        for card in CARDS:
            for m in self.groups[CARDS[card][1]]:
                self.assertIn(self.lines[m], names, m)

    def test_the_tool_block_is_in_sndinfo(self):
        if mws is None:
            self.skipTest("numpy is not installed: the tool is not importable")
        text = SNDINFO.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertIn(mws.sndinfo_block(), text)

    def test_the_izh_plays_its_pickup(self):
        code = re.sub(r"//[^\n]*", "", IZH_ZS.read_text(encoding="utf-8"))
        self.assertIn('Inventory.PickupSound "sd/weapon/izh/pickup";', code)


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

    def test_packed_flat_under_sounds(self):
        for lump in EXPECTED:
            self.assertIn(f"sounds/{lump}.ogg", self.names)

    def test_check_pk3_passes(self):
        report = check_pk3.check_pk3(self.pk3)
        self.assertEqual([f.render() for f in report.errors], [])


# --- Documents ------------------------------------------------------------------------------

def licence_row(text: str, lump: str) -> str:
    m = re.search(rf"(?m)^\| `{lump}` \|.*$", text)
    assert m, lump
    return m.group(0)


class DocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = LICENSES.read_text(encoding="utf-8")
        cls.section = text[text.index("## World sounds"):]
        cls.section = cls.section[:cls.section.index("\n## ", 1)]

    def test_a_licence_row_per_lump(self):
        for lump in EXPECTED:
            self.assertRegex(self.section, rf"(?m)^\| `{lump}` \|", lump)

    def test_ai_rows_name_chatterbox_and_gib_rows_credit_freedoom(self):
        for lump in EXPECTED:
            row = licence_row(self.section, lump)
            self.assertEqual("Chatterbox" in row, lump in AI_TAKES, lump)
            if lump in GIB_TAKES:
                self.assertIn('credit "Freedoom"', row)
                self.assertIn("DSSLOP", row)

    def test_the_verdict_is_quoted(self):
        for path in (LICENSES, PRD, WORLD_SOUNDS):
            text = path.read_text(encoding="utf-8")
            self.assertIn("«El audio está bien pero no tiene el ruido, yo dejaría los 2 audios a la vez»", text,
                          path.name)
            self.assertIn(", ".join(VERDICT_OK), text, path.name)
        self.assertRegex(PRD.read_text(encoding="utf-8"), r"(?m)^\| D125 \| 2026-10-23 \|")

    def test_world_sounds_records_the_install(self):
        text = WORLD_SOUNDS.read_text(encoding="utf-8")
        for lump, pin in PINS.items():
            self.assertIn(f"`{lump}`", text, lump)
            self.assertIn(pin, text, lump)


# --- Loudness (numpy + ffmpeg) ------------------------------------------------------------------

@needs_numpy
class LoudnessTests(unittest.TestCase):
    def test_in_window_or_at_the_pinned_shortfall(self):
        if gws.ffmpeg_path() is None:
            self.skipTest("ffmpeg is not on the PATH")
        for t in mws.TAKES:
            with self.subTest(t.lump):
                mws.check(t, (ASSET_DIR / f"{t.lump}.ogg").read_bytes())    # raises if out


@needs_numpy
@slow
class LayeredTests(unittest.TestCase):
    def test_sdploof1_re_renders_byte_for_byte(self):
        if gws.ffmpeg_path() is None or not CAND_DIR.is_dir():
            self.skipTest("ffmpeg or work/ missing")
        try:
            _, ogg = mws.render_layered()
        except Exception as e:                       # gen_world_sfx.Missing: a source not on disk
            self.skipTest(f"cannot render: {e}")
        self.assertEqual(sha256(ogg), PINS[LAYERED])


if __name__ == "__main__":
    unittest.main()
