// SD_Roks3 - slot 6, the ROKS-3 backpack flamethrower.
//
// Replaces Doom's PlasmaRifle and keeps the Cell ammo pool, which the mod
// reads as pressurised fuel canisters (the Hand Katyusha draws on the same
// pool, exactly as Doom's plasma rifle and BFG share cells).
//
// Sprites. The world pickup is ours since D48 (2026-10-14): SDKP A (was
// the IWAD's PLAS). The held frames SDRK A-B and the flame at the nozzle
// SDKF A since D84 (2026-10-20), built from the CEO's Google Gemini pair by
// tools/art/gemini_frames.py; only the four-letter names changed, every
// tic, action and jump is as it was. All in assets/sprites/roks3/.
// MOD-SPEC 6.3; tests/test_gemini_weapons_install.py. The flame is ours
// too since D82: SDFJ in flight, SDFX on impact (flame_blob.zs).
// Balance rationale: docs/engine/BALANCE.md.
//
// V3 reloads (D132, the CVar sd_reloads; magazine.zs): the backpack's fuel
// tank, emptied jet by jet and swapped for a fresh canister. Off, every
// frame below runs exactly as in v1.2: the guards only jump when reloads
// are on.

class SD_Roks3 : PlasmaRifle replaces PlasmaRifle
{
	mixin SD_MagazineWeapon;   // the tank counter and the reload (magazine.zs)

	// Reference: Doom's PlasmaRifle fires one PlasmaBall (avg 22.5) every 3
	// tics = ~262 damage/s at unlimited range. The ROKS-3 fires at the same
	// rate for 60% of that since D119 (157.5/s, the jet's damage is
	// SD_FLAME_DAMAGE in flame_blob.zs; 80% before), and only reaches 528
	// map units. The cadence stays 3 tics: the fire sound's jet loop is cut
	// to exactly 3 tics (tools/audio/gen_weapon_alts.py).
	const SD_ROKS3_SPREAD    = 4.0;   // degrees of random cone per jet
	const SD_ROKS3_AMMO_USE  = 1;     // one fuel unit per jet
	const SD_ROKS3_AMMO_GIVE = 40;    // same as Doom's plasma rifle pickup
	const SD_ROKS3_NOZZLE_X  = 6.0;   // the nozzle sits right of centre
	const SD_ROKS3_NOZZLE_Z  = 0.0;   // at the standard attack height

	// --- Reload (V3 experiment, docs/engine/2026-10-25_V3_reloads.md) -----
	// The real ROKS-3 carried some 6-8 s of fire; 80 jets is 6.9 s at 11.67
	// a second, enough for the heaviest Panzermensch (75 jets, BALANCE.md
	// section 3) on one tank.
	const SD_ROKS3_TANK             = 80;
	const SD_ROKS3_RELOAD_TICS      = 88;  // 2.5 s: canister knocked in, coupling turned, igniter armed
	const SD_ROKS3_RELOAD_DROP      = 16;  // tics down, and up again
	// SDRKRLD (1.05 s) arms the igniter at 0.88 s = 31 tics; started on tic
	// 41 it does so as the nozzle comes back up (tic 72).
	const SD_ROKS3_RELOAD_SOUND_TIC = 41;

	Default
	{
		Weapon.SelectionOrder 100;
		Weapon.AmmoUse SD_ROKS3_AMMO_USE;
		Weapon.AmmoGive SD_ROKS3_AMMO_GIVE;
		Weapon.AmmoType "Cell";
		Weapon.SlotNumber 6;
		Obituary "$SD_OB_ROKS3";
		Tag "$SD_TAG_ROKS3";
		Inventory.PickupMessage "$SD_PICKUP_ROKS3";
		Inventory.PickupSound "sd/weapon/roks3/pickup";  // SDRKPKP (N9, D74)
	}

	States
	{
	Ready:
		SDRK A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDRK A 1 A_Lower;
		Loop;
	Select:
		SDRK A 1 A_Raise;
		Loop;
	Fire:
		// 3 tics per jet while the trigger is held (same as Doom's plasma);
		// A_ReFire fires on entry to the next state, so the 20-tic frame is
		// only paid when the player lets go.
		// V3: an empty tank reloads instead (0 tics; never with reloads off).
		SDRK A 0 A_JumpIf(invoker.SD_MagazineDry(SD_ROKS3_TANK), "Reload");
		SDRK A 0 A_GunFlash;
		SDRK A 3 Bright A_SD_FireRoks3;
		SDRK B 20 A_ReFire;
		Goto Ready;
	Reload:
		// V3 (magazine.zs): the gun goes down off screen and comes back up,
		// 88 tics, the tank full again as it rises.
		SDRK A 0 A_JumpIf(!invoker.SD_CanReload(SD_ROKS3_TANK), "Ready");
		SDRK A 0 A_SD_BeginReload;
	ReloadLoop:
		SDRK A 1 A_SD_ReloadTick(SD_ROKS3_TANK, SD_ROKS3_RELOAD_TICS, SD_ROKS3_RELOAD_DROP, SD_ROKS3_RELOAD_SOUND_TIC, "sd/weapon/roks3/reload");
		SDRK A 0 A_JumpIf(invoker.sdReloadTic < SD_ROKS3_RELOAD_TICS, "ReloadLoop");
		Goto Ready;
	Flash:
		SDKF A 3 Bright A_Light1;
		Goto LightDone;
	Spawn:
		SDKP A -1;
		Stop;
	}

	action void A_SD_FireRoks3()
	{
		A_StartSound("sd/weapon/roks3/fire", CHAN_WEAPON);
		A_FireProjectile(
			"SD_FlameBlob",
			frandom[SDRoks3](-SD_ROKS3_SPREAD, SD_ROKS3_SPREAD),
			true,
			SD_ROKS3_NOZZLE_X,
			SD_ROKS3_NOZZLE_Z);
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDRKDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	// V3 reloads, both no-ops with sd_reloads off: an empty tank is swapped at
	// once (unless a weapon switch is pending), and the +reload key is
	// allowed when a reload would load.
	action state A_SD_WeaponReady()
	{
		if (player != null && player.PendingWeapon == WP_NOCHANGE
			&& invoker.SD_MagazineDry(SD_ROKS3_TANK))
		{
			return ResolveState("Reload");
		}
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/roks3/dry");
		A_WeaponReady(invoker.SD_ReadyFlags(SD_ROKS3_TANK));
		return null;
	}
}
