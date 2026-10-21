# Identity QA (участник 2)

## Контрольные количества

| Показатель | Значение |
|---|---|
| Forum profiles | 66592 |
| Профилей с реальным именем | 33460 |
| Профилей без реального имени | 33132 |
| Loyalty cards (строк) | 88827 |
| Уникальных card_key | 88826 |
| card_key у более чем одного profile_id | 1 |
| Boarding records | 155147 |
| Уникальных document_norm | 73263 |
| Документов у разных людей | 1 |
| Людей с несколькими документами | 1 |
| Строк в boarding_document_conflicts | 8 |

## Проверки

| Проверка | Результат |
|---|---|
| forum_identity_keys: 1 строка = 1 профиль (profile_id уникален) | OK |
| forum_identity_keys: сумма n_flights = строк forum_flights | OK |
| forum_loyalty_keys: строк = строк forum_loyalty (ничего не удалено) | OK |
| boarding_identity_keys: строк = строк boarding_clean | OK |
| boarding_identity_keys: source_record_id уникален | OK |
| document_norm хранится строкой (ведущие нули сохранены) | OK |

## Определения

- Человек в BoardingData = `first_name_norm + last_name_norm + birth_date`. Отчество в ключ не входит: оно записано то полностью, то инициалом.
- `same_document_different_people`: у одного `document_norm` больше одного такого человека.
- `same_person_multiple_documents`: у одного такого человека больше одного `document_norm`.
- Одна запись может попасть в оба типа конфликта.
- Ни одна запись не удалена и не исправлена; какая версия «правильная», не решалось.
- `link_candidates` на этом этапе не использовался.

## Карты у нескольких профилей

```
profile_id           nickname first_name_norm last_name_norm program card_number    card_key status
     19900 FrequentFlyer29897                                     FB   139888197 FB139888197  Elite
     47863 FrequentFlyer71993          OLESYA       GOLOVINA      FB   139888197 FB139888197  Elite
```

## Конфликтные группы документов

same_document_different_people - `doc:8248013778` (4 записей)

```
source_record_id first_name_norm second_name_norm last_name_norm birth_date document_norm flight_date flight_number
 boarding:150151           RAMIL      ALBERTOVICH          BUROV 1995-08-24    8248013778  2017-01-03        SU1273
  boarding:92874          GORDEI               M.         GLEBOV 1982-12-31    8248013778  2017-01-16        SU1057
  boarding:83246          GORDEI               M.         GLEBOV 1982-12-31    8248013778  2017-03-09        SU1276
 boarding:134532          GORDEI       MAKAREVICH         GLEBOV 1982-12-31    8248013778  2017-03-10        SU1281
```

same_person_multiple_documents - `person:AMALIIA|KUDRIAVTSEVA|1985-11-22` (4 записей)

```
source_record_id first_name_norm second_name_norm last_name_norm birth_date document_norm flight_date flight_number
 boarding:126633         AMALIIA               N.   KUDRIAVTSEVA 1985-11-22    1378965068  2017-01-02        SU1483
 boarding:120481         AMALIIA       RODIONOVNA   KUDRIAVTSEVA 1985-11-22    5518372746  2017-01-04        SU1491
  boarding:21723         AMALIIA       RODIONOVNA   KUDRIAVTSEVA 1985-11-22    5518372746  2017-02-24        SU1322
  boarding:37035         AMALIIA               R.   KUDRIAVTSEVA 1985-11-22    5518372746  2017-02-28        SU1493
```
