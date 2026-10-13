// SD_LegionTrooper - Liberty Legion basic infantry (BESTIARY section 4).
//
// Replaces Doom's ShotgunGuy at its numbers: 30 HP, three pellets. Drops the
// IZh-58, a captured Soviet shotgun (D35); SD_Izh replaces Shotgun anyway,
// but naming ours is clearer.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: SPOS, same layout as SDLT.

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
		BloodColor "C6 BD AA";     // plaster_warm 12: the Legion bleeds pale
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
		SPOS AB 10 A_Look;
		Loop;
	See:
		SPOS AABBCCDD 3 A_Chase;   // 3 tics: ShotgunGuy parity
		Loop;
	Missile:
		SPOS E 10 A_FaceTarget;
		SPOS F 10 Bright A_SD_Hitscan(SD_TROOPER_SHOTS, SD_TROOPER_HIT_DICE, SD_TROOPER_HIT_MULT);
		SPOS E 10;
		Goto See;
	Pain:
		SPOS G 3;
		SPOS G 3 A_Pain;
		Goto See;
	Death:
		SPOS H 5;
		SPOS I 5 A_Scream;
		SPOS J 5 A_NoBlocking;
		SPOS K 5;
		SPOS L -1;
		Stop;
	XDeath:
		SPOS M 5;
		SPOS N 5 A_StartSound("sd/mon/legiontrooper/xdeath", CHAN_VOICE);
		SPOS O 5 A_NoBlocking;
		SPOS PQRST 5;
		SPOS U -1;
		Stop;
	Raise:
		SPOS L 5;
		SPOS KJIH 5;
		Goto See;
	}
}
