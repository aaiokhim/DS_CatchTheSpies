# Категория 6 - активные связи с людьми из списка A–E

Скрипт `analysis/CAT6_connections.py`. Проверены все люди из `integration/resolved/persons`; «человек» - группа `person_id` одного человека («двойники»). Кандидаты - люди с признаками A–E, кроме D1/D2.

Параметры: cotravel - ≥ 3 общих перелётов, рейс-дни с > 300 людьми пропущены.

## 1. Итого

| показатель | значение |
|---|---|
| людей проверено (групп person_id) | 584394 |
| кандидатов (A–E без D1/D2) | 31552 |
| людей со связью хотя бы с одним кандидатом | 940 |
| …сами «чистые» по A–E (`clean_but_linked`) | 903 |
| …связаны с кандидатом с сильным признаком | 18 |
| …«чистые» и связаны с сильным кандидатом | 1 |

## 2. По уровню связанного кандидата

| макс. уровень кандидата | сам с признаками | сам чистый |
|---|---|---|
| medium | 7 | 5 |
| strong | 17 | 1 |
| weak | 13 | 897 |

## 3. Связи по типам (пар человек–кандидат)

| link_type | medium | strong | weak |
|---|---|---|---|
| card | 0 | 154 | 0 |
| cotravel | 10 | 1 | 910 |
| document | 0 | 6 | 0 |
| pointz_uid | 2 | 0 | 0 |

## 4. Связанные с сильными и средними кандидатами

Всего 30 (до 200 строк; полный список - `CAT6_results.csv`).

| analysis_person_id | имя | CAT6_strong | CAT6_medium | CAT6_link_types | self_features | CAT6_links |
|---|---|---|---|---|---|---|
| P0019901 | ROMAN MASLENNIKOV | 12 | 0 | card | A4; A6 | P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641  [A4] card 1 / P0595642  [A4] card 1 / P0595… |
| P0595640 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595641  [A4] card 1 / P0595642… |
| P0595641 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595642… |
| P0595642 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595643 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595644 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595645 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595646 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595647 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595648 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0595649 |  | 12 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0047864 GOLOVINA OLESIA [A4; E1] card 1 / P0293273 OLESYA GOLOVINA [A4] card 1 / P0595640  [A4] card 1 / P0595641… |
| P0047864 | GOLOVINA OLESIA | 11 | 0 | card | A4; E1 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0595640  [A4] card 1 / P0595641  [A4] card 1 / P0595642  [A4] card 1 / P0595643  [A4] card 1 / P0595644  [A4] car… |
| P0293273 | OLESYA GOLOVINA | 11 | 0 | card | A4 | P0019901 ROMAN MASLENNIKOV [A4; A6] card 1 / P0595640  [A4] card 1 / P0595641  [A4] card 1 / P0595642  [A4] card 1 / P0595643  [A4] card 1 / P0595644  [A4] car… |
| P0119448 | RAMIL ALBERTOVICH BUROV | 3 | 0 | document | A1 | P0103336 GORDEI M. GLEBOV [A1] document 1 / P0106284 GORDEI M. GLEBOV [A1] document 1 / P0116211 GORDEI MAKAREVICH GLEBOV [A1] document 1 |
| P0055443 |  | 1 | 0 | cotravel |  | P0079348 AMALIIA KUDRIAVTSEVA [A2] cotravel 3 |
| P0103336 | GORDEI M. GLEBOV | 1 | 0 | document | A1 | P0119448 RAMIL ALBERTOVICH BUROV [A1] document 1 |
| P0106284 | GORDEI M. GLEBOV | 1 | 0 | document | A1 | P0119448 RAMIL ALBERTOVICH BUROV [A1] document 1 |
| P0116211 | GORDEI MAKAREVICH GLEBOV | 1 | 0 | document | A1 | P0119448 RAMIL ALBERTOVICH BUROV [A1] document 1 |
| P0071711 | VLADISLAVA E. LEBEDEVA | 0 | 1 | cotravel |  | P0036844  [C3] cotravel 3 |
| P0080459 | ELISEI I. NECHAEV | 0 | 1 | cotravel |  | P0064720  [C3] cotravel 4 |
| P0109895 | RUSTAM IVANOVICH SINITSYN | 0 | 1 | cotravel |  | P0045886  [C3] cotravel 4 |
| P0113006 | ROBERT S. SHIROKOV | 0 | 1 | cotravel |  | P0060228  [C3] cotravel 3 |
| P0121474 | KIREEVA NATALIIA | 0 | 1 | cotravel |  | P0051258  [C3] cotravel 3 |
| P0029586 | STANISLAV KONDRATOV | 0 | 1 | pointz_uid | A5; A6 | P0584736 YULIYA KORSHUNOVA [A5] pointz_uid 1 |
| P0074047 | LILIIA V. VLADIMIROVA | 0 | 1 | cotravel | E2 | P0036521  [C3] cotravel 13 |
| P0079383 | BAZHENOV PETR | 0 | 1 | cotravel | E2 | P0026818  [C3] cotravel 9 |
| P0081510 | ANDREEVA DAR'YA | 0 | 1 | cotravel | E2 | P0039446  [C3] cotravel 8 |
| P0086847 | NATALIIA MIRONOVNA SHISHKINA | 0 | 1 | cotravel | E2 | P0021848  [C3] cotravel 6 |
| P0097532 | ELISEI A. IASHIN | 0 | 1 | cotravel | E2 | P0008109  [C3] cotravel 6 |
| P0584736 | YULIYA KORSHUNOVA | 0 | 1 | pointz_uid | A5 | P0029586 STANISLAV KONDRATOV [A5; A6] pointz_uid 1 |
