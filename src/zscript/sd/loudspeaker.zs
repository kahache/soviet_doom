// SD_Loudspeaker - the propaganda radio's loudspeaker (V3 B5, D124).
// Contract: MOD-SPEC 6.14; design: docs/sound/2026-10-23_V3_propaganda-radio.md
// section 5.
//
// A loudspeaker in a room that the sergeant hears as he comes near: Radio
// Moscow's announcers read war reports, slogans and civil-defence notices,
// a POSITIONAL sound OVER the level's music (unlike SD_Radio, 21200, which
// swaps the music). When the player first comes within its reach it plays a
// station jingle, then one line at a time from its playlist, shuffled (every
// line once before any repeats, never the same line twice in a row), with a
// pause between lines. Farther than reach + SD_LS_HYSTERESIS no new line
// starts; the one in progress finishes (a sentence cut mid-word sounds like
// a bug). The jingle plays again only after SD_LS_JINGLE_COOLDOWN seconds
// away, so walking in and out does not ring it each time.
//
// Editor number 21201 (MAPINFO DoomEdNums, the decoration sub-range).
// Map arguments (UDMF thing args):
//   arg0  the playlist, a bit mask of the sixteen lines: bit n-1 = line n
//         (sd/radio/line/nn, lump SDRADnn); 0 = all sixteen.
//   arg1  the reach in map units, measured in 3D; 0 = SD_LS_DEFAULT_REACH.
//   arg2  the pause between lines in seconds; 0 = SD_LS_DEFAULT_PAUSE. A
//         random 0..SD_LS_PAUSE_JITTER seconds is added each time.
//   arg3  flags: SD_LS_FLAG_NO_JINGLE (1), SD_LS_FLAG_BED (4: the valve
//         set's hum and crackle in a loop while it is on). Bit 2 is kept
//         for a visible horn on a wall (the design's "hidden body").
//   arg4  the jingle: 1-3 one of the three; 0 = a random one each time.
//
// Body: none to see yet. The horn (SDLS A) is art-director's, not drawn,
// so the loudspeaker is invisible and intangible (TNT1, +NOINTERACTION):
// a voice from the room's public-address system. PROVISIONAL-D116 until
// the sprite exists (MOD-SPEC 6.12). Not shootable: it is ours.
//
// Single-player: the listener is the local player, as SD_Radio's.
// NOT VERIFIED in the engine (D26): the class compiling, the shuffle, the
// turn-off, the rolloff, the bed's loop after a load.

class SD_Loudspeaker : Actor
{
	// The sixteen approved lines, SDRAD01-SDRAD16 (D124).
	const SD_LS_LINES = 16;
	// Reach and hysteresis, map units, 3D. 384 covers a big hall from its
	// middle; the extra 128 is one wide doorway, so standing on the edge
	// does not start and stop lines.
	const SD_LS_DEFAULT_REACH = 384;
	const SD_LS_HYSTERESIS = 128;
	// Seconds of silence between two lines, plus a random 0..jitter: a
	// broadcast with air in it, not a loop.
	const SD_LS_DEFAULT_PAUSE = 6;
	const SD_LS_PAUSE_JITTER = 4;
	// Seconds between the jingle's end and the first line.
	const SD_LS_JINGLE_GAP = 1;
	// Seconds away before the jingle plays again on the way back in.
	const SD_LS_JINGLE_COOLDOWN = 60;
	// How often the distance is measured, in tics (35 a second).
	const SD_LS_POLL_TICS = 8;
	// Under 1 so the enemies' sight and attack sounds stay on top; never
	// ATTN_NONE (it is a loudspeaker in a room, not the boss's call). The
	// distance falloff is SNDINFO's $rolloff for every sd/radio sound.
	const SD_LS_VOLUME = 0.7;
	const SD_LS_BED_VOLUME = 0.3;
	// arg3 bits.
	const SD_LS_FLAG_NO_JINGLE = 1;
	const SD_LS_FLAG_HIDDEN = 2;      // reserved: every loudspeaker is hidden until SDLS is drawn
	const SD_LS_FLAG_BED = 4;
	// arg4: the three station jingles (D124).
	const SD_LS_JINGLES = 3;

	// Saved with the actor.
	bool turnedOn;                // the player is inside reach (with the hysteresis)
	bool everOn;            // it has turned on at least once on this map
	bool speaking;          // it started a jingle or a line that may still be playing
	bool afterJingle;       // what is (or was last) playing is the jingle
	bool bedOn;             // the bed loop was started and not stopped
	int offSince;           // Level.maptime when it last turned off
	int nextLineAt;         // Level.maptime before which no line starts
	int startedAt;          // Level.maptime the jingle or the line started
	int lastLine;           // 1..16, the line played last; 0 = none yet
	Array<int> bag;         // the lines of this round not played yet
	// Not saved: false on the map's first tic and on the first tic after a
	// load, which is when a playing loudspeaker restarts its bed loop.
	transient bool synced;

	Default
	{
		+NOINTERACTION       // PROVISIONAL-D116: no body until SDLS is drawn
		+NOBLOCKMAP
		+NOGRAVITY
		+DONTSPLASH
	}

