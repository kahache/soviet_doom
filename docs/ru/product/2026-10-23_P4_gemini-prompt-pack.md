# Gemini: пакет промптов на завтра (P4, малая дневная квота, D116)

Каноническая версия: `docs/product/2026-10-23_P4_gemini-prompt-pack.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

**Для:** CEO. **Автор:** art-director, подготовлено 2026-10-22 для использования 23-го. **Статус:** готово к вставке.
Написано по-английски (D129: документы репозитория на английском; испанский только в чате с CEO); промпты находятся внутри блоков кода. В `docs/ru/` не зеркалируется (D34).
Изображения никогда не загружаются на GitHub (D77, `work/` игнорируется).

> **За 30 секунд.** Запрашивается **27 изображений**, упорядоченных по приоритету (таблица ниже, с
> накопительным итогом: где бы ни кончилась квота, сделанное до этой точки пригодно). Один новый чат на каждого персонажа. У каждого
> изображения свой полный промпт (общие блоки уже вставлены внутрь), имя файла и что приложить. Оружие идёт в `work/art/reference/`; враги в `work/art/reference/enemies/gemini/`.
> Затем PM преобразует их с помощью `tools/art/gemini_frames.py` и `tools/art/gemini_enemy.py`.

## 1. Сводка

| Приоритет | Объект | Изображений | Накопительный итог |
|---|---|---|---|
| 1 (высокий) | ТТ-33 (D111) | **2** | 2 |
| 2 | SD_LegionGunner (SDLG) | **5** | 7 |
| 3 | SD_LibertyColossus (SDLC) | **7** | 14 |
| 4 | Консорциум (SDCN) | **7** | 21 |
| 5 | АКМ | **2** (+1 необязательно: перезарядка) | 23 |
| 6 | Повторные запросы с наибольшим эффектом | **4** | 27 |

**Всего: 27 изображений** (28, если запросить и необязательную перезарядку АКМ). Естественные точки остановки (всё до них
остаётся пригодным): 2 (ТТ-33), 7 (+ пулемётчик), 14 (+ Колосс), 21 (+ Консорциум), 23 (+ АКМ), 27 (+ повторные запросы).

Что открывает каждый объект:

| Объект | Что попадает в игру | Примечания к количеству |
|---|---|---|
| ТТ-33 | стартовое оружие, переделанное с голыми руками (D111; сегодня «переделать», D61) | 2: покой и стрельба |
| SDLG | 70 лампов пулемётчика (5 новых листов + уже существующий `turn`) | боль и расчленение получаются производными (это делает конвейер) |
| SDLC | 81 ламп Колосса (7 листов) | лист топота несёт 2 ряда (Q сверху, R снизу) в 1 изображении |
| SDCN | 95 лампов финального босса (7 листов) | два листа несут по 2 ряда (прицеливание E/F, ходьба A/C) для экономии квоты; R (светящееся ядро) и боль H получаются производными |
| АКМ | второе оружие слота 4 | 2 изображения; перезарядка (необязательно) отложена (D47) |
| Повторные запросы | 4 самых заметных исправления из 7 уже установленных листов | в конце раздела 9 написано, что было оставлено и почему |

## 2. Практическая заметка (прочтите перед началом)

1. **Один новый чат на каждого персонажа** (8 чатов: ТТ-33, пулемётчик, Колосс, Консорциум, АКМ, гончая, Генерал, Легион).
   Так Gemini не смешивает стили. Внутри каждого чата изображения идут **в том порядке, в каком они здесь стоят**: первое
   фиксирует персонажа, а следующие запрашиваются в том же чате.
2. **Непрерывность.** Промпты вторых изображений начинаются с *"Using exactly the same character as in the previous
   image (same face, same colours, same equipment, same proportions, same scale)..."* и повторяют краткое описание
   персонажа. Если он всё равно уплывает (другое лицо, другая каска, другой масштаб), **не пересоздавайте вслепую**: в том же чате
   напишите *"Exactly the same character as in the first image of this chat: same face, same helmet, same colours, same
   scale. Redo only this pose."* и снова приложите первый лист. Каждое пересоздание тратит квоту: используйте его, только если
   персонаж стал другим человеком или фигуры касаются друг друга либо выходят за кадр.
3. **Прикрепление изображений** (пулемётчик, гончая, Генерал, Легион): меню «+» в Gemini, в первом сообщении чата.
   PM может сделать это через Chrome (`find` по скрытым полям выбора файла и `file_upload`); вручную перетащите PNG.
4. **Считайте фигуры перед сохранением.** В листах с одним рядом должно быть **5** фигур; в двухрядных 5 + 5; в листах
   смерти 5. Лишняя или недостающая фигура в листе смерти не требует переделки (конвейер выбирает, какие использовать); переделки
   требуют касающиеся друг друга фигуры, что-то, обрезанное краем, буквы или смена персонажа.
5. **Сохранение.** Скачайте изображение (или приём с canvas через `toDataURL`, шириной 1024 px; Chrome сохраняет в
   `E:\Downloads`) и переместите его под **точным именем**, которое указано у каждого изображения. Формат не важен (.png, .jpg, .jfif), но для
   врагов предпочтителен `.png`.
6. **Если Gemini отказывает или отвечает только текстом.** Сначала скажите *"Generate the image now"* (иногда он отвечает, не
   генерируя). Если отказывает, **переформулируйте без слов о насилии и без символов** и повторите в том же чате:

| Если отказ из-за... | Измените... |
|---|---|
| насилия | уберите `kill, dead, die, blood, wound, gore, shot, bullet`. Используйте `hit, struck, knocked out, flinching, falling`. В промптах смерти сохраняйте "cartoonish like a 1993 video game". Никогда слово *blood* |
| стрельбы | `blasting a burst` -> `with a bright yellow-orange flash of light at the muzzle of his prop gun` |
| символов | **никогда** не просите свастику, крюкообразный крест, "Nazi" или "SS". Повязка — это *"a red armband with a plain white empty square"*; если всё равно отказывает, просите только *"a red cloth band on the upper arm"* и учтите: конвейер дорисовывает символ (D108) |
| реальных людей | уберите *"inspired by the Statue of Liberty monument"* и оставьте *"a giant robed statue holding a torch"* (это памятник, а не человек, но на всякий случай); никогда не называйте лидеров или президентов |
| ничего из перечисленного | новый чат, снова приложите референс и просите **только позу** одним предложением, сохраняя блоки LAYOUT и BACKGROUND |

7. **Квота.** Согласно `docs/HANDOFF.md`, счётчик сбросился 22 окт. в 17:33; **не проверено**, что завтра
   он сбросится в то же время. Если квота кончится посреди объекта, сохранённое остаётся: запишите номер последнего
   сделанного изображения и продолжайте со следующего.
8. **Быстрая проверка перед сохранением каждого листа врага** (то, что стоило повторных запросов в семи уже сделанных):
   плоский пурпурный фон, **без тени, нарисованной на полу**; 10 px отступа вокруг и под ботинками (подошвы,
   обрезанные краем, были самым частым поводом для повторного запроса); ни одна фигура не касается соседней (включая вспышки выстрелов и дым);
   без букв и цифр; профиль смотрит влево; один масштаб у всех пяти фигур; повязка Рейха,
   красная с **пустым** белым квадратом. **Оружие:** голые руки, пять пальцев, правая рука справа, плоский пурпурный
   фон, оружие целиком, почти прямо и по центру; без перчаток, врагов, строки состояния, текста или обрезанного оружия.
9. **Советские флаги НЕ идут в очередь Gemini** (D119). Флаги и знамёна карт делаются нашими процедурными генераторами (D113), а не Gemini.

## 3. Общие блоки (справочно: **уже вставлены внутрь каждого промпта**)

Чтобы вы видели, откуда берётся каждая фраза. Что сработало с семью готовыми листами: пять видов в ряд, плоский
пурпурный фон, без символов; смерть "cartoonish like a 1993 video game" без слова *blood*, с последним кадром
"knocked out, lying completely flat and horizontal". (Оригинальные промпты тех листов в репозитории не хранятся:
эти блоки восстанавливают их по `docs/HANDOFF.md`, спецификациям `tools/art/gemini_enemy.py` и получившимся листам;
НЕ ПРОВЕРЕНО, что формулировка буквально та же.)

- **STYLE:** Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.
- **LAYOUT (5 vistas):** LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.
- **LAYOUT (2 filas):** LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.
- **BACKGROUND:** BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image.


## 4. Приоритет 1: ТТ-33 (D111): 2 изображения

Новый чат. Базовый промпт и блок `[WEAPON]` из `docs/product/2026-10-20_0030_M2_gemini-weapons.md` §3-§4, а промпт стрельбы из его §5, как есть.
Затем PM запускает `tools/art/gemini_frames.py` (~50k токенов).

#### Изображение 1 из 27 (ТТ-33 1/2)
- **Чат:** Чат 1 (ТТ-33)
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_tt33_A.png`
- **Заметка:** покой; проверьте чек-лист оружия в пункте 2.8

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet TT-33 Tokarev pistol held in the RIGHT hand only, arm extended forward, the left hand not visible.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Изображение 2 из 27 (ТТ-33 2/2)
- **Чат:** Чат 1 (ТТ-33)
- **Приложить:** ничего (тот же чат, сразу после A)
- **Сохранить как:** `work/art/reference/gemini_tt33_B.png`
- **Заметка:** стрельба

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```


## 5. Приоритет 2: SD_LegionGunner (SDLG): 5 изображений

Новый чат. **В первом сообщении приложите `gem_gunner_turn.png`** (5 уже существующих стоячих видов: Легион Свободы,
пулемёт M1919 у бедра, две перекрещённые пулемётные ленты, флаг США на правом плече) вместе с
промптом walkL. Остальные листы идут в том же чате. Кадры, которые требует класс
(`docs/engine/2026-10-22_P4_ep2-enemies.md` §4): A-D ходьба (walkL, walkR и уже существующий лист `turn`), E прицеливание
(aim, а также пауза между очередями), F огонь (fire, со вспышкой у бедра), G боль (производный от `turn`), H-L
смерть (лист смерти, 5 фигур), M-U расчленение (производное с эффектами конвейера). Поэтому не хватает только 5 листов.

**Плейтест CEO (D119):** *"el soldado que dispara ametralladora, que es todo de color ocre, su dibujo disparando parece que dispare lateral y no frontal"* (CEO: «солдат, стреляющий из пулемёта, весь охристого цвета, его рисунок при стрельбе выглядит так, будто он стреляет вбок, а не вперёд»). Промпты **aim** и **fire** теперь просят, чтобы **вид 1 (спереди) стрелял прямо на камеру** (ствол с ракурсом в сторону зрителя, дульная вспышка перед оружием, по центру), а остальные виды были направлены туда, куда смотрит каждый. Сегодняшний «весь охристый» вид — это временный тонированный спрайт (D116), он исчезнет с графикой Gemini.

**Проверка перед сохранением aim и fire (D119):** на фигуре 1 (спереди) оружие направлено **на камеру** (ствол виден в упор, в ракурсе, а не сбоку) и, в fire, дульная вспышка находится **перед оружием, по центру** фигуры, а не сбоку; на 3 (профиль) ствол направлен **влево**; на видах сзади ствол виден за его дальней стороной. Если вид спереди стреляет вбок, переделайте только этот лист с *"View 1 must fire straight at the camera, barrel foreshortened toward the viewer, flash in front of the weapon."*

#### Изображение 3 из 27 (SDLG 1/5)
- **Чат:** Чат 2 (пулемётчик Легиона)
- **Приложить:** work/art/reference/enemies/gemini/gem_gunner_turn.png (приложите этот лист в первом сообщении этого чата)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_gunner_walkL.png`
- **Заметка:** первое сообщение чата: приложите лист

