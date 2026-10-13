#!/usr/bin/env python3
"""Mechanical, non-musical repairs to a Standard MIDI File we did not write.

    python3 tools/audio/midi_edit.py in.mid out.mid --trim-head
    python3 tools/audio/midi_edit.py in.mid out.mid --velocity 0.80
    python3 tools/audio/midi_edit.py in.mid out.mid --trim-head --velocity 0.9 --loop-tail 2

Why this exists
---------------
`midi_inspect.py` found two defects in the downloaded candidates that are
faults of the *file*, not of the music, and that a player would hear
immediately:

1. **Leading silence.** `WM_Internationale_orch2.mid` starts with ~2 s of
   absolute digital silence. Harmless once, a two-second hole every loop.
   `--trim-head` shifts every event earlier so the first note-on lands on
   tick 0; events that sat before it (tempo, key, time signature, program
   changes, controllers) collapse to tick 0 in their original order, which is
   exactly where a sequencer would have put them.
2. **Clipping.** Two Mutopia renders peak at or above full scale through
   GZDoom's soundfont, because LilyPond writes generous velocities and every
   channel is the same loud piano. `--velocity F` scales every note-on
   velocity by F (clamped 1..127), which lowers the synth's summed output
   without touching a single pitch or duration.

`--loop-tail BEATS` is the third mechanical knob: it pads the end so a loop
does not slam back to bar 1 on the last note's release.

What this tool deliberately does **not** do: assign instruments, change notes,
re-harmonise, or cut sections. Those are musical decisions and they live in a
card in `docs/sound/SOUNDTRACK.md`, not in a flag.

**Licence note.** Every edit here produces a *derivative* of the input
sequencing. That is permitted by all the candidate licences we accepted
(CC0, `{{Attribution}}`, PD, CC BY 3.0), and for the attribution ones the
obligation to credit the original sequencer survives the edit and is recorded
in `docs/sound/MUSIC-RIGHTS.md` §4.4. Output files are written next to the
input with an explicit name; the downloaded originals are never overwritten.

Python 3 standard library only. Reads and writes SMF format 0 and 1.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

META = 0xFF
SYSEX = (0xF0, 0xF7)
NOTE_ON = 0x90
VELOCITY_MIN = 1
VELOCITY_MAX = 127
TWO_BYTE_KINDS = (0x80, 0x90, 0xA0, 0xB0, 0xE0)
ONE_BYTE_KINDS = (0xC0, 0xD0)
META_END_OF_TRACK = 0x2F


class Reader:
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


def write_varlen(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative delta time")
    out = bytearray([value & 0x7F])
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def read_smf(data: bytes) -> tuple[int, int, list[list[tuple[int, bytes]]]]:
    """-> (format, division, tracks); each track is [(absolute tick, raw event bytes)].

    Events are kept as their complete byte sequence with an explicit status
    byte: running status is expanded on read and never re-emitted. The file
    grows by a few per cent and stops being a parsing puzzle.
    """
    r = Reader(data)
    if r.take(4) != b"MThd":
        raise ValueError("not a Standard MIDI File (no MThd)")
    header_len = struct.unpack(">I", r.take(4))[0]
    fmt, ntracks, division = struct.unpack(">HHH", r.take(6))
    r.pos += header_len - 6
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported")

    tracks: list[list[tuple[int, bytes]]] = []
    for _ in range(ntracks):
        if r.take(4) != b"MTrk":
            raise ValueError("expected MTrk")
        length = struct.unpack(">I", r.take(4))[0]
        stop = r.pos + length
        tick = 0
        running = None
        events: list[tuple[int, bytes]] = []
        while r.pos < stop:
            tick += r.varlen()
            status = r.byte()
            if status < 0x80:
                if running is None:
                    raise ValueError("running status with no preceding status")
                r.pos -= 1
                status = running
            if status < 0xF0:
                running = status
            if status == META:
                meta = r.byte()
                n = r.varlen()
                payload = r.take(n)
                raw = bytes([META, meta]) + write_varlen(n) + payload
            elif status in SYSEX:
                n = r.varlen()
                payload = r.take(n)
                raw = bytes([status]) + write_varlen(n) + payload
            else:
                kind = status & 0xF0
                if kind in TWO_BYTE_KINDS:
                    raw = bytes([status]) + r.take(2)
                elif kind in ONE_BYTE_KINDS:
                    raw = bytes([status]) + r.take(1)
                else:
                    raise ValueError(f"unknown status 0x{status:02X} at {r.pos}")
            events.append((tick, raw))
        r.pos = stop
        tracks.append(events)
    return fmt, division, tracks


def write_smf(fmt: int, division: int, tracks: list[list[tuple[int, bytes]]]) -> bytes:
    out = bytearray(b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), division))
    for events in tracks:
        body = bytearray()
        prev = 0
        for tick, raw in events:
            body += write_varlen(tick - prev)
            body += raw
            prev = tick
        out += b"MTrk" + struct.pack(">I", len(body)) + bytes(body)
    return bytes(out)


def first_note_tick(tracks: list[list[tuple[int, bytes]]]) -> int | None:
    best: int | None = None
    for events in tracks:
        for tick, raw in events:
            if raw[0] & 0xF0 == NOTE_ON and len(raw) == 3 and raw[2] > 0:
                best = tick if best is None else min(best, tick)
                break
    return best


def last_tick(tracks: list[list[tuple[int, bytes]]]) -> int:
    return max((events[-1][0] for events in tracks if events), default=0)


def trim_head(tracks: list[list[tuple[int, bytes]]], shift: int) -> None:
    for i, events in enumerate(tracks):
        tracks[i] = [(max(0, tick - shift), raw) for tick, raw in events]


def scale_velocity(tracks: list[list[tuple[int, bytes]]], factor: float) -> int:
    touched = 0
    for i, events in enumerate(tracks):
        new: list[tuple[int, bytes]] = []
        for tick, raw in events:
            if raw[0] & 0xF0 == NOTE_ON and len(raw) == 3 and raw[2] > 0:
                vel = max(VELOCITY_MIN, min(VELOCITY_MAX, round(raw[2] * factor)))
                raw = bytes([raw[0], raw[1], vel])
                touched += 1
            new.append((tick, raw))
        tracks[i] = new
    return touched


def pad_tail(tracks: list[list[tuple[int, bytes]]], ticks: int) -> None:
    """Push every End of Track meta event `ticks` later."""
    for i, events in enumerate(tracks):
        new: list[tuple[int, bytes]] = []
        for tick, raw in events:
            if raw[0] == META and len(raw) > 1 and raw[1] == META_END_OF_TRACK:
                tick += ticks
            new.append((tick, raw))
        tracks[i] = new


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", type=Path)
    p.add_argument("target", type=Path)
    p.add_argument("--trim-head", action="store_true",
                   help="shift every event so the first note-on is at tick 0")
    p.add_argument("--velocity", type=float, metavar="F",
                   help="scale every note-on velocity by F (0 < F <= 2)")
    p.add_argument("--loop-tail", type=float, default=0.0, metavar="BEATS",
                   help="add BEATS of silence after the last event")
    args = p.parse_args(argv)

    if args.velocity is not None and not 0 < args.velocity <= 2:
        p.error("--velocity must be in (0, 2]")
    if not (args.trim_head or args.velocity is not None or args.loop_tail):
        p.error("nothing to do: pass --trim-head, --velocity and/or --loop-tail")
    if args.source.resolve() == args.target.resolve():
        p.error("refusing to overwrite the source file in place")

    fmt, division, tracks = read_smf(args.source.read_bytes())
    before = args.source.stat().st_size
    report = []

    if args.trim_head:
        start = first_note_tick(tracks)
        if start is None:
            p.error("no note-on in the file: nothing to trim to")
        if start == 0:
            report.append("trim-head: first note already at tick 0, nothing shifted")
        else:
            trim_head(tracks, start)
            report.append(f"trim-head: shifted everything {start} ticks earlier "
                          f"({start / division:.2f} beats of silence removed)")
    if args.velocity is not None:
        n = scale_velocity(tracks, args.velocity)
        report.append(f"velocity: {n} note-ons scaled by {args.velocity}")
    if args.loop_tail:
        ticks = round(args.loop_tail * division)
        pad_tail(tracks, ticks)
        report.append(f"loop-tail: +{ticks} ticks ({args.loop_tail} beats) before End of Track")

    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_bytes(write_smf(fmt, division, tracks))
    after = args.target.stat().st_size

    print(f"{args.source.name} -> {args.target}")
    for line in report:
        print(f"  {line}")
    print(f"  {before} B in, {after} B out, {len(tracks)} tracks, "
          f"{division} ticks/beat, last event at tick {last_tick(tracks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
