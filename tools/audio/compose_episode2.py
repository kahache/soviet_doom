#!/usr/bin/env python3
"""Episode 2, «The Road to Moscow» (D104) -- original draft music, two variants per map.

    .venv/Scripts/python.exe tools/audio/compose_episode2.py              # MIDIs + renders + sheet
    .venv/Scripts/python.exe tools/audio/compose_episode2.py --no-render  # MIDIs + self-check only
    .venv/Scripts/python.exe tools/audio/compose_episode2.py --only D_SDM04A --only D_SDM04B
    .venv/Scripts/python.exe tools/audio/compose_episode2.py --check      # self-check, writes nothing

What this is
------------
The same method and the same General MIDI band as MAP01's approved piece
(tools/audio/compose_map01.py, D92/D95: horns and trombones on the theme,
synth bass, cellos, tremolo strings, timpani, GM drums), rendered with
GZDoom's own zmusic.dll + gzdoom.sf2 as a library (no engine, D26).

ORIGINAL COMPOSITION (sound-designer, 2026-10-21). Nothing is quoted: no
Soviet song, no folk tune, no classical theme, no phrase of our own earlier
pieces (the self-check compares two-bar shapes with compose_map01's themes).
So there is no rights question beyond our own (CC BY-NC-SA 4.0, D15).
Early sketches whose opening contour came close to «Священная война»
(5-1-2-3-2-1) and «Катюша» (1-2-3-1-3) were rewritten before rendering.

Pieces (lumps are 8 characters; nothing is installed -- the CEO listens first):
  MAP04 Trans-Siberian  D_SDM04A / D_SDM04B   rail-yard ostinato, brass, 138 / 132 BPM
  MAP05 Volga Dam       D_SDM05A / D_SDM05B   broad, organ hum in the bass, 116 / 108 BPM
  MAP06 Red Square      D_SDM06A / D_SDM06B   march, brass choir, boss B section, 120 / 112 BPM
  MAP06 boss loop       D_SDBS6A / D_SDBS6B   section B+B' of MAP06 cut out as its own loop
  Episode 2 intermission D_SDE2IA / D_SDE2IB  the three motifs in one 16-bar loop, 92 / 104 BPM

Variants differ for real: key, tempo, groove, lead instruments and (MAP04)
the whole B section; the 4-bar motif of each map is shared, so the map has
one identity whichever the CEO picks.

Output: work/audio/episode2/*.mid; renders (loop + 10 s past the seam) in
work/audio/episode2/render/ with LEVELS.txt; the listening sheet
work/audio/preview/episode2_music_listening.html.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_music as gm  # noqa: E402
from gen_music import (  # noqa: E402
    CC_PAN, CC_REVERB, CC_VOLUME, SMF_FORMAT_MULTITRACK, SMF_HEADER_CHUNK,
    SMF_HEADER_LENGTH, TICKS_PER_BEAT, Track, pitch)

PROJECT_ROOT = gm.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "audio" / "episode2"
RENDER_DIR = OUT_DIR / "render"
SHEET = PROJECT_ROOT / "work" / "audio" / "preview" / "episode2_music_listening.html"
SEAM_PREVIEW_S = 10.0
BEATS_PER_BAR = 4
CC_EXPRESSION = 11
REVERB = 72

# -- General MIDI programs (0-based), all present in gzdoom.sf2 (bank 0) -----------------
ORGAN, SYNTH_BASS_1, SYNTH_BASS_2 = 16, 38, 39
CELLO, CONTRABASS, TREMOLO, PIZZ, TIMPANI = 42, 43, 44, 45, 47
STRINGS, SLOW_STRINGS, CHOIR = 48, 49, 52
TRUMPET, TROMBONE, TUBA, HORNS, BRASS = 56, 57, 58, 60, 61
TUBULAR_BELLS, TAIKO, MUTED_TRUMPET = 14, 116, 59
PAD_HALO = 94

# -- GM drum notes -----------------------------------------------------------------------
KICK, SIDESTICK, SNARE, CLOSED_HH = 36, 37, 38, 42
LOW_FLOOR_TOM, LOW_TOM, MID_TOM, HIGH_TOM = 41, 45, 47, 50
CRASH, CRASH2, RIDE, RIDE_BELL = 49, 57, 51, 53

LEGATO, MARCATO, STACCATO = 0.97, 0.86, 0.5

# Playable range per program (MIDI notes): a bar that leaves it is moved by an octave.
RANGE = {TRUMPET: (54, 81), MUTED_TRUMPET: (54, 81), HORNS: (41, 79), TROMBONE: (38, 72),
         TUBA: (28, 58), BRASS: (45, 81), CHOIR: (48, 79), STRINGS: (36, 93),
         SLOW_STRINGS: (36, 93), TREMOLO: (36, 93), CELLO: (36, 72)}

# -- Pitch classes, chords ---------------------------------------------------------------
PCS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITY = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10),
           "maj7": (0, 4, 7, 11), "dim": (0, 3, 6), "dim7": (0, 3, 6, 9), "sus4": (0, 5, 7)}
MINOR_KEY_SIG = {9: 0, 4: 1, 11: 2, 6: 3, 1: 4, 8: 5, 2: -1, 7: -2, 0: -3, 5: -4, 10: -5, 3: -6}


def pc_of(name: str) -> tuple[int, str]:
    """'F#m7' -> (6, 'm7')."""
    v, i = PCS[name[0]], 1
    while i < len(name) and name[i] in "#b":
        v += 1 if name[i] == "#" else -1
        i += 1
    return v % 12, name[i:]


def parse_chord(name: str) -> tuple[int, list[int]]:
    """'D/F#' -> (bass pc, [root, third, fifth(, seventh)] pcs)."""
    main, _, bass = name.partition("/")
    root, q = pc_of(main)
    tones = [(root + i) % 12 for i in QUALITY[q]]
    return (pc_of(bass)[0] if bass else root), tones


def mel(text: str) -> list[list[tuple[str | None, float]]]:
    """'E4:2 E4:1 r:4 | ...' (durations in sixteenths) -> bars of (note, beats)."""
    bars = []
    for chunk in text.split("|"):
        notes, total = [], 0
        for tok in chunk.split():
            n, d = tok.split(":")
            notes.append((None if n == "r" else n, int(d) / 4))
            total += int(d)
        if total != 16:
            raise ValueError(f"bar does not sum to 16 sixteenths ({total}): {chunk!r}")
        bars.append(notes)
    return bars


def harm(text: str) -> list[list[tuple[float, float, str]]]:
    out = []
    for chunk in text.split("|"):
        names = [n.strip() for n in chunk.split(",")]
        for n in names:
            parse_chord(n)
        out.append([(0.0, 4.0, names[0])] if len(names) == 1
                   else [(0.0, 2.0, names[0]), (2.0, 2.0, names[1])])
    return out


def in_range(pc: int, low: int) -> int:
    return low + (pc - low) % 12


# -- The song ---------------------------------------------------------------------------------

@dataclass
class Part:
    program: int
    volume: int
    pan: int
    reverb: int = REVERB


@dataclass
class Song:
    lump: str
    title: str
    bpm: float
    transpose: int                    # semitones from the written key (written keys: see each piece)
    tonic_pc: int                     # of the sounding minor key (key signature)
    parts: dict[str, Part]
    volume_scale: float = 0.88
    drum_volume: int = 94
    notes: list = field(default_factory=list)       # (part, pitch, start, beats, vel)
    hits: list = field(default_factory=list)        # (drum note, start, vel)
    ctrls: list = field(default_factory=list)       # (part, beat, cc, value)
    harmony: list = field(default_factory=list)     # per bar: [(start, beats, chord)]
    sections: list = field(default_factory=list)    # (label, bar)
    lead_parts: tuple = ()

    # -- form --------------------------------------------------------------
    def section(self, label: str, harmony_text: str) -> int:
        start = len(self.harmony)
        self.sections.append((label, start))
        self.harmony.extend(harm(harmony_text))
        return start

    @property
    def bars(self) -> int:
        return len(self.harmony)

    def chord_at(self, beat: float) -> str:
        bar = int(beat // BEATS_PER_BAR)
        inside = beat - bar * BEATS_PER_BAR
        for start, beats, name in self.harmony[bar]:
            if start <= inside + 1e-9 < start + beats:
                return name
        return self.harmony[bar][-1][2]

    def chord(self, name: str) -> tuple[int, list[int]]:
        bass, tones = parse_chord(name)
        t = self.transpose
        return (bass + t) % 12, [(x + t) % 12 for x in tones]

    # -- low-level ---------------------------------------------------------
    def n(self, part: str, p: int, start: float, beats: float, vel: float) -> None:
        if beats > 0:
            self.notes.append((part, int(p), float(start), float(beats), max(1, min(127, round(vel)))))

    def hit(self, note: int, start: float, vel: float) -> None:
        self.hits.append((note, float(start), max(1, min(127, round(vel)))))

    def cc(self, part: str, beat: float, cc: int, value: int) -> None:
        self.ctrls.append((part, float(beat), cc, max(0, min(127, round(value)))))

    def ramp(self, part: str, start: float, beats: float, v0: int, v1: int, steps: int = 12) -> None:
        for k in range(steps + 1):
            self.cc(part, start + beats * k / steps, CC_EXPRESSION, v0 + (v1 - v0) * k / steps)

    # -- writers -----------------------------------------------------------
    def fold(self, part: str, pitches: list[int]) -> int:
        """Octave shift that keeps a bar inside the part's range."""
        lo, hi = RANGE.get(self.parts[part].program, (0, 127))
        shift = 0
        while pitches and max(pitches) + shift > hi:
            shift -= 12
        while pitches and min(pitches) + shift < lo and max(pitches) + shift + 12 <= hi:
            shift += 12
        return shift

    def line(self, part: str, bars, bar0: int, vel: float, art: float = LEGATO,
             octave: int = 0, accent: float = 6, swell: float = 0.0) -> None:
        for i, notes in enumerate(bars):
            base = (bar0 + i) * BEATS_PER_BAR
            sounding = [pitch(nm) + self.transpose + 12 * octave for nm, _ in notes if nm]
            sh = self.fold(part, sounding)
            pos = 0.0
            for nm, beats in notes:
                if nm:
                    p = pitch(nm) + self.transpose + 12 * octave + sh
                    a = accent if pos == 0 else (accent / 2 if pos == 2.0 else 0)
                    self.n(part, p, base + pos, beats * art, vel + a + swell * i)
                pos += beats

    def below(self, p: int, beat: float, lo_gap: int = 3, hi_gap: int = 9, avoid=()) -> int:
        _, tones = self.chord(self.chord_at(beat))
        cands = [q for q in range(p - hi_gap, p - lo_gap + 1) if q % 12 in tones]
        fresh = [q for q in cands if q % 12 not in avoid]
        pool = fresh or cands
        return max(pool) if pool else p - 5

    def harmonize(self, part: str, bars, bar0: int, vel: float, art: float = LEGATO,
                  octave: int = 0, voices: int = 1, lo_gap: int = 3) -> None:
        """Chord tones under each melody note: a brass choir following the tune's rhythm."""
        for i, notes in enumerate(bars):
            base = (bar0 + i) * BEATS_PER_BAR
            pos = 0.0
            for nm, beats in notes:
                if nm:
                    top = pitch(nm) + self.transpose + 12 * octave
                    used = {top % 12}
                    q = top
                    for _ in range(voices):
                        q = self.below(q, base + pos, lo_gap, 9, used)
                        used.add(q % 12)
                        hi = RANGE.get(self.parts[part].program, (0, 127))[1]
                        self.n(part, q - 12 if q > hi else q, base + pos, beats * art, vel)
                pos += beats

    def chords(self, part: str, bar: int, low: str, vel: float, art: float = LEGATO,
               hits: tuple | None = None, length: float | None = None, bass: bool = False) -> None:
        """Sustained voicings for each chord of the bar, or short hits at `hits` beats."""
        lo = pitch(low)
        for start, beats, name in self.harmony[bar]:
            bpc, tones = self.chord(name)
            voicing = sorted(in_range(t, lo) for t in tones)
            if bass:
                voicing = [in_range(bpc, lo - 12)] + voicing
            t0 = bar * BEATS_PER_BAR + start
            if hits is None:
                for p in voicing:
                    self.n(part, p, t0, beats * art, vel)
            else:
                for h in hits:
                    if start <= h < start + beats:
                        for p in voicing:
                            self.n(part, p, bar * BEATS_PER_BAR + h, length or 0.45, vel)

    def pattern(self, part: str, bar: int, pat: str, low: str, vel: float,
                art: float = 0.9, accent: float = 14) -> None:
        """16 characters per bar, one per sixteenth, chord-relative:
        r root (slash bass), o octave, t third, f fifth, s seventh, n semitone above the
        root, l fifth below; '.' rest, '-' holds the previous note. Upper case = accent."""
        assert len(pat) == 16, pat
        lo = pitch(low)
        pending = None
        for k, ch in enumerate(pat + "."):
            if ch == "-" and pending:
                pending[2] += 0.25
                continue
            if pending:
                p, st, ln, v = pending
                self.n(part, p, st, ln * art if ln <= 0.25 else ln - 0.25 * (1 - art), v)
                pending = None
            if k == 16 or ch == ".":
                continue
            t = bar * BEATS_PER_BAR + 0.25 * k
            bpc, tones = self.chord(self.chord_at(t))
            r = in_range(bpc, lo)
            nxt = lambda pc: r + (pc - r) % 12 if (pc - r) % 12 else r + 12  # noqa: E731
            pmap = {"r": r, "o": r + 12, "t": nxt(tones[1]), "f": nxt(tones[2]),
                    "s": nxt(tones[3]) if len(tones) > 3 else r + 12, "n": r + 1,
                    "l": nxt(tones[2]) - 12}
            p = pmap[ch.lower()]
            pending = [p, t, 0.25, vel + (accent if ch.isupper() else 0)]

    def drums(self, bar: int, pats: dict[int, str], vel: float) -> None:
        """X accent, x normal, g ghost, R a two-stroke ruff (two 32nds)."""
        for note, pat in pats.items():
            assert len(pat) == 16, pat
            for k, ch in enumerate(pat):
                t = bar * BEATS_PER_BAR + 0.25 * k
                if ch == "X":
                    self.hit(note, t, vel)
                elif ch == "x":
                    self.hit(note, t, vel * 0.76)
                elif ch == "g":
                    self.hit(note, t, vel * 0.46)
                elif ch == "R":
                    self.hit(note, t, vel * 0.55)
                    self.hit(note, t + 0.125, vel * 0.8)

    def roll(self, note_or_part, start: float, beats: float, v0: float, v1: float,
             step: float = 0.25, p: int | None = None) -> None:
        k = int(round(beats / step))
        for i in range(k):
            v = v0 + (v1 - v0) * i / max(1, k - 1)
            if p is None:
                self.hit(note_or_part, start + i * step, v)
            else:
                self.n(note_or_part, p, start + i * step, step * 0.95, v)

    def timp(self, bar: int, pat: str, vel: float) -> None:
        self.pattern("timp", bar, pat, "E2", vel, art=0.9, accent=10)

    # -- serialisation -----------------------------------------------------
    def tracks(self, bar_from: int = 0, bar_to: int | None = None, mute=()) -> tuple[list[Track], float]:
        bar_to = self.bars if bar_to is None else bar_to
        t0, t1 = bar_from * BEATS_PER_BAR, bar_to * BEATS_PER_BAR
        names = list(self.parts)
        chans = [c for c in range(16) if c != gm.DRUM_CHANNEL]
        if len(names) > len(chans):
            raise ValueError("too many parts")
        ch = dict(zip(names, chans))
        tr = {k: Track(k) for k in names}
        drums = Track("percussion")
        first = tr[names[0]]
        first.track_name(f"Soviet Doom - {self.lump} ({self.title}, D104 draft, original)")
        first.tempo(0, self.bpm)
        first.time_signature(0, 4, 4)
        first.key_signature(0, MINOR_KEY_SIG[self.tonic_pc], True)
        for k in names:
            if k != names[0]:
                tr[k].track_name()
            p = self.parts[k]
            tr[k].program(0, ch[k], p.program)
            tr[k].control(0, ch[k], CC_VOLUME, round(p.volume * self.volume_scale))
            tr[k].control(0, ch[k], CC_PAN, p.pan)
            tr[k].control(0, ch[k], CC_REVERB, p.reverb)
            tr[k].control(0, ch[k], CC_EXPRESSION, 127)
        drums.track_name()
        drums.control(0, gm.DRUM_CHANNEL, CC_VOLUME, round(self.drum_volume * self.volume_scale))
        drums.control(0, gm.DRUM_CHANNEL, CC_REVERB, REVERB - 20)
        for part, beat, cc, val in self.ctrls:
            if t0 <= beat < t1:
                tr[part].control(beat - t0, ch[part], cc, val)
        for part, p, st, ln, v in self.notes:
            if part in mute or not (t0 <= st < t1):
                continue
            tr[part].note(ch[part], p, st - t0, min(ln, t1 - st), v)
        if "drums" not in mute:
            for note, st, v in self.hits:
                if t0 <= st < t1:
                    drums.hit(note, st - t0, v)
        return [tr[k] for k in names] + [drums], float(t1 - t0)

    def midi(self, bar_from: int = 0, bar_to: int | None = None, mute=()) -> bytes:
        tracks, end = self.tracks(bar_from, bar_to, mute)
        header = SMF_HEADER_CHUNK + struct.pack(">IHHH", SMF_HEADER_LENGTH, SMF_FORMAT_MULTITRACK,
                                                len(tracks), TICKS_PER_BEAT)
        return header + b"".join(t.to_bytes(end) for t in tracks)

    def seconds(self, bars: int | None = None) -> float:
        return (self.bars if bars is None else bars) * BEATS_PER_BAR * 60.0 / self.bpm


