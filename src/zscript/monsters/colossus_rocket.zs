// SD_ColossusRocket - one rocket of the Liberty Colossus's three-rocket
// salvo, fired from the torch (liberty_colossus.zs). Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep2-enemies.md 3.1).
//
// The PG-7V grenade with a monster's numbers: it inherits SD_Pg7Grenade's
// flight (SDPG, its eight-rotation sprite), its -DEHEXPLOSION and its two
// sounds (the RPG-7's launch and burst, existing SNDINFO names), and
// overrides speed, damage, obituary and the burst. Slower than the player's
// grenade so a salvo can be side-stepped; half a Cyberdemon rocket each,
// because three come at once.

class SD_ColossusRocket : SD_Pg7Grenade
{
	const SD_CROCKET_SPEED        = 20;   // Doom's Rocket speed; the PG-7V flies 28
	const SD_CROCKET_IMPACT       = 10;   // x random(1,8) = 10..80, avg 45 (Cyberdemon's: 20, avg 90)
	const SD_CROCKET_BLAST_DAMAGE = 64;   // (H) at the centre, falling off linearly (Rocket: 128)
	const SD_CROCKET_BLAST_RADIUS = 96;

	Default
	{
		Speed SD_CROCKET_SPEED;
		Damage SD_CROCKET_IMPACT;
		// No RPG-7 line when he kills you: an empty projectile obituary
		// leaves the colossus's own (SD_OB_COLOSSUS), as the General's
		// shell leaves his.
		Obituary "";
	}

	States
	{
	Death:
		SDPX A 8 Bright A_Explode(SD_CROCKET_BLAST_DAMAGE, SD_CROCKET_BLAST_RADIUS);
		SDPX B 6 Bright;
		SDPX C 4 Bright;
		Stop;
	}
}
