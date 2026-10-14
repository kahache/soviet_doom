# Backlog

Living document. Owner: PM. **Agents are launched only from this list**, top
first. The CEO approves what moves into "Next". Order follows the MVP rule
(D60) and the milestones of `docs/ROADMAP.md`. Status: `todo`, `doing`,
`waiting CEO`, `done` (done items move to the bottom section once committed).

## Doing (agents at work)

| # | Milestone | Task | Role | From |
|---|---|---|---|---|
| B1 | M1 | Metro v1: signpost the blue pass, populate by skill | level-designer | D58 |
| B2 | M1 | Factory v0: design doc and grey box | level-designer | D60 |
| B3 | M1 | Scripted route for the metro; MAP01's routes follow MAP01 -> metro | qa-engineer | D60 |
| B4 | — | `verify.py fast` back under ~20 s (saves tokens on every task) | qa-engineer | CEO list #6 |
| B5 | M2 | TT-33 seen from behind in the Freedoom-based hands, at Doom scale, centred | art-director | D57, D61 |
| B6 | M2 | Doughboy and Panzermensch design sweep | art-director | D35 |
| B7 | M2 | Pickups sweep: ammo, the blue pass «пропуск», the radio | art-director | MOD-SPEC T8, T23 |

## Next (proposed, in order)

| # | Milestone | Task | Role | Needs |
|---|---|---|---|---|
| N1 | M1 | **Map renumbering** (D62): metro -> MAP02, factory -> MAP03, the practice range out of the MAPxx slots | mod-engineer + level-designer | B1-B3 delivered |
| N2 | M1 | Engine pass of the campaign: MAP01 -> metro -> end, the pass, the transition text | PM | N1 |
| N3 | M2 | The other 6 weapons in the Freedoom-based hands, one at a time after the TT-33 is approved | art-director | CEO approves B5 |
| N4 | M2 | Doughboy, Panzermensch (+ Schwer) and General: full sets on the rig | art-director | CEO picks cells from B6 |
| N5 | M2 | Factory textures (brick, rust, chains: LORE) sweep | art-director | B2's list |
| N6 | M1 | Metro v2 and factory v1-v3, the MAP01 method | level-designer | CEO walks each |
| N7 | M3 | Music per map: pick PD works already in the repo, download licence-clean MIDIs if needed (D59) | sound-designer | — |
| N8 | M3 | Install the effects the CEO approves; wire SNDINFO | sound-designer + mod-engineer | CEO's listening |
| N9 | M4 | Full licence texts (GPL-3.0, CC BY-NC-SA 4.0) in the package | mod-engineer | CEO allows the download |
| N10 | M4 | Russian in-game text review, once, at the end of the delivery | translator-ru | M1-M3 done (D60) |

## Waiting for the CEO

See `docs/PENDING-CEO-DECISIONS.md`: sounds and music to hear, the
hand-played G3 runs (deferred by D60), voice takes (D36).

## Parked (after the MVP, D60)

G3 hostile pass and hand-played runs; balance tuning; weapon reloads
(`docs/ICEBOX.md`); voices; the Russian docs mirror (phase close, D34).

## Done (recent, newest first)

The 2026-10-13/14 work is in `git log` and `docs/PRD.md` D40-D62: the
campaign MAP01 -> metro, the blue pass, the four installed enemies, the
Stalin poster, the metro set and mosaic v2, the radio, the credits, the
Russian pause sign, the release tool, the hands study.
