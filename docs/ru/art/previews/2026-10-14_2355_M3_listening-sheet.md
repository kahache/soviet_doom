# Лист прослушивания M3 (2026-10-14 23:55, sound-designer)

Каноническая версия: `docs/art/previews/2026-10-14_2355_M3_listening-sheet.md` (английский).

Одна страница для слуха CEO: `2026-10-14_2355_M3_listening-sheet.html`, 80 строк для оценки (OK / NO / ? + заметка) и 3 необязательные.
Счёт: оружие 31 (у 6 дубли A/B/C), враги 35, подложки 8, музыка 6 (титул `D_SDINTL`, MAP01 `D_SDM01` и черновик `D_SDM01E`, MAP02 `D_SDFUNR`, MAP03 `D_SDGATE`, RANGE `D_SDAMUR`); необязательные `D_SDTITL`, `D_SDRAD1`, `D_SDRAD2`.
Каждая строка проигрывает черновик, а под ним — то, что игра играет сегодня (ламп Freedoom, прочитанный из `iwads/freedoom2.wad`, или «тишина»).
Звук читается по относительному пути из `work/audio/sfx/` и `work/audio/preview/` (в gitignore): страницу нужно держать в `docs/art/previews/`.
Музыка отрендерена в OGG собственными `zmusic.dll` + `gzdoom.sf2` GZDoom (движок не запускался); `D_SDTITL` совпал с рендером движка на Mac сэмпл в сэмпл (корреляция 0,9999996).
Дубли B/C извлечены из превью оружия от 2026-10-13 и 2026-10-14; дубль A на этих страницах байт-в-байт идентичен `work/audio/sfx/weapons/ogg/`.
Ответы сохраняются в браузере (localStorage); «Copiar resultado» кладёт `OK / NO / ? / tomas / notas` в буфер обмена и в textarea.
Открыть: `Start-Process "C:\Users\littl\Desktop\Claude\soviet_doom\docs\art\previews\2026-10-14_2355_M3_listening-sheet.html"`
Не включено: 12 голосов врагов (D37, ждут дублей CEO).
