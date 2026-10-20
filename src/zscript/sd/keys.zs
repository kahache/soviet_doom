// Soviet keys: the three passes (propusk). The metro's blue pass (MAP02,
// docs/levels/MAP03-metro.md 5) since D63; Tankograd's yellow and red passes
// (MAP03, locks 3 and 1) since D80, the blue pass's family: the same card in
// another ground colour (tools/art/gen_items.py, option A of SDKY and SDKK).
// Everything said below of the blue pass holds for the other two with their
// own lock and Species: lock 3 lists YellowCard, lock 1 RedCard
// (gzdoom.pk3 g4.14.2 -> lockdefs.txt).
//
// WHAT IT IS
// ----------
// The station duty officer's pass (propusk) that opens the bunker's hermetic
// door. In the engine it is Doom's blue keycard: MAP03 places editor number 5
// and its blast door asks for lock 2 (`Door_LockedRaise (4, 16, 0, 2, 0)`).
// `replaces BlueCard` makes the engine spawn this class wherever a map places
// 5 (or anything spawns a BlueCard), so no map has to know it exists - the
// same pattern as the ammo pickups in ammo.zs.
//
// WHY `Species "BlueCard"` AND NOT JUST THE INHERITANCE
// -----------------------------------------------------
// Lock 2 is defined in gzdoom.pk3 -> lockdefs.txt as `Lock 2 Doom { BlueCard
// ... }`. The engine's test for "does the player hold that key" is
// OneKey::check (src/gamedata/a_keys.cpp, tag g4.14.2), and for each
// inventory item it accepts exactly two things:
//
//   item->IsA(key)                         - the EXACT class (DObject::IsA is
//                                            `type == GetClass()`, no parents)
//   item->GetSpecies() == key->TypeName    - the item's Species
//
// Inheritance is never consulted, so a plain `SD_BluePass : BlueCard` would
// leave the blast door shut. An inventory item's Species defaults to its own
// class name (AActor::GetSpecies, src/playsim/p_mobj.cpp), so this class
// declares Species "BlueCard" and lock 2 - and every lock that lists
// BlueCard, such as lock 130 "any blue key" - accepts it. The same check
// drives the status bar's key slot (DoomStatusBar.DrawBarKeys calls
// CheckKeys(2, ...)) and the automap's key colour (P_GetMapColorForKey), so
// both treat the pass as the blue key. VERIFIED as code; NOT VERIFIED in the
// engine (D26: the PM's engine pass, MOD-SPEC 6, "The blue pass").
//
// The class still DERIVES from BlueCard, for what inheritance does give: the
// status bar icon STKEYS0, the size and +NOTDMATCH. The Spawn state is its
// own since D63 (SPRITE, below).
//
// WHAT IT CHANGES ON SCREEN
// -------------------------
// Only the pickup line: SD_PICKUP_BLUEPASS ("Blue pass." in English, its Russian
// twin in [ru]).
// Freedoom overrides the engine's GOTBLUECARD from its DEHACKED lump, and a
// DEHACKED string beats a LANGUAGE lump (ADR 003), so the line needs an id
// Freedoom does not know. The locked-door message is LANGUAGE's, not this
// file's (PD_BLUECO, MOD-SPEC 6).
//
// SPRITE
// ------
// Ours since D63 (2026-10-14): SDKB, a laminated card (option B of
// tools/art/gen_pickups.py, palette v2's cobalt so it reads blue, D45),
// installed from assets/sprites/pickups/. Frame B is the blink. The Spawn
// state below is BlueCard's line for line (gzdoom.pk3 g4.14.2 ->
// zscript/actors/doom/doomkeys.zs: `BKEY A 10; BKEY B 10 bright; loop;`)
// with only the four-letter name changed, so the pass blinks exactly as
// Doom's keys do (tests/test_pickup_sprites.py). The status bar icon is
// still BlueCard's STKEYS0, which since D80 the mod ships as the pass's own
// 7x5 card (assets/graphics/hud/STKEYS0.png); NOT VERIFIED in the engine.

class SD_BluePass : BlueCard replaces BlueCard
{
	Default
	{
		// Lock 2 matches by exact class or by Species, never by parentage
		// (see above). This line is what opens MAP03's blast door.
		Species "BlueCard";
		Inventory.PickupMessage "$SD_PICKUP_BLUEPASS";
	}

	States
	{
	Spawn:
		SDKB A 10;
		SDKB B 10 Bright;
		Loop;
	}
}

// --- The yellow and red passes (Tankograd, MAP03; D80) ---------------------
// MAP03 places editor numbers 6 and 13 and asks for locks 3 and 1 at its two
// coloured doors (Door_LockedRaise, tags 4 and 5): a press works the door by
// tag, so the line the player reads is PD_YELLOWCO / PD_REDCO (LANGUAGE).
// Status bar icons: inherited (STKEYS1, STKEYS2), which the mod ships as
// the passes' own small cards (assets/graphics/hud/), as it does STKEYS0.

class SD_YellowPass : YellowCard replaces YellowCard
{
	Default
	{
		// Lock 3 matches by exact class or by Species, never by parentage.
		Species "YellowCard";
		Inventory.PickupMessage "$SD_PICKUP_YELLOWPASS";
	}

	States
	{
	Spawn:
		SDKY A 10;
		SDKY B 10 Bright;
		Loop;
	}
}

class SD_RedPass : RedCard replaces RedCard
{
	Default
	{
		// Lock 1 matches by exact class or by Species, never by parentage.
		Species "RedCard";
		Inventory.PickupMessage "$SD_PICKUP_REDPASS";
	}

	States
	{
	Spawn:
		SDKK A 10;
		SDKK B 10 Bright;
		Loop;
	}
}
