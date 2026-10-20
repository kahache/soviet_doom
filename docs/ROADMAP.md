# Roadmap

Living document. Owner: PM. Russian mirror: `docs/ru/ROADMAP.md` (synced at
phase close, D34). **Roadmap v2, approved by the CEO on 2026-10-14 (D63).** The task list lives in
`docs/BACKLOG.md`; agents are launched only from it.

## The rule (D60, "instrucción importantísima")

**MVP first, gameplay later.** A complete, playable game ships first; balance,
hostile passes and other gameplay polish come after the MVP.

## What the MVP is (v1.0)

A player installs one PK3 next to Freedoom, starts a new game and plays the
whole episode in English or Russian:

| Area | MVP means | Today |
|---|---|---|
| Campaign | **3 maps linked**: MAP01 Zarya-7, MAP02 metro-bunker, MAP03 factory (D62 numbering), each finishable, populated, signposted, textured with our art, with its music | **done**: MAP01 v3, metro v1, Tankograd v1.1 linked, every route PASS in engine, walked by the CEO (M1, D70) |
| Arsenal | **7 weapons with our own first-person art** (Freedoom-based hands, D61; Gemini frames since D79) and our pickups | first person: **TT-33 and PPSh-41 installed (2 of 7)**; IZh-58, RPG-7, ROKS-3 and hand Katyusha approved from the CEO's Gemini frames (D84), install queued (N14-I); the ice axe's strike arm being redrawn (N14-AX, D84); pickups: 6 of 7 ours, the hand Katyusha's (`SDHP`) installing with M2a-i (in progress) |
| Bestiary | **7 enemies with our own sprites** | **7 of 7 installed** (D73); shells: the General's and the Stormtrooper's bolt ours, the Doughboy's and Panzermensch's approved (D81), install queued (M2b-i) |
| Sound | weapon and enemy effects approved by the CEO (voices optional) | **25 weapon sounds installed** (D74); SDIZFIR (take B), 30 enemy sounds and 5 beds approved (D83), install queued (N9e); 5 weapon and 8 enemy rows rejected or undecided, alternatives with the CEO (N9a) or in progress (N9m) |
| Music | title + one public-domain piece per map (no composing, D59) | approved and playing: title `D_SDINTL`, MAP02 `D_SDFUNR`, MAP03 `D_SDGATE` (D83). Open: MAP01 still plays `D_SDM01`, which D83 moves off MAP01 (a new PD piece, N9m); the intermission still plays Freedoom's `D_DM2INT` (`D_SDTITL` approved, N9e); RANGE plays `D_SDAMUR` (NO, D83) |
| Shell | menus, title, pause, credits, practice range; the status bar, face, stats screen and help screens (M4, D75) | menus, title, pause, credits, range **done**; status bar, face, stats screen, help screens still Freedoom's (backlog M2e) |
| Text | every in-game string in EN and RU, the Russian reviewed once at the end | bilingual (pickup lines EN/RU arriving with M2a-i); review owed (N11) |
| Release | the v1 package (G6) | `tools/release.py` ready; full licence texts (N10), Freedoom's BSD notice, player LICENSE/CREDITS and the AI line (G9), README EN/RU (G2), QA-G6-1/2 fixed (1bcf2e0); left: N11, sign-off, tag (`docs/qa/2026-10-14_2356_G6-readiness.md`) |

## Milestones to the MVP

| Milestone | Goal | Gate (measurable) | Status |
|---|---|---|---|
| F0-F2 | Pipeline, lore, art direction | G0, G1, G2 | **PASSED** (`docs/qa/GATE-REVIEWS.md`) |
| **M1** | **Campaign playable end to end** | the 3 maps run from New Game to the end text with no `idclip`, zero log errors, scripted route PASS on each (`tools/route.py`); the CEO walks it | **PASSED 2026-10-14 (D70):** every route PASS in engine with zero log errors, and the CEO walked it from New Game ("se puede jugar y perfecto") |
| **M2** | **Our art everywhere the player looks** | no Freedoom sprite left in first person, on enemies or on pickups; factory textures approved; plus the player's projectiles, puffs, blood, teleport fog, barrels and lamp (D75) | **19 of 46 asset groups ours (~41 %, 2026-10-20):** enemies 7/7; enemy projectiles 2/4 (SDDL/SDPL approved D81, queued M2b-i); first-person weapons 2/7 (four approved D84, queued N14-I; the ice axe redrawn, N14-AX); weapon pickups 6/7 and health/armour/map/backpack/keys 0/10 (approved D80, M2a-i in progress); player effects 0/9 (approved D82, queued M2c-i); Tankograd textures 21/21 and the range retextured (d8062e4). Every remaining group but the ice axe is approved; none waits on a new design |
| **M3** | **Sound and music** | CEO-approved effects installed; one PD piece per map | **25 of 61 approved effects installed** (the D74 weapon set); 36 approved in D83 queued (N9e); music: 2 of 3 maps play an approved PD piece (MAP02, MAP03), MAP01's replacement in progress (N9m) |
| **M4** | **Ship v1** (was F6) | G6: licence file with full texts, credits, README EN/RU, the Russian text reviewed, QA sign-off, tag v1.0; the HUD and shell art moves here (D75) | licence texts, Freedoom notice, LICENSE/CREDITS, README EN/RU and QA-G6-1/2 **done** (N10, G9, G2, 1bcf2e0); open: HUD/shell art (M2e), N11, the sign-off and tag (N16), RELEASE.md §2 refresh (G6 readiness G10) |

## After the MVP (gameplay, D60)

| Phase | Goal | Gate |
|---|---|---|
| P1 | Gameplay pass | G3's hostile pass and hand-played runs on skills 2 and 4 for every map; balance by playtest (BALANCE §5); the icebox's reloads if wanted |
| P2 | Voices and polish | the CEO's voice takes (D36); practice-range extras |
| P3 | Russian docs | the full `docs/ru/` mirror (D34) |
| P4 | **The full game: 15-20 levels** (D69) | its own roadmap when v1 ships; starts by mining Freedoom's 68 maps (BSD) to calibrate our map constants; Ultimate Doom Builder if N15 says yes |

The old phases F3 (MAP01), F4 (arsenal) and F5 (bestiary) fold into M1-M3;
their gates G3-G5 stay as the per-map and per-asset checks inside them.

Rules: gates are defined before the work starts; the first measurement is
honest and strict; a gate may be reframed only by a new D-decision of the CEO.
