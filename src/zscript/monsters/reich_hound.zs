// SD_ReichHound - the Reich's fast melee beast (BESTIARY section 6).
// Replaces Doom's Demon at its numbers except speed. Bite only.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: SARG, same layout as SDHN.

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
		BloodColor "53 4A 30";
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
		SARG AB 10 A_Look;
		Loop;
	See:
		SARG AABBCCDD 2 Fast A_Chase;
		Loop;
	Melee:
		SARG EF 8 Fast A_FaceTarget;
		SARG G 8 Fast A_SD_Melee(SD_HOUND_MELEE_DICE, SD_HOUND_MELEE_MULT);
		Goto See;
	Pain:
		SARG H 2 Fast;
		SARG H 2 Fast A_Pain;
		Goto See;
	Death:
		SARG I 8;
		SARG J 8 A_Scream;
		SARG K 4;
		SARG L 4 A_NoBlocking;
		SARG M 4;
		SARG N -1;
		Stop;
	Raise:
		SARG N 5;
		SARG MLKJI 5;
		Goto See;
	}
}
