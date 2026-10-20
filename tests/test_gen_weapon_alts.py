"""Tests for tools/audio/gen_weapon_alts.py: alternatives for the five weapon
sounds the CEO did not approve on the M3 listening sheet (D74).

What is tested:

- The contract: exactly the five lumps of D74 (NO: SDTTPKP, SDIZRLD,
  SDRKFIR; ?: SDAXPKP, SDIZPKP), three alternatives each, each its own
  recipe and none a recipe of the rejected drafts; the Freedoom lump each
  is levelled against is the one SNDINFO maps it to today.
- Provenance (WEAPON-SOUNDS §2): only files of the two CC0 packs already on
  disk (OGA-100, KEN-IMP), never a `shot_*` file, every file's SHA-256
  pinned, no dead entries; the jet is synthesis only.
- The engine facts the jet is cut to: roks3.zs restarts the fire sound every
  3 tics on CHAN_WEAPON, so the first 3780 samples are one period and the
  restart joins the period's end to its start.
- Levels (D74, N9): peak at -1 dBFS; the loudest 50 ms (A-weighted) within
  1 dB of its target, which is the Freedoom lump's own minus a fixed
  allowance; the Freedoom levels re-measured from the IWAD; at least half
  of the energy above 300 Hz (laptop speakers).
- The IZh break-open still snaps shut on frame A (22 tics) and fits 30 tics.
- The limiter never passes its ceiling; the held-trigger preview restarts
  every 3 tics and lets the last one play out.
- The listening page: Spanish, OK/NO/? and "Copiar resultado", relative
  paths only, localStorage inside try/catch, the rejected draft and the
  Freedoom sound on every row; the real page's files exist.
- Determinism: two renders are byte-identical.

The jet is synthesis, so its tests always run (numpy needed). The twelve
foley alternatives need ffmpeg and the gitignored work/audio/sfx_sources/;
they skip without them, and their full render (~10 s) is skipped with
SD_SKIP_SLOW_ART=1 (`tools/verify.py fast`). Nothing is written under
work/: outputs go to a temporary directory.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_weapon_alts -v
"""

from __future__ import annotations

import io
import os
import re
import sys
import tempfile
import unittest
import wave
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    import numpy as np
    import gen_weapon_sfx as gws
    import gen_weapon_alts as alts
except ImportError:                                    # pragma: no cover
    np = gws = alts = None

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the full render of the foley alternatives")

D74_NO = {"SDTTPKP", "SDIZRLD", "SDRKFIR"}
D74_UNSURE = {"SDAXPKP", "SDIZPKP"}
SNDINFO = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"
ROKS3_ZS = PROJECT_ROOT / "src" / "zscript" / "weapons" / "roks3.zs"
PREVIEWS = PROJECT_ROOT / "docs" / "art" / "previews"
REAL_OUT = PROJECT_ROOT / "work" / "audio" / "alt"
SNAP_WINDOW_S = 0.02


def _have_foley() -> bool:
    if np is None or gws.ffmpeg_path() is None:
        return False
    src = alts.AltSources()
    return all(src.path(k).is_file() for k in alts.ALT_SOURCES)


def _loudest_window_centre(x, window_s: float = SNAP_WINDOW_S) -> float:
    y = alts.a_weighted(x) ** 2
    w = gws.n_of(window_s)
    c = np.concatenate([[0.0], np.cumsum(y)])
    return (int(np.argmax(c[w:] - c[:-w])) + w / 2) / gws.SR


