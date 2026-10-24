#!/usr/bin/env python3
"""World sounds (v1.1): drafts for the sounds that were still Freedoom's.

D125 (2026-10-23): the CEO approved 50 of the 56 and asked for SDPLOOF w1
over w3's impact; tools/audio/master_world_sfx.py installs them byte for
byte (and renders that layer from this file's recipes). This file still
writes candidates only.

CLAUDE.md lists what the player still hears from the IWAD: the player's own
voice (pain, death, the "oof" of a landing, the use that does nothing, the
jump), the doors (normal and fast, opening and closing), the switches
(normal and exit), the pickups (item, power-up, and the IZh-58's, D94), the
lift (start, stop, the moving floor's loop) and the teleporter. Each gets 2-3
candidates with a 1970s Soviet identity: armoured bunker doors and bulkheads,
bakelite toggles and knife switches, metal pickups, an ANS-synthesiser
teleporter, a Sputnik beep for the power-up.

Three kinds of material, in the order the brief prefers:

* synthesis, with the DSP of gen_weapon_sfx.py and gen_sfx.py (as D83's);
* CC0 recordings downloaded without an account for this round (BigSoundBank,
  work/audio/sfx_sources/world/SOURCES.md), plus the CC0 packs on disk since
  D36 (Kenney, OGA-100) and one installed lump of ours;
* the sergeant's wordless voice: the HaelDB CC0 recordings themselves (a
  vocalist the enemies do not clone) and Chatterbox takes cloned from them
  (work/audio/candidates/world/voice/gen_player_voice.py).

Same chain and ruler as the installed sounds and the D107 dog candidates:
mono 44.1 kHz; loudest 50 ms A-weighted (gen_weapon_alts.loud_a_db) matched
to the Freedoom lump each replaces (the IZh pickup: DSWPNUP - 3 dB, the
weapon pickups' rule of gen_weapon_alts.ALLOWANCE_DB); peak -1 dBFS through
the look-ahead limiter, at most master_weapon_sfx.MAX_LIMIT_DB; voices
levelled by process_voice_takes.level (saturation, never a limiter on a
held vowel); the moving floor's loop by gain only, so it stays seamless;
Vorbis q4, decoded peak under master_weapon_sfx.DECODED_PEAK_CEILING_DBFS.

Downloads are untrusted data: they are only DECODED, by ffmpeg
(gen_weapon_sfx.decode); nothing in them is run.

    .venv/Scripts/python.exe -I tools/audio/gen_world_sfx.py            # candidates + page
    .venv/Scripts/python.exe -I tools/audio/gen_world_sfx.py --list     # the plan, writes nothing

Writes work/audio/candidates/world/<LUMP>_w<N>.ogg (+ wav/, MANIFEST.tsv),
the Freedoom lumps as WAV in work/audio/preview/world_freedoom/ and the page
work/audio/preview/world_sounds_listening.html. Touches nothing in assets/
or src/.
"""

from __future__ import annotations

import html
import json
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_sfx as gs  # noqa: E402  (spectral filters, reverb, crackle, varispeed)
import gen_weapon_alts as alts  # noqa: E402  (the ruler and the limiter)
import gen_weapon_sfx as gws  # noqa: E402  (decode, synthesis atoms, WAV/OGG writers)
import master_weapon_sfx as mws  # noqa: E402  (limit and codec ceilings)
import process_voice_takes as pvt  # noqa: E402  (voice trim and level)

SR = gws.SR
assert gs.SAMPLE_RATE == SR
ROOT = gws.PROJECT_ROOT
WORK = ROOT / "work" / "audio"
OUT_DIR = WORK / "candidates" / "world"
VOICE_RAW = OUT_DIR / "voice" / "raw"
PREVIEW_DIR = WORK / "preview"
PAGE = PREVIEW_DIR / "world_sounds_listening.html"
FD_DIR = PREVIEW_DIR / "world_freedoom"
IWAD = ROOT / "iwads" / "freedoom2.wad"

PEAK_DBFS = -1.0
EDGE_FADE_S = 0.004
LOOP_XFADE_S = 0.06           # the moving floor's loop: equal-power crossfade of its seam
LOOP_PREVIEW_REPEATS = 6      # the page plays the loop this many times, as the engine would
PICKUP_ALLOWANCE_DB = alts.ALLOWANCE_DB["pickup"]   # weapon pickups sit 3 dB under DSWPNUP
STAMP = "2026-10-22"

# Freedoom 0.13.0 lumps these replace, measured 2026-10-22 from iwads/freedoom2.wad
# with gen_weapon_alts.loud_a_db (loudest 50 ms, A-weighted, dB, at their own rate);
# tests/test_gen_world_sfx.py re-measures them when the IWAD is present.
FREEDOOM_LOUD_A: dict[str, float] = {
    "DSPLPAIN": -10.17, "DSPLDETH": -8.44, "DSPDIEHI": -8.58, "DSOOF": -22.48,
    "DSNOWAY": -17.34, "DSJUMP": -13.21, "DSDOROPN": -15.46, "DSDORCLS": -15.78,
    "DSBDOPN": -16.79, "DSBDCLS": -17.04, "DSSWTCHN": -17.67, "DSSWTCHX": -5.10,
    "DSITEMUP": -20.29, "DSGETPOW": -11.29, "DSWPNUP": -5.20, "DSPSTART": -15.02,
    "DSPSTOP": -15.72, "DSSTNMOV": -21.46, "DSTELEPT": -11.80,
}
FREEDOOM_LENGTH_S: dict[str, float] = {
    "DSPLPAIN": 0.81, "DSPLDETH": 0.75, "DSPDIEHI": 0.80, "DSOOF": 0.36, "DSNOWAY": 0.39,
    "DSJUMP": 0.27, "DSDOROPN": 1.65, "DSDORCLS": 1.66, "DSBDOPN": 0.84, "DSBDCLS": 0.73,
    "DSSWTCHN": 0.82, "DSSWTCHX": 0.39, "DSITEMUP": 0.20, "DSGETPOW": 0.41, "DSWPNUP": 0.52,
    "DSPSTART": 1.20, "DSPSTOP": 1.10, "DSSTNMOV": 0.27, "DSTELEPT": 1.07,
}


# --- Sources ------------------------------------------------------------------

@dataclass(frozen=True)
class Source:
    path: str            # under work/audio/ (sfx_sources/..., voice_refs/...) or the repo (assets/...)
    who: str             # author and collection, for the page
    licence: str         # "CC0 1.0", "CC BY 3.0", or "ours"
    url: str = ""

    @property
    def file(self) -> Path:
        return ROOT / self.path if self.path.startswith("assets/") else WORK / self.path


BSB = "Joseph Sardin, BigSoundBank"
BSB_URL = "https://bigsoundbank.com/"


def _bsb(n: str, what: str, page: str, author: str = BSB) -> Source:
    return Source(f"sfx_sources/world/bsb-{n}/{n}.wav", f"{author} #{n} ({what})", "CC0 1.0", BSB_URL + page)


HAEL = "voice_refs/haeldb/unz/yelling sounds/"
HAEL_URL = "https://opengameart.org/content/male-gruntyelling-sounds"

SOURCES: dict[str, Source] = {
    # BigSoundBank, downloaded 2026-10-22 (work/audio/sfx_sources/world/SOURCES.md)
    "bar_open1": _bsb("2355", "large metal barrier, opening", "grinding-metal-barrier-opening-1-s2355.html"),
    "bar_open3": _bsb("2357", "large metal barrier, opening", "grinding-metal-barrier-opening-3-s2357.html"),
    "bar_close1": _bsb("2358", "large metal barrier, slamming", "grinding-metal-barrier-closure-1-s2358.html"),
    "bar_close2": _bsb("2359", "large metal barrier, slamming", "grinding-metal-barrier-closure-2-s2359.html"),
    "bar_close3": _bsb("2360", "large metal barrier, slamming", "grinding-metal-barrier-closure-3-s2360.html"),
    "groan": _bsb("0616", "creaking metal door", "creaking-metallic-door-s0616.html"),
    "pneu": _bsb("1490", "pneumatic brake released", "pneumatic-brake-released-s1490.html"),
    "strike": _bsb("3442", "electric strike", "electric-strike-1-s3442.html"),
    "isw1": _bsb("3061", "large industrial switch", "industrial-switch-1-s3061.html"),
    "isw2": _bsb("3062", "large industrial switch", "industrial-switch-2-s3062.html"),
    "isw3": _bsb("3063", "large industrial switch", "industrial-switch-3-s3063.html"),
    "breaker": _bsb("1092", "electric circuit breaker", "electric-circuit-breaker-s1092.html"),
    "hoist": _bsb("1133", "chain hoist", "manual-chain-hoist-mounted-s1133.html"),
    "chain": _bsb("0359", "heavy chain", "heavy-chain-s0359.html", "DenisChardonnet, BigSoundBank"),
    "winch": _bsb("0708", "electric winch", "little-electric-winch-s0708.html"),
    "lift": _bsb("1711", "elevator, 3 floors", "elevator-3-floors-s1711.html"),
    "case1": _bsb("1367", "7.62 case on concrete", "bullet-case-7-62mm-on-concrete-1-s1367.html"),
    "load": _bsb("1988", "loading a magazine", "gun-loading-1-s1988.html"),
    "cock": _bsb("1984", "cocking a pistol", "pistol-cocking-1-s1984.html"),
    "shock": _bsb("0134", "electric spark", "electric-shock-s0134.html"),
    "weld": _bsb("0952", "short welds", "short-welds-s0952.html"),
    "barnlock": _bsb("1540", "barn lock locking", "barn-lock-locking-s1540.html"),
    "barnunlock": _bsb("1539", "barn lock unlocking", "barn-lock-unlocking-s1539.html"),
    "anvil": _bsb("3590", "anvil", "anvil-2-s3590.html", "Pablo Bergel, BigSoundBank"),
    # On disk since D36 (docs/sound/ENEMY-SOUNDS.md section 5.9)
    "steps": Source("sfx_sources/ken-imp/extracted/Audio/footstep_concrete_000.ogg",
                    "Kenney, Impact Sounds (footstep on concrete)", "CC0 1.0", "https://kenney.nl/assets/impact-sounds"),
    "steps2": Source("sfx_sources/ken-imp/extracted/Audio/footstep_concrete_003.ogg",
                     "Kenney, Impact Sounds (footstep on concrete)", "CC0 1.0", "https://kenney.nl/assets/impact-sounds"),
    "metal_light": Source("sfx_sources/ken-imp/extracted/Audio/impactMetal_light_002.ogg",
                          "Kenney, Impact Sounds (light metal impact)", "CC0 1.0", "https://kenney.nl/assets/impact-sounds"),
    # The sergeant: HaelDB's recordings, the vocalists the enemies do not clone (CC0)
    "hael_y12": Source(HAEL + "yell12.wav", "HaelDB, unnumbered vocalist, yell12", "CC0 1.0", HAEL_URL),
    "hael_y2": Source(HAEL + "yell2.wav", "HaelDB, unnumbered vocalist, yell2", "CC0 1.0", HAEL_URL),
    "hael_y4": Source(HAEL + "yell4.wav", "HaelDB, unnumbered vocalist, yell4", "CC0 1.0", HAEL_URL),
    "hael_2y9": Source(HAEL + "2yell9.wav", "HaelDB, vocalist 2, 2yell9", "CC0 1.0", HAEL_URL),
    "hael_g3": Source(HAEL + "3grunt3.wav", "HaelDB, vocalist 3, grunt 3grunt3", "CC0 1.0", HAEL_URL),
    "hael_g4": Source(HAEL + "3grunt4.wav", "HaelDB, vocalist 3, grunt 3grunt4", "CC0 1.0", HAEL_URL),
    "hael_g5": Source(HAEL + "3grunt5.wav", "HaelDB, vocalist 3, grunt 3grunt5", "CC0 1.0", HAEL_URL),
    # Ours, installed: the rifleman's gib (D83; a layer of Freedoom's DSSLOP, BSD-3)
    "gib": Source("assets/sounds/enemies/SDRRIXDT.ogg", "our SDRRIXDT (D83; with a layer of Freedoom's DSSLOP, BSD-3)",
                  "ours"),
}

