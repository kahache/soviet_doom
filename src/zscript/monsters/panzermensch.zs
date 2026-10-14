// SD_Panzermensch - the Reich's armoured brute (BESTIARY section 8).
// Replaces Doom's HellKnight at its numbers: 500 HP in MAP01 (D35). The
// 1000 HP variant for MAP03 is SD_PanzermenschSchwer, its own file.
//
// Sprites are OUR OWN since D67 (2026-10-14): SDPM, cell D of the heavies
// sweep (bare skull in a riveted iron mask, D65) on the 3D rig
// (tools/art/gen_heavy.py --full pm), 71 lumps in
// assets/sprites/panzermensch/: A-H in eight separate rotations, I-O
// rotation 0, the corpse lying flat. The swap from Freedoom's BOS2
// placeholder renamed the sprite only; every frame letter and tic is as
// before (tests/test_panzermensch_sprites.py pins them). Doom's own
// HellKnight, which this class replaces, keeps the IWAD's BOS2. The heavy
// variant draws its own set, SDPS (panzermensch_schwer.zs).

class SD_Panzermensch : SD_Monster replaces HellKnight
{
	const SD_PANZER_HEALTH     = 500;    // HellKnight parity (D35)
	const SD_PANZER_RADIUS     = 24;
	const SD_PANZER_HEIGHT     = 64;     // does not fit under a 56 lintel; arenas >= 72
	const SD_PANZER_SPEED      = 8;      // slow, so the player can kite
	const SD_PANZER_MASS       = 1000;   // an RPG-7 barely moves him
	const SD_PANZER_PAINCHANCE = 50;     // 20 %: the real difficulty, not the HP
	const SD_PANZER_MELEE_DICE = 8;      // random(1,8) x 10 = 10..80, A_BruisAttack
	const SD_PANZER_MELEE_MULT = 10;

	Default
	{
		Health SD_PANZER_HEALTH;
		Radius SD_PANZER_RADIUS;
		Height SD_PANZER_HEIGHT;
		Speed SD_PANZER_SPEED;
		Mass SD_PANZER_MASS;
		PainChance SD_PANZER_PAINCHANCE;
		// The heavy variant inherits this species, as Doom's Baron and Hell
		// Knight share one: their shells do not start fights between them.
		Species "SD_Panzermensch";
		SD_Monster.Faction SD_FACTION_REICH;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/panzermensch/sight";
		PainSound "sd/mon/panzermensch/pain";
		DeathSound "sd/mon/panzermensch/death";
		ActiveSound "sd/mon/panzermensch/active";
		Obituary "$SD_OB_PANZER";
		HitObituary "$SD_OBHIT_PANZER";
		Tag "$SD_TAG_PANZER";
	}

	States
	{
	Spawn:
		SDPM AB 10 A_Look;
		Loop;
	See:
		// One plated footstep per walk cycle (24 tics): the cheapest
		// "something heavy is coming" telegraph. (H) - cut if it is noise.
		SDPM A 3 A_SD_PanzerStep;
		SDPM ABBCCDD 3 A_Chase;
		Loop;
	Melee:
	Missile:
		SDPM EF 8 A_FaceTarget;
		SDPM G 8 A_SD_MeleeOrMissile(SD_PANZER_MELEE_DICE, SD_PANZER_MELEE_MULT, "sd/mon/panzermensch/melee", "SD_PanzerShell");
		Goto See;
	Pain:
		SDPM H 2;
		SDPM H 2 A_Pain;
		Goto See;
	Death:
		SDPM I 8;
		SDPM J 8 A_Scream;
		SDPM K 8;
		SDPM L 8 A_NoBlocking;
		SDPM MN 8;
		SDPM O -1;
		Stop;
	Raise:
		SDPM O 8;
		SDPM NMLKJI 8;
		Goto See;
	}

	// The step, then the chase: the shape of Doom's A_Hoof (cyberdemon.zs).
	void A_SD_PanzerStep()
	{
		A_StartSound("sd/mon/panzermensch/step", CHAN_BODY);
		A_Chase();
	}
}
