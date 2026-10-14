// SD_IceAxePuff - what the ice axe leaves where it strikes (N9, D74).
//
// Doom's BulletPuff with one addition: its AttackSound is the pick on
// stone, SDAXWAL. A "puff" is the small actor a hitscan or melee attack
// spawns where it lands. The engine plays a puff's AttackSound when the
// puff is spawned on a wall, floor or ceiling; on a monster that bleeds no
// puff is spawned (blood is), so the flesh hit stays A_SD_IceAxeSwing's own
// sd/weapon/iceaxe/hit. A miss spawns nothing and is silent but for the
// swing. The same mechanism carries Heretic's staff (StaffPuff,
// gzdoom.pk3:zscript/actors/heretic/weaponstaff.zs). NOT VERIFIED in our
// engine pass: that a bleeding target plays no wall sound, and that a
// non-bleeding one (a barrel) plays both, wall and hit (WEAPON-SOUNDS 6).
//
// Sprites: the inherited PUFF frames of the IWAD, no state of ours.

class SD_IceAxePuff : BulletPuff
{
	Default
	{
		AttackSound "sd/weapon/iceaxe/wall";
	}
}
