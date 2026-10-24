# Gemini: prompt pack for tomorrow (P4, small daily quota, D116)

**For:** the CEO. **Author:** art-director, prepared on 2026-10-22 for use on the 23rd. **Status:** ready to paste.
Written in English (D129: repo docs are English; Spanish only in chat with the CEO); the prompts are inside code blocks. Not mirrored in `docs/ru/` (D34).
Images are never uploaded to GitHub (D77, `work/` is ignored).

> **In 30 seconds.** **27 images** are requested, ordered by priority (table below, with the running
> total: wherever the quota runs out, what is done up to that point is usable). One new chat per character. Each
> image carries its complete prompt (the common blocks are already pasted inside), the file name and what to
> attach. Weapons go to `work/art/reference/`; enemies to `work/art/reference/enemies/gemini/`.
> The PM then converts them with `tools/art/gemini_frames.py` and `tools/art/gemini_enemy.py`.

## 1. Summary

| Priority | Piece | Images | Running total |
|---|---|---|---|
| 1 (high) | TT-33 (D111) | **2** | 2 |
| 2 | SD_LegionGunner (SDLG) | **5** | 7 |
| 3 | SD_LibertyColossus (SDLC) | **7** | 14 |
| 4 | The Consortium (SDCN) | **7** | 21 |
| 5 | AKM | **2** (+1 optional: reload) | 23 |
| 6 | Highest-impact re-asks | **4** | 27 |

**Total: 27 images** (28 if the optional AKM reload is also requested). Natural cut points (everything before stays
usable): 2 (TT-33), 7 (+ gunner), 14 (+ Colossus), 21 (+ Consortium), 23 (+ AKM), 27 (+ re-asks).

What each piece unlocks:

| Piece | What goes into the game | Quantity notes |
|---|---|---|
| TT-33 | the starting weapon redone with bare hands (D111; today "to be redone", D61) | 2: rest and firing |
| SDLG | the gunner's 70 lumps (5 new sheets + the `turn` that already exists) | pain and gib are derived (the pipeline does it) |
| SDLC | the Colossus's 81 lumps (7 sheets) | the stomp sheet carries 2 rows (Q on top, R below) in 1 image |
| SDCN | the final boss's 95 lumps (7 sheets) | two sheets carry 2 rows (aim E/F, walk A/C) to save quota; R (glowing core) and pain H are derived |
| AKM | second weapon of slot 4 | 2 images; the reload (optional) is parked (D47) |
| Re-asks | the 4 most visible fixes of the 7 sheets already installed | see the end of section 9 for what was left out and why |

## 2. Practical note (read it before starting)

1. **One new chat per character** (8 chats: TT-33, gunner, Colossus, Consortium, AKM, hound, General, Legion).
   This way Gemini does not mix styles. Within each chat the images go **in the order they appear here**: the first
   fixes the character and the following ones are requested in the same chat.
2. **Continuity.** Prompts for second images begin with *"Using exactly the same character as in the previous
   image (same face, same colours, same equipment, same proportions, same scale)..."* and repeat a short description of the
   character. If it still drifts (different face, another helmet, other scale), **do not regenerate blindly**: in the same chat
   write *"Exactly the same character as in the first image of this chat: same face, same helmet, same colours, same
   scale. Redo only this pose."* and attach the first sheet again. Each regeneration spends quota: use it only if the
   character is someone else, or if the figures touch or run off the frame.
3. **Attaching images** (gunner, hound, General, Legion): Gemini's "+" menu, in the first message of the chat.
   The PM can do it through Chrome (`find` on the hidden file inputs and `file_upload`); by hand, drag the PNG.
4. **Count figures before saving.** One-row sheets must have **5** figures; two-row ones, 5 + 5; death
   sheets, 5. An extra or missing figure in a death sheet does not force a redo (the pipeline picks which ones it
   uses); what does force a redo is figures touching, something cut off by the edge, letters, or the character changing.
5. **Saving.** Download the image (or the canvas trick with `toDataURL`, 1024 px wide; Chrome saves to
   `E:\Downloads`) and move it with the **exact name** each image gives. The format does not matter (.png, .jpg, .jfif), but for
   enemies `.png` is preferable.
6. **If Gemini refuses or answers with text only.** First say *"Generate the image now"* (sometimes it answers without
   generating). If it refuses, **rephrase without words of violence or symbols** and retry in the same chat:

| If it refuses because of... | Change... |
|---|---|
| violence | remove `kill, dead, die, blood, wound, gore, shot, bullet`. Use `hit, struck, knocked out, flinching, falling`. In the death prompts keep "cartoonish like a 1993 video game". Never the word *blood* |
| shooting | `blasting a burst` -> `with a bright yellow-orange flash of light at the muzzle of his prop gun` |
| symbols | **never** ask for a swastika, hooked cross, "Nazi" or "SS". The armband is *"a red armband with a plain white empty square"*; if it still refuses, ask only for *"a red cloth band on the upper arm"* and note: the pipeline paints the symbol (D108) |
| real people | remove *"inspired by the Statue of Liberty monument"* and leave *"a giant robed statue holding a torch"* (it is a monument, not a person, but just in case); never name leaders or presidents |
| none of the above | new chat, attach the reference again, and ask for **only the pose** in one sentence, keeping the LAYOUT and BACKGROUND blocks |

7. **Quota.** According to `docs/HANDOFF.md` the counter reset on 22 Oct at 17:33; it is **not verified** that tomorrow
   it will do so at the same time. If the quota runs out midway through a piece, what is saved is kept: note the number of the last
   image done and resume from the next one.
8. **Quick check before saving each enemy sheet** (what cost re-asks in the seven already done):
   flat magenta background, **no shadow painted on the floor**; 10 px of margin around and under the boots (soles
   cut off by the edge were the most repeated re-ask); no figure touches its neighbour (muzzle flashes and smoke included);
   no letters or numbers; profile facing left; same scale in all five figures; the Reich armband,
   red with an **empty** white square. **Weapons:** bare hands, five fingers, right hand on the right, flat magenta
   background, the whole weapon, almost straight and centred; no gloves, enemies, status bar, text or cut-off weapon.
9. **Soviet flags do NOT go to the Gemini queue** (D119). The flags and banners of the maps are made with our procedural generators (D113), not with Gemini.

## 3. Common blocks (informational: **already pasted inside each prompt**)

So you can see where each phrase comes from. What worked with the seven sheets done: five views in a row, flat
magenta background, no symbols; death "cartoonish like a 1993 video game" without the word *blood*, with the last frame
"knocked out, lying completely flat and horizontal". (The original prompts of those sheets are not stored in the repo:
these blocks reconstruct them from `docs/HANDOFF.md`, the specs of `tools/art/gemini_enemy.py` and the resulting sheets;
NOT VERIFIED that the wording is literally the same.)

- **STYLE:** Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.
- **LAYOUT (5 vistas):** LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.
- **LAYOUT (2 filas):** LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.
- **BACKGROUND:** BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image.


## 4. Priority 1: TT-33 (D111): 2 images

New chat. Base prompt and `[WEAPON]` block from `docs/product/2026-10-20_0030_M2_gemini-weapons.md` §3-§4, and the firing prompt from its §5, as they are.
Afterwards the PM runs `tools/art/gemini_frames.py` (~50k tokens).

#### Image 1 of 27 (TT-33 1/2)
- **Chat:** Chat 1 (TT-33)
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_tt33_A.png`
- **Note:** rest; check the weapons checklist in point 2.8

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet TT-33 Tokarev pistol held in the RIGHT hand only, arm extended forward, the left hand not visible.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Image 2 of 27 (TT-33 2/2)
- **Chat:** Chat 1 (TT-33)
- **Attach:** nothing (same chat, right after A)
- **Save as:** `work/art/reference/gemini_tt33_B.png`
- **Note:** firing

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```


## 5. Priority 2: SD_LegionGunner (SDLG): 5 images

New chat. **First message: attach `gem_gunner_turn.png`** (the 5 standing views that already exist: Liberty Legion,
M1919 machine gun at the hip, two crossed bandoliers of bullets, US flag on the right shoulder) together with the
walkL prompt. The remaining sheets follow in the same chat. Frames the class requires
(`docs/engine/2026-10-22_P4_ep2-enemies.md` §4): A-D walk (walkL, walkR and the `turn` sheet that already exists), E aim
(aim, also the pause between bursts), F fire (fire, with muzzle flash at the hip), G pain (derived from `turn`), H-L
death (the death sheet, 5 figures), M-U gib (derived with pipeline effects). That is why only 5 sheets are missing.

**CEO playtest (D119):** *"el soldado que dispara ametralladora, que es todo de color ocre, su dibujo disparando parece que dispare lateral y no frontal"* (CEO: "the soldier who fires a machine gun, the one all ochre-coloured, his drawing while firing looks like he fires sideways and not frontally"). The **aim** and **fire** prompts now ask that **view 1 (front) fire directly at the camera** (barrel foreshortened toward the viewer, muzzle flash in front of the weapon, in the centre) and that the other views point where each one faces. Today's "all ochre" look is the provisional tinted sprite (D116) and will disappear with the Gemini art.

