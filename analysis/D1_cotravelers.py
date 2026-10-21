"""
D1. Постоянные попутчики: пары людей с 3 и более общими перелётами.

Пары с одинаковым именем считаются одним человеком и пишутся в D1_same_person_candidates.csv
(файл двойников, его используют другие признаки). Запускать первым из признаков.

python3 analysis/D1_cotravelers.py [--min-shared 3] [--max-group 300]
"""
import argparse
import re

import pandas as pd

from common import RES, OUT


CYR = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               ["A", "B", "V", "G", "D", "E", "E", "ZH", "Z", "I", "I", "K", "L", "M", "N", "O", "P",
                "R", "S", "T", "U", "F", "KH", "TS", "CH", "SH", "SHCH", "", "Y", "", "E", "IU", "IA"]))
PATRONYMIC = re.compile(r"(VICH|VNA|ICH|ICHNA)$")


def skeleton(name):
    s = "".join(CYR.get(ch, ch) for ch in str(name).upper())
    s = re.sub(r"['’`.\-]", "", s)
    words = []
    for w in s.split():
        w = re.sub(r"(.)\1+", r"\1", w.replace("X", "KS").replace("TC", "TS").replace("Y", "I"))
        if len(w) > 1:
            words.append(w)
    if len(words) >= 3:
        words = [w for w in words if not PATRONYMIC.search(w)] or words
    return " ".join(sorted(set(words)))


def name_keys(variants):
    if not isinstance(variants, str):
        return set()
    return {skeleton(v) for v in variants.split("; ") if v.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-shared", type=int, default=3)
    ap.add_argument("--max-group", type=int, default=300)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    ev = pd.read_parquet(RES / "flight_events.parquet", columns=["person_id", "flight_number", "flight_date"])
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants"])

    ev = ev.drop_duplicates()
    size = ev.groupby(["flight_number", "flight_date"])["person_id"].transform("size")
    print(f"перелётов: {len(ev)}; рейс-дней с >{a.max_group} людьми (пропущено): "
          f"{ev[size > a.max_group][['flight_number', 'flight_date']].drop_duplicates().shape[0]}")
    ev = ev[(size >= 2) & (size <= a.max_group)]

    pairs = ev.merge(ev, on=["flight_number", "flight_date"], suffixes=("_1", "_2"))
    pairs = pairs[pairs["person_id_1"] < pairs["person_id_2"]]
    shared = pairs.groupby(["person_id_1", "person_id_2"]).size().rename("shared_flights").reset_index()
    shared = shared[shared["shared_flights"] >= a.min_shared]
    print(f"пар с ≥{a.min_shared} общими перелётами: {len(shared)}")

    keys = per.set_index("person_id")["name_variants"].map(name_keys)
    k1, k2 = shared["person_id_1"].map(keys), shared["person_id_2"].map(keys)
    shared["same_name"] = [bool(x and y and (x & y)) for x, y in zip(k1, k2)]

    same = shared[shared["same_name"]].copy()
    same["name_1"] = same["person_id_1"].map(per.set_index("person_id")["name_variants"])
    same["name_2"] = same["person_id_2"].map(per.set_index("person_id")["name_variants"])
    same.drop(columns="same_name").sort_values("shared_flights", ascending=False) \
        .to_csv(OUT / "D1_same_person_candidates.csv", index=False)

    shared = shared[~shared["same_name"]].drop(columns="same_name")
    shared.to_csv(OUT / "D1_pairs.csv", index=False)
    print(f"из них с тем же именем (вероятно один человек, НЕ попутчики): {len(same)} "
          f"-> D1_same_person_candidates.csv")
    print(f"настоящих пар попутчиков (разные имена): {len(shared)}")

    both = pd.concat([
        shared.rename(columns={"person_id_1": "person_id", "person_id_2": "companion"}),
        shared.rename(columns={"person_id_2": "person_id", "person_id_1": "companion"}),
    ]).sort_values(["person_id", "shared_flights"], ascending=[True, False])
    both["txt"] = both["companion"] + " (" + both["shared_flights"].astype(str) + ")"

    g = both.groupby("person_id")
    res = pd.DataFrame({
        "D1_flag": 1,
        "D1_count": g.size(),
        "D1_max_shared": g["shared_flights"].max(),
        "D1_companions": g["txt"].apply(lambda s: "; ".join(s.head(10))),
    }).reset_index()
    res = res.merge(per, on="person_id", how="left")
    res = res[["person_id", "name_variants", "D1_flag", "D1_count", "D1_max_shared",
               "D1_companions"]].sort_values("D1_max_shared", ascending=False)
    res.to_csv(OUT / "D1_results.csv", index=False)
    print(f"D1 сработал у {len(res)} человек -> {OUT / 'D1_results.csv'}")


if __name__ == "__main__":
    main()
