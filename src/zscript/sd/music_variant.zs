// SD_MusicVariant - episode 2's music: an A or a B piece per map, picked at
// random, and the boss loop on MAP06 (D106, 2026-10-22).
//
// Contract: docs/engine/MOD-SPEC.md 4.5 (what plays where) and 6.11 (this
// handler). Registered in MAPINFO -> GameInfo -> AddEventHandlers. An
// EventHandler (not a StaticEventHandler) lives in the level: the engine
// creates one per map and writes its fields into a savegame with the level
// (gzdoom g4.14.2 src/p_saveg.cpp 1024-1027), so the variant a map drew and
// whether its boss music started survive a save and a load.
//
// WHY. The CEO approved two pieces per map of episode 2 (D106, "10/10 OK")
// and the PM chose to play both: each new visit to MAP04, MAP05 or MAP06
// draws A or B. MAPINFO names the A (`music`), so with this handler off - or
// before it runs - the map plays A, as any other map plays its piece.
//
// HOW.
//   * WorldLoaded (a fresh map, not a load): draw the variant from the play
//     RNG `SD_MusicVariant` (seeded per game, network-safe) and, on a B, swap
//     the music with S_ChangeMusic. The engine has already started the A by
//     then: P_SetupLevel calls Level.SetMusic() (src/p_setup.cpp 446-451)
//     before WorldLoaded fires (src/g_level.cpp 1520-1522).
//   * A savegame: nothing to do. The engine saves the song that was PLAYING
//     (S_GetMusic) and starts it again on load, falling back to the level's
//     own `music` only if that fails (FLevelLocals::SerializeSounds,
//     src/p_saveg.cpp 572-593); this handler's fields come back with it.
//     A load therefore keeps B, or the boss loop, from the start of the song.
//   * The boss (MAP06 only, the only row with boss lumps): any monster with
//     the BOSS flag on that map - today SD_General standing in, later the
//     episode's own boss, with no change here - starts the boss loop of the
//     drawn variant the first time it has a player as its target (it saw or
//     heard him: A_Look
//     sets `target`) or a player hurts it. It does not stop: the loop plays
//     to the end of the map. MAP03 has no row, so its General changes
//     nothing; the General's class is not touched.
//   * The guard: SD_Radio (radio.zs) gives back Level.Music when the player
//     walks away, which is always the A. Once a second, if the A is playing
//     but this map wants B or the boss loop, the handler puts that back. The
//     same guard repairs a load whose saved song could not be restarted.
//
// TO SWITCH OFF: SD_MUSIC_VARIANTS_ENABLED = 0 (always A) and/or
// SD_BOSS_MUSIC_ENABLED = 0 (no boss loop). Rows: MusicCell's table.

class SD_MusicVariant : EventHandler
{
	// 1 = each map of the table draws A or B; 0 = always MAPINFO's A.
	const SD_MUSIC_VARIANTS_ENABLED = 1;
	// 1 = a map with boss lumps swaps to them when its boss engages.
	const SD_BOSS_MUSIC_ENABLED = 1;

	const SD_VARIANT_A = 0;
	const SD_VARIANT_B = 1;

	// The table: SD_MUSIC_ROWS rows of SD_MUSIC_COLS cells (MusicCell).
	const SD_MUSIC_ROWS = 3;
	const SD_MUSIC_COLS = 5;
	const SD_COL_MAP    = 0;
	const SD_COL_A      = 1;   // must equal the map's `music` in MAPINFO
	const SD_COL_B      = 2;
	const SD_COL_BOSS_A = 3;   // "" = no boss music on this map
	const SD_COL_BOSS_B = 4;

	// How often the bosses' targets are looked at: 4 tics, ~0.1 s.
	const SD_BOSS_POLL_TICS = 4;
	// How often the guard checks the radio's hand-back: once a second.
	const SD_MUSIC_GUARD_TICS = 35;

	// Saved with the level (see HOW).
	int variant;
	bool bossStarted;
	Array<Actor> bosses;