@dataclass(frozen=True)
class Variant:
    lump: str
    flavour: str          # "A" or "B"
    bpm: float
    transpose: int
    label: str


# =============================================================================================
# MAP04 -- Trans-Siberian (written in E minor)
# =============================================================================================
# The motif: a repeated-note "clack" (E E-E) that leaps to the fifth -- the wheels on the
# rail joints, then the whistle. Four bars: Em | D | C,Am | B7, answered a' in bars 5-8.

M4_THEME_H = "Em | D | C,Am | B7 | Em | D7 | Am,B7 | Em"
M4_THEME = mel("""
E4:2 E4:1 E4:1 G4:2 E4:2 B4:6 A4:2 |
D4:2 D4:1 D4:1 F#4:2 D4:2 A4:6 G4:2 |
E5:4 D5:2 C5:2 C5:3 B4:1 A4:4 |
B4:6 A4:1 G4:1 F#4:4 D#4:4 |
E4:2 E4:1 E4:1 G4:2 E4:2 B4:6 A4:2 |
F#4:2 F#4:1 F#4:1 A4:2 F#4:2 D5:6 C5:2 |
C5:2 B4:2 A4:4 B4:2 A4:2 F#4:2 D#4:2 |
E4:12 r:4""")
M4_COUNTER = mel("""G5:8 F#5:4 E5:4 | F#5:8 E5:4 D5:4 | E5:8 C5:8 | D#5:8 F#5:8 |
G5:8 B5:4 G5:4 | F#5:8 A5:4 F#5:4 | E5:8 D#5:8 | E5:16""")
# Variant A's B section: "the steppe" -- G major, a broad legato tune over the engine.
M4_STEPPE_H = "G | D/F# | Em | C | G/B | Am | D | D7 | C | G/B | Am | Em | C | D | B7 | B7"
M4_STEPPE = mel("""
B4:6 C5:2 D5:8 | A4:6 B4:2 A4:4 F#4:4 | G4:6 A4:2 B4:4 E5:4 | E5:8 D5:4 C5:4 |
D5:6 B4:2 G4:8 | C5:6 B4:2 A4:4 E5:4 | D5:12 C5:2 B4:2 | A4:16 |
G5:6 E5:2 C5:8 | D5:6 E5:2 D5:4 B4:4 | C5:6 D5:2 E5:4 A5:4 | G5:8 F#5:4 E5:4 |
E5:6 D5:2 C5:4 E5:4 | F#5:6 E5:2 D5:4 A4:4 | B4:6 C5:2 D#5:4 F#5:4 | F#5:8 D#5:4 B4:4""")
# Variant B's B section: "the pursuit" -- trumpet calls, trombone answers, the Phrygian F.
M4_PURSUIT_H = "Am | Am | Em | Em | F | F | B7 | B7 | Am | Am | Em | Em | F | F | B7 | B7"
M4_PURSUIT = mel("""
A4:3 A4:1 C5:2 E5:2 r:2 E5:2 D5:2 C5:2 |
E4:3 E4:1 D4:2 C4:2 B3:4 A3:4 |
B4:3 B4:1 D5:2 G5:2 r:2 G5:2 F#5:2 E5:2 |
G4:3 G4:1 F#4:2 E4:2 D4:4 B3:4 |
C5:3 C5:1 F5:2 A5:2 r:2 A5:2 G5:2 F5:2 |
A4:3 A4:1 G4:2 F4:2 E4:4 C4:4 |
B4:4 D#5:4 F#5:4 A5:4 |
B5:8 A5:4 F#5:4""")
M4_PURSUIT_WHO = ["tpt", "tbn", "tpt", "tbn", "tpt", "tbn", "tutti", "tutti"]
# C: the armoured train -- a slow chorale over the bare rail rhythm.
M4_CHORALE_H = "Em | C | Am | B | Em | F | Am | B7 | C | Am | F | B7"
M4_CHORALE = mel("""E4:8 G4:8 | G4:8 E4:8 | A4:8 C5:8 | B4:16 | B4:8 G4:8 | A4:8 F4:8 |
E4:8 A4:8 | F#4:16 | G4:8 C5:8 | C5:8 E5:8 | C5:8 A4:8 | B4:16""")
M4_BUILD_H = "B7 | B7 | B7 | B7"
M4_BUILD = mel("""B4:2 B4:1 B4:1 D#5:2 B4:2 r:8 | C5:2 C5:1 C5:1 E5:2 C5:2 r:8 |
D#5:2 D#5:1 D#5:1 F#5:2 D#5:2 r:8 | B4:4 B4:4 B4:4 B4:4""")
M4_BUILD_ANS = mel("""r:8 F#3:2 F#3:2 B3:4 | r:8 G3:2 G3:2 C4:4 | r:8 A3:2 A3:2 D#4:4 |
B3:4 B3:4 B3:4 B3:4""")
M4_CODA_H = "Em | C | B7 | B7"
M4_CODA = mel("""E4:2 E4:1 E4:1 G4:2 E4:2 B4:6 A4:2 | E4:2 E4:1 E4:1 G4:2 E4:2 C5:6 B4:2 |
B4:2 B4:1 B4:1 D#5:2 B4:2 F#5:8 | B4:2 r:2 B4:2 r:2 B4:2 B4:2 r:4""")

