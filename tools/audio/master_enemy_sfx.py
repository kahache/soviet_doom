#!/usr/bin/env python3
"""Master and install the enemy sounds the CEO approved (D83, D86; backlog N9e).

The weapon pass (`master_weapon_sfx.py`, N9w) is the model; this file reuses
its ruler, its limiter and its `master()` step and changes only what an
enemy needs. No re-synthesis: every recipe, seed and take belongs to the
generator that drew it, untouched:

  draft   the D83 OKs, the 2026-10-13 drafts of `gen_sfx.py` (seed 1977),
          rendered as that file renders them; 30 sounds and 5 beds (25
          sounds since D107 put real dogs in the hound's place: `--dogs`)
  alt     the D86 OKs, the alternatives of `gen_enemy_alts.py`, rendered as
          that file renders them (SDRRIATK alt2 with its final click
          lowered, as D86 asked; the fix is in `gen_enemy_alts.py`)

What happens to each, and nothing else:

1. **Target**: the Freedoom lump the game plays for that sound today (the
   placeholder in `src/lumps/SNDINFO` before N9e), measured from
   `iwads/freedoom2.wad` 0.13.0 with `gen_weapon_alts.py`'s ruler (loudest
   50 ms, A-weighted; `FREEDOOM_LOUD_A`, re-measured by the tests). A sound
   matches it (offset 0: it replaces it); a BED sits `BED_UNDER_VOICE_DB`
   under its voice's lump, as `gen_enemy_alts.py` levelled the bed
   alternatives (a voice goes on top, ENEMY-SOUNDS §5.10).
2. **Already in its window** (the D86 alternatives were levelled to these
   same targets for the CEO's page): left as it is, byte for byte (but for
   step 4). What the CEO approved is what ships.
3. Otherwise (the D83 drafts, levelled to `gen_sfx.py`'s class loudness,
   4-16 dB under Freedoom): `master_weapon_sfx.master()`, the weapons' pass:
   a gentle low shelf only for a bass-only sound, peak at -1 dBFS, gain
   down or the look-ahead limiter up to `MAX_LIMIT_DB` and make-up gain.
   No saturation. A sound the limiter cannot lift to its target (a thud
   with nothing above 1 kHz, a click in a 50 ms ruler) stops where more
   limiting stops paying and is pinned in `SHORT_OF_TARGET`.
4. **Codec check**: encoded and decoded, the OGG must peak under
   `DECODED_PEAK_CEILING_DBFS`; Vorbis lifts a dense, saturated sound well
   over its -1 dBFS master (the D86 alternatives up to +1.4 dBFS), so the
   limiter takes the master's ceiling down by the overshoot until it does
   (`CODEC_TRIMMED`; the only change to seven of the alternatives).
5. 16-bit WAV master (`work/audio/master_enemy/wav/`), then Vorbis OGG into
   `assets/sounds/enemies/<LUMP>.ogg` with `--install`, which the build
   packs as `sounds/<LUMP>.ogg`; `src/lumps/SNDINFO` maps the logical names.

Names (MOD-SPEC §6.2). A sound with one approved take ships under its card's
name (`SDSTOACT`). Where the CEO approved several takes of one sound (D86),
all ship and the game picks one (SNDINFO `$random`): the card's last letter
becomes the take number (`SDSTOPA1`-`SDSTOPA3`, the alternative's own
number). A bed is not its voice lump (`SDRRIDTH` stays the name of the
rifleman's death VOICE, which the bed will be mixed under, D87): it ships as
`SD` + actor + the event's initial + `B` + take (`SDRRIDB1`, `SDLTRPB1`-`3`),
aliased under `sd/bed/<actor>/<event>` and played by nothing yet: the beds
wait, packed, for the voice takes they go under (D87), as the D47 reloads
wait for a magazine.

Run:

    .venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --list
    .venv/Scripts/python.exe tools/audio/master_enemy_sfx.py            # masters + MANIFEST in work/
    .venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --install  # and the OGGs into assets/
    .venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --voices --install  # the voice takes of D91, D96, D110 and D118
    .venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --dogs --install    # the hound's dogs (D107)
    .venv/Scripts/python.exe -m unittest tests.test_enemy_sfx_install -v

Deterministic, as the weapon pass: the WAV masters are byte-identical run
to run on one machine; the OGGs depend on the local ffmpeg build, so an
installed sound is re-encoded only on the machine that installed it
(`INSTALLED_SHA256`).

GPL-3.0 (the script); its output CC BY-NC-SA 4.0 (D15), with the CC0
layers it mixes credited in `docs/art/LICENSES.md` and ENEMY-SOUNDS §5.9.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_enemy_alts as ea  # noqa: E402  (the D86 alternatives)
import gen_sfx as gs  # noqa: E402  (the D83 drafts)
import gen_weapon_alts as alts  # noqa: E402  (the ruler and the limiter)
import gen_weapon_sfx as gws  # noqa: E402  (WAV/OGG writers)
import master_weapon_sfx as mws  # noqa: E402  (the weapons' master step)

PROJECT_ROOT = gws.PROJECT_ROOT
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "enemies"
WORK_DIR = PROJECT_ROOT / "work" / "audio" / "master_enemy"
assert gs.SAMPLE_RATE == gws.SR == ea.SR

PEAK_DBFS = mws.PEAK_DBFS
LOUDNESS_TOLERANCE_DB = mws.LOUDNESS_TOLERANCE_DB
MAX_LIMIT_DB = mws.MAX_LIMIT_DB
SHORT_TOLERANCE_DB = mws.SHORT_TOLERANCE_DB
CODEC_LOUDNESS_DB = mws.CODEC_LOUDNESS_DB
DECODED_PEAK_CEILING_DBFS = mws.DECODED_PEAK_CEILING_DBFS
PEAK_SLACK_DB = 0.01
BED_UNDER_VOICE_DB = -ea.ALLOWANCE_DB["bed"]     # -3 dB: the voice goes on top

# Freedoom 0.13.0 lumps, measured with gen_weapon_alts.loud_a_db (loudest
# 50 ms, A-weighted, dB, at their own rates) from iwads/freedoom2.wad;
# tests/test_enemy_sfx_install.py re-measures them.
FREEDOOM_LOUD_A: dict[str, float] = {
    "DSSLOP": -11.56, "DSBGACT": -18.69, "DSBGSIT1": -10.96, "DSCLAW": -9.29,
    "DSFIRSHT": -15.90, "DSFIRXPL": -19.99, "DSDMACT": -12.90, "DSSGTSIT": -11.75,
    "DSSGTATK": -6.27, "DSDMPAIN": -11.72, "DSSGTDTH": -14.26, "DSCACSIT": -11.52,
    "DSCACDTH": -11.34, "DSKNTSIT": -9.48, "DSSKEPCH": -13.08, "DSKNTDTH": -8.86,
    "DSMETAL": -14.71, "DSRLAUNC": -14.24, "DSPODTH1": -10.60, "DSPOSACT": -28.63,
    "DSPOSIT2": -11.15, "DSCYBDTH": -11.26, "DSPOPAIN": -11.37, "DSPODTH2": -8.28,
    "DSPISTOL": -10.39, "DSDSHTGN": -7.94, "DSBGDTH1": -7.38, "DSPOSIT1": -10.12,
    "DSCYBSIT": -14.01, "DSVILSIT": -9.60,
}
FREEDOOM_TOLERANCE_DB = mws.FREEDOOM_TOLERANCE_DB


@dataclass(frozen=True)
class Install:
    lump: str            # the lump it ships as
    card: str            # its card in docs/sound/ENEMY-SOUNDS.md
    source: str          # "draft" (gen_sfx, D83), "bed" (gen_sfx bed, D83) or "alt" (gen_enemy_alts, D86)
    take: int            # the alternative's number (alt) or 1 (draft, bed: the only take)
    logical: str         # the SNDINFO name the lump gets
    group: str           # the name the game asks for ($random when several share it)
    ref: str             # the Freedoom lump the target is read from
    decision: str        # D83 / D86

    @property
    def bed(self) -> bool:
        return self.group.startswith("sd/bed/")

    @property
    def offset_db(self) -> float:
        return BED_UNDER_VOICE_DB if self.bed else 0.0

    @property
    def target_db(self) -> float:
        return FREEDOOM_LOUD_A[self.ref] + self.offset_db

    @property
    def draft_name(self) -> str:
        """The name its generator knows it by."""
        if self.source == "alt":
            return f"{self.card}_alt{self.take}"
        return f"{self.card}{gs.BED_SUFFIX}" if self.source == "bed" else self.card


ACTOR_KEY = {"RRI": "reichrifleman", "LTR": "legiontrooper", "STO": "stormtrooper", "HND": "reichhound",
             "DGB": "doughboy", "PZR": "panzermensch", "GEN": "general"}
EVENT_KEY = {"ACT": "active", "SIT": "sight", "ATK": "attack", "MEL": "melee", "MIS": "missile",
             "EXP": "explode", "PAI": "pain", "DTH": "death", "XDT": "xdeath", "STP": "step"}


def _sound(card: str, ref: str, decision: str = "D83") -> Install:
    logical = f"sd/mon/{ACTOR_KEY[card[2:5]]}/{EVENT_KEY[card[5:]]}"
    return Install(card, card, "draft", 1, logical, logical, ref, decision)


def _bed(card: str, ref: str, takes: tuple[int, ...] | None = None) -> list[Install]:
    group = f"sd/bed/{ACTOR_KEY[card[2:5]]}/{EVENT_KEY[card[5:]]}"
    stem = f"{card[:5]}{card[5]}B"
    if takes is None:       # the D83 draft, the only take
        return [Install(f"{stem}1", card, "bed", 1, group, group, ref, "D83")]
    return [Install(f"{stem}{n}", card, "alt", n, f"{group}/{n}", group, ref, "D86") for n in takes]


def _alts(card: str, ref: str, takes: tuple[int, ...]) -> list[Install]:
    group = f"sd/mon/{ACTOR_KEY[card[2:5]]}/{EVENT_KEY[card[5:]]}"
    if len(takes) == 1:
        return [Install(card, card, "alt", takes[0], group, group, ref, "D86")]
    return [Install(f"{card[:7]}{n}", card, "alt", n, f"{group}/{n}", group, ref, "D86") for n in takes]


# D83 (docs/PRD.md): 30 enemy sounds OK, each against the Freedoom lump
# SNDINFO played for it before N9e. The hound's five (SDHNDACT-SDHNDDTH)
# were retired by D107, which put real dogs in their place (DOG_INSTALLS):
# 25 remain.
D83_SOUNDS: tuple[tuple[str, str], ...] = (
    ("SDRRIXDT", "DSSLOP"), ("SDLTRXDT", "DSSLOP"),
    ("SDSTOACT", "DSBGACT"), ("SDSTOSIT", "DSBGSIT1"), ("SDSTOMEL", "DSCLAW"), ("SDSTOMIS", "DSFIRSHT"),
    ("SDSTOEXP", "DSFIRXPL"), ("SDSTOXDT", "DSSLOP"),
    ("SDDGBACT", "DSDMACT"), ("SDDGBSIT", "DSCACSIT"), ("SDDGBMEL", "DSCLAW"), ("SDDGBMIS", "DSFIRSHT"),
    ("SDDGBEXP", "DSFIRXPL"), ("SDDGBPAI", "DSDMPAIN"), ("SDDGBDTH", "DSCACDTH"),
    ("SDPZRACT", "DSDMACT"), ("SDPZRSIT", "DSKNTSIT"), ("SDPZRMEL", "DSSKEPCH"), ("SDPZRMIS", "DSFIRSHT"),
    ("SDPZREXP", "DSFIRXPL"), ("SDPZRDTH", "DSKNTDTH"), ("SDPZRSTP", "DSMETAL"),
    ("SDGENACT", "DSDMACT"), ("SDGENMIS", "DSRLAUNC"), ("SDGENEXP", "DSFIRXPL"),
)
# D83: five beds OK, each under the voice lump's Freedoom stand-in.
D83_BEDS: tuple[tuple[str, str], ...] = (
    ("SDRRIDTH", "DSPODTH1"), ("SDLTRACT", "DSPOSACT"), ("SDLTRSIT", "DSPOSIT2"),
    ("SDGENPAI", "DSDMPAIN"), ("SDGENDTH", "DSCYBDTH"),
)
# D86: the alternatives approved (SDRRIATK alt2 "once its final click is
# quieter than the first": FINAL_CLICK_DB in gen_enemy_alts.py).
D86_ALTS: tuple[tuple[str, str, tuple[int, ...]], ...] = (
    ("SDRRIATK", "DSPISTOL", (1, 2, 3)), ("SDLTRATK", "DSDSHTGN", (2,)),
    ("SDSTOPAI", "DSDMPAIN", (1, 2, 3)), ("SDSTODTH", "DSBGDTH1", (1, 2, 3)),
    ("SDPZRPAI", "DSDMPAIN", (1, 2, 3)),
)
D86_BEDS: tuple[tuple[str, str, tuple[int, ...]], ...] = (
    ("SDRRIPAI", "DSPOPAIN", (1, 2, 3)), ("SDLTRPAI", "DSPOPAIN", (1, 2, 3)),
    ("SDLTRDTH", "DSPODTH2", (1, 2, 3)),
)

INSTALLS: tuple[Install, ...] = tuple(
    [_sound(c, r) for c, r in D83_SOUNDS]
    + [i for c, r, t in D86_ALTS for i in _alts(c, r, t)]
    + [i for c, r in D83_BEDS for i in _bed(c, r)]
    + [i for c, r, t in D86_BEDS for i in _bed(c, r, t)])
INSTALLS_BY_LUMP = {i.lump: i for i in INSTALLS}

# Not installed (D83 NO and D86 NO): the rejected drafts and beds, and the
# Legion's shotgun alternatives 1 and 3. Their sounds keep Freedoom's lump
# (or, for a rejected draft whose alternative was approved, the alternative).
REJECTED_DRAFTS = ("SDRRIATK", "SDLTRATK", "SDSTOPAI", "SDSTODTH", "SDPZRPAI")
REJECTED_BEDS = ("SDRRIPAI", "SDLTRPAI", "SDLTRDTH")
REJECTED_ALTS = ("SDLTRATK_alt1", "SDLTRATK_alt3")

# Measured short of target (dB, the WAV master), at the pass's ceiling:
# written after the run, re-measured by the tests. WHY per lump in
# ENEMY-SOUNDS §5.12.
SHORT_OF_TARGET: dict[str, float] = {
    "SDSTOMEL": 4.7, "SDDGBACT": 3.9, "SDDGBMEL": 3.2, "SDDGBPAI": 1.4,
    "SDPZRSIT": 6.7, "SDPZRMEL": 3.5, "SDPZRDTH": 2.2, "SDPZRSTP": 3.1, "SDGENACT": 3.2,
    "SDSTODT3": 1.4,
}

# The lumps the codec check limited (dB taken off the master's peak so the
# decoded OGG stays under DECODED_PEAK_CEILING_DBFS): written after the
# run, re-measured by the tests. Every other D86 alternative ships byte for
# byte the OGG of the CEO's page.
CODEC_TRIMMED: dict[str, float] = {
    "SDRRIAT2": 0.5, "SDRRIAT3": 0.3, "SDLTRATK": 1.7, "SDSTOPA2": 0.7, "SDSTODT1": 0.4,
    "SDSTODT2": 1.0, "SDSTODT3": 1.6,
}

# SHA-256 of what is installed: (WAV master, OGG in assets/). Written by
# `--install`, pinned here by hand after review; the tests compare both.
INSTALLED_SHA256: dict[str, tuple[str, str]] = {
    "SDRRIXDT": ("d4ba799569f917ba95f1796ab911361c37d73b6107b04b7ea3f62b33ac2a0549",
                 "e8693e626bcca23d8c71406593374481461e849f52cc086709c7ea66033427b0"),
    "SDLTRXDT": ("ac87aece072979284e154e33636e9a2ca30d77785f631a310c7563b4a5695ae3",
                 "adb42dcef0f7b20a1be5970d007c29d0c3c622e016f54345125a2851571575d8"),
    "SDSTOACT": ("363f6f2fbf19b2218ae69cbf7bee9ab3f5a9f6f8f2beeb36a12f0bd0ce19200a",
                 "7bf1a9bbf726e4d5e52b954d072e0de19d3dc9f6e0b27c8726b66b3a1242e031"),
    "SDSTOSIT": ("bfeafee3d6d6d38bb26269637dca4d7ae3db1cb4276ffe982ddb26d686b76f3e",
                 "e845728a07056f511f89415bc366ac65f6c36c6ff0d94cc3231b02a2769e993a"),
    "SDSTOMEL": ("cf72caae57bc8f66b688a7091b8fdf587901aea597520fa3963425934ae1f5ad",
                 "cc6529bc5644bf6612ceab953355e3af02b87103e371cdb235e4997f0de7133a"),
    "SDSTOMIS": ("61dcf55e213a69cddd5a3850f065f8c41fda52453f26af0504f51edc08b32fb0",
                 "bf844aef30c8e3a6a90b5e1e2be7629902eb1ac63f3a907400cf08973f79091d"),
    "SDSTOEXP": ("ffe6b22ba8be4d524e513f2acf4c2e2f84ab34c628df7bfdf0a778251cb4c418",
                 "ae56a4300dc976d16bf6d28db4b00a41558ba14dc2c2982678266b6ebe2f4503"),
    "SDSTOXDT": ("85cb5cc027427ea886ea560e03bc2ad217ef202e01a505485fd53a2fc24dfdc6",
                 "080709cb8f1b7aa762fb00249f32b59a2959374bc68434bea5d384aa8a244865"),
    "SDDGBACT": ("7e94cc430a625b78a5f99235a19019f07130d9d43f72c3f23e6e28796cbe12bc",
                 "fec6c0e2c362aebc89165b397cb19a129a9ba7724c5e1f2487f4e82e22271346"),
    "SDDGBSIT": ("b7e7475bd5c3ca2fe69d0ee96ea106b03992ef8c59db22ce7b8c976da5cc2917",
                 "be7bdb3edfca6e034f770fc4b8836beb547b0c2d42311aac2d6bed7b41d518b2"),
    "SDDGBMEL": ("0d430d460f5449bdb8702438ffd25d993b332f268a2f2687106e8b2ea903dd5b",
                 "5ab45c9c4f105b9556e79b16c3e24db09679b3f99a4c93a261ed36b2a1c1e3dc"),
    "SDDGBMIS": ("65b69447fed3217dfe36d066b6adfffecb913a97412719335f9840909c9cb028",
                 "977598dbd0e94112639758476ee01627c8ed0a62c106bbb1a349e5faa0665e00"),
    "SDDGBEXP": ("65b8161438fcc654c63e8a3d236651730c23cfea8f4a6b1f9f2f6786b052b46a",
                 "9723a7459ab21429cea1a7f2d39cb0b34cf74fc4957c364ed459845ff3b02257"),
    "SDDGBPAI": ("556033abdc803b965a1927f6e305ea9cff6ac7ad3c862e3e2de3f5892bd50aa9",
                 "e284d65322a99bfb07377aa78914fa6b684deec01f43125b2b7a2e275daee35a"),
    "SDDGBDTH": ("b2de6b32110a79e4e1aaa2984950819657790d27955d564d911b503c48c242af",
                 "266a80432998c901e0651ad04ee02119e5b82ef427ba6fe63ba68ee9afcacf18"),
    "SDPZRACT": ("bef6def1becc11c1b68d95686d2068ce26a5bdb068afd3b12d261f87a9da4935",
                 "b39cebf99e571252fcdf5df5210e14bdcaf9e36c64e68226ad98759dfb286807"),
    "SDPZRSIT": ("4749338c615b6292f394238bd3ce9f9c8886657141cdb9090bd6a576da3acd21",
                 "94ad02e5d7e2a7e644d42b8727377fee3fde040cd7ec3e84d667dd71238f9449"),
    "SDPZRMEL": ("e61c687e0e5b8ac72f77ef5a1311b0f600336055d3509dbab7a7c9b45c0fb3f5",
                 "0ba3ad8992a3ec324b8d69f26a20f5c81133518a7fb18d9bd2f927c66eca2291"),
    "SDPZRMIS": ("4ce86e1aee869854ec40f4db529d1faabf64ba24e3004e9d1389f6c5eac31521",
                 "175411e473ba2e1951d6a080bc6403364cad9ea11c7fb1253b015207350bf6b0"),
    "SDPZREXP": ("dfa79c3fdb1edf5459da7d220ab0de71802a20bf42a87b8192bdc0056ecfc853",
                 "4cfc77bf46889642023acf2988b62e99c684b626b5500a462cbaccaf884edae4"),
    "SDPZRDTH": ("aeb3e60a5a9377dfefdb4d996b0837df90f39bb8150fcd081de41e2f78b83ffa",
                 "1f8e3ee6e5ccf24834ecc7481465b216180385c50f59e17696d7051ee26845cf"),
    "SDPZRSTP": ("64f24acbd46f1d9851e8bfa8c891b038c665c54bfb270dd21483e28ba99dcf49",
                 "62c0819c0f783c72ebd564d00f452976662e7f7935c99a896d98479598f242d0"),
    "SDGENACT": ("a2dbd44ec32d7578e6ffb3ed9b961810f49571676b7d63b54010d550c397cb61",
                 "f9e6cf0cb717220677e796a2e7e5c4eebd45b4b449afeadf5bf93cf4e6b47d8d"),
    "SDGENMIS": ("068593e58aa9e21e2a2d330a5df05691a686a46871f99dda607d009940c5ba90",
                 "2846d83a9267ef84b8d2d0d51afd73bfa1469cea51bc90f79cb4de5eaece788e"),
    "SDGENEXP": ("15c1bf6d5282056b59cbb316ab8de314929bc0809f86a7b2d9679eb8f0790e8d",
                 "98c8bbcff239bd7db7a160005ee312f5958de85c771757ba2dbb46f78bb1049a"),
    "SDRRIAT1": ("db54e1f9f6b3782262c3b6af10b3569ed85518b13acf0b68ec64ab2f2cad5e93",
                 "9b333ed596a8b30a66ecb6c281d4b672f8676d80b62c92dc53e2a1fb7c602953"),
    "SDRRIAT2": ("0ed4fe60440513f0dbc6846c43307928fcd95097f057115ca613054a72f23770",
                 "097a909a6849e3cfc9bbe8050f90b59e35e66630f011d714c05bcf5c1739ed8c"),
    "SDRRIAT3": ("9352f7463d64291aebab0eee0118fb700aa4a9f1520ff7fd013df8e3af27c8f4",
                 "589810e19523d29b2f0153bfbb7b6ff815d5f5e956a1920d8dc0933799069a71"),
    "SDLTRATK": ("0ecbc23400d6dafcf7504bdb20bf32187a9c86065c3dde4883b7ef7295e0c4f1",
                 "b8027da3f66cc94e99e8060bd4cc24b2e689b60f9528fe0c555c28437b4f2359"),
    "SDSTOPA1": ("73e4b2dfa57222befaf17d891fd872823b4bbfefd5a0c3191a362f2ae27831d6",
                 "84fe7d232e4b9e8d127246be6cc04e69f7fb7c295c40ce691247d15b486a3b06"),
    "SDSTOPA2": ("47f8b59bac9bf5b66757e2264cc06c9b3d04030b2474732e8cd0c9fe3fbe26b3",
                 "37ea2db8151f7dcb7020a98f5f7cc34f39ac2d18ceed295cc346e203d232f179"),
    "SDSTOPA3": ("3f4dc3450562377defd6741e43ca1d6d439ce71c454211d5454c917b87bc4d11",
                 "9e4b183ea79f0df236a734f7096ff0134931ba3ebbb653d5789c61b8904031bc"),
    "SDSTODT1": ("1cfa73fbb27ea21f8e4eda664df01e8a789267f98e4253a5bda79b11eb0d8d58",
                 "e9458fb00c0a996a2a7b696ca977703f6d006172de962feba4f2c0e85095bc9b"),
    "SDSTODT2": ("3e974f6dec11b2eb1d96ba578a2dbbb487e2a7cc013aa7070957512437d3fa02",
                 "abffe18f1f071d37521b845fee790744ee4d3e338c132717b853816ab60b521c"),
    "SDSTODT3": ("7d88822664590c726ddb727fedc609a534a51e7faa3c3f91d0ae14fe37e22712",
                 "031acd4243f917d8bf419c2aa72c4a483dc478827939316945761a4de32b3375"),
    "SDPZRPA1": ("9a8e87b2ee896d921c6e20f96e83d6db5bac90fa7eabb9de96aedf155d9f9500",
                 "4ed58a5d9dfefed6df1bf785aabd92e86e07460579adba01bf48b5ec71fa1223"),
    "SDPZRPA2": ("2d1f42d0fa403bc2379ea2a8eef387f260d79872d0404432015818d57cb26bb0",
                 "3b21a19b619a004e963042bdd713ff20907253be159f075310ea64e085df00d5"),
    "SDPZRPA3": ("07def89a1e2b27315888c4e7f0513db8d3e17e252d7ca8b28e5830e9ef313b0a",
                 "a5e1bf5482220e5157cd104f607c4722d8aaf05eb583792baa4d82e3601e15d9"),
    "SDRRIDB1": ("9522f694b74e244a4bc0a3db6e6a39e2e77bbe1a70de94dad5c99862a12f370b",
                 "f4c6c406f72e3e87c4a6377f184bfe7460cc25d89d137b76107c584797f89cd1"),
    "SDLTRAB1": ("438539c9958c3354f9b3837f3d4988c026dbe923ad337409a280d8ee78e81aff",
                 "2d8ee7917d4b5c41e2eabd56353ee3ac52db33a74a0cda48e7d58b7705040cf0"),
    "SDLTRSB1": ("36048db0d745230b076d39db45c1765b19452f72c88232c6f3b22b3db474224a",
                 "dd5ea43ac8b14678577da921d5de9e34b40c0d7c55cbcf8d22085eb3d5e84b8e"),
    "SDGENPB1": ("7f99843405a9045bbda6a44d3c3b9b4dd74d15ab5918d7916b1ad25412f3d854",
                 "11064ad61499ffa05f643f37782e8fcb268d0933f2a543d7a0adc652409771aa"),
    "SDGENDB1": ("5e141851482e4930954e92083917703dda1e7a0f22d432ef480046992ed42e89",
                 "301e2e38ac884a5eb3f7f0255bbde8a0849137b3cd163f4e596e16d81f84231f"),
    "SDRRIPB1": ("7970c3ce8486f16825355056beafaad1ae524395a717fdf4da1416f08d479141",
                 "6b070995908ac95d442b57fc794c3c28402ab17e792b3839cad484b3c8335375"),
    "SDRRIPB2": ("9062bbeb89c188771aab97704939ebcf56bc64a9c541db4b4fd38f329ca4e50f",
                 "534d1a706ab3b34e69c8c19bf9a8e1ee0c2380675f8fd34fab4f3e283eec4e13"),
    "SDRRIPB3": ("05238bc6d26a7a8db31e683774d232510bc6c9f292ebc294c34cf3d9e52d2ebc",
                 "b2547e903d3cdd2623699d5b2ef9976b0a9b1a2f002140cde83da13e4dac2e83"),
    "SDLTRPB1": ("6ff3aab059d1be2fd9d9323057b331820f09106ed55fcd4284543eaa453c4518",
                 "3e826792cc0ec5ff5593eb2c3a2e802a733ff9372344c990fdf932f43ab85f4d"),
    "SDLTRPB2": ("5d202942535e99fcf7fb23e9ee56b5e45188d446855929b2400f1814b49d2b05",
                 "39936f454d985b551242215dcc42cdfbd04245f523af67694d3dfbab8e249f75"),
    "SDLTRPB3": ("11f4bcdba0ef8d6c79096a71f5e908ee9488953cbee9f9def3e2df14aa5f4f74",
                 "17cea51ca9ca8692bdb14b9142fdd5d41b078408dfaf5295da4217ee15debfe7"),
    "SDLTRDB1": ("db4ae9f111a842b1e177193ba5e8a56b4e7b566897d50fe4a420c791e002f790",
                 "6b9cba1e526024640f774877954ede721183953c381d237a3a70606d757850db"),
    "SDLTRDB2": ("9b45b043beee329051461469e0979a9f78d2ee107e66b99d10bc84f6d402f7b9",
                 "8d51eb7b51991ea4c7fbc80b0ecbf7d4596647b15c254432d26f27d9a2c28e96"),
    "SDLTRDB3": ("d5d9200dc1bd2e68216651c02afc37d30a22b5cceeb7e1bb03eff7532d17383a",
                 "6eb6456a086b7dacd3ceeff657626082dbe61209ee00c2a52ff621ae219edbe1"),
}


# --- Mastering ---------------------------------------------------------------------

@dataclass
class Mastered:
    install: Install
    draft: np.ndarray        # as its generator renders it
    x: np.ndarray            # the master
    shelf_db: float
    limit_db: float
    gain_db: float
    untouched: bool          # already in its window and codec-safe: shipped as rendered
    reached: bool            # loudness within the window of its target
    codec_db: float = 0.0    # limiting added so the decoded OGG stays under DECODED_PEAK_CEILING_DBFS

    @property
    def wav(self) -> bytes:
        return gws.wav_bytes(self.x)


def in_window(x: np.ndarray, target_db: float) -> bool:
    return (abs(alts.loud_a_db(x) - target_db) <= LOUDNESS_TOLERANCE_DB
            and alts.peak_db(x) <= PEAK_DBFS + PEAK_SLACK_DB)


# Vorbis lifts a dense, saturated transient over its -1 dBFS master: the D86
# alternatives decoded up to +1.4 dBFS (SDLTRATK), a clip in any 16-bit
# path. After the master, each sound is encoded and decoded; while the
# decoded peak reaches DECODED_PEAK_CEILING_DBFS, the look-ahead limiter
# takes the master's ceiling down by the overshoot plus CODEC_MARGIN_DB (a
# change of the transients' peak, not of the level: the loudness window is
# re-checked by the tests). A sound that needs none ships as it was.
CODEC_MARGIN_DB = 0.2
CODEC_PASSES = 6


def decoded_peak_db(ogg: bytes) -> float:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.ogg"
        path.write_bytes(ogg)
        return alts.peak_db(gws.decode(path))


def codec_safe(m: Mastered) -> Mastered:
    base, depth = m.x, 0.0
    for _ in range(CODEC_PASSES):
        over = decoded_peak_db(ogg_of(m)) - DECODED_PEAK_CEILING_DBFS
        if over < 0:
            return m
        depth += over + CODEC_MARGIN_DB
        x = alts.limit(base, 10 ** ((alts.peak_db(base) - depth) / 20))
        reached = abs(alts.loud_a_db(x) - m.install.target_db) <= LOUDNESS_TOLERANCE_DB
        m = Mastered(m.install, m.draft, x, m.shelf_db, m.limit_db, m.gain_db, False,
                     reached if m.reached else False, depth)
    raise RuntimeError(f"{m.install.lump}: the OGG still overshoots after {CODEC_PASSES} passes")


def master(install: Install, draft: np.ndarray) -> Mastered:
    if in_window(draft, install.target_db):
        return codec_safe(Mastered(install, draft, draft, 0.0, 0.0, 0.0, True, True))
    m = mws.master(install, draft)          # duck-typed: it reads install.target_db only
    return codec_safe(Mastered(install, draft, m.x, m.shelf_db, m.limit_db, m.gain_db, False, m.reached))


def render_draft(install: Install) -> np.ndarray:
    """The approved take as its generator renders it."""
    if install.source == "alt":
        if install.draft_name in REJECTED_ALTS:
            raise ValueError(f"{install.draft_name} is not approved (D86)")
        return ea.render(ea.ALTS_BY_NAME[install.draft_name])[0]
    if install.card in (REJECTED_BEDS if install.source == "bed" else REJECTED_DRAFTS):
        raise ValueError(f"{install.draft_name} is not approved (D83)")
    return gs.render(install.draft_name).samples


def build(names=None) -> tuple[list[Mastered], dict[str, str]]:
    done, skipped = [], {}
    for inst in INSTALLS:
        if names and inst.lump not in names:
            continue
        try:
            done.append(master(inst, render_draft(inst)))
        except (gs.SourceMissing, gws.MissingSource) as exc:
            skipped[inst.lump] = str(exc)
    return done, skipped


# --- SNDINFO ---------------------------------------------------------------------------

def groups() -> dict[str, list[Install]]:
    """The name the game asks for -> its takes, in order."""
    out: dict[str, list[Install]] = {}
    for i in INSTALLS:
        out.setdefault(i.group, []).append(i)
    return out


def random_groups() -> dict[str, list[str]]:
    """The $random aliases: group -> its member names (ZDoom wiki SNDINFO; the
    syntax as gzdoom.pk3's own `$random grunt/sight { grunt/sight1 ... }`)."""
    return {g: [i.logical for i in takes] for g, takes in groups().items() if len(takes) > 1}


# --- Reports and outputs -------------------------------------------------------------

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_text(done: list[Mastered], oggs: dict[str, bytes] | None = None) -> str:
    lines = ["# master_enemy_sfx.py (N9e, D83, D86): the approved enemy sounds, before and after",
             "# loudA = loudest 50 ms, A-weighted, dB (gen_weapon_alts.py's ruler); >300 = energy share",
             "# untouched = already in its window (the D86 alternatives); else shelf/limit/gain as the weapons'",
             ""]
    for name, v in FREEDOOM_LOUD_A.items():
        lines.append(f"{name:9s} Freedoom loudA {v:6.2f}")
    lines.append("")
    for m in done:
        i = m.install
        b, a = alts.levels(m.draft), alts.levels(m.x)
        state = ("untouched" if m.untouched else
                 f"shelf {m.shelf_db:3.1f} dB  limit {m.limit_db:4.1f} dB  gain {m.gain_db:5.1f} dB")
        if m.codec_db:
            state += f"  codec {m.codec_db:3.1f} dB"
        row = (f"{i.lump} {i.decision} {i.draft_name:15s} target {i.target_db:6.1f} ({i.ref} {i.offset_db:+.0f})  "
               f"before peak {b['peak']:5.1f} loudA {b['loud_a']:6.1f} >300 {100 * b['above300']:3.0f} %  "
               f"after peak {a['peak']:5.1f} loudA {a['loud_a']:6.1f} >300 {100 * a['above300']:3.0f} %  "
               f"{state}  "
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
    rows = [f"{i.lump}  {i.decision} {i.draft_name:15s} {i.logical:34s} target {i.target_db:6.1f} dB A "
            f"({i.ref} {i.offset_db:+.0f})" for i in INSTALLS]
    beds = sum(1 for i in INSTALLS if i.bed)
    rows.append(f"{len(INSTALLS)} approved (D83, D86): {len(INSTALLS) - beds} sounds, {beds} beds; "
                f"{len(random_groups())} $random groups; not installed: "
                + ", ".join(REJECTED_DRAFTS + tuple(f"{b}-bed" for b in REJECTED_BEDS) + REJECTED_ALTS))
    return "\n".join(rows) + "\n"


# --- D91: the seven approved voice takes (Chatterbox, D87) --------------------------
# docs/art/previews/2026-10-20_1135_P2_voice-takes.html. OK: R06 t01, t03
# ("Kontakt!", the rifleman's sight) and L01 t01, t03, L02 t01-t03 ("Sector
# four, clear." and "Copy. Holding position.", the trooper's idle radio
# chatter); every other take NO (D91). They were processed and levelled to
# the Freedoom lump of their sound by tools/audio/process_voice_takes.py,
# and ship as those OGGs, byte for byte: the raw Chatterbox output is not
# reproducible here without the server, so nothing is re-encoded. The pass
# only checks them: decoded peak under DECODED_PEAK_CEILING_DBFS and
# loudness in its window. Lumps: the card's 7 letters plus a take number
# (R06's own t01/t03; the trooper's five numbered 1-5 in this order). The
# trooper's idle bed (SDLTRAB1) stays parked: mixing it under the voice is
# not approved yet.
VOICE_DIR = PROJECT_ROOT / "work" / "audio" / "voice_takes"
VOICE_DAY = "20261020"
# --- D96: seventeen takes of the aggressive round ----------------------------------
# docs/art/previews/2026-10-20_1330_P2_voice-takes-aggressive.html, 40/40 judged.
# OK: R01 t13, R02 t11, R03 t14 (the rifleman's idle), R04 t12+t13, R05 t12
# (his sight, beside D91's R06), R09 t12 (his death), L03 t12 (the trooper's
# idle, beside D91's L01/L02), L04 t12+t14, L05 t13, L06 t13 (his sight), L08
# t14+t15 (his pain), G01 t12 (the General's sight), G02 t13+t14 (his order,
# "Vorwärts!"). Cloned from shouted references (AI-LOG.csv, column voz:
# Thorsten-Voice "angry" CC0, kurt's "Soldier Voice Acting" CC-BY 3.0, HaelDB
# CC0; the references are not distributed), processed by
# process_voice_takes.py into VOICE_AGGRESSIVE_DIR. All ship byte for byte but
# one: G02 t13 decodes to -0.02 dBFS, so it gets the codec pass the D83/D86
# sounds got (codec_safe's loop on its master, which
# process_voice_takes.process_wave re-renders byte-identically from the raw
# take): VOICE_CODEC_TRIMMED. Names: a sound with one approved take ships under
# its card's name (SDRRIDTH, SDGENSIT); several are a $random group, the card's
# 7 letters plus the member number, numbered on after D91's (the rifleman's
# sight 4-6 beside R06's 1 and 3, the trooper's idle 6).
VOICE_AGGRESSIVE_DIR = VOICE_DIR / "aggressive"
# --- D110: seven takes of the P2 round (the wordless voices) -------------------------
# work/audio/preview/voices_p2_listening.html (gen_p2.py, page_p2.py). OK: R07
# t06+t02 (the rifleman's pain, "Argh!"; t05 NO), L09 t01+t02 and t04 once its
# tail is cut (the trooper's death), G03 t06+t04 (the General's pain; t03 NO);
# G04 (the General's death) all NO, redrafted in voice_takes/p2b/. Chatterbox
# Multilingual on the CPU (the server's own Python, special tokens dropped),
# cloned from the D96 references: Thorsten "angry" CC0 (R07 t06), HaelDB CC0
# (R07 t02, L09 t04), kurt's "Soldier Voice Acting" CC-BY 3.0 (wounded.ogg and
# battlecries.ogg: L09 t01, t02, G03 t04, t06). Processed by gen_p2.py with
# process_voice_takes.process_wave and levelled to the Freedoom lump they
# replace; all ship byte for byte but L09 t04, VOICE_TAIL_CUT. Every sound has
# several takes: $random groups, the card's 7 letters plus the member number in
# the CEO's order (SDRRIPA1 = R07 t06, SDLTRDT3 = L09 t04, SDGENPA1 = G03 t06);
# the beds' lumps are ...B<n>, so no name is shared.
VOICE_P2_DIR = VOICE_DIR / "p2"
# --- D118: five takes of the P2b round (the General's death) ------------------------
# work/audio/preview/voices_p2b_listening.html (gen_p2b.py, page_p2b.py): G04
# redrafted after D110's all-NO. OK t01, t07, t08, t05, t12; NO t10, t03, t04.
# Chatterbox Multilingual on the CPU as D110, cloned from kurt's "Soldier Voice
# Acting" (CC-BY 3.0): wounded.ogg + battlecries.ogg (t01, t07, t08) or
# battlecries.ogg alone (t05, t12). Processed by gen_p2b.py with
# process_voice_takes (t01 and t05: the junk after a long gap cut there, as the
# page played them) and levelled to DSCYBDTH, the Freedoom lump they replace.
# All five ship byte for byte as the page's OGGs; a $random group in the CEO's
# order (SDGENDT1 = t01 ... SDGENDT5 = t12). The bed stays SDGENDB1 (parked).
VOICE_P2B_DIR = VOICE_DIR / "p2b"
VOICE_DAYS = {"D91": VOICE_DAY, "D96": VOICE_DAY, "D110": "20261021", "D118": "20261022"}


@dataclass(frozen=True)
class VoiceInstall:
    lump: str
    take: str            # the processed file's stem in its folder
    logical: str
    group: str           # the name the game asks for ($random when several share it)
    ref: str
    decision: str = "D91"

    @property
    def target_db(self) -> float:
        return FREEDOOM_LOUD_A[self.ref]

    @property
    def folder(self) -> Path:
        return {"D91": VOICE_DIR, "D96": VOICE_AGGRESSIVE_DIR, "D110": VOICE_P2_DIR,
                "D118": VOICE_P2B_DIR}[self.decision]

    @property
    def path(self) -> Path:
        return self.folder / f"{self.take}.ogg"

    @property
    def raw_path(self) -> Path:
        return self.folder / "raw" / f"{self.take}.wav"


def _voice(lump: str, line: str, card: str, take: int, logical: str, n: int | None, ref: str,
           decision: str = "D91") -> VoiceInstall:
    """n None: the sound's only take, under the logical name itself (no $random)."""
    name = logical if n is None else f"{logical}/{n}"
    return VoiceInstall(lump, f"{line}_{card}_ai_chatterbox_{VOICE_DAYS[decision]}_t{take:02d}", name, logical,
                        ref, decision)


_RR, _LT, _GN = "sd/mon/reichrifleman", "sd/mon/legiontrooper", "sd/mon/general"
VOICE_INSTALLS: tuple[VoiceInstall, ...] = (
    _voice("SDRRISI1", "R06", "SDRRISIT", 1, f"{_RR}/sight", 1, "DSPOSIT1"),
    _voice("SDRRISI3", "R06", "SDRRISIT", 3, f"{_RR}/sight", 3, "DSPOSIT1"),
    _voice("SDLTRAC1", "L01", "SDLTRACT", 1, f"{_LT}/active", 1, "DSPOSACT"),
    _voice("SDLTRAC2", "L01", "SDLTRACT", 3, f"{_LT}/active", 2, "DSPOSACT"),
    _voice("SDLTRAC3", "L02", "SDLTRACT", 1, f"{_LT}/active", 3, "DSPOSACT"),
    _voice("SDLTRAC4", "L02", "SDLTRACT", 2, f"{_LT}/active", 4, "DSPOSACT"),
    _voice("SDLTRAC5", "L02", "SDLTRACT", 3, f"{_LT}/active", 5, "DSPOSACT"),
    # D96
    _voice("SDRRIAC1", "R01", "SDRRIACT", 13, f"{_RR}/active", 1, "DSPOSACT", "D96"),
    _voice("SDRRIAC2", "R02", "SDRRIACT", 11, f"{_RR}/active", 2, "DSPOSACT", "D96"),
    _voice("SDRRIAC3", "R03", "SDRRIACT", 14, f"{_RR}/active", 3, "DSPOSACT", "D96"),
    _voice("SDRRISI4", "R04", "SDRRISIT", 12, f"{_RR}/sight", 4, "DSPOSIT1", "D96"),
    _voice("SDRRISI5", "R04", "SDRRISIT", 13, f"{_RR}/sight", 5, "DSPOSIT1", "D96"),
    _voice("SDRRISI6", "R05", "SDRRISIT", 12, f"{_RR}/sight", 6, "DSPOSIT1", "D96"),
    _voice("SDRRIDTH", "R09", "SDRRIDTH", 12, f"{_RR}/death", None, "DSPODTH1", "D96"),
    _voice("SDLTRAC6", "L03", "SDLTRACT", 12, f"{_LT}/active", 6, "DSPOSACT", "D96"),
    _voice("SDLTRSI1", "L04", "SDLTRSIT", 12, f"{_LT}/sight", 1, "DSPOSIT2", "D96"),
    _voice("SDLTRSI2", "L04", "SDLTRSIT", 14, f"{_LT}/sight", 2, "DSPOSIT2", "D96"),
    _voice("SDLTRSI3", "L05", "SDLTRSIT", 13, f"{_LT}/sight", 3, "DSPOSIT2", "D96"),
    _voice("SDLTRSI4", "L06", "SDLTRSIT", 13, f"{_LT}/sight", 4, "DSPOSIT2", "D96"),
    _voice("SDLTRPA1", "L08", "SDLTRPAI", 14, f"{_LT}/pain", 1, "DSPOPAIN", "D96"),
    _voice("SDLTRPA2", "L08", "SDLTRPAI", 15, f"{_LT}/pain", 2, "DSPOPAIN", "D96"),
    _voice("SDGENSIT", "G01", "SDGENSIT", 12, f"{_GN}/sight", None, "DSCYBSIT", "D96"),
    _voice("SDGENSU1", "G02", "SDGENSUM", 13, f"{_GN}/summon", 1, "DSVILSIT", "D96"),
    _voice("SDGENSU2", "G02", "SDGENSUM", 14, f"{_GN}/summon", 2, "DSVILSIT", "D96"),
    # D110
    _voice("SDRRIPA1", "R07", "SDRRIPAI", 6, f"{_RR}/pain", 1, "DSPOPAIN", "D110"),
    _voice("SDRRIPA2", "R07", "SDRRIPAI", 2, f"{_RR}/pain", 2, "DSPOPAIN", "D110"),
    _voice("SDLTRDT1", "L09", "SDLTRDTH", 1, f"{_LT}/death", 1, "DSPODTH2", "D110"),
    _voice("SDLTRDT2", "L09", "SDLTRDTH", 2, f"{_LT}/death", 2, "DSPODTH2", "D110"),
    _voice("SDLTRDT3", "L09", "SDLTRDTH", 4, f"{_LT}/death", 3, "DSPODTH2", "D110"),
    _voice("SDGENPA1", "G03", "SDGENPAI", 6, f"{_GN}/pain", 1, "DSDMPAIN", "D110"),
    _voice("SDGENPA2", "G03", "SDGENPAI", 4, f"{_GN}/pain", 2, "DSDMPAIN", "D110"),
    # D118
    _voice("SDGENDT1", "G04", "SDGENDTH", 1, f"{_GN}/death", 1, "DSCYBDTH", "D118"),
    _voice("SDGENDT2", "G04", "SDGENDTH", 7, f"{_GN}/death", 2, "DSCYBDTH", "D118"),
    _voice("SDGENDT3", "G04", "SDGENDTH", 8, f"{_GN}/death", 3, "DSCYBDTH", "D118"),
    _voice("SDGENDT4", "G04", "SDGENDTH", 5, f"{_GN}/death", 4, "DSCYBDTH", "D118"),
    _voice("SDGENDT5", "G04", "SDGENDTH", 12, f"{_GN}/death", 5, "DSCYBDTH", "D118"),
)
VOICES_BY_LUMP = {v.lump: v for v in VOICE_INSTALLS}
# dB the codec pass took off a voice take's master peak (codec_safe's loop and margin).
VOICE_CODEC_TRIMMED: dict[str, float] = {"SDGENSU1": 0.6}
# D110: "has cortado mal el audio, se cuela algo al final" ("you cut the audio
# badly, something slips in at the end") (L09 t04). The raw take
# has the cry, 0.22 s of digital silence (1.17-1.39 s) and then a 0.08 s blip at
# -11 dB; process_voice_takes.trim only ends a line after a gap of MAX_GAP_S
# (0.45 s), so the blip stayed. The raw take is cut here, in seconds, before the
# blip, and processed as gen_p2.py processed it (voice_tail_cut_ogg).
VOICE_TAIL_CUT: dict[str, float] = {"SDLTRDT3": 1.20}
# SHA-256 of each installed OGG (= the processed take in its folder, but for the trimmed and the tail-cut).
VOICE_SHA256: dict[str, str] = {
    "SDRRISI1": "dd56db85f651faf912cf09031daa4f5a726455d03758531c809584f1b1e1ef18",
    "SDRRISI3": "9b8063c21dd9caa51f87562ae28de2a7eacdbffb002ce2944cf38cfe8fa7be2b",
    "SDLTRAC1": "45132e6973126e320508b2373995ccf12ac316f90d8672287f2a9cfa18316d82",
    "SDLTRAC2": "4ac94a6ee67c10db212f26d4fffff0e0775c0ac4731da6b083a47f5194ec68d9",
    "SDLTRAC3": "143887b4851dda474433f5ba465b963677ed33675eb9f9f09236b266a059f825",
    "SDLTRAC4": "c2c02cded81348a5a8264a1c0d42a7532e410145e4184572d178b4654ff7f4c6",
    "SDLTRAC5": "5acad54da26ab55e5fe929c8c8a42e6c46240a5c6d290a4b572b41aaf1656a16",
    # D96
    "SDRRIAC1": "5d34cb6f1e99f8ad4bfd315029f59eb59a6e7351ea1fe3e3f1b3878577f61be7",
    "SDRRIAC2": "18b440aa6fa0206097308acc0dfcba3668c0f7d0ded32cc7fff14a2405738a6c",
    "SDRRIAC3": "56ceff7ffae58567fbe8bf41be4d43f2858d219cb8ff3b284111222ebbb18b80",
    "SDRRISI4": "fa100a4f8e29167ab3be76651c42b14671a86f47f7ee68fb223deb71589f7089",
    "SDRRISI5": "a352944e75d086f9a789d9fcf6f539e2a30c29a13a4da6285f205ac0cc4aa552",
    "SDRRISI6": "ac6d58699d67c41b2988344f133f8cfa3a2cfa6be79fb103b7cad85c5653a019",
    "SDRRIDTH": "9de406901cec90a6d6b8f03080ad750c4feaa9651e0550530206e1d89d1552fa",
    "SDLTRAC6": "a7c20685c41a9b9314ae16e05eadc6424fe77098e7c2dc6802b57af00bf95593",
    "SDLTRSI1": "0b5ab35624419e5d91b9d32186c878f7ce00d0696dab8ff5e6fbc0c2b047c1ad",
    "SDLTRSI2": "0fdf1676b4b23efe2b5b6090be356d43a8b9ae62c8c60d7d5af1025579085f62",
    "SDLTRSI3": "cc1fd41c09113e96607edce43b7e9906a17c7b2f1e92e1e7ccd6f33b26ea4438",
    "SDLTRSI4": "815ab1a72ec0842a411f96ab484be3e56693a54727640b171e8d27a5039d6ffa",
    "SDLTRPA1": "2f4b26a5e4632a90ce8b8e3bb62915d2c17567e7fc28154b656574c5fb436bee",
    "SDLTRPA2": "249b167901c1122321c5dca0af756f15fe74c8310b372ae91928ce7b86733531",
    "SDGENSIT": "99669afd3d20cc603180f4d572694ddef781f2a4ace19e4927991c36ca9154dc",
    "SDGENSU1": "10184bed9a802498928bd273d5e8b47a80c6fb1764b632a7b2aef014cf6a7785",
    "SDGENSU2": "31d103bb6d541c19090f577a01292ec7e701950139d75bdaedc059dfe2dfea87",
    # D110
    "SDRRIPA1": "7f9c6bd1c66f5168291187048da86c5532f1656766ff47084795308449eef58f",
    "SDRRIPA2": "f9679ad86ca6e38be275c1f57b3f4ea1d3fa6cd405e80a3daa5b0874bf65aa25",
    "SDLTRDT1": "bf926b27325553784457c312f086ee3503a853ea8c8f914e0d05c5144adb9b16",
    "SDLTRDT2": "015ece147d92c6a80ef03f87d6ebe9967206560d5079d29279b1e600bb8ab592",
    "SDLTRDT3": "092c8c7d40763d74f171b796832df009a58f0424bd351d23312580802eae935c",
    "SDGENPA1": "d6025787d6b86ca32f89a953576a443c33880197dc67edddf8a7f2e48948a570",
    "SDGENPA2": "4ed7fc422994149fffd20f994b824543fb900f188f35c53b9924517ee79be1ad",
    # D118
    "SDGENDT1": "e6f27e5e9a4571eb2b898bbc1ff764619443bb8b5f3c0d460108a09d85534e67",
    "SDGENDT2": "b9ed883e6ee645187b86151aefb06849a174ecedbeed6e15c4554071fe3cea9c",
    "SDGENDT3": "0b93f029ae3accef66bb192eef1c486335bd3c3bedee3da17914c6aeefe28085",
    "SDGENDT4": "564a603043146f6526afd9746c0e5e8fd67f09eff2a5e3a5f2b81817a0c74eee",
    "SDGENDT5": "ef093366d886a14049f25d362bf55f9061dd592963a81f02c518b4f736f61cc6",
}


def voice_groups() -> dict[str, list[str]]:
    """$random alias -> its members' logical names, for the sounds with several voice takes."""
    out: dict[str, list[str]] = {}
    for v in VOICE_INSTALLS:
        if v.logical != v.group:
            out.setdefault(v.group, []).append(v.logical)
    return out


def _decode_ogg(ogg: bytes) -> np.ndarray:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.ogg"
        path.write_bytes(ogg)
        return gws.decode(path)


def voice_trimmed_ogg(v: VoiceInstall) -> tuple[bytes, float]:
    """The codec pass on a voice take: its master re-rendered from the raw take by
    process_voice_takes.process_wave, then codec_safe's loop. -> (OGG, dB taken off)."""
    import process_voice_takes as pvt
    base, _, _ = pvt.process_wave(gws.decode(v.raw_path), pvt.line_of(v.raw_path.name))
    x, depth = base, 0.0
    for _ in range(CODEC_PASSES):
        ogg = gws.ogg_bytes(gws.wav_bytes(x))
        over = decoded_peak_db(ogg) - DECODED_PEAK_CEILING_DBFS
        if over < 0:
            return ogg, depth
        depth += over + CODEC_MARGIN_DB
        x = alts.limit(base, 10 ** ((alts.peak_db(base) - depth) / 20))
    raise RuntimeError(f"{v.lump}: the OGG still overshoots after {CODEC_PASSES} passes")


def voice_render(v: VoiceInstall, cut_s: float | None = None) -> np.ndarray:
    """process_voice_takes.process_wave's chain on the raw take, the target given (the
    wordless rows of D110 have no Line there): high-pass, trim, the trooper's radio
    colour, level to the Freedoom lump, the last samples silent. cut_s: the raw take
    ends there first."""
    import process_voice_takes as pvt
    x = gws.decode(v.raw_path)
    if cut_s is not None:
        x = x[:int(round(cut_s * gws.SR))]
    y, _ = pvt.trim(pvt.high_pass(x), gws.SR)
    if v.logical.startswith(_LT + "/"):
        y = pvt.radio_colour(y)
    y, _ = pvt.level(y, v.target_db)
    y[-gws.n_of(pvt.TAIL_SILENCE_S):] = 0.0
    return y


def voice_tail_cut_ogg(v: VoiceInstall) -> bytes:
    """A take whose raw tail is cut (VOICE_TAIL_CUT), rendered as its page's OGG was."""
    return gws.ogg_bytes(gws.wav_bytes(voice_render(v, VOICE_TAIL_CUT[v.lump])))


def voice_ogg(v: VoiceInstall) -> bytes:
    """The OGG a voice take ships as: the processed take, or its codec-trimmed or tail-cut render."""
    if v.lump in VOICE_CODEC_TRIMMED:
        return voice_trimmed_ogg(v)[0]
    if v.lump in VOICE_TAIL_CUT:
        return voice_tail_cut_ogg(v)
    return v.path.read_bytes()


def voice_check(v: VoiceInstall, ogg: bytes | None = None) -> tuple[float, float]:
    """-> (decoded peak dBFS, loudest 50 ms A); raises if either is off."""
    x = gws.decode(v.path) if ogg is None else _decode_ogg(ogg)
    peak, loud = alts.peak_db(x), alts.loud_a_db(x)
    if peak >= DECODED_PEAK_CEILING_DBFS or abs(loud - v.target_db) > LOUDNESS_TOLERANCE_DB + CODEC_LOUDNESS_DB:
        raise ValueError(f"{v.take}: peak {peak:.2f} dBFS, {loud:.2f} dB A against {v.target_db:.2f}")
    return peak, loud


def install_voices(asset_dir: Path | None, lumps=None) -> dict[str, str]:
    out = {}
    for v in VOICE_INSTALLS:
        if lumps and v.lump not in lumps:
            continue
        data = voice_ogg(v)
        peak, loud = voice_check(v, data)
        out[v.lump] = sha256(data)
        if asset_dir is not None:
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / f"{v.lump}.ogg").write_bytes(data)
        print(f"{v.lump} {v.take} {v.logical:32s} peak {peak:5.2f} loudA {loud:6.2f} "
              f"(target {v.target_db:6.2f}, {v.ref})  ogg {out[v.lump]}")
    return out


# --- D107: the Reich hound's real dogs ------------------------------------------------
# work/audio/preview/dog_listening.html: five sounds x three candidates, built
# by work/audio/candidates/dog/make_dog_candidates.py from recordings of real
# dogs (BigSoundBank, Joseph Sardin, CC0; OpenGameArt: qubodup and pauliuw,
# CC0, congusbongus after juskiddink, CC BY 3.0; two Kenney CC0 clips already
# on disk; sources, licences and hashes in work/audio/sfx_sources/dog/SOURCES.md)
# and levelled there to the Freedoom lump of their sound, as the D86
# alternatives were. The CEO approved all fifteen ("TODOS OK"); the PM ships
# the three takes of each sound as a $random group (D107, as D94). They
# replace D83's synthetic SDHNDACT-SDHNDDTH. Each ships byte for byte as the
# page's OGG; the pass only checks it (decoded peak under
# DECODED_PEAK_CEILING_DBFS, loudness in its window), as for the voices.
# Lumps: the card's 7 letters with its last letter replaced by the take
# number, as the D86 groups (SDHNDAC1-3, SDHNDSI1-3, SDHNDAT1-3, SDHNDPA1-3,
# SDHNDDT1-3).
DOG_DIR = PROJECT_ROOT / "work" / "audio" / "candidates" / "dog"


@dataclass(frozen=True)
class DogInstall:
    lump: str
    candidate: str       # the page's file stem in DOG_DIR
    logical: str
    group: str           # the name the game asks for ($random over the three)
    ref: str
    decision: str = "D107"

    @property
    def target_db(self) -> float:
        return FREEDOOM_LOUD_A[self.ref]

    @property
    def path(self) -> Path:
        return DOG_DIR / f"{self.candidate}.ogg"


# card -> (its D107 lump stem, the Freedoom lump it was levelled to)
_DOG_CARDS: tuple[tuple[str, str, str], ...] = (
    ("SDHNDACT", "SDHNDAC", "DSDMACT"), ("SDHNDSIT", "SDHNDSI", "DSSGTSIT"),
    ("SDHNDATK", "SDHNDAT", "DSSGTATK"), ("SDHNDPAI", "SDHNDPA", "DSDMPAIN"),
    ("SDHNDDTH", "SDHNDDT", "DSSGTDTH"),
)
DOG_INSTALLS: tuple[DogInstall, ...] = tuple(
    DogInstall(f"{stem}{n}", f"{card}_dog{n}",
               f"sd/mon/reichhound/{EVENT_KEY[card[5:]]}/{n}", f"sd/mon/reichhound/{EVENT_KEY[card[5:]]}", ref)
    for card, stem, ref in _DOG_CARDS for n in (1, 2, 3))
DOGS_BY_LUMP = {d.lump: d for d in DOG_INSTALLS}
# The take the page recommended per sound (by measurement, not by ear); all ship.
DOG_RECOMMENDED = ("SDHNDAC1", "SDHNDSI2", "SDHNDAT1", "SDHNDPA1", "SDHNDDT2")
# SHA-256 of each installed OGG (= the page's candidate, byte for byte).
DOG_SHA256: dict[str, str] = {
    "SDHNDAC1": "6950d36709683616c0e57694baf22dbaf3a7e4ddef4e0854356f98ae25be6ca9",
    "SDHNDAC2": "e3f737f9f614c3bf708c0210e14fcf24dd3b037f3a8466ff871dd2fa72f0ed2d",
    "SDHNDAC3": "0c18ad0cc69afda409c56e9b83e16087e0fb58235621ca0273c422dea196ccad",
    "SDHNDSI1": "90f10758b6019d250fd88ba222ee76f949db0497952a040830ba397270ae13f2",
    "SDHNDSI2": "370cf96c6f42e7d14a5c956414df03fd704070d1c601d43e77aa1183bb469f22",
    "SDHNDSI3": "46e478093a5c547b74eb45acb462f146b5d7d7eee2c6b808b879243e2453aff8",
    "SDHNDAT1": "78f7f51620043d4947ab698afe5f2ef8a2469b5914360794392c942fe9797589",
    "SDHNDAT2": "835c00bdc30ff223e008c058136d531af7c719f9bf240015695eb23bef332a43",
    "SDHNDAT3": "e385fa91be42551964f9bf606c3902e18c7cae0f3d33b1b29245e5f185094ae2",
    "SDHNDPA1": "c2ad1d6ba82b8a8232c86a980a9a63fd91e7279fc5878096db397f98661b8046",
    "SDHNDPA2": "ad58d480f9c2aef8fa7883600948afb018c8f24d5d92a59a1ae4ab1592bac149",
    "SDHNDPA3": "a8767b25f821818cad7593347734c63a49e75df209c57a60399c2ed706865777",
    "SDHNDDT1": "4c85b6e34050f8f52569568b2457cf50d0b311aef059c2d5f64a043db8429f83",
    "SDHNDDT2": "f97a3f619f510e1f8db8f64af8d0fea53ac968e4fb5e7440351a249331b4fefb",
    "SDHNDDT3": "8116e8e0d502349c3225bee83c9e42032f920a1706d946d758b2f1a35d16cbb9",
}


def dog_groups() -> dict[str, list[str]]:
    """$random alias -> its three members' logical names."""
    out: dict[str, list[str]] = {}
    for d in DOG_INSTALLS:
        out.setdefault(d.group, []).append(d.logical)
    return out


def dog_check(d: DogInstall, ogg: bytes | None = None) -> tuple[float, float]:
    """-> (decoded peak dBFS, loudest 50 ms A); raises if either is off."""
    x = gws.decode(d.path) if ogg is None else _decode_ogg(ogg)
    peak, loud = alts.peak_db(x), alts.loud_a_db(x)
    if peak >= DECODED_PEAK_CEILING_DBFS or abs(loud - d.target_db) > LOUDNESS_TOLERANCE_DB + CODEC_LOUDNESS_DB:
        raise ValueError(f"{d.candidate}: peak {peak:.2f} dBFS, {loud:.2f} dB A against {d.target_db:.2f}")
    return peak, loud


def install_dogs(asset_dir: Path | None, lumps=None) -> dict[str, str]:
    out = {}
    for d in DOG_INSTALLS:
        if lumps and d.lump not in lumps:
            continue
        data = d.path.read_bytes()
        peak, loud = dog_check(d, data)
        out[d.lump] = sha256(data)
        if asset_dir is not None:
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / f"{d.lump}.ogg").write_bytes(data)
        print(f"{d.lump} {d.candidate} {d.logical:30s} peak {peak:5.2f} loudA {loud:6.2f} "
              f"(target {d.target_db:6.2f}, {d.ref})  ogg {out[d.lump]}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--install", action="store_true", help="also write the OGGs into assets/sounds/enemies/")
    ap.add_argument("--voices", action="store_true", help="the voice takes of D91, D96, D110 and D118 instead")
    ap.add_argument("--dogs", action="store_true", help="the hound's dog takes of D107 instead")
    ap.add_argument("names", nargs="*", help="only these lumps")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):            # pragma: no cover - a replaced stream
        pass
    if args.dogs:
        bad = [n for n in args.names if n not in DOGS_BY_LUMP]
        if bad:
            print(f"not an approved dog take: {', '.join(bad)}", file=sys.stderr)
            return 2
        install_dogs(ASSET_DIR if args.install else None, args.names or None)
        return 0
    if args.voices:
        bad = [n for n in args.names if n not in VOICES_BY_LUMP]
        if bad:
            print(f"not an approved voice take: {', '.join(bad)}", file=sys.stderr)
            return 2
        install_voices(ASSET_DIR if args.install else None, args.names or None)
        return 0
    if args.list:
        sys.stdout.write(plan_text())
        return 0
    bad = [n for n in args.names if n not in INSTALLS_BY_LUMP]
    if bad:
        print(f"not approved in D83/D86 (or unknown): {', '.join(bad)}", file=sys.stderr)
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
