# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-20, ~16:40 (Product + pmo, stages 6 and 7, after the v1.0
sign-off). Decisions up to **D99** are in `docs/PRD.md`; open CEO items in
`docs/PENDING-CEO-DECISIONS.md`; tasks and V2 estimates in `docs/BACKLOG.md`;
the checkpoint for the CEO is
`docs/product/2026-10-20_1639_P0_v1-roadmap-checkpoint.md`.

## Where we are

- **v1.0 shipped for a friends release:** G6 PASS (4a17a61, evidence
  `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`), tag `v1.0` at
  d530faa, GitHub release with `sovietdoom-1.0.zip` (SHA-256 `1b4731aa…`)
  on the repo, **public** since D100. CI green on 4a17a61; `main` = `origin/main`.
- **M1-M4 all PASSED** (`docs/ROADMAP.md`).
- **Nothing in flight.** No agent is working; the backlog's "Doing" is empty.

## Next steps

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
