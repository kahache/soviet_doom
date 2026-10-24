#!/usr/bin/env python3
"""V3 B5: install the propaganda radio (D124) into assets/sounds/radio/.

The CEO approved every take of SDRAD01-SDRAD16 and the three station jingles
(D124: "me fío para dar OK a TODO de radio", "I trust it enough to OK ALL of
the radio"). One take per line ships, the
best by the round's own measurements (work/audio/candidates/radio/METRICS.json,
rank 1: voice length against an announcer's pace, longest inner pause,
silence share; docs/sound/2026-10-23_V3_propaganda-radio.md section 8). Never
RAD07 t03, which the measurements flag as a runaway (6.04 s for 3.7 s).

What is copied, byte for byte, from the candidates folder:

  SDRAD01..SDRAD15  the chosen take of each line (TAKES below)
  SDRAD16           the time signal: the six pips, then RAD16's chosen take
                    (t02), as the round rendered it (RAD16_pips_demo): the
                    pips play before RAD16 only, so they are one file with it
  SDRADJ1..SDRADJ3  the three jingles (our synthesis, original motifs)

What is rendered here (procedural, ours, no source): SDRADBED, a 6 s
seamless loop of the radio set itself (50 Hz valve hum and its odd
harmonics, hiss, sparse crackle, a slow reception wobble, through the
300-3400 Hz band): the same set the round put under every take
(gen_radio.py valve_bed / wobble / radio_band), heard alone, for a
loudspeaker with SD_LS_FLAG_BED.

    .venv/Scripts/python.exe tools/audio/install_radio.py                # install
    .venv/Scripts/python.exe tools/audio/install_radio.py --source DIR   # from another checkout's candidates
    .venv/Scripts/python.exe tools/audio/install_radio.py --list         # the plan, writes nothing

The candidates live in the gitignored work/ of the main checkout. Needs
numpy and ffmpeg for the bed (the venv; ffmpeg on the PATH).
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "work" / "audio" / "candidates" / "radio"
DEST = PROJECT_ROOT / "assets" / "sounds" / "radio"
DAY = "20261023"

# Line -> take, rank 1 of METRICS.json (lowest score). RAD16's take is t02,
# shipped inside the pips file.
TAKES = {1: 1, 2: 2, 3: 2, 4: 3, 5: 1, 6: 3, 7: 1, 8: 2, 9: 2, 10: 3,
         11: 2, 12: 1, 13: 2, 14: 3, 15: 1, 16: 2}
PIPS_LINE = 16
JINGLES = ("J1", "J2", "J3")

# The bed (SDRADBED): seconds, seed, level.
SR = 44100
BED_SECONDS = 6.0
BED_FADE_SECONDS = 0.5          # the loop's crossfade, end into start
BED_SEED = 21201                # the loudspeaker's editor number
BED_RMS_DB = -30.0              # with SD_LS_BED_VOLUME (0.3) about 15 dB under the voice (the takes: -22 dBFS at 0.7)
BAND = (300.0, 3400.0)


def take_name(line: int, take: int) -> str:
    return f"RAD{line:02d}_SDRAD{line:02d}_ai_chatterbox_{DAY}_t{take:02d}.ogg"


def plan(source: Path) -> list[tuple[str, Path | None]]:
    """(lump, source file or None for a rendered one), in install order."""
    out: list[tuple[str, Path | None]] = []
    for line, take in TAKES.items():
        name = f"RAD{PIPS_LINE}_pips_demo_{DAY}.ogg" if line == PIPS_LINE else take_name(line, take)
        out.append((f"SDRAD{line:02d}", source / name))
    for j in JINGLES:
        out.append((f"SDRADJ{j[1]}", source / f"RADJ_{j}_synth_{DAY}.ogg"))
    out.append(("SDRADBED", None))
    return out


def render_bed():
    """The valve set alone, a seamless loop (numpy; gen_radio.py's set)."""
    import numpy as np
    sys.path.insert(0, str(HERE))
    import gen_weapon_sfx as gws  # noqa: E402  (filters and the OGG writer)

    rng = np.random.default_rng(BED_SEED)
    fade = int(BED_FADE_SECONDS * SR)
    length = int(BED_SECONDS * SR)
    n = fade + length + fade              # the filter's onset, the loop, the crossfade's source
    t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * 50 * k * t + rng.uniform(0, 6.28))
              for k, a in ((1, 1.0), (3, 0.5), (5, 0.3), (7, 0.18), (9, 0.1))) * 0.016
    hiss = rng.standard_normal(n) * 0.010
    crack = np.zeros(n)
    for _ in range(int(n / SR * 2.5)):                       # ~2.5 crackles a second
        i = int(rng.integers(0, n - 40))
        k = int(rng.integers(3, 30))
        crack[i:i + k] += rng.uniform(-1, 1) * rng.uniform(0.02, 0.09) * np.exp(-np.arange(k) / 6)
    # The wobble's two periods divide 6 s, so it is seamless too.
    wob = 10 ** ((0.6 * np.sin(2 * np.pi * t / 3.0) + 0.4 * np.sin(2 * np.pi * t / 1.5)) / 20)
    x = gws.filt((hum + hiss + crack) * wob,
                 lambda f: gws.butter(f, lo=BAND[0], hi=BAND[1], order=3) * gws.bump(f, 1400, 1.4, 3.0))
    s = x[fade:]                                             # drop the filter's onset
    loop = s[:length].copy()
    ramp = np.linspace(0.0, 1.0, fade)
    # Seamless: the loop's first `fade` samples fade from what follows its
    # end (s[length:]) into its own start, so its last sample flows into
    # its first.
    loop[:fade] = s[:fade] * ramp + s[length:length + fade] * (1 - ramp)
    rms = float(np.sqrt(np.mean(loop ** 2))) or 1.0
    loop *= 10 ** (BED_RMS_DB / 20) / rms
    data = gws.ogg_bytes(gws.wav_bytes(loop, SR))
    if data is None:
        raise SystemExit("ffmpeg is not on the PATH: the bed cannot be encoded")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    steps = plan(args.source)
    if args.list:
        for lump, src in steps:
            print(f"{lump:9s} <- {src.name if src else 'rendered here'}")
        return 0
    missing = [str(src) for _, src in steps if src is not None and not src.is_file()]
    if missing:
        raise SystemExit("missing candidates:\n  " + "\n  ".join(missing))
    DEST.mkdir(parents=True, exist_ok=True)
    for lump, src in steps:
        out = DEST / f"{lump}.ogg"
        if src is None:
            out.write_bytes(render_bed())
        else:
            shutil.copyfile(src, out)
        print(f"{lump:9s} {sha256(out)}  {out.stat().st_size:7d} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
