# Аномалии: форум + BoardingData

Аномалия не равна доказательству. Это список того, что нужно проверить по другим источникам.

| Код | Что ищем | Найдено строк |
|---|---|---|
| F1_card_shared_by_profiles | Одна карта лояльности (program+number) указана в нескольких профилях форума | 2 |
| F2_same_name_many_profiles | Одно и то же имя+фамилия у нескольких профилей (тёзки или один человек под разными никами) | 9550 |
| F3_several_cards_same_program | У одного профиля несколько карт одной и той же программы лояльности | 0 |
| F4_origin_equals_destination | Рейс, у которого аэропорт вылета совпадает с аэропортом прилёта (на практике - заглушка REA у рейсов KE/CZ, ошибка источника) | 7067 |
| F5_same_day_unconnected_flights | В один день у профиля есть рейс, который не стыкуется ни с одним другим рейсом этого дня | 0 |
| F6_too_many_flights_profile | Профили с аномально большим числом рейсов (> 37, правило Q3 + 3·IQR) | 4 |
| F7_duplicate_flight_in_profile | Один и тот же рейс в одну дату записан в профиле несколько раз | 0 |
| B1_document_different_people | Один номер документа у пассажиров с разными ФИО или датами рождения | 4 |
| B2_person_many_documents | Один и тот же человек (имя+фамилия+дата рождения) летал по разным документам | 4 |
| B3_document_two_flights_2h | Один документ сел на два разных рейса с разницей меньше 2 часов в один день | 0 |
| B4_ticket_shared | Один номер билета использован разными документами | 0 |
| B5_impossible_age | Возраст пассажира на дату полёта меньше 0 или больше 100 лет | 0 |
| B6_too_many_flights_document | Документы с аномально большим числом полётов (> 9, правило Q3 + 3·IQR) | 182 |
| X1_profile_linked_to_many_documents | Профиль форума совпал с посадками, где разные документы или даты рождения | 3 |
| X2_destination_mismatch | Связанный рейс: город назначения на форуме и в посадке различается | 0 |

## Люди с несколькими типами аномалий

Сущностей с хотя бы одной аномалией: 13817; с двумя и более типами: 709.

| entity | типов | аномалии |
|---|---|---|
| forum:40402 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:63431 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:33989 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:33994 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:63355 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:34000 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:16268 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:63394 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:34045 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:6345 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:62977 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:34115 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:16143 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:34229 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:16069 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:46229 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:63621 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:34310 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:16325 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |
| forum:33976 | 2 | F2_same_name_many_profiles; F4_origin_equals_destination |

## Примеры

### F1_card_shared_by_profiles
Одна карта лояльности (program+number) указана в нескольких профилях форума

```
 profile_id program status card_number_raw card_number    card_key           nickname first_name_norm last_name_norm
      19900      FB  Elite       139888197   139888197 FB139888197 FrequentFlyer29897                               
      47863      FB  Elite       139888197   139888197 FB139888197 FrequentFlyer71993          OLESYA       GOLOVINA
```

### F2_same_name_many_profiles
Одно и то же имя+фамилия у нескольких профилей (тёзки или один человек под разными никами)

```
 profile_id           nickname first_name_norm last_name_norm
       9556 FrequentFlyer14334           ARTEM        ABRAMOV
      27058 FrequentFlyer40667           ARTEM        ABRAMOV
      11358 FrequentFlyer17031           MAXIM        ABRAMOV
      47791 FrequentFlyer71893           MAXIM        ABRAMOV
      52031 FrequentFlyer78233           MAXIM        ABRAMOV
```

### F4_origin_equals_destination
Рейс, у которого аэропорт вылета совпадает с аэропортом прилёта (на практике - заглушка REA у рейсов KE/CZ, ошибка источника)

