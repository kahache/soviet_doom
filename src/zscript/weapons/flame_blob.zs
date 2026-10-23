// SD_FlameBlob - the burning jet thrown by the ROKS-3 flamethrower.
//
// A short-lived fire projectile. Its reach is set by how long it lives:
// the Spawn state runs a fixed number of frames and then falls through to
// Death, so range = speed x lifetime instead of an arbitrary cut-off.
//
// Sprites are ours since D82: SDFJ A-B in flight ("flame jet"; not SDFL,
// which with frame R and rotation 1 would spell the floor flat SDFLR1) and
// SDFX A-E on impact (MOD-SPEC 6.3).

class SD_FlameBlob : Actor
{
	// Reference: Doom's PlasmaBall is damage 5 (x random(1,8), avg 22.5) at
	// speed 25 with unlimited range.
	// D119 (2026-10-23, the CEO's playtest of Episodes 2-3: "kills every
	// enemy too easily"): 4 -> 3. One jet averages 13.5 (was 18), so the
	// ROKS-3 drops from 210 to 157.5 damage/s (Doom's rocket launcher) and
	// from 18 to 13.5 per unit of fuel, under the hand Katyusha's ~16.9
	// direct per cell. BALANCE.md slot 6. The bosses' flames keep 4 (their
	// own SD_BOSS_FLAME_DAMAGE): D119 retunes the weapon, not the bosses.
	const SD_FLAME_DAMAGE      = 3;    // x random(1,8) -> 3..24, avg 13.5
	const SD_FLAME_SPEED       = 22;   // map units per tic
	const SD_FLAME_LIFE_TICS   = 2;    // per frame; 12 frames below = 24 tics
	// 22 units/tic x 24 tics = 528 map units of reach (~16 m), the point of
	// a flamethrower: devastating close in, useless across a hangar.

	Default
	{
		Radius 10;
		Height 8;
		Speed SD_FLAME_SPEED;
		Damage SD_FLAME_DAMAGE;
		DamageType "Fire";
		Projectile;
		+RANDOMIZE
		+ZDOOMTRANS
		RenderStyle "Add";
		Alpha 0.85;
		DeathSound "";
		Obituary "$SD_OB_ROKS3";
	}

	States
	{
	Spawn:
		// 12 frames x 2 tics = 24 tics of flight, then the jet burns out.
		SDFJ ABABABABABAB 2 Bright;
		Goto Death;
	Death:
		SDFX ABCDE 3 Bright;
		Stop;
	}
}
