# participants

Первый этап проекта: каждый участник разбирал и чистил свои исходные файлы. У всех папок одинаковое устройство:

| Папка | Что в ней |
|---|---|
| `src/` | код разбора и очистки |
| `output/` | итоговые таблицы участника, их забирает `integration/src/merge_all.py`. В репозиторий не входят, получаются запуском кода |
| `intermediate/` | промежуточные таблицы: ошибки разбора, конфликты, проверки |
| `samples/` | примеры таблиц, по 20-100 строк |
| `reports/` | отчёты о качестве данных |

В `output/` и `intermediate/` таблицы получаются запуском кода из `src/`, на вход код берёт файлы из `data/raw/`.

| Папка | Участник | Что отдаёт в сведение |
|---|---|---|
| `p1_timetable` | Станислав | `timetable_unique.csv` и справочники аэропортов и маршрутов, нужны признакам C1 и C3 |
| `p2_forum_boarding` | Анна | таблицы форума (`processed/forum_*.parquet`) |
| `p3_sirena_boarding_passes` | Максим | `sirena.csv`, `boarding_passes.csv` |
| `p4_pointz_skyteam` | Анастасия | `pointz_users.csv`, `pointz_cards.csv`, `pointz_flights.csv`, `skyteam_exchange.csv` |

BoardingData отдельной таблицей не готовится: `merge_all.py` читает его прямо из `data/raw/`.
