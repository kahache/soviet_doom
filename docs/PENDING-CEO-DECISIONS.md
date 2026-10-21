# Pending CEO decisions

Updated: 2026-10-21 night, end of the night shift (D102, D103); before that
2026-10-20 ~16:40, after the v1.0 sign-off (G6 PASS, 4a17a61). Ordered by how much each item unblocks. What
closed since the previous update is listed at the end so nothing is lost.
Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md` (synced at phase close, D34).

## 1. Morning review of the night shift (D102)

Each item waits for your eye or ear; nothing unheard was installed.

1. **v1.1 draft release** (not public): publish it or not. It carries the hammer-and-sickle mouse cursor, the "Press E to continue" prompt on death and Catalan.
2. **Catalan** (`docs/product/2026-10-21_P6_catala-revisio.md`): the texts and questions Q1-Q23. Q3/Q4 were solved tonight with accented capitals in the three fonts.
3. **Dog sounds** for the Reich hound (`work/audio/preview/dog_listening.html`): 5 events × 3 candidates, CC0/CC-BY.
4. **The 4 voices still Freedoom's** (`work/audio/preview/voices_p2_listening.html`): 3 candidates each.
5. **The cursor** (`work/art/preview/cursor_preview.png`): installed; say if you want it changed.
6. Replace the published Windows package with the rebuilt one? The only change is GZDOOM-SOURCE.txt, which now points to the attached sources. Default: no.

## 2. Your own play-through of v1.0 (nothing blocks the release)

The sign-off checked these by instrument or not at all; your ears and eyes
are the check (`docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`):

- sound and music by ear (every engine pass ran `-nosound`);
- with `freedoom1.wad` also present, which IWAD the start dialog offers (G15);
- the credits screen at 16:9; the sergeant's face through its full damage ladder;
- D74's three questions: are the TT-33/PPSh shots strong enough, is the axe
  hit audible on laptop speakers, keep the three packed reload sounds?

Anything you dislike becomes a P1/P2 backlog line, not a v1 blocker.

## 3. V2: which phase first

The parked phases with their estimates are in `docs/BACKLOG.md` ("Parked")
and `docs/ROADMAP.md`: **P1** gameplay pass, **P2** voices and polish,
**P3** Russian docs, **P4** the full game (15-20 maps, more weapons and
enemies), **P5** portable downloads per OS, **P6** Catalan; and orchestrated
music (D99), not yet phased. Calls that wait for their phase: jump/crouch
(G17, P1), metro v2 / Tankograd v2 (N7b/N7c) and the UDB download (N15),
both P4. Nothing here blocks anything today.

## Closed since the previous update (for the record)

D103 (2026-10-21): no balance analysis now. D102: the night shift; P5 downloads approved and done (macOS and Linux packages and the GPL/LGPL sources on release v1.0).

D99 (2026-10-20): orchestrated music is a V2 item (Pro Tools, a better soundfont, MusicGen-Melody; Suno/Udio avoided). D98: v1 public by making this repo public (the yes to do it is item 1). D97: publish v1 for friends after the sign-off; N11's open questions closed with the PM's recommendations; Catalan for V2 (P6). D96: 17 aggressive voice takes approved and installed (8 of 12 voices ours). D95: MAP01 music N2 (`D_SDM1N2`). D94: weapon-sound alternatives (random groups), the IZh pickup keeps Freedoom's; freedoom1.wad allowed. D93: P5 portable downloads; every AI and tool credited (done, G11). D92: digits N2; the composed MAP01 piece; alternatives judged with the weapon animated. D91: 7 voice takes OK, the rest paused. D90: the Gemini face. D89: status bar A, the face from Gemini. D88: the ice axe approved (closes section 1 of the previous update). D87: Chatterbox voices. D86: enemy alternatives, `D_SDM01T` to the range, MAP01 downloads. With them closed: the 15 weapon-sound alternatives (N9a, D94), N9m's page (D86), the M2e sweeps (D89, D90, D92), "publish or not" (D97), the tag (v1.0 at d530faa). The Chatterbox-from-your-own-voice plan of D85 was overtaken by D87/D96; the 4 voices left wait for P2.

D85 (2026-10-20): voices Freedoom's until the MVP, then Chatterbox from the CEO's voice. D84 (2026-10-20): four Gemini weapons approved (IZh-58, RPG-7, ROKS-3, hand Katyusha); the ice axe's strike arm goes back. D83 (2026-10-20): the listening sheet judged 80 of 80 (30 enemy sounds and 5 beds OK; 8 rows NO; title, metro, Tankograd, intermission and radio music OK; `D_SDAMUR` NO; MAP01's music moves off MAP01 and is trimmed; SDIZFIR take B). This also closes the Glinka question (`D_SDGATE` stays in the anthem slot). D82: player effects, option A of each. D81: enemy shells, option A for both. D80: campaign pickups (recommended except SDAG C, SDAH C, SDBP B); the red cross question closed with the PM's default (white cross on green). D79: the Gemini-frames method adopted and Gemini credited (supersedes D78); the CEO's images for the five weapons arrived. D76-D77 (2026-10-15): the ice axe's size; Gemini references local only.

D75 (2026-10-15): ice axe hand C3; Freedoom's notice downloaded; AI line in the credits; Impact accepted; Russian docs after the MVP; M2 includes the player's effects, the HUD goes to M4. D74: the first 30 weapon sounds judged.

D70 (2026-10-14): M1 passed, the CEO walked the campaign; the Doughboy with the bigger flag approved. D69 (2026-10-14): the licence texts may be downloaded (done by the PM); the Lenin slogan closes as shipped («ЛЕНИН ЖИВ»); mining Freedoom's maps waits for the full-game phase; Ultimate Doom Builder is of interest (backlog N15). D44-D68 (2026-10-14): the Stalin poster 4C «СЛАВА СТАЛИНУ!» in the metro's secret shelter; the hound, rifleman, Stormtrooper, Legion, Panzermensch and Schwer installed; palette v2 for the mosaic and marble; Freedoom-based hands (D61) and the TT-33 in them; the map renumbering (D62); roadmap and backlog (D63); pipeline stage 6 (D64); the 21 Tankograd textures (D66); Tankograd's secret, damage and reward (D68). Details in `docs/PRD.md`.

The ice axe replaces the shovel (D40). MAP02 ships as a practice range (D41; the lump `RANGE` since D62). Every music recommendation of SOUNDTRACK §8, accepted (D43). Title screen and intermission (D18). Switch texture: all four variants
approved and installed (D25). Music model and La Internacional (D23).
Alphabet C (D24). Difficulty ladder (D20; the "Pyatiletka in one night" swap
stays an option, not a pending item). Language switch and Cyrillic
letterforms, level 2 (D21, D22). The engine gate (D26). The Windows PC as the
working machine (D27); the Mac's gitignored `work/` reached the PC the same
afternoon, so D27's "stays on the Mac until the CEO copies it" is now
history. Bug B2 (`SDPOSTR2`) resolved 2026-10-12. The font serif fix and the batch 3
props, columns C and D (D29). How MAP01 is judged: by walking it (D28). MAP01 v2 passed its gate and the
text menu is approved (D32); MAP01's scale, densify (D33). The bestiary's seven questions (D35). The German letters, installed for trial (D37). `SDCONC2` and `SDSTAR1` v5, approved
in the map (D30); the hangar wainscot, dropped with them. Bug B3 (art identity
test without `work/`) resolved 2026-10-13. T16, the switch `ANIMDEFS`,
written and seen to flip in engine 2026-10-13.
