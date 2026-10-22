# Episode 3 final boss: the Consortium (D112, P4)

Dated design snapshot, 2026-10-22, mod-engineer. Status: **DRAFT, playable
by summon, not in the mod.** Owner of the living numbers once integrated:
`docs/engine/BESTIARY.md` (who it is) and `docs/engine/MOD-SPEC.md` §6
(classes, editor numbers, sprites, sounds).

D112 ends Episode 3, and the first cycle of the story, at Tunguska's main
portal with "the final boss at the portal" (`docs/product/LORE.md`); until
it exists MAP09 places the General as a stand-in
(`docs/levels/MAP09-tunguska.md` §11). This document and the overlay below
are its concept and **behaviour**, on a provisional sprite the mod already
ships, built the way the Episode 2 gunner and colossus were
(`docs/engine/2026-10-22_P4_ep2-enemies.md`).

| | `SD_Consortium` |
|---|---|
| Role | the campaign's final boss (Doom's Icon of Sin and Spider Mastermind): huge, rooted, then slow; two phases |
| Where | MAP09's crater floor before the portal, `MAP09_BOSS_SPOT = (3968, 3136)`, facing the red gate |
| Editor number | **21112** |
| Replaces | nothing (§2.1) |
| Provisional sprite | `SDPS` (the heavy Panzermensch), `Scale 1.75`, tinted the portal's cobalt |
| Final sprite (to draw) | `SDCN` |
| Draft-only twin | `SD_ConsortiumWounded`: the same boss spawned at half health + 100, so the PM can play phase 2 at once; no editor number, deleted at integration |

**Editor number.** 21100–21109 are the bestiary's first nine (BESTIARY
§2.5, MOD-SPEC §6.1), 21110 and 21111 the Episode 2 overlay's gunner and
colossus. **21112** is the next free one in the enemy block;
`tools/make_ep3_boss_overlay.py` refuses any number the mod's `MAPINFO` or
the ep2-enemies overlay's already assigns, so both overlays load together.

## 1. How to play it (the PM; D26)

```sh
python tools/build.py                                   # the mod, unchanged
python tools/make_ep3_boss_overlay.py                   # -> work/overlays/sd-ep3-boss.pk3 (+ .txt)
SD_ALLOW_ENGINE=1 MAP=RANGE tools/run.sh -file work/overlays/sd-ep3-boss.pk3
# console (~):  summon SD_Consortium           (full health, phase 1)
#               summon SD_ConsortiumWounded    (4600 HP: the first hits trigger the Breach)
#               kill monsters                  (its death, its servants falling with it)
# both overlays at once:
SD_ALLOW_ENGINE=1 MAP=RANGE tools/run.sh -file work/overlays/sd-ep2-enemies.pk3 -file work/overlays/sd-ep3-boss.pk3
```

The overlay is a self-contained PK3, loaded after the mod: its own
`zscript.txt` (version 4.12, four `#include`s under `zscript/sd_ep3/`), its
own `MAPINFO` (a `DoomEdNums` block only) and its own `LANGUAGE` (three ids
in `[enu default]`, `[ru]` and `[ca]`). GZDoom compiles every `ZSCRIPT` lump
and merges every `MAPINFO` and `LANGUAGE` lump of every loaded file, so
nothing of the mod is replaced and dropping `-file …` removes it. It needs
nothing from the Episode 2 overlay. Its source lives in
`work/overlays/ep3-boss/` (gitignored `work/`: on the Windows PC only until
integration moves it into `src/`).

Engine checks for the PM (all **NOT VERIFIED**: no agent starts GZDoom):

