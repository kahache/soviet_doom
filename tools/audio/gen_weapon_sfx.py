#!/usr/bin/env python3
"""Draft weapon sound effects for the arsenal (F4, gate G4), reproducibly.

    .venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py            # Windows
    .venv/bin/python tools/audio/gen_weapon_sfx.py                    # macOS
    .venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --only SDPPFIR SDAXSWG
    .venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --list     # the plan, writes nothing
    .venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --preview docs/sound/previews/<dated>.html

Writes, and writes nothing else:

- `work/audio/sfx/weapons/<LUMP>.wav`: one 16-bit mono 44.1 kHz WAV per lump,
  the master. The 31 lumps are the cards of `docs/sound/WEAPON-SOUNDS.md`
  §4: fire, reload or break-open, pickup and empty click for the six guns,
  the RPG-7's and the Katyusha's extra events, and the ice axe (D40).
- `work/audio/sfx/weapons/ogg/<LUMP>.ogg`: the same, Vorbis, which is what
  `src/sounds/` will hold (MOD-SPEC §6.2). Needs `ffmpeg`; skipped without it.
- `work/audio/sfx/weapons/preview/*.wav`: listening aids that are NOT lumps
  (the PPSh-41 as a burst, at the engine's rate and at the real one).
- `work/audio/sfx/weapons/MANIFEST.txt` and `PROVENANCE.tsv`: per lump its
  length, peak, SHA-256 and the exact source files it used, with their own
  SHA-256 (the TSV has the columns of `work/audio/sfx/enemies/PROVENANCE.tsv`).
- `work/audio/sfx/sd-weapon-sfx-draft.pk3`: an audition overlay, loaded after
  `dist/sovietdoom.pk3`, whose SNDINFO re-points the weapon logical names at
  these drafts. Delete it and everything is as it was.
- with `--preview PATH`: one self-contained HTML page for the CEO (every lump
  embedded as OGG, the Freedoom placeholder heard today beside it).

Nothing here touches `src/` or `assets/`: the drafts are for the CEO's ears.

Where the sound comes from
--------------------------
Every bang, whoosh, hiss and boom is **our own synthesis** (numpy, fixed
seeds): route `SYN`. The only foreign material is short mechanical foley
from two CC0 packs downloaded under D36 and logged in
`docs/sound/ENEMY-SOUNDS.md` §2.1:

- `OGA-100` (rubberduck, *100 CC0 SFX*, his own recordings): clicks, latches,
  metal clunks, springs, a splash;
- `KEN-IMP` (Kenney, *Impact Sounds*): wood, metal and body impacts, and the
  pick-on-rock hits the ice axe needs. Kenney made them with GameSynth; that
  tool's terms on generated sound are NOT VERIFIED, the same open point as
  for the enemy sounds (ENEMY-SOUNDS §2.1).

No recording of a real firearm is used: the two `shot_*` files of OGA-100
are left out because what they recorded is not stated. Every foreign clip is
layered under synthesis, never shipped alone.

Sources are decoded with `ffmpeg` (on the PATH on the CEO's PC). If `ffmpeg`
or a source file is missing, the lumps that need it are skipped with a
message and the purely synthetic lumps are still built.

Takes (the sweep)
-----------------
A sweep is the unit of review (`docs/PIPELINE.md` §2). The lumps whose
character matters most (`Lump.sweep`) are also rendered as takes B (8 %
slower: lower, heavier) and C (8 % faster: higher, drier). The take a lump
ships with is `CHOSEN_TAKE` (default A), so the CEO's pick is a one-line edit.

Determinism: one `numpy.random.default_rng` per lump, seeded from the lump
name (CRC-32), no time, no global state; the PK3 carries a fixed zip date.
Two runs on one machine give byte-identical WAVs and PK3
(`tests/test_gen_weapon_sfx.py`). The OGG files and the HTML depend on the
local ffmpeg build and are not promised to be identical across machines.

Licence: the script GPL-3.0 with the code; its output CC BY-NC-SA 4.0 (D15),
with the CC0 inputs credited in WEAPON-SOUNDS.md.
"""

from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import html
import io
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
SOURCES_DIR = PROJECT_ROOT / "work" / "audio" / "sfx_sources"
SFX_DIR = PROJECT_ROOT / "work" / "audio" / "sfx"
OUT_DIR = SFX_DIR / "weapons"
PK3_PATH = SFX_DIR / "sd-weapon-sfx-draft.pk3"
IWAD_PATH = PROJECT_ROOT / "iwads" / "freedoom2.wad"

# --- Format ------------------------------------------------------------------
SR = 44100                     # Hz. Gunshots live above 5 kHz; 22.05 kHz would cut them
SAMPLE_WIDTH = 2               # bytes: 16-bit PCM, which GZDoom reads natively
PCM_MAX = 32767
DEFAULT_PEAK_DBFS = -1.0       # headroom against inter-sample overs, as ENEMY-SOUNDS §6
RELOAD_PEAK_DBFS = -3.0        # handling is quieter than a shot
PICKUP_PEAK_DBFS = -3.0
DRY_PEAK_DBFS = -6.0           # an empty click must not sound like a shot
# Handling sounds are levelled by short-term loudness, not by peak: a pickup
# is mostly sustained clatter and would otherwise outshout a pistol shot,
# whose energy is one 5 ms crack. Measured on the first drafts, the quietest
# shot of the arsenal (one PPSh round) reads -16 dB short-term; these targets
# sit under it. tests/test_gen_weapon_sfx.py holds the ordering.
SHORT_TERM_WINDOW_S = 0.05     # loudest 50 ms window, mean square, dB re full scale
RELOAD_LOUDNESS_DB = -20.0
PICKUP_LOUDNESS_DB = -21.0
DRY_LOUDNESS_DB = -25.0
TAIL_FLOOR_DB = -60.0          # trailing audio below this (re. peak) is trimmed
FADE_OUT_S = 0.008             # end of every lump: no click when the tail is cut
FADE_IN_S = 0.0003             # 13 samples: removes a DC step, keeps the transient
FILTER_PAD = 65536             # samples (1.5 s): room for ringing and for the cepstrum;
                               # 16384 time-aliased the 25 Hz high-pass into a -60 dB tail
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # as tools/sdbuild and audition.py
SOUNDS_DIR_IN_PK3 = "sounds"
OGG_QUALITY = "4"              # libvorbis -q:a; ~64 kbit/s mono, transparent for SFX

# --- Engine timing the sounds are cut to (read from src/zscript/weapons) -----
TICS_PER_SECOND = 35
MELEE_TICS_BEFORE_HIT = 5      # ice_axe.zs Fire: PUNG B 5, then the blow (the shovel's, D40)
TT_CYCLE_TICS = 16             # tokarev.zs Fire: 4 + 6 + 3 + 3
PPSH_TICS_PER_ROUND = 3        # ppsh.zs Fire: CHGG A 3 / CHGG B 3 -> 700 rpm
PPSH_REAL_RPM = 900            # the real gun, which 35 Hz cannot express
IZH_RELOAD_TICS = 30           # izh.zs Reload: 6 + 8 + 8 + 8
IZH_RELOAD_CLOSE_TICS = 22     # 6 + 8 + 8: frame A, where the shells are counted
RPG7_CYCLE_TICS = 26           # rpg7.zs Fire: 8 + 14 + 4
RPG7_TICS_BEFORE_LAUNCH = 8    # MISG B 8, then A_FireProjectile
KATYUSHA_CHARGE_TICS = 20      # katyusha.zs Fire: BFGG A 20 with the charge sound
KATYUSHA_RECOVERY_TICS = 20    # katyusha.zs Fire: BFGG B 20 A_ReFire, after the salvo


def tics(n: float) -> float:
    return n / TICS_PER_SECOND


# The RPG-7 reload is proposed 4 tics into the 14-tic launch frame, once the
# round has left (WEAPON-SOUNDS.md §6): it must be over before the next launch.
RPG7_RELOAD_DELAY_TICS = 4
RPG7_RELOAD_WINDOW_S = tics(RPG7_CYCLE_TICS - RPG7_TICS_BEFORE_LAUNCH - RPG7_RELOAD_DELAY_TICS)

# --- Sources -----------------------------------------------------------------
# key -> (pack ID of docs/sound/ENEMY-SOUNDS.md §2, path under SOURCES_DIR).
KEN = "ken-imp/extracted/Audio/"
SOURCE_FILES: dict[str, tuple[str, str]] = {
    "switch_01": ("OGA-100", "oga-100/extracted/switch_01.ogg"),
    "switch_02": ("OGA-100", "oga-100/extracted/switch_02.ogg"),
    "metal_01": ("OGA-100", "oga-100/extracted/metal_01.ogg"),
    "metal_02": ("OGA-100", "oga-100/extracted/metal_02.ogg"),
    "metal_03": ("OGA-100", "oga-100/extracted/metal_03.ogg"),
    "metal_07": ("OGA-100", "oga-100/extracted/metal_07.ogg"),
    "metal_09": ("OGA-100", "oga-100/extracted/metal_09.ogg"),
    "metal_11": ("OGA-100", "oga-100/extracted/metal_11.ogg"),
    "metal_12": ("OGA-100", "oga-100/extracted/metal_12.ogg"),
    "spring_04": ("OGA-100", "oga-100/extracted/spring_04.ogg"),
    "spring_06": ("OGA-100", "oga-100/extracted/spring_06.ogg"),
    "wooden_03": ("OGA-100", "oga-100/extracted/wooden_03.ogg"),
    "splash_01": ("OGA-100", "oga-100/extracted/splash_01.ogg"),
    "mining_002": ("KEN-IMP", KEN + "impactMining_002.ogg"),
    "punch_heavy_000": ("KEN-IMP", KEN + "impactPunch_heavy_000.ogg"),
    "soft_heavy_001": ("KEN-IMP", KEN + "impactSoft_heavy_001.ogg"),
    "wood_light_000": ("KEN-IMP", KEN + "impactWood_light_000.ogg"),
    "wood_light_001": ("KEN-IMP", KEN + "impactWood_light_001.ogg"),
    "wood_medium_000": ("KEN-IMP", KEN + "impactWood_medium_000.ogg"),
    "wood_medium_002": ("KEN-IMP", KEN + "impactWood_medium_002.ogg"),
    "metal_light_000": ("KEN-IMP", KEN + "impactMetal_light_000.ogg"),
    "metal_light_001": ("KEN-IMP", KEN + "impactMetal_light_001.ogg"),
    "metal_light_003": ("KEN-IMP", KEN + "impactMetal_light_003.ogg"),
    "metal_heavy_001": ("KEN-IMP", KEN + "impactMetal_heavy_001.ogg"),
}
ALLOWED_PACKS = ("OGA-100", "KEN-IMP")
SOURCE_ONSET_RATIO = 0.03      # a source "starts" at 3 % of its peak
SOURCE_PREROLL_S = 0.001       # kept before that onset


