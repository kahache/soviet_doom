# Gate reviews

One section per gate. Gates are measured, not argued. Russian mirror:
`docs/ru/qa/GATE-REVIEWS.md`.

## G0 — the pipeline works (F0, MVP) — **PASS** (2026-10-09 00:37)

**Criterion:** GZDoom loads `dist/sovietdoom.pk3` on Freedoom with no error
and no "Unknown" in the log, enters MAP01 and the player stands inside the
room.

**Environment:** Intel Mac (i5-5257U, Iris 6100), macOS 12.7.6, GZDoom
g4.14.2 (Homebrew cask), freedoom2.wad 0.13.0 (SHA-256 verified against the
signed release CHECKSUM).

**Evidence:**
- `docs/qa/evidence/2026-10-09_0037_F0_g0-gzdoom.log`: `adding
  dist/sovietdoom.pk3, 5 lumps` · `MAP01 - SD: Test Range` · `SOVIETDOOM
  loaded: map MAP01 (SD: Test Range)` (ZScript EventHandler) · `Captured
  Screenshot_Doom_20261009_003742.png`. Zero matches for
  `error|Unknown|missing|warning` after the MAPINFO fix.
- `docs/qa/evidence/2026-10-09_0037_F0_g0-map01-freedoom.png`: engine
  screenshot: room with Freedoom's STARTAN2 / FLOOR4_8 / CEIL3_5, player with
  pistol, HUD. No HOM: linedef orientation is correct.