```text
Using the attached reference sheet as the exact character reference (same figure in all five views, same equipment, same scale), make the WALK sheet, left-foot-forward stride.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the LEFT foot stepping forward and planted, the RIGHT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride, so that it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Изображение 4 из 27 (SDLG 2/5)
- **Чат:** Чат 2 (пулемётчик Легиона)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_gunner_walkR.png`

```text
Using exactly the same character as in the attached reference sheet and the previous sheet (same face, same colours, same equipment, same proportions, same scale), make the WALK sheet, right-foot-forward stride: the mirror of the previous walk sheet's legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the RIGHT foot stepping forward and planted, the LEFT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Изображение 5 из 27 (SDLG 3/5)
- **Чат:** Чат 2 (пулемётчик Легиона)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_gunner_aim.png`
- **Заметка:** вид 1 (спереди): целится в камеру, ствол в ракурсе в сторону зрителя (D119), см. проверку выше

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: AIMING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: AIMING. He plants his feet wide and braces, the M1919 levelled at hip height held with both hands, the barrel always pointing in the direction each view faces. VIEW 1 (front): he aims DIRECTLY AT THE CAMERA, head-on, not sideways: the gun is seen end-on and foreshortened, the muzzle opening a dark circle pointing straight at the viewer, centred in front of his belly, both arms reaching toward the viewer, shoulders square to the camera. View 2 (three-quarter front): the barrel angles toward the camera and to the LEFT. View 3 (profile facing LEFT): the barrel points horizontally to the LEFT. View 4 (three-quarter back): the barrel is seen beyond his far side, pointing away from the camera. View 5 (straight back): the gun is hidden mostly behind his body, only the end of the barrel showing beyond his far side, pointing away from the camera. Face scowling, gun steady, NO muzzle flash.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Изображение 6 из 27 (SDLG 4/5)
- **Чат:** Чат 2 (пулемётчик Легиона)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_gunner_fire.png`
- **Заметка:** вспышки, касающиеся соседней фигуры, усложнили лист огня Генерала. **Вид 1 (спереди): стреляет в камеру** (D119), см. проверку выше

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: FIRING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: FIRING. The same braced stance as the aiming sheet, but now the M1919 is blasting a burst: a bright yellow-orange muzzle flash with a small white-hot core at the muzzle, a few brass casings flying out, the gun and shoulders jerked back slightly by the recoil, mouth open shouting. DIRECTION OF FIRE: in VIEW 1 (front) he fires DIRECTLY AT THE CAMERA, NOT sideways: the M1919 is seen end-on and foreshortened with its barrel pointing straight at the viewer, shoulders square to the camera, and the muzzle flash is a star-shaped burst IN FRONT of the weapon, centred on the barrel in the middle of the figure (not off to one side), with the casings flying out to the sides. In view 2 (three-quarter front) the barrel and the flash angle toward the camera and to the LEFT; in view 3 (profile facing LEFT) the barrel and the flash point horizontally to the LEFT; in views 4 and 5 (back) the flash shows only beyond his far side, pointing away from the camera, never painted over his back. Keep the muzzle flash small and compact, well clear of the neighbouring figures (they must not touch).

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Изображение 7 из 27 (SDLG 5/5)
- **Чат:** Чат 2 (пулемётчик Легиона)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_gunner_death.png`
- **Заметка:** кадр 5: лежит совершенно плоско (конвейер использует его как труп, буква L)

