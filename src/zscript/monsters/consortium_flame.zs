// SD_ConsortiumFlame - one blob of the Consortium's fire, from the portal
// core in its chest (consortium.zs): the rooted gout and the free sweep.
// Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep3-final-boss.md 4).
//
// The ROKS-3's own flame (SD_FlameBlob: SDFJ in flight, SDFX burning out,
// 'Fire', speed 22) with a shorter life: 16 tics of
// flight instead of 24, so 352 units of reach instead of 528. A close-range
// threat; at range it uses the orbs and the rockets. It flies THROUGH
// monsters, as the rocket does.

class SD_ConsortiumFlame : SD_FlameBlob
{
	// The boss's fire keeps the flame's damage from before D119: 4 x
	// random(1,8) = 4..32, avg 18. D119 cut the ROKS-3's SD_FlameBlob to 3;
	// this keeps the bosses' fight as designed.
	const SD_BOSS_FLAME_DAMAGE = 4;

	Default
	{
		Damage SD_BOSS_FLAME_DAMAGE;
		Obituary "";   // leave the Consortium's own line, not the ROKS-3's
	}

	States
	{
	Spawn:
		// 8 frames x 2 tics = 16 tics x 22 units = 352 units, then it burns out.
		SDFJ ABABABAB 2 Bright;
		Goto Death;
	}

	override bool CanCollideWith(Actor other, bool passive)
	{
		if (!passive && other.bIsMonster && other.player == null)
			return false;
		return Super.CanCollideWith(other, passive);
	}
}
