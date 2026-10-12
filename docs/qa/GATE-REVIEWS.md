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
