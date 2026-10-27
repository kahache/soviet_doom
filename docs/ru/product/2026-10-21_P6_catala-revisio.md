# P6 — каталанский как третий язык: лист ревью для CEO

Каноническая версия: `docs/product/2026-10-21_P6_catala-revisio.md` (английский).

Синхронизировано с оригиналом: 2026-10-27.

Дата: 2026-10-21 (ночная смена, D102). Автор: mod-engineer (перевод и
движок). Исходное решение: **D97** («V2: add Catalan», «V2: добавить
каталанский»). Статус: **черновик для вашего ревью**; ничего из этого ещё не
видели в движке (D26).

Что сделано:

- `src/lumps/LANGUAGE`: секция **`[ca]`** с **165 id**, у которых есть
  `[enu default]` и `[ru]` (163 из v1.0 плюс два новых этой ночью:
  `SD_LANGVAL_CA`, название языка в списке, и `SD_DEATH_PROMPT`, приглашение
  при смерти из D100, на всех трёх языках).
- Опция языка (Options → Soviet Doom → Language) теперь предлагает
  **Català**; она пишет `language ca`, как «Русский» пишет `language ru`.
- Строка состояния на каталанском: **MUNICIÓ, SALUT, ARMES, ARMADURA**, в
  `SDSBCA` / `SDARCA`. Превью (EN, RU, CA, ×3):
  `docs/art/previews/2026-10-21_2236_P6_statusbar-ca.png`. Утверждённые
  английская и русская строки не пересоздавались и не трогались.
- `README.md`: раздел на каталанском (что это, как играть, как включить
  каталанский) и упоминание каталанского везде, где перечислены языки.

Критерии, которым я следовал: стандартный центральный каталанский (soc, te без
акцента, l·l со средней точкой), **tu** (неформальное «ты») к игроку, короткие
сухие фразы, как в оригинале, никаких калек с испанского, имена собственные и
русские термины как в английском (Zarya-7, Tankograd, Vilanova, PPSh-41,
IZh-58, Katyusha, Zelyonka, Panzermensch, Vorwärts). Причастия в сообщениях о
смерти избегают согласования с родом игрока (действительный залог или «ha
caigut»).

Как проводить ревью: прочитайте сомнения (ниже, **Q1-Q23**, нумеруются отдельно
от решений D; в таблицах id помечен **Qn**), а затем таблицы. Чтобы изменить
текст, просто скажите мне «id → новый текст»; таблица генерируется из самого
`LANGUAGE`, так что вы читаете в точности то, что лежит в лампе.

## Что важнее всего решить

**Q3. РЕШЕНО PM (2026-10-21, ночью): акценты теперь нарисованы.**
art-director добавил **À È É Í Ï Ò Ó Ú Ç** (заглавные, как весь шрифт) в три
шрифта с помощью `tools/art/gen_font.py --catalan` (`CATALAN_ACCENTS`), так же,
как Ä Ö Ü (D37): 27 новых файлов, 339 существующих не изменились ни на один
байт. Акцент: буква в низком поле умляутов под двухстрочным штрихом (гравис с
наклоном влево, акут с наклоном вправо); Ç: C сверху и седиль снизу, внутри
поля. Смотрите в `docs/art/previews/2026-10-21_P6_font-ca.png` (настоящая
фраза `[ca]` в каждом шрифте, ×4). Долг `CATALAN_UNDRAWN_ACCENTS` в тестах
теперь пуст. **НЕ ПРОВЕРЕНО в движке** (D26): что GZDoom рисует строчные à è é
í ò ó ú ç этими файлами заглавных букв. Исходный текст сомнения:

Акценты ещё не были нарисованы (самая заметная проблема). Три шрифта мода
(`defsmallfont`, `bigfont`, `sdmenu`; алфавит C «Mashina», D24) содержат только
ASCII, кириллицу и немецкие буквы. **À È É Í Ï Ò Ó Ú Ç** отсутствуют (· есть).
Текст в `LANGUAGE` написан верно; согласно коду GZDoom, буква с акцентом,
которой нет в шрифте, рисуется базовой буквой («MUNICIO», «CONTINUARA»), но
это **не проверено на экране**. Предложение: art-director добавляет эти 9
заглавных в три шрифта с помощью `tools/art/gen_font.py`, как было сделано с
Ä Ö Ü (D37). Оценка: ~50k токенов, и вы утверждаете это, глядя на лист. Тесты
несут список этих букв как явный долг (`CATALAN_UNDRAWN_ACCENTS`).

