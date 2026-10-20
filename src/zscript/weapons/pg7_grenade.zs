// SD_Pg7Grenade - the PG-7V round fired by the RPG-7 (SD_Rpg7).
//
// A "projectile" in GZDoom is an ordinary actor with the Projectile flag
// combination: it flies, and on impact it enters its Death state, where
// A_Explode deals radius damage.
//
// A PG-7V is a shaped charge: it punches much harder on a direct hit than a
// Doom rocket but its blast is tighter. Sprites are ours since D82: SDPG A
// in flight (eight rotations, five lumps) and SDPX A-C for the burst, which
// the Katyusha rocket shares (MOD-SPEC 6.3).

class SD_Pg7Grenade : Rocket
{
	// Reference: Doom's Rocket is 20 impact damage, 128 blast over 128 units,
	// speed 20 (map units per tic).
	const SD_PG7_IMPACT_DAMAGE = 30;   // x random(1,8) -> 30..240, avg 135
	const SD_PG7_BLAST_DAMAGE  = 100;  // at the centre, falling off linearly
	const SD_PG7_BLAST_RADIUS  = 104;  // map units; tighter than Doom's 128
	const SD_PG7_SPEED         = 28;   // the PG-7V is a fast, flat-flying round

	Default
	{
		Speed SD_PG7_SPEED;
		Damage SD_PG7_IMPACT_DAMAGE;
		// Rocket carries +DEHEXPLOSION, which makes A_Explode ignore its own
		// arguments in favour of DEHACKED values. We pass explicit numbers,
		// so the flag has to go.
		-DEHEXPLOSION
		SeeSound "sd/weapon/rpg7/fire";
		DeathSound "sd/weapon/rpg7/explode";
		Obituary "$SD_OB_RPG7";
	}

	States
	{
	Spawn:
		SDPG A 1 Bright;
		Loop;
	Death:
		// XF_HURTSOURCE is the default: the RPG-7 can kill the sergeant, as
		// Doom's rocket launcher can. Deliberate - it is the risk weapon.
		SDPX A 8 Bright A_Explode(SD_PG7_BLAST_DAMAGE, SD_PG7_BLAST_RADIUS);
		SDPX B 6 Bright;
		SDPX C 4 Bright;
		Stop;
	}
}