class MissingSource(RuntimeError):
    pass


@functools.lru_cache(maxsize=1)
def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def source_path(key: str, sources_dir: Path = SOURCES_DIR) -> Path:
    return sources_dir / SOURCE_FILES[key][1]


# Decoding is the slow part (one ffmpeg process per file), so a decoded file
# is kept for the life of the process, keyed by path, size and mtime.
_DECODED: dict[tuple[str, int, int], np.ndarray] = {}


def decode(path: Path) -> np.ndarray:
    """OGG -> mono float64 at SR, through ffmpeg. Raises MissingSource."""
    exe = ffmpeg_path()
    if exe is None:
        raise MissingSource("ffmpeg is not on the PATH")
    if not path.is_file():
        raise MissingSource(f"source not found: {path}")
    st = path.stat()
    key = (str(path.resolve()), st.st_size, st.st_mtime_ns)
    if key not in _DECODED:
        out = subprocess.run(
            [exe, "-v", "error", "-nostdin", "-i", str(path),
             "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
            capture_output=True, check=True).stdout
        _DECODED[key] = np.frombuffer(out, dtype="<f4").astype(np.float64)
    return _DECODED[key].copy()


class Sources:
    """Decoded, peak-normalised, onset-trimmed source clips, cached."""

    def __init__(self, sources_dir: Path = SOURCES_DIR):
        self.dir = sources_dir
        self._cache: dict[str, np.ndarray] = {}

    def available(self, keys) -> bool:
        if not keys:
            return True
        if ffmpeg_path() is None:
            return False
        return all(source_path(k, self.dir).is_file() for k in keys)

    def __call__(self, key: str) -> np.ndarray:
        if key not in self._cache:
            x = decode(source_path(key, self.dir))
            peak = np.max(np.abs(x)) if x.size else 0.0
            if peak <= 0:
                raise MissingSource(f"source is silent: {key}")
            x = x / peak    # several OGA-100 files decode above full scale
            onset = int(np.argmax(np.abs(x) >= SOURCE_ONSET_RATIO))
            onset = max(0, onset - n_of(SOURCE_PREROLL_S))
            self._cache[key] = x[onset:]
        return self._cache[key].copy()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- DSP primitives ----------------------------------------------------------

def n_of(seconds: float) -> int:
    return int(round(seconds * SR))


def times(n: int) -> np.ndarray:
    return np.arange(n) / SR


def place(buf: np.ndarray, x: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = n_of(at)
    if i >= len(buf):
        return
    end = min(len(buf), i + len(x))
    buf[i:end] += gain * x[:end - i]


def env(n: int, attack: float, decay: float, hold: float = 0.0) -> np.ndarray:
    """Linear attack, optional hold, exponential decay (time constant)."""
    t = times(n)
    a = np.ones(n) if attack <= 0 else np.clip(t / attack, 0.0, 1.0)
    d = np.exp(-np.maximum(t - attack - hold, 0.0) / decay)
    return a * d


def glide(n: int, f_start: float, f_end: float, tau: float) -> np.ndarray:
    """Sine whose frequency slides exponentially from f_start to f_end."""
    f = f_end + (f_start - f_end) * np.exp(-times(n) / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def butter(f: np.ndarray, lo: float | None = None, hi: float | None = None,
           order: int = 2) -> np.ndarray:
    """Butterworth-shaped magnitude: high-pass at lo, low-pass at hi."""
    g = np.ones_like(f)
    if hi is not None:
        g = g / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo is not None:
        g = g / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return g


def bump(f: np.ndarray, f0: float, q: float, gain_db: float) -> np.ndarray:
    """A resonant peak (or notch, if gain_db < 0) at f0."""
    g = 10 ** (gain_db / 20)
    ratio = np.maximum(f, 1e-3) / f0
    return 1 + (g - 1) / (1 + (q * (ratio - 1 / ratio)) ** 2)


def filt(x: np.ndarray, mag: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    """Causal minimum-phase filter with magnitude `mag(f)`.

    Built from the real cepstrum, so a transient is not smeared backwards in
    time the way a zero-phase FFT filter would smear it (pre-ringing before a
    gunshot is exactly the wrong sound).
    """
    n = len(x)
    size = 1 << int(np.ceil(np.log2(n + FILTER_PAD)))
    f = np.fft.rfftfreq(size, 1 / SR)
    log_mag = np.log(np.maximum(mag(f), 1e-5))
    cep = np.fft.irfft(log_mag, size)
    fold = np.zeros(size)
    fold[0] = cep[0]
    fold[1:size // 2] = 2 * cep[1:size // 2]
    fold[size // 2] = cep[size // 2]
    h = np.exp(np.fft.rfft(fold))
    return np.fft.irfft(np.fft.rfft(x, size) * h, size)[:n]


def shape(x: np.ndarray, gain: Callable[[float, np.ndarray], np.ndarray],
          frame: int = 1024) -> np.ndarray:
    """Time-varying spectral gain (sweeps, darkening tails) by STFT.

    Periodic Hann analysis at 50 % overlap sums to one, so with unit gain the
    signal comes back unchanged. Used on noise only, where phase is moot.
    """
    hop = frame // 2
    win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(frame) / frame)
    padded = np.concatenate([np.zeros(frame), x, np.zeros(frame)])
    out = np.zeros_like(padded)
    f = np.fft.rfftfreq(frame, 1 / SR)
    for start in range(0, len(padded) - frame + 1, hop):
        centre = (start + hop - frame) / SR
        spec = np.fft.rfft(padded[start:start + frame] * win)
        out[start:start + frame] += np.fft.irfft(spec * gain(centre, f), frame)
    return out[frame:frame + len(x)]


def resample(x: np.ndarray, ratio: float) -> np.ndarray:
    """Varispeed: ratio > 1 is higher and shorter."""
    n = int(len(x) / ratio)
    return np.interp(np.arange(n) * ratio, np.arange(len(x)), x)


def normalised(x: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(x))
    return x / peak if peak > 0 else x


def saturate(x: np.ndarray, drive: float) -> np.ndarray:
    return np.tanh(drive * normalised(x)) / np.tanh(drive)


def noise(rng: np.random.Generator, seconds: float) -> np.ndarray:
    return rng.standard_normal(n_of(seconds))


def wobble(rng: np.random.Generator, n: int, rate_hz: float) -> np.ndarray:
    """Smooth random control signal in about -1..1 (flame turbulence)."""
    k = max(4, int(n / SR * rate_hz) + 4)
    ctrl = rng.standard_normal(k)
    ctrl = np.convolve(ctrl, np.ones(3) / 3, mode="same")
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), ctrl)


def finish(x: np.ndarray, peak_dbfs: float) -> np.ndarray:
    """DC out, tail trimmed, fades, peak at peak_dbfs. Returns int16-ready floats."""
    x = filt(x, lambda f: butter(f, lo=25, order=2))
    peak = np.max(np.abs(x))
    if peak <= 0:
        raise ValueError("recipe produced silence")
    loud = np.nonzero(np.abs(x) >= peak * 10 ** (TAIL_FLOOR_DB / 20))[0]
    x = x[:loud[-1] + 1 + n_of(FADE_OUT_S)]
    fade_in = n_of(FADE_IN_S)
    x[:fade_in] *= np.linspace(0, 1, fade_in, endpoint=False)
    fade_out = min(n_of(FADE_OUT_S), len(x))
    x[-fade_out:] *= np.linspace(1, 0, fade_out)
    return x / np.max(np.abs(x)) * 10 ** (peak_dbfs / 20)


def to_pcm(x: np.ndarray) -> np.ndarray:
    return np.clip(np.round(x * PCM_MAX), -PCM_MAX, PCM_MAX).astype("<i2")


def wav_bytes(x: np.ndarray, rate: int = SR) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(rate)
        w.writeframes(to_pcm(x).tobytes())
    return buf.getvalue()


def short_term_db(x: np.ndarray, window: float = SHORT_TERM_WINDOW_S) -> float:
    """Loudest `window` of the lump, mean square in dB. A ruler, not LUFS."""
    w = n_of(window)
    sq = x ** 2
    if len(sq) <= w:
        return float(10 * np.log10(max(np.mean(sq), 1e-12)))
    c = np.concatenate([[0.0], np.cumsum(sq)])
    return float(10 * np.log10(max(np.max(c[w:] - c[:-w]) / w, 1e-12)))


def levelled(x: np.ndarray, loudness_db: float | None) -> np.ndarray:
    """Turn a finished lump down until its short-term loudness is the target."""
    if loudness_db is None:
        return x
    over = short_term_db(x) - loudness_db
    return x * 10 ** (-over / 20) if over > 0 else x


def rms_dbfs(x: np.ndarray) -> float:
    """Plain RMS over the whole lump. A ruler for the manifest, not loudness."""
    return float(20 * np.log10(max(np.sqrt(np.mean(x ** 2)), 1e-9)))


# --- Shared sound atoms ------------------------------------------------------

def crack(rng, decay: float, lo: float, hi: float, length: float = 0.06) -> np.ndarray:
    """The supersonic/muzzle crack: a very short broadband burst."""
    n = n_of(length)
    return filt(rng.standard_normal(n) * env(n, 0.0002, decay),
                lambda f: butter(f, lo=lo, hi=hi))


def thump(f_start: float, f_end: float, tau: float, decay: float,
          length: float) -> np.ndarray:
    n = n_of(length)
    return glide(n, f_start, f_end, tau) * env(n, 0.001, decay)


def burst_noise(rng, length: float, attack: float, decay: float,
                mag: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    n = n_of(length)
    return filt(rng.standard_normal(n) * env(n, attack, decay), mag)


def click(rng, centre: float, decay: float = 0.003) -> np.ndarray:
    """A small synthetic mechanical click (ratchet tooth, pawl)."""
    return burst_noise(rng, 0.03, 0.0002, decay,
                       lambda f: butter(f, lo=centre * 0.6, hi=centre * 1.8) *
                       bump(f, centre, 4, 9))


def ring(partials, decay: float, length: float, attack: float = 0.0005) -> np.ndarray:
    """Inharmonic metal ring: a sum of decaying sines, higher partials shorter."""
    n = n_of(length)
    t = times(n)
    out = np.zeros(n)
    for i, fr in enumerate(partials):
        out += np.sin(2 * np.pi * fr * t) * np.exp(-t / (decay / (1 + 0.4 * i))) / (1 + 0.3 * i)
    return out * np.clip(t / attack, 0, 1)


def scrape(rng, length: float, lo: float, hi: float, attack: float = 0.02,
           decay: float = 0.04, grain_hz: float = 160.0) -> np.ndarray:
    """Metal sliding on metal: band noise with a fast, rough grain."""
    n = n_of(length)
    rough = 0.6 + 0.4 * np.abs(wobble(rng, n, grain_hz))
    return filt(rng.standard_normal(n) * rough * env(n, attack, decay),
                lambda f: butter(f, lo=lo, hi=hi))


def cloth(rng, length: float = 0.12, attack: float = 0.02, decay: float = 0.04) -> np.ndarray:
    """A hand closing on a grip or a sling: soft, airy, short."""
    return burst_noise(rng, length, attack, decay, lambda f: butter(f, lo=1500, hi=6000))


def grit(rng, length: float, count: int, start: float, spread: float, tau: float,
         lo: float, hi: float) -> np.ndarray:
    """Sparse bright impulses thinning out: debris, chips, a crackle."""
    n = n_of(length)
    imp = np.zeros(n)
    for h in rng.uniform(start, start + spread, count):
        i = min(n - 1, n_of(h))
        imp[i] += rng.uniform(0.3, 1.0) * np.exp(-(h - start) / tau)
    return filt(imp, lambda f: butter(f, lo=lo, hi=hi))


def foley(src, key: str, ratio: float = 1.0, lo: float | None = None,
          hi: float | None = None, decay: float | None = None,
          length: float | None = None) -> np.ndarray:
    """A source clip, varispeeded, cut, band-limited and enveloped."""
    x = src(key)
    if ratio != 1.0:
        x = resample(x, ratio)
    if length is not None:
        x = x[:n_of(length)]
    if lo is not None or hi is not None:
        x = filt(x, lambda f: butter(f, lo=lo, hi=hi))
    if decay is not None:
        x = x * env(len(x), 0.0, decay)
    return x


def darkening_tail(rng, length: float, attack: float, decay: float,
                   hi_start: float, hi_end: float, lo: float = 60.0) -> np.ndarray:
    """Noise whose low-pass closes over time: the report dying in a room."""
    n = n_of(length)
    x = rng.standard_normal(n) * env(n, attack, decay)

    def gain(t, f):
        hi = hi_end + (hi_start - hi_end) * np.exp(-max(t, 0.0) / (length / 3))
        return butter(f, lo=lo, hi=hi)
    return shape(x, gain)


# --- The recipes (one per lump; the cards are WEAPON-SOUNDS.md §4) ----------
# Slot 1 - the ice axe (D40). Same 27-tic swing as the shovel it replaces.

def r_iceaxe_swing(rng, src) -> np.ndarray:
    """SDAXSWG: a narrow steel head through air; the pick whistles. Peaks before the blow."""
    length = 0.30
    n = n_of(length)
    t = times(n)
    peak_t = tics(MELEE_TICS_BEFORE_HIT) * 0.8          # ~0.114 s
    rise = 0.5 - 0.5 * np.cos(np.pi * np.clip(t / peak_t, 0, 1))
    fall = np.exp(-np.maximum(t - peak_t, 0) / 0.04)
    amp = rise * fall
    x = rng.standard_normal(n) * amp

    def gain(tc, f):
        # A head, not a blade: a narrower, higher band than the shovel's.
        k = np.clip(tc / peak_t, 0, 1.6)
        centre = 700 + 1300 * np.sin(np.pi / 2 * min(k, 1.0)) - 500 * max(k - 1, 0)
        return butter(f, lo=centre * 0.7, hi=centre * 1.45) * bump(f, centre, 2.5, 8)
    air = shape(x, gain)
    # The pick's point whistles; its pitch follows the head's speed.
    speed = np.sin(np.pi / 2 * np.clip(t / peak_t, 0, 1)) * fall
    f = 1500 + 1100 * speed
    whistle = np.sin(2 * np.pi * np.cumsum(f) / SR) * amp ** 1.5
    # The shaft: a thin low band so it reads as a tool with a handle.
    body = filt(rng.standard_normal(n) * amp, lambda fr: butter(fr, lo=120, hi=320))
    return air + 0.10 * whistle + 0.25 * body


def r_iceaxe_hit(rng, src) -> np.ndarray:
    """SDAXHIT: the pick goes into a body: a steel tick, then a dense, damped thud."""
    out = np.zeros(n_of(0.42))
    place(out, crack(rng, 0.0015, 2500, 9000, 0.02), 0.0, 0.45)
    place(out, thump(95, 50, 0.025, 0.05, 0.3), 0.0, 1.0)
    place(out, foley(src, "punch_heavy_000", ratio=0.9, decay=0.09), 0.002, 0.9)
    place(out, foley(src, "soft_heavy_001", decay=0.08), 0.004, 0.5)
    # Wet: low noise with a fast flutter, very short.
    n = n_of(0.12)
    flutter = 0.5 + 0.5 * np.sin(2 * np.pi * 38 * times(n))
    wet = filt(rng.standard_normal(n) * flutter * env(n, 0.004, 0.035),
               lambda f: butter(f, lo=150, hi=1200))
    place(out, wet, 0.012, 0.35)
    return saturate(out, 1.5)


def r_iceaxe_wall(rng, src) -> np.ndarray:
    """SDAXWAL: steel pick on concrete or stone: a bright chink, a short ring, grit."""
    out = np.zeros(n_of(0.6))
    place(out, foley(src, "mining_002", decay=0.12), 0.0, 1.0)
    place(out, crack(rng, 0.002, 2000, 12000, 0.03), 0.0, 0.6)
    place(out, ring((3150.0, 4720.0, 6930.0, 8800.0), 0.06, 0.3), 0.001, 0.18)
    place(out, thump(180, 120, 0.01, 0.02, 0.1), 0.0, 0.3)
    place(out, grit(rng, 0.4, 18, 0.01, 0.25, 0.08, 2000, 9000), 0.0, 0.9)
    return saturate(out, 1.3)


def r_iceaxe_pickup(rng, src) -> np.ndarray:
    """SDAXPKP: lifted off the dorm rack: the shaft knocks, the head clinks, a hand grips."""
    out = np.zeros(n_of(0.55))
    place(out, foley(src, "wood_light_001"), 0.0, 0.7)
    place(out, foley(src, "metal_light_000", ratio=1.2, decay=0.07), 0.05, 0.45)
    place(out, cloth(rng), 0.12, 0.15)
    return out


# Slot 2 - TT-33.

def r_tokarev(rng, src) -> np.ndarray:
    """SDTTFIR: dry, high-velocity crack; a pistol, so a short slide click."""
    out = np.zeros(n_of(0.62))
    place(out, crack(rng, 0.005, 900, 9000), 0.0, 1.0)
    place(out, burst_noise(rng, 0.20, 0.0008, 0.030,
                           lambda f: butter(f, lo=120, hi=2600) * bump(f, 1100, 2, 4)),
          0.0, 0.85)
    place(out, thump(150, 70, 0.02, 0.028, 0.15), 0.0, 0.55)
    place(out, darkening_tail(rng, 0.55, 0.004, 0.11, 2600, 500, lo=150), 0.002, 0.16)
    slide = filt(resample(src("switch_01"), 1.1), lambda f: butter(f, lo=1500))
    place(out, slide, 0.055, 0.22)
    return saturate(out, 1.8)


def r_tokarev_reload(rng, src) -> np.ndarray:
    """SDTTRLD: magazine out, a fresh one in, the slide released."""
    out = np.zeros(n_of(1.0))
    place(out, foley(src, "switch_01", ratio=1.3, lo=1500), 0.0, 0.4)
    place(out, scrape(rng, 0.08, 1500, 5000), 0.03, 0.25)
    place(out, foley(src, "metal_02", ratio=1.1, decay=0.03), 0.10, 0.25)
    place(out, scrape(rng, 0.05, 1500, 5000), 0.40, 0.2)
    place(out, foley(src, "switch_02", lo=900, decay=0.03), 0.44, 0.7)
    place(out, thump(220, 160, 0.01, 0.02, 0.08), 0.44, 0.25)
    place(out, foley(src, "metal_11", ratio=0.9, decay=0.05), 0.70, 0.9)
    place(out, foley(src, "switch_01"), 0.704, 0.5)
    place(out, thump(160, 110, 0.01, 0.03, 0.1), 0.70, 0.4)
    return out


def r_tokarev_pickup(rng, src) -> np.ndarray:
    """SDTTPKP: a pistol picked up and checked: a grip, the slide eased back and let go."""
    out = np.zeros(n_of(0.5))
    place(out, foley(src, "metal_light_001", ratio=1.3, decay=0.04), 0.0, 0.5)
    place(out, cloth(rng, 0.1), 0.0, 0.2)
    place(out, foley(src, "switch_02", ratio=1.2, lo=1200, decay=0.02), 0.14, 0.55)
    place(out, foley(src, "metal_11", ratio=1.05, decay=0.04), 0.26, 0.7)
    return out


def r_tokarev_dry(rng, src) -> np.ndarray:
    """SDTTDRY: the hammer falls on an empty chamber: one small, crisp click."""
    out = np.zeros(n_of(0.16))
    place(out, foley(src, "switch_01", ratio=1.15, lo=1200, decay=0.02), 0.0, 1.0)
    place(out, click(rng, 3200, 0.002), 0.0, 0.4)
    place(out, thump(400, 300, 0.005, 0.008, 0.04), 0.0, 0.2)
    return out


# Slot 3 - IZh-58.

def r_izh_fire(rng, src) -> np.ndarray:
    """SDIZFIR: one barrel of a 12-gauge: a deep boom with a long rumble."""
    out = np.zeros(n_of(1.15))
    place(out, crack(rng, 0.006, 600, 7000, 0.08), 0.0, 0.8)
    place(out, burst_noise(rng, 0.45, 0.0015, 0.065, lambda f: butter(f, lo=50, hi=3000)),
          0.0, 1.0)
    boom = thump(92, 42, 0.07, 0.12, 0.8)
    boom += 0.25 * thump(184, 84, 0.07, 0.07, 0.8)
    place(out, boom, 0.0, 1.15)
    place(out, darkening_tail(rng, 1.1, 0.008, 0.28, 2400, 350, lo=40), 0.004, 0.24)
    return saturate(out, 2.2)


def r_izh_reload(rng, src) -> np.ndarray:
    """SDIZRLD: break open, hulls out, two shells in, snap shut (30 tics).

    The snap lands on frame A (22 tics, 0.629 s), where izh.zs reloads.
    """
    close_t = tics(IZH_RELOAD_CLOSE_TICS) - 0.01
    out = np.zeros(n_of(tics(IZH_RELOAD_TICS) + 0.03))
    # Top lever thrown, barrels drop on the hinge.
    place(out, resample(src("switch_02"), 0.9), 0.0, 0.55)
    hinge = resample(src("metal_03"), 0.8)
    place(out, hinge * env(len(hinge), 0.0, 0.06), 0.045, 0.6)
    place(out, thump(130, 90, 0.02, 0.035, 0.12), 0.045, 0.45)
    # Two spent hulls drawn out by hand: a short plastic slide each.
    for at in (0.15, 0.20):
        place(out, burst_noise(rng, 0.07, 0.01, 0.02,
                               lambda f: butter(f, lo=1800, hi=7000)), at, 0.18)
    # Two fresh shells pushed in: brass rim knocking the breech.
    shell = resample(src("wooden_03"), 1.35)
    for at, g in ((0.33, 0.42), (0.47, 0.38)):
        place(out, shell * env(len(shell), 0.0, 0.03), at, g)
        place(out, thump(300, 240, 0.01, 0.018, 0.06), at, 0.25)
    # Snap shut: heavy metal clack plus the latch catching.
    snap = src("metal_09")
    place(out, snap * env(len(snap), 0.0, 0.09), close_t, 0.95)
    place(out, src("switch_01"), close_t + 0.006, 0.4)
    place(out, thump(110, 70, 0.02, 0.04, 0.15), close_t, 0.5)
    return out


def r_izh_pickup(rng, src) -> np.ndarray:
    """SDIZPKP: a double gun picked up: the stock knocks, the gun is broken and closed."""
    out = np.zeros(n_of(0.7))
    place(out, foley(src, "wood_medium_000", ratio=0.95), 0.0, 0.6)
    place(out, cloth(rng), 0.0, 0.15)
    place(out, foley(src, "switch_02", ratio=0.9), 0.18, 0.45)
    place(out, foley(src, "metal_09", decay=0.07), 0.30, 0.8)
    place(out, foley(src, "switch_01"), 0.306, 0.35)
    place(out, thump(110, 70, 0.02, 0.04, 0.15), 0.30, 0.4)
    return out


def r_izh_dry(rng, src) -> np.ndarray:
    """SDIZDRY: the hammerless lock clicks on nothing: duller than the pistol's click."""
    out = np.zeros(n_of(0.18))
    place(out, foley(src, "switch_01", ratio=0.8, lo=400, hi=4000, decay=0.025), 0.0, 1.0)
    place(out, thump(250, 180, 0.008, 0.015, 0.06), 0.0, 0.35)
    return out


# Slot 4 - PPSh-41.

def r_ppsh(rng, src) -> np.ndarray:
    """SDPPFIR: one round of the PPSh. The burst is the engine repeating it.

    Everything that must be heard in a burst happens inside one 3-tic cycle
    (86 ms): a new round on CHAN_WEAPON cuts the old one (ASSUMPTION, see
    WEAPON-SOUNDS.md §3), so only the last round's tail is ever heard whole.
    """
    out = np.zeros(n_of(0.45))
    place(out, crack(rng, 0.0035, 1500, 11000), 0.0, 0.95)
    # Thin barrel jacket: a brighter, "tinny" body with a resonance.
    place(out, burst_noise(rng, 0.12, 0.0005, 0.018,
                           lambda f: butter(f, lo=380, hi=4500) * bump(f, 2300, 3, 7)),
          0.0, 0.7)
    place(out, thump(190, 105, 0.012, 0.016, 0.09), 0.0, 0.32)
    # Jacket ring: three inharmonic partials, short.
    n = n_of(0.08)
    jacket = sum(np.sin(2 * np.pi * fr * times(n)) for fr in (2870.0, 4310.0, 6090.0))
    place(out, jacket * env(n, 0.0005, 0.02), 0.001, 0.05)
    # Open bolt slamming home, then the drum's loose rounds and spring.
    bolt = filt(src("switch_02"), lambda f: butter(f, lo=900))
    place(out, bolt * env(len(bolt), 0.0, 0.02), 0.028, 0.17)
    drum = filt(src("spring_04"), lambda f: butter(f, lo=800))
    place(out, drum * env(len(drum), 0.0, 0.035), 0.012, 0.11)
    place(out, darkening_tail(rng, 0.42, 0.003, 0.075, 2200, 400, lo=160), 0.002, 0.18)
    return saturate(out, 1.7)


def r_ppsh_reload(rng, src) -> np.ndarray:
    """SDPPRLD: the drum: catch pressed, drum out, a full one in, bolt pulled back."""
    out = np.zeros(n_of(1.15))
    place(out, foley(src, "switch_02", ratio=1.1, lo=900), 0.0, 0.45)
    place(out, foley(src, "metal_03", ratio=0.75, decay=0.08), 0.05, 0.55)
    place(out, foley(src, "spring_04", ratio=0.85, lo=700, decay=0.06), 0.07, 0.35)
    place(out, foley(src, "metal_09", ratio=0.9, decay=0.08), 0.45, 0.85)
    place(out, thump(140, 90, 0.02, 0.04, 0.15), 0.45, 0.5)
    place(out, foley(src, "spring_04", ratio=0.85, lo=700, decay=0.05), 0.47, 0.25)
    place(out, scrape(rng, 0.07, 1200, 4500), 0.80, 0.25)
    place(out, foley(src, "spring_06", ratio=1.2, lo=600, decay=0.05), 0.80, 0.3)
    place(out, foley(src, "switch_01", ratio=0.9), 0.86, 0.9)
    place(out, foley(src, "metal_02", ratio=0.8, decay=0.03), 0.862, 0.4)
    return out


def r_ppsh_pickup(rng, src) -> np.ndarray:
    """SDPPPKP: a PPSh off the floor: wooden stock, steel jacket, the drum's rounds shift."""
    out = np.zeros(n_of(0.6))
    place(out, foley(src, "wood_medium_002"), 0.0, 0.6)
    place(out, foley(src, "metal_light_003", ratio=0.9, decay=0.06), 0.02, 0.4)
    place(out, foley(src, "spring_04", lo=800, decay=0.05), 0.08, 0.35)
    place(out, foley(src, "switch_02", ratio=1.3, lo=1500, decay=0.02), 0.22, 0.2)
    return out


def r_ppsh_dry(rng, src) -> np.ndarray:
    """SDPPDRY: an empty drum: trigger and sear give one heavy, hollow clack."""
    out = np.zeros(n_of(0.2))
    place(out, foley(src, "metal_02", ratio=0.75, decay=0.03), 0.0, 0.8)
    place(out, foley(src, "switch_02", ratio=0.85, lo=600, decay=0.02), 0.0, 0.7)
    place(out, thump(170, 110, 0.01, 0.025, 0.1), 0.0, 0.6)
    return out


# Slot 5 - RPG-7.

RPG_TUBE_MODES = (420.0, 1130.0, 2150.0)   # a hollow steel tube, knocked


def r_rpg_fire(rng, src) -> np.ndarray:
    """SDRPFIR: recoilless thump and back-blast, then the motor's whistle."""
    out = np.zeros(n_of(1.45))
    place(out, crack(rng, 0.008, 250, 5000, 0.1), 0.0, 0.7)
    place(out, thump(75, 38, 0.05, 0.08, 0.5), 0.0, 1.0)
    # Back-blast: a broad whoosh that darkens.
    place(out, darkening_tail(rng, 0.6, 0.004, 0.13, 4500, 900, lo=80), 0.0, 0.7)
    # Sustainer motor: hiss plus a whistle falling as the round flies off.
    motor_t = 0.10
    n = n_of(1.3)
    t = times(n)
    amp = np.clip(t / 0.06, 0, 1) * np.exp(-t / 0.45)
    hiss = filt(rng.standard_normal(n), lambda f: butter(f, lo=1800, hi=8000))
    whistle = glide(n, 1900, 1150, 0.5) + 0.35 * glide(n, 3800, 2300, 0.5)
    place(out, hiss * amp, motor_t, 0.35)
    place(out, whistle * amp, motor_t, 0.2)
    return saturate(out, 1.5)


def r_rpg_explode(rng, src) -> np.ndarray:
    """SDRPEXP: a shaped charge: a hard crack first, then the boom."""
    out = np.zeros(n_of(1.7))
    place(out, crack(rng, 0.004, 1000, 14000, 0.05), 0.0, 1.0)
    place(out, burst_noise(rng, 0.6, 0.001, 0.09, lambda f: butter(f, lo=40, hi=4000)),
          0.003, 1.0)
    place(out, thump(62, 28, 0.12, 0.30, 1.4), 0.003, 1.3)
    place(out, darkening_tail(rng, 1.6, 0.01, 0.45, 1600, 180, lo=30), 0.01, 0.35)
    # Debris: sparse bright crackles thinning out.
    n = n_of(0.9)
    imp = np.zeros(n)
    hits = rng.uniform(0.08, 0.85, 24)
    for h in hits:
        imp[n_of(h) - 1] += rng.uniform(0.3, 1.0) * np.exp(-h / 0.4)
    place(out, filt(imp, lambda f: butter(f, lo=1800, hi=7000)), 0.0, 1.6)
    return saturate(out, 2.0)


def r_rpg_reload(rng, src) -> np.ndarray:
    """SDRPRLD: a PG-7V pushed into the muzzle: tube scrape, it seats, the detent clicks."""
    out = np.zeros(n_of(RPG7_RELOAD_WINDOW_S - 0.02))
    place(out, scrape(rng, 0.16, 900, 4000, attack=0.03, decay=0.06, grain_hz=90), 0.0, 0.35)
    place(out, ring(RPG_TUBE_MODES, 0.08, 0.25), 0.12, 0.2)
    place(out, foley(src, "metal_07", ratio=0.85, decay=0.07), 0.20, 0.8)
    place(out, thump(150, 100, 0.015, 0.03, 0.12), 0.20, 0.5)
    place(out, foley(src, "switch_01", lo=1200), 0.24, 0.6)
    return out


def r_rpg_pickup(rng, src) -> np.ndarray:
    """SDRPPKP: the launcher lifted: the wooden heat guard and a hollow steel tube."""
    out = np.zeros(n_of(0.6))
    place(out, foley(src, "wood_light_000"), 0.0, 0.5)
    place(out, foley(src, "metal_07", ratio=0.8, decay=0.1), 0.02, 0.6)
    place(out, ring(RPG_TUBE_MODES, 0.15, 0.45), 0.02, 0.2)
    place(out, cloth(rng), 0.15, 0.15)
    return out


def r_rpg_dry(rng, src) -> np.ndarray:
    """SDRPDRY: the hammer falls with no grenade in the tube: a snap, a hollow ring."""
    out = np.zeros(n_of(0.3))
    place(out, foley(src, "switch_01", ratio=0.9, lo=800), 0.0, 1.0)
    place(out, ring(RPG_TUBE_MODES, 0.09, 0.28), 0.002, 0.25)
    place(out, thump(260, 190, 0.01, 0.02, 0.08), 0.0, 0.3)
    return out


# Slot 6 - ROKS-3 flamethrower.

def r_roks3(rng, src) -> np.ndarray:
    """SDRKFIR: valve hiss and a roaring jet. Restarted every 3 tics held."""
    out = np.zeros(n_of(0.6))
    place(out, burst_noise(rng, 0.12, 0.002, 0.04, lambda f: butter(f, lo=3200, hi=12000)),
          0.0, 0.28)
    n = n_of(0.58)
    t = times(n)
    amp = np.clip(t / 0.02, 0, 1) * np.where(t < 0.22, 1.0, np.exp(-(t - 0.22) / 0.09))
    flicker = 1 + 0.35 * wobble(rng, n, 18)
    roar = filt(rng.standard_normal(n), lambda f: butter(f, lo=60, hi=900))
    tear = filt(rng.standard_normal(n), lambda f: butter(f, lo=1000, hi=3500))
    rumble = filt(rng.standard_normal(n), lambda f: butter(f, lo=30, hi=220))
    place(out, (roar + 0.35 * tear + 0.6 * rumble) * amp * flicker, 0.004, 1.0)
    return saturate(out, 1.4)


def r_roks3_reload(rng, src) -> np.ndarray:
    """SDRKRLD: a fresh fuel canister: coupled, screwed home, pressurised, igniter armed."""
    out = np.zeros(n_of(1.05))
    place(out, foley(src, "metal_01", ratio=0.85, decay=0.08), 0.0, 0.6)
    place(out, thump(120, 80, 0.02, 0.04, 0.15), 0.0, 0.4)
    at = 0.16
    for _ in range(4):                          # the coupling nut, four turns of a ratchet
        place(out, click(rng, 2200), at, 0.35)
        at += 0.07
    n = n_of(0.36)
    t = times(n)
    rise = np.clip(t / 0.3, 0, 1) ** 1.5 * np.clip((0.36 - t) / 0.02, 0, 1)
    hiss = filt(rng.standard_normal(n), lambda f: butter(f, lo=2500, hi=9000))
    place(out, hiss * rise, 0.48, 0.35)
    place(out, glide(n, 2600, 3300, 0.2) * rise, 0.48, 0.04)
    place(out, foley(src, "switch_02", ratio=1.2, lo=1500), 0.88, 0.7)
    place(out, crack(rng, 0.002, 2000, 8000, 0.02), 0.88, 0.25)
    return out


def r_roks3_pickup(rng, src) -> np.ndarray:
    """SDRKPKP: the tank pack lifted: steel canister, fuel sloshing inside, a hose."""
    out = np.zeros(n_of(0.75))
    place(out, foley(src, "metal_01", ratio=0.8, decay=0.1), 0.0, 0.6)
    place(out, foley(src, "splash_01", ratio=0.7, hi=2500, decay=0.2), 0.04, 0.55)
    place(out, cloth(rng, 0.15, 0.03, 0.05), 0.10, 0.2)
    return out


def r_roks3_dry(rng, src) -> np.ndarray:
    """SDRKDRY: tank empty: the igniter snaps and a last breath of gas sputters out."""
    out = np.zeros(n_of(0.35))
    place(out, foley(src, "switch_02", ratio=1.2, lo=1500, decay=0.02), 0.0, 0.8)
    for at in sorted(rng.uniform(0.02, 0.2, 3)):
        place(out, burst_noise(rng, 0.08, 0.004, 0.02,
                               lambda f: butter(f, lo=600, hi=3000)), at, 0.4)
    return out


# Slot 7 - hand Katyusha.

KATYUSHA_RAIL_MODES = (610.0, 1475.0, 2710.0, 4230.0)
MAINS_HZ = 50.0                # Soviet mains: the firing circuit's relay hums at 50 Hz


def r_katyusha_charge(rng, src) -> np.ndarray:
    """SDHKCHG: rails elevated by a geared crank: whine plus ratchet, locked."""
    length = tics(KATYUSHA_CHARGE_TICS)
    out = np.zeros(n_of(length + 0.12))
    n = n_of(length)
    t = times(n)
    f = 85 + 140 * (t / length) ** 0.8
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * phase) / k for k in range(1, 12))
    amp = np.clip(t / 0.03, 0, 1) * np.clip((length - t) / 0.04, 0, 1)
    place(out, filt(saw * amp, lambda fr: butter(fr, lo=180, hi=3000)), 0.0, 0.35)
    # Ratchet: teeth closer and closer together as the crank speeds up.
    at, gap = 0.02, 0.075
    while at < length - 0.05:
        place(out, click(rng, 2600), at, 0.5)
        at += gap
        gap = max(0.028, gap * 0.86)
    lock = resample(src("metal_03"), 0.7)
    place(out, lock * env(len(lock), 0.0, 0.07), length - 0.035, 0.7)
    return out


def r_katyusha_fire(rng, src) -> np.ndarray:
    """SDHKFIR: six rockets off the rails, rippled, each with a howl."""
    rockets = 6
    spacing = 0.065
    out = np.zeros(n_of(1.7))
    for i in range(rockets):
        at = i * spacing + rng.uniform(-0.008, 0.008)
        at = max(at, 0.0)
        pitch = rng.uniform(0.9, 1.12)
        g = rng.uniform(0.75, 1.0)
        place(out, crack(rng, 0.01, 300, 4500, 0.08), at, 0.6 * g)
        place(out, thump(90 * pitch, 45, 0.04, 0.06, 0.3), at, 0.6 * g)
        n = n_of(1.0)
        tt = times(n)
        amp = np.clip(tt / 0.03, 0, 1) * np.exp(-tt / 0.28)
        hiss = filt(rng.standard_normal(n), lambda f: butter(f, lo=1400, hi=7500))
        howl = glide(n, 760 * pitch, 520 * pitch, 0.4)
        place(out, (hiss * 0.8 + howl * 0.35) * amp, at + 0.01, 0.45 * g)
    place(out, darkening_tail(rng, 1.4, 0.02, 0.35, 900, 150, lo=30), 0.0, 0.5)
    return saturate(out, 1.6)


def r_katyusha_burst(rng, src) -> np.ndarray:
    """SDHKEXP: one salvo rocket: smaller and shorter than the PG-7V."""
    out = np.zeros(n_of(1.0))
    place(out, crack(rng, 0.004, 800, 9000, 0.05), 0.0, 0.8)
    place(out, burst_noise(rng, 0.4, 0.001, 0.06, lambda f: butter(f, lo=50, hi=3200)),
          0.002, 1.0)
    place(out, thump(75, 38, 0.06, 0.16, 0.8), 0.002, 1.0)
    place(out, darkening_tail(rng, 0.9, 0.006, 0.22, 1500, 250, lo=40), 0.006, 0.28)
    return saturate(out, 1.8)


def r_katyusha_reload(rng, src) -> np.ndarray:
    """SDHKRLD: rockets slid onto the rails, three quick strokes, the rack latch. 20 tics."""
    out = np.zeros(n_of(tics(KATYUSHA_RECOVERY_TICS)))
    for at in (0.0, 0.11, 0.22):
        place(out, scrape(rng, 0.09, 1200, 5000), at, 0.3)
        place(out, foley(src, "metal_02", ratio=0.7, decay=0.03), at + 0.08, 0.3)
    place(out, foley(src, "metal_09", ratio=0.8, decay=0.06), 0.38, 0.9)
    place(out, foley(src, "switch_01"), 0.385, 0.4)
    place(out, thump(120, 80, 0.02, 0.04, 0.15), 0.38, 0.4)
    return out


def r_katyusha_pickup(rng, src) -> np.ndarray:
    """SDHKPKP: the rail frame lifted: a heavy clank and the rails ringing."""
    out = np.zeros(n_of(0.8))
    place(out, foley(src, "metal_heavy_001", ratio=0.85), 0.0, 0.8)
    place(out, ring(KATYUSHA_RAIL_MODES, 0.25, 0.7), 0.002, 0.18)
    place(out, foley(src, "metal_12", ratio=0.8, decay=0.15), 0.03, 0.35)
    return out


def r_katyusha_dry(rng, src) -> np.ndarray:
    """SDHKDRY: firing switch thrown on empty rails: a toggle snap, a dead relay buzz."""
    out = np.zeros(n_of(0.25))
    place(out, foley(src, "switch_01"), 0.0, 0.9)
    n = n_of(0.09)
    t = times(n)
    buzz = sum(np.sign(np.sin(2 * np.pi * MAINS_HZ * k * t)) / k for k in (1, 3, 5))
    buzz = filt(buzz * env(n, 0.003, 0.05), lambda f: butter(f, lo=80, hi=2000))
    place(out, buzz, 0.012, 0.25)
    place(out, click(rng, 1800), 0.10, 0.4)
    return out


# --- The lump table -----------------------------------------------------------
# `wired`: True when src/zscript/weapons plays the logical name today, so the
# overlay replaces a sound the player already hears. False: the sound needs a
# hook from mod-engineer first (WEAPON-SOUNDS.md §6) and is heard in the
# overlay only with `playsound <logical>` from the console.

@dataclass(frozen=True)
class Lump:
    name: str
    logical: str
    weapon: str
    event: str            # fire / reload / pickup / dry / swing / hit / wall / ...
    hook: str             # where the engine plays it, or where it is proposed
    recipe: Callable
    sources: tuple[str, ...] = ()
    peak_dbfs: float = DEFAULT_PEAK_DBFS
    length_s: tuple[float, float] = (0.05, 2.0)   # sane bounds, checked by tests
    wired: bool = False
    sweep: bool = False                            # also rendered as takes B and C
    placeholder: str | None = None                 # Freedoom lump heard today, if any
    loudness_db: float | None = None               # short-term ceiling, handling sounds


LUMPS: tuple[Lump, ...] = (
    # Slot 1 - ice axe (D40): replaces SDSHSWG / SDSHHIT; see RETIRED_LUMPS.
    Lump("SDAXSWG", "sd/weapon/iceaxe/swing", "ice axe", "swing",
         "Fire, first frame (T10: two lines written out in SNDINFO's header)",
         r_iceaxe_swing, (), length_s=(0.18, 0.35), sweep=True),
    Lump("SDAXHIT", "sd/weapon/iceaxe/hit", "ice axe", "hit",
         "A_SD_IceAxeSwing, when the blow finds a target",
         r_iceaxe_hit, ("punch_heavy_000", "soft_heavy_001"), length_s=(0.15, 0.45),
         wired=True, sweep=True, placeholder="DSPUNCH"),
    Lump("SDAXWAL", "sd/weapon/iceaxe/wall", "ice axe", "wall",
         "proposed: the blow hits a wall (puff AttackSound, or LineAttack's puff)",
         r_iceaxe_wall, ("mining_002",), length_s=(0.2, 0.6), sweep=True),
    Lump("SDAXPKP", "sd/weapon/iceaxe/pickup", "ice axe", "pickup",
         "proposed: Inventory.PickupSound", r_iceaxe_pickup,
         ("wood_light_001", "metal_light_000"), peak_dbfs=PICKUP_PEAK_DBFS,
         length_s=(0.2, 0.6), placeholder="DSWPNUP"),
    # Slot 2 - TT-33.
    Lump("SDTTFIR", "sd/weapon/tokarev/fire", "TT-33", "fire", "Fire (AttackSound)",
         r_tokarev, ("switch_01",), length_s=(0.25, 0.65), wired=True, sweep=True,
         placeholder="DSPISTOL"),
    Lump("SDTTRLD", "sd/weapon/tokarev/reload", "TT-33", "reload",
         "proposed: no reload state exists (a Select-state chamber check, or later)",
         r_tokarev_reload, ("switch_01", "metal_02", "switch_02", "metal_11"),
         peak_dbfs=RELOAD_PEAK_DBFS, length_s=(0.7, 1.0)),
    Lump("SDTTPKP", "sd/weapon/tokarev/pickup", "TT-33", "pickup",
         "proposed: Inventory.PickupSound", r_tokarev_pickup,
         ("metal_light_001", "switch_02", "metal_11"), peak_dbfs=PICKUP_PEAK_DBFS,
         length_s=(0.25, 0.55), placeholder="DSWPNUP"),
    Lump("SDTTDRY", "sd/weapon/tokarev/dry", "TT-33", "dry",
         "proposed: trigger pulled with no Clip", r_tokarev_dry, ("switch_01",),
         peak_dbfs=DRY_PEAK_DBFS, length_s=(0.05, 0.2)),
    # Slot 3 - IZh-58.
    Lump("SDIZFIR", "sd/weapon/izh/fire", "IZh-58", "fire", "Fire (AttackSound)",
         r_izh_fire, (), length_s=(0.6, 1.2), wired=True, sweep=True,
         placeholder="DSSHOTGN"),
    Lump("SDIZRLD", "sd/weapon/izh/reload", "IZh-58", "reload", "Reload, frame SHTG D",
         r_izh_reload, ("switch_02", "metal_03", "wooden_03", "metal_09", "switch_01"),
         length_s=(0.75, 0.95), wired=True, placeholder="DSSGCOCK"),
    Lump("SDIZPKP", "sd/weapon/izh/pickup", "IZh-58", "pickup",
         "proposed: Inventory.PickupSound", r_izh_pickup,
         ("wood_medium_000", "switch_02", "metal_09", "switch_01"),
         peak_dbfs=PICKUP_PEAK_DBFS, length_s=(0.35, 0.75), placeholder="DSWPNUP"),
    Lump("SDIZDRY", "sd/weapon/izh/dry", "IZh-58", "dry",
         "proposed: trigger pulled with no Shell", r_izh_dry, ("switch_01",),
         peak_dbfs=DRY_PEAK_DBFS, length_s=(0.05, 0.2)),
    # Slot 4 - PPSh-41.
    Lump("SDPPFIR", "sd/weapon/ppsh/fire", "PPSh-41", "fire",
         "Fire (AttackSound), every 3 tics", r_ppsh, ("switch_02", "spring_04"),
         peak_dbfs=-2.0, length_s=(0.15, 0.5), wired=True, sweep=True,
         placeholder="DSPISTOL"),
    Lump("SDPPRLD", "sd/weapon/ppsh/reload", "PPSh-41", "reload",
         "proposed: no reload state exists (a Select-state drum change, or later)",
         r_ppsh_reload,
         ("switch_02", "metal_03", "spring_04", "metal_09", "spring_06", "switch_01",
          "metal_02"),
         peak_dbfs=RELOAD_PEAK_DBFS, length_s=(0.9, 1.2)),
    Lump("SDPPPKP", "sd/weapon/ppsh/pickup", "PPSh-41", "pickup",
         "proposed: Inventory.PickupSound", r_ppsh_pickup,
         ("wood_medium_002", "metal_light_003", "spring_04", "switch_02"),
         peak_dbfs=PICKUP_PEAK_DBFS, length_s=(0.3, 0.65), placeholder="DSWPNUP"),
    Lump("SDPPDRY", "sd/weapon/ppsh/dry", "PPSh-41", "dry",
         "proposed: trigger pulled with no Clip", r_ppsh_dry, ("metal_02", "switch_02"),
         peak_dbfs=DRY_PEAK_DBFS, length_s=(0.05, 0.25)),
    # Slot 5 - RPG-7.
    Lump("SDRPFIR", "sd/weapon/rpg7/fire", "RPG-7", "fire", "SD_Pg7Grenade SeeSound",
         r_rpg_fire, (), length_s=(0.8, 1.5), wired=True, placeholder="DSRLAUNC"),
    Lump("SDRPEXP", "sd/weapon/rpg7/explode", "RPG-7", "explode",
         "SD_Pg7Grenade DeathSound", r_rpg_explode, (), length_s=(0.8, 1.8),
         wired=True, placeholder="DSBAREXP"),
    Lump("SDRPRLD", "sd/weapon/rpg7/reload", "RPG-7", "reload",
         "proposed: 4 tics into the 14-tic launch frame, after the round has gone",
         r_rpg_reload, ("metal_07", "switch_01"), peak_dbfs=RELOAD_PEAK_DBFS,
         length_s=(0.25, 0.45)),
    Lump("SDRPPKP", "sd/weapon/rpg7/pickup", "RPG-7", "pickup",
         "proposed: Inventory.PickupSound", r_rpg_pickup, ("wood_light_000", "metal_07"),
         peak_dbfs=PICKUP_PEAK_DBFS, length_s=(0.3, 0.65), placeholder="DSWPNUP"),
    Lump("SDRPDRY", "sd/weapon/rpg7/dry", "RPG-7", "dry",
         "proposed: trigger pulled with no RocketAmmo", r_rpg_dry, ("switch_01",),
         peak_dbfs=DRY_PEAK_DBFS, length_s=(0.05, 0.32)),
    # Slot 6 - ROKS-3.
    Lump("SDRKFIR", "sd/weapon/roks3/fire", "ROKS-3", "fire",
         "A_SD_FireRoks3, every 3 tics", r_roks3, (), peak_dbfs=-3.0,
         length_s=(0.3, 0.65), wired=True, placeholder="DSFLAME"),
    Lump("SDRKRLD", "sd/weapon/roks3/reload", "ROKS-3", "reload",
         "proposed: no reload state exists (a Select-state canister change, or later)",
         r_roks3_reload, ("metal_01", "switch_02"), peak_dbfs=RELOAD_PEAK_DBFS,
         length_s=(0.8, 1.1)),
    Lump("SDRKPKP", "sd/weapon/roks3/pickup", "ROKS-3", "pickup",
         "proposed: Inventory.PickupSound", r_roks3_pickup, ("metal_01", "splash_01"),
         peak_dbfs=PICKUP_PEAK_DBFS, length_s=(0.3, 0.8), placeholder="DSWPNUP"),
    Lump("SDRKDRY", "sd/weapon/roks3/dry", "ROKS-3", "dry",
         "proposed: trigger pulled with no Cell", r_roks3_dry, ("switch_02",),
         peak_dbfs=DRY_PEAK_DBFS, length_s=(0.1, 0.35)),
    # Slot 7 - hand Katyusha.
    Lump("SDHKCHG", "sd/weapon/katyusha/charge", "hand Katyusha", "charge",
         "Fire, frame BFGG A (20 tics)", r_katyusha_charge, ("metal_03",),
         length_s=(0.5, 0.75), wired=True, placeholder="DSBFG"),
    Lump("SDHKFIR", "sd/weapon/katyusha/fire", "hand Katyusha", "fire",
         "A_SD_FireKatyusha", r_katyusha_fire, (), length_s=(0.9, 1.8), wired=True,
         placeholder="DSRLAUNC"),
    # Six of these can sound at once (one per rocket): 5 dB lower than the rest.
    Lump("SDHKEXP", "sd/weapon/katyusha/burst", "hand Katyusha", "burst",
         "SD_KatyushaRocket DeathSound", r_katyusha_burst, (), peak_dbfs=-6.0,
         length_s=(0.5, 1.1), wired=True, placeholder="DSBAREXP"),
    Lump("SDHKRLD", "sd/weapon/katyusha/reload", "hand Katyusha", "reload",
         "proposed: the 20-tic BFGG B A_ReFire frame after the salvo",
         r_katyusha_reload, ("metal_02", "metal_09", "switch_01"),
         peak_dbfs=RELOAD_PEAK_DBFS, length_s=(0.4, 0.58)),
    Lump("SDHKPKP", "sd/weapon/katyusha/pickup", "hand Katyusha", "pickup",
         "proposed: Inventory.PickupSound", r_katyusha_pickup,
         ("metal_heavy_001", "metal_12"), peak_dbfs=PICKUP_PEAK_DBFS,
         length_s=(0.4, 0.85), placeholder="DSWPNUP"),
    Lump("SDHKDRY", "sd/weapon/katyusha/dry", "hand Katyusha", "dry",
         "proposed: trigger pulled with fewer than 40 Cell", r_katyusha_dry,
         ("switch_01",), peak_dbfs=DRY_PEAK_DBFS, length_s=(0.1, 0.3)),
)
LUMPS_BY_NAME = {lump.name: lump for lump in LUMPS}

# D40: the shovel's requested lumps, retired, and the ice axe's that replace
# them (MOD-SPEC §6.2, renamed by mod-engineer on 2026-10-13).
RETIRED_LUMPS: dict[str, str] = {"SDSHSWG": "SDAXSWG", "SDSHHIT": "SDAXHIT"}

# Takes: varispeed ratios. A is the recipe as written.
TAKES: dict[str, float] = {"A": 1.0, "B": 0.92, "C": 1.08}
TAKE_NOTES = {"A": "as designed", "B": "8 % slower: lower, heavier", "C": "8 % faster: higher, drier"}
# The take each sweep lump ships with. The CEO's pick goes here.
CHOSEN_TAKE: dict[str, str] = {}


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode("ascii"))


def render(lump: Lump, sources: Sources, take: str | None = None) -> np.ndarray:
    """-> float samples in -1..1, finished. Raises MissingSource."""
    if not sources.available(lump.sources):
        missing = [k for k in lump.sources if not source_path(k, sources.dir).is_file()]
        why = "ffmpeg is not on the PATH" if ffmpeg_path() is None else f"missing {missing}"
        raise MissingSource(f"{lump.name}: {why}")
    take = take or CHOSEN_TAKE.get(lump.name, "A")
    rng = np.random.default_rng(seed_of(lump.name))
    x = lump.recipe(rng, sources)
    if TAKES[take] != 1.0:
        x = resample(x, TAKES[take])
    return levelled(finish(x, lump.peak_dbfs), loudness_of(lump))


EVENT_LOUDNESS_DB = {"reload": RELOAD_LOUDNESS_DB, "pickup": PICKUP_LOUDNESS_DB,
                     "dry": DRY_LOUDNESS_DB}


def loudness_of(lump: Lump) -> float | None:
    return lump.loudness_db if lump.loudness_db is not None else EVENT_LOUDNESS_DB.get(lump.event)


# --- Previews (not lumps) -----------------------------------------------------

def burst(shot: np.ndarray, interval_s: float, rounds: int, cut: bool) -> np.ndarray:
    """What a held trigger sounds like. cut=True: each round stops the last one
    (one CHAN_WEAPON), with a 2 ms fade; cut=False: rounds overlap."""
    step = n_of(interval_s)
    out = np.zeros(step * (rounds - 1) + len(shot))
    fade = n_of(0.002)
    for i in range(rounds):
        seg = shot.copy()
        if cut and i < rounds - 1:
            seg = seg[:step]
            seg[-fade:] *= np.linspace(1, 0, fade)
        out[i * step:i * step + len(seg)] += seg
    return out / np.max(np.abs(out)) * 10 ** (DEFAULT_PEAK_DBFS / 20)


def ppsh_previews(shot: np.ndarray) -> dict[str, np.ndarray]:
    engine = tics(PPSH_TICS_PER_ROUND)
    real = 60.0 / PPSH_REAL_RPM
    rounds = 24
    return {
        "SDPPFIR_burst_700rpm_engine.wav": burst(shot, engine, rounds, cut=True),
        "SDPPFIR_burst_900rpm_real.wav": burst(shot, real, rounds, cut=True),
        "SDPPFIR_burst_700rpm_overlap.wav": burst(shot, engine, rounds, cut=False),
    }


# --- Overlay PK3 --------------------------------------------------------------

SNDINFO_HEADER = """\
// Audition overlay - tools/audio/gen_weapon_sfx.py. NOT part of the mod.
// Load AFTER dist/sovietdoom.pk3 so these definitions win (later SNDINFO
// definitions of a logical name replace earlier ones: NOT VERIFIED in this
// engine, see docs/sound/WEAPON-SOUNDS.md section 7). Delete this PK3 and
// everything is as it was; src/lumps/SNDINFO is never touched.
// Names marked "needs a hook" are defined but nothing in the mod plays them
// yet (WEAPON-SOUNDS.md section 6); hear them from the console, e.g.
//     playsound sd/weapon/tokarev/reload
"""


def sndinfo_text(lumps) -> str:
    lines = [SNDINFO_HEADER]
    for lump in lumps:
        note = "" if lump.wired else "   // needs a hook"
        lines.append(f"{lump.logical:<28s}{lump.name}{note}\n")
    return "".join(lines)


def write_pk3(path: Path, rendered: dict[str, bytes]) -> None:
    lumps = [lump for lump in LUMPS if lump.name in rendered]   # slot order
    entries = [("SNDINFO", sndinfo_text(lumps).encode("ascii"))]
    entries += [(f"{SOUNDS_DIR_IN_PK3}/{lump.name}.wav", rendered[lump.name]) for lump in lumps]
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)


