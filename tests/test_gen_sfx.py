"""Tests for tools/audio/gen_sfx.py: the bestiary's draft sound effects.

What is tested:

- The contract: the 35 recipes plus the 12 postponed voices (D37) are exactly
  the 47 final lumps `src/lumps/SNDINFO` names in its comments, every one has
  a card in `docs/sound/ENEMY-SOUNDS.md`, beds exist only for voice lumps,
  and the only packs the script can read are the five D36 authorised.
- The DSP the drafts rely on: the limiter never passes the ceiling, the
  loudness normaliser reaches its class target, a bed keeps its head, the
  DMX/WAD readers, the brief features.
- The purely synthetic recipes (route C, and the C beds): they build with no
  pack and no IWAD at all (so they really are ours), deterministically, inside
  their card's length, under -1 dBFS, at their class loudness.
- The cards' words as numbers (`gen_sfx.features`): the Panzermensch's step
  mostly under 300 Hz, the Stormtrooper's bolt impact with no boom, the three
  projectiles in the order the bestiary asks for, the hound's sight carrying
  1-3 kHz with a fast attack, the Doughboy's death ending on its thud, the
  Legion's radio beds band-limited.
- The audition overlay: SNDINFO first, `sounds/<LUMP>.ogg`, fixed zip date,
  byte-reproducible, never a voice or a bed. The preview page embeds every
  file it lists. `build()` writes only where it is told.

The recipes that layer CC0 material need `ffmpeg` and the gitignored
`work/audio/sfx_sources/` (and the gibs `iwads/freedoom2.wad`); they skip when
those are absent (CI has none of them) and under SD_SKIP_SLOW_ART=1 (the
`fast` tier of tools/verify.py), because decoding the packs takes ~15 s.
Everything is skipped without numpy (CI's system python has none). Nothing is
written under `work/`: a tripwire hashes the real output before and after.

These are instruments, not ears: a draft can pass all of them and still be
wrong. The verdict is the CEO's (docs/sound/ENEMY-SOUNDS.md).

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_sfx -v
"""

from __future__ import annotations

import hashlib
import inspect
import io
import os
import re
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    import numpy as np
    import gen_sfx as gs
except ImportError:                                    # pragma: no cover
    np = None
    gs = None

from sdbuild.wad import validate_lump_name  # noqa: E402

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")

SNDINFO = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"
PLAN = PROJECT_ROOT / "docs" / "sound" / "ENEMY-SOUNDS.md"
REAL_OUT = PROJECT_ROOT / "work" / "audio" / "sfx" / "enemies"
REAL_PK3 = PROJECT_ROOT / "work" / "audio" / "sfx" / "sd-enemy-sfx-draft.pk3"
SOURCES = PROJECT_ROOT / "work" / "audio" / "sfx_sources"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"

AUTHORISED_PACKS = {"OGA-CRE1", "OGA-CRE2", "OGA-SNARL", "OGA-100", "KEN-IMP"}   # D36
HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
HAVE_SOURCES = HAVE_FFMPEG and SOURCES.is_dir()
SLOW_SKIPPED = bool(os.environ.get("SD_SKIP_SLOW_ART"))

needs_sources = unittest.skipUnless(
    HAVE_SOURCES and not SLOW_SKIPPED,
    "needs ffmpeg and work/audio/sfx_sources/ (gitignored), and not SD_SKIP_SLOW_ART")
needs_ffmpeg = unittest.skipUnless(HAVE_FFMPEG and not SLOW_SKIPPED,
                                   "needs ffmpeg, and not SD_SKIP_SLOW_ART")

# Under SD_SKIP_SLOW_ART (verify.py fast) only these synthetic drafts are
# rendered (~1 s instead of ~4 s); the rest of their checks skip.
FAST_SYNTHETIC = ("SDRRIATK", "SDLTRATK", "SDSTOMIS", "SDSTOEXP", "SDPZRMIS", "SDPZREXP",
                  "SDPZRSTP", "SDLTRSIT-bed")
FAST_DETERMINISM = ("SDRRIATK", "SDPZRSTP")
FULL_DETERMINISM = ("SDRRIATK", "SDPZRSTP", "SDLTRDTH-bed", "SDDGBDTH")

