# merged

Все источники в одном формате, без склейки и без удаления дубликатов. Создаётся `integration/src/merge_all.py`.

| Файл | Одна строка | Строк |
|---|---|---|
| `passengers_all.parquet` | запись о человеке в одном источнике | 1 059 924 |
| `flights_all/` | запись о перелёте в одном источнике | 4 358 805 |

`flights_all` разбита на файлы по источникам, потому что одним файлом она больше 100 МБ:

| Файл | Источник | Строк |
|---|---|---|
| `1_forum.parquet` | форум | 1 308 987 |
| `2_boarding_data.parquet` | BoardingData | 155 147 |
| `3_sirena.parquet` | Sirena | 155 757 |
| `4_boarding_passes.parquet` | посадочные талоны | 615 771 |
| `5_pointz.parquet` | Pointz | 436 090 |
| `6_skyteam.parquet` | SkyTeam | 1 687 053 |

Читать целиком: `from paths import read_flights_all; df = read_flights_all()`. Можно и `pd.read_parquet("integration/merged/flights_all")`, но тогда порядок строк может отличаться.

## Колонки passengers_all

| Колонка | Что значит |
|---|---|
| `source` | источник: forum, boarding_data, sirena, boarding_passes, pointz |
| `source_record_id` | номер записи, уникальный во всей таблице |
| `source_person_id` | ник форума или `user_uid` Pointz |
| `full_name_raw` | имя целиком, как в источнике (Sirena, посадочные, Pointz) |
| `first_name_raw`, `middle_name_raw`, `last_name_raw` | имя по частям (форум, BoardingData, Pointz) |
| `title` | MR / MRS из посадочных |
| `sex` | пол (форум, BoardingData) |
| `birth_date` | дата рождения (BoardingData, Sirena) |
| `document` | номер документа без пробелов |
| `loyalty_ids` | карты лояльности через `; ` |
| `pnr`, `e_ticket` | код брони и номер билета |

## Колонки flights_all

| Колонка | Что значит |
|---|---|
| `source`, `source_record_id` | источник и номер записи |
| `passenger_record_id` | запись о человеке в `passengers_all` (у SkyTeam нет, связь только через карту) |
| `flight_number`, `flight_date` | рейс и дата |
| `departure_time`, `arrival_date`, `arrival_time` | время вылета и прилёта, где есть |
| `origin_airport`, `destination_airport` | аэропорты, исходные значения в `*_raw` |
| `is_suspicious_airport` | один из битых кодов rea, ova, nia, ngo, nds |
| `origin_city`, `destination_city` | города, где есть |
| `codeshare`, `booking_class`, `fare_code` | код-шеринг, класс, тариф |
| `loyalty_id`, `document`, `pnr`, `e_ticket` | ключи этой записи |
| `baggage_raw` | багаж из BoardingData |

Примеры - `integration/samples/merged_*_sample.csv`, проверки форматов - `integration/reports/merge_qa.md`.
