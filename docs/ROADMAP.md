# Roadmap

Living document. Owner: PM. Russian mirror: `docs/ru/ROADMAP.md` (synced at
phase close, D34). **Roadmap v2, approved by the CEO on 2026-10-14 (D63). v1.0 shipped 2026-10-20 (G6 PASS, D97); next phases P1-P6 below.** The task list lives in
`docs/BACKLOG.md`; agents are launched only from it.

## The rule (D60, "instrucción importantísima")

**MVP first, gameplay later.** A complete, playable game ships first; balance,
hostile passes and other gameplay polish come after the MVP.

## What the MVP is (v1.0)

A player installs one PK3 next to Freedoom, starts a new game and plays the
whole episode in English or Russian:

| Area | MVP means | Today (2026-10-20, v1.0 tagged at d530faa) |
|---|---|---|
| Campaign | **3 maps linked**: MAP01 Zarya-7, MAP02 metro-bunker, MAP03 factory (D62 numbering), each finishable, populated, signposted, textured with our art, with its music | **done**: MAP01 v3, metro v1, Tankograd v1.1 linked; the CEO walked it (D70); every route PASS on the v1.0 zip's PK3 on skills 2, 3 and 4 (G6) |
| Arsenal | **7 weapons with our own first-person art** (Freedoom-based hands, D61; Gemini frames since D79) and our pickups | **done**: 7 of 7 in first person (TT-33 d2be8ca; PPSh-41 b5bd434; IZh-58, RPG-7, ROKS-3, hand Katyusha and the ice axe c68ad84, D84/D88); 7 of 7 weapon pickups (`SDHP` c68ad84) |
| Bestiary | **7 enemies with our own sprites** | **done**: 7 of 7 (D73) and 4 of 4 projectiles (SDDL/SDPL c68ad84, D81) |
| Sound | weapon and enemy effects approved by the CEO (voices optional) | **done**: 25 weapon sounds (D74) plus the approved alternatives (D94); 81 enemy lumps (c324f27, d18a40a): 43 of 47 enemy sounds ours, 8 of 12 voices (24 Chatterbox takes, D91/D96). Still Freedoom's: 4 voices (rifleman pain, trooper death, General pain and death), the IZh pickup (D94), player, door, switch and item sounds (no gate names them). The 8 beds are packed, unused (P2) |
| Music | title + one public-domain piece per map (no composing, D59) | **done**: title `D_SDINTL`, MAP01 `D_SDM1N2` (composed, the D92 exception, D95), MAP02 `D_SDFUNR`, MAP03 `D_SDGATE`, range `D_SDM01T` (D86), intermission `D_SDTITL` (D83) |
| Shell | menus, title, pause, credits, practice range; the status bar, face, stats screen and help screens (M4, D75) | **done**: status bar A EN/RU, the 42 Gemini faces, digits N2 (a5129c1, D89-D92); quit lines, help and credit pages ours (c324f27). Not ours: the engine's automap and cheat lines (`AMSTR_*`, `STSTR_*`) |
| Text | every in-game string in EN and RU, the Russian reviewed once at the end | **done**: 163 ids in `[enu default]` and `[ru]`; N11 reviewed every player-facing string once (d42596b, D97 follow-up d530faa) |
| Release | the v1 package (G6) | **done**: G6 PASS for a friends release (4a17a61, `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`); tag `v1.0` and the GitHub release with `sovietdoom-1.0.zip` (SHA-256 `1b4731aa…`) on the repo, **still private**; making it public is D98's next step |

## Milestones to the MVP

