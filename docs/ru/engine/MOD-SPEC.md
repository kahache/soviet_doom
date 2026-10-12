# MOD-SPEC — технический контракт мода

Владелец: `mod-engineer`. Контракт с `level-designer` и `art-director`: имена,
пути и лампы, которые ожидает движок. **Изменить его = обновить этот документ
раньше кода.** Статус: арсенал F4 проверен на GZDoom 4.14.2, 2026-10-12
(пайплайн F0 проверен 2026-10-09).
Английский оригинал: `docs/engine/MOD-SPEC.md`.

Минимальный глоссарий (для новичков в моддинге Doom):

- **IWAD**: файл данных базовой игры (`doom2.wad` или `freedoom2.wad`). Без него
  GZDoom не запускается.
- **PK3**: `.zip` с фиксированной структурой папок, который GZDoom монтирует
  поверх IWAD. Формат мода.
- **Ламп (lump)**: именованный блок данных (не более 8 символов ASCII). В PK3
  каждый файл — ламп, названный по имени файла без расширения.
- **UDMF**: текстовый формат карты (`TEXTMAP`), используемый GZDoom; мы
  генерируем его из Python.
- **DoomEdNum**: число, которым редактор карт обозначает размещаемый объект;
  `1` — «Player 1 start».

## 1. Идентичность

| Поле | Значение | Примечание |
|---|---|---|
| Название мода | **Soviet Doom**, пакет `sovietdoom` | D1 (ждёт ратификации CEO) |
| Префикс | `SD` / `SD_` | классы ZScript, идентификаторы LANGUAGE, собственные лампы |
| Выходной файл | `dist/sovietdoom.pk3` | генерируется `tools/build.py`; никогда не правится вручную |
| Движок | GZDoom 4.14.2, `version "4.12"` в `zscript.txt` | D3 (ждёт ратификации) |
| Поддерживаемые IWAD | `freedoom2.wad` (предпочтительно, D2) и `doom2.wad` | см. §5 |

## 2. Структура PK3 (выход)

```
sovietdoom.pk3
├── MAPINFO                 карты, эпизоды, GameInfo (AddEventHandlers)
├── LANGUAGE                локализованный текст: [enu default] и [ru] (D7)
├── SNDINFO                 логическое имя звука -> ламп (F4)
├── zscript.txt             вход ZScript: version + #include
├── zscript/sd/*.zs         системы (обработчики событий, класс игрока)
├── zscript/weapons/*.zs    арсенал, один класс на файл (F4)
├── maps/MAP01.wad          один WAD на карту, лампы MAP01, TEXTMAP, ENDMAP
├── maps/MAP02.wad          инженерный тестовый полигон (F4)
├── textures/  flats/       собственные текстуры стен и флэты
├── sprites/  sounds/  music/  graphics/  patches/  hires/
└── (будущее) ANIMDEFS, TEXTURES, GLDEFS, CVARINFO в корне
```

Правила:
- Файлы в корне: имя ≤ 8 символов без расширения (сборка проверяет и падает иначе).
- Лампы карт: `MAP01`, `MAP02`, … (формат Doom II). Внутри WAD порядок
  фиксирован: маркер `MAPxx` (пустой), `TEXTMAP`, `ENDMAP` (пустой). Без лампов
  нод: GZDoom строит их при загрузке (проверено на G0).
- Карты не распаковываются: GZDoom читает `maps/MAP01.wad` напрямую.

## 3. Структура `src/` (вход сборки)

```
src/
├── lumps/        → корень PK3 (плоско)
├── zscript/      → zscript/  (копируется как есть; sd/ = системы, weapons/ = арсенал)
├── maps/MAP01/map.py   → maps/MAP01.wad  (генерируется; определяет lumps())
├── maps/MAPxx.wad      → maps/MAPxx.wad  (копируется как есть; выход UDB)
└── textures/ flats/ sprites/ sounds/ music/ graphics/ patches/ hires/ → те же пути
```

- Генерируемая карта (`map.py`) предоставляет `lumps() -> list[(name, bytes)]`,
  первый ламп — маркер с именем папки. Импортирует `sdbuild.udmf` для сборки
  `TEXTMAP` (`tools/sdbuild/udmf.py`).
- `level-designer` может сдать `.wad`, сделанный в Ultimate Doom Builder, в
  `src/maps/`; сборка упаковывает его без изменений. Имя файла = имя карты.
- Сборка детерминирована (фиксированные метки времени, отсортированные записи):
  одни и те же исходники дают идентичные байты (есть тест).

