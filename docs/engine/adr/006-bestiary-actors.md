# ADR 006 — The bestiary's actors: one thin base, `replaces`, a `Species` each, our own drops

Date: 2026-10-13. Status: accepted and **partly seen in the engine**: the
classes load clean, the drops and the General's one summon were observed on
2026-10-13 (GZDoom 4.14.2); infighting, blood colour and the on-screen order
line were not. Owner: `mod-engineer`.
Russian mirror: docs/ru/engine/adr/006-bestiary-actors.md (owed at the
phase close, D34).

Implements D35 (`docs/PRD.md`: the seven enemies, infighting kept, drops
ours, the General summons once, Freedoom sprites and sounds as stand-ins
until our own arrive) and pays debt T20. The argument first written in
`docs/engine/BESTIARY.md` §2.2 and §2.4 (as "ADR 003", a number since taken)
is the source; the code is `src/zscript/monsters/`. The contract rows are in
`docs/engine/MOD-SPEC.md` §5.1, §6, §6.1–6.3.

Glossary for anyone new: an **actor** is any object the engine spawns
(monster, projectile, pickup). `replaces` tells GZDoom "wherever a map spawns
actor X, spawn mine instead". A **species** is a label the engine uses to
decide which monsters leave each other alone. `DropItem` is what a monster
leaves on the floor when it dies.

## Context

F5 adds eight enemy classes (rifleman, Legion trooper, Stormtrooper, hound,
Doughboy, Panzermensch with its heavy variant, General) and four projectiles.
Seven decisions had to be taken before the first line of ZScript, and every
one has a cheaper-looking alternative that fails later and quietly:

1. what the classes inherit from;
2. how maps come to spawn them;
3. how Doom's monsters-fight-each-other behaviour survives;
4. what a corpse leaves behind;
5. how the General's one verb, "order two recruits", is made to happen once;
6. what the classes wear and sound like while our art and sound do not exist;
7. how the build notices a sprite we forgot to declare.

## Options and decision

### D-006-1 — `SD_Monster : Actor`, not the Doom monsters

| Option | What it is | Against |
|---|---|---|
| A. `class SD_X : ZombieMan` (as the arsenal does with weapons, ADR 002) | inherit the Doom monster | inherits its whole `States` block, its sounds and its strings |
| **B. `class SD_X : SD_Monster`, `SD_Monster : Actor`** | one thin shared base; every state written out in each class | more lines per class |
| C. DECORATE | the 1993 syntax | the project rule is ZScript for everything new (`mod-engineer.md`); nothing here needs DECORATE |

**Decision: B.** A Doom monster's `States` block is 20-odd frames in eight
rotations pointing at IWAD sprites (`POSS`, `TROO`...). A class that forgets
to override one state shows a Freedoom sprite in the middle of the fight, and
that bug appears on a single animation of a single enemy. Inheritance also
brings `SeeSound "grunt/sight"`, `DropItem "Clip"` and `Obituary
"$OB_ZOMBIE"`: a Soviet mod that grunts in Freedoom and prints Freedoom's
death lines. With B nothing is inherited that is not written in our file.

`SD_Monster` holds only what all eight share: the `Monster` flag set,
`+FLOORCLIP`, a `Faction` meta property (`SD_FACTION_REICH`, `_LEGION`,
`_BOTH`; read by nothing yet, kept for lore and HUD), and three attack
helpers: `A_SD_Hitscan(shots, dice, multiplier)`, `A_SD_Melee(dice,
multiplier)`, `A_SD_MeleeOrMissile(dice, multiplier, meleesound, missile)`.
They have the shape of Doom's `A_PosAttack`, `A_SargAttack` and
`A_TroopAttack` and use the same engine primitives, but take the dice and the
sound as arguments, because Doom's versions hard-code both and
`A_CustomBulletAttack` rolls damage x random(1,3) where Doom's infantry roll
random(1,5) x 3. `MeleeRange` is deliberately left at the engine default,
which is Doom's 64-unit bite.

**Why this is the opposite of ADR 002.** A weapon is one rotationless HUD
sprite set on top of plumbing we want (ammo bookkeeping, slot handling), so
`class SD_Izh : Shotgun replaces Shotgun` is right there. A monster's
inherited state machine is exactly what we do not want. Different risk,
different answer; recorded so the inconsistency reads as a decision.

The one inheritance inside our tree is `SD_PanzermenschSchwer :
SD_Panzermensch` (1000 HP, name and nothing else), the way Doom derives the
Hell Knight from the Baron.

### D-006-2 — `replaces`, not renumbered maps

