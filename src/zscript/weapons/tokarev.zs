// SD_Tokarev - slot 2, the TT-33 Tokarev service pistol (7.62x25 mm).
//
// Replaces Doom's Pistol and is the sergeant's starting sidearm. Keeps the
// Clip ammo type: the TT-33 and the PPSh-41 historically fire the same
// 7.62x25 Tokarev cartridge, so one ammo pool is also the accurate choice.
//
// Sprites, all ours (assets/sprites/tt33/). The world pickup SDTP A since
// D48 (2026-10-14). The held frames SDTT A-C and the muzzle flash SDTF A
// since N17 (2026-10-15), redone with Gemini in D111 (2026-10-23): the
// project lead's Gemini pair processed by tools/art/gemini_frames.py like
// the other six weapons (bare hand, the arsenal's scale), in place of the
// D61 set (our TT-33 in Freedoom's recoloured pistol hands). Both sets
// replaced their predecessors letter for letter: never a tic, an action or
// the flow. MOD-SPEC 6.3.
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
		Inventory.PickupSound "sd/weapon/tokarev/pickup";  // SDTTPKP1/2 $random (N9e, D94)
		+WEAPON.WIMPY_WEAPON
	}

	States
	{
	Ready:
		SDTT A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDTT A 1 A_Lower;
		Loop;
	Select:
		SDTT A 1 A_Raise;
		Loop;
	Fire:
		// 4 + 6 + 3 + 3 = 16 tics per shot = 2.19 shots/s (Doom Pistol: 19 tics).
		SDTT A 4;
		SDTT B 0 A_GunFlash;
		SDTT B 6 A_FireBullets(SD_TT_SPREAD, 0, SD_TT_BULLETS, SD_TT_DAMAGE);
		SDTT C 3;
		SDTT B 3 A_ReFire;
		Goto Ready;
	Flash:
		SDTF A 5 Bright A_Light1;
		Goto LightDone;
	Spawn:
		SDTP A -1;
		Stop;
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDTTDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	action void A_SD_WeaponReady()
	{
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/tokarev/dry");
		A_WeaponReady();
	}
}
