// SD_Stormtrooper - the hybrid: a Reich body with a Legion weapon grafted
// into it (BESTIARY section 5). Replaces Doom's DoomImp at its numbers.
// Claws in melee range, fires SD_StormBolt otherwise.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: TROO, same layout as SDHS.

class SD_Stormtrooper : SD_Monster replaces DoomImp
{
	const SD_STORM_HEALTH     = 60;    // DoomImp parity: the shotgun's first lesson
	const SD_STORM_RADIUS     = 20;
	const SD_STORM_HEIGHT     = 56;
	const SD_STORM_SPEED      = 8;
	const SD_STORM_MASS       = 100;
	const SD_STORM_PAINCHANCE = 200;
	const SD_STORM_MELEE_DICE = 8;     // random(1,8) x 3 = 3..24, A_TroopAttack
	const SD_STORM_MELEE_MULT = 3;

	Default
	{
		Health SD_STORM_HEALTH;
		Radius SD_STORM_RADIUS;
		Height SD_STORM_HEIGHT;
		Speed SD_STORM_SPEED;
		Mass SD_STORM_MASS;
		PainChance SD_STORM_PAINCHANCE;
		Species "SD_Stormtrooper";
		SD_Monster.Faction SD_FACTION_BOTH;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/stormtrooper/sight";
		PainSound "sd/mon/stormtrooper/pain";
		DeathSound "sd/mon/stormtrooper/death";
		ActiveSound "sd/mon/stormtrooper/active";
		HitObituary "$SD_OBHIT_STORM";
		Obituary "$SD_OB_STORM";
		Tag "$SD_TAG_STORM";
	}

	States
	{
	Spawn:
		TROO AB 10 A_Look;
		Loop;
	See:
		TROO AABBCCDD 3 A_Chase;
		Loop;
	Melee:
	Missile:
		TROO EF 8 A_FaceTarget;
		TROO G 6 A_SD_MeleeOrMissile(SD_STORM_MELEE_DICE, SD_STORM_MELEE_MULT, "sd/mon/stormtrooper/melee", "SD_StormBolt");
		Goto See;
	Pain:
		TROO H 2;
		TROO H 2 A_Pain;
		Goto See;
	Death:
		TROO I 8;
		TROO J 8 A_Scream;
		TROO K 6;
		TROO L 6 A_NoBlocking;
		TROO M -1;
		Stop;
	XDeath:
		TROO N 5;
		TROO O 5 A_StartSound("sd/mon/stormtrooper/xdeath", CHAN_VOICE);
		TROO P 5;
		TROO Q 5 A_NoBlocking;
		TROO RST 5;
		TROO U -1;
		Stop;
	Raise:
		TROO ML 8;
		TROO KJI 6;
		Goto See;
	}
}
