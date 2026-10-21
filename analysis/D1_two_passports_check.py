"""
Проверка пар-двойников с внутренним и заграничным паспортом и базовый уровень
расхождения паспортов по броням, связанным одним билетом.

python3 analysis/D1_two_passports_check.py
"""

import pandas as pd

from common import MERGED, RES, OUT, read_flights_all


def doc_type(d):
    if not isinstance(d, str):
        return ""
    return {10: "internal(10)", 9: "foreign(9)"}.get(len(d), f"other({len(d)})")


def main():
    chk = pd.read_csv(OUT / "D1_same_person_check.csv", dtype=str)
    pairs = chk[chk["category"] == "same_person_two_passports"][["person_id_1", "person_id_2", "name_1"]]
    print(f"пар с двумя паспортами: {len(pairs)}")
    ids = set(pairs.person_id_1) | set(pairs.person_id_2)

    links = pd.read_parquet(RES / "record_links.parquet", columns=["source_record_id", "person_id"])
    links = links[links["person_id"].isin(ids)]
    f = read_flights_all(columns=["source_record_id", "source", "flight_number", "flight_date", "document"])
    f = f.merge(links, on="source_record_id")

    rows = []
    for p in pairs.itertuples():
        a = f[f.person_id == p.person_id_1]
        b = f[f.person_id == p.person_id_2]
        shared = set(zip(a.flight_number, a.flight_date)) & set(zip(b.flight_number, b.flight_date))
        for fn, fd in sorted(shared, key=lambda x: x[1]):
            ra = a[(a.flight_number == fn) & (a.flight_date == fd)]
            rb = b[(b.flight_number == fn) & (b.flight_date == fd)]
            da = {(s, d) for s, d in zip(ra.source, ra.document) if isinstance(d, str)}
            db = {(s, d) for s, d in zip(rb.source, rb.document) if isinstance(d, str)}
            docs_a, docs_b = {d for _, d in da}, {d for _, d in db}
            if not docs_a or not docs_b:
                kind = "no_document_overlap"
            elif docs_a & docs_b:
                kind = "same_document"
            elif any(s == "sirena" for s, _ in da) and any(s == "sirena" for s, _ in db):
                kind = "double_booking"
            elif {doc_type(d) for d in docs_a} != {doc_type(d) for d in docs_b}:
                kind = "booking_vs_boarding_two_types"
            else:
                kind = "booking_vs_boarding_same_type"
            rows.append({
                "person_id_1": p.person_id_1, "person_id_2": p.person_id_2, "name": p.name_1,
                "flight_number": fn, "flight_date": fd, "kind": kind,
                "side_1": "; ".join(sorted(f"{s}={d} {doc_type(d)}" for s, d in da)) or "; ".join(sorted(set(ra.source))),
                "side_2": "; ".join(sorted(f"{s}={d} {doc_type(d)}" for s, d in db)) or "; ".join(sorted(set(rb.source))),
            })

    fl = pd.DataFrame(rows, columns=["person_id_1", "person_id_2", "name", "flight_number", "flight_date",
                                     "kind", "side_1", "side_2"])
    fl.to_csv(OUT / "D1_two_passports_flights.csv", index=False)

    if len(fl):
        pc = fl.pivot_table(index=["person_id_1", "person_id_2", "name"], columns="kind",
                            values="flight_number", aggfunc="count", fill_value=0).reset_index()
    else:
        pc = pairs.rename(columns={"name_1": "name"}).copy()
    for k in ["double_booking", "booking_vs_boarding_same_type", "booking_vs_boarding_two_types",
              "same_document", "no_document_overlap"]:
        if k not in pc:
            pc[k] = 0
    pc["verdict"] = ["suspicious" if (x + y) > 0 else "normal"
                     for x, y in zip(pc["double_booking"], pc["booking_vs_boarding_same_type"])]
    pc = pc.sort_values(["verdict", "double_booking", "booking_vs_boarding_same_type"], ascending=[False, False, False])
    pc.to_csv(OUT / "D1_two_passports_pairs.csv", index=False)

    allf = read_flights_all(columns=["source", "e_ticket", "document"])
    bd = allf[allf.source == "boarding_data"].dropna(subset=["e_ticket", "document"])
    sr = allf[allf.source == "sirena"].dropna(subset=["e_ticket", "document"])
    m = bd.merge(sr, on="e_ticket", suffixes=("_b", "_s"))
    diff = m[m.document_b != m.document_s]
    same_type_diff = int((diff.document_b.map(doc_type) == diff.document_s.map(doc_type)).sum())
    base = (f"Базовый уровень: из {len(m)} броней, где Sirena и BoardingData связаны одним билетом, "
            f"документы различаются в {len(diff)} ({len(diff) / max(len(m), 1):.1%}); "
            f"из них документы одного типа: {same_type_diff}.")
    print(base)

    kc = fl["kind"].value_counts()
    vc = pc["verdict"].value_counts()
    L = ["# Два паспорта: как используются документы на общих перелётах", "",
         f"Пар: {len(pairs)}; общих перелётов: {len(fl)}", "",
         "| Тип общего перелёта | Перелётов | Что значит |", "|---|---|---|",
         f"| double_booking | {int(kc.get('double_booking', 0))} | две брони в Sirena на один рейс под разными документами - подозрительно |",
         f"| booking_vs_boarding_same_type | {int(kc.get('booking_vs_boarding_same_type', 0))} | бронь и посадка по разным документам ОДНОГО типа - подозрительно |",
         f"| booking_vs_boarding_two_types | {int(kc.get('booking_vs_boarding_two_types', 0))} | бронь по загранпаспорту, посадка по внутреннему (или наоборот) - норма для этих данных |",
         f"| same_document | {int(kc.get('same_document', 0))} | документ совпадает |",
         f"| no_document_overlap | {int(kc.get('no_document_overlap', 0))} | документ известен только у одной половины |",
         "", "| Итог по паре | Пар |", "|---|---|",
         f"| suspicious (есть double_booking или booking_vs_boarding_same_type) | {int(vc.get('suspicious', 0))} |",
         f"| normal | {int(vc.get('normal', 0))} |",
         "", base]
    sus = fl[fl["kind"].isin(["double_booking", "booking_vs_boarding_same_type"])].head(15)
    if len(sus):
        L += ["", "## Примеры подозрительных перелётов", "", "```",
              sus[["name", "flight_number", "flight_date", "kind", "side_1", "side_2"]].to_string(index=False), "```"]
    (OUT / "D1_two_passports_check.md").write_text("\n".join(L), encoding="utf-8")

    print(kc.to_string())
    print(vc.to_string())
    print(f"-> {OUT / 'D1_two_passports_check.md'}")


if __name__ == "__main__":
    main()
