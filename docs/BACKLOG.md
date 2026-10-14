# Backlog

Living document. Owner: PM. **Agents are launched only from this list**, top
first. The CEO approves what moves into "Next". Order follows the MVP rule
(D60) and the milestones of `docs/ROADMAP.md`. Status: `todo`, `doing`,
`waiting CEO`, `done` (done items move to the bottom section once committed).

## Token estimates (D69)

Every open task carries an estimate in **k tokens**: the agent's work plus the
PM's review, the engine pass and the commit. They are rough (±50 %) and exist
so the CEO can pick what fits in the rest of a session. Rule of thumb from
2026-10-14: a design sweep or a texture batch ~200-300k; a full enemy set
~300-400k with its tests; a map version ~300-500k; an install with an engine
pass ~100-150k; a research report ~100-150k. When a task closes, its real
cost goes in the Done line (from the agent's usage report) so the estimates
get better.

## Doing (agents at work)

| # | Milestone | Task | Role | Est. k tok | From |
|---|---|---|---|---|---|
| N14-2 | M2 | Ice axe right-handed (D73) + shaft and head polish, cells C1/C3/C4 again | art-director | 100 | D73 |
| N4 | M2 | Ice axe (weapon 1 of 6): round 2 with Freedoom's gripping hand (SHTGD0) **not passed by the PM** (blobby); waits on the CEO's Fooocus references (N14) | art-director | — | D66 |

## Next (approved order, D63)

| # | Milestone | Task | Role | Est. k tok | Needs |
|---|---|---|---|---|---|
| N17 | M2 | Install the approved TT-33 held frames (SDTT/SDTF, D61) into the PK3 + engine pass; today they live only in the draft overlay | mod-engineer | 120 | — |
| G2 | M4 | Fix the generated README EN/RU (three-map campaign, GZDoom 4.14 default controls, Phase 2 WAD, hash check) from the G6 review's proposal | mod-engineer | 50 | — |
| M2a | M2 | Pickups sweep + install: health, armour, area map, backpack, yellow and red keycards (113 placed on skill 3), the hand Katyusha's pickup (draft SDHPA0), fullscreen HUD icons, our pickup lines | art-director + mod-engineer | 480 | — |
| M2b | M2 | Enemy shells: the Doughboy's BAL2, the Panzermensch's BAL7 | art-director + mod-engineer | 150 | — |
| M2c | M2? | Player projectiles and hit effects (MISL, PLSS/PLSE, PUFF, BLUD shape, TFOG), barrels and lamp | art-director | 350-400 | CEO: in M2 or not |
| M2d | M2 | Practice range retexture (STARTAN2, FLOOR4_8, CEIL3_5) | level-designer | 40 | — |
| M2e | M2/M4? | Shell and HUD: STBAR, the face STF*, fonts, stats screen graphics, HELP/CREDIT, DEHACKED pickup and quit lines, intermission music (D_DM2INT plays today) | art-director + mod-engineer | 430-650 | CEO: M2 or M4 |
| N14 | M2 | Weapons in hand from the CEO's Fooocus references, one at a time, verified each (ice axe first, then 5 more) | art-director | 250 per weapon, ~1 500 all | CEO's images |
| N7b | M1+ | Metro v2 (textures aligned), optional: the CEO found M1 "perfecto" | level-designer | 350 | CEO decides if wanted |
| N7c | M1+ | Tankograd v2, optional (as N7b) | level-designer | 400 | CEO decides if wanted |
| N9 | M3 | Install the effects the CEO approves; wire SNDINFO; **loudness pass** (drafts are 6-18 dB quieter than the Freedoom sounds they replace; bass-heavy clips); engine pass | sound-designer + mod-engineer | 200 | CEO's listening |
| N8 | M3 | Music per map: swap any piece the CEO rejects for another PD work or a licence-clean MIDI (D59) | sound-designer | 80 per swap | CEO's listening |
| N15 | tooling | Evaluate Ultimate Doom Builder (D69, "me interesa"): install, open our UDMF maps, does a round trip keep `tools/sdbuild` working, report | mod-engineer + level-designer | 150 | CEO's OK to download UDB |
| N11 | M4 | Russian in-game text review, once, at the end of the delivery | translator-ru | 250 | M1-M3 done (D60) |
| N16 | M4 | Ship v1: G6 gate, QA sign-off, README EN/RU, tag v1.0 | qa-engineer + PM | 250 | everything above |

MVP left, roughly: **~4 500k tokens** after the M2 audit (the six weapons ~1 500k, pickups/shells ~630k, HUD/shell 430-650k if in the MVP).

## Waiting for the CEO

See `docs/PENDING-CEO-DECISIONS.md`: walk the campaign, the Doughboy flag,
the Fooocus hand images, sounds and music to hear.

## Parked (after the MVP, D60)

| Task | Phase | Est. k tok |
|---|---|---|
| The TT-33's colour and grey detail (D63, nice to have) | P1 | 100 |
| G3 hostile pass and hand-played runs, per map | P1 | 150 per map |
| Balance tuning by playtest (BALANCE §5) | P1 | 300 |
| Weapon reloads (`docs/ICEBOX.md`) | P1 | 400 |
| Voices: process the CEO's takes or the local generator's output (D36, after R1) | P2 | 300 |
| The Russian docs mirror (phase close, D34) | P3 | 400 |
| **Mine Freedoom's 68 maps (BSD) to calibrate our map constants** (`docs/product/2026-10-13_0944_F3_ml-level-generation.md` §6), D69: only when the full game starts | P4 | 500 |
| **The full game: 15-20 levels** (D69), a roadmap of its own when the MVP ships | P4 | ~400 per map |

## Done (recent, newest first)

**Bestiary complete (M2):** N12c, the General installed (413ba73), engine pass `docs/qa/evidence/2026-10-15_0010_F5_general-installed.md`. **Real 259k** (est. 200k).

A1: M2 Freedoom audit `docs/qa/2026-10-14_2357_M2-freedoom-audit.md`: campaign textures 100 % ours; blocks M2: TT-33 install, 6 weapons, Katyusha pickup, two enemy shells, 113 health/armour/key pickups; all sounds still Freedoom's. **Real 255k** (est. 80k).

A2: Fooocus prompt sheet for the 5 weapons `docs/product/2026-10-14_2356_M2_fooocus-prompts-armas.md` (Spanish, prompts in English; Method B = our/Freedoom frames as input; 6 required images); inputs in `work/art/reference/doom_inputs/`. **Real 213k** (est. 20k: the Method B inputs were added mid-task).

A3: listening sheet `docs/art/previews/2026-10-14_2355_M3_listening-sheet.html` (80 rows + 3 optional; music rendered with GZDoom's own zmusic, the first audible renders of four pieces). **Real 232k** (est. 60k).

A4: G6 readiness review `docs/qa/2026-10-14_2356_G6-readiness.md`: the release tool PASS, G6 blocked by M2/M3, the README, N11, sign-off and tag; gaps G1-G17 (~350k release-only). **Real 184k** (est. 80k).

N12b: the General CD full set drafted (81 + 5 lumps), waiting for the CEO; **real ~165k** (est. 500k); N12 all steps ~500k. N14-1: the ice axe from reference 1, three cells to the CEO; **real 327k** (est. 250k).

N13: the Doughboy installed (bcb7de2), engine pass `docs/qa/evidence/2026-10-14_2242_F5_doughboy-installed.md`; **real cost 250k** (est. 120k: the docs and tests mirror of 0bd65d9 is the bulk). N12b-1: the General CD turnaround (9939d6a), waiting for the CEO; **~50k** (est. 100k). Bestiary: 7 of 7 enemies drawn, 6 installed.

**M1 PASSED (D70):** the CEO walked the campaign. N12: the General's sweep, five cells A-E, `docs/art/previews/2026-10-14_2208_F5_general-sweep.html`, PM recommends C. **Real cost 282k** (est. 250k).

N10: the full GPL-3.0 and CC BY-NC-SA 4.0 texts ship in the v1 zip byte for byte, hashes pinned and tested; G6 row 2 PASS. **Real cost 128k** (est. 80k).

R1: local voice generation study, `docs/product/2026-10-14_2156_P2_local-voice-generation.md` (Spanish, for the CEO): Chatterbox Multilingual (MIT) via Chatterbox-TTS-Server on `Z:`, the CEO's own voice as reference only. **Real cost 147k** (est. 120k).

N2 + v1.1: tankograd-critical route; Tankograd v1.1 (D68). **All three campaign routes PASS in engine on 16427a7** (MAP01 -> MAP02 -> MAP03 -> end). D67: Panzermensch and Schwer installed.

N7: Tankograd v1 (textures, the red lock cleared, 25/38/52 with the General, ammo to G3-8), walked in engine (`docs/qa/evidence/2026-10-14_2131_F3_tankograd-v1-walk.png`, music D_SDGATE playing). N5: the heavies' full sets, waiting for the CEO.

N6b/N6c: SDCHAN1 (masked) and SDSLOG1 installed, the factory set complete (21 of 21); ANIMDEFS for the molten metal and the portal. N8: a PD piece per map in draft.

2026-10-14 night: N1 map renumbering (MAP01 Zarya-7 -> MAP02 metro -> MAP03 Tankograd, RANGE outside; routes PASS in engine for MAP01, the metro and RANGE); N3 pickups installed; N6 Tankograd textures 19/21 installed; B4 fast verify ~13 s; main green again (eea9992).

2026-10-14 evening: metro v1 (signposted pass, populated, route PASS in engine), factory v0, the route runner for the metro and MAPINFO-driven exits, the TT-33 in Freedoom-based hands, the pickups sweep, the blue pass actor, the campaign MAP01 -> metro, the hands study, the Doughboy/Panzermensch sweep.

The 2026-10-13/14 work is in `git log` and `docs/PRD.md` D40-D62: the
campaign MAP01 -> metro, the blue pass, the four installed enemies, the
Stalin poster, the metro set and mosaic v2, the radio, the credits, the
Russian pause sign, the release tool, the hands study.
