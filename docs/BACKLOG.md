# Backlog

Living document. Owner: PM. **Agents are launched only from this list**, top
first. The CEO approves what moves into "Next". Order follows the MVP rule
(D60) and the milestones of `docs/ROADMAP.md`. Status: `todo`, `doing`,
`waiting CEO`, `done` (done items move to the bottom section once committed).

## Doing (agents at work)

| # | Milestone | Task | Role | From |
|---|---|---|---|---|
| N4 | M2 | Ice axe (weapon 1 of 6): round 2 with Freedoom's gripping hand (SHTGD0) — **not passed by the PM** (the hand reads as a blob in B and D); waiting on the route decision | art-director | D66 |

## Next (approved order, D63)

| # | Milestone | Task | Role | Needs |
|---|---|---|---|---|
| N2 | M1 | Route for MAP03 Tankograd once it is populated (v1); MAP01 and the metro routes PASS in engine | qa-engineer | factory v1 |
| N5 | M2 | Doughboy C, Panzermensch D (+ Schwer) full sets (D65); then the General's design sweep | art-director | doing |
| N7b | M1 | Metro v2 (textures aligned); Tankograd v2 after the CEO walks v1 | level-designer | CEO walks each |
| N8 | M3 | Music per map from PD works already chosen or licence-clean MIDIs (D59) | sound-designer | — |
| N9 | M3 | Install the effects the CEO approves; wire SNDINFO | sound-designer + mod-engineer | CEO's listening |
| N10 | M4 | Full licence texts (GPL-3.0, CC BY-NC-SA 4.0) in the package | mod-engineer | CEO allows the download |
| N11 | M4 | Russian in-game text review, once, at the end of the delivery | translator-ru | M1-M3 done (D60) |

## Waiting for the CEO

See `docs/PENDING-CEO-DECISIONS.md`: sounds and music to hear, the
hand-played G3 runs (deferred by D60), voice takes (D36).

## Parked (after the MVP, D60)

The TT-33's colour and grey detail (D63, nice to have); G3 hostile pass and hand-played runs; balance tuning; weapon reloads
(`docs/ICEBOX.md`); voices; the Russian docs mirror (phase close, D34).

## Done (recent, newest first)

N7: Tankograd v1 (textures, the red lock cleared, 25/38/52 with the General, ammo to G3-8), walked in engine (`docs/qa/evidence/2026-10-14_2131_F3_tankograd-v1-walk.png`, music D_SDGATE playing). N5: the heavies' full sets, waiting for the CEO.

N6b/N6c: SDCHAN1 (masked) and SDSLOG1 installed, the factory set complete (21 of 21); ANIMDEFS for the molten metal and the portal. N8: a PD piece per map in draft.

2026-10-14 night: N1 map renumbering (MAP01 Zarya-7 -> MAP02 metro -> MAP03 Tankograd, RANGE outside; routes PASS in engine for MAP01, the metro and RANGE); N3 pickups installed; N6 Tankograd textures 19/21 installed; B4 fast verify ~13 s; main green again (eea9992).

2026-10-14 evening: metro v1 (signposted pass, populated, route PASS in engine), factory v0, the route runner for the metro and MAPINFO-driven exits, the TT-33 in Freedoom-based hands, the pickups sweep, the blue pass actor, the campaign MAP01 -> metro, the hands study, the Doughboy/Panzermensch sweep.

The 2026-10-13/14 work is in `git log` and `docs/PRD.md` D40-D62: the
campaign MAP01 -> metro, the blue pass, the four installed enemies, the
Stalin poster, the metro set and mosaic v2, the radio, the credits, the
Russian pause sign, the release tool, the hands study.