@needs_numpy
class ContractTests(unittest.TestCase):

    def test_exactly_the_five_lumps_of_d74_three_each(self):
        self.assertEqual(set(alts.TARGETS), D74_NO | D74_UNSURE)
        for lump in alts.TARGETS:
            got = sorted(a.index for a in alts.ALTS if a.lump == lump)
            self.assertEqual(got, list(range(1, alts.ALT_COUNT + 1)), lump)
        self.assertEqual(len(alts.ALTS_BY_NAME), len(alts.ALTS))
        for lump, (_, _, _, verdict, _) in alts.TARGETS.items():
            self.assertEqual(verdict, "NO" if lump in D74_NO else "?", lump)

    def test_every_alternative_is_its_own_recipe(self):
        recipes = [a.recipe for a in alts.ALTS]
        self.assertEqual(len(set(recipes)), len(recipes))
        rejected = {lump.recipe for lump in gws.LUMPS}
        for a in alts.ALTS:
            self.assertNotIn(a.recipe, rejected, a.name)
            self.assertTrue(a.label and a.what and a.recipe.__doc__, a.name)
        for lump in alts.TARGETS:
            labels = [a.label for a in alts.ALTS if a.lump == lump]
            self.assertEqual(len(set(labels)), len(labels), lump)
            foley = [frozenset(a.sources) for a in alts.ALTS if a.lump == lump and a.sources]
            self.assertEqual(len(set(foley)), len(foley), f"{lump}: two alternatives share every source")

    def test_kinds_and_the_freedoom_lump_each_replaces(self):
        sndinfo = SNDINFO.read_text(encoding="utf-8")
        for lump, (ref, *_rest) in alts.TARGETS.items():
            self.assertIn(ref, alts.FREEDOOM_LEVELS, lump)
            logical = gws.LUMPS_BY_NAME[lump].logical
            m = re.search(rf"^{re.escape(logical)}\s+(\S+)", sndinfo, re.M)
            group = re.search(rf"^\$random\s+{re.escape(logical)}\s", sndinfo, re.M)
            if m and m.group(1).startswith("DS"):   # wired today: the stand-in is the reference
                self.assertEqual(m.group(1), ref, lump)
            elif (m and m.group(1) == lump) or group:   # installed by N9e (D94): ref is what it replaced
                self.assertIn(ref, ("DSWPNUP", "DSSGCOCK", "DSFLAME"), lump)
            else:     # pickups: Doom's generic weapon pickup (MOD-SPEC, WEAPON-SOUNDS §6)
                self.assertEqual(ref, "DSWPNUP", lump)
        kinds = {a.lump: a.kind for a in alts.ALTS}
        self.assertEqual(kinds["SDRKFIR"], "fire")
        self.assertEqual(kinds["SDIZRLD"], "reload")
        for lump in ("SDTTPKP", "SDAXPKP", "SDIZPKP"):
            self.assertEqual(kinds[lump], "pickup")


@needs_numpy
class ProvenanceTests(unittest.TestCase):

    def test_only_the_cc0_packs_and_never_a_shot(self):
        for key, (pack, rel, digest) in alts.ALT_SOURCES.items():
            self.assertIn(pack, ("OGA-100", "KEN-IMP"), key)
            self.assertNotIn("shot_", rel, key)
            self.assertRegex(digest, r"^[0-9a-f]{64}$", key)

    def test_every_source_is_used_and_known(self):
        used = {k for a in alts.ALTS for k in a.sources}
        self.assertEqual(used, set(alts.ALT_SOURCES))
        for a in alts.ALTS:
            if a.kind == "fire":
                self.assertEqual(a.sources, (), "the jet is synthesis only")

    def test_shared_files_carry_the_hash_weapon_sounds_documents(self):
        for key, (pack, rel, digest) in alts.ALT_SOURCES.items():
            if key in gws.SOURCE_FILES:
                self.assertEqual(gws.SOURCE_FILES[key][1], rel, key)

    def test_source_files_match_their_pinned_sha256(self):
        src = alts.AltSources()
        missing = [k for k in alts.ALT_SOURCES if not src.path(k).is_file()]
        if missing:
            self.skipTest(f"work/audio/sfx_sources/ not on this machine ({len(missing)} missing)")
        for key, (_, _, digest) in alts.ALT_SOURCES.items():
            self.assertEqual(gws.sha256_file(src.path(key)), digest, key)