**Check before saving aim and fire (D119):** in figure 1 (front) the weapon points **at the camera** (the barrel is seen head-on, foreshortened, not from the side) and, in fire, the muzzle flash is **in front of the weapon, in the centre** of the figure, not off to one side; in 3 (profile) the barrel points **left**; in the back views the barrel is visible beyond its far side. If the front view fires sideways, redo only that sheet with *"View 1 must fire straight at the camera, barrel foreshortened toward the viewer, flash in front of the weapon."*

#### Image 3 of 27 (SDLG 1/5)
- **Chat:** Chat 2 (Legion gunner)
- **Attach:** work/art/reference/enemies/gemini/gem_gunner_turn.png (attach this sheet in the first message of this chat)
- **Save as:** `work/art/reference/enemies/gemini/gem_gunner_walkL.png`
- **Note:** first message of the chat: attach the sheet

```text
Using the attached reference sheet as the exact character reference (same figure in all five views, same equipment, same scale), make the WALK sheet, left-foot-forward stride.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the LEFT foot stepping forward and planted, the RIGHT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride, so that it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Image 4 of 27 (SDLG 2/5)
- **Chat:** Chat 2 (Legion gunner)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_gunner_walkR.png`

```text
Using exactly the same character as in the attached reference sheet and the previous sheet (same face, same colours, same equipment, same proportions, same scale), make the WALK sheet, right-foot-forward stride: the mirror of the previous walk sheet's legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the RIGHT foot stepping forward and planted, the LEFT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Image 5 of 27 (SDLG 3/5)
- **Chat:** Chat 2 (Legion gunner)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_gunner_aim.png`
- **Note:** view 1 (front): aims at the camera, barrel foreshortened toward the viewer (D119), see the check above

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: AIMING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: AIMING. He plants his feet wide and braces, the M1919 levelled at hip height held with both hands, the barrel always pointing in the direction each view faces. VIEW 1 (front): he aims DIRECTLY AT THE CAMERA, head-on, not sideways: the gun is seen end-on and foreshortened, the muzzle opening a dark circle pointing straight at the viewer, centred in front of his belly, both arms reaching toward the viewer, shoulders square to the camera. View 2 (three-quarter front): the barrel angles toward the camera and to the LEFT. View 3 (profile facing LEFT): the barrel points horizontally to the LEFT. View 4 (three-quarter back): the barrel is seen beyond his far side, pointing away from the camera. View 5 (straight back): the gun is hidden mostly behind his body, only the end of the barrel showing beyond his far side, pointing away from the camera. Face scowling, gun steady, NO muzzle flash.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Image 6 of 27 (SDLG 4/5)
- **Chat:** Chat 2 (Legion gunner)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_gunner_fire.png`
- **Note:** flashes touching the neighbouring figure were what complicated the General's fire sheet. **View 1 (front): fires at the camera** (D119), see the check above

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: FIRING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: FIRING. The same braced stance as the aiming sheet, but now the M1919 is blasting a burst: a bright yellow-orange muzzle flash with a small white-hot core at the muzzle, a few brass casings flying out, the gun and shoulders jerked back slightly by the recoil, mouth open shouting. DIRECTION OF FIRE: in VIEW 1 (front) he fires DIRECTLY AT THE CAMERA, NOT sideways: the M1919 is seen end-on and foreshortened with its barrel pointing straight at the viewer, shoulders square to the camera, and the muzzle flash is a star-shaped burst IN FRONT of the weapon, centred on the barrel in the middle of the figure (not off to one side), with the casings flying out to the sides. In view 2 (three-quarter front) the barrel and the flash angle toward the camera and to the LEFT; in view 3 (profile facing LEFT) the barrel and the flash point horizontally to the LEFT; in views 4 and 5 (back) the flash shows only beyond his far side, pointing away from the camera, never painted over his back. Keep the muzzle flash small and compact, well clear of the neighbouring figures (they must not touch).

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Image 7 of 27 (SDLG 5/5)
- **Chat:** Chat 2 (Legion gunner)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_gunner_death.png`
- **Note:** frame 5: lying completely flat (the pipeline uses it as the corpse, letter L)