- Suite `tests/`: **build 11/11** OK.
- CEO saw the window open with the empty map (literal verdict, Spanish: "se
  abría y se veía el mapa vacío").

**Findings during the gate:**
- **B1 (closed):** `lookup = "..."` is not accepted inside an `episode` block
  on GZDoom 4.14.2 (`Script error ... Unknown property 'lookup'`). Fixed with
  `name = "$SD_EP01_NAME"` (resolved through LANGUAGE).
- `music = ""` yields silence with no warning (was NOT VERIFIED; now verified).
- macOS `screencapture` does not capture the GZDoom window (Vulkan/MoltenVK);
  visual evidence is taken with the engine's own `screenshot` command
  (`+screenshot_dir` + `+"wait N; screenshot; quit"`). Standard QA method.

**Verdict:** PASS.

## G1 — lore and D-decisions ratified (F1) — **PASS** (2026-10-09 01:03) — retrospective entry, written 2026-10-13

**Criterion:** CEO ratifies lore and D1–D13 (`docs/ROADMAP.md`).

**Why this entry is retrospective:** the PMO audit of 2026-10-13 (PMO-03)
found that `CLAUDE.md` claims G0, G1 and G2 "all PASS with evidence in
`docs/qa/GATE-REVIEWS.md`" while this file only had G0 and G2. G1 was
closed by the PM in commit `2fc8db1` without a QA entry. This section was
written on 2026-10-13 by `qa-engineer` from what exists in git; nothing was
re-ratified and no verdict was re-dated. The date in the heading is the
commit's (`git log -1 --format=%ad 2fc8db1`: `Fri Oct 9 01:03:26 2026
+0200`), because that commit is the ratification event on record.

**Environment:** not applicable; a documentary gate, no engine run, no
asset check. Evidence was read from `git` on the Windows PC on 2026-10-13.

**Evidence (each item checked against the repository on 2026-10-13, not
quoted from memory):**
- Commit `2fc8db1857e08418a6fe021e70b2762308497bb1` (author kahache,
  2026-10-09 01:03:26 +0200): "F1 closed: gate G1 PASS, D1-D15 ratified
  (1977, names, licence), sci2 resolved, LICENSE.md". 12 files, EN and RU
  mirrors together. Its diff **is** the ratification: in `docs/PRD.md` §5,
  D1–D5 go from `proposed, CEO ratifies` to `ratified (CEO, 2026-10-09)`;
  D8 loses "year open" and fixes **1977**; D14 (names) and D15 (licence)
  are added. In `docs/product/LORE.md` the three `OPEN` markers (year,
  protagonist name, faction names) are replaced by the ratified values and
  the header goes from "(D8–D13)" to "(D8–D14), names included".
  `docs/PENDING-CEO-DECISIONS.md` drops all six F1 items (ratify D1–D5,
  exact year, protagonist name, faction names, `sci2`, licence) and reads
  "D1–D15 ratified". `docs/ROADMAP.md` G1 goes from "lore ratified
  2026-10-09; D1–D5 pending ratification" to "PASSED 2026-10-09".
- `docs/PRD.md` §5 at HEAD: D1–D14 all carry `ratified (CEO)`, dated
  2026-10-09 (D1–D5 with the date inline, D6–D14 under the Date column).
  D13 is the lore decision: "Lore v1, three-map episode, period arsenal
  and bestiary (`docs/product/LORE.md`) **ratified as written**". The
  D1–D15 rows are byte-identical between `2fc8db1` and HEAD (compared with
  `git show 2fc8db1:docs/PRD.md`); later decisions D16–D24 were appended
  without touching them (*historical, as written on 2026-10-13: the PRD
  now runs to D27*).
- `docs/product/LORE.md`: header "Status: **RATIFIED by the CEO on
  2026-10-09** (D8–D14), names included", unchanged since `2fc8db1`.
- `LICENSE.md` (D15): added in `2fc8db1`, the only commit that has ever
  touched it (`git log --oneline -- LICENSE.md`). GPL-3.0-or-later for
  code, CC BY-NC-SA 4.0 for assets and docs, EN and RU in the same file,
  full licence texts deferred to G6 as D15 itself says.
- The preceding commit `5be54de` (2026-10-09 00:58:22): "F0 closed, F1 lore
  ratified: ... PRD D1-D13, lore v1" already had the lore ratified with
  D1–D5 still pending; `2fc8db1`, five minutes later, closes the rest.

**What the evidence does not contain (stated, not smoothed over):**
- **No literal CEO quote for G1 exists in the repository.** G0 and G2 both
  carry one; G1 does not. The ratification happened in the chat session of
  2026-10-09 and its only durable record is the set of status flips in the
  PM's commit. This entry accepts the PM's commit as the record, which is
  the project's own rule (D6: the PM commits), but it is weaker evidence
  than a quote and the reader should know that.
- **D15 is not CEO-ratified.** Its status reads `decided by the PM on CEO
  delegation`, both in `2fc8db1` and at HEAD. The commit title and
  `docs/ROADMAP.md`'s "D1–D15 ratified" overstate by one decision. This
  does not touch the verdict: the criterion is D1–D13, and D14 is extra.
  It is a wording error in `docs/ROADMAP.md` (PM-owned); filed here, not
  fixed by QA.
- Whether the lore was ratified "as written" cannot be re-measured by QA
  after the fact; the ratified document itself is the evidence.
- The Russian mirror of this entry is `docs/ru/qa/GATE-REVIEWS.md` (D7),
  delivered by `translator-ru` the same day.

**Verdict:** PASS. The criterion is "CEO ratifies lore and D1–D13";
`docs/PRD.md` §5 records D1–D14 as `ratified (CEO)` on 2026-10-09,
`docs/product/LORE.md` carries the ratified header, and commit `2fc8db1`
is the event. Dated to the commit; written retrospectively on 2026-10-13.

## G2 — art direction + texture batch 1 (F2) — **PASS** (2026-10-12 22:35)

**Criterion:** ≥ 8 textures approved by the CEO, all with origin and
licence; palette fixed (`docs/ROADMAP.md`).

**Environment:** `.venv/bin/python` 3.14.4 (Pillow + numpy) on the same Mac
as G0; checks run against the working tree as of 2026-10-12 22:35
(`git status` snapshot included below, since two files were uncommitted at
review time).

**Evidence:**
- `docs/art/TEXTURE-INDEX.md` (HEAD, committed): 8 rows with a plain,
  unconditional `approved` status — `SDCONC1`, `SDSTEL1`, `SDDOOR1`,
  `SDFLR1`, `SDFLR2`, `SDFLR3`, `SDCEIL1`, `SDCEIL2` — matching the CEO's own
  tally quoted in the same file ("Gate G2 (≥ 8 approved): **8 approved**").
  Each has a matching PNG: `assets/textures/soviet_base/{SDCONC1,SDSTEL1,
  SDDOOR1}.png` and `assets/flats/soviet_base/{SDFLR1,SDFLR2,SDFLR3,SDCEIL1,
  SDCEIL2}.png` — 8 files, counted by `ls`, not assumed.
- `docs/art/LICENSES.md` §"Batch 1": all 12 batch-1 lumps, the 8 approved
  ones included, carry origin (`tools/art/gen_soviet_base.py`, `BATCH_SEED`
  1977, palette v1), author (Soviet Doom project / art-director) and licence
  (own work, CC BY-NC-SA 4.0, D15). No approved lump is missing from this
  table.
- `docs/art/ART-BIBLE.md` §3: "**Ratified by the CEO 2026-10-12** ('Palette
  OK' in the batch-1 verdict)." `docs/art/palette.json` has 162 colours.
- `.venv/bin/python -m unittest discover -s tests -v` (file `tests/test_art.py`):
  **14/14 tests OK**, including `ApprovedAssetsTests.test_layout_names_and_sizes`
  and `ApprovedAssetsTests.test_identical_to_work_source`, plus
  `PaletteJsonTests.test_palette_matches_generator` (confirms
  `palette.json` is exactly what `tools/art/palette.py` regenerates, i.e.
  "fixed", not just claimed).
- Independent re-check (not just trusting the suite), one `PIL.Image.open`
  per approved file against `docs/art/palette.json`: all 8 are mode `P`
  (indexed), every used colour is a subset of the 162-colour palette, every
  dimension is a multiple of 8, flats are exactly 64×64 and walls are 64×128
  or 128×128 per `docs/art/ART-BIBLE.md` §2 — e.g. `SDDOOR1.png` 128×128,
  `SDCONC1.png`/`SDSTEL1.png` 64×128, all five flats 64×64. Script output
  kept in this session's transcript; no row failed.

**Findings (do not block G2, numeric criterion already met by the clean 8;
reported as a process bug, not fixed by QA — D-rule: QA reports, does not
fix):**
- **B2 (open, → `art-director`):** `assets/textures/soviet_base/SDPOSTR2.png`
  is physically present (confirmed with `ls -la`, timestamp 22:31, one commit
  cycle after the other 8 files at 21:57) but it is an **untracked,
  uncommitted** file (`git status --porcelain`: `?? assets/textures/
  soviet_base/SDPOSTR2.png`). Every committed source of truth says it should
  **not** be there yet:
  - `docs/art/TEXTURE-INDEX.md` (HEAD) status for `SDPOSTR2`: "approved
    pending text confirmation (CEO likes it; the Russian wording is to be
    confirmed before it enters `assets/`)" — by the document's own legend
    this is the `approved pending …` transitional status, defined at the top
    of the file as "not in `assets/` yet".
  - `docs/PENDING-CEO-DECISIONS.md` (HEAD): "`SDPOSTR2` text was confirmed on
    2026-10-12 (...); it enters `assets/` **with the next batch pass**"
    (future tense — that pass is not recorded as done anywhere).
  - `docs/art/ART-BIBLE.md` §4 (HEAD): enumerates "**8 approved** (...) — in
    `assets/`" and separately "`SDPOSTR2` approved pending confirmation of
    its Russian text" — also only 8 in `assets/`.
  - On top of that, at review time `docs/art/TEXTURE-INDEX.md` **and** its
    Russian mirror had an uncommitted, half-finished edit (`git diff`
    confirmed) that changed `SDPOSTR2`'s status word from "approved pending
    text confirmation" to bare "approved" **without** removing the trailing
    clause that still reads "before it enters `assets/`", and without
    touching the "8 approved" tally line two rows above — i.e. the document
    contradicts itself in its current, uncommitted state.
  - `CLAUDE.md`'s own status section already asserts "SDPOSTR2 approved,
    text confirmed" — jumping ahead of `docs/art/TEXTURE-INDEX.md`, which
    `CLAUDE.md`'s own ownership table names as the owner of this fact.
  - The PNG itself passes every format check (mode P, 128×128, colours a
    subset of the palette) — this is not an asset-quality bug, it is an
    asset that entered `assets/` and got a doc half-edited before the
    CEO-confirmation → doc-update → commit sequence that the project's own
    workflow requires (`CLAUDE.md`: "Nothing enters `assets/` without
    explicit approval").
  - **Repro:** on this working tree, run `git status --porcelain` and `git
    diff docs/art/TEXTURE-INDEX.md`. **Expected:** clean tree, or a fully
    finished edit (status word, trailing clause, and the "N approved" tally
    all agreeing with each other and with `ART-BIBLE.md` §4 and
    `PENDING-CEO-DECISIONS.md`). **Observed:** an untracked PNG plus a
    self-contradictory half-edit. **Severity:** low (does not affect the
    numeric gate, nothing shipped is wrong) but **blocking for hygiene**:
    whoever finishes this must either (a) complete the transition — commit
    the PNG, set `SDPOSTR2` to a plain `approved`, update the "8 approved"
    line to 9, update `ART-BIBLE.md` §4 and `PENDING-CEO-DECISIONS.md` to
    match — or (b) revert — remove the PNG from `assets/` and discard the
    half-edit — until the batch pass is actually done. **Suspected cause:**
    an in-progress `art-director` edit left uncommitted. **Assigned to:**
    `art-director` (owner of `TEXTURE-INDEX.md` and `assets/`).
- Not a finding, explicitly out of scope for this gate and correctly so:
  `SDSTAR1` (currently `proposed v5`, no PNG in `assets/`) and the Lenin
  poster (`SDPOSTR1`, `discarded`, separate commission per
  `docs/PENDING-CEO-DECISIONS.md` item 2) remain open CEO decisions that do
  not block G2 — the criterion only needs ≥ 8, already met without them.
  `SDCONC2` (`pending in-map review`) is explicitly deferred to F3, once
  MAP01 exists in GZDoom for the CEO to judge it in place — correctly not
  decided from a flat preview.

**Verdict:** PASS. The criterion (≥ 8 CEO-approved textures, all with
origin and licence, palette fixed) is met with 8 unambiguous, cleanly
`approved` assets, independent of the `SDPOSTR2` situation above. B2 does
not reopen the gate — it is filed so the `SDPOSTR2` transition gets finished
cleanly before F3 treats it as a 9th approved asset.

**B2 — RESOLVED by the PM, 2026-10-12, same day.** The finding was correct and
the fault was the PM's: the CEO confirmed the Russian wording in chat, the PM
copied the PNG into `assets/` and flipped the status word, and then stopped —
leaving `ART-BIBLE.md` §4, `PENDING-CEO-DECISIONS.md` and the tally lines
saying the opposite. All of them now read **9 approved** with `SDPOSTR2` in
`assets/` unconditionally, and the previews were regenerated so their status
badges agree. The gate verdict is unaffected: G2 was measured on the 8
unconditional textures and passes on them alone.

## Environment change 2026-10-13 — from the Mac to the CEO's Windows PC (note, not a gate)

- **Verified by the PM, not re-run by QA** (QA does not start the engine;
  the `SD_ALLOW_ENGINE` gate is the PM's): `tools/smoke.py --map MAP01` and
  `tools/smoke.py --map MAP02` both end in VERDICT PASS on GZDoom g4.14.2
  with `dist/sovietdoom.pk3` at 259 lumps and a `464 x 281` window.
- **Checked by QA** on 2026-10-13 11:3x from the gitignored `logs/smoke.log`
  left by the PM's 11:31:58 MAP02 run: `GZDoom version g4.14.2`, `adding
  .../dist/sovietdoom.pk3, 259 lumps`, `Resolution: 464 x 281`, `MAP02 -
  Engineering Test Range`, `SOVIETDOOM loaded: map MAP02`, `Captured
  Screenshot_Doom_20261013_113204.png`. The same log says `Initialization
  of Vulkan failed: ... incompatible driver` and the engine runs on OpenGL
  4.6 (NVIDIA GeForce RTX 3050, driver 560.94); not a PK3 error, but it is
  in the log and the Mac ran Vulkan/MoltenVK. The MAP01 run was overwritten
  by the MAP02 run, so MAP01 PASS rests on the PM's statement and
  `CLAUDE.md` (11:28): **NOT VERIFIED by QA**.
- **Checked by QA:** `iwads/freedoom2.wad` (28,787,748 bytes) hashes to
  SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`
  (`sha256sum`, 2026-10-13), the value recorded for Freedoom 0.13.0; QA did
  not itself re-download the signed CHECKSUM file. Suite on Windows under
  `.venv/Scripts/python.exe` 3.14: 383 tests OK, 16 skipped (see
  `docs/qa/COVERAGE.md`); `tools/verify.py fast` VERDICT PASS at 11:38.
- **NOT VERIFIED on this machine, by anyone:** a complete playthrough of
  MAP01 on any skill; skills 2, 3 and 4 (the G3 criterion); sound and music
  playback; regeneration of the Lenin poster (its reference photograph is
  only on the Mac, so 13 tests skip here; *closed later the same day: the
  Mac's `work/` arrived that afternoon and those tests now run here, see
  "B3 — CLOSED" below*); any text-bearing asset
  regenerated on Windows (`CLAUDE.md`: Impact and Arial Narrow rasterise
  differently; an approved asset is regenerated only where it was rendered).
- **B3 (open, → PM / owner of `tests/test_art.py`):** on this machine
  `test_identical_to_work_source` skips only while `work/` is absent; the
  moment any generator creates `work/art/` it runs and fails, because the
  batch-1 render it compares against never travelled from the Mac.
  Observed live at 11:36 when another process created
  `work/art/batch2/switch/` (gone again by 11:37:52), turning `verify fast`
  red for one run. Repro and severity in `docs/qa/COVERAGE.md` §"Skips".
  **B3 — CLOSED 2026-10-13, afternoon, by the PM.** The Mac's `work/`
  arrived as the release asset `transfer-work-2026-10-13` (SHA-256 of the
  zip and of all 847 files checked against the Mac's manifest) and was
  installed in `work/`. `tools/verify.py art` then ran 384 tests with one
  skip, the opt-in engine test, and `test_identical_to_work_source` passes
  against the Mac's renders. The test stays as the tripwire: a text-bearing
  generator run on this PC overwrites a Mac render and turns it red, which
  is the intended behaviour (`CLAUDE.md`, generator rule).

## G3 — MAP01 finishable on skills 2, 3 and 4 (F3) — **IN PROGRESS** (opened 2026-10-13 20:29)

**Criterion:** "map finishable on skills 2, 3 and 4 with zero log errors and
zero softlocks; CEO verdict 'on point'" (`docs/ROADMAP.md`), measured as
G3-1…G3-9 of `docs/levels/MAP01-zarya-7.md` §11. There is no verdict yet.
This section holds two things: the engine checklist the PM runs (D26: QA
does not start GZDoom), and the record of what is already on file.

**Already proven without the engine** (not repeated here): the static rows
R1–R12 of `docs/levels/MAP01-zarya-7.md` §18.2. They cover G3-1, G3-3,
G3-6 and G3-8, and the static halves of G3-4 and G3-5. They are tests in
`tests/test_udmf.py` and `tests/test_map01.py`. G3 is signed only on a
`tools/verify.py full` run, never on `fast` (`docs/PIPELINE.md` §5).

**Already on file from the engine:**
- The CEO played skill 3 to the end (D38: "ha sido MUY divertido!!").
  **No log of that run is filed**, so G3-2 on skill 3 is unmeasured. C2
  below provides one, though it is a scripted run, not a played one.
- The PM's pass at 20:14 on `bc906f5`
  (`docs/qa/evidence/2026-10-13_2014_rack-and-mural.md`, with
  `docs/qa/evidence/2026-10-13_2014_mural-M1-M5_and_spawn.png` and
  `docs/qa/evidence/2026-10-13_2014_rack-pickup.png`) found:
  - the TT-33 raised on spawn;
  - the rack pickup working;
  - the mural whole in M1–M4;
  - **M5 inconclusive**: the first-person weapon hid the health bonus at
    the mural's foot.

  That build still had the shovel. D40 (`7b3ae65`) renamed the class to
  `SD_IceAxe`, so the rack is checked again on the ice-axe build (C1–C4).
- The PM's first run of `tools/route.py`, 20:36–20:39 on `51c2746`, from a
  clean worktree (`docs/qa/evidence/2026-10-13_2039_d40-d43-engine-pass.md`;
  QA also read the run logs left in the PM's worktree):
  - the helper (`route-1`) compiled. Position, door tags, lines, the
    inventory, the exit line and the unload all printed as the parser
    expects;
  - skill 2 PASS; skills 3 and 4 FAIL at A1 only;
  - skills 3 and 4 with `--nomonsters`: PASS, with the rack pickup, every
    gate in order, the exit switch and zero log failures;
  - the A1 failure is the runner's, not the map's: a live Stormtrooper
    stood in the Z1→Z3 corridor, and a scripted `+forward` cannot step
    round a body (the PM checked the screenshot). The skill-3 report shows
    every other step `[ok ]`;
  - `god` printed `God mode on.`;
  - `gamestate` after the exit was NOT SEEN: the per-level helper is gone
    once the level has ended;
  - MAP01's exit unloaded towards `enDSeQ1dce`, an end sequence, as
    MAPINFO's `next = endtitle` says;
  - none of these runs was filed with `--keep-evidence`, so C1–C3 below
    are still owed.

  The runner was changed after this run (`route-2`, below). C1–C3 must be
  run again on it.
- **The PM's `route-2` runs, 20:50–20:52 on `92dd9cf`, clean worktree,
  filed with `--keep-evidence`** (`docs/qa/evidence/2026-10-13_2050_F3_g3-map01-g3-auto-skill2*`,
  `…_2051_F3_g3-map01-g3-auto-skill3*`, `…_2051_F3_g3-map01-g3-auto-skill4*`,
  `…_2052_F3_g3-map02-map02-start-skill3*`; QA read every report and log
  and looked at the A0, R1, E1 and END shots):

  | Run | Monsters (engine = map) | Blockers killed by `sdclear` | Kills at the exit | Log failures | Exit | VERDICT |
  |---|---|---|---|---|---|---|
  | C1, `g3-auto`, skill 2 | 21 = 21 | 6 (A1 3, A3 2, A10 1) | 6 of 21 | none | switch pressed, unloaded towards `enDSeQ1dce` | **PASS** |
  | C2, `g3-auto`, skill 3 | 33 = 33 | 10 (A1 5, A3 3, A10 2) | 12 of 33 | none | the same | **PASS** |
  | C3, `g3-auto`, skill 4 | 46 = 46 | 13 (A1 5, A3 5, A10 2, A11 1) | 15 of 46 | none | the same | **PASS** |
  | C5, `map02-start`, skill 3 | 14 = 14 | 0 | 0 of 14 | none | `sdexit`, unloaded towards `enDSeQ1dce` | **PASS** |

  - On all three MAP01 skills: A0 `raised slot 2 (SD_Tokarev), 50 rounds;
    owned [2:SD_Tokarev]`, R1 `raised slot 1 (SD_IceAxe)`, every door tag
    shut before its switch and open after it, every walk-through in the
    zone it expects, zero secrets (so these are also zero-secret runs, with
    `god`). The A0 shot shows the TT-33 in hand and 50 rounds; the R1 shot
    the ice axe raised and `An ice axe.`. The END shot is MAP01's
    intermission, "Zarya-7 Cosmodrome — Finished".
  - Every blocker died (`dead`), none survived. They are the route's
    doing, not the map's: each stood within 128 of a scripted `+forward`.
    That skill 4 needs 13 against skill 2's 6 matches the 21/33/46
    placement.
  - On MAP02: A0 and R1 as on MAP01; the E1 and END shots both show
    `SD_END02_TEXT` ("The range is closed for the day. / The campaign
    begins from New Game.") over `SDFLR1`.
  - So `sdclear` and `sdexit` are now **verified in the engine**. C1, C2,
    C3 and C5 pass. C5 is run again on the new `map02-start` (below),
    which leaves MAP02 by its switch instead of `sdexit`.
- **The PM's pass at 20:56–20:57** (`docs/qa/evidence/2026-10-13_2057_map02-range-and-c12.md`,
  sheet `…_2057_map02-range-P1-P6_and_map01.png`), on `026c267` plus
  `level-designer`'s MAP01 and MAP02, committed right after as `f3cd8ea`
  and `d1e891f`:
  - **C12 PASS, G3-F1 closed.** From `warp 440 1300` facing north,
    `+forward` through the 48-wide lane between the lectern and the east
    lamp: the log prints `Health boosted!`. The record is the PM's written
    note; no screenshot and no log copy were filed for it, which QA accepts
    for a one-line pickup message.
  - **MAP02 for players** (`docs/levels/MAP02-practice-range.md` §7): P1
    (the exit alcove, the hazard panel whole), P2 (the gallery door rises
    from the hall), P3 and P5 (the bent passage; after the PPSh fired by the
    open door, `sdcount` shows all 15 bestiary actors alive), P6 (the exit
    switch shows `SD_END02_TEXT` over `SDFLR1`), P7 (zero `Script error`,
    `Missing`, `Unknown`). **P4, the door from the passage side, was not
    exercised**: it is now the scripted route `map02-door` (C5b below).
- **The PM's batch on the final build, 21:14–21:17 on `87d613b`, clean
  worktree, QA's uncommitted `route.py` (helper still `route-2`), filed
  with `--keep-evidence`.** QA read every report and log, and looked at the
  MAP02 E0, E1 and P4b shots.

  | Run | Evidence (`docs/qa/evidence/`) | Monsters (engine = map) | Blockers killed by `sdclear` | Kills | Log failures | Exit | VERDICT |
  |---|---|---|---|---|---|---|---|
  | C5, `map02-start`, skill 3 | `2026-10-13_2114_F3_g3-map02-map02-start-skill3*` | 14 = 14 | 0 | 1 of 14 (see G3-F5) | none | **switch pressed**, unloaded towards `enDSeQ1dce` | **PASS** |
  | C8, `g3-auto --nomonsters`, skill 3 | `2026-10-13_2115_F3_g3-map01-g3-auto-skill3-nomonsters*` | 0 = 0 | 0 | 0 of 0 | none | switch pressed, `enDSeQ1dce` | **PASS** |
  | C5b, `map02-door`, skill 3 | `2026-10-13_2115_F3_g3-map02-map02-door-skill3*` | 14 = 14 | 0 | level never ended | none | **NOT REACHED** | **FAIL at E0 only** (G3-F4, the route's bug) |
  | C1, `g3-auto`, skill 2 | `2026-10-13_2116_F3_g3-map01-g3-auto-skill2*` | 21 = 21 | 6 (A1 3, A3 2, A10 1) | 6 of 21 | none | switch pressed, `enDSeQ1dce` | **PASS** |
  | C2, `g3-auto`, skill 3 | `2026-10-13_2117_F3_g3-map01-g3-auto-skill3*` | 33 = 33 | 9 (A1 5, A3 2, A10 2) | 11 of 33 | none | the same | **PASS** |
  | C3, `g3-auto`, skill 4 | `2026-10-13_2117_F3_g3-map01-g3-auto-skill4*` | 46 = 46 | 16 (A1 7, A3 5, A8 1, A10 2, A11 1) | 21 of 46 | none | the same | **PASS** |

  - **The final build passes the route on skills 2, 3 and 4**, with
    monsters, after `f3cd8ea` (the rack zone renamed, the komnata lamps
    moved). R1 now ends in `z1_ice_axe_rack` (Z1 by its own name). Every
    blocker died; none survived.
  - **C5 PASS:** MAP02 is left by its exit switch, as a player leaves it.
    E0 ends in `EXIT` (`exit_alcove`) at (−15, 384); its first shot shows
    the hazard panel `ПУСК` whole between its steel jambs (P1); E1's
    activation is `special=243 … player=1`, and the E1 shot shows
    `SD_END02_TEXT` over `SDFLR1` (P6).
  - **C8 PASS:** G3-5's `-nomonsters` half is filed.
  - **C5b: P4 is verified.** P4a reads tag 1 shut (`ceil=0`) from the
    passage at (672, 864). P4b's press fires the passage-side face
    (`line index=19 special=12 arg0=1 front=3 back=2 player=1`), tag 1
    reads open (`ceil=124`, fully raised after 70 tics), and the walk
    ends in the hall at (672, 630). The run then failed at E0, for the
    route's sake, not the map's: G3-F4 below, fixed in `route-3`.

**What "after it: NOT SEEN" means.** On every run so far (route-1 and
route-2, MAP01 and MAP02) the report's exit line ends in `after it: NOT
SEEN`. The static `SDRouteState` was meant to answer `sdstate` after the
level ended, and it never printed: there is no `SDTEST state` line in any
log, not even for the `sdstate` E1 asks *during* MAP02's end text.
Hypothesis, NOT VERIFIED: GZDoom refuses the `netevent` console command
outside a level, so nothing typed after the exit reaches any handler. The
21:15 `map02-door` run supports it: its level never ended, and there the
same handler did answer, twice (`SDTEST state gamestate=0`, i.e. in a
level). **Impact on the verdict: none.**
- The exit is judged on two lines that do print, before the level is gone:
  the player's `Exit_Normal` activation (`SDTEST line … special=243 …
  player=1`) and the unload (`SDTEST unloaded … next=enDSeQ1dce`). The
  unload names the end sequence MAPINFO's `next = endtitle` asks for.
- What is on screen after it is not something a log line can show anyway.
  **The capture is the evidence, and it is enough:** the END shot of each
  MAP01 run shows the intermission, and MAP02's E1 and END shots show the
  end text. Since this pass the report says so in place: `after it: NOT
  SEEN (the helper cannot ask once the level is gone; judge the END shot)`.
- The query stays in the helper: it costs one line and would corroborate
  if a later engine answers.

### The tool: `tools/route.py`

`tools/route.py` walks a map's critical path by console commands, one
engine run per skill. It starts GZDoom only through `smoke.run_engine`,
which refuses without `SD_ALLOW_ENGINE=1`.

It loads a helper PK3 of its own from `logs/route/` (gitignored). The
helper reports the player's position, door heights, line activations,
secrets, the intermission and the inventory. It is never in `src/`,
`dist/` or the mod PK3; `tests/test_route.py` enforces that.

The start inventory is checked **by slot, never by class name**. The rack
is found by DoomEdNum 21001. So the D40 rename cannot break either check.

Every run prints a report that ends in a VERDICT. With `--keep-evidence`,
the run files its log, its report and one PNG per captured step under
`docs/qa/evidence/`, named
`<stamp>_F3_g3-<map>-<route>-skill<N>[-nomonsters]{.log,-report.txt,-<step>.png}`.
`<stamp>` is the run's `YYYY-MM-DD_HHMM`.

**Blockers.** Before every scripted walk, the helper's `sdclear` kills the
live monsters standing within 128 units of the walk's line, and logs each
one. A kill is never hidden. The report lists each one under `blockers`
(step, class, position, hit points). It counts them apart under `kills`
("N of M, of which K by the route's sdclear"), and it names them on the
VERDICT line: `PASS (1 blocker(s) killed by the route, listed above)`. A
blocker that survives fails the run. `--no-clear` turns clearing off.

**Ending a level.** Every built-in route ends its map by **pressing the
exit switch**, as a player does; a switch route ended by `sdexit` fails.
MAP01's switch is G3-4's. MAP02 got one with `d1e891f`: `Exit_Normal` on
the back wall of a lit alcove behind the start (the line x −32, y 352–416;
`docs/levels/MAP02-practice-range.md` §4.1). `map02-start` now ends there:
step E0 stands on the start (160, 384), turns to face west, shoots the
alcove (the P1 view) and walks in until the back wall stops him; E1
presses the switch, 16 units ahead, inside the 64-unit use range. The
helper's `sdexit` (`Level.ExitLevel`) is kept as a **documented recourse
only**, for a map with no exit line: a JSON route with `"exit_by":
"console"` uses it; no built-in route does, and `tests/test_route.py`
fails if one ever types it. The console `exit` quits GZDoom and is never
typed (PM, 20:39). Both maps say `next = endtitle`, and the report checks
that the level led to an end sequence.

**P4 as a route of its own, `map02-door`:** `map02-start` plus two steps
before the exit. P4a warps into the passage's south leg at (672, 864),
facing south, and reads tag 1 shut; P4b presses, reads tag 1 open after
70 tics, and walks through into the hall. The walk runs down x 672, 48
units off the PPSh-41 and 64 off the RPG-7, so it picks nothing up. It is
a separate route so that `map02-start`, proven at 20:52, cannot be failed
by a P4 problem of the route's own making. `tests/test_route.py` reads the
door back from the built map: Door_Raise on tag 1, wound with the passage
in front (ZDoom fires a use special from the front only), within reach.

**Zones.** MAP02's five sectors now have families of their own in the
report (`HALL`, `EXIT`, `GDOOR`, `PASSAGE`, `GALLERY`), so its steps say
where the player must end, as MAP01's do. The dead prefix row
`shovel_rack` is gone: since `f3cd8ea` the rack is `z1_ice_axe_rack` and
files under Z1 by its own name. A test now fails on any prefix row that
matches no sector.

**Verified in the engine.**
- route-1, the PM's run of 20:36: the helper compiles, and it reports
  position, tags, lines, inventory, the exit line and the unload.
- route-2, 20:50–20:52: `sdclear` and `sdexit`.
- **Never answered:** the static `SDRouteState`'s `sdstate` after the exit
  (see "What 'after it: NOT SEEN' means" above).
- route-2 again, 21:14–21:17: `map02-start`'s E0 and E1 (the walk to the
  switch and the press, replacing `sdexit`) and `map02-door`'s P4a and P4b.
- **`route-3` VERIFIED by the PM at 21:24** (G3-F4's fix; `map02-door` PASS
  with E0 in EXIT and the exit switch pressed, `2026-10-13_2124_F3_g3-map02-map02-door-skill3*`;
  `map02-start` and `g3-auto` 2/3/4 re-run unfiled, all PASS, 5/8/10 blockers): the
  helper's new `sdstop`, and `sdangle` now also stopping the body. Both
  write `Actor.Vel` and `PlayerInfo.vel`, declared writable in g4.14.2's
  `gzdoom.pk3` (`zscript/actors/actor.zs`: `native vector3 Vel;`,
  `zscript/actors/player/player.zs`: `native vector2 vel;`).

**Warps start and end at rest (`route-3`).** The console `warp` moves the
player and keeps his velocity (G3-F4). Every warp step is now `sdstop`,
`warp`, then `sdangle` (which also stops the body) or, for a warp with no
facing, `sdstop` again. `tests/test_route.py` holds it for every warp of
every built-in route, and holds the exact P4b-to-E0 sequence.

Every engine name these use was read from g4.14.2's `gzdoom.pk3`:
- `Level.ExitLevel(int, bool)`;
- `Actor.AngleToVector`, `Vec2To`, `bIsMonster`;
- `DMG_FORCED`, `DMG_THRUSTLESS`, `DMG_NO_FACTOR`;
- `StaticEventHandler`, and `GS_FINALE` (2).

If the helper does not compile, the log shows a `Script error` naming
`SDRouteHelper`, and `--minimal-helper` runs only the part already proven
(angle, hurt, count).

All commands below are typed in Git Bash at the repo root.

**Before any run:**

```
.venv/Scripts/python.exe tools/verify.py fast       # VERDICT PASS
git log --oneline -1 -- src/zscript/sd/player.zs   # 7b3ae65 or later: the build has the ice axe
.venv/Scripts/python.exe tools/route.py --print     # what the runs will type; opens nothing
```

### Engine checklist

A row passes only when its evidence is in `docs/qa/evidence/` under the
name given.

| # | Covers | Command | Pass when | Evidence (`docs/qa/evidence/`) |
|---|---|---|---|---|
| C1 | Q6, the start inventory, scripted, skill 2 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 2 --keep-evidence` | Report row `[ok ] A0: raised slot 2 (SD_Tokarev), 50 rounds; owned [2:SD_Tokarev]`. Report row `[ok ] R1: …; owned [1:SD_IceAxe, 2:SD_Tokarev]`. Doors ok. Exit REACHED towards an `enDSeQ…` sequence. VERDICT PASS (the route half of G3-4, `god` on). Copy the `blockers` lines into the notes: each is a place where a monster stood in a scripted walk | `<stamp>_F3_g3-map01-g3-auto-skill2.log`, `…-skill2-report.txt`, `…-skill2-a0.png`, `…-skill2-r1.png`, `…-skill2-end.png` |
| C2 | Q6, the same on skill 3, and a filed skill-3 log for G3-2 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 3 --keep-evidence` | As C1 | `<stamp>_F3_g3-map01-g3-auto-skill3{.log,-report.txt,-a0.png,-r1.png,-end.png}` |
| C3 | Q6, the same on skill 4 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 4 --keep-evidence` | As C1 | `<stamp>_F3_g3-map01-g3-auto-skill4{.log,-report.txt,-a0.png,-r1.png,-end.png}` |
| C4 | Q6 by eye: the TT-33 is raised on spawn, slot 1 is empty, the rack pickup works | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=3 tools/run.sh -nomonsters +screenshot_dir "$PWD/logs/shots"`. At spawn, console `screenshot`. Press `1`, then `screenshot`. Walk to the rack on the west wall (or console `warp 40 384`, face west, walk forward). Press `1`, then `screenshot`. `quit` | Shot 1: the TT-33 in hand. Shot 2: still the TT-33. The log has `An ice axe.` (`SD_PICKUP_ICEAXE`) once. Shot 3: the ice axe raised. `.venv/Scripts/python.exe tools/route.py --scan logs/gzdoom.log` gives VERDICT PASS | `<stamp>_F3_g3-start-tt33-raised.png`, `<stamp>_F3_g3-start-slot1-empty.png`, `<stamp>_F3_g3-rack-iceaxe.png`, `<stamp>_F3_g3-start-inventory.log` (a copy of `logs/gzdoom.log`) |
| C5 | Q6 on the practice range, and MAP02 left by its exit switch to its end text (D41) (about 20 s) | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route map02-start --skills 3 --keep-evidence` | Rows A0, R1 and E0 `[ok ]`, E0 in `EXIT` (`exit_alcove`). Exit `exit switch pressed: yes`, towards an `enDSeQ…` sequence. The first E0 shot shows the lit alcove with the hazard panel whole (P1); the E1 shot shows `SD_END02_TEXT` ("The range is closed for the day…") over `SDFLR1` (P6). VERDICT PASS | `<stamp>_F3_g3-map02-map02-start-skill3{.log,-report.txt,-a0.png,-r1.png,-e0.png,-e0-2.png,-e1.png,-end.png}` |
| C5b | MAP02's P4: the gallery door opened from the passage side (optional for G3, owed to `docs/levels/MAP02-practice-range.md` §7) | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route map02-door --skills 3 --keep-evidence` | Door rows `[ok ] tag 1 at P4a: want shut` and `[ok ] tag 1 at P4b: want open`; `[ok ] walk-through at P4b: ended in HALL`; then as C5. VERDICT PASS | `<stamp>_F3_g3-map02-map02-door-skill3{.log,-report.txt,-p4a.png,-p4b.png,-e1.png,-end.png}` |
| C6 | Q1, Q2, Q3 and Q5: G3-4 on skill 2, played, no cheats | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=2 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. Play from the start to the exit switch with no console command. Console `screenshot` facing the exit switch (the HUD shows health and ammo), then `screenshot` at the intermission, then `quit`. Copy `logs/gzdoom.log` to the evidence name, then run `.venv/Scripts/python.exe tools/route.py --scan docs/qa/evidence/<stamp>_F3_g3-map01-skill2-run.log` | Intermission reached. `--scan` VERDICT PASS (G3-2: 0 hits). Notes: time, health, deaths, any monster that never left a doorway or a closet mouth (Q3), anything that felt lavish (Q5) | `<stamp>_F3_g3-map01-skill2-run.log`, `<stamp>_F3_g3-map01-skill2-at-exit.png`, `<stamp>_F3_g3-map01-skill2-intermission.png`, notes in `<stamp>_F3_g3-map01-notes.md` |
| C7 | Q1, Q2, Q3, Q4 and Q5, plus G3-5's zero-secret run: skill 4, played, no cheats, **no secret entered** | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=4 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. As C6, and do not enter S1, S2 or S3. Then `grep -c "A secret is revealed" docs/qa/evidence/<stamp>_F3_g3-map01-skill4-run.log`, and `--scan` as in C6 | Intermission reached. `--scan` PASS. The grep prints `0`. Notes: ammo at the exit (from the HUD shot), and whether the player was ever left with only the ice axe (Q4) | `<stamp>_F3_g3-map01-skill4-run.log`, `<stamp>_F3_g3-map01-skill4-at-exit.png`, `<stamp>_F3_g3-map01-skill4-intermission.png`, notes in `<stamp>_F3_g3-map01-notes.md` |
| C8 | Q7: G3-5's `-nomonsters` run | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --nomonsters --skills 3 --keep-evidence` | Exit REACHED, `monsters: engine 0, map data 0`, VERDICT PASS | `<stamp>_F3_g3-map01-g3-auto-skill3-nomonsters{.log,-report.txt,-end.png}` |
| C9 | Q7: every secret entered and left | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route g3-secrets --skills 4 --keep-evidence` | `secrets : 3 of 3`, exit REACHED, VERDICT PASS | `<stamp>_F3_g3-map01-g3-secrets-skill4{.log,-report.txt,-s1.png,-s2.png,-s3.png,-end.png}` |
| C10 | Q7: G3-7, the hostile pass, skill 4 | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=4 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. `god` is allowed here: this tests the map, not the fight. Do every item of G3-7 in §11: throw each switch twice, re-enter every door, walk into each monster closet and back out, enter each secret and leave, drop off the catwalk and the cradle from all four sides, and play backwards from the hangar | "Could not get stuck". `--scan` PASS | `<stamp>_F3_g3-map01-hostile-skill4.log`, a `screenshot` of any place that traps the player, notes in `<stamp>_F3_g3-map01-notes.md` |
| C11 | Q8: the mural, M1–M5 (§17.13) | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route mural --skills 3 --nomonsters --hide-weapon --keep-evidence` | M1: the whole mural, nothing square in front of it, the lectern to its right. M2: the inner columns either side of the tribune. M3a and M3b: the mural whole, at most a sliver behind the jamb. M4: the lectern's plank top level, no HOM or seam at the step. M5: the health bonus at the mural's foot is visible, for the CEO's call (clutter or fine). The report shows six `[ok ]` steps, all in Z4 | `<stamp>_F3_g3-map01-mural-skill3-nomonsters{.log,-report.txt,-m1.png,-m2.png,-m3a.png,-m3b.png,-m4.png,-m5.png}` |
| C12 | Q8: the last part of M4, by hand | In any C4 or C6 session: `warp 440 1300`, face north, `+forward` through the lectern–lamp lane onto the health bonus at (432, 1400) | The bonus is picked up (its message is in the log) | `<stamp>_F3_g3-map01-m4-bonus.png`. **Done 20:57**: `Health boosted!`, recorded in `2026-10-13_2057_map02-range-and-c12.md` (no PNG filed) |

**What the checklist does not do.** G3-9 is the CEO's: the "on point"
verdict and the `SDCONC2` verdict. The route runs (C1–C3, C5, C5b, C8, C9,
C11) play with `god` on. They prove the path, the doors, the exit and the
inventory; they do not prove the fight. For G3-4, only C6, C7 and the
CEO's skill-3 run count.

**Checklist status (2026-10-13 21:30):**

| # | Status | Evidence |
|---|---|---|
| C1, C2, C3 | **PASS** (route-2, 20:50–20:51 on `92dd9cf`), and **PASS again on the final build** (21:16–21:17 on `87d613b`) | `2026-10-13_2116_F3_g3-map01-g3-auto-skill2*`, `…_2117_…-skill3*`, `…_2117_…-skill4*` (the final build); `…_2050_…`, `…_2051_…` (the earlier pass) |
| C4 | **Covered by C1–C3**, not run separately. Its three questions are answered by each run's A0 and R1 report rows (slot 1 empty, the TT-33 raised with 50 rounds, then the ice axe in slot 1) and shots (the TT-33 in hand; the ice axe raised and `An ice axe.`), on three skills instead of one | the `-a0.png`, `-r1.png` and `-report.txt` files above |
| C5 | **PASS** by the exit switch (21:14); earlier with `sdexit` (20:52) | `2026-10-13_2114_F3_g3-map02-map02-start-skill3*`; `…_2052_…` |
| C5b | **P4 verified** (21:15); the run FAILED at E0 on the route's own bug (G3-F4), fixed in `route-3`; **re-run owed** for a clean PASS | `2026-10-13_2115_F3_g3-map02-map02-door-skill3*` |
| C6, C7 | **Owed: G3-4 played on skills 2 and 4, no cheats** (C7 is also G3-5's zero-secret run as written; C1–C3 already reach the exit with zero secrets, but with `god`) | — |
| C8 | **PASS** (21:15), filed: G3-5's `-nomonsters` half | `2026-10-13_2115_F3_g3-map01-g3-auto-skill3-nomonsters*` |
| C9 | Optional: C10 enters and leaves every secret by hand; C9 is the scripted proof that the secret count reads 3 of 3 | — |
| C10 | **Owed: G3-7, the hostile pass on skill 4** | — |
| C11 | M1–M4 seen at 20:14 (`2026-10-13_2014_rack-and-mural.md`) and M1 again at 20:57 with the lamps moved; **M5 is the CEO's call** (clutter or fine), with G3-9. The filed route run is optional | `2026-10-13_2014_mural-M1-M5_and_spawn.png`, `2026-10-13_2057_map02-range-P1-P6_and_map01.png` frame 8 |
| C12 | **PASS** (20:57), G3-F1 closed | `2026-10-13_2057_map02-range-and-c12.md` |

### Findings so far

- **G3-F1 (CLOSED 2026-10-13 20:57; was low, → `level-designer`).** Fixed
  in `f3cd8ea`: both komnata floor lamps moved 16 units out (x 160 / 480),
  so the lane between the lectern and the east lamp is 48 wide, a body and
  a half (`docs/levels/MAP01-zarya-7.md` §17.15). C12 passed in the engine
  through that lane. The original finding, for the record: the health
  bonus at (432, 1400) on the tribune could be reached only through gaps
  exactly one body wide:
  - between the lectern (x 384…416, y 1344…1376) and the floor lamp at
    (464, 1376) (radius 16, so x 448…480): a 32-unit lane at x 416…448;
  - behind the lectern (y 1376…1408, up to the north wall): also 32.

  A player of radius 16 fits with zero tolerance. Doom allows touching, so
  it should have passed; the fix made the question moot.
- **Corrected: the god-mode line.** Before the first run, QA "fixed" the
  detector to look for "Degreelessness Mode ON", g4.14.2's `language.csv`
  text for `STSTR_DQDON`, and claimed here that "God mode on" never
  matched. The run disproved that: the engine printed `God mode on.`
  (hypothesis, not checked: Freedoom's strings replace GZDoom's). The
  detector kept the old spelling as well, so nothing broke. It now accepts
  both, and a test covers each.
- **G3-F2 (CLOSED 2026-10-13; was low, → `mod-engineer`):** `docs/engine/MOD-SPEC.md`
  (the "MAP02's exit" row) said MAP02's end text could be reached "for the
  `exit` console command". It cannot: `exit` quits GZDoom (PM, 2026-10-13
  20:39). Since `87d613b` the row says so, and names the exit switch of
  `d1e891f` as the way out.
- **G3-F4 (fixed in `route-3`, verified by the PM's 21:24 re-run; QA's own
  bug, in `tools/route.py`, not in the map):** a warp keeps the player's
  velocity.
  - Repro: `map02-door` on route-2 (`2026-10-13_2115_F3_g3-map02-map02-door-skill3.log`).
    P4b walks south for 35 tics and ends at (672, 630) with the body still
    gliding; E0 warps to (160, 384), turns west and walks.
  - Expected: E0 ends in the exit alcove (y 352–416), at about (−15, 384),
    as it does in `map02-start` at 21:14. Observed: (16, 345) in the hall,
    against the hall's west wall just south of the alcove's mouth; E1's
    `use` then finds no switch, and the exit is not reached.
  - Cause (an estimate from Doom's friction, 0.90625 a tic, and walking
    speed, about 8.3 units a tic, plus one assumption): six tics after
    P4b's `-forward` the body still moves at about 4.4 units a tic, and it
    glides about 4.4 × 0.906 / 0.094 ≈ 42 more units; E0 ended 39 south of
    its warp. The assumption, not read in
    GZDoom's C++ source: `warp` does not reset velocity. Why
    `map02-start` passed: its E0 follows R1, whose walk ends against the
    hall's north wall, at rest. The same glide shows harmlessly in MAP01:
    A2 warps to (256, 940) and reports (256, 961).
  - Fix (`route-3`): every warp is preceded by `sdstop` and followed by
    `sdangle` or `sdstop`, both of which zero `Actor.Vel` and
    `PlayerInfo.vel`. Tests: `test_every_warp_starts_and_ends_at_rest`,
    and `test_the_pms_map02_door_drift_is_caught_where_it_happened`, a
    `--parse` fixture of the real 21:15 log that must fail at E0 and at
    the exit and nowhere else.
- **G3-F5 (open, low, → `level-designer`; MAP02, not G3):** the range's
  targets open fire on the player at spawn. On every MAP02 run the player
  has already lost health when `god` comes on, 140 tics in (A0 at 91 or
  85, pushed back to x 140–148 from the start's 160). At 21:14 one of the
  14 monsters died with no route kill. Hypothesis, NOT VERIFIED: a
  rifleman in the second row of targets (x 1984) shot the one in front of
  it (x 1856) on the same line. The targets are `ambush` (deaf), not
  blind, and the start faces them down the lane. Whether a range should
  shoot back before the player has armed is a design call; it may be the
  intent ("targets prove damage on a living actor").
- **G3-F3 (open, trivial, → `mod-engineer`):** the same MOD-SPEC row says
  the `map02-start` route reaches the end text by `sdexit`. True of the
  20:52 run; since the 21:14 run `map02-start` presses the exit switch,
  and no built-in route types `sdexit`. One clause to update.
- **Checked: C7 does not use the console `exit`.** It ends MAP01 by its
  exit switch, played. No row in this checklist types `exit`, and
  `tests/test_route.py` fails if a route ever does.

**Verdict:** none yet. **IN PROGRESS.** The route half is green: C1–C3
on all three skills, the second time on the final build (`87d613b`), C5,
C8 and C12. **What is left to close G3:**

1. **C6 and C7: MAP01 played by hand on skills 2 and 4, no cheats** (G3-4;
   C7 is also G3-5's zero-secret run). The route runs play with `god` and
   kill what blocks them, so they prove the path, not the fight. The CEO's
   skill-3 run (D38) is the third of G3-4's three.
2. **C10: the hostile pass on skill 4** (G3-7: every switch twice, every
   door re-entered, every closet and secret in and out, the drops from the
   catwalk and the cradle, the map backwards from the hangar).
3. **G3-9: the CEO's "on point"**, with the `SDCONC2` verdict and M5's
   call (clutter or fine).

Owed alongside, quick and scripted: C5b re-run on `route-3` for a clean
PASS (P4 itself is verified; MAP02's checklist, not G3's), which also
verifies G3-F4's fix. Prudent, not required: `g3-auto` on 2, 3 and 4 once
more on `route-3`, since every warp now stops the body first. G3 is
signed only on a `tools/verify.py full` run.
