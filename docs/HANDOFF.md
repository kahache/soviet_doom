# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-21, ~23:30 (night shift closed, D102/D103). Before that: 2026-10-20, ~16:40 (Product + pmo, stages 6 and 7, after the v1.0
sign-off). Decisions up to **D99** are in `docs/PRD.md`; open CEO items in
`docs/PENDING-CEO-DECISIONS.md`; tasks and V2 estimates in `docs/BACKLOG.md`;
the checkpoint for the CEO is
`docs/product/2026-10-20_1639_P0_v1-roadmap-checkpoint.md`.

## NIGHT SHIFT 2026-10-21 (D102) — DONE 23:30; the morning report is `docs/product/2026-10-21_2330_P0_informe-noche.md`

The CEO is asleep and wants everything advanced; ask him nothing until morning.
Work items, in this order (tick them here as they land):
1. [x] **Cursor:** GZDoom's menu mouse pointer (Freedoom's `doomcurs`/CursorPic) -> our hammer and sickle (GameInfo `CursorPic`), EN/RU-neutral. Small.
2. [x] **P5:** PM downloads GZDoom g4.14.2 macOS + Linux builds and the source archives (GZDoom g4.14.2, OpenAL Soft 1.23.1, libsndfile 1.2.2, ZMusic) into isolated scratch dirs; attach the sources to release v1.0; agents build `sovietdoom-1.0-macos.zip` and `-linux.tar.gz` (tools/release_portable.py), test Linux under WSL if available; upload to v1.0.
3. [x] **v1.1:** real dog sounds for the Reich hound (licence-clean CC0/CC-BY, sound-designer; listening page for the morning, do not install unheard), and a clear EN/RU "press USE to continue" prompt on death that restarts the level.
4. [x] **P2 drafts:** the 4 voices still Freedoom's (rifleman pain, trooper death, General pain/death) with the aggressive references; listening page; do not install unheard.
5. [x] **P6 Catalan:** a third language (every LANGUAGE id in `[ca]`, the language option, a CA status-bar label band, README/CREDITS CA section); the CEO reviews in the morning.
6. [x] ~~**P1 analysis**~~ dropped 2026-10-21 night: the CEO played the campaign and finds it fine; P1 stays parked in V2 until a player complains about difficulty.
Closed 23:30: v1.1 DRAFT release created (not public, 8 assets, target 594eeef); macOS/Linux packages on v1.0; dog and P2 voice listening pages waiting for the CEO (nothing installed); Chatterbox server stopped (poisoned by a CUDA assert, see the P2 page). Earlier: GPL/LGPL sources attached to release v1.0 (4 tarballs). Agents running: P5 macOS/Linux packaging, cursor + death prompt, dog sounds, P2 voices, P6 Catalan (owner of LANGUAGE; adds SD_DEATH_PROMPT in EN/RU/CA). WSL is not installed: the Linux package cannot be run here.
7. [x] At the end: verify fast, engine pass, v1.1 **draft** release (not public), stage 6 docs, a Spanish morning report for the CEO.
Rules: commit with explicit paths; agents never commit; one owner per shared file (LANGUAGE, MAPINFO, SNDINFO, LICENSES.md, MOD-SPEC) — serialize installs; engine runs from a clean worktree.

## Where we are

- **v1.0 shipped for a friends release:** G6 PASS (4a17a61, evidence
  `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`), tag `v1.0` at
  d530faa, GitHub release with `sovietdoom-1.0.zip` (SHA-256 `1b4731aa…`)
  on the repo, **public** since D100. CI green on 4a17a61; `main` = `origin/main`.
- **M1-M4 all PASSED** (`docs/ROADMAP.md`).
- **Nothing in flight.** No agent is working; the backlog's "Doing" is empty.

## Next steps

0. **P5 Windows one-click package published** (D101, 335d04b): `sovietdoom-1.0-windows.zip` on the v1.0 release, tested unzipped fresh. Next for P5: macOS (~70k) and Linux (~55k) packages — need the CEO's OK to download those GZDoom builds; attach the GZDoom g4.14.2 source archive (and OpenAL Soft 1.23.1, libsndfile 1.2.2, ZMusic) to the release for GPL/LGPL 'same place' compliance (download needs the CEO's OK; today the package carries links + a written offer).
1. Done 2026-10-20: the README status line, the stage 7 paper-trail fixes
   (MOD-SPEC §6.2, MAPINFO comments) and the repo made public (D100).
   v1.1 details in `docs/ICEBOX.md` (dog sounds, continue after death).
2. The CEO plays the release: sound and music by ear, the two-IWAD dialog,
   the credits at 16:9, the face ladder (PENDING §2).
3. The CEO picks the first V2 phase (P1-P6, BACKLOG "Parked").

## Untracked on disk

`work/audio/candidates/borodin_steppes/` shows as untracked (Borodin was
rejected for MAP01, D92): gitignore it or delete it; it is not part of v1.

## Rules learned

Agents never commit or stage (D6); commit with `git commit -- <paths>`;
file ownership in every brief; only the PM runs GZDoom (D26) with
`-config logs/gzdoom-tooling.ini`; the PM gates every draft before the
CEO; short lists when asking the CEO (he lost track once); PowerShell and
full paths for the CEO; send images with SendUserFile; log each task's real
token cost in the BACKLOG's Done line when it closes (today's delivery was
not logged, so its estimates cannot be checked).