**Q2. «Кириллические» буквы меню (D22) появляются и в каталанском.** Шрифт
меню рисует R, N, E, W и A как Я, И, Э, Ш, Д для любого латинского текста,
поэтому «NOVA PARTIDA» будет выглядеть как «ИOVД PДЯTIDД». D22 решалось для
английского; в каталанском это происходит лишь потому, что шрифт один.
Варианты: (a) оставить, в согласии с «латиницей, помнящей кириллицу»; (b)
каталанский без подстановки, что требует второго шрифта меню и выбора шрифта в
меню по языку (не знаю, позволяет ли это MENUDEF: **НЕ ПРОВЕРЕНО**).
Рекомендую (a).

**Q4. РЕШЕНО PM (2026-10-21, ночью): «TRIA LA MISSIÓ».** Поскольку Ó уже есть в
`sdmenu` (Q3), `SD_MNU_CHOOSEEPISODE` теперь говорит «TRIA LA MISSIÓ». Исходный
текст сомнения: «TRIA EL FRONT» вместо «TRIA LA MISSIÓ». Заголовок экрана
эпизодов использует шрифт меню, в котором нет Ó (а тест требует, чтобы у
каждой буквы был глиф). «TRIA EL FRONT» подходит военному тону; если Q3
выполнена (с Ó в `sdmenu`), я меняю на «TRIA LA MISSIÓ».

**Q12. РЕШЕНО (2026-10-21, ночью): знак паузы говорит
«PAUSA».** mod-engineer + art-director сгенерировали только каталанский
вариант командой `tools/art/gen_cursor.py --catalan --install` (та же плашка P2
из D48, в `SDMENU`, без системных шрифтов), 77×20, как остальные, установлен
как `assets/localized/textures/M_PAUSE.ca.png`; `SD_PAUSE_SIGN` в `[ca]`
указывает на `localized/textures/m_pause.ca.png`, как это делает `[ru]`.
Английская и русская плашки не изменились ни на один байт (они по-прежнему
задают холст; «PAUSA» на 3 px шире «PAUSE» и помещается внутри, с 5-6 px
красного с каждой стороны). Как говорит Q2 (a), шрифт меню рисует латинскую A
как Д: читается **«PДUSД»**, в согласии с «ИOVД PДЯTIDД» меню. Смотрите в
`docs/art/previews/2026-10-21_P6_pause-ca.png` (EN, RU, CA поверх MAP01, ×4).
**НЕ ПРОВЕРЕНО в движке** (D26): пауза с `language ca`. Если вы выберете Q2 (b),
этот знак пересоздаётся другим шрифтом. Исходный текст сомнения:

**Q12. Знак паузы всё ещё на английском («PAUSE»).** ROADMAP просит
каталанский знак. Он генерируется `tools/art/gen_cursor.py`, который этой ночью
правит другой агент (курсор), поэтому я его не трогал. Когда появится
каталанское «PAUSA», это одна строка в `[ca]` (`SD_PAUSE_SIGN`) плюс
`localized/textures/M_PAUSE.ca.png`.

**Q13. Титры об ИИ.** В каталанском сказано, что Claude сделал «els textos en
rus i català» (тексты на русском и каталанском). В английском и русском всё ещё
сказано только «русский текст»: я не менял их без вашего разрешения. Я
предлагаю для EN «sound, music, Russian and Catalan text.» (39 символов);
русский не помещается в 40 без разбиения строки. Аналогично `CREDITS.txt`
релиза (`tools/release.py`, `AI_DISCLOSURE`) и `README` (этот уже говорит об
этом).

## Сомнения по переводу

- **Q1. Tú или vostè.** Я использую tu везде («Has agafat», «Prem Y», «N'estàs
  segur?»), как большинство игр на каталанском; русский использует «Вы».
  Приглашение при смерти, которое вы просили, «Prem %s per continuar», уже было
  на tu.
