# Pending CEO decisions

Updated: 2026-10-20 ~10:55, after D85 (pipeline stage 6, D64). Ordered by
how much each item unblocks. What closed since the previous update is listed
at the end so nothing is lost. Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`
(synced at phase close, D34).

## 1. Waiting for your eyes

Previews are sent to you as files; the paths are under `docs/art/previews/`.

| What | Preview | Asks [PM's recommendation] |
|---|---|---|
| **The ice axe's strike frame**, redrawn so the arm leaves the view straight (D84, N14-AX in progress) | coming | OK / NO; the last weapon of M2 (the other four install, N14-I) |

## 2. Waiting for your ears

| What | Page | Asks |
|---|---|---|
| Sound alternatives for the 5 weapon rows of D74 that were NO or ? (SDTTPKP, SDIZRLD, SDRKFIR, SDAXPKP, SDIZPKP); they keep Freedoom's sounds until then | `2026-10-15_0033_M3_listening-alternatives.html` (15 alternatives) | OK/NO per alternative, "Copiar resultado" |
| Coming (N9m, in progress): alternatives for the 8 enemy rows rejected in D83, MAP01 music trimmed to its melodic part (`D_SDM01T`) for the range, and PD candidates for MAP01 | a new listening page | you will get it when it is ready |

**Installed (D74, 70358e0):** the 25 approved weapon sounds. When you play,
three questions stay open, none blocks: are the TT-33/PPSh shots strong
enough next to the rifleman's? Is the axe hit (`SDAXHIT`, bass-heavy)
audible on laptop speakers? Keep the three reload sounds packed for a future
magazine mechanic, or drop them?

## 3. Your voice takes for the enemies (D36)

The sound-designer is writing `docs/sound/VOICE-SCRIPT.md`: every line in
German or English, with instructions for recording or for AI generation.
Nothing to decide. **Postponed by the CEO on 2026-10-13** ("lo dejamos
pending"): the enemies keep Freedoom's voices until the takes arrive, and
nothing else waits on them. D84: the local generator's default voice is not
the soldier the script needs; **D85: Freedoom's voices until the MVP ships,
then Chatterbox cloned from your own voice** (P2). Nothing open here.

## 4. Later, at the end of the MVP

- **M2e (HUD and shell art):** its sweeps will come to you for an OK, as the
  pickups did.
- **v1.0:** after the sign-off (N16), "publish or not" and the tag (G6
  readiness G13-G14). Optional calls there: a GAMEINFO IWAD hint (G15),
  jump/crouch allowed (G17).
- Whether to build metro v2 / Tankograd v2 (N7b/N7c, optional) and the UDB
  evaluation download (N15).

## Closed since the previous update (for the record)

D85 (2026-10-20): voices Freedoom's until the MVP, then Chatterbox from the CEO's voice. D84 (2026-10-20): four Gemini weapons approved (IZh-58, RPG-7, ROKS-3, hand Katyusha); the ice axe's strike arm goes back. D83 (2026-10-20): the listening sheet judged 80 of 80 (30 enemy sounds and 5 beds OK; 8 rows NO; title, metro, Tankograd, intermission and radio music OK; `D_SDAMUR` NO; MAP01's music moves off MAP01 and is trimmed; SDIZFIR take B). This also closes the Glinka question (`D_SDGATE` stays in the anthem slot). D82: player effects, option A of each. D81: enemy shells, option A for both. D80: campaign pickups (recommended except SDAG C, SDAH C, SDBP B); the red cross question closed with the PM's default (white cross on green). D79: the Gemini-frames method adopted and Gemini credited (supersedes D78); the CEO's images for the five weapons arrived. D76-D77 (2026-10-15): the ice axe's size; Gemini references local only.

D75 (2026-10-15): ice axe hand C3; Freedoom's notice downloaded; AI line in the credits; Impact accepted; Russian docs after the MVP; M2 includes the player's effects, the HUD goes to M4. D74: the first 30 weapon sounds judged.

D70 (2026-10-14): M1 passed, the CEO walked the campaign; the Doughboy with the bigger flag approved. D69 (2026-10-14): the licence texts may be downloaded (done by the PM); the Lenin slogan closes as shipped («ЛЕНИН ЖИВ»); mining Freedoom's maps waits for the full-game phase; Ultimate Doom Builder is of interest (backlog N15). D44-D68 (2026-10-14): the Stalin poster 4C «СЛАВА СТАЛИНУ!» in the metro's secret shelter; the hound, rifleman, Stormtrooper, Legion, Panzermensch and Schwer installed; palette v2 for the mosaic and marble; Freedoom-based hands (D61) and the TT-33 in them; the map renumbering (D62); roadmap and backlog (D63); pipeline stage 6 (D64); the 21 Tankograd textures (D66); Tankograd's secret, damage and reward (D68). Details in `docs/PRD.md`.

The ice axe replaces the shovel (D40). MAP02 ships as a practice range (D41; the lump `RANGE` since D62). Every music recommendation of SOUNDTRACK §8, accepted (D43). Title screen and intermission (D18). Switch texture: all four variants
approved and installed (D25). Music model and La Internacional (D23).
Alphabet C (D24). Difficulty ladder (D20; the "Pyatiletka in one night" swap
stays an option, not a pending item). Language switch and Cyrillic
letterforms, level 2 (D21, D22). The engine gate (D26). The Windows PC as the
working machine (D27); the Mac's gitignored `work/` reached the PC the same
afternoon, so D27's "stays on the Mac until the CEO copies it" is now
history. Bug B2 (`SDPOSTR2`) resolved 2026-10-12. The font serif fix and the batch 3
props, columns C and D (D29). How MAP01 is judged: by walking it (D28). MAP01 v2 passed its gate and the
text menu is approved (D32); MAP01's scale, densify (D33). The bestiary's seven questions (D35). The German letters, installed for trial (D37). `SDCONC2` and `SDSTAR1` v5, approved
in the map (D30); the hangar wainscot, dropped with them. Bug B3 (art identity
test without `work/`) resolved 2026-10-13. T16, the switch `ANIMDEFS`,
written and seen to flip in engine 2026-10-13.
