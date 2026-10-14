#!/usr/bin/env python3
"""Build the DRAFT enemy sound effects: every bestiary lump that is not a voice.

    .venv/Scripts/python.exe tools/audio/gen_sfx.py              # 35 lumps + 8 beds -> work/audio/sfx/
    .venv/Scripts/python.exe tools/audio/gen_sfx.py --preview docs/art/previews/<stamp>_F5_enemy-sfx-drafts.html --stamp "..."
    .venv/Scripts/python.exe tools/audio/gen_sfx.py --only SDHNDSIT SDPZRSTP SDGENDTH-bed
    .venv/Scripts/python.exe tools/audio/gen_sfx.py --seed 7     # another take of the synthesis
    .venv/Scripts/python.exe tools/audio/gen_sfx.py --list       # the plan: lump, route, length
    .venv/Scripts/python.exe tools/audio/gen_sfx.py --report     # measure what is on disk

What it is
----------
`docs/sound/ENEMY-SOUNDS.md` lists 47 enemy lumps. Twelve are voices, which
are the CEO's and are postponed (D37); this script builds the other **35**,
each by the route the plan gives it:

* **B** - a CC0 pack (D36, `work/audio/sfx_sources/`), cut, re-pitched,
  filtered and always layered with our own synthesis (route C);
* **C** - our own synthesis, numpy only;
* **A** - Freedoom's `DSSLOP` (BSD-3, read from `iwads/freedoom2.wad`), edited
  and layered with our own thump, for the three gibs.

It also builds eight **beds** (`<LUMP>-bed`): the non-vocal layers the cards
of the voice lumps name - the Legion's squelch and falling carrier, the
gear and the collapse under a death, the General's mechanism failure. They
are not lumps and never go in the overlay; they wait for the CEO's takes.

Every lump records the files it read, with their SHA-256, so the provenance
column of ENEMY-SOUNDS.md is written from what the script really did and not
from memory. Nothing it writes goes to `src/` or `assets/`: the drafts are
for the CEO's ears, and only he approves (project rule).

Outputs (all under the gitignored `work/audio/sfx/`)
---------------------------------------------------
* `enemies/wav/<LUMP>.wav` - 16-bit PCM mono 44.1 kHz, the master;
* `enemies/<LUMP>.ogg`     - Vorbis mono, what GZDoom reads (MOD-SPEC 6.2:
  `src/sounds/<LUMP>.ogg`). Encoded by `ffmpeg` (libvorbis);
* `enemies/beds/<LUMP>-bed.ogg` (and `beds/wav/`) - the beds;
* `enemies/PROVENANCE.tsv` - file, route, every source file and its hash;
* `enemies/REPORT.txt`     - the measures table (length, peak, loudness, and
  the briefs as numbers: centroid, energy under 150/300 Hz, in 1-3 kHz, onset);
* `sd-enemy-sfx-draft.pk3` - an audition OVERLAY: `sounds/<LUMP>.ogg` plus a
  SNDINFO that points the 35 logical names of `src/lumps/SNDINFO` at the
  drafts. Loaded after `dist/sovietdoom.pk3` it replaces the Freedoom
  stand-ins; removed, everything is as it was;
* with `--preview`, one self-contained HTML page (every OGG embedded) for
  the CEO: what each file replaces, its card, its numbers, its sources.

Why 44.1 kHz and not the 22.05 kHz the plan first proposed (ENEMY-SOUNDS.md
6): Freedoom ships 11 and 22 kHz DMX lumps, but the cracks and metal rings
of the bestiary live above 8 kHz, and a mono OGG one second long costs ~10 KB
either way. GZDoom resamples on playback; the rate is a free choice.

Loudness
--------
Each lump is brought to a target *class* loudness (`LOUDNESS_DB`): weapon
fire and impacts loudest, creature voices a little under, idle sounds well
under, the Panzermensch footstep in between because it repeats. The measure
is a gated, roughly K-weighted RMS (`weighted_loudness_db`), an approximation
of LUFS good enough to keep 35 sounds in one family; it is NOT a certified
loudness meter. A look-ahead limiter then holds every peak at -1 dBFS (the
OGG encoder overshoots a little; the report decodes the OGG and checks).

Determinism
-----------
Every random number comes from `numpy.random.default_rng([seed, crc32(lump)])`,
so one lump's take does not change when another recipe is edited, and the
same seed gives the same samples, bit for bit, on the same machine.

Licence: the script GPL-3.0 with the code; its output CC BY-NC-SA 4.0 (D15),
with the CC0 and BSD-3 inputs credited in ENEMY-SOUNDS.md.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
import wave
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = PROJECT_ROOT / "work" / "audio" / "sfx_sources"   # D36 downloads
IWAD_PATH = PROJECT_ROOT / "iwads" / "freedoom2.wad"
SNDINFO_PATH = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"        # read only
PLAN_PATH = PROJECT_ROOT / "docs" / "sound" / "ENEMY-SOUNDS.md"  # read only here
OUT_ROOT = PROJECT_ROOT / "work" / "audio" / "sfx"               # never assets/
OUT_DIR = OUT_ROOT / "enemies"
WAV_DIR = OUT_DIR / "wav"
OVERLAY_PK3 = OUT_ROOT / "sd-enemy-sfx-draft.pk3"

# =========================================================================
# 1. Constants
# =========================================================================

SAMPLE_RATE = 44100
DEFAULT_SEED = 1977              # the year of the story (LORE.md); any int works
PCM_FULL_SCALE = 32767
CEILING_DBFS = -1.0              # peak ceiling; leaves room for Vorbis overshoot
CLIP_THRESHOLD = 0.999           # same threshold as tools/audio/wav_report.py
MAX_LIMIT_DB = 6.0               # never squash more than this to reach a target
OGG_QUALITY = 6                  # libvorbis -q:a, ~112 kbit/s stereo-equivalent
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # reproducible PK3, as audition.py does

# Gated loudness (section 3): 20 ms blocks, keep the ones within 20 dB of the
# loudest, average their power. The gate makes a 0.1 s crack and a 2 s death
# comparable, which a plain RMS over the whole file does not.
LOUDNESS_BLOCK_S = 0.020
LOUDNESS_GATE_DB = 20.0

# Target gated loudness per class, dBFS. Fire and impacts lead; voices sit
# 2 dB under so a fight stays readable; idle sounds are heard through doors
# and must not compete; the footstep repeats every See cycle (ENEMY-SOUNDS.md
# 5.6: "without fatigue").
LOUDNESS_DB = {
    "fire": -13.0,
    "impact": -13.0,
    "creature": -15.0,
    "gib": -15.0,
    "step": -17.0,
    "idle": -20.0,
    "bed": -18.0,       # a layer under a voice take: its final level is set in that mix
}

# The pack IDs of ENEMY-SOUNDS.md 2 -> where the files are.
PACK_DIRS = {
    "OGA-CRE1": "oga-cre1/extracted",
    "OGA-CRE2": "oga-cre2/extracted",
    "OGA-SNARL": "oga-snarl",
    "OGA-100": "oga-100/extracted",
    "KEN-IMP": "ken-imp/extracted/Audio",
}
FREEDOOM_PACK = "FD"
SYNTH_PACK = "SYN"

# The twelve voice lumps (route D, the CEO's, postponed by D37). Not built.
VOICE_LUMPS = (
    "SDRRIACT", "SDRRISIT", "SDRRIPAI", "SDRRIDTH",
    "SDLTRACT", "SDLTRSIT", "SDLTRPAI", "SDLTRDTH",
    "SDGENSIT", "SDGENSUM", "SDGENPAI", "SDGENDTH",
)


class SourceMissing(RuntimeError):
    """A pack file or the IWAD is not on this machine (CI never has them)."""


# =========================================================================
# 2. Sources: decode, hash, cache
# =========================================================================

@dataclass(frozen=True)
class SourceRef:
    pack: str          # OGA-CRE1 ... FD
    name: str          # file name inside the pack, or "freedoom2.wad:DSSLOP"
    sha256: str        # of the file as it sits on disk (FD: of the lump bytes)
    segment: str = ""  # which part was used, when not the whole file

    def cite(self) -> str:
        seg = f" [{self.segment}]" if self.segment else ""
        return f"{self.pack} {self.name}{seg} sha256:{self.sha256[:12]}"


_DECODED: dict[Path, np.ndarray] = {}
_HASHES: dict[Path, str] = {}


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def sha256_file(path: Path) -> str:
    if path not in _HASHES:
        _HASHES[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _HASHES[path]


def channels_of(path: Path) -> int:
    exe = shutil.which("ffprobe")
    if exe is None:
        raise SourceMissing("ffprobe is not on the PATH")
    out = subprocess.run([exe, "-v", "error", "-select_streams", "a:0", "-show_entries",
                          "stream=channels", "-of", "csv=p=0", str(path)],
                         capture_output=True, check=True, text=True).stdout
    return int(out.strip().splitlines()[0])


def decode(path: Path) -> np.ndarray:
    """Any file ffmpeg reads -> mono float64 at SAMPLE_RATE.

    Decoded in its own channel count and averaged here. Not ffmpeg's `-ac`:
    its stereo-to-mono downmix adds ~3 dB to correlated stereo (the packs'
    files came out over full scale) and its mono-to-stereo upmix takes 3 dB
    off, so either way the level would depend on the file's layout.
    """
    if path in _DECODED:
        return _DECODED[path]
    if not path.is_file():
        raise SourceMissing(f"source not found: {path}")
    exe = ffmpeg_path()
    if exe is None:
        raise SourceMissing("ffmpeg is not on the PATH")
    channels = channels_of(path)
    raw = subprocess.run(
        [exe, "-v", "error", "-i", str(path), "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, dtype="<f4").astype(np.float64).reshape(-1, channels)
    _DECODED[path] = frames.mean(axis=1)
    return _DECODED[path]


def wad_lump(wad: Path, lump: str) -> bytes:
    """Read one lump from a WAD's directory (no extraction to disk)."""
    if not wad.is_file():
        raise SourceMissing(f"IWAD not found: {wad}")
    data = wad.read_bytes()
    count, offset = struct.unpack("<II", data[4:12])
    for i in range(count):
        pos, size, raw_name = struct.unpack("<II8s", data[offset + 16 * i:offset + 16 * i + 16])
        if raw_name.rstrip(b"\0").decode("ascii", "replace") == lump:
            return data[pos:pos + size]
    raise SourceMissing(f"{lump} not in {wad}")


DMX_FORMAT = 3
DMX_HEADER = 8
DMX_PAD = 16       # the format pads the samples with 16 bytes on each side


def dmx_to_float(lump: bytes) -> tuple[np.ndarray, int]:
    """Doom's DMX digital sound (8-bit unsigned) -> (float -1..1, rate)."""
    fmt, rate, count = struct.unpack("<HHI", lump[:DMX_HEADER])
    if fmt != DMX_FORMAT:
        raise ValueError(f"not a DMX sound (format {fmt})")
    body = np.frombuffer(lump[DMX_HEADER + DMX_PAD:DMX_HEADER + count - DMX_PAD], dtype=np.uint8)
    return (body.astype(np.float64) - 128.0) / 128.0, rate


# =========================================================================
# 3. DSP: filters, envelopes, synthesis, loudness, limiter
# =========================================================================
# Filters are zero-phase and work in the frequency domain (one FFT, one
# multiply, one inverse): numpy has no IIR filter and a per-sample Python loop
# would make the test suite slow. The magnitude curves are Butterworth's.

