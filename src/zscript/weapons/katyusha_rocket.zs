// SD_KatyushaRocket - one rocket of the Hand Katyusha salvo.
//
// Smaller and faster than a PG-7V, and it does NOT hurt the person who
// fired it: six of these leave the rails at once and a self-damaging salvo
// would be unusable. Doom's BFG shot does not hurt its owner either, so the
// slot-7 weapon keeps that contract.
//
// Sprites are ours since D82: SDKR A in flight (eight rotations, five
// lumps) and the PG-7V's burst SDPX A-C (MOD-SPEC 6.3).

class SD_KatyushaRocket : Rocket
{
	const SD_KAT_IMPACT_DAMAGE = 25;   // x random(1,8) by the missile rules
	const SD_KAT_BLAST_DAMAGE  = 70;
	const SD_KAT_BLAST_RADIUS  = 96;   // map units
	const SD_KAT_SPEED         = 32;   // faster than the PG-7V: unguided, light
	const SD_KAT_NO_SELF_HARM  = 0;    // A_Explode flags: XF_HURTSOURCE cleared

	Default
	{
		Speed SD_KAT_SPEED;
		Damage SD_KAT_IMPACT_DAMAGE;
		// See SD_Pg7Grenade: Rocket's +DEHEXPLOSION would override our
		// explicit A_Explode arguments.
		-DEHEXPLOSION
		SeeSound "";
		DeathSound "sd/weapon/katyusha/burst";
		Obituary "$SD_OB_KATYUSHA";
	}

	States
	{
	Spawn:
		SDKR A 1 Bright;
		Loop;
	Death:
		SDPX A 6 Bright A_Explode(SD_KAT_BLAST_DAMAGE, SD_KAT_BLAST_RADIUS, SD_KAT_NO_SELF_HARM);
		SDPX B 5 Bright;
		SDPX C 4 Bright;
		Stop;
	}
}
