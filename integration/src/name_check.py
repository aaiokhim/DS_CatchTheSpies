"""
Проверка склейки: нет ли внутри одного person_id записей с разными именами.

Имена сравниваются в нормализованном виде (транслитерация, без отчеств и инициалов).
Пишет integration/resolved/name_mismatches* и integration/reports/name_check_qa.md.

python3 integration/src/name_check.py
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import MERGED, PASSENGERS_ALL, RESOLVED, INT_SAMPLES, INT_REPORTS, read_flights_all

RES = RESOLVED
SAMPLES = INT_SAMPLES

CYR = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               ["A", "B", "V", "G", "D", "E", "E", "ZH", "Z", "I", "I", "K", "L", "M", "N", "O", "P",
                "R", "S", "T", "U", "F", "KH", "TS", "CH", "SH", "SHCH", "", "Y", "", "E", "IU", "IA"]))
PATRONYMIC = re.compile(r"(VICH|VNA|ICH|ICHNA)$")
SIMILAR = 0.75
SEVERITY = {"translit_only": 1, "one_word_differs": 2, "different_name": 3}


def log(m):
    print(m, flush=True)


def skeleton(name):
    if not isinstance(name, str) or not name.strip():
        return ()
    s = "".join(CYR.get(ch, ch) for ch in name.upper())
    s = re.sub(r"['’`.\-]", "", s)
    words = []
    for w in s.split():
        w = w.replace("X", "KS").replace("TC", "TS").replace("Y", "I")
        w = re.sub(r"(.)\1+", r"\1", w)
        if len(w) > 1:
            words.append(w)
    if len(words) >= 3:
        words = [w for w in words if not PATRONYMIC.search(w)] or words
    return tuple(sorted(set(words)))


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def compare(ref, var):
    if set(var) <= set(ref) or set(ref) <= set(var):
        return "subset", 1.0, ""
    exact = set(var) & set(ref)
    rest_v = [w for w in var if w not in exact]
    rest_r = [w for w in ref if w not in exact]
    best = [max((sim(w, r) for r in rest_r), default=0.0) for w in rest_v]
    score = min(best) if best else 1.0
    diff = " / ".join(rest_v) + "  vs  " + " / ".join(rest_r)
    if score >= SIMILAR:
        return "translit_only", round(score, 2), diff
    if exact:
        return "one_word_differs", round(score, 2), diff
    return "different_name", round(score, 2), diff


def main():
    log("[1/4] Чтение...")
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "sources", "n_records"])
    links = pd.read_parquet(RES / "record_links.parquet", columns=["source_record_id", "person_id"])
    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source_record_id", "source", "full_name_raw", "first_name_raw",
                                 "middle_name_raw", "last_name_raw"])
    parts = (P["first_name_raw"].fillna("") + " " + P["middle_name_raw"].fillna("") + " "
             + P["last_name_raw"].fillna("")).str.replace(r"\s+", " ", regex=True).str.strip()
    P["name"] = P["full_name_raw"].fillna(parts.mask(parts == ""))
    P = P.dropna(subset=["name"]).merge(links, on="source_record_id")

    log("[2/4] Скелеты имён...")
    uniq = pd.Series(P["name"].unique())
    sk = dict(zip(uniq, uniq.map(skeleton)))
    P["skel"] = P["name"].map(sk)
    P = P[P["skel"].map(len) > 0]

    V = (P.groupby(["person_id", "skel"])
          .agg(n=("source_record_id", "size"),
               sources=("source", lambda s: "; ".join(sorted(set(s)))),
               example=("name", "first"))
          .reset_index())
    n_var = V.groupby("person_id").size()
    multi = V[V["person_id"].isin(n_var[n_var > 1].index)]
    log(f"  людей с именем: {V['person_id'].nunique()}; с ≥2 разными скелетами: {multi['person_id'].nunique()}")

    log("[3/4] Сравнение вариантов...")
    rows = []
    for pid, g in multi.groupby("person_id", sort=False):
        g = g.sort_values(["n", "skel"], ascending=[False, True])
        ref = g.iloc[0]
        for v in g.iloc[1:].itertuples():
            cat, score, diff = compare(ref["skel"], v.skel)
            if cat == "subset":
                continue
            rows.append({
                "person_id": pid,
                "category": cat,
                "main_name": ref["example"],
                "main_name_sources": ref["sources"],
                "main_name_records": int(ref["n"]),
                "mismatched_name": v.example,
                "mismatched_sources": v.sources,
                "mismatched_records": int(v.n),
                "differing_words": diff,
                "similarity": score,
                "main_skeleton": " ".join(ref["skel"]),
                "mismatched_skeleton": " ".join(v.skel),
            })
    mm = pd.DataFrame(rows, columns=["person_id", "category", "main_name", "main_name_sources",
                                     "main_name_records", "mismatched_name", "mismatched_sources",
                                     "mismatched_records", "differing_words", "similarity",
                                     "main_skeleton", "mismatched_skeleton"])

    log("[4/4] Запись...")
    if len(mm):
        mm["severity"] = mm["category"].map(SEVERITY)
        pp = (mm.groupby("person_id")
                .agg(worst_category=("category", lambda s: max(s, key=SEVERITY.get)),
                     n_mismatched_variants=("category", "size"),
                     main_name=("main_name", "first"),
                     mismatched_names=("mismatched_name", lambda s: "; ".join(s)))
                .reset_index()
                .merge(per, on="person_id", how="left"))
        pp["severity"] = pp["worst_category"].map(SEVERITY)
        pp = pp.sort_values(["severity", "n_mismatched_variants"], ascending=False).drop(columns="severity")
        mm = mm.sort_values(["severity", "person_id"], ascending=[False, True]).drop(columns="severity")
    else:
        pp = pd.DataFrame(columns=["person_id", "worst_category"])

    mm.to_csv(RES / "name_mismatches.csv", index=False)
    mm.to_parquet(RES / "name_mismatches.parquet", index=False)
    pp.to_csv(RES / "name_check_persons.csv", index=False)
    for d in (SAMPLES, INT_REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    pd.concat([mm[mm.category == c].head(10) for c in ["different_name", "one_word_differs", "translit_only"]]
              ).to_csv(SAMPLES / "resolved_name_mismatches_sample.csv", index=False)

    n_named = V["person_id"].nunique()
    L = ["# Проверка имён внутри person_id (строгая склейка)", "",
         "Склейка не менялась. Ниже - люди, у которых среди записей есть имя, не совпадающее с основным.", "",
         "| Показатель | Значение |", "|---|---|",
         f"| Людей с именем | {n_named} |",
         f"| ...с одним вариантом имени (после нормализации) | {n_named - multi['person_id'].nunique()} |",
         f"| ...с несколькими вариантами, но все совместимы (часть другого) | "
         f"{multi['person_id'].nunique() - pp['person_id'].nunique()} |",
         f"| Людей с расхождением имён | {pp['person_id'].nunique()} |"]
    if len(pp):
        for c in ["different_name", "one_word_differs", "translit_only"]:
            L.append(f"| ...худшая категория `{c}` | {int((pp['worst_category'] == c).sum())} |")
        L += ["", "Категории:",
              "- `different_name` - ни одно слово не совпало (возможно, разные люди склеены через общий ключ);",
              "- `one_word_differs` - одно слово совпало, другое совсем другое (другое имя или другая фамилия);",
              "- `translit_only` - слова похожи, скорее другая транслитерация (обычно не проблема).", "",
              "## Между какими источниками расхождения (различные имена и одно слово)", "",
              "| Источники основного имени | Источники отличающегося | Вариантов |", "|---|---|---|"]
        serious = mm[mm.category != "translit_only"]
        top = serious.groupby(["main_name_sources", "mismatched_sources"]).size().sort_values(ascending=False).head(15)
        L += [f"| {a} | {b} | {n} |" for (a, b), n in top.items()]
        for c in ["different_name", "one_word_differs", "translit_only"]:
            ex = mm[mm.category == c].head(10)
            if len(ex):
                L += ["", f"## Примеры: {c}", "", "```",
                      ex[["person_id", "main_name", "main_name_sources", "mismatched_name",
                          "mismatched_sources", "similarity"]].to_string(index=False), "```"]
    L += ["", "## Как читать", "",
          "- `resolved/name_mismatches.csv` - каждый несовпавший вариант имени: какое основное имя, "
          "какое отличающееся, из каких источников, какие слова различаются.",
          "- `resolved/name_check_persons.csv` - один человек = одна строка, худшая категория.",
          "- Найти, через какой ключ склеились записи: `resolved/record_links` (person_id) + "
          "`merged/passengers_all` / `flights_all` (карта, документ, билет, PNR этих записей).",
          "- `different_name` и `one_word_differs` - кандидаты на проверку: либо ошибка склейки, "
          "либо один человек под разными именами (что может быть признаком для поиска шпионов)."]
    (INT_REPORTS / "name_check_qa.md").write_text("\n".join(L), encoding="utf-8")

    log(f"\nЛюдей с расхождением имён: {pp['person_id'].nunique()}  (вариантов: {len(mm)})")
    if len(pp):
        log(pp["worst_category"].value_counts().to_string())
    log("Готово: resolved/name_mismatches.csv, resolved/name_check_persons.csv, integration/reports/name_check_qa.md")


if __name__ == "__main__":
    main()
