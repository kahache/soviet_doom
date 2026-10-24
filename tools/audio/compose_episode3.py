#!/usr/bin/env python3
"""Episode 3, «The Portal» (D112) -- original draft music, two variants per piece.

    .venv/Scripts/python.exe tools/audio/compose_episode3.py              # MIDIs + renders + sheet
    .venv/Scripts/python.exe tools/audio/compose_episode3.py --no-render  # MIDIs + self-check only
    .venv/Scripts/python.exe tools/audio/compose_episode3.py --only D_SDM07A --only D_SDM07B
    .venv/Scripts/python.exe tools/audio/compose_episode3.py --check      # self-check, writes nothing

What this is
------------
The method of Episode 2 (tools/audio/compose_episode2.py, approved 10/10, D106),
whose Song machinery this file reuses unchanged: a 4-bar motif per map, its
answer, a contrasting B section, a quiet C, a build and a tutti, the same
General MIDI band rendered with GZDoom's own zmusic.dll + gzdoom.sf2 as a
library (no engine, D26), loudness matched to MAP01's D_SDM1N2.

ORIGINAL COMPOSITION (sound-designer, 2026-10-22). Nothing is quoted: no Soviet
song, no folk tune, no classical theme, no phrase of Episodes 1-2. The
self-check enforces the last part twice: (1) no two-bar shape (intervals +
rhythm) equal to one of MAP01's or Episode 2's written themes, and (2) no
seven-note interval run (rhythm ignored, transposition ignored) found in the
top or bottom voice of any MIDI installed in assets/music/ -- that covers
Episode 1's public-domain pieces (Internationale, «Вы жертвою пали»,
«Богатырские ворота», «Zarya») as well as our own. An early MAP08 sketch whose
head (A-D-F-E-D) leant on «Священная война» was rewritten before rendering.
So there is no rights question beyond our own (CC BY-NC-SA 4.0, D15).

Pieces (lumps are 8 characters; nothing is installed -- the CEO listens first):
  MAP07 Novaya Zemlya   D_SDM07A / D_SDM07B   radar pings, celesta / vibraphone, horns, 116 / 122 BPM
  MAP08 Severomorsk     D_SDM08A / D_SDM08B   low brass, shipyard metal, sonar, 124 / 120 BPM
  MAP09 Tunguska        D_SDM09A / D_SDM09B   brass choir + organ, arena B section, 132 / 138 BPM
  Final boss            D_SDBS9A / D_SDBS9B   its own loop for the portal arena, 140 / 146 BPM
  Episode 3 intermission D_SDE3IA / D_SDE3IB  the three motifs in one 16-bar loop, 96 / 108 BPM

Output: work/audio/episode3/*.mid; renders (loop + 10 s past the seam) in
work/audio/episode3/render/ with LEVELS.txt; the listening sheet
work/audio/preview/episode3_music_listening.html.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_episode2 as e2  # noqa: E402
import gen_music as gm  # noqa: E402
from compose_episode2 import (  # noqa: E402
    BEATS_PER_BAR, BRASS, CC_EXPRESSION, CELLO, CHOIR, CLOSED_HH, CONTRABASS, CRASH, CRASH2, HORNS,
    KICK, LEGATO, LOW_FLOOR_TOM, LOW_TOM, MARCATO, MID_TOM, MUTED_TRUMPET, PAD_HALO, PIZZ, RIDE,
    RIDE_BELL, SIDESTICK, SLOW_STRINGS, SNARE, STRINGS, SYNTH_BASS_1, SYNTH_BASS_2, TAIKO, TIMPANI,
    TREMOLO, TROMBONE, TRUMPET, TUBA, TUBULAR_BELLS, Part, Variant, in_range, mel)
from gen_music import pitch  # noqa: E402

PROJECT_ROOT = gm.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "audio" / "episode3"
RENDER_DIR = OUT_DIR / "render"
SHEET = PROJECT_ROOT / "work" / "audio" / "preview" / "episode3_music_listening.html"
INSTALLED_MUSIC = PROJECT_ROOT / "assets" / "music"
DRAFT_TAG = "D112 draft, original"

# -- General MIDI programs (0-based) new to this episode, all in gzdoom.sf2 bank 0 -----------
CELESTA, GLOCKENSPIEL, VIBRAPHONE, CHURCH_ORGAN = 8, 9, 11, 19
VOICE_OOHS, ORCH_HIT, CRYSTAL = 53, 55, 98
# -- GM drum notes new to this episode -------------------------------------------------------
CHINA, COWBELL, HIGH_AGOGO, LOW_AGOGO = 52, 56, 67, 68
MUTE_TRIANGLE, OPEN_TRIANGLE = 80, 81

# Playable ranges for the new programs (Episode 2's table folds bars by program; these
# programs are not used by Episode 2 through line()/harmonize(), so its output is unchanged).
for _prog, _rng in {CELESTA: (60, 108), GLOCKENSPIEL: (72, 108), VIBRAPHONE: (53, 89),
                    CHURCH_ORGAN: (36, 96), VOICE_OOHS: (48, 79)}.items():
    e2.RANGE.setdefault(_prog, _rng)

# Loop length windows (seconds) for the self-check.
LOOP_WINDOW = {"map": (110, 190), "boss": (40, 90), "int": (30, 60)}
# A run of this many intervals (8 notes) is a "phrase" for the quotation scan.
QUOTE_NGRAM = 7


class Song(e2.Song):
    """Episode 2's Song, with this episode's draft tag in the first track name."""

    def tracks(self, bar_from: int = 0, bar_to: int | None = None, mute=()):
        tracks, end = super().tracks(bar_from, bar_to, mute)
        events = tracks[0].events
        for i, (tick, order, seq, payload) in enumerate(events):
            if payload[:2] == bytes([gm.META_PREFIX, gm.META_TRACK_NAME]):
                text = f"Soviet Doom - {self.lump} ({self.title}, {DRAFT_TAG})".encode("ascii", "replace")
                events[i] = (tick, order, seq, payload[:2] + gm.varlen(len(text)) + text)
                break
        return tracks, end

    def finish(self) -> "Song":
        """Clip echo tails at the loop point (the writer clips them anyway; this keeps the check honest)."""
        end = self.bars * BEATS_PER_BAR
        self.notes = [(pt, p, st, min(ln, end - st), v) for pt, p, st, ln, v in self.notes if st < end]
        self.hits = [h for h in self.hits if h[1] < end]
        return self


def ping(s: Song, part: str, p: int, start: float, vel: float, echoes: int = 3, gap: float = 0.75,
         length: float = 1.0, decay: float = 0.55) -> None:
    """A radar / sonar ping: one strike and its fading echoes."""
    for k in range(echoes + 1):
        s.n(part, p, start + gap * k, length, vel * decay ** k)


def bass_roots(s: Song, part: str, b: int, low: str, vel: float, art: float = 0.98) -> None:
    for start, beats, name in s.harmony[b]:
        bpc, _ = s.chord(name)
        s.n(part, in_range(bpc, pitch(low)), b * BEATS_PER_BAR + start, beats * art, vel)


# =============================================================================================
# MAP07 -- Novaya Zemlya (written in B minor)
# =============================================================================================
# The motif: a lonely horn call that leaps a minor sixth (B up to G) and sinks back to the
# fifth, then a second leap of a sixth that lands on the Neapolitan C -- the radar beam
# sweeping the polar night. Answered by a dim descent (E-C#-A#) back to the tonic.

M7_THEME_H = "Bm | Em,F# | Bm,C | F#7 | G | Em | Em,F#7 | Bm"
M7_THEME = mel("""
B3:4 G4:8 F#4:4 | E4:3 F#4:1 D4:4 C#4:8 | B3:4 G4:4 E4:4 C5:4 | B4:12 A#4:4 |
D4:4 B4:8 A4:4 | G4:3 A4:1 F#4:4 E4:8 | G4:4 E5:4 C#5:4 A#4:4 | B4:12 r:4""")
M7_INTRO_HORN = mel("B3:4 G4:8 F#4:4 | F#4:8 B3:4 A#3:4")
M7_COUNTER = mel("""D3:8 F#3:8 | E3:8 C#3:8 | D3:8 E3:8 | E3:8 A#2:8 |
B2:8 D3:8 | E3:8 G3:8 | B3:8 C#4:8 | D4:4 C#4:4 B3:8""")
# Variant A's B section: «the aurora» -- D major, a wide string tune over celesta shimmer.
M7_AURORA_H = "D | A/C# | Bm | G | D/F# | Em | A | A7 | G | D/F# | Em | Bm | G | A | F# | F#7"
M7_AURORA = mel("""
F#4:8 A4:4 D5:4 | E5:8 C#5:4 A4:4 | B4:6 C#5:2 D5:4 F#5:4 | D5:8 B4:4 G4:4 |
A4:8 D5:4 F#5:4 | G5:6 F#5:2 E5:8 | C#5:6 B4:2 A4:4 E5:4 | E5:8 G5:8 |
B5:8 G5:4 D5:4 | A5:8 F#5:4 D5:4 | G5:6 E5:2 B4:4 G5:4 | F#5:12 D5:4 |
E5:6 D5:2 B4:4 G4:4 | A4:6 B4:2 C#5:4 E5:4 | F#5:6 E5:2 C#5:4 A#4:4 | F#4:8 A#4:4 C#5:4""")
# Variant B's B section: «the blizzard» -- the motif in diminution, trombone call, horn answer.
M7_STORM = mel("""B3:2 G4:4 F#4:2 E4:2 D4:2 C#4:4 | B3:2 G4:4 F#4:2 E4:2 C5:4 G4:2 |
F#4:4 A#4:4 C#5:4 E5:4 | D5:8 C#5:8""")
M7_STORM_ALT = mel("G4:4 B4:4 D5:4 F#5:4 | E5:8 C#5:4 A#4:4")
M7_STORM_H = " | ".join(["G,F#7 | Em,C | F#7 | F#7", "G,F#7 | Em,C | G | F#7"] * 2)
# C: «the radar» -- the motif augmented in the trombones, nothing but the pings above.
M7_RADAR_H = "Bm | Bm | Em | F# | Bm | C | F#sus4 | F#7"
M7_DEEP = mel("B2:8 G3:8 | F#3:16 | E3:6 F#3:2 D3:8 | C#3:16 | B2:8 G3:8 | E3:8 C4:8 | B3:16 | A#3:16")
M7_BUILD_H = "G | Am | F#7 | F#7"
M7_BUILD = mel("B3:4 G4:8 F#4:4 | C4:4 A4:8 G4:4 | C#4:4 A#4:8 G4:4 | F#4:4 A#4:4 C#5:4 E5:4")
M7_CODA_H = "Bm | C | F#7 | F#7"
M7_CODA = mel("B3:4 G4:8 F#4:4 | E4:4 C5:8 B4:4 | A#4:16 | r:16")

