// SD_Consortium - Episode 3's final boss (D112): the thing that holds the
// invaders' main portal open at Tunguska, and the bond between the two
// factions. The Fourth Reich and the Liberty Legion grown into one body: a
// Reich half (grey-green flesh, SS helmet, the armband) and a Legion half
// (chrome and pink flesh, M1 helmet, the flag on the shoulder) joined at a
// chest that is a core of the portal's cobalt field, its lower body a mass
// of cables plugged into the portal's plinth. "They fight for profit": this
// is the partnership itself. It waits on MAP09's crater floor before the
// portal (MAP09_BOSS_SPOT) and its death opens the control bunker.
// Design: docs/engine/2026-10-22_P4_ep3-final-boss.md; numbers in BESTIARY
// section 12 (row 11). In the mod since D116 (2026-10-22), on a provisional
// sprite; placed in no map yet (MAP09's boss swap is level-designer's).
//
// Two phases, split at half health:
//   ROOTED (9000-4501)  plugged into the portal: it does not walk, it turns
//       slowly to follow you. The Reich arm fires rocket salvoes, the Legion
//       arm fans of energy balls, the core a gout of fire when you are
//       close; every fourth attack the portal behind it lets through a pair
//       of reinforcements, one of each faction.
//   BREACH              at half health, once: invulnerable for 65 tics, the
//       ground shakes, a line on every screen, a wave of four reinforcements,
//       and it tears the cables out.
//   FREE (4500-0)       it walks (slowly) and fights harder: rockets and
//       orbs in one volley, wider fans of orbs, a sweeping jet of fire, a
//       pair of reinforcements every third attack.
// Its reinforcements never infight, and nothing a monster fires hurts it:
// the factions are united in it (DamageMobj below; the projectiles pass
// through monsters, consortium_*.zs). When it dies, they die with it.
//
// Replaces nothing. Doom's last free boss slot is the Icon of Sin's
// BossBrain, a scripted wall target rather than a monster; no map of ours
// places it, so taking it would buy nothing but a surprise. The class is
// placed by its own editor number (21112) or summoned by name.
//
// The exit. GZDoom runs a monster's thing special when it dies
// (AActor::Die), whoever killed it: MAP09 gives the boss's thing
// `Door_Open (12, 16)` and nothing here needs to know. +BOSSDEATH and the
// final A_BossDeath are the General's, so a MAPINFO SpecialAction on this
// class works as the belt-and-braces fix MAP09's design names (section 11).
//
// PROVISIONAL LOOK (D116): no art of its own yet (Gemini, a little at a
// time). It wears the heavy Panzermensch's SDPS (A-D walk, E-G the attack,
// H pain, I-O death), drawn 1.75 times larger and tinted with the portal's
// cobalt by the lines marked PROVISIONAL-D116. The final set is SDCN (95
// lumps: design doc section 5). When it is installed in
// assets/sprites/consortium/, the swap is the sprite name and those lines:
//   sed -i -e 's/^\(\s*\)SDPS /\1SDCN /' -e '/^\s*[^/[:space:]].*PROVISIONAL-D116/d' src/zscript/monsters/consortium.zs
// and then two state edits the drawing adds (design doc 7, step 2): the
// rooted See shows SDCN Q R instead of A B, and Breach's first two frames
// show S instead of H (MOD-SPEC 6.12; tests/test_ep3_boss.py pins it).
//
// NOT VERIFIED in the engine (D26: no agent starts GZDoom). Used here for
// the first time in this project: CHF_DONTMOVE and CHF_NODIRECTIONTURN
// (gzdoom.pk3 g4.14.2 zscript/constants.zs), the MissileChanceMult field,
// the DamageMobj and CanCollideWith virtuals and A_KillChildren (its
// zscript/actors/actor.zs), the NOINFIGHTING flag (the name is in
// gzdoom.exe g4.14.2). The names were read off the engine's own files; the
// behaviour is the design doc's engine checks.

