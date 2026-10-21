"""
Кандидаты на склейку по именам для записей, которые не связались ни по одному ключу.

Ничего не склеивает, только предлагает пары (уровни B и C).
Пишет integration/resolved/name_link_candidates* и integration/reports/name_candidates_qa.md.

python3 integration/src/name_candidates.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import MERGED, PASSENGERS_ALL, RESOLVED, INT_SAMPLES, INT_REPORTS, read_flights_all

RES = RESOLVED
SAMPLES = INT_SAMPLES

ORPHAN_SOURCES = {"boarding_passes", "sirena", "boarding_data"}

CYR = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               ["A", "B", "V", "G", "D", "E", "E", "ZH", "Z", "I", "I", "K", "L", "M", "N", "O", "P",
                "R", "S", "T", "U", "F", "KH", "TS", "CH", "SH", "SHCH", "", "Y", "", "E", "IU", "IA"]))
PATRONYMIC = re.compile(r"(VICH|VNA|ICH|ICHNA)$")


def log(m):
    print(m, flush=True)


def skeleton_tokens(name):
    if not isinstance(name, str) or not name.strip():
        return ()
    s = "".join(CYR.get(ch, ch) for ch in name.upper())
    s = re.sub(r"['’`.\-]", "", s)
    out = []
    for w in s.split():
        w = w.replace("X", "KS").replace("TC", "TS").replace("Y", "I")
        if len(w) <= 1 or PATRONYMIC.search(w):
            continue
        out.append(w)
    return tuple(sorted(set(out)))


def name_any(P):
    parts = (P["first_name_raw"].fillna("") + " " + P["middle_name_raw"].fillna("") + " "
             + P["last_name_raw"].fillna("")).str.replace(r"\s+", " ", regex=True).str.strip()
    return P["full_name_raw"].fillna(parts.mask(parts == ""))


def sex_of(P):
    t = P["title"].astype("string").str.upper().map({"MR": "Male", "MRS": "Female"})
    return P["sex"].astype("string").fillna(t)


def main():
    log("[1/5] Чтение...")
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "sources", "n_sources", "sex", "documents"])
    links = pd.read_parquet(RES / "record_links.parquet")
    ev = pd.read_parquet(RES / "flight_events.parquet",
                         columns=["flight_event_id", "person_id", "flight_number", "flight_date"])
    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source_record_id", "source", "full_name_raw", "first_name_raw",
                                 "middle_name_raw", "last_name_raw", "title", "sex", "document"])
    F = read_flights_all(columns=["source_record_id", "flight_number", "flight_date"])

    P["name"] = name_any(P)
    P["sex_any"] = sex_of(P)
    P = P.merge(links[["source_record_id", "person_id"]], on="source_record_id", how="left")

    log("[2/5] Скелеты имён...")
    uniq = pd.Series(P["name"].dropna().unique())
    skel = dict(zip(uniq, uniq.map(skeleton_tokens)))
    P["tokens"] = P["name"].map(skel)

    orphan_persons = set(per.loc[(per["n_sources"] == 1) & per["sources"].isin(ORPHAN_SOURCES), "person_id"])
    P["is_orphan"] = P["person_id"].isin(orphan_persons)
    log(f"  одиночек (людей): {len(orphan_persons)}; основных людей: {len(per) - len(orphan_persons)}")

    main_p = P[~P["is_orphan"] & P["tokens"].notna()][["person_id", "tokens"]]
    tok_p = main_p.explode("tokens").dropna().drop_duplicates().rename(columns={"tokens": "token"})

    orph = P[P["is_orphan"]][["source_record_id", "source", "person_id", "name", "tokens", "sex_any", "document"]]
    orph = orph.merge(F, on="source_record_id", how="left")
    orph["n_tok"] = orph["tokens"].map(len)
    orph_ok = orph[orph["n_tok"] >= 2]
    log(f"  записей-одиночек: {len(orph)}; из них с именем из ≥2 слов: {len(orph_ok)}")

    log("[3/5] Правило B: имя + рейс + дата...")
    fd = orph_ok[["flight_number", "flight_date"]].drop_duplicates()
    ev_main = ev[~ev["person_id"].isin(orphan_persons)].merge(fd, on=["flight_number", "flight_date"])
    tok_e = ev_main.merge(tok_p, on="person_id")
    tok_o = (orph_ok[["source_record_id", "flight_number", "flight_date", "tokens", "n_tok"]]
             .explode("tokens").rename(columns={"tokens": "token"}))
    pairs = tok_o.merge(tok_e, on=["flight_number", "flight_date", "token"])
    shared = pairs.groupby(["source_record_id", "person_id", "flight_event_id"]).agg(
        shared=("token", "nunique"), n_tok=("n_tok", "first")).reset_index()
    B = shared[shared["shared"] == shared["n_tok"]].drop(columns=["shared", "n_tok"])
    B["match_rule"], B["confidence"] = "name+flight+date", "B"
    log(f"  кандидатов B: {len(B)}")

    log("[4/5] Правило C: уникальное имя...")
    left = orph_ok[~orph_ok["source_record_id"].isin(B["source_record_id"])]
    main_keys = main_p.assign(key=main_p["tokens"].map(lambda t: " ".join(t)))
    main_keys = main_keys[main_keys["tokens"].map(len) >= 2][["person_id", "key"]].drop_duplicates()
    key_n = main_keys.groupby("key")["person_id"].nunique()
    uniq_keys = main_keys[main_keys["key"].isin(key_n[key_n == 1].index)]
    left = left.assign(key=left["tokens"].map(lambda t: " ".join(t)))
    C = left[["source_record_id", "key"]].merge(uniq_keys, on="key").drop(columns="key")
    C["flight_event_id"] = pd.NA
    C["match_rule"], C["confidence"] = "name_only_unique", "C"
    n_ambig_name = int(left["key"].isin(key_n[key_n > 1].index).sum())
    log(f"  кандидатов C: {len(C)}; имя есть у нескольких людей (не предлагалось): {n_ambig_name}")

    log("[5/5] Флаги и запись...")
    cand = pd.concat([B, C], ignore_index=True).rename(columns={"person_id": "candidate_person_id"})
    info = orph.drop(columns=["tokens", "n_tok"]).rename(columns={
        "person_id": "orphan_person_id", "source": "orphan_source", "name": "orphan_name",
        "sex_any": "orphan_sex", "document": "orphan_document"})
    cand = cand.merge(info, on="source_record_id", how="left")

    names = (P[~P["is_orphan"]][["person_id", "name"]].dropna().drop_duplicates()
             .groupby("person_id").head(5).groupby("person_id")["name"].agg("; ".join))
    cand["candidate_names"] = cand["candidate_person_id"].map(names)
    cand["candidate_sex"] = cand["candidate_person_id"].map(per.set_index("person_id")["sex"])

    cand["candidate_documents"] = cand["candidate_person_id"].map(per.set_index("person_id")["documents"])
    cand["flag_document_differs"] = [
        bool(isinstance(d, str) and isinstance(ds, str) and d not in ds.split("; "))
        for d, ds in zip(cand["orphan_document"], cand["candidate_documents"])]

    cand["n_candidates"] = cand.groupby("source_record_id")["candidate_person_id"].transform("nunique")
    cand["flag_ambiguous"] = cand["n_candidates"] > 1
    cs = cand["candidate_sex"].astype(object).where(cand["candidate_sex"].notna(), None)
    os_ = cand["orphan_sex"].astype(object).where(cand["orphan_sex"].notna(), None)
    cand["flag_sex_mismatch"] = [
        bool(a and b and ";" not in b and a != b) for a, b in zip(os_, cs)]

    cols = ["source_record_id", "orphan_person_id", "orphan_source", "orphan_name", "orphan_sex",
            "orphan_document", "flight_number", "flight_date",
            "candidate_person_id", "candidate_names", "candidate_sex", "candidate_documents",
            "flight_event_id", "match_rule", "confidence", "n_candidates",
            "flag_ambiguous", "flag_sex_mismatch", "flag_document_differs"]
    cand = cand[cols].rename(columns={"source_record_id": "orphan_record_id",
                                      "flight_event_id": "candidate_flight_event_id"})
    cand = cand.sort_values(["confidence", "orphan_record_id"])

    cand.to_parquet(RES / "name_link_candidates.parquet", index=False)
    cand.to_csv(RES / "name_link_candidates.csv", index=False)
    for d in (SAMPLES, INT_REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    pd.concat([cand[cand.confidence == "B"].head(10), cand[cand.confidence == "C"].head(10),
               cand[cand.flag_ambiguous].head(5), cand[cand.flag_sex_mismatch].head(5),
               cand[cand.flag_document_differs].head(10)]
              ).to_csv(SAMPLES / "resolved_name_link_candidates_sample.csv", index=False)

    rec_cov = cand.groupby("confidence")["orphan_record_id"].nunique()
    clean = cand[~cand.flag_ambiguous & ~cand.flag_sex_mismatch & ~cand.flag_document_differs]
    L = ["# Кандидаты на склейку по именам (этап 2)", "",
         "Результат этапа 1 не изменён. Это только предложения, ничего не слито.", "",
         "| Показатель | Значение |", "|---|---|",
         f"| Людей-одиночек (из одного источника посадок) | {len(orphan_persons)} |",
         f"| Записей-одиночек | {len(orph)} |",
         f"| ...с именем из ≥2 слов (можно сравнивать) | {len(orph_ok)} |",
         f"| Пар-кандидатов всего | {len(cand)} |",
         f"| Записей с кандидатом уровня B (имя + рейс + дата) | {int(rec_cov.get('B', 0))} |",
         f"| Записей с кандидатом уровня C (уникальное имя) | {int(rec_cov.get('C', 0))} |",
         f"| Записей без кандидата | {len(orph) - cand['orphan_record_id'].nunique()} |",
         f"| ...из них имя есть у нескольких людей (C не предлагался) | {n_ambig_name} |",
         f"| Пар с flag_ambiguous (подходит >1 человека) | {int(cand.flag_ambiguous.sum())} |",
         f"| Пар с flag_sex_mismatch | {int(cand.flag_sex_mismatch.sum())} |",
         f"| Пар с flag_document_differs (имя совпало, документ другой) | {int(cand.flag_document_differs.sum())} |",
         f"| ...из них уровня B (тот же рейс в тот же день!) | {int((cand.flag_document_differs & (cand.confidence == 'B')).sum())} |",
         f"| «Чистых» пар (без флагов) | {len(clean)} |",
         "", "## По источникам одиночек", "",
         "| Источник | Записей-одиночек | с кандидатом B | с кандидатом C |", "|---|---|---|---|"]
    for src, g in orph.groupby("source"):
        cg = cand[cand.orphan_source == src]
        L.append(f"| {src} | {len(g)} | {cg[cg.confidence == 'B'].orphan_record_id.nunique()} "
                 f"| {cg[cg.confidence == 'C'].orphan_record_id.nunique()} |")
    L += ["", "## Как пользоваться", "",
          "- Строгая версия (этап 1): `persons` + `flight_events` как есть.",
          "- Расширенная версия: дополнительно считать, что `orphan_person_id` = `candidate_person_id` "
          "для пар без флагов (или только уровня B).",
          "- Если человек подозрителен в обеих версиях - сильный сигнал; только в одной - смотреть вручную.",
          "- Пары с флагами сами по себе могут быть интересны (одно имя у разных людей, разный пол).",
          "- B + flag_document_differs: человек с тем же именем летел тем же рейсом в тот же день, "
          "но по другому документу - либо тёзки на одном рейсе, либо один человек с двумя документами.", "",
          "## Примеры", "", "```",
          cand.head(10)[["orphan_name", "flight_number", "flight_date", "candidate_names",
                         "confidence", "flag_ambiguous", "flag_sex_mismatch"]].fillna("").to_string(index=False),
          "```"]
    (INT_REPORTS / "name_candidates_qa.md").write_text("\n".join(L), encoding="utf-8")
    log(f"\nГотово: resolved/name_link_candidates (пар {len(cand)}), отчёт integration/reports/name_candidates_qa.md")


if __name__ == "__main__":
    main()
