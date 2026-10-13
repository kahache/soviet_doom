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
