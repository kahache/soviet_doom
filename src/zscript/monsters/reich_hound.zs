// SD_ReichHound - the Reich's fast melee beast (BESTIARY section 6).
// Replaces Doom's Demon at its numbers except speed. Bite only.
//
// Sprites are OUR OWN since D55 (2026-10-14): SDHN, the German shepherd of
// cell A (D50; tools/art/gen_hound.py --full), 46 lumps in
// assets/sprites/hound/: A-H at eight rotations drawn as Doom's mirrored
// pairs (SDHNA1, SDHNA2A8, SDHNA3A7, SDHNA4A6, SDHNA5), I-N rotation 0. The
// swap from Freedoom's SARG placeholder renamed the sprite only; every frame
// letter and tic is as before (tests/test_hound_sprites.py pins them). Doom's
// own DeadDemon (editor number 21) and Spectre (58) derive from Demon, not
// from this class, and keep the IWAD's SARG.

class SD_ReichHound : SD_Monster replaces Demon
{
	const SD_HOUND_HEALTH     = 150;   // Demon parity: two IZh barrels
	const SD_HOUND_RADIUS     = 30;    // parity: wide enough to block a corridor
	const SD_HOUND_HEIGHT     = 56;
	const SD_HOUND_SPEED      = 12;    // (H) Demon is 10; "fast melee", still outrunnable
	const SD_HOUND_MASS       = 400;
	const SD_HOUND_PAINCHANCE = 180;
	const SD_HOUND_MELEE_DICE = 10;    // random(1,10) x 4 = 4..40, A_SargAttack
	const SD_HOUND_MELEE_MULT = 4;

	Default
	{
		Health SD_HOUND_HEALTH;
		Radius SD_HOUND_RADIUS;
		Height SD_HOUND_HEIGHT;
		Speed SD_HOUND_SPEED;
		Mass SD_HOUND_MASS;
		PainChance SD_HOUND_PAINCHANCE;
		Species "SD_ReichHound";
		SD_Monster.Faction SD_FACTION_REICH;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/reichhound/sight";
		// A_Chase plays AttackSound on entering Melee, as for Doom's demon.
		AttackSound "sd/mon/reichhound/attack";
		PainSound "sd/mon/reichhound/pain";
		DeathSound "sd/mon/reichhound/death";
		ActiveSound "sd/mon/reichhound/active";
		Obituary "$SD_OB_HOUND";
		Tag "$SD_TAG_HOUND";
	}

	States
	{
	Spawn:
		SDHN AB 10 A_Look;
		Loop;
	See:
		SDHN AABBCCDD 2 Fast A_Chase;
		Loop;
	Melee:
		SDHN EF 8 Fast A_FaceTarget;
		SDHN G 8 Fast A_SD_Melee(SD_HOUND_MELEE_DICE, SD_HOUND_MELEE_MULT);
		Goto See;
	Pain:
		SDHN H 2 Fast;
		SDHN H 2 Fast A_Pain;
		Goto See;
	Death:
		SDHN I 8;
		SDHN J 8 A_Scream;
		SDHN K 4;
		SDHN L 4 A_NoBlocking;
		SDHN M 4;
		SDHN N -1;
		Stop;
	Raise:
		SDHN N 5;
		SDHN MLKJI 5;
		Goto See;
	}
}
