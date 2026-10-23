// SD_LibertyColossus - Episode 2's boss (D104): the Liberty Legion's chrome
// colossus, the Statue of Liberty perverted (a crown of spikes, a torch that
// is a rocket and flame projector, a tablet worn as a shield). Waits on the
// dais of MAP06's Kremlin courtyard; his death opens the exit gate.
// Design: docs/engine/2026-10-22_P4_ep2-enemies.md section 3; numbers in
// BESTIARY section 12 (row 10). In the mod since D116 (2026-10-22), MAP06's
// boss; on his own sprite since D123 (2026-10-23, the CEO's "la estatua de
// la libertad"). His chrome-tinted stand-in look stayed in the game as its
// own enemy, SD_ChromeGeneral (chrome_general.zs, D123): MAP08's mini-boss.
//
// Three verbs, chosen by distance each time he attacks:
//   far    a salvo of three rockets from the torch (SD_ColossusRocket);
//   near   a short jet of fire (SD_ColossusFlame, the ROKS-3's flame cut short);
//   close  sometimes a stomp: a shock wave along the floor that hurts and
//          throws back whoever stands on it, and that a jump clears.
// Replaces Doom's SpiderMastermind, the boss slot the General left free
// (he replaces the Cyberdemon).
//
// The exit. GZDoom runs a monster's thing special when it dies
// (AActor::Die), whoever killed it: MAP06 gives the boss's thing
// `Door_Open (12, 16)` and nothing here needs to know. +BOSSDEATH and the
// final A_BossDeath are the General's, so a MAPINFO SpecialAction on this
// class works as the belt-and-braces fix MAP06's design names (section 11).
//
// LOOK (D119, approved D123): SDLC, his own 81 lumps drawn from the CEO's
// Gemini sheets by tools/art/colossus_gemini.py (gemini_enemy.py's
// COLOSSUS), in assets/sprites/colossus/ (the General's frame letters:
// design doc section 4), drawn at full size: no Scale, no tint. Rotation 1 aims and fires the
// torch at the player (E1, F1).

class SD_LibertyColossus : SD_Monster replaces SpiderMastermind
{
	// D119 (2026-10-23): classic Doom's level. 4500 (the General's 3000 x
	// 1.5) -> 3000, the Spider Mastermind's, the class this one replaces.
	const SD_COLOSSUS_HEALTH     = 3000;  // Spider Mastermind parity (D119; was 4500, D104 brief)
	const SD_COLOSSUS_RADIUS     = 44;    // 88 wide: still passes MAP06's 128 gate passage
	const SD_COLOSSUS_HEIGHT     = 110;   // under the passage's 128; the courtyard is open sky
	const SD_COLOSSUS_SPEED      = 10;    // (H) slower than the General's 12: a statue walking
	const SD_COLOSSUS_MASS       = 1000;  // unmovable
	const SD_COLOSSUS_PAINCHANCE = 20;    // the General's: effectively unstunnable, a boss
	// Missile behaviour copied from the General (and so the Cyberdemon): he
	// attacks readily at any range, which is what makes an arena a fight.
	const SD_COLOSSUS_MIN_MISSILE_CHANCE  = 160;
	const SD_COLOSSUS_MISSILE_CHANCE_MULT = 0.5;

	// Where the torch is, relative to his origin: high, and to his right.
	const SD_COLOSSUS_TORCH_Z    = 88;
	const SD_COLOSSUS_TORCH_SIDE = 20;

	// Choosing the verb (A_SD_ColossusChoose).
	const SD_COLOSSUS_FLAME_RANGE  = 320;  // the jet flies 352 (SD_ColossusFlame); inside this, fire
	const SD_COLOSSUS_STOMP_RANGE  = 192;  // inside this he may stomp instead
	const SD_COLOSSUS_STOMP_CHANCE = 96;   // of 256 (38 %) when in stomp range

	// The jet: five blobs, one every 3 tics, each up to +-5.6 degrees off.
	const SD_COLOSSUS_FLAME_SPREAD_STEP = 5.625 / 256;

	// The stomp.
	const SD_STOMP_RADIUS        = 256;   // (H) the wave's reach along the floor
	const SD_STOMP_DICE          = 8;     // random(1,8) x 5 = 5..40, avg 22.5
	const SD_STOMP_MULT          = 5;
	const SD_STOMP_THRUST        = 12;    // units/tic away from him: out of flame range in a few tics
	const SD_STOMP_HOP           = 6;     // and up off the floor, so it reads as a blow
	const SD_STOMP_AIRBORNE      = 8;     // higher than this over the floor, the wave passes under
	const SD_STOMP_QUAKE         = 3;     // A_Quake intensity
	const SD_STOMP_QUAKE_TICS    = 14;
	const SD_STOMP_QUAKE_RADIUS  = 768;   // felt across most of the courtyard

