# QA-отчёт по подготовке данных к интеграции (Участник 4: Pointz XML + SkyTeam YAML)

## 1. Проверка уникальности сильного ключа (`loyalty_id_normalized + flight_date + flight_number`)
- **`pointz_flights.csv`**:
  - Всего строк: **436090**
  - Уникальных ключей `(loyalty_id_normalized, flight_date, flight_number)`: **436090**
  - Дубликатов ключа: **0** (ключ на 100% уникален)
- **`skyteam_exchange.csv`**:
  - Всего строк: **1687053**
  - Уникальных ключей `(loyalty_id_normalized, flight_date, flight_number)`: **1687053**
  - Дубликатов ключа: **0** (ключ на 100% уникален)

---

## 2. Статистика подозрительных аэропортов (`rea`, `ova`, `nia`, `ngo`, `nds`) и их восстановления

### 2.1. Изначальное количество проблем:
- **Всего строк с подозрительным аэропортом (`suspicious airport rows`):** **79292**
  - В `PointzAggregator`: **16299** строк
  - В `SkyTeamExchange`: **62993** строк
- **Всего подозрительных полей аэропортов (`suspicious airport fields`, т.к. в одной строке могут быть битыми и `origin`, и `destination`):** **90749**
  - В `PointzAggregator`: **18641** полей (`origin`: 9158, `destination`: 9483)
  - В `SkyTeamExchange`: **72108** полей (`origin`: 35276, `destination`: 36832)

### 2.2. Результаты доказуемого восстановления (`integration/bad_airport_repairs.csv`):
- **Успешно и доказуемо восстановлено (`recovered`):** **20** полей
  - Восстановлено для `PointzAggregator` (из `SkyTeamExchange`): **9**
  - Восстановлено для `SkyTeamExchange` (из `PointzAggregator`): **11**
- **Правило восстановления:** `match_rule = loyalty+date+flight_cross_source`, `confidence = HIGH` (одна сторона содержит битый код, другая — валидный 3-буквенный IATA-код, а парный аэропорт маршрута совпадает).
- **Распределение восстановленных кодов (`raw -> recovered_airport`):**
  - `'rea'` -> **`CMB`**: 5 раз
  - `'ngo'` -> **`NLA`**: 5 раз
  - `'ngo'` -> **`BZV`**: 3 раз
  - `'rea'` -> **`NRT`**: 3 раз
  - `'rea'` -> **`PVG`**: 2 раз
  - `'nia'` -> **`CAI`**: 1 раз
  - `'nds'` -> **`MIA`**: 1 раз

### 2.3. Оставшиеся неразрешёнными (`integration/unresolved_bad_airports.csv`):
- **Осталось `unresolved`:** **90729** полей
  - Из `PointzAggregator`: **18632**
  - Из `SkyTeamExchange`: **72097**
- **Причины попадания в `unresolved`:**
  - В обоих источниках на этом перелёте стоит одинаковый битый код (`both_sources_suspicious`): **23846**
  - Перелёт присутствует только в одном из двух источников (`no_cross_source_match`): **66721**
  - Конфликт направления/маршрута между источниками (`direction_or_route_conflict`): **162**
- **Распределение `unresolved` по исходным кодам:**
  - `'rea'`: 85399 раз
  - `'ova'`: 2267 раз
  - `'nia'`: 2229 раз
  - `'ngo'`: 760 раз
  - `'nds'`: 74 раз
- *Примечание:* Угадывание по стране/номеру рейса не применялось; код `'ngo'` (в нижнем регистре) не превращался автоматически в `'NGO'`, а заглавный `'NGO'` (Nagoya) корректно сохранён как валидный IATA-код.

---

## 3. Конфликты карт лояльности (`integration/pointz_loyalty_conflicts.csv`)
- **Количество `loyalty_id_normalized`, принадлежащих более чем одному пользователю:** **1**
- **Всего конфликтных строк в `pointz_loyalty_conflicts.csv`:** **2**
- **Найденные конфликтные записи (выгружено динамически из таблицы):**
  - Карта **`FB 139888197`** (`pz_card_26428`): `user_uid = 146589094`, **ROMAN MASLENNIKOV** (`cards_count = 3`, `flights_on_this_card = 8`)
  - Карта **`FB 139888197`** (`pz_card_63761`): `user_uid = 866799462`, **OLESYA GOLOVINA** (`cards_count = 4`, `flights_on_this_card = 5`)

---

## 4. Конфликты `user_uid` (`integration/user_uid_conflicts.csv`)
- **Количество `user_uid`, относящихся более чем к одному человеку:** **1**
- **Всего конфликтных строк в `user_uid_conflicts.csv`:** **2**
- **Найденные конфликтные записи (выгружено динамически из таблицы):**
  - `user_uid = 708343118` (`pz_user_18596`): **YULIYA KORSHUNOVA** (`n_cards = 0`, `n_flights = 0`)
  - `user_uid = 708343118` (`pz_user_29640`): **STANISLAV KONDRATOV** (`n_cards = 1`, `n_flights = 9`)