CEILING = 10 ** (-1.0 / 20)                  # gen_sfx.CEILING_DBFS
LOUDNESS_TOLERANCE_DB = 0.5

# The briefs (ENEMY-SOUNDS.md section 5), turned into thresholds.
STEP_MAX_S = 0.5                     # SDPZRSTP: "< 0.5 s"
STEP_MIN_LOW300 = 0.75               # "mostly < 300 Hz"
STEP_MAX_ONSET_S = 0.02              # "short and dry"
BOLT_IMPACT_MAX_SUB150 = 0.05        # SDSTOEXP: "no boom"
PANZER_IMPACT_MIN_SUB150 = 0.5       # SDPZREXP: "a dull heavy boom"
CRACK_MAX_ONSET_S = 0.01             # SDRRIATK: a crack, no lead-in
CRACK_MIN_CENTROID_HZ = 2000.0       # "dry ... higher"
HOUND_SIGHT_MIN_S = 1.0              # SDHNDSIT: ">= 1 s"
HOUND_SIGHT_MIN_MID = 0.40           # "strong 1-3 kHz"
HOUND_SIGHT_MAX_ONSET_S = 0.35       # "a ~0.3 s attack"
RADIO_BED_MAX_LOW300 = 0.05          # LEGION-RADIO: band-pass 400-3200 Hz
DOUGHBOY_THUD_SHARE = 0.75           # SDDGBDTH: the loudest moment is in the last quarter


def tree_digest(paths) -> str:
    h = hashlib.sha256()
    for root in paths:
        files = sorted(root.rglob("*")) if root.is_dir() else [root]
        for p in files:
            if p.is_file():
                h.update(str(p).encode())
                h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


_BEFORE = ""


def setUpModule():
    global _BEFORE
    _BEFORE = tree_digest([REAL_OUT, REAL_PK3])


def tearDownModule():
    if tree_digest([REAL_OUT, REAL_PK3]) != _BEFORE:
        raise AssertionError("tests/test_gen_sfx.py changed the real output under work/")


def sndinfo_final_lumps() -> set[str]:
    """The 47 cards SNDINFO's sd/mon/ names stand for: the `// -> SD...`
    comment of a line still on a Freedoom stand-in; the lump itself of a line
    installed by N9e; and, for a `$random` alias over several approved takes
    (D86), its card (the members' lump SDxxxAT1 is the card SDxxxATK with the
    take digit for its last letter)."""
    out, members, firsts = set(), set(), []
    raw_lines = SNDINFO.read_text(encoding="utf-8").splitlines()
    for raw in raw_lines:
        m = re.match(r"^\$random\s+sd/mon/\S+\s*\{\s*([^}]*?)\s*\}$", raw.split("//")[0].strip())
        if m:
            names = m.group(1).split()
            members |= set(names)
            firsts.append(names[0])
    lump_of = {}
    for raw in raw_lines:
        m = re.match(r"^(sd/mon/\S+)\s+(\S+)\s*(?://\s*->\s*(SD[A-Z0-9]{6})\b)?", raw.strip())
        if not m:
            continue
        lump_of[m.group(1)] = m.group(2)
        if m.group(1) not in members:
            out.add(m.group(3) or m.group(2))
    cards = set(gs.RECIPES) | set(gs.VOICE_LUMPS) if gs is not None else set()
    for first in firsts:
        out |= {c for c in cards if c[:7] == lump_of[first][:7]}
    return out


def recipe_packs(fn) -> set[str]:
    """Pack IDs a recipe's source text names in ctx.src(...) calls."""
    return set(re.findall(r'ctx\.src\("([A-Z0-9-]+)"', inspect.getsource(fn)))


def synthetic_names() -> list[str]:
    """Lumps and beds whose recipe reads no pack and no IWAD."""
    out = []
    for name in gs.all_names():
        src = inspect.getsource(gs.recipe_of(name).build)
        if "ctx.src(" not in src and "ctx.freedoom(" not in src:
            out.append(name)
    return out


# --- Contract -------------------------------------------------------------------

