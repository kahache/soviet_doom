// SD_Ppsh - slot 4, the PPSh-41 submachine gun. The icon of the mod.
//
// Replaces Doom's Chaingun. 71-round drum, 7.62x25 mm (same Clip pool as the
// TT-33). The real gun cycles at roughly 900 rounds per minute; the engine
// runs at 35 tics per second, so 3 tics per round (700 rpm) is the closest
// honest value that does not make slot 4 outclass everything after it.
//
// Sprites. The world pickup is ours since D48 (2026-10-14); the held and
// flash frames stay Freedoom (IWAD) PLACEHOLDERS until the hand is redrawn
// (the CEO found hand E deformed in MAP01, 2026-10-14). MOD-SPEC 5.1, 6.3.
// Held CHGG (final SDPP A-B), flash CHGF (final SDPF A-B). Pickup: SDPQ A
// (assets/sprites/ppsh/; was MGUN).
// Balance rationale: docs/engine/BALANCE.md.

class SD_Ppsh : Chaingun replaces Chaingun
{
	// --- Balance constants -------------------------------------------------
	// Reference: Doom's Chaingun is 5 x random(1,3) (avg 10) every 4 tics
	// = 87.5 damage/s. The PPSh trades per-round punch for rate of fire and
	// burns the magazine pool much faster.
	const SD_PPSH_DAMAGE    = 4;    // x random(1,3) -> 4..12, avg 8
	const SD_PPSH_SPREAD    = 7.0;  // degrees; an SMG is looser than a chaingun
	const SD_PPSH_BULLETS   = 1;    // 1 = the first round of a burst is pinpoint
	const SD_PPSH_AMMO_USE  = 1;
	const SD_PPSH_AMMO_GIVE = 35;   // half of a captured 71-round drum

	Default
	{
		Weapon.SelectionOrder 700;
		Weapon.AmmoUse SD_PPSH_AMMO_USE;
		Weapon.AmmoGive SD_PPSH_AMMO_GIVE;
		Weapon.AmmoType "Clip";
		Weapon.SlotNumber 4;
		AttackSound "sd/weapon/ppsh/fire";
		Obituary "$SD_OB_PPSH";
		Tag "$SD_TAG_PPSH";
		Inventory.PickupMessage "$SD_PICKUP_PPSH";
	}

	States
	{
	Ready:
		CHGG A 1 A_WeaponReady;
		Loop;
	Deselect:
		CHGG A 1 A_Lower;
		Loop;
	Select:
		CHGG A 1 A_Raise;
		Loop;
	Fire:
		// 3 tics per round = 11.67 rounds/s ~ 700 rpm (Doom Chaingun: 4 tics).
		CHGG A 0 A_GunFlash;
		CHGG A 3 A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE);
		CHGG B 0 A_GunFlash;
		CHGG B 3 A_FireBullets(SD_PPSH_SPREAD, 0, SD_PPSH_BULLETS, SD_PPSH_DAMAGE);
		CHGG B 0 A_ReFire;
		Goto Ready;
	Flash:
		CHGF A 3 Bright A_Light1;
		Goto LightDone;
	Spawn:
		SDPQ A -1;
		Stop;
	}
}
