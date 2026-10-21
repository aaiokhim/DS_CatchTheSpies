"""
Обработка данных участника 2: профили форума (JSON) и BoardingData (CSV).

Этапы: parse (разбор и очистка), export (CSV-копии и общий файл перелётов),
anomalies (локальные проверки), identity (таблицы ключей для интеграции).
Читает data/raw/, пишет в participants/p2_forum_boarding/.

python3 participants/p2_forum_boarding/src/pipeline.py [--skip-parse] [--only parse|export|anomalies|identity]
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import ROOT, RAW, P2_PROCESSED, P2_CSV, P2_ANOMALIES, P2_HANDOFF, P2_SAMPLES, P2_REPORTS

DATA = RAW
JSON_PATH = RAW / "FrequentFlyerForum-Profiles.json"
CSV_PATH = RAW / "BoardingData.csv"
PROCESSED = P2_PROCESSED
CSV_DIR = P2_CSV
ANOMALIES = P2_ANOMALIES
INTEGRATION = P2_HANDOFF
SAMPLES = P2_SAMPLES
BASE = ROOT

N_SAMPLE = 20
TABLES = ["forum_profiles", "forum_documents", "forum_loyalty",
          "forum_flights", "boarding_clean", "link_candidates"]

MISSING = {"", "not presented", "n/a", "na", "null", "none_value"}

PERSON_KEY = ["first_name_norm", "last_name_norm", "birth_date"]


def clean_str(x):
    if x is None:
        return None
    s = str(x).strip()
    return None if s.lower() in MISSING else s


def norm_name(x):
    s = clean_str(x)
    if s is None:
        return None
    s = s.upper().replace("’", "'").replace("`", "'").replace("–", "-")
    s = re.sub(r"\s*-\s*", "-", s)
    return re.sub(r"\s+", " ", s)


def norm_flight(x):
    s = clean_str(x)
    return None if s is None else re.sub(r"\s+", "", s).upper()


def norm_doc(x):
    s = clean_str(x)
    return None if s is None else re.sub(r"\s+", "", s).upper()


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def as_str(s):
    return s.astype("string")


def sample(df, name):
    df.head(N_SAMPLE).to_csv(SAMPLES / f"{name}_sample.csv", index=False)


def load(name):
    return pd.read_parquet(PROCESSED / f"{name}.parquet")


def null_table(df, cols):
    rows = [f"| {c} | {int(df[c].isna().sum())} | {df[c].isna().mean():.1%} |" for c in cols]
    return "| Поле | null | доля |\n|---|---|---|\n" + "\n".join(rows)


def iqr_outliers(series, k=3.0):
    q1, q3 = series.quantile([0.25, 0.75])
    thr = q3 + k * (q3 - q1)
    return series[series > thr], thr


def parse_forum(path):
    import ijson

    profiles, documents, loyalty, flights = [], [], [], []
    with open(path, "rb") as f:
        for pid, p in enumerate(ijson.items(f, "Forum Profiles.item")):
            name = p.get("Real Name") or {}
            profiles.append({
                "profile_id": pid,
                "nickname": clean_str(p.get("NickName")),
                "sex": clean_str(p.get("Sex")),
                "first_name_raw": name.get("First Name"),
                "last_name_raw": name.get("Last Name"),
                "first_name_norm": norm_name(name.get("First Name")),
                "last_name_norm": norm_name(name.get("Last Name")),
                "n_flights_raw": len(as_list(p.get("Registered Flights"))),
                "source": "forum",
                "source_record_id": f"forum:{pid}",
            })

            for doc in as_list(p.get("Travel Documents")):
                if not isinstance(doc, dict):
                    continue
                for doc_type, value in doc.items():
                    for v in as_list(value):
                        if clean_str(v) is None:
                            continue
                        documents.append({"profile_id": pid, "doc_type": doc_type,
                                          "document_raw": str(v), "document_norm": norm_doc(v)})

            for card in as_list(p.get("Loyality Programm")):
                program = clean_str(card.get("programm"))
                number = clean_str(card.get("Number"))
                loyalty.append({
                    "profile_id": pid,
                    "program": program,
                    "status": clean_str(card.get("Status")),
                    "card_number_raw": card.get("Number"),
                    "card_number": number,
                    "card_key": f"{program}{number}" if program and number else None,
                })

            for i, fl in enumerate(as_list(p.get("Registered Flights"))):
                dep = fl.get("Departure") or {}
                arr = fl.get("Arrival") or {}
                flights.append({
                    "profile_id": pid,
                    "flight_seq": i,
                    "date": fl.get("Date"),
                    "flight_number": norm_flight(fl.get("Flight")),
                    "codeshare": fl.get("Codeshare"),
                    "origin": clean_str(dep.get("Airport")),
                    "origin_city": clean_str(dep.get("City")),
                    "origin_country_raw": dep.get("Country"),
                    "destination": clean_str(arr.get("Airport")),
                    "destination_city": clean_str(arr.get("City")),
                    "destination_country_raw": arr.get("Country"),
                    "source": "forum",
                    "source_record_id": f"forum:{pid}:{i}",
                })

            if pid % 5000 == 0:
                print(f"    ...профилей обработано: {pid}", flush=True)

    profiles = pd.DataFrame(profiles)
    documents = pd.DataFrame(documents, columns=["profile_id", "doc_type", "document_raw", "document_norm"])
    loyalty = pd.DataFrame(loyalty)
    flights = pd.DataFrame(flights)

    flights["date"] = pd.to_datetime(flights["date"], errors="coerce").dt.date
    for c in ["origin", "destination"]:
        flights[c] = flights[c].str.upper()
    flights["codeshare"] = flights["codeshare"].astype("boolean")
    return profiles, documents, loyalty, flights


def parse_boarding(path):
    raw = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    df = pd.DataFrame({"source_record_id": "boarding:" + raw.index.astype(str)})

    df["first_name_raw"] = raw["PassengerFirstName"]
    df["second_name_raw"] = raw["PassengerSecondName"]
    df["last_name_raw"] = raw["PassengerLastName"]
    df["first_name_norm"] = raw["PassengerFirstName"].map(norm_name)
    df["last_name_norm"] = raw["PassengerLastName"].map(norm_name)
    df["second_name_norm"] = raw["PassengerSecondName"].map(norm_name)
    df["second_name_is_initial"] = df["second_name_norm"].str.fullmatch(r"[A-Z]\.?", na=False)

    df["sex"] = raw["PassengerSex"].map(clean_str)
    df["birth_date"] = pd.to_datetime(raw["PassengerBirthDate"], format="%m/%d/%Y", errors="coerce").dt.date
    df["document_raw"] = raw["PassengerDocument"]
    df["document_norm"] = raw["PassengerDocument"].map(norm_doc)
    df["pnr"] = raw["BookingCode"].map(clean_str)
    df["ticket_number"] = raw["TicketNumber"].map(clean_str)
    df["baggage"] = raw["Baggage"].str.strip()
    df["flight_date"] = pd.to_datetime(raw["FlightDate"], format="%Y-%m-%d", errors="coerce").dt.date
    df["flight_time"] = pd.to_datetime(raw["FlightTime"], format="%H:%M", errors="coerce").dt.time
    df["flight_number"] = raw["FlightNumber"].map(norm_flight)
    df["codeshare_raw"] = raw["CodeShare"]
    df["codeshare"] = raw["CodeShare"].str.strip().map({"Own": False, "Operated": True}).astype("boolean")
    df["destination_city"] = raw["Destination"].map(clean_str)
    df["source"] = "boarding_csv"
    return raw, df


def build_links(profiles, documents, flights, boarding):
    links = []

    if len(documents):
        m = documents.dropna(subset=["document_norm"]).merge(
            boarding[["source_record_id", "document_norm"]], on="document_norm")
        links += [(f"forum:{r.profile_id}", r.source_record_id, "document", "A") for r in m.itertuples()]

    named = profiles.dropna(subset=["first_name_norm", "last_name_norm"])[
        ["profile_id", "first_name_norm", "last_name_norm"]]
    pf = flights[["profile_id", "flight_number", "date"]].merge(named, on="profile_id")

    m = pf.merge(
        boarding[["source_record_id", "first_name_norm", "last_name_norm", "flight_number", "flight_date"]],
        left_on=["first_name_norm", "last_name_norm", "flight_number", "date"],
        right_on=["first_name_norm", "last_name_norm", "flight_number", "flight_date"])
    links += [(f"forum:{r.profile_id}", r.source_record_id, "name+flight+date", "B") for r in m.itertuples()]

    name_only = named.merge(boarding[["first_name_norm", "last_name_norm"]].drop_duplicates(),
                            on=["first_name_norm", "last_name_norm"])

    links = pd.DataFrame(links, columns=["record_a", "record_b", "match_rule", "confidence"]).drop_duplicates()
    return links, len(name_only)


def quality_report(profiles, documents, loyalty, flights, raw_b, boarding, links, n_name_only):
    L = ["# Quality report: forum JSON + BoardingData.csv", "", "## Forum JSON", "",
         f"- Профилей: {len(profiles)}",
         f"- Профилей с реальным именем: {profiles['last_name_norm'].notna().sum()}",
         f"- Паспортов (не null): {len(documents)}",
         f"- Карт лояльности: {len(loyalty)}",
         f"- Зарегистрированных рейсов: {len(flights)} "
         f"(проверка: сумма n_flights_raw = {profiles['n_flights_raw'].sum()})",
         f"- Уникальных никнеймов: {profiles['nickname'].nunique()} из {len(profiles)}", ""]
    L += [null_table(profiles, ["nickname", "sex", "first_name_norm", "last_name_norm"]), ""]
    L += [null_table(flights, ["date", "flight_number", "origin", "destination"]), ""]

    dup_cards = loyalty.dropna(subset=["card_key"]).groupby("card_key")["profile_id"].nunique()
    L += [f"- Карт, принадлежащих нескольким профилям: {(dup_cards > 1).sum()} (не удалялись)",
          f"- Повторяющихся рейсов внутри одного профиля (profile+flight+date): "
          f"{flights.duplicated(['profile_id', 'flight_number', 'date']).sum()}", ""]

    L += ["## BoardingData.csv", "", f"- Строк до/после: {len(raw_b)} / {len(boarding)}", ""]
    for col in ["BookingCode", "TicketNumber"]:
        n = (raw_b[col].str.strip() == "Not presented").sum()
        L.append(f"- '{col}' = 'Not presented' -> null: {n} ({n / len(raw_b):.1%})")
    L += [f"- Отчество только инициалом: {boarding['second_name_is_initial'].sum()}",
          f"- Нераспарсенных дат рождения: {boarding['birth_date'].isna().sum()}",
          f"- Нераспарсенных дат рейса: {boarding['flight_date'].isna().sum()}",
          f"- Полных дубликатов строк: {raw_b.duplicated().sum()}",
          f"- Дубликатов по смысловому ключу (документ+рейс+дата): "
          f"{boarding.duplicated(['document_norm', 'flight_number', 'flight_date']).sum()}",
          f"- Уникальных документов: {boarding['document_norm'].nunique()}", ""]
    L += [null_table(boarding, ["document_norm", "pnr", "ticket_number", "birth_date", "flight_number"]), ""]

    L += ["## Link candidates", ""]
    if len(links):
        L += ["| Правило | Уровень | Пар | Профилей форума |", "|---|---|---|---|"]
        for (rule, conf), g in links.groupby(["match_rule", "confidence"]):
            L.append(f"| {rule} | {conf} | {len(g)} | {g['record_a'].nunique()} |")
    L += ["", f"- Слабые кандидаты (только имя+фамилия, уровень D, не сохраняются): {n_name_only}", ""]
    return "\n".join(L)


def step_parse():
    print("[1/4] PARSE: data/ -> processed/*.parquet")
    print("  Forum JSON...")
    profiles, documents, loyalty, flights = parse_forum(JSON_PATH)
    print("  BoardingData.csv...")
    raw_b, boarding = parse_boarding(CSV_PATH)
    print("  Link candidates...")
    links, n_name_only = build_links(profiles, documents, flights, boarding)

    for name, df in zip(TABLES, [profiles, documents, loyalty, flights, boarding, links]):
        df.to_parquet(PROCESSED / f"{name}.parquet", index=False)
        print(f"  {name:20s} {len(df):>9} строк")

    text = quality_report(profiles, documents, loyalty, flights, raw_b, boarding, links, n_name_only)
    (P2_REPORTS / "quality_report.md").write_text(text, encoding="utf-8")
    print("  -> processed/quality_report.md")


def step_export():
    print("[2/4] EXPORT: processed/csv/, all_travel_events, samples/")
    t = {}
    for name in TABLES:
        df = load(name)
        t[name] = df
        df.to_csv(CSV_DIR / f"{name}.csv", index=False)
        sample(df, name)
        print(f"  {name:20s} {len(df):>9} строк -> csv/{name}.csv")

    prof, loy, fl, b, links = (t["forum_profiles"], t["forum_loyalty"], t["forum_flights"],
                               t["boarding_clean"], t["link_candidates"])

    cards = (loy.dropna(subset=["card_key"])
                .groupby("profile_id")["card_key"].agg(lambda s: "; ".join(sorted(set(s))))
                .rename("loyalty_cards").reset_index())

    f = (fl.merge(prof[["profile_id", "nickname", "sex", "first_name_norm", "last_name_norm"]],
                  on="profile_id", how="left")
           .merge(cards, on="profile_id", how="left"))

    lb = links[links["match_rule"] == "name+flight+date"].copy()
    lb["profile_id"] = lb["record_a"].str.replace("forum:", "", regex=False).astype(int)
    lb = lb.merge(b[["source_record_id", "flight_number", "flight_date"]],
                  left_on="record_b", right_on="source_record_id")
    conf = (lb.groupby(["profile_id", "flight_number", "flight_date"])["record_b"]
              .agg("; ".join).rename("linked_records").reset_index())
    f = f.merge(conf, left_on=["profile_id", "flight_number", "date"],
                right_on=["profile_id", "flight_number", "flight_date"], how="left")

    forum_events = pd.DataFrame({
        "source": "forum",
        "source_record_id": f["source_record_id"],
        "forum_profile_id": f["profile_id"],
        "nickname": f["nickname"],
        "first_name": f["first_name_norm"],
        "second_name": None,
        "last_name": f["last_name_norm"],
        "sex": f["sex"],
        "birth_date": None,
        "document": None,
        "loyalty_cards": f["loyalty_cards"],
        "flight_date": f["date"],
        "flight_time": None,
        "flight_number": f["flight_number"],
        "codeshare": f["codeshare"],
        "origin": f["origin"],
        "origin_city": f["origin_city"],
        "destination": f["destination"],
        "destination_city": f["destination_city"],
        "pnr": None,
        "ticket_number": None,
        "baggage": None,
        "linked_records": f["linked_records"],
    })

    bl = (lb.groupby("record_b")["record_a"].agg(lambda s: "; ".join(sorted(set(s))))
            .rename("linked_records").reset_index())
    bb = b.merge(bl, left_on="source_record_id", right_on="record_b", how="left")

    boarding_events = pd.DataFrame({
        "source": "boarding_csv",
        "source_record_id": bb["source_record_id"],
        "forum_profile_id": None,
        "nickname": None,
        "first_name": bb["first_name_norm"],
        "second_name": bb["second_name_norm"],
        "last_name": bb["last_name_norm"],
        "sex": bb["sex"],
        "birth_date": bb["birth_date"],
        "document": bb["document_norm"],
        "loyalty_cards": None,
        "flight_date": bb["flight_date"],
        "flight_time": bb["flight_time"],
        "flight_number": bb["flight_number"],
        "codeshare": bb["codeshare"],
        "origin": None,
        "origin_city": None,
        "destination": None,
        "destination_city": bb["destination_city"],
        "pnr": bb["pnr"],
        "ticket_number": bb["ticket_number"],
        "baggage": bb["baggage"],
        "linked_records": bb["linked_records"],
    })

    allev = pd.concat([forum_events, boarding_events], ignore_index=True)
    allev["forum_profile_id"] = allev["forum_profile_id"].astype("Int64")
    allev["is_linked"] = allev["linked_records"].notna()
    allev = allev.sort_values(["flight_date", "flight_number", "source"], kind="stable")

    allev.to_parquet(PROCESSED / "all_travel_events.parquet", index=False)
    allev.to_csv(CSV_DIR / "all_travel_events.csv", index=False)

    pd.concat([allev[allev["source"] == "forum"].head(7),
               allev[allev["source"] == "boarding_csv"].head(7),
               allev[allev["is_linked"]].head(6)]
              ).to_csv(SAMPLES / "all_travel_events_sample.csv", index=False)

    print(f"  all_travel_events    {len(allev):>9} строк (форум {len(forum_events)}, "
          f"boarding {len(boarding_events)}, связанных {int(allev['is_linked'].sum())})")


def step_anomalies():
    print("[3/4] ANOMALIES: processed/anomalies/")
    prof, loy, fl, b, links = (load("forum_profiles"), load("forum_loyalty"), load("forum_flights"),
                               load("boarding_clean"), load("link_candidates"))
    pinfo = prof[["profile_id", "nickname", "first_name_norm", "last_name_norm"]]
    results = {}

    def add(name, description, df):
        results[name] = (description, df)
        df.to_csv(ANOMALIES / f"{name}.csv", index=False)
        sample(df, f"anomaly_{name}")
        print(f"  {name:36s} {len(df):>7}")

    n = loy.dropna(subset=["card_key"]).groupby("card_key")["profile_id"].nunique()
    add("F1_card_shared_by_profiles",
        "Одна карта лояльности (program+number) указана в нескольких профилях форума",
        loy[loy["card_key"].isin(n[n > 1].index)].merge(pinfo, on="profile_id").sort_values("card_key"))

    named = pinfo.dropna(subset=["first_name_norm", "last_name_norm"])
    cnt = named.groupby(["first_name_norm", "last_name_norm"])["profile_id"].transform("count")
    add("F2_same_name_many_profiles",
        "Одно и то же имя+фамилия у нескольких профилей (тёзки или один человек под разными никами)",
        named[cnt > 1].sort_values(["last_name_norm", "first_name_norm"]))

    c = loy.groupby(["profile_id", "program"]).size().rename("n_cards").reset_index()
    add("F3_several_cards_same_program",
        "У одного профиля несколько карт одной и той же программы лояльности",
        c[c["n_cards"] > 1].merge(pinfo, on="profile_id"))

    add("F4_origin_equals_destination",
        "Рейс, у которого аэропорт вылета совпадает с аэропортом прилёта "
        "(на практике - заглушка REA у рейсов KE/CZ, ошибка источника)",
        fl[fl["origin"].notna() & (fl["origin"] == fl["destination"])].merge(pinfo, on="profile_id"))

    d = fl[["profile_id", "date", "flight_seq", "flight_number", "origin", "destination"]]
    multi = d[d.duplicated(["profile_id", "date"], keep=False)]
    pairs = multi.merge(multi, on=["profile_id", "date"], suffixes=("", "_other"))
    pairs = pairs[pairs["flight_seq"] != pairs["flight_seq_other"]]
    pairs["chained"] = ((pairs["destination"] == pairs["origin_other"]) |
                        (pairs["origin"] == pairs["destination_other"]))
    ok = pairs.groupby(["profile_id", "flight_seq"])["chained"].any().reset_index()
    bad = ok[~ok["chained"]][["profile_id", "flight_seq"]]
    add("F5_same_day_unconnected_flights",
        "В один день у профиля есть рейс, который не стыкуется ни с одним другим рейсом этого дня",
        multi.merge(bad, on=["profile_id", "flight_seq"]).merge(pinfo, on="profile_id")
             .sort_values(["profile_id", "date"]))

    out, thr = iqr_outliers(fl.groupby("profile_id").size().rename("n_flights"))
    add("F6_too_many_flights_profile",
        f"Профили с аномально большим числом рейсов (> {thr:.0f}, правило Q3 + 3·IQR)",
        out.reset_index().merge(pinfo, on="profile_id").sort_values("n_flights", ascending=False))

    add("F7_duplicate_flight_in_profile",
        "Один и тот же рейс в одну дату записан в профиле несколько раз",
        fl[fl.duplicated(["profile_id", "date", "flight_number"], keep=False)].merge(pinfo, on="profile_id"))

    bb = b[["source_record_id", "first_name_norm", "second_name_norm", "last_name_norm",
            "birth_date", "document_norm", "flight_date", "flight_time",
            "flight_number", "destination_city", "pnr", "ticket_number"]]

    g = bb.groupby("document_norm").agg(n_names=("last_name_norm", "nunique"),
                                         n_first=("first_name_norm", "nunique"),
                                         n_bdates=("birth_date", "nunique"))
    add("B1_document_different_people",
        "Один номер документа у пассажиров с разными ФИО или датами рождения",
        bb[bb["document_norm"].isin(g[(g > 1).any(axis=1)].index)].sort_values(["document_norm", "flight_date"]))

    nd = bb.groupby(PERSON_KEY)["document_norm"].transform("nunique")
    add("B2_person_many_documents",
        "Один и тот же человек (имя+фамилия+дата рождения) летал по разным документам",
        bb[nd > 1].sort_values(PERSON_KEY + ["flight_date"]))

    t = bb.dropna(subset=["flight_time"]).copy()
    t["ts"] = pd.to_datetime(t["flight_date"].astype(str) + " " + t["flight_time"].astype(str))
    t = t[t.duplicated(["document_norm", "flight_date"], keep=False)]
    m = t.merge(t, on=["document_norm", "flight_date"], suffixes=("", "_2"))
    m = m[(m["source_record_id"] < m["source_record_id_2"]) & (m["flight_number"] != m["flight_number_2"])]
    m["minutes_between"] = (m["ts_2"] - m["ts"]).abs().dt.total_seconds() / 60
    add("B3_document_two_flights_2h",
        "Один документ сел на два разных рейса с разницей меньше 2 часов в один день",
        m[m["minutes_between"] < 120][[
            "document_norm", "first_name_norm", "last_name_norm", "flight_date",
            "flight_number", "flight_time", "destination_city",
            "flight_number_2", "flight_time_2", "destination_city_2", "minutes_between",
            "source_record_id", "source_record_id_2"]])

    tk = bb.dropna(subset=["ticket_number"])
    add("B4_ticket_shared", "Один номер билета использован разными документами",
        tk[tk.groupby("ticket_number")["document_norm"].transform("nunique") > 1].sort_values("ticket_number"))

    age = (pd.to_datetime(bb["flight_date"]) - pd.to_datetime(bb["birth_date"])).dt.days / 365.25
    add("B5_impossible_age", "Возраст пассажира на дату полёта меньше 0 или больше 100 лет",
        bb.assign(age_at_flight=age.round(1))[(age < 0) | (age > 100)])

    out, thr = iqr_outliers(bb.groupby("document_norm").size().rename("n_flights"))
    add("B6_too_many_flights_document",
        f"Документы с аномально большим числом полётов (> {thr:.0f}, правило Q3 + 3·IQR)",
        out.reset_index()
           .merge(bb.drop_duplicates("document_norm")[["document_norm", "first_name_norm",
                                                       "last_name_norm", "birth_date"]], on="document_norm")
           .sort_values("n_flights", ascending=False))

    lk = links.merge(bb, left_on="record_b", right_on="source_record_id")
    lk["profile_id"] = lk["record_a"].str.replace("forum:", "", regex=False).astype(int)
    g = lk.groupby("profile_id").agg(n_docs=("document_norm", "nunique"), n_bdates=("birth_date", "nunique"))
    multi_id = g[(g > 1).any(axis=1)].index
    add("X1_profile_linked_to_many_documents",
        "Профиль форума совпал с посадками, где разные документы или даты рождения",
        lk[lk["profile_id"].isin(multi_id)][["profile_id", "first_name_norm", "last_name_norm", "birth_date",
                                             "document_norm", "flight_number", "flight_date"]]
          .merge(prof[["profile_id", "nickname"]], on="profile_id").sort_values(["profile_id", "flight_date"]))

    lf = lk.merge(fl[["profile_id", "flight_number", "date", "destination", "destination_city"]],
                  left_on=["profile_id", "flight_number", "flight_date"],
                  right_on=["profile_id", "flight_number", "date"], suffixes=("_boarding", "_forum"))

    def first_word(s):
        return s.fillna("").str.upper().str.split().str[0].str[:5]

    add("X2_destination_mismatch", "Связанный рейс: город назначения на форуме и в посадке различается",
        lf[first_word(lf["destination_city_forum"]) != first_word(lf["destination_city_boarding"])][[
            "profile_id", "first_name_norm", "last_name_norm", "flight_number", "flight_date",
            "destination", "destination_city_forum", "destination_city_boarding", "record_b"]])

    flags = []
    for name, (_, df) in results.items():
        if "profile_id" in df.columns:
            flags += [("forum:" + str(v), name) for v in df["profile_id"].dropna().unique()]
        elif "document_norm" in df.columns:
            flags += [("doc:" + str(v), name) for v in df["document_norm"].dropna().unique()]
    persons = (pd.DataFrame(flags, columns=["entity", "anomaly"])
                 .groupby("entity")["anomaly"]
                 .agg(n_anomaly_types="nunique", anomalies=lambda s: "; ".join(sorted(set(s))))
                 .reset_index().sort_values("n_anomaly_types", ascending=False))
    persons.to_csv(ANOMALIES / "persons_flags.csv", index=False)
    sample(persons, "anomaly_persons_flags")

    L = ["# Аномалии: форум + BoardingData", "",
         "Аномалия не равна доказательству. Это список того, что нужно проверить по другим источникам.", "",
         "| Код | Что ищем | Найдено строк |", "|---|---|---|"]
    L += [f"| {name} | {desc} | {len(df)} |" for name, (desc, df) in results.items()]
    L += ["", "## Люди с несколькими типами аномалий", "",
          f"Сущностей с хотя бы одной аномалией: {len(persons)}; "
          f"с двумя и более типами: {(persons['n_anomaly_types'] > 1).sum()}.", ""]
    if len(persons):
        L += ["| entity | типов | аномалии |", "|---|---|---|"]
        L += [f"| {r.entity} | {r.n_anomaly_types} | {r.anomalies} |" for r in persons.head(20).itertuples()]
    L += ["", "## Примеры", ""]
    for name, (desc, df) in results.items():
        if len(df):
            L += [f"### {name}", desc, "", "```", df.head(5).fillna("").to_string(index=False), "```", ""]
    (ANOMALIES / "anomalies_report.md").write_text("\n".join(L), encoding="utf-8")
    print("  -> processed/anomalies/anomalies_report.md")


def step_identity():
    print("[4/4] IDENTITY: integration/")
    prof, loy, fl, b = load("forum_profiles"), load("forum_loyalty"), load("forum_flights"), load("boarding_clean")

    def save(df, name):
        df.to_csv(INTEGRATION / f"{name}.csv", index=False)
        sample(df, f"integration_{name}")
        print(f"  {name:36s} {len(df):>8} строк")

    n_cards = loy.groupby("profile_id").size().rename("n_loyalty_cards")
    fstats = fl.groupby("profile_id").agg(n_flights=("flight_seq", "size"),
                                          first_flight_date=("date", "min"),
                                          last_flight_date=("date", "max"))
    fik = (prof[["profile_id", "source_record_id", "nickname", "sex", "first_name_norm", "last_name_norm"]]
           .merge(n_cards, on="profile_id", how="left")
           .merge(fstats, on="profile_id", how="left"))
    fik["has_real_name"] = fik["first_name_norm"].notna() & fik["last_name_norm"].notna()
    fik["n_loyalty_cards"] = fik["n_loyalty_cards"].fillna(0).astype(int)
    fik["n_flights"] = fik["n_flights"].fillna(0).astype(int)
    fik["profile_id"] = as_str(fik["profile_id"])
    fik = fik[["profile_id", "source_record_id", "nickname", "sex", "first_name_norm", "last_name_norm",
               "has_real_name", "n_loyalty_cards", "n_flights", "first_flight_date", "last_flight_date"]]

    flk = loy.merge(prof[["profile_id", "nickname", "first_name_norm", "last_name_norm"]],
                    on="profile_id", how="left")
    flk["profile_id"] = as_str(flk["profile_id"])
    for c in ["program", "card_number", "card_key", "status"]:
        flk[c] = as_str(flk[c])
    flk = flk[["profile_id", "nickname", "first_name_norm", "last_name_norm",
               "program", "card_number", "card_key", "status"]]

    bik = b[["source_record_id", "first_name_norm", "second_name_norm", "last_name_norm",
             "sex", "birth_date", "document_norm", "pnr", "ticket_number",
             "flight_date", "flight_time", "flight_number", "destination_city"]].copy()
    for c in ["document_norm", "pnr", "ticket_number", "flight_number"]:
        bik[c] = as_str(bik[c])

    persons_per_doc = (bik.dropna(subset=["document_norm"])
                          .drop_duplicates(["document_norm"] + PERSON_KEY)
                          .groupby("document_norm").size())
    bad_docs = persons_per_doc[persons_per_doc > 1].index
    c1 = bik[bik["document_norm"].isin(bad_docs)].copy()
    c1["conflict_type"] = "same_document_different_people"
    c1["conflict_group"] = "doc:" + c1["document_norm"]

    docs_per_person = (bik.dropna(subset=PERSON_KEY)
                          .groupby(PERSON_KEY)["document_norm"].nunique()
                          .rename("n_docs").reset_index())
    multi = docs_per_person[docs_per_person["n_docs"] > 1].drop(columns="n_docs")
    c2 = bik.merge(multi, on=PERSON_KEY)
    c2["conflict_type"] = "same_person_multiple_documents"
    c2["conflict_group"] = ("person:" + c2["first_name_norm"] + "|" + c2["last_name_norm"]
                            + "|" + c2["birth_date"].astype(str))

    conflicts = (pd.concat([c1, c2], ignore_index=True)[
                    ["conflict_type", "conflict_group", "source_record_id",
                     "first_name_norm", "second_name_norm", "last_name_norm", "birth_date",
                     "document_norm", "flight_date", "flight_number"]]
                   .sort_values(["conflict_type", "conflict_group", "flight_date"]))

    save(fik, "forum_identity_keys")
    save(flk, "forum_loyalty_keys")
    save(bik, "boarding_identity_keys")
    save(conflicts, "boarding_document_conflicts")

    cards_multi = flk.dropna(subset=["card_key"]).groupby("card_key")["profile_id"].nunique()
    shared_cards = cards_multi[cards_multi > 1]
    checks = {
        "forum_identity_keys: 1 строка = 1 профиль (profile_id уникален)":
            fik["profile_id"].is_unique and len(fik) == len(prof),
        "forum_identity_keys: сумма n_flights = строк forum_flights": fik["n_flights"].sum() == len(fl),
        "forum_loyalty_keys: строк = строк forum_loyalty (ничего не удалено)": len(flk) == len(loy),
        "boarding_identity_keys: строк = строк boarding_clean": len(bik) == len(b),
        "boarding_identity_keys: source_record_id уникален": bik["source_record_id"].is_unique,
        "document_norm хранится строкой (ведущие нули сохранены)":
            bik["document_norm"].dropna().str.len().eq(10).all(),
    }

    L = ["# Identity QA (участник 2)", "", "## Контрольные количества", "",
         "| Показатель | Значение |", "|---|---|",
         f"| Forum profiles | {len(fik)} |",
         f"| Профилей с реальным именем | {int(fik['has_real_name'].sum())} |",
         f"| Профилей без реального имени | {int((~fik['has_real_name']).sum())} |",
         f"| Loyalty cards (строк) | {len(flk)} |",
         f"| Уникальных card_key | {flk['card_key'].nunique()} |",
         f"| card_key у более чем одного profile_id | {len(shared_cards)} |",
         f"| Boarding records | {len(bik)} |",
         f"| Уникальных document_norm | {bik['document_norm'].nunique()} |",
         f"| Документов у разных людей | {len(bad_docs)} |",
         f"| Людей с несколькими документами | {len(multi)} |",
         f"| Строк в boarding_document_conflicts | {len(conflicts)} |",
         "", "## Проверки", "", "| Проверка | Результат |", "|---|---|"]
    L += [f"| {k} | {'OK' if v else 'FAIL'} |" for k, v in checks.items()]
    L += ["", "## Определения", "",
          "- Человек в BoardingData = `first_name_norm + last_name_norm + birth_date`. "
          "Отчество в ключ не входит: оно записано то полностью, то инициалом.",
          "- `same_document_different_people`: у одного `document_norm` больше одного такого человека.",
          "- `same_person_multiple_documents`: у одного такого человека больше одного `document_norm`.",
          "- Одна запись может попасть в оба типа конфликта.",
          "- Ни одна запись не удалена и не исправлена; какая версия «правильная», не решалось.",
          "- `link_candidates` на этом этапе не использовался.",
          "", "## Карты у нескольких профилей", ""]
    if len(shared_cards):
        sc = flk[flk["card_key"].isin(shared_cards.index)].sort_values("card_key")
        L += ["```", sc.fillna("").to_string(index=False), "```"]
    else:
        L.append("Нет.")
    L += ["", "## Конфликтные группы документов", ""]
    if len(conflicts):
        for (ctype, grp), g in conflicts.groupby(["conflict_type", "conflict_group"]):
            L += [f"{ctype} - `{grp}` ({len(g)} записей)", "", "```",
                  g.drop(columns=["conflict_type", "conflict_group"]).fillna("").to_string(index=False),
                  "```", ""]
    else:
        L.append("Нет.")
    (INTEGRATION / "identity_qa.md").write_text("\n".join(L), encoding="utf-8")


    print("  -> integration/identity_qa.md, integration/build_identity_keys.py")
    for k, v in checks.items():
        print(f"    {'OK  ' if v else 'FAIL'} {k}")


STEPS = {"parse": step_parse, "export": step_export, "anomalies": step_anomalies, "identity": step_identity}


def main():
    ap = argparse.ArgumentParser(description="Пайплайн участника 2: форум + BoardingData")
    ap.add_argument("--skip-parse", action="store_true",
                    help="не парсить JSON/CSV заново, взять готовые processed/*.parquet")
    ap.add_argument("--only", choices=STEPS.keys(), help="запустить только один этап")
    args = ap.parse_args()

    for d in [PROCESSED, CSV_DIR, ANOMALIES, INTEGRATION, SAMPLES, P2_REPORTS]:
        d.mkdir(parents=True, exist_ok=True)

    if args.only:
        steps = [args.only]
    else:
        steps = [s for s in STEPS if not (args.skip_parse and s == "parse")]

    if "parse" in steps:
        for p in [JSON_PATH, CSV_PATH]:
            if not p.exists():
                raise SystemExit(f"Не найден файл: {p}\nПоложи исходники в папку {DATA}")

    for s in steps:
        STEPS[s]()
    print(f"\nГотово. Папка проекта: {BASE}")


if __name__ == "__main__":
    main()
