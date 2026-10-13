// SD_Monster - the shared base of every enemy in the bestiary (F5).
//
// Contract: docs/engine/BESTIARY.md section 2.4. Every enemy is
// `class SD_X : SD_Monster replaces <DoomMonster>`. Nothing derives from
// ZombieMan, DoomImp and the rest, because inheriting a Doom monster also
// inherits its States block (IWAD sprites), its sounds ("grunt/sight") and
// its obituary strings: one state we forgot to override would show a
// Freedoom sprite in the middle of our fight. Each class writes every state
// out instead. (ADR 006 is owed for this decision; BESTIARY section 13.)
//
// The three attack helpers below have the shape of Doom's own A_PosAttack,
// A_SargAttack and A_TroopAttack (gzdoom.pk3, zscript/actors/doom/
// possessed.zs, demon.zs, doomimp.zs) and use the same engine primitives,
// but take the dice and the sound as arguments: Doom's versions hard-code
// both. A_CustomBulletAttack is not used because it rolls damage x
// random(1,3), and Doom's infantry roll random(1,5) x 3.

// Factions (BESTIARY section 2.1). Read by nothing yet; future HUD and lore
// code will ask an enemy which side it is on. Global constants rather than
// an enum: an int property set from a named constant in a Default block is
// the form the arsenal already runs in the engine.
const SD_FACTION_NONE   = 0;
const SD_FACTION_REICH  = 1;   // Fourth Reich: khaki, organic, the infantry
const SD_FACTION_LEGION = 2;   // Liberty Legion: chrome, pink, the officers
const SD_FACTION_BOTH   = 3;   // the hybrid Stormtrooper only

class SD_Monster : Actor
{
	meta int SDFaction;
	property Faction: SDFaction;

	// Doom's monster hitscan spread: Random2() (-255..255) times 22.5/256
	// degrees, i.e. triangular and at most +-22.4 degrees (A_PosAttack).
	// Monsters are inaccurate on purpose; volume and range are the threat.
	const SD_MONSTER_SPREAD_STEP = 22.5 / 256;

	Default
	{
		Monster;
		+FLOORCLIP
		SD_Monster.Faction SD_FACTION_NONE;
		// MeleeRange is deliberately NOT set: the engine default
		// (64 - MELEEDELTA, plus the target's radius) is Doom's own bite.
	}

	// N hitscan shots, each random(1, dice) x multiplier, one aim slope.
	// Plays AttackSound once, like A_SPosAttackUseAtkSound.
	void A_SD_Hitscan(int shots, int dice, int multiplier)
	{
		if (target == null)
			return;
		A_FaceTarget();
		double aim = angle;
		double slope = AimLineAttack(aim, MISSILERANGE);
		A_StartSound(AttackSound, CHAN_WEAPON);
		for (int i = 0; i < shots; i++)
		{
			double ang = aim + Random2[SD_MonsterHitscan]() * SD_MONSTER_SPREAD_STEP;
			int damage = random[SD_MonsterHitscan](1, dice) * multiplier;
			LineAttack(ang, MISSILERANGE, slope, damage, 'Hitscan', "BulletPuff");
		}
	}

	// A bite or a blow, random(1, dice) x multiplier, if the target is in
	// melee range. No sound here: A_Chase plays AttackSound on entering the
	// Melee state, as Doom's does for the demon.
	void A_SD_Melee(int dice, int multiplier)
	{
		let targ = target;
		if (targ && CheckMeleeRange())
		{
			int damage = random[SD_MonsterMelee](1, dice) * multiplier;
			int newdam = targ.DamageMobj(self, self, damage, 'Melee');
			targ.TraceBleed(newdam > 0 ? newdam : damage, self);
		}
	}

	// Melee if close, otherwise a projectile: Doom's imp, cacodemon and
	// baron pattern. The melee sound is passed in because these monsters
	// have no AttackSound (an AttackSound would also be played by A_Chase).
	// The projectile's own SeeSound is its launch sound.
	void A_SD_MeleeOrMissile(int dice, int multiplier, sound meleesound, class<Actor> missile)
	{
		let targ = target;
		if (targ == null)
			return;
		if (CheckMeleeRange())
		{
			int damage = random[SD_MonsterMelee](1, dice) * multiplier;
			A_StartSound(meleesound, CHAN_WEAPON);
			int newdam = targ.DamageMobj(self, self, damage, 'Melee');
			targ.TraceBleed(newdam > 0 ? newdam : damage, self);
		}
		else
		{
			SpawnMissile(targ, missile);
		}
	}
}
