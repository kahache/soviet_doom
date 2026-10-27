# MOD-SPEC — technical contract of the mod

Owner: `mod-engineer`. Contract with `level-designer` and `art-director`:
names, paths and lumps the engine expects. **Changing it = updating this doc
before the code.** Status: F4 arsenal verified on GZDoom 4.14.2, 2026-10-12;
ammunition renamed and the shovel silenced after the CEO's play session,
2026-10-13; PK3 tree, asset mapping, switch naming and the T9 closure
recorded after the `pmo` audit of the Mac batch (PMO-09, PMO-10),
2026-10-13; main menu and skill screen in our own type (D31, §6.6),
2026-10-13, pending the engine pass (F0 pipeline verified 2026-10-09);
F5 bestiary — eight enemy classes and four projectiles with Freedoom
placeholders, their editor numbers, sounds, sprites and MAP02 bench (D35,
§5.1, §6, §6.1–6.3), 2026-10-13; **engine pass done the same day**
(clean load, drops, one summon: ADR 006, `docs/engine/adr/006-bestiary-actors.md`),
with infighting, blood colour and attack numbers still NOT VERIFIED (T22).
**D40, 2026-10-13: slot 1 is an ice axe, `SD_IceAxe`, not a shovel**; the
new class, file, string, sound and sprite names are in §6 ("Slot 1 since
D40"); **engine pass done the same day** (the dorm rack's pickup prints
"An ice axe." and `printinv` lists `SD_IceAxe`; sprites still Freedoom's
placeholders: `docs/qa/evidence/2026-10-13_2039_d40-d43-engine-pass.md`).
**D41, the same day: MAP02 ships as a practice range**, a second episode on
the New Game screen (§4.4, ADR 007); **engine pass done the same day**
(the episode screen in English and Russian, same evidence), and MAP02's exit
switch and on-foot gallery followed in commit `d1e891f` (§4.4).
**D43 music (§4.5):** MAP01's `D_SDM01` seen in the engine the same day,
and the title's `D_SDINTL` at 21:50 (`currentmusic`,
`docs/qa/evidence/2026-10-13_2150_F6_title-music.log`).
**D43 diegetic radio (§6.7, ADR 008), 2026-10-13:** `SD_Radio` and its two
CC0 pieces `D_SDRAD1` / `D_SDRAD2`, written before the code; **NOT YET
SEEN IN THE ENGINE** (D26), and its editor number 21200 waits for the PM's
`MAPINFO` line.
**D46, 2026-10-14:** MAP02 is titled "Training Ground" / «Учебный полигон»
(§4, the episode name kept: §4.4), and the credits carry "A fan project,
not affiliated with id Software" in the team block (§6.8); both are
`LANGUAGE` text, **not yet seen in the engine** (D26).
**D48, 2026-10-14: the first sprites of our own ship.** The world pickups of
six weapons (`SDAP`, `SDTP`, `SDIP`, `SDPQ`, `SDRP`, `SDKP`) are packed from
`assets/sprites/` and named by the weapons' `Spawn` states (§6.3, "Installed
since D48"); the held and flash frames stay Freedoom's, the hand being
redrawn. **NOT YET SEEN IN THE ENGINE** (D26).
**D48 pause plaque per language and D49 blood, 2026-10-14:** the build
packs `assets/localized/**` at its own path, for the Russian face of the
pause sign `M_PAUSE` (§2, "Language variants"), and `check_pk3` validates
it; **GZDoom g4.14.2 loads such a variant but does not draw it** (read in
the engine source, T24). Every enemy bleeds dark red, `BloodColor "AD 27 21"`
(D49, `BESTIARY.md` §2.1, §6.3 below). Both **NOT YET SEEN IN THE ENGINE** (D26).
**T24, 2026-10-14: the mod draws the pause sign itself.** A status bar class
of ours, `SD_StatusBar`, derives from Doom's `DoomStatusBar` and overrides
only `DrawPaused`, drawing the graphic the `LANGUAGE` id `SD_PAUSE_SIGN`
names: `M_PAUSE` in English, the Russian variant's full path in Russian
(§6.5.1, ADR 010). `assets/localized/textures/M_PAUSE.ru.png` is installed
(P2 «ПАУЗА», D48) and `tools/release.py` credits `localized/` through the
base's licence row. **NOT YET SEEN IN THE ENGINE** (D26).
**D54, 2026-10-14: the first enemy wears its own sprites.** The Liberty
Legion trooper's full set, cell C with the redone death (70 `SDLT` lumps,
`assets/sprites/legion/`), is packed and every `SD_LegionTrooper` state
names `SDLT` instead of Freedoom's `SPOS`, not one tic changed (§5.1, §6.3,
"The Legion trooper, installed by D54"). **NOT YET SEEN IN THE ENGINE** (D26).
**D55, 2026-10-14: the Reich rifleman and the Reich hound wear their own
sprites.** The rifleman's full set from the rig with the bloody death and
flat corpse (70 `SDRR` lumps, `assets/sprites/rifleman/`) and the German
shepherd's (46 `SDHN` lumps with mirrored pairs, `assets/sprites/hound/`)
are packed; every `SD_ReichRifleman` state names `SDRR` instead of `POSS`
and every `SD_ReichHound` state `SDHN` instead of `SARG`, not one tic
changed (§5.1, §6.3, "The Reich rifleman and the Reich hound, installed by
D55"). **NOT YET SEEN IN THE ENGINE** (D26).
**D56, 2026-10-14: the Hybrid Stormtrooper and his bolt wear their own
sprites.** Cell E's full set with the redone death (77 `SDHS` and 5 `SDBL`
lumps, `assets/sprites/storm/`) is packed; every `SD_Stormtrooper` state
names `SDHS` instead of `TROO` and every `SD_StormBolt` state `SDBL`
instead of `BAL1`, not one tic changed (§5.1, §6.3, "The Hybrid
Stormtrooper and his bolt, installed by D56"). **NOT YET SEEN IN THE
ENGINE** (D26).
**MAP03's blue pass, 2026-10-14:** `SD_BluePass` (`zscript/sd/keys.zs`)
`replaces BlueCard`, so MAP03's editor number 5 spawns it with the map
untouched; it declares `Species "BlueCard"`, which is what makes lock 2
accept it (the engine's lock test ignores inheritance; read in g4.14.2's
source). Pickup line "Blue pass." / «Синий пропуск.»; the locked-door line
says pass / пропуск through the engine's own `PD_BLUECO` in `LANGUAGE`
(§6, "The blue pass"). Sprite still Freedoom's `BKEY`. **NOT YET SEEN IN
THE ENGINE** (D26).
**D62, 2026-10-14: the map slots follow the campaign (§4, §4.6).** MAP01
Zarya-7, **MAP02 the metro-bunker** (built as MAP03), **MAP03 the factory,
«Танкоград» / Tankograd** (built as MAP04, D63), and the practice range left
the MAPxx sequence for the lump **`RANGE`** (it was MAP02). The campaign is
MAP01 → MAP02 → MAP03, the factory ends it, and `SD_END01_TEXT` now tells
the portal's fall. Entries above this one use the numbers of their day: a
"MAP02" there is the range, a "MAP03" the metro. **NOT YET SEEN IN THE
ENGINE** (D26; the PM's checks C1-C8, §4.6).
**D67, 2026-10-14: the Panzermensch and the Schwer wear their own
sprites.** Cell D's full set (71 `SDPM` lumps) and the Schwer's, cell D
with S2 (71 `SDPS`), both in `assets/sprites/panzermensch/`, are packed;
every `SD_Panzermensch` state names `SDPM` instead of `BOS2`, and
`SD_PanzermenschSchwer` has a `States` block of its own, the base's line
for line on `SDPS`; not one tic changed in either (§5.1, §6.3, "The
Panzermensch and the Schwer, installed by D67"). The Schwer's body grows
with its drawing to 27 × 72 (was the base's 24 × 64), checked to fit
everywhere a map places it. **NOT YET SEEN IN THE ENGINE** (D26).
**D70, 2026-10-14: the Doughboy wears its own sprites.** Cell C's full set
with D67's bigger flag (54 `SDDB` lumps, `assets/sprites/doughboy/`) is
packed; every `SD_Doughboy` state names `SDDB` instead of `HEAD`, not one
tic changed (§5.1, §6.3, "The Doughboy, installed by D70"). The body stays
31 × 56: the drawing fits it as `HEAD` did, and every place a map puts it
was checked. The shell keeps `BAL2`. **NOT YET SEEN IN THE ENGINE** (D26).
**D73, 2026-10-14: the General and his shell wear their own sprites.** The
CD design's full set (81 `SDGN` and 5 `SDGL` lumps,
`assets/sprites/general/`) is packed; every `SD_General` state names `SDGN`
instead of `CYBR`, the two `Summon` lines with their own frames `Q R`
(they borrowed `CYBR E F`), and `SD_GeneralShell` names `SDGL` instead of
`MANF` and `MISL`, its burst on the new letters `C D E`; not one tic
changed (§5.1, §6.3, "The General and his shell, installed by D73"). The
body stays 40 × 100, and both places a map puts him were checked. **NOT
YET SEEN IN THE ENGINE** (D26).
**N17, 2026-10-15: the TT-33 is ours in hand.** Its held frames `SDTT` A–C
and its flash `SDTF` A, our TT-33 seen from behind in Freedoom's pistol
hands recoloured (R3-A1, D61; approved in hand, D63), are packed from
`assets/sprites/tt33/`; every `SD_Tokarev` state names `SDTT`/`SDTF`
instead of `PISG`/`PISF`, not one tic changed (§5.1, §6.3, "The TT-33 in
hand"; redone with Gemini by D123). Until now only the draft overlay showed them.
The first lumps of the PK3 derived from Freedoom's art (BSD 3-clause,
`docs/art/LICENSES.md`). **NOT YET SEEN IN THE ENGINE from the PK3**
(D26); the same files were seen through the overlay on 2026-10-14.
**D79, 2026-10-20: the PPSh-41 is ours in hand.** Its held frames `SDPP`
A–B and its flash `SDPF` A, built by `tools/art/gemini_frames.py` from the
CEO's Google Gemini pair (the method adopted by D79), are packed from
`assets/sprites/ppsh/`; every `SD_Ppsh` state names `SDPP`/`SDPF` instead
of `CHGG`/`CHGF`, not one tic changed (§5.1, §6.3, "The PPSh-41 in hand,
installed by D79"). **NOT YET SEEN IN THE ENGINE from the PK3** (D26); the
uncorrected test frames were seen through the overlay on 2026-10-19.
**D84, 2026-10-20: the IZh-58, RPG-7, ROKS-3 and hand Katyusha are ours in
hand.** Their held and flash frames (`SDIZ` A–D and `SDIF` A–B, `SDRL` A–B
and `SDRF` A–D, `SDRK` A–B and `SDKF` A, `SDHK` A–B and `SDHF` A–B), built
by `tools/art/gemini_frames.py` from the CEO's Google Gemini images, are
packed from `assets/sprites/<weapon>/`, and the hand Katyusha's floor
pickup (the Katyusha's `SDHP` A, D80) from `assets/sprites/pickups/`; every state names
them instead of `SHTG`/`SHTF`, `MISG`/`MISF`, `PLSG`/`PLSF`,
`BFGG`/`BFGF`/`BFUG`, not one tic changed (§5.1, §6.3, "The IZh-58, RPG-7,
ROKS-3 and hand Katyusha in hand, installed by D84"). **NOT YET SEEN IN
THE ENGINE from the PK3** (D26); the same frames were seen through the
overlay on 2026-10-20.
**D88, 2026-10-20: the ice axe is ours in hand.** Its held frames `SDAX`
A–D, the ready frame from the CEO's Google Gemini image and the swing
rotated from it as one rigid piece (`tools/art/gemini_frames.py`), are
packed from `assets/sprites/ice_axe/`; every `SD_IceAxe` state names `SDAX`
instead of `PUNG`, not one tic changed (§5.1, §6.3, "The ice axe in hand,
installed by D88"). Every weapon sprite the player holds or picks up is
ours; only the projectiles in flight still wear Freedoom's. **NOT YET SEEN
IN THE ENGINE from the PK3** (D26).
**D81, 2026-10-20: the Doughboy's and the Panzermensch's shells are ours.**
The Doughboy's shell `SDDL` A–E (option A, "comet") and the Panzermensch's
shell `SDPL` A–E (option A, "ember"), drawn by `tools/art/gen_shells.py`, are packed from `assets/sprites/doughboy/` and
`assets/sprites/panzermensch/`; `SD_DoughboyShell` names `SDDL` instead of
`BAL2` and `SD_PanzerShell` (the Panzermensch's and the Schwer's) `SDPL`
instead of `BAL7`, not one tic changed (§5.1, §6.3, "The two enemy shells,
installed by D81"). Every enemy and every enemy projectile draws our own
sprites. **NOT YET SEEN IN THE ENGINE** (D26).
**D116, 2026-10-22: the P4 actors are in the mod on provisional sprites.**
The CEO's art comes from Gemini a little at a time, and no other image
generator (D116); meanwhile the three P4 drafts left their overlays for
`src/`: the Legion gunner `SD_LegionGunner` (21110) and the Liberty Colossus
`SD_LibertyColossus` (21111) of Episode 2, the Consortium `SD_Consortium`
(21112) of Episode 3, and the AKM `SD_Akm` (21008, slot 4's second weapon)
with its own pool `SD_AkmAmmo` (21020, ADR 011). They wear sprites the mod
already ships, tinted in code, and play sounds the mod already ships under
their own logical names (§6.12); **no map places them yet**
(`level-designer`'s). **NOT YET SEEN IN THE ENGINE** (D26).
**D123, 2026-10-23: the gunner, the colossus and the TT-33 drawn; the
colossus's stand-in kept as an enemy.** The CEO approved the Gemini sets
("Ok gunner. Coloso me gustan las 2: colorear general y la estatua de la
libertad. Quiero los 2 en el juego. Ok T33"; "OK, gunner. Colossus: I like
both, the coloured General and the Statue of Liberty. I want both in the
game. OK, T33"): `SD_LegionGunner` wears its
own `SDLG` (70 lumps, `assets/sprites/legion_gunner/`) and
`SD_LibertyColossus` its own `SDLC` (81, `assets/sprites/colossus/`), with
no tint or scale left (§6.12); the TT-33's held and flash frames are the
Gemini set (§6.3, "The TT-33 in hand"), so **no Freedoom pixel is left in
the PK3's art**. The colossus's stand-in look (the General's `SDGN` ×1.3,
tinted chrome) stays as its own enemy, **`SD_ChromeGeneral`, "The Chrome
Marshal"** (21113): the colossus's behaviour and 3000 HP on that look,
MAP08's mini-boss on skills 3-4 where the colossus stood; MAP06 keeps the
statue. **NOT YET SEEN IN THE ENGINE** (D26).
**D128, 2026-10-24: the Consortium, the AKM, the walks and the title
drawn.** The CEO ("Pantalla de inicio CON brazaletes. Logo sin recuadro.
OK AKM y andares. Ok consorcio, añade paleta si es necesario"; "Title
screen WITH armbands. Logo without a frame. OK to the AKM and the walks.
OK, Consortium; add a palette if needed"):
`SD_Consortium` wears its own `SDCN` (95 lumps,
`assets/sprites/consortium/`, no tint or scale left, §6.12), its Reich half
in palette v3's `reich_greygreen` (ART-BIBLE §3: one ramp appended in
reserved slots, no approved asset changed); `SD_Akm` its own `SDAK`,
`SDAF`, `SDAQ` (§6.12; its magazine `SDAM` is still `SDCL` tinted); the
gunner's and the colossus's walk letters A and C are new strides (D127);
`TITLEPIC` is the Gemini painting and `M_DOOM` lost its black plate
(§6.6). **NOT YET SEEN IN THE ENGINE** (D26).
Russian mirror: `docs/ru/engine/MOD-SPEC.md`.

Minimal glossary (for anyone new to Doom modding):

- **IWAD**: the base game data file (`doom2.wad` or `freedoom2.wad`). GZDoom
  does not start without one.
- **PK3**: a `.zip` with a fixed folder layout that GZDoom mounts on top of
  the IWAD. The mod's format.
- **Lump**: a named data block (max 8 ASCII characters). In a PK3 every file
  is a lump named after the file without extension.
- **UDMF**: the text map format (`TEXTMAP`) GZDoom uses; we generate it from
  Python.
- **DoomEdNum**: the number a map editor uses to identify a placeable thing;
  `1` is "Player 1 start".

## 1. Identity

| Field | Value | Note |
|---|---|---|
| Mod name | **Soviet Doom**, package `sovietdoom` | D1, ratified by the CEO 2026-10-09 (`docs/PRD.md` §5) |
| Prefix | `SD` / `SD_` | ZScript classes, LANGUAGE ids, own lumps. **Documented exceptions:** names the engine looks up itself (the shell screens `TITLEPIC`, `INTERPIC`, `M_DOOM`, `M_SKULL1/2`, `M_PAUSE`; the key icons `STKEYS0-2`, D80) and, since D82, the engine actors' sprite overrides `PUFF`, `BLUD`, `TFOG`, `IFOG`, `BAR1`, `BEXP`, `COLU`, shipped under the IWAD's names with exactly Freedoom's lump set (§5.1, §6.3); since M2e-i (D89, D90, D92), the status bar pictures `DoomStatusBar` and its fonts draw by name: `STBAR`, `STARMS`, the 42 faces `STF*`, `STTNUM0-9`, `STTMINUS`, `STTPRCNT`, `STYSNUM0-9`, `STGNUM0-9`, each at Freedoom's size and offsets (§5.1, §6.5). The bar's Russian and Catalan pictures are ours, `SDSBRU`, `SDARRU`, `SDSBCA` and `SDARCA` (§6.5.1, P6) |
| Output file | `dist/sovietdoom.pk3` | generated by `tools/build.py`; never edited by hand |
| Engine | GZDoom 4.14.2, `version "4.12"` in `zscript.txt` | D3, ratified by the CEO 2026-10-09 (`docs/PRD.md` §5) |
| Supported IWADs | `freedoom2.wad` (preferred, D2) and `doom2.wad` | see §5 |

## 2. PK3 layout (output)

```
sovietdoom.pk3
├── MAPINFO                 maps, episodes, skills, GameInfo (AddEventHandlers, PlayerClasses,
│                           StatusBarClass since T24)
├── LANGUAGE                localized text: [enu default] and [ru] (D7)
├── MENUDEF                 language switch, main menu and skill screen in our own type (§6.6)
├── CVARINFO                V3 reloads: `sd_reloads`, the mod's first CVar (§6.15, ADR 014)
├── KEYCONF                 V3 reloads: `defaultbind r +reload` (§6.15)
├── SNDINFO                 logical sound name -> lump (F4)
├── zscript.txt             ZScript entry: version + #include
├── zscript/sd/*.zs         systems (event handlers, player class, ammo, the radio §6.7,
│                           the status bar class §6.5.1, the blue pass §6)
├── zscript/weapons/*.zs    the arsenal, one class per file (F4)
├── zscript/monsters/*.zs   the bestiary, one class per file (F5, BESTIARY.md)
├── maps/MAP01.wad          one WAD per map, lumps MAP01, TEXTMAP, ENDMAP
├── maps/MAP02.wad          the metro-bunker; MAP03.wad the factory (D62)
├── maps/RANGE.wad          the practice range, built as the F4 test range (D41, D62)
├── textures/SD*.png        approved wall textures: SDCONC1-2, SDDOOR1, SDPOSTR1-2, SDSTAR1,
│                           SDSTEL1 and the eight switch faces SDSW1A-D / SDSW2A-D (§4.3)
├── flats/SD*.png           approved flats: SDFLR1-3, SDCEIL1-2
├── graphics/TITLEPIC.png   title screen, 320×200: the Gemini painting, palette v2, armband variant A (D126, D128; D18's "Plakat" retired)
├── graphics/INTERPIC.png   intermission background, 320×200 (D18)
├── graphics/M_DOOM.png     main-menu logo, 200×64, placed by MENUDEF (§6.6); since D128 the lockup without its black plate
├── graphics/M_PAUSE.png    pause sign, plaque P2 in English, 77×20 (D48)
├── graphics/STKEYS0-2.png  the key icons, 7×5 (D80)
├── graphics/STBAR.png, STARMS.png, STF*.png (42), STTNUM0-9, STTMINUS, STTPRCNT,
│                           STYSNUM0-9, STGNUM0-9 (.png): status bar A, the face, digits N2,
│                           under Freedoom's names and sizes (§6.5; from assets/graphics/statusbar/)
├── graphics/SDSBRU.png, SDARRU.png  bar A's Russian pictures, drawn by SD_StatusBar (§6.5.1)
├── graphics/SDSBCA.png, SDARCA.png  bar A's Catalan pictures (P6), idem
├── graphics/SDCURSOR.png   the mouse pointer, hammer and sickle, 28×25, grAb 12,1 (D102; §6.6.1)
├── SDOPSCR                 V3: the intermission script of the operations map (§6.13, ADR 013),
│                           generated into src/lumps/ by tools/art/gen_ops_map.py
├── graphics/SDOPMAP.png, SDOPR02-09, SDOPSTAR, SDOPCUR0-1, SDOPYAH0 (.png)  V3: the operations
│                           map, its arrows and markers (from assets/graphics/opsmap/; §6.13)
├── graphics/SDAWCOU, SDAWRST, SDAWRBN, SDAWPTW, SDAWHER (.png)  V3: the five awards, 24×30
│                           (from assets/graphics/medals/; §6.13; proposal for the CEO)
├── localized/textures/     language variants of graphics, path kept whole:
│                           M_PAUSE.ru.png, plaque P2 in Russian, 77×20 (D48; see the rules)
│                           M_PAUSE.ca.png, plaque P2 in Catalan «PAUSA», 77×20 (P6)
├── fonts/defsmallfont/     <HEX>.png + font.inf — SmallFont glyphs, 107 files (D24)
├── fonts/bigfont/          <HEX>.png + font.inf — BigFont glyphs, 107 files (D24)
├── fonts/sdmenu/           <HEX>.png + font.inf — menu font SDMENU, 107 files (D31, §6.6)
├── music/D_SDINTL.mid       title music, Engelbach's Internationale (D43, §4.5)
├── music/D_SDM1N2.mid       MAP01's music, ours (D95, §4.5)
├── music/D_SDM04A.mid … D_SDE2IB.mid  episode 2's ten pieces, ours (D106, §4.5, §6.11):
│                           A/B of MAP04-06, MAP06's boss loops D_SDBS6A/B, intermission D_SDE2IA/B
├── music/D_SDM07A.mid … D_SDE3IB.mid  episode 3's ten pieces, ours (D113, §4.5, §6.11):
│                           A/B of MAP07-09, MAP09's final boss loops D_SDBS9A/B, intermission D_SDE3IA/B
├── music/D_SDRAD1.mid       diegetic radio: «Эй, ухнем», Gerloff's CC0 sequence (D43, §6.7)
├── music/D_SDRAD2.mid       diegetic radio: «Колокольчик», Gerloff's CC0 sequence (D43, §6.7)
├── sprites/SD*.png          our sprites (D48): the six weapon pickups SDAPA0, SDTPA0, SDIPA0,
│                           SDPQA0, SDRPA0, SDKPA0 (§6.3); everything else is still the IWAD's (§5.1)
├── sounds/SD*.ogg           our sounds: the 25 weapon sounds of D74 (§6.2), from
│                           assets/sounds/weapons/ (N9); the propaganda radio's 20
│                           (SDRAD01-16, SDRADJ1-3, SDRADBED; V3 B5, §6.14) from
│                           assets/sounds/radio/
├── patches/  hires/        standard folders, empty today (T1)
├── ANIMDEFS                switch pairs SDSW1x -> SDSW2x; animations SDMOLT1-4 (flat),
│                           SDPORT1-4 (texture) (§4.3)
└── (future) TEXTURES, GLDEFS — and no CVARINFO, by decision (ADR 004)
```

Rules:
- Root files: name ≤ 8 characters without extension (the build checks and fails otherwise).
- Fonts are **folder fonts**: GZDoom reads `fonts/<fontname>/<HEX>.png`, one
  PNG per code point in upper-case hex (`0410.png` = `А`), plus `font.inf`
  (`FontHeight 9` small, `FontHeight 16` big). `defsmallfont` is the folder
  name the engine's `SmallFont` consults for glyphs it lacks, so our PNGs
  **extend** Freedoom's small font (mechanism verified in-engine
  2026-10-13 with two glyphs, §6.4); `bigfont` is named after `BigFont`
  itself. **NOT VERIFIED**: whether `fonts/bigfont/` replaces or extends
  Freedoom's `BigFont` — the engine loads the package with zero errors and
  the title screen renders (commit 730bba4), but no screenshot of a
  BigFont Cyrillic string has been taken yet. `sdmenu` is a **standalone**
  font: it extends nothing, so it carries every glyph it draws (§6.6).
- Map lumps: `MAP01`, `MAP02`, `MAP03` for the campaign (Doom II format), and
  `RANGE` for the practice range (D62: any lump name of up to 8 characters is
  a map name to GZDoom; its own `mapinfo/doom2.txt` names maps `LEVEL01`…).
  Inside the WAD the order is fixed: marker named after the map (empty),
  `TEXTMAP`, `ENDMAP` (empty). No node lumps:
  GZDoom builds them at load (verified at G0).
- Maps are not extracted: GZDoom reads `maps/MAP01.wad` directly.
- **Language variants of graphics** (D48's pause plaque, D21 for pictures).
  GZDoom g4.14.2 has one mechanism for them, read in its source
  (`FTextureManager::AddLocalizedVariants`, `src/common/textures/texturemanager.cpp`,
  tag `g4.14.2`; **VERIFIED as code, NOT VERIFIED in the engine**):
  - it scans **exactly** `localized/textures/` (no other folder, no
    `filter/` variant) and splits each file name on `.`;
  - the first token is the **base** graphic (`M_PAUSE`), looked up as a
    MiscPatch, so `graphics/M_PAUSE.png` qualifies; the second is one or
    more **language IDs** of 2 or 3 letters joined by `-` (`ru`, `ru-uk`);
    `M_PAUSE.png` with no ID is ignored. The name we ship:
    **`localized/textures/M_PAUSE.ru.png`** (case is irrelevant: the engine
    lower-cases every PK3 path);
  - a variant whose size differs from its base's is refused ("Localized
    texture %s must be the same size as the one it replaces"); every
    refusal is a console line, never a load error, which is why
    `check_pk3` (category `localized`) turns each into an error offline;
  - **but in g4.14.2 nothing draws the variant.** The substitution line in
    `FTextureManager::ResolveTextureIndex` (`texturemanager.h`, line 32) is
    commented out, and the variant table is consulted only by
    `OkForLocalization`, which decides whether a menu graphic yields to
    text. The pause sign itself is drawn by `D_Display` (`src/d_main.cpp`,
    line 1110) with `GetGameTextureByName(gameinfo.PauseSign)`, which does
    no localization. So the Russian plaque packs and validates, and the
    game would still show the English one in Russian. **The mod therefore
    draws the pause sign itself** through the status bar's `DrawPaused`
    virtual (`gzdoom.pk3:zscript/ui/statusbar/statusbar.zs`, line 239;
    `D_Display` calls it first and skips its own drawing if it returns
    true): `SD_StatusBar`, §6.5.1, ADR 010. It names the variant by its
    **full path**, which `TexMan.CheckForTexture` resolves through the
    file system (`texturemanager.cpp`, the `strchr(name, '/')` branch), so
    the variant table's being unused does not matter. Any other
    `localized/` graphic would need the same treatment by whatever draws it.
  - The variant's licence row is its base's (`M_PAUSE`) or its own. It is
    kept out of `check_pk3.LICENSED_DIRS` (which matches by stem), and
    `check_pk3` category `localized` checks the row. Since T24
    `tools/release.py` adds `localized/` to the folders it credits and
    matches a variant by its base name too, so the shipped zip's licence
    check covers it.

## 3. `src/` layout (build input)

```
src/
├── lumps/        → PK3 root (flat: MAPINFO, LANGUAGE, MENUDEF, SNDINFO, ANIMDEFS, zscript.txt)
├── zscript/      → zscript/  (copied as is; sd/ = systems, weapons/ = arsenal, monsters/ = bestiary)
├── maps/MAP01/map.py   → maps/MAP01.wad  (generated; defines lumps())
├── maps/MAPxx.wad      → maps/MAPxx.wad  (copied as is; UDB output)
└── textures/ flats/ sprites/ sounds/ music/ graphics/ patches/ hires/ fonts/ → same paths

assets/   (CEO-approved art only; `work/` is gitignored and never ships)
├── <folder>/<set>/NAME.png → <folder>/NAME.png   the set folder is DROPPED
│     e.g. assets/textures/soviet_base/SDCONC1.png → textures/SDCONC1.png
│          assets/graphics/shell/TITLEPIC.png      → graphics/TITLEPIC.png
│          assets/sprites/tt33/SDTPA0.png          → sprites/SDTPA0.png   (the set is the weapon)
├── fonts/<fontname>/*      → fonts/<fontname>/*   kept whole: the folder IS the font
└── localized/**            → localized/**         kept whole: the path IS the contract (§2)
      e.g. assets/localized/textures/M_PAUSE.ru.png → localized/textures/M_PAUSE.ru.png
```

- **The asset mapping** (`tools/build.py`, packer `tools/sdbuild/pk3.py`,
  `collect_assets`). For every standard folder (`textures`, `flats`,
  `sprites`, `sounds`, `music`, `graphics`, `patches`, `hires`, `fonts`) a
  file at `assets/<folder>/<set>/NAME.png` is packed as `<folder>/NAME.png`:
  the set (`soviet_base`, `shell`) is a review-time grouping, and GZDoom
  names a lump after the file, so the set is dropped on the way in and the
  map's `SDCONC1` resolves. `fonts/` is the one exception
  (`NESTED_ASSET_DIRS`): `assets/fonts/<fontname>/…` keeps its path because
  the subfolder name is the font (D24). `src/<folder>/` is packed at the
  same paths; a path produced twice — from `src/` and `assets/`, or by two
  sets sharing a file name — fails the build (`duplicate PK3 path`). This
  mapping was blocker **M1** (2026-10-12): approved art sat in `assets/`
  and never reached the PK3, so every map referencing it died with
  `Unknown texture`. `tests/test_build.py` and `tools/check_pk3.py` hold it.
- Editor leftovers in `src/lumps/` (`.bak`, `.orig`, `.rej`, `.tmp`,
  `.swp`, `~`, dotfiles) are skipped, as are `.DS_Store`, `Thumbs.db` and
  `__pycache__` anywhere: a `MAPINFO.bak` would otherwise become a second
  `MAPINFO` lump (seen 2026-10-13).

- A generated map (`map.py`) exposes `lumps() -> list[(name, bytes)]`, first
  lump being the marker named after the folder. It imports `sdbuild.udmf` to
  build the `TEXTMAP` (`tools/sdbuild/udmf.py`).
- `level-designer` may deliver a `.wad` made in Ultimate Doom Builder under
  `src/maps/`; the build packs it untouched. File name = map name.
- The build is deterministic (fixed timestamps, sorted entries): same sources
  give identical bytes (tested).

## 4. Maps

| Lump | Title (LANGUAGE) | Episode | Status |
|---|---|---|---|
| `MAP01` | `SD_MAP01_NAME` = "Zarya-7 Cosmodrome" / «Космодром "Заря-7"» | `SD_EP01_NAME` = "Soviet Doom" / "Советский Doom" | Owned by `level-designer` since F3; design in `docs/levels/MAP01-zarya-7.md`. `cluster = 3`, `next = "MAP02"`, `par = 210` (§4.6; `next = "MAP03"` from D60 to D62, `cluster = 1`, `next = endtitle` before D60). Named in-engine 2026-10-13 (the log prints `MAP01 - Zarya-7 Cosmodrome`). |
| `MAP02` (`MAP03` until D62) | `SD_MAP02_NAME` = "Metro-Bunker" / «Метро-бункер» (working title, `docs/levels/MAP02-metro.md` §13) | `SD_EP01_NAME`, the campaign's second map | Owned by `level-designer`; design in `docs/levels/MAP02-metro.md`. `cluster = 4`, `next = "MAP03"`, `music = ""`, `par = 300` (§4.6): its exit leads to the factory through cluster 4's transition text. |
| `MAP03` (`MAP04` until D62) | `SD_MAP03_NAME` = "Tankograd" / «Танкоград» (D63) | `SD_EP01_NAME`, the campaign's third and last map | Owned by `level-designer`; design in `docs/levels/MAP03-factory.md` (v0, the grey box). `cluster = 1`, `next = EndSequence, "SD_Ending1"` (`endtitle` until V3 B2, §6.16), `music = ""`, `par = 360` (`level-designer`'s figure, design §11): its exit, the breaker that feeds the portal, ends the episode (§4.6). |
| `MAP04` (D104, P4) | `SD_MAP04_NAME` = "Trans-Siberian" / «Транссиб» / «Transsiberià» | `SD_EP03_NAME` = "The Road to Moscow" / «Дорога на Москву» / «El camí de Moscou», episode 2's first map | Owned by `level-designer` (`src/maps/MAP04/`): the Trans-Siberian marshalling yard at Sverdlovsk, the armoured train, the signal box, the locomotive roundhouse; left west on the armoured train. `cluster = 5`, `next = "MAP05"`, `music = "D_SDM04A"` (D106, §4.5), `par = 300` (the mod-engineer's placeholder) (§4.6). |
| `MAP05` (D104) | `SD_MAP05_NAME` = "Volga Dam" / «Волжская ГЭС» / «La presa del Volga» | `SD_EP03_NAME`, episode 2's second map | Owned by `level-designer` (`src/maps/MAP05/`): the hydroelectric dam at Zhiguli, the turbine hall, the spillway, the control room; left over the crest of the dam. `cluster = 6`, `next = "MAP06"`, `music = "D_SDM05A"` (D106), `par = 330` (placeholder). |
| `MAP06` (D104) | `SD_MAP06_NAME` = "Red Square" / «Красная площадь» / «La plaça Roja» | `SD_EP03_NAME`, episode 2's third and last map | Owned by `level-designer` (`src/maps/MAP06/`): Moscow, out of the metro at Ploshchad Revolyutsii, the GUM galleries, Red Square, the gate in the Kremlin wall, the boss arena. `cluster = 7`, `next = EndSequence, "SD_Ending2"` (§6.16), `music = "D_SDM06A"` (D106), `par = 420` (placeholder): its exit ends episode 2 (§4.6). |
| `MAP07` (D112, P4) | `SD_MAP07_NAME` = "Novaya Zemlya" / «Новая Земля» / «Nova Zembla» | `SD_EP04_NAME` = "The Portal" / «Портал» / «El portal», episode 3's first map | Owned by `level-designer` (`src/maps/MAP07/`): the Arctic radar station on Novaya Zemlya, the radomes, the barracks, the nuclear test site; the invaders use it to guide something in. `cluster = 8`, `next = "MAP08"`, `music = "D_SDM04B"`, `intermusic = "D_SDE2IB"` (both provisional, §4.5), `par = 330` (placeholder) (§4.6). |
| `MAP08` (D112) | `SD_MAP08_NAME` = "Severomorsk" / «Североморск» / «Severomorsk» | `SD_EP04_NAME`, episode 3's second map | Owned by `level-designer` (`src/maps/MAP08/`): the Northern Fleet's submarine base at Severomorsk, the covered docks, a nuclear submarine, the cranes, the tunnels in the rock. `cluster = 9`, `next = "MAP09"`, `music = "D_SDM05B"`, `intermusic = "D_SDE2IB"` (provisional), `par = 360` (placeholder). |
| `MAP09` (D112) | `SD_MAP09_NAME` = "Tunguska" / «Тунгуска» / «Tunguska» | `SD_EP04_NAME`, episode 3's third and last map | Owned by `level-designer` (`src/maps/MAP09/`): the invaders' main portal at Tunguska, the taiga flattened in 1908, an alien-industrial complex eating the forest, the portal, the final boss arena. `cluster = 10`, `next = EndSequence, "SD_Ending3"` (§6.16), `music = "D_SDM06B"` (provisional), `par = 480` (placeholder): its exit ends episode 3 and the first cycle (§4.6). |
| `RANGE` (`MAP02` until D62) | `SD_RANGE_NAME` = "Training Ground" / «Учебный полигон» (D46, 2026-10-14; was "Engineering Test Range" / "Инженерный полигон"; the id was `SD_MAP02_NAME` until D62) | `SD_EP02_NAME` = "Practice Range" / «Полигон» (D41, §4.4) | `cluster = 2`, `next = endtitle`, `nointermission`. F4: 2048×768 hall, ceiling 128, light 192, player start at (160,384) facing +x. The seven weapons, the four ammo pools, barrels and six targets (thing 3004, Soviet riflemen since F5). **F5: the bestiary gallery**, a second room 2048×768 at y 1024–1792, ceiling 192, light 192: one of each of the eight enemy classes in a row at y = 1600, deaf (`ambush`) and facing north, away from the arrival spot. Since D41 the player reaches the map from New Game (§4.4); `MAP=RANGE tools/run.sh` starts it (D62). **Since commit `d1e891f` (2026-10-13), v1 for players:** an `Exit_Normal` switch (`SDSW1D`) in a lit alcove straight behind the start, and the gallery reached on foot through a manual door (tag 1) in the hall's north wall and a bent passage that comes out behind the row; the console's `warp 1024 1152` still lands there. Geometry and reasons are `level-designer`'s, `docs/levels/RANGE-practice-range.md`. Built as an engineering fixture; shipped as the practice range. |

MAPINFO conventions: `clearepisodes` + one episode per campaign episode
(two since D104, three since D112, §4.6) plus the practice range (§4.4); **the MAPxx slots follow the campaign's order (D62)**
and a map outside the campaign takes a lump name that is not MAPxx (`RANGE`);
map titles by `lookup`, episode title by `name = "$ID"` (**`lookup` is not accepted inside an
episode block**, verified B1); every map and cluster names its music, and
`music = ""` where there is none (verified: silence, no warning; §4.5);
`sky1 = "SKY1"` (Freedoom's) on MAP02 only (the metro has no sky sector);
since D113 (2026-10-22) MAP01 and RANGE `sky1 = "SDSKY6"`, MAP03 `"SDSKY7"`,
MAP04 and MAP05 `"SDSKY1"`, MAP06 `"SDSKY2"`, MAP07-09 `"SDSKY3"`-`"SDSKY5"`: our own night skies,
1024×128 (one 360° turn), packed under `textures/` and declared in
`check_pk3`'s `SKY_TEXTURES`. How the engine maps a 1024-wide sky (its
stretch and where the horizon row falls) is NOT VERIFIED until the PM's
engine pass (D26).

### 4.4 The practice range (D41, 2026-10-13)

> Order note: §4.4, §4.5 and §4.6 come before §4.1 because they were added later;
> the sections are not renumbered, since other documents cite them by number.

The CEO: "Se puede publicar como práctica" ("it can be released as practice"). The range (MAP02 then, the lump
**`RANGE`** since D62) ships in v1 **outside the campaign**, and the player
reaches it from the New Game screen. The choice
between the ways of reaching it is ADR 007
(`docs/engine/adr/007-practice-range-as-a-second-episode.md`); the contract:

| What | Value |
|---|---|
| Episodes (`MAPINFO`, in this order) | `episode MAP01` name `$SD_EP01_NAME`, key `s`; **`episode MAP04` name `$SD_EP03_NAME`, key `m`** (D104, P4: episode 2, "The Road to Moscow"; the `03` is the order the episodes were declared in, the range having taken `02` in D41); `episode RANGE` name `$SD_EP02_NAME`, key `p` (`episode MAP02` until D62). **`episode MAP07` name `$SD_EP04_NAME`, key `t`** (D112, P4: episode 3, "The Portal" / «Портал» / «El portal»; `04`, the fourth declared), after episode 2. The order of the blocks is the order of the screen: the campaign's three episodes, then the range |
| The range's lump (D62) | **`RANGE`**: out of the MAPxx slots, which follow the campaign. A non-MAPxx map is plain MAPINFO: GZDoom g4.14.2's own `mapinfo/doom2bfg.txt` opens its second episode with `episode level01` on the maps `LEVEL01`–`LEVEL09` of `mapinfo/doom2.txt` (read in the installed `gzdoom.pk3`, 2026-10-14). The build and `check_pk3` take any lump name of up to 8 characters (`validate_lump_name`, `lump_name_problem`); `tools/verify.py` finds map folders by that rule since D62. Such a map has no level number, which only `Teleport_NewMap` and `-warp` use; neither reaches the range. **NOT VERIFIED in the engine** until the PM's C6-C7 (§4.6) |
| Episode names | `SD_EP02_NAME` = "Practice Range" / «Полигон». The map title under it is `SD_RANGE_NAME` = "Training Ground" / «Учебный полигон» since D46 (§4; the id was `SD_MAP02_NAME` until D62); the episode name stays (see the note below the table) |
| Flow | Main menu → New Game → **episode screen** (new: with one episode the engine skipped it) → skill screen → the map |
| Episode screen (`MENUDEF`) | `LISTMENU "EpisodeMenu"` redeclared like the skill screen (§6.6): logo `M_DOOM` at 60,0, one `SDMENU` header `$SD_MNU_CHOOSEEPISODE` at 32,70 ("CHOOSE MISSION" / «ВЫБЕРИТЕ ЗАДАНИЕ»), then `SmallFont` for the episode names, which the engine appends at run time. **`M_EPISOD` is never drawn** (T12) |
| MAP01's exit | `next = endtitle` until D60; `next = "MAP03"` (the metro's slot then) until D62; since D62 `next = "MAP02"`, the metro, and MAP03's exit ends the campaign (§4.6). In every version **no map's `next` is the range** |
| The range's exit | `cluster = 2`, `next = endtitle`: leaving the range shows `SD_END02_TEXT` ("The range is closed…" / «Полигон закрыт…») over `SDFLR1`, then the title screen. `nointermission` stays: a range has no score worth a stats screen. The player leaves by **the exit switch behind the start** (`Exit_Normal`, pressed; commit `d1e891f`, `docs/levels/RANGE-practice-range.md` §4.1). **Seen in the engine** 2026-10-13: pressing it shows `SD_END02_TEXT` over `SDFLR1` (P6 in `docs/qa/evidence/2026-10-13_2057_map02-range-and-c12.md`). The `range-start` route of `tools/route.py` (`map02-start` until D62; since route-3) presses that same switch, as a player does (`docs/qa/evidence/2026-10-13_2114_F3_g3-map02-map02-start-*`); `netevent sdexit` of the route helper (`Level.ExitLevel`) is only a documented recourse for a map with no exit line, used by no built-in route. **The console `exit` command does not reach it: it quits GZDoom** (G3-F2) |
| Cluster 2 | `exittext = lookup, "SD_END02_TEXT"`, `flat = "SDFLR1"`, `music = ""` |

**The episode name next to the map name (D46, checked 2026-10-14).** The
player reads "Practice Range" / «Полигон» on the episode screen and
"Training Ground" / «Учебный полигон» on the automap and the level-load
line. In English the two are different words for the same place, the
general and the particular, and `SD_END02_TEXT` ("The range is
closed…") still fits. In Russian the map name contains the episode name
(«Полигон» → «Учебный полигон»): an echo, not a contradiction; the map
name narrows the episode name, and `SD_END02_TEXT` («Полигон на сегодня
закрыт») agrees with both.
**Kept as is.** An alternative, not applied and the CEO's to take if he
dislikes the echo: episode «Стрельбище» (the literal "shooting range",
closer to "Practice Range"), which would also need `SD_END02_TEXT` [ru] to
say «Стрельбище на сегодня закрыто» — two `LANGUAGE` lines, nothing else.

Engine facts this rests on, read in GZDoom g4.14.2 (`gzdoom.pk3 →
menudef.txt`, `ListMenu "EpisodeMenu"`, and the episode-menu builder in the
engine source, `M_StartupEpisodeMenu`, not a file of this repo): the menu
lists one item per MAPINFO `episode` in the descriptor's **last** `Font`,
starting at its `Position`, below any static items; an episode with no
`picname` gets a text item; with exactly one episode the item is
autoselected and the screen never shows, which is why `M_EPISOD` never
appeared until now. The engine's own body also sets `NetgameMessage
"$NEWGAME"` (New Game refused in a net game); ours keeps it.

**Engine pass, done 2026-10-13** (the PM; D26):

- **The screen as drawn, in both languages, and the Russian names in
  `SmallFont`: VERIFIED** (20:39, `openmenu EpisodeMenu`, frames 2 and 3 of
  `docs/qa/evidence/2026-10-13_2039_ice-axe-and-episode-menu.png`; notes
  in `…_2039_d40-d43-engine-pass.md`): our logo, the `SDMENU` header and
  the two episodes, no `M_EPISOD`. That pass opened the menu from the
  console; it did not walk New Game → episode → skill.
- **That `nointermission` still shows cluster 2's text: VERIFIED** (20:57,
  P6 of `docs/qa/evidence/2026-10-13_2057_map02-range-and-c12.md`):
  the range's exit switch shows `SD_END02_TEXT` over `SDFLR1`. The route
  helper's `sdexit` reached it too (20:52, `…_2052_F3_g3-map02-*`, an earlier run; since route-3 `map02-start`, `range-start` since D62, presses the real exit switch and `sdexit` stays a documented recourse in `tools/route.py`).

**The range for players (commit `d1e891f`, 2026-10-13; MAP02 then).** D41 left two gaps to
`level-designer`, and both are closed: the range has an exit switch behind the
start, and the bestiary gallery is reached on foot, through a door (tag 1,
`Door_Raise` on both faces) and a bent passage that keeps the hall's
gunfire from waking it. Design: `docs/levels/RANGE-practice-range.md` §4.
Seen in the engine the same evening (P1-P3, P5, P6 of the 20:57 evidence);
**P4, the door opened from the passage side, is NOT VERIFIED in the
engine** (the map's tests pin both faces statically). Nothing in this
contract changed for it: MAPINFO, the cluster and the episode are as
above (D62 changed the lump's name only).

### 4.5 Music (D43, 2026-10-13)

The CEO accepted every music recommendation of `docs/sound/SOUNDTRACK.md`
§8 (D43); `sound-designer` installed the first two lumps in `assets/music/`
(commit `d89f99e`, rights in `docs/sound/MUSIC-RIGHTS.md`, rows in
`docs/art/LICENSES.md`), and the build packs them as `music/<LUMP>.mid`
(the asset mapping, §3). `MAPINFO` names them; `SNDINFO` is not involved
(music lumps are not sounds).

| Where | `MAPINFO` key | Lump |
|---|---|---|
| Title screen | `GameInfo { TitleMusic = "D_SDINTL" }` | `D_SDINTL`, the Internationale (Engelbach's sequence, credited) |
| Intermission (the stats screen between maps) | `GameInfo { IntermissionMusic = "D_SDTITL" }` (since N9e, D83) | `D_SDTITL`, "Zarya", ours; overrides gzdoom.pk3's `intermissionmusic = "$MUSIC_DM2INT"` (`mapinfo/doomcommon.txt`), Freedoom's `D_DM2INT` |
| MAP01, Zarya-7 | `map MAP01 { music = "D_SDM1N2" }` (since N9e, D95) | `D_SDM1N2`, ours, composed for MAP01 under D92 (`tools/audio/compose_map01.py`, variant `D_SDM01N2`); `D_SDM01` (D43) left MAP01 by D83 and no longer ships |
| MAP02, metro-bunker | `music = "D_SDFUNR"` (D62) | `D_SDFUNR`, ours (approved D83) |
| MAP03, Tankograd | `music = "D_SDGATE"` (D62) | `D_SDGATE`, ours (approved D83) |
| MAP04, Trans-Siberian (D104) | `music = "D_SDM04A"`, `intermusic = "D_SDE2IA"` (D106) | `D_SDM04A`, ours (`tools/audio/compose_episode2.py`); its B `D_SDM04B` is drawn at random by `SD_MusicVariant` (§6.11). The stats screen after MAP04 plays `D_SDE2IA` |
| MAP05, Volga Dam (D104) | `music = "D_SDM05A"`, `intermusic = "D_SDE2IA"` (D106) | `D_SDM05A`, ours; B `D_SDM05B` (§6.11); stats screen `D_SDE2IA` |
| MAP06, Red Square (D104) | `music = "D_SDM06A"` (D106) | `D_SDM06A`, ours; B `D_SDM06B`; the boss loop `D_SDBS6A` / `D_SDBS6B` (§6.11). Its stats screen keeps `D_SDTITL` |
| MAP07, Novaya Zemlya (D112) | `music = "D_SDM07A"`, `intermusic = "D_SDE3IA"` (D113) | `D_SDM07A`, ours (`tools/audio/compose_episode3.py`); B `D_SDM07B` (§6.11). The stats screen after MAP07 plays `D_SDE3IA`. Replaces D112's provisional `D_SDM04B` / `D_SDE2IB` |
| MAP08, Severomorsk (D112) | `music = "D_SDM08A"`, `intermusic = "D_SDE3IA"` (D113) | `D_SDM08A`, ours; B `D_SDM08B` (§6.11); stats screen `D_SDE3IA` |
| MAP09, Tunguska (D112) | `music = "D_SDM09A"` (D113) | `D_SDM09A`, ours; B `D_SDM09B`; the final boss loop `D_SDBS9A` / `D_SDBS9B` (§6.11). Its stats screen keeps `D_SDTITL` |
| RANGE, practice range | `music = "D_SDM01T"` (since N9e, D86) | `D_SDM01T`, MAP01's theme `D_SDM01E` cut to its melodic part (bar 49); `D_SDAMUR` (D62) was rejected by D83 and no longer ships |
| Clusters 1 to 10 (end and transition texts, §4.6) | `music = ""` | none |
| A diegetic radio (§6.7) | **none**: `SD_Radio` swaps the music from ZScript while the player is near it | `D_SDRAD1`, `D_SDRAD2` |
| Episodes 2 and 3's B pieces and the boss loops of MAP06 and MAP09 (§6.11) | **none**: `SD_MusicVariant` swaps them in from ZScript (D113 ended D112's provisional use of episode 2's B pieces on MAP07-09) | `D_SDM04B`, `D_SDM05B`, `D_SDM06B`, `D_SDBS6A`, `D_SDBS6B`, `D_SDM07B`, `D_SDM08B`, `D_SDM09B`, `D_SDBS9A`, `D_SDBS9B` |
| Each episode's intermission, variant B | **none**: packed, not wired (the stats screen's music is MAPINFO's, §6.11) | `D_SDE2IB`, `D_SDE3IB` |

**`intermusic`, per map (D106).** The stats screen asks the level being LEFT
for its music: `FLevelLocals::SetInterMusic` (gzdoom g4.14.2
src/g_level.cpp 2318-2327, called by `StatusScreen.StartMusic`,
`gzdoom.pk3:zscript/ui/statscreen/statscreen.zs` 827-831) plays the map's
`mapintermusic` for the next map if any, else its `intermusic`, else
GameInfo's `IntermissionMusic`. So MAP04's and MAP05's `intermusic =
"D_SDE2IA"` gives episode 2 its own stats-screen music, MAP07's and MAP08's
`"D_SDE3IA"` episode 3 its own (D113), and every other map keeps
`D_SDTITL`. The key is parsed by `DEFINE_MAP_OPTION(intermusic)`
(src/gamedata/g_mapinfo.cpp 1166-1170).

Rule: every `music` / `intermusic` / `TitleMusic` / `IntermissionMusic` value is `""` or a lump packed under
`music/` (`tests/test_mapinfo_music.py`, and `tests/test_enemy_sfx_install.py`
for N9e's two); a typo plays nothing and logs
nothing, which is why it is a test and not an engine-pass finding.
`TitleMusic` in the mod's `GameInfo` overrides the IWAD's (`D_DM2TTL` on
Freedoom), by the same block-merge that already carries `PlayerClasses`.
**Engine pass, 2026-10-13** (the PM,
`docs/qa/evidence/2026-10-13_2039_d40-d43-engine-pass.md`): **VERIFIED**
that `currentmusic` reports `D_SDM01` in MAP01 and no music in MAP02 (the
range, `RANGE` since D62).
**VERIFIED at 21:50 the same day**: the title screen plays `D_SDINTL`
(`currentmusic`, `docs/qa/evidence/2026-10-13_2150_F6_title-music.log`).
**Still NOT VERIFIED:** that the title music carries on into the main menu
as Doom's does; and (N9e, 2026-10-20) that the stats screen after MAP01
plays `D_SDTITL`, MAP01 `D_SDM1N2` and the range `D_SDM01T` (`currentmusic`, the PM's pass);
and (D106) that MAP04-06 play their A or B, the stats screens after MAP04
and MAP05 `D_SDE2IA`, and MAP06's boss its loop (§6.11); and (D113) that
MAP07-09 play their A or B, the stats screens after MAP07 and MAP08
`D_SDE3IA`, and MAP09's boss its loop (§6.11). D113's ten pieces were
approved unheard, so that pass is also the first listening.

### 4.6 The campaign's flow: MAP01 → MAP02 → MAP03, MAP04 → MAP05 → MAP06, MAP07 → MAP08 → MAP09 (D60, D62, D104, D112)

D60 amended D5: the campaign grew past MAP01. **D62 renumbered the slots to
follow it** ("para no confundir con los nombres", "so as not to mix up the names"): MAP01 Zarya-7, **MAP02 the
metro-bunker** (built as MAP03), **MAP03 the factory, «Танкоград» /
Tankograd** (built as MAP04, named by D63), and the practice range left the
MAPxx sequence for the lump `RANGE` (§4.4). The source folders, tests and
design documents moved with `git mv`; dated evidence keeps its old names (a
`map03` in an evidence file name is the metro, a `map02` the range). What
`MAPINFO` says and what the player sees:

| Map | `cluster` | `next` | Leaving it shows |
|---|---|---|---|
| `MAP01` | 3 | `"MAP02"` | the stats screen, then cluster 3's `SD_MAP01_EXIT_TEXT` over `SDFLR1`, then MAP02 |
| `MAP02` | 4 | `"MAP03"` | the stats screen, then cluster 4's `SD_MAP02_EXIT_TEXT` over `SDFLR1`, then MAP03 |
| `MAP03` | 1 | `EndSequence, "SD_Ending1"` (V3 B2; `endtitle` until then) | the stats screen, the awards page (§6.13), then cluster 1's `SD_END01_TEXT` over `SDFLR1`, then the illustration `SDEND1` (§6.16), then the title screen |
| `RANGE` | 2 | `endtitle` | unchanged (§4.4): no stats (`nointermission`), cluster 2's `SD_END02_TEXT`, the title screen |
| `MAP04` (D104) | 5 | `"MAP05"` | the stats screen, then cluster 5's `SD_MAP04_EXIT_TEXT` over `SDFLR1`, then MAP05 |
| `MAP05` (D104) | 6 | `"MAP06"` | the stats screen, then cluster 6's `SD_MAP05_EXIT_TEXT` over `SDFLR1`, then MAP06 |
| `MAP06` (D104) | 7 | `EndSequence, "SD_Ending2"` (V3 B2) | the stats screen, the awards page, then cluster 7's `SD_END03_TEXT` over `SDFLR1`, then `SDEND2` (§6.16), then the title screen |
| `MAP07` (D112) | 8 | `"MAP08"` | the stats screen, then cluster 8's `SD_MAP07_EXIT_TEXT` over `SDFLR1`, then MAP08 |
| `MAP08` (D112) | 9 | `"MAP09"` | the stats screen, then cluster 9's `SD_MAP08_EXIT_TEXT` over `SDFLR1`, then MAP09 |
| `MAP09` (D112) | 10 | `EndSequence, "SD_Ending3"` (V3 B2) | the stats screen, the awards page, then cluster 10's `SD_END04_TEXT` over `SDFLR1`, then `SDEND3` (§6.16), then the title screen |

| Cluster | `exittext` | Holds | Role |
|---|---|---|---|
| 1 | `lookup, "SD_END01_TEXT"` | MAP03 | the campaign's ending; always the campaign's **last** map |
| 2 | `lookup, "SD_END02_TEXT"` | RANGE | the range's ending |
| 3 | `lookup, "SD_MAP01_EXIT_TEXT"` | MAP01 | MAP01's chapter: the lift down into the metro |
| 4 | `lookup, "SD_MAP02_EXIT_TEXT"` | MAP02 | MAP02's chapter: out of the westbound tunnel at the tractor works |
| 5 | `lookup, "SD_MAP04_EXIT_TEXT"` | MAP04 | MAP04's chapter (D104): the armoured train west from Sverdlovsk to the Volga dam |
| 6 | `lookup, "SD_MAP05_EXIT_TEXT"` | MAP05 | MAP05's chapter (D104): over the crest of the dam, the last metro train into Moscow |
| 7 | `lookup, "SD_END03_TEXT"` | MAP06 | episode 2's ending (D104): the Kremlin holds, the invaders' main portal is still open |
| 8 | `lookup, "SD_MAP07_EXIT_TEXT"` | MAP07 | MAP07's chapter (D112): the radar on Novaya Zemlya goes dark; its log points to Severomorsk, across the Barents Sea |
| 9 | `lookup, "SD_MAP08_EXIT_TEXT"` | MAP08 | MAP08's chapter (D112): the submarine's warheads were bound for Tunguska; a night flight east |
| 10 | `lookup, "SD_END04_TEXT"` | MAP09 | episode 3's ending (D112): the main portal closes, the end of the first cycle; closes on TO BE CONTINUED / ПРОДОЛЖЕНИЕ СЛЕДУЕТ / CONTINUARÀ (D117; THE END until then) |

All ten: `flat = "SDFLR1"`, `music = ""`, no `entertext`.

**Why each map has its own cluster.** A cluster's text is printed only when
the game crosses from one cluster into another: `exittext` is "displayed
when leaving the cluster" (ZDoom wiki, MAPINFO/Cluster definition), and Doom
II's MAP01–MAP06 share one cluster and print nothing between them. Two
campaign maps in one cluster would therefore have **no** text between them.
Each transition needs a cluster boundary, and the ending needs to stay where
the campaign ends. The rule, so that the next map is mechanical:

- **cluster 1 is the campaign's ending and always holds its last map;**
  cluster 2 is the range's ending. Clusters 1 and 2 then match the episodes
  (`SD_EP01_NAME` / `SD_EP02_NAME`) and their endings (`SD_END01_TEXT` /
  `SD_END02_TEXT`): the `01` and `02` of those ids are **episode** numbers,
  not map numbers;
- every earlier campaign map gets its own chapter cluster, numbered from 3
  upward in play order, whose `exittext` is `SD_MAPnn_EXIT_TEXT`, the way
  into the next map;
- **D104 (P4) did not grow episode 1; it opened episode 2.** Episode 1
  stays MAP01 → MAP03 and cluster 1 stays its ending. Episode 2, "The Road
  to Moscow", is MAP04 → MAP05 → MAP06, a separate chain started from its
  own `episode MAP04` block: nothing leads into MAP04, and MAP03 still says
  `endtitle`. Its chapters continue the numbering (cluster 5 = MAP04's,
  6 = MAP05's) and its ending is cluster 7, MAP06's alone, with
  `SD_END03_TEXT` (the `03` of the episode ids, `SD_EP03_NAME`, is the order
  the episodes were declared in, not their place on the menu). A later
  episode follows the same pattern: its maps on the next MAPxx slots, one
  chapter cluster per map before its last, numbered on, and one ending
  cluster;
- **D112 (P4) opened episode 3 that way.** "The Portal" is MAP07 → MAP08 →
  MAP09, started from its own `episode MAP07` block (after episode 2's on
  the menu, before the range); nothing leads into MAP07 and MAP06 still
  says `endtitle`. Its chapters are clusters 8 (MAP07's) and 9 (MAP08's),
  its ending cluster 10, MAP09's alone, with `SD_END04_TEXT`
  (`SD_EP04_NAME`: the fourth episode declared). From episode 2 on, each
  episode takes the next numbers, its chapters and then its ending
  (`tests/test_campaign.py`, `expected_cluster_numbers`);
- the MAPxx slots stay in play order (D62); a map outside the campaign takes
  a non-MAPxx lump name, as `RANGE` does.

**The ending prints once.** Only cluster 1 carries `SD_END01_TEXT` and only
MAP03 is in it (and only cluster 7 `SD_END03_TEXT`, with MAP06 alone in it, and only cluster 10 `SD_END04_TEXT`, with MAP09 alone), so leaving MAP01 or MAP02 prints its own transition and
never the ending. No cluster has an `entertext`: GZDoom would show the next
cluster's `entertext` in place of the current one's `exittext` (read in the
engine source, `G_WorldDone`; **NOT VERIFIED in the engine**), and two texts
competing for one crossing is how an ending gets printed in the wrong place.

**The words.** `SD_MAP01_EXIT_TEXT` (D60) takes the service lift at the end
of MAP01 down into the metro (MAP01 §2, MAP02 §1). `SD_MAP02_EXIT_TEXT` (D62)
is new: out of the metro's westbound tunnel at the factory's goods spur,
from `level-designer`'s draft (`docs/levels/MAP03-factory.md` §11) with the
map's name added ("The workers have a name for it: Tankograd.").
`SD_END01_TEXT` is **rewritten** for the factory: it closed MAP01 until D60
("The gantry lights go out behind you…") and the bunker until D62 ("The
bunker lights go out behind you…"); it now tells the portal's fall at the
breaker that feeds it ("The breaker drops. Behind you the portal shrinks to
a point of light and goes out."), keeps the old frame (a light out behind
you, the place yours again, the invasion moving west, to Moscow) and keeps
the last line, TO BE CONTINUED / ПРОДОЛЖЕНИЕ СЛЕДУЕТ. All three are
**broken into lines by hand**, every line within 300 px of `SmallFont`
(Doom draws the text from x 10 on a 320-wide screen): whether GZDoom's text
screen wraps a long line on its own is **NOT VERIFIED**, and hand-broken
lines read the same either way (`tests/test_campaign.py`). The Russian is
the mod-engineer's and waits on `translator-ru`'s review when the delivery
has passed the pipeline (D60).

**`tools/route.py`.** Its routes find their maps by the named constants of
each `map.py` and read where each exit leads from `MAPINFO`, so D62 moved
nothing in their logic: `g3-auto` expects MAP01 to lead to MAP02, and the
metro's route expects MAP02 to lead to MAP03 (no longer an end sequence).
The route **names** follow the maps: `range-start`, `range-door` and
`metro-critical` were `map02-start`, `map02-door` and `map03-critical`
(`tests/test_route.py`). The factory has no route yet.

**Engine checks for the PM (D26), NOT VERIFIED until then:**

| # | Do | Expect |
|---|---|---|
| C1 | New Game → Soviet Doom → any skill; finish MAP01 by its exit switch | the stats screen titled "Zarya-7 Cosmodrome", then `SD_MAP01_EXIT_TEXT` typing out over `SDFLR1`, then MAP02 loads ("MAP02 - Metro-Bunker" in the log) |
| C2 | finish MAP02 by its exit switch (or `+map MAP02` and exit; `route.py --route metro-critical`) | the stats screen titled "Metro-Bunker", then `SD_MAP02_EXIT_TEXT` ("The westbound tunnel climbs into daylight…"), then MAP03 loads ("MAP03 - Tankograd") |
| C3 | finish MAP03 by its exit breaker (or `+map MAP03` and exit) | the stats screen titled "Tankograd", then `SD_END01_TEXT` ("The breaker drops…", TO BE CONTINUED), then the title screen with `D_SDINTL` |
| C4 | C1-C3 with the game in Russian | the Russian texts and «Танкоград», every line inside the screen, no missing glyph |
| C5 | MAP01 → MAP02 → MAP03 in one run | the ending is shown **once**, after MAP03; after MAP01 and MAP02 only their transitions |
| C6 | New Game → **Practice Range** → any skill (the episode screen, the menu way in); then its exit switch | "RANGE - Training Ground" in the log, the range as before; `SD_END02_TEXT`, then the title screen |
| C7 | `+map RANGE` from the command line (`MAP=RANGE tools/run.sh`), and `map RANGE` from the console | the range loads by its non-MAPxx name |
| C8 | the log of all the above | no `Script error` from `MAPINFO`, no `Unknown` lookup, no "map not found" |
| C9 (D104) | New Game: the episode screen | three episodes in this order: Soviet Doom, The Road to Moscow, Practice Range (and «Дорога на Москву», «El camí de Moscou» in Russian and Catalan), all inside the screen |
| C10 (D104) | New Game → The Road to Moscow → any skill; finish MAP04 | "MAP04 - Trans-Siberian" in the log; the stats screen, then `SD_MAP04_EXIT_TEXT` ("The armoured train clears the yard…"), then MAP05 |
| C11 (D104) | finish MAP05 | `SD_MAP05_EXIT_TEXT` ("You cross the crest of the dam…"), then MAP06 ("MAP06 - Red Square") |
| C12 (D104) | finish MAP06; then MAP03 again from episode 1 | `SD_END03_TEXT` ("The last of them falls at the Kremlin gate…", TO BE CONTINUED), then the title screen; MAP03 still ends with `SD_END01_TEXT` and never leads to MAP04 |
| C13 (D112) | New Game: the episode screen | four episodes in this order: Soviet Doom, The Road to Moscow, The Portal, Practice Range («Портал», «El portal» in Russian and Catalan), all inside the screen |
| C14 (D112) | New Game → The Portal → any skill; finish MAP07 | "MAP07 - Novaya Zemlya" in the log; the stats screen (with `D_SDE2IB`), then `SD_MAP07_EXIT_TEXT` ("The radar goes dark…"), then MAP08 ("MAP08 - Severomorsk") |
| C15 (D112) | finish MAP08 | `SD_MAP08_EXIT_TEXT` ("The submarine settles at its berth…"), then MAP09 ("MAP09 - Tunguska") |
| C16 (D112) | finish MAP09; then MAP06 again from episode 2 | `SD_END04_TEXT` ("The portal folds in on itself…", TO BE CONTINUED), then the title screen; MAP06 still ends with `SD_END03_TEXT` and never leads to MAP07 |

### 4.1 How the campaign ends (M3, closed 2026-10-13)

> **Since D60 the ending is the campaign's last map's, not MAP01's, and
> since D62 that map is MAP03, the factory** (§4.6): MAP03 is in cluster 1
> and says `next = endtitle`; MAP01 (cluster 3) and MAP02 (cluster 4) lead
> on. The three engine facts below still hold; read "MAP01" in them as "the
> campaign's last map".

`Exit_Normal` on MAP01 ended the game until D60. Three facts, all verified in-engine,
that anyone touching this needs:

- **The end-of-episode text belongs to the CLUSTER, not to the map.** The
  obvious `next = EndGame { Text = "…" }` does not parse: an endgame block
  accepts only `pic`, `hscroll`, `vscroll`, `cast` and `music`
  (`ParseEndGame`, gzdoom: src/intermission/intermission_parse.cpp, engine source, not a file of this repo), and GZDoom
  answers `Unknown property 'Text' found in endgame definition`. The copy is
  `cluster 1 { exittext = lookup, "SD_END01_TEXT" flat = "SDFLR1" }`.
- **`next = endtitle`** is the named end sequence for "roll the ending, then
  go back to the title screen" (`CheckEndSequence`, same file). Since V3 B2
  the three episode ends name their own sequences instead,
  `next = EndSequence, "SD_EndingN"`: the same path with one picture before
  the title (§6.16); the range keeps `endtitle`.
- **`nointermission` is gone from MAP01.** Pressing the exit used to restart
  the map in silence; the stats screen is the first thing that says the
  level was finished. `par = 210` is `level-designer`'s figure. **NOT
  VERIFIED**: that the screen prints 3:30 — the PAR row appears, but its
  value animates upward and never settled within an unattended run. QA, with
  a human at the keyboard.

### 4.2 Map specials in use (M5, from `level-designer`'s §9)

ZDoom's line-special NUMBERS are compiled into the engine, not shipped in any
file, so these were verified the only way left: by walking the map in v0 and
watching the geometry move. Evidence in `docs/levels/shots/`. The argument
*shapes* do ship, in `gzdoom.pk3 → xlat/`.

| Special | № | Arguments | Used for | Status |
|---|---|---|---|---|
| `Door_Raise` | **12** | `(tag, speed, delay, lighttag)`, emitted as `(tag, 16, 150, 0)` | manual door, openable from both sides; `playeruse` + `repeatspecial` | **VERIFIED in engine** 2026-10-13 |
| `Door_Open` | **11** | `(tag, speed, lighttag)`, emitted as `(tag, 16, 0)`, and since MAP01 v2 as `(10, 16, 30)` on SW-A | push panel that stays open; a one-sided wall switch opening a remote tagged door; with a lighttag, the sectors carrying that tag brighten while the door opens | **VERIFIED in engine** 2026-10-13; the lighttag on 2026-10-13 16:11 (the cabin seen through its window goes from dark to lit). A switch line without `repeatspecial` stays on its ON face (seen 105 tics after the press) |
| `Exit_Normal` | **243** | `(pos)` | the level exit switch | **VERIFIED in engine** 2026-10-13; since this change it ends the game (§4.1) rather than reloading MAP01 |

Constants from `xlat/defines.i`: `D_SLOW = 16`, `VDOORWAIT = 150`. Tags are a
UDMF `id` on the sector and `arg0` on the line.

Two engine facts that cost `level-designer` a rebuild each, kept here so the
next person does not pay again:

- A `playeruse` special fires **only from the front side of the line**, so a
  door needs the special on *both* flanking lines, each wound with the door
  as the BACK side. `LineStyle.back_sector` in `tools/sdbuild/udmf.py` does
  it and `tests/test_udmf.py` asserts it.
- `Door_Raise` / `Door_Open` raise a door to **(lowest neighbouring ceiling
  − 4)**, so a door opened off a low neighbour can end up impassable.

Sector specials, numbers from `gzdoom.pk3 → xlat/defines.i`:

| Sector special | № | Used for | Status |
|---|---|---|---|
| `dLight_Flicker` | **65** | the flickering stretch of Z5 (MAP01 v2) | **VERIFIED in engine** 2026-10-13 16:11: mean brightness 61 → 46 → 61 over three shots 5 tics apart |
| `SECRET_MASK` | **1024** | the three secret sectors S1-S3 | **VERIFIED in engine** 2026-10-13 16:11: each prints the secret message on entry |

Since MAP01 v3 one tag can name several doors: tag 10 opens D4 and the
three fuel-bay ambush panels, tag 11 opens D5 and the three hangar closets,
so each switch also releases a wave without a trigger line of its own.
NOT VERIFIED in engine until the v3 pass. Tag 30 is MAP01's "gate light": SW-A's lighttag, carried by the switch
niche, D4's recess and the booth. NOT VERIFIED: how much the niche itself
brightens, which the player sees without turning (measured +4 % mean
luma on the screenshot, with the switch face changing in the same frame).

Not used, and therefore not contract: `Light_ChangeToValue` (110) and
`Light_Flicker` (113); each would need a trigger line of its own.

Evidence of the v2 engine pass (24 screenshots, exact view angles set by a
throwaway helper that never enters the repo):
`docs/qa/evidence/2026-10-13_1611_F3_map01-v2-engine-pass-{1,2,3}.png` and
the log `…-engine-pass.log`, zero failure-pattern lines.

### 4.3 Switch textures, animations and masked textures: ANIMDEFS (T16, N6b, N6c)

Eight switch faces are approved and ship in `textures/` (batch 2,
2026-10-13; each 64×128, one wall segment on the 64 grid; origin and
licence in `docs/art/LICENSES.md`): `SDSW1A`–`SDSW1D` and
`SDSW2A`–`SDSW2D`. The **naming convention is contract from here on**, and
it is Doom's own (`SW1BRCOM` / `SW2BRCOM`):

| Characters | Meaning |
|---|---|
| `SDSW` | mod prefix + "switch" |
| `1` / `2` | the state: **1 = off** (unpressed), **2 = on** (pressed). The two lumps of a pair differ only in this digit |
| last letter `A`–`D` | the design variant (A knife switch, B domed button, C slide lever, D hazard panel) |

The name the brief used, `SDSWT1`/`SDSWT2` (level-design item A3,
`tools/art/gen_switch.py`), is withdrawn: four variants were approved, not
one, and the variant letter needs the eighth character.

The declaration that makes the engine **swap 1 for 2** when the line is
used is `src/lumps/ANIMDEFS`, packed as the root lump `ANIMDEFS` by the
build with no other change (§3). One line per pair:

```
switch doom 1 SDSW1A on pic SDSW2A tics 0
switch doom 1 SDSW1B on pic SDSW2B tics 0
switch doom 1 SDSW1C on pic SDSW2C tics 0
switch doom 1 SDSW1D on pic SDSW2D tics 0
```

- **Syntax verified against the engine's own definitions**, not the wiki
  (still unreachable on 2026-10-13): GZDoom g4.14.2 ships `animdefs.txt` at
  the root of `gzdoom.pk3`, and lines 194-235 declare every Doom switch in
  exactly this form (`switch doom 1 SW1BRCOM on pic SW2BRCOM tics 0`).
  `doom` is the game filter (Doom-family IWADs, which is what §1
  supports); the number is the oldest Doom release the pair exists in
  (1 shareware, 2 registered, 3 Doom II) and 1 is the most permissive; the
  next name is OFF, `on pic` names ON, `tics 0` holds the ON picture
  without animating. The bare form without a game filter is NOT VERIFIED
  and not used.
- **No `sound`.** None of the engine's Doom switch lines carries one (only
  Hexen's and Strife's do); the click is the engine default
  `switches/normbutn` → `DSSWTCHN` (`gzdoom.pk3 → filter/game-doomchex/sndinfo.txt`),
  `switches/exitbutn` on exit lines. Inferred from that file; NOT VERIFIED
  until heard in engine.
- **VERIFIED in engine, 2026-10-13 14:34** (GZDoom g4.14.2 + Freedoom
  0.13.0, Windows): `SDSW1A` flips to `SDSW2A` when the player presses it,
  and in a second run Freedoom's own `SW1BRCOM` still flips to `SW2BRCOM`
  with our lump loaded, so a mod's `ANIMDEFS` **adds** to the engine's
  definitions rather than replacing them. Method: a throwaway 256×256 map
  (not in the repo) with the switch as a one-sided `Door_Open` line 56 units
  in front of the player start, and the console sequence `wait 70;
  screenshot; wait 10; +use; wait 4; -use; wait 70; screenshot; quit`. Zero
  failure-pattern lines in either log. Evidence, before and after for both:
  `docs/qa/evidence/2026-10-13_1434_F2_t16-switch-flip.png`. Variants B, C
  and D share the same line form and were not pressed individually.
  **Still NOT VERIFIED:** the click, which an unattended run cannot hear.
- `SWITCHES`, Boom's binary lump, is not used: opaque to `git diff` and to
  `check_pk3.py`, and it does nothing `ANIMDEFS` does not.
- Guarded by `tests/test_animdefs.py` (one line per approved pair, each
  SDSW1x to its own SDSW2x, every name in `assets/`, the lump at the PK3
  root) and by `tools/check_pk3.py`, whose `textures` check holds every
  ANIMDEFS switch name to the same rule as a map texture (in the PK3 or in
  §5).

MAP01 v2 wears the real faces: SW-A = `SDSW1A`, SW-B = `SDSW1B`, the exit
= `SDSW1D` (`SWITCH_PLACEHOLDER` is gone). All three flipped in the v2
engine pass of 2026-10-13. A repeatable switch returns to OFF after a short
delay (Doom's behaviour, NOT VERIFIED here), which is why SW-A and SW-B are
single-use.

#### Animated surfaces (N6c, 2026-10-14)

Two Tankograd surfaces (D66) animate on their own: an **animation** in
ANIMDEFS tells the engine to swap a surface through a list of pictures,
forever, wherever a map uses the first one. A map names only frame 1.

| Map names | Keyword | Frames | Rate | Where it lives |
|---|---|---|---|---|
| `SDMOLT1` | `flat` (a floor or ceiling) | `SDMOLT1` → `SDMOLT2` → `SDMOLT3` → `SDMOLT4` → `SDMOLT1` | 8 tics each (8/35 s ≈ 0.23 s, a 0.9 s loop) | `flats/factory/` |
| `SDPORT1` | `texture` (a wall) | `SDPORT1` → `SDPORT2` → `SDPORT3` → `SDPORT4` → `SDPORT1` | 8 tics each | `textures/factory/` |
| `SDWATR1` | `flat` (MAP05's Volga, D107) | `SDWATR1` → `SDWATR2` → `SDWATR3` → `SDWATR4` → `SDWATR1` | 8 tics each, Doom's own water rate (FWATER1-4) | `flats/dam/` |
| `SDRADR1` | `texture` (MAP07's radar console, D113) | `SDRADR1` → `SDRADR2` → `SDRADR3` → `SDRADR4` → `SDRADR1` | **12 tics** each (the beam turns 90° a frame: a 48-tic, 1.4 s sweep) | `textures/arctic/` |
| `SDACID1` | `flat` (MAP09's acid, D113) | `SDACID1` → `SDACID2` → `SDACID3` → `SDACID4` → `SDACID1` | 8 tics each, as `SDWATR1` | `flats/taiga/` |

```
flat SDMOLT1
	pic SDMOLT1 tics 8
	pic SDMOLT2 tics 8
	pic SDMOLT3 tics 8
	pic SDMOLT4 tics 8

texture SDPORT1
	pic SDPORT1 tics 8
	...
```

- **Syntax VERIFIED in the engine source** (read 2026-10-14):
  `FTextureAnimator::InitAnimDefs` in
  `src/gamedata/textures/animations.cpp`, GZDoom tag g4.14.2, sends both
  `flat` and `texture` to `ParseAnim`, the first with the flat namespace and
  the second with the wall namespace; `ParseAnim` reads `[optional] NAME`,
  then `pic FRAME tics N` per frame or one `range LAST tics N`, and refuses
  fewer than two frames. The engine's own `gzdoom.pk3 → animdefs.txt` writes
  the `texture` form the same way (`texture optional M_SKULL1`, `pic M_SKULL1
  tics 8`) but has **no `flat` line**: Doom's own flats (`NUKAGE1-3`)
  animate from the binary `ANIMATED` lump in `filter/game-doomchex/`. The
  keyword follows the namespace (`flat` for a flat, `texture` for a wall);
  whether the lookup falls back to the other namespace was not read, so
  the wrong keyword is treated as an error here (NOT VERIFIED either way).
- **Every frame is named with `pic`**, not `range`: a range takes the frames
  between two names in the texture manager's order, and whether that order
  follows the file names for loose PNGs in a PK3 is NOT VERIFIED. Naming
  each frame removes the question.
- **The rate** is `art-director`'s proposal (8 tics a frame; the batch-4
  preview GIFs run at 229 ms, `GIF_MS` in `tools/art/gen_factory.py`). Each
  loop was drawn seamless, frame 4 leading back into 1.
- **Seen moving in the engine: NOT VERIFIED** (D26); the PM's engine pass.
- Guarded by `tests/test_animdefs.py` (`AnimdefsAnimationTest`: exactly the
  three animations, `flat` for a flat and `texture` for a wall, frames 1-4
  in order at 8 tics, every frame installed and packed in its own folder)
  and by `tools/check_pk3.py`, whose `textures` check holds every animation
  frame to the same rule as a map texture (`animdefs_anim_textures`).
  Since D113 the test pins five animations, each at its own rate (the radar
  12 tics, the rest 8).

#### Masked textures (N6b, D66, 2026-10-14)

A **masked texture** has holes: placed as the middle texture of a
two-sided line, the engine draws its opaque pixels and leaves the rest open,
so the player sees and shoots through the gaps (fences, grates, a hanging
chain). In this mod it is an **RGBA PNG with hard alpha** (every pixel 0 or
255), the only exception to the indexed-PNG rule under `textures/`.

| Lump | Size | Use |
|---|---|---|
| `SDCHAN1` | 64×128 | Tankograd's hanging chain and crane hook (D66); `texturemiddle` of a two-sided line, not tiling vertically |
| `SDKREM2` | 64×128 | MAP06's Kremlin merlon (D107), `SDKREM1`'s brick cut out, palette v2 (`PALETTE_V2_MASKED`); `texturemiddle` of a two-sided line on the wall top, tiles along x |
| `SDINSL1` | 64×128 | MAP05's high-voltage insulator string (D107); `texturemiddle` of a two-sided line, tiles along x |
| `SDCRAN1` | 64×128 | MAP08's quay crane jib lattice (D113); `texturemiddle` of a two-sided line, tiles in both axes |
| `SDGRIL1` | 64×128 | MAP05's control-room window bars (D113); `texturemiddle` of a two-sided line, tiles along x |
| `SDHVLT1` | 64×128 | MAP05's substation high-voltage fence with its «СТОЙ!» plate (D113); `texturemiddle`, tiles along x |
| `SDRUBY1` | 128×128 | MAP06's Kremlin ruby star (D113); `texturemiddle` of a two-sided line against the sky, does not tile |

- **The engine accepts it: VERIFIED in the source** (read 2026-10-14):
  GZDoom's PNG loader, `src/common/textures/formats/pngtexture.cpp` (tag
  g4.14.2), takes colour type 6 at 8 bits and sets `bMasked = true` for
  every RGBA PNG; in the paletted (software) path each pixel goes through
  `ImageHelpers::RGBToPalette` with its alpha, and index 0 is the
  transparent index there. The exact alpha threshold of that function was
  not read, which is why the alpha is hard: 0 and 255 land on the same side
  of any threshold. **Seen with its gaps open in the engine: NOT VERIFIED**
  (D26); the PM's engine pass.
- **Declared, not inferred:** the set is `MASKED_TEXTURES` in
  `tools/check_pk3.py`, and `tests/test_art.py` imports it, so the two
  validators cannot disagree. A lump in the set must be colour type 6 at
  8 bits, alpha only 0/255, and every opaque pixel in
  `docs/art/palette.json`; every other PNG under `textures/` and `flats/`
  stays indexed, and an RGBA one outside the set is still an error. A flat
  is never masked. Adding a masked texture = add it to `MASKED_TEXTURES`
  here first (this section), then install it.
- Guarded by `tests/test_check_pk3.py` (`MaskedTextureTest`: hard-alpha
  RGBA passes only inside the set, partial alpha, off-palette opaque
  pixels, an indexed copy of a declared lump and an RGBA flat all fail) and
  `tests/test_art.py` (`test_layout_names_and_sizes`,
  `MaskedTexturesTests`).

## 5. IWAD assets used

The mod redistributes nothing from the IWAD. Freedoom keeps Doom II lump
names, so a name reference works on both. Every IWAD reference must appear
here and in the `art-director`'s texture index flagged "IWAD".

| Name | Type | Used in | Verification |
|---|---|---|---|
| `STARTAN2` | wall texture 64×128 | MAP01, 4 walls | verified on freedoom2.wad 0.13.0 (G0 screenshot) |
| `FLOOR4_8` | flat (floor) | MAP01 | verified |
| `CEIL3_5` | flat (ceiling) | MAP01 | verified |
| `SKY1` | sky texture | MAPINFO `sky1` of MAP02 only (every other map wears its own `SDSKY1-7` since D113) | loads without error |

IWAD elements used implicitly: the status bar's layout and code
(`DoomStatusBar`; since M2e-i its pictures are ours, §6.5, but for the
lumps §5.1 lists as left to Freedoom), the four ammo pools
(`Clip`, `Shell`, `RocketAmmo`, `Cell`) with their pickups, and the Doom
weapon classes the arsenal inherits from. Since F4 the player pawn and all
seven weapons are **ours** (§6); Freedoom's are replaced, and the super
shotgun and chainsaw are unplaceable.

`RANGE` (the practice range, `MAP02` until D62) additionally places Doom
editor numbers as **test fixtures**:
explosive barrel (2035), zombieman (3004), medikit (2012), blue armour
(2019), backpack (8) and the ammo boxes 2046/2048/2049/17. Since F5 the six
3004 targets spawn **`SD_ReichRifleman`** (`replaces ZombieMan`), so the
arsenal is tested against our own enemy; the ammo boxes and the backpack
were already ours (§6.4); the medikit and the armour are ours since D80
(§6.3); the barrel is ours since D82, shipped under the IWAD's `BAR1`/`BEXP` (§5.1).

**MAP01 (campaign) since v3, 2026-10-13** places Doom editor numbers too:
monsters 3004, 9, 3001, 3002, 3005 and 69, each spawning our class through
`replaces` (§6.1), so the map needs no renumbering when our sprites land;
explosive barrel 2035, floor lamp 2028 and computer area map 2026; health
and armour 2011, 2012, 2014, 2015 and 2018; ammunition 2007, 2048, 2008,
2049, 2046 and backpack 8, the ammo ones ours by replacement (§6.4); and our
own weapon numbers 21001, 21003, 21004 and 21005 (§6.1), their first use in
a campaign map. Skill flags go in pairs, 1 = 2 and 4 = 5
(`tools/sdbuild/udmf.py`, `skill_tier`). Doom's 65 (chaingunner) and 58
(spectre) are not placed: no class of ours replaces them (T21).

### 5.1 IWAD sprites used as placeholders

A sprite named in a ZScript `States` block must be packed under `sprites/`
or written in this table; `tools/check_pk3.py` (category `sprites`) fails
the package otherwise, as it does for an undeclared IWAD texture. Every one
of them is a **placeholder** for a lump reserved in §6.3; none is
redistributed, the engine reads it from the loaded IWAD. The frames the
bestiary uses were checked against `iwads/freedoom2.wad` 0.13.0 by
`tests/test_bestiary.py` (it skips where no IWAD is present, as in CI).
`TNT1` (the engine's invisible sprite) and the `####` / `----` "keep the
previous sprite" markers are the engine's and need no row.

**Retired 2026-10-14 (D48):** `CSAW`, `PIST`, `SHOT`, `MGUN`, `LAUN` and
`PLAS`, the pickups of the ice axe, TT-33, IZh-58, PPSh-41, RPG-7 and
ROKS-3. Our weapons' `Spawn` states name our own pickups now (§6.3). Doom's
own classes that use those lumps (Freedoom's `Chainsaw`, `Shotgun`,
`Chaingun`, `RocketLauncher`, `PlasmaRifle`) are untouched: the swap is a
rename inside our states, not a replacement of the IWAD lump, so nothing
else changes picture. `BFUG` (the Katyusha's pickup) and every held and
flash sprite in the table remain.

**Retired 2026-10-14 (D54):** `SPOS`, the Legion trooper's placeholder.
Every `SD_LegionTrooper` state names our `SDLT` now (§6.3, "The Legion
trooper, installed by D54"). Doom's own `ShotgunGuy` and its corpse
`DeadShotgunGuy` (editor number 19; it derives from `ShotgunGuy`, not
from our class, and spawns as `Goto Super::Death+4`, read in g4.14.2's
`gzdoom.pk3`, `zscript/actors/doom/deadthings.zs`) keep Freedoom's `SPOS`:
the swap renamed our states and did not replace the IWAD lump. No map of
ours places 19 (counted in the built MAP01 and MAP02, 2026-10-14; that
MAP02 is the range, `RANGE` since D62).

**Retired 2026-10-14 (D55):** `POSS` and `SARG`, the placeholders of the
Reich rifleman and the Reich hound. Every `SD_ReichRifleman` state names
our `SDRR` and every `SD_ReichHound` state our `SDHN` now (§6.3, "The Reich
rifleman and the Reich hound, installed by D55"). Doom's own classes that
use those lumps keep Freedoom's: `ZombieMan` and its corpse `DeadZombieMan`
(editor number 18, `Goto Super::Death+4`), `Demon`, its corpse `DeadDemon`
(21, `Goto Super::Death+5`), the `Spectre` (58) and the stealth variants
`StealthZombieMan` and `StealthDemon`, all deriving from Doom's classes,
not from ours (read in g4.14.2's `gzdoom.pk3`, `zscript/actors/doom/`
`deadthings.zs`, `demon.zs`, `stealthmonsters.zs`). No map of ours places
18, 21, 58 or a stealth monster
(counted in the built MAP01 and the range, then MAP02, 2026-10-14; 58 is forbidden to maps
by `BESTIARY.md` §6).

**Retired 2026-10-14 (D56):** `TROO` and `BAL1`, the placeholders of the
Hybrid Stormtrooper and his bolt. Every `SD_Stormtrooper` state names our
`SDHS` and every `SD_StormBolt` state our `SDBL` now (§6.3, "The Hybrid
Stormtrooper and his bolt, installed by D56"). Doom's `DoomImp`, its corpse
`DeadDoomImp` (editor number 20), `StealthDoomImp` and `DoomImpBall` keep
Freedoom's: they are Doom's classes, not ours (read in g4.14.2's
`gzdoom.pk3`, `zscript/actors/doom/`). No map of ours places 20 or a
stealth imp (counted in the built MAP01 and the range, then MAP02, 2026-10-14).

**Retired 2026-10-14 (D67):** `BOS2`, the Panzermensch's placeholder. Every
`SD_Panzermensch` state names our `SDPM` and every `SD_PanzermenschSchwer`
state our `SDPS` now (§6.3, "The Panzermensch and the Schwer, installed by
D67"). Doom's own `HellKnight` (editor number 69) keeps Freedoom's `BOS2`
and `BaronOfHell` (3003) its `BOSS`, but ours replace both, so a map placing
either spawns ours; Doom ships no corpse thing of either. `BAL7` stayed: the
Panzermensch's shell, `SD_PanzerShell`, was not drawn yet (retired by D81,
below).

**Retired 2026-10-14 (D70):** `HEAD`, the Doughboy's placeholder. Every
`SD_Doughboy` state names our `SDDB` now (§6.3, "The Doughboy, installed by
D70"). Doom's own `Cacodemon` (editor number 3005) keeps Freedoom's `HEAD`,
but ours replaces it, so a map placing 3005 spawns ours (MAP01 does);
Doom's corpse thing `DeadCacodemon` (editor number 22, derived from
`Cacodemon`, not from ours; read in g4.14.2's `gzdoom.pk3`) keeps `HEAD`
too, and no map of ours places it (counted in the built MAP01, MAP02,
MAP03 and the range, 2026-10-14). `BAL2` stayed: the Doughboy's shell,
`SD_DoughboyShell`, was not drawn yet (retired by D81, below).

**Retired 2026-10-14 (D73):** `CYBR`, the General's placeholder, and `MANF`,
his shell's in flight. Every `SD_General` state names our `SDGN` and every
`SD_GeneralShell` state our `SDGL` now (§6.3, "The General and his shell,
installed by D73"). Doom's own `Cyberdemon` (editor number 16) keeps
Freedoom's `CYBR`, but ours replaces it, so a map placing 16 spawns ours;
Doom ships no corpse thing of it. Doom's `FatShot` keeps `MANF` (the
mancubus, `Fatso`, is not replaced, debt T21). `MISL` stays, for the PG-7V
grenade and the Katyusha rocket; only its use as the shell's burst ends.

**Retired 2026-10-15 (N17):** `PISG` and `PISF`, the TT-33's held and
flash placeholders. Every `SD_Tokarev` state names our `SDTT` and `SDTF`
now (§6.3, "The TT-33 in hand"). Doom's own `Pistol`
keeps Freedoom's `PISG`/`PISF`, but ours `replaces Pistol`, so the player
never holds it; no other class of ours named either.

**Retired 2026-10-20 (D79):** `CHGG` and `CHGF`, the PPSh-41's held and
flash placeholders. Every `SD_Ppsh` state names our `SDPP` and `SDPF` now
(§6.3, "The PPSh-41 in hand, installed by D79"). Doom's own `Chaingun`
keeps Freedoom's `CHGG`/`CHGF`, but ours `replaces Chaingun`, so the
player never holds it; no other class of ours named either.

**Retired 2026-10-20 (D84):** `SHTG`, `SHTF`, `MISG`, `MISF`, `PLSG`,
`PLSF`, `BFGG` and `BFGF`, the held and flash placeholders of the IZh-58,
RPG-7, ROKS-3 and hand Katyusha, and `BFUG`, the hand Katyusha's pickup
(D80). Every `SD_Izh`, `SD_Rpg7`, `SD_Roks3` and `SD_HandKatyusha` state
names our `SDIZ`/`SDIF`, `SDRL`/`SDRF`, `SDRK`/`SDKF`, `SDHK`/`SDHF` and
`SDHP` now (§6.3, "The IZh-58, RPG-7, ROKS-3 and hand Katyusha in hand,
installed by D84"). Doom's own `Shotgun`, `RocketLauncher`, `PlasmaRifle`
and `BFG9000` keep Freedoom's lumps, but ours replace all four, so the
player never holds one and no map can spawn one; no other class of ours
named any of the nine. `MISL` stays (the PG-7V grenade and the Katyusha
rocket), and `PLSS`/`PLSE` (the flame in flight): the projectiles are not
drawn yet.

**Retired 2026-10-20 (D88):** `PUNG`, the ice axe's held placeholder
(Freedoom's fist). Every `SD_IceAxe` state names our `SDAX` now (§6.3, "The
ice axe in hand, installed by D88"). Doom's own `Fist` keeps Freedoom's
`PUNG`, but ours `replaces Fist`, so the player never holds it; no other
class of ours named it.

**Retired 2026-10-20 (D81):** `BAL2` and `BAL7`, the placeholders of the
Doughboy's and the Panzermensch's shells. Every `SD_DoughboyShell` state
names our shell `SDDL` and every `SD_PanzerShell` state our shell `SDPL` now (§6.3,
"The two enemy shells, installed by D81"). Doom's own `CacodemonBall` and
`BaronBall` keep Freedoom's `BAL2` and `BAL7`; no class of ours fires
either (the Doughboy and the Panzermensch, which replace the Cacodemon and
the Hell Knight and Baron, fire ours).

**Retired 2026-10-14 (D63):** `PMAP`, the radio's placeholder (the computer
area map's pickup picture). `SD_Radio`'s `Spawn` state names our `SDRD` now
(§6.3, "The pickups, installed by D63"). Doom's own `Allmap` keeps
Freedoom's `PMAP`: MAP01 places it (editor number 2026), and from D63 on it
no longer looks like the radio. The ammunition pickups and the blue pass
never had a row here: no state of ours named `CLIP`, `AMMO`, `SHEL`,
`SBOX`, `ROCK`, `BROK`, `CELL`, `CELP` or `BKEY` (they were inherited from
Doom's classes); since D63 each of those classes names its own sprite.
`BPAK`, the backpack's, is still inherited and still needs no row.

**Retired 2026-10-20 (D80):** `STIM`, `MEDI`, `BON1`, `BON2`, `ARM1`,
`ARM2`, `PMAP`, `BPAK`, `YKEY` and `RKEY`, Freedoom's pictures of the
campaign's health, armour, area map, backpack and yellow and red keycards.
None ever had a row here (each was inherited from Doom's class); since D80
each of our replacing classes names its own sprite (§6.3, "The campaign
pickups, installed by D80"), so every Doom editor number the campaign
places for them (2011, 2012, 2014, 2015, 2018, 2019, 2026, 8, 6, 13)
spawns our picture. Doom's own classes keep Freedoom's lumps, but ours
replace them, so no map can spawn one. The armours' and the armour bonus'
HUD icons are ours too, and the key icons `STKEYS0`-`STKEYS2` are shipped
by the mod under the engine's names; the fullscreen HUD's health icon
`MEDIA0` is still Freedoom's (§6.3).
`BFUG`, the hand Katyusha's, followed on the same day with D84's install
(below).

**Retired 2026-10-20 (D82):** `MISL`, `PLSS` and `PLSE`, the last three:
the PG-7V grenade and the Katyusha rocket in flight and their burst, and
the ROKS-3's flame in flight and on impact. Every `SD_Pg7Grenade` state
names our `SDPG`/`SDPX`, every `SD_KatyushaRocket` state `SDKR`/`SDPX` and
every `SD_FlameBlob` state `SDFJ`/`SDFX` now (§6.3, "The player effects,
installed by D82"). Doom's own `Rocket` keeps Freedoom's `MISL` and
`PlasmaBall` its `PLSS`/`PLSE`, but no class of ours fires either (the
RPG-7 and the ROKS-3 replace the rocket launcher and the plasma rifle and
fire ours; the General's shell left `MISL` with D73). Checked before
retiring them: no `States` block under `src/zscript/` names any of the
three (`tests/test_effects_install.py`); only comments still tell the
history. **No IWAD sprite is a placeholder any more:** the table that
stood here is empty and gone.

**The engine actors' overrides (D82): IWAD names we ship.** The same
install replaced the pictures of seven engine actors without touching
their code: the mod ships its own lumps under the IWAD's names, `PUFF`
A-D (`BulletPuff`, and `SD_IceAxePuff`, which inherits its states),
`BLUD` A-C (`Blood`, still recoloured by `BloodColor`), `TFOG` A-J
(`TeleportFog`, the General's summon), `IFOG` A-E (`ItemFog`), `BAR1` A-B
and `BEXP` A-E (`ExplosiveBarrel`, editor number 2035) and `COLU` A
(`Column`, 2028), each in rotation 0. A PK3 loaded after the IWAD wins a
sprite name over it, so every path that spawns these actors draws ours:
the maps' barrels and lamps by editor number, the engine's blood and
puffs, the summon's fog. Each set is **exactly Freedoom's lump set for
that name** (read in `freedoom2.wad` 0.13.0: `PUFFA0`-`PUFFD0`,
`BLUDA0`-`BLUDC0`, `TFOGA0`-`TFOGJ0`, `IFOGA0`-`IFOGE0`,
`BAR1A0`-`BAR1B0`, `BEXPA0`-`BEXPE0`, `COLUA0`), so no Freedoom frame or
rotation is left to mix in; `tests/test_effects_install.py` reads the IWAD
(where present) and holds it. These are the one exception to the `SD`
prefix among sprites (§1; `tests/test_art.py`, `IWAD_OVERRIDE_SPRITES`);
they are not placeholders and need no row here (`check_pk3` finds them
packed under `sprites/`). Why not a new prefix: it would need a replacing
class per actor plus `SD_IceAxePuff`'s states, for the same pixels
(`tools/art/gen_effects.py`, `INSTALL_WHY`). No class of ours names any
of the seven in a `States` block.

**The status bar's pictures (M2e-i, D89, D90, D92): IWAD names we ship.**
Not sprites, graphics: `DoomStatusBar` draws `STBAR`, `STARMS`,
`STTPRCNT`, `STYSNUM*` / `STGNUM*` and the face (`GetMugShot`, the `STF`
prefix) by name, and its fonts `HUDFONT_DOOM` (`STTNUM0-9`, `STTMINUS`,
`STTPRCNT`; also the fullscreen HUD's numbers) and `INDEXFONT_DOOM`
(`STYSNUM0-9`; the ammo table) are built from these lumps
(`gzdoom.pk3:fontdefs.txt`). A PK3 loaded after the IWAD wins the name, so
the mod ships 76 of them under Freedoom's names, each at Freedoom 0.13.0's
size and `grAb` offsets (`tests/test_hud_install.py` re-reads the IWAD).
**Left to Freedoom, read from the IWAD and not redistributed:** the
multiplayer face backgrounds `STFB0-3` and `STPB0-3`, the skull-key icons
and pairs `STKEYS3-8` (the mod has no skull key), the HUD message font
`STCFN*` (extended by our `defsmallfont`, §2), the fullscreen HUD's
`MEDIA0` (§6.3), and `STDISK`, `STCDROM`.

The sounds are the same kind of borrowing and are listed in §6.2; they are
not checked by `check_pk3.py` (a missing sound is silence, not an error), but
`tests/test_bestiary.py` checks that every bestiary placeholder lump exists
in the IWAD.

## 6. ZScript

- Entry: `zscript.txt` with `version "4.12"` and only `#include`s.
- One class per file. `zscript/sd/` holds systems, `zscript/weapons/` holds
  the arsenal, `zscript/monsters/` the bestiary. Class names are prefixed
  `SD_`.
- Event handlers are registered in `MAPINFO → GameInfo → AddEventHandlers`.
- The player class is declared in `MAPINFO → GameInfo → PlayerClasses`
  (a player pawn cannot use `replaces`).
- Every gameplay number is a named constant whose comment says why; the
  reasoning lives in `docs/engine/BALANCE.md`.

| Class | Type | Purpose |
|---|---|---|
| `SD_LoadReporter` | `EventHandler` | `WorldLoaded` → `Console.PrintfEx(PRINT_HIGH \| PRINT_NONOTIFY, "SOVIETDOOM loaded: …")`: console and log only, never the HUD (QA-G6-2). Pipeline smoke test. No gameplay effect. |
| `OptionMenuItemSDLanguageOption` | `OptionMenuItemOption` | The Language row: overrides `GetSelection` only, so any `language` value shows Automatic, English, Russian or Catalan (any `ca*` code shows Català; QA-G6-1, ADR 004 D-004-7, P6). Writes nothing. |
| `SD_Player` | `DoomPlayer` | The sergeant. Starts with `SD_Tokarev` and 50 `Clip`, nothing else: no ice axe and no `Fist`, so slot 1 is empty until the ice axe is picked up (since 2026-10-13, `BALANCE.md` §4.1). Declares slots 1–7; slot 4 holds two since D116, `"SD_Ppsh", "SD_Akm"` in that order; slot 8 is the RGD-5's (V3, ADR 012). |
| `SD_IceAxe` | `Fist` *replaces Fist* | Slot 1, melee: the ice axe (D40; was `SD_Shovel`). Found, never issued: MAP01 places it on the dorm's rack (every skill, reachable with every door shut), `RANGE` on the range. |
| `SD_Tokarev` | `Pistol` *replaces Pistol* | Slot 2, `Clip`. |
| `SD_Izh` | `Shotgun` *replaces Shotgun* | Slot 3, `Shell`. Two barrels then a break-open reload (`int barrels`). Dropped by a trooper it carries 2 shells (`ModifyDropAmount`, D119). |
| `SD_Ppsh` | `Chaingun` *replaces Chaingun* | Slot 4, `Clip`. |
| `SD_Akm` | `DoomWeapon` (replaces nothing) | Slot 4's second weapon (D112, in the mod since D116): the AKM, `SD_AkmAmmo`, 21008. Its own look since D128 (`SDAK`, `SDAF`, `SDAQ`; §6.3, §6.12); its magazine `SDAM` is still provisional. Design `docs/engine/2026-10-22_P4_akm.md`. |
| `SD_AkmAmmo` | `Ammo` (a pool of its own) | The AKM's 7.62×39 pool and its 30-round magazine, 21020, in `zscript/sd/ammo.zs`; dropped by the Legion gunner. ADR 011, §6.4. |
| `SD_Rpg7` | `RocketLauncher` *replaces RocketLauncher* | Slot 5, `RocketAmmo`. Fires `SD_Pg7Grenade`. |
| `SD_Roks3` | `PlasmaRifle` *replaces PlasmaRifle* | Slot 6, `Cell`. Fires `SD_FlameBlob`. |
| `SD_HandKatyusha` | `BFG9000` *replaces BFG9000* | Slot 7, `Cell`, 40 per salvo. Fires six `SD_KatyushaRocket`. |
| `SD_Rgd5` | `DoomWeapon` (replaces nothing) | Slot 8, a key of its own (V3, A4; ADR 012): the RGD-5 hand grenade, `SD_Rgd5Ammo`; on the floor the pouch of two, 21009. Throws `SD_Rgd5Grenade`; never raised by itself. Own sprites `SDRG`, `SDRQ`, `SDRJ`, `SDRN`, `SDRZ` since D133 (§6.12). Design `docs/engine/2026-10-23_V3_rgd5.md`. |
| `SD_Rgd5Ammo` | `Ammo` (a pool of its own) | The RGD-5's pool and one loose grenade, 21021, in `zscript/weapons/rgd5_ammo.zs`; taken by a player with no `SD_Rgd5`, it gives the weapon too (ADR 012, §6.4). |
| `SD_Rgd5Box` | `SD_Rgd5Ammo` | A crate of four RGD-5s, 21022. |
| `SD_Pg7Grenade` | `Rocket` | Shaped-charge projectile. Not placeable. |
| `SD_FlameBlob` | `Actor` | Fire projectile, 528-unit reach, 3 x random(1,8) since D119 (the bosses' subclasses keep 4). Not placeable. |
| `SD_KatyushaRocket` | `Rocket` | Salvo rocket, does not hurt the shooter. Not placeable. |
| `SD_Rgd5Grenade` | `Actor` | The thrown RGD-5: an arc, short bounces, a 1.71 s fuse counted from the throw (`Death` is "stopped", the burst is `Detonate`), 100 blast over 128 units, hurts the thrower. Not placeable. |
| `SD_IceAxePuff` | `BulletPuff` | The ice axe's puff: `BulletPuff` plus `AttackSound` `sd/weapon/iceaxe/wall`, the pick on stone (N9, §6.2). Not placeable. |
| `SD_WeaponSounds` | `Object` (`play`) | Static helper, never instantiated: `DryClick`, the guns' empty click from `Ready` (N9, §6.2). |
| `SD_Monster` | `Actor` | Bestiary base (F5): `Monster`, `+FLOORCLIP`, the `Faction` property and the three attack helpers. Not placeable. Why enemies do not derive from Doom's monsters, why each sets its own `Species`: ADR 006 (`BESTIARY.md` §2.4 is the earlier draft). |
| `SD_ReichRifleman` | `SD_Monster` *replaces ZombieMan* | Reich infantry, 20 HP, one hitscan. Drops `SD_Clip`. |
| `SD_LegionTrooper` | `SD_Monster` *replaces ShotgunGuy* | Legion infantry, 30 HP, three pellets. Drops `SD_Izh`. |
| `SD_Stormtrooper` | `SD_Monster` *replaces DoomImp* | The hybrid, 60 HP, claw or `SD_StormBolt`. |
| `SD_ReichHound` | `SD_Monster` *replaces Demon* | 150 HP, bite only, speed 12 (H). |
| `SD_Doughboy` | `SD_Monster` *replaces Cacodemon* | Floating head, 400 HP, bite or `SD_DoughboyShell`. |
| `SD_Panzermensch` | `SD_Monster` *replaces HellKnight* | Armoured brute, 500 HP, blow or `SD_PanzerShell` (D35). |
| `SD_PanzermenschSchwer` | `SD_Panzermensch` *replaces BaronOfHell* | The 1000 HP variant for MAP03 (D35); since D67 its own `States` on `SDPS` (the base's, line for line) and a 27 × 72 body. |
| `SD_General` | `SD_Monster` *replaces Cyberdemon* | Boss, 3000 HP (H), three-shell salvo; once below half health, summons two `SD_ReichRifleman` and prints `SD_GENERAL_ORDER` (D35). |
| `SD_LegionGunner` | `SD_Monster` *replaces ChaingunGuy* | P4 (D104, in the mod since D116): Legion heavy machine-gunner, 80 HP, bursts of 4–6 hitscan rounds then a pause. Drops `SD_AkmAmmo`. Own sprite `SDLG` since D123 (§6.3, §6.12). |
| `SD_LibertyColossus` | `SD_Monster` *replaces SpiderMastermind* | P4: Episode 2's boss, 3000 HP (D119, the Spider Mastermind's; was 4500), torch rockets far, a fire jet near, a stomp close. Fires `SD_ColossusRocket` (`SD_Pg7Grenade`) and `SD_ColossusFlame` (`SD_FlameBlob`). MAP06's boss; own sprite `SDLC` since D123. |
| `SD_ChromeGeneral` | `SD_LibertyColossus` (replaces nothing) | P4 (D123): "The Chrome Marshal", the colossus variant: the colossus's body, flags, species, sounds and three verbs, 3000 HP, on `SDCM` (the General's `SDGN` with his armband repainted as the US flag, V3 `tools/art/insignia_fix.py`) at `Scale` 1.3 with the chrome `Translation` the colossus wore from D116 (an approved design, a palette swap, not a placeholder). Own `Tag` and obituaries (`SD_TAG_CHROME`, `SD_OB_CHROME`, `SD_OBHIT_CHROME`). MAP08's mini-boss on skills 3-4. `BESTIARY.md` §12 row 12. |
| `SD_Consortium` | `SD_Monster` (replaces nothing) | P4: Episode 3's final boss, 4000 HP (D119, the Cyberdemon's; was 9000), rooted then free at half health, calls servants of both factions. Fires `SD_ConsortiumRocket`, `SD_ConsortiumOrb` (`SD_GeneralShell`), `SD_ConsortiumFlame`. Own sprite `SDCN` since D128 (§6.3, §6.12). **Placed thing's `arg4` (V3 A3):** a sector tag; at the Breach's first tic, once, the boss sinks the sectors with that tag to their lowest neighbour, taking its flat and damage (`Floor_LowerToLowestTxTy (tag, 16)`), and sets them flickering (`Light_Flicker`); 0 (summoned) opens nothing. MAP09 gives it 15, its crater's scabs (`docs/levels/MAP09-tunguska.md` §18.3); its `special` stays the death's `Door_Open`, which reads arg0-arg2 only. Design `docs/engine/2026-10-22_P4_ep3-final-boss.md`. |
| `SD_ConsortiumWounded` | `SD_Consortium` | Test fixture for the engine pass, not an enemy: the boss at half health + 100, `summon` only; no number, no string. Delete when the pass no longer needs it. |
| `SD_ColossusRocket`, `SD_ColossusFlame`, `SD_ConsortiumRocket`, `SD_ConsortiumOrb`, `SD_ConsortiumFlame` | the arsenal's / the General's projectile | The P4 bosses' projectiles, on their parents' sprites; the Consortium's fly through monsters (`CanCollideWith`). Not placeable. |
| `SD_StormBolt`, `SD_DoughboyShell`, `SD_PanzerShell`, `SD_GeneralShell` | `Actor` | The four enemy projectiles. Not placeable. |
| `SD_Radio` | `Actor` | The diegetic radio (D43): a solid decoration that plays one of two CC0 pieces in place of the level's music while the player is near it, and gives the level's music back when the player walks away. Contract §6.7, reasons ADR 008. |
| `SD_Loudspeaker` | `Actor` | The propaganda radio's loudspeaker (V3 B5, D124), 21201: a positional voice OVER the level's music, a jingle and then shuffled Radio Moscow lines while the player is near it. A street loudspeaker on a pole, grey `SDLS` or olive `SDLO` (arg3 flag 8, D132), frame B while it speaks. Contract §6.14. |
| `SD_MusicVariant` | `EventHandler` | Episodes 2 and 3's music (D106, D113): on a fresh MAP04-MAP09 draws the A (MAPINFO's) or the B piece at random and swaps to the B; on MAP06 and MAP09 swaps to the boss loop when a BOSS monster engages. A load keeps what was playing. Contract §6.11. |
| `SD_BluePass` | `BlueCard` *replaces BlueCard* | The metro's blue pass (MAP02 since D62; propusk): Doom's blue keycard under a Soviet name. `Species "BlueCard"` so lock 2 opens for it; own pickup line `SD_PICKUP_BLUEPASS`; our own sprite since D63 and the `STKEYS0` icon, inherited (the mod ships its own `STKEYS0` since D80). Placed by Doom's editor number 5. Below, "The blue pass". |
| `SD_YellowPass`, `SD_RedPass` | `YellowCard`, `RedCard` *replace YellowCard, RedCard* | Tankograd's yellow and red passes (MAP03, D80): `SD_BluePass`'s pattern, `Species "YellowCard"` / `"RedCard"` so locks 3 and 1 open for them; lines `SD_PICKUP_YELLOWPASS` / `SD_PICKUP_REDPASS`; our own sprites (§6.3). Placed by Doom's editor numbers 6 and 13. |
| `SD_Stimpack`, `SD_Medikit`, `SD_HealthBonus`, `SD_ArmorBonus`, `SD_GreenArmor`, `SD_BlueArmor`, `SD_Allmap` | the Doom class each *replaces* | The campaign's health, armour and area map (D80, `zscript/sd/pickups.zs`): Doom's pickups with our sprite, line (`SD_GOT_*`) and, for the armours, HUD icon; nothing else changes (§6.3, "The campaign pickups, installed by D80"). |
| `SD_StatusBar` | `DoomStatusBar` | The status bar (T24), registered by `MAPINFO → GameInfo → StatusBarClass`. Doom's bar unchanged; overrides only `DrawPaused`, to draw the pause sign `LANGUAGE` names per language. Contract §6.5.1, reasons ADR 010. |

The bestiary's numbers, states, sounds and the reasons for each are
`docs/engine/BESTIARY.md`; that file is their owner, as `BALANCE.md` is the
arsenal's.

**Slot 1 since D40 (2026-10-13): the ice axe.** The CEO replaced the
sapper's shovel with an ice axe (piolet, «ледоруб»), knowing the Mercader
association (`docs/PRD.md` D40). It is a rename, not a new weapon: the
numbers stay the shovel's (`BALANCE.md` §4), the editor number stays
**21001** so both maps keep working unchanged, the class still `replaces
Fist`, and it is still found on MAP01's dorm rack, never issued. Every name
that said "shovel" changes; this table is the contract `art-director` and
`sound-designer` name their drafts by:

| What | Was | Is |
|---|---|---|
| Class | `SD_Shovel` | `SD_IceAxe` |
| File | `zscript/weapons/shovel.zs` | `zscript/weapons/ice_axe.zs` |
| Melee action | `A_SD_ShovelSwing` | `A_SD_IceAxeSwing` |
| Constants | `SD_SHOVEL_*` | `SD_ICEAXE_*` (same values) |
| Tag (`LANGUAGE`) | `SD_TAG_SHOVEL` "Sapper's shovel" / «Сапёрная лопата» | `SD_TAG_ICEAXE` "Ice axe" / «Ледоруб» |
| Pickup line | `SD_PICKUP_SHOVEL` | `SD_PICKUP_ICEAXE` "An ice axe." / «Ледоруб.» |
| Obituary | `SD_OB_SHOVEL` | `SD_OB_ICEAXE` "%o met %k's ice axe." / «%o встретил ледоруб %k.» |
| Logical sounds | `sd/weapon/shovel/swing`, `…/hit` | `sd/weapon/iceaxe/swing`, `sd/weapon/iceaxe/hit` |
| Final sound lumps | `SDSHSWG`, `SDSHHIT` | **`SDAXSWG`**, **`SDAXHIT`** (§6.2) |
| Final sprites | `SDSH` A–E held, `SDSP` A pickup | **`SDAX`** A–E held, **`SDAP`** A pickup (§6.3) |
| Map constants | `ED_SHOVEL` (MAP01), `ED_SD_SHOVEL` (MAP02) | `ED_ICE_AXE`, `ED_SD_ICE_AXE` |

"Ice axe" is the plain English name a 1970s mountaineering manual or a
translation of «ледоруб» would print; "piolet" is the French loan English
also uses, kept out of the game as too technical. `SDAX`/`SDAP` and
`SDAXSWG`/`SDAXHIT` were checked free: no lump of `freedoom2.wad` 0.13.0
starts with `SD`, and no other reserved name in §6.2, §6.3 or the bestiary
starts with `SDA`. MAP01's zone `shovel_rack` (a sector of the dorm) was
first left as it was, zone names being `level-designer`'s; since commit
`f3cd8ea` (2026-10-13) it is **`z1_ice_axe_rack`**, the `z1_` prefix
filing it under Z1 for `tools/route.py` (`docs/levels/MAP01-zarya-7.md`
§17.15).

**Engine pass, 2026-10-13** (the PM,
`docs/qa/evidence/2026-10-13_2039_d40-d43-engine-pass.md`): walking into
MAP01's dorm rack prints "An ice axe." and `printinv` lists `SD_IceAxe`.
The sprites seen were Freedoom's placeholders; `SDAX`/`SDAP` and
`SDAXSWG`/`SDAXHIT` are drafts at the CEO's gate.

**The blue pass (MAP02, 2026-10-14).** The metro's key (MAP02 since D62,
built as MAP03) is the station duty officer's pass
(`docs/levels/MAP02-metro.md` §5): editor number 5 on the
floor of the substation, and a blast door with `Door_LockedRaise (4, 16, 0,
2, 0)`, lock 2. It was Doom's `BlueCard` with Doom's words; it is ours now,
and **the map did not change**.

| What | Value |
|---|---|
| Class | `SD_BluePass : BlueCard replaces BlueCard`, `zscript/sd/keys.zs` |
| Editor number | none of its own: Doom's **5** spawns `BlueCard`, which the engine replaces with `SD_BluePass`. `level-designer` keeps `ED_BLUE_CARD = 5` |
| Lock | **2**, unchanged: GZDoom's own `lockdefs.txt`, no `LOCKDEFS` of ours |
| Pickup line | `SD_PICKUP_BLUEPASS` = "Blue pass." / «Синий пропуск.» (an id of ours: Freedoom's DEHACKED overrides `GOTBLUECARD`, ADR 003) |
| Locked-door line (MAP02) | engine id `PD_BLUECO`, overridden in `LANGUAGE`: "You need a blue pass to activate this object" / «Для применения нужен синий пропуск» (was "…blue card…" / «…нужна синяя карта») |
| Locked-door line, direct press | engine id `PD_BLUEC`, overridden too ("…to open this door" / «Для открытия нужен синий пропуск»), but **on Freedoom its DEHACKED wins** (below) |
| Sprite | `BKEY`, inherited from `BlueCard`, drawn by Freedoom; no §5.1 row because no state of ours names it. When `art-director` delivers the pass, a `Spawn` state naming the new lump goes into `keys.zs` and a name is reserved in §6.3 |
| Status bar | the blue-key slot (`STKEYS0`), drawn by `DoomStatusBar.DrawBarKeys` through `CheckKeys(2)` |

How lock 2 decides, read in GZDoom g4.14.2's source (tag `g4.14.2`; the
`lockdefs.txt` text in the installed `gzdoom.pk3`). **VERIFIED as code,
NOT VERIFIED in the engine:**

- `gzdoom.pk3 → lockdefs.txt` defines `Lock 2 Doom { BlueCard Message
  "$PD_BLUEC" RemoteMessage "$PD_BLUECO" Mapcolor 0 0 255 }`.
- `P_CheckKeys` (gzdoom: src/gamedata/a_keys.cpp) asks each key of the lock
  `OneKey::check`, which walks the player's inventory and accepts an item
  when `item->IsA(key)` **or** `item->GetSpecies() == key->TypeName`.
  `DObject::IsA` is `type == GetClass()` (gzdoom: src/common/objects/dobject.h):
  the exact class, **not** a subclass. So inheritance alone does **not**
  open the door: an `SD_BluePass` without a Species would leave the metro
  (MAP02) unfinishable.
- `AActor::GetSpecies` (gzdoom: src/playsim/p_mobj.cpp) returns `Species` when
  set and otherwise the class's own name (the walk up the parents is for
  monsters only). `SD_BluePass` sets `Species "BlueCard"`, and lock 2's
  key is `BlueCard`: they match. The same `check` runs for the status
  bar's key slot and for the automap's key colour (`P_GetMapColorForKey`),
  so both show the pass as the blue key. Every other lock that lists
  `BlueCard` (130, "any blue key") accepts it too.
- `replaces` is not consulted by the lock: `ParseLock` resolves `BlueCard`
  with `PClass::FindActor`, which returns the class itself.
- The console's `give BlueCard` hands over Doom's real `BlueCard`, not ours:
  `GiveInventory(…, givecheat = true)` spawns with `NO_REPLACE`
  (`gzdoom.pk3 → zscript/actors/inventory_util.zs`). An engine check of the
  pass says **`give SD_BluePass`**.

Which message, and why `LANGUAGE` and not `LOCKDEFS`. A lock prints its
`Message` when the line is the door itself and its `RemoteMessage` when the
line works a door by tag: `EV_DoDoor` calls `P_CheckKeys (thing, lock, tag
!= 0)` (gzdoom: src/playsim/mapthinkers/a_doors.cpp). The metro's blast door is tag
4, so the player reads **`PD_BLUECO`**, the line the CEO saw in Russian
(«Для применения нужна синяя карта»). Freedoom 0.13.0's DEHACKED rewrites
`PD_BLUEC` ("Blue passcard needed for this door.") but **not** `PD_BLUECO`,
so a `LANGUAGE` override of `PD_BLUECO` reaches the player in both
languages, and that is the whole change. A DEHACKED string sits in the
string table's override layer, consulted before any language
(`FStringTable::UpdateLanguage`, gzdoom: src/common/engine/stringtable.cpp), so
our `PD_BLUEC` only shows on `doom2.wad`; on Freedoom a **tag-0** blue door
would print Freedoom's English line in both languages. No map has one. If
one is ever built, the fix is a `LOCKDEFS` of ours redefining lock 2 with
`SD_` message ids (`ParseLock` replaces a lock by number, `Locks.InsertNew`);
it is not written today because nothing needs it (T25).

Engine checks for the PM (D26), the metro (MAP02) at skill 3, `+logfile`:

| # | Do | What must show |
|---|---|---|
| P1 | `summon BlueCard`, walk onto it (or walk to the pass at the substation) | the pickup line "Blue pass."; `printinv` lists `SD_BluePass`, not `BlueCard`; the blue key on the status bar |
| P2 | at the blast door (`docs/levels/MAP02-metro.md` §14.5 K2, `warp 1312 896`, facing 180), `+use` with no pass | the door stays shut and prints "You need a blue pass to activate this object" |
| P3 | `give SD_BluePass`, `+use` (**not** `give BlueCard`: that gives Doom's class and proves nothing about ours) | the door opens and stays open |
| P4 | `language ru`, then P2 again on a fresh load | «Для применения нужен синий пропуск»; P1 in Russian prints «Синий пропуск.» |
| P5 | the automap (`am_cheat 2` or `iddt` twice) | the pass drawn in the blue key's colour |
| P6 | the log | no `Script error`, nothing about `SD_BluePass`, `Species` or `keys.zs` |

`tests/test_blue_pass.py` pins the class, the include, the strings in both
languages and lock 2's acceptance, modelled on `OneKey::check`; it reads the
installed `gzdoom.pk3`'s `lockdefs.txt` where there is one and skips that
one comparison where there is not (CI).

### 6.1 Editor numbers (DoomEdNums)

**Soviet Doom reserves 21000–21999.** The earlier proposal of 14000–14999
was wrong and is withdrawn: GZDoom assigns 14001–14067 to `AmbientSound` /
`SoundSequence` and 14101–14165 to `MusicChanger` (verified 2026-10-12
against <https://zdoom.org/wiki/Standard_editor_numbers>). Rationale and
the full check are in `docs/engine/adr/002-arsenal-and-editor-numbers.md`.

| Sub-range | For |
|---|---|
| 21000–21019 | weapons |
| 21020–21039 | ammo and items |
| 21100–21199 | enemies |
| 21200–21299 | decorations |

| Number | Class |
|---|---|
| 21001 | `SD_IceAxe` (was `SD_Shovel`; number unchanged by D40) |
| 21002 | `SD_Tokarev` |
| 21003 | `SD_Izh` |
| 21004 | `SD_Ppsh` |
| 21005 | `SD_Rpg7` |
| 21006 | `SD_Roks3` |
| 21007 | `SD_HandKatyusha` |
| 21008 | `SD_Akm` (D116; slot 4's second weapon, replaces nothing) |
| 21009 | `SD_Rgd5` (V3, ADR 012; slot 8, the RGD-5 hand grenade: the pouch of two) |
| 21020 | `SD_AkmAmmo` (D116; the AKM's magazine, the first number of the ammo block: ADR 011) |
| 21021 | `SD_Rgd5Ammo` (V3, ADR 012; one loose RGD-5, which also gives the weapon) |
| 21022 | `SD_Rgd5Box` (V3, ADR 012; a crate of four RGD-5s) |
| 21100 | `SD_ReichRifleman` (also spawned by Doom's 3004) |
| 21101 | `SD_LegionTrooper` (also 9) |
| 21102 | `SD_Stormtrooper` (also 3001) |
| 21103 | `SD_ReichHound` (also 3002) |
| 21104 | `SD_Doughboy` (also 3005) |
| 21105 | `SD_Panzermensch` (also 69) |
| 21106 | `SD_General` (also 16) |
| 21107 | `SD_PanzermenschSchwer` (also 3003) |
| 21108 | *reserved*: a cloaked hound replacing `Spectre` (58), not implemented (`BESTIARY.md` §6) |
| 21110 | `SD_LegionGunner` (also 65; D116) |
| 21111 | `SD_LibertyColossus` (also 7; D116) |
| 21112 | `SD_Consortium` (its own number only; D116) |
| 21113 | `SD_ChromeGeneral` (its own number only; D123, the colossus variant) |
| 21200 | `SD_Radio`, the first decoration (§6.7). **Assigned here, not yet in `MAPINFO`**: the line `21200 = SD_Radio` is the PM's to add (the file was another agent's on 2026-10-13); until it lands, a map that places 21200 spawns nothing there |
| 21201 | `SD_Loudspeaker`, the propaganda radio's loudspeaker (V3 B5, D124; §6.14), in `MAPINFO` |

Every enemy also `replaces` its Doom counterpart, so a map may place either
number and both spawn ours; `level-designer` can keep MAP01's Doom numbers
or switch to these, the result in the engine is the same. Doom monsters the
bestiary does **not** replace (58 spectre and the rest of Doom II's roster,
`BESTIARY.md` §12) still spawn Freedoom's actor. Since
D116 the chaingunner (65) spawns `SD_LegionGunner` and the Spider
Mastermind (7) `SD_LibertyColossus`; no map of ours places 65 or 7 (checked
on the built maps, 2026-10-22): the P4 maps place ours by 21110-21113.

Removed from the game (mapped to `None` in `DoomEdNums`): **82** super
shotgun and **2005** chainsaw. The arsenal was seven weapons (D13); the AKM
(D116) is the eighth, beside the PPSh-41 in slot 4; the RGD-5 (V3, ADR 012)
the ninth, alone in slot 8.

Numbers are assigned only in MAPINFO's `DoomEdNums` block — the only method
available to a ZScript class.

### 6.2 Sounds (SNDINFO)

The code never names a lump; it names a logical sound, and `SNDINFO` maps
it to a lump. **`sound-designer` owns the right-hand column.** Two kinds of
lump: our own, a file `assets/sounds/<set>/<LUMP>.ogg` packed as
`sounds/<LUMP>.ogg` (the build drops the set folder, as for textures; lump
`<LUMP>`); or a Freedoom (IWAD) lump as a placeholder, read from the IWAD
at run time and never redistributed. Replacing a placeholder changes one
line of `SNDINFO` and no ZScript; a new event needs a hook as well.

**The arsenal since N9 (2026-10-15):** the 25 weapon sounds the CEO approved
in D74, mastered by `tools/audio/master_weapon_sfx.py` and installed in
`assets/sounds/weapons/` (`docs/sound/WEAPON-SOUNDS.md` §10, licence rows
in `docs/art/LICENSES.md` § "Weapon sounds"), and since N9e (2026-10-20)
the IZh-58's shot `SDIZFIR` in take B (D83) and the D94 alternatives of
`tools/audio/gen_weapon_alts.py` (`master_weapon_sfx.py --alts`;
`WEAPON-SOUNDS.md` §10.6): the TT-33's and the ice axe's pickups, the
IZh-58's reload and the ROKS-3's jet. The IZh-58's pickup kept Doom's
generic one (D94: NO) until D125 (2026-10-23) installed two takes of the
world-sounds round (`tools/audio/master_world_sfx.py`, `docs/sound/WORLD-SOUNDS.md`,
which also lists the player, door, switch, pickup, lift and teleporter
sounds D125 put on the engine's own names).

| Logical name | Lump | Played by |
|---|---|---|
| `sd/weapon/iceaxe/swing` | `SDAXSWG` | `SD_IceAxe` Fire, first frame (`SDAX B 5`), `CHAN_WEAPON` |
| `sd/weapon/iceaxe/hit` | `SDAXHIT` | `A_SD_IceAxeSwing` when the blow finds a target |
| `sd/weapon/iceaxe/wall` | `SDAXWAL` | `SD_IceAxePuff`'s `AttackSound` (the puff spawned on a wall, floor or ceiling) |
| `sd/weapon/iceaxe/pickup` | `$random`: `SDAXPKP1`, `SDAXPKP3` (D94) | `Inventory.PickupSound` (since N9e) |
| `sd/weapon/tokarev/fire` | `SDTTFIR` | `SD_Tokarev` `AttackSound` |
| `sd/weapon/tokarev/dry` | `SDTTDRY` | `A_SD_WeaponReady` → `SD_WeaponSounds.DryClick` |
| `sd/weapon/tokarev/reload` | `SDTTRLD` | parked by D47; on the branch `v3-reload` the `Reload` state, with `sd_reloads` on (§6.15) |
| `sd/weapon/tokarev/pickup` | `$random`: `SDTTPKP1`, `SDTTPKP2` (D94) | `Inventory.PickupSound` (since N9e) |
| `sd/weapon/izh/fire` | `SDIZFIR` (take B, D83; `DSSHOTGN` until N9e) | `SD_Izh` `AttackSound` |
| `sd/weapon/izh/reload` | `SDIZRLD` (D94 alt3; `DSSGCOCK` until N9e) | `SD_Izh` Reload, first frame |
| `sd/weapon/izh/dry` | `SDIZDRY` | `A_SD_WeaponReady` |
| `sd/weapon/izh/pickup` | `$random`: `SDIZPKP1`, `SDIZPKP2` (D125; Doom's `misc/w_pkup` until then) | `Inventory.PickupSound` (since D125) |
| `sd/weapon/ppsh/fire` | `SDPPFIR` | `SD_Ppsh` `AttackSound` |
| `sd/weapon/ppsh/pickup` | `SDPPPKP` | `Inventory.PickupSound` |
| `sd/weapon/ppsh/dry` | `SDPPDRY` | `A_SD_WeaponReady` |
| `sd/weapon/ppsh/reload` | `SDPPRLD` | parked by D47; on `v3-reload` the `Reload` state (§6.15) |
| `sd/weapon/rpg7/fire` | `SDRPFIR` | `SD_Pg7Grenade` `SeeSound` |
| `sd/weapon/rpg7/explode` | `SDRPEXP` | `SD_Pg7Grenade` `DeathSound` |
| `sd/weapon/rpg7/reload` | `SDRPRLD` | `SD_Rpg7` Fire, `SDRL B 10` (the launch frame split 4 + 10), `CHAN_WEAPON` |
| `sd/weapon/rpg7/pickup` | `SDRPPKP` | `Inventory.PickupSound` |
| `sd/weapon/rpg7/dry` | `SDRPDRY` | `A_SD_WeaponReady` |
| `sd/weapon/roks3/fire` | `$random`: `SDRKFIR1`-`SDRKFIR3` (D94; `DSFLAME` until N9e) | `A_SD_FireRoks3`, `CHAN_WEAPON`, restarted every 3 tics: a take per restart |
| `sd/weapon/roks3/pickup` | `SDRKPKP` | `Inventory.PickupSound` |
| `sd/weapon/roks3/dry` | `SDRKDRY` | `A_SD_WeaponReady` |
| `sd/weapon/roks3/reload` | `SDRKRLD` | parked by D47; on `v3-reload` the `Reload` state (§6.15) |
| `sd/weapon/katyusha/charge` | `SDHKCHG` | `SD_HandKatyusha` Fire, `SDHK A 20`, `CHAN_WEAPON` |
| `sd/weapon/katyusha/fire` | `SDHKFIR` | `A_SD_FireKatyusha`, `CHAN_WEAPON` |
| `sd/weapon/katyusha/burst` | `SDHKEXP` | `SD_KatyushaRocket` `DeathSound` |
| `sd/weapon/katyusha/reload` | `SDHKRLD` | `SD_HandKatyusha` Fire, a 0-tic frame before `SDHK B 20 A_ReFire`, `CHAN_5` (`SD_KATYUSHA_RELOAD_CHANNEL`) so the salvo is not cut |
| `sd/weapon/katyusha/pickup` | `SDHKPKP` | `Inventory.PickupSound` |
| `sd/weapon/katyusha/dry` | `SDHKDRY` | `A_SD_WeaponReady` |

Every weapon has its own `PickupSound`: the ice axe and the TT-33 since
N9e (D94), the IZh-58 since D125 (it played Doom's `misc/w_pkup` until then). **No hook changes a tic** (D39): the RPG-7's
14-tic launch frame became 4 + 10 on the same sprite, and the Katyusha's
reload is a 0-tic frame. **The empty click** (`SD_WeaponSounds.DryClick`,
called by each gun's `A_SD_WeaponReady` before `A_WeaponReady` on the same
frame) plays on the tic the fire button goes down while
`CheckAmmo(PrimaryFire, false)` says the gun cannot fire; with
`autoSwitch` false it only counts, so the engine's own switch to another
weapon (`BALANCE.md` §4.1) is untouched. Engine behaviour relied on and
not yet seen in our engine pass (puff sounds, the click, the channels):
`WEAPON-SOUNDS.md` §10.3, with what to listen for in §10.4.
`tests/test_arsenal.py` holds `SNDINFO` and the code in step (every name
played is defined, every name defined is played but the three parked
reloads); `tests/test_weapon_sfx_install.py` holds the install.

The slot-1 swing was **deliberately silent** from 2026-10-13 until N9.
It pointed at `DSSAWUP`, the chainsaw start-up, and the CEO heard a
chainsaw; Freedoom's only swing-through-air lump is `DSSKESWG`, the
revenant's melee wind-up. `tests/test_arsenal.py` still fails if any
placeholder points at a `*SAW*` lump. See
`docs/engine/adr/003-ammo-naming-and-the-silent-shovel.md` (its title keeps
the old name: an ADR is a dated record). The ice axe (D40) renamed the
logical names and the two final lumps (`SDSHSWG` → `SDAXSWG`, `SDSHHIT` →
`SDAXHIT`).

**The bestiary (F5): 47 logical names, `sd/mon/<actor>/<event>`.** Each line
of `SNDINFO` names the lump it plays: since N9e (2026-10-20; D83, D86,
D91, D96) ours for 43 of them, installed by `tools/audio/master_enemy_sfx.py` in
`assets/sounds/enemies/` (`docs/sound/ENEMY-SOUNDS.md` §5.12, licence rows
in `docs/art/LICENSES.md` § "Enemy sounds"), eight of them voices (the
Chatterbox takes of D91 and D96: the rifleman's idle, sight and death, the
trooper's idle, sight and pain, the General's sight and his order); for the
other four, voices still waiting for a take (the rifleman's pain, the
trooper's death, the General's pain and death), the Freedoom placeholder,
with the final lump in its comment. The final names
are the cards of `docs/sound/ENEMY-SOUNDS.md`, which `tests/test_bestiary.py`
holds equal. The count is 47, not the 52 that BESTIARY v0 printed
(`BESTIARY.md` §12). Projectiles own their launch (`SeeSound`) and impact
(`DeathSound`) sounds; a gib plays `xdeath` explicitly instead of Doom's
`misc/gibbed`.

**Several takes of one sound: `$random` (N9e, D86).** Where the CEO
approved several takes, they all ship and the name the code plays is a
`$random` alias over `<name>/<take>` lines, the syntax of gzdoom.pk3's own
`$random grunt/sight { grunt/sight1 grunt/sight2 grunt/sight3 }` (read in
g4.14.2's `filter/game-doomchex/sndinfo.txt`; ZDoom wiki SNDINFO): the
engine picks one member each time. The lumps take the card's name with its
last letter replaced by the take's number (`SDSTOPA1`-`SDSTOPA3` for
`SDSTOPAI`). No ZScript changes: `SeeSound`, `PainSound`, `DeathSound` and
`A_StartSound` take the alias as they took the single name. Thirteen groups
(since D96; seven at N9e): `sd/mon/reichrifleman/attack` (`SDRRIAT1`-`3`),
`sd/mon/stormtrooper/pain` (`SDSTOPA1`-`3`), `sd/mon/stormtrooper/death`
(`SDSTODT1`-`3`), `sd/mon/panzermensch/pain` (`SDPZRPA1`-`3`), the voices
`sd/mon/reichrifleman/active` (`SDRRIAC1`-`3`, D96),
`sd/mon/reichrifleman/sight` (`SDRRISI1`, `3`, `4`, `5`, `6`; D91 and D96),
`sd/mon/legiontrooper/active` (`SDLTRAC1`-`6`; D91 and D96),
`sd/mon/legiontrooper/sight` (`SDLTRSI1`-`4`, D96),
`sd/mon/legiontrooper/pain` (`SDLTRPA1`-`2`, D96) and
`sd/mon/general/summon` (`SDGENSU1`-`2`, D96), and three of the beds
below. The weapons use the same form since D94 (above).
`tests/test_arsenal.py` checks every group's members are defined, under the
group's name, never nested; **NOT VERIFIED in our engine** (the PM's pass).

**The beds (N9e, D83, D86): `sd/bed/<actor>/<event>`, parked.** The
non-vocal layers that go under the voices (`ENEMY-SOUNDS.md` §5.10) are
packed and named, and nothing plays them: each will be mixed under its
voice take when the CEO approves the takes (D87), and the voice lump keeps
the card's name. Lump: `SD` + actor + the event's initial + `B` + take.
`tests/test_arsenal.py` treats `sd/bed/` as parked, as it treats the three
reloads.

| Bed (logical `sd/bed/…`) | Lump(s) | Goes under |
|---|---|---|
| `reichrifleman/death` | `SDRRIDB1` (D83) | `sd/mon/reichrifleman/death` |
| `reichrifleman/pain` | `$random`: `SDRRIPB1`-`SDRRIPB3` (D86) | `sd/mon/reichrifleman/pain` |
| `legiontrooper/active` | `SDLTRAB1` (D83) | `sd/mon/legiontrooper/active` |
| `legiontrooper/sight` | `SDLTRSB1` (D83) | `sd/mon/legiontrooper/sight` |
| `legiontrooper/pain` | `$random`: `SDLTRPB1`-`SDLTRPB3` (D86) | `sd/mon/legiontrooper/pain` |
| `legiontrooper/death` | `$random`: `SDLTRDB1`-`SDLTRDB3` (D86) | `sd/mon/legiontrooper/death` |
| `general/pain` | `SDGENPB1` (D83) | `sd/mon/general/pain` |
| `general/death` | `SDGENDB1` (D83) | `sd/mon/general/death` |

| Actor (logical `sd/mon/…`) | Event → lump it plays (since N9e); *still a placeholder → final lump* |
|---|---|
| `reichrifleman` | attack `$random` `SDRRIAT1`-`3` (D86); active `$random` `SDRRIAC1`-`3` (D96 voice); sight `$random` `SDRRISI1`, `3`, `4`, `5`, `6` (D91, D96 voice); death `SDRRIDTH` (D96 voice); xdeath `SDRRIXDT`; *pain `DSPOPAIN` → `SDRRIPAI`* |
| `legiontrooper` | attack `SDLTRATK` (D86 alt2); active `$random` `SDLTRAC1`-`6` (D91, D96 voice); sight `$random` `SDLTRSI1`-`4` (D96 voice); pain `$random` `SDLTRPA1`-`2` (D96 voice); xdeath `SDLTRXDT`; *death `DSPODTH2` → `SDLTRDTH`* |
| `stormtrooper` | active `SDSTOACT`; sight `SDSTOSIT`; melee `SDSTOMEL`; missile `SDSTOMIS`; explode `SDSTOEXP`; pain `$random` `SDSTOPA1`-`3` (D86); death `$random` `SDSTODT1`-`3` (D86); xdeath `SDSTOXDT` |
| `reichhound` | active `SDHNDACT`; sight `SDHNDSIT`; attack `SDHNDATK`; pain `SDHNDPAI`; death `SDHNDDTH` |
| `doughboy` | active `SDDGBACT`; sight `SDDGBSIT`; melee `SDDGBMEL`; missile `SDDGBMIS`; explode `SDDGBEXP`; pain `SDDGBPAI`; death `SDDGBDTH` |
| `panzermensch` (and the heavy variant) | active `SDPZRACT`; sight `SDPZRSIT`; melee `SDPZRMEL`; missile `SDPZRMIS`; explode `SDPZREXP`; pain `$random` `SDPZRPA1`-`3` (D86); death `SDPZRDTH`; step `SDPZRSTP` |
| `general` | active `SDGENACT`; sight `SDGENSIT` (D96 voice); missile `SDGENMIS`; explode `SDGENEXP`; summon `$random` `SDGENSU1`-`2` (D96 voice, the order `SD_GENERAL_ORDER`); *pain `DSDMPAIN` → `SDGENPAI`; death `DSCYBDTH` → `SDGENDTH`* |

Until N9e the rifleman fired `DSPISTOL`, the TT-33's old stand-in, and the
trooper `DSDSHTGN`; both fire ours now. The General's order was `DSVILSIT`,
a creature's sight sound, because Freedoom has no voice that gives an
order; since D96 it is `sd/mon/general/summon`, two takes of "Vorwarts!"
(`SDGENSU1`-`2`), and no placeholder is knowingly imperfect any more. The
four voices left (rifleman pain, trooper death, General pain and death)
wait for a take.

**P4 sounds (D116, 2026-10-22).** The P4 actors play their **own logical
names**, and each name maps to a lump the mod already ships (or the IWAD
stand-in the General's death already uses) until `sound-designer` records
theirs. The final lump is in the `SNDINFO` comment after `->`, as for the
F5 placeholders; replacing one changes the right-hand column only. They
are not part of the bestiary's 47 (`gen_sfx.py`'s cards): `BESTIARY.md`
§12 counts them per row, and `tests/test_ep2_enemies.py`,
`test_ep3_boss.py` and `test_akm.py` hold them to the code.

| Logical name | Plays today | Final lump |
|---|---|---|
| `sd/weapon/akm/fire` | `SDPPFIR` (the PPSh-41's round) with `$pitchset sd/weapon/akm/fire 0.85` (**NOT VERIFIED** in the engine; the keyword is in g4.14.2's `gzdoom.exe`) | `SDAKFIR` (the `$pitchset` line goes with it) |
| `sd/weapon/akm/dry`, `…/pickup` | `SDPPDRY`, `SDPPPKP` | `SDAKDRY`, `SDAKPKP` |
| `sd/weapon/akm/reload` (V3 reloads, §6.15) | `SDPPRLD` (the PPSh-41's drum change) | `SDAKRLD` |
| `sd/mon/legiongunner/sight`, `…/active`, `…/pain`, `…/death` | the trooper's takes `SDLTRSI3`, `SDLTRAC3`, `SDLTRPA1`, `SDLTRDT1` | `SDLGNSIT`, `SDLGNACT`, `SDLGNPAI`, `SDLGNDTH` |
| `sd/mon/legiongunner/attack`, `…/xdeath` | `SDPPFIR`, `SDLTRXDT` | `SDLGNATK` (a slower, heavier M1919), `SDLGNXDT` |
| `sd/mon/colossus/sight`, `…/active`, `…/pain`, `…/death` | the General's `SDGENSIT`, `SDGENACT`, `SDGENPA1`, IWAD `DSCYBDTH` | `SDCOLSIT`, `SDCOLACT`, `SDCOLPAI`, `SDCOLDTH` (metal groaning, not a voice) |
| `sd/mon/colossus/step`, `…/stomp`, `…/flame` | `SDPZRSTP`, `SDRPEXP`, `SDRKFIR1` | `SDCOLSTP`, `SDCOLSTM`, `SDCOLFLM` |
| `sd/mon/consortium/sight`, `…/active`, `…/pain`, `…/death` | the Panzermensch's `SDPZRSIT`, `SDPZRACT`, `SDPZRPA3`, IWAD `DSCYBDTH` | `SDCNSSIT`, `SDCNSACT`, `SDCNSPAI`, `SDCNSDTH` |
| `sd/mon/consortium/call`, `…/breach`, `…/step`, `…/flame` | `SDGENSU1`, `SDPZRDTH`, `SDPZRSTP`, `SDRKFIR2` | `SDCNSCAL`, `SDCNSBRC`, `SDCNSSTP`, `SDCNSFLM` |

**V3 sounds (2026-10-23): the RGD-5** (ADR 012), the same scheme: its own
logical names over lumps the mod ships, the final lump after `->` in
`SNDINFO`; `tests/test_rgd5.py` holds them to the code. Why each, and what
`sound-designer` should record: `docs/engine/2026-10-23_V3_rgd5.md` §4.

| Logical name | Plays today | Final lump |
|---|---|---|
| `sd/weapon/rgd5/pin` | `SDTTDRY` (the TT-33's hammer click) | `SDRGPIN` |
| `sd/weapon/rgd5/throw` | `SDAXSWG` (the ice axe's swing) | `SDRGTHR` |
| `sd/weapon/rgd5/bounce` | `SDAXWAL` (the pick on stone), `SD_Rgd5Grenade`'s `BounceSound` | `SDRGBNC` |
| `sd/weapon/rgd5/explode` | `SDRPEXP` (the PG-7V's burst) with `$pitchset sd/weapon/rgd5/explode 1.2` (**NOT VERIFIED**) | `SDRGEXP` (the `$pitchset` line goes with it) |
| `sd/weapon/rgd5/pickup` | `SDTTPKP2` (the TT-33 out of its holster) | `SDRGPKP` |

**V3 sounds (2026-10-23): the propaganda radio** (B5, D124), ours: 20 lumps
in `assets/sounds/radio/`, installed by `tools/audio/install_radio.py`
(rows in `docs/art/LICENSES.md` § "Propaganda radio"), played by
`SD_Loudspeaker` (§6.14). Every name carries `$rolloff … linear 128 768`.

| Logical name | Lump | Played by |
|---|---|---|
| `sd/radio/line/01` … `sd/radio/line/16` | `SDRAD01` … `SDRAD16` (one take each; `SDRAD16` is the six pips and then the line) | `SD_Loudspeaker`, `CHAN_VOICE`, from its shuffled playlist |
| `sd/radio/jingle` | `$random` of `sd/radio/jingle/1`-`3` = `SDRADJ1`-`SDRADJ3` | `SD_Loudspeaker` on turning on (`arg4` 0); `arg4` 1-3 names one |
| `sd/radio/bed` | `SDRADBED` (6 s seamless loop) | `SD_Loudspeaker` with the bed flag, `CHAN_BODY`, `CHANF_LOOPING` |

The bosses' projectiles inherit their parents' sounds (the RPG-7's, the
General's shell's, none for the flame). The design docs proposed
seven-letter final names for the colossus and the Consortium (`SDLCSIT`,
`SDCNSIT`); this table gives the eight-letter forms that follow the
bestiary's `SD` + actor + event pattern, and it is the contract.

### 6.3 Sprites to be drawn (contract with `art-director`)

A Doom sprite lump is `NAME` + frame letter + rotation digit, 8 characters
max; `0` as the rotation means "same picture from every angle", which is
what HUD weapon sprites use. F4 runs on Freedoom lumps; the names below are
**reserved** for the real artwork and are free of any lump in
`freedoom2.wad` (checked: the IWAD has no lump starting with `SD`).

| Weapon | Held (HUD) | Muzzle flash | Pickup | Projectile |
|---|---|---|---|---|
| Ice axe (D40; was the sapper's shovel, `SDSH`/`SDSP`) | `SDAX` A–E | — | `SDAP` A | — |
| TT-33 Tokarev | `SDTT` A–E | `SDTF` A | `SDTP` A | — |
| IZh-58 | `SDIZ` A–F | `SDIF` A–B | `SDIP` A | — |
| PPSh-41 | `SDPP` A–B | `SDPF` A–B | `SDPQ` A | — |
| RPG-7 | `SDRL` A–B | `SDRF` A–D | `SDRP` A | `SDPG` A (8 rotations), burst `SDPX` A–C (D82) |
| ROKS-3 | `SDRK` A–B | `SDKF` A–B | `SDKP` A | `SDFJ` A–B (reserved as `SDFL` until D82), impact `SDFX` A–E |
| Hand Katyusha | `SDHK` A–C | `SDHF` A–B | `SDHP` A | `SDKR` A (8 rotations), burst `SDPX` A–C (D82) |

Frame counts follow the Doom weapon each one replaces, so the existing state
machines need no edit when the art lands — only the four-letter name in
each state line.

**Installed since D48 (2026-10-14): the world pickups only.** The CEO
approved hand E and six weapons as drawn, then, after playing MAP01 with the
draft overlay (§6.9) the same day, found the hand deformed: the held and
flash frames, which show it, wait for the hands to be redrawn. What ships:

| Weapon | Pickup lump | File | `Spawn` state (was) |
|---|---|---|---|
| Ice axe | `SDAPA0`, option C "upright, as in a rack" | `assets/sprites/ice_axe/SDAPA0.png` | `SDAP A -1` (`CSAW A -1`) |
| TT-33 | `SDTPA0` | `assets/sprites/tt33/SDTPA0.png` | `SDTP A -1` (`PIST A -1`) |
| IZh-58 | `SDIPA0` | `assets/sprites/izh/SDIPA0.png` | `SDIP A -1` (`SHOT A -1`) |
| PPSh-41 | `SDPQA0` | `assets/sprites/ppsh/SDPQA0.png` | `SDPQ A -1` (`MGUN A -1`) |
| RPG-7 | `SDRPA0` | `assets/sprites/rpg7/SDRPA0.png` | `SDRP A -1` (`LAUN A -1`) |
| ROKS-3 | `SDKPA0` | `assets/sprites/roks3/SDKPA0.png` | `SDKP A -1` (`PLAS A -1`) |

Each PNG is byte-identical to its render in `work/art/weapons/<weapon>/`
(`gen_weapon.py`, hand E), RGBA, with its `grAb` offsets inside the file
(about `left = width / 2`, `top` = the floor line, as the IWAD's pickups);
the build drops the set folder, so the engine sees `sprites/SDAPA0.png`.
Only the sprite name changed: frame letter, tics and every other state line
are as before, held by `tests/test_weapon_sprites.py` against the state
machines as they stood before D48. Not installed by D48: every held and
flash frame (`SDAX`, `SDTT`/`SDTF`, `SDIZ`/`SDIF`, `SDPP`/`SDPF`,
`SDRL`/`SDRF`, `SDRK`/`SDKF`; the TT-33's followed with N17, the PPSh-41's with D79, the IZh-58's, RPG-7's and ROKS-3's with D84 and the ice axe's with D88, below), the hand Katyusha (`SDHK`/`SDHF`/`SDHP`, to be redrawn,
D48; its frames and pickup followed with D84), the RPG-7's `_proposed` reload frames (`SDRL` C-D) and the
projectiles. Licence rows: `docs/art/LICENSES.md`, "Weapon pickups".

**The TT-33 in hand, redone with Gemini (D111, installed by D123, 2026-10-23).**
The CEO asked for the pistol to match the other six weapons ("rehaz los
sprites de la pistola también porque ahora no queda en tanta consonancia
con el resto de armas", "redo the pistol sprites too, because now it does
not match the other weapons so well", D111) and approved the result ("Ok T33", D123,
`docs/art/previews/2026-10-23_P4_tt33-gemini.html`). Four lumps ship in
`assets/sprites/tt33/`, beside the pickup `SDTPA0`, byte-identical to
`work/art/weapons/hand_G/tt33/`: the project lead's Gemini pair (ready,
firing; a bare hand on magenta) processed by `tools/art/gemini_frames.py
tt33` with the arsenal's constants (palette v2, x1.6 Freedoom's `CHGGA0`
above the bar, the D79 kick), the muzzle on the crosshair. Each PNG is RGBA
with hard alpha, all four in palette v2, with its `grAb` offsets;
`tokarev.zs` moves no weapon sprite in code (no `A_WeaponOffset`, no
`Weapon.YAdjust`).

| Lump | State | Size | `grAb` (left, top) | Above the status bar |
|---|---|---|---|---|
| `SDTTA0` | `Ready`, `Select`, `Deselect`; `Fire`'s first 4 tics | 77 × 92 | −154, −96 | 56 px (Freedoom's `PISGA0`: 55, D57's ±10 % band) |
| `SDTTB0` | `Fire`: the shot (`A_GunFlash`, `A_FireBullets`) and `A_ReFire` | 77 × 92 | −156, −93 | 59 px (the kick up and right) |
| `SDTTC0` | `Fire`: settling, half the kick | 77 × 92 | −155, −94 | 58 px |
| `SDTFA0` | `Flash` (`Bright`, `A_Light1`), over `SDTTB0`'s muzzle | 41 × 36 | −138, −77 | 75 px |

**History.** From N17 (2026-10-15) to D123 the same four names held our
TT-33 rendered on the 3D rig in Freedoom's own pistol hands (`PISGA0`-`PISGC0`,
recoloured: R3-A1, D61; approved in hand, D63; `tools/art/hand_study.py`
`build_tt33_fd`, kept): the PK3's only art derived from Freedoom's pixels.
Since D123 no sprite of the PK3 carries a Freedoom pixel; Freedoom's
BSD-3 notice still ships for the three enemy gib sounds that edit
Freedoom's `DSSLOP` (`docs/art/LICENSES.md`, "Base IWAD").

Only the four-letter names ever changed, `PISG` → `SDTT` and `PISF` →
`SDTF` (N17): frame letters, tics, actions and flow are as they were, held
by `tests/test_tt33_sprites.py` against the state machine as it stood at
HEAD 5c05577, before N17 (and by `tests/test_weapon_sprites.py`, which pins
it since D48). `SDTT` D–E, reserved above, are not drawn: no state uses
them. The draft overlay records `PISG` → `SDTT` and `PISF` → `SDTF` as
installed (§6.9). Licence rows: `docs/art/LICENSES.md`, "Weapon frames: the
TT-33 in hand". **NOT VERIFIED in the engine from the PK3** (D26): the PM's
pass.

**The PPSh-41 in hand, installed by D79 (2026-10-20).** The CEO generated
two images with Google Gemini (bare hands holding the PPSh-41 on flat
magenta: ready, and firing with a muzzle flash); they stay in
`work/art/reference/` and never ship (D77). `tools/art/gemini_frames.py
ppsh` turns them into pixel art (letterbox crop, magenta key, art-grid
downsample, palette v2, the flash cut out of the firing image, Doom size at
x1.6 Freedoom's `CHGGA0` above the bar and Doom's 1.2 pixel aspect) into
`work/art/weapons/hand_G/ppsh/`, with the two fixes D79 asked for after the
engine look of 2026-10-19: (1) **the arms leave the view cleanly**: where
the art is cut by the image's side (the right forearm), it runs on 112 px
past the screen's right edge, its texture mirrored from its last 12
columns (no one-column streaks), dropping as (k/112)³ so it is almost
straight within 4:3 and has curved down out of the canvas before its end:
no opaque pixel on a sprite border shows above the status bar (or the
screen bottom, bar off) within a 16:9 view (54 px past each side of 320)
plus the 16-px horizontal bob (`visible_cuts`); the bottom row is smeared
16 rows under the bar; (2) **recoil**: the firing frame and its flash sit
2 px right and 3 px up (`KICK`, through their `grAb`), so the flash stays
on the fired muzzle. Three lumps ship in `assets/sprites/ppsh/`, beside the
pickup `SDPQA0`, byte-identical to the build (a fresh build reproduces
them byte for byte where the sources exist). RGBA with hard alpha, all
three in palette v2; neither the zs nor anything else moves a weapon
sprite in code.

| Lump | State | Size | `grAb` (left, top) | Above the status bar |
|---|---|---|---|---|
| `SDPPA0` | `Ready`, `Select`, `Deselect`; `Fire`'s first round | 279 × 92 | −152, −96 | 56 px (x1.6 Freedoom's `CHGGA0`, 35) |
| `SDPPB0` | `Fire`'s second round and `A_ReFire` (the kick) | 279 × 92 | −154, −93 | 59 px |
| `SDPFA0` | `Flash` (`Bright`, `A_Light1`), on `SDPPB0`'s muzzle | 35 × 35 | −144, −81 | 71 px |

Only the four-letter names changed, `CHGG` → `SDPP` and `CHGF` → `SDPF`:
frame letters, tics, actions and flow are as they were, held by
`tests/test_ppsh_sprites.py` against the state machine as it stood at HEAD
c3aad1f, before D79 (and by `tests/test_weapon_sprites.py`). `SDPF` B,
reserved above, is not drawn: the `Flash` state has one frame, which
`A_GunFlash` starts on both rounds, so on round A (unkicked) the flash sits
2 px left and 3 px down of where it sits on B's muzzle. The draft overlay
records `CHGG` → `SDPP` and `CHGF` → `SDPF` as installed (§6.9). Licence
rows: `docs/art/LICENSES.md`, "Weapon frames: the PPSh-41 in hand"; the
credits name Google Gemini (`SD_CRED_AI_4`–`_5` since D93, `tools/release.py`
`AI_DISCLOSURE`). **NOT VERIFIED in the engine from the PK3** (D26): the
PM's pass.

**The IZh-58, RPG-7, ROKS-3 and hand Katyusha in hand, installed by D84
(2026-10-20).** The CEO approved the four after seeing them in engine
through the draft overlay
(`docs/art/previews/2026-10-20_1037_F4_five-weapons-gemini-in-engine.png`;
the ice axe, the fifth, waited for its strike to be redrawn and followed
with D88, below). Each was
built as the PPSh-41 was, by `tools/art/gemini_frames.py <weapon>` from
the CEO's Google Gemini images (the IZh-58 has three: ready, firing,
reloading; the others two: ready, firing), which stay in
`work/art/reference/` and never ship (D77), into
`work/art/weapons/hand_G/<weapon>/`: the same pipeline, the same height
(the ready frame's top 56 px above the bar, x1.6 Freedoom's `CHGGA0`, ±2),
the arms leaving the view with no cut edge (`visible_cuts` is 0 on every
lump, bar on and off, 16:9 and the bob), the firing frames kicked by
`KICK` (2 px right, 3 px up) where the gun recoils, the fading flash
frames shrunk about their root. Twenty lumps ship, byte-identical to the
build (a fresh build reproduces them byte for byte where the sources
exist), each folder beside its weapon's world pickup; the hand Katyusha's
in a new `assets/sprites/katyusha/` (its pickup lives with the campaign's
in `pickups/`, below). RGBA with hard alpha, all in palette v2; neither
the zs nor anything else moves a weapon sprite in code.

| Lump | State | Size | `grAb` (left, top) | Above the status bar |
|---|---|---|---|---|
| `SDIZA0` | IZh-58: `Ready`, `Select`, `Deselect`; `Fire`'s first and last two frames; the reload's last (shut) | 266 × 93 | −136, −95 | 57 px |
| `SDIZB0` | `Fire`: the recoil (`KICK`); the reload closing | 260 × 93 | −144, −92 | 60 px |
| `SDIZC0` | `Fire`: settling (half the kick); the reload | 260 × 93 | −143, −93 | 59 px |
| `SDIZD0` | `Reload`: broken open | 275 × 121 | −128, −67 | 85 px |
| `SDIFA0` | `Flash` A (`Bright`, `A_Light1`), on `SDIZA0`'s muzzles | 61 × 42 | −126, −73 | 79 px |
| `SDIFB0` | `Flash` B (`A_Light2`), the flash fading (x0.6) | 37 × 25 | −145, −84 | 68 px |
| `SDRLA0` | RPG-7: `Ready`, `Select`, `Deselect` | 301 × 92 | −131, −96 | 56 px |
| `SDRLB0` | `Fire`, every tic (the launch, the reload, `A_ReFire`; kicked) | 301 × 92 | −133, −93 | 59 px |
| `SDRFA0`–`SDRFD0` | `Flash` A–D over `SDRLB0`'s muzzle, fading (x1, 0.8, 0.6, 0.4) | 37 × 27 to 13 × 11 | −159, −85 to −175, −93 | 67 to 59 px |
| `SDRKA0` | ROKS-3: `Ready`, `Select`, `Deselect`; `Fire`'s jets | 181 × 92 | −135, −96 | 56 px |
| `SDRKB0` | `Fire`: the trigger let go (`A_ReFire`, 20 tics), in A's pose | 181 × 92 | −135, −96 | 56 px |
| `SDKFA0` | `Flash` (`Bright`, `A_Light1`): the flame at the nozzle | 46 × 23 | −118, −80 | 72 px |
| `SDHKA0` | hand Katyusha: `Ready`, `Select`, `Deselect`; the 20-tic wind-up | 169 × 92 | −146, −96 | 56 px |
| `SDHKB0` | `Fire`: the salvo, the reload and `A_ReFire` (kicked) | 169 × 92 | −148, −93 | 59 px |
| `SDHFA0` | `Flash` A (11 tics, `A_Light1`) over `SDHKB0`'s rails | 74 × 51 | −127, −72 | 80 px |
| `SDHFB0` | `Flash` B (6 tics, `A_Light2`), the smoke fading (x0.7) | 52 × 35 | −141, −81 | 71 px |

Only the four-letter names changed, `SHTG` → `SDIZ`, `SHTF` → `SDIF`,
`MISG` → `SDRL`, `MISF` → `SDRF`, `PLSG` → `SDRK`, `PLSF` → `SDKF`, `BFGG`
→ `SDHK`, `BFGF` → `SDHF` (and the Katyusha's `Spawn`, `BFUG` → `SDHP`):
frame letters, tics, actions and flow are as they were, held by
`tests/test_gemini_weapons_install.py` against the state machines as they
stood at HEAD e84c56c, before D84 (and by `tests/test_weapon_sprites.py`).
Reserved above and not drawn, because no state uses them: `SDIZ` E–F,
`SDKF` B, `SDHK` C. The draft overlay records the eight pairs as installed
(§6.9) and the Katyusha's pickup with the D48 pickups. Licence rows:
`docs/art/LICENSES.md`, "Weapon frames: the IZh-58, RPG-7, ROKS-3, hand
Katyusha and ice axe in hand". **NOT VERIFIED in the engine from the PK3** (D26): the
PM's pass.

**The ice axe in hand, installed by D88 (2026-10-20).** The CEO approved
the swing ("Piolet aprobado", D88;
`docs/art/previews/2026-10-20_1112_F4_ice-axe-swing-ABCD.png`) after its
first strike frame was rejected for an arm that left the view curved (D84).
`tools/art/gemini_frames.py ice_axe` builds the ready frame from the CEO's
Google Gemini image, taller than the guns (the top 72 px above the bar:
D76's long shaft and big head), and the swing by rotating that approved
frame as one rigid piece about the elbow (palette-safe, RotSprite-style;
D86): the wind-up lifted back, the strike, the follow-through carried on
down. The source image stays in `work/art/reference/` (D77). Four lumps ship
in `assets/sprites/ice_axe/`, beside the pickup `SDAPA0`, byte-identical to
`work/art/weapons/hand_G/ice_axe/` (a fresh build reproduces them where the
source exists); RGBA with hard alpha, palette v2; every one runs on under
the status bar (the build measures no visible cut edge, 16:9 and the bob).

| Lump | State | Size | `grAb` (left, top) | Above the status bar |
|---|---|---|---|---|
| `SDAXA0` | `Ready`, `Select`, `Deselect` | 104 × 108 | −185, −80 | 72 px |
| `SDAXB0` | `Fire`: the wind-up (5 tics, the swing sound) and the last 6 (`A_ReFire`) | 98 × 145 | −210, −73 | 79 px |
| `SDAXC0` | `Fire`: the strike (`A_SD_IceAxeSwing`) and the return | 268 × 124 | −131, −94 | 58 px |
| `SDAXD0` | `Fire`: the follow-through (6 tics) | 266 × 99 | −126, −119 | 33 px |

Only the four-letter name changed, `PUNG` → `SDAX`: frame letters, tics,
actions (N9's swing sound, `A_SD_IceAxeSwing` and its `SD_IceAxePuff`) and
flow are as they were, held by `tests/test_gemini_weapons_install.py`
against the state machine at HEAD e84c56c (and by
`tests/test_weapon_sprites.py`). `SDAX` E, reserved above, is not drawn: no
state uses it. The draft overlay records `PUNG` → `SDAX` as installed
(§6.9); no weapon swap is left. Licence rows: `docs/art/LICENSES.md`,
"Weapon frames: the IZh-58, RPG-7, ROKS-3, hand Katyusha and ice axe in
hand". **NOT VERIFIED in the engine from the PK3** (D26): the PM's pass.

**The bestiary (F5).** Reserved names, the frames the art must provide, and
the Freedoom placeholder each class wears today (declared in §5.1). The
frame layouts are Doom's, so the swap is a rename; the two exceptions are
marked. Images per class and the drawing briefs: `BESTIARY.md` §3–§9, §12.

| Class | Final sprite | Frames (rotations) | Placeholder today |
|---|---|---|---|
| `SD_ReichRifleman` | `SDRR` | A–G (8), H–U (0) | none: **installed, D55** (was `POSS`) |
| `SD_LegionTrooper` | `SDLT` | A–G (8), H–U (0) | none: **installed, D54** (was `SPOS`) |
| `SD_Stormtrooper` | `SDHS` | A–H (8), I–U (0) | none: **installed, D56** (was `TROO`) |
| `SD_StormBolt` | `SDBL` | A–E (0) | none: **installed, D56** (was `BAL1`) |
| `SD_ReichHound` | `SDHN` | A–H (8, as mirrored pairs), I–N (0) | none: **installed, D55** (was `SARG`) |
| `SD_Doughboy` | `SDDB` | A–F (8), G–L (0) | none: **installed, D70** (was `HEAD`) |
| `SD_DoughboyShell` | `SDDL` | A–E (0) | none: **installed, D81** (was `BAL2`) |
| `SD_Panzermensch` | `SDPM` | A–H (8), I–O (0) | none: **installed, D67** (was `BOS2`) |
| `SD_PanzermenschSchwer` | `SDPS` | A–H (8), I–O (0) | none: **installed, D67** (inherited `BOS2` from the base; its own `States` since D67) |
| `SD_PanzerShell` | `SDPL` | A–E (0) | none: **installed, D81** (was `BAL7`; rotations 1-8 in flight, ours rotation 0) |
| `SD_General` | `SDGN` | A–G (8), H–P (0), Q–R (8) | none: **installed, D73** (was `CYBR`; the `Summon` lines borrowed `CYBR E F` and became `SDGN Q R`) |
| `SD_GeneralShell` | `SDGL` | A–E (0) | none: **installed, D73** (was `MANF` A–B in flight, `MISL` B–D burst; the burst became `SDGL C D E`) |

**The seven enemies redrawn from Google Gemini, installed by D109 and D114
(2026-10-22).** The CEO had the seven enemy classes redone with Google
Gemini (D105), approved the result ("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`) and then the
armband symbol applied to the Reich ones (D108's mix, "Ok a lo de las
esvásticas!", "OK to the swastikas!", D114). Every lump below keeps the **name, frame letter and
rotation** of the rig-drawn set it replaces, so no state, class or map
changed: 540 PNGs overwritten in place, none added, none removed, no
orphan and no duplicate frame (`check_pk3`). The files are byte-identical
to `work/art/enemies_gemini/<set>/`, built by `python
tools/art/gemini_enemy.py all` from the CEO's Gemini sheets
(`work/art/reference/enemies/gemini/`, gitignored, never shipped, D77);
the rig generators (`gen_rig.py`, `gen_legion.py`, `gen_storm.py`,
`gen_hound.py`, `gen_heavy.py`, `gen_general.py`) are kept as history and
no longer match `assets/`.
The projectiles (the bolt `SDBL`, the shells `SDGL`, `SDDL` and `SDPL`)
were not redrawn. The paragraphs after this one keep the state
tables and the body and map checks of 2026-10-14; **their sources,
canvases and offsets are the rig sets' and are superseded by this
table.** The `Translation` / `BloodColor` notes stand.

Every lump is RGBA with hard alpha in palette v2 and carries its `grAb`:
`left` = half the canvas width (the body's axis), `top` = the floor line,
the feet's last row 4 px under it (`FEET_SINK`; the Doughboy's head hangs
14 px under its origin, as before), the same for every rotation of a
frame. Rotations 6-8 are rotations 4-2 mirrored and written as their own
lumps (eight separate rotations), except the hound, which keeps Doom's
mirrored pairs (`SDHNA2A8` …). On the Reich sets the D12 symbol is drawn
after the mirror, so it is never reversed.

| Set | Folder | Lumps | Canvas (`left`, `top`) per frame group |
|---|---|---|---|
| `SDRR` | `rifleman/` | 70 | A 96×64 (48, 57); B D 96×64 (48, 56); C 96×64 (48, 55); E 120×64 (60, 56); F 120×64 (60, 57); G 80×64 (40, 56); H M N 80×64 (40, 54); I O 48×56 (24, 51); J Q 96×56 (48, 48); K R 104×48 (52, 37); L S T U 104×32 (52, 21); P 48×56 (24, 44) |
| `SDLT` | `legion/` | 70 | A–D 72×64 (36, 54); E 88×64 (44, 55); F 112×64 (56, 55); G H M 72×64 (36, 55); I N O 64×64 (32, 55); J P Q 72×56 (36, 50); K R 72×40 (36, 35); L S 88×32 (44, 20); T U 80×32 (40, 20) |
| `SDHS` | `storm/` | 77 | A C 72×56 (36, 47); B D H 80×56 (40, 47); E F 96×56 (48, 47); G 112×56 (56, 47); I N 64×56 (32, 47); J O P 64×56 (32, 45); K Q R 64×48 (32, 40); L S 64×32 (32, 26); M T U 80×32 (40, 23) |
| `SDHN` | `hound/` | 46 (pairs) | A C F 112×48 (56, 36); B D E 104×48 (52, 36); G 88×40 (44, 35); H J 88×48 (44, 36); I 88×40 (44, 32); K 80×40 (40, 28); L 64×40 (32, 32); M 64×40 (32, 31); N 88×24 (44, 18) |
| `SDDB` | `doughboy/` | 54 | A B F 72×80 (36, 64); C D 72×80 (36, 63); E 80×80 (40, 64); G 80×80 (40, 58); H 72×80 (36, 61); I 96×80 (48, 61); J 72×64 (36, 47); K 72×40 (36, 22); L 96×40 (48, 23) |
| `SDPM` | `panzermensch/` | 71 | A 136×72 (68, 65); B D 112×72 (56, 65); C 104×72 (52, 66); E F 128×72 (64, 67); G 128×72 (64, 66); H 120×72 (60, 66); I 96×72 (48, 66); J 88×72 (44, 67); K 72×72 (36, 60); L 88×72 (44, 61); M 80×72 (40, 63); N O 96×56 (48, 46) |
| `SDPS` | `panzermensch/` | 71 | A 144×80 (72, 73); B D 120×80 (60, 73); C 120×80 (60, 74); E F 136×80 (68, 75); G 144×80 (72, 74); H 128×80 (64, 74); I 112×80 (56, 74); J 96×80 (48, 75); K 80×80 (40, 68); L 104×80 (52, 68); M 88×80 (44, 71); N O 112×64 (56, 52) |
| `SDGN` | `general/` | 81 | A–E Q R 72×104 (36, 93); F 112×104 (56, 93); G 88×104 (44, 93); H 80×96 (40, 88); I 88×104 (44, 98); J 64×96 (32, 86); K 72×96 (36, 85); L M 88×88 (44, 80); N O P 152×40 (76, 34) |

The figures are as tall in game as the sets they replace (the tool sizes
each set by the old one's standing frame: `SDRR` 59 rows, `SDLT` 56,
`SDHS` 50, the hound's profile 36, `SDDB` 77, `SDPM` 68, the Schwer × 1.12
= 76, `SDGN` 96). Frames Gemini did not draw are derived by the tool and
listed in each set's `metrics.json` (`derived`): the pain in rotations
2-8 (the standing view tilted back), the gib of the rifleman, the Legion
trooper and the stormtrooper (the death frames with procedural blood), the
General's `Summon` Q R (the standing and the aim views). **NOT VERIFIED in
the engine** (D26): how the new sets read in play, the mirrored rotations
6-8 (an armband or a flag patch changes arm there), and the corpses'
`top` against the floor. Held by `tests/test_<enemy>_sprites.py` and
`tests/test_gemini_enemy_install.py`. Licence rows: `docs/art/LICENSES.md`,
the seven "Enemy sprites" sections.

**The Legion trooper, installed by D54 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.** The CEO chose cell C
of the Legion sweep (D48) and approved its redone death, the corpse lying
flat (D54). The whole set ships, 70 lumps in `assets/sprites/legion/`,
byte-identical to `work/art/enemies/legion/full_C/` (`tools/art/gen_legion.py
--full`, rendered on the Windows PC on 2026-10-14); the superseded
`old_death/`, the GIFs, the `pair_*` lineups and `metrics.json` stay in
`work/`. Unlike the IWAD's placeholders the set has no mirrored pairs: the
figure is handed (shotgun across the chest, flag patch on the right
shoulder), so frames A–G are drawn in **eight separate rotations**
(`SDLTA1` … `SDLTG8`, 56 lumps) and H–U in rotation 0 (14 lumps). Each PNG
is RGBA with hard alpha and carries its `grAb` offsets: `left = width / 2`,
`top` = the rig's floor line (64 on the 64×72 and 96×72 standing canvases,
68 on the 96×80 death canvas, 76 on the 96×88 gib canvas), the same for the
eight rotations of a frame. The build drops the set folder (`sprites/SDLTA1.png`).

| Frames | Lumps | State |
|---|---|---|
| A–D | 32 | `Spawn` (A B), `See` (A A B B C C D D) |
| E–F | 16 | `Missile` (E aim, F fire, `Bright`) |
| G | 8 | `Pain` |
| H–L | 5 | `Death` (L the corpse, `-1`); `Raise` plays L K J I H |
| M–U | 9 | `XDeath` (U the remains, `-1`) |

Only the four-letter name changed, `SPOS` → `SDLT`: frame letters, tics,
`Bright`, actions and flow are as before, held by
`tests/test_legion_sprites.py` against the state machine as it stood
before D54. Blood stays the engine's sprite recoloured by `BloodColor
"AD 27 21"` (D49, below); the drawn deaths carry their own dark-red blood.
Licence rows: `docs/art/LICENSES.md`, "Enemy sprites: the Liberty Legion
trooper". The draft overlay carries nothing of the Legion (§6.9).

**The Reich rifleman and the Reich hound, installed by D55 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.**
The CEO approved the rifleman drawn on the rig (cell E, D38) with the much
bloodier death he asked for in D48, the corpse lying flat ("OK", D55), and
the German shepherd of cell A (D50) whole ("OK perro", D55). Both sets ship
byte-identical to their renders on the Windows PC on 2026-10-14; the GIFs,
the `lineup_*` sheets, `metrics.json` and the hound's four-cell sweep stay
in `work/`. Each PNG is RGBA with hard alpha and carries its `grAb`
offsets, `left = width / 2` and `top` = the floor line, the same for every
rotation of a frame. The build drops the set folders (`sprites/SDRRA1.png`,
`sprites/SDHNA2A8.png`).

*The rifleman*, 70 lumps in `assets/sprites/rifleman/` from
`work/art/enemies/rig/` (`tools/art/gen_rig.py`). Handed like the Legion
(rifle on the right hip, armband on the left arm, and a mirrored armband
would reverse the D12 symbol), so frames A–G are **eight separate
rotations** (`SDRRA1` … `SDRRG8`, 56 lumps) and H–U rotation 0 (14).
Canvases: 64×72 standing (`top` 64), 96×72 for aim and fire, 96×80 for the
death (`top` 68), 96×88 for the gib (`top` 76).

| Frames | Lumps | State |
|---|---|---|
| A–D | 32 | `Spawn` (A B), `See` (A A B B C C D D) |
| E–F | 16 | `Missile` (E aim, F fire) |
| G | 8 | `Pain` |
| H–L | 5 | `Death` (L the corpse lying flat, `-1`); `Raise` plays K J I H |
| M–U | 9 | `XDeath` (U the remains, `-1`) |

*The hound*, 46 lumps in `assets/sprites/hound/` from
`work/art/enemies/hound_gsd/full_A/` (`tools/art/gen_hound.py --full`). The
dog is drawn symmetric, so frames A–H use Doom's **mirrored pairs**: five
lumps a frame, `SDHNA1`, `SDHNA2A8`, `SDHNA3A7`, `SDHNA4A6`, `SDHNA5`,
where an eight-character name is frame A in rotation 2 and, flipped by the
engine about its `left` offset, rotation 8 (40 lumps); I–N are rotation 0
(6). `check_pk3` reads both halves of such a name and holds every frame's
eight slots complete; `tests/test_art.py` accepts the eight-character
names. Canvases: 112×64 standing (`left` 56, `top` 52), 128×88 for the
death (`left` 64, `top` 58). The death was drawn and judged from a
37-degree camera (a corpse is seen from above): that is the art, not
anything the engine is told.

| Frames | Lumps | State |
|---|---|---|
| A–D | 20 | `Spawn` (A B), `See` (A A B B C C D D) |
| E–G | 15 | `Melee` (E F `A_FaceTarget`, G the bite) |
| H | 5 | `Pain` |
| I–N | 6 | `Death` (N the dog lying on its side, `-1`); `Raise` plays N M L K J I |

Only the four-letter names changed, `POSS` → `SDRR` and `SARG` → `SDHN`:
frame letters, tics, `Fast`, actions and flow are as before, held by
`tests/test_rifleman_sprites.py` and `tests/test_hound_sprites.py` against
the state machines as they stood at HEAD 8b4ef67, before D55. Blood stays
the engine's sprite recoloured by `BloodColor "AD 27 21"` (D49, below); the
drawn deaths carry their own dark-red blood. Licence rows:
`docs/art/LICENSES.md`, "Enemy sprites: the Reich rifleman" and "Enemy
sprites: the Reich hound". The draft overlay carries nothing of either
(§6.9).

**The Hybrid Stormtrooper and his bolt, installed by D56 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.** The
CEO chose cell E of the Stormtrooper sweep (D48), approved its full set but
for the death (D53) and then the redone death, the corpse lying flat on his
back (D56, "Muerte OK"). The whole set ships, 82 lumps in
`assets/sprites/storm/`, byte-identical to `work/art/enemies/storm/full_E/`
(`tools/art/gen_storm.py --full`, death redone by `--death`, rendered on
the Windows PC on 2026-10-14); the superseded `old_death/`, the proposed
claw frames V W (`proposed_melee/`), the GIFs, the `blood_*` comparisons,
the `lineup_*` sheets and `metrics.json` stay in `work/`. The figure is
handed (chrome plate on his right, armband on his left), so `SDHS` A–H are
**eight separate rotations** (64 lumps) and I–U rotation 0 (13); `SDBL`
A–E are rotation 0 (5). Each PNG is RGBA with hard alpha and carries its
`grAb` offsets, `left = width / 2`: `top` 64 on the 80×72 standing canvas,
68 on the 112×80 death canvas, 84 on the 128×96 gib canvas; the bolt is
centred on its 32×32 canvas (16, 16), as a projectile is drawn about its
middle. The build drops the set folder (`sprites/SDHSA1.png`).

| Frames | Lumps | State |
|---|---|---|
| `SDHS` A–D | 32 | `Spawn` (A B), `See` (A A B B C C D D) |
| `SDHS` E–G | 24 | `Melee` falls through to `Missile`: E F `A_FaceTarget`, G claw or bolt (`A_SD_MeleeOrMissile`) |
| `SDHS` H | 8 | `Pain` |
| `SDHS` I–M | 5 | `Death` (M the corpse, `-1`); `Raise` plays M L K J I |
| `SDHS` N–U | 8 | `XDeath` (U the remains, `-1`) |
| `SDBL` A–E | 5 | `SD_StormBolt`: `Spawn` A B (`Bright`), `Death` C D E (`Bright`) |

Only the four-letter names changed, `TROO` → `SDHS` and `BAL1` → `SDBL`:
frame letters, tics, `Bright`, actions and flow (the empty `Melee:` label
included) are as before, held by `tests/test_storm_sprites.py` against the
state machines as they stood at HEAD 8b4ef67, before D56. The claw keeps
sharing the bolt's E F G (D53); the proposed V W would need `Melee` split
from `Missile`, a ZScript change not made. Blood stays the engine's sprite
recoloured by `BloodColor "AD 27 21"` (D49, below); the drawn deaths carry
their own dark-red blood. Licence rows: `docs/art/LICENSES.md`, "Enemy
sprites: the Hybrid Stormtrooper and his bolt". The draft overlay never
carried either (§6.9).

**The Panzermensch and the Schwer, installed by D67 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.** The CEO
chose cell D of the heavies sweep, the bare skull in a riveted iron mask
(D65), and approved its full set with the Schwer alongside ("OK al
Panzermensch", D67). The Schwer is cell D with the sweep's S2 treatment,
the PM's call in D65: black plate, modelled 12 % larger, spikes and exhaust
stacks, the mask's slit lit. Both sets ship, 142 lumps in
`assets/sprites/panzermensch/`, byte-identical to
`work/art/enemies/heavy/full/SDPM/` and `.../SDPS/` (`tools/art/gen_heavy.py
--full pm` and `--full ps`, rendered on the Windows PC on 2026-10-14); the
GIFs, the `lineup_*` sheets, `metrics.json` and `blood_share.json` stay in
`work/`. **`SDPS`** is a new reserved name (SD + Panzermensch Schwer),
checked free: no lump of `freedoom2.wad` 0.13.0 starts with `SD`, and no
name reserved above or packed under `assets/` starts with `SDPS` (the
`SDPOSTR*` posters share only `SDP`). The figure is handed (the banner
carries the D12 symbol, which a mirror reverses, and he throws with his
right), so A–H are **eight separate rotations** (64 lumps a set) and I–O
rotation 0 (7). Each PNG is RGBA with hard alpha and carries its `grAb`
offsets, the same for every rotation of a frame: `SDPM` 112×96 standing
(`left` 56, `top` 86), 176×120 for the death (64, 92); `SDPS` 128×104
standing (64, 94), 192×140 for the death (68, 100). The death's `left` is
the body's axis column of a canvas wider on one side, since he falls
forward off it, not `width / 2`. The build drops the set folder
(`sprites/SDPMA1.png`).

| Frames | Lumps a set | State (both classes) |
|---|---|---|
| A–D | 32 | `Spawn` (A B), `See` (A with the footstep, then A B B C C D D) |
| E–G | 24 | `Melee` falls through to `Missile`: E F `A_FaceTarget`, G blow or shell (`A_SD_MeleeOrMissile`) |
| H | 8 | `Pain` |
| I–O | 7 | `Death` (O the corpse, `-1`: `SDPMO0` lying flat, `SDPSO0` face down, the stacks forbidding his back); `Raise` plays O N M L K J I |

`SD_Panzermensch`: only the four-letter name changed, `BOS2` → `SDPM`.
`SD_PanzermenschSchwer` had no `States` block and drew the base's; it now
has its own, **the base's line for line with `SDPS`** (frame letters, tics,
actions, flow and the empty `Melee:` label), so `A_SD_PanzerStep` and the
melee constants still resolve from the base class. Both are held by
`tests/test_panzermensch_sprites.py` against the state machine as it stood
at HEAD 9fe6479, before D67. **The Translation planned in v0 is dropped:**
a `Translation` remaps palette indices, our sprites are truecolour PNGs and
the mod ships no `PLAYPAL`, so the recolour would go through Freedoom's
palette (gen_heavy's note, **NOT VERIFIED**); a drawn set of its own costs
nothing more on the rig.

**The Schwer's body grows with its drawing (D67).** At the base's 24 × 64 a
shot at the top of the stacks would hit nothing, so `SD_PanzermenschSchwer`
sets `Radius 27` and `Height 72` (× 1.12, constants `SD_PANZER_HEAVY_RADIUS`
and `SD_PANZER_HEAVY_HEIGHT`); the base keeps 24 × 64. Checked on the
built maps on 2026-10-14 before raising it: MAP03 places thing 21107 at
(3290, 256), the tank line, ceiling 256, nearest wall 54 units away in
the box metric, and at (520, 1550), the portal hall, ceiling 384, nearest
wall 114; the range at (1600, 1600), ceiling 192. MAP01 and MAP02 place
neither 21107 nor 3003. In each of those maps no passage (two-sided line,
every door opened to its neighbour's ceiling − 4) has an opening between
64 and 72, so the bigger body loses no route the base had, and no
two-sided line or sector is between 48 and 54 wide. The test pins the
three spawn boxes and the passages; how a 27-radius body squeezes between
props is not modelled (**NOT VERIFIED in the engine**, D26).

Blood stays the engine's sprite recoloured by `BloodColor "AD 27 21"` (D49,
below), inherited by the Schwer; the drawn deaths carry their own dark-red
blood. Licence rows: `docs/art/LICENSES.md`, "Enemy sprites: the
Panzermensch and the Schwer". The draft overlay never carried either
(§6.9). The shell, `SD_PanzerShell`, wore Freedoom's `BAL7` until D81
(below).

**The Doughboy, installed by D70 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.** The CEO chose cell C of
the heavies sweep, the head in its M1 helmet, severed, with a neck stump
and a dangling spine (D65), asked for a bigger flag on the helmet ("ponle
la bandera más grande en la cabeza", "make the flag on the head bigger", D67: the decal grew from 5 × 4 to
11 × 7 px across the set) and approved the set with it ("OK", D70). It
ships, 54 lumps in `assets/sprites/doughboy/`, byte-identical to
`work/art/enemies/heavy/full/SDDB/` (`tools/art/gen_heavy.py --full db`,
rendered on the Windows PC on 2026-10-14, and rendered again for the
install into a scratch folder: all 54 identical); the GIFs, `metrics.json`,
`blood_share.json` and `before_flag/` stay in `work/`. `SDDB` was reserved
for it from the start (§6.3's table). The head is handed (the helmet sits
askew, the flag decal and the buckle on one side), so A–F are **eight
separate rotations** (48 lumps) and G–L rotation 0 (6). Each PNG is RGBA
with hard alpha, in palette v2 (`flesh_pink`, D45, as the Legion trooper),
and carries its `grAb` offsets, the same for every rotation of a frame:
80×96 for A–F (`left` 40, `top` 76: the floater hangs by the actor's z, no
feet to sink), 160×108 for the death, G (72, 80), still in the air when
the eye bursts, and H–L (72, 76), on the floor. The build drops the set
folder (`sprites/SDDBA1.png`).

| Frames | Lumps | State |
|---|---|---|
| A | 8 | `Spawn` (A, `A_Look`), `See` (A, `A_Chase`): Doom's one-frame float |
| B–D | 24 | `Missile` (no `Melee`, as the cacodemon): B C `A_FaceTarget`, D `Bright`, bite or shell (`A_SD_MeleeOrMissile`) |
| E–F | 16 | `Pain` |
| G–L | 6 | `Death` (L the corpse, `-1` with `A_SetFloorClip`: `SDDBL0` a flat sack face up in its blood); `Raise` plays L K J I H G |

Only the four-letter name changed, `HEAD` → `SDDB`: frame letters, tics,
actions and flow are as they were, held by `tests/test_doughboy_sprites.py`
against the state machine as it stood at HEAD 093db98, before D70.

**The body stays 31 × 56 (D70).** D67's rule is that the body follows the
drawing; here the drawing follows the placeholder. Measured on the
installed lumps: the float and the attack (A–D) are 53–55 px wide,
inside the 62-unit box, and the pain's lurch (E, F) at most 64, where
Freedoom's `HEAD` is 61–69 wide; every living frame rises 60–62 px over
the actor's z, where `HEAD` A–D rise 61–62 (`freedoom2.wad` 0.13.0);
only the severed stump hangs lower than `HEAD`'s jaw, 15 px under z
against 5. Placements, checked on the built maps on
2026-10-14 against that body: MAP01 places thing 3005 at (2760, 1300),
MAP02 thing 21104 at (2976, 896), MAP03 at (1000, 400), (1150, 520) and
(864, 1216), the range at (1152, 1600); no wall inside any 31-unit box and
at least 128 units of opening over each. The test pins them. **NOT
VERIFIED in the engine** (D26): whether the 15-px stump, with the actor
resting on the floor at spawn (z = floor until it first floats), is drawn
into the floor or lifted by GZDoom's sprite clipping.

Blood stays the engine's sprite recoloured by `BloodColor "AD 27 21"` (D49,
below); the drawn deaths carry their own dark-red blood. Licence rows:
`docs/art/LICENSES.md`, "Enemy sprites: the Doughboy". The draft overlay
never carried it and records it as installed whole (`HEAD` → `SDDB`,
§6.9). The shell, `SD_DoughboyShell`, wore Freedoom's `BAL2` until D81
(below).

**The General and his shell, installed by D73 (2026-10-14). Redrawn from Google Gemini by D109 (above): the files, canvases and offsets this paragraph gives are the rig set's.** The CEO
combined cells C and D of the General's sweep, C from the front (the field
gun on his right shoulder, the swagger stick, the two shoulder pennants)
and D's two-flag cloak on his back (D71), approved the CD turnaround ("OK
al general", D72) and then the full set ("Ok general", D73). It ships, 86
lumps in `assets/sprites/general/`, byte-identical to
`work/art/general/full/SDGN/` and `.../SDGL/` (`tools/art/gen_general.py
--full`, seed 106, rendered on the Windows PC on 2026-10-14, and rendered
again for the install into a scratch folder: all 86 identical); the GIFs,
`info.json`, `metrics.json`, the sweep's cells and the turnaround stay in
`work/`. `SDGN` and `SDGL` were reserved from the start (§6.3's table). He
is handed (the gun rides his right shoulder, the pennants differ, the
cloak is split Reich | Legion), so A–G and Q–R are **eight separate
rotations** (72 lumps), H–P rotation 0 (9), and the shell A–E rotation 0
(5). Each PNG is RGBA with hard alpha, `SDGN` in palette v2 (`flesh_pink`
at the throat, D45), `SDGL` inside v1, and carries its `grAb` offsets, the
same for every rotation of a frame: 136×124 for the living frames (`left`
68, `top` 114: the boots sink 3–6 px under the actor's z, as the other
walkers'), 300×168 for the death (150, 136: he falls back across the
screen onto the spread cloak), 40×40 for the shell (20, 20, centred, as the
storm bolt). The build drops the set folder (`sprites/SDGNA1.png`).

| Frames | Lumps | State |
|---|---|---|
| A–D | 32 | `Spawn` (A B, `A_Look`), `See` (A A B B C C D D, `A_SD_GeneralChase`) |
| E–F | 16 | `Missile`: E aims (`A_FaceTarget`), F fires (`A_SD_GeneralShot`), three times |
| G | 8 | `Pain` |
| Q–R | 16 | `Summon`: Q `Bright` (`A_SD_GeneralSummon`, the order, his fist raised), R (he points the recruits on) |
| H–P | 9 | `Death` (M `A_NoBlocking`; P 30, then P `-1` with `A_BossDeath`: `SDGNP0` on his back on the cloak, the pool on the flags) |
| `SDGL` A–B, C–E | 5 | `SD_GeneralShell`: `Spawn` A B (flight, `Bright`), `Death` C D E (burst, `Bright`); `RenderStyle "Add"` stays |

Only the four-letter names changed, `CYBR` → `SDGN` and `MANF`/`MISL` →
`SDGL`, plus the frame letters the art was always going to need: the
`Summon` lines `CYBR E F` → `SDGN Q R`, the shell's burst `MISL B C D` →
`SDGL C D E`. Tics, actions and flow are as they were, held by
`tests/test_general_sprites.py` against the state machines as they stood
at HEAD 42ac443, before D73. He has no `Raise` state (a boss, as the
Cyberdemon) and no `XDeath`, so no gib.

**The body stays 40 × 100 (D73).** Measured on the installed lumps: the
living frames are 41–63 px wide, inside the 80-unit box (Freedoom's `CYBR`
is 67–108), and rise 89–92 px over the actor's z (`CYBR` 96–105,
`freedoom2.wad` 0.13.0); only Q's raised fist goes over the 100-unit
height, to 103–109 px, a sprite-only overhang a few pixels above `CYBR`'s
tallest frame. The corpse `SDGNP0` is 134 px across (`CYBRP0` 113) and,
drawn seen from above, reaches 31 px under the offset row, as the other
big corpses do (`SDPMO0` 23, `SDPSO0` 25, `SDDBL0` 21). Placements, checked
on the built maps on 2026-10-14 against that body: MAP03 places thing 21106
once, at (480, 1216) in the portal hall on every skill (ceiling 384), the
range once, at (1824, 1600) (ceiling 192); MAP01 and MAP02 never, and no
map places 16. No wall inside either 40-unit box, and the opening over each
leaves Q's fist 83 units of headroom at the least. The test pins them.
**NOT VERIFIED in the engine** (D26): Q's fist under a low ceiling (none
where he is placed; his 100 clears a 112 ceiling, BESTIARY §9, and the fist
would then poke through it) and the corpse's 31 px under z, whether
GZDoom's sprite clipping lifts it or draws it into the floor.

Blood stays the engine's sprite recoloured by `BloodColor "AD 27 21"` (D49,
below); the drawn deaths carry their own dark-red blood. Licence rows:
`docs/art/LICENSES.md`, "Enemy sprites: the General and his shell". The
draft overlay never carried either and records them as installed whole
(`CYBR` → `SDGN`, `MANF` → `SDGL`, §6.9); `MISL` is not recorded there,
because the PG-7V grenade and the Katyusha rocket still wear it.

**The two enemy shells, installed by D81 (2026-10-20).** The CEO took the
recommended option for both ("los que tú recomiendas", "the ones you recommend", D81;
`docs/art/previews/2026-10-19_2200_F5_enemy-shells.html`): option A of each
sweep of `tools/art/gen_shells.py`, the Doughboy's "comet" (a white-hot
core in a `flag_red` corona, the shell its attack frames kindle in the
mouth) and the Panzermensch's "ember" (a dull `hazard_yellow` ball in an
olive smoke halo, the ball its gauntlet throws; the Schwer fires the same
`SD_PanzerShell`). Ten lumps ship, byte-identical to
`work/art/shells/SDDL/` and `.../SDPL/` (rendered on the Windows PC on
2026-10-19; the sweep's other options, the GIFs, the scenes and
`metrics.json` stay in `work/`): the Doughboy's shell `SDDL` A–E in
`assets/sprites/doughboy/`, the Panzermensch's shell `SDPL` A–E in
`assets/sprites/panzermensch/`, beside their throwers. Each
is RGBA with hard alpha, inside palette v1, in rotation 0 (one image for
every angle, as `SDBL` and `SDGL`; Freedoom's `BAL7` had rotations 1-8 in
flight), with its `grAb` centring the ball on the actor half its `Height`
up, as Freedoom hangs its balls:

| Lumps | State | Canvas | `grAb` (left, top) |
|---|---|---|---|
| `SDDLA0`, `SDDLB0` | `SD_DoughboyShell` `Spawn`: `SDDL AB 4 Bright` | 48 × 48 | 24, 28 (the centre 4 px above z; `Height` 8) |
| `SDDLC0`, `SDDLD0`, `SDDLE0` | the shell's `Death`: `SDDL CDE 6 Bright` | 48 × 48 | 24, 28 |
| `SDPLA0`, `SDPLB0` | `SD_PanzerShell` `Spawn`: `SDPL AB 4 Bright` | 56 × 56 | 28, 36 (the centre 8 px above z; `Height` 16) |
| `SDPLC0`, `SDPLD0`, `SDPLE0` | the shell's `Death`: `SDPL CDE 6 Bright` | 56 × 56 | 28, 36 |

Only the four-letter names changed, `BAL2` → `SDDL` and `BAL7` → `SDPL`,
on the two state lines of each class: tics, `Bright`, flow and the
`RenderStyle "Add"` are as they were (`tests/test_shells_install.py`
pins them against the classes at HEAD e84c56c). Licence rows:
`docs/art/LICENSES.md`, "Enemy sprites: the Doughboy's and the
Panzermensch's shells". **NOT YET SEEN IN THE ENGINE** (D26); the additive
blend on our walls was a stand-in in the preview, NOT VERIFIED in GZDoom.

**The radio (§6.7).** `SD_Radio` → final sprite **`SDRD`** A (rotation
`0`, one picture from every angle), standing on the floor (`left = width /
2`, `top = height`). Installed by D63, below; the placeholder was `PMAP` A.
Checked free: no IWAD lump starts with `SD`, and no reserved sprite above
starts with `SDRD`.

**The pickups, installed by D63 (2026-10-14).** The CEO chose one option
of each object of the pickups sweep (`tools/art/gen_pickups.py`, T8, T23
and T25's sprite). The names are **reserved** here, and every one ships:

| Class | Sprite | Frames | Option chosen | File | `Spawn` (was) |
|---|---|---|---|---|---|
| `SD_Clip` | `SDCL` | A (0) | B, a torn paper packet of 7,62×25 rounds | `assets/sprites/pickups/SDCLA0.png` | `SDCL A -1` (`CLIP A -1`, inherited from `Clip`) |
| `SD_ClipBox` | `SDCB` | A (0) | B, an opened zinc (цинк) of rounds | `…/SDCBA0.png` | `SDCB A -1` (`AMMO A -1`, from `ClipBox`) |
| `SD_Shell` | `SDSL` | A (0) | A, four 12-gauge shells lying | `…/SDSLA0.png` | `SDSL A -1` (`SHEL A -1`, from `Shell`) |
| `SD_ShellBox` | `SDSB` | A (0) | B, the box open, twenty shells in it | `…/SDSBA0.png` | `SDSB A -1` (`SBOX A -1`, from `ShellBox`) |
| `SD_RocketAmmo` | `SDRA` | A (0) | A, one PG-7V round standing on its tail | `…/SDRAA0.png` | `SDRA A -1` (`ROCK A -1`, from `RocketAmmo`) |
| `SD_RocketBox` | `SDRB` | A (0) | A, an open crate with two rounds | `…/SDRBA0.png` | `SDRB A -1` (`BROK A -1`, from `RocketBox`) |
| `SD_Cell` | `SDFU` | A (0) | A, a 10-litre jerrycan | `…/SDFUA0.png` | `SDFU A -1` (`CELL A -1`, from `Cell`) |
| `SD_CellPack` | `SDFB` | A (0) | B, two ROKS-3 tanks in their back frame | `…/SDFBA0.png` | `SDFB A -1` (`CELP A -1`, from `CellPack`) |
| `SD_BluePass` | `SDKB` | A, B (0) | B, a laminated card; B is the blink | `…/SDKBA0.png`, `…/SDKBB0.png` | `SDKB A 10`, `SDKB B 10 Bright`, `Loop` (`BKEY`, the same three lines, from `BlueCard`) |
| `SD_Radio` | `SDRD` | A (0) | B, an Okean-209 on a tabouret | `…/SDRDA0.png` | `SDRD A -1` (`PMAP A -1`) |

Each PNG is byte-identical to its render in
`work/art/pickups/<object>/<option>/` (rendered on the Windows PC on
2026-10-14), RGBA with hard alpha, with its `grAb` offsets inside the file:
`left = width / 2` (rounded down), `top = height`, standing on the floor
like the IWAD's pickups. The build drops the set folder, so the engine sees
`sprites/SDCLA0.png`. Colour: palette v1 for all but the pass, which uses
palette v2's cobalt so Doom's blue key reads blue (D45); it is RGBA, so it
is listed in `tests/test_palette_v2.py`'s `APPROVED_IN_V2` and not in
`check_pk3`'s `PALETTE_V2_LUMPS` (indexed lumps only).

Only the sprite name changed. The eight ammunition classes and the pass
had **no** `States` block before D63: their `Spawn` came from Doom's
class. Each now declares a `Spawn` label of its own that is the parent's
line for line, read in GZDoom g4.14.2's `gzdoom.pk3`
(`zscript/actors/doom/doomammo.zs`, `doomkeys.zs`): `XXXX A -1; Stop;` for
the ammunition, `A 10; B 10 Bright; Loop;` for the pass, which blinks as
Doom's key cards do. A label declared in a subclass replaces only that
label; everything else (amounts, pools, icons, size) is still inherited.
The radio's own state changed name only. `tests/test_pickup_sprites.py`
pins all of it, including the parent's lines where a `gzdoom.pk3` is
installed. **Not changed:** the status bar icons (`Inventory.Icon`
`CLIPA0`, `SHELA0`, `ROCKA0`, `CELLA0`, and the pass's `STKEYS0`), still
Freedoom's; the backpack (`BPAK`), not in the sweep; the radio's body
(radius 16, height 28, sized on `PMAP` A; the new picture is 28×44 with the
tabouret). Checked free: no lump of `freedoom2.wad` 0.13.0 starts with
`SD`; none of the ten collides with a name reserved above. The flat
`SDRAIL1` (metro) shares `SDRA`'s first four letters but lives in `flats/`,
and the engine builds sprites from the `sprites/` namespace only (**NOT
VERIFIED in the engine**). Licence rows: `docs/art/LICENSES.md`,
"Pickups: ammunition, the blue pass and the radio". **NOT YET SEEN IN THE
ENGINE** (D26).

**The campaign pickups, installed by D80 (2026-10-20).** The CEO chose one
option per object of the campaign pickups sweep (`tools/art/gen_items.py`,
backlog M2a, audit B3 and B5; preview
`docs/art/previews/2026-10-19_2212_F5_campaign-pickups.html`): the
recommended option everywhere except the two armours (C) and the backpack
(B). The generator's `CHOSEN` table is that choice and `--install` renders
every frame of it. The names are **reserved** here, and every one but the
hand Katyusha's ships (below, "Pending"); each row names the Doom class the
sprite stands for:

| Class (replaces) | Sprite | Frames | Option chosen | `Spawn` (Doom's, renamed) | Pickup line |
|---|---|---|---|---|---|
| `SD_Stimpack` (`Stimpack`) | `SDBN` | A (0) | A, a field dressing packet (ИПП) with the first-aid sign | `SDBN A -1; Stop` (`STIM`) | `SD_GOT_STIMPACK` |
| `SD_Medikit` (`Medikit`) | `SDMD` | A (0) | A, an enamelled first-aid box with the first-aid sign | `SDMD A -1; Stop` (`MEDI`) | `SD_GOT_MEDIKIT`, also its `Health.LowMessage` |
| `SD_HealthBonus` (`HealthBonus`) | `SDHB` | A–D (0) | B, a bottle of zelyonka | `SDHB ABCDCB 6; Loop` (`BON1`) | `SD_GOT_HEALTHBONUS` |
| `SD_ArmorBonus` (`ArmorBonus`) | `SDAB` | A–D (0) | A, an SSh-68 steel helmet | `SDAB ABCDCB 6; Loop` (`BON2`); `Inventory.Icon` `SDABA0` | `SD_GOT_ARMORBONUS` |
| `SD_GreenArmor` (`GreenArmor`) | `SDAG` | A, B (0) | C, a flak vest with an SSh-68 at its foot | `SDAG A 6; SDAG B 7 Bright; Loop` (`ARM1`); `Inventory.Icon` `SDAGA0` | `SD_GOT_ARMOR` |
| `SD_BlueArmor` (`BlueArmor`) | `SDAH` | A, B (0) | C, a bare-steel SN-42 breastplate and helmet (palette v1) | `SDAH A 6; SDAH B 6 Bright; Loop` (`ARM2`); `Inventory.Icon` `SDAHA0` | `SD_GOT_MEGAARMOR` |
| `SD_Allmap` (`Allmap`) | `SDMP` | A–D (0) | A, an officer's map case (планшет) | `SDMP ABCDCB 6 Bright; Loop` (`PMAP`) | `SD_GOT_MAP` |
| `SD_Backpack` (`Backpack`) | `SDBP` | A (0) | B, an RD-54 paratrooper's pack | `SDBP A -1; Stop` (`BPAK`) | `SD_GOT_BACKPACK` |
| `SD_YellowPass` (`YellowCard`) | `SDKY` | A, B (0) | A, the blue pass's card in yellow | `SDKY A 10; SDKY B 10 Bright; Loop` (`YKEY`) | `SD_PICKUP_YELLOWPASS` |
| `SD_RedPass` (`RedCard`) | `SDKK` | A, B (0) | A, the blue pass's card in red, gold stamp | `SDKK A 10; SDKK B 10 Bright; Loop` (`RKEY`) | `SD_PICKUP_REDPASS` |
| `SD_HandKatyusha` (`BFG9000`), Katyusha | `SDHP` | A (0) | A, the D51 draft at its drawn size (70×37) | `SDHP A -1; Stop` (`BFUG`): installed with D84's weapon frames, see below | `SD_PICKUP_KATYUSHA` (unchanged) |

Files: `assets/sprites/pickups/<NAME>.png`, byte-identical to the renders in
`work/art/items/<item>/<option>/` (Windows PC, 2026-10-20), RGBA with hard
alpha and their `grAb` offsets inside the file (`left = width / 2`, `top =
height`). All palette v1. Classes: `zscript/sd/pickups.zs` (health,
armour, the map), `keys.zs` (the passes), `ammo.zs` (the backpack). Each
`Spawn` label is the Doom parent's line for line, read in GZDoom g4.14.2's
`gzdoom.pk3` (`doomhealth.zs`, `doomarmor.zs`, `doomartifacts.zs`,
`doomammo.zs`, `doomkeys.zs`, `weaponbfg.zs`), with only the four-letter
name changed; the `Default` blocks add the pickup line, the passes'
`Species`, the armours' icon and the medikit's low-health line (Freedoom's
DEHACKED prints `GOTMEDINEED` in English), nothing else. The passes copy
the blue pass: `Species "YellowCard"` and `Species "RedCard"`, because
locks 3 and 1 match by exact class or Species, never by parentage
(`keys.zs`).

The medical items wear the **first-aid sign**, a white cross on a green
field (ISO 7010 E003), not the protected red-cross emblem (D80); the green
is palette v1's `military_green`, the only green there is.

**HUD.** The status bar's and the fullscreen HUD's key icons are the
engine's `STKEYS0`-`STKEYS2` (blue, yellow, red; `DoomStatusBar.DrawBarKeys`
and the keys' `Inventory.Icon`), which the mod now ships as the passes'
own 7×5 cards: `assets/graphics/hud/STKEYS0.png` to `STKEYS2.png`, indexed
on palette v2 (`STKEYS0` uses `mosaic_cobalt`, so it is in `check_pk3`'s
`PALETTE_V2_LUMPS`; the other two use v1 colours only). The fullscreen
HUD's health icon is the literal `MEDIA0` (`doom_sbar.zs`,
`DrawFullScreenStuff`) and stays **Freedoom's medikit**: shipping ours
under that name would be the first sprite without the `SD` prefix (§1,
`tests/test_art.py`), and the other way, an `SD_StatusBar` override of
`DrawFullScreenStuff`, is a transcription of engine code (debt like T14).
Left for the CEO's H2 pass. The armour icon is the
`Inventory.Icon` of the armour last picked up, drawn at its own size and
offsets at (20, -22): our vest and breastplate are 39×40 and 36×47 against
Freedoom's 37×28 and 37×25. Standing on their own floor (`grAb` top =
height) they end where Freedoom's do, on the medikit icon's top edge
(y = -22; Freedoom's `MEDIA0` is 29×20 with offsets 14, 20), and rise 12
and 22 pixels higher, left of the armour count (x 44). **NOT VERIFIED in
the engine.**

**The Katyusha's pickup, installed with D84 (2026-10-20).**
`SD_HandKatyusha` lives in `zscript/weapons/katyusha.zs`, which another
task owned at the D80 install, so its picture waited
(`work/art/items/katyusha/A/`) for the weapon's own install: there the
Katyusha's `Spawn` became `SDHP A -1;`, the Katyusha's `SDHPA0` was copied
byte for byte into `assets/sprites/pickups/`, and the row `BFUG` left §5.1,
in one change (`tests/test_pickups_install.py` checks all three; the draft
overlay records the Katyusha's `BFUG` → `SDHP` as installed, §6.9).

Checked free: no lump of `freedoom2.wad` 0.13.0 starts with any of the ten
new names, and none collides with a name reserved above
(`tests/test_gen_items.py`). Licence rows: `docs/art/LICENSES.md`,
"Pickups: the campaign's health, armour, map, backpack and passes".
`tests/test_pickups_install.py` pins classes, sprites, frames, lines,
locks and the campaign maps' things. **NOT YET SEEN IN THE ENGINE** (D26).

**The player effects, installed by D82 (2026-10-20).** The CEO took
option A of every item ("también las recomendadas", "the recommended ones too", D82;
`docs/art/previews/2026-10-19_2208_F4_player-effects.html`). Fifty lumps
of `tools/art/gen_effects.py` (seed 75, palette v1) ship in
`assets/sprites/effects/`, byte-identical to `work/art/effects/<SPRITE>/`
(rendered on the Windows PC on 2026-10-19), each RGBA with hard alpha and
its `grAb`. Three methods, as the preview's install plan set them:

| Sprite | Lumps | Method | Edit | Actor |
|---|---|---|---|---|
| `SDPG` | 5 (`A1`, `A2A8`, `A3A7`, `A4A6`, `A5`) | new prefix | `Spawn`: `MISL A 1 Bright` → `SDPG A 1 Bright` | `SD_Pg7Grenade` |
| `SDKR` | 5 (idem) | new prefix | `Spawn`: `MISL A 1 Bright` → `SDKR A 1 Bright` | `SD_KatyushaRocket` |
| `SDPX` | 3 (`A0`-`C0`) | new prefix and letters | `Death`: `MISL B/C/D` → `SDPX A/B/C`, same tics (8, 6, 4 for the PG-7V; 6, 5, 4 for the Katyusha), `A_Explode` on A as it was on B | both rockets |
| `SDFJ` | 2 (`A0`-`B0`) | rename | `Spawn`: `PLSS ABABABABABAB 2 Bright` → `SDFJ …`, letters and tics as they are | `SD_FlameBlob` |
| `SDFX` | 5 (`A0`-`E0`) | rename | `Death`: `PLSE ABCDE 3 Bright` → `SDFX ABCDE 3 Bright` | `SD_FlameBlob` |
| `PUFF` | 4 | override, no ZScript | — | `BulletPuff`, `SD_IceAxePuff` |
| `BLUD` | 3 | override | — | `Blood` (tinted `AD 27 21`) |
| `TFOG` | 10 | override | — | `TeleportFog` |
| `IFOG` | 5 | override | — | `ItemFog` |
| `BAR1` | 2 | override | — | `ExplosiveBarrel` (2035) |
| `BEXP` | 5 | override | — | `ExplosiveBarrel` `Death` |
| `COLU` | 1 | override | — | `Column` (2028) |

The rockets are drawn in Doom's eight rotations as five lumps, the
mirrored pairs (2-8, 3-7, 4-6) the hound's way (D55), on a 72 × 24 canvas
with `grAb` 36, 16 (the centre 4 px above z, as Freedoom's `MISL A`); the
burst is 92 × 84 (`grAb` 46, 55). The flame keeps `RenderStyle "Add"`,
`Alpha 0.85`. `SDFJ` ("flame jet") replaces the reserved `SDFL`: `SDFL` +
frame `R` + rotation `1` would spell `SDFLR1`, an installed floor flat
(different namespaces, so a reader's clash, not the engine's). The seven
overrides keep the IWAD's names (§1; §5.1, "The engine actors'
overrides"). Every other line of the three classes, their constants,
sounds and flags are untouched (`tests/test_effects_install.py` pins the
`States` blocks against HEAD c68ad84 with only these names and letters
changed). Licence rows: `docs/art/LICENSES.md`, "Player effects and world
sprites". **NOT YET SEEN IN THE ENGINE** (D26): the blends (Add, the
puff's Translucent 0.5, the tinted blood) were stand-ins in the preview,
NOT VERIFIED in GZDoom.

The heavy Panzermensch draws its own set, `SDPS`, from a `States` block of
its own since D67 (above); the `Translation` once planned is dropped. Blood is recoloured by `BloodColor`
on the engine's own blood sprite; no blood sprite is reserved. **Since D49
(2026-10-14) every class bleeds dark red, `BloodColor "AD 27 21"`**
(`flag_red` 9; the Reich's olive and the Legion's pale are retired,
`BESTIARY.md` §2.1). The engine scales that value by each blood pixel's
brightness (`CreateBloodTranslation`, `src/r_data/r_translate.cpp`, read in
the g4.14.2 source), so Freedoom's `BLUD` came out as `flag_red` 0–5, the
band the drawn deaths use; since D82 the blood's shape is ours, `BLUD`
A-C shipped under the IWAD's name (§5.1), drawn so the same tint stays
inside `AD 27 21` (`tools/art/gen_effects.py`, `blood_tint`); `tests/test_blood.py` pins the value and runs
the formula on the IWAD's frames. The on-screen colour stays in T22.

**What the Freedoom placeholders look like today** (CEO play session,
2026-10-13). These are art defects, not engine defects: the mod sets no
`Scale` and no sprite offsets on any of them, and the offsets below are the
IWAD's own and are correct (`left = width / 2`, `top = height`, i.e. centred
and standing on the floor).

| Slot | Placeholder in use | What the CEO sees | Reality |
|---|---|---|---|
| 1, held | `PUNG` A–D (96×46 / 256×32) | "the sleeve is the same colour as the fist" | It **is** a bare fist: Freedoom's punch sprite, no sleeve, no blade. Replaced by `SDAX` A–E (D40). |
| 1, pickup | `CSAW` A (**until D48**; `SDAP` A since 2026-10-14) | a chainsaw on the floor | It **was** Freedoom's chainsaw pickup, and the CEO took it for one. Kept on purpose until `SDAP` A existed: every one of the 140 sprite prefixes in `freedoom2.wad` 0.13.0 was rendered on 2026-10-13 and none is a hand tool. The nearest candidates read worse: `PSTR` (berserk pack) promises a power-up, `PIST` a second pistol, `MEDI` health. A chainsaw at least says "melee weapon", and the pickup line names the ice axe. |
| ammo | `CLIP` 7×12, `AMMO` 17×16, `SHEL` 14×10, `SBOX` 34×13, `ROCK` 10×24, `BROK` 52×20, `CELL` 19×12, `CELP` 32×20 (**until D63**; ours since 2026-10-14, above), `BPAK` 26×30 (still) | "the ammunition has no three-dimensional look" | It **was** Freedoom's own pickup art, flat and lightly shaded. **T8, paid for the ammunition by D63**: each class's `Spawn` names its own sprite. The backpack keeps `BPAK`. |

The swap was what this section promised: one `Spawn` state per class, with
no change anywhere else (§6.4).

**Reserved for the P4 actors (D116).** Drawn by the CEO with Gemini, a
little at a time; until each lands its class wears an existing sprite
(§6.12). Names checked free against `assets/sprites/` and the IWAD (no
lump starts with `SD`). The gunner's and the colossus's are **installed
since D123** (licence rows: `docs/art/LICENSES.md`, "Enemy sprites: the
Legion gunner" and "the Liberty Colossus"); the colossus's old look is the
Chrome Marshal's own (`SD_ChromeGeneral`, `SDCM` ×1.3 tinted chrome, D123; `SDCM` is `SDGN` with the US-flag armband since V3).

| Class | Final sprite | Lumps | Frames (the design doc's) | Wears today |
|---|---|---|---|---|
| `SD_LegionGunner` | `SDLG` | 70 | the trooper's letters A–U | **`SDLG`**, installed (D123), `assets/sprites/legion_gunner/` |
| `SD_LibertyColossus` | `SDLC` | 81 | the General's letters A–G, Q–R, H–P | **`SDLC`**, installed (D123), `assets/sprites/colossus/` |
| `SD_Consortium` | `SDCN` | 95 | Q R rooted, A–D walk, E–H, S the Breach, I–O death | **`SDCN`**, installed (D128), `assets/sprites/consortium/`; palette v3 |
| `SD_Akm` | `SDAK` A–B held, `SDAF` A flash, `SDAQ` A pickup | 4 | the PPSh-41's | **`SDAK`, `SDAF`, `SDAQ`**, installed (D128), `assets/sprites/akm/` |
| `SD_AkmAmmo` | `SDAM` A | 1 | one curved magazine | `SDCL`, tinted |
| `SD_Rgd5` (V3) | `SDRG` A–D held, `SDRQ` A the pouch | 5 | A ready, B the pin out and the arm back, C the release, D the follow-through | **`SDRG`, `SDRQ`**, installed (D133), `assets/sprites/rgd5/` |
| `SD_Rgd5Ammo`, `SD_Rgd5Box` (V3) | `SDRJ` A one grenade (and the icon), `SDRZ` A the crate | 2 | | **`SDRJ`, `SDRZ`**, installed (D133), `assets/sprites/rgd5/`; icon `SDRJA0` |
| `SD_Rgd5Grenade` (V3) | `SDRN` A in flight and at rest | 1 | the burst stays `SDPX` A–C | **`SDRN`**, installed (D133), `assets/sprites/rgd5/` |

### 6.4 Ammunition (contract with `art-director` and `level-designer`)

The seven weapons of D13 use the **four Doom pools**, exactly the four they
need. **One pool is ours since D116: `SD_AkmAmmo`, the AKM's 7.62×39**
(`docs/engine/adr/011-akm-ammo-pool.md`): a new weapon gets a pool of its
own only when it fires another cartridge and sharing would retire a
weapon, and the reason goes in an ADR. **A second since V3: `SD_Rgd5Ammo`,
the RGD-5's grenades** (`docs/engine/adr/012-rgd5-hand-grenade.md`): ADR
012 widens the rule to a weapon that fires no cartridge at all (a thrown
weapon is its own ammunition). What else the mod owns is the nine
pickup actors, declared in
`zscript/sd/ammo.zs`, so that the player reads 1977 Soviet nomenclature
instead of "bullets" and "shells" (CEO decision, 2026-10-13).

| Pool | Pickup classes (ours) | Replaces | Used by | Name (`LANGUAGE`) |
|---|---|---|---|---|
| `Clip` | `SD_Clip`, `SD_ClipBox` | `Clip`, `ClipBox` | TT-33, PPSh-41 | `AMMO_CLIP` — 7.62x25 / «Патроны 7,62×25» |
| `Shell` | `SD_Shell`, `SD_ShellBox` | `Shell`, `ShellBox` | IZh-58 | `AMMO_SHELLS` — 12 gauge / «Патроны 12 кал.» |
| `RocketAmmo` | `SD_RocketAmmo`, `SD_RocketBox` | `RocketAmmo`, `RocketBox` | RPG-7 | `AMMO_ROCKETS` — PG-7V / «Выстрелы ПГ-7В» |
| `Cell` | `SD_Cell`, `SD_CellPack` | `Cell`, `CellPack` | ROKS-3, hand Katyusha | `AMMO_CELLS` — fuel / «Горючее» |
| — | `SD_Backpack` | `Backpack` | — | pickup line `SD_GOT_BACKPACK`; the RD-54's sprite since D80 (§6.3) |
| `SD_AkmAmmo` (ours, D116) | `SD_AkmAmmo`, both pool and magazine | nothing | AKM | `SD_AMMO_AKM` — 7.62x39 rounds / «Патроны 7,62×39»; pickup `SD_GOT_AKMMAG`; editor number **21020**; 30 a magazine, 150 maximum, the backpack's 30 / 300 |
| `SD_Rgd5Ammo` (ours, V3) | `SD_Rgd5Ammo` (one grenade, 21021), `SD_Rgd5Box` (four, 21022), in `zscript/weapons/rgd5_ammo.zs` | nothing | RGD-5 | `SD_AMMO_RGD5` — RGD-5 grenades / «Гранаты РГД-5»; pickups `SD_GOT_RGD5`, `SD_GOT_RGD5BOX`; the weapon (21009) gives 2; 6 maximum, the backpack 0 / 12; a loose grenade gives the weapon too |

Rules that matter to the other roles:

- **Maps keep using the Doom editor numbers** (2007/2048 clip, 2008/2049
  shell, 2010/2046 rocket, 2047/17 cell, 8 backpack). `replaces` does the
  rest; those classes get no editor number of their own. The AKM's
  magazine has no Doom counterpart, so it is placed by **21020**; the RGD-5's
grenades by **21021** and **21022**.
- Each class subclasses the Doom pickup it replaces. That is what keeps the
  pool Doom's: `GetParentAmmo()` walks up to the first child of `Ammo`.
  **Never** re-parent one of these to `Ammo` directly — it would silently
  create another pool. `SD_AkmAmmo` derives from `Ammo` on purpose (ADR
  011), and `tests/test_akm.py` holds it to being the only one.
- **Pickup lines come from `SD_GOT_*` ids, never from `GOTCLIP` and
  friends.** Freedoom redefines those nine ids in its `DEHACKED` lump, and a
  `DEHACKED` string replacement beats a `LANGUAGE` lump loaded afterwards
  (verified in-engine, 2026-10-13). A test enforces this.
- **The English section of `LANGUAGE` is still ASCII, and since D24 no
  longer has to be (T17).** Until 2026-10-13 Freedoom's `SmallFont` had no
  Cyrillic — GZDoom's glyph pack is under `filter/doom.id/`, which Freedoom
  does not select — so Cyrillic printed as blanks (verified: `ПГ-7В`
  printed as ` -7B`, and even `×` printed blank). That was debt **T9**, and
  D24 paid it the same day: the mod ships its own glyphs (§2). The `[ru]`
  section was correct all along. The English designations are still the
  Latin transliteration (`PG-7V rounds`, `7.62x25`); moving them to the
  Cyrillic forms D17 asks for is a text change plus flipping
  `tests/test_language.py::test_english_section_is_ascii` and its twin in
  `tests/test_arsenal.py`, and it needs an engine pass to see the glyphs on
  the HUD. Debt **T17**, not done here.

**T9 — paid (D24, 2026-10-13).** The mechanism was verified first, on
2026-10-13, with two throwaway glyphs, `П` and `Г`: a PNG at
`fonts/defsmallfont/<HEX>.png` extends GZDoom's `SmallFont` on Freedoom.
`art-director` then delivered the full set from `tools/art/gen_font.py`
(style C "Mashina", drawn from stroke data, no typeface licence inherited)
in both sizes: ASCII U+0020–U+0060, **U+0410–U+042F** (32 uppercase
Cyrillic letters), **U+0401** (`Ё`), `«»`, `×`, `°`, `·`, en and em dash,
`…` and `№` — 107 files per font, 214 in all, uppercase only because
Doom's fonts are. The ASCII range is included so Latin and Cyrillic share
one hand. Licence rows: `docs/art/LICENSES.md`.

### 6.5 Status bar — bar A, the Gemini face, digits N2 (M2e-i, 2026-10-20)

The words **AMMO**, **HEALTH**, **ARMS** and **ARMOR** are not text: they are
pixels painted inside `STBAR` (320×32; the arms panel is a second lump,
`STARMS`, 38×32), so no `LANGUAGE` string reaches them. The old question
here ("own `STBAR`" or "own status bar") is closed by the CEO's sweep
(`docs/art/previews/2026-10-20_1127_M4_hud-face-sweep.html`): **our own
pictures on Doom's own bar code.** The layout, the numbers' positions, the
mugshot logic and the fullscreen HUD stay `DoomStatusBar`'s.

| What | Decision | Lumps (in `assets/graphics/statusbar/`, packed flat as `graphics/<NAME>.png`) |
|---|---|---|
| Bar | **A**, the olive-drab instrument panel (D89), English, Russian and Catalan labels | `STBAR`, `STARMS` (English, the engine's names); `SDSBRU`, `SDARRU` (Russian) and `SDSBCA`, `SDARCA` (Catalan, P6), our names, §6.5.1. Indexed, palette v1 colours |
| Face | the sergeant from the CEO's Gemini sheets (D89, D90): 5 damage levels × straight (3 glances) / turned left / turned right / ouch / grin / rampage, plus god and dead | the 42 `STF*` at Freedoom's sizes and `grAb` offsets (`STFST00` … `STFDEAD0`). RGBA, palette v2. Gemini-derived: the licence rows say so; the sheets are not distributed |
| Numbers | **N2**, stencil segments (D92), all three sets | `STTNUM0-9`, `STTMINUS`, `STTPRCNT` (13×16; also `HUDFONT_DOOM`, the fullscreen HUD), `STYSNUM0-9` (4×6: slot owned, and `INDEXFONT_DOOM`, the ammo table), `STGNUM0-9` (4×6: slot not owned). RGBA, palette v1 |
| Left to Freedoom | — | `STFB0-3`, `STPB0-3` (multiplayer), `STKEYS3-8` (skull keys), `STCFN*`, `MEDIA0` (§5.1) |

The mugshot picks its frames by Doom's rules (`GetMugShot(5)`:
`STFST{level}0-2` idle glances, `STFTL/TR{level}0` hit from a side,
`STFOUCH{level}` a big hit, `STFEVL{level}` a weapon picked up,
`STFKILL{level}` sustained fire, `STFGOD0` in god mode or invulnerable,
`STFDEAD0` dead). Licence rows: `docs/art/LICENSES.md`, "Status bar, face
and numbers". Validated offline by `tests/test_hud_install.py`. **NOT
VERIFIED in the engine** (D26): the PM's checks H1-H5 in §6.5.1.

### 6.5.1 The status bar class and the pause sign (T24, 2026-10-14)

GZDoom draws the pause sign in `D_Display` (`src/d_main.cpp`, tag
`g4.14.2`, lines 1095-1123) from `GameInfo { PauseSign }` with no
localization, so the Russian plaque (§2, "Language variants") never
showed. Before drawing, the engine calls the status bar's
`DrawPaused(int player)` and skips its own drawing if that returns true.
That is the hook the mod uses. The contract:

| What | Value | Note |
|---|---|---|
| Class | `SD_StatusBar : DoomStatusBar`, `zscript/sd/status_bar.zs` | `DoomStatusBar` is the class Doom's `GameInfo` names today (`gzdoom.pk3:mapinfo/doomcommon.txt`, `statusbarclass = "DoomStatusBar"`); deriving from it keeps every pixel of the bar, the fullscreen HUD and the alt-HUD as they are |
| What it overrides | `DrawPaused` and, since M2e-i, `Draw`; one private helper, `SD_DrawLabelBand`. No field | `tests/test_pause_sign.py` fails on a third `override`, another function or a field |
| Registration | `MAPINFO → GameInfo → StatusBarClass = "SD_StatusBar"` | key `statusbarclass` (`src/gamedata/gi.cpp`, case-insensitive). The engine uses the last definition by file order, and our PK3 loads after gzdoom.pk3 and the IWAD. Neither `freedoom2.wad` 0.13.0 (no `MAPINFO`, no `SBARINFO` lump) nor GZDoom's support packages (only `filter/harmony/` sets one) define another; checked 2026-10-14 |
| The graphic's name | `LANGUAGE` id **`SD_PAUSE_SIGN`**: `[enu default]` `"M_PAUSE"`, `[ru]` `"localized/textures/m_pause.ru.png"`, `[ca]` `"localized/textures/m_pause.ca.png"` (P6, 2026-10-21) | a `LANGUAGE` id follows the language the player chose, `auto` included, which reading the `language` CVar would not. The Russian and Catalan values are the variants' full paths; `TexMan.CheckForTexture` resolves a name with a `/` through the file system. Why not an own lump `M_PAUSER`: ADR 010 |
| Lookup | `TexMan.CheckForTexture(name, TexMan.Type_MiscPatch)` (default flags `TryAny`) | the same call the engine's `GetGameTextureByName` makes (`GetTextureID` adds `TEXMAN_TryAny`) |
| Position | x = (screen width − width × `CleanXfac`) / 2 + left offset × `CleanXfac`; y = 4; `DTA_CleanNoMove`; animated | copied from `D_Display`: centred at the top, scaled by the clean factor, not moved |
| Multiplayer line | when `player >= 0` and `multiplayer`: `TXT_BY` with `%s` → the pausing player's name, `SmallFont` (`NewSmallFont` under `generic_ui`), `CR_RED`, centred at y = sign height × `CleanYfac` + 4 | `D_Display` draws it only when it draws the sign; returning true skips it, so the class draws it too |
| Fallback | if the name does not resolve, `DrawPaused` returns **false** and the engine draws `GameInfo { PauseSign }` (`M_PAUSE`) as before | the worst case is the English sign, never a missing one |

**The bar's labels per language (M2e-i, D89).** Localized textures are not
drawn in g4.14.2 (ADR 010) and `DoomStatusBar.DrawMainBar` is
`protected void`, not virtual, so it cannot be overridden. The Russian
pictures of bar A differ from the English ones only in the stencilled
labels (rows 23-28 of the bar; `tests/test_hud_install.py` measures it),
so `Draw` lets Doom draw everything and then redraws the labels:

| What | Value | Note |
|---|---|---|
| Override | `override void Draw(int state, double TicFrac)`: `Super.Draw(state, TicFrac)` first; then, only when `state == HUD_StatusBar` and the inventory bar is not open, the label band | the bar, numbers, face, keys and the fullscreen HUD are drawn by Doom's code; nothing of it is replaced |
| The pictures' names | `LANGUAGE` ids **`SD_SBAR_IMAGE`** (`[enu default]` `"STBAR"`, `[ru]` `"SDSBRU"`, `[ca]` `"SDSBCA"`) and **`SD_SBAR_ARMS_IMAGE`** (`"STARMS"` / `"SDARRU"` / `"SDARCA"`) | an id that names the engine's own picture means "already drawn": English costs nothing. Own 8-character lump names rather than ADR 010's full path: there is no localized variant to point at (a `localized/` entry would not be drawn anyway) |
| The band | screen y 189-199 (the bar's rows 21-31: `SD_LABEL_TOP` 189, `SD_LABEL_HEIGHT` 11); x 0-142 and 179-236 of `SD_SBAR_IMAGE`'s picture, x 104-141 of `SD_SBAR_ARMS_IMAGE`'s | below every number (the big digits end at y 186, the arms digits at 187) and clear of the face (143-178), the keys (from 239) and the ammo table (from 250); `tests/test_hud_install.py` checks it against `doom_sbar.zs`'s positions |
| Drawing | `SetClipRect(band)`; `DrawImage(name, position, DI_ITEM_OFFSETS)`; the clip rectangle in force before is restored (`Screen.GetClipRect` / `Screen.SetClipRect`) | the clip-and-restore idiom of the engine's own `DrawBar` (`statusbar.zs`) |
| Copied from `DrawMainBar` | the two positions, `(0, 168)` for `STBAR` and `(104, 168)` for `STARMS`, and its condition for drawing `STARMS`, not `deathmatch` or `teamplay` (it shows the frags there) | three facts, no code; debt T14 |

The three pause plaques are 77×20 (§2); `check_pk3` refuses a variant of
another size. The Catalan «PAUSA» (P6) is fitted inside the canvas English
and Russian sized (D48), never allowed to grow it; in `SDMENU` its Latin A
is D22's Д, so it reads PДUSД, as the menu does in Catalan (review sheet
Q2). **NOT VERIFIED in the engine** (D26): that the bar is
identical, the sign in English, the sign with `language ru` and with
`language ca`. `DrawPaused`
is verified as code in g4.14.2's `gzdoom.pk3`; whether GZDoom 4.12, the
`version` the mod declares, has it is **NOT VERIFIED** (ADR 010).

**The PM's engine checks for M2e-i** (D26; agents never start GZDoom):

| # | Check | How | Pass |
|---|---|---|---|
| H1 | Bar A in English | `language default`, MAP01, `screenblocks 10`, screenshot | the olive bar with AMMO / HEALTH / ARMS / ARMOR, the N2 numbers inside the wells, the keys in their slots, the ammo table readable; no `Script error`, no `Unknown texture` in the log |
| H2 | Bar A in Russian | `language ru`, the same screenshot, then a window size that scales the bar by a non-integer factor | the Cyrillic labels with no English letter left at the band's edges and no 1-px seam where the clip ends; every number, the face and the keys untouched |
| H3 | The face ladder | `god` (STFGOD0), then `god` off; take damage down the five levels with `buddha` on (it keeps the player alive at 1 %), watching the idle glances, a side hit (TL/TR), a big hit (ouch), a weapon pickup (grin) and held fire (rampage); `buddha` off and die (STFDEAD0) | every frame sits in the face recess, no Freedoom face left, no offset jump between frames |
| H4 | Digits | `screenblocks 10` and `11` (the fullscreen HUD draws `HUDFONT_DOOM`), ammo at 0 and above 100, armour 0; the arms slots grey and yellow | N2 everywhere, the minus and percent placed as Freedoom's; the ammo table's small digits N2 |
| H5 | Deathmatch (optional) | a local `-deathmatch` start, `language ru` | the frags number shows; no Russian arms label drawn over it |


## 6.6 Menus (`MENUDEF`)

The mod owns seven menu facts (the table has seven rows; it said six until
D41 added the episode screen). Four were learned in the engine, three of
them by breaking something first: the language switch, where it lives, the
main-menu logo and the difficulty names (rows 1, 2, 3 and 7); their
reasoning is in
`docs/engine/adr/004-language-switch-and-difficulty-ladder.md`. Two are D31
(2026-10-13), the main-menu items and the skill screen (rows 4 and 5),
reasoned in `docs/engine/adr/005-menu-text-instead-of-menu-graphics.md`. The
seventh is the episode screen (row 6, D41, ADR 007). The engine source lines
are quoted in `src/lumps/MENUDEF` itself.

| What | How | Why it is not obvious |
|---|---|---|
| Language switch | `OptionString "SD_LanguageValues"` with `auto` / `default` / `ru` / `ca` (P6), driving GZDoom's own archived `language` CVar | `OptionValue` parses its left column as a NUMBER and **the game will not start**; the mod declares no CVar of its own and no `CVARINFO` |
| Where the switch lives | `AddOptionMenu` on **both** `OptionsMenu` and `OptionsMenuSimple`, `BEFORE "os_Menu"` | `m_simpleoptions` defaults to true, so "Options" opens the SHORT screen; appending at the end puts the row below the fold |
| Main-menu logo | `LISTMENU "MainMenu"` redeclared with `StaticPatch 60, 0, "M_DOOM"` | the engine's own value is `94, 2`, which does not sit on the lockup painted into `TITLEPIC`. **This row is the contract: `M_DOOM` (200×64) goes at x=60, y=0 of the 320×200 screen.** Measured 2026-10-13: overlaying `assets/graphics/shell/M_DOOM.png` on `TITLEPIC.png` at (60,0) gives a mean per-channel difference of 6, against 22 or more at every neighbouring offset; re-measured 2026-10-24 on D128's Gemini `TITLEPIC` and the plate-less `M_DOOM`: 0 on the logo's opaque pixels at (60,0), against 31 or more one pixel off. The generator's manifest under gitignored `work/art/shell/` is evidence, not contract — it is not in every clone. Moving the lockup means changing this row, `MENUDEF` and `tests/test_language.py::MainMenuLogoTest` together. Since D31 the skill screen draws the same logo at the same place |
| Main-menu items (D31) | `TextItem "$SD_MNU_*"` in `Font "SDMENU", "Cream", "Gold"` (normal, selected). Same hotkeys (`n o l s r q`), same `IfOption(SwapMenu)` / `IfOption(ReadThis)` branches and same target menus as the engine's `PatchItem` lines they replace; `LineSpacing 16` and `Position 97, 72` (`97, 64` with ReadThis) unchanged | Freedoom's `M_NGAME`, `M_OPTION`, `M_LOADG`, `M_SAVEG`, `M_RDTHIS`, `M_QUITG` are pictures of English words: they cannot be translated and they are not our type. `Cream` / `Gold` because the glyphs are drawn red: untranslated they would be red on `TITLEPIC`'s red. Cream echoes the logo's lettering and gold its rule and star (`art-director`'s proposal); the skull selector still marks the current row |
| Skill screen (D31) | `LISTMENU "SkillMenu"`: `StaticPatch 60, 0, "M_DOOM"`; `Font "SDMENU", "Cream"` and **one** header, `StaticText 32, 70, "$SD_MNU_CHOOSESKILL"`; then `Font "SmallFont", "Red", "Gold"`, `LineSpacing 12`, `Position 32, 90`. **Order matters:** a static item takes the descriptor's font at the moment it is parsed, while the five rungs are built at run time from MAPINFO in the font the descriptor ends with — so `SmallFont` must be the LAST `Font` line | Freedoom's `M_NEWG` / `M_SKILL` at (96,14) / (54,38) sit on the name painted into `TITLEPIC` (visible in `docs/qa/evidence/2026-10-13_0955_F2_skill-ladder-en.png`). `art-director`'s layout (`docs/art/previews/2026-10-13_1554_F2_menu-sweep.png`) keeps the logo where the title screen has it and puts one header under it; "New Game" is dropped as a header because the player has just chosen it |
| Episode screen (D41) | `LISTMENU "EpisodeMenu"`: `NetgameMessage "$NEWGAME"`; `StaticPatch 60, 0, "M_DOOM"`; `Font "SDMENU", "Cream"`, `StaticText 32, 70, "$SD_MNU_CHOOSEEPISODE"`; then `Font "SmallFont", "Red", "Gold"`, `LineSpacing 12`, `Position 32, 90`. The skill screen's pattern exactly, and for the same reason: the items are built at run time in the font the descriptor ends with | The engine's body draws Freedoom's `M_EPISOD` ("Which episode?") at (54,38), a picture of English words on the name painted into `TITLEPIC` (T12). The episode names are proper nouns (D22's exception list), so they stay in `SmallFont`; only the header is `SDMENU` (§4.4, ADR 007) |
| Difficulty names | stay in `SmallFont` (`Red`, selected `Gold`), D-004-1 | the default BigFont fits ~26 characters and rung 5 is 38; the names are the CEO's and the font is the part we may change. **x = 32 is the only column that fits both ends:** rung 5, "HERO OF THE SOVIET UNION, POSTHUMOUSLY", is 288 px in `fonts/defsmallfont/` (32 + 288 = 320), and the skull is drawn 32 px left of the rungs (Doom's `Selector "M_SKULL1", -32, -5`), so x = 32 is also the smallest x that keeps it on a 4:3 screen. At the old `Position 48, 63` the engine moved the rungs by itself: in the 0955 screenshot they start at virtual x ≈ 0 (screen x 53 of 640, where the 4:3 area also starts) and the skull was drawn outside the 4:3 area. The rule the engine applied is **NOT VERIFIED** (no engine source on this machine); x = 32 leaves it nothing to correct |

### The menu font `SDMENU` (D31, built by `art-director`)

`fonts/sdmenu/` is a folder font (§2): `assets/fonts/bigfont/` — alphabet
C "Mashina", D24, cap 11 + 1 px shadow, `FontHeight 16` — copied byte for
byte, with exactly **five** Latin capitals redrawn with Cyrillic forms, D22
level 2: `0052` R → Я, `004E` N → И, `0045` E → Э, `0057` W → Ш,
`0041` A → Д. Generator: `tools/art/gen_menu.py`; reference sheet:
`docs/art/previews/2026-10-13_1554_F2_menu-sweep.png`.

**One font serves both languages.** The substitution lives in five Latin
code points. The `[ru]` strings are written in Cyrillic code points
(U+0400–U+04FF), which the font leaves untouched, so Russian reads as real
Russian while English reads "ИЭШ GДMЭ". `LANGUAGE` keeps correct English —
searchable, translatable, diffable — which is D22's rule: the mapping is
the font's job, not the strings'. Switching `language` changes the strings
and the font follows by itself; there is nothing per-language in `MENUDEF`.

**Where it is used is the exception list.** D22 keeps Latin for proper
nouns, calibres and key prompts. `SDMENU` is named only by the three menu
descriptors above (main, skill and, since D41, episode), and only for
strings that contain none of those; the episode names themselves are drawn
in `SmallFont`; `BigFont` and
`SmallFont` (level names, weapon tags, pickups, the skill names) are not
touched. A new `Font "SDMENU"` anywhere else must pass that test first.

Rules the strings follow (`tests/test_menudef.py`):

- `SD_MNU_*` strings are written in **capitals**. The font has no lowercase
  glyphs, and whether GZDoom draws lowercase with a capitals-only folder
  font's capitals is **NOT VERIFIED** for this font (it is what `SmallFont`
  visibly does with the skill names). Capitals make the question moot.
  Whether a font made only of our full-colour PNGs takes the `Cream` /
  `Gold` translation as `SmallFont` takes `Gold` is also **NOT VERIFIED**
  until the engine pass.
- Every character of every `SD_MNU_*` string, in both languages, has a
  glyph in `assets/fonts/sdmenu/`.
- Every main-menu item fits right of x = 97 and the header right of
  x = 32, measured as the sum of the glyph PNGs' widths (widest today:
  "НОВАЯ ИГРА", 117 px; "ВЫБЕРИТЕ СЛОЖНОСТЬ", 222 px).
- `tools/check_pk3.py` (category `menus`) fails the package when `MENUDEF`
  names a font that is neither an engine font nor a `fonts/<name>/` folder
  in the PK3.

Two engine behaviours that would replace the font, both read in
`gzdoom.pk3` (g4.14.2):

- `ui_generic` (`generic_ui` in ZScript): when a player turns it on, list
  menus draw their text in `NewSmallFont` instead
  (`zscript/engine/ui/menu/listmenuitems.zs` lines 130 and 180,
  `menucustomize.zs` line 27). That is the player's accessibility choice
  and we leave it alone.
- `MainMenuTextOnly`: the engine ships a second, text-only main menu "to be
  used with localized content" (`menudef.txt` lines 108–138), and the
  executable contains the name. When the engine switches to it is
  **NOT VERIFIED**. Evidence that it does not do so for us: the Russian
  main menu in `docs/qa/evidence/2026-10-13_1007_F2_mainmenu-ru.png` drew
  OUR redeclared `MainMenu` (logo at 60,0). If the Russian capture of D31
  ever shows the engine's strings with the logo at 94,2, redeclare
  `MainMenuTextOnly` with the same body.

No ZScript is involved in any of it. A mod may write a CVar from ZScript
only while the engine is handling menu input — `DMenu::InMenu` is raised
around `OnUIEvent`, `OnInputEvent` and `MenuEvent` and nothing else
(gzdoom: src/common/menu/menu.cpp, engine source, not a file of this repo) — so a write from `Init`, `Ticker` or `Drawer`
aborts the VM and drops the player to the console. **Do not add a menu
ZScript class that writes a CVar.**

The four redeclared menus are copies of GZDoom 4.14.2's own bodies: the
`os_Menu` anchor verbatim, `MainMenu` with the logo moved and its items
turned into text, `SkillMenu` and (D41) `EpisodeMenu` re-laid-out as above. Re-diff them against
`gzdoom.pk3/menudef.txt` on every engine upgrade (debt T14).

### 6.6.1 The mouse pointer `SDCURSOR` (D102, v1.1, 2026-10-21)

Not the menu selector (`M_SKULL1/2`, the list cursor, D48): this is the
operating-system pointer GZDoom shows over its window while a menu takes
the mouse. Read in the g4.14.2 source:

| Fact | Where |
|---|---|
| The pointer is GameInfo's `CursorPic` while the archived CVar `vid_cursor` is `"None"` (its default); a player who picks another cursor in Options › Mouse keeps it; if the picture fails, the engine's plain `"cursor"` arrow | gzdoom src/d_main.cpp, `CUSTOM_CVAR vid_cursor` |
| Doom's value is `cursorpic = "doomcurs"`; `game_support.pk3` replaces that picture with a 22×32 clawed hand (grAb 0,2), the "rabbit or monster" of D102 | `gzdoom.pk3:mapinfo/doomcommon.txt`; `game_support.pk3:graphics/doomcurs.png` |
| Windows refuses a picture over 32×32 and takes the **hot spot from the picture's offsets** (the PNG's `grAb`), as (x, y) from the top-left, scaled with the picture on high-DPI screens | gzdoom src/common/platform/win32/i_system.cpp, `I_SetCursor`, `CreateAlphaCursor` |
| macOS and Linux ignore the offsets: the hot spot is always (0, 0) | gzdoom posix/cocoa/i_video.mm (`hotSpot:NSMakePoint(0.0f, 0.0f)`), gzdoom posix/sdl/i_gui.cpp (`SDL_CreateColorCursor(…, 0, 0)`) |

The mod's answer: `CursorPic = "SDCURSOR"` in `MAPINFO`'s GameInfo (it
overrides `doomcommon.txt`'s key as `TitleMusic` does), and
`assets/graphics/shell/SDCURSOR.png`, packed as `graphics/SDCURSOR.png`:
RGBA, hard alpha, 28×25, the approved emblem geometry of SDSTAR1 v5
(imported from `gen_soviet_base`, as cursor B) upright, gold with a dark
flag-red contour (the selector's), from `tools/art/gen_mouse_cursor.py`
(no font, same pixels on every machine; review sheet
`work/art/preview/cursor_preview.png`). **The hot spot is the sickle's
tip, `grAb 12,1`.** A sickle's point lies on the blade's circle, never on
the corner of the bounding box, so on macOS/Linux the click lands 12 px left
of the tip and 1 px higher, as GZDoom's own Heretic pointer (`herecurs`,
grAb 4,4) is off there. `tests/test_mouse_cursor.py` pins the MAPINFO
line, the size limit, hard alpha and that the grAb is a sickle-tip pixel.
**NOT VERIFIED in the engine** (D26): the PM's pass opens the menu in a
window and looks.

## 6.7 The diegetic radio (D43, 2026-10-13)

D43 gave the radio two CC0 pieces; this section is the contract with
`level-designer`, who places it, and `art-director`, who draws it. Why a
music swap and not a positional sound: ADR 008
(`docs/engine/adr/008-diegetic-radio.md`). **A diegetic sound** is one
that exists inside the game world (the player's character hears it too),
as opposed to the soundtrack.

| What | Value |
|---|---|
| Class, file | `SD_Radio`, `zscript/sd/radio.zs` |
| Editor number | **21200** (§6.1; the `MAPINFO` line is owed by the PM) |
| `arg0`, the piece | `1` = `D_SDRAD1` «Эй, ухнем» (0:50); `2` = `D_SDRAD2` «Колокольчик» (0:39); `0` or anything else = `1` |
| `arg1`, the reach | map units, measured in 3D from the radio to the player; `0` = **128** (`SD_RADIO_DEFAULT_REACH`) |
| Turns on | the first tic the player is within the reach: `S_ChangeMusic(piece)`, looping |
| Turns off | the first tic the player is farther than **reach + 64** (`SD_RADIO_HYSTERESIS`): the level's own music comes back (`Level.Music`, at its `musicorder`), but only if the radio's piece is still what is playing |
| Body | `+SOLID`, radius 16, height 28 (the placeholder's 32×28 picture); not shootable, never moves |
| Sprite | `PMAP` A (IWAD placeholder, §5.1) → `SDRD` A (§6.3) |
| Lumps | `assets/music/D_SDRAD1.mid`, `D_SDRAD2.mid`: byte-identical copies of `work/audio/candidates/WM_Ej_uchnem.mid` (`D_CND09`) and `WM_Kolokolchik.mid` (`D_CND12`); rights `docs/sound/MUSIC-RIGHTS.md` §4.4–4.5, rows in `docs/art/LICENSES.md` § Music |
| `SNDINFO`, `LANGUAGE` | not involved: music lumps are named directly, and the radio prints nothing |

Rules for whoever places one:

- **The reach is a sphere and goes through walls.** Size it to the room:
  the default 128, from a radio in the middle of a 128×128 room, reaches
  about 60 units past its walls, so the doorway counts and the corridor
  outside mostly does not. A reach that leaks into a neighbouring room plays
  the radio there too.
- **Two radios' zones (reach + 64) must not overlap.** Each radio hands the
  music back only if its own piece is playing, so overlap does not leave a
  radio stuck on, but the two take the soundtrack from each other.
- **The music restarts.** MIDI cannot resume where it stopped, so the radio
  piece starts from its first bar every time the player walks in, and the
  level's music from its first bar every time they walk out. The level's
  loop heard in pieces is the price; keep radios out of rooms the player
  crosses again and again.
- **The player's music volume is the player's.** The radio never touches
  `snd_musicvolume` or the level's relative volume; with music off, the
  radio is silent, as the rest of the soundtrack is.
- **Single-player.** The listener is the local player (`consoleplayer`);
  in a network game each machine would switch its own music.

Saved games: the field that says "this radio has the music" is saved with
the actor; a second, `transient` (not saved) field makes the radio play its
piece again on the first tic after a load if it had the music when the game
was saved. Whether the engine itself restores the playing song on load is
**NOT VERIFIED**; the radio does not depend on it either way.

**NOT VERIFIED in the engine** (D26; the PM's pass, checklist in ADR 008):
that the class compiles, that `S_ChangeMusic` swaps and restores as above,
that the radio survives a save and a load, and that `PMAP` A draws.

## 6.8 Credits (G6, 2026-10-13)

The in-game credits, reasoned in `docs/engine/adr/009-in-game-credits.md`.
**Not yet seen in the engine** (the PM's batched pass, D26).

| What | Value |
|---|---|
| Where | `OptionMenu "SD_CreditsMenu"` in `MENUDEF`, reached by `Submenu "$SD_CRED_TITLE", "SD_CreditsMenu"` at the foot of our own `SD_OptionsMenu`: Options → Soviet Doom → Credits. **Not** on the main, skill or episode screens, the CEO's approved text menu (D31/D32); a main-menu row is his call (ADR 009, option C) |
| Rows | `Title "$SD_CRED_TITLE"`; one `StaticText "$SD_CRED_…"` per screen line, centred, in the engine's `NewSmallFont`; block headers `StaticText "$SD_CRED_H_…", 1` (header colour); a blank `StaticText " "` between blocks |
| Text | `LANGUAGE` ids `SD_CRED_*`, the same ids in `[enu default]` and `[ru]`, **at most 40 characters each**, no `
` (a row does not wrap). Blocks in order: team, music, engine, game data, sources (with the CC0 sound packs, `SD_CRED_SFX_1`-`_2`, D93), and "Made with AI" (`SD_CRED_H_AI`, `SD_CRED_AI_1`-`_8`, D93: Claude in Claude Code; Google Gemini for the weapons in hand, the sergeant's face and, since D109, the seven enemies; Fooocus / SDXL for the hand references and, since D108, the armband symbol's repaint in the enemies' close-up frames; Chatterbox for a few enemy voices; the long form is `CREDITS.txt`'s, `tools/release.py`) |
| Disclaimer (D46) | "A fan project, not affiliated / with id Software." / «Фанатский проект, не связанный / с компанией id Software.», `SD_CRED_FAN_1` and `_FAN_2`, the two rows right under `SD_CRED_TEAM_1` (the project's name), so it is the first thing the screen says after who made the game. The CEO's wording (D46; ADR 009 had left it to him). `tests/test_credits.py` pins the sentence in both languages inside the team block |
| Obligations | every name a licence register obliges us to credit is in the credits of both languages: `docs/art/LICENSES.md` rows whose licence says credit / `{{Attribution}}` / CC BY / BSD / MIT / OFL / CC0 and are not ours (D15), and the Obligation column of `docs/sound/MUSIC-RIGHTS.md` §4.5. Jerry Engelbach's line is MUSIC-RIGHTS §4.5's word for word in English. Enforced by `tests/test_credits.py`, which reads the registers, so a new attributed asset turns the suite red until its credit lines exist |
| Adding a credit | register row first (the name in bold, or as `credit "X"`), then `SD_CRED_*` lines in both languages, then the `StaticText` rows |

## 6.9 Draft sprite overlays (2026-10-13)

A **draft overlay** is a second PK3, loaded after the mod, that lets the CEO
play with sprites that are drawn but not approved. It is not part of the mod:
nothing in it enters `assets/`, `src/` or `dist/`, and the mod's states keep
naming the Freedoom placeholders of §5.1.

**What it no longer carries (D48, 2026-10-14).** The six weapon pickups
installed by D48 (§6.3) are out: their placeholders are no longer named by
any state, and the tool skips any swap whose sprite already sits under
`assets/sprites/` (`INSTALLED` in the tool lists the six). It still carries
the held and flash frames of the other weapons (hand E, held back by the
CEO) and the hand Katyusha's pickup. **The TT-33's held and flash frames
(N17, 2026-10-15)** ship from `assets/sprites/tt33/` and its states no
longer name `PISG`/`PISF`: the two swaps are gone and
`INSTALLED_WEAPON_FRAMES` in the tool records `PISG` → `SDTT` and `PISF` →
`SDTF`, so hand E's drafts can never be packed over them. **The Legion (D54, 2026-10-14)** ships
its own `SDLT` from `assets/sprites/legion/` and its states no longer name
`SPOS`; the overlay never carried it, and `INSTALLED_ENEMIES` in the tool
records `SPOS` → `SDLT` so that no swap can name either (a swap that did
would be skipped with a note). **The Reich rifleman and the Reich hound
(D55, 2026-10-14)** went the same way: the rifleman's swap (`POSS` ←
`SDRR`), the overlay's only enemy, is gone, the hound never had one, and
`INSTALLED_ENEMIES` records `POSS` → `SDRR` and `SARG` → `SDHN`. **The
Hybrid Stormtrooper and his bolt (D56)**, never overlaid, are recorded the
same way, `TROO` → `SDHS` and `BAL1` → `SDBL`, and so are the
Panzermensch (D67, `BOS2` → `SDPM`), the Doughboy (D70, `HEAD` → `SDDB`)
and the General with his shell (D73, `CYBR` → `SDGN`, `MANF` → `SDGL`;
`MISL`, the shell's old burst, is not recorded, because the PG-7V grenade
and the Katyusha rocket still wear it). The tool's
`enemies` group keeps the rig machinery (eight rotations, the IWAD check)
for the next enemy drafted on the rig; today it has no swap.

```sh
.venv/Scripts/python.exe tools/make_draft_overlay.py      # → work/overlays/sd-draft-sprites.pk3 (+ .txt manifest)
SD_ALLOW_ENGINE=1 tools/run.sh -file work/overlays/sd-draft-sprites.pk3   # MAP01 with the drafts on
SD_ALLOW_ENGINE=1 tools/run.sh                                            # the same build without them
```

`--only weapons|enemies` packs one group (`sd-draft-weapons.pk3`,
`sd-draft-enemies.pk3`; `enemies` is empty since D55 and refuses with
"nothing to pack"); `--hand X` takes another hand's renders from
`work/art/weapons/hand_X/<weapon>/` and refuses a hand nobody rendered (today
only hand E exists); `--dry-run` prints the plan.

**How it works.** The tool reads the frame letters each placeholder is used
with in `src/zscript/weapons/*.zs` (and an enemy swap's file under
`monsters/`; `reich_rifleman.zs` until D55), and copies our
draft for each of those frames, byte for byte (so the `grAb` offsets travel),
to `sprites/<PLACEHOLDER><frame><rotation>.png`: `SDAXA0` → `PUNGA0`
until D88 (and `SDIZA0` → `SHTGA0` until D84, `SDTTA0` → `PISGA0` until N17),
`SDRRA1` → `POSSA1` until D55, and so on through the pairs of §6.3. A draft no state
shows is not packed (the `_proposed` frames, for one); a frame with no draft keeps the
IWAD's. The 2026-10-13 overlay was 107 sprite lumps: 37 weapon frames (all
seven weapons, hand E, pickups included) and the rifleman's 70. Since D48
it was 101: 31 weapon frames (held and flash of the seven, the Katyusha's
pickup) and the rifleman's 70. Since D55 it was the 31 weapon frames;
since N17 it was 27 (the TT-33's four ship); since D79 it was 24 (the
PPSh-41's three ship); since D84 it was 4, the ice axe's held frames alone
(the IZh-58's, RPG-7's, ROKS-3's and hand Katyusha's 19 frames and the
Katyusha's pickup ship). Since D88 it is empty: the ice axe's four ship, no swap is left, and
the tool says "nothing to pack" and writes nothing until a weapon or an
enemy is drafted again.

**Sprite resolution across files** (why a partial frame is refused):

| Finding | Status |
|---|---|
| GZDoom collects every `-file` on the command line in order (`FArgs::CollectFiles` in GZDoom's src/common/utility/m_argv.cpp), and `run.sh` passes its extra arguments after its own `-file dist/sovietdoom.pk3`, so the overlay loads last | VERIFIED in the g4.14.2 source and by reading `run.sh` (`tests/test_draft_overlay.py` pins the `run.sh` half); NOT VERIFIED in the engine |
| A lump whose full name exists in two files becomes a texture only from the later file (`FTextureManager::AddGroup`: "to keep earlier entries from overriding later ones") | VERIFIED in the source |
| Sprite frames are assembled per rotation slot; the textures of later files are visited first, and a slot already filled is never overwritten (`R_InstallSpriteLump` / `R_InitSpriteDefs` in GZDoom's src/r_data/sprites.cpp) | VERIFIED in the source; NOT VERIFIED in the engine |
| Hence: an overlay frame with all of rotations 1-8 hides Doom II's mirrored pairs (`POSSA2A8` finds both its slots taken); a frame with only some rotations would be completed by the IWAD's drawing; a rotation-0 frame of ours fills all slots and hides any IWAD frame | inferred from the two rows above; NOT VERIFIED in the engine |
| Freedoom 0.13.0 draws `POSS` A-G as eight separate rotations, with no mirrored pairs, and H-U as rotation 0; Doom II's `doom2.wad` uses pairs | Freedoom VERIFIED by reading `iwads/freedoom2.wad`; Doom II from memory, NOT VERIFIED |

The tool therefore refuses a rotated frame without all eight rotations, a
frame mixing rotation 0 with 1-8, and, when the IWAD is present, a rotated
frame the IWAD has as rotation 0 or as 16-angle rotations 9-G.

**Side effects to expect.** The swap is by sprite name, so every actor that
names those sprites wears the draft: Doom's `DeadZombieMan` (editor number
18) lay as our rifleman's corpse while the rifleman was overlaid (until
D55), and Freedoom's own weapon classes
would look like ours (none is reachable: §5, §6). The PK3 is not checked by
`check_pk3.py`, which validates the mod only; its PNGs are RGBA as drawn.

## 6.10 After death: "Press <key> to continue" (D100, v1.1, 2026-10-21)

When the player dies Doom lays the view on the floor and waits for USE,
saying nothing (D100). What USE then does, read in the g4.14.2 source:

| Step | Source |
|---|---|
| `PlayerPawn.DeathThink`: with `BT_USE` (a human player does not wait for `respawn_time`), `playerstate = PST_ENTER` in single player; `PST_REBORN` only in multiplayer, with `allowrespawn`, `sv_singleplayerrespawn` or a skill's `PlayerRespawn`, none of which the mod sets | `gzdoom.pk3:zscript/actors/player/player.zs` 767-773 |
| `G_Ticker` hands a `PST_ENTER`/`PST_REBORN` player to `DoReborn` | gzdoom src/g_game.cpp 1156-1158 |
| `DoReborn`, single player: **"Load game from the last point it was saved"** — `BackupSaveName`, the last save written (`G_DoSaveGame`, 2497: autosave, quicksave or the player's own) or loaded (2189) — unless `cl_restartondeath` is on or there is none; else **"Reload the level from scratch"**, `G_InitNew(MapName)`: the same map, a fresh player (pistol start) | gzdoom src/g_game.cpp 1773-1787 |
| The level-entry autosave: made on a map change (`G_DoWorldDone` → `G_DoLoadLevel(…, autosave = true)`), not on New Game (`autosave = false`, and `BackupSaveName` is cleared), while `disableautosave` < 1, never while dead; `autosavecount` 0 also stops it | gzdoom src/g_level.cpp 1578, 659, 502, 1527; gzdoom src/d_net.cpp 2518-2530 |

So with the engine's defaults (`cl_restartondeath` false, `disableautosave`
0, `autosavecount` 4: the CEO's `gzdoom.ini` has exactly these) **USE
continues in the same map**: MAP01 restarts from its start; MAP02 and MAP03
reload the autosave made on entering them, with what the player carried in;
a player who saved by hand goes back to that save. Nothing is changed.

The mod adds the words only: `SD_DeathPrompt` (`zscript/sd/death_prompt.zs`,
registered by `AddEventHandlers`) counts the console player's tics in
`PST_DEAD` in `WorldTick` (a paused game does not count) and, after
**52 tics (~1.5 s)**, draws `LANGUAGE`'s **`SD_DEATH_PROMPT`** ("Press %s to
continue"; `%s` is the key) centred on the screen in `RenderOverlay`,
blinking (24 tics on, 11 off). The key is the first one bound to `+use`
(`Bindings.GetKeysForCommand`, named by `KeyBindings.NameKeys`: "E",
"Space", "Mouse2"), or the engine's `$CNTRLMNU_USE` ("Use / Open") when
nothing is bound. Font: `BigFont` (ours, no Cyrillic substitution, so a
key named E reads E; §6.6's SDMENU rule), gold, at the menus' integer scale
`CleanXFac` or less so the line fits 90 % of the width; when not even scale 1
fits (the Russian line at 320×200) `SmallFont`; `NewSmallFont` under
`ui_generic`. `tests/test_death_prompt.py` pins the include, the
registration, the constants, the key lookup and that every character of
the string in every language has a glyph in both fonts. **NOT VERIFIED in
the engine** (D26): the PM's pass dies in MAP01 and in MAP02, at 320×200
and at 16:9, in English and Russian, and presses the key.

## 6.11 Episodes 2 and 3's music: A/B variants and the boss loops (D106, D113, 2026-10-22)

The CEO approved two pieces per map of episode 2 (D106) and of episode 3
(D113, unheard) and the PM chose to play both. `SD_MusicVariant` (`zscript/sd/music_variant.zs`, an `EventHandler`
registered by `AddEventHandlers` after `SD_DeathPrompt`) does it; MAPINFO
keeps naming the A, so with the handler off every map plays its A.

| Table row (`MusicCell`) | A (= MAPINFO `music`) | B | Boss with A | Boss with B |
|---|---|---|---|---|
| MAP04 | `D_SDM04A` | `D_SDM04B` | — | — |
| MAP05 | `D_SDM05A` | `D_SDM05B` | — | — |
| MAP06 | `D_SDM06A` | `D_SDM06B` | `D_SDBS6A` | `D_SDBS6B` |
| MAP07 (D113) | `D_SDM07A` | `D_SDM07B` | — | — |
| MAP08 (D113) | `D_SDM08A` | `D_SDM08B` | — | — |
| MAP09 (D113) | `D_SDM09A` | `D_SDM09B` | `D_SDBS9A` | `D_SDBS9B` |

| When | What it does | Engine fact it rests on (g4.14.2) |
|---|---|---|
| `WorldLoaded`, a fresh map with a row | draws `random[SD_MusicVariant](0, 1)` (a play RNG: per-game seed, network-safe); on 1, `S_ChangeMusic(B)` | `P_SetupLevel` has already started the A (`Level.SetMusic()`, src/p_setup.cpp 446-451) before `WorldLoaded` fires (src/g_level.cpp 1520-1522) |
| `WorldLoaded` of a savegame or a hub return | nothing | the save holds the song that was **playing** and restarts it (`FLevelLocals::SerializeSounds`, src/p_saveg.cpp 572-593; it falls back to the level's `music` only if that fails); the handler's `variant`, `bossStarted` and `bosses` are saved with the level (src/p_saveg.cpp 1024-1027) |
| MAP06 and MAP09 (the rows with boss lumps): the first time a tracked BOSS monster has a player as `target` (polled every 4 tics) or a player damages one (`WorldThingDamaged`) | `S_ChangeMusic` to the boss loop of the drawn variant; it plays to the end of the map | BOSS monsters are found by flag (`bBOSS && bISMONSTER`): those on the map at `WorldLoaded` (a `ThinkerIterator`) and any spawned later (`WorldThingSpawned`). Today that is `SD_General` standing in; `SD_LibertyColossus` on MAP06 and a final boss on MAP09 later (D112), with no change here |
| Once a second | if the A is playing but the map wants B or the boss loop, puts it back | `SD_Radio` gives back `Level.Music` (§6.7), always the A; the same check repairs a load whose saved song failed to restart |

MAP03, whose General is also a BOSS, has no row: its music never changes.
Switches: `SD_MUSIC_VARIANTS_ENABLED = 0` plays always A;
`SD_BOSS_MUSIC_ENABLED = 0` drops the boss loop. A death that reloads the
entry autosave keeps the variant (it is a load); one that restarts the map
from scratch (no save, §6.10) draws again. The stats screen cannot follow
the draw: no handler ticks there and its music is MAPINFO's (§4.5), so the
intermission is `D_SDE2IA` / `D_SDE3IA` whichever variant played, and
`D_SDE2IB` / `D_SDE3IB` ship unwired. `tests/test_music_variant.py` pins the include, the registration,
the switches, the table against MAPINFO and the package, and the behaviour
above in the code. **NOT VERIFIED in the engine** (D26): the PM's pass
checks `currentmusic` on MAP04-09 over several New Games (both variants
appear), a save and load on a B (still B), the boss loop when the boss of
MAP06 and of MAP09 sees the player, none on MAP03, and the intermission
after MAP04 and MAP07.

## 6.12 Provisional looks: the P4 actors before their art (D116, 2026-10-22)

The CEO draws the remaining art with Gemini, a little at a time as the
account allows, and **no other image generator** (D116). So that the
gameplay is ready now and only the drawing changes later, the P4 actors
are in the mod wearing **sprites the mod already ships**, changed in code
only; **no new PNG enters `assets/`** for them.

| Class | File | Wears today | How it is told apart | Final (§6.3) |
|---|---|---|---|---|
| `SD_LegionGunner` | `zscript/monsters/legion_gunner.zs` | **its own `SDLG` since D123** (from D116 the trooper's `SDLT`, frame for frame) | nothing left to tell: the `Translation` to brass is gone | `SDLG`, installed |
| `SD_LibertyColossus` | `zscript/monsters/liberty_colossus.zs` | **its own `SDLC` since D123** (from D116 the General's `SDGN`, Q/R the stomp) | nothing left: `Scale 1.3` and the chrome `Translation` are gone from his file and live on as the Chrome Marshal's design (`SD_ChromeGeneral`, below) | `SDLC`, installed |
| `SD_Consortium` (and the `SD_ConsortiumWounded` fixture) | `zscript/monsters/consortium.zs` | **its own `SDCN` since D128** (from D116 the heavy Panzermensch's `SDPS`) | nothing left to tell: `Scale 1.75` and the cobalt `Translation` are gone; Spawn and the rooted `See` show Q R, the Breach's first two frames S (`tests/test_ep3_boss.py`) | `SDCN`, installed |
| `SD_Akm` | `zscript/weapons/akm.zs` | **its own `SDAK` A–B, `SDAF` A, `SDAQ` A since D128** (from D116 the PPSh-41's `SDPP`, `SDPF` and the tinted `SDPQ`, letter for letter) | nothing left to tell: the pickup's `Translation` is gone; `tests/test_akm_sprites.py` pins the states | `SDAK`, `SDAF`, `SDAQ`, installed |
| `SD_AkmAmmo` | `zscript/sd/ammo.zs` | the 7.62×25 magazine's `SDCL` A; icon `SDCLA0` | `Translation` (plum-orange) on the floor | `SDAM` |
| `SD_Rgd5` (V3) | `zscript/weapons/rgd5.zs` | **its own `SDRG` A–D in hand and `SDRQ` A on the floor since D133** (from D116 the ice axe's `SDAX` A–D and the health bonus's `SDHB` (borrowed from `SD_HealthBonus`) A, letter for letter) | nothing left to tell: the pouch's `Translation` and `Scale 1.4` are gone; `tests/test_rgd5_sprites.py` pins the states | `SDRG`, `SDRQ`, installed |
| `SD_Rgd5Ammo`, `SD_Rgd5Box` (V3) | `zscript/weapons/rgd5_ammo.zs` | **their own `SDRJ` A and `SDRZ` A since D133**; icon `SDRJA0` (from D116 `SDHB` (borrowed from `SD_HealthBonus`) A, the PG-7V crate's `SDRB` A, icon `SDHBA0`) | nothing left to tell: the `Translation` is gone | `SDRJ`, `SDRZ`, installed |
| `SD_Rgd5Grenade` (V3) | `zscript/weapons/rgd5_grenade.zs` | **its own `SDRN` A since D133** (from D116 `SDHB` (borrowed from `SD_HealthBonus`) A); the burst the PG-7V's `SDPX`, which stays | nothing left to tell: the `Translation` is gone | `SDRN`, installed |

**Swapped by D123 (2026-10-23).** The gunner's and the colossus's swaps
were done by the art-director's install patches
(`work/art/enemies_gemini/gunner/legion_gunner.zs.patch` and
`colossus/liberty_colossus.zs.patch`, `git apply`, the same result as the
`sed` below, plus their headers): no `PROVISIONAL-D116` line is left in
either file, and `tests/test_ep2_enemies.py` holds that (`SWAPS` empty,
`test_the_final_looks_are_installed`). **Not provisional, and so not
marked:** `SD_ChromeGeneral` (`zscript/monsters/chrome_general.zs`, D123)
wears `SDCM` (the General's `SDGN` with a US-flag armband, V3) at `Scale 1.3` with the colossus's old chrome
`Translation` as its approved design, the colossus's state machine line
for line; its tint carries no mark because no art will replace it.

**Swapped by D128 (2026-10-24).** The Consortium's and the AKM's swaps
were done by their install patches
(`work/art/enemies_gemini/consortium/consortium.zs.patch`, with the two
state edits the drawing adds, and
`work/art/weapons/hand_G/akm/install/akm-install.patch`): no
`PROVISIONAL-D116` line is left in `consortium.zs` or `akm.zs`;
`tests/test_ep3_boss.py` (`test_its_own_look_is_installed`) and
`tests/test_akm_sprites.py` hold that.

**Swapped by D133 (2026-10-25, the CEO: "Ok granada").** The RGD-5's
swaps (V3, on the `v3` branch) were done from
`work/art/weapons/hand_G/rgd5/install/` (the patch made against an older
`v3`, applied by hand where `v3` had moved): `SDAX` → `SDRG`, `SDRB` →
`SDRZ`, and the health bonus's sprite borrowed from `SD_HealthBonus` →
`SDRQ` / `SDRJ` / `SDRN`, with the icon;
no `PROVISIONAL-D116` line is left in `rgd5.zs`, `rgd5_ammo.zs` or
`rgd5_grenade.zs`, and `tests/test_rgd5.py`
(`test_its_own_look_the_swaps_done`) and `tests/test_rgd5_sprites.py` hold
that. The only marked line left in the mod is `SD_AkmAmmo`'s (`SDAM`,
below).

**The rule.** Every line of code that exists only because the art is not
drawn carries the comment mark `PROVISIONAL-D116`: the `Translation`, the
`Scale` and its constant. Nothing else does. A `Translation` on a
truecolour PNG makes GZDoom palettise it first, so the tint may look
coarser than the sprite (**NOT VERIFIED** in the engine; cosmetic).

**The swap when Gemini's frames land** (after the CEO approves them and
`art-director` installs them in `assets/sprites/<set>/`, with `grAb` and
licence rows): each class's header carries the exact command, one `sed`
that renames the sprite at the start of each state line and deletes the
marked code lines, for example

```sh
sed -i -e 's/^\(\s*\)SDLT /\1SDLG /' -e '/^\s*[^/[:space:]].*PROVISIONAL-D116/d' src/zscript/monsters/legion_gunner.zs
```

The colossus's is the same with `SDGN` → `SDLC`; the AKM's renames three
sprites (`SDPP` → `SDAK`, `SDPF` → `SDAF`, `SDPQ` → `SDAQ`). Two need a
little more: the **Consortium** also shows `SDCN` Q R in the rooted `See`
and S in the Breach's first two frames (states the drawing adds), and
**`SD_AkmAmmo`** renames `SDCL` → `SDAM` in its `Spawn` line and its
`Inventory.Icon` by hand. Every tic, action and jump stays. The tests
(`tests/test_ep2_enemies.py`, `test_ep3_boss.py`, `test_akm.py`) run the
documented swap in Python and check it leaves only the final sprite and no
tint, and they turn red the day a final sprite is installed and the swap
is not done.

**Sounds** follow the same idea through `SNDINFO` (§6.2, "P4 sounds"): own
logical names now, own lumps later, one line each.

## 6.13 Between levels: the operations map and the end-of-episode awards (V3 B1/B3, ADR 013, 2026-10-23)

**Proposal on the V3 branch** (the awards wait for the CEO: political
symbols; preview `docs/art/previews/2026-10-23_V3_ops-map-medals.png`).
Why this way and not another: ADR 013.

**The operations map (B1).** Every campaign map, MAP01–MAP09, names
`exitpic = "$SDOPSCR"` and `enterpic = "$SDOPSCR"` in MAPINFO: the stats page
after it and the "Entering" page before the next one are drawn over the
intermission script `SDOPSCR` (root lump; the language of gzdoom.pk3's
`in_epi1.txt`…`in_epi3.txt`). The range has `nointermission` and no map.

| On the… | the engine draws (in this order) | script lines |
|---|---|---|
| stats page of MAPn | `SDOPMAP`; the arrows `SDOPR02`…`SDOPR0n`; a star `SDOPSTAR` on MAP01…MAPn; the gold pulse `SDOPCUR0/1` (12 tics a frame) on MAPn; then Doom's figures over it | `IfLeaving MAPm Pic …` for every m ≥ the arrow's or star's map; `IfLeaving MAPn Animation …` |
| "Entering" page of MAPn+1 | `SDOPMAP`; arrows up to `SDOPR0(n+1)`; stars on MAP01…MAPn; the splat (`SDOPSTAR` again) on every visited site; the blinking ring `SDOPYAH0` on MAPn+1 (the `Pointer`, drawn only if it fits the screen); then "Entering" and the name | `IfEntering MAPm Pic …`; `Splat`; `Pointer`; `Spots` |

Progress never uses `IfVisited`, so starting episode 2 or 3 from New Game
still shows the road from Zarya-7 travelled. Sites (the script's `Spots`,
320×200): MAP01 (119,146), MAP02 (110,135), MAP03 (100,120), MAP04 (105,106),
MAP05 (68,106), MAP06 (70,88), MAP07 (134,65), MAP08 (106,56), MAP09 (182,125);
nothing above y = 45, where the engine prints the map name. Pictures: RGBA,
hard alpha, palette v2; the markers' grAb at their centre, the arrows' at
0,0 (the script places them by their box's corner). **`SDOPSCR` is
generated**: edit `tools/art/gen_ops_map.py` and run it with `--install`
(`tests/test_ops_map.py` compares the file with the generator).

**The awards (B3).** GameInfo `statscreen_single = "SD_StatusScreen"`
(`zscript/sd/status_screen.zs`), a `DoomStatusScreen` whose stats page is
untouched. After the stats of the last map of an episode (`wbs.next == ""`,
level number 3, 6 or 9: MAP03, MAP06, MAP09) it shows the **awards page**
instead of finishing: the map dimmed (`Screen.Dim`, 0.72), the title
(`SD_AWARDS_TITLE`, BigFont, gold), the episode's New Game name, four
columns (`SD_AWARDS_KILLS` %, `SD_AWARDS_SECRETS` n/m, `SD_AWARDS_TIME`,
`SD_AWARDS_PAR`, SmallFont), then five rows, one every 18 tics with
`intermission/nextstage` for each earned: the picture (darkened by a
black `DTA_ColorOverlay` of alpha 170 when not earned), the name
(`SD_MEDAL_*_NAME`, gold or dark grey) and the rule (`SD_MEDAL_*_RULE`, up to
two lines, `Font.BreakLines`). A key reveals every row
(`intermission/paststats`), the next one leaves; `wi_autoadvance` is
honoured. Then the cluster's ending text and the title screen (§4.6).

| Award | Lump | Earned when (the episode's three maps summed; `BALANCE.md` §9) |
|---|---|---|
| Medal "For Courage" | `SDAWCOU` | the episode completed |
| Order of the Red Star | `SDAWRST` | kills ≥ 75 % |
| Order of the Red Banner | `SDAWRBN` | secrets = 100 % (none in the episode counts 100) |
| Order of the Patriotic War | `SDAWPTW` | time ≤ the sum of the maps' `par` |
| Gold Star, Hero of the Soviet Union | `SDAWHER` | all three maps played in this game, kills ≥ 90 %, every secret, within par, skill 3 («Not one step back», SpawnFilter Normal) or harder |

**The figures.** `SD_AwardsRecorder` (`zscript/sd/awards.zs`, an
`EventHandler` after `SD_MusicVariant` in `AddEventHandlers`) writes, every
tic of a MAPxx level, the level's `killed_monsters`, `total_monsters`,
`found_secrets`, `total_secrets`, `time` (tics), `partime` (s) and the skill's
`SpawnFilter` into slot `levelnum` of each player's **`SD_CampaignLedger`**,
an `Inventory` given on the first tic (`MaxAmount 1`, `InterHubAmount 1` so a
map change keeps it, `UNDROPPABLE`, `UNTOSSABLE`, `UNCLEARABLE`, not in the
inventory bar). It travels with the player and is saved with the player;
New Game, or a death that restarts a map from scratch (§6.10), starts a new
one. The awards page reads the episode's first maps from it and the last map
from its own `wbs`. The rules are `SD_Awards` (data scope, integer maths
only). `tests/test_awards.py` pins the wiring, the ledger, the thresholds
against `BALANCE.md` §9, worked cases, the five pictures, the LANGUAGE ids in
the three languages (every glyph drawn, every line fitted) and the layout
against the preview's. **NOT VERIFIED in the engine** (D26): the pass ADR 013
lists.

## 6.14 The propaganda radio's loudspeaker (V3 B5, D124, 2026-10-24)

D124 approved the propaganda radio in full: sixteen Radio Moscow lines, the
three station jingles, no subtitles. The design, the script and the room
table are `docs/sound/2026-10-23_V3_propaganda-radio.md` (§5); this is the
contract with `level-designer`, who places it. Unlike `SD_Radio` (§6.7) it
does **not** touch the music: it is a positional sound over it.

| What | Value |
|---|---|
| Class, file | `SD_Loudspeaker`, `zscript/sd/loudspeaker.zs` |
| Editor number | **21201** (§6.1, in `MAPINFO`) |
| `arg0`, the playlist | a **bit mask** of the sixteen lines, bit n-1 = line n (`sd/radio/line/nn`); `0` = all sixteen. (The design proposed an index into a ZScript table; a mask keeps each map's choice in the map's own file.) |
| `arg1`, the reach | map units, 3D, to the local player; `0` = **384** (`SD_LS_DEFAULT_REACH`) |
| `arg2`, the pause | seconds of silence between lines; `0` = **6** (`SD_LS_DEFAULT_PAUSE`), plus a random 0-**4** (`SD_LS_PAUSE_JITTER`) |
| `arg3`, flags | **1** = no jingle (`SD_LS_FLAG_NO_JINGLE`); **4** = the valve bed in a loop while on (`SD_LS_FLAG_BED`); **8** = olive (`SD_LS_FLAG_OLIVE`, the army's `SDLO`; unset, the grey `SDLS`; D132); 2 is kept for a visible horn |
| `arg4`, the jingle | `1`-`3` one of `SDRADJ1`-`3`; `0` = a random one each time |
| Turns on | the first poll (every **8** tics, `SD_LS_POLL_TICS`) the player is within the reach: the jingle (unless flagged off, or a line is still playing), the bed if flagged; the first line **1** s after the jingle (`SD_LS_JINGLE_GAP`) |
| Plays | when nothing plays on `CHAN_VOICE` and the pause has passed, the next line from a **shuffle bag**: every line of the playlist once before any repeats, never the same line twice in a row |
| Turns off | farther than **reach + 128** (`SD_LS_HYSTERESIS`): no new line starts; the line in progress finishes, then the bed stops |
| Coming back | the jingle again only after **60** s away (`SD_LS_JINGLE_COOLDOWN`) |
| Volume | `SD_LS_VOLUME` **0.7**, the bed `SD_LS_BED_VOLUME` **0.3**, `ATTN_NORM`; the falloff is `SNDINFO`'s `$rolloff` (§6.2), full within 128, silent at 768 |
| Body | the street loudspeaker (`assets/sprites/loudspeaker/`, `tools/art/gen_loudspeaker.py`) in two colours (D132, "Ambos! A y B", both A and B): grey `SDLS` (the sheet's option A) by default, olive `SDLO` (option B, the same drawing) with flag **8**, entered from `PostBeginPlay` as the state `Olive` (**NOT VERIFIED**); a pole with two horns, one picture for every angle (`A0`), 69 units tall; frame B (the pilot lamp lit, the horns shaken) alternates with A on every poll while something plays (`frame` written from `Tick`, **NOT VERIFIED**); `+NOINTERACTION`, seen but never touched; not shootable |
| Saved games | the on flag, the bag, the last line and the timers are saved; a `transient` field restarts the bed after a load |

Rules for whoever places one:

- **One or two a map** (V3: MAP04-MAP09, and Episode 1 since the PM
  scheduled it on 2026-10-24), in a big room the player crosses and
  lingers in. Each map's table `LOUDSPEAKERS` in its
  `map.py`: `(zone, x, y, lines, reach, flags, jingle)`.
- **Two zones (reach + 128) must not overlap**, nor an `SD_Radio`'s
  (reach + 64): two broadcasts at once is noise.
- **The story filter:** RAD11 (Zarya-7 holds) is Episode 1's only (MAP01's
  komnata); RAD15 (Tankograd's plan) from MAP03 on; RAD02 (the Volga dam)
  from MAP06 on.
- **Where it stands is what it covers.** The reach is a sphere through
  walls, as the radio's.
- **The colour follows the place (D132):** grey (`SDLS`, flags without 8)
  in the city, the red-brick works and the Kremlin; olive (`SDLO`, flag 8)
  in the army's installations. Today: olive in MAP01 (Zarya-7), MAP07
  (Novaya Zemlya's barracks), MAP08 (Severomorsk) and MAP09 (the Tunguska
  outpost); grey in MAP02-MAP06.

Placed today (2026-10-24): MAP01 the komnata and the hangar; MAP02 the
central hall; MAP03 the assembly hall; MAP04 the platform; MAP05 the turbine hall;
MAP06 Red Square and the GUM's atrium; MAP07 the barracks; MAP08 the mess;
MAP09 the station yard, with the bed. `tests/test_loudspeaker.py` pins the
class, the numbers above, the sounds, the licences and the placements.
**NOT VERIFIED in the engine** (D26): that the class compiles, the shuffle,
the turn-off and the jingle's cooldown, the `$rolloff`, the bed's loop
(seam and restart after a load), the speaking frame and the olive state.

## 6.15 Weapon reloads, the V3 experiment (D132, ADR 014, 2026-10-25)

Branch `v3-reload` only: an option the CEO plays with and without (a nice
to have, D121). Design and the engine checks R1-R14:
`docs/engine/2026-10-25_V3_reloads.md`; the numbers: `BALANCE.md` §10.

| What | Value |
|---|---|
| The switch | CVar **`sd_reloads`**, `server bool`, default **true** on this branch (`src/lumps/CVARINFO`); the row Options > Soviet Doom > "Weapon reloads" (`MENUDEF`, `Option ... "OnOff"`), strings `SD_OPTMNU_RELOADS`, `SD_OPTMNU_RELOADHELP` in `[enu default]`, `[ru]`, `[ca]`. Off = v1.2's tics exactly |
| The key | `+reload` (the engine's `BT_RELOAD`); `KEYCONF` `defaultbind r +reload` (only if neither R nor `+reload` is bound); the engine's Customize Controls row "Reload" |
| Code | `zscript/weapons/magazine.zs`: `SD_Reloads` (static: `On()`, `ReloadOffset()`, `Magazine()`) and `mixin class SD_MagazineWeapon` (fields `sdMagFired`, `sdReloadTic`; `override DepleteAmmo`; `A_SD_BeginReload`, `A_SD_ReloadTick`) |
| Guns | `SD_Tokarev` 8 (`SD_TT_MAGAZINE`), `SD_Ppsh` 71 (`SD_PPSH_MAGAZINE`), `SD_Akm` 30 (`SD_AKM_MAGAZINE`), `SD_Roks3` 80 (`SD_ROKS3_TANK`); each with `SD_*_RELOAD_TICS`, `_RELOAD_DROP`, `_RELOAD_SOUND_TIC`. `SD_Izh`: its two barrels, plus `+reload` after one (`SD_CanReloadIzh`). None for the ice axe, RPG-7, hand Katyusha, RGD-5 |
| States, per gun | a 0-tic guard `A_JumpIf(invoker.SD_MagazineDry(...), "Reload")` as the first `Fire` frame (and before the PPSh-41's B round); `A_SD_WeaponReady` returns `Reload` on a dry magazine (no pending switch) and passes `WRF_ALLOWRELOAD` when a reload would load; new labels `Reload` (a 0-tic `SD_CanReload` check, `A_SD_BeginReload`) and `ReloadLoop` (the ready frame, 1 tic, `A_SD_ReloadTick`, repeated `*_RELOAD_TICS` times), then `Goto Ready` |
| Ammo | a counter over the pool (`Clip`, `SD_AkmAmmo`, `Cell`): no round created, lost or moved; the maps' ammunition is untouched |
| Animation | no new sprite: the ready frame lowered 32 → 128 and raised (`A_WeaponOffset`, `WOF_INTERPOLATE`); the reload sound on its tic (§6.2), the refill as the gun rises |
| Readout | `SD_MagazineHud` (`zscript/sd/magazine_hud.zs`), last in MAPINFO's `AddEventHandlers`: "rounds/capacity" in SmallFont (gold; red when empty) right-aligned at x 44, y 158 with the bar, x 290, y 170 over the fullscreen HUD, none at screenblocks 12 or on the automap |
| Saved games | `sdMagFired` and `sdReloadTic` are ordinary fields, saved; 0 is a full magazine, so older saves load full |

`tests/test_reloads.py` pins all of the above; `tests/_v3_reload_states.py`
is the table of state edits the sprite suites apply to their pinned
"before" states. **NOT VERIFIED in the engine** (D26).

## 6.16 The episode endings' illustrations (V3 B2, D132, 2026-10-25)

**Proposal on the `v3-endings` branch** (the pictures and the armband
symbol wait for the CEO: `docs/art/previews/2026-10-25_V3_episode-endings.html`).
**NOT VERIFIED in the engine** (D26): everything below is read from the
engine's own definitions (gzdoom.pk3 `mapinfo/common.txt`, `mapinfo/doom1.txt`)
and parser names, not seen run.

**The order of the screens** when MAP03, MAP06 or MAP09 is left:

| # | Screen | Who draws it |
|---|---|---|
| 1 | the stats over the operations map | `SD_StatusScreen` (§6.13, ADR 013 B1) |
| 2 | the awards page | `SD_StatusScreen`'s ShowNextLoc state (ADR 013 B3) |
| 3 | the ending text (`SD_END01/03/04_TEXT` over `SDFLR1`, silent) | the episode's ending cluster (§4.6), unchanged |
| 4 | **the illustration**, full screen, 4:3 (pillarboxed on a wide screen, like `TITLEPIC`), silent, until a key | `Intermission SD_EndingN`, `Image { Background = "SDENDn" }` |
| 5 | the title screen and its music | the same sequence's `GotoTitle`, as the engine's own `Inter_Titlescreen` (`endtitle`) |

**How.** The map says `next = EndSequence, "SD_EndingN"` (N = 1, 2, 3 for
MAP03, MAP06, MAP09) instead of `endtitle`; `MAPINFO` defines the three
`Intermission` blocks, each an `Image` with no `Time` (waits for a key, as
Doom 1's `Inter_Pic1`) and a `GotoTitle`. The engine prints the cluster's
`exittext` first and then links to the map's end sequence, which is Doom 1's
own order (E1M8: `next = "EndGame1"`, the text, then the picture), so the
text comes before the picture without new code. `wbs.next` is `""` for an
end sequence of any name, so the awards page still starts (ADR 013).
Rejected: the picture **before** the text (the three ending texts would have
to move from the clusters into `TextScreen` actions, drawn by another path:
font, colour and layout to be checked again in three languages) and the
picture **behind** the text (eight to ten lines over a painting do not read
without dimming it to half). The range keeps `endtitle`.

| Lump | Size | Where | Generator |
|---|---|---|---|
| `SDEND1` | 320×200, indexed, palette v3 | `assets/graphics/endings/` → `graphics/` | `tools/art/gen_endings.py` (Gemini painting, local, D77; the armband symbol, D108) |
| `SDEND2` | 320×200, indexed, palette v3 | same | same |
| `SDEND3` | 320×200, indexed, palette v3 | same | same (the armband symbol) |

`tests/test_endings.py` holds the contract: the three sequences, their
pictures packed and 320×200, each episode's last map naming its own, the
range still on `endtitle`, the generator's lumps the same as MAPINFO's.
The engine pass (the PM): finish MAP03, MAP06 and MAP09 (`-warp`, kill the
boss, exit) and see stats → awards → text → picture → title, at 4:3 and
16:9, the log clean (no "Unknown intermission", no "Unknown texture").

## 7. Commands

```sh
python3 tools/build.py                       # → dist/sovietdoom.pk3
python3 tools/build.py --print-textmap MAP01 # show the generated UDMF
python3 -m unittest discover -s tests -v     # build tests
tools/run.sh                                 # build + gzdoom + logs/gzdoom.log
MAP=RANGE tools/run.sh                       # the practice range (the F4 arsenal test range)
MAP=MAP01 SKILL=4 IWAD=/path/doom2.wad tools/run.sh -nosound
tools/run.sh -nosound +vid_fullscreen 0 +screenshot_dir "$PWD/logs/shots" +"wait 140; screenshot; wait 35; quit"  # QA evidence
python3 tools/smoke.py --map MAP01 --skill 4 [--keep-evidence]  # build + self-quitting GZDoom run + log analysis (exit 0 = clean)
python3 tools/check_pk3.py [--json] [--strict]   # static PK3 validation, no engine: lumps, map WADs, referenced textures, PNG palette, sprites, licences, #includes, fonts named by MENUDEF (exit 0 = clean)
```

`run.sh` looks for GZDoom in `/Applications/GZDoom.app/Contents/MacOS/gzdoom`,
`~/Applications/…`, on Windows `%LOCALAPPDATA%\Programs\GZDoom\gzdoom.exe`
and `%ProgramFiles%\GZDoom\gzdoom.exe` (the same order as `smoke.py` and
`audition.py`), and `PATH` (or `GZDOOM=`); the IWAD in `iwads/`,
`~/Library/Application Support/gzdoom/` and `$DOOMWADDIR` (or `IWAD=`),
preferring `freedoom2.wad`. It refuses to start the engine unless
`SD_ALLOW_ENGINE=1` is set (the engine gate, `docs/PIPELINE.md` stage 5).
It always writes `logs/gzdoom.log`; `qa-engineer` greps it for `Script
error`, `Unknown texture`, `Missing sprite`: any hit is a failure. On
Windows the commands above run the same under Git Bash with `python` in
place of `python3`; `run.sh` picks the venv interpreter itself. Screenshots
come from the engine's `screenshot` command on both systems (macOS
`screencapture` cannot see the game window).

## 8. Art tooling

Python virtualenv at `.venv/` (gitignored) with Pillow and numpy for
`tools/art/`. Create with `python3 -m venv .venv && .venv/bin/pip install
pillow numpy`.

## 9. Balance

Every gameplay number of the arsenal, and the reason for it, lives in
`docs/engine/BALANCE.md`. This file owns *names and structure*; that one
owns *values*. The code owns both as named constants — if a doc and the code
disagree, the code is right and the doc is the bug.

## 10. Known technical debt

Order note: rows are not strictly numeric (T16, T18-T21, T17, T22, T23): T17 was filed after T18-T21 and nothing is renumbered, since other documents cite the T-numbers.

| # | Debt | Pay it in |
|---|---|---|
| T1 | Every weapon sprite and sound is a Freedoom placeholder (§6.2, §6.3). **Partly paid 2026-10-14 (D48):** the six world pickups are ours (§6.3, "Installed since D48"). **N17 (2026-10-15):** the TT-33's held and flash frames are ours (§6.3, "The TT-33 in hand"). **D79 (2026-10-20):** the PPSh-41's too (§6.3, "The PPSh-41 in hand, installed by D79"). **D84 (2026-10-20):** the IZh-58's, RPG-7's, ROKS-3's and hand Katyusha's held and flash frames, and the Katyusha's pickup (§6.3, "The IZh-58, RPG-7, ROKS-3 and hand Katyusha in hand, installed by D84"); the weapon sounds were paid by N9 (D74). **D88 (2026-10-20):** the ice axe's held frames (§6.3, "The ice axe in hand, installed by D88"): every held, flash and pickup sprite of the arsenal is ours. **D82 (2026-10-20):** the projectiles too, `SDPG`, `SDKR`, `SDPX`, `SDFJ`, `SDFX` (§6.3, "The player effects, installed by D82"): **the sprite part of T1 is paid**; not yet seen in the engine (D26). | F4, once `art-director` redraws the hands and `sound-designer`'s sounds pass the CEO |
| ~~T2~~ | ~~Ammo pickups still read as Freedoom items.~~ **Paid 2026-10-13** (commit `720acd1`): §6.4. |  |
| T3 | `Player.DisplayName` is a plain English literal, not a `LANGUAGE` lookup — unverified whether that property resolves `$IDs`. | F5 |
| T4 | Freedoom's `Chainsaw` and `SuperShotgun` classes still exist; only their editor numbers were removed. | F6, if it ever matters |
| T5 | The DPS figures in `BALANCE.md` are computed, not measured against real enemies. The enemies have hit points since F5 and `BALANCE.md` §7 computes shots-to-kill; nothing is measured yet. | F5 playtest of MAP01 v3 |
| ~~T6~~ | ~~`MAP02` uses Freedoom monsters as targets.~~ **Paid 2026-10-13, F5** (commit `2b1aba5`): the 3004 targets spawn `SD_ReichRifleman`, and the bestiary gallery holds one of each class (§4); seen in the engine the same day (ADR 006). The barrels are ours since D82 (`BAR1`/`BEXP`, §5.1). |  |
| T7 | ~~No `CVARINFO` yet; nothing in the arsenal is player-tunable.~~ **Paid on the branch `v3-reload` (2026-10-25, ADR 014):** `CVARINFO` declares `sd_reloads` (§6.15). Open if the CEO drops the experiment. | — |
| T8 | ~~Ammo and backpack pickups are Freedoom sprites: flat, not Soviet crates (§6.3).~~ **Paid for the ammunition 2026-10-14 (D63)**: the eight ammunition classes name our own sprites, `SDCL`, `SDCB`, `SDSL`, `SDSB`, `SDRA`, `SDRB`, `SDFU`, `SDFB` (§6.3, "The pickups, installed by D63"); not yet seen in the engine (D26). Open: the backpack's `BPAK`, which the sweep did not cover, and the status bar icons (`CLIPA0`, `SHELA0`, `ROCKA0`, `CELLA0`), still Freedoom's. | `art-director`, the backpack, when it is asked for; the PM's engine pass for the eight |
| ~~T9~~ | ~~No Cyrillic in the game's font.~~ **Paid 2026-10-13 by D24** (font install `32b384e`, warning removed in `401a02e`): `fonts/defsmallfont/` and `fonts/bigfont/`, 214 glyphs (§2, §6.4). The player-facing warning it carried (`SD_OPTMNU_LANGWARN`, "Cyrillic is not drawn yet") is deleted from `LANGUAGE` and `MENUDEF`. |  |
| T10 | The slot-1 swing is silent (§6.2). ~~The ice axe's pickup is Freedoom's chainsaw~~: **paid 2026-10-14**, `SDAP` A option C (D48, §6.3). | F4, when `sound-designer` delivers `SDAXSWG` |
| ~~T11~~ | ~~`AMMO`/`HEALTH`/`ARMS`/`ARMOR` are pixels in the IWAD's `STBAR` (§6.5).~~ **Paid 2026-10-20 by M2e-i (D89)**: status bar A ships in English and Russian, the Russian labels drawn by `SD_StatusBar.Draw` (§6.5, §6.5.1); not yet seen in the engine (D26). | |
| T12 | **Mostly paid 2026-10-13 by D31 (commits `7ff8c5a`, `22567d9`); the CEO walked it on screen and approved the text menu the same day (D32, commit `f3cc523`).** The main menu's items and the skill screen's header are text in `SDMENU` (§6.6); `M_NGAME`, `M_OPTION`, `M_LOADG`, `M_SAVEG`, `M_RDTHIS`, `M_QUITG`, `M_NEWG` and `M_SKILL` are no longer named by `MENUDEF`. ~~**Still Freedoom's:** the skull cursor `M_SKULL1`/`M_SKULL2`, the pause sign `M_PAUSE`~~: **paid in English 2026-10-14 (D48)**: cursor B (hammer and sickle, blinking through gzdoom.pk3's own `ANIMDEFS`) and pause sign P2 in English ship as `graphics/M_SKULL1`, `M_SKULL2` and `M_PAUSE` (`assets/graphics/shell/`, `docs/art/TEXTURE-INDEX.md` "Shell pictures"); not yet seen in the engine (D26). ~~`M_EPISOD`~~ is never drawn: D41 gave the mod a second episode and the redeclared `EpisodeMenu` draws a text header instead (§4.4, §6.6). Engine-drawn text (load/save captions, message boxes, the options screens) uses fonts, not Freedoom's pictures. ~~**Open: the Russian `M_PAUSE`**~~: **paid in code 2026-10-14 (T24)**: P2's «ПАУЗА» plaque (D48) is installed as `assets/localized/textures/M_PAUSE.ru.png`, packed and validated (§2), and drawn by `SD_StatusBar` (§6.5.1); **not yet seen in the engine** (D26). | the PM's engine pass with `language ru` (T24). Treatment C, painted per-language menu graphics, is parked by the CEO (D31) |
| T13 | `MENUDEF` names `OptionsMenuSimple`, and `AddOptionMenu` on a name the engine does not define is a **hard parse error**. If a GZDoom upgrade drops the simple options menu, the lump stops loading until that block goes. **The same holds for `SD_StatusBar` since T24** (§6.5.1): it derives from `DoomStatusBar` and overrides `DrawPaused` and, since M2e-i, `Draw`; if an engine renames any of them, the ZScript does not compile. `tests/test_pause_sign.py` checks both names against the installed `gzdoom.pk3`. | at the next engine upgrade |
| T14 | Four engine menus (`MainMenu`, `SkillMenu`, `EpisodeMenu` since D41, and the `os_Menu` insertion anchor) are copied into `MENUDEF`; since D31 the first two, and since D41 the third, also differ in their items and layout (§6.6). They do not track engine changes. **Since T24, also `D_Display`'s pause drawing** (`src/d_main.cpp`, g4.14.2, lines 1095-1123): `SD_StatusBar.DrawPaused` copies its position and its multiplayer line (§6.5.1). **Since M2e-i, three facts of `DoomStatusBar.DrawMainBar`** (g4.14.2): where `STBAR` and `STARMS` are drawn and its deathmatch/teamplay condition for `STARMS`, which `SD_StatusBar.Draw` repeats for the Russian labels; `tests/test_pause_sign.py` and `tests/test_hud_install.py` re-read them from the installed `gzdoom.pk3`. | re-diff at every engine upgrade |
| T15 | MAP01's `par = 210` is set, the intermission's PAR row appears, but the printed value was never read in an unattended run (§4.1). | `qa-engineer`, with a human at the keyboard |
| ~~T16~~ | **PAID 2026-10-13**: the ANIMDEFS pairs in `be6525a`, MAP01 v2 retired `SWITCH_PLACEHOLDER` in `bf857a0`. Was: **Paid for the engine, open for the map.** `src/lumps/ANIMDEFS` ships the four `switch` pairs SDSW1x → SDSW2x (2026-10-13), syntax from `gzdoom.pk3 → animdefs.txt`, and `SDSW1A` was seen to flip in engine the same day (§4.3). Open: MAP01 still wears `SDDOOR1` (`SWITCH_PLACEHOLDER`); the click is heard on the CEO's first walk with real switches. | `level-designer`, MAP01 v2 |
| T18 | **Every bestiary sprite and sound is a Freedoom placeholder** (§5.1, §6.2, §6.3); the heavy Panzermensch looks exactly like the normal one. **Partly paid 2026-10-14 (D54):** the Legion trooper's sprites are ours, 70 `SDLT` lumps (§6.3, "The Legion trooper, installed by D54"). **Nearly paid for the sprites, 2026-10-14 (D55):** the Reich rifleman's (70 `SDRR`) and the Reich hound's (46 `SDHN`) are ours too (§6.3, "The Reich rifleman and the Reich hound, installed by D55"), so three of the seven classes, both infantries and the hound, wear their own sprites. **D56, the same day:** the Hybrid Stormtrooper (77 `SDHS`) and his bolt (5 `SDBL`) too (§6.3, "The Hybrid Stormtrooper and his bolt, installed by D56"): four of the seven classes and one of the four projectiles. **Nearly paid for the sprites, D67 (2026-10-14):** the Panzermensch (71 `SDPM`) and the heavy variant, drawn as a set of its own (71 `SDPS`, its own `States` block; the planned `Translation` is dropped) (§6.3, "The Panzermensch and the Schwer, installed by D67"): five of the seven classes and the heavy variant. **D70, the same day:** the Doughboy (54 `SDDB`) (§6.3, "The Doughboy, installed by D70"): six of the seven classes. **Paid for the classes' sprites, D73 (the same day):** the General (81 `SDGN`) and his shell (5 `SDGL`) (§6.3, "The General and his shell, installed by D73"): all seven classes and two of the four projectiles. **D81 (2026-10-20):** the two other projectiles too, the Doughboy's shell (`SDDL`) and the Panzermensch's (`SDPL`) (§6.3, "The two enemy shells, installed by D81"): every enemy sprite is ours. **N9e (2026-10-20, D83, D86, D91, D96):** 43 of the 47 bestiary sounds are ours, eight of them voices (§6.2; `ENEMY-SOUNDS.md` §5.12), and the eight beds are packed, parked. Open: four voices, the rifleman's pain, the trooper's death and the General's pain and death (they keep Freedoom's `DSPOPAIN`, `DSPODTH2`, `DSDMPAIN`, `DSCYBDTH` and wait for a take). | F5, as `art-director` and `sound-designer` deliver (D35: own drawings for the five most-seen) |
| ~~T19~~ | ~~Nothing has been seen in the engine: the eight classes compile only in theory until the PM's batch run (D26).~~ **Paid 2026-10-13** by the PM's engine pass (GZDoom 4.14.2, Freedoom 0.13.0): the classes load with no error, the gallery shows all eight, the drops and the General's single summon were counted, and MAP01 v3's 33 enemies spawn through Doom's numbers. Evidence `docs/qa/evidence/2026-10-13_1705_F5_map02-bestiary.log` and `…-gallery.png` (commit `2b1aba5`), `docs/qa/evidence/2026-10-13_1708_F3_map01-v3-engine-pass.log` (commit `bcbf35f`); the table is in ADR 006. What that pass did **not** settle is debt T22. |  |
| ~~T20~~ | ~~ADR 006 is owed.~~ **Paid 2026-10-13**: `docs/engine/adr/006-bestiary-actors.md` (seven decisions, what the engine showed, what it did not). Written in the working tree; the commit is the PM's (D6). |  |
| T21 | Doom monsters with no Soviet replacement (58 spectre, the rest of Doom II's roster) still spawn Freedoom's actors. **Partly paid by D116 (2026-10-22):** the chaingunner (65) is `SD_LegionGunner` and the Spider Mastermind (7) `SD_LibertyColossus`; MAP01 §8's "Legion heavy gunner" exists now; the P4 maps place the gunner (21110), the colossus (21111, MAP06) and since D123 the Chrome Marshal (21113, MAP08). | `level-designer`, where a map wants a gunner |
| T26 | **The P4 actors wore provisional looks (D116, §6.12)**: existing sprites, tinted and scaled in code (**paid**: the gunner and the colossus by D123, their own `SDLG` and `SDLC`; the Consortium and the AKM by D128, their own `SDCN` and `SDAK`/`SDAF`/`SDAQ`; the Chrome Marshal's tint is a design, not debt). **Still open:** the AKM's magazine `SDAM` (`SDCL` tinted), and existing sounds under their own names (§6.2, "P4 sounds"); status bar A has no row for the AKM's pool (ADR 011). **V3 adds the RGD-5** (ADR 012): its art **paid by D133** (its own `SDRG`, `SDRQ`, `SDRJ`, `SDRN`, `SDRZ`; it wore the ice axe's picture and tinted `SDHB` (borrowed from `SD_HealthBonus`)/`SDRB` from D116); still reused sounds, no bar A row for its pool either. **V3 B5's loudspeaker** (§6.14) wears its own `SDLS` since 2026-10-24 (no longer provisional). None of it is seen in the engine (D26): the design docs' checks E1–E11, A1–A9 and R1–R12 are owed. | the PM's engine pass now; the art and sound swaps as Gemini's frames and `sound-designer`'s takes are approved |
| T17 | **The English `LANGUAGE` section still carries Latin transliterations** (`PG-7V`, `7.62x25`) although the glyphs for the Cyrillic forms D17 asks for exist since D24 (§6.4). Two ASCII tests pin the current state (`tests/test_language.py`, `tests/test_arsenal.py`). | `mod-engineer`, one text change plus an engine screenshot of the HUD |
| T22 | **Bestiary behaviours the engine pass did not show** (ADR 006, "NOT VERIFIED"): infighting between our classes and the native `GetSpecies` rule behind the explicit `Species`; the colour of `BloodColor`; the General's order line on screen (the console log carries it); the recruits entering the chase and the blocked-spot fallback; the attack helpers' damage (both runs were god mode, deaf or `notarget`); how far a dead Doughboy falls; the sounds. | the PM's next engine pass, with enemies awake and one fighting another; `qa-engineer` for the sounds, with a human |
| T23 | **The radio (§6.7) is unseen.** `SD_Radio` has not run in the engine (D26). ~~its editor number 21200 is not yet in `MAPINFO`~~ (`MAPINFO` gives 21200 to `SD_Radio` since; read 2026-10-14). ~~its placeholder `PMAP` A is the computer area map's pickup, which MAP01 also places (2026): a player may walk at the radio expecting a pickup.~~ **The sprite part is paid 2026-10-14 (D63):** `SDRD` A, an Okean-209 on a tabouret (§6.3, "The pickups, installed by D63"); `PMAP` is retired from §5.1. | the PM's engine pass (ADR 008 checklist), which now also sees `SDRD` A draw |
| T25 | **The blue pass (§6, "The blue pass") is unseen and borrowed.** `SD_BluePass` has not run in the engine (D26; checks P1-P6); ~~it wears Freedoom's `BKEY` keycard~~ (**the sprite part is paid 2026-10-14, D63**: `SDKB` A/B, a laminated card blinking as Doom's keys do, §6.3, "The pickups, installed by D63"; the status bar icon `STKEYS0` is the mod's own 7×5 card since D80); and a blue door pressed directly (tag 0) would still print Freedoom's DEHACKED `PD_BLUEC` in English in both languages, because DEHACKED beats `LANGUAGE`. The metro's only blue door works by tag, so nothing shows it today. | the PM's engine pass; a `LOCKDEFS` of ours only if a tag-0 blue door is ever built |
| T24 | **Paid in code 2026-10-14, NOT YET SEEN IN THE ENGINE (D26).** Was: the Russian pause plaque packed but not drawn (§2, "Language variants"): GZDoom g4.14.2 registers `localized/textures/M_PAUSE.ru.png` and checks its size, but its display-time substitution is commented out. Now: `SD_StatusBar : DoomStatusBar`, registered by `GameInfo { StatusBarClass }`, overrides only `DrawPaused` and draws the graphic `LANGUAGE`'s `SD_PAUSE_SIGN` names (`M_PAUSE` / the variant's full path), at `D_Display`'s position, falling back to the engine's own drawing if the name does not resolve (§6.5.1, ADR 010). `assets/localized/textures/M_PAUSE.ru.png` is installed (byte-identical to `work/art/shell_extra/pause_P2_ru.png`), and `tools/release.py` credits `localized/` through the base's licence row. Open: the engine pass, ADR 010's checks E1-E3 (the bar identical, the pause in English, the pause with `language ru`). | the PM's engine pass |