# A Chatterbox take is named "ai:<take>" in a candidate's sources; its file is in VOICE_RAW.
AI_WHO = "Chatterbox (MIT) cloning HaelDB, unnumbered vocalist (CC0)"

_cache: dict[str, np.ndarray] = {}


class Missing(RuntimeError):
    pass


def src(key: str) -> np.ndarray:
    if key not in _cache:
        p = VOICE_RAW / f"{key[3:]}.wav" if key.startswith("ai:") else SOURCES[key].file
        if not p.is_file():
            raise Missing(str(p))
        x = gws.decode(p)
        _cache[key] = x - np.mean(x)
    return _cache[key]


def clip(key: str, t0: float = 0.0, t1: float | None = None, fin: float = EDGE_FADE_S,
         fout: float = EDGE_FADE_S) -> np.ndarray:
    x = src(key)
    a = int(round(t0 * SR))
    b = len(x) if t1 is None else min(len(x), int(round(t1 * SR)))
    return gs.fade(x[a:b].copy(), fin, fout)


def st(x: np.ndarray, semitones: float) -> np.ndarray:
    """Varispeed (tape): down is bigger, heavier and slower."""
    return x if semitones == 0 else gws.resample(x, 2 ** (semitones / 12))


def unit(x: np.ndarray) -> np.ndarray:
    p = np.max(np.abs(x))
    return x / p if p > 0 else x


def seq(*parts: tuple[np.ndarray, float, float]) -> np.ndarray:
    """Mix (sound, start seconds, gain dB) into one buffer."""
    end = max(int(round(t * SR)) + len(s) for s, t, _ in parts)
    out = np.zeros(end)
    for s, t, g in parts:
        a = int(round(t * SR))
        out[a:a + len(s)] += s * 10 ** (g / 20)
    return out


def bp(x: np.ndarray, lo: float | None = None, hi: float | None = None, order: int = 2) -> np.ndarray:
    return gws.filt(x, lambda f: gws.butter(f, lo=lo, hi=hi, order=order))


def eq(x: np.ndarray, f0: float, gain_db: float, width_oct: float = 0.8) -> np.ndarray:
    return gs.spectral(x, lambda f: gs._peak_mag(f, f0, gain_db, width_oct))


def room(x: np.ndarray, rng, rt60: float = 0.9, wet_db: float = -11.0, lp: float = 3500.0) -> np.ndarray:
    """A concrete bunker corridor: a dark, fairly short tail."""
    return gs.reverb(x, rng, rt60=rt60, wet_db=wet_db, lp_hz=lp)


def tail(x: np.ndarray, out_s: float, length_s: float | None = None) -> np.ndarray:
    if length_s is not None:
        x = x[:int(round(length_s * SR))]
    return gs.fade(x, 0.002, out_s)


# --- Synthesis atoms ------------------------------------------------------------

def steel_slam(rng, size: float = 1.0, length: float = 1.2) -> np.ndarray:
    """A thick steel door hitting its frame: the body thump, the plate ringing
    (inharmonic, low partials longest), a dark burst of the impact itself."""
    n = gws.n_of(length)
    base = 120.0 / size
    plate = gs.ring(n, base, (1.0, 2.32, 3.86, 5.41, 7.13, 9.20, 11.6),
                    (0.55, 0.40, 0.28, 0.20, 0.13, 0.09, 0.06), (0, -2, -4, -6, -9, -12, -15))
    body = gs.thump(n, 75.0 / size, 38.0 / size, 0.16)
    hit = bp(rng.standard_normal(n) * gws.env(n, 0.0005, 0.035), lo=80, hi=2600)
    return unit(body) + 0.5 * unit(plate) * gws.env(n, 0.001, 0.35) + 0.7 * unit(hit)


def latch(rng, pitch: float = 1.0) -> np.ndarray:
    """One bolt shooting home: a hard click and a short small-metal ring."""
    n = gws.n_of(0.12)
    c = gws.click(rng, 2200 * pitch, decay=0.004)
    r = gws.ring((1750 * pitch, 3080 * pitch, 4630 * pitch), 0.035, 0.12)
    out = np.zeros(n)
    gws.place(out, unit(c), 0.0)
    gws.place(out, 0.35 * unit(r), 0.002)
    thud = gs.thump(n, 220 * pitch, 140 * pitch, 0.02)
    return out + 0.5 * thud


def bolts(rng, count: int = 3, spacing: float = 0.055, pitch: float = 0.8) -> np.ndarray:
    """The dogs of a hermetic door, one after the other, a little out of step."""
    parts = []
    t = 0.0
    for i in range(count):
        parts.append((latch(rng, pitch * rng.uniform(0.92, 1.08)), t, -1.5 * i))
        t += spacing * rng.uniform(0.8, 1.25)
    return seq(*parts)


def hiss(rng, length: float, attack: float, decay: float, lo: float = 1500.0, hi: float = 9000.0,
         hold: float = 0.0) -> np.ndarray:
    """Compressed air let out of a door ram."""
    n = gws.n_of(length)
    return bp(rng.standard_normal(n) * gws.env(n, attack, decay, hold), lo=lo, hi=hi)


def rumble(rng, length: float, lo: float = 35.0, hi: float = 260.0, rate: float = 9.0,
           attack: float = 0.08, release: float = 0.12) -> np.ndarray:
    """A heavy door on its rollers: low band noise, lumpy at the rollers' rate."""
    n = gws.n_of(length)
    x = bp(rng.standard_normal(n), lo=lo, hi=hi)
    x = gs.am(x, rate, 0.45, 2.0)
    e = np.ones(n)
    a, r = gws.n_of(attack), gws.n_of(release)
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] *= np.linspace(1, 0, r)
    return x * e


def grind(rng, length: float, lo: float = 500.0, hi: float = 3200.0) -> np.ndarray:
    """Steel dragging on steel: rough band noise and a faint, unsteady squeal."""
    n = gws.n_of(length)
    s = gws.scrape(rng, length, lo, hi, attack=0.06, decay=length)
    f = 820 + 90 * gws.wobble(rng, n, 6.0)
    squeal = gs.tone(f, n) * (0.5 + 0.5 * np.abs(gws.wobble(rng, n, 14.0))) * gws.env(n, 0.1, length)
    return unit(s) + 0.12 * squeal


def mains_hum(length: float, attack: float = 0.02, decay: float = 0.4, base: float = 50.0) -> np.ndarray:
    """The USSR's 50 Hz grid through a transformer: 100 Hz and its family."""
    n = gws.n_of(length)
    t = gws.times(n)
    x = (0.4 * np.sin(2 * np.pi * base * t) + np.sin(2 * np.pi * 2 * base * t)
         + 0.5 * np.sin(2 * np.pi * 4 * base * t) + 0.3 * np.sin(2 * np.pi * 6 * base * t)
         + 0.15 * np.sin(2 * np.pi * 8 * base * t))
    return x * gws.env(n, attack, decay)


def motor(rng, length: float, f0: float, f1: float, tau: float, gain_env=None) -> np.ndarray:
    """An electric hoist motor: a sawtooth gliding between speeds, dulled, plus its hum."""
    n = gws.n_of(length)
    f = f1 + (f0 - f1) * np.exp(-gws.times(n) / tau)
    x = bp(gs.saw(f, n), lo=40, hi=1400) + 0.3 * bp(gs.saw(f * 2.01, n), lo=200, hi=2500)
    x = x * (1 + 0.15 * gws.wobble(rng, n, 7.0))
    if gain_env is not None:
        x = x * gain_env
    return x


def relay(rng, pitch: float = 1.0) -> np.ndarray:
    """A contactor pulling in: a dull clack and a buzz of the armature."""
    n = gws.n_of(0.09)
    k = gws.click(rng, 1300 * pitch, decay=0.006)
    b = gs.thump(n, 300 * pitch, 160 * pitch, 0.018)
    out = np.zeros(n)
    gws.place(out, unit(k), 0.0)
    return out + 0.6 * unit(b)


def arc(rng, length: float, rate0: float = 900.0, rate1: float = 80.0) -> np.ndarray:
    """An electric arc: spark grains thinning out over a 100 Hz buzz."""
    n = gws.n_of(length)
    sparks = gs.crackle(rng, length, rate0, rate1, grain_s=0.0015, lo=1800.0, hi=10000.0)
    buzz = bp(gs.saw(100.0 + 3 * gws.wobble(rng, n, 30.0), n), lo=150, hi=4000)
    buzz = buzz * np.abs(gws.wobble(rng, n, 60.0)) * gws.env(n, 0.002, length / 3)
    return unit(sparks) + 0.35 * unit(buzz)


def tock(rng, f0: float = 1100.0, decay: float = 0.012) -> np.ndarray:
    """Bakelite: a hollow, woody plastic knock with a narrow resonance."""
    n = gws.n_of(0.06)
    x = rng.standard_normal(n) * gws.env(n, 0.0003, decay)
    return gws.filt(x, lambda f: gws.butter(f, lo=400, hi=4000) * gws.bump(f, f0, 6, 14))


def beep(freq: float, length: float, attack: float = 0.004, release: float = 0.012) -> np.ndarray:
    """A valve oscillator's beep: a sine with some odd harmonics."""
    n = gws.n_of(length)
    t = gws.times(n)
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 3 * freq * t) + 0.12 * np.sin(2 * np.pi * 5 * freq * t)
    e = np.ones(n)
    a, r = gws.n_of(attack), gws.n_of(release)
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] *= np.linspace(1, 0, r)
    return x * e


