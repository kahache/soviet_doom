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

**NOT VERIFIED until the PM's first run:** that the helper's ZScript
compiles and prints as written. Every engine name it uses was read from
g4.14.2's `gzdoom.pk3` on 2026-10-13. If the helper does not compile, the
log shows a `Script error` naming `SDRouteHelper`. In that case
`--minimal-helper` runs only the part the PM has already proven in the
engine (angle, hurt, count), without the inventory.

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
| C1 | Q6, the start inventory, scripted, skill 2 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 2 --keep-evidence` | Report row `[ok ] A0: raised slot 2 (SD_Tokarev), 50 rounds; owned [2:SD_Tokarev]`. Report row `[ok ] R1: …; owned [1:SD_IceAxe, 2:SD_Tokarev]`. Doors ok, exit REACHED, VERDICT PASS (the route half of G3-4, `god` on) | `<stamp>_F3_g3-map01-g3-auto-skill2.log`, `…-skill2-report.txt`, `…-skill2-a0.png`, `…-skill2-r1.png`, `…-skill2-end.png` |
| C2 | Q6, the same on skill 3, and a filed skill-3 log for G3-2 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 3 --keep-evidence` | As C1 | `<stamp>_F3_g3-map01-g3-auto-skill3{.log,-report.txt,-a0.png,-r1.png,-end.png}` |
| C3 | Q6, the same on skill 4 | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --skills 4 --keep-evidence` | As C1 | `<stamp>_F3_g3-map01-g3-auto-skill4{.log,-report.txt,-a0.png,-r1.png,-end.png}` |
| C4 | Q6 by eye: the TT-33 is raised on spawn, slot 1 is empty, the rack pickup works | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=3 tools/run.sh -nomonsters +screenshot_dir "$PWD/logs/shots"`. At spawn, console `screenshot`. Press `1`, then `screenshot`. Walk to the rack on the west wall (or console `warp 40 384`, face west, walk forward). Press `1`, then `screenshot`. `quit` | Shot 1: the TT-33 in hand. Shot 2: still the TT-33. The log has `An ice axe.` (`SD_PICKUP_ICEAXE`) once. Shot 3: the ice axe raised. `.venv/Scripts/python.exe tools/route.py --scan logs/gzdoom.log` gives VERDICT PASS | `<stamp>_F3_g3-start-tt33-raised.png`, `<stamp>_F3_g3-start-slot1-empty.png`, `<stamp>_F3_g3-rack-iceaxe.png`, `<stamp>_F3_g3-start-inventory.log` (a copy of `logs/gzdoom.log`) |
| C5 | Q6 on the test range (optional, about 10 s) | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route map02-start --skills 3 --keep-evidence` | Rows A0 and R1 `[ok ]`, VERDICT PASS | `<stamp>_F3_g3-map02-map02-start-skill3{.log,-report.txt,-a0.png,-r1.png}` |
| C6 | Q1, Q2, Q3 and Q5: G3-4 on skill 2, played, no cheats | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=2 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. Play from the start to the exit switch with no console command. Console `screenshot` facing the exit switch (the HUD shows health and ammo), then `screenshot` at the intermission, then `quit`. Copy `logs/gzdoom.log` to the evidence name, then run `.venv/Scripts/python.exe tools/route.py --scan docs/qa/evidence/<stamp>_F3_g3-map01-skill2-run.log` | Intermission reached. `--scan` VERDICT PASS (G3-2: 0 hits). Notes: time, health, deaths, any monster that never left a doorway or a closet mouth (Q3), anything that felt lavish (Q5) | `<stamp>_F3_g3-map01-skill2-run.log`, `<stamp>_F3_g3-map01-skill2-at-exit.png`, `<stamp>_F3_g3-map01-skill2-intermission.png`, notes in `<stamp>_F3_g3-map01-notes.md` |
| C7 | Q1, Q2, Q3, Q4 and Q5, plus G3-5's zero-secret run: skill 4, played, no cheats, **no secret entered** | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=4 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. As C6, and do not enter S1, S2 or S3. Then `grep -c "A secret is revealed" docs/qa/evidence/<stamp>_F3_g3-map01-skill4-run.log`, and `--scan` as in C6 | Intermission reached. `--scan` PASS. The grep prints `0`. Notes: ammo at the exit (from the HUD shot), and whether the player was ever left with only the ice axe (Q4) | `<stamp>_F3_g3-map01-skill4-run.log`, `<stamp>_F3_g3-map01-skill4-at-exit.png`, `<stamp>_F3_g3-map01-skill4-intermission.png`, notes in `<stamp>_F3_g3-map01-notes.md` |
| C8 | Q7: G3-5's `-nomonsters` run | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --nomonsters --skills 3 --keep-evidence` | Exit REACHED, `monsters: engine 0, map data 0`, VERDICT PASS | `<stamp>_F3_g3-map01-g3-auto-skill3-nomonsters{.log,-report.txt,-end.png}` |
| C9 | Q7: every secret entered and left | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route g3-secrets --skills 4 --keep-evidence` | `secrets : 3 of 3`, exit REACHED, VERDICT PASS | `<stamp>_F3_g3-map01-g3-secrets-skill4{.log,-report.txt,-s1.png,-s2.png,-s3.png,-end.png}` |
| C10 | Q7: G3-7, the hostile pass, skill 4 | `SD_ALLOW_ENGINE=1 MAP=MAP01 SKILL=4 tools/run.sh +screenshot_dir "$PWD/logs/shots"`. `god` is allowed here: this tests the map, not the fight. Do every item of G3-7 in §11: throw each switch twice, re-enter every door, walk into each monster closet and back out, enter each secret and leave, drop off the catwalk and the cradle from all four sides, and play backwards from the hangar | "Could not get stuck". `--scan` PASS | `<stamp>_F3_g3-map01-hostile-skill4.log`, a `screenshot` of any place that traps the player, notes in `<stamp>_F3_g3-map01-notes.md` |
| C11 | Q8: the mural, M1–M5 (§17.13) | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/route.py --route mural --skills 3 --nomonsters --hide-weapon --keep-evidence` | M1: the whole mural, nothing square in front of it, the lectern to its right. M2: the inner columns either side of the tribune. M3a and M3b: the mural whole, at most a sliver behind the jamb. M4: the lectern's plank top level, no HOM or seam at the step. M5: the health bonus at the mural's foot is visible, for the CEO's call (clutter or fine). The report shows six `[ok ]` steps, all in Z4 | `<stamp>_F3_g3-map01-mural-skill3-nomonsters{.log,-report.txt,-m1.png,-m2.png,-m3a.png,-m3b.png,-m4.png,-m5.png}` |
| C12 | Q8: the last part of M4, by hand | In any C4 or C6 session: `warp 400 1320`, then walk onto the health bonus at (432, 1400) | The bonus is picked up (its message is in the log) | `<stamp>_F3_g3-map01-m4-bonus.png` |

