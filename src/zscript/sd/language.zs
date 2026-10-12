// SD_LanguageMenu - the mod's options screen, and the one piece of logic the
// language switch needs: turning GZDoom's "auto" into an explicit choice.
//
// THE PROBLEM
// -----------
// GZDoom's `language` CVar defaults to "auto": the engine picks a LANGUAGE
// section from the operating system's locale. The CEO asked for an explicit
// choice (docs/product/LANGUAGE-SWITCH.md), so the mod's menu offers exactly
// two values, "default" and "ru". An OptionMenu row whose CVar holds a value
// absent from its OptionValue list has nothing to show and GZDoom prints
// "$TXT_UNKNOWN" instead (verified in gzdoom.pk3,
// zscript/engine/ui/menu/optionmenuitems.zs:313). On a config that has never
// been touched, the language row would therefore read "Unknown".
//
// WHY THIS IS A MENU CLASS AND NOT AN EVENT HANDLER
// -------------------------------------------------
// The obvious fix is a StaticEventHandler that normalizes the CVar at
// startup. GZDoom 4.14.2 refuses: the engine aborted the VM with
// "Attempt to change CVAR 'language' outside of menu code" (verified
// in-engine 2026-10-13). `language` may only be written from UI/menu scope,
// which is exactly what an OptionMenu subclass is. So the normalization
// happens the moment the player opens this screen, before a single row is
// drawn - which is also the only moment it can matter to anyone.
//
// WHAT IT DECIDES, AND WHAT IT REFUSES TO DECIDE
// ----------------------------------------------
// It does NOT override the player's locale. It asks the engine which section
// it actually resolved and writes that same answer down explicitly. The
// question is asked through a probe string: every section of LANGUAGE
// defines SD_LANG_CODE with its own code ("default" in [enu default], "ru"
// in [ru]), so StringTable.Localize("$SD_LANG_CODE") names the active
// section. A Russian-locale player stays in Russian; everyone else gets our
// default. Nothing the player sees changes - only the CVar stops saying
// "auto", so the menu can show a real value.
//
// WHAT IT WRITES
// --------------
// The `language` CVar and nothing else. That CVar is archived by the engine,
// so the choice reaches the next session through the player's own
// gzdoom.ini, which is where a player expects their settings to live. It is
// the single key this mod is allowed to touch (CEO, 2026-10-13, after the
// incident where our TOOLING wrote to the CEO's config and left him with the
// music volume at zero; the tools now run with their own -config, see
// tools/smoke.py).

class SD_LanguageMenu : OptionMenu
{
	// GZDoom's value for "decide from the operating system locale".
	const AUTO_LANGUAGE = "auto";
	// The id whose value IS the active language code. Defined in every
	// section of LANGUAGE; read the comment there before adding a section.
	const LANGUAGE_PROBE = "$SD_LANG_CODE";

	override void Init(Menu parent, OptionMenuDescriptor desc)
	{
		PinLanguage();
		Super.Init(parent, desc);
	}

	// Replace "auto" with whatever "auto" already resolved to. Idempotent:
	// once the CVar is explicit this does nothing, so a player's own choice
	// is never second-guessed.
	private void PinLanguage()
	{
		CVar lang = CVar.FindCVar("language");
		if (lang == null || lang.GetString() != AUTO_LANGUAGE)
		{
			return;
		}
		string resolved = StringTable.Localize(LANGUAGE_PROBE);
		lang.SetString(resolved);
	}
}
