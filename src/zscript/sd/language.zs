// SD_LanguageGuard - makes the language the player sees and the language the
// menu claims agree, without touching anything else in their config.
//
// THE PROBLEM
// -----------
// GZDoom's `language` CVar defaults to "auto": the engine picks a LANGUAGE
// section from the operating system's locale. The CEO asked for an explicit
// choice (docs/product/LANGUAGE-SWITCH.md), and the mod's menu therefore
// offers exactly two values, "default" and "ru". An OptionMenu entry whose
// CVar holds a value that is not in its OptionValue list has nothing to
// show, so on a fresh install the language row would read as blank until
// the player touched it.
//
// THE FIX, AND WHY IT IS NOT A GUESS ABOUT THE PLAYER
// ---------------------------------------------------
// We do NOT override the player's locale. We ask the engine which section it
// actually resolved and write that same answer down explicitly. The question
// is asked through a probe string: every section of LANGUAGE defines
// SD_LANG_CODE with its own code ("default" in [enu default], "ru" in [ru]),
// so StringTable.Localize("$SD_LANG_CODE") returns the active section. A
// Russian-locale player keeps Russian; everyone else gets our default. The
// visible behaviour is unchanged - only the CVar stops saying "auto".
//
// WHAT IT WRITES
// --------------
// The `language` CVar and nothing else, once, and only while it still says
// "auto". `language` is archived by the engine, so the choice survives to
// the next session in the player's own gzdoom.ini, which is where a player
// expects their settings to be. This is the single key the mod is allowed
// to touch (CEO, 2026-10-13, after the tooling incident that left the CEO's
// own config with the music volume at zero; our TOOLS now run with their own
// -config, see tools/smoke.py).
//
// A StaticEventHandler (as opposed to EventHandler) lives for the whole
// session rather than per map, which is what we want: this must run once,
// not on every level load.

class SD_LanguageGuard : StaticEventHandler
{
	// GZDoom's value for "decide from the operating system locale".
	const AUTO_LANGUAGE = "auto";
	// The id whose value IS the active language code. Defined in every
	// section of LANGUAGE; see the comment there before adding a section.
	const LANGUAGE_PROBE = "$SD_LANG_CODE";

	override void OnRegister()
	{
		CVar lang = CVar.FindCVar("language");
		if (lang == null)
		{
			// Should be impossible: `language` is an engine CVar. Report it
			// rather than fail silently - the log is the contract (qa).
			Console.Printf("SOVIETDOOM: no 'language' CVar; language menu will not persist");
			return;
		}

		if (lang.GetString() != AUTO_LANGUAGE)
		{
			return;   // the player already has an explicit choice; leave it alone
		}

		// Whatever "auto" resolved to, say it out loud.
		string resolved = StringTable.Localize(LANGUAGE_PROBE);
		lang.SetString(resolved);
		Console.Printf("SOVIETDOOM: language was 'auto', pinned to '%s'", resolved);
	}
}
