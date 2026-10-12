#!/usr/bin/env python3
"""Inspect a downloaded Standard MIDI File before we trust it.

    python3 tools/audio/midi_inspect.py work/audio/candidates/*.mid

Why this exists
---------------
A MIDI we did not write is an unknown. Three things routinely go wrong with
third-party sequences and all three are invisible until the engine plays them:

1. **Tempo.** A piece written at 60 BPM and exported at 120 sounds comic. The
   file carries its own tempo map; we read it instead of guessing.
2. **Programs.** General MIDI program numbers decide what the player hears
   through GZDoom's bundled soundfont. A score typeset in LilyPond usually
   ships as "acoustic grand piano on every channel", which is the single most
   common reason a free MIDI sounds like a demo and not like music.
3. **Hanging notes.** A note-on without its note-off drones forever under a
   Doom map. Our own generator is checked for this; downloads must be too.

This reads the bytes itself (no dependencies) and reports what is actually in
the file. It does not modify anything.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

MICROSECONDS_PER_MINUTE = 60_000_000
DEFAULT_TEMPO_US = 500_000          # 120 BPM, the SMF default when none is given
PERCUSSION_CHANNEL = 9              # channel 10, 1-based

# General MIDI program names, grouped the way we care about them.
GM_FAMILIES = (
    "Piano", "Chromatic percussion", "Organ", "Guitar", "Bass", "Strings",
    "Ensemble", "Brass", "Reed", "Pipe", "Synth lead", "Synth pad",
    "Synth effects", "Ethnic", "Percussive", "Sound effects",
)


def gm_family(program: int) -> str:
    return GM_FAMILIES[program // 8]


class Reader:
    """Byte reader with the two SMF-specific primitives."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def take(self, n: int) -> bytes:
        chunk = self.data[self.pos:self.pos + n]
        if len(chunk) != n:
            raise ValueError(f"truncated: wanted {n} bytes at {self.pos}")
        self.pos += n
        return chunk

    def byte(self) -> int:
        return self.take(1)[0]

    def varlen(self) -> int:
        value = 0
        for _ in range(4):
            b = self.byte()
            value = (value << 7) | (b & 0x7F)
            if not b & 0x80:
                return value
        raise ValueError("variable-length quantity longer than 4 bytes")


