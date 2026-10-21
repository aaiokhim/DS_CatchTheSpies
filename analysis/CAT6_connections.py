"""
Категория 6: связи всех людей с людьми из списка A-E (совместные перелёты, общие документы,
карты, user_uid, билеты, брони). Признаки D1 и D2 кандидатами не считаются.

python3 analysis/CAT6_connections.py [--min-shared 3] [--max-group 300]
"""
import argparse
import re

import pandas as pd

from build_report import HERE, OUT, STRENGTH, first_name, md_table
from common import MERGED, RES, analysis_groups, links, skeleton, read_flights_all, PASSENGERS_ALL

LINK_FEATURES = {"D1", "D2"}
LEVEL = {"сильный": 3, "средний": 2, "слабый": 1}
LEVEL_NAME = {3: "strong", 2: "medium", 1: "weak"}


def order(c):
    return c[0], int(c[1:])


def load_seeds():
    rows = []
    for p in OUT.glob("*_results.csv"):
        if not re.fullmatch(r"[A-E]\d+_results\.csv", p.name):
            continue
        code = p.name.split("_")[0]
        if code in LINK_FEATURES:
            continue
        d = pd.read_csv(p, dtype={"person_id": str})
        if not len(d):
            continue
        lvl = LEVEL.get(STRENGTH.get(code, "слабый"), 1)
        part = pd.DataFrame({"person_id": d["person_id"], "feature": code, "level": lvl})
        if code == "A3" and "A3_kind" in d:
            part.loc[d["A3_kind"].eq("namesakes").values, "level"] = 1
        rows.append(part)
    if not rows:
        raise SystemExit("нет результатов признаков A-E в analysis/output/")
    return pd.concat(rows, ignore_index=True)


def cotravel_pairs(gid, seed_groups, min_shared, max_group):
    ev = pd.read_parquet(RES / "flight_events.parquet", columns=["person_id", "flight_number", "flight_date"])
    ev["g"] = ev["person_id"].map(gid).fillna(ev["person_id"])
    ev = ev[["g", "flight_number", "flight_date"]].drop_duplicates()
    size = ev.groupby(["flight_number", "flight_date"])["g"].transform("size")
    skipped = ev.loc[size > max_group, ["flight_number", "flight_date"]].drop_duplicates().shape[0]
    ev = ev[(size >= 2) & (size <= max_group)]
    seed_ev = ev[ev["g"].isin(seed_groups)]
    pairs = seed_ev.merge(ev, on=["flight_number", "flight_date"], suffixes=("_seed", ""))
    pairs = pairs[pairs["g"] != pairs["g_seed"]]
    sh = pairs.groupby(["g", "g_seed"]).size().rename("strength").reset_index()
    sh = sh[sh["strength"] >= min_shared]
    print(f"cotravel: рейс-дней пропущено (> {max_group} людей): {skipped}; пар с ≥{min_shared} общими "
          f"перелётами: {len(sh)}")
    return sh.assign(link_type="cotravel", key="")


