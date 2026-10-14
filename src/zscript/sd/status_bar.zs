// SD_StatusBar - Doom's status bar, with a pause sign per language (T24).
//
// Contract: docs/engine/MOD-SPEC.md 6.5.1; reasons:
// docs/engine/adr/010-pause-sign-per-language.md.
//
// A STATUS BAR CLASS is the ZScript object GZDoom asks to draw the bar, the
// fullscreen HUD and a few overlays; MAPINFO's GameInfo names it
// (StatusBarClass). Doom's is DoomStatusBar (gzdoom.pk3:
// mapinfo/doomcommon.txt). This class IS that one: it adds no field and
// overrides one virtual, so the bar the player sees is unchanged.
//
// WHY. GZDoom g4.14.2 draws the pause sign in D_Display (src/d_main.cpp)
// from GameInfo's PauseSign with no localization, so the Russian plaque
// packed at localized/textures/M_PAUSE.ru.png (D48) is never drawn: the
// engine's substitution line is commented out (texturemanager.h). Before
// drawing, D_Display calls the status bar's DrawPaused(player) and skips
// its own drawing when it returns true (gzdoom.pk3:
// zscript/ui/statusbar/statusbar.zs: "let the HUD handle drawing the pause
// graphics"). So the mod draws the sign itself, picking the graphic by a
// LANGUAGE id, which follows the language the player chose ("auto"
// included).
//
// Everything below the lookup is D_Display's own drawing, transcribed:
// same position, same scaling, same multiplayer line. Debt T14: it does not
// track engine changes; re-diff it at every engine upgrade.

class SD_StatusBar : DoomStatusBar
{
	// LANGUAGE id naming the pause graphic: "M_PAUSE" in [enu default], the
	// Russian variant's full path in [ru] (a name with a '/' is resolved
	// through the file system by TexMan.CheckForTexture).
	const SD_PAUSE_SIGN_ID = "$SD_PAUSE_SIGN";

	// D_Display draws the sign at y = 4 screen pixels, unscaled by the clean
	// factor (DTA_CleanNoMove scales the picture, not its position).
	const SD_PAUSE_SIGN_TOP = 4;

	// ...and the "by <player>" line 4 pixels below the scaled sign.
	const SD_PAUSED_BY_GAP = 4;

	// Engine string "By %s" (gzdoom.pk3:language.csv, TXT_BY).
	const SD_PAUSED_BY_ID = "$TXT_BY";

	override bool DrawPaused(int player)
	{
		// The same lookup as GetGameTextureByName: MiscPatch, TryAny.
		TextureID pauseSign = TexMan.CheckForTexture(StringTable.Localize(SD_PAUSE_SIGN_ID),
			TexMan.Type_MiscPatch);
		if (!pauseSign.IsValid())
		{
			// Nothing to draw: let the engine draw GameInfo's PauseSign
			// (M_PAUSE), the English sign rather than none.
			return false;
		}

		Vector2 size = TexMan.GetScaledSize(pauseSign);
		Vector2 offset = TexMan.GetScaledOffset(pauseSign);
		double x = (Screen.GetWidth() - size.x * CleanXfac) / 2 + offset.x * CleanXfac;
		Screen.DrawTexture(pauseSign, true, x, SD_PAUSE_SIGN_TOP, DTA_CleanNoMove, true);

		// D_Display: `if (paused && multiplayer)`, and it passes paused - 1,
		// so paused != 0 is player >= 0.
		if (player >= 0 && multiplayer)
		{
			Font fnt = generic_ui ? NewSmallFont : SmallFont;
			String pausedBy = StringTable.Localize(SD_PAUSED_BY_ID);
			pausedBy.Substitute("%s", players[player].GetUserName());
			Screen.DrawText(fnt, Font.CR_RED,
				(Screen.GetWidth() - fnt.StringWidth(pausedBy, false) * CleanXfac) / 2,
				size.y * CleanYfac + SD_PAUSED_BY_GAP,
				pausedBy, DTA_CleanNoMove, true);
		}
		return true;
	}
}
