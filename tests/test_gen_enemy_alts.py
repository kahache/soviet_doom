"""Tests for tools/audio/gen_enemy_alts.py: alternatives for the eight enemy
sounds the CEO marked NO on the M3 listening sheet (D83), the trimmed MAP01
music draft D_SDM01T, and the listening page.

What is tested:

- The contract: exactly the five lumps and three beds of D83, three
  alternatives each, each its own recipe and none a recipe of gen_sfx.py
  (the rejected drafts); the Freedoom lump each is levelled against is the
  one the M3 sheet put beside it.
- Provenance (ENEMY-SOUNDS §2): only files of the four CC0 packs on disk,
  never a `shot_*` file, every file's SHA-256 pinned and matching, every
  pinned file used, and every alternative that reads a pack also carries a
  layer of our own synthesis.
- Levels (D83, the ruler of gen_weapon_alts): peak at or under -1 dBFS, the
  loudest 50 ms (A-weighted) within 1 dB of the Freedoom sound's minus the
  kind's allowance, at least half of the energy above 300 Hz, the length in
  its bounds; the Freedoom levels re-measured from the IWAD.
- The music (D59: editing, not composing): every note of the trim is a note
  of D_SDM01E at the same pitch, velocity and length; it starts on its first
  tick, has no hanging note, is whole bars long, keeps every channel's setup
  at tick 0, and the draft on disk is what the function writes.
- The page: Spanish, OK/NO/? and "Copiar resultado", relative paths only,
  localStorage inside try/catch, rejected and Freedoom on every enemy row,
  the music rows and the MAP01 candidates with rights notes.

The pack alternatives need ffmpeg and the gitignored work/audio/sfx_sources/;
their full render (~15 s) is skipped with SD_SKIP_SLOW_ART=1 (`verify.py
fast`). The music render needs GZDoom's zmusic.dll on Windows. Nothing is
written under work/ or docs/ by the tests.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_enemy_alts -v
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    import numpy as np
    import gen_sfx as gs
    import gen_weapon_alts as wa
    import gen_weapon_sfx as gws
    import gen_enemy_alts as ea
except ImportError:                                    # pragma: no cover
    np = gs = wa = gws = ea = None

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the full render of the enemy alternatives")

D83_NO = {"SDRRIATK", "SDLTRATK", "SDSTOPAI", "SDSTODTH", "SDPZRPAI"}
D83_BEDS_NO = {"SDRRIPAI", "SDLTRPAI", "SDLTRDTH"}
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-14_2355_M3_listening-sheet.html"
PREVIEWS = PROJECT_ROOT / "docs" / "art" / "previews"


def _have_sources() -> bool:
    if np is None or gs.ffmpeg_path() is None:
        return False
    return all(ea.source_path(p, n).is_file() for p, n in ea.SOURCES)


@needs_numpy
class ContractTests(unittest.TestCase):

    def test_exactly_the_lumps_and_beds_of_d83_three_each(self):
        self.assertEqual(set(ea.TARGETS), D83_NO | D83_BEDS_NO)
        for lump, (kind, *_rest) in ea.TARGETS.items():
            self.assertEqual(kind == "bed", lump in D83_BEDS_NO, lump)
            got = sorted(a.index for a in ea.ALTS if a.lump == lump)
            self.assertEqual(got, list(range(1, ea.ALT_COUNT + 1)), lump)
        self.assertEqual(len(ea.ALTS_BY_NAME), len(ea.ALTS))

    def test_every_alternative_is_its_own_recipe_not_a_rejected_one(self):
        recipes = [a.recipe for a in ea.ALTS]
        self.assertEqual(len(set(recipes)), len(recipes))
        rejected = {r.build for r in gs.RECIPES.values()} | {r.build for r in gs.BEDS.values()}
        for a in ea.ALTS:
            self.assertNotIn(a.recipe, rejected, a.name)
            self.assertTrue(a.label and a.what and a.recipe.__doc__, a.name)
            self.assertTrue(a.recipe.__doc__.startswith(a.lump), a.name)
        for lump in ea.TARGETS:
            labels = [a.label for a in ea.ALTS if a.lump == lump]
            self.assertEqual(len(set(labels)), len(labels), lump)

    def test_freedoom_reference_is_the_one_beside_it_on_the_sheet(self):
        if not SHEET.is_file():
            self.skipTest("the M3 sheet is not here")
        items = json.loads(re.search(r"const ITEMS = (\[.*?\]);\n", SHEET.read_text(encoding="utf-8"), re.S).group(1))
        rep = {it["id"].replace("-bed", ""): it.get("repSrc", "") for it in items}
        for lump, (_, ref, rej, *_r) in ea.TARGETS.items():
            self.assertTrue(rep[lump].endswith(f"/{ref}.wav"), lump)
            self.assertIn(ref, ea.FREEDOOM_LEVELS)
            self.assertTrue(rej.endswith(f"{lump}.ogg") or rej.endswith(f"{lump}-bed.ogg"), lump)


@needs_numpy
class ProvenanceTests(unittest.TestCase):

    def test_only_cc0_packs_never_a_shot_every_hash_pinned(self):
        for (pack, name), digest in ea.SOURCES.items():
            self.assertIn(pack, ea.CC0_PACKS, name)
            self.assertNotIn("shot_", name)
            self.assertRegex(digest, r"^[0-9a-f]{64}$", name)
        names = [n for _, n in ea.SOURCES]
        self.assertEqual(len(set(names)), len(names), "a file name in two packs")

    def test_every_source_is_used_and_known(self):
        used = {k for a in ea.ALTS for k in a.sources}
        self.assertEqual(used, {n for _, n in ea.SOURCES})

    def test_source_files_match_their_pinned_sha256(self):
        missing = [n for p, n in ea.SOURCES if not ea.source_path(p, n).is_file()]
        if missing:
            self.skipTest(f"work/audio/sfx_sources/ not on this machine ({len(missing)} missing)")
        for (pack, name), digest in ea.SOURCES.items():
            self.assertEqual(gs.sha256_file(ea.source_path(pack, name)), digest, name)

    def test_an_unpinned_file_is_refused(self):
        c = ea.C("X", 1)
        with self.assertRaises(KeyError):
            c.src("OGA-100", "shot_01.ogg")


@needs_numpy
class FreedoomLevelTests(unittest.TestCase):

    def test_freedoom_levels_re_measured_from_the_iwad(self):
        for name, (pk, loud, rms) in ea.FREEDOOM_LEVELS.items():
            wav = gws.placeholder_wav(name)
            if wav is None:
                self.skipTest("iwads/freedoom2.wad is not on this machine")
            x, rate = wa.read_wav(wav)
            lv = wa.levels(x, rate)
            self.assertAlmostEqual(lv["peak"], pk, delta=ea.LEVEL_TOLERANCE_DB, msg=name)
            self.assertAlmostEqual(lv["loud_a"], loud, delta=ea.LEVEL_TOLERANCE_DB, msg=name)
            self.assertAlmostEqual(lv["rms"], rms, delta=ea.LEVEL_TOLERANCE_DB, msg=name)


class _Checks:

    def check(self, alt, x):
        lv = wa.levels(x)
        self.assertLessEqual(lv["peak"], ea.PEAK_DBFS + ea.PEAK_TOLERANCE_DB, alt.name)
        self.assertAlmostEqual(lv["loud_a"], ea.target_db(alt), delta=ea.LOUDNESS_TOLERANCE_DB, msg=alt.name)
        self.assertGreaterEqual(lv["above300"], ea.MIN_SHARE_ABOVE_300HZ, alt.name)
        lo, hi = alt.length_s
        self.assertTrue(lo <= lv["length"] <= hi, f"{alt.name}: {lv['length']:.3f} s")
        self.assertLess(np.max(np.abs(x[-gws.n_of(0.002):])), 0.01, f"{alt.name} ends in silence")


@needs_numpy
class SynthesisOnlyTests(unittest.TestCase, _Checks):
    """The alternatives with no pack file: always rendered."""

    @classmethod
    def setUpClass(cls):
        cls.out = {a.name: (a, ea.render(a)[0]) for a in ea.ALTS if not a.sources}

    def test_there_are_some(self):
        self.assertGreaterEqual(len(self.out), 3)

    def test_levels_band_and_length(self):
        for a, x in self.out.values():
            self.check(a, x)

    def test_deterministic(self):
        for name, (a, x) in self.out.items():
            self.assertEqual(gws.wav_bytes(ea.render(a)[0]), gws.wav_bytes(x), name)


@needs_numpy
@slow
class PackTests(unittest.TestCase, _Checks):
    """The alternatives that layer CC0 pack files: ffmpeg and the packs needed."""

    @classmethod
    def setUpClass(cls):
        if not _have_sources():
            raise unittest.SkipTest("ffmpeg or work/audio/sfx_sources/ missing")
        cls.out = {}
        for a in ea.ALTS:
            if a.sources:
                x, _, refs = ea.render(a)
                cls.out[a.name] = (a, x, refs)

    def test_levels_band_and_length(self):
        for a, x, _ in self.out.values():
            self.check(a, x)

    def test_refs_read_are_exactly_the_declared_sources(self):
        for a, _, refs in self.out.values():
            self.assertEqual({r.name for r in refs}, set(a.sources), a.name)
            for r in refs:
                self.assertEqual(r.sha256, ea.SOURCES[(r.pack, r.name)], a.name)

    def test_rifleman_alt2_final_click_is_quieter_than_the_first(self):
        """D86: SDRRIATK alt2 is approved "once its final click is quieter than
        the first". Loudest 50 ms, A-weighted, per part: the crack, the bolt's
        opening click, its closing ping."""
        _, x, _ = self.out["SDRRIATK_alt2"]
        bolt = gws.n_of(ea.RRI_BOLT_AT_S)
        ping = gws.n_of(ea.RRI_BOLT_AT_S + ea.RRI_FINAL_CLICK_AT_S - 0.01)
        crack, first, last = wa.loud_a_db(x[:bolt]), wa.loud_a_db(x[bolt:ping]), wa.loud_a_db(x[ping:])
        self.assertLessEqual(last, first - ea.FINAL_UNDER_FIRST_DB, (crack, first, last))
        self.assertLess(first, crack)
        self.assertLess(wa.peak_db(x[ping:]), wa.peak_db(x[bolt:ping]))

    def test_every_pack_alternative_carries_our_synthesis(self):
        for a in ea.ALTS:
            if a.sources:
                c = ea.C(a.name, ea.seed_of(a.name))
                a.recipe(c)
                self.assertTrue(c.synth, f"{a.name}: a CC0 clip must not ship alone")


def _src() -> bytes | None:
    return ea.MUSIC_SOURCE.read_bytes() if ea is not None and ea.MUSIC_SOURCE.is_file() else None


@needs_numpy
class MusicTrimTests(unittest.TestCase):

    def setUp(self):
        self.src = _src()
        if self.src is None:
            self.skipTest("work/audio/D_SDM01E.mid is not on this machine")
        self.div = ea.division_of(self.src)
        self.bar = self.div * ea.BEATS_PER_BAR

    def test_source_is_the_72_bar_piece_of_card_2b(self):
        self.assertEqual(ea.midi_length_ticks(self.src), ea.SOURCE_BARS * self.bar)

    def test_every_note_of_a_trim_is_a_note_of_the_source(self):
        src_notes = ea.notes_of(self.src)
        for lump, (first, *_r) in ea.TRIMS.items():
            cut = (first - 1) * self.bar
            want = [(t - cut, ch, p, v, ln) for t, ch, p, v, ln in src_notes if t >= cut]
            got = ea.notes_of(ea.trim_midi(self.src, first))
            self.assertEqual(got, want, lump)
            self.assertEqual(got[0][0], 0, f"{lump} starts on its first tick")

    def test_whole_bars_no_hanging_notes_setup_kept(self):
        import midi_edit as me
        for lump, (first, *_r) in ea.TRIMS.items():
            data = ea.trim_midi(self.src, first)
            self.assertEqual(ea.midi_length_ticks(data), (ea.SOURCE_BARS - first + 1) * self.bar, lump)
            _, _, tracks = me.read_smf(data)
            for events in tracks:
                ons = sum(1 for _, r in events if ea._is_on(r))
                offs = sum(1 for _, r in events if ea._is_off(r))
                self.assertEqual(ons, offs, lump)
                self.assertTrue(ea._is_eot(events[-1][1]))
            setup = lambda d: sorted(r for ev in me.read_smf(d)[2] for t, r in ev  # noqa: E731
                                     if t == 0 and r[0] & 0xF0 in (0xB0, 0xC0) or r[:2] == b"\xff\x51")
            self.assertEqual(setup(data), setup(self.src), lump)
            self.assertEqual(ea.tempo_us(data), ea.tempo_us(self.src))

    def test_the_draft_on_disk_is_what_the_function_writes(self):
        for lump, (first, *_r) in ea.TRIMS.items():
            p = ea.MUSIC_DIR / f"{lump}.mid"
            if not p.is_file():
                self.skipTest(f"{p.name} not written on this machine")
            name = f"Soviet Doom - {lump} (D_SDM01E from bar {first}, D83 draft)"
            self.assertEqual(p.read_bytes(), ea.trim_midi(self.src, first, name), lump)

    def test_lump_names_fit_eight_characters(self):
        for lump in ea.TRIMS:
            self.assertLessEqual(len(lump), 8)
        self.assertIn(ea.RECOMMENDED_TRIM, ea.TRIMS)


@needs_numpy
@slow
class MusicRenderTests(unittest.TestCase):

    def test_zmusic_renders_without_the_engine(self):
        src = _src()
        if src is None or ea.gzdoom_dir() is None or not sys.platform.startswith("win"):
            self.skipTest("D_SDM01E.mid or GZDoom's zmusic.dll not on this machine")
        data = ea.trim_midi(src, ea.TRIMS[ea.RECOMMENDED_TRIM][0])
        x, rate = ea.zmusic_render(data, 4.0)
        self.assertEqual(x.shape, (int(4.0 * rate), 2))
        self.assertGreater(np.max(np.abs(x)), 0.05, "the lament's first bars are not silent")
        self.assertLess(np.max(np.abs(x)), 1.0)


def _fake_done():
    out = []
    for a in ea.ALTS:
        x = np.sin(np.arange(4410) * 0.3) * 0.5
        out.append(ea.Rendered(a, x, 0.0, [], gws.wav_bytes(x)))
    return out


def _fake_music(root: Path):
    rows = [{"lump": "D_SDM01E", "bar": None, "seconds": 160.0, "bytes": 1, "ogg": root / "D_SDM01E.ogg"}]
    for lump, (bar, *_r) in ea.TRIMS.items():
        rows.append({"lump": lump, "bar": bar, "seconds": 53.3, "bytes": 1, "ogg": root / f"{lump}.ogg"})
    return rows


@needs_numpy
class PageTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.page = root / "docs" / "art" / "previews" / "2026-10-20_0100_M3_listening-enemy-alts-music.html"
        self.page.parent.mkdir(parents=True)
        self.html = ea.page_html(_fake_done(), self.page, root / "work" / "audio" / "enemy_alt",
                                 _fake_music(root / "work" / "audio" / "music_trim"), "2026-10-20_0100")
        self.items = json.loads(re.search(r"const ITEMS = (\[.*?\]);\n", self.html, re.S).group(1))

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

    def test_local_storage_only_inside_try(self):
        for line in self.html.splitlines():
            if "localStorage" in line:
                self.assertIn("try {", line)

    def test_rows_and_relative_paths(self):
        e = [i for i in self.items if i["sec"] == "e"]
        m = [i for i in self.items if i["sec"] == "m"]
        c = [i for i in self.items if i["sec"] == "c"]
        self.assertEqual(len(e), len(ea.ALTS))
        self.assertEqual({i["id"] for i in m}, set(ea.TRIMS))
        self.assertTrue(3 <= len(c) <= 5)
        for it in e + m:
            for key in ("src", "rej") + (("repSrc",) if it["sec"] == "e" else ()):
                self.assertFalse(re.match(r"^([A-Za-z]:|/)", it[key]), it[key])
        for it in e:
            self.assertIn("freedoom/DS", it["repSrc"])
        for it in c:
            self.assertTrue(it["rights"] and it["disk"] and it["who"], it["id"])
            self.assertRegex(it["disk"], r"^(SÍ|NO) está en disco")

    def test_the_real_page_points_at_files_that_exist(self):
        pages = sorted(PREVIEWS.glob("*_M3_listening-enemy-alts-music.html"))
        if not pages or not ea.OUT_DIR.is_dir():
            self.skipTest("the page or work/audio/enemy_alt/ is not on this machine")
        h = pages[-1].read_text(encoding="utf-8")
        srcs = set(re.findall(r'"(?:src|rej|repSrc)": "([^"]+)"', h))
        self.assertGreaterEqual(len(srcs), len(ea.ALTS) + len(ea.TARGETS))
        for rel in srcs:
            self.assertTrue((pages[-1].parent / rel).resolve().is_file(), rel)


@needs_numpy
class MainTests(unittest.TestCase):

    def test_list_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()) as out:
            self.assertEqual(ea.main(["--list", "--out", tmp]), 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(len(out.getvalue().strip().splitlines()), len(ea.ALTS))

    def test_main_writes_only_where_told(self):
        if gs.ffmpeg_path() is None:
            self.skipTest("ffmpeg is not on the PATH")
        before = sorted(p.stat().st_mtime_ns for p in ea.OUT_DIR.rglob("*")) if ea.OUT_DIR.is_dir() else []
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "2026-10-20_0100_M3_listening-enemy-alts-music.html"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = ea.main(["--out", tmp, "--no-music", "--page", str(page), "SDLTRPAI_alt2"])
            self.assertEqual(code, 0)
            names = {p.name for p in Path(tmp).rglob("*") if p.is_file()}
            self.assertTrue({"SDLTRPAI_alt2.ogg", "MANIFEST.txt", "PROVENANCE.tsv"} <= names)
            self.assertIn("Copiar resultado", page.read_text(encoding="utf-8"))
        after = sorted(p.stat().st_mtime_ns for p in ea.OUT_DIR.rglob("*")) if ea.OUT_DIR.is_dir() else []
        self.assertEqual(before, after, "work/audio/enemy_alt/ was touched")


if __name__ == "__main__":
    unittest.main()
