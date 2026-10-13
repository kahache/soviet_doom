// SD_Doughboy - the Legion's floating head in an M1 helmet (BESTIARY
// section 7). Replaces Doom's Cacodemon at its numbers. Bites in melee
// range, spits SD_DoughboyShell otherwise.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: HEAD, same layout as SDDB.

class SD_Doughboy : SD_Monster replaces Cacodemon
{
	const SD_DOUGHBOY_HEALTH     = 400;   // Cacodemon parity: the first ammo sink
	const SD_DOUGHBOY_RADIUS     = 31;    // parity: jams in doorways, keep lanes >= 96
	const SD_DOUGHBOY_HEIGHT     = 56;
	const SD_DOUGHBOY_SPEED      = 8;
	const SD_DOUGHBOY_MASS       = 400;
	const SD_DOUGHBOY_PAINCHANCE = 128;   // 50 %
	const SD_DOUGHBOY_MELEE_DICE = 6;     // random(1,6) x 10 = 10..60, A_HeadAttack
	const SD_DOUGHBOY_MELEE_MULT = 10;

	Default
	{
		Health SD_DOUGHBOY_HEALTH;
		Radius SD_DOUGHBOY_RADIUS;
		Height SD_DOUGHBOY_HEIGHT;
		Speed SD_DOUGHBOY_SPEED;
		Mass SD_DOUGHBOY_MASS;
		PainChance SD_DOUGHBOY_PAINCHANCE;
		+FLOAT
		+NOGRAVITY
		Species "SD_Doughboy";
		SD_Monster.Faction SD_FACTION_LEGION;
		BloodColor "C6 BD AA";
		SeeSound "sd/mon/doughboy/sight";
		PainSound "sd/mon/doughboy/pain";
		DeathSound "sd/mon/doughboy/death";
		ActiveSound "sd/mon/doughboy/active";
		Obituary "$SD_OB_DOUGHBOY";
		HitObituary "$SD_OBHIT_DOUGHBOY";
		Tag "$SD_TAG_DOUGHBOY";
	}

	States
	{
	Spawn:
		HEAD A 10 A_Look;
		Loop;
	See:
		HEAD A 3 A_Chase;
		Loop;
	Missile:
		// Like the cacodemon there is no Melee state: the attack itself
		// decides between the bite and the shell by range.
		HEAD B 5 A_FaceTarget;
		HEAD C 5 A_FaceTarget;
		HEAD D 5 Bright A_SD_MeleeOrMissile(SD_DOUGHBOY_MELEE_DICE, SD_DOUGHBOY_MELEE_MULT, "sd/mon/doughboy/melee", "SD_DoughboyShell");
		Goto See;
	Pain:
		HEAD E 3;
		HEAD E 3 A_Pain;
		HEAD F 6;
		Goto See;
	Death:
		// Deflate and sink: Doom's own sequence for a dead floater.
		HEAD G 8;
		HEAD H 8 A_Scream;
		HEAD I 8;
		HEAD J 8;
		HEAD K 8 A_NoBlocking;
		HEAD L -1 A_SetFloorClip;
		Stop;
	Raise:
		HEAD L 8 A_UnSetFloorClip;
		HEAD KJIHG 8;
		Goto See;
	}
}
