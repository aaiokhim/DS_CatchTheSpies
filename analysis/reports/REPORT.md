# Результаты поиска подозрительного поведения

_Отчёт собран автоматически скриптом `analysis/build_report.py` 2026-10-21 00:20 из файлов `analysis/output/`._

Методика признаков: `docs/SPY_FEATURES.md`.

## 1. Сводка по признакам

| Код | Признак | Сила | Людей | Случаев (сумма count) |
|---|---|---|---|---|
| A1 | Один документ у разных людей | сильный | 4 | 4 |
| A2 | Несколько документов у одного человека | сильный | 2 | 2 |
| A3 | Тот же рейс и дата, другой документ | сильный | 24 | 24 |
| A4 | Одна карта у разных людей | сильный | 13 | 13 |
| A5 | Один Pointz user_uid у разных людей | средний | 2 | 2 |
| A6 | Анонимный профиль форума раскрыт | слабый | 25588 | 25588 |
| A7 | Несовпадение пола | средний | 0 | 0 |
| B1 | Посадка без брони | средний | 0 | 0 |
| B2 | Бронь без посадки | слабый | 0 | 0 |
| B3 | Перелёт только в loyalty-источниках | средний | 0 | 0 |
| B4 | Один билет у разных людей | сильный | 0 | 0 |
| B5 | Много перелётов без даты рождения | слабый | 160 | 4575 |
| C1 | Невозможный маршрут | сильный | 0 | 0 |
| C2 | Аномально много перелётов | слабый | 3 | 124 |
| C3 | Короткие международные поездки | средний | 104 | 209 |
| C5 | Редкие направления | слабый | 32 | 67 |
| C6 | Рваная активность | слабый | 352 | 352 |
| D1 | Постоянные попутчики | средний | 4734 | 4736 |
| D2 | Общий PNR у разных людей | слабый | 0 | 0 |
| E1 | Много loyalty-карт / программ | слабый | 4725 | 18900 |
| E2 | Перекос источников | слабый | 2439 | 16073 |

Ещё не посчитаны: C4.

## 2. Категории

Топ внутри категории: все люди с сильным признаком (не меньше 10 строк); сортировка - по числу сильных признаков, затем средних, затем по числу разных признаков; люди с именем выше безымянных записей. Так слабые массовые признаки (A6, E1) не вытесняют сильные.

### A - Личность и идентификаторы

Людей хотя бы с одним признаком: 25625

| разных признаков | людей |
|---|---|
| 1 | 25617 |
| 2 | 8 |

Топ-19 (все люди с сильным признаком, но не меньше 10):

| person_id | имя | сильных | средних | A_flags_count | A_total_occurrences | A_triggered_features |
|---|---|---|---|---|---|---|
| P0019901 | ROMAN MASLENNIKOV | 1 | 0 | 2 | 2 | A4; A6 |
| P0047864 | GOLOVINA OLESIA | 1 | 0 | 1 | 1 | A4 |
| P0079348 | AMALIIA KUDRIAVTSEVA | 1 | 0 | 1 | 1 | A2 |
| P0103336 | GORDEI M. GLEBOV | 1 | 0 | 1 | 1 | A1 |
| P0106284 | GORDEI M. GLEBOV | 1 | 0 | 1 | 1 | A1 |
| P0114475 | AMALIIA N. KUDRIAVTSEVA | 1 | 0 | 1 | 1 | A2 |
| P0116211 | GORDEI MAKAREVICH GLEBOV | 1 | 0 | 1 | 1 | A1 |
| P0119448 | RAMIL ALBERTOVICH BUROV | 1 | 0 | 1 | 1 | A1 |
| P0293273 | OLESYA GOLOVINA | 1 | 0 | 1 | 1 | A4 |
| P0595640 |  | 1 | 0 | 1 | 1 | A4 |
| P0595641 |  | 1 | 0 | 1 | 1 | A4 |
| P0595642 |  | 1 | 0 | 1 | 1 | A4 |
| P0595643 |  | 1 | 0 | 1 | 1 | A4 |
| P0595644 |  | 1 | 0 | 1 | 1 | A4 |
| P0595645 |  | 1 | 0 | 1 | 1 | A4 |
| P0595646 |  | 1 | 0 | 1 | 1 | A4 |
| P0595647 |  | 1 | 0 | 1 | 1 | A4 |
| P0595648 |  | 1 | 0 | 1 | 1 | A4 |
| P0595649 |  | 1 | 0 | 1 | 1 | A4 |

