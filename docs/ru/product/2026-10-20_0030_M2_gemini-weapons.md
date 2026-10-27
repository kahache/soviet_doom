# Gemini: изображения оружия от первого лица (D79)

Каноническая версия: `docs/product/2026-10-20_0030_M2_gemini-weapons.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

**Для:** CEO. **Автор:** PM, 2026-10-20 00:30. **Веха:** M2 (арсенал).
Написано по-английски (D129: документы репозитория на английском; испанский
только в чате с CEO); промпты на английском.
В `docs/ru/` не зеркалируется (D34).

> **За 30 секунд.** Для каждого оружия — по 2 изображения в Gemini (в покое и
> при стрельбе; у ИЖ ещё и при перезарядке). Сохраните их в
> `C:\Users\littl\Desktop\Claude\soviet_doom\work\art\reference\` с точным
> именем из таблицы и сообщите мне. Я превращаю их в игровые кадры с помощью
> `tools/art/gemini_frames.py` (~50k токенов на оружие). Эти изображения
> никогда не загружаются на GitHub (D77).

## 1. Могу ли я сделать это из браузера?

**Сегодня нет.** Чтобы я мог пользоваться Gemini с вашим аккаунтом, мне нужен
**Claude in Chrome** (расширение Claude для вашего Chrome, где вы уже вошли в
Google). Сейчас ни один Chrome не подключён. Во встроенном браузере приложения
я не могу войти за вас: вводить пароли мне запрещено.

**Как включить (5 минут, один раз):**
1. Откройте Chrome с тем аккаунтом Google, с которым вы пользуетесь Gemini.
2. Найдите **«Claude»** в Chrome Web Store (официальное расширение Anthropic)
   и установите его.
3. Откройте его через значок пазла, войдите в свой аккаунт Claude и оставьте
   Chrome открытым.
4. В следующей сессии скажите мне «use Chrome»: я открою gemini.google.com в
   новой вкладке, вставлю промпты и один раз спрошу вашего разрешения на
   **скачивание изображений** (для скачивания файлов всегда нужно ваше явное
   OK).

## 2. Как сделать вручную (что работает сейчас)

1. Откройте https://gemini.google.com со своим аккаунтом (если университетский
   не позволяет генерировать изображения, используйте личный Gmail).
2. **Новый чат на каждое оружие** (чтобы не подмешивались стили предыдущих
   видов оружия).
3. Вставьте **базовый промпт** (§3) с блоком оружия (§4) в указанном месте.
   Сгенерируйте кадр A (покой).
4. Если вышло хорошо, **в том же чате** вставьте промпт стрельбы (§5).
5. Скачайте каждое изображение (кнопкой скачивания изображения) и
   **переименуйте** его, как сказано в таблице. Формат не важен (.png, .jpg
   или .jfif подойдут).
6. Переместите их в `C:\Users\littl\Desktop\Claude\soviet_doom\work\art\reference\`.
7. Скажите мне: «IZh ready».

Проверьте перед сохранением: ✅ голые руки, пять пальцев, правая рука справа;
✅ однотонный пурпурный фон без чего-либо ещё; ✅ оружие целиком, почти прямо
и по центру; ❌ перчатки, враги, строка состояния, текст, обрезанное оружие.

## 3. Базовый промпт (меняйте только блок `[WEAPON]`)

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

[WEAPON]

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

## 4. Блоки по видам оружия и имена файлов

| Оружие | Блок `[WEAPON]` | Файлы |
|---|---|---|
| **ИЖ-58** (дробовик) | `WEAPON: a Soviet IZh-58 side-by-side double-barrelled shotgun, closed, blued steel barrels and a dark walnut stock. The LEFT hand holds the fore-end under the barrels; the RIGHT hand grips the wrist of the stock behind the triggers.` | `gemini_izh_A.png` (покой), `gemini_izh_B.png` (стрельба), `gemini_izh_C.png` (перезарядка, §5) |
| **РПГ-7** | `WEAPON: a Soviet RPG-7 rocket launcher resting on the right shoulder, the olive PG-7V grenade loaded at the front, the wooden heat guard in the middle. The RIGHT hand on the pistol grip, the LEFT hand on the front grip.` | `gemini_rpg7_A.png`, `gemini_rpg7_B.png` |
| **РОКС-3** (огнемёт) | `WEAPON: a Soviet ROKS-3 backpack flamethrower gun, shaped like a short rifle with a wooden stock and a nozzle with a small igniter at the muzzle, a reinforced hose running from the gun down out of the bottom of the image. The LEFT hand under the barrel, the RIGHT hand on the stock and trigger.` | `gemini_roks3_A.png`, `gemini_roks3_B.png` (стрельба со струёй огня) |
| **Ручная «Катюша»** | `WEAPON: a hand-held Soviet "Katyusha" launcher: a cradle of four short steel rocket rails with four rockets loaded, a wooden shoulder stock and a pistol grip. The RIGHT hand on the grip, the LEFT hand under the rails.` | `gemini_katyusha_A.png`, `gemini_katyusha_B.png` |
| **Ледоруб** | `WEAPON: a Soviet mountaineering ice axe with a long straight ash-wood shaft and a steel head (pick and adze), held upright in the RIGHT hand only, the head at the top; the left hand is not visible.` | `gemini_iceaxe_A.png` (покой), `gemini_iceaxe_B.png` (удар, §5) |
| **ТТ-33** (необязательно, уже установлен) | `WEAPON: a Soviet TT-33 Tokarev pistol held in the RIGHT hand only, arm extended forward, the left hand not visible.` | `gemini_tt33_A.png`, `gemini_tt33_B.png` |

## 5. Вторые изображения (в том же чате)

**Стрельба** (всё огнестрельное):
```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```
(Для РОКС-3 замените последнее предложение: `...and a long jet of orange flame shoots from the nozzle.`)

**Перезарядка ИЖ:**
```text
Using exactly the same image, make the reloading frame: the shotgun is broken open, the barrels tipped down, the right hand pushing two red shotgun shells into the chambers. Same hands, same background, same pixel style.
```

**Удар ледорубом:**
```text
Using exactly the same image, make the strike frame: the right arm swings the ice axe down and forward, the pick pointing at the centre of the image, slight motion lines. Same hand, same background, same pixel style.
```