```text
Same character as the attached reference sheet and the previous sheets, new sheet: a death animation strip, cartoonish like a 1993 video game (no realism, nothing graphic, no wounds).

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

FRAMES, left to right: 1) flinching and staggering back from a hit, mouth open, still holding the machine gun; 2) struck, head thrown back, arms flung out, the M1919 dropping from his hands; 3) falling backwards at about 45 degrees, the gun in the air; 4) nearly down, sitting on the ground with his back almost on the floor, knees up, small puffs of dust, the gun on the ground beside him; 5) knocked out, lying completely flat and horizontal on his back on the ground, glowing eyes dimmed, arms limp, the M1919 lying beside him.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that his head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


## 6. Priority 3: SD_LibertyColossus (SDLC) from scratch: 7 images

New chat, **no reference image** (concept in `docs/engine/2026-10-22_P4_ep2-enemies.md` §3: the perverted Statue of
Liberty: chrome, spiked crown, a torch that is a rocket launcher and flamethrower, the tablet as a shield).
Art decisions taken here, to be confirmed on seeing the first sheet:
- Torch in **her right** hand, tablet on her **left** arm (matches the shot, which comes out "20 to her
  right"). **Blank** tablet (Gemini writes text as soon as it can).
- US flag on the right shoulder, like the rest of the Legion (D12); no armband and no other political symbols.
- Proportion 6 tall by 5 wide (~120-130 px tall, no more than ~100 wide in game).
- Class frames: A-D walk (turn + walkL + walkR), E aim, F fire, G pain (derived), Q and R stomp (a single
  image with 2 rows), H-P death (5 figures; the pipeline completes the 9 letters, as with the General).
- **Playable minimum** if the quota is cut midway: `turn`, `fire` and `death` (the rest is filled in with the standing view).

#### Image 8 of 27 (SDLC 1/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (text, no reference)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_turn.png`
- **Note:** this sheet fixes the character and the scale; if it comes out badly, do not go on: redo it first (counts as reserve)

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE LIBERTY COLOSSUS, a giant boss monster of an alien invasion army: a colossal chrome robot-statue shaped like a stern robed woman monument, inspired by the Statue of Liberty monument (a statue, not a real person; a generic stern face with hollow glowing pale-blue eyes). Chrome plate-armour robes with heavy folds reaching her shins, raw pink flesh showing at the joints (elbows, wrists, neck, knees), heavy chrome feet. On her head a crown of seven long steel spikes. Her RIGHT arm (on the left of the image in the front view) is raised high holding a huge TORCH that is really a rocket launcher and flame projector: a thick steel tube with a flared nozzle on top, glowing orange inside. Her LEFT arm carries a large stone tablet as a shield in front of her body; the tablet is completely blank, no text, no numbers, no carving. A small US flag patch (stars and stripes) on the plate of her RIGHT shoulder. Stocky and heavy for a boss: about 6 units tall to 5 wide, including the raised torch.

POSE: standing idle and menacing, feet planted apart, the torch held high with the nozzle pointing up and glowing, the blank tablet held on the left forearm in front of the chest, chin lowered, hollow glowing eyes.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 9 of 27 (SDLC 2/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_walkL.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, LEFT foot forward and planted, RIGHT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. A clear, wide stride so it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 10 of 27 (SDLC 3/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_walkR.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, RIGHT foot forward and planted, LEFT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. The mirror of the previous walk sheet's legs.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 11 of 27 (SDLC 4/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_aim.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: AIMING. The torch arm swings down and the torch is levelled to point at the viewer: in the front view the torch nozzle points straight at the camera (foreshortened, glowing orange inside), in the profile it points horizontally to the LEFT, in the back views it points away beyond her far side. The tablet is raised in front of her body, the legs braced wide. NO flame and NO rocket yet, only the glow.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 12 of 27 (SDLC 5/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_fire.png`
- **Note:** same care with flashes and smoke as in the General's fire sheet

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING. The same braced pose as the aiming sheet, but the torch is now discharging: a rocket leaving the nozzle with a short bright orange-yellow burst of flame and a puff of smoke, the whole figure jolted back slightly. Keep the flame and smoke short and compact, well clear of the neighbouring figures (they must not touch). In the back views the blast shows only beyond her far side, never painted over her back.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 13 of 27 (SDLC 6/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_stomp.png`
- **Note:** a single image with 2 rows (Q on top, R below); if the second row comes out badly, ask for it alone (reserve)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, the STOMP wind-up: she raises her LEFT knee high with the foot lifted well off the ground, the body leaning back a little, the torch held high, the tablet braced in front. BOTTOM ROW, the STOMP impact: the same foot slammed down onto the ground, the body leaning forward, the torch still high, a compact ring of dust and small cracked rock around the feet (kept close to the feet, not spreading to the neighbouring figures).

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 14 of 27 (SDLC 7/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_colossus_death.png`
- **Note:** frame 5 = the wreck that stays (letter P)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (the Colossus is a machine-statue falling to pieces; nothing graphic). This is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) shuddering, the crown cracking, one spike snapping off, a few chrome sparks; 2) the torch slipping from her hand and falling, the tablet shield dropping from her other arm; 3) swaying and leaning back, knees buckling, pieces of chrome plate breaking away; 4) toppling backwards at about 45 degrees, mid-fall; 5) wrecked, lying completely flat and horizontal on her back, the crown broken, the torch and the tablet lying beside the body, thin wisps of smoke.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that her head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 7. Priority 4: The Consortium (SDCN): 7 images

