#!/usr/bin/env python3
"""Pack the work-in-progress music into a throwaway PK3 and play or render it.

    python3 tools/audio/audition.py --pack            # just build the test PK3
    python3 tools/audio/audition.py --play map01      # launch GZDoom and listen
    python3 tools/audio/audition.py --play title
    python3 tools/audio/audition.py --render          # engine renders WAVs, no window

Why this exists
---------------
`work/audio/` is deliberately NOT packed by `tools/build.py`: nothing reaches
the player before the CEO approves it (project rule, same as `work/art/`).
So the only way to hear a draft in the real engine is a second PK3 loaded on
top of `dist/sovietdoom.pk3`. GZDoom reads MAPINFO from every loaded archive
in order, so the overlay's `map MAP01` block wins and MAP01 plays `D_SDM01`
without `src/lumps/MAPINFO` being touched (that lump belongs to
`mod-engineer`).

`--render` is the part that proves the file actually *sounds*: it uses
GZDoom's own `writewave <midi> <file>` console command, so the bytes are
parsed and synthesised by the same code that will play them in game, and the
result is a WAV we can measure (duration, peak, silence) without a human in
the loop.

This tool is for auditioning only. It writes to `work/audio/` and `logs/`,
never to `assets/`, `src/` or `dist/`.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = PROJECT_ROOT / "work" / "audio"
TEST_PK3 = AUDIO_DIR / "sd-music-draft.pk3"
MOD_PK3 = PROJECT_ROOT / "dist" / "sovietdoom.pk3"
LOG_DIR = PROJECT_ROOT / "logs"

# Same discovery order as tools/run.sh, kept in sync by hand (that script
# belongs to mod-engineer and is not edited from here).
GZDOOM_CANDIDATES = (
    Path("/Applications/GZDoom.app/Contents/MacOS/gzdoom"),
    Path.home() / "Applications/GZDoom.app/Contents/MacOS/gzdoom",
)
IWAD_CANDIDATES = (
    PROJECT_ROOT / "iwads" / "freedoom2.wad",
    PROJECT_ROOT / "iwads" / "doom2.wad",
)

MUSIC_DIR_IN_PK3 = "music"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # reproducible, as sdbuild.pk3 does

TITLE_LUMP = "D_SDTITL"
MAP01_LUMP = "D_SDM01"

# GZDoom runs at 35 tics per second; the console sequence is the same proven
# pattern tools/smoke.py uses.
TICS_PER_SECOND = 35
RENDER_WAIT_TICS = 70          # ~2 s for the engine to settle before rendering
RENDER_SETTLE_TICS = 140       # ~4 s for writewave to finish and flush
RENDER_TIMEOUT_S = 180.0
RENDER_SAMPLE_RATE = 44100

# A WAV that is all zeroes means the synth produced nothing: the file loaded
# but no sound came out. These are the thresholds `--render` checks.
MIN_PEAK_AMPLITUDE = 0.02      # of full scale
MIN_DURATION_RATIO = 0.80      # rendered length vs. the length we expect

MAPINFO_OVERLAY = f"""\
// Audition overlay - tools/audio/audition.py. NOT part of the mod.
// Loaded after dist/sovietdoom.pk3 so these blocks win. Delete the PK3 and
// everything is as it was; src/lumps/MAPINFO is never touched.

GameInfo
{{
	TitleMusic = "{TITLE_LUMP}"
	TitleTime = 90
}}