# --- OGG and the Freedoom placeholders ---------------------------------------

def ogg_bytes(wav: bytes) -> bytes | None:
    """WAV bytes -> Vorbis OGG bytes through ffmpeg; None without ffmpeg."""
    exe = ffmpeg_path()
    if exe is None:
        return None
    return subprocess.run(
        [exe, "-v", "error", "-nostdin", "-f", "wav", "-i", "-",
         "-c:a", "libvorbis", "-q:a", OGG_QUALITY,
         "-fflags", "+bitexact", "-flags:a", "+bitexact", "-f", "ogg", "-"],
        input=wav, capture_output=True, check=True).stdout


DMX_FORMAT = 3
DMX_HEADER = 8
DMX_PAD = 16          # DMX pads the samples with 16 bytes on each side


def dmx_to_wav(lump: bytes) -> bytes:
    """Doom's DMX digital sound (8-bit unsigned) -> 16-bit WAV at its own rate."""
    fmt, rate, count = struct.unpack("<HHI", lump[:DMX_HEADER])
    if fmt != DMX_FORMAT:
        raise ValueError(f"not a DMX sound (format {fmt})")
    body = np.frombuffer(lump[DMX_HEADER + DMX_PAD:DMX_HEADER + count - DMX_PAD], dtype=np.uint8)
    return wav_bytes((body.astype(np.float64) - 128) / 128, rate)