New chat, **no reference image** (`docs/engine/2026-10-22_P4_ep3-final-boss.md` §2 and §5). The red armband of the
half-Reich carries an **empty white square**: Gemini refuses the swastika and the pipeline paints the symbol (D108). The symbol is not
requested and the SS are not named: the helmet is "a grey German-style steel helmet".

Frames of the class and where each one comes from:

| Frames | What it is | Source |
|---|---|---|
| Q, R | rooted, core off / lit | SDCN 1/7 (Q); R is derived by lightening the core's cobalt blue |
| B, D | phase 2 standing, and the reference scale | SDCN 2/7 |
| G | firing, flash and core ablaze | SDCN 3/7 |
| I-O | death: core, they scream, halves, collapse, burns, wreck | SDCN 4/7 (5 figures; M and N are derived with fire) |
| E, F | orb tell / rocket tell | SDCN 5/7 (2 rows: E on top, F below) |
| A, C (walk) | phase 2 walking | SDCN 6/7 (2 rows: A on top, C below) |
| S | the Breach (cables snapping) | SDCN 7/7 |
| H | pain, the two heads | derived (the standing view, tilted) |

The order within the piece is the priority order: **playable minimum** = images 1 to 4 (rooted, turn, fire, death);
missing frames are filled in with the standing view.

**Art decision (confirm it):** attack frames E, F, G and S serve both phases, and the boss has no legs in phase 1 and has
them in phase 2. To avoid drawing two sets, in those frames the lower part is **wrapped in a knot of cables and dark
smoke that hides the legs**; this way they work in both phases. If it is unconvincing on seeing it, there is a second batch with legs
(not included in the total). The two helmets with the generic faces reproduce no one (D12).

#### Image 15 of 27 (SDCN 1/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (text, no reference)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_rooted.png`
- **Note:** fixes the character (frame Q). R, the glowing core, is derived by lightening the cobalt blue: it is not requested

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE CONSORTIUM, the final boss of an alien invasion, twice the height of a heavy brute: one huge trunk made of TWO halves welded together down the middle, with TWO heads joined at the shoulders (one per half), generic stern faces, no likeness of any real person. Its LEFT half (on the viewer's RIGHT in the front view) is the German half: grey-green skin, a grey German-style steel helmet with a small eagle badge, a red armband on the upper arm with a plain white square field that is completely empty (no symbol, no letters), and the forearm replaced by a rack of rocket tubes. Its RIGHT half (on the viewer's LEFT in the front view) is the American half: chrome plate armour over pink flesh, an American M1 steel helmet, a small US flag patch on the shoulder, and the forearm is a big chrome energy-ball projector with a glowing nozzle. Between the two halves, in the chest, a ribbed open cavity glowing cobalt blue (portal energy): the glowing core.

POSE: PHASE 1, standing still, plugged into the floor.

