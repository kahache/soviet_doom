// SD_LegionGunner - Liberty Legion heavy machine-gunner (D104, Episode 2).
// Design: docs/engine/2026-10-22_P4_ep2-enemies.md section 2; numbers in
// BESTIARY section 12 (row 9). In the mod since D116 (2026-10-22), placed
// in MAP04-MAP09; on his own sprites since D123 (2026-10-23, "Ok gunner").
//
// Doom's chaingunner role with a rhythm of his own: an M1919 belt-fed gun
// at the hip, BURSTS of 4-6 hitscan rounds and then a pause to breathe,
// instead of the chaingunner's hold-until-it-loses-sight. The pause is the
// window the player is meant to use. Replaces Doom's ChaingunGuy (65), the
// one Doom infantryman the bestiary had left alone (MOD-SPEC 6.1).
//
// LOOK (D119, approved D123): SDLG, his own 70 lumps drawn from the CEO's
// Gemini sheets by tools/art/gemini_enemy.py gunner, in
// assets/sprites/legion_gunner/ (the trooper's frame letters: design doc
// section 4). Rotation 1 fires at the
// player (F1: the flash in front of the chest).

class SD_LegionGunner : SD_Monster replaces ChaingunGuy
{
	const SD_GUNNER_HEALTH     = 80;    // (H) ChaingunGuy 70, plus the weight of the gun: survives one IZh barrel (avg 80) half the time
	const SD_GUNNER_RADIUS     = 20;    // infantry parity: corridors are built for it
	const SD_GUNNER_HEIGHT     = 56;
	const SD_GUNNER_SPEED      = 8;     // infantry parity
	const SD_GUNNER_MASS       = 100;
	const SD_GUNNER_PAINCHANCE = 150;   // 59 %: a little less than the trooper's 170 (66 %), the gun steadies him
	// One round per shot frame: random(1,5) x 3 = 3..15, avg 9, the
	// chaingunner's own roll (A_CPosAttack is A_PosAttack's dice).
	const SD_GUNNER_SHOTS      = 1;
	const SD_GUNNER_HIT_DICE   = 5;
	const SD_GUNNER_HIT_MULT   = 3;
	// The burst. Rolled once per Missile state; 4-6 rounds at one every 5
	// tics (Burst below: F 3 + E 2) is 7 rounds a second, a touch under the
	// chaingunner's ~7.8, then 20 tics of pause (Cooldown). Average burst
	// 5 x 9 = 45 if every round lands, which at Doom's spread they do not.
	const SD_GUNNER_BURST_MIN  = 4;
	const SD_GUNNER_BURST_MAX  = 6;

	// Rounds left in the current burst.
	int burstLeft;

	Default
	{
		Health SD_GUNNER_HEALTH;
		Radius SD_GUNNER_RADIUS;
		Height SD_GUNNER_HEIGHT;
		Speed SD_GUNNER_SPEED;
		Mass SD_GUNNER_MASS;
		PainChance SD_GUNNER_PAINCHANCE;
		Species "SD_LegionGunner";       // own species: vanilla infighting holds (BESTIARY 2.2)
		SD_Monster.Faction SD_FACTION_LEGION;
		BloodColor "AD 27 21";           // D49: dark red for every faction
		// His own logical names (SNDINFO), over the trooper's voice and the
		// PPSh-41's report until sound-designer records his (MOD-SPEC 6.2).
		SeeSound "sd/mon/legiongunner/sight";
		AttackSound "sd/mon/legiongunner/attack";
		PainSound "sd/mon/legiongunner/pain";
		DeathSound "sd/mon/legiongunner/death";
		ActiveSound "sd/mon/legiongunner/active";
		Obituary "$SD_OB_GUNNER";
		Tag "$SD_TAG_GUNNER";
		// The Legion's heavy infantry carries captured Warsaw Pact stocks: he
		// drops an AKM magazine (D116; the AKM doc section 3). No amount
		// given, so a dropped one carries half its 30 (Ammo.ModifyDropAmount:
		// 15 rounds at the default skill factor). The AKM lives on gunners,
		// the PPSh-41 on riflemen.
		DropItem "SD_AkmAmmo";
	}

	States
	{
	Spawn:
		SDLG AB 10 A_Look;
		Loop;
	See:
		SDLG AABBCCDD 3 A_Chase;    // infantry parity
		Loop;
	Missile:
		SDLG E 10 A_SD_GunnerAim;   // the gun comes up: the tell
	Burst:
		SDLG F 3 Bright A_SD_GunnerShot;
		SDLG E 2 A_SD_GunnerNext;   // leaves for Cooldown when the burst is spent
		Loop;
	Cooldown:
		SDLG E 20 A_FaceTarget;     // the pause between bursts: the player's window
		Goto See;
	Pain:
		SDLG G 3;
		SDLG G 3 A_Pain;
		Goto See;
	Death:
		SDLG H 5;
		SDLG I 5 A_Scream;
		SDLG J 5 A_NoBlocking;
		SDLG K 5;
		SDLG L -1;
		Stop;
	XDeath:
		SDLG M 5;
		SDLG N 5 A_StartSound("sd/mon/legiongunner/xdeath", CHAN_VOICE);
		SDLG O 5 A_NoBlocking;
		SDLG PQRST 5;
		SDLG U -1;
		Stop;
	Raise:
		SDLG L 5;
		SDLG KJIH 5;
		Goto See;
	}

	// Face the target and roll how long this burst will be.
	void A_SD_GunnerAim()
	{
		A_FaceTarget();
		burstLeft = random[SD_GunnerBurst](SD_GUNNER_BURST_MIN, SD_GUNNER_BURST_MAX);
	}

	// One round of the burst: A_SD_Hitscan faces the target again and plays
	// AttackSound, as A_CPosAttack does every round.
	void A_SD_GunnerShot()
	{
		burstLeft--;
		A_SD_Hitscan(SD_GUNNER_SHOTS, SD_GUNNER_HIT_DICE, SD_GUNNER_HIT_MULT);
	}

	// Keep firing while rounds are left and the target is alive and in
	// sight; otherwise stop and breathe. The shape of A_CPosRefire
	// (gzdoom.pk3 zscript/actors/doom/possessed.zs) with a count instead of
	// its random escape.
	void A_SD_GunnerNext()
	{
		if (burstLeft <= 0 || target == null || target.health <= 0 || !CheckSight(target))
			SetStateLabel("Cooldown");
	}
}
