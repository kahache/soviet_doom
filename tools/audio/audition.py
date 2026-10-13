#!/usr/bin/env python3
"""Pack the work-in-progress music into a throwaway PK3 and play or render it.

    python3 tools/audio/audition.py --pack            # just build the test PK3
    SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play map01   # launch GZDoom and listen (D26 gate)
    SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play title
    SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --render   # engine renders WAVs (D26 gate)

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
import math
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:          # run as a script from tools/audio/
    sys.path.insert(0, str(TOOLS_DIR))

from sdbuild.wad import WadError, validate_lump_name  # noqa: E402
AUDIO_DIR = PROJECT_ROOT / "work" / "audio"
CANDIDATES_DIR = AUDIO_DIR / "candidates"
TEST_PK3 = AUDIO_DIR / "sd-music-draft.pk3"
MOD_PK3 = PROJECT_ROOT / "dist" / "sovietdoom.pk3"
LOG_DIR = PROJECT_ROOT / "logs"
TOOLING_CONFIG = LOG_DIR / "gzdoom-tooling.ini"

# Same discovery order as tools/run.sh, kept in sync by hand (that script
# belongs to mod-engineer and is not edited from here).
GZDOOM_CANDIDATES = (
    Path("/Applications/GZDoom.app/Contents/MacOS/gzdoom"),
    Path.home() / "Applications/GZDoom.app/Contents/MacOS/gzdoom",
) + tuple(
    # Windows (the CEO's PC since 2026-10-13): the release zip unpacked under
    # %LOCALAPPDATA%\Programs\GZDoom, or the installer's Program Files.
    Path(os.environ[var]) / sub / "GZDoom" / "gzdoom.exe"
    for var, sub in (("LOCALAPPDATA", "Programs"), ("ProgramFiles", "."))
    if os.environ.get(var)
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
# `writewave` synthesises faster than real time but not by a large factor, and
# the candidate set contains two pieces of ten minutes. Twelve files took
# ~175 s on this machine, which overran the first 180 s budget *after* every
# WAV had been written correctly — a false failure. Ten minutes is slack
# enough for the whole set plus the settle-and-quit tail.
RENDER_TIMEOUT_S = 600.0
RENDER_SAMPLE_RATE = 44100

# A WAV that is all zeroes means the synth produced nothing: the file loaded
# but no sound came out. These are the thresholds `--render` checks.
MIN_PEAK_AMPLITUDE = 0.02      # of full scale
MIN_DURATION_RATIO = 0.80      # rendered length vs. the length we expect

MAPINFO_OVERLAY = """\
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


def by_file_name(path) -> str:
    """Sort key for the files we pack: the bare file name, by code point.

    Not the Path itself: WindowsPath compares case-insensitively and PosixPath
    by code point, so `sorted(paths)` can number the same folder differently
    on the CEO's PC and on the Mac, and "D_CND11" in a verdict would name a
    different piece (A5). Code point is what the Mac used when it wrote
    work/audio/candidates-lumps.txt, so the existing numbering is kept.
    """
    return path.name


CANDIDATE_LUMP_PREFIX = "D_CND"
CANDIDATE_REGISTRY_NAME = "LUMPS.txt"     # lives in CANDIDATES_DIR, tracked in git (D43)


