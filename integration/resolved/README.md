# resolved

Результат склейки. Создаётся скриптами `resolve_entities.py`, `name_check.py`, `name_candidates.py`. Таблицы большие, в репозиторий не входят, кроме `conflicted_keys.csv`. Примеры в `integration/samples/resolved_*`.

| Файл | Одна строка | Строк |
|---|---|---|
| `persons.parquet` | профиль человека (`person_id`) | 595 649 |
| `flight_events.parquet` | перелёт: человек, рейс, дата (`flight_event_id`) | 2 417 794 |
| `record_links.parquet` | исходная запись и её `person_id`, `flight_event_id` | 4 492 054 |
| `conflicted_keys.csv` | ключ, исключённый из склейки, и причина | 2 |
| `route_conflicts.csv` | перелёт, у которого источники называют разные аэропорты | 66 925 |
| `name_mismatches.parquet`, `name_check_persons.csv` | расхождения имён внутри профиля | 0 |
| `name_link_candidates.parquet` | одиночная запись и профиль, к которому она, возможно, относится | 308 518 |

Главные колонки `persons`: `person_id`, `sources`, `name_variants`, `sex`, `birth_dates`, `documents`, `loyalty_ids`, `forum_profiles`, `pointz_users`, `n_flight_events`.

Главные колонки `flight_events`: `flight_event_id`, `person_id`, `flight_number`, `flight_date`, `sources` и `n_sources` (в каких источниках есть перелёт), `origin_airport` и `destination_airport` с источником, `departure_time`, `arrival_date`, `arrival_time`, флаги `airport_still_broken`, `route_conflict`, `skyteam_route_disagrees`.

Все 66 925 расхождений маршрутов дают данные SkyTeam: там на номер рейса в день записан один маршрут. Между остальными источниками расхождений нет.
