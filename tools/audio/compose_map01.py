#!/usr/bin/env python3
"""MAP01 (Zarya-7) -- a new original piece in the style of D_SDM01T (D92).

    .venv/Scripts/python.exe tools/audio/compose_map01.py            # MIDIs + renders
    .venv/Scripts/python.exe tools/audio/compose_map01.py --no-render
    .venv/Scripts/python.exe tools/audio/compose_map01.py --only D_SDM01N

Why this exists
---------------
D59 stopped all composing. D92 makes ONE explicit exception: the CEO rejected
Borodin for MAP01 ("muy tranqui, muy chill; no pega") and asked for a new
piece in the style of our own D_SDM01T -- the horn-led lament of D_SDM01E
(gen_music.py section 4b, cut at bar 49 by gen_enemy_alts.py) -- but with the
drive of a combat level. So: the same General MIDI band as D_SDM01T (synth
bass 39, cellos 42, tremolo strings 44, trombones 57, horns 60, halo pad 94,
crystal 98, GM drums) plus timpani 47, which the brief asks for by name; the
melody from bar 1 (no intro); a rhythmic bed that never stops; three
sections; a loop of 60-120 s whose seam lands on the theme's downbeat.

ORIGINAL COMPOSITION (sound-designer, 2026-10-20). No phrase is taken from
D_SDM01/E/T (tests/test_compose_map01.py compares the bars) nor from any
other work: nothing is quoted, folk or otherwise, so there is no rights
question beyond our own (CC BY-NC-SA 4.0 with the rest of the assets, D15).

Form (48 bars of 4/4, D minor):
  A  "Tema"    1-16  horns state the theme on the downbeat of bar 1, over a
                     galloping synth bass, cellos chugging eighths, timpani
                     on 1 and 3 and a march snare. a a' b a'' (4+4+4+4).
  B  "Avance" 17-32  F major and back: trombones call, horns answer, then
                     both together in octaves; tremolo strings; snare
                     eighths; the Neapolitan Eb turns it back to A.
  C  "Lamento 33-48  the horn sings a slower line over a lighter but
     y vuelta"       unbroken bed (bass eighths, timpani, kick) for 12 bars;
                     bars 45-48 climb on the dominant A with a snare and
                     timpani roll, and the loop crashes back into bar 1.

Two variants (the notes are the same; only these knobs differ):
  D_SDM01N   116 BPM (1:39 loop), horns alone on the theme -- closest to
             D_SDM01T's colour.
  D_SDM01N2  128 BPM (1:30 loop), heavier: trombones double the theme an
             octave below from bar 9, the snare plays eighths in A as well
             as B, the kick doubles in B.

Output: work/audio/D_SDM01N.mid, D_SDM01N2.mid; renders (GZDoom's own
zmusic.dll + gzdoom.sf2 as a library, no engine, D26) with 10 s past the
loop point in work/audio/map01_new/, plus LEVELS.txt comparing loudness
with D_SDM01T, D_SDFUNR and D_SDGATE rendered the same way. Nothing goes to
assets/ (install needs the CEO's OK).
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_music as gm  # noqa: E402
from gen_music import (  # noqa: E402
    CC_PAN, CC_REVERB, CC_VOLUME, DRUM_BASS, DRUM_CRASH, DRUM_LOW_FLOOR_TOM,
    DRUM_RIDE, DRUM_SNARE, SMF_FORMAT_MULTITRACK, SMF_HEADER_CHUNK,
    SMF_HEADER_LENGTH, TICKS_PER_BEAT, Track, pitch)

PROJECT_ROOT = gm.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "audio"
RENDER_DIR = OUT_DIR / "map01_new"
SEAM_PREVIEW_S = 10.0                 # rendered past the loop point: the seam is heard

BEATS_PER_BAR = 4
KEY = (-1, True)                      # one flat, minor: D minor

# -- General MIDI programs (0-based) -----------------------------------------------------
GM_SYNTH_BASS_2 = gm.GM_SYNTH_BASS_2  # 39, D_SDM01T's pulse
GM_CELLO = 42
GM_TREMOLO_STRINGS = gm.GM_TREMOLO_STRINGS  # 44
GM_TIMPANI = gm.GM_TIMPANI            # 47
GM_TROMBONE = gm.GM_TROMBONE          # 57
GM_FRENCH_HORN = gm.GM_FRENCH_HORN    # 60
GM_PAD_HALO = gm.GM_PAD_HALO          # 94
GM_FX_CRYSTAL = gm.GM_FX_CRYSTAL      # 98

CH = {"bass": 0, "pad": 1, "strings": 2, "trombones": 3, "signal": 4,
      "horns": 5, "cellos": 6, "timpani": 7}
PROGRAMS = {"bass": GM_SYNTH_BASS_2, "pad": GM_PAD_HALO, "strings": GM_TREMOLO_STRINGS,
            "trombones": GM_TROMBONE, "signal": GM_FX_CRYSTAL, "horns": GM_FRENCH_HORN,
            "cellos": GM_CELLO, "timpani": GM_TIMPANI}
# (CC7 volume, CC10 pan). Horns a touch left, as in D_SDM01E; trombones right.
# Balance measured on stems (melody = horns + trombones, bed = the rest): D_SDM01T has
# its horns ~1 dB RMS over the bed; these put ours 1.4-3.1 dB over it (A 2.3, B 1.4, C 3.1).
MIX = {"bass": (98, 64), "pad": (58, 64), "strings": (72, 84), "trombones": (98, 88),
       "signal": (52, 100), "horns": (116, 44), "cellos": (82, 30), "timpani": (92, 70)}
DRUM_VOLUME = 94
REVERB = 72                           # as D_SDM01E
# Every CC7 above is multiplied by this. Measured (LEVELS.txt): at 1.0 the loop sat
# ~2 dB RMS and ~3 dB (loudest 3 s) over D_SDGATE, the loudest approved combat cue;
# FluidSynth's CC7 gain is ~40*log10(cc/127) dB, so 0.88 takes ~2.2 dB off.
VOLUME_SCALE = 0.88

# -- Form --------------------------------------------------------------------------------
SECTION_A = range(0, 16)              # 0-based bars
SECTION_B = range(16, 32)
SECTION_C_LAMENT = range(32, 44)
SECTION_C_BUILD = range(44, 48)
TOTAL_BARS = 48
SECTIONS = (("A", "Tema", SECTION_A.start), ("B", "Avance", SECTION_B.start),
            ("C", "Lamento y vuelta", SECTION_C_LAMENT.start))

# -- Harmony: one or two chords per bar --------------------------------------------------
# name -> (bass pitch class, chord tones as pitch classes)
PC = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8,
      "A": 9, "Bb": 10, "B": 11}
CHORDS = {
    "Dm": ("D", ("D", "F", "A")), "Dm/F": ("F", ("D", "F", "A")),
    "C": ("C", ("C", "E", "G")), "C/E": ("E", ("C", "E", "G")),
    "Gm": ("G", ("G", "Bb", "D")), "A": ("A", ("A", "C#", "E")),
    "A7": ("A", ("A", "C#", "E", "G")), "F": ("F", ("F", "A", "C")),
    "F/A": ("A", ("F", "A", "C")), "Bb": ("Bb", ("Bb", "D", "F")),
    "Eb": ("Eb", ("Eb", "G", "Bb")), "Bb/A": ("A", ("Bb", "D", "F")),
}
# A bar is a chord name, or two names for two half-bar chords.
HARMONY = [
    # A: a (1-4), a' (5-8), b (9-12), a'' (13-16)
    "Dm", "C", "Gm", "A",
    "Dm", "Gm", ("C", "A7"), "Dm",
    "F", "Bb", "Eb", "A",
    "Dm", "Gm", ("Bb", "A7"), "Dm",
    # B: trombone call / horn answer, then tutti; the Neapolitan Eb turns it to A
    "F", "C", "Dm", "Bb",
    "F", "C/E", "Dm", "A",
    "Bb", "F/A", "Gm", "Dm",
    "Bb", "Gm", "Eb", "A7",
    # C: the lament (33-44), then the climb on the dominant (45-48)
    "Dm", "Bb", "Gm", "A",
    "Dm/F", "Eb", "Gm", "A7",
    "Bb", "Gm", "Eb", "A",
    "Bb/A", "A", "Bb/A", "A7",
]

# -- Melodies: one list of (pitch or None, beats) per bar; every bar sums to 4 ---------
THEME = [  # horns, section A
    [("D4", 1.0), ("A4", 1.5), ("G4", 0.5), ("F4", 1.0)],            # 1  a
    [("E4", 0.5), ("F4", 0.5), ("G4", 1.0), ("A4", 2.0)],
    [("Bb4", 1.5), ("A4", 0.5), ("G4", 1.0), ("F4", 1.0)],
    [("E4", 3.0), ("A3", 1.0)],
    [("D4", 1.0), ("A4", 1.5), ("G4", 0.5), ("F4", 1.0)],            # 5  a'
    [("G4", 0.5), ("A4", 0.5), ("Bb4", 1.0), ("D5", 2.0)],
    [("C5", 1.5), ("Bb4", 0.5), ("A4", 1.0), ("G4", 0.5), ("E4", 0.5)],
    [("D4", 3.0), (None, 1.0)],
    [("F4", 1.0), ("C5", 1.5), ("Bb4", 0.5), ("A4", 1.0)],           # 9  b
    [("Bb4", 0.5), ("C5", 0.5), ("D5", 1.0), ("F5", 2.0)],
    [("Eb5", 1.5), ("D5", 0.5), ("C5", 1.0), ("Bb4", 1.0)],
    [("A4", 2.0), ("C#5", 1.0), ("E5", 1.0)],
    [("D5", 1.5), ("A4", 0.5), ("F4", 1.0), ("D4", 1.0)],            # 13 a'' (inverted)
    [("G4", 1.0), ("Bb4", 1.0), ("A4", 1.0), ("G4", 1.0)],
    [("F4", 1.0), ("E4", 0.5), ("F4", 0.5), ("G4", 1.0), ("C#4", 1.0)],
    [("D4", 2.0), (None, 2.0)],
]
# Section B: who plays each bar's tune ("tbn" call, "hrn" answer, "tutti").
ADVANCE = [
    ("tbn", [("C4", 0.75), ("C4", 0.25), ("F4", 1.0), ("A4", 1.5), ("G4", 0.5)]),   # 17
    ("tbn", [("G4", 1.5), ("E4", 0.5), ("C4", 2.0)]),
    ("hrn", [("D5", 1.0), ("C5", 0.5), ("A4", 0.5), ("F4", 1.0), ("A4", 1.0)]),
    ("hrn", [("Bb4", 1.5), ("A4", 0.5), ("F4", 2.0)]),
    ("tbn", [("C4", 0.75), ("C4", 0.25), ("F4", 1.0), ("C5", 1.5), ("Bb4", 0.5)]),  # 21
    ("tbn", [("G4", 1.0), ("A4", 0.5), ("G4", 0.5), ("E4", 2.0)]),
    ("hrn", [("F4", 0.5), ("G4", 0.5), ("A4", 1.0), ("D5", 1.0), ("F5", 1.0)]),
    ("hrn", [("E5", 2.0), ("C#5", 1.0), ("A4", 1.0)]),
    ("tutti", [("D5", 1.5), ("C5", 0.5), ("Bb4", 1.0), ("F4", 1.0)]),                # 25
    ("tutti", [("C5", 1.5), ("Bb4", 0.5), ("A4", 1.0), ("F4", 1.0)]),
    ("tutti", [("Bb4", 1.0), ("A4", 0.5), ("Bb4", 0.5), ("D5", 2.0)]),
    ("tutti", [("A4", 2.0), ("F4", 1.0), ("D4", 1.0)]),
    ("tutti", [("F4", 1.0), ("Bb4", 1.0), ("D5", 1.0), ("F5", 1.0)]),                # 29
    ("tutti", [("D5", 1.5), ("Bb4", 0.5), ("G4", 2.0)]),
    ("tutti", [("G4", 0.5), ("Bb4", 0.5), ("Eb5", 1.0), ("D5", 1.0), ("C5", 1.0)]),
    ("tutti", [("E5", 2.0), ("C#5", 1.0), ("A4", 1.0)]),
]
LAMENT = [  # horn solo, section C bars 33-44
    [("A4", 1.0), ("D5", 2.0), ("C5", 1.0)],
    [("Bb4", 1.5), ("A4", 0.5), ("F4", 2.0)],
    [("G4", 1.0), ("A4", 1.0), ("Bb4", 1.0), ("D5", 1.0)],
    [("C#5", 3.0), ("A4", 1.0)],
    [("F5", 1.5), ("E5", 0.5), ("D5", 1.0), ("A4", 1.0)],
    [("Eb5", 2.0), ("D5", 0.5), ("C5", 0.5), ("Bb4", 1.0)],
    [("Bb4", 1.5), ("A4", 0.5), ("G4", 1.0), ("D4", 1.0)],
    [("A4", 2.0), ("G4", 1.0), ("E4", 1.0)],
    [("F4", 1.0), ("Bb4", 1.0), ("D5", 1.5), ("C5", 0.5)],
    [("D5", 1.0), ("Bb4", 1.5), ("G4", 0.5), ("A4", 1.0)],
    [("G4", 1.5), ("F4", 0.5), ("Eb4", 1.0), ("G4", 1.0)],
    [("A4", 4.0)],
]
BUILD = [  # horns (and trombones an octave below), bars 45-48: the climb back to bar 1
    [("A4", 0.75), ("A4", 0.25), ("Bb4", 1.0), ("A4", 2.0)],
    [("C#5", 0.75), ("C#5", 0.25), ("D5", 1.0), ("C#5", 2.0)],
    [("E5", 0.75), ("E5", 0.25), ("F5", 1.0), ("E5", 2.0)],
    [("E5", 1.0), ("C#5", 1.0), ("A4", 2.0)],
]
SIGNALS = [(35, 1.0, "A5", 2.5), (39, 1.0, "G5", 2.5), (43, 0.0, "E5", 3.0)]  # (bar, beat, pitch, beats)

# -- Articulation and dynamics ------------------------------------------------------------
LEGATO, MARCATO, CHUG = 0.97, 0.86, 0.55
VEL_THEME, VEL_ADVANCE, VEL_LAMENT, VEL_BUILD = 96, 94, 86, 104
VEL_HORN_HOLD = 58                    # horns holding chord tones under the trombone call
VEL_PAD, VEL_STRINGS, VEL_SIGNAL = 44, 60, 52
VEL_BASS, VEL_CELLO, VEL_TIMPANI = 96, 78, 92
CELLO_ACCENTS = (84, 58, 66, 58, 80, 58, 66, 62)          # the eighths of one bar


@dataclass(frozen=True)
class Variant:
    lump: str
    tempo_bpm: float
    label: str
    trombones_double_theme: bool      # A from bar 9: trombones an octave under the horns
    snare_eighths_in_a: bool
    kick_doubled_in_b: bool


VARIANTS = (
    Variant("D_SDM01N", 116.0, "116 BPM, las trompas solas en el tema", False, False, False),
    Variant("D_SDM01N2", 128.0, "128 BPM, más pesada: trombones doblan el tema, más caja y bombo",
            True, True, True),
)
VARIANT_BY_LUMP = {v.lump: v for v in VARIANTS}


# -- Helpers ------------------------------------------------------------------------------

def bar_chords(bar: int) -> list[tuple[float, float, str]]:
    """-> [(start beat in bar, beats, chord name)] for a 0-based bar."""
    h = HARMONY[bar]
    if isinstance(h, tuple):
        return [(0.0, 2.0, h[0]), (2.0, 2.0, h[1])]
    return [(0.0, 4.0, h)]


def in_range(pc_name: str, low: int) -> int:
    """The pitch of this pitch class in [low, low + 12)."""
    return low + (PC[pc_name] - low) % 12


def voicing(chord: str, low: int) -> list[int]:
    return sorted(in_range(n, low) for n in CHORDS[chord][1])


def root(chord: str, low: int) -> int:
    return in_range(CHORDS[chord][0], low)


def fifth_of(chord: str, low: int) -> int:
    return in_range(CHORDS[chord][1][2], low)


def line(track: Track, channel: int, notes, start: float, velocity: int,
         articulation: float = LEGATO, transpose: int = 0) -> float:
    pos = start
    for name, beats in notes:
        if name is not None:
            # the first note of a bar leans a little; the rest follow the line
            accent = 6 if pos == start else 0
            track.note(channel, pitch(name) + transpose, pos, beats * articulation, velocity + accent)
        pos += beats
    return pos


def beat_of(bar: int) -> float:
    return float(bar * BEATS_PER_BAR)


# -- The builder ----------------------------------------------------------------------------

def build(variant: Variant) -> tuple[list[Track], float]:
    """All the tracks of one variant, and the loop's end beat."""
    names = ["bass", "pad", "strings", "trombones", "signal", "horns", "cellos", "timpani"]
    tr = {k: Track(k) for k in names}
    drums = Track("percussion")
    tracks = [tr[k] for k in names] + [drums]

    first = tr["bass"]
    first.track_name(f"Soviet Doom - {variant.lump} (MAP01 Zarya-7, D92 draft, original)")
    first.tempo(0, variant.tempo_bpm)
    first.time_signature(0, 4, 4)
    first.key_signature(0, *KEY)
    for k in names:
        if k != "bass":
            tr[k].track_name()
        vol, pan = MIX[k]
        tr[k].program(0, CH[k], PROGRAMS[k])
        tr[k].control(0, CH[k], CC_VOLUME, round(vol * VOLUME_SCALE))
        tr[k].control(0, CH[k], CC_PAN, pan)
        tr[k].control(0, CH[k], CC_REVERB, REVERB)
    drums.track_name()
    drums.control(0, gm.DRUM_CHANNEL, CC_VOLUME, round(DRUM_VOLUME * VOLUME_SCALE))
    drums.control(0, gm.DRUM_CHANNEL, CC_REVERB, REVERB - 20)

    horns, tbn, cel, bas, timp = tr["horns"], tr["trombones"], tr["cellos"], tr["bass"], tr["timpani"]

    # -- Melody --------------------------------------------------------------
    for i, bar_notes in enumerate(THEME):
        b = SECTION_A.start + i
        line(horns, CH["horns"], bar_notes, beat_of(b), VEL_THEME, MARCATO if i % 4 else LEGATO)
        if variant.trombones_double_theme and i >= 8:
            line(tbn, CH["trombones"], bar_notes, beat_of(b), VEL_THEME - 14, MARCATO, -12)
    for i, (who, bar_notes) in enumerate(ADVANCE):
        b = SECTION_B.start + i
        if who in ("tbn", "tutti"):
            line(tbn, CH["trombones"], bar_notes, beat_of(b), VEL_ADVANCE - (8 if who == "tutti" else 0),
                 MARCATO, -12 if who == "tutti" else 0)
        if who in ("hrn", "tutti"):
            line(horns, CH["horns"], bar_notes, beat_of(b), VEL_ADVANCE, MARCATO)
        if who == "tbn":                     # horns hold the chord's upper tones under the call
            for start, beats, chord in bar_chords(b):
                for p in voicing(chord, pitch("F4"))[1:]:
                    horns.note(CH["horns"], p, beat_of(b) + start, beats * LEGATO, VEL_HORN_HOLD)
    for i, bar_notes in enumerate(LAMENT):
        line(horns, CH["horns"], bar_notes, beat_of(SECTION_C_LAMENT.start + i), VEL_LAMENT, LEGATO)
    for i, bar_notes in enumerate(BUILD):
        b = SECTION_C_BUILD.start + i
        line(horns, CH["horns"], bar_notes, beat_of(b), VEL_BUILD - 8 + 4 * i, MARCATO)
        line(tbn, CH["trombones"], bar_notes, beat_of(b), VEL_BUILD - 14 + 4 * i, MARCATO, -12)

    # -- Trombone punctuation in A: the cadence bars ---------------------------
    if not variant.trombones_double_theme:
        for b in (3, 7, 11, 15):
            for start, beats, chord in bar_chords(b):
                tbn.chord(CH["trombones"], voicing(chord, pitch("D3")), beat_of(b) + start, 0.45, 82)
    else:
        for b in (3, 7):
            for start, beats, chord in bar_chords(b):
                tbn.chord(CH["trombones"], voicing(chord, pitch("D3")), beat_of(b) + start, 0.45, 82)

    # -- Pad: every bar, the cold colour of the cosmodrome ---------------------
    for b in range(TOTAL_BARS):
        for start, beats, chord in bar_chords(b):
            tr["pad"].chord(CH["pad"], voicing(chord, pitch("D3")), beat_of(b) + start,
                            beats * LEGATO, VEL_PAD)

    # -- Tremolo strings: B, the end of the lament, the climb --------------------
    for b in list(SECTION_B) + list(range(40, 44)) + list(SECTION_C_BUILD):
        swell = 10 if b in SECTION_C_BUILD else (-8 if b < 44 and b >= 40 else 0)
        for start, beats, chord in bar_chords(b):
            for p in voicing(chord, pitch("A3")):
                tr["strings"].note(CH["strings"], p, beat_of(b) + start, beats * LEGATO,
                                   VEL_STRINGS + swell)

    # -- Signals: the far-off crystal of D_SDM01T, three times in the lament ---
    for b, at, name, beats in SIGNALS:
        tr["signal"].note(CH["signal"], pitch(name), beat_of(b) + at, beats, VEL_SIGNAL)

    # -- The bed: bass, cellos, timpani ------------------------------------------
    for b in range(TOTAL_BARS):
        base = beat_of(b)
        lament = b in SECTION_C_LAMENT
        build_bar = b in SECTION_C_BUILD
        for start, beats, chord in bar_chords(b):
            r_bass = root(chord, pitch("E1"))
            r_cel = root(chord, pitch("C2"))
            r_tim = root(chord, pitch("E2"))
            f_tim = fifth_of(chord, pitch("E2"))
            halves = int(beats // 2)
            for h in range(halves):
                t0 = base + start + 2 * h
                if lament or build_bar:
                    # straight eighths: the pulse keeps going under the song
                    for e in range(4):
                        v = VEL_BASS - (26 if lament else 6) + (8 if e == 0 else 0) + (4 * (b - 44) if build_bar else 0)
                        bas.note(CH["bass"], r_bass, t0 + 0.5 * e, 0.5 * MARCATO, v)
                else:
                    # the gallop on the strong beat, octave and fifth on the weak one
                    for off, ln, p, dv in ((0.0, 0.5, r_bass, 8), (0.5, 0.25, r_bass, -10),
                                           (0.75, 0.25, r_bass, -6), (1.0, 0.5, r_bass + 12, -4),
                                           (1.5, 0.5, r_bass + 7, -8)):
                        bas.note(CH["bass"], p, t0 + off, ln * MARCATO, VEL_BASS + dv)
                # cellos
                if lament:
                    tones = voicing(chord, pitch("D3"))
                    cel.note(CH["cellos"], tones[1 if h == 0 else 0], t0, 2.0 * LEGATO, VEL_CELLO - 6)
                else:
                    for e in range(4):
                        p = r_cel + 12 if e == 3 else r_cel
                        acc = CELLO_ACCENTS[(4 * h + e) % 8] + (6 * (b - 44) if build_bar else 0)
                        cel.note(CH["cellos"], p, t0 + 0.5 * e, 0.5 * CHUG, acc)
                # timpani
                if build_bar:
                    if b >= 46:                                   # the roll: sixteenths, rising
                        for s in range(8):
                            v = 62 + int(44 * ((b - 46) * 16 + 8 * h + s) / 31)
                            timp.note(CH["timpani"], r_tim, t0 + 0.25 * s, 0.24, v)
                    else:
                        for e in range(4):
                            timp.note(CH["timpani"], r_tim, t0 + 0.5 * e, 0.45, 70 + 6 * (b - 44) + 4 * e)
                elif lament:
                    if h == 0:
                        timp.note(CH["timpani"], r_tim, t0, 1.5, VEL_TIMPANI - 26)
                else:
                    timp.note(CH["timpani"], r_tim if h == 0 else f_tim, t0, 1.5, VEL_TIMPANI - (0 if h == 0 else 12))
        if b in SECTION_A or b in SECTION_B:
            if b % 4 == 3 and b not in (15, 31):                  # the timpani answer the cadence
                for s, v in ((3.0, 80), (3.5, 86)):
                    timp.note(CH["timpani"], root(bar_chords(b)[-1][2], pitch("E2")), base + s, 0.4, v)

    # -- Percussion ----------------------------------------------------------------
    hit = drums.hit
    for b in range(TOTAL_BARS):
        base = beat_of(b)
        if b in SECTION_A or b in SECTION_B:
            in_b = b in SECTION_B
            hit(DRUM_BASS, base, 104)
            hit(DRUM_BASS, base + 2.0, 92)
            if in_b and variant.kick_doubled_in_b:
                hit(DRUM_BASS, base + 1.0, 80)
                hit(DRUM_BASS, base + 3.0, 80)
            hit(DRUM_SNARE, base + 1.0, 88)
            hit(DRUM_SNARE, base + 3.0, 94)
            if in_b or variant.snare_eighths_in_a:
                for off in (0.5, 1.5, 2.5):
                    hit(DRUM_SNARE, base + off, 44 if not in_b else 50)
                hit(DRUM_RIDE, base, 58)
                hit(DRUM_RIDE, base + 2.0, 52)
            if b % 4 == 3:                                        # the fill into the next phrase
                for k, off in enumerate((3.25, 3.5, 3.75)):
                    hit(DRUM_SNARE, base + off, 70 + 10 * k)
            else:
                hit(DRUM_SNARE, base + 3.75, 52)
            if b in (0, 8, 16, 24):
                hit(DRUM_CRASH, base, 100 if b != 8 else 86)
        elif b in SECTION_C_LAMENT:
            hit(DRUM_BASS, base, 84)
            hit(DRUM_BASS, base + 2.0, 72)
            hit(DRUM_LOW_FLOOR_TOM, base + 1.0, 48)
            hit(DRUM_LOW_FLOOR_TOM, base + 3.0, 54)
            if b in (32, 40):
                hit(DRUM_CRASH, base, 70)
        else:                                                     # the climb, 45-48
            k = b - SECTION_C_BUILD.start
            for q in range(4):
                hit(DRUM_BASS, base + q, 86 + 4 * k)
            if k < 2:
                for e in range(8):
                    hit(DRUM_SNARE, base + 0.5 * e, 54 + 8 * k + 3 * e)
            else:
                for s in range(16 if k == 2 else 15):              # stop one sixteenth short of the seam
                    hit(DRUM_SNARE, base + 0.25 * s, 66 + int(44 * ((k - 2) * 16 + s) / 31))
            if k == 0:
                hit(DRUM_CRASH, base, 84)
    return tracks, beat_of(TOTAL_BARS)


def midi_bytes(variant: Variant) -> bytes:
    tracks, end = build(variant)
    header = SMF_HEADER_CHUNK + struct.pack(">IHHH", SMF_HEADER_LENGTH, SMF_FORMAT_MULTITRACK,
                                            len(tracks), TICKS_PER_BEAT)
    return header + b"".join(t.to_bytes(end) for t in tracks)


def loop_seconds(variant: Variant) -> float:
    return TOTAL_BARS * BEATS_PER_BAR * 60.0 / variant.tempo_bpm


# -- Rendering and loudness -------------------------------------------------------------------

REFERENCES = {   # rendered the same way, for loudness: the approved D_SDM01T, and two OK pieces
    "D_SDM01T": OUT_DIR / "D_SDM01T.mid",
    "D_SDFUNR": PROJECT_ROOT / "assets" / "music" / "D_SDFUNR.mid",
    "D_SDGATE": PROJECT_ROOT / "assets" / "music" / "D_SDGATE.mid",
}


def measure(x, rate: int) -> dict:
    """Levels of a stereo float render: peak, mean RMS and the loudest 3 s window (dBFS)."""
    import numpy as np
    mono = x.mean(axis=1)
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    win = int(3.0 * rate)
    sq = np.cumsum(np.concatenate([[0.0], mono ** 2]))
    loud = float(np.sqrt(np.max(sq[win:] - sq[:-win]) / win)) if len(mono) > win else rms
    db = lambda v: 20 * np.log10(max(v, 1e-9))  # noqa: E731
    return {"peak": db(peak), "rms": db(rms), "loud3s": db(loud), "seconds": len(mono) / rate}


def render_all(lumps: list[str], out_dir: Path = RENDER_DIR) -> list[str]:
    import gen_enemy_alts as ea
    import gen_weapon_sfx as gws
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for lump in lumps:
        data = (OUT_DIR / f"{lump}.mid").read_bytes()
        secs = ea.seconds_of(data)
        x, rate = ea.zmusic_render(data, secs + SEAM_PREVIEW_S)
        lv = measure(x[: int(secs * rate)], rate)
        bar_s = secs / TOTAL_BARS
        lv["arc"] = {sec: measure(x[int(b0 * bar_s * rate): int(b1 * bar_s * rate)], rate)["rms"]
                     for sec, b0, b1 in (("A", 0, 16), ("B", 16, 32), ("C-lamento", 32, 44),
                                         ("C-subida", 44, 48))}
        ogg = gws.ogg_bytes(ea.stereo_wav(x, rate))
        if ogg is None:
            raise RuntimeError("ffmpeg is not on the PATH: no OGG")
        (out_dir / f"{lump}.ogg").write_bytes(ogg)
        rows.append((lump, secs, lv))
    for ref, path in REFERENCES.items():
        if not path.is_file():
            continue
        data = path.read_bytes()
        secs = ea.seconds_of(data)
        x, rate = ea.zmusic_render(data, secs)
        rows.append((ref + " (ref)", secs, measure(x, rate)))
    lines = ["# MAP01 new piece (D92): loudness of the loop, zmusic + gzdoom.sf2, no normalisation",
             "# (what the game plays: the MIDI's own velocities and CC7 decide the level)",
             "# peak / RMS / loudest 3 s, dBFS; renders in this folder run 10 s past the loop point", ""]
    for name, secs, lv in rows:
        lines.append(f"{name:18s} loop {secs:6.1f} s  peak {lv['peak']:6.1f}  RMS {lv['rms']:6.1f}  "
                     f"loud3s {lv['loud3s']:6.1f}"
                     + ("  arc RMS " + ", ".join(f"{k} {v:.1f}" for k, v in lv["arc"].items())
                        if "arc" in lv else ""))
    (out_dir / "LEVELS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", action="append", choices=sorted(VARIANT_BY_LUMP))
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args(argv)
    lumps = args.only or [v.lump for v in VARIANTS]
    for lump in lumps:
        v = VARIANT_BY_LUMP[lump]
        data = midi_bytes(v)
        (OUT_DIR / f"{lump}.mid").write_bytes(data)
        print(f"{lump}: {len(data)} bytes, {v.tempo_bpm:g} BPM, loop {loop_seconds(v):.1f} s -> "
              f"{OUT_DIR / (lump + '.mid')}")
    if not args.no_render:
        for line_ in render_all(lumps):
            print(line_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
