"""Episode 3's draft music (D112): tools/audio/compose_episode3.py.

Pure stdlib: builds the ten MIDIs in memory and reads them back with
tools/audio/midi_edit.py. Renders are not tested here (they need GZDoom's
zmusic.dll; levels are in work/audio/episode3/render/LEVELS.txt).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))

import compose_episode2 as e2  # noqa: E402
import compose_episode3 as e3  # noqa: E402
import midi_edit as me  # noqa: E402

SONGS = e3.all_songs()


class TestOriginality(unittest.TestCase):
    def test_self_check_is_clean(self):
        self.assertEqual(e3.self_check(SONGS), [])

    def test_the_scan_reads_episodes_1_and_2(self):
        refs = set(e3.reference_ngrams().values())
        for lump in ("D_SDM1N2", "D_SDINTL", "D_SDTITL", "D_SDM04A", "D_SDM06B", "D_SDBS6A"):
            self.assertIn(lump, refs)

    def test_the_scan_catches_a_copied_phrase(self):
        # Episode 2's MAP04 theme, as if pasted into Episode 3, is found in its installed MIDI.
        hits = e3.quote_hits({"PASTED": e2.M4_THEME})
        self.assertTrue(hits and "D_SDM04A" in hits[0], hits)

    def test_the_scan_catches_a_transposed_copy(self):
        shifted = [[(e3_transpose(n, 3), d) for n, d in bar] for bar in e2.M6_THEME]
        self.assertTrue(e3.quote_hits({"SHIFTED": shifted}))

    def test_a_scale_is_not_a_quotation(self):
        self.assertEqual(e3.interval_ngrams([60, 62, 63, 65, 67, 68, 70, 72, 74]), set())

    def test_two_bar_shapes_ignore_transposition(self):
        a = e2.mel("C4:4 E4:4 G4:8 | F4:16")
        b = e2.mel("D4:4 F#4:4 A4:8 | G4:16")
        self.assertEqual(e3.shapes(a), e3.shapes(b))


def e3_transpose(name: str | None, semis: int) -> str | None:
    if name is None:
        return None
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    p = e3.pitch(name) + semis
    return f"{names[p % 12]}{p // 12 - 1}"


class TestPieces(unittest.TestCase):
    def test_ten_lumps_of_eight_characters(self):
        lumps = [v.lump for _, v, _ in SONGS]
        self.assertEqual(len(lumps), 10)
        self.assertEqual(len(set(lumps)), 10)
        for lump in lumps:
            self.assertLessEqual(len(lump), 8)
            self.assertTrue(lump.startswith("D_SD"))

    def test_midis_read_back_with_no_hanging_notes(self):
        for _, v, s in SONGS:
            _, div, tracks = me.read_smf(s.midi())
            open_notes = 0
            for events in tracks:
                held: dict[tuple[int, int], int] = {}
                for _, raw in events:
                    if len(raw) == 3 and raw[0] & 0xF0 == 0x90 and raw[2] > 0:
                        held[(raw[0] & 0x0F, raw[1])] = held.get((raw[0] & 0x0F, raw[1]), 0) + 1
                    elif len(raw) == 3 and (raw[0] & 0xF0 == 0x80 or (raw[0] & 0xF0 == 0x90 and raw[2] == 0)):
                        key = (raw[0] & 0x0F, raw[1])
                        if held.get(key):
                            held[key] -= 1
                open_notes += sum(held.values())
            self.assertEqual(open_notes, 0, v.lump)
            self.assertEqual(me.last_tick(tracks), s.bars * 4 * div, v.lump)

    def test_draft_tag_in_the_track_name(self):
        _, v, s = SONGS[0]
        self.assertIn(b"D112 draft", s.midi())
        self.assertNotIn(b"D104", s.midi())

    def test_the_boss_is_its_own_piece(self):
        boss = [s for k, _, s in SONGS if k == "BOSS9"]
        maps = [s for k, _, s in SONGS if k == "MAP09"]
        for b, m in zip(boss, maps):
            self.assertNotEqual(b.bpm, m.bpm)
            self.assertLess(b.seconds(), m.seconds())

    def test_one_recommendation_per_piece(self):
        for key in e3.PIECES:
            recs = [v.lump for k, v, _ in SONGS if k == key and v.lump in e3.RECOMMENDED]
            self.assertEqual(len(recs), 1, key)


class TestSheet(unittest.TestCase):
    def test_sheet_is_episode_3s(self):
        rows = [{"lump": v.lump, "key": k, "bpm": v.bpm, "label": v.label, "seconds": s.seconds(),
                 "sections": [(label, 0.0) for label, _ in s.sections]} for k, v, s in SONGS]
        html = e3.sheet_html(rows)
        self.assertIn("Episode 3", html)
        self.assertIn("../episode3/render/D_SDM07A.ogg", html)
        self.assertIn("D_SDM1N2", html)
        self.assertIn("../episode2/render/D_SDM06A.ogg", html)
        self.assertNotIn("Episode 2 ·", html)
        self.assertIn("Copy result", html)


if __name__ == "__main__":
    unittest.main()
