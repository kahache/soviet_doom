// SD_General - the episode boss (BESTIARY section 9, D35 option B).
//
// Replaces Doom's Cyberdemon. A three-shell salvo, the Cyberdemon's rhythm
// with a dodgeable projectile, and one verb of his own: the first time his
// health drops below half, he stops, shouts an order and two Reich riflemen
// arrive at his side. He orders; he does not brawl. First placed in MAP03;
// testable today on MAP02's bestiary bench.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: CYBR, laid out like SDGN for
// A-P. The two Summon frames borrow CYBR E and F and become SDGN Q and R:
// the only lines of this file where the swap is more than a rename.

class SD_General : SD_Monster replaces Cyberdemon
{
	const SD_GENERAL_HEALTH     = 3000;   // (H) between Mastermind and Cyberdemon
	const SD_GENERAL_RADIUS     = 40;     // (H) Cyberdemon radius: fits a 128 door
	const SD_GENERAL_HEIGHT     = 100;    // (H) clears a 112 ceiling
	const SD_GENERAL_SPEED      = 12;     // (H) slower than the Cyberdemon's 16
	const SD_GENERAL_MASS       = 1000;   // unmovable
	const SD_GENERAL_PAINCHANCE = 20;     // effectively unstunnable: a boss
	const SD_GENERAL_SALVO      = 3;      // shells per Missile state (one per F frame)
	// Missile behaviour copied from the Cyberdemon (cyberdemon.zs): he fires
	// more readily at range, which is what makes the arena fight a fight.
	const SD_GENERAL_MIN_MISSILE_CHANCE = 160;
	const SD_GENERAL_MISSILE_CHANCE_MULT = 0.5;

	// The summon (D35). Below this fraction of his spawn health, once.
	const SD_GENERAL_SUMMON_FRACTION = 0.5;
	const SD_GENERAL_SUMMON_COUNT    = 2;     // "two recruits"
	// Distance from his centre to a recruit's: his radius 40 + theirs 20 +
	// 12 units of clearance, so a recruit spawned beside him never overlaps.
	const SD_GENERAL_SUMMON_SIDE     = 72;
	const SD_GENERAL_SUMMON_SPOTS    = 4;     // right, left, behind, in front

	// Set before the jump to Summon, so the order is given once per life.
	bool summoned;

	Default
	{
		Health SD_GENERAL_HEALTH;
		Radius SD_GENERAL_RADIUS;
		Height SD_GENERAL_HEIGHT;
		Speed SD_GENERAL_SPEED;
		Mass SD_GENERAL_MASS;
		PainChance SD_GENERAL_PAINCHANCE;
		MinMissileChance SD_GENERAL_MIN_MISSILE_CHANCE;
		MissileChanceMult SD_GENERAL_MISSILE_CHANCE_MULT;
		+BOSS
		+NORADIUSDMG        // the player's own RPG-7 splash must not do the work
		+DONTMORPH
		+BOSSDEATH          // so MAP03's exit can be tied to his death
		Species "SD_General";
		SD_Monster.Faction SD_FACTION_LEGION;
		BloodColor "AD 27 21";     // D49: dark red for every faction (flag_red 9 at full bright, BESTIARY 2.1)
		SeeSound "sd/mon/general/sight";
		PainSound "sd/mon/general/pain";
		DeathSound "sd/mon/general/death";
		ActiveSound "sd/mon/general/active";
		Obituary "$SD_OB_GENERAL";
		Tag "$SD_TAG_GENERAL";
	}

	States
	{
	Spawn:
		CYBR AB 10 A_Look;
		Loop;
	See:
		CYBR AABBCCDD 3 A_SD_GeneralChase;
		Loop;
	Missile:
		CYBR E 6 A_FaceTarget;
		CYBR F 12 A_SD_GeneralShot;
		CYBR E 12 A_FaceTarget;
		CYBR F 12 A_SD_GeneralShot;
		CYBR E 12 A_FaceTarget;
		CYBR F 12 A_SD_GeneralShot;
		Goto See;
	Summon:
		CYBR E 15 Bright A_SD_GeneralSummon;   // final art: SDGN Q
		CYBR F 15;                              // final art: SDGN R
		Goto See;
	Pain:
		CYBR G 10 A_Pain;
		Goto See;
	Death:
		CYBR H 10;
		CYBR I 10 A_Scream;
		CYBR JKL 10;
		CYBR M 10 A_NoBlocking;
		CYBR NO 10;
		CYBR P 30;
		CYBR P -1 A_BossDeath;
		Stop;
	}

	// The chase, unless this is the moment to give the order. Checked here
	// rather than when damage is taken, so a salvo is never cut in half: he
	// finishes shooting and summons on his next step.
	void A_SD_GeneralChase()
	{
		if (!summoned && health > 0 && health < SpawnHealth() * SD_GENERAL_SUMMON_FRACTION)
		{
			summoned = true;
			SetStateLabel("Summon");
			return;
		}
		A_Chase();
	}

	void A_SD_GeneralShot()
	{
		if (target == null)
			return;
		A_FaceTarget();
		SpawnMissile(target, "SD_GeneralShell");
	}

	// The order: a line on every player's screen, a shout heard across the
	// arena, and two riflemen at his sides, awake and already aimed at his
	// target. A_SpawnItemEx refuses to place a monster where it does not fit
	// (gzdoom.pk3 zscript/actors/attacks.zs), so a blocked spot is skipped and
	// the next one tried; a recruit never appears inside a wall.
	void A_SD_GeneralSummon()
	{
		A_StartSound("sd/mon/general/summon", CHAN_VOICE, CHANF_DEFAULT, 1.0, ATTN_NONE);
		A_PrintBold(StringTable.Localize("$SD_GENERAL_ORDER"));

		int arrived = 0;
		for (int i = 0; i < SD_GENERAL_SUMMON_SPOTS && arrived < SD_GENERAL_SUMMON_COUNT; i++)
		{
			// Offsets relative to his facing (A_SpawnItemEx's relative
			// mode): x forward, y to his right. Spot order: right, left,
			// behind, in front.
			double forward = 0;
			double right = 0;
			if (i == 0)
				right = SD_GENERAL_SUMMON_SIDE;
			else if (i == 1)
				right = -SD_GENERAL_SUMMON_SIDE;
			else if (i == 2)
				forward = -SD_GENERAL_SUMMON_SIDE;
			else
				forward = SD_GENERAL_SUMMON_SIDE;

			bool spawned;
			Actor recruit;
			[spawned, recruit] = A_SpawnItemEx("SD_ReichRifleman", forward, right, 0, 0, 0, 0, 0, SXF_TRANSFERPOINTERS);
			if (recruit == null)
				continue;
			arrived++;
			Spawn("TeleportFog", recruit.pos, ALLOW_REPLACE);
			// Wake it straight into the chase, the way Doom's boss brain
			// wakes what its cubes spawn (bossbrain.zs).
			if (recruit.SeeState != null)
				recruit.SetState(recruit.SeeState);
		}
	}
}
