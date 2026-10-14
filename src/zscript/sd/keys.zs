// Soviet keys: the metro's blue pass (MAP03, docs/levels/MAP03-metro.md 5).
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
// status bar icon STKEYS0, the size, +NOTDMATCH and the Spawn states.
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
// Inherited: BlueCard's BKEY, drawn by Freedoom, a placeholder until
// art-director delivers the pass. When it lands, a Spawn state naming the new
// sprite goes here; nothing else changes.

class SD_BluePass : BlueCard replaces BlueCard
{
	Default
	{
		// Lock 2 matches by exact class or by Species, never by parentage
		// (see above). This line is what opens MAP03's blast door.
		Species "BlueCard";
		Inventory.PickupMessage "$SD_PICKUP_BLUEPASS";
	}
}
