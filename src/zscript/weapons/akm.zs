// SD_Akm - slot 4's second weapon (D112, V2 "more weapons"): the AKM, the
// Soviet Army's 1970s assault rifle, 7.62x39 mm, 30-round magazine.
// Design and balance: docs/engine/2026-10-22_P4_akm.md; the numbers in
// BALANCE.md (slot 4b). In the mod since D116 (2026-10-22), on provisional
// sprites; placed in no map yet (level-designer's, the AKM doc section 6).
//
// Slot 4 holds two weapons, as Doom II's slot 3 holds the shotgun and the
// super shotgun: SD_Player lists both (Player.WeaponSlot 4, "SD_Ppsh",
// "SD_Akm"), and the key 4 cycles between them. Nothing is replaced;
// SD_Akm is a new class with its own editor number, 21008.
//
// Its character against the PPSh-41: slower (4 tics a round, 525 rpm,
// against 3), harder (avg 12 a round against 8) and ACCURATE IN SHORT
// BURSTS: the first round of a burst is pinpoint (Doom's own rule for one
// bullet with no refire, kept by A_FireBullets), rounds 2-3 spread 2.0
// degrees, and from the 4th the muzzle climbs and the spread opens to 5.0
// (still under the PPSh's 7.0). Tap it and it is a rifle; hold it and it
// is a worse PPSh with better ammo. It eats its own pool, SD_AkmAmmo
// (7.62x39), not the PPSh's Clip (7.62x25): see ammo.zs, ADR 011 and the doc.
//
// ITS OWN LOOK since 2026-10-24 (D128, the CEO: "OK AKM";
// D116 had it on the PPSh-41's frames): assets/sprites/akm/, held SDAK A
// (ready) and B (the kick), flash SDAF A, world pickup SDAQ A. The held and
// flash frames come from the project lead's one Gemini image (the ready
// one) by tools/art/gemini_frames.py akm: B is A kicked like every weapon's
// B and the flash is the PPSh-41's grafted at the AKM's muzzle brake (the
// firing image was not asked again); the pickup is drawn on the weapon
// pickups' rig, tools/art/gen_akm_pickup.py. They replaced the PPSh-41's
// SDPP, SDPF and the tinted SDPQ letter for letter (MOD-SPEC 6.12): only the
// sprite names changed and the tint line went; every tic, action and jump
// stayed (tests/test_akm_sprites.py pins the states).
//
// V3 reloads (D132, the CVar sd_reloads; magazine.zs): the 30-round
// magazine. Off, every frame below runs exactly as before: the guards only
// jump when reloads are on.

class SD_Akm : DoomWeapon
{
	mixin SD_MagazineWeapon;   // the magazine counter and the reload (magazine.zs)

	// --- Balance constants (docs/engine/2026-10-22_P4_akm.md section 2) ----
	// Reference: the PPSh-41 is 4 x random(1,3) (avg 8) every 3 tics = 93.3
	// damage/s. The AKM trades rate for punch and accuracy: 6 x random(1,3)
	// (avg 12, the TT-33's round) every 4 tics = 105 damage/s, +12.5 %, for
	// 25 % fewer rounds a second out of a scarcer pool.
	const SD_AKM_DAMAGE       = 6;    // x random(1,3) -> 6..18, avg 12
	const SD_AKM_BULLETS      = 1;    // 1 = the first round of a burst is pinpoint
	const SD_AKM_SHORT_BURST  = 3;    // rounds 1-3 are the short burst
	const SD_AKM_SPREAD_SHORT = 2.0;  // degrees, rounds 2-3 (TT-33 4.5, PPSh 7.0)
	const SD_AKM_SPREAD_LONG  = 5.0;  // degrees, round 4 onwards
	const SD_AKM_CLIMB_LONG   = 1.5;  // degrees of vertical spread from round 4: the muzzle climbs
	const SD_AKM_AMMO_USE     = 1;
	const SD_AKM_AMMO_GIVE    = 30;   // the weapon comes with one full magazine

	// --- Reload (V3 experiment, docs/engine/2026-10-25_V3_reloads.md) -----
	const SD_AKM_MAGAZINE         = 30;  // the box magazine (= SD_AKM_AMMO_GIVE)
	const SD_AKM_RELOAD_TICS      = 70;  // 2.0 s: magazine rocked out, a fresh one in, the bolt racked
	const SD_AKM_RELOAD_DROP      = 14;  // tics down, and up again
	// sd/weapon/akm/reload reuses SDPPRLD (SNDINFO, until an AKM take):
	// its bolt at 30 tics lands as the gun comes back up (tic 56).
	const SD_AKM_RELOAD_SOUND_TIC = 26;

