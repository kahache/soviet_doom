// SD_PanzermenschSchwer - the heavy Panzermensch, 1000 HP, for MAP03
// (BESTIARY section 8, D35). Replaces Doom's BaronOfHell, so a map that
// places thing 3003 gets ours and not a Freedoom baron.
//
// It derives from SD_Panzermensch - the way Doom derives the Hell Knight
// from the Baron - and changes only its health and its name. No States of
// its own: it looks identical until art-director's SDPM sprites land and a
// Translation recolours it (BESTIARY 2.7). Doom's Baron also carries
// +BOSSDEATH for E1M8-style map specials; no map of ours uses them.

class SD_PanzermenschSchwer : SD_Panzermensch replaces BaronOfHell
{
	const SD_PANZER_HEAVY_HEALTH = 1000;   // BaronOfHell parity (D35)

	Default
	{
		Health SD_PANZER_HEAVY_HEALTH;
		Tag "$SD_TAG_PANZER_HEAVY";
	}
}