FFT_PAD = 8192          # samples of zero padding so filter tails do not wrap


def n_of(seconds: float) -> int:
    return max(1, int(round(seconds * SAMPLE_RATE)))


def time_axis(n: int) -> np.ndarray:
    return np.arange(n) / SAMPLE_RATE


def spectral(x: np.ndarray, gain: Callable[[np.ndarray], np.ndarray], pad: int = FFT_PAD) -> np.ndarray:
    if x.size == 0:
        return x
    nfft = x.size + pad
    freqs = np.fft.rfftfreq(nfft, 1.0 / SAMPLE_RATE)
    return np.fft.irfft(np.fft.rfft(x, nfft) * gain(freqs), nfft)[:x.size]


def _lp_mag(f, fc, order):
    return 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order))


def _hp_mag(f, fc, order):
    with np.errstate(divide="ignore"):
        return np.where(f > 0, 1.0 / np.sqrt(1.0 + (fc / np.maximum(f, 1e-9)) ** (2 * order)), 0.0)


def lowpass(x, fc, order=2):
    return spectral(x, lambda f: _lp_mag(f, fc, order))


def highpass(x, fc, order=2):
    return spectral(x, lambda f: _hp_mag(f, fc, order))


def bandpass(x, lo, hi, order=2):
    return spectral(x, lambda f: _hp_mag(f, lo, order) * _lp_mag(f, hi, order))


def _peak_mag(f, f0, gain_db, width_oct):
    with np.errstate(divide="ignore"):
        octs = np.log2(np.maximum(f, 1.0) / f0)
    return 10 ** (gain_db * np.exp(-0.5 * (octs / width_oct) ** 2) / 20)


def peak_eq(x, f0, gain_db, width_oct=0.5):
    """Bell boost/cut, Gaussian in log-frequency."""
    return spectral(x, lambda f: _peak_mag(f, f0, gain_db, width_oct))


def comb(x, delay_s, feedback, tail_s=0.3):
    """Feedback comb y[n] = x[n] + g*y[n-D]: the resonance of a tube or bowl."""
    tail = n_of(tail_s)
    padded = np.concatenate([x, np.zeros(tail)])
    nfft = padded.size + FFT_PAD
    freqs = np.fft.rfftfreq(nfft, 1.0 / SAMPLE_RATE)
    h = 1.0 / (1.0 - feedback * np.exp(-2j * np.pi * freqs * delay_s))
    return np.fft.irfft(np.fft.rfft(padded, nfft) * h, nfft)[:padded.size] * (1.0 - feedback)


def convolve(a, b):
    n = a.size + b.size - 1
    return np.fft.irfft(np.fft.rfft(a, n) * np.fft.rfft(b, n), n)


def reverb(x, rng, rt60=0.6, wet_db=-14.0, lp_hz=5000.0):
    """A small synthetic room: exponentially decaying noise as the impulse
    response. Dry signal untouched; wet added at `wet_db`."""
    n = n_of(rt60)
    ir = rng.standard_normal(n) * np.exp(-6.9 * time_axis(n) / rt60)
    ir = lowpass(ir, lp_hz, 1)
    ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    wet = convolve(x, ir)
    out = np.concatenate([x, np.zeros(wet.size - x.size)])
    return out + wet * db(wet_db)


def tv_filter(x, gain_at: Callable[[np.ndarray, float], np.ndarray], frame=2048, hop=512):
    """Time-varying spectral gain by short-time Fourier overlap-add.
    `gain_at(freqs, t)` returns the magnitude for the frame centred at t."""
    window = np.hanning(frame)
    padded = np.concatenate([np.zeros(frame), x, np.zeros(frame)])
    out = np.zeros(padded.size)
    norm = np.zeros(padded.size)
    freqs = np.fft.rfftfreq(frame, 1.0 / SAMPLE_RATE)
    for start in range(0, padded.size - frame, hop):
        seg = padded[start:start + frame] * window
        t = (start + frame / 2 - frame) / SAMPLE_RATE
        out[start:start + frame] += np.fft.irfft(np.fft.rfft(seg) * gain_at(freqs, t), frame) * window
        norm[start:start + frame] += window ** 2
    return (out / np.maximum(norm, 1e-6))[frame:frame + x.size]


def sweep_band(x, f_start, f_end, width_oct=0.6):
    """Band-pass whose centre glides exponentially from f_start to f_end."""
    dur = max(x.size / SAMPLE_RATE, 1e-6)

    def gain(freqs, t):
        frac = min(max(t / dur, 0.0), 1.0)
        centre = f_start * (f_end / f_start) ** frac
        with np.errstate(divide="ignore"):
            octs = np.log2(np.maximum(freqs, 1.0) / centre)
        return np.exp(-0.5 * (octs / width_oct) ** 2)
    return tv_filter(x, gain)


def db(value_db):
    return 10.0 ** (value_db / 20.0)


def env_exp(n, tau_s, attack_s=0.0):
    t = time_axis(n)
    env = np.exp(-t / tau_s)
    if attack_s > 0:
        env *= np.clip(t / attack_s, 0.0, 1.0)
    return env


def env_points(n, points):
    """Piecewise-linear envelope through (seconds, level) points."""
    ts, vs = zip(*points)
    return np.interp(time_axis(n), ts, vs)


def fade(x, in_s=0.002, out_s=0.03):
    x = x.copy()
    a, b = min(n_of(in_s), x.size), min(n_of(out_s), x.size)
    x[:a] *= np.linspace(0.0, 1.0, a)
    x[x.size - b:] *= np.linspace(1.0, 0.0, b)
    return x


def tone(freq, n, phase=0.0):
    """Sine whose frequency may be an array (a glide)."""
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    return np.sin(phase + 2 * np.pi * np.cumsum(f) / SAMPLE_RATE)


def saw(freq, n):
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    phase = np.cumsum(f) / SAMPLE_RATE
    return 2.0 * (phase - np.floor(phase)) - 1.0


def glide(f0, f1, n):
    """Exponential frequency glide over n samples."""
    return f0 * (f1 / f0) ** np.linspace(0.0, 1.0, n)


def fm(carrier, ratio, index, n):
    """Two-operator FM; `carrier` and `index` may be arrays."""
    c = np.broadcast_to(np.asarray(carrier, dtype=np.float64), (n,))
    i = np.broadcast_to(np.asarray(index, dtype=np.float64), (n,))
    mod = np.sin(2 * np.pi * np.cumsum(c * ratio) / SAMPLE_RATE)
    return np.sin(2 * np.pi * np.cumsum(c) / SAMPLE_RATE + i * mod)


def ring(n, base, ratios, taus, gains_db):
    """Inharmonic partials with their own decays: struck metal."""
    t = time_axis(n)
    out = np.zeros(n)
    for r, tau, g in zip(ratios, taus, gains_db):
        out += db(g) * np.sin(2 * np.pi * base * r * t) * np.exp(-t / tau)
    return out


def thump(n, f0, f1, tau):
    """A falling sine with an exponential decay: the body of a hit."""
    return tone(glide(f0, f1, n), n) * env_exp(n, tau, attack_s=0.002)


def click(rng, length_s=0.003, lo=1500.0, hi=9000.0):
    n = n_of(length_s)
    return bandpass(rng.standard_normal(n) * np.hanning(n), lo, hi, 1)


def crackle(rng, dur_s, rate_start, rate_end, grain_s=0.002, lo=1500.0, hi=8000.0):
    """Sparks: a Poisson stream of tiny noise grains whose rate falls
    exponentially from rate_start to rate_end per second."""
    n = n_of(dur_s)
    out = np.zeros(n)
    g = n_of(grain_s)
    t = 0.0
    while t < dur_s:
        rate = rate_start * (rate_end / rate_start) ** (t / dur_s)
        t += rng.exponential(1.0 / rate)
        i = int(t * SAMPLE_RATE)
        if i + g >= n:
            break
        out[i:i + g] += rng.standard_normal(g) * np.hanning(g) * rng.uniform(0.2, 1.0)
    return bandpass(out, lo, hi, 2)


def saturate(x, drive=2.0):
    return np.tanh(drive * x) / np.tanh(drive)


def bitcrush(x, bits=8, hold=1):
    levels = 2 ** (bits - 1)
    y = np.round(x * levels) / levels
    if hold > 1:
        y = np.repeat(y[::hold], hold)[:x.size]
    return y


def stutter(x, at_s, slice_s, repeats):
    """Overwrite what follows `at_s` with `repeats` copies of one short slice:
    the digital glitch of HYBRID-GLITCH (ENEMY-SOUNDS.md 4)."""
    x = x.copy()
    a, length = n_of(at_s), n_of(slice_s)
    if a + length * repeats > x.size:
        return x
    piece = fade(x[a:a + length], 0.0005, 0.0005)
    for k in range(repeats):
        x[a + k * length:a + (k + 1) * length] = piece
    return x


def varispeed(x, semitones):
    """Tape-style pitch change: down is slower and longer, up shorter."""
    if semitones == 0 or x.size < 2:
        return x
    ratio = 2.0 ** (semitones / 12.0)
    if ratio > 1.0:   # speeding up: remove what would fold over Nyquist
        x = lowpass(x, 0.45 * SAMPLE_RATE / ratio, 4)
    pos = np.arange(0.0, x.size - 1, ratio)
    return np.interp(pos, np.arange(x.size), x)


def pitch_glide(x, st_start, st_end):
    """Varispeed whose amount slides from st_start to st_end semitones."""
    out_len_guess = int(x.size / 2 ** (min(st_start, st_end) / 12.0)) + 2
    st = np.linspace(st_start, st_end, out_len_guess)
    pos = np.concatenate([[0.0], np.cumsum(2.0 ** (st / 12.0))[:-1]])
    pos = pos[pos < x.size - 1]
    return np.interp(pos, np.arange(x.size), x)


def am(x, rate_hz, depth, shape=1.0):
    """Amplitude modulation; `shape` > 1 sharpens the pulses (purr, rattle)."""
    mod = 0.5 * (1 + np.sin(2 * np.pi * np.cumsum(np.broadcast_to(rate_hz, x.shape)) / SAMPLE_RATE))
    return x * (1 - depth + depth * mod ** shape)


def peak_normal(x):
    p = np.abs(x).max() if x.size else 0.0
    return x / p if p > 0 else x


def trim_silence(x, floor_db=-50.0, preroll_s=0.003):
    """Cut leading and trailing material below `floor_db` relative to peak."""
    if x.size == 0:
        return x
    loud = np.abs(x) > np.abs(x).max() * db(floor_db)
    if not loud.any():
        return x[:0]
    first = max(0, int(np.argmax(loud)) - n_of(preroll_s))
    last = x.size - int(np.argmax(loud[::-1]))
    return x[first:last]


def trim_tail(x, floor_db=-55.0):
    """trim_silence for the end only."""
    if x.size == 0:
        return x
    loud = np.abs(x) > np.abs(x).max() * db(floor_db)
    return x[:x.size - int(np.argmax(loud[::-1]))] if loud.any() else x[:0]


def from_onset(x, floor_db=-12.0):
    """Drop the lead-in before the signal first reaches `floor_db` below its
    peak (a slow-onset grunt used as a pain must answer the hit at once)."""
    if x.size == 0:
        return x
    loud = np.abs(x) > np.abs(x).max() * db(floor_db)
    return fade(x[max(0, int(np.argmax(loud)) - n_of(0.004)):], 0.003, 0.0)