M4_VARIANTS = (
    Variant("D_SDM04A", "A", 138.0, 0, "Mi menor, 138 BPM: galope de semicorcheas, trompas y trompetas, "
            "sección B «la estepa» en sol mayor (cuerdas)"),
    Variant("D_SDM04B", "B", 132.0, 3, "Sol menor, 132 BPM: ostinato 3-3-2 de cuerdas staccato, trombones "
            "en el tema, sección B «la persecución» (llamadas de trompeta), coral en coro"),
)


def m4_rail(s: Song, b: int, level: int, flavour: str) -> None:
    """The percussion of the rails. level 0: rails only; 1: + kick; 2: + snare; 3: busier."""
    hh = "XxgxXxgxXxgxXxgx" if flavour == "A" else "XxgXxgXxXxgXxgXx"
    pats = {CLOSED_HH: hh, SIDESTICK: "...x.......x....", LOW_TOM: "......xX......xX"}
    if level >= 1:
        pats[KICK] = "X.......X......." if flavour == "A" else "X.....X.....X..."
    if level >= 2:
        pats[SNARE] = "....X.......X..."
    if level >= 3:
        pats[KICK] = "X.....x.X.....x." if flavour == "A" else "X.....X.X...X.x."
        pats[SNARE] = "....X.g.....X.gg"
    s.drums(b, pats, 88 if level else 70)


def m4_engine(s: Song, b: int, level: int, flavour: str) -> None:
    if flavour == "A":
        if level >= 1:
            s.pattern("bass", b, "R.rrR.rrR.rrO.rr", "E1", 84, art=0.8)
        if level >= 2:
            s.pattern("low", b, "R.o.R.o.R.o.R.o.", "C2", 62, art=0.55)
    else:
        if level >= 1:
            s.pattern("bass", b, "R.r.r.R.r.r.R.r.", "E1", 82, art=0.75)
        if level >= 2:
            s.pattern("low", b, "R.f.o.R.f.o.R.f.", "C3", 60, art=0.45)
    if level >= 2:
        s.timp(b, "R.......F......." if level == 2 else "R.......F...F.F.", 78)


def build_map04(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "bass": Part(SYNTH_BASS_2 if A else SYNTH_BASS_1, 88, 64),
        "low": Part(CELLO if A else STRINGS, 76, 34),
        "trem": Part(TREMOLO, 70, 92),
        "strings": Part(STRINGS, 84, 76),
        "tbn": Part(TROMBONE, 104, 88),
        "tuba": Part(TUBA, 88, 60),
        "horns": Part(HORNS, 122, 44),
        "tpt": Part(TRUMPET, 108, 54),
        "timp": Part(TIMPANI, 92, 70),
    }
    if not A:
        parts["choir"] = Part(CHOIR, 92, 64)
        parts["brass"] = Part(BRASS, 100, 72)
    s = Song(v.lump, "MAP04 Trans-Siberian", v.bpm, v.transpose, (4 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "tbn", "brass"), drum_volume=84)
    fl = v.flavour

    # -- Intro: the engine starts, the whistle -----------------------------------
    i0 = s.section("Intro · el motor", "Em | Em | Em | Em,B7")
    for b in range(i0, i0 + 4):
        m4_rail(s, b, 0 if b == i0 else 1, fl)
        m4_engine(s, b, 1 if b == i0 else 2, fl)
    # the whistle: an Em7 on trombones and horns, fading (CC11)
    for part, low in (("tbn", "D3"), ("horns", "B3")):
        s.chords(part, i0, low, 92, art=0.94)
        s.ramp(part, i0 * 4, 3.7, 127, 40)
        s.cc(part, i0 * 4 + 3.95, CC_EXPRESSION, 127)
    s.roll("timp", (i0 + 3) * 4 + 2.0, 2.0, 50, 100, 0.25, p=in_range((4 + v.transpose + 7) % 12, pitch("E2")))

    # -- A1: the theme --------------------------------------------------------------
    a1 = s.section("A · el tema", M4_THEME_H)
    if A:
        s.line("horns", M4_THEME, a1, 98, MARCATO)
    else:
        s.line("tbn", M4_THEME, a1, 100, MARCATO, octave=-1)
        s.line("horns", M4_THEME[4:], a1 + 4, 84, MARCATO)
    for b in range(a1, a1 + 8):
        m4_rail(s, b, 2, fl)
        m4_engine(s, b, 2, fl)
        if (b - a1) % 4 == 3:
            s.chords("tbn" if A else "brass", b, "D3", 80, hits=(0.0, 2.0, 2.5))
    s.hit(CRASH, a1 * 4, 100)

    # -- A2: trumpets take it, a choir of horns under, the counter-line ---------
    a2 = s.section("A' · trompetas", M4_THEME_H)
    s.line("tpt", M4_THEME, a2, 98, MARCATO)
    s.harmonize("horns" if A else "brass", M4_THEME, a2, 76, MARCATO)
    s.line("strings", M4_COUNTER, a2, 74, LEGATO)
    for b in range(a2, a2 + 8):
        m4_rail(s, b, 3, fl)
        m4_engine(s, b, 3, fl)
    s.hit(CRASH, a2 * 4, 104)

    # -- B ------------------------------------------------------------------------
    if A:
        b0 = s.section("B · la estepa", M4_STEPPE_H)
        s.line("strings", M4_STEPPE, b0, 90, LEGATO, accent=4)
        s.line("horns", M4_STEPPE[8:], b0 + 8, 82, LEGATO, octave=-1)
        for b in range(b0, b0 + 16):
            second = b >= b0 + 8
            m4_rail(s, b, 2 if second else 1, fl)
            m4_engine(s, b, 2 if second else 1, fl)
            s.chords("trem", b, "G3", 50 if not second else 58)
            if not second:
                s.pattern("low", b, "r-------f-------", "C2", 56, art=0.98)
        s.hit(CRASH, b0 * 4, 92)
        s.hit(CRASH, (b0 + 8) * 4, 96)
    else:
        b0 = s.section("B · la persecución", M4_PURSUIT_H)
        for rep in range(2):
            for i, (who, bar) in enumerate(zip(M4_PURSUIT_WHO, M4_PURSUIT)):
                b = b0 + 8 * rep + i
                if who in ("tpt", "tutti"):
                    s.line("tpt", [bar], b, 100, MARCATO)
                if who in ("tbn", "tutti"):
                    s.line("tbn", [bar], b, 98, MARCATO, octave=-1 if who == "tutti" else 0)
                if who == "tutti" or rep == 1:
                    s.line("horns", [bar], b, 84 if who == "tutti" else 70, MARCATO,
                           octave=-1 if who == "tutti" else 0)
                if who == "tpt":
                    s.chords("tbn", b, "D3", 70, hits=(0.0,), length=1.8)
                s.chords("trem", b, "A3", 56 + 6 * rep)
                m4_rail(s, b, 3 if rep else 2, fl)
                m4_engine(s, b, 3 if rep else 2, fl)
        s.hit(CRASH, b0 * 4, 100)
        s.hit(CRASH, (b0 + 8) * 4, 104)

    # -- C: the armoured train (chorale) + the build -------------------------------
    c0 = s.section("C · el tren blindado", M4_CHORALE_H)
    if A:
        s.line("horns", M4_CHORALE, c0, 88, LEGATO, accent=4)
        s.harmonize("tbn", M4_CHORALE, c0, 78, LEGATO, voices=2)
    else:
        s.line("choir", M4_CHORALE, c0, 90, LEGATO, accent=4)
        s.harmonize("strings", M4_CHORALE, c0, 70, LEGATO, voices=2)
        s.line("horns", M4_CHORALE[8:], c0 + 8, 74, LEGATO)
    for b in range(c0, c0 + 12):
        bpc, _ = s.chord(s.harmony[b][0][2])
        s.n("tuba", in_range(bpc, pitch("E1")), b * 4, 4 * LEGATO, 76)
        m4_rail(s, b, 0, fl)
        s.pattern("bass", b, "r.r.r.r.r.r.r.r.", "E1", 52, art=0.6)
        if (b - c0) % 4 == 3:
            s.roll("timp", b * 4 + 2.0, 2.0, 46, 84, 0.25,
                   p=in_range(s.chord(s.harmony[b][0][2])[0], pitch("E2")))
    k0 = s.section("Subida", M4_BUILD_H)
    s.line("tpt", M4_BUILD, k0, 94, MARCATO, swell=4)
    s.line("horns", M4_BUILD, k0, 84, MARCATO, octave=-1, swell=4)
    s.line("tbn", M4_BUILD_ANS, k0, 92, MARCATO, swell=4)
    for b in range(k0, k0 + 4):
        m4_rail(s, b, 1 if b < k0 + 2 else 2, fl)
        m4_engine(s, b, 2, fl)
        s.chords("trem", b, "A3", 54 + 8 * (b - k0))
    s.roll(SNARE, (k0 + 2) * 4, 7.75, 40, 112)
    s.roll("timp", (k0 + 3) * 4, 4.0, 60, 110, 0.25, p=in_range((11 + v.transpose) % 12, pitch("E2")))

    # -- A3: tutti ---------------------------------------------------------------------
    a3 = s.section("A'' · tutti", M4_THEME_H + " | " + M4_THEME_H)
    for rep in range(2):
        b1 = a3 + 8 * rep
        s.line("tpt", M4_THEME, b1, 102, MARCATO)
        s.harmonize("horns" if A else "brass", M4_THEME, b1, 80, MARCATO)
        if rep == 1:
            s.line("strings", M4_COUNTER, b1, 80, LEGATO)
            s.line("tbn", M4_THEME, b1, 88, MARCATO, octave=-1)
            if not A:
                s.line("horns", M4_THEME, b1, 80, MARCATO, octave=-1)
        for b in range(b1, b1 + 8):
            if rep == 0:
                s.chords("tbn", b, "D3", 78, hits=(0.0, 1.5, 2.0))
            s.chords("trem", b, "A3", 60)
            m4_rail(s, b, 3, fl)
            m4_engine(s, b, 3, fl)
        s.hit(CRASH, b1 * 4, 106)

    # -- Coda: the motif climbs, back to the engine ----------------------------------
    d0 = s.section("Vuelta", M4_CODA_H)
    s.line("tpt", M4_CODA, d0, 102, MARCATO)
    s.line("horns", M4_CODA, d0, 88, MARCATO, octave=-1)
    s.line("tbn", M4_CODA[:3], d0, 84, MARCATO, octave=-1)
    for b in range(d0, d0 + 4):
        m4_rail(s, b, 3, fl)
        m4_engine(s, b, 3, fl)
    s.chords("tbn", d0 + 3, "D3", 100, hits=(0.0, 1.0, 2.0, 2.5))
    s.chords("tuba", d0 + 3, "E2", 96, hits=(0.0, 1.0, 2.0, 2.5))
    s.roll(SNARE, (d0 + 3) * 4 + 3.0, 1.0, 70, 110, 0.125)
    return s