	Default
	{
		// Lower is preferred when the engine picks a weapon (an empty gun,
		// a pickup): the AKM before the PPSh-41 (700), so an empty AKM
		// falls back to the PPSh and not the other way round.
		Weapon.SelectionOrder 650;
		Weapon.AmmoUse SD_AKM_AMMO_USE;
		Weapon.AmmoGive SD_AKM_AMMO_GIVE;
		Weapon.AmmoType "SD_AkmAmmo";
		Weapon.SlotNumber 4;
		// Its own logical names (SNDINFO) over the PPSh-41's lumps, the shot
		// pitched down ($pitchset); final lumps in the doc section 4.
		AttackSound "sd/weapon/akm/fire";
		Obituary "$SD_OB_AKM";
		Tag "$SD_TAG_AKM";
		Inventory.PickupMessage "$SD_PICKUP_AKM";
		Inventory.PickupSound "sd/weapon/akm/pickup";
	}

	States
	{
	Ready:
		SDAK A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDAK A 1 A_Lower;
		Loop;
	Select:
		SDAK A 1 A_Raise;
		Loop;
	Fire:
		// 2 + 2 = 4 tics per round = 8.75 rounds/s = 525 rpm (the real AKM
		// ~600; 3 tics would be the PPSh's 700). B is the kick frame.
		// V3: an empty magazine reloads instead (0 tics; never with reloads off).
		SDAK A 0 A_JumpIf(invoker.SD_MagazineDry(SD_AKM_MAGAZINE), "Reload");
		SDAK B 0 A_GunFlash;
		SDAK B 2 A_SD_FireAkm;
		SDAK A 2;
		SDAK A 0 A_ReFire;
		Goto Ready;
	Reload:
		// V3 (magazine.zs): the gun goes down off screen and comes back up,
		// 70 tics, the magazine full again as it rises.
		SDAK A 0 A_JumpIf(!invoker.SD_CanReload(SD_AKM_MAGAZINE), "Ready");
		SDAK A 0 A_SD_BeginReload;
	ReloadLoop:
		SDAK A 1 A_SD_ReloadTick(SD_AKM_MAGAZINE, SD_AKM_RELOAD_TICS, SD_AKM_RELOAD_DROP, SD_AKM_RELOAD_SOUND_TIC, "sd/weapon/akm/reload");
		SDAK A 0 A_JumpIf(invoker.sdReloadTic < SD_AKM_RELOAD_TICS, "ReloadLoop");
		Goto Ready;
	Flash:
		SDAF A 2 Bright A_Light1;
		Goto LightDone;
	Spawn:
		SDAQ A -1;
		Stop;
	}

	// One round. player.refire counts the rounds already fired in this
	// burst (A_ReFire adds one each time the trigger is still held, and
	// zeroes it on release; gzdoom.pk3 g4.14.2 stateprovider.zs). With one
	// bullet and refire 0, A_FireBullets ignores the spread: round 1 is
	// pinpoint whatever we pass. A_FireBullets takes the round from the
	// pool and plays AttackSound on CHAN_WEAPON.
	action void A_SD_FireAkm()
	{
		if (player == null)
			return;
		int fired = player.refire;
		double spread = 0.0;
		double climb = 0.0;
		if (fired >= SD_AKM_SHORT_BURST)
		{
			spread = SD_AKM_SPREAD_LONG;
			climb = SD_AKM_CLIMB_LONG;
		}
		else if (fired > 0)
		{
			spread = SD_AKM_SPREAD_SHORT;
		}
		A_FireBullets(spread, climb, SD_AKM_BULLETS, SD_AKM_DAMAGE);
	}

	// Ready with the empty click (N9, D74), as every gun of the mod:
	// SD_WeaponSounds.DryClick (the mod's weapon_sounds.zs) on the tic the
	// trigger goes down with an empty pool, then A_WeaponReady.
	// V3 reloads, both no-ops with sd_reloads off: a spent magazine reloads at
	// once (unless a weapon switch is pending), and the +reload key is
	// allowed when a reload would load.
	action state A_SD_WeaponReady()
	{
		if (player != null && player.PendingWeapon == WP_NOCHANGE
			&& invoker.SD_MagazineDry(SD_AKM_MAGAZINE))
		{
			return ResolveState("Reload");
		}
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/akm/dry");
		A_WeaponReady(invoker.SD_ReadyFlags(SD_AKM_MAGAZINE));
		return null;
	}
}
