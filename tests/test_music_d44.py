"""D44: the two tunes sequenced from a downloaded public-domain score.

What can be measured without ears and without GZDoom (D26), pinned here:

- the transcription is well formed: every bar of the copied melody adds up
  to the edition's time signature, and every per-bar table (harmony, bass,
  chords, the read/ours flags) has one entry per printed bar;
- the files: zero hanging notes, the expected length, the key signature
  the edition prints, written into the MIDI;
- the key, from the notes themselves: the only notes outside the printed
  key are the accidentals the edition prints (the leading tones and the
  raised fourth), and each melody ends on the printed key's tonic;
- loop behaviour: the waltz starts on its first note and every note ends
  inside the file, so the engine's loop is the edition's repeat; the
  funeral march is a cue that ends, so its last bar is silent;
- our part stays ours: on every downbeat the edition's melody note is a
  tone of the chord we harmonised it with;
- the drafts are installed in assets/ by D62 (N8) for the CEO to hear in
  play, byte for byte what the builders write, and SOUNDTRACK still calls
  them drafts; the scores they come from are the files whose SHA-256
  MUSIC-RIGHTS records.

Python standard library only. Run:
    python3 -m unittest tests.test_music_d44 -v
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

import gen_music as gm  # noqa: E402
import midi_inspect  # noqa: E402
from sdbuild.wad import validate_lump_name  # noqa: E402

MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"
SCORES = PROJECT_ROOT / "work" / "audio" / "scores"
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
SOUNDTRACK = PROJECT_ROOT / "docs" / "sound" / "SOUNDTRACK.md"

PRINTED_BARS = 32
NATURAL_MINOR = (0, 2, 3, 5, 7, 8, 10)          # semitones above the tonic
# The accidentals each edition prints in the melody, as pitch classes:
# Detlaf: F# (bars 3, 11, 27) and B natural (bar 23);
# Kyuss: B natural (the leading tone, bars 5-6, 15, 25, 27) and F# (bar 28).
FUNERAL_PRINTED_ACCIDENTALS = {6, 11}
AMUR_PRINTED_ACCIDENTALS = {11, 6}
FUNERAL_SECONDS = (0.5 + 2 * 64 + 3 * 2) * 60 / gm.FUNERAL_TEMPO_BPM   # pickup, 2 strophes, coda + tail
AMUR_SECONDS = 2 * 32 * 3 * 60 / gm.AMUR_TEMPO_BPM                    # the period, twice


def melody_pitches(bars) -> list[int]:
    return [p for bar in bars for pitches, _o, _b, grace in gm._events(bar) if not grace
            for p in pitches]


def note_spans(tracks) -> list[tuple[int, int, int, int]]:
    """(on_tick, off_tick, channel, pitch) for every note the builder scheduled."""
    spans, open_ = [], {}
    events = sorted((e for t in tracks for e in t.events), key=lambda e: (e[0], e[1], e[2]))
    for tick, _order, _seq, payload in events:
        kind, chan = payload[0] & 0xF0, payload[0] & 0x0F
        if kind == gm.STATUS_NOTE_ON and payload[2] > 0:
            open_.setdefault((chan, payload[1]), []).append(tick)
        elif kind == gm.STATUS_NOTE_OFF:
            spans.append((open_[(chan, payload[1])].pop(0), tick, chan, payload[1]))
    return spans


class TranscriptionTests(unittest.TestCase):
    def test_every_copied_bar_adds_up_to_the_printed_metre(self):
        cases = ((gm.FUNERAL_MELODY, gm.FUNERAL_BEATS_PER_BAR),
                 (gm.AMUR_MELODY, gm.AMUR_BEATS_PER_BAR),
                 (gm.AMUR_BASS, gm.AMUR_BEATS_PER_BAR))
        for bars, metre in cases:
            self.assertEqual(PRINTED_BARS, len(bars))
            for number, bar in enumerate(bars, start=1):
                with self.subTest(bar=number):
                    if bars is gm.AMUR_BASS:      # a bass bar may be a single downbeat
                        self.assertLessEqual(gm.bar_length(bar), metre)
                    else:
                        self.assertEqual(metre, gm.bar_length(bar))
        self.assertEqual(0.5, gm.bar_length(gm.FUNERAL_PICKUP), "the printed anacrusis is an eighth")

    def test_every_per_bar_table_has_one_entry_per_printed_bar(self):
        for table in (gm.FUNERAL_HARMONY, gm.AMUR_CHORDS, gm.AMUR_CHORD_SOURCE):
            self.assertEqual(PRINTED_BARS, len(table))
        for number, chords in enumerate(gm.FUNERAL_HARMONY, start=1):
            with self.subTest(bar=number):
                self.assertEqual(gm.FUNERAL_BEATS_PER_BAR, sum(beats for _a, beats, _v, _r in chords))
        for flag, chord in zip(gm.AMUR_CHORD_SOURCE, gm.AMUR_CHORDS):
            self.assertIn(flag, ("read", "ours", "-"))
            self.assertEqual(flag == "-", chord is None, "a bar with no chord is flagged '-'")

    def test_the_funeral_harmony_agrees_with_the_printed_melody_on_every_downbeat(self):
        for number, (bar, chords) in enumerate(zip(gm.FUNERAL_MELODY, gm.FUNERAL_HARMONY), start=1):
            with self.subTest(bar=number):
                first = next(pitches for pitches, offset, _b, grace in gm._events(bar) if not grace)
                voicing, root = chords[0][2], chords[0][3]
                chord_pcs = {gm.pitch(n) % 12 for n in voicing + (root,)}
                self.assertIn(first[0] % 12, chord_pcs)


class KeyTests(unittest.TestCase):
    def check_key(self, bars, tonic_pc, printed_accidentals):
        scale = {(tonic_pc + step) % 12 for step in NATURAL_MINOR}
        outside = {p % 12 for p in melody_pitches(bars)} - scale
        self.assertEqual(printed_accidentals, outside)

    def test_funeral_is_in_f_minor_with_only_the_printed_accidentals(self):
        self.assertEqual((-4, True), gm.FUNERAL_KEY)
        self.check_key(gm.FUNERAL_MELODY + [gm.FUNERAL_PICKUP], gm.FUNERAL_TONIC_PC,
                       FUNERAL_PRINTED_ACCIDENTALS)
        self.assertEqual(gm.FUNERAL_TONIC_PC, melody_pitches(gm.FUNERAL_MELODY)[-1] % 12)

    def test_amur_is_in_c_minor_with_only_the_printed_accidentals(self):
        self.assertEqual((-3, True), gm.AMUR_KEY)
        self.check_key(gm.AMUR_MELODY, gm.AMUR_TONIC_PC, AMUR_PRINTED_ACCIDENTALS)
        last_bar_tops = [max(p) for p, _o, _b, g in gm._events(gm.AMUR_MELODY[-1]) if not g]
        self.assertEqual(gm.AMUR_TONIC_PC, last_bar_tops[-1] % 12)


class FileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = {}
        for key in ("funeral", "amur"):
            path, seconds, _size = gm.generate(key, Path(cls.tmp.name), None, quiet=True)
            cls.out[key] = (midi_inspect.parse(path), seconds)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_clean_files_of_the_planned_length(self):
        for key, expected in (("funeral", FUNERAL_SECONDS), ("amur", AMUR_SECONDS)):
            with self.subTest(piece=key):
                info, seconds = self.out[key]
                self.assertEqual(0, info["hanging"], "a hanging note drones on")
                self.assertGreater(info["notes"], 0)
                self.assertAlmostEqual(expected, seconds, places=3)
                self.assertAlmostEqual(expected, info["seconds"], places=2)

    def test_the_printed_key_signature_is_in_the_file(self):
        self.assertEqual(["-4 minor"], self.out["funeral"][0]["key_sigs"])
        self.assertEqual(["-3 minor"], self.out["amur"][0]["key_sigs"])
        self.assertEqual(["2/4"], self.out["funeral"][0]["time_sigs"])
        self.assertEqual(["3/4"], self.out["amur"][0]["time_sigs"])

    def test_draft_names_are_legal_lumps_installed_as_drafts(self):
        """D62 (N8): installed so the CEO hears them in play (MAP02, RANGE),
        still drafts until he approves them by ear."""
        soundtrack = SOUNDTRACK.read_text(encoding="utf-8")
        for lump in (gm.FUNERAL_LUMP, gm.AMUR_LUMP):
            with self.subTest(lump=lump):
                self.assertEqual(lump, validate_lump_name(lump))
                self.assertTrue((MUSIC_ASSETS / f"{lump}.mid").is_file(), "D62 installs it")
                self.assertTrue(any(f"`{lump}`" in line and "pending the CEO's ear" in line
                                    for line in soundtrack.splitlines()),
                                "SOUNDTRACK.md must still call it a draft")


class LoopTests(unittest.TestCase):
    def test_the_waltz_loop_is_the_editions_repeat(self):
        tracks, end_beat = gm.build_amur(gm.AMUR_TEMPO_BPM)
        spans = note_spans(tracks)
        end_tick = round(end_beat * gm.TICKS_PER_BEAT)
        self.assertEqual(0, min(on for on, _off, _c, _p in spans), "no silence before bar 1")
        self.assertLessEqual(max(off for _on, off, _c, _p in spans), end_tick, "nothing rings past the loop")
        self.assertEqual(0, end_beat % gm.AMUR_BEATS_PER_BAR, "the loop point is a barline")
        period = len(gm.AMUR_MELODY) * gm.AMUR_BEATS_PER_BAR * gm.TICKS_PER_BEAT
        clarinet = sorted((on, p) for on, _off, c, p in spans if c == 0)
        first = [(on, p) for on, p in clarinet if on < period]
        second = [(on - period, p) for on, p in clarinet if on >= period]
        self.assertEqual(first, second, "both passes play the same printed notes")

    def test_the_funeral_march_ends_and_its_last_bar_is_silent(self):
        tracks, end_beat = gm.build_funeral(gm.FUNERAL_TEMPO_BPM)
        spans = note_spans(tracks)
        end_tick = round(end_beat * gm.TICKS_PER_BEAT)
        tail = end_tick - gm.FUNERAL_TAIL_BARS * gm.FUNERAL_BEATS_PER_BAR * gm.TICKS_PER_BEAT
        self.assertEqual([], [s for s in spans if s[0] >= tail], "the tail starts nothing")
        self.assertLessEqual(max(off for _on, off, _c, _p in spans), end_tick)
        self.assertEqual(0, min(on for on, _off, _c, _p in spans), "the anacrusis opens the file")


class ProvenanceTests(unittest.TestCase):
    def test_music_rights_and_soundtrack_name_both_drafts(self):
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        track = SOUNDTRACK.read_text(encoding="utf-8")
        for lump in (gm.FUNERAL_LUMP, gm.AMUR_LUMP, "D_SDGLNK"):
            self.assertIn(lump, rights)
            self.assertIn(lump, track)

    def test_every_downloaded_score_is_the_file_music_rights_records(self):
        files = sorted(SCORES.glob("*/*")) if SCORES.is_dir() else []
        if not files:
            self.skipTest("work/audio/scores/ is gitignored and absent on this checkout")
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        for path in files:
            with self.subTest(file=path.name):
                self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), rights)
                self.assertIn(path.name, rights)
        # one score per piece, each in its own directory (D44)
        self.assertEqual(len(files), len({p.parent for p in files}))


if __name__ == "__main__":
    unittest.main()