def placeholder_wav(name: str, iwad: Path = IWAD_PATH) -> bytes | None:
    """The Freedoom lump the game plays today, as WAV, or None if unavailable."""
    if not iwad.is_file():
        return None
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from sdbuild.wad import read_lump   # noqa: E402 - only needed for the preview
    try:
        return dmx_to_wav(read_lump(iwad.read_bytes(), name))
    except (KeyError, ValueError):
        return None


# --- Driver -------------------------------------------------------------------

@dataclass
class Result:
    rendered: dict[str, bytes] = field(default_factory=dict)
    samples: dict[str, np.ndarray] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)


def build(names=None, sources: Sources | None = None) -> Result:
    """Render the lumps in memory. Writes nothing."""
    sources = sources or Sources()
    result = Result()
    for lump in LUMPS:
        if names and lump.name not in names:
            continue
        try:
            x = render(lump, sources)
        except MissingSource as exc:
            result.skipped[lump.name] = str(exc)
            continue
        result.samples[lump.name] = x
        result.rendered[lump.name] = wav_bytes(x)
    return result


def manifest_text(result: Result, sources: Sources) -> str:
    lines = ["# gen_weapon_sfx.py manifest: lump, take, seconds, peak dBFS, RMS dBFS, loudest 50 ms, SHA-256, sources",
             "# sources: pack ID (docs/sound/ENEMY-SOUNDS.md section 2.1), file, SHA-256",
             ""]
    for name in sorted(result.rendered):
        x = result.samples[name]
        peak = 20 * np.log10(np.max(np.abs(x)))
        digest = hashlib.sha256(result.rendered[name]).hexdigest()
        take = CHOSEN_TAKE.get(name, "A")
        lines.append(f"{name}  take {take}  {len(x) / SR:.3f} s  peak {peak:.1f} dBFS  "
                     f"RMS {rms_dbfs(x):.1f} dBFS  short-term {short_term_db(x):.1f} dB  {digest}")
        lump = LUMPS_BY_NAME[name]
        if not lump.sources:
            lines.append("    synthesis only (SYN)")
        for key in lump.sources:
            pack, rel = SOURCE_FILES[key]
            lines.append(f"    {pack}  {rel}  {sha256_file(source_path(key, sources.dir))}")
    for name, why in sorted(result.skipped.items()):
        lines.append(f"{name}  SKIPPED: {why}")
    return "\n".join(lines) + "\n"


