# ADR 011 — The AKM gets an ammunition pool of its own

Date: 2026-10-22. Status: accepted (D116), **not yet seen in the engine**
(the PM's batched engine pass, D26). Owner: `mod-engineer`. Amends
`docs/engine/MOD-SPEC.md` §6.4 ("the mod creates no new ammo pools") and
ADR 003's premise that the four Doom pools are all the arsenal needs. The
design and the numbers are `docs/engine/2026-10-22_P4_akm.md` §3; the
balance rows are `BALANCE.md` §2-§4.

## Context

D112 asked for more weapons; the first is the AKM, slot 4's second gun
beside the PPSh-41. D116 (2026-10-22) put it in the mod on provisional
sprites. A weapon needs a pool. MOD-SPEC §6.4 said the mod creates none:
the four Doom pools (`Clip`, `Shell`, `RocketAmmo`, `Cell`) were exactly
the four the seven weapons of D13 needed, and every ammo class of ours
subclassed one of them so that `Ammo.GetParentAmmo()` kept Doom's pool
(ADR 003).

## Options

1. **Share `Clip` with the TT-33 and the PPSh-41.** No new actor, no new
   number, the status bar unchanged. But `Clip` is shared *because* the
   pistol and the sub-machine gun fire the same 7.62×25 Tokarev round
   (BALANCE §4); the AKM fires 7.62×39. And from one pool the AKM's 12 a
   round (105 DPS) beats the PPSh-41's 8 (93.3 DPS) on every count: nobody
   would raise the PPSh again.
2. **Share another Doom pool** (`Shell`, `Cell`). No reason in the fiction,
   and it would tie the AKM to the IZh-58 or the flamethrower's economy.
3. **A pool of its own, `SD_AkmAmmo : Ammo`.** One actor that is both the
   pool and its 30-round magazine pickup (as Doom's `Clip` is), one editor
   number, two strings per language, one sprite to draw.

## Decision

**Option 3.** `SD_AkmAmmo` derives from `Ammo` directly, in
`zscript/sd/ammo.zs` beside the nine renamed Doom pickups: amount 30 (one
magazine), maximum 150 (five), the backpack's 30 and 300 by Doom's rule.
Editor number **21020**, the first of the ammo-and-items block 21020–21039
(MOD-SPEC §6.1); the mod's other ammunition keeps Doom's numbers through
`replaces`. Strings `SD_AMMO_AKM` (the pool's Tag) and `SD_GOT_AKMMAG`
(the pickup line) in English, Russian and Catalan; both are `SD_` ids, so
Freedoom's DEHACKED cannot override them (ADR 003's lesson). The Legion
gunner drops it (15 rounds, half a magazine: `Ammo.ModifyDropAmount`).

The rule in MOD-SPEC §6.4 becomes: **the seven weapons of D13 use the four
Doom pools; a new weapon gets a pool of its own only when it fires another
cartridge and sharing would retire a weapon, and the reason is written in
an ADR.** ADR 003's warning stands for every other class: never re-parent a
Doom pickup subclass to `Ammo`.

## Consequences

- The PPSh-41 is the abundant gun (every rifleman's clip feeds it), the AKM
  the scarce, efficient one; level-designer counts its magazines per map
  (the AKM doc §6) and `tools/route.py`'s ammunition budget will need the
  pool when a map places it.
- **Status bar A shows no fifth row.** Its ammunition table lists Doom's
  four pools; the AKM's rounds show in the big AMMO number while it is held
  (`DoomStatusBar` draws the current weapon's ammo) and in the fullscreen
  HUD with the pickup's icon. **NOT VERIFIED in the engine.** A fifth row is
  an art change plus a `SD_StatusBar` change, debt for later (the AKM doc
  §8).
- Provisional look (MOD-SPEC §6.12): the pickup is the 7.62×25 magazine's
  `SDCL A`, tinted; the HUD icon is `SDCLA0` untinted; the final sprite is
  `SDAM A`.
- `tests/test_akm.py` pins the class, the parent, the number, the strings
  and that `SD_AkmAmmo` is the only class in `ammo.zs` that derives from
  `Ammo` directly.

## Verification (the PM, D26)

`give SD_Akm` (30 rounds), `summon SD_AkmAmmo` and walk onto it ("An AKM
magazine. 7.62x39.", +30, `printinv` lists `SD_AkmAmmo`), `give backpack`
(+30, cap 300), kill a `summon SD_LegionGunner` (a magazine drops, +15),
and the log shows nothing about `ammo.zs` or `SD_AkmAmmo`. The AKM doc §9
has the full list (A1–A9).
