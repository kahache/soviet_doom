// SD_Player - the player class of the mod: Sergeant Ramon Vilanova (D10, D14).
//
// A "player class" is the actor the engine spawns at a Player Start. Unlike
// ordinary actors it cannot be installed with `replaces`; it is declared in
// MAPINFO -> gameinfo -> PlayerClasses (verified on the ZDoom wiki,
// "Creating new player classes"). Declaring our own is what keeps Freedoom's
// marine, its starting pistol and its weapon slots out of the mod.
//
// Note (ZDoom wiki, Actor properties): "The initial startitem list is never
// inherited and must be specified in full for each player class." So the
// whole loadout is restated here even though DoomPlayer already has one.

class SD_Player : DoomPlayer
{
	// The alarm wakes the sergeant with his sidearm and 50 rounds, nothing
	// else. The shovel is NOT a start item (CEO bug, 2026-10-13): MAP01
	// teaches it from the dorm's rack, and a player who already owned it
	// could not pick that one up, so the rack showed a pickup that refused
	// to be taken. Slot 1 stays empty until the shovel is picked up.
	// Everything else is found on the map.
	const SD_START_CLIP = 50;   // same as Doom's marine: 50 rounds of 7.62x25

	Default
	{
		Player.DisplayName "Sergeant Vilanova";

		// Which weapon is raised on spawn: PlayerPawn.GiveDefaultInventory
		// (gzdoom.pk3, zscript/actors/player/player.zs) readies every start
		// weapon that has ammo at the moment it is given, so the ammo must
		// already be there. Doom's own order (weapon first, ammo last) is
		// kept: DoomPlayer declares Pistol, Fist, Clip and spawns with the
		// pistol, which is only possible if the list is walked last-declared
		// first (the walk itself is C++, NOT VERIFIED beyond that).
		Player.StartItem "SD_Tokarev";
		Player.StartItem "Clip", SD_START_CLIP;

		// One weapon per slot - the arsenal ratified by the CEO (D13).
		Player.WeaponSlot 1, "SD_Shovel";
		Player.WeaponSlot 2, "SD_Tokarev";
		Player.WeaponSlot 3, "SD_Izh";
		Player.WeaponSlot 4, "SD_Ppsh";
		Player.WeaponSlot 5, "SD_Rpg7";
		Player.WeaponSlot 6, "SD_Roks3";
		Player.WeaponSlot 7, "SD_HandKatyusha";
	}
}
