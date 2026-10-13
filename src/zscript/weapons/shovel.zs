// SD_Shovel - slot 1, the sapper's shovel (MPL-50 entrenching tool).
//
// Replaces Doom's Fist. A "Weapon" in GZDoom is an inventory actor that owns
// a set of HUD-sprite states (Ready / Select / Deselect / Fire); the engine
// runs those states on the player's weapon layer. `replaces Fist` tells the
// engine to hand out this class wherever the game would have given a Fist,
// so Freedoom's melee weapon never shows up.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: PUNG (held) and CSAW (pickup).
// Final lumps to be drawn by art-director: SDSH A-E (held), SDSP A (pickup).
// Balance rationale: docs/engine/BALANCE.md.

class SD_Shovel : Fist replaces Fist
{
	// --- Balance constants -------------------------------------------------
	// Reference: Doom's Fist deals random(1,10) << 1 = 2..20 (avg 11) over a
	// 22-tic swing. The shovel is sharpened steel on a shaft: harder hit,
	// slower swing. 27-tic swing (see Fire state below).
	const SD_SHOVEL_DAMAGE_MIN   = 3;      // << 1 below -> 6 damage minimum
	const SD_SHOVEL_DAMAGE_MAX   = 12;     // << 1 below -> 24 maximum (avg 15)
	const SD_SHOVEL_DAMAGE_SHIFT = 1;      // same doubling Doom's A_Punch uses
	const SD_SHOVEL_BERSERK_MUL  = 10;     // same multiplier as the berserk pack
	const SD_SHOVEL_SPREAD       = 5.625;  // degrees; Doom's melee spread
	const SD_SHOVEL_KICKBACK     = 120;    // Doom Fist is 100; a shovel shoves harder

	Default
	{
		Weapon.SelectionOrder 3700;   // same as the Fist: the last resort
		Weapon.Kickback SD_SHOVEL_KICKBACK;
		Weapon.SlotNumber 1;
		Obituary "$SD_OB_SHOVEL";
		Tag "$SD_TAG_SHOVEL";
		Inventory.PickupMessage "$SD_PICKUP_SHOVEL";
		+WEAPON.WIMPY_WEAPON      // never auto-switch TO it when ammo runs out
		+WEAPON.MELEEWEAPON
		+WEAPON.NOAUTOSWITCHTO
	}

	States
	{
	Ready:
		PUNG A 1 A_WeaponReady;
		Loop;
	Deselect:
		PUNG A 1 A_Lower;
		Loop;
	Select:
		PUNG A 1 A_Raise;
		Loop;
	Fire:
		// 5 + 5 + 6 + 5 + 6 = 27 tics per swing (Doom's Fist: 22).
		// No swing sound in F4: see the comment at the top of SNDINFO.
		// Silence is Doom's own behaviour for the Fist; the impact carries
		// the feedback. The tic count is unchanged.
		PUNG B 5;
		PUNG C 5 A_SD_ShovelSwing;
		PUNG D 6;
		PUNG C 5;
		PUNG B 6 A_ReFire;
		Goto Ready;
	Spawn:
		// Pickup sprite. The shovel is not in the start inventory (SD_Player):
		// it is found, on MAP01's dorm rack and on MAP02's range (editor
		// number 21001, MAPINFO DoomEdNums). CSAW is Freedoom's chainsaw,
		// a placeholder until art-director draws SDSP.
		CSAW A -1;
		Stop;
	}

	// Mirrors GZDoom's A_Punch (wadsrc/static/zscript/actors/doom/weaponfist.zs)
	// with our own damage range and sounds. In a weapon action function `self`
	// is the player pawn and `invoker` is the weapon.
	action void A_SD_ShovelSwing()
	{
		FTranslatedLineTarget t;

		int damage = random[SDShovel](SD_SHOVEL_DAMAGE_MIN, SD_SHOVEL_DAMAGE_MAX) << SD_SHOVEL_DAMAGE_SHIFT;
		if (FindInventory("PowerStrength"))
			damage *= SD_SHOVEL_BERSERK_MUL;

		double ang = angle + Random2[SDShovel]() * (SD_SHOVEL_SPREAD / 256);
		double range = MeleeRange + MELEEDELTA;
		double pitch = AimLineAttack(ang, range, null, 0., ALF_CHECK3D);

		LineAttack(ang, range, pitch, damage, 'Melee', "BulletPuff", LAF_ISMELEEATTACK, t);

		if (t.linetarget)
		{
			A_StartSound("sd/weapon/shovel/hit", CHAN_WEAPON);
			angle = t.angleFromSource;   // turn to face whatever we just hit
		}
	}
}
