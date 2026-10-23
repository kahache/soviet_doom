// The end-of-episode awards, play side (V3 B3, ADR 013): the record of each
// campaign map the player finishes, and the rules that turn an episode's
// record into medals. The awards PAGE is drawn by SD_StatusScreen
// (zscript/sd/status_screen.zs). Contract: docs/engine/MOD-SPEC.md 6.13;
// the thresholds and why: docs/engine/BALANCE.md 9.
//
// WHERE THE RECORD LIVES. The stats screen only knows the map just finished
// (WBStartStruct), but a medal is earned over a whole episode of three maps.
// The record is therefore kept in the player's inventory, in an item the
// player never sees, SD_CampaignLedger:
//   * it travels with the player from map to map (a non-hub map change keeps
//     every item whose InterHubAmount is >= 1: PlayerPawn.PlayerFinishLevel,
//     gzdoom.pk3:zscript/actors/player/player.zs);
//   * it is saved with the player, so loading a save or the entry autosave
//     after a death restores the record as it was then;
//   * New Game starts a new player, so a new episode starts a new record.
// The play-side SD_AwardsRecorder (registered in MAPINFO AddEventHandlers)
// copies the level's counters into the ledger every tic; the last write
// before the exit is the map's result. The stats screen (UI) only READS it.
//
// A death that restarts a map from scratch (no autosave, MOD-SPEC 6.10) is a
// new game in the engine (G_InitNew) and starts a new record: the maps
// before it count as not played, which only matters for the Gold Star
// (it needs the whole episode, SD_MAPS_PER_EPISODE).

// The ledger: one slot per campaign map, indexed by the map's level number
// (MAP01 = 1 ... MAP09 = 9; the practice range, RANGE, has none).
class SD_CampaignLedger : Inventory
{
	const SD_FIRST_SLOT = 1;
	const SD_LAST_SLOT = 9;
	const SD_SLOTS = 10;          // index 0 unused, so slot == levelnum

	bool played[SD_SLOTS];
	int kills[SD_SLOTS];
	int maxKills[SD_SLOTS];
	int secrets[SD_SLOTS];
	int maxSecrets[SD_SLOTS];
	int timeTics[SD_SLOTS];
	int parSecs[SD_SLOTS];
	int spawnFilter[SD_SLOTS];    // the skill's SpawnFilter bit (MAPINFO skills)

	Default
	{
		Inventory.MaxAmount 1;
		Inventory.InterHubAmount 1;   // kept across map changes (see above)
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
		+INVENTORY.UNCLEARABLE
		-INVENTORY.INVBAR
	}

	void Record(int slot, int k, int maxK, int s, int maxS, int tics, int par, int filter)
	{
		if (slot < SD_FIRST_SLOT || slot > SD_LAST_SLOT)
		{
			return;
		}
		played[slot] = true;
		kills[slot] = k;
		maxKills[slot] = maxK;
		secrets[slot] = s;
		maxSecrets[slot] = maxS;
		timeTics[slot] = tics;
		parSecs[slot] = par;
		spawnFilter[slot] = filter;
	}
}

// Copies the level's counters into every player's ledger, every tic.
class SD_AwardsRecorder : EventHandler
{
	override void WorldTick()
	{
		int slot = Level.levelnum;
		if (slot < SD_CampaignLedger.SD_FIRST_SLOT || slot > SD_CampaignLedger.SD_LAST_SLOT)
		{
			return;
		}
		int filter = G_SkillPropertyInt(SKILLP_SpawnFilter);
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || players[i].mo == null)
			{
				continue;
			}
			let mo = players[i].mo;
			let ledger = SD_CampaignLedger(mo.FindInventory("SD_CampaignLedger"));
			if (ledger == null)
			{
				ledger = SD_CampaignLedger(mo.GiveInventoryType("SD_CampaignLedger"));
				if (ledger == null)
				{
					continue;
				}
			}
			ledger.Record(slot, Level.killed_monsters, Level.total_monsters,
				Level.found_secrets, Level.total_secrets, Level.time, Level.partime, filter);
		}
	}
}

// One episode's figures, summed over the maps of it the player played.
class SD_EpisodeRecord
{
	int episode;                  // 1, 2 or 3
	int mapsPlayed;
	int kills, maxKills;
	int secrets, maxSecrets;
	int timeTics, parSecs;
	int minSpawnFilter;           // the easiest skill any of its maps was played on
}

// The rules. Every threshold is here and in docs/engine/BALANCE.md 9; the
// tests read both (tests/test_awards.py).
class SD_Awards abstract
{
	// The five awards, in the order the page lists them (and the lumps,
	// graphics/SDAW*.png, tools/art/gen_medals.py).
	enum EAward
	{
		SD_AWARD_COURAGE,         // Medal "For Courage": the episode completed
		SD_AWARD_REDSTAR,         // Order of the Red Star: kills
		SD_AWARD_REDBANNER,       // Order of the Red Banner: secrets
		SD_AWARD_PATRIOTIC,       // Order of the Patriotic War: time
		SD_AWARD_HERO,            // Gold Star of the Hero of the Soviet Union: all of it
		SD_AWARD_COUNT
	}

