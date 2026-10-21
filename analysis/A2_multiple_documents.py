"""
A2. Несколько документов одного типа у одного человека.

Один человек: person_id вместе с двойниками или записи с одинаковыми именем и датой рождения.
Тип документа по длине: 10 цифр - внутренний паспорт, 9 - заграничный.

python3 analysis/A2_multiple_documents.py [--include-two-types]
"""
import argparse

import pandas as pd

from common import MERGED, doc_type, links, name_any, patronymic_letter, save, skeleton, split_partners, PASSENGERS_ALL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-two-types", action="store_true")
    a = ap.parse_args()

    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source_record_id", "full_name_raw", "first_name_raw", "middle_name_raw",
                                 "last_name_raw", "birth_date", "document"]).dropna(subset=["document"])
    P = P.merge(links(), on="source_record_id")
    P["skel"] = name_any(P).map(skeleton)
    P["patr"] = [patronymic_letter(m, f) for m, f in zip(P["middle_name_raw"], P["full_name_raw"])]
    patr_by_doc = P.dropna(subset=["patr"]).groupby("document")["patr"].agg(set)

    partners = split_partners()
    groups = []
    for pid, g in P.groupby("person_id"):
        members = {pid} | partners.get(pid, set())
        groups.append((pid, members, "person_id"))
    by_pid = P.groupby("person_id")["document"].agg(set)

    nb = P.dropna(subset=["birth_date"])
    nb = nb[nb["skel"] != ""]
    key_pids = nb.groupby(["skel", "birth_date"])["person_id"].agg(set)
    key_docs = nb.groupby(["skel", "birth_date"])["document"].agg(set)

    found = {}
    def check(pid, docs, how, related=frozenset()):
        types = {}
        for d in docs:
            types.setdefault(doc_type(d), set()).add(d)
        same = max((len(v) for v in types.values()), default=0) >= 2
        if same or (a.include_two_types and len(docs) >= 2):
            r = found.setdefault(pid, {"docs": set(), "how": set(), "related": set(), "same": False})
            r["docs"] |= docs
            r["how"].add(how)
            r["related"] |= set(related) - {pid}
            r["same"] |= same

    for pid, members, how in groups:
        docs = set().union(*(by_pid.get(m, set()) for m in members))
        check(pid, docs, how)
    for k, pids in key_pids.items():
        if len(key_docs[k]) >= 2:
            for pid in pids:
                check(pid, key_docs[k], "name+birth_date", pids)

    rows = []
    for pid, r in found.items():
        types = {}
        for d in r["docs"]:
            types.setdefault(doc_type(d), set()).add(d)
        rows.append({
            "person_id": pid, "A2_flag": 1,
            "A2_count": max(len(v) for v in types.values()) - 1 if r["same"] else len(r["docs"]) - 1,
            "A2_documents": "; ".join(f"{d} ({doc_type(d)})" for d in sorted(r["docs"])),
            "A2_same_type": int(r["same"]),
            "A2_found_by": "; ".join(sorted(r["how"])),
            "A2_related_person_ids": "; ".join(sorted(r["related"])),
            "A2_patronymics": "; ".join(f"{d}: {''.join(sorted(patr_by_doc.get(d, set()))) or '?'}"
                                        for d in sorted(r["docs"])),
        })
    print(f"режим: {'любые ≥2 документа' if a.include_two_types else '≥2 документа ОДНОГО типа'}")
    save(pd.DataFrame(rows, columns=["person_id", "A2_flag", "A2_count", "A2_documents", "A2_same_type",
                                     "A2_found_by", "A2_related_person_ids", "A2_patronymics"]),
         "A2", ["A2_documents", "A2_same_type", "A2_found_by", "A2_related_person_ids", "A2_patronymics"])


if __name__ == "__main__":
    main()
