// SD_HandKatyusha - slot 7, the "hand Katyusha": a secret 1977 prototype
// that straps a six-rail rocket battery to a shoulder frame.
//
// Replaces Doom's BFG9000 and, like it, costs 40 cells per shot. Where the
// BFG concentrates everything on one target, the Katyusha fans a salvo:
// weaker against a single boss, better against a crowd. That is the point
// of a Katyusha and it is what makes slot 7 feel Soviet rather than borrowed.
//
// Sprites, all ours since 2026-10-20. The held frames SDHK A-B and the
// flash SDHF A-B (D84), built from the CEO's Google Gemini pair by
// tools/art/gemini_frames.py, in assets/sprites/katyusha/; the floor pickup
// SDHP A (D80, the D51 draft), in assets/sprites/pickups/. Only the
// four-letter names changed, every tic, action and jump is as it was.
// MOD-SPEC 6.3; tests/test_gemini_weapons_install.py and
// tests/test_pickups_install.py.
// Balance rationale: docs/engine/BALANCE.md.

class SD_HandKatyusha : BFG9000 replaces BFG9000
{
	const SD_KATYUSHA_ROCKETS  = 6;     // one per rail
	const SD_KATYUSHA_SPREAD   = 12.5;  // degrees either side of the aim line
	const SD_KATYUSHA_AMMO_USE = 40;    // same as Doom's BFG
	const SD_KATYUSHA_AMMO_GIVE = 40;
	// A sound channel nothing else of the player's uses: the salvo is on
	// CHAN_WEAPON, pickups on CHAN_ITEM (N9).
	const SD_KATYUSHA_RELOAD_CHANNEL = CHAN_5;

	Default
	{
		Height 20;
		Weapon.SelectionOrder 2800;
		Weapon.AmmoUse SD_KATYUSHA_AMMO_USE;
		Weapon.AmmoGive SD_KATYUSHA_AMMO_GIVE;
		Weapon.AmmoType "Cell";
		Weapon.SlotNumber 7;
		+WEAPON.NOAUTOFIRE
		Obituary "$SD_OB_KATYUSHA";
		Tag "$SD_TAG_KATYUSHA";
		Inventory.PickupMessage "$SD_PICKUP_KATYUSHA";
		Inventory.PickupSound "sd/weapon/katyusha/pickup";   // SDHKPKP (N9, D74)
	}

	States
	{
	Ready:
		SDHK A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDHK A 1 A_Lower;
		Loop;
	Select:
		SDHK A 1 A_Raise;
		Loop;
	Fire:
		// 20 + 10 + 10 + 0 + 20 = 60 tics (Doom BFG: 60). The long wind-up is
		// the rails coming up to firing angle. The 0-tic frame (N9) starts the
		// rails' reload as the 20-tic recovery begins, on its own channel, so
		// the salvo (1.4 s, started on CHAN_WEAPON 10 tics earlier) is not
		// cut. No tic is added.
		SDHK A 20 A_StartSound("sd/weapon/katyusha/charge", CHAN_WEAPON);
		SDHK B 10 A_GunFlash;
		SDHK B 10 A_SD_FireKatyusha;
		SDHK B 0 A_StartSound("sd/weapon/katyusha/reload", SD_KATYUSHA_RELOAD_CHANNEL);
		SDHK B 20 A_ReFire;
		Goto Ready;
	Flash:
		SDHF A 11 Bright A_Light1;
		SDHF B 6 Bright A_Light2;
		Goto LightDone;
	Spawn:
		SDHP A -1;
		Stop;
	}

	// Fires the whole salvo for a single ammo charge: the first rocket pays
	// for all six, the rest are launched with useammo = false.
	action void A_SD_FireKatyusha()
	{
		if (player == null)
			return;

		Weapon w = player.ReadyWeapon;
		if (w != null && invoker == w && stateinfo != null && stateinfo.mStateType == STATE_Psprite)
		{
			if (!w.DepleteAmmo(w.bAltFire, true))
				return;
		}

		A_StartSound("sd/weapon/katyusha/fire", CHAN_WEAPON);

		for (int i = 0; i < SD_KATYUSHA_ROCKETS; i++)
		{
			// Evenly spaced across the fan, from -SPREAD to +SPREAD.
			double frac = double(i) / double(SD_KATYUSHA_ROCKETS - 1);
			double ang = -SD_KATYUSHA_SPREAD + 2.0 * SD_KATYUSHA_SPREAD * frac;
			A_FireProjectile("SD_KatyushaRocket", ang, false);
		}
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDHKDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	action void A_SD_WeaponReady()
	{
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/katyusha/dry");
		A_WeaponReady();
	}
}
