# MOD-SPEC — технический контракт мода

Владелец: `mod-engineer`. Контракт с `level-designer` и `art-director`: имена,
пути и лампы, которые ожидает движок. **Изменить его = обновить этот документ
раньше кода.** Статус: F0 проверено на GZDoom 4.14.2, 2026-10-09. Каноническая
версия: `docs/engine/MOD-SPEC.md`.

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
├── zscript.txt             вход ZScript: version + #include
├── zscript/sd/*.zs         классы ZScript (один класс на файл)
├── maps/MAP01.wad          один WAD на карту, лампы MAP01, TEXTMAP, ENDMAP
├── textures/  flats/       (пусто в F0) собственные текстуры стен и флэты
├── sprites/  sounds/  music/  graphics/  patches/  hires/   (пусто в F0)
└── (будущее) SNDINFO, ANIMDEFS, TEXTURES, GLDEFS, CVARINFO в корне
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
├── zscript/      → zscript/  (копируется как есть)
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
| `MAP01` | `SD_MAP01_NAME` = "Test Range" / «Полигон» | `SD_EP01_NAME` = "Soviet Doom" / «Советский Doom» | F0: комната 512×512, пол 0, потолок 128, свет 160, старт игрока в (256,256) лицом к +y. `next = "MAP01"` (без выхода). |

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

Неявно используемые элементы IWAD: актор игрока (DoomPlayer), его оружие и
HUD. В F0 не переопределяются.

## 6. ZScript

- Вход: `zscript.txt` с `version "4.12"` и только `#include`.
- Один класс на файл в `zscript/sd/`, имя `SD_<Thing>`.
- Обработчики событий регистрируются в `MAPINFO → GameInfo → AddEventHandlers`.

| Класс | Тип | Назначение |
|---|---|---|
| `SD_LoadReporter` | `EventHandler` | `WorldLoaded` → `Console.Printf("SOVIETDOOM loaded: …")`. Дымовой тест пайплайна. Не влияет на игру. |

Собственные DoomEdNum: **пока нет.** При появлении новых акторов будет
зарезервирован диапазон (предложение 14000–14999; НЕ ПРОВЕРЕНО, свободен ли в
GZDoom) и перечислен здесь.

## 7. Команды

```sh
python3 tools/build.py                       # → dist/sovietdoom.pk3
python3 tools/build.py --print-textmap MAP01 # показать сгенерированный UDMF
python3 -m unittest discover -s tests -v     # тесты сборки
tools/run.sh                                 # сборка + gzdoom + logs/gzdoom.log
MAP=MAP01 SKILL=4 IWAD=/path/doom2.wad tools/run.sh -nosound
tools/run.sh -nosound +vid_fullscreen 0 +screenshot_dir "$PWD/logs/shots" +"wait 140; screenshot; wait 35; quit"  # доказательства QA
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
