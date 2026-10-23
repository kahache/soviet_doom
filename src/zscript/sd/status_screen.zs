// SD_StatusScreen - the stats screen between maps, with the awards page at
// the end of an episode (V3 B1 and B3, ADR 013). Named by MAPINFO GameInfo
// `statscreen_single` (gzdoom.pk3's mapinfo/doomcommon.txt names Doom's
// DoomStatusScreen there; ours derives from it and changes one thing).
// Contract: docs/engine/MOD-SPEC.md 6.13.
//
// THE STATS PAGE IS DOOM'S. Kills, items, secrets, time and par are counted
// and drawn by DoomStatusScreen exactly as before
// (gzdoom.pk3:zscript/ui/statscreen/statscreen_sp.zs). The operations map
// behind them (B1) is not drawn here at all: it is the intermission SCRIPT
// SDOPSCR that every campaign map names as its exitpic/enterpic, which the
// engine's own InterBackground draws (tools/art/gen_ops_map.py).
//
// THE AWARDS PAGE (B3). After the stats of a map that ENDS an episode
// (MAP03, MAP06, MAP09: their `next` is an end sequence, so wbs.next is ""),
// DoomStatusScreen would finish at once (StatusScreen.initShowNextLoc:
// "Last map in episode - there is no next location!"). Instead this class
// stays in the ShowNextLoc state and draws the episode's five awards over
// the dimmed map: each row is revealed in turn (SD_REVEAL_TICS apart, a
// stamp for every award earned); a key shows them all at once, the next
// key leaves. Then the engine goes on as before: the cluster's ending text,
// then the title screen (MOD-SPEC 4.6). Every other map keeps Doom's
// "Entering" page on the operations map.
//
// The figures: the first maps of the episode from the player's
// SD_CampaignLedger (zscript/sd/awards.zs, written play-side by
// SD_AwardsRecorder), the last map from this screen's own wbs (exact). The
// rules are SD_Awards.Earned; the thresholds docs/engine/BALANCE.md 9.
//
// FONTS. BigFont for the title, SmallFont for the rest: the mod's own
// (fonts/bigfont, fonts/defsmallfont; D24), with every glyph the three
// languages need (tests/test_awards.py). NewSmallFont under ui_generic, as
// the engine's own screens do. A rule that does not fit one line is broken
// into two (Font.BreakLines), the row has room for both.

class SD_StatusScreen : DoomStatusScreen
{
	// --- layout, in the stats screen's 320x200 space (DTA_Clean) -----------
	const SD_TITLE_Y = 3;
	const SD_EPISODE_Y = 21;
	const SD_SUMMARY_LABEL_Y = 32;
	const SD_SUMMARY_VALUE_Y = 41;
	const SD_SUMMARY_COLUMNS = 4;         // kills, secrets, time, par
	const SD_SUMMARY_COLUMN_W = 72;       // the four columns, centred on the screen
	const SD_ROWS_Y = 51;
	const SD_ROW_H = 29;
	const SD_ICON_X = 22;
	const SD_TEXT_X = 54;
	const SD_TEXT_RIGHT = 314;
	const SD_NAME_DY = 3;
	const SD_RULE_DY = 13;
	const SD_RULE_LINE_H = 9;             // SmallFont's FontHeight
	const SD_RULE_MAX_LINES = 2;
	const SD_SCREEN_W = 320;
	// Start value of the episode's easiest skill, above any SpawnFilter bit.
	const SD_NO_SKILL_YET = 0x7fffffff;
	// The map stays visible behind the awards, darkened by this much.
	const SD_DIM_AMOUNT = 0.72;
	// A not-earned award is drawn darkened by a black DTA_ColorOverlay of
	// this alpha (two thirds; black works in every renderer, the tag's note
	// in gzdoom.pk3:zscript/engine/base.zs).
	const SD_UNEARNED_ALPHA = 170;

	// --- timing ------------------------------------------------------------
	const SD_REVEAL_TICS = 18;            // one row every ~half second
	const SD_STAMP_SOUND = "intermission/nextstage";
	const SD_SKIP_SOUND = "intermission/paststats";

