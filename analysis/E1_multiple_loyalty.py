"""
E1. Много карт лояльности или несколько карт одной программы.

python3 analysis/E1_multiple_loyalty.py [--k 1.5]
"""
import argparse

import pandas as pd

from common import RES, OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=float, default=1.5)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants", "loyalty_ids"])
    per = per.dropna(subset=["loyalty_ids"])
    per["cards"] = per["loyalty_ids"].str.split("; ").map(lambda x: sorted({c for c in x if c.strip()}))
    per["n_cards"] = per["cards"].map(len)
    per["n_programs"] = per["cards"].map(lambda x: len({c.split(" ")[0] for c in x}))
    per["same_program"] = per["n_cards"] - per["n_programs"]

    q1, q3 = per["n_cards"].quantile([0.25, 0.75])
    thr = max(q3 + a.k * (q3 - q1), 2)
    print("число карт:\n" + per["n_cards"].value_counts().sort_index().to_string())
    print(f"порог по числу карт: > {thr:g}; людей с ≥2 картами одной программы: {int((per.same_program > 0).sum())}")

    many, same = per["n_cards"] > thr, per["same_program"] > 0
    hit = per[many | same].copy()
    hit["E1_reason"] = [("many_cards" if m else "") + ("; " if m and s else "") + ("same_program" if s else "")
                        for m, s in zip(many[many | same], same[many | same])]
    res = pd.DataFrame({
        "person_id": hit["person_id"], "name_variants": hit["name_variants"], "E1_flag": 1,
        "E1_count": hit["n_cards"], "E1_n_programs": hit["n_programs"],
        "E1_same_program_cards": hit["same_program"], "E1_threshold": thr,
        "E1_reason": hit["E1_reason"], "E1_cards": hit["cards"].map("; ".join),
    }).sort_values(["E1_same_program_cards", "E1_count"], ascending=False)
    res.to_csv(OUT / "E1_results.csv", index=False)
    print(f"E1 сработал у {len(res)} человек -> {OUT / 'E1_results.csv'}")


if __name__ == "__main__":
    main()