- **Q5. Название.** «Soviet Doom» остаётся как есть (русский переводит его:
  «Советский Doom»). Альтернатива: «Doom Soviètic».
- **Q6. Doughboy** остаётся «Doughboy» (русский использует «Каска»). В
  каталанском «Casc» столкнулось бы с «Un casc d'acer» из бонуса брони.
- **Q7. Stormtrooper → «Soldat d'assalt híbrid».** Альтернатива: оставить
  «Stormtrooper» как имя собственное.
- **Q8. Сложность 5: «Heroi de la Unió Soviètica, pòstum».** Естественной
  формой была бы «…, a títol pòstum», но она занимает 310 px, а колонка
  допускает 288. Альтернатива, которая помещается: «Heroi de l'URSS, a títol
  pòstum».
- **Q9. Сложность 1: «Encara soc pioner»** (soc без акцента, норма 2017 года).
- **Q10. Сложность 4: «No passaran, camarades»**, каталанская форма лозунга
  (английский использует испанское «No pasaran»). Если вы предпочитаете
  испанское как цитату, это правка в одну строку.
- **Q11. Тренировочные площадки:** карта «Camp d'instrucció» (Training Ground,
  «Тренировочный лагерь») и эпизод «Camp de tir» (Practice Range, «Стрельбище»).
- **Q14. Финал: «L'interruptor cau.»** вместо «The breaker drops». Более
  активная альтернатива: «Abaixes l'interruptor.»
- **Q15. Смерти:** в действительном залоге («Un fuseller del Reich ha abatut
  %o»), чтобы причастие не согласовывалось с родом игрока.
- **Q16. Глаголы меню в повелительном наклонении** (CARREGA, DESA, SURT), как
  программы на каталанском (Softcatalà); «AJUDA» для READ THIS (русский
  использует «СПРАВКА»).
- **Q17. Подбор оружия: «Has agafat…»** Альтернатива: «Has trobat…».
- **Q18. Калибры с десятичной запятой и ×: «7,62×25»**, как в русском;
  английский использует «7.62x25».
- **Q19. «l'RPG-7»** с апострофом (читается «эрра-пе-хе»), стандартно.
- **Q20. «Un embenat de campanya»** для «A field dressing».
- **Q21. «Zarya-7 torna a ser a les nostres mans»**: английский говорит
  «yours» (ваша), русский «наша»; я следую русскому (наша), так же в финале с
  Танкоградом.
- **Q22. Выход 2:** цитата Клочкова (1941) на каталанском: «Rússia és
  immensa, però no hi ha on retrocedir: Moscou és al darrere.»
- **Q23. Строка состояния: «MUNICIÓ»** с акцентом, нарисованным одним пикселем
  над O (смотрите в превью). Альтернатива без акцента: «MUNICIONS»
  (помещается, теснее).

## Что PM должен проверить в движке (D26)

1. Запуск с 0 ошибок; Options → Soviet Doom → Language показывает четыре
   строки; выбор Català меняет главное меню, заголовок экрана опций и титры «на
   лету», а строка показывает «Català».
2. `language ca` в консоли и `language cat`: строка показывает Català.
3. В игре с `language ca`: строка состояния с MUNICIÓ / SALUT / ARMES /
   ARMADURA (H2 из MOD-SPEC 6.5.1 на каталанском), сообщение о подборе с
   акцентом и с ç («Has agafat el llançaflames ROKS-3!»: что строчные à/ç
   выходят с новым глифом, а не с базовой буквой, Q3), переход MAP01→MAP02
   («Cosmòdrom», «il·luminat»), экран эпизодов с «TRIA LA MISSIÓ» (Q4) и финал
   с «CONTINUARÀ».
4. Назад на английский и на Русский: всё как раньше.

## Таблицы

### Главное меню и экраны выбора (шрифт SDMENU; акценты с Q3)

