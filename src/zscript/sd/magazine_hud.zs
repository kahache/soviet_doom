// SD_MagazineHud - the V3 reloads' readout (D132; magazine.zs).
//
// With sd_reloads on, a magazine the player cannot see is a reload that
// comes as a surprise, and the experiment has no frames of its own to show
// it (D132: no new art). So this draws one short line, "rounds/capacity"
// (the IZh-58's barrels "1/2"), in the HUD's small font, for the weapon in
// hand: just above status bar A's AMMO number when the bar is on, at the
// bottom right over Doom's fullscreen HUD (screenblocks 11), nothing with
// the HUD off (12) or the automap open. Digits and a slash only: nothing to
// translate. Reloads off, it draws nothing.
//
// An EventHandler (registered in MAPINFO's AddEventHandlers) rather than
// a change to SD_StatusBar, whose two overrides are pinned (ADR 010): the
// readout is an experiment, and taking it out is one line of MAPINFO.
// RenderOverlay runs in ui scope and only reads play data.
//
// Positions are on the 320x200 screen the status bar is drawn on, kept in
// the 4:3 middle (DTA_KeepRatio) as the bar is. NOT VERIFIED in the engine
// (D26): that the line lands where these numbers say on a widescreen
// display, with hud_scale and with the fullscreen HUD.

class SD_MagazineHud : EventHandler
{
	const SD_MAG_SCREEN_W = 320;
	const SD_MAG_SCREEN_H = 200;
	// Status bar A's AMMO number ends at x = 44 (DoomStatusBar.DrawMainBar
	// draws it right-aligned there); the line sits 10 px above the bar's
	// top edge (y = 168).
	const SD_MAG_BAR_RIGHT = 44;
	const SD_MAG_BAR_TOP = 158;
	// Over the fullscreen HUD: DoomStatusBar.DrawFullScreenStuff draws the
	// ammo number right-aligned at (-30, -20) from the bottom right, so
	// x = 290, y = 180 on a 320x200 screen; the line ends at the same x,
	// 10 px above it.
	const SD_MAG_FULL_RIGHT = 290;
	const SD_MAG_FULL_TOP = 170;
	// screenblocks: 10 and under, the bar; 11, the fullscreen HUD; 12, none.
	const SD_MAG_FULLSCREEN_BLOCKS = 11;

	override void RenderOverlay(RenderEvent e)
	{
		if (gamestate != GS_LEVEL || automapactive || !SD_Reloads.On())
		{
			return;
		}
		if (!playeringame[consoleplayer])
		{
			return;
		}
		PlayerInfo p = players[consoleplayer];
		if (p.playerstate != PST_LIVE || p.ReadyWeapon == null || p.camera != p.mo)
		{
			return;
		}
		CVar blocksVar = CVar.FindCVar("screenblocks");
		int blocks = blocksVar != null ? blocksVar.GetInt() : 10;
		if (blocks > SD_MAG_FULLSCREEN_BLOCKS)
		{
			return;
		}

		int loaded, capacity;
		[loaded, capacity] = SD_Reloads.Magazine(p.ReadyWeapon);
		if (capacity <= 0)
		{
			return;
		}

		String text = String.Format("%d/%d", loaded, capacity);
		Font fnt = generic_ui ? NewSmallFont : SmallFont;
		bool full = blocks == SD_MAG_FULLSCREEN_BLOCKS;
		double right = full ? SD_MAG_FULL_RIGHT : SD_MAG_BAR_RIGHT;
		double top = full ? SD_MAG_FULL_TOP : SD_MAG_BAR_TOP;
		// Gold while rounds are left, red on an empty magazine.
		int colour = loaded > 0 ? Font.CR_GOLD : Font.CR_RED;
		Screen.DrawText(fnt, colour, right - fnt.StringWidth(text), top, text,
			DTA_VirtualWidth, SD_MAG_SCREEN_W, DTA_VirtualHeight, SD_MAG_SCREEN_H,
			DTA_KeepRatio, true);
	}
}