@needs_numpy
class EngineFactTests(unittest.TestCase):

    def test_roks3_restarts_the_fire_sound_every_three_tics(self):
        zs = ROKS3_ZS.read_text(encoding="utf-8")
        self.assertRegex(zs, rf"SDRK A {alts.ROKS3_TICS_PER_JET} Bright A_SD_FireRoks3;")
        self.assertIn('A_StartSound("sd/weapon/roks3/fire", CHAN_WEAPON);', zs)
        self.assertRegex(zs, r"SDRK B \d+ A_ReFire;")

    def test_three_tics_are_a_whole_number_of_samples(self):
        self.assertEqual(alts.JET_LOOP_N, 3780)
        self.assertEqual(alts.JET_LOOP_N * gws.TICS_PER_SECOND, gws.SR * alts.ROKS3_TICS_PER_JET)


@needs_numpy
class DspTests(unittest.TestCase):

    def test_running_max_matches_brute_force(self):
        rng = np.random.default_rng(1)
        a = rng.uniform(0, 1, 257)
        for k in (1, 2, 7, 16, 257):
            want = np.array([a[i:i + k].max() for i in range(len(a) - k + 1)])
            np.testing.assert_array_equal(alts.running_max(a, k), want)

    def test_limiter_never_passes_its_ceiling(self):
        rng = np.random.default_rng(2)
        x = rng.standard_normal(20000) * np.exp(-np.arange(20000) / 3000)
        x[0] = 4.0                       # a transient on the very first sample
        for ceiling in (2.0, 0.5, 0.05):
            y = alts.limit(x, ceiling)
            self.assertEqual(len(y), len(x))
            self.assertLessEqual(np.max(np.abs(y)), ceiling + 1e-12)
        quiet = x * 1e-3
        np.testing.assert_allclose(alts.limit(quiet, 1.0), quiet)

    def test_held_restarts_every_three_tics_and_plays_the_last_out(self):
        x = np.arange(1, 10001, dtype=float)
        rate = gws.SR
        h = alts.held(x, rate, hold_s=0.5)
        step = alts.JET_LOOP_N
        starts = list(range(0, int(0.5 * rate), step))
        self.assertEqual(len(h), starts[-1] + len(x))
        for s in starts[:-1]:
            np.testing.assert_array_equal(h[s:s + step], x[:step])
        np.testing.assert_array_equal(h[starts[-1]:], x)
        h11 = alts.held(x[:2000], 11025, hold_s=0.5)       # Freedoom's rate: 945 per 3 tics
        self.assertEqual(h11[945], 1.0)

    def test_a_weighting_is_unity_at_one_kilohertz(self):
        self.assertAlmostEqual(20 * np.log10(alts.a_weight(np.array([1000.0]))[0]), 0.0, delta=0.05)
        self.assertLess(alts.a_weight(np.array([100.0]))[0], 0.15)


@needs_numpy
class FreedoomLevelTests(unittest.TestCase):

    def test_freedoom_levels_re_measured_from_the_iwad(self):
        for name, (pk, loud, rms) in alts.FREEDOOM_LEVELS.items():
            wav = gws.placeholder_wav(name)
            if wav is None:
                self.skipTest("iwads/freedoom2.wad is not on this machine")
            x, rate = alts.read_wav(wav)
            lv = alts.levels(x, rate)
            self.assertAlmostEqual(lv["peak"], pk, delta=alts.LEVEL_TOLERANCE_DB, msg=name)
            self.assertAlmostEqual(lv["loud_a"], loud, delta=alts.LEVEL_TOLERANCE_DB, msg=name)
            self.assertAlmostEqual(lv["rms"], rms, delta=alts.LEVEL_TOLERANCE_DB, msg=name)


class _LevelChecks:
    """Shared assertions for one rendered alternative."""

    def check_levels(self, alt, x):
        lv = alts.levels(x)
        self.assertAlmostEqual(lv["peak"], alts.PEAK_DBFS, delta=alts.PEAK_TOLERANCE_DB, msg=alt.name)
        self.assertAlmostEqual(lv["loud_a"], alts.target_db(alt),
                               delta=alts.LOUDNESS_TOLERANCE_DB, msg=alt.name)
        self.assertGreaterEqual(lv["above300"], alts.MIN_SHARE_ABOVE_300HZ, alt.name)
        lo, hi = alt.length_s
        self.assertTrue(lo <= lv["length"] <= hi, f"{alt.name}: {lv['length']:.3f} s")
        self.assertLess(np.max(np.abs(x[-gws.n_of(0.002):])), 0.01, f"{alt.name} ends in silence")
        pcm = gws.wav_bytes(x)
        with wave.open(io.BytesIO(pcm)) as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, gws.SR))