M7_VARIANTS = (
    Variant("D_SDM07A", "A", 116.0, 0, "B minor, 116 BPM: radar pings on celesta with echo, triangle "
            "in eighths, low tremolo and double basses, the theme on horns; B section «the aurora borealis» "
            "in D major (slow strings + celesta)"),
    Variant("D_SDM07B", "B", 122.0, 2, "C-sharp minor, 122 BPM, half-time: radar on vibraphone "
            "and glockenspiel, 3-3-2 pizzicato, theme on horns + «oohs» choir; B section «the blizzard» "
            "(the motif in diminution, trombones against horns, strings in sixteenths, taiko)"),
)


def m7_radar(s: Song, b: int, fl: str, level: int) -> None:
    """The station's pulse: the ping (and its echo) plus a ticking triangle."""
    t = s.transpose
    if fl == "A":
        if b % 2 == 0:
            ping(s, "cel", pitch("F#6") + t, b * 4, 86, echoes=3, gap=0.75, length=1.2)
        if level >= 1:
            s.drums(b, {MUTE_TRIANGLE: "X.x.x.x.x.x.x.x."}, 40 + 4 * min(level, 2))
    else:
        ping(s, "vib", pitch("F#5") + t, b * 4, 82 if b % 2 == 0 else 64, echoes=2, gap=1.0, length=1.5)
        if b % 4 == 0:
            ping(s, "glock", pitch("B6") + t, b * 4 + 0.5, 70, echoes=2, gap=1.0, length=1.0)
        if level >= 1:
            s.drums(b, {MUTE_TRIANGLE: "X..x..x.X..x..x."}, 40 + 4 * min(level, 2))


def m7_ice(s: Song, b: int, level: int, fl: str) -> None:
    """Low strings (the ice), the pulse, the arpeggio."""
    lv = min(level, 3)
    bass_roots(s, "bass", b, "B1", 58 + 5 * lv)
    s.chords("trem", b, "B2", 40 + 5 * lv)
    if level >= 1:
        if fl == "A":
            s.pattern("low", b, "R.r.r.r.R.r.r.r.", "D2", 52 + 4 * lv, art=0.4, accent=10)
        else:
            s.pattern("pizz", b, "R..f..o.R..f..o.", "B2", 58 + 4 * lv, art=0.5)
    if level >= 2:
        if fl == "A":
            s.pattern("cel", b, "r.t.f.o.t.f.o.f.", "B4", 40, art=0.9, accent=6)
        else:
            s.pattern("vib", b, "r..t..f.o..f..t.", "B4", 44, art=0.9, accent=6)


def m7_drums(s: Song, b: int, level: int, fl: str) -> None:
    pats = {}
    if fl == "A":
        if level >= 1:
            pats[KICK] = "X.....x...x....."
            pats[SIDESTICK] = "............x..."
        if level >= 2:
            pats[KICK] = "X.....x.X.....x."
            pats[SNARE] = "....x.......X..."
            pats.pop(SIDESTICK)
        if level >= 3:
            pats[KICK] = "X.....x.X..x..x."
            pats[SNARE] = "....X.......X.gx"
            pats[RIDE] = "x.x.x.x.x.x.x.x."
    else:
        if level >= 1:
            pats[KICK] = "X.........X....."
            s.n("taiko", pitch("C3"), b * 4, 0.5, 92)
        if level >= 2:
            pats[SNARE] = "........X......."
            pats[LOW_FLOOR_TOM] = "..g...g...g...g."
        if level >= 3:
            pats[KICK] = "X.....x...X....."
            pats[SNARE] = "........X.....gg"
            pats[CLOSED_HH] = "xgxgxgxgxgxgxgxg"
            s.n("taiko", pitch("C3"), b * 4 + 2.5, 0.5, 78)
    if pats:
        s.drums(b, pats, 86)
    if level >= 2:
        s.timp(b, "R.......F......." if level == 2 else "R.....r.F.......", 74)


def build_map07(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "bass": Part(CONTRABASS if A else SYNTH_BASS_1, 84, 64),
        "low": Part(CELLO, 72, 34),
        "trem": Part(TREMOLO, 66, 92, 90),
        "strings": Part(SLOW_STRINGS if A else STRINGS, 84, 76, 90),
        "horns": Part(HORNS, 122, 44, 84),
        "tbn": Part(TROMBONE, 98, 88),
        "tuba": Part(TUBA, 84, 60),
        "timp": Part(TIMPANI, 88, 70),
        "pad": Part(PAD_HALO, 60, 64, 100),
    }
    if A:
        parts["cel"] = Part(CELESTA, 100, 96, 110)
        parts["tpt"] = Part(MUTED_TRUMPET, 104, 54)
    else:
        parts["pizz"] = Part(PIZZ, 82, 30)
        parts["vib"] = Part(VIBRAPHONE, 96, 96, 110)
        parts["glock"] = Part(GLOCKENSPIEL, 72, 104, 110)
        parts["oohs"] = Part(VOICE_OOHS, 88, 64, 96)
        parts["taiko"] = Part(TAIKO, 84, 64, 50)
    s = Song(v.lump, "MAP07 Novaya Zemlya", v.bpm, v.transpose, (11 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "tbn", "oohs"), drum_volume=80)
    fl = v.flavour
    t = v.transpose
    fs = (6 + t) % 12                                         # the dominant's pitch class

    # -- Intro: the polar night, the radar alone, then the call -------------------------------
    i0 = s.section("Intro · the polar night", "Bm | Bm | Bm | F#sus4,F#7")
    for b in range(i0, i0 + 4):
        m7_radar(s, b, fl, 0 if b < i0 + 2 else 1)
        m7_ice(s, b, 0 if b < i0 + 2 else 1, fl)
        s.chords("pad", b, "F#3", 36)
    s.ramp("trem", 0, 8, 30, 127)
    s.line("horns", M7_INTRO_HORN, i0 + 2, 84, LEGATO, accent=3)
    s.roll("timp", (i0 + 3) * 4 + 2.0, 2.0, 30, 80, 0.25, p=in_range(fs, pitch("E2")))

    # -- A: the theme ---------------------------------------------------------------------------
    a1 = s.section("A · the theme", M7_THEME_H)
    s.line("horns", M7_THEME, a1, 98, LEGATO, accent=5)
    if not A:
        s.line("oohs", M7_THEME, a1, 70, LEGATO)
    for b in range(a1, a1 + 8):
        m7_radar(s, b, fl, 1)
        m7_ice(s, b, 1, fl)
        m7_drums(s, b, 1, fl)
        s.chords("pad", b, "F#3", 40)
    s.hit(CRASH, a1 * 4, 76)

    # -- A': the counter-line ------------------------------------------------------------------
    a2 = s.section("A' · countermelody", M7_THEME_H)
    s.line("horns", M7_THEME, a2, 100, LEGATO, accent=5)
    s.line("tbn", M7_COUNTER, a2, 86, LEGATO)
    if not A:
        s.harmonize("oohs", M7_THEME, a2, 62, LEGATO)
    for b in range(a2, a2 + 8):
        m7_radar(s, b, fl, 2)
        m7_ice(s, b, 2, fl)
        m7_drums(s, b, 2, fl)
        s.chords("strings", b, "B3", 50)
    s.hit(CRASH, a2 * 4, 90)

    # -- B ----------------------------------------------------------------------------------------
    if A:
        b0 = s.section("B · the aurora borealis", M7_AURORA_H)
        s.line("strings", M7_AURORA, b0, 94, LEGATO, accent=3)
        s.line("horns", M7_AURORA[8:], b0 + 8, 80, LEGATO, octave=-1)
        for b in range(b0, b0 + 16):
            second = b >= b0 + 8
            s.pattern("cel", b, "rtforfotrtforfot", "D5", 36 + 4 * second, art=0.9, accent=6)
            s.chords("pad", b, "F#3", 46)
            s.chords("trem", b, "D3", 40 if not second else 50)
            bass_roots(s, "bass", b, "B1", 60)
            if (b - b0) % 4 == 0:
                ping(s, "cel", pitch("F#6") + t, b * 4, 70, echoes=3, gap=0.75, length=1.2)
            m7_drums(s, b, 1 if second else 0, fl)
            if second:
                s.drums(b, {MUTE_TRIANGLE: "X.x.x.x.x.x.x.x."}, 40)
        s.hit(CRASH, (b0 + 8) * 4, 84)
    else:
        b0 = s.section("B · the blizzard", M7_STORM_H)
        for rep in range(4):
            b1 = b0 + 4 * rep
            bars = M7_STORM if rep % 2 == 0 else M7_STORM[:2] + M7_STORM_ALT
            s.line("tbn", bars[:2], b1, 98, MARCATO)
            s.line("horns", bars[2:], b1 + 2, 98, MARCATO)
            if rep >= 2:
                s.line("horns", bars[:2], b1, 82, MARCATO)
                s.line("oohs", bars[2:], b1 + 2, 78, LEGATO)
            for b in range(b1, b1 + 4):
                s.pattern("strings", b, "RfrfRfrfRfrfRfrf", "B3", 56 + 4 * rep, art=0.7, accent=10)
                m7_ice(s, b, 1, fl)
                m7_radar(s, b, fl, 1)
                m7_drums(s, b, 2 if rep < 2 else 3, fl)
            s.roll("timp", (b1 + 3) * 4 + 2.0, 2.0, 44, 90, 0.25, p=in_range(fs, pitch("E2")))
            s.hit(CRASH, b1 * 4, 84 + 6 * rep)

    # -- C: the radar ----------------------------------------------------------------------------
    c0 = s.section("C · the radar", M7_RADAR_H)
    s.line("tbn", M7_DEEP, c0, 90, LEGATO)
    s.line("tuba", M7_DEEP, c0, 70, LEGATO, octave=-1)
    if not A:
        s.line("oohs", M7_DEEP, c0, 62, LEGATO, octave=1)
    for b in range(c0, c0 + 8):
        m7_radar(s, b, fl, 0)
        bass_roots(s, "bass", b, "B1", 62)
        s.chords("trem", b, "B2", 46)
        s.chords("strings", b, "F#5", 34)
        s.drums(b, {KICK: "X..x............"}, 64)          # a heartbeat under the ice
    s.roll("timp", (c0 + 7) * 4, 4.0, 36, 96, 0.25, p=in_range(fs, pitch("E2")))

    # -- Build -----------------------------------------------------------------------------------
    k0 = s.section("Build", M7_BUILD_H)
    s.line("horns", M7_BUILD, k0, 92, MARCATO, swell=4)
    s.line("tbn", M7_BUILD, k0, 84, MARCATO, octave=-1, swell=4)
    if A:
        s.line("tpt", M7_BUILD[2:], k0 + 2, 88, MARCATO)
    else:
        s.line("oohs", M7_BUILD, k0, 70, LEGATO, swell=4)
    for b in range(k0, k0 + 4):
        m7_ice(s, b, 2, fl)
        m7_radar(s, b, fl, 2)
        m7_drums(s, b, 2, fl)
        s.pattern("strings", b, "rtforfotrtforfot", "B3", 56 + 5 * (b - k0), art=0.6)
    s.roll(SNARE, (k0 + 2) * 4, 8.0, 36, 108)
    s.roll("timp", (k0 + 3) * 4, 4.0, 56, 110, 0.25, p=in_range(fs, pitch("E2")))

    # -- A'': tutti ------------------------------------------------------------------------------
    a3 = s.section("A'' · tutti", M7_THEME_H + " | " + M7_THEME_H)
    for rep in range(2):
        b1 = a3 + 8 * rep
        s.line("horns", M7_THEME, b1, 102, MARCATO, accent=6)
        s.harmonize("tbn", M7_THEME, b1, 80, MARCATO, octave=-1)
        if rep == 1:
            s.line("strings", M7_COUNTER, b1, 78, LEGATO, octave=2)
            if A:
                s.line("tpt", M7_THEME, b1, 90, MARCATO)
            else:
                s.line("oohs", M7_THEME, b1, 80, LEGATO)
        elif not A:
            s.harmonize("oohs", M7_THEME, b1, 64, LEGATO)
        for b in range(b1, b1 + 8):
            m7_ice(s, b, 3, fl)
            m7_radar(s, b, fl, 2)
            m7_drums(s, b, 3, fl)
            s.chords("pad", b, "F#3", 46)
            s.pattern("tuba", b, "R.......F.......", "C2", 78, art=0.85)
            if rep == 0:
                s.chords("strings", b, "B3", 56)
        s.hit(CRASH, b1 * 4, 100)

    # -- Coda: the call fades back into the night --------------------------------------------------
    d0 = s.section("Return", M7_CODA_H)
    s.line("horns", M7_CODA, d0, 96, LEGATO)
    s.line("tbn", M7_CODA, d0, 78, LEGATO, octave=-1)
    for b in range(d0, d0 + 4):
        m7_radar(s, b, fl, 1 if b < d0 + 3 else 0)
        m7_ice(s, b, 2 if b < d0 + 2 else 0, fl)
        m7_drums(s, b, 2 if b < d0 + 2 else 0, fl)
    s.ramp("trem", (d0 + 2) * 4, 8.0, 127, 40)
    s.roll("timp", (d0 + 3) * 4, 4.0, 28, 64, 0.25, p=in_range(fs, pitch("E2")))
    return s.finish()


