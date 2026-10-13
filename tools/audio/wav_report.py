#!/usr/bin/env python3
"""Measure what a rendered WAV actually sounds like, in numbers.

    python3 tools/audio/wav_report.py work/audio/render-candidates/*.wav
    .venv/bin/python tools/audio/wav_report.py work/audio/render/*.wav   # faster

Why this exists
---------------
A sound designer who cannot put headphones on still has to answer "does this
sound good". These are the five things that decide it for game music, and all
five are measurable on the engine's own render (`audition.py --render`, which
synthesises through the same FluidSynth + `gzdoom.sf2` the player will hear):

1. **Peak and clipping.** Anything at or over full scale distorts. GZDoom does
   not limit for us.
2. **Leading silence.** A loop that starts with a hole has a hole every time
   it restarts.
3. **Trailing silence.** Too little and the loop slams; too much and it gapes.
4. **The loudness arc** — RMS per twelfth of the piece, as a percentage of its
   own loudest twelfth. A flat arc is the measurable form of "a bit simple":
   nothing enters, nothing builds, nothing leaves.
5. **Brightness** (spectral centroid, via zero-crossing rate as a cheap
   stand-in). Solo piano through a GM soundfont sits in a narrow band; a real
   orchestration moves. Reported because the Mutopia files are score previews
   and this is the number that shows it.

It reports; it never changes a file. Use `midi_edit.py` to act on what it
finds.

NumPy is used when importable (the project's `.venv` has it) and the stdlib
fallback produces the same numbers more slowly.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

ARC_SLOTS = 12
SILENCE_FLOOR = 1e-4            # below this a sample is silence for our purposes
CLIP_THRESHOLD = 0.999          # at or above full scale
WAV_FORMAT_PCM = 0x0001
WAV_FORMAT_IEEE_FLOAT = 0x0003
WAV_FORMAT_EXTENSIBLE = 0xFFFE
WAV_EXTENSIBLE_SUBFORMAT_OFFSET = 24

try:
    import numpy as _np
except ImportError:                                    # pragma: no cover
    _np = None


def read_wav(path: Path):
    """-> (samples as a float sequence in -1..1, sample rate, channels).

    GZDoom's `writewave` emits WAVE_FORMAT_EXTENSIBLE / IEEE float, which the
    stdlib `wave` module refuses, so the RIFF chunks are walked by hand. Same
    reader as `audition.measure_wav`, kept separate because that module is the
    engine driver and this one is the analysis.
    """
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"{path} is not a RIFF/WAVE file")
    offset, fmt, data = 12, None, b""
    while offset + 8 <= len(raw):
        chunk_id = raw[offset:offset + 4]
        (size,) = struct.unpack("<I", raw[offset + 4:offset + 8])
        body = raw[offset + 8:offset + 8 + size]
        if chunk_id == b"fmt ":
            fmt = body
        elif chunk_id == b"data":
            data = body
        offset += 8 + size + (size & 1)
    if fmt is None or not data:
        raise ValueError(f"{path}: missing fmt or data chunk")

    tag, channels, rate, _br, _al, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == WAV_FORMAT_EXTENSIBLE and len(fmt) >= WAV_EXTENSIBLE_SUBFORMAT_OFFSET + 2:
        (tag,) = struct.unpack("<H", fmt[WAV_EXTENSIBLE_SUBFORMAT_OFFSET:
                                         WAV_EXTENSIBLE_SUBFORMAT_OFFSET + 2])
    if tag == WAV_FORMAT_IEEE_FLOAT and bits == 32:
        dtype, scale = "<f4", 1.0
    elif tag == WAV_FORMAT_PCM and bits == 16:
        dtype, scale = "<i2", 32768.0
    else:
        raise ValueError(f"{path}: unsupported format {tag:#06x}/{bits} bits")

    if _np is not None:
        arr = _np.frombuffer(data[: len(data) - len(data) % (bits // 8)], dtype=dtype)
        return arr.astype(_np.float32) / scale, rate, channels

    import array
    a = array.array("f" if dtype == "<f4" else "h")
    a.frombytes(data[: len(data) - len(data) % a.itemsize])
    return [s / scale for s in a], rate, channels


def report(path: Path) -> dict:
    samples, rate, channels = read_wav(path)
    frames = len(samples) // max(channels, 1)
    seconds = frames / rate if rate else 0.0

    if _np is not None:
        mono = samples.reshape(-1, channels).mean(axis=1) if channels > 1 else samples
        peak = float(_np.abs(mono).max()) if mono.size else 0.0
        clipped = int((_np.abs(samples) >= CLIP_THRESHOLD).sum())
        loud = _np.abs(mono) > SILENCE_FLOOR
        lead = int(_np.argmax(loud)) if loud.any() else mono.size
        tail = int(mono.size - 1 - _np.argmax(loud[::-1])) if loud.any() else 0
        body = mono[lead:tail + 1] if loud.any() else mono[:0]
        arc = []
        if body.size:
            edges = _np.linspace(0, body.size, ARC_SLOTS + 1).astype(int)
            arc = [float(_np.sqrt((body[a:b].astype(_np.float64) ** 2).mean()))
                   if b > a else 0.0 for a, b in zip(edges[:-1], edges[1:])]
        zcr = (float((_np.diff(_np.signbit(body)).sum()) / (body.size / rate))
               if body.size > 1 else 0.0)
        rms = float(_np.sqrt((body.astype(_np.float64) ** 2).mean())) if body.size else 0.0
    else:                                              # pragma: no cover
        mono = samples[::channels] if channels > 1 else samples
        peak = max((abs(s) for s in mono), default=0.0)
        clipped = sum(1 for s in samples if abs(s) >= CLIP_THRESHOLD)
        lead, tail = len(mono), 0
        for i, s in enumerate(mono):
            if abs(s) > SILENCE_FLOOR:
                lead = i
                break
        for i in range(len(mono) - 1, -1, -1):
            if abs(mono[i]) > SILENCE_FLOOR:
                tail = i
                break
        body = mono[lead:tail + 1]
        arc = []
        if body:
            step = len(body) / ARC_SLOTS
            for k in range(ARC_SLOTS):
                seg = body[int(k * step):int((k + 1) * step)] or [0.0]
                arc.append((sum(s * s for s in seg) / len(seg)) ** 0.5)
        rms = ((sum(s * s for s in body) / len(body)) ** 0.5) if body else 0.0
        crossings = sum(1 for a, b in zip(body, body[1:]) if (a < 0) != (b < 0))
        zcr = crossings / (len(body) / rate) if len(body) > 1 else 0.0

    top = max(arc) if arc else 0.0
    return {
        "name": path.stem,
        "seconds": seconds,
        "peak": peak,
        "rms": rms,
        "clipped": clipped,
        "lead_s": lead / rate if rate else 0.0,
        "tail_s": (frames - 1 - tail) / rate if rate and tail else 0.0,
        "arc": [round(100 * a / top) if top else 0 for a in arc],
        "arc_spread": (round(100 * (max(arc) - min(arc)) / top) if top else 0),
        "zcr": zcr,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("wavs", nargs="+", type=Path)
    p.add_argument("--csv", action="store_true", help="machine-readable, one row per file")
    args = p.parse_args(argv)

    rows = []
    for w in args.wavs:
        try:
            rows.append(report(w))
        except Exception as exc:                       # noqa: BLE001 - report, keep going
            print(f"{w.name}: UNREADABLE: {exc}", file=sys.stderr)
    if args.csv:
        print("lump,seconds,peak,rms,clipped,lead_s,tail_s,arc_spread,zcr,arc")
        for r in rows:
            print(f"{r['name']},{r['seconds']:.2f},{r['peak']:.4f},{r['rms']:.4f},"
                  f"{r['clipped']},{r['lead_s']:.3f},{r['tail_s']:.3f},"
                  f"{r['arc_spread']},{r['zcr']:.0f}," + " ".join(map(str, r["arc"])))
        return 0
    for r in rows:
        m, s = divmod(r["seconds"], 60)
        flag = "  <-- CLIPS" if r["clipped"] else ("  <-- at the ceiling" if r["peak"] > 0.95 else "")
        print(f"{r['name']}  {int(m)}:{s:04.1f}")
        print(f"  peak {r['peak']:.3f}  rms {r['rms']:.4f}  "
              f"clipped samples {r['clipped']}{flag}")
        print(f"  silence: {r['lead_s']:.2f} s at the head"
              f"{'  <-- a hole on every loop' if r['lead_s'] > 0.5 else ''}, "
              f"{r['tail_s']:.2f} s at the tail")
        print(f"  arc {' '.join(f'{a:3d}' for a in r['arc'])}  "
              f"(spread {r['arc_spread']} points)"
              f"{'  <-- flat, nothing happens' if r['arc_spread'] < 30 else ''}")
        print(f"  brightness {r['zcr']:.0f} zero-crossings/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