@needs_numpy
class ContractTest(unittest.TestCase):

    def test_recipes_and_voices_are_the_47_sndinfo_lumps(self):
        recipes, voices = set(gs.RECIPES), set(gs.VOICE_LUMPS)
        self.assertEqual(len(recipes), 35)
        self.assertEqual(len(voices), 12)
        self.assertFalse(recipes & voices, "a voice lump has a recipe: voices are the CEO's (D37)")
        self.assertEqual(recipes | voices, sndinfo_final_lumps())

    def test_lump_names_are_legal_and_follow_the_bestiary_rule(self):
        for lump in list(gs.RECIPES) + list(gs.VOICE_LUMPS):
            with self.subTest(lump=lump):
                self.assertEqual(validate_lump_name(lump), lump)
                self.assertRegex(lump, r"^SD(RRI|LTR|STO|HND|DGB|PZR|GEN)[A-Z]{3}$")

    def test_every_lump_has_a_card_in_the_plan(self):
        plan = PLAN.read_text(encoding="utf-8")
        for lump in list(gs.RECIPES) + list(gs.VOICE_LUMPS):
            with self.subTest(lump=lump):
                self.assertIn(f"| `{lump}` |", plan)

    def test_beds_exist_only_for_voice_lumps(self):
        self.assertTrue(gs.BEDS)
        self.assertLessEqual(set(gs.BEDS), set(gs.VOICE_LUMPS))
        with self.assertRaises(ValueError):
            gs.bed("SDHNDSIT", "C", (0.1, 0.2), "not a voice")

    def test_only_the_five_authorised_packs(self):
        self.assertEqual(set(gs.PACK_DIRS), AUTHORISED_PACKS)
        for name in gs.all_names():
            with self.subTest(name=name):
                self.assertLessEqual(recipe_packs(gs.recipe_of(name).build), AUTHORISED_PACKS)

    def test_hound_uses_no_dog_or_wolf_recording(self):
        # ENEMY-SOUNDS.md 5.4: "not a dog and not a wolf": Barking and Howl unused.
        for lump in (x for x in gs.RECIPES if x.startswith("SDHND")):
            src = inspect.getsource(gs.RECIPES[lump].build).lower()
            self.assertNotIn("bark", src, lump)
            self.assertNotIn("howl", src, lump)

    def test_routes_match_what_the_recipe_reads(self):
        for name in gs.all_names():
            rec = gs.recipe_of(name)
            src = inspect.getsource(rec.build)
            with self.subTest(name=name, route=rec.route):
                self.assertEqual("B" in rec.route, "ctx.src(" in src)
                self.assertEqual("A" in rec.route, "ctx.freedoom(" in src)
                self.assertIn("C", rec.route)          # nothing ships unlayered (ENEMY-SOUNDS.md 2)

    def test_names_round_trip(self):
        self.assertEqual(gs.normalise_name("sdrridth-bed"), "SDRRIDTH-bed")
        self.assertEqual(gs.normalise_name(" sdhndsit "), "SDHNDSIT")
        for name in gs.all_names():
            self.assertIs(gs.recipe_of(gs.normalise_name(name.lower())), gs.recipe_of(name))

    def test_sndinfo_rows_name_the_freedoom_stand_ins(self):
        # Only lines still on a Freedoom stand-in carry `// -> SD...` (N9e
        # installed the hound's sight and the step; D91, D96 and D110 eleven of
        # the twelve voices; the General's death still waits, D110).
        rows = gs.sndinfo_rows(SNDINFO)
        self.assertEqual(rows["SDGENDTH"], ("sd/mon/general/death", "DSCYBDTH"))
        for ours in ("SDRRIACT", "SDRRISIT", "SDGENSUM", "SDHNDSIT",     # $random or ours since N9e
                     "SDRRIPAI", "SDLTRDTH", "SDGENPAI"):                 # $random since D110
            self.assertNotIn(ours, rows)
        self.assertEqual(set(rows), {"SDGENDTH"})


# --- DSP --------------------------------------------------------------------------