# =============================================================================================
# MAP08 -- Severomorsk (written in D minor)
# =============================================================================================
# The motif: a heavy hull-call in the trombones -- up a fourth, down two steps -- stated three
# times, each a step lower (D, C, B-flat) as if the boat were diving, then the dominant.
# The answer climbs the same cell back up (F-B-flat) and closes on the tonic.

M8_THEME_H = "Gm,Dm | F,A | Eb,Bb | A7 | Gm,Dm | Bb,F | Gm,A7 | Dm"
M8_THEME = mel("""
D3:4 G3:4 F3:3 E3:1 D3:4 | C3:4 F3:4 E3:3 D3:1 C#3:4 | Bb2:4 Eb3:4 D3:3 C3:1 Bb2:4 | A2:4 E3:4 G3:2 F3:2 E3:4 |
D3:4 G3:4 F3:3 E3:1 D3:4 | F3:4 Bb3:4 A3:3 G3:1 F3:4 | G3:4 Bb3:4 A3:3 G3:1 E3:2 C#3:2 | D3:12 r:4""")
M8_COUNTER = mel("""Bb4:8 A4:8 | A4:8 C#5:8 | G4:8 F4:8 | E4:8 C#5:8 |
Bb4:8 A4:8 | D5:8 C5:8 | Bb4:8 A4:8 | A4:16""")
# B: «the docks» -- the fleet's march in B-flat major (trumpets in A, horns + choir in B).
M8_DOCK_H = "Bb | F/A | Gm | D | Eb | Bb/D | Cm | F | Bb | F/A | Gm | Eb | Cm | D | Gm | A7"
M8_DOCK = mel("""
D5:6 C5:2 Bb4:4 F4:4 | A4:4 C5:4 F5:8 | G5:6 F5:2 D5:4 Bb4:4 | A4:8 F#4:8 |
G4:6 Bb4:2 Eb5:8 | D5:6 C5:2 Bb4:4 D5:4 | C5:4 Eb5:4 G5:6 F5:2 | F5:8 C5:8 |
D5:6 C5:2 Bb4:4 F4:4 | A4:4 C5:4 F5:8 | G5:4 D5:4 Bb4:4 G4:4 | Eb5:6 D5:2 C5:4 Bb4:4 |
C5:6 D5:2 Eb5:4 G5:4 | F#5:8 D5:4 A4:4 | G4:6 A4:2 Bb4:4 D5:4 | C#5:8 E5:4 A4:4""")
# C: «the dive» -- a slow chorale under the sonar.
M8_DEEP_H = "Dm | Dm | Eb | Eb | Dm | Dm | A7 | A7"
M8_DEEP = mel("D4:8 F4:8 | E4:8 D4:8 | Eb4:8 G4:8 | Bb4:16 | A4:8 F4:8 | D4:16 | C#4:8 E4:8 | A4:16")
M8_BUILD_H = "Eb,Bb | F | A7 | A7"
M8_BUILD = mel("Bb3:4 Eb4:4 D4:3 C4:1 Bb3:4 | C4:4 F4:4 Eb4:3 D4:1 C4:4 | C#4:4 E4:4 G4:4 A4:4 | A4:4 A4:4 A4:4 A4:4")
M8_CODA_H = "Gm,Dm | Eb,Bb | A7 | A7"
M8_CODA = mel("D4:4 G4:4 F4:3 E4:1 D4:4 | Bb3:4 Eb4:4 D4:3 C4:1 Bb3:4 | A3:4 E4:4 G4:2 F4:2 E4:4 | A3:4 r:4 A3:4 r:4")

M8_VARIANTS = (
    Variant("D_SDM08A", "A", 124.0, 0, "D minor, 124 BPM: the theme on trombones + tuba, a shipyard of "
            "ride bell and agogo, marching snare, echoing sonar, ship's bell; B section "
            "«the dock» with trumpets"),
    Variant("D_SDM08B", "B", 120.0, -2, "C minor, 120 BPM, half-time and heavier: taiko, block "
            "brass, men's choir doubling the theme; «the dock» on horns + choir, legato"),
)


def m8_sonar(s: Song, b: int, every: int = 2, vel: float = 80) -> None:
    if b % every == 0:
        ping(s, "sonar", pitch("A5") + s.transpose, b * 4, vel, echoes=3, gap=1.5, length=1.4, decay=0.5)


def ship_bell(s: Song, b: int, vel: float = 78) -> None:
    """Two strikes: a ship's bell rings in pairs."""
    p = pitch("A4") + s.transpose
    s.n("bells", p, b * 4, 1.5, vel)
    s.n("bells", p, b * 4 + 0.75, 1.5, vel - 8)


def m8_yard(s: Song, b: int, fl: str, level: int) -> None:
    """Shipyard metal + the march."""
    pats = {}
    if fl == "A":
        if level >= 1:
            pats[RIDE_BELL] = "X..x..x.X..x..x."
            pats[LOW_AGOGO] = "....x.......x.x."
        if level >= 2:
            pats[KICK] = "X.......X......."
            pats[SNARE] = "....X.......X.R."
        if level >= 3:
            pats[KICK] = "X.X.....X.X....."
            pats[SNARE] = "....X..g....X.RR"
    else:
        if level >= 1:
            pats[RIDE_BELL] = "x...x...x...x..."
            pats[LOW_AGOGO] = "........X......."
        if level >= 2:
            pats[KICK] = "X.........X....."
            pats[SNARE] = "........X......."
            s.n("taiko", pitch("C3"), b * 4, 0.5, 100)
            s.n("taiko", pitch("C3"), b * 4 + 2.5, 0.5, 80)
        if level >= 3:
            pats[KICK] = "X.....X...X....."
            pats[SNARE] = "........X.....xx"
            pats[CLOSED_HH] = "x.x.x.x.x.x.x.x."
    if pats:
        s.drums(b, pats, 88)


def m8_engine(s: Song, b: int, fl: str, level: int) -> None:
    """The boat's engines: bass, cellos, timpani."""
    if fl == "A":
        if level >= 1:
            s.pattern("bass", b, "R..rR.r.R..rR.r.", "E1", 82, art=0.75)
        if level >= 2:
            s.pattern("low", b, "R..rR..rR..rR.rr", "C2", 62, art=0.55, accent=12)
    else:
        if level >= 1:
            s.pattern("bass", b, "R-------R...r.r.", "E1", 82, art=0.9)
        if level >= 2:
            s.pattern("low", b, "R.......r...r...", "C2", 66, art=0.7, accent=12)
    if level >= 2:
        s.timp(b, "R.......F......." if level == 2 else "R...R...F...F.R.", 78)


