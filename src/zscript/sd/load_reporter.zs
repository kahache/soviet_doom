// SD_LoadReporter - smoke-test event handler.
//
// An EventHandler is a ZScript object the engine instantiates per map (as
// opposed to StaticEventHandler, which lives for the whole session) and
// whose virtual methods are called on world events. This one does nothing
// gameplay-wise: it prints a line to the console when the map has loaded so
// the log proves that MAPINFO (AddEventHandlers) and ZScript compiled and
// ran. It is registered in MAPINFO -> GameInfo -> AddEventHandlers.

class SD_LoadReporter : EventHandler
{
	override void WorldLoaded(WorldEvent e)
	{
		Console.Printf("SOVIETDOOM loaded: map %s (%s)", level.MapName, level.LevelName);
	}
}
