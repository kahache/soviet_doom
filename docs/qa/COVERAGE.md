# Code coverage

Living document (stable name); measured again whenever the CEO or a gate
asks for a fresh number. Russian mirror: `docs/ru/qa/COVERAGE.md` (D7).
Tooling: `tools/coverage.sh`, `.coveragerc` (both at the repo root/`tools/`).

`coverage` is a **dev-only** tool, installed only inside `.venv/`
(`.venv/bin/python -m pip install coverage`). `tools/build.py` keeps
building `dist/sovietdoom.pk3` with stdlib only — that did not change and
must not change.

## How to run it

```bash
tools/coverage.sh            # run the suite under coverage, print the report, write HTML
tools/coverage.sh --no-html  # same, skip the HTML report (faster)
```

This runs `python3 -m unittest discover -s tests` under `coverage run
--branch`, then `coverage report --sort=cover` (worst file first, total
last) and `coverage html` into `logs/coverage/html/` (gitignored — open
`logs/coverage/html/index.html` locally to click through any file).
`COVERAGE_FILE` is redirected to `logs/coverage/.coverage` so the raw data
never lands at the repo root.

The script's exit code is the **suite's** exit code, not a coverage
threshold — there is no `fail_under` gate here (see "What this is not"
below). Coverage is measured and printed even when tests fail; a failing
test still executes code on its way to failing, and that execution still
counts.

## Today's number (2026-10-13, commit `8a4ef40`)

**Branch coverage of `tools/`: 58% (3387 statements, 934 branches).**
Test suite: **190 tests, OK, 1 skipped** (`test_smoke_run_passes_on_the_current_pk3`,
gated behind `SD_ENGINE_TESTS=1` — it launches real GZDoom and is
intentionally opt-in, not part of the default suite).

**This is a moving target.** Four agents are working in this repo in
parallel right now. The suite was **red** when this task started — 149
tests, 3 failures, exactly matching the brief's warning
(`test_build.test_textmap_contents` off by `y=160`, plus two `test_art`
failures from `assets/graphics/shell/INTERPIC.png` landing mid-edit). By
the time this report was written, other agents had added
`tests/test_udmf.py` (41 new tests for the UDMF grid-map builder) and
fixed the three failures; the suite was green at measurement time. Both
facts are true and are recorded here; re-running `tools/coverage.sh` later
will give a different number as more tests and code land, which is the
point of shipping the tool rather than a one-off number.

### Per-file, worst to best

| File | Stmts | Branch | Cover | Note |
|---|--:|--:|--:|---|
| `tools/art/emblem_check.py` | 48 | 6 | **0%** | never imported by any test |
| `tools/art/gen_lenin.py` | 98 | 14 | **0%** | never imported by any test |
| `tools/art/gen_shell.py` | 350 | 68 | **0%** | never imported by any test |
| `tools/art/make_contact.py` | 34 | 2 | **0%** | never imported by any test |
| `tools/art/make_preview.py` | 60 | 12 | **0%** | never imported by any test |
| `tools/audio/audition.py` | 164 | 48 | **0%** | never imported by any test |
| `tools/audio/gen_music.py` | 377 | 86 | **0%** | never imported by any test |
| `tools/build.py` | 41 | 12 | 55% | default (non-`--quiet`) output, `--print-textmap`, the `BuildError` branch |
| `tools/smoke.py` | 297 | 104 | 68% | the real-engine run in `main()` (lines 455-551) |
| `tools/check_pk3.py` | 738 | 332 | 83% | scattered error-rendering branches of an otherwise heavily-tested validator |
| `tools/sdbuild/pk3.py` | 117 | 54 | 84% | see "what matters" below — small file, meaningful gaps |
| `tools/sdbuild/wad.py` | 65 | 30 | 87% | five `raise` guards in a tiny binary (de)serialiser |
| `tools/art/artlib.py` | 166 | 20 | 91% | `save_indexed()` and `tiling_seam_score()` only run via the untested `gen_soviet_base.main()` |
| `tools/art/palette.py` | 42 | 6 | 92% | only `main()` (CLI wiring) is missing |
| `tools/art/gen_soviet_base.py` | 463 | 42 | 93% | `tex_postr1()` is dead code (superseded, not in `TEXTURES`); `main()` itself untested |
| `tools/sdbuild/udmf.py` | 327 | 98 | 98% | the best-tested file in the tree (`tests/test_udmf.py`, 41 tests) |
| `tools/sdbuild/__init__.py` | 0 | 0 | 100% | empty |
| **TOTAL** | **3387** | **934** | **58%** | |