map MAP01 lookup "SD_MAP01_NAME"
{{
	next = "MAP01"
	music = "{MAP01_LUMP}"
	sky1 = "SKY1"
	nointermission
}}
"""


def find(candidates) -> Path | None:
    for c in candidates:
        if c.is_file():
            return c
    return None


def pack(quiet: bool = False) -> Path:
    midis = sorted(AUDIO_DIR.glob("*.mid"))
    if not midis:
        raise SystemExit(f"no .mid files in {AUDIO_DIR}; run tools/audio/gen_music.py first")
    TEST_PK3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TEST_PK3, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in [("MAPINFO", MAPINFO_OVERLAY.encode())] + [
            (f"{MUSIC_DIR_IN_PK3}/{p.name}", p.read_bytes()) for p in midis
        ]:
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
    if not quiet:
        print(f"packed {TEST_PK3} ({TEST_PK3.stat().st_size} B): "
              + ", ".join(p.stem for p in midis))
    return TEST_PK3


def engine_args(gzdoom: Path, iwad: Path, console: str, log: Path, extra: list[str]) -> list[str]:
    return [str(gzdoom), "-iwad", str(iwad), "-file", str(MOD_PK3), "-file", str(TEST_PK3),
            "+logfile", str(log), *extra, "+" + console]


def cmd_play(which: str) -> int:
    gzdoom, iwad = require_engine()
    pack()
    LOG_DIR.mkdir(exist_ok=True)
    log = LOG_DIR / "audition.log"
    if which == "title":
        # No +map: the engine sits on the title screen, which is where
        # GameInfo TitleMusic plays.
        args = [str(gzdoom), "-iwad", str(iwad), "-file", str(MOD_PK3), "-file", str(TEST_PK3),
                "+logfile", str(log)]
    else:
        args = [str(gzdoom), "-iwad", str(iwad), "-file", str(MOD_PK3), "-file", str(TEST_PK3),
                "+logfile", str(log), "+map", "MAP01"]
    print(" ".join(args))
    return subprocess.call(args)


def cmd_render(lumps: list[str], expected: dict[str, float]) -> int:
    """Have the engine itself synthesise each MIDI to a WAV, then measure it."""
    gzdoom, iwad = require_engine()
    pack()
    LOG_DIR.mkdir(exist_ok=True)
    out_dir = AUDIO_DIR / "render"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / "audition-render.log"

    console = [f"wait {RENDER_WAIT_TICS}"]
    for lump in lumps:
        console.append(f'writewave {lump} "{out_dir / (lump + ".wav")}" 0 {RENDER_SAMPLE_RATE}')
    console.append(f"wait {RENDER_SETTLE_TICS}")
    console.append("quit")

    args = [str(gzdoom), "-iwad", str(iwad), "-file", str(MOD_PK3), "-file", str(TEST_PK3),
            "+logfile", str(log), "-nosound", "+vid_fullscreen", "0",
            "+" + "; ".join(console)]
    print(" ".join(args))
    env = dict(os.environ, SDL_VIDEODRIVER=os.environ.get("SDL_VIDEODRIVER", ""))
    try:
        subprocess.run(args, timeout=RENDER_TIMEOUT_S, env=env, check=False)
    except subprocess.TimeoutExpired:
        print("render: the engine did not quit in time", file=sys.stderr)
        return 5

    failures = 0
    for lump in lumps:
        wav = out_dir / (lump + ".wav")
        if not wav.is_file():
            print(f"FAIL {lump}: {wav} was not written")
            failures += 1
            continue
        seconds, peak = measure_wav(wav)
        want = expected.get(lump, 0.0)
        ok_len = want == 0 or seconds >= want * MIN_DURATION_RATIO
        ok_peak = peak >= MIN_PEAK_AMPLITUDE
        status = "OK  " if ok_len and ok_peak else "FAIL"
        print(f"{status} {lump}: {wav.stat().st_size} B, {seconds:.1f}s "
              f"(expected ~{want:.1f}s), peak {peak:.3f} of full scale")
        failures += 0 if (ok_len and ok_peak) else 1
    return 1 if failures else 0


# GZDoom's `writewave` emits WAVE_FORMAT_EXTENSIBLE with the IEEE-float
# subformat, which Python's own `wave` module refuses to open
# ("unknown extended format: 00000003-..."). So we walk the RIFF chunks by
# hand. `audioop` would not have helped either: it was removed in 3.13.
WAV_FORMAT_PCM = 0x0001
WAV_FORMAT_IEEE_FLOAT = 0x0003
WAV_FORMAT_EXTENSIBLE = 0xFFFE
WAV_EXTENSIBLE_SUBFORMAT_OFFSET = 24       # bytes into the fmt chunk


def measure_wav(path: Path) -> tuple[float, float]:
    """Duration in seconds and peak amplitude (0..1). Any RIFF/WAVE, stdlib only."""
    import array

    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"{path} is not a RIFF/WAVE file")
    offset = 12
    fmt = None
    data = b""
    while offset + 8 <= len(raw):
        chunk_id = raw[offset:offset + 4]
        (size,) = struct.unpack("<I", raw[offset + 4:offset + 8])
        body = raw[offset + 8:offset + 8 + size]
        if chunk_id == b"fmt ":
            fmt = body
        elif chunk_id == b"data":
            data = body
        offset += 8 + size + (size & 1)     # chunks are word-aligned
    if fmt is None or not data:
        raise ValueError(f"{path}: missing fmt or data chunk")

    tag, channels, rate, _byte_rate, _align, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == WAV_FORMAT_EXTENSIBLE and len(fmt) >= WAV_EXTENSIBLE_SUBFORMAT_OFFSET + 2:
        (tag,) = struct.unpack("<H", fmt[WAV_EXTENSIBLE_SUBFORMAT_OFFSET:
                                         WAV_EXTENSIBLE_SUBFORMAT_OFFSET + 2])
    width = bits // 8
    frames = len(data) // (width * max(channels, 1))
    seconds = frames / rate if rate else 0.0

    if tag == WAV_FORMAT_IEEE_FLOAT and bits == 32:
        samples = array.array("f")
        samples.frombytes(data[: len(data) - len(data) % 4])
        full_scale = 1.0
    elif tag == WAV_FORMAT_PCM and bits == 16:
        samples = array.array("h")
        samples.frombytes(data[: len(data) - len(data) % 2])
        full_scale = 32768.0
    elif tag == WAV_FORMAT_PCM and bits == 8:
        samples = array.array("b", bytes((b - 128) & 0xFF for b in data))
        full_scale = 128.0
    else:
        raise ValueError(f"{path}: unsupported format tag {tag:#06x} at {bits} bits")
    peak = max((abs(s) for s in samples), default=0) / full_scale
    return seconds, peak


def require_engine() -> tuple[Path, Path]:
    gzdoom = find(GZDOOM_CANDIDATES) or (Path(shutil.which("gzdoom")) if shutil.which("gzdoom") else None)
    if gzdoom is None:
        raise SystemExit("gzdoom not found (brew install --cask gzdoom)")
    iwad = find(IWAD_CANDIDATES)
    if iwad is None:
        raise SystemExit(f"no IWAD in {PROJECT_ROOT / 'iwads'}")
    if not MOD_PK3.is_file():
        raise SystemExit(f"{MOD_PK3} missing; run python3 tools/build.py")
    return gzdoom, iwad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", action="store_true", help="only build the overlay PK3")
    parser.add_argument("--play", choices=("title", "map01"), help="launch GZDoom and listen")
    parser.add_argument("--render", action="store_true",
                        help="engine-render every MIDI to WAV and measure it")
    parser.add_argument("--expect", action="append", default=[], metavar="LUMP=SECONDS",
                        help="expected duration for --render, e.g. D_SDM01=142")
    args = parser.parse_args(argv)

    if args.play:
        return cmd_play(args.play)
    if args.render:
        expected = {}
        for item in args.expect:
            lump, _, value = item.partition("=")
            expected[lump] = float(value)
        lumps = sorted(p.stem for p in AUDIO_DIR.glob("*.mid"))
        return cmd_render(lumps, expected)
    pack()
    return 0


if __name__ == "__main__":
    sys.exit(main())