	bool sdAwardsPage;
	int sdAwardTics;
	int sdRevealed;
	SD_EpisodeRecord sdRecord;
	// One flag per award; SD_AWARD_SLOTS == SD_Awards.SD_AWARD_COUNT
	// (tests/test_awards.py), spelt as a literal for the array's size.
	const SD_AWARD_SLOTS = 5;
	bool sdEarned[SD_AWARD_SLOTS];

	protected override void initShowNextLoc()
	{
		if (wbs.next == "" && SD_Awards.IsEpisodeEnd(Level.levelnum))
		{
			SD_StartAwards();
			return;
		}
		Super.initShowNextLoc();
	}

	protected override void updateShowNextLoc()
	{
		if (!sdAwardsPage)
		{
			Super.updateShowNextLoc();
			return;
		}
		sdAwardTics++;
		if (sdRevealed < SD_Awards.SD_AWARD_COUNT && sdAwardTics >= (sdRevealed + 1) * SD_REVEAL_TICS)
		{
			if (sdEarned[sdRevealed])
			{
				PlaySound(SD_STAMP_SOUND);
			}
			sdRevealed++;
		}
		if (acceleratestage)
		{
			acceleratestage = 0;
			if (sdRevealed < SD_Awards.SD_AWARD_COUNT)
			{
				sdRevealed = SD_Awards.SD_AWARD_COUNT;
				PlaySound(SD_SKIP_SOUND);
			}
			else
			{
				End();
			}
		}
		else if (sdRevealed >= SD_Awards.SD_AWARD_COUNT && autoSkip())
		{
			End();
		}
	}

	protected override void drawShowNextLoc()
	{
		if (!sdAwardsPage)
		{
			Super.drawShowNextLoc();
			return;
		}
		SD_DrawAwards();
	}

	// ------------------------------------------------------------- the record
	private void SD_StartAwards()
	{
		CurState = ShowNextLoc;
		acceleratestage = 0;
		sdAwardsPage = true;
		sdAwardTics = 0;
		sdRevealed = 0;
		sdRecord = SD_Gather();
		for (int i = 0; i < SD_Awards.SD_AWARD_COUNT; i++)
		{
			sdEarned[i] = SD_Awards.Earned(i, sdRecord);
		}
	}

	// The episode that ends on this map: its first maps from the ledger the
	// player carries, this one from wbs (the figures the stats page showed).
	private SD_EpisodeRecord SD_Gather()
	{
		SD_CampaignLedger ledger = null;
		if (me >= 0 && me < MAXPLAYERS && players[me].mo != null)
		{
			ledger = SD_CampaignLedger(players[me].mo.FindInventory("SD_CampaignLedger"));
		}
		int last = Level.levelnum;
		let r = new("SD_EpisodeRecord");
		r.episode = SD_Awards.EpisodeOf(last);
		r.minSpawnFilter = SD_NO_SKILL_YET;
		for (int slot = last - SD_Awards.SD_MAPS_PER_EPISODE + 1; slot <= last; slot++)
		{
			bool known = ledger != null && ledger.played[slot];
			if (slot == last)
			{
				r.mapsPlayed++;
				r.kills += Plrs[me].skills;
				r.maxKills += wbs.maxkills;
				r.secrets += Plrs[me].ssecret;
				r.maxSecrets += wbs.maxsecret;
				r.timeTics += Plrs[me].stime;
				r.parSecs += Level.partime;
				r.minSpawnFilter = min(r.minSpawnFilter, known ? ledger.spawnFilter[slot] : 0);
			}
			else if (known)
			{
				r.mapsPlayed++;
				r.kills += ledger.kills[slot];
				r.maxKills += ledger.maxKills[slot];
				r.secrets += ledger.secrets[slot];
				r.maxSecrets += ledger.maxSecrets[slot];
				r.timeTics += ledger.timeTics[slot];
				r.parSecs += ledger.parSecs[slot];
				r.minSpawnFilter = min(r.minSpawnFilter, ledger.spawnFilter[slot]);
			}
		}
		return r;
	}

