# BALANCE — the arsenal in numbers

Owner: `mod-engineer`. **D119 (2026-10-23), after the CEO's playtest of
Episodes 2 and 3:** the ROKS-3 cut to 157.5 damage/s (§3, slot 6), a
trooper's dropped IZh carries 2 shells (§3, slot 3), the Liberty Colossus
and the Consortium at classic Doom's hit points (§7) and **the maps'
ammunition rules (§8)**, which the level designers apply. **V3 (2026-10-23,
ADR 012): the RGD-5 hand grenade, slot 8** (§2, §3, §4, §8.1), built and
not yet seen in the engine.
Status before D119: **F4, first pass, verified in GZDoom 4.14.2**
(every weapon fires, consumes ammo and kills in `MAP02`, the practice range,
the lump `RANGE` since D62; see §6).
Since D40 (2026-10-13) slot 1 is the **ice axe** (`SD_IceAxe`), which
took over the sapper's shovel's numbers unchanged; text below that
describes what was measured before that date keeps the shovel's name.
Russian mirror: `docs/ru/engine/BALANCE.md`.

This document owns the *why* of every gameplay number in `src/zscript/weapons/`.
Each number also exists in the code as a named constant with the same
reasoning in one line; if the two ever disagree, **the code is the truth and
this file is the bug**.

Nothing here is a CEO decision yet. It is an engineering first pass whose
only hard rule is: *do not break Doom's rhythm*. Every value is anchored to
the Doom II weapon it replaces, read from GZDoom's own source
(`wadsrc/static/zscript/actors/doom/weapon*.zs`, version 4.14.2).

## 0. How to read the numbers

- **tic** = 1/35 second. A weapon's cadence is the number of tics its Fire
  state takes while the trigger is held.
- Doom hitscan damage is `base x random(1,3)`; the averages below use 2.
- Doom projectile damage is `Damage x random(1,8)`; the averages use 4.5.
- **DPS** = average damage per shot x shots per second, every shot hitting
  one target. It is a ruler, not a promise: spread, travel time and blast
  radius change what actually lands.

## 1. The Doom II ruler

| Doom weapon | avg damage per shot | cycle (tics) | shots/s | DPS |
|---|---|---|---|---|
| Fist | 11 (2–20) | 22 | 1.59 | 17.5 |
| Pistol | 10 (5–15) | 19 | 1.84 | 18.4 |
| Shotgun | 70 (7 pellets) | 44 | 0.80 | 55.7 |
| Super shotgun | 200 (20 pellets) | 62 | 0.56 | 112.9 |
| Chaingun | 10 | 4 | 8.75 | 87.5 |
| Rocket launcher | 90 direct + 128 blast / 128 u | 20 | 1.75 | 157.5 |
| Plasma rifle | 22.5 | 3 | 11.67 | 262.5 |
| BFG 9000 | 450 ball + 40-ray spray | 60 | 0.58 | — |

The shape that matters: each slot is roughly **1.5x to 3x** the one before,
slot 3 is the first real weapon, slot 4 is the workhorse, slot 6 is the
sustained killer and slot 7 is the panic button.

## 2. The Soviet arsenal

| Slot | Weapon | Ammo / shot | avg damage per shot | cycle (tics) | shots/s | DPS | useful range (map units) |
|---|---|---|---|---|---|---|---|
| 1 | Ice axe (D40; the sapper's shovel's numbers) | — | 15 (6–24) | 27 | 1.30 | 19.4 | 84 (melee) |
| 2 | TT-33 Tokarev | 1 Clip | 12 (6–18) | 16 | 2.19 | 26.3 | ~1024 |
| 3 | IZh-58 double barrel | 1 Shell | 80 (8 pellets) | 23, +30 every 2 shots | 0.92 sustained | 73.7 sustained / 121.8 burst | ~512 |
| 4 | PPSh-41 | 1 Clip | 8 (4–12) | 3 | 11.67 | 93.3 | ~768 |
| 4b | AKM (D112, in the mod since D116) | 1 `SD_AkmAmmo` | 12 (6–18) | 4 | 8.75 | 105.0 | ~1024 (short bursts) |
| 5 | RPG-7 | 1 RocketAmmo | 135 direct + 100 blast / 104 u | 26 | 1.35 | 181.7 direct | unlimited |
| 6 | ROKS-3 flamethrower | 1 Cell | 13.5 (3–24) | 3 | 11.67 | 157.5 | **528 hard limit** |
| 7 | Hand Katyusha | 40 Cell | 6 x (112.5 direct + 70 blast / 96 u) | 60 | 0.58 | ~394 if all six land | unlimited, fan ±12.5° |
| 8 | RGD-5 hand grenade (V3, ADR 012) | 1 `SD_Rgd5Ammo` | no impact; 100 blast / 128 u on each target, 1.71 s after the throw | 33 | 1.06 | — (an area weapon; ≤ 100 on one target, 43 % of a PG-7V) | ~310 thrown level, ~600 aimed up; bounces |

