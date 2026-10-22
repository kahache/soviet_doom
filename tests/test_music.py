"""The music that ships, and the downloads it came from (D43).

What is pinned here, without ever starting GZDoom (D26):

- Every lump in `assets/music/` is a legal lump name, a well-formed Standard
  MIDI File with zero hanging notes, and has provenance in both registers
  (`docs/art/LICENSES.md`, which `tools/check_pk3.py` reads, and
  `docs/sound/MUSIC-RIGHTS.md`, which owns the rights analysis).
- Each installed file is REPRODUCIBLE from its source, byte for byte:
  `D_SDM1N2` (MAP01 since D95) from `tools/audio/compose_map01.py`, `D_SDINTL` from Engelbach's
  download with `midi_edit.py --trim-head`, the two D62 drafts
  (`D_SDFUNR`, `D_SDGATE`) from the builders they were written with under
  D44 and D54, and N9e's two (D83, D86): `D_SDTITL`, the intermission, from
  `gen_music.py`, and `D_SDM01T`, the range's, which is `D_SDM01E` (also
  `gen_music.py`) cut at bar 49 by `gen_enemy_alts.trim_midi` (that half
  needs numpy), and D106's ten episode 2 pieces from
  `tools/audio/compose_episode2.py` at the CC7 scale each was calibrated to.
  `D_SDAMUR` (D83: NO) no longer ships. Nothing is composed or sequenced here (D59): the
  generator is only run into a temporary folder to compare bytes. An approved asset that nobody can
  regenerate is an asset nobody can repair.
- The downloaded candidates in `work/audio/candidates/` (tracked in git since
  D43) are exactly the files whose SHA-256 MUSIC-RIGHTS records, every one has
  a stable lump in the registry, and the three D43 discards are gone.
- The Engelbach credit is where the credits live.

Python standard library only, like the tools. Run:
    python3 -m unittest tests.test_music -v
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import audition  # noqa: E402
import gen_music  # noqa: E402
import midi_edit  # noqa: E402
import midi_inspect  # noqa: E402
from sdbuild.wad import validate_lump_name  # noqa: E402

MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"
CANDIDATES = PROJECT_ROOT / "work" / "audio" / "candidates"
REGISTRY = CANDIDATES / audition.CANDIDATE_REGISTRY_NAME
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
SOUNDTRACK = PROJECT_ROOT / "docs" / "sound" / "SOUNDTRACK.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"

# D62 (N8): drafts installed for the CEO's ear, wired in MAPINFO; lump ->
# the gen_music.py piece key that wrote it (under D44 / D54, before D59).
D62_DRAFTS = {"D_SDFUNR": "funeral",                # MAP02, the metro
              "D_SDGATE": "gate"}                   # MAP03, Tankograd
# N9e (D83, D86): the intermission and the range's cut of MAP01's theme.
N9E_TITLE = ("D_SDTITL", "title")                   # gen_music.py piece key
N9E_RANGE = ("D_SDM01T", "map01e", 49)              # D_SDM01E cut from bar 49
RETIRED = ("D_SDAMUR", "D_SDM01")                  # D83: NO for the range; D95: off MAP01
N9E_MAP01 = ("D_SDM1N2", "D_SDM01N2")             # D95: the lump, compose_map01.py's variant
# D106 (CEO, "10/10 OK"): episode 2's pieces, lump -> the CC7 volume scale
# compose_episode2.calibrate_and_render settled on (work/audio/episode2/render/
# meta.json rounds it to 3 places; 0.8352 and 0.825 are the values that give
# back the approved bytes). The boss loops are cut from their MAP06 piece.
EPISODE2 = {"D_SDM04A": 0.921, "D_SDM04B": 0.953,
            "D_SDM05A": 0.843, "D_SDM05B": 0.828,
            "D_SDM06A": 0.848, "D_SDM06B": 0.8352,
            "D_SDE2IA": 0.88, "D_SDE2IB": 0.825}
EPISODE2_BOSS = {"D_SDBS6A": "D_SDM06A", "D_SDBS6B": "D_SDM06B"}
INSTALLED = ("D_SDINTL", N9E_MAP01[0],              # D43; MAP01's since D95
             "D_SDRAD1", "D_SDRAD2",                # D43 radio, tests/test_radio.py
             *D62_DRAFTS,                           # D62 drafts
             N9E_TITLE[0], N9E_RANGE[0],            # N9e
             *EPISODE2, *EPISODE2_BOSS)             # D106
ENGELBACH_SOURCE = "WM_Internationale_orch2.mid"
DISCARDED = ("MU_RimskyKorsakov_FugueBACH.mid",    # D_CND02
             "MU_Scriabin_Prelude_op11n1.mid",     # D_CND04
             "MU_Tchaikovsky_WoodenSoldiers.mid")  # D_CND08
RADIO = ("WM_Ej_uchnem.mid", "WM_Kolokolchik.mid")  # the diegetic radio, CC0 (D43)
ENGELBACH = "Jerry Engelbach"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InstalledMusicTests(unittest.TestCase):
    def test_the_installed_set_is_exactly_the_d43_set(self):
        self.assertEqual(sorted(INSTALLED),
                         sorted(p.stem for p in MUSIC_ASSETS.glob("*.mid")))
        self.assertEqual([], [p.name for p in MUSIC_ASSETS.iterdir()
                              if p.suffix.lower() != ".mid"])

    def test_every_lump_is_a_legal_name_and_a_clean_midi(self):
        for path in sorted(MUSIC_ASSETS.glob("*.mid")):
            with self.subTest(lump=path.stem):
                self.assertEqual(path.stem, validate_lump_name(path.stem))
                info = midi_inspect.parse(path)
                self.assertEqual(0, info["hanging"], "a hanging note drones under the map")
                self.assertGreater(info["notes"], 0)

    def test_every_lump_has_provenance_in_both_registers(self):
        licenses = LICENSES.read_text(encoding="utf-8")
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        for lump in INSTALLED:
            with self.subTest(lump=lump):
                self.assertIn(f"`{lump}`", licenses)
                self.assertIn(lump, rights)

    def test_d_sdm1n2_is_what_compose_map01_writes(self):
        import compose_map01
        lump, variant = N9E_MAP01
        data = compose_map01.midi_bytes(compose_map01.VARIANT_BY_LUMP[variant])
        self.assertEqual(hashlib.sha256(data).hexdigest(), sha256(MUSIC_ASSETS / f"{lump}.mid"))
        self.assertEqual(lump, validate_lump_name(lump))

    def test_episode_2_is_what_compose_episode2_writes(self):
        import compose_episode2 as ce
        songs = {v.lump: s for _key, v, s in ce.all_songs()}
        self.assertEqual(set(EPISODE2), set(songs))
        self.assertEqual(EPISODE2_BOSS, {boss: lump for lump, boss in ce.BOSS_LUMP.items()})
        for lump, scale in EPISODE2.items():
            song = songs[lump]
            song.volume_scale = scale
            with self.subTest(lump=lump):
                self.assertEqual(sha256(MUSIC_ASSETS / f"{lump}.mid"),
                                 hashlib.sha256(song.midi()).hexdigest())
        for boss, lump in EPISODE2_BOSS.items():
            with self.subTest(lump=boss):
                self.assertEqual(sha256(MUSIC_ASSETS / f"{boss}.mid"),
                                 hashlib.sha256(songs[lump].midi(*ce.BOSS_BARS)).hexdigest())

    def test_the_d62_drafts_are_the_files_the_ceo_was_given_to_hear(self):
        with tempfile.TemporaryDirectory() as tmp:
            for lump, key in D62_DRAFTS.items():
                with self.subTest(lump=lump):
                    path, _seconds, _size = gen_music.generate(key, Path(tmp), None, quiet=True)
                    self.assertEqual(f"{lump}.mid", path.name)
                    self.assertEqual(sha256(path), sha256(MUSIC_ASSETS / f"{lump}.mid"))

    def test_d_sdtitl_is_what_the_generator_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _seconds, _size = gen_music.generate(N9E_TITLE[1], Path(tmp), None, quiet=True)
            self.assertEqual(f"{N9E_TITLE[0]}.mid", path.name)
            self.assertEqual(sha256(path), sha256(MUSIC_ASSETS / path.name))

    def test_d_sdm01t_is_d_sdm01e_cut_at_bar_49(self):
        try:
            import gen_enemy_alts as ea
        except ImportError:
            self.skipTest("numpy is not installed (gen_enemy_alts.trim_midi's module needs it)")
        lump, key, bar = N9E_RANGE
        self.assertEqual(ea.TRIMS[lump][0], bar)
        with tempfile.TemporaryDirectory() as tmp:
            path, _seconds, _size = gen_music.generate(key, Path(tmp), None, quiet=True)
            cut = ea.trim_midi(path.read_bytes(), bar, f"Soviet Doom - {lump} (D_SDM01E from bar {bar}, D83 draft)")
        self.assertEqual(hashlib.sha256(cut).hexdigest(), sha256(MUSIC_ASSETS / f"{lump}.mid"))

    def test_the_rejected_range_piece_no_longer_ships(self):
        for lump in RETIRED:
            self.assertFalse((MUSIC_ASSETS / f"{lump}.mid").exists(), lump)

    def test_d_sdintl_is_engelbachs_file_with_the_head_silence_trimmed(self):
        source = CANDIDATES / ENGELBACH_SOURCE
        fmt, division, tracks = midi_edit.read_smf(source.read_bytes())
        start = midi_edit.first_note_tick(tracks)
        self.assertEqual(2863, start, "the 1.99 s hole SOUNDTRACK.md 4.1 measured")
        midi_edit.trim_head(tracks, start)
        rebuilt = midi_edit.write_smf(fmt, division, tracks)
        self.assertEqual(hashlib.sha256(rebuilt).hexdigest(),
                         sha256(MUSIC_ASSETS / "D_SDINTL.mid"))


class CandidateTests(unittest.TestCase):
    def test_discards_are_gone_and_the_radio_pieces_stay(self):
        for name in DISCARDED:
            self.assertFalse((CANDIDATES / name).exists(), name)
        for name in RADIO:
            self.assertTrue((CANDIDATES / name).is_file(), name)

    def test_every_candidate_hash_is_recorded_in_music_rights(self):
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        files = sorted(CANDIDATES.glob("*.mid"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(file=path.name):
                self.assertIn(sha256(path), rights)

    def test_every_candidate_has_a_registered_lump_and_vice_versa(self):
        registered = audition.read_registry(REGISTRY)
        present = {p.name for p in CANDIDATES.glob("*.mid")}
        self.assertEqual(present, set(registered))
        lumps = list(registered.values())
        self.assertEqual(len(lumps), len(set(lumps)), "two files share a lump")
        for lump in lumps:
            validate_lump_name(lump)
        # retired numbers are kept, commented, so they are never handed out again
        text = REGISTRY.read_text(encoding="utf-8")
        for name in DISCARDED:
            self.assertIn(name, text)


class CreditTests(unittest.TestCase):
    def test_engelbach_is_credited_wherever_the_credits_live(self):
        for doc in (MUSIC_RIGHTS, SOUNDTRACK, LICENSES):
            with self.subTest(doc=doc.name):
                self.assertIn(ENGELBACH, doc.read_text(encoding="utf-8"))


# --- the D43 enrichment of D_SDM01: a draft, never installed by a test -------

TICKS_PER_BAR = gen_music.TICKS_PER_BEAT * gen_music.BEATS_PER_BAR
NOTE_ON = gen_music.STATUS_NOTE_ON
DRUMS = gen_music.DRUM_CHANNEL


def note_ons(tracks) -> list[tuple[int, int, int]]:
    """(tick, channel, pitch) of every note-on the builder scheduled."""
    out = []
    for track in tracks:
        for tick, _order, _seq, payload in track.events:
            if payload[0] & 0xF0 == NOTE_ON and payload[2] > 0:
                out.append((tick, payload[0] & 0x0F, payload[1]))
    return out


def programs(tracks) -> set[int]:
    return {payload[1] for track in tracks for _t, _o, _s, payload in track.events
            if payload[0] & 0xF0 == gen_music.STATUS_PROGRAM_CHANGE}


class EnrichedMap01Tests(unittest.TestCase):
    """SOUNDTRACK.md 6, Card 2b: two more layers, a non-repeating fourth
    section, the loop kept, zero rights -- each one measured here."""

    @classmethod
    def setUpClass(cls):
        cls.tracks, cls.end_beat = gen_music.build_map01_enriched(gen_music.MAP01_TEMPO_BPM)
        cls.base_tracks, _ = gen_music.build_map01(gen_music.MAP01_TEMPO_BPM)
        cls.notes = note_ons(cls.tracks)
        sb = gen_music.MAP01_SECTION_BARS
        cls.lament = range(3 * sb, 4 * sb)

    def test_two_more_instrumental_layers(self):
        before, after = programs(self.base_tracks), programs(self.tracks)
        self.assertEqual(before | {gen_music.GM_FRENCH_HORN, gen_music.GM_CELLO}, after)
        self.assertEqual(len(before) + 2, len(after))

    def test_the_fourth_section_never_repeats_a_bar(self):
        bars = []
        for bar in self.lament:
            content = frozenset((tick - bar * TICKS_PER_BAR, ch, p) for tick, ch, p in self.notes
                                if ch != DRUMS and bar * TICKS_PER_BAR <= tick < (bar + 1) * TICKS_PER_BAR)
            self.assertTrue(content, f"bar {bar + 1} is empty")
            bars.append(content)
        self.assertEqual(len(bars), len(set(bars)), "two bars of the lament are identical")

    def test_the_lament_has_no_ostinato(self):
        for bar in self.lament:
            bass = [p for tick, ch, p in self.notes
                    if ch == 0 and bar * TICKS_PER_BAR <= tick < (bar + 1) * TICKS_PER_BAR]
            self.assertLessEqual(len(bass), 2, f"bar {bar + 1}: more than root and fifth")

    def test_every_written_bar_of_the_new_lines_is_four_beats(self):
        for name in ("MAP01E_LAMENT_HORN", "MAP01E_LAMENT_CELLO"):
            for index, bar in enumerate(getattr(gen_music, name)):
                with self.subTest(line=name, bar=index + 1):
                    self.assertEqual(gen_music.BEATS_PER_BAR, sum(length for _n, length in bar))
        self.assertEqual(gen_music.MAP01_SECTION_BARS, len(gen_music.MAP01E_LAMENT_HORN))
        self.assertEqual(gen_music.MAP01_SECTION_BARS, len(gen_music.MAP01E_LAMENT_HARMONY))

    def test_the_loop_still_restarts_from_near_silence(self):
        last_bar = int(self.end_beat) // gen_music.BEATS_PER_BAR
        tail = [n for n in self.notes if n[0] >= (last_bar - 2) * TICKS_PER_BAR]
        self.assertEqual([], tail, "the last two bars must start nothing new")
        first_bar = sorted(n for n in self.notes if n[0] < TICKS_PER_BAR)
        base_first = sorted(n for n in note_ons(self.base_tracks) if n[0] < TICKS_PER_BAR)
        self.assertEqual(base_first, first_bar, "the loop restarts on the same bar as before")

    def test_the_draft_is_a_clean_midi_under_a_draft_name(self):
        self.assertEqual("D_SDM01E", validate_lump_name(gen_music.MAP01E_LUMP))
        with tempfile.TemporaryDirectory() as tmp:
            path, seconds, _size = gen_music.generate("map01e", Path(tmp), None, quiet=True)
            info = midi_inspect.parse(path)
        self.assertEqual(0, info["hanging"])
        self.assertAlmostEqual(160.0, seconds, places=1)
        self.assertNotIn("D_SDM01E", [p.stem for p in MUSIC_ASSETS.glob("*.mid")],
                         "the draft enters assets/ only on the CEO's approval")


if __name__ == "__main__":
    unittest.main()
