#!/usr/bin/env python3
"""Install the world sounds the CEO approved (D125, 2026-10-23; backlog Next #10).

The candidates are `gen_world_sfx.py`'s, heard by the CEO on
`work/audio/preview/world_sounds_listening.html` (56 candidates, 19 sounds).
His verdict, 56/56 (docs/PRD.md D125): OK 50, NO 5 (SDPLDETH w2, SDPLJUMP w1
and w2, SDIZPKP w3, SDTELEPT w3), ? 1: SDPLOOF w1, "El audio está bien pero
no tiene el ruido, yo dejaría los 2 audios a la vez" ("The audio is fine but
it lacks the noise, I would keep both sounds at once").

What this does, and nothing else, the D107 dogs' way (`master_enemy_sfx.py
--dogs`):

* Every OK ships **byte for byte as the page's OGG**: the candidates were
  already levelled to the Freedoom lump each replaces (loudest 50 ms,
  A-weighted, `gen_weapon_alts.loud_a_db`; the IZh pickup at DSWPNUP - 3 dB,
  the weapon pickups' rule), peak -1 dBFS, codec-checked. The pass only
  re-checks them: decoded peak under `DECODED_PEAK_CEILING_DBFS`, loudness
  within its window (target +-1 dB plus the codec's 0.5 dB), or at the
  shortfall the page already reported (`SHORT_OF_TARGET`: Freedoom's exit
  switch and weapon pickup are 8-bit clipped lumps no clean transient
  reaches). The moving floor's loop is measured as the engine repeats it.
* **SDPLOOF w1** gets what the CEO asked for: its voice (the Chatterbox
  "Ух", 2 semitones down, as he heard it) laid over **w3's impact** (the
  boots and the kit on the concrete, rendered with w3's own seed, so the
  layer is the one he heard in w3), in w3's own recipe: the impact first,
  2 dB under the voice, the voice 20 ms after it. Then the page's chain for a
  mix (`gen_world_sfx.level` to DSOOF, `codec_safe`). It ships as `SDSGOOF1`.
* The jump keeps Freedoom's `DSJUMP` (both takes NO): no line, nothing packed.

Names (MOD-SPEC 6.2, as D86 and D107): the card's first seven letters and
the take number (the candidate's own `w<n>`): `SDDOROP1`. Two exceptions:
the switch cards share their first seven letters, so they drop the H
(`SDSWTCN<n>`, `SDSWTCX<n>`); the player's cards begin with SDPL, the
Panzermensch shell's sprite prefix (reserved, tests/test_gen_shells.py), so
the sergeant's sounds take SDSG and the event's three letters (`SDSGPAI1`). Each sound is a `$random` group (SNDINFO) over
its takes, wired to the engine in `src/lumps/SNDINFO` (`sndinfo_block()`
prints it): the player's on `sd/player/<event>`, reached through
`$playeralias`; the world's straight on the engine's own logical name
(`doors/dr1_open`...), so gzdoom.pk3's `$limit` and `$pitchshift` on the
pickups still hold (members `doors/dr1_open/1`...); the IZh-58's on `sd/weapon/izh/pickup`, its
`Inventory.PickupSound`.

Run:

    .venv/Scripts/python.exe tools/audio/master_world_sfx.py --list
    .venv/Scripts/python.exe tools/audio/master_world_sfx.py             # checks, writes work/ only
    .venv/Scripts/python.exe tools/audio/master_world_sfx.py --install   # and the OGGs into assets/
    .venv/Scripts/python.exe tools/audio/master_world_sfx.py --sndinfo   # the SNDINFO block
    .venv/Scripts/python.exe -m unittest tests.test_world_sfx_install -v

GPL-3.0 (the script); its output CC BY-NC-SA 4.0 (D15), with the CC0 layers
credited in `docs/art/LICENSES.md` ("World sounds") and the two xdeath takes
under Freedoom's BSD-3 for the DSSLOP inside our gib.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PROJECT_ROOT = HERE.parents[1]
CAND_DIR = PROJECT_ROOT / "work" / "audio" / "candidates" / "world"
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "world"
WORK_DIR = PROJECT_ROOT / "work" / "audio" / "master_world"
DECISION = "D125"

# card -> (lump stem, the $random group's name). Members are <group>/<n>,
# the file's convention (D86), engine names included (doors/dr1_open/1).
CARDS: dict[str, tuple[str, str]] = {
    "SDPLPAIN": ("SDSGPAI", "sd/player/pain"),
    "SDPLDETH": ("SDSGDET", "sd/player/death"),
    "SDPLXDTH": ("SDSGXDT", "sd/player/xdeath"),
    "SDPLOOF": ("SDSGOOF", "sd/player/oof"),
    "SDPLNOWY": ("SDSGNOW", "sd/player/usefail"),
    "SDDOROPN": ("SDDOROP", "doors/dr1_open"),
    "SDDORCLS": ("SDDORCL", "doors/dr1_clos"),
    "SDBDOPN": ("SDBDOPN", "doors/dr2_open"),
    "SDBDCLS": ("SDBDCLS", "doors/dr2_clos"),
    "SDSWTCHN": ("SDSWTCN", "switches/normbutn"),
    "SDSWTCHX": ("SDSWTCX", "switches/exitbutn"),
    "SDITEMUP": ("SDITEMU", "misc/i_pkup"),
    "SDGETPOW": ("SDGETPO", "misc/p_pkup"),
    "SDIZPKP": ("SDIZPKP", "sd/weapon/izh/pickup"),
    "SDPSTART": ("SDPSTAR", "plats/pt1_strt"),
    "SDPSTOP": ("SDPSTOP", "plats/pt1_stop"),
    "SDPMOVE": ("SDPMOVE", "plats/pt1_mid"),
    "SDTELEPT": ("SDTELEP", "misc/teleport"),
}
# D125, the CEO's OKs: card -> its approved candidate numbers. SDPLOOF 1 is
# the "?" resolved as he asked (LAYERED), not the page's w1.
APPROVED: dict[str, tuple[int, ...]] = {
    "SDPLPAIN": (1, 2, 3), "SDPLDETH": (1, 3), "SDPLXDTH": (1, 2, 3), "SDPLOOF": (1, 2, 3),
    "SDPLNOWY": (1, 2, 3), "SDDOROPN": (1, 2, 3), "SDDORCLS": (1, 2, 3), "SDBDOPN": (1, 2, 3),
    "SDBDCLS": (1, 2, 3), "SDSWTCHN": (1, 2, 3), "SDSWTCHX": (1, 2, 3), "SDITEMUP": (1, 2, 3),
    "SDGETPOW": (1, 2, 3), "SDIZPKP": (1, 2), "SDPSTART": (1, 2, 3), "SDPSTOP": (1, 2, 3),
    "SDPMOVE": (1, 2, 3), "SDTELEPT": (1, 2),
}
# D125's NO: never installed. The jump (both NO) keeps Freedoom's DSJUMP.
REJECTED: dict[str, tuple[int, ...]] = {
    "SDPLDETH": (2,), "SDPLJUMP": (1, 2), "SDIZPKP": (3,), "SDTELEPT": (3,),
}
LAYERED = "SDSGOOF1"     # w1's voice over w3's impact (the CEO's "?", D125)
# Engine names that play the same takes as another group: the key pickup
# sounds like any other item (gzdoom.pk3: misc/k_pkup dsitemup). It gets its
# own $random and member lines over the same lumps (a take is in one group
# only; its own $limit and $pitchshift stay on it).
ALSO_PLAYED_AS: dict[str, str] = {"misc/k_pkup": "misc/i_pkup"}
# The player's sounds (gzdoom.pk3 filter/game-doomchex/sndinfo.txt): Doom
# defines *pain75/50/25 and *land as duplicates of *pain100 and *grunt, so
# each is aliased again here, or it would keep playing Freedoom's lump (and
# a hard landing would play both: GZDoom plays *land unless it resolves to
# the same sound as *grunt). *jump, *gibbed and *fist stay Doom's. All three
# genders: the sergeant is one man whatever the "gender" setting says.
PLAYER_SOUNDS: dict[str, str] = {
    "*pain100": "sd/player/pain", "*pain75": "sd/player/pain", "*pain50": "sd/player/pain",
    "*pain25": "sd/player/pain", "*death": "sd/player/death", "*xdeath": "sd/player/xdeath",
    "*grunt": "sd/player/oof", "*land": "sd/player/oof", "*usefail": "sd/player/usefail",
}
GENDERS = ("male", "female", "other")
# Shortfalls the page already reported, dB under the target (measured on the decoded
# installed OGG, 2026-10-23; the tests hold them within SHORT_TOLERANCE_DB).
SHORT_OF_TARGET: dict[str, float] = {
    "SDSWTCX1": 3.66, "SDSWTCX2": 2.30, "SDSWTCX3": 1.70, "SDIZPKP1": 2.24,
}
SHORT_TOLERANCE_DB = 0.25
LOUDNESS_TOLERANCE_DB = 1.0
CODEC_LOUDNESS_DB = 0.5
DECODED_PEAK_CEILING_DBFS = -0.1


@dataclass(frozen=True)
class Take:
    card: str
    n: int

    @property
    def lump(self) -> str:
        return f"{CARDS[self.card][0]}{self.n}"

    @property
    def candidate(self) -> str:
        return f"{self.card}_w{self.n}"

    @property
    def group(self) -> str:
        return CARDS[self.card][1]

    @property
    def logical(self) -> str:
        return f"{self.group}/{self.n}"

    @property
    def layered(self) -> bool:
        return self.lump == LAYERED

    @property
    def path(self) -> Path:
        return CAND_DIR / f"{self.candidate}.ogg"


TAKES: tuple[Take, ...] = tuple(Take(card, n) for card, ns in APPROVED.items() for n in ns)
TAKES_BY_LUMP = {t.lump: t for t in TAKES}

# SHA-256 of each installed OGG. All but SDSGOOF1 are the page's candidate,
# byte for byte (work/audio/candidates/world/MANIFEST.tsv sha256_ogg).
INSTALLED_SHA256: dict[str, str] = {
    "SDSGPAI1": "8524ef65537241887c8b600bc1f76f1c69969b3b4dcc58b439c99e36078ade20",
    "SDSGPAI2": "4bd04d987c02d8b372d3a53c6e9f325d7fd01498a55daf34c646ef19ca68666c",
    "SDSGPAI3": "97d2c94e7a300844259a968fec29794f29de1518a20a1b33c0190d9ed6d939ac",
    "SDSGDET1": "7281e6af1aa8bcbcb3f2feae985a49859113c7937af3caab2fe9443c91bd029b",
    "SDSGDET3": "2653aa253f9e3560778b5d9986e214263bbb26a329897fc5a573701f23377609",
    "SDSGXDT1": "ac193da4562ce75e65105026bed894e95fd03e73530e742fb8225cce5cd1724d",
    "SDSGXDT2": "e926366aef5b87f539f45cff6625ae9ba3623dd428d204a36d1f75ae7e1fc43a",
    "SDSGXDT3": "0bf4901aeb2be96ef51db561105baec4394244763180b299d9a134546f6ae911",
    "SDSGOOF1": "9c84029f52f272f24d9fe36ca567e62f599b09751e5df73dbc61a52de89db2c6",
    "SDSGOOF2": "c6989f365e7a3cd62b070c5eeb7d8add93a641b83fc46bc6a30ad5f009037b5b",
    "SDSGOOF3": "6f4e1888f4e7d30526b3a919a9bc9da5514e60545733be4caf2b156e14f277b1",
    "SDSGNOW1": "f49cf82dec1094ecd5aa3b1310e34741e0bb87e72b7e13f9a7ca33011bc3783e",
    "SDSGNOW2": "5c7042882d0485316b787f1c1cf5bb2e4c592bdce9a4035789400a0b3088ba10",
    "SDSGNOW3": "66eac5d626aff83913645919a15450df1944bf9e356355af21fa7c3c5b3985fa",
    "SDDOROP1": "6ec79bace0446a780a9d045340bfa0c19d91ddbc0fab181b7d12498ae114687a",
    "SDDOROP2": "146264777b6a0a8d645dfd370f57597c74aae17d46ef172694269a54285da499",
    "SDDOROP3": "9b502f982762082d62c917cc3d831cb323318e34bf777de191c1d9d2ce8fc017",
    "SDDORCL1": "679cf4fdc0f89c031670c0fbc38e392d78b048d776a0bc81a5fab34bd3b0655f",
    "SDDORCL2": "70dcbf6e2a35ceb0bd7bdbcf537b367cc36e1b4786110d7f0f2983e2a6561b0e",
    "SDDORCL3": "e2530a3eeef1d6be0cfefddcbfef5f6f01c1ecb239ed60db2c82eb1f912b16e5",
    "SDBDOPN1": "95d53e1c0818ba466b80b4ecfedacd800a9677e76af3bd0a43483fc41d0831c1",
    "SDBDOPN2": "aa161b59af818025bca110e4022b1a9f847e24c3b45734b830feafb4fb3dbfb5",
    "SDBDOPN3": "efa0ab9a0f937bde5b21506413509f62e11221b2d79c16e181b05ec0d37e6787",
    "SDBDCLS1": "f0b8a53ce0937f3672a418724c0893ec5d52fd52c86b9f8b41999093e051afd1",
    "SDBDCLS2": "9328aa6843751acc7708e064f4052ca60bd2103444f2f8c55faaa113f313e848",
    "SDBDCLS3": "ffd40b17963edddba163595615ec1bda7d87482d4253f39f99a869f698c564bc",
    "SDSWTCN1": "c9f3cbd0a87b2cde9200ae6f2665a9bdd81cb57ed33bee6a44760588f6ed617a",
    "SDSWTCN2": "1ddec71989b04196f6f9c7b7d48bc61b498af56e19e1839a4178f3c23192213a",
    "SDSWTCN3": "aa8a8721d5aabc189e4dec196520f1a1f4bf20607f289360154ebfe75d4dae9c",
    "SDSWTCX1": "60483f6d07cd71e5d259c4fd4ae7fa8708acf965ac318eff5730ddd0ff9a81ba",
    "SDSWTCX2": "d95732c9de475c491e04358def7abd69a9a0ee9b874f2fa342e40a4e02c24899",
    "SDSWTCX3": "113549cbb9ba8d3976c26f56796d053bb00310502e99ab788aa6c0568e17dab9",
    "SDITEMU1": "2f09aa2674a142237c10895bcc930b928ecd3449c6026cbca20ef800f4db4d20",
    "SDITEMU2": "e6884b5c8770a4f5cb2dc69bbfff1cbd970aa97152be98a9cb6ba3f17d3999ca",
    "SDITEMU3": "9e42b31bd41b13bafb8df097ff75492f9b90b780534578a96230d1dc25da6b43",
    "SDGETPO1": "d06839142ca51ea8266671e8d5f7262b21a6fae02f513f41dbb6587858263b7f",
    "SDGETPO2": "1e9ce7f1feaea0608b68493094b328f74c30ace9563e84fa094a4e97fee11570",
    "SDGETPO3": "b628edbdc56b56f9c1051c94c489931cf947cd213c5701d10ffbf031abf66dd0",
    "SDIZPKP1": "49d3e28ef25b5df7bf5184d5753d64f55f5e480447d8a318d74f802441467f92",
    "SDIZPKP2": "e512452bc59c608f83eac54c252399bcae728340f26ce162ef40a0b9ae89cc5a",
    "SDPSTAR1": "26dc14e42151ead32470b5c1ba635ca92d59262a59cc9f494de3db53b608c2a5",
    "SDPSTAR2": "30283d60a6cbdb7f0a2749b0ed4790f76dbe90a6a1a5a3eb2afc6edfe662b0ac",
    "SDPSTAR3": "7d509960d769d7dcfc66e5d06cf304b96150552204e553f8df39541dac69ddab",
    "SDPSTOP1": "01efa324dce36c331b62e2e8bc611e234c390aeb75437b9a4541544797266785",
    "SDPSTOP2": "74660403b99fa5b00dbbb9b261d41ea5545d91529560e212c59584225d521322",
    "SDPSTOP3": "084e9a2adc8ab3fca2e4a2c18ba0365c0426cb9a7419ac572534cfd239c6240d",
    "SDPMOVE1": "a7c078144ee4a572fef63d1294b9ceeb7baef5c198ef491c358ff6077fae03bf",
    "SDPMOVE2": "b1db44f797981ab627cc5176b8b3bd661c5b9af8db400dba04ab62970fc94d41",
    "SDPMOVE3": "c9949f25092b999225eeeb29fde7998ba180978be7e01c3cd8030ed07bcb944f",
    "SDTELEP1": "57dd6584edcbd418797b9cea52f7a249525bf0bd2a0de11367fb599070362ffd",
    "SDTELEP2": "3c1df4543a87f4215ed8ea5d00c911391d60c5b83a08132f244bf6871435507b",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def groups() -> dict[str, list[str]]:
    """$random group -> its members' logical names, in take order."""
    out: dict[str, list[str]] = {}
    for t in TAKES:
        out.setdefault(t.group, []).append(t.logical)
    return out


