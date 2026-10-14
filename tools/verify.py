#!/usr/bin/env python3
"""One entry point for verification, with a level that matches the change.

    python3 tools/verify.py fast     # seconds, never opens a window
    python3 tools/verify.py full     # everything, including GZDoom
    python3 tools/verify.py auto     # read git, pick the level, say why
    python3 tools/verify.py docs --gate   # phase close: every mirror present

Why this exists: `docs/PIPELINE.md` stage 5 used to be four separate
commands, and the slowest of them (`tools/smoke.py`) boots a real GZDoom and
puts a window on screen. Running it after a documentation edit costs the
person at the keyboard a stolen screen for nothing. The CEO, 2026-10-13:
"no paran de abrirseme pantallas [...] habria que poder hacer que QA tenga
criterio de cuando lanzar tests y cuando no; o bien hacer una pasada fast y
otra full."

The levels are a true ladder: each one contains the one below it.

    docs   Russian mirror (D34) + repo-path references in the changed
           documents. No build, no suite, no engine.             ~0.1 s
    fast   build + check_pk3 + the suite's FAST tier. No window. ~15 s
    art    build + check_pk3 + EVERY test. Still no window.     ~110 s
    full   art, plus tools/smoke.py on every map. Opens GZDoom.

What the suite runs at each level is decided in ONE place,
`tests/_tiers.py` (the runner this script calls instead of a bare
`unittest discover`):

    fast   every discovered test EXCEPT the SLOW table in tests/_tiers.py,
           with SD_SKIP_SLOW_ART=1 for the files that read that switch.
           What stays: the build and check_pk3 tests, every text/contract
           test (LANGUAGE, MAPINFO, ZScript, UDMF, MENUDEF, licences,
           verify itself), the map plans, the cheap generator contracts.
    art    every discovered test, SD_SKIP_SLOW_ART unset. On top of fast:
           art and sound generator renders, the rig, release end to end,
           the draft overlay, work/ scans (test_art's work/ identity,
           test_audition's work/audio guard), gzdoom.pk3 reads, MAP01/RANGE
           sight-line geometry, route.MapData, whole-PK3 re-checks.
    full   the same suite as art (plus the engine smoke).

Nothing runs only at fast: fast + (art only) = every discovered test;
`python tests/_tiers.py --list` prints that count. The runner also keeps a
per-process PK3 build cache keyed by the content of src/, assets/ and
tools/ (bypassed for tests/test_build.py), so the many tests that build
the same PK3 build it once.

Measured on the Windows PC 2026-10-14 (other agents running): fast went
from ~100 s (1595 tests, all in one tier) to ~15 s; art is the old fast plus
the slow art runs. See docs/qa/COVERAGE.md "Test tiers".

`auto` classifies every path git reports as changed, takes the highest level
any of them demands, and prints the rule and the reason before running
anything, so the decision is auditable and the CEO can disagree with it.
Use `--explain` to see the plan without executing it.

The Russian mirror (D7, amended by D34 on 2026-10-13): `docs/ru/` is synced
in a batch when a phase closes and in full before a release, not in the same
task. So between gates a document without its `docs/ru/` twin is a WARNING
at every level and never blocks. `--gate` is for the phase close: it scans
the whole `docs/` tree, whatever changed, and any document without its twin
fails the docs stage (exit 10). It checks that the twin exists, not that it
is up to date; freshness is the translator's and `pmo`'s to judge. `--gate`
changes only the docs stage: the level, and what `auto` decides, are the
same with or without it.

In-game text is not covered by D34 and stays bilingual in every task (D21).
That check is not repeated here: `tests/test_language.py`
(`test_every_mod_id_is_translated`) runs in the suite at fast, art and full,
and a `docs`-level batch cannot have touched `src/lumps/LANGUAGE`, because
any `src/` path lifts `auto` to full.

Exit codes - one per stage, so a wrapper can tell them apart:

    0   everything the level asked for passed
    2   usage error (unknown level, bad argument)
    3   `auto` could not ask git what changed
    10  the documentation check failed (a missing mirror: only with --gate)
    11  tools/build.py failed
    12  tools/check_pk3.py failed
    13  the test suite failed
    14  tools/smoke.py failed (the engine; the smoke exit code is printed)

This script never fixes anything and never commits (D6). Python 3 standard
library only, like everything else in tools/.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
TESTS_DIR = PROJECT_ROOT / "tests"
TIERS_RUNNER = TESTS_DIR / "_tiers.py"  # which test runs at fast vs art, and the runner
DOCS_DIR = PROJECT_ROOT / "docs"
RU_DIR = DOCS_DIR / "ru"
MAPS_DIR = PROJECT_ROOT / "src" / "maps"
# The project venv's interpreter: the POSIX layout (the Mac the project
# started on) or the Windows one (the CEO's PC since 2026-10-13), whichever
# exists. The first is also the name quoted in docs when neither does.
_VENV_CANDIDATES = (PROJECT_ROOT / ".venv" / "bin" / "python",
                    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
VENV_PYTHON = next((p for p in _VENV_CANDIDATES if p.is_file()), _VENV_CANDIDATES[0])

# --- Exit codes ------------------------------------------------------------
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_GIT = 3
EXIT_DOCS = 10
EXIT_BUILD = 11
EXIT_CHECK_PK3 = 12
EXIT_TESTS = 13
EXIT_ENGINE = 14


class Level(IntEnum):
    """Verification depth. Higher contains lower; `auto` takes the maximum."""

    DOCS = 0
    FAST = 1
    ART = 2
    FULL = 3

    @property
    def label(self) -> str:
        return self.name.lower()


LEVEL_BY_NAME = {level.label: level for level in Level}


# --- The decision table ----------------------------------------------------
# Order matters: the FIRST rule whose prefix matches a path wins, so the
# specific entries (tools/build.py, tools/art/) come before the general one
# (tools/). Every rule carries the sentence `auto` prints as its reason; if
# you cannot write that sentence, the rule does not belong here.

@dataclass(frozen=True)
class Rule:
    id: str
    prefixes: tuple[str, ...]  # path prefixes, POSIX, relative to the repo root
    level: Level
    why: str
    suffixes: tuple[str, ...] = ()  # matched on the basename, for root files


RULES: tuple[Rule, ...] = (
    Rule(
        "engine-src", ("src/",), Level.FULL,
        "only GZDoom parses ZScript, UDMF and the definition lumps; a bad "
        "property or a missing actor appears in no static check",
    ),
    Rule(
        "packer", ("tools/build.py", "tools/sdbuild/"), Level.FULL,
        "the packer decides what reaches the engine, and a wrong lump name "
        "or layout is only fatal at load time",
    ),
    Rule(
        "art", ("assets/", "tools/art/", "tools/audio/"), Level.ART,
        "art and audio can only break the package: check_pk3 already proves "
        "palette, size, naming and references, so the engine adds nothing a "
        "validator has not already seen",
    ),
    Rule(
        "tooling", ("tests/", "tools/", ".github/", ".coveragerc", ".gitignore"), Level.FAST,
        "tooling and tests: the suite is the thing under test, and none of "
        "it is packed into the PK3",
    ),
    Rule(
        "docs", ("docs/", "work/", ".claude/", "LICENSE.md"), Level.DOCS,
        "documentation and scratch work: nothing here is built, packed or "
        "parsed by the engine",
        suffixes=(".md",),
    ),
)

# Anything no rule claims. The safe answer to "I do not know what this is"
# is the most expensive level, not the cheapest.
UNKNOWN_RULE = Rule(
    "unknown", (), Level.FULL,
    "no rule covers this path, and the safe default for an unknown change "
    "is the highest level",
)

# Root-level documents. They carry their Russian text inline (README.md) or
# are not mirrored at all (CLAUDE.md, LICENSE.md), so they never demand a
# docs/ru/ twin; see "The documentation check" in docs/PIPELINE.md.
ROOT_DOCS = ("README.md", "CLAUDE.md", "LICENSE.md")

RULE_BY_ID = {rule.id: rule for rule in RULES}


def normalise(path: str) -> str:
    """Repo-relative POSIX form. NOT str.lstrip('./'): that eats the leading
    dot of `.github/` and `.coveragerc` and sends them to the unknown rule,
    which would boot GZDoom for a workflow edit."""
    clean = str(path).strip().replace("\\", "/")
    while clean.startswith("./"):
        clean = clean[2:]
    return clean


def classify(path: str) -> Rule:
    """Map one repo-relative POSIX path to the rule that governs it."""
    clean = normalise(path)
    if not clean:
        return UNKNOWN_RULE
    if clean in ROOT_DOCS:
        return RULE_BY_ID["docs"]
    for rule in RULES:
        for prefix in rule.prefixes:
            if clean == prefix or clean.startswith(prefix.rstrip("/") + "/"):
                return rule
        if "/" not in clean and any(clean.endswith(s) for s in rule.suffixes):
            return rule
    return UNKNOWN_RULE


# Paths that are noise, not work: editor droppings and compiled bytecode.
IGNORED_BASENAMES = (".DS_Store",)
IGNORED_FRAGMENTS = ("__pycache__/",)


def is_noise(path: str) -> bool:
    return (
        path.rsplit("/", 1)[-1] in IGNORED_BASENAMES
        or any(frag in path for frag in IGNORED_FRAGMENTS)
        or path.endswith(".pyc")
    )


# A map folder is named after its lump: up to 8 upper-case letters, digits or
# underscores (MOD-SPEC 3). Not only MAPxx / ExMy: since D62 the practice
# range is the lump RANGE.
RE_MAP_PATH = re.compile(r"^src/maps/([A-Z0-9_]{1,8})(?:/|$)")


def discover_maps(maps_dir: Path = MAPS_DIR) -> tuple[str, ...]:
    """Every map the build can produce, from src/maps/<NAME>/."""
    if not maps_dir.is_dir():
        return ()
    names = sorted(
        d.name for d in maps_dir.iterdir()
        if d.is_dir() and RE_MAP_PATH.match(f"src/maps/{d.name}")
    )
    return tuple(names)


@dataclass(frozen=True)
class Reason:
    rule: Rule
    example: str
    count: int

    def render(self) -> str:
        more = f" (+{self.count - 1} more)" if self.count > 1 else ""
        return f"  {self.example}{more}\n      -> {self.rule.level.label}: {self.rule.why}"


@dataclass(frozen=True)
class Decision:
    level: Level
    reasons: tuple[Reason, ...]
    maps: tuple[str, ...]
    paths: tuple[str, ...]
    ignored: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.paths


def decide(paths, all_maps: tuple[str, ...] = ()) -> Decision:
    """Pick the level for a set of changed paths and say why.

    This is the whole point of the tool, so it is a pure function of the
    path list: tests/test_verify.py drives it with synthetic lists.
    """
    kept: list[str] = []
    ignored: list[str] = []
    for raw in paths:
        clean = normalise(raw)
        if not clean:
            continue
        (ignored if is_noise(clean) else kept).append(clean)

    if not kept:
        return Decision(Level.DOCS, (), (), (), tuple(sorted(set(ignored))))

    by_rule: dict[str, list[str]] = {}
    rules: dict[str, Rule] = {}
    for path in kept:
        rule = classify(path)
        by_rule.setdefault(rule.id, []).append(path)
        rules[rule.id] = rule

    level = max(rules[rid].level for rid in rules)

    # Reasons: the rules that actually set the level first, then the rest,
    # so the top line of the explanation is the one that cost the time.
    ordered = sorted(
        rules.values(),
        key=lambda r: (-int(r.level), r.id),
    )
    reasons = tuple(
        Reason(rule, sorted(by_rule[rule.id])[0], len(by_rule[rule.id]))
        for rule in ordered
    )

    maps = engine_maps(kept, all_maps) if level is Level.FULL else ()
    return Decision(level, reasons, maps, tuple(sorted(set(kept))), tuple(sorted(set(ignored))))


def engine_maps(paths, all_maps: tuple[str, ...]) -> tuple[str, ...]:
    """Which maps the smoke stage must load.

    If every path that forces the engine lives under src/maps/, only those
    maps need booting. Anything else (ZScript, a lump, the packer) is global
    and every map has to be loaded again.
    """
    forcing = [p for p in paths if classify(p).level is Level.FULL]
    named: list[str] = []
    for path in forcing:
        match = RE_MAP_PATH.match(path)
        if match:
            named.append(match.group(1))
        else:
            return all_maps  # a global change: no shortcut
    if not named:
        return all_maps
    return tuple(sorted(set(named)))


# --- What git says changed -------------------------------------------------

def _git(args: list[str], root: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(root),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def parse_porcelain(data: str) -> list[str]:
    """Paths out of `git status --porcelain=v1 -z -uall`.

    NUL-separated records of `XY <path>`; a rename or copy is followed by a
    second, bare record holding the ORIGINAL path. Both sides of a rename
    count as changed, so both are returned.
    """
    records = [r for r in data.split("\0") if r]
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4 or record[2] != " ":
            # Not a status record (this is the original path of a rename
            # that we already consumed, or output we do not understand).
            paths.append(record)
            continue
        status, path = record[:2], record[3:]
        paths.append(path)
        if "R" in status or "C" in status:
            if index < len(records):
                paths.append(records[index])
                index += 1
    return [p for p in paths if p]


def changed_paths(root: Path = PROJECT_ROOT, since: str | None = None) -> list[str]:
    """Everything git considers changed: working tree, index and untracked."""
    if since:
        out = _git(["diff", "--name-only", "-z", since], root)
        return [p for p in out.split("\0") if p]
    out = _git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], root)
    return parse_porcelain(out)


# --- The documentation check ----------------------------------------------
# D7 as amended by D34: every English document under docs/ has a Russian
# mirror at the same path under docs/ru/, synced in a batch at each phase
# close. Whether the twin EXISTS is the one part a script can check; the rest
# (one owner per fact, D-numbers, evidence paths) belongs to the `pmo` agent
# at stage 6 and is not duplicated here. Between gates a gap is a warning;
# with --gate it fails the stage.

def mirror_path(path: str) -> str | None:
    """docs/x/y.md -> docs/ru/x/y.md, and back. None when no mirror is owed."""
    if not path.endswith(".md"):
        return None
    if path.startswith("docs/ru/"):
        return "docs/" + path[len("docs/ru/"):]
    if path.startswith("docs/"):
        return "docs/ru/" + path[len("docs/"):]
    return None


def mirror_gaps(paths, root: Path = PROJECT_ROOT) -> list[str]:
    """Documents whose mirror twin is missing, as `a.md -> b.md` lines.

    Both directions: an English document without its Russian twin, and a
    Russian page whose English source is gone (renamed or deleted without
    the mirror following).
    """
    gaps: list[str] = []
    for path in sorted(set(paths)):
        twin = mirror_path(path)
        if twin is None or not (root / path).is_file():
            continue
        if not (root / twin).is_file():
            gaps.append(f"{path} -> {twin}")
    return gaps


def all_docs(root: Path = PROJECT_ROOT) -> list[str]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    return sorted(
        p.relative_to(root).as_posix()
        for p in docs.rglob("*.md")
        if p.is_file()
    )


RE_BACKTICK_PATH = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*/[A-Za-z0-9_./-]+)`")
# Only check references that point at trees we own and that name a real file
# extension or an existing directory; a backtick is also how this project
# writes shell fragments and lump names, and those are not paths.
REFERENCE_ROOTS = ("docs/", "src/", "tools/", "tests/", "assets/", ".github/")


def broken_references(paths, root: Path = PROJECT_ROOT) -> list[str]:
    """Repo paths quoted in the changed documents that do not exist.

    Warning-level on purpose: a document may legitimately name a path that
    is about to exist. It is here because a dead path in a document is how
    an agent ends up reading the wrong file.
    """
    broken: list[str] = []
    for path in sorted(set(paths)):
        if not path.endswith(".md"):
            continue
        source = root / path
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for ref in sorted(set(RE_BACKTICK_PATH.findall(text))):
            if not ref.startswith(REFERENCE_ROOTS):
                continue
            if "*" in ref or ref.endswith("/"):
                continue
            target = root / ref
            if not target.exists():
                broken.append(f"{path}: `{ref}`")
    return broken


# --- Stage running ---------------------------------------------------------

@dataclass
class StageResult:
    name: str
    ok: bool
    seconds: float
    note: str = ""
    output: str = ""
    exit_code: int = 0


@dataclass
class Plan:
    level: Level
    docs_check: bool
    build: bool
    check_pk3: bool
    tests: bool
    slow_art: bool
    engine: bool
    maps: tuple[str, ...]
    doc_paths: tuple[str, ...] = ()  # empty means "scan the whole docs/ tree"
    engine_tests: bool = False
    gate: bool = False  # phase close (D34): whole tree, a missing mirror fails
    stages: tuple[str, ...] = field(default_factory=tuple)


def plan_for(level: Level, maps: tuple[str, ...] = (), doc_paths: tuple[str, ...] = (),
             engine_tests: bool = False, gate: bool = False) -> Plan:
    """The ladder, written once.

    `gate` touches the docs stage only: it widens the scan to the whole
    docs/ tree (a phase close audits the mirror, not the batch) and makes a
    missing mirror fail. Every other stage is the level's own.
    """
    plan = Plan(
        level=level,
        docs_check=True,
        build=level >= Level.FAST,
        check_pk3=level >= Level.FAST,
        tests=level >= Level.FAST,
        slow_art=level >= Level.ART,
        engine=level >= Level.FULL,
        maps=maps,
        doc_paths=() if gate else doc_paths,
        engine_tests=engine_tests,
        gate=gate,
    )
    names = ["docs --gate" if gate else "docs"]
    if plan.build:
        names.append("build")
    if plan.check_pk3:
        names.append("check_pk3")
    if plan.tests:
        names.append("tests+slow-art" if plan.slow_art else "tests")
    if plan.engine:
        names.append("smoke " + (" ".join(plan.maps) if plan.maps else "(no map found)"))
    plan.stages = tuple(names)
    return plan


def pick_python(explicit: str | None = None) -> str:
    """.venv/bin/python when it exists: without Pillow the art tests skip."""
    if explicit:
        return explicit
    if VENV_PYTHON.is_file() and os.access(VENV_PYTHON, os.X_OK):
        return str(VENV_PYTHON)
    return sys.executable


def _run(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, float]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    except OSError as exc:
        # A missing interpreter or tool is a red stage with a readable
        # reason, not a traceback out of a verification tool.
        return 127, f"could not run {' '.join(cmd)}: {exc}", time.monotonic() - started
    return proc.returncode, proc.stdout, time.monotonic() - started


RE_CHECK_COUNTS = re.compile(r"(\d+) error\(s\), (\d+) warning\(s\)")
RE_TESTS_RAN = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s", re.M)
RE_TESTS_TAIL = re.compile(r"^(OK|FAILED)(?: \((.*)\))?$", re.M)
RE_SMOKE_VERDICT = re.compile(r"^VERDICT: (\w+)(.*)$", re.M)
RE_TIER_DEFERRED = re.compile(r"^tier fast: \d+ of \d+ tests \((\d+) deferred", re.M)
RE_TIER_STALE = re.compile(r"^WARNING: tests/_tiers\.py SLOW entry '([^']+)'", re.M)


def stage_docs(plan: Plan, root: Path = PROJECT_ROOT) -> StageResult:
    """Russian mirror and quoted repo paths.

    D34 (2026-10-13, amends D7): the mirror is batch work done at a phase
    close, so a missing twin is a warning here, even for a document changed
    in this very batch; only `--gate` turns it into a failure (EXIT_DOCS).
    Dead path references are always a warning.
    """
    name ="docs --gate" if plan.gate else "docs"
    started = time.monotonic()
    scoped = bool(plan.doc_paths) and not plan.gate
    paths = list(plan.doc_paths) if scoped else all_docs(root)
    gaps = mirror_gaps(paths, root)
    broken = broken_references(paths, root)
    seconds = time.monotonic() - started

    lines = []
    if gaps:
        if plan.gate:
            lines.append("Russian mirror missing (D34: the phase-close gate needs every twin):")
        else:
            lines.append("Russian mirror missing (D34: owed at the phase close, not now; "
                         "`verify.py docs --gate` fails on these):")
        lines += [f"  {g}" for g in gaps]
    if broken:
        lines.append("repo paths quoted in these documents do not exist:")
        lines += [f"  {b}" for b in broken]
    output = "\n".join(lines)

    if plan.gate and gaps:
        return StageResult(name, False, seconds,
                           f"{len(gaps)} doc(s) without a Russian mirror (D34 gate)",
                           output, EXIT_DOCS)
    note_bits = []
    if plan.gate:
        english = sum(1 for p in paths if not p.startswith("docs/ru/"))
        note_bits.append(f"{english} English doc(s), every Russian mirror present")
    if gaps:
        note_bits.append(f"WARN {len(gaps)} doc(s) without a Russian mirror (D34: due at phase close)")
    if broken:
        note_bits.append(f"WARN {len(broken)} dead path reference(s)")
    if not note_bits:
        note_bits.append(f"{len(paths)} document(s), mirrors and references OK")
    return StageResult(name, True, seconds, "; ".join(note_bits), output, EXIT_DOCS)


def stage_build(python: str) -> StageResult:
    code, out, secs = _run([python, str(TOOLS_DIR / "build.py"), "--quiet"])
    note = "dist/sovietdoom.pk3" if code == 0 else f"build.py exit {code}"
    return StageResult("build", code == 0, secs, note, out, EXIT_BUILD)


def stage_check_pk3(python: str) -> StageResult:
    code, out, secs = _run([python, str(TOOLS_DIR / "check_pk3.py"), "--quiet"])
    match = RE_CHECK_COUNTS.search(out)
    note = (f"{match.group(1)} error(s), {match.group(2)} warning(s)" if match
            else f"check_pk3.py exit {code}")
    return StageResult("check_pk3", code == 0, secs, note, out, EXIT_CHECK_PK3)


def stage_tests(python: str, slow_art: bool, engine_tests: bool) -> StageResult:
    env = dict(os.environ)
    if slow_art:
        env.pop("SD_SKIP_SLOW_ART", None)
    else:
        env["SD_SKIP_SLOW_ART"] = "1"
    if engine_tests:
        env["SD_ENGINE_TESTS"] = "1"
    else:
        env.pop("SD_ENGINE_TESTS", None)
    # tests/_tiers.py is `unittest discover -s tests` plus the tier table and
    # a per-process PK3 build cache; `art` runs every discovered test.
    tier = "art" if slow_art else "fast"
    code, out, secs = _run([python, str(TIERS_RUNNER), tier], env)
    ran = RE_TESTS_RAN.search(out)
    tail = RE_TESTS_TAIL.search(out)
    note = f"{ran.group(1)} tests" if ran else f"unittest exit {code}"
    if tail and tail.group(2):
        note += f", {tail.group(2)}"
    if not slow_art:
        deferred = RE_TIER_DEFERRED.search(out)
        note += (f" ({deferred.group(1)} slow ones deferred to art)" if deferred
                 else " (slow art skipped)")
    stale = RE_TIER_STALE.findall(out)
    if stale:
        note += f"; WARN {len(stale)} stale SLOW entr{'y' if len(stale) == 1 else 'ies'} in tests/_tiers.py"
    return StageResult("tests", code == 0, secs, note, out, EXIT_TESTS)


def stage_smoke(python: str, map_name: str, wait: int | None, extra: list[str]) -> StageResult:
    cmd = [python, str(TOOLS_DIR / "smoke.py"), "--map", map_name, "--no-build"]
    if wait is not None:
        cmd += ["--wait", str(wait)]
    cmd += extra
    code, out, secs = _run(cmd)
    verdict = RE_SMOKE_VERDICT.search(out)
    note = (verdict.group(1) + verdict.group(2)).strip() if verdict else f"smoke exit {code}"
    return StageResult(f"smoke {map_name}", code == 0, secs, note, out, EXIT_ENGINE)


# --- Reporting -------------------------------------------------------------

def print_decision(decision: Decision, plan: Plan) -> None:
    """Say what is about to happen and why, before anything happens."""
    if decision.is_empty:
        print("auto: git reports no changes"
              + (f" ({len(decision.ignored)} ignored: editor/bytecode noise)" if decision.ignored else ""))
    else:
        noise = f", {len(decision.ignored)} ignored" if decision.ignored else ""
        print(f"auto: {len(decision.paths)} changed path(s){noise}")
        for reason in decision.reasons:
            print(reason.render())
    print(f"plan: {plan.level.label} -> " + ", ".join(plan.stages))


def print_header(plan: Plan, python: str) -> None:
    interpreter = Path(python).name
    if Path(python) == VENV_PYTHON:
        interpreter = ".venv/" + VENV_PYTHON.relative_to(PROJECT_ROOT / ".venv").as_posix()
    print(f"verify {plan.level.label}  ({interpreter})")


def print_stage(result: StageResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    note = f"   {result.note}" if result.note else ""
    print(f"  {result.name:<14} {status}  {result.seconds:5.1f}s{note}")


# --- CLI -------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tools/verify.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("level", nargs="?", default="auto",
                        choices=[*LEVEL_BY_NAME, "auto"],
                        help="docs | fast | art | full | auto (default: auto)")
    parser.add_argument("--gate", action="store_true",
                        help="phase close (D34): scan all of docs/ and FAIL the docs stage on any "
                             "document without its docs/ru/ mirror (default: warn only)")
    parser.add_argument("--explain", action="store_true",
                        help="print the plan and the reasons, run nothing")
    parser.add_argument("--since", metavar="REF",
                        help="auto: compare against REF (git diff) instead of the working tree")
    parser.add_argument("--files", nargs="*", metavar="PATH",
                        help="auto: classify these paths instead of asking git")
    parser.add_argument("--maps", metavar="LIST",
                        help="full: comma-separated maps for the smoke stage (default: all of src/maps/)")
    parser.add_argument("--python", metavar="PATH",
                        help="interpreter for build/check/tests (default: .venv/bin/python when present)")
    parser.add_argument("--engine-tests", action="store_true",
                        help="also set SD_ENGINE_TESTS=1 for the suite (a SECOND GZDoom window; "
                             "off by default because the smoke stage already runs the same thing)")
    parser.add_argument("--smoke-wait", type=int, metavar="TICS",
                        help="pass --wait TICS to tools/smoke.py (default: smoke's own)")
    parser.add_argument("--verbose", action="store_true",
                        help="print each stage's full output, not just the summary line")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    all_maps = discover_maps()
    explicit_maps = tuple(m.strip().upper() for m in args.maps.split(",")) if args.maps else ()

    decision: Decision | None = None
    if args.level == "auto":
        try:
            paths = args.files if args.files is not None else changed_paths(since=args.since)
        except (RuntimeError, FileNotFoundError) as exc:
            print(f"verify: {exc}", file=sys.stderr)
            print("verify: pass an explicit level (fast/full) when git is unavailable",
                  file=sys.stderr)
            return EXIT_NO_GIT
        decision = decide(paths, all_maps)
        doc_paths = tuple(p for p in decision.paths if p.endswith(".md"))
        plan = plan_for(decision.level, explicit_maps or decision.maps, doc_paths,
                        args.engine_tests, args.gate)
    else:
        level = LEVEL_BY_NAME[args.level]
        plan = plan_for(level, explicit_maps or all_maps, (), args.engine_tests, args.gate)

    if decision is not None:
        print_decision(decision, plan)
    if args.explain:
        if decision is None:
            print(f"plan: {plan.level.label} -> " + ", ".join(plan.stages))
        print("(--explain: nothing was run)")
        return EXIT_OK

    python = pick_python(args.python)
    print_header(plan, python)
    started = time.monotonic()
    results: list[StageResult] = []

    def finish(failed: StageResult | None) -> int:
        total = time.monotonic() - started
        if failed is not None:
            print(f"\n--- {failed.name} output ---")
            print(failed.output.rstrip() or "(no output)")
            print(f"\nVERDICT: FAIL at {failed.name} in {total:.1f}s (exit {failed.exit_code})")
            return failed.exit_code
        warned = [r for r in results if "WARN" in r.note]
        suffix = f" ({len(warned)} warning stage(s))" if warned else ""
        print(f"VERDICT: PASS in {total:.1f}s{suffix}")
        return EXIT_OK

    stages: list = []
    if plan.docs_check:
        stages.append(lambda: stage_docs(plan))
    if plan.build:
        stages.append(lambda: stage_build(python))
    if plan.check_pk3:
        stages.append(lambda: stage_check_pk3(python))
    if plan.tests:
        stages.append(lambda: stage_tests(python, plan.slow_art, plan.engine_tests))
    if plan.engine:
        if not plan.maps:
            print("  smoke          SKIP   no map found under src/maps/")
        for map_name in plan.maps:
            stages.append(lambda m=map_name: stage_smoke(python, m, args.smoke_wait, []))

    for stage in stages:
        result = stage()
        results.append(result)
        print_stage(result)
        # Warning detail is printed only where it is the point of the run
        # (level `docs`) or where it was asked for. `fast` must stay at four
        # lines and a verdict: that is the whole reason this tool exists.
        show_detail = args.verbose or (plan.level is Level.DOCS and "WARN" in result.note)
        if show_detail and result.output.strip():
            for line in result.output.rstrip().splitlines():
                print(f"       | {line}")
        elif result.ok and "WARN" in result.note:
            print("                 (python3 tests/_tiers.py --list names them)" if result.name == "tests"
                  else "                 (python3 tools/verify.py docs lists them)")
        if not result.ok:
            return finish(result)

    return finish(None)


if __name__ == "__main__":
    sys.exit(main())
