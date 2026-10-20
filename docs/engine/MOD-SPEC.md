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
hand, installed by N17"). Until now only the draft overlay showed them.
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
| Prefix | `SD` / `SD_` | ZScript classes, LANGUAGE ids, own lumps. **Documented exceptions:** names the engine looks up itself (the shell screens `TITLEPIC`, `INTERPIC`, `M_DOOM`, `M_SKULL1/2`, `M_PAUSE`; the key icons `STKEYS0-2`, D80) and, since D82, the engine actors' sprite overrides `PUFF`, `BLUD`, `TFOG`, `IFOG`, `BAR1`, `BEXP`, `COLU`, shipped under the IWAD's names with exactly Freedoom's lump set (§5.1, §6.3) |
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
├── graphics/TITLEPIC.png   title screen, 320×200 (D18)
├── graphics/INTERPIC.png   intermission background, 320×200 (D18)
├── graphics/M_DOOM.png     main-menu logo, 200×64, placed by MENUDEF (§6.6)
├── graphics/M_PAUSE.png    pause sign, plaque P2 in English, 77×20 (D48)
├── localized/textures/     language variants of graphics, path kept whole:
│                           M_PAUSE.ru.png, plaque P2 in Russian, 77×20 (D48; see the rules)
├── fonts/defsmallfont/     <HEX>.png + font.inf — SmallFont glyphs, 107 files (D24)
├── fonts/bigfont/          <HEX>.png + font.inf — BigFont glyphs, 107 files (D24)
├── fonts/sdmenu/           <HEX>.png + font.inf — menu font SDMENU, 107 files (D31, §6.6)
├── music/D_SDINTL.mid       title music, Engelbach's Internationale (D43, §4.5)
├── music/D_SDM1N2.mid       MAP01's music, ours (D95, §4.5)
├── music/D_SDRAD1.mid       diegetic radio: «Эй, ухнем», Gerloff's CC0 sequence (D43, §6.7)
├── music/D_SDRAD2.mid       diegetic radio: «Колокольчик», Gerloff's CC0 sequence (D43, §6.7)
├── sprites/SD*.png          our sprites (D48): the six weapon pickups SDAPA0, SDTPA0, SDIPA0,
│                           SDPQA0, SDRPA0, SDKPA0 (§6.3); everything else is still the IWAD's (§5.1)
├── sounds/SD*.ogg           our sounds: the 25 weapon sounds of D74 (§6.2), from
│                           assets/sounds/weapons/ (N9)
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
| `MAP03` (`MAP04` until D62) | `SD_MAP03_NAME` = "Tankograd" / «Танкоград» (D63) | `SD_EP01_NAME`, the campaign's third and last map | Owned by `level-designer`; design in `docs/levels/MAP03-factory.md` (v0, the grey box). `cluster = 1`, `next = endtitle`, `music = ""`, `par = 360` (`level-designer`'s figure, design §11): its exit, the breaker that feeds the portal, ends the episode (§4.6). |
| `RANGE` (`MAP02` until D62) | `SD_RANGE_NAME` = "Training Ground" / «Учебный полигон» (D46, 2026-10-14; was "Engineering Test Range" / "Инженерный полигон"; the id was `SD_MAP02_NAME` until D62) | `SD_EP02_NAME` = "Practice Range" / «Полигон» (D41, §4.4) | `cluster = 2`, `next = endtitle`, `nointermission`. F4: 2048×768 hall, ceiling 128, light 192, player start at (160,384) facing +x. The seven weapons, the four ammo pools, barrels and six targets (thing 3004, Soviet riflemen since F5). **F5: the bestiary gallery**, a second room 2048×768 at y 1024–1792, ceiling 192, light 192: one of each of the eight enemy classes in a row at y = 1600, deaf (`ambush`) and facing north, away from the arrival spot. Since D41 the player reaches the map from New Game (§4.4); `MAP=RANGE tools/run.sh` starts it (D62). **Since commit `d1e891f` (2026-10-13), v1 for players:** an `Exit_Normal` switch (`SDSW1D`) in a lit alcove straight behind the start, and the gallery reached on foot through a manual door (tag 1) in the hall's north wall and a bent passage that comes out behind the row; the console's `warp 1024 1152` still lands there. Geometry and reasons are `level-designer`'s, `docs/levels/RANGE-practice-range.md`. Built as an engineering fixture; shipped as the practice range. |

MAPINFO conventions: `clearepisodes` + one episode per campaign (plus the
practice range, §4.4); **the MAPxx slots follow the campaign's order (D62)**
and a map outside the campaign takes a lump name that is not MAPxx (`RANGE`);
map titles by `lookup`, episode title by `name = "$ID"` (**`lookup` is not accepted inside an
episode block**, verified B1); every map and cluster names its music, and
`music = ""` where there is none (verified: silence, no warning; §4.5);
`sky1 = "SKY1"`.

### 4.4 The practice range (D41, 2026-10-13)

> Order note: §4.4, §4.5 and §4.6 come before §4.1 because they were added later;
> the sections are not renumbered, since other documents cite them by number.

The CEO: "Se puede publicar como práctica". The range (MAP02 then, the lump
**`RANGE`** since D62) ships in v1 **outside the campaign**, and the player
reaches it from the New Game screen. The choice
between the ways of reaching it is ADR 007
(`docs/engine/adr/007-practice-range-as-a-second-episode.md`); the contract:

| What | Value |
|---|---|
| Episodes (`MAPINFO`, in this order) | `episode MAP01` name `$SD_EP01_NAME`, key `s`; `episode RANGE` name `$SD_EP02_NAME`, key `p` (`episode MAP02` until D62) |
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
| RANGE, practice range | `music = "D_SDM01T"` (since N9e, D86) | `D_SDM01T`, MAP01's theme `D_SDM01E` cut to its melodic part (bar 49); `D_SDAMUR` (D62) was rejected by D83 and no longer ships |
| Clusters 1 to 4 (end and transition texts, §4.6) | `music = ""` | none |
| A diegetic radio (§6.7) | **none**: `SD_Radio` swaps the music from ZScript while the player is near it | `D_SDRAD1`, `D_SDRAD2` |