Every enemy declares `replaces <DoomMonster>`: `ZombieMan`, `ShotgunGuy`,
`DoomImp`, `Demon`, `Cacodemon`, `HellKnight`, `BaronOfHell` (the heavy one)
and `Cyberdemon`. Options were to renumber the maps to our DoomEdNums
(21100–21107) or to rely on `replaces`. **Decision: `replaces`, and both
numbers work.** A map placing 3004 spawns a Soviet rifleman, and so does one
placing 21100; `level-designer` can keep the familiar numbers, a Freedoom or
Doom II map loaded with the mod turns Soviet, and nothing has to be rewritten
when our sprites land. `replaces` does not consume the replaced actor's
number for another use; it redirects the spawn. Our own numbers are assigned
only in MAPINFO's `DoomEdNums` block, the one method open to a ZScript class
(MOD-SPEC §6.1).

Limit, stated so nobody is surprised: only the Doom monsters we replace turn
Soviet. 65 (chaingunner), 58 (spectre) and the rest of Doom II's roster still
spawn Freedoom's actor (debt T21).

### D-006-3 — an explicit `Species` per class

GZDoom keeps a projectile from hurting a monster of the *owner's species*,
and an actor with no `Species` takes one from its class tree. The function,
`GetSpecies`, is native (no body in `gzdoom.pk3`), and the rule "a monster's
default species is its topmost *monster* ancestor" is from memory of the C++
source and **NOT VERIFIED**. If it holds, eight classes under one
`SD_Monster` (which carries `Monster`) would be one species, and a
Stormtrooper's bolt could never start a fight with a trooper, which would
silently remove D35's infighting ("they fight for profit, we fight for
everyone").

**Decision:** every class sets `Species "<its own class name>"` in `Default`.
The heavy Panzermensch inherits the Panzermensch's, as the Baron and the Hell
Knight share one in Doom. The outcome is then vanilla whichever way the
native rule reads: guaranteed by data, not by an assumption. No
`+DONTHARMSPECIES` and no `+DOHARMSPECIES` anywhere. `tests/test_bestiary.py`
(`test_every_class_sets_its_own_species`) fails a new class that forgets.

### D-006-4 — the drops are ours

The rifleman drops `SD_Clip` and the Legion trooper `SD_Izh` (D35: the
invaders carry captured Soviet arms). Both are named explicitly instead of
leaving Doom's `Clip` and `Shotgun` to be turned into ours by their own
`replaces` (ADR 003, ADR 002): the drop then reads as ours in the file, and
it does not depend on a replacement chain staying intact. The other six
classes drop nothing. `tests/test_bestiary.py` (`test_every_drop_is_ours`)
fails any `DropItem` that names a non-`SD_` class. The drop is made by the
`A_NoBlocking` state of the death animation.

### D-006-5 — the General summons once, from his own chase

