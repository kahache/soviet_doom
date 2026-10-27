# Gemini: промпты для гранаты РГД-5 (V3, A4; D116, D120)

Каноническая версия: `docs/product/2026-10-23_V3_gemini-rgd5-prompts.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

**Для:** CEO. **Автор:** mod-engineer, подготовлено 2026-10-23 для V3. **Статус:** готово к вставке.
Тот же формат, что и в `docs/product/2026-10-23_P4_gemini-prompt-pack.md`, написано по-английски (D129: документы
репозитория на английском; испанский только в чате с CEO); промпты находятся внутри блоков кода. В `docs/ru/` не
зеркалируется (D34).
Изображения никогда не загружаются на GitHub (D77, `work/` игнорируется); это стилевые референсы, а не копии.

> **За 30 секунд.** Нужно **5 изображений** (4 руки от первого лица и россыпью лежащая граната) и **2
> необязательных** (подсумок на две и ящик). Новый чат только для РГД-5. Всё сохраняется в `work/art/reference/`.
> Пока они не пришли, граната носит временные спрайты: в руке — ледоруб; на полу — фляга бонуса здоровья,
> тонированная в металлический серый (D116; `docs/engine/2026-10-23_V3_rgd5.md` §5).

## 1. Сводка

| Приоритет | Изображение | Файл | Что даёт | Итоговый спрайт |
|---|---|---|---|---|
| 1 | в покое | `gemini_rgd5_A.png` | рука с гранатой, готова | `SDRG` A |
| 2 | выдернуть чеку и отвести руку назад | `gemini_rgd5_B.png` | кольцо выдернуто, рука отведена | `SDRG` B |
| 3 | бросок | `gemini_rgd5_C.png` | рука вперёд, граната вылетает | `SDRG` C |
| 4 | движение по инерции | `gemini_rgd5_D.png` | рука вытянута, ладонь пуста | `SDRG` D |
| 5 | граната в мире | `gemini_rgd5_pickup.png` | лежащая граната (21021) **и** граната в полёте | `SDRJ` A, `SDRN` A |
| 6 (необязательно) | подсумок на две | `gemini_rgd5_pouch.png` | оружие на полу (21009) | `SDRQ` A |
| 7 (необязательно) | ящик | `gemini_rgd5_crate.png` | ящик на четыре (21022) | `SDRZ` A |

Естественные точки остановки: **4** (вся рука; пол остаётся временным), **5** (всё необходимое), 7 (всё).
Без 6 подсумок использует изображение 5, чуть увеличенное; без 7 ящик остаётся тонированным ящиком ПГ-7В.

## 2. Практическая заметка

1. **Новый чат** для РГД-5; изображения **в этом порядке**. В изображениях 2-4 сказано «Using exactly the same hand...»:
   первое фиксирует руку, рукав и гранату.
2. **Чем РГД-5 отличается от других** (проверьте перед сохранением): **гладкий яйцевидный** корпус, оливково-зелёный,
   один тонкий шов посередине, **без насечки**; сверху стальной запал с **изогнутым рычагом**, идущим вниз по
   одному боку, и **круглым кольцом**. Если вышло рифлёным (это «ананас» Ф-1), повторите с:
   *"smooth egg shape, NOT the ribbed F-1 pineapple grenade"*.
3. **Проверка оружия** (из пакета, пункт 2.8): голая рука, пять пальцев, правая рука справа, однотонный
   пурпурный фон, рукав оливковой гимнастёрки от нижнего края; без перчаток, врагов, строки состояния, текста и
   ничего обрезанного, кроме предплечья.
4. **Если Gemini отказывается** (граната = оружие): уберите *"explosive"*, *"fragmentation"* и *"throw at"*; оставьте
   *"a Soviet RGD-5 prop grenade, as in a 1990s video game"* и *"tossing it forward"*. Никогда не врагов и не людей на
   изображении.
5. **Сохранение:** точное имя из таблицы, в `work/art/reference/`. Формат не важен (предпочтительно .png).
6. **После этого** (не дело CEO): `art-director` добавляет запись РГД-5 в `tools/art/gemini_frames.py` (~30k) и
   обрезает изображения 5-7 (~25k); `mod-engineer` занимается переименованием (один `sed` на файл, уже написан в
   каждом заголовке).

## 3. От первого лица: 4 изображения

#### Изображение 1 из 7 (РГД-5 1/4): в покое
- **Чат:** RGD-5
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_A.png`
- **Заметка:** граната в правой руке, низко, справа; кольцо видно

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet RGD-5 hand grenade of the 1970s held in the RIGHT hand: a smooth egg-shaped body in olive-green painted steel with one thin seam around its middle (smooth, NOT the ribbed F-1 pineapple grenade), a dull grey steel fuse screwed into the top, its curved steel lever (spoon) running down the side of the body under the fingers, and a round steel pull-ring with a split pin on the fuse. The right hand closes round the body and holds the lever down; the ring points to the left, towards the centre of the image. The left hand is not visible.

