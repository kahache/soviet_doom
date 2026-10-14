// SD_ReichRifleman - Fourth Reich basic infantry (BESTIARY section 3).
//
// Replaces Doom's ZombieMan, at ZombieMan's numbers: 20 HP is what the whole
// ammo economy of MAP01 is sized against. Drops a Soviet magazine: the
// invaders carry captured Soviet arms (D35).
//
// Sprites are OUR OWN since D55 (2026-10-14): SDRR, cell E on the 3D rig
// (tools/art/gen_rig.py, D38) with the bloody death and flat corpse of D48,
// 70 lumps in assets/sprites/rifleman/: A-G in eight separate rotations, H-U
// rotation 0. The swap from Freedoom's POSS placeholder renamed the sprite
// only; every frame letter and tic is as before (tests/test_rifleman_sprites.py
// pins them). Doom's own DeadZombieMan (editor number 18) derives from
// ZombieMan, not from this class, and keeps the IWAD's POSS corpse.
// Sounds are logical names; SNDINFO points them at Freedoom lumps for now.

class SD_ReichRifleman : SD_Monster replaces ZombieMan
{
	const SD_RIFLEMAN_HEALTH     = 20;    // ZombieMan parity; sets the ammo economy
	const SD_RIFLEMAN_RADIUS     = 20;    // parity; corridors are built for it
	const SD_RIFLEMAN_HEIGHT     = 56;
	const SD_RIFLEMAN_SPEED      = 8;     // parity
	const SD_RIFLEMAN_MASS       = 100;   // parity: how far an RPG-7 throws him
	const SD_RIFLEMAN_PAINCHANCE = 200;   // 78 %: stunlockable, as Doom's zombie
	const SD_RIFLEMAN_SHOTS      = 1;     // one bolt-action round per attack
	const SD_RIFLEMAN_HIT_DICE   = 5;     // random(1,5) x 3 = 3..15, A_PosAttack
	const SD_RIFLEMAN_HIT_MULT   = 3;

	Default
	{
		Health SD_RIFLEMAN_HEALTH;
		Radius SD_RIFLEMAN_RADIUS;
		Height SD_RIFLEMAN_HEIGHT;
		Speed SD_RIFLEMAN_SPEED;
		Mass SD_RIFLEMAN_MASS;
		PainChance SD_RIFLEMAN_PAINCHANCE;
		// Own species, so vanilla infighting holds across our classes
		// (BESTIARY 2.2).
		Species "SD_ReichRifleman";
		SD_Monster.Faction SD_FACTION_REICH;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/reichrifleman/sight";
		AttackSound "sd/mon/reichrifleman/attack";
		PainSound "sd/mon/reichrifleman/pain";
		DeathSound "sd/mon/reichrifleman/death";
		ActiveSound "sd/mon/reichrifleman/active";
		Obituary "$SD_OB_RIFLEMAN";
		Tag "$SD_TAG_RIFLEMAN";
		DropItem "SD_Clip";        // a captured 7.62x25 magazine (D35)
	}

	States
	{
	Spawn:
		SDRR AB 10 A_Look;
		Loop;
	See:
		SDRR AABBCCDD 4 A_Chase;
		Loop;
	Missile:
		SDRR E 10 A_FaceTarget;
		SDRR F 8 A_SD_Hitscan(SD_RIFLEMAN_SHOTS, SD_RIFLEMAN_HIT_DICE, SD_RIFLEMAN_HIT_MULT);
		SDRR E 8;
		Goto See;
	Pain:
		SDRR G 3;
		SDRR G 3 A_Pain;
		Goto See;
	Death:
		SDRR H 5;
		SDRR I 5 A_Scream;
		SDRR J 5 A_NoBlocking;     // drops the DropItem
		SDRR K 5;
		SDRR L -1;
		Stop;
	XDeath:
		SDRR M 5;
		SDRR N 5 A_StartSound("sd/mon/reichrifleman/xdeath", CHAN_VOICE);
		SDRR O 5 A_NoBlocking;
		SDRR PQRST 5;
		SDRR U -1;
		Stop;
	Raise:
		SDRR K 5;
		SDRR JIH 5;
		Goto See;
	}
}