# =============================================================================================
# MAP05 -- Volga Dam (written in C minor)
# =============================================================================================
# The motif: a rising minor arpeggio in long dotted notes -- the wall of the dam -- that
# lands on a suspension (C over G) and climbs an octave across eight bars.

M5_INTRO_H = "Cm | Cm | Ab | G"
M5_INTRO_TBN = mel("C3:6 Eb3:2 G3:8 | G3:16 | Ab3:6 G3:2 F3:4 Eb3:4 | D3:16")
M5_THEME_H = "Cm | Ab | Fm,G | G | Cm | Ab | Fm,G7 | Cm"
M5_THEME = mel("""
C4:6 Eb4:2 G4:8 | Ab4:6 G4:2 F4:4 Eb4:4 | F4:4 Ab4:4 C5:6 B4:2 | D5:6 C5:2 B4:8 |
G4:6 C5:2 Eb5:8 | Eb5:6 C5:2 Ab4:4 C5:4 | F5:6 Eb5:2 D5:4 B4:4 | C5:12 r:4""")
M5_TBN_COUNTER = mel("""Eb3:8 G3:8 | Ab3:8 Eb3:8 | C3:8 D3:8 | B2:8 G2:8 |
C3:8 Eb3:8 | Eb3:8 Ab3:8 | Ab3:8 F3:8 | Eb3:16""")
M5_RIVER_H = "Eb | Bb/D | Cm | Ab | Eb/G | Fm | Bb | Bb7"
M5_RIVER = mel("""G4:8 Bb4:4 Eb5:4 | D5:8 C5:4 Bb4:4 | C5:6 Bb4:2 G4:8 | Ab4:6 Bb4:2 C5:8 |
Bb4:8 Eb5:4 G5:4 | F5:6 Eb5:2 C5:8 | D5:6 C5:2 Bb4:4 F4:4 | Bb4:12 r:4""")
M5_DEV_H = "Ab | Bb | Cm | Db | Ab/C | Fm | G | G7"
M5_DEV = mel("""Ab3:6 C4:2 Eb4:8 | Bb3:6 D4:2 F4:8 | C4:6 Eb4:2 G4:8 | Db4:6 F4:2 Ab4:8 |
C5:4 Ab4:4 Eb4:4 Ab4:4 | F4:4 Ab4:4 C5:4 F5:4 | G5:8 D5:4 B4:4 | G4:4 B4:4 D5:4 F5:4""")
M5_DEV_WHO = ["tbn", "horns", "tpt", "tutti", "tutti", "tutti", "tutti", "tutti"]
M5_HALL_H = "Cm | Cm | Ab | Ab | Fm | Fm | Db | G"
M5_HALL = mel("""C3:12 Eb3:4 | G3:16 | Ab3:12 G3:4 | F3:8 Eb3:8 | F3:8 Ab3:8 | C4:16 |
Db4:12 C4:4 | B3:16""")
M5_BUILD_H = "Ab | Ab | G | G7"
M5_BUILD = mel("Eb4:4 Ab4:4 C5:8 | Eb5:16 | D5:4 D5:4 D5:4 D5:4 | B4:4 D5:4 F5:4 G5:4")

M5_VARIANTS = (
    Variant("D_SDM05A", "A", 116.0, 0, "Do menor, 116 BPM: zumbido de órgano en los graves, pulso de "
            "turbina en corcheas, trompas en el tema, el río en las cuerdas"),
    Variant("D_SDM05B", "B", 108.0, 2, "Re menor, 108 BPM, en medio tiempo: tema en cuerdas + coro, "
            "taiko en vez de bombo, contrabajos; el río en la trompa sola"),
)


def m5_machine(s: Song, b: int, level: int, flavour: str) -> None:
    """Hum (organ, every bar), turbine pulse, the machinery's 3-against-4 bell."""
    for start, beats, name in s.harmony[b]:
        bpc, tones = s.chord(name)
        r = in_range(bpc, pitch("C2"))
        s.n("hum", r, b * 4 + start, beats * 0.99, 58 + 6 * min(level, 2))
        s.n("hum", r + 7 if (r + 7) % 12 in tones else r + 12, b * 4 + start, beats * 0.99, 50 + 6 * min(level, 2))
    # the bell on every dotted quarter, counted from the start of the piece
    for k in range(16):
        if (b * 16 + k) % 6 == 0:
            s.hit(RIDE_BELL, b * 4 + 0.25 * k, 34 + 8 * min(level, 2))
    if flavour == "A":
        s.pattern("bass", b, "R.r.R.r.R.r.R.r." if level >= 1 else "r.......r.......", "C1", 74, art=0.7)
    else:
        s.pattern("bass", b, "R..rR...R..rR..." if level >= 1 else "r-------r-------", "C2", 72, art=0.8)
    if level >= 2:
        s.pattern("low", b, "R.r.r.r.O.r.r.r." if flavour == "A" else "RrrrRrrrRrrrRrrr", "C2", 64,
                  art=0.55, accent=12)


def m5_drums(s: Song, b: int, level: int, flavour: str) -> None:
    if flavour == "A":
        pats = {LOW_FLOOR_TOM: "..g...g...g...g."}
        if level >= 1:
            pats[KICK] = "X.......X......."
        if level >= 2:
            pats[SNARE] = "....X.......X..."
        if level >= 3:
            pats[KICK] = "X.....x.X......."
            pats[SNARE] = "....X.......X.gg"
        s.drums(b, pats, 92)
    else:
        pats = {LOW_FLOOR_TOM: "..g...g...g...g."}
        if level >= 2:
            pats[SNARE] = "........X......."
        if level >= 3:
            pats[SNARE] = "........X.....gg"
            pats[CLOSED_HH] = "x.x.x.x.x.x.x.x."
        s.drums(b, pats, 92)
        if level >= 1:
            for t, v in ((0.0, 104), (1.5, 80), (2.5, 72 if level >= 3 else 0)):
                if v:
                    s.n("taiko", pitch("C3"), b * 4 + t, 0.5, v)
    if level >= 1:
        s.timp(b, "R.......F......." if level < 3 else "R.....r.F...F.f.", 80)


def build_map05(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "hum": Part(ORGAN, 84, 64, 40),
        "bass": Part(SYNTH_BASS_2 if A else CONTRABASS, 88, 64),
        "low": Part(CELLO, 82, 30),
        "trem": Part(TREMOLO, 70, 92),
        "strings": Part(STRINGS, 96, 76),
        "tbn": Part(TROMBONE, 98, 88),
        "tuba": Part(TUBA, 88, 60),
        "horns": Part(HORNS, 120, 44),
        "tpt": Part(TRUMPET, 96, 54),
        "timp": Part(TIMPANI, 94, 70),
        "choir": Part(CHOIR, 86, 64),
    }
    if not A:
        parts["taiko"] = Part(TAIKO, 88, 64, 50)
    s = Song(v.lump, "MAP05 Volga Dam", v.bpm, v.transpose, (0 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "strings") if not A else ("horns", "tpt", "tbn"))
    fl = v.flavour

    i0 = s.section("Intro · la sala de turbinas", M5_INTRO_H)
    s.line("tbn", M5_INTRO_TBN, i0, 98, LEGATO)
    s.line("tuba", M5_INTRO_TBN, i0, 70, LEGATO, octave=-1)
    for b in range(i0, i0 + 4):
        m5_machine(s, b, 1, fl)
        m5_drums(s, b, 1 if b > i0 else 0, fl)
    s.roll("timp", (i0 + 3) * 4, 4.0, 40, 104, 0.25, p=in_range((7 + v.transpose) % 12, pitch("E2")))

    # -- A1 ----------------------------------------------------------------------------------
    a1 = s.section("A · el tema", M5_THEME_H)
    if A:
        s.line("horns", M5_THEME, a1, 100, LEGATO)
    else:
        s.line("strings", M5_THEME, a1, 96, LEGATO)
        s.line("choir", M5_THEME, a1, 84, LEGATO)
    for b in range(a1, a1 + 8):
        m5_machine(s, b, 2, fl)
        m5_drums(s, b, 2, fl)
        s.chords("trem", b, "G3", 52)
        if not A:
            s.chords("horns", b, "F3", 60, art=LEGATO)
    s.hit(CRASH, a1 * 4, 100)

    # -- A2: trumpets + horns, trombone counter-line ------------------------------------------
    a2 = s.section("A' · metales", M5_THEME_H)
    s.line("tpt", M5_THEME, a2, 96, LEGATO)
    s.line("horns", M5_THEME, a2, 92, LEGATO, octave=0 if A else -1)
    s.line("tbn", M5_TBN_COUNTER, a2, 90, LEGATO)
    if not A:
        s.line("choir", M5_THEME, a2, 76, LEGATO)
    for b in range(a2, a2 + 8):
        m5_machine(s, b, 2, fl)
        m5_drums(s, b, 3, fl)
        s.chords("trem", b, "G3", 62)
    s.hit(CRASH, a2 * 4, 104)

    # -- B: the river, then the spillway -----------------------------------------------------
    r0 = s.section("B · el río", M5_RIVER_H)
    if A:
        s.line("strings", M5_RIVER, r0, 92, LEGATO, accent=4)
        for b in range(r0, r0 + 8):
            s.chords("horns", b, "Eb3", 58)
    else:
        s.line("horns", M5_RIVER, r0, 98, LEGATO, accent=4)
        for b in range(r0, r0 + 8):
            s.chords("strings", b, "G3", 58)
            s.chords("choir", b, "Bb3", 50)
    for b in range(r0, r0 + 8):
        m5_machine(s, b, 1, fl)
        m5_drums(s, b, 1, fl)
    s.hit(CRASH, r0 * 4, 84)
    d0 = s.section("B' · el aliviadero", M5_DEV_H)
    for i, (who, bar) in enumerate(zip(M5_DEV_WHO, M5_DEV)):
        b = d0 + i
        if who in ("tbn", "tutti"):
            s.line("tbn", [bar], b, 94, LEGATO, octave=0 if who == "tbn" else -1 if i >= 4 else 0)
        if who in ("horns", "tutti"):
            s.line("horns", [bar], b, 96, LEGATO)
        if who in ("tpt", "tutti"):
            s.line("tpt", [bar], b, 94 + 2 * i, LEGATO)
        if i >= 4:
            s.line("strings", [bar], b, 84, LEGATO, octave=1)
        s.chords("trem", b, "G3", 56 + 3 * i)
        m5_machine(s, b, 2, fl)
        m5_drums(s, b, 2 if i < 4 else 3, fl)
    s.roll(SNARE, (d0 + 7) * 4, 4.0, 50, 104)

    # -- C: the turbine hall -------------------------------------------------------------------
    h0 = s.section("C · las turbinas", M5_HALL_H)
    s.line("tbn", M5_HALL, h0, 94, LEGATO)
    s.line("tuba", M5_HALL, h0, 80, LEGATO, octave=-1)
    if not A:
        for b in range(h0, h0 + 8):
            s.chords("choir", b, "C4", 52)
    for b in range(h0, h0 + 8):
        m5_machine(s, b, 2, fl)
        s.pattern("low", b, "RrrrRrrrRrrrRrrr", "C2", 58, art=0.6, accent=16)
        m5_drums(s, b, 1, fl)
    s.hit(CRASH, h0 * 4, 90)
    k0 = s.section("Subida", M5_BUILD_H)
    s.line("horns", M5_BUILD, k0, 94, LEGATO, swell=3)
    s.line("tpt", M5_BUILD[2:], k0 + 2, 96, MARCATO, swell=4)
    for b in range(k0, k0 + 4):
        m5_machine(s, b, 2, fl)
        s.pattern("strings", b, "rtforfotrtforfot", "G3", 60 + 6 * (b - k0), art=0.6)
        m5_drums(s, b, 2, fl)
    s.roll(SNARE, (k0 + 2) * 4, 8.0, 40, 112)
    s.roll("timp", (k0 + 3) * 4, 4.0, 60, 110, 0.25, p=in_range((7 + v.transpose) % 12, pitch("E2")))

    # -- A3: the whole dam -----------------------------------------------------------------------
    a3 = s.section("A'' · tutti", M5_THEME_H + " | " + M5_THEME_H)
    for rep in range(2):
        b1 = a3 + 8 * rep
        s.line("tpt", M5_THEME, b1, 100, LEGATO)
        s.line("horns", M5_THEME, b1, 96, LEGATO, octave=0 if rep == 0 else -1)
        if rep == 0:
            s.harmonize("tbn", M5_THEME, b1, 82, LEGATO, voices=2)
        else:
            s.line("tbn", M5_TBN_COUNTER, b1, 92, LEGATO)
            s.line("strings", M5_THEME, b1, 82, LEGATO, octave=1)
        s.line("tuba", M5_TBN_COUNTER, b1, 78, LEGATO, octave=-1)
        for b in range(b1, b1 + 8):
            s.chords("choir", b, "G3", 58 if A else 64)
            s.chords("trem", b, "G3", 64)
            m5_machine(s, b, 2, fl)
            m5_drums(s, b, 3, fl)
        s.hit(CRASH, b1 * 4, 108)
    last = a3 + 15
    s.roll(SNARE, last * 4 + 2.0, 2.0, 50, 100, 0.125)
    return s


