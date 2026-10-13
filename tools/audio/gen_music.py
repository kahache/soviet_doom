#!/usr/bin/env python3
"""Generate the mod's music as Standard MIDI Files (stdlib only).

    python3 tools/audio/gen_music.py                 # -> work/audio/*.mid
    python3 tools/audio/gen_music.py --only title
    python3 tools/audio/gen_music.py --only map01e     # the D43 enriched draft
    python3 tools/audio/gen_music.py --title-tempo 72 --map01-tempo 96
    python3 tools/audio/gen_music.py --list           # what exists and how long

Why MIDI, and why we write the bytes ourselves
----------------------------------------------
D16 (CEO, 2026-10-13): "el camino correcto es instrumental en MIDI". Every
genuine Soviet recording (Melodiya, the Alexandrov Ensemble, Radio USSR) is
a *phonogram* protected in the United States into the 2040s-2070s, which is
independent of whether the composition itself is free -- see
`docs/sound/MUSIC-RIGHTS.md` section 1. Sequencing our own instrumental MIDI
removes the phonogram right and the lyric right in one move, and a whole
soundtrack then weighs a few kilobytes inside the PK3.

NO third-party library is used and none is needed. A Standard MIDI File is a
chunked binary format: an `MThd` header followed by `MTrk` chunks of
delta-time + event bytes. The whole writer is ~80 lines below. Adding
`mido` or `midiutil` would buy nothing and would put a dependency between
the CEO and hearing a change.

Both pieces are ORIGINAL COMPOSITIONS (sound-designer, 2026-10-13), not
arrangements of any existing work. Style is not copyrightable -- the same
finding the poster research reached -- so writing *in the idiom* of the
Soviet parade march and of Eduard Artemyev's ANS electronics is free, while
quoting an actual tune is a rights question every single time. Nothing here
quotes anything. Licence: CC BY-NC-SA 4.0 with the rest of the assets (D15).

Everything the CEO might want to change -- tempo, instruments, how loud the
brass is, how long each section lasts -- is a named constant in section 2.

Output goes to `work/audio/`. Nothing enters `assets/` without the CEO's
explicit approval (project rule).
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "work" / "audio"  # never assets/: needs CEO approval


# =========================================================================
# 1. Standard MIDI File writer
# =========================================================================
# Reference: the SMF 1.0 specification (MIDI Manufacturers Association).
# Verified against GZDoom 4.14.2, which parses these files and renders them
# with `writewave` (see docs/sound/SOUNDTRACK.md, "How this was verified").

SMF_HEADER_CHUNK = b"MThd"
SMF_TRACK_CHUNK = b"MTrk"
SMF_HEADER_LENGTH = 6          # bytes of header payload: format, ntracks, division
SMF_FORMAT_MULTITRACK = 1      # format 1 = several tracks played simultaneously
TICKS_PER_BEAT = 480           # division: ticks per quarter note. 480 divides
                               # cleanly by 2/3/4/5/6/8, so triplets and 32nds
                               # are all exact integers -- no rounding drift.
MICROSECONDS_PER_MINUTE = 60_000_000

# Channel-voice status bytes (the low nibble carries the channel).
STATUS_NOTE_OFF = 0x80
STATUS_NOTE_ON = 0x90
STATUS_CONTROL_CHANGE = 0xB0
STATUS_PROGRAM_CHANGE = 0xC0

# Meta events.
META_PREFIX = 0xFF
META_TRACK_NAME = 0x03
META_TEMPO = 0x51
META_TIME_SIGNATURE = 0x58
META_END_OF_TRACK = 0x2F

# Controller numbers we use (MIDI CC, General MIDI level 1).
CC_VOLUME = 7                  # per-channel mix level, 0-127
CC_PAN = 10                    # 0 = hard left, 64 = centre, 127 = hard right
CC_REVERB = 91                 # GM2/GS reverb send; ignored by OPL, used by FluidSynth

# General MIDI percussion lives on channel 10, which is index 9 zero-based.
DRUM_CHANNEL = 9

# Event ordering inside one tick. Program/controller changes must land before
# the notes they affect, and a note-off must precede a note-on of the same
# pitch or the synth kills the note that just started.
ORDER_META = 0
ORDER_CONTROL = 1
ORDER_NOTE_OFF = 2
ORDER_NOTE_ON = 3

NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MIDDLE_C_OCTAVE = 4            # convention: MIDI note 60 is "C4"
MIDI_NOTE_MIN, MIDI_NOTE_MAX = 0, 127


def pitch(name: str) -> int:
    """'D4' -> 62, 'Bb2' -> 46, 'C#5' -> 73. Middle C (60) is C4."""
    letter = name[0].upper()
    if letter not in NOTE_NAMES:
        raise ValueError(f"bad note name {name!r}")
    i = 1
    accidental = 0
    while i < len(name) and name[i] in "#b":
        accidental += 1 if name[i] == "#" else -1
        i += 1
    octave = int(name[i:])
    value = NOTE_NAMES[letter] + accidental + (octave - MIDDLE_C_OCTAVE + 5) * 12
    if not MIDI_NOTE_MIN <= value <= MIDI_NOTE_MAX:
        raise ValueError(f"note {name!r} is outside the MIDI range")
    return value


def varlen(value: int) -> bytes:
    """MIDI variable-length quantity: 7 bits per byte, high bit = continue."""
    if value < 0:
        raise ValueError("negative delta time")
    out = bytearray([value & 0x7F])
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


@dataclass
class Track:
    """One MTrk chunk. Times are given in BEATS and converted to ticks here."""

    name: str
    events: list[tuple[int, int, int, bytes]] = field(default_factory=list)
    _seq: int = 0

    def _add(self, beat: float, order: int, payload: bytes) -> None:
        self._seq += 1
        self.events.append((round(beat * TICKS_PER_BEAT), order, self._seq, payload))

    # -- setup -----------------------------------------------------------
    def meta(self, beat: float, kind: int, payload: bytes) -> None:
        self._add(beat, ORDER_META, bytes([META_PREFIX, kind]) + varlen(len(payload)) + payload)

    def track_name(self, text: str | None = None) -> None:
        self.meta(0, META_TRACK_NAME, (text or self.name).encode("ascii", "replace"))

    def tempo(self, beat: float, bpm: float) -> None:
        self.meta(beat, META_TEMPO, struct.pack(">I", round(MICROSECONDS_PER_MINUTE / bpm))[1:])

    def time_signature(self, beat: float, numerator: int, denominator: int) -> None:
        power = denominator.bit_length() - 1           # 4 -> 2, 8 -> 3
        self.meta(beat, META_TIME_SIGNATURE, bytes([numerator, power, 24, 8]))

    def program(self, beat: float, channel: int, gm_program: int) -> None:
        self._add(beat, ORDER_CONTROL, bytes([STATUS_PROGRAM_CHANGE | channel, gm_program]))

    def control(self, beat: float, channel: int, controller: int, value: int) -> None:
        self._add(beat, ORDER_CONTROL, bytes([STATUS_CONTROL_CHANGE | channel, controller, clamp7(value)]))

    # -- notes -----------------------------------------------------------
    def note(self, channel: int, note: int, start: float, length: float, velocity: int) -> None:
        if length <= 0:
            return
        self._add(start, ORDER_NOTE_ON, bytes([STATUS_NOTE_ON | channel, note, clamp7(velocity)]))
        self._add(start + length, ORDER_NOTE_OFF, bytes([STATUS_NOTE_OFF | channel, note, 0]))

    def chord(self, channel: int, notes, start: float, length: float, velocity: int) -> None:
        for n in notes:
            self.note(channel, n if isinstance(n, int) else pitch(n), start, length, velocity)

    def hit(self, note: int, start: float, velocity: int, length: float = 0.125) -> None:
        """A percussion strike on the GM drum channel (length is irrelevant to a drum)."""
        self.note(DRUM_CHANNEL, note, start, length, velocity)

    # -- serialisation ---------------------------------------------------
    def to_bytes(self, end_beat: float) -> bytes:
        self._add(end_beat, ORDER_META, bytes([META_PREFIX, META_END_OF_TRACK, 0x00]))
        data = bytearray()
        previous = 0
        for tick, _order, _seq, payload in sorted(self.events, key=lambda e: (e[0], e[1], e[2])):
            data += varlen(tick - previous)
            data += payload
            previous = tick
        return SMF_TRACK_CHUNK + struct.pack(">I", len(data)) + bytes(data)


def clamp7(value: int) -> int:
    return max(0, min(127, int(round(value))))


def write_midi(path: Path, tracks: list[Track], end_beat: float) -> int:
    header = SMF_HEADER_CHUNK + struct.pack(
        ">IHHH", SMF_HEADER_LENGTH, SMF_FORMAT_MULTITRACK, len(tracks), TICKS_PER_BEAT
    )
    body = b"".join(t.to_bytes(end_beat) for t in tracks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + body)
    return len(header) + len(body)


# =========================================================================
# 2. The knobs the CEO can turn
# =========================================================================
# General MIDI program numbers, 0-based (printed GM charts are 1-based, so
# "57 Trumpet" in a chart is 56 here). Swapping an instrument is a one-line
# edit; the notes do not change.
GM_TRUMPET = 56
GM_TROMBONE = 57
GM_TUBA = 58
GM_FRENCH_HORN = 60
GM_TIMPANI = 47
GM_STRINGS = 48                # String Ensemble 1
GM_TREMOLO_STRINGS = 44
GM_TUBULAR_BELLS = 14
GM_SYNTH_BASS_2 = 39           # the hard, resonant one: the cosmodrome pulse
GM_PAD_HALO = 94               # cold, wide; the Artemyev / ANS colour
GM_FX_CRYSTAL = 98

# GM percussion key map (channel 10). These are note numbers, not pitches.
DRUM_BASS = 36                 # Bass Drum 1
DRUM_SNARE = 38                # Acoustic Snare
DRUM_LOW_FLOOR_TOM = 41
DRUM_LOW_TOM = 45
DRUM_HIGH_FLOOR_TOM = 43
DRUM_CRASH = 49
DRUM_RIDE = 51

BEATS_PER_BAR = 4              # both pieces are in 4/4

# -- D_SDTITL -------------------------------------------------------------
# Tempo: a Soviet *parade* march runs 112-120 BPM, but this is not a parade,
# it is the music under a propaganda poster on a title screen. Newsreel and
# documentary fanfares of the period sit far slower and heavier. 80 BPM is a
# contained step: serious, not jaunty. Ask for "more solemn" -> try 72;
# "more military" -> try 96. (--title-tempo on the command line.)
TITLE_TEMPO_BPM = 80

# Velocities = how hard each line is struck, 0-127. This is the CEO's
# "less brass" knob: drop TITLE_VEL_MELODY / TITLE_VEL_TUTTI, or lower the
# channel volume in TITLE_MIX below.
TITLE_VEL_MELODY = 96
TITLE_VEL_HARMONY = 70
TITLE_VEL_BASS = 82
TITLE_VEL_TIMPANI = 88
TITLE_VEL_STRINGS = 58
TITLE_VEL_BELL = 72

# Per-channel mix: (CC7 volume, CC10 pan). Pan spreads the band across the
# stereo field the way an orchestra sits: horns left, trumpets right.
TITLE_MIX = {
    "melody": (104, 70),
    "harmony": (86, 48),
    "bass": (96, 64),
    "timpani": (94, 64),
    "strings": (72, 84),
    "bell": (80, 64),
}

# Articulation: a note is held for this fraction of its written length, so
# repeated notes re-trigger instead of smearing into one another.
MARCATO = 0.86                 # detached, march-like
LEGATO = 0.98                  # sustained lines (strings, pads)

# How many bars each section lasts. Total title length = sum, in bars.
TITLE_INTRO_BARS = 4           # timpani + bare fifth, the lights coming up
TITLE_THEME_BARS = 8           # the period itself
TITLE_CODA_BARS = 5            # plagal descent + the final chord with the bell
TITLE_TAIL_BARS = 1            # silence before the loop point, so it breathes

# The theme: an 8-bar period in D natural minor, with the leading note (C#)
# raised only at the cadence -- the harmonic-minor dominant that gives
# Russian marches their particular bite. (pitch, length in beats). The first
# entry is an anacrusis: it sits in the last beat of the preceding bar.
TITLE_THEME = [
    ("A3", 1.0),                                              # anacrusis
    ("D4", 1.5), ("F4", 0.5), ("E4", 1.0), ("D4", 1.0),       # bar 1   i
    ("C4", 2.0), ("A3", 2.0),                                 # bar 2   VII/III
    ("Bb3", 1.5), ("C4", 0.5), ("D4", 1.0), ("E4", 1.0),      # bar 3   iv
    ("F4", 3.0), ("A3", 1.0),                                 # bar 4   i
    ("G4", 1.5), ("F4", 0.5), ("E4", 1.0), ("D4", 1.0),       # bar 5   VI
    ("C4", 2.0), ("E4", 2.0),                                 # bar 6   v
    ("F4", 1.0), ("E4", 1.0), ("D4", 1.0), ("C#4", 1.0),      # bar 7   V7
    ("D4", 4.0),                                              # bar 8   i
]

# One chord per bar of the theme, voiced for three trombones, plus the bass
# root an octave or two below.
TITLE_HARMONY = [
    (("D3", "F3", "A3"), "D2"),     # i    Dm
    (("C3", "F3", "A3"), "F2"),     # III  F
    (("D3", "G3", "Bb3"), "G2"),    # iv   Gm
    (("D3", "F3", "A3"), "D2"),     # i    Dm
    (("D3", "F3", "Bb3"), "Bb2"),   # VI   Bb
    (("C3", "E3", "A3"), "A2"),     # v    Am
    (("C#3", "E3", "G3"), "A2"),    # V7   A7  <- the raised leading note
    (("D3", "F3", "A3"), "D2"),     # i    Dm
]

# The coda: VI - iv - V7 - i - i. Plagal weight, then the dominant, then the
# tonic twice so the last chord can ring under the bell.
TITLE_CODA = [
    (("D3", "F3", "Bb3"), "Bb2"),
    (("D3", "G3", "Bb3"), "G2"),
    (("C#3", "E3", "G3"), "A2"),
    (("D3", "F3", "A3"), "D2"),
    (("D3", "F3", "A3"), "D2"),
]

# -- D_SDM01 --------------------------------------------------------------
# MAP01 is 5-8 minutes long (docs/levels/MAP01-zarya-7.md section 2), so this
# has to survive three or four loops without wearing a hole in the player.
# The defences against that are: a long cycle (64 bars ~ 2m22s), four
# sections that change what is on top of the ostinato, and a deliberately
# empty section D so the loop point lands on a release instead of a cut.
MAP01_TEMPO_BPM = 108          # fast enough to push, slow enough to be heavy
MAP01_SECTION_BARS = 16        # A pulse / B dread / C alarm / D release
MAP01_SECTIONS = 4
MAP01_TAIL_BARS = 0            # the loop is seamless: no gap

MAP01_VEL_BASS = 100
MAP01_VEL_PAD = 46
MAP01_VEL_STRINGS = 54
MAP01_VEL_BRASS = 88
MAP01_VEL_LEAD = 50
MAP01_VEL_DRUM_ACCENT = 104
MAP01_VEL_DRUM_PULSE = 72
MAP01_VEL_DRUM_GHOST = 44      # the quiet strikes that make a loop breathe

MAP01_MIX = {
    "bass": (112, 64),
    "pad": (62, 64),
    "strings": (70, 44),
    "brass": (92, 84),
    "lead": (58, 96),
    "drums": (104, 64),
}

# The ostinato. One bar of (pitch or None for a rest, length in beats).
# D minor with an Eb leaning on the tonic: the flat second is the oldest
# "something is wrong" interval there is, and it costs one note.
MAP01_OSTINATO_A = [
    ("D1", 0.5), ("D1", 0.25), (None, 0.25), ("D1", 0.5), ("F1", 0.5),
    ("D1", 0.5), (None, 0.25), ("C1", 0.25), ("D1", 0.5), ("Eb1", 0.5),
]
# Every fourth bar the riff turns upward instead of resolving, so the ear
# never settles into a one-bar groove.
MAP01_OSTINATO_B = [
    ("D1", 0.5), ("D1", 0.25), (None, 0.25), ("D1", 0.5), ("F1", 0.5),
    ("G1", 0.5), (None, 0.25), ("A1", 0.25), ("Bb1", 0.5), ("A1", 0.5),
]
MAP01_OSTINATO_VARIANT_EVERY = 4   # bars

# Section B: tremolo strings crawl up a chromatic line, two bars per step.
MAP01_CRAWL = ["D3", "Eb3", "E3", "F3", "F#3", "G3", "Ab3", "A3"]
MAP01_CRAWL_BARS_PER_STEP = 2

# Section C: the alarm. Brass stabs on and off the beat, alternating the
# tonic triad with its Neapolitan (Eb) -- two chords a semitone apart,
# which is the whole trick.
MAP01_STAB_BEATS = (0.0, 2.5, 6.0, 7.5, 10.0, 12.5, 14.0, 15.5)   # within a 4-bar group
MAP01_STAB_LENGTH = 0.4
MAP01_STAB_CHORD_I = ("D3", "F3", "A3")
MAP01_STAB_CHORD_N = ("Eb3", "G3", "Bb3")

# Section D: the release. A cold pad and a few far-off signals, nothing else.
MAP01_PAD_CHORDS = [("D2", "A2", "D3"), ("D2", "Bb2", "D3"), ("D2", "A2", "C3"), ("D2", "G2", "D3")]
MAP01_PAD_BARS_PER_CHORD = 4
MAP01_LEAD_NOTES = [("A5", 3.0), ("Bb5", 2.0), ("A5", 4.0), ("F5", 6.0)]


# =========================================================================
# 3. D_SDTITL -- title theme
# =========================================================================

def build_title(tempo_bpm: float) -> tuple[list[Track], float]:
    """March in D minor for brass, timpani and strings. Original composition."""
    melody = Track("melody - horns / trumpets")
    harmony = Track("harmony - trombones")
    bass = Track("bass - tuba")
    timpani = Track("timpani")
    strings = Track("strings")
    bell = Track("tubular bell")
    drums = Track("percussion")
    tracks = [melody, harmony, bass, timpani, strings, bell, drums]

    # Channels: one per line, drums forced onto the GM percussion channel.
    ch = {"melody": 0, "harmony": 1, "bass": 2, "timpani": 3, "strings": 4, "bell": 5}

    # Conductor data goes on the first track, as SMF format 1 expects.
    melody.track_name("Soviet Doom - D_SDTITL")
    melody.tempo(0, tempo_bpm)
    melody.time_signature(0, 4, 4)

    programs = {
        "melody": GM_FRENCH_HORN,      # the first statement is horns; trumpets double later
        "harmony": GM_TROMBONE,
        "bass": GM_TUBA,
        "timpani": GM_TIMPANI,
        "strings": GM_STRINGS,
        "bell": GM_TUBULAR_BELLS,
    }
    for track, key in zip(tracks, ch):
        volume, pan = TITLE_MIX[key]
        track.track_name()
        track.program(0, ch[key], programs[key])
        track.control(0, ch[key], CC_VOLUME, volume)
        track.control(0, ch[key], CC_PAN, pan)
        track.control(0, ch[key], CC_REVERB, 64)
    drums.track_name()
    drums.control(0, DRUM_CHANNEL, CC_VOLUME, 88)

    bar = 0.0  # position in bars; multiply by BEATS_PER_BAR for the beat

    def beat_of(bar_number: float, beat_in_bar: float = 0.0) -> float:
        return bar_number * BEATS_PER_BAR + beat_in_bar

    # -- Intro: timpani alone, then the bare fifth underneath ------------
    # No third in the chord for four bars: the mode is withheld until the
    # theme states it. The roll grows 8 velocity steps per bar.
    for b in range(TITLE_INTRO_BARS):
        base = beat_of(bar + b)
        growth = b * 8
        timpani.note(ch["timpani"], pitch("D2"), base + 0.0, 0.9, TITLE_VEL_TIMPANI - 24 + growth)
        timpani.note(ch["timpani"], pitch("D2"), base + 1.5, 0.4, TITLE_VEL_TIMPANI - 40 + growth)
        timpani.note(ch["timpani"], pitch("A2"), base + 2.0, 0.9, TITLE_VEL_TIMPANI - 30 + growth)
        timpani.note(ch["timpani"], pitch("D2"), base + 3.0, 0.9, TITLE_VEL_TIMPANI - 34 + growth)
        if b >= 2:
            bass.chord(ch["bass"], ("D2", "A2"), base, BEATS_PER_BAR * LEGATO,
                       TITLE_VEL_BASS - 20 + growth)
    bar += TITLE_INTRO_BARS

    def play_theme(start_bar: float, *, octave_shift: int, with_strings: bool,
                   melody_velocity: int, doubling: bool) -> None:
        """One 8-bar statement: melody + trombone chords + tuba + timpani."""
        # Melody, starting one beat early (the anacrusis).
        position = beat_of(start_bar, -1.0)
        for name, length in TITLE_THEME:
            note = pitch(name) + 12 * octave_shift
            melody.note(ch["melody"], note, position, length * MARCATO, melody_velocity)
            if doubling:
                # Horns an octave below the trumpets: the standard way to make
                # a march sound like a band and not like one instrument.
                melody.note(ch["melody"], note - 12, position, length * MARCATO,
                            melody_velocity - 18)
            position += length

        for index, (chord_notes, root) in enumerate(TITLE_HARMONY):
            base = beat_of(start_bar + index)
            # Trombones on beats 1 and 3: the march's two feet.
            for offset in (0.0, 2.0):
                harmony.chord(ch["harmony"], chord_notes, base + offset, 1.8 * MARCATO,
                              TITLE_VEL_HARMONY)
            bass.note(ch["bass"], pitch(root), base, 1.8 * MARCATO, TITLE_VEL_BASS)
            bass.note(ch["bass"], pitch(root), base + 2.0, 1.8 * MARCATO, TITLE_VEL_BASS - 8)
            # The timpani takes the root AS WRITTEN. An earlier version built
            # the drum pitch out of root[0] plus an octave digit, which both
            # dropped the accidental (Bb2 -> B natural under a Bb chord) and
            # pushed every stroke down to MIDI 26-35, below the real timpani
            # range (F1-F3) where the soundfont has nothing but mud.
            timpani.note(ch["timpani"], pitch(root), base, 0.9, TITLE_VEL_TIMPANI)
            timpani.note(ch["timpani"], pitch(root), base + 2.0, 0.9, TITLE_VEL_TIMPANI - 18)
            if with_strings:
                strings.chord(ch["strings"], tuple(pitch(n) + 12 for n in chord_notes),
                              base, BEATS_PER_BAR * LEGATO, TITLE_VEL_STRINGS)

    # -- Statement 1: horns, bare ----------------------------------------
    play_theme(bar, octave_shift=0, with_strings=False,
               melody_velocity=TITLE_VEL_MELODY - 14, doubling=False)
    bar += TITLE_THEME_BARS

    # -- Statement 2: trumpets an octave up, horns doubling, strings in --
    melody.program(beat_of(bar, -1.2), ch["melody"], GM_TRUMPET)
    play_theme(bar, octave_shift=1, with_strings=True,
               melody_velocity=TITLE_VEL_MELODY, doubling=True)
    bar += TITLE_THEME_BARS

    # -- Coda -------------------------------------------------------------
    for index, (chord_notes, root) in enumerate(TITLE_CODA):
        base = beat_of(bar + index)
        last = index == len(TITLE_CODA) - 1
        length = BEATS_PER_BAR * (2 if last else 1) * LEGATO
        harmony.chord(ch["harmony"], chord_notes, base, length, TITLE_VEL_HARMONY + 6)
        strings.chord(ch["strings"], tuple(pitch(n) + 12 for n in chord_notes), base, length,
                      TITLE_VEL_STRINGS + 6)
        bass.note(ch["bass"], pitch(root), base, length, TITLE_VEL_BASS)
        melody.note(ch["melody"], pitch(chord_notes[-1]) + 12, base, length, TITLE_VEL_MELODY - 10)
        if not last:
            timpani.note(ch["timpani"], pitch("D2"), base, 0.9, TITLE_VEL_TIMPANI)
            timpani.note(ch["timpani"], pitch("D2"), base + 2.0, 0.9, TITLE_VEL_TIMPANI - 20)
        else:
            timpani.note(ch["timpani"], pitch("D2"), base, 2.0, TITLE_VEL_TIMPANI + 8)
            bell.note(ch["bell"], pitch("D4"), base, 4.0, TITLE_VEL_BELL)
            bell.note(ch["bell"], pitch("D5"), base, 4.0, TITLE_VEL_BELL - 12)
            drums.hit(DRUM_CRASH, base, MAP01_VEL_DRUM_ACCENT)
    bar += TITLE_CODA_BARS + 1        # the final chord is two bars long
    bar += TITLE_TAIL_BARS

    return tracks, beat_of(bar)


# =========================================================================
# 4. D_SDM01 -- Zarya-7 cosmodrome, MAP01
# =========================================================================

def build_map01(tempo_bpm: float) -> tuple[list[Track], float]:
    """Industrial ostinato in D minor. Original composition.

    Sections, 16 bars each:
      A  pulse    the bass figure and the toms, nothing else. The base is
                  still standing; the player is walking through it.
      B  dread    tremolo strings crawl up chromatically, a pad underneath.
      C  alarm    brass stabs on and off the beat, the drums at full weight.
      D  release  the pad and a far-off signal. The loop restarts from quiet,
                  which is what stops it wearing out over 8 minutes.
    """
    bassline = Track("bass - synth ostinato")
    pad = Track("pad")
    strings = Track("tremolo strings")
    brass = Track("brass stabs")
    lead = Track("signal")
    drums = Track("percussion")
    tracks = [bassline, pad, strings, brass, lead, drums]

    ch = {"bass": 0, "pad": 1, "strings": 2, "brass": 3, "lead": 4}
    programs = {
        "bass": GM_SYNTH_BASS_2,
        "pad": GM_PAD_HALO,
        "strings": GM_TREMOLO_STRINGS,
        "brass": GM_TROMBONE,
        "lead": GM_FX_CRYSTAL,
    }

    bassline.track_name("Soviet Doom - D_SDM01")
    bassline.tempo(0, tempo_bpm)
    bassline.time_signature(0, 4, 4)

    for track, key in zip(tracks, ch):
        volume, pan = MAP01_MIX[key]
        track.track_name()
        track.program(0, ch[key], programs[key])
        track.control(0, ch[key], CC_VOLUME, volume)
        track.control(0, ch[key], CC_PAN, pan)
        track.control(0, ch[key], CC_REVERB, 72)
    drums.track_name()
    drums.control(0, DRUM_CHANNEL, CC_VOLUME, MAP01_MIX["drums"][0])

    total_bars = MAP01_SECTION_BARS * MAP01_SECTIONS

    def section_of(bar_index: int) -> int:
        return bar_index // MAP01_SECTION_BARS

    # -- The ostinato runs under everything except the last four bars -----
    for bar_index in range(total_bars):
        base = bar_index * BEATS_PER_BAR
        section = section_of(bar_index)
        if section == 3 and bar_index % MAP01_SECTION_BARS >= 12:
            continue                            # section D empties out
        figure = (MAP01_OSTINATO_B if (bar_index + 1) % MAP01_OSTINATO_VARIANT_EVERY == 0
                  else MAP01_OSTINATO_A)
        # Quieter in A and D, full weight in B and C.
        velocity = MAP01_VEL_BASS - (18 if section in (0, 3) else 0)
        position = 0.0
        for name, length in figure:
            if name is not None:
                bassline.note(ch["bass"], pitch(name), base + position, length * MARCATO, velocity)
            position += length

    # -- Percussion --------------------------------------------------------
    for bar_index in range(total_bars):
        base = bar_index * BEATS_PER_BAR
        section = section_of(bar_index)
        in_section = bar_index % MAP01_SECTION_BARS

        if section == 3 and in_section >= 8:
            # Release: one low tom per bar, then nothing.
            if in_section < 12:
                drums.hit(DRUM_LOW_FLOOR_TOM, base, MAP01_VEL_DRUM_GHOST)
            continue

        drums.hit(DRUM_LOW_FLOOR_TOM, base + 0.0, MAP01_VEL_DRUM_ACCENT)
        drums.hit(DRUM_LOW_TOM, base + 2.0, MAP01_VEL_DRUM_PULSE)
        if section >= 1:
            drums.hit(DRUM_BASS, base + 0.0, MAP01_VEL_DRUM_ACCENT)
            drums.hit(DRUM_BASS, base + 2.5, MAP01_VEL_DRUM_PULSE)
        if section >= 2:
            # A march snare, two and four: the Soviet half of the texture.
            drums.hit(DRUM_SNARE, base + 1.0, MAP01_VEL_DRUM_PULSE)
            drums.hit(DRUM_SNARE, base + 3.0, MAP01_VEL_DRUM_ACCENT)
            drums.hit(DRUM_RIDE, base + 3.5, MAP01_VEL_DRUM_GHOST)
        if in_section % 8 == 7:
            drums.hit(DRUM_HIGH_FLOOR_TOM, base + 3.0, MAP01_VEL_DRUM_PULSE)
            drums.hit(DRUM_HIGH_FLOOR_TOM, base + 3.5, MAP01_VEL_DRUM_PULSE)
        if in_section == 0 and section > 0:
            drums.hit(DRUM_CRASH, base, MAP01_VEL_DRUM_ACCENT)

    # -- Section B: the chromatic crawl ------------------------------------
    b_start = MAP01_SECTION_BARS
    for step, name in enumerate(MAP01_CRAWL):
        bar_index = b_start + step * MAP01_CRAWL_BARS_PER_STEP
        if bar_index >= b_start + MAP01_SECTION_BARS:
            break
        base = bar_index * BEATS_PER_BAR
        length = MAP01_CRAWL_BARS_PER_STEP * BEATS_PER_BAR * LEGATO
        strings.note(ch["strings"], pitch(name), base, length, MAP01_VEL_STRINGS)
        strings.note(ch["strings"], pitch(name) + 7, base, length, MAP01_VEL_STRINGS - 12)

    # The crawl keeps going under section C, an octave up and quieter, so the
    # alarm has something to sit on.
    c_start = MAP01_SECTION_BARS * 2
    for step, name in enumerate(MAP01_CRAWL[::-1]):
        bar_index = c_start + step * MAP01_CRAWL_BARS_PER_STEP
        if bar_index >= c_start + MAP01_SECTION_BARS:
            break
        base = bar_index * BEATS_PER_BAR
        length = MAP01_CRAWL_BARS_PER_STEP * BEATS_PER_BAR * LEGATO
        strings.note(ch["strings"], pitch(name) + 12, base, length, MAP01_VEL_STRINGS - 16)

    # -- Section C: the alarm ----------------------------------------------
    for group in range(MAP01_SECTION_BARS // 4):
        group_base = (c_start + group * 4) * BEATS_PER_BAR
        for index, offset in enumerate(MAP01_STAB_BEATS):
            chord_notes = MAP01_STAB_CHORD_N if index % 2 else MAP01_STAB_CHORD_I
            brass.chord(ch["brass"], chord_notes, group_base + offset,
                        MAP01_STAB_LENGTH, MAP01_VEL_BRASS)
            brass.note(ch["brass"], pitch(chord_notes[0]) - 12, group_base + offset,
                       MAP01_STAB_LENGTH, MAP01_VEL_BRASS - 10)

    # -- Pad: from section B to the end ------------------------------------
    for bar_index in range(MAP01_SECTION_BARS, total_bars, MAP01_PAD_BARS_PER_CHORD):
        chord_notes = MAP01_PAD_CHORDS[(bar_index // MAP01_PAD_BARS_PER_CHORD) % len(MAP01_PAD_CHORDS)]
        base = bar_index * BEATS_PER_BAR
        length = MAP01_PAD_BARS_PER_CHORD * BEATS_PER_BAR * LEGATO
        pad.chord(ch["pad"], chord_notes, base, length, MAP01_VEL_PAD)

    # -- Section D: the far-off signal --------------------------------------
    d_start = MAP01_SECTION_BARS * 3
    position = d_start * BEATS_PER_BAR + 2.0
    for name, length in MAP01_LEAD_NOTES:
        lead.note(ch["lead"], pitch(name), position, length * LEGATO, MAP01_VEL_LEAD)
        position += length + 2.0        # silence between signals is the point

    end_beat = (total_bars + MAP01_TAIL_BARS) * BEATS_PER_BAR
    return tracks, end_beat


# =========================================================================
# 4b. D_SDM01E -- Zarya-7 enriched (D43 draft)
# =========================================================================
# The CEO found the first two pieces "un poco simples" and D43 accepted the
# fix SOUNDTRACK.md 8.3 proposed: two more instrumental layers and a
# non-repeating fourth section, keeping the zero-rights position and the
# loop. build_map01() above is FROZEN: it is what assets/music/D_SDM01.mid
# was approved as, and tests/test_music.py regenerates that file from it
# byte for byte. This builder is the candidate that replaces it if the CEO
# approves it by ear; until then it is written as D_SDM01E, a draft name,
# and nothing in assets/ changes.
#
# Form, 72 bars (2:40 at 108 BPM):
#   A  pulse    1-16   as before, plus CELLOS from bar 9: a descending
#                       tetrachord D-C-Bb-A under the ostinato
#   B  dread   17-32   as before, plus a cello pedal and a HORN line that
#                       wobbles by semitones against the chromatic crawl
#   C  alarm   33-48   as before, plus horns climbing in half-bar steps and
#                       cellos pressing D against its Neapolitan Eb
#   D  lament  49-64   NEW and through-composed: no ostinato, no bar
#                       repeats another. Horns carry a 16-bar melody, cellos
#                       a counter-line, the bass walks the roots, the pad
#                       follows the harmony bar by bar
#   E  release 65-72   the old release, shortened: four bars of quiet
#                       ostinato and the far-off signals, then pad alone, so
#                       the loop still restarts from near-silence
GM_CELLO = 42

MAP01E_LUMP = "D_SDM01E"           # draft name; becomes D_SDM01 on approval
MAP01E_RELEASE_BARS = 8
MAP01E_QUIET_OSTINATO_BARS = 4     # of the release
MAP01E_VEL_HORN = 78
MAP01E_VEL_CELLO = 66
MAP01E_MIX_EXTRA = {
    "horns": (88, 40),
    "cellos": (84, 30),
}

# Section A, bars 9-16: cellos, two bars a note, the descending tetrachord.
MAP01E_A_CELLO = [("D3", 8.0), ("C3", 8.0), ("Bb2", 8.0), ("A2", 8.0)]
# Section B, bars 25-32: horns against the crawl (F#3, G3, Ab3, A3 below).
MAP01E_B_HORN = [("A4", 8.0), ("Bb4", 8.0), ("Ab4", 8.0), ("A4", 8.0)]
# Section B: the cello pedal, re-struck every two bars.
MAP01E_B_CELLO_PEDAL = "D2"
# Section C: horns climb in half-bar steps across the four 4-bar groups.
MAP01E_C_HORN = [("D4", 8.0), ("F4", 8.0), ("Eb4", 8.0), ("G4", 8.0),
                 ("F4", 8.0), ("A4", 8.0), ("Bb4", 8.0), ("A4", 8.0)]
MAP01E_C_CELLO = [("D3", 8.0), ("Eb3", 8.0)] * 4

# Section D, the lament: one chord per bar, (pad voicing, bass root, fifth).
MAP01E_LAMENT_HARMONY = [
    (("D3", "F3", "A3"), "D2", "A1"),      # 1  i
    (("D3", "F3", "Bb3"), "Bb1", "F2"),    # 2  VI
    (("D3", "G3", "Bb3"), "G1", "D2"),     # 3  iv
    (("C#3", "E3", "A3"), "A1", "E2"),     # 4  V
    (("D3", "F3", "A3"), "F1", "C2"),      # 5  i6
    (("Eb3", "G3", "Bb3"), "Eb2", "Bb1"),  # 6  bII, the piece's flat second
    (("D3", "G3", "Bb3"), "Bb1", "D2"),    # 7  iv6
    (("C#3", "G3", "A3"), "A1", "E2"),     # 8  V7
    (("D3", "F3", "Bb3"), "Bb1", "F2"),    # 9  VI, the climb begins
    (("C3", "F3", "A3"), "A1", "C2"),      # 10 III6
    (("D3", "G3", "Bb3"), "G1", "D2"),     # 11 iv
    (("Eb3", "G3", "Bb3"), "Eb2", "G1"),   # 12 bII
    (("D3", "F3", "A3"), "A1", "D2"),      # 13 i64, the high point
    (("D3", "F3", "Bb3"), "Bb1", "D2"),    # 14 VI
    (("C#3", "E3", "A3"), "A1", "A2"),     # 15 V
    (("D3", "A3", "D4"), "D2", "A1"),      # 16 i, open fifth
]
# The horn melody: every bar distinct (tests/test_music.py checks it).
MAP01E_LAMENT_HORN = [
    [("A4", 3.0), ("F4", 1.0)],
    [("D5", 2.0), ("C5", 1.0), ("Bb4", 1.0)],
    [("A4", 1.5), ("G4", 0.5), ("Bb4", 2.0)],
    [("E4", 1.0), ("A4", 1.0), ("C#5", 2.0)],
    [("D5", 3.0), ("A4", 1.0)],
    [("Bb4", 2.0), ("G4", 1.0), ("Eb5", 1.0)],
    [("D5", 1.5), ("C5", 0.5), ("Bb4", 1.0), ("G4", 1.0)],
    [("A4", 2.0), ("G4", 1.0), ("C#5", 1.0)],
    [("D5", 1.0), ("F5", 2.0), ("D5", 1.0)],
    [("C5", 3.0), ("A4", 1.0)],
    [("Bb4", 1.5), ("A4", 0.5), ("G4", 2.0)],
    [("G4", 1.0), ("Bb4", 1.0), ("Eb5", 2.0)],
    [("F5", 2.0), ("E5", 1.0), ("D5", 1.0)],
    [("D5", 1.0), ("C5", 1.0), ("Bb4", 2.0)],
    [("A4", 2.0), ("C#5", 2.0)],
    [("D5", 4.0)],
]
MAP01E_LAMENT_CELLO = [
    [("D3", 2.0), ("F3", 2.0)],
    [("F3", 2.0), ("D3", 2.0)],
    [("G3", 2.0), ("Bb3", 2.0)],
    [("A3", 2.0), ("C#3", 2.0)],
    [("F3", 4.0)],
    [("G3", 2.0), ("Bb3", 2.0)],
    [("Bb3", 2.0), ("A3", 1.0), ("G3", 1.0)],
    [("E3", 2.0), ("G3", 2.0)],
    [("F3", 4.0)],
    [("A3", 2.0), ("C4", 2.0)],
    [("D4", 2.0), ("Bb3", 2.0)],
    [("Eb3", 2.0), ("G3", 2.0)],
    [("A3", 2.0), ("F3", 2.0)],
    [("Bb2", 2.0), ("D3", 2.0)],
    [("E3", 2.0), ("C#3", 2.0)],
    [("D3", 4.0)],
]
MAP01E_LAMENT_CLIMAX_BARS = range(8, 13)   # 0-based bars of D: strings + bass drum
# The release's pad: Bb colour, then the open tonic fifth the loop restarts on.
MAP01E_RELEASE_PADS = [("D2", "Bb2", "D3"), ("D2", "A2", "D3")]


def _line(track: Track, channel: int, notes, start: float, velocity: int,
          articulation: float = LEGATO) -> float:
    """Play (pitch, beats) pairs from `start`; returns the beat after the last."""
    position = start
    for name, length in notes:
        track.note(channel, pitch(name), position, length * articulation, velocity)
        position += length
    return position


def build_map01_enriched(tempo_bpm: float) -> tuple[list[Track], float]:
    """D_SDM01 with horns and cellos and a through-composed lament. Original."""
    bassline = Track("bass - synth ostinato")
    pad = Track("pad")
    strings = Track("tremolo strings")
    brass = Track("brass stabs")
    lead = Track("signal")
    horns = Track("horns")
    cellos = Track("cellos")
    drums = Track("percussion")
    tracks = [bassline, pad, strings, brass, lead, horns, cellos, drums]

    ch = {"bass": 0, "pad": 1, "strings": 2, "brass": 3, "lead": 4, "horns": 5, "cellos": 6}
    programs = {
        "bass": GM_SYNTH_BASS_2,
        "pad": GM_PAD_HALO,
        "strings": GM_TREMOLO_STRINGS,
        "brass": GM_TROMBONE,
        "lead": GM_FX_CRYSTAL,
        "horns": GM_FRENCH_HORN,
        "cellos": GM_CELLO,
    }
    mix = dict(MAP01_MIX, **MAP01E_MIX_EXTRA)

    bassline.track_name("Soviet Doom - D_SDM01 enriched (D43 draft)")
    bassline.tempo(0, tempo_bpm)
    bassline.time_signature(0, 4, 4)
    for track, key in zip(tracks, ch):
        volume, pan = mix[key]
        track.track_name()
        track.program(0, ch[key], programs[key])
        track.control(0, ch[key], CC_VOLUME, volume)
        track.control(0, ch[key], CC_PAN, pan)
        track.control(0, ch[key], CC_REVERB, 72)
    drums.track_name()
    drums.control(0, DRUM_CHANNEL, CC_VOLUME, MAP01_MIX["drums"][0])

    sb = MAP01_SECTION_BARS
    a0, b0, c0, d0, e0 = 0, sb, 2 * sb, 3 * sb, 4 * sb
    total_bars = e0 + MAP01E_RELEASE_BARS

    def beat(bar_index: float) -> float:
        return bar_index * BEATS_PER_BAR

    # -- Ostinato: A, B, C, and the first bars of the release --------------
    for bar_index in list(range(a0, d0)) + list(range(e0, e0 + MAP01E_QUIET_OSTINATO_BARS)):
        figure = (MAP01_OSTINATO_B if (bar_index + 1) % MAP01_OSTINATO_VARIANT_EVERY == 0
                  else MAP01_OSTINATO_A)
        quiet = bar_index < b0 or bar_index >= e0
        velocity = MAP01_VEL_BASS - (18 if quiet else 0)
        position = 0.0
        for name, length in figure:
            if name is not None:
                bassline.note(ch["bass"], pitch(name), beat(bar_index) + position,
                              length * MARCATO, velocity)
            position += length

    # -- Percussion ---------------------------------------------------------
    for bar_index in range(total_bars):
        base = beat(bar_index)
        if bar_index >= e0:                                  # release
            if bar_index < e0 + MAP01E_QUIET_OSTINATO_BARS:
                drums.hit(DRUM_LOW_FLOOR_TOM, base, MAP01_VEL_DRUM_GHOST)
            continue
        if bar_index >= d0:                                  # lament
            in_d = bar_index - d0
            drums.hit(DRUM_LOW_FLOOR_TOM, base, MAP01_VEL_DRUM_GHOST + (16 if in_d % 4 == 0 else 0))
            if in_d in MAP01E_LAMENT_CLIMAX_BARS:
                drums.hit(DRUM_BASS, base, MAP01_VEL_DRUM_PULSE)
            if in_d in (0, MAP01E_LAMENT_CLIMAX_BARS.start):
                drums.hit(DRUM_CRASH, base, MAP01_VEL_DRUM_PULSE)
            continue
        section = bar_index // sb
        in_section = bar_index % sb
        drums.hit(DRUM_LOW_FLOOR_TOM, base + 0.0, MAP01_VEL_DRUM_ACCENT)
        drums.hit(DRUM_LOW_TOM, base + 2.0, MAP01_VEL_DRUM_PULSE)
        if section >= 1:
            drums.hit(DRUM_BASS, base + 0.0, MAP01_VEL_DRUM_ACCENT)
            drums.hit(DRUM_BASS, base + 2.5, MAP01_VEL_DRUM_PULSE)
        if section >= 2:
            drums.hit(DRUM_SNARE, base + 1.0, MAP01_VEL_DRUM_PULSE)
            drums.hit(DRUM_SNARE, base + 3.0, MAP01_VEL_DRUM_ACCENT)
            drums.hit(DRUM_RIDE, base + 3.5, MAP01_VEL_DRUM_GHOST)
        if in_section % 8 == 7:
            drums.hit(DRUM_HIGH_FLOOR_TOM, base + 3.0, MAP01_VEL_DRUM_PULSE)
            drums.hit(DRUM_HIGH_FLOOR_TOM, base + 3.5, MAP01_VEL_DRUM_PULSE)
        if in_section == 0 and section > 0:
            drums.hit(DRUM_CRASH, base, MAP01_VEL_DRUM_ACCENT)

    # -- Strings: the crawl in B and C, as before; a high tremolo at the lament's climax
    crawl_length = MAP01_CRAWL_BARS_PER_STEP * BEATS_PER_BAR * LEGATO
    for step, name in enumerate(MAP01_CRAWL):
        bar_index = b0 + step * MAP01_CRAWL_BARS_PER_STEP
        strings.note(ch["strings"], pitch(name), beat(bar_index), crawl_length, MAP01_VEL_STRINGS)
        strings.note(ch["strings"], pitch(name) + 7, beat(bar_index), crawl_length,
                     MAP01_VEL_STRINGS - 12)
    for step, name in enumerate(MAP01_CRAWL[::-1]):
        bar_index = c0 + step * MAP01_CRAWL_BARS_PER_STEP
        strings.note(ch["strings"], pitch(name) + 12, beat(bar_index), crawl_length,
                     MAP01_VEL_STRINGS - 16)
    for in_d in MAP01E_LAMENT_CLIMAX_BARS:
        voicing, _root, _fifth = MAP01E_LAMENT_HARMONY[in_d]
        for name in voicing[1:]:
            strings.note(ch["strings"], pitch(name) + 12, beat(d0 + in_d),
                         BEATS_PER_BAR * LEGATO, MAP01_VEL_STRINGS - 10)

    # -- Brass stabs: section C, as before ------------------------------------
    for group in range(sb // 4):
        group_base = beat(c0 + group * 4)
        for index, offset in enumerate(MAP01_STAB_BEATS):
            chord_notes = MAP01_STAB_CHORD_N if index % 2 else MAP01_STAB_CHORD_I
            brass.chord(ch["brass"], chord_notes, group_base + offset,
                        MAP01_STAB_LENGTH, MAP01_VEL_BRASS)
            brass.note(ch["brass"], pitch(chord_notes[0]) - 12, group_base + offset,
                       MAP01_STAB_LENGTH, MAP01_VEL_BRASS - 10)

    # -- Pad: B and C cycle as before; the lament follows its harmony; the
    #    release holds two chords and ends on the open tonic fifth.
    for bar_index in range(b0, d0, MAP01_PAD_BARS_PER_CHORD):
        chord_notes = MAP01_PAD_CHORDS[(bar_index // MAP01_PAD_BARS_PER_CHORD) % len(MAP01_PAD_CHORDS)]
        pad.chord(ch["pad"], chord_notes, beat(bar_index),
                  MAP01_PAD_BARS_PER_CHORD * BEATS_PER_BAR * LEGATO, MAP01_VEL_PAD)
    for in_d, (voicing, _root, _fifth) in enumerate(MAP01E_LAMENT_HARMONY):
        pad.chord(ch["pad"], voicing, beat(d0 + in_d), BEATS_PER_BAR * LEGATO, MAP01_VEL_PAD)
    half = MAP01E_RELEASE_BARS // len(MAP01E_RELEASE_PADS)
    for index, chord_notes in enumerate(MAP01E_RELEASE_PADS):
        pad.chord(ch["pad"], chord_notes, beat(e0 + index * half),
                  half * BEATS_PER_BAR * LEGATO, MAP01_VEL_PAD)

    # -- The lament's bass: roots on 1, fifths on 3, a new pair every bar ----
    for in_d, (_voicing, root, fifth) in enumerate(MAP01E_LAMENT_HARMONY):
        base = beat(d0 + in_d)
        bassline.note(ch["bass"], pitch(root), base, 2.0 * LEGATO, MAP01_VEL_BASS - 22)
        bassline.note(ch["bass"], pitch(fifth), base + 2.0, 2.0 * LEGATO, MAP01_VEL_BASS - 30)

    # -- Horns ----------------------------------------------------------------
    _line(horns, ch["horns"], MAP01E_B_HORN, beat(b0 + 8), MAP01E_VEL_HORN - 14)
    _line(horns, ch["horns"], MAP01E_C_HORN, beat(c0), MAP01E_VEL_HORN - 6)
    for in_d, bar_notes in enumerate(MAP01E_LAMENT_HORN):
        swell = 10 if in_d in MAP01E_LAMENT_CLIMAX_BARS else 0
        _line(horns, ch["horns"], bar_notes, beat(d0 + in_d), MAP01E_VEL_HORN + swell)

    # -- Cellos ---------------------------------------------------------------
    _line(cellos, ch["cellos"], MAP01E_A_CELLO, beat(a0 + 8), MAP01E_VEL_CELLO - 10)
    for bar_index in range(b0, c0, 2):
        cellos.note(ch["cellos"], pitch(MAP01E_B_CELLO_PEDAL), beat(bar_index),
                    2 * BEATS_PER_BAR * LEGATO, MAP01E_VEL_CELLO - 14)
    _line(cellos, ch["cellos"], MAP01E_C_CELLO, beat(c0), MAP01E_VEL_CELLO)
    for in_d, bar_notes in enumerate(MAP01E_LAMENT_CELLO):
        _line(cellos, ch["cellos"], bar_notes, beat(d0 + in_d), MAP01E_VEL_CELLO)

    # -- The release: the far-off signals, as before --------------------------
    position = beat(e0) + 2.0
    for name, length in MAP01_LEAD_NOTES:
        lead.note(ch["lead"], pitch(name), position, length * LEGATO, MAP01_VEL_LEAD)
        position += length + 2.0

    return tracks, beat(total_bars)


# =========================================================================
# 5. Catalogue and command line
# =========================================================================

@dataclass(frozen=True)
class Piece:
    lump: str                  # the lump name GZDoom will see (8 chars max)
    builder: object
    default_tempo: float
    where: str


PIECES = {
    "title": Piece("D_SDTITL", build_title, TITLE_TEMPO_BPM,
                   "title screen (MAPINFO GameInfo TitleMusic)"),
    "map01": Piece("D_SDM01", build_map01, MAP01_TEMPO_BPM,
                   "MAP01 Zarya-7 cosmodrome (MAPINFO map MAP01 music); "
                   "installed as assets/music/D_SDM01.mid (D43) -- FROZEN"),
    "map01e": Piece(MAP01E_LUMP, build_map01_enriched, MAP01_TEMPO_BPM,
                    "D_SDM01 enriched: horns, cellos, a through-composed lament "
                    "(D43 draft; replaces D_SDM01 only on the CEO's approval)"),
}

MAX_LUMP_NAME = 8              # WAD directory limit; check_pk3.py enforces it too
MIDI_EXTENSION = ".mid"


def duration_seconds(end_beat: float, tempo_bpm: float) -> float:
    return end_beat * 60.0 / tempo_bpm


def generate(key: str, out_dir: Path, tempo: float | None, quiet: bool) -> tuple[Path, float, int]:
    piece = PIECES[key]
    if len(piece.lump) > MAX_LUMP_NAME:
        raise SystemExit(f"lump name {piece.lump!r} exceeds {MAX_LUMP_NAME} characters")
    bpm = tempo if tempo else piece.default_tempo
    tracks, end_beat = piece.builder(bpm)
    path = out_dir / (piece.lump + MIDI_EXTENSION)
    size = write_midi(path, tracks, end_beat)
    seconds = duration_seconds(end_beat, bpm)
    if not quiet:
        print(f"{piece.lump:<9} {path}  {size:>6} B  {int(seconds // 60)}:{seconds % 60:04.1f}"
              f"  {bpm:g} BPM  {len(tracks)} tracks")
    return path, seconds, size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR,
                        help="output directory (default: work/audio/)")
    parser.add_argument("--only", choices=sorted(PIECES), action="append",
                        help="generate just this piece (repeatable)")
    parser.add_argument("--title-tempo", type=float, help="override D_SDTITL tempo, BPM")
    parser.add_argument("--map01-tempo", type=float,
                        help="override D_SDM01 (and D_SDM01E) tempo, BPM")
    parser.add_argument("--list", action="store_true", help="print the catalogue and exit")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if args.list:
        for key, piece in PIECES.items():
            print(f"{key:<6} {piece.lump:<9} {piece.default_tempo:g} BPM  {piece.where}")
        return 0

    tempos = {"title": args.title_tempo, "map01": args.map01_tempo,
              "map01e": args.map01_tempo}
    for key in (args.only or sorted(PIECES)):
        generate(key, args.out, tempos.get(key), args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
