// SD_PanzerShell - the Panzermensch's projectile (BESTIARY section 8).
// BaronBall parity: faster than the bolt and the Doughboy's shell, which is
// how a Doom player reads the threat from the projectile alone. Not placeable.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: BAL7, same layout as SDPL.

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
		BAL7 AB 4 Bright;
		Loop;
	Death:
		BAL7 CDE 6 Bright;
		Stop;
	}
}