def radio(x: np.ndarray, rng, lo: float = 300.0, hi: float = 3200.0, drive: float = 1.6,
          static_db: float = -26.0) -> np.ndarray:
    """A 1970s receiver: band-limited, a little driven, with a bed of static."""
    y = gws.saturate(bp(x, lo=lo, hi=hi), drive)
    st_ = bp(rng.standard_normal(len(y)), lo=1500, hi=7000) * 10 ** (static_db / 20)
    return y + st_


def make_loop(x: np.ndarray, loop_s: float, xfade_s: float = LOOP_XFADE_S) -> np.ndarray:
    """Cut a seamless loop of loop_s from x (which must be at least loop_s + xfade_s long):
    the xfade_s after the loop is folded onto its start with an equal-power crossfade, so
    sample loop[-1] runs into loop[0] the way x[L-1] runs into x[L]."""
    L, X = gws.n_of(loop_s), gws.n_of(xfade_s)
    if len(x) < L + X:
        raise ValueError("source shorter than the loop and its crossfade")
    out = x[:L].copy()
    w = np.linspace(0, np.pi / 2, X)
    out[:X] = x[:X] * np.sin(w) + x[L:L + X] * np.cos(w)
    return out


VOICE_ONSET = 0.1        # the cry starts where it first reaches 10 % of its peak...
VOICE_PREROLL_S = 0.01   # ...less 10 ms: a pain sound must not lag the hit


def from_onset(y: np.ndarray) -> np.ndarray:
    i = int(np.argmax(np.abs(y) >= VOICE_ONSET * np.max(np.abs(y))))
    return gs.fade(y[max(0, i - gws.n_of(VOICE_PREROLL_S)):], 0.004, 0.0005)


def ai_voice(name: str) -> np.ndarray:
    """A raw Chatterbox take: high-passed and trimmed as the enemy voices are."""
    y, _ = pvt.trim(pvt.high_pass(src("ai:" + name)), SR)
    if len(y) == 0:
        raise Missing(f"silent take {name}")
    return from_onset(y)


def rec_voice(key: str, semis: float = 0.0, chest_db: float = 0.0, max_s: float | None = None) -> np.ndarray:
    """A HaelDB recording: trimmed like a take, a touch lower and fuller if asked."""
    y, _ = pvt.trim(pvt.high_pass(src(key)), SR)
    y = st(from_onset(y), semis)
    if chest_db:
        y = eq(y, 170.0, chest_db, 1.0)
    if max_s is not None and len(y) > gws.n_of(max_s):
        y = tail(y, 0.08, max_s)
    return y


# --- The recipes --------------------------------------------------------------------
# Times are seconds in the source, found on its 10 ms envelope (onsets, segment ends);
# nobody here can listen, so every cut is placed by measurement. st = semitones.
# Voice takes chosen from work/audio/candidates/world/voice/raw by length and trim.

AI = {  # the Chatterbox takes the page offers (picked by gen_world_sfx's metrics, see MANIFEST)
    "pain": "PLP_SDPLPAIN_ai_chatterbox_20261022_t01",
    "death": "PLD_SDPLDETH_ai_chatterbox_20261022_t03",
    "xdeath": "PLX_SDPLXDTH_ai_chatterbox_20261022_t03",
    "oof": "PLO_SDPLOOF_ai_chatterbox_20261022_t03",
}


# Player ------------------------------------------------------------------------------

def plpain1(rng):
    return rec_voice("hael_y12", -1.0, 3.0, max_s=0.55)


def plpain2(rng):
    return eq(st(ai_voice(AI["pain"]), -1.0), 170.0, 2.0, 1.0)


def plpain3(rng):
    return rec_voice("hael_2y9", 0.0, 2.0, max_s=0.55)


def pldeth1(rng):
    return rec_voice("hael_y2", -1.5, 3.0, max_s=1.25)


def pldeth2(rng):
    return eq(st(ai_voice(AI["death"]), -1.0), 170.0, 2.0, 1.0)


def pldeth3(rng):   # the cry, then the body and the kit on the concrete
    v = rec_voice("hael_y2", -2.0, 3.0, max_s=1.0)
    fall = seq((unit(st(clip("steps", 0, 0.25), -6)), 0.0, 0), (gs.thump(gws.n_of(0.3), 110, 55, 0.08), 0.01, -4),
               (unit(gws.grit(rng, 0.25, 7, 0.0, 0.12, 0.06, 2500, 6000)), 0.03, -12))
    return seq((unit(v), 0.0, 0), (unit(fall), len(v) / SR - 0.12, -8))


def plxdth1(rng):
    v = rec_voice("hael_y4", -1.5, 2.0, max_s=0.9)
    return seq((unit(v), 0.0, 0), (unit(clip("gib")), 0.05, -7))


def plxdth2(rng):
    v = eq(st(ai_voice(AI["xdeath"]), -1.0), 170.0, 2.0, 1.0)
    return seq((unit(v), 0.0, 0), (unit(clip("gib")), 0.05, -7))


def plxdth3(rng):
    return rec_voice("hael_y4", -2.5, 3.0, max_s=1.0)


def ploof1(rng):
    return st(ai_voice(AI["oof"]), -2.0)


def boots(rng) -> np.ndarray:
    """Two boots and the kit landing on concrete: a heel, the other heel, webbing and a canteen."""
    l = unit(st(clip("steps", 0, 0.22), -3))
    r = unit(st(clip("steps2", 0, 0.22), -4))
    body = gs.thump(gws.n_of(0.25), 95, 55, 0.06)
    kit = gws.grit(rng, 0.2, 6, 0.0, 0.08, 0.05, 2200, 5500)
    return seq((l, 0.0, 0), (r, 0.035, -2), (body, 0.0, -3), (unit(kit), 0.02, -14))


def ploof2(rng):
    return boots(rng)


def ploof3(rng):
    g = rec_voice("hael_g4", -3.0, 3.0, max_s=0.3)
    return seq((unit(boots(rng)), 0.0, -2), (unit(g), 0.02, 0))


def plnowy1(rng):   # a bolt that will not move: rattled against its keeper
    return st(clip("barnlock", 1.25, 1.72, 0.004, 0.06), -2.0)


def plnowy2(rng):   # synth: the handle yanked, the steel does not give
    n = gws.n_of(0.4)
    thud = gs.thump(n, 140, 85, 0.05)
    rattle = seq(*[(latch(rng, 0.55), 0.03 + 0.045 * i + rng.uniform(0, 0.01), -4 - 3 * i) for i in range(3)])
    return tail(seq((unit(thud), 0.0, 0), (unit(rattle), 0.0, -6)), 0.08)


def plnowy3(rng):
    g = rec_voice("hael_g5", -2.0, 3.0, max_s=0.35)
    r = st(clip("barnlock", 1.25, 1.55, 0.004, 0.05), -3.0)
    return seq((unit(g), 0.0, 0), (unit(r), 0.03, -9))


def pljump1(rng):   # the kit jolting: webbing, a strap, the canteen knocking
    c = gws.cloth(rng, 0.16, 0.01, 0.05)
    kit = gws.grit(rng, 0.22, 5, 0.02, 0.1, 0.06, 1800, 5000)
    knock = gs.thump(gws.n_of(0.12), 260, 180, 0.02)
    return seq((unit(c), 0.0, 0), (unit(kit), 0.0, -6), (unit(knock), 0.06, -10))


def pljump2(rng):
    g = rec_voice("hael_g3", -3.0, 2.0, max_s=0.24)
    return seq((unit(g), 0.0, 0), (unit(gws.cloth(rng, 0.14, 0.01, 0.05)), 0.0, -8))


# Doors -------------------------------------------------------------------------------

def doropn1(rng):   # hermetic door: the dogs drawn back, the ram's air, the slab rolling aside
    b = st(clip("barnunlock", 1.55, 1.78), -4)
    b2 = st(clip("barnunlock", 2.25, 2.55), -4)
    air = st(clip("pneu", 0.12, 0.85, 0.002, 0.2), -2)
    slide = st(clip("bar_open1", 0.15, 1.75, 0.03, 0.25), -5)[:gws.n_of(1.15)]
    rum = rumble(rng, 1.1, rate=8.0)
    x = seq((unit(b), 0.0, -2), (unit(b2), 0.12, -4), (unit(air), 0.16, -6), (unit(slide), 0.28, 0),
            (unit(rum), 0.30, -7))
    return tail(room(x, rng), 0.25, 1.7)


def doropn2(rng):   # synthesis
    x = seq((unit(bolts(rng, 3)), 0.0, -2), (unit(hiss(rng, 0.6, 0.004, 0.18)), 0.12, -8),
            (unit(rumble(rng, 1.15, rate=9.0)), 0.22, 0), (unit(grind(rng, 1.05)), 0.26, -10),
            (unit(steel_slam(rng, 1.4, 0.6)), 1.36, -9))
    return tail(room(x, rng), 0.25, 1.7)


def doropn3(rng):   # the long groan of a heavy hinged door, after its lever
    lever = st(clip("barnlock", 1.25, 1.45), -4)
    g = st(clip("groan", 0.05, 2.14, 0.02, 0.3), -4)[:gws.n_of(1.4)]
    x = seq((unit(lever), 0.0, -2), (unit(g), 0.10, 0), (unit(rumble(rng, 1.3, rate=6.0)), 0.12, -10))
    return tail(room(x, rng), 0.3, 1.65)


def dorcls1(rng):   # slides home and slams; the dogs go in after it
    slide = st(clip("bar_open3", 0.29, 1.25, 0.05, 0.02), -5)
    slam = st(clip("bar_close1", 1.45, 2.48, 0.002, 0.3), -4)
    lock = st(clip("barnlock", 1.25, 1.45), -4)
    x = seq((unit(slide), 0.0, -4), (unit(rumble(rng, 0.85, rate=8.0)), 0.0, -8),
            (unit(slam), 0.78, 0), (gs.thump(gws.n_of(0.4), 70, 38, 0.12), 0.78, -3), (unit(lock), 1.22, -8))
    return tail(room(x, rng), 0.25, 1.7)


def dorcls2(rng):   # synthesis
    x = seq((unit(rumble(rng, 0.9, rate=9.0)), 0.0, -2), (unit(grind(rng, 0.85)), 0.04, -12),
            (unit(steel_slam(rng, 1.0)), 0.86, 0), (unit(bolts(rng, 3)), 1.24, -9))
    return tail(room(x, rng), 0.3, 1.7)


