# ADR 002 — Arsenal in ZScript, own player class, editor-number range

Date: 2026-10-12. Status: accepted (F4), verified on GZDoom 4.14.2. Owner:
`mod-engineer`. Russian mirror: `docs/ru/engine/adr/002-arsenal-and-editor-numbers.md`.

## Context

F4 puts the seven period weapons (D13) into the engine: slot 1 sapper's
shovel, 2 TT-33, 3 IZh-58, 4 PPSh-41, 5 RPG-7, 6 ROKS-3, 7 hand Katyusha.
Three coupled questions had to be answered before writing any of them.

1. **How do our weapons displace Freedoom's?** If both sets exist the player
   ends up with a mixed arsenal and a wrong HUD.
2. **How do new actors become placeable on a map?** ZScript classes have no
   editor number until one is assigned, and `docs/engine/MOD-SPEC.md`
   proposed the range 14000–14999 marked NOT VERIFIED.
3. **How much complexity goes into the first pass?** F4's gate (G4) only
   asks that each weapon exists, has sprites, sounds, balance and a test
   range.

## Options

**Displacement.** (a) `replaces` on each weapon only — covers map-placed
pickups but leaves Freedoom's marine with Freedoom's slots and starting
pistol. (b) Own player class via MAPINFO `gameinfo { PlayerClasses }` —
replaces the whole loadout and slot table but does not touch pickups already
placed in maps. (c) Both.

**Editor numbers.** (a) The proposed 14000–14999. (b) Another range.
(c) No numbers at all, relying on `replaces` for placement.

**Melee and the double barrel.** (a) Reuse Doom's `A_Punch` / plain
`A_FireBullets` and accept a fist and a pump shotgun with new names.
(b) Write the behaviour that makes each weapon recognisable: a heavier,
slower swing, and a real two-shot break-open gun.

## Decision

1. **Both (c) for displacement.** Every weapon is `class SD_X : <DoomWeapon>
   replaces <DoomWeapon>`, *and* `SD_Player : DoomPlayer` is declared in
   MAPINFO under `gameinfo { PlayerClasses = "SD_Player" }`. The player pawn
   cannot be installed with `replaces` (ZDoom wiki, "Creating new player
   classes"), and `Player.StartItem` is explicitly **not inherited**, so the
   full loadout is restated in `SD_Player`. Both `Weapon.SlotNumber` and
   `Player.WeaponSlot` are set: the first is the fallback the engine uses
   when a slot table does not mention the weapon, the second is the table.
   Doom's chainsaw and super shotgun have no Soviet counterpart, so their
   editor numbers (2005, 82) are mapped to `None`.

2. **The mod reserves 21000–21999**, not 14000–14999. The proposal collides:
   GZDoom's standard editor-number list assigns **14001–14067** to
   `AmbientSound` / `SoundSequence` and **14101–14165** to `MusicChanger`.
   Verified against <https://zdoom.org/wiki/Standard_editor_numbers>
   (parsed 2026-10-12: nothing is assigned between 10504 and 13999, nor
   between 14166 and 31999 except 32000). 21000–21999 was chosen over the
   also-free 11000s and 20000s because the ZDoom wiki's own example uses
   20110–20112 and mods that copy it cluster there. Sub-blocks:
   21000–21019 weapons, 21020–21039 ammo and items, 21100–21199 enemies,
   21200–21299 decorations. Numbers are assigned in MAPINFO's `DoomEdNums`
   block, the only way for a ZScript class (ZDoom wiki, "Editor number").

3. **(b) for behaviour, inside a strict budget.** Exactly one weapon carries
   internal state (`SD_Izh.barrels`, the two-barrel counter). Everything
   else is Doom's own action functions with our constants. Every gameplay
   number is a named constant whose comment says why, and the reasoning
   lives in `docs/engine/BALANCE.md`.

4. **ZScript only**, per the project rule. No DECORATE anywhere in F4.

5. **Sprites and sounds stay Freedoom placeholders** for the whole of F4's
   first pass. Sounds go through SNDINFO logical names
   (`sd/weapon/<gun>/<event>`), so when real audio lands only the right-hand
   column of SNDINFO changes and no ZScript is touched. Sprite lump names
   are reserved in `docs/engine/MOD-SPEC.md` for `art-director`.

## Consequences

- Freedoom's weapons are gone from the player's hands: `printinv` on MAP02
  lists exactly the seven `SD_` classes and nothing else.
- Any map in the mod can place a weapon with 21001–21007, and MAP02 does.
- `docs/engine/MOD-SPEC.md` §6 had to be corrected: the 14000–14999
  proposal was wrong, and it was wrong because it was never checked. The
  NOT VERIFIED label did its job.
- The ammo pools stay Doom's four (`Clip`, `Shell`, `RocketAmmo`, `Cell`),
  so Freedoom ammo pickups and the status bar keep working. The cost is one
  open question for the CEO: whether the hand Katyusha deserves its own
  ammo type instead of sharing fuel with the flamethrower.
- Freedoom's super shotgun and chainsaw classes still exist in the engine
  (only their editor numbers were removed). A cheat or a future mod could
  still conjure one; no map can.
- Technical debt is listed in `docs/engine/MOD-SPEC.md` §10.
