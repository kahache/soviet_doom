# M2 audit: every Freedoom asset the player still sees (and hears)

Dated snapshot, immutable. Owner: `qa-engineer`. Backlog task **A1**
(`docs/BACKLOG.md`). Scope: the campaign MAP01 → MAP02 → MAP03 and the
practice range `RANGE`, plus the shell (title, menus, HUD, intermission,
end). Gate under audit: **M2**, "no Freedoom sprite left in first person,
on enemies or on pickups; factory textures approved" (`docs/ROADMAP.md`).

**Method: static analysis only.** GZDoom was not started (D26); no
`SD_ALLOW_ENGINE`. A fresh PK3 was built from the working tree into a
scratch path (`tools/build.py --out <scratch>`; `dist/` untouched) and
compared lump by lump against `iwads/freedoom2.wad` 0.13.0 (1 350 sprite
lumps, 240 flats, 963 wall textures, 950 global lumps). Read: every state
line in `src/zscript/**`, `MAPINFO`, `SNDINFO`, `ANIMDEFS`, `MENUDEF`,
`LANGUAGE`, the four generated TEXTMAPs (things, sidedefs, sectors,
specials), Freedoom's `DEHACKED`, and the engine's own defaults in GZDoom
g4.14.2's `gzdoom.pk3` (`mapinfo/doom2.txt`, `mapinfo/doomcommon.txt`,
`menudef.txt`, `zscript/ui/statusbar/doom_sbar.zs`,
`filter/game-doomchex/sndinfo.txt`). Scripts and intermediate JSON stay in
the agent's scratch directory. Thing counts are **skill 3** unless stated.
Engine pass: **pending, the PM's batch.**

The General (`SDGN` body, `SDGL` shell, replacing `CYBR`/`BAL2`-era
placeholders) is being installed by `mod-engineer` right now (N12c): the
working tree already names `SDGN`/`SDGL` and `assets/sprites/general/`
holds the 86 lumps. He is listed as **in progress** and not counted as a
gap.

---

## 0. Summary

### What blocks M2 (the gate read literally)

| # | Item | Freedoom lumps | Seen | Est. k tok |
|---|---|---|---|---|
| B1 | **TT-33 in first person is NOT installed** | `PISG` A–C, `PISF` A | the starting weapon, on screen from the first tic of MAP01 | **100** (art approved D63, sitting in `work/`) |
| B2 | The other six weapons in first person (ice axe, IZh, PPSh, RPG-7, ROKS-3, Katyusha) | `PUNG`, `SHTG`/`SHTF`, `CHGG`/`CHGF`, `MISG`/`MISF`, `PLSG`/`PLSF`, `BFGG`/`BFGF` | whenever held | 1 500 (already in the backlog as N14; ice axe in progress N4/N14-2) |
| B3 | **The hand Katyusha's world pickup** | `BFUG` A | MAP03 (secret), RANGE | **80** (a draft `SDHPA0` exists in `work/art/weapons/katyusha/pass2/`) |
| B4 | Enemy shells of two installed enemies | `BAL2` A–E (Doughboy), `BAL7` A–E (Panzermensch and Schwer) | every Doughboy/Panzermensch attack; 1+1 per map on skill 3 | **150** (one small sprite batch + install) |
| B5 | Health, armour, map, backpack and two keycards | `STIM`, `MEDI`, `BON1`, `BON2`, `ARM1`, `ARM2`, `PMAP`, `BPAK`, `YKEY`, `RKEY` | **113 placed pickups in the campaign on skill 3** (vs. 0 Freedoom ammo pickups) | **400** (sweep ~250 + install ~150, incl. our own pickup lines EN/RU) |
| | **Total that blocks M2** | | | **~2 230k** (of which ~730k is NOT yet in the backlog) |

### Gate ambiguous: the CEO should rule whether M2 includes these