def dorcls3(rng):   # the hinge groans shut, the slab hits the frame
    g = st(clip("groan", 15.10, 16.30, 0.05, 0.05), -4)[:gws.n_of(0.95)]
    slam = st(clip("bar_close3", 0.20, 0.98, 0.002, 0.25), -3)
    x = seq((unit(g), 0.0, -3), (unit(slam), 0.9, 0), (gs.thump(gws.n_of(0.4), 70, 38, 0.12), 0.9, -4))
    return tail(room(x, rng), 0.3, 1.7)


def bdopn1(rng):   # the fast door: lock buzz, a blast of air, a quick slide
    s = clip("strike", 0.02, 0.28, 0.002, 0.03)
    air = clip("pneu", 0.15, 0.6, 0.002, 0.12)
    slide = st(clip("bar_open3", 0.29, 0.85, 0.01, 0.1), -2)
    x = seq((unit(s), 0.0, -8), (unit(air), 0.08, -2), (unit(slide), 0.14, -1), (unit(latch(rng, 0.6)), 0.62, -8))
    return tail(room(x, rng, 0.7), 0.15, 0.88)


def bdopn2(rng):
    x = seq((unit(relay(rng)), 0.0, -6), (unit(hiss(rng, 0.45, 0.003, 0.12, 1200, 9000)), 0.03, 0),
            (unit(rumble(rng, 0.55, rate=16.0, attack=0.03, release=0.06)), 0.07, -2),
            (unit(steel_slam(rng, 1.6, 0.4)), 0.6, -10))
    return tail(room(x, rng, 0.7), 0.15, 0.85)


def bdopn3(rng):
    air = clip("pneu", 0.15, 0.7, 0.002, 0.12)
    slide = st(clip("bar_open1", 0.17, 0.95, 0.01, 0.12), -3)
    return tail(room(seq((unit(air), 0.0, -2), (unit(slide), 0.05, 0)), rng, 0.7), 0.15, 0.88)


def bdcls1(rng):
    air = clip("pneu", 0.15, 0.45, 0.002, 0.08)
    slam = st(clip("bar_close2", 1.08, 1.78, 0.002, 0.2), -3)
    return tail(room(seq((unit(air), 0.0, -4), (unit(slam), 0.16, 0)), rng, 0.7), 0.15, 0.78)


def bdcls2(rng):
    x = seq((unit(hiss(rng, 0.3, 0.003, 0.08, 1200, 9000)), 0.0, -3),
            (unit(rumble(rng, 0.2, rate=18.0, attack=0.02, release=0.03)), 0.0, -4),
            (unit(steel_slam(rng, 0.85, 0.6)), 0.17, 0))
    return tail(room(x, rng, 0.7), 0.15, 0.78)


def bdcls3(rng):
    air = clip("pneu", 0.15, 0.4, 0.002, 0.06)
    slam = st(clip("bar_close3", 0.20, 0.85, 0.002, 0.2), -2)
    return tail(room(seq((unit(air), 0.0, -8), (unit(slam), 0.12, 0)), rng, 0.7), 0.15, 0.78)


# Switches ----------------------------------------------------------------------------

def swtchn1(rng):   # a big industrial throw switch, as made by BigSoundBank (switch, iron bar, reverb)
    return tail(st(clip("isw2", 0.0, 1.0, 0.001, 0.25), -2), 0.2)


def swtchn2(rng):   # a cabinet breaker and the panel's transformer coming up
    k = st(clip("breaker", 0.27, 0.75, 0.001, 0.15), -3)
    hum = mains_hum(0.7, 0.03, 0.22)
    return tail(room(seq((unit(k), 0.0, 0), (unit(hum), 0.02, -14), (unit(relay(rng, 0.8)), 0.14, -10)), rng, 0.6),
                0.15, 0.82)


def swtchn3(rng):   # synthesis: a bakelite toggle, then a relay in the wall
    t1 = tock(rng, 1050.0, 0.010)
    snap = gws.click(rng, 3200, 0.003)
    x = seq((unit(t1), 0.0, 0), (unit(snap), 0.018, -6), (unit(relay(rng, 0.7)), 0.13, -5),
            (unit(mains_hum(0.5, 0.02, 0.15)), 0.14, -16))
    return tail(room(x, rng, 0.6, -14), 0.12, 0.7)


def knife(rng) -> np.ndarray:
    """A knife switch (рубильник) thrown: blades scraping into the jaws, the
    contact snapping home, an arc, the load coming on."""
    scr = gws.scrape(rng, 0.09, 1500, 7000, attack=0.01, decay=0.03)
    snap = seq((unit(latch(rng, 0.9)), 0.0, 0), (gs.thump(gws.n_of(0.2), 160, 90, 0.04), 0.0, -2))
    x = seq((unit(scr), 0.0, -6), (unit(snap), 0.07, 0), (unit(arc(rng, 0.3, 1400.0, 300.0)), 0.072, -1),
            (unit(mains_hum(0.32, 0.005, 0.2)), 0.075, -4))
    return x


def swtchx1(rng):
    return tail(room(knife(rng), rng, 0.6, -12), 0.12, 0.5)


def swtchx2(rng):
    s = clip("isw1", 0.0, 0.42, 0.001, 0.12)
    a = clip("shock", 18.58, 18.74, 0.002, 0.05)
    x = seq((unit(s), 0.0, 0), (unit(a), 0.02, 0), (gs.thump(gws.n_of(0.2), 150, 80, 0.04), 0.0, -4))
    return tail(gws.saturate(x, 2.5), 0.08, 0.42)


def swtchx3(rng):
    s = clip("isw3", 0.0, 0.39, 0.001, 0.12)
    k = clip("breaker", 0.28, 0.45, 0.001, 0.08)
    return tail(gws.saturate(seq((unit(s), 0.0, 0), (unit(k), 0.0, -3)), 2.5), 0.08, 0.42)


# Pickups -----------------------------------------------------------------------------

def itemup1(rng):   # a 7.62 case on concrete: the ammo you just picked up
    return tail(st(clip("case1", 0.06, 0.34, 0.001, 0.06), -2), 0.05)


def itemup2(rng):   # synthesis: a canvas pouch and its buckle
    c = gws.cloth(rng, 0.1, 0.006, 0.03)
    k = gws.click(rng, 2600, 0.003)
    r = gws.ring((2350, 4120, 6050), 0.03, 0.12)
    return tail(seq((unit(c), 0.0, -4), (unit(k), 0.05, 0), (unit(r), 0.052, -8)), 0.05, 0.2)


def itemup3(rng):   # a round pressed into a magazine, and the pouch
    k = clip("load", 0.31, 0.46, 0.001, 0.05)
    return tail(seq((unit(gws.cloth(rng, 0.09, 0.006, 0.03)), 0.0, -8), (unit(st(k, -1)), 0.02, 0)), 0.05, 0.22)


def getpow1(rng):   # synthesis: Sputnik's beep-beep on a valve receiver (PS-1, 1957)
    b = beep(1000.0, 0.11)
    x = seq((b, 0.0, 0), (b, 0.2, 0))
    return tail(radio(x, rng, static_db=-34.0), 0.04, 0.36)


def getpow2(rng):   # synthesis: an ANS-like chord rising, as in 70s Soviet science fiction
    n = gws.n_of(0.46)
    t = gws.times(n)
    f = 220 * 2 ** (2 * np.clip(t / 0.36, 0, 1))
    x = np.zeros(n)
    for r, g in ((1.0, 1.0), (1.498, 0.6), (2.0, 0.5), (2.997, 0.3), (4.01, 0.18)):
        vib = 1 + 0.006 * np.sin(2 * np.pi * 6.2 * t + r)
        x += g * gs.tone(f * r * vib, n)
    x *= gws.env(n, 0.03, 0.2, 0.18)
    return tail(room(x, rng, 0.8, -12, 6000), 0.06, 0.46)


def getpow3(rng):   # synthesis: a relay, then a condenser charging up with a whine
    n = gws.n_of(0.44)
    whine = gs.tone(gs.glide(1800, 5200, n), n) * gws.env(n, 0.06, 0.25, 0.1)
    x = seq((unit(relay(rng)), 0.0, 0), (unit(whine), 0.03, -8), (unit(mains_hum(0.44, 0.08, 0.3)), 0.02, -6))
    return tail(x, 0.05, 0.44)


def izpkp1(rng):   # two strokes of a steel action, a little heavier than a pistol's
    a = clip("cock", 0.04, 0.17, 0.001, 0.02)
    b = clip("cock", 1.45, 1.56, 0.001, 0.04)
    return tail(gws.saturate(st(seq((unit(a), 0.0, 0), (unit(b), 0.21, 0)), -3), 2.5), 0.06, 0.5)


def izpkp2(rng):
    a = st(clip("load", 0.31, 0.42, 0.001, 0.02), -2)
    b = st(clip("cock", 1.45, 1.56, 0.001, 0.04), -3)
    m = st(clip("metal_light", 0.0, 0.25, 0.001, 0.08), -2)
    return tail(seq((unit(a), 0.0, -1), (unit(b), 0.2, 0), (unit(m), 0.205, -9)), 0.06, 0.5)


def izpkp3(rng):   # synthesis, Doom's shape: two sharp steel clacks and a slide between
    def clack(p):
        c = gws.click(rng, 2600 * p, 0.003)
        r = gws.ring((740 * p, 2040 * p, 3900 * p), 0.05, 0.16)
        return seq((unit(c), 0.0, 0), (unit(r), 0.001, -7), (gs.thump(gws.n_of(0.08), 300 * p, 180 * p, 0.015), 0.0, -6))
    sl = gws.scrape(rng, 0.12, 1800, 6500, attack=0.02, decay=0.05)
    return tail(seq((clack(1.0), 0.0, 0), (unit(sl), 0.07, -12), (clack(0.85), 0.21, 0)), 0.06, 0.5)


# Lift --------------------------------------------------------------------------------

def pstart1(rng):   # synthesis: the contactor pulls in, the motor spins up, the chain takes the load
    n = gws.n_of(1.2)
    e = gws.env(n, 0.25, 2.0)
    m = motor(rng, 1.2, 22.0, 92.0, 0.35, e)
    ch = gws.grit(rng, 1.0, 22, 0.15, 0.8, 0.5, 2000, 6000)
    whine = gs.tone(300 * (1100 / 300) ** np.clip(gws.times(n) / 0.5, 0, 1), n) * e
    x = seq((unit(relay(rng, 0.6)), 0.0, 0), (unit(m), 0.04, -3), (unit(mains_hum(1.15, 0.2, 2.0)), 0.04, -12),
            (unit(ch), 0.0, -7), (unit(whine), 0.04, -14), (unit(rumble(rng, 1.1, 30, 180, 5.0, 0.3, 0.05)), 0.1, -8))
    return tail(room(x, rng, 0.8, -13), 0.12, 1.2)


def pstart2(rng):   # a real lift starting (a Paris elevator), the first 1.25 s of its run
    return tail(clip("lift", 3.38, 4.70, 0.01, 0.15), 0.15)


