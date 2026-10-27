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
// section 12 (row 11). In the mod since D116 (2026-10-22), on its own
// sprite (SDCN) since D128 (2026-10-24; the CEO: "Ok consorcio"); MAP09
// places it (src/maps/MAP09/map.py, BOSS_KIND "consortium").
//
// Two phases, split at half health:
//   ROOTED (4000-2001)  plugged into the portal: it does not walk, it turns
//       slowly to follow you. The Reich arm fires rocket salvoes, the Legion
//       arm fans of energy balls, the core a gout of fire when you are
//       close; every fourth attack the portal behind it lets through a pair
//       of reinforcements, one of each faction.
//   BREACH              at half health, once: invulnerable for 65 tics, the
//       ground shakes, a line on every screen, a wave of four reinforcements,
//       and it tears the cables out. Where the map asks for it, the ground
//       opens too (V3 A3, below).
//   FREE (2000-0)       it walks (slowly) and fights harder: rockets and
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
// The ground that opens (V3 A3, D120; MAP09's design section 18.3). At the
// Breach's first tic, once, the boss sinks the sectors tagged with its
// placed thing's arg4 one step into the acid beside them
// (Floor_LowerToLowestTxTy: the floor takes the flat and the damage of the
// neighbour it sinks to) and sets them flickering. The tag rides arg4
// because the thing's special is its death's Door_Open (tag, speed,
// lighttag), which reads arg0-arg2 only; a summoned boss, or one placed
// without arg4, has 0 there and opens nothing, so the class stays
// map-agnostic and tag 15 means nothing on any other map. Calling an action
// special by name is gzdoom.pk3's own way (strife/alienspectres.zs:
// `Floor_LowerToLowest(999, 8)`; doom/keen.zs: `Door_Open(doortag, 16)`).
//
// LOOK: SDCN, its own 95 lumps drawn from the CEO's Gemini sheets by
// tools/art/consortium_gemini.py (gemini_enemy.py's CONSORTIUM), in
// assets/sprites/consortium/ (design doc section 5), at full size: no
// Scale, no tint. Eight rotations of its own (the halves are not mirror
// images). Rooted it shows Q R (Spawn, See), free A-D (Walk); E the
// Legion arm's tell, F the Reich arm's, G firing, H pain, S the Breach's
// first frames, I-O death.
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
	// D119 (2026-10-23): the CEO wants the bosses at classic Doom's level.
	// 9000 (the colossus's old 4500 x 2) -> 4000, the Cyberdemon's. The
	// two phases and the Breach at half health are unchanged (2000 each).
	const SD_CONSORTIUM_HEALTH     = 4000;  // Cyberdemon parity (D119; was 9000, D112 brief)
	const SD_CONSORTIUM_RADIUS     = 56;    // 112 wide: the crater is 2048 square, the terraces 64 deep
	const SD_CONSORTIUM_HEIGHT     = 128;   // the crater's sky is 640 over its floor
	const SD_CONSORTIUM_SPEED      = 8;     // (H) once free; slower than the colossus's 10
	const SD_CONSORTIUM_MASS       = 10000; // rooted in the portal: nothing moves it
	const SD_CONSORTIUM_PAINCHANCE = 10;    // half the General's 20: a boss that barely flinches
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
	// The ground that opens at the Breach (V3 A3; see the header).
	const SD_CONSORTIUM_BREACH_TAG_ARG    = 4;    // which of the placed thing's args names the tag
	const SD_CONSORTIUM_BREACH_SINK_SPEED = 16;   // 2 units a tic: a 16 step in 8 tics, under the quake
	const SD_CONSORTIUM_BREACH_GLOW_UPPER = 176;  // the opened ground flickers as bright as a pit's acid
	const SD_CONSORTIUM_BREACH_GLOW_LOWER = 112;  // ... and down to a shade under the crater's 160

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
		// The General's boss flags, one for one.
		+BOSS
		+NORADIUSDMG        // the player's own RPG-7 splash must not do the work
		+DONTMORPH
		+BOSSDEATH          // A_BossDeath below: MAPINFO SpecialAction can name it
		+NOINFIGHTING       // it never turns on its own servants (NOT VERIFIED)
		Species "SD_Consortium";
		SD_Monster.Faction SD_FACTION_BOTH;   // both factions in one body
		BloodColor "AD 27 21";     // D49: dark red for every faction
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
		SDCN QR 10 A_Look;
		Loop;
	See:
		SDCN Q 0 A_JumpIf(unbound, "Walk");
		// Rooted: it breathes and turns, it does not walk.
		SDCN Q 6 A_SD_ConsortiumChase;
		SDCN R 6 A_SD_ConsortiumChase;
		Loop;
	Walk:
		SDCN A 3 A_SD_ConsortiumStep;   // one footfall per cycle
		SDCN ABBCCDD 3 A_SD_ConsortiumChase;
		Loop;
	Missile:
		SDCN E 0 A_SD_ConsortiumChoose;  // always jumps; falls into Orbs only without a target

	// ---- phase 1, rooted --------------------------------------------------
	Orbs:
		SDCN E 12 A_FaceTarget;          // the Legion arm comes up: the tell
		SDCN G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, 0);
		SDCN E 10 A_FaceTarget;
		SDCN G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, SD_CONSORTIUM_FAN_SHIFT);
		SDCN E 16;                       // recovery: the window
		Goto See;
	Rockets:
		SDCN F 12 A_FaceTarget;          // the Reich arm comes up
		SDCN G 8 Bright A_SD_ConsortiumRocket;
		SDCN F 6 A_FaceTarget;
		SDCN G 8 Bright A_SD_ConsortiumRocket;
		SDCN F 6 A_FaceTarget;
		SDCN G 8 Bright A_SD_ConsortiumRocket;
		SDCN F 16;
		Goto See;
	Flame:
		SDCN E 10 A_FaceTarget;          // the core opens
		SDCN G 3 Bright A_SD_ConsortiumFlame;
		SDCN G 3 Bright A_SD_ConsortiumFlame;
		SDCN G 3 Bright A_SD_ConsortiumFlame;
		SDCN G 3 Bright A_SD_ConsortiumFlame;
		SDCN G 3 Bright A_SD_ConsortiumFlame;
		SDCN E 12;
		Goto See;
	Summon:
		SDCN E 15 Bright A_SD_ConsortiumCall;   // the portal behind it flares; two come through
		SDCN F 10;
		Goto See;

	// ---- the breach, once, at half health ---------------------------------
	Breach:
		SDCN S 10 A_SD_ConsortiumBreach;        // invulnerable; the ground shakes; the line
		SDCN S 10;
		SDCN E 20 Bright A_SD_ConsortiumWave;   // four come through at once
		SDCN F 15 Bright;
		SDCN G 10 Bright A_SD_ConsortiumUnbind; // the cables tear: it walks, and can be hurt
		Goto See;

	// ---- phase 2, free ----------------------------------------------------
	Volley:
		SDCN F 8 A_FaceTarget;           // both arms come up
		SDCN G 6 Bright A_SD_ConsortiumRocket;
		SDCN G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, 0);
		SDCN G 6 Bright A_SD_ConsortiumRocket;
		SDCN G 6 Bright A_SD_ConsortiumOrbFan(3, SD_CONSORTIUM_FAN, SD_CONSORTIUM_FAN_SHIFT);
		SDCN F 12;
		Goto See;
	Barrage:
		SDCN E 8 A_FaceTarget;
		SDCN G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, 0);
		SDCN E 6 A_FaceTarget;
		SDCN G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, SD_CONSORTIUM_FAN_WIDE / 2);
		SDCN E 6 A_FaceTarget;
		SDCN G 4 Bright A_SD_ConsortiumOrbFan(5, SD_CONSORTIUM_FAN_WIDE, 0);
		SDCN E 12;
		Goto See;
	Sweep:
		SDCN E 8 A_SD_ConsortiumSweepStart;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN G 2 Bright A_SD_ConsortiumSweep;
		SDCN E 10;
		Goto See;

	Pain:
		SDCN H 3;
		SDCN H 3 A_Pain;
		Goto See;
	Death:
		SDCN I 10 A_SD_ConsortiumFall;   // its servants fall with it
		SDCN J 10 A_Scream;
		SDCN K 10;
		SDCN L 10 A_NoBlocking;
		SDCN MN 10;
		SDCN O 30;
		SDCN O -1 A_BossDeath;
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
		A_SD_ConsortiumOpenGround();
	}

	// Once (the Breach runs once): the sectors tagged with the placed
	// thing's arg4 sink one step to their lowest neighbour, taking its flat
	// and its damage (on MAP09 the crater's acid pits), and flicker. Tag 0
	// (summoned, or no arg4) opens nothing.
	void A_SD_ConsortiumOpenGround()
	{
		int tag = args[SD_CONSORTIUM_BREACH_TAG_ARG];
		if (tag <= 0)
			return;
		Floor_LowerToLowestTxTy(tag, SD_CONSORTIUM_BREACH_SINK_SPEED);
		Light_Flicker(tag, SD_CONSORTIUM_BREACH_GLOW_UPPER, SD_CONSORTIUM_BREACH_GLOW_LOWER);
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