class SD_Consortium : SD_Monster
{
	const SD_CONSORTIUM_HEALTH     = 9000;  // (H) the Liberty Colossus's 4500 x 2 (D112 brief)
	const SD_CONSORTIUM_RADIUS     = 56;    // 112 wide: the crater is 2048 square, the terraces 64 deep
	const SD_CONSORTIUM_HEIGHT     = 128;   // the crater's sky is 640 over its floor
	const SD_CONSORTIUM_SPEED      = 8;     // (H) once free; slower than the colossus's 10
	const SD_CONSORTIUM_MASS       = 10000; // rooted in the portal: nothing moves it
	const SD_CONSORTIUM_PAINCHANCE = 10;    // half the General's 20: a boss that barely flinches
	const SD_CONSORTIUM_SCALE      = 1.75;  // SDPS is 72 units tall; 72 x 1.75 ~ 126 (PROVISIONAL-D116)
	// Missile behaviour: the General's (the Cyberdemon's) while rooted;
	// once free, a lower multiplier makes it attack more readily at range.
	const SD_CONSORTIUM_MIN_MISSILE_CHANCE       = 160;
	const SD_CONSORTIUM_MISSILE_CHANCE_MULT      = 0.5;
	const SD_CONSORTIUM_FREE_MISSILE_CHANCE_MULT = 0.375;  // (H)

	// The phases.
	const SD_CONSORTIUM_BREACH_FRACTION = 0.5;   // below half its spawn health, once
	const SD_CONSORTIUM_ROOTED_TURN     = 8;     // (H) degrees per chase step while rooted: slow
	const SD_CONSORTIUM_BREACH_QUAKE        = 4;
	const SD_CONSORTIUM_BREACH_QUAKE_TICS   = 65;  // the whole Breach state
	const SD_CONSORTIUM_BREACH_QUAKE_RADIUS = 2048; // the whole crater

	// Where its weapons are, relative to its origin (to its left is negative).
	const SD_CONSORTIUM_ARM_Z          = 96;
	const SD_CONSORTIUM_REICH_ARM_SIDE = -32;  // the Reich arm: rockets
	const SD_CONSORTIUM_LEGION_ARM_SIDE = 32;  // the Legion arm: energy balls
	const SD_CONSORTIUM_CORE_Z         = 64;   // the chest: fire

	// Choosing the attack (A_SD_ConsortiumChoose).
	const SD_CONSORTIUM_FLAME_RANGE = 320;   // the fire flies 352 (SD_ConsortiumFlame); inside this, fire
	const SD_CONSORTIUM_ORB_CHANCE  = 128;   // of 256: orbs or rockets when not close

	// The orb fans (degrees between two balls of a fan).
	const SD_CONSORTIUM_FAN         = 12;    // three balls over 24 degrees
	const SD_CONSORTIUM_FAN_WIDE    = 8;     // five balls over 32 degrees (free)
	const SD_CONSORTIUM_FAN_SHIFT   = 6;     // the second fan of a pair falls between the first's

	// The fire: rooted, five blobs straight at you, each up to +-5.6 degrees
	// off; free, nine blobs sweeping from 16 degrees one side to 16 the other.
	const SD_CONSORTIUM_FLAME_SPREAD_STEP = 5.625 / 256;
	const SD_CONSORTIUM_SWEEP_FROM  = -16;
	const SD_CONSORTIUM_SWEEP_STEP  = 4;

	// The reinforcements (the portal lets them through behind it).
	const SD_CONSORTIUM_CALL_EVERY_ROOTED = 4;   // (H) every 4th attack while rooted
	const SD_CONSORTIUM_CALL_EVERY_FREE   = 3;   // (H) every 3rd once free
	const SD_CONSORTIUM_CAP_ROOTED        = 4;   // (H) never more than this many alive
	const SD_CONSORTIUM_CAP_FREE          = 6;
	const SD_CONSORTIUM_PAIR              = 2;   // one of each faction
	const SD_CONSORTIUM_WAVE              = 4;   // the Breach
	// Spots, relative to its facing (x forward, y to its right). It stands
	// before the portal facing away from it (MAP09: the portal's base ends
	// 192 units behind the spot), so "behind" is the portal side. Its radius
	// 56 + a servant's up to 31 (the Doughboy) + clearance: 144 behind, 120
	// to a side. A blocked spot is skipped (A_SpawnItemEx refuses a monster
	// where it does not fit), and the next one tried.
	const SD_CONSORTIUM_SPOT_BACK  = 144;
	const SD_CONSORTIUM_SPOT_PAIR  = 80;
	const SD_CONSORTIUM_SPOT_SIDE  = 120;
	const SD_CONSORTIUM_SPOTS      = 6;