def read_registry(path: Path) -> dict[str, str]:
    """file name -> lump, from `LUMP  FILE` lines; '#' starts a comment."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        lump, _, name = line.partition(" ")
        if name.strip():
            out[name.strip()] = lump.strip().upper()
    return out


def candidate_lumps(files: list[Path]) -> list[tuple[str, Path]]:
    """Stable `D_CNDnn` names for the downloaded candidates.

    The numbers were first positional (file-name order). That made every
    number a function of which OTHER files happened to be in the folder, so
    deleting the three discards of D43 (D_CND02, 04, 08) would silently have
    renamed nine pieces, and "D_CND09" in a CEO verdict or in
    docs/sound/SOUNDTRACK.md would have named a different piece -- the same
    failure as bug A5, by another route. So the assignment is now a registry,
    `candidates/LUMPS.txt`, tracked in git with the files themselves:

    - a file listed there keeps its lump forever;
    - a new file gets the next number after the highest ever registered
      (a retired number is never reused: its line stays, commented);
    - with no registry the numbering is the old positional one, which is how
      the Mac's twelve were numbered, so the registry reproduces it.

    The registry is written only when a new file needed a number.
    """
    registry_path = CANDIDATES_DIR / CANDIDATE_REGISTRY_NAME
    known = read_registry(registry_path)
    used = set(known.values())
    if registry_path.is_file():
        # retired lines ("# D_CND02  file  retired ...") still hold their number
        for line in registry_path.read_text(encoding="utf-8").splitlines():
            token = line.lstrip("# ").split(" ", 1)[0].upper()
            if token.startswith(CANDIDATE_LUMP_PREFIX):
                used.add(token)
    highest = max((int(u[len(CANDIDATE_LUMP_PREFIX):]) for u in used
                   if u[len(CANDIDATE_LUMP_PREFIX):].isdigit()), default=0)
    pairs: list[tuple[str, Path]] = []
    new_lines: list[str] = []
    for p in files:
        lump = known.get(p.name)
        if lump is None:
            highest += 1
            lump = f"{CANDIDATE_LUMP_PREFIX}{highest:02d}"
            new_lines.append(f"{lump}  {p.name}\n")
        pairs.append((lump, p))
    if new_lines:
        old = registry_path.read_text(encoding="utf-8") if registry_path.is_file() else ""
        if old and not old.endswith("\n"):
            old += "\n"
        registry_path.write_text(old + "".join(new_lines), encoding="utf-8")
    return sorted(pairs, key=lambda pair: (len(pair[0]), pair[0]))


def sources(use_candidates: bool) -> list[tuple[str, Path]]:
    """(lump name, file) pairs to pack.

    Our own drafts are already named as lumps (`D_SDTITL.mid`); that is
    checked here, as tools/sdbuild/pk3.py checks src/lumps. Downloaded
    candidates are not: their names are long, carry punctuation and would not
    survive as Doom lump names, so they get stable positional names
    `D_CND01`..`D_CNDnn` in file-name order (`by_file_name`). The mapping is
    printed on every pack and written next to the PK3, because `writewave`
    and the MAPINFO `music` key both address the lump, not the file.
    """
    if use_candidates:
        files = sorted(CANDIDATES_DIR.glob("*.mid"), key=by_file_name)
        if not files:
            raise SystemExit(f"no .mid files in {CANDIDATES_DIR}")
        return candidate_lumps(files)
    files = sorted(AUDIO_DIR.glob("*.mid"), key=by_file_name)
    if not files:
        raise SystemExit(f"no .mid files in {AUDIO_DIR}; run tools/audio/gen_music.py first")
    pairs = []
    for p in files:
        try:
            pairs.append((validate_lump_name(p.stem), p))
        except WadError as exc:
            raise SystemExit(f"audition: draft {p} cannot be packed as a lump: {exc}. "
                             "Rename it: at most 8 characters, A-Z 0-9 _") from exc
    return pairs


def pack(use_candidates: bool = False, first_lump: str | None = None,
         quiet: bool = False) -> list[tuple[str, Path]]:
    pairs = sources(use_candidates)
    lumps = [lump for lump, _ in pairs]
    if first_lump is not None:
        # Checked before anything is written: a MAPINFO naming a lump that is
        # not in the PK3 plays silence, the very symptom this tool rules out.
        if first_lump.upper() not in lumps:
            raise SystemExit(f"audition: --lump {first_lump} is not in the pack; "
                             f"packed lumps: {', '.join(lumps)}")
        first_lump = first_lump.upper()
    title = first_lump or (pairs[0][0] if use_candidates else TITLE_LUMP)
    map01 = first_lump or (pairs[0][0] if use_candidates else MAP01_LUMP)
    mapinfo = MAPINFO_OVERLAY.format(TITLE_LUMP=title, MAP01_LUMP=map01)

    TEST_PK3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TEST_PK3, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in [("MAPINFO", mapinfo.encode())] + [
            (f"{MUSIC_DIR_IN_PK3}/{lump}.mid", p.read_bytes()) for lump, p in pairs
        ]:
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)

    manifest = AUDIO_DIR / "candidates-lumps.txt" if use_candidates else None
    if manifest:
        manifest.write_text("".join(f"{lump}  {p.name}\n" for lump, p in pairs))
    if not quiet:
        print(f"packed {TEST_PK3} ({TEST_PK3.stat().st_size} B), "
              f"title/MAP01 = {title}")
        for lump, p in pairs:
            print(f"  {lump}  {p.name}")
    return pairs


def cmd_play(which: str, use_candidates: bool = False, lump: str | None = None) -> int:
    gzdoom, iwad = require_engine()
    pack(use_candidates=use_candidates, first_lump=lump)
    LOG_DIR.mkdir(exist_ok=True)
    log = LOG_DIR / "audition.log"
    # Explicit volumes and our own config: the CEO heard silence because his
    # gzdoom.ini had snd_musicvolume at 0 while the engine was happily playing
    # D_SDTITL. An audition tool that depends on the listener's mixer settings
    # is not a tool. -config also stops our runs from writing state back into
    # the user's own preferences.
    audio = ["-config", str(TOOLING_CONFIG),
             "+snd_musicvolume", "0.8", "+snd_sfxvolume", "0.8"]
    if which == "title":
        # No +map: the engine sits on the title screen, which is where
        # GameInfo TitleMusic plays.
        args = [str(gzdoom), *audio, "-iwad", str(iwad), "-file", str(MOD_PK3),
                "-file", str(TEST_PK3), "+logfile", str(log)]
    else:
        args = [str(gzdoom), *audio, "-iwad", str(iwad), "-file", str(MOD_PK3),
                "-file", str(TEST_PK3), "+logfile", str(log), "+map", "MAP01"]
    print(" ".join(args))
    return subprocess.call(args)


def cmd_render(expected: dict[str, float], use_candidates: bool = False) -> int:
    """Have the engine itself synthesise each MIDI to a WAV, then measure it."""
    gzdoom, iwad = require_engine(need_mod=False)
    pairs = pack(use_candidates=use_candidates)
    lumps = [lump for lump, _ in pairs]
    names = dict(pairs)
    unknown = sorted(set(expected) - set(lumps))
    if unknown:
        # A mistyped --expect (D_SDMO1 for D_SDM01, or a draft name with
        # --candidates) would otherwise skip the very check it asked for.
        print(f"audition: --expect names lumps that were not packed: {', '.join(unknown)}; "
              f"packed lumps: {', '.join(lumps)}", file=sys.stderr)
        return EXIT_USAGE
    LOG_DIR.mkdir(exist_ok=True)
    out_dir = AUDIO_DIR / ("render-candidates" if use_candidates else "render")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / "audition-render.log"

    console = [f"wait {RENDER_WAIT_TICS}"]
    for lump in lumps:
        console.append(f'writewave {lump} "{out_dir / (lump + ".wav")}" 0 {RENDER_SAMPLE_RATE}')
    console.append(f"wait {RENDER_SETTLE_TICS}")
    console.append("quit")

    # `--render` deliberately does NOT load dist/sovietdoom.pk3; `--play` does.
    #
    # Two reasons, in order of importance. (1) The mod PK3 contributes nothing
    # to a `writewave` render: it ships no soundfont, no MIDI lump and no
    # sound CVar (`grep -i 'midi\|soundfont\|snd_' src/lumps/` is empty), so
    # the synthesis is byte-for-byte the FluidSynth + bundled `gzdoom.sf2`
    # path the player gets. (2) Loading it while another agent is rebuilding
    # it was observed, 2026-10-13, to leave the engine alive after the last
    # `writewave` so it never reached `quit` — a false timeout on a render
    # that had already written every WAV. Measurement must not depend on
    # somebody else's build being mid-flight. `--play` keeps the mod because
    # there the point IS the real game: title screen, menu, MAP01. For the
    # same reason require_engine() is not asked for the mod PK3 here.
    #
    # -config, as in --play and tools/smoke.py: without it this
    # `-nosound +vid_fullscreen 0` run reads the user's own gzdoom.ini and
    # writes its state back over it on quit.
    args = [str(gzdoom), "-config", str(TOOLING_CONFIG),
            "-iwad", str(iwad), "-file", str(TEST_PK3),
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
        print(f"{status} {lump} ({names[lump].name}): {wav.stat().st_size} B, "
              f"{seconds:.1f}s (expected ~{want:.1f}s), peak {peak:.3f} of full scale")
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


# The engine gate (D26), the same contract as tools/smoke.py and tools/run.sh:
# --play and --render both open a GZDoom window, and on 2026-10-13 agents
# opening windows every few seconds stopped the CEO working. Only the PM (or
# the CEO at the keyboard) sets the variable; --pack needs no engine and is
# never gated.
ENGINE_GATE_VAR = "SD_ALLOW_ENGINE"
EXIT_ENGINE_BLOCKED = 9   # same code as tools/run.sh
EXIT_USAGE = 2            # argparse's own code for a usage error


def engine_allowed(env: dict[str, str] | None = None) -> bool:
    env = os.environ if env is None else env
    return env.get(ENGINE_GATE_VAR) == "1"


def require_engine(need_mod: bool = True) -> tuple[Path, Path]:
    """GZDoom and the IWAD, behind the D26 gate. `need_mod`: also insist on
    dist/sovietdoom.pk3 (--play loads it; --render does not)."""
    if not engine_allowed():
        print(f"audition: refusing to start GZDoom (set {ENGINE_GATE_VAR}=1 to override).\n"
              "  Agents: never set it (D26). Say in your summary that the listening "
              "run is owed; the PM batches engine runs.", file=sys.stderr)
        raise SystemExit(EXIT_ENGINE_BLOCKED)
    gzdoom = find(GZDOOM_CANDIDATES) or (Path(shutil.which("gzdoom")) if shutil.which("gzdoom") else None)
    if gzdoom is None:
        raise SystemExit(
            "gzdoom not found. Install it (brew install --cask gzdoom; on Windows "
            "unzip the release under %LOCALAPPDATA%\\Programs\\GZDoom). Looked in: "
            + ", ".join(str(c) for c in GZDOOM_CANDIDATES) + " and $PATH")
    iwad = find(IWAD_CANDIDATES)
    if iwad is None:
        raise SystemExit(f"no IWAD in {PROJECT_ROOT / 'iwads'}")
    if need_mod and not MOD_PK3.is_file():
        raise SystemExit(f"{MOD_PK3} missing; run python3 tools/build.py")
    return gzdoom, iwad


def parse_expect(item: str) -> tuple[str, float]:
    """argparse type for --expect LUMP=SECONDS: a usage error, not a traceback."""
    lump, sep, value = item.partition("=")
    try:
        if not sep:
            raise ValueError("missing '='")
        lump = validate_lump_name(lump)
        seconds = float(value)
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("SECONDS must be a positive number")
    except (ValueError, WadError) as exc:
        raise argparse.ArgumentTypeError(
            f"{item!r} is not LUMP=SECONDS (e.g. D_SDM01=142): {exc}") from exc
    return lump, seconds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", action="store_true", help="only build the overlay PK3")
    parser.add_argument("--play", choices=("title", "map01"), help="launch GZDoom and listen")
    parser.add_argument("--render", action="store_true",
                        help="engine-render every MIDI to WAV and measure it")
    parser.add_argument("--expect", action="append", default=[], metavar="LUMP=SECONDS",
                        type=parse_expect,
                        help="expected duration for --render, e.g. D_SDM01=142")
    parser.add_argument("--candidates", action="store_true",
                        help="use work/audio/candidates/ (downloaded MIDIs) instead of "
                             "our own drafts; they are packed as D_CND01..D_CNDnn")
    parser.add_argument("--lump", metavar="NAME",
                        help="with --play: which lump to put on the title screen and MAP01 "
                             "(e.g. D_CND11). Default: the first one packed")
    args = parser.parse_args(argv)

    if args.play:
        return cmd_play(args.play, use_candidates=args.candidates, lump=args.lump)
    if args.render:
        return cmd_render(dict(args.expect), use_candidates=args.candidates)
    pack(use_candidates=args.candidates, first_lump=args.lump)
    return 0


if __name__ == "__main__":
    sys.exit(main())
