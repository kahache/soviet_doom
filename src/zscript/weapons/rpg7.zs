// SD_Rpg7 - slot 5, the RPG-7 rocket-propelled grenade launcher.
//
// Replaces Doom's RocketLauncher and keeps the RocketAmmo pool. Fires
// SD_Pg7Grenade: more damage on a direct hit, a tighter blast, and a
// noticeably slower reload than Doom's launcher.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: MISG (held), MISF (flash),
// LAUN (pickup). Final lumps: SDRL A-B, SDRF A-D, SDRP A.
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
	}

	States
	{
	Ready:
		MISG A 1 A_WeaponReady;
		Loop;
	Deselect:
		MISG A 1 A_Lower;
		Loop;
	Select:
		MISG A 1 A_Raise;
		Loop;
	Fire:
		// 8 + 14 + 4 = 26 tics per round (Doom RocketLauncher: 20): the RPG-7
		// is reloaded from the muzzle, one grenade at a time.
		MISG B 8 A_GunFlash;
		MISG B 14 A_FireProjectile("SD_Pg7Grenade");
		MISG B 4 A_ReFire;
		Goto Ready;
	Flash:
		MISF A 3 Bright A_Light1;
		MISF B 4 Bright;
		MISF CD 4 Bright A_Light2;
		Goto LightDone;
	Spawn:
		LAUN A -1;
		Stop;
	}
}
