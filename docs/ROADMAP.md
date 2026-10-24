# Roadmap

Living document. Owner: PM. Russian mirror: `docs/ru/ROADMAP.md` (synced at
phase close, D34). **Roadmap v2, approved by the CEO on 2026-10-14 (D63). v1.0 shipped 2026-10-20 (G6 PASS, D97); phases P1-P6 below, P4 under way since 2026-10-21 (D104) and updated 2026-10-22 (D114).** The task list lives in
`docs/BACKLOG.md`; agents are launched only from it.

## The rule (D60, "instrucción importantísima" (CEO: "a hugely important instruction"))

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
| Release | the v1 package (G6) | **done**: G6 PASS for a friends release (4a17a61, `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`); tag `v1.0` and the GitHub release with `sovietdoom-1.0.zip` (SHA-256 `1b4731aa…`) on the repo, **public since 2026-10-20** (D98, D100) |

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
| P2 | Voices and polish | the enemy voices: **3 of the 4 left are ours since D110** (rifleman pain, trooper death, General pain, as `$random` groups, 0c21f76); only the General's death is still Freedoom's (a new round is drafted, waiting for the CEO); the 8 packed beds mixed under their voices, practice-range extras |
| P3 | Russian docs | the full `docs/ru/` mirror (D34) |
| P4 | **The full game: 15-20 levels** (D69) | **In progress since 2026-10-21 (D104): 9 maps in three episodes** — see "P4 today" below. Still ahead: the bosses with their own art, more weapons, v1.1/v1.2; mining Freedoom's 68 maps (BSD) to calibrate our map constants, Ultimate Doom Builder if N15 says yes, and MAP01's alternative piece N for a map (D95) stay parked |
| P5 | **Portable downloads for everyone** (D93) | a public download page on GitHub (Releases of a public repo, no account needed) with a ready-to-run package per OS: Windows (portable zip and/or installer), macOS (app bundle) and Linux (AppImage or tarball), each bundling GZDoom (GPL: source offer), Freedoom (BSD notice) and our PK3; double-click to play. Publishing publicly is a CEO decision at the time. **Done 2026-10-21 for v1.0** (D101, D102): Windows (tested), macOS and Linux (built, not yet run on real machines), sources attached. |
| P6 | **Catalan** (D97) | a third game language: every in-game string, menus, the pause sign and status-bar labels, README and credits in Catalan, with the language switch; reviewed once at the end like N11. **Built 2026-10-21** (0f89be2, D102): the option, the bar, accented font capitals, the pause sign (c9414c2). **The CEO accepted the texts 2026-10-22 ("parece OK", D110).** It ships with the next release (v1.1 draft); Episode 2 and 3 strings are in `[ca]` too (173 ids per language today). |

## P4 today (2026-10-22, D104-D114)

Nine campaign maps in three episodes, picked from the New Game menu (Soviet
Doom → «The Road to Moscow» → «The Portal» → the practice range), each with
its design doc in `docs/levels/`. Maps are UDMF by script, the engine routes
PASS on skills 2, 3 and 4 for all six new maps (18 of 18 reports,
`docs/qa/evidence/2026-10-22_*_report.txt`; Episode 2 at 00:18-00:28,
Episode 3 at 12:33-12:39 on the engine, 9133be1).

| Piece | State |
|---|---|
| **Episode 2, «The Road to Moscow»**: MAP04 Trans-Siberian yard, MAP05 Volga dam, MAP06 Red Square and the Kremlin | **built, routes PASS** (8b98687, D104). Textures: 25 pieces approved (D107) and installed with the maps (43fded6, 7102118, 0bf4de7); the second round (night skies, cab, signal box, levers, roundhouse doors, station sign, window bars, blue door, HV fence, Spasskaya clock and star, GUM shopfronts, museum brick, flags: 23 lumps, b0e46cf) is installed on disk, **commit pending** |
| **Episode 3, «The Portal»**: MAP07 Novaya Zemlya, MAP08 Severomorsk, MAP09 Tunguska | **built, routes PASS** (b42491e, 9133be1, D112). Textures (arctic, naval, taiga/alien: 30 pieces, 36 lumps, 91588fe) installed under the CEO's standing approval (D113), **commit pending**. The ending closes the first cycle with «THE END / For now» |
| Music | **Episode 2: 10 pieces approved (D106) and installed** (0c21f76); **Episode 3: 10 pieces installed** (835f283, D113): each map plays its A, with a random A/B at map start and the boss loop (MAP06, MAP09) when the boss engages |
| Enemies | the seven current enemies **redrawn with Gemini** (D105, D109) with the swastika armbands applied (D108, D114): installed in `assets/sprites/`, **commit pending**. Two new Episode 2 enemies, the Legion heavy gunner `SD_LegionGunner` (21110) and `SD_LibertyColossus` (21111), exist only as behaviour plus provisional sprites in a draft overlay (7c162ae), placed in no map |
| Posters | Lenin, Stalin and the mural in MAP01-06 and the range (e44985b); two slots per map for the Marx and Engels pair (all nine maps) |
| Voices and sound | the Reich hound's 15 barks installed (D107, 0c21f76); three of the four P2 voices installed (D110) |
| Catalan, EN, RU | every Episode 2 and 3 string in the three languages |

**What is missing for P4's first cut**

- **Bosses with their own art.** MAP06 and MAP09 use the General as a
  stand-in (`MAP06_BOSS_SPOT`, `MAP09_BOSS_SPOT`); the Legion gunner, the
  Colossus and the episode boss need Gemini sprites (rate-limited until
  2026-10-22 17:33), install and placement.
- **The TT-33 redone with Gemini** (D111), to match the other six weapons.
- **The Marx and Engels pair** (`SDPOSTR4`/`5`): sweep made (b99fa3f), waiting
  for the CEO's cell, mirror and slogan split; nothing installed.
- **AKM and further weapons**, and the world sounds (doors, switches, items:
  still Freedoom's, P2). Neither has a D-number yet.
- **The Gemini re-asks** listed in the enemy sheet, and the General's death
  voice (new round drafted).
- **Releases:** v1.1 is a **draft** (c9414c2: cursor, death prompt, Catalan);
  it predates all of Episodes 2 and 3. The CEO chooses between publishing it
  as is and waiting for a **v1.2** with P4's work (D109; the PM suggests v1.2,
  `docs/PENDING-CEO-DECISIONS.md`). A v1.2 would need a G6-style sign-off
  (clean clone, routes on the zip's PK3) that has not been run.
- The CEO has not walked Episodes 2 or 3 (D113 replaces his listening and
  texture review for MIDI and procedural textures, not his walk).

Not phased yet: orchestrated music (D99, `docs/ICEBOX.md`). Possible later: a private,
paid Steam build (D98 notes the licence work it would need).

The old phases F3 (MAP01), F4 (arsenal) and F5 (bestiary) fold into M1-M3;
their gates G3-G5 stay as the per-map and per-asset checks inside them.

Rules: gates are defined before the work starts; the first measurement is
honest and strict; a gate may be reframed only by a new D-decision of the CEO.