HANDS: a BARE human hand, no glove, natural adult proportions, five fingers, visible knuckles, light skin with warm shading. The forearm rises from the very BOTTOM edge of the image, right of centre, in an olive-drab Soviet WWII cotton tunic sleeve (gymnastyorka, khaki-olive, plain cuff). The arm never leaves the image sideways.

VIEW: seen from behind and slightly above, as the player's own hand at rest (ready pose, NOT throwing): the grenade held low, a little right of centre, at about chest height.

COMPOSITION: hand and grenade fill only the lower 40% of the image, right of centre. The upper half is empty background. Nothing is cut off except the forearm at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Изображение 2 из 7 (РГД-5 2/4): выдернуть чеку и отвести руку назад
- **Чат:** RGD-5 (тот же чат, после изображения 1)
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_B.png`
- **Заметка:** две руки: левая, низко слева, с кольцом и чекой; правая, высоко и назад

```text
Using exactly the same hand, sleeve, grenade and pixel style as in the previous image, make the "pin pulled, arm drawn back" frame: the RIGHT arm is raised and drawn back, the grenade held high at the right edge of the image near the top of the lower half, the steel lever still pressed down by the fingers. The LEFT hand, BARE, five fingers, olive-drab gymnastyorka sleeve rising from the BOTTOM edge left of centre, holds the round steel pull-ring with its split pin just pulled out of the fuse. Both forearms rise from the bottom edge and never leave the image sideways. Hands and grenade fill only the lower 60% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

