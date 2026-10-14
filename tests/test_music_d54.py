"""D54: the anthem slot, «Богатырские ворота» sequenced from the 1886 Bessel edition.

Glinka's Patriotic Song was dropped (D54); its replacement is the top voice of
Mussorgsky's «Богатырские ворота» (Pictures at an Exhibition, No. 10), copied
from one downloaded public-domain score. What can be measured without ears
and without GZDoom (D26), pinned here:

- the transcription is well formed: every copied bar adds up to the printed
  C (4/4), every per-bar table (harmony, source map) has one entry per bar;
- the key, from the notes themselves: the edition prints no accidental in
  the copied top voice, so every melody note is diatonic to E-flat major,
  and the piece ends on the tonic;
- the phrase comes from the edition: each copied bar carries its printed
  page, system and bar, and SOUNDTRACK.md's Card 5 maps the same bars;
- our part stays ours: at every chord change the edition's melody note is
  a tone of the chord we harmonised it with;
- the file: zero hanging notes, nothing re-struck while it still sounds, the
  length the tempo map gives, the printed key and metre written in, a silent
  last bar (the cue ends), and the draft stays out of assets/;
- the pieces that already exist come out of the generator unchanged.

Python standard library only. Run:
    python3 -m unittest tests.test_music_d54 -v
"""

from __future__ import annotations

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
SCORE = (PROJECT_ROOT / "work" / "audio" / "scores" / "bogatyrskie_vorota"
         / "Mussorgsky_Pictures_Exhibition_Piano_Score.pdf")
SCORE_SHA256 = "0a73559cd865083558f6e5923dddae4390069883dad795725c19f18646e58b71"
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
SOUNDTRACK = PROJECT_ROOT / "docs" / "sound" / "SOUNDTRACK.md"

E_FLAT_MAJOR = {(gm.GATE_TONIC_PC + s) % 12 for s in (0, 2, 4, 5, 7, 9, 11)}
COPIED_BARS = 16               # printed page 30, bars 1-16
GRAVE_BARS = 13                # printed page 34, the Grave, bars a-m
# 62 beats at 100, bar 16's last two beats at 84, the Grave (13 bars, four
# fermatas of 2 beats) and one silent bar at 60
EXPECTED_SECONDS = 62 * 60 / 100 + 2 * 60 / 84 + (13 * 4 + 4 * 2 + 4) * 60 / 60


def pitches_of(bars) -> list[int]:
    return [p for bar in bars for ps, _o, _b, grace in gm._events(bar) if not grace for p in ps]


def note_events(tracks):
    return sorted((e for t in tracks for e in t.events), key=lambda e: (e[0], e[1], e[2]))


class TranscriptionTests(unittest.TestCase):
    def test_every_copied_bar_adds_up_to_the_printed_metre(self):
        self.assertEqual(COPIED_BARS, len(gm.GATE_MELODY))
        self.assertEqual(GRAVE_BARS, len(gm.GATE_GRAVE))
        for name, bars in (("theme", gm.GATE_MELODY), ("grave", gm.GATE_GRAVE)):
            for number, bar in enumerate(bars, start=1):
                with self.subTest(part=name, bar=number):
                    self.assertEqual(gm.GATE_BEATS_PER_BAR, gm.bar_length(bar))

    def test_every_per_bar_table_has_one_entry_per_copied_bar(self):
        self.assertEqual(COPIED_BARS, len(gm.GATE_HARMONY))
        self.assertEqual(COPIED_BARS, len(gm.GATE_SOURCE))
        self.assertEqual(GRAVE_BARS, len(gm.GATE_GRAVE_HARMONY))
        self.assertEqual(GRAVE_BARS, len(gm.GATE_GRAVE_SOURCE))
        for chords, bar in zip(gm.GATE_HARMONY + gm.GATE_GRAVE_HARMONY,
                               gm.GATE_MELODY + gm.GATE_GRAVE):
            sounding = sum(b for n, b in bar if n is not None)
            self.assertEqual(sounding, sum(beats for _a, beats, _v, _r in chords))

    def test_the_source_map_is_the_editions_pages_in_order(self):
        self.assertEqual({30}, {page for page, _s, _b in gm.GATE_SOURCE})
        self.assertEqual({34}, {page for page, _s, _b in gm.GATE_GRAVE_SOURCE})
        for source in (gm.GATE_SOURCE, gm.GATE_GRAVE_SOURCE):
            self.assertEqual(sorted(source), list(source), "bars are copied in printed order")
            self.assertEqual(len(source), len(set(source)), "no printed bar is copied twice")

    def test_fermatas_and_ties_point_at_printed_bars(self):
        for index in gm.GATE_GRAVE_FERMATAS:
            self.assertEqual(1, len(gm.GATE_GRAVE[index]), "a fermata sits on a whole-note bar")
        for index in gm.GATE_GRAVE_TIED:
            self.assertEqual(gm.GATE_GRAVE[index - 1], gm.GATE_GRAVE[index], "a tie joins equal notes")