# --- SNDINFO -------------------------------------------------------------------------

def sndinfo_block() -> str:
    """The lines src/lumps/SNDINFO carries for D125 (comments say the take)."""
    lines: list[str] = []
    for card in CARDS:
        takes = [t for t in TAKES if t.card == card]
        g = takes[0].group
        lines.append(f"$random {g} {{ {' '.join(t.logical for t in takes)} }}")
        for t in takes:
            note = "SDPLOOF_w1's voice over SDPLOOF_w3's impact" if t.layered else t.candidate
            lines.append(f"{t.logical:30s} {t.lump}    // {DECISION} {note}")
        for alias, target in ALSO_PLAYED_AS.items():
            if target == g:
                lines.append(f"$random {alias} {{ {' '.join(f'{alias}/{t.n}' for t in takes)} }}")
                for t in takes:
                    lines.append(f"{alias + '/' + str(t.n):30s} {t.lump}    // {DECISION} {t.candidate}, as {g}")
    for g in GENDERS:
        for ref, group in PLAYER_SOUNDS.items():
            lines.append(f"$playeralias player {g:6s} {ref:9s} {group}")
    return "\n".join(lines) + "\n"


# --- The layered oof (numpy and the page's generator from here on) --------------------

def render_layered():
    """-> (levelled samples, OGG bytes) of SDSGOOF1: w1's voice over w3's impact."""
    import numpy as np
    import gen_world_sfx as w

    rng = np.random.default_rng(w.seed_of("SDPLOOF_w3"))     # w3's seed: w3's impact, as heard
    impact = w.boots(rng)
    voice = w.ploof1(None)                                   # w1's voice, as heard (no rng)
    x = w.seq((w.unit(impact), 0.0, -2), (w.unit(voice), 0.02, 0))   # ploof3's recipe
    y, _ = w.level(x, w.EVENT["SDPLOOF"].target_db)
    y, ogg, _ = w.codec_safe(y)
    return y, ogg


