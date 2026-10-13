// SD_StormBolt - the Stormtrooper's projectile (BESTIARY section 5).
// DoomImpBall parity: a dodgeable bolt. Not placeable.
//
// Sprites are Freedoom (IWAD) PLACEHOLDERS: BAL1, same layout as SDBL
// (A-B flight, C-E burst).

class SD_StormBolt : Actor
{
	const SD_STORMBOLT_RADIUS    = 6;
	const SD_STORMBOLT_HEIGHT    = 8;
	const SD_STORMBOLT_SPEED     = 10;   // Doom's dodgeable-fireball speed
	const SD_STORMBOLT_FASTSPEED = 20;   // under fast monsters / skill 5
	const SD_STORMBOLT_DAMAGE    = 3;    // engine rolls random(1,8) x 3 = 3..24

	Default
	{
		Radius SD_STORMBOLT_RADIUS;
		Height SD_STORMBOLT_HEIGHT;
		Speed SD_STORMBOLT_SPEED;
		FastSpeed SD_STORMBOLT_FASTSPEED;
		Damage SD_STORMBOLT_DAMAGE;
		Projectile;
		+RANDOMIZE
		+ZDOOMTRANS
		RenderStyle "Add";
		Alpha 1;
		SeeSound "sd/mon/stormtrooper/missile";
		DeathSound "sd/mon/stormtrooper/explode";
	}

	States
	{
	Spawn:
		BAL1 AB 4 Bright;
		Loop;
	Death:
		BAL1 CDE 6 Bright;
		Stop;
	}
}
