# Resolve QA: этап 1 (сильные ключи)

Склейка только по сильным ключам: карта, документ, билет, PNR+рейс+дата, принадлежность перелёта профилю. Имена не использовались. Конфликтные ключи исключены (conflicted_keys.csv).

## Итог

| Показатель | Значение |
|---|---|
| Записей о пассажирах (passengers_all) | 1059924 |
| Записей о перелётах (flights_all) | 4358805 |
| Всего уникальных записей | 4492054 |
| Людей (person_id) | 595649 |
| из них с именем | 588095 |
| Перелётов (flight_event_id) | 2417794 |
| перелётов, подтверждённых ≥2 источниками | 1421863 |
| перелётов с битым аэропортом, восстановленным из другого источника | 563 |
| перелётов, где битый аэропорт остался битым | 87014 |
| перелётов с разными аэропортами в разных источниках (route_conflicts.csv) | 66925 |
| ...из них SkyTeam расходится с остальными | 66925 |
| ...из них у SkyTeam направление перевёрнуто | 19191 |
| ...конфликт между другими источниками (без SkyTeam) | 0 |

## Сколько рёбер дал каждый тип ключа

| Ключ | Рёбер | Уникальных ключей | Исключено как конфликтные |
|---|---|---|---|
| card | 2483746 | 133361 | 1 |
| doc | 310904 | 101662 | 1 |
| owner | 1868612 | 123535 | 0 |
| pnr | 848914 | 748995 | 0 |
| tkt | 848875 | 749192 | 0 |

## Из каких источников собраны люди

| Комбинация источников | Людей |
|---|---|
| boarding_passes | 431895 |
| boarding_data; boarding_passes; sirena | 15262 |
| boarding_data; sirena | 12979 |
| boarding_data | 12568 |
| boarding_passes; forum; pointz; skyteam | 11200 |
| boarding_passes; pointz; skyteam | 11195 |
| boarding_passes; forum; skyteam | 10938 |
| forum | 9441 |
| pointz | 9438 |
| sirena | 9223 |
| boarding_data; boarding_passes; forum; sirena; skyteam | 8226 |
| boarding_data; boarding_passes; pointz; sirena; skyteam | 8111 |
| boarding_data; boarding_passes; forum; pointz; sirena; skyteam | 8053 |
| boarding_passes; sirena | 5695 |
| forum; pointz; skyteam | 5693 |
| forum; skyteam | 5656 |
| pointz; skyteam | 5622 |
| boarding_data; boarding_passes | 3364 |
| boarding_passes; pointz; sirena; skyteam | 1764 |
| boarding_passes; forum; sirena; skyteam | 1734 |

## Перелёты по числу подтверждающих источников

| Источников | Перелётов |
|---|---|
| 1 | 995931 |
| 2 | 1023829 |
| 3 | 296131 |
| 4 | 84386 |
| 5 | 15823 |
| 6 | 1694 |

| Комбинация источников | Перелётов |
|---|---|
| forum; skyteam | 810723 |
| boarding_passes | 431895 |
| skyteam | 326227 |
| forum | 184814 |
| pointz; skyteam | 157651 |
| forum; pointz; skyteam | 155867 |
| boarding_passes; forum; pointz; skyteam | 38782 |
| boarding_passes; pointz; skyteam | 38780 |
| boarding_passes; forum; skyteam | 38505 |
| boarding_data | 32847 |
| sirena | 20148 |
| boarding_data; sirena | 17831 |
| boarding_passes; sirena | 16303 |
| boarding_data; forum; sirena; skyteam | 16194 |
| forum; sirena; skyteam | 16042 |

## Конфликты маршрута: какие значения расходятся (топ-15)

| Вылет (разные значения) | Прилёт (разные значения) | Источники | Перелётов |
|---|---|---|---|
| SIP; SVO | SIP; SVO | forum; skyteam | 883 |
| NBC; SVO | NBC; SVO | forum; skyteam | 505 |
| MED; ORN | MED; ORN | forum; skyteam | 356 |
| KHV; OHH | KHV; OHH | forum; skyteam | 350 |
| NUX; SVO | NUX; SVO | forum; skyteam | 339 |
| CDG; SVO | CDG; SVO | forum; skyteam | 337 |
| BCN; SVO | BCN; SVO | forum; skyteam | 304 |
| SVO | CAN; WUH | forum; skyteam | 211 |
| SIP; SVO | SIP; SVO | pointz; skyteam | 208 |
| MCX; SVO | MCX; SVO | forum; skyteam | 199 |
| FCO; LIN | FCO; LIN | forum; skyteam | 195 |
| SIP; SVO | SIP; SVO | forum; pointz; skyteam | 170 |
| KHV; OHH | KHV; OHH | boarding_data; forum; skyteam | 164 |
| KHV; OHH | KHV; OHH | boarding_data; forum; sirena; skyteam | 153 |
| KHV; OHH | KHV; OHH | forum; sirena; skyteam | 149 |

