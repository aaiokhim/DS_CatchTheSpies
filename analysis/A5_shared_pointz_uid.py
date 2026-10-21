"""
A5. Один user_uid Pointz у пользователей с разными именами.

python3 analysis/A5_shared_pointz_uid.py
"""
import pandas as pd

from common import MERGED, links, name_any, save, skeleton, PASSENGERS_ALL


def main():
    P = pd.read_parquet(PASSENGERS_ALL)
    P = P[P["source"] == "pointz"].copy()
    P["name"] = name_any(P)
    P["skel"] = P["name"].map(skeleton)
    n = P.groupby("source_person_id")["skel"].transform("nunique")
    hit = P[n > 1].merge(links(), on="source_record_id")
    print(f"user_uid с разными людьми: {hit['source_person_id'].nunique()}")
    if len(hit):
        print(hit[["source_person_id", "source_record_id", "name", "loyalty_ids", "person_id"]].to_string(index=False))

    rows = []
    for pid, g in hit.groupby("person_id"):
        others = hit[hit["source_person_id"].isin(g["source_person_id"]) & (hit["person_id"] != pid)]
        rows.append({
            "person_id": pid, "A5_flag": 1, "A5_count": g["source_person_id"].nunique(),
            "A5_user_uids": "; ".join(sorted(g["source_person_id"].unique())),
            "A5_other_people": "; ".join(sorted(set(others["name"].dropna()) - set(g["name"].dropna()))),
            "A5_has_cards": int(g["loyalty_ids"].notna().any()),
        })
    save(pd.DataFrame(rows, columns=["person_id", "A5_flag", "A5_count", "A5_user_uids", "A5_other_people",
                                     "A5_has_cards"]),
         "A5", ["A5_user_uids", "A5_other_people", "A5_has_cards"])


if __name__ == "__main__":
    main()