	const SD_MAPS_PER_EPISODE = 3;        // MAP01-03, MAP04-06, MAP07-09 (MOD-SPEC 4.6)
	const SD_EPISODES = 3;
	const SD_REDSTAR_KILLS_PCT = 75;      // of the episode's enemies, the three maps summed
	const SD_REDBANNER_SECRETS_PCT = 100; // every secret of the episode
	const SD_HERO_KILLS_PCT = 90;
	// Skill 3, "Not one step back", is SpawnFilter Normal (MAPINFO skill
	// sd_notonestep): the bits are Baby 1, Easy 2, Normal 4, Hard 8,
	// Nightmare 16, so "skill 3 or harder" is a filter of 4 or more.
	const SD_HERO_MIN_SPAWNFILTER = 4;
	const SD_TICRATE = 35;

	static clearscope bool IsEpisodeEnd(int levelnum)
	{
		return levelnum >= SD_MAPS_PER_EPISODE && levelnum <= SD_MAPS_PER_EPISODE * SD_EPISODES
			&& levelnum % SD_MAPS_PER_EPISODE == 0;
	}

	static clearscope int EpisodeOf(int levelnum)
	{
		return (levelnum - 1) / SD_MAPS_PER_EPISODE + 1;
	}

	// The lump, the name and the rule of each award, by its EAward value.
	static clearscope String LumpOf(int award)
	{
		switch (award)
		{
		case SD_AWARD_COURAGE:   return "SDAWCOU";
		case SD_AWARD_REDSTAR:   return "SDAWRST";
		case SD_AWARD_REDBANNER: return "SDAWRBN";
		case SD_AWARD_PATRIOTIC: return "SDAWPTW";
		}
		return "SDAWHER";
	}

	static clearscope String NameOf(int award)
	{
		switch (award)
		{
		case SD_AWARD_COURAGE:   return "$SD_MEDAL_COURAGE_NAME";
		case SD_AWARD_REDSTAR:   return "$SD_MEDAL_REDSTAR_NAME";
		case SD_AWARD_REDBANNER: return "$SD_MEDAL_REDBANNER_NAME";
		case SD_AWARD_PATRIOTIC: return "$SD_MEDAL_PATRIOTIC_NAME";
		}
		return "$SD_MEDAL_HERO_NAME";
	}

	static clearscope String RuleOf(int award)
	{
		switch (award)
		{
		case SD_AWARD_COURAGE:   return "$SD_MEDAL_COURAGE_RULE";
		case SD_AWARD_REDSTAR:   return "$SD_MEDAL_REDSTAR_RULE";
		case SD_AWARD_REDBANNER: return "$SD_MEDAL_REDBANNER_RULE";
		case SD_AWARD_PATRIOTIC: return "$SD_MEDAL_PATRIOTIC_RULE";
		}
		return "$SD_MEDAL_HERO_RULE";
	}

	// The New Game screen's name of each episode (MAPINFO episode blocks).
	static clearscope String EpisodeNameOf(int episode)
	{
		switch (episode)
		{
		case 1: return "$SD_EP01_NAME";
		case 2: return "$SD_EP03_NAME";
		}
		return "$SD_EP04_NAME";
	}

	// Kills and secrets as the stats screen counts them: p * 100 / b,
	// 100 when the episode has none.
	static clearscope int Percent(int part, int whole)
	{
		return whole <= 0 ? 100 : part * 100 / whole;
	}

	static clearscope int TimeSecs(SD_EpisodeRecord r)
	{
		return r.timeTics / SD_TICRATE;
	}

	static clearscope bool BeatPar(SD_EpisodeRecord r)
	{
		return r.parSecs > 0 && TimeSecs(r) <= r.parSecs;
	}

	static clearscope bool Earned(int award, SD_EpisodeRecord r)
	{
		int killPct = Percent(r.kills, r.maxKills);
		int secretPct = Percent(r.secrets, r.maxSecrets);
		switch (award)
		{
		case SD_AWARD_COURAGE:
			return r.mapsPlayed > 0;
		case SD_AWARD_REDSTAR:
			return killPct >= SD_REDSTAR_KILLS_PCT;
		case SD_AWARD_REDBANNER:
			return secretPct >= SD_REDBANNER_SECRETS_PCT;
		case SD_AWARD_PATRIOTIC:
			return BeatPar(r);
		case SD_AWARD_HERO:
			return r.mapsPlayed >= SD_MAPS_PER_EPISODE && killPct >= SD_HERO_KILLS_PCT
				&& secretPct >= SD_REDBANNER_SECRETS_PCT && BeatPar(r)
				&& r.minSpawnFilter >= SD_HERO_MIN_SPAWNFILTER;
		}
		return false;
	}
}
