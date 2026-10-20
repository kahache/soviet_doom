#!/usr/bin/env python3
"""Master and install the weapon sounds the CEO approved (D74, N9; D83 added SDIZFIR B, N9e).

The drafts of `gen_weapon_sfx.py` were levelled for the CEO's ear, not for
the game: the listening sheet measured them 6-18 dB under the Freedoom sound
each replaces, and three of them (`SDAXHIT`, `SDRPEXP`, `SDHKEXP`) with more
than 90 % of their energy under 300 Hz, which a laptop speaker does not
play. This file is the loudness pass, and the install.

What it does to each approved sound, and nothing else (no re-synthesis: the
recipe, its seed and the CEO's take are `gen_weapon_sfx.py`'s, untouched):

1. Render the draft with the take the CEO chose (D74: `SDAXSWG` C,
   `SDAXWAL` C, `SDTTFIR` B, `SDPPFIR` C, the rest A; D83: `SDIZFIR` B,
   installed by N9e on 2026-10-20).
2. **Shelf**, only if the sound is "bass-only" (under `BASS_FLAG_SHARE`
   above 300 Hz, the sheet's flag): a first-order low shelf at
   `SHELF_CORNER_HZ`, as shallow as reaches `MIN_SHARE_ABOVE_300HZ`, never
   deeper than `MAX_SHELF_DB`. The bass stays; it is turned down under the
   rest, so the rest can come up.
3. **Peak** at -1 dBFS (the project's headroom, ENEMY-SOUNDS §6).
4. **Level** to the target with the same ruler as `gen_weapon_alts.py`
   (loudest 50 ms, A-weighted mean square): gain down if it is over; if it
   is under, the look-ahead limiter of `gen_weapon_alts.py` (a gain that
   moves over 12 ms, never a clip) and make-up gain back to -1 dBFS. No
   saturation: a limiter changes the level of a transient, not its timbre.
5. 16-bit WAV master (`work/audio/master/wav/`), then Vorbis OGG into
   `assets/sounds/weapons/<LUMP>.ogg`, which the build packs as
   `sounds/<LUMP>.ogg` (lump `<LUMP>`; `src/lumps/SNDINFO` maps the
   logical names to it).

Targets (`TARGETS`): each sound is set against the Freedoom lump the game
plays for it today, or for its weapon's shot, measured from
`iwads/freedoom2.wad` 0.13.0 with the same ruler (`FREEDOOM_LEVELS`; a test
re-measures them):

- a shot or an impact matches the Freedoom sound it replaces (offset 0);
- the hand Katyusha's per-rocket burst sits 6 dB under `DSBAREXP`: six
  play at once (the draft's own headroom, WEAPON-SOUNDS §4);
- the Katyusha's charge is never louder than the salvo it announces
  (`DSRLAUNC`, offset 0), not `DSBFG`: the BFG's whoosh is 7 dB over the
  salvo, and matching it would need ~12 dB of limiting on a crank;
- the ice axe's swing sits 4 dB under its hit (the hit cuts it, §6);
- a reload sits 4 dB under its weapon's shot as the game plays it today
  (the ROKS-3's shot is still `DSFLAME`: `SDRKFIR` is not approved);
- a pickup sits 3 dB under `DSWPNUP` (D74 brief, as `gen_weapon_alts.py`);
- an empty click sits 6 dB under a pickup, and at least 4 dB under its
  weapon's shot (the two launchers, whose A-weighted level is low): a click
  must not read as a shot.

Run:

    .venv/Scripts/python.exe tools/audio/master_weapon_sfx.py --list
    .venv/Scripts/python.exe tools/audio/master_weapon_sfx.py            # masters + MANIFEST in work/
    .venv/Scripts/python.exe tools/audio/master_weapon_sfx.py --install  # and the OGGs into assets/
    .venv/Scripts/python.exe tools/audio/master_weapon_sfx.py --alts --install  # D94's alternatives (N9e)
    .venv/Scripts/python.exe -m unittest tests.test_weapon_sfx_install -v

Deterministic: the drafts are (gen_weapon_sfx.py), and every step here is
plain arithmetic with fixed constants and a fixed-step search. The WAV
masters are byte-identical run to run on one machine; the OGGs depend on
the local ffmpeg build (as the drafts' do), so an installed sound is
re-encoded only on the machine that installed it, or it goes back through
the tests as a new install (`INSTALLED_SHA256`).

GPL-3.0 (the script); its output CC BY-NC-SA 4.0 (D15), with the CC0
layers it mixes credited in `docs/art/LICENSES.md` and WEAPON-SOUNDS §2.1.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_weapon_alts as alts  # noqa: E402  (the ruler and the limiter)
import gen_weapon_sfx as gws  # noqa: E402  (the recipes, takes, WAV/OGG writers)

PROJECT_ROOT = gws.PROJECT_ROOT
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "weapons"
WORK_DIR = PROJECT_ROOT / "work" / "audio" / "master"

PEAK_DBFS = alts.PEAK_DBFS                  # -1 dBFS
LOUDNESS_TOLERANCE_DB = alts.LOUDNESS_TOLERANCE_DB   # 1 dB, the alternatives' window
BASS_EDGE_HZ = alts.BASS_EDGE_HZ            # 300 Hz, the listening sheet's line
BASS_FLAG_SHARE = 0.10                      # under this above 300 Hz = "bass-only" (the sheet's flag)
MIN_SHARE_ABOVE_300HZ = 0.12                # what the shelf aims for: clear of the flag, no more
SHELF_CORNER_HZ = 250.0                     # first-order shelf: -1.5 dB at 300 Hz for a 6 dB shelf
SHELF_STEP_DB = 0.5
MAX_SHELF_DB = 9.0                          # "gentle": deeper than this is re-voicing, not mastering
MAX_LIMIT_DB = 9.0                          # deepest limiting: beyond it a transient is flattened
PLATEAU_DB = 0.25                           # short of target: stop where more limiting stops paying
LIMIT_SEARCH_STEPS = 20
DECODED_PEAK_CEILING_DBFS = -0.1            # the OGG overshoots its -1 dBFS master by up to ~0.8 dB; never clips
CODEC_LOUDNESS_DB = 0.5                     # decoded OGG vs its WAV master, loudest 50 ms A (measured <= 0.42)

# Freedoom 0.13.0 lumps, measured with gen_weapon_alts.levels (loudest 50 ms,
# A-weighted, dB) from iwads/freedoom2.wad; tests/test_weapon_sfx_install.py
# re-measures them. 8-bit DMX at their own rates, all peaking at 0 dBFS.
FREEDOOM_LOUD_A: dict[str, float] = {
    "DSPUNCH": -12.48,     # the fist's hit: SDAXHIT's stand-in
    "DSPISTOL": -10.39,    # the TT-33's and the PPSh-41's stand-in
    "DSRLAUNC": -14.24,    # the RPG-7's launch and the Katyusha's salvo
    "DSBAREXP": -9.05,     # the PG-7V's and the Katyusha rocket's burst
    "DSFLAME": -11.05,     # the ROKS-3's jet, still in game (SDRKFIR not approved)
    "DSWPNUP": -5.20,      # every weapon pickup today
    "DSSHOTGN": -8.17,     # the IZh-58's shot until D83 (SDIZFIR B)
}
FREEDOOM_TOLERANCE_DB = 0.05


@dataclass(frozen=True)
class Install:
    lump: str
    take: str            # the CEO's take (D74)
    kind: str            # shot / impact / burst / charge / swing / reload / pickup / dry
    ref: str             # the Freedoom lump the target is read from
    offset_db: float     # target = FREEDOOM_LOUD_A[ref] + offset_db
    why: str

    @property
    def target_db(self) -> float:
        return FREEDOOM_LOUD_A[self.ref] + self.offset_db


SWING_UNDER_HIT_DB = -4.0
RELOAD_UNDER_SHOT_DB = -4.0
PICKUP_UNDER_DSWPNUP_DB = -3.0
DRY_UNDER_PICKUP_DB = -6.0
BURST_SIX_AT_ONCE_DB = -6.0
DRY_UNDER_SHOT_DB = -4.0      # where the shot itself is under DSWPNUP - 9 (the two launchers)

_DRY = PICKUP_UNDER_DSWPNUP_DB + DRY_UNDER_PICKUP_DB

# The 25 OK of D74 and SDIZFIR B of D83 (docs/PRD.md), in slot order. Takes: SDAXSWG C,
# SDAXWAL C, SDTTFIR B, SDPPFIR C; the rest A.
INSTALLS: tuple[Install, ...] = (
    Install("SDAXSWG", "C", "swing", "DSPUNCH", SWING_UNDER_HIT_DB, "under the hit, which cuts it"),
    Install("SDAXHIT", "A", "impact", "DSPUNCH", 0.0, "replaces DSPUNCH"),
    Install("SDAXWAL", "C", "impact", "DSPUNCH", 0.0, "the same blow, on stone"),
    Install("SDTTFIR", "B", "shot", "DSPISTOL", 0.0, "replaces DSPISTOL"),
    Install("SDTTRLD", "A", "reload", "DSPISTOL", RELOAD_UNDER_SHOT_DB, "under the TT-33's shot"),
    Install("SDTTDRY", "A", "dry", "DSWPNUP", _DRY, "under a pickup"),
    Install("SDIZDRY", "A", "dry", "DSWPNUP", _DRY, "under a pickup"),
    Install("SDIZFIR", "B", "shot", "DSSHOTGN", 0.0, "replaces DSSHOTGN (D83: take B, N9e)"),
    Install("SDPPFIR", "C", "shot", "DSPISTOL", 0.0, "replaces DSPISTOL"),
    Install("SDPPRLD", "A", "reload", "DSPISTOL", RELOAD_UNDER_SHOT_DB, "under the PPSh's shot"),
    Install("SDPPPKP", "A", "pickup", "DSWPNUP", PICKUP_UNDER_DSWPNUP_DB, "3 dB under DSWPNUP"),
    Install("SDPPDRY", "A", "dry", "DSWPNUP", _DRY, "under a pickup"),
    Install("SDRPFIR", "A", "shot", "DSRLAUNC", 0.0, "replaces DSRLAUNC"),
    Install("SDRPEXP", "A", "impact", "DSBAREXP", 0.0, "replaces DSBAREXP"),
    Install("SDRPRLD", "A", "reload", "DSRLAUNC", RELOAD_UNDER_SHOT_DB, "under the launch"),
    Install("SDRPPKP", "A", "pickup", "DSWPNUP", PICKUP_UNDER_DSWPNUP_DB, "3 dB under DSWPNUP"),
    Install("SDRPDRY", "A", "dry", "DSRLAUNC", DRY_UNDER_SHOT_DB, "under the launch, which is quieter than a pickup"),
    Install("SDRKRLD", "A", "reload", "DSFLAME", RELOAD_UNDER_SHOT_DB, "under the jet heard today"),
    Install("SDRKPKP", "A", "pickup", "DSWPNUP", PICKUP_UNDER_DSWPNUP_DB, "3 dB under DSWPNUP"),
    Install("SDRKDRY", "A", "dry", "DSWPNUP", _DRY, "under a pickup"),
    Install("SDHKCHG", "A", "charge", "DSRLAUNC", 0.0, "never over the salvo it announces"),
    Install("SDHKFIR", "A", "shot", "DSRLAUNC", 0.0, "replaces DSRLAUNC"),
    Install("SDHKEXP", "A", "burst", "DSBAREXP", BURST_SIX_AT_ONCE_DB, "six play at once"),
    Install("SDHKRLD", "A", "reload", "DSRLAUNC", RELOAD_UNDER_SHOT_DB, "under the salvo"),
    Install("SDHKPKP", "A", "pickup", "DSWPNUP", PICKUP_UNDER_DSWPNUP_DB, "3 dB under DSWPNUP"),
    Install("SDHKDRY", "A", "dry", "DSRLAUNC", DRY_UNDER_SHOT_DB, "under the salvo, which is quieter than a pickup"),
)
INSTALLS_BY_LUMP = {i.lump: i for i in INSTALLS}

# Not approved in D74 (NO: SDTTPKP, SDIZRLD, SDRKFIR; ?: SDAXPKP, SDIZPKP).
# They stay on Freedoom or silent, and this file refuses them. SDIZFIR left
# this list with D83 (take B OK).
UNDECIDED = ("SDTTPKP", "SDIZRLD", "SDRKFIR", "SDAXPKP", "SDIZPKP")

# The reloads of guns with no reload state (D47 parked magazines): packed
# and named in SNDINFO, played by nothing until a magazine mechanic exists.
PARKED = ("SDTTRLD", "SDPPRLD", "SDRKRLD")

# Measured short of target (dB, the WAV master): every one already at the
# brief's ceiling (-1 dBFS peak, limiting stopped where more stops paying,
# MAX_LIMIT_DB at most). Why, per kind, in WEAPON-SOUNDS.md section 10:
# clicks are 3-10 ms long in a 50 ms ruler; SDAXHIT has nothing above
# 1 kHz for A-weighting to count; the shots and pickups would need
# saturation, which this pass does not use. A test re-measures each.
SHORT_OF_TARGET: dict[str, float] = {
    "SDAXHIT": 6.3, "SDAXWAL": 3.3, "SDTTFIR": 2.6, "SDTTRLD": 1.1, "SDTTDRY": 6.2,
    "SDIZDRY": 5.1, "SDPPFIR": 2.6, "SDPPRLD": 1.2, "SDPPPKP": 2.4, "SDPPDRY": 1.8,
    "SDRPEXP": 4.8, "SDRPPKP": 3.2, "SDRKPKP": 3.6,
    "SDIZFIR": 7.0,     # D83 take B: 88 % of it under 300 Hz, which A-weighting does not count
}
SHORT_TOLERANCE_DB = 0.15

# SHA-256 of what is installed: the WAV master (this machine's numpy and
# ffmpeg decode of the sources) and the OGG in assets/ (this machine's
# ffmpeg). Written by `--install`, pinned here by hand after review; the
# tests compare both.
INSTALLED_SHA256: dict[str, tuple[str, str]] = {
    "SDAXSWG": ("668648bf218a5cbdaa5784d5d97c0a37eca451581c0991843edc86356f951071",
                "1d51018b7e580a5ec801071261ced711fb414f8f1ad8e38b0515594d5a1e3cfb"),
    "SDAXHIT": ("e3879ef543af268ad4153d05a9cb565c8123940b6089738107a529a7b8857b8b",
                "2e04114992654ed5f3f6ff35d3b99bececcb81427fdfd0c29e74397522acc8c2"),
    "SDAXWAL": ("b82723321cf6a5133a9730c1276bf05b59628f5d4913792f0f7a489a3f0d91eb",
                "ed4e99c4360a34edf610799ac940e0b43c1b4aa6809705975954450cd70115aa"),
    "SDTTFIR": ("dc14616870b095cad7a0a30a0c8f6f0f5d98d15212305b3db86660ed5f37a457",
                "739ae2ed34cd1c3b357bb8fd5ce94ace5f14dcb84b769e076097baf6b0494f8a"),
    "SDTTRLD": ("a692434d44863b3fa02719da69b9b23623f0373e094e5a84e36618a6f1c1f8cd",
                "2b169eb4348ef6ed213d5467298c9fcefeb3d9b00b3a1a4e43eac0af78293d4c"),
    "SDTTDRY": ("c93e8ef4c8a8c67814cbbc0fe30364767ebc56751ff1b9e7b576c21c671979fb",
                "045ae7e97c90bf730b9188bc9eee5eff3e03f9c9ec91d3fae96f613abe726180"),
    "SDIZDRY": ("bb61fb8191fb9c538c2806a2a196713dfd241d2e6e7475cbdf198f67e944fa47",
                "cfb39f64fcd7ace268c520d8f150236b25f0af56979b2c382a47a421ed14fc29"),
    "SDIZFIR": ("a751909955602904217cbfe900d89330b036124ded864812bbe527d4dc183ddc",
                "21c97f9dc8286c0355eb0822de585e0c1a65f4224d8cd44ba7b3ce3e4526c077"),
    "SDPPFIR": ("f3ac80e99bf96ddc7471bce0a9afdec49e5d3de41bcce3b36ea60db384d11c9a",
                "95c7c9a43af93c977e0bcdd5a05d234d62ed04ad9f54e734b0503aac52de78a1"),
    "SDPPRLD": ("7ede0d53a6f1bffa4fd327008d3a62e3062e14c0490890ac142525a5f45a209e",
                "628cfaf6396b8aa873889b7aea740076e96a819f13ab7c715356611ed9488fd2"),
    "SDPPPKP": ("5d683d30c34e53699deb0ded7693834bdc9e0e4c72a21bda2a9143b6dcafd040",
                "5646109b593d73ca9bbe9ff54dfb29058ee3440635dbbfb50376878688780225"),
    "SDPPDRY": ("7130bb9142e2fbfad2edc211ba5209169bbc64022f70dc483e79047027ed4918",
                "a091c637ced99d8a539e9cdcfb5585d22b0389475106bc23d3a15ecf5713066e"),
    "SDRPFIR": ("02e0cfc07718ca8d0491082a17f3aaf091b7bcd9112fdf1a47b3dd1830cbea55",
                "dc7ee5466385c06fb668997220369d9733efa8aa570a4ce0209cd22e151b7baa"),
    "SDRPEXP": ("e7a3521129a65d1f8151a0cdd76951993b4220572ad5f759e75a335bac256a84",
                "9367c7703521a4f704403db2e0911c5d1a6ed700d6ef7ca626ef1ed2b0b7365b"),
    "SDRPRLD": ("94ebff764eefa7d3ed0d00aecc4d782a3ac66d8c265fdac902f7ef94f4c5d322",
                "057c0ca4bbc209a47b6e24a168106534d44f6e035391b5cfc2717eb5f4336868"),
    "SDRPPKP": ("413a9fb4a270f368f1e795e1fba3f18d6db63bd26fad96bf0e7666c894eb6932",
                "5e5b85f42adaee54e6d847cfc5ca8972702d0787d482b710db892f13eb20152d"),
    "SDRPDRY": ("e391f56dc654913f0b476eab22a3271ea1d38c43e247d13507f05ed0e96f3aff",
                "aea27fb0124ab3028982cb2426f5938c87f95c505869ec783f8669de737fcce2"),
    "SDRKRLD": ("5a42720f58d87a8340a509ee797fb7d069dcfc5001280a8f21b837cc71c3a59a",
                "787a5421ac8d62d07e0c7e6789d33a15d5d635d8c23cb01f304eb343da776d33"),
    "SDRKPKP": ("ca5fe366301ba87ede37617283ee6dadafd2938b6f2cd19d1d94e7fb33a6b0da",
                "eb417c4dca5200932cf2c036bc10926524a4aeec8d31a14cc7892a4a11990b8e"),
    "SDRKDRY": ("9a00471ebb4e1de5d7220d4fc8536e1e0984ae21205bcebf0d223959ea92ebee",
                "39a4408fee7524481c9266fab577bb2a5a9ad59950b3aa19eb035f8be3460fb4"),
    "SDHKCHG": ("f40d0261b8e5d08fc57e2344a8876892e6434be7a8619c570dbcc18b3f585b90",
                "cdec06bbc08ad4f276971613a0b24d5ce57cc6ef20aeeeb4de5058e5b4303940"),
    "SDHKFIR": ("47faccddb37b112063866f389810f5c6a028c4e2a4c6385da4fda10e891a2d06",
                "77158e47090ae51f1a9f39b53d8cc35587daeff00ca2adc538de0f3ea1b77e7c"),
    "SDHKEXP": ("73a4c7e77b1620aadaf8c5c1979cfc3576b9f99edc00e1777410ae0b040e2ae2",
                "8ddfb670b7a63da5176528deddb6490d8c82bb5c3ec7fbdcc6532ea1a57ca94a"),
    "SDHKRLD": ("7bc809b0dab7021700024285eba10fd9b892fa6ed37070c7f513ae86fccc4437",
                "f066966e537ec14814ab68a9ffb576607df1b5f5862c809a34b718c3a7d0f6f6"),
    "SDHKPKP": ("b0cbce1c6d99ea82da9026c1cb14b04ca61f070472a076f7434672b0bfac1da7",
                "21e9a723104add1f3dcee63580169d15b14ecb7f65ed0af331a8c8d75716ad45"),
    "SDHKDRY": ("0b3fe95c81f1ad499178e42e14c7ef1d3297b9f621e76664f7e34574d01f7234",
                "575e5665ac291d905b6289fa1720c4197c1a89b308872dcd85c0fa20ca285316"),
}


# --- Mastering ---------------------------------------------------------------------

def low_shelf(x: np.ndarray, depth_db: float, corner_hz: float = SHELF_CORNER_HZ) -> np.ndarray:
    """First-order low shelf, minimum phase: -depth_db at DC, 0 dB far above corner."""
    if depth_db <= 0:
        return x.copy()
    g = 10 ** (-depth_db / 20)
    y = gws.filt(x, lambda f: np.sqrt((f ** 2 + (g * corner_hz) ** 2) / (f ** 2 + corner_hz ** 2)))
    fo = min(gws.n_of(gws.FADE_OUT_S), len(y))
    y[-fo:] *= np.linspace(1, 0, fo)        # the filter's memory must not end on a step
    return y


def at_peak(x: np.ndarray, peak_dbfs: float = PEAK_DBFS) -> np.ndarray:
    return x / np.max(np.abs(x)) * 10 ** (peak_dbfs / 20)


def limited(x: np.ndarray, depth_db: float) -> np.ndarray:
    """The limiter `depth_db` under the peak, then make-up gain to PEAK_DBFS."""
    if depth_db <= 0:
        return at_peak(x)
    return at_peak(alts.limit(x, np.max(np.abs(x)) * 10 ** (-depth_db / 20)))


def _shallowest(y: np.ndarray, wanted_db: float, hi: float) -> float:
    """Shallowest limiter depth in [0, hi] whose loudness reaches wanted_db
    (loudness rises with depth, then flattens: the bisection needs no more)."""
    lo = 0.0
    for _ in range(LIMIT_SEARCH_STEPS):
        mid = (lo + hi) / 2
        if alts.loud_a_db(limited(y, mid)) < wanted_db:
            lo = mid
        else:
            hi = mid
    return hi


@dataclass
class Level:
    x: np.ndarray
    limit_db: float
    gain_db: float
    reached: bool


def level(y: np.ndarray, target_db: float) -> Level:
    """y (peak at PEAK_DBFS) to target: gain down, or the limiter and make-up.

    When even MAX_LIMIT_DB cannot reach the target (a click, a thud with
    nothing above 1 kHz: the 50 ms A-weighted window is full and only the
    tail would still rise), the limiter stops where it stops paying, within
    PLATEAU_DB of what MAX_LIMIT_DB gives, and the lump is SHORT_OF_TARGET.
    """
    loud = alts.loud_a_db(y)
    if loud >= target_db:
        gain = target_db - loud
        return Level(y * 10 ** (gain / 20), 0.0, gain, True)
    best = alts.loud_a_db(limited(y, MAX_LIMIT_DB))
    if best >= target_db:
        depth = _shallowest(y, target_db, MAX_LIMIT_DB)
        return Level(limited(y, depth), depth, 0.0, True)
    depth = _shallowest(y, best - PLATEAU_DB, MAX_LIMIT_DB)
    return Level(limited(y, depth), depth, 0.0, False)


def bass_only(x: np.ndarray) -> bool:
    return alts.share_above(x) < BASS_FLAG_SHARE


def shelf_steps(x: np.ndarray) -> list[float]:
    if not bass_only(x):
        return [0.0]
    n = int(round(MAX_SHELF_DB / SHELF_STEP_DB))
    return [SHELF_STEP_DB * k for k in range(1, n + 1)]


@dataclass
class Mastered:
    install: Install
    draft: np.ndarray        # the take as gen_weapon_sfx renders it
    x: np.ndarray            # the master
    shelf_db: float
    limit_db: float
    gain_db: float           # applied after the peak step (<= 0: turned down)
    reached: bool            # loudness within the window of its target

    @property
    def wav(self) -> bytes:
        return gws.wav_bytes(self.x)

    @property
    def pre_limit(self) -> np.ndarray:
        """The shelved draft at peak, before the level step (the limiter's input)."""
        return at_peak(low_shelf(self.draft, self.shelf_db))


def master(install: Install, draft: np.ndarray) -> Mastered:
    """Shelf (bass-only sounds: the shallowest step whose MASTER clears
    MIN_SHARE_ABOVE_300HZ, the limiter included, which ducks the transients
    that carry the highs), peak, level."""
    for shelf in shelf_steps(draft):
        lv = level(at_peak(low_shelf(draft, shelf)), install.target_db)
        if shelf == 0.0 or alts.share_above(lv.x) >= MIN_SHARE_ABOVE_300HZ:
            break
    reached = abs(alts.loud_a_db(lv.x) - install.target_db) <= LOUDNESS_TOLERANCE_DB
    return Mastered(install, draft, lv.x, shelf, lv.limit_db, lv.gain_db, reached)


def render_draft(install: Install, sources: gws.Sources, take: str | None = None) -> np.ndarray:
    if install.lump in UNDECIDED:
        raise ValueError(f"{install.lump} is not approved (D74)")
    return gws.render(gws.LUMPS_BY_NAME[install.lump], sources, take or install.take)


def build(names=None, sources: gws.Sources | None = None) -> tuple[list[Mastered], dict[str, str]]:
    sources = sources or gws.Sources()
    done, skipped = [], {}
    for inst in INSTALLS:
        if names and inst.lump not in names:
            continue
        try:
            done.append(master(inst, render_draft(inst, sources)))
        except gws.MissingSource as exc:
            skipped[inst.lump] = str(exc)
    return done, skipped


# --- Reports and outputs -------------------------------------------------------------

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_text(done: list[Mastered], oggs: dict[str, bytes] | None = None) -> str:
    lines = ["# master_weapon_sfx.py (N9, D74): the approved weapon sounds, before and after",
             "# loudA = loudest 50 ms, A-weighted, dB (gen_weapon_alts.py's ruler); >300 = energy share",
             "# shelf = low-shelf depth at 250 Hz (bass-only sounds only); limit = limiter depth; gain = turned down",
             ""]
    for name, v in FREEDOOM_LOUD_A.items():
        lines.append(f"{name:9s} Freedoom loudA {v:6.2f}")
    lines.append("")
    for m in done:
        i = m.install
        b, a = alts.levels(m.draft), alts.levels(m.x)
        row = (f"{i.lump} take {i.take} {i.kind:7s} target {i.target_db:6.1f} ({i.ref} {i.offset_db:+.0f})  "
               f"before peak {b['peak']:5.1f} loudA {b['loud_a']:6.1f} >300 {100 * b['above300']:3.0f} %  "
               f"after peak {a['peak']:5.1f} loudA {a['loud_a']:6.1f} >300 {100 * a['above300']:3.0f} %  "
               f"shelf {m.shelf_db:3.1f} dB  limit {m.limit_db:4.1f} dB  gain {m.gain_db:5.1f} dB  "
               f"{'on target' if m.reached else 'SHORT ' + format(i.target_db - a['loud_a'], '.1f') + ' dB'}  "
               f"wav {sha256(m.wav)}")
        if oggs and i.lump in oggs:
            row += f"  ogg {sha256(oggs[i.lump])}"
        lines.append(row)
    return "\n".join(lines) + "\n"


def ogg_of(m: Mastered) -> bytes:
    ogg = gws.ogg_bytes(m.wav)
    if ogg is None:
        raise gws.MissingSource("ffmpeg is not on the PATH: no OGG")
    return ogg


def write_outputs(done: list[Mastered], work_dir: Path = WORK_DIR,
                  asset_dir: Path | None = None) -> dict[str, bytes]:
    """WAV masters and the MANIFEST under work/; the OGGs into asset_dir if given."""
    (work_dir / "wav").mkdir(parents=True, exist_ok=True)
    (work_dir / "ogg").mkdir(parents=True, exist_ok=True)
    oggs = {}
    for m in done:
        (work_dir / "wav" / f"{m.install.lump}.wav").write_bytes(m.wav)
        oggs[m.install.lump] = ogg_of(m)
        (work_dir / "ogg" / f"{m.install.lump}.ogg").write_bytes(oggs[m.install.lump])
    if asset_dir is not None:
        asset_dir.mkdir(parents=True, exist_ok=True)
        for lump, data in oggs.items():
            (asset_dir / f"{lump}.ogg").write_bytes(data)
    (work_dir / "MANIFEST.txt").write_text(manifest_text(done, oggs), encoding="utf-8")
    return oggs


def plan_text() -> str:
    rows = [f"{i.lump}  take {i.take}  {i.kind:7s} target {i.target_db:6.1f} dB A ({i.ref} {i.offset_db:+.0f}: {i.why})"
            for i in INSTALLS]
    return "\n".join(rows + [f"{len(INSTALLS)} approved (D74, D83); not installed: {', '.join(UNDECIDED)}"]) + "\n"


# --- D94 (N9e): the weapon-sound alternatives the CEO approved ------------------------
# docs/art/previews/2026-10-20_1235_M3_listening-alternatives-animated.html,
# judged with each weapon's frames moving (D92). OK: SDTTPKP alt1+alt2,
# SDAXPKP alt1+alt3, SDIZRLD alt3, SDRKFIR alt1-3; NO: SDIZPKP alt1-3 (the
# IZh-58's pickup keeps Doom's generic one). Several takes of one sound all
# ship under the weapon's 7-letter name plus the take number and the code's
# name becomes a SNDINFO `$random` over <name>/<take> (MOD-SPEC 6.2). One
# take keeps the bare name (SDIZRLD).
#
# The pass, as for the enemies' D86 alternatives (master_enemy_sfx.py): each
# was levelled by gen_weapon_alts.py to its target for the CEO's page, so a
# take in its window ships as rendered; then the codec check (encode,
# decode; while the decoded peak reaches DECODED_PEAK_CEILING_DBFS, the
# look-ahead limiter takes the master's ceiling down by the overshoot plus
# CODEC_MARGIN_DB). The ROKS-3 restarts its fire sound every 3 tics on
# CHAN_WEAPON (roks3.zs); a $random alias picks a take at each restart.

@dataclass(frozen=True)
class AltInstall:
    lump: str            # the lump it ships as
    alt: str             # gen_weapon_alts.py's name, <CARD>_alt<N>
    logical: str         # its SNDINFO name
    group: str           # the name the code plays

    @property
    def card(self) -> str:
        return self.alt.split("_alt")[0]

    @property
    def target_db(self) -> float:
        return alts.target_db(alts.ALTS_BY_NAME[self.alt])


def _alt_group(card: str, logical: str, takes: tuple[int, ...]) -> list[AltInstall]:
    if len(takes) == 1:
        return [AltInstall(card, f"{card}_alt{takes[0]}", logical, logical)]
    return [AltInstall(f"{card}{n}", f"{card}_alt{n}", f"{logical}/{n}", logical) for n in takes]


D94_ALTS = (("SDTTPKP", "sd/weapon/tokarev/pickup", (1, 2)), ("SDAXPKP", "sd/weapon/iceaxe/pickup", (1, 3)),
            ("SDIZRLD", "sd/weapon/izh/reload", (3,)), ("SDRKFIR", "sd/weapon/roks3/fire", (1, 2, 3)))
ALT_INSTALLS: tuple[AltInstall, ...] = tuple(i for c, lg, t in D94_ALTS for i in _alt_group(c, lg, t))
ALT_INSTALLS_BY_LUMP = {i.lump: i for i in ALT_INSTALLS}
REJECTED_ALTS = ("SDTTPKP_alt3", "SDAXPKP_alt2", "SDIZPKP_alt1", "SDIZPKP_alt2", "SDIZPKP_alt3",
                 "SDIZRLD_alt1", "SDIZRLD_alt2")
CODEC_MARGIN_DB = 0.2
CODEC_PASSES = 6

# Written after the run (--alts), pinned by hand: the takes the codec check
# limited (dB), and (WAV master, OGG) SHA-256 of what is installed.
ALT_CODEC_TRIMMED: dict[str, float] = {"SDTTPKP2": 0.9, "SDIZRLD": 0.5, "SDRKFIR1": 0.7}
ALT_INSTALLED_SHA256: dict[str, tuple[str, str]] = {
    "SDTTPKP1": ("78a28da4bbf2e22e0a5a70f4862d525529d4f8d702f2c59dd9bde786e257d3d7",
                 "5ed5bbe224888bb2483de7a7339b50f2f7b8c88716e667600f46c29d88a29efe"),
    "SDTTPKP2": ("ed9ceeb9c76c121aad5f4789e4631239a7a6696f3c87f54744108b37a5c072f0",
                 "85edcef3644a53b6efeebdf563f4396f199f4d505d8e2578e94d049cf1e35b77"),
    "SDAXPKP1": ("50b1efba2410d6fb56b154f061ede8e3e34e0ace4f1fd2cc0fbbb95430b07007",
                 "f4c60daa9351018252ab26972a2ead0895ee4582864b50dacdde7da653d6875b"),
    "SDAXPKP3": ("b74be921511a9b6ee412ec49e9707425bd8efa72ac78ec21d08c5e2ced21b304",
                 "535f4a703dc1518713ca3c66fc50dfc3b79de6ec814dc50809f04cdb8c1ff3c5"),
    "SDIZRLD": ("a9e959f8fb9356b14280849a86de0f5395c91fb144243b97b1a4c33f1cb38e51",
                 "ec78869141e46c829b58df0797d9fedafb303bf70b8fd7dfada59641d00bbdb2"),
    "SDRKFIR1": ("069d082b4ac768556bec4b54295d330a9787ba36fc575b69c79d9c4f5297eeda",
                 "09c2466546f788646339c34710bf09569cb91ffaa30061ec0115979e19a76149"),
    "SDRKFIR2": ("d34b7f99cc91e19c4d7a028ee7fb25d1acb68d08e453fed66c871ab381c4a6fe",
                 "9fe85a3fe943d5785e7fc7a9ef86e67f5f69f561b20b20ab6347e6050223da9e"),
    "SDRKFIR3": ("1560d78336ab7a9209f42108b0298aaa875a3363548b5b0ccd268073d22ac16d",
                 "53a7b6ed136f8c2647e72acfdd1cb7d39e248725e93b5c8923effc9e6573b80b"),
}


@dataclass
class AltMastered:
    install: AltInstall
    draft: np.ndarray
    x: np.ndarray
    untouched: bool
    codec_db: float

    @property
    def wav(self) -> bytes:
        return gws.wav_bytes(self.x)


def decoded_peak_db(ogg: bytes) -> float:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.ogg"
        path.write_bytes(ogg)
        return alts.peak_db(gws.decode(path))


def master_alt(install: AltInstall, sources: alts.AltSources | None = None) -> AltMastered:
    if install.alt in REJECTED_ALTS:
        raise ValueError(f"{install.alt} is not approved (D94)")
    draft, _ = alts.render(alts.ALTS_BY_NAME[install.alt], sources or alts.AltSources())
    loud = alts.loud_a_db(draft)
    x = draft if abs(loud - install.target_db) <= LOUDNESS_TOLERANCE_DB else None
    if x is None:
        raise ValueError(f"{install.alt}: {loud:.2f} dB A is out of its window; it is not what the CEO heard")
    depth = 0.0
    for _ in range(CODEC_PASSES):
        over = decoded_peak_db(gws.ogg_bytes(gws.wav_bytes(x))) - DECODED_PEAK_CEILING_DBFS
        if over < 0:
            return AltMastered(install, draft, x, depth == 0.0, round(depth, 3))
        depth += over + CODEC_MARGIN_DB
        x = alts.limit(draft, 10 ** ((alts.peak_db(draft) - depth) / 20))
    raise RuntimeError(f"{install.lump}: the OGG still overshoots after {CODEC_PASSES} passes")


def alt_manifest_text(done: list[AltMastered], oggs: dict[str, bytes]) -> str:
    lines = ["# master_weapon_sfx.py --alts (N9e, D94): the approved weapon-sound alternatives", ""]
    for m in done:
        a = alts.levels(m.x)
        state = "untouched" if m.untouched else f"codec {m.codec_db:.1f} dB"
        lines.append(f"{m.install.lump} {m.install.alt:13s} {m.install.logical:30s} target {m.install.target_db:6.1f}  "
                     f"peak {a['peak']:5.1f} loudA {a['loud_a']:6.1f} >300 {100 * a['above300']:3.0f} %  {state}  "
                     f"wav {sha256(m.wav)}  ogg {sha256(oggs[m.install.lump])}")
    return "\n".join(lines) + "\n"


def install_alts(asset_dir: Path | None, work_dir: Path = WORK_DIR) -> list[AltMastered]:
    sources = alts.AltSources()
    done = [master_alt(i, sources) for i in ALT_INSTALLS]
    oggs = {m.install.lump: gws.ogg_bytes(m.wav) for m in done}
    (work_dir / "alt").mkdir(parents=True, exist_ok=True)
    for m in done:
        (work_dir / "alt" / f"{m.install.lump}.wav").write_bytes(m.wav)
        if asset_dir is not None:
            (asset_dir / f"{m.install.lump}.ogg").write_bytes(oggs[m.install.lump])
    text = alt_manifest_text(done, oggs)
    (work_dir / "alt" / "MANIFEST.txt").write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--install", action="store_true", help="also write the OGGs into assets/sounds/weapons/")
    ap.add_argument("--alts", action="store_true", help="the D94 alternatives instead (N9e)")
    ap.add_argument("names", nargs="*", help="only these lumps")
    args = ap.parse_args(argv)
    if args.alts:
        install_alts(ASSET_DIR if args.install else None)
        return 0
    if args.list:
        sys.stdout.write(plan_text())
        return 0
    bad = [n for n in args.names if n not in INSTALLS_BY_LUMP]
    if bad:
        print(f"not approved in D74 (or unknown): {', '.join(bad)}", file=sys.stderr)
        return 2
    done, skipped = build(args.names or None)
    for lump, why in skipped.items():
        print(f"skipped {lump}: {why}", file=sys.stderr)
    if skipped and args.install:
        print("refusing to install a partial set", file=sys.stderr)
        return 1
    write_outputs(done, WORK_DIR, ASSET_DIR if args.install else None)
    sys.stdout.write(manifest_text(done))
    return 0 if not skipped else 1


if __name__ == "__main__":
    sys.exit(main())
