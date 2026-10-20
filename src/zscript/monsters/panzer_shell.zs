// SD_PanzerShell - the Panzermensch's projectile (BESTIARY section 8).
// BaronBall parity: faster than the bolt and the Doughboy's shell, which is
// how a Doom player reads the threat from the projectile alone. Not placeable.
//
// Sprites: ours since D81 (2026-10-20), SDPL A-E, the "ember" (option A of
// tools/art/gen_shells.py): A-B in flight, C-E the burst, rotation 0, in
// assets/sprites/panzermensch/. Only the four-letter name changed, every
// tic is as it was. MOD-SPEC 6.3; tests/test_shells_install.py.

class SD_PanzerShell : Actor
{
	const SD_PANZERSHELL_RADIUS    = 6;
	const SD_PANZERSHELL_HEIGHT    = 16;
	const SD_PANZERSHELL_SPEED     = 15;
	const SD_PANZERSHELL_FASTSPEED = 20;
	const SD_PANZERSHELL_DAMAGE    = 8;   // random(1,8) x 8 = 8..64

	Default
	{
		Radius SD_PANZERSHELL_RADIUS;
		Height SD_PANZERSHELL_HEIGHT;
		Speed SD_PANZERSHELL_SPEED;
		FastSpeed SD_PANZERSHELL_FASTSPEED;
		Damage SD_PANZERSHELL_DAMAGE;
		Projectile;
		+RANDOMIZE
		+ZDOOMTRANS
		RenderStyle "Add";
		Alpha 1;
		SeeSound "sd/mon/panzermensch/missile";
		DeathSound "sd/mon/panzermensch/explode";
	}

	States
	{
	Spawn:
		SDPL AB 4 Bright;
		Loop;
	Death:
		SDPL CDE 6 Bright;
		Stop;
	}
}
