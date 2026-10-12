#!/usr/bin/env python3
"""In-engine smoke test: build the PK3, run GZDoom headless-ish, read the log.

This automates the manual evidence procedure documented in the G0 entry of
`docs/qa/GATE-REVIEWS.md`: launch GZDoom on the built PK3, let it reach the
map, take an engine screenshot (macOS `screencapture` cannot see the GZDoom
window) and quit by itself, then grep the log for the patterns that mean the
mod did not load cleanly.

Usage:
  python3 tools/smoke.py                       # MAP01, engine default skill
  python3 tools/smoke.py --map MAP01 --skill 4
  python3 tools/smoke.py --keep-evidence --phase F3 --slug g3-map01-skill4
  python3 tools/smoke.py --no-build            # use dist/sovietdoom.pk3 as is
  python3 tools/smoke.py --list-patterns       # print the failure contract

Exit codes (2/3/4 match `tools/run.sh` on purpose):
  0  clean run
  1  the log contains at least one failure pattern
  2  gzdoom not found / not executable
  3  IWAD not found
  4  build failed, or the PK3 is missing
  5  the engine did not exit within --timeout (process killed)
  6  the engine exited with a non-zero status
  7  the engine ran but never reached the map / never wrote a screenshot

NOT VERIFIED: whether GZDoom 4.14.2 supports a `-norun` early-exit switch.
We therefore use the console sequence that is proven in this project
(`+"wait N; screenshot; wait M; quit"`), with a hard timeout as the backstop.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# --- Exit codes ------------------------------------------------------------
EXIT_OK = 0
EXIT_LOG_FAILURES = 1
EXIT_NO_GZDOOM = 2
EXIT_NO_IWAD = 3
EXIT_BUILD_FAILED = 4
EXIT_TIMEOUT = 5
EXIT_ENGINE_FAILED = 6
EXIT_NO_MAP = 7


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOD_NAME = "sovietdoom"
DEFAULT_PK3 = PROJECT_ROOT / "dist" / f"{MOD_NAME}.pk3"
BUILD_SCRIPT = PROJECT_ROOT / "tools" / "build.py"

# Default (gitignored) output, so a routine run never dirties the repo.
DEFAULT_LOG = PROJECT_ROOT / "logs" / "smoke.log"
DEFAULT_SHOT_DIR = PROJECT_ROOT / "logs" / "shots"
# Dated evidence, only with --keep-evidence (project convention
# YYYY-MM-DD_HHMM_FN_slug.*, see docs/WORKING-AGREEMENTS.md).
EVIDENCE_DIR = PROJECT_ROOT / "docs" / "qa" / "evidence"
DEFAULT_PHASE = "F2"  # current phase per CLAUDE.md; pass --phase when it moves

# Engine timing, in tics (GZDoom runs at 35 tics/s).
TICS_PER_SECOND = 35
DEFAULT_WAIT_TICS = 140  # ~4 s: enough for the map to be drawn at least once
DEFAULT_SETTLE_TICS = 35  # ~1 s after the screenshot, so the PNG is flushed
DEFAULT_TIMEOUT_S = 120.0
TERMINATE_GRACE_S = 5.0

# --- The failure contract -------------------------------------------------
# Every pattern that makes a smoke run FAIL lives here and nowhere else, so
# this tuple *is* the contract QA enforces (referenced from
# docs/engine/MOD-SPEC.md 7). Entries: (id, regex, why it matters).
# Matching is per line, case-sensitive unless the regex says otherwise,
# because GZDoom's own messages are capitalised consistently.
LOG_FAILURE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("script-error", r"Script error",
     "ZScript / DECORATE / MAPINFO parse failure (this is how B1 showed up at G0)"),
    ("execution-stopped", r"Execution could not continue",
     "fatal abort: the engine gave up on a script"),
    ("unknown-texture", r"Unknown texture",
     "a TEXTMAP references a wall texture present in neither the PK3 nor the IWAD"),
    ("unknown-flat", r"Unknown flat",
     "a sector references a floor/ceiling flat that does not exist"),
    ("missing-sprite", r"Missing sprite",
     "an actor state points at a sprite frame/rotation that is not in the PK3"),
    ("unknown-property", r"Unknown property",
     "a definition lump uses a key this GZDoom build does not accept"),
    ("unknown-other", r"\bUnknown [A-Za-z]",
     "catch-all for the rest of GZDoom's 'Unknown <thing>' messages"),
    ("bad-thing", r"\bBad [A-Za-z]",
     "'Bad syntax', 'Bad override', 'Bad lumpnum'...: malformed data"),
    ("tried-to-find", r"(?i)\b(?:can(?:no|')t find|could not find|unable to find)\b",
     "a lump, actor or file the engine expected is absent"),
    ("fatal", r"(?i)\b(?:fatal error|segmentation fault|assertion failed)\b",
     "engine crash"),
    ("generic-error", r"(?i)\berrors?\b",
     "anything the engine itself calls an error"),
)

# Lines that match a failure pattern but are known-benign. Kept explicit and
# commented so nobody silences a real failure by editing the patterns above.
LOG_BENIGN_PATTERNS: tuple[tuple[str, str], ...] = (
    # The Vulkan driver dumps its whole extension list on one line; extension
    # names are vendor strings and must never be read as engine messages.
    ("vulkan-extensions", r"^Vulkan extensions:"),
    # Freedoom's own banner mentions the BSD licence and URLs, not errors.
    ("freedoom-banner", r"^(?:This is Freedoom|Freedoom is freely|    https://freedoom)"),
)

# Non-fatal but worth printing; --strict promotes them to failures.
LOG_WARNING_PATTERNS: tuple[tuple[str, str], ...] = (
    ("warning", r"(?i)\bwarnings?\b"),
    ("deprecated", r"(?i)\bdeprecated\b"),
)

# --- Log facts we extract for the summary ---------------------------------
RE_VERSION = re.compile(r"^GZDoom version (\S+)", re.M)
RE_ADDING = re.compile(r"^adding (.+?), (\d+) lumps", re.M)
RE_MAP_ENTERED = re.compile(r"^(MAP\w+|E\dM\d) - (.*)$", re.M)
RE_SCREENSHOT = re.compile(r"^Captured (\S+)", re.M)


class SmokeError(Exception):
    """Fatal condition with the exit code the CLI must return."""

    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LogHit:
    lineno: int  # 1-based, as a human reads the log
    pattern_id: str
    reason: str
    line: str

    def render(self) -> str:
        return f"  log:{self.lineno}  [{self.pattern_id}] {self.line.strip()}"


@dataclass
class LogReport:
    version: str | None = None
    loaded: list[tuple[str, int]] = field(default_factory=list)  # (path, lumps)
    map_entered: str | None = None
    map_title: str | None = None
    screenshot_name: str | None = None
    failures: list[LogHit] = field(default_factory=list)
    warnings: list[LogHit] = field(default_factory=list)

    @property
    def iwad(self) -> str | None:
        """First loaded .wad: GZDoom lists the IWAD before any -file."""
        for path, _lumps in self.loaded:
            if path.lower().endswith(".wad"):
                return path
        return None

    @property
    def mod_lumps(self) -> int | None:
        for path, lumps in self.loaded:
            if path.lower().endswith(f"{MOD_NAME}.pk3"):
                return lumps
        return None


# --- Locating the engine and the game data (same rules as tools/run.sh) ---

def gzdoom_candidates() -> list[Path]:
    return [
        Path("/Applications/GZDoom.app/Contents/MacOS/gzdoom"),
        Path.home() / "Applications/GZDoom.app/Contents/MacOS/gzdoom",
    ]


def find_gzdoom(explicit: str | None = None, env: dict[str, str] | None = None) -> Path:
    """Resolve the GZDoom binary; raise SmokeError(2) with advice if absent."""
    env = os.environ if env is None else env
    wanted = explicit or env.get("GZDOOM") or ""
    if wanted:
        path = Path(wanted)
        if path.is_file() and os.access(path, os.X_OK):
            return path
        raise SmokeError(f"GZDOOM={wanted} is not an executable file", EXIT_NO_GZDOOM)
    for cand in gzdoom_candidates():
        if cand.is_file() and os.access(cand, os.X_OK):
            return cand
    on_path = shutil.which("gzdoom", path=env.get("PATH"))
    if on_path:
        return Path(on_path)
    raise SmokeError(
        "gzdoom not found. Install it (brew install --cask gzdoom) or pass "
        "--gzdoom /path/to/gzdoom (or GZDOOM=...). Looked in: "
        + ", ".join(str(c) for c in gzdoom_candidates())
        + " and $PATH",
        EXIT_NO_GZDOOM,
    )


IWAD_NAMES = ("freedoom2.wad", "doom2.wad", "DOOM2.WAD")


def iwad_dirs(env: dict[str, str] | None = None, root: Path = PROJECT_ROOT) -> list[Path]:
    env = os.environ if env is None else env
    dirs = [root / "iwads", Path(env.get("HOME", "~")).expanduser() / "Library/Application Support/gzdoom"]
    doomwaddir = env.get("DOOMWADDIR")
    if doomwaddir:
        dirs.append(Path(doomwaddir))
    return dirs


def find_iwad(
    explicit: str | None = None,
    env: dict[str, str] | None = None,
    root: Path = PROJECT_ROOT,
) -> Path:
    """Resolve the IWAD, preferring freedoom2.wad (D2); SmokeError(3) if absent."""
    env = os.environ if env is None else env
    wanted = explicit or env.get("IWAD") or ""
    if wanted:
        path = Path(wanted)
        if path.is_file():
            return path
        raise SmokeError(f"IWAD={wanted} does not exist", EXIT_NO_IWAD)
    for directory in iwad_dirs(env, root):
        if not directory.is_dir():
            continue
        for name in IWAD_NAMES:
            cand = directory / name
            if cand.is_file():
                return cand
    raise SmokeError(
        "no IWAD found (looked for "
        + " / ".join(IWAD_NAMES)
        + " in "
        + ", ".join(str(d) for d in iwad_dirs(env, root))
        + "). Pass --iwad /path/to/file.wad (or IWAD=...)",
        EXIT_NO_IWAD,
    )


# --- Command line fed to the engine ---------------------------------------

def console_sequence(wait_tics: int, settle_tics: int, screenshot: bool) -> str:
    """The proven self-quitting console sequence (one argv element)."""
    steps = [f"wait {wait_tics}"]
    if screenshot:
        steps += ["screenshot", f"wait {settle_tics}"]
    steps.append("quit")
    return "+" + "; ".join(steps)


def build_command(
    gzdoom: Path,
    iwad: Path,
    pk3: Path,
    log: Path,
    shot_dir: Path,
    map_name: str = "MAP01",
    skill: int | None = None,
    wait_tics: int = DEFAULT_WAIT_TICS,
    settle_tics: int = DEFAULT_SETTLE_TICS,
    screenshot: bool = True,
    sound: bool = False,
    extra: list[str] | None = None,
) -> list[str]:
    """Assemble the argv, mirroring the order proven in tools/run.sh."""
    argv = [str(gzdoom), "-iwad", str(iwad), "-file", str(pk3), "+logfile", str(log)]
    if skill is not None:
        argv += ["-skill", str(skill)]
    argv += ["+map", map_name]
    if not sound:
        argv.append("-nosound")
    # Windowed, so the run never steals the whole screen from whoever is working.
    argv += ["+vid_fullscreen", "0"]
    if screenshot:
        argv += ["+screenshot_dir", str(shot_dir)]
    argv.append(console_sequence(wait_tics, settle_tics, screenshot))
    argv += list(extra or [])
    return argv


# --- Log analysis ----------------------------------------------------------

def _compiled(patterns):
    """Compile a pattern table once; the regexes never change at runtime."""
    return [(pid, re.compile(rx), *rest) for pid, rx, *rest in patterns]


_FAILURES = _compiled(LOG_FAILURE_PATTERNS)
_BENIGN = _compiled(LOG_BENIGN_PATTERNS)
_WARNINGS = _compiled(LOG_WARNING_PATTERNS)


def is_benign(line: str) -> bool:
    return any(rx.search(line) for _pid, rx in _BENIGN)


def scan_log(text: str, strict: bool = False) -> LogReport:
    """Extract the facts and every failure/warning hit, with line numbers."""
    report = LogReport()

    match = RE_VERSION.search(text)
    if match:
        report.version = match.group(1)
    report.loaded = [(path, int(lumps)) for path, lumps in RE_ADDING.findall(text)]
    entered = RE_MAP_ENTERED.search(text)
    if entered:
        report.map_entered = entered.group(1)
        report.map_title = entered.group(2).strip()
    shot = RE_SCREENSHOT.search(text)
    if shot:
        report.screenshot_name = shot.group(1)

    failures, warnings = _FAILURES, _WARNINGS
    for index, line in enumerate(text.splitlines(), start=1):
        if is_benign(line):
            continue
        for pid, rx, reason in failures:
            if rx.search(line):
                report.failures.append(LogHit(index, pid, reason, line))
                break
        else:
            for pid, rx in warnings:
                if rx.search(line):
                    hit = LogHit(index, pid, "engine warning", line)
                    (report.failures if strict else report.warnings).append(hit)
                    break
    return report


# --- Running the engine ----------------------------------------------------

@dataclass
class RunResult:
    returncode: int | None
    timed_out: bool
    seconds: float


def run_engine(argv: list[str], timeout_s: float, cwd: Path = PROJECT_ROOT) -> RunResult:
    """Run GZDoom, killing the whole process group if it overruns the timeout."""
    started = time.monotonic()
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,  # own process group, so nothing survives a kill
    )
    try:
        proc.wait(timeout=timeout_s)
        return RunResult(proc.returncode, False, time.monotonic() - started)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        return RunResult(None, True, time.monotonic() - started)
    except KeyboardInterrupt:
        _kill_group(proc)
        raise


def _kill_group(proc: subprocess.Popen) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=TERMINATE_GRACE_S)
            return
        except subprocess.TimeoutExpired:
            continue


def run_build(quiet: bool = True) -> None:
    cmd = [sys.executable, str(BUILD_SCRIPT)] + (["--quiet"] if quiet else [])
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if proc.returncode != 0:
        raise SmokeError("build failed (python3 tools/build.py)", EXIT_BUILD_FAILED)


# --- Evidence --------------------------------------------------------------

def evidence_stem(phase: str, slug: str, when: datetime | None = None) -> str:
    """YYYY-MM-DD_HHMM_FN_slug, the project's dated-document convention."""
    when = when or datetime.now()
    return f"{when:%Y-%m-%d_%H%M}_{phase}_{slug}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tools/smoke.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--map", default="MAP01", help="map lump to load (default: MAP01)")
    parser.add_argument("--skill", type=int, choices=range(1, 6),
                        help="skill 1..5 (default: the engine's own)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S,
                        help=f"hard timeout in seconds (default: {DEFAULT_TIMEOUT_S:g})")
    parser.add_argument("--wait", type=int, default=DEFAULT_WAIT_TICS,
                        help=f"tics in the map before the screenshot (default: {DEFAULT_WAIT_TICS})")
    parser.add_argument("--settle", type=int, default=DEFAULT_SETTLE_TICS,
                        help=f"tics after the screenshot before quit (default: {DEFAULT_SETTLE_TICS})")
    parser.add_argument("--no-screenshot", action="store_true", help="load and quit, no PNG")
    parser.add_argument("--sound", action="store_true", help="do not pass -nosound")
    parser.add_argument("--no-build", action="store_true", help="use the existing PK3")
    parser.add_argument("--pk3", default=str(DEFAULT_PK3), help="PK3 to load")
    parser.add_argument("--gzdoom", help="GZDoom binary (else $GZDOOM, else the usual places)")
    parser.add_argument("--iwad", help="IWAD file (else $IWAD, else iwads/)")
    parser.add_argument("--strict", action="store_true", help="treat engine warnings as failures")
    parser.add_argument("--keep-evidence", action="store_true",
                        help=f"also copy log and screenshot to {EVIDENCE_DIR.relative_to(PROJECT_ROOT)}/")
    parser.add_argument("--phase", default=DEFAULT_PHASE, help="phase tag for the evidence name")
    parser.add_argument("--slug", help="slug for the evidence name (default: smoke-<map>[-skill<N>])")
    parser.add_argument("--list-patterns", action="store_true",
                        help="print the failure contract and exit")
    parser.add_argument("extra", nargs="*", help="extra args passed straight to gzdoom")
    return parser.parse_args(argv)


