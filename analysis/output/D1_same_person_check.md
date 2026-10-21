# Пары «одинаковое имя + ≥3 общих перелёта»

Всего пар: 11255

| Категория | Пар | Что значит |
|---|---|---|
| suspicious_two_identities | 0 | одни рейсы, разные документы/карты при одинаковых имени, дате рождения и поле - сильный сигнал |
| different_people_same_name | 0 | разные люди-тёзки (разная дата рождения/пол) многократно летят вместе |
| unclear | 0 | смотреть вручную |
| same_person_two_passports | 345 | всё совпадает, документы - внутренний + загран: скорее один человек |
| likely_same_person | 5743 | у обоих брони/посадки, противоречий нет, перелёты пересекаются: скорее один человек |
| split_same_person | 5167 | один человек, разрезанный склейкой (мили / поездки) - артефакт |

## Примеры: likely_same_person

```
person_id_1 person_id_2  shared_flights                       reasons                                                                                                               name_1
   P0023004    P0090273              14 same_trip_source; overlap=1.0                                                                                         GERMAN A GUSEV; GERMAN GUSEV
   P0044834    P0067750              13 same_trip_source; overlap=1.0                                                                           OLESIA SHAPOSHNIKOVA; OLESYA SHAPOSHNIKOVA
   P0075147    P0499207              13 same_trip_source; overlap=1.0                         VLADA I. MEDVEDEVA; VLADA IAROMIROVNA MEDVEDEVA; VLADA MEDVEDEVA; МЕДВЕДЕВА ВЛАДА ЯРОМИРОВНА
   P0025483    P0089203              11 same_trip_source; overlap=1.0                                                                                                       ALINA NAZAROVA
   P0036686    P0091980              11 same_trip_source; overlap=1.0                                                                                 SOF'YA KALMYKOVA; SOF'YA V KALMYKOVA
   P0009865    P0069036              11 same_trip_source; overlap=1.0                                                                                     NIKIFOROV ROMAN; ROMAN NIKIFOROV
   P0074146    P0143207              11 same_trip_source; overlap=1.0 SNEZHANA M. ZINOVEVA; SNEZHANA MIRONOVNA ZINOVEVA; SNEZHANA ZINOVEVA; ZINOVEVA SNEZHANA; ЗИНОВЬЕВА СНЕЖАНА МИРОНОВНА
   P0012918    P0079744              11 same_trip_source; overlap=1.0                                                         DMITRIEVA KRISTINA; DMITRIEVA KRISTINA B; KRISTINA DMITRIEVA
   P0031366    P0091122              10 same_trip_source; overlap=1.0                                                                                         IGNAT SOBOLEV; SOBOLEV IGNAT
   P0047161    P0067113              10 same_trip_source; overlap=1.0                                                                           EVGENIYA I KARTASHOVA; EVGENIYA KARTASHOVA
```