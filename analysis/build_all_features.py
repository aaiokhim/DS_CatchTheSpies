"""
Все люди, у которых сработал хотя бы один признак, в одной таблице
(analysis/output/all_features_results.csv) и статистика по ним (analysis/reports/ALL_FEATURES_SUMMARY.md).

python3 analysis/build_all_features.py
"""
import re

import pandas as pd

from build_report import CATEGORY_TITLES, OUT, STRENGTH, TITLES, HERE, first_name, md_table
from common import RES, split_partners

DETAIL = {
    "A1": ["A1_documents"], "A2": ["A2_documents"], "A3": ["A3_kind", "A3_flights"], "A4": ["A4_cards"],
    "A5": ["A5_user_uids"], "A6": ["A6_forum_profiles"], "A7": ["A7_values"],
    "B1": ["B1_share"], "B2": ["B2_share"], "B3": ["B3_share"], "B4": ["B4_tickets"], "B5": ["B5_sources"],
    "C1": ["C1_examples"], "C2": ["C2_threshold"], "C3": ["C3_examples"], "C4": ["C4_examples"],
    "C5": ["C5_airports"], "C6": ["C6_examples"],
    "D1": ["D1_companions"], "D2": ["D2_partners"], "E1": ["E1_cards"], "E2": ["E2_direction"],
}


def order(c):
    return c[0], int(c[1:])