Below half health the General stops, shouts an order (a `LANGUAGE` line on
every player's screen and a sound heard across the arena) and two Reich
riflemen arrive at his sides. Decisions:

- **Once is a flag, not a threshold crossing.** `bool summoned` is set
  *before* the jump to the `Summon` state, so nothing that re-enters the
  chase can order twice.
- **Checked in his own chase function**, `A_SD_GeneralChase`, not in the
  damage hook: a salvo in progress is never cut in half; he finishes
  shooting and summons on his next step. The condition is `!summoned &&
  health > 0 && health < SpawnHealth() * SD_GENERAL_SUMMON_FRACTION`.
- **Recruits never appear inside a wall.** `A_SpawnItemEx` (relative mode,
  `SXF_TRANSFERPOINTERS`) refuses to place a monster where it does not fit;
  four spots are tried in order (right, left, behind, in front, 72 units from
  his centre) until two have arrived. If fewer than two fit, fewer arrive;
  the order is still given and only once.
- **Awake on arrival.** Each recruit gets a `TeleportFog` and is put straight
  into its `See` state, as Doom's boss brain does with its cubes.
- The text is `$SD_GENERAL_ORDER` through `StringTable.Localize`, so it
  follows the language switch (ADR 004). `+BOSSDEATH` and `A_BossDeath` are
  set so MAP03's exit can be tied to his death.

### D-006-6 — IWAD sprites and sounds as declared stand-ins

Until `art-director` and `sound-designer` deliver, each state names an IWAD
sprite directly (`POSS`, `SPOS`, `TROO`, `SARG`, `HEAD`, `BOS2`, `CYBR`,
`BAL1`, `BAL2`, `BAL7`, `MANF`, `MISL`) laid out frame for frame like the
final reserved names (`SDRR`, `SDLT`, `SDHS`...; MOD-SPEC §6.3), so the swap
is a rename of four letters per state line. Sounds are **logical names**
(`sd/mon/<actor>/<event>`, 47 of them) that `SNDINFO` points at Freedoom
lumps; replacing one is a one-line `SNDINFO` edit plus a file under
`src/sounds/`. Two exceptions where the swap is more than a rename (the
General's `Summon` frames borrow `CYBR E F` and become `SDGN Q R`; his shell
flies as `MANF` and bursts as `MISL`) are marked in the class and in §6.3.

The mod redistributes **nothing**: the engine reads these from the loaded
IWAD, which is why a stand-in sprite is allowed only if it is written down.
**Every sprite name used is declared in MOD-SPEC §5.1**, the same rule §5
applies to IWAD textures; the sounds are listed in §6.2. A placeholder is
debt T18 until our art lands; the heavy Panzermensch looks exactly like the
normal one.

### D-006-7 — the build checks the sprites

`tools/check_pk3.py` (category `sprites`) reads every `States` block in the
packed ZScript (`zscript_state_sprites`, comments stripped first, flow
keywords such as `Goto` and `Loop` skipped) and fails the package when a
sprite name is none of: packed under `sprites/`, one of the engine's own
(`TNT1`, `####`, `----`), or declared in MOD-SPEC §5.1 (`check_state_sprites`).
It is the static twin of the engine's `Missing sprite`, and it means a
Freedoom sprite cannot enter a state without appearing in the contract.

Sounds are not checked by the build: a missing sound is silence, not an
error. `tests/test_bestiary.py` covers them instead, and also checks that
every placeholder sprite *frame* and sound lump exists in
`iwads/freedoom2.wad` 0.13.0 (skipped where no IWAD is present, as in CI).

## Consequences

- Eight classes, one file each, every state written out; adding an enemy is
  copying a sibling, not learning what a Doom monster secretly inherits.
- The price is volume: each class carries its own `Default` and `States`
  where inheritance would have saved them.
- Maps keep Doom's numbers and still field Soviet enemies; the cost is that
  an unreplaced Doom monster (T21) spawns Freedoom's, with Freedoom's drops
  and sounds.
- Swapping art or sound is mechanical (rename, one `SNDINFO` line), and the
  contract tables (§5.1, §6.2, §6.3) say exactly what to swap.
- The class names are `Species` strings: renaming a class means renaming its
  `Species` in the same commit (the test catches it).
- `Faction` is dead data until something reads it.

## Verified in the engine (2026-10-13)

GZDoom g4.14.2, Freedoom 0.13.0, Windows 10. Evidence:
`docs/qa/evidence/2026-10-13_1705_F5_map02-bestiary.log` and
`docs/qa/evidence/2026-10-13_1705_F5_map02-bestiary-gallery.png` (commit
`2b1aba5`); the MAP01 v3 pass
`docs/qa/evidence/2026-10-13_1708_F3_map01-v3-engine-pass.log` (commit
`bcbf35f`). The `SDTEST` lines come from a throwaway helper package loaded
beside the mod (counts and a `hurt` command); it is not in the repo.

| Claim | What was seen |
|---|---|
| The package loads clean | `sd.pk3` (385 lumps) mounted; no `Script error`, `Missing sprite`, `Unknown` or warning line in either log; MAP02 and MAP01 reach `SOVIETDOOM loaded` |
| All eight classes spawn from the gallery | one count per class on MAP02: 7 riflemen, 1 each of Legion trooper, Stormtrooper, hound, Doughboy, heavy Panzermensch and General, 2 Panzermensch |
| `replaces` works on Doom's numbers | MAP01 v3 places only Doom numbers and counts 14 riflemen, 8 Legion troopers, 5 Stormtroopers, 4 hounds, 1 Doughboy, 1 Panzermensch (33 in all), all ours |
| The drops | 7 riflemen killed: `SD_Clip` 0 to 7. Legion trooper killed: `SD_Izh` 1 to 2 |
| The General summons once | 1600 damage (3000 to 1400, under half): the log prints `The General: Recruits - advance!` once and riflemen go 7 to 9 (2 alive). 500 more damage: still 9 riflemen, no second line |
| The localized order reaches the string table and the console | the line above is the `$SD_GENERAL_ORDER` text, printed by `A_PrintBold` from a monster |
| A human played it | the CEO played MAP01 v3 on skill 3, "ha sido MUY divertido!!" (D38, commit `b26a210`) |

## NOT VERIFIED

- **Infighting between our classes.** No monster shot another in any log.
  The native `GetSpecies` rule that made D-006-3 necessary is still unread;
  the explicit `Species` makes the answer independent of it, but nobody has
  watched a Stormtrooper's bolt hurt a trooper.
- **`BloodColor "RR GG BB"`.** The engine accepts the string (no parse error)
  and no corpse was shot at a distance where the colour is visible.
- **The order line on the screen.** The console log carries it; no
  screenshot shows it in the middle of the view (`A_PrintBold` from a
  monster, `BESTIARY.md` §9).
- **The recruits fighting.** They exist and count as alive; that they enter
  the chase and attack was not logged. Nor was the blocked-spot fallback.
- **The attack helpers' damage.** Both engine passes ran in god mode, the
  gallery enemies were deaf and the MAP01 pass had `notarget`; no attack
  number was measured (debt T5). The CEO's play session is the only evidence
  that enemies attack.
- **How far a dead Doughboy falls** (`BESTIARY.md` §7).
- **Every value marked (H)** in the classes: guesses until measured.
- **Sounds**, which an unattended run cannot hear.
- **That `Species` is what stops friendly fire**: nothing was fired by one
  enemy at another.
