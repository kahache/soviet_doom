# Fooocus: референсы рук для 5 видов оружия, всё ещё на руках Freedoom

Каноническая версия: `docs/product/2026-10-14_2356_M2_fooocus-prompts-weapons.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

**Автор:** art-director · **Дата:** 2026-10-14 23:56 · **Веха:** M2 (арсенал, фаза F4)
**Для:** CEO, с документом, открытым на ПК рядом с Fooocus (http://127.0.0.1:7865).
**Язык:** Написано по-английски (D129: документы репозитория на английском; испанский только в чате с CEO). Промпты и негативные промпты на английском, потому что SDXL лучше понимает английский. Документ не копируется в `docs/ru/` (D34).

> **За 30 секунд.** Пять видов оружия: ИЖ, ППШ-41, РПГ-7, РОКС-3 и ручная «Катюша». С **6 обязательными партиями** Метода A или с **6 входными изображениями** Метода B мы покрываем все пять: несколько видов оружия делят один хват.
> **Сначала попробуйте Метод B** (§4): вы подаёте Fooocus один из наших кадров, где композиция Doom уже верна, и Fooocus превращает его в фото. Если не получается, используйте **Метод A** (§5), только текстовый.
> **Порядок:** калибровка с ТТ-33 (5 мин) → ППШ → ИЖ → РПГ-7 → (РОКС-3 только если попросит PM) → «Катюша».

---

## 1. Рабочий процесс, всегда один и тот же

1. Один раз настройте Fooocus с **базовыми настройками** (§3).
2. Вставьте промпт и негативный промпт из нужного блока и нажмите **Generate**. Вы получите **4 изображения**.
3. Посмотрите на каждое по его **чек-листу** (✅ = оставить, ❌ = отбросить).
4. Сохраните **лучшее или 2 лучших** в `work/art/reference/` с **точным именем** блока (если сохраняете два, добавьте `2`: `ppsh_ready_rh2.png`).
5. Если рука получилась **зеркальной** (левая рука входит слева, когда мы просили правую справа), **это всё равно подходит**: сохраните с суффиксом `_mirrored` (`ppsh_ready_rh_mirrored.png`), и мы отразим сами (D73). **Не подходит** скрещённая рука: правая рука, входящая слева, или левая, входящая справа.
6. Если ни одно из 4 не годится, сгенерируйте ещё 4 (seed случайный). Если после **3 партий** всё ещё не получается, остановитесь и скажите PM, приложив лучшее из плохих: так мы подправим промпт, и вы не потратите больше времени.
7. Сообщите PM одной строкой: *"PPSh ready: ppsh_ready_rh.png, ppsh_ready_lh.png"*.

**Что важно, а что нет.** Важны рука, запястье, рукав, поза хвата и свет. **Оружие на фото не важно**: мы рисуем его сами и помещаем под пальцы с помощью `tools/art/hand_ref.py`. Простой контрастный фон (небо, снег) даёт чистое выделение.

---

## 2. Какое оружие, какие позы и сколько референсов

**Кадры стрельбы и отдачи не требуют референса**: мы получаем их из кадра покоя поворотом и сдвигом и добавлением дульной вспышки. Фото нужны только для различных поз.

| Оружие (слот) | Класс Doom и спрайт | Состояния, которые использует наш ZScript | Руки на экране | Позы, требующие фото | Изображений сохранить |
|---|---|---|---|---|---|
| **ИЖ-58**, двуствольный дробовик (3) | `SD_Izh` заменяет Shotgun, `SHTG` | A покой; B, C отдача; **D открыт для перезарядки** (D → C → B → A) | левая под цевьём; правая при перезарядке | **покой** (левая) и **открыт, перезарядка** (обе) | 2 (+1 необязательно) |
| **ППШ-41** (4), икона мода | `SD_Ppsh` заменяет Chaingun, `CHGG` | A, B чередуются при стрельбе | **обе**: левая спереди, правая на прикладе и спуске | **покой**, одно фото на руку | 2 |
| **РПГ-7** (5) | `SD_Rpg7` заменяет RocketLauncher, `MISG` | A покой; B огонь | правая на рукоятке; левая спереди необязательна | **покой** (правая) | 1 (+1 необязательно) |
| **РОКС-3**, огнемёт (6) | `SD_Roks3` заменяет PlasmaRifle, `PLSG` | A огонь; B остывание | обе, как у ППШ | **новых нет**: использует руки ППШ | 0 (+2 необязательно) |
| **Ручная «Катюша»** (7, секретная, D68) | `SD_HandKatyusha` заменяет BFG9000, `BFGG` | A заряд 20 тиков; B огонь | **обе**: левая на передней планке, правая на рукоятке | **покой**: новая левая; правая — от РПГ | 1 (+1 необязательно) |

**Хваты, которые используются повторно** (каждый генерируется только один раз):
- **Правая, хват с указательным пальцем на спуске** (`rpg7_ready_rh`): подходит и «Катюше».
- **Правая, на шейке деревянного приклада** (`ppsh_ready_rh`): подходит и РОКС-3 и, при необходимости, ИЖ.
- **Левая, держит горизонтальную палку снизу** (`ppsh_ready_lh`): подходит и РОКС-3. Для ИЖ угол меняется настолько, что нужен свой.

Как это решает Doom, для сравнения: во Freedoom `CHGG`, `MISG` и `PLSG` **не показывают рук** (оружие закрывает всё); `SHTG` B-D показывают правую руку, качающую цевьё, а `BFGG` лишь немного показывает торчащие пальцы. Мы показываем больше руки, как утверждённый ТТ-33 (D63).

---

## 3. Базовые настройки Fooocus (оба метода)

Запускайте `Z:\Fooocus\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\run_realistic.bat` и **меняйте то, что выделено жирным**, относительно пресета:

| Где | Настройка | Значение |
|---|---|---|
| Settings → Performance | Performance | **Quality** (60 шагов; именно это вы использовали сегодня) |
| Settings → Aspect Ratios | aspect ratio | **1152×896** (пресет поставляется с вертикальным 896×1152: смените) |
| Settings | Image Number | **4** |
| Settings | Random (seed) | ✔ отмечено |
| Styles | **снять отметку** | **Fooocus V2** и **Fooocus Photograph** |
| Styles | **отметить** (набрать "iphone" в *Search Styles*) | **Photo Iphone Photographic** + **Fooocus Negative** |
| Models | Base Model | `realisticStockPhoto_v20.safetensors` (уже установлена) |
| Models | Refiner | None |
| Models | LoRA 1 `SDXL_FILM_PHOTOGRAPHY_STYLE_V1` | **None** (или вес 0): она добавляет зерно и винтажный тон, а это загрязняет выделение |
| Advanced | Guidance Scale | **4** (пресет ставит 3; при 4 он лучше слушается длинного промпта; если кожа выходит пластиковой или перенасыщенной, вернитесь к 3) |
| Advanced | Image Sharpness | 2 (по умолчанию) |

**Почему эти изменения (я видел в вашем сегодняшнем логе, `Fooocus/outputs/2026-10-14/log.html`).** Вы просили *"plain flat light grey seamless studio background"*, а получились горы. Лог показывает причину: **Fooocus V2** добавил в промпт *"scenic, epic, surreal, futuristic, magical atmosphere…"*, а **Fooocus Photograph** добавил *"cinematic… hbo dark moody, grainy, vignette, vintage, found footage"*. Оба толкают к пейзажу и виньетированию. **Photo Iphone Photographic** добавляет лишь *"large depth of field, deep depth of field, highly detailed"*: резкое фото без боке и виньетки. **Fooocus Negative** добавляет в негатив список уродств рук. Установленные чекпойнты — `juggernautXL_v8Rundiffusion`, `realisticStockPhoto_v20` и `animaPencilXL_v500` (последний — аниме; не используйте его).

**Важное идёт в начало промпта.** SDXL уделяет больше внимания первым словам, поэтому каждый промпт начинается с руки, стороны экрана и хвата. Fooocus принимает веса вида `(right hand:1.3)`.

---

## 4. Метод B (ПОПРОБУЙТЕ ПЕРВЫМ): от кадра Doom к фото (идея CEO)

### 4.1 Почему он должен быть быстрее, и его риски
- **Преимущество:** входной кадр уже несёт **композицию, точку обзора, масштаб и положение на экране** Doom (масштаб D57 и расположение наших эскизов). Мы избавлены от угадывания камеры, а именно на этом провалились референсы 2 и 3 ледоруба (варежка, увиденная сзади, и хват наоборот).
- **Риск 1, получается пикселизованным:** SDXL может скопировать ступени пикселей. Поэтому входные изображения уже **сглажены** (бикубическая интерполяция плюс размытие в треть пикселя), а `pixelated, blocky` стоит в негативе.
- **Риск 2, изобретает шестой палец:** у наших эскизов толстые блочные пальцы, и контроль по границам может превратить один блок в два пальца. Решается понижением **Weight** PyraCanny и негативом (таблица в §4.6).
- **Риск 3, наследует цвета на маршруте Vary:** у 2D-эскизов коричневая перчатка и рукав с полосами тельняшки. PyraCanny смотрит только на границы и цветов не наследует; Vary наследует. Поэтому основной рецепт — PyraCanny.
- **При первом использовании PyraCanny, CPDS или ImagePrompt:** Fooocus **скачивает** управляющую модель из собственного репозитория (`huggingface.co/lllyasviel/misc`). Сегодня в `models/controlnet` лежит только `fooocus_ip_negative`. Загрузки: `control-lora-canny-rank128.safetensors` (PyraCanny), `fooocus_xl_cpds_128.safetensors` (CPDS) и, для ImagePrompt, `clip_vision_vit_h.safetensors` плюс `ip-adapter-plus_sdxl_vit-h.bin`. Размеры **НЕ ПРОВЕРЕНЫ**: около 0,4 ГБ на управляющую модель и около 2-3 ГБ на пару для ImagePrompt. Это ваша машина: решаете вы. **Vary (Strong) ничего не скачивает.**

### 4.2 Правило лицензий (обязательное)
В качестве входных данных мы используем **только** спрайты из **Freedoom (BSD-3)** или **наши собственные кадры**. **НИКОГДА спрайты Doom от id Software** (`DOOM.WAD`, `DOOM2.WAD`): они коммерческие и не могут распространяться, а фото, полученное из них, тоже. Doom от id пригоден лишь как стилевой референс, глазами. Все входные данные из §4.3 происходят из `iwads/freedoom2.wad` или из `work/art/`.

### 4.3 Подготовленные входные изображения: `work/art/reference/doom_inputs/`
Все размером 1152×896 (соотношение сторон Fooocus), на **однотонном бледно-голубом небе**. `_index.png` показывает их все вместе. `_close` = обрезано вокруг оружия и рук, с увеличенными руками, **используйте его первым**. `_full` = весь экран Doom 320×200, когда нужна полная композиция.

| Оружие / поза | Основной вход (наш) | Происхождение | Альтернатива Freedoom (BSD-3) |
|---|---|---|---|
| **Калибровка** | `tt33_ready_ours_close.png` | `weapons_fd/tt33/SDTTA0`: утверждённый ТТ-33 (D63), с перекрашенными руками Freedoom | — |
| ППШ покой | `ppsh_ready_ours_close.png` | 2D-эскиз `SDPPA0` | `ppsh_ready_fd-CHGGA0_*` (без рук) |
| ИЖ покой | `izh_ready_ours_close.png` | 2D-эскиз `SDIZA0` | `izh_ready_fd-SHTGA0_*` (почти без рук) |
| ИЖ открыт | `izh_open_ours_close.png` | 2D-эскиз `SDIZD0` | `izh_open_fd-SHTGD0_*` (правая рука на цевье) |
| РПГ-7 покой | `rpg7_ready_ours_close.png` | 2D-эскиз `SDRLA0` | `rpg7_ready_fd-MISGA0_*` (без рук) |
| РОКС-3 покой | `roks3_ready_ours_close.png` | 2D-эскиз `SDRKA0` | `roks3_ready_fd-PLSGA0_*` (без рук) |
| «Катюша» покой | `katyusha_ready_ours_close.png` | 2D-эскиз `SDHKA0` | `katyusha_ready_fd-BFGGA0_*` (торчат пальцы) |
| Согласованность руки | `ref_hand_rh.png` | ваш `hand grabbing mirrored.png`, отражённый в правую руку (оригинал не тронут) | — |

Версии Freedoom почти не показывают рук, поэтому **годятся только для мультяшного варианта или как композиция**; для рук всегда используйте наши. Входные данные пересоздаются командой `work/art/reference/doom_inputs/make_doom_inputs.py`.

### 4.4 Рецепт B1, основной: Image Prompt с PyraCanny
1. Отметьте **Input Image** (под промптом) и откройте вкладку **Image Prompt**.
2. Отметьте **Advanced** (под 4 окнами изображений), чтобы увидеть *Type*, *Stop At* и *Weight*.
3. **Окно 1:** перетащите `_close`-вход оружия. Type **PyraCanny**, **Stop At 0.5**, **Weight 0.8**.
4. **Окно 2** (необязательно, сохраняет объёмы и свет): **то же изображение**. Type **CPDS**, **Stop At 0.35**, **Weight 0.5**.
5. **Окно 3** (необязательно, чтобы рука была одинаковой у всего оружия): `ref_hand_rh.png` или ваше лучшее калибровочное фото (§4.7), когда оно у вас появится. Type **ImagePrompt**, **Stop At 0.5**, **Weight 0.35**. С большим весом просачиваются ледоруб и горы.
6. Базовые настройки из §3, промпт из §4.7 и **Generate** (4 изображения).

### 4.5 Рецепт B2, если B1 не соблюдает положение руки: Vary (Strong) плюс PyraCanny
1. **Input Image** → вкладка **Upscale or Variation** → перетащите тот же вход → выберите **Vary (Strong)** (это денойз 0,85).
2. **Advanced** → отметьте **Developer Debug Mode** → вкладка **Control** → отметьте **Mixing Image Prompt and Vary/Upscale**.
3. Вкладка **Image Prompt**, окно 1: тот же вход, **PyraCanny, Stop At 0.5, Weight 0.7**.
4. Тот же промпт. Если он слишком копирует эскиз (блоки, коричневая перчатка): в *Developer Debug Mode* поднимите **Forced Overwrite of Denoising Strength of "Vary"** до **0.9**. Если изобретает что-то лишнее, опустите до **0.75**.

### 4.6 Если что-то идёт не так (оба метода B)

| Симптом | Что изменить |
|---|---|
| Получается пикселизованным или со ступенями | PyraCanny **Stop At 0.35-0.4** и **Weight 0.6** (меньше времени привязки к границам, больше свободы рисовать кожу), уберите CPDS. В *Developer Debug Mode → Control → Canny*: Low **100**, High **200** (игнорирует мелкие границы) |
| Не соблюдает композицию (рука в другом месте, оружие повёрнуто) | PyraCanny **Stop At 0.6-0.7** и **Weight 1.0**, и добавьте CPDS. Больше *Stop At* = вернее границам, **но и блокам**: повышайте только при необходимости |
| Шестой палец или слипшиеся пальцы | **Weight 0.6**, сгенерируйте заново; негатив уже просит об этом. Если не проходит, отбросьте и перейдите на B2 или на Метод A |
| Коричневая перчатка или полосатый рукав (унаследованы от эскиза) | Бывает в B2: вернитесь на B1. В промпте `(bare skin:1.3)` и `(plain olive sleeve:1.2)` |
| Пейзаж на фоне | Проверьте, что **Fooocus V2** и **Fooocus Photograph** сняты; добавьте `(plain pale blue sky background:1.3)` |
| Получается зеркально | Нормально: сохраните с `_mirrored` |

### 4.7 Промпты Метода B (фото и мультфильм)

**Настройки варианта «фото»:** из §3 (realisticStockPhoto, стили **Photo Iphone Photographic + Fooocus Negative**).
**Настройки варианта «мультфильм»** (может пикселизоваться чище; присылайте всё, что получится): Base Model **`juggernautXL_v8Rundiffusion`**. Стили: отметьте только **Cel Shaded Art** и **снимите Fooocus Negative** (его негатив включает *"cartoon, anime, drawing, graphic"* и отменил бы стиль). Если выходит слишком плоско, добавьте **SAI Comic Book**. Guidance 4.

**Общий негатив B, фото** (вставляйте как есть):
```
pixelated, pixel art, blocky, jagged edges, low resolution, video game, 3d render, cgi, cartoon, drawing, painting, illustration, plastic skin, toy, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, extra arms, crossed arms, gloves, striped sleeve, wristwatch, ring, tattoo, fisheye, distorted perspective, motion blur, bokeh, depth of field, vignette, film grain, face, person, people, landscape, mountains, trees, buildings, text, watermark, logo, signature
```
**Общий негатив B, мультфильм:**
```
photo, photorealistic, pixelated, pixel art, blocky, jagged edges, noisy, blurry, gradient banding, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, crossed arms, gloves, striped sleeve, wristwatch, face, person, landscape, background details, text, watermark, logo, signature
```

Для варианта «мультфильм» замените начало фото-промпта *"first-person view photograph, …"* на **"cel shaded comic illustration, clean bold black outlines, flat colors with three shades per material, first-person view, …"** и уберите *"realistic photograph, 28mm lens"* из конца.

| № | Вход (окна 1 и 2) | Фото-промпт (английский) | Сохранить как |
|---|---|---|---|
| B0 калибровка | `tt33_ready_ours_close.png` | см. ниже | `tt33_ready_fromdoom_photo.png` / `_cartoon.png` |
| B1 ППШ | `ppsh_ready_ours_close.png` | см. ниже | `ppsh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B2 ИЖ покой | `izh_ready_ours_close.png` | см. ниже | `izh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B3 ИЖ открыт | `izh_open_ours_close.png` | см. ниже | `izh_open_fromdoom_photo.png` / `_cartoon.png` |
| B4 РПГ-7 | `rpg7_ready_ours_close.png` | см. ниже | `rpg7_ready_fromdoom_photo.png` / `_cartoon.png` |
| B5 РОКС-3 | `roks3_ready_ours_close.png` | см. ниже | `roks3_ready_fromdoom_photo.png` / `_cartoon.png` |
| B6 «Катюша» | `katyusha_ready_ours_close.png` | см. ниже | `katyusha_ready_fromdoom_photo.png` / `_cartoon.png` |

**B0, калибровка с ТТ-33 (сделайте первой: 1 партия, около 5 мин).** Мы уже знаем, как должно выглядеть, поэтому она скажет, работает ли Метод B. Если выходит хорошо, это фото становится **эталонной рукой** для окна 3 у остального оружия.
```
first-person view photograph, seen through the eyes of the shooter, (two bare hands:1.2) holding a black steel pistol straight ahead at the center of the frame with a two-handed grip, the right hand wrapped around the grip and the left hand cupping it from below, the thumbs side by side along the left of the frame, knuckles toward the camera, exactly five fingers on each hand, lightly tanned skin, olive drab cotton sleeves of a WWII Soviet army tunic at the bottom edge, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B1, ППШ-41**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage wooden submachine gun with a round drum magazine, the gun runs diagonally from the bottom right toward the center of the frame, the left hand comes in from the bottom left and holds the front of the gun from below, the right hand at the bottom right grips the wooden stock with the index finger on the trigger, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B2, ИЖ в покое**
```
first-person view photograph, seen through the eyes of a hunter, a side-by-side double barrel shotgun with a wooden stock held low, the two steel barrels point forward toward the center of the frame, (bare left hand:1.2) coming in from the bottom left holds the wooden fore-end from below, palm up, fingers curled over the far side, thumb along the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B3, ИЖ открыт (перезарядка)**
```
first-person view photograph looking down at a broken-open side-by-side double barrel shotgun held at waist height, the barrels tipped down on the hinge and the two empty chambers facing up, (bare right hand:1.2) pushing two red paper shotgun shells into the chambers with thumb and index finger, the left hand under the barrels holding the gun open, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain flat white snow on the ground as background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B4, РПГ-7**
```
first-person view photograph, seen through the eyes of a soldier, a long thick olive green launcher tube rests on the right shoulder and points forward, the tube runs diagonally from the bottom right toward the center of the frame, (bare right hand:1.2) at the bottom right grips the launcher with a firm fist, knuckles toward the camera, thumb wrapped around the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B5, РОКС-3**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage rifle-shaped flamethrower gun with a wooden stock and a long thin steel nozzle, the gun runs diagonally from the bottom right toward the left of the frame, the left hand comes in from the bottom left and holds the barrel from below, the right hand at the bottom right grips the wooden stock, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B6, ручная «Катюша»**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) carrying a heavy olive green steel rack of six rocket rails on the right shoulder, the left hand comes in from the bottom left and grips a horizontal steel bar at the front of the rack with an overhand grip, knuckles up, the right hand at the bottom right grips a vertical steel handle under the rack, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**Чек-лист Метода B** (в дополнение к общему из §6): рука **на том же месте, что во входном изображении**. Это настоящая кожа, без блоков. Рукав однотонный оливковый, **без полос**. ❌ Отбросьте, если пальцы повторяют блочный контур эскиза (сосиски), если вышла перчатка или если оружие закрывает пальцы, вместо того чтобы пальцы лежали поверх оружия.

---

## 5. Метод A (ЗАПАСНОЙ): только текст

Базовые настройки из §3, без Input Image. Необязательно, чтобы рука была одинаковой у всего оружия: **Input Image → Image Prompt**, окно 1 с `doom_inputs/ref_hand_rh.png` (или вашим лучшим калибровочным фото), **Type ImagePrompt, Stop At 0.5, Weight 0.35**. Требует загрузки из §4.1.

**Зачем предметы-заменители.** Если назвать "Soviet submachine gun", SDXL рисует военные сцены, солдат и пейзажи. Если дать ему **предмет той же формы и размера** (приклад охотничьего ружья, черенок метлы, трубу), рука держит так же, а фон остаётся чистым. Важен только хват.

**Общий негатив A, для ПРАВОЙ руки** (вставляйте целиком):
```
left hand, two left hands, arm entering from the left, crossed arms, extra fingers, six fingers, four fingers, fused fingers, missing fingers, long fingers, sausage fingers, claw, twisted wrist, broken wrist, extra hands, third hand, extra arms, floating hand, disconnected hand, cropped hand, cut-off fingers, out of frame, gloves, glove, wristwatch, bracelet, ring, tattoo, nail polish, striped sleeve, rolled-up sleeve, fisheye, distorted perspective, wide angle distortion, motion blur, bokeh, depth of field, vignette, film grain, dark, low light, face, person, people, head, legs, landscape, mountains, trees, buildings, clouds, busy background, text, watermark, logo, signature, label, cartoon, drawing, painting, illustration, 3d render, cgi, plastic skin
```
**Общий негатив A, для ЛЕВОЙ руки:** то же самое, заменив первые 3 записи на `right hand, two right hands, arm entering from the right`.

---

### A1. ППШ-41, правая рука на прикладе. `ppsh_ready_rh.png` (ОБЯЗАТЕЛЬНО; подходит и РОКС-3 и ИЖ)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's right hand:1.3) and forearm entering the frame from the bottom right corner, the right hand grips the narrow curved wooden wrist of an old hunting rifle stock, the stock runs diagonally from the bottom right corner up toward the center of the frame, firm trigger grip: the back of the hand and the four knuckles face the camera, thumb wrapped over the top of the wood, middle, ring and little fingers curled around the underside, index finger lying straight along the side of the wood, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand fills the lower right quarter of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Тыльная сторона кисти и 4 костяшки повёрнуты к камере · большой палец поверх дерева · указательный палец вытянут отдельно · оливковый рукав уходит через нижний край · однотонное небо.
❌ Ладонь к камере · указательный палец сжат, как в кулаке · дерево перед пальцами · вертикальный приклад.

### A2. ППШ-41, левая рука спереди. `ppsh_ready_lh.png` (ОБЯЗАТЕЛЬНО; подходит и РОКС-3)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand supports a thick round wooden broom handle from below, the handle is held level and points forward and slightly up toward the center of the frame like the front grip of a rifle, palm up under the wood, four fingers curled up around the far side so the fingertips show on top of the wood, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand in the lower left third of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Дерево проходит **над ладонью**, кончики пальцев выглядывают сверху · большой палец с ближней стороны · предплечье снизу слева.
❌ Рука, держащая сверху, как трость · дерево перед пальцами (это был провал референса 3) · палка, направленная на камеру.

### A3. ИЖ, левая рука под стволами. `izh_ready_lh.png` (ОБЯЗАТЕЛЬНО)
```
first-person point of view photograph, seen through the eyes of a hunter, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand holds the wooden fore-end of a side-by-side double barrel hunting shotgun from below, the two steel barrels point straight ahead to the center of the frame, the gun is low in the frame at the bottom center, palm up under the wood, four fingers curled around the far side, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Стволы идут **прямо в центр** · рука под цевьём, пальцы с дальней стороны.
❌ Помповый дробовик · рука на спуске · стволы, пересекающие экран из стороны в сторону.
*Необязательно:* `izh_ready_rh.png`, только если попросит PM: это A1 с *"a side-by-side double barrel hunting shotgun"* вместо *"an old hunting rifle"* и стволами прямо в центр.

