# BESTIARY — enemy specification (F5)

Living document. Owner: `mod-engineer`. Russian mirror:
`docs/ru/engine/BESTIARY.md` (synced in batch at the phase close, D34).
Status: **v1, implemented with Freedoom placeholders, 2026-10-13.** v0 was the
specification of 2026-10-12; the CEO closed its seven open questions on
2026-10-13 (**D35**, §14) and the seven classes, the heavy Panzermensch and
the four projectiles now exist in `src/zscript/monsters/`, one class per
file, wearing Freedoom sprites and sounds until our own arrive (§2.7). The
engine pass of 2026-10-13 loaded them clean, counted the drops and the
General's single summon, and left infighting, blood colour and the attack
numbers unseen (`docs/engine/adr/006-bestiary-actors.md`, debt T22).

This document is the contract for the six ratified enemies (D13) between
`mod-engineer` (classes, numbers, states), `art-director` (sprites, colour)
and `sound-designer` (sound lumps). Product facts — the two allied factions,
their look, the tone — come from `docs/PRD.md` (D9, D12, D13, D14) and
`docs/product/LORE.md` and are not repeated here. Colour rules come from
`docs/art/ART-BIBLE.md` §6 and are quoted, not redefined.

Every number below is now a **named constant in the class** with the same
reason in one line; if this file and the code disagree, the code is the truth
and this file is the bug (the rule of `BALANCE.md`). `tests/test_bestiary.py`
holds the key numbers of §3–§9 to the code. The ones marked **(H)** are still
hypotheses to calibrate in the F5 playtest.

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
| Blood | **dark red** — `flag_red` 0–5 on screen, `BloodColor "AD 27 21"` (D49) | **dark red**, the same (D49) |

Value check against ART-BIBLE §6.1 (walls live in the 0.45–0.70 band, concrete
mid is 0.58): Reich body ≈ 0.38, Legion body ≈ 0.72–0.80. Both clear the
"≥ 2 ramp steps away from concrete" rule, in opposite directions. **The two
factions are told apart by value, not by hue** — that is the whole legibility
plan and it also survives Doom's sector lighting, which crushes hue first.

Blood colour is set with the `BloodColor` property, which recolours the
standard blood sprite; no new blood actor is needed.