## 4. Карты

| Ламп | Заголовок (LANGUAGE) | Эпизод | Статус |
|---|---|---|---|
| `MAP01` | `SD_MAP01_NAME` = "Test Range" / «Полигон» | `SD_EP01_NAME` = "Soviet Doom" / «Советский Doom» | F0: комната 512×512, пол 0, потолок 128, свет 160, старт игрока в (256,256) лицом к +y. `next = "MAP01"` (без выхода). Владелец — `level-designer`, начиная с F3. |
| `MAP02` | `SD_MAP02_NAME` = "Engineering Test Range" / «Инженерный полигон» | нет (вне эпизода) | F4: зал 2048×768, потолок 128, свет 192, старт игрока в (160,384) лицом к +x. Семь видов оружия, четыре пула патронов, бочки и цели-плейсхолдеры. Запускается командой `MAP=MAP02 tools/run.sh`. Инженерная заготовка, **не артефакт дизайна**. |

Соглашения MAPINFO: `clearepisodes` + один эпизод на кампанию; заголовки карт
через `lookup`, заголовок эпизода через `name = "$ID"` (**`lookup` не
принимается внутри блока episode**, проверено, B1); `music = ""`, пока нет
музыки (проверено: тишина, без предупреждения); `sky1 = "SKY1"`.

## 5. Используемые ассеты IWAD

Мод не распространяет ничего из IWAD. Freedoom сохраняет имена лампов Doom II,
поэтому ссылка по имени работает на обоих. Каждая ссылка на IWAD должна быть
здесь и в индексе текстур `art-director` с пометкой «IWAD».

| Имя | Тип | Где используется | Проверка |
|---|---|---|---|
| `STARTAN2` | текстура стены 64×128 | MAP01, 4 стены | проверено на freedoom2.wad 0.13.0 (скриншот G0) |
| `FLOOR4_8` | флэт (пол) | MAP01 | проверено |
| `CEIL3_5` | флэт (потолок) | MAP01 | проверено |
| `SKY1` | текстура неба | MAPINFO `sky1` | загружается без ошибок |

Неявно используемые элементы IWAD: HUD и строка статуса, четыре пула
патронов (`Clip`, `Shell`, `RocketAmmo`, `Cell`) с их подборами и классы
оружия Doom, от которых наследуется арсенал. Начиная с F4 пешка игрока и все
семь видов оружия — **наши** (§6); оружие Freedoom заменено, а
супердробовик и кулак нельзя разместить на карте.

`MAP02` дополнительно размещает акторов Freedoom как **тестовые
заготовки**: взрывающуюся бочку (2035), зомби (3004), аптечку (2012), синюю
броню (2019), рюкзак (8) и ящики патронов 2046/2048/2049/17. Это
плейсхолдеры до появления бестиария (F5), и ни на одной карте кампании они
не встречаются.

## 6. ZScript

- Вход: `zscript.txt` с `version "4.12"` и только `#include`.
- Один класс на файл. `zscript/sd/` содержит системы, `zscript/weapons/` —
  арсенал. Имена классов с префиксом `SD_`.
- Обработчики событий регистрируются в `MAPINFO → GameInfo → AddEventHandlers`.
- Класс игрока объявляется в `MAPINFO → GameInfo → PlayerClasses`
  (пешка игрока не может использовать `replaces`).
- Каждое игровое число — именованная константа, в комментарии к которой
  написано, почему оно такое; обоснование живёт в `docs/engine/BALANCE.md`.

| Класс | Тип | Назначение |
|---|---|---|
| `SD_LoadReporter` | `EventHandler` | `WorldLoaded` → `Console.Printf("SOVIETDOOM loaded: …")`. Дымовой тест пайплайна. Не влияет на игру. |
| `SD_Player` | `DoomPlayer` | Сержант. Начинает с `SD_Tokarev`, `SD_Shovel`, 50 `Clip`. Объявляет слоты 1–7. |
| `SD_Shovel` | `Fist` *заменяет Fist* | Слот 1, ближний бой. |
| `SD_Tokarev` | `Pistol` *заменяет Pistol* | Слот 2, `Clip`. |
| `SD_Izh` | `Shotgun` *заменяет Shotgun* | Слот 3, `Shell`. Два ствола, затем перезарядка «переломкой» (`int barrels`). |
| `SD_Ppsh` | `Chaingun` *заменяет Chaingun* | Слот 4, `Clip`. |
| `SD_Rpg7` | `RocketLauncher` *заменяет RocketLauncher* | Слот 5, `RocketAmmo`. Стреляет `SD_Pg7Grenade`. |
| `SD_Roks3` | `PlasmaRifle` *заменяет PlasmaRifle* | Слот 6, `Cell`. Стреляет `SD_FlameBlob`. |
| `SD_HandKatyusha` | `BFG9000` *заменяет BFG9000* | Слот 7, `Cell`, 40 за залп. Стреляет шестью `SD_KatyushaRocket`. |
| `SD_Pg7Grenade` | `Rocket` | Кумулятивный снаряд. Не размещается на карте. |
| `SD_FlameBlob` | `Actor` | Снаряд огня, дальность 528 юнитов. Не размещается на карте. |
| `SD_KatyushaRocket` | `Rocket` | Ракета залпа, не вредит стрелку. Не размещается на карте. |