| # | Do | What must show |
|---|---|---|
| E1 | load with the overlay, read the log | no `Script error`; nothing about `sd_ep3`, `Consortium`, `Translation`, `NOINFIGHTING`, `CHF_` |
| E2 | `summon SD_Consortium` at 600+ units | a big cobalt brute that **does not walk** and turns slowly after you; fans of three balls from its right arm, salvoes of three rockets from its left |
| E3 | stand within ~320 units | a gout of fire from its chest that dies out before 352 units |
| E4 | let it attack four times | the teleport flash behind it (the portal side): a Reich rifleman and a Legion trooper; never more than four alive |
| E5 | stand behind a servant | its rockets and balls pass through the servant; the servants never turn on it or on each other |
| E6 | `summon SD_ConsortiumWounded`, hit it | the Breach: "The Consortium tears itself free of the portal!", the ground shakes ~2 s, shots do nothing for that time, four servants (rifleman, trooper, hound, Doughboy), then it **walks** |
| E7 | fight phase 2 | the volley (rockets and balls together), the barrage (five-ball fans), a jet of fire that sweeps across you; a hound and a trooper every third attack, at most six alive |
| E8 | kill it | its servants die with it; the death frames end on the wreck; `A_BossDeath` (no log line) |
| E9 | MAP09 with `BOSS_KIND` swapped (§7), kill it | the bunker's gate (tag 12) opens: the thing special runs on death; the boss loop starts when it engages (`music_variant.zs`, any `+BOSS` on MAP09) |
| E10 | `language ru`, `language ca`; die to it; reach the Breach | its tag, its obituary and the Breach line in each language |
| E11 | load both overlays (§1) | E1 holds; 21110, 21111 and 21112 each spawn their own class |

## 2. Concept: what holds the portal open

The invaders "fight for profit" and came "to defend capital" (LORE). Two
factions that should hate each other share supply lines, bases and the
final portal. **The Consortium is that partnership given a body**: the
thing at Tunguska that keeps the main portal open, grown out of both
factions into one, and the reason they march together. Kill it and the
alliance has nothing holding it; throw the breaker and the portal folds
(MAP09 §11, `SD_END04_TEXT`).

| Language | Name | Why |
|---|---|---|
| EN | **The Consortium** | two partners pooled for profit; abstract, no real company |
| RU | **Консорциум** | the same word, as the Soviet press used it of Western capital |
| CA | **El Consorci** | the same word |

Alternatives if the CEO prefers: *The Cartel* / «Картель» / «El Càrtel»;
*The Board* / «Правление» / «El Consell».

**Look.** Twice a Panzermensch's height. One trunk, two halves:

- the **Reich half** (its left): grey-green flesh, an SS helmet on its head,
  the red armband on the arm (the approved enemy armband, D105/D114), the
  forearm a rack of rocket tubes;
- the **Legion half** (its right): chrome plate over pink flesh, an M1
  helmet on its head, the US flag on the shoulder, the forearm a chrome
  projector that throws energy balls;
- between them, where the halves are welded, the **portal core**: a ribbed
  chest cavity of the portal's cobalt field (the colour of `SDPORT1`), the
  source of the fire jet;
- **phase 1, rooted:** the lower body is a skirt of black cables and
  conduits running back into the portal's plinth;
- **phase 2, free:** the cables torn out (stumps sparking and dragging),
  two heavy mechanical legs underneath; the core burns brighter.

**Respect (D12).** A video game and a fantastic alternate history. No real
person's face or likeness (no historical leader, no president); the
helmets are generic. The swastika appears only on the armband, as on the
approved enemy set, never as the boss's centrepiece. Nothing about camps,
famines or real victims; the satire is of the alliance of capital, aimed
at the invaders, not at any real group of people.

### 2.1 Why `replaces` nothing

Every bestiary class replaces its Doom counterpart so a map may place
either number (MOD-SPEC §6.1). The Cyberdemon is the General's, the
Spider Mastermind and the chaingunner the ep2 overlay's. Doom's other
final boss, the Icon of Sin, is `BossBrain`: a scripted target behind a
wall, not a monster. Replacing it would put a walking boss where any IWAD
map expects a wall face, and no map of ours places 88. So the class takes
only its own number; `summon SD_Consortium` gives it.

## 3. Stats

