"""Pickup events on episode 3's maps (V3, D120's A2 and A3): the model and the checks.

Owner: `level-designer`. Not a test module (no `test` prefix): MAP07's,
MAP08's and MAP09's tests mix `PickupEventChecks` in and call the model
helpers from their own `heights()` and progression.

What a pickup event is (MAP04's red key and MAP09's red key are the model):
a thing - a key or an item - whose UDMF `special` and `arg0..` GZDoom runs
when the player picks it up (Inventory's pickup special; the Door_Open form
VERIFIED in the engine by tunguska-critical's RKEY step, 2026-10-23 02:23).
Its tag is carried by NO line, so nothing but the pickup moves those sectors.
Each map lists its events in `PICKUP_EVENTS` (map.py), one row each:

    name     a short id
    trigger  the editor number of the thing that carries the special
    spot     (x, y) of that thing (one thing there, on every skill)
    special  Door_Open (11) or Floor_LowerToLowest (21)
    args     the special's arguments, the tag first
    zones    the sectors the tag moves (a closet's door, a sinking wall, a
             lift's car)
    waiting  where the released monsters wait (the closet, the cell, the car)
    lamp     the warning: a flickering lamp (sector special 65) in front of
             the event, seen before it fires

The model, the same one the doors use: a Door_Open sector is a door (its
ceiling rises to its lowest neighbour's minus 4); a Floor_LowerToLowest
sector's floor drops to the lowest floor among itself and its neighbours
(Doom's P_FindLowestFloorSurrounding). A pickup fires as soon as its thing's
sector is reachable, in the same round (the player is standing on it).

The rules the checks hold (the V3 brief): an event never shuts the player in
and never sits on the critical path (the exit is reached with every event
tag left shut); its monsters are hidden until it fires (no line from them to
the rest of the map has an opening, so nothing sees or hears through), are
there on every skill and far from the start; and it is warned: the lamp in
front of it flickers before it fires, and the moving sector sounds.
"""

from __future__ import annotations

import math

SPECIAL_DOOR_OPEN = 11
SPECIAL_FLOOR_LOWER_TO_LOWEST = 21
SECTOR_SPECIAL_LIGHT_FLICKER = 65
SAFE_START_DISTANCE = 768        # tests/test_safe_starts.py's
EVENT_SKILLS = (2, 3, 4)
ALL_SKILLS = (1, 2, 3, 4, 5)


def floor_movers(module) -> dict[int, list[str]]:
    """{tag: zone names} for the map's Floor_LowerToLowest events."""
    return {e.args[0]: list(e.zones) for e in module.PICKUP_EVENTS
            if e.special == SPECIAL_FLOOR_LOWER_TO_LOWEST}


def lowest_floor(index: int, sectors, neighbours) -> int:
    return min([sectors[index]["heightfloor"]] + [sectors[n]["heightfloor"] for n in neighbours[index]])


def apply_moves(out: list, sectors, neighbours, plan, module, open_tags) -> list:
    """Lower the floor of every Floor_LowerToLowest event whose tag is open
    (in place on `out`, a list of (floor, ceiling) per sector)."""
    for tag, zones in floor_movers(module).items():
        if tag not in open_tags:
            continue
        for name in zones:
            i = plan[name]
            out[i] = (lowest_floor(i, sectors, neighbours), out[i][1])
    return out


def pickup_tags(things, monster_numbers) -> list[tuple[int, tuple[float, float]]]:
    """[(tag, (x, y))] of every non-monster thing carrying a special."""
    return [(t["arg0"], (t["x"], t["y"])) for t in things
            if t.get("special") and t["type"] not in monster_numbers]