def pstart3(rng):
    w = st(clip("winch", 0.18, 1.06, 0.03, 0.15), -5)
    ch = st(clip("chain", 2.21, 2.70, 0.005, 0.1), -3)
    x = seq((unit(relay(rng, 0.6)), 0.0, -2), (unit(w), 0.05, 0), (unit(ch), 0.3, -8))
    return tail(room(x, rng, 0.8, -13), 0.15, 1.2)


def pstop1(rng):   # synthesis: the motor winds down, the brake bites, the platform settles
    n = gws.n_of(0.6)
    m = motor(rng, 0.6, 92.0, 25.0, 0.18, gws.env(n, 0.0, 0.2))
    whine = gs.tone(1100 * (300 / 1100) ** np.clip(gws.times(n) / 0.25, 0, 1), n) * gws.env(n, 0.0, 0.15)
    x = seq((unit(m), 0.0, -2), (unit(whine), 0.0, -12), (unit(steel_slam(rng, 1.3, 0.8)), 0.18, -1),
            (unit(bolts(rng, 2, 0.08, 0.6)), 0.24, -6),
            (unit(gws.grit(rng, 0.5, 10, 0.0, 0.3, 0.15, 2000, 6000)), 0.2, -9))
    return tail(room(x, rng, 0.9, -12), 0.2, 1.1)


def pstop2(rng):   # the same lift arriving: its second loud event (NOT VERIFIED by ear: arrival or doors)
    return tail(clip("lift", 23.80, 24.98, 0.005, 0.2), 0.2)


def pstop3(rng):   # an anvil blow, nine semitones down: a platform of plate hitting its stop
    a = st(clip("anvil", 1.18, 1.96, 0.001, 0.2), -9)
    ch = st(clip("chain", 3.28, 3.50, 0.002, 0.06), -3)
    x = seq((unit(a), 0.0, 0), (gs.thump(gws.n_of(0.4), 80, 40, 0.12), 0.0, -3), (unit(ch), 0.05, -10))
    return tail(room(x, rng, 0.9, -12), 0.2, 1.1)


MOVE_LOOP_S = 0.48


def pmove1(rng):   # synthesis: motor hum, roller rumble and two pawl clicks per turn, periodic
    L = MOVE_LOOP_S
    n = gws.n_of(L * 3)
    t = gws.times(n)
    f = 1 / L                                  # every partial a multiple of 1/L: the loop is exact
    m = sum(g * np.sin(2 * np.pi * round(fr / f) * f * t)
            for fr, g in ((96, 0.6), (192, 0.6), (288, 0.5), (400, 0.35), (600, 0.25), (800, 0.15)))
    rum = rumble(rng, L * 3, 60, 900, 2 / L, 0.001, 0.001)
    clicks = np.zeros(n)
    for k in range(6):
        gws.place(clicks, unit(gws.click(rng, 1600, 0.006)), k * L / 2 + 0.01)
    x = unit(m) + 0.8 * unit(rum) + 0.35 * unit(clicks)
    return make_loop(x[gws.n_of(L):], L)


def pmove2(rng):   # the winch's steady run, six semitones down
    return make_loop(st(clip("winch", 10.0, 11.0, 0.0, 0.0), -6), MOVE_LOOP_S)


def pmove3(rng):   # the chain hoist's ratchet, five down
    return make_loop(st(clip("hoist", 8.0, 9.0, 0.0, 0.0), -5), MOVE_LOOP_S)


# Teleport ----------------------------------------------------------------------------

def telept1(rng):   # synthesis: an ANS-like cluster rising out of the mains hum, sparks at the top
    n = gws.n_of(1.05)
    t = gws.times(n)
    base = 110 * 2 ** (2 * np.clip(t / 0.8, 0, 1))
    x = np.zeros(n)
    for i, r in enumerate((1.0, 1.5, 2.02, 2.99, 4.03, 5.04, 6.1)):
        sh = 0.6 + 0.4 * np.abs(gws.wobble(rng, n, 9.0 + i))
        x += gs.tone(base * r, n) * sh / (1 + 0.5 * i)
    x *= gws.env(n, 0.12, 0.25, 0.65)
    y = seq((unit(x), 0.0, 0), (unit(mains_hum(1.0, 0.3, 0.5)), 0.0, -8), (unit(arc(rng, 0.3)), 0.62, -8),
            (gs.thump(gws.n_of(0.3), 90, 45, 0.08), 0.75, -6))
    return tail(room(y, rng, 1.0, -10, 6000), 0.15, 1.08)


def telept2(rng):   # recorded arcs over a rising tone
    a1 = clip("shock", 18.20, 18.74, 0.003, 0.05)
    a2 = clip("shock", 20.28, 20.60, 0.003, 0.05)
    w = clip("weld", 2.77, 3.50, 0.02, 0.15)
    n = gws.n_of(1.0)
    rise = gs.tone(gs.glide(160, 640, n), n) * gws.env(n, 0.3, 0.25, 0.5)
    y = seq((unit(rise), 0.0, -4), (unit(w), 0.05, -6), (unit(a1), 0.3, -2), (unit(a2), 0.62, -3))
    return tail(room(y, rng, 0.8, -12), 0.15, 1.08)


def telept3(rng):   # synthesis: a reversed tail sucking in, then a struck steel ring
    n = gws.n_of(0.55)
    rev = (bp(rng.standard_normal(n), 400, 6000) * gws.env(n, 0.0, 0.18))[::-1]
    bell = gs.ring(gws.n_of(0.7), 330.0, (1.0, 2.76, 5.40, 8.93), (0.5, 0.3, 0.18, 0.1), (0, -4, -8, -12))
    y = seq((unit(rev), 0.0, -2), (unit(mains_hum(0.9, 0.4, 0.3)), 0.0, -10), (unit(bell), 0.5, 0),
            (unit(arc(rng, 0.2)), 0.5, -12))
    return tail(room(y, rng, 1.0, -10, 6000), 0.15, 1.1)


# --- The table ------------------------------------------------------------------------

@dataclass(frozen=True)
class Event:
    lump: str          # what it would ship as
    ref: str           # the Freedoom lump it replaces (target loudness)
    engine: str        # the engine names that play it today
    group: str         # the page's section
    ev: str            # the event, in words
    note: str          # when the player hears it
    why: str           # why the recommended one
    offset_db: float = 0.0
    loop: bool = False

    @property
    def target_db(self) -> float:
        return FREEDOOM_LOUD_A[self.ref] + self.offset_db


@dataclass(frozen=True)
class Cand:
    lump: str
    n: int
    make: Callable
    kind: str                       # "synthesis", "recording", "mix", "recorded voice", "AI voice"
    sources: tuple[str, ...]
    label: str
    what: str
    rec: bool = False

    @property
    def name(self) -> str:
        return f"{self.lump}_w{self.n}"

    @property
    def voice(self) -> bool:
        return self.kind.endswith("voice")


def ai(key: str) -> str:
    return "ai:" + AI[key]


EVENTS: tuple[Event, ...] = (
    Event("SDPLPAIN", "DSPLPAIN", "*pain100 (and *pain75/50/25)", "Player (the sergeant)", "pain",
          "Plays every time you are hit: short, and wordless (the sergeant does not speak).",
          "w1: a real recording, short (0.5 s) and low, of a person who is none of the enemies."),
    Event("SDPLDETH", "DSPLDETH", "*death", "Player (the sergeant)", "death",
          "Once per lost game; just before the «Press E to continue».",
          "w3: the cry and, at the end, the body and the kit on the concrete; it reads without seeing the screen."),
    Event("SDPLXDTH", "DSPDIEHI", "*xdeath", "Player (the sergeant)", "violent death (explosion)",
          "When you die blown apart: a harsher cry with our enemies' «gib» under it.",
          "w1: a short real cry with D83's gib under it; the same body you hear in the enemies."),
    Event("SDPLOOF", "DSOOF", "*grunt and *land", "Player (the sergeant)", "«oof» on a long fall",
          "On landing from a fall. Freedoom's is very quiet (−22 dB): we match it, so it is discreet.",
          "w3: the boots and the kit on the floor with a short grunt on top; the grunt alone (w1) is mistaken for pain."),
    Event("SDPLNOWY", "DSNOWAY", "*usefail", "Player (the sergeant)", "using something that does not open",
          "On pressing E against a wall or a locked door.",
          "w1: a bolt that will not give, rattled against its keeper: it says «it is locked» without a voice."),
    Event("SDPLJUMP", "DSJUMP", "*jump", "Player (the sergeant)", "jump",
          "Only if jumping is allowed (in GZDoom it is by default; NOT VERIFIED in our maps).",
          "w1: the kit jolting, no voice: a grunt on every jump gets tiring at once."),
    Event("SDDOROPN", "DSDOROPN", "doors/dr1_open", "Doors", "normal door, opens",
          "The bunker's armoured door: bolts, the ram's air and the slab rolling (it lasts as long as the movement, ~1.6 s).",
          "w1: real recordings (bolt, pneumatic brake, steel barrier) 4-5 semitones lower so it weighs like a bulkhead."),
    Event("SDDORCLS", "DSDORCLS", "doors/dr1_clos", "Doors", "normal door, closes",
          "The slab rolls and hits the frame; the bolts go in after.",
          "w1: the steel barrier's real slam, lower, with the bolts after: a bulkhead closing."),
    Event("SDBDOPN", "DSBDOPN", "doors/dr2_open", "Doors", "fast door, opens",
          "The «blazing» (fast) doors: all in under a second.",
          "w1: the electric strike's buzz and the blast of air before the slide: it sounds like a mechanism, not a hinge."),
    Event("SDBDCLS", "DSBDCLS", "doors/dr2_clos", "Doors", "fast door, closes",
          "Air and a slam, fast.",
          "w2: synthesis, the lowest and driest slam; the recordings (w1, w3) are higher."),
    Event("SDSWTCHN", "DSSWTCHN", "switches/normbutn", "Switches", "normal switch",
          "Every switch in the map (D25's SDSW1A-D).",
          "w2: a switchboard circuit breaker and the transformer coming up (the Soviet grid's 50 Hz): heavy, industrial."),
    Event("SDSWTCHX", "DSSWTCHX", "switches/exitbutn", "Switches", "exit switch",
          "The end-of-map one: the loudest of all (Freedoom −5 dB).",
          "w1: a рубильник (knife switch) with its spark: the end of the map with an electric arc."),
    Event("SDITEMUP", "DSITEMUP", "misc/i_pkup and misc/k_pkup", "Pickups", "item (ammo, medkit, armour, key)",
          "Very short and quiet (Freedoom 0.2 s, −20 dB): it plays hundreds of times.",
          "w2: neutral synthesis (canvas and buckle) that suits ammo, medkit and key; the cases (w1) only fit the ammo."),
    Event("SDGETPOW", "DSGETPOW", "misc/p_pkup", "Pickups", "power-up",
          "The special pickups (sphere, berserk, invulnerability…).",
          "w1: Sputnik's «beep-beep» on a valve radio: the most Soviet thing you can hear in half a second."),
    Event("SDIZPKP", "DSWPNUP", "misc/w_pkup (the IZh-58 has no sound of its own)", "Pickups", "picking up the IZh-58",
          "In D94 you said NO to the three alternatives and kept Freedoom's: these imitate its shape (two dry steel knocks) with our own material. Level: the other weapons' (DSWPNUP −3 dB).",
          "w3: synthesis with the exact shape of Freedoom's (two clacks and a slide) and the timbre of the IZh's barrels.",
          offset_db=-PICKUP_ALLOWANCE_DB),
    Event("SDPSTART", "DSPSTART", "plats/pt1_strt", "Lift and platforms", "platform starts",
          "A freight lift: contactor, motor spinning up, chain.",
          "w1: synthesis; the contactor and the accelerating electric motor come through clearly; the lift recording (w2) I could not check by ear."),
    Event("SDPSTOP", "DSPSTOP", "plats/pt1_stop", "Lift and platforms", "platform stops",
          "Also plays when a moving floor or ceiling finishes (the «stopsound»).",
          "w3: an anvil blow 9 semitones lower: a plate platform hitting its stop."),
    Event("SDPMOVE", "DSSTNMOV", "plats/pt1_mid (loop)", "Lift and platforms", "floor or ceiling moving (loop)",
          "Repeats non-stop while a floor or a ceiling moves («playrepeat»): the sheet plays it 6 times in a row, as the engine does.",
          "w1: synthesis; its hum fits whole in 0.48 s, so the seam barely exists (all three also carry a 60 ms crossfade on it); the recordings (w2, w3) repeat a real chunk and may show more.",
          loop=True),
    Event("SDTELEPT", "DSTELEPT", "misc/teleport", "Teleport", "teleport",
          "On entering a teleporter (and when the General's enemies appear).",
          "w1: synthesis in the style of the ANS synthesiser (1970s Soviet science fiction) over the mains hum and a spark."),
)
EVENT = {e.lump: e for e in EVENTS}

