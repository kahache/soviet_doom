// SD_Rgd5Grenade - one thrown RGD-5 (V3, A4; ADR 012). Thrown by SD_Rgd5
// (rgd5.zs). Design and balance: docs/engine/2026-10-23_V3_rgd5.md.
//
// A FUSED grenade, not an impact one. It flies in an arc (gravity on),
// bounces short off walls, floors, ceilings and monsters, comes to rest, and
// bursts when the fuse has burned SD_RGD5_FUSE_TICS from the throw, wherever
// it is by then. That is what lets the sergeant throw it round a corner.
//
// Why the fuse is our own counter and not Strife's pattern. GZDoom's own
// grenades (gzdoom.pk3 g4.14.2, zscript/actors/strife/weapongrenade.zs,
// HEGrenade) count ReactionTime down with A_Countdown and explode in their
// Death state; but a bouncing missile also enters Death when it stops
// bouncing (BounceType "Doom" switches bouncing off once it is slow, and the
// next floor contact "explodes" it, P_ExplodeMissile), so Strife's grenade
// bursts the moment it comes to rest. Here Death means only "stopped": the
// grenade lies there with the fuse still burning, and the burst is a state
// of its own, Detonate, which only the fuse reaches. When P_ExplodeMissile
// puts it in Death it also clears MISSILE and zeroes its speed; gravity
// still pulls it (-NOGRAVITY), so one stopped in the air drops to the floor.
// The engine half (when exactly a bounce turns into Death) is C++, NOT
// VERIFIED in the engine (D26).
//
// The blast hurts the thrower (XF_HURTSOURCE), as the RPG-7's does: a
// grenade that bounces back off a wall is the risk. The bosses (the General,
// the colossus, the Consortium) have +NORADIUSDMG and take nothing from it,
// on purpose (BALANCE.md section 3, slot 8).
//
// ITS OWN LOOK since 2026-10-25 (D133, "Ok granada"; D116 had it on
// the health bonus's SDHB A, tinted gunmetal): SDRN A in flight and at
// rest, assets/sprites/rgd5/, the project lead's Gemini grenade turned 35
// degrees and a little smaller (tools/art/gen_rgd5_pickups.py). The burst
// is the PG-7V's SDPX A-C, which stays. Only the sprite name changed and
// the tint line went; every tic, action and jump stayed (MOD-SPEC 6.12;
// tests/test_rgd5_sprites.py).

class SD_Rgd5Grenade : Actor
{
	// --- Balance constants (docs/engine/2026-10-23_V3_rgd5.md section 2) ---
	// Reference: the PG-7V (pg7_grenade.zs) is 30 x random(1,8) on impact
	// (avg 135) plus 100 blast over 104 units: about 235 on the one it hits.
	// The RGD-5 has no impact damage at all and the PG-7V's 100 blast spread
	// wider: under the RPG-7 on any single target, better against a group.
	const SD_RGD5_BLAST_DAMAGE = 100;   // at the centre, falling off linearly (Doom's A_Explode)
	const SD_RGD5_BLAST_RADIUS = 128;   // map units: Doom's rocket's; the PG-7V's shaped charge is 104
	const SD_RGD5_FULL_RADIUS  = 0;     // no full-damage core: the falloff starts at the centre
	const SD_RGD5_FUSE_TICS    = 60;    // 1.71 s from the throw (35 tics a second); the real one is 3.2-4.2 s
	const SD_RGD5_SPEED        = 24;    // map units a tic on release: ~310 units on the flat, ~600 aimed 30 degrees up
	const SD_RGD5_BOUNCE       = 0.35;  // floor and ceiling: a short bounce, a steel egg on concrete
	const SD_RGD5_WALL_BOUNCE  = 0.4;   // off a wall it comes back slowly enough to see it coming
	const SD_RGD5_RADIUS       = 5;     // a 58 mm body: it fits through any gap a player sees through
	const SD_RGD5_HEIGHT       = 8;

	int burnt;   // tics the fuse has burned since the throw

	Default
	{
		Radius SD_RGD5_RADIUS;
		Height SD_RGD5_HEIGHT;
		Speed SD_RGD5_SPEED;
		Damage 0;                        // no impact damage: it bounces off monsters
		Mass 20;                         // Strife's HEGrenade's
		Projectile;
		-NOGRAVITY                       // the arc
		+SKYEXPLODE                      // into a sky it stops and falls back (Death), not vanishes: NOT VERIFIED
		+BOUNCEONACTORS                  // off a monster, as Strife's HEGrenade
		BounceType "Doom";               // walls, floors, ceilings, actors; bouncing stops once slow
		BounceFactor SD_RGD5_BOUNCE;
		WallBounceFactor SD_RGD5_WALL_BOUNCE;
		BounceSound "sd/weapon/rgd5/bounce";
		MaxStepHeight 4;                 // Strife's HEGrenade's: it does not climb steps as it slides
		Obituary "$SD_OB_RGD5";
	}

	States
	{
	Spawn:
		// In flight: one frame, the fuse burning.
		SDRN A 1 A_SD_BurnFuse;
		Loop;
	Death:
		// Stopped (it hit something it does not bounce off, or came to rest):
		// it lies there and the fuse keeps burning. NOT the burst.
		SDRN A 1 A_SD_BurnFuse;
		Loop;
	Detonate:
		// Reached only by A_SD_BurnFuse. The PG-7V's burst, 8 + 6 + 4 tics.
		SDPX A 8 Bright A_SD_Detonate;
		SDPX B 6 Bright;
		SDPX C 4 Bright;
		Stop;
	}

	// One tic of fuse, in flight or at rest; the burst when it has burned out.
	void A_SD_BurnFuse()
	{
		burnt++;
		if (burnt >= SD_RGD5_FUSE_TICS)
			SetStateLabel("Detonate");
	}

	// The burst where it lies: stop it (a grenade still flying when the fuse
	// ends bursts in the air, and the burst must not keep moving or fall),
	// the sound, then the blast. alert: a grenade going off wakes the room it
	// lands in, as Strife's does (A_Explode's own flag).
	void A_SD_Detonate()
	{
		A_Stop();
		bNoGravity = true;
		A_StartSound("sd/weapon/rgd5/explode", CHAN_BODY);
		A_Explode(SD_RGD5_BLAST_DAMAGE, SD_RGD5_BLAST_RADIUS, XF_HURTSOURCE, true, SD_RGD5_FULL_RADIUS);
	}
}
