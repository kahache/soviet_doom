#!/usr/bin/env python3
"""Alternatives for the five weapon sounds the CEO did not approve (D74).

On the M3 listening sheet (`docs/art/previews/2026-10-14_2355_M3_listening-sheet.html`)
the CEO marked three drafts NO (`SDTTPKP`, `SDIZRLD`, `SDRKFIR`) and two ?
(`SDAXPKP`, `SDIZPKP`). This file makes THREE clearly different takes on
each, not variations of the rejected recipe: a different gesture or a
different material per alternative. The drafts of `gen_weapon_sfx.py` are
not touched; this file imports its DSP primitives and its constants (the
engine timings), so a change there is a change here.

Rules kept (docs/sound/WEAPON-SOUNDS.md §2):

- Sources: our synthesis plus files of the two CC0 packs already on disk
  under D36 (`OGA-100`, `KEN-IMP`, pack rows in `docs/sound/ENEMY-SOUNDS.md`
  §2.1). No download. No `shot_*` file. No foreign clip ships alone: each is
  cut, re-pitched, filtered, enveloped and layered with synthesis. Every
  source file's SHA-256 is pinned below and checked by the tests.
- Loudness (D74, N9): the drafts were measured 6-18 dB under the Freedoom
  sound each replaces, so these are levelled TOWARDS that sound: peak at
  -1 dBFS (Freedoom's are at 0 dBFS, 8-bit and clipped) and the loudest
  50 ms (A-weighted mean square) within a fixed allowance of the Freedoom
  lump's own. They get there by a soft saturation whose drive is searched,
  so they are denser, not only louder.
- Laptop speakers: at least `MIN_SHARE_ABOVE_300HZ` of each sound's energy
  sits above 300 Hz (the sheet flagged sounds with >90 % below).
- `SDRKFIR` fits its use: `roks3.zs` restarts it every 3 tics on
  `CHAN_WEAPON` while the trigger is held (ASSUMPTION, WEAPON-SOUNDS §3: a
  restart cuts the sound already playing). So the first 3 tics (3780
  samples at 44.1 kHz, exactly) are one period of a periodic jet: cut and
  restarted, it joins itself. After those 3 tics comes the release tail,
  heard only when the trigger is let go (the last restart plays out).
- `SDIZRLD` snaps shut on frame A of the reload (22 tics), like the draft.

Outputs (gitignored `work/`):

    work/audio/alt/<LUMP>_alt<N>.ogg      the 15 alternatives (what the page plays)
    work/audio/alt/wav/<LUMP>_alt<N>.wav  16-bit masters
    work/audio/alt/preview/*.ogg          the flamethrower held for 1.2 s, each way
    work/audio/alt/MANIFEST.txt           levels against the Freedoom sound, sources
    work/audio/alt/PROVENANCE.tsv         one row per source file per alternative

Run:

    .venv/Scripts/python.exe tools/audio/gen_weapon_alts.py --list
    .venv/Scripts/python.exe tools/audio/gen_weapon_alts.py \\
        --page docs/art/previews/<YYYY-MM-DD_HHMM>_M3_listening-alternatives.html
    .venv/Scripts/python.exe -m unittest tests.test_gen_weapon_alts -v

GPL-3.0 (the script); its output is CC BY-NC-SA 4.0 (D15).
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import wave
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_weapon_sfx as gws  # noqa: E402
from gen_weapon_sfx import (  # noqa: E402
    SR, butter, bump, click, cloth, filt, finish, grit, n_of, place,
    ring, scrape, shape, thump, tics, times, wav_bytes)

PROJECT_ROOT = gws.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "audio" / "alt"
REJECTED_OGG_DIR = gws.OUT_DIR / "ogg"                       # the drafts the CEO judged
FREEDOOM_PREVIEW_DIR = PROJECT_ROOT / "work" / "audio" / "preview" / "freedoom"

ALT_COUNT = 3
PEAK_DBFS = -1.0                 # the project's headroom (ENEMY-SOUNDS §6)
PEAK_TOLERANCE_DB = 0.3
LOUDNESS_TOLERANCE_DB = 1.0      # each alternative lands within this of its target
MIN_SHARE_ABOVE_300HZ = 0.5      # laptop speakers (the sheet's "bass-only" flag)
BASS_EDGE_HZ = 300.0
MAX_DRIVE = 24.0                 # the jet's saturation drive ceiling for the level search
DRIVE_SEARCH_STEPS = 22

# How far under the Freedoom lump's loudest 50 ms (A-weighted) each kind is
# set. The jet is continuous like DSFLAME and matches it; a pickup stays
# 3 dB under its stand-in (handling under the guns, as WEAPON-SOUNDS §4
# wants, and Freedoom's 8-bit chirps are squarer than any knock can be
# without being squared off). The break-open is a sequence whose snap must
# stay its loudest moment: levelled harder, the limiter would flatten every
# step to the snap's height, so it sits 5 dB under DSSGCOCK.
ALLOWANCE_DB = {"pickup": 3.0, "reload": 5.0, "fire": 0.0}

# The Freedoom lumps these replace, measured from iwads/freedoom2.wad 0.13.0
# (11025 Hz, 8-bit DMX) with the rulers below; a test re-measures them.
# name -> (peak dBFS, A-weighted loudest 50 ms dB, plain RMS dBFS)
FREEDOOM_LEVELS: dict[str, tuple[float, float, float]] = {
    "DSWPNUP": (0.0, -5.2, -12.4),
    "DSSGCOCK": (0.0, -4.4, -11.7),
    "DSFLAME": (0.0, -11.1, -11.0),
}
LEVEL_TOLERANCE_DB = 0.2

# --- Engine facts (read from src/zscript/weapons/*.zs; tests read them again) --
ROKS3_TICS_PER_JET = 3                                   # roks3.zs: PLSG A 3 Bright A_SD_FireRoks3
JET_LOOP_N = SR * ROKS3_TICS_PER_JET // gws.TICS_PER_SECOND   # 3780 samples, exact
assert JET_LOOP_N * gws.TICS_PER_SECOND == SR * ROKS3_TICS_PER_JET
HELD_PREVIEW_S = 1.2             # the flame held for this long on the page
IZH_CLOSE_S = tics(gws.IZH_RELOAD_CLOSE_TICS) - 0.01   # as the draft: 10 ms before frame A
IZH_SNAP_TOLERANCE_S = 0.04
FADE_OUT_S = gws.FADE_OUT_S

# --- Sources -------------------------------------------------------------------
# key -> (pack, path under work/audio/sfx_sources/, SHA-256 of that file).
KEN = gws.KEN
ALT_SOURCES: dict[str, tuple[str, str, str]] = {
    "switch_01": ("OGA-100", "oga-100/extracted/switch_01.ogg",
                  "a24004ad0adbc08571324456963533c496bd27cf4808b40cb90833dc06b95792"),
    "switch_02": ("OGA-100", "oga-100/extracted/switch_02.ogg",
                  "769dca6ccbea5c33cef602cdaa6ab0350b0dc2b093f02eae36f33e2552036f67"),
    "metal_02": ("OGA-100", "oga-100/extracted/metal_02.ogg",
                 "545c2d698e72e1a3f0f22407fc0567a1f1041d9dbeff528bef0947284b45fdf2"),
    "metal_06": ("OGA-100", "oga-100/extracted/metal_06.ogg",
              "5409b5a3a21e800b9dbfafe1ab0dfb219a53eca2a0654fa932ff04b4b5d4371b"),
    "metal_11": ("OGA-100", "oga-100/extracted/metal_11.ogg",
                 "8f52c3a878e87ea2abb8f7a9fba90d0ec32034393661ddf87ba2b2b086024195"),
    "key_open_02": ("OGA-100", "oga-100/extracted/key_open_02.ogg",
                 "d1bdc1f001837e370902bf332bf3c08eef16bb9356d0c41e8ea1670fca76fa72"),
    "spring_07": ("OGA-100", "oga-100/extracted/spring_07.ogg",
               "a53ae8b8aea0d6a08a04633b5c4cdb4d5dbde4933e42cc81e3408aa6db271ef3"),
    "spring_08": ("OGA-100", "oga-100/extracted/spring_08.ogg",
               "55d3a9b9de5921f8c541bd2825c37b29d964ebdef9b5bb56e8629278e8145041"),
    "metal_light_001": ("KEN-IMP", KEN + "impactMetal_light_001.ogg",
                        "fba69c467ddd85da7b1d82e259f936b876d9ba6a3d6f1b24bdd10468e46bfe08"),
    "metal_light_002": ("KEN-IMP", KEN + "impactMetal_light_002.ogg",
                        "25a96f90a9a1f88a531e824e126f0519504625e5635e65a72e4f31611428db29"),
    "metal_light_003": ("KEN-IMP", KEN + "impactMetal_light_003.ogg",
                        "92d5db6bfc672d9dc1b4f390b2900504f013187fa36335472554fafefa9050b1"),
    "metal_light_004": ("KEN-IMP", KEN + "impactMetal_light_004.ogg",
                     "9b1c35820fba507081261f19ab5f461f69a5e2627a7d91acdb73ca3cfc997979"),
    "metal_light_000": ("KEN-IMP", KEN + "impactMetal_light_000.ogg",
                        "33b5e6e37c6e9d54e07bf5a89b12c76e879f40c1ea83cdd82714df1d6f9fec6d"),
    "metal_medium_001": ("KEN-IMP", KEN + "impactMetal_medium_001.ogg",
                      "e8a9eaba7c4d27422e4eeb3e6c7100d5d7dc0f83e005efc98c960adcc5265337"),
    "metal_medium_003": ("KEN-IMP", KEN + "impactMetal_medium_003.ogg",
                      "2a185e2e57211d02c1bdd33b872d6b6a2fe83e6c14f4e56f426a95e717acf08e"),
    "metal_medium_004": ("KEN-IMP", KEN + "impactMetal_medium_004.ogg",
                         "03e10f800199c7166208e41c11cf4acfac6cc265467f02357da71972bc967295"),
    "metal_heavy_000": ("KEN-IMP", KEN + "impactMetal_heavy_000.ogg",
                     "e07045693e4a2b3d165c424e3dab4c781d9ff8880a386880ac89a51315d7f831"),
    "metal_heavy_002": ("KEN-IMP", KEN + "impactMetal_heavy_002.ogg",
                     "b914c8f1eb7c0f34bb165d7c77f4be0351f6be0660c13c53e65424e262e2c093"),
    "plate_light_002": ("KEN-IMP", KEN + "impactPlate_light_002.ogg",
                     "8ac5869ea434cf0d364872774efe70b2d666a4f02ba35ddfc1e051d336721be8"),
    "plate_light_003": ("KEN-IMP", KEN + "impactPlate_light_003.ogg",
                     "dbfb7c1d002576696df3e9a43d6639ee3f342068398b5e7b55bc2389d20508a9"),
    "plate_heavy_000": ("KEN-IMP", KEN + "impactPlate_heavy_000.ogg",
                     "112d4f93ddcc370b410630f971c0f5d991856102da9c76bc5c5540d388e75aaa"),
    "generic_light_000": ("KEN-IMP", KEN + "impactGeneric_light_000.ogg",
                          "f0e982611e97512fee5f777986b67e8b435434b601f94992ec044f7e89fb5acb"),
    "generic_light_002": ("KEN-IMP", KEN + "impactGeneric_light_002.ogg",
                       "d0bf60905b59ff630ffe01eb0edeeacd2504eaa8fb6523aeef7d2458b78264d3"),
    "tin_medium_002": ("KEN-IMP", KEN + "impactTin_medium_002.ogg",
                    "c1d2c4f9910d4529581ae56a9a9a01454c4619fbb7d6da7616221d8ec58cc0c4"),
    "wood_light_002": ("KEN-IMP", KEN + "impactWood_light_002.ogg",
                    "b183cf7a5bd783817e0e4b82af34ac6658fa1927049089dadc8b15c2ecc771dc"),
    "wood_light_003": ("KEN-IMP", KEN + "impactWood_light_003.ogg",
                    "cdfbe8af2fe7ff9ee28f337a0a989deee0f327620da456c8413644880e9d0004"),
    "wood_light_004": ("KEN-IMP", KEN + "impactWood_light_004.ogg",
                    "e10009f67ddaeb3a59a3e1129cfc1615d84ba60ab578eae07e7092ac223f099c"),
    "wood_medium_003": ("KEN-IMP", KEN + "impactWood_medium_003.ogg",
                     "635c37cfcd854b187d643d450ff0397798dcc29ae94da32192b814fae6bd854c"),
    "wood_medium_004": ("KEN-IMP", KEN + "impactWood_medium_004.ogg",
                     "7ba48f2f99c91c71be420841a91f1e69c0cbc4fe887fcd7213144d67bb87b13a"),
    "punch_medium_002": ("KEN-IMP", KEN + "impactPunch_medium_002.ogg",
                      "6492f9ccbc8d24dcef607bb1b48790b7870961474561f7fe5601e1c73a3018ef"),
    "soft_medium_001": ("KEN-IMP", KEN + "impactSoft_medium_001.ogg",
                     "7642a4fd43e547afe4f7adfadb3dabb681c0ff512f52c1674bae30a726841faf"),
    "soft_medium_003": ("KEN-IMP", KEN + "impactSoft_medium_003.ogg",
                     "5c4a1f35fde7e14046931da7bc3d1b23736541b7190ba107e08a379c4ca43cd6"),
    "mining_001": ("KEN-IMP", KEN + "impactMining_001.ogg",
                "61235a18de3f3d92118235398222dbf51d448f1be70b1c8bc962b10b86f2d9c6"),
    "concrete_002": ("KEN-IMP", KEN + "footstep_concrete_002.ogg",
                  "b21fa546d74941196b25da8a20b7010abd8c05c4fcf93545d1f344e66a664e13"),
}
ALLOWED_PACKS = gws.ALLOWED_PACKS


class AltSources(gws.Sources):
    """gws.Sources over this file's key table (same decoding and trimming)."""

    def available(self, keys) -> bool:
        if not keys:
            return True
        if gws.ffmpeg_path() is None:
            return False
        return all(self.path(k).is_file() for k in keys)

    def path(self, key: str) -> Path:
        return self.dir / ALT_SOURCES[key][1]

    def __call__(self, key: str) -> np.ndarray:
        if key not in self._cache:
            x = gws.decode(self.path(key))
            peak = np.max(np.abs(x)) if x.size else 0.0
            if peak <= 0:
                raise gws.MissingSource(f"source is silent: {key}")
            x = x / peak
            onset = int(np.argmax(np.abs(x) >= gws.SOURCE_ONSET_RATIO))
            onset = max(0, onset - n_of(gws.SOURCE_PREROLL_S))
            self._cache[key] = x[onset:]
        return self._cache[key].copy()


