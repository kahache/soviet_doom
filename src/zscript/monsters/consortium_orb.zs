// SD_ConsortiumOrb - one energy ball of the Consortium's fans, fired from
// its Legion arm (consortium.zs). Not placeable.
// In the mod since D116 (design: docs/engine/2026-10-22_P4_ep3-final-boss.md 4).
//
// The General's shell (SD_GeneralShell: SDGL, a white-hot core in a yellow
// fire, his launch and burst sounds), slower and lighter because it comes
// three or five at a time: a fan is read and side-stepped, not tanked. It
// flies THROUGH monsters, as the rocket does.

class SD_ConsortiumOrb : SD_GeneralShell
{
	const SD_CNORB_SPEED     = 16;   // (H) the shell flies 20; a fan needs time to read
	const SD_CNORB_FASTSPEED = 20;   // fast monsters / skill 5: the shell's own speed
	const SD_CNORB_DAMAGE    = 6;    // x random(1,8) = 6..48, avg 27 (the shell: avg 36)

	Default
	{
		Speed SD_CNORB_SPEED;
		FastSpeed SD_CNORB_FASTSPEED;
		Damage SD_CNORB_DAMAGE;
	}

	override bool CanCollideWith(Actor other, bool passive)
	{
		if (!passive && other.bIsMonster && other.player == null)
			return false;
		return Super.CanCollideWith(other, passive);
	}
}
