# Soviet Doom — Product Requirements Document

Living document. Owner: PM. Russian mirror: `docs/ru/PRD.md`.
Last update: 2026-10-09 (G1 passed).

## 1. Vision

A GZDoom total conversion in which the USSR of the 1970s is invaded by two
allied alien factions, one Yankee and one Nazi, who have joined forces for
the same goal: to defend capital. The player is a Spetsnaz sergeant who was
a Spanish Civil War refugee child. Soviet paraphernalia everywhere: Lenin
and Stalin posters, slogans, red stars; period weapons. Serious tone.

Lore detail: `docs/product/LORE.md`.

## 2. Who it is for

Classic Doom players (GZDoom) who like total conversions with a strong
visual identity. No monetisation: this is a hobby project, released for free
under a licence to be decided.

## 3. Scope of v1 (D5, proposed)

One complete map (MAP01, Zarya-7 cosmodrome) with its own texture set,
period weapons replacing Doom's slots, and the first enemies. Maps 2 and 3
follow once MAP01 passes its gate.

## 4. Non-goals (for now)

Multiplayer balance, new music, voice acting, Steam/ModDB publishing. Each
goes to `docs/ICEBOX.md` when someone has a concrete idea.

## 5. Decisions (D-numbered, immutable; amend with a new decision)

| # | Date | Decision | Status |
|---|---|---|---|
| D1 | 2026-10-09 | Name **Soviet Doom**. Repo `kahache/soviet_doom`, package `sovietdoom.pk3`, prefix `SD`. Three hobby repos share the name on GitHub (none is a published mod). | ratified (CEO, 2026-10-09) |
| D2 | 2026-10-09 | Base IWAD **Freedoom 0.13.0** (`freedoom2.wad`). The mod redistributes nothing from a commercial IWAD. | ratified (CEO, 2026-10-09) |
| D3 | 2026-10-09 | Engine **GZDoom 4.14.2** minimum (`version "4.12"` in zscript.txt until a 4.14 feature is needed). | ratified (CEO, 2026-10-09) |
| D4 | 2026-10-09 | Textures: own procedural scripts first, OTEX (non-commercial, credited) and Freedoom assets second, CEO material third. Never assets from commercial games. | ratified (CEO, 2026-10-09) |
| D5 | 2026-10-09 | v1 scope = one complete map with own texture set. | ratified (CEO, 2026-10-09) |
| D6 | 2026-10-09 | **The PM commits and pushes.** Private repo from day one. Agents never commit. | ratified (CEO) |
| D7 | 2026-10-09 | **Repo documentation in English and Russian.** English is canonical; every doc has a mirror under `docs/ru/` delivered in the same task. Code and comments in English. In-game text in English and Russian. Conversation with the CEO in Spanish. | ratified (CEO) |
| D8 | 2026-10-09 | Era: **the 1970s**, exact year **1977** (60th anniversary of October). | ratified (CEO) |
| D9 | 2026-10-09 | **Two allied factions**, Yankee aliens and Nazi aliens, united to defend capital. Both appear in the bestiary. | ratified (CEO) |
| D10 | 2026-10-09 | Protagonist: a **Spanish Civil War refugee child** (evacuated from Barcelona to the USSR), now a **Spetsnaz sergeant**. | ratified (CEO) |
| D11 | 2026-10-09 | Tone **serious**. Humour in posters may come later. | ratified (CEO) |
| D12 | 2026-10-09 | Enemies **do carry swastikas and US flags**. It is a video game and a fantastic alternate history; no trivialisation of real victims. Distribution note: Germany allows such symbols in games since 2018 when artistically justified; some stores may still reject them. | ratified (CEO) |
| D13 | 2026-10-09 | Lore v1, three-map episode, period arsenal and bestiary (`docs/product/LORE.md`) **ratified as written**. | ratified (CEO) |
| D14 | 2026-10-09 | Names: protagonist **Sergeant Ramon Vilanova** (Рамон Виланова, b. Barcelona 1931); factions **Fourth Reich** (Nazi aliens) and **Liberty Legion** (Yankee aliens). | ratified (CEO) |
| D16 | 2026-10-13 | **Music: our own instrumental MIDI sequences.** The CEO: "el camino correcto es instrumental en MIDI". No Soviet recordings: every phonogram of Melodiya, the Alexandrov Choir or Radio USSR is protected in the United States into the 2040s-2070s. Historical public-domain compositions may be sequenced by us; the bulk of in-game music is original composition in the idiom of the period. | ratified (CEO) |
| D17 | 2026-10-13 | **Ammo and pickup names in Cyrillic** (period forms: 7,62×25, патроны, ПГ-7В, горючее). The status bar's own AMMO/HEALTH/ARMS/ARMOR are painted into the IWAD's STBAR graphic and are a separate, costed decision. | ratified (CEO) |
| D15 | 2026-10-09 | Licence of the mod: **GPL-3.0** for code (`tools/`, `src/zscript/`, scripts) and **CC BY-NC-SA 4.0** for assets and docs (textures, sprites, maps, sounds, lore). Non-commercial is required anyway by OTEX's terms. Full texts added at F6; `LICENSE.md` states it now. | decided by the PM on CEO delegation |

## 6. Phases and gates

See `docs/ROADMAP.md`. Gates are measured, not argued.

## 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Procedural textures look generic | the Soviet identity is the product | small batches, CEO approves each; poster set is hand-composed from typography and vector shapes |
| Asset licensing | a takedown kills a free mod | `docs/art/LICENSES.md` audited by QA before each gate |
| No level editor on macOS 12 | slow geometry | script-generated UDMF; evaluate UDB on the Windows PC (LA-BESTIA) |
| Russian doc mirror drifts | D7 broken | mirror delivered in the same task; QA checks file parity at each gate |
