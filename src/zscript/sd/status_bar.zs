// SD_StatusBar - Doom's status bar, with a pause sign per language (T24)
// and status bar A's labels per language (M2e-i, D89).
//
// Contract: docs/engine/MOD-SPEC.md 6.5.1; reasons:
// docs/engine/adr/010-pause-sign-per-language.md (and its M2e-i addendum).
//
// A STATUS BAR CLASS is the ZScript object GZDoom asks to draw the bar, the
// fullscreen HUD and a few overlays; MAPINFO's GameInfo names it
// (StatusBarClass). Doom's is DoomStatusBar (gzdoom.pk3:
// mapinfo/doomcommon.txt). This class IS that one: it adds no field and
// overrides two virtuals, DrawPaused and Draw; Draw first lets Doom draw
// everything, so the bar's layout, numbers, face and keys are Doom's.
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
//
// THE LABELS (M2e-i). Status bar A ships in English under the engine's names
// STBAR and STARMS, which DoomStatusBar.DrawMainBar draws by name. The
// Russian pictures (SDSBRU, SDARRU) differ from them only in the stencilled
// labels, rows 23-28 of the 32-row bar (tests/test_hud_install.py measures
// it). Localized textures are not drawn in g4.14.2 (ADR 010), and
// DrawMainBar is not virtual, so it cannot be overridden. Instead Draw lets
// Doom draw the whole bar, then, when a LANGUAGE id names another picture,
// draws that picture again clipped to the label band only: the bar's rows
// 21-31, where Doom draws no number, and the columns that avoid the face,
// the keys and the ammo table. Nothing of DrawMainBar is copied but the two
// pictures' positions, (0, 168) and (104, 168), and its condition for
// drawing STARMS, `deathmatch || teamplay` (it shows the frags there); the
// clip-and-restore is the engine's own DrawBar idiom (statusbar.zs).

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

	// LANGUAGE ids naming the pictures the labels are drawn from: the
	// engine's own names in [enu default] (already drawn: nothing to do),
	// status bar A's Russian pictures in [ru].
	const SD_SBAR_IMAGE_ID = "$SD_SBAR_IMAGE";
	const SD_SBAR_ARMS_IMAGE_ID = "$SD_SBAR_ARMS_IMAGE";
	const SD_SBAR_ENGINE_IMAGE = "STBAR";
	const SD_SBAR_ENGINE_ARMS = "STARMS";

	// Where DoomStatusBar.DrawMainBar draws them on the 320x200 bar screen
	// (gzdoom.pk3:zscript/ui/statusbar/doom_sbar.zs, g4.14.2).
	const SD_SBAR_X = 0;
	const SD_SBAR_Y = 168;
	const SD_SBAR_ARMS_X = 104;
	const SD_SBAR_ARMS_END = 142;       // STARMS is 38 wide

	// The label band: rows 21-31 of the bar. The big numbers end at y 186,
	// the arms digits at 187.
	const SD_LABEL_TOP = 189;
	const SD_LABEL_HEIGHT = 11;
	// Its columns: left of the face (x 0-142) and between the face and the
	// keys (179-236). The face (143-178), the key icons (from 239) and the
	// ammo table (from 250) are never redrawn.
	const SD_LABEL_LEFT_END = 143;
	const SD_LABEL_RIGHT_X = 179;
	const SD_LABEL_RIGHT_END = 237;

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

	override void Draw(int state, double TicFrac)
	{
		Super.Draw(state, TicFrac);

		// Only the bar has labels; an open inventory bar covers them.
		if (state != HUD_StatusBar || isInventoryBarVisible())
		{
			return;
		}

		String bar = StringTable.Localize(SD_SBAR_IMAGE_ID);
		if (bar != SD_SBAR_ENGINE_IMAGE)
		{
			SD_DrawLabelBand(bar, SD_SBAR_X, SD_SBAR_X, SD_LABEL_LEFT_END);
			SD_DrawLabelBand(bar, SD_SBAR_X, SD_LABEL_RIGHT_X, SD_LABEL_RIGHT_END);
		}

		// DrawMainBar's own condition: STARMS is drawn outside deathmatch
		// and teamplay only.
		String arms = StringTable.Localize(SD_SBAR_ARMS_IMAGE_ID);
		if (arms != SD_SBAR_ENGINE_ARMS && !(deathmatch || teamplay))
		{
			SD_DrawLabelBand(arms, SD_SBAR_ARMS_X, SD_SBAR_ARMS_X, SD_SBAR_ARMS_END);
		}
	}

	// Draws `image` at (imageX, SD_SBAR_Y), as DrawMainBar places it, clipped
	// to the label band between x = left and x = right; the clip rectangle in
	// force before is restored.
	private void SD_DrawLabelBand(String image, double imageX, double left, double right)
	{
		int cx, cy, cw, ch;
		[cx, cy, cw, ch] = Screen.GetClipRect();
		SetClipRect(left, SD_LABEL_TOP, right - left, SD_LABEL_HEIGHT);
		DrawImage(image, (imageX, SD_SBAR_Y), DI_ITEM_OFFSETS);
		Screen.SetClipRect(cx, cy, cw, ch);
	}
}