@needs_numpy
class JetTests(unittest.TestCase, _LevelChecks):
    """The flamethrower alternatives: synthesis only, always rendered."""

    @classmethod
    def setUpClass(cls):
        cls.src = alts.AltSources()
        cls.jets = {a.name: (a, alts.render(a, cls.src)[0]) for a in alts.ALTS if a.kind == "fire"}

    def test_three_jets(self):
        self.assertEqual(len(self.jets), alts.ALT_COUNT)

    def test_deterministic(self):
        for name, (a, x) in self.jets.items():
            self.assertEqual(gws.wav_bytes(alts.render(a, self.src)[0]), gws.wav_bytes(x), name)

    def test_levels_band_and_length(self):
        for a, x in self.jets.values():
            self.check_levels(a, x)

    def test_restart_joins_the_period_to_itself(self):
        n = alts.JET_LOOP_N
        for name, (a, x) in self.jets.items():
            loop = x[:n]
            step = np.percentile(np.abs(np.diff(loop)), 99)
            self.assertLessEqual(abs(x[0]), step, f"{name}: the first press starts near zero")
            self.assertLessEqual(abs(loop[0] - loop[-1]), step, f"{name}: the seam is a normal step")
            h = alts.held(x, gws.SR)
            seams = range(n, int(alts.HELD_PREVIEW_S * gws.SR), n)
            for s in seams:
                self.assertLessEqual(abs(h[s] - h[s - 1]), step, f"{name}: restart at {s}")

    def test_the_loop_is_as_loud_as_the_whole(self):
        n = alts.JET_LOOP_N
        for name, (a, x) in self.jets.items():
            held = alts.held(x, gws.SR)[:int(alts.HELD_PREVIEW_S * gws.SR)]
            self.assertAlmostEqual(alts.loud_a_db(held), alts.target_db(a),
                                   delta=alts.LOUDNESS_TOLERANCE_DB + 0.5, msg=name)
            self.assertGreater(len(x), n + gws.n_of(0.1), f"{name}: a release tail after the loop")


@needs_numpy
@slow
class FoleyTests(unittest.TestCase, _LevelChecks):
    """The twelve pickups and break-opens: CC0 foley, ffmpeg needed."""

    @classmethod
    def setUpClass(cls):
        if not _have_foley():
            raise unittest.SkipTest("ffmpeg or work/audio/sfx_sources/ missing")
        cls.src = alts.AltSources()
        cls.out = {a.name: (a, alts.render(a, cls.src)[0]) for a in alts.ALTS if a.kind != "fire"}

    def test_twelve(self):
        self.assertEqual(len(self.out), 4 * alts.ALT_COUNT)

    def test_levels_band_and_length(self):
        for a, x in self.out.values():
            self.check_levels(a, x)

    def test_deterministic(self):
        for name in ("SDTTPKP_alt2", "SDIZRLD_alt3", "SDIZPKP_alt3"):
            a, x = self.out[name]
            fresh = alts.render(a, alts.AltSources())[0]
            self.assertEqual(gws.wav_bytes(fresh), gws.wav_bytes(x), name)

    def test_izh_snaps_shut_on_the_reload_frame(self):
        for i in range(1, alts.ALT_COUNT + 1):
            a, x = self.out[f"SDIZRLD_alt{i}"]
            self.assertAlmostEqual(_loudest_window_centre(x), gws.tics(gws.IZH_RELOAD_CLOSE_TICS),
                                   delta=alts.IZH_SNAP_TOLERANCE_S, msg=a.name)
            self.assertLessEqual(len(x) / gws.SR, gws.tics(gws.IZH_RELOAD_TICS) + 0.1, a.name)


