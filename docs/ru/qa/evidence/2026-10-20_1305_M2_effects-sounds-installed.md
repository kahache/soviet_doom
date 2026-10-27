# Прогон в движке: установлены эффекты, звуки, музыка и тексты оболочки (PM, 2026-10-20 13:05)

Каноническая версия: `docs/qa/evidence/2026-10-20_1305_M2_effects-sounds-installed.md`.

Сборка: main c324f27 в чистом worktree, GZDoom g4.14.2, skill 3.

- `tools/route.py` **g3-auto, metro-critical, tankograd-critical, range-start:
  PASS**, ошибок в логе нет; ни `Unknown sound`, ни `Missing sprite`, ни
  `Script error` ни в одном логе маршрута (64 звука врагов, группы `$random`,
  новые звуки оружия и 7 дублей голосов — всё разрешается; `SD_HelpMenu` и
  ключи GameInfo загружаются).
- `2026-10-20_1305_M2_effects-sounds-installed.png`: РПГ-7 стреляет PG-7V с
  дымом и вспышкой взрыва SDPX на дальней двери; струя РОКС-3 нашего
  оранжевого пламени (синей плазмы Freedoom больше нет).
- Здесь не проверено (`-nosound`): прослушивание звуков и музыки
  (`currentmusic` требует включённого звука); это покрывает план приёмки.
