# ADR 012 — The RGD-5 hand grenade: slot 8, its own pool, a fuse of our own

Date: 2026-10-23. Status: proposed for V3 (D120, proposal A4), **built in a
worktree, not in v1.2, not yet seen in the engine** (the PM's batched engine
pass, D26). Owner: `mod-engineer`. Amends `docs/engine/MOD-SPEC.md` §6.4
(the rule for a pool of our own) and the "one weapon per slot" reading of
D13 a second time (ADR 011 was the first). The design and the numbers are
`docs/engine/2026-10-23_V3_rgd5.md`; the balance rows `BALANCE.md` §2, §3
(slot 8), §4 and §8.1.

## Context

The CEO chose a hand grenade for V3 (D120: "A4 - RGD-5 hand grenade, a
thrown weapon with its own ammo"). Four questions had to be settled before
any code: which key throws it, which pool it eats, how a thrown, fused,
bouncing grenade is built in GZDoom, and how a loose grenade on the floor
becomes something the sergeant can throw. Doom has no grenade to replace;
GZDoom's own nearest piece is Strife's grenade launcher and its
`HEGrenade` (gzdoom.pk3 g4.14.2, `zscript/actors/strife/weapongrenade.zs`,
read 2026-10-23).

## Options

**Key.**

1. **Slot 7, beside the hand Katyusha.** No new key; the two "heavy
   Soviet surprises" together. But slot 7 is the panic button (BALANCE §1),
   and when both are owned the key 7 cycles: the grenade thrown round a
   corner would cost one press or two depending on what was raised last,
   and the Katyusha's 40-cell salvo could come up instead of a grenade.
2. **Slot 5, beside the RPG-7** (the explosives). Same cycling problem
   with the weapon the sergeant raises most in Episodes 2-3.
3. **Slot 1, beside the ice axe** (the "no gun" slot; Doom's slot 1 held
   the fist and the chainsaw). Slot 1 is the last resort; the grenade is a
   tactical tool, and cycling applies again.
4. **Slot 8, a key of its own.** GZDoom binds 1-0 to `slot 1`…`slot 0` by
   default (gzdoom.pk3 g4.14.2 `engine/commonbinds.txt`, read 2026-10-23:
   `8 "slot 8"`), so the key exists on every fresh install and nothing has
   to be bound. Doom's seven weapons never used it. Cost: status bar A's
   ARMS panel shows slots 2-7 only, so the grenade has no digit there
   (nor does the ice axe in slot 1 today).
5. **A quick-throw key** (throw without raising the grenade, as modern
   shooters do): a `+user1` button read in `SD_Player` or an event
   handler. No default binding (the player would have to find it in the
   controls menu), no hand animation, and a code path no other weapon has.

**Pool.**

1. **Share `RocketAmmo`** with the RPG-7: the grenades would eat PG-7V
   rounds and the reverse; no fiction for it.
2. **A pool of our own, `SD_Rgd5Ammo : Ammo`**, which is also the loose
   grenade's pickup (as Doom's `Clip` is both), with a crate deriving from it.

**The fuse.**

1. **Strife's pattern:** `ReactionTime` counted down by `A_Countdown`, the
   burst in `Death`. But a bouncing missile also enters `Death` when it
   stops bouncing (`BounceType "Doom"` turns bouncing off once it is slow;
   the next floor contact goes through `P_ExplodeMissile`), so Strife's
   grenade bursts the moment it comes to rest, a timed impact grenade.
2. **Our own counter:** `Death` means "stopped" and keeps the fuse
   burning; the burst is a state of its own, `Detonate`, reached only when
   the fuse has burned out.

**A loose grenade.**

1. **Ammo only:** a loose grenade fills the pool; the weapon comes only from
   the pouch (21009). A player who finds three loose grenades first cannot
   throw any.
