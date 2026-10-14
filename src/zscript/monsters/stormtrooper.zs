// SD_Stormtrooper - the hybrid: a Reich body with a Legion weapon grafted
// into it (BESTIARY section 5). Replaces Doom's DoomImp at its numbers.
// Claws in melee range, fires SD_StormBolt otherwise.
//
// Sprites are OUR OWN since D56 (2026-10-14): SDHS, cell E on the 3D rig
// (tools/art/gen_storm.py --full, D48) with the death redone so the corpse
// lies flat (D53, approved in D56), 77 lumps in assets/sprites/storm/: A-H
// in eight separate rotations, I-U rotation 0. The swap from Freedoom's TROO
// placeholder renamed the sprite only; every frame letter and tic is as
// before (tests/test_storm_sprites.py pins them). Doom's own DoomImp, its
// corpse DeadDoomImp (editor number 20) and StealthDoomImp derive from
// DoomImp, not from this class, and keep the IWAD's TROO.

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
		SDHS AB 10 A_Look;
		Loop;
	See:
		SDHS AABBCCDD 3 A_Chase;
		Loop;
	Melee:
	Missile:
		SDHS EF 8 A_FaceTarget;
		SDHS G 6 A_SD_MeleeOrMissile(SD_STORM_MELEE_DICE, SD_STORM_MELEE_MULT, "sd/mon/stormtrooper/melee", "SD_StormBolt");
		Goto See;
	Pain:
		SDHS H 2;
		SDHS H 2 A_Pain;
		Goto See;
	Death:
		SDHS I 8;
		SDHS J 8 A_Scream;
		SDHS K 6;
		SDHS L 6 A_NoBlocking;
		SDHS M -1;
		Stop;
	XDeath:
		SDHS N 5;
		SDHS O 5 A_StartSound("sd/mon/stormtrooper/xdeath", CHAN_VOICE);
		SDHS P 5;
		SDHS Q 5 A_NoBlocking;
		SDHS RST 5;
		SDHS U -1;
		Stop;
	Raise:
		SDHS ML 8;
		SDHS KJI 6;
		Goto See;
	}
}