#### Изображение 3 из 7 (РГД-5 3/4): бросок
- **Чат:** RGD-5 (тот же чат)
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_C.png`
- **Заметка:** рука идёт вперёд, ладонь раскрывается; граната только что вылетела, в центре, меньше

```text
Using exactly the same right hand, sleeve, grenade and pixel style as before, make the "release" frame: the RIGHT arm swings forward and up towards the centre of the image, the hand opening, and the grenade has just left the fingers, a little smaller because it is moving away, slightly above the hand near the centre of the image. The steel lever (spoon) is flying off the grenade. The left hand is not visible. The forearm rises from the BOTTOM edge, right of centre, and never leaves the image sideways. Hand and grenade fill only the lower 55% of the image. Same perfectly flat solid magenta (#FF00FF) background, no motion blur, no speed lines, no shadow, no text, no enemies, no HUD.
```

#### Изображение 4 из 7 (РГД-5 4/4): движение руки после броска
- **Чат:** RGD-5 (тот же чат)
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_D.png`
- **Заметка:** ладонь пуста и раскрыта, рука вытянута; гранаты быть НЕ должно

```text
Using exactly the same right hand, sleeve and pixel style as before, make the "follow-through" frame: the RIGHT arm is extended forward and slightly down after the throw, the hand open and EMPTY (no grenade anywhere in the image), fingers relaxed, palm facing down, a little right of centre. The left hand is not visible. The forearm rises from the BOTTOM edge and never leaves the image sideways. Hand and arm fill only the lower 40% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

## 4. В мире: 1 изображение необходимо и 2 необязательных

Отдельные предметы на полу, вид немного сверху, как у остальных предметов мода. Тот же чат (он помнит гранату)
или новый, если чат заполнен; в этом случае приложите `gemini_rgd5_A.png`.

#### Изображение 5 из 7: лежащая граната (и в полёте)
- **Чат:** RGD-5
- **Приложить:** ничего (или `gemini_rgd5_A.png` в новом чате)
- **Сохранить как:** `work/art/reference/gemini_rgd5_pickup.png`
- **Заметка:** из этого изображения получаются два спрайта: граната на полу (`SDRJ`) и в полёте (`SDRN`)

```text
Create ONE small item sprite for a 1993-1996 PC first-person shooter, in the same hand-pixelled style: 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, 4 to 6 flat shade steps per material, a thin dark outline.

OBJECT: one single Soviet RGD-5 hand grenade lying on its side on the floor: the smooth egg-shaped olive-green steel body with one thin seam around the middle (NOT the ribbed F-1 pineapple), the grey steel fuse at one end with its curved lever along the body and the round steel pull-ring. Seen from the side and slightly above (about 30 degrees), the fuse pointing to the right.

COMPOSITION: the grenade alone, centred, filling about 60% of the image width, nothing cut off, at least 10 px of empty background on every side.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No floor, no painted or cast shadow, no gradient, no scenery, no hands, no text, no letters, no numbers, no logo, no watermark. FORMAT: square image.
```

#### Изображение 6 из 7 (НЕОБЯЗАТЕЛЬНО): подсумок на две гранаты
- **Чат:** RGD-5
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_pouch.png`
- **Заметка:** оружие на полу; без него подсумок использует изображение 5, чуть увеличенное

```text
Using the same RGD-5 grenade and pixel style as before, create ONE item sprite: a Soviet Army khaki canvas grenade pouch for two grenades, with a flap and a small leather strap, lying flat on the floor, the flap open and the tops of two olive-green RGD-5 grenades (grey steel fuses, round pull-rings) showing. Seen from the side and slightly above (about 30 degrees). Centred, filling about 70% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no letters, no logo. FORMAT: square image.
```

#### Изображение 7 из 7 (НЕОБЯЗАТЕЛЬНО): ящик
- **Чат:** RGD-5
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_rgd5_crate.png`
- **Заметка:** без надписей: у настоящего ящика советская маркировка содержит текст, здесь только полоса

```text
Using the same pixel style as before, create ONE item sprite: a small Soviet Army wooden ammunition crate painted olive-green, with rope handles at both ends, steel corner brackets and a plain yellow stencilled stripe on the side (NO letters, NO numbers, NO symbols), the lid propped open showing four olive-green RGD-5 grenades lying in a row. Seen from the front and slightly above (about 30 degrees). Centred, filling about 80% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no logo. FORMAT: wide landscape image.
```

## 5. Звуки (не для Gemini; для `sound-designer`)

Сегодня граната проигрывает уже установленные звуки под собственными именами (`SNDINFO`, «Slot 8»). Не хватает
пяти: `SDRGPIN` (кольцо и чека), `SDRGTHR` (рука и слетающий рычаг), `SDRGBNC` (стальное яйцо о бетон), `SDRGEXP`
(сухой разрыв с осколками, меньше, чем ПГ-7В) и `SDRGPKP` (брезентовый подсумок, две гранаты).
Подробности в `docs/engine/2026-10-23_V3_rgd5.md` §4.

Gemini не открывался, и ни одно изображение не было сгенерировано при подготовке этих промптов. Всё сказанное о
том, как он ответит, **НЕ ПРОВЕРЕНО**, пока им не воспользуются; кадры 2 и 3 (две руки, движение) несут
наибольший риск расхождения.
