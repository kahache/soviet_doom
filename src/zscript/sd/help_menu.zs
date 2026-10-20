// SD_HelpMenu - what F1 opens: our credits, not Freedoom's help pictures
// (M4 shell, audit docs/qa/2026-10-14_2357_M2-freedoom-audit.md, H4).
//
// WHAT THIS IS
// ------------
// Doom's help key (F1, the console command `menu_help`) opens the menu named
// ReadThisMenu, and GZDoom swaps that name for GameInfo's HelpMenuClass
// before opening it (gzdoom g4.14.2 src/menu/doommenu.cpp, M_SetSpecialMenu:
// "allow us to override the ReadThisMenu class"). The engine's own class
// draws GameInfo's InfoPage pictures, which on Freedoom are its English HELP
// and CREDIT screens. Our MAPINFO names this class instead.
//
// WHAT IT DOES
// ------------
// It draws nothing. On its first tic it opens SD_CreditsMenu, the credits
// option screen of ADR 009 (MENUDEF), as its child. When the player backs
// out of the credits, this menu is the current one again and closes itself
// on the next tic, so Escape from the credits returns to wherever F1 was
// pressed (the game or the title) in one key press, as Doom's help does.
//
// RULES IT KEEPS
// --------------
// No CVar writes (ADR 004, D-004-4; tests/test_language.py). The class must
// exist and derive from Menu, or the engine stops at startup with
// "Undefined help menu class" (doommenu.cpp, SetDefaultMenuColors);
// tests/test_freedoom_text.py ties the MAPINFO name to this class.
// NOT VERIFIED in the engine (D26, the PM's batched pass): the one-tic
// frame between the two menus, and that Menu.SetMenu from Ticker gives the
// credits this menu as parent (M_SetMenu passes CurrentMenu as the parent).

class SD_HelpMenu : GenericMenu
{
	bool mCreditsOpened;

	override void Init(Menu parent)
	{
		Super.Init(parent);
		// Nothing of ours is drawn, so the one tic this menu is on screen
		// must not dim or blur the view behind it.
		DontDim = true;
		DontBlur = true;
		mCreditsOpened = false;
	}

	override void Ticker()
	{
		Super.Ticker();
		if (GetCurrentMenu() != self)
		{
			return;
		}
		if (!mCreditsOpened)
		{
			mCreditsOpened = true;
			// The credits screen: the OptionMenu of this name in MENUDEF.
			Menu.SetMenu('SD_CreditsMenu');
		}
		else
		{
			// Back from the credits: leave the way F1 came in.
			Close();
		}
	}

	override void Drawer()
	{
		// Deliberately empty (no back button either): the credits draw
		// themselves.
	}
}