	States
	{
	Spawn:
		TNT1 A -1;           // PROVISIONAL-D116: SDLS A, the horn, when drawn
		Stop;
	}

	double SpeakerReach()
	{
		return args[1] > 0 ? double(args[1]) : double(SD_LS_DEFAULT_REACH);
	}

	int PlaylistMask()
	{
		int all = (1 << SD_LS_LINES) - 1;
		int mask = args[0] & all;
		return mask != 0 ? mask : all;
	}

	int PauseTics()
	{
		int pause = args[2] > 0 ? args[2] : SD_LS_DEFAULT_PAUSE;
		return (pause + random(0, SD_LS_PAUSE_JITTER)) * TICRATE;
	}

	bool UsesBed()
	{
		return (args[3] & SD_LS_FLAG_BED) != 0;
	}

	static Sound LineSound(int num)
	{
		return Sound(String.Format("sd/radio/line/%02d", num));
	}

	Sound JingleSound()
	{
		int pick = args[4];
		if (pick < 1 || pick > SD_LS_JINGLES)
		{
			return "sd/radio/jingle";      // the $random of the three
		}
		return Sound(String.Format("sd/radio/jingle/%d", pick));
	}

	// A new round of the shuffle bag: every line of the playlist once, in a
	// random order, and never the line just played first.
	void RefillBag()
	{
		bag.Clear();
		int mask = PlaylistMask();
		for (int num = 1; num <= SD_LS_LINES; num++)
		{
			if ((mask & (1 << (num - 1))) != 0)
			{
				bag.Push(num);
			}
		}
		for (int i = bag.Size() - 1; i > 0; i--)
		{
			int j = random(0, i);
			int swap = bag[i];
			bag[i] = bag[j];
			bag[j] = swap;
		}
		// The bag is drawn from its end: keep the last line off that end.
		if (bag.Size() > 1 && bag[bag.Size() - 1] == lastLine)
		{
			int swap = bag[0];
			bag[0] = bag[bag.Size() - 1];
			bag[bag.Size() - 1] = swap;
		}
	}

	int NextLine()
	{
		if (bag.Size() == 0)
		{
			RefillBag();
		}
		int num = bag[bag.Size() - 1];
		bag.Pop();
		lastLine = num;
		return num;
	}

	void StartBed()
	{
		A_StartSound("sd/radio/bed", CHAN_BODY, CHANF_LOOPING, SD_LS_BED_VOLUME, ATTN_NORM);
		bedOn = true;
	}

	void TurnOn()
	{
		turnedOn = true;
		bool jingle = (args[3] & SD_LS_FLAG_NO_JINGLE) == 0
			&& (!everOn || Level.maptime - offSince >= SD_LS_JINGLE_COOLDOWN * TICRATE);
		everOn = true;
		if (UsesBed())
		{
			StartBed();
		}
		if (jingle && !IsActorPlayingSound(CHAN_VOICE))
		{
			A_StartSound(JingleSound(), CHAN_VOICE, CHANF_DEFAULT, SD_LS_VOLUME, ATTN_NORM);
			speaking = true;
			afterJingle = true;
			startedAt = Level.maptime;
		}
		else
		{
			nextLineAt = max(nextLineAt, Level.maptime + SD_LS_JINGLE_GAP * TICRATE);
		}
	}

	override void Tick()
	{
		Super.Tick();
		if (bDestroyed)
		{
			return;
		}
		if (!synced)
		{
			synced = true;
			// After a load: start the bed again (a second start on the same
			// channel replaces the first, harmless if the engine restored it).
			if (bedOn)
			{
				StartBed();
			}
		}
		if (Level.maptime % SD_LS_POLL_TICS != 0)
		{
			return;
		}

		let listener = players[consoleplayer].mo;
		if (listener == null)
		{
			return;
		}

		double distance = Distance3D(listener);
		double reach = SpeakerReach();
		if (!turnedOn && distance <= reach)
		{
			TurnOn();
		}
		else if (turnedOn && distance > reach + SD_LS_HYSTERESIS)
		{
			turnedOn = false;
			offSince = Level.maptime;
		}

		// A sound started on this very poll is not judged until the next one.
		bool talking = IsActorPlayingSound(CHAN_VOICE);
		if (speaking && !talking && Level.maptime > startedAt)
		{
			speaking = false;
			nextLineAt = Level.maptime + (afterJingle ? SD_LS_JINGLE_GAP * TICRATE : PauseTics());
			afterJingle = false;
		}

		if (turnedOn)
		{
			if (!speaking && Level.maptime >= nextLineAt)
			{
				A_StartSound(LineSound(NextLine()), CHAN_VOICE, CHANF_DEFAULT, SD_LS_VOLUME, ATTN_NORM);
				speaking = true;
				startedAt = Level.maptime;
			}
		}
		else if (!speaking && bedOn)
		{
			// The line in progress has finished: the set goes quiet.
			A_StopSound(CHAN_BODY);
			bedOn = false;
		}
	}
}
