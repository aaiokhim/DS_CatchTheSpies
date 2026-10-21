"""
A1. Один документ у разных людей (документы, исключённые склейкой как конфликтные).

python3 analysis/A1_shared_document.py
"""
import pandas as pd

from common import MERGED, RES, links, name_any, save, PASSENGERS_ALL


def main():
    conf = pd.read_csv(RES / "conflicted_keys.csv", dtype=str)
    docs = conf[conf["key_type"] == "doc"].assign(document=lambda d: d["key"].str.replace("doc:", "", regex=False))
    print(f"общих документов в conflicted_keys: {len(docs)}")

    P = pd.read_parquet(PASSENGERS_ALL)
    P = P[P["document"].isin(docs["document"])]
    P["name"] = name_any(P)
    P = P.merge(links(), on="source_record_id")
    print(P[["person_id", "source", "name", "birth_date", "document"]].to_string(index=False))

    rows = []
    for pid, g in P.groupby("person_id"):
        mine = set(g["name"].dropna())
        others = P[P["document"].isin(g["document"]) & (P["person_id"] != pid)]
        rows.append({
            "person_id": pid, "A1_flag": 1, "A1_count": g["document"].nunique(),
            "A1_documents": "; ".join(sorted(g["document"].unique())),
            "A1_other_people": "; ".join(sorted(set(others["name"].dropna()) - mine)),
            "A1_reason": "; ".join(sorted(docs[docs["document"].isin(g["document"])]["reason"].unique())),
        })
    save(pd.DataFrame(rows, columns=["person_id", "A1_flag", "A1_count", "A1_documents",
                                     "A1_other_people", "A1_reason"]),
         "A1", ["A1_documents", "A1_other_people", "A1_reason"])


if __name__ == "__main__":
    main()