LOWER BODY, ROOTED: no legs. The lower body is a heavy skirt of thick black cables and conduits that flare out and pool on the floor, with more thick cables running away from its back and skirt into the distance (in the front view they disappear behind it). The core glows a dim, steady cobalt blue. Both arms hang heavily at its sides, the weapon forearms pointing down, a heavy brooding stance.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 16 of 27 (SDCN 2/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_turn.png`
- **Note:** phase 2 reference sheet (frames B and D, and scale)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, but PHASE 2. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: PHASE 2, standing, the same upper body as the previous sheet.

LOWER BODY, FREE: the cables have been torn out: short stumps of black cable hang at its back and hips, sparking and trailing along the floor, and under the trunk there are two heavy mechanical legs of grey steel with hydraulic pistons and big flat armoured feet. The core burns brighter, a vivid cobalt glow. Standing, both arms hanging heavily, the weapon forearms pointing down.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 17 of 27 (SDCN 3/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_fire.png`
- **Note:** art decision: the lower part is hidden in a knot of cables and smoke so it works in phase 1 and 2 (see the section text)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING (frame G, shared by both phases). Both arms fire at once: the energy projector (its RIGHT forearm) discharges a bright cobalt-and-white ball of energy with a muzzle flare, the rocket tubes (its LEFT forearm) shoot a rocket with a burst of orange flame, and the chest core blazes bright white-blue; the whole body jolted back slightly, both mouths open roaring. Keep every flare and flame compact, well clear of the neighbouring figures (they must not touch). In the back views the blasts show only beyond the far side, never painted over its back.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 18 of 27 (SDCN 4/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_death.png`
- **Note:** 5 figures cover I J K L (M and N are derived with fire) and O (the wreck with the two helmets)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (nothing graphic). This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) the core cracking: bright cobalt-white cracks of light across the chest, both heads recoiling; 2) both heads screaming, both arms thrown out; 3) the two halves tearing apart along the welded seam, the chest splitting open with blinding cobalt light, plates and sparks flying; 4) collapsing and sagging down onto its knees, the halves separating, small flames starting; 5) the wreck: a low smoking ruined heap of grey-green and chrome plates and tangled cables, with the two steel helmets (one grey German-style, one American M1) lying side by side in the ash, a few small flames.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the boss falling backwards so that its heads end up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 19 of 27 (SDCN 5/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_aim.png`
- **Note:** a single image with 2 rows (E on top, F below)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW (the orb tell): its RIGHT arm, the chrome energy projector, is levelled forward at the viewer with the nozzle glowing, the chest core opening wide and glowing brighter, the other arm hanging; in the front view the nozzle points at the camera (foreshortened), in the profile it points horizontally to the LEFT. BOTTOM ROW (the rocket tell): its LEFT arm, the rack of rocket tubes, is raised and aimed at the viewer, the tubes loaded and ready, the other arm hanging. NO flames and NO shots yet.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 20 of 27 (SDCN 6/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_walk.png`
- **Note:** a single image with 2 rows (A on top = walkL, C below = walkR)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs and the torn cable stumps dragging.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, WALK with the LEFT mechanical leg forward and planted, the RIGHT leg behind with the heel lifted, cable stumps dragging on the floor, a heavy lumbering stride, both arms hanging. BOTTOM ROW, the mirrored stride: RIGHT leg forward and planted, LEFT leg behind with the heel lifted. A clear, wide stride in both rows.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 21 of 27 (SDCN 7/7)
- **Chat:** Chat 4 (Consortium)
- **Attach:** nothing (same conversation)
- **Save as:** `work/art/reference/enemies/gemini/gem_consortium_breach.png`
- **Note:** last of the piece: only seen for two seconds when the health bar splits; if missing, the pipeline uses the pain frame (H)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: THE BREACH (frame S): the thick black cables snapping off its back and hips and whipping outward with white sparks, the core flaring blinding white, both arms thrown wide, both heads roaring upward, the body arched back. Keep sparks and cable ends compact, clear of the neighbouring figures.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 8. Priority 5: AKM: 2 images (+1 optional)

New chat. The `[WEAPON]` block and the ready base prompt from `docs/engine/2026-10-22_P4_akm.md` §5, with the firing prompt
from `docs/product/2026-10-20_0030_M2_gemini-weapons.md` §5 unchanged, in the same chat. **Check**, in addition to the
weapons checklist in point 2.8: the **curved magazine** and the **oblique muzzle brake** (what distinguishes an AKM from the PPSh-41 at 320x200).

#### Image 22 of 27 (AKM 1/2)
- **Chat:** Chat 5 (AKM)
- **Attach:** nothing
- **Save as:** `work/art/reference/gemini_akm_A.png`
- **Note:** rest; check the CURVED magazine and the OBLIQUE muzzle brake

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet AKM assault rifle of the 1970s (7.62x39), seen from behind: a black phosphated steel receiver with a stamped dust cover, a reddish-brown laminated wooden handguard and pistol grip, a curved 30-round magazine in orange-brown bakelite, the gas tube above the barrel, and the slanted muzzle brake at the very end of the barrel. The LEFT hand holds the wooden handguard under the barrel; the RIGHT hand grips the pistol grip, the index finger along the trigger guard. The stock is tucked into the right shoulder, out of the image.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Image 23 of 27 (AKM 2/2)
- **Chat:** Chat 5 (AKM)
- **Attach:** nothing (same chat)
- **Save as:** `work/art/reference/gemini_akm_B.png`
- **Note:** firing

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```

#### OPTIONAL image (outside the total)
- **Chat:** Chat 5 (AKM)
- **Attach:** nothing (same chat, after A)
- **Save as:** `work/art/reference/gemini_akm_C.png`
- **Note:** OPTIONAL (reloads parked, D47): only if quota is left over; does not count in the total

```text
Using exactly the same image, make the reloading frame: the rifle is tilted a little to the right, the LEFT hand pulls the empty curved magazine down and out of the magazine well, a fresh curved magazine held against it. Same hands, same rifle, same magenta background, same pixel style.
```


## 9. Priority 6: highest-impact re-asks: 4 images

From the list in the sheet `docs/art/previews/2026-10-22_P4_enemies-gemini.html` (field "Pedir otra vez a Gemini", i.e. "Ask Gemini again", which comes from
`tools/art/gemini_enemy.py`), only the four most visible in play, in this order: the hound lunging, the
General's order with raised fist (plus pointing, in the same image), the Legion flag that changes shoulder and the Legion death
with the cut-off shotgun. The first two are new frames; the last two fix visible defects of the rank-and-file
soldier, who is the most frequent enemy. The new files do not overwrite the existing ones (`_v2`, `lunge`, `summon`, `turnB`).

#### Image 24 of 27 (Re-ask 1/4)
- **Chat:** Chat 6 (hound)
- **Attach:** work/art/reference/enemies/gemini/gem_hound_bite.png (character and grid reference)
- **Save as:** `work/art/reference/enemies/gemini/gem_hound_lunge.png`
- **Note:** hound re-ask: today the bite barely changes the pose; this gives the leap (frames F/G)

```text
Using the attached sheet as the exact reference (same Reich hound: grey skin, brown fur on the back, riveted steel helmet-collar and shoulder plates, spiked collar, yellow eyes; same pixel style, same scale, same 2-rows-by-4 grid layout and same view order), make a NEW sheet of the ATTACK LUNGE.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: the hound launching its attack: the front paws completely off the ground, the body stretched out in mid-leap, jaws wide open at full stretch, head thrust forward, the hind legs still pushing off. Views as in the reference grid (front, three-quarter front, profile facing LEFT, three-quarter back, back, repeated as in the reference).

LAYOUT: the same 2 rows by 4 figures as the reference, each figure fully inside the image with at least 10 px of empty background all round, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere, NO ground shadow under the dog, no gradient, no scenery, no text, no letters, no logo, no watermark. FORMAT: landscape image.
```

#### Image 25 of 27 (Re-ask 2/4)
- **Chat:** Chat 7 (General)
- **Attach:** work/art/reference/enemies/gemini/gem_general_turn.png (character reference)
- **Save as:** `work/art/reference/enemies/gemini/gem_general_summon.png`
- **Note:** General re-ask: frames Q and R of the 'Vorwarts!' order (today they are the idle pose and the aim)

```text
Using the attached sheet as the exact reference (same General: cream greatcoat with gold epaulettes, medals, monocle, peaked cap, black boots and belt, striped red-and-white cape, olive bazooka; same pixel style, same scale), make a NEW sheet with TWO rows of poses.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, GIVING AN ORDER: his LEFT fist raised high above his head, mouth open shouting a command, the bazooka resting on his RIGHT shoulder. BOTTOM ROW, POINTING: his LEFT arm extended straight forward with the index finger pointing at the viewer, the bazooka resting on his RIGHT shoulder. In every view the small US flag patch is on his RIGHT arm and the red armband with a plain white empty square field is on his LEFT arm (as in the three-quarter views of the reference), no symbol or letters in the armband.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Image 26 of 27 (Re-ask 3/4)
- **Chat:** Chat 8 (Legion trooper)
- **Attach:** work/art/reference/enemies/gemini/gem_legion_turn.png (character reference)
- **Save as:** `work/art/reference/enemies/gemini/gem_legion_turnB.png`
- **Note:** Legion re-ask: fixes the flag that changes shoulder when mirrored (views 2-4)

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same white helmet, same shotgun, same style and scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CORRECTION: the three-quarter front, the side profile and the three-quarter back views must all face LEFT, with the small US flag patch on his RIGHT shoulder sleeve in every view where that shoulder is visible. Keep the same standing pose, shotgun held across the chest, in all five views.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Image 27 of 27 (Re-ask 4/4)
- **Chat:** Chat 8 (Legion trooper)
- **Attach:** work/art/reference/enemies/gemini/gem_legion_death.png (reference; same chat 8, attach it again)
- **Save as:** `work/art/reference/enemies/gemini/gem_legion_death_v2.png`
- **Note:** Legion re-ask: the corpse's dropped shotgun comes out cut off by the edge; save it as _v2 so as not to overwrite the original

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same five death frames in the same order, same cartoonish 1993 video-game style, same scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) flinching and staggering back from a hit, still holding the shotgun; 2) struck, head thrown back, the shotgun dropping; 3) falling backwards at about 45 degrees; 4) nearly down, sitting with his back almost on the floor, small puffs of dust; 5) knocked out, lying completely flat and horizontal on his back, the shotgun lying beside him.

CORRECTION: the figures were cut off by the right and bottom edges (the dropped shotgun of the last frame). Draw every frame fully inside the image, with at least 12 px of empty background on every side and under the figures, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


### Re-asks that are left out (and why)

| Re-ask from the sheet | Why it is not in tomorrow's quota |
|---|---|
| Stormtrooper: the 6 sheets on a taller canvas (cut-off soles) | 6 images; the pipeline already adds a dark 5 px sole (barely visible in game) |
| Panzermensch: the 6 sheets taller, armbands without letters, launch toward the left | 6 or more images; the armband is already patched (`patch`) and the sole is added |
| Stormtrooper aim2/fire2 and charge | optional ("only if the CEO wants it") |
| Hound walkL/walkR more distinct, pain | optional; the lunge is the visible change |
| Doughboy: attack views 3-4 without the duplicated glow | the pipeline already erases the glow (`erase`), acceptable |
| General: front and back with the flag on the right arm (5 sheets) | 5 images for a defect of ~3x2 px in game |
| General: fire with more space; death at the same scale | already solved by the pipeline (`split_x`, scale x1.39) |

If quota is left over, the next one by impact would be the **Panzermensch** (`fire` sheet with armbands without letters) and then the
**General: death at scale**.

## 10. Quota control

Execution order = image number (1 to 27). Natural cut points: 2, 7, 14, 21, 23, 27. Within a
piece, the gunner needs all 5 sheets to replace its provisional art; the Colossus and the Consortium need at minimum
`turn`, `fire` and `death` (the Consortium, in addition, `rooted`).

Possible saving if trimming is needed without losing frames: ask for the gunner's and the Colossus's `walkL`+`walkR` in 2 rows
(2 images fewer, with the risk that the second row loses consistency).

No image has been generated and Gemini has not been opened while preparing this pack, no other file has been touched and no
commit has been made. Everything said about how Gemini will respond is **not verified** until it is used; the Colossus prompts
and the Consortium prompts (new characters, no reference) are the ones at highest risk of refusal or drift.

## 11. LAST, before publishing v1.2: epic start screen (TITLEPIC) (D126)

CEO's order (2026-10-23): *"Antes de publicar, nueva pantalla de inicio con Gemini! Que sea epica como la del Doom, con nuestro heroe y la bandera roja asesinando los enemigos nazis y yankis"* (CEO: "Before publishing, new start screen with Gemini! Make it epic like Doom's, with our hero and the red flag killing the Nazi and Yankee enemies"). New chat. **Attach** the hero sheet if it exists in `work/art/reference/` (the status-bar sergeant, the 42 Gemini faces, D89) so that it is the same man; if not, text only. The `TITLEPIC` is 320x200 and the `M_DOOM` logo (200x64) is painted on top at x=60, y=0 (MOD-SPEC, menu contract): **the top third stays free** (sky) for the logo; the pipeline composes the logo and reduces to the palette. Gemini does not draw swastikas or accept "Nazi": red armband with an empty white square (the pipeline paints the symbol as with the enemies, D108). No words about blood.

- **Save as:** `work/art/reference/gemini_titlepic_A.png` (and `_B` if a second version is requested)

```text
Epic painted cover art for a 1990s PC first-person shooter, in the style of the classic 1993 DOOM box art and title screen: dramatic heroic low-angle composition, bold painted look with visible brush strokes, high contrast, fiery orange-and-red light. SCENE: a lone Soviet Spetsnaz sergeant of the 1970s, rugged unshaven face, olive-drab Soviet uniform with a striped telnyashka undershirt at the collar, a fur-lined ushanka hat or a steel helmet, stands on top of a heap of defeated alien invaders, raising a huge RED BANNER on a pole in his left hand (a plain bright red flag with a small golden hammer and sickle and a golden star in its upper corner) while he fires a Soviet PPSh-41 submachine gun with his right hand at the enemies charging him. THE ENEMIES, cartoonish 1990s game monsters, no realism: grey-green alien soldiers in grey German-style steel helmets with red armbands that have a plain empty white square, and chrome-skinned alien soldiers in white American M1 helmets with small US flag patches, some knocked down at his feet, others charging from both sides with their weapons, one giant chrome statue-robot monster with a torch looming in the smoky background. SETTING: a burning Soviet city at night, red sky, sparks and smoke, a red star on a distant tower. LAYOUT: the hero and the flag fill the centre and the lower two thirds of the image; the TOP THIRD of the image is open dark red sky with smoke only, empty, so a game logo can be placed there later. No text, no letters, no numbers, no logo, no watermark, no symbols other than those described, nothing graphic or gory. FORMAT: landscape 16:10.
```

Check before saving: the hero reads as Soviet (uniform, red flag with hammer and sickle), the enemies read as the two sides (German helmets with a red armband and chrome ones with an M1 helmet), the top third is clear, no text. Afterwards: the art-director reduces to 320x200, composes the `M_DOOM` logo and paints the armbands' symbol (D108; **the CEO sees the swastika before it is applied**, D105), preview to the CEO, and only then is it installed at `assets/graphics/shell/TITLEPIC.png`.