### B - Бронирование / посадка / мили

Людей хотя бы с одним признаком: 160

| разных признаков | людей |
|---|---|
| 1 | 160 |

Топ-10 (все люди с сильным признаком, но не меньше 10):

| person_id | имя | сильных | средних | B_flags_count | B_total_occurrences | B_triggered_features |
|---|---|---|---|---|---|---|
| P0000573 | CHERNOVA SOFIIA | 0 | 0 | 1 | 35 | B5 |
| P0124948 | MARK PETROV | 0 | 0 | 1 | 35 | B5 |
| P0048094 | ANASTASIIA TITOVA | 0 | 0 | 1 | 34 | B5 |
| P0126566 | AGATA LITVINOVA | 0 | 0 | 1 | 34 | B5 |
| P0122013 | MAYYA GLUKHOVA | 0 | 0 | 1 | 33 | B5 |
| P0122342 | IRINA A LOBANOVA | 0 | 0 | 1 | 33 | B5 |
| P0001943 | DANIL I TITOV | 0 | 0 | 1 | 32 | B5 |
| P0008440 | MARK GRISHIN | 0 | 0 | 1 | 32 | B5 |
| P0019304 | BOGDAN LOGINOV | 0 | 0 | 1 | 32 | B5 |
| P0031877 | EROFEEV STEPAN | 0 | 0 | 1 | 32 | B5 |

### C - Время и география

Людей хотя бы с одним признаком: 491

| разных признаков | людей |
|---|---|
| 1 | 491 |

Топ-10 (все люди с сильным признаком, но не меньше 10):

| person_id | имя | сильных | средних | C_flags_count | C_total_occurrences | C_triggered_features |
|---|---|---|---|---|---|---|
| P0034531 | RADMIR SYCHEV | 0 | 1 | 1 | 3 | C3 |
| P0001767 | NEKRASOVA STEFANIIA | 0 | 1 | 1 | 2 | C3 |
| P0001817 | ARINA FEDOTOVA | 0 | 1 | 1 | 2 | C3 |
| P0002017 | MIKHAIL G. ZORIN | 0 | 1 | 1 | 2 | C3 |
| P0004031 | ALEXEY USOV | 0 | 1 | 1 | 2 | C3 |
| P0004140 | SVYATOSLAV ANISIMOV | 0 | 1 | 1 | 2 | C3 |
| P0005034 | MAKAROV NIKOLAY P | 0 | 1 | 1 | 2 | C3 |
| P0005059 | LARINA MIROSLAVA | 0 | 1 | 1 | 2 | C3 |
| P0005403 | LEONID M. TIKHOMIROV | 0 | 1 | 1 | 2 | C3 |
| P0005919 | NAZAR D. KOCHETOV | 0 | 1 | 1 | 2 | C3 |

### D - Совместные поездки и бронирования

Людей хотя бы с одним признаком: 4734

| разных признаков | людей |
|---|---|
| 1 | 4734 |

Топ-10 (все люди с сильным признаком, но не меньше 10):

| person_id | имя | сильных | средних | D_flags_count | D_total_occurrences | D_triggered_features |
|---|---|---|---|---|---|---|
| P0005296 | SAVVA GULIAEV | 0 | 1 | 1 | 1 | D1 |
| P0029474 | ADELINA KHOMIAKOVA | 0 | 1 | 1 | 1 | D1 |
| P0031791 | LEV NIKOLAEV | 0 | 1 | 1 | 1 | D1 |
| P0038455 | POLINA NIKITINA | 0 | 1 | 1 | 1 | D1 |
| P0049516 | MORGUNOVA STEFANIIA | 0 | 1 | 1 | 1 | D1 |
| P0050563 | IL'YA NECHAEV | 0 | 1 | 1 | 1 | D1 |
| P0051505 | DENIS ARTEMICH KARASEV | 0 | 1 | 1 | 1 | D1 |
| P0052711 | ROSTISLAV I. OREKHOV | 0 | 1 | 1 | 1 | D1 |
| P0058864 | AMALIIA D. SHAPOVALOVA | 0 | 1 | 1 | 1 | D1 |
| P0066627 | LILIIA T. TIKHOMIROVA | 0 | 1 | 1 | 1 | D1 |

