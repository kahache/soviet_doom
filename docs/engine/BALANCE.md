# BALANCE — the arsenal in numbers

Owner: `mod-engineer`. Status: **F4, first pass, verified in GZDoom 4.14.2**
(every weapon fires, consumes ammo and kills in `MAP02`; see §6).
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
| 1 | Sapper's shovel | — | 15 (6–24) | 27 | 1.30 | 19.4 | 84 (melee) |
| 2 | TT-33 Tokarev | 1 Clip | 12 (6–18) | 16 | 2.19 | 26.3 | ~1024 |
| 3 | IZh-58 double barrel | 1 Shell | 80 (8 pellets) | 23, +30 every 2 shots | 0.92 sustained | 73.7 sustained / 121.8 burst | ~512 |
| 4 | PPSh-41 | 1 Clip | 8 (4–12) | 3 | 11.67 | 93.3 | ~768 |
| 5 | RPG-7 | 1 RocketAmmo | 135 direct + 100 blast / 104 u | 26 | 1.35 | 181.7 direct | unlimited |
| 6 | ROKS-3 flamethrower | 1 Cell | 18 (4–32) | 3 | 11.67 | 210.0 | **528 hard limit** |
| 7 | Hand Katyusha | 40 Cell | 6 x (112.5 direct + 70 blast / 96 u) | 60 | 0.58 | ~394 if all six land | unlimited, fan ±12.5° |

The ladder (19 → 26 → 74 → 93 → 182 → 210 → 394) keeps Doom's shape: every
slot beats the one below it, and the jumps land in the same places.

## 3. Why each number

### Slot 1 — sapper's shovel (replaces Fist)

`random(3,12) << 1` = 6–24, avg 15, over a 27-tic swing.
A sharpened MPL-50 entrenching tool is not a fist: **+36% damage** for
**+23% swing time**, which nets +11% DPS. It stays a last resort (it is still
under one twentieth of slot 4) but it no longer feels like punching a wall.
Kickback 120 against the Fist's 100: a shovel shoves. Berserk keeps Doom's
x10, so the berserk pack is still the thing that turns melee into a weapon.

### Slot 2 — TT-33 Tokarev (replaces Pistol)

`6 x random(1,3)` = 6–18, avg 12, every 16 tics, 4.5° spread.
The TT-33 fires a high-velocity bottlenecked 7.62x25 round; it should hit
harder and group tighter than Doom's generic pistol (5 base, 5.625°). The
cycle drops from 19 to 16 tics because a single-action pistol has no
mechanism to wait for.

Result: **26.3 DPS against Doom's 18.4, +43%.** This is the single most
aggressive number in the table and the first one to cut if the opening
minutes of MAP01 feel soft. It is deliberate: the sergeant starts with this
gun and nothing else that shoots, and Doom's pistol is famously the weapon
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

`4 x random(1,8)` = 4–32, avg 18, every 3 tics, 4° random cone, damage type
`Fire`. **Range is capped at 528 map units** by the projectile's lifetime
(22 units/tic x 24 tics) rather than by an arbitrary cut-off.

80% of Doom's plasma DPS (210 vs 262.5) at the same ammo cost, in exchange
for a hard range limit that no other weapon in the game has. Across a hangar
it is useless; in a corridor it is the best thing the sergeant owns.

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

## 4. Ammunition

The arsenal reuses Doom's four pools unchanged, so every Freedoom ammo
pickup and the whole status bar keep working:

| Pool | Reads as | Used by | Pickup gives |
|---|---|---|---|
| `Clip` | 7.62x25 Tokarev rounds | TT-33, PPSh-41 | 20 (TT-33), 35 (PPSh-41) |
| `Shell` | 12-gauge shells | IZh-58 | 8 |
| `RocketAmmo` | PG-7V grenades | RPG-7 | 2 |
| `Cell` | fuel canisters | ROKS-3, hand Katyusha | 40 |

Since 2026-10-13 the "reads as" column is no longer only a figure of speech:
the player sees those names. The pools are still Doom's — nothing in the
table above changed — but the nine pickup actors are ours and carry Soviet
names and pickup lines. Numbers unaffected; see `MOD-SPEC.md` §6.4 and
`adr/003-ammo-naming-and-the-silent-shovel.md`.

The sapper's shovel also lost its swing sound the same day (a placeholder
that played the chainsaw start-up). **The swing still takes 27 tics**: the
`A_StartSound` call was removed from a frame that was already there, so
every number in §2 stands.

**Open for the CEO:** whether the hand Katyusha should have its own ammo
type instead of sharing fuel with the flamethrower. Sharing is what Doom
does (plasma and BFG both eat cells) and it needs no new pickup sprite; a
separate pool would read better in the fiction but costs an actor, a
DoomEdNum, a pickup sprite and a HUD line.

## 5. What is NOT balanced yet

- **Enemies exist since F5 but have not been fought** (D26: the engine pass
  is owed). Their numbers are owned by `docs/engine/BESTIARY.md`, not
  repeated here; §7 below only crosses them with the arsenal. The real
  calibration is the MAP01 playtest.
- **Ammo economy per map** is untested: how much of each pool MAP01 hands
  out decides whether the PPSh's appetite is a cost or a joke.
- **Difficulty skills** are untouched; GZDoom's defaults apply.
- The shovel's **berserk** interaction is inherited, not tuned.

## 6. How this was verified

GZDoom 4.14.2 over Freedoom 0.13.0, map `MAP02` (`MAP=MAP02 tools/run.sh`):

- All seven classes appear in `printinv` and **no Freedoom weapon does** —
  the player owns exactly `SD_Shovel`, `SD_Tokarev`, `SD_Izh`, `SD_Ppsh`,
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

| Enemy | HP | Shovel swings | TT-33 rounds | IZh-58 barrels | PPSh-41 rounds | RPG-7 direct hits | ROKS-3 bursts | Katyusha rockets |
|---|---|---|---|---|---|---|---|---|
| Reich rifleman | 20 | 2 | 2 | 1 | 3 | 1 | 2 | 1 |
| Legion trooper | 30 | 2 | 3 | 1 | 4 | 1 | 2 | 1 |
| Hybrid Stormtrooper | 60 | 4 | 5 | 1 | 8 | 1 | 4 | 1 |
| Reich hound | 150 | 10 | 13 | 2 | 19 | 2 | 9 | 2 |
| Doughboy | 400 | 27 | 34 | 5 | 50 | 3 | 23 | 4 |
| Panzermensch | 500 | 34 | 42 | 7 | 63 | 4 | 28 | 5 |
| Heavy Panzermensch | 1000 | 67 | 84 | 13 | 125 | 8 | 56 | 9 |
| The General | 3000 | 200 | 250 | 38 | 375 | 23 | 167 | 27 |

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

`MOD-SPEC.md` debt T5 stays open until these numbers are measured in a
playtest.
