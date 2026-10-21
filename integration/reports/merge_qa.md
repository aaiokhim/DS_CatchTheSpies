# Merge QA: все источники

Строки не удалялись, дубликаты не убирались, имена не изменялись.

## passengers_all - 1059924 строк

| Источник | Строк | пусто: full_name_raw | пусто: last_name_raw | пусто: birth_date | пусто: document | пусто: loyalty_ids | пусто: pnr | пусто: e_ticket |
|---|---|---|---|---|---|---|---|---|
| forum | 66592 | 100% | 50% | 100% | 100% | 14% | 100% | 100% |
| boarding_data | 155147 | 100% | 0% | 0% | 0% | 100% | 50% | 50% |
| sirena | 155757 | 0% | 100% | 50% | 0% | 67% | 0% | 0% |
| boarding_passes | 615771 | 0% | 100% | 100% | 100% | 79% | 0% | 0% |
| pointz | 66657 | 0% | 0% | 100% | 100% | 14% | 100% | 100% |

Проверка формата (доля непустых значений, НЕ подходящих под шаблон):

| Источник | birth_date | document |
|---|---|---|
| forum | OK | OK |
| boarding_data | OK | OK |
| sirena | OK | OK |
| boarding_passes | OK | OK |
| pointz | OK | OK |

## flights_all - 4358805 строк

| Источник | Строк | пусто: flight_number | пусто: flight_date | пусто: origin_airport | пусто: destination_airport | пусто: loyalty_id | пусто: document | пусто: pnr | пусто: e_ticket |
|---|---|---|---|---|---|---|---|---|---|
| forum | 1308987 | 0% | 0% | 0% | 0% | 100% | 100% | 100% | 100% |
| boarding_data | 155147 | 0% | 0% | 100% | 100% | 100% | 0% | 50% | 50% |
| sirena | 155757 | 0% | 0% | 0% | 0% | 67% | 0% | 0% | 0% |
| boarding_passes | 615771 | 0% | 0% | 0% | 0% | 79% | 100% | 0% | 0% |
| pointz | 436090 | 0% | 0% | 0% | 0% | 0% | 100% | 100% | 100% |
| skyteam | 1687053 | 0% | 0% | 0% | 0% | 0% | 100% | 100% | 100% |

Проверка формата (доля непустых значений, НЕ подходящих под шаблон):

| Источник | flight_number | flight_date | departure_time | origin_airport | destination_airport | loyalty_id | document |
|---|---|---|---|---|---|---|---|
| forum | OK | OK | OK | OK | OK | OK | OK |
| boarding_data | OK | OK | OK | OK | OK | OK | OK |
| sirena | OK | OK | OK | OK | OK | OK | OK |
| boarding_passes | OK | OK | OK | OK | OK | OK | OK |
| pointz | OK | OK | OK | OK | OK | OK | OK |
| skyteam | OK | OK | OK | OK | OK | OK | OK |

| Источник | битых аэропортов (is_suspicious_airport) |
|---|---|
| forum | 48684 |
| boarding_data | 0 |
| sirena | 0 |
| boarding_passes | 22787 |
| pointz | 16299 |
| skyteam | 62993 |

## Как связаны таблицы

- `flights_all.passenger_record_id` -> `passengers_all.source_record_id` (forum: профиль; boarding_data / sirena / boarding_passes: та же строка; pointz: пользователь по user_uid).
- У skyteam записей о людях нет, связь только через `loyalty_id`.
- Один и тот же реальный перелёт может встречаться в нескольких источниках - это не удалялось.
