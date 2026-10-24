#!/usr/bin/env python3
"""Alternatives for the eight enemy sounds the CEO marked NO (D83), the
trimmed MAP01 music draft, and the listening page that carries both.

On the M3 listening sheet (`docs/art/previews/2026-10-14_2355_M3_listening-sheet.html`)
the CEO marked NO five enemy lumps (`SDRRIATK`, `SDLTRATK`, `SDSTOPAI`,
`SDSTODTH`, `SDPZRPAI`) and three beds, the non-vocal layers that will go
under the voice takes (`SDRRIPAI`, `SDLTRPAI`, `SDLTRDTH`). This file makes
THREE clearly different takes on each: another gesture or another material,
never a retouch of the rejected recipe (`gen_sfx.py`, which is not touched;
its DSP primitives and its `Ctx` are imported, so its source handling and
provenance are the same).

Rules kept (docs/sound/ENEMY-SOUNDS.md §2, §5.9):

- Sources: our synthesis plus files of the CC0 packs already on disk under
  D36 (`OGA-CRE1`, `OGA-CRE2`, `OGA-100`, `KEN-IMP`). No download, no
  `shot_*` file. Every alternative that reads a pack also carries a layer of
  our own synthesis, so no CC0 clip ships alone. Every source file's SHA-256
  is pinned below and checked by the tests.
- Loudness (D83, the weapon ruler of `gen_weapon_alts.py`): peak at -1 dBFS
  and the loudest 50 ms (A-weighted mean square) at the Freedoom sound the
  lump replaces, minus a fixed allowance per kind (0 dB for shots and
  voices; a bed sits `ALLOWANCE_DB["bed"]` under, since a voice goes on top).
  Shots reach it by a searched soft saturation (denser, not only louder),
  the rest by a look-ahead limiter, the same `to_target` the weapons use.
- Laptop speakers: at least `MIN_SHARE_ABOVE_300HZ` of every sound's energy
  sits above 300 Hz (the sheet flagged `SDPZRPAI` at 96 % below).

The music (D83, "intro demasiado larga, la parte melódica mucho mejor",
"intro too long, the melodic part much better"):
`D_SDM01E.mid` is cut so it starts where the horns take the melody, and is
written as `work/audio/D_SDM01T.mid`. Editing our own sequence, not
composing (D59): every note of the cut exists, at the same pitch, velocity
and length, in `D_SDM01E` (the tests check it). Both are rendered with
GZDoom's own `zmusic.dll` and `gzdoom.sf2`, loaded as a library: the engine
is never started (D26).

Outputs (gitignored `work/`):

    work/audio/enemy_alt/<LUMP>_alt<N>.ogg      the 24 alternatives
    work/audio/enemy_alt/wav/<LUMP>_alt<N>.wav  16-bit masters
    work/audio/enemy_alt/MANIFEST.txt           levels against the Freedoom sound
    work/audio/enemy_alt/PROVENANCE.tsv         one row per source file per alternative
    work/audio/D_SDM01T.mid (and D_SDM01U.mid)  the trimmed music drafts
    work/audio/music_trim/<LUMP>.ogg            renders: one loop plus the seam

Run:

    .venv/Scripts/python.exe tools/audio/gen_enemy_alts.py --list
    .venv/Scripts/python.exe tools/audio/gen_enemy_alts.py \\
        --page docs/art/previews/<YYYY-MM-DD_HHMM>_M3_listening-enemy-alts-music.html
    .venv/Scripts/python.exe -m unittest tests.test_gen_enemy_alts -v

GPL-3.0 (the script); its output is CC BY-NC-SA 4.0 (D15).
"""

from __future__ import annotations

import argparse
import ctypes
import html
import json
import os
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_sfx as gs  # noqa: E402
import gen_weapon_alts as wa  # noqa: E402
import gen_weapon_sfx as gws  # noqa: E402
import midi_edit as me  # noqa: E402
from gen_sfx import (  # noqa: E402
    am, bandpass, bitcrush, click, comb, crackle, db, env_exp, env_points, fade,
    from_onset, glide, highpass, lowpass, mix, n_of, peak_eq, peak_normal,
    pitch_glide, reverb, ring, saturate, saw, stutter, sweep_band, thump, time_axis,
    tone, tv_filter)

PROJECT_ROOT = gs.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "audio" / "enemy_alt"
REJECTED_DIR = gs.OUT_DIR                                     # work/audio/sfx/enemies
FREEDOOM_PREVIEW_DIR = wa.FREEDOOM_PREVIEW_DIR
SR = gs.SAMPLE_RATE
assert SR == gws.SR                                          # one ruler for both files

ALT_COUNT = 3
PEAK_DBFS = wa.PEAK_DBFS
PEAK_TOLERANCE_DB = wa.PEAK_TOLERANCE_DB
LOUDNESS_TOLERANCE_DB = wa.LOUDNESS_TOLERANCE_DB
MIN_SHARE_ABOVE_300HZ = wa.MIN_SHARE_ABOVE_300HZ
FINAL_FADE_S = 0.02              # after levelling: the limiter lifted the quiet end
LOW_CUT_HZ = 90.0                # every alternative: what a laptop cannot play, out

# How far under the Freedoom lump's loudest 50 ms (A-weighted) each kind sits.
# Shots and voices match it. A bed is a layer under the CEO's voice take
# (ENEMY-SOUNDS §5.10): at the voice's own level it would bury the voice.
ALLOWANCE_DB = {"fire": 0.0, "voice": 0.0, "bed": 3.0}
LEVEL_ROUTE = {"fire": "fire", "voice": "handling", "bed": "handling"}   # wa.to_target kinds

# The Freedoom lumps these stand beside on the M3 sheet (its "rep" column),
# measured from iwads/freedoom2.wad 0.13.0 with gen_weapon_alts' rulers; a test
# re-measures them. name -> (peak dBFS, A-weighted loudest 50 ms dB, plain RMS dBFS)
FREEDOOM_LEVELS: dict[str, tuple[float, float, float]] = {
    "DSPISTOL": (0.0, -10.39, -9.23),
    "DSDSHTGN": (0.0, -7.94, -4.49),
    "DSDMPAIN": (-2.41, -11.72, -12.85),
    "DSBGDTH1": (0.0, -7.38, -12.06),
    "DSPOPAIN": (-2.14, -11.37, -14.1),
    "DSPODTH2": (0.0, -8.28, -9.71),
}
LEVEL_TOLERANCE_DB = 0.2