Rule: every `music` / `TitleMusic` / `IntermissionMusic` value is `""` or a lump packed under
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
plays `D_SDTITL`, MAP01 `D_SDM1N2` and the range `D_SDM01T` (`currentmusic`, the PM's pass).

### 4.6 The campaign's flow: MAP01 → MAP02 → MAP03 (D60, D62, 2026-10-14)

D60 amended D5: the campaign grew past MAP01. **D62 renumbered the slots to
follow it** ("para no confundir con los nombres"): MAP01 Zarya-7, **MAP02 the
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
| `MAP03` | 1 | `endtitle` | the stats screen, then cluster 1's `SD_END01_TEXT` over `SDFLR1`, then the title screen |
| `RANGE` | 2 | `endtitle` | unchanged (§4.4): no stats (`nointermission`), cluster 2's `SD_END02_TEXT`, the title screen |

| Cluster | `exittext` | Holds | Role |
|---|---|---|---|
| 1 | `lookup, "SD_END01_TEXT"` | MAP03 | the campaign's ending; always the campaign's **last** map |
| 2 | `lookup, "SD_END02_TEXT"` | RANGE | the range's ending |
| 3 | `lookup, "SD_MAP01_EXIT_TEXT"` | MAP01 | MAP01's chapter: the lift down into the metro |
| 4 | `lookup, "SD_MAP02_EXIT_TEXT"` | MAP02 | MAP02's chapter: out of the westbound tunnel at the tractor works |

All four: `flat = "SDFLR1"`, `music = ""`, no `entertext`.

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
- a fourth map (MAP04) would join cluster 1, MAP03 would get cluster 5 with
  `SD_MAP03_EXIT_TEXT` and `next = "MAP04"`, and `SD_END01_TEXT` would be
  rewritten for MAP04;
- the MAPxx slots stay in play order (D62); a map outside the campaign takes
  a non-MAPxx lump name, as `RANGE` does.

**The ending prints once.** Only cluster 1 carries `SD_END01_TEXT` and only
MAP03 is in it, so leaving MAP01 or MAP02 prints its own transition and
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
  go back to the title screen" (`CheckEndSequence`, same file).
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
  two animations, `flat` for the flat and `texture` for the wall, frames 1-4
  in order at 8 tics, every frame installed and packed in its own folder)
  and by `tools/check_pk3.py`, whose `textures` check holds every animation
  frame to the same rule as a map texture (`animdefs_anim_textures`).

#### Masked textures (N6b, D66, 2026-10-14)

A **masked texture** has holes: placed as the middle texture of a
two-sided line, the engine draws its opaque pixels and leaves the rest open,
so the player sees and shoots through the gaps (fences, grates, a hanging
chain). In this mod it is an **RGBA PNG with hard alpha** (every pixel 0 or
255), the only exception to the indexed-PNG rule under `textures/`.

| Lump | Size | Use |
|---|---|---|
| `SDCHAN1` | 64×128 | Tankograd's hanging chain and crane hook (D66); `texturemiddle` of a two-sided line, not tiling vertically |

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
| `SKY1` | sky texture | MAPINFO `sky1` | loads without error |

IWAD elements used implicitly: the HUD and status bar, the four ammo pools
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
now (§6.3, "The TT-33 in hand, installed by N17"). Doom's own `Pistol`
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
| `OptionMenuItemSDLanguageOption` | `OptionMenuItemOption` | The Language row: overrides `GetSelection` only, so any `language` value shows Automatic, English or Russian (QA-G6-1, ADR 004 D-004-7). Writes nothing. |
| `SD_Player` | `DoomPlayer` | The sergeant. Starts with `SD_Tokarev` and 50 `Clip`, nothing else: no ice axe and no `Fist`, so slot 1 is empty until the ice axe is picked up (since 2026-10-13, `BALANCE.md` §4.1). Declares slots 1–7. |
| `SD_IceAxe` | `Fist` *replaces Fist* | Slot 1, melee: the ice axe (D40; was `SD_Shovel`). Found, never issued: MAP01 places it on the dorm's rack (every skill, reachable with every door shut), `RANGE` on the range. |
| `SD_Tokarev` | `Pistol` *replaces Pistol* | Slot 2, `Clip`. |
| `SD_Izh` | `Shotgun` *replaces Shotgun* | Slot 3, `Shell`. Two barrels then a break-open reload (`int barrels`). |
| `SD_Ppsh` | `Chaingun` *replaces Chaingun* | Slot 4, `Clip`. |
| `SD_Rpg7` | `RocketLauncher` *replaces RocketLauncher* | Slot 5, `RocketAmmo`. Fires `SD_Pg7Grenade`. |
| `SD_Roks3` | `PlasmaRifle` *replaces PlasmaRifle* | Slot 6, `Cell`. Fires `SD_FlameBlob`. |
| `SD_HandKatyusha` | `BFG9000` *replaces BFG9000* | Slot 7, `Cell`, 40 per salvo. Fires six `SD_KatyushaRocket`. |
| `SD_Pg7Grenade` | `Rocket` | Shaped-charge projectile. Not placeable. |
| `SD_FlameBlob` | `Actor` | Fire projectile, 528-unit reach. Not placeable. |
| `SD_KatyushaRocket` | `Rocket` | Salvo rocket, does not hurt the shooter. Not placeable. |
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
| `SD_StormBolt`, `SD_DoughboyShell`, `SD_PanzerShell`, `SD_GeneralShell` | `Actor` | The four enemy projectiles. Not placeable. |
| `SD_Radio` | `Actor` | The diegetic radio (D43): a solid decoration that plays one of two CC0 pieces in place of the level's music while the player is near it, and gives the level's music back when the player walks away. Contract §6.7, reasons ADR 008. |
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
| 21100 | `SD_ReichRifleman` (also spawned by Doom's 3004) |
| 21101 | `SD_LegionTrooper` (also 9) |
| 21102 | `SD_Stormtrooper` (also 3001) |
| 21103 | `SD_ReichHound` (also 3002) |
| 21104 | `SD_Doughboy` (also 3005) |
| 21105 | `SD_Panzermensch` (also 69) |
| 21106 | `SD_General` (also 16) |
| 21107 | `SD_PanzermenschSchwer` (also 3003) |
| 21108 | *reserved*: a cloaked hound replacing `Spectre` (58), not implemented (`BESTIARY.md` §6) |
| 21200 | `SD_Radio`, the first decoration (§6.7). **Assigned here, not yet in `MAPINFO`**: the line `21200 = SD_Radio` is the PM's to add (the file was another agent's on 2026-10-13); until it lands, a map that places 21200 spawns nothing there |

