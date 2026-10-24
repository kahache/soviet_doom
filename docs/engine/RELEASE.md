# RELEASE — the v1 package and the G6 checklist

Living document. Owner: `mod-engineer` (the tool and this checklist);
`qa-engineer` signs G6 off, the PM tags (D6), the CEO decides when anything
is published. Russian mirror: after the MVP (D75, ROADMAP P3), at the same
path under `docs/ru/`.

Gate G6 (`docs/ROADMAP.md`, M4): **licence file, credits, README EN/RU, the
in-game Russian text reviewed (N11), QA sign-off, tag v1.0.** The
`docs/ru/` documentation mirror is not a G6 item (D75; row 6 below). The
step-by-step sign-off is `docs/qa/2026-10-20_1230_M4_v1-signoff-plan.md`.
This document says how the package is made, what the
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

One folder, `sovietdoom-<version>/`, with exactly eight files:

| File | Where it comes from |
|---|---|
| `sovietdoom.pk3` | `tools/build.py` on the checked-out tree, the same build CI makes |
| `LICENSE.md` | the repo's `LICENSE.md`, as git stores it (LF line endings) |
| `LICENSE-GPL-3.0.txt` | the full GNU GPL v3 text (the code's licence, D15), byte for byte as https://www.gnu.org/licenses/gpl-3.0.txt served it; SHA-256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |
| `LICENSE-CC-BY-NC-SA-4.0.txt` | the full CC BY-NC-SA 4.0 legal code (the assets' and docs' licence, D15), byte for byte as https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt served it; SHA-256 `e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd` |
| `LICENSE-FREEDOOM-BSD-3.txt` | Freedoom's BSD-3 notice (copyright, conditions, disclaimer), the licence of the Freedoom pixels the PK3 packs (today the TT-33 hands, `SDTT` A-C, D61), byte for byte as https://raw.githubusercontent.com/freedoom/freedoom/v0.13.0/COPYING.adoc served it (Freedoom v0.13.0, the IWAD we test with, D2; downloaded by the PM, D75); SHA-256 `ed60abcf1ff64bf61bf8b4c585ab63643d655a21f8997ba284c01f94ed681fc5`. BSD-3 clause 2 asks the notice to travel with every binary redistribution |
| `CREDITS.txt` | generated, for a player who has the package and not the repo (backlog G9): the in-game credits (`SD_CRED_*` of the PK3's own `LANGUAGE`, English then Russian, in screen order, and since v1.1 (P6) the Catalan `[ca]` screen as a last section, which carries the short AI form `SD_CRED_AI_*`); the AI disclosure (D75, D79, D93) in each language half (`ai_disclosure()`): one paragraph per AI tool and what it did (Claude's paragraph says it translated the text into Russian and Catalan), Claude (Anthropic) through Claude Code, Google Gemini, Fooocus / SDXL and Chatterbox (Resemble AI); the two claims that depend on the package are read from it (`ai_ships()`): the sergeant's face appears once our `STF*` lumps are packed, and the Chatterbox paragraph says the enemies speak with Freedoom's voices until a packed sound's register row names Chatterbox; the lines `docs/sound/MUSIC-RIGHTS.md` §4.5 says to reproduce verbatim; one entry per register row that covers a packed asset (files, origin, licence, and for music the §4.5 obligation); a closing line naming the three full texts. Its headings and its own sentences name no repo path (`CREDITS_HEADINGS`; `CreditsTextTest`, fast tier); the register cells it quotes (an Origin may name its generator) are quoted, not edited |
| `README.txt` | generated (`README_TEMPLATE` in `tools/release.py`): the player readme, English then Russian: what it is and the D46 disclaimer; what is in it (the campaign's three maps in play order, MAP01 → MAP02 → MAP03, which ends the episode, under New Game → Soviet Doom; the practice range under New Game → Practice Range; the five difficulties by their first and last name); what to download (GZDoom ≥ 4.14.2, D3; Freedoom: Phase 2, tested with 0.13.0, D2; **the IWAD is not included**; the Freedoom download holds two WADs and the game needs `freedoom2.wad`); the three in-game languages (English, Russian and Catalan, v1.1); how to start it on Windows (drag-and-drop, choosing Freedoom: Phase 2 if GZDoom asks; the command line, and `.\gzdoom` in PowerShell) and on macOS and Linux; where the language switch (Automatic, English, Russian or Catalan) and the credits are; GZDoom 4.14.2's default controls for a new configuration (W A S D, mouse, E uses, **Space jumps**, Shift runs, 1–7 and the wheel, Tab, F2/F3 and F6/F9, Esc; Ctrl and the arrows are unbound, G6 review §3.2); the licence; what it was made with (D93; MADE WITH / ЧЕМ СДЕЛАНО, `render_made_with()`): GZDoom and Freedoom, the AI tools with one line each (the face and voices lines follow `ai_ships()` as in CREDITS.txt), the CC0 sound packs (Kenney, rubberduck, Darsycho), the public-domain music and its MIDI sequencers (Jerry Engelbach, Peter Gerloff) and the tooling (Python, Pillow, NumPy, FFmpeg); the hash check for Linux (`sha256sum -c`), macOS (`shasum -a 256 -c`) and Windows (`Get-FileHash`, `certutil -hashfile`). Every map, episode, menu, skill and language name is read from `LANGUAGE` (`README_IDS`), so the readme names things as the game does, and a missing id refuses the release. It names only files inside the package, never a repo path. Pinned by `ReadmeTest` in `tests/test_release.py` (fast tier) |
| `SHA256SUMS` | `sha256sum -c` format, for the seven files above |

Beside the zip, `sovietdoom-<version>.zip.sha256` holds the hash of the zip
itself, for the release page.

### 1.2 What it refuses (exit 1, nothing written)

- A dirty tree without `--allow-dirty`; a malformed or missing version.
- **A full licence text that is missing or not the published one.** All
  three are pinned by SHA-256 in `LICENCE_TEXTS` (`tools/release.py`) and
  checked before anything is built: an edit, a re-wrap or a truncation stops
  the release. They are never edited; to restore one, check it out from git.
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
D27). Line endings never reach the shipped licence files: `LICENSE.md` is
read as text (CRLF becomes LF), and the three full texts, which hold no CR at
all, have any CRLF turned back into LF before their hash is checked. The
repo has no `.gitattributes` and this PC runs `core.autocrlf=true`, so a
fresh Windows checkout may write them with CRLF; the zip is the same either
way.

## 2. The G6 checklist, measured 2026-10-14

| # | Item | State | What is missing |
|---|---|---|---|
| 1 | **The phases before it are closed.** F6 follows F3, F4 and F5 (`docs/ROADMAP.md`) | **OPEN** | **G3** in progress: C6 and C7 (MAP01 hand-played on skills 2 and 4, no cheats), C10 (the hostile pass, skill 4) and G3-9 (the CEO's "on point") are owed (`docs/qa/GATE-REVIEWS.md`, G3). **G4** started: every weapon still shows Freedoom placeholder sprites and sounds; hand and glove, ice axe, PPSh-41 and the weapon-sound drafts wait on the CEO. **G5** started: own enemy sprites (the Reich rifleman is a draft) and sounds, the voices on the CEO's takes (D36), and the MAP01 playtest. Until they pass, a package would be a preview, not v1 |
| 2 | **Licence file** | **PASS** (2026-10-14, backlog N10; Freedoom's notice added 2026-10-15, backlog G9, D75) | Nothing. **G9 (2026-10-15):** `LICENSE-FREEDOOM-BSD-3.txt` ships as the third pinned text (`LICENCE_TEXTS`, the same CRLF-safe read, in `SHA256SUMS`), because the TT-33 frames carry Freedoom's pixels; `LICENSE.md` gives Freedoom-derived art its own bullet and its own line among the third parties, drops OTEX (no OTEX texture is used: nothing under `src/` or `assets/` names it, pinned by `test_no_otex_texture_is_packed`), says that in the package `CREDITS.txt` reproduces the registers, and its Russian half names the same third parties (wording reviewed in N11). Earlier, N10: `LICENSE.md` states the dual licence (D15) and points to the two full texts beside it in the repo root: `LICENSE-GPL-3.0.txt` (code), from https://www.gnu.org/licenses/gpl-3.0.txt, SHA-256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`, and `LICENSE-CC-BY-NC-SA-4.0.txt` (assets and documentation), from https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt, SHA-256 `e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd`, downloaded verbatim by the PM with the CEO's permission. Both are in `RELEASE_FILES` and in `SHA256SUMS`; `README.txt` and `CREDITS.txt` name them. Guarded by `tests/test_release.py`: `LicenceTextTest` (fast tier: the repo files hash to the published texts, the tool pins the same hashes and sources, `LICENSE.md` names each file in the bullet of what it covers, an edited or missing text is refused before the build) and `RealReleaseTest` (art tier: the texts in the zip byte-identical to the repo files) |
| 3 | **Credits** | **DONE, engine pass owed** | 2026-10-15 (G9): `SD_CRED_IWAD_4`/`_5` now say the TT-33 hands are Freedoom's, recoloured, and the other placeholders are read from the IWAD; `SD_CRED_SRC_4`-`_6` carry the AI line (D75) under Sources, both languages, 40 characters at most; the engine pass of these lines is owed with the rest. In game: Options → Soviet Doom → Credits (ADR 009, MOD-SPEC §6.8), guarded by `tests/test_credits.py`. In the package: `CREDITS.txt`, guarded by `tools/release.py` and `tests/test_release.py`. Owed: the PM's engine pass of the screen (D26), and a check that the credits still name everyone when the drafts (own sprites, Kenney sound sets, D44) enter `assets/` with their register rows |
| 4 | **README EN/RU** | **DONE for the package (2026-10-15, backlog G2); controls to confirm in the sign-off; Russian to N11** | `README.txt` in the zip, both languages, rewritten from the G6 review's proposal (`docs/qa/2026-10-14_2356_G6-readiness.md` §2.4, §5): three maps instead of one, the practice range, Phase 2, launch lines for PowerShell, macOS and Linux, a hash check for each system, and the controls corrected (Space jumps, it does not use; Ctrl and the arrows are unbound). The controls are the bindings the review read in the installed `gzdoom.pk3` (`engine/commonbinds.txt` + `engine/defbinds.txt`) and found in the CEO's `gzdoom.ini`; that a new install gets exactly these is **NOT VERIFIED until the sign-off run** on a fresh configuration (move `gzdoom.ini` aside, never delete it), which also checks the IWAD question with both Freedoom WADs present (item 5). The Russian half is reviewed once by `translator-ru` in N11 (D60), with the `[ru]` strings of `LANGUAGE` it quotes. If jumping is forbidden (G6 review G17), the Jump line changes. The repo `README.md` has both languages; its Russian half was brought level with the English on 2026-10-14 |
| 5 | **QA sign-off** | **OPEN** | `qa-engineer`'s G6 entry in `docs/qa/GATE-REVIEWS.md`, from the package itself, not the repo: (a) `tools/release.py --version 1.0` on a clean tree at the commit to be tagged; (b) `sha256sum -c` on the `.sha256` and on `SHA256SUMS`; (c) unzip into an empty folder with only GZDoom 4.14.2 and `freedoom2.wad`, start it as `README.txt` says (both ways: drag-and-drop and the command line), zero errors in the log (the PM's engine run, D26); (d) MAP01 to the exit and the practice range opened; (e) the credits screen read in English and Russian; (f) the readme's controls tried on a fresh config; (g) the zip listing checked against §1.1. The full ordered checklist (fresh config with `gzdoom.ini` moved aside, the IWAD question with both Freedoom WADs, both launch methods, the campaign on skills 2/3/4, every weapon, pickup, enemy, HUD, menu and text in EN and RU) is `docs/qa/2026-10-20_1230_M4_v1-signoff-plan.md` |
| 6 | **Russian: the in-game text (N11), not the docs mirror** | **OPEN (N11)**; the docs mirror **out of G6** (D75, 2026-10-20 G10) | **Required for v1:** `translator-ru` reviews, once and after the last string lands (M2a-i pickup lines, M2e quit lines), everything Russian a player reads: the `[ru]` half of `LANGUAGE` (menus, credits, pickups, obituaries, transition and end texts, quit messages), the Russian half of `README.txt` (`README_TEMPLATE`, `tools/release.py`) and of `LICENSE.md` (N11, D60; scope in `docs/qa/2026-10-14_2356_G6-readiness.md` §2.5). The sign-off then reads it on screen with `language ru`. **Not required for v1:** the `docs/ru/` mirror of the repo documentation. D75 (CEO, 2026-10-15) moved it after the MVP (ROADMAP P3), superseding, for this release, D34's "in full before release": the player never reads `docs/`. The `tools/verify.py` docs stage keeps reporting missing mirrors as a WARN; that WARN does not block G6 |
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

## 4. Portable packages (P5)

ROADMAP P5 (D93), pulled forward for the CEO's friends: one download per OS
that needs nothing else. **Windows** (`tools/release_portable.py`,
2026-10-20), **macOS and Linux** (`--platform macos|linux`, 2026-10-21,
D101/D102; see 4.5). Windows is the default platform.

### 4.1 Making the Windows package

```bash
.venv/Scripts/python.exe tools/release.py --version 1.0 --out-dir <dir>     # or the v1.0 release asset
.venv/Scripts/python.exe tools/release_portable.py --version 1.0 --out <outside-the-repo> \
    --release-zip <dir>/sovietdoom-1.0.zip
# -> <out>/sovietdoom-1.0-windows.zip and sovietdoom-1.0-windows.zip.sha256
```

`--out` is mandatory and must be **outside the repo** (the zip is ~36 MB:
GZDoom and Freedoom are in it). `--release-zip` repackages a zip made by
`tools/release.py` (checked: one folder, exactly its eight files, its
SHA256SUMS true), so the portable package carries the very PK3 that was
signed off; without it, the tool runs `release.make_release` on the tree
(dirty trees refused unless `--allow-dirty`, tests only). The engine comes
from the local install (`%LOCALAPPDATA%\Programs\GZDoom`, or `--engine-dir`)
and must be g4.14.2; `freedoom2.wad` comes from `iwads/` and must be
Freedoom 0.13.0 (SHA-256 `a8772e08…`, pinned). Nothing is downloaded.
Same inputs, same bytes: entries sorted, every timestamp the release zip's
(the commit's time). Tests: `tests/test_release_portable.py`
(`RealPortableTest`, which needs the installed engine, is in the art tier
and skips on CI).

### 4.2 What the zip holds

One folder, `SovietDoom/`. Languages (D129): the game, `README.txt` and
`CREDITS.txt` are English, Russian and Catalan; the launchers and
`README-FIRST.txt` are English. No Spanish file or text ships (the packages
built before D129, v1.0's among them, also carried `Jugar Soviet Doom.*`,
`jugar.sh` and a Spanish `LEEME.txt`); `tests/test_no_spanish.py` guards it.

| File | Why |
|---|---|
| `Play Soviet Doom.bat` | the launcher: `cd /d "%~dp0"`, then `start "" "%~dp0gzdoom.exe" -iwad "%~dp0freedoom2.wad" -file "%~dp0sovietdoom.pk3"`. If `gzdoom.exe` is not beside the .bat (opened from inside the zip without extracting) it says to extract first and waits. ASCII and CRLF |
| `README-FIRST.txt` | English: unzip anywhere but Program Files, double-click, SmartScreen ("More info → Run anyway"; or tick "Unblock" on the zip before extracting), Russian or Catalan (the menu path read from `LANGUAGE`, English labels: Options > Soviet Doom > Language > Russian / Catalan), the keys, where saves live, the licences. UTF-8 with BOM, CRLF |
| `gzdoom.exe`, `gzdoom.pk3`, `zmusic.dll`, `openal32.dll`, `sndfile.dll`, `licenses.zip`, `soundfonts/`, `fm_banks/`, `lights.pk3`, `brightmaps.pk3`, `game_support.pk3`, `game_widescreen_gfx.pk3` | GZDoom g4.14.2 for Windows, unmodified. Only these names are copied (`ENGINE_FILES`, `ENGINE_DIRS`): a user's ini, `Save/`, screenshots or WADs in the install folder never ship |
| `gzdoom_portable.ini` | GZDoom's portable switch (4.3); comment lines only, GZDoom fills it on the first run |
| `freedoom2.wad`, `LICENSE-FREEDOOM-BSD-3.txt` | Freedoom: Phase 2 0.13.0 and its BSD notice |
| `sovietdoom.pk3`, `LICENSE.md`, `LICENSE-GPL-3.0.txt`, `LICENSE-CC-BY-NC-SA-4.0.txt`, `CREDITS.txt` | the release's files, byte for byte |
| `README.txt` | the release's readme with a note on top (EN/RU) saying GZDoom and Freedoom are already here |
| `GZDOOM-SOURCE.txt` | GPL: the exact source, attached to the v1.0 release as `gzdoom-g4.14.2-source.tar.gz`, `openal-soft-1.23.1-source.tar.gz`, `libsndfile-1.2.2-source.tar.gz`, `zmusic-1.1.14-source.tar.gz` (since 2026-10-21), and the `g4.14.2` tag and its source archives on GitHub; the DLLs' libraries and their source; a written offer; the SHA-256 of every engine file |
| `SHA256SUMS` | every other file of the folder |

### 4.3 How GZDoom behaves (read from the g4.14.2 source, not run by an agent)

- **No IWAD picker.** [d_iwad.cpp](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/d_iwad.cpp), `IdentifyVersion`: the picker opens
  when `queryiwad` is on and there is no `-iwad`, or when more than one
  candidate remains; a found `-iwad` leaves one. So `-iwad` alone suffices,
  even on a PC with Steam/GOG Doom installed; no `+queryiwad 0` (a `+`
  command runs after the IWAD is chosen anyway). The path is absolute
  because a relative `-iwad` is only looked up in the config's IWAD search
  directories.
- **Portable config.** [i_specialpaths.cpp](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_specialpaths.cpp),
  `IsPortable`: if the program folder is not under `%ProgramFiles%` or
  `%ProgramFiles(x86)%`, and `gzdoom_portable.ini` exists in it and opens
  for read and write, GZDoom prints "Using portable configuration" and uses
  that file as its ini; `Save/`, `Screenshots/` and `Demos/` go in the
  program folder too, and the "documents" path is the program folder.
  Under Program Files, or read-only, it falls back to
  `Documents\My Games\GZDoom` (hence "not in Program Files" in the guides).
  `M_GetAppDataPath` and `M_GetCachePath` ignore portability
  (`%LOCALAPPDATA%\gzdoom`, `%LOCALAPPDATA%\zdoom\cache`); on this PC
  neither folder exists after every engine run of the project, so nothing
  observed is written there. NOT VERIFIED by running the bundle: the PM
  tests it (unzip to a fresh folder, run the .bat, check the log says
  "Using portable configuration" and that `Save\` appears in the folder).
- **SmartScreen.** GZDoom is unsigned. A zip downloaded from the web
  carries the mark of the web, and Explorer passes it on to the extracted
  files, so Windows may show "Windows protected your PC" or the "Open
  File - Security Warning". Unblocking the zip before extracting removes
  the mark. Signing would need a code-signing certificate (not planned).

### 4.4 GPL and the other platforms

GZDoom is GPL 3.0, OpenAL Soft and libsndfile LGPL. Distributing their
binaries from a server is GPL 3.0 §6(d): offer the corresponding source
"in the same way through the same place", or on another server with clear
directions next to the binaries; we stay responsible for it remaining
available. Since 2026-10-21 the source archives of GZDoom g4.14.2, OpenAL
Soft 1.23.1, libsndfile 1.2.2 and ZMusic 1.1.14 are attached to the
[v1.0 release](https://github.com/kahache/soviet_doom/releases/tag/v1.0);
`GZDOOM-SOURCE.txt` (every platform) names them first, then the upstream
links and the written offer. They stay valid for every package that ships
g4.14.2, whatever the mod's version.

### 4.5 macOS and Linux

```bash
python tools/release_portable.py --platform macos --version 1.0 --out <outside-the-repo> \
    --release-zip <dir>/sovietdoom-1.0.zip --engine-archive <dl>/gzdoom-4-14-2-macos.zip
python tools/release_portable.py --platform linux --version 1.0 --out <outside-the-repo> \
    --release-zip <dir>/sovietdoom-1.0.zip --engine-archive <dl>/gzdoom_4.14.2_amd64.deb \
    --gzdoom-source <dl>/gzdoom-g4.14.2-source.tar.gz
# -> sovietdoom-1.0-macos.zip / sovietdoom-1.0-linux.tar.gz, each with its .sha256
```

The engine archives are the official g4.14.2 downloads from
[GZDoom's release page](https://github.com/ZDoom/gzdoom/releases/tag/g4.14.2),
read as data (never run, never extracted to disk). The tool checks the
version (`Info.plist` `CFBundleShortVersionString`, the `.deb` control
`Version`, and the `g4.14.2` string in the executable), refuses unsafe paths
and symlinks that leave the engine folder, and lists what it leaves out.

**macOS** (`sovietdoom-<v>-macos.zip`, folder `SovietDoom/`):

| File | Why |
|---|---|
| `GZDoom.app/` | every entry of the official zip under `GZDoom.app/`, bytes and `external_attr` copied verbatim: `Contents/MacOS/gzdoom` stays 755 (a universal x86_64 + arm64 binary, macOS 10.15+ per `Info.plist`), symlinks stay symlinks (g4.14.2 has none), and the AppleDouble `._*` files beside the data files in `Contents/MacOS/` ship too: they hold the `com.apple.cs.*` code-signature attributes of those files, and macOS's unzip turns them back into attributes |
| `gzdoom-licenses/` | the official zip's `Licenses/` (GPL, LGPL, BSD and the others) |
| `Play Soviet Doom.command` | sh, mode 755, LF: `cd "$(dirname "$0")"`, then `exec GZDoom.app/Contents/MacOS/gzdoom -iwad freedoom2.wad -file sovietdoom.pk3 -config gzdoom.ini -savedir saves` with absolute paths built from the folder; if the engine is missing, a message and a wait for Enter |
| `README-FIRST.txt` | English, UTF-8 with BOM (TextEdit), LF: Gatekeeper (`xattr -dr com.apple.quarantine SovietDoom`, or right-click → Open; on macOS 15+ System Settings → Privacy & Security → Open Anyway), Russian or Catalan, keys, saves |
| the rest | as on Windows: `freedoom2.wad`, the release's files, `README.txt` with a macOS note, `GZDOOM-SOURCE.txt` (the libraries linked into the executable: ZMusic, OpenAL Soft, libsndfile 1.2.2, MoltenVK), `SHA256SUMS` (every regular file except the `._*` ones, which are gone after macOS unzips) |

**Linux** (`sovietdoom-<v>-linux.tar.gz`, folder `SovietDoom/`): a tarball
because a zip loses the modes with many unzippers.

| File | Why |
|---|---|
| `gzdoom/` | `/opt/gzdoom` of the `.deb` (ar archive → `data.tar.xz`, parsed in Python, no dpkg): `gzdoom` (RPATH `$ORIGIN`, so it finds `libzmusic.so.1` beside it), the engine pk3s, `soundfonts/`, `fm_banks/`. The `/usr/games` wrapper, the `.desktop` file and the icon are left out |
| `gzdoom-licenses/` | `docs/licenses/` of `gzdoom-g4.14.2-source.tar.gz` (`--gzdoom-source`): the `.deb` ships no licence texts |
| `play.sh` | mode 755, same command as the `.command` files, no wait |
| `README-FIRST.txt` | English, UTF-8, LF: the `.deb` control's `Depends` (read from the file, not copied by hand), its `Recommends` (`libopenal1`: no sound without it), plus `libsndfile1` (`libzmusic.so.1` names `libsndfile.so.1` and the mod's sounds are OGG; the `.deb` does not declare it), and one `sudo apt install` line for them; Ubuntu 24.04+ may need `libasound2t64` for `libasound2` (NOT VERIFIED) |
| the rest | `freedoom2.wad`, the release's files, `README.txt` with a Linux note, `GZDOOM-SOURCE.txt`, `SHA256SUMS` |

Tar entries: sorted, every parent folder present, folders and executables
755, other files 644, owner root (0:0), every mtime the release zip's, GNU
format; the gzip header carries no name and no time. Same inputs, same bytes
(both packages, checked by rebuilding).

**Verified on this PC (Windows, 2026-10-21):** listings, modes, that every
`GZDoom.app` entry equals the official zip's (bytes and `external_attr`), the
PK3 equals the v1.0 release's, `sha256sum -c SHA256SUMS` passes in both
extracted folders, `sh -n` parses the four launchers, two builds give the
same bytes. **NOT VERIFIED:** running either package. Nobody has opened the
macOS zip on a Mac (Archive Utility's handling of the `._*` files,
Gatekeeper's dialogs, `-savedir`/`-config` in practice), and WSL is not
installed here, so the Linux package has not run on Linux (the library
list comes from the `.deb` control and the strings in the binaries).
