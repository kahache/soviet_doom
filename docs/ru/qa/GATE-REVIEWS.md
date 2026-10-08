# Обзоры гейтов

Один раздел на гейт. Гейты измеряются, а не обсуждаются. Каноническая
версия: `docs/qa/GATE-REVIEWS.md`.

## G0 — пайплайн работает (F0, MVP) — **PASS** (2026-10-09 00:37)

**Критерий:** GZDoom загружает `dist/sovietdoom.pk3` поверх Freedoom без
ошибок и без «Unknown» в логе, входит в MAP01, и игрок стоит внутри комнаты.

**Окружение:** Intel Mac (i5-5257U, Iris 6100), macOS 12.7.6, GZDoom g4.14.2
(Homebrew cask), freedoom2.wad 0.13.0 (SHA-256 сверен с подписанным CHECKSUM
релиза).

**Доказательства:**
- `docs/qa/evidence/2026-10-09_0037_F0_g0-gzdoom.log`: `adding
  dist/sovietdoom.pk3, 5 lumps` · `MAP01 - SD: Test Range` · `SOVIETDOOM
  loaded: map MAP01 (SD: Test Range)` (EventHandler на ZScript) · `Captured
  Screenshot_Doom_20261009_003742.png`. Ноль совпадений по
  `error|Unknown|missing|warning` после исправления MAPINFO.
- `docs/qa/evidence/2026-10-09_0037_F0_g0-map01-freedoom.png`: скриншот
  движка: комната с STARTAN2 / FLOOR4_8 / CEIL3_5 из Freedoom, игрок с
  пистолетом, HUD. Без HOM: ориентация linedef верна.
- Набор тестов `tests/`: **build 11/11** OK.
- CEO видел, как открылось окно с пустой картой (дословный вердикт,
  по-испански: «se abría y se veía el mapa vacío»).

**Находки во время гейта:**
- **B1 (закрыт):** `lookup = "..."` не принимается внутри блока `episode` в
  GZDoom 4.14.2 (`Script error ... Unknown property 'lookup'`). Исправлено на
  `name = "$SD_EP01_NAME"` (разрешается через LANGUAGE).
- `music = ""` даёт тишину без предупреждения (было НЕ ПРОВЕРЕНО; теперь проверено).
- `screencapture` в macOS не захватывает окно GZDoom (Vulkan/MoltenVK);
  визуальные доказательства снимаются командой `screenshot` самого движка
  (`+screenshot_dir` + `+"wait N; screenshot; quit"`). Стандартный метод QA.

**Вердикт:** PASS.