Every enemy also `replaces` its Doom counterpart, so a map may place either
number and both spawn ours; `level-designer` can keep MAP01's Doom numbers
or switch to these, the result in the engine is the same. Doom monsters the
bestiary does **not** replace (65 chaingunner, 58 spectre, and the rest of
Doom II's roster, `BESTIARY.md` §12) still spawn Freedoom's actor.

Removed from the game (mapped to `None` in `DoomEdNums`): **82** super
shotgun and **2005** chainsaw. The arsenal is exactly seven weapons (D13).

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
IZh-58's reload and the ROKS-3's jet. Only the IZh-58's pickup is not ours
(D94: NO); it keeps Doom's generic one.

| Logical name | Lump | Played by |
|---|---|---|
| `sd/weapon/iceaxe/swing` | `SDAXSWG` | `SD_IceAxe` Fire, first frame (`SDAX B 5`), `CHAN_WEAPON` |
| `sd/weapon/iceaxe/hit` | `SDAXHIT` | `A_SD_IceAxeSwing` when the blow finds a target |
| `sd/weapon/iceaxe/wall` | `SDAXWAL` | `SD_IceAxePuff`'s `AttackSound` (the puff spawned on a wall, floor or ceiling) |
| `sd/weapon/iceaxe/pickup` | `$random`: `SDAXPKP1`, `SDAXPKP3` (D94) | `Inventory.PickupSound` (since N9e) |
| `sd/weapon/tokarev/fire` | `SDTTFIR` | `SD_Tokarev` `AttackSound` |
| `sd/weapon/tokarev/dry` | `SDTTDRY` | `A_SD_WeaponReady` → `SD_WeaponSounds.DryClick` |
| `sd/weapon/tokarev/reload` | `SDTTRLD` | nothing: parked, no reload state (D47) |
| `sd/weapon/tokarev/pickup` | `$random`: `SDTTPKP1`, `SDTTPKP2` (D94) | `Inventory.PickupSound` (since N9e) |
| `sd/weapon/izh/fire` | `SDIZFIR` (take B, D83; `DSSHOTGN` until N9e) | `SD_Izh` `AttackSound` |
| `sd/weapon/izh/reload` | `SDIZRLD` (D94 alt3; `DSSGCOCK` until N9e) | `SD_Izh` Reload, first frame |
| `sd/weapon/izh/dry` | `SDIZDRY` | `A_SD_WeaponReady` |
| `sd/weapon/ppsh/fire` | `SDPPFIR` | `SD_Ppsh` `AttackSound` |
| `sd/weapon/ppsh/pickup` | `SDPPPKP` | `Inventory.PickupSound` |
| `sd/weapon/ppsh/dry` | `SDPPDRY` | `A_SD_WeaponReady` |
| `sd/weapon/ppsh/reload` | `SDPPRLD` | nothing: parked (D47) |
| `sd/weapon/rpg7/fire` | `SDRPFIR` | `SD_Pg7Grenade` `SeeSound` |
| `sd/weapon/rpg7/explode` | `SDRPEXP` | `SD_Pg7Grenade` `DeathSound` |
| `sd/weapon/rpg7/reload` | `SDRPRLD` | `SD_Rpg7` Fire, `SDRL B 10` (the launch frame split 4 + 10), `CHAN_WEAPON` |
| `sd/weapon/rpg7/pickup` | `SDRPPKP` | `Inventory.PickupSound` |
| `sd/weapon/rpg7/dry` | `SDRPDRY` | `A_SD_WeaponReady` |
| `sd/weapon/roks3/fire` | `$random`: `SDRKFIR1`-`SDRKFIR3` (D94; `DSFLAME` until N9e) | `A_SD_FireRoks3`, `CHAN_WEAPON`, restarted every 3 tics: a take per restart |
| `sd/weapon/roks3/pickup` | `SDRKPKP` | `Inventory.PickupSound` |
| `sd/weapon/roks3/dry` | `SDRKDRY` | `A_SD_WeaponReady` |
| `sd/weapon/roks3/reload` | `SDRKRLD` | nothing: parked (D47) |
| `sd/weapon/katyusha/charge` | `SDHKCHG` | `SD_HandKatyusha` Fire, `SDHK A 20`, `CHAN_WEAPON` |
| `sd/weapon/katyusha/fire` | `SDHKFIR` | `A_SD_FireKatyusha`, `CHAN_WEAPON` |
| `sd/weapon/katyusha/burst` | `SDHKEXP` | `SD_KatyushaRocket` `DeathSound` |
| `sd/weapon/katyusha/reload` | `SDHKRLD` | `SD_HandKatyusha` Fire, a 0-tic frame before `SDHK B 20 A_ReFire`, `CHAN_5` (`SD_KATYUSHA_RELOAD_CHANNEL`) so the salvo is not cut |
| `sd/weapon/katyusha/pickup` | `SDHKPKP` | `Inventory.PickupSound` |
| `sd/weapon/katyusha/dry` | `SDHKDRY` | `A_SD_WeaponReady` |

No `PickupSound` on the IZh-58: its pickup (D94: every alternative NO)
keeps Doom's `misc/w_pkup`. The ice axe and the TT-33 got theirs with N9e
(D94). **No hook changes a tic** (D39): the RPG-7's
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
D91) ours for 37 of them, installed by `tools/audio/master_enemy_sfx.py` in
`assets/sounds/enemies/` (`docs/sound/ENEMY-SOUNDS.md` §5.12, licence rows
in `docs/art/LICENSES.md` § "Enemy sounds"), two of them voices (D91's
Chatterbox takes: the rifleman's sight, the trooper's idle); for the other
ten, voices still waiting for a take (D91), the Freedoom placeholder, with
the final lump in its comment. The final names
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
`A_StartSound` take the alias as they took the single name. Seven groups:
`sd/mon/reichrifleman/attack` (`SDRRIAT1`-`3`), `sd/mon/stormtrooper/pain`
(`SDSTOPA1`-`3`), `sd/mon/stormtrooper/death` (`SDSTODT1`-`3`),
`sd/mon/panzermensch/pain` (`SDPZRPA1`-`3`), the D91 voices
`sd/mon/reichrifleman/sight` (`SDRRISI1`, `SDRRISI3`) and
`sd/mon/legiontrooper/active` (`SDLTRAC1`-`5`), and three of the beds
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
| `reichrifleman` | attack `$random` `SDRRIAT1`-`3` (D86); sight `$random` `SDRRISI1`, `SDRRISI3` (D91 voice); xdeath `SDRRIXDT`; *active `DSPOSACT` → `SDRRIACT`; pain `DSPOPAIN` → `SDRRIPAI`; death `DSPODTH1` → `SDRRIDTH`* |
| `legiontrooper` | attack `SDLTRATK` (D86 alt2); active `$random` `SDLTRAC1`-`5` (D91 voice); xdeath `SDLTRXDT`; *sight `DSPOSIT2` → `SDLTRSIT`; pain `DSPOPAIN` → `SDLTRPAI`; death `DSPODTH2` → `SDLTRDTH`* |
| `stormtrooper` | active `SDSTOACT`; sight `SDSTOSIT`; melee `SDSTOMEL`; missile `SDSTOMIS`; explode `SDSTOEXP`; pain `$random` `SDSTOPA1`-`3` (D86); death `$random` `SDSTODT1`-`3` (D86); xdeath `SDSTOXDT` |
| `reichhound` | active `SDHNDACT`; sight `SDHNDSIT`; attack `SDHNDATK`; pain `SDHNDPAI`; death `SDHNDDTH` |
| `doughboy` | active `SDDGBACT`; sight `SDDGBSIT`; melee `SDDGBMEL`; missile `SDDGBMIS`; explode `SDDGBEXP`; pain `SDDGBPAI`; death `SDDGBDTH` |
| `panzermensch` (and the heavy variant) | active `SDPZRACT`; sight `SDPZRSIT`; melee `SDPZRMEL`; missile `SDPZRMIS`; explode `SDPZREXP`; pain `$random` `SDPZRPA1`-`3` (D86); death `SDPZRDTH`; step `SDPZRSTP` |
| `general` | active `SDGENACT`; missile `SDGENMIS`; explode `SDGENEXP`; *sight `DSCYBSIT` → `SDGENSIT`; summon `DSVILSIT` → `SDGENSUM`; pain `DSDMPAIN` → `SDGENPAI`; death `DSCYBDTH` → `SDGENDTH`* |