```text
Same character as the attached reference sheet and the previous sheets, new sheet: a death animation strip, cartoonish like a 1993 video game (no realism, nothing graphic, no wounds).

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

FRAMES, left to right: 1) flinching and staggering back from a hit, mouth open, still holding the machine gun; 2) struck, head thrown back, arms flung out, the M1919 dropping from his hands; 3) falling backwards at about 45 degrees, the gun in the air; 4) nearly down, sitting on the ground with his back almost on the floor, knees up, small puffs of dust, the gun on the ground beside him; 5) knocked out, lying completely flat and horizontal on his back on the ground, glowing eyes dimmed, arms limp, the M1919 lying beside him.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that his head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


## 6. Приоритет 3: SD_LibertyColossus (SDLC) с нуля: 7 изображений

Новый чат, **без референсного изображения** (концепция в `docs/engine/2026-10-22_P4_ep2-enemies.md` §3: извращённая
Статуя Свободы: хром, зубчатая корона, факел, являющийся ракетной установкой и огнемётом, скрижаль как щит).
Художественные решения, принятые здесь, подлежат подтверждению при виде первого листа:
- Факел в **её правой** руке, скрижаль на **левой** руке (соответствует выстрелу, который выходит "20 справа
  от неё"). **Пустая** скрижаль (Gemini пишет текст, как только может).
- Флаг США на правом плече, как у остального Легиона (D12); без повязки и других политических символов.
- Пропорция 6 в высоту на 5 в ширину (~120-130 px высотой, не более ~100 в ширину в игре).
- Кадры класса: A-D ходьба (turn + walkL + walkR), E прицеливание, F огонь, G боль (производный), Q и R топот (одно
  изображение с 2 рядами), H-P смерть (5 фигур; конвейер достраивает 9 букв, как с Генералом).
- **Играбельный минимум**, если квоту обрежут посередине: `turn`, `fire` и `death` (остальное заполняется стоячим видом).

#### Изображение 8 из 27 (SDLC 1/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (текст, без референса)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_turn.png`
- **Заметка:** этот лист фиксирует персонажа и масштаб; если вышел плохо, не продолжайте: сначала переделайте его (считается резервом)

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE LIBERTY COLOSSUS, a giant boss monster of an alien invasion army: a colossal chrome robot-statue shaped like a stern robed woman monument, inspired by the Statue of Liberty monument (a statue, not a real person; a generic stern face with hollow glowing pale-blue eyes). Chrome plate-armour robes with heavy folds reaching her shins, raw pink flesh showing at the joints (elbows, wrists, neck, knees), heavy chrome feet. On her head a crown of seven long steel spikes. Her RIGHT arm (on the left of the image in the front view) is raised high holding a huge TORCH that is really a rocket launcher and flame projector: a thick steel tube with a flared nozzle on top, glowing orange inside. Her LEFT arm carries a large stone tablet as a shield in front of her body; the tablet is completely blank, no text, no numbers, no carving. A small US flag patch (stars and stripes) on the plate of her RIGHT shoulder. Stocky and heavy for a boss: about 6 units tall to 5 wide, including the raised torch.