### E - Loyalty-программы и профиль источников

Людей хотя бы с одним признаком: 7164

| разных признаков | людей |
|---|---|
| 1 | 7164 |

Топ-10 (все люди с сильным признаком, но не меньше 10):

| person_id | имя | сильных | средних | E_flags_count | E_total_occurrences | E_triggered_features |
|---|---|---|---|---|---|---|
| P0070946 | KARINA NAUMOVA | 0 | 0 | 1 | 20 | E2 |
| P0074841 | AKSENOV EGOR | 0 | 0 | 1 | 18 | E2 |
| P0079786 | GORDEEV VASILII | 0 | 0 | 1 | 18 | E2 |
| P0075001 | KONDRAT'EVA UL'YANA | 0 | 0 | 1 | 17 | E2 |
| P0068498 | KOLPAKOVA VERA | 0 | 0 | 1 | 16 | E2 |
| P0073134 | MADINA A. SOBOLEVA | 0 | 0 | 1 | 16 | E2 |
| P0078442 | KULIKOVA MILENA | 0 | 0 | 1 | 16 | E2 |
| P0080636 | ALEKSEI A. MAKEEV | 0 | 0 | 1 | 16 | E2 |
| P0066605 | IURII I. NIKOLAEV | 0 | 0 | 1 | 15 | E2 |
| P0067672 | EGOROV VLADISLAV | 0 | 0 | 1 | 15 | E2 |

## 3. Признаки подробно

### A1 - Один документ у разных людей (сильный)

Людей: 4

`A1_reason`: известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) - 4

Примеры:

| person_id | имя | A1_count | A1_documents | A1_other_people | A1_reason |
|---|---|---|---|---|---|
| P0103336 | GORDEI M. GLEBOV | 1 | 8248013778 | GORDEI MAKAREVICH GLEBOV; RAMIL ALBERTOVICH BUROV; БУРОВ РАМИЛЬ АЛЬБЕРТОВИЧ; ГЛ… | известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) |
| P0106284 | GORDEI M. GLEBOV | 1 | 8248013778 | GORDEI MAKAREVICH GLEBOV; RAMIL ALBERTOVICH BUROV; БУРОВ РАМИЛЬ АЛЬБЕРТОВИЧ | известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) |
| P0116211 | GORDEI MAKAREVICH GLEBOV | 1 | 8248013778 | GORDEI M. GLEBOV; RAMIL ALBERTOVICH BUROV; БУРОВ РАМИЛЬ АЛЬБЕРТОВИЧ; ГЛЕБОВ ГОР… | известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) |
| P0119448 | RAMIL ALBERTOVICH BUROV | 1 | 8248013778 | GORDEI M. GLEBOV; GORDEI MAKAREVICH GLEBOV; ГЛЕБОВ ГОРДЕЙ МАКАРЕВИЧ | известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) |

### A2 - Несколько документов у одного человека (сильный)

Людей: 2

`A2_same_type`: 1 - 2

`A2_found_by`: name+birth_date - 2

Примеры:

| person_id | имя | A2_count | A2_documents | A2_same_type | A2_found_by | A2_related_person_ids |
|---|---|---|---|---|---|---|
| P0114475 | AMALIIA N. KUDRIAVTSEVA | 1 | 1378965068 (internal); 5518372746 (internal); 630145095 (foreign) | 1 | name+birth_date | P0079348 |
| P0079348 | AMALIIA KUDRIAVTSEVA | 1 | 1378965068 (internal); 5518372746 (internal); 630145095 (foreign) | 1 | name+birth_date | P0114475 |

