// SD_Radio - the diegetic radio (D43). Contract: MOD-SPEC 6.7; reasons:
// docs/engine/adr/008-diegetic-radio.md.
//
// A radio on a desk that the sergeant hears too. While the local player is
// within its reach it plays one of two CC0 pieces IN PLACE OF the level's
// music; when the player walks away it gives the level's music back. It is
// a music swap, not a positional sound: the pieces are MIDI, and GZDoom
// plays MIDI only as music (ADR 008, option A).
//
// Editor number 21200 (MAPINFO DoomEdNums, the decoration sub-range).
// Map arguments:
//   arg0  the piece: 1 = D_SDRAD1 "Ej, ukhnem", 2 = D_SDRAD2 "Kolokolchik";
//         0 or anything else = 1.
//   arg1  the reach in map units, measured in 3D; 0 = the default.
//
// The sprite is a Freedoom (IWAD) PLACEHOLDER: PMAP A, the computer area
// map's picture, held still. Final art: SDRD A0 (MOD-SPEC 6.3).

class SD_Radio : Actor
{
	// Turns on within this many map units of the player (arg1 = 0). From a
	// radio in the middle of a 128x128 room it reaches about 60 units past
	// the walls: the doorway counts, the corridor outside mostly does not.
	const SD_RADIO_DEFAULT_REACH = 128;
	// Turns off only this much farther out than it turned on: one grid cell,
	// so a player standing or strafing on the edge does not make the music
	// flicker between two songs (ADR 008, D-008-2).
	const SD_RADIO_HYSTERESIS = 64;

	// arg0 values. Anything else falls back to the first piece.
	const SD_RADIO_PIECE_EJ_UKHNEM   = 1;
	const SD_RADIO_PIECE_KOLOKOLCHIK = 2;

	// Body: the placeholder picture is 32x28, a set on a desk.
	const SD_RADIO_RADIUS = 16;
	const SD_RADIO_HEIGHT = 28;

	// True while this radio has the music. Saved with the actor.
	bool playing;
	// Not saved: false on the map's first tic and again on the first tic
	// after a load, which is when a playing radio re-asserts its piece.
	transient bool synced;

	Default
	{
		Radius SD_RADIO_RADIUS;
		Height SD_RADIO_HEIGHT;
		+SOLID
	}

	States
	{
	Spawn:
		PMAP A -1;     // final art: SDRD A
		Stop;
	}

	// The music lump for arg0.
	static String PieceLump(int piece)
	{
		if (piece == SD_RADIO_PIECE_KOLOKOLCHIK)
		{
			return "D_SDRAD2";
		}
		return "D_SDRAD1";
	}

	double RadioReach()
	{
		return args[1] > 0 ? double(args[1]) : double(SD_RADIO_DEFAULT_REACH);
	}

	override void Tick()
	{
		Super.Tick();
		if (bDestroyed)
		{
			return;
		}

		String piece = PieceLump(args[0]);
		if (!synced)
		{
			synced = true;
			// Without `force`, S_ChangeMusic does nothing when this song is
			// already playing, so this is harmless if the engine restored it.
			if (playing)
			{
				S_ChangeMusic(piece);
			}
		}

		// The listener is the local player (single-player mod, MOD-SPEC 6.7).
		let listener = players[consoleplayer].mo;
		if (listener == null)
		{
			return;
		}

		double distance = Distance3D(listener);
		double reach = RadioReach();
		if (!playing && distance <= reach)
		{
			playing = true;
			S_ChangeMusic(piece);
		}
		else if (playing && distance > reach + SD_RADIO_HYSTERESIS)
		{
			playing = false;
			// Hand back only what we took: if something else changed the
			// music meanwhile, leave it alone (ADR 008, D-008-4).
			if (musplaying.name ~== piece)
			{
				S_ChangeMusic(Level.Music, Level.musicorder);
			}
		}
	}
}