C = Cand
CANDS: tuple[Cand, ...] = (
    C("SDPLPAIN", 1, plpain1, "recorded voice", ("hael_y12",), "Real grunt",
      "A short pain cry by HaelDB (unnumbered vocalist), 1 semitone lower and with more chest.", True),
    C("SDPLPAIN", 2, plpain2, "AI voice", (ai("pain"),), "Cloned grunt",
      "Chatterbox (CPU) cloning the same voice, «Agh!», 1 semitone lower."),
    C("SDPLPAIN", 3, plpain3, "recorded voice", ("hael_2y9",), "Real grunt, another voice",
      "A short cry by HaelDB, vocalist 2: the lowest of his series."),
    C("SDPLDETH", 1, pldeth1, "recorded voice", ("hael_y2",), "Death cry",
      "A long cry by HaelDB (unnumbered vocalist), 1.5 semitones lower."),
    C("SDPLDETH", 2, pldeth2, "AI voice", (ai("death"),), "Cloned cry",
      "Chatterbox cloning the same voice, «Aaaaah!»: a 1 s cry that falls (−1 semitone)."),
    C("SDPLDETH", 3, pldeth3, "mix", ("hael_y2", "steps"), "Cry and fall",
      "w1's cry a little shorter and, at the end, the body and the kit on the concrete.", True),
    C("SDPLXDTH", 1, plxdth1, "mix", ("hael_y4", "gib"), "Cry and gib",
      "A harsh cry by HaelDB with our D83 gib under it.", True),
    C("SDPLXDTH", 2, plxdth2, "AI voice", (ai("xdeath"), "gib"), "Cloned cry and gib",
      "Chatterbox, «AAAAH!», with the same gib under it."),
    C("SDPLXDTH", 3, plxdth3, "recorded voice", ("hael_y4",), "Harsh cry",
      "w1's cry, 2.5 semitones lower, without the gib."),
    C("SDPLOOF", 1, ploof1, "AI voice", (ai("oof"),), "Cloned «Ух»",
      "Chatterbox, a short, low «Ух.» (Russian) (−2 semitones)."),
    C("SDPLOOF", 2, ploof2, "mix", ("steps", "steps2"), "Boots and kit",
      "No voice: two heels on concrete (Kenney), the body and the kit jingling."),
    C("SDPLOOF", 3, ploof3, "mix", ("hael_g4", "steps", "steps2"), "Boots and grunt",
      "w2's boots with a short real grunt (HaelDB 3grunt4, −3 semitones).", True),
    C("SDPLNOWY", 1, plnowy1, "recording", ("barnlock",), "Bolt that will not give",
      "An iron bolt rattled against its keeper, 2 semitones lower.", True),
    C("SDPLNOWY", 2, plnowy2, "synthesis", (), "Tug against the steel",
      "Synthesis: a dull knock of the handle and the bolt shaking without moving."),
    C("SDPLNOWY", 3, plnowy3, "mix", ("hael_g5", "barnlock"), "Grunt of effort",
      "A real grunt of effort (HaelDB 3grunt5) with the rattled bolt under it."),
    C("SDPLJUMP", 1, pljump1, "synthesis", (), "The kit jolts",
      "Synthesis: webbing, a buckle and the canteen at take-off.", True),
    C("SDPLJUMP", 2, pljump2, "mix", ("hael_g3",), "Huff",
      "A short real huff (HaelDB 3grunt3, −3 semitones) and the canvas."),
    C("SDDOROPN", 1, doropn1, "mix", ("barnunlock", "pneu", "bar_open1"), "Hermetic door",
      "Bolts drawing back, the ram's air and the steel slab rolling (a real barrier, −5 semitones), in a concrete corridor.", True),
    C("SDDOROPN", 2, doropn2, "synthesis", (), "Synthetic bulkhead",
      "Synthesis: three bolts, a pneumatic hiss, rollers and the stop at the end."),
    C("SDDOROPN", 3, doropn3, "mix", ("barnlock", "groan"), "Groaning hinge",
      "The lever and the long groan of a heavy metal door (−4 semitones)."),
    C("SDDORCLS", 1, dorcls1, "mix", ("bar_open3", "bar_close1", "barnlock"), "Bulkhead slam",
      "The rolling slab, a steel barrier's real slam (−4 semitones) and the bolts.", True),
    C("SDDORCLS", 2, dorcls2, "synthesis", (), "Synthetic slam",
      "Synthesis: rollers, a thick plate hit with its ring, and three bolts."),
    C("SDDORCLS", 3, dorcls3, "mix", ("groan", "bar_close3"), "Hinge and slam",
      "The groan of the hinge closing and the hit against the frame."),
    C("SDBDOPN", 1, bdopn1, "mix", ("strike", "pneu", "bar_open3"), "Strike and air",
      "An electric strike's buzz, the air and a fast slide.", True),
    C("SDBDOPN", 2, bdopn2, "synthesis", (), "Synthetic pneumatics",
      "Synthesis: relay, a blast of air, fast rollers and a soft stop."),
    C("SDBDOPN", 3, bdopn3, "recording", ("pneu", "bar_open1"), "Air and barrier",
      "Recordings only: the pneumatic brake and the barrier opening (−3 semitones)."),
    C("SDBDCLS", 1, bdcls1, "recording", ("pneu", "bar_close2"), "Air and slam",
      "The air and the barrier's slam (−3 semitones)."),
    C("SDBDCLS", 2, bdcls2, "synthesis", (), "Fast synthetic slam",
      "Synthesis: a short hiss and the thick plate against the frame, lower than the recordings.", True),
    C("SDBDCLS", 3, bdcls3, "recording", ("pneu", "bar_close3"), "Dry slam",
      "Another slam of the barrier, with barely any air."),
    C("SDSWTCHN", 1, swtchn1, "recording", ("isw2",), "Industrial switch",
      "A large industrial switch with a hall echo (BigSoundBank made it with a switch, an iron bar and reverb), −2 semitones."),
    C("SDSWTCHN", 2, swtchn2, "mix", ("breaker",), "Breaker and transformer",
      "A real switchboard breaker (−3 semitones), a relay and the 50 Hz hum coming up.", True),
    C("SDSWTCHN", 3, swtchn3, "synthesis", (), "Bakelite toggle",
      "Synthesis: the hollow «tock» of bakelite, the spring and a relay in the wall."),
    C("SDSWTCHX", 1, swtchx1, "synthesis", (), "Рубильник with a spark",
      "Synthesis: the blades entering the jaws, the contact, an electric arc and the load coming on.", True),
    C("SDSWTCHX", 2, swtchx2, "mix", ("isw1", "shock"), "Switch and spark",
      "The industrial switch with a real spark on top."),
    C("SDSWTCHX", 3, swtchx3, "recording", ("isw3", "breaker"), "Switch and breaker",
      "Two recordings together: the industrial switch and the breaker."),
    C("SDITEMUP", 1, itemup1, "recording", ("case1",), "Cartridge case",
      "A 7.62 case on concrete (−2 semitones)."),
    C("SDITEMUP", 2, itemup2, "synthesis", (), "Canvas and buckle",
      "Synthesis: a canvas pouch and its metal buckle.", True),
    C("SDITEMUP", 3, itemup3, "mix", ("load",), "Round into the magazine",
      "A cartridge going into the magazine, and the canvas."),
    C("SDGETPOW", 1, getpow1, "synthesis", (), "Sputnik's beep-beep",
      "Synthesis: two beeps like Sputnik's (1957) on a valve radio, with some static.", True),
    C("SDGETPOW", 2, getpow2, "synthesis", (), "ANS chord",
      "Synthesis: a rising chord, with vibrato, in the style of the ANS synthesiser (Solaris, 1972)."),
    C("SDGETPOW", 3, getpow3, "synthesis", (), "Capacitor charging",
      "Synthesis: a relay and the whine of a capacitor charging over the mains hum."),
    C("SDIZPKP", 1, izpkp1, "recording", ("cock",), "Two steel knocks",
      "The two strokes of cocking a pistol, together and 3 semitones lower (more shotgun)."),
    C("SDIZPKP", 2, izpkp2, "mix", ("load", "cock", "metal_light"), "Load and lock",
      "A cartridge going in and the action closing with a light metal knock."),
    C("SDIZPKP", 3, izpkp3, "synthesis", (), "Freedoom's shape, IZh timbre",
      "Synthesis: two dry clacks with the ring of the IZh's barrels and a slide between them.", True),
    C("SDPSTART", 1, pstart1, "synthesis", (), "Contactor and motor",
      "Synthesis: the contactor pulling in, the electric motor spinning up, the chain and the hum.", True),
    C("SDPSTART", 2, pstart2, "recording", ("lift",), "Real lift",
      "An old Paris lift starting (1.3 s; which part of the run it is was not checked by ear)."),
    C("SDPSTART", 3, pstart3, "mix", ("winch", "chain"), "Winch and chain",
      "An electric winch starting (−5 semitones) and a heavy chain pulling taut."),
    C("SDPSTOP", 1, pstop1, "synthesis", (), "Brake and stop",
      "Synthesis: the motor stopping, the brake biting, the platform's knock and two bolts."),
    C("SDPSTOP", 2, pstop2, "recording", ("lift",), "Real lift, arrival",
      "The same lift's second loud event (arrival or doors: NOT checked by ear)."),
    C("SDPSTOP", 3, pstop3, "mix", ("anvil", "chain"), "Anvil blow",
      "A hammer blow on an anvil, 9 semitones lower, with the chain settling.", True),
    C("SDPMOVE", 1, pmove1, "synthesis", (), "Motor and rollers",
      "Synthesis: the motor's hum (partials that fit whole in the loop), rollers and two pawl clicks per turn; 0.48 s.", True),
    C("SDPMOVE", 2, pmove2, "recording", ("winch",), "Winch",
      "The electric winch running, 6 semitones lower, in a 0.48 s loop."),
    C("SDPMOVE", 3, pmove3, "recording", ("hoist",), "Chain hoist",
      "A chain hoist's ratchet, 5 semitones lower, in a 0.48 s loop."),
    C("SDTELEPT", 1, telept1, "synthesis", (), "ANS chord and spark",
      "Synthesis: a cluster of partials rising out of the mains hum, a spark at the top and a dull knock on arrival.", True),
    C("SDTELEPT", 2, telept2, "mix", ("shock", "weld"), "Electric arcs",
      "Real sparks and welding over a rising tone."),
    C("SDTELEPT", 3, telept3, "synthesis", (), "Suction and bell",
      "Synthesis: a reversed air sucking in and a struck steel ring."),
)


