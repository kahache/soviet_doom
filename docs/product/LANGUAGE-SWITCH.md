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

**Decided by the CEO, 2026-10-13: the English build substitutes Cyrillic
letterforms. R becomes Я and N becomes И.**

The PM argued against it — a fake accent, read as a joke, against the serious
tone of D11, and costly to legibility at 320×200 — and the CEO disagreed and
decided. Recorded so the reasoning is not relitigated, not so it is reopened.

### The substitution map

The CEO named the core pair. Three intensities were rendered on real game
strings (`docs/art/previews/2026-10-13_0120_F2_faux-cyrillic-levels.png`) so
the level can be chosen on evidence rather than in the abstract:

| Level | Map | Effect |
|---|---|---|
| **1 — the CEO's core** | R→Я, N→И | Reads as English everywhere. "ZARYA-7 COSMODЯOME", "ИOT OИE STEP BACK" |
| 2 | + E→Э, W→Ш, A→Д | "ЗДЯУД-7" stops being readable as Zarya |
| 3 | + U→Ц, G→Б, D→Д, Y→У, B→Б | Words dissolve; "A BOX" becomes "Д БОХ" |

**Recommendation: level 1, the CEO's own pair, and nothing beyond it.** The
two he named are the two that survive being read. From level 2 the device
stops decorating English and starts replacing it, which costs the player
information rather than giving them flavour.

### Where it applies

- **Yes**: the English build's display type and menus.
- **No**: the Russian build, where real Cyrillic is real Cyrillic and a
  substituted Я would simply be a spelling mistake.
- **No**: numbers, weapon calibres and key prompts, where a misread costs
  the player something.

The substitution is a **font-level mapping**, not an edit to the strings:
`LANGUAGE` keeps correct English so the text stays searchable, translatable
and diffable, and the English font draws those two letters with their
Cyrillic forms. One switch turns it off if it ever grates.

## The shared blocker

Both wait on debt **T9**, the Cyrillic font. Freedoom's font is ASCII only,
and the Cyrillic glyphs GZDoom ships are gated behind a filter that only
activates for an id Software IWAD, which we do not use. Verified on screen by
`mod-engineer`: «ПГ-7В» renders as « -7B».

So the order is: font, then language switch, then the Latin-with-Cyrillic-
bones variant. The font is in progress.
