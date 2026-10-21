# p1_timetable

Станислав Лисенков. Источник: расписание SkyTeam `Skyteam_Timetable.pdf` (312 МБ).

Расписание действует с 1 ноября 2018 по 31 января 2019 года, а перелёты пассажиров относятся к 2017 году. Поэтому в общую таблицу перелётов оно не входит и используется только как справочник: время прилёта рейса, город и страна аэропорта.

## Что получается

| Файл | Одна строка | Строк | Где используется |
|---|---|---|---|
| `output/timetable_unique.csv` | правило расписания | 168 648 | признаки C1 и C3 |
| `output/airports_reference.csv` | аэропорт: город, страна, частота, флаг `has_conflict` | | |
| `output/routes_reference.csv` | маршрут номера рейса: перевозчик, кодшеринг, время прилёта | | |

Признаки ищут расписание по пути `participants/p1_timetable/output/timetable_unique.csv`.

## Запуск

### Шаг 1. Парсинг PDF-расписания:
```bash 
python3 participants/p1_timetable/src/parse_timetable.py
```

### Шаг 2. Сборка справочников аэропортов и маршрутов:
```bash 
python3 participants/p1_timetable/src/build_references.py
```



## Примеры

`samples/timetable_sample.csv` - первые строки `timetable_unique.csv`.