def print_patterns() -> None:
    print("Failure patterns (a match on any non-benign log line fails the run):")
    for pid, rx, reason in LOG_FAILURE_PATTERNS:
        print(f"  {pid:<18} /{rx}/\n{'':<22}{reason}")
    print("\nBenign (never counted):")
    for pid, rx in LOG_BENIGN_PATTERNS:
        print(f"  {pid:<18} /{rx}/")
    print("\nWarnings (printed; failures only with --strict):")
    for pid, rx in LOG_WARNING_PATTERNS:
        print(f"  {pid:<18} /{rx}/")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_patterns:
        print_patterns()
        return EXIT_OK

    try:
        gzdoom = find_gzdoom(args.gzdoom)
        iwad = find_iwad(args.iwad)
        if not args.no_build:
            run_build()
        pk3 = Path(args.pk3)
        if not pk3.is_file():
            raise SmokeError(f"{pk3} missing; run python3 tools/build.py", EXIT_BUILD_FAILED)
    except SmokeError as exc:
        print(f"smoke: {exc}", file=sys.stderr)
        return exc.code

    log_path = DEFAULT_LOG
    shot_dir = DEFAULT_SHOT_DIR
    log_path.parent.mkdir(parents=True, exist_ok=True)
    shot_dir.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        log_path.unlink()
    before = {p.name for p in shot_dir.glob("*.png")}

    command = build_command(
        gzdoom, iwad, pk3, log_path, shot_dir,
        map_name=args.map, skill=args.skill,
        wait_tics=args.wait, settle_tics=args.settle,
        screenshot=not args.no_screenshot, sound=args.sound,
        extra=args.extra,
    )
    print(f"gzdoom : {gzdoom}")
    print(f"iwad   : {iwad}")
    print(f"pk3    : {pk3}")
    print(f"log    : {log_path}")
    print(f"args   : {' '.join(command[1:])}")

    result = run_engine(command, args.timeout)
    print(f"engine : exit {result.returncode} in {result.seconds:.1f}s"
          + (" (TIMED OUT, killed)" if result.timed_out else ""))

    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    report = scan_log(text, strict=args.strict)

    shot_path: Path | None = None
    new_shots = sorted(p for p in shot_dir.glob("*.png") if p.name not in before)
    if new_shots:
        shot_path = new_shots[-1]

    # --- Summary ----------------------------------------------------------
    print("\n--- smoke summary ---")
    print(f"gzdoom version : {report.version or 'UNKNOWN (no version line in the log)'}")
    print(f"iwad loaded    : {report.iwad or 'UNKNOWN'}")
    print(f"mod lumps      : {report.mod_lumps if report.mod_lumps is not None else 'UNKNOWN'}")
    for path, lumps in report.loaded:
        print(f"  loaded       : {path} ({lumps} lumps)")
    print(f"map            : {report.map_entered or 'NOT REACHED'}"
          + (f" - {report.map_title}" if report.map_title else ""))
    print(f"screenshot     : {shot_path if shot_path else 'none'}")
    print(f"log lines      : {len(text.splitlines())}")

    if report.warnings:
        print(f"warnings       : {len(report.warnings)}")
        for hit in report.warnings:
            print(hit.render())

    if report.failures:
        print(f"FAILURES       : {len(report.failures)}")
        for hit in report.failures:
            print(hit.render())
    else:
        print("failures       : none")

    if args.keep_evidence:
        slug = args.slug or f"smoke-{args.map.lower()}" + (f"-skill{args.skill}" if args.skill else "")
        stem = evidence_stem(args.phase, slug)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        if log_path.exists():
            kept_log = EVIDENCE_DIR / f"{stem}.log"
            shutil.copy2(log_path, kept_log)
            print(f"evidence log   : {kept_log}")
        if shot_path:
            kept_shot = EVIDENCE_DIR / f"{stem}.png"
            shutil.copy2(shot_path, kept_shot)
            print(f"evidence shot  : {kept_shot}")

    # --- Verdict ----------------------------------------------------------
    if result.timed_out:
        print(f"\nVERDICT: FAIL - engine still alive after {args.timeout:g}s, process killed")
        return EXIT_TIMEOUT
    if report.failures:
        print(f"\nVERDICT: FAIL - {len(report.failures)} failure line(s) in the log")
        return EXIT_LOG_FAILURES
    if result.returncode not in (0, None):
        print(f"\nVERDICT: FAIL - engine exited {result.returncode}")
        return EXIT_ENGINE_FAILED
    if report.map_entered is None:
        print("\nVERDICT: FAIL - the engine never reported entering a map")
        return EXIT_NO_MAP
    if not args.no_screenshot and shot_path is None:
        print("\nVERDICT: FAIL - no screenshot was written")
        return EXIT_NO_MAP
    print("\nVERDICT: PASS")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
