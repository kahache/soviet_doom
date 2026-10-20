// SD_Izh - slot 3, the IZh-58 side-by-side 12-gauge hunting shotgun.
//
// Replaces Doom's Shotgun. It is a genuine double barrel: two shots, then
// the gun has to be broken open and reloaded. That break-open pause is the
// weapon's character and is tracked by the `barrels` counter below.
//
// The mod has no super shotgun; MAPINFO maps editor number 82 to None so
// Freedoom's SSG can never appear. This weapon therefore has to carry the
// whole of slot 3 and sits between Doom's Shotgun and its SSG in damage.
//
// Sprites, all ours. The world pickup since D48 (2026-10-14): SDIP A (was
// the IWAD's SHOT). The held frames SDIZ A-D and the flash SDIF A-B since
// D84 (2026-10-20), built from the CEO's Google Gemini images (ready,
// firing, reloading) by tools/art/gemini_frames.py; only the four-letter
// names changed, every tic, action and jump is as it was. All in
// assets/sprites/izh/. MOD-SPEC 6.3; tests/test_gemini_weapons_install.py.
// Balance rationale: docs/engine/BALANCE.md.

class SD_Izh : Shotgun replaces Shotgun
{
	// --- Balance constants -------------------------------------------------
	// Reference per pellet is Doom's 5 x random(1,3) (avg 10); Doom's Shotgun
	// fires 7 pellets every 44 tics, the SSG 20 pellets (2 shells) every 57.
	const SD_IZH_PELLETS    = 8;     // avg 80 damage per barrel
	const SD_IZH_DAMAGE     = 5;     // x random(1,3) per pellet, Doom's value
	const SD_IZH_SPREAD_X   = 8.0;   // degrees; Doom shotgun 5.625, SSG 11.25
	const SD_IZH_SPREAD_Y   = 3.5;   // hunting choke: a real vertical spread
	const SD_IZH_BARRELS    = 2;     // shots before the break-open reload
	const SD_IZH_AMMO_USE   = 1;     // one shell per barrel
	const SD_IZH_AMMO_GIVE  = 8;     // same as Doom's shotgun pickup

	// Shots left in the barrels. Reset by the Reload state.
	int barrels;

	override void BeginPlay()
	{
		Super.BeginPlay();
		barrels = SD_IZH_BARRELS;   // the gun is picked up loaded
	}

	Default
	{
		Weapon.SelectionOrder 1300;
		Weapon.AmmoUse SD_IZH_AMMO_USE;
		Weapon.AmmoGive SD_IZH_AMMO_GIVE;
		Weapon.AmmoType "Shell";
		Weapon.SlotNumber 3;
		AttackSound "sd/weapon/izh/fire";
		Obituary "$SD_OB_IZH";
		Tag "$SD_TAG_IZH";
		Inventory.PickupMessage "$SD_PICKUP_IZH";
	}

	States
	{
	Ready:
		SDIZ A 1 A_SD_WeaponReady;
		Loop;
	Deselect:
		SDIZ A 1 A_Lower;
		Loop;
	Select:
		SDIZ A 1 A_Raise;
		Loop;
	Fire:
		// 3 + 6 + 4 + 4 + 3 + 3 = 23 tics per barrel (Doom Shotgun: 44).
		SDIZ A 3;
		SDIZ A 6 A_SD_FireIzh;
		SDIZ B 4;
		SDIZ C 4;
		SDIZ A 3 A_JumpIf(invoker.barrels <= 0, "Reload");
		SDIZ A 3 A_ReFire;
		Goto Ready;
	Reload:
		// 6 + 8 + 8 + 8 = 30 tics to break the gun open and feed two shells.
		SDIZ D 6 A_StartSound("sd/weapon/izh/reload", CHAN_WEAPON);
		SDIZ C 8;
		SDIZ B 8;
		SDIZ A 8 A_SD_ReloadIzh;
		Goto Ready;
	Flash:
		SDIF A 4 Bright A_Light1;
		SDIF B 3 Bright A_Light2;
		Goto LightDone;
	Spawn:
		SDIP A -1;
		Stop;
	}

	// Fires one barrel. A_FireBullets consumes one Shell (FBF_USEAMMO is on
	// by default) and plays AttackSound.
	action void A_SD_FireIzh()
	{
		if (invoker.barrels <= 0)
			return;   // defensive: the Reload branch should have caught this

		A_GunFlash();
		A_FireBullets(SD_IZH_SPREAD_X, SD_IZH_SPREAD_Y, SD_IZH_PELLETS, SD_IZH_DAMAGE);
		invoker.barrels--;
	}

	action void A_SD_ReloadIzh()
	{
		invoker.barrels = SD_IZH_BARRELS;
	}

	// Ready with the empty click (N9, D74): A_WeaponReady exactly as before,
	// plus SDIZDRY on the tic the trigger goes down with too little ammo to
	// fire (SD_WeaponSounds.DryClick, weapon_sounds.zs). Same frame, same tic.
	action void A_SD_WeaponReady()
	{
		SD_WeaponSounds.DryClick(invoker, "sd/weapon/izh/dry");
		A_WeaponReady();
	}
}
