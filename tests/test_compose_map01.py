"""MAP01's new piece (D92): tools/audio/compose_map01.py.

Pure stdlib: builds the MIDIs in memory (milliseconds) and reads them back
with tools/audio/midi_edit.py. The renders are not tested here; they need
GZDoom's zmusic.dll and are measured in work/audio/map01_new/LEVELS.txt.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))

import compose_map01 as cm  # noqa: E402
import gen_music as gm  # noqa: E402
import midi_edit as me  # noqa: E402

HORN_CH = cm.CH["horns"]
BAR_TICKS = cm.BEATS_PER_BAR * gm.TICKS_PER_BEAT
LOOP_TICKS = cm.TOTAL_BARS * BAR_TICKS
# D_SDM01T's band (midi_inspect): the new piece keeps all of it and adds only timpani.
SDM01T_PROGRAMS = {39, 42, 44, 57, 60, 94, 98}


def parse(data: bytes):
    """-> (division, tracks, notes[(on tick, off tick, channel, pitch)], programs, open notes)."""
    _, div, tracks = me.read_smf(data)
    notes, programs, hanging = [], set(), 0
    for events in tracks:
        open_: dict[tuple[int, int], list[int]] = {}
        for tick, raw in events:
            kind = raw[0] & 0xF0
            if kind == 0xC0:
                programs.add((raw[0] & 0x0F, raw[1]))
            elif kind == 0x90 and raw[2] > 0:
                open_.setdefault((raw[0] & 0x0F, raw[1]), []).append(tick)
            elif kind == 0x80 or (kind == 0x90 and raw[2] == 0):
                stack = open_.get((raw[0] & 0x0F, raw[1]))
                if stack:
                    notes.append((stack.pop(0), tick, raw[0] & 0x0F, raw[1]))
        hanging += sum(len(v) for v in open_.values())
    return div, tracks, sorted(notes), programs, hanging


def shape(bar_notes) -> tuple:
    """A bar as (intervals, rhythm): transposition does not hide a copy."""
    sounding = [(gm.pitch(n), b) for n, b in bar_notes if n is not None]
    return (tuple(b - a for (a, _), (b, _) in zip(sounding, sounding[1:])),
            tuple(b for n, b in bar_notes))


class TestForm(unittest.TestCase):
    def test_harmony_covers_the_48_bars(self):
        self.assertEqual(len(cm.HARMONY), cm.TOTAL_BARS)
        for h in cm.HARMONY:
            for name in (h if isinstance(h, tuple) else (h,)):
                self.assertIn(name, cm.CHORDS)

    def test_every_melody_bar_is_one_4_4_bar(self):
        bars = cm.THEME + [b for _, b in cm.ADVANCE] + cm.LAMENT + cm.BUILD
        self.assertEqual(len(bars), cm.TOTAL_BARS)
        for i, bar in enumerate(bars):
            self.assertAlmostEqual(sum(b for _, b in bar), cm.BEATS_PER_BAR, msg=f"bar {i + 1}")

    def test_three_sections_back_to_back(self):
        spans = [cm.SECTION_A, cm.SECTION_B, cm.SECTION_C_LAMENT, cm.SECTION_C_BUILD]
        self.assertEqual([b for r in spans for b in r], list(range(cm.TOTAL_BARS)))
        self.assertEqual(len(cm.SECTIONS), 3)


class TestEachVariant(unittest.TestCase):
    def setUp(self):
        self.data = {v.lump: cm.midi_bytes(v) for v in cm.VARIANTS}

    def test_two_variants_n_and_n2(self):
        self.assertEqual([v.lump for v in cm.VARIANTS], ["D_SDM01N", "D_SDM01N2"])

    def test_deterministic(self):
        for v in cm.VARIANTS:
            self.assertEqual(cm.midi_bytes(v), self.data[v.lump], v.lump)

    def test_loop_is_60_to_120_seconds_and_every_track_ends_on_bar_48(self):
        for v in cm.VARIANTS:
            div, tracks, *_ = parse(self.data[v.lump])
            self.assertEqual(div, gm.TICKS_PER_BEAT)
            for events in tracks:
                self.assertEqual(events[-1][0], LOOP_TICKS, v.lump)
            self.assertTrue(60.0 <= cm.loop_seconds(v) <= 120.0, cm.loop_seconds(v))

    def test_the_tempo_in_the_file_is_the_variants(self):
        for v in cm.VARIANTS:
            _, tracks, *_ = parse(self.data[v.lump])
            tempos = [int.from_bytes(raw[3:6], "big") for ev in tracks for _, raw in ev
                      if raw[0] == me.META and raw[1] == 0x51]
            self.assertEqual(tempos, [round(60_000_000 / v.tempo_bpm)])

    def test_gm_programs_are_d_sdm01t_band_plus_timpani(self):
        for v in cm.VARIANTS:
            _, _, _, programs, _ = parse(self.data[v.lump])
            used = {p for _, p in programs}
            self.assertEqual(used, SDM01T_PROGRAMS | {gm.GM_TIMPANI}, v.lump)
            self.assertEqual(len(programs), len(used), "one program per channel, set once")

    def test_no_hanging_notes_and_nothing_past_the_loop(self):
        for v in cm.VARIANTS:
            _, tracks, notes, _, hanging = parse(self.data[v.lump])
            self.assertEqual(hanging, 0, v.lump)
            self.assertTrue(notes)
            for on, off, ch, p in notes:
                self.assertLess(on, off)
                self.assertLess(off, LOOP_TICKS, f"{v.lump}: ch {ch} note {p} ends on/after the seam")
            for events in tracks:            # End of Track is the last event: no note-off after it
                eot = [i for i, (_, raw) in enumerate(events) if raw[0] == me.META and raw[1] == me.META_END_OF_TRACK]
                self.assertEqual(eot, [len(events) - 1])

    def test_the_melody_starts_by_bar_4(self):
        for v in cm.VARIANTS:
            _, _, notes, _, _ = parse(self.data[v.lump])
            first = min(on for on, _, ch, _ in notes if ch == HORN_CH)
            self.assertLess(first, 4 * BAR_TICKS)
            self.assertEqual(first, 0, "in fact on the downbeat of bar 1")

    def test_horns_sing_in_every_section(self):
        for v in cm.VARIANTS:
            _, _, notes, _, _ = parse(self.data[v.lump])
            bars = {on // BAR_TICKS for on, _, ch, _ in notes if ch == HORN_CH}
            for _, _, start in cm.SECTIONS:
                self.assertIn(start, bars)

    def test_the_rhythmic_bed_never_stops(self):
        """Every beat of the loop has a bass-channel attack (the ostinato)."""
        for v in cm.VARIANTS:
            _, _, notes, _, _ = parse(self.data[v.lump])
            beats = {on // gm.TICKS_PER_BEAT for on, _, ch, _ in notes if ch == cm.CH["bass"]}
            self.assertEqual(beats, set(range(cm.TOTAL_BARS * cm.BEATS_PER_BAR)), v.lump)

    def test_variants_play_the_same_horn_notes(self):
        horn = {}
        for v in cm.VARIANTS:
            _, _, notes, _, _ = parse(self.data[v.lump])
            horn[v.lump] = [(on, p) for on, _, ch, p in notes if ch == HORN_CH]
        self.assertEqual(horn["D_SDM01N"], horn["D_SDM01N2"])

    @unittest.skipUnless((cm.OUT_DIR / "D_SDM01N.mid").is_file(), "work/audio is not on this machine")
    def test_the_files_on_disk_are_this_generator_s(self):
        for v in cm.VARIANTS:
            path = cm.OUT_DIR / f"{v.lump}.mid"
            if path.is_file():
                self.assertEqual(path.read_bytes(), self.data[v.lump], v.lump)


class TestOriginal(unittest.TestCase):
    """New material: no bar of three or more notes repeats a bar of D_SDM01E's
    horn lines (the source of D_SDM01T) or of its title theme, even transposed."""

    def test_no_bar_copies_d_sdm01e_or_the_title(self):
        old = [gm.MAP01E_LAMENT_HORN, [[n] for n in gm.MAP01E_B_HORN], [[n] for n in gm.MAP01E_C_HORN]]
        old_shapes = {shape(bar) for group in old for bar in group if len(bar) >= 3}
        new = cm.THEME + [b for _, b in cm.ADVANCE] + cm.LAMENT + cm.BUILD
        for i, bar in enumerate(new):
            if sum(1 for n, _ in bar if n is not None) >= 3:
                self.assertNotIn(shape(bar), old_shapes, f"bar {i + 1}")

    def test_no_four_note_figure_of_the_title_or_the_lament_reappears(self):
        """Any 4 consecutive notes, as (intervals, rhythm), across bar lines."""
        def windows(seq, n=4):
            out = set()
            for i in range(len(seq) - n + 1):
                w = seq[i:i + n]
                p = [gm.pitch(name) for name, _ in w]
                out.add((tuple(b - a for a, b in zip(p, p[1:])), tuple(b for _, b in w)))
            return out
        flat = lambda bars: [x for bar in bars for x in bar if x[0] is not None]  # noqa: E731
        old = windows(list(gm.TITLE_THEME)) | windows(flat(gm.MAP01E_LAMENT_HORN))
        new = windows(flat(cm.THEME + [b for _, b in cm.ADVANCE] + cm.LAMENT + cm.BUILD))
        self.assertEqual(new & old, set())

    def test_no_two_bar_span_copies_the_lament_rhythm_and_contour(self):
        old = gm.MAP01E_LAMENT_HORN
        old_pairs = {shape(a + b) for a, b in zip(old, old[1:])}
        new = cm.THEME + [b for _, b in cm.ADVANCE] + cm.LAMENT + cm.BUILD
        for i, (a, b) in enumerate(zip(new, new[1:])):
            self.assertNotIn(shape(a + b), old_pairs, f"bars {i + 1}-{i + 2}")


if __name__ == "__main__":
    unittest.main()