# --- Level, encode, page ------------------------------------------------------------------

def seed_of(name: str) -> int:
    return zlib.crc32(name.encode()) & 0xFFFFFFFF


def level(x: np.ndarray, target: float) -> tuple[np.ndarray, float]:
    """-> (sound at `target` loudness with peak <= -1 dBFS, dB of limiting). The dog candidates' rule."""
    x = unit(x)
    pk = 10 ** (PEAK_DBFS / 20)

    def at(c_db: float) -> np.ndarray:
        y = alts.limit(x, 10 ** (c_db / 20)) if c_db < 0 else x
        return y / np.max(np.abs(y)) * pk

    if alts.loud_a_db(at(0.0)) >= target:
        y = at(0.0)
        return y * 10 ** ((target - alts.loud_a_db(y)) / 20), 0.0
    lo, hi = -mws.MAX_LIMIT_DB, 0.0
    if alts.loud_a_db(at(lo)) < target - alts.LOUDNESS_TOLERANCE_DB:
        # Freedoom's 8-bit, clipped lumps (the exit switch, the weapon pickup) are denser than
        # 9 dB of limiting can make a clean transient: the weapons' handling chain then
        # (gen_weapon_alts.to_target: deeper look-ahead limiting, the fixed soft saturation).
        y, lim = alts.to_target(x, target, "pickup")
        return y, lim
    if alts.loud_a_db(at(lo)) < target:
        return at(lo), mws.MAX_LIMIT_DB
    for _ in range(22):
        mid = (lo + hi) / 2
        if alts.loud_a_db(at(mid)) < target:
            hi = mid
        else:
            lo = mid
    return at(lo), -lo


def level_loop(x: np.ndarray, target: float) -> np.ndarray:
    """Gain only (a limiter would bend the seam); never over -1 dBFS."""
    y = x * 10 ** ((target - alts.loud_a_db(np.tile(x, 3))) / 20)
    p = np.max(np.abs(y))
    ceiling = 10 ** (PEAK_DBFS / 20)
    return y * (ceiling / p) if p > ceiling else y


def codec_safe(y: np.ndarray, loop: bool = False) -> tuple[np.ndarray, bytes, float]:
    """Vorbis lifts dense peaks: limit (a loop: turn down) until the decoded peak is safe."""
    trim = 0.0
    for _ in range(6):
        ogg = gws.ogg_bytes(gws.wav_bytes(y))
        over = mws.decoded_peak_db(ogg) - mws.DECODED_PEAK_CEILING_DBFS
        if over <= 0:
            return y, ogg, trim
        trim += over + 0.1
        y = y * 10 ** (-(over + 0.1) / 20) if loop else alts.limit(y, 10 ** ((PEAK_DBFS - trim) / 20))
    return y, ogg, trim


@dataclass
class Done:
    cand: Cand
    y: np.ndarray
    limit_db: float
    trim_db: float
    drive: float
    levels: dict = field(default_factory=dict)


def render(c: Cand) -> Done:
    e = EVENT[c.lump]
    rng = np.random.default_rng(seed_of(c.name))
    x = c.make(rng)
    lim = drive = 0.0
    if e.loop:
        y = level_loop(x, e.target_db)
    elif c.voice:
        y, drive = pvt.level(x, e.target_db)
    else:
        y, lim = level(x, e.target_db)
    y, ogg, trim = codec_safe(y, e.loop)
    d = Done(c, y, lim, trim, drive)
    d.levels = alts.levels(np.tile(y, 3) if e.loop else y)
    d.levels["length"] = len(y) / SR
    d.ogg = ogg
    return d


def freedoom_wavs() -> list[str]:
    """The lumps the page plays as 'today', as WAV at their own rate; missing IWAD -> none."""
    FD_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for e in EVENTS:
        p = FD_DIR / f"{e.ref}.wav"
        if not p.is_file():
            data = gws.placeholder_wav(e.ref, IWAD)
            if data is None:
                continue
            p.write_bytes(data)
        made.append(e.ref)
    loop_ref = EVENT["SDPMOVE"].ref                    # the engine repeats it: so does the page
    p = FD_DIR / f"{loop_ref}_loop.wav"
    if (FD_DIR / f"{loop_ref}.wav").is_file() and not p.is_file():
        x, rate = alts.read_wav((FD_DIR / f"{loop_ref}.wav").read_bytes())
        p.write_bytes(gws.wav_bytes(np.tile(x, LOOP_PREVIEW_REPEATS * 2), rate))
    return made


def licence_chips(c: Cand) -> list[dict]:
    out = []
    for k in c.sources:
        if k.startswith("ai:"):
            out.append({"a": AI_WHO, "l": "AI voice"})
        else:
            s = SOURCES[k]
            out.append({"a": s.who, "l": "ours" if s.licence == "ours" else s.licence})
    if c.kind in ("synthesis", "mix") and not any(k.startswith("ai:") for k in c.sources):
        out.append({"a": "our own synthesis (tools/audio/gen_world_sfx.py)", "l": "ours"})
    return out


def fmt_db(v: float) -> str:
    return f"{v:.1f}"


def page_html(done: list[Done]) -> str:
    rel_c = "../candidates/world/"
    items = []
    for d in done:
        c, e, lv = d.cand, EVENT[d.cand.lump], d.levels
        shortfall = e.target_db - lv["loud_a"]
        lvl = (f"peak {fmt_db(lv['peak'])} dBFS · loudness {fmt_db(lv['loud_a'])} dB "
               f"(Freedoom {e.ref}{' −3' if e.offset_db else ''}: {fmt_db(e.target_db)})"
               + (f" · <b>falls {fmt_db(shortfall)} dB short</b>" if shortfall > alts.LOUDNESS_TOLERANCE_DB else "")
               + f" · {100 * lv['above300']:.0f} % above 300 Hz")
        items.append({"id": c.name, "lump": c.lump, "n": c.n, "label": c.label, "what": c.what, "kind": c.kind,
                      "rec": c.rec, "src": rel_c + (f"{c.name}_loop.ogg" if e.loop else f"{c.name}.ogg"),
                      "single": rel_c + f"{c.name}.ogg" if e.loop else "",
                      "dur": round(d.levels["length"], 2), "who": licence_chips(c), "lvl": lvl})
    events = []
    for e in EVENTS:
        if not any(d.cand.lump == e.lump for d in done):
            continue
        fd = f"world_freedoom/{e.ref}{'_loop' if e.loop else ''}.wav"
        events.append({"lump": e.lump, "ref": e.ref, "engine": e.engine, "group": e.group, "ev": e.ev,
                       "note": e.note, "why": e.why, "fd": fd, "fdlen": FREEDOOM_LENGTH_S[e.ref]})
    return (PAGE_TEMPLATE.replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__EVENTS__", json.dumps(events, ensure_ascii=False))
            .replace("__COUNT__", str(len(items))).replace("__STAMP__", STAMP))


