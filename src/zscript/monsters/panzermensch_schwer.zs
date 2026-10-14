// SD_PanzermenschSchwer - the heavy Panzermensch, 1000 HP, for MAP03
// (BESTIARY section 8, D35). Replaces Doom's BaronOfHell, so a map that
// places thing 3003 gets ours and not a Freedoom baron.
//
// It derives from SD_Panzermensch - the way Doom derives the Hell Knight
// from the Baron - and changes its health, its name, its body and its
// sprite. Doom's Baron also carries +BOSSDEATH for E1M8-style map
// specials; no map of ours uses them.
//
// Sprites are OUR OWN since D67 (2026-10-14): SDPS, cell D with the sweep's
// S2 treatment (black plate, 12 % larger, spikes and exhaust stacks, D65),
// 71 lumps in assets/sprites/panzermensch/ beside the base's SDPM: A-H in
// eight separate rotations, I-O rotation 0; he dies face down, since the
// stacks would prop him off the floor on his back. Its States block is the
// base's line for line with SDPS for SDPM and nothing else changed
// (tests/test_panzermensch_sprites.py pins both against HEAD before D67);
// A_SD_PanzerStep and the melee constants resolve from the base class.
//
// The body grows with the drawing: the figure is modelled 12 % larger than
// the base's (D65's S2; SDPSA1 is 84 px high with the stacks, SDPMA1 68), so
// 64 x 1.12 ~ 72 high and 24 x 1.12 ~ 27 radius, or a shot at the top of
// the stacks would hit nothing. Every place a map puts thing 21107 or 3003 was checked to fit at
// this size (MOD-SPEC 6.3; the test pins it on the built maps).

class SD_PanzermenschSchwer : SD_Panzermensch replaces BaronOfHell
{
	const SD_PANZER_HEAVY_HEALTH = 1000;   // BaronOfHell parity (D35)
	const SD_PANZER_HEAVY_RADIUS = 27;     // 24 x 1.12: the drawing is 12 % larger (D65, D67)
	const SD_PANZER_HEAVY_HEIGHT = 72;     // 64 x 1.12; still clears the >= 72 brute arenas (BESTIARY 8)

	Default
	{
		Health SD_PANZER_HEAVY_HEALTH;
		Radius SD_PANZER_HEAVY_RADIUS;
		Height SD_PANZER_HEAVY_HEIGHT;
		Tag "$SD_TAG_PANZER_HEAVY";
	}

	States
	{
	Spawn:
		SDPS AB 10 A_Look;
		Loop;
	See:
		// One plated footstep per walk cycle (24 tics), as the base.
		SDPS A 3 A_SD_PanzerStep;
		SDPS ABBCCDD 3 A_Chase;
		Loop;
	Melee:
	Missile:
		SDPS EF 8 A_FaceTarget;
		SDPS G 8 A_SD_MeleeOrMissile(SD_PANZER_MELEE_DICE, SD_PANZER_MELEE_MULT, "sd/mon/panzermensch/melee", "SD_PanzerShell");
		Goto See;
	Pain:
		SDPS H 2;
		SDPS H 2 A_Pain;
		Goto See;
	Death:
		SDPS I 8;
		SDPS J 8 A_Scream;
		SDPS K 8;
		SDPS L 8 A_NoBlocking;
		SDPS MN 8;
		SDPS O -1;
		Stop;
	Raise:
		SDPS O 8;
		SDPS NMLKJI 8;
		Goto See;
	}
}
