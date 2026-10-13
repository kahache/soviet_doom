# Playing the whole game in Russian, and a Latin that remembers Cyrillic

Owner: PM. Status: **requested by the CEO 2026-10-13**, commissioned.
Russian mirror: `docs/ru/product/LANGUAGE-SWITCH.md`.

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
| 1 | R→Я, N→И | Reads as English everywhere |
| **2 — CHOSEN by the CEO 2026-10-13** | + E→Э, W→Ш, A→Д | The level that ships |
| 3 | + U→Ц, G→Б, D→Д, Y→У, B→Б | Words dissolve; "A BOX" becomes "Д БОХ" |

The PM recommended level 1; the CEO saw all three rendered on real strings
and chose 2. Settled.

### One carve-out the level-2 map needs

At level 2 the proper noun **ZARYA-7 renders as ZДЯYД-7**. (An earlier
version of this document said ЗДЯУД-7 and the CEO caught it: Z is not in the
map and never was, nor is Y. The PM had transcribed the rendered sheet from
memory instead of from the mapping. Corrected, and the number of letters the
device actually touches is smaller than the PM claimed.)

Even so ZДЯYД-7 no longer reads as the name of the cosmodrome the whole game
is set in, and the same applies to any calibre the player has to act on. The
mapping is therefore applied to **running text and menus**, and these keep
Latin:

- Proper nouns the fiction depends on: ZARYA-7, the faction names.
- Numbers, calibres and model designations: 7.62x25, PG-7V, PPSh-41.
- Key prompts and anything the player must type or match.

This is a one-line exclusion list in the font mapping, not a judgement to be
made string by string.

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

## The shared blocker, paid

Both waited on debt **T9**, the Cyrillic font. Freedoom's font is ASCII only,
and the Cyrillic glyphs GZDoom ships are gated behind a filter that only
activates for an id Software IWAD, which we do not use. Verified on screen by
`mod-engineer`: «ПГ-7В» rendered as « -7B».

**Paid on 2026-10-13 by D24:** alphabet C "Mashina" is installed and the
Russian menu renders
(`docs/qa/evidence/2026-10-13_1020_F2_language-screen-ru.png`). The order
was: font, then the language switch (ADR 004), then the Latin-with-Cyrillic-
bones variant (D22, level 2).
