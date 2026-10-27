# Gemini: prompts for the RGD-5 grenade (V3, A4; D116, D120)

**For:** the CEO. **Author:** mod-engineer, prepared on 2026-10-23 for V3. **Status:** ready to paste.
Same format as `docs/product/2026-10-23_P4_gemini-prompt-pack.md`, written in English (D129: repo docs are
English; Spanish only in chat with the CEO); the prompts are inside code blocks. Not mirrored in `docs/ru/` (D34).
Images are never uploaded to GitHub (D77, `work/` is ignored); they are style references, not copies.

> **In 30 seconds.** **5 images needed** (4 of the hand in first person and the loose grenade) and **2
> optional** (the pouch of two and the crate). A new chat for the RGD-5 alone. Everything goes to `work/art/reference/`.
> Until they arrive, the grenade wears provisional sprites: in the hand, the ice axe; on the floor, the
> health bonus's canteen tinted metal grey (D116; `docs/engine/2026-10-23_V3_rgd5.md` §5).

## 1. Summary

| Priority | Image | File | What it gives | Final sprite |
|---|---|---|---|---|
| 1 | at rest | `gemini_rgd5_A.png` | the hand with the grenade, ready | `SDRG` A |
| 2 | pull the pin and draw the arm back | `gemini_rgd5_B.png` | the ring out, the arm back | `SDRG` B |
| 3 | throw | `gemini_rgd5_C.png` | the arm forward, the grenade leaving | `SDRG` C |
| 4 | follow-through | `gemini_rgd5_D.png` | the arm extended, the hand empty | `SDRG` D |
| 5 | grenade in the world | `gemini_rgd5_pickup.png` | the loose grenade (21021) **and** the grenade in flight | `SDRJ` A, `SDRN` A |
| 6 (optional) | pouch of two | `gemini_rgd5_pouch.png` | the weapon on the floor (21009) | `SDRQ` A |
| 7 (optional) | crate | `gemini_rgd5_crate.png` | the crate of four (21022) | `SDRZ` A |

Natural cut-off points: **4** (the whole hand; the floor stays provisional), **5** (everything needed), 7 (everything).
Without 6, the pouch uses image 5 a little larger; without 7, the crate stays the tinted PG-7V one.

## 2. Practical note

1. **A new chat** for the RGD-5; the images **in this order**. Images 2-4 say "Using exactly the same hand...":
   the first one fixes the hand, the sleeve and the grenade.
2. **What tells an RGD-5 apart** (check before saving): a **smooth egg-shaped** body, olive green, one thin
   seam around the middle, **no grid**; on top the steel fuse with the **curved lever** running down one side
   and the **round ring**. If it comes out ribbed (that is the F-1 "pineapple"), repeat with: *"smooth egg
   shape, NOT the ribbed F-1 pineapple grenade"*.