# --- Sources ---------------------------------------------------------------------
# (pack, file name) -> SHA-256 of the file as on disk under work/audio/sfx_sources/.
CC0_PACKS = ("OGA-CRE1", "OGA-CRE2", "OGA-100", "KEN-IMP")
SOURCES: dict[tuple[str, str], str] = {
    ("OGA-CRE1", "hurt_04.ogg"):
        "65a6524d46bbf2acccb09b551fe7e3616dbd19f62266b5ea7e6313df29031df1",
    ("OGA-CRE1", "monster_02.ogg"):
        "2f590aec7086b2327a141ec71d5e8b8e83524a30e6b9baf3be2784f4adb153b3",
    ("OGA-CRE1", "roar_03.ogg"):
        "983396c808eb658ed3bd223ffaf9ea7f756dba7bc45ecc3fde117083026a4556",
    ("OGA-CRE1", "troll_02.ogg"):
        "d63ae3a57294b8370eb6370cc4c75f544f4a8571d893ea3a48a4564d82e078cb",
    ("OGA-CRE2", "grunt_06.ogg"):
        "406b88a519f2b067f99dedbce1b3dc2f472c7f5a50f8443e8dddbcf5e0edaf53",
    ("OGA-CRE2", "grunt_07.ogg"):
        "3cfc82e16c9a40d8a82505877746836110735cae60f6abe98c77e325764e92af",
    ("OGA-CRE2", "die_01.ogg"):
        "d592dfbbe36a5e3e4b7dcaaa13498e50c59319d6df443c309858affb69336523",
    ("OGA-CRE2", "monster_12.ogg"):
        "ed46c28e65ae5022b47c3b50e60bfaf2d448efce3e54bfa705e723dc247b3f86",
    ("OGA-CRE2", "roar_06.ogg"):
        "87c2c2658788e287c3f05f81605c7f343b56fc8197fe251bca0811c7520eeb7c",
    ("OGA-100", "metal_02.ogg"):
        "545c2d698e72e1a3f0f22407fc0567a1f1041d9dbeff528bef0947284b45fdf2",
    ("OGA-100", "spring_03.ogg"):
        "f05277b7af3301cc9eb4d76ab3751235cd60b42205f0763f06036cd90bdbaadf",
    ("OGA-100", "switch_02.ogg"):
        "769dca6ccbea5c33cef602cdaa6ab0350b0dc2b093f02eae36f33e2552036f67",
    ("KEN-IMP", "impactMetal_light_001.ogg"):
        "fba69c467ddd85da7b1d82e259f936b876d9ba6a3d6f1b24bdd10468e46bfe08",
    ("KEN-IMP", "impactMetal_light_003.ogg"):
        "92d5db6bfc672d9dc1b4f390b2900504f013187fa36335472554fafefa9050b1",
    ("KEN-IMP", "impactMetal_light_004.ogg"):
        "9b1c35820fba507081261f19ab5f461f69a5e2627a7d91acdb73ca3cfc997979",
    ("KEN-IMP", "impactMetal_heavy_000.ogg"):
        "e07045693e4a2b3d165c424e3dab4c781d9ff8880a386880ac89a51315d7f831",
    ("KEN-IMP", "impactMetal_heavy_002.ogg"):
        "b914c8f1eb7c0f34bb165d7c77f4be0351f6be0660c13c53e65424e262e2c093",
    ("KEN-IMP", "impactPunch_medium_000.ogg"):
        "486988aa2d6440ffc4c62a0e8ccf3c23673ba84424bd4723378d451b7255eb5c",
    ("KEN-IMP", "impactPunch_medium_003.ogg"):
        "2d7c719c05999e0532f4384e1018e04cd916db715140bf16dee2dff3f820e908",
    ("KEN-IMP", "impactPlate_heavy_003.ogg"):
        "59775f8979a396c8a793b0a1db206d5bdc651eae808d858e9acaee8ebda5bc6d",
    ("KEN-IMP", "impactPlate_medium_001.ogg"):
        "68ba7701b71ef620f498f3038e832157d71ac8db7ad59424545890b250ceb24e",
    ("KEN-IMP", "impactPlate_medium_003.ogg"):
        "964c5fcfb91e7710e2af25c2243c8b7160756b223b0984bacc9eb25bfeea057b",
    ("KEN-IMP", "impactPlate_light_000.ogg"):
        "6e797cf8a5bfc52d7ed5eb47c227974c1cf2a674954fec5b539cea7d62c7282c",
    ("KEN-IMP", "impactPlate_light_004.ogg"):
        "9cb33b0c0cce948313f078b60769d2f8e4075472494fc8f8129aa4a23c951897",
    ("KEN-IMP", "impactBell_heavy_001.ogg"):
        "9df61e3ae9a83dc65e5a1fd3ed19d480876f3b22b963a1b9ef6fa293592dcec4",
    ("KEN-IMP", "impactWood_light_001.ogg"):
        "4b76bf3ccc8e60d19188f3165b778a7817786faa6887c55d9049bcbeef3b425f",
    ("KEN-IMP", "impactTin_medium_003.ogg"):
        "0d18737d93ba7aa0669f751094cbc1671bbebac4fe207783922938ce75e24334",
    ("KEN-IMP", "impactGeneric_light_003.ogg"):
        "0e8896706130f6bc88cdf1f0157aaacdbe88dce86cf0330f9136e44eb1209e81",
    ("KEN-IMP", "impactGeneric_light_004.ogg"):
        "f906fa3a37acc4372787b496efcedefa2856045d5ec9456a3bd6c303c0eabb41",
    ("KEN-IMP", "impactSoft_heavy_002.ogg"):
        "d130ae541951243d3f6ed963d0057450a445ffe117fbf9a084d34eb1635cb563",
    ("KEN-IMP", "footstep_concrete_001.ogg"):
        "507a75eb19b897087855a3be3cf11a12d7fa37d143ad535eeebe0b8031c7325d",
    ("KEN-IMP", "footstep_carpet_002.ogg"):
        "9af3c3f76705107339e72036e4053bdca3eaa50ad31c8c929f42ce8d40e5d781",
}


def source_path(pack: str, name: str, sources_dir: Path = gs.SOURCES_DIR) -> Path:
    return sources_dir / gs.PACK_DIRS[pack] / name


class C(gs.Ctx):
    """gen_sfx's recipe context, refusing any file not pinned in SOURCES."""

    def src(self, pack, name, start=None, end=None, st=0.0, trim=True):
        if (pack, name) not in SOURCES:
            raise KeyError(f"{pack} {name} is not in SOURCES")
        return super().src(pack, name, start, end, st, trim)


def hp(x, f=LOW_CUT_HZ):
    return highpass(x, f, 2)


# --- Shared atoms (new here) -------------------------------------------------------

def report(c, length, attack, tau, lo, hi):
    """A muzzle report: band noise, near-instant attack, exponential decay."""
    n = n_of(length)
    return bandpass(c.noise(length) * env_exp(n, tau, attack_s=attack), lo, hi, 2)


def echo_taps(x, taps):
    """Discrete reflections (delay s, gain dB), each one darker than the last."""
    out = mix((0, x, 0), *[(d, lowpass(x, 5000 / (1 + i), 1), g) for i, (d, g) in enumerate(taps)])
    return out


def ring_mod(x, f):
    """A voice multiplied by a sine: the robotic metallic double of it."""
    return x * tone(f, x.size)


def chop(x, rate_hz, duty=0.55, start_s=0.0):
    """Gate the signal on and off rate_hz times a second after start_s (a broken link)."""
    t = time_axis(x.size)
    gate = ((t * rate_hz) % 1.0 < duty) | (t < start_s)
    g = np.convolve(gate.astype(float), np.ones(n_of(0.0015)) / n_of(0.0015), "same")
    return x * g


def radio(x, crush=True):
    """LEGION-RADIO's band (ENEMY-SOUNDS §4): 300-3000 Hz, overdriven, 8-bit-ish."""
    y = saturate(peak_normal(bandpass(x, 300, 3000, 3)), 2.5)
    return bitcrush(y, 8, 4) if crush else y


def spark(c, length, rate0, rate1):
    """Electric arcing: a dense crackle, brighter than debris."""
    c.syn()
    return crackle(c.rng, length, rate0, rate1, 0.0015, 2500, 11000)


def hiss(c, length, lo, hi, tau, attack=0.005):
    """A hydraulic / steam release."""
    n = n_of(length)
    return bandpass(c.noise(length) * env_exp(n, tau, attack_s=attack), lo, hi, 2)


def roger_beep(c, tones=((1200.0, 0.06), (900.0, 0.08))):
    """The two-tone end-of-transmission beep of a field radio."""
    c.syn()
    parts = []
    for f, d in tones:
        n = n_of(d)
        parts.append(np.sin(2 * np.pi * f * time_axis(n)) * env_points(n, [(0, 0), (0.004, 1), (d - 0.006, 1), (d, 0)]))
    return np.concatenate(parts)


def landing(c, keys, start, gap, gain_db=0.0, decay=0.62):
    """Gear landing on concrete: hits closing up and fading (a bouncing object)."""
    layers, t, g, dt = [], start, gain_db, gap
    for pack, name, st in keys:
        layers.append((t, c.src(pack, name, st=st), g))
        t += dt
        dt *= decay
        g -= 5.0
    return layers


# --- Recipes: SDRRIATK, the Reich rifle shot (rejected: band-passed crack + bolt at 0.3 s) ----

def r_rri_hangar(c):
    """SDRRIATK alt1: one crack, then the hangar answers: two slapback echoes, no bolt."""
    crack = report(c, 0.12, 0.0005, 0.018, 900, 9000)
    body = report(c, 0.2, 0.002, 0.05, 250, 2500)
    shot = mix((0, peak_normal(crack), 0), (0, peak_normal(body), -6),
               (0, click(c.rng, 0.0012, 3000, 12000), -3))
    return echo_taps(shot, ((0.085, -9), (0.19, -14), (0.31, -20)))


# D86: alt2 is approved "once its final click is quieter than the first". As
# rendered for the page, the bolt's closing ping (impactMetal_light_004 at
# +0.09 s) measured -27.0 dB A over its loudest 50 ms against -27.2 for the
# opening click (switch_02): it rings longer, so it read as the louder. It
# now sits FINAL_CLICK_DB under the bolt's own level, which puts it at least
# FINAL_UNDER_FIRST_DB under the first click (and ~20 dB under the crack);
# tests/test_gen_enemy_alts.py measures both. Before D86 the gain was -4.
FINAL_CLICK_DB = -11.0
FINAL_UNDER_FIRST_DB = 6.0
RRI_BOLT_AT_S = 0.24             # the bolt worked after the crack
RRI_FINAL_CLICK_AT_S = 0.09      # the closing ping, after the opening click


def r_rri_receiver(c):
    """SDRRIATK alt2: a dry crack with the steel of the receiver ringing, then the bolt worked."""
    crack = report(c, 0.09, 0.0008, 0.022, 1200, 7000)
    steel = c.src("KEN-IMP", "impactMetal_light_001.ogg", st=7)
    punch = hp(c.src("KEN-IMP", "impactPunch_medium_000.ogg", st=3), 400)
    bolt = mix((0, c.src("OGA-100", "switch_02.ogg", st=2), 0),
               (RRI_FINAL_CLICK_AT_S, c.src("KEN-IMP", "impactMetal_light_004.ogg", st=5), FINAL_CLICK_DB))
    return mix((0, peak_normal(crack), 0), (0, steel, -9), (0, punch, -8), (RRI_BOLT_AT_S, hp(bolt, 600), -14))


