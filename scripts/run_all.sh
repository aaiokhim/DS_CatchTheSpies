#!/usr/bin/env bash
# Запуск всего проекта по порядку. Без аргументов - начиная со склейки (integration/merged уже в репозитории).
# С --from-raw - с самого начала, нужны исходники в data/raw и таблицы участников в participants/*/output.
set -e
cd "$(dirname "$0")/.."

if [ "$1" == "--from-raw" ]; then
    python3 participants/p2_forum_boarding/src/pipeline.py
    python3 integration/src/merge_all.py --no-csv
fi

python3 integration/src/resolve_entities.py --no-csv
python3 integration/src/name_check.py
python3 integration/src/name_candidates.py

for s in D1_cotravelers D1_same_person_check D1_two_passports_check D2_shared_pnr build_category_D \
         A1_shared_document A2_multiple_documents A3_same_flight_different_document A4_shared_loyalty_card \
         A5_shared_pointz_uid A6_anonymous_forum_linked A7_sex_mismatch build_category_A \
         B1_boarding_without_booking B2_booking_without_boarding B3_loyalty_only_flights B4_shared_ticket \
         B5_no_birth_date build_category_B \
         C1_impossible_route C2_many_flights C3_short_international_trips C5_rare_destinations \
         C6_bursty_activity build_category_C \
         E1_multiple_loyalty E2_source_imbalance build_category_E \
         build_report build_all_features CAT6_connections; do
    echo "== $s"
    python3 analysis/$s.py || echo "!! $s не посчитан"
done
