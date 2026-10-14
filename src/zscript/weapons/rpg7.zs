// SD_Rpg7 - slot 5, the RPG-7 rocket-propelled grenade launcher.
//
// Replaces Doom's RocketLauncher and keeps the RocketAmmo pool. Fires
// SD_Pg7Grenade: more damage on a direct hit, a tighter blast, and a
// noticeably slower reload than Doom's launcher.
//
// Sprites. The world pickup is ours since D48 (2026-10-14); the held and
// flash frames stay Freedoom (IWAD) PLACEHOLDERS until the hand is redrawn
// (the CEO found hand E deformed in MAP01, 2026-10-14). MOD-SPEC 5.1, 6.3.
// Held MISG (final SDRL A-B), flash MISF (final SDRF A-D). Pickup: SDRP A
// (assets/sprites/rpg7/; was LAUN). The PG-7V in flight and its burst
// still wear MISL (pg7_grenade.zs).
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
		MISG A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		MISG A 1 A_Lower;
		Loop;
	Select:
		MISG A 1 A_Raise;
		Loop;
	Fire:
		// 8 + 4 + 10 + 4 = 26 tics per round (Doom RocketLauncher: 20): the
		// RPG-7 is reloaded from the muzzle, one grenade at a time. The 14-tic
		// launch frame is split 4 + 10 (N9) so the reload is heard once the
		// round has left: same sprite, same total, nothing else in between.
		// The launch sound is the grenade's SeeSound, so CHAN_WEAPON is free.
		MISG B 8 A_GunFlash;
		MISG B 4 A_FireProjectile("SD_Pg7Grenade");
		MISG B 10 A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON);
		MISG B 4 A_ReFire;
		Goto Ready;
	Flash:
		MISF A 3 Bright A_Light1;
		MISF B 4 Bright;
		MISF CD 4 Bright A_Light2;
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