POSE: standing idle and menacing, feet planted apart, the torch held high with the nozzle pointing up and glowing, the blank tablet held on the left forearm in front of the chest, chin lowered, hollow glowing eyes.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 9 из 27 (SDLC 2/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_walkL.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, LEFT foot forward and planted, RIGHT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. A clear, wide stride so it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 10 из 27 (SDLC 3/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_walkR.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, RIGHT foot forward and planted, LEFT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. The mirror of the previous walk sheet's legs.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 11 из 27 (SDLC 4/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_aim.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: AIMING. The torch arm swings down and the torch is levelled to point at the viewer: in the front view the torch nozzle points straight at the camera (foreshortened, glowing orange inside), in the profile it points horizontally to the LEFT, in the back views it points away beyond her far side. The tablet is raised in front of her body, the legs braced wide. NO flame and NO rocket yet, only the glow.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 12 из 27 (SDLC 5/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_fire.png`
- **Заметка:** та же осторожность со вспышками и дымом, что и в листе огня Генерала

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING. The same braced pose as the aiming sheet, but the torch is now discharging: a rocket leaving the nozzle with a short bright orange-yellow burst of flame and a puff of smoke, the whole figure jolted back slightly. Keep the flame and smoke short and compact, well clear of the neighbouring figures (they must not touch). In the back views the blast shows only beyond her far side, never painted over her back.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 13 из 27 (SDLC 6/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_stomp.png`
- **Заметка:** одно изображение с 2 рядами (Q сверху, R снизу); если второй ряд вышел плохо, запросите его отдельно (резерв)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, the STOMP wind-up: she raises her LEFT knee high with the foot lifted well off the ground, the body leaning back a little, the torch held high, the tablet braced in front. BOTTOM ROW, the STOMP impact: the same foot slammed down onto the ground, the body leaning forward, the torch still high, a compact ring of dust and small cracked rock around the feet (kept close to the feet, not spreading to the neighbouring figures).

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 14 из 27 (SDLC 7/7)
- **Чат:** Чат 3 (Колосс Свободы)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_colossus_death.png`
- **Заметка:** кадр 5 = обломки, которые остаются (буква P)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (the Colossus is a machine-statue falling to pieces; nothing graphic). This is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) shuddering, the crown cracking, one spike snapping off, a few chrome sparks; 2) the torch slipping from her hand and falling, the tablet shield dropping from her other arm; 3) swaying and leaning back, knees buckling, pieces of chrome plate breaking away; 4) toppling backwards at about 45 degrees, mid-fall; 5) wrecked, lying completely flat and horizontal on her back, the crown broken, the torch and the tablet lying beside the body, thin wisps of smoke.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that her head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 7. Приоритет 4: Консорциум (SDCN): 7 изображений

