// SD_ConsortiumWounded - a TEST FIXTURE for the PM's engine pass (D26),
// not an enemy: the Consortium (consortium.zs) spawned at half its health
// plus a margin, so the first hits trigger the Breach and phase 2 can be
// played without emptying an arsenal first. `summon SD_ConsortiumWounded`.
// No editor number, no LANGUAGE id of its own (it inherits the boss's);
// placed by no map. Kept in the mod (D116) while the boss is tuned; delete
// this file and its #include when the engine pass no longer needs it.

class SD_ConsortiumWounded : SD_Consortium
{
	const SD_WOUNDED_MARGIN = 100;   // HP over the Breach threshold: two or three hits

	override void PostBeginPlay()
	{
		Super.PostBeginPlay();
		health = int(SpawnHealth() * SD_CONSORTIUM_BREACH_FRACTION) + SD_WOUNDED_MARGIN;
	}
}