	Default
	{
		Health SD_COLOSSUS_HEALTH;
		Radius SD_COLOSSUS_RADIUS;
		Height SD_COLOSSUS_HEIGHT;
		Speed SD_COLOSSUS_SPEED;
		Mass SD_COLOSSUS_MASS;
		PainChance SD_COLOSSUS_PAINCHANCE;
		MinMissileChance SD_COLOSSUS_MIN_MISSILE_CHANCE;
		MissileChanceMult SD_COLOSSUS_MISSILE_CHANCE_MULT;
		// The General's boss flags, one for one.
		+BOSS
		+NORADIUSDMG        // the player's own RPG-7 splash must not do the work
		+DONTMORPH
		+BOSSDEATH          // A_BossDeath below: MAPINFO SpecialAction can name him
		Species "SD_LibertyColossus";
		SD_Monster.Faction SD_FACTION_LEGION;
		BloodColor "AD 27 21";     // D49: dark red for every faction
		// His own logical names (SNDINFO), over the General's lumps until
		// sound-designer records his (MOD-SPEC 6.2).
		SeeSound "sd/mon/colossus/sight";
		PainSound "sd/mon/colossus/pain";
		DeathSound "sd/mon/colossus/death";
		ActiveSound "sd/mon/colossus/active";
		Obituary "$SD_OB_COLOSSUS";      // rockets and fire
		HitObituary "$SD_OBHIT_COLOSSUS"; // the stomp ('Melee' damage)
		Tag "$SD_TAG_COLOSSUS";
	}

	States
	{
	Spawn:
		SDLC AB 10 A_Look;
		Loop;
	See:
		SDLC A 3 A_SD_ColossusStep;  // one footfall per cycle, as the Cyberdemon's A_Hoof
		SDLC ABBCCDD 3 A_Chase;
		Loop;
	Missile:
		SDLC E 0 A_SD_ColossusChoose;   // jumps to Flame or Stomp when close; else the salvo
	Rockets:
		SDLC E 10 A_FaceTarget;         // the torch comes up: the tell
		SDLC F 8 Bright A_SD_ColossusRocket;
		SDLC E 6 A_FaceTarget;
		SDLC F 8 Bright A_SD_ColossusRocket;
		SDLC E 6 A_FaceTarget;
		SDLC F 8 Bright A_SD_ColossusRocket;
		SDLC E 16 A_FaceTarget;         // recovery: the window to close in or get out
		Goto See;
	Flame:
		SDLC E 10 A_FaceTarget;         // the torch levels at you
		SDLC F 3 Bright A_SD_ColossusFlame;
		SDLC F 3 Bright A_SD_ColossusFlame;
		SDLC F 3 Bright A_SD_ColossusFlame;
		SDLC F 3 Bright A_SD_ColossusFlame;
		SDLC F 3 Bright A_SD_ColossusFlame;
		SDLC E 12;
		Goto See;
	Stomp:
		SDLC Q 14 A_FaceTarget;         // the foot goes up
		SDLC R 6 A_SD_ColossusStomp;    // ... and comes down
		SDLC R 14;
		Goto See;
	Pain:
		SDLC G 10 A_Pain;
		Goto See;
	Death:
		SDLC H 10;
		SDLC I 10 A_Scream;
		SDLC JKL 10;
		SDLC M 10 A_NoBlocking;
		SDLC NO 10;
		SDLC P 30;
		SDLC P -1 A_BossDeath;
		Stop;
	}

	void A_SD_ColossusStep()
	{
		A_StartSound("sd/mon/colossus/step", CHAN_BODY);
		A_Chase();
	}

	// Called on a 0-tic frame at the top of Missile. Far: fall through to
	// the rockets. Near: the jet. Close: sometimes the stomp, else the jet.
	void A_SD_ColossusChoose()
	{
		if (target == null)
			return;
		double dist = Distance2D(target);
		if (dist <= SD_COLOSSUS_STOMP_RANGE && random[SD_ColossusChoose](0, 255) < SD_COLOSSUS_STOMP_CHANCE)
		{
			SetStateLabel("Stomp");
			return;
		}
		if (dist <= SD_COLOSSUS_FLAME_RANGE)
			SetStateLabel("Flame");
	}

	void A_SD_ColossusRocket()
	{
		if (target == null)
			return;
		A_FaceTarget();
		A_SpawnProjectile("SD_ColossusRocket", SD_COLOSSUS_TORCH_Z, SD_COLOSSUS_TORCH_SIDE);
	}

	// One blob of the jet; a report per blob, as the ROKS-3 restarts its
	// own every 3 tics.
	void A_SD_ColossusFlame()
	{
		if (target == null)
			return;
		A_FaceTarget();
		A_StartSound("sd/mon/colossus/flame", CHAN_WEAPON);
		A_SpawnProjectile("SD_ColossusFlame", SD_COLOSSUS_TORCH_Z, SD_COLOSSUS_TORCH_SIDE,
			Random2[SD_ColossusFlame]() * SD_COLOSSUS_FLAME_SPREAD_STEP);
	}

	// The stomp: the ground shakes for everyone near, and each player who is
	// standing on the floor within reach, in his sight, is hurt and thrown
	// back. Players only, so the wave never starts a fight with his own
	// escort; a player in the air when it lands is not touched.
	void A_SD_ColossusStomp()
	{
		A_StartSound("sd/mon/colossus/step", CHAN_BODY);
		A_StartSound("sd/mon/colossus/stomp", CHAN_WEAPON);
		A_Quake(SD_STOMP_QUAKE, SD_STOMP_QUAKE_TICS, 0, SD_STOMP_QUAKE_RADIUS);
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i])
				continue;
			let mo = players[i].mo;
			if (mo == null || mo.health <= 0)
				continue;
			if (Distance2D(mo) > SD_STOMP_RADIUS)
				continue;
			if (mo.pos.z > mo.floorz + SD_STOMP_AIRBORNE)
				continue;
			if (!CheckSight(mo))
				continue;
			int damage = random[SD_ColossusStomp](1, SD_STOMP_DICE) * SD_STOMP_MULT;
			mo.DamageMobj(self, self, damage, 'Melee');
			mo.Thrust(SD_STOMP_THRUST, AngleTo(mo));
			mo.Vel.Z += SD_STOMP_HOP;
		}
	}
}