| id | EN | CA |
|---|---|---|
| `SD_MNU_NEWGAME` **Q2** | NEW GAME | NOVA PARTIDA |
| `SD_MNU_OPTIONS` | OPTIONS | OPCIONS |
| `SD_MNU_LOADGAME` **Q16** | LOAD GAME | CARREGA PARTIDA |
| `SD_MNU_SAVEGAME` | SAVE GAME | DESA PARTIDA |
| `SD_MNU_READTHIS` | READ THIS! | AJUDA |
| `SD_MNU_QUITGAME` | QUIT GAME | SURT DEL JOC |
| `SD_MNU_CHOOSESKILL` | CHOOSE DIFFICULTY | TRIA LA DIFICULTAT |
| `SD_MNU_CHOOSEEPISODE` **Q4** | CHOOSE MISSION | TRIA LA MISSIÓ |

### Опции мода (Options → Soviet Doom)

| id | EN | CA |
|---|---|---|
| `SD_OPTMNU_TITLE` | Soviet Doom | Soviet Doom |
| `SD_OPTMNU_LANGUAGE` | Language | Idioma |
| `SD_OPTMNU_LANGHELP` | Applies immediately. Saved for the next session. | S'aplica a l'acte. Es desa per a la propera sessió. |
| `SD_LANGVAL_AUTO` | Automatic (system) | Automàtic (sistema) |
| `SD_LANGVAL_EN` | English | Anglès |
| `SD_LANGVAL_RU` | Russian | Rus |
| `SD_LANGVAL_CA` | Catalan | Català |

### Сложность

| id | EN | CA |
|---|---|---|
| `SD_SKILL_1` **Q9** | I am still a Pioneer | Encara soc pioner |
| `SD_SKILL_2` | I have seen worse winters | He vist hiverns pitjors |
| `SD_SKILL_3` | Not one step back | Ni un pas enrere |
| `SD_SKILL_4` **Q10** | No pasaran, comrades | No passaran, camarades |
| `SD_SKILL_5` **Q8** | Hero of the Soviet Union, posthumously | Heroi de la Unió Soviètica, pòstum |
| `SD_SKILL_5_CONFIRM` | The award is posthumous and the enemy dead do not stay dead. // Are you sure? | La condecoració és pòstuma, i aquí els enemics morts no es queden morts. // N'estàs segur? |

### Эпизоды и карты

| id | EN | CA |
|---|---|---|
| `SD_EP01_NAME` **Q5** | Soviet Doom | Soviet Doom |
| `SD_EP02_NAME` **Q11** | Practice Range | Camp de tir |
| `SD_MAP01_NAME` | Zarya-7 Cosmodrome | Cosmòdrom Zarya-7 |
| `SD_MAP02_NAME` | Metro-Bunker | Metro-búnquer |
| `SD_MAP03_NAME` | Tankograd | Tankograd |
| `SD_RANGE_NAME` **Q11** | Training Ground | Camp d'instrucció |
| `SD_PLAYER_NAME` | Sergeant Vilanova | Sergent Vilanova |

### Переходы между картами и финал (текстовый экран; «/» = перенос строки, «//» = пустая строка)

| id | EN | CA |
|---|---|---|
| `SD_MAP01_EXIT_TEXT` **Q21** | Zarya-7 is yours again. // The service lift drops into the dark, / past the last lit level, and keeps / going. Under the cosmodrome runs a / metro line, dug deep for the next war. // The invaders found it first. / You follow them down. | Zarya-7 torna a ser a les nostres mans. // L'ascensor de servei baixa cap a la / foscor, deixa enrere l'últim nivell / il·luminat i no s'atura. Sota el / cosmòdrom hi passa una línia de / metro, excavada ben fonda per a la / propera guerra. // Els invasors la van trobar primer. / Els segueixes cap avall. |
| `SD_MAP02_EXIT_TEXT` | The westbound tunnel climbs into / daylight at a goods spur. // Beyond the buffers stand the sheds / of a tractor works. The tracks in / the yard are too wide for tractors. // The workers have a name for it: / Tankograd. | El túnel cap a l'oest surt a la llum / del dia en un ramal de mercaderies. // Darrere els topalls s'alcen les naus / d'una fàbrica de tractors. Al pati hi ha / rodades massa amples per a tractors. // Els obrers li diuen d'una altra manera: / Tankograd. |
| `SD_END01_TEXT` **Q14** | The breaker drops. Behind you the / portal shrinks to a point of light / and goes out. // Tankograd is yours again: the line / stands still, and nothing more / comes through. // Those already through are marching / west, to Moscow. // TO BE CONTINUED | L'interruptor cau. Darrere teu, el / portal s'encongeix fins a un punt de / llum i s'apaga. // Tankograd torna a ser a les nostres / mans: la cadena s'atura, i ja no hi / arriba ningú més. // Els que ja havien passat marxen cap a / l'oest, cap a Moscou. // CONTINUARÀ |
| `SD_END02_TEXT` | The range is closed for the day. // The campaign begins from New Game. | El camp de tir tanca per avui. // La campanya comença a «Nova partida». |