def identifier_pairs(gid, seed_groups):
    lk = links()
    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source", "source_record_id", "source_person_id", "document", "loyalty_ids", "e_ticket"])
    F = read_flights_all(columns=["source_record_id", "flight_number", "flight_date", "loyalty_id", "document",
                                 "pnr", "e_ticket"])
    keys = []
    keys.append(P[["source_record_id"]].assign(link_type="document", key=P["document"]))
    card = P[["source_record_id", "loyalty_ids"]].dropna()
    card = card.assign(key=card["loyalty_ids"].str.split(";")).explode("key")
    keys.append(card[["source_record_id", "key"]].assign(link_type="card"))
    pz = P[P["source"] == "pointz"]
    keys.append(pz[["source_record_id"]].assign(link_type="pointz_uid", key=pz["source_person_id"]))
    keys.append(P[["source_record_id"]].assign(link_type="ticket", key=P["e_ticket"]))
    keys.append(F[["source_record_id"]].assign(link_type="document", key=F["document"]))
    keys.append(F[["source_record_id"]].assign(link_type="card", key=F["loyalty_id"]))
    keys.append(F[["source_record_id"]].assign(link_type="ticket", key=F["e_ticket"]))
    keys.append(F[["source_record_id"]].assign(
        link_type="pnr", key=F["pnr"] + "|" + F["flight_number"] + "|" + F["flight_date"]))
    K = pd.concat(keys, ignore_index=True).dropna(subset=["key"])
    K["key"] = K["key"].astype(str).str.strip()
    K = K[K["key"].ne("") & ~K["key"].str.contains("nan", regex=False)]
    K = K[K.duplicated(["link_type", "key"], keep=False)]
    K = K.merge(lk, on="source_record_id")
    K["g"] = K["person_id"].map(gid).fillna(K["person_id"])
    K = K[["link_type", "key", "g"]].drop_duplicates()
    n = K.groupby(["link_type", "key"])["g"].transform("nunique")
    K = K[n > 1]
    seed_side = K[K["g"].isin(seed_groups)]
    pr = seed_side.merge(K, on=["link_type", "key"], suffixes=("_seed", ""))
    pr = pr[pr["g"] != pr["g_seed"]]
    print("общие идентификаторы у разных людей: " +
          (", ".join(f"{t} {k}" for t, k in K.groupby("link_type")["key"].nunique().items()) or "нет"))
    return (pr.groupby(["g", "g_seed", "link_type"])["key"]
              .agg(lambda s: "; ".join(sorted(set(s))[:5])).reset_index().assign(strength=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-shared", type=int, default=3)
    ap.add_argument("--max-group", type=int, default=300)
    a = ap.parse_args()

    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants"])
    groups = analysis_groups()
    gid = groups.set_index("person_id")["analysis_person_id"]
    members = groups.groupby("analysis_person_id")["person_id"].agg(lambda s: "; ".join(sorted(s)))

    per["g"] = per["person_id"].map(gid).fillna(per["person_id"])
    gnames = per.dropna(subset=["name_variants"]).groupby("g")["name_variants"].agg("; ".join)

    seeds = load_seeds()
    seeds["g"] = seeds["person_id"].map(gid).fillna(seeds["person_id"])
    sg = seeds.groupby("g")
    seed_info = pd.DataFrame({"level": sg["level"].max(),
                              "features": sg["feature"].agg(lambda s: "; ".join(sorted(set(s), key=order)))})
    print(f"кандидатов (людей с признаками A-E, кроме D1/D2): {len(seed_info)} - "
          + ", ".join(f"{LEVEL_NAME[k]} {v}" for k, v in seed_info["level"].value_counts().sort_index(ascending=False).items()))
    print(f"всего людей (групп person_id) проверяется: {per['g'].nunique()}")

    seed_groups = set(seed_info.index)
    pairs = pd.concat([cotravel_pairs(gid, seed_groups, a.min_shared, a.max_group),
                       identifier_pairs(gid, seed_groups)], ignore_index=True)
    keys = gnames.map(lambda v: {skeleton(x) for x in str(v).split("; ") if x.strip()} - {""})
    k1, k2 = pairs["g"].map(keys), pairs["g_seed"].map(keys)
    same = pd.Series([bool(isinstance(x, set) and isinstance(y, set) and x & y) for x, y in zip(k1, k2)],
                     index=pairs.index)
    print("исключено как тот же человек (одинаковое имя): " +
          ", ".join(f"{t} {n}" for t, n in pairs[same].groupby("link_type").size().items()))
    pairs = pairs[~same]
    pairs["seed_level"] = pairs["g_seed"].map(seed_info["level"]).map(LEVEL_NAME)
    pairs["seed_features"] = pairs["g_seed"].map(seed_info["features"])
    pairs["seed_name"] = pairs["g_seed"].map(gnames).map(first_name)
    pairs["name"] = pairs["g"].map(gnames).map(first_name)
    pairs = pairs.sort_values(["g", "strength"], ascending=[True, False])
    pairs.rename(columns={"g": "analysis_person_id", "g_seed": "seed_person_id"})[
        ["analysis_person_id", "name", "seed_person_id", "seed_name", "seed_level", "seed_features",
         "link_type", "strength", "key"]].to_csv(OUT / "CAT6_pairs.csv", index=False, encoding="utf-8-sig")
    print(f"связей человек-кандидат: {len(pairs)} ({', '.join(f'{k} {v}' for k, v in pairs['link_type'].value_counts().items())})")

    pairs["lvl"] = pairs["g_seed"].map(seed_info["level"])
    pairs["txt"] = (pairs["g_seed"] + " " + pairs["seed_name"].fillna("") + " [" + pairs["seed_features"] + "] "
                    + pairs["link_type"] + " " + pairs["strength"].astype(str))
    g = pairs.groupby("g")
    per_seed = pairs.groupby(["g", "g_seed"])["lvl"].max().reset_index()
    ps = per_seed.groupby("g")
    res = pd.DataFrame({
        "CAT6_flag": 1,
        "CAT6_count": ps["g_seed"].nunique(),
        "CAT6_strong": ps["lvl"].agg(lambda s: int((s == 3).sum())),
        "CAT6_medium": ps["lvl"].agg(lambda s: int((s == 2).sum())),
        "CAT6_weak": ps["lvl"].agg(lambda s: int((s == 1).sum())),
        "CAT6_max_level": ps["lvl"].max().map(LEVEL_NAME),
        "CAT6_link_types": g["link_type"].agg(lambda s: "; ".join(sorted(set(s)))),
        "CAT6_max_shared_flights": pairs[pairs["link_type"] == "cotravel"].groupby("g")["strength"].max(),
        "CAT6_links": g["txt"].agg(lambda s: " | ".join(s.head(10))),
    })
    res["CAT6_max_shared_flights"] = res["CAT6_max_shared_flights"].fillna(0).astype(int)
    res["self_features"] = res.index.map(seed_info["features"]).fillna("")
    res["self_flagged"] = (res["self_features"] != "").astype(int)
    res["clean_but_linked"] = 1 - res["self_flagged"]
    res = res.reset_index().rename(columns={"g": "analysis_person_id"})

    res["CAT6_group"] = res["analysis_person_id"].map(members).fillna("")
    out = res.merge(groups, on="analysis_person_id", how="left")
    out["person_id"] = out["person_id"].fillna(out["analysis_person_id"])
    out = out.drop(columns="analysis_person_id").merge(per[["person_id", "name_variants"]], on="person_id", how="left")
    cols = ["person_id", "name_variants", "CAT6_flag", "CAT6_count", "CAT6_strong", "CAT6_medium", "CAT6_weak",
            "CAT6_max_level", "CAT6_link_types", "CAT6_max_shared_flights", "CAT6_links", "self_flagged",
            "self_features", "clean_but_linked", "CAT6_group"]
    out = out[cols].sort_values(["CAT6_strong", "CAT6_medium", "clean_but_linked", "CAT6_count"], ascending=False)
    assert out["person_id"].is_unique
    out.to_csv(OUT / "CAT6_results.csv", index=False, encoding="utf-8-sig")

    hum = res
    L = ["# Категория 6 - активные связи с людьми из списка A–E", "",
         "Скрипт `analysis/CAT6_connections.py`. Проверены все люди из `integration/resolved/persons`; «человек» - группа "
         "`person_id` одного человека («двойники»). Кандидаты - люди с признаками A–E, кроме D1/D2.", "",
         f"Параметры: cotravel - ≥ {a.min_shared} общих перелётов, рейс-дни с > {a.max_group} людьми пропущены.", "",
         "## 1. Итого", "",
         md_table(pd.DataFrame({"показатель": [
             "людей проверено (групп person_id)", "кандидатов (A–E без D1/D2)",
             "людей со связью хотя бы с одним кандидатом", "…сами «чистые» по A–E (`clean_but_linked`)",
             "…связаны с кандидатом с сильным признаком", "…«чистые» и связаны с сильным кандидатом"],
             "значение": [per["g"].nunique(), len(seed_info), len(hum), int(hum["clean_but_linked"].sum()),
                          int((hum["CAT6_strong"] > 0).sum()),
                          int(((hum["CAT6_strong"] > 0) & (hum["clean_but_linked"] == 1)).sum())]})), "",
         "## 2. По уровню связанного кандидата", ""]
    lv = pd.crosstab(hum["CAT6_max_level"], hum["clean_but_linked"].map({1: "сам чистый", 0: "сам с признаками"}))
    L += [md_table(lv.reset_index().rename(columns={"CAT6_max_level": "макс. уровень кандидата"})), ""]
    lt = pairs.groupby(["link_type", "seed_level"]).size().unstack(fill_value=0)
    L += ["## 3. Связи по типам (пар человек–кандидат)", "", md_table(lt.reset_index()), ""]
    top = hum[(hum["CAT6_strong"] > 0) | (hum["CAT6_medium"] > 0)].sort_values(
        ["CAT6_strong", "CAT6_medium", "clean_but_linked", "CAT6_count"], ascending=False)
    top = top.assign(имя=top["analysis_person_id"].map(gnames).map(first_name))
    L += ["## 4. Связанные с сильными и средними кандидатами", "",
          f"Всего {len(top)} (до 200 строк; полный список - `CAT6_results.csv`).", "",
          md_table(top[["analysis_person_id", "имя", "CAT6_strong", "CAT6_medium", "CAT6_link_types",
                        "self_features", "CAT6_links"]], max_rows=200, max_len=160), ""]
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "CAT6_SUMMARY.md").write_text("\n".join(L), encoding="utf-8")

    print(f"людей со связью с кандидатом: {len(hum)}; из них сами чистые: {int(hum['clean_but_linked'].sum())}; "
          f"связаны с сильным кандидатом: {int((hum['CAT6_strong'] > 0).sum())}")
    print(f"-> {OUT / 'CAT6_results.csv'}\n-> {OUT / 'CAT6_pairs.csv'}\n-> {HERE / 'CAT6_SUMMARY.md'}")


if __name__ == "__main__":
    main()