# =============================================================================================
# MAP06 -- Red Square (written in F minor)
# =============================================================================================
# The motif: tonic, a leap to the fifth held in a march dotted rhythm, and the minor sixth
# leaning on it (C-Db-C) -- the parade under the Kremlin wall. Brass choir underneath.

M6_INTRO_H = "Fm | Fm | Fm | C"
M6_FANFARE = mel("C5:2 C5:1 C5:1 E5:4 C5:2 C5:1 C5:1 G4:4")
M6_THEME_H = "Fm | Bbm | Db,C | C | Fm | Bbm,Db | Bbm,C7 | Fm"
M6_THEME = mel("""
F4:4 C5:3 C5:1 C5:4 Db5:2 C5:2 | Bb4:3 Ab4:1 Bb4:4 Db5:4 F4:4 |
Ab4:3 Bb4:1 Ab4:2 F4:2 G4:3 Ab4:1 Bb4:4 | C5:8 G4:4 E4:4 |
F4:4 C5:3 C5:1 C5:4 Db5:2 C5:2 | Db5:3 C5:1 Bb4:4 F5:6 Db5:2 |
Db5:3 C5:1 Bb4:2 Ab4:2 G4:3 Bb4:1 E4:4 | F4:12 r:4""")
M6_CHORALE_H = "Db | Ab/C | Bbm | Fm/Ab | Gb | Db/F | Eb7 | C"
M6_CHORALE = mel("""Ab4:8 F4:8 | Eb5:8 C5:8 | Db5:8 F5:8 | C5:16 | Bb4:8 Db5:8 | F5:8 Db5:8 |
G4:8 Bb4:8 | C5:16""")
M6_BOSS_H = "Fm | Gb/F | Fm | Gb/F | Db | Bdim7 | C | C"
M6_BOSS = mel("""C5:4 Db5:4 C5:4 r:4 | Bb4:3 Db5:1 C5:4 Gb4:8 | F4:3 F4:1 Ab4:4 C5:4 Db5:4 | C5:16 |
F5:4 Eb5:4 Db5:4 Ab4:4 | Ab4:4 B4:4 D5:4 F5:4 | G4:3 Ab4:1 G4:4 E4:4 C4:4 | C4:4 r:4 C5:4 r:4""")
M6_BUILD_H = "Db | Ddim7 | Eb | Edim7 | Fm | F#dim7 | C | C7"
M6_BUILD = mel("""Ab4:2 Ab4:1 Ab4:1 Ab4:4 Db5:4 F5:4 | Ab4:2 Ab4:1 Ab4:1 Ab4:4 D5:4 F5:4 |
Bb4:2 Bb4:1 Bb4:1 Bb4:4 Eb5:4 G5:4 | Bb4:2 Bb4:1 Bb4:1 Bb4:4 Db5:4 G5:4 |
C5:2 C5:1 C5:1 C5:4 F5:4 Ab5:4 | C5:2 C5:1 C5:1 C5:4 Eb5:4 A5:4 | G5:8 E5:4 C5:4 |
Bb4:4 C5:4 E5:4 G5:4""")
M6_CODA_H = "Db | Bbm | C | C7"
M6_CODA = mel("Ab4:8 Db5:4 F5:4 | F5:8 Db5:4 Bb4:4 | C5:16 | C5:2 C5:1 C5:1 C5:4 r:8")

M6_VARIANTS = (
    Variant("D_SDM06A", "A", 120.0, 0, "Fa menor, 120 BPM: marcha con caja militar, trompetas en el tema "
            "y coro de metales debajo, coral con campanas, arena del jefe en semicorcheas"),
    Variant("D_SDM06B", "B", 112.0, -2, "Mi bemol menor, 112 BPM, más solemne y pesada: tema en trompas + "
            "coro, caja con redobles, taiko; la arena con metales en bloque"),
)
BOSS_BARS = (28, 52)                 # B + B' of MAP06, cut out as the boss-arena loop

MARCH_A = ("X..xX.x.X..xX.x.", "X..xX.x.X.x.RRRR")
MARCH_B = ("X.RxX.x.X.RxX.x.", "X.RxX.RxX.R.RRRR")


def m6_march(s: Song, b: int, flavour: str, level: int, phrase_pos: int) -> None:
    pats = {}
    if level == 0:                                    # muffled roll (chorale)
        pats[SNARE] = "gggggggggggggggg"
        s.drums(b, pats, 60)
        s.hit(KICK, b * 4, 58)
        return
    if level == 1:
        pats[SNARE] = MARCH_A[phrase_pos % 2] if flavour == "A" else MARCH_B[phrase_pos % 2]
    if level >= 2:
        pats[SNARE] = (MARCH_A if flavour == "A" else MARCH_B)[phrase_pos % 2]
        pats[KICK] = "X.......X......."
    if level >= 3:                                    # the arena: relentless
        pats[SNARE] = "XgxgXgxgXgxgXgxg" if flavour == "A" else "X.xgX.xgXgxgX.RR"
        pats[KICK] = "X..X..X.X..X..X."
        pats[LOW_TOM] = "..............xx"
    s.drums(b, pats, 92)
    if flavour == "B" and level >= 2:
        s.n("taiko", pitch("C3"), b * 4, 0.5, 98)
        s.n("taiko", pitch("C3"), b * 4 + 2, 0.5, 84)


