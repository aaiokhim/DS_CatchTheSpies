"""
Проверка пар-двойников из D1: противоречат ли друг другу данные двух person_id.

python3 analysis/D1_same_person_check.py
"""

import pandas as pd

from common import RES, OUT


LOYALTY = {"forum", "pointz", "skyteam"}
TRAVEL = {"sirena", "boarding_data", "boarding_passes"}
MIN_OVERLAP = 0.5


def as_set(x):
    return set(x.split("; ")) if isinstance(x, str) and x.strip() else set()


def programs(cards):
    out = {}
    for c in cards:
        p, _, n = c.partition(" ")
        out.setdefault(p, set()).add(n)
    return out


def classify(r):
    s1, s2 = as_set(r.sources_1), as_set(r.sources_2)
    b1, b2 = as_set(r.birth_dates_1), as_set(r.birth_dates_2)
    x1, x2 = as_set(r.sex_1), as_set(r.sex_2)
    d1, d2 = as_set(r.documents_1), as_set(r.documents_2)
    c1, c2 = programs(as_set(r.loyalty_ids_1)), programs(as_set(r.loyalty_ids_2))

    complementary = (s1 <= LOYALTY and s2 <= TRAVEL) or (s2 <= LOYALTY and s1 <= TRAVEL)
    same_trip_source = bool(s1 & TRAVEL) and bool(s2 & TRAVEL)
    birth_conflict = bool(b1 and b2 and not (b1 & b2))
    sex_conflict = bool(len(x1) == 1 and len(x2) == 1 and x1 != x2)
    f1 = {len(d): set() for d in d1}
    for d in d1: f1[len(d)].add(d)
    f2 = {len(d): set() for d in d2}
    for d in d2: f2[len(d)].add(d)
    doc_conflict = any(k in f2 and not (f1[k] & f2[k]) for k in f1)
    two_passports = bool(d1 and d2 and not (d1 & d2) and not doc_conflict)
    card_conflict = any(p in c2 and not (c1[p] & c2[p]) for p in c1)
    small = min(r.n_flight_events_1, r.n_flight_events_2) or 1
    overlap = round(r.shared_flights / small, 2)

    reasons = [n for n, v in [("complementary", complementary), ("same_trip_source", same_trip_source),
                              ("birth_conflict", birth_conflict), ("sex_conflict", sex_conflict),
                              ("doc_conflict", doc_conflict), ("two_passport_types", two_passports),
                              ("card_conflict", card_conflict)] if v]
    reasons.append(f"overlap={overlap}")

    if birth_conflict or sex_conflict:
        cat = "different_people_same_name"
    elif doc_conflict or card_conflict:
        cat = "suspicious_two_identities"
    elif two_passports:
        cat = "same_person_two_passports"
    elif complementary or (not same_trip_source and overlap >= MIN_OVERLAP):
        cat = "split_same_person"
    elif overlap >= MIN_OVERLAP:
        cat = "likely_same_person"
    else:
        cat = "unclear"
    return cat, overlap, "; ".join(reasons)


def main():
    path = OUT / "D1_same_person_candidates.csv"
    if not path.exists():
        raise SystemExit("нет D1_same_person_candidates.csv - сначала запусти analysis/D1_cotravelers.py")
    pairs = pd.read_csv(path, dtype={"person_id_1": str, "person_id_2": str})
    cols = ["person_id", "sources", "birth_dates", "sex", "documents", "loyalty_ids", "n_flight_events"]
    per = pd.read_parquet(RES / "persons.parquet", columns=cols)
    for i in ("1", "2"):
        pairs = pairs.merge(per.add_suffix(f"_{i}").rename(columns={f"person_id_{i}": f"person_id_{i}"}),
                            on=f"person_id_{i}", how="left")

    res = pairs.apply(classify, axis=1, result_type="expand")
    pairs["category"], pairs["overlap"], pairs["reasons"] = res[0], res[1], res[2]
    order = {"suspicious_two_identities": 0, "different_people_same_name": 1, "unclear": 2,
             "same_person_two_passports": 3, "likely_same_person": 4, "split_same_person": 5}
    pairs = pairs.sort_values(["category", "shared_flights"], key=lambda s: s.map(order) if s.name == "category" else -s)
    keep = ["category", "reasons", "person_id_1", "person_id_2", "shared_flights", "overlap",
            "name_1", "name_2", "sources_1", "sources_2", "birth_dates_1", "birth_dates_2",
            "documents_1", "documents_2", "loyalty_ids_1", "loyalty_ids_2",
            "n_flight_events_1", "n_flight_events_2"]
    pairs[keep].to_csv(OUT / "D1_same_person_check.csv", index=False)

    vc = pairs["category"].value_counts()
    L = ["# Пары «одинаковое имя + ≥3 общих перелёта»", "",
         f"Всего пар: {len(pairs)}", "", "| Категория | Пар | Что значит |", "|---|---|---|"]
    meaning = {
        "split_same_person": "один человек, разрезанный склейкой (мили / поездки) - артефакт",
        "suspicious_two_identities": "одни рейсы, разные документы/карты при одинаковых имени, дате рождения и поле - сильный сигнал",
        "different_people_same_name": "разные люди-тёзки (разная дата рождения/пол) многократно летят вместе",
        "same_person_two_passports": "всё совпадает, документы - внутренний + загран: скорее один человек",
        "likely_same_person": "у обоих брони/посадки, противоречий нет, перелёты пересекаются: скорее один человек",
        "unclear": "смотреть вручную",
    }
    for c in ["suspicious_two_identities", "different_people_same_name", "unclear",
              "same_person_two_passports", "likely_same_person", "split_same_person"]:
        L.append(f"| {c} | {int(vc.get(c, 0))} | {meaning[c]} |")
    for c in ["suspicious_two_identities", "different_people_same_name", "unclear", "likely_same_person"]:
        ex = pairs[pairs.category == c].head(10)
        if len(ex):
            L += ["", f"## Примеры: {c}", "", "```",
                  ex[["person_id_1", "person_id_2", "shared_flights", "reasons", "name_1"]].to_string(index=False),
                  "```"]
    (OUT / "D1_same_person_check.md").write_text("\n".join(L), encoding="utf-8")
    print(vc.to_string())
    print(f"-> {OUT / 'D1_same_person_check.csv'}, {OUT / 'D1_same_person_check.md'}")


if __name__ == "__main__":
    main()
