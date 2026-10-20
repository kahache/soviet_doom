// SD_Doughboy - the Legion's floating head in an M1 helmet (BESTIARY
// section 7). Replaces Doom's Cacodemon at its numbers. Bites in melee
// range, spits SD_DoughboyShell otherwise.
//
// Sprites are OUR OWN since D70 (2026-10-14): SDDB, cell C of the heavies
// sweep (the head in its M1 helmet, severed: neck stump, dangling spine,
// D65) with the bigger US flag decal on the helmet (D67, 11 x 7 px), drawn
// on the 3D rig (tools/art/gen_heavy.py --full db): 54 lumps in
// assets/sprites/doughboy/, A-F in eight separate rotations, G-L rotation
// 0, the corpse a deflated sack flat on the floor. The swap from Freedoom's
// HEAD placeholder renamed the sprite only; every frame letter and tic is
// as before (tests/test_doughboy_sprites.py pins them). The body stays
// 31 x 56: the drawing is 53-55 px wide (64 in the pain's lurch; HEAD is
// 61-69) and rises 60-62 px above the actor's z, as HEAD did; only the
// stump hangs lower (15 px below z, HEAD 5). Doom's own Cacodemon, which
// this class replaces, keeps the IWAD's HEAD. The shell, SD_DoughboyShell,
// wears our SDDL since D81 (doughboy_shell.zs).

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
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
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
		SDDB A 10 A_Look;
		Loop;
	See:
		SDDB A 3 A_Chase;
		Loop;
	Missile:
		// Like the cacodemon there is no Melee state: the attack itself
		// decides between the bite and the shell by range.
		SDDB B 5 A_FaceTarget;
		SDDB C 5 A_FaceTarget;
		SDDB D 5 Bright A_SD_MeleeOrMissile(SD_DOUGHBOY_MELEE_DICE, SD_DOUGHBOY_MELEE_MULT, "sd/mon/doughboy/melee", "SD_DoughboyShell");
		Goto See;
	Pain:
		SDDB E 3;
		SDDB E 3 A_Pain;
		SDDB F 6;
		Goto See;
	Death:
		// Deflate and sink: Doom's own sequence for a dead floater.
		SDDB G 8;
		SDDB H 8 A_Scream;
		SDDB I 8;
		SDDB J 8;
		SDDB K 8 A_NoBlocking;
		SDDB L -1 A_SetFloorClip;
		Stop;
	Raise:
		SDDB L 8 A_UnSetFloorClip;
		SDDB KJIHG 8;
		Goto See;
	}
}