### A3 - Тот же рейс и дата, другой документ (сильный)

Людей: 24

`A3_kind`: namesakes - 24

Примеры:

| person_id | имя | A3_count | A3_kind | A3_flights | A3_documents | A3_sources |
|---|---|---|---|---|---|---|
| P0003349 | ADEL VASILEV | 1 | namesakes | SU6290 2017-01-01 | 1193568854 (рожд. ?; отч. A); 3208548917 (рожд. ?; отч. L) | sirena |
| P0020044 | GOROKHOVA TAISIIA | 1 | namesakes | SU1212 2017-02-22 | 6007623748 (рожд. 1999-01-31; отч. S); 9898891869 (рожд. 1992-11-01; отч. A) | sirena |
| P0121279 | БЕЛОВА АМАЛИЯ ИЛЬДАРОВНА | 1 | namesakes | SU1435 2017-01-16 | 5256826616 (рожд. 1977-09-28; отч. I); 8183154430 (рожд. 1981-09-17; отч. R) | boarding_data; sirena |
| P0118358 | LEV ARTEMOV | 1 | namesakes | SU1523 2017-01-05 | 4984610985 (рожд. 1970-12-18; отч. G); 9870525649 (рожд. 1970-05-08; отч. D) | boarding_data; sirena |
| P0111699 | SOFIA AMIROVNA DOBRYNINA | 1 | namesakes | SU5611 2017-01-13 | 2080777803 (рожд. 2000-09-17; отч. V); 6278501266 (рожд. 1974-03-25; отч. A) | boarding_data; sirena |

### A4 - Одна карта у разных людей (сильный)

Людей: 13

Примеры:

| person_id | имя | A4_count | A4_cards | A4_other_people | A4_n_records |
|---|---|---|---|---|---|
| P0019901 | ROMAN MASLENNIKOV | 1 | FB 139888197 | OLESIA GOLOVINA; OLESYA GOLOVINA | 10 |
| P0047864 | GOLOVINA OLESIA | 1 | FB 139888197 | ROMAN MASLENNIKOV | 9 |
| P0293273 | OLESYA GOLOVINA | 1 | FB 139888197 | OLESIA GOLOVINA; ROMAN MASLENNIKOV | 2 |
| P0595640 |  | 1 | FB 139888197 | OLESIA GOLOVINA; OLESYA GOLOVINA; ROMAN MASLENNIKOV | 1 |
| P0595641 |  | 1 | FB 139888197 | OLESIA GOLOVINA; OLESYA GOLOVINA; ROMAN MASLENNIKOV | 1 |

### A5 - Один Pointz user_uid у разных людей (средний)

Людей: 2

Примеры:

| person_id | имя | A5_count | A5_user_uids | A5_other_people | A5_has_cards |
|---|---|---|---|---|---|
| P0029586 | STANISLAV KONDRATOV | 1 | 708343118 | YULIYA KORSHUNOVA | 1 |
| P0584736 | YULIYA KORSHUNOVA | 1 | 708343118 | STANISLAV KONDRATOV | 0 |

### A6 - Анонимный профиль форума раскрыт (слабый)

Людей: 25588

Примеры:

| person_id | имя | A6_count | A6_forum_profiles | A6_named_sources |
|---|---|---|---|---|
| P0000001 | RUMYANTSEV VIKTOR | 1 | forum:0 | boarding_passes |
| P0044433 | KIREEVA LIANA | 1 | forum:44432 | boarding_data; boarding_passes; pointz; sirena |
| P0044429 | POLINA USTINOVA | 1 | forum:44428 | boarding_passes; pointz |
| P0044422 | RAMIL' S NIKIFOROV | 1 | forum:44421 | boarding_passes |
| P0044419 | LIUBOV I. MIKHAILOVA | 1 | forum:44418 | boarding_data; boarding_passes; pointz; sirena |

### A7 - Несовпадение пола (средний)

Людей: 0

### B1 - Посадка без брони (средний)

Людей: 0

### B2 - Бронь без посадки (слабый)

Людей: 0

### B3 - Перелёт только в loyalty-источниках (средний)

