"""
B5. Много перелётов, есть записи Sirena, но даты рождения нет нигде.

python3 analysis/B5_no_birth_date.py [--quantile 0.95]
"""
import argparse

import pandas as pd

from common import RES, save, split_partners, union_events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quantile", type=float, default=0.95)
    a = ap.parse_args()
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "sources", "birth_dates"])
    partners = split_partners(verbose=False)
    has_birth = set(per.loc[per["birth_dates"].notna(), "person_id"])
    u = union_events()
    n = u.groupby("person_id").size()

    p = per[per["sources"].fillna("").str.contains("sirena")].copy()
    p["n_flights"] = p["person_id"].map(n).fillna(0).astype(int)
    p["birth_known"] = [pid in has_birth or bool(partners.get(pid, set()) & has_birth) for pid in p["person_id"]]
    thr = p["n_flights"].quantile(a.quantile)
    hit = p[~p["birth_known"] & (p["n_flights"] > thr)]
    print(f"людей с записями Sirena: {len(p)}; без даты рождения (и у двойников): {int((~p.birth_known).sum())}; "
          f"порог перелётов > {thr:g}")
    res = pd.DataFrame({"person_id": hit["person_id"], "B5_flag": 1, "B5_count": hit["n_flights"],
                        "B5_threshold": thr, "B5_sources": hit["sources"]})
    save(res, "B5", ["B5_threshold", "B5_sources"])


if __name__ == "__main__":
    main()
