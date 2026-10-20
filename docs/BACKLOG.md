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

Checked against the repo on 2026-10-20 ~10:45 (pmo / Product, stage 6).

| # | Milestone | Task | Role | Est. k tok | From |
|---|---|---|---|---|---|
| M2a-i | M2 | (doing, D80; uncommitted in the working tree: 11 pickup sprites, `pickups.zs`, HUD key icons `STKEYS0-2`, LANGUAGE lines) Install the campaign pickups (11 items incl. the hand Katyusha's `SDHP`, keys SD_YellowPass/SD_RedPass via Species, HUD key icons, pickup lines EN/RU) | mod-engineer | 200 (installs have run ~1.7x their estimate: plan 300) | CEO OK on `2026-10-19_2212_F5_campaign-pickups.html` |
| N9m | M3 | (doing) Enemy sound alternatives (8), MAP01 music trimmed (`D_SDM01T`, for the range) and PD candidates for MAP01, listening page | sound-designer | 200 | D83 |
| M2b-i | M2 | (queued behind M2a-i, same files; approved D81) Install the enemy shells SDDL/SDPL (today `BAL2`/`BAL7`) | mod-engineer | 80 (plan 130) | CEO OK on `2026-10-19_2200_F5_enemy-shells.html` |
| M2e-i | M4 | (queued) Install status bar A (EN/RU by code) + the 42 Gemini faces (D89, D90) + digits (N2 recommended, CEO to confirm) + engine pass | mod-engineer | 150 | D90 |
| M2c-i | M2 | (queued behind M2a-i and M2b-i; approved D82) Install the player effects (SDPG, SDKR, SDPX, SDFJ/SDFX, PUFF, BLUD, TFOG/IFOG, BAR1/BEXP, COLU; today `MISL`, `PLSS`/`PLSE` and Freedoom's) | mod-engineer | 150 (plan 250) | CEO OK on `2026-10-19_2208_F4_player-effects.html` |
| N9e | M3 | (queued behind M2c-i, same files) Install the 30 enemy sounds and 5 beds approved in D83 + SDIZFIR take B, loudness pass, SNDINFO; `D_SDTITL` as intermission music (today Freedoom's `D_DM2INT`) | sound-designer + mod-engineer | 250 (N9w, 25 sounds, cost 400: plan 400) | D83 |
| N14-I | M2 | (queued behind M2a-i, same files) Install the IZh-58, RPG-7, ROKS-3 and Katyusha Gemini frames (D84) + engine pass | mod-engineer | 120 (PPSh-41 install alone cost 150 + 40: plan 250) | D84 |
| N14-AX | M2 | Ice axe strike frame: the arm leaves straight, not curved (D84) | art-director | 30, then ~80 to install after the CEO's OK (plan 120) | doing; the CEO's OK (D84) |

## Next (approved order, D63)

| # | Milestone | Task | Role | Est. k tok | Needs |
|---|---|---|---|---|---|
| M2e | M4 (D75) | Shell and HUD: STBAR, the face STF*, fonts, stats screen graphics, HELP/CREDIT, DEHACKED pickup and quit lines (the intermission music moved to N9e, D83) | art-director + mod-engineer | 430-650 | the CEO's OK on the sweeps |
| N9 | M3 | Install what the CEO approves from the alternatives: N9a's 15 (for SDTTPKP, SDIZRLD, SDRKFIR, SDAXPKP, SDIZPKP; these five keep Freedoom's today) and N9m's 8 enemy rows; MAP01's new PD piece and the range's music (D83). N9w installed the 25 of D74 (70358e0) | sound-designer + mod-engineer | 150 | CEO's listening (N9a page, N9m page) |
| N8 | M3 | Music per map: any further swap the CEO asks for (D59); MAP01 and RANGE are in N9m/N9 | sound-designer | 80 per swap | CEO's listening |
| N7b | M1+ | Metro v2 (textures aligned), optional: the CEO found M1 "perfecto" | level-designer | 350 | CEO decides if wanted |
| N7c | M1+ | Tankograd v2, optional (as N7b) | level-designer | 400 | CEO decides if wanted |
| N15 | tooling | Evaluate Ultimate Doom Builder (D69, "me interesa"): install, open our UDMF maps, does a round trip keep `tools/sdbuild` working, report | mod-engineer + level-designer | 150 | CEO's OK to download UDB |
| N11 | M4 | Russian in-game text review, once, at the end of the delivery (after M2a-i and M2e add their lines) | translator-ru | 250 (plan 300) | M1-M3 done (D60) |
| N16 | M4 | Ship v1: G6 gate, QA sign-off, tag v1.0; with the G6-readiness leftovers G7 (in-game credits refresh for the new assets and sounds), G10 (RELEASE.md §2 refresh: rows 1 and 6 per D75), G16 (repo README status line); optional G15, G17 | qa-engineer + PM + mod-engineer | 250 (plan 350) | everything above; the CEO's "publish or not" |

N14 (weapons from Fooocus references, ~1 500k) and N4 (the ice axe round 2) are
superseded by D79: the five weapons were drafted from Gemini frames (N14-G,
dbd82e4); D84 approved four (N14-I) and sent the ice axe back (N14-AX).

**MVP left, recomputed 2026-10-20 with the real costs logged so far: ~3 050k
tokens (range 2 600-3 800k).** Real costs ran 1.4x the estimates overall
(21 closed tasks: 4 207k real against 3 005k estimated) and 1.7x on installs
(N17, N12c, N13, N9w), so the plan numbers above are used: M2 ~1 050k (M2a-i
300, M2b-i 130, M2c-i 250, N14-I 250, N14-AX 120), M3 ~750k (N9m 200, N9e
400, N9 150), M4 ~1 250k (M2e ~600, N11 300, N16 350). Not counted: N7b/N7c,
N15, N8 extra swaps. Snapshot: `docs/product/2026-10-20_1045_P0_mvp-status.md`.

## Waiting for the CEO

See `docs/PENDING-CEO-DECISIONS.md`: the ice axe's straight strike arm
(N14-AX), the 15 sound alternatives (N9a), then N9m's listening page.

## Parked (after the MVP, D60)

| Task | Phase | Est. k tok |
|---|---|---|
| The TT-33's colour and grey detail (D63, nice to have) | P1 | 100 |
| G3 hostile pass and hand-played runs, per map | P1 | 150 per map |
| Balance tuning by playtest (BALANCE §5) | P1 | 300 |
| Weapon reloads (`docs/ICEBOX.md`) | P1 | 400 |
| Voices: Chatterbox cloned from the CEO's own voice (D85), the script in EN/DE, then processing | P2 | 250 |
| The Russian docs mirror (phase close, D34) | P3 | 400 |
| **Mine Freedoom's 68 maps (BSD) to calibrate our map constants** (`docs/product/2026-10-13_0944_F3_ml-level-generation.md` §6), D69: only when the full game starts | P4 | 500 |
| **The full game: 15-20 levels** (D69), a roadmap of its own when the MVP ships | P4 | ~400 per map |

## Done (recent, newest first)

**2026-10-20 morning:** the CEO's verdicts D80-D83 (pickups, shells, effects, the listening sheet 80 of 80); the five other weapons drafted from the CEO's Gemini frames (dbd82e4, preview dc49b40), cost not logged; D84 approved four of them.

G9: player LICENSE.md and CREDITS.txt without repo paths, Freedoom's BSD-3 notice in the zip (hash pinned), the AI line in the credits, in-game credits corrected (465a83e); real cost not logged (est. 40k).

**2026-10-20 night:** D79, the Gemini-frames method: the PPSh-41 installed (b5bd434, sleeve fix 362df5a), **2 of 7 weapons ours**; test ~48k, install ~150k, sleeve ~40k. QA-G6-1/2 fixed (1bcf2e0), ~66k. Engine evidence `docs/qa/evidence/2026-10-20_0317_*`. Guide for the next weapons `docs/product/2026-10-20_0030_M2_gemini-armas.md`.

M2a: campaign pickups sweep + sets for 11 items (gen_items.py); **real 320k** (est. 480k incl. install).

M2d: range retextured (d8062e4), route PASS; **real 160k** (est. 40k). M2b: enemy shells sweep + sets (0c22bf0); **real 175k** (est. 150k). M2c: player effects sweep + sets (ab03aee); **real 260k** (est. 350-400k). PPSh hand-drawn silhouettes stopped after two rounds (method change).

N9w: 25 weapon sounds installed (70358e0), load pass clean (`docs/qa/evidence/2026-10-15_0117_M3_weapon-sounds-load.md`), listening pass owed; 13 of 25 are 1-6 dB under target (no saturation, per brief). **Real ~400k** (est. 250k). N14-P: PPSh-41 silhouettes; **real 26k**.

N17: the TT-33 hands installed (d2be8ca), engine pass `docs/qa/evidence/2026-10-15_0037_F4_tt33-installed.md`: **1 of 7 weapons ours in the PK3**. **Real 279k** (est. 120k). N9a: 15 sound alternatives, page `docs/art/previews/2026-10-15_0033_M3_listening-alternatives.html`; **real 275k** (est. 120k). N14-3: ice axe silhouettes; **real 10k** (est. 40k).

G2: README EN/RU rewritten (666b85d), 12 tests. **Real 156k** (est. 50k).

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
