// SD_StormBolt - the Stormtrooper's projectile (BESTIARY section 5).
// DoomImpBall parity: a dodgeable bolt. Not placeable.
//
// Sprites are OUR OWN since D56 (2026-10-14): SDBL A-B flight, C-E burst,
// rotation 0, 5 lumps in assets/sprites/storm/ (tools/art/gen_storm.py
// --full). The swap from Freedoom's BAL1 placeholder renamed the sprite
// only; tics and Bright are as before (tests/test_storm_sprites.py). Doom's
// own DoomImpBall keeps the IWAD's BAL1.

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
		SDBL AB 4 Bright;
		Loop;
	Death:
		SDBL CDE 6 Bright;
		Stop;
	}
}