def fol(src, key: str, ratio: float = 1.0, lo: float | None = None,
        hi: float | None = None, decay: float | None = None,
        length: float | None = None) -> np.ndarray:
    """gws.foley on this file's sources."""
    return gws.foley(src, key, ratio, lo, hi, decay, length)


# --- Rulers ----------------------------------------------------------------------

def a_weight(f: np.ndarray) -> np.ndarray:
    """IEC 61672 A-weighting magnitude (linear), 0 dB at 1 kHz."""
    f2 = np.maximum(f, 1e-3) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / (
        (f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return ra * 10 ** (2.0 / 20)


def a_weighted(x: np.ndarray, rate: int = SR) -> np.ndarray:
    """Zero-phase A-weighting (a measurement, never heard)."""
    n = 1 << int(np.ceil(np.log2(len(x) + rate // 10)))
    f = np.fft.rfftfreq(n, 1 / rate)
    return np.fft.irfft(np.fft.rfft(x, n) * a_weight(f), n)[:len(x)]


def loud_db(x: np.ndarray, rate: int = SR, window: float = gws.SHORT_TERM_WINDOW_S,
            weighted: bool = True) -> float:
    """Loudest 50 ms, mean square (A-weighted unless told not), dB re full scale."""
    y = (a_weighted(x, rate) if weighted else x) ** 2
    w = max(1, int(round(window * rate)))
    if len(y) <= w:
        return float(10 * np.log10(max(np.mean(y), 1e-12)))
    c = np.concatenate([[0.0], np.cumsum(y)])
    return float(10 * np.log10(max(np.max(c[w:] - c[:-w]) / w, 1e-12)))


def loud_a_db(x: np.ndarray, rate: int = SR) -> float:
    return loud_db(x, rate)


def peak_db(x: np.ndarray) -> float:
    return float(20 * np.log10(max(np.max(np.abs(x)), 1e-9)))


def share_above(x: np.ndarray, rate: int = SR, edge: float = BASS_EDGE_HZ) -> float:
    e = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / rate)
    return float(e[f >= edge].sum() / max(e.sum(), 1e-20))


def levels(x: np.ndarray, rate: int = SR) -> dict[str, float]:
    return {"peak": peak_db(x), "loud_a": loud_a_db(x, rate), "rms": gws.rms_dbfs(x),
            "st50": loud_db(x, rate, weighted=False),
            "above300": share_above(x, rate), "length": len(x) / rate}


def read_wav(data: bytes) -> tuple[np.ndarray, int]:
    import io
    with wave.open(io.BytesIO(data)) as w:
        rate, width = w.getframerate(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width == 1:                       # 8-bit WAV is unsigned (Freedoom's DMX lumps)
        return (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128, rate
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / gws.PCM_MAX, rate


# --- Level: denser, not just louder ------------------------------------------------
# Handling sounds: a look-ahead peak limiter (offline, so it can look both
# ways) brings the knocks' peaks down towards their bodies, then a gentle
# fixed saturation; the limiter's ceiling is what the search moves. A gain
# that changes over 12 ms instead of per sample keeps the distortion low,
# which squaring the knocks with a hard tanh would not. The jet is noise and
# must stay periodic, so it gets a memoryless saturation only.

LIMIT_WINDOW_S = 0.006           # look-ahead and release, each side (a 12 ms gain window)
LIMIT_FLOOR_DB = -24.0           # the deepest ceiling the search may try
HANDLING_SOFT_DRIVE = 1.8        # the fixed saturation after the limiter


def running_max(a: np.ndarray, k: int) -> np.ndarray:
    """max(a[i:i+k]) for every i (van Herk / Gil-Werman, O(n))."""
    n = len(a)
    m = -(-n // k) * k
    p = np.concatenate([a, np.zeros(m - n)]).reshape(-1, k)
    pre = np.maximum.accumulate(p, axis=1).ravel()
    suf = np.maximum.accumulate(p[:, ::-1], axis=1)[:, ::-1].ravel()
    return np.maximum(suf[:n - k + 1], pre[k - 1:n])


def limit(x: np.ndarray, ceiling: float) -> np.ndarray:
    """No sample above `ceiling`; the gain is a box-smoothed minimum, never a clip.

    env(t) is the largest |x| within +-w of t; the gain ceiling/env is averaged
    over the same +-w, and every gain in that average is <= ceiling/|x(t)|.
    """
    w = n_of(LIMIT_WINDOW_S)
    k = 2 * w + 1
    xp = np.concatenate([np.zeros(w), x, np.zeros(w)])    # gains exist +-w around every sample
    env = running_max(np.concatenate([np.zeros(w), np.abs(xp), np.zeros(w)]), k)
    g = np.minimum(1.0, ceiling / np.maximum(env, 1e-12))
    c = np.concatenate([[0.0], np.cumsum(np.concatenate([np.ones(w), g, np.ones(w)]))])
    return (xp * (c[k:] - c[:-k]) / k)[w:w + len(x)]


def soft(x: np.ndarray, drive: float) -> np.ndarray:
    """Memoryless soft saturation, peak back at PEAK_DBFS (keeps a loop a loop)."""
    y = np.tanh(drive * x / np.max(np.abs(x)))
    return y / np.max(np.abs(y)) * 10 ** (PEAK_DBFS / 20)


def _bisect(make: Callable[[float], np.ndarray], lo: float, hi: float,
            target_db: float, rising_with_hi: bool) -> tuple[np.ndarray, float]:
    """Find the parameter in [lo, hi] whose output is at target loudness."""
    for _ in range(DRIVE_SEARCH_STEPS):
        mid = (lo + hi) / 2
        too_quiet = loud_a_db(make(mid)) < target_db
        if too_quiet == rising_with_hi:
            lo = mid
        else:
            hi = mid
    best = (lo + hi) / 2
    return make(best), best


def to_target(x: np.ndarray, target_db: float, kind: str) -> tuple[np.ndarray, float]:
    """-> (levelled sound, the dB of limiting or the saturation drive used).

    Loudness rises monotonically with both. If the search's range cannot
    reach the target the nearest version is returned and the tests say so.
    """
    if kind == "fire":
        y, ld = _bisect(lambda d: soft(x, float(np.exp(d))), np.log(0.01), np.log(MAX_DRIVE),
                        target_db, rising_with_hi=True)
        return y, float(np.exp(ld))
    if loud_a_db(soft(x, HANDLING_SOFT_DRIVE)) > target_db:
        # Already loud enough unlimited: ease the saturation instead.
        y, _ = _bisect(lambda d: soft(x, float(np.exp(d))), np.log(0.01),
                       np.log(HANDLING_SOFT_DRIVE), target_db, rising_with_hi=True)
        return y, 0.0
    y, ceiling_db = _bisect(lambda c: soft(limit(x, 10 ** (c / 20)), HANDLING_SOFT_DRIVE),
                            LIMIT_FLOOR_DB, 0.0, target_db, rising_with_hi=False)
    return y, -ceiling_db


# --- Shared atoms (new here) --------------------------------------------------------

def hp(x: np.ndarray, lo: float, order: int = 2) -> np.ndarray:
    return filt(x, lambda f: butter(f, lo=lo, order=order))


def creak(rng, length: float, rate_start: float, rate_end: float,
          centres=(1150.0, 2600.0)) -> np.ndarray:
    """Leather under strain: stick-slip, a jittered pulse train through two resonances."""
    n = n_of(length)
    out = np.zeros(n)
    t, i = 0.0, 0
    while t < length:
        k = min(n - 1, n_of(t))
        out[k] += rng.uniform(0.5, 1.0)
        frac = t / length
        rate = rate_start + (rate_end - rate_start) * frac
        t += (1 / rate) * rng.uniform(0.75, 1.25)
        i += 1
    shaped = filt(out, lambda f: butter(f, lo=500, hi=5000) * bump(f, centres[0], 5, 12)
                  * bump(f, centres[1], 6, 9))
    return shaped * np.sin(np.pi * np.clip(times(n) / length, 0, 1)) ** 0.6


def tubes(partials, length: float, decay: float, detune: float = 1.035) -> np.ndarray:
    """Two barrels side by side: two rings a little apart, so they beat."""
    return ring(partials, decay, length) + 0.8 * ring([p * detune for p in partials],
                                                       decay * 0.9, length)


def bounces(src, key: str, start: float, first_gap: float, count: int,
            ratio: float, lo: float, gain: float, out: np.ndarray,
            restitution: float = 0.62) -> None:
    """A hull dropped on concrete: knocks closing up and fading (a bouncing ball)."""
    t, g, gap = start, gain, first_gap
    for _ in range(count):
        place(out, fol(src, key, ratio=ratio, lo=lo, decay=0.025), t, g)
        t += gap
        gap *= restitution
        g *= restitution


# --- Recipes: TT-33 pickup (rejected: grip + a gentle press check) -------------------

def r_tt_rack(rng, src) -> np.ndarray:
    """SDTTPKP alt1: the slide racked hard: back to the stop and slammed home."""
    out = np.zeros(n_of(0.45))
    place(out, cloth(rng, 0.06, 0.01, 0.02), 0.0, 0.15)
    place(out, fol(src, "metal_light_004", ratio=1.1, decay=0.03), 0.0, 0.35)
    place(out, scrape(rng, 0.06, 2000, 8000, attack=0.01, decay=0.03, grain_hz=240), 0.07, 0.4)
    place(out, fol(src, "switch_01", ratio=1.25, lo=1500), 0.072, 0.4)
    place(out, fol(src, "metal_light_002", ratio=0.95, decay=0.03), 0.125, 0.55)
    place(out, click(rng, 3800), 0.125, 0.3)
    slam = 0.18
    place(out, fol(src, "metal_02", ratio=0.95), slam, 0.75)
    place(out, fol(src, "metal_light_000", ratio=0.9, decay=0.06), slam, 0.65)
    place(out, fol(src, "switch_02", ratio=1.1, lo=1200), slam + 0.003, 0.5)
    place(out, hp(thump(320, 220, 0.01, 0.015, 0.06), 180), slam, 0.3)
    place(out, ring((2900.0, 4700.0, 7300.0), 0.05, 0.15), slam, 0.06)
    return out


def r_tt_holster(rng, src) -> np.ndarray:
    """SDTTPKP alt2: drawn from a leather holster: the flap's stud, the leather, steel in the hand."""
    out = np.zeros(n_of(0.55))
    place(out, click(rng, 2500, 0.002), 0.0, 0.55)
    place(out, fol(src, "soft_medium_001", lo=400, decay=0.03), 0.0, 0.45)
    place(out, scrape(rng, 0.2, 500, 3500, attack=0.06, decay=0.08, grain_hz=40), 0.05, 0.3)
    place(out, creak(rng, 0.16, 45, 110), 0.07, 0.6)
    grip = 0.27
    place(out, fol(src, "soft_medium_003", lo=300, decay=0.04), grip, 0.45)
    place(out, fol(src, "metal_light_004", ratio=0.85, decay=0.05), grip + 0.004, 0.6)
    place(out, hp(thump(260, 190, 0.01, 0.02, 0.06), 160), grip, 0.25)
    # The hammer thumbed to half-cock: the TT-33 has no manual safety.
    place(out, fol(src, "switch_01", ratio=0.95, lo=900), 0.40, 0.45)
    place(out, click(rng, 3000), 0.40, 0.2)
    return out


def r_tt_magazine(rng, src) -> np.ndarray:
    """SDTTPKP alt3: a magazine slapped into the grip, the hammer cocked: heavier."""
    out = np.zeros(n_of(0.5))
    place(out, scrape(rng, 0.05, 1200, 6000, attack=0.008, decay=0.025), 0.0, 0.3)
    slap = 0.05
    place(out, fol(src, "metal_medium_003"), slap, 0.8)
    place(out, fol(src, "punch_medium_002", lo=300, decay=0.04), slap, 0.35)
    place(out, hp(thump(260, 170, 0.01, 0.02, 0.08), 150), slap, 0.35)
    place(out, fol(src, "switch_02", lo=1000), slap + 0.006, 0.45)
    place(out, fol(src, "switch_01", ratio=1.3, lo=1500), 0.22, 0.4)
    place(out, fol(src, "metal_light_001", ratio=1.4, decay=0.02), 0.26, 0.45)
    place(out, click(rng, 3300), 0.26, 0.25)
    return out


# --- Recipes: ice axe pickup (?: wooden shaft knock + head clink + hand) -------------

def r_axe_stone(rng, src) -> np.ndarray:
    """SDAXPKP alt1: lifted off stone: the head scrapes, the pick knocks and the steel rings."""
    out = np.zeros(n_of(0.7))
    place(out, scrape(rng, 0.09, 1500, 7000, attack=0.01, decay=0.04, grain_hz=220), 0.0, 0.35)
    place(out, fol(src, "concrete_002", ratio=1.3, lo=300), 0.0, 0.5)
    knock = 0.08
    place(out, fol(src, "metal_light_003", ratio=0.9), knock, 0.7)
    place(out, fol(src, "mining_001", ratio=1.6, lo=250, decay=0.06), knock, 0.55)
    place(out, ring((1870.0, 3150.0, 4720.0, 6930.0), 0.18, 0.55), knock + 0.001, 0.16)
    place(out, grit(rng, 0.3, 10, 0.0, 0.2, 0.07, 2000, 9000), knock + 0.02, 0.5)
    return out


def r_axe_carabiner(rng, src) -> np.ndarray:
    """SDAXPKP alt2: the wrist leash's carabiner snaps and jingles, a hand takes the shaft."""
    out = np.zeros(n_of(0.5))
    place(out, fol(src, "key_open_02"), 0.0, 0.5)
    place(out, fol(src, "switch_02", ratio=1.4, lo=2000), 0.0, 0.4)
    for at, key, ratio, g in ((0.06, "metal_light_001", 1.5, 0.4),
                              (0.11, "metal_light_004", 1.7, 0.3),
                              (0.17, "metal_light_001", 1.8, 0.35),
                              (0.24, "metal_light_004", 1.6, 0.2)):
        place(out, fol(src, key, ratio=ratio, decay=0.03), at, g)
    place(out, ring((3400.0, 5100.0, 7900.0), 0.05, 0.2), 0.06, 0.05)
    place(out, fol(src, "wood_light_003", ratio=1.1), 0.20, 0.4)
    place(out, cloth(rng), 0.20, 0.15)
    return out


def r_axe_palm(rng, src) -> np.ndarray:
    """SDAXPKP alt3: slapped into the palm: wood and the steel head's weight, one heavy clunk."""
    out = np.zeros(n_of(0.45))
    place(out, fol(src, "punch_medium_002", lo=250), 0.0, 0.6)
    place(out, fol(src, "wood_medium_003", ratio=1.2, lo=250), 0.0, 0.6)
    place(out, fol(src, "metal_medium_001", ratio=0.85), 0.008, 0.7)
    place(out, hp(thump(240, 150, 0.01, 0.025, 0.1), 150), 0.0, 0.35)
    place(out, ring((1240.0, 2980.0, 4600.0), 0.06, 0.25), 0.008, 0.12)
    place(out, cloth(rng), 0.12, 0.2)
    place(out, fol(src, "metal_light_004", ratio=1.6, decay=0.02), 0.15, 0.15)
    return out


# --- Recipes: IZh-58 pickup (?: stock knock + broken open and snapped shut) ----------

IZH_BARREL_PARTIALS = (740.0, 2040.0, 3900.0)    # a 12-gauge tube, knocked


def r_izh_barrels(rng, src) -> np.ndarray:
    """SDIZPKP alt1: the butt knocks the floor and the two barrels ring together."""
    out = np.zeros(n_of(0.65))
    place(out, fol(src, "wood_medium_004", lo=200), 0.0, 0.7)
    place(out, hp(thump(200, 130, 0.015, 0.03, 0.12), 150), 0.0, 0.35)
    place(out, fol(src, "metal_medium_003", ratio=0.8), 0.015, 0.6)
    place(out, tubes(IZH_BARREL_PARTIALS, 0.5, 0.15), 0.016, 0.14)
    place(out, scrape(rng, 0.1, 800, 4000, attack=0.03, decay=0.04, grain_hz=90), 0.2, 0.2)
    return out


def r_izh_sling(rng, src) -> np.ndarray:
    """SDIZPKP alt2: up on the sling: the strap creaks, the swivels clink, onto the shoulder."""
    out = np.zeros(n_of(0.6))
    place(out, creak(rng, 0.2, 35, 90, centres=(950.0, 2200.0)), 0.0, 0.6)
    place(out, cloth(rng, 0.15), 0.0, 0.2)
    place(out, fol(src, "metal_light_003", ratio=1.3, decay=0.04), 0.03, 0.4)
    place(out, fol(src, "metal_light_001", ratio=1.45, decay=0.03), 0.09, 0.3)
    settle = 0.22
    place(out, fol(src, "soft_medium_001", lo=300), settle, 0.45)
    place(out, fol(src, "wood_light_004", ratio=0.9), settle, 0.45)
    place(out, tubes(IZH_BARREL_PARTIALS, 0.3, 0.08), settle + 0.002, 0.06)
    return out


def r_izh_shells(rng, src) -> np.ndarray:
    """SDIZPKP alt3: the gun taken up with loose shells rattling in the box."""
    out = np.zeros(n_of(0.55))
    place(out, fol(src, "metal_medium_001", ratio=0.9), 0.0, 0.6)
    place(out, fol(src, "wood_light_002"), 0.0, 0.4)
    for at in np.sort(rng.uniform(0.04, 0.34, 8)):
        key = "generic_light_000" if rng.uniform() < 0.5 else "generic_light_002"
        place(out, fol(src, key, ratio=rng.uniform(1.6, 2.0), lo=600, decay=0.02),
              float(at), rng.uniform(0.25, 0.4))
        place(out, click(rng, rng.uniform(3000, 4500)), float(at), 0.15)
    return out


# --- Recipes: IZh-58 break-open (NO). Snap on frame A, as the draft ------------------

# The steps before the snap sit this far under it, so that levelling (which
# limits whatever is loudest) leaves the snap the loudest moment of the reload.
IZH_PRE_SNAP_GAIN = 0.4          # -8 dB
IZH_PRE_SNAP_GAIN_CRISP = 0.7    # -3 dB: alt1's steps are light knocks already


def _snap(out, src, keys_gains, at: float) -> None:
    for key, ratio, lo, g, dt in keys_gains:
        place(out, fol(src, key, ratio=ratio, lo=lo), at + dt, g)


def _izh_buffers() -> tuple[np.ndarray, np.ndarray]:
    n = n_of(tics(gws.IZH_RELOAD_TICS) + 0.03)
    return np.zeros(n), np.zeros(n)


def r_izh_reload_crisp(rng, src) -> np.ndarray:
    """SDIZRLD alt1: lever, barrels drop, hulls drawn and dropped, two shells in, snap."""
    out, snap = _izh_buffers()
    place(out, fol(src, "switch_01", ratio=0.95), 0.0, 0.5)
    place(out, fol(src, "metal_light_004", ratio=1.1, decay=0.03), 0.0, 0.4)
    drop = 0.05
    place(out, fol(src, "metal_medium_001", ratio=0.85), drop, 0.55)
    place(out, hp(thump(170, 120, 0.015, 0.03, 0.1), 140), drop, 0.25)
    place(out, tubes(IZH_BARREL_PARTIALS, 0.3, 0.1), drop, 0.06)
    for at in (0.16, 0.22):                          # hulls drawn: plastic on steel
        place(out, scrape(rng, 0.06, 1500, 6000, attack=0.01, decay=0.02), at, 0.25)
    for at in (0.27, 0.31):                          # and dropped on the floor
        bounces(src, "generic_light_002", at, 0.05, 2, 1.8, 500, 0.3, out)
        place(out, click(rng, 2600), at, 0.15)
    for at in (0.40, 0.50):                          # two shells pushed in, seated
        place(out, scrape(rng, 0.04, 1500, 5000, attack=0.01, decay=0.015), at - 0.04, 0.2)
        place(out, fol(src, "metal_light_001", ratio=0.8, decay=0.02), at, 0.35)
        place(out, fol(src, "wood_light_002", ratio=1.4), at, 0.25)
    _snap(snap, src, (("metal_medium_003", 0.85, None, 0.85, 0.0),
                     ("metal_02", 1.0, None, 0.5, 0.0),
                     ("switch_02", 1.0, 900, 0.6, 0.008)), IZH_CLOSE_S)
    place(snap, hp(thump(200, 140, 0.01, 0.03, 0.1), 150), IZH_CLOSE_S, 0.3)
    place(snap, tubes(IZH_BARREL_PARTIALS, 0.25, 0.08), IZH_CLOSE_S, 0.06)
    return IZH_PRE_SNAP_GAIN_CRISP * out + snap


def r_izh_reload_hulls(rng, src) -> np.ndarray:
    """SDIZRLD alt2: the hulls thrown clear and bouncing on concrete; shells dropped in, snap."""
    out, snap = _izh_buffers()
    place(out, fol(src, "key_open_02", ratio=0.9), 0.0, 0.5)
    place(out, click(rng, 2200), 0.0, 0.3)
    drop = 0.04
    place(out, fol(src, "tin_medium_002", ratio=0.9, lo=300), drop, 0.25)
    place(out, fol(src, "metal_light_002", ratio=0.7), drop, 0.2)
    place(out, fol(src, "spring_08", length=0.05, decay=0.02), 0.09, 0.4)
    bounces(src, "generic_light_000", 0.20, 0.07, 3, 1.6, 500, 0.45, out)
    bounces(src, "plate_light_003", 0.205, 0.07, 3, 2.2, 800, 0.15, out)
    bounces(src, "generic_light_002", 0.26, 0.06, 3, 1.9, 500, 0.4, out)
    for at in (0.45, 0.53):
        place(out, fol(src, "wood_light_002", ratio=1.2), at, 0.4)
        place(out, hp(thump(380, 300, 0.005, 0.012, 0.05), 200), at, 0.2)
    _snap(snap, src, (("metal_heavy_002", 1.3, 250, 0.8, 0.0),
                     ("metal_medium_003", 1.0, None, 0.6, 0.0),
                     ("metal_11", 1.0, None, 0.45, 0.0),
                     ("switch_01", 1.0, None, 0.4, 0.006)), IZH_CLOSE_S)
    return IZH_PRE_SNAP_GAIN * out + snap


def r_izh_reload_heavy(rng, src) -> np.ndarray:
    """SDIZRLD alt3: heavy and deliberate: a hard drop, solid shells, a deep slam."""
    out, snap = _izh_buffers()
    place(out, fol(src, "metal_06", length=0.08, decay=0.03), 0.0, 0.5)
    place(out, fol(src, "switch_02", ratio=0.8), 0.0, 0.4)
    drop = 0.06
    place(out, fol(src, "metal_heavy_000", ratio=1.15, lo=250), drop, 0.8)
    place(out, fol(src, "plate_light_002", ratio=0.9), drop, 0.4)
    place(out, tubes(IZH_BARREL_PARTIALS, 0.4, 0.2), drop, 0.1)
    place(out, scrape(rng, 0.12, 900, 4500, attack=0.03, decay=0.05), 0.2, 0.3)
    place(out, fol(src, "generic_light_002", ratio=1.3, lo=400), 0.28, 0.4)
    place(out, fol(src, "generic_light_002", ratio=1.45, lo=400), 0.30, 0.3)
    for at in (0.40, 0.47):
        place(out, fol(src, "wood_medium_003", ratio=1.25, lo=300), at, 0.5)
        place(out, fol(src, "metal_light_004", ratio=0.75, decay=0.02), at, 0.3)
    _snap(snap, src, (("plate_heavy_000", 1.0, 250, 0.7, 0.0),
                     ("metal_medium_004", 0.8, None, 0.85, 0.0),
                     ("metal_02", 0.85, None, 0.35, 0.002),
                     ("switch_02", 0.85, 900, 0.5, 0.012)), IZH_CLOSE_S)
    place(snap, fol(src, "spring_07", length=0.1, lo=400, decay=0.04), IZH_CLOSE_S + 0.02, 0.2)
    place(snap, hp(thump(150, 100, 0.01, 0.04, 0.12), 120), IZH_CLOSE_S, 0.35)
    return IZH_PRE_SNAP_GAIN * out + snap


# --- Recipes: ROKS-3 jet (NO). A periodic first 3 tics, then the release tail -------

def periodic_noise(rng, mag: Callable[[np.ndarray], np.ndarray],
                   n: int = JET_LOOP_N) -> np.ndarray:
    """Noise filtered circularly: exactly periodic with period n."""
    f = np.fft.rfftfreq(n, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * mag(f), n)
    return x / np.sqrt(np.mean(x ** 2))


def periodic_wobble(rng, harmonics: int, n: int = JET_LOOP_N) -> np.ndarray:
    """A smooth control signal in about -1..1, periodic in n (flame turbulence)."""
    t = np.arange(n) / n
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        out += np.sin(2 * np.pi * k * t + rng.uniform(0, 2 * np.pi)) / k
    return out / np.max(np.abs(out))


def periodic_ticks(rng, at_fracs, lo: float, hi: float, n: int = JET_LOOP_N) -> np.ndarray:
    """Spark-igniter ticks at fixed places inside the period, filtered circularly."""
    imp = np.zeros(n)
    for frac in at_fracs:
        imp[int(frac * n) % n] += rng.uniform(0.7, 1.0)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(np.fft.rfft(imp) * butter(f, lo=lo, hi=hi) * bump(f, 4200, 3, 6), n)


def jet(period: np.ndarray, length: float, hold: float, decay: float) -> np.ndarray:
    """Tile one period over `length`; full level for the loop and `hold`, then decay.

    Rotated first so the sound starts on an upward zero crossing inside the
    period's quietest millisecond: no fade-in is needed (the first press
    starts from zero) and none is wanted (a restart must join the period's
    end to its start with nothing in between).
    """
    period = np.roll(period, -quiet_zero_crossing(period))
    n = n_of(length)
    x = np.tile(period, n // len(period) + 1)[:n]
    t = times(n)
    start = len(period) / SR + hold
    return x * np.where(t < start, 1.0, np.exp(-(t - start) / decay))


def darken_after(x: np.ndarray, start_s: float, hi_start: float, hi_end: float,
                 tau: float, lo: float = 80.0) -> np.ndarray:
    """A low-pass closing over the tail only; the loop is left as it is."""
    i = n_of(start_s)
    head, tail = x[:i], x[i:]

    def gain(t, f):
        hi = hi_end + (hi_start - hi_end) * np.exp(-max(t, 0.0) / tau)
        return butter(f, lo=lo, hi=hi)
    return np.concatenate([head, shape(tail, gain)])


def quiet_zero_crossing(period: np.ndarray, window_s: float = 0.001) -> int:
    """Index of the upward zero crossing nearest the quietest `window_s` (circular)."""
    w = n_of(window_s)
    e = np.convolve(np.concatenate([period, period[:w]]) ** 2, np.ones(w), "valid")[:len(period)]
    start = int(np.argmin(e))
    up = np.nonzero((np.roll(period, 1) < 0) & (period >= 0))[0]
    return int(up[np.argmin((up - start) % len(period))]) if len(up) else start


def r_jet_roar(rng, src) -> np.ndarray:
    """SDRKFIR alt1: a roaring jet, the igniter hissing under it; on release it dies away."""
    roar = periodic_noise(rng, lambda f: butter(f, lo=90, hi=1800) * bump(f, 420, 1.5, 4))
    tear = periodic_noise(rng, lambda f: butter(f, lo=1500, hi=4500))
    hiss = periodic_noise(rng, lambda f: butter(f, lo=4500, hi=11000, order=3))
    period = (roar * (1 + 0.3 * periodic_wobble(rng, 4))
              + 0.4 * tear * (1 + 0.4 * periodic_wobble(rng, 6))
              + 0.22 * hiss)
    x = jet(period, 0.6, 0.06, 0.11)
    x = darken_after(x, JET_LOOP_N / SR + 0.06, 9000, 900, 0.12)
    pff = gws.burst_noise(rng, 0.06, 0.004, 0.02, lambda f: butter(f, lo=2000, hi=8000))
    place(x, pff, JET_LOOP_N / SR + 0.16, 0.25)
    return x


def r_jet_torch(rng, src) -> np.ndarray:
    """SDRKFIR alt2: a pressurised torch: bright hiss, a nozzle tone, the spark igniter ticking."""
    jetn = periodic_noise(rng, lambda f: butter(f, lo=700, hi=7000) * bump(f, 1600, 2, 5))
    low = periodic_noise(rng, lambda f: butter(f, lo=150, hi=900))
    ticks = periodic_ticks(rng, (0.12, 0.61), 2500, 9000)
    ticks = ticks / np.max(np.abs(ticks)) * 2.2
    period = (jetn * (1 + 0.15 * periodic_wobble(rng, 3))
              + 0.5 * low * (1 + 0.35 * periodic_wobble(rng, 5))
              + ticks)
    x = jet(period, 0.55, 0.03, 0.06)
    after = JET_LOOP_N / SR + 0.03
    place(x, grit(rng, 0.35, 14, 0.0, 0.3, 0.12, 1500, 8000), after, 1.2)
    place(x, gws.burst_noise(rng, 0.04, 0.002, 0.012, lambda f: butter(f, lo=3000, hi=9000)),
          after + 0.08, 0.5)
    return x


def r_jet_pulse(rng, src) -> np.ndarray:
    """SDRKFIR alt3: the fuel pump's pulse: a heavy chug at the restart rate; a whoosh on release."""
    n = JET_LOOP_N
    t = np.arange(n) / SR
    pulse = 0.5 + 0.5 * np.clip(t / 0.008, 0, 1) * np.exp(-t / 0.045)
    roar = periodic_noise(rng, lambda f: butter(f, lo=120, hi=1500) * bump(f, 600, 1.2, 3))
    chuff = periodic_noise(rng, lambda f: butter(f, lo=1000, hi=5000))
    chuff_env = np.clip(t / 0.003, 0, 1) * np.exp(-t / 0.018)
    hiss = periodic_noise(rng, lambda f: butter(f, lo=5000, hi=12000, order=3))
    period = roar * pulse + 0.6 * chuff * chuff_env + 0.18 * hiss
    x = jet(period, 0.7, 0.0, 0.09)
    m = n_of(0.4)
    whoosh = rng.standard_normal(m) * np.sin(np.pi * np.clip(times(m) / 0.4, 0, 1)) ** 1.5

    def sweep(tc, f):
        c = 2200 * np.exp(-max(tc, 0.0) / 0.25) + 500
        return butter(f, lo=c * 0.5, hi=c * 2.0)
    place(x, shape(whoosh, sweep), JET_LOOP_N / SR + 0.02, 0.55)
    return x


# --- The table -------------------------------------------------------------------------

@dataclass(frozen=True)
class Alt:
    lump: str
    index: int
    kind: str                  # pickup / reload / fire
    recipe: Callable
    sources: tuple[str, ...]
    length_s: tuple[float, float]
    label: str                 # Spanish, for the page
    what: str                  # Spanish, for the page

    @property
    def name(self) -> str:
        return f"{self.lump}_alt{self.index}"


# lump -> (Freedoom lump it replaces, Spanish weapon group, Spanish event, verdict, what was rejected)
TARGETS: dict[str, tuple[str, str, str, str, str]] = {
    "SDTTPKP": ("DSWPNUP", "TT-33 (ranura 2)", "recoger", "NO",
                "agarrar la pistola y comprobar la recámara con suavidad"),
    "SDAXPKP": ("DSWPNUP", "Piolet (ranura 1)", "recoger", "?",
                "mango de madera, cabeza que tintinea, mano que agarra"),
    "SDIZPKP": ("DSWPNUP", "IZh-58 (ranura 3)", "recoger", "?",
                "la culata golpea; abrir y cerrar para ver que está vacía"),
    "SDIZRLD": ("DSSGCOCK", "IZh-58 (ranura 3)", "recarga (abrir y cerrar)", "NO",
                "abrir la báscula, sacar dos vainas, meter dos cartuchos, cerrar"),
    "SDRKFIR": ("DSFLAME", "ROKS-3, lanzallamas (ranura 6)", "disparo", "NO",
                "siseo de válvula y chorro rugiente"),
}

ALTS: tuple[Alt, ...] = (
    Alt("SDTTPKP", 1, "pickup", r_tt_rack,
        ("metal_light_004", "switch_01", "metal_light_002", "metal_02", "metal_light_000", "switch_02"),
        (0.25, 0.45), "Corredera a fondo",
        "Acero puro: la corredera atrás hasta el tope y suelta de golpe; un clac metálico fuerte."),
    Alt("SDTTPKP", 2, "pickup", r_tt_holster,
        ("soft_medium_001", "soft_medium_003", "metal_light_004", "switch_01"),
        (0.35, 0.55), "Funda de cuero",
        "Sale de la funda: el broche salta, el cuero cruje y roza, el acero cae en la mano, martillo a medio montar."),
    Alt("SDTTPKP", 3, "pickup", r_tt_magazine,
        ("metal_medium_003", "punch_medium_002", "switch_02", "switch_01", "metal_light_001"),
        (0.3, 0.5), "Cargador de un golpe",
        "Más pesado: el cargador entra y se encaja con la palma, luego se monta el martillo (dos clics)."),
    Alt("SDAXPKP", 1, "pickup", r_axe_stone,
        ("concrete_002", "metal_light_003", "mining_001"),
        (0.4, 0.7), "Acero sobre piedra",
        "Se levanta del suelo de piedra: la cabeza raspa, el pico golpea y el acero queda sonando."),
    Alt("SDAXPKP", 2, "pickup", r_axe_carabiner,
        ("key_open_02", "switch_02", "metal_light_001", "metal_light_004", "wood_light_003"),
        (0.3, 0.5), "Mosquetón y dragonera",
        "El mosquetón de la dragonera se cierra y tintinea; la mano coge el mango."),
    Alt("SDAXPKP", 3, "pickup", r_axe_palm,
        ("punch_medium_002", "wood_medium_003", "metal_medium_001", "metal_light_004"),
        (0.25, 0.45), "Golpe en la palma",
        "Un solo golpe pesado: el mango cae en la palma con el peso de la cabeza de acero."),
    Alt("SDIZPKP", 1, "pickup", r_izh_barrels,
        ("wood_medium_004", "metal_medium_003"),
        (0.4, 0.65), "Culata y cañones",
        "La culata toca el suelo y los dos cañones suenan juntos, con un leve batido."),
    Alt("SDIZPKP", 2, "pickup", r_izh_sling,
        ("metal_light_003", "metal_light_001", "soft_medium_001", "wood_light_004"),
        (0.35, 0.6), "Correa al hombro",
        "Cuero y metal: la correa cruje, las anillas tintinean, la escopeta se asienta en el hombro."),
    Alt("SDIZPKP", 3, "pickup", r_izh_shells,
        ("metal_medium_001", "wood_light_002", "generic_light_000", "generic_light_002"),
        (0.25, 0.55), "Cartuchos sueltos",
        "Se coge el arma y suenan los cartuchos sueltos en la caja."),
    Alt("SDIZRLD", 1, "reload", r_izh_reload_crisp,
        ("switch_01", "metal_light_004", "metal_medium_001", "generic_light_002",
         "metal_light_001", "wood_light_002", "metal_medium_003", "metal_02", "switch_02"),
        (0.8, 0.95), "Báscula nítida",
        "Llave, cañones que caen, dos vainas fuera y al suelo, dos cartuchos dentro, cierre seco a 0,62 s."),
    Alt("SDIZRLD", 2, "reload", r_izh_reload_hulls,
        ("key_open_02", "tin_medium_002", "metal_light_002", "spring_08", "generic_light_000",
         "plate_light_003", "generic_light_002", "wood_light_002", "metal_heavy_002",
         "metal_11", "switch_01"),
        (0.8, 0.95), "Vainas al suelo",
        "Los expulsores lanzan las vainas, que rebotan en el hormigón; cartuchos dentro, cierre a 0,62 s."),
    Alt("SDIZRLD", 3, "reload", r_izh_reload_heavy,
        ("metal_06", "switch_02", "metal_heavy_000", "plate_light_002", "generic_light_002",
         "wood_medium_003", "metal_light_004", "plate_heavy_000", "metal_medium_004", "spring_07"),
        (0.8, 0.95), "Pesada y lenta",
        "Más grave y deliberada: los cañones caen con peso, cartuchos firmes, portazo de acero a 0,62 s."),
    Alt("SDRKFIR", 1, "fire", r_jet_roar, (), (0.4, 0.65), "Chorro rugiente",
        "Rugido ancho del chorro con el siseo del ignitor encima; al soltar se apaga y se oscurece."),
    Alt("SDRKFIR", 2, "fire", r_jet_torch, (), (0.4, 0.6), "Soplete con chispa",
        "Chorro a presión, más agudo: silbido de boquilla y la chispa del ignitor crepitando; al soltar, chisporroteo."),
    Alt("SDRKFIR", 3, "fire", r_jet_pulse, (), (0.5, 0.75), "Bomba a pulsos",
        "Grave y pulsante: la bomba empuja el combustible a golpes (justo al ritmo de disparo); al soltar, una llamarada."),
)
ALTS_BY_NAME = {a.name: a for a in ALTS}
LUMPS = tuple(TARGETS)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode("ascii"))


def target_db(alt: Alt) -> float:
    return FREEDOOM_LEVELS[TARGETS[alt.lump][0]][1] - ALLOWANCE_DB[alt.kind]


def finish_jet(x: np.ndarray) -> np.ndarray:
    """The jet's own finish: no filtering and no fade-in (either would break the
    loop; jet() starts it on a zero crossing), a fade-out, the peak."""
    loud = np.nonzero(np.abs(x) >= np.max(np.abs(x)) * 10 ** (gws.TAIL_FLOOR_DB / 20))[0]
    x = x[:loud[-1] + 1 + n_of(FADE_OUT_S)].copy()
    fo = n_of(FADE_OUT_S)
    x[-fo:] *= np.linspace(1, 0, fo)
    return x / np.max(np.abs(x)) * 10 ** (PEAK_DBFS / 20)


def render(alt: Alt, sources: AltSources) -> tuple[np.ndarray, float]:
    """-> (float samples, dB of limiting or the jet's drive). Raises gws.MissingSource."""
    if not sources.available(alt.sources):
        raise gws.MissingSource(f"{alt.name}: sources or ffmpeg missing")
    rng = np.random.default_rng(seed_of(alt.name))
    x = alt.recipe(rng, sources)
    x = finish_jet(x) if alt.kind == "fire" else finish(x, PEAK_DBFS)
    y, drive = to_target(x, target_db(alt), alt.kind)
    if alt.kind == "fire":
        # The fade-out again: saturation lifted its quiet end.
        fo = n_of(FADE_OUT_S)
        y[-fo:] *= np.linspace(1, 0, fo)
    return y, drive


def held(x: np.ndarray, rate: int, hold_s: float = HELD_PREVIEW_S,
         tics_per_restart: int = ROKS3_TICS_PER_JET) -> np.ndarray:
    """The trigger held: restarted every 3 tics, each restart cutting the last
    (ASSUMPTION, WEAPON-SOUNDS §3); on release the last restart plays out."""
    step = rate * tics_per_restart // gws.TICS_PER_SECOND
    starts = range(0, int(hold_s * rate), step)
    last = list(starts)[-1]
    out = np.zeros(last + len(x))
    for s in starts:
        seg = x if s == last else x[:step]
        out[s:s + len(seg)] = seg[:len(out) - s]
    return out


# --- Driver ---------------------------------------------------------------------------

@dataclass
class Rendered:
    alt: Alt
    x: np.ndarray
    drive: float
    wav: bytes


def build(names=None, sources: AltSources | None = None) -> tuple[list[Rendered], list[str]]:
    sources = sources or AltSources()
    done, skipped = [], []
    for alt in ALTS:
        if names and alt.name not in names and alt.lump not in names:
            continue
        try:
            x, d = render(alt, sources)
        except gws.MissingSource as e:
            skipped.append(str(e))
            continue
        done.append(Rendered(alt, x, d, wav_bytes(x)))
    return done, skipped


def freedoom_wav(name: str) -> bytes | None:
    p = FREEDOOM_PREVIEW_DIR / f"{name}.wav"
    if p.is_file():
        return p.read_bytes()
    return gws.placeholder_wav(name)


def manifest_text(done: list[Rendered], sources: AltSources) -> str:
    L = ["# Weapon sound alternatives (D74), written by tools/audio/gen_weapon_alts.py",
         "# Levels: peak dBFS; loudA = loudest 50 ms, A-weighted, dB; RMS dBFS; >300 Hz = energy share.",
         "# Target loudA = the Freedoom lump's loudA minus the allowance of the kind "
         f"({', '.join(f'{k} {v:g} dB' for k, v in ALLOWANCE_DB.items())}).", ""]
    for name, (pk, la, rms) in FREEDOOM_LEVELS.items():
        L.append(f"{name:10s} Freedoom  peak {pk:6.1f}  loudA {la:6.1f}  RMS {rms:6.1f}")
    L.append("")
    for r in done:
        lv = levels(r.x)
        ref = TARGETS[r.alt.lump][0]
        L.append(f"{r.alt.name:13s} {r.alt.label:24s} {lv['length']:.2f} s  peak {lv['peak']:5.1f}  "
                 f"loudA {lv['loud_a']:6.1f} (target {target_db(r.alt):5.1f}, {ref} {FREEDOOM_LEVELS[ref][1]:.1f})  "
                 f"RMS {lv['rms']:6.1f}  >300 Hz {100 * lv['above300']:3.0f} %  "
                 f"{'drive' if r.alt.kind == 'fire' else 'limited'} {r.drive:5.2f}{'' if r.alt.kind == 'fire' else ' dB'}  "
                 f"sources: {', '.join(r.alt.sources) or 'synthesis only'}")
    return "\n".join(L) + "\n"


def provenance_tsv(done: list[Rendered], sources: AltSources) -> str:
    rows = ["alternative\tpack\tfile\tsha256"]
    for r in done:
        if not r.alt.sources:
            rows.append(f"{r.alt.name}\tSYN\t-\t-")
        for k in r.alt.sources:
            pack, rel, _ = ALT_SOURCES[k]
            rows.append(f"{r.alt.name}\t{pack}\t{rel}\t{gws.sha256_file(sources.path(k))}")
    return "\n".join(rows) + "\n"


def write_outputs(done: list[Rendered], out_dir: Path, sources: AltSources) -> list[Path]:
    written = []
    (out_dir / "wav").mkdir(parents=True, exist_ok=True)
    (out_dir / "preview").mkdir(parents=True, exist_ok=True)

    def put(path: Path, data: bytes) -> None:
        path.write_bytes(data)
        written.append(path)

    def put_ogg(path: Path, wav: bytes) -> None:
        ogg = gws.ogg_bytes(wav)
        if ogg is None:
            raise gws.MissingSource("ffmpeg is not on the PATH: no OGG")
        put(path, ogg)

    for r in done:
        put(out_dir / "wav" / f"{r.alt.name}.wav", r.wav)
        put_ogg(out_dir / f"{r.alt.name}.ogg", r.wav)
        if r.alt.kind == "fire":
            put_ogg(out_dir / "preview" / f"{r.alt.name}_held.ogg", wav_bytes(held(r.x, SR)))
    # The same hold for what the CEO rejected and for what plays today.
    rej = gws.OUT_DIR / "SDRKFIR.wav"
    if rej.is_file():
        x, rate = read_wav(rej.read_bytes())
        put_ogg(out_dir / "preview" / "SDRKFIR_rejected_held.ogg", wav_bytes(held(x, rate), rate))
    fd = freedoom_wav("DSFLAME")
    if fd is not None:
        x, rate = read_wav(fd)
        put_ogg(out_dir / "preview" / "DSFLAME_held.ogg", wav_bytes(held(x, rate), rate))
    put(out_dir / "MANIFEST.txt", manifest_text(done, sources).encode("utf-8"))
    put(out_dir / "PROVENANCE.tsv", provenance_tsv(done, sources).encode("utf-8"))
    return written


# --- The listening page (same style as the M3 sheet) -----------------------------------

PAGE_KEY_PREFIX = "sd-m3-alternatives-"


def _rel(target: Path, page: Path) -> str:
    import os
    return Path(os.path.relpath(target, page.parent)).as_posix()


def page_items(done: list[Rendered], page: Path, out_dir: Path) -> list[dict]:
    items = []
    for r in done:
        a = r.alt
        ref, group, ev, verdict, rejected_what = TARGETS[a.lump]
        lv = levels(r.x)
        it = {
            "id": a.name, "lump": a.lump, "group": group, "ev": ev, "label": a.label,
            "what": a.what, "verdict": verdict, "rejWhat": rejected_what,
            "src": _rel(out_dir / f"{a.name}.ogg", page),
            "rej": _rel(REJECTED_OGG_DIR / f"{a.lump}.ogg", page),
            "rep": f"Freedoom {ref}",
            "repSrc": _rel(FREEDOOM_PREVIEW_DIR / f"{ref}.wav", page),
            "dur": round(lv["length"], 2),
            "lvl": (f"pico {lv['peak']:.1f} dBFS · fuerza {lv['loud_a']:.1f} dB "
                    f"(Freedoom {ref}: {FREEDOOM_LEVELS[ref][1]:.1f}) · "
                    f"{100 * lv['above300']:.0f} % por encima de 300 Hz"),
            "extras": [],
        }
        if a.kind == "fire":
            it["extras"] = [
                {"l": "Esta alternativa con el gatillo apretado 1,2 s y soltado",
                 "src": _rel(out_dir / "preview" / f"{a.name}_held.ogg", page)},
                {"l": "El rechazado, igual de apretado",
                 "src": _rel(out_dir / "preview" / "SDRKFIR_rejected_held.ogg", page)},
                {"l": "Freedoom DSFLAME (lo de hoy), igual de apretado",
                 "src": _rel(out_dir / "preview" / "DSFLAME_held.ogg", page)},
            ]
        items.append(it)
    return items


PAGE_CSS = """
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4;--warn:#7a4b00;--warnbg:#fff4dc}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--warn:#f0c674;--warnbg:#2f2814}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--warn:#f0c674;--warnbg:#2f2814}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
.prog{font-variant-numeric:tabular-nums;color:var(--mute)}
.prog b{color:var(--ink)}
.bar{flex:1 1 160px;height:6px;background:var(--chip);border-radius:3px;overflow:hidden;min-width:120px}
.bar i{display:block;height:100%;background:var(--accent);width:0}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
label.chk{color:var(--mute);user-select:none}
.intro{margin:14px 0;color:var(--ink)}
.intro p{margin:6px 0}
.intro ul{margin:6px 0;padding-left:20px}
details.grp{margin:14px 0;border:1px solid var(--line);border-radius:8px;background:var(--card)}
details.grp>summary{cursor:pointer;padding:10px 12px;font-weight:650;font-size:15px;list-style:none;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
details.grp>summary::-webkit-details-marker{display:none}
details.grp>summary::before{content:"\\25B8";color:var(--mute)}
details.grp[open]>summary::before{content:"\\25BE"}
.gcount{margin-left:auto;font-weight:400;color:var(--mute);font-size:13px;font-variant-numeric:tabular-nums}
.rejnote{font-weight:400;color:var(--mute);font-size:13px}
.row{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr) 230px;gap:10px 16px;padding:10px 12px;border-top:1px solid var(--line)}
.row.hide{display:none}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
.name code{font:600 14px ui-monospace,Consolas,monospace}
.ev{display:inline-block;background:var(--chip);border-radius:10px;padding:0 8px;margin-left:6px;font-size:12px;color:var(--mute)}
.tag{display:inline-block;font-size:11px;border-radius:10px;padding:0 7px;margin-left:4px;border:1px solid var(--line);color:var(--mute)}
.tag.no{border-color:var(--no);color:var(--no)}.tag.q{border-color:var(--q);color:var(--q)}
.what{margin:3px 0}
.meta{color:var(--mute);font-size:12.5px;margin:2px 0}
.meta b{color:var(--ink);font-weight:600}
.players{display:flex;flex-direction:column;gap:4px}
.pl{display:flex;flex-direction:column}
.pl span{font-size:12px;color:var(--mute)}
.pl.main span{color:var(--ink);font-weight:600}
audio{width:100%;height:32px}
.extra summary{cursor:pointer;font-size:12px;color:var(--mute)}
.vote{display:flex;flex-direction:column;gap:6px}
.btns{display:flex;gap:6px}
.btns button{flex:1;font-weight:650;padding:6px 0}
.btns button.on.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btns button.on.no{background:var(--no);border-color:var(--no);color:#fff}
.btns button.on.q{background:var(--q);border-color:var(--q);color:#111}
textarea.note{width:100%;min-height:34px;resize:vertical;font:inherit;font-size:13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 7px}
#result{width:100%;min-height:150px;font:12.5px ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);padding:10px}
.copied{color:var(--ok);font-weight:600;margin-left:8px}
footer{color:var(--mute);font-size:12.5px;margin-top:24px}
@media (max-width:900px){.row{grid-template-columns:1fr}}
"""

PAGE_JS = r"""
const KEY = "__KEY__";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = s => s.toFixed(2).replace(".", ",") + " s";
const audio = src => `<audio controls preload="none" src="${esc(src)}"></audio>`;
function rowHTML(it){
  const s = st(it.id);
  let players = `<div class="pl main"><span>Alternativa ${esc(it.id.slice(-1))} · ${fmt(it.dur)}</span>${audio(it.src)}</div>`;
  players += `<div class="pl"><span>El rechazado (${esc(it.lump)}, ${esc(it.verdict)})</span>${audio(it.rej)}</div>`;
  players += `<div class="pl"><span>Hoy en el juego: ${esc(it.rep)}</span>${audio(it.repSrc)}</div>`;
  if (it.extras.length) players += `<details class="extra" open><summary>Con el gatillo apretado (como en el juego)</summary>${it.extras.map(e => `<div class="pl"><span>${esc(e.l)}</span>${audio(e.src)}</div>`).join("")}</details>`;
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><div class="name"><code>${esc(it.id)}</code><span class="ev">${esc(it.ev)}</span></div>
      <div class="what"><b>${esc(it.label)}.</b> ${esc(it.what)}</div>
      <div class="meta"><b>Nivel:</b> ${esc(it.lvl)}</div></div>
    <div class="players">${players}</div>
    <div class="vote"><div class="btns">
      <button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
      <textarea class="note" placeholder="Nota (opcional)">${esc(s.n || "")}</textarea></div>
  </div>`;
}
function build(){
  let h = "", lumps = [...new Set(ITEMS.map(i => i.lump))];
  for (const L of lumps) {
    const its = ITEMS.filter(i => i.lump === L), a = its[0];
    const tag = a.verdict === "NO" ? `<span class="tag no">dijiste NO</span>` : `<span class="tag q">dijiste ?</span>`;
    h += `<details class="grp" open><summary><code>${esc(L)}</code> ${esc(a.group)} · ${esc(a.ev)} ${tag}<span class="rejnote">rechazado: ${esc(a.rejWhat)}</span><span class="gcount" data-l="${esc(L)}"></span></summary>`;
    for (const it of its) h += rowHTML(it);
    h += `</details>`;
  }
  document.getElementById("groups").innerHTML = h;
  for (const it of ITEMS) paint(it.id);
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
  r.classList.toggle("hide", document.getElementById("onlyOpen").checked && !!s.v);
}
function summary(){
  const by = v => ITEMS.filter(i => st(i.id).v === v).map(i => i.id);
  const done = ITEMS.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  document.getElementById("pBar").style.width = (100 * done / ITEMS.length) + "%";
  for (const L of new Set(ITEMS.map(i => i.lump))) {
    const g = ITEMS.filter(i => i.lump === L), d = g.filter(i => st(i.id).v).length;
    const el = document.querySelector(`.gcount[data-l="${L}"]`); if (el) el.textContent = `${d} / ${g.length}`;
  }
  const notes = ITEMS.filter(i => (st(i.id).n || "").trim()).map(i => `${i.id}: «${st(i.id).n.trim().replace(/\s+/g, " ")}»`);
  const open = ITEMS.filter(i => !st(i.id).v).map(i => i.id);
  const L = [`Alternativas M3 (__STAMP__): ${done}/${ITEMS.length} juzgadas`,
    `OK (${by("ok").length}): ${by("ok").join(", ") || "—"}`,
    `NO (${by("no").length}): ${by("no").join(", ") || "—"}`,
    `? (${by("q").length}): ${by("q").join(", ") || "—"}`,
    `notas: ${notes.join(" / ") || "—"}`];
  if (open.length) L.push(`sin juzgar (${open.length}): ${open.join(", ")}`);
  document.getElementById("result").value = L.join("\n");
}
function copy(){
  const t = document.getElementById("result"), msg = document.getElementById("copied");
  summary();
  const done = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? done() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } t.scrollIntoView({block:"center"}); };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(done, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.addEventListener("play", e => { document.querySelectorAll("audio").forEach(a => { if (a !== e.target) a.pause(); }); }, true);
document.getElementById("onlyOpen").addEventListener("change", () => ITEMS.forEach(i => paint(i.id)));
document.getElementById("copyTop").addEventListener("click", copy);
document.getElementById("copyBottom").addEventListener("click", copy);
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar todas las respuestas y notas de esta hoja?")) { S = {}; save(); build(); summary(); } });
build(); summary();
"""


def page_html(done: list[Rendered], page: Path, out_dir: Path, stamp: str) -> str:
    items = page_items(done, page, out_dir)
    n = len(items)
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    js = PAGE_JS.replace("__KEY__", PAGE_KEY_PREFIX + stamp).replace("__STAMP__", stamp)
    allow = ", ".join(f"{k} {v:g} dB" for k, v in ALLOWANCE_DB.items())
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alternativas de sonido M3</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Alternativas de sonido M3</h1>
  <span class="prog">Juzgadas <b id="pDone">0</b> de <b>{n}</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> solo sin juzgar</label>
  <button class="primary" id="copyTop">Copiar resultado</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>Tres alternativas <b>distintas</b> (otro gesto u otro material, no retoques) para cada sonido de arma que marcaste <b>NO</b> (<code>SDTTPKP</code>, <code>SDIZRLD</code>, <code>SDRKFIR</code>) o <b>?</b> (<code>SDAXPKP</code>, <code>SDIZPKP</code>) en la hoja de escucha (D74). En cada fila: la alternativa, debajo el borrador rechazado y lo que suena hoy en el juego (Freedoom). Pulsa <b>OK</b>, <b>NO</b> o <b>?</b> y escribe una nota si quieres. Se guarda solo en este navegador. Al terminar, <b>Copiar resultado</b> y pégalo en el chat.</p>
  <ul>
    <li><b>Volumen: ya están subidas.</b> Pico a −1 dBFS y la parte más fuerte a pocos dB de la de Freedoom (margen: recoger y recarga {ALLOWANCE_DB["pickup"]:g} dB, lanzallamas {ALLOWANCE_DB["fire"]:g} dB). Los borradores rechazados siguen al volumen antiguo, más bajo: compara el carácter, no el volumen.</li>
    <li><b>Ninguna depende solo de los graves:</b> al menos la mitad de la energía de cada una está por encima de 300 Hz, para que se oigan en altavoces de portátil.</li>
    <li><b>Lanzallamas:</b> el juego lo reinicia cada 3 tics mientras aprietas. Por eso cada alternativa tiene una versión «con el gatillo apretado» 1,2 s y soltado; es lo que oirás de verdad. Los primeros 3 tics enlazan consigo mismos sin corte.</li>
    <li><b>Recarga de la IZh:</b> el cierre cae a 0,62 s, en el fotograma donde el juego cuenta los cartuchos.</li>
    <li>Fuentes: nuestra síntesis y los dos paquetes CC0 que ya usamos (Kenney Impact Sounds y 100 CC0 SFX). Nada descargado.</li>
  </ul>
</section>
<main id="groups"></main>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Resultado para pegar en el chat</h2>
  <p class="meta">Se actualiza solo. Si el botón no copia (algunos navegadores lo bloquean en archivos locales), selecciona el texto y Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copiar resultado</button> <button id="reset">Borrar todas mis respuestas</button></p>
</section>
<footer>Generado {html.escape(stamp)} por sound-designer con <code>tools/audio/gen_weapon_alts.py</code>. Audio: <code>work/audio/alt/</code> (alternativas), <code>work/audio/sfx/weapons/ogg/</code> (rechazados), <code>work/audio/preview/freedoom/</code> (Freedoom de hoy). Margen de volumen: {html.escape(allow)}. La página lee los archivos del repo por ruta relativa: no la muevas de <code>docs/art/previews/</code>.</footer>
</div>
<script>
const ITEMS = {data};
{js}
</script>
</body>
</html>
"""


def plan_text() -> str:
    L = []
    for a in ALTS:
        ref = TARGETS[a.lump][0]
        L.append(f"{a.name:13s} {a.kind:7s} target loudA {target_db(a):5.1f} (vs {ref})  "
                 f"{a.label}: {', '.join(a.sources) or 'synthesis only'}")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print the plan, write nothing")
    ap.add_argument("--out", type=Path, default=OUT_DIR, help="output directory")
    ap.add_argument("--page", type=Path, help="also write the listening page here")
    ap.add_argument("--stamp", help="the page's YYYY-MM-DD_HHMM (default: from its file name)")
    ap.add_argument("names", nargs="*", help="only these alternatives or lumps")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")    # Spanish labels on a Windows console
    except (AttributeError, ValueError):            # pragma: no cover - a replaced stream
        pass
    if args.list:
        print(plan_text())
        return 0
    sources = AltSources()
    done, skipped = build(args.names or None, sources)
    for s in skipped:
        print(f"skipped: {s}", file=sys.stderr)
    if not done:
        return 1
    write_outputs(done, args.out, sources)
    print(manifest_text(done, sources), end="")
    if args.page:
        stamp = args.stamp or args.page.name[:15]
        args.page.parent.mkdir(parents=True, exist_ok=True)
        args.page.write_text(page_html(done, args.page.resolve(), args.out.resolve(), stamp),
                             encoding="utf-8")
        print(f"page: {args.page}")
    return 0 if not skipped else 2


if __name__ == "__main__":
    sys.exit(main())
