# p4_pointz_skyteam

Анастасия Зотова. Источники: агрегатор миль Pointz (`PointzAggregator.xml`, 146 МБ) и обмен данными альянса SkyTeam (`SkyTeam-Exchange.yaml`, 164 МБ).

XML читается потоково, с очисткой памяти после каждого пользователя. YAML нарезается по датам верхнего уровня и разворачивается в плоскую таблицу: одна строка - одна карта на одном рейсе.

## Что получается

| Файл | Одна строка | Строк |
|---|---|---|
| `output/pointz_users.csv` | пользователь Pointz (`user_uid`) | 66 657 |
| `output/pointz_cards.csv` | карта лояльности пользователя | 88 818 |
| `output/pointz_flights.csv` | перелёт по карте | 436 090 |
| `output/skyteam_exchange.csv` | использование карты на рейсе | 1 687 053 |
| `intermediate/pointz_skyteam_matches.csv` | перелёт, найденный и в Pointz, и в SkyTeam | 280 885 |

Таблицы из `output/` забирает `integration/src/merge_all.py`.

## Что нашлось

- Pointz и SkyTeam сопоставлены по карте, дате и номеру рейса. Общих карт 88 064, общих перелётов 280 885, тариф совпал во всех.
- Карта FB 139888197 у двух разных людей: Роман Масленников и Олеся Головина.
- Один `user_uid` 708343118 у двух пользователей: Юлия Коршунова (без карт) и Станислав Кондратов. Чтобы карта Кондратова не досталась Коршуновой, при сведении карты привязаны к пользователю, у которого они есть.
- Битые коды аэропортов (16 299 строк в XML, 62 993 в YAML) - это последние три буквы названий стран: rea, ova, nia, ngo, nds (Korea, Moldova, Tanzania, Congo, Netherlands). Битый ngo в нижнем регистре не путается с аэропортом NGO в Нагое.
- В SkyTeam на один номер рейса в день записан один маршрут, хотя под одним номером летают в обе стороны. Поэтому при склейке аэропорты SkyTeam берутся в последнюю очередь, а в признаках C маршруты только от SkyTeam не используются.

## Запуск

Исходные файлы `PointzAggregator-AirlinesData.xml` и `SkyTeam-Exchange.yaml` должны лежать в `data/raw/`.

```bash
python3 participants/p4_pointz_skyteam/src/parse_pointz.py
python3 participants/p4_pointz_skyteam/src/parse_skyteam.py
python3 participants/p4_pointz_skyteam/src/match_pointz_skyteam.py

## Примеры

`samples/pointz_users_sample.csv`, `pointz_cards_sample.csv`, `pointz_flights_sample.csv`, `pointz_full_sample.csv` (пользователь, карта и перелёт в одной строке), `skyteam_exchange_sample.csv`, `pointz_skyteam_matches_sample.csv`.
