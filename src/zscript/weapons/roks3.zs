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
// MOD-SPEC 6.3; tests/test_gemini_weapons_install.py. The flame in flight
// still wears the IWAD's PLSS / PLSE (flame_blob.zs, MOD-SPEC 5.1).
// Balance rationale: docs/engine/BALANCE.md.

class SD_Roks3 : PlasmaRifle replaces PlasmaRifle
{
	// Reference: Doom's PlasmaRifle fires one PlasmaBall (avg 22.5) every 3
	// tics = ~262 damage/s at unlimited range. The ROKS-3 fires at the same
	// rate for roughly 60% of that, and only reaches 528 map units.
	const SD_ROKS3_SPREAD    = 4.0;   // degrees of random cone per jet
	const SD_ROKS3_AMMO_USE  = 1;     // one fuel unit per jet
	const SD_ROKS3_AMMO_GIVE = 40;    // same as Doom's plasma rifle pickup
	const SD_ROKS3_NOZZLE_X  = 6.0;   // the nozzle sits right of centre
	const SD_ROKS3_NOZZLE_Z  = 0.0;   // at the standard attack height

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
		SDRK A 0 A_GunFlash;
		SDRK A 3 Bright A_SD_FireRoks3;
		SDRK B 20 A_ReFire;
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
	action void A_SD_WeaponReady()
	{
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/roks3/dry");
		A_WeaponReady();
	}
}