class KeyTests(unittest.TestCase):
    def test_the_copied_melody_is_diatonic_to_e_flat_major(self):
        self.assertEqual((-3, False), gm.GATE_KEY)
        outside = {p % 12 for p in pitches_of(gm.GATE_MELODY + gm.GATE_GRAVE)} - E_FLAT_MAJOR
        self.assertEqual(set(), outside, "the edition prints no accidental in the copied voice")

    def test_theme_and_grave_open_on_the_tonic_and_the_piece_ends_on_it(self):
        self.assertEqual(gm.GATE_TONIC_PC, pitches_of(gm.GATE_MELODY)[0] % 12)
        self.assertEqual(gm.GATE_TONIC_PC, pitches_of(gm.GATE_GRAVE)[0] % 12)
        self.assertEqual(gm.GATE_TONIC_PC, pitches_of(gm.GATE_GRAVE)[-1] % 12)

    def test_the_theme_is_restated_where_the_edition_restates_it(self):
        # bars 9-10 and 12 repeat bars 1-2 and 4; bars 7-8 repeat 5-6
        for a, b in ((0, 8), (1, 9), (3, 11), (4, 6), (5, 7)):
            self.assertEqual(gm.GATE_MELODY[a], gm.GATE_MELODY[b])

    def test_our_harmony_agrees_with_the_printed_melody_at_every_chord_change(self):
        for part, bars, harmony in (("theme", gm.GATE_MELODY, gm.GATE_HARMONY),
                                    ("grave", gm.GATE_GRAVE, gm.GATE_GRAVE_HARMONY)):
            for number, (bar, chords) in enumerate(zip(bars, harmony), start=1):
                events = [(o, ps) for ps, o, _b, g in gm._events(bar) if not g]
                for at, _beats, voicing, root in chords:
                    with self.subTest(part=part, bar=number, beat=at):
                        sounding = [ps for o, ps in events if o <= at][-1]
                        tones = {gm.pitch(n) % 12 for n in voicing + (root,)}
                        self.assertIn(sounding[0] % 12, tones)


class FileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path, cls.seconds, _size = gm.generate("gate", Path(cls.tmp.name), None, quiet=True)
        cls.info = midi_inspect.parse(path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_clean_file_of_the_planned_length(self):
        self.assertEqual(0, self.info["hanging"], "a hanging note drones on")
        self.assertGreater(self.info["notes"], 0)
        self.assertAlmostEqual(EXPECTED_SECONDS, self.seconds, places=3)
        self.assertAlmostEqual(EXPECTED_SECONDS, self.info["seconds"], places=2)

    def test_the_printed_key_and_metre_are_in_the_file(self):
        self.assertEqual(["-3 major"], self.info["key_sigs"])
        self.assertEqual(["4/4"], self.info["time_sigs"])
        self.assertEqual([gm.GATE_GRAVE_BPM, gm.GATE_RIT_BPM, gm.GATE_TEMPO_BPM],
                         self.info["bpm"])

    def test_nothing_is_re_struck_while_it_still_sounds(self):
        tracks, _end = gm.build_gate(gm.GATE_TEMPO_BPM)
        sounding = {}
        for tick, _o, _s, payload in note_events(tracks):
            kind, key = payload[0] & 0xF0, (payload[0] & 0x0F, payload[1])
            if kind == gm.STATUS_NOTE_ON and payload[2] > 0:
                self.assertEqual(0, sounding.get(key, 0), f"re-struck at tick {tick}: {key}")
                sounding[key] = 1
            elif kind == gm.STATUS_NOTE_OFF:
                sounding[key] = 0

    def test_the_cue_ends_and_its_last_bar_is_silent(self):
        tracks, end_beat = gm.build_gate(gm.GATE_TEMPO_BPM)
        end_tick = round(end_beat * gm.TICKS_PER_BEAT)
        tail = end_tick - gm.GATE_TAIL_BARS * gm.GATE_BEATS_PER_BAR * gm.TICKS_PER_BEAT
        ons = [e[0] for e in note_events(tracks)
               if e[3][0] & 0xF0 == gm.STATUS_NOTE_ON and e[3][2] > 0]
        offs = [e[0] for e in note_events(tracks) if e[3][0] & 0xF0 == gm.STATUS_NOTE_OFF]
        self.assertEqual(0, min(ons), "the theme opens the file")
        self.assertLess(max(ons), tail, "the tail starts nothing")
        self.assertLessEqual(max(offs), end_tick)

    def test_the_draft_name_is_a_legal_lump_and_stays_out_of_assets(self):
        self.assertEqual(gm.GATE_LUMP, validate_lump_name(gm.GATE_LUMP))
        self.assertFalse((MUSIC_ASSETS / f"{gm.GATE_LUMP}.mid").exists(),
                         "a draft enters assets/ only on the CEO's approval")


class ExistingPiecesTests(unittest.TestCase):
    def test_adding_the_gate_changed_no_other_piece(self):
        # SHA-256 of every earlier piece as the generator wrote it before D54
        before = {
            "title": "6f74c09309e0910c7a660f268c69a181542a5c0bda17e4cb75bf6e86fa7eea28",
            "map01": "c0fce2821f33f72a1084dc8b080b39d906be977e65923a81bcb980b40624118b",
            "map01e": "d9e330fffbb7e259b698ec56a9fcf2ef59ce80cbbc876433c727200ea5c70341",
            "funeral": "e7dc22424b298fdd88a928d4800eb9d10831e58d11719cec3eb4e5fb203c8f09",
            "amur": "2854af3bea63d1118ad68b5792a26478ab4cef33b329f13e2e8597e1f68cd8ad",
        }
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            for key, digest in before.items():
                with self.subTest(piece=key):
                    path, _s, _b = gm.generate(key, Path(tmp), None, quiet=True)
                    self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())


class ProvenanceTests(unittest.TestCase):
    def test_both_documents_name_the_draft_and_the_score(self):
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        track = SOUNDTRACK.read_text(encoding="utf-8")
        for doc in (rights, track):
            self.assertIn(gm.GATE_LUMP, doc)
            self.assertIn("D54", doc)
        self.assertIn(SCORE_SHA256, rights)
        self.assertIn(SCORE.name, rights)

    def test_card_5_maps_every_copied_bar_to_the_edition(self):
        track = SOUNDTRACK.read_text(encoding="utf-8")
        card = track[track.index("#### Card 5"):]
        card = card[:card.index("\n### ")] if "\n### " in card else card
        for page, system, bar in gm.GATE_SOURCE + gm.GATE_GRAVE_SOURCE:
            self.assertIn(f"p. {page} · {system}", card)
        self.assertIn("1-16", card)
        self.assertIn("Grave", card)

    def test_the_downloaded_score_is_the_file_music_rights_records(self):
        if not SCORE.is_file():
            self.skipTest("work/audio/scores/ is gitignored and absent on this checkout")
        import hashlib
        self.assertEqual(SCORE_SHA256, hashlib.sha256(SCORE.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
