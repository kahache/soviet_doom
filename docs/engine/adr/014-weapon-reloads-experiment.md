# ADR 014 — Weapon reloads with no new art: a counter, a mixin and a CVar

Date: 2026-10-25. Status: **experiment on the branch `v3-reload`**, for the
CEO to play with and without and then keep or drop (D132; a nice to have,
D121); not in v1.2, **not yet seen in the engine** (D26). Owner:
`mod-engineer`. Amends D-004-2 of ADR 004 (the mod declared no CVar of its
own) and pays debt T7 (MOD-SPEC §10). Design and engine checks:
`docs/engine/2026-10-25_V3_reloads.md`; numbers: `BALANCE.md` §10;
contract: `MOD-SPEC.md` §6.15.

## Context

D47 parked reloads so D39's balance would stand; the reload sounds of the
TT-33, the PPSh-41 and the ROKS-3 were recorded (D74) and packed unused.
D132 asked to explore reloads if Gemini's quota allowed reload frames. It
does not until tomorrow, so the brief became: magazines for the guns the
Icebox names (and the AKM if it fits), a saved per-weapon state, an
automatic reload and a reload key, an animation made of the existing frame
lowered and raised, realistic durations, a CVar the CEO can flip in the
mod's menu, and the maps' ammunition untouched.

## Decisions

### D-014-1 — A magazine is a counter over the existing pool

Options: (a) a second ammo class per gun as the magazine (`AmmoType2`,
the usual GZDoom reload mod), the reserve moved into it on reload; (b) a
counter on the weapon of rounds fired since the last reload, the rounds
still taken from the pool.

**(b).** It creates, loses and moves no ammunition, so the maps' budgets
(`BALANCE.md` §8), the status bar's AMMO number and every pickup stay as
they are; turning the CVar off at any moment needs no conversion back; and
the TT-33 and the PPSh-41 keep sharing `Clip`. The price: the loaded count
is "capacity minus fired, never more than the pool", so a gun can show a
magazine the other gun has partly spent. Option (a) would need new ammo
classes, a status bar row per gun, and a rule for what the CVar does to
rounds already in a magazine.

### D-014-2 — The count lives in `DepleteAmmo`, the jumps in three places

The counter is raised in an override of `Weapon.DepleteAmmo`, which
`A_FireBullets` and `A_FireProjectile` call for every shot (gzdoom.pk3
g4.14.2 `weapons.zs`): no Fire frame changes for the counting. The jumps
to `Reload` are a 0-tic guard as the first Fire frame (and before the
PPSh-41's second round), the Ready function (a dry magazine reloads at
once, unless a weapon switch is pending), and the engine's own `+reload`
button through `WRF_ALLOWRELOAD`, passed only when a reload would load.
Rejected: making `CheckAmmo` report "no ammo" on a dry magazine. It stops
the shot with no state change, but the engine also asks `CheckAmmo` when
choosing weapons (slot keys, `PickNewWeapon`), and a gun with a dry
magazine would become unselectable.

### D-014-3 — One mixin for four unrelated classes

The four guns derive from Pistol, Chaingun, DoomWeapon and PlasmaRifle, so
they share no base to add fields to. A `mixin class` (ZScript: its body is
copied into each class that names it) carries the two fields, the helpers
and the override once. Every helper takes the capacity as an argument, so
the mixin does not rely on names the including class defines; the HUD
finds each gun's capacity by its class. The fields are ordinary fields and
go into saved games; zero is a full magazine, so a weapon needs no
initialisation and older saves load full.

### D-014-4 — The animation is the switch's, the sound while out of sight

No frames (D132). The `Reload` state repeats the gun's ready frame one tic
at a time, setting its height with `A_WeaponOffset(0, y,
WOF_INTERPOLATE)`: down from 32 to 128 (the engine's WEAPONTOP and
WEAPONBOTTOM), out of sight, back up. Each gun's reload sound is started
so its loudest moment (slide, bolt, igniter) lands as the gun comes back
up; the magazine fills on that tic. Not `A_Lower`/`A_Raise`: at the bottom
`A_Lower` brings up the pending weapon (gzdoom.pk3 `weapons.zs`), which is
a weapon switch, not a reload.

### D-014-5 — `sd_reloads`, the mod's first CVar

`server bool sd_reloads = true` in a new `CVARINFO`: a gameplay setting,
archived in the player's ini like the engine's own. D-004-2 kept the mod's
footprint in the player's config at one key (`language`); this adds a
second, by request, and only on this branch. The menu row is the engine's
own `Option` with its `OnOff` list, so the write happens during menu input
(D-004-4). On by default here so the CEO plays it first; if it ships, the
default is the CEO's call. `KEYCONF` suggests R with `defaultbind`, which
never overrides a binding the player has.

### D-014-6 — A readout as an event handler

The player needs to see the magazine; there are no frames to show it. A
"rounds/capacity" line drawn by `SD_MagazineHud`, an `EventHandler`,
rather than a third override in `SD_StatusBar` (ADR 010 pins its two):
the experiment comes out by deleting one name from MAPINFO.

## Consequences

- With `sd_reloads 0` every gun's tics are v1.2's; the tests pin that the
  guards are the only Fire edits.
- Sustained DPS falls 25-37 % and slot 4 drops under the IZh-58
  (`BALANCE.md` §10): the CEO's call after playing.
- New engine features the pass must see work (D26): a mixin with an
  `override` and `action` functions, `defaultbind` in KEYCONF,
  `CVar.FindCVar` on a mod CVar, `A_WeaponOffset` with `WOF_INTERPOLATE`,
  a state-returning `A_SD_WeaponReady`.
- If the CEO drops it: delete `magazine.zs`, `magazine_hud.zs`, `CVARINFO`,
  `KEYCONF`, the mixin lines, guards and `Reload` blocks, the menu row and
  its strings, and restore the three "PARKED" SNDINFO comments.
