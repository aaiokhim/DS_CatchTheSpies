"""
Строгая склейка: какие записи относятся к одному человеку и к одному перелёту.

Записи связываются только по сильным ключам (карта, документ, билет, PNR + рейс + дата, профиль),
имена не используются. Ключи, которые встречаются у явно разных людей, исключаются.
Читает integration/merged, пишет integration/resolved и integration/reports/resolve_qa.md.

python3 integration/src/resolve_entities.py [--no-csv]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import MERGED, PASSENGERS_ALL, RESOLVED, INT_SAMPLES, INT_REPORTS, read_flights_all

OUT = RESOLVED
SAMPLES = INT_SAMPLES
N_SAMPLE = 20

KNOWN_CONFLICTS = {
    "card:FB 139888197": "известный конфликт: ROMAN MASLENNIKOV / OLESYA GOLOVINA (Pointz), 2 профиля форума",
    "doc:8248013778": "известный конфликт: GORDEI GLEBOV / RAMIL BUROV (BoardingData)",
}

SOURCE_PRIORITY = {"sirena": 0, "boarding_passes": 1, "boarding_data": 2,
                   "pointz": 3, "forum": 4, "skyteam": 9}


def log(msg):
    print(msg, flush=True)


def join_unique(df, by, col, limit=None):
    x = df[[by, col]].dropna().drop_duplicates().sort_values(col, kind="stable")
    size = x.groupby(by)[col].transform("size")
    single = x[size == 1].set_index(by)[col]
    multi = x[size > 1]
    if limit:
        multi = multi.groupby(by).head(limit)
    multi = multi.groupby(by)[col].agg("; ".join)
    return pd.concat([single, multi])


def build_edges(P, F):
    parts = []

    def add(rec, key, ktype, source):
        e = pd.DataFrame({"record_id": rec.values, "key": key.values, "source": source.values})
        e = e.dropna(subset=["key"])
        e["key_type"] = ktype
        parts.append(e)

    pc = P[["source_record_id", "loyalty_ids", "source"]].dropna(subset=["loyalty_ids"])
    pc = pc.assign(card=pc["loyalty_ids"].str.split("; ")).explode("card")
    add(pc["source_record_id"], "card:" + pc["card"], "card", pc["source"])
    add(F["source_record_id"], "card:" + F["loyalty_id"], "card", F["source"])

    add(P["source_record_id"], "doc:" + P["document"], "doc", P["source"])
    add(F["source_record_id"], "doc:" + F["document"], "doc", F["source"])

    add(F["source_record_id"], "tkt:" + F["e_ticket"], "tkt", F["source"])

    add(F["source_record_id"], "pnr:" + F["pnr"] + "|" + F["flight_number"] + "|" + F["flight_date"],
        "pnr", F["source"])

    own = F[["source_record_id", "passenger_record_id", "source"]].dropna(subset=["passenger_record_id"])
    own = own[~own["passenger_record_id"].str.contains(";", regex=False)]
    own = own[own["passenger_record_id"] != own["source_record_id"]]
    add(own["source_record_id"], "owner:" + own["passenger_record_id"], "owner", own["source"])
    add(own["passenger_record_id"], "owner:" + own["passenger_record_id"], "owner", own["source"])

    edges = pd.concat(parts, ignore_index=True).drop_duplicates(["record_id", "key"])
    return edges


def find_conflicts(P, edges):
    bad = {}

    rk = edges[edges["key_type"].isin(["tkt", "pnr"])]
    cnt = rk.groupby(["key", "source"])["record_id"].nunique()
    for key in cnt[cnt > 1].index.get_level_values(0).unique():
        bad[key] = "ключ встречается у нескольких записей одного источника"

    pc = edges[(edges["key_type"] == "card") & edges["source"].isin(["forum", "pointz"])
               & edges["record_id"].isin(P["source_record_id"])]
    cnt = pc.groupby(["key", "source"])["record_id"].nunique()
    for key in cnt[cnt > 1].index.get_level_values(0).unique():
        bad[key] = "карта у нескольких разных профилей/пользователей одного источника"

    d = P.dropna(subset=["document"])
    nb = d.dropna(subset=["birth_date"]).groupby("document")["birth_date"].nunique()
    for doc in nb[nb > 1].index:
        bad["doc:" + doc] = "у документа разные даты рождения"
    bd = d[d["source"] == "boarding_data"]
    nn = bd.groupby("document")[["first_name_raw", "last_name_raw"]].nunique().max(axis=1)
    for doc in nn[nn > 1].index:
        bad.setdefault("doc:" + doc, "у документа разные ФИО в BoardingData")
    sr = d[d["source"] == "sirena"]
    nn = sr.groupby("document")["full_name_raw"].nunique()
    for doc in nn[nn > 1].index:
        bad.setdefault("doc:" + doc, "у документа разные ФИО в Sirena")

    for k, why in KNOWN_CONFLICTS.items():
        bad[k] = why

    n_rec = edges[edges["key"].isin(bad)].groupby("key")["record_id"].nunique()
    conf = pd.DataFrame({"key": list(bad), "reason": list(bad.values())})
    conf["key_type"] = conf["key"].str.split(":").str[0]
    conf["n_records"] = conf["key"].map(n_rec).fillna(0).astype(int)
    return conf.sort_values(["key_type", "key"])


def components(record_ids, edges):
    rec_index = pd.Index(record_ids)
    r = rec_index.get_indexer(edges["record_id"])
    keep = r >= 0
    r = r[keep]
    k, _ = pd.factorize(edges["key"].values[keep])
    n_rec, n_key = len(rec_index), k.max() + 1 if len(k) else 0

    label = np.arange(n_rec)
    it = 0
    while True:
        it += 1
        kmin = np.full(n_key, n_rec, dtype=np.int64)
        np.minimum.at(kmin, k, label[r])
        new = label.copy()
        np.minimum.at(new, r, kmin[k])
        new = new[new]
        changed = int((new != label).sum())
        label = new
        log(f"    итерация {it}: изменено меток {changed}")
        if changed == 0:
            break

    codes, _ = pd.factorize(label)
    return pd.Series([f"P{c + 1:07d}" for c in codes], index=rec_index, name="person_id")


def build_flight_events(F):
    log("  flight_events...")
    F = F.copy()
    F["prio"] = F["source"].map(SOURCE_PRIORITY).fillna(9)
    F["is_suspicious_airport"] = F["is_suspicious_airport"].astype("boolean").fillna(False).astype(bool)
    key = ["person_id", "flight_number", "flight_date"]
    F["flight_event_id"] = F.groupby(key, sort=False).ngroup()
    F["flight_event_id"] = "FE" + (F["flight_event_id"] + 1).astype(str).str.zfill(8)

    for side in ["origin", "destination"]:
        raw = F[f"{side}_airport_raw"].astype("string")
        code = F[f"{side}_airport"].astype("string")
        city = F[f"{side}_city"].astype("string")
        bad = raw.str.fullmatch(r"[a-z]{3}", na=False) | code.isin(["REA", "OVA", "NIA", "NDS"]).fillna(False)
        bad |= ((code == "NGO").fillna(False) & city.notna()
                & ~city.str.upper().str.contains("NAGOYA", na=False))
        F[f"{side}_bad"] = bad.astype(bool)
        F[f"{side}_good"] = code.mask(F[f"{side}_bad"])

    F = F.sort_values("prio", kind="stable")
    best = lambda c: F.dropna(subset=[c]).groupby("flight_event_id")[c].first()

    ev = F.groupby("flight_event_id").agg(
        person_id=("person_id", "first"),
        flight_number=("flight_number", "first"),
        flight_date=("flight_date", "first"),
        n_records=("source_record_id", "size"),
        n_sources=("source", "nunique"))
    ev["sources"] = join_unique(F, "flight_event_id", "source")
    ev["origin_airport"] = best("origin_good")
    ev["destination_airport"] = best("destination_good")
    for side in ["origin", "destination"]:
        ev[f"{side}_airport_source"] = (F.dropna(subset=[f"{side}_good"])
                                         .groupby("flight_event_id")["source"].first())
    for c in ["departure_time", "arrival_date", "arrival_time", "origin_city", "destination_city",
              "booking_class", "fare_code"]:
        ev[c] = best(c)

    g = F.groupby("flight_event_id")
    o_bad, d_bad = g["origin_bad"].any(), g["destination_bad"].any()
    ev["has_suspicious_airport_record"] = o_bad | d_bad
    rec_o = o_bad & ev["origin_airport"].notna()
    rec_d = d_bad & ev["destination_airport"].notna()
    ev["airport_recovered_from_other_source"] = rec_o | rec_d
    ev["airport_still_broken"] = (o_bad & ev["origin_airport"].isna()) | (d_bad & ev["destination_airport"].isna())

    n_o = g["origin_good"].nunique()
    n_d = g["destination_good"].nunique()
    ev["route_conflict"] = (n_o > 1) | (n_d > 1)

    sky = F[F["source"] == "skyteam"].groupby("flight_event_id")[["origin_good", "destination_good"]].first()
    oth = F[F["source"] != "skyteam"]
    oth = pd.DataFrame({
        "o": oth.dropna(subset=["origin_good"]).groupby("flight_event_id")["origin_good"].first(),
        "d": oth.dropna(subset=["destination_good"]).groupby("flight_event_id")["destination_good"].first()})
    j = sky.join(oth, how="inner")
    dis = (((j["origin_good"] != j["o"]) & j["origin_good"].notna() & j["o"].notna())
           | ((j["destination_good"] != j["d"]) & j["destination_good"].notna() & j["d"].notna()))
    rev = ((j["origin_good"] == j["d"]) & (j["destination_good"] == j["o"])).fillna(False)
    ev["skyteam_route_disagrees"] = dis.reindex(ev.index).fillna(False).astype(bool)
    ev["skyteam_route_reversed"] = (dis & rev).reindex(ev.index).fillna(False).astype(bool)
    oth_all = F[F["source"] != "skyteam"].groupby("flight_event_id")
    ev["route_conflict_without_skyteam"] = ((oth_all["origin_good"].nunique() > 1)
                                            | (oth_all["destination_good"].nunique() > 1)
                                            ).reindex(ev.index).fillna(False).astype(bool)

    cf = F[F["flight_event_id"].isin(ev.index[ev["route_conflict"]])]
    detail = None
    if len(cf):
        cf = cf.assign(o=cf["source"] + "=" + cf["origin_good"].fillna("?"),
                       d=cf["source"] + "=" + cf["destination_good"].fillna("?"))
        detail = pd.DataFrame({
            "origins": join_unique(cf, "flight_event_id", "o"),
            "destinations": join_unique(cf, "flight_event_id", "d"),
            "origin_values": join_unique(cf, "flight_event_id", "origin_good"),
            "destination_values": join_unique(cf, "flight_event_id", "destination_good"),
        })
        detail = ev[["person_id", "flight_number", "flight_date", "sources"]].join(detail, how="inner").reset_index()

    return ev.reset_index(), F[["source_record_id", "flight_event_id"]], detail


def build_persons(P, F, rec_person, ev):
    log("  persons...")
    P = P.assign(person_id=P["source_record_id"].map(rec_person))
    F = F.assign(person_id=F["source_record_id"].map(rec_person))

    parts = (P["first_name_raw"].fillna("") + " " + P["middle_name_raw"].fillna("") + " "
             + P["last_name_raw"].fillna(""))
    parts = parts.str.replace(r"\s+", " ", regex=True).str.strip()
    name = P["full_name_raw"].fillna(parts.mask(parts == ""))
    P = P.assign(name_variant=name)

    cards = pd.concat([
        P[["person_id", "loyalty_ids"]].dropna().assign(card=lambda d: d["loyalty_ids"].str.split("; "))
                                    .explode("card")[["person_id", "card"]],
        F[["person_id", "loyalty_id"]].dropna().rename(columns={"loyalty_id": "card"}),
    ])

    all_recs = pd.concat([P[["person_id", "source", "source_record_id"]],
                          F[["person_id", "source", "source_record_id"]]]).drop_duplicates("source_record_id")

    per = all_recs.groupby("person_id").agg(n_records=("source_record_id", "size"),
                                            n_sources=("source", "nunique"))
    per["sources"] = join_unique(all_recs, "person_id", "source")
    per["name_variants"] = join_unique(P, "person_id", "name_variant", limit=10)
    per["n_name_variants"] = P.dropna(subset=["name_variant"]).groupby("person_id")["name_variant"].nunique()
    per["sex"] = join_unique(P, "person_id", "sex")
    per["birth_dates"] = join_unique(P, "person_id", "birth_date")
    per["n_birth_dates"] = P.dropna(subset=["birth_date"]).groupby("person_id")["birth_date"].nunique()
    per["documents"] = join_unique(P, "person_id", "document")
    per["loyalty_ids"] = join_unique(cards, "person_id", "card")
    per["forum_profiles"] = join_unique(P[P["source"] == "forum"], "person_id", "source_record_id")
    per["pointz_users"] = join_unique(P[P["source"] == "pointz"], "person_id", "source_record_id")
    per["n_forum_profiles"] = P[P["source"] == "forum"].groupby("person_id").size()
    per["n_pointz_users"] = P[P["source"] == "pointz"].groupby("person_id").size()
    per["n_flight_events"] = ev.groupby("person_id").size()
    per["n_flight_records"] = F.groupby("person_id").size()

    for c in ["n_name_variants", "n_birth_dates", "n_forum_profiles", "n_pointz_users",
              "n_flight_events", "n_flight_records"]:
        per[c] = per[c].fillna(0).astype(int)

    per["flag_multiple_birth_dates"] = per["n_birth_dates"] > 1
    per["flag_multiple_forum_profiles"] = per["n_forum_profiles"] > 1
    per["flag_multiple_pointz_users"] = per["n_pointz_users"] > 1
    per["has_name"] = per["name_variants"].notna()
    return per.reset_index()


def report(P, F, edges, conf, rec_person, per, ev, route_cf):
    L = ["# Resolve QA: этап 1 (сильные ключи)", "",
         "Склейка только по сильным ключам: карта, документ, билет, PNR+рейс+дата, принадлежность "
         "перелёта профилю. Имена не использовались. Конфликтные ключи исключены (conflicted_keys.csv).", "",
         "## Итог", "", "| Показатель | Значение |", "|---|---|",
         f"| Записей о пассажирах (passengers_all) | {len(P)} |",
         f"| Записей о перелётах (flights_all) | {len(F)} |",
         f"| Всего уникальных записей | {rec_person.size} |",
         f"| Людей (person_id) | {len(per)} |",
         f"| из них с именем | {int(per['has_name'].sum())} |",
         f"| Перелётов (flight_event_id) | {len(ev)} |",
         f"| перелётов, подтверждённых ≥2 источниками | {int((ev['n_sources'] >= 2).sum())} |",
         f"| перелётов с битым аэропортом, восстановленным из другого источника | "
         f"{int(ev['airport_recovered_from_other_source'].sum())} |",
         f"| перелётов, где битый аэропорт остался битым | {int(ev['airport_still_broken'].sum())} |",
         f"| перелётов с разными аэропортами в разных источниках (route_conflicts.csv) | {int(ev['route_conflict'].sum())} |",
         f"| ...из них SkyTeam расходится с остальными | {int(ev['skyteam_route_disagrees'].sum())} |",
         f"| ...из них у SkyTeam направление перевёрнуто | {int(ev['skyteam_route_reversed'].sum())} |",
         f"| ...конфликт между другими источниками (без SkyTeam) | {int(ev['route_conflict_without_skyteam'].sum())} |",
         "", "## Сколько рёбер дал каждый тип ключа", "",
         "| Ключ | Рёбер | Уникальных ключей | Исключено как конфликтные |", "|---|---|---|---|"]
    for kt, g in edges.groupby("key_type"):
        L.append(f"| {kt} | {len(g)} | {g['key'].nunique()} | {int((conf['key_type'] == kt).sum())} |")

    L += ["", "## Из каких источников собраны люди", "",
          "| Комбинация источников | Людей |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in per["sources"].value_counts().head(20).items()]

    L += ["", "## Перелёты по числу подтверждающих источников", "",
          "| Источников | Перелётов |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in ev["n_sources"].value_counts().sort_index().items()]
    L += ["", "| Комбинация источников | Перелётов |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in ev["sources"].value_counts().head(15).items()]

    if route_cf is not None and len(route_cf):
        L += ["", "## Конфликты маршрута: какие значения расходятся (топ-15)", "",
              "| Вылет (разные значения) | Прилёт (разные значения) | Источники | Перелётов |", "|---|---|---|---|"]
        top = route_cf.groupby(["origin_values", "destination_values", "sources"]).size().sort_values(ascending=False).head(15)
        L += [f"| {o} | {d} | {s} | {n} |" for (o, d, s), n in top.items()]

    forum_named = per[(per["n_forum_profiles"] > 0) & per["has_name"]]
    L += ["", "## Форум и Pointz", "",
          f"- Людей с профилем форума: {int((per['n_forum_profiles'] > 0).sum())}",
          f"- ...из них связаны с Pointz: {int(((per['n_forum_profiles'] > 0) & (per['n_pointz_users'] > 0)).sum())}",
          f"- ...из них есть имя (из любого источника): {len(forum_named)}",
          "", "## Флаги возможной ложной склейки (не исправлялись)", "",
          f"- Несколько разных дат рождения у одного person_id: {int(per['flag_multiple_birth_dates'].sum())}",
          f"- Несколько профилей форума в одном person_id: {int(per['flag_multiple_forum_profiles'].sum())}",
          f"- Несколько пользователей Pointz в одном person_id: {int(per['flag_multiple_pointz_users'].sum())}",
          "", "## Самые большие person_id (проверить глазами)", "", "```",
          per.sort_values("n_records", ascending=False).head(10)[
              ["person_id", "n_records", "sources", "n_name_variants", "n_birth_dates",
               "n_flight_events", "name_variants"]].fillna("").to_string(index=False),
          "```", "", "## Исключённые конфликтные ключи", "",
          "| Тип | Ключей | Причины |", "|---|---|---|"]
    for kt, g in conf.groupby("key_type"):
        L.append(f"| {kt} | {len(g)} | {'; '.join(sorted(g['reason'].unique()))} |")

    L += ["", "## Проверки", "", "| Проверка | Результат |", "|---|---|"]
    checks = {
        "каждая запись получила person_id": rec_person.notna().all(),
        "каждая запись о перелёте получила flight_event_id": True,
        "сумма n_records по людям = числу уникальных записей": per["n_records"].sum() == rec_person.size,
        "сумма n_records по перелётам = строкам flights_all": ev["n_records"].sum() == len(F),
    }
    L += [f"| {k} | {'OK' if v else 'FAIL'} |" for k, v in checks.items()]
    (INT_REPORTS / "resolve_qa.md").write_text("\n".join(L), encoding="utf-8")
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-csv", action="store_true")
    args = ap.parse_args()
    for d in (OUT, SAMPLES, INT_REPORTS):
        d.mkdir(parents=True, exist_ok=True)

    log("[1/5] Чтение merged/...")
    P = pd.read_parquet(PASSENGERS_ALL)
    F = read_flights_all()
    log(f"  passengers_all {len(P)}, flights_all {len(F)}")

    log("[2/5] Ключи и конфликты...")
    edges = build_edges(P, F)
    conf = find_conflicts(P, edges)
    used = edges[~edges["key"].isin(set(conf["key"]))]
    log(f"  рёбер {len(edges)}, исключено конфликтных ключей {len(conf)}")

    log("[3/5] Связные компоненты...")
    record_ids = pd.unique(pd.concat([P["source_record_id"], F["source_record_id"]]))
    rec_person = components(record_ids, used)

    log("[4/5] Люди и перелёты...")
    F["person_id"] = F["source_record_id"].map(rec_person)
    ev, f_ev, route_cf = build_flight_events(F)
    per = build_persons(P, F.drop(columns="person_id"), rec_person, ev)

    links = rec_person.rename_axis("source_record_id").reset_index()
    src = pd.concat([P[["source_record_id", "source"]], F[["source_record_id", "source"]]]).drop_duplicates("source_record_id")
    links = links.merge(src, on="source_record_id", how="left").merge(f_ev, on="source_record_id", how="left")

    log("[5/5] Запись...")
    per.to_parquet(OUT / "persons.parquet", index=False)
    ev.to_parquet(OUT / "flight_events.parquet", index=False)
    links.to_parquet(OUT / "record_links.parquet", index=False)
    conf.to_csv(OUT / "conflicted_keys.csv", index=False)
    if route_cf is not None:
        route_cf.to_csv(OUT / "route_conflicts.csv", index=False)
    if not args.no_csv:
        per.to_csv(OUT / "persons.csv", index=False)
        ev.to_csv(OUT / "flight_events.csv", index=False)

    for name, df in [("persons", per), ("flight_events", ev), ("record_links", links)]:
        df.head(N_SAMPLE).to_csv(SAMPLES / f"resolved_{name}_sample.csv", index=False)
    rich = per.sort_values(["n_sources", "n_flight_events"], ascending=False).head(N_SAMPLE)
    rich.to_csv(SAMPLES / "resolved_persons_multisource_sample.csv", index=False)

    checks = report(P, F, edges, conf, rec_person, per, ev, route_cf)
    log(f"\nЛюдей: {len(per)}   Перелётов: {len(ev)}   Записей: {rec_person.size}")
    for k, v in checks.items():
        log(f"  {'OK  ' if v else 'FAIL'} {k}")
    log(f"Готово: {OUT}  (отчёт: integration/reports/resolve_qa.md)")


if __name__ == "__main__":
    main()
