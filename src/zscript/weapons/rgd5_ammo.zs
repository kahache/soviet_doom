// SD_Rgd5Ammo, SD_Rgd5Box - the RGD-5's grenades (V3, A4; ADR 012): the
// pool, one loose grenade (21021) and a crate of them (21022). The weapon
// is rgd5.zs, the thrown grenade rgd5_grenade.zs; design and balance in
// docs/engine/2026-10-23_V3_rgd5.md section 3.
//
// THE GRENADE IS ITS OWN AMMUNITION. SD_Rgd5Ammo derives from Ammo
// directly, so it is a pool of its own (GetParentAmmo() is itself), the
// mod's second after the AKM's (ADR 011): a thrown grenade shares no
// cartridge with any gun, and sharing a pool (RocketAmmo, say) would let
// the grenade eat the RPG-7's rounds. It is both the pool and the loose
// grenade's pickup, as Doom's Clip is; the crate derives from it, as
// ClipBox from Clip, and fills the same pool.
//
// A loose grenade is also the weapon. A sergeant who walks onto one RGD-5
// can throw it: when SD_Rgd5Ammo (or the crate) is taken by a player who
// does not own SD_Rgd5 yet, TryPickup hands him the weapon too, with no
// extra grenades (AmmoGive 0) and no switch to it (SD_Rgd5 carries
// NO_AUTO_SWITCH). The pickup line is the grenade's, not the weapon's:
// CallTryPickup prints nothing, the Touch of the grenade on the floor does.
// The pattern is the engine's own GiveInventory (spawn the item, then
// CallTryPickup, destroy it if refused); NOT VERIFIED in the engine (D26).
//
// The backpack gives no grenade (BackpackAmount 0) but doubles the room:
// Doom's backpack hands out every pool (BackpackItem.CreateCopy, gzdoom.pk3
// g4.14.2 ammo.zs), and a grenade the sergeant cannot throw, because only a
// grenade PICKUP gives the weapon, would read as a bug.
//
// PROVISIONAL LOOK (D116): the loose grenade shows the health bonus's olive
// flask SDHB A, the crate the PG-7V crate SDRB A, both tinted gunmetal by
// the one line marked PROVISIONAL-D116 (the crate inherits it), until
// Gemini's SDRJ A and SDRZ A are drawn. The HUD icon is SDHBA0 untinted (an
// icon takes no Translation). The swap when they land in assets/sprites/rgd5/:
//   sed -i -e 's/^\(\s*\)SDHB /\1SDRJ /' -e 's/^\(\s*\)SDRB /\1SDRZ /' -e '/^\s*[^/[:space:]].*PROVISIONAL-D116/d' src/zscript/weapons/rgd5_ammo.zs
// and SDHBA0 -> SDRJA0 in Inventory.Icon by hand (MOD-SPEC 6.12;
// tests/test_rgd5.py pins both halves).

class SD_Rgd5Ammo : Ammo
{
	const SD_RGD5_LOOSE        = 1;    // one grenade on the floor
	const SD_RGD5_MAX          = 6;    // three twin pouches: scarce on purpose, the maps' rule (BALANCE.md section 8)
	const SD_RGD5_BACKPACK     = 0;    // see the header: no grenade without the weapon
	const SD_RGD5_BACKPACK_MAX = 12;   // Doom's rule: the backpack doubles the maximum

	Default
	{
		Inventory.PickupMessage "$SD_GOT_RGD5";
		Inventory.PickupSound "sd/weapon/rgd5/pickup";
		Inventory.Amount SD_RGD5_LOOSE;
		Inventory.MaxAmount SD_RGD5_MAX;
		Ammo.BackpackAmount SD_RGD5_BACKPACK;
		Ammo.BackpackMaxAmount SD_RGD5_BACKPACK_MAX;
		Inventory.Icon "SDHBA0";
		Tag "$SD_AMMO_RGD5";
		Translation "0:255=%[0.03,0.04,0.05]:[0.80,0.88,0.95]";   // PROVISIONAL-D116: gunmetal, not the bonus's olive
	}

	States
	{
	Spawn:
		SDHB A -1;
		Stop;
	}

	// The grenade is the weapon too (header). The ammunition is taken first,
	// by the engine's own rules (refused when the pool is full); only then,
	// and only if the toucher has no RGD-5 yet, the weapon follows, empty.
	override bool TryPickup(in out Actor toucher)
	{
		if (!Super.TryPickup(toucher))
			return false;
		if (toucher != null && toucher.player != null && toucher.FindInventory("SD_Rgd5") == null)
		{
			let w = Weapon(Spawn("SD_Rgd5"));
			if (w != null)
			{
				w.AmmoGive1 = 0;   // the grenade just taken is the ammunition
				if (!w.CallTryPickup(toucher))
					w.Destroy();
			}
		}
		return true;
	}
}

class SD_Rgd5Box : SD_Rgd5Ammo
{
	const SD_RGD5_CRATE = 4;   // a crate is a reward, not a supply line (the RPG-7's crate gives 5 rounds)

	Default
	{
		Inventory.PickupMessage "$SD_GOT_RGD5BOX";
		Inventory.Amount SD_RGD5_CRATE;
	}

	States
	{
	Spawn:
		SDRB A -1;
		Stop;
	}
}