def provenance_tsv(result: Result, sources: Sources) -> str:
    """Same columns as work/audio/sfx/enemies/PROVENANCE.tsv."""
    rows = ["lump\troute\tpack\tfile\tsegment\tsha256"]
    for lump in LUMPS:
        if lump.name not in result.rendered:
            continue
        route = "B+C" if lump.sources else "C"
        for key in lump.sources:
            pack, rel = SOURCE_FILES[key]
            rows.append(f"{lump.name}\t{route}\t{pack}\t{Path(rel).name}\t\t"
                        f"{sha256_file(source_path(key, sources.dir))}")
        rows.append(f"{lump.name}\t{route}\tSYN\tgen_weapon_sfx.py\t\t")
    return "\n".join(rows) + "\n"


def plan_text() -> str:
    lines = [f"{'lump':8s} {'logical name':28s} {'wired':5s} {'peak':>5s}  sources"]
    for lump in LUMPS:
        src = ", ".join(lump.sources) or "SYN"
        lines.append(f"{lump.name:8s} {lump.logical:28s} {'yes' if lump.wired else 'no':5s} "
                     f"{lump.peak_dbfs:5.1f}  {src}")
    lines.append(f"{len(LUMPS)} lumps, {sum(lump.wired for lump in LUMPS)} wired today, "
                 f"{sum(lump.sweep for lump in LUMPS)} with takes B and C")
    return "\n".join(lines)