3. **Weapon check** (the pack's, point 2.8): bare hand, five fingers, the right hand on the right, flat magenta
   background, olive gymnastyorka sleeve from the bottom edge; no gloves, enemies, status bar, text, and nothing
   cut off but the forearm.
4. **If Gemini refuses** (grenade = weapon): drop *"explosive"*, *"fragmentation"* and *"throw at"*; keep *"a Soviet
   RGD-5 prop grenade, as in a 1990s video game"* and *"tossing it forward"*. Never enemies or people in the image.
5. **Saving:** the table's exact name, in `work/art/reference/`. The format does not matter (.png preferred).
6. **Afterwards** (not the CEO's): `art-director` adds the RGD-5 entry to `tools/art/gemini_frames.py` (~30k) and crops
   images 5-7 (~25k); `mod-engineer` does the renaming (one `sed` per file, already written in each
   header).

## 3. First person: 4 images

#### Image 1 of 7 (RGD-5 1/4): at rest
- **Chat:** RGD-5
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_A.png`
- **Note:** the grenade in the right hand, low, on the right; the ring visible

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet RGD-5 hand grenade of the 1970s held in the RIGHT hand: a smooth egg-shaped body in olive-green painted steel with one thin seam around its middle (smooth, NOT the ribbed F-1 pineapple grenade), a dull grey steel fuse screwed into the top, its curved steel lever (spoon) running down the side of the body under the fingers, and a round steel pull-ring with a split pin on the fuse. The right hand closes round the body and holds the lever down; the ring points to the left, towards the centre of the image. The left hand is not visible.

HANDS: a BARE human hand, no glove, natural adult proportions, five fingers, visible knuckles, light skin with warm shading. The forearm rises from the very BOTTOM edge of the image, right of centre, in an olive-drab Soviet WWII cotton tunic sleeve (gymnastyorka, khaki-olive, plain cuff). The arm never leaves the image sideways.

VIEW: seen from behind and slightly above, as the player's own hand at rest (ready pose, NOT throwing): the grenade held low, a little right of centre, at about chest height.

COMPOSITION: hand and grenade fill only the lower 40% of the image, right of centre. The upper half is empty background. Nothing is cut off except the forearm at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Image 2 of 7 (RGD-5 2/4): pull the pin and draw the arm back
- **Chat:** RGD-5 (the same chat, after image 1)
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_B.png`
- **Note:** two hands: the left one, low on the left, with the ring and the pin; the right one, high and back

```text
Using exactly the same hand, sleeve, grenade and pixel style as in the previous image, make the "pin pulled, arm drawn back" frame: the RIGHT arm is raised and drawn back, the grenade held high at the right edge of the image near the top of the lower half, the steel lever still pressed down by the fingers. The LEFT hand, BARE, five fingers, olive-drab gymnastyorka sleeve rising from the BOTTOM edge left of centre, holds the round steel pull-ring with its split pin just pulled out of the fuse. Both forearms rise from the bottom edge and never leave the image sideways. Hands and grenade fill only the lower 60% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

#### Image 3 of 7 (RGD-5 3/4): throw
- **Chat:** RGD-5 (the same chat)
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_C.png`
- **Note:** the arm going forward, the hand opening; the grenade just leaving, in the centre, smaller

```text
Using exactly the same right hand, sleeve, grenade and pixel style as before, make the "release" frame: the RIGHT arm swings forward and up towards the centre of the image, the hand opening, and the grenade has just left the fingers, a little smaller because it is moving away, slightly above the hand near the centre of the image. The steel lever (spoon) is flying off the grenade. The left hand is not visible. The forearm rises from the BOTTOM edge, right of centre, and never leaves the image sideways. Hand and grenade fill only the lower 55% of the image. Same perfectly flat solid magenta (#FF00FF) background, no motion blur, no speed lines, no shadow, no text, no enemies, no HUD.
```

#### Image 4 of 7 (RGD-5 4/4): the throw's follow-through
- **Chat:** RGD-5 (the same chat)
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_D.png`
- **Note:** the hand empty, open, the arm extended; there must be NO grenade

```text
Using exactly the same right hand, sleeve and pixel style as before, make the "follow-through" frame: the RIGHT arm is extended forward and slightly down after the throw, the hand open and EMPTY (no grenade anywhere in the image), fingers relaxed, palm facing down, a little right of centre. The left hand is not visible. The forearm rises from the BOTTOM edge and never leaves the image sideways. Hand and arm fill only the lower 40% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

## 4. In the world: 1 image needed and 2 optional

Loose objects on the floor, seen a little from above, like the mod's other items. The same chat (it keeps the
grenade) or a new one if the chat is full; in that case attach `gemini_rgd5_A.png`.

#### Image 5 of 7: the loose grenade (and in flight)
- **Chat:** RGD-5
- **Attach:** nothing (or `gemini_rgd5_A.png` in a new chat)
- **Save as:** `work/art/reference/gemini_rgd5_pickup.png`
- **Note:** two sprites come from this image: the grenade on the floor (`SDRJ`) and the one in flight (`SDRN`)

```text
Create ONE small item sprite for a 1993-1996 PC first-person shooter, in the same hand-pixelled style: 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, 4 to 6 flat shade steps per material, a thin dark outline.

OBJECT: one single Soviet RGD-5 hand grenade lying on its side on the floor: the smooth egg-shaped olive-green steel body with one thin seam around the middle (NOT the ribbed F-1 pineapple), the grey steel fuse at one end with its curved lever along the body and the round steel pull-ring. Seen from the side and slightly above (about 30 degrees), the fuse pointing to the right.

COMPOSITION: the grenade alone, centred, filling about 60% of the image width, nothing cut off, at least 10 px of empty background on every side.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No floor, no painted or cast shadow, no gradient, no scenery, no hands, no text, no letters, no numbers, no logo, no watermark. FORMAT: square image.
```

#### Image 6 of 7 (OPTIONAL): the pouch of two grenades
- **Chat:** RGD-5
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_pouch.png`
- **Note:** the weapon on the floor; without it, the pouch uses image 5 a little larger

```text
Using the same RGD-5 grenade and pixel style as before, create ONE item sprite: a Soviet Army khaki canvas grenade pouch for two grenades, with a flap and a small leather strap, lying flat on the floor, the flap open and the tops of two olive-green RGD-5 grenades (grey steel fuses, round pull-rings) showing. Seen from the side and slightly above (about 30 degrees). Centred, filling about 70% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no letters, no logo. FORMAT: square image.
```

#### Image 7 of 7 (OPTIONAL): the crate
- **Chat:** RGD-5
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_rgd5_crate.png`
- **Note:** no lettering: a real crate's Soviet markings carry text, here only a stripe

```text
Using the same pixel style as before, create ONE item sprite: a small Soviet Army wooden ammunition crate painted olive-green, with rope handles at both ends, steel corner brackets and a plain yellow stencilled stripe on the side (NO letters, NO numbers, NO symbols), the lid propped open showing four olive-green RGD-5 grenades lying in a row. Seen from the front and slightly above (about 30 degrees). Centred, filling about 80% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no logo. FORMAT: wide landscape image.
```

## 5. Sounds (not Gemini's; for `sound-designer`)

Today the grenade plays sounds already installed, under names of its own (`SNDINFO`, "Slot 8"). Five are
missing: `SDRGPIN` (ring and pin), `SDRGTHR` (the arm and the lever springing off), `SDRGBNC` (a steel egg on
concrete), `SDRGEXP` (a dry burst with shrapnel, smaller than the PG-7V) and `SDRGPKP` (canvas pouch, two grenades).
Detail in `docs/engine/2026-10-23_V3_rgd5.md` §4.

Gemini was not opened and no image was generated while preparing these prompts. Everything said about how it will
respond is **NOT VERIFIED** until it is used; frames 2 and 3 (two hands, motion) carry the highest risk of drift.
