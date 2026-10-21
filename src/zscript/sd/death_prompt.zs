// SD_DeathPrompt - "Press <use key> to continue" on the dead player's
// screen (D100, v1.1).
//
// Contract: docs/engine/MOD-SPEC.md 6.10. Registered in MAPINFO -> GameInfo
// -> AddEventHandlers (an EventHandler is created for every map, so nothing
// survives a restart or a load but what a fresh map gives it).
//
// WHY. When the player dies, Doom freezes the view on the floor and waits
// for the USE key; nothing on screen says so, and the CEO did not know what
// to do (D100). The engine already does the right thing on USE; this
// handler only TELLS the player, it changes no rule.
//
// WHAT USE DOES AFTER DEATH (gzdoom g4.14.2 source, read 2026-10-21):
//   * PlayerPawn.DeathThink (gzdoom.pk3:zscript/actors/player/player.zs,
//     lines 767-773): BT_USE sets playerstate to PST_ENTER in single player
//     (PST_REBORN in multiplayer, or with allowrespawn,
//     sv_singleplayerrespawn or a skill's PlayerRespawn; the mod sets none).
//     A human player's USE does not wait for respawn_time.
//   * G_Ticker (src/g_game.cpp 1156-1158) then calls DoReborn, which in
//     single player (src/g_game.cpp 1773-1787) LOADS BackupSaveName - the
//     last save written or loaded this session: the autosave made on
//     entering MAP02 or MAP03, or the player's own save - unless
//     cl_restartondeath is on or there is none; else it restarts the map
//     from scratch with G_InitNew (a fresh player, pistol start).
//   * The level-entry autosave is made on map changes only (G_DoWorldDone
//     -> G_DoLoadLevel(..., autosave = true), src/g_level.cpp 1578), never
//     on New Game (src/g_level.cpp 659), while disableautosave < 1
//     (src/g_level.cpp 1527), and never while dead (src/d_net.cpp 2524).
//   So with the engine's defaults USE continues in the same map: MAP01
//   restarts, MAP02/MAP03 reload their entry autosave. Nothing to change.
//
// HOW. WorldTick (play side, so a paused game or an open menu does not
// count) counts the console player's tics in PST_DEAD; RenderOverlay (UI)
// draws the line once SD_PROMPT_DELAY_TICS have passed, blinking. The key
// is the first one bound to +use (Bindings, the engine's key table), with
// the engine's own "Use / Open" string when nothing is bound. The text is
// the LANGUAGE id SD_DEATH_PROMPT, "%s" standing for the key.
//
// FONT. BigFont, the mod's (fonts/bigfont/, alphabet C, D24): the font of
// the level names, with no Cyrillic substitution, so a key named "E" reads
// E (SDMENU would draw it Э: D22 keeps key prompts in Latin, MOD-SPEC 6.6).
// It is drawn at the menus' integer scale (CleanXFac) and smaller when the
// line would not fit SD_MAX_WIDTH; when even scale 1 does not fit (the
// Russian line on a 320-wide screen) it falls back to SmallFont. Both fonts
// are capitals-only and the engine draws lowercase with the capitals
// (src/common/fonts/font.cpp 780-788). A player with ui_generic on gets
// NewSmallFont, as the engine's own menus do.

class SD_DeathPrompt : EventHandler
{
	// ~1.5 s: DeathThink sinks the view 1 unit per tic from eye height to 6
	// (player.zs), about a second; the prompt comes once the camera rests.
	const SD_PROMPT_DELAY_TICS = 52;

	// One blink a second (TICRATE 35): shown 24 tics, hidden 11.
	const SD_BLINK_PERIOD_TICS = 35;
	const SD_BLINK_ON_TICS = 24;

	// LANGUAGE: "Press %s to continue" and its translations.
	const SD_PROMPT_ID = "$SD_DEATH_PROMPT";
	const SD_KEY_PLACEHOLDER = "%s";

	// The console command DeathThink reads as BT_USE.
	const SD_USE_COMMAND = "+use";
	// Engine string (gzdoom.pk3:language.0): "Use / Open", in every
	// language the engine ships.
	const SD_USE_FALLBACK_ID = "$CNTRLMNU_USE";

	// The line keeps a margin of 5 % on each side.
	const SD_MAX_WIDTH = 0.9;

	// Tics the console player has been dead. Transient: never written to a
	// save (a fresh map starts at 0, and the engine refuses to save while
	// the player is dead).
	transient int deadTics;

	override void WorldTick()
	{
		if (playeringame[consoleplayer] && players[consoleplayer].playerstate == PST_DEAD)
		{
			deadTics++;
		}
		else
		{
			deadTics = 0;
		}
	}

	override void RenderOverlay(RenderEvent e)
	{
		if (gamestate != GS_LEVEL || deadTics < SD_PROMPT_DELAY_TICS)
		{
			return;
		}
		if (!playeringame[consoleplayer] || players[consoleplayer].playerstate != PST_DEAD)
		{
			return;
		}
		if ((deadTics - SD_PROMPT_DELAY_TICS) % SD_BLINK_PERIOD_TICS >= SD_BLINK_ON_TICS)
		{
			return;
		}

		String text = StringTable.Localize(SD_PROMPT_ID);
		text.Substitute(SD_KEY_PLACEHOLDER, SD_UseKeyName());

		Font fnt = generic_ui ? NewSmallFont : BigFont;
		int scale = SD_FitScale(fnt, text);
		if (scale == 0 && !generic_ui)
		{
			fnt = SmallFont;
			scale = SD_FitScale(fnt, text);
		}
		scale = max(scale, 1);

		double x = (Screen.GetWidth() - fnt.StringWidth(text) * scale) / 2.;
		double y = (Screen.GetHeight() - fnt.GetHeight() * scale) / 2.;
		Screen.DrawText(fnt, Font.CR_GOLD, x, y, text, DTA_ScaleX, scale, DTA_ScaleY, scale);
	}

	// The first key bound to +use, by the engine's own key names ("E",
	// "Space", "Mouse2"); the engine's "Use / Open" when none is bound.
	private ui String SD_UseKeyName()
	{
		int first, second;
		[first, second] = Bindings.GetKeysForCommand(SD_USE_COMMAND);
		if (first > 0)
		{
			return KeyBindings.NameKeys(first, 0);
		}
		return StringTable.Localize(SD_USE_FALLBACK_ID);
	}

	// The largest integer scale, at most the menus' CleanXFac, at which the
	// line fits SD_MAX_WIDTH of the screen; 0 when not even scale 1 fits.
	private ui int SD_FitScale(Font fnt, String text)
	{
		double room = Screen.GetWidth() * SD_MAX_WIDTH;
		int width = fnt.StringWidth(text);
		for (int scale = max(CleanXFac, 1); scale >= 1; scale--)
		{
			if (width * scale <= room)
			{
				return scale;
			}
		}
		return 0;
	}
}