**What the checklist does not do.** G3-9 is the CEO's: the "on point"
verdict and the `SDCONC2` verdict. The route runs (C1–C3, C5, C8, C9, C11)
play with `god` on. They prove the path, the doors, the exit and the
inventory; they do not prove the fight. For G3-4, only C6, C7 and the
CEO's skill-3 run count.

### Findings so far

- **G3-F1 (open, low, → `level-designer`; static, NOT VERIFIED in the
  engine):** the health bonus at (432, 1400) on the tribune can be reached
  only through gaps exactly one body wide:
  - between the lectern (x 384…416, y 1344…1376) and the floor lamp at
    (464, 1376) (radius 16, so x 448…480): a 32-unit lane at x 416…448;
  - behind the lectern (y 1376…1408, up to the north wall): also 32.

  A player of radius 16 fits with zero tolerance. Doom allows touching, so
  it should pass; C12 checks it. If the engine refuses, the map shows a
  pickup it does not give, the same pattern as the CEO's rack bug.
- **Fixed in `tools/route.py` before its first run:** the god-mode
  detector looked for "God mode on". GZDoom answers `god` with
  `STSTR_DQDON`, "Degreelessness Mode ON" (g4.14.2's `language.csv`), so
  the report would have said god was never on. It now matches the real
  string, and a test covers it.

**Verdict:** none yet. **IN PROGRESS.** G3 waits on C1–C12 and on the
CEO's G3-9.
