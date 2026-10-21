"""
A4. Одна карта лояльности у разных людей (карты, исключённые склейкой как конфликтные).

python3 analysis/A4_shared_loyalty_card.py
"""
import pandas as pd

from common import MERGED, RES, links, name_any, save, read_flights_all, PASSENGERS_ALL


def main():
    conf = pd.read_csv(RES / "conflicted_keys.csv", dtype=str)
    cards = set(conf.loc[conf["key_type"] == "card", "key"].str.replace("card:", "", regex=False))
    print(f"общих карт в conflicted_keys: {len(cards)}: {sorted(cards)}")

    P = pd.read_parquet(PASSENGERS_ALL)
    P["name"] = name_any(P)
    pc = P.dropna(subset=["loyalty_ids"]).assign(card=lambda d: d["loyalty_ids"].str.split("; ")).explode("card")
    pc = pc[pc["card"].isin(cards)][["source_record_id", "card", "name"]]
    F = read_flights_all(columns=["source_record_id", "loyalty_id"])
    fc = F[F["loyalty_id"].isin(cards)].rename(columns={"loyalty_id": "card"})
    fc = fc.merge(P[["source_record_id", "name"]], on="source_record_id", how="left")
    rec = pd.concat([pc, fc]).merge(links(), on="source_record_id")

    rows = []
    for pid, g in rec.groupby("person_id"):
        mine = set(g["name"].dropna())
        others = rec[rec["card"].isin(g["card"]) & (rec["person_id"] != pid)]
        rows.append({
            "person_id": pid, "A4_flag": 1, "A4_count": g["card"].nunique(),
            "A4_cards": "; ".join(sorted(g["card"].unique())),
            "A4_other_people": "; ".join(sorted(set(others["name"].dropna()) - mine)) or "(без имени)",
            "A4_n_records": len(g),
        })
    save(pd.DataFrame(rows, columns=["person_id", "A4_flag", "A4_count", "A4_cards", "A4_other_people",
                                     "A4_n_records"]),
         "A4", ["A4_cards", "A4_other_people", "A4_n_records"])


if __name__ == "__main__":
    main()