Людей: 0

### B4 - Один билет у разных людей (сильный)

Людей: 0

### B5 - Много перелётов без даты рождения (слабый)

Людей: 160

Пороги: `B5_threshold` = 26.0

Примеры:

| person_id | имя | B5_count | B5_sources |
|---|---|---|---|
| P0000573 | CHERNOVA SOFIIA | 35 | boarding_passes; forum; pointz; sirena; skyteam |
| P0124948 | MARK PETROV | 35 | boarding_passes; pointz; sirena; skyteam |
| P0048094 | ANASTASIIA TITOVA | 34 | boarding_passes; forum; sirena; skyteam |
| P0126566 | AGATA LITVINOVA | 34 | boarding_passes; pointz; sirena; skyteam |
| P0122342 | IRINA A LOBANOVA | 33 | boarding_passes; pointz; sirena; skyteam |

### C1 - Невозможный маршрут (сильный)

Людей: 0

### C2 - Аномально много перелётов (слабый)

Людей: 3

Пороги: `C2_threshold` = 40

Примеры:

| person_id | имя | C2_count | C2_group |
|---|---|---|---|
| P0040327 | GALKIN YAN | 42 |  |
| P0031966 | UL'YANA KORCHAGINA | 41 | P0031966; P0087959 |
| P0087959 | ULIANA E. KORCHAGINA | 41 | P0031966; P0087959 |

### C3 - Короткие международные поездки (средний)

Людей: 104

Примеры:

| person_id | имя | C3_count | C3_examples | C3_group |
|---|---|---|---|---|
| P0034531 | RADMIR SYCHEV | 3 | SU2800 2017-02-04 AER-SIP -> SU1625 2017-02-05 SIP-SVO (1 дн.) / SU1620 2017-02… |  |
| P0001767 | NEKRASOVA STEFANIIA | 2 | SU2090 2017-06-18 SVO-BEG -> SU2093 2017-06-20 BEG-SVO (2 дн.) / SU2142 2017-09… |  |
| P0038704 | BYKOV SEMEN | 2 | SU1940 2017-03-22 SVO-ALA -> SU1941 2017-03-24 ALA-SVO (2 дн.) / SU3962 2017-05… |  |
| P0044562 | LARIONOV ROMAN S | 2 | OK4893 2017-01-06 SVO-PRG -> OK4902 2017-01-07 PRG-SVO (1 дн.) / SU1860 2017-03… |  |
| P0044459 | ALEKSEY KORNILOV | 2 | SU2352 2017-02-28 SVO-VIE -> SU2185 2017-03-02 VIE-SVO (2 дн.) / SU2684 2017-03… |  |

### C5 - Редкие направления (слабый)

Людей: 32

Пороги: `C5_threshold` = 33

Примеры:

| person_id | имя | C5_count | C5_airports | C5_group |
|---|---|---|---|---|
| P0002727 | NINA KUPRIYANOVA | 3 | PSU (всего 32); SQG (всего 17) | P0002727; P0082136 |
| P0012475 | DOROFEEVA MAR'YANA D | 3 | CEN (всего 33); CME (всего 24); CPE (всего 33) |  |
| P0082136 | NINA R. KUPRIIANOVA | 3 | PSU (всего 32); SQG (всего 17) | P0002727; P0082136 |
| P0034884 | ANATOLIY KALUGIN | 2 | PSU (всего 32) |  |
| P0036622 |  | 2 | PSU (всего 32) |  |

### C6 - Рваная активность (слабый)

Людей: 352

Примеры:

| person_id | имя | C6_count | C6_max_burst_flights | C6_examples | C6_group |
|---|---|---|---|---|---|
| P0000580 |  | 1 | 4 | пауза 113 дн.; с 2017-05-26 - 4 рейсов за 14 дн. |  |
| P0000685 | SOF'YA FILATOVA | 1 | 4 | пауза 136 дн.; с 2017-06-11 - 4 рейсов за 14 дн. |  |
| P0062302 | MAR'YANA R PROKOF'EVA | 1 | 4 | пауза 96 дн.; с 2017-06-12 - 4 рейсов за 14 дн. |  |
| P0080973 | NAZAR PETROVICH SHCHERBAKOV | 1 | 4 | пауза 108 дн.; с 2017-05-01 - 4 рейсов за 14 дн. | P0062269; P0080973 |
| P0062269 | NAZAR SHCHERBAKOV | 1 | 4 | пауза 108 дн.; с 2017-05-01 - 4 рейсов за 14 дн. | P0062269; P0080973 |