def main(argv: list[str]) -> int:
    if "--list" in argv:
        for e in EVENTS:
            cs = [c for c in CANDS if c.lump == e.lump]
            print(f"{e.lump:9s} {e.ref:9s} target {e.target_db:6.2f}  {e.engine}")
            for c in cs:
                print(f"    w{c.n} {c.kind:12s} {'rec ' if c.rec else '    '}{c.label}  [{', '.join(c.sources) or 'synth'}]")
        return 0
    only = [a for a in argv if not a.startswith("-")]
    (OUT_DIR / "wav").mkdir(parents=True, exist_ok=True)
    freedoom_wavs()
    done, skipped = [], []
    for c in CANDS:
        if only and c.lump not in only and c.name not in only:
            continue
        try:
            d = render(c)
        except Missing as m:
            skipped.append(f"{c.name}: missing {m}")
            continue
        (OUT_DIR / "wav" / f"{c.name}.wav").write_bytes(gws.wav_bytes(d.y))
        (OUT_DIR / f"{c.name}.ogg").write_bytes(d.ogg)
        if EVENT[c.lump].loop:
            prev = np.tile(d.y, LOOP_PREVIEW_REPEATS)
            (OUT_DIR / f"{c.name}_loop.ogg").write_bytes(gws.ogg_bytes(gws.wav_bytes(prev)))
        done.append(d)
        lv = d.levels
        print(f"{c.name:12s} {c.kind:12s} loudA {lv['loud_a']:6.2f} (target {EVENT[c.lump].target_db:6.2f})"
              f" peak {lv['peak']:5.2f} lim {d.limit_db:3.1f} drive {d.drive:3.1f} codec {d.trim_db:3.1f}"
              f" len {lv['length']:4.2f}")
    rows = ["file\tlump\tref\ttarget_dB\tloud_A_dB\tpeak_dBFS\tlimit_dB\tvoice_drive\tcodec_trim_dB\t"
            "above300_pct\tlength_s\tkind\tsources\tsha256_ogg"]
    import hashlib
    for d in done:
        c, e, lv = d.cand, EVENT[d.cand.lump], d.levels
        srcs = "; ".join((k if k.startswith("ai:") else f"{SOURCES[k].who} [{SOURCES[k].licence}] {SOURCES[k].path}")
                         for k in c.sources) or "synthesis"
        rows.append(f"{c.name}.ogg\t{c.lump}\t{e.ref}\t{e.target_db:.2f}\t{lv['loud_a']:.2f}\t{lv['peak']:.2f}\t"
                    f"{d.limit_db:.1f}\t{d.drive:.2f}\t{d.trim_db:.1f}\t{100 * lv['above300']:.0f}\t{lv['length']:.2f}\t"
                    f"{c.kind}\t{srcs}\t{hashlib.sha256(d.ogg).hexdigest()}")
    if not only:
        (OUT_DIR / "MANIFEST.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        PAGE.write_text(page_html(done), encoding="utf-8")
        print(f"page: {PAGE}  ({len(done)} candidates)")
    for s in skipped:
        print("SKIPPED", s)
    return 0


PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World sounds</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4;--warn:#7a4b00;--warnbg:#fff4dc;--ai:#2b4f8a;--aibg:#e6eefb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--warn:#f0c674;--warnbg:#2f2814;--ai:#9dbcf0;--aibg:#1d2638}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--warn:#f0c674;--warnbg:#2f2814;--ai:#9dbcf0;--aibg:#1d2638}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
h2.sec{font-size:16px;margin:28px 0 4px;padding-bottom:4px;border-bottom:2px solid var(--accent)}
.prog{font-variant-numeric:tabular-nums;color:var(--mute)}
.prog b{color:var(--ink)}
.bar{flex:1 1 160px;height:6px;background:var(--chip);border-radius:3px;overflow:hidden;min-width:120px}
.bar i{display:block;height:100%;background:var(--accent);width:0}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
label.chk{color:var(--mute);user-select:none}
.intro{margin:14px 0}
.intro p{margin:6px 0}
.intro ul{margin:6px 0;padding-left:20px}
details.grp{margin:12px 0;border:1px solid var(--line);border-radius:8px;background:var(--card)}
details.grp>summary{cursor:pointer;padding:10px 12px;font-weight:650;font-size:15px;list-style:none;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
details.grp>summary::-webkit-details-marker{display:none}
details.grp>summary::before{content:"\25B8";color:var(--mute)}
details.grp[open]>summary::before{content:"\25BE"}
.gcount{margin-left:auto;font-weight:400;color:var(--mute);font-size:13px;font-variant-numeric:tabular-nums}
.rejnote{font-weight:400;color:var(--mute);font-size:13px}
.eng{font:12px ui-monospace,Consolas,monospace;color:var(--mute);font-weight:400}
.row{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr) 230px;gap:10px 16px;padding:10px 12px;border-top:1px solid var(--line)}
.row.hide{display:none}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
.name code{font:600 14px ui-monospace,Consolas,monospace}
.ev{display:inline-block;background:var(--chip);border-radius:10px;padding:0 8px;margin-left:6px;font-size:12px;color:var(--mute)}
.what{margin:3px 0}
.meta{color:var(--mute);font-size:12.5px;margin:2px 0}
.meta b{color:var(--ink);font-weight:600}
.players{display:flex;flex-direction:column;gap:4px}
.pl{display:flex;flex-direction:column}
.pl span{font-size:12px;color:var(--mute)}
.pl.main span{color:var(--ink);font-weight:600}
.pl a{font-size:12px;color:var(--mute)}
audio{width:100%;height:32px}
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
.rec{display:inline-block;font-size:11px;border-radius:10px;padding:0 7px;margin-left:6px;background:var(--ok);color:#fff}
.chip{display:inline-block;font-size:11.5px;border-radius:10px;padding:0 7px;margin:2px 4px 0 0;background:var(--chip);color:var(--ink)}
.chip.ai{background:var(--aibg);color:var(--ai)}
.chip.ours{background:transparent;border:1px solid var(--line);color:var(--mute)}
.refs{padding:8px 12px;border-top:1px solid var(--line);max-width:560px}
.why{padding:6px 12px 10px;color:var(--mute);font-size:13px}
.why b{color:var(--ink)}
@media (max-width:900px){.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>World sounds</h1>
  <span class="prog">Judged <b id="pDone">0</b> of <b id="pAll">__COUNT__</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> unjudged only</label>
  <button class="primary" id="copyTop">Copy result</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>Drafts to <b>replace the last sounds that are still Freedoom's</b>: the sergeant's voice, the doors, the switches, the pickups, the lift, the teleporter and the IZh pickup (D94). Two or three candidates per sound. Press <b>OK</b>, <b>NO</b> or <b>?</b> on each one (you can OK several: they would go in a <code>$random</code>, like the dogs) and write a note if you like; it is saved only in this browser. When you finish, <b>Copy result</b> and paste it in the chat. <b>Nothing is installed.</b></p>
  <ul>
    <li><b>At the top of each sound</b>: what plays <b>in the game today</b> (Freedoom's).</li>
    <li><b>Volume matched</b> to that Freedoom sound (the same rule as the enemies and the dogs), peak at most −1 dBFS; the IZh 3 dB under, like the other weapons. Compare the character, not the volume.</li>
    <li><b>Kind</b>: <i>synthesis</i> (made here with the repo's tools), <i>recording</i> (BigSoundBank, CC0, downloaded without an account), a <i>mix</i> of the two, <i>recorded voice</i> (HaelDB, CC0: a real person who is none of the enemies) or <i>AI voice</i> (Chatterbox cloning that same voice). Everything is <b>CC0 or ours</b>; nothing on this sheet is CC BY. Sources, URLs and SHA-256 in <code>work/audio/sfx_sources/world/SOURCES.md</code>.</li>
    <li><b>Recommended</b>: chosen by measurements and spectrum, <b>not by ear</b> (I cannot listen). Your ear decides.</li>
  </ul>
</section>
<main id="groups"></main>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Result to paste in the chat</h2>
  <p class="meta">It updates itself. If the button does not copy (some browsers block it on local files), select the text and press Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copy result</button> <button id="reset">Clear all my answers</button></p>
</section>
<footer>Generated __STAMP__ by sound-designer with <code>tools/audio/gen_world_sfx.py</code> (synthesis, cuts, varispeed, filters, bunker reverb and levelling with the tools in <code>tools/audio/</code>; measurements in <code>work/audio/candidates/world/MANIFEST.tsv</code>). AI voices: <code>work/audio/candidates/world/voice/</code> (AI-LOG.csv). Audio: <code>work/audio/candidates/world/</code> (candidates), <code>work/audio/preview/world_freedoom/</code> (Freedoom). The page reads the files by relative path: do not move it out of <code>work/audio/preview/</code>.</footer>
</div>
<script>
const ITEMS = __ITEMS__;
const EVENTS = __EVENTS__;
const KEY = "sd-v11-world-2026-10-22";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = s => s.toFixed(2) + " s";
const audio = src => `<audio controls preload="none" src="${esc(src)}"></audio>`;
const vote = it => `<div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div><textarea class="note" placeholder="Note (optional)">${esc(st(it.id).n || "")}</textarea></div>`;
const chipCls = l => l === "AI voice" ? " ai" : (l === "ours" ? " ours" : "");
const chips = it => it.who.map(w => `<span class="chip${chipCls(w.l)}">${esc(w.l)} · ${esc(w.a)}</span>`).join("");
function row(it){
  const loop = it.single ? `<a href="${esc(it.single)}">the loop on its own (${fmt(it.dur)})</a>` : "";
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><div class="name"><code>${esc(it.id)}</code><span class="ev">${esc(it.kind)}</span>${it.rec ? '<span class="rec">recommended</span>' : ""}</div>
      <div class="what"><b>${esc(it.label)}.</b> ${esc(it.what)}</div>
      <div class="meta">${chips(it)}</div>
      <div class="meta"><b>Level:</b> ${it.lvl}</div></div>
    <div class="players"><div class="pl main"><span>Candidate ${it.n}${it.single ? " · played 6 times in a row" : " · " + fmt(it.dur)}</span>${audio(it.src)}${loop}</div></div>${vote(it)}</div>`;
}
function build(){
  let h = "", grp = "";
  for (const e of EVENTS) {
    if (e.group !== grp) { grp = e.group; h += `<h2 class="sec">${esc(grp)}</h2>`; }
    const its = ITEMS.filter(i => i.lump === e.lump);
    h += `<details class="grp" open><summary><code>${esc(e.lump)}</code> ${esc(e.ev)} <span class="eng">${esc(e.engine)}</span><span class="rejnote">${esc(e.note)}</span><span class="gcount" data-l="${esc(e.lump)}"></span></summary>
      <div class="refs"><div class="pl"><span>In the game today: Freedoom ${esc(e.ref)} (${fmt(e.fdlen)})</span>${audio(e.fd)}</div></div>`;
    for (const it of its) h += row(it);
    h += `<div class="why"><b>Why the recommended one:</b> ${esc(e.why)}</div></details>`;
  }
  document.getElementById("groups").innerHTML = h;
  document.getElementById("pAll").textContent = ITEMS.length;
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
  for (const e of EVENTS) {
    const g = ITEMS.filter(i => i.lump === e.lump), el = document.querySelector(`.gcount[data-l="${e.lump}"]`);
    if (el) el.textContent = `${g.filter(i => st(i.id).v).length} / ${g.length}`;
  }
  const notes = ITEMS.filter(i => (st(i.id).n || "").trim()).map(i => `${i.id}: «${st(i.id).n.trim().replace(/\s+/g, " ")}»`);
  const open = ITEMS.filter(i => !st(i.id).v).map(i => i.id);
  const L = [`World sounds (__STAMP__): ${done}/${ITEMS.length} judged`,
    `OK (${by("ok").length}): ${by("ok").join(", ") || "—"}`,
    `NO (${by("no").length}): ${by("no").join(", ") || "—"}`,
    `? (${by("q").length}): ${by("q").join(", ") || "—"}`,
    `notes: ${notes.join(" / ") || "—"}`];
  if (open.length) L.push(`unjudged (${open.length}): ${open.join(", ")}`);
  document.getElementById("result").value = L.join("\n");
}
function copy(){
  const t = document.getElementById("result"), msg = document.getElementById("copied");
  summary();
  const done = () => { msg.textContent = "copied"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? done() : (msg.textContent = "select and Ctrl+C below"); } catch (e) { msg.textContent = "select and Ctrl+C below"; } t.scrollIntoView({block:"center"}); };
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
document.getElementById("reset").addEventListener("click", () => { if (confirm("Clear all the answers and notes on this sheet?")) { S = {}; save(); build(); summary(); } });
build(); summary();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
