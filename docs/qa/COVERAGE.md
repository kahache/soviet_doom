# Code coverage

Living document (stable name); measured again whenever the CEO or a gate
asks for a fresh number. Russian mirror: `docs/ru/qa/COVERAGE.md` (D7).
Tooling: `tools/coverage.sh`, `.coveragerc` (both at the repo root/`tools/`).

`coverage` is a **dev-only** tool, installed only inside `.venv/`
(`.venv/bin/python -m pip install coverage` on the Mac,
`.venv/Scripts/python.exe -m pip install coverage` on Windows).
`tools/build.py` keeps building `dist/sovietdoom.pk3` with stdlib only —
that did not change and must not change.

## How to run it

```bash
tools/coverage.sh                  # run the suite under coverage, print the report, write HTML
tools/coverage.sh --no-html        # same, skip the HTML report (faster)
bash tools/coverage.sh --no-html   # Windows: the same script under Git Bash
```

This runs `python -m unittest discover -s tests` under `coverage run
--branch`, then `coverage report --sort=cover` (worst file first, total
last) and `coverage html` into `logs/coverage/html/` (gitignored — open
`logs/coverage/html/index.html` locally to click through any file).
`COVERAGE_FILE` is redirected to `logs/coverage/.coverage` so the raw data
never lands at the repo root. The script finds the venv interpreter on
either machine (`.venv/bin/python`, else `.venv/Scripts/python.exe`); on
Windows it ran unmodified on 2026-10-13 (the PM had already added the
Windows path).

The script's exit code is the **suite's** exit code, not a coverage
threshold — there is no `fail_under` gate here (see "What this is not"
below). Coverage is measured and printed even when tests fail; a failing
test still executes code on its way to failing, and that execution still
counts.

## Test tiers: what `verify.py fast` runs and what waits for `art` (2026-10-14, QA)

Coverage is unaffected: `tools/coverage.sh` still runs the whole suite
with plain `unittest discover`, so every number below includes every test.
What changed is `tools/verify.py`: the suite now goes through
`tests/_tiers.py`, the single place that decides each test's tier.

- **`fast`** runs every discovered test except the `SLOW` table in
  `tests/_tiers.py` (57 entries: modules, classes or single tests, each
  with its reason), with `SD_SKIP_SLOW_ART=1` as before. It keeps the
  build and check_pk3 tests, every text/contract test (LANGUAGE, MAPINFO,
  ZScript, UDMF, MENUDEF, licences, verify itself), the map plans
  (MAP03, MAP04) and the cheap generator contracts.
- **`art` and `full`** run **every** discovered test. On top of `fast`
  that adds generator renders (art, sound, the rig), the release end to
  end, the draft overlay, work/ scans, gzdoom.pk3 reads, MAP01/MAP02
  sight-line geometry, `route.MapData`, and the sprite sets' whole-PK3
  re-checks.
- **Nothing is lost:** fast + (art only) = discovered.
  `python tests/_tiers.py --list` prints the split. On 2026-10-14 ~19:50:
  1767 discovered = 1283 fast + 484 art only. `verify.py art` ran 1750 of
  1750 discovered a few minutes earlier (PASS, skipped=1, the opt-in engine
  test). At `fast`, unittest's "Ran" is ~16 below the tier count: classes
  whose `setUpClass` skips under `SD_SKIP_SLOW_ART` count once as a skip,
  not per test.
- **Build cache:** 19 tests built the same PK3. The runner wraps
  `sdbuild.pk3.build` for one process. The key is the content of src/,
  assets/ and tools/, and an unchanged file's digest is reused while its
  size and mtime stay put. `tests/test_build.py` bypasses the cache,
  because it tests the builder itself (including reproducibility). A fast
  run now builds twice and reuses six.
- **Before → after**, Windows PC with other agents running, back to back
  on one tree at ~19:55: the old fast suite (`SD_SKIP_SLOW_ART=1 python -m
  unittest discover -s tests`, 1751 tests) took **119 s** wall. The new
  `verify.py fast` (docs + build + check_pk3 + 1267 tests) took **14 s**
  (13.5 s VERDICT). Earlier runs under heavier load: 16-19 s.
- **Keeping it fast:** `python tests/_tiers.py fast --durations 15` names
  the slowest tests in the tier. A new slow class goes into `SLOW`, with
  its reason. If a rename leaves an entry matching nothing, `verify.py`
  shows a WARN on the tests stage, because that class would otherwise
  return to `fast` silently.

