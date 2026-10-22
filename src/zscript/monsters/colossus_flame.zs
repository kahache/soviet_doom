// SD_ColossusFlame - one blob of the Liberty Colossus's short fire jet
// (liberty_colossus.zs). Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep2-enemies.md 3.1).
//
// The ROKS-3's own flame (SD_FlameBlob: SDFJ in flight, SDFX burning out,
// damage 4 x random(1,8), 'Fire', speed 22) with a shorter life: 16 tics of
// flight instead of 24, so 352 units of reach instead of 528. The jet is a
// close-range threat; at range he uses the rockets.

class SD_ColossusFlame : SD_FlameBlob
{
	Default
	{
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
