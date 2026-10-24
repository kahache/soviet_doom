# Fooocus: hand references for the 5 weapons still on Freedoom's hands

**Author:** art-director · **Date:** 2026-10-14 23:56 · **Milestone:** M2 (arsenal, phase F4)
**For:** the CEO, with the document open on the PC next to Fooocus (http://127.0.0.1:7865).
**Language:** Written in English (D129: repo docs are English; Spanish only in chat with the CEO). The prompts and negative prompts are in English because SDXL understands English better. The document is not copied to `docs/ru/` (D34).

> **In 30 seconds.** There are five weapons: IZh, PPSh-41, RPG-7, ROKS-3 and the hand-held Katyusha. With **6 mandatory batches** of Method A, or with **6 input images** of Method B, we cover all five: several weapons share a grip.
> **Try Method B first** (§4): you feed Fooocus one of our frames, with the Doom composition already right, and Fooocus turns it into a photo. If it does not work, use **Method A** (§5), which is text only.
> **Order:** calibration with the TT-33 (5 min) → PPSh → IZh → RPG-7 → (ROKS-3 only if the PM asks) → Katyusha.

---

## 1. The workflow, always the same

1. Set up Fooocus once with the **base settings** (§3).
2. Paste the prompt and negative prompt from the relevant block and press **Generate**. You get **4 images**.
3. Look at each one against its **checklist** (✅ = keep, ❌ = discard).
4. Save **the best one, or the 2 best**, in `work/art/reference/` with the block's **exact name** (if you save two, add `2`: `ppsh_ready_rh2.png`).
5. If the hand comes out **mirrored** (a left hand entering from the left when we asked for the right hand from the right), **it still works**: save it with the suffix `_mirrored` (`ppsh_ready_rh_mirrored.png`) and we flip it ourselves (D73). What **does not work** is a crossed arm: a right hand entering from the left, or a left hand entering from the right.
6. If none of the 4 is good, generate another 4 (the seed is random). If after **3 batches** it still does not come out, stop and tell the PM, with the best of the bad ones: that way we adjust the prompt and you do not waste more time.
7. Tell the PM in one line: *"PPSh ready: ppsh_ready_rh.png, ppsh_ready_lh.png"*.

**What matters and what does not.** What matters is the hand, the wrist, the sleeve, the grip pose and the light. **The weapon in the photo does not matter**: we draw it ourselves and put it under the fingers with `tools/art/hand_ref.py`. A plain, contrasting background (sky, snow) makes the cut-out come out clean.

---

## 2. Which weapons, which poses and how many references

The **firing and recoil frames need no reference**: we derive them from the rest frame by rotating and shifting it and adding the muzzle flash. We only need photos of the distinct poses.

| Weapon (slot) | Doom class and sprite | States our ZScript uses | Hands on screen | Poses that need a photo | Images to save |
|---|---|---|---|---|---|
| **IZh-58**, double-barrelled shotgun (3) | `SD_Izh` replaces Shotgun, `SHTG` | A rest; B, C recoil; **D open for reloading** (D → C → B → A) | left under the fore-end; right when reloading | **rest** (left) and **open, reloading** (both) | 2 (+1 optional) |
| **PPSh-41** (4), the mod's icon | `SD_Ppsh` replaces Chaingun, `CHGG` | A, B alternate when firing | **both**: left in front, right on the stock and the trigger | **rest**, one photo per hand | 2 |
| **RPG-7** (5) | `SD_Rpg7` replaces RocketLauncher, `MISG` | A rest; B fire | right on the grip; the left in front is optional | **rest** (right) | 1 (+1 optional) |
| **ROKS-3**, flamethrower (6) | `SD_Roks3` replaces PlasmaRifle, `PLSG` | A fire; B cool-down | both, same as the PPSh | **none new**: uses the PPSh hands | 0 (+2 optional) |
| **Hand-held Katyusha** (7, secret, D68) | `SD_HandKatyusha` replaces BFG9000, `BFGG` | A charge 20 tics; B fire | **both**: left on the front bar, right on the grip | **rest**: new left; the right is the RPG's | 1 (+1 optional) |

**Grips that are reused** (each is generated only once):
- **Right, grip with the index finger on the trigger** (`rpg7_ready_rh`): also serves the Katyusha.
- **Right, on the throat of a wooden stock** (`ppsh_ready_rh`): also serves the ROKS-3 and, if needed, the IZh.
- **Left, holding a horizontal stick from below** (`ppsh_ready_lh`): also serves the ROKS-3. For the IZh the angle changes enough that it needs its own.

How Doom solves it, for comparison: in Freedoom, `CHGG`, `MISG` and `PLSG` **show no hands** (the weapon covers everything); `SHTG` B-D show the right hand pumping the slide, and `BFGG` only shows a few fingers poking out. We show more hand, as the approved TT-33 does (D63).

---

## 3. Fooocus base settings (both methods)

Start with `Z:\Fooocus\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\run_realistic.bat` and **change what is in bold** relative to the preset:

| Where | Setting | Value |
|---|---|---|
| Settings → Performance | Performance | **Quality** (60 steps; it is what you used today) |
| Settings → Aspect Ratios | aspect ratio | **1152×896** (the preset ships 896×1152 vertical: change it) |
| Settings | Image Number | **4** |
| Settings | Random (seed) | ✔ checked |
| Styles | **uncheck** | **Fooocus V2** and **Fooocus Photograph** |
| Styles | **check** (type "iphone" in *Search Styles*) | **Photo Iphone Photographic** + **Fooocus Negative** |
| Models | Base Model | `realisticStockPhoto_v20.safetensors` (already installed) |
| Models | Refiner | None |
| Models | LoRA 1 `SDXL_FILM_PHOTOGRAPHY_STYLE_V1` | **None** (or weight 0): it adds grain and a vintage tone, and that dirties the cut-out |
| Advanced | Guidance Scale | **4** (the preset ships 3; at 4 it obeys a long prompt better; if the skin comes out plastic or oversaturated, go back to 3) |
| Advanced | Image Sharpness | 2 (default) |

**Why these changes (I saw it in your log from today, `Fooocus/outputs/2026-10-14/log.html`).** You asked for *"plain flat light grey seamless studio background"* and mountains came out. The log shows the cause: **Fooocus V2** added to the prompt *"scenic, epic, surreal, futuristic, magical atmosphere…"* and **Fooocus Photograph** added *"cinematic… hbo dark moody, grainy, vignette, vintage, found footage"*. Both push toward landscape and vignetting. **Photo Iphone Photographic** only adds *"large depth of field, deep depth of field, highly detailed"*: a sharp photo, with no bokeh or vignette. **Fooocus Negative** adds a list of hand malformations to the negative. The installed checkpoints are `juggernautXL_v8Rundiffusion`, `realisticStockPhoto_v20` and `animaPencilXL_v500` (the last one is anime; do not use it).

**The important part goes at the start of the prompt.** SDXL pays more attention to the first words, which is why every prompt starts with the hand, the side of the screen and the grip. Fooocus accepts weights of the form `(right hand:1.3)`.

---

## 4. Method B (TRY FIRST): from Doom frame to photo (CEO's idea)

### 4.1 Why it should be faster, and its risks
- **Advantage:** the input frame already has Doom's **composition, point of view, scale and on-screen position** (the D57 scale and the placement of our sketches). We save ourselves from guessing the camera, which is exactly what failed with references 2 and 3 of the ice axe (the mitten seen from behind and the grip the wrong way round).
- **Risk 1, it comes out pixelated:** SDXL may copy the pixel steps. That is why the inputs already come **smoothed** (bicubic plus a third-of-a-pixel blur), and `pixelated, blocky` is in the negative.
- **Risk 2, it invents a sixth finger:** our sketches have thick, blocky fingers, and the edge control may turn one block into two fingers. It is fixed by lowering the PyraCanny **Weight** and with the negative (table in §4.6).
- **Risk 3, it inherits colours on the Vary route:** the 2D sketches have a brown glove and a sleeve with telnyashka stripes. PyraCanny only looks at edges and inherits no colours; Vary does inherit them. That is why the main recipe is PyraCanny.
- **The first time you use PyraCanny, CPDS or ImagePrompt:** Fooocus **downloads** the control model from its own repository (`huggingface.co/lllyasviel/misc`). Today `models/controlnet` only holds `fooocus_ip_negative`. Downloads: `control-lora-canny-rank128.safetensors` (PyraCanny), `fooocus_xl_cpds_128.safetensors` (CPDS) and, for ImagePrompt, `clip_vision_vit_h.safetensors` plus `ip-adapter-plus_sdxl_vit-h.bin`. Sizes **NOT VERIFIED**: about 0.4 GB per control model and about 2-3 GB for the ImagePrompt pair. It is your machine: you decide. **Vary (Strong) downloads nothing.**

### 4.2 Licence rule (binding)
As input we use **only** sprites from **Freedoom (BSD-3)** or **our own frames**. **NEVER Doom sprites from id Software** (`DOOM.WAD`, `DOOM2.WAD`): they are commercial and cannot be redistributed, and a photo derived from them cannot either. id's Doom is only valid as a style reference, by looking at it. All the inputs in §4.3 come from `iwads/freedoom2.wad` or from `work/art/`.

### 4.3 Input images already prepared: `work/art/reference/doom_inputs/`
All measure 1152×896 (Fooocus's aspect ratio), on a **plain pale blue sky**. `_index.png` shows them all together. `_close` = cropped around the weapon and the hands, with larger hands, which is **the one to use first**. `_full` = the whole 320×200 Doom screen, for when you want the full composition.

| Weapon / pose | Main input (ours) | Origin | Freedoom alternative (BSD-3) |
|---|---|---|---|
| **Calibration** | `tt33_ready_ours_close.png` | `weapons_fd/tt33/SDTTA0`: the approved TT-33 (D63), with recoloured Freedoom hands | — |
| PPSh rest | `ppsh_ready_ours_close.png` | 2D sketch `SDPPA0` | `ppsh_ready_fd-CHGGA0_*` (no hands) |
| IZh rest | `izh_ready_ours_close.png` | 2D sketch `SDIZA0` | `izh_ready_fd-SHTGA0_*` (almost no hands) |
| IZh open | `izh_open_ours_close.png` | 2D sketch `SDIZD0` | `izh_open_fd-SHTGD0_*` (right hand on a slide) |
| RPG-7 rest | `rpg7_ready_ours_close.png` | 2D sketch `SDRLA0` | `rpg7_ready_fd-MISGA0_*` (no hands) |
| ROKS-3 rest | `roks3_ready_ours_close.png` | 2D sketch `SDRKA0` | `roks3_ready_fd-PLSGA0_*` (no hands) |
| Katyusha rest | `katyusha_ready_ours_close.png` | 2D sketch `SDHKA0` | `katyusha_ready_fd-BFGGA0_*` (fingers poke out) |
| Hand consistency | `ref_hand_rh.png` | your `hand grabbing mirrored.png`, flipped to a right hand (the original is untouched) | — |

The Freedoom versions show almost no hands, so they **only serve for the cartoon variant or as a composition**; for the hands always use ours. The inputs are regenerated with `work/art/reference/doom_inputs/make_doom_inputs.py`.

### 4.4 Recipe B1, the main one: Image Prompt with PyraCanny
1. Check **Input Image** (below the prompt) and open the **Image Prompt** tab.
2. Check **Advanced** (below the 4 image boxes) to see *Type*, *Stop At* and *Weight*.
3. **Box 1:** drag in the weapon's `_close` input. Type **PyraCanny**, **Stop At 0.5**, **Weight 0.8**.
4. **Box 2** (optional, keeps volumes and light): **the same image**. Type **CPDS**, **Stop At 0.35**, **Weight 0.5**.
5. **Box 3** (optional, so the hand is the same across all weapons): `ref_hand_rh.png`, or your best calibration photo (§4.7) once you have it. Type **ImagePrompt**, **Stop At 0.5**, **Weight 0.35**. With more weight the ice axe and the mountains sneak in.
6. Base settings from §3, the prompt from §4.7 and **Generate** (4 images).

### 4.5 Recipe B2, if B1 does not respect the hand position: Vary (Strong) plus PyraCanny
1. **Input Image** → **Upscale or Variation** tab → drag in the same input → choose **Vary (Strong)** (that is a denoise of 0.85).
2. **Advanced** → check **Developer Debug Mode** → **Control** tab → check **Mixing Image Prompt and Vary/Upscale**.
3. **Image Prompt** tab, box 1: the same input, **PyraCanny, Stop At 0.5, Weight 0.7**.
4. Same prompt. If it copies the sketch too much (blocks, brown glove): in *Developer Debug Mode*, raise **Forced Overwrite of Denoising Strength of "Vary"** to **0.9**. If it invents something else, lower it to **0.75**.

### 4.6 If something goes wrong (both B methods)

| Symptom | Change |
|---|---|
| It comes out pixelated or with steps | PyraCanny **Stop At 0.35-0.4** and **Weight 0.6** (less time tied to the edges, more freedom to paint skin), remove CPDS. In *Developer Debug Mode → Control → Canny*: Low **100**, High **200** (ignores small edges) |
| It does not respect the composition (hand in another place, weapon rotated) | PyraCanny **Stop At 0.6-0.7** and **Weight 1.0**, and add CPDS. More *Stop At* = more faithful to the edges, **but also to the blocks**: raise it only if needed |
| Sixth finger or fused fingers | **Weight 0.6**, regenerate; the negative already asks for it. If it persists, discard and move to B2 or to Method A |
| Brown glove or striped sleeve (inherited from the sketch) | Happens in B2: go back to B1. In the prompt, `(bare skin:1.3)` and `(plain olive sleeve:1.2)` |
| Landscape in the background | Check that **Fooocus V2** and **Fooocus Photograph** are unchecked; put `(plain pale blue sky background:1.3)` |
| It comes out mirrored | Fine: save it with `_mirrored` |

### 4.7 Method B prompts (photo and cartoon)

**Photo variant settings:** those of §3 (realisticStockPhoto, styles **Photo Iphone Photographic + Fooocus Negative**).
**Cartoon variant settings** (it may pixelate more cleanly; send us whatever comes out): Base Model **`juggernautXL_v8Rundiffusion`**. Styles: check only **Cel Shaded Art**, and **uncheck Fooocus Negative** (its negative includes *"cartoon, anime, drawing, graphic"* and would cancel the style). If it comes out too flat, add **SAI Comic Book**. Guidance 4.

**Common B negative, photo** (paste it as is):
```
pixelated, pixel art, blocky, jagged edges, low resolution, video game, 3d render, cgi, cartoon, drawing, painting, illustration, plastic skin, toy, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, extra arms, crossed arms, gloves, striped sleeve, wristwatch, ring, tattoo, fisheye, distorted perspective, motion blur, bokeh, depth of field, vignette, film grain, face, person, people, landscape, mountains, trees, buildings, text, watermark, logo, signature
```
**Common B negative, cartoon:**
```
photo, photorealistic, pixelated, pixel art, blocky, jagged edges, noisy, blurry, gradient banding, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, crossed arms, gloves, striped sleeve, wristwatch, face, person, landscape, background details, text, watermark, logo, signature
```

For the cartoon variant, replace the start of the photo prompt *"first-person view photograph, …"* with **"cel shaded comic illustration, clean bold black outlines, flat colors with three shades per material, first-person view, …"** and remove *"realistic photograph, 28mm lens"* from the end.

| # | Input (box 1 and 2) | Photo prompt (English) | Save as |
|---|---|---|---|
| B0 calibration | `tt33_ready_ours_close.png` | see below | `tt33_ready_fromdoom_photo.png` / `_cartoon.png` |
| B1 PPSh | `ppsh_ready_ours_close.png` | see below | `ppsh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B2 IZh rest | `izh_ready_ours_close.png` | see below | `izh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B3 IZh open | `izh_open_ours_close.png` | see below | `izh_open_fromdoom_photo.png` / `_cartoon.png` |
| B4 RPG-7 | `rpg7_ready_ours_close.png` | see below | `rpg7_ready_fromdoom_photo.png` / `_cartoon.png` |
| B5 ROKS-3 | `roks3_ready_ours_close.png` | see below | `roks3_ready_fromdoom_photo.png` / `_cartoon.png` |
| B6 Katyusha | `katyusha_ready_ours_close.png` | see below | `katyusha_ready_fromdoom_photo.png` / `_cartoon.png` |

**B0, calibration with the TT-33 (do it first: 1 batch, about 5 min).** We already know how it should look, so it tells us whether Method B works. If it comes out well, this photo becomes the **model hand** for box 3 on the rest of the weapons.
```
first-person view photograph, seen through the eyes of the shooter, (two bare hands:1.2) holding a black steel pistol straight ahead at the center of the frame with a two-handed grip, the right hand wrapped around the grip and the left hand cupping it from below, the thumbs side by side along the left of the frame, knuckles toward the camera, exactly five fingers on each hand, lightly tanned skin, olive drab cotton sleeves of a WWII Soviet army tunic at the bottom edge, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B1, PPSh-41**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage wooden submachine gun with a round drum magazine, the gun runs diagonally from the bottom right toward the center of the frame, the left hand comes in from the bottom left and holds the front of the gun from below, the right hand at the bottom right grips the wooden stock with the index finger on the trigger, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B2, IZh at rest**
```
first-person view photograph, seen through the eyes of a hunter, a side-by-side double barrel shotgun with a wooden stock held low, the two steel barrels point forward toward the center of the frame, (bare left hand:1.2) coming in from the bottom left holds the wooden fore-end from below, palm up, fingers curled over the far side, thumb along the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B3, IZh open (reloading)**
```
first-person view photograph looking down at a broken-open side-by-side double barrel shotgun held at waist height, the barrels tipped down on the hinge and the two empty chambers facing up, (bare right hand:1.2) pushing two red paper shotgun shells into the chambers with thumb and index finger, the left hand under the barrels holding the gun open, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain flat white snow on the ground as background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B4, RPG-7**
```
first-person view photograph, seen through the eyes of a soldier, a long thick olive green launcher tube rests on the right shoulder and points forward, the tube runs diagonally from the bottom right toward the center of the frame, (bare right hand:1.2) at the bottom right grips the launcher with a firm fist, knuckles toward the camera, thumb wrapped around the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B5, ROKS-3**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage rifle-shaped flamethrower gun with a wooden stock and a long thin steel nozzle, the gun runs diagonally from the bottom right toward the left of the frame, the left hand comes in from the bottom left and holds the barrel from below, the right hand at the bottom right grips the wooden stock, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B6, hand-held Katyusha**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) carrying a heavy olive green steel rack of six rocket rails on the right shoulder, the left hand comes in from the bottom left and grips a horizontal steel bar at the front of the rack with an overhand grip, knuckles up, the right hand at the bottom right grips a vertical steel handle under the rack, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**Method B checklist** (in addition to the general one in §6): the hand is **in the same place as in the input**. It is real skin, with no blocks. The sleeve is plain olive, **with no stripes**. ❌ Discard if the fingers follow the sketch's block outline (sausages), if a glove comes out, or if the weapon covers the fingers instead of the fingers sitting on top of the weapon.

---

## 5. Method A (FALLBACK): text only

Base settings from §3, no Input Image. Optional, so the hand is the same across all weapons: **Input Image → Image Prompt**, box 1 with `doom_inputs/ref_hand_rh.png` (or your best calibration photo), **Type ImagePrompt, Stop At 0.5, Weight 0.35**. Requires the download in §4.1.

**Why stand-in objects.** If we name "Soviet submachine gun", SDXL draws war scenes, soldiers and landscapes. If we give it an **object of the same shape and size** (a hunting-shotgun stock, a broomstick, a tube), the hand grips the same way and the background stays clean. The only thing that matters is the grip.

**Common negative A, for a RIGHT hand** (paste it whole):
```
left hand, two left hands, arm entering from the left, crossed arms, extra fingers, six fingers, four fingers, fused fingers, missing fingers, long fingers, sausage fingers, claw, twisted wrist, broken wrist, extra hands, third hand, extra arms, floating hand, disconnected hand, cropped hand, cut-off fingers, out of frame, gloves, glove, wristwatch, bracelet, ring, tattoo, nail polish, striped sleeve, rolled-up sleeve, fisheye, distorted perspective, wide angle distortion, motion blur, bokeh, depth of field, vignette, film grain, dark, low light, face, person, people, head, legs, landscape, mountains, trees, buildings, clouds, busy background, text, watermark, logo, signature, label, cartoon, drawing, painting, illustration, 3d render, cgi, plastic skin
```
**Common negative A, for a LEFT hand:** the same, replacing the first 3 entries with `right hand, two right hands, arm entering from the right`.

---

### A1. PPSh-41, right hand on the stock. `ppsh_ready_rh.png` (MANDATORY; also serves the ROKS-3 and the IZh)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's right hand:1.3) and forearm entering the frame from the bottom right corner, the right hand grips the narrow curved wooden wrist of an old hunting rifle stock, the stock runs diagonally from the bottom right corner up toward the center of the frame, firm trigger grip: the back of the hand and the four knuckles face the camera, thumb wrapped over the top of the wood, middle, ring and little fingers curled around the underside, index finger lying straight along the side of the wood, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand fills the lower right quarter of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Back of the hand and the 4 knuckles facing the camera · thumb over the wood · index finger extended apart · the olive sleeve leaves through the bottom edge · plain sky.
❌ Palm toward the camera · the index finger closed like a fist · wood in front of the fingers · vertical stock.

### A2. PPSh-41, left hand in front. `ppsh_ready_lh.png` (MANDATORY; also serves the ROKS-3)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand supports a thick round wooden broom handle from below, the handle is held level and points forward and slightly up toward the center of the frame like the front grip of a rifle, palm up under the wood, four fingers curled up around the far side so the fingertips show on top of the wood, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand in the lower left third of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ The wood passes **over the palm**, with the fingertips poking out on top · thumb on the near side · forearm from the bottom left.
❌ The hand gripping from above like a walking stick · the wood in front of the fingers (it was the failure of ref. 3) · the stick pointing at the camera.

### A3. IZh, left hand under the barrels. `izh_ready_lh.png` (MANDATORY)
```
first-person point of view photograph, seen through the eyes of a hunter, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand holds the wooden fore-end of a side-by-side double barrel hunting shotgun from below, the two steel barrels point straight ahead to the center of the frame, the gun is low in the frame at the bottom center, palm up under the wood, four fingers curled around the far side, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ The barrels go **straight to the centre** · the hand under the fore-end, with the fingers on the far side.
❌ Pump-action shotgun · the hand on the trigger · the barrels crossing the screen from side to side.
*Optional:* `izh_ready_rh.png`, only if the PM asks: it is A1 with *"a side-by-side double barrel hunting shotgun"* instead of *"an old hunting rifle"* and the barrels straight to the centre.

### A4. IZh open, reloading. `izh_open_rh.png` (MANDATORY; both hands appear, and that is normal)
Negative: the common right-hand one **without** `third hand`, `extra hands` or `arm entering from the left` (the left does appear).
```
first-person point of view photograph looking down at waist height, seen through the eyes of a hunter, a broken-open side-by-side double barrel hunting shotgun held in the center of the frame, the barrels tipped down on the hinge and the two empty chambers facing up toward the camera, (the right hand:1.3) coming in from the bottom right pushes two red paper shotgun shells into the chambers between thumb and index finger, the left hand coming in from the bottom left holds the barrels from below to keep the gun open, exactly five fingers on each hand, natural proportions, bare skin, lightly tanned, short clean nails, both forearms covered by plain olive drab cotton sleeves of a WWII Soviet army tunic, the sleeves leave the picture at the bottom edge, plain flat white snow on the ground as the only background, soft daylight from the upper left, sharp focus on the hands, 28mm lens, natural perspective, realistic photograph
```
✅ Shotgun clearly **open** (bent hinge) · shells between the right thumb and index finger · both sleeves leave through the bottom · plain snow background.
❌ Closed shotgun · more than two hands · floating shells · a hand entering from above.

### A5. RPG-7, right hand on the grip. `rpg7_ready_rh.png` (MANDATORY; also serves the Katyusha)
```
first-person point of view photograph, seen through the eyes of the holder, a long thick olive green metal pipe rests on the right shoulder and points forward, the pipe runs diagonally from the bottom right corner up toward the center of the frame, (a single adult man's right hand:1.3) grips a black vertical pistol grip under the pipe at the lower right of the frame, the back of the hand and the knuckles face the camera, thumb wrapped around the left side of the grip, index finger curled on a trigger, the other three fingers wrapped around the grip, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Closed fist around a **vertical** grip · knuckles toward the camera · tube above the hand · the sleeve leaves through the bottom right.
❌ The hand gripping the tube from above · a drill or a tool instead of the grip · the tube pointing at the camera.
*Optional:* `rpg7_ready_lh.png`, the left hand in front: A2 changing *"a thick round wooden broom handle"* to *"the underside of a thick olive green metal pipe"*.

### A6. Hand-held Katyusha, left hand on the bar. `katyusha_ready_lh.png` (MANDATORY; the right is the one from A5)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand grips a thick horizontal steel pipe at chest height with an overhand grip, the pipe crosses the frame from the left edge to the center, knuckles up and toward the camera, four fingers wrapped over and around the pipe, thumb under the pipe, wrist slightly bent down, the hand left of center, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ **Overhand** grip (back of the hand up, knuckles visible) · horizontal tube · forearm from the bottom left.
❌ Palm up · the hand hanging from a gym bar with the arm stretched upward · a vertical bar.

### A7. ROKS-3 (OPTIONAL: only if the PM says the PPSh hands do not fit)
`roks3_ready_rh.png` / `roks3_ready_lh.png`: A1 and A2 with these changes: *"held low at hip height, pointing slightly down toward the center of the frame"* instead of *"diagonally … up toward the center"*, and in A2 *"a long thin steel pipe"* instead of *"a thick round wooden broom handle"*.

---

## 6. General checklist (all images)

**✅ Keep if:**
- [ ] It is a **real hand** with **5 fingers**, no fused fingers and with visible knuckles.
- [ ] It is the **requested hand** entering from **its own side** (or the exact mirror → `_mirrored`).
- [ ] The **forearm and sleeve leave through the bottom edge** of the image (if the sleeve ends inside the frame, the cut is visible on screen; it was the failure of ref. 3).
- [ ] The **sleeve is olive, plain, cotton**, with the cuff at the wrist: no glove, no stripes, no watch.
- [ ] The **fingers sit on top of the object** (the object passes *inside* the fist, not in front of the fingers).
- [ ] **Plain, light background** (sky or snow) around the whole hand.
- [ ] Soft light from the upper left, no hard shadows on the fingers.
- [ ] Sharp hand, no bokeh, no grain and no vignette.

**❌ Discard if:** a mitten comes out (the hand seen from behind, ref. 2) · the grip is the wrong way round (the hand seen from below, ref. 3) · there is a crossed arm · there is a third hand · fisheye bends the forearm · there is a person or a face · there is text or a watermark.

---

## 7. Notes for the PM (the CEO need not read them)

- **Hypothesis, NOT VERIFIED:** that Method B gives usable hands. It depends on PyraCanny reading our 2D sketches as hands and not as blocks. The B0 calibration with the approved TT-33 decides it in a single batch.
- **Hypothesis:** that the single-hand photos (Method A) combine well in `hand_ref.py` for two-handed weapons. If `hand_ref.py` only accepts one hand per photo, A4 (IZh open, two hands) may need a manual crop.
- If the hand comes out mirrored, the light we ask for from the upper left ends up at the upper right after flipping. The tones in `hand_ref.py` absorb it in part; if it shows, the CEO should say so.
- **Licences:** the inputs are from Freedoom (BSD-3) or ours. The CEO's photos are his own SDXL generations. Each needs its row in `docs/art/LICENSES.md` if a cell derived from it is approved, as with the ice axe.
- The inputs live in `work/art/reference/doom_inputs/` (gitignored, like all of `work/`). They are generated by `make_doom_inputs.py`, in that same folder: it reads the IWAD, composes on 320×200 with the `grAb` offsets, crops and scales with bicubic plus blur.
