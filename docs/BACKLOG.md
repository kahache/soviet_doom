# Backlog

Living document. Owner: PM. **Agents are launched only from this list**, top
first. The CEO approves what moves into "Next". Order follows the MVP rule
(D60) and the milestones of `docs/ROADMAP.md`. Status: `todo`, `doing`,
`waiting CEO`, `done` (done items move to the bottom section once committed).

## Doing (agents at work)

| # | Milestone | Task | Role | From |
|---|---|---|---|---|
| B4 | — | `verify.py fast` back under ~20 s (saves tokens on every task) | qa-engineer | CEO list #6 |

## Next (approved order, D63)

| # | Milestone | Task | Role | Needs |
|---|---|---|---|---|
| N1 | M1 | **Map renumbering** (D62): metro -> MAP02, factory «Танкоград» -> MAP03, the practice range out of the MAPxx slots; campaign MAP01 -> MAP02 -> MAP03 | mod-engineer + level-designer | B4 delivered |
| N2 | M1 | Engine pass of the whole campaign through the route runner | PM | N1 |
| N3 | M2 | Install the chosen pickups (D63) and wire their states | mod-engineer | — |
| N4 | M2 | The other 6 weapons in the Freedoom-based hands, like the TT-33, one sheet each, PM-gated | art-director | — |
| N5 | M2 | Doughboy, Panzermensch (+ Schwer) and General: the CEO picks cells from the sweep, then full sets | art-director | CEO's pick |
| N6 | M2 | Factory textures: the 13 industrial pieces of MAP04-factory §7.2 | art-director | — |
| N7 | M1 | Factory v1 (populated, signposted like the metro v1) and the metro v2 (textures aligned) | level-designer | CEO walks each |
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

2026-10-14 evening: metro v1 (signposted pass, populated, route PASS in engine), factory v0, the route runner for the metro and MAPINFO-driven exits, the TT-33 in Freedoom-based hands, the pickups sweep, the blue pass actor, the campaign MAP01 -> metro, the hands study, the Doughboy/Panzermensch sweep.

The 2026-10-13/14 work is in `git log` and `docs/PRD.md` D40-D62: the
campaign MAP01 -> metro, the blue pass, the four installed enemies, the
Stalin poster, the metro set and mosaic v2, the radio, the credits, the
Russian pause sign, the release tool, the hands study.