def build_map08(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "bass": Part(SYNTH_BASS_2 if A else CONTRABASS, 90, 64),
        "low": Part(CELLO, 80, 30),
        "trem": Part(TREMOLO, 66, 92),
        "strings": Part(STRINGS, 84, 76),
        "tbn": Part(TROMBONE, 110, 88),
        "tuba": Part(TUBA, 94, 60),
        "horns": Part(HORNS, 118, 44),
        "timp": Part(TIMPANI, 94, 70),
        "sonar": Part(CRYSTAL, 86, 100, 110),
        "bells": Part(TUBULAR_BELLS, 84, 84),
        "choir": Part(CHOIR, 80, 64),
    }
    if A:
        parts["tpt"] = Part(TRUMPET, 104, 54)
    else:
        parts["brass"] = Part(BRASS, 100, 72)
        parts["taiko"] = Part(TAIKO, 80, 64, 50)
    s = Song(v.lump, "MAP08 Severomorsk", v.bpm, v.transpose, (2 + v.transpose) % 12, parts,
             lead_parts=("tbn", "horns", "tpt", "brass") if A else ("tbn", "horns", "brass", "choir"),
             drum_volume=88)
    fl = v.flavour
    a_pc = (9 + v.transpose) % 12

    # -- Intro: the fjord, the sonar, the engines start ------------------------------------------
    i0 = s.section("Intro · the fjord", "Dm | Dm | Gm,Dm | A7")
    for b in range(i0, i0 + 4):
        m8_sonar(s, b, every=2, vel=84)
        bass_roots(s, "low", b, "D2", 52)
        s.chords("trem", b, "A2", 44 + 4 * (b - i0))
        if b >= i0 + 2:
            m8_yard(s, b, fl, 1)
            m8_engine(s, b, fl, 1)
    ship_bell(s, i0)
    s.line("tbn", [M8_THEME[0], M8_THEME[3]], i0 + 2, 92, MARCATO)
    s.line("tuba", [M8_THEME[0], M8_THEME[3]], i0 + 2, 76, MARCATO, octave=-1)
    s.roll("timp", (i0 + 3) * 4 + 2.0, 2.0, 50, 100, 0.25, p=in_range(a_pc, pitch("E2")))

    # -- A: the hull-call in the trombones -----------------------------------------------------
    a1 = s.section("A · the theme", M8_THEME_H)
    s.line("tbn", M8_THEME, a1, 100, MARCATO, accent=8)
    s.line("tuba", M8_THEME, a1, 82, MARCATO, octave=-1)
    if not A:
        s.line("choir", M8_THEME, a1, 70, LEGATO, octave=1)
    for b in range(a1, a1 + 8):
        m8_yard(s, b, fl, 2)
        m8_engine(s, b, fl, 2)
        s.chords("trem", b, "A2", 50)
        if (b - a1) % 4 == 3:
            s.chords("horns", b, "D4", 86, hits=(0.0, 2.0, 2.5), length=0.5)
        if (b - a1) % 4 == 0:
            m8_sonar(s, b, every=4, vel=66)
    ship_bell(s, a1)
    s.hit(CRASH, a1 * 4, 100)

    # -- A': horns on top, the strings' counter-line ---------------------------------------------
    a2 = s.section("A' · the brass", M8_THEME_H)
    s.line("horns", M8_THEME, a2, 100, MARCATO, octave=1, accent=6)
    s.line("tbn", M8_THEME, a2, 92, MARCATO)
    s.line("strings", M8_COUNTER, a2, 76, LEGATO)
    if A:
        for b in (a2 + 3, a2 + 7):
            s.chords("tpt", b, "A4", 86, hits=(0.0, 0.75, 1.0, 2.0), length=0.4)
    else:
        s.harmonize("brass", M8_THEME, a2, 74, MARCATO, octave=1)
    for b in range(a2, a2 + 8):
        m8_yard(s, b, fl, 3)
        m8_engine(s, b, fl, 3)
    s.hit(CRASH, a2 * 4, 104)
    s.hit(CHINA, (a2 + 4) * 4, 80)

    # -- B: the docks ---------------------------------------------------------------------------
    b0 = s.section("B · the dock", M8_DOCK_H)
    if A:
        s.line("tpt", M8_DOCK, b0, 98, MARCATO)
        s.harmonize("horns", M8_DOCK[8:], b0 + 8, 76, MARCATO)
    else:
        s.line("horns", M8_DOCK, b0, 98, LEGATO, accent=4)
        s.line("choir", M8_DOCK, b0, 78, LEGATO)
        s.harmonize("strings", M8_DOCK, b0, 62, LEGATO, voices=2)
    for b in range(b0, b0 + 16):
        second = b >= b0 + 8
        s.pattern("tuba", b, "R.......F.......", "C2", 82, art=0.85)
        s.chords("trem", b, "F3", 46 + 6 * second)
        if not A and second:
            s.chords("brass", b, "F3", 70, hits=(0.0, 2.0), length=1.5)
        if A and not second:
            s.chords("strings", b, "D4", 52)
        m8_yard(s, b, fl, 3 if second else 2)
        m8_engine(s, b, fl, 2)
    ship_bell(s, b0)
    s.hit(CRASH, b0 * 4, 96)
    s.hit(CRASH, (b0 + 8) * 4, 100)

    # -- C: the dive ----------------------------------------------------------------------------
    c0 = s.section("C · dive", M8_DEEP_H)
    if A:
        s.line("horns", M8_DEEP, c0, 86, LEGATO)
        s.harmonize("tbn", M8_DEEP, c0, 66, LEGATO, voices=2)
    else:
        s.line("choir", M8_DEEP, c0, 88, LEGATO)
        s.harmonize("horns", M8_DEEP, c0, 62, LEGATO, voices=2)
    for b in range(c0, c0 + 8):
        m8_sonar(s, b, every=2, vel=88)
        bass_roots(s, "bass", b, "E1", 70)
        s.chords("trem", b, "A2", 48)
        if A:
            s.drums(b, {KICK: "X..x............", RIDE_BELL: "........x......."}, 66)
        else:
            s.n("taiko", pitch("C3"), b * 4, 0.5, 70)
            s.drums(b, {RIDE_BELL: "........x......."}, 60)
    s.roll("timp", (c0 + 7) * 4, 4.0, 40, 104, 0.25, p=in_range(a_pc, pitch("E2")))

    # -- Build -----------------------------------------------------------------------------------
    k0 = s.section("Build", M8_BUILD_H)
    s.line("horns", M8_BUILD, k0, 94, MARCATO, swell=4)
    s.line("tbn", M8_BUILD, k0, 90, MARCATO, octave=-1, swell=4)
    for b in range(k0, k0 + 4):
        m8_engine(s, b, fl, 2)
        m8_yard(s, b, fl, 1 if b < k0 + 2 else 2)
        s.pattern("strings", b, "rtforfotrtforfot", "A3", 56 + 5 * (b - k0), art=0.6)
        s.chords("tpt" if A else "brass", b, "A4" if A else "F4", 80 + 4 * (b - k0), hits=(0.0, 1.0, 2.0, 3.0),
                 length=0.4)
    s.roll(SNARE, (k0 + 2) * 4, 8.0, 40, 112)
    s.roll("timp", (k0 + 3) * 4, 4.0, 60, 112, 0.25, p=in_range(a_pc, pitch("E2")))

    # -- A'': tutti --------------------------------------------------------------------------------
    a3 = s.section("A'' · tutti", M8_THEME_H + " | " + M8_THEME_H)
    for rep in range(2):
        b1 = a3 + 8 * rep
        s.line("tbn", M8_THEME, b1, 100, MARCATO, accent=8)
        s.line("tuba", M8_THEME, b1, 84, MARCATO, octave=-1)
        s.line("horns", M8_THEME, b1, 98, MARCATO, octave=1)
        if A:
            s.line("tpt", M8_THEME, b1, 92, MARCATO, octave=1)
        else:
            s.harmonize("brass", M8_THEME, b1, 80, MARCATO, octave=1, voices=2)
            s.line("choir", M8_THEME, b1, 74, LEGATO, octave=1)
        if rep == 1:
            s.line("strings", M8_COUNTER, b1, 82, LEGATO)
        for b in range(b1, b1 + 8):
            m8_yard(s, b, fl, 3)
            m8_engine(s, b, fl, 3)
            s.chords("trem", b, "A3", 58)
        s.hit(CRASH, b1 * 4, 108)
        s.hit(CHINA, (b1 + 4) * 4, 84)
        ship_bell(s, b1, 84)

    # -- Coda: the hull-call once more, the dominant hangs ---------------------------------------
    d0 = s.section("Return", M8_CODA_H)
    s.line("horns", M8_CODA, d0, 94, MARCATO)
    s.line("tbn", M8_CODA, d0, 98, MARCATO, octave=-1)
    s.line("tuba", M8_CODA, d0, 82, MARCATO, octave=-2)
    for b in range(d0, d0 + 4):
        m8_yard(s, b, fl, 3 if b < d0 + 3 else 1)
        m8_engine(s, b, fl, 3 if b < d0 + 3 else 1)
    s.roll(SNARE, (d0 + 3) * 4 + 2.0, 2.0, 50, 100, 0.125)
    return s.finish()


# =============================================================================================
# MAP09 -- Tunguska (written in C minor)
# =============================================================================================
# The motif: a quartal climb -- tonic, up a fourth, a step down, then a leap that grows each
# time it comes back (to the seventh, to the octave, to the eleventh): the portal opening.

M9_THEME_H = "Cm | Fm,Bb | Ab | G | Cm | Db,Eb | Fm,G7 | Cm"
M9_THEME = mel("""
C4:3 F4:1 Eb4:4 Bb4:8 | Ab4:3 Bb4:1 G4:4 F4:4 D4:4 | C4:3 F4:1 Eb4:4 C5:8 | B4:4 G4:4 D5:8 |
C4:3 F4:1 Eb4:4 Bb4:8 | Db5:3 C5:1 Bb4:4 Ab4:4 G4:4 | Ab4:3 C5:1 F5:4 D5:4 B4:4 | C5:12 r:4""")
# B: «the arena» -- relentless 3-3-2 brass over the 16th ostinato.
M9_ARENA_H = "Cm | Ab,G | Fm | Db | Cm | Ab | Fm,G | G7"
M9_ARENA = mel("""
G4:3 C5:3 Eb5:2 D5:4 C5:4 | Eb5:3 C5:3 Ab4:2 G4:8 | F4:3 Ab4:3 C5:2 Bb4:4 Ab4:4 | Db5:3 C5:3 Ab4:2 F4:8 |
G4:3 C5:3 Eb5:2 G5:4 F5:4 | F5:3 Eb5:3 C5:2 Ab4:8 | F4:3 Ab4:3 C5:2 B4:4 D5:4 | B4:4 D5:4 F5:4 G5:4""")
# C: «the heart of the portal» -- organ and choir chorale.
M9_CHORALE_H = "Ab | Eb/G | Fm | Cm/Eb | Db | Ab/C | Bbm | G"
M9_CHORALE = mel("""C5:12 Bb4:4 | Bb4:8 Eb5:8 | C5:12 Ab4:4 | G4:16 | Ab4:12 F4:4 | Eb4:8 Ab4:8 |
Bb4:12 Db5:4 | D5:16""")
M9_BUILD_H = "Ab | Fm | G | G7"
M9_BUILD = mel("Eb4:3 Ab4:1 G4:4 Eb5:8 | Eb4:3 Ab4:1 G4:4 F5:8 | D4:3 G4:1 F4:4 B4:4 D5:4 | G4:4 B4:4 D5:4 G5:4")
M9_CODA_H = "Cm | Db | G7 | G7"
M9_CODA = mel("C4:3 F4:1 Eb4:4 Bb4:8 | Db5:3 C5:1 Ab4:4 F4:8 | G4:4 B4:4 D5:4 F5:4 | G5:4 r:4 G4:4 r:4")

M9_VARIANTS = (
    Variant("D_SDM09A", "A", 132.0, 0, "C minor, 132 BPM: brass up front (horns + trombones, then "
            "trumpets with brass choir), church organ underneath, timpani and snare; the arena "
            "with brass hits in hemiola"),
    Variant("D_SDM09B", "B", 138.0, -1, "B minor, 138 BPM, more mechanical: organ and choir carry the theme, "
            "3-3-2 ostinato, taiko and orchestra hits, block brass; trumpets only in the tutti"),
)