**Blood is dark red for every faction (D49, CEO 2026-10-14: "rojo oscuro,
nada de oliva").** This supersedes the original row, which gave the Reich
dark olive (`khaki_olive` 1–4) and the Legion pale (`plaster_warm` 10–14) so
that a corpse told the factions apart by value. The CEO's call is about the
deaths reading as deaths; the factions stay apart by body, helmet and
accent, which carry the legibility plan above, and the drawn deaths (the
rifleman's D48 death and gib, the Stormtrooper's) already bleed `flag_red`.
One value for all seven classes, `BloodColor "AD 27 21"` (`flag_red` 9),
set in each file under `src/zscript/monsters/` and pinned by
`tests/test_blood.py`; `SD_PanzermenschSchwer` inherits it.

Why 9 and not the 0–5 the drawn deaths use: GZDoom does not paint the
`BloodColor` value, it scales it by each blood pixel's brightness,
`BloodColor × max(r,g,b) / 255` (`CreateBloodTranslation`, g4.14.2
`src/r_data/r_translate.cpp`, read in the source: VERIFIED as code, the
on-screen look NOT VERIFIED until the PM's engine pass). The value is the
colour at full brightness. Freedoom's `BLUD` frames run from 67 to 191 in
brightness, so `flag_red` 9 comes out as `flag_red` 0–5 on screen: the same
band as the drawn deaths, darker than the armband's `flag_red` 4–11, so the
floor still never competes with a `flag_red` accent. The test runs that
formula on the IWAD's real `BLUD` frames. Particle splashes
(`P_DrawSplash2`, only with particle blood on) use the value itself, i.e.
`flag_red` 9.

Rows elsewhere in this document that still say "olive" (§3's "Olive
blood", §6's Blood row) predate D49 and are superseded by this section.

### 2.2 Infighting

**Vanilla Doom infighting is kept (D35, closing Q5).** A Reich shell that
clips a Legion trooper starts a fight, exactly as in Doom. Lore reading: the
alliance is one of convenience — "they fight for profit, we fight for
everyone" (`LORE.md`). This is also the single biggest tactical pleasure of
Doom and removing it would change the rhythm of every room.

**Implementation: every class sets its own `Species`** (its class name; the
heavy Panzermensch inherits the Panzermensch's, as the Baron and the Hell
Knight share one in Doom). The reason is the shared base class. GZDoom stops a
projectile from hurting a monster of the projectile owner's species, and an
actor with no `Species` gets one from its class tree. That function,
`GetSpecies`, is native (`actor.zs:862`, no body in `gzdoom.pk3`), and the
rule that a monster's default species is its topmost *monster* ancestor is
from memory of the C++ source, **NOT VERIFIED**. If it holds, seven classes
under one `SD_Monster` (which carries `Monster;`) would all be one species and
a Stormtrooper's bolt could never start a fight with a trooper. Setting
`Species` explicitly makes the outcome the same whichever way the native code
reads, so the vanilla behaviour is guaranteed by the data, not by an
assumption. No `+DONTHARMSPECIES` and no `+DOHARMSPECIES` anywhere.

### 2.3 Naming

| Thing | Pattern | Example |
|---|---|---|
| ZScript class | `SD_<Name>` | `SD_ReichRifleman` |
| Source file | `src/zscript/monsters/<snake_case>.zs`, one class per file | `src/zscript/monsters/reich_rifleman.zs` |
| Sprite | `SD` + 2 letters | `SDRR` |
| Sound lump | `SD` + 3-letter actor code + 3-letter event code = 8 chars | `SDRRISIT` |
| SNDINFO logical name | `sd/mon/<actor>/<event>` | `sd/mon/reichrifleman/sight` |
| LANGUAGE id | `SD_TAG_<X>`, `SD_OB_<X>`, `SD_OBHIT_<X>`; the General's order `SD_GENERAL_ORDER` | `SD_TAG_RIFLEMAN` |

The logical-name scheme matches the arsenal's (`sd/weapon/iceaxe/swing`,
named in `src/zscript/weapons/ice_axe.zs`; the shovel's until D40). The
lump scheme differs by one character — the arsenal uses a 2-letter weapon
code (`SDAXSWG`), the
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
`+FLOORCLIP`, a `Faction` property used by future lore/HUD code, and the
attack helpers of the next paragraphs). It does not set `MeleeRange`: the
engine default, `64 - MELEEDELTA` = 44 plus the target's radius
(`actor.zs:90,411`), is Doom's 64-unit bite and is what every Doom monster
uses. Nothing derives from `ZombieMan`, `DoomImp` or the others; the one
exception is inside our own tree, `SD_PanzermenschSchwer : SD_Panzermensch`
(§8), which is how Doom itself derives the Hell Knight from the Baron.

`Faction` is an `int` meta property, `SD_Monster.Faction`, with three global
constants (`SD_FACTION_REICH`, `SD_FACTION_LEGION`, `SD_FACTION_BOTH`) rather
than a ZScript `enum`: an int property set from a named constant in a
`Default` block is the form the arsenal already runs in the engine
(`Weapon.SlotNumber`, `Weapon.AmmoUse SD_IZH_AMMO_USE`), and nothing reads the
value yet, so the cheapest proven form wins.

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

**Attack code:** three helpers on `SD_Monster` —
`A_SD_Hitscan(shots, dice, multiplier)`, `A_SD_Melee(dice, multiplier)` and
`A_SD_MeleeOrMissile(dice, multiplier, missile)` — written in the shape of
Doom's own `A_PosAttack` / `A_SargAttack` / `A_TroopAttack`
(`possessed.zs:267`, `demon.zs:88`, `doomimp.zs:106`), out of the same engine
primitives (`AimLineAttack`, `LineAttack`, `CheckMeleeRange`, `DamageMobj`,
`TraceBleed`, `SpawnMissile`), but with the dice and the sound as arguments.
Not the Doom functions, because they hard-code both the damage formula and
the sound (`A_PosAttack` plays `"grunt/attack"` literally); not the generic
`A_CustomBulletAttack` either, because it rolls `damage × random(1,3)`
(`attacks.zs:47`) and Doom's infantry roll `random(1,5) × 3`, which is the
parity this document promises. The damage formulas live in named constants
in each class, per CLAUDE.md.

This whole subsection became **ADR 006** (`docs/engine/adr/006-bestiary-actors.md`,
2026-10-13); v0 called it ADR 003, a number since taken (ammo naming,
language switch, menu text). Where the two differ, the ADR is later.

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

**Decided (D35, closing Q6): mixed.** The five enemies the player sees most
get drawings of their own; death and gib frames may be edited Freedoom
(BSD-3, credited in `docs/art/LICENSES.md`). Until any of it arrives, every
class wears a Freedoom sprite as a placeholder (§2.7).

With Doom's mirroring convention (rotations 2&8, 3&7, 4&6 share one image, so
an 8-rotation frame costs 5 drawings) the seven actors and their four
projectiles need about **354 sprite images** (itemised in §12; v0 said 356,
the frame layouts were aligned to Doom's in v1, §2.7). That is the
single largest cost in F5 and it is larger than
all of F2 put together. The two mitigations v0 listed, kept for the record:

1. **Freedoom as reference, not as pixels.** Freedoom is BSD-3-Clause
   (verified: `iwads/freedoom-0.13.0/COPYING.txt`, "Redistribution and use …
   with or without modification, are permitted"), so shipping edited Freedoom
   sprites is legal provided we retain the copyright notice and disclaimer in
   `docs/art/LICENSES.md` and never imply Freedoom endorses the mod (the
   third clause). BSD-3 is permissive, so derivatives may carry our
   CC BY-NC-SA 4.0 (D15). **But** a recoloured Freedoom monster still reads as
   Freedoom, and the mod's identity is the product. Recommendation: use
   Freedoom for *animation timing and silhouette blocking*, draw our own
   pixels. (Was Q6; closed by D35 as "mixed", above.)
2. **Pose once, render many.** A posed low-poly model or a paper-doll rig
   rendered at 8 angles is the standard way modern TCs afford this. Out of
   `mod-engineer` scope; flagged so F5 is planned with the real number.

The sprite lumps `POSS SPOS CPOS TROO SARG HEAD BOSS BOS2` all exist in
`iwads/freedoom2.wad` (verified by lump listing: 70, 49, 48, 53, 46, 36, 72,
71 lumps respectively). Their *visual content* has **NOT been inspected** by
`mod-engineer`; every "could derive from Freedoom" judgement below is
**NOT VERIFIED** and is for `art-director` to confirm by looking.

No Freedoom lump begins with `SD` (verified), so our sprite namespace is free.

### 2.7 Placeholders until our art and sound arrive (F5, D35)

The classes are playable now, the way the arsenal was in F4: every state
names a Freedoom sprite, every sound is a logical name (`sd/mon/<actor>/<event>`)
that `SNDINFO` points at a Freedoom lump. The full tables, with the final
lump each placeholder stands in for, are contract and live in
`MOD-SPEC.md` §6.2 (sounds) and §6.3 (sprites); the IWAD sprites are declared
in `MOD-SPEC.md` §5, which is what lets `tools/check_pk3.py` accept them.

| Class | Final sprite | Placeholder | Same frame layout? |
|---|---|---|---|
| `SD_ReichRifleman` | `SDRR` | `POSS` (zombieman) | yes |
| `SD_LegionTrooper` | `SDLT` | `SPOS` (shotgun guy) | yes |
| `SD_Stormtrooper` | `SDHS` | `TROO` (imp) | yes (v1 aligned §5's gib to `TROO`'s N–U) |
| `SD_StormBolt` | `SDBL` | `BAL1` | yes |
| `SD_ReichHound` | `SDHN` | `SARG` (demon) | yes |
| `SD_Doughboy` | `SDDB` | `HEAD` (cacodemon) | yes |
| `SD_DoughboyShell` | `SDDL` | `BAL2` | yes |
| `SD_Panzermensch` and `SD_PanzermenschSchwer` | `SDPM` | `BOS2` (hell knight) | yes |
| `SD_PanzerShell` | `SDPL` | `BAL7` | yes |
| `SD_General` | `SDGN` | `CYBR` (cyberdemon) | yes for A–P (v1 aligned §9 to `CYBR`); the two `Summon` lines borrow `CYBR E F` and become `SDGN Q R` |
| `SD_GeneralShell` | `SDGL` | `MANF` A–B flight, `MISL` B–D burst (Doom's mancubus shot) | no: the burst becomes `SDGL C D E` |

**The swap rule.** Because the frame letters already follow §3–§9, replacing
a placeholder is a rename of the four-letter sprite name in that class's
`States` block, and nothing else — except the four lines named in the last
two rows. Sounds are a one-line `SNDINFO` change each and no ZScript at all.

**Not swapped by a rename:** the heavy Panzermensch has no sprites of its
own. It inherits every state from `SD_Panzermensch`, so today it looks
identical; the recolour v0 planned is a `Translation` added when `SDPM` lands
and the palette for it exists (`art-director`). Until then the PM tells the
two apart by `Tag` and by how long they take to die.

---

## 3. Fourth Reich rifleman — basic infantry (1 of 2)

> Bestiary row "Yankee-Nazi recruits" is specified as **two classes**, one per
> faction, because Doom's basic-infantry slot is itself two actors (zombie and
> sergeant) and because splitting them is what puts both factions in the
> player's first room. **Two names for the two classes (D35, closing Q1):**
> *Reich rifleman* / «стрелок Рейха» and *Legion trooper* / «легионер».
> `docs/levels/MAP01-zarya-7.md` §8 says "Fourth Reich recruit" for the same
> unit; the player-facing name is the `LANGUAGE` one, and "recruit" survives
> as the lore word the General's order uses (§9).

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
| `Health` | **20** | `ZombieMan` parity. This number sets the whole ammo economy: 20 HP is two TT-33 rounds (avg 12), three PPSh rounds (avg 8) or one IZh barrel. Change it and every ammo pickup in MAP01 is wrong. |
| `Radius`/`Height` | **20 × 56** | parity. Doom's corridor widths and doorway heights assume this; the `level-designer` builds on 64-unit grid against it. |
| `Speed` | **8** | parity. |
| `Mass` | **100** | parity — governs how far he is thrown by an RPG blast. |
| `PainChance` | **200** | parity (78 % chance per hit). High painchance is what makes the basic zombie *stunlockable*, which is how a Doom player safely opens a fight. |
| Attack | hitscan, `random(1,5) × 3` = 3–15, 1 shot | parity with `A_PosAttack`. |
| Accuracy spread | `random2() × 22.5/256` degrees: triangular, at most ±22.4° (`possessed.zs:267`) | parity. v0 wrote "≈ ±1.4°", which was wrong by a factor of sixteen: `Random2()` spans −255…255. Doom's infantry is *inaccurate* and dangerous by volume and at short range, which is exactly why a corner is a Doom player's best friend. |
| `MeleeRange` | n/a (no melee) | parity. |
| Range | `MISSILERANGE` (2048 units) | parity. |
| `DropItem` | **`SD_Clip`** | `ZombieMan` parity in amount, ours in name (D35, closing Q4: the invaders hold the Zarya-7 armoury and carry **captured Soviet arms**). ADR 002 kept Doom's four ammo pools and the TT-33 and the PPSh both draw `Clip`; `SD_Clip` is our 7.62x25 magazine (`MOD-SPEC.md` §6.4), so the player picks up "A magazine. 7.62x25." from a dead invader. |

### States and sounds

| State | Frames | Sound event | Sound lump | Note for `sound-designer` |
|---|---|---|---|---|
| `Spawn` (idle/look) | `SDRR A B`, 10 tics, `A_Look` | `active` | `SDRRIACT` | a muttered order in real German (D36; lines in `docs/sound/VOICE-SCRIPT.md`) |
| `See` (walk) | `SDRR AABBCCDD`, 4 tics, `A_Chase` | `sight` | `SDRRISIT` | a bark, short; heard many times per map |
| `Missile` | `SDRR E` 10 `A_FaceTarget`, `F` 8 *attack*, `E` 8 | `attack` | `SDRRIATK` | dry bolt-action crack, drier than the player's TT-33 so the player can tell incoming from outgoing |
| `Pain` | `SDRR G` 3, `G` 3 `A_Pain` | `pain` | `SDRRIPAI` | |
| `Death` | `SDRR H I J K`, 5 tics, `L` −1 | `death` | `SDRRIDTH` | |
| `XDeath` | `SDRR M N O P Q R S T`, 5 tics, `U` −1 | `xdeath` | `SDRRIXDT` | gib; triggered when damage exceeds `GibHealth` |

6 sounds (v0 said 7, but listed these 6; the "52" total was the same slip, §12). Lump names are all exactly 8 characters.

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
| `DropItem` | **`SD_Izh`** | parity with `ShotgunGuy` dropping a `Shotgun`. Because `SD_Izh replaces Shotgun` (ADR 002), writing either class name works; naming ours is clearer. Captured Soviet arms (D35). |

### States and sounds

Same state layout as §3 with sprite `SDLT` and lumps `SDLTRSIT`, `SDLTRACT`,
`SDLTRATK`, `SDLTRPAI`, `SDLTRDTH`, `SDLTRXDT`, with one difference that is
`ShotgunGuy` parity: the `See` cycle is **3** tics per frame, not 4, and the
`Missile` frames are 10/10/10 (`possessed.zs`, `ShotgunGuy`). 6 sounds (no
separate idle bark is strictly needed, but one is listed so the two factions
sound different in an ambush).

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
| `XDeath` | `SDHS N O P Q R S T` 5, `U` −1 | `xdeath` | `SDSTOXDT` |

8 sounds. Note the bolt owns two of them.

### Sprites

| Group | Frames | Rot | Images |
|---|---|---|---|
| Walk | A B C D | 8 | 20 |
| Attack | E F G | 8 | 15 |
| Pain | H | 8 | 5 |
| Death | I–M (5) | 0 | 5 |
| Gib | N–U (8) | 0 | 8 |
| **Total** | | | **53** + 5 bolt |

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

**Colour.** `khaki_olive` **1–9** hide, black underbelly and muzzle, black
claw tips. **D45 (2026-10-14) moved the hide down the ramp from the 4–10 this
section first gave:** `art-director`'s first render in 4–10 measured a body
luma of **99 against `SDSTEL1`'s 101**, a gap of 1, and the hound vanished on
green steel (`docs/art/previews/2026-10-13_2211_F5_storm-hound-sweep.html`).
In 1–9 it is Reich-dark like the rifleman (the sweep notes body luma 70–75)
and separates from `SDSTEL1` by value; §10's **caution** on green steel and
its light-112 rule still stand. The CEO accepted it with palette v2 (D45,
`docs/PRD.md`). **No red accent at all** — the hound is the one enemy with no faction
insignia, because a dog does not wear an armband, and because it gives the
level designer one enemy that will never be camouflaged against a poster.

### Stats

| Property | Value | Why |
|---|---|---|
| `Health` | **150** | `Demon` parity. Kept exactly, because 150 is the number that makes a pinky cost two shotgun blasts; it is the main consumer of shells in early Doom and our MAP01 shell budget is built on it. |
| `Radius`/`Height` | **30 × 56** | parity. The wide radius is why pinkies block corridors — that is a *feature* the level designer uses. |
| `Speed` | **12** **(H)** | +20 % over the pinky's 10. The bestiary says "fast melee" and the hound must feel different from a shambling pinky. 12 is chosen rather than 14 because a melee-only monster faster than the player's forward run (≈ 16 units/tic equivalent) cannot be outrun in a corridor, which turns every hound into a guaranteed 4–40 damage tax. **Calibration lever: drop to 10 if MAP01 playtest shows corridors are unwinnable without the ice axe (the shovel until D40).** |
| `Mass` | **400** | parity. |
| `PainChance` | **180** | parity. |
| Melee | `random(1,10) × 4` = 4–40 | parity with `A_SargAttack`. |
| `MeleeRange` | engine default, not set | parity. The default is `64 - MELEEDELTA` = 44 plus the target's radius (`actor.zs:90,411`): Doom's 64-unit bite against a 20-radius player. A longer lunge range was considered and rejected — it reads as "the bite missed but hurt me", which players correctly call unfair. |
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

5 sounds (v0 said 6). No gib death: Doom's pinky has none either, and 6 extra rotationless
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
| Russian name | «Каска» ("the Helmet") — Q1(a) had no recommendation; chosen because "Doughboy" means nothing to a Russian-speaking player and the helmet is the unit's identity. One `LANGUAGE` line if the CEO prefers otherwise. |

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

7 sounds (v0 said 8). The death animation must *deflate and sink*, otherwise
the corpse hangs in the air. Doom's own sequence, read in `cacodemon.zs`, does
not touch `+NOGRAVITY`: it calls `A_NoBlocking` and then `A_SetFloorClip` on
the last frame, and the dead floater falls (where the C++ drops it is
**NOT VERIFIED**; it is what every Doom cacodemon visibly does). The class
copies that sequence.

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
v1 is **one map**. A 1000 HP brute in MAP01 costs about 8 RPG-7 direct hits
(135 average each, `BALANCE.md`) or 125 PPSh rounds — eleven seconds of
holding the trigger with every round landing, which is not a fight, it is a
wall. (v0 said "5 RPG-7 hits or 48 PPSh rounds"; both figures were wrong.)

**Decided (D35, closing Q2): `SD_Panzermensch` ships at Hell Knight numbers
(500 HP) and `replaces HellKnight`; the heavy variant
`SD_PanzermenschSchwer` (1000 HP, `replaces BaronOfHell`, DoomEdNum
**21107**) exists for MAP03.** The variant is implemented now because it
costs twenty lines and closes a hole: without it a map placing Doom's Baron
(3003) would spawn a Freedoom baron in a Soviet map. It derives from
`SD_Panzermensch` and changes only `Health` and `Tag`, so it has no
`States` block of its own and no sprite name to swap. It does not copy the
Baron's `+BOSSDEATH` / `A_BossDeath`: in Doom those serve only E1M8-style
map specials (`baronspecial`), which no map of ours uses. Its recolour is a
`Translation` added when the art exists (§2.7).

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

8 sounds (v0 said 9). The footstep is the cheapest possible "boss is coming"
telegraph and costs one `A_StartSound` in the `See` state, on the first frame
of each 8-frame cycle (one step per 24 tics). Marked **(H)**: cut it if it
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
| LANGUAGE | `SD_TAG_GENERAL`, `SD_OB_GENERAL`, `SD_GENERAL_ORDER` |
| **Scope** | **First placed in MAP03.** Implemented in F5 (2026-10-13) so the mechanic can be tested on MAP02's bench (§11) long before MAP03 exists; no MAP01 places him. |

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

### The design question (Q3) — decided: B (D35)

Two shapes for this fight; the CEO chose **B** on 2026-10-13.

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

`mod-engineer` recommended **B** and the CEO took it. Anything larger (phase
changes, invulnerable shields, scripted arenas) is out of proportion for a
three-map episode and would be its own ADR.

**How B is built (v1).**

- **Trigger.** Every `See` frame calls `A_SD_GeneralChase`, which checks
  `health < SpawnHealth() × SD_GENERAL_SUMMON_FRACTION` (0.5) before it
  chases. Checking in the chase rather than in `DamageMobj` means the summon
  never cuts a salvo in half: if the shot that crosses 50 % lands mid-salvo,
  he finishes it and summons on his next step (≤ 72 tics later). If one blow
  takes him from above half to dead, there is no summon, which is correct.
- **Once.** A `bool summoned` on the actor, set before the jump to `Summon`,
  so it cannot repeat even if he is resurrected from the console.
- **Who comes.** `SD_GENERAL_SUMMON_COUNT` = **2** × `SD_ReichRifleman`. v0
  named an `SD_ReichRecruit` that was never specified; the recruits *are*
  the Reich's basic infantry (§3), and "the Reich supplies the bodies, the
  Legion the capital" is this unit's whole lore.
- **Where.** `A_SpawnItemEx` at `SD_GENERAL_SUMMON_SIDE` (72 units: his
  radius 40 + theirs 20 + 12 clear) to his right and left; if a side is
  blocked, the next spot in the list is tried (behind, then in front).
  `A_SpawnItemEx` refuses to place a monster where it does not fit
  (`attacks.zs:235`), so a recruit never appears inside a wall; in a cramped
  spot fewer than two may come, the price of never telefragging anyone. Each
  recruit takes his target (`SXF_TRANSFERPOINTERS`), wakes straight into
  `See` the way Doom's boss-brain cubes wake their spawn
  (`bossbrain.zs:397`), and arrives inside a `TeleportFog`.
- **The order.** `A_PrintBold` of `SD_GENERAL_ORDER` (`LANGUAGE`, EN and RU,
  resolved explicitly with `StringTable.Localize`) and the sound
  `sd/mon/general/summon` → `SDGENSUM` at no attenuation, so it is heard
  across the arena. The wording is a placeholder until the CEO answers
  `docs/sound/ENEMY-SOUNDS.md` §7 C; text and sound change together.
  **NOT VERIFIED:** that `A_PrintBold` called by a monster reaches the
  player's screen (signature at `actor.zs:1203`; the behaviour is native).

### States, sounds, sprites

| State | Frames | Sound | Lump |
|---|---|---|---|
| `Spawn` | `SDGN A B` 10 `A_Look` | `active` | `SDGENACT` |
| `See` | `SDGN AABBCCDD` 3 `A_Chase` | `sight` | `SDGENSIT` |
| `Missile` | `SDGN E` 6 `A_FaceTarget`, then (`F` 12 *shot*, `E` 12 `A_FaceTarget`) ×3 | launch | `SDGENMIS` |
| | | impact | `SDGENEXP` |
| `Summon` (B) | `SDGN Q` 15 *order*, `R` 15 | order | `SDGENSUM` |
| `Pain` | `SDGN G` 10 `A_Pain` | `pain` | `SDGENPAI` |
| `Death` | `SDGN H I J K L M N O` 10, `P` 30, `P` −1 `A_BossDeath` | `death` | `SDGENDTH` |

7 sounds (v0 said 8). The `death` lump is the last sound in the episode;
`sound-designer` should treat it as a cue, not an effect.

**v1 changed the frame letters** to `Cyberdemon`'s layout (`cyberdemon.zs`):
walk A–D, attack E–F, pain G, death H–P, and the two summon frames appended
as Q–R. That keeps the placeholder swap a rename for every state but
`Summon` (§2.7).

Sprites: walk 4×5 = 20, attack 2×5 = 10, summon 2×5 = 10, pain 1×5 = 5,
death 9 = **54 images** + 5 projectile.

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
F5 and F3 can be planned against the same assumption. **D35 (Q7): MAP01 is
Reich first**; the Liberty Legion appears halfway, as the force holding the
hangar. MAP02 inverts it and MAP03 mixes.

### 11.1 The test bench on MAP02 (F5)

Before any campaign map places them, every class stands in a row in MAP02's
**bestiary gallery** (`src/maps/MAP02/map.py`, `MOD-SPEC.md` §4): a room of
its own, not connected to the arsenal hall, so nothing in it hears or sees
the firing range. Each one is deaf (`ambush`) and faces the far wall, away
from the spot the PM warps to, so they stand still until shot one at a time.
The engine checklist that uses it is in the F5 hand-off; the room's
coordinates are constants in the map script.

---

## 12. Summary table

| # | Name | Class | Faction | EdNum | Replaces | HP | Spd | Pain | Attack | Sprite (placeholder) | Images | Sounds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Reich rifleman | `SD_ReichRifleman` | Reich | 21100 | `ZombieMan` | 20 | 8 | 200 | hitscan 3–15 | `SDRR` (`POSS`) | 49 | 6 |
| 2 | Legion trooper | `SD_LegionTrooper` | Legion | 21101 | `ShotgunGuy` | 30 | 8 | 170 | 3× hitscan 3–15 | `SDLT` (`SPOS`) | 49 | 6 |
| 3 | Hybrid Stormtrooper | `SD_Stormtrooper` | both | 21102 | `DoomImp` | 60 | 8 | 200 | melee 3–24 / bolt 3–24 | `SDHS` `SDBL` (`TROO` `BAL1`) | 58 | 8 |
| 4 | Reich hound | `SD_ReichHound` | Reich | 21103 | `Demon` | 150 | **12 (H)** | 180 | melee 4–40 | `SDHN` (`SARG`) | 46 | 5 |
| 5 | Doughboy | `SD_Doughboy` | Legion | 21104 | `Cacodemon` | 400 | 8 | 128 | melee 10–60 / shell 5–40 | `SDDB` `SDDL` (`HEAD` `BAL2`) | 41 | 7 |
| 6 | Panzermensch | `SD_Panzermensch` | Reich | 21105 | `HellKnight` | **500** | 8 | 50 | melee 10–80 / shell 8–64 | `SDPM` `SDPL` (`BOS2` `BAL7`) | 52 | 8 |
| 7 | The General | `SD_General` | Legion | 21106 | `Cyberdemon` | **3000 (H)** | 12 | 20 | 3× shell 8–64; summons 2 riflemen once below 50 % | `SDGN` `SDGL` (`CYBR`; `MANF` `MISL`) | 59 | 7 |
| 8 | Heavy Panzermensch | `SD_PanzermenschSchwer` | Reich | 21107 | `BaronOfHell` | 1000 | 8 | 50 | as #6 | inherits #6 | 0 (a translation) | 0 |
| — | *cloaked hound* | *reserved, not implemented* | Reich | *21108 reserved* | `Spectre` | 150 | 12 | 180 | as #4 | `SDHN` `+SHADOW` | 0 | 0 |

Totals for F5: **8 classes + 4 projectile actors, ≈ 354 sprite images,
47 sound lumps.** v0 said 356 and 52. The images moved with the frame
layouts (§2.7). The sounds never were 52: the per-actor lines of §3, §6, §7,
§8 and §9 each counted one more sound than their own tables list (7/6, 6/5,
8/7, 9/8, 8/7), and the tables were right. 47 is the list
`docs/sound/ENEMY-SOUNDS.md` §1 found by counting rows, the list `SNDINFO`
now defines (`sd/mon/*`, 47 logical names) and the list
`tests/test_bestiary.py` holds the two to.

Classes the bestiary does **not** replace, so a map placing them still gets
Freedoom's actor: `ChaingunGuy` (65), `Spectre` (58, reserved above),
`LostSoul`, `PainElemental`, `Revenant`, `Fatso`, `Arachnotron`, `Archvile`,
`SpiderMastermind`, `WolfensteinSS`, `CommanderKeen` and the boss-brain set.
**`level-designer`: MAP01 §8 plans a "Legion heavy gunner" on thing 65; no
such class exists or is ratified (D13 lists six enemies).** Either it is cut,
or it becomes a CEO question for a seventh enemy; until then 65 is a Freedoom
chaingunner.

---

## 13. What other documents must change

| Document | Change | Owner | Status |
|---|---|---|---|
| `docs/engine/MOD-SPEC.md` §6.1 | The bestiary numbers in the `21100–21199` table | `mod-engineer` | **Done 2026-10-13** |
| `docs/engine/MOD-SPEC.md` §2, §3, §5, §6, §6.2, §6.3 | `zscript/monsters/` in both layouts; the IWAD sprites in §5; the classes in §6; the 47 sounds in §6.2; the sprite reservations and placeholders in §6.3 | `mod-engineer` | **Done 2026-10-13** |
| `docs/engine/MOD-SPEC.md` §5 | MAP02's zombieman fixtures (3004) are Soviet riflemen now | `mod-engineer` | **Done 2026-10-13** |
| `docs/engine/BALANCE.md` | Link here; shots-to-kill of each enemy by weapon | `mod-engineer` | **Done 2026-10-13** |
| `docs/art/ART-BIBLE.md` §3 | The **pink/flesh ramp** reserved for the Liberty Legion must be added as `palette.json` **v2** before any Legion sprite is drawn; §6 should absorb the six map rules of §10 above | `art-director` | open |
| `docs/art/TEXTURE-INDEX.md` | Sprites are not textures, but the F5 sprite sheets need their own index with the same origin/licence columns | `art-director` | open |
| `src/lumps/LANGUAGE` | 8 `SD_TAG_*`, 7 `SD_OB_*`, 3 `SD_OBHIT_*` and `SD_GENERAL_ORDER`, `[enu default]` and `[ru]` (D21) | `mod-engineer` | **Done 2026-10-13** |
| `docs/art/LICENSES.md` | When any edited Freedoom pixel or sound ships (D35 allows it for deaths and gibs), the BSD-3 notice, disclaimer and no-endorsement clause. Placeholders read from the IWAD at run time are not redistributed and need no row (MOD-SPEC §5) | `qa-engineer` audit | open, nothing ships yet |
| `docs/engine/adr/006-bestiary-actors.md` | **ADR 006 — "Enemies derive from `SD_Monster : Actor`, not from the Doom monsters"**: context (§2.4), options (derive from Doom monsters / from `Actor` / DECORATE), decision, consequences (every state written out; no inherited IWAD sprites or sounds; explicit `Species`; deliberate divergence from ADR 002's choice for weapons). v0 called it 003, a number since taken | `mod-engineer` | **Done 2026-10-13** (debt T20) |
| `docs/levels/MAP01-zarya-7.md` §8 | Swap the Freedoom placeholders for our editor numbers (or keep the Doom numbers, which `replaces` already turns into ours); settle the heavy gunner (§12) | `level-designer` | open |

---

## 14. Questions for the CEO — closed by D35 (2026-10-13)

All seven were answered on 2026-10-13, every one as recommended
(`docs/PRD.md`, D35). Kept as the record of what was asked.

| # | Question | Answer (D35) | Where it landed |
|---|---|---|---|
| **Q1** | **Names.** Proposed finals: *Reich rifleman* («стрелок Рейха»), *Legion trooper* («легионер»), *Hybrid Stormtrooper* («штурмовик-гибрид»), *Reich hound* («гончая Рейха»), *Doughboy*, *Panzermensch*, *the General* («Генерал»). (a) Is "Doughboy" readable to a Russian-speaking player? (b) One name for the two infantries, or two? | (b) **Two names.** (a) was not answered separately; `mod-engineer` chose «Каска» (§7), one `LANGUAGE` line to change | `LANGUAGE`, §3, §7 |
| **Q2** | **Panzermensch tier**: 500 HP in MAP01 and a 1000 HP variant for MAP03, or Baron numbers? | **500 in MAP01, 1000 variant for MAP03** | §8, `SD_PanzermenschSchwer` at 21107 |
| **Q3** | **Is the General a boss or a big brute?** | **B, a boss with one verb**: below half health he summons two recruits and shouts an order | §9 |
| **Q4** | **What do enemies drop?** | **Captured Soviet arms**: our ammunition and our weapons | §3 (`SD_Clip`), §4 (`SD_Izh`) |
| **Q5** | **Infighting** between the allied factions? | **Kept**, an alliance of convenience | §2.2 |
| **Q6** | **Freedoom sprites?** | **Mixed**: own drawings for the five most-seen enemies; deaths and gibs may be edited Freedoom (BSD-3, credited) | §2.6, §2.7 |
| **Q7** | **Does one faction dominate MAP01?** | **Reich first**; the Legion appears halfway, holding the hangar. MAP02 inverts it, MAP03 mixes | §11, for `level-designer` |

---

*Verification note (CLAUDE.md radical honesty).* **Verified** (v0,
2026-10-12): GZDoom 4.14.2 actor stats and the `extend class Actor` attack
functions; the editor-number collision at 14001–14165 and the free gaps; the
presence and lump counts of Freedoom's monster sprites; Freedoom's BSD-3
licence text; that no `SD`-prefixed lump exists in `freedoom2.wad`; that the
string `DoomEdNum` appears nowhere in GZDoom's own `zscript/` tree; that none
of the sprite prefixes or sound lumps collides with the arsenal's.
**Verified in v1** (2026-10-13), by reading `gzdoom.pk3` of the installed
g4.14.2 on Windows as a zip: the Doom monsters' states and frame layouts that
§2.7 aligns to; the signatures of every engine function and flag the classes
call (`AimLineAttack`, `LineAttack`, `CheckMeleeRange`, `DamageMobj`,
`TraceBleed`, `SpawnMissile`, `A_SpawnItemEx` and its `SXF_*` flags,
`SpawnHealth`, `A_PrintBold`, `StringTable.Localize`, `A_BossDeath`,
`A_SetFloorClip`, `TeleportFog`, `ATTN_NONE`, `MELEEDELTA`); that every
placeholder sprite frame the states name and every placeholder sound lump
`SNDINFO` names exists in `iwads/freedoom2.wad` 0.13.0
(`tests/test_bestiary.py`, which runs it whenever the IWAD is present).
**NOT VERIFIED:** anything in the engine — no class has been loaded by
GZDoom yet (D26: the PM's batch run); the native `GetSpecies` rule (§2.2);
the `BloodColor` property's string form, which is native and not used in any
engine `.zs` file; that `A_PrintBold` from a monster reaches the screen
(§9); how far a dead Doughboy falls (§7); the visual content of any Freedoom
sprite; every value marked **(H)**; that a 16-px value test separates the two
recruits; that GZDoom reports duplicate editor numbers as an error rather
than silently overriding.