### Оружие: название и сообщение о подборе

| id | EN | CA |
|---|---|---|
| `SD_TAG_ICEAXE` | Ice axe | Piolet |
| `SD_TAG_TOKAREV` | TT-33 Tokarev | Tokarev TT-33 |
| `SD_TAG_IZH` | IZh-58 double barrel | IZh-58 de dos canons |
| `SD_TAG_PPSH` | PPSh-41 | PPSh-41 |
| `SD_TAG_RPG7` | RPG-7 | RPG-7 |
| `SD_TAG_ROKS3` | ROKS-3 flamethrower | Llançaflames ROKS-3 |
| `SD_TAG_KATYUSHA` | Hand Katyusha | Katyusha de mà |
| `SD_PICKUP_ICEAXE` | An ice axe. | Un piolet. |
| `SD_PICKUP_TOKAREV` **Q17** | You got the TT-33 Tokarev! | Has agafat la Tokarev TT-33! |
| `SD_PICKUP_IZH` | You got the IZh-58 double barrel! | Has agafat l'escopeta de dos canons IZh-58! |
| `SD_PICKUP_PPSH` | You got the PPSh-41! | Has agafat el PPSh-41! |
| `SD_PICKUP_RPG7` **Q19** | You got the RPG-7! | Has agafat l'RPG-7! |
| `SD_PICKUP_ROKS3` | You got the ROKS-3 flamethrower! | Has agafat el llançaflames ROKS-3! |
| `SD_PICKUP_KATYUSHA` | You got the hand Katyusha. Prototype. Do not drop it. | Has agafat la Katyusha de mà. Prototip. No la deixis caure. |

### Боеприпасы, здоровье, броня и карта (сообщения о подборе)

| id | EN | CA |
|---|---|---|
| `AMMO_CLIP` **Q18** | 7.62x25 rounds | Cartutxos de 7,62×25 |
| `AMMO_SHELLS` | 12 gauge shells | Cartutxos del calibre 12 |
| `AMMO_ROCKETS` | PG-7V rounds | Projectils PG-7V |
| `AMMO_CELLS` | Fuel | Combustible |
| `SD_GOT_CLIP` | A magazine. 7.62x25. | Un carregador. 7,62×25. |
| `SD_GOT_CLIPBOX` | A box of 7.62x25. | Una caixa de 7,62×25. |
| `SD_GOT_SHELLS` | Four shells. 12 gauge. | Quatre cartutxos. Calibre 12. |
| `SD_GOT_SHELLBOX` | A box of 12 gauge shells. | Una caixa de cartutxos del calibre 12. |
| `SD_GOT_ROCKET` | One PG-7V round. | Un projectil PG-7V. |
| `SD_GOT_ROCKBOX` | A crate of PG-7V rounds. | Un caixó de projectils PG-7V. |
| `SD_GOT_CELL` | A canister of fuel. | Un bidó de combustible. |
| `SD_GOT_CELLPACK` | A full fuel tank. | Un dipòsit ple de combustible. |
| `SD_GOT_BACKPACK` | A paratrooper's pack. Everything you can carry! | Una motxilla de paracaigudista. Tot el que puguis carregar! |
| `SD_GOT_STIMPACK` **Q20** | A field dressing. | Un embenat de campanya. |
| `SD_GOT_MEDIKIT` | A first-aid box. | Una farmaciola. |
| `SD_GOT_HEALTHBONUS` | Zelyonka. | Zelyonka. |
| `SD_GOT_ARMORBONUS` | A steel helmet. | Un casc d'acer. |
| `SD_GOT_ARMOR` | A flak vest and a helmet. | Una armilla antibales i un casc. |
| `SD_GOT_MEGAARMOR` | A steel breastplate and helmet! | Una cuirassa d'acer i un casc! |
| `SD_GOT_MAP` | A commander's map case. The whole area is on it. | Un portamapes de comandant. Hi surt tota la zona. |