Новый чат, **без референсного изображения** (`docs/engine/2026-10-22_P4_ep3-final-boss.md` §2 и §5). Красная повязка
полу-Рейха несёт **пустой белый квадрат**: Gemini отказывает в свастике, а конвейер дорисовывает символ (D108). Символ не
запрашивается, и SS не называются: каска — это "a grey German-style steel helmet".

Кадры класса и откуда берётся каждый:

| Кадры | Что это | Источник |
|---|---|---|
| Q, R | укоренён, ядро погашено / горит | SDCN 1/7 (Q); R получается осветлением кобальтово-синего цвета ядра |
| B, D | фаза 2 стоя и эталонный масштаб | SDCN 2/7 |
| G | стрельба, вспышка и пылающее ядро | SDCN 3/7 |
| I-O | смерть: ядро, они кричат, половины, обрушение, горение, обломки | SDCN 4/7 (5 фигур; M и N получаются производными с огнём) |
| E, F | предвестник сферы / предвестник ракеты | SDCN 5/7 (2 ряда: E сверху, F снизу) |
| A, C (ходьба) | фаза 2, ходьба | SDCN 6/7 (2 ряда: A сверху, C снизу) |
| S | Прорыв (рвущиеся кабели) | SDCN 7/7 |
| H | боль, две головы | производный (стоячий вид, наклонённый) |

Порядок внутри объекта — это порядок приоритета: **играбельный минимум** = изображения с 1 по 4 (укоренён, turn, fire, death);
недостающие кадры заполняются стоячим видом.

**Художественное решение (подтвердите его):** кадры атаки E, F, G и S служат обеим фазам, а у босса нет ног в фазе 1 и есть
в фазе 2. Чтобы не рисовать два набора, в этих кадрах нижняя часть **обмотана узлом кабелей и тёмного дыма, скрывающим ноги**; так
они работают в обеих фазах. Если при просмотре это неубедительно, есть вторая партия с ногами
(в общий итог не входит). Две каски с типовыми лицами никого не воспроизводят (D12).

#### Изображение 15 из 27 (SDCN 1/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (текст, без референса)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_rooted.png`
- **Заметка:** фиксирует персонажа (кадр Q). R, светящееся ядро, получается осветлением кобальтово-синего: его не запрашивают

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE CONSORTIUM, the final boss of an alien invasion, twice the height of a heavy brute: one huge trunk made of TWO halves welded together down the middle, with TWO heads joined at the shoulders (one per half), generic stern faces, no likeness of any real person. Its LEFT half (on the viewer's RIGHT in the front view) is the German half: grey-green skin, a grey German-style steel helmet with a small eagle badge, a red armband on the upper arm with a plain white square field that is completely empty (no symbol, no letters), and the forearm replaced by a rack of rocket tubes. Its RIGHT half (on the viewer's LEFT in the front view) is the American half: chrome plate armour over pink flesh, an American M1 steel helmet, a small US flag patch on the shoulder, and the forearm is a big chrome energy-ball projector with a glowing nozzle. Between the two halves, in the chest, a ribbed open cavity glowing cobalt blue (portal energy): the glowing core.

POSE: PHASE 1, standing still, plugged into the floor.

