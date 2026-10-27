// SD_Tokarev - slot 2, the TT-33 Tokarev service pistol (7.62x25 mm).
//
// Replaces Doom's Pistol and is the sergeant's starting sidearm. Keeps the
// Clip ammo type: the TT-33 and the PPSh-41 historically fire the same
// 7.62x25 Tokarev cartridge, so one ammo pool is also the accurate choice.
//
// Sprites, all ours (assets/sprites/tt33/). The world pickup SDTP A since
// D48 (2026-10-14). The held frames SDTT A-C and the muzzle flash SDTF A
// since N17 (2026-10-15), redone with Gemini in D111 (2026-10-23): the
// project lead's Gemini pair processed by tools/art/gemini_frames.py like
// the other six weapons (bare hand, the arsenal's scale), in place of the
// D61 set (our TT-33 in Freedoom's recoloured pistol hands). Both sets
// replaced their predecessors letter for letter: never a tic, an action or
// the flow. MOD-SPEC 6.3.
// Balance rationale: docs/engine/BALANCE.md.
//
// V3 reloads (D132, the CVar sd_reloads; magazine.zs): an 8-round
// magazine. Off, every frame below runs exactly as in v1.2: the two guards
// (the first Fire frame, the Ready function) only jump when reloads are on.

class SD_Tokarev : Pistol replaces Pistol
{
	mixin SD_MagazineWeapon;   // the magazine counter and the reload (magazine.zs)

	// --- Balance constants -------------------------------------------------
	// Reference: Doom's Pistol is 5 x random(1,3) (5..15, avg 10) every 19
	// tics while held. The TT-33 is a high-velocity single-action pistol:
	// a little more damage, a little tighter, a slightly shorter cycle.
	const SD_TT_DAMAGE    = 6;    // x random(1,3) -> 6..18, avg 12
	const SD_TT_SPREAD    = 4.5;  // degrees; Doom's hitscan spread is 5.625
	const SD_TT_BULLETS   = 1;    // 1 = the first shot of a burst is pinpoint
	const SD_TT_AMMO_USE  = 1;
	const SD_TT_AMMO_GIVE = 20;   // a dropped TT with two spare magazines

	// --- Reload (V3 experiment, docs/engine/2026-10-25_V3_reloads.md) -----
	const SD_TT_MAGAZINE          = 8;   // the TT-33's single-stack magazine
	const SD_TT_RELOAD_TICS       = 42;  // 1.2 s: magazine out, a fresh one in, slide released
	const SD_TT_RELOAD_DROP       = 10;  // tics to lower the gun off screen, and to raise it
	// SDTTRLD (0.86 s) slams the slide home at 0.70 s = 24.5 tics; started
	// on tic 8 the slam lands as the gun comes back up (tic 32).
	const SD_TT_RELOAD_SOUND_TIC  = 8;

	Default
	{
		Weapon.SelectionOrder 1900;
		Weapon.AmmoUse SD_TT_AMMO_USE;
		Weapon.AmmoGive SD_TT_AMMO_GIVE;
		Weapon.AmmoType "Clip";
		Weapon.SlotNumber 2;
		// A_FireBullets plays the weapon's AttackSound on the weapon channel
		// only when the shot actually happens, so the sound goes here rather
		// than in a separate A_StartSound.
		AttackSound "sd/weapon/tokarev/fire";
		Obituary "$SD_OB_TOKAREV";
		Tag "$SD_TAG_TOKAREV";
		Inventory.PickupMessage "$SD_PICKUP_TOKAREV";
		Inventory.PickupSound "sd/weapon/tokarev/pickup";  // SDTTPKP1/2 $random (N9e, D94)
		+WEAPON.WIMPY_WEAPON
	}

	States
	{
	Ready:
		SDTT A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDTT A 1 A_Lower;
		Loop;
	Select:
		SDTT A 1 A_Raise;
		Loop;
	Fire:
		// 4 + 6 + 3 + 3 = 16 tics per shot = 2.19 shots/s (Doom Pistol: 19 tics).
		// V3: an empty magazine reloads instead (0 tics; never with reloads off).
		SDTT A 0 A_JumpIf(invoker.SD_MagazineDry(SD_TT_MAGAZINE), "Reload");
		SDTT A 4;
		SDTT B 0 A_GunFlash;
		SDTT B 6 A_FireBullets(SD_TT_SPREAD, 0, SD_TT_BULLETS, SD_TT_DAMAGE);
		SDTT C 3;
		SDTT B 3 A_ReFire;
		Goto Ready;
	Reload:
		// V3 (magazine.zs): the gun goes down off screen and comes back up,
		// 42 tics, the magazine full again as it rises. The +reload key
		// comes here only when a reload would load (SD_ReadyFlags).
		SDTT A 0 A_JumpIf(!invoker.SD_CanReload(SD_TT_MAGAZINE), "Ready");
		SDTT A 0 A_SD_BeginReload;
	ReloadLoop:
		SDTT A 1 A_SD_ReloadTick(SD_TT_MAGAZINE, SD_TT_RELOAD_TICS, SD_TT_RELOAD_DROP, SD_TT_RELOAD_SOUND_TIC, "sd/weapon/tokarev/reload");
		SDTT A 0 A_JumpIf(invoker.sdReloadTic < SD_TT_RELOAD_TICS, "ReloadLoop");
		Goto Ready;
	Flash:
		SDTF A 5 Bright A_Light1;
		Goto LightDone;
	Spawn:
		SDTP A -1;
		Stop;
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDTTDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	// V3 reloads, both no-ops with sd_reloads off: a spent magazine reloads
	// at once (unless a weapon switch is pending), and the +reload key is
	// allowed when a reload would load.
	action state A_SD_WeaponReady()
	{
		if (player != null && player.PendingWeapon == WP_NOCHANGE
			&& invoker.SD_MagazineDry(SD_TT_MAGAZINE))
		{
			return ResolveState("Reload");
		}
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/tokarev/dry");
		A_WeaponReady(invoker.SD_ReadyFlags(SD_TT_MAGAZINE));
		return null;
	}
}
