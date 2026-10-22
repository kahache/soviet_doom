// SD_ConsortiumRocket - one rocket of the Consortium's salvo, fired from its
// Reich arm (consortium.zs). Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep3-final-boss.md 4).
//
// The PG-7V grenade with a monster's numbers, as the Liberty Colossus's
// rocket (colossus_rocket.zs) but its own class, so either boss can change
// without the other: it inherits SD_Pg7Grenade's flight (SDPG, eight
// rotations), its -DEHEXPLOSION and its two sounds, and overrides speed,
// damage, obituary and the burst. It flies THROUGH monsters: the
// Consortium's fire never hurts its own servants, so they never turn on it.

class SD_ConsortiumRocket : SD_Pg7Grenade
{
	const SD_CNROCKET_SPEED        = 20;   // Doom's Rocket speed; the PG-7V flies 28: side-steppable
	const SD_CNROCKET_IMPACT       = 10;   // x random(1,8) = 10..80, avg 45 (Cyberdemon's: avg 90)
	const SD_CNROCKET_BLAST_DAMAGE = 64;   // (H) at the centre, falling off linearly (Rocket: 128)
	const SD_CNROCKET_BLAST_RADIUS = 96;

	Default
	{
		Speed SD_CNROCKET_SPEED;
		Damage SD_CNROCKET_IMPACT;
		Obituary "";   // leave the Consortium's own line, not the RPG-7's
	}

	States
	{
	Death:
		SDPX A 8 Bright A_Explode(SD_CNROCKET_BLAST_DAMAGE, SD_CNROCKET_BLAST_RADIUS);
		SDPX B 6 Bright;
		SDPX C 4 Bright;
		Stop;
	}

	// Through every monster, into players and walls (NOT VERIFIED in play).
	override bool CanCollideWith(Actor other, bool passive)
	{
		if (!passive && other.bIsMonster && other.player == null)
			return false;
		return Super.CanCollideWith(other, passive);
	}
}