2. **The grenade is the weapon too:** `SD_Rgd5Ammo.TryPickup` takes the
   ammunition by the engine's rules, then, if the toucher has no `SD_Rgd5`,
   gives him one with `AmmoGive1 = 0` through `CallTryPickup` (the engine's
   own `GiveInventory` pattern).

## Decision

- **Key: option 4, slot 8.** One press, always the grenade. `SD_Player`
  declares `Player.WeaponSlot 8, "SD_Rgd5"` and the class carries
  `Weapon.SlotNumber 8`. Option 5 stays an idea for later (it can be added
  on top of slot 8 without changing it).
- **Pool: option 2, `SD_Rgd5Ammo`.** ADR 011's rule is widened: **a new
  weapon gets a pool of its own when it fires another cartridge and
  sharing would retire a weapon, or when it fires no cartridge at all (a
  thrown weapon is its own ammunition); the reason goes in an ADR.** The
  class lives in `zscript/weapons/rgd5_ammo.zs`, not `zscript/sd/ammo.zs`
  (ADR 011's test holds `SD_AkmAmmo` as the only direct `Ammo` child *of
  that file*, and the grenade's pool belongs with the weapon). Amount 1,
  maximum 6, backpack 0 and 12 (a backpack that handed out a grenade with
  no weapon to throw it would read as a bug), the crate 4.
- **Fuse: option 2.** `SD_Rgd5Grenade` counts `burnt` up each tic in both
  `Spawn` (flying) and `Death` (stopped) and jumps to `Detonate` at 60 tics
  (1.71 s from the throw). Strife's flags otherwise: `BounceType "Doom"`,
  `+BOUNCEONACTORS`, `-NOGRAVITY`, `MaxStepHeight 4`; no impact damage.
- **A loose grenade: option 2.** The crate inherits it.
- **Never raised by itself:** `+WEAPON.NO_AUTO_SWITCH` (not on pickup),
  `+WEAPON.NOAUTOSWITCHTO` (not when a grenade is picked up with an empty
  gun), `SelectionOrder 4000` (after the ice axe's 3700 when every gun is
  dry), `+WEAPON.NOAUTOFIRE` and no `A_ReFire` (one press, one throw).
- **Editor numbers:** **21009** `SD_Rgd5` (the pouch of two), **21021**
  `SD_Rgd5Ammo`, **21022** `SD_Rgd5Box` (MOD-SPEC §6.1; checked free in
  `MAPINFO`, `tools/` and every map on 2026-10-23).

## Consequences

- The arsenal is nine weapons in eight slots. `docs/product/LORE.md`'s
  arsenal table needs a row (Product's, not this ADR's).
- **The grenade count shows only while it is held** (the big AMMO number);
  bar A lists Doom's four pools, as for the AKM (ADR 011). The fullscreen
  HUD is expected to list the pool with its icon. **NOT VERIFIED.** A row
  on bar A is debt for `art-director` + `mod-engineer`.
- The three bosses have `+NORADIUSDMG`: grenades do nothing to them, by
  design (BALANCE §3, slot 8). Level designers should not count grenades
  for a boss's stage (BALANCE §8.1).
- Provisional look (MOD-SPEC §6.12): in hand the ice axe's frames, on the
  floor the health bonus's flask and the PG-7V crate, tinted gunmetal; the
  final names `SDRG`, `SDRQ`, `SDRJ`, `SDRZ`, `SDRN`. Sounds reuse shipped
  lumps under their own names (`sd/weapon/rgd5/*`, MOD-SPEC §6.2).
- `tests/test_rgd5.py` pins the classes, numbers, slot, flags, fuse,
  balance, swaps, sounds, strings and these documents.

## Verification (the PM, D26)

The design doc §9 has the checks R1–R12 (`give SD_Rgd5`, `summon
SD_Rgd5Ammo`, a throw on the flat and round a corner, the fuse at rest, the
blast on a group of `SD_LegionTrooper`s, the self-damage, a boss untouched,
the backpack, the three languages, the log).
