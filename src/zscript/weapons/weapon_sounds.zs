// SD_WeaponSounds - the arsenal's empty click (N9, D74).
//
// Doom has no dry-fire sound: with too little ammo the trigger does nothing
// and, if another weapon has ammo, the engine switches to it. Silence read
// as a bug to the CEO once already ("una puerta que no hace ningun ruido"),
// and BALANCE.md section 4.1 keeps a case where it matters: an empty TT-33
// with no ice axe stays raised. So each gun's Ready state calls DryClick
// before A_WeaponReady, on the same frame: no tic, no state and no
// auto-switch changes (WEAPON-SOUNDS.md section 6).
//
// A class with only static functions, never instantiated. `play` scope
// because it starts a sound on the player (the engine's own ScriptUtil is
// declared the same way, gzdoom.pk3:zscript/scriptutil/scriptutil.zs).

class SD_WeaponSounds play
{
	// Plays `drysound` on the owner's weapon channel on the one tic the fire
	// button goes down while `w` is raised and cannot fire. CheckAmmo with
	// autoSwitch false only counts: the engine's own fire handling still
	// decides the switch, exactly as before. A held trigger clicks once.
	static void DryClick(Weapon w, Sound drysound)
	{
		if (w == null || w.Owner == null || w.Owner.player == null)
			return;
		let player = w.Owner.player;
		if (player.ReadyWeapon != w)
			return;
		bool pressed = (player.cmd.buttons & BT_ATTACK) && !(player.oldbuttons & BT_ATTACK);
		if (!pressed || w.CheckAmmo(Weapon.PrimaryFire, false))
			return;
		w.Owner.A_StartSound(drysound, CHAN_WEAPON);
	}
}