def m9_engine(s: Song, b: int, fl: str, level: int) -> None:
    """Organ, the relentless ostinato, bass, timpani."""
    lv = min(level, 4)
    s.chords("organ", b, "G3", 50 + 5 * lv, bass=True)
    if level >= 1:
        if fl == "A":
            s.pattern("low", b, "RrrrRrrfRrrrRrro", "C2", 60 + 3 * lv, art=0.55, accent=14)
            s.pattern("bass", b, "R..rR..rR..rR..r", "E1", 76 + 2 * lv, art=0.75)
        else:
            s.pattern("low", b, "R..r..R..r..R.r.", "C2", 66 + 3 * lv, art=0.7, accent=14)
            s.pattern("bass", b, "R..r..R..r..R.r.", "E1", 78 + 2 * lv, art=0.8)
    if level >= 2:
        s.timp(b, "R.......F......." if level < 4 else "R.r.R.r.F.f.F.f.", 80)


def m9_drums(s: Song, b: int, fl: str, level: int) -> None:
    pats = {}
    if fl == "A":
        if level >= 1:
            pats[KICK] = "X.......X......."
            pats[LOW_FLOOR_TOM] = "..g...g...g...g."
        if level >= 2:
            pats[KICK] = "X..X....X..X...."
            pats[SNARE] = "....X.......X..."
        if level >= 3:
            pats[KICK] = "X.XX....X.XX...."
            pats[SNARE] = "....X..g....X.gg"
        if level >= 4:
            pats[KICK] = "X.X.X.X.X.X.X.X."
            pats[SNARE] = "....X..x....X..."
            pats[LOW_TOM] = "............xxXX" if b % 4 == 3 else "................"
            pats[CLOSED_HH] = "x.x.x.x.x.x.x.x."
    else:
        if level >= 1:
            s.n("taiko", pitch("C3"), b * 4, 0.5, 100)
            s.n("taiko", pitch("C3"), b * 4 + 1.5, 0.5, 82)
        if level >= 2:
            pats[KICK] = "X.....X...X....."
            pats[SNARE] = "........X......."
        if level >= 3:
            pats[KICK] = "X..X..X...X..X.."
            pats[SNARE] = "....X.......X..."
            s.n("taiko", pitch("C3"), b * 4 + 3.0, 0.5, 86)
        if level >= 4:
            pats[KICK] = "X..X..X.X..X..X."
            pats[SNARE] = "....X..g....X.gg"
            pats[MID_TOM] = "............xxXX" if b % 4 == 3 else "................"
    if pats:
        s.drums(b, pats, 92)


def build_map09(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "organ": Part(CHURCH_ORGAN, 62 if A else 76, 64, 96),
        "bass": Part(CONTRABASS if A else SYNTH_BASS_2, 86, 64),
        "low": Part(CELLO, 72, 30),
        "trem": Part(TREMOLO, 62, 92),
        "strings": Part(STRINGS, 78, 76),
        "choir": Part(CHOIR, 78 if A else 90, 64),
        "horns": Part(HORNS, 124, 44),
        "tbn": Part(TROMBONE, 104, 88),
        "tuba": Part(TUBA, 84, 60),
        "tpt": Part(TRUMPET, 110, 54),
        "brass": Part(BRASS, 86, 72),
        "timp": Part(TIMPANI, 96, 70),
    }
    if not A:
        parts["taiko"] = Part(TAIKO, 90, 64, 50)
        parts["hit"] = Part(ORCH_HIT, 74, 64)
    s = Song(v.lump, "MAP09 Tunguska", v.bpm, v.transpose, (0 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "tbn", "choir") if A else ("horns", "tpt", "tbn", "choir", "organ"))
    fl = v.flavour
    g_pc = (7 + v.transpose) % 12

    # -- Intro: the dead forest, the hum of the portal --------------------------------------------
    i0 = s.section("Intro · the dead forest", "Db/C | Cm | Cm | G7")
    for b in range(i0, i0 + 4):
        m9_engine(s, b, fl, 0 if b < i0 + 2 else 1)
        s.chords("choir", b, "G3", 48 + 6 * (b - i0))
        s.chords("trem", b, "G3", 44 + 6 * (b - i0))
        m9_drums(s, b, fl, 1 if b >= i0 + 2 else 0)
    s.line("horns", [M9_THEME[0]], i0 + 2, 90, MARCATO)
    s.line("tbn", [M9_THEME[0]], i0 + 2, 84, MARCATO, octave=-1)
    s.line("horns", [M9_THEME[3]], i0 + 3, 94, MARCATO)
    s.line("tbn", [M9_THEME[3]], i0 + 3, 88, MARCATO, octave=-1)
    s.roll("timp", (i0 + 3) * 4, 4.0, 40, 108, 0.25, p=in_range(g_pc, pitch("E2")))

    # -- A ------------------------------------------------------------------------------------
    a1 = s.section("A · the theme", M9_THEME_H)
    if A:
        s.line("horns", M9_THEME, a1, 100, MARCATO, accent=6)
        s.line("tbn", M9_THEME, a1, 90, MARCATO, octave=-1)
    else:
        s.line("organ", M9_THEME, a1, 92, LEGATO, octave=1)
        s.line("choir", M9_THEME, a1, 90, LEGATO)
        s.line("horns", M9_THEME, a1, 80, MARCATO, octave=-1)
    for b in range(a1, a1 + 8):
        m9_engine(s, b, fl, 2)
        m9_drums(s, b, fl, 2)
        s.chords("strings", b, "G3", 52)
        if (b - a1) % 4 == 3:
            s.chords("brass", b, "E4", 84, hits=(0.0, 1.5, 3.0), length=0.5)
    s.hit(CRASH, a1 * 4, 104)
    if not A:
        s.chords("hit", a1, "C4", 96, hits=(0.0,), length=0.5)

    # -- A': trumpets and the brass choir -------------------------------------------------------
    a2 = s.section("A' · brass choir", M9_THEME_H)
    if A:
        s.line("tpt", M9_THEME, a2, 100, MARCATO, accent=6)
        s.harmonize("horns", M9_THEME, a2, 82, MARCATO, voices=2)
        s.line("tbn", M9_THEME, a2, 88, MARCATO, octave=-1)
    else:
        s.line("horns", M9_THEME, a2, 100, MARCATO, accent=6)
        s.harmonize("brass", M9_THEME, a2, 80, MARCATO, voices=2)
        s.line("choir", M9_THEME, a2, 80, LEGATO)
    s.line("tuba", M9_THEME, a2, 74, MARCATO, octave=-2)
    for b in range(a2, a2 + 8):
        m9_engine(s, b, fl, 3)
        m9_drums(s, b, fl, 3)
        s.chords("choir" if A else "strings", b, "G3", 56)
        s.chords("trem", b, "G3", 58)
    s.hit(CRASH, a2 * 4, 108)
    s.hit(CRASH2, (a2 + 4) * 4, 90)

    # -- B: the arena -----------------------------------------------------------------------------
    b0 = s.section("B · the arena", M9_ARENA_H + " | " + M9_ARENA_H)
    for rep in range(2):
        b1 = b0 + 8 * rep
        s.line("horns", M9_ARENA, b1, 100, MARCATO, accent=6)
        s.line("tbn", M9_ARENA, b1, 92, MARCATO, octave=-1)
        if rep == 1:
            s.line("tpt" if A else "organ", M9_ARENA, b1, 92, MARCATO, octave=0 if A else 1)
            s.chords("choir", b1, "G3", 62)
        for b in range(b1, b1 + 8):
            m9_engine(s, b, fl, 4)
            m9_drums(s, b, fl, 4)
            if A:
                s.chords("brass", b, "E4", 82, hits=(0.0, 1.5, 3.0), length=0.35)
            else:
                s.chords("brass", b, "E4", 84, hits=(0.0, 0.75, 1.5), length=0.35)
                if b % 2 == 0:
                    s.chords("hit", b, "C4", 92, hits=(0.0,), length=0.5)
            s.chords("trem", b, "G3", 60 + 6 * rep)
            if rep == 1:
                s.chords("choir", b, "G3", 62)
        s.hit(CRASH, b1 * 4, 110)

    # -- C: the heart of the portal ----------------------------------------------------------------
    c0 = s.section("C · the heart of the portal", M9_CHORALE_H)
    s.line("choir", M9_CHORALE, c0, 90, LEGATO, accent=4)
    s.harmonize("organ", M9_CHORALE, c0, 70, LEGATO, voices=2)
    s.line("horns", M9_CHORALE, c0, 72 if A else 64, LEGATO, octave=-1)
    for b in range(c0, c0 + 8):
        bass_roots(s, "bass", b, "E1", 70)
        bass_roots(s, "organ", b, "C2", 66)
        s.chords("trem", b, "G3", 44)
        s.drums(b, {LOW_FLOOR_TOM: "X.....x...x....."}, 70)
    s.roll("timp", (c0 + 7) * 4, 4.0, 40, 108, 0.25, p=in_range(g_pc, pitch("E2")))

    # -- Build -------------------------------------------------------------------------------------
    k0 = s.section("Build", M9_BUILD_H)
    s.line("tpt", M9_BUILD, k0, 94, MARCATO, swell=4)
    s.line("horns", M9_BUILD, k0, 90, MARCATO, octave=-1, swell=4)
    s.line("tbn", M9_BUILD, k0, 86, MARCATO, octave=-1, swell=4)
    for b in range(k0, k0 + 4):
        m9_engine(s, b, fl, 3)
        m9_drums(s, b, fl, 2)
        s.pattern("strings", b, "rtforfotrtforfot", "G3", 58 + 5 * (b - k0), art=0.6)
        s.chords("choir", b, "G3", 56 + 5 * (b - k0))
    s.roll(SNARE, (k0 + 2) * 4, 8.0, 40, 116)
    s.roll("timp", (k0 + 3) * 4, 4.0, 60, 116, 0.25, p=in_range(g_pc, pitch("E2")))

    # -- A'': the portal opens (tutti) ----------------------------------------------------------------
    a3 = s.section("A'' · tutti", M9_THEME_H + " | " + M9_THEME_H)
    for rep in range(2):
        b1 = a3 + 8 * rep
        s.line("tpt", M9_THEME, b1, 102, MARCATO, accent=6)
        s.line("horns", M9_THEME, b1, 96, MARCATO, octave=-1 if rep else 0)
        s.harmonize("tbn", M9_THEME, b1, 84, MARCATO, octave=-1, voices=2)
        s.harmonize("brass", M9_THEME, b1, 72, MARCATO)
        s.line("tuba", M9_THEME, b1, 76, MARCATO, octave=-2)
        if rep == 1:
            s.line("strings", M9_THEME, b1, 80, LEGATO, octave=1)
            if not A:
                s.line("organ", M9_THEME, b1, 84, LEGATO, octave=1)
        for b in range(b1, b1 + 8):
            m9_engine(s, b, fl, 3 if rep == 0 else 4)
            m9_drums(s, b, fl, 3 if rep == 0 else 4)
            s.chords("choir", b, "G3", 62)
            s.chords("trem", b, "G3", 62)
        s.hit(CRASH, b1 * 4, 110)
        if not A:
            s.chords("hit", b1, "C4", 98, hits=(0.0,), length=0.5)

    # -- Coda ----------------------------------------------------------------------------------------
    d0 = s.section("Return", M9_CODA_H)
    s.line("tpt", M9_CODA, d0, 98, MARCATO)
    s.line("horns", M9_CODA, d0, 94, MARCATO, octave=-1)
    s.line("tbn", M9_CODA[:3], d0, 88, MARCATO, octave=-1)
    for b in range(d0, d0 + 4):
        m9_engine(s, b, fl, 3)
        m9_drums(s, b, fl, 3 if b < d0 + 3 else 2)
        s.chords("choir", b, "G3", 60)
    s.chords("tbn", d0 + 3, "D3", 100, hits=(0.0, 2.0), length=0.6)
    s.chords("tuba", d0 + 3, "E2", 96, hits=(0.0, 2.0), length=0.6)
    s.roll(SNARE, (d0 + 3) * 4 + 3.0, 1.0, 60, 110, 0.125)
    return s.finish()