The ladder (19 → 26 → 74 → 93 / 105 → 182 → 157.5 → 394) keeps Doom's
shape where it matters: slot 3 is the first real weapon, slot 4 the
workhorse, slot 7 the panic button. Since D119 slot 6 no longer beats slot
5 on paper: the ROKS-3 is the best **sustained** weapon (1.5 times the AKM,
no reload, no self-damage, a near-certain hit inside 528 units) and the
RPG-7 the best **burst** (181.7 direct plus the blast, at any range, at the
risk of the sergeant's own life). Each wins somewhere and neither wins
everywhere, which is what the CEO asked for (§3, slot 6). The
AKM (slot 4's second weapon since D116) slots in at **105**, above the
PPSh-41 and well under the RPG-7, as Doom II's super shotgun is slot 3's
better gun; it pays with a scarcer pool of its own (§4). The RGD-5 (slot 8,
V3) is off the ladder: no DPS to speak of, a tool for groups and for what
the RPG-7 cannot see (§3, slot 8).

## 3. Why each number

### Slot 1 — ice axe (`SD_IceAxe`, replaces Fist)

`random(3,12) << 1` = 6–24, avg 15, over a 27-tic swing.
These are the sapper's shovel's numbers, kept as they were when the CEO
made slot 1 an ice axe (D40, 2026-10-13); constants `SD_ICEAXE_*` in
`src/zscript/weapons/ice_axe.zs`, pinned by `tests/test_arsenal.py`.
A steel pick on a shaft is not a fist: **+36% damage** for **+23% swing
time**, which nets +11% DPS. It stays a last resort (it is still under one
twentieth of slot 4) but it no longer feels like punching a wall.
Kickback 120 against the Fist's 100: a swung pick shoves. Berserk keeps
Doom's x10, so the berserk pack is still the thing that turns melee into a
weapon. Whether an ice axe should hit harder than a shovel (a pick
concentrates the blow) is a fair question the CEO did not ask: D40 kept the
numbers, and the MAP01 playtest is where it would show.

The ice axe is **found, not issued** (since 2026-10-13, §4.1): it is not in
the starting inventory, and the first one lies on the rack of MAP01's dorm.

### Slot 2 — TT-33 Tokarev (replaces Pistol)

`6 x random(1,3)` = 6–18, avg 12, every 16 tics, 4.5° spread.
The TT-33 fires a high-velocity bottlenecked 7.62x25 round; it should hit
harder and group tighter than Doom's generic pistol (5 base, 5.625°). The
cycle drops from 19 to 16 tics because a single-action pistol has no
mechanism to wait for.

Result: **26.3 DPS against Doom's 18.4, +43%.** This is the single most
aggressive number in the table and the first one to cut if the opening
minutes of MAP01 feel soft. It is deliberate: the sergeant starts with this
gun and nothing else at all (not even a melee weapon, §4.1), and Doom's pistol is famously the weapon
players stop using the moment they find anything.

Ammo: `Clip`, unchanged. The TT-33 and the PPSh-41 historically fire the
**same 7.62x25 Tokarev cartridge**, so one pool is both the Doom-correct and
the historically correct answer.

### Slot 3 — IZh-58 double barrel (replaces Shotgun)

8 pellets of `5 x random(1,3)` = avg 80 per barrel; 8.0° horizontal and 3.5°
vertical spread; 23 tics per barrel, then a 30-tic break-open reload after
the second.

Slot 3 has to carry more than Doom's shotgun does, because **the mod has no
super shotgun** (MAPINFO maps editor number 82 to `None`). So:

- 8 pellets instead of 7, and real vertical spread: a hunting gun with an
  open choke, not a riot gun.
- Two fast shots (121.8 DPS burst) then a long pause — **73.7 DPS
  sustained**, between Doom's shotgun (55.7) and its SSG (112.9).
- The reload is the balancing mechanism and the identity at once. It is the
  only weapon in the mod with an internal state (`int barrels`).

**D119: does it dominate?** The CEO, after Episodes 2 and 3: "you always
end up with the shotgun". Measured against its role:

| | IZh-58 | its role | verdict |
|---|---|---|---|
| DPS sustained | 73.7 | under slot 4 (PPSh 93.3, AKM 105) | in role |
| damage a unit of ammo | 80 a shell | Doom's shotgun 70, SSG 100 | in role |
| damage a small pickup | 320 (4 shells) | 80 a 10-round clip: 4 to 1 (Doom 2.8 to 1) | rich, the maps' job (§8) |
| a trooper's drop | **4 shells for a 30-HP man one shell kills: +3 a kill** | Doom's shotgun guy pays the same, but Episodes 2-3 field the Legion by the dozen | **over its role** |

So the gun is not too strong; it **feeds itself**. The minimum fix: a
dropped IZh carries **2 shells** (`SD_IZH_DROPPED_SHELLS`, an override of
`Weapon.ModifyDropAmount`, which halves 8 to 4 and is now capped at 2;
skills 1 and 5 still double it), +1 shell a kill instead of +3. Placed IZhs
still give 8; pellets, spread and reload are untouched, so the one-shot
infantry of §7 stays. The shells lying in the maps are §8's rule (no more
than 35 % of a map's ammunition). NOT VERIFIED in the engine (D26).

### Slot 4 — PPSh-41 (replaces Chaingun)

`4 x random(1,3)` = 4–12, avg 8, every 3 tics, 7.0° spread.
The real PPSh-41 cycles at about 900 rpm. At 35 tics/s the options are 2
tics (1050 rpm, and 175 DPS, which would make slots 5 and 6 pointless) or
3 tics (700 rpm, inside the weapon's real range). 3 tics it is.

Per round it is **weaker** than Doom's chaingun (8 vs 10) and sprays wider
(7.0° vs 5.625°); overall it is **+6.7% DPS** while burning **33% more
ammo per second**. That is the trade the icon of the mod should make: it
wins fights and empties your pockets. Pickup gives 35 rounds (half a
captured 71-round drum) rather than Doom's 20.

### Slot 4b — AKM (`SD_Akm`, replaces nothing; D112, in the mod since D116)

`6 x random(1,3)` = 6–18, avg 12 (the TT-33's round), every **4 tics**
(525 rpm; the real AKM's ~600 would be 3.5, and 3 tics would make it the
PPSh-41 with other dice): **105 DPS, +12.5 %** over the PPSh-41 for 25 %
fewer rounds a second. **Accurate in short bursts:** the first round of a
burst is pinpoint (Doom's rule for one bullet with no refire), rounds 2–3
spread ±2.0°, and from the 4th ±5.0° plus ±1.5° vertical (the muzzle
climbs), still under the PPSh's 7.0°. Tap it and it is a rifle for the
long sightlines of Episodes 2 and 3; hold it and it is a PPSh with a better
round. The weapon gives 30 rounds (one magazine). Selection order 650 (the
PPSh-41's 700): an empty AKM falls back to the PPSh. Every number is a
constant in `zscript/weapons/akm.zs`; the long why, the spread table and
the shots against the bestiary are `docs/engine/2026-10-22_P4_akm.md` §2.
**NOT YET MEASURED** (T5).

### Slot 5 — RPG-7 (replaces Rocket launcher)

PG-7V round: `30 x random(1,8)` = avg 135 direct, plus 100 blast damage over
a 104-unit radius; speed 28 map units/tic; 26-tic cycle.

A PG-7V is a **shaped charge**, so the trade against Doom's HE rocket is
explicit: **+50% on a direct hit, −22% blast damage, −19% blast radius,
+30% reload time, +40% flight speed**. Better against one armoured thing,
worse against a crowd, and harder to use as a panic weapon.

It keeps `XF_HURTSOURCE`: the RPG-7 **can kill the sergeant**. It is the
risk weapon, exactly as in Doom.

### Slot 6 — ROKS-3 flamethrower (replaces Plasma rifle)

`3 x random(1,8)` = 3–24, avg 13.5, every 3 tics, 4° random cone, damage
type `Fire`. **Range is capped at 528 map units** by the projectile's
lifetime (22 units/tic x 24 tics) rather than by an arbitrary cut-off.

**D119 (2026-10-23).** The CEO, after Episodes 2 and 3: "the flamethrower
is a little unbalanced, it kills every enemy very easily". It was 4 x
random(1,8) (avg 18): **210 DPS**, 80 % of Doom's plasma, the highest
sustained figure in the game, no reload, no self-damage, and a stream that
also stuns (11.67 hits a second against pain chances up to 50 %). Now:

| | before | D119 | the comparison |
|---|---|---|---|
| damage a jet | 18 (4–32) | **13.5 (3–24)** | `SD_FLAME_DAMAGE` 4 → 3 |
| DPS | 210 | **157.5** | Doom's rocket launcher exactly; 1.5 x the AKM (105), 60 % of Doom's plasma (262.5), under the RPG-7's 181.7 direct |
| damage a unit of fuel | 18 | **13.5** | Doom's plasma 22.5; the hand Katyusha ~16.9 direct a cell plus six blasts: big targets are now the Katyusha's fuel |
| a 40-cell pickup | 720 | 540 | |
| range, cadence, cone | 528, 3 tics, 4° | unchanged | |

Why the damage and not the cadence: the fire sound is a jet loop cut to
exactly 3 tics (`tools/audio/gen_weapon_alts.py`), so a 4-tic cadence
would stutter; and the per-cell cut is half the point, because fuel was
the most efficient ammunition in the game. Why not the range: 528 units is
the weapon's identity, and it already makes it useless across a hangar.
What it is now: in a corridor still the best thing the sergeant owns
against anything up to a heavy Panzermensch (75 jets, 6.4 s); against a
boss at range, or a crowd, the RPG-7 and the Katyusha are better.

The Liberty Colossus's and the Consortium's flames inherit `SD_FlameBlob`
and **keep 4 x random(1,8)** (`SD_BOSS_FLAME_DAMAGE` in their files): D119
retunes the weapon, not the bosses.

Ammo: `Cell`, read in this mod as pressurised fuel canisters.

### Slot 7 — hand Katyusha (replaces BFG 9000)

Six rockets in one salvo for 40 cells, fanned ±12.5°. Each rocket:
`25 x random(1,8)` = avg 112.5 direct plus 70 blast over 96 units.

Against a single target with every rocket connecting: ~675 direct damage,
below Doom's BFG (a 450-average ball **plus** up to 40 spray rays). Against
a group, the fan covers roughly 230 map units of frontage at 512 units of
distance and every rocket carries its own blast.

That inversion is the point: a Katyusha is area saturation, not a death ray.
The salvo does **not** hurt the sergeant (`A_Explode` flags = 0) — six
self-damaging rockets leaving the rails at once would make the weapon
unusable, and Doom's BFG shot does not hurt its owner either.

### Slot 8 — RGD-5 hand grenade (`SD_Rgd5`, replaces nothing; V3, ADR 012)

A fused fragmentation grenade thrown in an arc: **no impact damage, 100
blast at the centre over 128 units** (linear falloff, no core), **1.71 s
fuse** (60 tics) from the throw, a short bounce (×0.35 floors, ×0.4 walls),
one throw every **33 tics**, and it **hurts the thrower**. Constants in
`zscript/weapons/rgd5_grenade.zs` and `rgd5.zs`; the long why, the throw
distances and the kill radii in `docs/engine/2026-10-23_V3_rgd5.md` §2.

Why these numbers, against the PG-7V (slot 5):

- **Under the RPG-7 by unit.** A PG-7V gives the one it hits ~235 (135
  direct + 100 blast); a grenade at most **100**, 43 %. On a tight group of
  four troopers the PG-7V still does more (~350 against 200).
- **Better where the RPG-7 is not.** The blast is 23 % wider (128 against
  the shaped charge's 104: Doom's own rocket radius), so a spread group
  still bleeds (25 at 96 units, against the PG-7V's 8), and the arc and
  the bounce reach round a corner, over a barricade and down a stairwell.
- **The infantry's weapon.** One grenade kills a rifleman inside ~102
  units, a trooper inside ~90, a Stormtrooper inside ~51; the hound and
  up are not its job, and **the three bosses take nothing**
  (`+NORADIUSDMG`), so it never shortens a boss fight.
- **1.71 s.** The real UZRGM burns 3.2-4.2 s; the brief asked for 1.5-2 so
  a throw is not a wait and a monster does not walk out of the blast.
- **Scarce.** Six at most (twelve with the backpack, which gives none);
  the maps hand out 2-4 a map (§8, the design doc §6). Selection order
  4000, after the ice axe: an empty gun never puts a grenade in the hand.

**NOT YET MEASURED** (T5); not seen in the engine (D26).

## 4. Ammunition

The seven weapons of D13 reuse Doom's four pools unchanged, so every
Freedoom ammo pickup and the whole status bar keep working; the AKM (D116)
has a pool of its own (ADR 011), and so does the RGD-5 (V3, ADR 012; the
last two rows):

| Pool | Reads as | Used by | Pickup gives |
|---|---|---|---|
| `Clip` | 7.62x25 Tokarev rounds | TT-33, PPSh-41 | 20 (TT-33), 35 (PPSh-41) |
| `Shell` | 12-gauge shells | IZh-58 | 8 (the weapon; a trooper's dropped IZh 2 since D119, §3) |
| `RocketAmmo` | PG-7V grenades | RPG-7 | 2 |
| `Cell` | fuel canisters | ROKS-3, hand Katyusha | 40 |
| `SD_AkmAmmo` (ours, D116) | 7.62x39 rounds | AKM | 30 a magazine (the weapon too); 15 from a Legion gunner's drop; maximum 150, 300 with the backpack, which also gives 30 |
| `SD_Rgd5Ammo` (ours, V3) | RGD-5 grenades | RGD-5 | 1 a loose grenade (which also gives the weapon), 2 the pouch (the weapon), 4 a crate; maximum 6, 12 with the backpack, which gives none |

Since 2026-10-13 the "reads as" column is no longer only a figure of speech:
the player sees those names. The pools are still Doom's — nothing in the
table above changed — but the nine pickup actors are ours and carry Soviet
names and pickup lines. Numbers unaffected; see `MOD-SPEC.md` §6.4 and
`adr/003-ammo-naming-and-the-silent-shovel.md`.

The sapper's shovel (the ice axe since D40) also lost its swing sound the
same day (a placeholder that played the chainsaw start-up). **The swing still takes 27 tics**: the
`A_StartSound` call was removed from a frame that was already there, so
every number in §2 stands.

**Open for the CEO:** whether the hand Katyusha should have its own ammo
type instead of sharing fuel with the flamethrower. Sharing is what Doom
does (plasma and BFG both eat cells) and it needs no new pickup sprite; a
separate pool would read better in the fiction but costs an actor, a
DoomEdNum, a pickup sprite and a HUD line.

### 4.1 Starting inventory (changed 2026-10-13)

The sergeant spawns with **the TT-33 and 50 `Clip`, nothing else**: no
melee weapon and no `Fist`, so slot 1 is empty until the ice axe (the
shovel when this was written; D40 renamed it) is picked up.
Before this change `SD_Player` also listed `SD_Shovel`, and the CEO found
the bug in MAP01: the dorm's rack showed a pickup (Freedoom's chainsaw
sprite, the placeholder) that could not be taken, because a weapon the
player already owns and that gives no ammo is refused by the engine. The
map's design makes the rack the shovel's lesson, so the start item went,
not the rack. Pinned by `tests/test_arsenal.py`.

What the engine does with a player who owns no melee weapon, read from
`gzdoom.pk3` 4.14.2 (`zscript/actors/player/player.zs`,
`zscript/actors/inventory/weapons.zs`, `stateprovider.zs`):

- **Weapon raised on spawn.** `PlayerPawn.GiveDefaultInventory` readies a
  start weapon only if `CheckAmmo` passes at the moment it is given, so the
  rounds must already be in the inventory. `SD_Player` keeps Doom's order
  (weapon first, ammo last); `DoomPlayer` declares `Pistol`, `Fist`, `Clip`
  and spawns with the pistol, which only works if the list is walked
  last-declared first. The walk itself is C++; **VERIFIED in engine
  2026-10-13**: the TT-33 is raised on spawn with 50 rounds, owning only
  slot 2 (first frame of
  `docs/qa/evidence/2026-10-13_2014_mural-M1-M5_and_spawn.png`; row A0 of
  `docs/qa/evidence/2026-10-13_2117_F3_g3-map01-g3-auto-skill3-report.txt`).
- **Out of rounds, no ice axe.** Firing calls `FireWeapon`, which calls
  `CheckAmmo(PrimaryFire, autoSwitch = true)`; that calls `PickNewWeapon`,
  whose `BestWeapon` finds nothing and returns null, and nothing changes.
  The empty TT-33 stays raised and the trigger does nothing; `A_ReFire`
  takes the same path. `ReadyWeapon` never becomes null because nothing
  takes the TT-33 away. No crash path found.
- **Out of rounds, ice axe owned.** `BestWeapon` ignores `NOAUTOSWITCHTO`,
  so the empty TT-33 falls back to the ice axe (selection order 3700), as
  Doom's pistol falls back to the fist.
- **Taking the ice axe from the rack** raises it: `Weapon.AttachToOwner`
  switches to a newly picked-up weapon unless it has `NO_AUTO_SWITCH` or the
  player has set "never switch on pickup". The ice axe's `NOAUTOSWITCHTO` only
  governs the switch after an ammo pickup (`CheckWeaponSwitch`).
- **Berserk** (not placed in MAP01) calls `A_SelectWeapon("Fist")`, and
  `FindInventory` matches the exact class by default, so it does not select
  the ice axe with or without it (C++ lookup **NOT VERIFIED**). Harmless.

**Can the player run dry before the rack?** Counted from `src/maps/MAP01/map.py`
(the TEXTMAP's things); TT-33 average 12 per round, two rounds per rifleman
(§7), four at worst damage; a dead rifleman drops 5 rounds (Doom's half
clip). Skills 1 and 5 double ammo pickups and are not counted.

| In the dorm, with every door still shut | Skill 2 | Skill 3 | Skill 4 |
|---|---|---|---|
| Riflemen | 2 | 3 | 4 |
| Rounds to kill them, average / worst damage | 4 / 8 | 6 / 12 | 8 / 16 |
| Rounds there: start + dorm clips (+ drops) | 50 + 20 (+10) | 50 + 10 (+15) | 50 + 10 (+20) |

Running dry in the dorm means firing all 50 starting rounds and landing
fewer than 4 / 6 / 8 of them: more than 84 % misses on skill 4. And even
then nothing is lost: the rack is in the same room, about 400 units from
the player start with no door between (`tests/test_arsenal.py` checks
this on the TEXTMAP), so the cost is a walk under fire, not a softlock.

The exposure is **a player who walks past the rack**. Up to the IZh on the
guard post (Z1 to Z5, the washroom hound included):

| Up to the IZh rack | Skill 2 | Skill 3 | Skill 4 |
|---|---|---|---|
| Enemies (riflemen + stormtroopers + hounds) | 9 + 0 + 0 | 11 + 1 + 2 | 14 + 2 + 3 |
| TT-33 rounds to kill, every round landing | 18 | 53 | 77 |
| … with the ice axe taking the hounds | 18 | 27 | 38 |
| Rounds placed + start, no drops | 120 | 100 | 90 |
| Hit rate needed without the ice axe, no drops / with drops | 15 % / 11 % | 53 % / 34 % | **86 % / 48 %** |

On skill 4 a player who skips the ice axe and kills three hounds with the
pistol (13 rounds each) needs to land 86 % of his shots, or about half of
them if he also collects every rifleman's drop. If he runs out, he still
has a way back to the rack (`tests/test_udmf.py` checks a path back to the
start from every reachable sector, part of G3-6), but it is a long one. Any fix is a map change (the rack's prominence, or
rounds before the first hound), owned by `level-designer`.

## 5. What is NOT balanced yet

- **Enemies exist since F5 but have not been fought** (D26: the engine pass
  is owed). Their numbers are owned by `docs/engine/BESTIARY.md`, not
  repeated here; §7 below only crosses them with the arsenal. The real
  calibration is the MAP01 playtest.
- **Ammo economy per map**: since D119 a rule with a floor and a ceiling
  per skill (§8); still to be felt in a playtest.
- **Difficulty skills** are untouched; GZDoom's defaults apply.
- The ice axe's **berserk** interaction is inherited, not tuned.

## 6. How this was verified

GZDoom 4.14.2 over Freedoom 0.13.0, map `MAP02` (`MAP=MAP02 tools/run.sh`; the
practice range, `MAP=RANGE` since D62):

- All seven classes appear in `printinv` and **no Freedoom weapon does** —
  the player owned exactly `SD_Shovel` (now `SD_IceAxe`, D40), `SD_Tokarev`, `SD_Izh`, `SD_Ppsh`,
  `SD_Rpg7`, `SD_Roks3`, `SD_HandKatyusha`.
- Each one selects, raises, fires and consumes its pool. The hand Katyusha
  takes exactly 40 cells per salvo (600 → 520 over two salvos).
- Damage confirmed visually: the RPG-7 destroys the barrel line and clears
  the target rank; the shovel kills a summoned target in melee.
- `logs/gzdoom.log`: **zero** `Script error`, `Unknown`, `Missing`, `Warning`.

Numbers above are computed, not measured frame by frame; treat the DPS
column as a design ruler until QA plays MAP01 with real enemies.

## 7. The arsenal against the bestiary (F5, computed)

Average shots to kill, `ceil(HP / average damage per shot)`, every shot
landing. Enemy hit points come from `BESTIARY.md` §12 (the owner); average
damage per shot from §2 above. A ruler, like the DPS column: spread, pain
stagger and blast are not in it.

| Enemy | HP | Ice axe swings | TT-33 rounds | IZh-58 barrels | PPSh-41 rounds | RPG-7 direct hits | ROKS-3 bursts | Katyusha rockets |
|---|---|---|---|---|---|---|---|---|
| Reich rifleman | 20 | 2 | 2 | 1 | 3 | 1 | 2 | 1 |
| Legion trooper | 30 | 2 | 3 | 1 | 4 | 1 | 3 | 1 |
| Hybrid Stormtrooper | 60 | 4 | 5 | 1 | 8 | 1 | 5 | 1 |
| Reich hound | 150 | 10 | 13 | 2 | 19 | 2 | 12 | 2 |
| Doughboy | 400 | 27 | 34 | 5 | 50 | 3 | 30 | 4 |
| Panzermensch | 500 | 34 | 42 | 7 | 63 | 4 | 38 | 5 |
| Heavy Panzermensch | 1000 | 67 | 84 | 13 | 125 | 8 | 75 | 9 |
| The General | 3000 | 200 | 250 | 38 | 375 | 23 | 223 | 27 |
| Legion gunner (P4, D116) | 80 | 6 | 7 | 1 | 10 | 1 | 6 | 1 |
| Liberty Colossus (P4, D116; D119) | 3000 | 200 | 250 | 38 | 375 | 23 | 223 | 27 |
| Chrome Marshal (P4, D123: the colossus variant, MAP08) | 3000 | 200 | 250 | 38 | 375 | 23 | 223 | 27 |
| The Consortium (P4, D116; D119), whole | 4000 | 267 | 334 | 50 | 500 | 30 | 297 | 36 |

**The AKM** (slot 4b, avg 12 a round, D116) against the same rows:
rifleman 2, trooper 3, Stormtrooper 5, hound 13, Doughboy 34, Panzermensch
42, heavy Panzermensch 84, the General 250, the Legion gunner 7, the
Liberty Colossus and the Chrome Marshal 250 each, the Consortium 334 rounds (a 30-round magazine is
~360 at 100 %). An infantry gun: the bosses stay the RPG-7's and the
Katyusha's. The three P4 rows' numbers and their reasons are their design
documents (`2026-10-22_P4_ep2-enemies.md` §2–§3,
`2026-10-22_P4_ep3-final-boss.md` §3; the Chrome Marshal, D123, is the
colossus's numbers on the General's tinted sprites, `BESTIARY.md` §12 row
12); the colossus, the Marshal and the Consortium have
`+NORADIUSDMG`, so their RPG-7 column is the impact only, and the
Consortium's servants add to its bill (50 HP a rooted pair, 600 at its
Breach, 180 a free pair).

What it says, before anyone has played it:

- **The IZh-58 one-shots the three humanoids.** One barrel (avg 80) kills
  a rifleman, a trooper and a Stormtrooper, which is Doom's shotgun-vs-imp
  relationship made slightly kinder by the 8th pellet. If MAP01 feels too
  easy, this is the first lever (`SD_IZH_PELLETS`), not enemy health.
- **The RPG-7 column is a floor.** It counts the 135-average impact only;
  every enemy except the General also takes the blast (up to 100 at the
  centre), so a direct hit on a Panzermensch is nearer 235. The General has
  `+NORADIUSDMG` and takes the impact only, on purpose (`BESTIARY.md` §9).
- **A full hand-Katyusha salvo (six rockets, ~675 direct) kills anything up
  to the Panzermensch** if all six land on one target; the heavy
  Panzermensch needs a second salvo, and against the General one salvo is
  under a quarter of his health: the boss fight cannot be skipped with one
  weapon.
- **The General summons two riflemen at 1500 HP**, so the fight's second
  half adds two TT-33 pairs or one IZh barrel each to the bill.
- **The Legion gunner dies to one IZh-58 barrel about half the time** (80
  HP against an average 80); his drop, half an AKM magazine (15 rounds,
  ~180 damage), pays for the 7 rounds he costs at about a 45 % hit rate.
- **D119: the bosses at classic Doom's hit points.** The CEO, after the
  final boss: "I don't know if it is too hard (but if the original Doom
  was like that, let's keep that level)". It was not like that: the
  Consortium had 9000, more than twice Doom's toughest monster. Now:

  | Boss | HP | Doom's counterpart | was | PG-7V direct hits | Katyusha salvos (6 landing) | ROKS-3 jets |
  |---|---|---|---|---|---|---|
  | The General (MAP03) | 3000 | Spider Mastermind 3000 | 3000, unchanged | 23 | 4.4 | 223 |
  | Liberty Colossus (MAP06) | **3000** | Spider Mastermind 3000, the class it replaces | 4500 | 23 | 4.4 | 223 |
  | Chrome Marshal (MAP08's mini-boss, D123) | 3000 | the colossus's (his variant) | the colossus stood there at 3000 | 23 | 4.4 | 223 |
  | The Consortium (MAP09) | **4000** | Cyberdemon 4000 | 9000 | 30 | 5.9 | 297 |

  The Consortium keeps both phases and the Breach at half health: rooted
  4000–2001, the Breach at 2000, free 2000–0; the test fixture
  `SD_ConsortiumWounded` spawns at 2000 + 100 = 2100. Doom's Cyberdemon and
  Mastermind also ignore splash, as ours do (`+NORADIUSDMG`): Doom's 4000
  costs about 45 rockets (90 direct each), ours 30 PG-7V (135 direct), so
  even at Doom's hit points the fight is a little kinder than Doom's. The
  attacks are unchanged (the bosses' fire keeps 4 x random(1,8), §3). The
  rest of the bestiary was already at Doom's scale (rifleman 20 / zombieman
  20, trooper 30 / shotgun guy 30, Stormtrooper 60 / imp 60, gunner 80 /
  chaingunner 70, hound 150 / demon 150, Doughboy 400 / cacodemon 400,
  Panzermensch 500 / Hell knight 500, heavy 1000 / baron 1000) and is not
  touched.

`MOD-SPEC.md` debt T5 stays open until these numbers are measured in a
playtest.

## 8. Ammunition in the maps (D119)

**Why.** The CEO, after Episodes 2 and 3: ammunition "always comes out in
surplus", and "you always end up with the shotgun". G3-8 had a floor
(1.35 x what killing everything takes) and, on skill 4 only, a ceiling of
3 x; MAP07 measured 4.64 / 2.54 / 1.55 on skills 2 / 3 / 4. And a campaign
is not a pistol start: the sergeant arrives with what he did not spend in
the map before. These rules replace G3-8's number with a band per skill,
cap the shells, and spread the rest over the weapons the player actually
has. **The level designers apply them to MAP04–MAP09 now** (D119); MAP01–
MAP03 shipped in v1.0, are not part of the complaint, and are re-measured
only when the PM schedules it (their tests already hold them in the band;
V3 recounts them with the RGD-5, §8.6). Owner of the rule: this section; owner of
each map's numbers: its design doc in `docs/levels/`.

### 8.1 The ruler (G3-8's, with three D119 changes)

**Needed**, in shells, for every monster placed on that skill (MAP01's
`SHELLS_TO_KILL`, about 62.5 HP a shell):

| Monster | shells | | Monster | shells |
|---|---|---|---|---|
| Reich rifleman | 1 | | Doughboy | 6 |
| Legion trooper | 1 | | Panzermensch | 8 |
| Hybrid Stormtrooper | 2 | | heavy Panzermensch | 16 |
| Legion gunner | 2 | | the General | 48 |
| Reich hound | 3 | | **Liberty Colossus** | **48** (D119; was 72) |
| | | | **Chrome Marshal** (D123) | **48**, the colossus's |
| | | | **the Consortium** | **64** (D119; was 144) + its servants, as MAP09's test already counts them |

**Placed**, in shell-equivalents, every pickup on the route of that skill:

| Unit | shell-equivalents | from | pickups (units) |
|---|---|---|---|
| a shell | 1 | the IZh's 80 a barrel | shells 4, box 20, IZh 8 |
| a 7.62x25 round (`Clip`) | 0.1 (10 a shell) | the PPSh's 8 | clip 10, box 50, PPSh-41 35 |
| a 7.62x39 round (`SD_AkmAmmo`) | 0.15 (12 / 80) | the AKM's 12 | magazine 30, AKM 30 |
| a PG-7V (`RocketAmmo`) | 2 | 135 direct plus the blast | 1, box 5, RPG-7 2 |
| a unit of fuel (`Cell`) | **0.16875 (13.5 / 80; D119, was 0.25)** | the ROKS-3's jet, 13.5 since D119 | 20, pack 100, ROKS-3 40, Katyusha 40 |
| an RGD-5 (`SD_Rgd5Ammo`; V3) | 1.25 (100 / 80) | the blast at the centre on one target, as a shell counts one barrel on one | loose 1, pouch (the weapon) 2, crate 4 |

**Grenades never count towards a boss's stage** (8.4, rule 3): the three
bosses take no splash. The backpack counts as what it gives (§4). **Not counted** in the ratio:
secrets, drops, skills 1 and 5's double ammunition, and the inventory
carried from the map before.

### 8.2 The band, per skill

`ratio = placed / needed`, on the route, no secret, no drop:

| Skill | floor | ceiling | before D119 |
|---|---|---|---|
| 2 | 1.5 | 2.0 | ≥ 1.35, no ceiling |
| 3 | 1.3 | 1.6 | ≥ 1.35, no ceiling |
| 4 | 1.2 | 1.45 | ≥ 1.35, < 3 |

In short: skill 2 **1.5–2.0**, skill 3 **1.3–1.6**, skill 4 **1.2–1.45**.
The floors of skills 3 and 4 sit under the old 1.35 on purpose: the ruler
already carries a 28 % margin (a shell is counted at 62.5 HP and averages
80), so skill 4's 1.2 still places 1.2 x 80 / 62.5 = 1.54 x the hit points
as average damage, and the player brings the previous map's leftovers.

**Stage by stage** (the readiness check every map test already has: the
damage placed so far plus the 50 starting rounds x 8 against the hit points
met so far) keeps running, with that skill's **floor** as the margin
(1.5 / 1.3 / 1.2) instead of 1.35, and the fuel at **13.5** a unit
(`ROKS_AVERAGE = 13.5`).

### 8.3 Shells: no more than 35 % (every skill)

    shell share = (placed shells + 2 x Legion troopers on that skill)
                / (placed shell-equivalents + every drop on that skill)  <= 0.35

Drops, in shell-equivalents: a Legion trooper's IZh **2** (2 shells since
D119, §3), a rifleman's clip 0.5 (5 rounds), a Legion gunner's magazine
2.25 (15 AKM rounds). The drops count **here only**, because they are where
the shells came from: in Episodes 2 and 3 the Legion fields troopers by the
dozen. A placed IZh counts its 8 shells. If a map with many troopers cannot
get under 35 % without stripping every shell box, the fix is fewer boxes,
not fewer troopers.

### 8.4 The rest, by the weapons the player has

For each stage of the route (the stages of the readiness check):

1. **A pool is placed only from the stage where its weapon is.** `Clip`
   from the start (the TT-33 is the start weapon); AKM rounds from the AKM
   or the first gunner; PG-7V from the RPG-7; fuel from the ROKS-3 or the
   Katyusha. The map's own weapons count (each map places its weapons for
   a pistol start); a weapon a previous map gave does not.
2. **The newest weapon's pool leads.** Of the stage's non-shell ammunition
   (in shell-equivalents), the pool of the last weapon met on the route
   before or in that stage (the IZh excepted: shells have their own rule,
   8.3) has the largest share, and at least **40 %** of it. A stage that
   introduces no weapon keeps the previous stage's newest.
   *PM amendment (2026-10-23, after the first Episode 3 pass):* when the
   newest weapon is the **ROKS-3**, fuel need not lead (it stays moderate:
   at most **15 %** of the map's damage); the previous newest leads instead.
   **PG-7V stay a heavy pool, not the main one:** outside the boss's stage
   (or a mini-boss's), rockets are at most **30 %** of the stage's damage,
   so a stage where the RPG-7 is newest is led by the newest bullet weapon
   (the AKM, else the PPSh) and the RPG-7 is the strong second. The CEO's
   complaint was one weapon carrying the whole game (D119): the shotgun
   must not be replaced by the rocket launcher.
3. **The boss is the heavy weapons' job.** In the boss's stage, PG-7V and
   fuel together cover at least **1.0 x** the boss's shells (the General
   and the colossus 48, the Consortium 64). *(The second half of the
   first draft, "shells and rounds alone cover every monster but the boss
   at the floor", is dropped by the PM: it cannot hold together with 8.3
   and the skill-4 ceiling.)*

### 8.5 What changes in the map tests

| Constant | before | D119 |
|---|---|---|
| `G3_8_MARGIN` | 1.35 on every skill, < 3 on skill 4 | a floor and a ceiling per skill (8.2) |
| `SHELLS_PER_CELL` | 0.25 | `13.5 / 80` |
| `ROKS_AVERAGE` | 18 | 13.5 |
| `SHELLS_TO_KILL["SD_LibertyColossus"]` | 72 | 48 |
| `SHELLS_TO_KILL["SD_Consortium"]` | 144 | 64 |
| hit points read from the class files | colossus 4500, Consortium 9000 | 3000, 4000 (read, not typed: nothing to change) |
| new | — | the shell share (8.3) and the newest weapon's share (8.4) |

`tests/test_d119_balance.py` pins this section's weapon and boss numbers
against the code.

### 8.6 The RGD-5 in the maps (V3 A4, 2026-10-24)

Placed in MAP04-MAP09 and the range (`docs/engine/2026-10-23_V3_rgd5.md`
§6; the maps' docs, "V3 (2026-10-24)"), and in Episode 1 the same day once
the PM scheduled it. A grenade is a **consumable** in
each map's `ITEMS`, so it scales **down** with skill, unlike the D119
ammunition; none in a boss's arena, no crate in the campaign. Recount,
1.25 shell-equivalents a grenade (8.1), in the band (8.2) and in the shell
share's whole (8.3) only; the stage readiness, the lead (8.4.2) and the
boss's stage (8.4.3) leave grenades out. No other pickup moved: every map
stays in its band.

| Map | grenades, skills 2 / 3 / 4 | ratio skill 2 | skill 3 | skill 4 |
|---|---|---|---|---|
| MAP01 | 4 / 3 / 2 (the pouch, 2 loose) | 1.500 → 1.661 | 1.341 → 1.401 | 1.213 → 1.244 |
| MAP02 | 3 / 3 / 2 (the pouch, 1 loose) | 1.512 → 1.606 | 1.410 → 1.466 | 1.237 → 1.263 |
| MAP03 | 4 / 3 / 2 (the pouch, 2 loose) | 1.510 → 1.561 | 1.328 → 1.359 | 1.216 → 1.229 |
| MAP04 | 4 / 3 / 2 (the pouch, 2 loose) | 1.658 → 1.746 | 1.440 → 1.481 | 1.228 → 1.246 |
| MAP05 | 3 / 3 / 2 (3 loose) | 1.559 → 1.611 | 1.334 → 1.366 | 1.233 → 1.248 |
| MAP06 | 4 / 3 / 2 (the pouch, 2 loose) | 1.540 → 1.577 | 1.387 → 1.408 | 1.280 → 1.288 |
| MAP07 | 4 / 3 / 2 (the pouch, 2 loose) | 1.657 → 1.725 | 1.465 → 1.494 | 1.294 → 1.308 |
| MAP08 | 3 / 2 / 2 (3 loose) | 1.583 → 1.631 | 1.370 → 1.384 | 1.282 → 1.293 |
| MAP09 | 3 / 2 / 2 (3 loose) | 1.610 → 1.628 | 1.347 → 1.355 | 1.239 → 1.245 |
| RANGE | 6 on every skill (the pouch, a crate) | — | — | — |

The band: 1.5-2.0 / 1.3-1.6 / 1.2-1.45. Each map test counts grenades in
its `ammo_placed` (`GRENADES_GIVEN`, `SHELLS_PER_GRENADE`);
`tests/test_rgd5_maps.py` pins the counts, the zones, the arenas and the
range. Drops (a trooper's grenade) are still only a recommendation (the
design doc §6).

## 9. Medals (V3 B3, ADR 013; proposal, 2026-10-23)

At the end of each episode (after the stats of MAP03, MAP06 and MAP09, before
the ending text) the awards page shows five Soviet decorations; each is
earned or not by the **whole episode's** figures: the three maps' kills,
secrets and times **summed**, against the summed par times. A map of the
episode not played in this game (a New Game is started on its first map;
a death that restarts a map from scratch starts a new record, MOD-SPEC 6.13)
counts as not played. The page lists all five every time, the earned ones
lit, the others dark with the rule still readable, so the player learns what
to aim for. Code: `SD_Awards` in `zscript/sd/awards.zs`; the table below is
read by `tests/test_awards.py`.

| Award | Rule | Constant | Value |
|---|---|---|---|
| Medal "For Courage" | the episode completed (always: one award for everyone who gets there) | — | — |
| Order of the Red Star | kills, % of the episode's enemies, at least | `SD_REDSTAR_KILLS_PCT` | 75 |
| Order of the Red Banner | secrets, % of the episode's secrets, at least (an episode with none counts 100) | `SD_REDBANNER_SECRETS_PCT` | 100 |
| Order of the Patriotic War | the episode's time no more than the sum of its maps' `par` (whole seconds) | — | — |
| Gold Star, Hero of the Soviet Union | all three maps played in this game, kills at least the Hero's %, every secret, within par, and on skill 3 or harder | `SD_HERO_KILLS_PCT` | 90 |
| (the Hero's skill) | the episode's easiest skill, as the skill's SpawnFilter bit: 4 = Normal = «Not one step back» (MAPINFO) | `SD_HERO_MIN_SPAWNFILTER` | 4 |
| (an episode) | maps per episode | `SD_MAPS_PER_EPISODE` | 3 |

Why these numbers:

- **75 % for the Red Star.** Doom's 100 % kills is a completionist's figure
  (monsters behind closed areas, on ledges, teleported in late); three
  quarters of an episode means fighting through each map rather than running
  it, and leaves room for a missed room per map. Kills above 100 % (Nightmare
  respawns, skill 5) still count, as the stats screen counts them.
- **100 % for the Red Banner**, as the brief asks: the secrets are hand-placed,
  with clues (each map's design doc, "Secrets"), so all of them is fair.
- **Par for the Patriotic War.** `par` is what the stats screen prints as
  PAR. **Debt:** every par is still the mod-engineer's or the
  level-designer's placeholder (MAPINFO comments; MAP01 210 s, MAP02 300,
  MAP03 360 -> episode 1 14:30; MAP04-06 300/330/420 -> 17:30; MAP07-09
  330/360/480 -> 19:30), not a timed human run. Until QA times them this
  award may be easy or impossible; the rule does not change when the pars do.
- **The Gold Star needs all of it, at 90 %, on skill 3 or harder**: the
  rung the menu starts on (`DefaultSkill`), so the Hero is earned at the
  game's intended difficulty or above, never on the two easy rungs; 90 %
  rather than 75 % because it is the one award that should feel rare. It
  echoes skill 5's name, «Hero of the Soviet Union, posthumously».

**NOT VERIFIED in the engine** (D26): the PM's pass ends each episode with
known figures (the console's `kill monsters` gives 100 % kills) and checks the
page against this table.