# --- The CEO's preview page ------------------------------------------------------

PREVIEW_CSS = """
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1f;--mute:#6b6862;--red:#b3261e;--line:#dcd8cf;--ok:#2e7d32;--warn:#a46a00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1b1c1f;--card:#26282c;--ink:#e8e6e0;--mute:#9a9892;--red:#e0544b;--line:#3a3d44;--ok:#7cc47f;--warn:#e0b44b}}
:root[data-theme="dark"]{--bg:#1b1c1f;--card:#26282c;--ink:#e8e6e0;--mute:#9a9892;--red:#e0544b;--line:#3a3d44;--ok:#7cc47f;--warn:#e0b44b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif}
header{padding:20px 16px;border-bottom:2px solid var(--red)}h1{margin:0 0 6px;font-size:22px}
.wrap{max-width:1100px;margin:0 auto}.meta{color:var(--mute);font-size:12px}
section{padding:16px;border-top:1px solid var(--line)}h2{font-size:17px;margin:0 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px;margin:0 0 10px}
.card h3{margin:0;font-size:15px}.card h3 code{font-size:13px;color:var(--mute)}
.desc{margin:4px 0 8px;color:var(--mute)}
.row{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.clip{display:flex;flex-direction:column;gap:2px;font-size:11px;color:var(--mute)}
.clip b{color:var(--ink)}audio{width:240px;max-width:100%;height:32px}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:3px;border:1px solid var(--line);margin-left:6px}
.tag.ok{color:var(--ok);border-color:var(--ok)}.tag.hook{color:var(--warn);border-color:var(--warn)}
.src{font-size:11px;color:var(--mute);margin-top:6px}
ul{margin:6px 0;padding-left:20px}
"""


