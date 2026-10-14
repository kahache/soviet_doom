# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-14, near the usage limit. Decisions up to **D54** are in
`docs/PRD.md`; open CEO items in `docs/PENDING-CEO-DECISIONS.md`.

## In flight when the session stopped (uncommitted work may be on disk)

Check `git status` first. Each item below was an agent's task; if its files
are half-done, verify with the listed tests before committing, or relaunch.

| Task | Files | Done when |
|---|---|---|
| Reich rifleman: lots of **dark red** blood, corpse lying flat (D48, D49) | `tools/art/gen_rig.py`, `tests/test_gen_rig.py`, preview `docs/art/previews/2026-10-14_1141_F5_reich-rifleman-blood.html` | A-G byte-identical; corpse-on-floor test; CEO approves |
| Stormtrooper death redone flat (D53) | `tools/art/gen_storm.py`, `tests/test_gen_storm.py`, `work/art/enemies/storm/full_E/` | M0 and U0 flat, A-H byte-identical |
| Hound, German shepherd cell A, full set (D50) | `tools/art/gen_hound.py`, `tests/test_gen_hound.py`, `work/art/enemies/hound_gsd/full_A/` | mirrored rotations, dark red blood, flat corpse |
| 2D hands on all seven weapons, Katyusha B (D51, D52) | `tools/art/gen_hands_2d.py`, `tools/art/gen_weapon.py`, `work/art/weapons_2d/` | numbered preview; then draft overlay for the CEO to play |
| Legion C installed in the game (D54) | `assets/sprites/legion/`, `src/zscript/monsters/legion_trooper.zs` (SPOS -> SDLT) | tics pinned by a test; PM engine pass |
| Anthem slot: a public-domain replacement for Glinka (D54) | `tools/audio/gen_music.py`, `docs/sound/SOUNDTRACK.md` card 5, `MUSIC-RIGHTS.md` | one PD score downloaded with provenance, draft sequenced |
| Stalin poster, like Lenin's (CEO request 2026-10-14; download of one PD photo **authorised by the CEO**) | `tools/art/gen_stalin.py`, `docs/product/*stalin-poster-sourcing.md`, `work/art/reference/` | 15-cell sweep preview for the CEO |

## Next for the PM

- Engine passes owed: the Legion in game; the 2D hands via
  `tools/make_draft_overlay.py`; the blood colour on hit (not yet seen).
- G3 still needs the CEO's hand-played runs on skills 2 and 4 and G3-9.
- Rules learned: agents never commit (D6); give file ownership and ADR
  numbers up front; send previews to the CEO with SendUserFile and full
  paths (relative links did not open); PowerShell commands for the CEO,
  not Git Bash.