	// The music table, map -> (A, B, boss with A, boss with B). Lumps are
	// assets/music/<LUMP>.mid; tests/test_music_variant.py checks every cell
	// against MAPINFO and the package.
	static String MusicCell(int row, int col)
	{
		static const String SD_MUSIC_TABLE[] =
		{
			// map    A (MAPINFO)  B            boss with A  boss with B
			"MAP04",  "D_SDM04A",  "D_SDM04B",  "",          "",
			"MAP05",  "D_SDM05A",  "D_SDM05B",  "",          "",
			"MAP06",  "D_SDM06A",  "D_SDM06B",  "D_SDBS6A",  "D_SDBS6B"
		};
		return SD_MUSIC_TABLE[row * SD_MUSIC_COLS + col];
	}

	// This map's row of the table, or -1.
	int MapRow()
	{
		for (int row = 0; row < SD_MUSIC_ROWS; row++)
		{
			if (Level.MapName ~== MusicCell(row, SD_COL_MAP))
			{
				return row;
			}
		}
		return -1;
	}

	bool HasBossMusic(int row)
	{
		return SD_BOSS_MUSIC_ENABLED && row >= 0 && MusicCell(row, SD_COL_BOSS_A) != "";
	}

	// What this map should be playing now.
	String WantedMusic(int row)
	{
		bool b = variant == SD_VARIANT_B;
		if (bossStarted && HasBossMusic(row))
		{
			return MusicCell(row, b ? SD_COL_BOSS_B : SD_COL_BOSS_A);
		}
		return MusicCell(row, b ? SD_COL_B : SD_COL_A);
	}

	static bool IsBoss(Actor mo)
	{
		return mo != null && mo.bBOSS && mo.bISMONSTER && mo.health > 0;
	}

	void TrackBoss(Actor mo)
	{
		if (IsBoss(mo) && bosses.Find(mo) == bosses.Size())
		{
			bosses.Push(mo);
		}
	}

	void StartBossMusic(int row)
	{
		bossStarted = true;
		S_ChangeMusic(WantedMusic(row));
	}

	override void WorldLoaded(WorldEvent e)
	{
		// A load brings back the song and these fields (see HOW).
		if (e.IsSaveGame || e.IsReopen)
		{
			return;
		}
		int row = MapRow();
		if (row < 0)
		{
			return;
		}
		variant = SD_VARIANT_A;
		if (SD_MUSIC_VARIANTS_ENABLED && random[SD_MusicVariant](0, 1) == 1)
		{
			variant = SD_VARIANT_B;
		}
		bossStarted = false;
		if (variant == SD_VARIANT_B)
		{
			S_ChangeMusic(MusicCell(row, SD_COL_B));
		}
		if (HasBossMusic(row))
		{
			// The map's own things were spawned before this event.
			let it = ThinkerIterator.Create("Actor");
			Actor mo;
			while (mo = Actor(it.Next()))
			{
				TrackBoss(mo);
			}
		}
	}

	override void WorldThingSpawned(WorldEvent e)
	{
		// A boss spawned later (a script, a summon). The flags first: this
		// runs for every projectile and puff.
		if (!bossStarted && IsBoss(e.thing) && HasBossMusic(MapRow()))
		{
			TrackBoss(e.thing);
		}
	}

	override void WorldThingDamaged(WorldEvent e)
	{
		if (!bossStarted && IsBoss(e.thing) && e.DamageSource != null && e.DamageSource.player != null)
		{
			int row = MapRow();
			if (HasBossMusic(row))
			{
				StartBossMusic(row);
			}
		}
	}

	override void WorldTick()
	{
		if (!bossStarted && bosses.Size() > 0 && Level.maptime % SD_BOSS_POLL_TICS == 0)
		{
			for (int i = 0; i < bosses.Size(); i++)
			{
				let mo = bosses[i];
				if (IsBoss(mo) && mo.target != null && mo.target.player != null)
				{
					int bossRow = MapRow();
					if (HasBossMusic(bossRow))
					{
						StartBossMusic(bossRow);
					}
					break;
				}
			}
		}

		if (Level.maptime % SD_MUSIC_GUARD_TICS == 0)
		{
			int guardRow = MapRow();
			if (guardRow >= 0)
			{
				String wanted = WantedMusic(guardRow);
				String a = MusicCell(guardRow, SD_COL_A);
				if (!(wanted ~== a) && musplaying.name ~== a)
				{
					S_ChangeMusic(wanted);
				}
			}
		}
	}
}
