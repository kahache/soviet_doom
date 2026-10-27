# Pending CEO decisions

Updated: 2026-10-22, after Episode 3's routes PASS (9133be1, D114); before that
2026-10-21 night (D102, D103) and 2026-10-20 ~16:40 (v1.0 sign-off, G6 PASS,
4a17a61). Ordered by how much each item unblocks. What closed since the
previous update is listed at the end so nothing is lost.
Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md` (synced at phase close, D34).

> **2026-10-27: the game is closed.** v1.3 (V3) is published as the finished game and the last
> content version (D131, D135, D136); v1.2 and v1.0 were deleted. What follows is the 2026-10-22 snapshot,
> kept as history. The only scheduled item is the Android APK (`docs/ICEBOX.md`, D131).

Nothing is open with the CEO: §1 (v1.1 or v1.2) closed with D130, and every later question with D131-D136.

## 1. Release: v1.1 now, or wait for v1.2 (D109)

The **v1.1 draft release** (not public; target c9414c2) carries the
hammer-and-sickle cursor, the "Press E to continue" prompt on death and
Catalan (accepted, D110). Since then P4 added Episodes 2 and 3 (six maps), the
Gemini enemies, new music and textures, none of it in v1.1.

- **Publish v1.1 as it is**, or **wait for a v1.2** with everything of P4.
  The PM suggests v1.2 (D109): v1.1 would ship the old three-map game. A v1.2 needs a G6-style
  sign-off first (BACKLOG Next #12).
- Replace the published Windows package of v1.0 with the rebuilt one? The
  only change is GZDOOM-SOURCE.txt, which now points to the attached sources.
  Default: no.

## 2. Marx and Engels poster pair (D106)

The sweep is `docs/art/previews/2026-10-22_P4_marx-engels-sweep.png` (study:
`docs/product/2026-10-22_P4_marx-engels-poster-sourcing.md` §8). Four calls,
the PM's proposal first; nothing is installed until you answer:

1. **Cells:** Marx 4D, Engels 4C (point at another in the sweep if you prefer).
2. **Mirror:** Engels flipped so the two face each other (proposed; a flip
   changes his likeness: parting, beard), or as photographed.
3. **The slogan's cut:** «ПРОЛЕТАРИИ ВСЕХ / СТРАН,» + «СОЕДИНЯЙТЕСЬ!» at 15 px
   (your split), or «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» at 17 px.
4. **Alignment:** Engels's word on the row of Marx's second line (proposed),
   or centred.

## 3. The General's death voice (D110)

Every take was NO (D110); a **new round** is drafted
(`work/audio/preview/voices_p2b_listening.html`). Until you pick one, his death
keeps Freedoom's sound.

## 4. Episode 3: open points (walk MAP07-MAP09)

No walk of Episodes 2 or 3 by the CEO is recorded in the PRD (D113 covers music and textures, not
the maps). Questions that only your eye can answer:

- **MAP07 (`docs/levels/MAP07-novaya-zemlya.md` §14):** the exit vehicle,
  **a submarine (as built) or an icebreaker?** (the conning tower becomes a
  bridge door); and the **Hand Katyusha**: keep it in secret S3, or give it on
  the route at the start of Episode 3? (MAP05 and MAP08 keep it in a secret as built.)
- **MAP09 (§17):** is the taiga calm enough or too empty? Is the crater's
  descent the right finale, or should the portal itself be reachable?
- **The end of Episode 3** (`SD_END04_TEXT`): «THE END / For now» («КОНЕЦ /
  Пока»), the first ending that is not «TO BE CONTINUED»; Episodes 1 and 2 still
  end on «TO BE CONTINUED». Right as written?

## 5. Your own play-through of v1.0 (nothing blocks the release)

The sign-off checked these by instrument or not at all; your ears and eyes
are the check (`docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`):

- sound and music by ear (every engine pass ran `-nosound`);
- with `freedoom1.wad` also present, which IWAD the start dialog offers (G15);
- the credits screen at 16:9; the sergeant's face through its full damage ladder;
- D74's three questions: are the TT-33/PPSh shots strong enough, is the axe
  hit audible on laptop speakers, keep the three packed reload sounds?

Anything you dislike becomes a P1/P2 backlog line, not a v1 blocker.

## 6. V2: which phase first

The parked phases with their estimates are in `docs/BACKLOG.md` ("Parked")
and `docs/ROADMAP.md`: **P1** gameplay pass, **P2** voices and polish,
**P3** Russian docs, **P4** the full game (15-20 maps, more weapons and
enemies), **P5** portable downloads per OS, **P6** Catalan; and orchestrated
music (D99), not yet phased. Calls that wait for their phase: jump/crouch
(G17, P1), metro v2 / Tankograd v2 (N7b/N7c) and the UDB download (N15),
both P4. Nothing here blocks anything today.

## Closed since the previous update (for the record)

D104-D114 (2026-10-21 to 2026-10-22): the cursor and the Catalan letters approved (D104), and the Catalan texts accepted with the PM's answers to Q1-Q23 (D110); the night shift's review items are all closed: the 15 dog sounds OK and installed (D107), three of the four P2 voices OK and installed (D110; the General's death is §3), the cursor installed. The armband swastika: the mix approved and the seven Gemini enemies approved (D108, D109, D114). Episode 2's 10 pieces (D106) and 25 textures (D107) approved. Standing approval for composed music and procedural textures (D113): the CEO no longer reviews those. Episodes 2 and 3 opened under the long autonomous push (D104, D112); the TT-33 queued for Gemini (D111).

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
