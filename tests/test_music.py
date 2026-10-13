"""The music that ships, and the downloads it came from (D43).

What is pinned here, without ever starting GZDoom (D26):

- Every lump in `assets/music/` is a legal lump name, a well-formed Standard
  MIDI File with zero hanging notes, and has provenance in both registers
  (`docs/art/LICENSES.md`, which `tools/check_pk3.py` reads, and
  `docs/sound/MUSIC-RIGHTS.md`, which owns the rights analysis).
- Each installed file is REPRODUCIBLE from its source, byte for byte:
  `D_SDM01` from `tools/audio/gen_music.py`, `D_SDINTL` from Engelbach's
  download with `midi_edit.py --trim-head`. An approved asset that nobody can
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

INSTALLED = ("D_SDINTL", "D_SDM01")                 # D43
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

    def test_d_sdm01_is_what_the_generator_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _seconds, _size = gen_music.generate("map01", Path(tmp), None, quiet=True)
            self.assertEqual(sha256(MUSIC_ASSETS / "D_SDM01.mid"), sha256(path))

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
