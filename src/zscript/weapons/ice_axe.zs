// SD_IceAxe - slot 1, the ice axe (piolet, "ledorub"), D40.
//
// Until 2026-10-13 this slot was the sapper's shovel (SD_Shovel). The CEO
// replaced it with an ice axe, knowing the Mercader association (docs/PRD.md
// D40). It is a rename, not a new weapon: the numbers are the shovel's
// (docs/engine/BALANCE.md section 4), the editor number is still 21001, so
// both maps keep working, and it is still found on MAP01's dorm rack.
//
// Replaces Doom's Fist. A "Weapon" in GZDoom is an inventory actor that owns
// a set of HUD-sprite states (Ready / Select / Deselect / Fire); the engine
// runs those states on the player's weapon layer. `replaces Fist` tells the
// engine to hand out this class wherever the game would have given a Fist,
// so Freedoom's melee weapon never shows up.
//
// Sprites, all ours. The pickup since D48 (2026-10-14): SDAP A, option C,
// upright as in a rack (was CSAW, Freedoom's chainsaw). The held frames
// SDAX A-D since D88 (2026-10-20), built from the CEO's Google Gemini image
// by tools/art/gemini_frames.py (ready; the wind-up, strike and
// follow-through rotate it as one rigid piece about the elbow); only the
// four-letter name changed, every tic, action and jump is as it was. All in
// assets/sprites/ice_axe/. MOD-SPEC 6.3; tests/test_gemini_weapons_install.py.
// Names: docs/engine/MOD-SPEC.md section 6, "Slot 1 since D40".
// Balance rationale: docs/engine/BALANCE.md.

class SD_IceAxe : Fist replaces Fist
{
	// --- Balance constants -------------------------------------------------
	// Reference: Doom's Fist deals random(1,10) << 1 = 2..20 (avg 11) over a
	// 22-tic swing. The ice axe is a steel pick on a shaft: harder hit,
	// slower swing. 27-tic swing (see Fire state below). Values unchanged
	// from the shovel (D40).
	const SD_ICEAXE_DAMAGE_MIN   = 3;      // << 1 below -> 6 damage minimum
	const SD_ICEAXE_DAMAGE_MAX   = 12;     // << 1 below -> 24 maximum (avg 15)
	const SD_ICEAXE_DAMAGE_SHIFT = 1;      // same doubling Doom's A_Punch uses
	const SD_ICEAXE_BERSERK_MUL  = 10;     // same multiplier as the berserk pack
	const SD_ICEAXE_SPREAD       = 5.625;  // degrees; Doom's melee spread
	const SD_ICEAXE_KICKBACK     = 120;    // Doom Fist is 100; a swung pick shoves harder

	Default
	{
		Weapon.SelectionOrder 3700;   // same as the Fist: the last resort
		Weapon.Kickback SD_ICEAXE_KICKBACK;
		Weapon.SlotNumber 1;
		Obituary "$SD_OB_ICEAXE";
		Tag "$SD_TAG_ICEAXE";
		Inventory.PickupMessage "$SD_PICKUP_ICEAXE";
		Inventory.PickupSound "sd/weapon/iceaxe/pickup";  // SDAXPKP1/3 $random (N9e, D94)
		+WEAPON.WIMPY_WEAPON      // never auto-switch TO it when ammo runs out
		+WEAPON.MELEEWEAPON
		+WEAPON.NOAUTOSWITCHTO
	}

	States
	{
	Ready:
		SDAX A 1 A_WeaponReady;
		Loop;
	Deselect:
		SDAX A 1 A_Lower;
		Loop;
	Select:
		SDAX A 1 A_Raise;
		Loop;
	Fire:
		// 5 + 5 + 6 + 5 + 6 = 27 tics per swing (Doom's Fist: 22).
		// The swing (SDAXSWG, N9, D74) starts with the wind-up and peaks
		// before the blow; a hit, 5 tics later on the same channel, cuts its
		// tail, a miss lets it play out. Silent from 2026-10-13 until N9
		// (MOD-SPEC 6.2). The tic count is unchanged.
		SDAX B 5 A_StartSound("sd/weapon/iceaxe/swing", CHAN_WEAPON);
		SDAX C 5 A_SD_IceAxeSwing;
		SDAX D 6;
		SDAX C 5;
		SDAX B 6 A_ReFire;
		Goto Ready;
	Spawn:
		// Pickup sprite. The ice axe is not in the start inventory
		// (SD_Player): it is found, on MAP01's dorm rack and on the practice range (RANGE)
		// (editor number 21001, MAPINFO DoomEdNums). SDAP A, option C, since
		// D48; until then it wore Freedoom's chainsaw pickup, which the CEO
		// took for a chainsaw (MOD-SPEC 6.3).
		SDAP A -1;
		Stop;
	}

	// Mirrors GZDoom's A_Punch (wadsrc/static/zscript/actors/doom/weaponfist.zs)
	// with our own damage range and sounds. In a weapon action function `self`
	// is the player pawn and `invoker` is the weapon.
	action void A_SD_IceAxeSwing()
	{
		FTranslatedLineTarget t;

		int damage = random[SDIceAxe](SD_ICEAXE_DAMAGE_MIN, SD_ICEAXE_DAMAGE_MAX) << SD_ICEAXE_DAMAGE_SHIFT;
		if (FindInventory("PowerStrength"))
			damage *= SD_ICEAXE_BERSERK_MUL;

		double ang = angle + Random2[SDIceAxe]() * (SD_ICEAXE_SPREAD / 256);
		double range = MeleeRange + MELEEDELTA;
		double pitch = AimLineAttack(ang, range, null, 0., ALF_CHECK3D);

		// SD_IceAxePuff is BulletPuff with the wall sound (ice_axe_puff.zs).
		LineAttack(ang, range, pitch, damage, 'Melee', "SD_IceAxePuff", LAF_ISMELEEATTACK, t);

		if (t.linetarget)
		{
			A_StartSound("sd/weapon/iceaxe/hit", CHAN_WEAPON);
			angle = t.angleFromSource;   // turn to face whatever we just hit
		}
	}
}