def parse(path: Path) -> dict:
    data = path.read_bytes()
    r = Reader(data)
    if r.take(4) != b"MThd":
        raise ValueError("not a Standard MIDI File (no MThd)")
    header_len = struct.unpack(">I", r.take(4))[0]
    fmt, ntracks, division = struct.unpack(">HHH", r.take(6))
    r.pos += header_len - 6
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported by this tool")

    tempos: list[tuple[int, int]] = []       # (tick, microseconds per quarter)
    programs: dict[int, set[int]] = {}       # channel -> program numbers
    channels_used: set[int] = set()
    note_count = 0
    hanging = 0
    end_tick = 0
    track_names: list[str] = []
    key_sigs: set[str] = set()
    time_sigs: set[str] = set()

    for _ in range(ntracks):
        if r.take(4) != b"MTrk":
            raise ValueError("expected MTrk")
        length = struct.unpack(">I", r.take(4))[0]
        stop = r.pos + length
        tick = 0
        running = None
        open_notes: dict[tuple[int, int], int] = {}

        while r.pos < stop:
            tick += r.varlen()
            status = r.byte()
            if status < 0x80:                 # running status
                if running is None:
                    raise ValueError("running status with no preceding status")
                r.pos -= 1
                status = running
            if status < 0xF0:
                running = status

            kind, chan = status & 0xF0, status & 0x0F

            if status == 0xFF:                # meta
                meta = r.byte()
                n = r.varlen()
                payload = r.take(n)
                if meta == 0x51 and n == 3:
                    tempos.append((tick, int.from_bytes(payload, "big")))
                elif meta == 0x03:
                    track_names.append(payload.decode("latin-1", "replace").strip())
                elif meta == 0x58 and n >= 2:
                    time_sigs.add(f"{payload[0]}/{2 ** payload[1]}")
                elif meta == 0x59 and n >= 2:
                    sharps = struct.unpack("b", payload[0:1])[0]
                    key_sigs.add(f"{sharps:+d} {'minor' if payload[1] else 'major'}")
            elif status in (0xF0, 0xF7):      # sysex
                r.pos += r.varlen()
            elif kind in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                a, b = r.byte(), r.byte()
                channels_used.add(chan)
                if kind == 0x90 and b > 0:
                    note_count += 1
                    open_notes[(chan, a)] = open_notes.get((chan, a), 0) + 1
                elif kind == 0x80 or (kind == 0x90 and b == 0):
                    key = (chan, a)
                    if open_notes.get(key):
                        open_notes[key] -= 1
            elif kind in (0xC0, 0xD0):
                a = r.byte()
                channels_used.add(chan)
                if kind == 0xC0:
                    programs.setdefault(chan, set()).add(a)
            else:
                raise ValueError(f"unknown status 0x{status:02X} at {r.pos}")

        hanging += sum(open_notes.values())
        end_tick = max(end_tick, tick)
        r.pos = stop

    # Walk the tempo map to turn ticks into seconds.
    tempos.sort()
    seconds = 0.0
    prev_tick, current = 0, DEFAULT_TEMPO_US
    for t, us in tempos + [(end_tick, 0)]:
        t = min(t, end_tick)
        if t > prev_tick:
            seconds += (t - prev_tick) / division * current / 1_000_000
        if us:
            current = us
        prev_tick = t

    bpms = sorted({round(MICROSECONDS_PER_MINUTE / us, 1) for _, us in tempos}) or [120.0]
    return {
        "path": path,
        "bytes": len(data),
        "format": fmt,
        "tracks": ntracks,
        "division": division,
        "seconds": seconds,
        "bpm": bpms,
        "notes": note_count,
        "hanging": hanging,
        "channels": sorted(channels_used),
        "programs": programs,
        "percussion": PERCUSSION_CHANNEL in channels_used,
        "track_names": [n for n in track_names if n][:6],
        "key_sigs": sorted(key_sigs),
        "time_sigs": sorted(time_sigs),
    }


def describe(info: dict) -> str:
    progs = sorted({p for s in info["programs"].values() for p in s})
    if not progs:
        voices = "NO PROGRAM CHANGE -> every channel plays GM 0, acoustic grand piano"
    else:
        voices = ", ".join(f"{p} ({gm_family(p)})" for p in progs)
    m, s = divmod(info["seconds"], 60)
    return (
        f"{info['path'].name}\n"
        f"  {info['bytes']} bytes · SMF format {info['format']} · "
        f"{info['tracks']} tracks · {info['division']} ticks/beat\n"
        f"  length {int(m)}:{s:04.1f} · tempo {info['bpm']} BPM"
        f"{' (varies)' if len(info['bpm']) > 1 else ''}"
        f" · time {','.join(info['time_sigs']) or 'n/a'}\n"
        f"  {info['notes']} notes on channels {info['channels']}"
        f"{' · PERCUSSION present' if info['percussion'] else ' · no percussion channel'}\n"
        f"  voices: {voices}\n"
        f"  hanging notes: {info['hanging']}"
        f"{'  <-- PROBLEM' if info['hanging'] else ''}\n"
        + (f"  track names: {'; '.join(info['track_names'])}\n" if info["track_names"] else "")
    )


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]]
    if not paths:
        print(__doc__)
        return 2
    bad = 0
    for p in paths:
        try:
            print(describe(parse(p)))
        except Exception as exc:                       # noqa: BLE001 - report, keep going
            bad += 1
            print(f"{p.name}\n  UNREADABLE: {exc}\n")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
