// SD_GeneralShell - one shell of the General's three-shell salvo (BESTIARY
// section 9). Not placeable.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS, borrowed from Doom's mancubus
// shot: MANF A-B in flight, MISL B-D for the burst. The final SDGL is laid
// out A-B flight, C-E burst, so the Death state needs new frame letters as
// well as the new name when the art lands (BESTIARY 2.7).

class SD_GeneralShell : Actor
{
	const SD_GENERALSHELL_RADIUS = 6;
	const SD_GENERALSHELL_HEIGHT = 8;
	// (H) Fast enough to punish standing still, slow enough to sidestep at
	// twenty metres. Already at Doom's fast-projectile speed, so no FastSpeed.
	const SD_GENERALSHELL_SPEED  = 20;
	const SD_GENERALSHELL_DAMAGE = 8;     // random(1,8) x 8 = 8..64, BaronBall parity

	Default
	{
		Radius SD_GENERALSHELL_RADIUS;
		Height SD_GENERALSHELL_HEIGHT;
		Speed SD_GENERALSHELL_SPEED;
		Damage SD_GENERALSHELL_DAMAGE;
		Projectile;
		+RANDOMIZE
		+ZDOOMTRANS
		RenderStyle "Add";
		Alpha 1;
		SeeSound "sd/mon/general/missile";
		DeathSound "sd/mon/general/explode";
	}

	States
	{
	Spawn:
		MANF AB 4 Bright;
		Loop;
	Death:
		MISL B 8 Bright;
		MISL C 6 Bright;
		MISL D 4 Bright;
		Stop;
	}
}
