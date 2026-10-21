"""
A3. Тот же рейс и дата, то же имя, но другой документ того же типа.

Каждая группа помечается как namesakes (разные даты рождения или отчества) или same_person_possible.

python3 analysis/A3_same_flight_different_document.py
"""
import itertools

import pandas as pd

from common import MERGED, doc_type, links, name_any, patronymic_letter, save, skeleton, read_flights_all, PASSENGERS_ALL


def different_people(a, b):
    if a["birth"] and b["birth"] and not (a["birth"] & b["birth"]):
        return True
    if a["patr"] and b["patr"] and not (a["patr"] & b["patr"]):
        return True
    return False


def main():
    F = read_flights_all(columns=["source_record_id", "source", "flight_number", "flight_date", "document"]
                        ).dropna(subset=["document"])
    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source_record_id", "full_name_raw", "first_name_raw", "middle_name_raw",
                                 "last_name_raw", "birth_date", "document"])
    P["skel"] = name_any(P).map(skeleton)
    P["patr"] = [patronymic_letter(m, f) for m, f in zip(P["middle_name_raw"], P["full_name_raw"])]

    pd_ = P.dropna(subset=["document"])
    ident = {d: {"birth": set(g["birth_date"].dropna()), "patr": set(g["patr"].dropna())}
             for d, g in pd_.groupby("document")}

    F = F.merge(P[["source_record_id", "skel"]], on="source_record_id").merge(links(), on="source_record_id")
    F = F[F["skel"] != ""]
    F["dtype"] = F["document"].map(doc_type)

    key = ["flight_number", "flight_date", "skel", "dtype"]
    n = F.groupby(key)["document"].transform("nunique")
    cand = F[n >= 2]
    n_groups = cand[key].drop_duplicates().shape[0]

    kinds = []
    for k, g in cand.groupby(key):
        docs = sorted(set(g["document"]))
        same = any(not different_people(ident[a], ident[b]) for a, b in itertools.combinations(docs, 2))
        kinds.append((*k, "same_person_possible" if same else "namesakes"))
    kinds = pd.DataFrame(kinds, columns=key + ["kind"])
    hit = cand.merge(kinds, on=key)
    print(f"записей с документом: {len(F)}; групп (рейс+дата+имя+тип) с ≥2 документами: {n_groups}")
    print(f"  ...тёзки (разные даты рождения или отчества): {int((kinds.kind == 'namesakes').sum())}")
    print(f"  ...без доказательства, что это разные люди: {int((kinds.kind == 'same_person_possible').sum())}")
    print("  (в результат записываются оба типа; тип - в колонке A3_kind)")

    def ident_txt(d):
        i = ident.get(d, {"birth": set(), "patr": set()})
        return f"{d} (рожд. {', '.join(sorted(i['birth'])) or '?'}; отч. {''.join(sorted(i['patr'])) or '?'})"

    rows = []
    for pid, g in hit.groupby("person_id"):
        grp = hit.merge(g[key].drop_duplicates(), on=key)
        fl = (g["flight_number"] + " " + g["flight_date"]).drop_duplicates()
        rows.append({
            "person_id": pid, "A3_flag": 1, "A3_count": len(fl),
            "A3_kind": "; ".join(sorted(set(g["kind"]))),
            "A3_flights": "; ".join(sorted(fl)[:10]),
            "A3_documents": "; ".join(ident_txt(d) for d in sorted(set(grp["document"]))),
            "A3_sources": "; ".join(sorted(set(grp["source"]))),
            "A3_other_person_ids": "; ".join(sorted(set(grp["person_id"]) - {pid})),
        })
    save(pd.DataFrame(rows, columns=["person_id", "A3_flag", "A3_count", "A3_kind", "A3_flights",
                                     "A3_documents", "A3_sources", "A3_other_person_ids"]),
         "A3", ["A3_kind", "A3_flights", "A3_documents", "A3_sources", "A3_other_person_ids"])


if __name__ == "__main__":
    main()