| Milestone | Goal | Gate (measurable) | Status |
|---|---|---|---|
| F0-F2 | Pipeline, lore, art direction | G0, G1, G2 | **PASSED** (`docs/qa/GATE-REVIEWS.md`) |
| **M1** | **Campaign playable end to end** | the 3 maps run from New Game to the end text with no `idclip`, zero log errors, scripted route PASS on each (`tools/route.py`); the CEO walks it | **PASSED 2026-10-14 (D70)**; re-run on the v1.0 zip at the G6 sign-off: 11 of 11 routes PASS |
| **M2** | **Our art everywhere the player looks** | no Freedoom sprite left in first person, on enemies or on pickups; factory textures approved; plus the player's projectiles, puffs, blood, teleport fog, barrels and lamp (D75) | **PASSED 2026-10-20** (G6 sign-off): the M2 audit's list closed by D80-D92 (pickups e84c56c, weapons and shells c68ad84, effects c324f27); 46 of 46 asset groups ours |
| **M3** | **Sound and music** | CEO-approved effects installed; one PD piece per map | **PASSED 2026-10-20** (G6 sign-off): every approved effect, take and piece installed (D74-D96; c324f27, d18a40a); MAP01's piece is composed by the D92 exception. Not yet heard in engine by anyone but the CEO's own play (the engine passes run `-nosound`) |
| **M4** | **Ship v1** (was F6) | G6: licence file with full texts, credits, README EN/RU, the in-game Russian text reviewed (N11), QA sign-off, tag v1.0; the HUD and shell art (D75). The `docs/ru/` mirror is **not** part of G6: it is P3 (D75) | **PASSED 2026-10-20 for a friends release (G6, D97)**: licences (N10, G9), every AI and tool credited (G11, D93), README EN/RU, HUD and shell (a5129c1), N11, the clean-clone sign-off, tag `v1.0`. Left for the CEO's own play: sound and music by ear, the two-IWAD dialog, the credits screen at 16:9, the face's full damage ladder |

## After the MVP (gameplay, D60)

| Phase | Goal | Gate |
|---|---|---|
| P1 | Gameplay pass | G3's hostile pass and hand-played runs on skills 2 and 4 for every map; balance by playtest (BALANCE §5); the icebox's reloads if wanted |
| P2 | Voices and polish | the 4 enemy voices still Freedoom's (D91/D96: a shouted reference first), the 8 packed beds mixed under their voices, practice-range extras |
| P3 | Russian docs | the full `docs/ru/` mirror (D34) |
| P4 | **The full game: 15-20 levels** (D69) | its own roadmap when v1 ships; starts by mining Freedoom's 68 maps (BSD) to calibrate our map constants; Ultimate Doom Builder if N15 says yes; more weapons and enemies, and the seven enemies v2 from Gemini frames (`docs/ICEBOX.md`); MAP01's alternative piece N kept for one of its maps (D95) |
| P5 | **Portable downloads for everyone** (D93) | a public download page on GitHub (Releases of a public repo, no account needed) with a ready-to-run package per OS: Windows (portable zip and/or installer), macOS (app bundle) and Linux (AppImage or tarball), each bundling GZDoom (GPL: source offer), Freedoom (BSD notice) and our PK3; double-click to play. Publishing publicly is a CEO decision at the time. **Done 2026-10-21 for v1.0** (D101, D102): Windows (tested), macOS and Linux (built, not yet run on real machines), sources attached. |
| P6 | **Catalan** (D97) | a third game language: every in-game string, menus, the pause sign and status-bar labels, README and credits in Catalan, with the language switch; reviewed once at the end like N11. **Built 2026-10-21** (0f89be2, D102): 165 ids, the option, the bar, accented font capitals; waiting for the CEO's review. The pause sign is still English. |

Not phased yet: orchestrated music (D99, `docs/ICEBOX.md`). Possible later: a private,
paid Steam build (D98 notes the licence work it would need).

The old phases F3 (MAP01), F4 (arsenal) and F5 (bestiary) fold into M1-M3;
their gates G3-G5 stay as the per-map and per-asset checks inside them.

Rules: gates are defined before the work starts; the first measurement is
honest and strict; a gate may be reframed only by a new D-decision of the CEO.