## Форум и Pointz

- Людей с профилем форума: 66592
- ...из них связаны с Pointz: 28596
- ...из них есть имя (из любого источника): 59048

## Флаги возможной ложной склейки (не исправлялись)

- Несколько разных дат рождения у одного person_id: 0
- Несколько профилей форума в одном person_id: 0
- Несколько пользователей Pointz в одном person_id: 0

## Самые большие person_id (проверить глазами)

```
person_id  n_records                                                        sources  n_name_variants  n_birth_dates  n_flight_events                                                                                                                                                name_variants
 P0049182        113 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                6              1               29                               DOROFEEV MATVEY S; MATVEI DOROFEEV; MATVEI S. DOROFEEV; MATVEI SEMENOVICH DOROFEEV; MATVEY DOROFEEV; ДОРОФЕЕВ МАТВЕЙ СЕМЕНОВИЧ
 P0000573        113                boarding_passes; forum; pointz; sirena; skyteam                5              0               35                                                                 CHERNOVA SOFIIA; CHERNOVA SOFIYA; SOFIIA CHERNOVA; SOFIYA CHERNOVA; ЧЕРНОВА СОФИЯ ВАСИЛЬЕВНА
 P0053932        112 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                5              1               37                                                    GORDEI E. SVESHNIKOV; GORDEI SVESHNIKOV; GORDEY SVESHNIKOV; SVESHNIKOV GORDEI; СВЕШНИКОВ ГОРДЕЙ ЭМИЛЬЕВИЧ
 P0054768        112 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                6              1               38                                                    GLEB I ZHDANOV; GLEB I. ZHDANOV; GLEB IVANOVICH ZHDANOV; GLEB ZHDANOV; ZHDANOV GLEB; ЖДАНОВ ГЛЕБ ИВАНОВИЧ
 P0050211        111 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                6              1               32                                                    PANINA VLADA; PANINA VLADA I; VLADA I. PANINA; VLADA IGOREVNA PANINA; VLADA PANINA; ПАНИНА ВЛАДА ИГОРЕВНА
 P0040865        111 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                6              1               34                     ANATOLII A. SAMOILOV; ANATOLII ARTUROVICH SAMOILOV; ANATOLII SAMOILOV; ANATOLIY SAMOYLOV; SAMOYLOV ANATOLIY; САМОЙЛОВ АНАТОЛИЙ АРТУРОВИЧ
 P0055157        110 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                7              1               34                          ANTON TROITCKII; ANTON TROITSKIY; ANTON V TROITSKIY; ANTON V. TROITSKII; TROITCKII ANTON; TROITSKIY ANTON; ТРОИЦКИЙ АНТОН ВЛАДЬЕВИЧ
 P0053592        110 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                4              1               32                                                                                  SUVOROV VADIM; VADIM IUREVICH SUVOROV; VADIM SUVOROV; СУВОРОВ ВАДИМ ЮРЬЕВИЧ
 P0058399        109 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                5              1               30                                                  ARIANA O SOROKINA; ARIANA ODISSEEVNA SOROKINA; ARIANA SOROKINA; SOROKINA ARIANA; СОРОКИНА АРИАНА ОДИССЕЕВНА
 P0045527        108 boarding_data; boarding_passes; forum; pointz; sirena; skyteam                7              1               29 MAIIA K. SELIVANOVA; MAIIA KONSTANTINOVNA SELIVANOVA; MAIIA SELIVANOVA; MAYYA SELIVANOVA; SELIVANOVA MAIIA; SELIVANOVA MAYYA; СЕЛИВАНОВА МАЙЯ КОНСТАНТИНОВНА
```

## Исключённые конфликтные ключи

| Тип | Ключей | Причины |
|---|---|---|
| card | 1 | известный конфликт: ROMAN MASLENNIKOV / OLESYA GOLOVINA (Pointz), 2 профиля форума |
| doc | 1 | известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData) |

## Проверки

| Проверка | Результат |
|---|---|
| каждая запись получила person_id | OK |
| каждая запись о перелёте получила flight_event_id | OK |
| сумма n_records по людям = числу уникальных записей | OK |
| сумма n_records по перелётам = строкам flights_all | OK |