def build_map06(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "tuba": Part(TUBA, 92, 60),
        "bass": Part(CONTRABASS, 84, 64),
        "low": Part(CELLO, 80, 30),
        "trem": Part(TREMOLO, 72, 92),
        "strings": Part(STRINGS, 86, 76),
        "tbn": Part(TROMBONE, 98, 88),
        "horns": Part(HORNS, 120, 44),
        "tpt": Part(TRUMPET, 106, 54),
        "timp": Part(TIMPANI, 94, 70),
        "choir": Part(CHOIR, 80, 64),
        "bells": Part(TUBULAR_BELLS, 100, 80),
    }
    if not A:
        parts["taiko"] = Part(TAIKO, 88, 64, 50)
        parts["brass"] = Part(BRASS, 100, 72)
    s = Song(v.lump, "MAP06 Red Square", v.bpm, v.transpose, (5 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "tbn", "brass"))
    fl = v.flavour

    # -- Intro: the drums of the parade -------------------------------------------------------
    i0 = s.section("Intro · el desfile", M6_INTRO_H)
    for b in range(i0, i0 + 4):
        m6_march(s, b, fl, 2, b - i0)
        s.chords("trem", b, "F3", 50 + 4 * (b - i0))
        s.timp(b, "R.......R......." if b < i0 + 3 else "R...R...R...RRRR", 76)
        if b < i0 + 3:
            s.n("tuba", in_range((5 + v.transpose) % 12, pitch("C2")), b * 4, 4 * LEGATO, 70)
            s.n("tbn", in_range((5 + v.transpose) % 12, pitch("C3")), b * 4, 4 * LEGATO, 64)
    s.line("tpt", M6_FANFARE, i0 + 3, 100, MARCATO)
    s.chords("tbn", i0 + 3, "E3", 80, hits=(0.0, 1.0, 2.0, 3.0), length=0.6)

    def theme_block(b1: int, big: bool) -> None:
        lead = "tpt" if (A or big) else "horns"
        s.line(lead, M6_THEME, b1, 100, MARCATO)
        if not A and not big:
            s.line("choir", M6_THEME, b1, 88, LEGATO)
        if A and not big:
            s.harmonize("horns", M6_THEME, b1, 78, MARCATO)
        if big:
            s.line("horns", M6_THEME, b1, 94, MARCATO, octave=-1)
            s.harmonize("tbn", M6_THEME, b1, 84, MARCATO, octave=-1, voices=2)
            s.harmonize("brass" if not A else "choir", M6_THEME, b1, 66 if A else 76, LEGATO)
        for b in range(b1, b1 + 8):
            if not big:
                s.chords("tbn", b, "D3", 76, hits=(0.0, 2.0), length=0.9)
            s.pattern("tuba", b, "R.......F.......", "C2", 82, art=0.85)
            s.timp(b, "R.......F.......", 82)
            m6_march(s, b, fl, 2, b - b1)
            if big:
                s.chords("trem", b, "F3", 60)
        s.hit(CRASH, b1 * 4, 104)
        s.hit(CRASH2, (b1 + 4) * 4, 86)

    a1 = s.section("A · el tema", M6_THEME_H)
    theme_block(a1, big=False)
    a2 = s.section("A' · coro de metales", M6_THEME_H)
    theme_block(a2, big=True)
    if A:
        for b in range(a2, a2 + 8):
            s.chords("choir", b, "F3", 54)

    # -- The chorale: the Kremlin ---------------------------------------------------------------
    c0 = s.section("Coral · el Kremlin", M6_CHORALE_H)
    top = "horns" if A else "choir"
    s.line(top, M6_CHORALE, c0, 90, LEGATO, accent=4)
    s.harmonize("tbn" if A else "strings", M6_CHORALE, c0, 80 if A else 72, LEGATO, voices=2)
    s.line("choir" if A else "horns", M6_CHORALE, c0, 66 if A else 70, LEGATO, octave=0 if A else -1)
    for b in range(c0, c0 + 8):
        bpc, _ = s.chord(s.harmony[b][0][2])
        s.n("tuba", in_range(bpc, pitch("C2")), b * 4, 4 * LEGATO, 74)
        first = M6_CHORALE[b - c0][0][0]
        s.n("bells", pitch(first) + v.transpose + 12 if pitch(first) + v.transpose < 72 else pitch(first) + v.transpose,
            b * 4, 3.0, 84 if (b - c0) % 2 == 0 else 70)
        m6_march(s, b, fl, 0, 0)
    s.roll("timp", (c0 + 7) * 4, 4.0, 40, 108, 0.25, p=in_range((0 + v.transpose) % 12, pitch("E2")))

    # -- B: the boss arena ------------------------------------------------------------------------
    b0 = s.section("B · la arena del jefe", M6_BOSS_H + " | " + M6_BOSS_H)
    assert b0 == BOSS_BARS[0], b0
    for rep in range(2):
        b1 = b0 + 8 * rep
        s.line("horns", M6_BOSS, b1, 100, MARCATO)
        s.line("tbn", M6_BOSS, b1, 94, MARCATO, octave=-1)
        if rep == 1:
            s.line("tpt", M6_BOSS, b1, 92, MARCATO)
        for b in range(b1, b1 + 8):
            s.pattern("low", b, "RrrnRrrnRrrnRrfo", "C2", 76, art=0.6, accent=16)
            s.pattern("bass", b, "R.r.R.r.R.r.R.r.", "E1", 80, art=0.6)
            stab = "brass" if not A else "tpt"
            if A and rep == 0 or not A:
                s.chords(stab, b, "A4" if A else "F4", 84, hits=(0.0, 0.75, 1.5, 2.5, 3.0), length=0.3)
            s.chords("trem", b, "F3", 58 + 8 * rep)
            if rep == 1:
                s.chords("choir", b, "F3", 62)
            s.timp(b, "R.R.R.R.R.R.F.F.", 84)
            m6_march(s, b, fl, 3, b - b1)
        s.hit(CRASH, b1 * 4, 108)

    k0 = s.section("B' · subida", M6_BUILD_H)
    s.line("tpt", M6_BUILD, k0, 96, MARCATO, swell=1.5)
    s.line("horns", M6_BUILD, k0, 88, MARCATO, octave=-1, swell=1.5)
    for b in range(k0, k0 + 8):
        s.chords("tbn", b, "D3", 80 + 2 * (b - k0), hits=(0.0, 1.0, 2.0, 3.0), length=0.5)
        s.pattern("strings", b, "rtforfotrtforfot", "F3", 62 + 3 * (b - k0), art=0.6)
        s.pattern("low", b, "R.r.R.r.R.r.R.r.", "C2", 76)
        s.pattern("bass", b, "R...R...R...R...", "E1", 82)
        if not A and b - k0 in (0, 2, 4, 6):
            s.chords("brass", b, "F4", 96, hits=(0.0,), length=0.5)
        m6_march(s, b, fl, 2 if b < k0 + 6 else 3, b - k0)
        if b < k0 + 6:
            s.timp(b, "R...R...R...R...", 80)
    s.roll("timp", (k0 + 6) * 4, 8.0, 56, 112, 0.25, p=in_range((0 + v.transpose) % 12, pitch("E2")))
    s.roll(SNARE, (k0 + 7) * 4, 4.0, 60, 116, 0.125)

    # -- A3: the whole square ---------------------------------------------------------------------
    a3 = s.section("A'' · tutti", M6_THEME_H + " | " + M6_THEME_H)
    theme_block(a3, big=True)
    theme_block(a3 + 8, big=True)
    s.line("strings", M6_THEME, a3 + 8, 80, LEGATO, octave=1)
    for b in range(a3, a3 + 16):
        s.chords("choir", b, "F3", 60)

    # -- Coda: plagal turn, the drum leads back to the parade ------------------------------------
    d0 = s.section("Vuelta", M6_CODA_H)
    s.line("tpt", M6_CODA, d0, 98, MARCATO)
    s.line("horns", M6_CODA, d0, 90, MARCATO, octave=-1)
    for b in range(d0, d0 + 4):
        if b < d0 + 3:
            s.chords("tbn", b, "D3", 84, art=LEGATO)
        else:
            s.chords("tbn", b, "E3", 90, hits=(0.0, 1.0), length=0.6)
        bpc, _ = s.chord(s.harmony[b][0][2])
        s.n("tuba", in_range(bpc, pitch("C2")), b * 4, 4 * LEGATO if b < d0 + 3 else 1.5, 80)
        s.chords("choir", b, "F3", 60)
        m6_march(s, b, fl, 2, b - d0)
    s.roll(SNARE, (d0 + 3) * 4 + 2.0, 2.0, 50, 110, 0.125)
    return s


# =============================================================================================
# Episode 2 intermission -- the three motifs (written in F minor)
# =============================================================================================
# bars 1-8 the Red Square theme (the destination), 9-12 the Trans-Siberian motif a semitone
# up, 13-16 the Volga Dam cadence: the whole road in sixteen bars.

INT_H = M6_THEME_H + " | Fm | Eb | Db,Bbm | C7 | Fm | Db | Bbm,C7 | Fm"
INT_TRAIN = mel("""F4:2 F4:1 F4:1 Ab4:2 F4:2 C5:6 Bb4:2 | Eb4:2 Eb4:1 Eb4:1 G4:2 Eb4:2 Bb4:6 Ab4:2 |
F5:4 Eb5:2 Db5:2 Db5:3 C5:1 Bb4:4 | C5:6 Bb4:1 Ab4:1 G4:4 E4:4""")
INT_DAM = mel("C4:6 F4:2 Ab4:8 | Ab4:6 F4:2 Db4:4 F4:4 | Bb4:6 Ab4:2 G4:4 E4:4 | F4:12 r:4")

INT_VARIANTS = (
    Variant("D_SDE2IA", "A", 92.0, 0, "Fa menor, 92 BPM, recogida: trompa sola con cuerdas, "
            "el tren en trompeta con sordina y pizzicato, la presa en metales"),
    Variant("D_SDE2IB", "B", 104.0, 0, "Fa menor, 104 BPM, en marcha: trompetas, caja militar y "
            "coro de metales; los tres motivos sin pausa"),
)


def build_intermission(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "tuba": Part(TUBA, 84, 60),
        "low": Part(CELLO, 80, 30),
        "pizz": Part(PIZZ, 80, 84),
        "strings": Part(STRINGS, 84, 76),
        "tbn": Part(TROMBONE, 92, 88),
        "horns": Part(HORNS, 112, 44),
        "tpt": Part(MUTED_TRUMPET if A else TRUMPET, 116 if A else 96, 54),
        "timp": Part(TIMPANI, 88, 70),
        "pad": Part(PAD_HALO, 56, 64),
    }
    s = Song(v.lump, "Episode 2 intermission", v.bpm, v.transpose, 5, parts,
             lead_parts=("horns", "tpt", "tbn"))
    i0 = s.section("Plaza Roja (tema)", M6_THEME_H)
    t0 = s.section("Transiberiano", "Fm | Eb | Db,Bbm | C7")
    d0 = s.section("La presa y cadencia", "Fm | Db | Bbm,C7 | Fm")
    if A:
        s.line("horns", M6_THEME, i0, 92, LEGATO, accent=4)
        s.line("tpt", INT_TRAIN, t0, 84, MARCATO)
        s.line("horns", INT_DAM, d0, 94, LEGATO)
        s.line("tbn", INT_DAM, d0, 78, LEGATO, octave=-1)
        for b in range(s.bars):
            s.chords("strings", b, "F3", 54 if b < 12 else 62)
            s.chords("pad", b, "C4", 40)
            for start, beats, name in s.harmony[b]:
                bpc, _ = s.chord(name)
                s.n("low", in_range(bpc, pitch("C2")), b * 4 + start, beats * LEGATO, 64)
            if t0 <= b < d0:
                s.pattern("pizz", b, "r.f.o.f.r.f.o.f.", "C3", 64, art=0.5)
            if b % 4 == 3:
                s.roll("timp", b * 4 + 2.0, 2.0, 36, 70, 0.25, p=in_range(bpc, pitch("E2")))
        s.drums(7, {SNARE: "........gggggggg"}, 60)
        s.drums(15, {SNARE: "........gggggggg"}, 64)
    else:
        s.line("tpt", M6_THEME, i0, 96, MARCATO)
        s.harmonize("horns", M6_THEME, i0, 74, MARCATO)
        s.line("horns", INT_TRAIN, t0, 96, MARCATO)
        s.line("tbn", INT_TRAIN, t0, 84, MARCATO, octave=-1)
        s.line("tpt", INT_DAM, d0, 98, LEGATO)
        s.line("horns", INT_DAM, d0, 90, LEGATO, octave=-1)
        s.harmonize("tbn", INT_DAM, d0, 80, LEGATO, voices=2, octave=-1)
        for b in range(s.bars):
            s.pattern("tuba", b, "R.......F.......", "C2", 80)
            s.timp(b, "R.......F.......", 76)
            m6_march(s, b, "A", 2, b)
            s.chords("strings", b, "F3", 52)
            if b < 12 and b not in range(t0, d0):
                s.chords("tbn", b, "D3", 70, hits=(0.0, 2.0), length=0.9)
            if t0 <= b < d0:
                s.pattern("pizz", b, "R.r.R.r.R.r.R.r.", "C3", 70, art=0.5)
        s.hit(CRASH, 0, 96)
        s.hit(CRASH, t0 * 4, 90)
        s.hit(CRASH, d0 * 4, 96)
        s.roll(SNARE, 15 * 4 + 2.0, 2.0, 50, 96, 0.125)
    return s