# =============================================================================================
# Final boss -- the portal arena (written in C minor, its own loop)
# =============================================================================================
# The boss cell: a long note, a tritone below it, the semitone up (C ... F#-G): the portal's
# guardian. Sections: the guardian · the call (trumpets) · MAP09's theme over the riff ·
# a chromatic rise · tutti, straight back into the guardian.

BS9_H = "Cm | Ab,Bb7 | Cm | G | Fm | Db | G | G7"
BS9_THEME = mel("""
C5:6 F#4:2 G4:8 | Eb5:6 A4:2 Bb4:4 Ab4:4 | C5:6 F#4:2 G4:4 Eb5:4 | D5:6 G#4:2 A4:4 B4:4 |
F5:6 B4:2 C5:8 | Db5:6 G4:2 Ab4:8 | G4:4 Ab4:4 B4:4 D5:4 | F5:8 Eb5:4 D5:4""")
BS9_RISE_H = "Ab | Ab | Bbm | Bbm | Bdim7 | Bdim7 | G | G7"
BS9_RISE = mel("""Eb5:4 C5:4 Ab4:8 | Eb5:16 | F5:4 Db5:4 Bb4:8 | F5:16 | F5:4 D5:4 B4:8 | Ab5:16 |
G5:16 | G5:4 G5:4 G5:4 G5:4""")

BS9_VARIANTS = (
    Variant("D_SDBS9A", "A", 140.0, 0, "C minor, 140 BPM (paired with D_SDM09A): 3-3-3-3-2-2 riff on "
            "cellos and double basses, the guardian cell on horns, trumpets on the call, the Tunguska "
            "theme in the middle, organ and choir"),
    Variant("D_SDBS9B", "B", 146.0, -1, "B minor, 146 BPM (paired with D_SDM09B): the same guardian with "
            "organ up front, taiko and orchestra hits, block brass on the offbeat"),
)


def bs9_riff(s: Song, b: int, fl: str, level: int) -> None:
    if fl == "A":
        s.pattern("low", b, "R..N..R..L..R.n.", "C2", 72, art=0.6, accent=14)
        s.pattern("bass", b, "R..R..R..R..R.R.", "E1", 80, art=0.7)
    else:
        s.pattern("low", b, "RrNrRrLrRrNrRrfo", "C2", 70, art=0.55, accent=14)
        s.pattern("bass", b, "R..R..R..R..R.R.", "E1", 82, art=0.7)
    s.pattern("tuba", b, "R..r..R..r..R.r.", "C2", 70 + 4 * min(level, 3), art=0.7)
    s.chords("organ", b, "G3", 58 + 4 * min(level, 3), bass=True)
    s.timp(b, "R..r..R..r..F.f." if level >= 3 else "R.......F.......", 82)


def build_boss(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "organ": Part(CHURCH_ORGAN, 62 if A else 76, 64, 96),
        "bass": Part(CONTRABASS if A else SYNTH_BASS_2, 86, 64),
        "low": Part(CELLO, 72, 30),
        "trem": Part(TREMOLO, 60, 92),
        "strings": Part(STRINGS, 76, 76),
        "choir": Part(CHOIR, 76, 64),
        "horns": Part(HORNS, 124, 44),
        "tbn": Part(TROMBONE, 104, 88),
        "tuba": Part(TUBA, 84, 60),
        "tpt": Part(TRUMPET, 110, 54),
        "brass": Part(BRASS, 86, 72),
        "timp": Part(TIMPANI, 96, 70),
    }
    if not A:
        parts["taiko"] = Part(TAIKO, 90, 64, 50)
        parts["hit"] = Part(ORCH_HIT, 74, 64)
    s = Song(v.lump, "Final boss, the portal", v.bpm, v.transpose, (0 + v.transpose) % 12, parts,
             lead_parts=("horns", "tpt", "tbn", "organ") if not A else ("horns", "tpt", "tbn"))
    fl = v.flavour
    g_pc = (7 + v.transpose) % 12

    def stabs(b: int) -> None:
        if A:
            s.chords("brass", b, "E4", 82, hits=(0.0, 1.5, 3.0), length=0.35)
        else:
            s.chords("brass", b, "E4", 84, hits=(0.75, 1.5, 2.75, 3.5), length=0.3)
            if b % 2 == 0:
                s.chords("hit", b, "C4", 94, hits=(0.0,), length=0.5)

    g0 = s.section("I · the guardian", BS9_H)
    s.line("horns", BS9_THEME, g0, 100, MARCATO, accent=6)
    s.line("tbn", BS9_THEME, g0, 92, MARCATO, octave=-1)
    if not A:
        s.line("organ", BS9_THEME, g0, 80, LEGATO)
    for b in range(g0, g0 + 8):
        bs9_riff(s, b, fl, 3)
        m9_drums(s, b, fl, 3)
        s.chords("choir", b, "G3", 58)
        s.chords("trem", b, "G3", 56)
    s.hit(CRASH, g0 * 4, 106)

    l0 = s.section("II · the call", BS9_H)
    s.line("tpt", BS9_THEME, l0, 102, MARCATO, accent=6)
    s.harmonize("horns", BS9_THEME, l0, 82, MARCATO, voices=2)
    s.line("tbn", BS9_THEME, l0, 90, MARCATO, octave=-1)
    for b in range(l0, l0 + 8):
        bs9_riff(s, b, fl, 4)
        m9_drums(s, b, fl, 4)
        stabs(b)
        s.chords("choir", b, "G3", 62)
        s.chords("trem", b, "G3", 62)
    s.hit(CRASH, l0 * 4, 110)

    p0 = s.section("III · the portal (MAP09's theme)", M9_THEME_H)
    s.line("horns", M9_THEME, p0, 100, MARCATO, accent=6)
    s.line("tbn", M9_THEME, p0, 90, MARCATO, octave=-1)
    s.line("choir", M9_THEME, p0, 78, LEGATO)
    for b in range(p0, p0 + 8):
        bs9_riff(s, b, fl, 3)
        m9_drums(s, b, fl, 3)
        s.chords("strings", b, "G3", 56)
    s.hit(CRASH, p0 * 4, 104)

    r0 = s.section("IV · build", BS9_RISE_H)
    s.line("tpt", BS9_RISE, r0, 92, MARCATO, swell=1.5)
    s.line("horns", BS9_RISE, r0, 86, MARCATO, octave=-1, swell=1.5)
    for b in range(r0, r0 + 8):
        bs9_riff(s, b, fl, 2 if b < r0 + 4 else 3)
        m9_drums(s, b, fl, 2 if b < r0 + 4 else 3)
        s.pattern("strings", b, "rtforfotrtforfot", "G3", 58 + 3 * (b - r0), art=0.6)
        s.chords("choir", b, "G3", 52 + 3 * (b - r0))
        if b >= r0 + 4:
            s.chords("tbn", b, "D3", 80 + 3 * (b - r0), hits=(0.0, 1.0, 2.0, 3.0), length=0.5)
    s.roll(SNARE, (r0 + 6) * 4, 8.0, 44, 116, 0.125)
    s.roll("timp", (r0 + 7) * 4, 4.0, 60, 116, 0.25, p=in_range(g_pc, pitch("E2")))

    t0 = s.section("V · tutti", BS9_H)
    s.line("tpt", BS9_THEME, t0, 104, MARCATO, accent=6)
    s.line("horns", BS9_THEME, t0, 96, MARCATO, octave=-1)
    s.harmonize("tbn", BS9_THEME, t0, 86, MARCATO, octave=-1, voices=2)
    s.line("strings", BS9_THEME, t0, 80, LEGATO, octave=1)
    s.line("choir", BS9_THEME, t0, 74, LEGATO)
    for b in range(t0, t0 + 8):
        bs9_riff(s, b, fl, 4)
        m9_drums(s, b, fl, 4)
        stabs(b)
        s.chords("trem", b, "G3", 64)
    s.hit(CRASH, t0 * 4, 112)
    return s.finish()


# =============================================================================================
# Episode 3 intermission -- the three motifs (written in C minor)
# =============================================================================================
# bars 1-4 the Novaya Zemlya call a semitone up, 5-8 the Severomorsk hull-call a tone down,
# 9-16 the Tunguska theme: the whole road to the portal in sixteen bars.

INT3_RADAR = mel("C4:4 Ab4:8 G4:4 | F4:3 G4:1 Eb4:4 D4:8 | C4:4 Ab4:4 F4:4 Db5:4 | C5:12 B4:4")
INT3_FLEET = mel("""C4:4 F4:4 Eb4:3 D4:1 C4:4 | Bb3:4 Eb4:4 D4:3 C4:1 B3:4 |
Ab3:4 Db4:4 C4:3 Bb3:1 Ab3:4 | G3:4 D4:4 F4:2 Eb4:2 D4:4""")
INT3_H = "Cm | Fm,G | Cm,Db | G7 | Fm,Cm | Eb,G | Db,Ab | G7 | " + M9_THEME_H

INT3_VARIANTS = (
    Variant("D_SDE3IA", "A", 96.0, 0, "C minor, 96 BPM, intimate: the radar on solo horn with celesta, "
            "the naval base on trombones with sonar, Tunguska on horns + choir and soft organ"),
    Variant("D_SDE3IB", "B", 108.0, 0, "C minor, 108 BPM, marching: horns, trombones and trumpets with "
            "snare, ship's bell and organ; the three motifs without a pause"),
)


