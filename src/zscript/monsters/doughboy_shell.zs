// SD_DoughboyShell - the Doughboy's projectile (BESTIARY section 7).
// CacodemonBall parity. Not placeable.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: BAL2, same layout as SDDL.

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
		BAL2 AB 4 Bright;
		Loop;
	Death:
		BAL2 CDE 6 Bright;
		Stop;
	}
}