def mix(*layers):
    """Sum (offset_s, signal, gain_db) layers into one buffer."""
    starts = [int(round(off * SAMPLE_RATE)) for off, _, _ in layers]
    out = np.zeros(max(a + sig.size for a, (_, sig, _) in zip(starts, layers)))
    for a, (_, sig, gain) in zip(starts, layers):
        out[a:a + sig.size] += sig * db(gain)
    return out


def weighted_loudness_db(x):
    """Gated, roughly K-weighted RMS in dBFS (see LOUDNESS_* above).
    Weighting: high-pass 60 Hz and a +4 dB shelf above ~1.5 kHz, which is
    the shape of ITU-R BS.1770's K filter, drawn freehand. Not LUFS."""
    if x.size == 0:
        return -120.0
    w = spectral(x, lambda f: _hp_mag(f, 60.0, 2) * (1.0 + (db(4.0) - 1.0) * _hp_mag(f, 1500.0, 1)))
    block = n_of(LOUDNESS_BLOCK_S)
    nblk = max(1, w.size // block)
    power = (w[:nblk * block].reshape(nblk, -1) ** 2).mean(axis=1) if w.size >= block else np.array([(w ** 2).mean()])
    power_db = 10 * np.log10(power + 1e-20)
    kept = power[power_db > power_db.max() - LOUDNESS_GATE_DB]
    return float(10 * np.log10(kept.mean() + 1e-20))


LIMITER_WINDOW_S = 0.008
LOUDNESS_PASSES = 4          # gain -> limit -> re-measure, at most this often
LOUDNESS_SETTLE_DB = 0.1     # close enough to the class target


def limit(x, ceiling):
    """Zero-phase look-ahead limiter that cannot exceed `ceiling`.

    needed[n] = the gain sample n needs. A running minimum over a centred
    window of radius R, then a moving average of radius R: every sample that
    enters the average at n came from a minimum whose window contained n, so
    the averaged gain is never above needed[n] (no overshoot, by construction),
    and it moves smoothly over ~2R (no click). Returns (y, max reduction dB).
    """
    mag = np.abs(x)
    needed = np.minimum(1.0, ceiling / np.maximum(mag, 1e-12))
    if needed.min() >= 1.0:
        return x, 0.0
    r = n_of(LIMITER_WINDOW_S / 2)
    padded = np.concatenate([np.ones(r), needed, np.ones(r)])
    mins = np.lib.stride_tricks.sliding_window_view(padded, 2 * r + 1).min(axis=1)
    mins_p = np.concatenate([np.ones(r), mins, np.ones(r)])
    csum = np.concatenate([[0.0], np.cumsum(mins_p)])
    smooth = (csum[2 * r + 1:] - csum[:-(2 * r + 1)]) / (2 * r + 1)
    gain = np.minimum(smooth, needed)      # float safety: never above what is needed
    return x * gain, float(-20 * np.log10(gain.min()))


@dataclass
class Finished:
    samples: np.ndarray
    loudness_db: float
    target_db: float
    limited_db: float


def finish(x, loud_class, keep_head=False):
    """Clean, trim, fade, normalise loudness to the class, limit to -1 dBFS.
    `keep_head` keeps a leading silence (a bed's offsets are its timing)."""
    x = highpass(np.asarray(x, dtype=np.float64), 25.0, 2)        # DC and rumble
    x = trim_tail(x, -55.0) if keep_head else trim_silence(x, -55.0)
    x = fade(x, 0.002, 0.03)
    target = LOUDNESS_DB[loud_class]
    ceiling = db(CEILING_DBFS)
    gain_db = target - weighted_loudness_db(x)
    over = 20 * np.log10(np.abs(x).max() * db(gain_db) / ceiling)
    if over > MAX_LIMIT_DB:                    # would need heavy squashing
        gain_db -= over - MAX_LIMIT_DB
    # The limiter takes loudness away from a transient-heavy sound; give it
    # back (a few passes), never past MAX_LIMIT_DB of reduction.
    src = x
    for _ in range(LOUDNESS_PASSES):
        x, reduction = limit(src * db(gain_db), ceiling)
        short = target - weighted_loudness_db(x)
        if short < LOUDNESS_SETTLE_DB or reduction >= MAX_LIMIT_DB:
            break
        gain_db += short
    peak = np.abs(x).max()
    if peak > ceiling:                         # numerically impossible; cheap to keep
        x *= ceiling / peak
    return Finished(x.astype(np.float64), weighted_loudness_db(x), target, reduction)


# =========================================================================
# 4. Recipes
# =========================================================================

@dataclass
class Ctx:
    lump: str
    seed: int
    sources_dir: Path = SOURCES_DIR
    iwad: Path = IWAD_PATH
    refs: list = field(default_factory=list)
    synth: bool = False

    def __post_init__(self):
        self.rng = np.random.default_rng([self.seed, zlib.crc32(self.lump.encode("ascii"))])

    def src(self, pack, name, start=None, end=None, st=0.0, trim=True):
        """A pack file (or a segment of it), trimmed, re-pitched by `st`
        semitones and peak-normalised. Records the provenance."""
        path = self.sources_dir / PACK_DIRS[pack] / name
        x = decode(path)
        segment = ""
        if start is not None or end is not None:
            a = n_of(start) if start else 0
            b = n_of(end) if end is not None else x.size
            x = x[a:b]
            segment = f"{start or 0:.2f}-{end:.2f} s" if end is not None else f"from {start:.2f} s"
        ref = SourceRef(pack, name, sha256_file(path), segment)
        if ref not in self.refs:
            self.refs.append(ref)
        if trim:
            x = trim_silence(x, -45.0)
        return peak_normal(varispeed(x, st))

    def freedoom(self, lump):
        raw = wad_lump(self.iwad, lump)
        ref = SourceRef(FREEDOOM_PACK, f"freedoom2.wad:{lump}", hashlib.sha256(raw).hexdigest())
        if ref not in self.refs:
            self.refs.append(ref)
        x, rate = dmx_to_float(raw)
        pos = np.arange(0.0, x.size - 1, rate / SAMPLE_RATE)
        up = np.interp(pos, np.arange(x.size), x)
        return peak_normal(lowpass(up, 0.45 * rate, 4))   # drop the imaging above the old Nyquist

    def noise(self, seconds):
        self.synth = True
        return self.rng.standard_normal(n_of(seconds))

    def syn(self):
        """Mark that the lump contains a LAYER of our own synthesis (route C).
        Called by what generates sound, never by what only processes it
        (filters, reverb, stutter): ENEMY-SOUNDS.md 2 wants every CC0 clip
        layered, and the PROVENANCE line "SYN" must mean exactly that."""
        self.synth = True
        return self.rng


@dataclass
class Recipe:
    lump: str
    route: str                 # as planned: "B+C", "C", "A+C" (and C+B where it moved)
    loud_class: str
    duration: tuple            # (min, max) seconds of the finished lump
    build: Callable[[Ctx], np.ndarray]
    brief: str


RECIPES: dict[str, Recipe] = {}


def recipe(lump, route, loud_class, duration, brief):
    def wrap(fn):
        RECIPES[lump] = Recipe(lump, route, loud_class, duration, fn, brief)
        return fn
    return wrap


# ---- shared pieces -------------------------------------------------------

def helmet(x):
    """HELMET-RESONANCE: a voice inside a steel bowl, ~400 Hz."""
    return 0.6 * x + comb(peak_eq(x, 410.0, 8.0, 0.35), 1 / 410.0, 0.6, 0.25)[:x.size] * 1.6


def plate_low(x):
    """PLATE-LOW's filter half (the pitch is done at the source)."""
    return lowpass(x, 3000.0, 2)


def glitch(ctx, x, at_s, slice_s=0.012, repeats=3, crush_from=None, crush_to=None):
    """HYBRID-GLITCH: one stutter and optionally a bit-crushed stretch.
    Processing, not a layer: it does not mark the lump as route C."""
    y = stutter(x, at_s, slice_s, repeats)
    if crush_from is not None:
        a, b = n_of(crush_from), min(n_of(crush_to), y.size)
        y[a:b] = bitcrush(y[a:b], 6, 4)
    return y


def servo(ctx, seconds, f0, f1, gain_db=0.0):
    """A small electric motor: two harmonics, stepped pitch, crushed."""
    rng = ctx.syn()
    n = n_of(seconds)
    f = glide(f0, f1, n)
    steps = np.floor(np.linspace(0, 12, n)) / 12.0          # 12 audible steps
    f = f0 * (f1 / f0) ** steps * (1 + 0.004 * rng.standard_normal(n).cumsum() / np.sqrt(n))
    sig = tone(f, n) + 0.4 * tone(2 * f, n) + 0.2 * saw(3 * f, n)
    return bitcrush(sig * env_points(n, [(0, 0), (0.02, 1), (seconds - 0.05, 0.8), (seconds, 0)]), 7, 3) * db(gain_db)


def relay_click(ctx, f_ping=1800.0):
    rng = ctx.syn()
    n = n_of(0.03)
    return mix((0, click(rng, 0.002, 2000, 9000), 0),
               (0, np.sin(2 * np.pi * f_ping * time_axis(n)) * env_exp(n, 0.006), -6))


# ---- 5.1 Reich rifleman --------------------------------------------------

@recipe("SDRRIATK", "C", "fire", (0.30, 0.60),
        "dry bolt-action crack, drier and higher than the TT-33, then the bolt")
def _rri_atk(ctx):
    rng = ctx.syn()
    crack = ctx.noise(0.2) * env_exp(n_of(0.2), 0.035, attack_s=0.008)
    crack = peak_eq(bandpass(crack, 1000, 5000, 2), 2800, 4.0, 0.6)
    snap = click(rng, 0.0015, 3000, 12000)
    body = thump(n_of(0.12), 190, 95, 0.03)
    bolt = mix((0, relay_click(ctx, 2400), 0), (0.075, relay_click(ctx, 2900), -3))
    return mix((0, crack, 0), (0, snap, -4), (0, body, -11), (0.30, bolt, -17))


@recipe("SDRRIXDT", "A+C", "gib", (0.80, 1.40),
        "a wet burst, no voice: Freedoom's slop plus our low thump")
def _rri_xdt(ctx):
    slop = ctx.freedoom("DSSLOP")
    ctx.syn()
    body = mix((0, thump(n_of(0.3), 85, 42, 0.09), 0),
               (0, lowpass(ctx.noise(0.15) * env_exp(n_of(0.15), 0.03), 300, 2), -3))
    return mix((0, slop, 0), (0, body, -5))


# ---- 5.2 Liberty Legion trooper -----------------------------------------

@recipe("SDLTRATK", "C", "fire", (0.50, 0.90),
        "a shotgun blast heavier and more metallic than the IZh, chrome ring on top")
def _ltr_atk(ctx):
    blast = ctx.noise(0.6) * env_exp(n_of(0.6), 0.09, attack_s=0.003)
    blast = bandpass(blast, 80, 6000, 2)
    boom = thump(n_of(0.5), 115, 58, 0.12)
    burst = ctx.noise(0.03) * np.hanning(n_of(0.03))
    chrome = comb(burst, 1 / 2200.0, 0.93, 0.45) + 0.7 * comb(burst, 1 / 3170.0, 0.9, 0.45)
    chrome = bandpass(chrome, 1500, 9000, 2)
    dry = mix((0, saturate(blast, 1.6), 0), (0, boom, -1), (0.004, peak_normal(chrome), -12))
    return reverb(dry, ctx.rng, 0.35, -17.0, 4000)


@recipe("SDLTRXDT", "A+C", "gib", (0.80, 1.40),
        "the rifleman's burst plus a crackle of radio static")
def _ltr_xdt(ctx):
    slop = ctx.freedoom("DSSLOP")
    ctx.syn()
    body = thump(n_of(0.3), 85, 42, 0.09)
    static = bandpass(ctx.noise(0.42), 400, 3200, 3)
    static = bitcrush(static / (np.abs(static).max() + 1e-9), 8, 5)     # 8 bit, ~8.8 kHz
    gate = (ctx.rng.random(static.size // 441 + 1) > 0.35).repeat(441)[:static.size]
    static = static * gate * env_points(static.size, [(0, 0.3), (0.05, 1), (0.36, 0.8), (0.42, 0)])
    squelch = bandpass(ctx.noise(0.06), 1500, 6000, 2) * env_exp(n_of(0.06), 0.015)
    return mix((0, slop, 0), (0, body, -6), (0.04, static, -9), (0.46, squelch, -12))


# ---- 5.3 Hybrid Stormtrooper -------------------------------------------

@recipe("SDSTOACT", "B+C", "idle", (0.80, 1.60),
        "low rasping breath and a faint servo tick")
def _sto_act(ctx):
    exhale = ctx.src("OGA-CRE1", "breath.ogg", st=-5)
    inhale = ctx.src("OGA-CRE2", "breath_02.ogg", st=-4)
    rasp = lambda x: bandpass(saturate(x, 3.0), 180, 3200, 2)          # noqa: E731
    tick = mix((0, relay_click(ctx, 1500), 0), (0.06, relay_click(ctx, 1500), -4),
               (0.1, servo(ctx, 0.14, 1400, 1750), -10))
    return lowpass(mix((0, rasp(exhale), 0), (0.62, rasp(inhale), -3), (0.34, tick, -20)), 5000, 2)


@recipe("SDSTOSIT", "B+C", "creature", (0.55, 1.00),
        "a rasp-snarl chopped by a digital stutter")
def _sto_sit(ctx):
    body = ctx.src("OGA-CRE1", "monster_06.ogg", st=-2)
    edge = ctx.src("OGA-CRE1", "alien_03.ogg", st=-3)
    voice = saturate(mix((0, body, 0), (0.02, edge, -4)), 1.8)
    # A rasp lives in the presence band, not the sub: the raw pair measured
    # 83 % of its energy under 300 Hz (centroid 314 Hz), a growl, not a rasp.
    voice = peak_eq(highpass(voice, 300.0, 2), 2600.0, 7.0, 0.7)
    voice = glitch(ctx, voice, 0.16, 0.012, 4, crush_from=0.30, crush_to=0.46)
    arm = servo(ctx, 0.30, 700, 1500)                   # the Legion arm answers the rasp
    return glitch(ctx, mix((0, voice, 0), (0.28, arm, -15)), 0.40, 0.008, 3)


@recipe("SDSTOMEL", "B+C", "creature", (0.30, 0.60),
        "a raking blow: metal scrape on flesh")
def _sto_mel(ctx):
    flesh = ctx.src("KEN-IMP", "impactPunch_medium_001.ogg")
    claws = ctx.src("KEN-IMP", "impactMetal_light_002.ogg")
    grit = am(ctx.noise(0.32), 85.0, 0.7, 3.0) * env_points(n_of(0.32), [(0, 0), (0.01, 1), (0.2, 0.6), (0.32, 0)])
    scrape = comb(sweep_band(grit, 4500, 1800, 0.5), 1 / 1300.0, 0.6, 0.05)[:grit.size]
    return mix((0, flesh, 0), (0.008, claws, -6), (0.0, scrape, -5))


@recipe("SDSTOMIS", "C", "fire", (0.40, 0.65),
        "a tearing, rising zap; not the Doughboy's, not the Panzermensch's")
def _sto_mis(ctx):
    rng = ctx.syn()
    n = n_of(0.5)
    f = glide(180, 1400, n) * (1 + 0.01 * rng.standard_normal(n))
    zap = bandpass(saw(f, n) + 0.5 * saw(f * 1.012, n), 300, 6000, 2)
    tear = bandpass(am(ctx.noise(0.5), glide(60, 130, n), 0.9, 4.0), 1500, 7000, 2)
    sig = bitcrush(peak_normal(zap) + 0.6 * peak_normal(tear), 8, 2)
    return sig * env_points(n, [(0, 0), (0.02, 1), (0.38, 0.9), (0.5, 0)])


@recipe("SDSTOEXP", "C", "impact", (0.30, 0.50),
        "a short crackle, no boom: a dodgeable bolt, not a rocket")
def _sto_exp(ctx):
    rng = ctx.syn()
    sparks = crackle(rng, 0.42, 450, 15, 0.002, 1500, 9000)
    sizzle = highpass(ctx.noise(0.3), 3000, 2) * env_exp(n_of(0.3), 0.07, attack_s=0.002)
    pop = click(rng, 0.004, 800, 6000)
    return highpass(mix((0, peak_normal(sparks), 0), (0, sizzle, -9), (0, pop, -3)), 300, 3)


@recipe("SDSTOPAI", "B+C", "creature", (0.20, 0.50),
        "a rasp yelp with one glitch")
def _sto_pai(ctx):
    yelp = saturate(ctx.src("OGA-CRE1", "hurt_02.ogg", st=-1), 2.0)
    jerk = servo(ctx, 0.10, 1600, 900)                  # the arm jerks with the hit
    return glitch(ctx, mix((0, yelp, 0), (0.02, jerk, -16)), 0.08, 0.010, 3, crush_from=0.12, crush_to=0.2)


@recipe("SDSTODTH", "B+C", "creature", (0.90, 1.60),
        "the rasp collapses; a servo whine winds down")
def _sto_dth(ctx):
    rasp = saturate(ctx.src("OGA-CRE1", "monster_07.ogg", st=-2), 1.8)
    rasp = peak_eq(highpass(rasp, 140.0, 2), 2200.0, 5.0, 0.8)   # same reason as SDSTOSIT
    whine = servo(ctx, 1.05, 1800, 120) * env_points(n_of(1.05), [(0, 1), (0.8, 0.7), (1.05, 0)])
    return mix((0, rasp, 0), (0.18, whine, -11))


@recipe("SDSTOXDT", "A+C", "gib", (0.80, 1.40),
        "burst plus sparks")
def _sto_xdt(ctx):
    slop = ctx.freedoom("DSSLOP")
    rng = ctx.syn()
    body = thump(n_of(0.3), 85, 42, 0.09)
    sparks = peak_normal(crackle(rng, 0.65, 260, 6, 0.0015, 3000, 10000))
    zap = bandpass(saw(glide(2400, 600, n_of(0.08)), n_of(0.08)), 600, 8000, 1) * env_exp(n_of(0.08), 0.03)
    return mix((0, slop, 0), (0, body, -6), (0.03, sparks, -7), (0.02, zap, -14))


# ---- 5.4 Reich hound -----------------------------------------------------

@recipe("SDHNDACT", "B+C", "idle", (0.80, 1.50),
        "wet, rhythmic panting under a low purr; not a dog")
def _hnd_act(ctx):
    pants = []
    for k, (name, st) in enumerate([("breath_02.ogg", -2), ("breath.ogg", -1), ("breath_02.ogg", -3)]):
        pack = "OGA-CRE2" if name == "breath_02.ogg" else "OGA-CRE1"
        x = ctx.src(pack, name, st=st + ctx.rng.uniform(-0.4, 0.4))
        pants.append((0.36 * k, bandpass(x, 250, 4500, 1), -1.5 * k))
    n = n_of(1.2)
    purr = am(lowpass(ctx.noise(1.2), 380, 3), 24.0, 0.85, 3.0) + 0.5 * am(tone(46, n), 24.0, 0.9, 3.0)
    purr *= env_points(n, [(0, 0), (0.15, 1), (1.0, 1), (1.2, 0)])
    return mix(*pants, (0, purr, -9))


@recipe("SDHNDSIT", "B+C", "creature", (1.00, 1.60),
        "the most important sound: a rising snarl-shriek with an un-animal metallic edge")
def _hnd_sit(ctx):
    # From 12.85 s the snarl reaches full level ~0.2 s in (the brief's ~0.3 s
    # attack); from 12.55 s, as first cut, it took 0.5 s.
    snarl = ctx.src("OGA-SNARL", "monster-snarl-attack.ogg", start=12.85, end=13.95, trim=False)
    shriek = ctx.src("OGA-CRE2", "alien_07.ogg", st=4)
    rng = ctx.syn()
    n = n_of(1.3)
    edge = fm(glide(1700, 2350, n), 1.41, env_points(n, [(0, 0.5), (0.4, 2.5), (1.3, 1.2)]), n)
    edge *= env_points(n, [(0, 0), (0.3, 1), (1.0, 0.8), (1.3, 0)]) * (1 + 0.05 * rng.standard_normal(n))
    sig = mix((0, snarl, 0), (0.28, shriek, -7), (0.05, edge, -15))
    # Strong 1-3 kHz: what carries through a door. A wide bell plus a gentle
    # high-pass, so the band holds at least half of the energy.
    sig = peak_eq(highpass(sig, 600.0, 1), 1900, 8.0, 0.9)
    rise = env_points(sig.size, [(0, 0.35), (0.25, 1.0), (10, 1.0)])
    return sig * rise


@recipe("SDHNDATK", "B+C", "creature", (0.30, 0.50),
        "jaw snap and wet crunch")
def _hnd_atk(ctx):
    rng = ctx.syn()
    teeth = mix((0, click(rng, 0.003, 2000, 12000), 0),
                (0, np.sin(2 * np.pi * 3200 * time_axis(n_of(0.03))) * env_exp(n_of(0.03), 0.008), -4))
    flesh = ctx.src("KEN-IMP", "impactPunch_heavy_002.ogg")
    wet = ctx.src("OGA-CRE1", "eat_02.ogg")
    crunch = peak_normal(crackle(rng, 0.14, 300, 40, 0.004, 800, 4000))
    return mix((0, teeth, 0), (0.028, teeth, -4), (0.02, flesh, -3), (0.04, wet, -6), (0.03, crunch, -10))


@recipe("SDHNDPAI", "B+C", "creature", (0.20, 0.45),
        "a short alien yelp")
def _hnd_pai(ctx):
    yelp = ctx.src("OGA-CRE2", "monster_10.ogg", st=3)
    n = n_of(0.25)
    edge = fm(glide(2100, 1600, n), 1.41, 1.5, n) * env_exp(n, 0.07, attack_s=0.01)
    ctx.syn()
    return mix((0, yelp, 0), (0.01, edge, -17))


@recipe("SDHNDDTH", "B+C", "creature", (0.90, 1.60),
        "a drawn-out rattle that collapses")
def _hnd_dth(ctx):
    first = ctx.src("OGA-CRE2", "die_03.ogg", st=-4)
    rattle = ctx.src("OGA-CRE2", "die_02.ogg", st=-6)
    rattle = am(rattle, 28.0, 0.7, 2.0)
    n = n_of(1.0)                                       # the idle purr, winding down
    purr = am(lowpass(ctx.noise(1.0), 380, 3), glide(24.0, 9.0, n), 0.85, 3.0)
    purr *= env_points(n, [(0, 0), (0.1, 1), (0.6, 0.5), (1.0, 0)])
    collapse = lowpass(mix((0, first, 0), (0.35, rattle, -4), (0.05, peak_normal(purr), -12)), 4000, 1)
    n = collapse.size
    return collapse * env_points(n, [(0, 1), (0.7 * n / SAMPLE_RATE, 0.9), (n / SAMPLE_RATE, 0.0)])


# ---- 5.5 Doughboy --------------------------------------------------------

@recipe("SDDGBACT", "C", "idle", (1.20, 1.80),
        "a low hollow drone with a slow wobble")
def _dgb_act(ctx):
    ctx.syn()
    n = n_of(1.5)
    wobble = 1 + 0.02 * np.sin(2 * np.pi * 0.7 * time_axis(n))
    drone = tone(55 * wobble, n) + db(-6) * tone(110 * wobble, n) + db(-12) * tone(165 * wobble, n)
    hollow = am(helmet(lowpass(ctx.noise(1.5), 900, 2)), 3.0, 0.5)
    # The 55 Hz drone alone does not exist on a laptop speaker; the bowl's
    # ~410 Hz ring is what tells the player a Doughboy is idling nearby.
    sig = mix((0, drone, 0), (0, peak_normal(hollow), -3))
    return sig * env_points(n, [(0, 0), (0.3, 1), (1.1, 1), (1.5, 0)])


@recipe("SDDGBSIT", "B+C", "creature", (0.70, 1.40),
        "a hollow wail, a voice in a bucket")
def _dgb_sit(ctx):
    wail = ctx.src("OGA-CRE1", "scream_02.ogg", st=-5)
    under = ctx.src("OGA-CRE1", "monster_03.ogg", st=-3)
    ctx.syn()
    n = n_of(0.9)                                       # a synthetic throat under the two
    throat = fm(glide(180, 120, n), 1.5, 2.0, n) * env_points(n, [(0, 0), (0.08, 1), (0.6, 0.7), (0.9, 0)])
    return helmet(mix((0, wail, 0), (0.03, under, -5), (0.02, throat, -12)))


@recipe("SDDGBMEL", "B+C", "creature", (0.35, 0.70),
        "a bite that clangs on the helmet")
def _dgb_mel(ctx):
    chomp = ctx.src("OGA-CRE1", "eat_02.ogg")
    clang = ctx.src("KEN-IMP", "impactMetal_heavy_001.ogg", st=-3)
    ctx.syn()
    bowl = ring(n_of(0.45), 410.0, (1.0, 2.32, 4.1), (0.22, 0.12, 0.06), (0, -6, -12))
    return mix((0, chomp, 0), (0.035, clang, -3), (0.035, bowl, -12))


@recipe("SDDGBMIS", "B+C", "fire", (0.55, 0.90),
        "a wet electric spit, lower, longer and wetter than the Stormtrooper's zap")
def _dgb_mis(ctx):
    spit = ctx.src("OGA-CRE1", "spit_02.ogg", st=-4)
    rng = ctx.syn()
    n = n_of(0.55)
    f = glide(420, 150, n) * (1 + 0.01 * rng.standard_normal(n))
    zap = am(bandpass(saw(f, n), 200, 3000, 2), 50.0, 0.6) * env_points(n, [(0, 0), (0.03, 1), (0.4, 0.7), (0.55, 0)])
    return mix((0, spit, 0), (0.02, bitcrush(peak_normal(zap), 7, 2), -8))


@recipe("SDDGBEXP", "C+B", "impact", (0.45, 0.80),
        "a heavier splat with a flash (moved from C to C+B: the slime layer)")
def _dgb_exp(ctx):
    slime = ctx.src("OGA-CRE2", "slime_07.ogg", st=-4)
    ctx.syn()
    body = lowpass(ctx.noise(0.5), 1200, 2) * env_exp(n_of(0.5), 0.11, attack_s=0.004)
    thud = thump(n_of(0.4), 95, 45, 0.1)
    n = n_of(0.07)
    flash = bitcrush(tone(glide(3000, 800, n), n) * env_exp(n, 0.025), 6, 2)
    return mix((0, body, 0), (0, thud, -3), (0.015, slime, -2), (0, flash, -12))


@recipe("SDDGBPAI", "B+C", "creature", (0.30, 0.60),
        "a lowered hollow cry")
def _dgb_pai(ctx):
    cry = ctx.src("OGA-CRE1", "hurt_05.ogg", st=-4)
    ctx.syn()
    n = n_of(0.3)
    throat = fm(glide(200, 140, n), 1.5, 1.5, n) * env_exp(n, 0.1, attack_s=0.01)
    return helmet(mix((0, cry, 0), (0.01, throat, -12)))


@recipe("SDDGBDTH", "C", "creature", (1.60, 2.40),
        "deflate and sink: air escaping, falling pitch, a soft thud")
def _dgb_dth(ctx):
    ctx.syn()
    n = n_of(1.8)
    air = sweep_band(ctx.noise(1.8), 2500, 300, 0.7) * env_points(n, [(0, 0), (0.05, 1), (1.3, 0.7), (1.8, 0)])
    carrier = glide(220, 70, n)
    voice = fm(carrier, 1.5, glide(3.0, 0.5, n), n)
    voice = am(voice, glide(18, 6, n), 0.6, 2.0) * env_points(n, [(0, 0), (0.1, 1), (1.5, 0.5), (1.8, 0)])
    voice = helmet(voice)
    fall = mix((0, thump(n_of(0.35), 70, 40, 0.08), 0),
               (0, lowpass(ctx.noise(0.08) * env_exp(n_of(0.08), 0.015), 600, 2), -6))
    return mix((0, peak_normal(air), -2), (0, peak_normal(voice), -4), (1.82, fall, -1))


# ---- 5.6 Panzermensch ----------------------------------------------------

def stick_slip(ctx, seconds, rate0, rate1, freqs=(700.0, 1300.0)):
    """A creak: friction as a train of tiny resonant pings whose rate rises
    and falls (stick-slip)."""
    rng = ctx.syn()
    n = n_of(seconds)
    out = np.zeros(n)
    t = 0.0
    while t < seconds:
        frac = t / seconds
        rate = rate0 + (rate1 - rate0) * np.sin(np.pi * frac)
        t += 1.0 / rate * rng.uniform(0.7, 1.3)
        i = int(t * SAMPLE_RATE)
        if i >= n:
            break
        out[i] += rng.uniform(0.4, 1.0)
    m = n_of(0.02)
    ping = sum(np.sin(2 * np.pi * f * time_axis(m)) for f in freqs) * env_exp(m, 0.004)
    return np.convolve(out, ping)[:n]


@recipe("SDPZRACT", "B+C", "idle", (1.00, 2.00),
        "heavy breath through plate, an armour creak")
def _pzr_act(ctx):
    exhale = plate_low(ctx.src("OGA-CRE1", "breath.ogg", st=-5))
    inhale = plate_low(ctx.src("OGA-CRE2", "breath_02.ogg", st=-6))
    plate = ctx.src("KEN-IMP", "impactPlate_light_001.ogg", st=-7)
    creak = peak_normal(stick_slip(ctx, 0.35, 30, 85))
    return mix((0, exhale, 0), (0.85, inhale, -2), (0.5, plate, -14), (0.45, creak, -13))


@recipe("SDPZRSIT", "B+C", "creature", (1.20, 2.00),
        "a low roar with an armour clank")
def _pzr_sit(ctx):
    roar = ctx.src("OGA-CRE2", "roar_05.ogg", st=-5)
    roar2 = ctx.src("OGA-CRE1", "roar_02.ogg", st=-5)
    clank = ctx.src("KEN-IMP", "impactPlate_heavy_001.ogg", st=-3)
    clank2 = ctx.src("KEN-IMP", "impactMetal_heavy_003.ogg", st=-5)
    ctx.syn()
    stomp = thump(n_of(0.4), 60, 38, 0.1)               # he plants a foot to roar
    dry = plate_low(mix((0, roar, 0), (0.05, roar2, -5), (0, clank, -4), (0.12, clank2, -8), (0, stomp, -6)))
    return reverb(dry, ctx.rng, 0.5, -16.0, 3000)


@recipe("SDPZRMEL", "B+C", "creature", (0.40, 0.80),
        "a slam: fist on flesh and plate")
def _pzr_mel(ctx):
    fist = ctx.src("KEN-IMP", "impactPunch_heavy_000.ogg", st=-2)
    plate = ctx.src("KEN-IMP", "impactPlate_heavy_003.ogg", st=-4)
    ctx.syn()
    sub = thump(n_of(0.5), 62, 40, 0.12)
    return mix((0, fist, 0), (0.005, plate, -3), (0, sub, -2))


@recipe("SDPZRMIS", "C", "fire", (0.65, 0.95),
        "heavier and slower than the Stormtrooper's bolt: a low lob")
def _pzr_mis(ctx):
    rng = ctx.syn()
    n = n_of(0.8)
    whoosh = sweep_band(ctx.noise(0.8), 300, 650, 0.8) * env_points(n, [(0, 0), (0.15, 1), (0.5, 0.8), (0.8, 0)])
    hum = lowpass(saw(glide(70, 110, n) * (1 + 0.005 * rng.standard_normal(n)), n), 900, 2)
    hum *= env_points(n, [(0, 0), (0.05, 1), (0.6, 0.6), (0.8, 0)])
    launch = mix((0, thump(n_of(0.3), 70, 48, 0.1), 0),
                 (0, lowpass(ctx.noise(0.2) * env_exp(n_of(0.2), 0.04), 400, 2), -4))
    return plate_low(mix((0, peak_normal(whoosh), 0), (0, peak_normal(hum), -6), (0, launch, -2)))


@recipe("SDPZREXP", "C", "impact", (0.65, 1.00),
        "a dull heavy boom")
def _pzr_exp(ctx):
    ctx.syn()
    n = n_of(0.8)
    body = lowpass(ctx.noise(0.8), 700, 2) * env_exp(n, 0.18, attack_s=0.005)
    sub = thump(n_of(0.8), 58, 34, 0.22)
    crunch = bandpass(ctx.noise(0.12), 800, 2500, 2) * env_exp(n_of(0.12), 0.04)
    dry = saturate(mix((0, peak_normal(body), 0), (0, sub, 0), (0, crunch, -10)), 1.5)
    wet = reverb(dry, ctx.rng, 0.5, -14.0, 1500)[:n_of(0.92)]
    return fade(wet, 0.0, 0.25)


@recipe("SDPZRPAI", "B+C", "creature", (0.30, 0.60),
        "a low grunt")
def _pzr_pai(ctx):
    grunt = plate_low(ctx.src("OGA-CRE2", "grunt_09.ogg", st=-5))
    grunt = from_onset(grunt, -7.0)[:n_of(0.55)]      # pain answers the hit at once
    ctx.syn()
    jolt = ring(n_of(0.15), 640.0, (1.0, 2.31, 3.9), (0.05, 0.03, 0.02), (0, -5, -9))   # the plates jolt
    return fade(mix((0, grunt, 0), (0, jolt, -16)), 0.002, 0.12)


@recipe("SDPZRDTH", "B+C", "creature", (1.50, 2.50),
        "a roar sliding into a plate-crash")
def _pzr_dth(ctx):
    die = ctx.src("OGA-CRE2", "die_04.ogg", st=-6)     # die_03 is the hound's death
    roar = peak_normal(pitch_glide(ctx.src("OGA-CRE2", "roar_04.ogg"), -4, -9))
    crash1 = ctx.src("KEN-IMP", "impactPlate_heavy_004.ogg", st=-4)
    crash2 = ctx.src("KEN-IMP", "impactMetal_heavy_001.ogg", st=-6)
    fall = ctx.src("KEN-IMP", "impactPunch_heavy_002.ogg", st=-2)
    settle = ctx.src("KEN-IMP", "impactPlate_heavy_002.ogg", st=-6)
    ctx.syn()
    floor = thump(n_of(0.5), 55, 32, 0.13)              # 1000 kg of him meets the floor
    dry = plate_low(mix((0, roar, -3), (0, die, 0), (1.05, fall, -2), (1.05, crash1, -1),
                        (1.08, crash2, -5), (1.36, settle, -8), (1.05, floor, -3)))
    return reverb(lowpass(dry, 3500, 2), ctx.rng, 0.8, -14.0, 2500)


@recipe("SDPZRSTP", "C", "step", (0.25, 0.50),
        "one heavy plated footfall, mostly under 300 Hz, short and dry")
def _pzr_stp(ctx):
    rng = ctx.syn()
    body = thump(n_of(0.35), 72, 50, 0.07)
    weight = lowpass(ctx.noise(0.12) * env_exp(n_of(0.12), 0.03, attack_s=0.002), 250, 3)
    heel = click(rng, 0.002, 1000, 4000)
    clink = ring(n_of(0.1), 1100.0, (1.0, 1.573), (0.03, 0.02), (0, -3))
    # Heel and clink are what a small speaker plays; the body stays under 300 Hz.
    return mix((0, body, 0), (0, peak_normal(weight), -4), (0, heel, -14), (0.004, clink, -17))


# ---- 5.7 The General -----------------------------------------------------

@recipe("SDGENACT", "C", "idle", (1.60, 2.40),
        "a slow, measured mechanism hum with an occasional click; no voice")
def _gen_act(ctx):
    ctx.syn()
    n = n_of(2.0)
    hum = lowpass(saw(98, n), 600, 2) + db(-10) * tone(196, n)
    hum = am(hum, 0.5, 0.2)
    sig = mix((0, peak_normal(hum), 0),
              (0.55, relay_click(ctx, 1800), -10),
              (1.38, relay_click(ctx, 1650), -11), (1.43, relay_click(ctx, 1650), -14),
              (0.95, servo(ctx, 0.25, 900, 1100), -24))
    return sig * env_points(sig.size, [(0, 0), (0.2, 1), (1.7, 1), (2.0, 0)])


@recipe("SDGENMIS", "C+B", "fire", (0.45, 0.80),
        "one shell of the salvo: the heaviest launch, bright metal")
def _gen_mis(ctx):
    ctx.syn()
    blast = bandpass(ctx.noise(0.4), 150, 9000, 2) * env_exp(n_of(0.4), 0.07, attack_s=0.002)
    boom = thump(n_of(0.4), 90, 45, 0.09)
    bright = ring(n_of(0.5), 620.0, (1.0, 2.76, 5.40, 8.93), (0.25, 0.18, 0.12, 0.08), (0, -2, -5, -8))
    metal = ctx.src("KEN-IMP", "impactMetal_heavy_001.ogg", st=-2)
    trail = sweep_band(ctx.noise(0.4), 3000, 1200, 0.7) * env_points(n_of(0.4), [(0, 0), (0.05, 1), (0.4, 0)])
    return mix((0, saturate(blast, 1.4), 0), (0, boom, -2), (0.002, bright, -11),
               (0, metal, -6), (0.05, peak_normal(trail), -14))


@recipe("SDGENEXP", "C+B", "impact", (0.50, 0.90),
        "a bright metal burst")
def _gen_exp(ctx):
    rng = ctx.syn()
    burst = highpass(ctx.noise(0.6), 200, 2) * env_exp(n_of(0.6), 0.12, attack_s=0.002)
    sparks = peak_normal(crackle(rng, 0.45, 300, 10, 0.002, 2000, 8000))
    bright = ring(n_of(0.65), 840.0, (1.0, 2.76, 5.40), (0.35, 0.2, 0.1), (0, -3, -6))
    plate = ctx.src("KEN-IMP", "impactPlate_heavy_000.ogg")
    low = thump(n_of(0.35), 70, 45, 0.1)
    return mix((0, peak_normal(burst), 0), (0.01, sparks, -8), (0, bright, -12), (0, plate, -6), (0, low, -6))



# =========================================================================
# 4b. Beds: the non-vocal layers of the twelve voice lumps
# =========================================================================
# The voices are the CEO's and postponed (D37); until they arrive the
# rifleman, the trooper and the General keep Freedoom's voices. But four of
# their cards (ENEMY-SOUNDS.md 5.1, 5.2, 5.7) also name what is NOT a voice:
# the Legion's squelch and falling carrier, the General's mechanism failure,
# the collapse under a death. Those are built now as BEDS: files that are not
# lumps, never go in the overlay, and are mixed under the take when it comes.
# They start where the voice starts (no head trim), so the offsets inside
# them are the timing proposal: "the collapse lands 0.45 s after the voice".

BED_SUFFIX = "-bed"
BEDS: dict[str, Recipe] = {}


def bed(lump, route, duration, brief):
    if lump not in VOICE_LUMPS:
        raise ValueError(f"{lump} is not a voice lump: it needs a recipe, not a bed")

    def wrap(fn):
        BEDS[lump] = Recipe(lump, route, "bed", duration, fn, brief)
        return fn
    return wrap


def gear_rattle(ctx, seconds=0.18, pings=6, lo_hz=2300.0, hi_hz=4200.0):
    """Webbing, buckles and a sling swivel shaken once: small metal pings at
    random moments plus a cloth rustle."""
    rng = ctx.syn()
    n = n_of(seconds)
    out = np.zeros(n)
    m = n_of(0.05)
    for _ in range(pings):
        at = int(rng.uniform(0.0, 0.7) * n)
        f = rng.uniform(lo_hz, hi_hz)
        p = ring(m, f, (1.0, 1.51, 2.37), (0.012, 0.008, 0.005), (0, -5, -9)) * rng.uniform(0.3, 1.0)
        end = min(n, at + m)
        out[at:end] += p[:end - at]
    cloth = bandpass(ctx.noise(seconds), 400, 2500, 1) * env_points(n, [(0, 0), (0.01, 1), (seconds * 0.6, 0.4), (seconds, 0)])
    return mix((0, out, 0), (0, cloth, -14))


def body_fall(ctx, gain_db=0.0):
    """A body meeting a concrete floor: a low thud and a short cloth slap."""
    ctx.syn()
    thud = thump(n_of(0.35), 90, 45, 0.07)
    slap = lowpass(ctx.noise(0.09) * env_exp(n_of(0.09), 0.02, attack_s=0.002), 1200, 2)
    return mix((0, thud, 0), (0, peak_normal(slap), -5)) * db(gain_db)


def squelch(ctx, seconds=0.06, closing=False):
    """LEGION-RADIO's squelch burst (ENEMY-SOUNDS.md 4): 60 ms of filtered,
    crushed noise; the closing one ends in the click of the carrier dropping."""
    ctx.syn()
    n = n_of(seconds)
    hiss = bitcrush(peak_normal(bandpass(ctx.noise(seconds), 400, 3200, 3)), 8, 5)
    shape = env_points(n, [(0, 0.2), (0.008, 1), (seconds, 0.6)]) if not closing else \
        env_points(n, [(0, 0.6), (seconds - 0.006, 1), (seconds, 0)])
    sig = hiss * shape
    if closing:
        sig = mix((0, sig, 0), (seconds - 0.004, click(ctx.rng, 0.003, 800, 4000), -2))
    return sig


def carrier_hiss(ctx, seconds):
    """The open channel under the voice: band-limited, crushed, low."""
    n = n_of(seconds)
    hiss = bitcrush(peak_normal(bandpass(ctx.noise(seconds), 400, 3200, 2)), 8, 5)
    return hiss * env_points(n, [(0, 0), (0.02, 1), (seconds - 0.02, 1), (seconds, 0)])


@bed("SDRRIPAI", "C", (0.15, 0.40),
     "under the grunt: the webbing and the rifle jolt once")
def _rri_pai_bed(ctx):
    return gear_rattle(ctx, 0.20, 6)


@bed("SDRRIDTH", "C+B", (0.90, 1.50),
     "under the exhale: the rifle clatters on concrete, the body falls, the helmet rings once")
def _rri_dth_bed(ctx):
    rifle1 = ctx.src("KEN-IMP", "impactWood_light_002.ogg", st=-1)
    rifle2 = ctx.src("KEN-IMP", "impactMetal_light_000.ogg", st=-2)
    helmet_hit = ctx.src("KEN-IMP", "impactTin_medium_001.ogg", st=-3)
    return mix((0.05, gear_rattle(ctx, 0.22, 5), -6),
               (0.45, body_fall(ctx), 0),
               (0.52, rifle1, -6), (0.60, rifle2, -9), (0.71, rifle1, -16),   # it bounces,
               (0.86, rifle2, -18), (0.97, rifle1, -24),                      # and settles
               (0.56, helmet_hit, -10))


@bed("SDLTRACT", "C", (1.20, 1.80),
     "the radio frame of the idle report: squelch opens, the channel hisses, squelch closes")
def _ltr_act_bed(ctx):
    return mix((0, squelch(ctx), 0), (0.05, carrier_hiss(ctx, 1.30), -16),
               (1.35, squelch(ctx, 0.07, closing=True), -2))


@bed("SDLTRSIT", "C", (0.45, 0.70),
     "the radio frame of the callout: a short open, a squelch tail")
def _ltr_sit_bed(ctx):
    return mix((0, squelch(ctx, 0.05), -2), (0.04, carrier_hiss(ctx, 0.42), -16),
               (0.46, squelch(ctx, 0.08, closing=True), 0))


@bed("SDLTRPAI", "C", (0.20, 0.45),
     "under the grunt: a burst of static and a gear jolt")
def _ltr_pai_bed(ctx):
    static = carrier_hiss(ctx, 0.22)
    gate = (ctx.rng.random(static.size // 220 + 1) > 0.4).repeat(220)[:static.size]
    return mix((0, static * gate, -4), (0.01, gear_rattle(ctx, 0.18, 4, 1800, 3300), -6))


@bed("SDLTRDTH", "C", (0.85, 1.60),
     "the signal dies: the carrier falls, the squelch clicks off, then the body and the gear")
def _ltr_dth_bed(ctx):
    rng = ctx.syn()
    n = n_of(0.6)
    f = glide(1400, 180, n) * (1 + 0.003 * rng.standard_normal(n))
    fall = bitcrush(bandpass(saw(f, n), 400, 3200, 2) * env_points(n, [(0, 0), (0.03, 1), (0.5, 0.6), (0.6, 0)]), 6, 6)
    return mix((0, squelch(ctx, 0.05), -4), (0.04, carrier_hiss(ctx, 0.62), -14),
               (0.05, peak_normal(fall), -6), (0.66, squelch(ctx, 0.05, closing=True), -2),
               (0.62, body_fall(ctx), -1), (0.66, gear_rattle(ctx, 0.25, 7), -6))


@bed("SDGENPAI", "C+B", (0.30, 0.60),
     "under the metallic grunt: a chrome plate struck, a servo jerks")
def _gen_pai_bed(ctx):
    plate = ctx.src("KEN-IMP", "impactPlate_medium_002.ogg", st=-2)
    ctx.syn()
    chrome = ring(n_of(0.4), 840.0, (1.0, 2.76, 5.40), (0.15, 0.09, 0.05), (0, -4, -8))
    return mix((0, plate, 0), (0.002, chrome, -10), (0.04, servo(ctx, 0.12, 1300, 700), -12))


@bed("SDGENDTH", "C+B", (3.00, 4.20),
     "a cue, not an effect: the mechanism fails - servos wind down, relays chatter, sparks, the chrome falls and rings")
def _gen_dth_bed(ctx):
    rng = ctx.syn()
    wind = servo(ctx, 1.6, 1500, 70) * env_points(n_of(1.6), [(0, 1), (1.2, 0.8), (1.6, 0)])
    hum_n = n_of(1.9)
    hum = lowpass(saw(glide(98, 31, hum_n), hum_n), 600, 2) * env_points(hum_n, [(0, 1), (1.5, 0.6), (1.9, 0)])
    relays = [(t, relay_click(ctx, rng.uniform(1300, 2100)), rng.uniform(-14, -8))
              for t in np.sort(rng.uniform(0.15, 1.4, 9))]
    sparks = peak_normal(crackle(rng, 1.3, 140, 8, 0.002, 2000, 8000))
    fall = ctx.src("KEN-IMP", "impactPlate_heavy_002.ogg", st=-3)
    crash = ctx.src("KEN-IMP", "impactMetal_heavy_004.ogg", st=-4)
    tail = ring(n_of(2.2), 620.0, (1.0, 2.76, 5.40, 8.93), (1.1, 0.7, 0.4, 0.2), (0, -4, -8, -12))
    sig = mix((0, wind, -2), (0, peak_normal(hum), -8), *relays, (0.2, sparks, -16),
              (1.55, fall, 0), (1.58, crash, -4), (1.56, tail, -12),
              (1.56, thump(n_of(0.5), 70, 40, 0.14), -2))
    return reverb(sig, ctx.rng, 1.2, -16.0, 3500)

# =========================================================================
# 5. Render, write, encode, measure, pack
# =========================================================================

@dataclass
class Rendered:
    name: str                  # the lump, or "<LUMP>-bed" for a bed
    recipe: Recipe
    samples: np.ndarray        # float64, finished (-1 dBFS ceiling)
    refs: list
    synth: bool
    loudness_db: float
    limited_db: float

    @property
    def lump(self):
        return self.recipe.lump

    @property
    def is_bed(self):
        return self.name.endswith(BED_SUFFIX)

    @property
    def seconds(self):
        return self.samples.size / SAMPLE_RATE

    def provenance(self) -> list[str]:
        cites = [r.cite() for r in self.refs]
        if self.synth:
            cites.append("SYN gen_sfx.py")
        return cites


def all_names() -> list[str]:
    """Every buildable name: the 35 lumps, then the beds."""
    return list(RECIPES) + [f"{lump}{BED_SUFFIX}" for lump in BEDS]


def recipe_of(name: str) -> Recipe:
    if name.endswith(BED_SUFFIX):
        return BEDS[name[:-len(BED_SUFFIX)]]
    return RECIPES[name]


def normalise_name(token: str) -> str:
    """'sdrridth-bed' -> 'SDRRIDTH-bed', 'sdhndsit' -> 'SDHNDSIT'."""
    t = token.strip()
    if t.lower().endswith(BED_SUFFIX):
        return t[:-len(BED_SUFFIX)].upper() + BED_SUFFIX
    return t.upper()


def render(name, seed=DEFAULT_SEED, sources_dir=SOURCES_DIR, iwad=IWAD_PATH) -> Rendered:
    rec = recipe_of(name)
    ctx = Ctx(name, seed, sources_dir, iwad)
    raw = rec.build(ctx)
    done = finish(raw, rec.loud_class, keep_head=name.endswith(BED_SUFFIX))
    return Rendered(name, rec, done.samples, list(ctx.refs), ctx.synth, done.loudness_db, done.limited_db)


# ---- the briefs as numbers ----------------------------------------------
# What a card asks for in words ("mostly under 300 Hz", "strong 1-3 kHz", "no
# boom") measured on the finished samples. The report prints them and
# tests/test_gen_sfx.py holds the drafts to them. They are instruments, not
# ears: a sound can pass every one and still be wrong (nobody has listened).

FEATURE_BLOCK_S = 0.010
ONSET_DB = -6.0


def features(x: np.ndarray) -> dict:
    """centroid_hz; share of energy under 150 / 300 Hz and in 1-3 kHz;
    onset_s = time for the 10 ms RMS to first reach -6 dB of its maximum."""
    if x.size == 0:
        return {"centroid_hz": 0.0, "sub150": 0.0, "low300": 0.0, "mid1_3k": 0.0, "onset_s": 0.0}
    power = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(x.size, 1.0 / SAMPLE_RATE)
    total = power.sum() + 1e-20
    blk = n_of(FEATURE_BLOCK_S)
    nb = max(1, x.size // blk)
    if x.size >= blk:
        rms = np.sqrt((x[:nb * blk].reshape(nb, -1) ** 2).mean(axis=1))
    else:
        rms = np.array([np.abs(x).max()])
    onset = int(np.argmax(rms >= rms.max() * db(ONSET_DB))) * FEATURE_BLOCK_S
    return {
        "centroid_hz": float((power * f).sum() / total),
        "sub150": float(power[f < 150].sum() / total),
        "low300": float(power[f < 300].sum() / total),
        "mid1_3k": float(power[(f >= 1000) & (f < 3000)].sum() / total),
        "onset_s": float(onset),
    }


def to_pcm16(x: np.ndarray) -> np.ndarray:
    return np.clip(np.round(x * PCM_FULL_SCALE), -PCM_FULL_SCALE, PCM_FULL_SCALE).astype("<i2")


def write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(to_pcm16(x).tobytes())


def encode_ogg(wav: Path, ogg: Path) -> None:
    exe = ffmpeg_path()
    if exe is None:
        raise SourceMissing("ffmpeg is not on the PATH: cannot encode OGG")
    ogg.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, "-y", "-v", "error", "-i", str(wav), "-c:a", "libvorbis",
                    "-q:a", str(OGG_QUALITY), "-map_metadata", "-1",
                    "-fflags", "+bitexact", "-flags:a", "+bitexact", str(ogg)],
                   check=True)


SNDINFO_LINE = (r"^(?P<logical>sd/mon/\S+)\s+(?P<placeholder>\S+)\s*//\s*->\s*"
                r"(?P<lump>SD[A-Z0-9]{6})\b")


def sndinfo_rows(path: Path = SNDINFO_PATH) -> dict[str, tuple[str, str]]:
    """final lump -> (logical name, Freedoom stand-in), from src/lumps/SNDINFO."""
    import re
    rx = re.compile(SNDINFO_LINE)
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = rx.match(line.strip())
        if m:
            out[m.group("lump")] = (m.group("logical"), m.group("placeholder"))
    return out


def sndinfo_targets(path: Path = SNDINFO_PATH) -> dict[str, str]:
    """final lump -> logical name, from the comments of src/lumps/SNDINFO."""
    return {lump: row[0] for lump, row in sndinfo_rows(path).items()}


def overlay_sndinfo(lumps, targets) -> str:
    lines = [
        "// Audition overlay - tools/audio/gen_sfx.py. NOT part of the mod.",
        "// Loaded after dist/sovietdoom.pk3, so these definitions replace the",
        "// Freedoom stand-ins of src/lumps/SNDINFO for the logical names below.",
        "// DRAFTS for the CEO's ears (docs/sound/ENEMY-SOUNDS.md); nothing here is approved.",
        "// No voice (D37) and no bed is in it: the enemies keep Freedoom's voices.",
        "",
    ]
    width = max(len(targets[lump]) for lump in lumps)
    lines += [f"{targets[lump]:<{width}}  {lump}" for lump in lumps]
    return "\n".join(lines) + "\n"


def pack_overlay(lumps, ogg_dir=OUT_DIR, pk3=OVERLAY_PK3, sndinfo=SNDINFO_PATH) -> Path:
    lumps = [x for x in lumps if not x.endswith(BED_SUFFIX)]       # beds never ship
    targets = sndinfo_targets(sndinfo)
    missing = [lump for lump in lumps if lump not in targets]
    if missing:
        raise SystemExit(f"gen_sfx: no logical name in SNDINFO for {', '.join(missing)}")
    pk3.parent.mkdir(parents=True, exist_ok=True)
    entries = [("SNDINFO", overlay_sndinfo(lumps, targets).encode("ascii"))]
    entries += [(f"sounds/{lump}.ogg", (ogg_dir / f"{lump}.ogg").read_bytes()) for lump in lumps]
    with zipfile.ZipFile(pk3, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
    return pk3


def _wav_report():
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import wav_report                                   # same folder, reused as is
    return wav_report


def paths_of(name, out_dir=OUT_DIR):
    """(wav, ogg) for a lump or a bed."""
    if name.endswith(BED_SUFFIX):
        return out_dir / "beds" / "wav" / f"{name}.wav", out_dir / "beds" / f"{name}.ogg"
    return out_dir / "wav" / f"{name}.wav", out_dir / f"{name}.ogg"


def measure(name, out_dir=OUT_DIR) -> dict:
    """Numbers for one written file: wav_report's, loudness, the brief
    features, and the OGG's own decoded peak (Vorbis can overshoot)."""
    wav, ogg = paths_of(name, out_dir)
    wr = _wav_report()
    row = wr.report(wav)
    row["name"] = name
    samples, _rate, _ch = wr.read_wav(wav)
    x = np.asarray(samples, dtype=np.float64)
    row["loudness_db"] = weighted_loudness_db(x)
    row.update(features(x))
    if ogg.is_file() and ffmpeg_path():
        _DECODED.pop(ogg, None)
        dec = decode(ogg)
        _DECODED.pop(ogg, None)
        row["ogg_peak"] = float(np.abs(dec).max())
        row["ogg_bytes"] = ogg.stat().st_size
    return row


def dbfs(value):
    return 20 * np.log10(max(value, 1e-9))


def report_table(rows) -> str:
    head = ("| File | Route | Class | s | Peak dBFS | Loudness dB | Limited dB | OGG peak dBFS | "
            "OGG KB | Centroid Hz | <150 Hz | <300 Hz | 1-3 kHz | Onset s |")
    out = [head, "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        rec = recipe_of(r["name"])
        ogg_peak = f"{dbfs(r['ogg_peak']):.1f}" if "ogg_peak" in r else "-"
        out.append(
            f"| `{r['name']}` | {rec.route} | {rec.loud_class} | {r['seconds']:.2f} | "
            f"{dbfs(r['peak']):.1f} | {r['loudness_db']:.1f} | {r.get('limited_db', 0.0):.1f} | "
            f"{ogg_peak} | {r.get('ogg_bytes', 0) / 1024:.1f} | {r['centroid_hz']:.0f} | "
            f"{r['sub150']:.2f} | {r['low300']:.2f} | {r['mid1_3k']:.2f} | {r['onset_s']:.2f} |")
    return "\n".join(out) + "\n"


def write_provenance(rendered, path=OUT_DIR / "PROVENANCE.tsv") -> None:
    lines = ["file\troute\tpack\tsource\tsegment\tsha256"]
    for r in rendered:
        for ref in r.refs:
            lines.append(f"{r.name}\t{r.recipe.route}\t{ref.pack}\t{ref.name}\t{ref.segment}\t{ref.sha256}")
        if r.synth:
            lines.append(f"{r.name}\t{r.recipe.route}\t{SYNTH_PACK}\tgen_sfx.py\t\t")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(names, seed=DEFAULT_SEED, encode=True, pack=True, quiet=False,
          out_dir=OUT_DIR, pk3=OVERLAY_PK3):
    rendered = []
    for name in names:
        r = render(name, seed)
        lo, hi = r.recipe.duration
        flag = "" if lo <= r.seconds <= hi else f"  <-- OUT OF RANGE {lo:.2f}-{hi:.2f}"
        wav, ogg = paths_of(name, out_dir)
        write_wav(wav, r.samples)
        if encode:
            encode_ogg(wav, ogg)
        rendered.append(r)
        if not quiet:
            print(f"{name:<13} {r.recipe.route:<4} {r.seconds:5.2f} s  "
                  f"loud {r.loudness_db:6.1f} dB  limited {r.limited_db:4.1f} dB{flag}")
    write_provenance(rendered, out_dir / "PROVENANCE.tsv")
    if encode:
        rows = []
        for r in rendered:
            row = measure(r.name, out_dir)
            row["limited_db"] = r.limited_db
            rows.append(row)
        table = report_table(rows)
        (out_dir / "REPORT.txt").write_text(
            f"gen_sfx.py seed {seed}, {len(rows)} files, {SAMPLE_RATE} Hz mono, "
            f"ceiling {CEILING_DBFS} dBFS\n\n" + table, encoding="utf-8")
        clips = [r["name"] for r in rows if r["clipped"] or r.get("ogg_peak", 0) >= CLIP_THRESHOLD]
        if not quiet:
            print()
            print(table)
            print("clipping: " + (", ".join(clips) if clips else "none (WAV and decoded OGG)"))
        if pack:
            lumps = [r.name for r in rendered if not r.is_bed]
            out = pack_overlay(lumps, out_dir, pk3)
            if not quiet:
                print(f"overlay: {out} ({out.stat().st_size} B, {len(lumps)} lumps, no beds)")
    return rendered


# =========================================================================
# 6. The preview for the CEO (one self-contained HTML page)
# =========================================================================
# The CEO validates by looking (CLAUDE.md); for sound, by listening. The page
# embeds every OGG (base64) so it plays from a double-click with no server,
# the way the art previews embed their PNGs, and lists per file what it
# replaces, what the card asked for, the numbers, and every source.

ACTORS = (
    ("RRI", "Reich rifleman", "SD_ReichRifleman", "5.1"),
    ("LTR", "Liberty Legion trooper", "SD_LegionTrooper", "5.2"),
    ("STO", "Hybrid Stormtrooper", "SD_Stormtrooper", "5.3"),
    ("HND", "Reich hound", "SD_ReichHound", "5.4"),
    ("DGB", "Doughboy", "SD_Doughboy", "5.5"),
    ("PZR", "Panzermensch, and the heavy Panzermensch (inherits every sound)",
     "SD_Panzermensch, SD_PanzermenschSchwer", "5.6"),
    ("GEN", "The General", "SD_General", "5.7"),
)

PAGE_CSS = """
:root{--bg:#1b1c1f;--card:#26282c;--ink:#e8e6e0;--mute:#9a9892;--red:#c8302a;--line:#3a3d44;--warn:#c9a227}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f6f5f2;--card:#ebe9e4;--ink:#1d1d1f;--mute:#5d5b57;--line:#d4d1ca;--warn:#8a6d00}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
header{padding:20px 16px;border-bottom:2px solid var(--red)}h1{margin:0 0 6px;font-size:22px}
.meta{color:var(--mute);font-size:12px}.intro{max-width:1000px;margin:10px 0 0}
section{padding:18px 16px;border-top:1px solid var(--line)}
h2{font-size:15px;margin:0 0 8px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:900px;font-size:12.5px}
td,th{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}
th{color:var(--mute);font-weight:normal}
code{font-family:Menlo,Consolas,monospace;font-size:12px}
audio{width:230px;height:32px;margin-top:4px}
.src{color:var(--mute);font-size:11.5px;font-family:Menlo,Consolas,monospace;word-break:break-all}
.voice{color:var(--warn);margin:0 0 8px}
pre{background:var(--card);padding:10px 12px;border-radius:4px;overflow-x:auto;font-size:12px}
"""

AUDITION_TEXT = """\
.venv/Scripts/python.exe tools/audio/gen_sfx.py          # rebuild the drafts, the overlay and the report
.venv/Scripts/python.exe tools/build.py                  # dist/sovietdoom.pk3
SD_ALLOW_ENGINE=1 tools/run.sh -file work/audio/sfx/sd-enemy-sfx-draft.pk3 +map RANGE
# RANGE, the practice range, holds the bestiary gallery. Drop the -file argument and the Freedoom stand-ins are back.
# That a second -file and a later SNDINFO override the mod's is what the music and weapon
# overlays rely on; NOT VERIFIED by the sound-designer, who does not start the engine (D26)."""


def _esc(text: str) -> str:
    import html
    return html.escape(text, quote=True)


def preview_html(rendered, rows, seed, stamp, out_dir=OUT_DIR, sndinfo=SNDINFO_PATH) -> str:
    import base64
    by_name = {r.name: r for r in rendered}
    numbers = {row["name"]: row for row in rows}
    stand_in = sndinfo_rows(sndinfo)

    def player(name):
        _wav, ogg = paths_of(name, out_dir)
        data = base64.b64encode(ogg.read_bytes()).decode("ascii")
        return f'<audio controls preload="none" src="data:audio/ogg;base64,{data}"></audio>'

    def row_html(name):
        r, m = by_name[name], numbers[name]
        logical, fd = stand_in.get(r.lump, ("-", "-"))
        if r.is_bed:
            what = f"a bed under the voice <code>{r.lump}</code>; not a lump, not in the overlay"
        else:
            what = f"<code>{_esc(logical)}</code><br>today Freedoom <code>{fd}</code>"
        srcs = "<br>".join(_esc(c) for c in r.provenance())
        nums = (f"{r.seconds:.2f} s, loudness {m['loudness_db']:.1f} dB, peak {dbfs(m['peak']):.1f} dBFS<br>"
                f"centroid {m['centroid_hz']:.0f} Hz, &lt;300 Hz {m['low300']:.2f}, "
                f"1-3 kHz {m['mid1_3k']:.2f}, onset {m['onset_s']:.2f} s")
        return (f"<tr><td><code>{name}</code><br>{player(name)}</td><td>{r.recipe.route}</td>"
                f"<td>{_esc(r.recipe.brief)}</td><td>{what}</td><td>{nums}</td>"
                f'<td class="src">{srcs}</td></tr>')

    head = ("<tr><th>File</th><th>Route</th><th>What the card asks for</th><th>Replaces</th>"
            "<th>Measured</th><th>Sources (pack, file, segment, sha256 prefix)</th></tr>")
    n_lumps = sum(not r.is_bed for r in rendered)
    n_beds = len(rendered) - n_lumps
    parts = ["<!doctype html>",
             '<html lang="en"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width,initial-scale=1">'
             f"<title>Enemy SFX drafts</title><style>{PAGE_CSS}</style></head><body>",
             "<header><h1>Soviet Doom: enemy sound effects, drafts (F5)</h1>",
             f'<div class="meta">{_esc(stamp)}. tools/audio/gen_sfx.py, seed {seed}, '
             f"{SAMPLE_RATE} Hz mono, Vorbis q{OGG_QUALITY}. Plan, cards and rights: "
             "docs/sound/ENEMY-SOUNDS.md.</div>",
             '<p class="intro"><b>Drafts: nothing approved, nothing in the PK3.</b> '
             f"{n_lumps} lumps, every bestiary sound that is not a voice. The twelve voices are the "
             "CEO's and postponed (D37); until they come the enemies keep Freedoom's voices. "
             f"Under eight of those voices goes a <b>bed</b> ({n_beds} here): the squelch, the gear, "
             "the collapse, the General's mechanism failing, built now so a take only has to be laid "
             "on top. Routes: <b>C</b> our synthesis; <b>B</b> a CC0 pack authorised by D36, always "
             "layered with C; <b>A</b> Freedoom's DSSLOP (BSD-3). <b>Nobody has listened to these "
             "yet.</b> The numbers are instruments; the verdict is the CEO's ear.</p></header>"]
    for code, title, cls, sec in ACTORS:
        names = [n for n in by_name if n[2:5] == code]
        if not names:
            continue
        voices = [v for v in VOICE_LUMPS if v[2:5] == code]
        parts.append(f"<section><h2>{_esc(title)}: <code>{_esc(cls)}</code> "
                     f"(ENEMY-SOUNDS.md {sec})</h2>")
        if voices:
            parts.append(f'<p class="voice">Voices postponed (D37): {", ".join(voices)}.</p>')
        parts.append('<div class="wrap"><table>' + head + "".join(row_html(n) for n in names)
                     + "</table></div></section>")
    parts.append("<section><h2>How to hear them in the game (the PM, D26)</h2><pre>"
                 + _esc(AUDITION_TEXT) + "</pre></section></body></html>")
    return "\n".join(parts) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="+", metavar="NAME", help="build only these lumps or beds (SDRRIDTH-bed)")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--list", action="store_true", help="print the recipes and exit")
    p.add_argument("--no-pk3", action="store_true", help="do not write the audition overlay")
    p.add_argument("--report", action="store_true", help="measure what is on disk and exit")
    p.add_argument("--preview", metavar="HTML", type=Path,
                   help="also write the self-contained listening page (full build only)")
    p.add_argument("--stamp", default="", help="the date line printed on the preview")
    args = p.parse_args(argv)

    if args.list:
        for name in all_names():
            rec = recipe_of(name)
            print(f"{name:<13} {rec.route:<4} {rec.loud_class:<8} "
                  f"{rec.duration[0]:.2f}-{rec.duration[1]:.2f} s  {rec.brief}")
        print(f"{len(RECIPES)} lumps and {len(BEDS)} beds; voices not built (D37): {' '.join(VOICE_LUMPS)}")
        return 0
    names = [normalise_name(x) for x in args.only] if args.only else all_names()
    known = set(all_names())
    unknown = [x for x in names if x not in known]
    if unknown:
        print(f"gen_sfx: no recipe for {', '.join(unknown)}", file=sys.stderr)
        return 2
    if args.report:
        rows = [measure(x) for x in names if paths_of(x)[0].is_file()]
        print(report_table(rows))
        return 0
    if args.preview and args.only:
        print("gen_sfx: --preview needs the full build (it lists every draft)", file=sys.stderr)
        return 2
    try:
        rendered = build(names, args.seed, encode=True, pack=not args.no_pk3 and not args.only)
    except SourceMissing as exc:
        print(f"gen_sfx: {exc}", file=sys.stderr)
        return 3
    if args.preview:
        rows = [measure(r.name) for r in rendered]
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(preview_html(rendered, rows, args.seed, args.stamp or "undated"),
                                encoding="utf-8")
        print(f"preview: {args.preview} ({args.preview.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