def main():
    files = sorted((p for p in OUT.glob("*_results.csv") if re.fullmatch(r"[A-E]\d+_results\.csv", p.name)),
                   key=lambda p: order(p.name.split("_")[0]))
    if not files:
        raise SystemExit("нет файлов <код>_results.csv - сначала запусти признаки")
    feats = {p.name.split("_")[0]: pd.read_csv(p, dtype={"person_id": str}) for p in files}
    codes = sorted(feats, key=order)
    print("признаки: " + ", ".join(f"{c} {len(feats[c])}" for c in codes))

    a3 = feats.get("A3")
    weak_a3 = set(a3.loc[a3["A3_kind"] == "namesakes", "person_id"]) if a3 is not None and "A3_kind" in a3 else set()

    rows = []
    for c, d in feats.items():
        if not len(d):
            continue
        det = next((col for col in DETAIL.get(c, []) if col in d), None)
        rows.append(pd.DataFrame({
            "person_id": d["person_id"], "feature": c,
            "count": pd.to_numeric(d.get(f"{c}_count"), errors="coerce").fillna(1).astype(int),
            "detail": d[det].astype(str).str.slice(0, 300) if det else "",
            "name_variants": d["name_variants"]}))
    long = pd.concat(rows, ignore_index=True)
    long["strength"] = long["feature"].map(STRENGTH).fillna("слабый")
    long.loc[(long["feature"] == "A3") & long["person_id"].isin(weak_a3), "strength"] = "слабый"
    long["category"] = long["feature"].str[0]

    g = long.groupby("person_id")
    feat_list = lambda s: "; ".join(sorted(set(s), key=order))
    res = pd.DataFrame({
        "name_variants": g["name_variants"].first(),
        "n_features": g["feature"].nunique(),
        "n_strong": g["strength"].agg(lambda s: int((s == "сильный").sum())),
        "n_medium": g["strength"].agg(lambda s: int((s == "средний").sum())),
        "n_weak": g["strength"].agg(lambda s: int((s == "слабый").sum())),
        "n_categories": g["category"].nunique(),
        "categories": g["category"].agg(lambda s: "; ".join(sorted(set(s)))),
        "triggered_features": g["feature"].agg(feat_list),
    }).reset_index()
    strong = long[long["strength"] == "сильный"].groupby("person_id")["feature"].agg(feat_list)
    res["strong_features"] = res["person_id"].map(strong).fillna("")
    res["name"] = res["name_variants"].map(first_name)
    for cat in "ABCDE":
        n = long[long["category"] == cat].groupby("person_id")["feature"].nunique()
        res[f"{cat}_flags_count"] = res["person_id"].map(n).fillna(0).astype(int)

    per = pd.read_parquet(RES / "persons.parquet",
                          columns=["person_id", "sources", "n_records", "n_flight_events", "birth_dates",
                                   "documents", "loyalty_ids"])
    res = res.merge(per, on="person_id", how="left")
    partners = split_partners(verbose=False)
    res["same_person_ids"] = res["person_id"].map(lambda p: "; ".join(sorted(partners.get(p, set()))))
    res["is_fragment"] = (res["name_variants"].isna() & res["n_records"].eq(1)).astype(int)

    for c in codes:
        sub = long[long["feature"] == c].set_index("person_id")
        res[f"{c}_flag"] = res["person_id"].isin(sub.index).astype(int)
        res[f"{c}_count"] = res["person_id"].map(sub["count"]).fillna(0).astype(int)
        res[f"{c}_detail"] = res["person_id"].map(sub["detail"]).fillna("")

    res["_named"] = res["is_fragment"].eq(0)
    res = res.sort_values(["n_strong", "_named", "n_medium", "n_categories", "n_features"],
                          ascending=False).drop(columns="_named")
    head = ["person_id", "name", "name_variants", "n_features", "n_strong", "n_medium", "n_weak",
            "n_categories", "categories", "triggered_features", "strong_features"] + \
           [f"{c}_flags_count" for c in "ABCDE"] + \
           ["same_person_ids", "is_fragment", "sources", "n_records", "n_flight_events", "birth_dates",
            "documents", "loyalty_ids"]
    res = res[head + [x for c in codes for x in (f"{c}_flag", f"{c}_count", f"{c}_detail")]]
    assert res["person_id"].is_unique
    res.to_csv(OUT / "all_features_results.csv", index=False, encoding="utf-8-sig")

    N = len(res)
    L = ["# Полная статистика по людям с признаками", "",
         f"Источник: `analysis/output/all_features_results.csv` (скрипт `build_all_features.py`). "
         f"Одна строка = один `person_id`.", "",
         "## 1. Итого", "",
         md_table(pd.DataFrame({"показатель": [
             "person_id хотя бы с одним признаком", "…из них осколков (без имени, одна запись)",
             "…хотя бы с одним сильным признаком", "…хотя бы со средним (без сильных)",
             "…только слабые признаки", "…в ≥2 категориях", "…с ≥2 разными признаками",
             "…с «двойниками» (другой person_id того же человека)"],
             "значение": [N, int(res["is_fragment"].sum()), int((res["n_strong"] > 0).sum()),
                          int(((res["n_strong"] == 0) & (res["n_medium"] > 0)).sum()),
                          int(((res["n_strong"] == 0) & (res["n_medium"] == 0)).sum()),
                          int((res["n_categories"] >= 2).sum()), int((res["n_features"] >= 2).sum()),
                          int((res["same_person_ids"] != "").sum())]})), ""]

    tab = pd.DataFrame({"код": codes, "признак": [TITLES.get(c, "") for c in codes],
                        "сила": [STRENGTH.get(c, "") for c in codes],
                        "людей": [int(res[f"{c}_flag"].sum()) for c in codes],
                        "случаев": [int(res[f"{c}_count"].sum()) for c in codes],
                        "только этот признак": [int(((res[f"{c}_flag"] == 1) & (res["n_features"] == 1)).sum())
                                                for c in codes]})
    L += ["## 2. По признакам", "", md_table(tab), ""]

    cat = pd.DataFrame({"категория": list("ABCDE"),
                        "название": [CATEGORY_TITLES.get(c, "") for c in "ABCDE"],
                        "людей": [int((res[f"{c}_flags_count"] > 0).sum()) for c in "ABCDE"],
                        "с ≥2 признаками категории": [int((res[f"{c}_flags_count"] >= 2).sum()) for c in "ABCDE"]})
    L += ["## 3. По категориям", "", md_table(cat), ""]

    for col, title in [("n_features", "разных признаков"), ("n_categories", "категорий")]:
        vc = res[col].value_counts().sort_index()
        L += [f"## {'4' if col == 'n_features' else '5'}. Распределение: {title}", "",
              md_table(pd.DataFrame({title: vc.index, "людей": vc.values})), ""]

    st = pd.DataFrame({"сильных": res["n_strong"], "средних": res["n_medium"], "слабых": res["n_weak"]})
    vc = st.value_counts().reset_index(name="людей").sort_values(["сильных", "средних", "слабых"], ascending=False)
    L += ["## 6. Сочетания по силе признаков", "", md_table(vc), ""]

    combo = res["triggered_features"].value_counts().head(25)
    L += ["## 7. Самые частые сочетания признаков (топ-25)", "",
          md_table(pd.DataFrame({"признаки": combo.index, "людей": combo.values})), ""]

    flags = res[[f"{c}_flag" for c in codes]].set_axis(codes, axis=1)
    co = flags.T.dot(flags)
    co.insert(0, "признак", co.index)
    L += ["## 8. Совместная встречаемость признаков", "",
          "Число людей, у которых сработали оба признака (на диагонали - всего людей с признаком).", "",
          md_table(co), ""]

    top = res[(res["n_strong"] > 0) | (res["n_categories"] >= 3)]
    top = top[["person_id", "name", "n_strong", "n_medium", "n_weak", "n_categories", "triggered_features",
               "same_person_ids", "is_fragment"]]
    L += ["## 9. Люди с сильным признаком или в ≥3 категориях", "",
          f"Всего {len(top)} (показано до 200; полный список - в CSV); осколки (`is_fragment = 1`) - "
          f"отдельные записи без имени.", "", md_table(top, max_rows=200), ""]
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "ALL_FEATURES_SUMMARY.md").write_text("\n".join(L), encoding="utf-8")

    print(f"людей с признаками: {N} (осколков {int(res['is_fragment'].sum())}); с сильным: "
          f"{int((res['n_strong'] > 0).sum())}; в ≥2 категориях: {int((res['n_categories'] >= 2).sum())}")
    print(f"-> {OUT / 'all_features_results.csv'}")
    print(f"-> {HERE / 'ALL_FEATURES_SUMMARY.md'}")


if __name__ == "__main__":
    main()