### A4. ИЖ открыт, перезарядка. `izh_open_rh.png` (ОБЯЗАТЕЛЬНО; появляются обе руки, и это нормально)
Негатив: общий для правой руки **без** `third hand`, `extra hands` и `arm entering from the left` (левая появляется).
```
first-person point of view photograph looking down at waist height, seen through the eyes of a hunter, a broken-open side-by-side double barrel hunting shotgun held in the center of the frame, the barrels tipped down on the hinge and the two empty chambers facing up toward the camera, (the right hand:1.3) coming in from the bottom right pushes two red paper shotgun shells into the chambers between thumb and index finger, the left hand coming in from the bottom left holds the barrels from below to keep the gun open, exactly five fingers on each hand, natural proportions, bare skin, lightly tanned, short clean nails, both forearms covered by plain olive drab cotton sleeves of a WWII Soviet army tunic, the sleeves leave the picture at the bottom edge, plain flat white snow on the ground as the only background, soft daylight from the upper left, sharp focus on the hands, 28mm lens, natural perspective, realistic photograph
```
✅ Дробовик явно **открыт** (согнутый шарнир) · патроны между большим и указательным пальцами правой руки · оба рукава уходят через низ · однотонный снежный фон.
❌ Закрытый дробовик · больше двух рук · парящие патроны · рука, входящая сверху.

