# Кандидаты на склейку по именам (этап 2)

Результат этапа 1 не изменён. Это только предложения, ничего не слито.

| Показатель | Значение |
|---|---|
| Людей-одиночек (из одного источника посадок) | 453686 |
| Записей-одиночек | 455901 |
| ...с именем из ≥2 слов (можно сравнивать) | 455901 |
| Пар-кандидатов всего | 308518 |
| Записей с кандидатом уровня B (имя + рейс + дата) | 282014 |
| Записей с кандидатом уровня C (уникальное имя) | 24795 |
| Записей без кандидата | 149092 |
| ...из них имя есть у нескольких людей (C не предлагался) | 144099 |
| Пар с flag_ambiguous (подходит >1 человека) | 3417 |
| Пар с flag_sex_mismatch | 0 |
| Пар с flag_document_differs (имя совпало, документ другой) | 2478 |
| ...из них уровня B (тот же рейс в тот же день!) | 2288 |
| «Чистых» пар (без флагов) | 302922 |

## По источникам одиночек

| Источник | Записей-одиночек | с кандидатом B | с кандидатом C |
|---|---|---|---|
| boarding_data | 14291 | 13281 | 291 |
| boarding_passes | 431895 | 259531 | 24369 |
| sirena | 9715 | 9202 | 135 |

## Как пользоваться

- Строгая версия (этап 1): `persons` + `flight_events` как есть.
- Расширенная версия: дополнительно считать, что `orphan_person_id` = `candidate_person_id` для пар без флагов (или только уровня B).
- Если человек подозрителен в обеих версиях - сильный сигнал; только в одной - смотреть вручную.
- Пары с флагами сами по себе могут быть интересны (одно имя у разных людей, разный пол).
- B + flag_document_differs: человек с тем же именем летел тем же рейсом в тот же день, но по другому документу - либо тёзки на одном рейсе, либо один человек с двумя документами.

## Примеры

```
                 orphan_name flight_number flight_date                                                                          candidate_names confidence  flag_ambiguous  flag_sex_mismatch
             VERA R. GRIBOVA        SU1108  2017-09-24                                                               VERA GRIBOVA; GRIBOVA VERA          B           False              False
        NATASHA S. KORNILOVA        SU1357  2017-02-10                                                                        NATASHA KORNILOVA          B           False              False
   ELENA AIDAROVNA BELIAKOVA        SU1357  2017-02-10                                                                          ELENA BELIAKOVA          B           False              False
         GRIGORII V. KOROVIN        SU1515  2017-01-06                                     GRIGORIY KOROVIN; KOROVIN GRIGORII; GRIGORII KOROVIN          B           False              False
     AIDAR LVOVICH KOCHETKOV        SU1515  2017-01-06                                                                          AYDAR KOCHETKOV          B           False              False
 VLADISLAVA AMIROVNA LAPTEVA        SU1523  2017-01-08                             LAPTEVA VLADISLAVA; LAPTEVA VLADISLAVA A; VLADISLAVA LAPTEVA          B           False              False
KONSTANTIN EMILEVICH ALEKHIN        SU1523  2017-01-08                                                 KONSTANTIN ALEKHIN; KONSTANTIN E ALEKHIN          B           False              False
          DMITRII N. MALTSEV        SU1523  2017-01-08                                                                       DMITRIY N MAL'TSEV          B           False              False
   ELVIRA AIDAROVNA NOVIKOVA        SU1523  2017-01-08 EL'VIRA NOVIKOVA; NOVIKOVA EL'VIRA; NOVIKOVA ELVIRA; NOVIKOVA EL'VIRA A; ELVIRA NOVIKOVA          B           False              False
    ELINA PAVLOVNA TSVETKOVA        SU1523  2017-01-08                                        ELINA TCVETKOVA; TCVETKOVA ELINA; ELINA TSVETKOVA          B           False              False
```