def build_intermission(v: Variant) -> Song:
    A = v.flavour == "A"
    parts = {
        "horns": Part(HORNS, 114, 44),
        "tbn": Part(TROMBONE, 96, 88),
        "tuba": Part(TUBA, 84, 60),
        "trem": Part(TREMOLO, 62, 92),
        "strings": Part(STRINGS, 80, 76),
        "low": Part(CELLO, 76, 30),
        "organ": Part(CHURCH_ORGAN, 62 if A else 72, 64, 96),
        "timp": Part(TIMPANI, 86, 70),
    }
    if A:
        parts["cel"] = Part(CELESTA, 92, 96, 110)
        parts["sonar"] = Part(CRYSTAL, 80, 100, 110)
        parts["oohs"] = Part(VOICE_OOHS, 82, 64, 96)
    else:
        parts["tpt"] = Part(TRUMPET, 100, 54)
        parts["brass"] = Part(BRASS, 92, 72)
        parts["bells"] = Part(TUBULAR_BELLS, 80, 84)
    s = Song(v.lump, "Episode 3 intermission", v.bpm, v.transpose, 0, parts,
             lead_parts=("horns", "tpt", "tbn", "oohs"))
    r0 = s.section("Novaya Zemlya", "Cm | Fm,G | Cm,Db | G7")
    f0 = s.section("Severomorsk", "Fm,Cm | Eb,G | Db,Ab | G7")
    t0 = s.section("Tunguska", M9_THEME_H)
    if A:
        s.line("horns", INT3_RADAR, r0, 92, LEGATO, accent=4)
        s.line("tbn", INT3_FLEET, f0, 104, MARCATO, accent=8)
        s.line("horns", INT3_FLEET, f0, 82, LEGATO, octave=1)
        s.line("tuba", INT3_FLEET, f0, 78, MARCATO, octave=-1)
        s.line("horns", M9_THEME, t0, 94, LEGATO, accent=4)
        s.line("oohs", M9_THEME, t0, 72, LEGATO)
        for b in range(s.bars):
            bass_roots(s, "low", b, "C2", 62)
            s.chords("trem", b, "G3", 40 if b < t0 else 48)
            if b < f0:
                if b % 2 == 0:
                    ping(s, "cel", pitch("G6"), b * 4, 76, echoes=3, gap=0.75, length=1.2)
                s.pattern("cel", b, "r.t.f.o.t.f.o.f.", "C5", 36, art=0.9)
            elif b < t0:
                if b % 2 == 0:
                    ping(s, "sonar", pitch("G5"), b * 4, 74, echoes=2, gap=1.5, length=1.4, decay=0.5)
                s.drums(b, {RIDE_BELL: "x.....x.....x..."}, 52)
            else:
                s.chords("organ", b, "G3", 46, bass=True)
                s.chords("strings", b, "C4", 50)
            if b % 4 == 3:
                bpc, _ = s.chord(s.harmony[b][-1][2])
                s.roll("timp", b * 4 + 2.0, 2.0, 34, 70, 0.25, p=in_range(bpc, pitch("E2")))
        s.drums(15, {SNARE: "........gggggggg"}, 60)
    else:
        s.line("horns", INT3_RADAR, r0, 96, MARCATO)
        s.harmonize("brass", INT3_RADAR, r0, 72, MARCATO)
        s.line("tbn", INT3_FLEET, f0, 100, MARCATO, accent=8)
        s.line("tuba", INT3_FLEET, f0, 80, MARCATO, octave=-1)
        s.line("horns", INT3_FLEET, f0, 84, MARCATO, octave=1)
        s.line("tpt", M9_THEME, t0, 98, MARCATO)
        s.harmonize("horns", M9_THEME, t0, 78, MARCATO, voices=2)
        s.line("tbn", M9_THEME, t0, 84, MARCATO, octave=-1)
        for b in range(s.bars):
            s.pattern("tuba", b, "R.......F.......", "C2", 78)
            s.timp(b, "R.......F.......", 74)
            s.chords("strings", b, "G3", 50)
            if b >= t0:
                s.chords("organ", b, "G3", 52, bass=True)
            if r0 <= b < f0:
                s.drums(b, {MUTE_TRIANGLE: "X.x.x.x.x.x.x.x.", KICK: "X.....x.X.....x.", SNARE: "....x.......X..."}, 80)
            elif b < t0:
                s.drums(b, {RIDE_BELL: "X..x..x.X..x..x.", KICK: "X.......X.......", SNARE: "....X.......X.R."}, 84)
            else:
                s.drums(b, {KICK: "X..X....X..X....", SNARE: "....X.......X..."}, 86)
        ship_bell(s, f0, 80)
        s.hit(CRASH, 0, 92)
        s.hit(CRASH, f0 * 4, 88)
        s.hit(CRASH, t0 * 4, 98)
        s.roll(SNARE, 15 * 4 + 2.0, 2.0, 50, 96, 0.125)
    return s.finish()


# =============================================================================================
# Catalogue, checks, rendering
# =============================================================================================

PIECES = {"MAP07": (build_map07, M7_VARIANTS), "MAP08": (build_map08, M8_VARIANTS),
          "MAP09": (build_map09, M9_VARIANTS), "BOSS9": (build_boss, BS9_VARIANTS),
          "E3INT": (build_intermission, INT3_VARIANTS)}
WINDOW_OF = {"MAP07": "map", "MAP08": "map", "MAP09": "map", "BOSS9": "boss", "E3INT": "int"}
# Target loudness of the loop (RMS dBFS through zmusic): MAP01's installed N2 sits at -25.7,
# Episode 2's boss loops at -24.7, its intermissions at -28.5.
TARGET_RMS = {"MAP07": -25.9, "MAP08": -25.7, "MAP09": -25.5, "BOSS9": -24.7, "E3INT": -28.5}
RECOMMENDED = {"D_SDM07A", "D_SDM08A", "D_SDM09A", "D_SDBS9A", "D_SDE3IA"}


def all_songs() -> list[tuple[str, Variant, Song]]:
    return [(key, v, fn(v)) for key, (fn, variants) in PIECES.items() for v in variants]


def _is_melody(val) -> bool:
    return (isinstance(val, list) and bool(val) and all(
        isinstance(bar, list) and bar and all(isinstance(t, tuple) and len(t) == 2 for t in bar) for bar in val))


def melodies_of(module) -> dict[str, list]:
    """Every written melody (a module-level list of bars of (note, beats)) of a composer module."""
    out = {name: val for name, val in vars(module).items() if name.isupper() and _is_melody(val)}
    advance = getattr(module, "ADVANCE", None)                 # compose_map01: (who, bar) pairs
    if isinstance(advance, list) and advance and all(isinstance(x, tuple) and len(x) == 2 for x in advance):
        out["ADVANCE"] = [bar for _, bar in advance]
    return out


def shapes(bars) -> set:
    """Two-bar shapes (intervals + rhythm): transposition does not hide a copy."""
    out = set()
    for a, b in zip(bars, bars[1:]):
        seq = [(pitch(n), d) for n, d in a + b if n]
        out.add((tuple(y - x for (x, _), (y, _) in zip(seq, seq[1:])), tuple(float(d) for _, d in a + b)))
    return out


def interval_ngrams(pitches: list[int], n: int = QUOTE_NGRAM) -> set:
    """Interval runs of length n, minus the ones any tonal line shares (scales, repeats, see-saws)."""
    iv = [b - a for a, b in zip(pitches, pitches[1:])]
    out = set()
    for k in range(len(iv) - n + 1):
        g = tuple(iv[k:k + n])
        if sum(1 for x in g if x == 0) >= 3 or len(set(g)) <= 2:
            continue
        if all(abs(x) <= 2 for x in g) and (all(x >= 0 for x in g) or all(x <= 0 for x in g)):
            continue
        out.add(g)
    return out


def midi_voices(data: bytes) -> list[list[int]]:
    """Top and bottom voice of every non-drum channel: one pitch per onset."""
    import midi_edit as me
    _, _, tracks = me.read_smf(data)
    onsets: dict[int, dict[int, list[int]]] = {}
    for events in tracks:
        for tick, raw in events:
            if len(raw) == 3 and raw[0] & 0xF0 == 0x90 and raw[2] > 0 and raw[0] & 0x0F != gm.DRUM_CHANNEL:
                onsets.setdefault(raw[0] & 0x0F, {}).setdefault(tick, []).append(raw[1])
    out = []
    for by_tick in onsets.values():
        ticks = sorted(by_tick)
        out.append([max(by_tick[t]) for t in ticks])
        out.append([min(by_tick[t]) for t in ticks])
    return out


def reference_ngrams(folder: Path = INSTALLED_MUSIC, skip: frozenset[str] = frozenset()) -> dict[tuple, str]:
    """Interval runs of every installed piece (Episodes 1-2), mapped to the first lump having it.

    `skip`: lumps left out of the scan. Since D113 installed Episode 3's own ten pieces in
    assets/music/, self_check skips them: a piece always "quotes" itself."""
    found: dict[tuple, str] = {}
    for path in sorted(folder.glob("*.mid")):
        if path.stem in skip:
            continue
        for voice in midi_voices(path.read_bytes()):
            for g in interval_ngrams(voice):
                found.setdefault(g, path.stem)
    return found


def quote_hits(melodies: dict[str, list], refs: dict[tuple, str] | None = None) -> list[str]:
    refs = reference_ngrams() if refs is None else refs
    hits = []
    for name, bars in melodies.items():
        line = [pitch(nm) for bar in bars for nm, _ in bar if nm]
        same = sorted({refs[g] for g in interval_ngrams(line) if g in refs})
        if same:
            hits.append(f"{name}: an 8-note run equals one in {', '.join(same)}")
    return hits


def self_check(songs) -> list[str]:
    """Originality and structure checks (bar sums are checked by mel()). Returns problems."""
    import compose_map01 as cm
    problems = []
    ours = melodies_of(sys.modules[__name__])
    earlier: set = set()
    for module in (cm, e2):
        for bars in melodies_of(module).values():
            earlier |= shapes(bars)
    for name, bars in ours.items():
        clash = shapes(bars) & earlier
        if clash:
            problems.append(f"{name}: a two-bar shape equals one of Episode 1-2's ({len(clash)})")
    if INSTALLED_MUSIC.is_dir():
        problems += quote_hits(ours, reference_ngrams(skip=frozenset(v.lump for _k, v, _s in songs)))
    else:
        problems.append(f"{INSTALLED_MUSIC} missing: the quotation scan did not run")
    by_key: dict[str, list] = {}
    for key, v, s in songs:
        by_key.setdefault(key, []).append((v, s))
        if len(v.lump) > 8:
            problems.append(f"{v.lump}: lump name longer than 8 characters")
        if any(not 0 <= p <= 127 for _, p, *_ in s.notes):
            problems.append(f"{v.lump}: a note outside the MIDI range")
        for part, p, st, ln, vel in s.notes:
            lo, hi = e2.RANGE.get(s.parts[part].program, (0, 127))
            if part in ("tpt", "horns", "tbn", "choir", "oohs") and not lo - 5 <= p <= hi:
                problems.append(f"{v.lump}: {part} note {p} at beat {st} outside {lo}-{hi}")
                break
        if len(s.parts) > 15:
            problems.append(f"{v.lump}: {len(s.parts)} parts, 15 channels")
        secs = s.seconds()
        lo_s, hi_s = LOOP_WINDOW[WINDOW_OF[key]]
        if not lo_s <= secs <= hi_s:
            problems.append(f"{v.lump}: loop {secs:.1f} s outside {lo_s}-{hi_s} s")
        if not any(st < 0.01 for _, _, st, _, _ in s.notes) and not any(st < 0.01 for _, st, _ in s.hits):
            problems.append(f"{v.lump}: nothing sounds on beat 1 (the seam)")
        if max(st + ln for _, _, st, ln, _ in s.notes) > s.bars * 4 + 1e-6:
            problems.append(f"{v.lump}: a note runs past the loop point")
    for key, pair in by_key.items():
        (va, sa), (vb, sb) = pair
        progs_a = {p.program for p in sa.parts.values()}
        progs_b = {p.program for p in sb.parts.values()}
        if va.bpm == vb.bpm or (va.transpose == vb.transpose and progs_a == progs_b):
            problems.append(f"{key}: variants A and B are too alike (tempo, key, band)")
    return problems


