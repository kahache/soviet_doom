// SD_Rpg7 - slot 5, the RPG-7 rocket-propelled grenade launcher.
//
// Replaces Doom's RocketLauncher and keeps the RocketAmmo pool. Fires
// SD_Pg7Grenade: more damage on a direct hit, a tighter blast, and a
// noticeably slower reload than Doom's launcher.
//
// Sprites. The world pickup is ours since D48 (2026-10-14): SDRP A (was
// the IWAD's LAUN). The held frames SDRL A-B and the flash SDRF A-D since
// D84 (2026-10-20), built from the CEO's Google Gemini pair by
// tools/art/gemini_frames.py; only the four-letter names changed, every
// tic, action and jump is as it was. All in assets/sprites/rpg7/.
// MOD-SPEC 6.3; tests/test_gemini_weapons_install.py. The PG-7V in flight
// and its burst still wear the IWAD's MISL (pg7_grenade.zs, MOD-SPEC 5.1).
// Balance rationale: docs/engine/BALANCE.md.

class SD_Rpg7 : RocketLauncher replaces RocketLauncher
{
	const SD_RPG7_AMMO_USE  = 1;
	const SD_RPG7_AMMO_GIVE = 2;   // the tube plus one spare round, as in Doom

	Default
	{
		Weapon.SelectionOrder 2500;
		Weapon.AmmoUse SD_RPG7_AMMO_USE;
		Weapon.AmmoGive SD_RPG7_AMMO_GIVE;
		Weapon.AmmoType "RocketAmmo";
		Weapon.SlotNumber 5;
		+WEAPON.NOAUTOFIRE   // one press, one round: no holding the trigger
		+WEAPON.EXPLOSIVE
		Obituary "$SD_OB_RPG7";
		Tag "$SD_TAG_RPG7";
		Inventory.PickupMessage "$SD_PICKUP_RPG7";
		Inventory.PickupSound "sd/weapon/rpg7/pickup";   // SDRPPKP (N9, D74)
	}

	States
	{
	Ready:
		SDRL A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDRL A 1 A_Lower;
		Loop;
	Select:
		SDRL A 1 A_Raise;
		Loop;
	Fire:
		// 8 + 4 + 10 + 4 = 26 tics per round (Doom RocketLauncher: 20): the
		// RPG-7 is reloaded from the muzzle, one grenade at a time. The 14-tic
		// launch frame is split 4 + 10 (N9) so the reload is heard once the
		// round has left: same sprite, same total, nothing else in between.
		// The launch sound is the grenade's SeeSound, so CHAN_WEAPON is free.
		SDRL B 8 A_GunFlash;
		SDRL B 4 A_FireProjectile("SD_Pg7Grenade");
		SDRL B 10 A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON);
		SDRL B 4 A_ReFire;
		Goto Ready;
	Flash:
		SDRF A 3 Bright A_Light1;
		SDRF B 4 Bright;
		SDRF CD 4 Bright A_Light2;
		Goto LightDone;
	Spawn:
		SDRP A -1;
		Stop;
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDRPDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	action void A_SD_WeaponReady()
	{
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/rpg7/dry");
		A_WeaponReady();
	}
}