def r_rri_whip(c):
    """SDRRIATK alt3: the round arrives before the report: a supersonic whip-crack, then a distant thump."""
    c.syn()
    n = n_of(0.004)
    nwave = np.concatenate([np.linspace(0, 1, n // 2), np.linspace(1, -1, n), np.linspace(-1, 0, n // 2)])
    snap = mix((0, highpass(nwave, 1500, 2), 0), (0, click(c.rng, 0.002, 4000, 14000), -4))
    zip_ = sweep_band(c.noise(0.05) * env_points(n_of(0.05), [(0, 0), (0.04, 1), (0.05, 0)]), 6000, 2500, 0.5)
    muzzle = report(c, 0.35, 0.004, 0.08, 300, 1800)
    return mix((0, peak_normal(zip_), -10), (0.05, peak_normal(snap), 0), (0.11, reverb(peak_normal(muzzle), c.rng, 0.5, -12, 3000), -7))


# --- Recipes: SDLTRATK, the Legion shotgun (rejected: noise blast + 70 Hz thump + comb ring) ----

def r_ltr_pump(c):
    """SDLTRATK alt1: an American pump gun: the blast, then the slide racked, chk-chak."""
    blast = saturate(report(c, 0.45, 0.002, 0.07, 200, 5000), 2.2)
    chrome = hp(c.src("OGA-100", "metal_02.ogg", st=-2), 800)
    rack = mix((0, c.src("OGA-100", "switch_02.ogg", st=-3), 0),
               (0.012, c.src("KEN-IMP", "impactMetal_light_003.ogg", st=-2), -3),
               (0.13, c.src("OGA-100", "spring_03.ogg", st=0), -10),
               (0.16, c.src("KEN-IMP", "impactMetal_heavy_000.ogg", st=4), -2))
    return mix((0, peak_normal(blast), 0), (0.004, chrome, -12), (0.38, hp(rack, 400), -9))


def r_ltr_volley(c):
    """SDLTRATK alt2: a short thunderclap: three loads fired as one, a stagger of cracks over a plated body."""
    cracks = mix(*[(0.006 * i, peak_normal(report(c, 0.06, 0.0005, 0.012, 1500, 9000)), -2 * i) for i in range(3)])
    boom = saturate(report(c, 0.5, 0.003, 0.11, 150, 2200), 1.8)
    plate = hp(c.src("KEN-IMP", "impactPlate_heavy_003.ogg", st=5), 300)
    return mix((0, cracks, -3), (0, peak_normal(boom), 0), (0.002, plate, -8))


def r_ltr_barrel(c):
    """SDLTRATK alt3: a chromed barrel that rings like a bell: blast, then a metallic boing."""
    blast = report(c, 0.3, 0.002, 0.05, 300, 6000)
    bell = c.src("KEN-IMP", "impactBell_heavy_001.ogg", st=3)
    tube = comb(c.noise(0.02) * np.hanning(n_of(0.02)), 1 / 640.0, 0.95, 0.5)
    return mix((0, saturate(peak_normal(blast), 1.6), 0), (0.003, hp(bell, 400), -8),
               (0.003, peak_normal(bandpass(tube, 500, 5000, 2)), -11))


# --- Recipes: SDSTOPAI, the Stormtrooper's pain (rejected: hurt_02 yelp + servo + stutter) ----

def r_sto_ringmod(c):
    """SDSTOPAI alt1: a shout turned metallic: the voice ring-modulated, the tail crushed to 6 bits."""
    yell = highpass(from_onset(c.src("OGA-CRE1", "hurt_04.ogg", st=-3), -10)[:n_of(0.42)], 350, 4)
    metal = ring_mod(yell, 170.0)
    y = mix((0, yell, -4), (0, metal, 0))
    y = np.concatenate([y[:n_of(0.2)], bitcrush(y[n_of(0.2):], 6, 6)])
    c.syn()
    return mix((0, hp(peak_eq(y, 1800, 4, 0.8), 300), 0), (0.0, tone(glide(2400, 900, n_of(0.12)), n_of(0.12)) * env_exp(n_of(0.12), 0.04), -20))


def r_sto_spark(c):
    """SDSTOPAI alt2: a grunt and the machine half shorting out: a burst of sparks and a relay snap."""
    grunt = saturate(from_onset(c.src("OGA-CRE2", "grunt_07.ogg", st=-1), -10)[:n_of(0.35)], 2.0)
    return mix((0, peak_eq(highpass(grunt, 400, 4), 1500, 6, 0.8), 0), (0.03, spark(c, 0.3, 900, 60), -6),
               (0.03, click(c.rng, 0.003, 2000, 9000), -4), (0.16, click(c.rng, 0.003, 1500, 6000), -9))


def r_sto_chopped(c):
    """SDSTOPAI alt3: a shriek cut to pieces: the signal breaks up 28 times a second."""
    shriek = from_onset(c.src("OGA-CRE1", "monster_02.ogg", st=2), -10)[:n_of(0.45)]
    shriek = bandpass(shriek, 400, 6000, 2)
    c.syn()
    hum = saw(glide(120, 80, shriek.size), shriek.size) * env_exp(shriek.size, 0.2)
    return chop(mix((0, peak_normal(shriek), 0), (0, bandpass(hum, 300, 3000, 1), -18)), 28, 0.55, 0.08)


# --- Recipes: SDSTODTH, the Stormtrooper's death (rejected: monster_07 + servo whine) ----

def r_sto_short(c):
    """SDSTODTH alt1: a death cry, a short circuit that dies down, and the body's steel on the floor."""
    cry = hp(c.src("OGA-CRE2", "die_01.ogg", st=-3), 200)[:n_of(0.75)]
    fall = c.src("KEN-IMP", "impactMetal_heavy_002.ogg", st=2)
    return mix((0, fade(cry, 0.002, 0.15), 0), (0.05, spark(c, 0.9, 1200, 15), -7),
               (0.72, hp(fall, 250), -4), (0.72, thump(n_of(0.2), 160, 90, 0.05), -14))


def r_sto_tape(c):
    """SDSTODTH alt2: the voice slows like a tape when the power fails, crushing as it sinks, then a dropout."""
    roar = from_onset(c.src("OGA-CRE1", "roar_03.ogg", st=0), -10)[:n_of(0.7)]
    sunk = pitch_glide(roar, 0, -14)
    k = np.linspace(0, 1, sunk.size)
    crushed = np.where(k > 0.5, bitcrush(sunk, 6, 5), sunk)
    c.syn()
    return mix((0, hp(peak_eq(peak_normal(crushed), 2000, 5, 0.8), 200), 0),
               (sunk.size / SR - 0.04, click(c.rng, 0.004, 800, 6000), -2))


def r_sto_hydraulic(c):
    """SDSTODTH alt3: a death rattle, the hydraulics let go with a hiss, the armour plates clatter down."""
    rattle = hp(c.src("OGA-CRE2", "monster_12.ogg", st=-2), 250)[:n_of(0.6)]
    layers = [(0, fade(saturate(rattle, 2.0), 0.002, 0.12), 0), (0.25, hiss(c, 0.6, 2000, 7000, 0.18, 0.01), -6)]
    layers += landing(c, (("KEN-IMP", "impactPlate_medium_001.ogg", 0),
                          ("KEN-IMP", "impactPlate_light_004.ogg", 2),
                          ("KEN-IMP", "impactPlate_medium_001.ogg", 3)), 0.62, 0.14, -9)
    return mix(*layers)


# --- Recipes: SDPZRPAI, the Panzermensch's pain (rejected: grunt_09 -5 st, 96 % under 300 Hz) ----

def r_pzr_plates(c):
    """SDPZRPAI alt1: a heavy grunt, the plates jolting with a clank you hear on a laptop."""
    grunt = hp(from_onset(c.src("OGA-CRE2", "grunt_06.ogg", st=-3), -10)[:n_of(0.45)], 220)
    grunt = peak_eq(grunt, 1200, 6, 0.8)
    clank = c.src("KEN-IMP", "impactPlate_heavy_003.ogg", st=4)
    c.syn()
    return mix((0, fade(grunt, 0.002, 0.08), 0), (0.01, hp(clank, 400), -6),
               (0.01, ring(n_of(0.25), 820.0, (1.0, 2.13, 3.4), (0.08, 0.05, 0.03), (0, -4, -8)), -14))


def r_pzr_helmet(c):
    """SDPZRPAI alt2: a snort inside the steel helmet: the voice resonates in the bowl, steam escapes."""
    snort = from_onset(c.src("OGA-CRE1", "troll_02.ogg", st=-4), -10)[:n_of(0.45)]
    bowl = gs.helmet(hp(snort, 200))
    return mix((0, peak_eq(peak_normal(bowl), 900, 5, 0.7), 0), (0.08, hiss(c, 0.35, 1500, 6000, 0.1, 0.02), -12))


def r_pzr_roar(c):
    """SDPZRPAI alt3: a short bark of a roar with a bright edge and the clang of the chest plate."""
    roar = from_onset(c.src("OGA-CRE2", "roar_06.ogg", st=-2), -10)[:n_of(0.42)]
    roar = peak_eq(hp(roar, 250), 1600, 7, 0.9)
    plate = c.src("KEN-IMP", "impactMetal_heavy_000.ogg", st=3)
    c.syn()
    return mix((0, fade(saturate(roar, 1.8), 0.002, 0.1), 0), (0.0, hp(plate, 500), -10),
               (0, thump(n_of(0.15), 220, 140, 0.04), -16))


# --- Recipes: beds (no voice: what goes UNDER the CEO's take) ------------------------------

def r_rripai_helmet(c):
    """SDRRIPAI bed alt1: the stock knocks the helmet: wood and a tin ring, once."""
    stock = c.src("KEN-IMP", "impactWood_light_001.ogg", st=2)
    tin = c.src("KEN-IMP", "impactTin_medium_003.ogg", st=1)
    c.syn()
    return mix((0, hp(stock, 300), 0), (0.012, tin, -4), (0.012, ring(n_of(0.15), 1450.0, (1.0, 2.7), (0.05, 0.03), (0, -6)), -18))


def r_rripai_buckles(c):
    """SDRRIPAI bed alt2: real buckles this time: small steel pings and the coat's cloth."""
    layers = [(0.0, c.src("KEN-IMP", "footstep_carpet_002.ogg", st=4), -6)]
    for i, (at, st) in enumerate(((0.0, 9), (0.035, 11), (0.07, 8), (0.11, 12))):
        layers.append((at, c.src("KEN-IMP", "impactMetal_light_003.ogg", st=st), -3 - 3 * i))
    c.syn()
    layers.append((0.0, bandpass(c.noise(0.15) * env_exp(n_of(0.15), 0.05, 0.01), 1500, 6000, 1), -16))
    return mix(*layers)


def r_rripai_stagger(c):
    """SDRRIPAI bed alt3: the hit knocks him back a step: boot on concrete, the rifle rattles."""
    step = c.src("KEN-IMP", "footstep_concrete_001.ogg", st=0)
    rifle = c.src("KEN-IMP", "impactGeneric_light_003.ogg", st=2)
    sling = c.src("KEN-IMP", "impactMetal_light_004.ogg", st=6)
    c.syn()
    return mix((0, highpass(step, 350, 4), 0), (0.03, rifle, -5), (0.05, sling, -9),
               (0.0, thump(n_of(0.1), 180, 110, 0.03), -14))


def r_ltrpai_mic(c):
    """SDLTRPAI bed alt1: the hit knocks the microphone: a thump through the radio and a stab of feedback."""
    knock = highpass(radio(c.src("KEN-IMP", "impactPunch_medium_003.ogg", st=-2), crush=False), 500, 4)
    c.syn()
    n = n_of(0.16)
    howl = np.sin(2 * np.pi * np.cumsum(glide(2300, 2150, n)) / SR) * env_points(n, [(0, 0), (0.03, 1), (0.13, 0.7), (0.16, 0)])
    return mix((0, knock, 0), (0.02, howl, -14), (0.0, radio(c.noise(0.2) * env_exp(n_of(0.2), 0.06)), -16))


def r_ltrpai_dropout(c):
    """SDLTRPAI bed alt2: the link breaks up: static chopped 22 times a second, two relay clicks."""
    static = radio(c.noise(0.26) * env_points(n_of(0.26), [(0, 0.4), (0.02, 1), (0.22, 0.8), (0.26, 0)]))
    return mix((0, chop(static, 22, 0.5), 0), (0.0, click(c.rng, 0.003, 1200, 5000), -2),
               (0.24, click(c.rng, 0.003, 1200, 5000), -4))


def r_ltrpai_jam(c):
    """SDLTRPAI bed alt3: a heterodyne whistle sweeping down through the band, and his kit jolting."""
    n = n_of(0.28)
    c.syn()
    whine = np.sin(2 * np.pi * np.cumsum(glide(3200, 900, n)) / SR) * env_points(n, [(0, 0), (0.02, 1), (0.28, 0)])
    plate = c.src("KEN-IMP", "impactPlate_light_000.ogg", st=3)
    return mix((0, radio(mix((0, whine, 0), (0, c.noise(0.28) * 0.3, 0))), 0), (0.01, hp(plate, 400), -8))


def r_ltrdth_dropped(c):
    """SDLTRDTH bed alt1: the radio hits the floor before he does: static runs on, then cuts with a click."""
    static = radio(c.noise(0.55))
    layers = [(0, static * env_points(static.size, [(0, 0.5), (0.01, 1), (0.55, 0.9)]), -12),
              (0.0, c.src("KEN-IMP", "impactPlate_medium_003.ogg", st=2), -2),
              (0.05, c.src("KEN-IMP", "impactGeneric_light_004.ogg", st=1), -8),
              (0.55, click(c.rng, 0.003, 800, 4000), -2),
              (0.6, c.src("KEN-IMP", "impactSoft_heavy_002.ogg", st=2), -4)]
    return mix(*layers)


def r_ltrdth_roger(c):
    """SDLTRDTH bed alt2: the end-of-transmission beep, slurring as the set dies, then the body lands."""
    beep = roger_beep(c)
    slur = pitch_glide(beep, 0, -5)
    tail = radio(c.noise(0.25) * env_exp(n_of(0.25), 0.08))
    return mix((0, radio(slur, crush=True), -4), (0.16, tail, -10),
               (0.5, c.src("KEN-IMP", "impactSoft_heavy_002.ogg", st=0), -3),
               (0.52, c.src("KEN-IMP", "footstep_concrete_001.ogg", st=-1), -8))


def r_ltrdth_drown(c):
    """SDLTRDTH bed alt3: the carrier drowns: the static closes down to a rumble, crackling, as the gear lands."""
    static = radio(c.noise(0.8), crush=False)

    def closing(f, t):
        hi = 3500 * np.exp(-max(t, 0.0) / 0.25) + 250
        return 1 / np.sqrt(1 + (f / hi) ** 4)
    drown = bitcrush(peak_normal(tv_filter(static, closing)), 6, 8)
    layers = [(0, drown * env_points(drown.size, [(0, 0), (0.02, 1), (0.7, 0.5), (0.8, 0)]), -4),
              (0.05, spark(c, 0.6, 300, 30), -12)]
    layers += landing(c, (("KEN-IMP", "impactMetal_light_004.ogg", 0),
                          ("KEN-IMP", "impactMetal_light_001.ogg", 2),
                          ("KEN-IMP", "impactMetal_light_004.ogg", 3)), 0.55, 0.12, -5)
    return mix(*layers)


# --- The table -------------------------------------------------------------------------

@dataclass(frozen=True)
class Alt:
    lump: str
    index: int
    recipe: Callable
    sources: tuple[str, ...]          # file names, all in SOURCES
    length_s: tuple[float, float]
    label: str                        # for the page
    what: str                         # for the page

    @property
    def name(self) -> str:
        return f"{self.lump}_alt{self.index}"

    @property
    def kind(self) -> str:
        return TARGETS[self.lump][0]


# lump -> (kind, Freedoom lump beside it on the sheet, rejected file, group, event, what was rejected)
TARGETS: dict[str, tuple[str, str, str, str, str, str]] = {
    "SDRRIATK": ("fire", "DSPISTOL", "SDRRIATK.ogg", "Reich Rifleman", "attack (shot)",
                 "filtered crack and bolt at 0.3 s"),
    "SDLTRATK": ("fire", "DSDSHTGN", "SDLTRATK.ogg", "Legion Soldier", "attack (shotgun)",
                 "noise blast, 70 Hz low thump and comb ring"),
    "SDSTOPAI": ("voice", "DSDMPAIN", "SDSTOPAI.ogg", "Hybrid Stormtrooper", "pain",
                 "raspy yelp (hurt_02), servo and digital stutter"),
    "SDSTODTH": ("voice", "DSBGDTH1", "SDSTODTH.ogg", "Hybrid Stormtrooper", "death",
                 "collapsing rasp and a servo winding down"),
    "SDPZRPAI": ("voice", "DSDMPAIN", "SDPZRPAI.ogg", "Panzermensch", "pain",
                 "low grunt: 96 % below 300 Hz, inaudible on a laptop"),
    "SDRRIPAI": ("bed", "DSPOPAIN", "beds/SDRRIPAI-bed.ogg", "Reich Rifleman", "layer under the pain",
                 "synthetic webbing being shaken"),
    "SDLTRPAI": ("bed", "DSPOPAIN", "beds/SDLTRPAI-bed.ogg", "Legion Soldier", "layer under the pain",
                 "burst of static and the kit jolting"),
    "SDLTRDTH": ("bed", "DSPODTH2", "beds/SDLTRDTH-bed.ogg", "Legion Soldier", "layer under the death",
                 "falling carrier, squelch and the body on the floor"),
}

ALTS: tuple[Alt, ...] = (
    Alt("SDRRIATK", 1, r_rri_hangar, (), (0.35, 0.75), "Hangar echo",
        "A dry crack and the hangar answers with two or three short echoes. No bolt."),
    Alt("SDRRIATK", 2, r_rri_receiver, ("impactMetal_light_001.ogg", "impactPunch_medium_000.ogg",
                                        "switch_02.ogg", "impactMetal_light_004.ogg"),
        (0.3, 0.7), "Bolt and steel",
        "A dry shot with the steel of the receiver ringing; then the bolt is worked, click-clack."),
    Alt("SDRRIATK", 3, r_rri_whip, (), (0.4, 0.9), "Bullet whip",
        "The bullet arrives before the shot: a supersonic whip-crack and, behind it, the distant report."),
    Alt("SDLTRATK", 1, r_ltr_pump, ("metal_02.ogg", "switch_02.ogg", "impactMetal_light_003.ogg",
                                    "spring_03.ogg", "impactMetal_heavy_000.ogg"),
        (0.6, 1.1), "Pump shotgun",
        "An American shotgun: the blast and then the slide, chk-chak. The IZh does not do this."),
    Alt("SDLTRATK", 2, r_ltr_volley, ("impactPlate_heavy_003.ogg",), (0.4, 0.9), "Short thunderclap",
        "Three loads as one: staggered cracks over a low body and a metal plate."),
    Alt("SDLTRATK", 3, r_ltr_barrel, ("impactBell_heavy_001.ogg",), (0.4, 1.4), "Chromed barrel",
        "The blast and the chromed barrel ringing like a bell: a metallic «boing»."),
    Alt("SDSTOPAI", 1, r_sto_ringmod, ("hurt_04.ogg",), (0.2, 0.55), "Metallic shout",
        "A shout turned to metal (ring modulation); the tail breaks up at 6 bits."),
    Alt("SDSTOPAI", 2, r_sto_spark, ("grunt_07.ogg",), (0.25, 0.5), "Grunt and spark",
        "A grunt and the machine half shorting out: sparks and the snap of a relay."),
    Alt("SDSTOPAI", 3, r_sto_chopped, ("monster_02.ogg",), (0.3, 0.55), "Broken-up shriek",
        "A shriek cut to pieces, 28 times a second, like a signal being lost."),
    Alt("SDSTODTH", 1, r_sto_short, ("die_01.ogg", "impactMetal_heavy_002.ogg"), (0.9, 1.6),
        "Short circuit and fall",
        "A death cry, a short circuit dying down and the steel of the body against the floor."),
    Alt("SDSTODTH", 2, r_sto_tape, ("roar_03.ogg",), (0.4, 1.4), "Tape grinding to a halt",
        "The voice slows like a tape losing power, breaks up as it sinks and cuts out."),
    Alt("SDSTODTH", 3, r_sto_hydraulic, ("monster_12.ogg", "impactPlate_medium_001.ogg",
                                         "impactPlate_light_004.ogg"),
        (0.9, 1.5), "Hydraulics and plates",
        "A death rattle; the hydraulics give way with a hiss and the armour plates fall to the floor."),
    Alt("SDPZRPAI", 1, r_pzr_plates, ("grunt_06.ogg", "impactPlate_heavy_003.ogg"), (0.3, 0.6),
        "Grunt and plates",
        "A heavy grunt with the clank of the plates, in the range a laptop does play."),
    Alt("SDPZRPAI", 2, r_pzr_helmet, ("troll_02.ogg",), (0.3, 0.6), "Inside the helmet",
        "A snort inside the steel helmet: the voice resonates in the bowl and steam escapes."),
    Alt("SDPZRPAI", 3, r_pzr_roar, ("roar_06.ogg", "impactMetal_heavy_000.ogg"), (0.3, 0.6),
        "Short roar",
        "A brief roar with a bright edge and the metallic clang of the chest plate."),
    Alt("SDRRIPAI", 1, r_rripai_helmet, ("impactWood_light_001.ogg", "impactTin_medium_003.ogg"),
        (0.1, 0.5), "Stock against the helmet",
        "The stock knocks the helmet: wood and a tin ring, just once."),
    Alt("SDRRIPAI", 2, r_rripai_buckles, ("footstep_carpet_002.ogg", "impactMetal_light_003.ogg"),
        (0.15, 0.5), "Real buckles",
        "Real buckles and rings this time: small steel pings and the cloth of the coat."),
    Alt("SDRRIPAI", 3, r_rripai_stagger, ("footstep_concrete_001.ogg", "impactGeneric_light_003.ogg",
                                          "impactMetal_light_004.ogg"),
        (0.15, 0.5), "Step back",
        "The hit knocks him back a step: a boot on concrete and the rifle rattling."),
    Alt("SDLTRPAI", 1, r_ltrpai_mic, ("impactPunch_medium_003.ogg",), (0.15, 0.5), "Knock on the microphone",
        "The hit jolts the microphone: a thump through the radio and a stab of feedback."),
    Alt("SDLTRPAI", 2, r_ltrpai_dropout, (), (0.2, 0.5), "Link breaking up",
        "The signal breaks up: static chopped 22 times a second and two relay clicks."),
    Alt("SDLTRPAI", 3, r_ltrpai_jam, ("impactPlate_light_000.ogg",), (0.2, 0.5), "Interference",
        "An interference whistle sweeping down through the band and the kit jolting."),
    Alt("SDLTRDTH", 1, r_ltrdth_dropped, ("impactPlate_medium_003.ogg", "impactGeneric_light_004.ogg",
                                          "impactSoft_heavy_002.ogg"),
        (0.7, 1.4), "Radio on the floor",
        "The radio falls before he does: the static runs on and cuts out with a click; the body falls."),
    Alt("SDLTRDTH", 2, r_ltrdth_roger, ("impactSoft_heavy_002.ogg", "footstep_concrete_001.ogg"),
        (0.6, 1.3), "End-of-transmission beep",
        "The end-of-transmission beep, slurring as the set dies; then the body."),
    Alt("SDLTRDTH", 3, r_ltrdth_drown, ("impactMetal_light_004.ogg", "impactMetal_light_001.ogg"),
        (0.7, 1.4), "Drowned carrier",
        "The static closes down to a rumble, crackling, while the kit falls to the floor."),
)
ALTS_BY_NAME = {a.name: a for a in ALTS}
LUMPS = tuple(TARGETS)
PACK_OF = {name: pack for (pack, name) in SOURCES}


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode("ascii"))


def target_db(alt: Alt) -> float:
    return FREEDOOM_LEVELS[TARGETS[alt.lump][1]][1] - ALLOWANCE_DB[alt.kind]


def sources_available(alt: Alt, sources_dir: Path = gs.SOURCES_DIR) -> bool:
    if not alt.sources:
        return True
    if gs.ffmpeg_path() is None:
        return False
    return all(source_path(PACK_OF[k], k, sources_dir).is_file() for k in alt.sources)


def render(alt: Alt, sources_dir: Path = gs.SOURCES_DIR) -> tuple[np.ndarray, float, list]:
    """-> (float samples, dB of limiting or the drive, the source refs read)."""
    if not sources_available(alt, sources_dir):
        raise gs.SourceMissing(f"{alt.name}: sources or ffmpeg missing")
    c = C(alt.name, seed_of(alt.name), sources_dir=sources_dir)
    x = hp(np.asarray(alt.recipe(c), dtype=np.float64))
    x = gws.finish(x, PEAK_DBFS)
    y, drive = wa.to_target(x, target_db(alt), LEVEL_ROUTE[alt.kind])
    over = wa.loud_a_db(y) - target_db(alt)
    if over > 0:      # dense even unsaturated (static, a beep): turned down, peak under -1 dBFS
        y = y * 10 ** (-over / 20)
    fo = n_of(FINAL_FADE_S)
    y = y.copy()
    y[-fo:] *= np.linspace(1, 0, fo)
    return y, drive, list(c.refs)


@dataclass
class Rendered:
    alt: Alt
    x: np.ndarray
    drive: float
    refs: list
    wav: bytes


def build(names=None, sources_dir: Path = gs.SOURCES_DIR) -> tuple[list[Rendered], list[str]]:
    done, skipped = [], []
    for alt in ALTS:
        if names and alt.name not in names and alt.lump not in names:
            continue
        try:
            x, d, refs = render(alt, sources_dir)
        except gs.SourceMissing as e:
            skipped.append(str(e))
            continue
        done.append(Rendered(alt, x, d, refs, gws.wav_bytes(x)))
    return done, skipped


# --- The music: D_SDM01E cut to its melodic part (D83) --------------------------------

MUSIC_SOURCE = PROJECT_ROOT / "work" / "audio" / "D_SDM01E.mid"
MUSIC_DIR = PROJECT_ROOT / "work" / "audio"
MUSIC_RENDER_DIR = PROJECT_ROOT / "work" / "audio" / "music_trim"
BEATS_PER_BAR = 4                       # D_SDM01E is 4/4 throughout (midi_inspect)
SOURCE_BARS = 72                        # Card 2b: A 1-16, B 17-32, C 33-48, D 49-64, E 65-72
# lump -> (first bar kept, label, note). The loop is the cut piece
# itself: GZDoom restarts a MIDI from its first tick when it ends.
TRIMS: dict[str, tuple[int, str, str]] = {
    "D_SDM01T": (49, "From the lament (bar 49)",
                 "Starts where the horns take the melody (section D, the «lament») and goes on into the close "
                 "(E). At the end it returns to the lament: the close ends on the pad alone, so the loop comes "
                 "in from near silence. A, B and C are removed (1:46 of introduction)."),
    "D_SDM01U": (33, "From the rising horns (bar 33)",
                 "A longer variant in case the lament alone falls short: it starts at C, where the horns "
                 "rise above the brass chords, and goes on into the lament and the close. A and B are "
                 "removed (1:11 of introduction)."),
}
RECOMMENDED_TRIM = "D_SDM01T"
SEAM_PREVIEW_S = 12.0                   # rendered past the loop point, so the seam is heard
SOUNDFONT_NAME = "gzdoom.sf2"
ZMUSIC_FLUIDSYNTH = 4                   # zmusic.h EMidiDevice: MDEV_FLUIDSYNTH


def _is_on(raw: bytes) -> bool:
    return raw[0] & 0xF0 == 0x90 and len(raw) == 3 and raw[2] > 0


def _is_off(raw: bytes) -> bool:
    return (raw[0] & 0xF0 == 0x80) or (raw[0] & 0xF0 == 0x90 and len(raw) == 3 and raw[2] == 0)


def _is_eot(raw: bytes) -> bool:
    return raw[0] == me.META and len(raw) > 1 and raw[1] == me.META_END_OF_TRACK


def trim_midi(data: bytes, first_bar: int, track_name: str | None = None) -> bytes:
    """Keep bars first_bar..end. Setup events before the cut move to tick 0 in
    their order; a note sounding across the cut is dropped whole (it belongs to
    the bars removed); the End of Track keeps its place relative to the music."""
    fmt, div, tracks = me.read_smf(data)
    cut = (first_bar - 1) * BEATS_PER_BAR * div
    out_tracks = []
    for ti, events in enumerate(tracks):
        head, body, dropped, eot = [], [], set(), None
        for tick, raw in events:
            if _is_eot(raw):
                eot = tick
                continue
            if _is_on(raw):
                key = (raw[0] & 0x0F, raw[1])
                if tick < cut:
                    dropped.add(key)
                    continue
                dropped.discard(key)
                body.append((tick - cut, raw))
            elif _is_off(raw):
                key = (raw[0] & 0x0F, raw[1])
                if tick < cut or key in dropped:
                    dropped.discard(key)
                    continue
                body.append((tick - cut, raw))
            elif tick < cut:
                if ti == 0 and track_name and raw[0] == me.META and raw[1] == 0x03 and not head:
                    payload = track_name.encode("ascii")
                    raw = bytes([me.META, 0x03]) + me.write_varlen(len(payload)) + payload
                head.append((0, raw))
            else:
                body.append((tick - cut, raw))
        end = (eot if eot is not None else max([t for t, _ in events] + [cut])) - cut
        out_tracks.append(head + body + [(max(end, 0), bytes([me.META, me.META_END_OF_TRACK, 0]))])
    return me.write_smf(fmt, div, out_tracks)


def notes_of(data: bytes) -> list[tuple[int, int, int, int, int]]:
    """-> sorted (start tick, channel, pitch, velocity, length) of every note."""
    _, _, tracks = me.read_smf(data)
    out = []
    for events in tracks:
        open_: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for tick, raw in events:
            if _is_on(raw):
                open_.setdefault((raw[0] & 0x0F, raw[1]), []).append((tick, raw[2]))
            elif _is_off(raw):
                stack = open_.get((raw[0] & 0x0F, raw[1]))
                if stack:
                    start, vel = stack.pop(0)
                    out.append((start, raw[0] & 0x0F, raw[1], vel, tick - start))
    return sorted(out)


def midi_length_ticks(data: bytes) -> int:
    _, _, tracks = me.read_smf(data)
    return me.last_tick(tracks)


def division_of(data: bytes) -> int:
    return me.read_smf(data)[1]


def tempo_us(data: bytes) -> int:
    _, _, tracks = me.read_smf(data)
    for events in tracks:
        for _, raw in events:
            if raw[0] == me.META and raw[1] == 0x51:
                return int.from_bytes(raw[3:6], "big")
    return 500000


def seconds_of(data: bytes) -> float:
    return midi_length_ticks(data) / division_of(data) * tempo_us(data) / 1e6


def gzdoom_dir() -> Path | None:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return None
    d = Path(base) / "Programs" / "GZDoom"
    return d if (d / "zmusic.dll").is_file() and (d / "soundfonts" / SOUNDFONT_NAME).is_file() else None


def zmusic_render(data: bytes, seconds: float) -> tuple[np.ndarray, int]:
    """Synthesise a MIDI with GZDoom's own zmusic.dll + gzdoom.sf2, looping, for
    `seconds`. A library call: no engine, no window (D26). -> (stereo float, rate)."""
    d = gzdoom_dir()
    if d is None or not sys.platform.startswith("win"):
        raise gs.SourceMissing("GZDoom's zmusic.dll and gzdoom.sf2 are not on this machine")
    os.add_dll_directory(str(d))
    lib = ctypes.CDLL(str(d / "zmusic.dll"))
    vp, i = ctypes.c_void_p, ctypes.c_int

    class Info(ctypes.Structure):
        _fields_ = [("mBufferSize", i), ("mSampleRate", i), ("mNumChannels", i)]
    lib.ZMusic_OpenSongMem.restype = vp
    lib.ZMusic_OpenSongMem.argtypes = [vp, ctypes.c_size_t, i, ctypes.c_char_p]
    lib.ZMusic_Start.argtypes = [vp, i, ctypes.c_bool]
    lib.ZMusic_Start.restype = ctypes.c_bool
    lib.ZMusic_GetStreamInfo.argtypes = [vp, ctypes.POINTER(Info)]
    lib.ZMusic_FillStream.argtypes = [vp, vp, i]
    lib.ZMusic_FillStream.restype = ctypes.c_bool
    lib.ZMusic_Close.argtypes = [vp]
    lib.ZMusic_GetLastError.restype = ctypes.c_char_p
    buf = ctypes.create_string_buffer(data, len(data))
    song = lib.ZMusic_OpenSongMem(buf, len(data), ZMUSIC_FLUIDSYNTH,
                                  str(d / "soundfonts" / SOUNDFONT_NAME).encode())
    if not song:
        raise RuntimeError(f"zmusic: {lib.ZMusic_GetLastError()!r}")
    try:
        if not lib.ZMusic_Start(song, 0, True):
            raise RuntimeError(f"zmusic: {lib.ZMusic_GetLastError()!r}")
        info = Info()
        lib.ZMusic_GetStreamInfo(song, ctypes.byref(info))
        if info.mNumChannels != 2:
            raise RuntimeError(f"zmusic: expected float stereo, got {info.mNumChannels} channels")
        chunk = ctypes.create_string_buffer(info.mBufferSize)
        frames, chunks = int(seconds * info.mSampleRate), []
        while sum(len(c) for c in chunks) < frames:
            if not lib.ZMusic_FillStream(song, chunk, info.mBufferSize):
                break
            chunks.append(np.frombuffer(chunk.raw, dtype="<f4").reshape(-1, 2).astype(np.float64))
        return np.concatenate(chunks)[:frames], info.mSampleRate
    finally:
        lib.ZMusic_Close(song)


def stereo_wav(x: np.ndarray, rate: int) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.clip(np.round(x * gws.PCM_MAX), -gws.PCM_MAX, gws.PCM_MAX).astype("<i2").tobytes())
    return buf.getvalue()


def build_music(out_midi_dir: Path = MUSIC_DIR, render_dir: Path | None = MUSIC_RENDER_DIR) -> list[dict]:
    """Write the trimmed MIDIs; render them and the untrimmed source if zmusic is here."""
    src = MUSIC_SOURCE.read_bytes()
    rows = []
    pieces = [("D_SDM01E", src, None)] + [(lump, trim_midi(src, bar, f"Soviet Doom - {lump} (D_SDM01E from bar {bar}, D83 draft)"), bar)
                                          for lump, (bar, _, _) in TRIMS.items()]
    for lump, data, bar in pieces:
        if bar is not None:
            out_midi_dir.mkdir(parents=True, exist_ok=True)
            (out_midi_dir / f"{lump}.mid").write_bytes(data)
        row = {"lump": lump, "bar": bar, "seconds": seconds_of(data), "bytes": len(data), "ogg": None}
        if render_dir is not None:
            try:
                x, rate = zmusic_render(data, seconds_of(data) + SEAM_PREVIEW_S)
            except gs.SourceMissing as e:
                row["skipped"] = str(e)
            else:
                render_dir.mkdir(parents=True, exist_ok=True)
                ogg = gws.ogg_bytes(stereo_wav(x, rate))
                if ogg is not None:
                    (render_dir / f"{lump}.ogg").write_bytes(ogg)
                    row["ogg"] = render_dir / f"{lump}.ogg"
                row["peak"] = float(np.max(np.abs(x)))
        rows.append(row)
    return rows


# --- MAP01: candidate public-domain pieces (D83, D59: nothing composed) ----------------
# Rights per docs/sound/MUSIC-RIGHTS.md §1-§2 (dates and sources there); "on disk"
# was checked against work/audio/candidates/ and work/audio/scores/ on 2026-10-20.
MAP01_CANDIDATES: tuple[dict, ...] = (
    {"id": "MAP01-c1", "work": "«Красная армия всех сильней» (Belaya armiya, chorny baron)",
     "who": "Samuil Pokrass (1897-1939); lyrics Pavel Grigoryev (1895-1961)",
     "fit": "The 1920 Red Army march: the cosmodrome's garrison answers the first attack.",
     "rights": "Music: free in RU since 1-1-2010 (d. 1939 +70); free in the US (published 1920, before 1931). "
               "Lyrics: protected in Russia until 1-1-2032 → instrumental only. MUSIC-RIGHTS §2.2.",
     "disk": "NOT on disk. It needs a MIDI with a clean licence (CC0/CC BY/PD per file): "
             "I know of none (SOUNDTRACK §3.2: what is online has no licence). Download to be authorised; "
             "if none exists, it is dropped (D59: we do not sequence).",
     "verdict": "recommended if a clean MIDI turns up"},
    {"id": "MAP01-c2", "work": "Ippolitov-Ivanov, «Шествие сардаря» (Procession of the Sardar), Caucasian Sketches op. 10",
     "who": "Mikhail Ippolitov-Ivanov (1859-1935)",
     "fit": "A short, menacing brass march: the enemy column advancing down the runway.",
     "rights": "Free in RU since 1-1-2006 (d. 1935 +70; died before the war, no +4); free in the US "
               "(published 1894-95). Instrumental, no lyrics. MUSIC-RIGHTS §2.3.",
     "disk": "NOT on disk. Download to be authorised: a PD orchestral score is on IMSLP (blocked by "
             "CAPTCHA for an agent, §4.6.5); an orchestral MIDI with a clean licence: NOT VERIFIED that one exists.",
     "verdict": "the best for tone; depends on finding the MIDI"},
    {"id": "MAP01-c3", "work": "Borodin, «В Средней Азии» (In the Steppes of Central Asia)",
     "who": "Aleksandr Borodin (1833-1887)",
     "fit": "A cosmodrome on the steppe (like Baikonur): wide and still, the calm just before everything breaks.",
     "rights": "Free in RU and the US (d. 1887; composed 1880 and published in the author's lifetime, exact year NOT VERIFIED, "
               "in any case before 1931). Instrumental. MUSIC-RIGHTS §2.3.",
     "disk": "NOT on disk. Download to be authorised; a clean orchestral MIDI NOT VERIFIED.",
     "verdict": "perfect theme, but perhaps too calm for combat"},
    {"id": "MAP01-c4", "work": "Mussorgsky, «Ночь на лысой горе» (Night on Bald Mountain), transcr. Chernov",
     "who": "Modest Mussorgsky (1839-1881); transcription Konstantin Chernov (d. 1944); MIDI Robert Clausecker / Mutopia 2013",
     "fit": "The demonic invasion par excellence; continuous menace, 10 minutes.",
     "rights": "The composition is free in RU and the US; Chernov's transcription free in RU since 2015 or 2019 (both already "
               "past). The MIDI is CC BY 3.0: Clausecker and Mutopia must be credited. MUSIC-RIGHTS §4.4.",
     "disk": "ON disk: work/audio/candidates/MU_Mussorgsky_BaldMountain.mid (D_CND01). No download. "
             "But it is solo piano (no program changes) and its loudest moment is bar 1.",
     "verdict": "the only one ready today; solo piano, the texture you already called plain"},
    {"id": "MAP01-c5", "work": "«Смело, товарищи, в ногу» (Bravely, comrades, keep in step)",
     "who": "Leonid Radin (1860-1900), music and lyrics",
     "fit": "The most Soviet revolutionary song that is wholly free; first map, first fight.",
     "rights": "Music and lyrics free in RU (d. 1900) and the US (published 1901-02). MUSIC-RIGHTS §2.2.",
     "disk": "NOT on disk, and already searched for: neither a reliable PD score (only a protected Soviet "
             "arrangement of 1969) nor a clean MIDI was found. MUSIC-RIGHTS §4.6.5.",
     "verdict": "perfect rights, no source: not viable today"},
)
MAP01_REJECTED = ("Rejected for rights or theme: «Прощание славянки» (Agapkin d. 1964, protected in Russia until "
                  "2039), «Священная война» and Aleksandrov's anthem (restored in the US until 2037-2040), "
                  "Prokofiev and Shostakovich (protected), Tchaikovsky's Marche slave and 1812 (they quote the tsarist anthem).")


# --- Manifest, provenance ----------------------------------------------------------------

def manifest_text(done: list[Rendered]) -> str:
    L = ["# Enemy sound alternatives (D83), written by tools/audio/gen_enemy_alts.py",
         "# Levels: peak dBFS; loudA = loudest 50 ms, A-weighted, dB; RMS dBFS; >300 Hz = energy share.",
         "# Target loudA = the Freedoom lump's loudA minus the allowance of the kind "
         f"({', '.join(f'{k} {v:g} dB' for k, v in ALLOWANCE_DB.items())}).", ""]
    for name, (pk, la, rms) in FREEDOOM_LEVELS.items():
        L.append(f"{name:10s} Freedoom  peak {pk:6.1f}  loudA {la:6.1f}  RMS {rms:6.1f}")
    L.append("")
    for r in done:
        lv = wa.levels(r.x)
        ref = TARGETS[r.alt.lump][1]
        L.append(f"{r.alt.name:13s} {r.alt.label:26s} {lv['length']:.2f} s  peak {lv['peak']:5.1f}  "
                 f"loudA {lv['loud_a']:6.1f} (target {target_db(r.alt):6.1f}, {ref})  RMS {lv['rms']:6.1f}  "
                 f">300 Hz {100 * lv['above300']:3.0f} %  sources: {', '.join(r.alt.sources) or 'synthesis only'}")
    return "\n".join(L) + "\n"


def provenance_tsv(done: list[Rendered]) -> str:
    rows = ["alternative\tpack\tfile\tsha256"]
    for r in done:
        packs = [ref for ref in r.refs if ref.pack in CC0_PACKS]
        if not packs:
            rows.append(f"{r.alt.name}\tSYN\t-\t-")
        for ref in packs:
            rows.append(f"{r.alt.name}\t{ref.pack}\t{ref.name}\t{ref.sha256}")
        if packs:
            rows.append(f"{r.alt.name}\tSYN\t-\t-")       # the layer of our own synthesis
    return "\n".join(rows) + "\n"


def write_outputs(done: list[Rendered], out_dir: Path) -> list[Path]:
    written = []
    (out_dir / "wav").mkdir(parents=True, exist_ok=True)

    def put(path: Path, data: bytes) -> None:
        path.write_bytes(data)
        written.append(path)
    for r in done:
        put(out_dir / "wav" / f"{r.alt.name}.wav", r.wav)
        ogg = gws.ogg_bytes(r.wav)
        if ogg is None:
            raise gs.SourceMissing("ffmpeg is not on the PATH: no OGG")
        put(out_dir / f"{r.alt.name}.ogg", ogg)
    put(out_dir / "MANIFEST.txt", manifest_text(done).encode("utf-8"))
    put(out_dir / "PROVENANCE.tsv", provenance_tsv(done).encode("utf-8"))
    return written


# --- The listening page (the style of the M3 sheets) -----------------------------------------

PAGE_KEY_PREFIX = "sd-m3-enemy-alts-music-"
_rel = wa._rel


def _mmss(s: float) -> str:
    return f"{int(s // 60)}:{int(round(s % 60)):02d}"


def page_items(done: list[Rendered], page: Path, out_dir: Path, music: list[dict]) -> list[dict]:
    items = []
    for r in done:
        a = r.alt
        kind, ref, rej, group, ev, rej_what = TARGETS[a.lump]
        lv = wa.levels(r.x)
        items.append({
            "id": a.name, "sec": "e", "lump": a.lump, "group": group, "ev": ev, "label": a.label,
            "what": a.what, "rejWhat": rej_what, "bed": kind == "bed",
            "src": _rel(out_dir / f"{a.name}.ogg", page),
            "rej": _rel(REJECTED_DIR / rej, page),
            "rep": f"Freedoom {ref}", "repSrc": _rel(FREEDOOM_PREVIEW_DIR / f"{ref}.wav", page),
            "dur": round(lv["length"], 2),
            "lvl": (f"peak {lv['peak']:.1f} dBFS · loudness {lv['loud_a']:.1f} dB "
                    f"(Freedoom {ref}: {FREEDOOM_LEVELS[ref][1]:.1f}) · "
                    f"{100 * lv['above300']:.0f} % above 300 Hz"),
        })
    by = {m["lump"]: m for m in music}
    full = by.get("D_SDM01E")
    for lump, (bar, label, note) in TRIMS.items():
        m = by.get(lump)
        if not m or not m.get("ogg") or not full or not full.get("ogg"):
            continue
        items.append({
            "id": lump, "sec": "m", "lump": lump, "label": label, "what": note,
            "rec": lump == RECOMMENDED_TRIM,
            "src": _rel(m["ogg"], page), "rej": _rel(full["ogg"], page),
            "dur": round(m["seconds"], 1),
            "lvl": (f"loop of {_mmss(m['seconds'])} (was {_mmss(full['seconds'])}) · cut at bar {bar} · "
                    f"the audio runs {SEAM_PREVIEW_S:.0f} s past the end so you hear it come back to the start"),
        })
    for cnd in MAP01_CANDIDATES:
        items.append({"sec": "c", "lump": "MAP01", **cnd})
    return items


PAGE_CSS = wa.PAGE_CSS + """
table.cand{width:100%;border-collapse:collapse;font-size:13.5px}
table.cand th,table.cand td{border-top:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
table.cand th{font-size:12.5px;color:var(--mute);font-weight:600}
table.cand td.vote{width:200px}
table.cand tr.row{display:table-row}table.cand tr.row.hide{display:none}
table.cand tr.row.v-ok td:first-child{box-shadow:inset 4px 0 var(--ok)}table.cand tr.row.v-no td:first-child{box-shadow:inset 4px 0 var(--no)}table.cand tr.row.v-q td:first-child{box-shadow:inset 4px 0 var(--q)}
.rec{display:inline-block;font-size:11px;border-radius:10px;padding:0 7px;margin-left:6px;background:var(--ok);color:#fff}
@media (max-width:900px){table.cand thead{display:none}table.cand tr.row,table.cand td{display:block;width:auto}table.cand td.vote{width:auto}}
"""

PAGE_JS = r"""
const KEY = "__KEY__";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = s => s.toFixed(2) + " s";
const audio = src => `<audio controls preload="none" src="${esc(src)}"></audio>`;
const vote = it => `<div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div><textarea class="note" placeholder="Note (optional)">${esc(st(it.id).n || "")}</textarea></div>`;
function rowE(it){
  let p = `<div class="pl main"><span>Alternative ${esc(it.id.slice(-1))} · ${fmt(it.dur)}</span>${audio(it.src)}</div>`;
  p += `<div class="pl"><span>The rejected one (${esc(it.lump)}${it.bed ? " layer" : ""}, you said NO)</span>${audio(it.rej)}</div>`;
  p += `<div class="pl"><span>${it.bed ? "The Freedoom voice that plays today (the layer will go under your take)" : "In the game today: " + esc(it.rep)}</span>${audio(it.repSrc)}</div>`;
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><div class="name"><code>${esc(it.id)}</code><span class="ev">${esc(it.ev)}</span></div>
      <div class="what"><b>${esc(it.label)}.</b> ${esc(it.what)}</div>
      <div class="meta"><b>Level:</b> ${esc(it.lvl)}</div></div>
    <div class="players">${p}</div>${vote(it)}</div>`;
}
function rowM(it){
  const p = `<div class="pl main"><span>${esc(it.lump)} trimmed · loop ${it.dur.toFixed(1)} s</span>${audio(it.src)}</div><div class="pl"><span>Untrimmed: the whole D_SDM01E</span>${audio(it.rej)}</div>`;
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><div class="name"><code>${esc(it.id)}</code><span class="ev">${esc(it.label)}</span>${it.rec ? '<span class="rec">recommended</span>' : ""}</div>
      <div class="what">${esc(it.what)}</div><div class="meta">${esc(it.lvl)}</div></div>
    <div class="players">${p}</div>${vote(it)}</div>`;
}
function rowC(it){
  return `<tr class="row" id="r-${it.id}" data-id="${it.id}"><td><b>${esc(it.work)}</b><div class="meta">${esc(it.who)}</div><div class="what">${esc(it.fit)}</div></td>
    <td>${esc(it.rights)}</td><td>${esc(it.disk)}<div class="meta"><b>${esc(it.verdict)}</b></div></td><td class="vote">${vote(it)}</td></tr>`;
}
function build(){
  let h = "";
  const E = ITEMS.filter(i => i.sec === "e"), M = ITEMS.filter(i => i.sec === "m"), Cn = ITEMS.filter(i => i.sec === "c");
  for (const L of [...new Set(E.map(i => i.lump))]) {
    const its = E.filter(i => i.lump === L), a = its[0];
    h += `<details class="grp" open><summary><code>${esc(L)}${a.bed ? "-bed" : ""}</code> ${esc(a.group)} · ${esc(a.ev)} <span class="tag no">you said NO</span><span class="rejnote">rejected: ${esc(a.rejWhat)}</span><span class="gcount" data-l="${esc(L)}"></span></summary>`;
    for (const it of its) h += rowE(it);
    h += `</details>`;
  }
  document.getElementById("groups").innerHTML = h;
  document.getElementById("music").innerHTML = M.length ? `<details class="grp" open><summary>MAP01 music trimmed (D_SDM01E from the melodic part) <span class="gcount" data-l="m"></span></summary>${M.map(rowM).join("")}</details>` : `<p class="meta">The music could not be rendered on this machine.</p>`;
  document.getElementById("cands").innerHTML = `<details class="grp" open><summary>Public-domain candidates for MAP01 <span class="gcount" data-l="c"></span></summary><div style="overflow-x:auto"><table class="cand"><thead><tr><th>Work and why it fits</th><th>Rights</th><th>On disk?</th><th>Your vote</th></tr></thead><tbody>${Cn.map(rowC).join("")}</tbody></table></div><p class="meta" style="padding:0 12px 10px">${esc(REJECTED)}</p></details>`;
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
  const groups = {};
  for (const i of ITEMS) { const k = i.sec === "e" ? i.lump : i.sec; (groups[k] = groups[k] || []).push(i); }
  for (const [k, g] of Object.entries(groups)) {
    const el = document.querySelector(`.gcount[data-l="${k}"]`); if (el) el.textContent = `${g.filter(i => st(i.id).v).length} / ${g.length}`;
  }
  const notes = ITEMS.filter(i => (st(i.id).n || "").trim()).map(i => `${i.id}: «${st(i.id).n.trim().replace(/\s+/g, " ")}»`);
  const open = ITEMS.filter(i => !st(i.id).v).map(i => i.id);
  const L = [`M3 enemy alternatives and music (__STAMP__): ${done}/${ITEMS.length} judged`,
    `OK (${by("ok").length}): ${by("ok").join(", ") || "—"}`,
    `NO (${by("no").length}): ${by("no").join(", ") || "—"}`,
    `? (${by("q").length}): ${by("q").join(", ") || "—"}`,
    `notes: ${notes.join(" / ") || "—"}`];
  if (open.length) L.push(`not judged (${open.length}): ${open.join(", ")}`);
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
"""


def page_html(done: list[Rendered], page: Path, out_dir: Path, music: list[dict], stamp: str) -> str:
    items = page_items(done, page, out_dir, music)
    n = len(items)
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    rejected = json.dumps(MAP01_REJECTED, ensure_ascii=False)
    js = PAGE_JS.replace("__KEY__", PAGE_KEY_PREFIX + stamp).replace("__STAMP__", stamp)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M3 enemies and music</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>M3 enemies and music</h1>
  <span class="prog">Judged <b id="pDone">0</b> of <b>{n}</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> only not judged</label>
  <button class="primary" id="copyTop">Copy result</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>What you marked <b>NO</b> on the listening sheet (D83), with three <b>different</b> alternatives for each (another gesture or another material, not retouches); the MAP01 music trimmed so it starts at the melodic part; and the candidate works for the new MAP01. Press <b>OK</b>, <b>NO</b> or <b>?</b> on each row and write a note if you like. It is saved only in this browser. When you are done, <b>Copy result</b> and paste it in the chat.</p>
  <ul>
    <li><b>Volume: already raised</b> to the loudness of the Freedoom sound beside them (shots and voices at the same level; the layers {ALLOWANCE_DB["bed"]:g} dB under, because they will go under your voice). The rejected ones stay at the old, lower volume: compare the character, not the volume.</li>
    <li><b>Laptop:</b> at least half of each alternative's energy is above 300 Hz.</li>
    <li><b>Layers (beds):</b> they are not voices. They go under your voice take when it arrives; in the game today the Freedoom voice plays alone.</li>
    <li><b>Music:</b> rendered with the same library (<code>zmusic.dll</code>) and the same soundfont (<code>gzdoom.sf2</code>) as your GZDoom, without starting the game. Each trim runs {SEAM_PREVIEW_S:.0f} s past the end so you hear how it starts again. Proposal: the trim goes to the <b>practice range</b> (RANGE), where you rejected D_SDAMUR, and MAP01 gets another work.</li>
    <li>Sources: our synthesis and the CC0 packs already on disk (rubberduck on OpenGameArt and Kenney). Nothing downloaded.</li>
  </ul>
</section>
<main id="groups"></main>
<section id="music"></section>
<section id="cands"></section>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Result to paste in the chat</h2>
  <p class="meta">It updates itself. If the button does not copy (some browsers block it on local files), select the text and press Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copy result</button> <button id="reset">Clear all my answers</button></p>
</section>
<footer>Generated {html.escape(stamp)} by sound-designer with <code>tools/audio/gen_enemy_alts.py</code>. Audio: <code>work/audio/enemy_alt/</code> (alternatives), <code>work/audio/sfx/enemies/</code> (rejected), <code>work/audio/preview/freedoom/</code> (today's Freedoom), <code>work/audio/music_trim/</code> (music). The page reads the repo's files by relative path: do not move it out of <code>docs/art/previews/</code>.</footer>
</div>
<script>
const ITEMS = {data};
const REJECTED = {rejected};
{js}
</script>
</body>
</html>
"""


def plan_text() -> str:
    L = []
    for a in ALTS:
        L.append(f"{a.name:13s} {a.kind:5s} target loudA {target_db(a):6.1f} (vs {TARGETS[a.lump][1]})  "
                 f"{a.label}: {', '.join(a.sources) or 'synthesis only'}")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print the plan, write nothing")
    ap.add_argument("--out", type=Path, default=OUT_DIR, help="output directory for the alternatives")
    ap.add_argument("--music-out", type=Path, default=MUSIC_DIR, help="where the trimmed MIDIs go")
    ap.add_argument("--render-out", type=Path, default=MUSIC_RENDER_DIR, help="where the music renders go")
    ap.add_argument("--no-music", action="store_true", help="skip the music trim and render")
    ap.add_argument("--page", type=Path, help="also write the listening page here")
    ap.add_argument("--stamp", help="the page's YYYY-MM-DD_HHMM (default: from its file name)")
    ap.add_argument("names", nargs="*", help="only these alternatives or lumps")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):            # pragma: no cover - a replaced stream
        pass
    if args.list:
        print(plan_text())
        return 0
    done, skipped = build(args.names or None)
    for s in skipped:
        print(f"skipped: {s}", file=sys.stderr)
    if done:
        write_outputs(done, args.out)
        print(manifest_text(done), end="")
    music = [] if args.no_music else build_music(args.music_out, args.render_out)
    for m in music:
        print(f"{m['lump']}: {m['seconds']:.1f} s per loop, {m['bytes']} B"
              + (f", rendered peak {m['peak']:.3f}" if "peak" in m else f" ({m.get('skipped', 'not rendered')})"))
    if args.page:
        stamp = args.stamp or args.page.name[:15]
        args.page.parent.mkdir(parents=True, exist_ok=True)
        args.page.write_text(page_html(done, args.page.resolve(), args.out.resolve(), music, stamp),
                             encoding="utf-8")
        print(f"page: {args.page}")
    if not done and not music:
        return 1
    return 0 if not skipped else 2


if __name__ == "__main__":
    sys.exit(main())