### Пропуска и двери

| id | EN | CA |
|---|---|---|
| `SD_PICKUP_BLUEPASS` | Blue pass. | Passi blau. |
| `SD_PICKUP_YELLOWPASS` | Yellow pass. | Passi groc. |
| `SD_PICKUP_REDPASS` | Red pass. | Passi vermell. |
| `PD_BLUECO` | You need a blue pass to activate this object | Necessites un passi blau per activar aquest objecte |
| `PD_YELLOWCO` | You need a yellow pass to activate this object | Necessites un passi groc per activar aquest objecte |
| `PD_REDCO` | You need a red pass to activate this object | Necessites un passi vermell per activar aquest objecte |

### Враги и Генерал

| id | EN | CA |
|---|---|---|
| `SD_TAG_RIFLEMAN` | Reich rifleman | Fuseller del Reich |
| `SD_TAG_TROOPER` | Legion trooper | Soldat de la Legió |
| `SD_TAG_STORM` **Q7** | Hybrid Stormtrooper | Soldat d'assalt híbrid |
| `SD_TAG_HOUND` | Reich hound | Gos del Reich |
| `SD_TAG_DOUGHBOY` **Q6** | Doughboy | Doughboy |
| `SD_TAG_PANZER` | Panzermensch | Panzermensch |
| `SD_TAG_PANZER_HEAVY` | Heavy Panzermensch | Panzermensch pesant |
| `SD_TAG_GENERAL` | The General | El General |
| `SD_GENERAL_ORDER` | The General: Vorwärts! | El General: Vorwärts! |
| `SD_OB_RIFLEMAN` **Q15** | %o was shot by a Reich rifleman. | Un fuseller del Reich ha abatut %o. |
| `SD_OB_TROOPER` | %o was blasted by a Legion trooper. | Un soldat de la Legió ha cosit %o a trets. |
| `SD_OB_STORM` | %o was burned by a Stormtrooper's bolt. | La descàrrega d'un soldat d'assalt ha cremat %o. |
| `SD_OBHIT_STORM` | %o was torn open by a Stormtrooper. | Un soldat d'assalt ha esbudellat %o. |
| `SD_OB_HOUND` | %o was run down by a Reich hound. | Un gos del Reich ha atrapat %o. |
| `SD_OB_DOUGHBOY` | %o was hit by a Doughboy's shell. | Un obús d'un Doughboy ha tocat %o. |
| `SD_OBHIT_DOUGHBOY` | %o was bitten by a Doughboy. | Un Doughboy ha mossegat %o. |
| `SD_OB_PANZER` | %o was shelled by a Panzermensch. | Un Panzermensch ha bombardejat %o. |
| `SD_OBHIT_PANZER` | %o was crushed by a Panzermensch. | Un Panzermensch ha aixafat %o. |
| `SD_OB_GENERAL` | %o fell to the General's salvo. | %o ha caigut sota la salva del General. |

### Смерти в мультиплеере (%o жертва, %k убийца)

| id | EN | CA |
|---|---|---|
| `SD_OB_ICEAXE` | %o met %k's ice axe. | %o ha topat amb el piolet de %k. |
| `SD_OB_TOKAREV` | %o was shot by %k's Tokarev. | %k ha abatut %o amb la Tokarev. |
| `SD_OB_IZH` | %o took both barrels from %k. | %o s'ha menjat els dos canons de %k. |
| `SD_OB_PPSH` | %o was cut down by %k's PPSh-41. | El PPSh-41 de %k ha segat %o. |
| `SD_OB_RPG7` | %o was blown apart by %k's RPG-7. | L'RPG-7 de %k ha fet miques %o. |
| `SD_OB_ROKS3` | %o burned under %k's ROKS-3. | El ROKS-3 de %k ha rostit %o. |
| `SD_OB_KATYUSHA` | %o caught %k's whole salvo. | %o s'ha empassat tota la salva de %k. |

### Приглашение при смерти (новое, v1.1) и пауза