```
 profile_id  flight_seq       date flight_number  codeshare origin origin_city origin_country_raw destination destination_city destination_country_raw source source_record_id        nickname first_name_norm last_name_norm
         11          10 2017-04-03        KE1333      False    REA       Seoul                 Ko         REA            Seoul                      Ko  forum      forum:11:10 FrequentFlyer18        ALEXANDR       NIKOLAEV
         11          16 2017-03-28        KE1210      False    REA       Seoul                 Ko         REA            Seoul                      Ko  forum      forum:11:16 FrequentFlyer18        ALEXANDR       NIKOLAEV
         13          12 2017-02-21        KE1104      False    REA       Seoul                 Ko         REA            Seoul                      Ko  forum      forum:13:12 FrequentFlyer20                               
         13          18 2017-04-01        KE1609      False    REA       Seoul                 Ko         REA            Seoul                      Ko  forum      forum:13:18 FrequentFlyer20                               
         13          19 2017-01-19        KE1241      False    REA       Seoul                 Ko         REA            Seoul                      Ko  forum      forum:13:19 FrequentFlyer20                               
```

### F6_too_many_flights_profile
Профили с аномально большим числом рейсов (> 37, правило Q3 + 3·IQR)

```
 profile_id  n_flights           nickname first_name_norm last_name_norm
      40326         42 FrequentFlyer60655             YAN         GALKIN
      31965         41 FrequentFlyer48038         UL'YANA     KORCHAGINA
       8206         38 FrequentFlyer12233           ARTEM         LAVROV
      54767         38 FrequentFlyer82348                               
```

### B1_document_different_people
Один номер документа у пассажиров с разными ФИО или датами рождения

```
source_record_id first_name_norm second_name_norm last_name_norm birth_date document_norm flight_date flight_time flight_number destination_city    pnr    ticket_number
 boarding:150151           RAMIL      ALBERTOVICH          BUROV 1995-08-24    8248013778  2017-01-03    11:15:00        SU1273           Moscow        7230123462656045
  boarding:92874          GORDEI               M.         GLEBOV 1982-12-31    8248013778  2017-01-16    01:45:00        SU1057           Moscow EJQBAD 2082229451418171
  boarding:83246          GORDEI               M.         GLEBOV 1982-12-31    8248013778  2017-03-09    07:15:00        SU1276            Kazan        5858732412927507
 boarding:134532          GORDEI       MAKAREVICH         GLEBOV 1982-12-31    8248013778  2017-03-10    14:15:00        SU1281           Moscow BQCUKX                 
```

### B2_person_many_documents
Один и тот же человек (имя+фамилия+дата рождения) летал по разным документам

```
source_record_id first_name_norm second_name_norm last_name_norm birth_date document_norm flight_date flight_time flight_number destination_city pnr    ticket_number
 boarding:126633         AMALIIA               N.   KUDRIAVTSEVA 1985-11-22    1378965068  2017-01-02    11:10:00        SU1483           Moscow                     
 boarding:120481         AMALIIA       RODIONOVNA   KUDRIAVTSEVA 1985-11-22    5518372746  2017-01-04    13:20:00        SU1491           Moscow     5447675451334173
  boarding:21723         AMALIIA       RODIONOVNA   KUDRIAVTSEVA 1985-11-22    5518372746  2017-02-24    21:25:00        SU1322         Murmansk                     
  boarding:37035         AMALIIA               R.   KUDRIAVTSEVA 1985-11-22    5518372746  2017-02-28    21:40:00        SU1493           Moscow                     
```

### B6_too_many_flights_document
Документы с аномально большим числом полётов (> 9, правило Q3 + 3·IQR)

```
document_norm  n_flights first_name_norm last_name_norm birth_date
   1548113497         16           MAIIA       BARANOVA 1970-05-22
   7126372174         15          TIKHON      GONCHAROV 1992-07-11
   5293500602         14          KARINA        NAUMOVA 1989-01-15
   6937933652         14         MIKHAIL     CHEBOTAREV 1995-08-30
   8816864475         14            AMIR         MASLOV 1990-07-23
```

### X1_profile_linked_to_many_documents
Профиль форума совпал с посадками, где разные документы или даты рождения

```
 profile_id first_name_norm last_name_norm birth_date document_norm flight_number flight_date           nickname
      55210          EDUARD          POPOV 1980-03-19    3018045556        SU1395  2017-01-05 FrequentFlyer83017
      55210          EDUARD          POPOV 1984-09-30    4773310642        SU1395  2017-01-05 FrequentFlyer83017
      55210          EDUARD          POPOV 1984-09-30    4773310642        SU1366  2017-05-18 FrequentFlyer83017
```
