// SD_Tokarev - slot 2, the TT-33 Tokarev service pistol (7.62x25 mm).
//
// Replaces Doom's Pistol and is the sergeant's starting sidearm. Keeps the
// Clip ammo type: the TT-33 and the PPSh-41 historically fire the same
// 7.62x25 Tokarev cartridge, so one ammo pool is also the accurate choice.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: PISG (held), PISF (muzzle flash),
// PIST (pickup). Final lumps: SDTT A-E, SDTF A, SDTP A.
// Balance rationale: docs/engine/BALANCE.md.

class SD_Tokarev : Pistol replaces Pistol
{
	// --- Balance constants -------------------------------------------------
	// Reference: Doom's Pistol is 5 x random(1,3) (5..15, avg 10) every 19
	// tics while held. The TT-33 is a high-velocity single-action pistol:
	// a little more damage, a little tighter, a slightly shorter cycle.
	const SD_TT_DAMAGE    = 6;    // x random(1,3) -> 6..18, avg 12
	const SD_TT_SPREAD    = 4.5;  // degrees; Doom's hitscan spread is 5.625
	const SD_TT_BULLETS   = 1;    // 1 = the first shot of a burst is pinpoint
	const SD_TT_AMMO_USE  = 1;
	const SD_TT_AMMO_GIVE = 20;   // a dropped TT with two spare magazines

	Default
	{
		Weapon.SelectionOrder 1900;
		Weapon.AmmoUse SD_TT_AMMO_USE;
		Weapon.AmmoGive SD_TT_AMMO_GIVE;
		Weapon.AmmoType "Clip";
		Weapon.SlotNumber 2;
		// A_FireBullets plays the weapon's AttackSound on the weapon channel
		// only when the shot actually happens, so the sound goes here rather
		// than in a separate A_StartSound.
		AttackSound "sd/weapon/tokarev/fire";
		Obituary "$SD_OB_TOKAREV";
		Tag "$SD_TAG_TOKAREV";
		Inventory.PickupMessage "$SD_PICKUP_TOKAREV";
		+WEAPON.WIMPY_WEAPON
	}

	States
	{
	Ready:
		PISG A 1 A_WeaponReady;
		Loop;
	Deselect:
		PISG A 1 A_Lower;
		Loop;
	Select:
		PISG A 1 A_Raise;
		Loop;
	Fire:
		// 4 + 6 + 3 + 3 = 16 tics per shot = 2.19 shots/s (Doom Pistol: 19 tics).
		PISG A 4;
		PISG B 0 A_GunFlash;
		PISG B 6 A_FireBullets(SD_TT_SPREAD, 0, SD_TT_BULLETS, SD_TT_DAMAGE);
		PISG C 3;
		PISG B 3 A_ReFire;
		Goto Ready;
	Flash:
		PISF A 5 Bright A_Light1;
		Goto LightDone;
	Spawn:
		PIST A -1;
		Stop;
	}
}