def target_db(t: Take) -> float:
    import gen_world_sfx as w
    return w.EVENT[t.card].target_db


def measure(t: Take, ogg: bytes) -> tuple[float, float]:
    """-> (decoded peak dBFS, loudest 50 ms A dB; a loop measured repeated)."""
    import tempfile
    import numpy as np
    import gen_weapon_alts as alts
    import gen_weapon_sfx as gws
    import gen_world_sfx as w

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.ogg"
        p.write_bytes(ogg)
        x = gws.decode(p)
    loud = alts.loud_a_db(np.tile(x, 3) if w.EVENT[t.card].loop else x)
    return alts.peak_db(x), loud


def check(t: Take, ogg: bytes) -> tuple[float, float]:
    peak, loud = measure(t, ogg)
    target = target_db(t) - SHORT_OF_TARGET.get(t.lump, 0.0)
    window = SHORT_TOLERANCE_DB if t.lump in SHORT_OF_TARGET else LOUDNESS_TOLERANCE_DB + CODEC_LOUDNESS_DB
    if peak >= DECODED_PEAK_CEILING_DBFS or abs(loud - target) > window:
        raise ValueError(f"{t.lump}: peak {peak:.2f} dBFS, {loud:.2f} dB A against {target:.2f}")
    return peak, loud