| id | EN | CA |
|---|---|---|
| `SD_DEATH_PROMPT` | Press %s to continue | Prem %s per continuar |
| `SD_PAUSE_SIGN` **Q12** | M_PAUSE | localized/textures/m_pause.ca.png |

### Сообщения при выходе (каждое заканчивается «(Prem Y per sortir.)», здесь опущено)

| id | EN | CA |
|---|---|---|
| `SD_QUIT_01` **Q1** | Leaving your post, Sergeant? / The Urals will not hold themselves. | Abandones el teu lloc, sergent? / Els Urals no es defensaran tots sols. |
| `SD_QUIT_02` **Q22** | Russia is vast, but there is nowhere / to retreat. Moscow is behind us. | Rússia és immensa, però no hi ha on / retrocedir: Moscou és al darrere. |
| `SD_QUIT_03` | The five-year plan is not fulfilled. / Nobody leaves the shift early. | El pla quinquennal no s'ha complert. / Aquí ningú no plega abans d'hora. |
| `SD_QUIT_04` | The parade is only days away. / Who marches if you go home? | Falten pocs dies per a la desfilada. / Qui desfilarà si te'n vas a casa? |
| `SD_QUIT_05` | The Fourth Reich takes no days off. / Nor does the Liberty Legion. | El Quart Reich no fa festa. / La Legió de la Llibertat, tampoc. |
| `SD_QUIT_06` | The canteen closes at eight. / The war does not. | El menjador tanca a les vuit. / La guerra, no. |
| `SD_QUIT_07` | Comrade, the Party committee / will want an explanation. | Camarada, el comitè del Partit / voldrà una explicació. |
| `SD_QUIT_08` | Your absence is in the duty log. / In pencil, for now. | La teva absència ja consta al registre. / De moment, a llapis. |
| `SD_QUIT_09` | Barcelona waited forty years. / The Urals can wait one evening. | Barcelona va esperar quaranta anys. / Els Urals poden esperar un vespre. |
| `SD_QUIT_10` | The capitalists are counting on you / to go home early. | Els capitalistes compten que / te'n tornaràs aviat a casa. |
| `SD_QUIT_11` | Leave the radio on. / The next sentry gets lonely. | Deixa la ràdio encesa. / Al teu relleu li farà companyia. |
| `SD_QUIT_12` | Lenin is watching from the wall. / He does not look pleased. | Lenin et mira des de la paret. / I no fa cara de content. |
| `SD_QUIT_13` | Your shift ends / when the invaders do. | El teu torn s'acaba / quan s'acabin els invasors. |
| `SD_QUIT_14` | Hand your rifle in at the armoury / and sign for it twice. | Torna el fusell a l'armeria / i signa el rebut dues vegades. |
| `SD_QUIT_15` | The tea is still hot, Sergeant. / Stay a little longer. | El te encara és calent, sergent. / Queda't una estona més. |

### Титры (одна экранная строка на id, макс. 40 символов)

