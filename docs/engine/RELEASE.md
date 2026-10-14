# RELEASE — the v1 package and the G6 checklist

Living document. Owner: `mod-engineer` (the tool and this checklist);
`qa-engineer` signs G6 off, the PM tags (D6), the CEO decides when anything
is published. Russian mirror: owed (D34), at the same path under `docs/ru/`.

Gate G6 (`docs/ROADMAP.md`): **licence file, credits, README EN/RU, QA
sign-off, tag v1.0.** This document says how the package is made, what the
tool guarantees, and, item by item, what is still missing on 2026-10-14.
**Nothing is published today**: no tag, no GitHub release, no upload.

## 1. Making the package

```bash
.venv/Scripts/python.exe tools/release.py --version 1.0   # Windows; python3 on the Mac
# -> dist/release/sovietdoom-1.0.zip and dist/release/sovietdoom-1.0.zip.sha256
```

`dist/` is gitignored (`.gitignore`, line 2), so the package never enters
the repo. `--version` is mandatory (`1.0`, `1.0.1`, `1.0-rc1`; no leading
`v`: the tag is `v1.0`, the version is `1.0`). The tool refuses a tree with
uncommitted or untracked changes: a release is made from a commit, so the
zip can be traced to it. `--allow-dirty` exists **for the test suite only**
(`tests/test_release.py`); a package made with it says `+dirty` after the
commit in `CREDITS.txt` and `README.txt` and must never be handed out.

### 1.1 What the zip holds

One folder, `sovietdoom-<version>/`, with exactly five files:

| File | Where it comes from |
|---|---|
| `sovietdoom.pk3` | `tools/build.py` on the checked-out tree, the same build CI makes |
| `LICENSE.md` | the repo's `LICENSE.md`, byte for byte |
| `CREDITS.txt` | generated: the in-game credits (`SD_CRED_*` of the PK3's own `LANGUAGE`, English then Russian, in screen order); the lines `docs/sound/MUSIC-RIGHTS.md` §4.5 says to reproduce verbatim; one entry per register row that covers a packed asset (files, origin, licence, and for music the §4.5 obligation) |
| `README.txt` | generated: a short player readme in English and Russian: what it is, the D46 disclaimer, what to download (GZDoom ≥ 4.14.2, D3; Freedoom: Phase 2, tested with 0.13.0, D2; **the IWAD is not included**), how to start it, the basic controls. Map and menu names are read from `LANGUAGE`, so the readme names things as the game does |
| `SHA256SUMS` | `sha256sum -c` format, for the four files above |

Beside the zip, `sovietdoom-<version>.zip.sha256` holds the hash of the zip
itself, for the release page.

### 1.2 What it refuses (exit 1, nothing written)

- A dirty tree without `--allow-dirty`; a malformed or missing version.
- **A packed asset without a licence row.** "Asset" means every file under
  the folders `tools/check_pk3.py` audits (`textures/`, `flats/`, `sprites/`,
  `sounds/`, `music/`, `graphics/`, `patches/`, `hires/`, `fonts/`). Stricter
  than `check_pk3`: the asset must be named in the **first cell of a table
  row** of `docs/art/LICENSES.md` whose table has a Licence column; a name in
  a paragraph does not license anything. A token with a `/`
  (`fonts/bigfont/*.png`) covers that folder and nothing else. **Music**
  also needs its row in `docs/sound/MUSIC-RIGHTS.md` §4.5, the "what ships"
  table.
- **A licence that requires attribution whose name is not in the credits,
  in English and in Russian.** The names come from the registers:
  `credit "Name"` in the licence cell; else, for a cell that says credit,
  `{{Attribution…}}`, CC BY, BSD, MIT or OFL, every bold name in the row;
  `idem` repeats the row above; our own rows (D15) need "Soviet Doom" and
  "CC BY-NC-SA 4.0"; a §4.5 obligation "credit Name" counts too. A row that
  needs a credit and names nobody is an error. CC0 is a courtesy: a missing
  courtesy name is a warning. The credits checked are the `SD_CRED_*` lines,
  which are both the in-game screen and the top of `CREDITS.txt`, so the
  file and the game can never disagree; the provenance list lower down
  does not count as a credit.
- Anything from `work/`, `tools/`, `tests/`, `logs/`, `iwads/`, any preview,
  any IWAD (by its `IWAD` magic, wherever it hides), a `.wad` outside
  `maps/` or a map WAD that is not a PWAD, in the PK3 or in the zip.
- A PK3 that `tools/check_pk3.py` rejects.

### 1.3 Determinism

Same commit, same zip, byte for byte (`tests/test_release.py` builds it twice
and compares). Entries are sorted; every entry carries the commit's own
time (UTC) as its date; the "made on" system and the permissions are fixed
(the zip module would otherwise write 0 on Windows and 3 elsewhere); the
PK3 build is already reproducible (`tools/sdbuild/pk3.py`). Across the two
machines the bytes may still differ if git checks text files out with
different line endings; make the release on one machine (the Windows PC,
D27).

## 2. The G6 checklist, measured 2026-10-14

| # | Item | State | What is missing |
|---|---|---|---|
| 1 | **The phases before it are closed.** F6 follows F3, F4 and F5 (`docs/ROADMAP.md`) | **OPEN** | **G3** in progress: C6 and C7 (MAP01 hand-played on skills 2 and 4, no cheats), C10 (the hostile pass, skill 4) and G3-9 (the CEO's "on point") are owed (`docs/qa/GATE-REVIEWS.md`, G3). **G4** started: every weapon still shows Freedoom placeholder sprites and sounds; hand and glove, ice axe, PPSh-41 and the weapon-sound drafts wait on the CEO. **G5** started: own enemy sprites (the Reich rifleman is a draft) and sounds, the voices on the CEO's takes (D36), and the MAP01 playtest. Until they pass, a package would be a preview, not v1 |
| 2 | **Licence file** | **PARTIAL** | `LICENSE.md` states the dual licence (D15) but says itself that "full licence texts will be added before the v1 release". The GPL-3.0 and CC BY-NC-SA 4.0 texts must be added to the repo (downloading them is the PM's step, with the CEO's OK) and then to `RELEASE_FILES` in `tools/release.py`, with a test |
| 3 | **Credits** | **DONE, engine pass owed** | In game: Options → Soviet Doom → Credits (ADR 009, MOD-SPEC §6.8), guarded by `tests/test_credits.py`. In the package: `CREDITS.txt`, guarded by `tools/release.py` and `tests/test_release.py`. Owed: the PM's engine pass of the screen (D26), and a check that the credits still name everyone when the drafts (own sprites, Kenney sound sets, D44) enter `assets/` with their register rows |
| 4 | **README EN/RU** | **DONE for the package, controls NOT VERIFIED** | `README.txt` in the zip, both languages. The controls listed are GZDoom's defaults as we expect them (W A S D, mouse, E or Space to use, 1–7, Tab, Esc); **NOT VERIFIED** against a fresh GZDoom 4.14.2 configuration: QA checks them in the sign-off run (item 5). The repo `README.md` has both languages; its Russian half was brought level with the English on 2026-10-14 |
| 5 | **QA sign-off** | **OPEN** | `qa-engineer`'s G6 entry in `docs/qa/GATE-REVIEWS.md`, from the package itself, not the repo: (a) `tools/release.py --version 1.0` on a clean tree at the commit to be tagged; (b) `sha256sum -c` on the `.sha256` and on `SHA256SUMS`; (c) unzip into an empty folder with only GZDoom 4.14.2 and `freedoom2.wad`, start it as `README.txt` says (both ways: drag-and-drop and the command line), zero errors in the log (the PM's engine run, D26); (d) MAP01 to the exit and the practice range opened; (e) the credits screen read in English and Russian; (f) the readme's controls tried on a fresh config; (g) the zip listing checked against §1.1 |
| 6 | **Russian mirrors** | **OPEN** | D7 as amended by D34: the mirror is synced in full before release. Missing today (`tools/verify.py` mirror check): `engine/adr/008-diegetic-radio.md`, `engine/adr/009-in-game-credits.md`, `engine/RELEASE.md` (this file), `sound/ENEMY-SOUNDS.md`, `sound/WEAPON-SOUNDS.md`, and five evidence notes under `qa/evidence/` (2026-10-13 20:14, 20:39, 20:57, 22:25, 23:10). Whether the existing mirrors are current is `translator-ru`'s batch and `pmo`'s audit, not a script's |
| 7 | **Tag v1.0** | **OPEN, the PM's** | After 1–6: the PM tags the signed-off commit `v1.0` (D6) and runs `tools/release.py --version 1.0` on it. Publishing the zip (a GitHub release, ModDB) is a separate CEO decision; the repo is private |

### 2.1 Risks to clear before tagging

- **The Impact font in text-bearing textures.** `docs/art/LICENSES.md`
  ("Fonts used to rasterise Cyrillic text") records the position that
  rasterised pixels are not covered by the font licence as **NOT VERIFIED
  by a lawyer**, and offers the clean route: re-render with an OFL font and
  have the CEO re-approve. `qa-engineer` decides at sign-off whether to ask.
- **Drafts are not v1 content.** `tools/make_draft_overlay.py` packs drafts
  into `work/overlays/`, which the release never touches; anything a player
  should get must first be approved into `assets/` with its register row.
- **CI does not run `tools/release.py`.** The suite runs it (twice) on every
  push through `tests/test_release.py`, with `--allow-dirty` semantics; the
  clean-tree refusal itself is only exercised with a stubbed git state.

## 3. Conventions the tool relies on

For the art-director's and the sound-designer's registers, so that a new row
is read correctly:

- Put the lump name (or a folder token like `fonts/<name>/*.png`) in
  backticks in the **first cell** of a table row whose table has a column
  named Licence (or "Origin and licence").
- When a licence obliges a credit, write it as `credit "Name" is required`
  in the licence cell. Bold names in the row also work; a row that needs a
  credit and names nobody stops the release.
- New music: a row in LICENSES.md § Music **and** in MUSIC-RIGHTS §4.5, with
  its Obligation cell either `credit Name` or `none`.
- Then add the name to the `SD_CRED_*` lines in both languages
  (`tests/test_credits.py` already demands it for the screen).