### A5. РПГ-7, правая рука на рукоятке. `rpg7_ready_rh.png` (ОБЯЗАТЕЛЬНО; подходит и «Катюше»)
```
first-person point of view photograph, seen through the eyes of the holder, a long thick olive green metal pipe rests on the right shoulder and points forward, the pipe runs diagonally from the bottom right corner up toward the center of the frame, (a single adult man's right hand:1.3) grips a black vertical pistol grip under the pipe at the lower right of the frame, the back of the hand and the knuckles face the camera, thumb wrapped around the left side of the grip, index finger curled on a trigger, the other three fingers wrapped around the grip, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Сжатый кулак вокруг **вертикальной** рукоятки · костяшки к камере · труба над рукой · рукав уходит через нижний правый край.
❌ Рука, берущая трубу сверху · дрель или инструмент вместо рукоятки · труба, направленная на камеру.
*Необязательно:* `rpg7_ready_lh.png`, левая рука спереди: A2 с заменой *"a thick round wooden broom handle"* на *"the underside of a thick olive green metal pipe"*.

### A6. Ручная «Катюша», левая рука на планке. `katyusha_ready_lh.png` (ОБЯЗАТЕЛЬНО; правая — из A5)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand grips a thick horizontal steel pipe at chest height with an overhand grip, the pipe crosses the frame from the left edge to the center, knuckles up and toward the camera, four fingers wrapped over and around the pipe, thumb under the pipe, wrist slightly bent down, the hand left of center, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Хват **сверху** (тыльная сторона кисти вверх, костяшки видны) · горизонтальная труба · предплечье снизу слева.
❌ Ладонь вверх · рука, висящая на турнике с вытянутой вверх рукой · вертикальная планка.

### A7. РОКС-3 (НЕОБЯЗАТЕЛЬНО: только если PM скажет, что руки ППШ не подходят)
`roks3_ready_rh.png` / `roks3_ready_lh.png`: A1 и A2 со следующими изменениями: *"held low at hip height, pointing slightly down toward the center of the frame"* вместо *"diagonally … up toward the center"*, а в A2 *"a long thin steel pipe"* вместо *"a thick round wooden broom handle"*.

---

## 6. Общий чек-лист (все изображения)

**✅ Оставить, если:**
- [ ] Это **настоящая рука** с **5 пальцами**, без слипшихся пальцев и с видимыми костяшками.
- [ ] Это **запрошенная рука**, входящая **со своей стороны** (или точное зеркало → `_mirrored`).
- [ ] **Предплечье и рукав уходят через нижний край** изображения (если рукав кончается внутри кадра, на экране виден обрез; это был провал референса 3).
- [ ] **Рукав оливковый, однотонный, хлопковый**, с манжетой на запястье: без перчатки, без полос, без часов.
- [ ] **Пальцы лежат поверх предмета** (предмет проходит *внутри* кулака, а не перед пальцами).
- [ ] **Однотонный светлый фон** (небо или снег) вокруг всей руки.
- [ ] Мягкий свет сверху слева, без жёстких теней на пальцах.
- [ ] Резкая рука, без боке, без зерна и без виньетки.

**❌ Отбросить, если:** вышла варежка (рука, увиденная сзади, референс 2) · хват наоборот (рука, увиденная снизу, референс 3) · есть скрещённая рука · есть третья рука · «рыбий глаз» искривляет предплечье · есть человек или лицо · есть текст или водяной знак.

---

## 7. Заметки для PM (CEO необязательно их читать)

- **Гипотеза, НЕ ПРОВЕРЕНО:** что Метод B даёт пригодные руки. Это зависит от того, прочитает ли PyraCanny наши 2D-эскизы как руки, а не как блоки. Калибровка B0 с утверждённым ТТ-33 решает это одной партией.
- **Гипотеза:** что фото одной руки (Метод A) хорошо сочетаются в `hand_ref.py` для двуручного оружия. Если `hand_ref.py` принимает только одну руку на фото, A4 (ИЖ открыт, две руки) может потребовать ручной обрезки.
- Если рука получилась зеркальной, свет, который мы просим сверху слева, после отражения оказывается сверху справа. Тона в `hand_ref.py` частично это поглощают; если будет заметно, CEO должен сказать.
- **Лицензии:** входные данные из Freedoom (BSD-3) или наши. Фото CEO — его собственные генерации SDXL. Каждому нужна своя строка в `docs/art/LICENSES.md`, если одобрена производная от него ячейка, как с ледорубом.
- Входные данные лежат в `work/art/reference/doom_inputs/` (gitignored, как и весь `work/`). Они создаются `make_doom_inputs.py` в той же папке: он читает IWAD, компонует на 320×200 со смещениями `grAb`, обрезает и масштабирует бикубической интерполяцией с размытием.
