"""
A7. Разный пол у одного человека в разных источниках (sex, title MR/MRS).

python3 analysis/A7_sex_mismatch.py
"""
import pandas as pd

from common import MERGED, links, save, PASSENGERS_ALL


def main():
    P = pd.read_parquet(PASSENGERS_ALL, columns=["source_record_id", "source", "sex", "title"])
    t = P["title"].astype("string").str.upper().map({"MR": "Male", "MRS": "Female"})
    P["sx"] = P["sex"].astype("string").str.strip().str.capitalize().fillna(t)
    P = P.dropna(subset=["sx"]).merge(links(), on="source_record_id")
    n = P.groupby("person_id")["sx"].transform("nunique")
    hit = P[n > 1]
    print(f"записей с полом: {len(P)}; людей с разным полом: {hit['person_id'].nunique()}")

    rows = []
    for pid, g in hit.groupby("person_id"):
        vc = g["sx"].value_counts()
        minority = vc.index[-1]
        rows.append({
            "person_id": pid, "A7_flag": 1, "A7_count": int(vc.iloc[-1]),
            "A7_values": "; ".join(f"{k}: {v}" for k, v in vc.items()),
            "A7_sources": "; ".join(sorted(set(g.loc[g["sx"] == minority, "source"]))),
        })
    save(pd.DataFrame(rows, columns=["person_id", "A7_flag", "A7_count", "A7_values", "A7_sources"]),
         "A7", ["A7_values", "A7_sources"])


if __name__ == "__main__":
    main()