def _fake_done():
    out = []
    for a in alts.ALTS:
        x = np.sin(np.arange(4410) * 0.3) * 0.5
        out.append(alts.Rendered(a, x, 0.0, gws.wav_bytes(x)))
    return out


@needs_numpy
class PageTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.page = root / "docs" / "art" / "previews" / "2026-10-15_0100_M3_listening-alternatives.html"
        self.page.parent.mkdir(parents=True)
        self.html = alts.page_html(_fake_done(), self.page, REAL_OUT, "2026-10-15_0100")

    def tearDown(self):
        self.tmp.cleanup()

    def test_spanish_vote_buttons_and_copy(self):
        h = self.html
        self.assertIn('<html lang="es">', h)
        self.assertIn("Copiar resultado", h)
        for b in ('data-v="ok">OK<', 'data-v="no">NO<', 'data-v="q">?<'):
            self.assertIn(b, h)
        self.assertIn("El rechazado", h)
        self.assertIn("Hoy en el juego", h)
        self.assertIn("<title>Alternativas de sonido M3</title>", h)

    def test_local_storage_only_inside_try(self):
        for line in self.html.splitlines():
            if "localStorage" in line:
                self.assertIn("try {", line)

    def test_every_row_has_alternative_rejected_and_freedoom(self):
        m = re.search(r"const ITEMS = (\[.*?\]);\n", self.html, re.S)
        import json
        items = json.loads(m.group(1))
        self.assertEqual(len(items), len(alts.ALTS))
        for it in items:
            for key in ("src", "rej", "repSrc"):
                self.assertFalse(re.match(r"^([A-Za-z]:|/)", it[key]), it[key])
            self.assertTrue(it["src"].endswith(f"{it['id']}.ogg"))
            self.assertTrue(it["rej"].endswith(f"{it['lump']}.ogg"))
            self.assertIn("freedoom/DS", it["repSrc"])
            if it["lump"] == "SDRKFIR":
                self.assertEqual(len(it["extras"]), 3)

    def test_the_real_page_points_at_files_that_exist(self):
        pages = sorted(PREVIEWS.glob("*_M3_listening-alternatives.html"))
        if not pages or not REAL_OUT.is_dir():
            self.skipTest("the page or work/audio/alt/ is not on this machine")
        h = pages[-1].read_text(encoding="utf-8")
        srcs = set(re.findall(r'"(?:src|rej|repSrc)": "([^"]+)"', h))
        self.assertGreaterEqual(len(srcs), len(alts.ALTS) + len(alts.TARGETS))
        for rel in srcs:
            self.assertTrue((pages[-1].parent / rel).resolve().is_file(), rel)


@needs_numpy
class MainTests(unittest.TestCase):

    def test_list_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()) as out:
            self.assertEqual(alts.main(["--list", "--out", tmp]), 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(len(out.getvalue().strip().splitlines()), len(alts.ALTS))

    @slow
    def test_main_writes_only_where_told(self):
        if gws.ffmpeg_path() is None:
            self.skipTest("ffmpeg is not on the PATH")
        before = sorted(p.stat().st_mtime_ns for p in REAL_OUT.rglob("*")) if REAL_OUT.is_dir() else []
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "2026-10-15_0100_M3_listening-alternatives.html"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = alts.main(["--out", tmp, "--page", str(page), "SDRKFIR"])
            self.assertEqual(code, 0)
            names = {p.name for p in Path(tmp).rglob("*") if p.is_file()}
            for i in range(1, alts.ALT_COUNT + 1):
                self.assertIn(f"SDRKFIR_alt{i}.ogg", names)
                self.assertIn(f"SDRKFIR_alt{i}_held.ogg", names)
            self.assertIn("MANIFEST.txt", names)
            self.assertIn("PROVENANCE.tsv", names)
            self.assertIn("Copiar resultado", page.read_text(encoding="utf-8"))
        after = sorted(p.stat().st_mtime_ns for p in REAL_OUT.rglob("*")) if REAL_OUT.is_dir() else []
        self.assertEqual(before, after, "work/audio/alt/ was touched")


if __name__ == "__main__":
    unittest.main()
