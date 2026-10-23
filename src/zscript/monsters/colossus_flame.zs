// SD_ColossusFlame - one blob of the Liberty Colossus's short fire jet
// (liberty_colossus.zs). Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep2-enemies.md 3.1).
//
// The ROKS-3's own flame (SD_FlameBlob: SDFJ in flight, SDFX burning out,
// 'Fire', speed 22) with a shorter life: 16 tics of
// flight instead of 24, so 352 units of reach instead of 528. The jet is a
// close-range threat; at range he uses the rockets.

class SD_ColossusFlame : SD_FlameBlob
{
	// The boss's fire keeps the flame's damage from before D119: 4 x
	// random(1,8) = 4..32, avg 18. D119 cut the ROKS-3's SD_FlameBlob to 3;
	// this keeps the bosses' fight as designed.
	const SD_BOSS_FLAME_DAMAGE = 4;

	Default
	{
		Damage SD_BOSS_FLAME_DAMAGE;
		Obituary "";   // leave the colossus's own line, not the ROKS-3's
	}

	States
	{
	Spawn:
		// 8 frames x 2 tics = 16 tics x 22 units = 352 units, then it burns out.
		SDFJ ABABABAB 2 Bright;
		Goto Death;
	}
}