# =============================================================================================
# Catalogue, checks, rendering
# =============================================================================================

PIECES = {"MAP04": (build_map04, M4_VARIANTS), "MAP05": (build_map05, M5_VARIANTS),
          "MAP06": (build_map06, M6_VARIANTS), "E2INT": (build_intermission, INT_VARIANTS)}
BOSS_LUMP = {"D_SDM06A": "D_SDBS6A", "D_SDM06B": "D_SDBS6B"}
# Target loudness of the loop (RMS dBFS through zmusic): MAP01's installed N2 sits at -25.7.
TARGET_RMS = {"MAP04": -25.7, "MAP05": -25.9, "MAP06": -25.7, "E2INT": -28.5}
RECOMMENDED = {"D_SDM04A", "D_SDM05A", "D_SDM06A", "D_SDE2IA", "D_SDBS6A"}


def all_songs() -> list[tuple[str, Variant, Song]]:
    out = []
    for key, (fn, variants) in PIECES.items():
        for v in variants:
            out.append((key, v, fn(v)))
    return out


def self_check(songs) -> list[str]:
    """Structure checks (bar sums are checked by mel()). Returns problems."""
    import compose_map01 as cm
    problems = []

    def shapes(bars):
        out = set()
        for a, b in zip(bars, bars[1:]):
            seq = [(pitch(n), d) for n, d in a + b if n]
            out.add((tuple(y - x for (x, _), (y, _) in zip(seq, seq[1:])), tuple(d for _, d in a + b)))
        return out

    ours = set()
    for bars in (cm.THEME, [b for _, b in cm.ADVANCE], cm.LAMENT, cm.BUILD):
        ours |= shapes(bars)
    themes = {"M4_THEME": M4_THEME, "M4_STEPPE": M4_STEPPE, "M4_PURSUIT": M4_PURSUIT,
              "M5_THEME": M5_THEME, "M5_RIVER": M5_RIVER, "M6_THEME": M6_THEME, "M6_BOSS": M6_BOSS}
    for name, bars in themes.items():
        clash = shapes(bars) & ours
        if clash:
            problems.append(f"{name}: a two-bar shape equals one of MAP01's ({len(clash)})")
    for key, v, s in songs:
        if any(not 0 <= p <= 127 for _, p, *_ in s.notes):
            problems.append(f"{v.lump}: a note outside the MIDI range")
        for part, p, st, ln, vel in s.notes:
            lo, hi = RANGE.get(s.parts[part].program, (0, 127))
            if part in ("tpt", "horns", "tbn", "choir") and not lo - 5 <= p <= hi:
                problems.append(f"{v.lump}: {part} note {p} at beat {st} outside {lo}-{hi}")
                break
        secs = s.seconds()
        lo_s, hi_s = (30, 60) if key == "E2INT" else (110, 190)
        if not lo_s <= secs <= hi_s:
            problems.append(f"{v.lump}: loop {secs:.1f} s outside {lo_s}-{hi_s} s")
        if not any(st < 0.01 for _, _, st, _, _ in s.notes) and not any(st < 0.01 for _, st, _ in s.hits):
            problems.append(f"{v.lump}: nothing sounds on beat 1 (the seam)")
        if max(st + ln for _, _, st, ln, _ in s.notes) > s.bars * 4 + 1e-6:
            problems.append(f"{v.lump}: a note runs past the loop point")
    return problems


def render_lump(data: bytes, extra: float = SEAM_PREVIEW_S):
    import gen_enemy_alts as ea
    secs = ea.seconds_of(data)
    x, rate = ea.zmusic_render(data, secs + extra)
    return x, rate, secs


def write_ogg(x, rate, path: Path) -> None:
    import gen_enemy_alts as ea
    import gen_weapon_sfx as gws
    ogg = gws.ogg_bytes(ea.stereo_wav(x, rate))
    if ogg is None:
        raise RuntimeError("ffmpeg is not on the PATH: no OGG")
    path.write_bytes(ogg)


def calibrate_and_render(key: str, v: Variant, s: Song, stems: bool) -> dict:
    import compose_map01 as cm
    import numpy as np
    target = TARGET_RMS[key]
    for _ in range(3):
        x, rate, secs = render_lump(s.midi(), 0.0)
        lv = cm.measure(x, rate)
        delta = target - lv["rms"]
        if abs(delta) < 0.4:
            break
        s.volume_scale *= 10 ** (delta / 40.0)    # FluidSynth CC7 ~ 40*log10
    data = s.midi()
    (OUT_DIR / f"{v.lump}.mid").write_bytes(data)
    x, rate, secs = render_lump(data)
    loop = x[: int(secs * rate)]
    lv = cm.measure(loop, rate)
    bar_s = secs / s.bars
    bounds = [b for _, b in s.sections] + [s.bars]
    lv["arc"] = {}
    for (label, b0), b1 in zip(s.sections, bounds[1:]):
        seg = loop[int(b0 * bar_s * rate): int(b1 * bar_s * rate)]
        lv["arc"][label] = round(float(20 * np.log10(max(np.sqrt(np.mean(seg.mean(axis=1) ** 2)), 1e-9))), 1)
    write_ogg(x, rate, RENDER_DIR / f"{v.lump}.ogg")
    row = {"lump": v.lump, "key": key, "flavour": v.flavour, "bpm": v.bpm, "label": v.label,
           "seconds": secs, "bars": s.bars, "levels": lv, "scale": round(s.volume_scale, 3),
           "sections": [(label, round(b * bar_s, 1)) for label, b in s.sections],
           "programs": sorted({p.program for p in s.parts.values()})}
    if stems:
        lead = [k for k in s.parts if k in s.lead_parts]
        xl, _, _ = render_lump(s.midi(mute=[k for k in s.parts if k not in lead] + ["drums"]), 0.0)
        xb, _, _ = render_lump(s.midi(mute=lead), 0.0)
        row["lead_over_bed_db"] = round(cm.measure(xl, rate)["rms"] - cm.measure(xb, rate)["rms"], 1)
    if v.lump in BOSS_LUMP:
        b0, b1 = BOSS_BARS
        boss = s.midi(b0, b1)
        name = BOSS_LUMP[v.lump]
        (OUT_DIR / f"{name}.mid").write_bytes(boss)
        xb2, rate2, secs2 = render_lump(boss)
        write_ogg(xb2, rate2, RENDER_DIR / f"{name}.ogg")
        lvb = cm.measure(xb2[: int(secs2 * rate2)], rate2)
        row["boss"] = {"lump": name, "seconds": secs2, "levels": lvb,
                       "sections": [("B · arena", 0.0), ("B' · subida", round(16 * bar_s, 1)),
                                    ("Costura (−5 s)", round(secs2 - 5, 1))]}
    return row


def levels_txt(rows: list[dict]) -> str:
    lines = ["# Episode 2 drafts (D104): loudness through zmusic + gzdoom.sf2, no normalisation",
             "# peak / RMS / loudest 3 s, dBFS, over the loop; renders run 10 s past the seam.",
             "# Reference: D_SDM1N2 (MAP01, installed) loop RMS -25.7, loud3s -22.3, peak -8.0", ""]
    for r in rows:
        lv = r["levels"]
        lines.append(f"{r['lump']:9s} {r['bpm']:5.0f} BPM  loop {r['seconds']:6.1f} s  peak {lv['peak']:6.1f}  "
                     f"RMS {lv['rms']:6.1f}  loud3s {lv['loud3s']:6.1f}  CC7 scale {r['scale']:.3f}"
                     + (f"  lead-over-bed {r['lead_over_bed_db']:+.1f} dB" if "lead_over_bed_db" in r else ""))
        lines.append("          arc RMS: " + ", ".join(f"{k} {val:.1f}" for k, val in lv["arc"].items()))
        if "boss" in r:
            b = r["boss"]
            lines.append(f"{b['lump']:9s} (MAP06 bars {BOSS_BARS[0] + 1}-{BOSS_BARS[1]})  loop {b['seconds']:6.1f} s  "
                         f"peak {b['levels']['peak']:6.1f}  RMS {b['levels']['rms']:6.1f}  "
                         f"loud3s {b['levels']['loud3s']:6.1f}")
    return "\n".join(lines) + "\n"


# -- The listening sheet --------------------------------------------------------------------------

GROUP_TEXT = {
    "MAP04": ("MAP04 · Trans-Siberian (estación de clasificación, tren blindado)",
              "Motor ferroviario: ostinato de bajo y cuerdas que no para, y una percusión de vías "
              "(charles en semicorcheas, el «ta-DUM» de la baqueta en el aro, el doble golpe de tom de "
              "los bogies). El motivo de 4 compases repite una nota como las ruedas en las juntas "
              "(mi-mi-mi) y salta a la quinta como un silbato. Forma: intro del motor · tema · tema en "
              "trompetas con contracanto · sección B · coral «el tren blindado» sobre las vías solas · "
              "subida · tutti · vuelta."),
    "MAP05": ("MAP05 · Volga Dam (sala de turbinas, presa enorme)",
              "Más ancha y grave: un zumbido de órgano sigue el bajo todo el rato, un pulso de turbina "
              "debajo y una campana mecánica que cae cada 3 corcheas (3 contra 4, maquinaria). El tema "
              "sube un arpegio menor en notas largas y acaba una octava más arriba: el muro de la presa. "
              "Forma: intro de turbinas · tema · tema en metales · el río (mi bemol mayor) · el "
              "aliviadero (el motivo sube en secuencia) · sala de turbinas (trombones lentos) · subida · tutti."),
    "MAP06": ("MAP06 · Red Square (el desfile, el Kremlin, el jefe)",
              "Marcial y solemne: caja militar, bombo en 1 y 3, tuba en «um-pa», trompetas con el tema y "
              "un coro de metales que armoniza cada nota. Un coral con campanas tubulares (el Kremlin) y "
              "una sección B mucho más tensa para la arena del jefe: semicorcheas de chelos con la "
              "semitonía fa-solb, golpes de metal sincopados, timbales en corcheas. Forma: desfile · "
              "tema · coro de metales · coral · arena · subida cromática · tutti · vuelta."),
    "BOSS": ("MAP06 · solo la arena del jefe (bucle aparte)",
             "Las secciones B + B' de cada versión de MAP06 cortadas como bucle propio, por si la arena "
             "del jefe cambia de música (24 compases). Mismas notas que dentro de la pieza."),
    "E2INT": ("Intermedio / tema del Episodio 2 (opcional)",
              "16 compases que recorren el camino: el tema de la Plaza Roja, el motivo del Transiberiano "
              "y la cadencia de la presa. Para la pantalla entre mapas o el texto del episodio."),
}