| Stat | Value | Why |
|---|---|---|
| Health | **9000** | the Liberty Colossus's 4500 × 2 (D112 brief; the General's 3000 × 3) |
| Phases | rooted 9000–4501, free 4500–0 | the split at half health, once (`SD_CONSORTIUM_BREACH_FRACTION`) |
| Radius / height | 56 / 128 | 112 wide; MAP09's crater is 2048 square under a sky 640 over its floor, terraces 64 deep and 16 high |
| Speed | 0 effective while rooted (`A_Chase` with `CHF_DONTMOVE`), **8** free | slower than the colossus's 10 and the General's 12 |
| Turn while rooted | 8° per chase step (every 6 tics) | slow enough to be flanked; it cannot be got behind for long |
| Mass | 10000 | rooted in the portal; nothing moves it |
| Pain chance | **10** | half the General's 20 |
| Missile chance | `MinMissileChance` 160; `MissileChanceMult` 0.5 rooted, **0.375** free | the General's (the Cyberdemon's), then more aggressive |
| Flags | `+BOSS +NORADIUSDMG +DONTMORPH +BOSSDEATH` (the General's, one for one) and `+NOINFIGHTING` | no splash damage, so the RPG-7 and the Katyusha's blast do not do the work |
| Damage from monsters | **none** (`DamageMobj` override) | its servants' stray shots and any other monster's fire never touch it: the factions are united in it |
| Faction / species | `SD_FACTION_BOTH` / own | both factions in one body (the Stormtrooper is the only other `BOTH`) |
| Scale / tint (provisional) | 1.75, cobalt | `SDPS` is 72 units tall; 72 × 1.75 ≈ 126. Removed with the final art |

**Against the arsenal** (BALANCE §7's ruler, every shot landing, the
impact only for rockets because of `+NORADIUSDMG`):

| | HP | Ice axe | TT-33 | IZh-58 | PPSh-41 | RPG-7 hits | ROKS-3 bursts | Katyusha rockets |
|---|---|---|---|---|---|---|---|---|
| The General (today's stand-in) | 3000 | 200 | 250 | 38 | 375 | 23 | 167 | 27 |
| The Liberty Colossus (draft) | 4500 | 300 | 375 | 57 | 563 | 34 | 250 | 40 |
| **The Consortium**, each phase | 4500 | 300 | 375 | 57 | 563 | 34 | 250 | 40 |
| **The Consortium**, whole | 9000 | 600 | 750 | 113 | 1125 | 67 | 500 | 80 |

Thirteen to fourteen full hand-Katyusha salvoes (675 each), or 67 RPG-7
hits: the longest fight in the campaign, on purpose, and **the first number
to measure** (H). MAP09's ammunition was counted against the General's
3000 (MAP09 §10); level-designer recounts at integration. The servants add
to the bill: 50 HP per rooted pair, 600 for the Breach wave, 180 per free
pair.

## 4. The phases and their attacks

The choice is made each time it attacks (`A_SD_ConsortiumChoose`, a 0-tic
frame at the top of `Missile`), in this order: **the portal** when it is due
and there is room under the cap; else **fire** when the target is within
320; else **orbs or rockets**, even odds.

All three projectiles are the mod's own, subclassed with monster numbers
and an empty obituary (so the boss's line prints), and all three **fly
through monsters** (`CanCollideWith`): its fire never hits its servants, so
it never gives them a reason to fight it.

| Class | Derives from | Sprites (existing) | Changes |
|---|---|---|---|
| `SD_ConsortiumRocket` | `SD_Pg7Grenade` | `SDPG` A (8 rotations) in flight, `SDPX` A–C burst | speed 20, impact `random(1,8) × 10` (avg 45), burst 64 over 96 |
| `SD_ConsortiumOrb` ("energy ball") | `SD_GeneralShell` | `SDGL` A–B in flight, C–E burst (inherited) | speed 16 (fast 20), `random(1,8) × 6` (avg 27; the shell's avg 36) |
| `SD_ConsortiumFlame` | `SD_FlameBlob` | `SDFJ` A–B in flight, `SDFX` A–E (inherited) | 8 flight frames instead of 12: 352 units of reach, `random(1,8) × 4` (avg 18), `Fire` |

### 4.1 Phase 1: rooted (9000–4501)

Plugged into the portal: it breathes (`See`, A/B at 6 tics) and turns 8°
at a time; it never walks.

| Attack | When | What | Tics |
|---|---|---|---|
| **Orbs** | far, 50 % | two fans of three balls from the Legion arm (96 up, 32 to its right), 12° apart; the second fan shifted 6° to fall between the first's | E 12 tell → G 6 → E 10 → G 6 → E 16 = 50 |
| **Rockets** | far, 50 % | three rockets from the Reich arm (96 up, 32 to its left), each aimed | F 12 tell → G 8 / F 6 / G 8 / F 6 / G 8 → F 16 = 64 |
| **Flame** | within 320 | a gout of five blobs from the core (64 up), one every 3 tics, each up to ±5.6° off | E 10 → G 3 × 5 → E 12 = 37 |
| **Summon** | every 4th attack, under 4 alive | the portal behind it lets through **a Reich rifleman and a Legion trooper** | E 15 → F 10 = 25 |

### 4.2 The Breach (once, at half health)

On the first chase step under 4500 HP (checked in the chase, as the
General checks his summon, so an attack is never cut in half):

1. `unbound` set, **invulnerable**; its death roar and a blast heard map-wide;
   the ground shakes for 65 tics across 2048 units; every player reads
   `SD_CONSORTIUM_FREE`.
2. 40 tics in: a wave of **four** through the portal: a rifleman and a
   trooper, a Reich hound and a Doughboy.
3. 65 tics in: the cables tear; invulnerability off, speed 8, the more
   aggressive missile chance. `Goto See`, which now jumps to `Walk`.

H 10 → H 10 → E 20 → F 15 → G 10 = 65 tics (1.9 s).

### 4.3 Phase 2: free (4500–0)

It walks (`Walk`: a footfall per cycle, A–D at 3 tics) and fights harder.

| Attack | When | What | Tics |
|---|---|---|---|
| **Volley** | far, 50 % | rocket, fan of three, rocket, shifted fan of three: both arms at once | F 8 → G 6 × 4 → F 12 = 44 |
| **Barrage** | far, 50 % | three fans of five balls, 8° apart (32° wide), the middle one shifted 4° | E 8 → G 4 / E 6 / G 4 / E 6 / G 4 → E 12 = 44 |
| **Sweep** | within 320 | nine blobs from −16° to +16° in 4° steps, one every 2 tics, without turning: the jet crosses where you stood | E 8 → G 2 × 9 → E 10 = 36 |
| **Summon** | every 3rd attack, under 6 alive | **a Reich hound and a Legion trooper** | 25 |

### 4.4 The reinforcements

Always one of each faction (Reich first), spawned relative to its facing:
144 behind it and 80 to either side (the portal side: on MAP09 the
portal's base ends 192 behind the spot), then straight behind, then 120 to
its right and left, then in front. `A_SpawnItemEx` refuses a monster where
it does not fit, so a blocked spot is skipped and the next tried (the
General's method). Each arrives in a teleport flash, awake, aimed at its
target, with **NOINFIGHTING** set and the boss as its `master`.

| Wave | Who | HP | Cap (alive) |
|---|---|---|---|
| rooted, every 4th attack | `SD_ReichRifleman` + `SD_LegionTrooper` | 50 | 4 |
| the Breach | those two + `SD_ReichHound` + `SD_Doughboy` | 600 | 6 |
| free, every 3rd attack | `SD_ReichHound` + `SD_LegionTrooper` | 180 | 6 |

### 4.5 Death

`SDPS` I 10 (`A_KillChildren`: **its servants die with it**), J 10
(`A_Scream`), K 10, L 10 (`A_NoBlocking`), M N 10, O 30, O −1
(`A_BossDeath`). No `XDeath`, no `Raise`. GZDoom runs the thing's special
in `AActor::Die`, whoever killed it, so MAP09's `Door_Open (12, 16)` on the
boss's thing opens the bunker with no code here, exactly as for the General
today (MAP09 §11; **NOT VERIFIED** in play, check E9). `+BOSSDEATH` and
`A_BossDeath` make the belt-and-braces fix possible as well: a MAPINFO
`SpecialAction = "SD_Consortium", "Door_Open", 12, 16` in MAP09's block.

## 5. Sprites to draw (contract with `art-director` and the PM's Gemini frames)

Doom's convention: a frame letter per pose; rotations 1–8 (1 = facing the
viewer, clockwise) for anything the player walks around, rotation 0 for
death frames. The two halves make it strongly asymmetric, so **eight
separate rotations, no mirrored pairs**. Offsets in a `grAb` chunk,
centred, feet (or the cable skirt) on the floor line (MOD-SPEC §6.3).
Drawn at full size: **~135–145 px tall** (the body is 128 units), at most
**~120 px wide** (112 units of body); `Scale` and `Translation` go when it
lands.

**`SDCN`, the Consortium** (95 lumps):

| Frames | Pose | Rotations | Lumps |
|---|---|---|---|
| Q R | **rooted** idle: the cables run from its back and skirt into the plinth behind; Q the core dim, R the core bright (it breathes) | 1–8 | 16 |
| A B C D | **free** walk: heavy mechanical legs, cable stumps dragging | 1–8 | 32 |
| E | the Legion arm (its right) levelled, the chrome projector glowing: the orb tell, and the core opening for the fire | 1–8 | 8 |
| F | the Reich arm (its left) raised, the rocket rack aimed: the rocket tell | 1–8 | 8 |
| G | firing (`Bright`): muzzle flare at the arm, the core blazing | 1–8 | 8 |
| H | pain: both heads recoil | 1–8 | 8 |
| S | the Breach: cables snapping off its back, the core flaring white | 1–8 | 8 |
| I J K L M N O | death: I the core cracks, J both heads scream, K the halves tear apart at the weld, L it collapses, M N it burns, O the wreck with the two helmets in the ash (stays) | 0 | 7 |

Optional, if the art can tell the fire from the arms' shots: **T**, the
core's jet alone (1–8, 8 more lumps); `Flame` and `Sweep` would show T
instead of G.

**Gemini brief** (the PM's, reference-based as for the seven enemies):
the same painted style as the redrawn bestiary; the Reich half in the
Panzermensch's grey-green flesh and plates, the Legion half in the
colossus's chrome and pink; the core in `SDPORT1`'s cobalt; generic faces
under the helmets (no likeness of any real person); the armband as on the
approved riflemen; a dark background to cut out, the figure whole in frame.
Sheet order: Q1–Q8, R1–R8, A1–D8, E1–H8, S1–S8, then I–O.

Projectiles: none to draw now (all three reuse the RPG-7's, the General's
and the ROKS-3's). A cobalt orb of its own (`SDCB`, rotation 0, A–B flight
and C–E burst) would be a nice to have.

## 6. Sounds (today: existing names; final: to record)

Today every sound is a logical name the mod's `SNDINFO` already defines
(`tests/test_ep3_boss.py` checks it). At integration each gets its own name
and lump (`sound-designer`; lump names checked free against MOD-SPEC §6.2):

| Event | Today | Final logical name → lump |
|---|---|---|
| Sight / active / pain | `sd/mon/panzermensch/sight`, `…/active`, `…/pain` | `sd/mon/consortium/sight` `SDCNSIT`, `…/active` `SDCNACT`, `…/pain` `SDCNPAI`: two voices at once, a German and an American, in one throat |
| Death | `sd/mon/general/death` | `sd/mon/consortium/death` `SDCNDTH`: the two voices torn apart, metal |
| The portal opening (summon) | `sd/mon/general/summon` (the General's "Vorwärts!") | `sd/mon/consortium/call` `SDCNCAL`: the portal's hum swelling, no words |
| The Breach | `sd/mon/panzermensch/death` + `sd/weapon/rpg7/explode` (+ `world/quake`) | `sd/mon/consortium/breach` `SDCNBRC`: cables snapping, a roar |
| Footfall (free) | `sd/mon/panzermensch/step` | `sd/mon/consortium/step` `SDCNSTP` |
| Rockets / orbs | `sd/weapon/rpg7/fire`, `…/explode`; `sd/mon/general/missile`, `…/explode` (inherited) | keep, or `sd/mon/consortium/rocket` `SDCNRKT`, `…/orb` `SDCNORB` |
| Fire | `sd/weapon/roks3/fire` | `sd/mon/consortium/flame` `SDCNFLM` |

## 7. Integration, when the CEO approves the art

One task for mod-engineer (≈ 40k tokens), one for level-designer (MAP09's
boss swap and ammunition recount, ≈ 30k), one for art-director/PM (install
the 95 frames, ≈ 20k), one for sound-designer if the sounds of §6 are made
(≈ 30k).

1. **Art:** the approved PNGs into `assets/sprites/consortium/` (`SDCN`,
   95), with `grAb`, licence rows in `docs/art/LICENSES.md`, reserved in
   MOD-SPEC §6.3.
2. **Code:** `work/overlays/ep3-boss/zscript/sd_ep3/*.zs` →
   `src/zscript/monsters/` (`consortium.zs`, `consortium_rocket.zs`,
   `consortium_orb.zs`, `consortium_flame.zs`), `#include`d from
   `src/lumps/zscript.txt`; `SDPS` → `SDCN`; the rooted `See` shows Q R
   instead of A B, `Breach` shows S in its first two frames; the
   `Translation` and `Scale` lines deleted; **`SD_ConsortiumWounded`
   deleted**.
3. **Lumps:** `21112 = SD_Consortium` into `src/lumps/MAPINFO`'s
   `DoomEdNums`, the three ids × three languages into `src/lumps/LANGUAGE`,
   the sounds of §6 into `SNDINFO` (placeholders kept until recorded), and
   MAP09's fallback `SpecialAction = "SD_Consortium", "Door_Open", 12, 16`.
4. **Contracts first** (MOD-SPEC is the contract): §6 class table, §6.1
   number 21112, §6.2 sounds, §6.3 sprites; a BESTIARY row; BALANCE §7 one
   row (§3 above); `tools/route.py` `MONSTER_EDNUMS` (today
   `range(21100, 21108)`) and `COUNT_CLASSES` gain it, so the route helper
   can place and hurt it.
5. **MAP09** (level-designer; `src/maps/MAP09/map.py`): `BOSS_KIND` →
   `"consortium"`, added to `MONSTER_KINDS` / `MONSTER_CLASSES` (and to
   `CLASS_FILES` in its test); **`MAP09_BOSS_SPOT`, `BOSS_ANGLE = 90` and
   `BOSS_DEATH_SPECIAL` (`Door_Open (12, 16)`) unchanged**. The facing
   matters: the reinforcements come from behind it, which is the portal
   only while it faces away from it. Recount the ammunition for 9000 HP
   plus the servants (§3).
6. **Music:** nothing to do. `src/zscript/sd/music_variant.zs` starts
   MAP09's boss loop (`D_SDBS9A` / `D_SDBS9B`) for any `+BOSS` monster on
   the map that engages, today the General, then the Consortium (D113).
7. **Tests:** `tests/test_ep3_boss.py`'s `ModUntouchedTests` flips (the
   classes are then the mod's) and the overlay tests retire with the
   overlay; a `test_consortium_sprites.py` pins the states, as for every
   installed enemy; MAP09's test pins the new kind.
8. **Engine pass** (the PM): E1–E10 on the built mod without the overlay,
   plus MAP09's `tunguska-critical` route on skills 2, 3 and 4.

## 8. Open, said plainly

- Everything above is **NOT VERIFIED in the engine** (D26): the ZScript was
  written against g4.14.2's API and never compiled. Six things are new to
  this project; their names were read off the engine's own files on this
  PC, their behaviour was not seen: `CHF_DONTMOVE` and
  `CHF_NODIRECTIONTURN` (`gzdoom.pk3` `zscript/constants.zs`), the
  `MissileChanceMult` field changed at run time, the `DamageMobj` and
  `CanCollideWith` virtuals and `A_KillChildren` (`zscript/actors/actor.zs`),
  and the `NOINFIGHTING` flag (its name is in `gzdoom.exe`). E1 is the
  first thing to read.
- The rockets' burst (`A_Explode`) still hurts servants standing next to
  the player; with `NOINFIGHTING` they do not turn on the boss for it.
  Servants' hitscan can still hit each other, with the same result.
- Servants spawned on a terrace step may be refused; the fallback spots
  cover it, but on a crowded step a wave can arrive short (as the
  General's). Their kills count towards the map's total, as his do.
- The tint is the colossus's caveat: a `Translation` on a truecolour PNG
  palettises it first. Cosmetic, provisional, gone at integration.
- Balance numbers marked (H) in the code are first guesses, to be measured
  in the PM's play (T5, MOD-SPEC §10). 9000 HP is the brief's number; if
  the fight drags, the first lever is `SD_CONSORTIUM_HEALTH`, the second the
  caps.
- The overlay source sits in gitignored `work/`: until integration, a copy
  lives only on the Windows PC.
