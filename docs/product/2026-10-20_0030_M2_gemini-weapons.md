# Gemini: first-person weapon images (D79)

**For:** the CEO. **Author:** PM, 2026-10-20 00:30. **Milestone:** M2 (arsenal).
Written in English (D129: repo docs are English; Spanish only in chat with the CEO); the prompts are in English.
Not mirrored in `docs/ru/` (D34).

> **In 30 seconds.** For each weapon, 2 images in Gemini (at rest and
> firing; the IZh also reloading). Save them in
> `C:\Users\littl\Desktop\Claude\soviet_doom\work\art\reference\` with the
> exact name from the table and tell me. I turn them into game frames with
> `tools/art/gemini_frames.py` (~50k tokens per weapon). These images are
> never uploaded to GitHub (D77).

## 1. Can I do it from the browser?

**Not today.** For me to use Gemini with your account I need **Claude in
Chrome** (Claude's extension for your Chrome, where you are already signed in
to Google). Right now no Chrome is connected. In the app's built-in browser I
cannot sign in for you: typing passwords is forbidden for me.

**To enable it (5 minutes, once):**
1. Open Chrome with the Google account you use Gemini with.
2. Search for **"Claude"** in the Chrome Web Store (Anthropic's official
   extension) and install it.
3. Open it from the puzzle icon, sign in with your Claude account
   and leave Chrome open.
4. In the next session tell me "use Chrome": I open gemini.google.com in a
   new tab, paste the prompts and ask your permission once to **download
   the images** (downloading files always needs your explicit OK).

## 2. How to do it by hand (what works now)

1. Open https://gemini.google.com with your account (if the university one
   does not let you generate images, use a personal Gmail account).
2. **A new chat per weapon** (so it does not mix in styles from earlier weapons).
3. Paste the **base prompt** (§3) with the weapon's block (§4) in the place
   indicated. Generate frame A (rest).
4. If it comes out well, **in the same chat** paste the firing prompt (§5).
5. Download each image (the image's download button) and **rename it**
   as the table says. The format does not matter (.png, .jpg or .jfif all work).
6. Move them to `C:\Users\littl\Desktop\Claude\soviet_doom\work\art\reference\`.
7. Tell me: "IZh ready".

Check before saving: ✅ bare hands, five fingers, right hand on the
right; ✅ plain magenta background with nothing else; ✅ whole weapon, almost straight and
centred; ❌ gloves, enemies, status bar, text, cropped weapon.

## 3. Base prompt (change only the `[WEAPON]` block)

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

[WEAPON]

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

## 4. Blocks per weapon and file names

| Weapon | `[WEAPON]` block | Files |
|---|---|---|
| **IZh-58** (shotgun) | `WEAPON: a Soviet IZh-58 side-by-side double-barrelled shotgun, closed, blued steel barrels and a dark walnut stock. The LEFT hand holds the fore-end under the barrels; the RIGHT hand grips the wrist of the stock behind the triggers.` | `gemini_izh_A.png` (rest), `gemini_izh_B.png` (firing), `gemini_izh_C.png` (reload, §5) |
| **RPG-7** | `WEAPON: a Soviet RPG-7 rocket launcher resting on the right shoulder, the olive PG-7V grenade loaded at the front, the wooden heat guard in the middle. The RIGHT hand on the pistol grip, the LEFT hand on the front grip.` | `gemini_rpg7_A.png`, `gemini_rpg7_B.png` |
| **ROKS-3** (flamethrower) | `WEAPON: a Soviet ROKS-3 backpack flamethrower gun, shaped like a short rifle with a wooden stock and a nozzle with a small igniter at the muzzle, a reinforced hose running from the gun down out of the bottom of the image. The LEFT hand under the barrel, the RIGHT hand on the stock and trigger.` | `gemini_roks3_A.png`, `gemini_roks3_B.png` (firing with a jet of fire) |
| **Hand-held Katyusha** | `WEAPON: a hand-held Soviet "Katyusha" launcher: a cradle of four short steel rocket rails with four rockets loaded, a wooden shoulder stock and a pistol grip. The RIGHT hand on the grip, the LEFT hand under the rails.` | `gemini_katyusha_A.png`, `gemini_katyusha_B.png` |
| **Ice axe** | `WEAPON: a Soviet mountaineering ice axe with a long straight ash-wood shaft and a steel head (pick and adze), held upright in the RIGHT hand only, the head at the top; the left hand is not visible.` | `gemini_iceaxe_A.png` (rest), `gemini_iceaxe_B.png` (strike, §5) |
| **TT-33** (optional, already installed) | `WEAPON: a Soviet TT-33 Tokarev pistol held in the RIGHT hand only, arm extended forward, the left hand not visible.` | `gemini_tt33_A.png`, `gemini_tt33_B.png` |

## 5. Second images (in the same chat)

**Firing** (all firearms):
```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```
(For the ROKS-3 change the last sentence: `...and a long jet of orange flame shoots from the nozzle.`)

**IZh reload:**
```text
Using exactly the same image, make the reloading frame: the shotgun is broken open, the barrels tipped down, the right hand pushing two red shotgun shells into the chambers. Same hands, same background, same pixel style.
```

**Ice axe strike:**
```text
Using exactly the same image, make the strike frame: the right arm swings the ice axe down and forward, the pick pointing at the centre of the image, slight motion lines. Same hand, same background, same pixel style.
```
