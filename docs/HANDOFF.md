# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-20, ~10:45 (pmo / Product check, stage 6). Decisions up
to **D85** are in `docs/PRD.md`; open CEO items in
`docs/PENDING-CEO-DECISIONS.md`; tasks with token estimates in
`docs/BACKLOG.md` (D69); the MVP snapshot is
`docs/product/2026-10-20_1045_P0_mvp-status.md`.

## Where we are

- **M1 PASSED** (D70): the CEO walked MAP01 -> metro -> Tankograd -> end.
- **M2 (~41 % by asset group):** 7 of 7 enemies ours; TT-33 and PPSh-41
  in hand (2 of 7 weapons); IZh-58, RPG-7, ROKS-3 and hand Katyusha
  approved from Gemini frames (D84), install N14-I queued; the ice axe's
  strike arm being redrawn (N14-AX). Pickups (D80),
  enemy shells (D81) and player effects (D82) approved: M2a-i installing
  now (uncommitted), M2b-i and M2c-i queued behind it.
- **M3:** 25 weapon sounds installed (D74); D83 approved 30 enemy sounds,
  5 beds, SDIZFIR B and the intermission music (install N9e, queued);
  alternatives: N9a's 15 with the CEO, N9m in progress (8 enemy rows,
  MAP01's new PD piece). MAP02 and MAP03 music approved and playing.
- **M4:** README (G2), licences/credits/Freedoom notice (G9), licence texts
  (N10), QA-G6-1/2 (1bcf2e0) done; left: HUD/shell art (M2e), N11, N16.

## Weapons: the method (D79, after D77-D78)

The CEO makes two images per weapon with **Google Gemini** (ready, firing;
flat magenta); they live in `work/art/reference/` (gitignored, **never
pushed**, D77). `tools/art/gemini_frames.py` turns them into the weapon's
frames (per-weapon `WEAPONS` table since dbd82e4), Gemini is credited (D79),
bare hands. Installed this way: the PPSh-41 (b5bd434). Approved (D84), install
queued: IZh-58, RPG-7, ROKS-3, hand Katyusha. The ice axe goes back for a
straight strike arm.

## In flight (2026-10-20, ~10:45)

- **M2a-i** (mod-engineer): the campaign pickups install, uncommitted in the
  working tree (`assets/sprites/pickups/`, `assets/graphics/hud/`,
  `src/zscript/sd/pickups.zs`, `keys.zs`, `ammo.zs`, LANGUAGE, LICENSES,
  MOD-SPEC, tests). M2b-i, M2c-i and N9e wait behind it (same files).
- **N9m** (sound-designer): enemy alternatives and MAP01 music candidates.
- **N14-AX** (art-director): the ice axe's straight strike arm.
- **Waiting on the CEO:** the ice axe after N14-AX, the 15 sound
  alternatives (N9a).

## Rules learned

Agents never commit or stage (D6); commit with `git commit -- <paths>`;
file ownership in every brief; only the PM runs GZDoom (D26) with
`-config logs/gzdoom-tooling.ini`; the PM gates every draft before the
CEO; short lists when asking the CEO (he lost track once); PowerShell and
full paths for the CEO; send images with SendUserFile.
