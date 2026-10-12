# Soviet Doom

A GZDoom total conversion. The USSR of the 1970s is invaded by two allied
alien factions, Yankee and Nazi, united to defend capital. You are a Spetsnaz
sergeant who came to this country as a refugee child from Barcelona.

Status: F0 closed (pipeline verified), F1 lore ratified, F2 art direction next.
See `CLAUDE.md` for the operational summary, `docs/PRD.md` for decisions and
`docs/ru/` for the Russian mirror of all documentation.

```bash
python3 tools/build.py        # → dist/sovietdoom.pk3
tools/run.sh                  # needs GZDoom and freedoom2.wad in iwads/
python3 tools/verify.py auto  # verify what changed: fast (~7 s, no window),
                              # full (~30 s, boots GZDoom) or just the docs —
                              # it reads git, picks the level and says why
```

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request to `main`:
repo hygiene (no stray `.wad`/`.pk3`, nothing over 5 MB committed), then
`tools/build.py`, `tools/check_pk3.py` and the `tests/` suite, in that order,
failing at the first red step; the built PK3 is uploaded as a run artifact.

**What it does not run:** `tools/smoke.py`. That needs a real GZDoom install
and an IWAD, neither of which exists on the runner, and fetching Freedoom
(~23 MB) on every run isn't worth it yet. The engine smoke test stays the
committer's responsibility, locally, before every push — see
`docs/PIPELINE.md`, stage 5.

---

# Советский Doom

Тотальная конверсия для GZDoom. СССР 1970-х годов подвергается вторжению двух
союзных инопланетных фракций, янки и нацистов, объединившихся ради защиты
капитала. Вы — сержант спецназа, попавший в эту страну ребёнком-беженцем из
Барселоны.

Статус: F0 закрыта (пайплайн проверен), лор F1 ратифицирован, далее F2 —
арт-дирекшн. См. `CLAUDE.md` (операционная сводка), `docs/PRD.md` (решения)
и `docs/ru/` (русское зеркало всей документации).

## Непрерывная интеграция

`.github/workflows/ci.yml` запускается при каждом push и pull request в
`main`: сначала гигиена репозитория (никаких случайных `.wad`/`.pk3`, ничего
тяжелее 5 МБ в коммите), затем `tools/build.py`, `tools/check_pk3.py` и набор
тестов `tests/`, в этом порядке, с остановкой на первом же красном шаге;
собранный PK3 загружается как артефакт запуска.

**Чего CI не делает:** не запускает `tools/smoke.py`. Для этого нужен
настоящий GZDoom и IWAD, которых на раннере нет, а скачивать Freedoom
(~23 МБ) при каждом запуске пока не оправдано. Проверка в движке остаётся
обязанностью коммитящего, локально, перед каждым push — см. `docs/PIPELINE.md`,
этап 5.