### 6.1 Номера редактора (DoomEdNums)

**Soviet Doom резервирует 21000–21999.** Прежнее предложение 14000–14999
было ошибочным и отозвано: GZDoom присваивает 14001–14067 классам
`AmbientSound` / `SoundSequence` и 14101–14165 — `MusicChanger` (проверено
2026-10-12 по <https://zdoom.org/wiki/Standard_editor_numbers>). Обоснование
и полная проверка — в
`docs/engine/adr/002-arsenal-and-editor-numbers.md`.

| Поддиапазон | Для |
|---|---|
| 21000–21019 | оружие |
| 21020–21039 | патроны и предметы |
| 21100–21199 | враги |
| 21200–21299 | декорации |

| Номер | Класс |
|---|---|
| 21001 | `SD_Shovel` |
| 21002 | `SD_Tokarev` |
| 21003 | `SD_Izh` |
| 21004 | `SD_Ppsh` |
| 21005 | `SD_Rpg7` |
| 21006 | `SD_Roks3` |
| 21007 | `SD_HandKatyusha` |

Убраны из игры (переведены в `None` в `DoomEdNums`): **82** супердробовик и
**2005** бензопила. Арсенал — ровно семь видов оружия (D13).

Номера присваиваются только в блоке `DoomEdNums` MAPINFO — единственном
доступном способе для класса ZScript.

### 6.2 Звуки (SNDINFO)

Код никогда не называет ламп напрямую; он называет логический звук. F4
привязывает каждое логическое имя к лампу Freedoom как плейсхолдер.
**`sound-designer` владеет правым столбцом**; заменить звук означает
положить `src/sounds/<LUMP>.ogg` в дерево файлов и отредактировать одну
строку `SNDINFO`.

| Логическое имя | Плейсхолдер F4 | Итоговый ламп для сдачи |
|---|---|---|
| `sd/weapon/shovel/swing` | `DSSAWUP` | `SDSHSWG` |
| `sd/weapon/shovel/hit` | `DSPUNCH` | `SDSHHIT` |
| `sd/weapon/tokarev/fire` | `DSPISTOL` | `SDTTFIR` |
| `sd/weapon/izh/fire` | `DSSHOTGN` | `SDIZFIR` |
| `sd/weapon/izh/reload` | `DSSGCOCK` | `SDIZRLD` |
| `sd/weapon/ppsh/fire` | `DSPISTOL` | `SDPPFIR` |
| `sd/weapon/rpg7/fire` | `DSRLAUNC` | `SDRPFIR` |
| `sd/weapon/rpg7/explode` | `DSBAREXP` | `SDRPEXP` |
| `sd/weapon/roks3/fire` | `DSFLAME` | `SDRKFIR` |
| `sd/weapon/katyusha/charge` | `DSBFG` | `SDHKCHG` |
| `sd/weapon/katyusha/fire` | `DSRLAUNC` | `SDHKFIR` |
| `sd/weapon/katyusha/burst` | `DSBAREXP` | `SDHKEXP` |

### 6.3 Спрайты, которые предстоит нарисовать (контракт с `art-director`)

Ламп спрайта Doom — это `ИМЯ` + буква кадра + цифра поворота, максимум 8
символов; `0` в качестве поворота означает «одна и та же картинка под любым
углом» — так устроены спрайты оружия на HUD. F4 работает на лампах
Freedoom; имена ниже **зарезервированы** для настоящей графики и свободны
от любого лампа в `freedoom2.wad` (проверено: в IWAD нет ни одного лампа,
начинающегося на `SD`).

| Оружие | В руках (HUD) | Вспышка выстрела | Подбор | Снаряд |
|---|---|---|---|---|
| Сапёрная лопата | `SDSH` A–E | — | `SDSP` A | — |
| ТТ-33 Токарева | `SDTT` A–E | `SDTF` A | `SDTP` A | — |
| ИЖ-58 | `SDIZ` A–F | `SDIF` A–B | `SDIP` A | — |
| ППШ-41 | `SDPP` A–B | `SDPF` A–B | `SDPQ` A | — |
| РПГ-7 | `SDRL` A–B | `SDRF` A–D | `SDRP` A | `SDPG` A–B, разрыв `SDPX` A–C |
| РОКС-3 | `SDRK` A–B | `SDKF` A–B | `SDKP` A | `SDFL` A–B, попадание `SDFX` A–E |
| Ручная «Катюша» | `SDHK` A–C | `SDHF` A–B | `SDHP` A | `SDKR` A–B |

Число кадров повторяет оружие Doom, которое каждый заменяет, так что
существующие конечные автоматы состояний не нужно будет править, когда
придёт арт — только имя из четырёх букв в каждой строке состояния.

## 7. Команды

```sh
python3 tools/build.py                       # → dist/sovietdoom.pk3
python3 tools/build.py --print-textmap MAP01 # показать сгенерированный UDMF
python3 -m unittest discover -s tests -v     # тесты сборки
tools/run.sh                                 # сборка + gzdoom + logs/gzdoom.log
MAP=MAP02 tools/run.sh                       # тестовый полигон арсенала F4
MAP=MAP01 SKILL=4 IWAD=/path/doom2.wad tools/run.sh -nosound
tools/run.sh -nosound +vid_fullscreen 0 +screenshot_dir "$PWD/logs/shots" +"wait 140; screenshot; wait 35; quit"  # доказательства QA
python3 tools/smoke.py --map MAP01 --skill 4 [--keep-evidence]  # сборка + самозавершающийся запуск GZDoom + разбор лога (код 0 = чисто)
python3 tools/check_pk3.py [--json] [--strict]   # статическая проверка PK3 без движка: лампы, WAD-файлы карт, используемые текстуры, палитра PNG, спрайты, лицензии, #include (код 0 = чисто)
```

`run.sh` ищет GZDoom в `/Applications/GZDoom.app/Contents/MacOS/gzdoom`,
`~/Applications/…` и `PATH` (или `GZDOOM=`), а IWAD — в `iwads/`,
`~/Library/Application Support/gzdoom/` и `$DOOMWADDIR` (или `IWAD=`),
предпочитая `freedoom2.wad`. Всегда пишет `logs/gzdoom.log`; `qa-engineer`
ищет в нём `Script error`, `Unknown texture`, `Missing sprite`: любое
совпадение — провал. `screencapture` в macOS не видит окно игры; используйте
команду `screenshot` движка.

## 8. Инструменты для арта

Виртуальное окружение Python в `.venv/` (в gitignore) с Pillow и numpy для
`tools/art/`. Создание: `python3 -m venv .venv && .venv/bin/pip install pillow numpy`.

## 9. Баланс

Каждое игровое число арсенала и причина, по которой оно такое, живёт в
`docs/engine/BALANCE.md`. Этот файл владеет *именами и структурой*; тот —
*значениями*. Код владеет и тем, и другим как именованные константы — если
документ и код расходятся, прав код, а документ — ошибка.

## 10. Известный технический долг

| № | Долг | Когда оплатить |
|---|---|---|
| T1 | Каждый спрайт и звук оружия — плейсхолдер Freedoom (§6.2, §6.3). | F4, как только `art-director` и `sound-designer` сдадут свои материалы |
| T2 | Подборы патронов всё ещё читаются как предметы Freedoom; четыре пула не переименованы в `LANGUAGE`. | F4 (дёшево) или F6 |
| T3 | `Player.DisplayName` — обычный литерал на английском, а не ссылка на `LANGUAGE`; не проверено, разрешает ли это свойство `$ID`. | F5 |
| T4 | Классы Freedoom `Chainsaw` и `SuperShotgun` всё ещё существуют; убраны только их номера редактора. | F6, если это когда-нибудь станет важно |
| T5 | Цифры DPS в `BALANCE.md` вычислены, а не измерены против настоящих врагов. | F5, когда у бестиария появятся очки здоровья |
| T6 | `MAP02` использует монстров и бочки Freedoom как цели. | F5, заменить на настоящий бестиарий |
| T7 | Пока нет `CVARINFO`; в арсенале нет ничего, что настраивал бы игрок. | когда это понадобится для игровой опции |
