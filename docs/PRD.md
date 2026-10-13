# Soviet Doom — Product Requirements Document

Living document. Owner: PM. Russian mirror: `docs/ru/PRD.md`.
Last update: 2026-10-13 (D25-D36).

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

Multiplayer balance, voice acting, Steam/ModDB publishing. Each goes to
`docs/ICEBOX.md` when someone has a concrete idea. (Music was listed here
until D16 brought it into scope on 2026-10-13.)

## 5. Decisions (D-numbered, immutable; amend with a new decision)

| # | Date | Decision | Status |
|---|---|---|---|
| D1 | 2026-10-09 | Name **Soviet Doom**. Repo `kahache/soviet_doom`, package `sovietdoom.pk3`, prefix `SD`. Three hobby repos share the name on GitHub (none is a published mod). | ratified (CEO, 2026-10-09) |
| D2 | 2026-10-09 | Base IWAD **Freedoom 0.13.0** (`freedoom2.wad`). The mod redistributes nothing from a commercial IWAD. | ratified (CEO, 2026-10-09) |
| D3 | 2026-10-09 | Engine **GZDoom 4.14.2** minimum (`version "4.12"` in zscript.txt until a 4.14 feature is needed). | ratified (CEO, 2026-10-09) |
| D4 | 2026-10-09 | Textures: own procedural scripts first, OTEX (non-commercial, credited) and Freedoom assets second, CEO material third. Never assets from commercial games. | ratified (CEO, 2026-10-09) |
| D5 | 2026-10-09 | v1 scope = one complete map with own texture set. | ratified (CEO, 2026-10-09) |
| D6 | 2026-10-09 | **The PM commits and pushes.** Private repo from day one. Agents never commit. | ratified (CEO) |
| D7 | 2026-10-09 | **Repo documentation in English and Russian.** English is canonical; every doc has a mirror under `docs/ru/` delivered in the same task. Code and comments in English. In-game text in English and Russian. Conversation with the CEO in Spanish. | ratified (CEO); **amended by D34** (docs mirrored in batches at phase close) |
| D8 | 2026-10-09 | Era: **the 1970s**, exact year **1977** (60th anniversary of October). | ratified (CEO) |
| D9 | 2026-10-09 | **Two allied factions**, Yankee aliens and Nazi aliens, united to defend capital. Both appear in the bestiary. | ratified (CEO) |
| D10 | 2026-10-09 | Protagonist: a **Spanish Civil War refugee child** (evacuated from Barcelona to the USSR), now a **Spetsnaz sergeant**. | ratified (CEO) |
| D11 | 2026-10-09 | Tone **serious**. Humour in posters may come later. | ratified (CEO) |
| D12 | 2026-10-09 | Enemies **do carry swastikas and US flags**. It is a video game and a fantastic alternate history; no trivialisation of real victims. Distribution note: Germany allows such symbols in games since 2018 when artistically justified; some stores may still reject them. | ratified (CEO) |
| D13 | 2026-10-09 | Lore v1, three-map episode, period arsenal and bestiary (`docs/product/LORE.md`) **ratified as written**. | ratified (CEO) |
| D14 | 2026-10-09 | Names: protagonist **Sergeant Ramon Vilanova** (Рамон Виланова, b. Barcelona 1931); factions **Fourth Reich** (Nazi aliens) and **Liberty Legion** (Yankee aliens). | ratified (CEO) |
| D23 | 2026-10-13 | **Amends D16.** Music is no longer composed by us in a script: the CEO judged the first two pieces "bien pero un poco simples" and ruled "no construyas tú los MIDIs, mejor descargarlos". Free MIDI sequences with a verified licence come first, our own sequencing is the fallback for works that exist only as free scores. **La Internacional is the title theme.** The three-rights rule of D16 stands in full: a free composition does not imply a free sequence, and a free sequence does not imply a free recording. | ratified (CEO) |
| D24 | 2026-10-13 | **Alphabet: variant C "Mashina"**, chosen from three set against real game strings in both scripts. Installed as `fonts/defsmallfont/` and `fonts/bigfont/`, 214 glyphs, drawn from the project's own stroke rules so no typeface licence is inherited. This is what makes D7 and D21 possible inside the game at all. | ratified (CEO) |
| D20 | 2026-10-13 | **Difficulty ladder** (`docs/product/DIFFICULTY-NAMES.md`): Pioneer / worse winters / not one step back / no pasarán, comrades / Hero of the Soviet Union, posthumously. Chosen by the CEO from three proposed sets. | ratified (CEO) |
| D21 | 2026-10-13 | **The game can be played entirely in Russian**, chosen explicitly in the menu, not inherited from the system locale. A test fails if any `SD_*` string exists in English without its Russian line. | ratified (CEO) |
| D22 | 2026-10-13 | **The English build uses Cyrillic letterforms for R (Я) and N (И)**, as a font-level mapping, leaving the strings themselves correct English. The PM argued against it as a fake accent that costs legibility; the CEO decided otherwise. **Level 2**: R→Я, N→И, E→Э, W→Ш, A→Д, chosen by the CEO on 2026-10-13 after seeing all three intensities rendered on real strings. The PM recommended level 1. | ratified (CEO), PM dissent recorded |
| D18 | 2026-10-13 | **Shell screens: treatment A as `TITLEPIC`, treatment C as `INTERPIC`.** The CEO liked both ("me flipan A y C") and the two roles let both ship: A greets, C sits behind the between-level statistics because its diagonal leaves the centre empty. Menu logo follows A. | ratified (CEO) |
| D19 | 2026-10-13 | **The work pipeline is written and enforced** (`docs/PIPELINE.md`): seven stages, file ownership declared per commission, sweeps as the unit of visual review, four green verifications before any commit, a `pmo` agent that blocks on documentation gaps, and explicit rules for when to stop and ask the CEO and when to proceed. Created at the CEO's request. | ratified (CEO) |
| D16 | 2026-10-13 | **Music: our own instrumental MIDI sequences.** The CEO: "el camino correcto es instrumental en MIDI". No Soviet recordings: every phonogram of Melodiya, the Alexandrov Choir or Radio USSR is protected in the United States into the 2040s-2070s. Historical public-domain compositions may be sequenced by us; the bulk of in-game music is original composition in the idiom of the period. | ratified (CEO) |
| D17 | 2026-10-13 | **Ammo and pickup names in Cyrillic** (period forms: 7,62×25, патроны, ПГ-7В, горючее). The status bar's own AMMO/HEALTH/ARMS/ARMOR are painted into the IWAD's STBAR graphic and are a separate, costed decision. | ratified (CEO) |
| D25 | 2026-10-13 | **Switch textures: all four variants ship**, `SDSW1A-D` (off) and `SDSW2A-D` (on), Doom's own 1 = off / 2 = on convention with the variant letter last. The CEO took all four rather than one: "yo por mí mete todos, así tenemos diversidad". Variant A was relaid first (its word and lamp overlapped; the CEO saw it). | ratified (CEO) |
| D26 | 2026-10-13 | **Amends D19. Agents never start GZDoom.** `tools/run.sh` and `tools/smoke.py` refuse to launch unless `SD_ALLOW_ENGINE=1` is set, and only the PM sets it; an agent whose change needs the engine verifies with `tools/verify.py fast`, says the engine run is owed, and the PM batches those runs. CEO: "no paran de abrirse ventanas del doom interrumpiendo mi trabajo, como 3-4 ventanas cada 20 segundos". | ratified (CEO) |
| D27 | 2026-10-13 | **The working machine is the CEO's Windows PC** ("vamos a hacer todo desde aquí"). GZDoom g4.14.2, Freedoom 0.13.0 and the venv live there; the tooling finds both machines' layouts. Gitignored `work/` stays on the Mac until the CEO copies it; **nothing done on the Mac is redone**. Approved assets are regenerated only on the machine that rendered them (text-bearing lumps differ between the two Impact builds) or go back to the CEO as a new proposal. | ratified (CEO) |
| D28 | 2026-10-13 | **A map is judged by walking it, not by reading it.** The CEO did not ratify MAP01's design text: "solo por texto no sabía yo si estaría bien el mapa o no; decidimos montarlo sin texturas para navegarlo y opinar". Hence v0 as an untextured grey box (built 2026-10-13, walked by the CEO the same night, `docs/levels/MAP01-zarya-7.md` §14). The design document is a working brief the PM approved; the CEO's verdict comes from the engine. Applies to every map. | ratified (CEO) |
| D29 | 2026-10-13 | **Two art approvals.** The alphabet C serif fix for M, М and W (6 of 214 glyph files, QA finding H1), and batch 3 props: column C for the three crate pieces, kept in khaki with the stencilled numbers, and column D for the locker. CEO: "apruebo el arreglo de la fuente y cajas C y D". | ratified (CEO) |
| D30 | 2026-10-13 | **The last two batch-1 textures are approved in the map**, after the CEO walked MAP01 v1 in GZDoom on this PC. `SDCONC2`, the red stripe, ships as built, three bands in the hangar included: "no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas" (so no hangar wainscot). `SDSTAR1` v5, the emblem plaque: "la apruebo, preciosa". Batch 1 is 12 of 12 approved. The CEO on v1 overall: "ahora sí que funciona". | ratified (CEO) |
| D31 | 2026-10-13 | **The main menu and the skill-screen headers become text in our alphabet, with D22's letterforms in English** (treatment B), replacing Freedoom's red graphics (debt T12). One folder font, `SDMENU`, serves both languages: Russian strings use Cyrillic code points and are untouched by the substitution. Built for an in-engine trial; the CEO judges it on screen. Painted poster-style menu graphics (treatment C) are parked in `docs/ICEBOX.md`. CEO: "Vamos con B a ver q tal queda, y anota como pendiente en el futuro hacer C si fuera necesario". Also first construction of D22, ratified the same morning and never built until now. | ratified (CEO) |
| D32 | 2026-10-13 | **MAP01 v2 passes its gate criterion, and the text menu of D31 is approved.** The CEO walked v2 on this PC: "he pasado el hangar sin ayuda, menú aprobado, incluso he encontrado la sala secreta (aunque era muy evidente)". The secret being too obvious is a v3 note. His verdict on scale: "como nivel de prueba está bien; a nivel de juego sería un nivel muy corto/pequeño. un nivel de doom normal puede ser de 5 a 6 veces ésto". Measured the same day against Freedoom's 32 maps: our 80 sectors / 322 lines against 211 / 1274 for Freedoom's MAP01 and a median of 240 / 1861; the footprint is already a first map's (6.5 against 8.2 million square units), the density is not. | ratified (CEO) |
| D33 | 2026-10-13 | **MAP01 is densified, not enlarged.** Same floor plan and flow; v3 adds shape to the empty rooms (pillars, height changes, alcoves, structure), combat and resources by skill, and subtler secrets, aiming at the density of Freedoom's MAP01 (~200 sectors, ~1200 lines) and 5-8 minutes of play. MAP02 and MAP03 are built at median size later. D5 (v1 = one complete map) stands. Chosen by the CEO from three options: densify MAP01, enlarge it five-fold, or make v1 the three-map episode. | ratified (CEO) |
| D34 | 2026-10-13 | **Amends D7. In-game text stays bilingual at all times; the repo documentation is mirrored into Russian in batches, not in the same task.** Every `SD_*` string still ships with its `[ru]` line (D21, enforced by test). The `docs/ru/` mirror is brought up to date when a phase closes at its gate, and in full before any release (F6); between batches each mirror states the date it was last synced. Why: the mirror is an artistic gesture and a door for future Russian players ("lo quería solo como parte artística y para atraer usuarios rusos en el futuro"), nobody reads it during development, and same-task mirroring cost about a third of the agent runs on 2026-10-13 while translating documents that were rewritten hours later. Proposed by the PM, decided by the CEO: "sigamos con tu propuesta". | ratified (CEO) |
| D35 | 2026-10-13 | **The bestiary's seven open questions, answered** (`docs/engine/BESTIARY.md` §14, all on the recommendation). Sprites: **mixed**, the five most-seen enemies drawn from scratch with an identity of their own, death and gib frames may be edited Freedoom (BSD-3, credited). Drops: the invaders carry **captured Soviet arms**, so they drop our ammunition and weapons. MAP01 is **Reich-first**, the Liberty Legion appearing halfway as the force holding the hangar; MAP02 inverts it, MAP03 mixes. And: two names for the two infantries; Panzermensch at 500 HP in MAP01 with a 1000 HP variant for MAP03; the General is a boss with a verb (below half health he summons two recruits); the factions keep Doom's infighting, an alliance of convenience. | ratified (CEO) |
| D36 | 2026-10-13 | **Enemy sound: sources and voices** (`docs/sound/ENEMY-SOUNDS.md`). The CC0 packs listed there may be downloaded, each with its provenance row and SHA-256. The enemy voices are the CEO's: "me encargaré de las grabaciones y/o generar con IA lo que sea necesario"; any AI-generated voice carries the tool and its licence in the licence register like any other asset. **Factions speak real languages:** "prefiero que sea alemán real e inglés real", so the Reich speaks German and the Liberty Legion English, replacing the sound-designer's proposal of invented German-sounding syllables. The General's order is **"Vorwärts."** D11 (serious tone) and D12 still bind: real military callouts, not the regime's slogans. | ratified (CEO) |
| D15 | 2026-10-09 | Licence of the mod: **GPL-3.0** for code (`tools/`, `src/zscript/`, scripts) and **CC BY-NC-SA 4.0** for assets and docs (textures, sprites, maps, sounds, lore). Non-commercial is required anyway by OTEX's terms. Full texts added at F6; `LICENSE.md` states it now. | decided by the PM on CEO delegation |

## 6. Phases and gates

See `docs/ROADMAP.md`. Gates are measured, not argued.

## 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Procedural textures look generic | the Soviet identity is the product | small batches, CEO approves each; poster set is hand-composed from typography and vector shapes |
| Asset licensing | a takedown kills a free mod | `docs/art/LICENSES.md` audited by QA before each gate |
| Maps are built by script, no editor | slow geometry | script-generated UDMF works (MAP01 v1, 54 sectors); Ultimate Doom Builder is now possible on the Windows PC (D27), to be evaluated when a map needs hand editing |
| Russian doc mirror drifts | the mirror is wrong when a Russian reader arrives | D34: drift is accepted between gates; each mirror carries its sync date, and the mirror is synced and parity-checked at every phase close and in full before release |
