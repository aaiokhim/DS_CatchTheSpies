"""
Сводит таблицы всех участников в две общие таблицы одного формата, без удаления дубликатов.

Читает: participants/p2_forum_boarding/output/processed, participants/*/output, data/raw/BoardingData.csv.
Пишет: integration/merged/passengers_all.parquet, integration/merged/flights_all/ (по файлу на источник),
integration/reports/merge_qa.md, integration/samples/merged_*.

python3 integration/src/merge_all.py [--no-csv]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import (ROOT, RAW, PARTICIPANT_OUTPUTS, P2_PROCESSED, MERGED, FLIGHTS_ALL, INT_SAMPLES,
                   INT_REPORTS, FLIGHT_PARTS)

BASE = ROOT
PROCESSED = P2_PROCESSED
SAMPLES = INT_SAMPLES
SEARCH_DIRS = [RAW] + PARTICIPANT_OUTPUTS

N_SAMPLE = 20

FILES = {
    "boarding_data": "BoardingData.csv",
    "sirena": "sirena.csv",
    "boarding_passes": "boarding_passes.csv",
    "pointz_users": "pointz_users.csv",
    "pointz_cards": "pointz_cards.csv",
    "pointz_flights": "pointz_flights.csv",
    "skyteam": "skyteam_exchange.csv",
}

P_COLS = [
    "source", "source_record_id", "source_person_id",
    "full_name_raw", "first_name_raw", "middle_name_raw", "last_name_raw",
    "title", "sex", "birth_date", "document", "loyalty_ids", "pnr", "e_ticket",
]
F_COLS = [
    "source", "source_record_id", "passenger_record_id",
    "flight_number", "flight_date", "departure_time", "arrival_date", "arrival_time",
    "origin_airport_raw", "origin_airport", "destination_airport_raw", "destination_airport",
    "is_suspicious_airport", "origin_city", "destination_city",
    "codeshare", "booking_class", "fare_code",
    "loyalty_id", "document", "pnr", "e_ticket", "baggage_raw",
]
BOOL_COLS = {"is_suspicious_airport", "codeshare"}

NA_TOKENS = {"", "N/A", "NA", "NOT PRESENTED", "NULL", "NAN", "NONE_VALUE"}
BAD_AIRPORTS = {"REA", "OVA", "NIA", "NGO", "NDS"}


def find(key):
    hits = [h for d in SEARCH_DIRS if d.exists() for h in sorted(d.rglob(FILES[key]))]
    return hits[0] if hits else None


def read_csv(key, **kw):
    path = find(key)
    if path is None:
        print(f"  !! не найден {FILES[key]} (искала в data/raw и participants/*/output) - источник пропущен")
        return None
    print(f"  читаю {path.relative_to(BASE)}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, **kw)


def col(df, name):
    if name in df.columns:
        return df[name]
    return pd.Series(pd.NA, index=df.index, dtype="string")


def clean(s):
    s = s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return s.mask(s.str.upper().isin(NA_TOKENS))


def name_raw(s):
    s = s.astype("string")
    return s.mask(s.str.strip() == "")


def upper_nospace(s):
    return clean(s).str.upper().str.replace(" ", "", regex=False)


def to_date(s, fmt=None):
    d = pd.to_datetime(clean(s.astype("string")), format=fmt, errors="coerce")
    return d.dt.strftime("%Y-%m-%d").astype("string")


def to_time(s):
    t = pd.to_datetime(clean(s), format="%H:%M", errors="coerce")
    return t.dt.strftime("%H:%M").astype("string")


def airport(s):
    return clean(s).str.upper()


def loyalty(program, number):
    p = upper_nospace(program)
    n = upper_nospace(number)
    return (p + " " + n).where(p.notna() & n.notna())


def loyalty_from_id(s):
    x = upper_nospace(s)
    parts = x.str.extract(r"^([A-Z]{2})(\d+)$")
    return (parts[0] + " " + parts[1]).where(parts[0].notna(), x)


def suspicious(raw, code, city=None):
    raw = raw.astype("string")
    flag = raw.str.fullmatch(r"[a-z]{3}", na=False)
    flag |= code.isin(BAD_AIRPORTS - {"NGO"}).fillna(False)
    ngo = (code == "NGO").fillna(False)
    if city is None:
        flag |= ngo & raw.str.fullmatch("ngo", na=False)
    else:
        flag |= ngo & ~city.astype("string").str.upper().str.contains("NAGOYA", na=False)
    return flag.astype(bool)


def codeshare_from(s, true_values, false_values):
    x = clean(s).str.upper()
    out = pd.Series(pd.NA, index=s.index, dtype="boolean")
    out[x.isin(true_values).fillna(False)] = True
    out[x.isin(false_values).fillna(False)] = False
    return out


def frame(cols, n, **values):
    idx = pd.RangeIndex(n)
    out = {}
    for c in cols:
        v = values.get(c)
        if v is None:
            out[c] = pd.Series(pd.NA, index=idx, dtype="boolean" if c in BOOL_COLS else "string")
        elif isinstance(v, pd.Series):
            out[c] = v.reset_index(drop=True)
        else:
            out[c] = pd.Series([v] * n, index=idx)
    df = pd.DataFrame(out)
    for c in cols:
        df[c] = df[c].astype("boolean" if c in BOOL_COLS else "string")
    return df


class Sink:
    def __init__(self, name, cols, write_csv):
        self.cols = cols
        self.schema = pa.schema([(c, pa.bool_() if c in BOOL_COLS else pa.string()) for c in cols])
        self.partitioned = name == "flights_all"
        self.writers = {}
        if not self.partitioned:
            self.pq = pq.ParquetWriter(MERGED / f"{name}.parquet", self.schema)
        self.csv = (MERGED / f"{name}.csv") if write_csv else None
        self.csv_header = True
        self.name = name
        self.stats = []
        self.samples = []

    def write(self, df):
        if df is None or len(df) == 0:
            return
        df = df[self.cols]
        table = pa.Table.from_pandas(df, schema=self.schema, preserve_index=False)
        if self.partitioned:
            src = df["source"].iloc[0]
            if src not in self.writers:
                part = next(p for p in FLIGHT_PARTS if p.split("_", 1)[1] == src)
                FLIGHTS_ALL.mkdir(parents=True, exist_ok=True)
                self.writers[src] = pq.ParquetWriter(FLIGHTS_ALL / f"{part}.parquet", self.schema)
            self.writers[src].write_table(table)
        else:
            self.pq.write_table(table)
        if self.csv:
            df.to_csv(self.csv, mode="w" if self.csv_header else "a", header=self.csv_header, index=False)
            self.csv_header = False
        src = df["source"].iloc[0]
        self.stats.append((src, len(df), df.isna().sum().to_dict(), df))
        self.samples.append(df.head(5))
        print(f"    {self.name:16s} + {len(df):>9} строк  ({src})")

    def close(self):
        for w in ([*self.writers.values()] if self.partitioned else [self.pq]):
            w.close()
        pd.concat(self.samples).to_csv(SAMPLES / f"merged_{self.name}_sample.csv", index=False)


def forum(P, F):
    need = [PROCESSED / f"{t}.parquet" for t in ["forum_profiles", "forum_loyalty", "forum_flights"]]
    if not all(p.exists() for p in need):
        print("  !! нет processed/forum_*.parquet - сначала запусти pipeline.py; форум пропущен")
        return
    print("  читаю processed/forum_*.parquet")
    prof, loy, fl = (pd.read_parquet(p) for p in need)

    cards = (loy.assign(lid=loyalty(loy["program"], loy["card_number"]))
                .dropna(subset=["lid"])
                .groupby("profile_id")["lid"].agg(lambda s: "; ".join(s)))
    prof = prof.merge(cards.rename("loyalty_ids"), on="profile_id", how="left")

    P.write(frame(P_COLS, len(prof),
                  source="forum",
                  source_record_id=prof["source_record_id"].astype("string"),
                  source_person_id=prof["profile_id"].astype("string"),
                  first_name_raw=name_raw(prof["first_name_raw"]),
                  last_name_raw=name_raw(prof["last_name_raw"]),
                  sex=clean(prof["sex"]),
                  loyalty_ids=prof["loyalty_ids"].astype("string")))

    org, dst = airport(fl["origin"]), airport(fl["destination"])
    F.write(frame(F_COLS, len(fl),
                  source="forum",
                  source_record_id=fl["source_record_id"].astype("string"),
                  passenger_record_id="forum:" + fl["profile_id"].astype("string"),
                  flight_number=upper_nospace(fl["flight_number"]),
                  flight_date=to_date(fl["date"].astype("string")),
                  origin_airport_raw=fl["origin"].astype("string"),
                  origin_airport=org,
                  destination_airport_raw=fl["destination"].astype("string"),
                  destination_airport=dst,
                  is_suspicious_airport=suspicious(fl["origin"], org, fl["origin_city"])
                                        | suspicious(fl["destination"], dst, fl["destination_city"]),
                  origin_city=clean(fl["origin_city"]).str.upper(),
                  destination_city=clean(fl["destination_city"]).str.upper(),
                  codeshare=fl["codeshare"].astype("boolean")))


def boarding_data(P, F):
    df = read_csv("boarding_data", sep=";")
    if df is None:
        return
    rid = "boarding:" + pd.Series(df.index.astype(str), dtype="string")
    doc = upper_nospace(df["PassengerDocument"])
    pnr, tkt = upper_nospace(df["BookingCode"]), upper_nospace(df["TicketNumber"])

    P.write(frame(P_COLS, len(df),
                  source="boarding_data", source_record_id=rid,
                  first_name_raw=name_raw(df["PassengerFirstName"]),
                  middle_name_raw=name_raw(df["PassengerSecondName"]),
                  last_name_raw=name_raw(df["PassengerLastName"]),
                  sex=clean(df["PassengerSex"]),
                  birth_date=to_date(df["PassengerBirthDate"], "%m/%d/%Y"),
                  document=doc, pnr=pnr, e_ticket=tkt))

    F.write(frame(F_COLS, len(df),
                  source="boarding_data", source_record_id=rid, passenger_record_id=rid,
                  flight_number=upper_nospace(df["FlightNumber"]),
                  flight_date=to_date(df["FlightDate"], "%Y-%m-%d"),
                  departure_time=to_time(df["FlightTime"]),
                  destination_city=clean(df["Destination"]).str.upper(),
                  codeshare=codeshare_from(df["CodeShare"], {"OPERATED"}, {"OWN"}),
                  document=doc, pnr=pnr, e_ticket=tkt,
                  baggage_raw=df["Baggage"].astype("string").str.strip()))


def sirena(P, F):
    df = read_csv("sirena")
    if df is None:
        return
    rid = "sirena:" + pd.Series(df.index.astype(str), dtype="string")
    doc = upper_nospace(df["travel_doc"])
    pnr, tkt = upper_nospace(df["pnr"]), upper_nospace(df["e_ticket"])
    lid = loyalty(col(df, "loyalty_program_code"), col(df, "loyalty_number"))

    P.write(frame(P_COLS, len(df),
                  source="sirena", source_record_id=rid,
                  full_name_raw=name_raw(df["passenger_name_raw"]),
                  birth_date=to_date(df["birth_date"], "%Y-%m-%d"),
                  document=doc, loyalty_ids=lid, pnr=pnr, e_ticket=tkt))

    org, dst = airport(df["origin_airport"]), airport(df["destination_airport"])
    F.write(frame(F_COLS, len(df),
                  source="sirena", source_record_id=rid, passenger_record_id=rid,
                  flight_number=upper_nospace(df["flight_number"]),
                  flight_date=to_date(df["depart_date"], "%Y-%m-%d"),
                  departure_time=to_time(df["depart_time"]),
                  arrival_date=to_date(df["arrival_date"], "%Y-%m-%d"),
                  arrival_time=to_time(df["arrival_time"]),
                  origin_airport_raw=df["origin_airport"].astype("string"), origin_airport=org,
                  destination_airport_raw=df["destination_airport"].astype("string"), destination_airport=dst,
                  is_suspicious_airport=suspicious(df["origin_airport"], org) | suspicious(df["destination_airport"], dst),
                  codeshare=codeshare_from(df["sh_raw"], {"YES"}, {"NO"}),
                  booking_class=upper_nospace(df["travel_class"]),
                  fare_code=upper_nospace(df["fare"]),
                  loyalty_id=lid, document=doc, pnr=pnr, e_ticket=tkt,
                  baggage_raw=clean(df["baggage"])))


def boarding_passes(P, F):
    df = read_csv("boarding_passes")
    if df is None:
        return
    rid = "bp:" + pd.Series(df.index.astype(str), dtype="string")
    pnr, tkt = upper_nospace(df["pnr"]), upper_nospace(df["e_ticket"])
    lid = loyalty_from_id(df["loyalty_id_raw"])

    P.write(frame(P_COLS, len(df),
                  source="boarding_passes", source_record_id=rid,
                  full_name_raw=name_raw(df["passenger_name_raw"]),
                  title=clean(df["title"]).str.upper(),
                  loyalty_ids=lid, pnr=pnr, e_ticket=tkt))

    org, dst = airport(df["origin_airport"]), airport(df["destination_airport"])
    F.write(frame(F_COLS, len(df),
                  source="boarding_passes", source_record_id=rid, passenger_record_id=rid,
                  flight_number=upper_nospace(df["flight_number"]),
                  flight_date=to_date(df["flight_date"], "%Y-%m-%d"),
                  departure_time=to_time(df["departure_time"]),
                  origin_airport_raw=df["origin_airport"].astype("string"), origin_airport=org,
                  destination_airport_raw=df["destination_airport"].astype("string"), destination_airport=dst,
                  is_suspicious_airport=suspicious(df["origin_airport"], org, df["origin_city"])
                                        | suspicious(df["destination_airport"], dst, df["destination_city"]),
                  origin_city=clean(df["origin_city"]).str.upper(),
                  destination_city=clean(df["destination_city"]).str.upper(),
                  booking_class=upper_nospace(df["booking_class_raw"]),
                  loyalty_id=lid, pnr=pnr, e_ticket=tkt))


def pointz(P, F):
    users = read_csv("pointz_users")
    cards = read_csv("pointz_cards")
    flights = read_csv("pointz_flights")

    uid_to_rec = None
    if users is not None:
        users = users.copy()
        n_cards = pd.to_numeric(col(users, "cards_count"), errors="coerce").fillna(1)
        dup = users["user_uid"].duplicated(keep=False)
        owners = users[~dup | (n_cards > 0)]
        n_own = owners.groupby("user_uid").size()
        unresolved = n_own[n_own != 1].index
        owners = pd.concat([owners[~owners["user_uid"].isin(unresolved)],
                            users[users["user_uid"].isin(unresolved)]])
        users["is_card_owner"] = users["source_record_id"].isin(owners["source_record_id"])
        if dup.any():
            print(f"    user_uid с дублями: {users.loc[dup, 'user_uid'].nunique()}; "
                  f"карты/перелёты отданы владельцу по cards_count, нерешённых: {len(unresolved)}")

        if cards is not None:
            c = (cards.assign(lid=loyalty_from_id(cards["loyalty_id_raw"]))
                      .dropna(subset=["lid"])
                      .groupby("user_uid")["lid"].agg(lambda s: "; ".join(s)))
            users = users.merge(c.rename("loyalty_ids"), left_on="user_uid", right_index=True, how="left")
            users.loc[~users["is_card_owner"], "loyalty_ids"] = pd.NA
        P.write(frame(P_COLS, len(users),
                      source="pointz", source_record_id=users["source_record_id"].astype("string"),
                      source_person_id=upper_nospace(users["user_uid"]),
                      full_name_raw=name_raw(users["full_name_raw"]),
                      first_name_raw=name_raw(users["first_name_raw"]),
                      last_name_raw=name_raw(users["last_name_raw"]),
                      loyalty_ids=col(users, "loyalty_ids").astype("string")))
        uid_to_rec = users[users["is_card_owner"]].groupby("user_uid")["source_record_id"].agg("; ".join)

    if flights is not None:
        org, dst = airport(flights["origin_airport"]), airport(flights["destination_airport"])
        prec = flights["user_uid"].map(uid_to_rec) if uid_to_rec is not None else None
        F.write(frame(F_COLS, len(flights),
                      source="pointz", source_record_id=flights["source_record_id"].astype("string"),
                      passenger_record_id=None if prec is None else prec.astype("string"),
                      flight_number=upper_nospace(flights["flight_number"]),
                      flight_date=to_date(flights["flight_date"], "%Y-%m-%d"),
                      origin_airport_raw=flights["origin_airport_raw"].astype("string"), origin_airport=org,
                      destination_airport_raw=flights["destination_airport_raw"].astype("string"), destination_airport=dst,
                      is_suspicious_airport=suspicious(flights["origin_airport_raw"], org)
                                            | suspicious(flights["destination_airport_raw"], dst),
                      fare_code=upper_nospace(col(flights, "fare_code")),
                      loyalty_id=loyalty_from_id(flights["loyalty_id_raw"])))


def skyteam(P, F):
    df = read_csv("skyteam")
    if df is None:
        return
    expected = ["source_record_id", "loyalty_id_raw", "flight_number", "flight_date",
                "origin_airport_raw", "destination_airport_raw"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        print(f"  !! в skyteam_exchange.csv нет колонок {missing}; есть: {list(df.columns)}")
    o_raw = col(df, "origin_airport_raw") if "origin_airport_raw" in df else col(df, "origin_airport")
    d_raw = col(df, "destination_airport_raw") if "destination_airport_raw" in df else col(df, "destination_airport")
    org, dst = airport(o_raw), airport(d_raw)
    lid_src = col(df, "loyalty_id_raw") if "loyalty_id_raw" in df else col(df, "loyalty_id_normalized")
    rid = (df["source_record_id"].astype("string") if "source_record_id" in df
           else "st:" + pd.Series(df.index.astype(str), dtype="string"))
    F.write(frame(F_COLS, len(df),
                  source="skyteam", source_record_id=rid,
                  flight_number=upper_nospace(col(df, "flight_number")),
                  flight_date=to_date(col(df, "flight_date"), "%Y-%m-%d"),
                  origin_airport_raw=o_raw.astype("string"), origin_airport=org,
                  destination_airport_raw=d_raw.astype("string"), destination_airport=dst,
                  is_suspicious_airport=suspicious(o_raw, org) | suspicious(d_raw, dst),
                  booking_class=upper_nospace(col(df, "booking_class")),
                  fare_code=upper_nospace(col(df, "fare_code")),
                  loyalty_id=loyalty_from_id(lid_src)))


FORMAT_CHECKS = {
    "flight_number": r"[A-Z0-9]{2}\d{1,4}",
    "flight_date": r"\d{4}-\d{2}-\d{2}",
    "birth_date": r"\d{4}-\d{2}-\d{2}",
    "departure_time": r"\d{2}:\d{2}",
    "origin_airport": r"[A-Z]{3}",
    "destination_airport": r"[A-Z]{3}",
    "loyalty_id": r"[A-Z]{2} \d+",
    "document": r"\S+",
}


def report(P, F):
    L = ["# Merge QA: все источники", "",
         "Строки не удалялись, дубликаты не убирались, имена не изменялись.", ""]
    for sink, key_cols in [(P, ["full_name_raw", "last_name_raw", "birth_date", "document", "loyalty_ids", "pnr", "e_ticket"]),
                           (F, ["flight_number", "flight_date", "origin_airport", "destination_airport",
                                "loyalty_id", "document", "pnr", "e_ticket"])]:
        total = sum(n for _, n, _, _ in sink.stats)
        L += [f"## {sink.name} - {total} строк", "",
              "| Источник | Строк | " + " | ".join(f"пусто: {c}" for c in key_cols) + " |",
              "|---" * (len(key_cols) + 2) + "|"]
        for src, n, nulls, _ in sink.stats:
            L.append(f"| {src} | {n} | " + " | ".join(f"{nulls[c] / n:.0%}" for c in key_cols) + " |")
        L += ["", "Проверка формата (доля непустых значений, НЕ подходящих под шаблон):", "",
              "| Источник | " + " | ".join(c for c in FORMAT_CHECKS if c in sink.cols) + " |",
              "|---" * (1 + sum(c in sink.cols for c in FORMAT_CHECKS)) + "|"]
        for src, n, _, df in sink.stats:
            cells = []
            for c, rx in FORMAT_CHECKS.items():
                if c not in sink.cols:
                    continue
                v = df[c].dropna()
                bad = (~v.str.fullmatch(rx)).sum() if len(v) else 0
                cells.append(f"{bad}" if bad else "OK")
            L.append(f"| {src} | " + " | ".join(cells) + " |")
        if "is_suspicious_airport" in sink.cols:
            L += ["", "| Источник | битых аэропортов (is_suspicious_airport) |", "|---|---|"]
            L += [f"| {src} | {int(df['is_suspicious_airport'].sum())} |" for src, _, _, df in sink.stats]
        L.append("")
    L += ["## Как связаны таблицы", "",
          "- `flights_all.passenger_record_id` -> `passengers_all.source_record_id` "
          "(forum: профиль; boarding_data / sirena / boarding_passes: та же строка; pointz: пользователь по user_uid).",
          "- У skyteam записей о людях нет, связь только через `loyalty_id`.",
          "- Один и тот же реальный перелёт может встречаться в нескольких источниках - это не удалялось.", ""]
    (INT_REPORTS / "merge_qa.md").write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Объединение всех источников без удаления дубликатов")
    ap.add_argument("--no-csv", action="store_true", help="писать только parquet")
    args = ap.parse_args()

    for d in (MERGED, SAMPLES, INT_REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    for p in FLIGHTS_ALL.glob("*.parquet"):
        p.unlink()
    P = Sink("passengers_all", P_COLS, not args.no_csv)
    F = Sink("flights_all", F_COLS, not args.no_csv)

    for name, fn in [("FORUM", forum), ("BOARDING DATA", boarding_data), ("SIRENA", sirena),
                     ("BOARDING PASSES", boarding_passes), ("POINTZ", pointz), ("SKYTEAM", skyteam)]:
        print(f"[{name}]")
        fn(P, F)

    P.close()
    F.close()
    report(P, F)
    print(f"\nГотово: {MERGED}  (отчёт: integration/reports/merge_qa.md)")


if __name__ == "__main__":
    main()