| # | Item | Lumps | Est. k tok |
|---|---|---|---|
| A1 | The player's own projectiles and blasts (PG-7V, Katyusha rockets, flame jet) | `MISL` A–D, `PLSS` A–B, `PLSE` A–E | 200 |
| A2 | Hit effects and fog: bullet puff, blood drops (recoloured but Freedoom-shaped), teleport fog | `PUFF` A–D, `BLUD` A–C, `TFOG` A–J | 150 |
| A3 | Placed decorations: explosive barrels (and their blast), the floor lamp | `BAR1` A–B, `BEXP` A–E, `COLU` A | 100–150 (or ~50 for `level-designer` to swap them for our props) |
| A4 | RANGE's walls and flats (the gate names only the factory) | `STARTAN2`, `FLOOR4_8`, `CEIL3_5` | 40 |
| | **Total if ruled in** | | **~490–540k** |

### Outside M2 (shell and HUD; M4 polish or a CEO call)

| # | Item | Lumps | Est. k tok |
|---|---|---|---|
| H1 | The status bar: bar, numbers, **the face**, key slots | `STBAR`, `STARMS`, `STF*` (42), `STTNUM*`, `STYSNUM*`, `STGNUM*`, `STTPRCNT`, `STTMINUS`, `STKEYS0-8` | 300–400 (art + install; T11's Cyrillic labels decision rides here) |
| H2 | Fullscreen HUD icons | `MEDIA0`, `ARM1A0`/`ARM2A0`, `CLIPA0`/`SHELA0`/`ROCKA0`/`CELLA0` | 30 (point `Inventory.Icon` at our sprites once B5 exists) |
| H3 | The stats screen's labels and digits (English only) | `WIF`, `WIOSTK`, `WIOSTI`, `WISCRT2`, `WITIME`, `WIPAR`, `WINUM0-9`, `WIPCNT`, `WICOLON`, `WIMINUS`, `WISUCKS` | 40 (text route, NOT VERIFIED) or ~150 (art) |
| H4 | F1 help and the title's attract loop | `HELP`, `CREDIT` | 30–50 |
| H5 | Freedoom's English text through its `DEHACKED`: health/armour/key/map pickup lines, the quit messages | `DEHACKED` [STRINGS] | pickup lines go with B5; quit lines ~30 |
| | **Total** | | **~430–650k** |

### Sounds (second list): 100 % Freedoom

Every sound effect the player hears is a Freedoom `DS*` lump: our 58
`SNDINFO` aliases point at **36 distinct Freedoom lumps**, and the player,
doors, switches, item pickups, menus and stats screen use the engine's
Doom defaults, which resolve to another ~20 Freedoom lumps. The weapon and
enemy drafts wait on the CEO's ears (M3, N9 ~200k); **player, door/switch,
item, menu and intermission sounds have no drafts at all** (~200–250k more).
The stats screen plays Freedoom's `D_DM2INT` (§7.6).

### Proposed order

1. **B1, TT-33 install (100k).** Approved art, a pure install, and the
   weapon the player holds first. Cheapest visible win in the list.
2. **B5 + B3 + H2, the pickups sweep and its install (~480k).** 113
   Freedoom objects on the floor of the campaign; one sweep, one install,
   and the pickup lines in our LANGUAGE end Freedoom's English messages
   ("Armor boosted!", seen in `docs/qa/evidence/2026-10-13_2039_ice-axe-and-episode-menu.png`)
   in the Russian game as well.
3. **B4 (+ A1, A2 if the CEO rules them in), one effects batch (~150–500k).**
   Rotation-0 sprites, the `SDBL`/`SDGL` pattern; cheap per lump.
4. **B2, N14 weapons** keep running in parallel; they are the long pole
   (and the art-director's capacity is the real bottleneck for 2-4).
5. **A4, RANGE retexture (40k)**, any time, `level-designer`, parallel to
   everything above. **A3** with it if ruled in.
6. Then the shell (H1, H3, H4, H5) once the CEO places it (M2 or M4).

### Surprises

1. **The TT-33 is not in hand in the shipped PK3.** `docs/ROADMAP.md` (M2
   row) says "TT-33 in hand (1 of 7 weapons)" and the backlog's done list
   says "the TT-33 in Freedoom-based hands". The CEO approved it (D63), but
   `src/zscript/weapons/tokarev.zs` still draws `PISG`/`PISF`, and
   `assets/` has no `SDTT`/`SDTF`: the approved frames exist only in
   `work/art/weapons_fd/tt33/` and are seen only through the draft overlay
   (`tools/make_draft_overlay.py`, `Swap(... "PISG", "SDTT")`). A player
   of the release sees Freedoom's pistol. **0 of 7 weapons are ours in
   first person.**
2. **The roadmap contradicts itself on pickups.** The MVP table says
   "pickups installed (6 of 7)"; the M2 row says "7 of 7 pickups". The PK3
   agrees with the first: the hand Katyusha still spawns as `BFUG`.
3. **The literal M2 gate is much bigger than the M2 status row suggests.**
   "On pickups" includes health, armour, the area map, the backpack and
   MAP03's two keycards: 113 objects on skill 3, none in any sweep so far.
   Only the ammunition, the weapons (6/7), the blue pass and the radio were
   redrawn.
4. **Installed enemies still throw Freedoom shells.** The Doughboy (installed
   D70) fires `BAL2`, Freedoom's cacodemon ball; the Panzermensch and the
   Schwer (installed D67) fire `BAL7`, Freedoom's hell knight ball. Only the
   Stormtrooper (`SDBL`) and the General (`SDGL`, in progress) have ours.
5. **The campaign is 100 % our textures.** MAP01, MAP02 and MAP03 use zero
   Freedoom wall textures or flats (1 470 visible wall faces and 344
   sectors, all `SD*`). Only RANGE is still on Freedoom's `STARTAN2` look.
6. **The stats screen plays Freedoom's music.** `MAPINFO` overrides the
   title music but not `intermissionmusic`, so `D_DM2INT` plays between
   MAP01→MAP02 and MAP02→MAP03 and after MAP03 (VERIFIED by reading both
   files; not heard in the engine). The cluster texts' `music = ""` may fall
   back to Freedoom's finale music `D_READ_M` (NOT VERIFIED; see §7.6).

---

## 1. First-person weapons (all Freedoom)

Source: the `Ready`/`Fire`/`Reload`/`Flash` states of
`src/zscript/weapons/*.zs`. Every held and flash frame below exists only in
the IWAD; the PK3 has no lump of these prefixes.

| Slot | Weapon | Held frames | Flash | Where the player has it | Severity |
|---|---|---|---|---|---|
| 1 | Ice axe (`SD_IceAxe`) | `PUNG` A–D (Freedoom's fist) | — | from MAP01's dorm rack on; RANGE | **blocks M2** (N4/N14-2 in progress) |
| 2 | TT-33 (`SD_Tokarev`) | `PISG` A–C | `PISF` A | **start item: on screen from tic 1 of every new game** | **blocks M2**; approved art not installed (surprise 1) |
| 3 | IZh-58 (`SD_Izh`) | `SHTG` A–D (D in the break-open reload) | `SHTF` A–B | MAP01, MAP02, MAP03 (one each), RANGE; dropped by every Legion trooper | **blocks M2** |
| 4 | PPSh-41 (`SD_Ppsh`) | `CHGG` A–B | `CHGF` A | MAP01, MAP02, MAP03, RANGE | **blocks M2** |
| 5 | RPG-7 (`SD_Rpg7`) | `MISG` A–B | `MISF` A–D | MAP01, MAP02, MAP03, RANGE | **blocks M2** |
| 6 | ROKS-3 (`SD_Roks3`) | `PLSG` A–B | `PLSF` A | MAP03, RANGE | **blocks M2** |
| 7 | Hand Katyusha (`SD_HandKatyusha`) | `BFGG` A–B | `BFGF` A–B | MAP03 (secret, D68), RANGE | **blocks M2** |

World pickups: six of seven are ours (`SDAP`, `SDTP`, `SDIP`, `SDPQ`,
`SDRP`, `SDKP`, D48). **The Katyusha's is `BFUG` A** (Freedoom's BFG),
placed once in MAP03 and once in RANGE: blocks M2 (B3).

Cost: TT-33 install ~100k (rename `SDTT` A–C / `SDTF` A into
`assets/sprites/tt33/`, four state lines, LICENSES, tests, engine pass;
MOD-SPEC §6.3 already names the lumps). The other six: N14, 250k each,
~1 500k as the backlog states.

## 2. Enemies, their projectiles and effects

All seven enemy bodies draw our sprites (`SDRR`, `SDLT`, `SDHS`, `SDHN`,
`SDDB`, `SDPM`, `SDPS`; `SDGN` in progress), corpses and gibs included.
What still comes from Freedoom:

| Item | Lumps | Actor | Where / how often | Severity | k tok |
|---|---|---|---|---|---|
| Doughboy shell | `BAL2` A–B flight, C–E burst | `SD_DoughboyShell` | every Doughboy ranged attack; Doughboys on skill 3: MAP01 1, MAP02 1, MAP03 1 (skill 4: 1/1/3), RANGE 1 | **blocks M2** ("on enemies") | 150 with B4's other half |
| Panzermensch / Schwer shell | `BAL7` A–B flight (4 rotations), C–E burst | `SD_PanzerShell` | every ranged attack; skill 3: MAP01 1, MAP02 1, MAP03 1 (+2 Schwer on skill 4–5), RANGE 2 | **blocks M2** | (in B4) |
| Stormtrooper bolt | `SDBL` | ours | — | done | — |
| The General and his shell | `SDGN`, `SDGL` | ours | MAP03, RANGE | **in progress (N12c)** | — |
| Bullet puff | `PUFF` A–D | engine `BulletPuff` | **every hitscan shot that hits a wall**: the TT-33, IZh (8 pellets), PPSh, the ice axe, and every Reich rifleman and Legion trooper shot. The most frequent Freedoom sprite in play after the weapons | gate ambiguous (A2) | 150 for A2 |
| Blood drops | `BLUD` A–C (shape), tinted `AD 27 21` by `BloodColor` | engine `Blood` | every hit on any enemy | gate ambiguous; reads as generic dark-red drops | (in A2) |
| Teleport fog | `TFOG` A–J | engine `TeleportFog` | the General's summon (one fog per recruit, `general.zs:163`), MAP03 and RANGE; on skill 5 every respawning monster | gate ambiguous | (in A2) |
| Item fog | `IFOG` | engine | only when items respawn (deathmatch) | invisible in practice | — |
| Crush gibs | `POL5` (engine `Actor` crush state) | engine | only under a crusher; no map has one | invisible in practice | — |
| Player body | `PLAY` | `DoomPlayer` via `SD_Player` | first person never shows it | invisible in practice | — |

Dropped items are clean: the rifleman drops `SD_Clip` (`SDCL`), the Legion
trooper `SD_Izh` (`SDIP`), the General's recruits are riflemen.

## 3. Pickups, keys, powerups, armour, health

Ours since D48/D63: the six weapon pickups, the eight ammunition classes
(`SDCL`, `SDCB`, `SDSL`, `SDSB`, `SDRA`, `SDRB`, `SDFU`, `SDFB`), the blue
pass (`SDKB`) and the radio (`SDRD`). Not touched by any sweep:

| Doom class (ednum) | Freedoom lumps | MAP01 | MAP02 | MAP03 | RANGE | Skill 3 total | Freedoom pickup line (DEHACKED, English in both languages) |
|---|---|---|---|---|---|---|---|
| HealthBonus (2014) | `BON1` A–D | 17 | 10 | 10 | — | 37 | "Health boosted!" |
| ArmorBonus (2015) | `BON2` A–D | 8 | 10 | 8 | — | 26 | "Armor boosted!" |
| Stimpack (2011) | `STIM` A | 6 | 6 | 8 | — | 20 | "Took a health refill." |
| Medikit (2012) | `MEDI` A | 5 | 6 | 8 | 2 | 19 (+2) | "Took a large health refill." |
| GreenArmor (2018) | `ARM1` A–B | 1 | 1 | 2 | — | 4 | "Put on a force field vest." |
| BlueArmor (2019) | `ARM2` A–B | — | 1 | 1 | 1 | 2 (+1) | "Put on the attuned force field armor!" |
| Allmap (2026) | `PMAP` A–D | 1 | — | — | — | 1 | "Area survey map." |
| Backpack (8), `SD_Backpack` keeps the sprite | `BPAK` A | 1 | 1 | — | 1 | 2 (+1) | ours (`SD_GOT_BACKPACK`) |
| YellowCard (6) | `YKEY` A–B; bar icon `STKEYS1` | — | — | 1 | — | 1 | "Yellow passcard secured!" |
| RedCard (13) | `RKEY` A–B; bar icon `STKEYS2` | — | — | 1 | — | 1 | "Red passcard secured!" |
| BlueCard (5) → `SD_BluePass` | sprite ours; bar icon `STKEYS0` | — | 1 | — | — | — | ours |
| **Freedoom pickups, skill 3** | | **39** | **35** | **39** | (4) | **113** | |

Severity: **all block M2** (the gate says "on pickups"). The two keycards
are on MAP03's critical path, so every player meets them. Both keycards'
locks print engine text, not Freedoom's: the doors are tagged
(`Door_LockedRaise` tags 4 and 5, locks 3 and 1), so the remote messages
`PD_YELLOWCO`/`PD_REDCO` come from GZDoom's own `language.csv`, which
Freedoom's DEHACKED does not touch.

Fix pattern (MOD-SPEC §6.4, as for the ammo): a thin `SD_X : X replaces X`
per class with its own `Spawn` sprite, `Inventory.PickupMessage "$SD_GOT_*"`
in EN and RU (D21), and `Inventory.Icon` where the fullscreen HUD draws it
(H2). Cost ~400k (sweep 250 + install 150).

## 4. Decorations placed in our maps

| Thing (ednum) | Lumps | Placed | Seen | Severity | k tok |
|---|---|---|---|---|---|
| ExplosiveBarrel (2035) | `BAR1` A–B; blast `BEXP` A–E (+ sound `DSBAREXP`) | MAP01 10, RANGE 6 | MAP01's route and the range's hall; every barrel shot | gate ambiguous (A3); a green Freedoom drum in a Soviet base | 100–150 (sprite) or ~50 (replace by our crates) |
| Column (2028), Freedoom's floor lamp | `COLU` A | MAP01 3 | MAP01 | gate ambiguous (A3) | (in A3) |

No other Doom decoration is placed (no corpses, torches, trees). The lamps,
crates and lockers elsewhere are sectors with our textures.

## 5. Wall and flat textures per map

Counted from the generated TEXTMAPs. "Visible faces" counts a sidedef part
only where geometry shows it (one-sided middles, upper parts where the
facing ceiling is higher, lower parts where the facing floor is lower,
two-sided middles).

| Map | Sectors | Visible wall faces | Freedoom walls | Freedoom flats | Verdict |
|---|---|---|---|---|---|
| MAP01 Zarya-7 | 165 | 654 | **0** | **0** | ours (13 wall textures, 6 flats) |
| MAP02 metro | 87 | 432 | **0** | **0** | ours (15 wall, 11 flats) |
| MAP03 Tankograd | 92 | 384 | **0** | **0** | ours (23 wall, 10 flats incl. the animated `SDMOLT1`, `SDPORT1`) |
| RANGE | 5 | 25 | **`STARTAN2`: 18 faces (25 set)** | **`FLOOR4_8`: 5 floors; `CEIL3_5`: 4 ceilings** | Freedoom (A4) |

M2's texture clause ("factory textures approved") is met: Tankograd uses
21 of 21 approved lumps and nothing else. Every map names `sky1 = "SKY1"`
(Freedoom's), but no sector shows the sky (`F_SKY1` is not used):
invisible in practice. Switches animate through our own `ANIMDEFS` pairs.

RANGE fix: three constants in `src/maps/RANGE/map.py` (`WALL_TEXTURE`,
`FLOOR_FLAT`, `CEILING_FLAT`), e.g. `SDCONC1` / `SDFLR2` / `SDCEIL2`;
~40k with the route re-run and an engine look.

## 6. HUD and shell

| Element | Lumps | Ours or Freedoom | Seen | Severity | k tok |
|---|---|---|---|---|---|
| Title screen | `TITLEPIC` | ours (D18) | — | done | — |
| Main menu, skill, episode screens | `M_DOOM`; text items in `SDMENU`/`SmallFont` | ours (D31, D41); `M_NGAME`…`M_EPISOD` never drawn | — | done | — |
| Skull cursor | `M_SKULL1`/`M_SKULL2` | ours (D48) | — | done | — |
| Pause sign | `M_PAUSE`, `M_PAUSE.ru` | ours (D48, T24) | — | done | — |
| Load/save/options titles | text (engine `StaticTextCentered`) | ours (fonts) | — | done | — |
| Fonts | `fonts/bigfont`, `fonts/defsmallfont`, `fonts/sdmenu` | ours; the stats screen's map name is drawn in our BigFont (`docs/qa/evidence/2026-10-13_0929_F2_intermission-zarya7.png`). Whether our Latin glyphs or Freedoom's `STCFN` win in every SmallFont string is NOT VERIFIED here | — | — | — |
| Intermission background | `INTERPIC` | ours (D18) | — | done | — |
| **Status bar** | `STBAR`, `STARMS`, `STTNUM0-9`, `STTMINUS`, `STTPRCNT`, `STYSNUM0-9`, `STGNUM0-9`, `STKEYS0-8` | **Freedoom** | permanently, at the default screen size | outside the gate; the most-seen Freedoom art after the weapons | H1: 300–400 |
| **The face (mugshot)** | `STF*`: 42 lumps (`STFST*`, `STFTL*`, `STFTR*`, `STFOUCH*`, `STFEVL*`, `STFKILL*`, `STFGOD0`, `STFDEAD0`) | **Freedoom's protagonist**, not Sergeant Vilanova | permanently, centre of the bar | outside the gate; product-visible | (in H1) |
| Fullscreen HUD (screen size 11) | `MEDIA0`, armour `ARM1A0`/`ARM2A0` (GameInfo `armoricons`), ammo icons `CLIPA0`/`SHELA0`/`ROCKA0`/`CELLA0` (inherited `Inventory.Icon`), key `STKEYS*` | Freedoom | only if the player enlarges the view | cosmetic | H2: 30 |
| Stats screen labels and digits (English) | `WIF`, `WIOSTK`, `WIOSTI`, `WISCRT2`, `WITIME`, `WIPAR`, `WINUM0-9`, `WIPCNT`, `WICOLON`, `WIMINUS`, `WISUCKS` | **Freedoom**, seen in the 0929 screenshot ("FINISHED", "KILLS", the red digits) | after MAP01 and MAP02, and after MAP03 before the ending (RANGE has `nointermission`) | outside the gate | H3: 40 / 150 |
| Stats screen map names | `CWILV*` | not used: our `map` blocks have no `titlepatch`, the name is text (0929 screenshot) | — | done | — |
| Stats screen in Russian | engine text in our BigFont (NOT VERIFIED: GZDoom swaps IWAD word-patches for text in non-English languages, `cl_gfxlocalization`) | — | — | — | — |
| F1 help, title attract loop | `HELP`, `CREDIT` (GameInfo `infopage = "HELP", "CREDIT"`, `creditpage = "CREDIT"` in `mapinfo/doom2.txt`, not overridden) | **Freedoom's** help and credits screens | F1 in game; idling on the title (titletime 11 s, then pages). The attract loop's exact order with Freedoom's vanilla `DEMO1-4` is NOT VERIFIED | cosmetic | H4: 30–50 |
| Ending | cluster 1 text over `SDFLR1`, then `endtitle` | ours (no cast call, no `BOSSBACK`) | — | done | — |
| Automap | vector lines; mark digits `AMMNUM0-9` | Freedoom digits only when the player sets marks | rarely | invisible in practice | — |
| Small-screen border | `GRNROCK` flat, `BRDR_*` | Freedoom | only at screen sizes below the status bar | invisible in practice | — |
| Window / startup title | IWAD's "Freedoom: Phase 2" | Freedoom | the window title bar | cosmetic; a `GAMEINFO` `STARTUPTITLE` may cover it (NOT VERIFIED) | ~20 |
| `ENDOOM` | `ENDOOM` | Freedoom | only with `showendoom` on (off by default) | invisible in practice | — |

**Freedoom text the player reads** (DEHACKED beats our LANGUAGE, ADR 003,
verified 2026-10-13; seen: "Armor boosted!" in
`docs/qa/evidence/2026-10-13_2039_ice-axe-and-episode-menu.png`): the
pickup lines of §3's classes (fixed by B5), **the 15 quit messages**
(`QUITMSG`…`QUITMSG14`, English in the Russian game; GameInfo
`quitmessages` can list ids of ours, ~30k), the automap toggles
(`AMSTR_*`) and the cheat lines (`STSTR_*`, cheats only).

## 7. Sounds (second list)

Everything below is a Freedoom lump. Freedoom's `DS*` sounds are BSD like
its art, so this is about identity, not licence.

### 7.1 Weapons (our aliases, `SNDINFO`)

| Event | Freedoom lump | Draft waiting (WEAPON-SOUNDS.md) |
|---|---|---|
| Ice axe hit | `DSPUNCH` | `SDAXHIT` |
| TT-33 fire, PPSh fire | `DSPISTOL` (both) | `SDTTFIR`, `SDPPFIR` |
| IZh fire / reload | `DSSHOTGN` / `DSSGCOCK` | `SDIZFIR`, `SDIZRLD` |
| RPG-7 fire / burst | `DSRLAUNC` / `DSBAREXP` | `SDRPFIR`, `SDRPEXP` |
| ROKS-3 jet | `DSFLAME` | `SDRKFIR` |
| Katyusha charge / salvo / burst | `DSBFG` / `DSRLAUNC` / `DSBAREXP` | `SDHKCHG`, `SDHKFIR`, `SDHKEXP` |
| Weapon pickup | engine `misc/w_pkup` → `DSWPNUP` | `*PKP` (7) |

### 7.2 Enemies (our aliases)

47 aliases for the eight enemy classes (7 of them the General's): `DSPOSACT`,
`DSPOSIT1`, `DSPOSIT2`, `DSPISTOL`, `DSPOPAIN`, `DSPODTH1`, `DSPODTH2`,
`DSSLOP`, `DSDSHTGN`, `DSBGACT`, `DSBGSIT1`, `DSBGDTH1`, `DSCLAW`,
`DSFIRSHT`, `DSFIRXPL`, `DSDMACT`, `DSDMPAIN`, `DSSGTSIT`, `DSSGTATK`,
`DSSGTDTH`, `DSCACSIT`, `DSCACDTH`, `DSKNTSIT`, `DSKNTDTH`, `DSSKEPCH`,
`DSMETAL`, `DSCYBSIT`, `DSCYBDTH`, `DSVILSIT`, `DSRLAUNC`. Every
sight, attack, pain, death and gib of every enemy. Drafts in
`docs/sound/ENEMY-SOUNDS.md`; voices wait on the CEO's takes (D36). The
General's are in this list (his sprites are in progress, his sounds are
not part of N12c).

### 7.3 Player (engine defaults for `DoomPlayer`, inherited by `SD_Player`)

`DSPLPAIN` (every hit taken, including MAP03's molten channel), `DSPLDETH`,
`DSPDIEHI`, `DSSLOP` (gibbed), `DSOOF` (landing, and `menu/invalid`),
`DSNOWAY` (pressing a wall that does nothing: frequent while hunting
switches), `DSJUMP` (only if jumping is allowed). **No draft exists.**

### 7.4 World: doors, switches, barrels, teleport

`DSDOROPN` / `DSDORCLS` (every door: all 18 door lines of MAP01 run at
speed 16, the slow `doors/dr1_*` pair), `DSSWTCHN` (every switch),
`DSSWTCHX` (every exit switch), `DSBAREXP` (barrels), `DSTELEPT` (the
General's summon fog; NOT VERIFIED that `TeleportFog` itself plays it).
The secret chime `DSSECRET` is the engine's own, not Freedoom's.
**No draft exists.**

### 7.5 Items and menus

`DSITEMUP` (every ammo, health, armour and key pickup: the most frequent
sound in the game after gunfire), `DSGETPOW` (the area map), `DSWPNUP`.
Menus: `DSSWTCHN` (open, back, prompt), `DSPSTOP` (cursor), `DSSTNMOV`
(change value), `DSOOF` (invalid), `DSSWTCHX` (dismiss, close),
`DSPISTOL` (choose); the quit sound is a random Freedoom monster/player
sound. **No draft exists.**

### 7.6 Intermission and music

Stats screen: `DSPISTOL` (counter tick), `DSSHOTGN` (each stat done),
`DSBAREXP` (next stage). Music: **`D_DM2INT`, Freedoom's intermission
piece** (GameInfo `intermissionmusic = "$MUSIC_DM2INT"` in
`mapinfo/doomcommon.txt`; our `GameInfo` sets only `TitleMusic`, and no
`map` block sets `intermusic`). Fix ~20k (`intermusic` per map or one
GameInfo line), M3. The cluster texts (`music = ""`): the MAPINFO comment
says they are read in silence; GZDoom may instead fall back to GameInfo's
`finalemusic` (`D_READ_M`, Freedoom). **NOT VERIFIED**: the PM's engine pass
should run `currentmusic` on a cluster text. Every map's own music, the
title's and the radio's are ours.

**Sound cost:** N9 (weapon + enemy drafts install) ~200k as in the backlog;
a player/world/item/menu sweep that does not exist yet ~200–250k.

---

## 8. Invisible in practice (listed so nobody re-audits them)

`PLAY` (the player's body), `IFOG` (item respawn), `POL5` (crush gibs, no
crushers), `SKY1` (no sky ceilings), `ENDOOM`, `GRNROCK`/`BRDR_*`
(small-screen border), `AMMNUM*` (automap marks), the engine's `+ROCKETTRAIL`
on our two rocket classes (particles by default, engine graphics, not
Freedoom), decals (`gzdoom.pk3`, not Freedoom).

## 9. For the PM's engine pass (things only the engine can settle)

1. Does the title idle into Freedoom's `CREDIT` page, and when?
2. `currentmusic` on the MAP01→MAP02 stats screen (expect `D_DM2INT`) and
   on a cluster text (silence or `D_READ_M`?).
3. With `language ru`, is the stats screen text in our BigFont?
4. Does an English SmallFont string use our glyphs or Freedoom's `STCFN`?
5. Does the General's summon play `DSTELEPT`?
