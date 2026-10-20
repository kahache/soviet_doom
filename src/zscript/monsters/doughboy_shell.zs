// SD_DoughboyShell - the Doughboy's projectile (BESTIARY section 7).
// CacodemonBall parity. Not placeable.
//
// Sprites: ours since D81 (2026-10-20), SDDL A-E, the "comet" (option A of
// tools/art/gen_shells.py): A-B in flight, C-E the burst, rotation 0, in
// assets/sprites/doughboy/. Only the four-letter name changed, every tic is
// as it was. MOD-SPEC 6.3; tests/test_shells_install.py.

class SD_DoughboyShell : Actor
{
	const SD_DOUGHBOYSHELL_RADIUS    = 6;
	const SD_DOUGHBOYSHELL_HEIGHT    = 8;
	const SD_DOUGHBOYSHELL_SPEED     = 10;
	const SD_DOUGHBOYSHELL_FASTSPEED = 20;
	const SD_DOUGHBOYSHELL_DAMAGE    = 5;   // random(1,8) x 5 = 5..40

	Default
	{
		Radius SD_DOUGHBOYSHELL_RADIUS;
		Height SD_DOUGHBOYSHELL_HEIGHT;
		Speed SD_DOUGHBOYSHELL_SPEED;
		FastSpeed SD_DOUGHBOYSHELL_FASTSPEED;
		Damage SD_DOUGHBOYSHELL_DAMAGE;
		Projectile;
		+RANDOMIZE
		+ZDOOMTRANS
		RenderStyle "Add";
		Alpha 1;
		SeeSound "sd/mon/doughboy/missile";
		DeathSound "sd/mon/doughboy/explode";
	}

	States
	{
	Spawn:
		SDDL AB 4 Bright;
		Loop;
	Death:
		SDDL CDE 6 Bright;
		Stop;
	}
}
