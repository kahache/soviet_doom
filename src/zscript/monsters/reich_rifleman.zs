// SD_ReichRifleman - Fourth Reich basic infantry (BESTIARY section 3).
//
// Replaces Doom's ZombieMan, at ZombieMan's numbers: 20 HP is what the whole
// ammo economy of MAP01 is sized against. Drops a Soviet magazine: the
// invaders carry captured Soviet arms (D35).
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: POSS, same frame layout as the
// final SDRR (BESTIARY 2.7), so the swap is a rename of the four letters.
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
		BloodColor "53 4A 30";     // khaki_olive 3: the Reich bleeds dark olive
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
		POSS AB 10 A_Look;
		Loop;
	See:
		POSS AABBCCDD 4 A_Chase;
		Loop;
	Missile:
		POSS E 10 A_FaceTarget;
		POSS F 8 A_SD_Hitscan(SD_RIFLEMAN_SHOTS, SD_RIFLEMAN_HIT_DICE, SD_RIFLEMAN_HIT_MULT);
		POSS E 8;
		Goto See;
	Pain:
		POSS G 3;
		POSS G 3 A_Pain;
		Goto See;
	Death:
		POSS H 5;
		POSS I 5 A_Scream;
		POSS J 5 A_NoBlocking;     // drops the DropItem
		POSS K 5;
		POSS L -1;
		Stop;
	XDeath:
		POSS M 5;
		POSS N 5 A_StartSound("sd/mon/reichrifleman/xdeath", CHAN_VOICE);
		POSS O 5 A_NoBlocking;
		POSS PQRST 5;
		POSS U -1;
		Stop;
	Raise:
		POSS K 5;
		POSS JIH 5;
		Goto See;
	}
}
