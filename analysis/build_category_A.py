"""
Сводит признаки A1-A7 в analysis/output/category_A_results.csv.

python3 analysis/build_category_A.py
"""

import pandas as pd

from common import OUT

CATEGORY = "A"
FEATURES = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]


def main():
    merged, names = None, []
    for f in FEATURES:
        path = OUT / f"{f}_results.csv"
        if not path.exists():
            print(f"!! нет {path.name} - признак {f} считается не сработавшим")
            continue
        df = pd.read_csv(path, dtype={"person_id": str})
        assert df["person_id"].is_unique, f"{path.name}: person_id повторяется"
        names.append(df[["person_id", "name_variants"]])
        part = df[["person_id", f"{f}_flag", f"{f}_count"]]
        merged = part if merged is None else merged.merge(part, on="person_id", how="outer")
        print(f"{f}: {len(df)} человек")
    if merged is None:
        raise SystemExit("нет ни одного файла признаков")

    for f in FEATURES:
        for c in (f"{f}_flag", f"{f}_count"):
            merged[c] = merged[c].fillna(0).astype(int) if c in merged else 0

    flags = merged[[f"{f}_flag" for f in FEATURES]]
    merged[f"{CATEGORY}_flags_count"] = flags.sum(axis=1)
    merged[f"{CATEGORY}_total_occurrences"] = merged[[f"{f}_count" for f in FEATURES]].sum(axis=1)
    merged[f"{CATEGORY}_triggered_features"] = flags.apply(
        lambda r: "; ".join(f for f in FEATURES if r[f"{f}_flag"] == 1), axis=1)

    nm = pd.concat(names).dropna().drop_duplicates("person_id")
    merged = merged.merge(nm, on="person_id", how="left")
    cols = ["person_id", "name_variants"] + [c for f in FEATURES for c in (f"{f}_flag", f"{f}_count")] + \
           [f"{CATEGORY}_flags_count", f"{CATEGORY}_total_occurrences", f"{CATEGORY}_triggered_features"]
    merged = merged[cols].sort_values([f"{CATEGORY}_flags_count", f"{CATEGORY}_total_occurrences"],
                                      ascending=False)
    merged.to_csv(OUT / f"category_{CATEGORY}_results.csv", index=False)
    print(f"\ncategory_{CATEGORY}: {len(merged)} человек")
    print(merged[f"{CATEGORY}_flags_count"].value_counts().sort_index().rename("людей по числу признаков").to_string())
    print(f"-> {OUT / f'category_{CATEGORY}_results.csv'}")


if __name__ == "__main__":
    main()