| id | EN | CA |
|---|---|---|
| `SD_CRED_TITLE` | Credits | Crèdits |
| `SD_CRED_H_TEAM` | Made by | Fet per |
| `SD_CRED_TEAM_1` | the Soviet Doom project | el projecte Soviet Doom |
| `SD_CRED_FAN_1` | A fan project, not affiliated | Un projecte de fans, sense cap vincle |
| `SD_CRED_FAN_2` | with id Software. | amb id Software. |
| `SD_CRED_TEAM_2` | Code: GNU GPL 3.0 or later | Codi: GNU GPL 3.0 o posterior |
| `SD_CRED_TEAM_3` | Art, sound, maps and text | Art, so, mapes i textos |
| `SD_CRED_TEAM_4` | under CC BY-NC-SA 4.0 | amb llicència CC BY-NC-SA 4.0 |
| `SD_CRED_H_MUSIC` | Music | Música |
| `SD_CRED_MUSIC_1` | The Internationale (title music): | La Internacional (música d'inici): |
| `SD_CRED_MUSIC_2` | composed by Pierre De Geyter (1888), | composta per Pierre De Geyter (1888), |
| `SD_CRED_MUSIC_3` | public domain; | domini públic; |
| `SD_CRED_MUSIC_4` | MIDI sequence by Jerry Engelbach, | seqüència MIDI de Jerry Engelbach, |
| `SD_CRED_MUSIC_5` | used under his attribution licence | usada amb la seva llicència |
| `SD_CRED_MUSIC_6` | (Wikimedia Commons, | d'atribució (Wikimedia Commons, |
| `SD_CRED_MUSIC_7` | File:Internationale_orch2.mid). | fitxer Internationale_orch2.mid). |
| `SD_CRED_MUSIC_8` | Radio: Ey, ukhnem and Kolokolchik; | Ràdio: Ey, ukhnem i Kolokolchik; |
| `SD_CRED_MUSIC_9` | MIDI sequences by Peter Gerloff, CC0. | seqüències MIDI de Peter Gerloff, CC0. |
| `SD_CRED_H_ENGINE` | Engine | Motor |
| `SD_CRED_ENGINE_1` | GZDoom (zdoom.org), GNU GPL 3.0, | GZDoom (zdoom.org), GNU GPL 3.0, |
| `SD_CRED_ENGINE_2` | by the GZDoom and ZDoom developers, | dels desenvolupadors de GZDoom i ZDoom, |
| `SD_CRED_ENGINE_3` | based on the Doom source code | basat en el codi font de Doom |
| `SD_CRED_ENGINE_4` | released by id Software. | publicat per id Software. |
| `SD_CRED_H_IWAD` | Game data | Dades del joc |
| `SD_CRED_IWAD_1` | Freedoom (freedoom.github.io), | Freedoom (freedoom.github.io), |
| `SD_CRED_IWAD_2` | by the Contributors to the Freedoom | dels col·laboradors del projecte |
| `SD_CRED_IWAD_3` | project, modified BSD licence. | Freedoom, llicència BSD modificada. |
| `SD_CRED_IWAD_4` | TT-33 hands: Freedoom's, recoloured; | Mans de la TT-33: Freedoom, repintades; |
| `SD_CRED_IWAD_5` | other placeholders read from the IWAD. | altres elements provisionals: de l'IWAD. |
| `SD_CRED_H_SOURCES` | Sources | Fonts |
| `SD_CRED_SRC_1` | Lenin poster after a photograph | Cartell de Lenin a partir d'una foto |
| `SD_CRED_SRC_2` | by Pavel Zhukov (1920), | de Pavel Zhukov (1920), |
| `SD_CRED_SRC_3` | public domain. | domini públic. |
| `SD_CRED_SFX_1` | Sound clips: CC0 packs by Kenney, | Sons: paquets CC0 de Kenney, |
| `SD_CRED_SFX_2` | rubberduck and Darsycho (OpenGameArt). | rubberduck i Darsycho (OpenGameArt). |
| `SD_CRED_SFX_3` | Voice reference: kurt, CC-BY 3.0. | Referència de veu: kurt, CC-BY 3.0. |
| `SD_CRED_H_AI` | Made with AI | Fet amb IA |
| `SD_CRED_AI_1` | Claude (Anthropic), in Claude Code: | Claude (Anthropic), a Claude Code: |
| `SD_CRED_AI_2` | design, maps, code, textures, sprites, | disseny, mapes, codi, textures, sprites, |
| `SD_CRED_AI_3` **Q13** | sound, music and the Russian text. | so, música i els textos en rus i català. |
| `SD_CRED_AI_4` | Google Gemini: source images for the | Google Gemini: imatges d'origen per a |
| `SD_CRED_AI_5` | weapons in hand and the sergeant's face. | les armes a la mà i la cara del sergent. |
| `SD_CRED_AI_6` | Fooocus / SDXL (local): hand references. | Fooocus / SDXL (local): models de mans. |
| `SD_CRED_AI_7` | Chatterbox (Resemble AI, local): | Chatterbox (Resemble AI, local): |
| `SD_CRED_AI_8` | most enemy voices. | la majoria de veus dels enemics. |

Id, не перечисленные (не читаются как текст или почти никогда не видны): `PD_BLUEC`, `PD_REDC`, `PD_YELLOWC`, `SD_SBAR_ARMS_IMAGE`, `SD_SBAR_IMAGE`.