def _audio_tag(wav: bytes) -> str:
    ogg = ogg_bytes(wav)
    mime, data = ("audio/ogg", ogg) if ogg else ("audio/wav", wav)
    return (f'<audio controls preload="none" src="data:{mime};base64,'
            f'{base64.b64encode(data).decode("ascii")}"></audio>')


def _clip(label: str, wav: bytes | None, detail: str = "") -> str:
    if wav is None:
        return (f'<div class="clip"><b>{html.escape(label)}</b>'
                f'<span>{html.escape(detail or "silent today")}</span></div>')
    return (f'<div class="clip"><b>{html.escape(label)}</b>{_audio_tag(wav)}'
            f'<span>{html.escape(detail)}</span></div>')


def preview_html(result: Result, sources: Sources, stamp: str) -> str:
    """One self-contained page: every lump, its takes and today's placeholder."""
    cards: dict[str, list[str]] = {}
    for lump in LUMPS:
        if lump.name not in result.rendered:
            continue
        x = result.samples[lump.name]
        clips = []
        today = placeholder_wav(lump.placeholder) if lump.placeholder else None
        clips.append(_clip("Today", today,
                           f"Freedoom {lump.placeholder}" if lump.placeholder else "silent today"))
        if lump.sweep:
            for take, note in TAKE_NOTES.items():
                xt = x if take == CHOSEN_TAKE.get(lump.name, "A") else render(lump, sources, take)
                clips.append(_clip(f"Draft, take {take}", wav_bytes(xt),
                                   f"{note}; {len(xt) / SR:.2f} s"))
        else:
            clips.append(_clip("Draft", result.rendered[lump.name],
                               f"{len(x) / SR:.2f} s, peak {lump.peak_dbfs:.0f} dBFS"))
        if lump.name == "SDPPFIR":
            for fname, xb in ppsh_previews(x).items():
                label = fname.replace("SDPPFIR_burst_", "Burst ").replace(".wav", "").replace("_", " ")
                clips.append(_clip(label, wav_bytes(xb), "24 rounds"))
        status = ('<span class="tag ok">heard in game today</span>' if lump.wired else
                  '<span class="tag hook">needs a hook from mod-engineer</span>')
        srcs = ", ".join(f"{SOURCE_FILES[k][0]} {Path(SOURCE_FILES[k][1]).name}"
                         for k in lump.sources) or "our synthesis only"
        doc = (lump.recipe.__doc__ or "").strip().split("\n")[0]
        doc = doc.split(": ", 1)[1] if ": " in doc else doc
        cards.setdefault(lump.weapon, []).append(
            f'<div class="card"><h3>{html.escape(lump.event)} <code>{lump.name} · '
            f'{html.escape(lump.logical)}</code>{status}</h3>'
            f'<p class="desc">{html.escape(doc)}</p>'
            f'<div class="row">{"".join(clips)}</div>'
            f'<div class="src">Where it plays: {html.escape(lump.hook)}. Sources: '
            f'{html.escape(srcs)}.</div></div>')
    body = "".join(f'<section><h2>{html.escape(w)}</h2>{"".join(c)}</section>'
                   for w, c in cards.items())
    wired = sum(1 for lump in LUMPS if lump.wired and lump.name in result.rendered)
    total = len(result.rendered)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arsenal sound drafts</title><style>{PREVIEW_CSS}</style></head>