def ogg_of(t: Take) -> bytes:
    if t.layered:
        import gen_weapon_sfx as gws
        y, ogg = render_layered()
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        (WORK_DIR / f"{t.lump}.wav").write_bytes(gws.wav_bytes(y))
        return ogg
    return t.path.read_bytes()


def install(asset_dir: Path | None, lumps=None) -> dict[str, str]:
    out = {}
    for t in TAKES:
        if lumps and t.lump not in lumps:
            continue
        data = ogg_of(t)
        peak, loud = check(t, data)
        out[t.lump] = sha256(data)
        if asset_dir is not None:
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / f"{t.lump}.ogg").write_bytes(data)
        print(f"{t.lump} {t.candidate if not t.layered else 'SDPLOOF_w1+w3':14s} {t.logical:34s} "
              f"peak {peak:6.2f} loudA {loud:6.2f} (target {target_db(t):6.2f})  ogg {out[t.lump]}")
    return out


def plan_text() -> str:
    rows = [f"{t.lump}  {t.candidate:13s} {t.logical}" + ("   (w1's voice over w3's impact)" if t.layered else "")
            for t in TAKES]
    rows.append("rejected: " + ", ".join(f"{c}_w{n}" for c, ns in REJECTED.items() for n in ns)
                + "; the jump keeps DSJUMP")
    return "\n".join(rows) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--sndinfo", action="store_true", help="print the SNDINFO block and write nothing")
    ap.add_argument("--install", action="store_true", help="also write the OGGs into assets/sounds/world/")
    ap.add_argument("names", nargs="*", help="only these lumps")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):            # pragma: no cover - a replaced stream
        pass
    if args.list:
        sys.stdout.write(plan_text())
        return 0
    if args.sndinfo:
        sys.stdout.write(sndinfo_block())
        return 0
    bad = [n for n in args.names if n not in TAKES_BY_LUMP]
    if bad:
        print(f"not an approved D125 take: {', '.join(bad)}", file=sys.stderr)
        return 2
    install(ASSET_DIR if args.install else None, args.names or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
