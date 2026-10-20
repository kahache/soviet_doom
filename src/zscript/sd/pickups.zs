// Soviet campaign pickups: health, armour and the area map (D80, backlog
// M2a-i).
//
// WHAT THIS IS
// ------------
// The campaign places 113 of Doom's own pickups on skill 3 (audit
// docs/qa/2026-10-14_2357_M2-freedoom-audit.md, B5): stimpacks, medikits,
// both bonuses, both armours and the computer area map. Each class below
// `replaces` its Doom counterpart, so the engine spawns ours wherever a map
// places the Doom editor number (2011, 2012, 2014, 2015, 2018, 2019, 2026)
// and no map has to know these classes exist: the pattern of ammo.zs.
//
// WHAT CHANGES
// ------------
// The picture and the pickup line, nothing else. Each class declares a
// Spawn label that is its Doom parent's line for line (gzdoom.pk3 g4.14.2,
// zscript/actors/doom/doomhealth.zs, doomarmor.zs, doomartifacts.zs) with
// only the four-letter sprite name changed, so every tic, Bright flag and
// loop is Doom's (tests/test_pickups_install.py). Amounts, save percents,
// sizes and flags are inherited.
//
// The pickup lines are SD_GOT_* ids: Freedoom overrides the engine's own
// GOTSTIM, GOTMEDIKIT, ... from its DEHACKED lump, and a DEHACKED string
// beats a LANGUAGE lump (ADR 003), so the engine's ids cannot carry ours.
//
// SPRITES
// -------
// Drawn by tools/art/gen_items.py, the CEO's choice per object (D80):
// SDBN (a field dressing packet), SDMD (an enamelled first-aid box), SDHB
// (a bottle of zelyonka), SDAB (an SSh-68 helmet), SDAG (a flak vest and a
// helmet), SDAH (a bare-steel SN-42 breastplate and helmet), SDMP (an
// officer's map case). Installed from assets/sprites/pickups/, the offsets
// in each PNG's grAb chunk; MOD-SPEC 6.3, "The campaign pickups, installed
// by D80". The two medical items wear the first-aid sign, a white cross on
// a green field, not the protected red-cross emblem (D80).
//
// HUD
// ---
// The armours' and the armour bonus' Inventory.Icon is our frame A: the
// fullscreen HUD draws the icon of the armour last picked up (BasicArmor
// takes the pickup's Icon; doom_sbar.zs DrawFullScreenStuff). The health
// icon of that HUD is the literal "MEDIA0", still Freedoom's medikit: our
// sprite names carry the SD prefix (MOD-SPEC 1), so replacing it means
// either an IWAD-named sprite or an SD_StatusBar override of
// DrawFullScreenStuff (MOD-SPEC 6.3, D80). NOT VERIFIED in the engine.

// --- Health -----------------------------------------------------------------

class SD_Stimpack : Stimpack replaces Stimpack
{
	Default { Inventory.PickupMessage "$SD_GOT_STIMPACK"; }
	States
	{
	Spawn:
		SDBN A -1;
		Stop;
	}
}

class SD_Medikit : Medikit replaces Medikit
{
	// Medikit's own Health.LowMessage threshold (gzdoom.pk3 g4.14.2,
	// doomhealth.zs: `Health.LowMessage 25, "$GOTMEDINEED"`).
	const SD_MEDIKIT_LOW_HEALTH = 25;

	// Medikit's Health.LowMessage (below 25 health) is GOTMEDINEED, which
	// Freedoom's DEHACKED overrides in English ("Took a large health refill.
	// Never give up!", read in freedoom2.wad 0.13.0), so a Russian player
	// would read English there. The low line is therefore our own pickup line,
	// at Medikit's own threshold.
	Default
	{
		Inventory.PickupMessage "$SD_GOT_MEDIKIT";
		Health.LowMessage SD_MEDIKIT_LOW_HEALTH, "$SD_GOT_MEDIKIT";
	}
	States
	{
	Spawn:
		SDMD A -1;
		Stop;
	}
}

class SD_HealthBonus : HealthBonus replaces HealthBonus
{
	Default { Inventory.PickupMessage "$SD_GOT_HEALTHBONUS"; }
	States
	{
	Spawn:
		SDHB ABCDCB 6;
		Loop;
	}
}

// --- Armour -----------------------------------------------------------------

class SD_ArmorBonus : ArmorBonus replaces ArmorBonus
{
	Default
	{
		Inventory.PickupMessage "$SD_GOT_ARMORBONUS";
		Inventory.Icon "SDABA0";
	}
	States
	{
	Spawn:
		SDAB ABCDCB 6;
		Loop;
	}
}

class SD_GreenArmor : GreenArmor replaces GreenArmor
{
	Default
	{
		Inventory.PickupMessage "$SD_GOT_ARMOR";
		Inventory.Icon "SDAGA0";
	}
	States
	{
	Spawn:
		SDAG A 6;
		SDAG B 7 Bright;
		Loop;
	}
}

class SD_BlueArmor : BlueArmor replaces BlueArmor
{
	Default
	{
		Inventory.PickupMessage "$SD_GOT_MEGAARMOR";
		Inventory.Icon "SDAHA0";
	}
	States
	{
	Spawn:
		SDAH A 6;
		SDAH B 6 Bright;
		Loop;
	}
}

// --- The area map -------------------------------------------------------------

class SD_Allmap : Allmap replaces Allmap
{
	Default { Inventory.PickupMessage "$SD_GOT_MAP"; }
	States
	{
	Spawn:
		SDMP ABCDCB 6 Bright;
		Loop;
	}
}