	// Which wave A_SD_ConsortiumServant() is asked about.
	const SD_WAVE_ROOTED = 0;
	const SD_WAVE_BREACH = 1;
	const SD_WAVE_FREE   = 2;

	bool unbound;               // phase 2: set once, at the top of Breach
	int attacksSinceCall;       // attacks since the portal last let anyone through
	int sweepStep;              // which blob of the sweep is next
	Array<Actor> servants;      // the reinforcements it called, alive or not

	Default
	{
		Health SD_CONSORTIUM_HEALTH;
		Radius SD_CONSORTIUM_RADIUS;
		Height SD_CONSORTIUM_HEIGHT;
		Speed SD_CONSORTIUM_SPEED;
		Mass SD_CONSORTIUM_MASS;
		PainChance SD_CONSORTIUM_PAINCHANCE;
		MinMissileChance SD_CONSORTIUM_MIN_MISSILE_CHANCE;
		MissileChanceMult SD_CONSORTIUM_MISSILE_CHANCE_MULT;
		Scale SD_CONSORTIUM_SCALE;   // PROVISIONAL-D116
		// The General's boss flags, one for one.
		+BOSS
		+NORADIUSDMG        // the player's own RPG-7 splash must not do the work
		+DONTMORPH
		+BOSSDEATH          // A_BossDeath below: MAPINFO SpecialAction can name it
		+NOINFIGHTING       // it never turns on its own servants (NOT VERIFIED)
		Species "SD_Consortium";
		SD_Monster.Faction SD_FACTION_BOTH;   // both factions in one body
		BloodColor "AD 27 21";     // D49: dark red for every faction
		// The portal's cobalt: the whole palette mapped by luminance onto a
		// dark-violet-to-ice-blue gradient. NOT VERIFIED in the engine on
		// truecolour PNGs (same caveat as the colossus).
		Translation "0:255=%[0.04,0.02,0.12]:[1.10,1.40,2.00]";   // PROVISIONAL-D116
		// Its own logical names (SNDINFO), over a brute's voice and the
		// General's death cue until its own are recorded (design doc 6).
		SeeSound "sd/mon/consortium/sight";
		PainSound "sd/mon/consortium/pain";
		DeathSound "sd/mon/consortium/death";
		ActiveSound "sd/mon/consortium/active";
		Obituary "$SD_OB_CONSORTIUM";
		Tag "$SD_TAG_CONSORTIUM";
	}