@needs_numpy
class DspTest(unittest.TestCase):

    def setUp(self):
        self.rng = np.random.default_rng(5)

    def test_limiter_never_passes_the_ceiling(self):
        x = self.rng.standard_normal(gs.n_of(0.5)) * 3.0
        y, reduction = gs.limit(x, CEILING)
        self.assertLessEqual(np.abs(y).max(), CEILING + 1e-12)
        self.assertGreater(reduction, 0.0)
        quiet = x * 0.01
        same, none = gs.limit(quiet, CEILING)
        self.assertIs(same, quiet)
        self.assertEqual(none, 0.0)

    def test_finish_reaches_the_class_target(self):
        x = gs.bandpass(self.rng.standard_normal(gs.n_of(0.6)), 300, 3000) * 0.01
        done = gs.finish(x, "creature")
        self.assertAlmostEqual(done.loudness_db, gs.LOUDNESS_DB["creature"], delta=LOUDNESS_TOLERANCE_DB)
        self.assertLessEqual(np.abs(done.samples).max(), CEILING + 1e-12)

    def test_loudness_tracks_gain(self):
        x = np.sin(2 * np.pi * 1000 * gs.time_axis(gs.n_of(0.3))) * 0.1
        self.assertAlmostEqual(gs.weighted_loudness_db(2 * x) - gs.weighted_loudness_db(x),
                               20 * np.log10(2), places=6)

    def test_a_bed_keeps_its_head(self):
        x = np.concatenate([np.zeros(gs.n_of(0.4)), self.rng.standard_normal(gs.n_of(0.2)), np.zeros(500)])
        kept = gs.finish(x, "bed", keep_head=True).samples
        trimmed = gs.finish(x, "bed").samples
        self.assertLess(np.abs(kept[:gs.n_of(0.3)]).max(), 1e-3)
        # trim_silence keeps a 3 ms preroll and the zero-phase high-pass rings a
        # little ahead of the onset, so the difference is 0.4 s minus ~15 ms.
        self.assertAlmostEqual(kept.size - trimmed.size, gs.n_of(0.4), delta=gs.n_of(0.02))

    def test_from_onset_drops_a_slow_lead_in(self):
        x = np.concatenate([np.linspace(0, 0.05, gs.n_of(0.2)), np.ones(gs.n_of(0.1))])
        self.assertLess(gs.from_onset(x, -12.0).size, gs.n_of(0.15))

    def test_varispeed_octave(self):
        x = self.rng.standard_normal(4410)
        self.assertAlmostEqual(gs.varispeed(x, -12).size, 2 * x.size, delta=3)
        self.assertAlmostEqual(gs.varispeed(x, 12).size, x.size / 2, delta=3)

    def test_features_of_pure_tones(self):
        n = gs.n_of(0.5)
        low = gs.features(np.sin(2 * np.pi * 100 * gs.time_axis(n)))
        mid = gs.features(np.sin(2 * np.pi * 2000 * gs.time_axis(n)))
        self.assertGreater(low["low300"], 0.99)
        self.assertGreater(low["sub150"], 0.99)
        self.assertGreater(mid["mid1_3k"], 0.99)
        self.assertAlmostEqual(mid["centroid_hz"], 2000, delta=20)
        ramp = np.sin(2 * np.pi * 500 * gs.time_axis(n)) * np.linspace(0, 1, n)
        self.assertAlmostEqual(gs.features(ramp)["onset_s"], 0.25, delta=0.02)

    def test_dmx_and_wad_readers(self):
        body = bytes(range(100, 140))
        lump = struct.pack("<HHI", gs.DMX_FORMAT, 11025, len(body) + 2 * gs.DMX_PAD) \
            + bytes([128]) * gs.DMX_PAD + body + bytes([128]) * gs.DMX_PAD
        x, rate = gs.dmx_to_float(lump)
        self.assertEqual(rate, 11025)
        self.assertEqual(x.size, len(body))
        self.assertAlmostEqual(x[0], (100 - 128) / 128)
        with self.assertRaises(ValueError):
            gs.dmx_to_float(struct.pack("<HHI", 1, 11025, 0) + bytes(40))
        with tempfile.TemporaryDirectory() as tmp:
            wad = Path(tmp) / "t.wad"
            directory_at = 12 + len(lump)
            wad.write_bytes(b"IWAD" + struct.pack("<II", 1, directory_at) + lump
                            + struct.pack("<II8s", 12, len(lump), b"DSSLOP"))
            self.assertEqual(gs.wad_lump(wad, "DSSLOP"), lump)
            with self.assertRaises(gs.SourceMissing):
                gs.wad_lump(wad, "DSNOPE")
            with self.assertRaises(gs.SourceMissing):
                gs.wad_lump(Path(tmp) / "absent.wad", "DSSLOP")