	// ------------------------------------------------------------- the page
	private void SD_DrawAwards()
	{
		// the operations map as on this map's stats page (the route to here)
		bg.drawBackground(StatCount, false, false);
		Screen.Dim(0, SD_DIM_AMOUNT, 0, 0, Screen.GetWidth(), Screen.GetHeight());

		Font big = generic_ui ? NewSmallFont : BigFont;
		Font small = generic_ui ? NewSmallFont : SmallFont;

		SD_Centred(big, Font.CR_GOLD, SD_SCREEN_W / 2, SD_TITLE_Y, StringTable.Localize("$SD_AWARDS_TITLE"));
		SD_Centred(small, Font.CR_CREAM, SD_SCREEN_W / 2, SD_EPISODE_Y,
			StringTable.Localize(SD_Awards.EpisodeNameOf(sdRecord.episode)));

		// the summary: four columns, label over value
		int x0 = SD_SCREEN_W / 2 - 2 * SD_SUMMARY_COLUMN_W + SD_SUMMARY_COLUMN_W / 2;
		for (int c = 0; c < SD_SUMMARY_COLUMNS; c++)
		{
			int cx = x0 + c * SD_SUMMARY_COLUMN_W;
			SD_Centred(small, Font.CR_GRAY, cx, SD_SUMMARY_LABEL_Y, StringTable.Localize(SD_SummaryLabel(c)));
			SD_Centred(small, Font.CR_WHITE, cx, SD_SUMMARY_VALUE_Y, SD_SummaryValue(c));
		}

		// the five awards, revealed in turn
		for (int i = 0; i < sdRevealed && i < SD_Awards.SD_AWARD_COUNT; i++)
		{
			int y = SD_ROWS_Y + i * SD_ROW_H;
			bool earned = sdEarned[i];
			TextureID tex = TexMan.CheckForTexture(SD_Awards.LumpOf(i), TexMan.Type_MiscPatch);
			if (tex.IsValid())
			{
				SD_Picture(tex, SD_ICON_X, y, earned);
			}
			DrawText(small, earned ? Font.CR_GOLD : Font.CR_DARKGRAY, SD_TEXT_X, y + SD_NAME_DY,
				StringTable.Localize(SD_Awards.NameOf(i)));
			BrokenLines rule = small.BreakLines(StringTable.Localize(SD_Awards.RuleOf(i)), SD_TEXT_RIGHT - SD_TEXT_X);
			for (int l = 0; l < rule.Count() && l < SD_RULE_MAX_LINES; l++)
			{
				DrawText(small, earned ? Font.CR_CREAM : Font.CR_GRAY, SD_TEXT_X,
					y + SD_RULE_DY + l * SD_RULE_LINE_H, rule.StringAt(l));
			}
		}
	}

	private String SD_SummaryLabel(int column)
	{
		switch (column)
		{
		case 0: return "$SD_AWARDS_KILLS";
		case 1: return "$SD_AWARDS_SECRETS";
		case 2: return "$SD_AWARDS_TIME";
		}
		return "$SD_AWARDS_PAR";
	}

	private String SD_SummaryValue(int column)
	{
		switch (column)
		{
		case 0: return String.Format("%d%%", SD_Awards.Percent(sdRecord.kills, sdRecord.maxKills));
		case 1: return String.Format("%d/%d", sdRecord.secrets, sdRecord.maxSecrets);
		case 2: return SD_Clock(SD_Awards.TimeSecs(sdRecord));
		}
		return SD_Clock(sdRecord.parSecs);
	}

	private void SD_Centred(Font fnt, int colour, int cx, int y, String text)
	{
		DrawText(fnt, colour, cx - fnt.StringWidth(text) / 2, y, text);
	}

	private void SD_Picture(TextureID tex, double x, double y, bool earned)
	{
		Color overlay = earned ? Color(0, 0, 0, 0) : Color(SD_UNEARNED_ALPHA, 0, 0, 0);
		if (scalemode == -1)
		{
			screen.DrawTexture(tex, true, x, y, DTA_Clean, true, DTA_ColorOverlay, overlay);
		}
		else
		{
			screen.DrawTexture(tex, true, x, y, DTA_FullscreenScale, scalemode,
				DTA_VirtualWidth, cwidth, DTA_VirtualHeight, cheight, DTA_ColorOverlay, overlay);
		}
	}

	// m:ss, or h:mm:ss past the hour (the stats page's own format).
	private String SD_Clock(int secs)
	{
		int h = secs / 3600;
		int m = (secs % 3600) / 60;
		int s = secs % 60;
		if (h > 0)
		{
			return String.Format("%d:%02d:%02d", h, m, s);
		}
		return String.Format("%d:%02d", m, s);
	}
}