	States
	{
	Spawn:
		SDPS AB 10 A_Look;
		Loop;
	See:
		SDPS A 0 A_JumpIf(unbound, "Walk");
		// Rooted: it breathes and turns, it does not walk.
		SDPS A 6 A_SD_ConsortiumChase;
		SDPS B 6 A_SD_ConsortiumChase;
		Loop;
	Walk:
		SDPS A 3 A_SD_ConsortiumStep;   // one footfall per cycle
		SDPS ABBCCDD 3 A_SD_ConsortiumChase;
		Loop;
	Missile:
		SDPS E 0 A_SD_ConsortiumChoose;  // always jumps; falls into Orbs only without a target

	// ---- phase 1, rooted --------------------------------------------------
	Orbs:
		SDPS E 12 A_FaceTarget;          // the Legion arm comes up: the tell
		SDPS G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, 0);
		SDPS E 10 A_FaceTarget;
		SDPS G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, SD_CONSORTIUM_FAN_SHIFT);
		SDPS E 16;                       // recovery: the window
		Goto See;
	Rockets:
		SDPS F 12 A_FaceTarget;          // the Reich arm comes up
		SDPS G 8 Bright A_SD_ConsortiumRocket;
		SDPS F 6 A_FaceTarget;
		SDPS G 8 Bright A_SD_ConsortiumRocket;
		SDPS F 6 A_FaceTarget;
		SDPS G 8 Bright A_SD_ConsortiumRocket;
		SDPS F 16;
		Goto See;
	Flame:
		SDPS E 10 A_FaceTarget;          // the core opens
		SDPS G 3 Bright A_SD_ConsortiumFlame;
		SDPS G 3 Bright A_SD_ConsortiumFlame;
		SDPS G 3 Bright A_SD_ConsortiumFlame;
		SDPS G 3 Bright A_SD_ConsortiumFlame;
		SDPS G 3 Bright A_SD_ConsortiumFlame;
		SDPS E 12;
		Goto See;
	Summon:
		SDPS E 15 Bright A_SD_ConsortiumCall;   // the portal behind it flares; two come through
		SDPS F 10;
		Goto See;

	// ---- the breach, once, at half health ---------------------------------
	Breach:
		SDPS H 10 A_SD_ConsortiumBreach;        // invulnerable; the ground shakes; the line
		SDPS H 10;
		SDPS E 20 Bright A_SD_ConsortiumWave;   // four come through at once
		SDPS F 15 Bright;
		SDPS G 10 Bright A_SD_ConsortiumUnbind; // the cables tear: it walks, and can be hurt
		Goto See;

	// ---- phase 2, free ----------------------------------------------------
	Volley:
		SDPS F 8 A_FaceTarget;           // both arms come up
		SDPS G 6 Bright A_SD_ConsortiumRocket;
		SDPS G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, 0);
		SDPS G 6 Bright A_SD_ConsortiumRocket;
		SDPS G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, SD_CONSORTIUM_FAN_SHIFT);
		SDPS F 12;
		Goto See;
	Barrage:
		SDPS E 8 A_FaceTarget;
		SDPS G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, 0);
		SDPS E 6 A_FaceTarget;
		SDPS G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, SD_CONSORTIUM_FAN_WIDE / 2);
		SDPS E 6 A_FaceTarget;
		SDPS G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, 0);
		SDPS E 12;
		Goto See;
	Sweep:
		SDPS E 8 A_SD_ConsortiumSweepStart;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS G 2 Bright A_SD_ConsortiumSweep;
		SDPS E 10;
		Goto See;

	Pain:
		SDPS H 3;
		SDPS H 3 A_Pain;
		Goto See;
	Death:
		SDPS I 10 A_SD_ConsortiumFall;   // its servants fall with it
		SDPS J 10 A_Scream;
		SDPS K 10;
		SDPS L 10 A_NoBlocking;
		SDPS MN 10;
		SDPS O 30;
		SDPS O -1 A_BossDeath;
		Stop;
	}

	// ------------------------------------------------------------ moving
	// Rooted: turn a little towards the target and let A_Chase decide to
	// attack, never to move. Free: Doom's chase. Either way, the first step
	// under half health is the Breach (checked here, as the General checks
	// his summon, so an attack is never cut in half).
	void A_SD_ConsortiumChase()
	{
		if (!unbound && health > 0 && health < SpawnHealth() * SD_CONSORTIUM_BREACH_FRACTION)
		{
			SetStateLabel("Breach");
			return;
		}
		if (unbound)
		{
			A_Chase();
			return;
		}
		if (target != null)
			A_FaceTarget(SD_CONSORTIUM_ROOTED_TURN);
		A_Chase(flags: CHF_DONTMOVE | CHF_NODIRECTIONTURN);
	}

	void A_SD_ConsortiumStep()
	{
		A_StartSound("sd/mon/consortium/step", CHAN_BODY);
		A_SD_ConsortiumChase();
	}

	// ------------------------------------------------------------ choosing
	// Called on a 0-tic frame at the top of Missile. The portal first, when
	// it is due and there is room; then fire when close; else orbs or
	// rockets (rooted) or the barrage or the volley (free).
	void A_SD_ConsortiumChoose()
	{
		if (target == null)
			return;
		attacksSinceCall++;
		int every = unbound ? SD_CONSORTIUM_CALL_EVERY_FREE : SD_CONSORTIUM_CALL_EVERY_ROOTED;
		if (attacksSinceCall >= every && LiveServants() < ServantCap())
		{
			attacksSinceCall = 0;
			SetStateLabel("Summon");
			return;
		}
		bool close = Distance2D(target) <= SD_CONSORTIUM_FLAME_RANGE;
		bool orbs = random[SD_ConsortiumChoose](0, 255) < SD_CONSORTIUM_ORB_CHANCE;
		if (unbound)
		{
			if (close)
				SetStateLabel("Sweep");
			else if (orbs)
				SetStateLabel("Barrage");
			else
				SetStateLabel("Volley");
		}
		else
		{
			if (close)
				SetStateLabel("Flame");
			else if (orbs)
				SetStateLabel("Orbs");
			else
				SetStateLabel("Rockets");
		}
	}

	// ------------------------------------------------------------ attacks
	void A_SD_ConsortiumRocket()
	{
		if (target == null)
			return;
		A_FaceTarget();
		A_SpawnProjectile("SD_ConsortiumRocket", SD_CONSORTIUM_ARM_Z, SD_CONSORTIUM_REICH_ARM_SIDE);
	}

	// A fan of `count` energy balls, `spread` degrees apart, centred on the
	// target and turned by `shift` degrees.
	void A_SD_ConsortiumOrbFan(int count, double spread, double shift)
	{
		if (target == null)
			return;
		A_FaceTarget();
		double first = shift - spread * (count - 1) / 2;
		for (int i = 0; i < count; i++)
			A_SpawnProjectile("SD_ConsortiumOrb", SD_CONSORTIUM_ARM_Z, SD_CONSORTIUM_LEGION_ARM_SIDE, first + i * spread);
	}

	// One blob of the rooted gout; a report per blob, as the ROKS-3's.
	void A_SD_ConsortiumFlame()
	{
		if (target == null)
			return;
		A_FaceTarget();
		A_StartSound("sd/mon/consortium/flame", CHAN_WEAPON);
		A_SpawnProjectile("SD_ConsortiumFlame", SD_CONSORTIUM_CORE_Z, 0,
			Random2[SD_ConsortiumFlame]() * SD_CONSORTIUM_FLAME_SPREAD_STEP);
	}

	void A_SD_ConsortiumSweepStart()
	{
		sweepStep = 0;
		A_FaceTarget();
	}

	// One blob of the free sweep: it does not turn while it sweeps, so the
	// jet crosses the place you stood.
	void A_SD_ConsortiumSweep()
	{
		if (target == null)
			return;
		A_StartSound("sd/mon/consortium/flame", CHAN_WEAPON);
		A_SpawnProjectile("SD_ConsortiumFlame", SD_CONSORTIUM_CORE_Z, 0,
			SD_CONSORTIUM_SWEEP_FROM + sweepStep * SD_CONSORTIUM_SWEEP_STEP);
		sweepStep++;
	}

	// ------------------------------------------------------------ the portal
	void A_SD_ConsortiumCall()
	{
		A_StartSound("sd/mon/consortium/call", CHAN_VOICE, CHANF_DEFAULT, 1.0, ATTN_NONE);
		SummonServants(unbound ? SD_WAVE_FREE : SD_WAVE_ROOTED, SD_CONSORTIUM_PAIR);
	}

	void A_SD_ConsortiumBreach()
	{
		unbound = true;          // so the chase never comes back here
		bInvulnerable = true;    // the transition reads; nothing is lost in it
		A_StartSound("sd/mon/consortium/breach", CHAN_VOICE, CHANF_DEFAULT, 1.0, ATTN_NONE);
		A_StartSound("sd/weapon/rpg7/explode", CHAN_WEAPON, CHANF_DEFAULT, 1.0, ATTN_NONE);
		A_Quake(SD_CONSORTIUM_BREACH_QUAKE, SD_CONSORTIUM_BREACH_QUAKE_TICS, 0, SD_CONSORTIUM_BREACH_QUAKE_RADIUS);
		A_PrintBold(StringTable.Localize("$SD_CONSORTIUM_FREE"));
	}

	void A_SD_ConsortiumWave()
	{
		A_StartSound("sd/mon/consortium/call", CHAN_VOICE, CHANF_DEFAULT, 1.0, ATTN_NONE);
		SummonServants(SD_WAVE_BREACH, SD_CONSORTIUM_WAVE);
	}

	void A_SD_ConsortiumUnbind()
	{
		bInvulnerable = false;
		Speed = SD_CONSORTIUM_SPEED;
		MissileChanceMult = SD_CONSORTIUM_FREE_MISSILE_CHANCE_MULT;
		A_StartSound("sd/mon/consortium/step", CHAN_BODY);
	}

	void A_SD_ConsortiumFall()
	{
		bInvulnerable = false;   // in case anything ever kills it mid-Breach
		A_KillChildren();        // every servant has it as master
	}

	// The servants alive now; the dead are forgotten.
	int LiveServants()
	{
		int alive = 0;
		for (int i = servants.Size() - 1; i >= 0; i--)
		{
			if (servants[i] == null || servants[i].health <= 0)
				servants.Delete(i);
			else
				alive++;
		}
		return alive;
	}

	int ServantCap()
	{
		return unbound ? SD_CONSORTIUM_CAP_FREE : SD_CONSORTIUM_CAP_ROOTED;
	}

	// Who comes through: always one of each faction, Reich first.
	//   rooted   a Reich rifleman and a Legion trooper (the infantry);
	//   breach   those two, plus a Reich hound and a Doughboy;
	//   free     a Reich hound and a Legion trooper.
	class<Actor> ServantClass(int wave, int i)
	{
		class<Actor> rifleman = "SD_ReichRifleman";   // Reich
		class<Actor> hound    = "SD_ReichHound";      // Reich
		class<Actor> trooper  = "SD_LegionTrooper";   // Legion
		class<Actor> doughboy = "SD_Doughboy";        // Legion
		bool reich = (i % 2 == 0);
		if (wave == SD_WAVE_BREACH && i >= SD_CONSORTIUM_PAIR)
			return reich ? hound : doughboy;
		if (!reich)
			return trooper;
		return (wave == SD_WAVE_FREE) ? hound : rifleman;
	}

	// Spot i, relative to its facing: behind-right, behind-left (the
	// portal), straight behind, then right, left and in front.
	double, double SpotOffset(int i)
	{
		if (i == 0) return -SD_CONSORTIUM_SPOT_BACK, SD_CONSORTIUM_SPOT_PAIR;
		if (i == 1) return -SD_CONSORTIUM_SPOT_BACK, -SD_CONSORTIUM_SPOT_PAIR;
		if (i == 2) return -SD_CONSORTIUM_SPOT_BACK, 0;
		if (i == 3) return 0, SD_CONSORTIUM_SPOT_SIDE;
		if (i == 4) return 0, -SD_CONSORTIUM_SPOT_SIDE;
		return SD_CONSORTIUM_SPOT_SIDE, 0;
	}

	// Up to `count` servants, under the cap, each awake and aimed at its
	// target, never infighting, with it as their master (A_KillChildren).
	void SummonServants(int wave, int count)
	{
		int arrived = 0;
		for (int i = 0; i < SD_CONSORTIUM_SPOTS && arrived < count; i++)
		{
			if (LiveServants() >= ServantCap())
				return;
			double forward, right;
			[forward, right] = SpotOffset(i);
			bool spawned;
			Actor servant;
			[spawned, servant] = A_SpawnItemEx(ServantClass(wave, arrived),
				forward, right, 0, 0, 0, 0, 0, SXF_TRANSFERPOINTERS);
			if (servant == null)
				continue;
			arrived++;
			servant.master = self;
			servant.bNoInfighting = true;
			servants.Push(servant);
			Spawn("TeleportFog", servant.pos, ALLOW_REPLACE);
			if (servant.SeeState != null)
				servant.SetState(servant.SeeState);
		}
	}

	// Nothing a monster does hurts it: not its servants' stray shots, not a
	// Panzermensch's ball that missed you. Players and the world still do.
	override int DamageMobj(Actor inflictor, Actor source, int damage, Name mod, int flags, double angle)
	{
		if (source != null && source != self && source.bIsMonster && source.player == null)
			return 0;
		return Super.DamageMobj(inflictor, source, damage, mod, flags, angle);
	}
}