Slow costs that are test inefficiencies, reported to the files' owners
rather than fixed here (QA does not edit other agents' tests):
`test_art.ApprovedAssetsTests.test_identical_to_work_source` rglobs all of
work/ once per installed PNG (26 s; one index of work/ by name would make
it ~1 s). `test_audition`'s module fixtures SHA-256 all of `work/audio`
(296 MB) twice (~3 s; a stat-based digest would do). `test_route.ParseTest`
builds `route.MapData` for both maps in `setUpClass` (9 s).

## Latest number (2026-10-13 22:23, Windows PC, QA)

**Branch coverage of `tools/`: 82% (81.53%; 14754 statements, 3512
branches).** Test suite: **1088 tests, OK, 1 skipped** (the opt-in engine
test), **1 expected failure** (B4 below, new). `tools/verify.py art` on
the same tree, a few minutes earlier: PASS, 1076 tests.

Measurement facts:
- Command: `bash tools/coverage.sh --no-html` under Git Bash, interpreter
  `.venv/Scripts/python.exe` (Python 3.14), the Mac's `work/` in place;
  178 s wall clock.
- Tree: HEAD `3ddec9d` plus uncommitted work: `tools/art/gen_weapon.py`
  and `tests/test_gen_weapon.py` (another agent's, in progress) and QA's
  three new test files below. Seven agents were working at once; between
  the "before" and this run `tools/` grew by ~2000 statements
  (`gen_cursor.py`, `gen_legion.py`, `gen_storm.py`, a larger
  `gen_weapon.py`) and the suite by 172 tests, of which 87 are QA's.
- **Before**, same evening (HEAD `b694c33` + working tree, same command):
  **79% (79.22%; 12737 statements, 3064 branches), 916 tests, OK,
  1 skipped.** The two totals are on different trees, so their difference
  is not QA's alone.
- **QA's share, measured on one tree:** a run of the whole suite *without*
  `tests/test_cov_*.py` (978 tests) against `bash tools/coverage.sh`
  *with* them (1065 tests), started together on the same working tree at
  ~22:10 (14750 statements, 3508 branches): **73.68% → 76.69%, +3.0
  points** from the 87 new tests. (Both runs had 6 failures in other
  agents' in-progress `test_radio.py` / `test_credits.py`; none in QA's
  files. The 22:23 run above is clean.)

What the new tests cover, per file (before → after):

| File | Before | After | Test file |
|---|--:|--:|---|
| `tools/art/emblem_check.py` | 0% | **100%** | `tests/test_cov_art_previews.py` |
| `tools/art/make_contact.py` | 0% | **100%** | `tests/test_cov_art_previews.py` |
| `tools/art/make_preview.py` | 0% | **100%** | `tests/test_cov_art_previews.py` |
| `tools/art/gen_menu.py` | 24% | **99%** | `tests/test_cov_gen_menu.py` |
| `tools/art/gen_switch.py` | 41% | **99%** | `tests/test_cov_gen_switch.py` |

They assert what each tool promises, not just that it runs:
- `make_preview.py`: the status of each card is read from
  `TEXTURE-INDEX.md` by column name per table (fallback "proposed"); the
  page is self-contained (no external URL, every PNG inlined, the same
  bytes in the 1x, 4x and 2x2 views); zoom sizes, escaping of manifest
  text, the Russian mirror, the JS summary labels; `main()` writes the EN
  page and its RU mirror under one stamped name.
- `make_contact.py`: sheet geometry, every lump a nearest-neighbour 3x
  copy in manifest order with its name above, the half-size copy.
- `emblem_check.py`: two panels and a gap; guides only on the right;
  the emblem fills its panel on flag red; SDSTAR1 at exactly 8x nearest;
  the reference points are read live from `gen_soviet_base`.
- `gen_menu.py`: `build_font()` clears stale glyphs and **refuses** a
  Latin glyph that is not byte-identical to the installed Cyrillic one;
  `install()`; `FolderFont` recolouring (body / shadow, lower case drawn
  as capitals, missing glyphs skipped); `_skull()` decodes a synthetic
  Doom patch through PLAYPAL and returns `None` without the IWAD or the
  lumps; the menu dim reproduces the engine's measured (25,20,1) and
  (193,44,37) → (119,41,18) within 1; the main menu's geometry is
  `MENUDEF`'s; every skill rung fits at `MENUDEF`'s x = 32 and rung 5
  ends exactly at 320; the documented CLI.
- `gen_switch.py`: the seeds are the index's 2078-2081; the recess border
  is one flat colour and the bevel is lit top-left; variant D's chevrons
  are in both states; **"only the switch moves, never the panel"**: with
  the lamp glow taken out, every pixel that differs between the two
  states lies inside the parts that move; host lumas 147 / 101, "six or
  more is a lamp", B the strongest far read and A the weakest, as the
  sheet says; one `main()` run into a tempdir (40 indexed PNGs, the
  manifest, EN + RU sheets, one recommended card).
- **Approved-asset regression (`ApprovedSwitchTests`):** the eight
  approved `SDSW1x`/`SDSW2x` are rebuilt and quantised in memory and
  compared with `assets/`: **0 pixels differ outside the painted «ПУСК»
  box** on this PC, 162-181 inside it (Impact rasterises differently
  here, as `CLAUDE.md` measured). So everything but the word is still
  reproduced byte for byte, and a change to a switch's panel, lamp or
  lever now turns the suite red.
- Mutation check (by hand, not in the suite): moving the bolts by one
  pixel, deleting the moving-part boxes, or building the two states of a
  variant from different seeds each makes the relevant test fail.

D27: none of these tests writes to `work/`, `assets/` or `docs/`. Output
constants are redirected with `mock.patch.object` to temp directories;
`gen_menu`'s `build_font()`/`install()` only ever get temp paths and its
`main()` runs with its three actions mocked; the `gen_switch.main()` and
`gen_menu.sheet()` tests also assert that the real `work/` files kept
their modification times.

### Bugs found (QA found, did not fix)

**B4 (CLOSED 2026-10-13 23:00: the mock-up reads SkillMenu from MENUDEF; the expected failure is gone).** `gen_menu.py` mocks the skill
screen's suggested layout at `SUGGEST_HEADER = (48, 70)` and
`SUGGEST_ITEMS = (48, 90)`, but `src/lumps/MENUDEF` ships it at
`StaticText 32, 70` and `Position 32, 90` (moved to 32 because rung 5 is
288 px: 32 + 288 = 320; MOD-SPEC §6.6). The module calls these numbers
"Engine geometry (src/lumps/MENUDEF ...)". Consequence: a regenerated
menu sweep draws a skill screen the game does not have, and its width
check prints a false overflow. **Repro:**
`.venv/Scripts/python.exe -m unittest tests.test_cov_gen_menu.MenudefGeometryTests -v`
→ `test_suggested_skill_layout_is_the_one_menudef_ships ... expected
failure` (`((32, 70), (32, 90)) != ((48, 70), (48, 90))`); and
`gen_menu.mock_skill("en", "suggest", ...)` returns
`["'Hero of the Soviet Union, posthumously' ends at x=336"]`.
**Expected:** the suggested layout is `MENUDEF`'s, no overflow.
Encoded as `@unittest.expectedFailure`; when the constants are fixed the
test becomes an unexpected success and the marker must come off.

**B5 (CLOSED 2026-10-13 23:00: paths resolved at call time, `out_dir` respected; was →`art-director`; low, a D27 hazard rather than a wrong
asset).** `gen_menu.sheet(stamp, font_dir, out_dir)` writes the sweep to
`out_dir` but `MENUMOCK_main_en.png` / `_ru.png` to the module-level
`OUT_ROOT` (`work/art/menu/`) whatever `out_dir` says, and does not
create `OUT_ROOT` (on a clean clone, `sheet()` called on its own raises
`FileNotFoundError`; through `main()` it works because `build_font()`
creates the folder first). Also, `build_font()`, `install()` and
`sheet()` take their default paths as default arguments, bound at import:
patching `gen_menu.OUT_FONT` / `INSTALL_DIR` / `PREVIEW_DIR` does **not**
redirect `main()`, which would then write `work/art/menu/sdmenu/`,
`assets/fonts/sdmenu/` (with `--install`) and `docs/art/previews/`.
**Repro (read, NOT executed):** line 407 of `tools/art/gen_menu.py`
saves to `OUT_ROOT / f"MENUMOCK_main_{lang}.png"` with no reference to
`out_dir`, so `sheet("X", out_dir=Path(tmp))` would rewrite
`work/art/menu/MENUMOCK_*`. QA did not run that call, because it would
write into `work/` (D27); the tests run `sheet()` only with `OUT_ROOT`
patched to a tempdir, and there the two mocks land in the tempdir, which
confirms where the path comes from. **Expected:** every output under the
paths the caller passes. Not encoded as a failing test for the same
reason.

The largest gaps are now `tools/audio/midi_edit.py` (54%),
`tools/art/gen_enemy.py` (56%), `tools/audio/wav_report.py` (58%) and
the new `gen_storm.py` (62%); `sdbuild/pk3.py`'s three documented
branches are still unexercised.

| File | Stmts | Branch | Cover |
|---|--:|--:|--:|
| `tools/audio/midi_edit.py` | 173 | 76 | 54% |
| `tools/art/gen_enemy.py` | 582 | 100 | 56% |
| `tools/audio/wav_report.py` | 90 | 28 | 58% |
| `tools/art/gen_storm.py` | 519 | 130 | 62% |
| `tools/art/gen_props.py` | 584 | 150 | 67% |
| `tools/art/gen_legion.py` | 580 | 116 | 68% |
| `tools/build.py` | 41 | 12 | 68% |
| `tools/art/gen_weapon.py` | 1501 | 304 | 68% |
| `tools/smoke.py` | 342 | 122 | 69% |
| `tools/audio/midi_inspect.py` | 134 | 58 | 75% |
| `tools/art/gen_cursor.py` | 349 | 76 | 76% |
| `tools/art/gen_rig.py` | 908 | 180 | 78% |
| `tools/audio/gen_music.py` | 515 | 144 | 80% |
| `tools/verify.py` | 395 | 148 | 80% |
| `tools/route.py` | 825 | 318 | 83% |
| `tools/art/gen_metro.py` | 603 | 84 | 84% |
| `tools/art/gen_lenin.py` | 98 | 14 | 84% |
| `tools/sdbuild/pk3.py` | 129 | 60 | 84% |
| `tools/check_pk3.py` | 900 | 408 | 84% |
| `tools/art/gen_shell.py` | 350 | 68 | 86% |
| `tools/sdbuild/wad.py` | 65 | 30 | 87% |
| `tools/audio/gen_weapon_sfx.py` | 810 | 130 | 93% |
| `tools/audio/gen_sfx.py` | 1066 | 154 | 94% |
| `tools/art/gen_soviet_base.py` | 472 | 42 | 96% |
| `tools/sdbuild/udmf.py` | 375 | 116 | 98% |
| `tools/audio/audition.py` | 262 | 92 | 98% |
| `tools/art/gen_font.py` | 1084 | 190 | 99% |
| `tools/art/artlib.py` | 181 | 28 | 99% |
| `tools/art/gen_menu.py` | 264 | 60 | 99% |
| `tools/art/gen_switch.py` | 336 | 44 | 99% |
| `tools/art/emblem_check.py` | 48 | 6 | 100% |
| `tools/art/make_contact.py` | 34 | 2 | 100% |
| `tools/art/make_preview.py` | 60 | 12 | 100% |
| `tools/art/palette.py` | 42 | 6 | 100% |
| `tools/art/sheetlib.py` | 37 | 4 | 100% |
| `tools/sdbuild/__init__.py` | 0 | 0 | 100% |
| **TOTAL** | **14754** | **3512** | **82%** |

## Previous number (2026-10-13 21:10, Windows PC, QA)

**Branch coverage of `tools/`: 79% (12732 statements, 3062 branches).**
Test suite: **914 tests, OK, 1 skipped** (the opt-in engine test), **no
expected failure** (the font fix retired `SlabSerifDefectTests`' one).

Measurement facts:
- Command: `bash tools/coverage.sh --no-html` under Git Bash, interpreter
  `.venv/Scripts/python.exe` (Python 3.14), the Mac's `work/` in place;
  91 s wall clock, of which the suite 85 s.
- Tree: HEAD `87d613b` (its `tools/` and `tests/` are `d1e891f`'s; the
  commit touched docs only) **plus QA's uncommitted G3 route work**:
  `tools/route.py` and `tests/test_route.py` (56 tests in that file, 8
  more than at `d1e891f`). So the suite at `d1e891f` itself is 906 tests.
- `CLAUDE.md`'s "882 tests" was `tools/verify.py art`'s count earlier the
  same evening; this is the whole `unittest discover` under coverage, on a
  tree that has grown since.

What moved since the 14:50 figure (65%, 450 tests): `tools/` more than
doubled in tests and grew by 6233 statements, and coverage rose anyway.
`audition.py` went from 21% to **98%**, so it is no longer the largest
gap; `gen_font.py` is at 99%. The largest gaps now are the three files no
test imports (`emblem_check.py`, `make_contact.py`, `make_preview.py`, all
0%) and two generators with approved or proposed output: `gen_menu.py`
(24%) and `gen_switch.py` (41%). `sdbuild/pk3.py`'s three documented
branches (below, "The three gaps that matter most", item 2) are still
unexercised, at lines 90-92, 150 and 179.

| File | Stmts | Branch | Cover |
|---|--:|--:|--:|
| `tools/art/emblem_check.py` | 48 | 6 | **0%** |
| `tools/art/make_contact.py` | 34 | 2 | **0%** |
| `tools/art/make_preview.py` | 60 | 12 | **0%** |
| `tools/art/gen_menu.py` | 264 | 60 | 24% |
| `tools/art/gen_switch.py` | 336 | 44 | 41% |
| `tools/audio/midi_edit.py` | 173 | 76 | 54% |
| `tools/art/gen_enemy.py` | 582 | 100 | 56% |
| `tools/audio/wav_report.py` | 90 | 28 | 58% |
| `tools/art/gen_weapon.py` | 932 | 178 | 62% |
| `tools/art/gen_props.py` | 584 | 150 | 67% |
| `tools/build.py` | 41 | 12 | 68% |
| `tools/smoke.py` | 342 | 122 | 69% |
| `tools/audio/midi_inspect.py` | 134 | 58 | 73% |
| `tools/art/gen_rig.py` | 908 | 180 | 78% |
| `tools/audio/gen_music.py` | 515 | 144 | 80% |
| `tools/verify.py` | 395 | 148 | 80% |
| `tools/route.py` | 820 | 316 | 83% |
| `tools/art/gen_metro.py` | 603 | 84 | 84% |
| `tools/art/gen_lenin.py` | 98 | 14 | 84% |
| `tools/sdbuild/pk3.py` | 129 | 60 | 84% |
| `tools/check_pk3.py` | 900 | 408 | 84% |
| `tools/art/gen_shell.py` | 350 | 68 | 86% |
| `tools/sdbuild/wad.py` | 65 | 30 | 87% |
| `tools/audio/gen_weapon_sfx.py` | 810 | 130 | 93% |
| `tools/audio/gen_sfx.py` | 1066 | 154 | 94% |
| `tools/art/gen_soviet_base.py` | 472 | 42 | 96% |
| `tools/sdbuild/udmf.py` | 375 | 116 | 98% |
| `tools/audio/audition.py` | 262 | 92 | 98% |
| `tools/art/gen_font.py` | 1084 | 190 | 99% |
| `tools/art/artlib.py` | 181 | 28 | 99% |
| `tools/art/palette.py` | 42 | 6 | 100% |
| `tools/art/sheetlib.py` | 37 | 4 | 100% |
| `tools/sdbuild/__init__.py` | 0 | 0 | 100% |
| **TOTAL** | **12732** | **3062** | **79%** |

`tools/route.py`'s 17% left is mostly what only the PM's engine runs
reach (D26): `keep_evidence()` and `main()`'s loop after the engine returns
(lines 1519-1540 and 1676-1704 of the measured file), plus report branches
no synthetic log takes.

**Everything below this point is the history of the morning and afternoon
measurements** (11:35 to 14:50). Its per-file table and its analysis
describe the 11:35 tree; read them with the table above.

## Earlier the same day (2026-10-13 11:35, Windows PC, HEAD `b92c314` + uncommitted tooling)

**Branch coverage of `tools/`: 49% (5727 statements, 1486 branches).**
Test suite: **383 tests, OK, 16 skipped** (reasons below).
Re-measured by the PM at 12:00 the same day, after `gen_switch.py`'s sheet
fix and `tests/test_language.py`'s cleanup landed: **50% (5731 statements,
1488 branches), 384 tests, OK, 16 skipped.** Same machine, same command;
the per-file table below is from the 11:35 run and is not re-drawn for one
point.

**Latest, 2026-10-13 afternoon, after the Mac's `work/` arrived on this PC
and `tests/test_audition.py` was added: 52% (5739 statements, 1490
branches), 388 tests, OK, 1 skipped** (the opt-in engine test). The fifteen
skips that depended on `work/` now run: `gen_lenin.py` goes from 0% to 84%,
and B3 is closed by the same arrival (`docs/qa/GATE-REVIEWS.md`).
`gen_font.py` is still 0% and `audition.py` is 21%; those remain the two
largest gaps.

**Latest, 2026-10-13 ~14:50, with the whole afternoon's deliveries in the
tree** (`tests/test_gen_font.py`, `test_gen_font_fix.py`,
`test_gen_props.py`, `test_animdefs.py` and the new `gen_props.py`): **65%
(6499 statements, 1698 branches), 450 tests, OK, 1 skipped (the opt-in
engine test) and 1 expected failure** (`SlabSerifDefectTests`, the known
M/W defect). Measured by the PM at ~14:50 and re-measured by QA with
`bash tools/coverage.sh --no-html`: the same figures, to the statement and
the branch. Per file: `gen_font.py` 98% (was 0%), `gen_props.py` 67%,
`audition.py` 21%, now the largest remaining gap.

**Previous number:** 58% (3387 statements, 934 branches), 190 tests, measured
on the Mac at commit `8a4ef40` (2026-10-13 00:27). Both numbers are real;
the drop is explained, not excused, in the next section.

Measurement facts, so this can be reproduced or disputed:
- Machine: the CEO's Windows 10 PC (Intel i7-4790), the working machine
  since 2026-10-13. Interpreter: `.venv/Scripts/python.exe` (Python 3.14,
  Pillow, numpy, coverage). Command: `bash tools/coverage.sh --no-html`
  under Git Bash; output kept in this session's transcript.
- Tree: HEAD `b92c314` ("Agents may no longer start GZDoom: the engine
  gate"), **plus uncommitted modifications** to `tools/smoke.py`,
  `tools/verify.py`, `tools/run.sh`, `tools/coverage.sh`,
  `tools/art/artlib.py`, `tools/art/gen_lenin.py`,
  `tools/audio/audition.py` and four test files (`git status` at
  measurement time). So this number belongs to the working tree of the
  Windows move, not to a single commit; the next commit will carry it.
- The tree was moving while this was measured: `tools/verify.py fast`
  three minutes later reported **384** tests. Someone added one in
  between. The 383 figure is the one the coverage run saw.
- The HTML report was not written (`--no-html`); `logs/coverage/.coverage`
  holds the raw data if anyone wants `coverage report -m` on a file.

### Why 58% became 49%: 2340 new statements, most of them untested

`tools/` grew from 3387 to 5727 statements between `8a4ef40` and this tree
(`git diff --stat 8a4ef40 HEAD -- tools`): eight new files
(`tools/art/gen_font.py` 791 stmts, `tools/verify.py` 388,
`tools/art/gen_switch.py` 332, `tools/art/gen_metro.py` 264,
`tools/audio/midi_edit.py` 173, `tools/audio/midi_inspect.py` 134,
`tools/audio/wav_report.py` 90, `tools/art/sheetlib.py` 37) plus growth in
`audition.py`, `smoke.py`, `pk3.py` and `udmf.py`. Of the new files,
`verify.py` arrived with its own suite (`tests/test_verify.py`, 68%) and
`gen_switch.py`/`sheetlib.py` with a handful of layout tests (30% / 37%);
the other five arrived at **0%**.

Meanwhile the files that already existed got **better**, not worse:
`gen_shell.py` 0% → 86% (`tests/test_generators.py`), `gen_soviet_base.py`
93% → 96%, `artlib.py` 91% → 99% (`tests/test_artlib.py`, 575 lines, new),
`palette.py` 92% → 100%, `smoke.py` 68% → 69%, `pk3.py` 84% → 84%,
`udmf.py` 98% → 97% (grew by 63 lines), `check_pk3.py` 83% → 82% (grew).
That is the honest reading: the test investment kept pace in
`tools/art/artlib.py`, `gen_shell.py` and `verify.py`, and did not happen
at all for the font generator, the metro set, and the three new audio
tools. The new code drags the total down; the old code did not regress.

### Skips: why 16 tests did not run here, and what that does to the number

| Skipped | Reason (verbatim from the run) | Effect on the number |
|--:|---|---|
| 13 | `reference photograph absent (work\art\reference\lenin_1920_zhukov.jpg is under gitignored work/)` | `tools/art/gen_lenin.py` reads **0%** here; on the Mac these 13 tests run and the file is covered. Bound: 98 statements + 14 branches out of 7213, so the Mac number for this same tree would be **at most ~1.5 points higher**. NOT measured on the Mac. |
| 1 | `switch batch not generated` (`test_every_state_pair_is_the_contract_size`) | reads PNGs under `work/art/batch2/switch/`; exercises no `tools/` code either way |
| 1 | `work/ not present (gitignored work-in-progress)` (`test_identical_to_work_source`) | exercises no `tools/` code; see **B3** below |
| 1 | `set SD_ENGINE_TESTS=1 to run the real engine` | unchanged since the first report; the engine run in `smoke.py main()` stays opt-in |

`work/` is gitignored and did not travel from the Mac (`CLAUDE.md`), so
every test that depends on a generated-but-unapproved artefact under it
skips on this machine. That is the designed behaviour and the number above
is the Windows number. **The coverage figure is therefore machine-dependent
by up to ~1.5 points**, and only through `gen_lenin.py`.

**B3 (open, → PM / owner of `tests/test_art.py`; found 2026-10-13 11:36,
not fixed by QA; *closed later the same day: see "B3 — CLOSED" in
`docs/qa/GATE-REVIEWS.md` and the "Latest" paragraph in the header*):** `test_identical_to_work_source` guards itself with
"skip if `work/` does not exist", not "skip if the batch-1 render does not
exist". On this machine the batch-1 render never will exist unless someone
regenerates it, and `CLAUDE.md` says text-bearing lumps (`SDDOOR1`,
`SDPOSTR2`, the switches) rasterise differently here, so a regenerated
batch would fail the byte-identity check anyway. Consequence: **the first
time any generator writes anything under `work/art/` on Windows, this test
stops skipping and fails, and `tools/verify.py fast` goes red** — which the
pipeline (`docs/PIPELINE.md` §"When the pipeline stops") treats as "work
stops at stage 5". Observed live: at 11:36:00 another process created
`work/art/batch2/switch/` (40 PNGs; gone again by 11:37:52), and the
`verify fast` run that happened to fall in that window failed with
`assets/flats/soviet_base/SDCEIL1.png: matches no file generated under
work/`; the next run, with `work/` gone, passed. **Minimal repro** (from
the repo root, Git Bash, no `work/` present): `mkdir -p work/art &&
.venv/Scripts/python.exe -m unittest
tests.test_art.ApprovedAssetsTests.test_identical_to_work_source` →
**expected** skip (nothing to compare against) or a check scoped to the
files that do exist; **observed** `FAILED (failures=1)` on `SDCEIL1.png`,
a text-free flat that `CLAUDE.md` says is byte-identical when regenerated.
(`rmdir work/art work` afterwards; QA ran exactly this and cleaned up.)
**Severity:** medium: no shipped artefact is wrong, but the fast loop
becomes red by accident on the working machine, and a red `verify fast`
is what blocks commits. **Suspected cause:** the skip condition predates
the two-machine setup.

### Per-file, worst to best

| File | Stmts | Branch | Cover | Note |
|---|--:|--:|--:|---|
| `tools/art/emblem_check.py` | 48 | 6 | **0%** | never imported by any test (unchanged since the first report) |
| `tools/art/gen_font.py` | 791 | 118 | **0%** | **new, the largest file in `tools/`**: the D24 alphabet generator (214 glyphs, two sizes). The installed glyphs in `assets/fonts/` are only checked for byte-identity against `work/art/font/` by `test_identical_to_work_source`, which skips here (B3). On this machine nothing exercises the font generator or its output. |
| `tools/art/gen_lenin.py` | 98 | 14 | **0%** | 0% **on Windows only**: its 13 tests skip without the reference photograph. Covered on the Mac. |
| `tools/art/gen_metro.py` | 264 | 30 | **0%** | new (batch 2 "metro" set), never imported by any test |
| `tools/art/make_contact.py` | 34 | 2 | **0%** | never imported by any test |
| `tools/art/make_preview.py` | 60 | 12 | **0%** | never imported by any test |
| `tools/audio/audition.py` | 186 | 56 | **0%** | grew by 22 statements, still no test |
| `tools/audio/gen_music.py` | 377 | 86 | **0%** | unchanged; superseded in practice by D23 (download, don't compose) but still in the tree |
| `tools/audio/midi_edit.py` | 173 | 76 | **0%** | new, never imported by any test |
| `tools/audio/midi_inspect.py` | 134 | 58 | **0%** | new, never imported by any test |
| `tools/audio/wav_report.py` | 90 | 28 | **0%** | new, never imported by any test |
| `tools/art/gen_switch.py` | 332 | 42 | 30% | only `SwitchLayoutTests` (4 tests: box layout, `build_sheet()` with stubs). `main()` (696-725), every render function (142-251, 316-512) and `flr1_before_after()` untested |
| `tools/art/sheetlib.py` | 37 | 4 | 37% | new; only the import-time and layout helpers run (via `gen_switch` tests); lines 62-117 (the sheet writer) untested |
| `tools/build.py` | 41 | 12 | 55% | unchanged: default (non-`--quiet`) output, `--print-textmap`, the `BuildError` branch |
| `tools/verify.py` | 388 | 144 | 68% | new, arrived with `tests/test_verify.py` (556 lines). 110 statements missing; not itemised here |
| `tools/smoke.py` | 342 | 122 | 69% | the real-engine run in `main()`, opt-in behind `SD_ENGINE_TESTS=1` |
| `tools/check_pk3.py` | 752 | 340 | 82% | scattered error-rendering branches of an otherwise heavily-tested validator |
| `tools/sdbuild/pk3.py` | 129 | 60 | 84% | see "gaps that matter": the three documented branches are still untested, now at lines 90-92, 150 and 179 |
| `tools/art/gen_shell.py` | 350 | 68 | 86% | was 0%; `ShellTests` in `tests/test_generators.py` now run `build()` into a tempdir. Missing: 872-929, 950-972 (`main()` and the sweep writer) |
| `tools/sdbuild/wad.py` | 65 | 30 | 87% | six `raise` guards (57, 64, 75, 93, 96, 111) in a tiny binary (de)serialiser |
| `tools/art/gen_soviet_base.py` | 472 | 42 | 96% | only `main()` (469-492) is missing; the dead `tex_postr1()` is gone |
| `tools/sdbuild/udmf.py` | 341 | 102 | 97% | six lines (108, 115, 188, 403, 478-479) |
| `tools/art/artlib.py` | 181 | 28 | 99% | was 91%; `save_indexed()` and `tiling_seam_score()` are now tested directly (`tests/test_artlib.py`). One line (54) and one branch left |
| `tools/art/palette.py` | 42 | 6 | 100% | was 92% |
| `tools/sdbuild/__init__.py` | 0 | 0 | 100% | empty |
| **TOTAL** | **5727** | **1486** | **49%** | |

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
  and `tools/smoke.py` — into its own `parse_args()` function. The files
  that build their parser *inline inside* `main()`, mixed with real logic
  (`tools/build.py`, `tools/art/gen_lenin.py`, `tools/art/make_preview.py`,
  `tools/audio/audition.py`, `tools/audio/gen_music.py`, and the tools
  added since) are **deliberately not excluded**, because carving out just
  the `add_argument` lines there would be exactly the kind of cosmetic
  trim this report was told not to do. Their gaps are counted and
  discussed as real gaps, CLI-shaped or not.
- Nothing else is excluded. The `.coveragerc` has not changed since the
  first report; no exclusion was added to soften the Windows number.

**One real bug the first report surfaced, fixed, not papered over:** by
default, `coverage`'s "also report files that were never executed at all"
pass (`find_possibly_unexecuted_files` in `coverage/inorout.py`) skips any
subdirectory that lacks an `__init__.py`, unless
`[report] include_namespace_packages = True` is set. `tools/art/` and
`tools/audio/` have no `__init__.py` (tests import their modules by bare
name via `sys.path.insert`, see `tests/test_art.py`), so without that one
line the first run of this tool silently **hid** seven whole files from
the report instead of showing their true 0%. The total before the fix
read **86%**; after it, **58%**. That gap was not code getting worse, it
was the measurement finally looking at code it had been blind to. The
same flag is what makes the eleven 0% files above visible today: without
it this report would read far higher and be wrong.

## Honest analysis

### Contrasting the CEO's hypothesis, second measurement

**"`tools/sdbuild/` is critically undercovered" — still not true in
aggregate, still true in the same three spots.** `sdbuild/udmf.py` is at
97% after growing by 63 lines (`tests/test_udmf.py` grew with it),
`sdbuild/wad.py` 87%, `sdbuild/pk3.py` 84%. Inside `pk3.py` the three
**documented, supported, and completely unexercised** branches named in
the first report are all still unexercised, only their line numbers moved:

1. **`collect_maps()`'s raw-`.wad` branch** (now lines 90-92): a map
   dropped as a `.wad` under `src/maps/` (exported from Ultimate Doom
   Builder) instead of generated by `map.py`. Never run under test.
2. **`collect_assets()`'s missing-directory branch** (now line 150,
   `return []`) and with it `tools/build.py --assets <missing path>`,
   advertised in `build.py --help`. Never run under test.
3. **`collect_entries()`'s duplicate-path guard** (now line 179,
   `raise BuildError(f"duplicate PK3 path ...")`). Never fired under test.

**"The art generators in `tools/art/` are critically undercovered" — true,
and the split has moved.** In the first report the line ran between the
shipped batch-1 generator (93%) and everything newer (0%). Since then
`gen_shell.py` (title/menu/intermission, D18) went from 0% to 86% and
`artlib.py` from 91% to 99%, with `save_indexed()` — the function that
enforces "indexed to the mod palette" — now tested directly, which closes
most of the first report's third gap. The new line runs between those and
the **three generators behind assets the CEO has already approved or is
reviewing that have no test at all**: `gen_font.py` (0%, the D24 alphabet
that ships in `assets/fonts/`), `gen_metro.py` (0%, batch 2) and
`gen_switch.py` (30%, the switches already in `assets/`, whose `main()`
and render path are untested). `tools/audio/` is at 0% across all five
files; three of them are new since the last report.

### Confirming the other half: CLI and error branches that don't matter much

- **`tools/smoke.py`'s gap** is still `main()`'s actual engine run,
  correctly left to the opt-in `SD_ENGINE_TESTS=1` test and to the PM's
  engine passes (D26: agents no longer start GZDoom at all).
- **`tools/verify.py` at 68%** is new and arrived with a 556-line test
  file; its 110 missing statements were not itemised in this pass and are
  not claimed to be harmless. Next measurement should look.
- **`tools/build.py`'s and `tools/check_pk3.py`'s remaining gaps** are
  mostly print-formatting branches and secondary error paths of CLIs
  whose core logic is heavily exercised. Low value to chase.
- **`tools/sdbuild/wad.py`'s six gaps** are all `raise WadError(...)`
  guards, each one `assertRaises` away from closed. Not urgent.

## The three gaps that matter most

Ranked by "a regression here would ship silently and nobody would know
until a human hit it in-game or in a build log":

1. **`tools/art/gen_font.py`, 0% of 791 statements.** The largest file in
   `tools/`, generating the 214 glyphs that make D7 and D21 possible in
   the game (D24). Its output is in `assets/fonts/` today. The only test
   that looks at those glyphs (`test_identical_to_work_source`) compares
   bytes against `work/art/font/`, which does not exist on the working
   machine, so it skips (B3). A regression in the generator — a glyph
   off-palette, a wrong cell size, a missing codepoint — would be caught
   by nothing until someone reads a menu in-game.
   *Test that would close it:* run the generator for one variant into a
   tempdir (as `ShellTests` does for `gen_shell.build()`), then assert the
   glyph count per size, every opaque pixel's colour ⊆
   `docs/art/palette.json` with alpha only 0 or 255 (the folder fonts are
   RGBA by design, `docs/art/ART-BIBLE.md` §2, not mode `P`; this is now
   watched by `InstalledGlyphPaletteTests` in `tests/test_gen_font.py`),
   and the cell sizes the font layout in
   `docs/engine/MOD-SPEC.md` declares.

2. **`sdbuild/pk3.py`'s three branches (90-92, 150, 179)**, unchanged from
   the first report and still untested after a second measurement: the
   raw-`.wad` map path, the missing-`assets/` path, and the duplicate-path
   guard. Three small tests, described in the first report, still not
   written: a tiny PWAD fixture named `MAPXX.wad` placed under `src/maps/`
   with no sibling `map.py`; `build(..., assets=tmp / "does-not-exist")`;
   and two entries with the same path through `collect_entries()`
   asserting `BuildError`.

3. **`gen_switch.py` `main()` and render path (30%) and
   `gen_soviet_base.py` `main()` (469-492).** Both generators have assets
   in `assets/` approved by the CEO; neither's end-to-end write path runs
   under the suite. `artlib.save_indexed()` is now tested in isolation,
   which removes the worst risk (an un-indexed PNG), but the loops that
   choose names, sizes and manifest fields are still unexercised.
   *Test that would close it:* `main()` with `OUT_DIR`/`MANIFEST`
   redirected to a tempdir, as `tests/test_art.py` already does for
   `gen_soviet_base` helpers, asserting file count, size, mode and the
   manifest fields `make_preview.py`/`check_pk3.py` read.

(Fourth, named because the fix is a one-liner: **B3** above. Until the
skip condition in `test_identical_to_work_source` looks for the batch
render rather than for `work/`, the fast loop on Windows is one generator
run away from red.)

## What this report is not

- **Not a new gate.** No fixed threshold (`fail_under`) is set. The CEO
  asked for the real number, not a pass/fail line; `docs/ROADMAP.md` and
  `docs/PRD.md` own gate definitions, and adding a coverage gate there is
  a product decision for the CEO, not something this report decides on
  its own.
- **Not new tests.** None were written in this pass (the brief for the
  Windows move forbade touching `tests/`). The gaps above are described
  with enough detail to write them: `mod-engineer` for `sdbuild/`,
  `art-director` for `tools/art/`, `sound-designer` for `tools/audio/`.
- **Not a Mac number.** 49% is what this tree measures on the Windows PC
  with `work/` absent. The same tree on the Mac would read up to ~1.5
  points higher (`gen_lenin.py`); that was not measured and is not claimed.
- **Not a verdict on a single commit.** The working tree had uncommitted
  tooling changes at measurement time (listed above); the number is tied
  to the Windows-move commit that follows, whichever hash it gets.
