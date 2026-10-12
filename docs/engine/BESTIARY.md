# BESTIARY — enemy specification (F5)

Living document. Owner: `mod-engineer`. Russian mirror:
`docs/ru/engine/BESTIARY.md`. Status: **v0, specification only, 2026-10-12.**
No ZScript exists for any of these actors yet.

This document is the contract for the six ratified enemies (D13) between
`mod-engineer` (classes, numbers, states), `art-director` (sprites, colour)
and `sound-designer` (sound lumps). Product facts — the two allied factions,
their look, the tone — come from `docs/PRD.md` (D9, D12, D13, D14) and
`docs/product/LORE.md` and are not repeated here. Colour rules come from
`docs/art/ART-BIBLE.md` §6 and are quoted, not redefined.

**Nothing here is implemented.** Every number is a *proposal with a reason*;
the ones marked **(H)** are hypotheses to calibrate in the F5 playtest.

Minimal glossary, for anyone new to Doom modding:

- **Actor**: any thing that exists in the map — a monster, a projectile, a
  barrel. In GZDoom an actor is a ZScript class.
- **DoomEdNum** (editor number): the number a map editor writes into the map
  to say "put *this* kind of thing here". Two actors with the same number
  collide.
- **`replaces`**: a ZScript keyword. `class A replaces B` tells the engine to
  spawn `A` everywhere the game would have spawned `B`.
- **State**: one step of an actor's animation (sprite frame + duration + an
  action to run). `Spawn`, `See`, `Pain`, `Melee`, `Missile`, `Death`,
  `XDeath` are the states a monster needs.
- **Hitscan**: an instant-hit shot (a rifle). **Projectile**: a travelling
  actor you can dodge (a fireball).
- **Sprite name**: exactly 4 letters, then a frame letter and a rotation
  digit — `SDRRA1` is sprite `SDRR`, frame `A`, rotation 1 (seen from the
  front). Rotation `0` means "same image from every angle".

---

## 1. Reference values: what the engine actually does

Everything below is **verified** by reading the ZScript shipped inside
`/Applications/GZDoom.app/Contents/MacOS/gzdoom.pk3` of the installed
**GZDoom g4.14.2** (D3), files `zscript/actors/doom/*.zs`. These are the
numbers our numbers are argued against.

| Doom actor | HP | Radius × Height | Speed | PainChance | Attack |
|---|---|---|---|---|---|
| `ZombieMan` | 20 | 20 × 56 | 8 | 200 | hitscan, `random(1,5) × 3` = 3–15 |
| `ShotgunGuy` | 30 | 20 × 56 | 8 | 170 | 3 hitscans, `random(1,5) × 3` each |
| `DoomImp` | 60 | 20 × 56 | 8 | 200 | melee `random(1,8) × 3`; else `DoomImpBall` |
| `Demon` | 150 | 30 × 56 | 10 | 180 | melee only, `random(1,10) × 4` |
| `Cacodemon` | 400 | 31 × 56 | 8 | 128 | melee `random(1,6) × 10`; else `CacodemonBall` |
| `HellKnight` | 500 | 24 × 64 | 8 | 50 | melee `random(1,8) × 10`; else `BaronBall` |
| `BaronOfHell` | 1000 | 24 × 64 | 8 | 50 | same as Hell Knight |
| `Cyberdemon` | 4000 | 40 × 110 | 16 | 20 | 3 × `Rocket` |

| Doom projectile | Radius × Height | Speed | Damage property |
|---|---|---|---|
| `DoomImpBall` | 6 × 8 | 10 (fast 20) | 3 → `random(1,8) × 3` |
| `CacodemonBall` | 6 × 8 | 10 (fast 20) | 5 → `random(1,8) × 5` |
| `BaronBall` | 6 × 16 | 15 (fast 20) | 8 → `random(1,8) × 8` |

> Doom's projectile `Damage N` is not N damage: the engine rolls
> `random(1,8) × N`. A `Damage 5` ball does 5–40.

Two further verified facts that shape the design:

1. **`A_PosAttack`, `A_SPosAttack`, `A_TroopAttack`, `A_SargAttack`,
   `A_HeadAttack`, `A_BruisAttack` are declared in `extend class Actor`**, not
   as members of `ZombieMan`/`DoomImp`/etc. An actor derived from plain
   `Actor` can call them. (Verified in `possessed.zs:267`, `doomimp.zs:106`,
   `demon.zs:88`, `cacodemon.zs:101`, `bruiser.zs:153`.) We will **not** use
   them anyway — see §2.4 — but it means deriving from `Actor` costs us
   nothing in available code.
2. **Editor numbers 14001–14165 are taken by GZDoom itself**
   (`mapinfo/common.txt`: `AmbientSound` 1–64, `AmbientSoundNoGravity`,
   `SoundSequence`, `SoundEnvironment`; the free blocks above 9000 are
   `10504–14000` and `14166–31999`). This independently confirms, from the
   engine's own data rather than from the wiki, the finding that **ADR 002**
   already acted on: the old `14000–14999` proposal was wrong and the mod now
   reserves **21000–21999**, of which **21100–21199 is the enemy
   sub-range** (`docs/engine/MOD-SPEC.md` §6.1). This document assigns
   numbers inside that sub-range and introduces no new range.

---

## 2. Conventions binding on all seven classes

### 2.1 Faction colour contract (from ART-BIBLE §6)

| | Fourth Reich | Liberty Legion |
|---|---|---|
| Body mass | `khaki_olive` ramp (index 144–159), mid ≈ `(108,97,64)` | reserved **pink/flesh ramp** (to be added to `palette.json` v2) |
| Shadow / armour | true black + `khaki_olive` 0–3 | `steel_blue` 0–5 (dark chrome) |
| Highlight | `khaki_olive` 12–15 | `steel_blue` 11–15 (bright chrome) |
| Helmet | Stahlhelm, flared skirt | M1 "pot", round bowl |
| Accent (D12) | swastika armband: `flag_red` + black + `plaster_warm` | US flag shoulder patch: `flag_red` + `steel_blue` + `plaster_warm` |
| Forbidden | `military_green` (owned by the world: doors, plates) | large areas of pure `concrete_cold` (camouflage) |
| Blood | dark olive — `khaki_olive` 1–4 | pale — `plaster_warm` 10–14 |

Value check against ART-BIBLE §6.1 (walls live in the 0.45–0.70 band, concrete
mid is 0.58): Reich body ≈ 0.38, Legion body ≈ 0.72–0.80. Both clear the
"≥ 2 ramp steps away from concrete" rule, in opposite directions. **The two
factions are told apart by value, not by hue** — that is the whole legibility
plan and it also survives Doom's sector lighting, which crushes hue first.

Blood colour is set with the `BloodColor` property, which recolours the
standard blood sprite; no new blood actor is needed. Keep both bloods
desaturated so the floor never competes with a `flag_red` accent.

### 2.2 Infighting

**Vanilla Doom infighting is kept.** No `Species` / `DontHarmSpecies` flags
are set, so a Reich shell that clips a Legion trooper starts a fight, exactly
as in Doom. Lore reading: the alliance is one of convenience — "they fight
for profit, we fight for everyone" (`LORE.md`). This is also the single
biggest tactical pleasure of Doom and removing it would change the rhythm of
every room. Open question **Q5** for the CEO.

### 2.3 Naming

