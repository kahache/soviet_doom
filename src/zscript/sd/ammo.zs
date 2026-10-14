// Soviet ammunition pickups.
//
// WHY THESE CLASSES EXIST
// -----------------------
// The mod does NOT invent new ammo pools: the four Doom pools (Clip, Shell,
// RocketAmmo, Cell) are exactly the four the Soviet arsenal needs, and every
// weapon in zscript/weapons/ already declares one of them as its AmmoType.
// What the CEO asked for (2026-10-13) is that the player stop reading
// "bullets" and "shells" and start reading 1977 Soviet nomenclature.
//
// The pickup LINE could not be changed through the engine's own string ids
// (GOTCLIP, GOTSHELLS, ...): Freedoom overrides those from its DEHACKED
// lump, and a DEHACKED [STRINGS] replacement beats a LANGUAGE lump loaded
// afterwards (verified in-engine on GZDoom 4.14.2 + Freedoom 0.13.0,
// 2026-10-13). So each pickup gets a thin subclass of its Doom counterpart
// that carries an SD_GOT_* id Freedoom knows nothing about.
// Rationale and alternatives: docs/engine/adr/003-ammo-naming-and-the-silent-shovel.md.
//
// WHY THE POOLS ARE STILL DOOM'S
// ------------------------------
// GZDoom resolves which pool an ammo item feeds with Ammo.GetParentAmmo(),
// which walks up the inheritance chain until the parent class is `Ammo`.
// SD_ClipBox -> ClipBox -> Clip -> Ammo, so the item still fills the Clip
// pool, still respects its MaxAmount, and the weapons need no edit. The
// pool's own name comes from its Tag ("$AMMO_CLIP"), overridden in LANGUAGE.
//
// `replaces X` makes the engine hand out our class wherever the game would
// have spawned X - map things, monster drops and the Backpack alike - so no
// map has to know these classes exist.
//
// Sprites (D63, 2026-10-14): the eight ammunition pickups wear our own
// sprites, SDCL/SDCB/SDSL/SDSB/SDRA/SDRB/SDFU/SDFB (MOD-SPEC 6.3), drawn by
// tools/art/gen_pickups.py and installed from assets/sprites/pickups/. Each
// class overrides ONLY its Spawn state, and that state is its Doom parent's
// line for line (`XXXX A -1; Stop;`, gzdoom.pk3 g4.14.2 ->
// zscript/actors/doom/doomammo.zs) with the four-letter name changed: no tic
// moves (tests/test_pickup_sprites.py). No Scale, no offsets in code: the
// offsets are the grAb chunk inside each PNG. The status bar icons
// (Inventory.Icon CLIPA0, SHELA0, ROCKA0, CELLA0) are inherited and still
// Freedoom's. The backpack (BPAK) was not part of the sweep and keeps
// Freedoom's sprite.

// --- 7,62x25: TT-33 and PPSh-41 (Clip pool) --------------------------------

class SD_Clip : Clip replaces Clip
{
	Default { Inventory.PickupMessage "$SD_GOT_CLIP"; }
	States
	{
	Spawn:
		SDCL A -1;
		Stop;
	}
}

class SD_ClipBox : ClipBox replaces ClipBox
{
	Default { Inventory.PickupMessage "$SD_GOT_CLIPBOX"; }
	States
	{
	Spawn:
		SDCB A -1;
		Stop;
	}
}

// --- 12 gauge: IZh-58 (Shell pool) -----------------------------------------

class SD_Shell : Shell replaces Shell
{
	Default { Inventory.PickupMessage "$SD_GOT_SHELLS"; }
	States
	{
	Spawn:
		SDSL A -1;
		Stop;
	}
}

class SD_ShellBox : ShellBox replaces ShellBox
{
	Default { Inventory.PickupMessage "$SD_GOT_SHELLBOX"; }
	States
	{
	Spawn:
		SDSB A -1;
		Stop;
	}
}

// --- PG-7V rounds: RPG-7 (RocketAmmo pool) ---------------------------------

class SD_RocketAmmo : RocketAmmo replaces RocketAmmo
{
	Default { Inventory.PickupMessage "$SD_GOT_ROCKET"; }
	States
	{
	Spawn:
		SDRA A -1;
		Stop;
	}
}

class SD_RocketBox : RocketBox replaces RocketBox
{
	Default { Inventory.PickupMessage "$SD_GOT_ROCKBOX"; }
	States
	{
	Spawn:
		SDRB A -1;
		Stop;
	}
}

// --- Fuel: ROKS-3 and the hand Katyusha (Cell pool) ------------------------
// Both slot 6 and slot 7 draw on this pool (see BALANCE.md); the name is the
// flamethrower's, because that is what the canister looks like in the world.

class SD_Cell : Cell replaces Cell
{
	Default { Inventory.PickupMessage "$SD_GOT_CELL"; }
	States
	{
	Spawn:
		SDFU A -1;
		Stop;
	}
}

class SD_CellPack : CellPack replaces CellPack
{
	Default { Inventory.PickupMessage "$SD_GOT_CELLPACK"; }
	States
	{
	Spawn:
		SDFB A -1;
		Stop;
	}
}

// --- Quartermaster's satchel (Backpack) ------------------------------------

class SD_Backpack : Backpack replaces Backpack
{
	Default { Inventory.PickupMessage "$SD_GOT_BACKPACK"; }
}
