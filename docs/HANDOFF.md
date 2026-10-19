# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-15, ~01:00, the CEO went to sleep. Decisions up to **D77**
are in `docs/PRD.md`; open CEO items in `docs/PENDING-CEO-DECISIONS.md`;
tasks with token estimates in `docs/BACKLOG.md` (D69).

## Where we are

- **M1 PASSED** (D70): the CEO walked MAP01 -> metro -> Tankograd -> end.
- **M2:** all 7 enemy classes draw our sprites (Doughboy D70, General D73,
  engine passes in `docs/qa/evidence/2026-10-15_0010_*`); the TT-33 hands
  are installed (N17, `2026-10-15_0037_*`): 1 of 7 weapons. Open: the 6
  other weapons (N14), health/armour/key pickups, enemy shells, player
  effects (M2a-M2d, audit `docs/qa/2026-10-14_2357_M2-freedoom-audit.md`).
- **M3:** 25 weapon sounds approved (D74) and being installed (N9w); 15
  alternatives for the other 5 wait for the CEO
  (`docs/art/previews/2026-10-15_0033_M3_listening-alternatives.html`);
  50 rows of the big listening sheet unjudged.
- **M4:** README (G2), licences/credits and Freedoom's BSD notice (G9) done;
  G6 review `docs/qa/2026-10-14_2356_G6-readiness.md`.

## Weapons: the new method (D77)

The CEO makes references with **Google Gemini**; they live in
`work/art/reference/gemini_*` (gitignored, **never pushed**). We draw our
own frames from them (`tools/art/hand_ref.py`), **bare hands**, one weapon
at a time, **silhouettes first** (cheapest review), then colour, then the
animation. PPSh-41 is first. The ice axe (hand C3, shaft x1.7, head x1.8,
straight shaft) and the IZh wait for bare-hand references. Gemini is inspiration only, never traced and never credited (D78).

## In flight at handoff (2026-10-19 night)

Nothing running. Waiting on the CEO: the PPSh-41 Gemini-frames test (two
images to save as files), the sweeps for enemy shells, player effects and
campaign pickups (installs M2a-i, M2b-i, M2c-i queued), the 15 sound
alternatives. The range is retextured and passes its route.

## Rules learned

Agents never commit or stage (D6); commit with `git commit -- <paths>`;
file ownership in every brief; only the PM runs GZDoom (D26) with
`-config logs/gzdoom-tooling.ini`; the PM gates every draft before the
CEO; short lists when asking the CEO (he lost track once); PowerShell and
full paths for the CEO; send images with SendUserFile.
