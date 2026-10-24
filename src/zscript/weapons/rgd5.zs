// SD_Rgd5 - slot 8, the RGD-5 hand grenade (V3, A4; D120; ADR 012): the
// Soviet Army's standard fragmentation grenade from 1954, a 310 g olive
// steel egg with a UZRGM fuse. Design and balance:
// docs/engine/2026-10-23_V3_rgd5.md; the numbers in BALANCE.md (slot 8).
// Placed in no map yet (level-designer's, the V3 doc section 6).
//
// Slot 8, a key of its own: GZDoom binds 8 to "slot 8" by default
// (gzdoom.pk3 g4.14.2 engine/commonbinds.txt), Doom's seven weapons never
// used it, and the throw round a corner wants one press, not a cycle
// through the hand Katyusha's slot 7 (ADR 012 has the options). SD_Player
// declares it (Player.WeaponSlot 8, "SD_Rgd5"); nothing is replaced.
//
// The grenade is its own ammunition: SD_Rgd5Ammo (rgd5_ammo.zs), a pool of
// its own; a loose grenade on the floor gives the weapon too. This class is
// the pouch of two on the floor (21009) and the hand that throws. One press,
// one throw (NOAUTOFIRE, no A_ReFire): a held trigger never empties the
// pouch. It is never raised by itself: not on pickup (NO_AUTO_SWITCH), not
// when ammo arrives (NOAUTOSWITCHTO), and after the ice axe when the guns
// run dry (SelectionOrder 4000 > the ice axe's 3700).
//
// The throw: the pin out and the arm back (8 tics), the arm forward (3),
// release (2; A_SD_ThrowRgd5), the follow-through (8) and the next grenade
// into the hand (12; A_CheckReload switches away when the last is gone):
// 33 tics, about one throw a second. The grenade leaves along the view,
// lofted SD_RGD5_LOFT degrees up, with no autoaim (an arc, not a homing
// shot): its own speed, gravity, bounce and 1.71 s fuse are rgd5_grenade.zs.
//
// ITS OWN LOOK since 2026-10-25 (D133, the CEO: "Ok granada";
// D116 had it on the ice axe's SDAX A-D and the health bonus's SDHB A,
// tinted): assets/sprites/rgd5/, held SDRG A ready, B the pin out (the left
// hand with the ring) and the arm back, C the release, D the follow-through
// (the hand empty), and the pouch of two SDRQ A on the floor. The held
// frames come from the project lead's three Gemini images (A, B, C) by
// tools/art/gemini_frames.py rgd5: B's third hand cut away, D derived from
// C without the grenade; the pouch is drawn on the weapon pickups' rig with
// Gemini's grenade in it, tools/art/gen_rgd5_pickups.py. They replaced the
// borrowed names letter for letter (MOD-SPEC 6.12): only the sprite names
// changed and the tint and scale lines went; every tic, action and jump
// stayed (tests/test_rgd5_sprites.py pins the states).

class SD_Rgd5 : DoomWeapon
{
	// --- Constants (docs/engine/2026-10-23_V3_rgd5.md section 2) -----------
	const SD_RGD5_AMMO_USE  = 1;       // one grenade a throw
	const SD_RGD5_AMMO_GIVE = 2;       // the pouch on the floor holds two
	// GZDoom's pitch is positive DOWNWARDS, so the loft is negative: a throw
	// aimed level leaves 10 degrees up and lands ~310 units away on the flat.
	const SD_RGD5_LOFT      = -10.0;
	// The steepest throw: view pitch plus loft never passes 80 degrees up,
	// so a throw straight at the ceiling never tips past the vertical and
	// flies backwards.
	const SD_RGD5_MAX_UP    = -80.0;

	Default
	{
		// Higher is less preferred when the engine picks a weapon: after the
		// ice axe (3700), so an empty gun never lands a grenade in the hand.
		Weapon.SelectionOrder 4000;
		Weapon.AmmoUse SD_RGD5_AMMO_USE;
		Weapon.AmmoGive SD_RGD5_AMMO_GIVE;
		Weapon.AmmoType "SD_Rgd5Ammo";
		Weapon.SlotNumber 8;
		+WEAPON.NOAUTOFIRE       // one press, one throw
		+WEAPON.NO_AUTO_SWITCH   // picking it up does not raise it
		+WEAPON.NOAUTOSWITCHTO   // nor does picking up a grenade with an empty gun in hand
		+WEAPON.EXPLOSIVE        // the engine's hint that it is a splash weapon
		Obituary "$SD_OB_RGD5";
		Tag "$SD_TAG_RGD5";
		Inventory.PickupMessage "$SD_PICKUP_RGD5";
		Inventory.PickupSound "sd/weapon/rgd5/pickup";
	}

	States
	{
	Ready:
		SDRG A 1 A_WeaponReady;
		Loop;
	Deselect:
		SDRG A 1 A_Lower;
		Loop;
	Select:
		SDRG A 1 A_Raise;
		Loop;
	Fire:
		// 8 + 3 + 2 + 8 + 12 = 33 tics a throw (the RPG-7: 26 a round).
		SDRG B 8 A_StartSound("sd/weapon/rgd5/pin", CHAN_WEAPON);
		SDRG C 3 A_StartSound("sd/weapon/rgd5/throw", CHAN_WEAPON);
		SDRG C 2 A_SD_ThrowRgd5;
		SDRG D 8;
		SDRG A 12 A_CheckReload;
		Goto Ready;
	Spawn:
		SDRQ A -1;
		Stop;
	}

	// The throw. A_FireProjectile takes the grenade from the pool and spawns
	// SD_Rgd5Grenade along the view with `pitch` added to the player's
	// (gzdoom.pk3 g4.14.2 stateprovider.zs: self.Pitch += pitch around
	// SpawnPlayerMissile), FPF_NOAUTOAIM so autoaim does not flatten the arc.
	// In a weapon action `self` is the player, so `pitch` is the view's.
	action void A_SD_ThrowRgd5()
	{
		double loft = max(SD_RGD5_LOFT, SD_RGD5_MAX_UP - pitch);
		A_FireProjectile("SD_Rgd5Grenade", 0, true, 0, 0, FPF_NOAUTOAIM, loft);
	}
}
