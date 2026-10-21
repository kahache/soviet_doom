// OptionMenuItemSDLanguageOption - the Language row of Options > Soviet Doom.
//
// A MENUDEF row keyword `Foo` makes GZDoom build an object of the ZScript
// class `OptionMenuItemFoo`, so MENUDEF writes this row as
// `SDLanguageOption "$SD_OPTMNU_LANGUAGE", "language", "SD_LanguageValues"`.
// It is the engine's own `Option` row (OptionMenuItemOption,
// gzdoom.pk3:zscript/engine/ui/menu/optionmenuitems.zs) with ONE change: how
// it decides which entry of the list to DRAW.
//
// WHY (bug QA-G6-1). The engine's row compares the `language` CVar with the
// list's left column literally (case-insensitive) and, on no match, draws
// "Unknown". Our list has four entries - auto, default, ru, ca (Catalan
// since D97, P6) - but the CVar can hold other spellings of the same
// languages: GZDoom's own Language menu writes "eng" for English (UK), a
// console `language enu` or `language en` is legal, and so are "rus" and
// "cat". For the TEXT OF THIS MOD every one of those resolves to a section we
// ship: the mod has `[enu default]`, `[ru]` and `[ca]`, so any code that is
// not auto, Russian or Catalan falls through to `default`, i.e. English. The
// row now names that language instead of "Unknown".
//
// WHAT THIS CLASS MAY NOT DO (ADR 004, D-004-4). ZScript may write a CVar
// only while the engine handles menu input; a write from Init, Ticker or
// Drawer aborts the VM. This class therefore overrides nothing but
// GetSelection, which only READS the CVar. Changing the language still goes
// through the inherited SetSelection, called from the inherited MenuEvent -
// input handling, exactly as before - and writes one of the three listed
// values. Pressing left/right on a row showing "eng" as English moves to the
// neighbour of English, as a player would expect.
//
// HOW GZDOOM PICKS [ca] (FStringTable::UpdateLanguage, g4.14.2; NOT VERIFIED
// in the engine for Catalan, D26): the CVar's 2-3 letters are the language
// id; the table tries that id, then its first two letters, then `default`.
// "ca" (and "cat") therefore read our [ca] section, and every engine string
// [ca] does not define (GZDoom ships no Catalan) falls back to English.
// The CVar's change callback re-reads the table at once, as for "ru".

class OptionMenuItemSDLanguageOption : OptionMenuItemOption
{
	// The list entry each language is stored under (src/lumps/MENUDEF,
	// OptionString "SD_LanguageValues"). A test pins these to that list.
	const VALUE_AUTO = "auto";
	const VALUE_ENGLISH = "default";
	const VALUE_RUSSIAN = "ru";
	const VALUE_CATALAN = "ca";

	OptionMenuItemSDLanguageOption Init(String label, Name command, Name values, CVar graycheck = null, int center = 0, int graycheckVal = 0)
	{
		Super.Init(label, command, values, graycheck, center, graycheckVal);
		return self;
	}

	// The list entry whose label describes `value`. Exact entries map to
	// themselves; "" and "auto" are the engine's "ask the system"; any "ru*"
	// code selects our [ru] section and any "ca*" code our [ca] (GZDoom also
	// tries a code's two-letter base); everything else reads our
	// [enu default] section.
	static String ListEntryFor(String value)
	{
		if (value.Length() == 0 || value ~== VALUE_AUTO)
		{
			return VALUE_AUTO;
		}
		if (value.Left(2) ~== VALUE_RUSSIAN)
		{
			return VALUE_RUSSIAN;
		}
		if (value.Left(2) ~== VALUE_CATALAN)
		{
			return VALUE_CATALAN;
		}
		return VALUE_ENGLISH;
	}

	override int GetSelection()
	{
		int selection = Super.GetSelection();
		if (selection >= 0 || mCVar == null)
		{
			return selection;
		}
		String entry = ListEntryFor(mCVar.GetString());
		int count = OptionValues.GetCount(mValues);
		for (int i = 0; i < count; i++)
		{
			if (entry ~== OptionValues.GetTextValue(mValues, i))
			{
				return i;
			}
		}
		return selection;
	}
}