Until N9e the rifleman fired `DSPISTOL`, the TT-33's old stand-in, and the
trooper `DSDSHTGN`; both fire ours now. One placeholder left is knowingly
imperfect: the General's order is `DSVILSIT`, a creature's sight sound,
because Freedoom has no voice that gives an order; it goes when D87's
`SDGENSUM` is approved.

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

**The TT-33 in hand, installed by N17 (2026-10-15).** The hands are
Freedoom's own pistol hands (`PISGA0`, `PISGB0`, `PISGC0`), their pistol
cut out and every hand pixel recoloured to our skin and sleeve; the CEO
approved them as R3-A1 ("R3A1 ok!", D61). Our TT-33, rendered from behind
on the 3D rig, sits in their grip; the CEO approved it in hand ("está
bien", D63) once it had been shown in engine through the draft overlay
(`docs/qa/evidence/2026-10-14_1950_F4_tt33-freedoom-hands-in-engine.png`).
Four lumps ship in `assets/sprites/tt33/`, beside the pickup `SDTPA0`,
byte-identical to `work/art/weapons_fd/tt33/` (`tools/art/hand_study.py`,
`build_tt33_fd`; rendered again for the install from commit 33f47e8, the
code of the frames shown in engine, into a scratch folder: all four
identical). Hand E's drafts of the same names in `work/art/weapons/tt33/`
(rejected, D48) do not ship. Each PNG is RGBA with hard alpha (`SDTT` in
palette v2 for `flesh_pink`, `SDTF` in v1) and carries its `grAb`
offsets, which place it exactly where the overlay showed it: the overlay
copied the same bytes under the placeholder names, and neither it nor
`tokarev.zs` moves a weapon sprite in code (no `A_WeaponOffset`, no
`Weapon.YAdjust`).

| Lump | State | Size | `grAb` (left, top) | Above the status bar |
|---|---|---|---|---|
| `SDTTA0` | `Ready`, `Select`, `Deselect`; `Fire`'s first 4 tics | 82 × 104 | −125, −96 | 56 px (Freedoom's `PISGA0`: 55, D57's ±10 % band) |
| `SDTTB0` | `Fire`: the shot (`A_GunFlash`, `A_FireBullets`) and `A_ReFire` | 82 × 116 | −125, −82 | 67 px (the kick up) |
| `SDTTC0` | `Fire`: coming down | 84 × 113 | −124, −87 | 59 px |
| `SDTFA0` | `Flash` (`Bright`, `A_Light1`), over `SDTTB0`'s muzzle | 19 × 20 | −150, −77 | 75 px |

Only the four-letter names changed, `PISG` → `SDTT` and `PISF` → `SDTF`:
frame letters, tics, actions and flow are as they were, held by
`tests/test_tt33_sprites.py` against the state machine as it stood at HEAD
5c05577, before N17 (and by `tests/test_weapon_sprites.py`, which pins it
since D48). `SDTT` D–E, reserved above, are not drawn: no state uses them.
The draft overlay records `PISG` → `SDTT` and `PISF` → `SDTF` as installed
(§6.9). Licence rows, and what Freedoom's BSD licence asks of a release:
`docs/art/LICENSES.md`, "Weapon frames: the TT-33 in hand". **NOT VERIFIED
in the engine from the PK3** (D26): the PM's pass.

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
credits name Google Gemini (`SD_CRED_SRC_4`–`_6`, `tools/release.py`
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

**The Legion trooper, installed by D54 (2026-10-14).** The CEO chose cell C
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

**The Reich rifleman and the Reich hound, installed by D55 (2026-10-14).**
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

**The Hybrid Stormtrooper and his bolt, installed by D56 (2026-10-14).** The
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

**The Panzermensch and the Schwer, installed by D67 (2026-10-14).** The CEO
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

**The Doughboy, installed by D70 (2026-10-14).** The CEO chose cell C of
the heavies sweep, the head in its M1 helmet, severed, with a neck stump
and a dangling spine (D65), asked for a bigger flag on the helmet ("ponle
la bandera más grande en la cabeza", D67: the decal grew from 5 × 4 to
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

**The General and his shell, installed by D73 (2026-10-14).** The CEO
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
recommended option for both ("los que tú recomiendas", D81;
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
option A of every item ("también las recomendadas", D82;
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

### 6.4 Ammunition (contract with `art-director` and `level-designer`)

The mod creates **no new ammo pools**: the four Doom pools are exactly the
four the arsenal needs. What it owns is the nine pickup actors, declared in
`zscript/sd/ammo.zs`, so that the player reads 1977 Soviet nomenclature
instead of "bullets" and "shells" (CEO decision, 2026-10-13).

| Pool | Pickup classes (ours) | Replaces | Used by | Name (`LANGUAGE`) |
|---|---|---|---|---|
| `Clip` | `SD_Clip`, `SD_ClipBox` | `Clip`, `ClipBox` | TT-33, PPSh-41 | `AMMO_CLIP` — 7.62x25 / «Патроны 7,62×25» |
| `Shell` | `SD_Shell`, `SD_ShellBox` | `Shell`, `ShellBox` | IZh-58 | `AMMO_SHELLS` — 12 gauge / «Патроны 12 кал.» |
| `RocketAmmo` | `SD_RocketAmmo`, `SD_RocketBox` | `RocketAmmo`, `RocketBox` | RPG-7 | `AMMO_ROCKETS` — PG-7V / «Выстрелы ПГ-7В» |
| `Cell` | `SD_Cell`, `SD_CellPack` | `Cell`, `CellPack` | ROKS-3, hand Katyusha | `AMMO_CELLS` — fuel / «Горючее» |
| — | `SD_Backpack` | `Backpack` | — | pickup line `SD_GOT_BACKPACK`; the RD-54's sprite since D80 (§6.3) |

Rules that matter to the other roles:

- **Maps keep using the Doom editor numbers** (2007/2048 clip, 2008/2049
  shell, 2010/2046 rocket, 2047/17 cell, 8 backpack). `replaces` does the
  rest; our classes get no editor number of their own.
- Each class subclasses the Doom pickup it replaces. That is what keeps the
  pool Doom's: `GetParentAmmo()` walks up to the first child of `Ammo`.
  **Never** re-parent one of these to `Ammo` directly — it would silently
  create a fifth pool.
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

### 6.5 Status bar — open question for the CEO

The words **AMMO**, **HEALTH**, **ARMS** and **ARMOR** the CEO wants in
Cyrillic are **not text**: they are pixels painted inside the IWAD's `STBAR`
graphic (320×32 in `freedoom2.wad`, verified; the grey weapon digits are a
second lump, `STARMS`, 38×32). No `LANGUAGE` string reaches them. Two ways out, neither
done:

| Way | What it is | Cost | Consequence |
|---|---|---|---|
| **Own `STBAR`** | `art-director` repaints one 320×32 graphic with Cyrillic labels; it would ship as src/graphics/STBAR.png (planned path, **not in the tree yet**) and override the IWAD lump by name (standard lump replacement; **not yet verified in this project**). | ~1 art task, 0 code | Cheapest. The bar keeps Doom's exact layout, and the numbers keep working untouched. Locked to one language — the Russian and English builds would show the same bar. |
| **Own status bar** | A `SBARINFO` lump or a ZScript `BaseStatusBar` subclass draws the whole bar ourselves. | ~1 engineering task + the same art | Full control: localized labels, Soviet layout, our own ammo `Tag`s finally visible. Also our bug surface, and it has to be redrawn for the alt-HUD and widescreen. |

**Recommendation: neither yet.** The Cyrillic font was the prerequisite
for a localized status bar and it is paid (T9, D24, 2026-10-13). Repaint
`STBAR` in F6 when `art-director` is doing HUD art in one pass. A ZScript
status bar is worth it only if we decide the HUD itself should stop looking
like Doom's.

Since T24 (2026-10-14) the mod does have a status bar class, `SD_StatusBar`
(§6.5.1), but it draws **nothing of its own** on the bar: it is Doom's
`DoomStatusBar` with one virtual overridden, for the pause sign. The choice
above is unchanged. If it is ever "Own status bar", that class is where the
work goes, and §6.5.1's rule (override, do not copy) still holds.

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
| What it overrides | **only** `DrawPaused`. No field, no other virtual | `tests/test_pause_sign.py` fails on a second `override` or on a field |
| Registration | `MAPINFO → GameInfo → StatusBarClass = "SD_StatusBar"` | key `statusbarclass` (`src/gamedata/gi.cpp`, case-insensitive). The engine uses the last definition by file order, and our PK3 loads after gzdoom.pk3 and the IWAD. Neither `freedoom2.wad` 0.13.0 (no `MAPINFO`, no `SBARINFO` lump) nor GZDoom's support packages (only `filter/harmony/` sets one) define another; checked 2026-10-14 |
| The graphic's name | `LANGUAGE` id **`SD_PAUSE_SIGN`**: `[enu default]` `"M_PAUSE"`, `[ru]` `"localized/textures/m_pause.ru.png"` | a `LANGUAGE` id follows the language the player chose, `auto` included, which reading the `language` CVar would not. The Russian value is the variant's full path; `TexMan.CheckForTexture` resolves a name with a `/` through the file system. Why not an own lump `M_PAUSER`: ADR 010 |
| Lookup | `TexMan.CheckForTexture(name, TexMan.Type_MiscPatch)` (default flags `TryAny`) | the same call the engine's `GetGameTextureByName` makes (`GetTextureID` adds `TEXMAN_TryAny`) |
| Position | x = (screen width − width × `CleanXfac`) / 2 + left offset × `CleanXfac`; y = 4; `DTA_CleanNoMove`; animated | copied from `D_Display`: centred at the top, scaled by the clean factor, not moved |
| Multiplayer line | when `player >= 0` and `multiplayer`: `TXT_BY` with `%s` → the pausing player's name, `SmallFont` (`NewSmallFont` under `generic_ui`), `CR_RED`, centred at y = sign height × `CleanYfac` + 4 | `D_Display` draws it only when it draws the sign; returning true skips it, so the class draws it too |
| Fallback | if the name does not resolve, `DrawPaused` returns **false** and the engine draws `GameInfo { PauseSign }` (`M_PAUSE`) as before | the worst case is the English sign, never a missing one |

Both pause plaques are 77×20 (§2); `check_pk3` refuses a variant of
another size. **NOT VERIFIED in the engine** (D26): that the bar is
identical, the sign in English, the sign with `language ru`. `DrawPaused`
is verified as code in g4.14.2's `gzdoom.pk3`; whether GZDoom 4.12, the
`version` the mod declares, has it is **NOT VERIFIED** (ADR 010).

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
| Language switch | `OptionString "SD_LanguageValues"` with `auto` / `default` / `ru`, driving GZDoom's own archived `language` CVar | `OptionValue` parses its left column as a NUMBER and **the game will not start**; the mod declares no CVar of its own and no `CVARINFO` |
| Where the switch lives | `AddOptionMenu` on **both** `OptionsMenu` and `OptionsMenuSimple`, `BEFORE "os_Menu"` | `m_simpleoptions` defaults to true, so "Options" opens the SHORT screen; appending at the end puts the row below the fold |
| Main-menu logo | `LISTMENU "MainMenu"` redeclared with `StaticPatch 60, 0, "M_DOOM"` | the engine's own value is `94, 2`, which does not sit on the lockup painted into `TITLEPIC`. **This row is the contract: `M_DOOM` (200×64) goes at x=60, y=0 of the 320×200 screen.** Measured 2026-10-13: overlaying `assets/graphics/shell/M_DOOM.png` on `TITLEPIC.png` at (60,0) gives a mean per-channel difference of 6, against 22 or more at every neighbouring offset. The generator's manifest under gitignored `work/art/shell/` is evidence, not contract — it is not in every clone. Moving the lockup means changing this row, `MENUDEF` and `tests/test_language.py::MainMenuLogoTest` together. Since D31 the skill screen draws the same logo at the same place |
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
` (a row does not wrap). Blocks in order: team, music, engine, game data, sources |
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
| T1 | Every weapon sprite and sound is a Freedoom placeholder (§6.2, §6.3). **Partly paid 2026-10-14 (D48):** the six world pickups are ours (§6.3, "Installed since D48"). **N17 (2026-10-15):** the TT-33's held and flash frames are ours (§6.3, "The TT-33 in hand, installed by N17"). **D79 (2026-10-20):** the PPSh-41's too (§6.3, "The PPSh-41 in hand, installed by D79"). **D84 (2026-10-20):** the IZh-58's, RPG-7's, ROKS-3's and hand Katyusha's held and flash frames, and the Katyusha's pickup (§6.3, "The IZh-58, RPG-7, ROKS-3 and hand Katyusha in hand, installed by D84"); the weapon sounds were paid by N9 (D74). **D88 (2026-10-20):** the ice axe's held frames (§6.3, "The ice axe in hand, installed by D88"): every held, flash and pickup sprite of the arsenal is ours. **D82 (2026-10-20):** the projectiles too, `SDPG`, `SDKR`, `SDPX`, `SDFJ`, `SDFX` (§6.3, "The player effects, installed by D82"): **the sprite part of T1 is paid**; not yet seen in the engine (D26). | F4, once `art-director` redraws the hands and `sound-designer`'s sounds pass the CEO |
| ~~T2~~ | ~~Ammo pickups still read as Freedoom items.~~ **Paid 2026-10-13** (commit `720acd1`): §6.4. |  |
| T3 | `Player.DisplayName` is a plain English literal, not a `LANGUAGE` lookup — unverified whether that property resolves `$IDs`. | F5 |
| T4 | Freedoom's `Chainsaw` and `SuperShotgun` classes still exist; only their editor numbers were removed. | F6, if it ever matters |
| T5 | The DPS figures in `BALANCE.md` are computed, not measured against real enemies. The enemies have hit points since F5 and `BALANCE.md` §7 computes shots-to-kill; nothing is measured yet. | F5 playtest of MAP01 v3 |
| ~~T6~~ | ~~`MAP02` uses Freedoom monsters as targets.~~ **Paid 2026-10-13, F5** (commit `2b1aba5`): the 3004 targets spawn `SD_ReichRifleman`, and the bestiary gallery holds one of each class (§4); seen in the engine the same day (ADR 006). The barrels are ours since D82 (`BAR1`/`BEXP`, §5.1). |  |
| T7 | No `CVARINFO` yet; nothing in the arsenal is player-tunable. | when a gameplay option needs it |
| T8 | ~~Ammo and backpack pickups are Freedoom sprites: flat, not Soviet crates (§6.3).~~ **Paid for the ammunition 2026-10-14 (D63)**: the eight ammunition classes name our own sprites, `SDCL`, `SDCB`, `SDSL`, `SDSB`, `SDRA`, `SDRB`, `SDFU`, `SDFB` (§6.3, "The pickups, installed by D63"); not yet seen in the engine (D26). Open: the backpack's `BPAK`, which the sweep did not cover, and the status bar icons (`CLIPA0`, `SHELA0`, `ROCKA0`, `CELLA0`), still Freedoom's. | `art-director`, the backpack, when it is asked for; the PM's engine pass for the eight |
| ~~T9~~ | ~~No Cyrillic in the game's font.~~ **Paid 2026-10-13 by D24** (font install `32b384e`, warning removed in `401a02e`): `fonts/defsmallfont/` and `fonts/bigfont/`, 214 glyphs (§2, §6.4). The player-facing warning it carried (`SD_OPTMNU_LANGWARN`, "Cyrillic is not drawn yet") is deleted from `LANGUAGE` and `MENUDEF`. |  |
| T10 | The slot-1 swing is silent (§6.2). ~~The ice axe's pickup is Freedoom's chainsaw~~: **paid 2026-10-14**, `SDAP` A option C (D48, §6.3). | F4, when `sound-designer` delivers `SDAXSWG` |
| T11 | `AMMO`/`HEALTH`/`ARMS`/`ARMOR` are pixels in the IWAD's `STBAR` (§6.5). Parked in `docs/ICEBOX.md` until F6. Since T24 the mod has a status bar class, `SD_StatusBar` (§6.5.1), which draws nothing of the bar itself; if the "Own status bar" way is chosen, that class is where it goes. | F6, with the HUD art (was blocked on T9; unblocked since D24) |
| T12 | **Mostly paid 2026-10-13 by D31 (commits `7ff8c5a`, `22567d9`); the CEO walked it on screen and approved the text menu the same day (D32, commit `f3cc523`).** The main menu's items and the skill screen's header are text in `SDMENU` (§6.6); `M_NGAME`, `M_OPTION`, `M_LOADG`, `M_SAVEG`, `M_RDTHIS`, `M_QUITG`, `M_NEWG` and `M_SKILL` are no longer named by `MENUDEF`. ~~**Still Freedoom's:** the skull cursor `M_SKULL1`/`M_SKULL2`, the pause sign `M_PAUSE`~~: **paid in English 2026-10-14 (D48)**: cursor B (hammer and sickle, blinking through gzdoom.pk3's own `ANIMDEFS`) and pause sign P2 in English ship as `graphics/M_SKULL1`, `M_SKULL2` and `M_PAUSE` (`assets/graphics/shell/`, `docs/art/TEXTURE-INDEX.md` "Shell pictures"); not yet seen in the engine (D26). ~~`M_EPISOD`~~ is never drawn: D41 gave the mod a second episode and the redeclared `EpisodeMenu` draws a text header instead (§4.4, §6.6). Engine-drawn text (load/save captions, message boxes, the options screens) uses fonts, not Freedoom's pictures. ~~**Open: the Russian `M_PAUSE`**~~: **paid in code 2026-10-14 (T24)**: P2's «ПАУЗА» plaque (D48) is installed as `assets/localized/textures/M_PAUSE.ru.png`, packed and validated (§2), and drawn by `SD_StatusBar` (§6.5.1); **not yet seen in the engine** (D26). | the PM's engine pass with `language ru` (T24). Treatment C, painted per-language menu graphics, is parked by the CEO (D31) |
| T13 | `MENUDEF` names `OptionsMenuSimple`, and `AddOptionMenu` on a name the engine does not define is a **hard parse error**. If a GZDoom upgrade drops the simple options menu, the lump stops loading until that block goes. **The same holds for `SD_StatusBar` since T24** (§6.5.1): it derives from `DoomStatusBar` and overrides `DrawPaused`; if an engine renames either, the ZScript does not compile. `tests/test_pause_sign.py` checks both names against the installed `gzdoom.pk3`. | at the next engine upgrade |
| T14 | Four engine menus (`MainMenu`, `SkillMenu`, `EpisodeMenu` since D41, and the `os_Menu` insertion anchor) are copied into `MENUDEF`; since D31 the first two, and since D41 the third, also differ in their items and layout (§6.6). They do not track engine changes. **Since T24, also `D_Display`'s pause drawing** (`src/d_main.cpp`, g4.14.2, lines 1095-1123): `SD_StatusBar.DrawPaused` copies its position and its multiplayer line (§6.5.1). | re-diff at every engine upgrade |
| T15 | MAP01's `par = 210` is set, the intermission's PAR row appears, but the printed value was never read in an unattended run (§4.1). | `qa-engineer`, with a human at the keyboard |
| ~~T16~~ | **PAID 2026-10-13**: the ANIMDEFS pairs in `be6525a`, MAP01 v2 retired `SWITCH_PLACEHOLDER` in `bf857a0`. Was: **Paid for the engine, open for the map.** `src/lumps/ANIMDEFS` ships the four `switch` pairs SDSW1x → SDSW2x (2026-10-13), syntax from `gzdoom.pk3 → animdefs.txt`, and `SDSW1A` was seen to flip in engine the same day (§4.3). Open: MAP01 still wears `SDDOOR1` (`SWITCH_PLACEHOLDER`); the click is heard on the CEO's first walk with real switches. | `level-designer`, MAP01 v2 |
| T18 | **Every bestiary sprite and sound is a Freedoom placeholder** (§5.1, §6.2, §6.3); the heavy Panzermensch looks exactly like the normal one. **Partly paid 2026-10-14 (D54):** the Legion trooper's sprites are ours, 70 `SDLT` lumps (§6.3, "The Legion trooper, installed by D54"). **Nearly paid for the sprites, 2026-10-14 (D55):** the Reich rifleman's (70 `SDRR`) and the Reich hound's (46 `SDHN`) are ours too (§6.3, "The Reich rifleman and the Reich hound, installed by D55"), so three of the seven classes, both infantries and the hound, wear their own sprites. **D56, the same day:** the Hybrid Stormtrooper (77 `SDHS`) and his bolt (5 `SDBL`) too (§6.3, "The Hybrid Stormtrooper and his bolt, installed by D56"): four of the seven classes and one of the four projectiles. **Nearly paid for the sprites, D67 (2026-10-14):** the Panzermensch (71 `SDPM`) and the heavy variant, drawn as a set of its own (71 `SDPS`, its own `States` block; the planned `Translation` is dropped) (§6.3, "The Panzermensch and the Schwer, installed by D67"): five of the seven classes and the heavy variant. **D70, the same day:** the Doughboy (54 `SDDB`) (§6.3, "The Doughboy, installed by D70"): six of the seven classes. **Paid for the classes' sprites, D73 (the same day):** the General (81 `SDGN`) and his shell (5 `SDGL`) (§6.3, "The General and his shell, installed by D73"): all seven classes and two of the four projectiles. **D81 (2026-10-20):** the two other projectiles too, the Doughboy's shell (`SDDL`) and the Panzermensch's (`SDPL`) (§6.3, "The two enemy shells, installed by D81"): every enemy sprite is ours. **N9e (2026-10-20, D83, D86, D91):** 37 of the 47 bestiary sounds are ours, two of them voices (§6.2; `ENEMY-SOUNDS.md` §5.12), and the eight beds are packed, parked. Open: ten voices of the rifleman, the trooper and the General (D91: they wait for a shouted reference). | F5, as `art-director` and `sound-designer` deliver (D35: own drawings for the five most-seen) |
| ~~T19~~ | ~~Nothing has been seen in the engine: the eight classes compile only in theory until the PM's batch run (D26).~~ **Paid 2026-10-13** by the PM's engine pass (GZDoom 4.14.2, Freedoom 0.13.0): the classes load with no error, the gallery shows all eight, the drops and the General's single summon were counted, and MAP01 v3's 33 enemies spawn through Doom's numbers. Evidence `docs/qa/evidence/2026-10-13_1705_F5_map02-bestiary.log` and `…-gallery.png` (commit `2b1aba5`), `docs/qa/evidence/2026-10-13_1708_F3_map01-v3-engine-pass.log` (commit `bcbf35f`); the table is in ADR 006. What that pass did **not** settle is debt T22. |  |
| ~~T20~~ | ~~ADR 006 is owed.~~ **Paid 2026-10-13**: `docs/engine/adr/006-bestiary-actors.md` (seven decisions, what the engine showed, what it did not). Written in the working tree; the commit is the PM's (D6). |  |
| T21 | Doom monsters with no Soviet replacement (65 chaingunner, 58 spectre, the rest of Doom II's roster) still spawn Freedoom's actors. MAP01 §8 plans a "Legion heavy gunner" on 65 that the bestiary does not have. | CEO question, if a seventh enemy is wanted |
| T17 | **The English `LANGUAGE` section still carries Latin transliterations** (`PG-7V`, `7.62x25`) although the glyphs for the Cyrillic forms D17 asks for exist since D24 (§6.4). Two ASCII tests pin the current state (`tests/test_language.py`, `tests/test_arsenal.py`). | `mod-engineer`, one text change plus an engine screenshot of the HUD |
| T22 | **Bestiary behaviours the engine pass did not show** (ADR 006, "NOT VERIFIED"): infighting between our classes and the native `GetSpecies` rule behind the explicit `Species`; the colour of `BloodColor`; the General's order line on screen (the console log carries it); the recruits entering the chase and the blocked-spot fallback; the attack helpers' damage (both runs were god mode, deaf or `notarget`); how far a dead Doughboy falls; the sounds. | the PM's next engine pass, with enemies awake and one fighting another; `qa-engineer` for the sounds, with a human |
| T23 | **The radio (§6.7) is unseen.** `SD_Radio` has not run in the engine (D26). ~~its editor number 21200 is not yet in `MAPINFO`~~ (`MAPINFO` gives 21200 to `SD_Radio` since; read 2026-10-14). ~~its placeholder `PMAP` A is the computer area map's pickup, which MAP01 also places (2026): a player may walk at the radio expecting a pickup.~~ **The sprite part is paid 2026-10-14 (D63):** `SDRD` A, an Okean-209 on a tabouret (§6.3, "The pickups, installed by D63"); `PMAP` is retired from §5.1. | the PM's engine pass (ADR 008 checklist), which now also sees `SDRD` A draw |
| T25 | **The blue pass (§6, "The blue pass") is unseen and borrowed.** `SD_BluePass` has not run in the engine (D26; checks P1-P6); ~~it wears Freedoom's `BKEY` keycard~~ (**the sprite part is paid 2026-10-14, D63**: `SDKB` A/B, a laminated card blinking as Doom's keys do, §6.3, "The pickups, installed by D63"; the status bar icon `STKEYS0` is the mod's own 7×5 card since D80); and a blue door pressed directly (tag 0) would still print Freedoom's DEHACKED `PD_BLUEC` in English in both languages, because DEHACKED beats `LANGUAGE`. The metro's only blue door works by tag, so nothing shows it today. | the PM's engine pass; a `LOCKDEFS` of ours only if a tag-0 blue door is ever built |
| T24 | **Paid in code 2026-10-14, NOT YET SEEN IN THE ENGINE (D26).** Was: the Russian pause plaque packed but not drawn (§2, "Language variants"): GZDoom g4.14.2 registers `localized/textures/M_PAUSE.ru.png` and checks its size, but its display-time substitution is commented out. Now: `SD_StatusBar : DoomStatusBar`, registered by `GameInfo { StatusBarClass }`, overrides only `DrawPaused` and draws the graphic `LANGUAGE`'s `SD_PAUSE_SIGN` names (`M_PAUSE` / the variant's full path), at `D_Display`'s position, falling back to the engine's own drawing if the name does not resolve (§6.5.1, ADR 010). `assets/localized/textures/M_PAUSE.ru.png` is installed (byte-identical to `work/art/shell_extra/pause_P2_ru.png`), and `tools/release.py` credits `localized/` through the base's licence row. Open: the engine pass, ADR 010's checks E1-E3 (the bar identical, the pause in English, the pause with `language ru`). | the PM's engine pass |