class PickupEventChecks:
    """Mixed into a map's TestCase. Needs from it: m, plan, sectors, lines,
    things, neighbours, zone_of, rounds, every_tag, monster_numbers,
    heights(open_tags), adjacency(open_tags), reachable(open_tags),
    flood(adj, start), reverse(adj), sector_at(x, y), monsters(),
    on(skill, things), named(*names), exit_sector() and start."""

    def events(self):
        events = self.m.PICKUP_EVENTS
        self.assertTrue(events, "V3: the map has its pickup events")
        return events

    def event_tags(self):
        return {e.args[0] for e in self.events()}

    def waiting_monsters(self, event, skill):
        rooms = self.named(*event.waiting)
        return [t for t in self.on(skill, self.monsters()) if self.sector_at(t["x"], t["y"]) in rooms]

    def test_pickup_events_two_or_three_and_their_tags_are_their_own(self):
        events = self.events()
        self.assertGreaterEqual(len(events), 2, "V3 brief: two or three events a map")
        self.assertLessEqual(len(events), 4)
        tags = [e.args[0] for e in events]
        self.assertEqual(len(tags), len(set(tags)), "one tag an event")
        for e in events:
            self.assertIn(e.special, (SPECIAL_DOOR_OPEN, SPECIAL_FLOOR_LOWER_TO_LOWEST), e.name)
            tag = e.args[0]
            tagged = {i for i, s in enumerate(self.sectors) if s.get("id") == tag}
            self.assertEqual(self.named(*e.zones), tagged, f"{e.name}: tag {tag} moves its zones and nothing else")
            carried = [i for i, ld in enumerate(self.lines) if ld.get("special") and ld.get("arg0") == tag]
            self.assertEqual([], carried, f"{e.name}: no line carries tag {tag}, only the pickup")

    def test_each_pickup_event_rides_its_thing_on_every_skill(self):
        found = []
        for e in self.events():
            here = [t for t in self.things if t["type"] == e.trigger and (t["x"], t["y"]) == tuple(e.spot)]
            self.assertEqual(1, len(here), f"{e.name}: one thing {e.trigger} at {e.spot}")
            t = here[0]
            args = tuple(e.args) + (0,) * (5 - len(e.args))
            self.assertEqual((e.special,) + args, (t.get("special"),) + tuple(t.get(f"arg{i}", 0) for i in range(5)),
                             e.name)
            for skill in ALL_SKILLS:
                self.assertTrue(t[f"skill{skill}"], f"{e.name}: its thing is missing on skill {skill}")
            found.append((e.args[0], (t["x"], t["y"])))
        self.assertEqual(sorted(found), sorted(pickup_tags(self.things, self.monster_numbers)),
                         "every item special is an event of PICKUP_EVENTS")

    def test_each_pickup_event_hides_its_monsters_until_it_fires(self):
        """Before the pickup, no line from the rooms its monsters wait in to
        any other sector (its moving zones included) has an opening: nothing
        is seen through it, and no sound goes through it (Doom's sound stops
        at a closed line), so they wait."""
        h = self.heights(set())
        for e in self.events():
            hidden = self.named(*e.waiting)
            for ld in self.lines:
                if "sideback" not in ld:
                    continue
                a = self.sides[ld["sidefront"]]["sector"]
                b = self.sides[ld["sideback"]]["sector"]
                if (a in hidden) == (b in hidden):
                    continue
                opening = min(h[a][1], h[b][1]) - max(h[a][0], h[b][0])
                self.assertLessEqual(opening, 0, f"{e.name}: {self.zone_of[a]} | {self.zone_of[b]}")

    def test_each_pickup_event_opens_onto_where_its_thing_is_taken(self):
        """The thing's place is reached without the event; the event's rooms
        are not; once it fires they open onto the room the lamp is in, and
        there is a way back from them. It fires in the round its thing is
        reached (MAP07's and MAP08's model: he is standing on it) or the next
        one (MAP04's and MAP09's, which open a pickup like a lock), never
        before."""
        for e in self.events():
            tag = e.args[0]
            without = self.reachable(self.every_tag - {tag})
            trigger = self.sector_at(*e.spot)
            self.assertIn(trigger, without, f"{e.name}: its thing needs its own event")
            waiting = self.named(*e.waiting)
            self.assertFalse(waiting & without, f"{e.name}: open without the pickup")
            self.assertTrue(waiting <= self.rounds[-1][1], f"{e.name}: never opens")
            reached = next(k for k, r in enumerate(self.rounds) if trigger in r[1])
            fired = next(k for k, r in enumerate(self.rounds) if tag in r[0])
            self.assertIn(fired, (reached, reached + 1), f"{e.name}: fired away from its thing")
            self.assertTrue(waiting <= self.rounds[fired][1], f"{e.name}: not with its pickup")
            if fired:
                self.assertFalse(waiting & self.rounds[fired - 1][1], f"{e.name}: open before it fires")
            lamp = self.plan[e.lamp]
            onward = self.flood(self.adjacency(self.every_tag), lamp)
            self.assertTrue(waiting <= onward, f"{e.name}: its rooms do not open onto its lamp's")
            back = self.flood(self.reverse(self.adjacency(self.every_tag)), self.start)
            self.assertTrue(waiting <= back, f"{e.name}: a trap")

    def test_each_pickup_event_moves_as_its_special_says(self):
        """Door_Open: the zones are doors (floor = ceiling) that rise a door
        high. Floor_LowerToLowest: each zone's floor drops at least a body's
        height, to its room's floor."""
        for e in self.events():
            tag = e.args[0]
            before, after = self.heights(set()), self.heights({tag})
            for name in e.zones:
                i = self.plan[name]
                if e.special == SPECIAL_DOOR_OPEN:
                    self.assertEqual(before[i][0], before[i][1], f"{e.name}: {name} is a shut door")
                    self.assertGreaterEqual(after[i][1] - after[i][0], 56, name)
                else:
                    self.assertGreaterEqual(before[i][0] - after[i][0], 56, f"{e.name}: {name} hardly moves")
                    self.assertEqual(self.sectors[self.plan[e.lamp]]["heightfloor"], after[i][0],
                                     f"{e.name}: {name} comes down to the lamp's floor")

    def test_each_pickup_event_holds_a_fight_on_every_skill_far_from_the_start(self):
        sx, sy = self.m.PLAYER_START
        for e in self.events():
            counts = {skill: len(self.waiting_monsters(e, skill)) for skill in EVENT_SKILLS}
            self.assertGreaterEqual(counts[2], 1, f"{e.name}: empty on skill 2")
            self.assertLessEqual(counts[2], counts[3], e.name)
            self.assertLessEqual(counts[3], counts[4], e.name)
            for t in self.waiting_monsters(e, 4):
                self.assertGreaterEqual(math.dist((t["x"], t["y"]), (sx, sy)), SAFE_START_DISTANCE,
                                        f"{e.name}: a monster near the start")

    def test_each_pickup_event_is_warned_by_a_flickering_lamp(self):
        """The lamp is Doom's random flicker (65, as the bunker's lamp on
        MAP07 and MAP01's), brighter than the darkest of its neighbours so
        the flicker shows, touching the event, in reach before it fires."""
        for e in self.events():
            lamp = self.plan[e.lamp]
            s = self.sectors[lamp]
            self.assertEqual(SECTOR_SPECIAL_LIGHT_FLICKER, s.get("special"), e.lamp)
            self.assertGreater(s["lightlevel"], min(self.sectors[n]["lightlevel"] for n in self.neighbours[lamp]),
                               f"{e.lamp}: no darker neighbour, no flicker")
            self.assertTrue(self.neighbours[lamp] & self.named(*e.zones, *e.waiting), f"{e.lamp} is not at {e.name}")
            self.assertIn(lamp, self.reachable(self.every_tag - {e.args[0]}), e.lamp)

    def test_no_pickup_event_is_needed(self):
        """Never on the critical path: the exit with every event left shut."""
        self.assertIn(self.exit_sector(), self.reachable(self.every_tag - self.event_tags()))
