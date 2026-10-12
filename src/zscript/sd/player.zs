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
	// The sergeant walks out of the hangar with his sidearm, his entrenching
	// tool and two magazines. Everything else is found on the map.
	const SD_START_CLIP = 50;   // same as Doom's marine: 50 rounds of 7.62x25

	Default
	{
		Player.DisplayName "Sergeant Vilanova";

		// The FIRST StartItem weapon is the one selected on spawn.
		Player.StartItem "SD_Tokarev";
		Player.StartItem "SD_Shovel";
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