def calibrate_and_render(key: str, v: Variant, s: Song, stems: bool) -> dict:
    import compose_map01 as cm
    import numpy as np
    target = TARGET_RMS[key]
    for _ in range(3):
        x, rate, secs = e2.render_lump(s.midi(), 0.0)
        lv = cm.measure(x, rate)
        delta = target - lv["rms"]
        if abs(delta) < 0.4:
            break
        s.volume_scale *= 10 ** (delta / 40.0)    # FluidSynth CC7 ~ 40*log10
    data = s.midi()
    (OUT_DIR / f"{v.lump}.mid").write_bytes(data)
    x, rate, secs = e2.render_lump(data)
    loop = x[: int(secs * rate)]
    lv = cm.measure(loop, rate)
    bar_s = secs / s.bars
    bounds = [b for _, b in s.sections] + [s.bars]
    lv["arc"] = {}
    for (label, b0), b1 in zip(s.sections, bounds[1:]):
        seg = loop[int(b0 * bar_s * rate): int(b1 * bar_s * rate)]
        lv["arc"][label] = round(float(20 * np.log10(max(np.sqrt(np.mean(seg.mean(axis=1) ** 2)), 1e-9))), 1)
    e2.write_ogg(x, rate, RENDER_DIR / f"{v.lump}.ogg")
    row = {"lump": v.lump, "key": key, "flavour": v.flavour, "bpm": v.bpm, "label": v.label,
           "seconds": secs, "bars": s.bars, "levels": lv, "scale": round(s.volume_scale, 3),
           "sections": [(label, round(b * bar_s, 1)) for label, b in s.sections],
           "programs": sorted({p.program for p in s.parts.values()})}
    if stems:
        lead = [k for k in s.parts if k in s.lead_parts]
        xl, _, _ = e2.render_lump(s.midi(mute=[k for k in s.parts if k not in lead] + ["drums"]), 0.0)
        xb, _, _ = e2.render_lump(s.midi(mute=lead), 0.0)
        row["lead_over_bed_db"] = round(cm.measure(xl, rate)["rms"] - cm.measure(xb, rate)["rms"], 1)
    return row


def levels_txt(rows: list[dict]) -> str:
    lines = ["# Episode 3 drafts (D112): loudness through zmusic + gzdoom.sf2, no normalisation",
             "# peak / RMS / loudest 3 s, dBFS, over the loop; renders run 10 s past the seam.",
             "# Reference: D_SDM1N2 (MAP01, installed) loop RMS -25.7, loud3s -22.3, peak -8.0", ""]
    for r in rows:
        lv = r["levels"]
        lines.append(f"{r['lump']:9s} {r['bpm']:5.0f} BPM  loop {r['seconds']:6.1f} s  peak {lv['peak']:6.1f}  "
                     f"RMS {lv['rms']:6.1f}  loud3s {lv['loud3s']:6.1f}  CC7 scale {r['scale']:.3f}"
                     + (f"  lead-over-bed {r['lead_over_bed_db']:+.1f} dB" if "lead_over_bed_db" in r else ""))
        lines.append("          arc RMS: " + ", ".join(f"{k} {val:.1f}" for k, val in lv["arc"].items()))
    return "\n".join(lines) + "\n"


# -- The listening sheet (Episode 2's page, re-labelled) -------------------------------------------

GROUP_TEXT = {
    "MAP07": ("MAP07 · Novaya Zemlya (Arctic radar station, polar night)",
              "Cold and tense: an echoing radar ping every two bars (celesta in A, vibraphone and "
              "glockenspiel in B), a triangle that ticks, low strings in tremolo and double basses. "
              "The 4-bar motif is a horn call that leaps a minor sixth (B→G) and falls "
              "to the fifth, then leaps again up to the Neapolitan C: the radar beam in the night. "
              "Form: polar night · theme · countermelody · B section · «the radar» (the motif augmented on "
              "trombones, only the pings above) · build · tutti · back to the night."),
    "MAP08": ("MAP08 · Severomorsk (Northern Fleet submarine base)",
              "Heavy and naval: the theme on trombones and tuba, a motif that climbs a fourth and descends by "
              "step, three times, each time a tone lower (the hull diving). Shipyard "
              "percussion (ride bell, low agogo, the ship's bell ringing in pairs), echoing "
              "sonar, engines in the bass. Form: the fjord · theme · brass with countermelody · «the "
              "dock» (the fleet's march in B-flat major) · «dive» (a chorale under the sonar) · "
              "build · tutti · return."),
    "MAP09": ("MAP09 · Tunguska (the portal, the campaign's climax)",
              "Epic and dark: church organ under everything, brass choir and choir, a sixteenth-note "
              "ostinato that never stops. The motif climbs by fourths and its leap grows each time it returns "
              "(to the seventh, the octave, the eleventh): the portal opening. B section «the arena», "
              "brass in 3-3-2 over the ostinato. Form: the dead forest · theme · brass choir · "
              "arena · «the heart of the portal» (organ and choir chorale) · build · tutti · return."),
    "BOSS9": ("Final boss · the portal arena (separate loop)",
              "A piece of its own, not a cut: 3-3-3-3-2-2 riff on cellos, double basses and tuba, the "
              "«guardian cell» (long note, tritone down, semitone up) on horns and then on "
              "trumpets, the Tunguska theme in the middle, a chromatic build and tutti, and it starts "
              "again without a breath. Each version pairs with MAP09's of the same letter."),
    "E3INT": ("Intermission / Episode 3 theme",
              "16 bars that travel the episode: the radar call, the Severomorsk hull and "
              "the Tunguska theme, all three in C minor. For the statistics screen."),
}


def _swap(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"sheet template changed: {old[:50]!r}")
    return text.replace(old, new)


def _swap_block(text: str, start: str, stop: str, new: str) -> str:
    i, j = text.index(start), text.index(stop)
    return text[:i] + new + text[j:]


INTRO_HTML = """<div class="intro">
  <p><b>What this is (D112).</b> <b>Original</b> drafts for Episode 3, «The Portal»: the three maps, a loop of its own for the final boss, and the intermission. Same method and same General MIDI orchestra as the Episode 2 you approved 10/10 (horns, trombones, trumpets, tuba, strings, timpani, GM drums), plus what each place asks for: <b>celesta, vibraphone and glockenspiel</b> for the Arctic radar, <b>ship's bells, shipyard metal and sonar</b> for the submarine base, <b>church organ and choir</b> for the portal. They quote no Soviet or folk song, nor phrases of Episodes 1-2 (the generator checks it): there are no third-party rights.</p>
  <p><b>Two versions of each piece that really sound different</b>: key, tempo, background rhythm and instruments change (in MAP07, the whole B section). The 4-bar motif is the same in both. The one marked <span class="badge">recommended</span> is the one I would install.</p>
  <p class="meta">Rendered with GZDoom's own synthesiser (zmusic + gzdoom.sf2), without starting the game. Each audio <b>runs 10 s past the loop point</b> so you can hear the seam. Volume matched to <code>D_SDM1N2</code> (MAP01). The buttons jump to each section. Nothing installed.</p>
</div>
"""

REFS_HTML = """<h2>References</h2>
<div class="card ref">
  <div class="name"><code>D_SDM1N2</code><span class="ev">1:30 · 128 BPM</span></div>
  <p class="meta">The one that plays in MAP01 (D95). To compare style and volume.</p>
  <audio controls preload="none" src="../map01_new/D_SDM01N2.ogg"></audio>
</div>
<div class="card ref">
  <div class="name"><code>D_SDM06A</code><span class="ev">2:24 · 120 BPM</span></div>
  <p class="meta">MAP06 Red Square, from the approved Episode 2 (D106). The yardstick for this episode.</p>
  <audio controls preload="none" src="../episode2/render/D_SDM06A.ogg"></audio>
</div>

"""


def sheet_template() -> str:
    t = e2.SHEET_TEMPLATE
    t = _swap(t, "<title>Episode 2 Music</title>", "<title>Episode 3 Music</title>")
    t = _swap(t, "Episode 2 Music · «The Road to Moscow»", "Episode 3 Music · «The Portal»")
    t = _swap_block(t, '<div class="intro">', '<div id="items">', INTRO_HTML)
    t = _swap_block(t, "<h2>Reference: MAP01 as installed</h2>", "<h2>Result</h2>", REFS_HTML)
    t = _swap(t, "tools/audio/compose_episode2.py", "tools/audio/compose_episode3.py")
    t = _swap(t, "work/audio/episode2/*.mid", "work/audio/episode3/*.mid")
    t = _swap(t, "work/audio/episode2/render/</code>", "work/audio/episode3/render/</code>")
    t = _swap(t, "sd-2026-10-21_episode2-music", "sd-2026-10-22_episode3-music")
    t = _swap(t, "Episode 2 music (D104, original drafts)", "Episode 3 music (D112, original drafts)")
    return t


def sheet_html(rows: list[dict]) -> str:
    items = []
    for r in rows:
        jumps = [[label, t] for label, t in r["sections"]] + [["Seam (−5 s)", round(r["seconds"] - 5, 1)]]
        items.append({"id": r["lump"], "group": r["key"], "src": f"../episode3/render/{r['lump']}.ogg",
                      "len": f"{int(r['seconds'] // 60)}:{int(round(r['seconds'] % 60)):02d}", "bpm": round(r["bpm"]),
                      "what": r["label"], "jumps": jumps, "rec": r["lump"] in RECOMMENDED})
    order = list(GROUP_TEXT)
    items.sort(key=lambda it: (order.index(it["group"]), it["id"]))
    groups = {k: list(v) for k, v in GROUP_TEXT.items()}
    return sheet_template().replace("__ITEMS__", json.dumps(items, ensure_ascii=False)) \
        .replace("__GROUPS__", json.dumps(groups, ensure_ascii=False)).replace("__N__", str(len(items)))


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