### D1 - Постоянные попутчики (средний)

Людей: 4734

Примеры:

| person_id | имя | D1_count | D1_max_shared | D1_companions |
|---|---|---|---|---|
| P0075001 | KONDRAT'EVA UL'YANA | 1 | 17 | P0043623 (17) |
| P0043623 |  | 1 | 17 | P0075001 (17) |
| P0073151 | ELIZAROVA ESENIIA | 1 | 15 | P0007538 (15) |
| P0007538 |  | 1 | 15 | P0073151 (15) |
| P0083272 | AVDEEVA VASILISA | 1 | 14 | P0021549 (14) |

### D2 - Общий PNR у разных людей (слабый)

Людей: 0

### E1 - Много loyalty-карт / программ (слабый)

Людей: 4725

Пороги: `E1_threshold` = 3.5

`E1_reason`: many_cards - 4725

Примеры:

| person_id | имя | E1_count | E1_n_programs | E1_same_program_cards | E1_reason | E1_cards |
|---|---|---|---|---|---|---|
| P0000005 | D'YAKOV RUSLAN | 4 | 4 | 0 | many_cards | DT 479114128; FB 629903943; KE 629925275; SU 525500144 |
| P0000006 | DANIL VAVILOV | 4 | 4 | 0 | many_cards | DT 980250352; FB 650748133; KE 885948676; SU 510085965 |
| P0000011 | KAROLINA SKVORTSOVA | 4 | 4 | 0 | many_cards | DT 595640733; FB 67411245; KE 218776505; SU 907725575 |
| P0000012 | ALEKSANDR NIKOLAEV | 4 | 4 | 0 | many_cards | DT 560293421; FB 966797673; KE 58547979; SU 288949592 |
| P0000018 | GERMAN BULGAKOV | 4 | 4 | 0 | many_cards | DT 437327368; FB 351327051; KE 985948315; SU 638306630 |

### E2 - Перекос источников (слабый)

Людей: 2439

Пороги: `E2_low_threshold` = 0.465; `E2_high_threshold` = 1.248; `E2_median` = 0.889

`E2_direction`: travel_heavy - 2439

Примеры:

| person_id | имя | E2_count | E2_direction | E2_imbalance | E2_n_flights | E2_loyalty_only |
|---|---|---|---|---|---|---|
| P0066595 | ANATOLII PETROVICH SHILOV | 5 | travel_heavy | -1.0 | 5 | 0 |
| P0086377 | ALISA BIRIUKOVA | 7 | travel_heavy | -1.0 | 7 | 0 |
| P0086296 | DROZDOVA TAMARA | 5 | travel_heavy | -1.0 | 5 | 0 |
| P0086297 | IL'YA M SHCHUKIN | 7 | travel_heavy | -1.0 | 7 | 0 |
| P0086311 | DANIEL MASLOV | 13 | travel_heavy | -1.0 | 13 | 0 |

## 4. Общий рейтинг

Людей хотя бы с одним признаком: 35468; хотя бы с одним сильным: 19.

Сортировка: число сильных признаков → число категорий → число признаков. Сильные: A1, A2, A3, A4, B4, C1 (A3 - только `same_person_possible`).

| категорий | людей |
|---|---|
| 3 | 23 |
| 2 | 2660 |
| 1 | 32785 |

Топ-30:

| person_id | имя | категорий | признаков | сильных | признаки |
|---|---|---|---|---|---|
| P0047864 | GOLOVINA OLESIA | 2 | 2 | 1 | A4; E1 |
| P0079348 | AMALIIA KUDRIAVTSEVA | 2 | 2 | 1 | A2; D1 |
| P0019901 | ROMAN MASLENNIKOV | 1 | 2 | 1 | A4; A6 |
| P0103336 | GORDEI M. GLEBOV | 1 | 1 | 1 | A1 |
| P0106284 | GORDEI M. GLEBOV | 1 | 1 | 1 | A1 |
| P0114475 | AMALIIA N. KUDRIAVTSEVA | 1 | 1 | 1 | A2 |
| P0116211 | GORDEI MAKAREVICH GLEBOV | 1 | 1 | 1 | A1 |
| P0119448 | RAMIL ALBERTOVICH BUROV | 1 | 1 | 1 | A1 |
| P0293273 | OLESYA GOLOVINA | 1 | 1 | 1 | A4 |
| P0595640 |  | 1 | 1 | 1 | A4 |
| P0595641 |  | 1 | 1 | 1 | A4 |
| P0595642 |  | 1 | 1 | 1 | A4 |
| P0595643 |  | 1 | 1 | 1 | A4 |
| P0595644 |  | 1 | 1 | 1 | A4 |
| P0595645 |  | 1 | 1 | 1 | A4 |
| P0595646 |  | 1 | 1 | 1 | A4 |
| P0595647 |  | 1 | 1 | 1 | A4 |
| P0595648 |  | 1 | 1 | 1 | A4 |
| P0595649 |  | 1 | 1 | 1 | A4 |
| P0001943 | DANIL I TITOV | 3 | 3 | 0 | A6; B5; E1 |
| P0005605 | GROMOV VALERIY | 3 | 3 | 0 | A6; B5; E1 |
| P0007552 | RUSTAM P VOROB'EV | 3 | 3 | 0 | A6; C6; E1 |
| P0012242 | KALACHEV VITALIY | 3 | 3 | 0 | A6; B5; E1 |
| P0016660 | EREMIN IAN | 3 | 3 | 0 | A6; B5; E1 |
| P0020669 | MITROFANOVA NATAL'YA | 3 | 3 | 0 | A6; C3; E1 |
| P0024498 | KUKUSHKIN PAVEL | 3 | 3 | 0 | A6; B5; E1 |
| P0027225 | AMINA KOCHETKOVA | 3 | 3 | 0 | A6; B5; E1 |
| P0030284 | ALEKSEI S. SHUVALOV | 3 | 3 | 0 | A6; C6; E1 |
| P0032723 | SHCHUKIN FILIPP | 3 | 3 | 0 | A6; C5; E1 |
| P0036150 | ARTUR BOGOMOLOV | 3 | 3 | 0 | A6; B5; E1 |

Полный рейтинг: `analysis/output/report_ranking.csv`.

## 5. Проверка на известных случаях

Люди с уже найденными аномалиями должны получить ожидаемые признаки. «не найден» - у человека нет ни одного сработавшего признака.

| Кто | Ожидается | person_id | Сработавшие признаки | Итог |
|---|---|---|---|---|
| GORDEI GLEBOV | A1 | P0103336, P0106284, P0116211 | A1 | OK |
| RAMIL BUROV | A1 | P0119448, P0034596 | A1; A6 | OK |
| AMALIIA KUDRIAVTSEVA | A2 | P0079348, P0114475, P0038150, P0063447 | A2; A6; D1 | OK |
| ROMAN MASLENNIKOV | A4 | P0019901 | A4; A6 | OK |
| OLESYA GOLOVINA | A4 | P0047864, P0293273 | A4; E1 | OK |
| YULIYA KORSHUNOVA | A5 | P0057058, P0041146, P0584736 | A5; A6; E1 | OK |
| STANISLAV KONDRATOV | A5 | P0029586 | A5; A6 | OK |

## 6. Служебные проверки

Пары «одно имя + ≥3 общих перелёта» (`D1_same_person_check.csv`):

| категория | пар |
|---|---|
| likely_same_person | 5743 |
| split_same_person | 5167 |
| same_person_two_passports | 345 |

Два паспорта (`D1_two_passports_pairs.csv`): normal - 345

Попутчики (`D1_pairs.csv`): пар 2368; максимум общих перелётов у пары - 17.
