// SD_LegionTrooper - Liberty Legion basic infantry (BESTIARY section 4).
//
// Replaces Doom's ShotgunGuy at its numbers: 30 HP, three pellets. Drops the
// IZh-58, a captured Soviet shotgun (D35); SD_Izh replaces Shotgun anyway,
// but naming ours is clearer.
//
// Sprites are OUR OWN since D54 (2026-10-14): SDLT, cell C of the Legion
// sweep (tools/art/gen_legion.py), 70 lumps in assets/sprites/legion/:
// A-G in eight separate rotations, H-U rotation 0. The swap from Freedoom's
// SPOS placeholder renamed the sprite only; every frame letter and tic is as
// before (tests/test_legion_sprites.py pins them).

class SD_LegionTrooper : SD_Monster replaces ShotgunGuy
{
	const SD_TROOPER_HEALTH     = 30;    // ShotgunGuy parity: survives one TT-33 round
	const SD_TROOPER_RADIUS     = 20;
	const SD_TROOPER_HEIGHT     = 56;
	const SD_TROOPER_SPEED      = 8;
	const SD_TROOPER_MASS       = 100;
	const SD_TROOPER_PAINCHANCE = 170;   // 66 %: harder to stunlock than the rifleman
	const SD_TROOPER_SHOTS      = 3;     // three pellets on one aim slope
	const SD_TROOPER_HIT_DICE   = 5;     // random(1,5) x 3 each = 9..45 a blast
	const SD_TROOPER_HIT_MULT   = 3;

	Default
	{
		Health SD_TROOPER_HEALTH;
		Radius SD_TROOPER_RADIUS;
		Height SD_TROOPER_HEIGHT;
		Speed SD_TROOPER_SPEED;
		Mass SD_TROOPER_MASS;
		PainChance SD_TROOPER_PAINCHANCE;
		Species "SD_LegionTrooper";
		SD_Monster.Faction SD_FACTION_LEGION;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/legiontrooper/sight";
		AttackSound "sd/mon/legiontrooper/attack";
		PainSound "sd/mon/legiontrooper/pain";
		DeathSound "sd/mon/legiontrooper/death";
		ActiveSound "sd/mon/legiontrooper/active";
		Obituary "$SD_OB_TROOPER";
		Tag "$SD_TAG_TROOPER";
		DropItem "SD_Izh";         // a captured IZh-58 (D35)
	}

	States
	{
	Spawn:
		SDLT AB 10 A_Look;
		Loop;
	See:
		SDLT AABBCCDD 3 A_Chase;   // 3 tics: ShotgunGuy parity
		Loop;
	Missile:
		SDLT E 10 A_FaceTarget;
		SDLT F 10 Bright A_SD_Hitscan(SD_TROOPER_SHOTS, SD_TROOPER_HIT_DICE, SD_TROOPER_HIT_MULT);
		SDLT E 10;
		Goto See;
	Pain:
		SDLT G 3;
		SDLT G 3 A_Pain;
		Goto See;
	Death:
		SDLT H 5;
		SDLT I 5 A_Scream;
		SDLT J 5 A_NoBlocking;
		SDLT K 5;
		SDLT L -1;
		Stop;
	XDeath:
		SDLT M 5;
		SDLT N 5 A_StartSound("sd/mon/legiontrooper/xdeath", CHAN_VOICE);
		SDLT O 5 A_NoBlocking;
		SDLT PQRST 5;
		SDLT U -1;
		Stop;
	Raise:
		SDLT L 5;
		SDLT KJIH 5;
		Goto See;
	}
}