Full line/branch detail: `logs/coverage/html/index.html` (regenerate with
`tools/coverage.sh`; the directory is gitignored).

## `.coveragerc`: what is excluded, and why

```ini
[run]
source = tools
branch = True
omit = tests/*, .venv/*, work/*, */__pycache__/*

[report]
include_namespace_packages = True
exclude_also =
    if __name__ == .__main__.:
    def parse_args\(
```

- **`source = tools`, `omit = tests/*, .venv/*, work/*`**: we measure our
  own tooling, not the test harness, the virtualenv, or art
  work-in-progress (`work/` is gitignored scratch space, never shipped).
- **`branch = True`**: the CEO asked specifically *which branches run*, not
  just which lines — line coverage alone would hide an `if` whose `else`
  never fires.
- **`if __name__ == .__main__.:`**: this guard (and the `sys.exit(main())`
  line it protects) only runs when a file is executed directly —
  `python3 tools/build.py`, `tools/run.sh`, `tools/smoke.py` from the
  shell. The suite always imports these modules by name and calls
  `main()`/`build()` with an explicit `argv`, which is exactly how
  `tests/test_build.py` and `tests/test_smoke.py` already exercise them.
  Contains no logic of its own.
- **`def parse_args\(`**: excludes pure argparse wiring, but **only** in the
  two files where it is cleanly split from logic — `tools/check_pk3.py`
  and `tools/smoke.py` — into its own `parse_args()` function. Five other
  files build their parser *inline inside* `main()`, mixed with real logic
  (`tools/build.py`, `tools/art/gen_lenin.py`, `tools/art/make_preview.py`,
  `tools/audio/audition.py`, `tools/audio/gen_music.py`): those are
  **deliberately not excluded**, because carving out just the
  `add_argument` lines there would be exactly the kind of cosmetic trim
  this report was told not to do. Their gaps are counted and discussed
  below as real gaps, CLI-shaped or not.
- Nothing else is excluded. No defensive `except ImportError` fallback
  exists anywhere under `tools/` (checked), so there was no candidate for
  that common exclusion either.

**One real bug this surfaced, fixed, not papered over:** by default,
`coverage`'s "also report files that were never executed at all" pass
(`find_possibly_unexecuted_files` in `coverage/inorout.py`) skips any
subdirectory that lacks an `__init__.py`, unless
`[report] include_namespace_packages = True` is set. `tools/art/` and
`tools/audio/` have no `__init__.py` (tests import their modules by bare
name via `sys.path.insert`, see `tests/test_art.py`), so without that one
line the first run of this tool silently **hid** seven whole files —
`gen_lenin.py`, `gen_shell.py`, `make_contact.py`, `make_preview.py`,
`emblem_check.py`, `audition.py`, `gen_music.py` — from the report instead
of showing their true 0%. The total coverage number before the fix read
**86%**; after it, **58%**. That 28-point gap was not code getting worse,
it was the measurement finally looking at code it had been blind to. This
is the exact failure mode the brief warned against, just in the opposite
direction from "inflating the number by excluding real gaps" — a default
left alone would have inflated it by *hiding* files outright. Anyone
re-running `coverage` ad hoc without this `.coveragerc` would get the
misleadingly rosy number.

## Honest analysis

### Contrasting the CEO's hypothesis

**"`tools/sdbuild/` is critically undercovered" — not true in aggregate,
true in two specific spots.** `sdbuild/udmf.py` is the best-tested file in
the whole tree (98%, 41 dedicated tests just landed). `sdbuild/wad.py`
(87%) and `sdbuild/pk3.py` (84%) are solidly covered on their main path —
the one every `tools/build.py` run actually takes. But inside
`sdbuild/pk3.py`, three **documented, supported, and completely
unexercised** branches sit behind that respectable 84%:

1. **`collect_maps()`'s raw-`.wad` branch** (lines 85-86): the module's own
   docstring says a map can arrive either as `src/maps/<MAP>/map.py`
   (generated) *or* `src/maps/<MAP>.wad` (copied verbatim, e.g. exported
   from Ultimate Doom Builder). Only the first path has ever run under
   test. If level-designer starts exporting from UDB, this is the first
   time that code executes for real.
2. **`collect_assets()`'s missing-directory branch** (line 126) and, with
   it, `tools/build.py --assets <missing path>` — advertised in
   `build.py`'s own `--help` text as "pass a missing path to build without
   art" and the exact state the project was in for most of F0/F1. Never
   tested.
3. **`collect_entries()`'s duplicate-path guard** (line 150): the check
   that stops two files from silently colliding at the same PK3 path. It
   is the kind of guard that exists *because* something like it already
   went wrong once (see the `collect_assets` docstring's "blocker M1, found
   by level-designer 2026-10-12" note) — and it has never fired under test.

None of this shows up in the file's 84%; the aggregate number hides it.

**"The art generators in `tools/art/` are critically undercovered" — true,
but split sharply by age.** `gen_soviet_base.py` — the script behind the 9
CEO-approved batch-1 textures — is well tested at 93%, and not
superficially: `tests/test_art.py` checks its `quantize`/`Overlay`/
`ramp_colour` helpers against real pixel output, palette limits, and
tiling-seam math. What it does *not* test is `gen_soviet_base.main()`
itself (684-710) — the loop that actually writes the PNGs and the
manifest JSON — nor, by extension, `artlib.save_indexed()` (the function
that enforces "indexed to the mod palette", one of the literal gate
criteria in `CLAUDE.md`'s QA brief) or `artlib.tiling_seam_score()`. Every
*other* art generator — `gen_shell.py` (title/menu/intermission screens,
350 statements), `gen_lenin.py` (the Lenin poster), `make_contact.py`,
`make_preview.py`, `emblem_check.py` — sits at a literal, unqualified 0%.
These are newer tools (F3/F4, "in progress in parallel" per `CLAUDE.md`'s
own status line) that simply haven't had the same test investment yet as
the batch that already shipped. `tools/audio/` (`audition.py`,
`gen_music.py`) is 0% for the same reason, one day old as of this
writing (D16, 2026-10-13).

### Confirming the other half: CLI and error branches that don't matter much

- **`tools/smoke.py`'s big gap (lines 455-551)** is `main()`'s actual
  engine run: building the command line, launching real GZDoom as a
  subprocess, reading its log, printing the summary, deciding the exit
  code. It needs a real GZDoom binary and a display; it is correctly left
  to the opt-in `test_smoke_run_passes_on_the_current_pk3` (skipped by
  default, `SD_ENGINE_TESTS=1` to run it for real) and to the manual
  evidence runs QA already does with `tools/run.sh`. Every piece of logic
  that *feeds* that block — `scan_log()`, `find_gzdoom()`, `find_iwad()`,
  the timeout handling — already has its own dedicated tests in
  `tests/test_smoke.py`. The one piece of real, untested logic buried in
  that block is the final if-chain that turns a `Report` into one of
  `EXIT_TIMEOUT` / `EXIT_LOG_FAILURES` / `EXIT_ENGINE_FAILED` /
  `EXIT_NO_MAP` / `EXIT_OK` — see the "gaps that matter" list below.
- **`tools/build.py`'s and `tools/check_pk3.py`'s remaining gaps** are
  mostly print-formatting branches (`build.py`'s default, non-`--quiet`
  summary; `check_pk3.py`'s human-readable rendering of a report that is
  already checked field-by-field in the 26 KB of `tests/test_check_pk3.py`)
  and secondary error paths of CLIs whose core per-check logic is already
  heavily exercised. Low value to chase.
- **`tools/sdbuild/wad.py`'s five gaps** (lines 57, 64, 93, 96, 111) are
  all `raise WadError(...)` guards in an 18-line binary writer/reader —
  real, but trivially small and isolated (each is a one-line
  `assertRaises` away from closed). Not urgent, not critical.

## The three gaps that matter most

Ranked by "a regression here would ship silently and nobody would know
until a human hit it in-game or in a build log":

1. **`sdbuild/pk3.py::collect_maps()`, the raw-`.wad` map branch
   (lines 85-86).** A documented, supported way to hand the builder a map
   (export from Ultimate Doom Builder, drop the `.wad` under `src/maps/`)
   has never executed once under test.
   *Test that would close it:* drop a tiny, valid PWAD fixture (built with
   `sdbuild.wad.build_pwad`, as `tests/test_check_pk3.py` already does for
   its own fixtures) at `src/maps/MAPXX.wad` with no sibling `map.py`, call
   `collect_maps()`/`build()`, and assert it is packed at `maps/MAPXX.wad`
   byte-for-byte, alongside a second assertion that mixing a `map.py` map
   and a raw-`.wad` map in the same build produces both.

2. **`sdbuild/pk3.py::collect_assets()`, the missing-`assets/`-directory
   branch (line 126) — and by extension `tools/build.py --assets
   <missing>`.** This is not a hypothetical: it is the exact state the
   project was in through most of F0/F1, and `build.py --help` advertises
   it ("pass a missing path to build without art"). Nothing currently
   calls `build()` with a nonexistent `assets` path.
   *Test that would close it:* `build(src, out, tools_dir, assets=tmp_path
   / "does-not-exist")` and assert it still produces a PK3 containing only
   `src/`'s own content, no exception, no silently-empty texture folder
   created on disk.

3. **`gen_soviet_base.py::main()` (684-710) and
   `artlib.save_indexed()` (272-277) — the actual PNG-and-manifest write
   path.** Everything this function calls (`quantize`, `Overlay`,
   `ramp_colour`, `tiling_seam_score`) is well tested in isolation; the
   function that wires them together, writes `SD*.png` to disk indexed to
   the mod palette, and writes `palette`-adjacent manifest JSON has never
   run under the suite. Today it is only checked after the fact, by
   `check_pk3.py` scanning files that already made it into `assets/`, and
   by a human looking at the HTML preview. A regression here (e.g. a
   texture silently saved un-indexed, or the manifest losing a field
   `check_pk3`/`make_preview.py` relies on) would not be caught by any
   currently-green test.
   *Test that would close it:* run `gen.main()` with `OUT_DIR` monkeypatched
   to a tmp dir, then assert every `TEXTURES` entry produced a file with
   ≤256 palette colours (`Image.open(p).getcolors()`), the declared
   width/height, and that `manifest.json` has exactly as many entries as
   `TEXTURES` with the fields `make_preview.py`/`check_pk3.py` read.

(A fourth, smaller one worth naming since it is a one-line fix each: the
five `WadError` guards in `sdbuild/wad.py` — empty lump list, non-`bytes`
lump data, truncated blob, bad magic, missing lump name — have zero tests
between them. Any one is a single `self.assertRaises(WadError, ...)` call.)

## What this report is not

- **Not a new gate.** No fixed threshold (`fail_under`) is set. The CEO
  asked for the real number, not a pass/fail line; `docs/ROADMAP.md` and
  `docs/PRD.md` own gate definitions, and adding a coverage gate there is
  a product decision for the CEO, not something this report decides on
  its own.
- **Not new tests.** Per the brief, none were written here — the three
  gaps above (and the `wad.py` one) are described with enough detail to
  write them, intentionally left to whoever owns that code
  (`mod-engineer` for `sdbuild/`, `art-director` for `tools/art/`) so this
  task does not collide with the QA agent already writing tests for the
  art generators in parallel.
- **Not a verdict on the suite being red or green.** Both states were
  observed in this one session (red at the start, matching the brief's
  warning to the letter; green at measurement time, after other agents'
  fixes landed) and both are recorded above with their exact test counts.