# --- Synthetic recipes: no pack, no IWAD ------------------------------------------

@needs_numpy
class SyntheticTest(unittest.TestCase):
    """Rendered once with the sources pointed at an empty directory: if a
    recipe here reached for a pack it would raise SourceMissing."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        empty = Path(cls.tmp.name)
        cls.names = synthetic_names()
        built = FAST_SYNTHETIC if SLOW_SKIPPED else cls.names
        cls.r = {n: gs.render(n, gs.DEFAULT_SEED, empty, empty / "no.wad") for n in built}
        cls.f = {n: gs.features(r.samples) for n, r in cls.r.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def need(self, *names):
        missing = [n for n in names if n not in self.r]
        if missing:
            self.skipTest(f"not rendered under SD_SKIP_SLOW_ART: {', '.join(missing)}")

    def test_the_synthetic_set_is_the_route_c_set(self):
        expected = {n for n in gs.all_names() if gs.recipe_of(n).route == "C"}
        self.assertEqual(set(self.names), expected)
        self.assertGreaterEqual(len(self.names), 15)

    def test_no_sources_recorded(self):
        for n, r in self.r.items():
            with self.subTest(name=n):
                self.assertEqual(r.refs, [])
                self.assertTrue(r.synth)
                self.assertEqual(r.provenance(), ["SYN gen_sfx.py"])

    def test_deterministic_and_seeded(self):
        empty = Path(self.tmp.name)
        for n in FAST_DETERMINISM if SLOW_SKIPPED else FULL_DETERMINISM:
            with self.subTest(name=n):
                again = gs.render(n, gs.DEFAULT_SEED, empty, empty)
                self.assertTrue(np.array_equal(again.samples, self.r[n].samples))
                other = gs.render(n, gs.DEFAULT_SEED + 1, empty, empty)
                self.assertFalse(np.array_equal(other.samples, self.r[n].samples))

    def test_length_peak_and_loudness(self):
        for n, r in self.r.items():
            lo, hi = r.recipe.duration
            with self.subTest(name=n):
                self.assertGreaterEqual(r.seconds, lo)
                self.assertLessEqual(r.seconds, hi)
                self.assertLessEqual(np.abs(r.samples).max(), CEILING + 1e-12)
                target = gs.LOUDNESS_DB[r.recipe.loud_class]
                if r.limited_db < gs.MAX_LIMIT_DB - 0.01:
                    self.assertAlmostEqual(r.loudness_db, target, delta=LOUDNESS_TOLERANCE_DB)
                else:                                   # held back rather than squashed
                    self.assertLess(r.loudness_db, target)

    def test_panzermensch_step(self):
        r, f = self.r["SDPZRSTP"], self.f["SDPZRSTP"]
        self.assertLess(r.seconds, STEP_MAX_S)
        self.assertGreaterEqual(f["low300"], STEP_MIN_LOW300)
        self.assertLessEqual(f["onset_s"], STEP_MAX_ONSET_S)

    def test_bolt_impact_has_no_boom_and_the_panzer_shell_does(self):
        self.assertLessEqual(self.f["SDSTOEXP"]["sub150"], BOLT_IMPACT_MAX_SUB150)
        self.assertGreaterEqual(self.f["SDPZREXP"]["sub150"], PANZER_IMPACT_MIN_SUB150)

    def test_stormtrooper_bolt_is_brighter_and_shorter_than_the_panzer_lob(self):
        self.assertGreater(self.f["SDSTOMIS"]["centroid_hz"], self.f["SDPZRMIS"]["centroid_hz"])
        self.assertLess(self.r["SDSTOMIS"].seconds, self.r["SDPZRMIS"].seconds)

    def test_rifleman_crack_is_dry_and_bright(self):
        f = self.f["SDRRIATK"]
        self.assertLessEqual(f["onset_s"], CRACK_MAX_ONSET_S)
        self.assertGreaterEqual(f["centroid_hz"], CRACK_MIN_CENTROID_HZ)
        self.assertGreater(f["centroid_hz"], self.f["SDLTRATK"]["centroid_hz"])

    def test_doughboy_death_ends_on_its_thud(self):
        self.need("SDDGBDTH")
        x = self.r["SDDGBDTH"].samples
        blk = gs.n_of(0.01)
        rms = np.sqrt((x[:x.size // blk * blk].reshape(-1, blk) ** 2).mean(axis=1))
        self.assertGreaterEqual(np.argmax(rms) / rms.size, DOUGHBOY_THUD_SHARE)

    def test_legion_radio_beds_are_band_limited_and_framed(self):
        for n in ("SDLTRACT-bed", "SDLTRSIT-bed"):
            if n not in self.r:
                continue
            with self.subTest(name=n):
                self.assertLessEqual(self.f[n]["low300"], RADIO_BED_MAX_LOW300)
                x = self.r[n].samples
                tail = np.abs(x[-gs.n_of(0.1):]).max()
                self.assertGreater(tail, 0.1 * np.abs(x).max(), "the squelch must close at the end")


# --- Sourced recipes (CC0 packs, Freedoom) -----------------------------------------

@needs_numpy
@needs_sources
class SourcedTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        names = [n for n in gs.all_names() if n not in synthetic_names()]
        if not IWAD.is_file():
            names = [n for n in names if "A" not in gs.recipe_of(n).route]
        cls.r = {n: gs.render(n) for n in names}
        cls.f = {n: gs.features(r.samples) for n, r in cls.r.items()}

    def test_every_sourced_draft_builds_inside_its_card(self):
        for n, r in self.r.items():
            lo, hi = r.recipe.duration
            with self.subTest(name=n):
                self.assertGreaterEqual(r.seconds, lo)
                self.assertLessEqual(r.seconds, hi)
                self.assertLessEqual(np.abs(r.samples).max(), CEILING + 1e-12)

    def test_provenance_is_recorded_and_authorised(self):
        for n, r in self.r.items():
            with self.subTest(name=n):
                self.assertTrue(r.refs)
                self.assertTrue(r.synth, "route C layer missing")
                for ref in r.refs:
                    self.assertIn(ref.pack, AUTHORISED_PACKS | {gs.FREEDOOM_PACK})
                    self.assertRegex(ref.sha256, r"^[0-9a-f]{64}$")
                    if ref.pack == gs.FREEDOOM_PACK:
                        self.assertEqual(ref.name, "freedoom2.wad:DSSLOP")

    def test_hound_sight_carries_through_a_door(self):
        r, f = self.r["SDHNDSIT"], self.f["SDHNDSIT"]
        self.assertGreaterEqual(r.seconds, HOUND_SIGHT_MIN_S)
        self.assertGreaterEqual(f["mid1_3k"], HOUND_SIGHT_MIN_MID)
        self.assertLessEqual(f["onset_s"], HOUND_SIGHT_MAX_ONSET_S)

    def test_three_projectiles_in_the_bestiary_order(self):
        # Doughboy: "lower, longer and wetter than the Stormtrooper's zap";
        # Panzermensch: "heavier and slower than the Stormtrooper's bolt".
        empty = Path(tempfile.gettempdir()) / "gen_sfx_no_sources"
        sto, pzr = (gs.render(n, gs.DEFAULT_SEED, empty, empty) for n in ("SDSTOMIS", "SDPZRMIS"))
        dgb = self.r["SDDGBMIS"]
        c = {k: gs.features(v.samples)["centroid_hz"] for k, v in (("sto", sto), ("dgb", dgb), ("pzr", pzr))}
        self.assertGreater(c["sto"], c["dgb"])
        self.assertGreater(c["dgb"], c["pzr"])
        self.assertLess(sto.seconds, dgb.seconds)
        self.assertLess(dgb.seconds, pzr.seconds)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not here (gitignored)")
    def test_gibs_are_freedoom_slop_plus_our_thump(self):
        for lump in ("SDRRIXDT", "SDLTRXDT", "SDSTOXDT"):
            with self.subTest(lump=lump):
                self.assertEqual([ref.pack for ref in self.r[lump].refs], [gs.FREEDOOM_PACK])


# --- Overlay, preview, writing ----------------------------------------------------

@needs_numpy
class OverlayTest(unittest.TestCase):

    def test_overlay_layout_reproducible_and_without_voices_or_beds(self):
        # the hound's sight is a $random group since D107: a single-line draft instead
        lumps = ["SDSTOSIT", "SDPZRSTP"]
        with tempfile.TemporaryDirectory() as tmp:
            ogg_dir = Path(tmp)
            for lump in lumps:
                (ogg_dir / f"{lump}.ogg").write_bytes(lump.encode() * 10)
            a = gs.pack_overlay(lumps + ["SDRRIDTH-bed"], ogg_dir, ogg_dir / "a.pk3", SNDINFO)
            b = gs.pack_overlay(lumps, ogg_dir, ogg_dir / "b.pk3", SNDINFO)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as zf:
                self.assertEqual(zf.namelist(), ["SNDINFO", "sounds/SDSTOSIT.ogg", "sounds/SDPZRSTP.ogg"])
                self.assertTrue(all(i.date_time == gs.FIXED_ZIP_TIME for i in zf.infolist()))
                text = zf.read("SNDINFO").decode("ascii")
            self.assertRegex(text, r"(?m)^sd/mon/stormtrooper/sight\s+SDSTOSIT$")
            self.assertRegex(text, r"(?m)^sd/mon/panzermensch/step\s+SDPZRSTP$")
            no_names = Path(tmp) / "SNDINFO"
            no_names.write_text("// nothing", encoding="utf-8")
            with self.assertRaises(SystemExit):
                gs.pack_overlay(["SDSTOSIT"], ogg_dir, ogg_dir / "c.pk3", no_names)

    def test_main_lists_and_rejects(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(gs.main(["--list"]), 0)
        self.assertEqual(len(out.getvalue().splitlines()), len(gs.all_names()) + 1)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(gs.main(["--only", "SDRRISIT"]), 2)          # a voice: no recipe
            self.assertEqual(gs.main(["--only", "SDPZRSTP", "--preview", "x.html"]), 2)

    @needs_ffmpeg
    def test_build_writes_only_where_told_and_the_preview_embeds_every_file(self):
        names = ["SDPZRSTP", "SDSTOEXP", "SDLTRSIT-bed"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "enemies"
            pk3 = Path(tmp) / "draft.pk3"
            rendered = gs.build(names, quiet=True, out_dir=out, pk3=pk3)
            for n in names:
                wav, ogg = gs.paths_of(n, out)
                self.assertTrue(wav.is_file() and ogg.is_file(), n)
            self.assertTrue((out / "PROVENANCE.tsv").is_file())
            self.assertIn("SDLTRSIT-bed", (out / "REPORT.txt").read_text(encoding="utf-8"))
            with zipfile.ZipFile(pk3) as zf:
                self.assertNotIn("sounds/SDLTRSIT-bed.ogg", zf.namelist())
            rows = [gs.measure(n, out) for n in names]
            for row in rows:
                self.assertLess(row["ogg_peak"], gs.CLIP_THRESHOLD)
            page = gs.preview_html(rendered, rows, gs.DEFAULT_SEED, "test", out, SNDINFO)
            self.assertEqual(page.count('src="data:audio/ogg;base64,'), len(names))
            for n in names:
                self.assertIn(f"<code>{n}</code>", page)
            # N9e installed both lumps: the page names their logical names.
            self.assertIn("<code>sd/mon/panzermensch/step</code><br>installed (N9e)", page)
            self.assertIn("SYN gen_sfx.py", page)


if __name__ == "__main__":
    unittest.main()
