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
| Campaign | **3 maps linked**: MAP01 Zarya-7, MAP02 metro-bunker, MAP03 factory (D62 numbering), each finishable, populated, signposted, textured with our art, with its music | MAP01 v3 done; metro v0 walked, v1 in progress; factory v0 in progress |
| Arsenal | **7 weapons with our own first-person art** (Freedoom-based hands, D61) and our pickups | pickups installed (6 of 7); first-person: TT-33 in progress, the rest after it |
| Bestiary | **7 enemies with our own sprites** | 4 of 7 installed (rifleman, Legion, Stormtrooper, hound) |
| Sound | weapon and enemy effects approved by the CEO (voices optional) | drafts waiting for the CEO's ears |
| Music | title + one public-domain piece per map (no composing, D59) | title and MAP01 done |
| Shell | menus, title, pause, credits, practice range | done |
| Text | every in-game string in EN and RU, the Russian reviewed once at the end | bilingual; review owed |
| Release | the v1 package (G6) | `tools/release.py` ready; full licence texts owed |

## Milestones to the MVP

| Milestone | Goal | Gate (measurable) | Status |
|---|---|---|---|
| F0-F2 | Pipeline, lore, art direction | G0, G1, G2 | **PASSED** (`docs/qa/GATE-REVIEWS.md`) |
| **M1** | **Campaign playable end to end** | the 3 maps run from New Game to the end text with no `idclip`, zero log errors, scripted route PASS on each (`tools/route.py`); the CEO walks it | MAP01 ✓, MAP02 metro v1 ✓ (routes PASS in engine, linked MAP01 -> MAP02 -> MAP03); MAP03 Tankograd v0 (needs v1 and its route); the CEO's walk owed |
| **M2** | **Our art everywhere the player looks** | no Freedoom sprite left in first person, on enemies or on pickups; factory textures approved | 4 of 7 enemies, 7 of 7 pickups, TT-33 in hand (1 of 7 weapons), Tankograd textures 19 of 21 installed |
| **M3** | **Sound and music** | CEO-approved effects installed; one PD piece per map | drafts done, waiting on the CEO |
| **M4** | **Ship v1** (was F6) | G6: licence file with full texts, credits, README EN/RU, the Russian text reviewed, QA sign-off, tag v1.0 | prep done (`docs/engine/RELEASE.md`) |

## After the MVP (gameplay, D60)

| Phase | Goal | Gate |
|---|---|---|
| P1 | Gameplay pass | G3's hostile pass and hand-played runs on skills 2 and 4 for every map; balance by playtest (BALANCE §5); the icebox's reloads if wanted |
| P2 | Voices and polish | the CEO's voice takes (D36); practice-range extras |
| P3 | Russian docs | the full `docs/ru/` mirror (D34) |

The old phases F3 (MAP01), F4 (arsenal) and F5 (bestiary) fold into M1-M3;
their gates G3-G5 stay as the per-map and per-asset checks inside them.

Rules: gates are defined before the work starts; the first measurement is
honest and strict; a gate may be reframed only by a new D-decision of the CEO.