def sheet_html(rows: list[dict]) -> str:
    items = []
    for r in rows:
        jumps = [[label, t] for label, t in r["sections"]] + [["Costura (−5 s)", round(r["seconds"] - 5, 1)]]
        items.append({"id": r["lump"], "group": r["key"], "src": f"../episode2/render/{r['lump']}.ogg",
                      "len": f"{int(r['seconds'] // 60)}:{int(round(r['seconds'] % 60)):02d}", "bpm": round(r["bpm"]),
                      "what": r["label"], "jumps": jumps, "rec": r["lump"] in RECOMMENDED})
        if "boss" in r:
            b = r["boss"]
            items.append({"id": b["lump"], "group": "BOSS", "src": f"../episode2/render/{b['lump']}.ogg",
                          "len": f"{int(b['seconds'] // 60)}:{int(round(b['seconds'] % 60)):02d}", "bpm": round(r["bpm"]),
                          "what": f"La arena de {r['lump']} sola (compases {BOSS_BARS[0] + 1}-{BOSS_BARS[1]}), en bucle.",
                          "jumps": b["sections"], "rec": b["lump"] in RECOMMENDED})
    order = ["MAP04", "MAP05", "MAP06", "BOSS", "E2INT"]
    items.sort(key=lambda it: (order.index(it["group"]), it["id"]))
    groups = {k: list(v) for k, v in GROUP_TEXT.items()}
    return SHEET_TEMPLATE.replace("__ITEMS__", json.dumps(items, ensure_ascii=False)) \
        .replace("__GROUPS__", json.dumps(groups, ensure_ascii=False)).replace("__N__", str(len(items)))


SHEET_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Música Episodio 2</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4;--rec:#a3201c}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--rec:#e0574f}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--rec:#e0574f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
h2{font-size:15px;margin:26px 0 4px}
.gtext{color:var(--mute);font-size:13px;margin:0 0 6px}
.prog{font-variant-numeric:tabular-nums;color:var(--mute)}
.prog b{color:var(--ink)}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.intro p{margin:6px 0}
.card{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:10px 0}
.card.rec{border-color:var(--rec)}
.row{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:10px 16px;padding:12px}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
.name code{font:600 14px ui-monospace,Consolas,monospace}
.ev{display:inline-block;background:var(--chip);border-radius:10px;padding:0 8px;margin-left:6px;font-size:12px;color:var(--mute)}
.badge{display:inline-block;background:var(--rec);color:#fff;border-radius:10px;padding:0 8px;margin-left:6px;font-size:11.5px;font-weight:650}
.meta{color:var(--mute);font-size:12.5px;margin:3px 0}
.meta b{color:var(--ink);font-weight:600}
audio{width:100%;height:34px;margin:6px 0}
.jumps{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0}
.jumps button{font-size:12px;padding:3px 8px}
.vote{display:flex;flex-direction:column;gap:6px}
.btns{display:flex;gap:6px}
.btns button{flex:1;font-weight:650;padding:6px 0}
.btns button.on.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btns button.on.no{background:var(--no);border-color:var(--no);color:#fff}
.btns button.on.q{background:var(--q);border-color:var(--q);color:#111}
textarea.note{width:100%;min-height:52px;resize:vertical;font:inherit;font-size:13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 7px}
.ref{padding:12px}
.ref .name::after{content:"referencia";margin-left:8px;font-size:11px;border:1px solid var(--line);border-radius:10px;padding:0 7px;color:var(--mute)}
#result{width:100%;min-height:150px;font:12.5px ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);padding:10px}
.copied{color:var(--ok);font-weight:600;margin-left:8px}
footer{color:var(--mute);font-size:12.5px;margin-top:24px}
@media (max-width:720px){.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Música del Episodio 2 · «The Road to Moscow»</h1>
  <span class="prog"><b id="pDone">0</b> / __N__ juzgadas</span>
  <button class="primary" id="copyTop">Copiar resultado</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
<div class="intro">
  <p><b>Qué es (D104).</b> Borradores <b>originales</b> para los tres mapas nuevos, compuestos como el <code>D_SDM1N2</code> de MAP01 (misma herramienta, misma orquesta General MIDI que suena en GZDoom: trompas, trombones, trompetas, tuba, bajo sintético, chelos, cuerdas, timbales, batería GM; más órgano, coro y campanas donde pegan). No citan ninguna canción soviética ni popular: no hay derechos de terceros.</p>
  <p><b>Dos versiones por mapa que suenan distintas de verdad</b>: cambian tonalidad, tempo, ritmo de fondo e instrumentos del tema (y en MAP04, toda la sección B). El motivo de 4 compases es el mismo en las dos, para que el mapa tenga una identidad elijas la que elijas. La marcada <span class="badge">recomendada</span> es la que yo instalaría.</p>
  <p class="meta">Renders con el propio sintetizador de GZDoom (zmusic + gzdoom.sf2), sin arrancar el juego. Cada audio <b>sigue 10 s después del punto de bucle</b> para oír la costura. Volumen igualado con <code>D_SDM1N2</code> (MAP01). Los botones saltan a cada sección. Nada instalado.</p>
</div>
<div id="items"></div>

<h2>Referencia: MAP01 instalada</h2>
<div class="card ref">
  <div class="name"><code>D_SDM1N2</code><span class="ev">1:30 · 128 BPM</span></div>
  <p class="meta">La que suena en MAP01 (D95). Para comparar estilo y volumen.</p>
  <audio controls preload="none" src="../map01_new/D_SDM01N2.ogg"></audio>
</div>

<h2>Resultado</h2>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copiar resultado</button><span class="copied" id="copiedBottom"></span> <button id="reset">Borrar respuestas</button></p>
<footer>Generador: <code>tools/audio/compose_episode2.py</code> · MIDIs: <code>work/audio/episode2/*.mid</code> · renders y niveles: <code>work/audio/episode2/render/</code> (<code>LEVELS.txt</code>). Nada instalado: si una vale, la instala el PM con tu OK.</footer>
</div>
<script>
const ITEMS = __ITEMS__;
const GROUPS = __GROUPS__;
const KEY = "sd-2026-10-21_episode2-music";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
const st = id => (S[id] = S[id] || {v:"", n:""});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = t => `${Math.floor(t/60)}:${String(Math.round(t%60)).padStart(2,"0")}`;
function card(it){
  return `<div class="card${it.rec ? " rec" : ""}"><div class="row" id="r-${it.id}" data-id="${it.id}">
    <div>
      <div class="name"><code>${it.id}</code><span class="ev">${it.len} · ${it.bpm} BPM · bucle + 10 s</span>${it.rec ? '<span class="badge">recomendada</span>' : ""}</div>
      <p class="meta">${esc(it.what)}</p>
      <audio controls preload="none" src="${esc(it.src)}"></audio>
      <div class="jumps">${it.jumps.map(([l, t]) => `<button data-t="${t}" title="${fmt(t)}">${esc(l)}</button>`).join("")}</div>
    </div>
    <div class="vote">
      <div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
      <textarea class="note" placeholder="Notas (qué sobra, qué falta, en qué segundo)">${esc(st(it.id).n)}</textarea>
    </div>
  </div></div>`;
}
function build(){
  let h = "";
  for (const [g, [title, text]] of Object.entries(GROUPS)) {
    const its = ITEMS.filter(i => i.group === g);
    if (!its.length) continue;
    h += `<h2>${esc(title)}</h2><p class="gtext">${esc(text)}</p>` + its.map(card).join("");
  }
  document.getElementById("items").innerHTML = h;
  ITEMS.forEach(i => paint(i.id));
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
}
function summary(){
  const label = {ok:"OK", no:"NO", q:"?"};
  const done = ITEMS.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  const L = [`Música Episodio 2 (D104, borradores originales): ${done}/${ITEMS.length} juzgadas`];
  for (const i of ITEMS) {
    const s = st(i.id), n = (s.n || "").trim().replace(/\s+/g, " ");
    L.push(`${i.id}${i.rec ? " (recomendada)" : ""}: ${label[s.v] || "sin juzgar"}${n ? ` — «${n}»` : ""}`);
  }
  document.getElementById("result").value = L.join("\n");
}
function copy(which){
  const t = document.getElementById("result"), msg = document.getElementById(which);
  summary();
  const ok = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(ok, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const j = e.target.closest(".jumps button");
  if (j) { const a = j.closest(".row").querySelector("audio"); a.currentTime = +j.dataset.t; a.play(); return; }
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.addEventListener("play", e => { document.querySelectorAll("audio").forEach(a => { if (a !== e.target) a.pause(); }); }, true);
document.getElementById("copyTop").addEventListener("click", () => copy("copiedTop"));
document.getElementById("copyBottom").addEventListener("click", () => copy("copiedBottom"));
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar las respuestas y notas de esta hoja?")) { S = {}; save(); build(); summary(); } });
build(); summary();
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", action="append")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--check", action="store_true", help="self-check only; writes nothing")
    ap.add_argument("--no-stems", action="store_true", help="skip the lead/bed balance renders")
    args = ap.parse_args(argv)
    songs = all_songs()
    problems = self_check(songs)
    for p in problems:
        print("CHECK:", p)
    if args.check:
        for key, v, s in songs:
            print(f"{v.lump}: {s.bars} bars, {v.bpm:g} BPM, loop {s.seconds():.1f} s, "
                  f"{len(s.notes)} notes, {len(s.hits)} hits")
        return 1 if problems else 0
    if problems:
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    chosen = [(k, v, s) for k, v, s in songs if not args.only or v.lump in args.only]
    if args.no_render:
        for key, v, s in chosen:
            (OUT_DIR / f"{v.lump}.mid").write_bytes(s.midi())
            if v.lump in BOSS_LUMP:
                (OUT_DIR / f"{BOSS_LUMP[v.lump]}.mid").write_bytes(s.midi(*BOSS_BARS))
            print(f"{v.lump}: loop {s.seconds():.1f} s")
        return 0
    meta_path = RENDER_DIR / "meta.json"
    rows = {r["lump"]: r for r in json.loads(meta_path.read_text(encoding="utf-8"))} if meta_path.is_file() else {}
    for key, v, s in chosen:
        row = calibrate_and_render(key, v, s, stems=not args.no_stems)
        rows[v.lump] = row
        print(f"{v.lump}: {row['seconds']:.1f} s, RMS {row['levels']['rms']:.1f}, scale {row['scale']}"
              + (f", lead-over-bed {row['lead_over_bed_db']:+.1f} dB" if "lead_over_bed_db" in row else ""))
    ordered = [rows[v.lump] for _, v, _ in songs if v.lump in rows]
    meta_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    (RENDER_DIR / "LEVELS.txt").write_text(levels_txt(ordered), encoding="utf-8")
    SHEET.write_text(sheet_html(ordered), encoding="utf-8")
    print(f"sheet -> {SHEET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