LOWER BODY, ROOTED: no legs. The lower body is a heavy skirt of thick black cables and conduits that flare out and pool on the floor, with more thick cables running away from its back and skirt into the distance (in the front view they disappear behind it). The core glows a dim, steady cobalt blue. Both arms hang heavily at its sides, the weapon forearms pointing down, a heavy brooding stance.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 16 из 27 (SDCN 2/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_turn.png`
- **Заметка:** эталонный лист фазы 2 (кадры B и D, и масштаб)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, but PHASE 2. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: PHASE 2, standing, the same upper body as the previous sheet.

LOWER BODY, FREE: the cables have been torn out: short stumps of black cable hang at its back and hips, sparking and trailing along the floor, and under the trunk there are two heavy mechanical legs of grey steel with hydraulic pistons and big flat armoured feet. The core burns brighter, a vivid cobalt glow. Standing, both arms hanging heavily, the weapon forearms pointing down.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 17 из 27 (SDCN 3/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_fire.png`
- **Заметка:** художественное решение: нижняя часть спрятана в узле кабелей и дыма, чтобы работать в фазах 1 и 2 (см. текст раздела)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING (frame G, shared by both phases). Both arms fire at once: the energy projector (its RIGHT forearm) discharges a bright cobalt-and-white ball of energy with a muzzle flare, the rocket tubes (its LEFT forearm) shoot a rocket with a burst of orange flame, and the chest core blazes bright white-blue; the whole body jolted back slightly, both mouths open roaring. Keep every flare and flame compact, well clear of the neighbouring figures (they must not touch). In the back views the blasts show only beyond the far side, never painted over its back.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 18 из 27 (SDCN 4/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_death.png`
- **Заметка:** 5 фигур покрывают I J K L (M и N получаются производными с огнём) и O (обломки с двумя касками)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (nothing graphic). This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) the core cracking: bright cobalt-white cracks of light across the chest, both heads recoiling; 2) both heads screaming, both arms thrown out; 3) the two halves tearing apart along the welded seam, the chest splitting open with blinding cobalt light, plates and sparks flying; 4) collapsing and sagging down onto its knees, the halves separating, small flames starting; 5) the wreck: a low smoking ruined heap of grey-green and chrome plates and tangled cables, with the two steel helmets (one grey German-style, one American M1) lying side by side in the ash, a few small flames.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the boss falling backwards so that its heads end up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 19 из 27 (SDCN 5/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_aim.png`
- **Заметка:** одно изображение с 2 рядами (E сверху, F снизу)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW (the orb tell): its RIGHT arm, the chrome energy projector, is levelled forward at the viewer with the nozzle glowing, the chest core opening wide and glowing brighter, the other arm hanging; in the front view the nozzle points at the camera (foreshortened), in the profile it points horizontally to the LEFT. BOTTOM ROW (the rocket tell): its LEFT arm, the rack of rocket tubes, is raised and aimed at the viewer, the tubes loaded and ready, the other arm hanging. NO flames and NO shots yet.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 20 из 27 (SDCN 6/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_walk.png`
- **Заметка:** одно изображение с 2 рядами (A сверху = walkL, C снизу = walkR)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs and the torn cable stumps dragging.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, WALK with the LEFT mechanical leg forward and planted, the RIGHT leg behind with the heel lifted, cable stumps dragging on the floor, a heavy lumbering stride, both arms hanging. BOTTOM ROW, the mirrored stride: RIGHT leg forward and planted, LEFT leg behind with the heel lifted. A clear, wide stride in both rows.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 21 из 27 (SDCN 7/7)
- **Чат:** Чат 4 (Консорциум)
- **Приложить:** ничего (тот же разговор)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_consortium_breach.png`
- **Заметка:** последний в объекте: виден лишь две секунды, когда полоса здоровья раскалывается; если его нет, конвейер использует кадр боли (H)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: THE BREACH (frame S): the thick black cables snapping off its back and hips and whipping outward with white sparks, the core flaring blinding white, both arms thrown wide, both heads roaring upward, the body arched back. Keep sparks and cable ends compact, clear of the neighbouring figures.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 8. Приоритет 5: АКМ: 2 изображения (+1 необязательно)

Новый чат. Блок `[WEAPON]` и готовый базовый промпт из `docs/engine/2026-10-22_P4_akm.md` §5, с промптом стрельбы
из `docs/product/2026-10-20_0030_M2_gemini-weapons.md` §5 без изменений, в том же чате. **Проверьте**, помимо
чек-листа оружия в пункте 2.8: **изогнутый магазин** и **косой дульный тормоз** (то, что отличает АКМ от ППШ-41 при 320x200).

#### Изображение 22 из 27 (АКМ 1/2)
- **Чат:** Чат 5 (АКМ)
- **Приложить:** ничего
- **Сохранить как:** `work/art/reference/gemini_akm_A.png`
- **Заметка:** покой; проверьте ИЗОГНУТЫЙ магазин и КОСОЙ дульный тормоз

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet AKM assault rifle of the 1970s (7.62x39), seen from behind: a black phosphated steel receiver with a stamped dust cover, a reddish-brown laminated wooden handguard and pistol grip, a curved 30-round magazine in orange-brown bakelite, the gas tube above the barrel, and the slanted muzzle brake at the very end of the barrel. The LEFT hand holds the wooden handguard under the barrel; the RIGHT hand grips the pistol grip, the index finger along the trigger guard. The stock is tucked into the right shoulder, out of the image.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Изображение 23 из 27 (АКМ 2/2)
- **Чат:** Чат 5 (АКМ)
- **Приложить:** ничего (тот же чат)
- **Сохранить как:** `work/art/reference/gemini_akm_B.png`
- **Заметка:** стрельба

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```

#### НЕОБЯЗАТЕЛЬНОЕ изображение (вне итога)
- **Чат:** Чат 5 (АКМ)
- **Приложить:** ничего (тот же чат, после A)
- **Сохранить как:** `work/art/reference/gemini_akm_C.png`
- **Заметка:** НЕОБЯЗАТЕЛЬНО (перезарядки отложены, D47): только если останется квота; в итог не входит

```text
Using exactly the same image, make the reloading frame: the rifle is tilted a little to the right, the LEFT hand pulls the empty curved magazine down and out of the magazine well, a fresh curved magazine held against it. Same hands, same rifle, same magenta background, same pixel style.
```


## 9. Приоритет 6: повторные запросы с наибольшим эффектом: 4 изображения

Из списка в листе `docs/art/previews/2026-10-22_P4_enemies-gemini.html` (поле "Pedir otra vez a Gemini", то есть «Попросить Gemini ещё раз», которое берётся из
`tools/art/gemini_enemy.py`) — только четыре самых заметных в игре, в таком порядке: гончая в броске, приказ
Генерала с поднятым кулаком (плюс указание рукой, в том же изображении), флаг Легиона, меняющий плечо, и смерть Легиона
с обрезанным дробовиком. Первые два — новые кадры; последние два исправляют видимые дефекты рядового
солдата, самого частого врага. Новые файлы не перезаписывают существующие (`_v2`, `lunge`, `summon`, `turnB`).

#### Изображение 24 из 27 (повторный запрос 1/4)
- **Чат:** Чат 6 (гончая)
- **Приложить:** work/art/reference/enemies/gemini/gem_hound_bite.png (референс персонажа и сетки)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_hound_lunge.png`
- **Заметка:** повторный запрос по гончей: сегодня укус почти не меняет позу; это даёт прыжок (кадры F/G)

```text
Using the attached sheet as the exact reference (same Reich hound: grey skin, brown fur on the back, riveted steel helmet-collar and shoulder plates, spiked collar, yellow eyes; same pixel style, same scale, same 2-rows-by-4 grid layout and same view order), make a NEW sheet of the ATTACK LUNGE.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: the hound launching its attack: the front paws completely off the ground, the body stretched out in mid-leap, jaws wide open at full stretch, head thrust forward, the hind legs still pushing off. Views as in the reference grid (front, three-quarter front, profile facing LEFT, three-quarter back, back, repeated as in the reference).

LAYOUT: the same 2 rows by 4 figures as the reference, each figure fully inside the image with at least 10 px of empty background all round, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere, NO ground shadow under the dog, no gradient, no scenery, no text, no letters, no logo, no watermark. FORMAT: landscape image.
```

#### Изображение 25 из 27 (повторный запрос 2/4)
- **Чат:** Чат 7 (Генерал)
- **Приложить:** work/art/reference/enemies/gemini/gem_general_turn.png (референс персонажа)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_general_summon.png`
- **Заметка:** повторный запрос по Генералу: кадры Q и R приказа 'Vorwarts!' (сегодня это поза покоя и прицеливание)

```text
Using the attached sheet as the exact reference (same General: cream greatcoat with gold epaulettes, medals, monocle, peaked cap, black boots and belt, striped red-and-white cape, olive bazooka; same pixel style, same scale), make a NEW sheet with TWO rows of poses.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, GIVING AN ORDER: his LEFT fist raised high above his head, mouth open shouting a command, the bazooka resting on his RIGHT shoulder. BOTTOM ROW, POINTING: his LEFT arm extended straight forward with the index finger pointing at the viewer, the bazooka resting on his RIGHT shoulder. In every view the small US flag patch is on his RIGHT arm and the red armband with a plain white empty square field is on his LEFT arm (as in the three-quarter views of the reference), no symbol or letters in the armband.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Изображение 26 из 27 (повторный запрос 3/4)
- **Чат:** Чат 8 (солдат Легиона)
- **Приложить:** work/art/reference/enemies/gemini/gem_legion_turn.png (референс персонажа)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_legion_turnB.png`
- **Заметка:** повторный запрос по Легиону: исправляет флаг, меняющий плечо при отражении (виды 2-4)

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same white helmet, same shotgun, same style and scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CORRECTION: the three-quarter front, the side profile and the three-quarter back views must all face LEFT, with the small US flag patch on his RIGHT shoulder sleeve in every view where that shoulder is visible. Keep the same standing pose, shotgun held across the chest, in all five views.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Изображение 27 из 27 (повторный запрос 4/4)
- **Чат:** Чат 8 (солдат Легиона)
- **Приложить:** work/art/reference/enemies/gemini/gem_legion_death.png (референс; тот же чат 8, приложите его снова)
- **Сохранить как:** `work/art/reference/enemies/gemini/gem_legion_death_v2.png`
- **Заметка:** повторный запрос по Легиону: выпавший дробовик трупа выходит обрезанным краем; сохраните как _v2, чтобы не перезаписать оригинал

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same five death frames in the same order, same cartoonish 1993 video-game style, same scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) flinching and staggering back from a hit, still holding the shotgun; 2) struck, head thrown back, the shotgun dropping; 3) falling backwards at about 45 degrees; 4) nearly down, sitting with his back almost on the floor, small puffs of dust; 5) knocked out, lying completely flat and horizontal on his back, the shotgun lying beside him.

CORRECTION: the figures were cut off by the right and bottom edges (the dropped shotgun of the last frame). Draw every frame fully inside the image, with at least 12 px of empty background on every side and under the figures, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


### Повторные запросы, которые оставлены (и почему)

| Повторный запрос из листа | Почему его нет в завтрашней квоте |
|---|---|
| Штурмовик: 6 листов на более высоком холсте (обрезанные подошвы) | 6 изображений; конвейер уже добавляет тёмную подошву в 5 px (в игре почти не видна) |
| Panzermensch: 6 листов выше, повязки без букв, запуск влево | 6 и более изображений; повязка уже исправлена (`patch`) и подошва добавляется |
| Штурмовик aim2/fire2 и атака | необязательно («только если CEO хочет») |
| Гончая walkL/walkR более различимые, боль | необязательно; видимое изменение — прыжок |
| Doughboy: виды атаки 3-4 без дублированного свечения | конвейер уже стирает свечение (`erase`), приемлемо |
| Генерал: спереди и сзади с флагом на правой руке (5 листов) | 5 изображений ради дефекта ~3x2 px в игре |
| Генерал: огонь с большим пространством; смерть в том же масштабе | уже решено конвейером (`split_x`, масштаб x1.39) |

Если останется квота, следующим по эффекту был бы **Panzermensch** (лист `fire` с повязками без букв), а затем
**Генерал: смерть в масштабе**.

## 10. Контроль квоты

Порядок выполнения = номер изображения (с 1 по 27). Естественные точки остановки: 2, 7, 14, 21, 23, 27. Внутри
объекта пулемётчику нужны все 5 листов, чтобы заменить его временную графику; Колоссу и Консорциуму нужны минимум
`turn`, `fire` и `death` (Консорциуму, кроме того, `rooted`).

Возможная экономия, если понадобится урезать без потери кадров: запросить `walkL`+`walkR` пулемётчика и Колосса в 2 ряда
(на 2 изображения меньше, с риском, что второй ряд потеряет согласованность).

При подготовке этого пакета ни одно изображение не генерировалось, Gemini не открывался, никакой другой файл не трогался и ни
один коммит не делался. Всё сказанное о том, как отреагирует Gemini, **не проверено**, пока им не воспользуются; промпты Колосса
и промпты Консорциума (новые персонажи, без референса) несут наибольший риск отказа или расхождения.

## 11. ПОСЛЕДНЕЕ, перед публикацией v1.2: эпичный стартовый экран (TITLEPIC) (D126)

Приказ CEO (2026-10-23): *"Antes de publicar, nueva pantalla de inicio con Gemini! Que sea epica como la del Doom, con nuestro heroe y la bandera roja asesinando los enemigos nazis y yankis"* (CEO: «Перед публикацией новый стартовый экран с Gemini! Пусть он будет эпичным, как в Doom, с нашим героем и красным флагом, убивающими нацистских и янки-врагов»). Новый чат. **Приложите** лист героя, если он есть в `work/art/reference/` (сержант из строки состояния, 42 лица Gemini, D89), чтобы это был тот же человек; если нет, только текст. `TITLEPIC` — 320x200, а логотип `M_DOOM` (200x64) рисуется поверх в x=60, y=0 (MOD-SPEC, контракт меню): **верхняя треть остаётся свободной** (небо) для логотипа; конвейер компонует логотип и сводит к палитре. Gemini не рисует свастики и не принимает "Nazi": красная повязка с пустым белым квадратом (конвейер дорисовывает символ, как с врагами, D108). Без слов о крови.

- **Сохранить как:** `work/art/reference/gemini_titlepic_A.png` (и `_B`, если запрашивается вторая версия)

```text
Epic painted cover art for a 1990s PC first-person shooter, in the style of the classic 1993 DOOM box art and title screen: dramatic heroic low-angle composition, bold painted look with visible brush strokes, high contrast, fiery orange-and-red light. SCENE: a lone Soviet Spetsnaz sergeant of the 1970s, rugged unshaven face, olive-drab Soviet uniform with a striped telnyashka undershirt at the collar, a fur-lined ushanka hat or a steel helmet, stands on top of a heap of defeated alien invaders, raising a huge RED BANNER on a pole in his left hand (a plain bright red flag with a small golden hammer and sickle and a golden star in its upper corner) while he fires a Soviet PPSh-41 submachine gun with his right hand at the enemies charging him. THE ENEMIES, cartoonish 1990s game monsters, no realism: grey-green alien soldiers in grey German-style steel helmets with red armbands that have a plain empty white square, and chrome-skinned alien soldiers in white American M1 helmets with small US flag patches, some knocked down at his feet, others charging from both sides with their weapons, one giant chrome statue-robot monster with a torch looming in the smoky background. SETTING: a burning Soviet city at night, red sky, sparks and smoke, a red star on a distant tower. LAYOUT: the hero and the flag fill the centre and the lower two thirds of the image; the TOP THIRD of the image is open dark red sky with smoke only, empty, so a game logo can be placed there later. No text, no letters, no numbers, no logo, no watermark, no symbols other than those described, nothing graphic or gory. FORMAT: landscape 16:10.
```

Проверьте перед сохранением: герой читается как советский (форма, красный флаг с серпом и молотом), враги читаются как две стороны (немецкие каски с красной повязкой и хромовые с каской M1), верхняя треть свободна, без текста. Затем: art-director сводит к 320x200, компонует логотип `M_DOOM` и дорисовывает символ на повязках (D108; **CEO видит свастику до того, как она применена**, D105), превью для CEO, и только потом это устанавливается в `assets/graphics/shell/TITLEPIC.png`.
