# Исследование: Soviet Doom на Android с экранным управлением (V3, 2026-10-24)

Каноническая версия: `docs/product/2026-10-24_V3_android-port-study.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

Датированный снимок. Автор: `mod-engineer`, по просьбе CEO («an Android
version with on-screen controls», «версия для Android с экранным управлением»).
Только исследование: **ничего не скачивалось, не устанавливалось, не
собиралось и не запускалось**; источники — веб-страницы и публичные
репозитории, прочитанные через GitHub API. Всё, что не подтверждено цитируемым
источником, помечено **НЕ ПРОВЕРЕНО**. Оценки даны в k токенов работы команды
(D69, ±50 %). Здесь ничего не решено: выбирает CEO.

Что мы поставляем сегодня (измерено на `dist/sovietdoom.pk3`, 2026-10-24): один
PK3 в **9,2 МБ**, 1 824 записи, ZScript `version "4.12"`, проверено на GZDoom
**g4.14.2** с `freedoom2.wad` 0.13.0 (28,8 МБ). Собственные файлы движка под
Windows — ~28 МБ (`gzdoom.exe` 11,4 МБ, `gzdoom.pk3` 3,1 МБ,
`game_widescreen_gfx.pk3` 5,6 МБ, `game_support.pk3` 2,4 МБ, DLL, soundfont в
3 МБ). В моде **нет GLDEFS и нет собственных динамических источников света**;
самые большие изображения — семь небес 1024×128, затем спрайты не более
232×144 (графика Gemini уменьшена до масштаба Doom); десять карт небольшие (не
более ~1 050 линий и ~265 объектов каждая, узлы строятся при загрузке).

## 0. Контекст, меняющий картину

- **GZDoom не выпускался после g4.14.2** (2025-05-03, [ZDoom/gzdoom releases](https://github.com/ZDoom/gzdoom/releases)).
  Большинство его разработчиков в октябре 2025 года сделали форк **UZDoom**;
  UZDoom 4.14.3 (ноябрь 2025) — это "a direct follow-up to GZDoom 4.14.2", а
  **UZDoom 5.0 вышел 2026-08-31** (5.0.3 — 2026-09-23)
  ([GamingOnLinux, ноябрь 2025](https://www.gamingonlinux.com/2025/11/gzdoom-successor-project-uzdoom-gets-a-first-preview-release/),
  [GamingOnLinux, август 2026](https://www.gamingonlinux.com/2026/08/gzdoom-successor-uzdoom-5-0-is-officially-out-now/),
  [UZDoom releases](https://github.com/UZDoom/UZDoom/releases)). Ни один из
  проектов не публикует сборку для Android.
- **Каждый живой GZDoom для Android происходит от одного человека: Эмиль
  Белангер** (Emile Belanger; Beloko Games / Open Touch Gaming, GitHub
  `emileb`). Его форк [emileb/gzdoom](https://github.com/emileb/gzdoom)
  (GPL-3.0, форк ZDoom/gzdoom) содержит ветку на каждую версию движка, среди
  них **`mobile_g4.14.2`**: 15 коммитов поверх тега `g4.14.2`, последний
  коммит 2026-09-02 ("Added vulkan mailbox…"), затронуто 112 файлов:
  makefile'ы ndk-build в `mobile/`, исправления GLES и Vulkan для телефонов,
  пути Android (сравнение `g4.14.2...emileb:mobile_g4.14.2`, прочитано через
  GitHub API). Есть также `uz_5.0`, `uz_5.0_pre`, `uz_mobile_4.15.x`. Слой
  касаний и оболочка приложения — отдельные репозитории (§1b).
- **Основной g4.14.2 уже содержит рендерер GLES**
  (`src/common/rendering/gles/`; мобильная ветка изменяет файлы, которые там
  есть). ПРОВЕРЕНО как код, не запускалось.

## 1. Маршруты

### Сводка

| Маршрут | Запускает наш PK3 как есть? | Сенсорное управление | Лицензия / можем ли мы распространять | Усилие (k) | Главный риск |
|---|---|---|---|---|---|
| **A. Delta Touch** (приложение за $2,99) + наш PK3 как мод | Очень вероятно: предлагает сборку **GZDoom 4.14.2** (сторонняя инструкция) и UZDoom 5.0.1 — НЕ ПРОВЕРЕНО с нашим PK3 | Да, зрелое, настраиваемое, гироскоп, 18 пользовательских кнопок | Мы поставляем только наш PK3 + инструкцию; сам Delta Touch платный, его оболочка не открыта (значки и сенсорная графика © Open Touch Gaming) | **~90** | Каждый игрок платит $2,99 и копирует файлы вручную; мы зависим от одного приложения |
| **B1. Собственный APK, форк открытой Android-оболочки** ([manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026)) с движком `mobile_g4.14.2` от emileb | Да, если соберём эту ветку (тот же движок, что на десктопе); НЕ ПРОВЕРЕНО | Да: MobileTouchControls от emileb (то же, что в Delta Touch) | Движок GPL-3.0 — нормально; **библиотеки касаний и «клея» имеют GPLv2-only или вообще никакой лицензии** (§1b) — нужно письменное разъяснение Эмиля Белангера | **~350** (+60 для Play) | Лицензия слоя касаний; апстримы из одного человека; отладка сборки на Windows |
| **B2. Собственный APK со своим слоем касаний** (движок emileb + SDL2 + оверлей, который пишем мы) | Да, тот же движок | Наше, нужно написать (стик, обзор перетаскиванием, кнопки) | Чисто: всё GPL-3.0 / zlib / LGPL, наше | **~700** | Объёмно; ветка движка всё ещё компилирует «клеевые» файлы Open Touch, которые пришлось бы заменить |
| **C1. Веб-сборка (WASM) в браузере телефона** | Нет: только экспериментальные порты (UZDoom 4.14.3, патчи не опубликованы) | Нет | GPL-3.0, но ничего пригодного для повторного использования не опубликовано | **≥ 800**, разведочно | Незрело; нет слоя касаний; производительность неизвестна |
| **C2. Другой движок с ZScript на Android** | Нет | — | — | — | Такого нет: ZScript существует только в линии GZDoom; LZDoom/QuestZDoom старее или только для VR |

### 1a. Delta Touch (Open Touch Gaming)

**Что это** (страница Google Play, прочитана 2026-10-24,
[com.opentouchgaming.deltatouch](https://play.google.com/store/apps/details?id=com.opentouchgaming.deltatouch&hl=en_US&gl=US)):
"Delta Touch [10 x Doom engine]" от Open Touch Gaming, **$2,99**, более 50
тыс. загрузок, 4,8 звезды, **обновлено 2026-09-16**. Перечисленные движки:
"GZDoom (v1.9.1 & v3.25 & v3.82 & v4.x)", "UZDoom (dev)", LZDoom, Zandronum 3.2
alpha, Chocolate, PrBoom+, Crispy, Doom Retro, DSDA, Doom64EX+, Dhewm3. В
последнем «What's new» сказано "UPT: UZDoom v5.0.1", "GZ/UZ: Auto fix OpenGL
shaders", "GZ/UZ: Optimised Vulkan for mobile". Возможности: "Highly
customizable touch screen controls", "18 custom buttons for GZDoom for mods",
геймпад, мышь и клавиатура (Android 8+), помощь в прицеливании гироскопом,
сохранённые раскладки касаний, встроенная клавиатура для консоли, "Custom UI to
easily select your wads and mods", "FreeDoom data included", ~60 МБ
дополнительной загрузки для музыкальных библиотек и Freedoom. Полный возврат
денег по запросу. Юридическая строка: "Icons and internal touch screen graphics
are copyright to Open Touch Gaming… This is a GPL source port". Пространство
имён пакета `com.opentouchgaming` совпадает с библиотекой AndroidCore от
emileb, так что GZDoom внутри — это форк emileb.

**Какой GZDoom.** Руководство пользователя для другой игры на GZDoom в Delta
Touch говорит нажимать кнопку версии "until the GZDoom version equals 4.14.2"
([руководство teletype](https://teletype.in/@easyapk_telegram/sharpshooter3d-android-guide), датировано
«May 19», год не указан). Вместе с веткой `mobile_g4.14.2` (§0) это означает,
что **4.14.2, очень вероятно, можно выбрать**; НЕ ПРОВЕРЕНО на телефоне. В
более старых сообщениях упоминается dev-сборка 4.10
([комментарий на itch.io](https://itch.io/post/8911704)).

**Загрузка внешнего PK3.** Да. То же руководство: задать вторичную папку
хранилища `OpenTouch/Delta`, положить файлы в `OpenTouch/Delta/mods`, выбрать
IWAD, нажать **MOD**, отметить файлы, запустить. Delta Touch добавляет `-file`
перед каждым путём мода; для длинных списков работают response-файлы
([тема в Steam](https://steamcommunity.com/app/2300/discussions/0/3095635055516492759),
[GBAtemp](https://gbatemp.net/goto/post?id=9738651)). Точные имена папок в
текущей версии НЕ ПРОВЕРЕНЫ.

**Можно ли упаковать нашу игру как «мод» для него?** Не существует
опубликованного формата пакета или intent запуска, который сделал бы Soviet
Doom отдельной записью; ничего не найдено. Что мы можем поставить:
`sovietdoom-<v>-android.zip` с `sovietdoom.pk3`, `freedoom2.wad` 0.13.0 (BSD,
чтобы игрок не зависел от того Freedoom, который включает Delta Touch; его
версия НЕ ПРОВЕРЕНА), необязательным мобильным оверлейным PK3 (§3),
лицензиями и `README-ANDROID.txt` на EN/RU/CA (D129) с шагами и скриншотами.
Сам Delta Touch мы включить в поставку не можем.

- **ZScript 4.14:** да, если игрок выберет сборку 4.14.2; под UZDoom 5.0.1,
  вероятно (мы фиксируем `version "4.12"`), НЕ ПРОВЕРЕНО.
- **Касания:** лучшее из доступного сегодня (стик, обзор, огонь, действие,
  колесо оружия, автокарта, меню, пользовательские кнопки).
- **Лицензия:** мы распространяем только свои файлы, ровно как сегодня. NC не
  затрагивается (мы ничего не берём; $2,99 — это продажа приложения Open Touch
  Gaming).
- **Усилие:** ~90 k: мобильный оверлей и строки (§3) 40, zip для Android в
  инструментах релиза с тестами 25, README-ANDROID EN/RU/CA 10, сессия PM на
  устройстве и её свидетельства 15.
- **Риски:** платная зависимость для каждого игрока; копирование файлов через
  средства выбора хранилища Android — самый трудный шаг для нетехнических
  друзей; Delta Touch может изменить папки или убрать сборку 4.14.2; мы не
  контролируем привязки по умолчанию и раскладку касаний (можем лишь описать
  их в документации).

### 1b. Сборка собственного APK

**Найденные открытые порты GZDoom на Android** (GitHub API, 2026-10-24):

| Репозиторий | Состояние | Движок | Касания | Лицензия |
|---|---|---|---|---|
| [emileb/gzdoom](https://github.com/emileb/gzdoom) | Активен (push 2026-09-03) | ветка на версию: **`mobile_g4.14.2`**, `uz_5.0` | в движке нет; компилирует `Clibs_OpenTouch/idtech1/touch_interface.cpp` и `gzdoom_game_interface.cpp` (его `mobile/Android_src.mk`) | GPL-3.0 |
| [emileb/MobileTouchControls](https://github.com/emileb/MobileTouchControls) | Активен (2026-10-23) | — | библиотека экранных элементов управления (джойстик, кнопки, сетки, рисование GL) | `License.txt`: "**under GPLv2 license.** Please contact me if you wish to use a different license." Без «or later»; в заголовках исходников нет уведомления |
| emileb/[Clibs_OpenTouch](https://github.com/emileb/Clibs_OpenTouch), [AndroidCore_OpenTouch](https://github.com/emileb/AndroidCore_OpenTouch), [SDL2_OpenTouch](https://github.com/emileb/SDL2_OpenTouch), [AudioLibs_OpenTouch](https://github.com/emileb/AudioLibs_OpenTouch), [SAFFAL](https://github.com/emileb/SAFFAL) | Активны | «клей», библиотека лаунчера (Java/Kotlin, minSdk 19, targetSdk 35), SDL, звук | раскладка касаний GZDoom живёт в Clibs | **файла лицензии нет** (GitHub сообщает, что её нет) |
| [emileb/Zeta_Touch](https://github.com/emileb/Zeta_Touch), Sigma_Touch, Psi_Touch | Активны | Raze, другие | те же библиотеки как подмодули | лицензии нет; собственная оболочка Delta Touch не опубликована |
| [manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026) | Один разработчик, последний push 2026-06-30, релизов нет | emileb `uz_5.0_pre` (UZDoom 5.0.0-pre); раньше `mobile_4.15.x` | MobileTouchControls + Clibs вендорены; настройки касаний на Compose | файл LICENSE — GPL-2.0 (при том что вендорится код GPL-3.0) |
| [dports/GZDA](https://github.com/dports/GZDA), GZDA2 | **Прекращён** (2024) | старый форк D-Touch | да | GPL-3.0 |
| [andrewrabert/GZDoom-Android](https://github.com/andrewrabert/GZDoom-Android), [Freedoom-for-Android](https://github.com/mkrupczak3/Freedoom-for-Android), F-Droid [net.nullsum.freedoom](https://f-droid.org/de/packages/net.nullsum.freedoom/) | Прекращены | GZDoom ~2.1 (без ZScript) | базовые | GPL |
| [DrBeef/QuestZDoom](https://github.com/DrBeef/QuestZDoom) | Активен (OpenXR, 2026-08) | основа LZDoom/GZDoom | **только VR-гарнитуры**, касаний нет | GPL-3.0 |

**manuelsiuro/GZDoom-Android-2026** — самая полезная отправная точка. Его
README говорит: лаунчер на Kotlin + Jetpack Compose; compileSdk 36, minSdk 23;
arm64-v8a и armeabi-v7a; выравнивание страниц 16 КБ (Android 15+); FMOD
удалён (OpenAL + FluidSynth); NDK r27, JDK 17; нативная сборка
`build_native.sh` (ndk-build), затем `./gradlew :doom:assembleDebug`;
предсобранные `.so` закоммичены; "rendering verified on a real device (Galaxy
S24…), 3D world + HUD + weapon sprites + touch controls"; эмулятор Android
показывает чёрный вид игры (значит, нужен настоящий телефон); конфигурация
подписи релиза всё ещё «planned». В нём также есть браузер idgames, редактор
карт и загрузчик WAD, которые мы бы убрали.

**Чем был бы B1:** форкнуть его вне нашего репозитория (новый репозиторий,
например `kahache/soviet_doom_android`, GPL-3.0); заменить движок на
`mobile_g4.14.2` от emileb (наш закреплённый движок, D3); урезать лаунчер до
одного экрана (Играть / Настройки / Лицензии) или вовсе убрать и запускать
движок напрямую с `-iwad freedoom2.wad -file sovietdoom.pk3` из ассетов APK;
раскладка касаний и привязки по умолчанию под наши действия; наш значок и имя;
подписанные релизные APK и AAB; предложение исходного кода GPL (коммит ветки
движка, репозиторий приложения, исходные архивы в релизе, как мы делаем для
v1.0, RELEASE §4.4).

**Что для этого нужно** (размеры приблизительные, НЕ ПРОВЕРЕНО): JDK 17 (~190
МБ); инструменты командной строки Android SDK + platform-tools (`adb`) +
platform 36 + build-tools (~0,4 ГБ); **NDK r27** (~0,7–1 ГБ загрузки, ~2–3 ГБ на
диске); Gradle и его кэш зависимостей (~0,5–1 ГБ); два дерева исходников
(emileb/gzdoom — ~220 МБ как git-репозиторий, GZDoom-Android-2026 ~230 МБ).
Android Studio (~1,2 ГБ) необязательна. **Итого ~3–5 ГБ загрузок, ~8–10 ГБ
диска.** CMake не нужен (мобильная сборка использует ndk-build `Android.mk`).
Первая нативная сборка GZDoom под две ABI: оценка 20–60 мин на этом ПК,
инкрементальные сборки — минуты (НЕ ПРОВЕРЕНО). Подпись: хранилище ключей,
созданное `keytool` из JDK, хранится у CEO вне репозитория с резервной копией
(потеря означает невозможность обновлений под тем же id приложения); в Play —
Play App Signing.

**Оценка размера APK (НЕ ПРОВЕРЕНО):** `.so` движка на ABI ~15–25 МБ, pk3
движка ~11 МБ, `freedoom2.wad` 28,8 МБ, наш PK3 9,2 МБ, soundfont 3 МБ, SDL /
OpenAL / ZMusic / FluidSynth ~5–10 МБ: **~55–75 МБ только для arm64**, около
+20 МБ с armeabi-v7a. В пределах лимитов Play.

- **ZScript 4.14:** да, это та же версия движка, что и в десктопной сборке.
- **Касания:** библиотека emileb, та же, что в Delta Touch, значит, то же
  качество.
- **Лицензия, блокер:** GZDoom (GPL-3.0) и MobileTouchControls («GPLv2»,
  «or later» не указано) были бы скомпонованы в один двоичный файл на стороне
  `libgzdoom`; код GPLv2-only и GPLv3 объединять нельзя
  ([список лицензий FSF](https://www.gnu.org/licenses/license-list.html#GPLv2)).
  У «клея» (Clibs, AndroidCore, SDL2_OpenTouch) лицензии нет вовсе, а это по
  умолчанию означает, что все права защищены. Delta Touch поставляет их вместе,
  так что автор очень вероятно подразумевает совместимую лицензию, но **мы не
  должны это предполагать**: CEO (или PM с его OK) должен написать Эмилю
  Белангеру с просьбой о "GPL-2.0-or-later or GPL-3.0" для этих репозиториев.
  Если он откажет, B1 превращается в B2.
- **Усилие B1:** ~350 k: настройка SDK/NDK и первая сборка 50, замена движка и
  исправления нативной сборки 80, урезание и брендинг лаунчера, автозапуск,
  ассеты 80, раскладка касаний и привязки по умолчанию 40, подпись,
  `tools/release_android.py`, исходники GPL и тесты 70, документы EN (RU при
  закрытии фазы) 30. Листинг в Play сверху (~60 k, §2).
- **Риски:** лицензия (см. выше); апстримы из одного человека (emileb,
  manuelsiuro); особенности сборки на Windows (форк документирует пути NDK для
  macOS); страницы 16 КБ и правила target-SDK меняются каждый год; эмулятор не
  показывает игру, так что для всего тестирования нужны телефон CEO и его
  время.

**B2 (собственный слой касаний):** тот же движок, но свой оверлей: Android
`View` над поверхностью SDL, рисующий левый стик, область обзора на правой
половине и кнопки, отправляющий события клавиш SDL и относительной мыши, так
что движок видит клавиатуру и мышь и не нуждается в «клее» Open Touch. Чистая
лицензия (всё наше, GPL-3.0; SDL zlib; OpenAL/FluidSynth LGPL). Но
`mobile/Android_src.mk` компилирует «клей» Open Touch
(`gzdoom_game_interface.cpp`, `android_jni.cpp`), так что нам пришлось бы
заменить и эту точку входа. ~700 k, и каждую деталь управления (мёртвые зоны,
чувствительность, мультитач, редактор раскладки) нам предстоит довести до ума
самим.

### 1c. Другие маршруты

- **Web/WASM.** Найдены только эксперименты: [blahm1dplays/uzdoom-wasm](https://github.com/blahm1dplays/uzdoom-wasm)
  (UZDoom 4.14.3 → WebGL2 в воркере, играется FreeDM MAP01, есть живая демо;
  серия патчей "intentionally not in this repo"; лицензия не указана) и заготовки
  вроде [HyperCrab2000/doom](https://github.com/HyperCrab2000/doom). Нет ввода
  касаниями, нет тестирования на мобильных, зависит от поддержки JSPI в
  браузере телефона (НЕ ПРОВЕРЕНО). Интересно для страницы «играть в браузере»
  когда-нибудь; не маршрут к игре на Android сейчас.
- **Другой движок с ZScript.** Такого нет: ZScript существует только в линии
  GZDoom (GZDoom, UZDoom, VKDoom на десктопе). LZDoom (основа QuestZDoom,
  3.8x) и Zandronum 3.2 — более старые движки и отвергнут `version "4.12"`
  (НЕ ПРОВЕРЕНО для уровня ZScript в Zandronum).
- **Геймпад вместо касаний:** оба маршрута, A и B, поддерживают
  Bluetooth-геймпады; дешёвый способ сделать плейтесты удобными, но не замена
  касаниям.

## 2. Рекомендация и MVP

**Два шага, первый почти бесплатный.**

1. **Сейчас: маршрут A как MVP (~90 k).** CEO покупает Delta Touch на свой
   телефон, мы даём ему `sovietdoom-<v>-android.zip`, и за одну сессию
   подтверждаем три вещи, от которых зависит каждый маршрут: PK3 загружается
   на сборке 4.14.2 от emileb с чистой консолью, частота кадров играбельна
   на MAP06 и MAP09 (самых тяжёлых картах), и что в нашем HUD, меню и текстах
   ломается на телефоне (§3). Всё исправленное здесь переносится на B1, который
   работает на том же форке движка. Друзья получают рабочий путь за $2,99.
2. **Затем, если CEO захочет бесплатное автономное приложение или листинг в
   Play: маршрут B1 (~350 k, + ~60 k для Play)**, начатый только после ответа
   Эмиля Белангера по лицензии; если он откажет, B2 (~700 k) или остаться на A.

**MVP, «играбельно на телефоне», означает:** игра запускается одним касанием
(A: из списка Delta Touch с отмеченным нашим PK3; B1: наш значок); альбомная
ориентация, полный экран; **левый стик** для движения и стрейфа, **перетаскивание
по правой половине** для обзора и поворота, **Огонь**, **Действие** (также
продолжает после смерти), **следующее/предыдущее оружие** плюс колесо оружия,
**Автокарта**, **Меню** (Esc) с сенсорной навигацией, постоянный бег включён;
сохранение и загрузка из меню, автосохранение при входе на карту сохранено;
три языка; музыка слышна. Прыжок и кнопка быстрого сохранения желательны. Гейт:
PM проходит MAP01 до выхода на телефоне на сложности 3 без читов, плюс
тренировочный полигон, и записывает лог консоли и скриншоты как свидетельство
(D26 всё ещё действует: агенты не запускают движок; на телефоне это руки CEO).

**Что команде нужно от CEO:**

| Для | Что | Стоимость |
|---|---|---|
| A и B | **Тестовый телефон: Samsung Galaxy M55** (CEO, 2026-10-24; характеристики в §4). От него ещё нужны: объём RAM (8 или 12 ГБ) и версия Android / One UI, которая стоит сейчас (Настройки → О телефоне → Сведения о программном обеспечении). Второй, более слабый телефон помог бы, но не обязателен | — |
| A | **Купить Delta Touch** в его аккаунте Google (его покупка, возвращаемая согласно листингу) | $2,99 |
| A | Скопировать один zip на телефон (USB или ссылка) и один раз пройти нашу инструкцию вместе с нами | его время, ~30 мин |
| B1 | **Письменное разъяснение лицензии от Эмиля Белангера** (сообщение, которое CEO отправляет или разрешает отправить) | — |
| B1 | **OK на загрузку и установку** JDK 17, инструментов Android SDK, NDK r27, зависимостей Gradle и двух деревьев исходников (§1b: ~3–5 ГБ загрузки, ~8–10 ГБ диска) | место на диске |
| B1 | На телефоне: включить параметры разработчика и отладку по USB, USB-кабель, чтобы работал `adb install` (изменение его настроек) | — |
| B1, в Play | **Аккаунт разработчика Google Play**: $25 один раз ([страница проверки разработчиков Android](https://support.google.com/android-developer-console/answer/16561738?hl=en); собственная страница Play с оплатой не читалась), подтверждение личности и, для личного аккаунта, созданного после 2023-11-13, **закрытое тестирование с ≥ 12 тестерами, подключёнными 14 дней подряд**, до производства ([справка Play Console](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB)); страница политики конфиденциальности; анкета возрастного рейтинга | $25 + 2 недели + 12 друзей |
| B1, вне Play | **APK на GitHub Releases** (наш канал уже есть) и/или **itch.io** (бесплатно). С 2027 года Google распространяет **проверку разработчиков на каждое приложение, устанавливаемое на сертифицированные устройства**, включая установленные вне магазина; она начинается 2026-09-30 лишь в нескольких странах (Индонезия, Сингапур, Таиланд по странице Google; в сообщениях также называют Бразилию). Бесплатный аккаунт «limited distribution» (без платы, без ID, **до 20 устройств**) покрывает друзей; более широкое распространение требует проверенного аккаунта за $25 даже вне Play; пользователи по-прежнему могут устанавливать непроверенные приложения через ADB или «advanced flow» (та же страница Google) | $0–25 |

**Позволяет ли CC BY-NC-SA Google Play?** Очень вероятно да, если приложение
**бесплатное, без рекламы, без внутриигровых покупок и без платного уровня**:
некоммерческая оговорка связывает то, что мы делаем с ассетами, а бесплатный
листинг не является "primarily intended for commercial advantage" (CC BY-NC-SA
4.0 §1(i)). То, что коммерческий магазин самого Google её распространяет, по
обычному прочтению не делает наше использование коммерческим. **НЕ ПРОВЕРЕНО
юристом.** GPL-3.0 в Play допустима (мы предлагаем исходный код, как на
GitHub).

**Отдельный риск Play: повязки со свастикой (D105).** Руководство Play по
декларациям просит разработчиков помечать нацистскую символику, и Play
блокировал историческую игру о Второй мировой в Германии, Австрии, Франции и
России из-за неё
([справка Google Play](https://support.google.com/googleplay/android-developer/answer/7022576?hl=en),
[Gameluster об Attentat 1942](https://gameluster.com/google-play-blocks-anti-nazi-game-over-nazi-references/)).
Россия — страна одного из наших трёх языков. Ожидайте как минимум блокировок по
странам или спор на ревью в Play; у GitHub/itch.io такого ревью нет. НЕ
ПРОВЕРЕНО для нашего случая.

## 3. Что должен адаптировать мод

Правило, которое мы соблюдаем: **один `sovietdoom.pk3` для каждой платформы.**
Отличия только для мобильных идут в небольшой **мобильный оверлейный PK3**
(`sovietdoom-mobile.pk3`, загружается после основного через `-file`, тот же
механизм, что у черновых оверлеев, MOD-SPEC §6.9) или в командную строку APK,
но никогда не в форк мода.

- **Рендеринг и производительность.** Риск меньше, чем опасались. Мод не
  добавляет GLDEFS и динамического света; текстуры и спрайты Gemini уже в
  масштабе Doom (самые большие — небеса 1024×128, спрайты ≤ 232×144, 1 542 PNG,
  5,7 МБ спрайтов), так что память текстур невелика; карты лёгкие. За чем
  следить: `lights.pk3`/`brightmaps.pk3` движка, если сборка загружает их
  автоматически; постобработка (bloom, tonemap, SSAO) выключена; выбор
  рендерера (GLES или Vulkan, в ветке emileb есть оба); масштабирование
  разрешения рендера на экранах с высокой плотностью. Это настройки движка: в A
  игрок задаёт их в Delta Touch (мы документируем значения по умолчанию); в B1
  APK передаёт их аргументами `+set` при запуске, что сохраняет ADR 004 (мод не
  пишет ни одного CVar). Измерить на телефоне: fps на MAP06 и MAP09 командой
  `stat fps` (НЕ ПРОВЕРЕНО, что в этой сборке команда именно такая).
- **Музыка.** Вся наша музыка — MIDI. На телефоне нет синтезатора MIDI Windows:
  движок использует FluidSynth с soundfont (Delta Touch скачивает его; B1 должен
  включить `gzdoom.sf2`, ~3 МБ, или использовать эмуляцию OPL из `fm_banks/`).
  Композиции прозвучат иначе, чем те, что одобрил CEO; `sound-designer`
  слушает на телефоне и выбирает устройство и soundfont (НЕ ПРОВЕРЕНО, на каком
  устройстве CEO одобрял под Windows).
- **HUD на маленьком экране.** `SD_StatusBar` рисует панель A из Doom,
  масштабированную по ширине; на телефоне 20:9 сенсорный стик и кнопки ложатся
  на её углы (патроны, лицо, оружие). Варианты для проверки: раскладка оставляет
  панель свободной; `screenblocks 11` (HUD на весь экран) из командной строки
  APK; `hud_scale`. Корректно ли HUD на весь экран показывает наши цифры и
  лицо — НЕ ПРОВЕРЕНО. Приглашение при смерти и знак паузы (RenderOverlay,
  BigFont) должны оставаться выше сенсорных кнопок.
- **Меню.** Главное меню и меню сложности в `SDMENU` достаточно крупные; меню
  опций (Options → Soviet Doom → Language, Credits) используют мелкий шрифт, и
  по ним может быть трудно попасть пальцем. Принимают ли меню GZDoom 4.14.2
  касания как щелчки мыши в этих сборках — НЕ ПРОВЕРЕНО; Delta Touch
  предлагает режим навигации по меню. Измерить на телефоне до каких-либо
  изменений.
- **Тексты, называющие клавиши.** `SD_DEATH_PROMPT` ("Press %s to continue")
  называет первую клавишу, привязанную к `+use`; при касаниях игрок нажимает
  кнопку, а не «E», и кнопка «Действие» в Delta Touch может вообще не быть
  клавишей (НЕ ПРОВЕРЕНО). Наш экран справки (F1, `SD_HelpMenu`) и README
  перечисляют управление клавиатурой. Мобильный оверлей даёт этим id сенсорные
  формулировки ("Tap USE to continue", страница справки для касаний) в
  `[enu default]`, `[ru]` и `[ca]` в той же задаче (D7, P6). То, что id
  LANGUAGE более позднего PK3 переопределяет более ранний, — документированный
  способ, которым моды заменяют строки движка, НЕ ПРОВЕРЕНО для наших id в
  g4.14.2.
- **Сохранения.** Сохранения работают как на десктопе (сохранение/загрузка из
  меню, автосохранение при входе на карту). Особенности телефона: Android может
  убить игру в фоне, поэтому кнопка быстрого сохранения в раскладке важна; в A
  сохранения живут в папках Delta Touch для каждой сборки движка, и смена
  сборки (4.14.2 ↔ UZDoom) может сделать их незагружаемыми; в B1 они лежат в
  хранилище приложения и **удаляются при удалении** (документировать; позже
  предложить экспорт). Сохранения между нашими версиями мода остаются такими же
  хрупкими, как на десктопе.
- **Язык.** Собственный переключатель мода (Options → Soviet Doom → Language)
  работает так же; следует ли `language auto` локали телефона в этих сборках —
  НЕ ПРОВЕРЕНО.
- **Инструменты релиза.** A: `tools/release.py` (или новый
  `tools/release_android.py`) делает `sovietdoom-<v>-android.zip` с PK3,
  оверлеем, `freedoom2.wad`, лицензиями, `README-ANDROID.txt` EN/RU/CA,
  `SHA256SUMS`, с тестами, как у портативных пакетов. B1: APK собирается в
  своём репозитории; наш релиз закрепляет его версию и прикрепляет его
  исходники GPL.

## 4. Тестовый телефон CEO: Samsung Galaxy M55

По [GSMArena](https://m.gsmarena.com/samsung_galaxy_m55-12896.php) (не по
Samsung): выпущен 2024-03-28; **Qualcomm Snapdragon 7 Gen 1** (SM7450-AB, 4
нм; 1× 2,4 ГГц + 3× 2,36 ГГц Cortex-A710, 4× 1,8 ГГц Cortex-A510); GPU
**Adreno 644**; 8 или 12 ГБ RAM; 6,7" 1080×2400 (20:9) 120 Гц AMOLED;
выпущен с Android 14 / One UI 6.1, указан как обновляемый до Android 16 / One
UI 8.5. Adreno 644 поддерживает **OpenGL ES 3.2 и Vulkan 1.1**
([Notebookcheck](https://www.notebookcheck.net/Adreno-644-vs-Adreno-618-vs-Adreno-660_11580_9900_10603.247598.0.html), сторонний источник). Не путать с M55s —
отдельной моделью с тем же чипом.

Что это значит для нас:

- **Это телефон верхнего среднего класса (64-бит, arm64-v8a)**, заметно выше
  того, что нужно нашим лёгким картам и графике в масштабе Doom; предупреждение
  Delta Touch о "high-end device" относится к модам вроде Brutal Doom. Ожидайте,
  что он потянет Soviet Doom с играбельной частотой на рендерере GLES (НЕ
  ПРОВЕРЕНО, пока не измерено).
- **Рендерер: начинать с OpenGL ES, а не с Vulkan.** Бэкенд Vulkan в GZDoom
  на мобильном драйвере Vulkan 1.1 — более рискованный путь: в ветке
  `mobile_g4.14.2` от emileb есть коммиты "Relax Vulkan requirments" и "Added
  Vulkan hardware buffer…, much faster on mobile now" (2026-08-31), а последние
  заметки Delta Touch говорят "GZ/UZ: Auto fix OpenGL shaders", что намекает на
  проблемы с шейдерами, зависящие от драйвера, на некоторых GPU. **Ни одного
  сообщения, относящегося именно к GZDoom на Adreno 644 или на Samsung, не
  найдено** (искали; нашлись лишь не связанные ошибки Adreno-Vulkan в других
  движках). Единственное публичное утверждение "verified on a real device" у
  открытого форка относится к Galaxy S24 с GPU **Exynos/Xclipse**, а не
  Adreno, так что M55 был бы первым тестом на Adreno для B1.
- **Экран 20:9:** классическая панель состояния 4:3 и сенсорные кнопки будут
  конкурировать за нижние углы (§3, HUD).
- **Samsung «Auto Blocker»** (One UI 6+) может блокировать установку извне
  магазинов Play/Galaxy и команды по USB. Samsung говорит, что он **по умолчанию
  выключен** ([редакционная статья Samsung](https://news.samsung.com/us/setting-boundaries-without-building-walls-choice-means-stronger-security-dr-seungwon-shin-samsung/),
  [9to5Google](https://9to5google.com/?p=593360)); если у CEO он включён, для
  `adb install` в B1 и любого APK с GitHub/itch.io его нужно выключить (его
  настройка). Изменила ли One UI 8.x значение по умолчанию — НЕ ПРОВЕРЕНО.
  Маршрут A — обычная покупка в Play, и это его не затрагивает.

## 5. «У меня когда-то был Doom на Android, значит, он существует и открыт»

CEO прав в том, что Doom на Android существует, но **не каждое приложение было
с открытым исходным кодом, и только одно живое приложение запускает GZDoom 4.x с
ZScript.** Кандидаты, от наиболее вероятного:

| Приложение | Кто / когда | Открытый код? | GZDoom 4.x + ZScript? | Подходит нам? |
|---|---|---|---|---|
| **Doom Touch → D-Touch → Delta Touch** (Play, платное, сегодня $2,99) | Эмиль Белангер, Beloko Games / Open Touch Gaming; первый релиз 0.9 в январе 2018, переименовывалось со временем ([фрагмент DoomWiki](https://doomwiki.org/wiki/Delta_Touch)) | **Частично.** Движки — форки GPL на GitHub (`emileb/gzdoom` GPL-3.0); библиотека касаний говорит GPLv2; оболочка приложения и «клей» опубликованы, но **лицензии не имеют**, собственный лаунчер Delta Touch не опубликован, а его значки и сенсорная графика © Open Touch Gaming (§1a, §1b) | **Да**: сборки GZDoom 4.x (4.14.2 очень вероятно) и UZDoom 5.0.1 | **Маршрут A** |
| **DOOM / DOOM II** от Bethesda (Play, 2019) | Nerve Software / id Software, «порт на Unity», запущен 2019-07-26; пользовательские дополнения на Android ([DoomWiki](https://doomwiki.org/wiki/Unity_port)) | **Нет**, проприетарный | **Нет** (собственный движок; дополнения WAD, без ZScript) | Нет |
| **Freedoom for Android** (F-Droid `net.nullsum.freedoom`, последний 0.4.3, 2024-05-14) | nvllsvm → mkrupczak3 → форк emileb как исходник ([F-Droid](https://f-droid.org/de/packages/net.nullsum.freedoom/), [форк emileb](https://github.com/emileb/Freedoom-for-Android)) | **Да**, GPL-2.0-only по F-Droid | **Нет**: эпоха GZDoom ~2.1 ([DoomWiki](https://doomwiki.org/wiki/Freedoom_For_Android)), до ZScript; сенсорное управление из раннего форка MobileTouchControls, репозитория которого больше нет | Нет (движок слишком старый); его преемник 2026 года — [manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026), основа маршрута B1 |
| **PrBoom For Android** (F-Droid `android.game.prboom`) | впервые портирован Владимиром Сильвой для эпохи G1 | **Да**, GPL-3.0 по F-Droid; F-Droid отмечает, что исходники апстрима для старой сборки "is no longer available" | **Нет** (PrBoom: ванильные/Boom-карты, без ZScript, без модов PK3) | Нет |
| GZDoom-Android / GZDA (nvllsvm, dports) | GitHub, прекращены в 2024 или раньше | Да, GPL | старые сборки, нет актуального ZScript | Нет |

Итак: если CEO играл на Android до 2019 года с сенсорной раскладкой, то это,
скорее всего, был **Doom Touch / D-Touch** от Beloko (сегодня Delta Touch) или
открытые сборки **Freedoom for Android / PrBoom**; начиная с 2019 года, возможно,
официальный DOOM от Bethesda. Какой именно, отсюда выяснить нельзя. **По-настоящему
открытые слишком стары для нашего ZScript; тот, что запускает наш движок, — это
Delta Touch, у которого движок открыт, а приложение нет.** Именно этот
пробел заполняет маршрут B1, и именно поэтому важен вопрос о его лицензии
(§1b).

## Источники

- Delta Touch в Google Play (прочитано во встроенном браузере, 2026-10-24): https://play.google.com/store/apps/details?id=com.opentouchgaming.deltatouch&hl=en_US&gl=US
- Выбор GZDoom 4.14.2 в Delta Touch и папки модов (сторонняя инструкция): https://teletype.in/@easyapk_telegram/sharpshooter3d-android-guide
- Сообщения о загрузке модов в Delta Touch: https://steamcommunity.com/app/2300/discussions/0/3095635055516492759 , https://gbatemp.net/goto/post?id=9738651 , https://itch.io/post/8911704
- Delta Touch на DoomWiki (только фрагмент поиска; страница отказалась загружаться): https://doomwiki.org/wiki/Delta_Touch
- Репозитории emileb (GitHub API): https://github.com/emileb/gzdoom (ветка `mobile_g4.14.2`), https://github.com/emileb/MobileTouchControls (`License.txt`), https://github.com/emileb/Clibs_OpenTouch , https://github.com/emileb/AndroidCore_OpenTouch , https://github.com/emileb/Zeta_Touch
- https://github.com/manuelsiuro/GZDoom-Android-2026 (README, LICENSE, дерево)
- https://github.com/dports/GZDA , https://github.com/andrewrabert/GZDoom-Android , https://github.com/mkrupczak3/Freedoom-for-Android , https://f-droid.org/de/packages/net.nullsum.freedoom/
- https://github.com/DrBeef/QuestZDoom ; история движка QuestZDoom: https://vrscout.com/news/doom-vr-mod-isabelle-companion-oculus-quest
- Релизы GZDoom и UZDoom: https://github.com/ZDoom/gzdoom/releases , https://github.com/UZDoom/UZDoom/releases , https://www.gamingonlinux.com/2025/11/gzdoom-successor-project-uzdoom-gets-a-first-preview-release/ , https://www.gamingonlinux.com/2026/08/gzdoom-successor-uzdoom-5-0-is-officially-out-now/
- WASM: https://github.com/blahm1dplays/uzdoom-wasm , https://github.com/HyperCrab2000/doom
- Проверка разработчиков Android: https://support.google.com/android-developer-console/answer/16561738?hl=en ; Бразилия в первой волне: https://www.androidauthority.com/android-sideloading-changes-timeline-3679204/
- Закрытое тестирование Play: https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB
- Play и нацистская символика: https://support.google.com/googleplay/android-developer/answer/7022576?hl=en , https://gameluster.com/google-play-blocks-anti-nazi-game-over-nazi-references/
- Galaxy M55: https://m.gsmarena.com/samsung_galaxy_m55-12896.php ; API Adreno 644: https://www.notebookcheck.net/Adreno-644-vs-Adreno-618-vs-Adreno-660_11580_9900_10603.247598.0.html ; Auto Blocker: https://news.samsung.com/us/setting-boundaries-without-building-walls-choice-means-stronger-security-dr-seungwon-shin-samsung/ , https://9to5google.com/?p=593360
- Старые приложения Doom: https://doomwiki.org/wiki/Unity_port , https://doomwiki.org/wiki/Freedoom_For_Android , https://f-droid.org/packages/android.game.prboom/ (фрагмент поиска; страница при загрузке вернула 404)
- Совместимость GPL: https://www.gnu.org/licenses/license-list.html#GPLv2 ; CC BY-NC-SA 4.0: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
