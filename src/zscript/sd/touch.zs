// SD_Touch - the touch-screen switch (Android, D137; ADR 015) and the
// option row that names a key or a touch button.
//
// Contract: docs/engine/MOD-SPEC.md 6.17; the study of what a phone needs:
// docs/engine/2026-10-27_A1_mod-touch-adaptations.md.
//
// WHAT. The Android app (its own repository, D137) draws a touch layer over
// the engine and sends it KEYS and MOUSE DELTAS, nothing else; the engine
// never knows there is a screen being tapped. So every line of ours that
// names a key ("Press E", "R reloads") would still name a key on a phone,
// where the player taps a button labelled USE. The CVar `sd_touch`
// (src/lumps/CVARINFO: user, not archived, false) is the app's way to tell
// the mod: it passes `+sd_touch 1` on the engine's command line at every
// launch. The mod reads it, never writes it (ADR 004: ZScript may write a
// CVar only while handling menu input, and this one is not the player's to
// change in a menu). On a desktop it is false and nothing below changes a
// pixel.
//
// WHAT IT CHANGES, all read at draw time so the console can flip it live:
//   * the death prompt: SD_DEATH_PROMPT_TOUCH with the USE button's label
//     instead of SD_DEATH_PROMPT with the bound key (death_prompt.zs);
//   * the reload note in Options > Soviet Doom: the touch wording with the
//     RELOAD button's label (OptionMenuItemSDKeyText below);
//   * the magazine readout: centred above the bar, clear of the corners
//     where the stick and the buttons sit (magazine_hud.zs).
// The BUTTON LABELS are LANGUAGE's SD_TOUCH_BTN_* ids: the app labels its
// buttons with the same words, per language, so a prompt and the button it
// points at always agree (the contract is MOD-SPEC 6.17's table).

class SD_Touch
{
	// The CVar (src/lumps/CVARINFO). Missing (a broken package) means a
	// desktop: the game exactly as v1.3.
	const SD_TOUCH_CVAR = "sd_touch";

	static bool On()
	{
		CVar cv = CVar.FindCVar(SD_TOUCH_CVAR);
		return cv != null && cv.GetBool();
	}

	// The engine's name for the first key bound to `command` ("E",
	// "Space", "Mouse2"; KeyBindings.NameKeys), or the LANGUAGE string
	// `fallbackId` when nothing is bound (the engine's own control names,
	// "$CNTRLMNU_USE", "$CNTRLMNU_RELOAD", exist in every language it ships).
	static ui String KeyNameFor(String command, String fallbackId)
	{
		int first, second;
		[first, second] = Bindings.GetKeysForCommand(command);
		if (first > 0)
		{
			return KeyBindings.NameKeys(first, 0);
		}
		return StringTable.Localize(fallbackId);
	}
}

// OptionMenuItemSDKeyText - a StaticText row whose "%s" is the key bound to
// a command, or a touch button's label when sd_touch is on.
//
// MENUDEF writes it as
//   SDKeyText "$ID", "+command", "$ID_TOUCH", "$ID_OF_THE_BUTTON_LABEL"
// (a row keyword `Foo` is the class OptionMenuItemFoo, as the Language row
// already relies on; language_option.zs). It derives from the engine's
// StaticText row and overrides only Draw: the text is chosen and filled in
// when drawn, so rebinding the key in Customize Controls, or `sd_touch 1`
// in the console, shows at once. It writes nothing (ADR 004, D-004-4) and
// is not selectable, as a StaticText is not.
//
// The fallback when no key is bound: the engine's control name for the
// command, looked up as "$CNTRLMNU_" plus the command without its "+"
// ("+reload" -> "$CNTRLMNU_RELOAD", the Customize Controls row's label). If
// that id does not exist the engine returns the id itself, which is at least
// not wrong. The engine draws the row the way drawLabel does for a centred
// StaticText (optionmenuitems.zs): OptionWidth, CleanXfac_1, DrawOptionText.

class OptionMenuItemSDKeyText : OptionMenuItemStaticText
{
	const SD_KEY_PLACEHOLDER = "%s";
	const SD_CONTROL_NAME_PREFIX = "$CNTRLMNU_";

	String mCommand;
	String mTouchLabel;
	String mButtonId;

	OptionMenuItemSDKeyText Init(String label, String command, String touchLabel, String buttonId, int cr = -1)
	{
		Super.Init(label, cr);
		mCommand = command;
		mTouchLabel = touchLabel;
		mButtonId = buttonId;
		return self;
	}

	// The text as it reads now: desktop or touch, key or button.
	ui String SD_Text()
	{
		String text;
		if (SD_Touch.On())
		{
			text = StringTable.Localize(mTouchLabel);
			text.Substitute(SD_KEY_PLACEHOLDER, StringTable.Localize(mButtonId));
		}
		else
		{
			String fallback = SD_CONTROL_NAME_PREFIX .. SD_CommandStem(mCommand);
			text = StringTable.Localize(mLabel);
			text.Substitute(SD_KEY_PLACEHOLDER, SD_Touch.KeyNameFor(mCommand, fallback));
		}
		return text;
	}

	// "+reload" -> "RELOAD": the command without its "+", in capitals, the
	// spelling of the engine's CNTRLMNU_ ids.
	static String SD_CommandStem(String command)
	{
		String stem = command;
		if (stem.Left(1) == "+")
		{
			stem = stem.Mid(1);
		}
		return stem.MakeUpper();
	}

	override int Draw(OptionMenuDescriptor desc, int y, int indent, bool selected)
	{
		String text = SD_Text();
		int w = Menu.OptionWidth(text) * CleanXfac_1;
		int x = mCentered ? (screen.GetWidth() - w) / 2 : indent - w;
		drawText(x, y, mColor, text);
		return -1;
	}
}
