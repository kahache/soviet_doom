// SD_Roks3 - slot 6, the ROKS-3 backpack flamethrower.
//
// Replaces Doom's PlasmaRifle and keeps the Cell ammo pool, which the mod
// reads as pressurised fuel canisters (the Hand Katyusha draws on the same
// pool, exactly as Doom's plasma rifle and BFG share cells).
//
// Sprites. The world pickup is ours since D48 (2026-10-14); the held and
// flash frames stay Freedoom (IWAD) PLACEHOLDERS until the hand is redrawn
// (the CEO found hand E deformed in MAP01, 2026-10-14). MOD-SPEC 5.1, 6.3.
// Held PLSG (final SDRK A-B), flash PLSF (final SDKF A-B). Pickup: SDKP A
// (assets/sprites/roks3/; was PLAS). The flame in flight still wears
// PLSS / PLSE (flame_blob.zs).
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
	}

	States
	{
	Ready:
		PLSG A 1 A_WeaponReady;
		Loop;
	Deselect:
		PLSG A 1 A_Lower;
		Loop;
	Select:
		PLSG A 1 A_Raise;
		Loop;
	Fire:
		// 3 tics per jet while the trigger is held (same as Doom's plasma);
		// A_ReFire fires on entry to the next state, so the 20-tic frame is
		// only paid when the player lets go.
		PLSG A 0 A_GunFlash;
		PLSG A 3 Bright A_SD_FireRoks3;
		PLSG B 20 A_ReFire;
		Goto Ready;
	Flash:
		PLSF A 3 Bright A_Light1;
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
}
