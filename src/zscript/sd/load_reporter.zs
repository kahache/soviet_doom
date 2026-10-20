// SD_LoadReporter - smoke-test event handler.
//
// An EventHandler is a ZScript object the engine instantiates per map (as
// opposed to StaticEventHandler, which lives for the whole session) and
// whose virtual methods are called on world events. This one does nothing
// gameplay-wise: it writes a line to the console and the log file when the
// map has loaded so the log proves that MAPINFO (AddEventHandlers) and
// ZScript compiled and ran. It is registered in MAPINFO -> GameInfo ->
// AddEventHandlers. The gate reviews quote the line as evidence
// (docs/qa/GATE-REVIEWS.md), so its wording stays.
//
// LOG, NOT SCREEN (bug QA-G6-2). A plain Console.Printf is PRINT_HIGH, and
// GZDoom also copies every PRINT_HIGH line into the HUD's notify area: the
// player saw an English tooling line at the top of the screen at every map
// start, whatever the language. PRINT_NONOTIFY is the engine's flag for
// "console and log file, not the notify buffer"
// (gzdoom.pk3:zscript/engine/base.zs, enum EPrintLevel, g4.14.2, the D3
// minimum; Console.PrintfEx is declared in the same file with no version
// gate, so the `version "4.12"` pin compiles it).

class SD_LoadReporter : EventHandler
{
	// Console and +logfile, never the HUD.
	const REPORT_PRINT_LEVEL = PRINT_HIGH | PRINT_NONOTIFY;

	override void WorldLoaded(WorldEvent e)
	{
		Console.PrintfEx(REPORT_PRINT_LEVEL, "SOVIETDOOM loaded: map %s (%s)", level.MapName, level.LevelName);
	}
}