| Thing | Pattern | Example |
|---|---|---|
| ZScript class | `SD_<Name>` | `SD_ReichRifleman` |
| Source file | `src/zscript/monsters/<snake_case>.zs`, one class per file | `src/zscript/monsters/reich_rifleman.zs` |
| Sprite | `SD` + 2 letters | `SDRR` |
| Sound lump | `SD` + 3-letter actor code + 3-letter event code = 8 chars | `SDRRISIT` |
| SNDINFO logical name | `sd/mon/<actor>/<event>` | `sd/mon/reichrifleman/sight` |
| LANGUAGE id | `SD_TAG_<X>`, `SD_OB_<X>`, `SD_OBHIT_<X>` | `SD_TAG_RIFLEMAN` |

The logical-name scheme matches the arsenal's (`sd/weapon/shovel/swing`,
already in `src/zscript/weapons/shovel.zs`). The lump scheme differs by one
character — the arsenal uses a 2-letter weapon code (`SDSHSWG`), the
bestiary a 3-letter actor code (`SDRRISIT`) — because there are more actors
than weapons and more events per actor. Both stay inside the 8-character
PK3 rule of MOD-SPEC §2; the SNDINFO *logical* name has no such limit.

**Namespace check against MOD-SPEC §6.2 and §6.3 (done 2026-10-12).** The
arsenal has reserved the sprite prefixes `SDSH SDSP SDTT SDTF SDTP SDIZ SDIF
SDIP SDPP SDPF SDPQ SDRL SDRF SDRP SDPG SDPX SDRK SDKF SDKP SDFL SDFX SDHK
SDHF SDHP SDKR` and the sound lumps `SDSH* SDTT* SDIZ* SDPP* SDRP* SDRK*
SDHK*`. The bestiary's prefixes (`SDRR SDLT SDHS SDHN SDDB SDPM SDGN SDBL
SDDL SDPL SDGL`) and sound lumps (`SDRRI* SDLTR* SDSTO* SDHND* SDDGB* SDPZR*
SDGEN*`) collide with none of them, and no lump in `freedoom2.wad` begins
with `SD`.

### 2.4 Base class and replacement strategy

Every enemy is `class SD_X : SD_Monster`, where `SD_Monster : Actor` is a
thin shared base holding what all seven have in common (`Monster;`,
`+FLOORCLIP`, a `Faction` enum used by future lore/HUD code, and the default
`MeleeRange`). Nothing derives from `ZombieMan`, `DoomImp` or the others.

Why not derive from the Doom monsters:

- Inheriting brings their `States` block, which references **IWAD sprites**
  (`POSS`, `TROO`…). Any state we forget to override silently falls back to a
  Freedoom sprite mid-fight — a bug that only shows on one animation.
- It brings their `SeeSound "grunt/sight"` etc.; we would ship a Soviet
  mod that grunts in Freedoom.
- It brings `DropItem "Clip"` and `Obituary "$OB_ZOMBIE"` — IWAD strings in
  our HUD.
- The attack functions we would have inherited are on `Actor` anyway (§1.1).

**Why this differs from the arsenal.** ADR 002 made the opposite choice for
weapons: `class SD_X : <DoomWeapon> replaces <DoomWeapon>`. That is correct
*there* and wrong *here*, and the reason is sprites. A weapon has one
rotationless HUD sprite set and almost no inherited state machine worth
fearing; the Doom weapon base is mostly plumbing (ammo bookkeeping, slot
behaviour) that we want. A monster's inherited `States` block is 20+ frames
in 8 rotations pointing at IWAD lumps, and a single un-overridden state is a
Freedoom sprite appearing in the middle of our fight. Different risk,
different answer — recorded so the inconsistency reads as a decision rather
than an oversight.

Each class additionally declares `replaces <DoomActor>` so that (a) a Doom II
or Freedoom map loaded with the mod becomes a Soviet Doom map, and (b) the
`level-designer` can place either the Soviet DoomEdNum or the familiar Doom
one. `replaces` does **not** consume the replaced actor's editor number for
our own use; both numbers end up spawning our class.

**Attack code:** we use the generic `Actor` functions
(`A_CustomBulletAttack`, `A_SpawnProjectile`, `A_CustomMeleeAttack`,
`A_CustomComboAttack`) rather than `A_PosAttack`/`A_TroopAttack`, because the
Doom functions hard-code both the damage formula and the sound lump
(`A_PosAttack` plays `"grunt/attack"` literally). Our damage formulas live in
named constants in the class, per CLAUDE.md.

This whole subsection is **ADR material**: see §13, ADR **003** to be written
when implementation starts (002 is taken by the arsenal).

### 2.5 DoomEdNum block

The bestiary spends the **21100–21199** sub-range already reserved for
enemies by ADR 002 and MOD-SPEC §6.1. Assignments: 21100–21109 the seven
classes plus two reserved variants (§12); 21110–21199 free for later
enemies; invader-side corpses and decorations belong to the decoration
sub-range **21200–21299**, not here.

**Editor numbers are assigned only in MAPINFO's `DoomEdNums` block**, which
is the method ADR 002 established for the arsenal and the only one available
to a ZScript class. Corroborated here: the string `DoomEdNum` does not occur
anywhere in GZDoom 4.14.2's own `zscript/` tree, so there is no such actor
property to use. The bestiary's numbers go into the same `DoomEdNums` block
as the weapons' — one block, one place to check for collisions.

### 2.6 Sprite work: the honest total

With Doom's mirroring convention (rotations 2&8, 3&7, 4&6 share one image, so
an 8-rotation frame costs 5 drawings) the seven actors and their four
projectiles need about **356 sprite images** (itemised in §12). That is the
single largest cost in F5 and it is larger than
all of F2 put together. Two mitigations, both for `art-director` to judge:

1. **Freedoom as reference, not as pixels.** Freedoom is BSD-3-Clause
   (verified: `iwads/freedoom-0.13.0/COPYING.txt`, "Redistribution and use …
   with or without modification, are permitted"), so shipping edited Freedoom
   sprites is legal provided we retain the copyright notice and disclaimer in
   `docs/art/LICENSES.md` and never imply Freedoom endorses the mod (the
   third clause). BSD-3 is permissive, so derivatives may carry our
   CC BY-NC-SA 4.0 (D15). **But** a recoloured Freedoom monster still reads as
   Freedoom, and the mod's identity is the product. Recommendation: use
   Freedoom for *animation timing and silhouette blocking*, draw our own
   pixels. Open question **Q6**.
2. **Pose once, render many.** A posed low-poly model or a paper-doll rig
   rendered at 8 angles is the standard way modern TCs afford this. Out of
   `mod-engineer` scope; flagged so F5 is planned with the real number.

The sprite lumps `POSS SPOS CPOS TROO SARG HEAD BOSS BOS2` all exist in
`iwads/freedoom2.wad` (verified by lump listing: 70, 49, 48, 53, 46, 36, 72,
71 lumps respectively). Their *visual content* has **NOT been inspected** by
`mod-engineer`; every "could derive from Freedoom" judgement below is
**NOT VERIFIED** and is for `art-director` to confirm by looking.

No Freedoom lump begins with `SD` (verified), so our sprite namespace is free.

---

## 3. Fourth Reich rifleman — basic infantry (1 of 2)

> Bestiary row "Yankee-Nazi recruits" is specified as **two classes**, one per
> faction, because Doom's basic-infantry slot is itself two actors (zombie and
> sergeant) and because splitting them is what puts both factions in the
> player's first room. Open question **Q1**.

| Field | Value |
|---|---|
| Class | `SD_ReichRifleman` |
| Faction | Fourth Reich |
| DoomEdNum | **21100** |
| Replaces | `ZombieMan` (3004) |
| Sprite | `SDRR` |
| Actor code (sounds) | `RRI` |
| LANGUAGE | `SD_TAG_RIFLEMAN`, `SD_OB_RIFLEMAN` |

**Why this faction.** `LORE.md` gives the Reich the infantry, the hounds and
the armoured brutes. The rifleman is the ground the player walks over.

**Colour.** `khaki_olive` greatcoat, black boots and webbing, Stahlhelm in
`khaki_olive` 2–5. The one saturated thing on him is the `flag_red` armband
with the black swastika (D12). Olive blood.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **20** | `ZombieMan` parity. This number sets the whole ammo economy: 20 HP is one TT-33 round pair, one PPSh burst, or a single shotgun pellet group. Change it and every ammo pickup in MAP01 is wrong. |
| `Radius`/`Height` | **20 × 56** | parity. Doom's corridor widths and doorway heights assume this; the `level-designer` builds on 64-unit grid against it. |
| `Speed` | **8** | parity. |
| `Mass` | **100** | parity — governs how far he is thrown by an RPG blast. |
| `PainChance` | **200** | parity (78 % chance per hit). High painchance is what makes the basic zombie *stunlockable*, which is how a Doom player safely opens a fight. |
| Attack | hitscan, `random(1,5) × 3` = 3–15, 1 shot | parity with `A_PosAttack`. |
| Accuracy spread | `±22.5/256 × random2()` ≈ ±1.4° | parity: a rifleman is Doom-accurate, i.e. deadly at range, which is the only reason low-HP infantry stays a threat. |
| `MeleeRange` | n/a (no melee) | parity. |
| Range | `MISSILERANGE` (2048 units) | parity. |
| `DropItem` | **`Clip`** | `ZombieMan` parity. ADR 002 kept Doom's four ammo pools (`Clip`, `Shell`, `RocketAmmo`, `Cell`), and the TT-33 and the PPSh both draw `Clip`, so the vanilla drop is already the right one. Lore reading in **Q4**: the invaders hold the Zarya-7 armoury and carry seized Soviet small arms. |

### States and sounds

| State | Frames | Sound event | Sound lump | Note for `sound-designer` |
|---|---|---|---|---|
| `Spawn` (idle/look) | `SDRR A B`, 10 tics, `A_Look` | `active` | `SDRRIACT` | muttered command in a language that is not quite German |
| `See` (walk) | `SDRR AABBCCDD`, 4 tics, `A_Chase` | `sight` | `SDRRISIT` | a bark, short; heard many times per map |
| `Missile` | `SDRR E` 10 `A_FaceTarget`, `F` 8 *attack*, `E` 8 | `attack` | `SDRRIATK` | dry bolt-action crack, drier than the player's TT-33 so the player can tell incoming from outgoing |
| `Pain` | `SDRR G` 3, `G` 3 `A_Pain` | `pain` | `SDRRIPAI` | |
| `Death` | `SDRR H I J K`, 5 tics, `L` −1 | `death` | `SDRRIDTH` | |
| `XDeath` | `SDRR M N O P Q R S T`, 5 tics, `U` −1 | `xdeath` | `SDRRIXDT` | gib; triggered when damage exceeds `GibHealth` |

7 sounds. Lump names are all exactly 8 characters.

### Sprites

| Group | Frames | Rotations | Images |
|---|---|---|---|
| Walk / idle | A B C D | 8 (mirrored → 5 drawings each) | 20 |
| Fire | E F | 8 | 10 |
| Pain | G | 8 | 5 |
| Death | H I J K L | 0 | 5 |
| Gib death | M–U (9) | 0 | 9 |
| **Total** | | | **49** |

Visual brief for `art-director`: *a gaunt field-grey infantryman in a
calf-length greatcoat, Stahlhelm pulled low over a face that has no eyes;
bolt-action rifle carried at the hip; a red armband is the only colour on
him.*

Freedoom derivation: `POSS` is a humanoid of the same proportions and the
same 21-frame layout, so it is a usable **animation reference**. NOT VERIFIED
whether its pixels are worth editing.

### Legibility

16-px silhouette: upright rectangle, flared helmet skirt widening the head,
the rifle a horizontal bar at waist height. **Distinct from the Legion
trooper only by value and weapon line, not by shape** — see §5.

---

## 4. Liberty Legion trooper — basic infantry (2 of 2)

| Field | Value |
|---|---|
| Class | `SD_LegionTrooper` |
| Faction | Liberty Legion |
| DoomEdNum | **21101** |
| Replaces | `ShotgunGuy` (9) |
| Sprite | `SDLT` |
| Actor code | `LTR` |
| LANGUAGE | `SD_TAG_TROOPER`, `SD_OB_TROOPER` |

**Why this faction.** The Legion is the ranged, chrome, officer side; the
shotgunner is the first unit whose damage the player must respect at
distance.

**Colour.** Pink flesh forearms and face, chrome cuirass and M1 helmet in
`steel_blue` 11–15, `steel_blue` 0–5 for the shadow side. US-flag patch on
the shoulder (D12) is the only `flag_red` on him.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **30** | `ShotgunGuy` parity. 30 HP is the Doom breakpoint that survives exactly one TT-33 round and dies to one shotgun hit; the whole "trade shells for shells" exchange depends on it. |
| `Radius`/`Height` | **20 × 56** | parity. |
| `Speed` | **8** | parity. |
| `PainChance` | **170** | parity (66 %). Deliberately lower than the rifleman: he is harder to stunlock, which is what makes him the one you shoot first. |
| Attack | **3** hitscans, `random(1,5) × 3` each = 9–45 | parity with `A_SPosAttackInternal`. At point blank this one-shots a 40 HP player start; it is the reason Doom players learn to use corners. |
| Spread | ±1.4° per pellet, all on one aim slope | parity. |
| `DropItem` | **`SD_Izh`** | parity with `ShotgunGuy` dropping a `Shotgun`. Because `SD_Izh replaces Shotgun` (ADR 002), writing either class name works; naming ours is clearer. Same armoury reading as **Q4**. |

### States and sounds

Same state layout as §3 with sprite `SDLT` and lumps `SDLTRSIT`, `SDLTRACT`,
`SDLTRATK`, `SDLTRPAI`, `SDLTRDTH`, `SDLTRXDT`. 6 sounds (no separate idle
bark is strictly needed, but one is listed so the two factions sound
different in an ambush).

Brief for `sound-designer`: the Legion's voice is **processed and clipped** —
radio squelch, a vocoder edge — against the Reich's dry organic bark. The
player must be able to name the faction behind a door with the lights off.

### Sprites

Identical budget to §3: **49 images**. The rig is the same humanoid; the
drawing is not shared, but the pose sheet and timing are.

Visual brief: *a heavy-shouldered trooper in a chromed breastplate over pink,
too-smooth flesh; round M1 helmet; a short pump shotgun held high across the
chest; a small star-spangled patch on the shoulder.*

Freedoom derivation: `SPOS` is the same layout. NOT VERIFIED.

### Legibility

16-px silhouette: upright, wider at the shoulders than the rifleman, round
helmet, weapon held **high** (chest) rather than at the hip. Light value mass.

---

## 5. Hybrid Stormtrooper — ranged skirmisher

| Field | Value |
|---|---|
| Class | `SD_Stormtrooper` |
| Faction | **both** — the alliance made flesh |
| DoomEdNum | **21102** |
| Replaces | `DoomImp` (3001) |
| Sprite | `SDHS`; projectile sprite `SDBL` |
| Actor code | `STO` |
| LANGUAGE | `SD_TAG_STORM`, `SD_OB_STORM`, `SD_OBHIT_STORM` |

**Why this faction.** The bestiary calls it a *hybrid*, and the lore's one
unexplained fact is why these two factions march together. This unit is the
answer made visible: a Reich body with Legion hardware grafted into it. It is
the only actor allowed to wear both palettes.

**Colour.** Body mass `khaki_olive` + black (Reich, dark). The grafted right
arm and the weapon fused to it are `steel_blue` chrome with pink flesh at the
seam (Legion, light). That asymmetry is deliberate: the bright mass is on one
side only, which is also the silhouette tell.

**Legibility risk, stated plainly:** two palettes on one 40-px-tall body is
exactly what ART-BIBLE §6.2 warns against. It works only if the Legion
material is confined to one limb (≤ 25 % of body area) and the body mass
stays Reich-dark. If `art-director` cannot hold that, the honest fallback is
to make the Stormtrooper purely Reich and move the hybrid idea to a later
unit. Flagged, not hidden.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **60** | `DoomImp` parity. 60 is the classic "two pistol clips or one shotgun blast" wall; it is the unit that teaches the player the shotgun's value. |
| `Radius`/`Height` | **20 × 56** | parity. |
| `Speed` | **8** | parity. |
| `Mass` | **100** | parity. |
| `PainChance` | **200** | parity. |
| Melee | `random(1,8) × 3` = 3–24 | parity with `A_TroopAttack`. |
| Missile | `SD_StormBolt`, `Damage 3` → `random(1,8) × 3` | parity with `DoomImpBall`. |
| Projectile speed | **10** (`FastSpeed 20`) | parity. Doom's dodgeable-fireball speed is a tuned constant; faster and the imp becomes a hitscanner, slower and it is free experience. |
| Projectile size | 6 × 8 | parity. |
| `MinMissileChance` | default | parity. |

`SD_StormBolt` is a separate actor (`Projectile; +RANDOMIZE; RenderStyle
"Add"`), sprite `SDBL`, frames `AB` spawn + `CDE` death, all `BRIGHT`.
Colour: a **pale chrome-white bolt with a red core** — Legion technology,
Reich ammunition — rendered additively so it never disappears against the
grey of `SDCONC1`. 2 + 3 = 5 images, rotation 0.

### States and sounds

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDHS A B` 10 `A_Look` | `active` | `SDSTOACT` |
| `See` | `SDHS AABBCCDD` 3 `A_Chase` | `sight` | `SDSTOSIT` |
| `Melee` / `Missile` | `SDHS E F` 8 `A_FaceTarget`, `G` 6 *attack* | melee hit | `SDSTOMEL` |
| | | missile launch (on the bolt's `SeeSound`) | `SDSTOMIS` |
| | | bolt impact (bolt's `DeathSound`) | `SDSTOEXP` |
| `Pain` | `SDHS H` 2, `H` 2 `A_Pain` | `pain` | `SDSTOPAI` |
| `Death` | `SDHS I J K L` 8, `M` −1 | `death` | `SDSTODTH` |
| `XDeath` | `SDHS N O P Q R` 5, `S` −1 | `xdeath` | `SDSTOXDT` |

8 sounds. Note the bolt owns two of them.

### Sprites

| Group | Frames | Rot | Images |
|---|---|---|---|
| Walk | A B C D | 8 | 20 |
| Attack | E F G | 8 | 15 |
| Pain | H | 8 | 5 |
| Death | I–M (5) | 0 | 5 |
| Gib | N–S (6) | 0 | 6 |
| **Total** | | | **51** + 5 bolt |

Visual brief: *a hunched soldier whose right arm has been replaced below the
shoulder by a chromed emitter; the graft is raw, pink flesh at the seam; the
left half is still a Reich greatcoat. He walks lopsided.*

Freedoom derivation: Freedoom's `TROO` is, as far as `mod-engineer` knows, a
**non-humanoid** creature, which would make it a poor base for a humanoid
hybrid. **NOT VERIFIED** — `art-director` must look before planning on it.
Assume from scratch.

### Legibility

16-px silhouette: asymmetric and top-heavy — one shoulder a bright blob, the
other a dark slope. This is the only enemy whose silhouette is
*unbalanced*, which makes it the easiest of the humanoids to name at range.

---

## 6. Reich hound — fast melee

| Field | Value |
|---|---|
| Class | `SD_ReichHound` |
| Faction | Fourth Reich |
| DoomEdNum | **21103** |
| Replaces | `Demon` (3002) |
| Sprite | `SDHN` |
| Actor code | `HND` |
| LANGUAGE | `SD_TAG_HOUND`, `SD_OB_HOUND` |

**Why this faction.** `LORE.md` assigns the hounds to the Reich. A hound is
also the right unit to be *organic* while the Legion is chrome.

**Colour.** `khaki_olive` 4–10 hide, black underbelly and muzzle, black claw
tips. **No red accent at all** — the hound is the one enemy with no faction
insignia, because a dog does not wear an armband, and because it gives the
level designer one enemy that will never be camouflaged against a poster.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **150** | `Demon` parity. Kept exactly, because 150 is the number that makes a pinky cost two shotgun blasts; it is the main consumer of shells in early Doom and our MAP01 shell budget is built on it. |
| `Radius`/`Height` | **30 × 56** | parity. The wide radius is why pinkies block corridors — that is a *feature* the level designer uses. |
| `Speed` | **12** **(H)** | +20 % over the pinky's 10. The bestiary says "fast melee" and the hound must feel different from a shambling pinky. 12 is chosen rather than 14 because a melee-only monster faster than the player's forward run (≈ 16 units/tic equivalent) cannot be outrun in a corridor, which turns every hound into a guaranteed 4–40 damage tax. **Calibration lever: drop to 10 if MAP01 playtest shows corridors are unwinnable without the shovel.** |
| `Mass` | **400** | parity. |
| `PainChance` | **180** | parity. |
| Melee | `random(1,10) × 4` = 4–40 | parity with `A_SargAttack`. |
| `MeleeRange` | **64** (engine default) | parity; a longer lunge range was considered and rejected — it reads as "the bite missed but hurt me", which players correctly call unfair. |
| Blood | olive | §2.1 |

**Spectre note.** Doom's `Spectre` (DoomEdNum **58**) is a separate class.
We do not replace it in v1, so a map that places thing 58 would spawn a
Freedoom spectre. **Rule for `level-designer`: thing 58 is forbidden in Soviet
Doom maps.** A cloaked variant (`+SHADOW`, same sprites, DoomEdNum 21108) is
nearly free and can be added later.

### States and sounds

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDHN A B` 10 `A_Look` | `active` | `SDHNDACT` |
| `See` | `SDHN AABBCCDD` 2 `A_Chase` | `sight` | `SDHNDSIT` |
| `Melee` | `SDHN E F` 8 `A_FaceTarget`, `G` 8 *attack* | `attack` | `SDHNDATK` |
| `Pain` | `SDHN H` 2, `H` 2 `A_Pain` | `pain` | `SDHNDPAI` |
| `Death` | `SDHN I J K L M` 8, `N` −1 | `death` | `SDHNDDTH` |
| `XDeath` | — | — | — |

6 sounds. No gib death: Doom's pinky has none either, and 6 extra rotationless
frames bought nothing. `art-director` may add one later without touching the
class (the engine falls back to `Death`).

Brief for `sound-designer`: the hound's `sight` is the most important sound in
the mod after the shotgun. It must be audible through a closed door and must
not be a wolf sample — these are not animals from Earth.

### Sprites

| Group | Frames | Rot | Images |
|---|---|---|---|
| Walk | A B C D | 8 | 20 |
| Bite | E F G | 8 | 15 |
| Pain | H | 8 | 5 |
| Death | I–N (6) | 0 | 6 |
| **Total** | | | **46** |

Visual brief: *a low, long quadruped the size of a large dog, hairless olive
hide stretched over visible ribs, a flat head that is mostly jaw, no eyes. It
runs with its spine low.*

Freedoom derivation: `SARG`. **NOT VERIFIED** whether Freedoom's demon
replacement is quadruped or bipedal; if bipedal, there is no base and this is
from scratch.

### Legibility

16-px silhouette: a **horizontal** bar under 40 units tall when every other
enemy is a vertical one. It is the most legible unit in the bestiary and
should therefore be the one the level designer uses in the dark.

---

## 7. Doughboy — floating head

| Field | Value |
|---|---|
| Class | `SD_Doughboy` |
| Faction | Liberty Legion |
| DoomEdNum | **21104** |
| Replaces | `Cacodemon` (3005) |
| Sprite | `SDDB`; projectile `SDDL` |
| Actor code | `DGB` |
| LANGUAGE | `SD_TAG_DOUGHBOY`, `SD_OB_DOUGHBOY`, `SD_OBHIT_DOUGHBOY` |

**Why this faction.** The M1 helmet is the unit's whole identity (D13), and
`LORE.md` gives the Legion the floating heads. "Doughboy" is the US infantry
nickname of 1917 — the joke is that the thing kept the helmet and lost the
body. Serious tone (D11) is preserved because the result is grotesque, not
funny.

**Colour.** Pink flesh sphere, `steel_blue` 2–6 helmet (dark, on top),
`steel_blue` 12–15 rim highlight, a single small US-flag decal on the helmet
(D12). The dark helmet on top of a light body is the silhouette plan.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **400** | `Cacodemon` parity. 400 is "two rockets or a sustained PPSh burst"; it is the first enemy that makes the player commit ammunition, and the hangar fight in MAP01 is sized around that cost. |
| `Radius`/`Height` | **31 × 56** | parity. The 31 radius is famously one unit wider than everything else and is what makes cacodemons jam in doorways; the `level-designer` should keep flight lanes ≥ 96 units wide. |
| `Speed` | **8** | parity. |
| `Mass` | **400** | parity. |
| `PainChance` | **128** | parity (50 %). |
| Flags | `+FLOAT +NOGRAVITY` | parity — it flies, and it will drift to the player's altitude. |
| Melee | `random(1,6) × 10` = 10–60 | parity with `A_HeadAttack`. |
| Missile | `SD_DoughboyShell`, `Damage 5` → `random(1,8) × 5` = 5–40 | parity with `CacodemonBall`. |
| Projectile speed | 10 (`FastSpeed 20`) | parity. |

`SD_DoughboyShell`: sprite `SDDL`, 2 spawn + 3 death frames, additive,
**`steel_blue` white-hot core with a `flag_red` trail** — it must not be the
same colour as the Stormtrooper's bolt, because the player's correct reaction
to each is different (dodge sideways vs. break line of sight).

### States and sounds

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDDB A` 10 `A_Look` | `active` | `SDDGBACT` |
| `See` | `SDDB A` 3 `A_Chase` | `sight` | `SDDGBSIT` |
| `Missile` | `SDDB B` 5 `A_FaceTarget`, `C` 5 `A_FaceTarget`, `D` 5 *attack* | melee | `SDDGBMEL` |
| | | launch (projectile `SeeSound`) | `SDDGBMIS` |
| | | impact (projectile `DeathSound`) | `SDDGBEXP` |
| `Pain` | `SDDB E` 3, `E` 3 `A_Pain`, `F` 6 | `pain` | `SDDGBPAI` |
| `Death` | `SDDB G H I J` 8, `K` 8 `A_SetFloorClip`, `L` −1 | `death` | `SDDGBDTH` |

8 sounds. The death animation must *deflate and sink* (clear `+NOGRAVITY` in
the death state as Doom does), otherwise the corpse hangs in the air.

### Sprites

| Group | Frames | Rot | Images |
|---|---|---|---|
| Float / chase | A | 8 | 5 |
| Attack | B C D | 8 | 15 |
| Pain | E F | 8 | 10 |
| Death | G–L (6) | 0 | 6 |
| **Total** | | | **36** + 5 projectile |

**The cheapest enemy in the bestiary** — a one-frame float cycle is Doom's own
trick. Worth knowing when F5 is scheduled.

Visual brief: *a pink, veined sphere of flesh the size of a man's torso, one
huge lidless eye, a slack mouth underneath; a battered steel M1 helmet
strapped onto the top with a chinstrap that goes nowhere. It bobs.*

Freedoom derivation: `HEAD` is a floating round creature of the same
dimensions — on paper the **best derivation candidate** in the set, because
the body is a sphere and the work is the helmet. **NOT VERIFIED.**

### Legibility

16-px silhouette: a circle with a flat notch on top. No legs, no arms, so it
cannot be confused with anything else even as a 10-px blob. The risk is not
shape but **ground**: see §8.

---

## 8. Panzermensch — armoured brute

| Field | Value |
|---|---|
| Class | `SD_Panzermensch` |
| Faction | Fourth Reich |
| DoomEdNum | **21105** |
| Replaces | `HellKnight` (69) |
| Sprite | `SDPM`; projectile `SDPL` |
| Actor code | `PZR` |
| LANGUAGE | `SD_TAG_PANZER`, `SD_OB_PANZER`, `SD_OBHIT_PANZER` |

**Why this faction.** Armoured brutes are the Reich's in `LORE.md`, and the
name is German.

**Colour.** Black-painted plate armour over `khaki_olive` flesh at the joints,
`khaki_olive` 1–4 for the darkest shadow. A `flag_red` banner panel on the
back carries the swastika (D12) — visible when he turns away, which is the
moment the player is supposed to notice he is in a fight.

### The deviation from D13, stated openly

D13 calls the Panzermensch "baron". A `BaronOfHell` has **1000 HP**. Doom II
puts its first Hell Knight in MAP03 and its first Baron in MAP08; Soviet Doom
v1 is **one map**. A 1000 HP brute in MAP01 costs roughly 5 RPG-7 hits or 48
PPSh rounds — twenty-plus seconds of holding a trigger, which is not a fight,
it is a wall.

**Decision: `SD_Panzermensch` ships at Hell Knight numbers (500 HP) and
`replaces HellKnight`.** The Baron slot stays free for a heavier variant,
`SD_PanzermenschSchwer` (1000 HP, `replaces BaronOfHell`, DoomEdNum **21107**
reserved), which is a translation swap and two extra frames over the same
sprite set — it costs almost nothing and belongs to MAP03. This honours "the
Panzermensch is the baron-tier enemy" while keeping MAP01 playable.
Open question **Q2**.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **500** | `HellKnight` parity; see above. |
| `Radius`/`Height` | **24 × 64** | parity. The 64 height is the one that does **not** fit under a 56-unit lintel: the `level-designer` must keep brute arenas at ≥ 72 units clear. |
| `Speed` | **8** | parity. Brutes are slow in Doom so the player can kite; this is the mechanic that makes 500 HP survivable. |
| `Mass` | **1000** | parity — an RPG-7 barely moves him. |
| `PainChance` | **50** | parity (20 %). Low painchance is what stops the player from stunlocking him with the PPSh and is therefore the actual difficulty, more than the HP. |
| Melee | `random(1,8) × 10` = 10–80 | parity with `A_BruisAttack`. |
| Missile | `SD_PanzerShell`, `Damage 8` → `random(1,8) × 8` = 8–64 | parity with `BaronBall`. |
| Projectile speed | **15** (`FastSpeed 20`) | parity. Faster than the imp/caco balls — that difference is how a Doom player reads threat level from the projectile alone. |
| Projectile size | 6 × 16 | parity. |

`SD_PanzerShell`: sprite `SDPL`, 2 + 3 frames, additive, **dull
`hazard_yellow` core with an olive smoke edge** — Reich ordnance, visually
heavier and slower-tumbling than the Stormtrooper bolt.

### States and sounds

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDPM A B` 10 `A_Look` | `active` | `SDPZRACT` |
| `See` | `SDPM AABBCCDD` 3 `A_Chase` | `sight` | `SDPZRSIT` |
| `Melee` / `Missile` | `SDPM E F` 8 `A_FaceTarget`, `G` 8 *attack* | melee | `SDPZRMEL` |
| | | launch | `SDPZRMIS` |
| | | impact | `SDPZREXP` |
| `Pain` | `SDPM H` 2, `H` 2 `A_Pain` | `pain` | `SDPZRPAI` |
| `Death` | `SDPM I J K L M N` 8, `O` −1 | `death` | `SDPZRDTH` |
| | plus a **footstep** every See cycle **(H)** | `step` | `SDPZRSTP` |

9 sounds. The footstep is the cheapest possible "boss is coming" telegraph and
costs one `A_StartSound` in the `See` state. Marked **(H)**: cut it if it
turns into noise.

No `XDeath`: Doom's bruisers do not gib, and a 1000-mass armoured unit that
bursts reads wrong.

### Sprites

| Group | Frames | Rot | Images |
|---|---|---|---|
| Walk | A B C D | 8 | 20 |
| Attack | E F G | 8 | 15 |
| Pain | H | 8 | 5 |
| Death | I–O (7) | 0 | 7 |
| **Total** | | | **47** + 5 projectile |

Visual brief: *a man-shaped slab of riveted black plate two heads taller than
a rifleman, arms ending in gauntlets too big for them, no face behind the
visor slit, a red banner panel bolted to his back. He does not run.*

Freedoom derivation: `BOSS`/`BOS2` are humanoid brutes of the same height
class and the same frame layout. **NOT VERIFIED.**

### Legibility

16-px silhouette: the widest vertical mass in the game — a rectangle with
shoulder horns. The problem is not shape, it is **value**: he is the darkest
thing in the mod. See rule 3 of the legibility matrix (§10).

---

## 9. The General — episode boss

| Field | Value |
|---|---|
| Class | `SD_General` |
| Faction | Liberty Legion (commanding both) |
| DoomEdNum | **21106** |
| Replaces | `Cyberdemon` (16) |
| Sprite | `SDGN`; projectile `SDGL` |
| Actor code | `GEN` |
| LANGUAGE | `SD_TAG_GENERAL`, `SD_OB_GENERAL` |
| **Scope** | **MAP03 only — not implemented in v1.** Specified here so F5's design is complete and so `art-director` can plan. |

**Why this faction.** `LORE.md` gives the Legion the officers. Making the
alliance's commander the *Yankee* one is also the lore's point: the Reich
supplies the bodies, the Legion supplies the capital.

**Colour.** `steel_blue` chromed dress armour over a `plaster_warm` greatcoat,
pink flesh at the throat, `hazard_yellow` braid. Both a swastika and a US
flag hang from his shoulders (D12) — he is the only actor that wears both
insignia, because he is the alliance.

### Stats

All **(H)** — there is no Doom equivalent to argue from and no MAP03 to test
in.

| Property | Value | Why |
|---|---|---|
| `Health` | **3000 (H)** | Between `SpiderMastermind` (3000) and `Cyberdemon` (4000). Below the Cyberdemon because our heaviest weapon, the hand Katyusha, is an unknown quantity until F4 closes, and because a boss that outlasts the player's entire ammo reserve is a reload-and-retry, not a fight. |
| `Radius`/`Height` | **40 × 100 (H)** | Cyberdemon radius (fits a 128-wide door) but 10 units shorter, so a 112-unit ceiling clears him. MAP03 must be built for this. |
| `Speed` | **12 (H)** | Slower than the Cyberdemon's 16: he is an officer in a greatcoat, and the arena fight needs the player able to circle. |
| `Mass` | **1000** | Cyberdemon parity: unmovable. |
| `PainChance` | **20** | Cyberdemon parity. Effectively unstunnable, which is the definition of a boss in Doom. |
| Flags | `+BOSS +NORADIUSDMG +BOSSDEATH +FLOORCLIP` | `+NORADIUSDMG` so the player's own RPG-7 splash does not do the work; `+BOSSDEATH` so MAP03's exit can be tied to his death. |
| Salvo | 3 × `SD_GeneralShell`, `Damage 8` → 8–64 each | A three-shot salvo is the Cyberdemon's own rhythm (the thing that makes Doom's best fight work) but with a dodgeable projectile instead of a rocket. |
| Projectile speed | **20 (H)** | Fast enough to punish standing still, slow enough to sidestep at 20 metres. |

### The open design question (Q3)

Two shapes for this fight; the CEO decides.

**A — brute with more health.** The General is a Panzermensch with 3000 HP
and a salvo. Cost: ~58 sprites, ~8 sounds, ~1 day of ZScript. Risk: in a mod
with exactly one boss, "more HP" is a long shotgun session.

**B — boss with one own verb (recommended).** Everything in A, plus a single
mechanic: below 50 % health he enters a `Summon` state that spawns two
`SD_ReichRecruit` at marked spots and shouts an order. One extra state, two
extra frames, one `A_SpawnItemEx` call, one sound. Cost over A: ~10 sprites,
1 sound, half a day. Gain: the fight has two halves and the arena's shape
starts to matter. It also pays off the lore — the General does not fight, he
*orders*.

`mod-engineer` recommends **B**. Anything larger (phase changes, invulnerable
shields, scripted arenas) is out of proportion for a three-map episode and
would be its own ADR.

### States, sounds, sprites

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDGN A B` 10 `A_Look` | `active` | `SDGENACT` |
| `See` | `SDGN AABBCCDD` 3 `A_Chase` | `sight` | `SDGENSIT` |
| `Missile` | `SDGN E` 12 `A_FaceTarget`, `F G` 12 *salvo ×3* | launch | `SDGENMIS` |
| | | impact | `SDGENEXP` |
| `Summon` (option B) | `SDGN H I` 15 | order | `SDGENSUM` |
| `Pain` | `SDGN J` 10 `A_Pain` | `pain` | `SDGENPAI` |
| `Death` | `SDGN K L M N O P Q` 10, `R` −1 | `death` | `SDGENDTH` |

8 sounds. The `death` lump is the last sound in the episode; `sound-designer`
should treat it as a cue, not an effect.

Sprites: walk 4×5 = 20, salvo 3×5 = 15, summon 2×5 = 10, pain 1×5 = 5,
death 8 = **58 images** + 5 projectile.

Visual brief: *tall and unhurried, a chromed cuirass over a pale greatcoat
that flares at the knee; a peaked cap with too much braid; the face is a
smooth chrome plate with a single slot. A swastika pennant on one shoulder, a
star-spangled one on the other.*

Freedoom derivation: none — from scratch.

### Legibility

16-px silhouette: the tallest figure in the game, with a coat flare at the
bottom and a peaked-cap wedge on top — an hourglass, unlike every other
enemy's rectangle. Bright value, which is correct: he must be visible across
a factory floor.

---

## 10. Legibility matrix against the "Soviet base" set

Textures as of the F2 verdict (`docs/art/TEXTURE-INDEX.md`): approved
`SDCONC1`, `SDSTEL1`, `SDDOOR1`, `SDPOSTR2`, `SDFLR1`, `SDFLR2`, `SDFLR3`,
`SDCEIL1`, `SDCEIL2`; pending `SDCONC2`, `SDSTAR1`.

Legend: **OK** · **caution** (works if the stated condition holds) ·
**BAD** (do not place this fight here).

| Enemy | `SDCONC1` grey wall | `SDSTEL1` green steel | `SDDOOR1` green door | `SDPOSTR2` red mural | `SDFLR1/2` concrete floor | `SDFLR3` grey tiles |
|---|---|---|---|---|---|---|
| Reich rifleman | OK (value 0.38 vs 0.58) | **caution** | **caution** | OK | OK | OK |
| Legion trooper | OK (0.75 vs 0.58) | OK | OK | **BAD** | OK | OK |
| Stormtrooper | OK | **caution** | **caution** | OK | OK | OK |
| Reich hound | OK | **caution** | OK | OK | **caution** (`SDFLR1`) | OK |
| Doughboy | OK | OK | OK | **BAD** | n/a (flies) | n/a |
| Panzermensch | **caution** | OK | OK | OK | OK | OK |
| The General | OK | OK | OK | **caution** | OK | OK |

Conditions and rules, for `level-designer`:

1. **Reich units on green steel.** `khaki_olive` and `military_green` are
   adjacent hues and both sit mid-dark. They separate by value and by the
   black undercoat — but only above sector light **112**. *Rule: no Reich
   ambush in a space walled mainly in `SDSTEL1` at light ≤ 112.*
2. **Legion units on the mural.** Pink flesh on `flag_red` ground is the worst
   pairing in the mod, and it also kills the US-flag accent, violating
   ART-BIBLE §6.3 (accent exclusivity). *Rule: `SDPOSTR2` never forms the
   backdrop of a Legion fight; put it on a wall the player faces while
   **leaving** a cleared room.* Same applies to the `SDSTAR1` plaque once it is
   approved.
3. **Panzermensch in the dark.** He is the darkest mass in the game. At the
   night-exterior light of 96–128 proposed in ART-BIBLE §4 he disappears
   against `SDCONC1`. *Rule: wherever a Panzermensch fights, sector light
   ≥ 128, or there is a `flag_red`/`hazard_yellow` light source behind him.*
   The red back banner is the mitigation of last resort and only helps when he
   turns.
4. **Hound over the lane line.** `SDFLR1`'s `hazard_yellow` line is a
   mid-value warm stripe and the hound is a mid-value warm quadruped seen
   mostly against the floor. *Rule: the lane line does not run through a hound
   ambush zone; or `art-director` gives the hound a true-black underbelly so
   its bottom edge always reads.*
5. **Doughboy under lamps.** A pink sphere against the bright `SDCEIL1` lamp
   flat loses its top edge — which is why the **helmet is dark and on top**.
   This is a design requirement on the sprite, not a map rule.
6. **Tile grain.** `SDFLR3`'s grout is an 8-px pattern; ART-BIBLE §6.4 caps
   wall detail below the 16-px silhouette scale and this complies. No issue.

### The one real silhouette collision

**Reich rifleman vs. Legion trooper.** Both are 56-unit upright humanoids. At
16 px the helmet difference (flared skirt vs. round bowl) is about 2 pixels —
not enough. They are separated by:

- **value** — dark khaki vs. light pink/chrome (the primary tell, and the one
  that survives low light);
- **weapon line** — rifle horizontal at the hip vs. shotgun high across the
  chest;
- **shoulder width** — the trooper's cuirass is visibly wider.

`art-director`: if a 16-px value test ever shows the two reading the same,
the fix is to push the trooper lighter, not to redraw helmets.

---

## 11. Implementation order and first appearance

Order is chosen so each step adds exactly one new engine capability, and so
the first step is the one that proves the whole monster pipeline (sprite
naming, `SNDINFO`, `DoomEdNum`, death, `LANGUAGE`, obituary) end to end.

| # | Class | New capability it proves | First map | Count in MAP01 **(H)** |
|---|---|---|---|---|
| 1 | `SD_Monster` base + `SD_ReichRifleman` | the entire monster pipeline; `replaces`; hitscan | MAP01 | 12–18 |
| 2 | `SD_LegionTrooper` | second faction reads apart; multi-hitscan | MAP01 | 6–9 |
| 3 | `SD_Stormtrooper` + `SD_StormBolt` | first projectile actor; melee/missile combo | MAP01 | 8–12 |
| 4 | `SD_ReichHound` | melee-only AI; non-humanoid silhouette | MAP01 | 4–6 |
| 5 | `SD_Doughboy` + `SD_DoughboyShell` | `+FLOAT +NOGRAVITY`; a corpse that sinks | MAP01 hangar | 1–2 |
| 6 | `SD_Panzermensch` + `SD_PanzerShell` | brute pacing; low painchance; `BOSSDEATH`-adjacent | MAP01 finale | 1 |
| 7 | `SD_General` + `SD_GeneralShell` | boss flags, `+BOSSDEATH`, summon state | **MAP03** | 0 |

Five of the six bestiary entries therefore appear in v1's single map, which
satisfies the "less to more: every delivery is playable or visible" rule.
The Doughboy is placed in the hangar specifically because it is MAP01's only
space with vertical room, and the Panzermensch gates the exit.

Counts are hypotheses for the `level-designer` to own; they are listed only so
F5 and F3 can be planned against the same assumption.

---

## 12. Summary table

| # | Name | Class | Faction | EdNum | Replaces | HP | Spd | Pain | Attack | Sprite | Images | Sounds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Reich rifleman | `SD_ReichRifleman` | Reich | 21100 | `ZombieMan` | 20 | 8 | 200 | hitscan 3–15 | `SDRR` | 49 | 7 |
| 2 | Legion trooper | `SD_LegionTrooper` | Legion | 21101 | `ShotgunGuy` | 30 | 8 | 170 | 3× hitscan 3–15 | `SDLT` | 49 | 6 |
| 3 | Hybrid Stormtrooper | `SD_Stormtrooper` | both | 21102 | `DoomImp` | 60 | 8 | 200 | melee 3–24 / bolt 3–24 | `SDHS` `SDBL` | 56 | 8 |
| 4 | Reich hound | `SD_ReichHound` | Reich | 21103 | `Demon` | 150 | **12 (H)** | 180 | melee 4–40 | `SDHN` | 46 | 6 |
| 5 | Doughboy | `SD_Doughboy` | Legion | 21104 | `Cacodemon` | 400 | 8 | 128 | melee 10–60 / shell 5–40 | `SDDB` `SDDL` | 41 | 8 |
| 6 | Panzermensch | `SD_Panzermensch` | Reich | 21105 | `HellKnight` | **500** | 8 | 50 | melee 10–80 / shell 8–64 | `SDPM` `SDPL` | 52 | 9 |
| 7 | The General | `SD_General` | Legion | 21106 | `Cyberdemon` | **3000 (H)** | 12 | 20 | 3× shell 8–64 | `SDGN` `SDGL` | 63 | 8 |
| — | *heavy Panzermensch* | `SD_PanzermenschSchwer` | Reich | *21107 reserved* | `BaronOfHell` | 1000 | 8 | 50 | as #6 | `SDPM` recolour | +2 | 0 |
| — | *cloaked hound* | *reserved* | Reich | *21108 reserved* | `Spectre` | 150 | 12 | 180 | as #4 | `SDHN` `+SHADOW` | 0 | 0 |

Totals for F5: **7 classes + 4 projectile actors, ≈ 356 sprite images,
52 sound lumps.**

---

## 13. What other documents must change

`mod-engineer` owns only this file in this task. These are the amendments the
owners of the other documents must make before implementation starts.

| Document | Change | Owner |
|---|---|---|
| `docs/engine/MOD-SPEC.md` §6.1 | Add the nine bestiary numbers to the `21100–21199` enemy sub-range table (21100–21106 the seven classes, 21107–21108 reserved variants). No range change: ADR 002 already fixed the 14000 collision. | `mod-engineer` (MOD-SPEC) |
| `docs/engine/MOD-SPEC.md` §2, §3, §6, §6.2, §6.3 | Add `src/zscript/monsters/` → `zscript/monsters/` to both layouts; add the eleven bestiary sprite prefixes to the §6.3 reserved table and the 52 sound lumps to the §6.2 table; list the monster classes in the §6 class table. | idem |
| `docs/engine/MOD-SPEC.md` §5 | `MAP02`'s Freedoom test fixtures include thing **3004** (zombieman). Once `SD_ReichRifleman replaces ZombieMan` lands, that fixture silently becomes a Soviet rifleman. That is the correct outcome, but the §5 note calling it a Freedoom placeholder stops being true and should say so. | idem |
| `docs/engine/BALANCE.md` | Should **link here** rather than copy: this file is the source of truth for enemy numbers, BALANCE.md for weapon numbers and the ammo economy that connects them. | `mod-engineer` (arsenal) |
| `docs/art/ART-BIBLE.md` §3 | The **pink/flesh ramp** reserved for the Liberty Legion must be added as `palette.json` **v2** before any Legion sprite is drawn; §6 should absorb the six map rules of §10 above. | `art-director` |
| `docs/art/TEXTURE-INDEX.md` | Sprites are not textures, but the F5 sprite sheets need their own index with the same origin/licence columns. | `art-director` |
| `src/lumps/LANGUAGE` | 7 `SD_TAG_*`, 7 `SD_OB_*`, 4 `SD_OBHIT_*` ids, `[enu default]` and `[ru]` (D7). | `mod-engineer` (arsenal owns the file today) |
| `docs/art/LICENSES.md` | If any Freedoom pixels ship, the BSD-3 notice, disclaimer and no-endorsement clause must be reproduced. | `qa-engineer` audit |
| `docs/engine/adr/003-*.md` | **ADR 003 — "Enemies derive from `Actor`, not from the Doom monsters"**: context (§2.4), options (derive from Doom monsters / derive from `Actor` / DECORATE), decision, consequences (every state must be written out; no inherited IWAD sprites or sounds; deliberate divergence from ADR 002's choice for weapons, §2.4). To be written when implementation starts. | `mod-engineer` |

---

## 14. Open questions for the CEO

| # | Question | What `mod-engineer` recommends |
|---|---|---|
| **Q1** | **Names.** The ratified names are provisional (D13). Proposed finals: *Reich rifleman* (Rus. «стрелок Рейха»), *Legion trooper* («легионер»), *Hybrid Stormtrooper* («штурмовик-гибрид»), *Reich hound* («гончая Рейха»), *Doughboy* («Каска» / «Doughboy»?), *Panzermensch*, *the General* («Генерал»). Two sub-questions: (a) is "Doughboy" readable to a Russian-speaking player, or does it need a Russian name of its own? (b) should the basic infantry be **one** name covering two classes, or two names? | Two names. The player must be able to say "the pink ones shoot harder". |
| **Q2** | **Panzermensch tier.** D13 says "baron" (1000 HP). I propose shipping it at Hell Knight numbers (**500 HP**) so MAP01 is a fight and not a wall, and reserving a 1000 HP heavy variant for MAP03. Accept, or hold the Baron numbers? | 500 in MAP01, 1000 variant in MAP03. |
| **Q3** | **Is the General a boss or a big brute?** Option A = more HP and a salvo. Option B = A plus one mechanic (below half health he summons two recruits and shouts an order), costing about half a day and 10 sprites more. | **B.** One verb is enough to make the fight a fight, and it pays off the lore: the General orders, he does not brawl. |
| **Q4** | **What do enemies drop?** The clean solution is that the invaders hold the Zarya-7 armoury and carry **seized Soviet small arms**, so a dead rifleman drops PPSh ammunition and a dead trooper drops the IZh. This is one sentence of lore and it saves inventing a second arsenal. Accept? | Accept. The alternative — alien weapons the player cannot use — means enemies drop nothing, which starves MAP01. |
| **Q5** | **Infighting.** Doom lets monsters fight each other when they hit each other by accident; it is one of the game's best tactics. Our two factions are *allies*. Keep vanilla infighting (and read it as "an alliance of convenience"), or suppress it between the factions? | Keep it. Suppressing it would remove a core Doom verb to protect a lore detail that the lore itself already undercuts. |
| **Q6** | **Freedoom sprites.** Freedoom's monsters are BSD-3 licensed and legally reusable with attribution. Using them as a base would cut F5's ~356 drawings substantially, but a recoloured Freedoom monster still looks like Freedoom, and the mod's identity is the product. Reference only, or ship edited Freedoom pixels where they fit? | Reference only for the five enemies the player sees most; edited Freedoom acceptable for gib and death frames, which play for 1 second and are drawn from a single angle. `art-director` has the final say. |
| **Q7** | **Does one faction dominate MAP01?** Zarya-7 is the first landing. Proposal: MAP01 is **Reich-heavy** (they are the infantry, the boots on the ground) with the Legion appearing as the units that hold the hangar — so the player meets the Reich first and learns there is a second enemy halfway through the map. MAP02 inverts it; MAP03 mixes. | Reich-heavy MAP01. It gives the map a dramatic turn at no cost. |

---

*Verification note (CLAUDE.md radical honesty).* Verified in this task:
GZDoom 4.14.2 actor stats and the `extend class Actor` attack functions
(read from the installed `gzdoom.pk3`); the editor-number collision at
14001–14165 and the free gaps; the presence and lump counts of Freedoom's
monster sprites; Freedoom's BSD-3 licence text; that no `SD`-prefixed lump
exists in `freedoom2.wad`; that the string `DoomEdNum` appears nowhere in
GZDoom's own `zscript/` tree, which corroborates ADR 002's "MAPINFO
`DoomEdNums` is the only method"; that none of this document's sprite
prefixes or sound lumps collides with the arsenal's reservations in
MOD-SPEC §6.2–6.3. **NOT VERIFIED:** the visual content of any
Freedoom sprite; every value marked **(H)**; that a 16-px value test actually
separates the two recruits (it needs the first sprite sheet); that GZDoom
reports duplicate editor numbers as an error rather than silently overriding.
