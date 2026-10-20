// SD_GeneralShell - one shell of the General's three-shell salvo (BESTIARY
// section 9). Not placeable.
//
// Sprites are OUR OWN since D73 (2026-10-14): SDGL, a white-hot core in a
// braid-yellow fire with an ember ring (tools/art/gen_general.py --full),
// 5 lumps in assets/sprites/general/, rotation 0: A-B in flight, C-E the
// burst. The placeholders were Freedoom's MANF A-B (Doom's mancubus shot) in
// flight and MISL B-D for the burst, so the Death state took new frame
// letters as well as the new name (BESTIARY 2.7); every tic is as before
// (tests/test_general_sprites.py). RenderStyle Add stays: only the bright
// colours show, as with the placeholders. The PG-7V grenade and the Katyusha
// rocket left MISL too with D82 (SDPX for their burst).

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
		SDGL AB 4 Bright;
		Loop;
	Death:
		SDGL C 8 Bright;
		SDGL D 6 Bright;
		SDGL E 4 Bright;
		Stop;
	}
}
