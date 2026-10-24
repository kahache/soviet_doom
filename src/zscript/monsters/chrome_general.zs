// SD_ChromeGeneral - "The Chrome Marshal" (D123, 2026-10-23): a Liberty
// Colossus variant, MAP08's mini-boss on skills 3 and 4, in the loading bay
// where the colossus stood. Numbers in BESTIARY section 12 (row 12).
//
// Where he comes from. From D116 to D123 the colossus wore the General's
// SDGN, drawn 1.3 times larger and tinted chrome, until Gemini drew his own
// SDLC. The CEO liked both ("Coloso me gustan las 2: colorear general y la
// estatua de la libertad. Quiero los 2 en el juego", D123): the statue is
// MAP06's boss, and that look stays in the game as this enemy, an approved
// design, not a placeholder. Doom's own way of making a new monster out of
// an old one: the General's sprites under a palette swap (as the Hell Knight
// is the Baron in other colours), at 1.3 times his size.
//
// Behaviour: the colossus's, unchanged. He inherits every constant, flag,
// sound and action of SD_LibertyColossus (the three-rocket salvo far, the
// fire jet near, the stomp close; +BOSS, +NORADIUSDMG, +DONTMORPH,
// +BOSSDEATH) and his species, so the two never fight each other. Only the
// look and the name are his: the States below are the colossus's line for
// line on SDGN (the General's frame letters match the verbs: E/F the salvo
// and the jet, Q/R the stomp, G pain, H-P death), plus his own Tag and
// obituaries. Replaces nothing: placed by his own number, 21113.
//
// The look: SDGN (assets/sprites/general/), Scale 1.3 and a Translation
// that maps the whole palette by luminance onto a cold silver gradient. The
// translation on truecolour PNG sprites is NOT VERIFIED in the engine
// (GZDoom palettises a translated graphic): the engine pass checks it.
// His body is the colossus's 88 x 110; the sprite drawn x1.3 (the General's
// Gemini set) stands a little taller than that, as it did from D116.

class SD_ChromeGeneral : SD_LibertyColossus
{
	const SD_CHROME_HEALTH = 3000;   // the colossus's (D119, the Spider Mastermind's): 48 IZh shells (BALANCE 8)
	const SD_CHROME_SCALE  = 1.3;    // the General's SDGN drawn larger, the colossus's stand-in size (D116)

	Default
	{
		Health SD_CHROME_HEALTH;
		Scale SD_CHROME_SCALE;
		// Chrome: the palette by luminance onto a cold silver gradient, the
		// line the colossus wore from D116 to D123.
		Translation "0:255=%[0.05,0.05,0.10]:[1.60,1.60,1.80]";
		Obituary "$SD_OB_CHROME";        // rockets and fire
		HitObituary "$SD_OBHIT_CHROME";  // the stomp ('Melee' damage)
		Tag "$SD_TAG_CHROME";
	}

	States
	{
	Spawn:
		SDGN AB 10 A_Look;
		Loop;
	See:
		SDGN A 3 A_SD_ColossusStep;  // one footfall per cycle, as the Cyberdemon's A_Hoof
		SDGN ABBCCDD 3 A_Chase;
		Loop;
	Missile:
		SDGN E 0 A_SD_ColossusChoose;   // jumps to Flame or Stomp when close; else the salvo
	Rockets:
		SDGN E 10 A_FaceTarget;         // the bazooka comes up: the tell
		SDGN F 8 Bright A_SD_ColossusRocket;
		SDGN E 6 A_FaceTarget;
		SDGN F 8 Bright A_SD_ColossusRocket;
		SDGN E 6 A_FaceTarget;
		SDGN F 8 Bright A_SD_ColossusRocket;
		SDGN E 16 A_FaceTarget;         // recovery: the window to close in or get out
		Goto See;
	Flame:
		SDGN E 10 A_FaceTarget;         // the barrel levels at you
		SDGN F 3 Bright A_SD_ColossusFlame;
		SDGN F 3 Bright A_SD_ColossusFlame;
		SDGN F 3 Bright A_SD_ColossusFlame;
		SDGN F 3 Bright A_SD_ColossusFlame;
		SDGN F 3 Bright A_SD_ColossusFlame;
		SDGN E 12;
		Goto See;
	Stomp:
		SDGN Q 14 A_FaceTarget;         // the General's raised fist: the foot goes up
		SDGN R 6 A_SD_ColossusStomp;    // ... and comes down
		SDGN R 14;
		Goto See;
	Pain:
		SDGN G 10 A_Pain;
		Goto See;
	Death:
		SDGN H 10;
		SDGN I 10 A_Scream;
		SDGN JKL 10;
		SDGN M 10 A_NoBlocking;
		SDGN NO 10;
		SDGN P 30;
		SDGN P -1 A_BossDeath;
		Stop;
	}
}
