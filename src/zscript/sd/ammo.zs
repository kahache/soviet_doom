// Soviet ammunition pickups.
//
// WHY THESE CLASSES EXIST
// -----------------------
// The seven weapons of D13 use the four Doom pools (Clip, Shell,
// RocketAmmo, Cell), exactly the four they need. Since D116 there is ONE
// pool of our own, SD_AkmAmmo at the end of this file, for the AKM's
// 7.62x39 (ADR 011); every other weapon in zscript/weapons/ declares a Doom
// pool as its AmmoType.
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
// Freedoom's. The backpack was not part of that sweep; it wears our SDBP
// since D80 (an RD-54 paratrooper's pack, tools/art/gen_items.py option B),
// its Spawn the Backpack's line for line (`BPAK A -1; Stop;`,
// doomammo.zs) with the name changed.

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

// --- The paratrooper's pack (Backpack; RD-54 since D80) ---------------------

class SD_Backpack : Backpack replaces Backpack
{
	Default { Inventory.PickupMessage "$SD_GOT_BACKPACK"; }
	States
	{
	Spawn:
		SDBP A -1;
		Stop;
	}
}

// --- 7,62x39: AKM (its own pool, D116; ADR 011) ----------------------------
// SD_AkmAmmo - the AKM's 7.62x39 pool, and the 30-round magazine that fills
// it (docs/engine/2026-10-22_P4_akm.md section 3). The mod's only pool that
// is not one of Doom's four. Why its own rather than the PPSh-41's Clip:
// the TT-33 and the PPSh-41 share Clip because they fire the same 7.62x25
// Tokarev round (BALANCE.md section 4); the AKM fires another cartridge.
// And sharing would retire the PPSh: from one pool the AKM gives 12 damage
// a round to the PPSh's 8 and more DPS too. Apart, the PPSh is the abundant
// gun and the AKM the scarce, efficient one.
//
// Unlike every class above, this one derives from Ammo DIRECTLY, on
// purpose: that is what makes it a pool (GetParentAmmo() is itself). It is
// both the pool and its pickup, as Doom's Clip is; a crate would derive from
// it, as ClipBox from Clip, and feed the same pool. Placed by its own editor
// number, 21020 (MOD-SPEC 6.1), and dropped by the Legion gunner.
//
// PROVISIONAL LOOK (D116): the 7.62x25 magazine's sprite SDCL A, tinted
// plum-orange by the line marked PROVISIONAL-D116, until Gemini's SDAM A is
// drawn; the HUD icon is SDCL A untinted (an icon takes no Translation).
// The swap when SDAM lands in assets/sprites/pickups/: SDCL -> SDAM in the
// Spawn line and in Inventory.Icon, and delete the marked line (MOD-SPEC
// 6.12).

class SD_AkmAmmo : Ammo
{
	const SD_AKM_MAG          = 30;    // one AKM magazine
	const SD_AKM_MAX          = 150;   // five magazines: Clip carries 200 rounds of a pistol cartridge
	const SD_AKM_BACKPACK     = 30;    // Doom's rule: a backpack gives one small pickup of every pool
	const SD_AKM_BACKPACK_MAX = 300;   // Doom's rule: the backpack doubles the maximum

	Default
	{
		Inventory.PickupMessage "$SD_GOT_AKMMAG";
		Inventory.Amount SD_AKM_MAG;
		Inventory.MaxAmount SD_AKM_MAX;
		Ammo.BackpackAmount SD_AKM_BACKPACK;
		Ammo.BackpackMaxAmount SD_AKM_BACKPACK_MAX;
		Inventory.Icon "SDCLA0";
		Tag "$SD_AMMO_AKM";
		Translation "0:255=%[0.10,0.03,0.05]:[1.45,0.85,0.55]";   // PROVISIONAL-D116
	}

	States
	{
	Spawn:
		SDCL A -1;
		Stop;
	}
}
