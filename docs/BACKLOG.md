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

Checked against the repo on 2026-10-20 ~16:40 (Product, stage 6, after the
v1.0 sign-off 4a17a61). **Nothing in flight.** Every MVP task closed; see
Done.

## Next (approved order, D63)

**Empty for v1: the MVP shipped** (tag `v1.0` at d530faa, G6 PASS). The one
v1 step left is the PM's, not an agent's:

| # | Milestone | Task | Role | Est. k tok | Needs |
|---|---|---|---|---|---|

What the CEO chooses next comes from "Parked" below, phase by phase.

## Waiting for the CEO

See `docs/PENDING-CEO-DECISIONS.md`: his own
play-through of the release, and the order of the V2 phases.

## Parked (after the MVP, D60): V2 phases P1-P6

Estimates are raw (±50 %); real costs have run 1.4x overall and 1.7x on
installs (see Done), so plan for the higher number.

| Task | Phase | Est. k tok |
|---|---|---|
| G3 hostile pass and hand-played runs, per map, skills 2 and 4 | P1 | 150 per map |
| Balance tuning by playtest (BALANCE §5) | P1 | 300 |
| Weapon reloads (`docs/ICEBOX.md`); decides whether the three packed reload sounds stay | P1 | 400 |
| The TT-33's colour and grey detail (D63, nice to have) | P1 | 100 |
| G15: a GAMEINFO `IWAD` hint so drag-and-drop picks Phase 2 (two-IWAD behaviour NOT VERIFIED) | P1 | 25 |
| G17: jump/crouch allowed or not (a gameplay call for the CEO) | P1 | 20 |
| The CEO's three sound questions of D74 (TT-33/PPSh shot strength, the axe hit on laptops, the reloads), answered by playing | P1 | 0-80 |
| Voices: the 4 enemy voices still Freedoom's (rifleman pain, trooper death, General pain and death; D91/D96 need a shouted reference) | P2 | 150 |
| The 8 packed beds mixed under their voices (`sd/bed/`, MOD-SPEC §6.2), or dropped | P2 | 80 |
| Polish found at the sign-off: the face's full damage ladder by eye, the credits screen at 16:9, the IZh pickup sound (Freedoom's, D94) | P2 | 60 |
| Practice-range extras | P2 | 100 |
| The Russian docs mirror (`docs/ru/`, D34, D75) | P3 | 400 |
| **The full game: 15-20 levels** (D69), a roadmap of its own | P4 | ~400 per map |
| Mine Freedoom's 68 maps (BSD) to calibrate our map constants (`docs/product/2026-10-13_0944_F3_ml-level-generation.md` §6) | P4 | 500 |
| More weapons and more enemies (Gemini frames, D79); the seven enemies v2 from Gemini (`docs/ICEBOX.md`) | P4 | 300 per weapon set; enemies v2 to be measured on one enemy first |
| N15: evaluate Ultimate Doom Builder (D69, needs the CEO's OK to download) | P4 | 150 |
| N7b / N7c: metro v2, Tankograd v2 (optional) | P4 | 350 / 400 |
| Portable downloads per OS, GZDoom + Freedoom + our PK3 (D93) | P5 | 300 (NOT measured; no study yet) |
| Catalan as the third game language (D97), reviewed once like N11 | P6 | 350 (NOT measured) |
| Orchestrated music (D99): a licence-clean orchestral soundfont, then MusicGen-Melody; the CEO's Pro Tools as baseline | V2, not phased | 150 for the evaluation |

N14 (weapons from Fooocus references) and N4 (the ice axe round 2) were
superseded by D79. N8 (further music swaps) has no request open.

## Done (recent, newest first)

**2026-10-20, ~10:45 to 16:35: the rest of the MVP, v1.0 shipped.** At
10:45 the plan for what was left was ~3 050k tokens (range 2 600-3 800k,
`docs/product/2026-10-20_1045_P0_mvp-status.md`); all of it closed the same
day. **Real costs were not logged per task for this delivery** (no agent
usage report reached the repo), so its estimate-against-real cannot be
measured here.

| # | What | Commit | Est. k tok (plan) | Real |
|---|---|---|---|---|
| M2a-i | Campaign pickups installed (D80), engine pass | e84c56c, add161f | 200 (300) | not logged |
| N9m | Enemy sound alternatives, MAP01 trimmed, PD candidates (D86) | 517a1e5, 4c7e29e | 200 | not logged |
| N14-AX | Ice axe swing as one rigid piece (D86, D88) | a3a2812, c04e706 | 30 (120 with install) | not logged |
| N14-I + M2b-i | IZh-58, RPG-7, ROKS-3, hand Katyusha, ice axe in hand; `SDHP`; shells SDDL/SDPL (D81, D84, D88) | c68ad84, ce90179 | 120 + 80 (250 + 130) | not logged |
| M2e | Status bar, face and digits sweep; the Gemini face (D89, D90, D92) | 70c01cb, ce90179 | 430-650 (600, with M2e-i) | not logged |
| M2c-i + N9e + N9 + M4 shell | Player effects; 64 enemy sounds with `$random`; weapon-sound alternatives (D94); SDIZFIR B; the 7 D91 voice takes; MAP01 `D_SDM1N2` (D95), range `D_SDM01T`, intermission `D_SDTITL`; quit lines, help and credit pages | c324f27, ca375c3 | 150 + 250 + 150 (250 + 400 + 150) | not logged |
| M2e-i | Status bar A EN/RU, 42 Gemini faces, digits N2, in-game AI credits | a5129c1, 7ce0984 | 150 | not logged |
| G11 + G10 | Every technology and AI credited (D93); RELEASE.md row 6 per D75 | c1044ec | 60 | not logged |
| Voices | Chatterbox round 1 (D87, 57 takes), round 2 (40 aggressive takes, D96); 17 installed with D91's 7: 8 of 12 voices ours | b1501ba, 7360d20, a98c7c4, d18a40a | not estimated | not logged |
| MAP01 music | The composed piece (D92 exception), N2 chosen (D95) | b22508e, 042cd02 | not estimated | not logged |
| N11 | The one-time Russian review (162 ids, README/CREDITS/LICENSE RU halves), D97 follow-up | d42596b, d530faa | 250 (300) | not logged |
| N16 | Sign-off plan, QA-M4-1, the clean-clone sign-off, tag `v1.0`, the GitHub release; the repo made public (D100) | 4d95475, 4a17a61 | 250 (350) | not logged |

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