<body><header><div class="wrap"><h1>Soviet Doom — the arsenal's sounds, drafts for the CEO</h1>
<div class="meta">{html.escape(stamp)} · F4 · tools/audio/gen_weapon_sfx.py ·
plan and provenance: docs/sound/WEAPON-SOUNDS.md · nothing here is in the game</div>
<ul>
<li><b>{total} drafts</b>: fire, reload or break-open, pickup and empty click for the six guns,
the RPG-7's and the Katyusha's other events, and the ice axe that replaces the shovel (D40).</li>
<li><b>{wired}</b> replace a sound the game already plays ("heard in game today"); the rest need
a small hook from mod-engineer before the engine can play them.</li>
<li>"Today" is the Freedoom stand-in you hear now, for comparison. Where a card has takes A, B
and C, point at one; A ships unless you say otherwise.</li>
<li>Nobody on the team has listened to these: the agent that made them cannot hear. Every
number on the cards was measured; the taste is yours.</li>
</ul></div></header><div class="wrap">{body}</div></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="+", metavar="LUMP", help="build only these lumps")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--pk3", type=Path, default=PK3_PATH)
    ap.add_argument("--sources", type=Path, default=SOURCES_DIR)
    ap.add_argument("--no-pk3", action="store_true")
    ap.add_argument("--no-ogg", action="store_true", help="do not write ogg/<LUMP>.ogg")
    ap.add_argument("--preview", type=Path, metavar="HTML",
                    help="also write the CEO's preview page here")
    ap.add_argument("--list", action="store_true", help="print the plan and write nothing")
    args = ap.parse_args(argv)

    if args.list:
        print(plan_text())
        return 0
    if args.only:
        unknown = [n for n in args.only if n.upper() not in LUMPS_BY_NAME]
        if unknown:
            ap.error(f"unknown lump(s): {', '.join(unknown)}")
    names = {n.upper() for n in args.only} if args.only else None
    sources = Sources(args.sources)
    result = build(names, sources)

    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in result.rendered.items():
        (args.out / f"{name}.wav").write_bytes(data)
        x = result.samples[name]
        print(f"  {name}  {len(x) / SR:5.3f} s  peak {20 * np.log10(np.max(np.abs(x))):5.1f} dBFS"
              f"  RMS {rms_dbfs(x):5.1f} dBFS  short-term {short_term_db(x):5.1f} dB")
    if not args.no_ogg and ffmpeg_path() and result.rendered:
        (args.out / "ogg").mkdir(exist_ok=True)
        for name, data in result.rendered.items():
            (args.out / "ogg" / f"{name}.ogg").write_bytes(ogg_bytes(data))
        print(f"  ogg/: {len(result.rendered)} files")
    if "SDPPFIR" in result.samples:
        preview_dir = args.out / "preview"
        preview_dir.mkdir(exist_ok=True)
        for fname, x in ppsh_previews(result.samples["SDPPFIR"]).items():
            (preview_dir / fname).write_bytes(wav_bytes(x))
            print(f"  preview/{fname}")
    (args.out / "MANIFEST.txt").write_text(manifest_text(result, sources), encoding="utf-8")
    (args.out / "PROVENANCE.tsv").write_text(provenance_tsv(result, sources), encoding="utf-8")
    for name, why in sorted(result.skipped.items()):
        print(f"  SKIPPED {why}", file=sys.stderr)
    if not args.no_pk3 and result.rendered:
        write_pk3(args.pk3, result.rendered)
        print(f"packed {args.pk3} ({args.pk3.stat().st_size} B, {len(result.rendered)} lumps)")
    if args.preview and result.rendered:
        stamp = args.preview.stem.split("_F")[0] if "_F" in args.preview.stem else args.preview.stem
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(preview_html(result, sources, stamp), encoding="utf-8")
        print(f"preview {args.preview} ({args.preview.stat().st_size} B)")
    return 0 if result.rendered else 1


if __name__ == "__main__":
    sys.exit(main())
