# Playing the whole game in Russian, and a Latin that remembers Cyrillic

Owner: PM. Status: **requested by the CEO 2026-10-13**, commissioned.
Russian mirror pending.

**Veredicto literal:** "Molaría que el juego permita elegir si lanzar todo en
ruso. Y si se lanza en inglés, que algunas letras parezcan (o se tomen) del
cirílico."

Two separate things, with one shared blocker.

## 1. The language switch

Every string the player sees already exists in both languages (D7): pickup
messages, map names, the difficulty ladder, weapon tags. What is missing is a
way to choose, and a menu that survives the choice.

Scope for `mod-engineer`:
- A language option in the mod's own menu, driven by GZDoom's `language`
  CVar, offering English and Russian explicitly rather than relying on the
  system locale.
- An audit that **every** `SD_*` string id has a `[ru]` line. A half-translated
  game is worse than an English one, because the gaps look like bugs.
- The choice must persist between sessions, and it must not write to the
  player's own engine config beyond that CVar.

## 2. A Latin alphabet that remembers Cyrillic

This is a type decision, not a code one, and it goes to `art-director` as a
follow-up to the font already in progress.

The cheap version of this idea is faux Cyrillic: swapping R for Я and N for
И. **I recommend against it.** It is the visual equivalent of a fake accent,
it is read as a joke, and the mod's tone is serious (D11). It also hurts
legibility, which matters at 320×200.

The version worth doing is subtler and better: draw the **Latin glyphs with
the stroke logic of the Cyrillic ones**. Soviet poster lettering has a
particular skeleton, heavy verticals, flat terminals, a narrow aperture, and
when a Latin R, N or E is built on that skeleton it reads as Latin but feels
of a piece with Я, И and Э sitting next to it. The two scripts then share a
voice instead of one imitating the other.

Where a genuine swap earns its place is in **display type only**, a title or
a poster headline, never body text: `SOVIET DOOM` can afford one borrowed
letterform; a pickup message cannot.

## The shared blocker

Both wait on debt **T9**, the Cyrillic font. Freedoom's font is ASCII only,
and the Cyrillic glyphs GZDoom ships are gated behind a filter that only
activates for an id Software IWAD, which we do not use. Verified on screen by
`mod-engineer`: «ПГ-7В» renders as « -7B».

So the order is: font, then language switch, then the Latin-with-Cyrillic-
bones variant. The font is in progress.
